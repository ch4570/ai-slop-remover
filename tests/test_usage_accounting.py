"""Accounting controls use synthetic, hash-bound records, never billing claims."""
import copy
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import usage_accounting as accounting
from compare_evals import SUITE, scope_suites


def usage(input_tokens=100, cached=20, writes=10, output=40, reasoning=15):
    return {"input_tokens": input_tokens, "cached_input_tokens": cached,
            "cache_write_tokens": writes, "output_tokens": output,
            "reasoning_output_tokens": reasoning}


def sample(sample_id, **kwargs):
    return {"sample_id": sample_id, **usage(**kwargs)}


def price(**overrides):
    return {"schema": 1, "provider": "test-provider", "model": "observed-model",
            "currency": "USD", "source": "https://provider.example/pricing",
            "as_of": "2026-09-09", "rates": {"input": "2", "cached_input": "0.5",
            "cache_write": "3", "output": "10"}, **overrides}


class SampleTests(unittest.TestCase):
    def test_delta_sums_unique_events_without_double_counting_reasoning(self):
        first, second = sample("first"), sample("second", input_tokens=200)
        actual = accounting.normalize_samples([first, copy.deepcopy(first), second], "delta")
        self.assertEqual(actual, usage(input_tokens=300, cached=40, writes=20,
                                       output=80, reasoning=30))

    def test_cumulative_uses_last_snapshot_not_sum(self):
        first, final = sample("first"), sample("final", input_tokens=200, output=80)
        self.assertEqual(accounting.normalize_samples([first, final, final], "cumulative"),
                         usage(input_tokens=200, output=80))

    def test_conflicting_duplicate_identity_is_invalid_in_both_modes(self):
        for mode in ("delta", "cumulative"):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                accounting.normalize_samples([sample("event"), sample("event", output=50)], mode)

    def test_decreasing_cumulative_component_is_invalid(self):
        for field in usage():
            first, final = sample("first"), sample("final")
            final[field] -= 1
            with self.subTest(field=field), self.assertRaises(ValueError):
                accounting.normalize_samples([first, final], "cumulative")

    def test_unknown_fields_stay_null(self):
        unknown = sample("unknown", writes=None, reasoning=None)
        for mode in ("delta", "cumulative"):
            with self.subTest(mode=mode):
                actual = accounting.normalize_samples([sample("first"), unknown], mode)
                self.assertIsNone(actual["cache_write_tokens"])
                self.assertIsNone(actual["reasoning_output_tokens"])

    def test_cumulative_later_known_snapshot_recovers_unknown_but_cannot_regress(self):
        samples = [sample("first"), sample("unknown", writes=None), sample("known")]
        self.assertEqual(accounting.normalize_samples(samples, "cumulative"), usage())
        samples[-1]["cache_write_tokens"] = 9
        with self.assertRaises(ValueError):
            accounting.normalize_samples(samples, "cumulative")

    def test_unknown_delta_must_not_be_replaced_by_known_fragment(self):
        unknown = sample("unknown", writes=None)
        actual = accounting.normalize_samples([unknown, sample("known")], "delta")
        self.assertIsNone(actual["cache_write_tokens"])
        self.assertEqual(actual["input_tokens"], 200)

    def test_mode_empty_samples_and_missing_identity_are_invalid(self):
        for samples, mode in (([sample("one")], None), ([sample("one")], "guess"),
                              ([], "delta"), ([usage()], "delta")):
            with self.subTest(samples=samples, mode=mode), self.assertRaises(ValueError):
                accounting.normalize_samples(samples, mode)

    def test_invalid_counts_and_subset_overflow_are_rejected(self):
        cases = []
        for field in usage():
            for bad in (True, -1, 1.5, "1", float("nan")):
                item = sample("one")
                item[field] = bad
                cases.append(item)
        cases.extend([sample("one", cached=95, writes=10), sample("one", reasoning=41)])
        for item in cases:
            with self.subTest(item=item), self.assertRaises(ValueError):
                accounting.normalize_samples([item], "delta")


class RunFixtures(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def make_run(self, variant="baseline", run_id=None, outcome="pass", attempts=None,
                 suite=None):
        suite = SUITE if suite is None else suite
        run_id = run_id or variant + "-trial"
        root = self.root / run_id
        root.mkdir()
        result = {"schema": 1, "suite": suite["id"], "run_id": run_id, "variant": variant,
                  "fixture": {"id": suite["fixture_id"], "sha256": "a" * 64},
                  "task_sha256": "b" * 64, "model": "requested-model",
                  "settings": {"reasoning": "high"}, "skill_revision": "revision-" + variant,
                  "cases": [{"id": case, "checks": [
                      {"id": check, "kind": kind, "status": "pass", "evidence": {
                          "text": "Synthetic observed contract used for accounting tests."}}
                      for check, kind in checks.items()]}
                      for case, checks in suite["cases"].items()]}
        if outcome != "pass":
            check = result["cases"][0]["checks"][0]
            check["status"] = outcome
            if outcome == "not-run":
                check["reason"] = "Synthetic execution did not complete this observation."
                del check["evidence"]
        result_path = root / "result.json"
        result_path.write_text(json.dumps(result), encoding="utf-8")
        attempts = copy.deepcopy(attempts if attempts is not None else [self.attempt()])
        for index, attempt in enumerate(attempts):
            source = root / ("source-" + str(index) + ".jsonl")
            source.write_text(json.dumps({"synthetic": attempt}), encoding="utf-8")
            attempt["source"] = {"path": source.name,
                                 "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
        sidecar = {"schema": 1, "run_id": run_id,
                   "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
                   "attempts": attempts}
        sidecar_path = root / "usage.json"
        sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")
        return result_path, sidecar_path

    def attempt(self, **overrides):
        return {"attempt_id": "root", "parent_id": None, "status": "completed",
                "provider": "test-provider", "runtime_version": "synthetic-1",
                "requested_model": "requested-model", "observed_model": "observed-model",
                "usage_status": "observed", "includes_children": False, "usage": usage(),
                "duration_seconds": 2.5, **overrides}

    def rewrite(self, path, mutate):
        value = json.loads(path.read_text(encoding="utf-8"))
        mutate(value)
        path.write_text(json.dumps(value), encoding="utf-8")

    def summarize(self, paths, prices=None):
        return accounting.summarize_run(*paths, prices=prices)


class RunTests(RunFixtures):
    def test_exact_cache_and_reasoning_arithmetic_and_provenance(self):
        summary = self.summarize(self.make_run(), [price()])
        # 70 ordinary input * 2 + 20 cached * .5 + 10 writes * 3 + 40 output * 10.
        self.assertEqual(Decimal(summary["estimated_cost"]), Decimal("0.00058"))
        self.assertEqual(summary["tokens"], usage())
        self.assertEqual(summary["usage_status"], "observed")
        self.assertEqual(summary["cost_status"], "estimated")
        self.assertEqual(summary["cost_kind"], "rate-estimate")
        self.assertTrue(summary["quality_pass"])
        self.assertEqual(summary["pricing"][0]["source"], price()["source"])
        self.assertEqual(summary["pricing"][0]["as_of"], "2026-09-09")
        self.assertEqual(summary["execution"][0]["observed_model"], "observed-model")

    def test_large_fractional_rates_keep_decimal_precision(self):
        rates = {key: "0.12345678901234567890123456789" for key in price()["rates"]}
        summary = self.summarize(self.make_run(attempts=[self.attempt(
            usage=usage(input_tokens=10**30, cached=0, writes=0, output=0, reasoning=0))]),
            [price(rates=rates)])
        self.assertEqual(summary["estimated_cost"], "123456789012345678901234.56789")

    def test_failed_retry_and_child_all_count(self):
        attempts = [self.attempt(attempt_id="first", status="failed"),
                    self.attempt(attempt_id="retry"),
                    self.attempt(attempt_id="child", parent_id="retry")]
        summary = self.summarize(self.make_run(attempts=attempts), [price()])
        self.assertEqual(summary["tokens"], usage(input_tokens=300, cached=60, writes=30,
                                                output=120, reasoning=45))
        self.assertEqual(Decimal(summary["estimated_cost"]), Decimal("0.00174"))
        self.assertEqual(summary["coverage"]["attempts"], 3)
        self.assertEqual(summary["duration_seconds"], 7.5)

    def test_missing_sidecar_is_unavailable_and_quality_still_passes(self):
        result, _ = self.make_run()
        summary = accounting.summarize_run(result)
        self.assertTrue(summary["quality_pass"])
        self.assertEqual(summary["usage_status"], "unavailable")
        self.assertIsNone(summary["tokens"])
        self.assertIsNone(summary["estimated_cost"])

    def test_raw_result_hash_and_run_id_must_match(self):
        for field, value in (("result_sha256", "c" * 64), ("run_id", "different-run")):
            with self.subTest(field=field):
                paths = self.make_run(run_id="mismatch-" + field.replace("_", "-"))
                self.rewrite(paths[1], lambda document: document.update({field: value}))
                summary = self.summarize(paths, [price()])
                self.assertEqual(summary["usage_status"], "invalid")
                self.assertTrue(summary["quality_pass"])
                self.assertIsNone(summary["estimated_cost"])

    def test_result_whitespace_changes_break_raw_byte_binding(self):
        paths = self.make_run()
        paths[0].write_text(paths[0].read_text() + "\n", encoding="utf-8")
        self.assertEqual(self.summarize(paths)["usage_status"], "invalid")

    def test_source_hash_path_empty_and_symlink_escape_are_invalid(self):
        for index, mutation in enumerate((
                lambda source: source.update(sha256="c" * 64),
                lambda source: source.update(path="../outside.jsonl"),
                lambda source: source.update(path="/etc/passwd"),
                lambda source: source.update(path="missing.jsonl"),
                lambda source: source.update(path=""))):
            with self.subTest(index=index):
                paths = self.make_run(run_id="bad-source-" + str(index))
                self.rewrite(paths[1], lambda document: mutation(document["attempts"][0]["source"]))
                self.assertEqual(self.summarize(paths)["usage_status"], "invalid")
        paths = self.make_run(run_id="empty-source")
        (paths[0].parent / "source-0.jsonl").write_bytes(b"")
        self.assertEqual(self.summarize(paths)["usage_status"], "invalid")
        paths = self.make_run(run_id="symlink-source")
        outside = self.root / "outside.jsonl"
        outside.write_text("synthetic outside source", encoding="utf-8")
        link = paths[0].parent / "outside-link.jsonl"
        try:
            link.symlink_to(outside)
        except OSError:
            self.skipTest("Symlink creation not available on this platform")
        self.rewrite(paths[1], lambda document: document["attempts"][0]["source"].update(
            path=link.name, sha256=hashlib.sha256(outside.read_bytes()).hexdigest()))
        self.assertEqual(self.summarize(paths)["usage_status"], "invalid")

    def test_missing_child_or_incomplete_retry_prevents_partial_totals(self):
        for index, unknown in enumerate((
                self.attempt(attempt_id="child", parent_id="root", usage_status="unavailable",
                             usage=None, reason="Child token telemetry was unavailable."),
                self.attempt(attempt_id="retry", status="incomplete"))):
            with self.subTest(index=index):
                paths = self.make_run(run_id="incomplete-" + str(index),
                                      attempts=[self.attempt(), unknown])
                summary = self.summarize(paths, [price()])
                self.assertEqual(summary["usage_status"], "unavailable")
                self.assertIsNone(summary["tokens"])
                self.assertIsNone(summary["estimated_cost"])

    def test_parent_including_separately_listed_child_is_unavailable(self):
        paths = self.make_run(attempts=[self.attempt(includes_children=True),
                                       self.attempt(attempt_id="child", parent_id="root")])
        summary = self.summarize(paths, [price()])
        self.assertEqual(summary["usage_status"], "unavailable")
        self.assertTrue(any("includes_children" in reason for reason in summary["reasons"]))
        self.assertIsNone(summary["tokens"])

    def test_duplicate_id_missing_parent_and_cycles_are_invalid(self):
        collections = [[self.attempt(), self.attempt()],
                       [self.attempt(parent_id="absent")],
                       [self.attempt(parent_id="root")],
                       [self.attempt(parent_id="child"),
                        self.attempt(attempt_id="child", parent_id="root")]]
        for index, attempts in enumerate(collections):
            with self.subTest(index=index):
                paths = self.make_run(run_id="bad-tree-" + str(index), attempts=attempts)
                self.assertEqual(self.summarize(paths)["usage_status"], "invalid")

    def test_same_source_path_cannot_be_charged_as_two_attempts(self):
        paths = self.make_run(attempts=[self.attempt(), self.attempt(attempt_id="retry")])
        self.rewrite(paths[1], lambda document: document["attempts"][1].update(
            source={**document["attempts"][0]["source"], "path": "./source-0.jsonl"}))
        summary = self.summarize(paths, [price()])
        self.assertEqual(summary["usage_status"], "invalid")
        self.assertTrue(any("source path" in message for message in summary["errors"]))
        self.assertIsNone(summary["estimated_cost"])

    def test_identical_bytes_in_distinct_sources_can_describe_independent_attempts(self):
        paths = self.make_run(attempts=[self.attempt(), self.attempt(attempt_id="retry")])
        source = paths[0].parent / "source-0.jsonl"
        (paths[0].parent / "source-1.jsonl").write_bytes(source.read_bytes())
        self.rewrite(paths[1], lambda document: document["attempts"][1]["source"].update(
            sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
        summary = self.summarize(paths, [price()])
        self.assertEqual(summary["usage_status"], "observed")
        self.assertEqual(Decimal(summary["estimated_cost"]), Decimal("0.00116"))

    def test_unknown_cache_writes_blocks_price_but_reasoning_does_not(self):
        paths = self.make_run(attempts=[self.attempt(usage=usage(writes=None))])
        summary = self.summarize(paths, [price()])
        self.assertEqual(summary["usage_status"], "observed")
        self.assertIsNone(summary["tokens"]["cache_write_tokens"])
        self.assertIsNone(summary["estimated_cost"])
        paths = self.make_run(run_id="unknown-reasoning", attempts=[self.attempt(
            usage=usage(reasoning=None))])
        self.assertEqual(Decimal(self.summarize(paths, [price()])["estimated_cost"]),
                         Decimal("0.00058"))

    def test_missing_prices_or_observed_model_cannot_use_requested_model(self):
        paths = self.make_run(attempts=[self.attempt(observed_model=None)])
        self.assertIsNone(self.summarize(paths, [price(model="requested-model")])["estimated_cost"])
        paths = self.make_run(run_id="no-prices")
        self.assertIsNone(self.summarize(paths)["estimated_cost"])
        self.assertIsNone(self.summarize(paths, [price(model="different-model")])["estimated_cost"])
        self.assertIsNone(self.summarize(paths, [price(provider="other-provider")])["estimated_cost"])

    def test_invalid_price_provenance_and_numeric_forms_fail_closed(self):
        invalid = [price(as_of="2026-02-30"), price(as_of="20260909"),
                   price(source="http://provider.example/pricing"), price(source="https://"),
                   price(currency=""), price(schema=True)]
        for bad in ("NaN", "Infinity", "-1", 1, True, "", "1e10"):
            rates = price()["rates"]
            rates["input"] = bad
            invalid.append(price(rates=rates))
        paths = self.make_run()
        for table in invalid:
            with self.subTest(table=table):
                summary = self.summarize(paths, [table])
                self.assertEqual(summary["cost_status"], "invalid")
                self.assertIsNone(summary["estimated_cost"])
                self.assertEqual(summary["usage_status"], "observed")
        self.assertEqual(self.summarize(paths, [price(), price()])["cost_status"], "invalid")

    def test_attempt_metadata_and_duration_are_validated(self):
        mutations = [{"duration_seconds": True}, {"duration_seconds": -1},
                     {"duration_seconds": float("inf")}, {"includes_children": 1},
                     {"status": "success"}, {"usage_status": "unknown"},
                     {"usage_status": "unavailable", "usage": None},
                     {"observed_model": ""}, {"runtime_version": None}, {"provider": ""}]
        for index, mutation in enumerate(mutations):
            with self.subTest(mutation=mutation):
                paths = self.make_run(run_id="metadata-" + str(index),
                                      attempts=[self.attempt(**mutation)])
                self.assertEqual(self.summarize(paths)["usage_status"], "invalid")

    def test_invalid_quality_record_has_no_quality_pass_claim(self):
        paths = self.make_run()
        self.rewrite(paths[0], lambda document: document["cases"][0]["checks"].pop())
        summary = self.summarize(paths)
        self.assertIsNone(summary["quality_pass"])
        self.assertEqual(summary["usage_status"], "invalid")

    def test_known_scope_suite_is_validated_without_changing_default_quality_schema(self):
        suite = scope_suites()["narrow-spacing-v1"]
        paths = self.make_run(suite=suite)
        self.assertTrue(self.summarize(paths)["quality_pass"])
        self.assertEqual(json.loads(paths[0].read_text())["schema"], 1)

    def test_duplicate_json_keys_are_invalid(self):
        paths = self.make_run()
        paths[1].write_text('{"schema": 1, "schema": 1}', encoding="utf-8")
        self.assertEqual(self.summarize(paths)["usage_status"], "invalid")


class ComparisonTests(RunFixtures):
    def pair(self, number=0, baseline_outcome="pass", candidate_outcome="pass",
             baseline_attempts=None, candidate_attempts=None):
        baseline = self.make_run("baseline", "baseline-" + str(number), baseline_outcome,
                                 baseline_attempts)
        candidate = self.make_run("candidate", "candidate-" + str(number), candidate_outcome,
                                  candidate_attempts)
        return {"baseline_result": baseline[0], "baseline_usage": baseline[1],
                "candidate_result": candidate[0], "candidate_usage": candidate[1]}

    def test_cost_per_completion_includes_failed_tasks_and_retries(self):
        pairs = [self.pair(0), self.pair(1, baseline_outcome="fail", candidate_outcome="fail",
                 baseline_attempts=[self.attempt(status="failed")],
                 candidate_attempts=[self.attempt(attempt_id="failed", status="failed"),
                                     self.attempt(attempt_id="retry", status="failed")])]
        summary = accounting.compare_runs(pairs, [price()])
        self.assertEqual(summary["matched_pairs"], 2)
        self.assertEqual(Decimal(summary["cost"]["baseline"]["attempted_cost"]), Decimal("0.00116"))
        self.assertEqual(Decimal(summary["cost"]["candidate"]["attempted_cost"]), Decimal("0.00174"))
        self.assertEqual(summary["cost"]["candidate"]["completed_tasks"], 1)
        self.assertEqual(Decimal(summary["cost"]["candidate"]["cost_per_completed_task"]), Decimal("0.00174"))
        self.assertEqual(summary["quality"]["candidate"]["completion_rate"], 0.5)
        self.assertEqual(Decimal(summary["cost"]["median_pair_cost_delta"]), Decimal("0.00029"))
        self.assertNotIn("p95", summary["cost"])

    def test_missing_pair_usage_is_excluded_with_reason_and_not_zero(self):
        pairs = [self.pair(0), self.pair(1)]
        pairs[1]["candidate_usage"] = None
        summary = accounting.compare_runs(pairs, [price()])
        self.assertEqual(summary["matched_pairs"], 1)
        self.assertEqual(summary["excluded_pairs"], 1)
        self.assertTrue(summary["pairs"][1]["exclusions"])
        self.assertIsNone(summary["pairs"][1]["candidate"]["estimated_cost"])
        self.assertEqual(summary["quality"]["candidate"]["completed_tasks"], 2)

    def test_missing_result_still_retains_other_outcome(self):
        pair = self.pair(candidate_outcome="fail")
        pair["baseline_result"] = self.root / "missing.json"
        summary = accounting.compare_runs([pair], [price()])
        self.assertFalse(summary["pairs"][0]["candidate"]["quality_pass"])
        self.assertEqual(summary["quality"]["candidate"]["completed_tasks"], 0)
        self.assertEqual(summary["excluded_pairs"], 1)

    def test_no_completions_and_zero_baseline_have_no_savings_ratio(self):
        summary = accounting.compare_runs([self.pair(baseline_outcome="fail",
            candidate_outcome="fail")], [price()])
        self.assertIsNone(summary["cost"]["baseline"]["cost_per_completed_task"])
        self.assertIsNone(summary["savings_fraction"])
        zero = self.attempt(usage=usage(0, 0, 0, 0, 0))
        summary = accounting.compare_runs([self.pair(1, baseline_attempts=[zero])], [price()])
        self.assertIsNone(summary["savings_fraction"])

    def test_quality_regression_prevents_savings_claim(self):
        cheap = self.attempt(usage=usage(0, 0, 0, 1, 0))
        summary = accounting.compare_runs([self.pair(candidate_outcome="fail",
            candidate_attempts=[cheap])], [price()])
        self.assertEqual(summary["verdict"], "tradeoff")
        self.assertIsNone(summary["savings_fraction"])
        self.assertTrue(summary["pairs"][0]["quality"]["regressions"])

    def test_settings_model_fixture_task_and_suite_mismatch_are_excluded(self):
        mutations = [("settings", {"reasoning": "low"}), ("model", "other-model"),
                     ("fixture", {"id": SUITE["fixture_id"], "sha256": "c" * 64}),
                     ("task_sha256", "c" * 64), ("suite", "unknown-suite")]
        for index, (field, value) in enumerate(mutations):
            with self.subTest(field=field):
                pair = self.pair(index)
                self.rewrite(pair["candidate_result"], lambda document: document.update({field: value}))
                summary = accounting.compare_runs([pair], [price()])
                self.assertEqual(summary["matched_pairs"], 0)
                self.assertTrue(summary["pairs"][0]["exclusions"])

    def test_observed_execution_model_currency_and_pricing_snapshot_must_match(self):
        other = self.attempt(observed_model="second-model")
        pair = self.pair(candidate_attempts=[other])
        for overrides in ({}, {"currency": "EUR"}, {"as_of": "2026-09-08"}):
            with self.subTest(overrides=overrides):
                summary = accounting.compare_runs([pair], [price(), price(model="second-model", **overrides)])
                self.assertEqual(summary["matched_pairs"], 0)
                self.assertTrue(summary["pairs"][0]["exclusions"])

    def test_duplicate_pair_or_reused_run_is_rejected_without_silent_dedup(self):
        pair = self.pair()
        summary = accounting.compare_runs([pair, pair], [price()])
        self.assertEqual(summary["verdict"], "invalid")
        self.assertIsNone(summary["savings_fraction"])
        self.assertTrue(summary["errors"])
        self.assertEqual(len(summary["pairs"]), 2)

    def test_empty_pair_list_reports_no_comparison(self):
        summary = accounting.compare_runs([], [price()])
        self.assertEqual(summary["matched_pairs"], 0)
        self.assertIsNone(summary["savings_fraction"])
        self.assertIsNone(summary["quality"]["candidate"]["completion_rate"])

    def test_observed_tokens_can_be_compared_without_inventing_model_or_prices(self):
        unknown = self.attempt(observed_model=None)
        cheaper = self.attempt(observed_model=None, usage=usage(input_tokens=70, output=20))
        summary = accounting.compare_runs([self.pair(baseline_attempts=[unknown],
            candidate_attempts=[cheaper])])
        self.assertEqual(summary["matched_pairs"], 0)
        self.assertEqual(summary["usage_matched_pairs"], 1)
        self.assertEqual(summary["verdict"], "compared_usage")
        self.assertEqual(summary["usage"]["baseline"]["total_tokens"], 140)
        self.assertEqual(summary["usage"]["candidate"]["total_tokens"], 90)
        self.assertEqual(summary["usage"]["median_pair_total_token_delta"], "-50")
        self.assertIsNone(summary["savings_fraction"])
        self.assertIsNone(summary["pairs"][0]["baseline"]["execution"][0]["observed_model"])

    def test_token_attempt_total_includes_failure_and_has_no_partial_unknown_total(self):
        pairs = [self.pair(0), self.pair(1, baseline_outcome="fail", candidate_outcome="fail")]
        summary = accounting.compare_runs(pairs)
        self.assertEqual(summary["usage"]["baseline"]["total_tokens"], 280)
        self.assertEqual(summary["usage"]["baseline"]["tokens_per_completed_task"], "280")
        pairs[1]["candidate_usage"] = None
        summary = accounting.compare_runs(pairs)
        self.assertEqual(summary["usage_matched_pairs"], 1)
        self.assertEqual(summary["usage_excluded_pairs"], 1)
        self.assertIsNone(summary["pairs"][1]["total_token_delta"])

    def test_same_model_child_is_an_accounted_outcome_not_a_condition_mismatch(self):
        child = self.attempt(attempt_id="child", parent_id="root")
        summary = accounting.compare_runs([self.pair(candidate_attempts=[self.attempt(), child])], [price()])
        self.assertEqual(summary["usage_matched_pairs"], 1)
        self.assertEqual(summary["matched_pairs"], 1)
        self.assertEqual(summary["usage"]["candidate"]["total_tokens"], 280)
        self.assertEqual(summary["cost"]["candidate"]["attempted_cost"], "0.00116")
        self.assertEqual(summary["pairs"][0]["exclusions"], [])

    def test_even_median_and_cost_delta_keep_precision_beyond_decimal_default(self):
        count = 10**30
        baseline = self.attempt(usage=usage(count, 0, 0, 0, 0))
        candidate = self.attempt(usage=usage(count + 1, 0, 0, 0, 0))
        pair = self.pair(baseline_attempts=[baseline], candidate_attempts=[candidate])
        rates = {key: "0.12345678901234567890123456789" for key in price()["rates"]}
        summary = accounting.compare_runs([pair], [price(rates=rates)])
        expected = Decimal("0.00000012345678901234567890123456789")
        self.assertEqual(Decimal(summary["pairs"][0]["cost_delta"]), expected)
        self.assertEqual(Decimal(summary["cost"]["median_pair_cost_delta"]), expected)
        pairs = [self.pair(1), self.pair(2, candidate_attempts=[candidate])]
        summary = accounting.compare_runs(pairs, [price(rates=rates)])
        # Rational arithmetic independently checks all decimal digits: the first
        # pair's delta is zero; the second adds (10**30 + 1) - 140 priced tokens.
        expected_median = Fraction(10**30 - 139) * Fraction(rates["input"]) / 2000000
        self.assertEqual(Fraction(summary["cost"]["median_pair_cost_delta"]), expected_median)

    def test_positive_savings_requires_passing_observed_quality(self):
        cheap = self.attempt(usage=usage(50, 10, 5, 20, 5))
        summary = accounting.compare_runs([self.pair(candidate_attempts=[cheap])], [price()])
        self.assertEqual(summary["savings_fraction"], "0.5")
        pair = self.pair(1, baseline_outcome="not-run", candidate_outcome="not-run",
                         candidate_attempts=[cheap])
        summary = accounting.compare_runs([self.pair(2), pair], [price()])
        self.assertIsNone(summary["savings_fraction"])


if __name__ == "__main__":
    unittest.main()
