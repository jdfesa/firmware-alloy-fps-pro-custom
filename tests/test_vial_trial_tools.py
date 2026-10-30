import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import test_vial_persistence as trial
from test_hyperx_hid import FakeHid


class TrialTests(unittest.TestCase):
    def test_only_exact_q_test_and_physical_lock_handshake(self):
        d=trial.TrialDevice(FakeHid())
        for code in (0x14,0x1d):
            p=bytes([5,0,2,1,0,code])+bytes(26)
            self.assertTrue(d.allowed(p))
            for index in (1,2,3,4,6):
                q=bytearray(p);q[index]^=1
                self.assertFalse(d.allowed(q))
        for command in (6,7,8):
            self.assertTrue(d.allowed(bytes([254,command])+bytes(30)))
        self.assertFalse(d.allowed(bytes([0x13])+bytes(31)))

    def test_baseline_and_only_one_key_change(self):
        b=bytearray(896);b[34:36]=b'\0\x14';after=trial.modified(bytes(b))
        self.assertEqual(after[:34],b[:34]);self.assertEqual(after[36:],b[36:])
        self.assertEqual(after[34:36],b'\0\x1d')
        with self.assertRaises(ValueError):trial.modified(bytes(896))
        with self.assertRaises(ValueError):trial.modified(bytes(900))

    def test_no_write_if_preimage_changed_or_locked(self):
        class Dev:
            def query(self,p):
                assert p == [254,5]
                return bytes(32)
        with patch.object(trial,'read_map',return_value=b'changed'):
            with self.assertRaises(ValueError):trial.set_q(Dev(),0x1d,b'before',b'after')
        with patch.object(trial,'read_map',return_value=b'before'):
            with self.assertRaises(ValueError):trial.set_q(Dev(),0x1d,b'before',b'after')

    def test_rejected_write_is_not_retried(self):
        class Dev:
            writes=0
            def query(self,p):
                if p == [254,5]:return b'\1\0'+bytes(30)
                self.writes+=1
                return b'\xff'+bytes(31)
        d=Dev()
        with patch.object(trial,'read_map',return_value=b'before'):
            with self.assertRaises(ValueError):trial.set_q(d,0x1d,b'before',b'after')
        self.assertEqual(d.writes,1)

    def test_unlock_timeout_has_no_map_write(self):
        class Dev:
            commands=[]
            def query(self,p):
                self.commands.append(p)
                assert p[0] == 254 and p[1] in (5,6,7)
                return bytes([0,0,2,0,3,0])+bytes(26)
        d=Dev()
        with self.assertRaises(TimeoutError):trial.unlock(d,seconds=0)
        self.assertEqual(d.commands,[[254,5],[254,6]])
