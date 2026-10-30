#!/usr/bin/env python3
"""macOS ISP-only Feature transport. No OEM entry, erase or security API.

hidapi includes report ID zero in both 65-byte buffers; USB payload is 64B.
Reference: https://libusb.info/hidapi/group__API.html
Reuses the reviewed F260 stream, not the RAW configuration transport.
"""
from hyperx_hid import load_hid
import probe_hyperx as probe
from flash_trial import TrialDevice, validate_image


def inventory(hid):
    # Only enumerate the reviewed ISP identity, never other keyboards.
    return [d for d in hid.enumerate(0x0c45, 0x7010)
            if (d.get('vendor_id'), d.get('product_id'), d.get('release_number'))
            == (0x0c45, 0x7010, 0x0100)
            and d.get('interface_number') in (-1, 0)]


def metadata(hid=None):
    return [{k: d.get(k) for k in ('path', 'vendor_id', 'product_id',
             'release_number', 'interface_number', 'usage_page', 'usage',
             'product_string')} for d in inventory(hid or load_hid())]


class MacTrialDevice(TrialDevice):
    def __init__(self, path, hid=None):
        self.hid = hid or load_hid()
        devices = inventory(self.hid)
        # Fail closed on multiple ISP collections/devices, even with a path.
        if len(devices) != 1 or devices[0]['path'] != path:
            raise ValueError('need exactly one reviewed ISP collection and its current exact path')
        self.item = devices[0]
        self.dev = self.hid.device()
        try:
            self.dev.open_path(path)
            if inventory(self.hid) != devices or self.dev.get_product_string() != self.item['product_string']:
                raise ValueError('ISP identity changed at open')
        except BaseException:
            self.dev.close()
            raise

    def close(self):
        self.dev.close()

    def _write(self, payload):
        if len(payload) != 64:
            raise ValueError('only complete 64-byte Feature reports')
        if self.dev.send_feature_report(b'\0' + payload) != 65:
            raise OSError('short Feature write; no retry or reboot')

    def receive(self):
        reply = bytes(self.dev.get_feature_report(0, 65))
        if len(reply) != 65 or reply[0] != 0:
            raise ValueError('expected report ID zero plus exactly 64 ISP bytes')
        return reply[1:]

    def send(self, payload):
        if payload not in [probe.command(op) for op in (1, 6, 7)]:
            raise ValueError('ISP query/explicit return only; no OEM entry')
        self._write(payload)

    def program(self, offset, data, event):
        validate_image(data, offset)
        if offset != 0x200 or offset + len(data) > 0x7000:
            raise ValueError('macOS update must preserve jumploader, map banks and ISP')
        return super().program(offset, data, event)
