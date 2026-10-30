#!/usr/bin/env python3
"""Build-only loader for real upstream QMK generators, with local source deps.

PyPI is unreachable here. This deliberately does not load QMK's broad command
registry or its USB/flash dependencies. Generator implementations and schema
validation are upstream, not replacements. No flash command is registered.
"""
import importlib
import os
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
QMK = ROOT / "artifacts/tools/qmk"
SOURCE_DEPS = ROOT / "artifacts/tools/python-src"
GENERATORS = {"generate-config-h": "config_h", "generate-rules-mk": "rules_mk",
              "generate-keyboard-c": "keyboard_c", "generate-keyboard-h": "keyboard_h",
              "generate-version-h": "version_h", "generate-make-dependencies": "make_dependencies"}
COMMUNITY = {"generate-community-modules-rules-mk", "generate-community-post-config-h",
             "generate-community-modules-h", "generate-community-modules-c",
             "generate-community-modules-introspection-c", "generate-community-modules-introspection-h",
             "generate-led-matrix-community-modules-inc", "generate-rgb-matrix-community-modules-inc",
             "generate-split-transaction-id-community-modules-inc"}
OTHER = {"resolve-alias": "resolve_alias", "list-keyboards": "list.keyboards", "list-keymaps": "list.keymaps", "hello": "hello"}
EXTERNAL = {"env": "qmk_cli.subcommands.env"}


def main():
    # Make invokes one explicit subcommand per process, with only command-local flags.
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command not in GENERATORS and command not in COMMUNITY and command not in OTHER and command not in EXTERNAL:
        raise SystemExit("Build-only CLI: command not allowed (no flash, USB, setup, or config commands).")
    # Do not inherit a user's QMK config/userspace, especially another keyboard.
    os.environ["XDG_CONFIG_HOME"] = str(ROOT / "artifacts/tools/config")
    os.environ["XDG_CACHE_HOME"] = str(ROOT / "artifacts/tools/cache")
    os.environ["QMK_USERSPACE"] = str(ROOT / "artifacts/tools/empty-userspace")
    os.environ["ORIG_CWD"] = str(QMK)
    os.environ["QMK_HOME"] = str(QMK)
    for dependency in sorted(SOURCE_DEPS.iterdir()):
        sys.path[:0] = [str(dependency / "src"), str(dependency)]
    sys.path.insert(0, str(QMK / "lib/python"))
    os.chdir(QMK)
    from milc import cli
    cli.milc_options(name="qmk-build-only", author="local", version="upstream-62973ee")

    # qmk.cli.__init__ normally eagerly imports every CLI command and checks all
    # optional device/image deps. Supply its package path, importing only reviewed
    # build commands below. Do not patch/replace generator functions or schemas.
    package = types.ModuleType("qmk.cli")
    package.__path__ = [str(QMK / "lib/python/qmk/cli")]
    package.__package__ = "qmk.cli"
    sys.modules["qmk.cli"] = package
    if command in EXTERNAL:
        importlib.import_module(EXTERNAL[command])
    elif command in GENERATORS:
        importlib.import_module("qmk.cli.generate." + GENERATORS[command])
    elif command in COMMUNITY:
        importlib.import_module("qmk.cli.generate.community_modules")
    else:
        importlib.import_module("qmk.cli." + OTHER[command])
    result = cli()
    return 1 if result is False else 0


if __name__ == "__main__":
    sys.exit(main())
