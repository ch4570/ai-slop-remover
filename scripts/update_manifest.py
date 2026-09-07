#!/usr/bin/env python3
"""Refresh release hashes after intentional edits, or check them without writing."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
import install  # noqa: E402


def build_manifest():
    manifest = install.read_json(ROOT / "manifest.json")
    if manifest.get("schema") != 2:
        raise install.BundleError("Release tooling requires manifest schema 2")
    paths = sorted(install.RELEASE_FILES)
    paths += ["skills/" + name for name in sorted(install.tree_files(ROOT / "skills", ignore_metadata=True))]
    manifest["files"] = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths
    }
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        expected = build_manifest()
        current = install.read_json(ROOT / "manifest.json")
        if args.check:
            if current != expected:
                raise install.BundleError("Release hashes are stale; review changes then run scripts/update_manifest.py")
            install.load_packages(ROOT)
            print("Release inventory and SHA-256 hashes match.")
        else:
            # Validate inventory and dependency metadata before publishing hashes.
            install.load_skill_set(ROOT, expected)
            (ROOT / "manifest.json").write_text(json.dumps(expected, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print("Updated {} release hashes.".format(len(expected["files"])))
    except (install.BundleError, OSError) as exc:
        print("Error: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
