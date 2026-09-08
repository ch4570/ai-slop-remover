#!/usr/bin/env python3
"""Validate four cases x two repeats x two native contexts and compare eight pairs."""
import argparse
import json
from pathlib import Path
import sys

from compare_evals import compare, load_result, meaningful, scope_suites, validate


def local_file(root, name):
    if not isinstance(name, str) or not name:
        raise ValueError("Artifact path is missing")
    path = (root / name).resolve()
    if Path(name).is_absolute() or not path.is_relative_to(root.resolve()) or not path.is_file() or path.stat().st_size == 0:
        raise ValueError("Artifact is absent, empty or outside manifest directory: " + name)
    return path


def summarize(manifest, root):
    errors, missing, entries, native_ids, loaded = [], [], {}, set(), {}
    suites = scope_suites()
    cases = tuple(suite["fixture_id"] for suite in suites.values())
    if not isinstance(manifest, dict) or manifest.get("schema") != 1 or type(manifest.get("schema")) is not int or manifest.get("repetitions") != 2 or type(manifest.get("repetitions")) is not int:
        return {"verdict": "incomplete", "errors": ["Manifest requires schema 1 and exactly two repetitions"], "pairs": []}
    host = manifest.get("host_coverage", {})
    for mode in ("installed-host-explicit", "automatic-discovery"):
        coverage = host.get(mode, {}) if isinstance(host, dict) else {}
        if not isinstance(coverage, dict):
            errors.append(mode + ": host coverage must be an object")
        elif coverage.get("status") != "not-run" or not meaningful(coverage.get("reason"), 12):
            errors.append(mode + ": snapshot-direct trials do not establish this host coverage")
    trials = manifest.get("trials", [])
    if not isinstance(trials, list):
        trials = []
        errors.append("trials must be a list")
    common_conditions = None
    observed_candidate_failures = {}
    revisions = {}
    case_conditions = {}
    run_ids = set()
    for index, trial in enumerate(trials):
        label = "trial " + str(index + 1)
        try:
            if not isinstance(trial, dict) or set(trial) != {"case", "repeat", "variant", "native_agent_id", "result", "launch", "output"}:
                raise ValueError("Unexpected or missing trial fields")
            case, repeat, variant = trial["case"], trial["repeat"], trial["variant"]
            if case not in cases or type(repeat) is not int or repeat not in (1, 2) or variant not in ("baseline", "candidate"):
                raise ValueError("Unknown case, repetition or variant")
            key = (case, repeat, variant)
            label = "/".join(map(str, key))
            if key in entries:
                raise ValueError("Duplicate case/repeat/variant")
            entries[key] = trial
            result_path = local_file(root, trial["result"])
            run = load_result(result_path)
            schema_errors = validate(run, variant, result_path.parent, suites[case + "-v1"])
            if schema_errors:
                raise ValueError("; ".join(schema_errors))
            if variant == "candidate":
                observed_candidate_failures[(case, repeat)] = [
                    case + "/" + check["id"] for check in run["cases"][0]["checks"] if check["status"] == "fail"]
            agent_id = trial["native_agent_id"]
            if not meaningful(agent_id) or agent_id in native_ids:
                raise ValueError("Missing or duplicate native agent ID")
            native_ids.add(agent_id)
            launch = load_result(local_file(root, trial["launch"]))
            local_file(root, trial["output"])
            if launch.get("request", {}).get("fork_turns") != "none" or launch.get("response", {}).get("task_name") != agent_id:
                raise ValueError("Launch must record fork_turns=none and the matching actual agent ID")
            if run.get("run_id") in run_ids:
                raise ValueError("Duplicate result run_id")
            run_ids.add(run.get("run_id"))
            if run.get("settings", {}).get("invocation_mode") != "snapshot-direct":
                raise ValueError("This manifest requires snapshot-direct invocation_mode")
            if run.get("variant") != variant:
                raise ValueError("Manifest variant differs from result variant")
            conditions = (run.get("model"), run.get("settings"))
            if common_conditions is None:
                common_conditions = conditions
            elif common_conditions != conditions:
                errors.append(label + ": model/settings differ across the sixteen contexts")
            fixture_task = (run.get("fixture"), run.get("task_sha256"))
            if case not in case_conditions:
                case_conditions[case] = fixture_task
            elif case_conditions[case] != fixture_task:
                errors.append(label + ": fixture/task changed between repetitions of the same case")
            revision = run.get("skill_revision")
            if variant not in revisions:
                revisions[variant] = revision
            elif revisions[variant] != revision:
                errors.append(label + ": skill revision changed within the same variant")
            loaded[key] = (run, result_path.parent)
        except (OSError, ValueError, TypeError, AttributeError, KeyError) as error:
            errors.append(label + ": " + str(error))
    pairs = []
    for case in cases:
        for repeat in (1, 2):
            keys = [(case, repeat, variant) for variant in ("baseline", "candidate")]
            absent = ["/".join(map(str, key)) for key in keys if key not in loaded]
            if absent:
                missing.extend(absent)
                outcome = {"verdict": "incomplete", "missing": absent}
            else:
                baseline, candidate = (loaded[key] for key in keys)
                outcome = compare(baseline[0], candidate[0], baseline[1], candidate[1], suites[case + "-v1"])
                if outcome["verdict"] == "invalid":
                    errors.extend(case + "/" + str(repeat) + ": " + message for message in outcome["errors"])
            failures = observed_candidate_failures.get((case, repeat), [])
            if failures and outcome["verdict"] != "changes-required":
                # Comparison needs both contexts; an observed candidate failure does not.
                outcome = {**outcome, "comparison_verdict": outcome["verdict"], "verdict": "changes-required",
                           "candidate_failures": failures, "regressions": [], "improvements": [],
                           "limits": "Candidate failures are recorded, but missing or invalid paired evidence cannot establish regressions or improvements."}
            pairs.append({"case": case, "repeat": repeat, **outcome})
    # Missing launches or paired records never erase a schema-valid candidate failure.
    failed = any(pair["verdict"] == "changes-required" for pair in pairs)
    incomplete = bool(errors or missing or any(pair["verdict"] != "pass" for pair in pairs))
    return {"schema": 1, "verdict": "changes-required" if failed else "incomplete" if incomplete else "pass",
            "expected_trials": 16, "loaded_trials": len(loaded), "expected_pairs": 8,
            "pairs": pairs, "errors": errors, "missing": missing, "host_coverage": host,
            "limits": "Two repetitions per case are recorded outcomes, not general quality or causal improvement. Raw evidence truth and semantic/visual judgments require independent review. Host invocation/discovery remain not-run."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = summarize(load_result(args.manifest), args.manifest.parent)
    except (OSError, ValueError) as error:
        result = {"verdict": "incomplete", "errors": [str(error)], "pairs": []}
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return {"pass": 0, "changes-required": 1, "incomplete": 3}[result["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
