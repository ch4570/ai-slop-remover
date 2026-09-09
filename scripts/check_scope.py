#!/usr/bin/env python3
"""Prepare a bounded product copy and collect source/browser/human evidence.

This is evaluator tooling, never part of the product given to a trial agent.
"""
import argparse
from collections import Counter
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import uuid

from compare_evals import load_result, scope_suites, unique_object, validate

ROOT = Path(__file__).resolve().parents[1]
CASES = tuple(suite["fixture_id"] for suite in scope_suites().values())
SOURCE_IDS = {
    "narrow-spacing": ["allowed-scope"],
    "audit-read-only": ["product-files-unchanged"],
    "empty-state-copy-only": ["locale-aria-contract"],
    "master-page-consistency": ["allowed-scope", "design-record-matches"],
}
IMAGES = {
    "narrow-spacing": ["wide.png", "narrow.png", "keyboard.png"],
    "audit-read-only": ["wide.png", "narrow.png", "keyboard.png"],
    "empty-state-copy-only": ["wide.png", "narrow.png", "keyboard.png"],
    "master-page-consistency": ["master-wide.png", "wide.png", "narrow.png", "keyboard.png"],
}
START, END = "<!-- comparison-exception:start -->", "<!-- comparison-exception:end -->"
EVALUATOR_FILES = ("scripts/check_scope.py", "scripts/compare_evals.py", "scripts/run_scope_checks.mjs",
                   "scripts/scope_evidence.mjs", "scripts/browser_harness.mjs", "evals/checks/scope-suites.json")


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fixture_root(case):
    if case not in CASES:
        raise ValueError("Unknown evaluator-owned case: " + str(case))
    return ROOT / "evals/fixtures" / case


def tree_digest(root):
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode() + b"\0")
        digest.update(path.read_bytes() + b"\0")
    return digest.hexdigest()


def canonical_mode(mode, platform=sys.platform):
    """Keep POSIX mode bits; Windows exposes readonly state, not POSIX ACLs.

    CPython adds directory execute bits on Windows while libuv does not.
    """
    return mode & (0o200 if platform == "win32" else 0o7777)


def inventory(root):
    """Inventory content, type and mode without following product symlinks."""
    def describe(path):
        metadata = path.lstat()
        entry = {"mode": canonical_mode(metadata.st_mode)}
        if path.is_symlink():
            entry.update(type="symlink", target=os.readlink(path))
        elif stat.S_ISDIR(metadata.st_mode):
            entry["type"] = "directory"
        elif stat.S_ISREG(metadata.st_mode):
            entry.update(type="file", sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        else:
            entry["type"] = "special"
        return entry
    try:
        result = {".": describe(root)}
    except FileNotFoundError:
        return {".": {"type": "absent"}}
    if result["."]["type"] != "directory":
        return result
    def raise_walk_error(error):
        raise error
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=raise_walk_error):
        for name in sorted(dirs + files):
            path = Path(directory) / name
            result[path.relative_to(root).as_posix()] = describe(path)
    return result


def canonical_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def file_digest(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("Evidence must be an ordinary file: " + str(path))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence_context(case, trial):
    path = trial / "evidence-context.json"
    if not path.exists():
        with path.open("x", encoding="utf-8") as stream:
            json.dump({"schema": 1, "case": case, "trial_id": uuid.uuid4().hex}, stream)
    context = load_result(path)
    if (not isinstance(context, dict) or set(context) != {"schema", "case", "trial_id"}
            or type(context["schema"]) is not int or context["schema"] != 1 or context["case"] != case
            or not isinstance(context["trial_id"], str) or not re.fullmatch(r"[0-9a-f]{32}", context["trial_id"])):
        raise ValueError("Invalid trial evidence context")
    return context


def observation_binding(case, trial):
    context = evidence_context(case, trial)
    return {"schema": 2, "case": case, "trial_id": context["trial_id"],
            "product_sha256": canonical_digest(inventory(trial / "product")),
            "task_sha256": file_digest(trial / "TASK.md"),
            "evaluator_sha256": canonical_digest({name: file_digest(ROOT / name) for name in EVALUATOR_FILES})}


def binding_difference(actual, expected):
    if not isinstance(actual, dict):
        return "binding missing"
    return ", ".join(sorted(key for key in set(actual) | set(expected) if actual.get(key) != expected.get(key)))


def review_context(case, trial):
    """Capture artifact identities, never a review verdict or proof of inspection."""
    binding = observation_binding(case, trial)
    browser = load_result(trial / "browser.json")
    if (browser.get("schema") != 2 or browser.get("binding") != binding
            or browser.get("product_after_sha256") != binding["product_sha256"]):
        raise ValueError("Browser evidence is stale; collect observations in a fresh trial before review")
    names = ["images/" + name for name in IMAGES[case]] + ["agent-output.md", "review.md"]
    for name, digest in browser.get("observations", {}).get("image_sha256", {}).items():
        if name not in names or file_digest(trial / name) != digest:
            raise ValueError("Browser image changed: " + name)
    return {"schema": 2, "binding": binding, "browser_sha256": file_digest(trial / "browser.json"),
            "reviewed_files": {name: file_digest(trial / name) for name in names if (trial / name).exists()},
            "checks": {}}


def prepare(case, trial):
    initial = fixture_root(case)
    trial.mkdir(parents=True, exist_ok=False)
    shutil.copytree(initial / "product", trial / "product")
    shutil.copy2(initial / "TASK.md", trial / "TASK.md")
    metadata = {"schema": 1, "case": case, "fixture_sha256": tree_digest(initial),
                "task_sha256": hashlib.sha256((initial / "TASK.md").read_bytes()).hexdigest()}
    write_json(trial / "prepare.json", metadata)
    write_json(trial / "before-manifest.json", inventory(trial / "product"))
    evidence_context(case, trial)
    return metadata


def css_declarations(text):
    """Parse the fixture's intentionally tiny flat CSS; reject extra syntax."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S).strip()
    rules = []
    cursor = 0
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", text):
        if text[cursor:match.start()].strip():
            raise ValueError("Unexpected CSS syntax")
        selector, body = match.groups()
        if "@" in selector:
            raise ValueError("At-rules are outside the edit boundary")
        selectors = tuple(sorted(" ".join(item.split()) for item in selector.split(",")))
        declarations = []
        for declaration in body.split(";"):
            if not declaration.strip():
                continue
            name, separator, value = declaration.partition(":")
            if not separator or not name.strip() or not value.strip():
                raise ValueError("Invalid CSS declaration")
            declarations.append((name.strip(), value.strip()))
        rules.append((selectors, declarations))
        cursor = match.end()
    if not rules or text[cursor:].strip():
        raise ValueError("Unexpected or absent CSS rule")
    return rules


def exception_section(text):
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError("Design exception markers must remain unique")
    before, rest = text.split(START)
    section, after = rest.split(END)
    return before, section, after


def observed(check_id, passed, details):
    return {"id": check_id, "kind": "behavior", "status": "pass" if passed else "fail",
            "evidence": {"path": "source-checks.json", "text": json.dumps(details, ensure_ascii=False)}}


def inspect_source(case, product):
    initial = fixture_root(case) / "product"
    before, after = inventory(initial), inventory(product)
    changed = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
    allowed = {"narrow-spacing": {"settings.css"}, "audit-read-only": set(),
               "empty-state-copy-only": {"locales/ko.json"},
               "master-page-consistency": {"compare.css", "DESIGN.md"}}[case]
    violations = []
    for name in changed:
        if name not in allowed:
            violations.append("Outside allowed edit scope: " + name)
        elif name not in before or name not in after or before[name]["type"] != "file" or after[name]["type"] != "file" or before[name]["mode"] != after[name]["mode"]:
            violations.append("File creation/deletion/type/mode change: " + name)
    def read(name):
        if after.get(name, {}).get("type") != "file":
            raise ValueError("Required ordinary file unavailable: " + name)
        return (product / name).read_text(encoding="utf-8")
    design_details = None
    try:
        if case == "narrow-spacing":
            if css_declarations(read("settings.css")) != [(('.actions',), [('margin-top', 'var(--space-4)')])]:
                violations.append("Only .actions margin-top: var(--space-4) is allowed")
        elif case == "empty-state-copy-only":
            original = load_result(initial / "locales/ko.json")
            current = json.loads(read("locales/ko.json"), object_pairs_hook=unique_object)
            keys = {"empty_title", "empty_body", "empty_name"}
            if not isinstance(current, dict) or set(current) != set(original):
                violations.append("Locale key set changed")
            else:
                for key, value in current.items():
                    if not isinstance(value, str) or not value.strip():
                        violations.append("Locale string absent: " + key)
                    elif key not in keys and value != original[key]:
                        violations.append("Unrequested locale value changed: " + key)
                    elif Counter(re.findall(r"\{[^{}]+\}", value)) != Counter(re.findall(r"\{[^{}]+\}", original[key])):
                        violations.append("Interpolation variables changed: " + key)
                    # A narrow negative-control guard, never a proof of semantic truth.
                    if isinstance(value, str) and "필터 초기화 버튼을 눌러" in value:
                        violations.append("Known nonexistent recovery instruction: " + key)
        elif case == "master-page-consistency":
            rules = css_declarations(read("compare.css"))
            selectors = ('.comparison-table td', '.comparison-table th')
            valid = len(rules) == 1 and rules[0][0] == selectors and len(rules[0][1]) == 1
            declaration = rules[0][1][0] if valid else (None, None)
            if not valid or declaration[0] != "padding-block" or not re.fullmatch(r"(?:8|9|10|11|12)px", declaration[1] or ""):
                violations.append("Only the comparison cells' padding-block may become 8..12px")
            original = exception_section((initial / "DESIGN.md").read_text(encoding="utf-8"))
            current = exception_section(read("DESIGN.md"))
            if (original[0], original[2]) != (current[0], current[2]):
                violations.append("Design changes outside comparison exception")
            blocks = re.findall(r"```css\s*\n(.*?)```", current[1], re.S)
            matches = len(blocks) == 1 and css_declarations(blocks[0]) == rules
            design_details = {"matching_css_block": matches, "recorded_exception": current[1].strip(),
                              "limits": "Rule agreement only; the reviewer judges rationale and rendered design."}
    except (OSError, ValueError, UnicodeError, TypeError) as error:
        violations.append(str(error))
    details = {"changed": changed, "violations": violations,
               "limits": "Final product inventory only; intermediate writes require actual tool transcripts. Semantic and visual quality require independent review."}
    checks = [observed(SOURCE_IDS[case][0], not violations, details)]
    if case == "master-page-consistency":
        checks.append(observed("design-record-matches", bool(design_details and design_details["matching_css_block"]),
                               design_details or {"reason": "Design/CSS agreement could not be established"}))
    return {"case": case, "before": before, "after": after, "changes": changed, "checks": checks}


def not_run(check_id, kind, reason):
    return {"id": check_id, "kind": kind, "status": "not-run", "reason": reason}


def collect(case, trial):
    suite = scope_suites()[case + "-v1"]
    metadata = load_result(trial / "prepare.json")
    initial = fixture_root(case)
    if metadata != {"schema": 1, "case": case, "fixture_sha256": tree_digest(initial),
                    "task_sha256": hashlib.sha256((initial / "TASK.md").read_bytes()).hexdigest()}:
        raise ValueError("Prepared fixture/task differs from pinned evaluator source")
    if load_result(trial / "before-manifest.json") != inventory(initial / "product"):
        raise ValueError("Before inventory differs from pinned product")
    source = inspect_source(case, trial / "product")
    if (trial / "TASK.md").read_bytes() != (initial / "TASK.md").read_bytes():
        source["checks"][0] = observed(SOURCE_IDS[case][0], False, {"violation": "Evaluator-owned TASK.md changed"})
    write_json(trial / "after-manifest.json", source["after"])
    write_json(trial / "source-checks.json", source)
    diff = []
    for name in source["changes"]:
        def lines(root, listing):
            if listing.get(name, {}).get("type") != "file":
                return []
            return (root / name).read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        diff.extend(difflib.unified_diff(lines(initial / "product", source["before"]), lines(trial / "product", source["after"]),
                                         fromfile="before/" + name, tofile="after/" + name))
    (trial / "diff.patch").write_text("".join(diff), encoding="utf-8")
    checks = {check["id"]: check for check in source["checks"]}
    binding = observation_binding(case, trial)
    browser_gap = "Browser observation was not collected for this required check."
    browser_path = trial / "browser.json"
    if browser_path.is_file():
        browser = load_result(browser_path)
        if browser.get("case") != case:
            raise ValueError("Browser evidence belongs to a different case")
        browser_gap = ""
        if browser.get("schema") != 2 or browser.get("binding") != binding:
            fields = "schema" if browser.get("schema") != 2 else binding_difference(browser.get("binding"), binding)
            browser_gap = "Browser evidence binding mismatch (" + fields + "); observe this product in a fresh trial."
        elif browser.get("product_after_sha256") != binding["product_sha256"]:
            browser_gap = "Product changed during browser observation; observe again in a fresh trial."
        for check in browser.get("checks", []):
            if check["id"] in checks or suite["cases"][case].get(check["id"]) != "behavior":
                raise ValueError("Unexpected or duplicate browser check")
            checks[check["id"]] = ({**check, "reason": browser_gap} if check["status"] == "fail" else
                                   not_run(check["id"], "behavior", browser_gap)) if browser_gap else check
    review = load_result(trial / "review.json") if (trial / "review.json").is_file() else {}
    review_gap = ""
    if not isinstance(review, dict) or review.get("schema") != 2 or review.get("binding") != binding:
        fields = "schema" if not isinstance(review, dict) or review.get("schema") != 2 else binding_difference(review.get("binding"), binding)
        review_gap = "Review evidence binding mismatch (" + fields + "); review the current product and images."
    elif browser_gap or review.get("browser_sha256") != file_digest(browser_path):
        review_gap = "Reviewed browser evidence changed or is incomplete; repeat the observation and review."
    reviewed_files = review.get("reviewed_files", {}) if isinstance(review, dict) else {}
    if not isinstance(reviewed_files, dict):
        reviewed_files = {}
    review_checks = review.get("checks", {}) if isinstance(review, dict) and review.get("schema") == 2 else review
    required_images = ["images/" + name for name in IMAGES[case]]
    image_hashes = browser.get("observations", {}).get("image_sha256", {}) if browser_path.is_file() else {}
    for check_id, kind in suite["cases"][case].items():
        if kind == "quality":
            item = review_checks.get(check_id) if isinstance(review_checks, dict) else None
            missing = [name for name in required_images if not (trial / name).is_file() or (trial / name).stat().st_size == 0]
            if not (trial / "agent-output.md").is_file() or (trial / "agent-output.md").stat().st_size == 0:
                missing.append("agent-output.md")
            uninspected = [name for name in required_images if not item or name not in item.get("reviewed_images", [])]
            gap_reason = "Independent review, actual final output or inspected images unavailable: " + ", ".join(sorted(set(missing + uninspected)))
            artifacts = required_images + ["agent-output.md"]
            if item and isinstance(item.get("evidence"), dict) and "path" in item["evidence"]:
                artifacts.append(item["evidence"]["path"])
            drifted = []
            for name in artifacts:
                try:
                    target = trial / name
                    if (Path(name).is_absolute() or not target.resolve().is_relative_to(trial.resolve())
                            or reviewed_files.get(name) != file_digest(target)
                            or name in required_images and image_hashes.get(name) != reviewed_files.get(name)):
                        drifted.append(name)
                except (OSError, ValueError, TypeError):
                    drifted.append(str(name))
            binding_gap = review_gap or ("Reviewed files changed or lack hashes: " + ", ".join(drifted) if drifted else "")
            if binding_gap:
                gap_reason += "; " + binding_gap
            if item and item.get("status") == "fail" and "agent-output.md" not in missing:
                # A concrete review failure is still a failure when other views are absent.
                # validate() below still requires valid, nonempty failure evidence.
                checks[check_id] = {"id": check_id, "kind": kind, **{key: item[key] for key in ("status", "evidence", "reason") if key in item}}
                if missing or uninspected or binding_gap:
                    checks[check_id]["reason"] = gap_reason
            elif not item or missing or uninspected or binding_gap:
                checks[check_id] = not_run(check_id, kind, gap_reason)
            else:
                checks[check_id] = {"id": check_id, "kind": kind, **{key: item[key] for key in ("status", "evidence", "reason") if key in item}}
        elif check_id not in checks:
            checks[check_id] = not_run(check_id, kind, browser_gap or "Browser observation was not collected for this required check.")
    invocation = load_result(trial / "invocation.json")
    result = {"schema": 1, "suite": suite["id"],
              **{key: invocation[key] for key in ("run_id", "variant", "model", "settings", "skill_revision")},
              "fixture": {"id": case, "sha256": metadata["fixture_sha256"]}, "task_sha256": metadata["task_sha256"],
              "cases": [{"id": case, "checks": [checks[key] for key in suite["cases"][case]]}]}
    errors = validate(result, invocation["variant"], trial, suite)
    if errors:
        raise ValueError("Invalid collected result: " + "; ".join(errors))
    write_json(trial / "result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "collect", "review-context"))
    parser.add_argument("case", choices=CASES)
    parser.add_argument("trial", type=Path)
    args = parser.parse_args()
    try:
        operation = {"prepare": prepare, "collect": collect, "review-context": review_context}[args.operation]
        output = operation(args.case, args.trial)
        print(json.dumps(output, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("Error: " + str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
