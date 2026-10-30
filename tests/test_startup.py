import json
import struct
import unittest
from test_firmware import ROOT, module

startup = module("build_jumploader")
generator = module("generate_qmk")


class StartupTests(unittest.TestCase):
    def valid(self):
        return struct.pack("<48I", 0x20000780, 193, *([201] * 46)) + bytes(244)

    def test_valid_vectors_and_padding_boundary(self):
        self.assertEqual(startup.validate(self.valid())["raw_bytes"], 436)

    def test_reject_oversize_short_sp_non_thumb_outside_proxy(self):
        valid = self.valid()
        cases = [valid + bytes(100), valid[:100]]
        for offset, value in [(0, 0x20000800), (4, 192), (4, 0x391), (8, 0), (12, 203)]:
            bad = bytearray(valid)
            struct.pack_into("<I", bad, offset, value)
            cases.append(bad)
        for bad in cases:
            with self.assertRaises(ValueError):
                startup.validate(bad)

    def test_optional_function_row_does_not_modify_42_base(self):
        matrix = json.loads((ROOT / "hardware/matrix-inference.json").read_text())
        _, maps, _ = generator.layers(matrix)
        result = generator.with_function_row(matrix, maps)
        self.assertEqual(sum(k != "KC_NO" for k in maps[0]), 42)
        self.assertEqual(sum(k != "KC_NO" for k in result[0]), 54)
        self.assertEqual(len(result), 4)
        for layer in result:
            for i in range(1, 13):
                self.assertIn(f"KC_F{i}", layer)
            self.assertEqual(layer[56:61], ["KC_NO"] * 5)
        self.assertEqual((generator.DEST / "keymaps/custom42_fn/keymap.c").read_text(), generator.c_source(result, True))
