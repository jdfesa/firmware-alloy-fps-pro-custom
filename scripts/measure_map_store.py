#!/usr/bin/env python3
"""Compile the standalone map-store object; no backend, firmware image or USB."""
import json
import subprocess

import build_firmware as build


def main():
    lock = build.validate_sources()
    source = build.ROOT / "firmware/experiments/vial_store/map_store.c"
    out = build.ROOT / "build/map-store"
    out.mkdir(parents=True, exist_ok=True)
    obj = out / "map_store.o"
    command = [build.PREFIX + "gcc", "-mcpu=cortex-m0", "-mthumb", "-Os", "-std=c11",
               "-Wall", "-Wextra", "-Werror", "-ffreestanding", "-fstack-usage", "-c", str(source), "-o", str(obj)]
    subprocess.run(command, check=True)
    sizes = build.output(build.PREFIX + "size", "-A", str(obj))
    sections = build.parse_sections(sizes)
    stack = obj.with_suffix(".su").read_text()
    result = {
        "scope": "standalone Cortex-M0 object, not linked into QMK; simulated backend only",
        "qmk_revision": lock["qmk"]["commit"],
        "source_sha256": build.digest(source),
        "header_sha256": build.digest(source.with_suffix(".h")),
        "object_sha256": build.digest(obj),
        "sections": sections,
        "caller_state_bytes": 8,
        "stack_usage_per_function": stack,
        "stack_scope": "compiler static frames only, not cumulative call-chain/runtime high-water",
        "physical_storage_backend": False,
        "flash_approved": False,
    }
    if any(sections.get(name, {}).get("size", 0) for name in (".data", ".bss")):
        raise ValueError("unexpected global RAM reservation in streaming store")
    (out / "measurement.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
