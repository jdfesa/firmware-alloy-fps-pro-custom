"""Temporarily apply an exact patch to pinned tools; never discard other edits."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import subprocess


def sha(data):
    return hashlib.sha256(data).hexdigest()


@contextmanager
def applied(root, patch, preimages):
    root, patch = Path(root), Path(patch).resolve()
    hashes = json.loads(Path(preimages).read_text())
    names = subprocess.check_output(["git", "apply", "--numstat", str(patch)], cwd=root, text=True)
    if {line.split("\t")[-1] for line in names.splitlines()} != set(hashes):
        raise ValueError("patch path list differs from preimages")
    originals = {}
    for name, expected in hashes.items():
        path = root / name
        if not path.resolve().is_relative_to(root.resolve()) or path.is_symlink():
            raise ValueError("unsafe patch path")
        data = path.read_bytes()
        if sha(data) != expected:
            raise ValueError("upstream preimage differs; refusing overwrite: " + name)
        originals[name] = data
    subprocess.run(["git", "apply", "--check", str(patch)], cwd=root, check=True)
    subprocess.run(["git", "apply", str(patch)], cwd=root, check=True)
    patched = {name: sha((root / name).read_bytes()) for name in hashes}
    try:
        yield
    finally:
        # A concurrent edit is not ours to erase, even while restoring upstream.
        changed = [name for name in hashes if sha((root / name).read_bytes()) != patched[name]]
        if changed:
            raise RuntimeError("concurrent changes; keeping files for manual review: " + repr(changed))
        for name, data in originals.items():
            (root / name).write_bytes(data)
