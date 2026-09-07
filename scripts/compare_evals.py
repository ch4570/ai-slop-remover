#!/usr/bin/env python3
"""Compare evaluator-recorded behavior/quality evidence; never judge from packaging."""

import argparse
import json
import math
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SUITE = json.loads((ROOT / "evals/checks/suite.json").read_text(encoding="utf-8"))
PLACEHOLDER = re.compile(r"^(?:todo|tbd|unknown|example|placeholder|n/?a|pass|looks good)(?:\b|:)", re.I)
IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9._-]*\Z")


def meaningful(value, minimum=3):
    return isinstance(value, str) and len(value.strip()) >= minimum and not PLACEHOLDER.match(value.strip())


def digest(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{64}", value)) and value != "0" * 64


def validate(run, variant, evidence_root=None):
    """Validate declared evidence, not its truth; files resolve inside the run folder."""
    errors = []
    if not isinstance(run, dict):
        return [f"{variant}: result must be an object"]
    required = {"schema", "suite", "run_id", "variant", "fixture", "task_sha256", "model", "settings", "skill_revision", "cases"}
    if set(run) != required:
        errors.append(f"{variant}: unexpected/missing fields: {sorted(set(run) ^ required)}")
    if type(run.get("schema")) is not int or run.get("schema") != 1:
        errors.append(f"{variant}: schema must be integer 1")
    if run.get("suite") != SUITE["id"] or run.get("variant") != variant:
        errors.append(f"{variant}: incorrect suite or variant")
    if not isinstance(run.get("run_id"), str) or not IDENTIFIER.fullmatch(run["run_id"]):
        errors.append(f"{variant}: run_id must be a nonempty lowercase identifier")
    for key in ("model", "skill_revision"):
        if not meaningful(run.get(key)):
            errors.append(f"{variant}: {key} must identify the actual run")
    if not digest(run.get("task_sha256")):
        errors.append(f"{variant}: task_sha256 must be a nonzero SHA-256")
    fixture = run.get("fixture")
    if not isinstance(fixture, dict) or set(fixture) != {"id", "sha256"} or fixture.get("id") != SUITE["fixture_id"] or not digest(fixture.get("sha256")):
        errors.append(f"{variant}: fixture needs the original suite fixture id and SHA-256")
    settings = run.get("settings")
    if not isinstance(settings, dict) or not settings:
        errors.append(f"{variant}: settings must describe actual runtime settings")
    else:
        for key, value in settings.items():
            valid_value = type(value) in (bool, int) or (type(value) is float and math.isfinite(value)) or meaningful(value, 1)
            if not isinstance(key, str) or not IDENTIFIER.fullmatch(key) or not valid_value:
                errors.append(f"{variant}: invalid runtime setting {key!r}")
    cases = run.get("cases")
    if not isinstance(cases, list) or not cases:
        return errors + [f"{variant}: cases must be a nonempty list"]
    case_ids = []
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"id", "checks"} or not isinstance(case.get("id"), str):
            errors.append(f"{variant}: invalid case object")
            continue
        case_id = case["id"]
        case_ids.append(case_id)
        expected = SUITE["cases"].get(case_id, {})
        checks = case["checks"]
        if not isinstance(checks, list):
            errors.append(f"{variant}/{case_id}: checks must be a list")
            continue
        check_ids = []
        for check in checks:
            if not isinstance(check, dict) or not {"id", "kind", "status"} <= set(check) or set(check) - {"id", "kind", "status", "evidence", "reason"} or not isinstance(check.get("id"), str):
                errors.append(f"{variant}/{case_id}: invalid check object")
                continue
            check_id = check["id"]
            check_ids.append(check_id)
            label = f"{variant}/{case_id}/{check_id}"
            if check.get("kind") != expected.get(check_id):
                errors.append(f"{label}: check kind differs from evaluator-owned suite")
            status = check.get("status")
            if status not in ("pass", "fail", "not-run"):
                errors.append(f"{label}: status must be pass, fail, or not-run")
            elif status == "not-run":
                if not meaningful(check.get("reason"), 12):
                    errors.append(f"{label}: not-run needs a concrete reason")
            else:
                evidence = check.get("evidence")
                if not isinstance(evidence, dict) or not evidence or set(evidence) - {"text", "path"}:
                    errors.append(f"{label}: observed evidence is required")
                    continue
                if "text" in evidence and not meaningful(evidence["text"], 12):
                    errors.append(f"{label}: evidence text must describe an actual observation")
                if "path" in evidence:
                    path = evidence["path"]
                    if not isinstance(path, str) or not path.strip() or evidence_root is None:
                        errors.append(f"{label}: file evidence requires a valid result-relative path")
                        continue
                    root = Path(evidence_root).resolve()
                    target = (root / path).resolve()
                    if Path(path).is_absolute() or not target.is_relative_to(root) or not target.is_file() or target.stat().st_size == 0:
                        errors.append(f"{label}: evidence file is absent, empty, or outside result directory")
        if len(check_ids) != len(set(check_ids)) or set(check_ids) != set(expected):
            errors.append(f"{variant}/{case_id}: duplicate, missing, or unknown checks")
    if len(case_ids) != len(set(case_ids)) or set(case_ids) != set(SUITE["cases"]):
        errors.append(f"{variant}: duplicate, missing, or unknown cases")
    return errors


def compare(baseline, candidate, baseline_root=None, candidate_root=None):
    errors = validate(baseline, "baseline", baseline_root) + validate(candidate, "candidate", candidate_root)
    if errors:
        return {"verdict": "invalid", "errors": errors}
    for field in ("suite", "fixture", "task_sha256", "model", "settings"):
        if baseline[field] != candidate[field]:
            errors.append(f"Runs are not comparable: {field} differs")
    if baseline["run_id"] == candidate["run_id"]:
        errors.append("Runs must have distinct run_id values")
    if errors:
        return {"verdict": "invalid", "errors": errors}
    flatten = lambda run: {f"{case['id']}/{check['id']}": check for case in run["cases"] for check in case["checks"]}
    before, after = flatten(baseline), flatten(candidate)
    incomplete = sorted(f"{variant}/{key}" for variant, checks in (("baseline", before), ("candidate", after)) for key, check in checks.items() if check["status"] == "not-run")
    failures = sorted(key for key, check in after.items() if check["status"] == "fail")
    regressions = sorted(key for key in after if before[key]["status"] == "pass" and after[key]["status"] == "fail")
    improvements = sorted(key for key in after if before[key]["status"] == "fail" and after[key]["status"] == "pass")
    verdict = "changes-required" if failures else "incomplete" if incomplete else "pass"
    return {
        "verdict": verdict, "improvements": improvements, "regressions": regressions,
        "candidate_failures": failures, "not_run": incomplete,
        "limits": "Recorded outcomes only; this comparison does not verify evidence truth or establish general UI quality.",
    }


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError(f"Invalid JSON number: {value}")


def load_result(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object,
                      parse_constant=invalid_constant)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    try:
        outcome = compare(load_result(args.baseline), load_result(args.candidate), args.baseline.parent, args.candidate.parent)
    except (OSError, UnicodeError, ValueError) as error:
        outcome = {"verdict": "invalid", "errors": [str(error)]}
    print(json.dumps(outcome, ensure_ascii=False, indent=2))
    return {"pass": 0, "changes-required": 1, "invalid": 2, "incomplete": 3}[outcome["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
