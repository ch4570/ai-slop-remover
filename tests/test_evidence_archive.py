"""Read-only verification of recorded evidence inventories and tar archives."""

import copy
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock
import zlib


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_evidence_archive.py"
spec = importlib.util.spec_from_file_location("check_evidence_archive", SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def inventory(files, schema=1):
    entries = {name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
               for name, data in files.items()}
    if schema is None:
        return {"agent": "recorded-trial", "files": {
            name: entry["sha256"] for name, entry in entries.items()}}
    return {"schema": schema, "baseline_commit": "recorded-revision", "files": entries}


def member(name, data=b"", kind=tarfile.REGTYPE, **attributes):
    header = tarfile.TarInfo(name)
    header.type = kind
    header.size = len(data)
    for key, value in attributes.items():
        setattr(header, key, value)
    return header, data


class EvidenceArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.inventory_path = self.root / "inventory.json"
        self.archive_path = self.root / "evidence.tar.gz"
        self.files = {"tools/check.py": b"print('recorded evidence')\n",
                      "captures/wide.png": b"\x89PNG\r\n\x1a\nrecorded bytes\0",
                      "captures/.browser-evidence-started": b"trial marker\n",
                      "empty.txt": b""}

    def write_inventory(self, value=None):
        self.inventory_path.write_text(
            json.dumps(inventory(self.files) if value is None else value), encoding="utf-8")

    def write_archive(self, members=None, mode="w:gz"):
        if members is None:
            members = [member("./", kind=tarfile.DIRTYPE),
                       member("./tools/", kind=tarfile.DIRTYPE),
                       member("./captures/", kind=tarfile.DIRTYPE)]
            members += [member("./" + name, data) for name, data in self.files.items()]
        with tarfile.open(self.archive_path, mode, format=tarfile.PAX_FORMAT) as archive:
            for header, data in members:
                archive.addfile(header, io.BytesIO(data))

    def run_cli(self, expected_code=0, contains=None):
        before = {path.name: path.read_bytes() for path in self.root.iterdir() if path.is_file()}
        run = subprocess.run([sys.executable, "-B", str(SCRIPT),
                              str(self.inventory_path), str(self.archive_path)],
                             cwd=self.root, capture_output=True, text=True)
        self.assertEqual(run.returncode, expected_code, run.stdout + run.stderr)
        self.assertEqual(run.stderr, "")
        result = json.loads(run.stdout)
        self.assertEqual(result["verdict"], "verified" if expected_code == 0 else "invalid")
        if contains:
            self.assertIn(contains, "\n".join(result.get("errors", [])))
        self.assertEqual(set(path.name for path in self.root.iterdir()), set(before))
        self.assertEqual({path.name: path.read_bytes() for path in self.root.iterdir()}, before)
        return result

    def test_existing_inventory_formats_and_compression_are_verified(self):
        for schema in (None, 1):
            for mode in ("w", "w:gz", "w:bz2", "w:xz"):
                with self.subTest(schema=schema, mode=mode):
                    self.write_inventory(inventory(self.files, schema))
                    self.write_archive(mode=mode)
                    result = self.run_cli()
                    self.assertEqual(result["files"], len(self.files))
                    self.assertEqual(result["bytes"], sum(map(len, self.files.values())))
                    self.assertEqual(result["inventory_format"], "legacy" if schema is None else "schema-1")

    def test_regular_members_without_directory_headers_are_valid(self):
        self.write_inventory()
        self.write_archive([member(name, data) for name, data in self.files.items()])
        self.run_cli()

    def test_unlisted_empty_directory_is_allowed(self):
        self.write_inventory()
        self.write_archive([member(name, data) for name, data in self.files.items()]
                           + [member("unused/", kind=tarfile.DIRTYPE)])
        self.run_cli()

    def test_pax_long_unicode_path_is_valid(self):
        self.files = {"한글/" + "recorded-evidence-" * 12 + ".txt": b"observation\n"}
        self.write_inventory()
        self.write_archive()
        self.run_cli()

    def test_appledouble_sidecar_is_an_extra_regular_file(self):
        self.write_inventory()
        self.write_archive([member(name, data) for name, data in self.files.items()]
                           + [member("./captures/._wide.png", b"AppleDouble metadata")])
        self.run_cli(1, "unexpected regular files: ['captures/._wide.png']")

    def test_missing_modified_and_wrong_size_evidence(self):
        for change, diagnostic in (("missing", "missing regular files"),
                                   ("modified", "SHA-256 mismatch"),
                                   ("wrong-size", "size mismatch")):
            with self.subTest(change=change):
                expected = inventory(self.files)
                archived = dict(self.files)
                if change == "missing":
                    del archived["tools/check.py"]
                elif change == "modified":
                    archived["tools/check.py"] = b"x" * len(archived["tools/check.py"])
                else:
                    expected["files"]["tools/check.py"]["bytes"] += 1
                self.write_inventory(expected)
                self.write_archive([member(name, data) for name, data in archived.items()])
                self.run_cli(1, diagnostic)

    def test_duplicate_normalized_regular_and_directory_paths(self):
        for duplicate in ([member("a", b"x"), member("a", b"x")],
                          [member("a", b"x"), member("./a", b"x")],
                          [member("a/", kind=tarfile.DIRTYPE), member("./a/", kind=tarfile.DIRTYPE)],
                          [member(".", kind=tarfile.DIRTYPE), member("./", kind=tarfile.DIRTYPE)]):
            with self.subTest(paths=[item[0].name for item in duplicate]):
                self.write_inventory(inventory({"a": b"x"}))
                self.write_archive(duplicate)
                self.run_cli(1, "duplicate normalized path")

    def test_unsafe_or_ambiguous_tar_paths(self):
        for name in ("../outside", "/absolute", "a/../../outside", "a//b", "a/./b",
                     "././a", "a\\b", "C:/outside", "C:outside", "a\nb", ""):
            with self.subTest(name=name):
                self.write_inventory(inventory({}))
                self.write_archive([member(name, b"x")])
                self.run_cli(1, "path")

    def test_links_special_and_sparse_members_are_rejected(self):
        for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.CHRTYPE,
                     tarfile.BLKTYPE, tarfile.FIFOTYPE, tarfile.CONTTYPE,
                     tarfile.GNUTYPE_SPARSE, b"Z"):
            with self.subTest(kind=kind):
                self.write_inventory(inventory({}))
                self.write_archive([member("unsafe", kind=kind, linkname="../outside")])
                self.run_cli(1, "sparse" if kind == tarfile.GNUTYPE_SPARSE else "unsupported member type")

    def test_pax_sparse_marker_is_rejected(self):
        self.write_inventory(inventory({"sparse": b"x"}))
        self.write_archive([member("sparse", b"x", pax_headers={"GNU.sparse.name": "sparse"})])
        self.run_cli(1, "sparse")

    def test_file_directory_conflicts_are_rejected_regardless_of_order(self):
        for entries in ([member("a", b"x"), member("a/b", b"y")],
                        [member("a/b", b"y"), member("a", b"x")],
                        [member("a", b"x"), member("a/b/", kind=tarfile.DIRTYPE)]):
            with self.subTest(paths=[item[0].name for item in entries]):
                self.write_inventory(inventory({"a": b"x"}))
                self.write_archive(entries)
                self.run_cli(1, "file/directory conflict")

    def test_directory_payload_is_rejected(self):
        self.write_inventory(inventory({}))
        self.write_archive([member("a/", b"unexpected data", kind=tarfile.DIRTYPE)])
        self.run_cli(1, "directory has a payload")

    def test_truncated_payload_and_tar_terminator_are_rejected(self):
        self.files = {"evidence": b"x" * 2048}
        self.write_inventory()
        self.write_archive(mode="w")
        complete = self.archive_path.read_bytes()
        for length in (512 + 100, 512 + 2048, 512 + 2048 + 512):
            with self.subTest(length=length):
                self.archive_path.write_bytes(complete[:length])
                self.run_cli(1)

    def test_corrupt_header_is_rejected(self):
        self.write_inventory()
        self.write_archive(mode="w")
        data = bytearray(self.archive_path.read_bytes())
        data[0] ^= 1
        self.archive_path.write_bytes(data)
        self.run_cli(1)

    def test_oversized_metadata_headers_report_invalid_without_traceback(self):
        self.write_inventory(inventory({}))
        for kind in (tarfile.XHDTYPE, tarfile.XGLTYPE, tarfile.GNUTYPE_LONGNAME):
            with self.subTest(kind=kind):
                header = tarfile.TarInfo("oversized")
                header.type = kind
                header.size = 2 ** 80
                self.archive_path.write_bytes(header.tobuf(format=tarfile.GNU_FORMAT) + b"\0" * 1024)
                self.run_cli(1)

    def test_truncated_and_corrupt_compression_trailers_are_rejected(self):
        self.write_inventory()
        self.write_archive()
        complete = self.archive_path.read_bytes()
        corrupt_crc = bytearray(complete)
        corrupt_crc[-8] ^= 1
        for data in (complete[:-1], complete[:-8], bytes(corrupt_crc)):
            with self.subTest(length=len(data)):
                self.archive_path.write_bytes(data)
                self.run_cli(1)

    def test_corrupt_deflate_data_reports_invalid_without_traceback(self):
        self.write_inventory()
        self.write_archive()
        data = bytearray(gzip.compress(gzip.decompress(self.archive_path.read_bytes())))
        data[10] = 255  # Reserved DEFLATE block type, after gzip's ten-byte header.
        self.archive_path.write_bytes(data)
        # tarfile can wrap the decoder error in a generic ReadError depending
        # on the Python version. Assert the CLI contract, not stdlib wording.
        result = self.run_cli(1)
        self.assertIsInstance(result["errors"], list)
        self.assertTrue(result["errors"])
        self.assertTrue(all(isinstance(error, str) and error.strip()
                            for error in result["errors"]))

    def test_wrapped_and_raw_decoder_errors_report_invalid_json(self):
        for error in (tarfile.ReadError("file could not be opened successfully"),
                      zlib.error("Error -3 while decompressing data: invalid block type")):
            with self.subTest(error=type(error).__name__):
                output = io.StringIO()
                with mock.patch.object(checker, "verify_archive", side_effect=error), \
                        mock.patch.object(sys, "argv", [str(SCRIPT), str(self.inventory_path),
                                                       str(self.archive_path)]), \
                        mock.patch.object(sys, "stdout", output):
                    self.assertEqual(checker.main(), 1)
                self.assertEqual(json.loads(output.getvalue()),
                                 {"verdict": "invalid", "errors": [str(error)]})

    def test_invalid_unicode_in_inventory_path_still_reports_json(self):
        self.write_inventory(inventory({"../\ud800": b"x"}))
        self.write_archive()
        self.run_cli(1, "path")

    def test_nonzero_trailing_data_and_incomplete_padding_are_rejected(self):
        self.write_inventory()
        self.write_archive(mode="w")
        complete = self.archive_path.read_bytes()
        for tail, diagnostic in ((b"hidden bytes", "nonzero data"), (b"\0", "truncated tar padding")):
            with self.subTest(tail=tail):
                self.archive_path.write_bytes(complete + tail)
                self.run_cli(1, diagnostic)

    def test_malformed_and_duplicate_inventory_json_are_rejected(self):
        digest = hashlib.sha256(b"x").hexdigest()
        for raw, diagnostic in (("{", "Expecting"),
                                ('{"files":{},"files":{}}', "duplicate JSON key"),
                                ('{"files":{"a":"' + digest + '","a":"' + digest + '"}}', "duplicate JSON key"),
                                ('{"schema":1,"files":{"a":{"bytes":1,"bytes":1,"sha256":"' + digest + '"}}}', "duplicate JSON key"),
                                ('{"files":{},"metadata":NaN}', "invalid JSON number")):
            with self.subTest(raw=raw):
                self.inventory_path.write_text(raw, encoding="utf-8")
                self.write_archive()
                self.run_cli(1, diagnostic)

    def test_invalid_schema_entries_and_digests_are_rejected(self):
        good = inventory({"a": b"x"})
        invalid = [[], {}, {"files": []}, {"files": good["files"]},
                   {"schema": 1, "files": {"a": good["files"]["a"]["sha256"]}}]
        invalid += [dict(good, schema=value) for value in (True, False, 0, 2, 1.0, "1", None)]
        for size in (-1, True, False, 1.0, "1", None):
            value = copy.deepcopy(good)
            value["files"]["a"]["bytes"] = size
            invalid.append(value)
        for digest in ("a" * 63, "A" * 64, "g" * 64, "a" * 64 + "\n", None, 12):
            value = copy.deepcopy(good)
            value["files"]["a"]["sha256"] = digest
            invalid.append(value)
        invalid += [{"schema": 1, "files": {"a": {"sha256": "a" * 64}}},
                    {"schema": 1, "files": {"a": {"bytes": 1, "sha256": "a" * 64, "extra": 0}}},
                    {"files": {"a": "a" * 64, "b": good["files"]["a"]}}]
        self.write_archive()
        for value in invalid:
            with self.subTest(value=value):
                self.write_inventory(value)
                self.run_cli(1)

    def test_inventory_paths_must_be_canonical_relative_file_paths(self):
        for name in ("", "../outside", "/absolute", "./a", "a/./b", "a/../b", "a//b",
                     "a/", "a\\b", "C:/a", "a\0b"):
            with self.subTest(name=name):
                self.write_inventory(inventory({name: b"x"}))
                self.write_archive()
                self.run_cli(1, "path")
        self.write_inventory(inventory({"a": b"x", "a/b": b"y"}))
        self.run_cli(1, "file/directory conflict")

    def test_large_file_is_hashed_in_chunks_without_extraction(self):
        self.files = {"large": b"recorded bytes\n" * 200000}
        self.write_inventory()
        self.write_archive()
        original_read = tarfile.ExFileObject.read
        sizes = []

        def read(payload, size=-1):
            sizes.append(size)
            self.assertGreater(size, 0)
            self.assertLessEqual(size, checker.CHUNK_SIZE)
            return original_read(payload, size)

        with mock.patch.object(tarfile.ExFileObject, "read", read), \
                mock.patch.object(tarfile.TarFile, "extract", side_effect=AssertionError("extraction")), \
                mock.patch.object(tarfile.TarFile, "extractall", side_effect=AssertionError("extraction")):
            result = checker.verify_archive(self.inventory_path, self.archive_path)
        self.assertEqual(result["verdict"], "verified")
        self.assertGreater(len(sizes), 2)
        self.run_cli()

    def test_missing_inputs_report_invalid_and_usage_errors_exit_two(self):
        self.run_cli(1)
        self.write_inventory()
        self.run_cli(1)
        usage = subprocess.run([sys.executable, "-B", str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(usage.returncode, 2)
        self.assertIn("inventory archive", usage.stderr)
        help_result = subprocess.run([sys.executable, "-B", str(SCRIPT), "--help"],
                                     capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)
        self.assertIn("0 verified, 1 invalid", help_result.stdout)


if __name__ == "__main__":
    unittest.main()
