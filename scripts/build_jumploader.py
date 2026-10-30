#!/usr/bin/env python3
"""Build a standalone 512-byte-region candidate. Never combines or flashes it."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
GCC = ROOT / "artifacts/tools/xpack-arm-none-eabi-gcc-12.3.1-1.2/bin/arm-none-eabi-"


def validate(binary):
    if not 192 <= len(binary) <= 512:
        raise ValueError("jumploader must fit [0, 0x200)")
    vectors = struct.unpack_from("<48I", binary)
    if vectors[0] != 0x20000780:
        raise ValueError("stack must not overwrite QMK reset magic")
    for address in vectors[1:]:
        if not address & 1 or not 192 <= (address & ~1) < len(binary):
            raise ValueError("invalid Thumb vector or target outside jumploader")
    if len(set(vectors[2:])) != 1:
        raise ValueError("all exceptions must share the application vector proxy")
    return {"raw_bytes": len(binary), "padded_bytes": 512, "load_address": 0,
            "app_address": 512, "app_upper_exclusive": 0x7800,
            "reset_vector": vectors[1], "exception_proxy": vectors[2]}


def build():
    folder = ROOT / "build/jumploader"
    folder.mkdir(parents=True, exist_ok=True)
    src = ROOT / "firmware/jumploader"
    elf, raw = folder / "candidate.elf", folder / "candidate-raw.bin"
    subprocess.run([str(GCC) + "gcc", "-mcpu=cortex-m0", "-mthumb", "-Os", "-flto",
                    "-ffreestanding", "-fno-builtin", "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
                    "-Wall", "-Wextra", "-Werror", "-nostdlib", "-nostartfiles",
                    "-Wl,--build-id=none", "-Wl,--gc-sections", f"-Wl,-Map={folder / 'candidate.map'}",
                    "-T", str(src / "linker.ld"), str(src / "main.c"), str(src / "startup.S"),
                    "-o", str(elf)], check=True)
    subprocess.run([str(GCC) + "objcopy", "-O", "binary", str(elf), str(raw)], check=True)
    binary = raw.read_bytes()
    report = validate(binary)
    padded = binary.ljust(512, b"\0")
    (folder / "candidate-offset-0x0.bin").write_bytes(padded)
    report.update({"binary_sha256": hashlib.sha256(padded).hexdigest(),
                   "source_hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in sorted(src.iterdir()) if p.is_file()},
                   "compiler": subprocess.check_output([str(GCC) + "gcc", "--version"], text=True).splitlines()[0],
                   "escape_pins": {"output": "C0", "input": "A0", "status": "inferred_not_tested"},
                   "runtime_validated": False, "flash_approved": False,
                   "warning": "Do not install alone over OEM: OEM application is NOT linked at 0x200."})
    (folder / "build-manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    (folder / "disassembly.txt").write_text(subprocess.check_output([str(GCC) + "objdump", "-d", str(elf)], text=True))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()
