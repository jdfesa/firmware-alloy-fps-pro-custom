#!/usr/bin/env python3
"""Explicit, bounded HyperX Q->Z persistence trial; NOT a firmware installer.

No arbitrary key/command/interface arguments. Default is read-only verification.
Unlock is the Vial physical key handshake, NOT MCU security/unprotect.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

from hyperx_hid import HidRawDevice, read_allowed

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT/'build/trial/mac-q-to-z.json'
UID = bytes.fromhex('a714f08d9b3162e6')
OFFSET = (2*8+1)*2  # layer 0, physical Q [2,1]


class TrialDevice(HidRawDevice):
    def allowed(self, p):
        # Only the two exact one-key mutations and physical unlock/lock.
        return (read_allowed(p) or
                (p[:2] in (b'\xfe\x06', b'\xfe\x07', b'\xfe\x08') and not any(p[2:])) or
                (p[:5] == bytes([5,0,2,1,0]) and p[5] in (0x14,0x1d) and not any(p[6:])))


def read_map(dev):
    identity = dev.query([0xfe,0])
    if identity[:4] != bytes([6,0,0,0]) or identity[4:12] != UID:
        raise ValueError('wrong Vial protocol or design UID')
    if dev.query([0x11])[1] != 4:
        raise ValueError('wrong layer count')
    result = b''
    for offset in range(0,896,28):
        prefix = bytes([0x12,offset>>8,offset&255,28])
        response = dev.query(prefix)
        if response[:4] != prefix:
            raise ValueError('invalid map reply')
        result += response[4:32]
    return result


def modified(before):
    if len(before) != 896 or before[OFFSET:OFFSET+2] != b'\0\x14':
        raise ValueError('baseline is not Q at physical [2,1]')
    return before[:OFFSET]+b'\0\x1d'+before[OFFSET+2:]


def unlock(dev, seconds=45):
    state = dev.query([0xfe,5])
    if state[2:6] != bytes([2,0,3,0]):
        raise ValueError('unexpected physical unlock keys')
    dev.query([0xfe,6])
    print('HOLD TAB + CAPS LOCK ON HYPERX NOW (up to 45s)',flush=True)
    end = time.monotonic()+seconds
    while time.monotonic() < end:
        time.sleep(0.11)
        p = dev.query([0xfe,7])
        if p[:2] == b'\x01\0':
            print('PHYSICAL UNLOCK VERIFIED; release keys',flush=True)
            return
    raise TimeoutError('physical unlock not completed; no map write')


def set_q(dev, code, expected_before, expected_after):
    if read_map(dev) != expected_before:
        raise ValueError('map changed since preflight; refusing overwrite')
    if dev.query([0xfe,5])[:2] != b'\x01\0':
        raise ValueError('keyboard is locked; no write')
    request = bytes([5,0,2,1,0,code])
    start = time.monotonic()
    response = dev.query(request)  # one write only, never retry on timeout/error
    elapsed = time.monotonic()-start
    if response != request+bytes(26):
        raise ValueError('SET_KEYCODE rejected; stop and inspect, do not retry')
    if read_map(dev) != expected_after:
        raise ValueError('full map readback mismatch; stop and inspect')
    return elapsed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--action', choices=('verify','q-to-z','restore'), default='verify')
    args = parser.parse_args()
    dev = TrialDevice()
    attempted_unlock = False
    try:
        current = read_map(dev)
        if args.action == 'q-to-z':
            # No overwrite of an unfinished trial's baseline.
            if STATE.exists():
                raise ValueError('trial record exists; verify/restore it first')
            target = modified(current)
            record = {'before_hex':current.hex(),'before_sha256':hashlib.sha256(current).hexdigest(),
                      'test_sha256':hashlib.sha256(target).hexdigest(),'stage':'prepared_no_write'}
            STATE.parent.mkdir(parents=True,exist_ok=True)
            STATE.write_text(json.dumps(record,indent=2)+'\n')
        else:
            record = json.loads(STATE.read_text())
            before = bytes.fromhex(record['before_hex'])
            if hashlib.sha256(before).hexdigest() != record['before_sha256']:
                raise ValueError('baseline record corrupted')
            test = modified(before)
            if hashlib.sha256(test).hexdigest() != record['test_sha256']:
                raise ValueError('test record corrupted')
            if args.action == 'verify':
                if current not in (before,test):
                    raise ValueError('map differs from both expected snapshots')
                print(json.dumps({'map_matches':'Q restored/original' if current==before else 'Q->Z',
                                  'map_sha256':hashlib.sha256(current).hexdigest(),
                                  'unlocked':bool(dev.query([0xfe,5])[0]),
                                  'cold_reconnect_requires_user_confirmation':True},indent=2))
                return
            if current != test:
                raise ValueError('current map is not exactly the saved Q->Z test; refusing overwrite')
            target = before
        attempted_unlock = True
        unlock(dev)
        record['stage'] = 'write_about_to_be_sent'
        STATE.write_text(json.dumps(record,indent=2)+'\n')
        seconds = set_q(dev, 0x1d if args.action=='q-to-z' else 0x14, current, target)
        record['stage'] = 'Q->Z readback verified' if args.action=='q-to-z' else 'Q restored readback verified'
        record['last_write_seconds'] = seconds
        STATE.write_text(json.dumps(record,indent=2)+'\n')
        print(json.dumps({'result':record['stage'],'write_seconds':seconds,
                          'map_sha256':hashlib.sha256(target).hexdigest()},indent=2),flush=True)
    finally:
        try:
            if attempted_unlock:
                dev.query([0xfe,8])  # relock even after timeout/rejection
        finally:
            dev.close()


if __name__ == '__main__':
    main()
