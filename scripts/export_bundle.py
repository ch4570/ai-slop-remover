#!/usr/bin/env python3
"""Export validated manifest-listed files as a portable offline ZIP."""

import argparse
from pathlib import Path
import sys
import zipfile

sys.dont_write_bytecode = True
from check_package import ROOT, check
import install


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        check()
        manifest = install.read_json(ROOT / "manifest.json")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Source timestamps are not release content. Clamp them to ZIP's range
        # without changing validated source bytes or filesystem metadata.
        with zipfile.ZipFile(args.output, "x", compression=zipfile.ZIP_DEFLATED,
                             strict_timestamps=False) as archive:
            for name in ["manifest.json", *sorted(manifest["files"])]:
                archive.write(ROOT / name, arcname=name)
        print("Exported " + str(args.output))
    except (install.BundleError, OSError, ValueError) as exc:
        print("Error: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
