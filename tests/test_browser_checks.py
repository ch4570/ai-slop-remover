"""Opt-in Chrome regressions using synthetic fixture copies and actual outcomes."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SAVE = "const updated = notes.map(note => note.id === draft.id ? draft : note);"


def replace_once(source, before, after):
    if source.count(before) != 1:
        raise AssertionError(f"Fixture changed; expected one mutation site: {before!r}")
    return source.replace(before, after)


def repaired_source():
    source = (ROOT / "evals/fixtures/search-editor/app.js").read_text(encoding="utf-8")
    for before, after in (
        ("history.pushState({}, '', url);", "history.replaceState({}, '', url);"),
        ("if (event.key === 'Enter') {", "if (event.key === 'Enter' && !event.isComposing) {"),
        ("    renderNotes();\n  } catch {\n    openNote(selectedId);",
         "    renderNotes();\n    showStatus('success', '메모를 저장했습니다.');\n  } catch {\n"
         "    showStatus('error', '저장에 실패했습니다. 다시 시도하세요.');"),
        ("    el('save').disabled = false;\n    showStatus('success', '메모를 저장했습니다.');",
         "    el('save').disabled = false;"),
    ):
        source = replace_once(source, before, after)
    return source


@unittest.skipUnless(os.environ.get("AI_SLOP_BROWSER_TESTS") == "1",
                     "Opt in with AI_SLOP_BROWSER_TESTS=1 (existing Chrome and Node 22+).")
class BrowserCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="slop-check-tests-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        evidence_root = Path(os.environ.get("AI_SLOP_BROWSER_EVIDENCE", cls.root / "evidence"))
        evidence_root.mkdir(parents=True, exist_ok=True)
        # A failed driver must never be mistaken for evidence from an earlier run.
        cls.evidence = Path(tempfile.mkdtemp(prefix="run-", dir=evidence_root))

    def run_fixture(self, name, source, allow_exceptions=False):
        fixture = self.root / name
        shutil.copytree(ROOT / "evals/fixtures/search-editor", fixture)
        (fixture / "app.js").write_text(source, encoding="utf-8")
        output = self.evidence / name
        run = subprocess.run(
            ["node", str(ROOT / "scripts/run_browser_checks.mjs"), str(fixture), str(output)],
            capture_output=True, text=True, timeout=90,
        )
        self.assertIn(run.returncode, (0, 1) if allow_exceptions else (0,), run.stdout + run.stderr)
        self.assertTrue((output / "browser.json").is_file(), run.stdout + run.stderr)
        observed = json.loads((output / "browser.json").read_text(encoding="utf-8"))
        if not allow_exceptions:
            self.assertEqual(observed["exceptions"], [])
        checks = observed["checks"]
        suite = json.loads((ROOT / "evals/checks/suite.json").read_text(encoding="utf-8"))
        required = {key for key, kind in suite["cases"]["search-editor"].items() if kind == "behavior"}
        self.assertEqual({check["id"] for check in checks}, required)
        self.assertEqual(len(checks), len(required))
        return {check["id"]: check["status"] for check in checks}

    def assert_failed(self, checks, *ids):
        for check_id in ids:
            self.assertEqual(checks.get(check_id), "fail", f"{check_id}: {checks}")

    def test_repaired_control_passes(self):
        checks = self.run_fixture("repaired", repaired_source())
        self.assertEqual(set(checks.values()), {"pass"}, checks)

    def test_record_order_does_not_change_integrity(self):
        source = replace_once(repaired_source(), SAVE, SAVE[:-1] + ".reverse();")
        checks = self.run_fixture("reordered", source)
        self.assertEqual(set(checks.values()), {"pass"}, checks)

    def test_data_loss_is_rejected(self):
        source = replace_once(repaired_source(), SAVE, "const updated = [draft];")
        # Dropping id 1 also breaks the fixture's initial selection after reload.
        # Require complete behavioral observations, not merely a nonzero exit.
        checks = self.run_fixture("data-loss", source, allow_exceptions=True)
        self.assert_failed(checks, "retry-persists", "ordinary-save", "ordinary-enter")

    def test_other_record_changes_are_rejected(self):
        source = replace_once(repaired_source(), SAVE,
                              "const updated = notes.map(note => note.id === draft.id ? draft "
                              ": { ...note, body: 'Unrelated content overwritten' });")
        checks = self.run_fixture("other-record-change", source)
        self.assert_failed(checks, "retry-persists", "ordinary-save", "ordinary-enter")

    def test_duplicate_ids_are_rejected(self):
        source = replace_once(repaired_source(), SAVE,
                              SAVE + "\n    updated[2] = { ...updated[2], id: updated[1].id };")
        checks = self.run_fixture("duplicate-id", source)
        self.assert_failed(checks, "retry-persists", "ordinary-save", "ordinary-enter")

    def test_hard_coded_id_one_update_is_rejected(self):
        source = replace_once(repaired_source(), SAVE,
                              "const updated = notes.map(note => note.id === 1 ? { ...draft, id: 1 } : note);")
        checks = self.run_fixture("hard-coded-id", source)
        self.assertEqual(checks["retry-persists"], "pass")
        self.assert_failed(checks, "ordinary-save", "ordinary-enter")

    def test_failure_cannot_mutate_other_notes(self):
        source = replace_once(repaired_source(), "if (shouldFail) throw new Error('연습용 저장 실패');",
                              "if (shouldFail) {\n"
                              "      localStorage.setItem(storageKey, JSON.stringify(notes.map(note => "
                              "note.id === 2 ? { ...note, body: 'Changed during failure' } : note)));\n"
                              "      throw new Error('연습용 저장 실패');\n    }")
        checks = self.run_fixture("failure-storage", source)
        self.assert_failed(checks, "failed-save-storage")

    def test_reload_must_read_persisted_notes(self):
        source = replace_once(repaired_source(),
                              "let notes = JSON.parse(localStorage.getItem(storageKey) || 'null') || initialNotes;",
                              "let notes = initialNotes;")
        checks = self.run_fixture("reload-ignores-storage", source)
        for check_id in ("retry-persists", "ordinary-save", "ordinary-enter"):
            self.assertEqual(checks[check_id], "pass", checks)
        self.assert_failed(checks, "retry-reload", "ordinary-reload", "ordinary-enter-reload")

    def test_reload_cannot_reset_storage(self):
        source = replace_once(repaired_source(), "const el = id => document.getElementById(id);",
                              "localStorage.setItem(storageKey, JSON.stringify(initialNotes));\n"
                              "const el = id => document.getElementById(id);")
        checks = self.run_fixture("reload-resets-storage", source)
        self.assert_failed(checks, "retry-reload", "ordinary-reload", "ordinary-enter-reload")

    def test_original_fixture_keeps_its_intended_failures(self):
        source = (ROOT / "evals/fixtures/search-editor/app.js").read_text(encoding="utf-8")
        checks = self.run_fixture("original", source)
        self.assert_failed(checks, "query-history", "failed-save-draft", "failed-save-feedback", "composition-enter")
        for check_id in ("search-matches", "ordinary-save", "ordinary-enter"):
            self.assertEqual(checks[check_id], "pass", checks)


if __name__ == "__main__":
    unittest.main()
