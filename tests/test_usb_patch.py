import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from test_firmware import module, ROOT

patcher = module("verified_patch")


class PatchSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.target = self.root / "example.c"
        self.target.write_text("old\n")
        self.patch = self.root / "change.patch"
        self.patch.write_text("".join(difflib.unified_diff(["old\n"], ["new\n"], fromfile="a/example.c", tofile="b/example.c")))
        self.hashes = self.root / "preimages.json"
        self.hashes.write_text(json.dumps({"example.c": patcher.sha(b"old\n")}))

    def test_apply_and_restore(self):
        with patcher.applied(self.root, self.patch, self.hashes):
            self.assertEqual(self.target.read_text(), "new\n")
        self.assertEqual(self.target.read_text(), "old\n")

    def test_restore_after_failed_build(self):
        with self.assertRaisesRegex(RuntimeError, "build failed"):
            with patcher.applied(self.root, self.patch, self.hashes):
                raise RuntimeError("build failed")
        self.assertEqual(self.target.read_text(), "old\n")

    def test_refuse_changed_preimage(self):
        self.target.write_text("user work\n")
        with self.assertRaisesRegex(ValueError, "preimage differs"):
            with patcher.applied(self.root, self.patch, self.hashes):
                self.fail("must not enter")
        self.assertEqual(self.target.read_text(), "user work\n")

    def test_preserve_concurrent_edit(self):
        with self.assertRaisesRegex(RuntimeError, "concurrent changes"):
            with patcher.applied(self.root, self.patch, self.hashes):
                self.target.write_text("concurrent work\n")
        self.assertEqual(self.target.read_text(), "concurrent work\n")

    def test_refuse_patch_outside_manifest(self):
        self.hashes.write_text("{}")
        with self.assertRaisesRegex(ValueError, "path list differs"):
            with patcher.applied(self.root, self.patch, self.hashes):
                self.fail("must not enter")
        self.assertEqual(self.target.read_text(), "old\n")


class UsbReportBoundsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cc = shutil.which("cc")
        cls.upstream = ROOT / "artifacts/tools/qmk"
        if not cls.cc or not (cls.upstream / "tmk_core/protocol/chibios/usb_report_handling.h").exists():
            raise unittest.SkipTest("C compiler and pinned upstream sources needed")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.root = Path(cls.tmp.name)
        patch = ROOT / "patches/qmk/compact-usb.patch"
        hashes = json.loads(patch.with_name("compact-usb-preimages.json").read_text())
        for name, expected in hashes.items():
            data = (cls.upstream / name).read_bytes()
            if patcher.sha(data) != expected:
                raise AssertionError("unexpected upstream source")
            target = cls.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        subprocess.run(["git", "apply", str(patch)], cwd=cls.root, check=True)
        (cls.root / "ch.h").write_text("#include <stdbool.h>\n#include <stddef.h>\n#include <stdint.h>\ntypedef uint16_t systime_t;\n")
        (cls.root / "hal.h").write_text("typedef struct USBDriver USBDriver;\n")
        (cls.root / "timer.h").write_text("typedef uint32_t time_msecs_t;\n")

    def compile(self, capacity, report_size):
        source = self.root / "bounds.c"
        source.write_text('#define QMK_USB_REPORT_STORAGE_SIZE ' + str(capacity) + '\n#include "tmk_core/protocol/chibios/usb_report_handling.h"\nconst usb_report_storage_t *storage = QMK_USB_REPORT_STORAGE_DEFAULT(' + str(report_size) + ');\n')
        return subprocess.run([self.cc, "-std=gnu11", "-I", str(self.root), "-c", str(source), "-o", str(self.root / "bounds.o")], capture_output=True, text=True)

    def test_keyboard_and_raw_fit(self):
        for size in (8, 32):
            result = self.compile(32, size)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_oversized_report_and_bad_capacity_fail_compile(self):
        for capacity, size in ((32, 33), (0, 8), (65, 8)):
            self.assertNotEqual(self.compile(capacity, size).returncode, 0)

    def test_four_layers_tapping_and_stacks_preserved(self):
        config = (ROOT / "firmware/keyboards/hyperx/alloy_fps_pro/keymaps/raw_compact/config.h").read_text()
        self.assertNotIn("NO_ACTION_TAPPING", config)
        self.assertNotIn("STACKSIZE", config)
        self.assertIn("LAYER_STATE_8BIT", config)
        keymap = (ROOT / "firmware/keyboards/hyperx/alloy_fps_pro/keymaps/raw_compact/keymap.c").read_text()
        self.assertIn('../custom42_fn/keymap.c', keymap)

    def test_report_copy_bounds_under_sanitizers(self):
        implementation = (self.root / "tmk_core/protocol/chibios/usb_report_handling.c").read_text()
        functions = implementation[implementation.index("void usb_set_report("):implementation.index("bool usb_get_report_cb(")]
        source = self.root / "report_runtime.c"
        source.write_text('''#define QMK_USB_REPORT_STORAGE_SIZE 32
#include "tmk_core/protocol/chibios/usb_report_handling.h"
#include <assert.h>
#include <string.h>
#define REPORT_ID_COUNT 1
static systime_t chVTGetSystemTimeX(void) { return 42; }
_Static_assert(sizeof(usb_fs_report_t) <= 40, "unexpected report storage growth");
''' + functions + '''
int main(void) {
    uint8_t input[256];
    memset(input, 0xa5, sizeof input);
    input[0] = 1;
    for (size_t n = 0; n < sizeof input; ++n) {
        usb_fs_report_t item = {.length = 8}, result = {.length = 99};
        usb_fs_report_t *reports[2] = {&item, &item};
        usb_set_report(reports, input, n);
        assert(item.length == (n <= 32 ? n : 8));
        if (n <= 32) assert(memcmp(item.data, input, n) == 0);
        item.length = 8;
        usb_shared_set_report(reports, input, n);
        assert(item.length == (n > 0 && n <= 32 ? n : 8));
        usb_get_report(reports, 0, &result);
        assert(result.length == item.length);
        reports[0] = NULL;
        usb_get_report(reports, 0, &result);
        assert(result.length == 0);
        result.length = 99;
        usb_shared_get_report(reports, 2, &result);
        assert(result.length == 0);
    }
    usb_fs_report_t *empty[2] = {NULL, NULL};
    usb_shared_set_report(empty, NULL, 0);
    return 0;
}
''')
        executable = self.root / "report_runtime"
        run = subprocess.run([self.cc, "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-fsanitize=address,undefined", "-I", str(self.root), str(source), "-o", str(executable)], text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        run = subprocess.run([str(executable)], text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
