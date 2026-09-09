"""Behavioral checks for frozen, local-only learning evidence decisions."""

import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/ui-craft-bundle/scripts/learning_gate.py"
spec = importlib.util.spec_from_file_location("learning_gate_test_subject", SCRIPT)
gate = importlib.util.module_from_spec(spec)
old_bytecode = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    spec.loader.exec_module(gate)
finally:
    sys.dont_write_bytecode = old_bytecode


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def plan_record():
    plan = {
        "schema": 1,
        "candidate_sha256": digest("keyboard-visible submission rule"),
        "base_sha256": digest("installed common skill snapshot"),
        "parent_release": None,
        "expected_generation": 0,
        "policy_sha256": digest("project scope and propose mode"),
        "profile": "reviewed-local",
        "target_pairs": ["keyboard-short", "keyboard-long"],
        "transfer_pairs": ["copy-only-counterexample"],
        "required_checks": ["keyboard-submit", "scope-preserved", "ordinary-enter"],
        "improvement_checks": ["keyboard-submit"],
        "context": {
            "task_sha256": digest("fixed task collection"),
            "fixture_sha256": digest("fixed fixture collection"),
            "model": "recorded-comparison-model",
            "settings": {"reasoning": "high", "viewport": [390, 844]},
            "tools_sha256": digest("fixed evaluator and tools"),
        },
        "budget": {"max_runs": 6, "max_seconds": 60},
    }
    transfer_context = copy.deepcopy(plan["context"])
    transfer_context["fixture_sha256"] = digest("heldout copy-only fixture with unrelated form")
    transfer_context["task_sha256"] = digest("change only the requested text on heldout fixture")
    plan["transfer_contexts"] = {"copy-only-counterexample": transfer_context}
    return plan


def report_record(plan):
    pairs = []
    for kind, ids in (("target", plan["target_pairs"]), ("transfer", plan["transfer_pairs"])):
        for pair_id in ids:
            context = plan["context"] if kind == "target" else plan["transfer_contexts"][pair_id]
            pair = {"pair_id": pair_id, "kind": kind, "context": copy.deepcopy(context)}
            for variant in ("baseline", "candidate"):
                checks = []
                for check_id in plan["required_checks"]:
                    failure = kind == "target" and variant == "baseline" and check_id == "keyboard-submit"
                    checks.append({
                        "id": check_id, "status": "fail" if failure else "pass",
                        "evidence": "observations.txt",
                        "reason": "Observed submit obscured by keyboard." if failure else "Observed required action and preserved state in the recorded run.",
                    })
                pair[variant] = {"run_id": pair_id + "-" + variant, "checks": checks, "duration_seconds": 10}
            pairs.append(pair)
    return {
        "schema": 1, "plan_sha256": gate.canonical_digest(plan),
        "candidate_sha256": plan["candidate_sha256"], "pairs": pairs,
        "review": {"independent": True, "reproduced": True, "evaluator_isolated": False,
                   "holdout_unseen": False, "evidence": "review.txt"},
    }


@unittest.skipUnless(hasattr(os, "O_NOFOLLOW") and os.open in os.supports_dir_fd,
                     "Evidence eligibility requires no-follow descriptor walks")
class LearningGateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.evidence = Path(self.temporary.name).resolve()
        (self.evidence / "observations.txt").write_text(
            "Synthetic unit-test evidence: baseline cannot submit with keyboard visible; "
            "candidate submits, reload preserves the value, and copy-only task changes only text.\n"
        )
        (self.evidence / "review.txt").write_text(
            "Synthetic independent-review record for validator testing, not a real UI evaluation. "
            "Reviewer compared fixed fixture hashes and reproduced both target outcomes.\n"
        )
        self.plan = plan_record()
        self.report = report_record(self.plan)

    def evaluate(self):
        return gate.evaluate(self.plan, self.report, self.evidence)

    def rebind(self):
        self.report["plan_sha256"] = gate.canonical_digest(self.plan)

    def check(self, pair=0, variant="candidate", index=0):
        return self.report["pairs"][pair][variant]["checks"][index]

    def assert_verdict(self, verdict):
        result = self.evaluate()
        self.assertEqual(result["verdict"], verdict, result)
        self.assertEqual(result["evidence_level"], "declared-records")
        self.assertIn("do not authenticate", result["limitation"])
        for field in ("improvements", "regressions", "missing", "errors", "reason", "eligible_for"):
            self.assertIn(field, result)
        if verdict != "eligible":
            self.assertEqual(result["eligible_for"], [])
        return result

    def test_repeated_improvement_with_counterexample_is_manual_eligible(self):
        result = self.assert_verdict("eligible")
        self.assertEqual(result["eligible_for"], ["manual"])
        self.assertEqual(len(result["improvements"]), 2)
        self.assertEqual(result["evidence_sha256"]["review.txt"], digest((self.evidence / "review.txt").read_text()))

    def test_all_pass_is_no_change(self):
        for pair in self.report["pairs"]:
            for check in pair["baseline"]["checks"]:
                check["status"] = "pass"
        self.assert_verdict("no-change")

    def test_only_one_target_improves_is_no_change(self):
        self.check(pair=1, variant="baseline")["status"] = "pass"
        self.assert_verdict("no-change")

    def test_different_improvements_in_two_targets_do_not_establish_repeatability(self):
        self.plan["improvement_checks"].append("ordinary-enter")
        self.rebind()
        self.check(pair=1, variant="baseline")["status"] = "pass"
        self.check(pair=1, variant="baseline", index=2)["status"] = "fail"
        self.assert_verdict("no-change")

    def test_non_predeclared_improvement_does_not_qualify(self):
        for pair in (0, 1):
            self.check(pair, "baseline")["status"] = "pass"
            self.check(pair, "baseline", 1)["status"] = "fail"
        self.assert_verdict("no-change")

    def test_regression_overrides_improvement_and_missing_report(self):
        self.check(index=2)["status"] = "fail"
        self.report["pairs"].pop()
        del self.report["review"]
        result = self.assert_verdict("rejected")
        self.assertTrue(result["missing"])
        self.assertEqual(result["regressions"][0]["kind"], "regression")

    def test_malformed_candidate_failure_is_not_erased(self):
        self.check()["status"] = "fail"
        del self.check()["evidence"]
        del self.check()["reason"]
        self.report["schema"] = True
        result = self.assert_verdict("rejected")
        self.assertTrue(result["errors"])
        self.assertTrue(result["missing"])

    def test_counterexample_failure_rejects_even_when_targets_improve(self):
        self.check(pair=2, index=1)["status"] = "fail"
        self.assert_verdict("rejected")

    def test_failing_transfer_baseline_does_not_prove_preservation(self):
        self.check(pair=2, variant="baseline", index=1)["status"] = "fail"
        self.assert_verdict("incomplete")

    def test_transfer_requires_a_frozen_different_fixture(self):
        self.assertNotEqual(self.report["pairs"][0]["context"]["fixture_sha256"], self.report["pairs"][2]["context"]["fixture_sha256"])
        self.assert_verdict("eligible")
        self.plan["transfer_contexts"]["copy-only-counterexample"]["fixture_sha256"] = self.plan["context"]["fixture_sha256"]
        self.report = report_record(self.plan)
        self.assert_verdict("incomplete")

    def test_transfer_cannot_change_model_settings_or_tools(self):
        for field, value in (("model", "different-model"), ("settings", {"reasoning": "different"}), ("tools_sha256", digest("different tools"))):
            with self.subTest(field=field):
                self.plan = plan_record()
                self.plan["transfer_contexts"]["copy-only-counterexample"][field] = value
                self.report = report_record(self.plan)
                self.assert_verdict("incomplete")

    def test_report_cannot_swap_in_a_different_transfer_fixture_after_plan(self):
        self.report["pairs"][2]["context"]["fixture_sha256"] = digest("new easier transfer fixture")
        self.assert_verdict("rejected")

    def test_missing_transfer_context_and_extra_mapping_entry_are_incomplete(self):
        del self.plan["transfer_contexts"]
        self.rebind()
        self.assert_verdict("incomplete")
        self.plan = plan_record()
        self.plan["transfer_contexts"]["unplanned"] = copy.deepcopy(self.plan["context"])
        self.rebind()
        self.assert_verdict("incomplete")

    def test_not_run_is_incomplete_and_needs_no_evidence(self):
        self.check()["status"] = "not-run"
        self.check()["reason"] = "Native keyboard unavailable in this environment."
        del self.check()["evidence"]
        self.assert_verdict("incomplete")

    def test_removed_check_from_both_variants_still_incomplete(self):
        for pair in self.report["pairs"]:
            for variant in ("baseline", "candidate"):
                pair[variant]["checks"].pop()
        self.assert_verdict("incomplete")

    def test_missing_or_duplicate_pairs_do_not_pass(self):
        original = copy.deepcopy(self.report)
        self.report["pairs"].pop()
        self.assert_verdict("incomplete")
        self.report = original
        self.report["pairs"][1] = copy.deepcopy(self.report["pairs"][0])
        self.assert_verdict("incomplete")

    def test_reused_run_id_cannot_count_as_independent_comparison(self):
        self.report["pairs"][1]["candidate"]["run_id"] = self.report["pairs"][0]["candidate"]["run_id"]
        self.assert_verdict("incomplete")

    def test_extra_unplanned_pair_cannot_hide_failed_planned_pair(self):
        self.report["pairs"][0]["pair_id"] = "replacement-easier-task"
        self.assert_verdict("rejected")

    def test_added_check_or_changed_pair_kind_breaks_frozen_contract(self):
        self.check()["id"] = "new-easy-check"
        self.assert_verdict("rejected")
        self.report = report_record(self.plan)
        self.report["pairs"][2]["kind"] = "target"
        self.assert_verdict("rejected")

    def test_duplicate_and_case_colliding_checks_cannot_pass(self):
        self.report["pairs"][0]["candidate"]["checks"].append(copy.deepcopy(self.check()))
        self.assert_verdict("incomplete")
        self.report["pairs"][0]["candidate"]["checks"][-1]["id"] = "KEYBOARD-SUBMIT"
        self.assert_verdict("rejected")

    def test_candidate_and_plan_digest_changes_reject(self):
        self.report["candidate_sha256"] = digest("edited after evaluation")
        self.assert_verdict("rejected")
        self.report = report_record(self.plan)
        self.plan["required_checks"].pop()
        self.assert_verdict("rejected")

    def test_context_mismatch_rejects_but_missing_context_is_incomplete(self):
        self.report["pairs"][0]["context"]["fixture_sha256"] = digest("different easier fixture")
        self.assert_verdict("rejected")
        self.report = report_record(self.plan)
        del self.report["pairs"][0]["context"]
        self.assert_verdict("incomplete")

    def test_self_review_and_unreproduced_review_are_incomplete(self):
        for field in ("independent", "reproduced"):
            with self.subTest(field=field):
                self.report = report_record(self.plan)
                self.report["review"][field] = False
                self.assert_verdict("incomplete")

    def test_review_booleans_are_strict(self):
        for value in (1, "true", "false", None):
            with self.subTest(value=value):
                self.report["review"]["independent"] = value
                self.assert_verdict("incomplete")

    def test_enforced_profile_does_not_silently_downgrade(self):
        self.plan["profile"] = "enforced"
        self.rebind()
        self.assert_verdict("incomplete")
        self.report["review"]["evaluator_isolated"] = True
        self.assert_verdict("incomplete")
        self.report["review"]["holdout_unseen"] = True
        self.assertEqual(self.assert_verdict("eligible")["eligible_for"], ["manual", "auto-local"])

    def test_reviewed_local_never_gets_auto_eligibility_from_booleans(self):
        self.report["review"]["evaluator_isolated"] = True
        self.report["review"]["holdout_unseen"] = True
        self.assertEqual(self.assert_verdict("eligible")["eligible_for"], ["manual"])

    def test_exact_budget_is_valid_and_overrun_is_incomplete(self):
        self.assert_verdict("eligible")
        for budget in ({"max_runs": 5, "max_seconds": 60}, {"max_runs": 6, "max_seconds": 59.9}):
            self.plan["budget"] = budget
            self.rebind()
            self.assert_verdict("incomplete")

    def test_decimal_durations_at_exact_budget_remain_eligible(self):
        for duration, budget in ((0.01, 0.06), (1.07, 6.42), (100.01, 600.06)):
            with self.subTest(duration=duration, budget=budget):
                self.plan["budget"]["max_seconds"] = budget
                for pair in self.report["pairs"]:
                    for variant in ("baseline", "candidate"):
                        pair[variant]["duration_seconds"] = duration
                self.rebind()
                self.assert_verdict("eligible")

    def test_decimal_budget_neighbors_preserve_the_exact_boundary(self):
        for pair in self.report["pairs"]:
            for variant in ("baseline", "candidate"):
                pair[variant]["duration_seconds"] = 100.01
        for budget, verdict in ((math.nextafter(600.06, math.inf), "eligible"),
                                (math.nextafter(600.06, -math.inf), "incomplete")):
            with self.subTest(budget=budget):
                self.plan["budget"]["max_seconds"] = budget
                self.rebind()
                result = self.assert_verdict(verdict)
                if verdict == "incomplete":
                    self.assertTrue(any("time budget exceeded" in item for item in result["missing"]))

    def test_small_positive_duration_cannot_disappear_from_budget_total(self):
        self.plan["budget"]["max_seconds"] = 1
        durations = iter((1, 1e-28, 0, 0, 0, 0))
        for pair in self.report["pairs"]:
            for variant in ("baseline", "candidate"):
                pair[variant]["duration_seconds"] = next(durations)
        self.rebind()
        result = self.assert_verdict("incomplete")
        self.assertIn("time budget exceeded: 1.0000000000000000000000000001/1", result["missing"])

    def test_failure_is_preserved_when_budget_exhausted(self):
        self.plan["budget"]["max_runs"] = 2
        self.rebind()
        self.check(index=1)["status"] = "fail"
        self.assert_verdict("rejected")

    def test_invalid_durations_and_budget_types_are_not_accepted(self):
        for value in (True, -1, float("nan"), float("inf"), 10 ** 1000, "10"):
            with self.subTest(type=type(value).__name__):
                self.report = report_record(self.plan)
                self.report["pairs"][0]["candidate"]["duration_seconds"] = value
                self.assert_verdict("incomplete")
        self.report = report_record(self.plan)
        self.plan["budget"]["max_runs"] = True
        self.rebind()
        self.assert_verdict("incomplete")

    def test_schema_unknown_fields_and_invalid_identifier_sets_are_incomplete(self):
        for mutate in (
            lambda p: p.update(schema=True),
            lambda p: p.update(expected_generation=True),
            lambda p: p.update(candidate_sha256="a" * 64),
            lambda p: p.update(unknown="silently weaken gate"),
            lambda p: p.update(target_pairs=["only-one"]),
            lambda p: p.update(transfer_pairs=[]),
            lambda p: p.update(improvement_checks=[]),
        ):
            self.plan = plan_record()
            mutate(self.plan)
            self.report = report_record(self.plan)
            # New candidate digest remains a malformed record, not a binding mismatch.
            with self.subTest(plan=self.plan):
                self.assert_verdict("incomplete")

    def test_missing_and_placeholder_evidence_cannot_pass(self):
        self.check()["evidence"] = "missing.txt"
        self.assert_verdict("incomplete")
        self.check()["evidence"] = "observations.txt"
        for text in ("", "pass", "TODO: collect screenshot", "looks good"):
            (self.evidence / "observations.txt").write_text(text)
            self.assert_verdict("incomplete")

    def test_placeholder_reason_cannot_pass_even_with_real_evidence(self):
        self.check()["reason"] = "pass"
        self.assert_verdict("incomplete")

    def test_unsafe_paths_are_rejected_without_external_reads(self):
        outside = self.evidence.parent / (self.evidence.name + "-outside.txt")
        outside.write_text("Must remain outside the evidence boundary.")
        self.addCleanup(lambda: outside.unlink(missing_ok=True))
        for path in ("../" + outside.name, str(outside), "./observations.txt", "sub//file", "sub\\file", "C:/secret", "observations.txt ", "line\nfile"):
            with self.subTest(path=path):
                self.check()["evidence"] = path
                self.assert_verdict("rejected")

    def test_symlink_file_directory_and_root_are_rejected(self):
        (self.evidence / "linked.txt").symlink_to(self.evidence / "observations.txt")
        (self.evidence / "linked-dir").symlink_to(self.evidence, target_is_directory=True)
        for path in ("linked.txt", "linked-dir/observations.txt"):
            self.check()["evidence"] = path
            self.assert_verdict("rejected")
        self.check()["evidence"] = "observations.txt"
        linked_root = self.evidence / "linked-dir"
        self.assertEqual(gate.evaluate(self.plan, self.report, linked_root)["verdict"], "rejected")

    def test_directory_and_fifo_are_not_evidence_and_do_not_block(self):
        (self.evidence / "directory").mkdir()
        os.mkfifo(self.evidence / "pipe")
        for path in ("directory", "pipe"):
            self.check()["evidence"] = path
            self.assert_verdict("rejected")

    def test_case_colliding_path_components_are_rejected(self):
        (self.evidence / "logs").mkdir()
        (self.evidence / "logs" / "one.txt").write_text("Recorded first keyboard result.")
        (self.evidence / "logs" / "two.txt").write_text("Recorded second keyboard result.")
        self.check()["evidence"] = "logs/one.txt"
        self.check(pair=1)["evidence"] = "LOGS/two.txt"
        self.assert_verdict("rejected")

    def test_evaluate_does_not_mutate_records_or_write_files(self):
        before_plan, before_report = copy.deepcopy(self.plan), copy.deepcopy(self.report)
        before_files = {p.relative_to(self.evidence): p.read_bytes() for p in self.evidence.rglob("*") if p.is_file()}
        self.assert_verdict("eligible")
        self.assertEqual(self.plan, before_plan)
        self.assertEqual(self.report, before_report)
        self.assertEqual(before_files, {p.relative_to(self.evidence): p.read_bytes() for p in self.evidence.rglob("*") if p.is_file()})

    def test_canonical_digest_is_order_stable_and_rejects_nan(self):
        self.assertEqual(gate.canonical_digest({"a": 1, "b": "한글"}), gate.canonical_digest({"b": "한글", "a": 1}))
        with self.assertRaises(ValueError):
            gate.canonical_digest({"duration": math.nan})

    def test_installed_copy_runs_without_checkout_or_dependencies(self):
        installed = self.evidence / "installed"
        installed.mkdir()
        shutil.copyfile(SCRIPT, installed / "learning_gate.py")
        (installed / "plan.json").write_text(json.dumps(self.plan))
        (installed / "report.json").write_text(json.dumps(self.report))
        code = "import json; from pathlib import Path; from learning_gate import evaluate; print(evaluate(json.loads(Path('plan.json').read_text()), json.loads(Path('report.json').read_text()), Path('..').resolve())['verdict'])"
        run = subprocess.run([sys.executable, "-B", "-c", code], cwd=installed, text=True, capture_output=True, timeout=10)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), "eligible")
        self.assertFalse((installed / "__pycache__").exists())

    def test_oversized_pair_list_is_rejected_with_bounded_processing(self):
        self.report["pairs"] = [{}] * 5000
        original = gate._Audit.fields
        labels = []
        def count_fields(audit, value, expected, label, optional=()):
            labels.append(label)
            return original(audit, value, expected, label, optional)
        with mock.patch.object(gate._Audit, "fields", count_fields):
            result = self.assert_verdict("rejected")
        self.assertIn("report.pairs exceeds supported bound", result["errors"])
        pair_labels = [label for label in labels if label.startswith("report.pairs[") and label.endswith("]")]
        self.assertEqual(len(pair_labels), gate.MAX_PAIRS)

    def test_oversized_checks_are_rejected_and_capped_even_with_failure_in_tail(self):
        self.report["pairs"][0]["candidate"]["checks"] = [{}] * 5000 + [
            {"id": "ordinary-enter", "status": "fail", "reason": "Observed missing submission."}]
        original = gate._Audit.fields
        labels = []
        def count_fields(audit, value, expected, label, optional=()):
            labels.append(label)
            return original(audit, value, expected, label, optional)
        with mock.patch.object(gate._Audit, "fields", count_fields):
            self.assert_verdict("rejected")
        checked = [label for label in labels if label.startswith("report.pairs[0].candidate.checks[")]
        self.assertEqual(len(checked), gate.MAX_CHECKS)


class LearningGateUnsupportedPlatformTests(unittest.TestCase):
    def test_missing_descriptor_support_never_grants_eligibility(self):
        plan = plan_record()
        report = report_record(plan)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "observations.txt").write_text("Observed synthetic keyboard behavior.", encoding="utf-8")
            (root / "review.txt").write_text("Independent synthetic reproduction record.", encoding="utf-8")
            with mock.patch.object(gate.os, "supports_dir_fd", set()):
                decision = gate.evaluate(plan, report, root)
        self.assertEqual(decision["verdict"], "incomplete", decision)
        self.assertEqual(decision["eligible_for"], [])
        self.assertIn("platform lacks no-follow evidence path support", decision["missing"])


if __name__ == "__main__":
    unittest.main()
