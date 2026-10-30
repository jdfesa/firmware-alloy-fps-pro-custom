import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


vendor = module("vendor_image")
infer = module("infer_matrix")
generator = module("generate_qmk")
readiness = module("check_port_readiness")
builder = module("build_firmware")


def record(kind, address=0, data=b""):
    row = bytes([len(data)]) + address.to_bytes(2, "big") + bytes([kind]) + data
    return b":" + (row + bytes([-sum(row) & 255])).hex().upper().encode() + b"\n"


class HexTests(unittest.TestCase):
    def test_checksum_and_address_records(self):
        data = record(4, data=b"\x00\x01") + record(0, 4, b"abc") + record(5, data=b"\0\0\0\xf5") + record(1)
        self.assertEqual(vendor.ihex(data), {0x10004: 97, 0x10005: 98, 0x10006: 99})

    def test_bad_checksum_rejected(self):
        with self.assertRaises(ValueError):
            vendor.ihex(b":010000000100\n:00000001FF\n")

    def test_missing_or_trailing_eof_rejected(self):
        for data in [record(0, data=b"a"), record(0, data=b"a") + record(1) + record(0, data=b"b")]:
            with self.assertRaises(ValueError):
                vendor.ihex(data)

    def test_conflicting_overlap_rejected(self):
        with self.assertRaises(ValueError):
            vendor.ihex(record(0, data=b"a") + record(0, data=b"b") + record(1))

    def test_resource_split_and_bounds(self):
        h, dll = b"HEX", b"MZ\0\0"
        compressed = zlib.compress(h + dll)
        resource = struct.pack("<III", len(h), len(dll), len(compressed)) + compressed
        self.assertEqual(vendor.unpack_resource(resource), (h, dll))
        with self.assertRaises(ValueError):
            vendor.unpack_resource(resource[:-1])


class FirmwareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads((ROOT / "hardware/matrix-inference.json").read_text())
        cls.default, cls.maps, cls.active = generator.layers(cls.matrix)

    def test_87_physical_keys_and_42_selected(self):
        self.assertEqual(sum(key != "KC_NO" for key in self.default[0]), 87)
        self.assertEqual(len(self.active), 42)
        self.assertEqual(sum(key != "KC_NO" for key in self.maps[0]), 42)
        self.assertEqual(len(self.maps), 4)

    def test_special_zero_is_up_not_a_hole(self):
        up = self.matrix["entries"][13 * 8]
        self.assertEqual((up["raw"], up["special"], up["usage"]), (0, True, 0x52))
        self.assertEqual(self.default[0][13 * 8], "KC_UP")

    def test_dead_number_keys_and_unused_positions_always_disabled(self):
        selected = {r * 8 + c for r, c in self.active}
        for layer in self.maps:
            for i, code in enumerate(layer):
                if i not in selected:
                    self.assertEqual(code, "KC_NO")
            for col in range(5):
                self.assertEqual(layer[7 * 8 + col], "KC_NO")

    def test_layer_entries_and_numbers_accessible_elsewhere(self):
        self.assertEqual(self.maps[0][3 * 8], "LT(NAV, KC_ESC)")
        self.assertEqual(self.maps[0][11 * 8 + 2], "MO(NUM)")
        self.assertEqual(self.maps[0][11 * 8 + 3], "MO(SYM)")
        for key in ["KC_" + ch for ch in "1234567890"]:
            self.assertIn(key, self.maps[1])
        for key in ["KC_LEFT", "KC_RGHT", "KC_UP", "KC_DOWN", "KC_BSPC", "KC_ENT"]:
            self.assertIn(key, self.maps[3])

    def test_rows_cols_do_not_overlap_or_duplicate(self):
        pins = self.matrix["rows"] + self.matrix["cols"]
        self.assertEqual(len(pins), len(set(pins)))
        self.assertEqual(len(self.matrix["rows"]), 14)
        self.assertEqual(len(self.matrix["cols"]), 8)

    def test_generated_sources_current(self):
        for name, maps, custom in [("default", self.default + [["KC_TRNS" if k != "KC_NO" else "KC_NO" for k in self.default[0]]], False), ("custom42", self.maps, True)]:
            actual = (generator.DEST / "keymaps" / name / "keymap.c").read_text()
            self.assertEqual(actual, generator.c_source(maps, custom))

    def test_not_flash_ready(self):
        status = json.loads((ROOT / "hardware/validation-status.json").read_text())
        self.assertIn("original_recovery_verified", readiness.missing(status))
        # First-flash evidence now supports the installed startup path; the
        # general checklist still lacks OEM recovery and full matrix validation.
        self.assertTrue(status["jumploader_path_verified"])
        evidence = json.loads((ROOT / "hardware/first-flash-evidence.json").read_text())
        self.assertTrue(evidence["cold_plug_escape_rescue_verified"])
        self.assertTrue(evidence["qmk_after_escape_released"]["user_typing_confirmed"])
        self.assertFalse(evidence["failed_application_recovery_tested"])
        self.assertEqual(readiness.missing({key: "true" for key in readiness.REQUIRED}), list(readiness.REQUIRED))
        run = subprocess.run(["python3", str(ROOT / "scripts/check_port_readiness.py")], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertIn("NOT READY TO FLASH", run.stdout)

    def test_build_tools_reject_flash_commands_before_loading_dependencies(self):
        for argv in [["scripts/qmk_build_cli.py", "flash"], ["scripts/build_firmware.py", "--keymap", "custom42:flash"]]:
            run = subprocess.run(["python3", *argv], cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)

    def test_memory_report_enforces_flash_offset_and_ram_bounds(self):
        sections = {".vectors_512_aligned": {"address": 0x200}, ".data": {"size": 280}, ".bss": {"size": 972}}
        symbols = {"__ram0_base__": 0x20000000, "__ram0_end__": 0x20000800, "__heap_base__": 0x200007A8,
                   "__heap_end__": 0x20000800, "__main_stack_size__": 224, "__process_stack_size__": 480}
        binary = struct.pack("<II", 0x200000E0, 0x391) + bytes(500)
        report = builder.memory_report(sections, symbols, binary)
        self.assertEqual(report["binary_load_address"], 512)
        self.assertTrue(report["requires_jumploader"])
        self.assertEqual(report["heap_bytes"], 88)
        with self.assertRaises(ValueError):
            builder.memory_report({**sections, ".vectors_512_aligned": {"address": 0}}, symbols, binary)
        with self.assertRaises(ValueError):
            builder.memory_report(sections, {**symbols, "__heap_base__": 0x20001000}, binary)
        with self.assertRaises(ValueError):
            builder.memory_report(sections, symbols, binary + bytes(30208))
        for sp, pc in [(0x20000000, 0x391), (0x200000E1, 0x391), (0x200000E0, 0x1FFF0009),
                       (0x200000E0, 0x201), (0x200000E0, 0x390)]:
            with self.assertRaises(ValueError):
                builder.memory_report(sections, symbols, struct.pack("<II", sp, pc) + bytes(500))

    def test_recovery_source_and_no_invalid_vial_rule(self):
        keyboard = json.loads((generator.DEST / "keyboard.json").read_text())
        self.assertTrue(keyboard["features"]["bootmagic"])
        self.assertEqual(self.default[0][0], "KC_ESC")
        rules = (generator.DEST / "rules.mk").read_text()
        self.assertNotIn("\nVIAL_ENABLE =", rules)

    @unittest.skipUnless(shutil.which("gcc"), "host GCC unavailable")
    def test_c_keymap_syntax_and_data_on_host_not_arm_qmk(self):
        # This shim validates C tables, not QMK firmware, USB, timing or MCU linkage.
        enum = {name: value for value, name in generator.HID.items() if name.startswith("KC_")}
        enum["KC_TRNS"] = 1
        with tempfile.TemporaryDirectory(prefix="alloy-host-") as folder:
            base = Path(folder)
            header = base / "qmk_mock.h"
            header.write_text("#include <stdint.h>\n#define MATRIX_ROWS 14\n#define MATRIX_COLS 8\n#define PROGMEM\n"
                              + "enum {" + ",".join(f"{key}={value}" for key, value in enum.items()) + "};\n"
                              + "#define S(k) (0x0200u | (k))\n#define MO(l) (0x5220u | (l))\n#define LT(l,k) (0x4000u | ((l)<<8) | (k))\n")
            for name in ("default", "custom42", "custom42_fn"):
                source = generator.DEST / "keymaps" / name / "keymap.c"
                subprocess.run(["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-fsyntax-only",
                                f'-DQMK_KEYBOARD_H="{header}"', str(source)], check=True, capture_output=True)
            program = base / "check.c"
            source = generator.DEST / "keymaps/custom42/keymap.c"
            program.write_text(f'#include "{source}"\n#include <assert.h>\nint main(void) {{\n'
                               'unsigned count=0; for(unsigned r=0;r<14;r++) for(unsigned c=0;c<8;c++) count += keymaps[0][r][c]!=KC_NO;\n'
                               'assert(count==42); assert(sizeof(keymaps)/sizeof(keymaps[0])==4);\n'
                               'for(unsigned l=0;l<4;l++) for(unsigned c=0;c<5;c++) assert(keymaps[l][7][c]==KC_NO);\n'
                               'assert(keymaps[NUM][2][1]==KC_1); assert(keymaps[NAV][3][6]==KC_LEFT);\n'
                               'assert(keymaps[BASE][11][2]==0x5221); assert(keymaps[BASE][11][3]==0x5222); return 0; }\n')
            executable = base / "host-check"
            subprocess.run(["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror", f'-DQMK_KEYBOARD_H="{header}"', str(program), "-o", str(executable)], check=True, capture_output=True)
            subprocess.run([str(executable)], check=True)

    @unittest.skipUnless((ROOT / "artifacts/analysis/FPS_Pro_v2112.analysis-only.bin").exists(), "proprietary local input absent")
    def test_inference_matches_exact_local_image(self):
        self.assertEqual(infer.infer((ROOT / "artifacts/analysis/FPS_Pro_v2112.analysis-only.bin").read_bytes()), self.matrix)


if __name__ == "__main__":
    unittest.main()
