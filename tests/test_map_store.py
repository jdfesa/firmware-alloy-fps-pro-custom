"""C store + fake NOR medium. No device, flash geometry or firmware integration."""
import ctypes
import json
from pathlib import Path
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

from test_firmware import ROOT, generator

SOURCE = ROOT / "firmware/experiments/vial_store"
OK, INVALID, IO_ERROR, NOT_MOUNTED, AMBIGUOUS = range(5)


class Store(ctypes.Structure):
    _fields_ = [("generation", ctypes.c_uint32), ("bank", ctypes.c_int8), ("mounted", ctypes.c_bool)]


@unittest.skipUnless(shutil.which("cc"), "host C compiler unavailable")
class MapStoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="alloy-store-")
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.root = Path(cls.tmp.name)
        codes = {name: value for value, name in generator.HID.items() if name.startswith("KC_")}
        codes["KC_TRNS"] = 1
        (cls.root / "qmk_mock.h").write_text(
            "#pragma once\n#include <stdint.h>\n#define MATRIX_ROWS 14\n#define MATRIX_COLS 8\n#define PROGMEM\n"
            + "enum {" + ",".join(f"{key}={value}" for key, value in codes.items()) + "};\n"
            + "#define S(k) (0x0200u | (k))\n#define MO(l) (0x5220u | (l))\n"
            + "#define LT(l,k) (0x4000u | ((l)<<8) | (k))\n")
        # Actual compiled default map, not a second hand-maintained fixture.
        keymap = ROOT / "firmware/keyboards/hyperx/alloy_fps_pro/keymaps/custom42_fn/keymap.c"
        (cls.root / "test_keymap.h").write_text(keymap.read_text())
        cls.flags = ["-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-I", str(SOURCE),
                     "-I", str(cls.root), '-DQMK_KEYBOARD_H="qmk_mock.h"']
        cls.sources = [str(SOURCE / "map_store.c"), str(ROOT / "tests/map_store_harness.c")]
        library = cls.root / "store.so"
        subprocess.run(["cc", *cls.flags, "-shared", "-fPIC", *cls.sources, "-o", str(library)],
                       check=True, capture_output=True)
        cls.lib = ctypes.CDLL(str(library))
        cls.lib.patch_map.argtypes = [ctypes.c_uint16, ctypes.POINTER(ctypes.c_uint8), ctypes.c_uint8]
        cls.lib.dump_map.argtypes = [ctypes.POINTER(ctypes.c_uint8)]
        cls.lib.alloy_map_get.argtypes = [ctypes.POINTER(Store), ctypes.c_uint16, ctypes.POINTER(ctypes.c_uint16)]
        cls.lib.alloy_map_mount.argtypes = [ctypes.POINTER(Store)]

    def setUp(self):
        self.lib.reset_medium()
        self.medium = (ctypes.c_uint8 * 2048).in_dll(self.lib, "medium")
        self.store = Store.in_dll(self.lib, "store")
        self.assertEqual(self.lib.mount_map(), OK)
        self.default = self.dump()

    def integer(self, name):
        return ctypes.c_int.in_dll(self.lib, name)

    def patch(self, offset, data):
        return self.lib.patch_map(offset, (ctypes.c_uint8 * len(data)).from_buffer_copy(data), len(data))

    def dump(self):
        out = (ctypes.c_uint8 * 896)()
        self.lib.dump_map(out)
        return bytes(out)

    def bank(self, number, generation, data=None, schema=0x01040e08):
        payload = self.default if data is None else data
        prefix = struct.pack("<III", 0x314d5641, schema, generation)
        crc = zlib.crc32(prefix + payload)
        contents = prefix + struct.pack("<I", crc) + b"\xff" * 12 + b"CMIT" + payload
        self.medium[number * 1024:(number + 1) * 1024] = contents + b"\xff" * (1024 - len(contents))

    def test_defaults_and_streaming_state(self):
        self.assertEqual(ctypes.sizeof(Store), 8)
        self.assertEqual(self.store.bank, -1)
        self.assertEqual(self.integer("mutations").value, 0)
        self.assertEqual(len(self.dump()), 896)
        for layer in range(4):
            self.assertEqual(self.default[(layer * 112 + 56) * 2:(layer * 112 + 61) * 2], bytes(10))

    def test_patch_roundtrip_odd_offsets_and_bank_alternation(self):
        expected = bytearray(self.default)
        for offset, data in ((34, b"\x00\x05"), (35, b"\x06"), (34, b"\x02\x1e"), (35, b"\x1f\x00\x07")):
            old_bank = self.store.bank
            self.assertEqual(self.patch(offset, data), OK)
            self.assertNotEqual(self.store.bank, old_bank)
            expected[offset:offset + len(data)] = data
            self.assertEqual(self.dump(), expected)
            self.assertEqual(self.lib.mount_map(), OK)
            self.assertEqual(self.dump(), expected)

    def test_noop_and_invalid_requests_never_mutate(self):
        self.assertEqual(self.patch(34, self.default[34:36]), OK)
        self.assertEqual(self.patch(896, b""), OK)
        for offset, data in ((897, b""), (895, bytes(2)), (65535, bytes(1)), (0, bytes(29)),
                             (34, b"\xff\xff"), (34, b"\x52\x7c"), (34, b"\x52\x24"),
                             (112, b"\x00\x04")):
            self.assertEqual(self.patch(offset, data), INVALID)
        self.assertEqual(self.lib.patch_map(34, None, 1), INVALID)
        self.assertEqual(self.integer("mutations").value, 0)
        self.assertEqual(bytes(self.medium), b"\xff" * 2048)
        self.assertEqual(self.lib.alloy_map_mount(None), INVALID)
        out = ctypes.c_uint16(1234)
        self.assertEqual(self.lib.alloy_map_get(ctypes.byref(self.store), 448, ctypes.byref(out)), INVALID)
        self.assertEqual(out.value, 1234)

    def test_crc_and_format_are_independently_decodable(self):
        self.assertEqual(self.patch(34, b"\x00\x05"), OK)
        bank = bytes(self.medium[:1024])
        self.assertEqual(bank[:4], b"AVM1")
        self.assertEqual(bank[28:32], b"CMIT")
        self.assertEqual(struct.unpack("<I", bank[12:16])[0], zlib.crc32(bank[:12] + bank[32:928]))
        self.assertEqual(bank[16:28] + bank[928:], b"\xff" * 108)

    def test_corruption_and_unknown_schema_fall_back_without_writes(self):
        for byte in (0, 4, 8, 12, 16, 24, 28, 32, 927):
            with self.subTest(byte=byte):
                self.bank(0, 5)
                self.bank(1, 6)
                self.medium[1024 + byte] ^= 1
                self.assertEqual(self.lib.mount_map(), OK)
                self.assertEqual(self.store.bank, 0)
        self.bank(0, 5, schema=0x02040e08)
        self.bank(1, 6, schema=0x02040e08)
        self.assertEqual(self.lib.mount_map(), OK)
        self.assertEqual(self.store.bank, -1)
        self.assertEqual(self.dump(), self.default)
        self.assertEqual(self.integer("mutations").value, 0)

    def test_valid_crc_does_not_bypass_keycode_policy(self):
        for offset, code in ((34, b"\xff\xff"), (112, b"\x00\x04")):
            data = bytearray(self.default)
            data[offset:offset + 2] = code
            self.bank(0, 1, data)
            self.assertEqual(self.lib.mount_map(), OK)
            self.assertEqual(self.store.bank, -1)

    def test_generation_wrap_and_ambiguity(self):
        for a, b, result, winner in ((0xffffffff, 0, OK, 1), (0, 0xffffffff, OK, 0),
                                      (8, 8, AMBIGUOUS, -1), (1, 5, AMBIGUOUS, -1),
                                      (0, 0x80000000, AMBIGUOUS, -1)):
            self.bank(0, a)
            self.bank(1, b)
            self.assertEqual(self.lib.mount_map(), result)
            self.assertEqual(self.store.bank, winner)
            self.assertEqual(self.store.mounted, result == OK)
        self.bank(0, 0xffffffff)
        self.medium[1024:] = b"\xff" * 1024
        self.assertEqual(self.lib.mount_map(), OK)
        self.assertEqual(self.patch(34, b"\x00\x05"), OK)
        self.assertEqual(self.store.generation, 0)
        self.assertEqual(self.lib.mount_map(), OK)
        self.assertEqual(self.store.bank, 1)

    def test_every_program_bit_erase_byte_and_read_cut(self):
        cases = self.lib.exercise_powercuts()
        self.assertGreater(cases, 8500)
        for code in (5, 6):
            self.assertEqual(self.patch(34, bytes([0, code])), OK)
            self.assertGreater(self.lib.exercise_powercuts(), 8500)

    def test_failure_requires_remount_and_retry_is_possible(self):
        for step in (0, 4, 100, 228, 229):
            self.lib.reset_medium()
            self.assertEqual(self.lib.mount_map(), OK)
            self.integer("fail_mutation").value = step
            self.integer("torn").value = 16
            self.assertEqual(self.patch(34, b"\x00\x05"), IO_ERROR)
            self.assertEqual(self.patch(34, b"\x00\x06"), NOT_MOUNTED)
            self.integer("fail_mutation").value = -1
            ctypes.c_bool.in_dll(self.lib, "powered").value = True
            self.assertEqual(self.lib.mount_map(), OK)
            self.assertEqual(self.patch(34, b"\x00\x06"), OK)
            self.assertEqual(self.dump()[34:36], b"\x00\x06")

    def test_read_errors_and_unacknowledged_or_lying_backend(self):
        # A read error must not be interpreted as empty storage/defaults.
        self.integer("fail_read").value = self.integer("reads").value
        self.assertEqual(self.lib.mount_map(), IO_ERROR)
        self.assertFalse(self.store.mounted)
        # A backend claiming success without programming header/CRC/commit fails.
        for operation in (1, 2, 3, 228, 229):
            self.lib.reset_medium()
            self.assertEqual(self.lib.mount_map(), OK)
            self.integer("lie_mutation").value = operation
            self.assertEqual(self.patch(34, b"\x00\x05"), IO_ERROR)
            self.assertFalse(self.store.mounted)
        # Failed erase verification on a previously used inactive bank.
        self.lib.reset_medium()
        self.assertEqual(self.lib.mount_map(), OK)
        self.assertEqual(self.patch(34, b"\x00\x05"), OK)
        self.assertEqual(self.patch(34, b"\x00\x06"), OK)
        self.integer("lie_mutation").value = self.integer("mutations").value
        self.assertEqual(self.patch(34, b"\x00\x07"), IO_ERROR)

    def test_random_edits_against_bytearray_model(self):
        rng = random.Random(754)
        enabled = [i for i in range(448) if self.default[2 * (i % 112):2 * (i % 112) + 2] != b"\x00\x00"]
        expected = bytearray(self.default)
        for _ in range(250):
            index = rng.choice(enabled)
            value = struct.pack(">H", rng.choice([0, 1, 4, 0x31, 0xe1, 0x021e, 0x5223, 0x4329]))
            self.assertEqual(self.patch(index * 2, value), OK)
            expected[index * 2:index * 2 + 2] = value
            self.assertEqual(self.lib.mount_map(), OK)
            self.assertEqual(self.dump(), expected)

    def test_powercuts_under_address_and_undefined_behavior_sanitizers(self):
        executable = self.root / "stress"
        flags = ["-fsanitize=address,undefined", "-fno-omit-frame-pointer"]
        if sys.platform.startswith("linux"):
            flags += ["-no-pie"]
        run = subprocess.run(["cc", *self.flags, *flags, *self.sources, "-o", str(executable)],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        run = subprocess.run([str(executable)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
