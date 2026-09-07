"""Fail-closed comparison of observed UI outcomes, independently of packaging."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/compare_evals.py"
spec = importlib.util.spec_from_file_location("compare_evals", SCRIPT)
comparator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparator)


def result(variant):
    suite = json.loads((ROOT / "evals/checks/suite.json").read_text())
    return {
        "schema": 1,
        "suite": suite["id"],
        "run_id": variant + "-trial",
        "variant": variant,
        "fixture": {"id": "search-editor", "sha256": "a" * 64},
        "task_sha256": "b" * 64,
        "model": "test-model-contract",
        "settings": {"reasoning": "high", "seed": 12},
        "skill_revision": "test-revision-" + variant,
        "cases": [{
            "id": case_id,
            "checks": [{
                "id": check_id, "kind": kind, "status": "pass",
                "evidence": {"text": "Observed draft remained after the failed save; storage unchanged."},
            } for check_id, kind in checks.items()],
        } for case_id, checks in suite["cases"].items()],
    }


class CompareEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.baseline = result("baseline")
        self.candidate = result("candidate")

    def compare(self):
        return comparator.compare(self.baseline, self.candidate)

    def invalid(self):
        self.assertEqual(self.compare()["verdict"], "invalid")

    def test_missing_evidence_cannot_pass(self):
        del self.candidate["cases"][0]["checks"][0]["evidence"]
        self.invalid()

    def test_placeholder_evidence_cannot_pass(self):
        for text in ("pass", "looks good", "TODO: collect evidence", "", "   "):
            with self.subTest(text=text):
                self.candidate["cases"][0]["checks"][0]["evidence"] = {"text": text}
                self.invalid()

    def test_duplicate_or_missing_checks_are_invalid(self):
        for mutate in (lambda checks: checks.pop(), lambda checks: checks.append(copy.deepcopy(checks[0]))):
            self.candidate = result("candidate")
            mutate(self.candidate["cases"][0]["checks"])
            self.invalid()

    def test_missing_same_check_in_both_runs_still_invalid(self):
        self.baseline["cases"][0]["checks"].pop()
        self.candidate["cases"][0]["checks"].pop()
        self.invalid()

    def test_each_storage_check_is_required_in_both_runs(self):
        for check_id in ("failed-save-storage", "retry-reload", "ordinary-reload", "ordinary-enter-reload"):
            with self.subTest(check_id=check_id):
                self.baseline, self.candidate = result("baseline"), result("candidate")
                for run in (self.baseline, self.candidate):
                    checks = run["cases"][0]["checks"]
                    self.assertIn(check_id, {check["id"] for check in checks})
                    checks[:] = [check for check in checks if check["id"] != check_id]
                self.invalid()

    def test_old_suite_cannot_claim_current_pass(self):
        self.baseline["suite"] = self.candidate["suite"] = "search-editor-v1"
        self.invalid()

    def test_example_tracks_the_current_suite_without_claiming_observations(self):
        example = json.loads((ROOT / "evals/examples/result-template.json").read_text(encoding="utf-8"))
        self.assertEqual(example["suite"], self.candidate["suite"])
        self.assertEqual(len(example["cases"]), len(self.candidate["cases"]))
        for sample, actual in zip(example["cases"], self.candidate["cases"]):
            self.assertEqual(sample["id"], actual["id"])
            self.assertEqual([(check["id"], check["kind"]) for check in sample["checks"]],
                             [(check["id"], check["kind"]) for check in actual["checks"]])
            self.assertEqual({check["status"] for check in sample["checks"]}, {"not-run"})

    def test_duplicate_or_empty_cases_are_invalid(self):
        self.candidate["cases"].append(copy.deepcopy(self.candidate["cases"][0]))
        self.invalid()
        self.candidate["cases"] = []
        self.invalid()

    def test_incomparable_runs_are_invalid(self):
        for field, value in (("model", "different-model"), ("settings", {"reasoning": "low"}), ("task_sha256", "c" * 64), ("fixture", {"id": "search-editor", "sha256": "d" * 64})):
            with self.subTest(field=field):
                self.candidate = result("candidate")
                self.candidate[field] = value
                self.invalid()

    def test_bogus_metadata_is_invalid(self):
        for field, value in (("schema", True), ("schema", 2), ("model", "unknown"), ("settings", {}), ("settings", {"temperature": float("nan")}), ("settings", {"reasoning": "TODO"}), ("task_sha256", "0" * 64), ("skill_revision", "example"), ("variant", "baseline")):
            with self.subTest(field=field, value=value):
                self.candidate = result("candidate")
                self.candidate[field] = value
                self.invalid()

    def test_same_run_id_is_invalid(self):
        self.candidate["run_id"] = self.baseline["run_id"]
        self.invalid()

    def test_unknown_status_and_kind_are_invalid(self):
        for field, value in (("status", "skipped"), ("kind", "package-check")):
            self.candidate = result("candidate")
            self.candidate["cases"][0]["checks"][0][field] = value
            self.invalid()

    def test_not_run_is_incomplete_even_with_all_other_checks_passing(self):
        check = self.candidate["cases"][0]["checks"][-1]
        check.update(status="not-run", reason="No browser was available for keyboard inspection.")
        check.pop("evidence")
        self.assertEqual(self.compare()["verdict"], "incomplete")

    def test_not_run_requires_a_concrete_reason(self):
        self.candidate["cases"][0]["checks"][0].update(status="not-run")
        self.invalid()

    def test_failed_candidate_requires_changes_and_identifies_check(self):
        self.candidate["cases"][0]["checks"][0]["status"] = "fail"
        verdict = self.compare()
        self.assertEqual(verdict["verdict"], "changes-required")
        self.assertEqual(verdict["regressions"], ["search-editor/search-matches"])

    def test_observed_failure_takes_priority_over_unexecuted_checks(self):
        self.candidate["cases"][0]["checks"][0]["status"] = "fail"
        self.candidate["cases"][0]["checks"][-1].update(
            status="not-run", reason="No browser was available for keyboard inspection.")
        verdict = self.compare()
        self.assertEqual(verdict["verdict"], "changes-required")
        self.assertEqual(verdict["candidate_failures"], ["search-editor/search-matches"])
        self.assertEqual(verdict["not_run"], ["candidate/search-editor/narrow-keyboard-review"])

    def test_unverified_baseline_cannot_establish_improvement(self):
        check = self.baseline["cases"][0]["checks"][0]
        check.update(status="not-run", reason="Baseline browser execution was not available.")
        self.assertEqual(self.compare()["verdict"], "incomplete")

    def test_pass_records_improvements_without_beauty_score(self):
        self.baseline["cases"][0]["checks"][0]["status"] = "fail"
        verdict = self.compare()
        self.assertEqual(verdict["verdict"], "pass")
        self.assertEqual(verdict["improvements"], ["search-editor/search-matches"])
        self.assertNotIn("score", verdict)

    def test_path_evidence_must_exist_inside_result_directory(self):
        check = self.candidate["cases"][0]["checks"][0]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in ("missing.png", "../outside.png", "/etc/passwd"):
                check["evidence"] = {"path": path}
                errors = comparator.validate(self.candidate, "candidate", root)
                self.assertTrue(errors, path)
            (root / "observed.txt").write_text("Observed title before and after saved draft.")
            check["evidence"] = {"path": "observed.txt"}
            self.assertEqual(comparator.validate(self.candidate, "candidate", root), [])

    def test_cli_rejects_duplicate_json_keys_and_reports_exit_code(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline, candidate = root / "baseline.json", root / "candidate.json"
            baseline.write_text(json.dumps(self.baseline))
            candidate.write_text('{"schema": 1, "schema": 1}')
            run = subprocess.run([sys.executable, str(SCRIPT), str(baseline), str(candidate)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(json.loads(run.stdout)["verdict"], "invalid")


if __name__ == "__main__":
    unittest.main()
