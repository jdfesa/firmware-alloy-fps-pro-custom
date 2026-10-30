#!/usr/bin/env python3
"""Narrow hidapi transport for the experimental HyperX configuration interface.

Never opens the boot keyboard collection or requests live switch state.
Dependency is optional, local to artifacts/tools/macos-hid; no install on import.
"""
from pathlib import Path
import sys

VID, PID, USAGE_PAGE, USAGE = 0xFEED, 0xA11F, 0xFF60, 0x61
PRODUCTS = {'Alloy FPS Pro Vial READ-ONLY', 'Alloy FPS Pro Vial EDITABLE TEST'}


def load_hid():
    local = Path(__file__).resolve().parents[1]/'artifacts/tools/macos-hid'
    if local.is_dir():
        sys.path.insert(0, str(local))
    import hid
    return hid


def inventory(hid):
    return [d for d in hid.enumerate(VID, PID)
            if (d.get('vendor_id'), d.get('product_id'), d.get('usage_page'), d.get('usage'))
            == (VID, PID, USAGE_PAGE, USAGE) and d.get('product_string') in PRODUCTS]


def read_allowed(p):
    return (p[0] in (1, 4, 0x11, 0x12) or
            (p[0] == 0xFE and p[1] in (0, 1, 2, 5)))


class HidRawDevice:
    def __init__(self, hid=None):
        self.hid = hid or load_hid()
        devices = inventory(self.hid)
        if len(devices) != 1:
            raise ValueError('need exactly one HyperX experimental RAW interface; close other clients')
        item = devices[0]
        self.dev = self.hid.device()
        try:
            self.dev.open_path(item['path'])
            if item not in inventory(self.hid) or self.dev.get_product_string() != item['product_string']:
                raise ValueError('HyperX identity changed at open')
        except Exception:
            self.dev.close()
            raise

    def close(self):
        self.dev.close()

    def allowed(self, p):
        return read_allowed(p)

    def query(self, request):
        p = bytes(request).ljust(32, b'\0')
        if len(p) != 32 or not self.allowed(p):
            raise ValueError('RAW command allowlist')
        # Report ID zero is mandatory for hidapi output, not part of the protocol.
        if self.dev.write(b'\0'+p) != 33:
            raise OSError('short RAW report write')
        response = bytes(self.dev.read(32, 2000))
        if len(response) != 32:
            raise TimeoutError('RAW response missing/short; do not retry writes')
        return response
