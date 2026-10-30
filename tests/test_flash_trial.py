import importlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
trial = importlib.import_module("flash_trial")


def app():
    return struct.pack("<II", 0x200000e0, 0x2c1) + bytes(248)


def boot():
    return struct.pack("<48I", 0x20000780, 193, *([201] * 46)) + bytes(320)


def reply(op, value=0):
    data = bytearray(struct.pack("<IIH", 0x55aa00 | op, 0xfafafafa, value) + bytes(54))
    return data


class TrialTests(unittest.TestCase):
    def test_bounded_images_and_headers(self):
        self.assertEqual(trial.program_header(0x200, app())[:12], struct.pack("<III", 0x55aa05, 512, 4))
        trial.validate_image(boot() + app(), 0)
        for offset, data in [(64, app()), (0x7800, app()), (0, boot()), (512, b""),
                             (512, app()[:-1]), (0, boot()+app()+bytes(0x7800))]:
            with self.assertRaises(ValueError):
                trial.program_header(offset, data)

    def test_vector_validation(self):
        for offset, value in [(0, 0), (0, 0x20000808), (0, 0x200000e4),
                              (4, 0x2c0), (4, 0x7811), (4, 0x200)]:
            data = bytearray(app())
            struct.pack_into("<I", data, offset, value)
            with self.assertRaises(ValueError):
                trial.validate_image(data, 512)

    def test_completion_is_not_readback(self):
        raw = reply(5, 0x1234)
        raw[60:] = app()[-4:]
        result = trial.verify_completion(raw, app())
        self.assertTrue(result["last_word_echo_matches"])
        self.assertFalse(result["readback_verified"])
        self.assertFalse(result["checksum_domain_verified"])
        for index in (0, 4, 60):
            bad = bytearray(raw)
            bad[index] ^= 1
            with self.assertRaises(ValueError):
                trial.verify_completion(bad, app())

    def test_manifest_binary_and_source_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/"firmware").mkdir()
            source = root/"firmware/source.c"
            source.write_text("source")
            folder = root/"build/default"
            folder.mkdir(parents=True)
            (folder/"candidate-offset-0x200.bin").write_bytes(app())
            manifest = {"binary_sha256": trial.sha(app()),
                        "source_hashes": {"firmware/source.c": trial.sha(b"source")},
                        "keymap": "default", "memory": {"binary_load_address": 512,
                        "ram_reserved_through_heap_base": 1960}}
            (folder/"build-manifest.json").write_text(json.dumps(manifest))
            with patch.object(trial, "ROOT", root):
                data, plan = trial.candidate("default")
                self.assertEqual(data, app())
                self.assertEqual(plan["offset"], 512)
                source.write_text("stale")
                with self.assertRaises(ValueError):
                    trial.candidate("default")
                source.write_text("source")
                (folder/"candidate-offset-0x200.bin").write_bytes(app()+bytes(64))
                with self.assertRaises(ValueError):
                    trial.candidate("default")

    def test_command_allowlist_excludes_erase_and_security(self):
        dev = object.__new__(trial.TrialDevice)
        sent = []
        dev._write = sent.append
        for op in range(256):
            raw = struct.pack("<I", 0x55aa00 | op) + bytes(60)
            if op in (1, 6, 7):
                dev.send(raw)
            else:
                with self.assertRaises(ValueError):
                    dev.send(raw)
        self.assertEqual(len(sent), 3)

    def test_program_exact_stream_no_erase_or_reboot(self):
        dev = object.__new__(trial.TrialDevice)
        sent, events = [], []
        dev._write = sent.append
        end = reply(5)
        end[60:] = app()[-4:]
        responses = iter([reply(5), end])
        dev.receive = lambda: next(responses)
        with patch.object(trial.time, "sleep"):
            dev.program(512, app(), events.append)
        self.assertEqual(sent, [trial.program_header(512, app())] + [app()[i:i+64] for i in range(0,256,64)])
        self.assertEqual(events[-1]["event"], "completion")

    def test_no_payload_after_bad_prepare_ack(self):
        dev = object.__new__(trial.TrialDevice)
        sent = []
        dev._write = sent.append
        dev.receive = lambda: bytes(64)
        with patch.object(trial.time, "sleep"), self.assertRaises(ValueError):
            dev.program(512, app(), lambda e: None)
        self.assertEqual(len(sent), 1)

    def test_no_usb_write_for_invalid_image(self):
        dev = object.__new__(trial.TrialDevice)
        sent = []
        dev._write = sent.append
        with self.assertRaises(ValueError):
            dev.program(512, bytes(64), lambda e: None)
        self.assertEqual(sent, [])

    def test_apply_checks_chip_security_and_checksum_before_program(self):
        class Fake:
            def __init__(self, family=32, cs=0, checksum=0x27d1):
                self.family, self.cs, self.checksum = family, cs, checksum
                self.programs = []
            def query(self, op):
                raw = reply(op)
                if op == 1:
                    raw[8:10] = bytes((self.family, 2))
                    struct.pack_into("<H", raw, 14, self.cs)
                else:
                    struct.pack_into("<H", raw, 8, self.checksum)
                return raw
            def program(self, offset, data, event):
                self.programs.append((offset, data))
                return {"readback_verified": False}
        plan = {"offset": 512, "sha256": trial.sha(app())}
        for dev in (Fake(1), Fake(cs=0x5a5a), Fake(checksum=0)):
            with self.assertRaises(ValueError):
                trial.apply(dev, app(), plan, 0x27d1, lambda e: None)
            self.assertEqual(dev.programs, [])
        dev = Fake()
        self.assertTrue(trial.apply(dev, app(), plan, 0x27d1, lambda e: None)["left_in_isp"])
        self.assertEqual(dev.programs, [(512, app())])

    def test_invalid_plan_precedes_device_queries(self):
        with self.assertRaises(ValueError):
            trial.apply(None, app(), {"offset": 512, "sha256": "wrong"}, 0, lambda e: None)

    def test_failed_write_stops_without_retry(self):
        dev = object.__new__(trial.TrialDevice)
        writes = []
        def fail(payload):
            writes.append(payload)
            if len(writes) == 3:
                raise OSError("USB disconnected")
        dev._write = fail
        dev.receive = lambda: reply(5)
        with patch.object(trial.time, "sleep"), self.assertRaises(OSError):
            dev.program(512, app(), lambda e: None)
        self.assertEqual(len(writes), 3)
