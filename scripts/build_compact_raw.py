#!/usr/bin/env python3
"""Compile compact USB experiments only. No USB access or flash target."""
import argparse
import json
import os
import shutil
import subprocess
import build_firmware as build
from verified_patch import applied
from measure_raw_hid import overflow_from_log


KEYMAPS = ("raw_compact", "vial_readonly", "vial_editable")


def main(keymap="raw_compact"):
    if keymap not in KEYMAPS:
        raise ValueError("unsupported keymap; no flash target")
    lock = build.validate_sources()
    if keymap == "vial_readonly":
        from generate_vial_readonly import generate
        generate(check=True)
    if keymap == "vial_editable":
        from generate_vial_editable import generate
        generate(check=True)
    shutil.copytree(build.SOURCE, build.QMK / "keyboards/hyperx/alloy_fps_pro", dirs_exist_ok=True)
    patch = build.ROOT / "patches/qmk/compact-usb.patch"
    preimages = patch.with_name("compact-usb-preimages.json")
    env = os.environ.copy()
    env["PATH"] = str(build.GCC) + os.pathsep + env.get("PATH", "/usr/bin:/bin")
    analysis = build.ROOT / "artifacts/analysis"
    analysis.mkdir(parents=True, exist_ok=True)
    label = keymap.replace("_", "-")
    log = analysis / (label + ".log")
    with applied(build.QMK, patch, preimages):
        command = ["make", "hyperx/alloy_fps_pro:" + keymap, "QMK_BIN=" + str(build.CLI), "SKIP_GIT=yes", "-j2"]
        with log.open("w") as stream:
            run = subprocess.run(command, cwd=build.QMK, env=env, stdout=stream, stderr=subprocess.STDOUT)
        text = build.ANSI.sub("", log.read_text())
        log.write_text(text)
        if run.returncode or any(marker in text for marker in ("☒", "Traceback (", "fatal error:", "[ERRORS]")):
            print(json.dumps(overflow_from_log(text)))
            print(text[-4500:])
            raise RuntimeError("Compact Raw HID build failed; no image approved")
        stem = build.QMK / (".build/hyperx_alloy_fps_pro_" + keymap)
        elf, binary = stem.with_suffix(".elf"), stem.with_suffix(".bin")
        sizes = build.output(build.PREFIX + "size", "-A", str(elf))
        nm = build.output(build.PREFIX + "nm", "-n", str(elf))
        report = build.memory_report(build.parse_sections(sizes), build.parse_symbols(nm), binary.read_bytes())
        if keymap == "vial_editable" and len(binary.read_bytes()) + 0x200 > 0x7000:
            raise ValueError("editable application overlaps reserved map banks")
        out = build.ROOT / "build" / keymap
        out.mkdir(parents=True, exist_ok=True)
        shutil.copy2(elf, out / "candidate.elf")
        shutil.copy2(binary, out / "candidate-offset-0x200.bin")
        (analysis / (label + "-symbols.txt")).write_text(nm)
        (analysis / (label + "-size.txt")).write_text(sizes)
        result = {"keymap": keymap, "qmk_revision": lock["qmk"]["commit"],
                  "patch_sha256": build.digest(patch), "binary_sha256": build.digest(binary),
                  "preimages_sha256": build.digest(preimages),
                  "source_hashes": {str(p.relative_to(build.ROOT)): build.digest(p) for p in sorted(build.SOURCE.rglob("*")) if p.is_file()},
                  "memory": report, "flash_approved": False, "device_tested": False,
                  "vial_integrated": False, "layers": 4, "tapping_enabled": True,
                  "vial_protocol_subset": "read_only_vial6_via9" if keymap == "vial_readonly" else None,
                  "configuration_editable": False, "persistent_keymap": False,
                  "note": "Compile-only prototype. No complete Vial integration, no editable/persistent keymap. Needs jumploader."}
        if keymap == "vial_editable":
            result.update({"vial_protocol_subset":"editable_basic_vial6_via9", "configuration_editable":True,
                           "persistent_keymap":True,"map_storage_range":[0x7000,0x7800],
                           "note":"Experimental physical page backend; must verify actual editing and persistence."})
        if keymap in ("vial_readonly", "vial_editable"):
            result["protocol_lock_sha256"] = build.digest(build.ROOT / "toolchains/vial-protocol-lock.json")
        (out / "build-manifest.json").write_text(json.dumps(result, indent=2) + "\n")
        (analysis / (label + ".json")).write_text(json.dumps(result, indent=2) + "\n")
    # Ensure our temporary patch was restored rather than relaxing source checks.
    build.validate_sources()
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keymap", choices=KEYMAPS, default="raw_compact")
    main(parser.parse_args().keymap)
