"""Host protocol tests, not a USB/GUI/hardware certification."""
import ctypes
import json
import lzma
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

from test_firmware import ROOT, generator

PORT = ROOT / "firmware/keyboards/hyperx/alloy_fps_pro/keymaps/vial_readonly"


class DefinitionTests(unittest.TestCase):
    def test_generated_definition_is_current(self):
        run = subprocess.run([sys.executable, "scripts/generate_vial_readonly.py", "--check"],
                             cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)

    def test_definition_has_exactly_54_enabled_positions_and_no_dead_keys(self):
        data = json.loads((PORT / "vial.json").read_text())
        coords = [tuple(map(int, key.split(","))) for row in data["layouts"]["keymap"]
                  for key in row if isinstance(key, str)]
        matrix = json.loads((ROOT / "hardware/matrix-inference.json").read_text())
        _, maps, _ = generator.layers(matrix)
        base = generator.with_function_row(matrix, maps)[0]
        expected = {(i // 8, i % 8) for i, code in enumerate(base) if code != "KC_NO"}
        self.assertEqual(set(coords), expected)
        self.assertEqual(len(coords), 54)
        self.assertFalse(set(coords) & {(7, col) for col in range(5)})
        self.assertEqual(data["matrix"], {"rows": 14, "cols": 8})
        self.assertIn("READ-ONLY", data["name"])
        self.assertIn("electrical grid", data["name"])

    def test_build_entry_point_rejects_flash_before_loading_toolchain(self):
        for arg in ("vial_readonly:flash", "flash", "default"):
            run = subprocess.run([sys.executable, "scripts/build_compact_raw.py", "--keymap", arg],
                                 cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("invalid choice", run.stderr)


@unittest.skipUnless(shutil.which("cc"), "host C compiler unavailable")
class VialProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="alloy-vial-host-")
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.root = Path(cls.tmp.name)
        codes = {name: value for value, name in generator.HID.items() if name.startswith("KC_")}
        codes["KC_TRNS"] = 1
        (cls.root / "qmk_mock.h").write_text(
            "#include <stdint.h>\n#define MATRIX_ROWS 14\n#define MATRIX_COLS 8\n#define PROGMEM\n"
            + "enum {" + ",".join(f"{key}={value}" for key, value in codes.items()) + "};\n"
            + "#define S(k) (0x0200u | (k))\n#define MO(l) (0x5220u | (l))\n"
            + "#define LT(l,k) (0x4000u | ((l)<<8) | (k))\n"
            + "#define pgm_read_word(p) (*(const uint16_t *)(p))\n")
        (cls.root / "raw_hid.h").write_text("#include <stdint.h>\nvoid raw_hid_send(uint8_t *, uint8_t);\n")
        cls.shim = cls.root / "transport.c"
        cls.shim.write_text("""#include <assert.h>
#include <stdint.h>
unsigned sends;
void raw_hid_send(uint8_t *data, uint8_t length) { assert(data); assert(length == 32); ++sends; }
""")
        cls.flags = ["-std=c11", "-Wall", "-Wextra", "-Werror", "-I", str(cls.root), "-I", str(PORT),
                     '-DQMK_KEYBOARD_H="qmk_mock.h"']
        cls.sources = [str(PORT / "protocol.c"), str(PORT / "keymap.c"), str(cls.shim)]
        library = cls.root / "protocol.so"
        subprocess.run(["cc", *cls.flags, "-shared", "-fPIC", *cls.sources, "-o", str(library)],
                       check=True, capture_output=True)
        cls.lib = ctypes.CDLL(str(library))
        cls.lib.alloy_vial_readonly.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t]
        cls.lib.alloy_vial_readonly.restype = ctypes.c_bool
        cls.lib.alloy_vial_keycode.argtypes = [ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8]
        cls.lib.alloy_vial_keycode.restype = ctypes.c_uint16
        cls.lib.raw_hid_receive.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_uint8]

    def exchange(self, request):
        self.assertLessEqual(len(request), 32)
        p = (ctypes.c_uint8 * 32).from_buffer_copy(request + bytes(32 - len(request)))
        self.assertTrue(self.lib.alloy_vial_readonly(p, 32))
        return bytes(p)

    def test_gui_discovery_sequence_and_definition_round_trip(self):
        self.assertEqual(struct.unpack(">H", self.exchange(b"\x01")[1:3])[0], 9)
        identity = self.exchange(b"\xfe\x00")
        version, uid = struct.unpack("<IQ", identity[:12])
        self.assertEqual(version, 6)
        self.assertEqual(uid, 0xe562319b8df014a7)
        self.assertEqual(identity[12:], bytes(20))
        size = struct.unpack("<I", self.exchange(b"\xfe\x01")[:4])[0]
        packed = b"".join(self.exchange(struct.pack("<BBI", 0xfe, 2, page))
                          for page in range((size + 31) // 32))
        self.assertEqual(packed[size:], bytes(len(packed) - size))
        self.assertEqual(json.loads(lzma.decompress(packed[:size])), json.loads((PORT / "vial.json").read_text()))
        self.assertEqual(self.exchange(b"\x11")[1], 4)
        self.assertEqual(self.exchange(b"\x0c"), b"\x0c" + bytes(31))
        self.assertEqual(self.exchange(b"\x0d"), b"\x0d" + bytes(31))
        self.assertEqual(self.exchange(b"\xfe\x09"), b"\xff" * 32)
        self.assertEqual(self.exchange(b"\xfe\x0d\x00"), bytes(32))

    def compiled_map(self):
        return b"".join(struct.pack(">H", self.lib.alloy_vial_keycode(layer, row, col))
                        for layer in range(4) for row in range(14) for col in range(8))

    def test_gui_reads_all_four_layers_in_28_byte_chunks(self):
        result = b""
        for offset in range(0, 896, 28):
            count = min(28, 896 - offset)
            response = self.exchange(struct.pack(">BHB", 0x12, offset, count))
            result += response[4:4 + count]
        self.assertEqual(result, self.compiled_map())
        self.assertEqual(struct.unpack(">H", result[3 * 8 * 2:3 * 8 * 2 + 2])[0], 0x4329)
        self.assertEqual(self.lib.alloy_vial_keycode(0, 11, 2), 0x5221)
        self.assertEqual(self.lib.alloy_vial_keycode(0, 11, 3), 0x5222)
        for layer in range(4):
            for col in range(5):
                self.assertEqual(self.lib.alloy_vial_keycode(layer, 7, col), 0)

    def test_keycode_reads_and_invalid_coordinates(self):
        for layer in range(4):
            for row in range(14):
                for col in range(8):
                    prefix = bytes((4, layer, row, col))
                    response = self.exchange(prefix)
                    self.assertEqual(response[:4], prefix)
                    self.assertEqual(response[4:6], struct.pack(">H", self.lib.alloy_vial_keycode(layer, row, col)))
                    self.assertEqual(response[6:], bytes(26))
        for coords in ((4, 0, 0), (0, 14, 0), (0, 0, 8), (255, 255, 255)):
            self.assertEqual(self.exchange(bytes((4, *coords))), b"\xff" + bytes(31))

    def test_buffer_boundaries_odd_offsets_and_no_overflow(self):
        expected = self.compiled_map()
        for offset in (*range(897), 65535):
            for count in (0, 1, 2, 27, 28, 29, 255):
                response = self.exchange(struct.pack(">BHB", 0x12, offset, count))
                if count > 28 or offset + count > 896:
                    self.assertEqual(response, b"\xff" + bytes(31))
                else:
                    self.assertEqual(response[4:4 + count], expected[offset:offset + count])
                    self.assertEqual(response[4 + count:], bytes(28 - count))

    def test_definition_pages_reject_out_of_range_and_high_word(self):
        size = struct.unpack("<I", self.exchange(b"\xfe\x01")[:4])[0]
        for page in ((size + 31) // 32, 65535, 65536, 0xffffffff):
            self.assertEqual(self.exchange(struct.pack("<BBI", 0xfe, 2, page)), b"\xff" + bytes(31))

    def test_all_mutation_commands_fail_closed_and_do_not_change_map(self):
        before = self.compiled_map()
        for command in range(256):
            if command not in (1, 2, 4, 12, 13, 17, 18, 254):
                self.assertEqual(self.exchange(bytes([command]) + b"\xa5" * 31), b"\xff" + bytes(31))
        for command in range(256):
            if command not in (0, 1, 2, 5, 9, 13):
                self.assertEqual(self.exchange(bytes([254, command]) + b"\xa5" * 30), b"\xff" + bytes(31))
        for value in (1, 3, 4, 5, 255):
            self.assertEqual(self.exchange(bytes([2, value])), b"\xff" + bytes(31))
        self.assertEqual(self.exchange(b"\xfe\x0d\x01"), b"\xff" + bytes(31))
        self.assertEqual(self.compiled_map(), before)
        self.assertEqual(self.exchange(b"\xfe\x05"), b"\x00\x00" + b"\xff" * 30)

    def test_transport_drops_invalid_lengths_without_reply_or_mutation(self):
        sends = ctypes.c_uint.in_dll(self.lib, "sends")
        for length in range(256):
            p = (ctypes.c_uint8 * 256)(*([0xa5] * 256))
            old = bytes(p)
            previous = sends.value
            self.lib.raw_hid_receive(p, length)
            self.assertEqual(sends.value, previous + (length == 32))
            if length != 32:
                self.assertEqual(bytes(p), old)
        self.assertFalse(self.lib.alloy_vial_readonly(None, 32))

    def test_parser_under_address_and_undefined_behavior_sanitizers(self):
        source = self.root / "stress.c"
        source.write_text('''#include "protocol.h"
#include <assert.h>
#include <string.h>
int main(void) {
    uint8_t guarded[34], before[34];
    uint32_t rng = 7;
    for (unsigned cmd = 0; cmd < 256; ++cmd) {
        for (unsigned sub = 0; sub < 256; ++sub) {
            for (unsigned i = 0; i < sizeof guarded; ++i) {
                rng = rng * 1664525u + 1013904223u;
                guarded[i] = rng >> 24;
            }
            guarded[1] = cmd;
            guarded[2] = sub;
            memcpy(before, guarded, sizeof guarded);
            assert(!alloy_vial_readonly(guarded + 1, 31));
            assert(!alloy_vial_readonly(guarded + 1, 33));
            assert(memcmp(before, guarded, sizeof guarded) == 0);
            assert(alloy_vial_readonly(guarded + 1, 32));
            assert(guarded[0] == before[0] && guarded[33] == before[33]);
        }
    }
    return 0;
}
''')
        executable = self.root / "stress"
        flags = ["-fsanitize=address,undefined", "-fno-omit-frame-pointer"]
        if sys.platform.startswith("linux"):
            flags += ["-no-pie"]
        run = subprocess.run(["cc", *self.flags, *flags, *self.sources, str(source), "-o", str(executable)],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        run = subprocess.run([str(executable)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
