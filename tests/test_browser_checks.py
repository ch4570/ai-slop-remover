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
QUERY_FROM_URL = "el('query').value = new URL(location.href).searchParams.get('q') || '';"
POPSTATE = "window.addEventListener('popstate', () => {\n  " + QUERY_FROM_URL + "\n  renderNotes();\n});"


def evidence_snapshot(root):
    return {str(path.relative_to(root)): (path.is_dir(), path.stat().st_mtime_ns,
                                        None if path.is_dir() else path.read_bytes())
            for path in [root, *root.rglob('*')]}


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
        self.observed = observed
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

    def test_existing_browser_artifacts_are_preserved(self):
        env = {**os.environ, "AI_SLOP_CHROME": str(self.root / "absent-chrome")}
        for artifact in ("browser.json", "wide.png", "narrow.png", "keyboard.png"):
            with self.subTest(artifact=artifact):
                output = self.evidence / ("existing-" + artifact)
                output.mkdir()
                (output / artifact).write_bytes(b"Previous collection evidence must survive unchanged.")
                before = evidence_snapshot(output)
                run = subprocess.run(["node", str(ROOT / "scripts/run_browser_checks.mjs"),
                                      str(ROOT / "evals/fixtures/search-editor"), str(output)],
                                     capture_output=True, text=True, timeout=30, env=env)
                self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
                self.assertIn("new output path", run.stderr)
                self.assertEqual(before, evidence_snapshot(output))

    def test_started_collection_reserves_output_exclusively(self):
        output = self.evidence / 'interrupted-collection'
        script = f"import {{ claimBrowserEvidence }} from {json.dumps((ROOT / 'scripts/browser_harness.mjs').as_uri())};\n"
        script += "const results = await Promise.allSettled([0, 1].map(() => claimBrowserEvidence(process.argv[1], ['wide.png', 'narrow.png', 'keyboard.png'])));\n"
        script += "console.log(JSON.stringify(results.map(result => ({ status: result.status, reason: String(result.reason || '') }))));\n"
        run = subprocess.run(['node', '--input-type=module', '--eval', script, str(output)],
                             capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        attempts = json.loads(run.stdout)
        self.assertEqual(sorted(attempt['status'] for attempt in attempts), ['fulfilled', 'rejected'])
        self.assertIn('new output path', next(attempt['reason'] for attempt in attempts if attempt['status'] == 'rejected'))
        # The reserving process exits before writing browser evidence. Both drivers
        # must still reject this interrupted output without changing its artifacts.
        self.assertFalse((output / 'browser.json').exists())
        before = evidence_snapshot(output)
        env = {**os.environ, 'AI_SLOP_CHROME': str(self.root / 'absent-chrome')}
        for arguments in ([str(ROOT / 'scripts/run_browser_checks.mjs'), str(ROOT / 'evals/fixtures/search-editor')],
                          [str(ROOT / 'scripts/run_scope_checks.mjs'), 'narrow-spacing', str(ROOT / 'evals/fixtures/narrow-spacing/product')]):
            run = subprocess.run(['node', *arguments, str(output)], capture_output=True, text=True, timeout=30, env=env)
            self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
            self.assertIn('new output path', run.stderr)
            self.assertEqual(before, evidence_snapshot(output))

    def test_unavailable_browser_uses_a_fresh_output_and_preserves_failed_runs(self):
        env = {**os.environ, 'AI_SLOP_CHROME': str(self.root / 'absent-chrome')}
        output = self.evidence / 'fresh-unavailable-browser'
        command = ['node', str(ROOT / 'scripts/run_browser_checks.mjs'), str(ROOT / 'evals/fixtures/search-editor')]
        run = subprocess.run([*command, str(output)], capture_output=True, text=True, timeout=30, env=env)
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        browser = json.loads((output / 'browser.json').read_text())
        self.assertEqual({check['status'] for check in browser['checks']}, {'not-run'})
        self.assertTrue(browser['collectionErrors'])
        before = evidence_snapshot(output)
        run = subprocess.run([*command, str(output)], capture_output=True, text=True, timeout=30, env=env)
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
        self.assertEqual(before, evidence_snapshot(output))
        fresh = self.evidence / 'another-fresh-unavailable-browser'
        run = subprocess.run([*command, str(fresh)], capture_output=True, text=True, timeout=30, env=env)
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        self.assertTrue((fresh / 'browser.json').is_file())
        self.assertEqual(before, evidence_snapshot(output))

    def test_record_order_does_not_change_integrity(self):
        source = replace_once(repaired_source(), SAVE, SAVE[:-1] + ".reverse();")
        checks = self.run_fixture("reordered", source)
        self.assertEqual(set(checks.values()), {"pass"}, checks)

    def test_missing_popstate_restoration_is_rejected(self):
        source = replace_once(repaired_source(), POPSTATE, "")
        checks = self.run_fixture("missing-popstate", source)
        self.assert_failed(checks, "history-back", "history-forward")

    def test_popstate_must_restore_the_list(self):
        source = replace_once(repaired_source(), POPSTATE,
                              "window.addEventListener('popstate', () => {\n  " + QUERY_FROM_URL + "\n});")
        checks = self.run_fixture("popstate-stale-list", source)
        self.assert_failed(checks, "history-back", "history-forward")

    def test_popstate_must_restore_the_count(self):
        source = replace_once(repaired_source(), POPSTATE,
                              POPSTATE.replace("renderNotes();", "renderNotes();\n  el('count').textContent = '99개 메모';"))
        checks = self.run_fixture("popstate-stale-count", source)
        self.assert_failed(checks, "history-back", "history-forward")

    def test_direct_entry_and_reload_must_restore_query(self):
        source = replace_once(repaired_source(), QUERY_FROM_URL + "\n\nfunction showStatus",
                              "el('query').value = '';\n\nfunction showStatus")
        checks = self.run_fixture("entry-ignores-query", source)
        self.assert_failed(checks, "query-direct-entry", "query-reload")

    def test_reload_query_restoration_has_its_own_observation(self):
        source = replace_once(repaired_source(), QUERY_FROM_URL + "\n\nfunction showStatus",
                              QUERY_FROM_URL + "\nif (performance.getEntriesByType('navigation')[0].type === 'reload') "
                              "el('query').value = '';\n\nfunction showStatus")
        checks = self.run_fixture("reload-ignores-query", source)
        self.assertEqual(checks.get("query-direct-entry"), "pass", checks)
        self.assert_failed(checks, "query-reload")

    def test_unobserved_popstate_cannot_pass_or_erase_later_checks(self):
        source = replace_once(repaired_source(), POPSTATE,
                              POPSTATE.replace("() => {", "event => {\n  if (!event.isTrusted) return;\n"
                                               "  event.stopImmediatePropagation();\n"
                                               "  queueMicrotask(() => window.dispatchEvent("
                                               "new PopStateEvent('popstate', { state: event.state })));"))
        checks = self.run_fixture("unobserved-popstate", source)
        for check_id in ("history-back", "history-forward"):
            self.assertEqual(checks.get(check_id), "not-run", checks)
        for check_id in ("query-direct-entry", "query-reload", "ordinary-enter-reload"):
            self.assertEqual(checks.get(check_id), "pass", checks)
        for check in self.observed["checks"]:
            if check["id"] in ("history-back", "history-forward"):
                self.assertIn("popstate", check["reason"])
                navigations = json.loads(check["evidence"]["text"])["navigations"]
                self.assertTrue(navigations)
                for navigation in navigations:
                    self.assertFalse(navigation["completed"])
                    self.assertIn("timeout", navigation["reason"].lower())
                    self.assertTrue(navigation["stateMatches"])

    def test_unavailable_shared_document_keeps_prior_failures(self):
        source = replace_once(repaired_source(), POPSTATE, "")
        source += "\nif (new URL(location.href).searchParams.get('q') === '긴 한국어') el('save').remove();\n"
        checks = self.run_fixture("unavailable-shared-document", source)
        self.assert_failed(checks, "history-back", "history-forward")
        for check_id in ("query-direct-entry", "query-reload"):
            self.assertEqual(checks.get(check_id), "not-run", checks)
        self.assertEqual(checks["ordinary-enter-reload"], "pass", checks)
        for check in self.observed["checks"]:
            if check["id"] in ("query-direct-entry", "query-reload"):
                self.assertIn("Fixture did not finish loading", check["reason"])

    def test_unavailable_save_reload_keeps_prior_failures_and_missing_checks(self):
        source = replace_once(repaired_source(), "history.replaceState({}, '', url);",
                              "history.pushState({}, '', url);")
        source += "\nif (notes.find(note => note.id === 1).title !== initialNotes[0].title) el('save').remove();\n"
        checks = self.run_fixture("unavailable-save-reload", source, allow_exceptions=True)
        self.assert_failed(checks, "query-history")
        for check_id in ("search-matches", "failed-save-draft", "failed-save-feedback", "failed-save-storage", "retry-persists"):
            self.assertEqual(checks[check_id], "pass", checks)
        self.assertEqual(sum(status == "not-run" for status in checks.values()), 10, checks)
        self.assertTrue(self.observed["collectionErrors"])
        for check in self.observed["checks"]:
            if check["status"] == "not-run":
                self.assertIn("Fixture did not finish loading", check["reason"])

    def test_unavailable_initial_document_records_every_required_check(self):
        source = repaired_source() + "\nel('save').remove();\n"
        checks = self.run_fixture("unavailable-initial-document", source, allow_exceptions=True)
        self.assertEqual(set(checks.values()), {"not-run"}, checks)
        self.assertTrue(self.observed["collectionErrors"])

    def test_image_state_failure_keeps_completed_behavior_observations(self):
        source = repaired_source()
        source += "\nel('editor').addEventListener('submit', () => { if (innerWidth < 400) location.href = 'about:blank'; });\n"
        checks = self.run_fixture("unavailable-image-state", source, allow_exceptions=True)
        self.assertEqual(set(checks.values()), {"pass"}, checks)
        self.assertTrue(self.observed["collectionErrors"])

    def test_delayed_earlier_input_cannot_replace_the_final_query(self):
        source = replace_once(repaired_source(), "history.replaceState({}, '', url);",
                              "history.replaceState({}, '', url);\n  if (el('query').value === '배') "
                              "setTimeout(() => history.replaceState({}, '', url), 50);")
        checks = self.run_fixture("delayed-stale-query", source)
        self.assert_failed(checks, "query-history")

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
