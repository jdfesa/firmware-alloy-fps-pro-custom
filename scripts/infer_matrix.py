#!/usr/bin/env python3
"""Decode reviewed static tables, not live hardware. This is an inference."""
from pathlib import Path
import hashlib
import json
import struct

ROOT = Path(__file__).resolve().parents[1]
IMAGE_SHA = "787a054754c0604a16f2bcb636c68f8269ce0042e5c777bbf6cd56f8512ed7b2"


def infer(image: bytes) -> dict:
    if hashlib.sha256(image).hexdigest() != IMAGE_SHA:
        raise ValueError("unreviewed analysis image")
    if image[0x5B38:0x5B3E] != bytes.fromhex("5109d2161221"):
        raise ValueError("unexpected USB identity")
    ports = {0x40044000: "A", 0x40046000: "B", 0x40048000: "C", 0x4004A000: "D"}
    rows = []
    for row in range(14):
        data, mode, mask = struct.unpack_from("<III", image, 0x5D88 + row * 12)
        if data not in ports or mode != data + 4 or mask == 0 or mask & (mask - 1):
            raise ValueError("invalid row selector record")
        rows.append(f"{ports[data]}{mask.bit_length() - 1}")
    entries = []
    for row in range(14):
        flags = image[0x5E30 + row]
        for col in range(8):
            raw = struct.unpack_from("<H", image, 0x5ED6 + 2 * (row * 8 + col))[0]
            special = bool(flags & (1 << col))
            if special and raw > 12:
                raise ValueError("unexpected special index")
            usage = image[0x5E58 + raw * 2] if special else raw
            entries.append({"matrix": [row, col], "raw": raw, "special": special, "usage": usage})
    if sum(entry["usage"] != 0 for entry in entries) != 87:
        raise ValueError("unexpected key count")
    return {
        "status": "inferred_from_distribution_image_not_validated_on_device",
        "mcu_candidate": "SN32F268F", "usb": {"vid": "0951", "pid": "16d2", "bcdDevice": "2112"},
        "source_image_sha256": IMAGE_SHA, "rows": rows,
        "cols": ["A0", "A1", "A2", "A3", "A7", "A8", "A9", "A10"],
        "diode_direction_candidate": "COL2ROW", "active_low": True,
        "evidence_offsets": {"scan": "0x288c", "row_loop_end": "0x2968", "row_selectors": "0x5d88",
                             "key_table": "0x5ed6", "special_flags": "0x5e30", "special_decode": "0x5e58"},
        "entries": entries,
        "not_verified": ["connected PCB revision", "bootloader entry and recovery", "flash geometry/offset",
                         "compiler memory budget", "real key scanning/timing"],
    }


if __name__ == "__main__":
    result = infer((ROOT / "artifacts/analysis/FPS_Pro_v2112.analysis-only.bin").read_bytes())
    target = ROOT / "hardware/matrix-inference.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(f"{target.relative_to(ROOT)}: inferred 14 x 8, 87 keys; NOT device-validated")
