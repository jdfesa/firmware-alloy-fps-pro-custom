#!/usr/bin/env python3
"""Report missing evidence. Does NOT flash or open a USB device."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ("unit_revision_matched", "matrix_behavior_validated", "bootloader_path_verified",
            "original_recovery_verified", "arm_build_and_memory_verified", "jumploader_path_verified")


def missing(status: dict) -> list[str]:
    return [key for key in REQUIRED if status.get(key) is not True]


if __name__ == "__main__":
    status = json.loads((ROOT / "hardware/validation-status.json").read_text())
    pending = missing(status)
    print("NOT READY TO FLASH: " + ", ".join(pending) if pending else "Evidence checklist complete; no device operation performed.")
    sys.exit(2 if pending else 0)
