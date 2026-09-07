"""Installer contract tests using isolated bundles and destination directories."""

import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
LEGACY_NAME = "ui-craft-bundle"
LEGACY_PREFIX = "skills/" + LEGACY_NAME + "/"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(root):
    """Include directories and links so refusal tests detect incidental writes."""
    result = {".": ("directory", root.stat().st_mtime_ns)}
    for path in sorted(root.rglob("*")):
        name = path.relative_to(root).as_posix()
        modified = path.lstat().st_mtime_ns
        if path.is_symlink():
            result[name] = ("link", str(path.readlink()), modified)
        elif path.is_dir():
            result[name] = ("directory", modified)
        else:
            result[name] = ("file", path.read_bytes(), modified)
    return result


class InstallerTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ai-slop-installer-test-")
        self.addCleanup(self.temporary.cleanup)
        # macOS exposes its temporary directory through /var -> /private/var.
        # Use the real root; dedicated cases introduce links intentionally.
        self.workspace = Path(self.temporary.name).resolve()
        self.bundle = self.workspace / "bundle"
        self.bundle.mkdir()
        self.dest = self.workspace / "destination" / LEGACY_NAME
        self.repo = self.workspace / "project"
        self.repo.mkdir()

    def run_installer(self, *args):
        return subprocess.run(
            [sys.executable, str(self.bundle / "install.py"), *map(str, args)],
            cwd=self.workspace,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def assert_refused_without_changes(self, *args):
        before = snapshot(self.workspace)
        result = self.run_installer(*args)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(snapshot(self.workspace), before)
        return result

    def write_manifest(self):
        (self.bundle / "manifest.json").write_text(
            json.dumps(self.manifest, indent=2) + "\n", encoding="utf-8"
        )

    def write_payload(self, name, data):
        path = self.bundle / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def assert_payload_installed(self, skill, dest):
        prefix = "skills/" + skill + "/"
        for name, expected_hash in self.manifest["files"].items():
            if name.startswith(prefix):
                path = dest / name[len(prefix):]
                self.assertTrue(path.is_file(), str(path))
                self.assertEqual(digest(path.read_bytes()), expected_hash, name)


@unittest.skipUnless(shutil.which("git"), "Git is required for checkout regression tests")
class CheckoutInstallerTests(InstallerTestCase):
    def run_git(self, *args):
        result = subprocess.run(
            ["git", "-c", "core.attributesFile=" + os.devnull, *map(str, args)],
            cwd=self.workspace,
            env=dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assert_success(result)
        return result

    def test_fresh_clones_preserve_release_bytes_and_install(self):
        # Commit a disposable release snapshot so uncommitted checkout rules are
        # exercised without changing the developer's index, config, or files.
        self.manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        names = set(self.manifest["files"]) | {"manifest.json", "scripts/update_manifest.py"}
        if (ROOT / ".gitattributes").exists():
            names.add(".gitattributes")
        source_bytes = {name: (ROOT / name).read_bytes() for name in sorted(names)}
        for name, data in source_bytes.items():
            self.write_payload(name, data)
        source = self.bundle
        self.run_git("init", "--quiet", "--template=", source)
        self.run_git("-C", source, "-c", "core.autocrlf=false", "add", "--", *sorted(names))
        self.run_git(
            "-C", source, "-c", "user.name=Checkout regression",
            "-c", "user.email=checkout-test@example.invalid", "-c", "commit.gpgsign=false",
            "commit", "--quiet", "-m", "Preserve release bytes for checkout regression tests",
        )
        source_before = snapshot(source)

        for autocrlf in ("false", "true"):
            with self.subTest(autocrlf=autocrlf):
                self.bundle = self.workspace / ("checkout-" + autocrlf)
                self.run_git(
                    "-c", "core.autocrlf=" + autocrlf, "clone", "--quiet",
                    "--no-hardlinks", source, self.bundle,
                )
                self.repo = self.workspace / ("project-" + autocrlf)
                user_files = self.repo / "user-files"
                user_files.mkdir(parents=True)
                (user_files / "notes.txt").write_bytes(b"Keep user content\r\n")
                user_before = snapshot(user_files)

                before = snapshot(self.workspace)
                listing = self.run_installer("--list")
                self.assert_success(listing)
                for skill in self.manifest["skills"]:
                    self.assertIn(skill + " (dependencies:", listing.stdout)
                check = subprocess.run(
                    [sys.executable, str(self.bundle / "scripts/update_manifest.py"), "--check"],
                    cwd=self.workspace, capture_output=True, text=True, timeout=15, check=False,
                )
                self.assert_success(check)
                self.assertEqual(snapshot(self.workspace), before)
                # This includes the banner PNG as well as every hashed text file.
                for name, data in source_bytes.items():
                    self.assertEqual((self.bundle / name).read_bytes(), data, name)

                for agent, folder in (("codex", ".agents"), ("claude", ".claude")):
                    with self.subTest(agent=agent):
                        before = snapshot(self.workspace)
                        self.assert_success(self.run_installer(
                            "--repo", self.repo, "--agent", agent, "--dry-run",
                        ))
                        self.assertEqual(snapshot(self.workspace), before)
                        self.assert_success(self.run_installer("--repo", self.repo, "--agent", agent))
                        skill_root = self.repo / folder / "skills"
                        self.assertEqual({path.name for path in skill_root.iterdir()}, set(self.manifest["skills"]))
                        for skill in self.manifest["skills"]:
                            self.assert_payload_installed(skill, skill_root / skill)
                        for name, data in source_bytes.items():
                            if name.startswith("skills/"):
                                self.assertEqual((skill_root / name[len("skills/"):]).read_bytes(), data, name)
                        self.assertEqual(snapshot(user_files), user_before)

                changed = self.bundle / "README.ko.md"
                changed.write_bytes(changed.read_bytes() + b"\nChanged after checkout\n")
                for agent in ("codex", "claude"):
                    result = self.assert_refused_without_changes("--repo", self.repo, "--agent", agent)
                    self.assertIn("SHA-256 mismatch: README.ko.md", result.stderr)
                self.assertEqual(snapshot(source), source_before)


class LegacyInstallerTests(InstallerTestCase):
    def setUp(self):
        super().setUp()
        # Copy only declared legacy files. Repository metadata and macOS noise
        # must not make the exported-bundle regression fixture invalid.
        source_manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        names = [
            name for name in source_manifest["files"]
            if name in ("install.py", "README.ko.md") or name.startswith(LEGACY_PREFIX)
        ]
        self.manifest = {"schema": 1, "name": LEGACY_NAME, "version": "1.0.0", "files": {}}
        for name in names:
            data = (ROOT / name).read_bytes()
            self.write_payload(name, data)
            self.manifest["files"][name] = digest(data)
        self.write_manifest()

    def test_dry_run_creates_no_files_or_directories(self):
        before = snapshot(self.workspace)
        self.assert_success(self.run_installer("--dest", self.dest, "--dry-run"))
        self.assertEqual(snapshot(self.workspace), before)

    def test_fresh_install_copies_verified_payload(self):
        self.assert_success(self.run_installer("--dest", self.dest))
        self.assert_payload_installed(LEGACY_NAME, self.dest)
        self.assertFalse((self.dest / "install.py").exists())
        self.assertFalse((self.dest / "manifest.json").exists())
        self.assertTrue((self.dest / ".ui-craft-bundle-install.json").is_file())

    def test_second_install_is_identical_and_writes_nothing(self):
        self.assert_success(self.run_installer("--dest", self.dest))
        before = snapshot(self.workspace)
        self.assert_success(self.run_installer("--dest", self.dest))
        self.assertEqual(snapshot(self.workspace), before)

    def test_status_supports_legacy_bundle_records_without_writing(self):
        self.assert_success(self.run_installer("--dest", self.dest))
        before = snapshot(self.workspace)
        result = self.run_installer("--dest", self.dest, "--status")
        self.assert_success(result)
        self.assertIn("Status: identical installation", result.stdout)
        self.assertIn("Installed version: 1.0.0; release version: 1.0.0", result.stdout)
        self.assertEqual(snapshot(self.workspace), before)

    def test_edited_destination_is_preserved(self):
        self.assert_success(self.run_installer("--dest", self.dest))
        (self.dest / "SKILL.md").write_text("User customization\n", encoding="utf-8")
        self.assert_refused_without_changes("--dest", self.dest)

    def test_additional_destination_file_is_preserved(self):
        self.assert_success(self.run_installer("--dest", self.dest))
        (self.dest / "user-notes.md").write_text("Do not delete", encoding="utf-8")
        self.assert_refused_without_changes("--dest", self.dest)

    def test_missing_destination_file_is_not_silently_repaired(self):
        self.assert_success(self.run_installer("--dest", self.dest))
        (self.dest / "SKILL.md").unlink()
        self.assert_refused_without_changes("--dest", self.dest)

    def test_existing_unowned_directory_is_preserved(self):
        self.dest.mkdir(parents=True)
        self.assert_refused_without_changes("--dest", self.dest)

    def test_modified_source_fails_hash_check(self):
        (self.bundle / LEGACY_PREFIX / "SKILL.md").write_text("Changed\n", encoding="utf-8")
        result = self.assert_refused_without_changes("--dest", self.dest)
        self.assertIn("SHA-256", result.stderr)

    def test_unlisted_source_file_is_rejected(self):
        (self.bundle / "unexpected.txt").write_text("Not declared", encoding="utf-8")
        self.assert_refused_without_changes("--dest", self.dest)

    def test_manifest_traversal_is_rejected(self):
        for unsafe in ("../outside.txt", "skills/ui-craft-bundle/../outside.txt", "/tmp/outside.txt"):
            with self.subTest(path=unsafe):
                self.manifest["files"][unsafe] = "0" * 64
                self.write_manifest()
                self.assert_refused_without_changes("--dest", self.dest)
                del self.manifest["files"][unsafe]
        self.write_manifest()

    def test_source_payload_symlink_is_rejected(self):
        source = self.bundle / LEGACY_PREFIX / "SKILL.md"
        outside = self.workspace / "outside.md"
        shutil.copyfile(source, outside)
        source.unlink()
        source.symlink_to(outside)
        self.assert_refused_without_changes("--dest", self.dest)

    def test_manifest_symlink_is_rejected(self):
        manifest = self.bundle / "manifest.json"
        outside = self.workspace / "external-manifest.json"
        manifest.rename(outside)
        manifest.symlink_to(outside)
        self.assert_refused_without_changes("--dest", self.dest)

    def test_destination_symlink_is_rejected(self):
        self.dest.parent.mkdir()
        self.dest.symlink_to(self.repo, target_is_directory=True)
        self.assert_refused_without_changes("--dest", self.dest)

    def test_destination_parent_symlink_is_rejected(self):
        self.dest.parent.symlink_to(self.repo, target_is_directory=True)
        self.assert_refused_without_changes("--dest", self.dest)

    def test_destination_inside_source_is_rejected(self):
        self.assert_refused_without_changes("--dest", self.bundle / "new-install")

    def test_source_inside_destination_is_rejected(self):
        self.assert_refused_without_changes("--dest", self.workspace)

    def test_repository_install_uses_agent_skill_directory(self):
        for agent, folder in (("codex", ".agents"), ("claude", ".claude")):
            with self.subTest(agent=agent):
                self.assert_success(self.run_installer("--repo", self.repo, "--agent", agent))
                self.assert_payload_installed(LEGACY_NAME, self.repo / folder / "skills" / LEGACY_NAME)

    def test_invalid_cli_combinations_do_not_write(self):
        cases = (
            (),
            ("--repo", self.repo),
            ("--agent", "codex"),
            ("--dest", self.dest, "--agent", "codex"),
            ("--repo", self.repo, "--dest", self.dest, "--agent", "codex"),
            ("--repo", self.repo, "--agent", "unknown"),
            ("--repo", self.workspace / "missing", "--agent", "codex"),
            ("--repo", self.bundle / "install.py", "--agent", "codex"),
        )
        for args in cases:
            with self.subTest(args=args):
                self.assert_refused_without_changes(*args)

    def test_legacy_load_bundle_api_returns_flat_payload(self):
        api = runpy.run_path(str(self.bundle / "install.py"))
        manifest, payload = api["load_bundle"](self.bundle)
        self.assertEqual(manifest, self.manifest)
        expected_names = {
            name[len(LEGACY_PREFIX):]
            for name in self.manifest["files"] if name.startswith(LEGACY_PREFIX)
        }
        self.assertEqual(set(payload), expected_names)
        for name, data in payload.items():
            self.assertIsInstance(data, bytes)
            self.assertEqual(digest(data), self.manifest["files"][LEGACY_PREFIX + name])

    def test_legacy_install_api_keeps_dry_run_and_idempotency_contract(self):
        api = runpy.run_path(str(self.bundle / "install.py"))
        before = snapshot(self.workspace)
        with contextlib.redirect_stdout(io.StringIO()):
            api["install"](self.bundle, self.dest, dry_run=True)
        self.assertEqual(snapshot(self.workspace), before)
        with contextlib.redirect_stdout(io.StringIO()):
            api["install"](self.bundle, self.dest)
        self.assert_payload_installed(LEGACY_NAME, self.dest)
        installed = snapshot(self.workspace)
        with contextlib.redirect_stdout(io.StringIO()):
            api["install"](self.bundle, self.dest)
        self.assertEqual(snapshot(self.workspace), installed)


class SkillSetInstallerTests(InstallerTestCase):
    def setUp(self):
        super().setUp()
        # Synthetic packages isolate installer behavior from skill authoring and
        # release hash updates happening elsewhere in the checkout.
        self.dependencies = {
            LEGACY_NAME: [],
            "ai-slop-audit": [LEGACY_NAME],
            "ai-slop-refine": ["ai-slop-audit", LEGACY_NAME],
            "ui-copy": [],
        }
        self.manifest = {
            "schema": 2,
            "name": "ai-slop-remover",
            "version": "2.0.0",
            "skills": {
                name: {"dependencies": dependencies}
                for name, dependencies in self.dependencies.items()
            },
            "files": {},
        }
        self.add_file("install.py", (ROOT / "install.py").read_bytes())
        self.add_file("README.ko.md", "설치 안내\n".encode())
        for name in self.dependencies:
            self.add_file(
                "skills/" + name + "/SKILL.md",
                ("---\nname: " + name + "\ndescription: Fixture skill\n---\n# " + name + "\n").encode(),
            )
            self.add_file("skills/" + name + "/references/guide.md", (name + " reference\n").encode())
        self.write_manifest()

    def add_file(self, name, data):
        self.write_payload(name, data)
        self.manifest["files"][name] = digest(data)

    def installed_names(self, folder=".agents"):
        root = self.repo / folder / "skills"
        return {path.name for path in root.iterdir()} if root.exists() else set()

    def install_repo(self, *args):
        return self.run_installer("--repo", self.repo, "--agent", "codex", *args)

    def assert_repo_refused(self, *args):
        return self.assert_refused_without_changes("--repo", self.repo, "--agent", "codex", *args)

    def status_repo(self, *args):
        before = snapshot(self.workspace)
        result = self.install_repo("--status", *args)
        self.assert_success(result)
        self.assertEqual(snapshot(self.workspace), before)
        return result.stdout

    def status_block(self, output, name):
        return output.split(name + ":\n", 1)[1].split("\n\n", 1)[0]

    def status_without_reading(self, forbidden):
        before = snapshot(self.workspace)
        api = runpy.run_path(str(self.bundle / "install.py"))
        original_open = Path.open

        def guarded_open(path, *args, **kwargs):
            self.assertFalse(path.resolve().is_relative_to(forbidden), "Status opened an outside target: " + str(path))
            return original_open(path, *args, **kwargs)

        output = io.StringIO()
        with mock.patch.object(Path, "open", guarded_open), mock.patch.object(sys, "argv", [
            "install.py", "--repo", str(self.repo), "--agent", "codex", "--status",
        ]), contextlib.redirect_stdout(output):
            self.assertEqual(api["main"](), 0)
        self.assertEqual(snapshot(self.workspace), before)
        return output.getvalue()

    def test_status_lists_missing_selection_and_dependencies_without_creating_directories(self):
        output = self.status_repo("--skill", "ai-slop-refine", "--skill", "ai-slop-audit")
        for name in (LEGACY_NAME, "ai-slop-audit", "ai-slop-refine"):
            block = self.status_block(output, name)
            self.assertIn("Status: not installed", block)
            self.assertIn("Installed version: none; release version: 2.0.0", block)
            self.assertIn(str(self.repo / ".agents" / "skills" / name), block)
        self.assertNotIn("ui-copy:", output)
        self.assertEqual(output.count("Status:"), 3)
        self.assertIn("Checked 3 skills (including dependencies). No files changed.", output)

    def test_status_reports_identical_installs_for_both_agents(self):
        for agent in ("codex", "claude"):
            with self.subTest(agent=agent):
                args = ("--repo", self.repo, "--agent", agent)
                self.assert_success(self.run_installer(*args))
                before = snapshot(self.workspace)
                result = self.run_installer(*args, "--status")
                self.assert_success(result)
                self.assertEqual(snapshot(self.workspace), before)
                self.assertEqual(result.stdout.count("Status: identical installation"), len(self.dependencies))
                self.assertNotIn("Review and back up", result.stdout)

    def test_status_reports_2_1_to_2_2_as_version_only_while_install_still_refuses(self):
        self.manifest["version"] = "2.1.0"
        self.write_manifest()
        self.assert_success(self.install_repo())
        self.manifest["version"] = "2.2.0"
        self.write_manifest()
        output = self.status_repo()
        for name in self.dependencies:
            block = self.status_block(output, name)
            self.assertIn("Installed version: 2.1.0; release version: 2.2.0", block)
            self.assertIn("Status: version only; skill contents identical", block)
            self.assertIn("Local changes vs installation record: none", block)
            self.assertIn("Release changes vs installation record: none", block)
            self.assertIn("Review and back up before reinstalling: " + str(self.repo / ".agents" / "skills" / name), block)
        self.assert_repo_refused("--dry-run")
        self.assert_repo_refused()

    def test_status_compares_local_and_release_changes_independently_against_record(self):
        self.assert_success(self.install_repo())
        cases = (
            ("ai-slop-audit", False, True, "release content changed"),
            ("ai-slop-refine", True, False, "user modifications"),
            ("ui-copy", True, True, "release content changed; user modifications"),
        )
        for name, local_change, release_change, status in cases:
            dest = self.repo / ".agents" / "skills" / name
            prefix = "skills/" + name + "/"
            if release_change:
                self.add_file(prefix + "SKILL.md", b"Shared revised contents\n")
                self.add_file(prefix + "references/release.md", b"Release addition\n")
                (self.bundle / prefix / "references/guide.md").unlink()
                del self.manifest["files"][prefix + "references/guide.md"]
            if local_change:
                # Even when local bytes already equal the new release, both
                # changed independently from the recorded installation.
                (dest / "SKILL.md").write_bytes(b"Shared revised contents\n")
                (dest / "references/guide.md").unlink()
                (dest / "references/local-notes.md").write_bytes(b"Private user notes\n")
        self.write_manifest()
        output = self.status_repo()
        for name, local_change, release_change, status in cases:
            with self.subTest(skill=name):
                block = self.status_block(output, name)
                self.assertIn("Status: " + status, block)
                local, release = block.split("  Release changes vs installation record:", 1)
                for section, changed, added in (
                    (local, local_change, "references/local-notes.md"),
                    (release, release_change, "references/release.md"),
                ):
                    if changed:
                        for action, path in (("added", added), ("deleted", "references/guide.md"), ("modified", "SKILL.md")):
                            self.assertIn(action + ": " + json.dumps(path), section)
                    else:
                        self.assertIn("none", section)
                self.assertIn("Review and back up before reinstalling: " + str(self.repo / ".agents" / "skills" / name), block)
        self.assertNotIn("Private user notes", output)
        self.assertNotIn("Shared revised contents", output)
        self.assert_repo_refused()

    def test_status_continues_after_first_unowned_destination(self):
        dest = self.repo / ".agents" / "skills" / LEGACY_NAME
        dest.mkdir(parents=True)
        (dest / "SKILL.md").write_text("Private user skill\n", encoding="utf-8")
        output = self.status_repo()
        self.assertIn("Status: unverifiable", self.status_block(output, LEGACY_NAME))
        for name in set(self.dependencies) - {LEGACY_NAME}:
            self.assertIn("Status: not installed", self.status_block(output, name))
        self.assertNotIn("Private user skill", output)
        self.assert_repo_refused()

    def test_status_treats_malformed_records_as_unverifiable_and_continues(self):
        self.assert_success(self.install_repo())
        marker = self.repo / ".agents" / "skills" / LEGACY_NAME / ".ui-craft-bundle-install.json"
        original = json.loads(marker.read_text(encoding="utf-8"))
        cases = ["{Private broken receipt", "[]", '{"schema": 1, "schema": 1}']
        for field, value in (
            ("schema", True), ("schema", 2), ("installer", "another-installer"),
            ("version", "Private invalid version"), ("version", None),
            ("files", []), ("files", {}), ("files", {"SKILL.md": "not-a-hash"}),
            ("files", {"references/guide.md": "0" * 64}),
        ):
            record = dict(original, **{field: value})
            cases.append(json.dumps(record))
        for unsafe in ("../private.txt", "/private.txt", "references/../../private.txt", "a\\private.txt", "C:private.txt", "./private.txt", "."):
            record = dict(original, files={**original["files"], unsafe: "0" * 64})
            cases.append(json.dumps(record))
        for files in (
            {"skill.md": "0" * 64},
            {".ui-craft-bundle-install.json": "0" * 64},
            {"references": "0" * 64},
        ):
            cases.append(json.dumps(dict(original, files={**original["files"], **files})))
        cases.extend((json.dumps({**original, "extra": "Private receipt field"}), json.dumps({key: value for key, value in original.items() if key != "installer"})))
        for record in cases:
            with self.subTest(record=record):
                marker.write_text(record, encoding="utf-8")
                output = self.status_repo()
                self.assertIn("Status: unverifiable", self.status_block(output, LEGACY_NAME))
                self.assertEqual(output.count("Status: identical installation"), len(self.dependencies) - 1)
                self.assertNotIn("Private", output)

    def test_status_continues_after_deeply_nested_receipt(self):
        self.assert_success(self.install_repo())
        marker = self.repo / ".agents" / "skills" / LEGACY_NAME / ".ui-craft-bundle-install.json"
        marker.write_text("[" * 2000 + "0" + "]" * 2000, encoding="utf-8")
        output = self.status_repo()
        self.assertIn("Status: unverifiable", self.status_block(output, LEGACY_NAME))
        self.assertEqual(output.count("Status:"), len(self.dependencies))
        self.assertEqual(output.count("Status: identical installation"), len(self.dependencies) - 1)
        refused = self.assert_repo_refused()
        self.assertNotIn("Traceback", refused.stderr)

    def test_status_reports_deletions_leaving_empty_directories_and_added_empty_directories(self):
        self.assert_success(self.install_repo())
        dest = self.repo / ".agents" / "skills" / LEGACY_NAME
        (dest / "private-empty").mkdir()
        block = self.status_block(self.status_repo(), LEGACY_NAME)
        self.assertIn("Status: user modifications", block)
        self.assertIn('added directory: "private-empty/"', block)
        self.assertNotIn("deleted:", block)
        (dest / "references/guide.md").unlink()
        block = self.status_block(self.status_repo(), LEGACY_NAME)
        self.assertIn("Status: user modifications", block)
        self.assertIn('deleted: "references/guide.md"', block)
        self.assertIn('added directory: "private-empty/"', block)
        self.assertNotIn('added directory: "references/"', block)
        self.assert_repo_refused()

    def test_status_never_reads_files_addressed_by_forged_receipt_paths(self):
        self.assert_success(self.install_repo())
        marker = self.repo / ".agents" / "skills" / LEGACY_NAME / ".ui-craft-bundle-install.json"
        outside = self.workspace / "private.txt"
        outside.write_bytes(b"Sensitive contents that must not be opened\n")
        record = json.loads(marker.read_text(encoding="utf-8"))
        record["files"][os.path.relpath(outside, marker.parent)] = digest(outside.read_bytes())
        marker.write_text(json.dumps(record), encoding="utf-8")
        output = self.status_without_reading(outside)
        self.assertIn("Status: unverifiable", output)
        self.assertNotIn("Sensitive contents", output)

    def test_status_marks_symlinks_unverifiable_without_reading_targets(self):
        for location in ("destination", "parent", "marker", "file", "directory", "dangling"):
            with self.subTest(location=location):
                self.repo = self.workspace / ("project-" + location)
                self.repo.mkdir()
                self.assert_success(self.install_repo())
                dest = self.repo / ".agents" / "skills" / LEGACY_NAME
                target = {
                    "destination": dest, "parent": dest.parent,
                    "marker": dest / ".ui-craft-bundle-install.json",
                    "file": dest / "SKILL.md", "directory": dest / "references",
                    "dangling": dest,
                }[location]
                outside = self.workspace / ("outside-" + location)
                target.rename(outside)
                target.symlink_to(outside if location != "dangling" else self.workspace / "absent", target_is_directory=outside.is_dir())
                output = self.status_without_reading(outside)
                self.assertIn("Status: unverifiable", self.status_block(output, LEGACY_NAME))
                self.assertEqual(output.count("Status:"), len(self.dependencies))
                if location != "parent":
                    self.assertEqual(output.count("Status: identical installation"), len(self.dependencies) - 1)
                self.assert_repo_refused()

    def test_status_marks_unreadable_subdirectories_unverifiable_instead_of_deleted(self):
        self.assert_success(self.install_repo())
        dest = self.repo / ".agents" / "skills" / LEGACY_NAME
        api = runpy.run_path(str(self.bundle / "install.py"))
        manifest, packages = api["load_packages"](self.bundle)
        original_scandir = os.scandir

        def guarded_scandir(path):
            if Path(path) == dest / "references":
                raise PermissionError("Cannot inspect fixture directory")
            return original_scandir(path)

        before = snapshot(self.workspace)
        output = io.StringIO()
        with mock.patch.object(os, "scandir", guarded_scandir), contextlib.redirect_stdout(output):
            api["report_status"](self.bundle, dest, manifest, LEGACY_NAME, packages[LEGACY_NAME])
        self.assertIn("Status: unverifiable", output.getvalue())
        self.assertNotIn("deleted:", output.getvalue())
        self.assertEqual(snapshot(self.workspace), before)

    def test_status_is_mutually_exclusive_with_dry_run_and_list(self):
        for args in (("--list", "--status"), ("--repo", self.repo, "--agent", "codex", "--status", "--dry-run")):
            result = self.assert_refused_without_changes(*args)
            self.assertEqual(result.returncode, 2)

    def test_status_supports_exact_destination_and_preserves_overlap_safety(self):
        self.assert_success(self.run_installer("--dest", self.dest, "--skill", "ui-copy"))
        before = snapshot(self.workspace)
        result = self.run_installer("--dest", self.dest, "--skill", "ui-copy", "--status")
        self.assert_success(result)
        self.assertIn("Status: identical installation", result.stdout)
        self.assertEqual(snapshot(self.workspace), before)
        for dest in (self.bundle / "new-skill", self.workspace):
            result = self.run_installer("--dest", dest, "--status")
            self.assert_success(result)
            self.assertIn("Status: unverifiable", result.stdout)
            self.assertEqual(snapshot(self.workspace), before)

    def test_default_installs_every_skill_for_each_agent(self):
        for agent, folder in (("codex", ".agents"), ("claude", ".claude")):
            with self.subTest(agent=agent):
                self.assert_success(self.run_installer("--repo", self.repo, "--agent", agent))
                self.assertEqual(self.installed_names(folder), set(self.dependencies))
                for name in self.dependencies:
                    self.assert_payload_installed(name, self.repo / folder / "skills" / name)

    def test_success_output_identifies_each_installed_skill(self):
        result = self.install_repo()
        self.assert_success(result)
        messages = result.stdout.splitlines()
        for name in self.dependencies:
            self.assertTrue(
                any(line.startswith("Installed " + name + " 2.0.0 to ") for line in messages),
                result.stdout,
            )

    def test_dry_run_checks_every_skill_without_writing(self):
        before = snapshot(self.workspace)
        result = self.install_repo("--dry-run")
        self.assert_success(result)
        self.assertEqual(snapshot(self.workspace), before)
        for name in self.dependencies:
            self.assertIn(name, result.stdout)

    def test_second_full_install_is_unchanged(self):
        self.assert_success(self.install_repo())
        before = snapshot(self.workspace)
        self.assert_success(self.install_repo())
        self.assertEqual(snapshot(self.workspace), before)

    def test_selection_installs_recursive_dependencies(self):
        self.assert_success(self.install_repo("--skill", "ai-slop-refine"))
        expected = {"ai-slop-refine", "ai-slop-audit", LEGACY_NAME}
        self.assertEqual(self.installed_names(), expected)
        for name in expected:
            self.assert_payload_installed(name, self.repo / ".agents" / "skills" / name)

    def test_repeatable_selection_unions_and_deduplicates_dependencies(self):
        self.assert_success(self.install_repo(
            "--skill", "ai-slop-audit", "--skill", "ui-copy", "--skill", "ai-slop-audit"
        ))
        self.assertEqual(self.installed_names(), {"ai-slop-audit", LEGACY_NAME, "ui-copy"})

    def test_standalone_selection_excludes_unrelated_skills(self):
        self.assert_success(self.install_repo("--skill", "ui-copy"))
        self.assertEqual(self.installed_names(), {"ui-copy"})

    def test_exact_destination_defaults_to_legacy_skill(self):
        self.assert_success(self.run_installer("--dest", self.dest))
        self.assert_payload_installed(LEGACY_NAME, self.dest)
        self.assertFalse((self.dest.parent / "ai-slop-audit").exists())

    def test_exact_destination_accepts_explicit_standalone_skill(self):
        self.assert_success(self.run_installer("--dest", self.dest, "--skill", "ui-copy"))
        self.assert_payload_installed("ui-copy", self.dest)

    def test_exact_destination_rejects_skill_with_dependencies(self):
        result = self.assert_refused_without_changes("--dest", self.dest, "--skill", "ai-slop-audit")
        self.assertIn("--repo", result.stderr)

    def test_exact_destination_rejects_multiple_skills(self):
        self.assert_refused_without_changes(
            "--dest", self.dest, "--skill", LEGACY_NAME, "--skill", "ui-copy"
        )

    def test_unknown_selection_is_rejected_without_writing(self):
        self.assert_repo_refused("--skill", "unknown-skill")

    def test_list_needs_no_destination_and_does_not_write(self):
        before = snapshot(self.workspace)
        result = self.run_installer("--list")
        self.assert_success(result)
        self.assertEqual(snapshot(self.workspace), before)
        for name in self.dependencies:
            self.assertIn(name, result.stdout)

    def test_conflict_in_last_destination_prevents_all_new_installations(self):
        conflict = self.repo / ".agents" / "skills" / "ui-copy"
        conflict.mkdir(parents=True)
        (conflict / "SKILL.md").write_text("Existing user skill\n", encoding="utf-8")
        self.assert_repo_refused()
        self.assertEqual(self.installed_names(), {"ui-copy"})

    def test_changed_dependency_prevents_installing_selected_skill(self):
        self.assert_success(self.install_repo("--skill", LEGACY_NAME))
        source = self.repo / ".agents" / "skills" / LEGACY_NAME / "SKILL.md"
        source.write_text("Keep user edit\n", encoding="utf-8")
        self.assert_repo_refused("--skill", "ai-slop-refine")
        self.assertEqual(self.installed_names(), {LEGACY_NAME})

    def test_added_file_in_new_skill_is_never_removed_or_overwritten(self):
        self.assert_success(self.install_repo("--skill", "ui-copy"))
        dest = self.repo / ".agents" / "skills" / "ui-copy"
        (dest / "user-notes.md").write_text("Keep notes\n", encoding="utf-8")
        self.assert_repo_refused()

    def test_dry_run_reports_destination_conflict_without_writing(self):
        (self.repo / ".agents" / "skills" / "ui-copy").mkdir(parents=True)
        self.assert_repo_refused("--dry-run")

    def test_known_checkout_files_do_not_enter_installed_payload(self):
        for name in (".git/HEAD", "docs/plan.md", "tests/test_sample.py", "scripts/build.py"):
            self.write_payload(name, b"Checkout-only content\n")
        self.assert_success(self.install_repo())
        for name in self.dependencies:
            dest = self.repo / ".agents" / "skills" / name
            self.assert_payload_installed(name, dest)
            self.assertFalse((dest / "docs").exists())
            self.assertFalse((dest / ".git").exists())

    def test_worktree_git_file_is_allowed_as_checkout_metadata(self):
        self.write_payload(".git", b"gitdir: /nonexistent/worktree\n")
        self.assert_success(self.install_repo())

    def test_macos_metadata_is_ignored_inside_payload(self):
        for name in (".DS_Store", "skills/.DS_Store", "skills/ui-copy/.DS_Store"):
            self.write_payload(name, b"Finder metadata")
        self.assert_success(self.install_repo())
        for name in self.dependencies:
            self.assertFalse((self.repo / ".agents" / "skills" / name / ".DS_Store").exists())

    def test_unlisted_file_in_skill_payload_is_rejected(self):
        self.write_payload("skills/ui-copy/extra.txt", b"Unlisted payload")
        self.assert_repo_refused()

    def test_unlisted_hidden_payload_file_is_rejected(self):
        self.write_payload("skills/ui-copy/.hidden", b"Unlisted hidden payload")
        self.assert_repo_refused()

    def test_unlisted_skill_directory_is_rejected(self):
        self.write_payload("skills/unlisted/SKILL.md", b"Unlisted skill")
        self.assert_repo_refused()

    def test_missing_listed_payload_is_rejected(self):
        (self.bundle / "skills/ui-copy/references/guide.md").unlink()
        self.assert_repo_refused()

    def test_missing_required_skill_entrypoint_is_rejected(self):
        name = "skills/ui-copy/SKILL.md"
        del self.manifest["files"][name]
        (self.bundle / name).unlink()
        self.write_manifest()
        self.assert_repo_refused()

    def test_changed_readme_fails_hash_check(self):
        (self.bundle / "README.ko.md").write_text("Changed readme\n", encoding="utf-8")
        result = self.assert_repo_refused()
        self.assertIn("SHA-256", result.stderr)

    def test_changed_installer_fails_hash_check(self):
        with (self.bundle / "install.py").open("a", encoding="utf-8") as installer:
            installer.write("\n# Source changed after packaging\n")
        result = self.assert_repo_refused()
        self.assertIn("SHA-256", result.stderr)

    def test_unselected_skill_hash_is_still_verified(self):
        (self.bundle / "skills/ui-copy/SKILL.md").write_text("Corrupted\n", encoding="utf-8")
        result = self.assert_repo_refused("--skill", LEGACY_NAME)
        self.assertIn("SHA-256", result.stderr)

    def test_unknown_dependency_is_rejected(self):
        self.manifest["skills"]["ai-slop-audit"]["dependencies"] = ["absent"]
        self.write_manifest()
        self.assert_repo_refused()

    def test_dependency_cycle_is_rejected(self):
        self.manifest["skills"][LEGACY_NAME]["dependencies"] = ["ai-slop-refine"]
        self.write_manifest()
        self.assert_repo_refused()

    def test_invalid_skill_identifier_is_rejected(self):
        self.manifest["skills"]["../outside"] = {"dependencies": []}
        self.write_manifest()
        self.assert_repo_refused()

    def test_invalid_manifest_metadata_is_reported_without_traceback(self):
        original = json.dumps(self.manifest)
        cases = (
            ("version", None), ("version", 2), ("version", "invalid"),
            ("skills", None), ("skills", []), ("skills", {}),
            ("files", None), ("files", []), ("files", {}),
        )
        for key, value in cases:
            with self.subTest(field=key, value=value):
                self.manifest = json.loads(original)
                self.manifest[key] = value
                self.write_manifest()
                result = self.assert_repo_refused()
                self.assertNotIn("Traceback", result.stderr)

    def test_invalid_skill_metadata_is_reported_without_traceback(self):
        original = json.dumps(self.manifest)
        cases = (
            None, [], "not-an-object", {},
            {"dependencies": None}, {"dependencies": "ui-craft-bundle"},
            {"dependencies": [None]}, {"dependencies": [{}]},
            {"dependencies": [LEGACY_NAME, LEGACY_NAME]},
        )
        for metadata in cases:
            with self.subTest(metadata=metadata):
                self.manifest = json.loads(original)
                self.manifest["skills"]["ai-slop-audit"] = metadata
                self.write_manifest()
                result = self.assert_repo_refused()
                self.assertNotIn("Traceback", result.stderr)

    def test_reserved_install_markers_cannot_be_declared_as_payload(self):
        for marker in (".ui-craft-bundle-install.json", ".ai-slop-remover-install.json"):
            with self.subTest(marker=marker):
                name = "skills/ui-copy/" + marker
                self.add_file(name, b"{}\n")
                self.write_manifest()
                result = self.assert_repo_refused()
                self.assertIn("Reserved", result.stderr)
                del self.manifest["files"][name]
                (self.bundle / name).unlink()

    def test_case_colliding_payload_paths_are_rejected(self):
        original = "skills/ui-copy/SKILL.md"
        self.manifest["files"]["skills/ui-copy/skill.md"] = self.manifest["files"][original]
        self.write_manifest()
        result = self.assert_repo_refused()
        self.assertIn("Case-colliding", result.stderr)

    def test_invalid_hash_metadata_is_reported_without_traceback(self):
        for invalid_hash in (None, 42, [], "0" * 63, "A" * 64):
            with self.subTest(value=invalid_hash):
                self.manifest["files"]["skills/ui-copy/SKILL.md"] = invalid_hash
                self.write_manifest()
                result = self.assert_repo_refused()
                self.assertIn("SHA-256", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_manifest_traversal_is_rejected(self):
        self.manifest["files"]["skills/ui-copy/../../outside"] = "0" * 64
        self.write_manifest()
        self.assert_repo_refused()

    def test_duplicate_manifest_keys_are_rejected(self):
        manifest = self.bundle / "manifest.json"
        data = manifest.read_text(encoding="utf-8").replace('"schema": 2,', '"schema": 2, "schema": 2,', 1)
        manifest.write_text(data, encoding="utf-8")
        self.assert_repo_refused()

    def test_payload_symlink_is_rejected_even_when_hash_matches(self):
        source = self.bundle / "skills/ui-copy/SKILL.md"
        outside = self.workspace / "outside.md"
        source.rename(outside)
        source.symlink_to(outside)
        self.assert_repo_refused()

    def test_skill_directory_symlink_is_rejected(self):
        source = self.bundle / "skills/ui-copy"
        outside = self.workspace / "outside-skill"
        source.rename(outside)
        source.symlink_to(outside, target_is_directory=True)
        self.assert_repo_refused()

    def test_agent_skill_root_symlink_is_rejected(self):
        (self.repo / ".agents").mkdir()
        outside = self.workspace / "outside-skills"
        outside.mkdir()
        (self.repo / ".agents" / "skills").symlink_to(outside, target_is_directory=True)
        self.assert_repo_refused()

    def test_one_destination_symlink_prevents_all_installations(self):
        skill_root = self.repo / ".agents" / "skills"
        skill_root.mkdir(parents=True)
        outside = self.workspace / "outside-skill"
        outside.mkdir()
        (skill_root / "ui-copy").symlink_to(outside, target_is_directory=True)
        self.assert_repo_refused()

    def test_exact_destination_inside_source_is_rejected(self):
        self.assert_refused_without_changes("--dest", self.bundle / "new-skill")


if __name__ == "__main__":
    unittest.main()
