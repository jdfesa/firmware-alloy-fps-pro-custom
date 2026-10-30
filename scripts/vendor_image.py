#!/usr/bin/env python3
"""Offline, hash-bound extraction. Never execute the updater or open a device."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import zipfile
import zlib

ZIP_SHA = "d023babeea8fb4305d727fe550f9bdc57e9a1fc82fe909b9072cbb066a297a6e"
EXE_SHA = "c192c4a2e678d416778b0dd042abb215489f8dba4e20e9130d43904d144ceada"
RESOURCE_SHA = "045dc26ec2159eff8200e121eb1694adf668d8b3908c53993ad963fbfcb9f4b5"
MEMBER = "HyperX_Alloy_FPS_Pro_Keyboard_Firmware_Updater_v2112.exe"
ROOT = Path(__file__).resolve().parents[1]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ihex(data: bytes) -> dict[int, int]:
    """Validate lengths, checksums, EOF, address records and overlaps."""
    memory: dict[int, int] = {}
    base = 0
    ended = False
    for number, line in enumerate(data.decode("ascii").splitlines(), 1):
        if not line:
            continue
        if ended or not line.startswith(":"):
            raise ValueError(f"record outside HEX/after EOF at line {number}")
        row = bytes.fromhex(line[1:])
        if len(row) < 5 or len(row) != row[0] + 5 or sum(row) & 255:
            raise ValueError(f"invalid record/checksum at line {number}")
        size, address, kind = row[0], int.from_bytes(row[1:3], "big"), row[3]
        payload = row[4:-1]
        if kind == 0:
            for offset, value in enumerate(payload):
                key = base + address + offset
                if key in memory and memory[key] != value:
                    raise ValueError("conflicting HEX overlap")
                memory[key] = value
        elif kind in (2, 4) and size == 2 and address == 0:
            base = int.from_bytes(payload, "big") << (4 if kind == 2 else 16)
        elif kind == 1 and size == 0 and address == 0:
            ended = True
        elif kind in (3, 5) and size == 4 and address == 0:
            pass  # Execution start metadata, not an address for subsequent data.
        else:
            raise ValueError(f"unsupported/malformed HEX record {kind}")
    if not ended or not memory:
        raise ValueError("missing EOF or empty HEX")
    return memory


def unpack_resource(resource: bytes) -> tuple[bytes, bytes]:
    if len(resource) < 12:
        raise ValueError("truncated resource header")
    hex_size, dll_size, compressed_size = struct.unpack_from("<III", resource)
    if hex_size + dll_size > 1024 * 1024 or compressed_size != len(resource) - 12:
        raise ValueError("resource size bounds")
    decoder = zlib.decompressobj()
    data = decoder.decompress(resource[12:], hex_size + dll_size + 1)
    if not decoder.eof or decoder.unused_data or len(data) != hex_size + dll_size:
        raise ValueError("resource decompression bounds")
    h, dll = data[:hex_size], data[hex_size:]
    if not dll.startswith(b"MZ"):
        raise ValueError("missing embedded PE DLL")
    return h, dll


def extract(zip_path: Path) -> dict:
    zip_bytes = zip_path.read_bytes()
    if sha(zip_bytes) != ZIP_SHA:
        raise ValueError("unreviewed ZIP: hash mismatch")
    with zipfile.ZipFile(zip_path) as archive:
        if archive.namelist() != [MEMBER] or archive.getinfo(MEMBER).file_size != 2243096:
            raise ValueError("unexpected archive inventory")
        exe = archive.read(MEMBER)
    if sha(exe) != EXE_SHA:
        raise ValueError("unreviewed executable")
    # REA PE resource Evidence ev_92b2a7...; offsets bound to the EXE hash above.
    resource = exe[1511564:1511564 + 94922]
    if sha(resource) != RESOURCE_SHA:
        raise ValueError("resource identity mismatch")
    h, dll = unpack_resource(resource)
    memory = ihex(h)
    if min(memory) != 0 or max(memory) != 0x77FF:
        raise ValueError("unexpected application address range")
    image = bytes(memory.get(address, 0xFF) for address in range(0x8000))
    inputs, outputs = ROOT / "artifacts/vendor", ROOT / "artifacts/analysis"
    inputs.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)
    for name, data in [(MEMBER, exe), ("embedded-resource-140.rar", resource),
                       ("FPS_Pro_v2112.hex", h), ("SnxHidCtrlLib.dll", dll)]:
        (inputs / name).write_bytes(data)
    (outputs / "FPS_Pro_v2112.analysis-only.bin").write_bytes(image)
    ranges: list[list[int]] = []
    for address in sorted(memory):
        if ranges and address == ranges[-1][1] + 1:
            ranges[-1][1] = address
        else:
            ranges.append([address, address])
    record = {
        "source_type": "third_party_mirror_not_authenticated",
        "source_repo": "IRus/blog", "source_commit": "f280a57181cb8166c1031d064869fa83d3f0d5a9",
        "zip_sha256": ZIP_SHA, "exe_sha256": EXE_SHA, "resource_sha256": RESOURCE_SHA,
        "hex_sha256": sha(h), "dll_sha256": sha(dll), "analysis_sha256": sha(image),
        "hex_address_ranges": ranges, "analysis_fill_byte": 255,
        "analysis_padding_is_not_read_from_device": True,
        "bootloader_present_in_hex": False, "executed": False,
        "dump_of_connected_device": False, "restoration_verified": False,
        "rea_resources_evidence": "ev_92b2a7f1bc47af8ad6b24984ddf3af14a384cfc10c902e3a6dd3f10f2795ae28",
    }
    (outputs / "extraction.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip", type=Path)
    print(json.dumps(extract(parser.parse_args().zip), indent=2))
