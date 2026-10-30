#!/usr/bin/env python3
"""Bounded SN32F26x first trial. Dry-run default; never erase/unprotect.

References and verification limitations: docs/first-flash-trial.md.
Apply deliberately leaves the device in ISP, including on failure. No retries.
"""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import struct
import time

import probe_hyperx as probe
import build_jumploader

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 0x7800
PAGE = 64
KEYMAPS = ("default", "custom42", "custom42_fn", "vial_readonly")
OEM_DESCRIPTOR = "225f708546bcd693001522ee72ae5a866fcb674dd433eba3687974b1ac128bdc"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked_artifact(folder, name):
    manifest = json.loads((folder / "build-manifest.json").read_text())
    data = (folder / name).read_bytes()
    if sha(data) != manifest["binary_sha256"]:
        raise ValueError("binary differs from build manifest")
    sources = manifest.get("source_hashes", {})
    if not sources:
        raise ValueError("missing source provenance")
    for path, expected in sources.items():
        target = (ROOT / path).resolve()
        if not target.is_relative_to((ROOT / "firmware").resolve()) or sha(target.read_bytes()) != expected:
            raise ValueError("source differs from build manifest: " + path)
    return data, manifest


def validate_app(data):
    if not 192 <= len(data) <= LIMIT - 0x200:
        raise ValueError("application size outside bounded region")
    sp, pc = struct.unpack_from("<II", data)
    if not 0x20000000 < sp <= 0x20000800 or sp & 7:
        raise ValueError("invalid application stack")
    if not pc & 1 or not 0x2c0 <= (pc & ~1) < 0x200 + len(data):
        raise ValueError("invalid application reset vector")


def validate_image(data, offset):
    if offset not in (0, 0x200) or not data or len(data) % PAGE or offset + len(data) > LIMIT:
        raise ValueError("image range/alignment forbidden")
    if offset == 0:
        if len(data) <= 512:
            raise ValueError("never install a jumploader alone over OEM")
        build_jumploader.validate(data[:512])
        validate_app(data[512:])
    else:
        validate_app(data)


def candidate(keymap, first_install=False):
    if keymap not in KEYMAPS:
        raise ValueError("unsupported keymap")
    app, manifest = checked_artifact(ROOT / "build" / keymap, "candidate-offset-0x200.bin")
    validate_app(app)
    if manifest.get("keymap") != keymap or manifest["memory"]["binary_load_address"] != 0x200:
        raise ValueError("wrong application manifest")
    if manifest["memory"]["ram_reserved_through_heap_base"] > 2048:
        raise ValueError("RAM overflow")
    data, offset = app, 0x200
    if first_install:
        boot, _ = checked_artifact(ROOT / "build/jumploader", "candidate-offset-0x0.bin")
        if len(boot) != 512:
            raise ValueError("jumploader must be exactly 512 bytes")
        build_jumploader.validate(boot)
        data, offset = boot + app, 0
    data += b"\xff" * (-len(data) % PAGE)
    validate_image(data, offset)
    plan = {"keymap": keymap, "first_install": first_install,
            "offset": offset, "end_exclusive": offset + len(data),
            "bytes": len(data), "reports": len(data) // PAGE, "sha256": sha(data),
            "isp_region_untouched": "[0x7800,0x8000)",
            "explicit_erase": False, "security_change": False,
            "jumploader_preserved": not first_install,
            "automatic_reboot": False, "readback_verified": False,
            "warning": "Experimental. Completion ACK/echo is NOT readback or proven recovery."}
    return data, plan


def program_header(offset, data):
    validate_image(data, offset)
    return struct.pack("<III", 0x55aa05, offset, len(data) // PAGE) + bytes(52)


def verify_completion(reply, data):
    probe.parse_reply(reply, 5)
    if reply[60:64] != data[-4:]:
        raise ValueError("final program echo differs from last payload word")
    return {"completion_ack": True, "last_word_echo_matches": True,
            "program_checksum_raw": struct.unpack_from("<H", reply, 8)[0],
            "image_sum16": sum(struct.unpack("<%dH" % (len(data)//2), data)) & 0xffff,
            "checksum_domain_verified": False, "readback_verified": False}


class TrialDevice(probe.FeatureDevice):
    """Only fixed queries, OEM entry, reviewed program stream and explicit return."""
    def _write(self, payload):
        if len(payload) != PAGE:
            raise ValueError("only complete 64-byte reports")
        buf = bytearray(b"\0" + payload)
        fcntl.ioctl(self.fd, 0xC0000000 | (65 << 16) | (ord("H") << 8) | 6, buf, True)

    def send(self, payload):
        # Do not broaden probe_hyperx's diagnostic allowlist.
        if payload != probe.ENTRY and payload not in [probe.command(c) for c in (1, 6, 7)]:
            raise ValueError("command forbidden")
        self._write(payload)

    def program(self, offset, data, event):
        header = program_header(offset, data)  # Validate before first USB write.
        event({"event": "program_requested", "offset": offset, "reports": len(data)//PAGE})
        self._write(header)
        time.sleep(0.2)
        probe.parse_reply(self.receive(), 5)
        event({"event": "program_enabled_ack"})
        for pos in range(0, len(data), PAGE):
            self._write(data[pos:pos+PAGE])
            # Datasheet typical page programming 5 ms; conservative pacing.
            time.sleep(0.02)
            if (pos // PAGE + 1) % 32 == 0 or pos + PAGE == len(data):
                event({"event": "reports_sent", "count": pos//PAGE + 1})
        time.sleep(0.3)
        result = verify_completion(self.receive(), data)
        event({"event": "completion", **result})
        return result


def open_target(port, enter_oem=False):
    item = probe.select(probe.inventory(), port, {probe.OEM, probe.ISP})
    if (item["vid"], item["pid"]) == probe.OEM:
        if item["bcdDevice"] != "2112" or item["report_descriptor_sha256"] != OEM_DESCRIPTOR:
            raise ValueError("unreviewed OEM revision/descriptor")
    dev = TrialDevice(item)
    if enter_oem:
        if (item["vid"], item["pid"]) != probe.OEM:
            dev.close()
            raise ValueError("first installation must start at the reviewed OEM")
        try:
            dev.send(probe.ENTRY)
        finally:
            dev.close()
        time.sleep(1)
        # Some ISP implementations retain the OEM descriptors.
        item = probe.select(probe.inventory(), port, {probe.OEM, probe.ISP})
        dev = TrialDevice(item)
    return dev


def require_f260_cs0(dev):
    result = probe.decode_version(dev.query(1))
    if result["family"] != "SN32F26x" or result["security_raw"] not in (0, 0xffff):
        raise ValueError("requires observed F260 / CS0; never change protection")
    return result


def apply(dev, data, plan, expected_checksum, event):
    # Defense in depth: callers cannot bypass image validation via transport.
    validate_image(data, plan["offset"])
    if sha(data) != plan["sha256"]:
        raise ValueError("plan/image mismatch")
    version = require_f260_cs0(dev)
    event({"event": "version", **version})
    before = struct.unpack_from("<H", dev.query(6), 8)[0]
    event({"event": "checksum_before", "value": before})
    if before != expected_checksum:
        raise ValueError("checksum changed since reviewed device state")
    result = dev.program(plan["offset"], data, event)
    after = struct.unpack_from("<H", dev.query(6), 8)[0]
    event({"event": "checksum_after", "value": after})
    # No auto-reboot: failed stream or bad app must remain in ISP for inspection.
    return {**result, "checksum_after": after, "left_in_isp": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keymap", choices=KEYMAPS, default="default")
    parser.add_argument("--first-install", action="store_true")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--inspect-isp", action="store_true")
    mode.add_argument("--return-user", action="store_true")
    parser.add_argument("--port")
    parser.add_argument("--expected-sha256")
    parser.add_argument("--expected-checksum", type=lambda v: int(v, 0))
    args = parser.parse_args()
    if args.inspect_isp or args.return_user:
        if not args.port or args.first_install:
            parser.error("explicit port required; first-install not allowed for ISP controls")
        dev = open_target(args.port)
        try:
            print(json.dumps(require_f260_cs0(dev)), flush=True)
            checksum = struct.unpack_from("<H", dev.query(6), 8)[0]
            print(json.dumps({"isp_checksum": checksum}), flush=True)
            if args.return_user:
                if args.expected_checksum != checksum:
                    raise ValueError("explicit matching checksum required before return")
                dev.send(probe.command(7))
                print("RETURN_USER sent; enumeration and typing are not yet verified", flush=True)
        finally:
            dev.close()
        return
    data, plan = candidate(args.keymap, args.first_install)
    print(json.dumps(plan, indent=2), flush=True)
    if not args.apply:
        return
    if not args.port or args.expected_sha256 != plan["sha256"] or args.expected_checksum is None:
        parser.error("apply requires port, exact dry-run SHA256 and reviewed checksum")
    folder = ROOT / "build/trial"
    folder.mkdir(parents=True, exist_ok=True)
    log = folder / (time.strftime("%Y%m%d-%H%M%S") + ".jsonl")
    with log.open("x") as stream:
        def event(value):
            line = json.dumps(value)
            stream.write(line + "\n")
            stream.flush()
            print(line, flush=True)
        event({"event": "plan", **plan})
        dev = open_target(args.port, args.first_install)
        try:
            apply(dev, data, plan, args.expected_checksum, event)
        except BaseException as exc:
            event({"event": "ABORT_NO_REBOOT_NO_RETRY", "error": str(exc)})
            raise
        finally:
            dev.close()


if __name__ == "__main__":
    main()
