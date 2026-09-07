#!/usr/bin/env python3
"""Install an unpacked UI Craft bundle using Python's standard library only.

Run the exported bundle's install.py, not this source file. Hashes detect damaged
or edited payloads; they do not authenticate a publisher or replace code review.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile

NAME = "ui-craft-bundle"
PAYLOAD = "skills/" + NAME + "/"
MARKER = ".ui-craft-bundle-install.json"


class BundleError(Exception):
    pass


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise BundleError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    except (ValueError, UnicodeError, OSError) as exc:
        raise BundleError("Cannot read JSON: " + str(path)) from exc


def safe_relative(name):
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise BundleError("Invalid manifest path")
    path = PurePosixPath(name)
    if path.is_absolute() or str(path) != name or any(
        part in (".", "..") or ":" in part for part in path.parts
    ):
        raise BundleError("Unsafe manifest path: " + name)
    return path


def tree_files(root):
    """Enumerate regular files without following links, including hidden files."""
    result = set()
    if root.is_symlink() or not root.is_dir():
        raise BundleError("Expected a real directory: " + str(root))
    for base, dirs, files in os.walk(root, followlinks=False):
        if Path(base) != root and not dirs and not files:
            raise BundleError("Unexpected empty directory: " + str(base))
        for name in dirs + files:
            path = Path(base) / name
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise BundleError("Symlinks are not allowed: " + str(path))
            if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                raise BundleError("Special files are not allowed: " + str(path))
        for name in files:
            result.add((Path(base) / name).relative_to(root).as_posix())
    return result


def load_bundle(root):
    if (root / "manifest.json").is_symlink():
        raise BundleError("Manifest cannot be a symlink")
    manifest = read_json(root / "manifest.json")
    if not isinstance(manifest, dict) or manifest.get("schema") != 1 or manifest.get("name") != NAME:
        raise BundleError("Unsupported bundle manifest")
    version = manifest.get("version")
    if not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?", version):
        raise BundleError("Invalid bundle version")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise BundleError("Manifest files must be a non-empty object")
    required = {"install.py", "README.ko.md", PAYLOAD + "SKILL.md"}
    if not required.issubset(files):
        raise BundleError("Bundle is missing required files")
    folded = set()
    for name, expected in files.items():
        safe_relative(name)
        if name not in ("install.py", "README.ko.md") and not name.startswith(PAYLOAD):
            raise BundleError("Unexpected manifest location: " + name)
        if name == PAYLOAD + MARKER:
            raise BundleError("Payload uses the reserved install marker")
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise BundleError("Invalid SHA-256 for: " + name)
        if name.casefold() in folded:
            raise BundleError("Case-colliding manifest paths: " + name)
        folded.add(name.casefold())
    actual = tree_files(root)
    if actual != set(files) | {"manifest.json"}:
        raise BundleError("Bundle contains missing or unlisted files")
    payload = {}
    for name, expected in files.items():
        path = root.joinpath(*PurePosixPath(name).parts)
        if not path.resolve().is_relative_to(root.resolve()):
            raise BundleError("Source escaped the bundle: " + name)
        data = path.read_bytes()
        if sha256(data) != expected:
            raise BundleError("SHA-256 mismatch: " + name)
        if name.startswith(PAYLOAD):
            payload[name[len(PAYLOAD):]] = data
    return manifest, payload


def check_no_symlink_ancestors(path):
    for ancestor in (path,) + tuple(path.parents):
        if ancestor.is_symlink():
            raise BundleError("Destination uses a symlink: " + str(ancestor))
        if ancestor.exists() and ancestor != path and not ancestor.is_dir():
            raise BundleError("Destination parent is not a directory: " + str(ancestor))


def destination(args):
    if args.repo:
        repo = Path(args.repo).expanduser().resolve(strict=True)
        if not repo.is_dir():
            raise BundleError("--repo must point to an existing directory")
        result = repo / (".agents" if args.agent == "codex" else ".claude") / "skills" / NAME
    else:
        result = Path(os.path.abspath(os.path.expanduser(args.dest)))
    check_no_symlink_ancestors(result)
    return result


def install_marker(manifest, payload):
    return {
        "schema": 1,
        "installer": NAME,
        "version": manifest["version"],
        "files": {name: sha256(data) for name, data in sorted(payload.items())},
    }


def existing_is_identical(dest, expected):
    if not dest.is_dir() or not (dest / MARKER).is_file():
        raise BundleError("Destination already exists and is not an owned installation: " + str(dest))
    actual_files = tree_files(dest)
    marker = read_json(dest / MARKER)
    if marker != expected:
        raise BundleError("Destination has a different or edited installation; no files changed: " + str(dest))
    if actual_files != set(expected["files"]) | {MARKER}:
        raise BundleError("Destination contains added or missing files; no files changed: " + str(dest))
    for name, expected_hash in expected["files"].items():
        if sha256(dest.joinpath(*PurePosixPath(name).parts).read_bytes()) != expected_hash:
            raise BundleError("Destination contains edited files; no files changed: " + str(dest))
    return True


def install(root, dest, dry_run=False):
    manifest, payload = load_bundle(root)
    expected = install_marker(manifest, payload)
    if dest.exists():
        existing_is_identical(dest, expected)
        print("Already installed; no changes: " + str(dest))
        return
    if dest.resolve().is_relative_to(root.resolve()) or root.resolve().is_relative_to(dest.resolve()):
        raise BundleError("Destination must not overlap the source bundle")
    if dry_run:
        print("Verified {} files. Would install {} {} to {}".format(len(payload), NAME, manifest["version"], dest))
        return
    created_parents = []
    current = dest.parent
    while not current.exists():
        created_parents.append(current)
        current = current.parent
    stage = None
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        check_no_symlink_ancestors(dest)
        stage = Path(tempfile.mkdtemp(prefix=".ui-craft-stage-", dir=dest.parent))
        for name, data in payload.items():
            target = stage.joinpath(*PurePosixPath(name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        (stage / MARKER).write_text(json.dumps(expected, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if dest.exists() or dest.is_symlink():
            raise BundleError("Destination appeared during installation; refusing replacement")
        stage.rename(dest)
        stage = None
    finally:
        if stage is not None:
            shutil.rmtree(stage)
        for parent in created_parents:
            try:
                parent.rmdir()
            except OSError:
                pass
    print("Installed {} {} to {}".format(NAME, manifest["version"], dest))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--repo", help="Existing project directory")
    target.add_argument("--dest", help="Exact skill directory for another agent")
    parser.add_argument("--agent", choices=("codex", "claude"), help="Required with --repo")
    parser.add_argument("--dry-run", action="store_true", help="Verify and show destination without writing")
    args = parser.parse_args()
    if bool(args.repo) != bool(args.agent):
        parser.error("Use --repo with --agent, or --dest without --agent")
    try:
        install(Path(__file__).absolute().parent, destination(args), args.dry_run)
    except (BundleError, OSError) as exc:
        print("Error: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
