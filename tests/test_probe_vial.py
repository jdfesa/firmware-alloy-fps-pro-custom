import importlib
import json
import lzma
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
pv=importlib.import_module("probe_vial")

class VialProbeTests(unittest.TestCase):
    def test_only_read_commands_reach_transport(self):
        dev=object.__new__(pv.RawDevice)
        for op in (3,5,6,7,8,9,10,11,0x13,0xff):
            with self.assertRaises(ValueError): dev.query([op])
        for op in (3,4,6,7,8,10,11,12):
            with self.assertRaises(ValueError): dev.query([0xfe,op])
        with self.assertRaises(ValueError): dev.query(bytes(33))

    def test_discovery_definition_and_map_reads(self):
        compressed=lzma.compress(json.dumps({"name":"test READ-ONLY"}).encode())
        requests=[]
        class Fake:
            def query(self,p):
                requests.append(p)
                if p==[1]: return bytes([1,0,9])+bytes(29)
                if p==[0xfe,0]: return bytes([6])+bytes(31)
                if p==[0xfe,1]: return len(compressed).to_bytes(4,"little")+bytes(28)
                if p[:2]==[0xfe,2]:
                    off=(p[2]+p[3]*256)*32
                    return compressed[off:off+32].ljust(32,b"\0")
                if p==[0x11]: return bytes([0x11,4])+bytes(30)
                if p[0]==0x12: return bytes(p)+bytes(28)
                raise AssertionError(p)
        result=pv.inspect(Fake())
        self.assertEqual(result["map_bytes"],896)
        self.assertEqual(result["definition_name"],"test READ-ONLY")
        self.assertFalse(result["configuration_editing_tested"])
        self.assertFalse(result["gui_detection_tested"])
        self.assertTrue(all(p[0] in (1,0xfe,0x11,0x12) for p in requests))
