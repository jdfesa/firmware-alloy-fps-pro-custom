import struct
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from hyperx_isp_hid import MacTrialDevice, metadata
import flash_trial as trial
import probe_hyperx as probe


def app():
    return struct.pack('<II', 0x200000e0, 0x2c1) + bytes(248)


def reply(op):
    return struct.pack('<II', 0x55aa00 | op, 0xfafafafa) + bytes(56)


class Hid:
    def __init__(self):
        self.items = [dict(path=b'isp', vendor_id=0x0c45, product_id=0x7010,
            release_number=0x100, interface_number=0, product_string='ISP')]
        self.sent, self.reads, self.opens = [], [], []
        self.responses = [b'\0' + reply(1)]
        self.closed = False
        self.short = False
    def enumerate(self, vid, pid):
        assert (vid, pid) == (0x0c45, 0x7010)
        return self.items
    def device(self): return self
    def open_path(self, path): self.opens.append(path)
    def get_product_string(self): return 'ISP'
    def close(self): self.closed = True
    def send_feature_report(self, data):
        self.sent.append(data)
        return 64 if self.short else len(data)
    def get_feature_report(self, rid, size):
        self.reads.append((rid, size))
        return self.responses.pop(0)


class MacTests(unittest.TestCase):
    def test_editable_advertises_public_desktop_discovery_marker(self):
        config = (Path(__file__).resolve().parents[1] / 'firmware/keyboards/hyperx/alloy_fps_pro/keymaps/vial_editable/config.h').read_text()
        self.assertIn('#undef SERIAL_NUMBER', config)
        self.assertIn('#define SERIAL_NUMBER "vial:f64c2b3c"', config)

    def test_metadata_never_opens(self):
        h=Hid(); self.assertEqual(metadata(h)[0]['path'], b'isp'); self.assertEqual(h.opens, [])

    def test_feature_framing_and_query(self):
        h=Hid(); d=MacTrialDevice(b'isp', h)
        with patch.object(probe.time, 'sleep'):
            self.assertEqual(d.query(1), reply(1))
        self.assertEqual(h.sent, [b'\0'+probe.command(1)])
        self.assertEqual(h.reads, [(0,65)])
        d.close(); self.assertTrue(h.closed)

    def test_identity_ambiguity_and_stale_path_fail_closed(self):
        for mutation in ('duplicate','revision','interface','path','vid'):
            h=Hid()
            if mutation=='duplicate': h.items.append(h.items[0].copy())
            elif mutation=='revision': h.items[0]['release_number']=0x101
            elif mutation=='interface': h.items[0]['interface_number']=1
            elif mutation=='vid': h.items[0]['vendor_id']=1
            else: h.items[0]['path']=b'changed'
            with self.assertRaises(ValueError): MacTrialDevice(b'isp', h)
            self.assertEqual(h.sent,[]); self.assertEqual(h.opens,[])

    def test_identity_changed_after_open_closes(self):
        h=Hid(); h.get_product_string=lambda:'changed'
        with self.assertRaises(ValueError): MacTrialDevice(b'isp',h)
        self.assertTrue(h.closed); self.assertEqual(h.sent,[])

    def test_no_generic_commands_erase_security_or_entry(self):
        h=Hid(); d=MacTrialDevice(b'isp',h)
        for op in range(256):
            if op in (1,6,7): continue
            with self.assertRaises(ValueError): d.send(struct.pack('<I',0x55aa00|op)+bytes(60))
        with self.assertRaises(ValueError): d.send(probe.ENTRY)
        self.assertEqual(h.sent,[])

    def test_bad_feature_framing_and_short_writes_never_retry(self):
        for response in (reply(1), b'\1'+reply(1), bytes(66)):
            h=Hid(); d=MacTrialDevice(b'isp',h); h.responses=[response]
            with self.assertRaises(ValueError): d.receive()
            self.assertEqual(len(h.reads),1)
        h=Hid(); d=MacTrialDevice(b'isp',h); h.short=True
        with self.assertRaises(OSError): d.send(probe.command(1))
        self.assertEqual(len(h.sent),1)

    def test_exact_program_stream_and_no_reboot(self):
        h=Hid(); d=MacTrialDevice(b'isp',h)
        h.responses=[b'\0'+reply(5), b'\0'+reply(5)]
        with patch.object(trial.time,'sleep'): d.program(512,app(),lambda e:None)
        expected=[trial.program_header(512,app())]+[app()[i:i+64] for i in range(0,256,64)]
        self.assertEqual(h.sent,[b'\0'+p for p in expected])

    def test_ranges_preserve_boot_maps_isp_before_any_write(self):
        h=Hid(); d=MacTrialDevice(b'isp',h)
        for offset,data in ((0,app()), (512,app()+bytes(0x7000)),(0x7000,app())):
            with self.assertRaises(ValueError): d.program(offset,data,lambda e:None)
        self.assertEqual(h.sent,[])

    def test_bad_prepare_ack_stops_before_payload(self):
        h=Hid(); d=MacTrialDevice(b'isp',h);h.responses=[b'\0'+bytes(64)]
        with patch.object(trial.time,'sleep'), self.assertRaises(ValueError):
            d.program(512,app(),lambda e:None)
        self.assertEqual(len(h.sent),1)
