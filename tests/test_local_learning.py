"""Exercise project-local learning through its shipped CLI in disposable projects."""

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/ui-craft-bundle/scripts/local_learning.py"


class LocalLearningLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.base = self.root / "skills"
        self.base_skill = self.base / "ui-craft-bundle" / "SKILL.md"
        self.base_skill.parent.mkdir(parents=True)
        self.base_skill.write_text(
            "---\nname: ui-craft-bundle\ndescription: Test skill.\n---\n"
            "Preserve the user's task and verify observable behavior.\n",
            encoding="utf-8",
        )
        self.inputs = self.root / "inputs"
        self.inputs.mkdir()
        self.rules = self.inputs / "rules.md"
        self.rules.write_text(
            "Keep the user's draft available when a form submission fails.\n"
            "Apply to web forms in this project after reviewing the current task.\n",
            encoding="utf-8",
        )
        self.spec = {
            "scope": {
                "skill_ids": ["ui-craft-bundle"],
                "platforms": ["web"],
                "task_kinds": ["form"],
            },
            "profile": "reviewed-local",
            "target_pairs": ["t1", "t2"],
            "transfer_pairs": ["x1"],
            "required_checks": ["outcome", "scope"],
            "improvement_checks": ["outcome"],
            "context": {
                "task_sha256": hashlib.sha256(b"synthetic form task").hexdigest(),
                "fixture_sha256": hashlib.sha256(b"synthetic form fixture").hexdigest(),
                "model": "test-runtime",
                "settings": {"reasoning": "test"},
                "tools_sha256": hashlib.sha256(b"synthetic test tool contract").hexdigest(),
            },
        }
        self.spec["transfer_contexts"] = {"x1": dict(
            self.spec["context"],
            fixture_sha256=hashlib.sha256(b"distinct synthetic transfer fixture").hexdigest(),
        )}
        self.spec_path = self.inputs / "spec.json"
        self.write_json(self.spec_path, self.spec)
        self.local = self.project / ".lutriva" / "local"
        self.report_count = 0

    @staticmethod
    def write_json(path, value):
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def cli(self, *args, code=0):
        completed = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), *map(str, args)],
            cwd=self.root,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(
            completed.returncode, code,
            f"command: {args}\nstdout: {completed.stdout}\nstderr: {completed.stderr}",
        )
        output = completed.stderr if code == 2 else completed.stdout
        try:
            result = json.loads(output)
        except json.JSONDecodeError as error:
            self.fail(f"CLI did not emit one JSON document: {error}\n{output}")
        self.assertIsInstance(result, dict)
        if code == 2:
            self.assertEqual(completed.stdout, "")
        else:
            self.assertEqual(completed.stderr, "")
        return result

    def initialize(self):
        return self.cli("init", "--project", self.project, "--base", self.base)

    def propose(self, *, code=0):
        return self.cli(
            "propose", "--project", self.project,
            "--rules", self.rules, "--spec", self.spec_path, code=code,
        )

    def active(self):
        return json.loads((self.local / "active.json").read_text(encoding="utf-8"))

    def context(self, *, skill="ui-craft-bundle", platform="web", task_kind="form"):
        return self.cli(
            "context", "--project", self.project,
            "--skill", skill, "--platform", platform,
            "--task-kind", task_kind,
        )

    @staticmethod
    def canonical_digest(value):
        return hashlib.sha256(json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")).hexdigest()

    def report(self, proposal, *, improved=True):
        """Synthetic gate records test contract handling, never real UI quality."""
        self.report_count += 1
        folder = self.inputs / ("report-" + str(self.report_count))
        folder.mkdir()
        evidence = folder / "evidence"
        evidence.mkdir()
        (evidence / "observations.txt").write_text(
            "Synthetic fixture: the candidate kept the submitted draft after failure, "
            "and the untouched action remained keyboard reachable.\n",
            encoding="utf-8",
        )
        (evidence / "review.txt").write_text(
            "Synthetic independent reviewer record: the frozen comparisons and "
            "raw observations were inspected and the target outcome reproduced.\n",
            encoding="utf-8",
        )
        plan = proposal["plan"]
        pairs = []
        for kind, pair_ids in (("target", plan["target_pairs"]),
                               ("transfer", plan["transfer_pairs"])):
            for pair_id in pair_ids:
                context = plan["context"] if kind == "target" else plan["transfer_contexts"][pair_id]
                pair = {"pair_id": pair_id, "kind": kind, "context": copy.deepcopy(context)}
                for variant in ("baseline", "candidate"):
                    pair[variant] = {
                        "run_id": pair_id + "-" + variant,
                        "duration_seconds": 1,
                        "checks": [{
                            "id": check_id,
                            "status": "fail" if (
                                improved and kind == "target" and variant == "baseline"
                                and check_id == plan["improvement_checks"][0]
                            ) else "pass",
                            "evidence": "observations.txt",
                            "reason": "Observed the declared draft preservation and keyboard reachability outcome.",
                        } for check_id in plan["required_checks"]],
                    }
                pairs.append(pair)
        report = {
            "schema": 1,
            "plan_sha256": self.canonical_digest(plan),
            "candidate_sha256": plan["candidate_sha256"],
            "pairs": pairs,
            "review": {
                "independent": True,
                "reproduced": True,
                "evaluator_isolated": False,
                "holdout_unseen": False,
                "evidence": "review.txt",
            },
        }
        path = folder / "report.json"
        self.write_json(path, report)
        return report, path, evidence

    def evaluate(self, proposal, *, improved=True, mutate=None, code=0):
        if not hasattr(os, "O_NOFOLLOW") or os.open not in os.supports_dir_fd:
            self.skipTest("Eligible evidence validation requires no-follow directory-descriptor support")
        report, path, evidence = self.report(proposal, improved=improved)
        if mutate:
            mutate(report)
            self.write_json(path, report)
        result = self.cli(
            "evaluate", "--project", self.project,
            "--candidate", proposal["candidate_id"],
            "--report", path, "--evidence", evidence, code=code,
        )
        return result

    def promote(self, evaluation, *, code=0):
        return self.cli(
            "promote", "--project", self.project,
            "--evaluation", evaluation["evaluation_id"], code=code,
        )

    def test_init_starts_at_generation_zero_without_editing_project_or_base(self):
        product = self.project / "form.html"
        product.write_text("<form><input name='draft'></form>\n", encoding="utf-8")
        product_before = product.read_bytes()
        base_before = self.base_skill.read_bytes()
        self.initialize()
        active = self.active()
        self.assertEqual(active["generation"], 0)
        self.assertEqual(active["state"], "base-only")
        self.assertIsNone(active["release_id"])
        self.assertEqual(product.read_bytes(), product_before)
        self.assertEqual(self.base_skill.read_bytes(), base_before)
        self.assertEqual(self.context()["rules"], [])

    def test_init_does_not_overwrite_existing_learning_store(self):
        self.initialize()
        before = {path.relative_to(self.local): path.read_bytes()
                  for path in self.local.rglob("*") if path.is_file()}
        self.cli("init", "--project", self.project, "--base", self.base, code=2)
        after = {path.relative_to(self.local): path.read_bytes()
                 for path in self.local.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

    def test_proposal_remains_inactive_and_captures_rules(self):
        self.initialize()
        pointer_before = (self.local / "active.json").read_bytes()
        proposal = self.propose()
        candidate = self.local / "candidates" / proposal["candidate_id"]
        snapshot = (candidate / "rules.md").read_bytes()
        self.assertIn(self.rules.read_bytes().decode("utf-8").strip(), snapshot.decode("utf-8"))
        self.assertEqual(hashlib.sha256(snapshot).hexdigest(), proposal["plan"]["candidate_sha256"])
        self.assertIsInstance(proposal["plan"], dict)
        self.assertEqual((self.local / "active.json").read_bytes(), pointer_before)
        self.assertEqual(self.context()["rules"], [])

    def test_duplicate_spec_keys_are_rejected_before_candidate_creation(self):
        self.initialize()
        text = self.spec_path.read_text(encoding="utf-8")
        self.spec_path.write_text(text[:-1] + ', "profile": "reviewed-local"}', encoding="utf-8")
        self.propose(code=2)
        self.assertEqual(list((self.local / "candidates").iterdir()), [])

    def test_candidate_scope_rejects_unknown_skill(self):
        self.initialize()
        self.spec["scope"]["skill_ids"] = ["missing-skill"]
        self.write_json(self.spec_path, self.spec)
        self.propose(code=2)
        self.assertEqual(self.active()["generation"], 0)

    def test_existing_writer_lock_blocks_mutation_without_removing_the_lock(self):
        self.initialize()
        lock = self.local / ".lock"
        lock.write_text("another writer owns this lock\n", encoding="utf-8")
        self.propose(code=2)
        self.assertEqual(lock.read_text(encoding="utf-8"), "another writer owns this lock\n")
        self.assertEqual(self.active()["generation"], 0)
        self.assertEqual(list((self.local / "candidates").iterdir()), [])

    def test_symlinked_learning_root_is_not_initialized(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.project / ".lutriva").symlink_to(outside, target_is_directory=True)
        self.cli("init", "--project", self.project, "--base", self.base, code=2)
        self.assertEqual(list(outside.iterdir()), [])

    def test_learning_stores_are_isolated_between_projects(self):
        self.initialize()
        first_id = self.active()["project_id"]
        self.propose()
        other = self.root / "other-project"
        other.mkdir()
        self.cli("init", "--project", other, "--base", self.base)
        other_local = other / ".lutriva" / "local"
        other_active = json.loads((other_local / "active.json").read_text(encoding="utf-8"))
        self.assertNotEqual(first_id, other_active["project_id"])
        self.assertEqual(other_active["generation"], 0)
        self.assertEqual(list((other_local / "candidates").iterdir()), [])

    def test_missing_pointer_cannot_be_reset_as_a_fresh_store(self):
        self.initialize()
        self.propose()
        (self.local / "active.json").unlink()
        self.cli("init", "--project", self.project, "--base", self.base, code=2)
        self.assertFalse((self.local / "active.json").exists())
        self.assertEqual(len(list((self.local / "candidates").iterdir())), 1)

    def test_eligible_manual_promotion_supplies_context_and_rollback_advances_generation(self):
        self.initialize()
        proposal = self.propose()
        evaluation = self.evaluate(proposal)
        self.assertEqual(evaluation["decision"]["verdict"], "eligible")
        self.assertEqual(evaluation["decision"]["eligible_for"], ["manual"])
        self.assertEqual(self.active()["generation"], 0)
        self.promote(evaluation)
        promoted = self.active()
        self.assertEqual(promoted["generation"], 1)
        self.assertEqual(promoted["state"], "active")
        context = self.context()
        self.assertEqual(len(context["rules"]), 1)
        self.assertEqual(context["rules"][0]["text"], self.rules.read_bytes().decode("utf-8").strip())
        self.assertEqual(context["generation"], 1)
        self.cli("rollback", "--project", self.project)
        restored = self.active()
        self.assertEqual(restored["generation"], 2)
        self.assertEqual(restored["state"], "base-only")
        self.assertIsNone(restored["release_id"])
        self.assertEqual(self.context()["rules"], [])

    def test_equal_passing_results_cannot_be_promoted(self):
        self.initialize()
        evaluation = self.evaluate(self.propose(), improved=False)
        self.assertEqual(evaluation["decision"]["verdict"], "no-change")
        self.assertEqual(evaluation["decision"]["eligible_for"], [])
        self.promote(evaluation, code=2)
        self.assertEqual(self.active()["generation"], 0)
        self.assertEqual(self.context()["rules"], [])

    def test_decimal_exact_budget_can_be_evaluated_and_promoted(self):
        self.cli("init", "--project", self.project, "--base", self.base,
                 "--max-seconds", "600.06")
        proposal = self.propose()

        def record_durations(report):
            for pair in report["pairs"]:
                for variant in ("baseline", "candidate"):
                    pair[variant]["duration_seconds"] = 100.01

        evaluation = self.evaluate(proposal, mutate=record_durations)
        self.assertEqual(evaluation["decision"]["verdict"], "eligible")
        self.promote(evaluation)
        self.assertEqual(self.active()["generation"], 1)
        self.assertEqual(len(self.context()["rules"]), 1)

    def test_candidate_failure_rejects_and_cannot_be_promoted(self):
        self.initialize()
        evaluation = self.evaluate(
            self.propose(),
            mutate=lambda report: report["pairs"][2]["candidate"]["checks"][1].update(status="fail"),
            code=1,
        )
        self.assertEqual(evaluation["decision"]["verdict"], "rejected")
        self.promote(evaluation, code=2)
        self.assertEqual(self.active()["generation"], 0)

    def test_missing_independent_reproduction_remains_incomplete(self):
        self.initialize()
        evaluation = self.evaluate(
            self.propose(),
            mutate=lambda report: report["review"].update(reproduced=False),
            code=3,
        )
        self.assertEqual(evaluation["decision"]["verdict"], "incomplete")
        self.promote(evaluation, code=2)
        self.assertEqual(self.active()["generation"], 0)

    def test_rules_tampering_after_evaluation_cannot_be_promoted(self):
        self.initialize()
        proposal = self.propose()
        evaluation = self.evaluate(proposal)
        candidate_rules = self.local / "candidates" / proposal["candidate_id"] / "rules.md"
        candidate_rules.write_text("Changed after the successful evaluation.\n", encoding="utf-8")
        self.promote(evaluation, code=2)
        self.assertEqual(self.active()["generation"], 0)
        self.assertEqual(self.context()["rules"], [])

    def test_scope_mismatch_excludes_an_active_rule(self):
        self.initialize()
        self.promote(self.evaluate(self.propose()))
        self.assertEqual(self.context(skill="ux-writing")["rules"], [])
        self.assertEqual(self.context(platform="ios")["rules"], [])
        self.assertEqual(self.context(task_kind="navigation")["rules"], [])
        self.assertEqual(len(self.context()["rules"]), 1)

    def test_base_drift_excludes_previously_active_rules(self):
        self.initialize()
        self.promote(self.evaluate(self.propose()))
        self.base_skill.write_text(self.base_skill.read_text(encoding="utf-8")
                                   + "Updated shared behavior contract.\n", encoding="utf-8")
        context = self.context()
        self.assertEqual(context["rules"], [])
        self.assertEqual(context["state"], "suspended")

    def test_two_candidates_for_the_same_generation_cannot_both_be_promoted(self):
        self.initialize()
        first, second = self.propose(), self.propose()
        first_evaluation, second_evaluation = self.evaluate(first), self.evaluate(second)
        self.promote(first_evaluation)
        pointer_before = (self.local / "active.json").read_bytes()
        self.promote(second_evaluation, code=2)
        self.assertEqual((self.local / "active.json").read_bytes(), pointer_before)

    def test_stored_evidence_tampering_prevents_promotion(self):
        self.initialize()
        evaluation = self.evaluate(self.propose())
        evidence = self.local / "evaluations" / evaluation["evaluation_id"] / "evidence" / "observations.txt"
        evidence.write_text("Different evidence after eligibility was recorded.\n", encoding="utf-8")
        self.promote(evaluation, code=2)
        self.assertEqual(self.active()["generation"], 0)

    def test_decision_tampering_cannot_turn_no_change_into_eligible(self):
        self.initialize()
        evaluation = self.evaluate(self.propose(), improved=False)
        decision_path = self.local / "evaluations" / evaluation["evaluation_id"] / "decision.json"
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
        decision.update(verdict="eligible", eligible_for=["manual"])
        self.write_json(decision_path, decision)
        self.promote(evaluation, code=2)
        self.assertEqual(self.active()["generation"], 0)

    def test_evidence_symlink_is_rejected_without_creating_an_evaluation(self):
        self.initialize()
        proposal = self.propose()
        _, report_path, evidence = self.report(proposal)
        observed = evidence / "observations.txt"
        external = self.inputs / "external-observation.txt"
        external.write_bytes(observed.read_bytes())
        observed.unlink()
        observed.symlink_to(external)
        self.cli(
            "evaluate", "--project", self.project,
            "--candidate", proposal["candidate_id"],
            "--report", report_path, "--evidence", evidence, code=2,
        )
        self.assertEqual(list((self.local / "evaluations").iterdir()), [])
        self.assertEqual(self.active()["generation"], 0)

    def test_evidence_directory_symlink_is_rejected(self):
        self.initialize()
        proposal = self.propose()
        _, report_path, evidence = self.report(proposal)
        alias = self.inputs / "evidence-alias"
        alias.symlink_to(evidence, target_is_directory=True)
        self.cli(
            "evaluate", "--project", self.project,
            "--candidate", proposal["candidate_id"],
            "--report", report_path, "--evidence", alias, code=2,
        )
        self.assertEqual(list((self.local / "evaluations").iterdir()), [])

    def test_rollback_to_the_same_parent_does_not_revive_a_stale_evaluation(self):
        self.initialize()
        first, stale = self.propose(), self.propose()
        first_evaluation, stale_evaluation = self.evaluate(first), self.evaluate(stale)
        self.promote(first_evaluation)
        self.cli("rollback", "--project", self.project)
        self.assertIsNone(self.active()["release_id"])
        self.assertEqual(self.active()["generation"], 2)
        self.promote(stale_evaluation, code=2)
        self.assertEqual(self.active()["generation"], 2)

    def test_explicit_rollback_restores_a_previous_rule_set_and_preserves_history(self):
        self.initialize()
        self.promote(self.evaluate(self.propose()))
        first_release = self.active()["release_id"]
        self.rules.write_text("Explain the exact next action after a form succeeds.\n", encoding="utf-8")
        self.promote(self.evaluate(self.propose()))
        second_release = self.active()["release_id"]
        self.assertNotEqual(first_release, second_release)
        self.assertEqual(len(self.context()["rules"]), 2)
        self.cli("rollback", "--project", self.project, "--release", first_release)
        self.assertEqual(self.active()["generation"], 3)
        self.assertEqual(self.active()["release_id"], first_release)
        self.assertEqual(len(self.context()["rules"]), 1)
        self.assertTrue((self.local / "releases" / second_release / "manifest.json").is_file())

    def test_candidate_context_is_explicit_and_does_not_activate_the_candidate(self):
        self.initialize()
        proposal = self.propose()
        result = self.cli(
            "context", "--project", self.project,
            "--skill", "ui-craft-bundle", "--platform", "web", "--task-kind", "form",
            "--candidate", proposal["candidate_id"],
        )
        self.assertEqual(result["candidate_id"], proposal["candidate_id"])
        self.assertEqual(len(result["rules"]), 1)
        self.assertEqual(result["rules"][0]["sha256"], hashlib.sha256(
            self.rules.read_bytes().decode("utf-8").strip().encode("utf-8")).hexdigest())
        self.assertEqual(self.active()["generation"], 0)
        self.assertEqual(self.context()["rules"], [])

    def test_policy_drift_after_evaluation_prevents_promotion(self):
        self.initialize()
        evaluation = self.evaluate(self.propose())
        policy_path = self.local / "policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["max_seconds"] += 1
        self.write_json(policy_path, policy)
        self.promote(evaluation, code=2)
        self.assertEqual(self.active()["generation"], 0)

    def test_base_drift_after_evaluation_prevents_promotion(self):
        self.initialize()
        evaluation = self.evaluate(self.propose())
        self.base_skill.write_text(self.base_skill.read_text(encoding="utf-8")
                                   + "Shared skill changed after evaluation.\n", encoding="utf-8")
        self.promote(evaluation, code=2)
        self.assertEqual(self.active()["generation"], 0)

    def test_status_is_explicit_about_unsupported_automatic_execution(self):
        self.initialize()
        status = self.cli("status", "--project", self.project)
        self.assertEqual(status["mode"], "propose")
        self.assertIs(status["automatic_execution"], False)

    def test_argument_errors_are_machine_readable_json(self):
        result = self.cli("context", code=2)
        self.assertIn("error", result)

    def test_restored_old_pointer_cannot_reset_generation_or_revive_old_eligibility(self):
        self.initialize()
        initial = (self.local / "active.json").read_bytes()
        first, stale = self.propose(), self.propose()
        first_evaluation, stale_evaluation = self.evaluate(first), self.evaluate(stale)
        self.promote(first_evaluation)
        self.cli("rollback", "--project", self.project)
        self.assertEqual(self.active()["generation"], 2)
        (self.local / "active.json").write_bytes(initial)
        result = self.promote(stale_evaluation, code=2)
        self.assertIn("newest committed journal", result["error"])
        self.assertEqual((self.local / "active.json").read_bytes(), initial)
        self.cli("status", "--project", self.project, code=2)

    def test_corrupt_current_release_can_roll_back_to_base(self):
        self.initialize()
        self.promote(self.evaluate(self.propose()))
        release = self.active()["release_id"]
        (self.local / "releases" / release / "rules.md").write_text("Corrupted current rules.")
        self.cli("status", "--project", self.project, code=2)
        result = self.cli("rollback", "--project", self.project)
        self.assertEqual(result["generation"], 2)
        self.assertEqual(result["state"], "base-only")
        self.assertEqual(self.context()["rules"], [])

    def test_corrupt_current_release_can_roll_back_to_explicit_good_release(self):
        self.initialize()
        self.promote(self.evaluate(self.propose()))
        good = self.active()["release_id"]
        self.promote(self.evaluate(self.propose()))
        broken = self.active()["release_id"]
        (self.local / "releases" / broken / "rules.md").write_text("Corrupted current rules.")
        result = self.cli("rollback", "--project", self.project, "--release", good)
        self.assertEqual(result["generation"], 3)
        self.assertEqual(result["release_id"], good)
        self.assertEqual(len(self.context()["rules"]), 1)

    def test_corrupt_previous_release_defaults_to_base_without_loading_it(self):
        self.initialize()
        self.promote(self.evaluate(self.propose()))
        previous = self.active()["release_id"]
        self.promote(self.evaluate(self.propose()))
        (self.local / "releases" / previous / "rules.md").write_text("Corrupted previous rules.")
        result = self.cli("rollback", "--project", self.project)
        self.assertEqual(result["generation"], 3)
        self.assertEqual(result["state"], "base-only")
        self.assertEqual(self.context()["rules"], [])

    def test_stale_candidate_context_cannot_claim_current_generation(self):
        self.initialize()
        first, stale = self.propose(), self.propose()
        self.promote(self.evaluate(first))
        result = self.cli("context", "--project", self.project,
                          "--skill", "ui-craft-bundle", "--platform", "web", "--task-kind", "form",
                          "--candidate", stale["candidate_id"], code=2)
        self.assertIn("Stale candidate", result["error"])
        self.assertEqual(self.active()["generation"], 1)

    def test_missing_or_forked_history_does_not_supply_context(self):
        self.initialize()
        self.promote(self.evaluate(self.propose()))
        journal_path = next((self.local / "journal").glob("*.json"))
        original = journal_path.read_bytes()
        journal_path.unlink()
        self.cli("status", "--project", self.project, code=2)
        journal_path.write_bytes(original)
        journal = json.loads(original)
        journal["old"]["base_sha256"] = "f" * 64
        self.write_json(journal_path, journal)
        # A first old snapshot cannot be authenticated outside local history;
        # a later discontinuity must still be rejected.
        self.cli("rollback", "--project", self.project)
        second_path = [p for p in (self.local / "journal").glob("*.json") if p != journal_path][0]
        second = json.loads(second_path.read_text())
        second["old"]["base_sha256"] = "e" * 64
        self.write_json(second_path, second)
        self.cli("status", "--project", self.project, code=2)

    def test_prepared_transition_old_and_new_pointers_are_explicitly_withheld(self):
        self.initialize()
        self.promote(self.evaluate(self.propose()))
        journal_path = next((self.local / "journal").glob("*.json"))
        journal = json.loads(journal_path.read_text())
        journal["phase"] = "prepared"
        self.write_json(journal_path, journal)
        for side in ("old", "new"):
            self.write_json(self.local / "active.json", journal[side])
            error = self.cli("status", "--project", self.project, code=2)
            self.assertIn("matches the " + side + " snapshot", error["error"])
            self.cli("rollback", "--project", self.project, code=2)

    def test_wrong_record_shapes_return_one_json_error_without_traceback(self):
        self.initialize()
        proposal = self.propose()
        candidate_path = self.local / "candidates" / proposal["candidate_id"] / "candidate.json"
        self.write_json(candidate_path, [])
        result = self.cli("context", "--project", self.project,
                          "--skill", "ui-craft-bundle", "--platform", "web", "--task-kind", "form",
                          "--candidate", proposal["candidate_id"], code=2)
        self.assertIn("JSON object", result["error"])
        self.write_json(self.local / "policy.json", [])
        self.cli("status", "--project", self.project, code=2)

    def test_init_rejects_project_inside_installed_base_without_creating_store(self):
        for project in (self.base, self.base_skill.parent):
            self.cli("init", "--project", project, "--base", self.base, code=2)
            self.assertFalse((project / ".lutriva").exists())

    def test_project_can_contain_its_normal_installed_skill_directory(self):
        import shutil
        installed = self.project / ".agents" / "skills"
        installed.parent.mkdir()
        shutil.copytree(self.base, installed)
        self.cli("init", "--project", self.project, "--base", installed)
        self.assertEqual(self.active()["generation"], 0)
        self.assertEqual(self.context()["rules"], [])

    def test_policy_cannot_retarget_base_to_contain_local_store(self):
        self.initialize()
        policy_path = self.local / "policy.json"
        policy = json.loads(policy_path.read_text())
        policy["base"] = str(self.project)
        self.write_json(policy_path, policy)
        result = self.cli("status", "--project", self.project, code=2)
        self.assertIn("inside the installed skill base", result["error"])

    def test_propose_rejects_overlapping_target_and_transfer_ids_before_writing(self):
        self.initialize()
        self.spec["transfer_pairs"] = ["t1"]
        self.spec["transfer_contexts"] = {"t1": self.spec["transfer_contexts"]["x1"]}
        self.write_json(self.spec_path, self.spec)
        result = self.propose(code=2)
        self.assertIn("distinct", result["error"])
        self.assertEqual(list((self.local / "candidates").iterdir()), [])

    def test_propose_rejects_improvement_outside_required_checks_before_writing(self):
        self.initialize()
        self.spec["improvement_checks"] = ["unplanned-check"]
        self.write_json(self.spec_path, self.spec)
        result = self.propose(code=2)
        self.assertIn("subset", result["error"])
        self.assertEqual(list((self.local / "candidates").iterdir()), [])

    def test_git_timeout_is_one_json_error_without_partial_initialization(self):
        code = (
            "import sys, subprocess; from unittest.mock import patch; "
            "sys.path.insert(0, sys.argv[1]); import local_learning; "
            "failure = subprocess.TimeoutExpired('git', 10); "
            "patcher = patch.object(local_learning.subprocess, 'run', side_effect=failure); "
            "patcher.start(); raise SystemExit(local_learning.main("
            "['init', '--project', sys.argv[2], '--base', sys.argv[3]]))"
        )
        completed = subprocess.run([sys.executable, "-B", "-c", code, str(SCRIPT.parent),
                                    str(self.project), str(self.base)], text=True, capture_output=True, timeout=10)
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertEqual(completed.stdout, "")
        self.assertIn("timed out", json.loads(completed.stderr)["error"])
        self.assertFalse(self.local.exists())

    def test_previous_release_cannot_be_rewritten_with_self_consistent_new_hashes(self):
        self.initialize()
        self.promote(self.evaluate(self.propose()))
        previous = self.active()["release_id"]
        self.promote(self.evaluate(self.propose()))
        manifest = self.local / "releases" / previous / "manifest.json"
        record = json.loads(manifest.read_text())
        record["evaluation_id"] = "e-forged"
        self.write_json(manifest, record)
        result = self.cli("rollback", "--project", self.project, "--release", previous, code=2)
        self.assertIn("changed since activation", result["error"])
        result = self.cli("rollback", "--project", self.project)
        self.assertEqual(result["state"], "base-only")

    def tracked_deleted_local_path(self):
        if shutil.which("git") is None:
            self.skipTest("Git integration requires a Git executable")
        subprocess.run(["git", "init", "-q", str(self.project)], check=True, capture_output=True)
        tracked = self.local / "retained.json"
        tracked.parent.mkdir(parents=True)
        tracked.write_text('{"tracked":true}', encoding="utf-8")
        subprocess.run(["git", "-C", str(self.project), "add", "-f", ".lutriva/local/retained.json"],
                       check=True, capture_output=True)
        tracked.unlink()
        tracked.parent.rmdir()

    def test_corrupt_git_index_prevents_initialization_before_any_local_recording(self):
        self.tracked_deleted_local_path()
        (self.project / ".git" / "index").write_bytes(b"corrupt index")
        error = self.cli("init", "--project", self.project, "--base", self.base, code=2)
        self.assertIn("Git index check failed", error["error"])
        self.assertFalse(self.local.exists())
        self.assertEqual(list((self.project / ".lutriva").iterdir()), [])

    def test_tracked_but_deleted_local_path_prevents_reinitialization(self):
        self.tracked_deleted_local_path()
        error = self.cli("init", "--project", self.project, "--base", self.base, code=2)
        self.assertIn("already tracked", error["error"])
        self.assertFalse(self.local.exists())

    def test_normal_nongit_project_can_initialize(self):
        self.assertFalse((self.project / ".git").exists())
        self.initialize()
        self.assertEqual(self.active()["generation"], 0)

    def test_missing_git_executable_is_optional(self):
        code = (
            "import sys; from unittest.mock import patch; "
            "sys.path.insert(0, sys.argv[1]); import local_learning; "
            "patcher = patch.object(local_learning.subprocess, 'run', side_effect=FileNotFoundError('git')); "
            "patcher.start(); raise SystemExit(local_learning.main("
            "['init', '--project', sys.argv[2], '--base', sys.argv[3]]))"
        )
        completed = subprocess.run([sys.executable, "-B", "-c", code, str(SCRIPT.parent),
                                    str(self.project), str(self.base)], text=True, capture_output=True, timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stderr, "")
        self.assertEqual(json.loads(completed.stdout)["state"], "base-only")

    def test_evaluation_record_schema_id_and_unknown_fields_are_rejected_before_promotion(self):
        self.initialize()
        evaluation = self.evaluate(self.propose())
        path = self.local / "evaluations" / evaluation["evaluation_id"] / "record.json"
        original = json.loads(path.read_text(encoding="utf-8"))
        for changes in ({"schema": 99}, {"schema": True}, {"evaluation_id": "e-unrelated"},
                        {"unexpected": "unrecognized metadata"}):
            with self.subTest(changes=changes):
                self.write_json(path, dict(original, **changes))
                self.promote(evaluation, code=2)
                self.assertEqual(self.active()["generation"], 0)
                self.assertEqual(list((self.local / "releases").iterdir()), [])
        self.write_json(path, original)
        self.promote(evaluation)
        self.assertEqual(self.active()["generation"], 1)

    def test_evaluation_record_hash_id_and_file_map_types_are_validated(self):
        self.initialize()
        evaluation = self.evaluate(self.propose())
        path = self.local / "evaluations" / evaluation["evaluation_id"] / "record.json"
        original = json.loads(path.read_text(encoding="utf-8"))
        for changes, message in (
            ({"candidate_id": []}, "candidate ID"),
            ({"candidate_record_sha256": True}, "record digest"),
            ({"plan_sha256": "not-a-digest"}, "record digest"),
            ({"files": []}, "file digest map"),
            ({"files": {"report.json": 123}}, "file digest map"),
            ({"files": {"report.json": "not-a-digest"}}, "file digest map"),
        ):
            with self.subTest(changes=changes):
                self.write_json(path, dict(original, **changes))
                error = self.promote(evaluation, code=2)
                self.assertIn(message, error["error"])
                self.assertEqual(self.active()["generation"], 0)
                self.assertEqual(list((self.local / "releases").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
