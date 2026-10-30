import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from hyperx_hid import HidRawDevice, inventory


class FakeHid:
    def __init__(self):
        self.items = [dict(vendor_id=0xfeed,product_id=0xa11f,usage_page=0xff60,usage=0x61,
                           path=b'raw',product_string='Alloy FPS Pro Vial EDITABLE TEST')]
        self.items += [dict(self.items[0],path=b'keyboard',usage_page=1,usage=6)]
        self.writes = []
        self.closed = False
        self.response = [1,0,9]+[0]*29
        self.short_write = False
    def enumerate(self, vid, pid):
        assert (vid,pid) == (0xfeed,0xa11f)
        return self.items
    def device(self): return self
    def open_path(self,path): assert path == b'raw'
    def get_product_string(self): return 'Alloy FPS Pro Vial EDITABLE TEST'
    def close(self): self.closed = True
    def write(self,p):
        self.writes.append(p)
        return 1 if self.short_write else len(p)
    def read(self,size,timeout):
        assert (size,timeout) == (32,2000)
        return self.response


class HidTests(unittest.TestCase):
    def test_only_configuration_collection_selected(self):
        h=FakeHid();self.assertEqual(len(inventory(h)),1)
        d=HidRawDevice(h);self.assertEqual(d.query([1])[:3],b'\x01\0\x09')
        self.assertEqual(h.writes,[bytes([0,1])+bytes(31)]);d.close();self.assertTrue(h.closed)
    def test_ambiguity_or_unrecognized_product_rejected(self):
        h=FakeHid();h.items.append(h.items[0].copy())
        with self.assertRaises(ValueError):HidRawDevice(h)
        h=FakeHid();h.items[0]['product_string']='different device'
        with self.assertRaises(ValueError):HidRawDevice(h)
    def test_no_mutations_switch_capture_or_boot_commands(self):
        h=FakeHid();d=HidRawDevice(h)
        for p in ([5],[0x13],[0xfe,6],[0xfe,7],[0xfe,8],[0xb],[2,3],[0]*33):
            with self.assertRaises(ValueError):d.query(p)
        self.assertEqual(h.writes,[])
    def test_failures_never_retry(self):
        h=FakeHid();d=HidRawDevice(h);h.response=[]
        with self.assertRaises(TimeoutError):d.query([1])
        self.assertEqual(len(h.writes),1)
        h.short_write=True
        with self.assertRaises(OSError):d.query([1])
        self.assertEqual(len(h.writes),2)
