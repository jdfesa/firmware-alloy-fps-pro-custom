import unittest
from unittest.mock import patch
from test_firmware import module

probe = module("probe_hyperx")


class ProbeTests(unittest.TestCase):
    def test_decode_observed_family_and_security(self):
        raw = bytes.fromhex("01aa5500fafafafa200200000200000084858687") + bytes(44)
        self.assertEqual(probe.decode_version(raw)["family"], "SN32F26x")
        self.assertEqual(probe.decode_version(raw)["security_level"], "CS0")

    def test_return_waits_for_reenumeration_and_times_out(self):
        target = {"port": "1-6", "vid": "0951", "pid": "16d2"}
        with patch.object(probe, "inventory", side_effect=[[], [], [target]]), patch.object(probe.time, "sleep"):
            self.assertEqual(probe.wait_for_oem("1-6", 3), [target])
        with patch.object(probe, "inventory", return_value=[]), patch.object(probe.time, "sleep"):
            self.assertEqual(probe.wait_for_oem("1-6", 3), [])

    def test_only_diagnostic_commands(self):
        for op in range(256):
            if op in (1, 6, 7):
                self.assertEqual(len(probe.command(op)), 64)
            else:
                with self.assertRaises(ValueError):
                    probe.command(op)

    def test_strict_ack(self):
        for bad in (bytes(64), bytes.fromhex("01aa5500fafafafa"), probe.command(1)):
            with self.assertRaises(ValueError):
                probe.parse_reply(bad, 1)
        good = bytes.fromhex("01aa5500fafafafa") + bytes(56)
        self.assertEqual(probe.parse_reply(good, 1), good)
        with self.assertRaises(ValueError):
            probe.parse_reply(good, 6)

    def test_selection_rejects_other_device_port_interface_ambiguity(self):
        target = {"port": "1-6", "vid": "0951", "pid": "16d2"}
        other = {"port": "1-7", "vid": "feed", "pid": "1234"}
        self.assertEqual(probe.select([target, other], "1-6", {probe.OEM}), target)
        for devices in ([other], [], [target, target]):
            with self.assertRaises(ValueError):
                probe.select(devices, "1-6", {probe.OEM})

    def test_return_attempted_when_query_fails(self):
        item = {"port": "1-6", "vid": "0951", "pid": "16d2", "bcdDevice": "2112"}
        class Fake:
            sent = []
            def __init__(self, item): self.item = item
            def send(self, data): self.sent.append(data)
            def query(self, op): raise OSError("simulated timeout")
            def close(self): pass
        with patch.object(probe, "inventory", return_value=[item]), patch.object(probe, "FeatureDevice", Fake), patch.object(probe.time, "sleep"):
            result = probe.cycle("1-6")
        self.assertEqual(Fake.sent, [probe.ENTRY, probe.command(7)])
        self.assertIn("error", result)
        self.assertFalse(result["flash_written"])
        self.assertFalse(result["original_recovery_verified"])
