"""Offline export integration checks on disposable copies of the real release."""

import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]


class ExportBundleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="lutriva-export-test-")
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name).resolve()
        self.bundle = self.workspace / "source bundle"
        self.manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.release_names = {"manifest.json", *self.manifest["files"]}
        for name in self.release_names | {"scripts/check_package.py", "scripts/export_bundle.py"}:
            target = self.bundle / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        self.output = self.workspace / "archives" / "offline bundle.zip"

    def source_snapshot(self):
        return {
            path.relative_to(self.bundle).as_posix(): (
                path.stat().st_mtime_ns,
                hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None,
            )
            for path in [self.bundle, *self.bundle.rglob("*")]
        }

    def run_export(self):
        return subprocess.run(
            [sys.executable, "-B", str(self.bundle / "scripts/export_bundle.py"),
             "--output", str(self.output)],
            cwd=self.workspace, capture_output=True, text=True, timeout=20, check=False,
        )

    def assert_verified_archive(self):
        with zipfile.ZipFile(self.output) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(set(archive.namelist()), self.release_names)
            self.assertEqual(len(archive.namelist()), len(self.release_names))
            for name in self.release_names:
                self.assertEqual(archive.read(name), (self.bundle / name).read_bytes(), name)
            for name, expected in self.manifest["files"].items():
                self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), expected, name)
            # These paths were validated above against the actual release list.
            extracted = self.workspace / "extracted bundle"
            archive.extractall(extracted)
        project = self.workspace / "new project"
        project.mkdir()
        result = subprocess.run(
            [sys.executable, "-B", str(extracted / "install.py"), "--repo", str(project),
             "--agent", "codex"],
            cwd=self.workspace, capture_output=True, text=True, timeout=20, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        skills = project / ".agents" / "skills"
        self.assertEqual({path.name for path in skills.iterdir()}, set(self.manifest["skills"]))
        for name in self.manifest["files"]:
            if name.startswith("skills/"):
                self.assertEqual((skills / name[len("skills/"):]).read_bytes(),
                                 (self.bundle / name).read_bytes(), name)

    def test_export_contains_verified_release_and_keeps_source_unchanged(self):
        before = self.source_snapshot()
        result = self.run_export()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_verified_archive()
        self.assertEqual(self.source_snapshot(), before)

    def test_pre_1980_file_time_is_clamped_without_changing_release_bytes(self):
        source = self.bundle / "README.ko.md"
        os.utime(source, (0, 0))
        before = self.source_snapshot()
        result = self.run_export()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with zipfile.ZipFile(self.output) as archive:
            self.assertEqual(archive.getinfo("README.ko.md").date_time, (1980, 1, 1, 0, 0, 0))
        self.assert_verified_archive()
        self.assertEqual(self.source_snapshot(), before)

    def test_post_2107_file_time_is_clamped_without_changing_release_bytes(self):
        source = self.bundle / "README.ko.md"
        future = datetime.datetime(2108, 1, 1).timestamp()
        try:
            os.utime(source, (future, future))
        except (OSError, OverflowError) as exc:
            self.skipTest("Filesystem cannot represent this timestamp: " + str(exc))
        self.assertGreater(datetime.datetime.fromtimestamp(source.stat().st_mtime).year, 2107)
        before = self.source_snapshot()
        result = self.run_export()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with zipfile.ZipFile(self.output) as archive:
            # ZIP stores seconds in two-second increments.
            self.assertEqual(archive.getinfo("README.ko.md").date_time, (2107, 12, 31, 23, 59, 58))
        self.assert_verified_archive()
        self.assertEqual(self.source_snapshot(), before)

    def test_existing_output_is_never_overwritten(self):
        self.output.parent.mkdir()
        self.output.write_bytes(b"User-owned existing archive\n")
        before = (self.output.read_bytes(), self.output.stat().st_mtime_ns, self.source_snapshot())
        result = self.run_export()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertNotIn("Exported ", result.stdout)
        self.assertEqual((self.output.read_bytes(), self.output.stat().st_mtime_ns,
                          self.source_snapshot()), before)

    def test_invalid_release_is_refused_before_creating_output(self):
        source = self.bundle / "README.ko.md"
        source.write_bytes(source.read_bytes() + b"\nUnreviewed content change\n")
        before = self.source_snapshot()
        result = self.run_export()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("SHA-256 mismatch", result.stderr)
        self.assertFalse(self.output.parent.exists())
        self.assertEqual(self.source_snapshot(), before)


if __name__ == "__main__":
    unittest.main()
