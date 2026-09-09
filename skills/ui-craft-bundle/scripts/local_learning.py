#!/usr/bin/env python3
"""Explicit, project-local learning records and reversible rule selection.

This tool validates declared evidence. It does not launch models, independently
observe a UI, or authorize automatic learning from an agent's own claims.
"""

import argparse
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import uuid
import subprocess

sys.dont_write_bytecode = True
from learning_gate import canonical_digest, evaluate  # noqa: E402

SKILLS = {"ai-slop-remover", "ui-craft-bundle", "ui-quality-gate",
          "ui-slop-audit", "ui-visual-refine", "ux-flow-refine", "ux-writing"}
MAX_FILE = 8 * 1024 * 1024
MAX_EVIDENCE = 64 * 1024 * 1024


class LearningError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise LearningError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def identifier(prefix):
    return prefix + "-" + uuid.uuid4().hex


def valid_id(value):
    return (isinstance(value, str) and 1 <= len(value) <= 100
            and all(c in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in value))


def valid_digest(value):
    return (isinstance(value, str) and len(value) == 64
            and all(c in "0123456789abcdef" for c in value))


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON key")
        result[key] = value
    return result


def read_bytes(path):
    require(not path.is_symlink() and path.is_file(), "Expected a regular file: " + str(path))
    require(path.stat().st_size <= MAX_FILE, "File exceeds size limit")
    return path.read_bytes()


def read_json(path):
    value = json.loads(read_bytes(path).decode("utf-8"), object_pairs_hook=unique,
                       parse_constant=lambda _: (_ for _ in ()).throw(LearningError("Non-finite JSON number")))
    require(isinstance(value, dict), "Expected a JSON object: " + str(path))
    return value


def atomic_json(path, data):
    payload = (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2,
                          allow_nan=False) + "\n").encode()
    require(not path.is_symlink(), "Refusing a symlink output")
    fd, tmp = tempfile.mkstemp(prefix=".write-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(payload)
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def inventory(root, excluded=()):
    require(root.is_dir() and not root.is_symlink(), "Expected a real directory")
    files = {}
    total = 0
    for current, directories, names in os.walk(root, followlinks=False):
        for name in directories + names:
            path = Path(current) / name
            require(not path.is_symlink(), "Symlinks are not supported: " + str(path))
            require(path.is_dir() or path.is_file(), "Special files are not supported")
        for name in names:
            path = Path(current) / name
            relative = path.relative_to(root).as_posix()
            if relative in excluded or name == ".DS_Store":
                continue
            content = read_bytes(path)
            total += len(content)
            require(total <= MAX_EVIDENCE, "Snapshot exceeds size limit")
            files[relative] = sha(content)
    return dict(sorted(files.items()))


def base_digest(base):
    require(base.is_dir() and not base.is_symlink(), "Base must be a real skill-root directory")
    content = {}
    for name in sorted(SKILLS):
        path = base / name
        if path.exists() or path.is_symlink():
            require((path / "SKILL.md").is_file(), "Base skill lacks SKILL.md")
            for relative, digest in inventory(path).items():
                content[name + "/" + relative] = digest
    require("ui-craft-bundle/SKILL.md" in content, "Base requires ui-craft-bundle")
    result = hashlib.sha256()
    for relative in sorted(content):
        result.update(relative.encode() + b"\0" + read_bytes(base / relative) + b"\0")
    return result.hexdigest()


def project_path(value):
    project = Path(value).expanduser().resolve(strict=True)
    require(project.is_dir(), "Project must be an existing directory")
    require(not (project / ".lutriva").is_symlink(), "Local state parent cannot be a symlink")
    require(not (project / ".lutriva/local").is_symlink(), "Local state cannot be a symlink")
    return project


@contextmanager
def locked(root):
    path = root / ".lock"
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise LearningError("Local store is locked. Verify the owner stopped before removing a stale .lock.")
    try:
        with os.fdopen(fd, "w") as out:
            json.dump({"pid": os.getpid()}, out)
            out.flush()
            os.fsync(out.fileno())
        yield
    finally:
        path.unlink()


def state_root(project):
    root = project / ".lutriva/local"
    require(root.is_dir() and not root.is_symlink(), "Initialize this project's local store first")
    for name in ("candidates", "evaluations", "releases", "journal"):
        require((root / name).is_dir() and not (root / name).is_symlink(), "Invalid store directory")
    return root


def record_dir(root, category, name):
    require(valid_id(name), "Invalid record ID")
    path = root / category / name
    require(path.is_dir() and not path.is_symlink(), "Record is unavailable")
    return path


def policy_of(root):
    policy = read_json(root / "policy.json")
    require(set(policy) == {"schema", "project_id", "base", "mode", "max_runs",
                            "max_seconds", "max_rule_bytes", "max_rule_count"}, "Invalid policy fields")
    require(type(policy["schema"]) is int and policy["schema"] == 1 and policy["mode"] == "propose", "Only explicit manual adoption is implemented")
    require(valid_id(policy["project_id"]), "Invalid project identity")
    for field in ("max_runs", "max_rule_bytes", "max_rule_count"):
        require(type(policy[field]) is int and policy[field] > 0, "Invalid policy limit")
    require(type(policy["max_seconds"]) in (int, float)
            and math.isfinite(policy["max_seconds"]) and policy["max_seconds"] > 0, "Invalid time limit")
    require(isinstance(policy["base"], str) and Path(policy["base"]).is_absolute(), "Invalid base location")
    base = Path(policy["base"]).resolve(strict=True)
    require(not root.resolve().is_relative_to(base), "Local learning store cannot be inside the installed skill base")
    return policy


def pointer_shape(active, policy):
    require(isinstance(active, dict) and set(active) == {"schema", "project_id", "generation", "state", "base_sha256",
                            "release_id", "release_sha256", "previous_release_id", "journal_id"}, "Invalid active pointer")
    require(type(active["schema"]) is int and active["schema"] == 1
            and active["project_id"] == policy["project_id"], "Active project mismatch")
    require(type(active["generation"]) is int and active["generation"] >= 0, "Invalid generation")
    require(active["state"] in ("active", "suspended", "base-only"), "Invalid active state")
    for field in ("base_sha256", "release_sha256"):
        value = active[field]
        require((field == "release_sha256" and value is None) or (
            isinstance(value, str) and len(value) == 64
            and all(c in "0123456789abcdef" for c in value)), "Invalid pointer digest")
    for field in ("release_id", "previous_release_id", "journal_id"):
        require(active[field] is None or valid_id(active[field]), "Invalid pointer record ID")
    if active["state"] == "base-only":
        require(active["release_id"] is None and active["release_sha256"] is None, "Base-only pointer has a release")
    else:
        require(active["release_id"] is not None and active["release_sha256"] is not None, "Active pointer lacks a release")
    if active["generation"] == 0:
        require(active["state"] == "base-only" and active["journal_id"] is None
                and active["previous_release_id"] is None, "Invalid initial pointer")
    else:
        require(active["journal_id"] is not None, "Generation lacks a transition journal")


def verify_history(root, policy, active):
    """Require the pointer to be the newest snapshot of one continuous journal.

    Interrupted prepared transitions deliberately stop reads and mutations. The
    error identifies whether the durable pointer is old/new; this command does
    not guess or silently erase history to recover an ambiguous store.
    """
    journals = []
    for path in (root / "journal").iterdir():
        require(path.suffix == ".json" and valid_id(path.stem), "Unexpected transition journal file")
        journal = read_json(path)
        require(set(journal) == {"schema", "phase", "reason", "old", "new"}, "Invalid journal fields")
        require(type(journal["schema"]) is int and journal["schema"] == 1
                and journal["phase"] in ("prepared", "committed")
                and journal["reason"] in ("manual-adoption", "explicit-rollback"), "Invalid transition journal")
        pointer_shape(journal["old"], policy)
        pointer_shape(journal["new"], policy)
        require(journal["new"]["journal_id"] == path.stem, "Journal ID mismatch")
        require(journal["new"]["generation"] == journal["old"]["generation"] + 1
                and journal["new"]["previous_release_id"] == journal["old"]["release_id"], "Invalid journal transition")
        journals.append(journal)
    journals.sort(key=lambda entry: entry["new"]["generation"])
    if not journals:
        require(active["generation"] == 0, "Active generation has no transition history")
        return
    expected = journals[0]["old"]
    require(expected["generation"] == 0, "Transition history does not start at generation zero")
    for index, journal in enumerate(journals):
        require(journal["old"] == expected and journal["new"]["generation"] == index + 1,
                "Transition history is discontinuous or contains a conflicting generation")
        if journal["phase"] == "prepared":
            require(index == len(journals) - 1, "Unresolved prepared transition precedes newer history")
            side = "old" if active == journal["old"] else "new" if active == journal["new"] else None
            require(side is not None, "Active pointer matches neither prepared transition snapshot")
            raise LearningError("Prepared transition requires recovery; active pointer matches the " + side
                                + " snapshot. Local rules and further transitions are withheld.")
        expected = journal["new"]
    require(active == expected, "Active pointer is stale or differs from the newest committed journal")


def active_of(root, policy, verify_release=True):
    active = read_json(root / "active.json")
    pointer_shape(active, policy)
    verify_history(root, policy, active)
    if verify_release and active["state"] != "base-only":
        release_of(root, active["release_id"], expected_sha256=active["release_sha256"])
    return active


def release_of(root, name, expected_sha256=None):
    path = record_dir(root, "releases", name)
    record = read_json(path / "manifest.json")
    if expected_sha256 is not None:
        require(canonical_digest(record) == expected_sha256, "Release changed since activation")
    require(set(record) == {"schema", "release_id", "project_id", "base_sha256", "parent_release_id",
                            "evaluation_id", "evaluation_sha256", "rules", "rules_sha256"}, "Invalid release fields")
    require(type(record["schema"]) is int and record["schema"] == 1, "Invalid release schema")
    require(record.get("release_id") == name, "Release ID mismatch")
    require(sha(read_bytes(path / "rules.md")) == record.get("rules_sha256"), "Release rules changed")
    require(render_rules(record.get("rules", [])) == read_bytes(path / "rules.md"), "Release rule metadata changed")
    require(valid_digest(record["evaluation_sha256"]), "Invalid release evaluation digest")
    _, candidate, plan = evaluation_of(root, record["evaluation_id"], record["evaluation_sha256"])
    require(record["project_id"] == candidate["project_id"]
            and record["base_sha256"] == plan["base_sha256"]
            and record["parent_release_id"] == plan["parent_release"]
            and record["rules"] == candidate["rules"]
            and record["rules_sha256"] == plan["candidate_sha256"], "Release differs from evaluated candidate")
    return record


def render_rules(rules):
    require(isinstance(rules, list), "Rules must be a list")
    parts = []
    for rule in rules:
        require(isinstance(rule, dict) and set(rule) == {"id", "scope", "text", "sha256"}, "Invalid rule fields")
        require(valid_id(rule["id"]) and isinstance(rule["text"], str), "Invalid rule")
        validate_scope(rule["scope"])
        require(sha(rule["text"].encode()) == rule["sha256"], "Rule content changed")
        parts.append("## " + rule["id"] + "\n\nScope: " + json.dumps(rule["scope"], sort_keys=True, ensure_ascii=False)
                     + "\n\n" + rule["text"].rstrip() + "\n")
    require(len({r["id"] for r in rules}) == len(rules), "Duplicate rule IDs")
    return "\n".join(parts).encode()


def validate_scope(scope):
    require(isinstance(scope, dict) and set(scope) == {"skill_ids", "platforms", "task_kinds"}, "Invalid scope")
    for field, values in scope.items():
        require(isinstance(values, list) and values and all(valid_id(v) for v in values)
                and len(values) == len(set(values)), "Scope needs unique explicit values")
    require(set(scope["skill_ids"]) <= SKILLS, "Unknown scope skill")


def candidate_of(root, name):
    path = record_dir(root, "candidates", name)
    candidate = read_json(path / "candidate.json")
    plan = read_json(path / "plan.json")
    require(set(candidate) == {"schema", "candidate_id", "project_id", "rules", "plan_sha256"}, "Invalid candidate fields")
    require(type(candidate["schema"]) is int and candidate["schema"] == 1, "Invalid candidate schema")
    require(candidate.get("candidate_id") == name, "Candidate ID mismatch")
    require(canonical_digest(plan) == candidate.get("plan_sha256"), "Candidate plan changed")
    require(render_rules(candidate["rules"]) == read_bytes(path / "rules.md"), "Candidate rule metadata changed")
    require(sha(read_bytes(path / "rules.md")) == plan["candidate_sha256"], "Candidate rules changed")
    return candidate, plan


def current_rules(root, active, digest):
    if active["state"] != "active" or active["base_sha256"] != digest:
        return []
    release = release_of(root, active["release_id"])
    require(release["base_sha256"] == digest, "Release base mismatch")
    return release["rules"]


def transition(root, policy, old, release_id, digest, reason):
    release = release_of(root, release_id) if release_id else None
    if release:
        require(release["base_sha256"] == digest and release["project_id"] == policy["project_id"], "Release is incompatible")
    jid = identifier("j")
    new = {"schema": 1, "project_id": policy["project_id"], "generation": old["generation"] + 1,
           "state": "active" if release else "base-only", "base_sha256": digest,
           "release_id": release_id, "release_sha256": canonical_digest(release) if release else None,
           "previous_release_id": old["release_id"], "journal_id": jid}
    journal = {"schema": 1, "phase": "prepared", "reason": reason, "old": old, "new": new}
    atomic_json(root / "journal" / (jid + ".json"), journal)
    atomic_json(root / "active.json", new)
    journal["phase"] = "committed"
    atomic_json(root / "journal" / (jid + ".json"), journal)
    return new


def init(args, project):
    root = project / ".lutriva/local"
    require(not root.exists(), "Local store already exists; no files changed")
    base = Path(args.base).expanduser().resolve(strict=True)
    require(not project.is_relative_to(base), "Project-local learning cannot be initialized inside the installed skill base")
    digest = base_digest(base)
    require(args.max_runs > 0 and args.max_seconds > 0, "Positive budgets are required")
    require(math.isfinite(args.max_seconds), "Time budget must be finite")
    try:
        # A missing Git executable or a normal nonrepository directory is valid.
        # Failure to read an existing repository's index is not evidence that the
        # learning path is untracked. Use a fixed diagnostic locale to distinguish
        # Git's explicit nonrepository result from configuration/access failures.
        git_environment = dict(os.environ, LC_ALL="C", LANG="C")
        probe = subprocess.run(["git", "-C", str(project), "rev-parse", "--is-inside-work-tree"],
                               capture_output=True, timeout=10, check=False, env=git_environment)
        if probe.returncode != 0:
            markers = any((parent / ".git").exists() or (parent / ".git").is_symlink()
                          for parent in (project, *project.parents))
            require(probe.stderr.startswith(b"fatal: not a git repository") and not markers
                    and not git_environment.get("GIT_DIR") and not git_environment.get("GIT_WORK_TREE"),
                    "Cannot verify Git repository state; local recording was not initialized")
        else:
            require(probe.stdout.strip() == b"true", "Project must be outside Git metadata and bare repositories")
            tracked = subprocess.run(["git", "-C", str(project), "ls-files", "-z", "--", ".lutriva/local"],
                                     capture_output=True, timeout=10, check=False, env=git_environment)
            require(tracked.returncode == 0, "Cannot verify tracked local paths; Git index check failed")
            require(not tracked.stdout, "Local learning path is already tracked by Git; choose a separate project location")
    except FileNotFoundError:
        pass  # Git is optional; no network or global configuration is involved.
    parent = root.parent
    parent.mkdir(exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".local-init-", dir=str(parent)))
    try:
        for name in ("candidates", "evaluations", "releases", "journal"):
            (staging / name).mkdir()
        policy = {"schema": 1, "project_id": identifier("p"), "base": str(base), "mode": "propose",
                  "max_runs": args.max_runs, "max_seconds": args.max_seconds,
                  "max_rule_bytes": 8000, "max_rule_count": 12}
        atomic_json(staging / "policy.json", policy)
        atomic_json(staging / "active.json", {"schema": 1, "project_id": policy["project_id"],
                    "generation": 0, "state": "base-only", "base_sha256": digest, "release_id": None,
                    "release_sha256": None, "previous_release_id": None, "journal_id": None})
        # The local ignore file prevents ordinary Git adds without modifying
        # shared repository policy. Existing tracked/synced locations need owner review.
        (staging / ".gitignore").write_text("*\n", encoding="utf-8")
        require(not root.exists(), "Concurrent initialization detected")
        os.rename(staging, root)
    finally:
        if staging.exists():
            import shutil
            shutil.rmtree(staging)
    return {"state": "base-only", "project_id": policy["project_id"], "store": str(root),
            "mode": "propose", "automatic_execution": False}


def propose(args, root, policy, active, digest):
    spec = read_json(Path(args.spec).expanduser().resolve(strict=True))
    required = {"scope", "profile", "target_pairs", "transfer_pairs", "transfer_contexts", "required_checks", "improvement_checks", "context"}
    require(set(spec) in (required, required | {"replaces"}), "Invalid proposal specification fields")
    require(spec["profile"] == "reviewed-local", "An enforced execution adapter is not implemented")
    validate_scope(spec["scope"])
    text = read_bytes(Path(args.rules).expanduser().resolve(strict=True)).decode("utf-8").strip()
    require(text, "Rule text cannot be empty")
    rules = current_rules(root, active, digest)
    replaces = spec.get("replaces", [])
    require(isinstance(replaces, list) and all(valid_id(v) for v in replaces), "Invalid replacement IDs")
    require(set(replaces) <= {r["id"] for r in rules}, "Replacement refers to an inactive rule")
    cid = identifier("c")
    rules = [r for r in rules if r["id"] not in replaces] + [{"id": cid, "scope": spec["scope"], "text": text, "sha256": sha(text.encode())}]
    payload = render_rules(rules)
    require(len(rules) <= policy["max_rule_count"] and len(payload) <= policy["max_rule_bytes"], "Active rule budget exceeded")
    plan = {"schema": 1, "candidate_sha256": sha(payload), "base_sha256": digest,
            "parent_release": active["release_id"], "expected_generation": active["generation"],
            "policy_sha256": canonical_digest(policy), "profile": spec["profile"],
            "budget": {"max_runs": policy["max_runs"], "max_seconds": policy["max_seconds"]}}
    for key in ("target_pairs", "transfer_pairs", "transfer_contexts", "required_checks", "improvement_checks", "context"):
        plan[key] = spec[key]
    # The evaluator validates the complete plan even before evidence exists.
    probe = evaluate(plan, {}, root)
    plan_errors = [e for e in probe.get("errors", []) + probe.get("missing", []) if str(e).startswith("plan")]
    require(not plan_errors, "Invalid plan: " + "; ".join(plan_errors))
    required_runs = 2 * (len(plan["target_pairs"]) + len(plan["transfer_pairs"]))
    require(required_runs <= policy["max_runs"],
            "Plan requires " + str(required_runs) + " runs, but max_runs allows " + str(policy["max_runs"]))
    path = root / "candidates" / cid
    path.mkdir()
    (path / "rules.md").write_bytes(payload)
    atomic_json(path / "plan.json", plan)
    candidate = {"schema": 1, "candidate_id": cid, "project_id": policy["project_id"],
                 "rules": rules, "plan_sha256": canonical_digest(plan)}
    atomic_json(path / "candidate.json", candidate)
    return {"candidate_id": cid, "plan": plan, "plan_sha256": canonical_digest(plan), "path": str(path)}


def evaluate_candidate(args, root, policy, active, digest):
    candidate, plan = candidate_of(root, args.candidate)
    require(candidate["project_id"] == policy["project_id"], "Candidate project mismatch")
    report = read_json(Path(args.report).expanduser().resolve(strict=True))
    source = Path(args.evidence).expanduser()
    require(not source.is_symlink(), "Evidence root cannot be a symlink")
    source = source.resolve(strict=True)
    require(not root.is_relative_to(source) and not source.is_relative_to(root),
            "Import evidence from outside the local learning store")
    before = inventory(source)
    require(before, "Evidence directory is empty")
    eid = identifier("e")
    path = root / "evaluations" / eid
    path.mkdir()
    dest = path / "evidence"
    dest.mkdir()
    for name in before:
        out = dest / name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(read_bytes(source / name))
    require(inventory(dest) == before and inventory(source) == before, "Evidence changed during snapshot")
    decision = evaluate(plan, report, dest)
    atomic_json(path / "report.json", report)
    atomic_json(path / "decision.json", decision)
    meta = {"schema": 1, "evaluation_id": eid, "candidate_id": args.candidate,
            "candidate_record_sha256": canonical_digest(candidate), "plan_sha256": canonical_digest(plan),
            "files": inventory(path)}
    atomic_json(path / "record.json", meta)
    return {"evaluation_id": eid, "decision": decision, "path": str(path)}


def evaluation_of(root, name, expected_sha256=None):
    """Verify immutable evaluation records without requiring the current policy or generation."""
    path = record_dir(root, "evaluations", name)
    meta = read_json(path / "record.json")
    if expected_sha256 is not None:
        require(canonical_digest(meta) == expected_sha256, "Release evaluation changed")
    require(set(meta) == {"schema", "evaluation_id", "candidate_id", "candidate_record_sha256",
                          "plan_sha256", "files"}, "Invalid evaluation record fields")
    require(type(meta["schema"]) is int and meta["schema"] == 1, "Invalid evaluation record schema")
    require(valid_id(meta["evaluation_id"]) and meta["evaluation_id"] == name,
            "Evaluation record ID does not match its directory")
    require(valid_id(meta["candidate_id"]), "Invalid evaluation candidate ID")
    require(valid_digest(meta["candidate_record_sha256"]) and valid_digest(meta["plan_sha256"]),
            "Invalid evaluation record digest")
    require(isinstance(meta["files"], dict) and meta["files"]
            and all(isinstance(name, str) and name and valid_digest(value)
                    for name, value in meta["files"].items()), "Invalid evaluation file digest map")
    require(meta["files"] == inventory(path, excluded=("record.json",)), "Evaluation evidence changed")
    candidate, plan = candidate_of(root, meta["candidate_id"])
    require(meta["candidate_record_sha256"] == canonical_digest(candidate)
            and meta["plan_sha256"] == canonical_digest(plan), "Evaluated candidate changed")
    return meta, candidate, plan


def promote(args, root, policy, active, digest):
    meta, candidate, plan = evaluation_of(root, args.evaluation)
    require(candidate["project_id"] == policy["project_id"], "Project mismatch")
    require(plan["base_sha256"] == digest and plan["policy_sha256"] == canonical_digest(policy), "Base or policy changed; evaluate a new candidate")
    require(plan["expected_generation"] == active["generation"] and plan["parent_release"] == active["release_id"], "Stale candidate parent or generation")
    path = record_dir(root, "evaluations", args.evaluation)
    decision = evaluate(plan, read_json(path / "report.json"), path / "evidence")
    require(decision == read_json(path / "decision.json"), "Evaluation decision changed")
    require(decision["verdict"] == "eligible" and "manual" in decision["eligible_for"], "Only manually eligible candidates can be promoted")
    rid = identifier("r")
    release_path = root / "releases" / rid
    release_path.mkdir()
    payload = render_rules(candidate["rules"])
    (release_path / "rules.md").write_bytes(payload)
    release = {"schema": 1, "release_id": rid, "project_id": policy["project_id"], "base_sha256": digest,
               "parent_release_id": active["release_id"], "evaluation_id": args.evaluation,
               "evaluation_sha256": canonical_digest(meta), "rules": candidate["rules"], "rules_sha256": sha(payload)}
    atomic_json(release_path / "manifest.json", release)
    state = transition(root, policy, active, rid, digest, "manual-adoption")
    return dict(state, adopted=True, evidence_level=decision.get("evidence_level", "declared-records"))


def rollback(args, root, policy, active, digest):
    if args.base_only:
        return transition(root, policy, active, None, digest, "explicit-rollback")
    rid = args.release or active["previous_release_id"]
    if rid:
        try:
            recorded = {entry["new"]["release_sha256"]
                        for entry in (read_json(path) for path in (root / "journal").glob("*.json"))
                        if entry["new"]["release_id"] == rid}
            require(len(recorded) == 1, "Rollback release changed since activation")
            release = release_of(root, rid, expected_sha256=next(iter(recorded)))
            require(release["base_sha256"] == digest and release["project_id"] == policy["project_id"],
                    "Requested rollback release is incompatible")
        except (LearningError, OSError, ValueError, KeyError, TypeError):
            if args.release is not None:
                raise
            rid = None  # A damaged previous release cannot prevent return to the common base.
    return transition(root, policy, active, rid, digest, "explicit-rollback")


def read_status(args, root, policy, active, digest):
    state = dict(active)
    if active["base_sha256"] != digest:
        state["state"] = "suspended" if active["release_id"] else "base-only"
    state["current_base_sha256"] = digest
    state["mode"] = policy["mode"]
    state["automatic_execution"] = False
    state["locked"] = (root / ".lock").exists()
    return state


def context(args, root, policy, active, digest):
    result = read_status(args, root, policy, active, digest)
    rules = current_rules(root, active, digest)
    if args.candidate:
        candidate, plan = candidate_of(root, args.candidate)
        require(candidate["project_id"] == policy["project_id"] and plan["base_sha256"] == digest
                and plan["policy_sha256"] == canonical_digest(policy), "Candidate context is incompatible")
        require(plan["expected_generation"] == active["generation"]
                and plan["parent_release"] == active["release_id"], "Stale candidate parent or generation")
        rules = candidate["rules"]
        result["candidate_id"] = args.candidate
        result["candidate_sha256"] = plan["candidate_sha256"]
    selected = [r for r in rules if args.skill in r["scope"]["skill_ids"]
                and args.platform in r["scope"]["platforms"] and args.task_kind in r["scope"]["task_kinds"]]
    result["rules"] = selected
    result["selected_rules_sha256"] = canonical_digest(selected)
    result["delivery"] = "explicit-context-only; pass these scoped notes with the task; no host injection"
    return result


def parser():
    class JsonParser(argparse.ArgumentParser):
        def error(self, message):
            print(json.dumps({"error": message}), file=sys.stderr)
            raise SystemExit(2)
    command = JsonParser(description=__doc__)
    sub = command.add_subparsers(dest="operation", required=True)
    for name in ("init", "propose", "evaluate", "promote", "rollback", "status", "context"):
        item = sub.add_parser(name)
        item.add_argument("--project", required=True)
        if name == "init":
            item.add_argument("--base", default=str(Path(__file__).resolve().parents[2]))
            item.add_argument("--max-runs", type=int, default=6)
            item.add_argument("--max-seconds", type=float, default=1200)
        elif name == "propose":
            item.add_argument("--rules", required=True)
            item.add_argument("--spec", required=True)
        elif name == "evaluate":
            item.add_argument("--candidate", required=True)
            item.add_argument("--report", required=True)
            item.add_argument("--evidence", required=True)
        elif name == "promote":
            item.add_argument("--evaluation", required=True)
        elif name == "rollback":
            target = item.add_mutually_exclusive_group()
            target.add_argument("--release", help="Restore a specific compatible release")
            target.add_argument("--base-only", action="store_true", help="Disable all local rules and invalidate older candidates without deleting history")
        elif name == "context":
            item.add_argument("--skill", choices=sorted(SKILLS), required=True)
            item.add_argument("--platform", required=True)
            item.add_argument("--task-kind", required=True)
            item.add_argument("--candidate")
    return command


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        project = project_path(args.project)
        if args.operation == "init":
            result = init(args, project)
        else:
            root = state_root(project)
            def invoke():
                policy = policy_of(root)
                active = active_of(root, policy, verify_release=args.operation != "rollback")
                digest = base_digest(Path(policy["base"]))
                action = {"propose": propose, "evaluate": evaluate_candidate, "promote": promote,
                          "rollback": rollback, "status": read_status, "context": context}[args.operation]
                return action(args, root, policy, active, digest)
            if args.operation in ("status", "context"):
                result = invoke()
            else:
                with locked(root):
                    result = invoke()
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))
        verdict = result.get("decision", {}).get("verdict")
        return 1 if verdict == "rejected" else 3 if verdict == "incomplete" else 0
    except (LearningError, OSError, ValueError, KeyError, TypeError, AttributeError,
            OverflowError, RecursionError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
