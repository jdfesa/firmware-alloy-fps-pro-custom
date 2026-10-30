#!/usr/bin/env python3
"""Query only the experimental HyperX Raw HID interface; never key input.

No keymap writes, matrix-state requests, unlock, ISP or generic command option.
"""
import argparse
import hashlib
import json
import lzma
import os
from pathlib import Path
import select
import time

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = ("feed", "a11f")
RAW_USAGE = bytes.fromhex("0660ff0961")


def inventory():
    matches = []
    for node in Path("/sys/class/hidraw").glob("hidraw*"):
        device = (node/"device").resolve()
        usb = next((p for p in device.parents if (p/"idVendor").exists()), None)
        if usb is None:
            continue
        if tuple((usb/k).read_text().strip() for k in ("idVendor", "idProduct")) != IDENTITY:
            continue
        descriptor = (device/"report_descriptor").read_bytes()
        if not descriptor.startswith(RAW_USAGE):
            continue
        matches.append({"port":usb.name, "node":"/dev/"+node.name,
                        "rdev":(node/"dev").read_text().strip(),
                        "descriptor_sha256":hashlib.sha256(descriptor).hexdigest()})
    return matches


class RawDevice:
    def __init__(self, port):
        devices = [d for d in inventory() if d["port"] == port]
        if len(devices) != 1:
            raise ValueError("need exactly one HyperX experimental RAW interface on selected port")
        item = devices[0]
        self.fd = os.open(item["node"], os.O_RDWR | os.O_NONBLOCK | os.O_CLOEXEC | os.O_NOFOLLOW)
        st = os.fstat(self.fd)
        if f"{os.major(st.st_rdev)}:{os.minor(st.st_rdev)}" != item["rdev"] or item not in inventory():
            self.close()
            raise ValueError("identity changed at open")

    def close(self):
        os.close(self.fd)

    def query(self, request):
        p = bytes(request).ljust(32, b"\0")
        allowed = (p[0] in (1, 4, 0x11, 0x12) or (p[0] == 0xfe and p[1] in (0, 1, 2, 5)))
        if len(p) != 32 or not allowed:
            raise ValueError("read-only command allowlist")
        if os.write(self.fd, b"\0"+p) != 33:
            raise OSError("short RAW report write")
        if not select.select([self.fd], [], [], 2)[0]:
            raise TimeoutError("RAW response timed out")
        response = os.read(self.fd, 32)
        if len(response) != 32:
            raise ValueError("bad RAW report length")
        return response


def inspect(dev):
    version = dev.query([1])
    if version[:3] != bytes([1,0,9]):
        raise ValueError("unexpected VIA version")
    identity = dev.query([0xfe,0])
    if int.from_bytes(identity[:4], "little") != 6:
        raise ValueError("unexpected Vial version")
    size = int.from_bytes(dev.query([0xfe,1])[:4], "little")
    if not 1 <= size <= 8192:
        raise ValueError("definition exceeds probe bound")
    compressed = b"".join(dev.query([0xfe,2,i&255,i>>8]) for i in range((size+31)//32))[:size]
    definition = json.loads(lzma.decompress(compressed, memlimit=2**24))
    layers = dev.query([0x11])[1]
    if layers != 4:
        raise ValueError("unexpected layer count")
    codes = b""
    for offset in range(0, 896, 28):
        count = min(28,896-offset)
        response = dev.query([0x12,offset>>8,offset&255,count])
        if response[:4] != bytes([0x12,offset>>8,offset&255,count]):
            raise ValueError("bad map response header")
        codes += response[4:4+count]
    return {"via_protocol":9,"vial_protocol":6,"uid_hex":identity[4:12].hex(),
            "definition_name":definition.get("name"),"definition_bytes":size,
            "definition_sha256":hashlib.sha256(compressed).hexdigest(),
            "layers":layers,"map_bytes":len(codes),"map_sha256":hashlib.sha256(codes).hexdigest(),
            "read_only_commands":True,"configuration_editing_tested":False,
            "gui_detection_tested":False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port")
    args=parser.parse_args()
    if not args.port:
        print(json.dumps({"metadata_only":True,"interfaces":inventory()},indent=2));return
    dev=RawDevice(args.port)
    try:
        print(json.dumps(inspect(dev),indent=2))
    finally:
        dev.close()


if __name__ == "__main__":
    main()
