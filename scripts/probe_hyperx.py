#!/usr/bin/env python3
"""HyperX-only metadata / explicit temporary ISP cycle. NO flash or unlock API.

Linux hidraw; standard library only. Default mode never opens a device node.
--probe-cycle sends OEM ISP entry, queries version/checksum, then requests user
mode in finally. This disrupts the HyperX temporarily; it is NOT passive.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import struct
import time

OEM = ("0951", "16d2")
ISP = ("0c45", "7010")
ENTRY = bytes.fromhex("aa55a55aff0033cc") + bytes(56)
ALLOWED = {1: "version", 6: "checksum", 7: "return_user"}


def command(opcode):
    if opcode not in ALLOWED:
        raise ValueError("command forbidden: no erase/program/security operations")
    return struct.pack("<I", 0x55AA00 | opcode) + bytes(60)


def parse_reply(data, opcode):
    if len(data) != 64 or struct.unpack_from("<II", data) != (0x55AA00 | opcode, 0xFAFAFAFA):
        raise ValueError("unexpected ISP response; no assumptions about chip/security")
    return data


def decode_version(data):
    parse_reply(data, 1)
    cs = struct.unpack_from("<H", data, 14)[0]
    return {"family_byte": data[8], "chip_byte": data[9],
            "family": "SN32F26x" if data[8:10] == b"\x20\x02" else "unknown",
            "word12_raw_uninterpreted": struct.unpack_from("<H", data, 12)[0],
            "security_raw": cs,
            "security_level": {0: "CS0", 65535: "CS0", 0x5A5A: "CS1", 0xA5A5: "CS2", 0x55AA: "CS3"}.get(cs, "unknown")}


def wait_for_oem(port, attempts=50):
    for _ in range(attempts):
        found = [d for d in inventory() if d["port"] == port and (d["vid"], d["pid"]) == OEM]
        if len(found) == 1:
            return found
        time.sleep(0.1)
    return []


def read(path):
    return path.read_text().strip()


def inventory(root=Path("/sys/class/hidraw")):
    matches = []
    for item in sorted(root.glob("hidraw*")):
        device = (item / "device").resolve()
        usb = next((p for p in device.parents if (p / "idVendor").exists()), None)
        if usb is None:
            continue
        identity = (read(usb / "idVendor"), read(usb / "idProduct"))
        if identity not in (OEM, ISP):
            continue  # Never read report descriptors, configuration or input of other keyboards.
        interface = next((p for p in device.parents if (p / "bInterfaceNumber").exists()), None)
        if interface is None or read(interface / "bInterfaceNumber") != "00":
            continue
        matches.append({"node": "/dev/" + item.name, "port": usb.name,
                        "vid": identity[0], "pid": identity[1],
                        "bcdDevice": read(usb / "bcdDevice"),
                        "device_number": read(usb / "devnum"),
                        "device_rdev": read(item / "dev"),
                        "report_descriptor_sha256": hashlib.sha256((device / "report_descriptor").read_bytes()).hexdigest()})
    return matches


def select(devices, port, identities):
    found = [d for d in devices if d["port"] == port and (d["vid"], d["pid"]) in identities]
    if len(found) != 1:
        raise ValueError("expected exactly one allowed interface 0 on the selected physical USB port")
    return found[0]


class FeatureDevice:
    def __init__(self, item):
        self.item = item
        self.fd = os.open(item["node"], os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW)
        try:
            st = os.fstat(self.fd)
            if f"{os.major(st.st_rdev)}:{os.minor(st.st_rdev)}" != item["device_rdev"]:
                raise ValueError("device node changed")
            current = select(inventory(), item["port"], {(item["vid"], item["pid"])})
            if current != item:
                raise ValueError("USB identity changed during open")
        except BaseException:
            self.close()
            raise

    def close(self):
        os.close(self.fd)

    def send(self, payload):
        if payload != ENTRY and payload not in [command(c) for c in ALLOWED]:
            raise ValueError("payload is not allowlisted")
        buf = bytearray(b"\0" + payload)
        fcntl.ioctl(self.fd, 0xC0000000 | (65 << 16) | (ord("H") << 8) | 6, buf, True)

    def receive(self):
        buf = bytearray(65)
        fcntl.ioctl(self.fd, 0xC0000000 | (65 << 16) | (ord("H") << 8) | 7, buf, True)
        return bytes(buf[1:])

    def query(self, opcode):
        if opcode not in (1, 6):
            raise ValueError("not a query")
        self.send(command(opcode))
        time.sleep(0.15)
        return parse_reply(self.receive(), opcode)


def cycle(port):
    before = select(inventory(), port, {OEM})
    if before["bcdDevice"] != "2112":
        raise ValueError("unreviewed OEM revision")
    log = {"before": before, "operations": [], "flash_written": False,
           "security_changed": False, "original_recovery_verified": False}
    device = FeatureDevice(before)
    entered = False
    try:
        # Mark before the request: a timeout may mean it entered ISP successfully.
        entered = True
        log["operations"].append("OEM entry requested (temporary mode change)")
        device.send(ENTRY)
        time.sleep(1)
        current = select(inventory(), port, {OEM, ISP})
        if current != before:
            device.close()
            device = None
            device = FeatureDevice(current)
        version = device.query(1)
        log["version_response_hex"] = version.hex()
        log["decoded_version"] = decode_version(version)
        log["operations"].append("GET_FW_VERSION acknowledged")
        checksum = device.query(6)
        log["checksum"] = f"0x{struct.unpack_from('<H', checksum, 8)[0]:04x}"
        log["operations"].append("GET_CHECKSUM acknowledged")
    except Exception as exc:
        log["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        if entered:
            try:
                # Reopen the same physical port if the old handle was disconnected.
                current = select(inventory(), port, {OEM, ISP})
                if device is None or current != device.item:
                    if device is not None:
                        device.close()
                    device = None
                    device = FeatureDevice(current)
                device.send(command(7))
                log["operations"].append("RETURN_USER_MODE sent (not functional confirmation)")
            except Exception as exc:
                log["return_error"] = f"{type(exc).__name__}: {exc}"
        if device is not None:
            device.close()
        time.sleep(1)
        log["after"] = wait_for_oem(port)
        log["oem_metadata_returned"] = bool(log["after"])
        if not log["after"]:
            log.setdefault("return_error", "OEM not observed within timeout; check/reconnect ONLY the HyperX")
    return log


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe-cycle", action="store_true")
    parser.add_argument("--port", help="physical port from metadata, not a hidraw number")
    args = parser.parse_args()
    if args.probe_cycle:
        if not args.port:
            parser.error("--probe-cycle requires an explicit --port")
        result = cycle(args.port)
    else:
        result = {"metadata_only": True, "devices": inventory()}
    print(json.dumps(result, indent=2))
    return 2 if "error" in result or "return_error" in result else 0


if __name__ == "__main__":
    raise SystemExit(main())
