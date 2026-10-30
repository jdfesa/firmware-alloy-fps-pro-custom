#!/usr/bin/env python3
"""Compile/link an experimental ARM candidate. No USB or flashing operations."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
QMK = ROOT / "artifacts/tools/qmk"
GCC = ROOT / "artifacts/tools/xpack-arm-none-eabi-gcc-12.3.1-1.2/bin"
PREFIX = str(GCC / "arm-none-eabi-")
CLI = ROOT / "scripts/qmk_build_cli.py"
SOURCE = ROOT / "firmware/keyboards/hyperx/alloy_fps_pro"
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def output(*command, cwd=None):
    return subprocess.check_output(command, cwd=cwd, text=True)


def validate_sources():
    lock = json.loads((ROOT / "toolchains/build-lock.json").read_text())
    targets = [(QMK, lock["qmk"]["commit"])]
    targets += [(QMK / "lib" / name, item["commit"]) for name, item in lock["submodules"].items()]
    targets += [(ROOT / "artifacts/tools/python-src" / name, item["commit"]) for name, item in lock["python_sources"].items()]
    for path, expected in targets:
        observed = output("git", "-C", str(path), "rev-parse", "HEAD").strip()
        if observed != expected:
            raise ValueError(f"toolchain source revision mismatch: {path}")
        # Untracked pycache/version-generation files are not firmware edits.
        if output("git", "-C", str(path), "diff", "HEAD", "--name-only").strip():
            raise ValueError(f"tracked upstream source modified: {path}")
    if not os.access(CLI, os.X_OK):
        raise ValueError("qmk_build_cli.py must be executable (single-word QMK_BIN)")
    return lock


def parse_sections(text):
    sections = {}
    for line in text.splitlines():
        match = re.fullmatch(r"\s*(\.[\w.]+)\s+(\d+)\s+(\d+)\s*", line)
        if match:
            sections[match[1]] = {"size": int(match[2]), "address": int(match[3])}
    return sections


def parse_symbols(text):
    result = {}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) == 3 and re.fullmatch("[0-9a-fA-F]+", fields[0]):
            result[fields[2]] = int(fields[0], 16)
    return result


def memory_report(sections, symbols, binary):
    vectors = sections[".vectors_512_aligned"]["address"]
    ram_base, ram_end = symbols["__ram0_base__"], symbols["__ram0_end__"]
    heap_base, heap_end = symbols["__heap_base__"], symbols["__heap_end__"]
    if vectors != 0x200 or len(binary) > 0x7800 - vectors:
        raise ValueError("unexpected application flash address/size")
    if (ram_base, ram_end) != (0x20000000, 0x20000800) or not ram_base <= heap_base <= heap_end <= ram_end:
        raise ValueError("unexpected RAM map/overflow")
    stack = int.from_bytes(binary[:4], "little")
    reset = int.from_bytes(binary[4:8], "little")
    if len(binary) < 192 or not ram_base < stack <= ram_end or stack & 7:
        raise ValueError("invalid initial stack vector")
    if not reset & 1 or not vectors + 192 <= (reset & ~1) < vectors + len(binary):
        raise ValueError("reset vector is not Thumb code inside the application")
    return {"binary_bytes": len(binary), "binary_load_address": vectors, "flash_upper_exclusive": 0x7800,
            "flash_application_capacity": 0x7800 - vectors, "requires_jumploader": True,
            "vectors_at_zero": False, "ram_bytes": ram_end - ram_base,
            "ram_reserved_through_heap_base": heap_base - ram_base, "heap_bytes": heap_end - heap_base,
            "main_irq_stack_bytes": symbols["__main_stack_size__"],
            "process_stack_bytes": symbols["__process_stack_size__"],
            "data_bytes": sections[".data"]["size"], "bss_bytes": sections[".bss"]["size"],
            "runtime_stack_high_water_measured": False}


def build(keymap):
    if keymap not in ("default", "custom42", "custom42_fn"):
        raise ValueError("unsupported keymap; build driver has no flash target")
    lock = validate_sources()
    shutil.copytree(SOURCE, QMK / "keyboards/hyperx/alloy_fps_pro", dirs_exist_ok=True)
    env = os.environ.copy()
    env["PATH"] = str(GCC) + os.pathsep + env.get("PATH", "/usr/bin:/bin")
    for variable, name in [("XDG_CONFIG_HOME", "config"), ("XDG_CACHE_HOME", "cache")]:
        env[variable] = str(ROOT / "artifacts/tools" / name)
    command = ["make", f"hyperx/alloy_fps_pro:{keymap}", f"QMK_BIN={CLI}", "SKIP_GIT=yes", "-j2"]
    analysis = ROOT / "artifacts/analysis"
    analysis.mkdir(parents=True, exist_ok=True)
    log = analysis / f"arm-build-{keymap}.log"
    print(f"Building Cortex-M0 {keymap}; log: {log.relative_to(ROOT)}", flush=True)
    with log.open("w") as stream:
        run = subprocess.run(command, cwd=QMK, env=env, stdout=stream, stderr=subprocess.STDOUT)
    text = ANSI.sub("", log.read_text())
    log.write_text(text)
    if run.returncode or any(marker in text for marker in ("☒", "Traceback (", "fatal error:", "[ERRORS]")):
        print(text[-7000:])
        raise RuntimeError(f"ARM build failed; see {log}")
    stem = "hyperx_alloy_fps_pro_" + keymap
    elf = QMK / ".build" / (stem + ".elf")
    binary_path = elf.with_suffix(".bin")
    binary = binary_path.read_bytes()
    sizes = output(PREFIX + "size", "-A", str(elf))
    symbols_text = output(PREFIX + "nm", "-n", str(elf))
    report = memory_report(parse_sections(sizes), parse_symbols(symbols_text), binary)
    folder = ROOT / "build" / keymap
    folder.mkdir(parents=True, exist_ok=True)
    for path, name in [(elf, "candidate.elf"), (binary_path, "candidate-offset-0x200.bin"), (elf.with_suffix(".hex"), "candidate.hex")]:
        shutil.copy2(path, folder / name)
    (analysis / f"arm-size-{keymap}.txt").write_text(sizes)
    (analysis / f"arm-symbols-{keymap}.txt").write_text(symbols_text)
    source_hashes = {str(path.relative_to(ROOT)): digest(path) for path in sorted(SOURCE.rglob("*")) if path.is_file()}
    manifest = {"keymap": keymap, "architecture": "ARM Cortex-M0", "native_arm_build": True,
                "qmk_revision": lock["qmk"]["commit"], "gcc": output(PREFIX + "gcc", "--version").splitlines()[0],
                "source_hashes": source_hashes, "binary_sha256": hashlib.sha256(binary).hexdigest(),
                "elf_sha256": digest(elf), "memory": report, "flash_approved": False,
                "device_tested": False, "original_recovery_verified": False,
                "warning": "Application at 0x200. Needs a compatible jumploader; NOT an image to write at zero."}
    (folder / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (analysis / f"arm-build-{keymap}.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"artifacts": str(folder.relative_to(ROOT)), "memory": report,
                      "binary_sha256": manifest["binary_sha256"], "flash_approved": False}, indent=2))
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keymap", choices=("default", "custom42", "custom42_fn"), default="custom42")
    args = parser.parse_args()
    build(args.keymap)
