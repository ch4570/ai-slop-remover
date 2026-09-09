"""Validate frozen local-learning records; never run a model or activate rules.

The gate verifies record consistency and reads bounded local evidence files. It
cannot authenticate a reviewer or infer that an asserted observation occurred.
Its eligibility is conditional on the independent review recorded in the input.
"""

import hashlib
import json
import math
import os
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
import re
import stat
import unicodedata


PLAN_FIELDS = {
    "schema", "candidate_sha256", "base_sha256", "parent_release",
    "expected_generation", "policy_sha256", "profile", "target_pairs",
    "transfer_pairs", "required_checks", "improvement_checks", "context", "transfer_contexts", "budget",
}
CONTEXT_FIELDS = {"task_sha256", "fixture_sha256", "model", "settings", "tools_sha256"}
REPORT_FIELDS = {"schema", "plan_sha256", "candidate_sha256", "pairs", "review"}
REVIEW_FIELDS = {"independent", "evidence", "reproduced", "evaluator_isolated", "holdout_unseen"}
PAIR_FIELDS = {"pair_id", "kind", "context", "baseline", "candidate"}
RUN_FIELDS = {"run_id", "checks", "duration_seconds"}
CHECK_FIELDS = {"id", "status", "evidence", "reason"}
MAX_PAIRS = 130
MAX_CHECKS = 256
MAX_EVIDENCE_BYTES = 32 * 1024 * 1024
MAX_TOTAL_EVIDENCE_BYTES = 256 * 1024 * 1024
LIMITATION = (
    "Declared records only: hashes and schema validation do not authenticate "
    "observations, reviewer independence, reproduction, isolation or unseen "
    "holdouts. A separate reviewer must inspect the evidence; this function "
    "does not execute evaluations or authorize activation."
)
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_PLACEHOLDERS = {"", "pass", "fail", "ok", "todo", "tbd", "pending", "placeholder", "looks good"}


def canonical_digest(value):
    """SHA-256 of UTF-8 canonical JSON; reject non-JSON floats such as NaN."""
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")).hexdigest()


def _digest(value):
    return isinstance(value, str) and bool(_SHA256.fullmatch(value)) and len(set(value)) > 1


def _text(value, limit=4096):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        return False
    lowered = value.strip().lower()
    return lowered not in _PLACEHOLDERS and not lowered.startswith(("todo:", "tbd:", "placeholder:"))


def _number(value):
    if type(value) not in (int, float) or value < 0:
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


class _Audit:
    def __init__(self, evidence_root):
        self.errors = []
        self.missing = []
        self.regressions = []
        self.improvements = []
        self.rejections = []
        self._errors_seen = set()
        self._missing_seen = set()
        self._rejections_seen = set()
        self.evidence = {}
        self.path_spellings = {}
        self.evidence_bytes = 0
        self.root = Path(evidence_root)

    def error(self, message, reject=False):
        if message not in self._errors_seen:
            self._errors_seen.add(message)
            self.errors.append(message)
        if reject and message not in self._rejections_seen:
            self._rejections_seen.add(message)
            self.rejections.append(message)

    def absent(self, message):
        if message not in self._missing_seen:
            self._missing_seen.add(message)
            self.missing.append(message)

    def fields(self, value, expected, label, optional=()):
        if not isinstance(value, dict):
            self.error(label + " must be an object")
            return False
        for key in sorted(expected - set(value)):
            self.absent(label + "." + key)
        unknown = set(value) - expected - set(optional)
        if unknown:
            self.error(label + " has unknown fields: " + ", ".join(sorted(map(str, unknown))))
        return True

    def ids(self, value, label, minimum=1, maximum=MAX_CHECKS):
        if not isinstance(value, list):
            self.error(label + " must be a list")
            return []
        if not minimum <= len(value) <= maximum:
            self.error(label + " must contain " + str(minimum) + ".." + str(maximum) + " IDs")
        valid = []
        seen = set()
        for item in value[:maximum]:
            if not isinstance(item, str) or not _ID.fullmatch(item):
                self.error(label + " contains an invalid ID")
            elif item.casefold() in seen:
                self.error(label + " contains duplicate/case-colliding ID: " + item)
            else:
                valid.append(item)
                seen.add(item.casefold())
        return valid

    def context(self, value, label):
        before = len(self.errors) + len(self.missing)
        if not self.fields(value, CONTEXT_FIELDS, label):
            return False
        for field in ("task_sha256", "fixture_sha256", "tools_sha256"):
            if field in value and not _digest(value[field]):
                self.error(label + "." + field + " must be a non-placeholder SHA-256")
        if "model" in value and not _text(value["model"], 256):
            self.error(label + ".model must identify the comparison model")
        if "settings" in value:
            if not isinstance(value["settings"], dict):
                self.error(label + ".settings must be an object")
            else:
                try:
                    canonical_digest(value["settings"])
                except (ValueError, TypeError, UnicodeError, RecursionError):
                    self.error(label + ".settings must contain finite JSON values")
        return len(self.errors) + len(self.missing) == before

    def file(self, relative, label):
        """Read only regular files beneath root, using no-follow descriptor walks."""
        if not isinstance(relative, str) or not relative or len(relative) > 1024:
            self.absent(label + " needs an evidence file path")
            return False
        parts = relative.split("/")
        if (relative.startswith("/") or "\\" in relative or ":" in relative
                or any(p in ("", ".", "..") or p.rstrip(" .") != p for p in parts)
                or any(ord(c) < 32 or ord(c) == 127 for c in relative)
                or unicodedata.normalize("NFC", relative) != relative):
            self.error(label + " has an unsafe/non-canonical evidence path", reject=True)
            return False
        for end in range(1, len(parts) + 1):
            prefix = "/".join(parts[:end])
            folded = prefix.casefold()
            if folded in self.path_spellings and self.path_spellings[folded] != prefix:
                self.error(label + " has a case-colliding evidence path", reject=True)
                return False
            self.path_spellings[folded] = prefix
        if relative in self.evidence:
            return True
        opened = []
        try:
            # O_NOFOLLOW is required: silently falling back would weaken the contract.
            if not hasattr(os, "O_NOFOLLOW") or os.open not in os.supports_dir_fd:
                self.absent("platform lacks no-follow evidence path support")
                return False
            flags = os.O_RDONLY | os.O_NOFOLLOW
            directory = os.open(str(self.root), flags | os.O_DIRECTORY)
            opened.append(directory)
            for part in parts[:-1]:
                directory = os.open(part, flags | os.O_DIRECTORY, dir_fd=directory)
                opened.append(directory)
            descriptor = os.open(parts[-1], flags | os.O_NONBLOCK, dir_fd=directory)
            opened.append(descriptor)
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode):
                self.error(label + " evidence must be a regular file", reject=True)
                return False
            if before.st_size <= 0:
                self.absent(label + " evidence is empty")
                return False
            if before.st_size > MAX_EVIDENCE_BYTES:
                self.absent(label + " exceeds evidence size limit")
                return False
            if self.evidence_bytes + before.st_size > MAX_TOTAL_EVIDENCE_BYTES:
                self.absent("total evidence exceeds size limit")
                return False
            hasher = hashlib.sha256()
            prefix = b""
            count = 0
            while True:
                chunk = os.read(descriptor, 65536)
                if not chunk:
                    break
                count += len(chunk)
                if count > MAX_EVIDENCE_BYTES:
                    self.absent(label + " exceeds evidence size limit")
                    return False
                hasher.update(chunk)
                if len(prefix) < 4096:
                    prefix += chunk[:4096 - len(prefix)]
            after = os.fstat(descriptor)
            if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                    after.st_size, after.st_mtime_ns, after.st_ctime_ns) or count != before.st_size:
                self.error(label + " evidence changed while reading", reject=True)
                return False
            if count <= 4096:
                try:
                    if not _text(prefix.decode("utf-8"), 4096):
                        self.absent(label + " evidence contains only a placeholder")
                        return False
                except UnicodeError:
                    pass  # Binary evidence still needs the independent review below.
            self.evidence_bytes += count
            self.evidence[relative] = hasher.hexdigest()
            return True
        except FileNotFoundError:
            self.absent(label + " evidence file is missing: " + relative)
        except (OSError, ValueError) as exc:
            self.error(label + " evidence cannot be read safely: " + str(exc), reject=True)
        finally:
            for descriptor in reversed(opened):
                os.close(descriptor)
        return False

    def result(self, verdict, reason, eligible_for=()):
        return {
            "schema": 1,
            "verdict": verdict,
            "eligible_for": list(eligible_for) if verdict == "eligible" else [],
            "improvements": self.improvements,
            "regressions": self.regressions,
            "missing": self.missing,
            "errors": self.errors,
            "reason": reason,
            "evidence_level": "declared-records",
            "limitation": LIMITATION,
            "evidence_sha256": dict(sorted(self.evidence.items())),
        }


def evaluate(plan, report, evidence_root):
    """Return a deterministic, fail-closed decision without mutating any files.

    The caller must bind plan candidate/base/policy digests to actual snapshots,
    reject duplicate JSON keys while decoding and enforce activation permissions.
    Malformed/missing data is incomplete; binding violations or candidate failures
    are rejected even when other required records are missing.
    """
    audit = _Audit(evidence_root)
    if not audit.fields(plan, PLAN_FIELDS, "plan"):
        plan = {}
    if not audit.fields(report, REPORT_FIELDS, "report"):
        report = {}
    for label, record in (("plan", plan), ("report", report)):
        if "schema" in record and (type(record["schema"]) is not int or record["schema"] != 1):
            audit.error(label + ".schema must be integer 1")
    for field in ("candidate_sha256", "base_sha256", "policy_sha256"):
        if field in plan and not _digest(plan[field]):
            audit.error("plan." + field + " must be a non-placeholder SHA-256")
    parent = plan.get("parent_release")
    if parent is not None and (not isinstance(parent, str) or not _ID.fullmatch(parent)):
        audit.error("plan.parent_release must be a release ID or null")
    generation = plan.get("expected_generation")
    if "expected_generation" in plan and (type(generation) is not int or generation < 0):
        audit.error("plan.expected_generation must be a nonnegative integer")
    profile = plan.get("profile")
    if profile not in ("enforced", "reviewed-local"):
        audit.error("plan.profile must be enforced or reviewed-local")
    targets = audit.ids(plan.get("target_pairs"), "plan.target_pairs", 2, 2)
    transfers = audit.ids(plan.get("transfer_pairs"), "plan.transfer_pairs", 1, MAX_PAIRS - 2)
    if set(t.casefold() for t in targets) & set(t.casefold() for t in transfers):
        audit.error("plan target and transfer pair IDs must be distinct")
    required = audit.ids(plan.get("required_checks"), "plan.required_checks")
    improvement_checks = audit.ids(plan.get("improvement_checks"), "plan.improvement_checks")
    if not set(improvement_checks).issubset(required):
        audit.error("plan.improvement_checks must be a subset of required_checks")
    target_context_valid = audit.context(plan.get("context"), "plan.context")
    transfer_contexts = plan.get("transfer_contexts")
    if not audit.fields(transfer_contexts, set(transfers), "plan.transfer_contexts"):
        transfer_contexts = {}
    valid_transfer_contexts = {}
    for pair_id in transfers:
        transfer_context = transfer_contexts.get(pair_id)
        valid = audit.context(transfer_context, "plan.transfer_contexts." + pair_id)
        valid_transfer_contexts[pair_id] = valid
        if valid and target_context_valid:
            if transfer_context["fixture_sha256"] == plan["context"]["fixture_sha256"]:
                audit.error("plan.transfer_contexts." + pair_id + " must use a different fixture from targets")
            for field in ("model", "settings", "tools_sha256"):
                if canonical_digest(transfer_context[field]) != canonical_digest(plan["context"][field]):
                    audit.error("plan.transfer_contexts." + pair_id + "." + field + " must match target comparison settings")
    budget = plan.get("budget")
    if not audit.fields(budget, {"max_runs", "max_seconds"}, "plan.budget"):
        budget = {}
    max_runs = budget.get("max_runs")
    max_seconds = budget.get("max_seconds")
    if type(max_runs) is not int or max_runs < 1:
        audit.error("plan.budget.max_runs must be a positive integer")
        max_runs = None
    if not _number(max_seconds) or max_seconds == 0:
        audit.error("plan.budget.max_seconds must be a finite positive number")
        max_seconds = None
    for field in ("plan_sha256", "candidate_sha256"):
        if field in report and not _digest(report[field]):
            audit.error("report." + field + " must be a non-placeholder SHA-256")
    try:
        plan_hash = canonical_digest(plan)
    except (TypeError, ValueError, UnicodeError, RecursionError):
        audit.error("plan must contain finite JSON values")
        plan_hash = None
    if "plan_sha256" in report and plan_hash is not None and report["plan_sha256"] != plan_hash:
        audit.error("report.plan_sha256 does not match frozen plan", reject=True)
    if ("candidate_sha256" in report and "candidate_sha256" in plan
            and report["candidate_sha256"] != plan["candidate_sha256"]):
        audit.error("report.candidate_sha256 does not match frozen candidate", reject=True)

    expected_pairs = {pair: "target" for pair in targets}
    expected_pairs.update({pair: "transfer" for pair in transfers})
    pairs = report.get("pairs")
    if not isinstance(pairs, list):
        audit.error("report.pairs must be a list")
        pairs = []
    if len(pairs) > MAX_PAIRS:
        audit.error("report.pairs exceeds supported bound", reject=True)
    seen_pairs = set()
    seen_runs = set()
    runs_used = 0
    seconds_used = Fraction(0)
    improvements_by_target = {}
    for position, pair in enumerate(pairs[:MAX_PAIRS]):
        label = "report.pairs[" + str(position) + "]"
        if not audit.fields(pair, PAIR_FIELDS, label):
            continue
        pair_id = pair.get("pair_id")
        valid_id = isinstance(pair_id, str) and bool(_ID.fullmatch(pair_id))
        if not valid_id:
            audit.error(label + ".pair_id must be a valid ID")
        else:
            if pair_id.casefold() in seen_pairs:
                audit.error(label + ": duplicate/case-colliding pair ID " + pair_id)
            seen_pairs.add(pair_id.casefold())
            if pair_id not in expected_pairs:
                audit.error(label + ": unplanned pair " + pair_id, reject=True)
            elif pair.get("kind") != expected_pairs[pair_id]:
                audit.error(label + ".kind differs from frozen plan", reject=True)
        context_valid = audit.context(pair.get("context"), label + ".context")
        if valid_id and pair_id in transfers:
            expected_context = transfer_contexts.get(pair_id)
            planned_context_valid = valid_transfer_contexts.get(pair_id, False)
        else:
            expected_context = plan.get("context")
            planned_context_valid = target_context_valid
        try:
            same_context = canonical_digest(pair.get("context")) == canonical_digest(expected_context)
        except (ValueError, TypeError, UnicodeError, RecursionError):
            same_context = False
        if context_valid and planned_context_valid and not same_context:
            audit.error(label + ".context differs from frozen plan", reject=True)
        states = {}
        for variant in ("baseline", "candidate"):
            run_label = label + "." + variant
            run = pair.get(variant)
            if not audit.fields(run, RUN_FIELDS, run_label):
                continue
            runs_used += 1
            run_id = run.get("run_id")
            if not isinstance(run_id, str) or not _ID.fullmatch(run_id):
                audit.error(run_label + ".run_id must be a valid ID")
            elif run_id.casefold() in seen_runs:
                audit.error(run_label + ": reused/case-colliding run ID " + run_id)
            else:
                seen_runs.add(run_id.casefold())
            duration = run.get("duration_seconds")
            if not _number(duration):
                audit.error(run_label + ".duration_seconds must be finite and nonnegative")
            else:
                # Compare the submitted decimal values exactly: binary float
                # sums can either invent or erase a time-budget overrun.
                seconds_used += Fraction(str(duration))
            checks = run.get("checks")
            if not isinstance(checks, list):
                audit.error(run_label + ".checks must be a list")
                checks = []
            if len(checks) > MAX_CHECKS:
                audit.error(run_label + ".checks exceeds supported bound", reject=True)
            statuses = {}
            check_ids = set()
            for index, check in enumerate(checks[:MAX_CHECKS]):
                check_label = run_label + ".checks[" + str(index) + "]"
                if not isinstance(check, dict):
                    audit.error(check_label + " must be an object")
                    continue
                # Keep known candidate failures even if that same record is malformed.
                status = check.get("status")
                check_id = check.get("id")
                if variant == "candidate" and status == "fail":
                    audit.regressions.append({
                        "pair_id": pair_id, "check_id": check_id,
                        "kind": "candidate-failure", "reason": check.get("reason"),
                    })
                optional = ("evidence",) if status == "not-run" else ()
                audit.fields(check, CHECK_FIELDS - set(optional), check_label, optional)
                if not isinstance(check_id, str) or not _ID.fullmatch(check_id):
                    audit.error(check_label + ".id must be a valid ID")
                    continue
                if check_id.casefold() in check_ids:
                    audit.error(check_label + ": duplicate/case-colliding check ID " + check_id)
                check_ids.add(check_id.casefold())
                if check_id not in required:
                    audit.error(check_label + ": unplanned check " + check_id, reject=True)
                if status not in ("pass", "fail", "not-run"):
                    audit.error(check_label + ".status must be pass, fail or not-run")
                    continue
                if not _text(check.get("reason")):
                    audit.absent(check_label + ".reason needs an observed result or nonexecution explanation")
                evidence_ok = False
                if status == "not-run":
                    audit.absent(run_label + ": " + check_id + " was not run")
                else:
                    evidence_ok = audit.file(check.get("evidence"), check_label)
                statuses[check_id] = status if evidence_ok else "not-run"
            for check_id in required:
                if check_id.casefold() not in check_ids:
                    audit.absent(run_label + ": missing required check " + check_id)
            states[variant] = statuses
        if valid_id and pair_id in expected_pairs:
            baseline = states.get("baseline", {})
            candidate = states.get("candidate", {})
            improved = set()
            for check_id in required:
                before, after = baseline.get(check_id), candidate.get(check_id)
                if before == "pass" and after == "fail":
                    for regression in audit.regressions:
                        if regression["pair_id"] == pair_id and regression["check_id"] == check_id:
                            regression["kind"] = "regression"
                if expected_pairs[pair_id] == "target" and check_id in improvement_checks:
                    if before == "fail" and after == "pass":
                        improved.add(check_id)
                        audit.improvements.append({"pair_id": pair_id, "check_id": check_id,
                                                   "baseline": "fail", "candidate": "pass"})
                if expected_pairs[pair_id] == "transfer" and before == "fail":
                    audit.absent(label + ": transfer baseline failed " + check_id + "; preservation unproven")
            if expected_pairs[pair_id] == "target":
                improvements_by_target[pair_id] = improved
    for pair_id in expected_pairs:
        if pair_id.casefold() not in seen_pairs:
            audit.absent("report is missing planned pair " + pair_id)
    if max_runs is not None and runs_used > max_runs:
        audit.absent("run budget exceeded: " + str(runs_used) + "/" + str(max_runs))
    if max_seconds is not None and seconds_used > Fraction(str(max_seconds)):
        # Decimal inputs leave only factors 2 and 5 in the denominator. Its
        # bit length bounds the decimal places needed for an exact diagnostic.
        with localcontext() as decimal_context:
            decimal_context.prec = len(str(seconds_used.numerator)) + seconds_used.denominator.bit_length()
            seconds_label = str(Decimal(seconds_used.numerator) / Decimal(seconds_used.denominator))
        audit.absent("time budget exceeded: " + seconds_label + "/" + str(max_seconds))

    review = report.get("review")
    if audit.fields(review, REVIEW_FIELDS, "report.review"):
        for field in REVIEW_FIELDS - {"evidence"}:
            if field in review and type(review[field]) is not bool:
                audit.error("report.review." + field + " must be a boolean")
        audit.file(review.get("evidence"), "report.review")
        if review.get("independent") is not True:
            audit.absent("independent review has not been recorded")
        if profile == "reviewed-local" and review.get("reproduced") is not True:
            audit.absent("reviewed-local requires independent reproduction")
        if profile == "enforced":
            if review.get("evaluator_isolated") is not True:
                audit.absent("enforced profile requires evaluator isolation")
            if review.get("holdout_unseen") is not True:
                audit.absent("enforced profile requires an unseen holdout")
    if audit.regressions or audit.rejections:
        return audit.result("rejected", "Candidate failures or frozen-contract violations prohibit adoption.")
    if audit.errors or audit.missing:
        return audit.result("incomplete", "Required valid execution or independent review evidence is missing.")
    shared_improvements = set(improvement_checks)
    for pair_id in targets:
        shared_improvements &= improvements_by_target.get(pair_id, set())
    if not shared_improvements:
        return audit.result("no-change", "No predeclared check improved in both target comparisons.")
    eligible_for = ["manual"]
    if profile == "enforced":
        eligible_for.append("auto-local")
    return audit.result("eligible", "Recorded comparisons show repeated improvement and required preservation; independent review claims remain external attestations.", eligible_for)
