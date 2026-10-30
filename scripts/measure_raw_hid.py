#!/usr/bin/env python3
"""Compile-only Raw HID RAM measurements. No USB, flash, erase or unlock commands."""
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COMMON = """#pragma once
#define RAW_IN_CAPACITY 1
#define RAW_OUT_CAPACITY 1
#define KEYBOARD_IN_CAPACITY 1
"""
CASES = {
    "raw_budget_full": COMMON,
    # Measurement ONLY: disabling tapping breaks the custom42_fn LT(NAV, ESC).
    "raw_budget_minimal": COMMON + """#define NO_ACTION_ONESHOT
#define NO_ACTION_TAPPING
#define SERIAL_NUMBER "EXPERIMENTAL"
""",
}


def overflow_from_log(text):
    """Recognize this pinned linker's RAM boundary error, not arbitrary failures."""
    match = re.search(r"cannot move location counter backwards \(from (?:0x)?([0-9a-fA-F]+) to (?:0x)?([0-9a-fA-F]+)\)", text)
    if not match:
        return None
    location, end = (int(value, 16) for value in match.groups())
    if end != 0x20000800 or not end < location < 0x20010000:
        return None
    return {"ram_bytes": 2048, "linker_ram_location_bytes": location - 0x20000000,
            "overflow_bytes": location - end}


def measure():
    import build_firmware as build
    build.validate_sources()
    analysis = ROOT / "artifacts/analysis"
    analysis.mkdir(parents=True, exist_ok=True)
    # Reuse only the pinned, clean upstream and the canonical local port.
    import shutil
    shutil.copytree(build.SOURCE, build.QMK / "keyboards/hyperx/alloy_fps_pro", dirs_exist_ok=True)
    env = os.environ.copy()
    env["PATH"] = str(build.GCC) + os.pathsep + env.get("PATH", "/usr/bin:/bin")
    reports = {}
    for name, config in CASES.items():
        folder = build.QMK / "keyboards/hyperx/alloy_fps_pro/keymaps" / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "keymap.c").write_bytes((build.SOURCE / "keymaps/custom42_fn/keymap.c").read_bytes())
        (folder / "rules.mk").write_text("RAW_ENABLE = yes\n")
        (folder / "config.h").write_text(config)
        log = analysis / (name + ".log")
        command = ["make", "hyperx/alloy_fps_pro:" + name, "QMK_BIN=" + str(build.CLI), "SKIP_GIT=yes", "-j2"]
        with log.open("w") as stream:
            run = subprocess.run(command, cwd=build.QMK, env=env, stdout=stream, stderr=subprocess.STDOUT)
        text = build.ANSI.sub("", log.read_text())
        log.write_text(text)
        overflow = overflow_from_log(text)
        if run.returncode:
            if overflow is None:
                raise RuntimeError("Unclassified build failure: " + str(log))
            report = {"status": "linker_ram_overflow", **overflow}
        else:
            elf = build.QMK / ".build" / ("hyperx_alloy_fps_pro_" + name + ".elf")
            sections = build.parse_sections(build.output(build.PREFIX + "size", "-A", str(elf)))
            symbols = build.parse_symbols(build.output(build.PREFIX + "nm", "-n", str(elf)))
            report = {"status": "linked_not_runtime_validated", "memory": build.memory_report(sections, symbols, elf.with_suffix(".bin").read_bytes())}
        reports[name] = {**report, "config": config, "flash_approved": False,
                         "vial_integrated": False, "device_tested": False,
                         "usable_keymap": False, "log": str(log.relative_to(ROOT))}
    output = {"purpose": "Raw HID transport budget only; NOT usable firmware",
              "qmk_revision": json.loads((ROOT / "toolchains/build-lock.json").read_text())["qmk"]["commit"],
              "cases": reports}
    (analysis / "raw-hid-budget.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))
    return output


if __name__ == "__main__":
    measure()
