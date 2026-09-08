#!/usr/bin/env python3
"""Verify an evidence tar against its inventory without extracting any files."""

import argparse
import hashlib
import json
import lzma
from pathlib import Path
import re
import sys
import tarfile
import zlib


CHUNK_SIZE = 1024 * 1024


class InvalidEvidence(ValueError):
    """The inventory or archive does not satisfy the evidence contract."""


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidEvidence(f"inventory: duplicate JSON key {key!r}")
        result[key] = value
    return result


def invalid_constant(value):
    raise InvalidEvidence(f"inventory: invalid JSON number {value}")


def canonical_path(name, *, archive=False, directory=False):
    """Use POSIX paths; accept tar's conventional root and leading './'."""
    original = name
    if not isinstance(name, str) or not name:
        raise InvalidEvidence(f"invalid path: {original!r}")
    if "\\" in name or any(ord(char) < 32 or ord(char) == 127 for char in name):
        raise InvalidEvidence(f"unsafe or ambiguous path: {original!r}")
    if archive and name.startswith("./"):
        name = name[2:]
    if archive and directory:
        if name in ("", "."):
            return ""
        if name.endswith("/"):
            name = name[:-1]
    parts = name.split("/")
    if (not name or re.match(r"^[A-Za-z]:", name)
            or any(part in ("", ".", "..") for part in parts)):
        raise InvalidEvidence(f"unsafe or ambiguous path: {original!r}")
    return name


def parents(path):
    parts = path.split("/")
    return ("/".join(parts[:index]) for index in range(1, len(parts)))


def reject_file_directory_conflicts(files, directories):
    for path in files:
        if path in directories:
            raise InvalidEvidence(f"file/directory conflict: {path!r}")
    for path in set(files) | directories:
        for parent in parents(path):
            if parent in files:
                raise InvalidEvidence(f"file/directory conflict: {parent!r} contains {path!r}")


def load_inventory(path):
    inventory = json.loads(Path(path).read_text(encoding="utf-8"),
                           object_pairs_hook=unique_object,
                           parse_constant=invalid_constant)
    if not isinstance(inventory, dict):
        raise InvalidEvidence("inventory: expected a JSON object")
    schema = inventory.get("schema")
    if "schema" in inventory and (type(schema) is not int or schema != 1):
        raise InvalidEvidence("inventory: schema must be integer 1, or absent for legacy files")
    entries = inventory.get("files")
    if not isinstance(entries, dict):
        raise InvalidEvidence("inventory: files must be a path-to-digest object")
    files = {}
    for name, entry in entries.items():
        path = canonical_path(name)
        if schema == 1:
            if not isinstance(entry, dict) or set(entry) != {"bytes", "sha256"}:
                raise InvalidEvidence(f"inventory: {path!r} requires exactly bytes and sha256")
            size, digest = entry["bytes"], entry["sha256"]
            if type(size) is not int or size < 0:
                raise InvalidEvidence(f"inventory: {path!r} bytes must be a nonnegative integer")
        else:
            size, digest = None, entry
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise InvalidEvidence(f"inventory: {path!r} requires a lowercase SHA-256 digest")
        files[path] = {"bytes": size, "sha256": digest}
    reject_file_directory_conflicts(files, set())
    return files, "schema-1" if schema == 1 else "legacy"


def verify_tar_end(archive):
    """Check tar termination and consume compression trailers after logical EOF."""
    archive.fileobj.seek(archive.offset)
    length = 0
    while True:
        chunk = archive.fileobj.read(CHUNK_SIZE)
        if not chunk:
            break
        length += len(chunk)
        if chunk.strip(b"\0"):
            raise InvalidEvidence("archive: nonzero data after the last tar member")
    if length < 2 * tarfile.BLOCKSIZE:
        raise InvalidEvidence("archive: truncated tar terminator (two zero blocks required)")
    if length % tarfile.BLOCKSIZE:
        raise InvalidEvidence("archive: truncated tar padding (incomplete 512-byte block)")


def verify_archive(inventory_path, archive_path):
    """Match regular file names, bytes, and digests; do not assess evidence truth."""
    expected, inventory_format = load_inventory(inventory_path)
    seen = set()
    files = set()
    directories = set()
    total_bytes = 0
    errors = []
    with tarfile.open(archive_path, mode="r:*") as archive:
        for member in archive:
            path = canonical_path(member.name, archive=True, directory=member.isdir())
            if path in seen:
                raise InvalidEvidence(f"archive: duplicate normalized path {path!r}")
            seen.add(path)
            if (member.sparse is not None or member.type == tarfile.GNUTYPE_SPARSE
                    or any(key.startswith("GNU.sparse.") for key in member.pax_headers)):
                raise InvalidEvidence(f"archive: sparse member is unsupported: {path!r}")
            if member.isdir():
                if member.size != 0:
                    raise InvalidEvidence(f"archive: directory has a payload: {path!r}")
                directories.add(path)
                continue
            if member.type not in (tarfile.REGTYPE, tarfile.AREGTYPE):
                raise InvalidEvidence(f"archive: unsupported member type {member.type!r}: {path!r}")
            if member.size < 0:
                raise InvalidEvidence(f"archive: negative file size: {path!r}")
            files.add(path)
            digest = hashlib.sha256()
            size = 0
            with archive.extractfile(member) as payload:
                while True:
                    chunk = payload.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    digest.update(chunk)
                    size += len(chunk)
            if size != member.size:
                raise InvalidEvidence(f"archive: truncated payload: {path!r}")
            total_bytes += size
            if path in expected:
                entry = expected[path]
                if entry["bytes"] is not None and size != entry["bytes"]:
                    errors.append(f"size mismatch: {path!r}: expected {entry['bytes']}, got {size}")
                if digest.hexdigest() != entry["sha256"]:
                    errors.append(f"SHA-256 mismatch: {path!r}")
        verify_tar_end(archive)
    reject_file_directory_conflicts(files, directories)
    missing, extra = sorted(set(expected) - files), sorted(files - set(expected))
    if missing:
        errors.append(f"missing regular files: {missing!r}")
    if extra:
        errors.append(f"unexpected regular files: {extra!r}")
    if errors:
        return {"verdict": "invalid", "errors": errors}
    return {"verdict": "verified", "inventory_format": inventory_format,
            "files": len(files), "bytes": total_bytes,
            "limits": "Inventory/archive consistency only; evidence truth is not evaluated."}


def main():
    parser = argparse.ArgumentParser(
        description="Verify inventory file names, sizes, and SHA-256 against a tar archive, without extraction.",
        epilog="Exit codes: 0 verified, 1 invalid inventory/archive, 2 command-line usage error.")
    parser.add_argument("inventory", type=Path, help="JSON inventory (legacy or schema 1)")
    parser.add_argument("archive", type=Path, help="tar archive (optionally compressed)")
    args = parser.parse_args()
    try:
        result = verify_archive(args.inventory, args.archive)
    except (OSError, ValueError, EOFError, OverflowError,
            tarfile.TarError, zlib.error, lzma.LZMAError) as error:
        result = {"verdict": "invalid", "errors": [str(error)]}
    print(json.dumps(result, indent=2))
    return 0 if result["verdict"] == "verified" else 1


if __name__ == "__main__":
    sys.exit(main())
