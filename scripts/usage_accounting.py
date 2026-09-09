#!/usr/bin/env python3
"""Account for declared run telemetry separately from evaluator-owned quality.

Hashes bind local evidence bytes; they do not authenticate provider billing.
Costs are explicit rate estimates, including failed attempts and child work.
"""
from datetime import date
from decimal import Decimal, localcontext
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.parse import urlsplit

from compare_evals import (compare, digest, invalid_constant, select_suite,
                           unique_object, validate)


TOKEN_FIELDS = ("input_tokens", "cached_input_tokens", "cache_write_tokens",
                "output_tokens", "reasoning_output_tokens")
ATTEMPT_FIELDS = {"attempt_id", "parent_id", "status", "provider", "runtime_version",
                  "requested_model", "observed_model", "usage_status", "includes_children",
                  "source", "usage", "duration_seconds"}
PRICE_FIELDS = {"schema", "provider", "model", "currency", "source", "as_of", "rates"}
RATE_FIELDS = {"input", "cached_input", "cache_write", "output"}
LIMITS = ("Local hashes bind declared telemetry, not authenticated provider billing. "
          "Rate estimates are not subscription charges or invoices. Duration is summed "
          "attempt time, which may overlap across concurrent children.")


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _usage(value):
    if not isinstance(value, dict) or set(value) != set(TOKEN_FIELDS):
        raise ValueError("usage requires exactly the five normalized token fields")
    for key, count in value.items():
        if count is not None and (type(count) is not int or count < 0):
            raise ValueError(key + " must be a nonnegative integer or null")
    total = value["input_tokens"]
    known_cached = sum(value[key] or 0 for key in ("cached_input_tokens", "cache_write_tokens"))
    if total is not None and known_cached > total:
        raise ValueError("cached input plus cache writes exceeds total input")
    output, reasoning = value["output_tokens"], value["reasoning_output_tokens"]
    if output is not None and reasoning is not None and reasoning > output:
        raise ValueError("reasoning output exceeds total output")
    return dict(value)


def _sum_usage(values):
    return {key: None if any(value[key] is None for value in values)
            else sum(value[key] for value in values) for key in TOKEN_FIELDS}


def normalize_samples(samples, mode):
    """Use explicit delta events or monotone cumulative snapshots; keep nulls.

    Event identity deduplicates exact replays in either mode. Reusing an identity
    for a changed record is invalid. A later known cumulative value may recover
    an earlier unknown subset, but must not decrease from its last known value.
    """
    if mode not in ("delta", "cumulative"):
        raise ValueError("mode must be explicitly delta or cumulative")
    if not isinstance(samples, list) or not samples:
        raise ValueError("samples must be a nonempty list")
    seen, values = {}, []
    last_known = {key: None for key in TOKEN_FIELDS}
    for sample in samples:
        if not isinstance(sample, dict) or set(sample) != set(TOKEN_FIELDS) | {"sample_id"}:
            raise ValueError("sample requires sample_id and normalized usage")
        identity = sample["sample_id"]
        if not _text(identity):
            raise ValueError("sample_id must be a nonempty string")
        value = _usage({key: sample[key] for key in TOKEN_FIELDS})
        if identity in seen:
            if seen[identity] != value:
                raise ValueError("conflicting repeated sample_id: " + identity)
            continue
        seen[identity] = value
        if mode == "cumulative":
            for key, count in value.items():
                previous = last_known[key]
                if count is not None:
                    if previous is not None and count < previous:
                        raise ValueError("cumulative " + key + " decreased")
                    last_known[key] = count
        values.append(value)
    return _sum_usage(values) if mode == "delta" else values[-1]


def _load_json(path):
    raw = path.read_bytes()
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object,
                      parse_constant=invalid_constant), raw


def _quality(path):
    run, raw = _load_json(path)
    if not isinstance(run, dict) or run.get("variant") not in ("baseline", "candidate"):
        raise ValueError("result must identify baseline or candidate variant")
    try:
        suite = select_suite(run.get("suite"))
    except (KeyError, TypeError):
        raise ValueError("result suite is not a known evaluator-owned suite") from None
    errors = validate(run, run["variant"], path.parent, suite)
    if errors:
        raise ValueError("; ".join(errors))
    return run, raw, suite


def _source(source, sidecar_root, run_root):
    if not isinstance(source, dict) or set(source) != {"path", "sha256"}:
        raise ValueError("source requires path and sha256")
    name = source["path"]
    if not _text(name) or not digest(source["sha256"]):
        raise ValueError("source requires a relative path and SHA-256")
    declared = sidecar_root / name
    if declared.is_symlink():
        raise ValueError("source must be a regular file, not a symlink")
    target = declared.resolve()
    if Path(name).is_absolute() or not target.is_relative_to(run_root):
        raise ValueError("source path is outside the run directory")
    if not target.is_file() or target.stat().st_size == 0:
        raise ValueError("source file is missing, empty, or not a regular file")
    if hashlib.sha256(target.read_bytes()).hexdigest() != source["sha256"]:
        raise ValueError("source SHA-256 does not match evidence bytes")
    return target


def _attempts(sidecar, sidecar_path, result_path, run, raw):
    if (not isinstance(sidecar, dict)
            or set(sidecar) != {"schema", "run_id", "result_sha256", "attempts"}
            or type(sidecar["schema"]) is not int or sidecar["schema"] != 1):
        raise ValueError("usage sidecar requires schema 1 and its declared fields")
    if sidecar["run_id"] != run["run_id"]:
        raise ValueError("usage sidecar run_id differs from quality result")
    if sidecar["result_sha256"] != hashlib.sha256(raw).hexdigest():
        raise ValueError("usage sidecar result_sha256 does not match raw result bytes")
    attempts = sidecar["attempts"]
    if not isinstance(attempts, list) or not attempts:
        raise ValueError("usage sidecar attempts must be a nonempty list")
    ids, sources = {}, set()
    for attempt in attempts:
        if (not isinstance(attempt, dict) or not ATTEMPT_FIELDS <= set(attempt)
                or set(attempt) - ATTEMPT_FIELDS - {"reason"}):
            raise ValueError("attempt has unexpected or missing fields")
        identity = attempt["attempt_id"]
        if not _text(identity) or identity in ids:
            raise ValueError("attempt_id must be nonempty and unique")
        ids[identity] = attempt
        for key in ("provider", "runtime_version"):
            if not _text(attempt[key]):
                raise ValueError(identity + ": " + key + " must be recorded")
        for key in ("parent_id", "requested_model", "observed_model"):
            if attempt[key] is not None and not _text(attempt[key]):
                raise ValueError(identity + ": " + key + " must be a string or null")
        if attempt["status"] not in ("completed", "failed", "incomplete"):
            raise ValueError(identity + ": invalid attempt status")
        if type(attempt["includes_children"]) is not bool:
            raise ValueError(identity + ": includes_children must be boolean")
        duration = attempt["duration_seconds"]
        if duration is not None and (type(duration) not in (int, float)
                or not math.isfinite(duration) or duration < 0):
            raise ValueError(identity + ": duration_seconds must be finite and nonnegative or null")
        if attempt["usage_status"] == "observed":
            _usage(attempt["usage"])
        elif attempt["usage_status"] == "unavailable":
            if attempt["usage"] is not None or not _text(attempt.get("reason")):
                raise ValueError(identity + ": unavailable usage requires null usage and a reason")
        else:
            raise ValueError(identity + ": usage_status must be observed or unavailable")
        source = _source(attempt["source"], sidecar_path.parent.resolve(), result_path.parent.resolve())
        if source in sources:
            raise ValueError(identity + ": source path already belongs to another declared attempt")
        sources.add(source)
    for identity, attempt in ids.items():
        visited = {identity}
        parent = attempt["parent_id"]
        while parent is not None:
            if parent not in ids:
                raise ValueError(identity + ": parent_id is absent from declared attempts")
            if parent in visited:
                raise ValueError(identity + ": cycle in attempt parents")
            visited.add(parent)
            parent = ids[parent]["parent_id"]
    return attempts


def _price_tables(prices):
    if prices is None:
        return {}
    tables = [prices] if isinstance(prices, dict) else prices
    if not isinstance(tables, list):
        raise ValueError("prices must be a price table or list of price tables")
    lookup = {}
    for table in tables:
        if (not isinstance(table, dict) or set(table) != PRICE_FIELDS
                or type(table["schema"]) is not int or table["schema"] != 1):
            raise ValueError("price table requires schema 1 and its declared fields")
        if any(not _text(table[key]) for key in ("provider", "model", "currency", "source", "as_of")):
            raise ValueError("price table must identify provider, model, currency, source, and as_of")
        url = urlsplit(table["source"])
        if url.scheme != "https" or not url.hostname or url.username or url.password:
            raise ValueError("price source must be an HTTPS URL without credentials")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", table["as_of"]):
            raise ValueError("price as_of must be YYYY-MM-DD")
        date.fromisoformat(table["as_of"])
        rates = table["rates"]
        if not isinstance(rates, dict) or set(rates) != RATE_FIELDS:
            raise ValueError("price rates must specify input, cached_input, cache_write, output")
        for rate in rates.values():
            if not isinstance(rate, str) or not re.fullmatch(r"\d+(?:\.\d+)?", rate):
                raise ValueError("price rates must be nonnegative plain decimal strings per million")
        key = table["provider"], table["model"]
        if key in lookup:
            raise ValueError("duplicate price table for provider/model")
        lookup[key] = table
    return lookup


def _decimal_sum(values):
    if not values:
        return Decimal(0)
    places = max(max(-value.as_tuple().exponent, 0) for value in values)
    digits = max(max(value.adjusted() + 1, 1) for value in values)
    with localcontext() as context:
        context.prec = places + digits + len(str(len(values))) + 2
        return sum(values, Decimal(0))


def _estimate(value, table):
    counts = {"input": value["input_tokens"] - value["cached_input_tokens"] - value["cache_write_tokens"],
              "cached_input": value["cached_input_tokens"], "cache_write": value["cache_write_tokens"],
              "output": value["output_tokens"]}
    terms = []
    for key, count in counts.items():
        rate = Decimal(table["rates"][key])
        with localcontext() as context:
            context.prec = len(str(count)) + len(rate.as_tuple().digits) + 10
            terms.append(Decimal(count) * rate / Decimal(1000000))
    return _decimal_sum(terms)


def _money(value):
    if value is None:
        return None
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _median(values):
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    total = _decimal_sum(ordered[middle - 1:middle + 1])
    with localcontext() as context:
        context.prec = len(total.as_tuple().digits) + 2
        return total / Decimal(2)


def _price_attempts(attempts, prices):
    lookup = _price_tables(prices)
    estimates, used, reasons = [], {}, []
    for attempt in attempts:
        label = attempt["attempt_id"] + ": "
        key = attempt["provider"], attempt["observed_model"]
        if key[1] is None:
            reasons.append(label + "observed model is unavailable; requested model cannot price usage")
        elif key not in lookup:
            reasons.append(label + "no price table for observed provider/model")
        elif any(attempt["usage"][field] is None for field in TOKEN_FIELDS if field != "reasoning_output_tokens"):
            reasons.append(label + "input/cache/output pricing breakdown is unavailable")
        else:
            table = lookup[key]
            used[key] = table
            estimates.append(_estimate(attempt["usage"], table))
    currencies = {table["currency"] for table in used.values()}
    if len(currencies) > 1:
        reasons.append("attempt prices use different currencies")
    tables = [used[key] for key in sorted(used)]
    if reasons:
        return None, None, tables, reasons
    return _decimal_sum(estimates), next(iter(currencies)), tables, []


def summarize_run(result_path, sidecar_path=None, prices=None):
    """Validate quality and hash bindings, then account for every declared attempt.

    Missing or incomplete telemetry never becomes zero. Unknown reasoning or
    cache-write subsets preserve known token totals; cache-write uncertainty
    blocks pricing. Quality remains the evaluator's independently recorded result.
    """
    summary = {"run_id": None, "variant": None, "quality_pass": None,
               "quality_complete": None, "usage_status": "unavailable",
               "cost_status": "unavailable", "tokens": None, "estimated_cost": None,
               "currency": None, "cost_kind": None, "pricing": [], "execution": [],
               "metadata": None, "duration_seconds": None, "duration_kind": "summed-attempt-time",
               "coverage": {"attempts": 0, "observed_attempts": 0, "unavailable_attempts": 0},
               "errors": [], "reasons": [], "limits": LIMITS}
    result_path = Path(result_path)
    try:
        run, raw, _ = _quality(result_path)
    except (OSError, UnicodeError, ValueError, TypeError) as error:
        summary.update(usage_status="invalid", cost_status="invalid", errors=[str(error)])
        return summary
    statuses = [check["status"] for case in run["cases"] for check in case["checks"]]
    summary.update(run_id=run["run_id"], variant=run["variant"],
                   quality_pass=all(status == "pass" for status in statuses),
                   quality_complete=all(status != "not-run" for status in statuses),
                   metadata={key: run[key] for key in ("suite", "fixture", "task_sha256", "model", "settings")})
    if sidecar_path is None:
        summary["reasons"].append("usage sidecar was not supplied")
        return summary
    sidecar_path = Path(sidecar_path)
    try:
        if not sidecar_path.resolve().is_relative_to(result_path.parent.resolve()):
            raise ValueError("usage sidecar must be inside the run directory")
        sidecar, _ = _load_json(sidecar_path)
        attempts = _attempts(sidecar, sidecar_path, result_path, run, raw)
    except FileNotFoundError as error:
        summary["reasons"].append("usage sidecar or source is absent: " + str(error))
        return summary
    except (OSError, UnicodeError, ValueError, TypeError, OverflowError) as error:
        summary.update(usage_status="invalid", cost_status="invalid", errors=[str(error)])
        return summary
    summary["execution"] = [{key: attempt[key] for key in
        ("attempt_id", "parent_id", "status", "provider", "runtime_version", "requested_model",
         "observed_model", "usage_status", "includes_children")} for attempt in attempts]
    observed = sum(attempt["usage_status"] == "observed" for attempt in attempts)
    summary["coverage"] = {"attempts": len(attempts), "observed_attempts": observed,
                           "unavailable_attempts": len(attempts) - observed}
    durations = [attempt["duration_seconds"] for attempt in attempts]
    if all(value is not None for value in durations):
        total_duration = sum(durations)
        if math.isfinite(total_duration):
            summary["duration_seconds"] = total_duration
    parents = {attempt["parent_id"] for attempt in attempts if attempt["parent_id"] is not None}
    for attempt in attempts:
        label = attempt["attempt_id"] + ": "
        if attempt["includes_children"] and attempt["attempt_id"] in parents:
            summary["reasons"].append(label + "includes_children conflicts with separately listed children")
        if attempt["status"] == "incomplete":
            summary["reasons"].append(label + "attempt is incomplete")
        if attempt["usage_status"] == "unavailable":
            summary["reasons"].append(label + attempt["reason"])
        elif any(attempt["usage"][key] is None for key in ("input_tokens", "cached_input_tokens", "output_tokens")):
            summary["reasons"].append(label + "input, cached input, or output telemetry is unknown")
    if summary["reasons"]:
        return summary
    summary.update(usage_status="observed", tokens=_sum_usage([attempt["usage"] for attempt in attempts]))
    try:
        estimate, currency, tables, reasons = _price_attempts(attempts, prices)
    except (ValueError, TypeError) as error:
        summary.update(cost_status="invalid", errors=[str(error)])
        return summary
    summary.update(estimated_cost=_money(estimate), currency=currency, pricing=tables)
    summary["reasons"].extend(reasons)
    if estimate is not None:
        summary.update(cost_status="estimated", cost_kind="rate-estimate")
    return summary


def _execution_conditions(summary):
    # Attempt count and parent structure are outcomes, not fixed conditions.
    return {(attempt["provider"], attempt["runtime_version"], attempt["requested_model"],
             attempt["observed_model"]) for attempt in summary["execution"]}


def _ratio(numerator, denominator):
    if denominator == 0:
        return None
    with localcontext() as context:
        context.prec = max(40, len(numerator.as_tuple().digits) + len(denominator.as_tuple().digits) + 12)
        return numerator / denominator


def _quality_totals(pairs, variant):
    completed = sum(pair[variant]["quality_pass"] is True for pair in pairs)
    known = sum(pair[variant]["quality_pass"] is not None for pair in pairs)
    return {"attempted_tasks": len(pairs), "completed_tasks": completed,
            "failed_or_incomplete_tasks": known - completed, "unknown_tasks": len(pairs) - known,
            "completion_rate": completed / len(pairs) if pairs else None}


def _cost_totals(matched, variant):
    values = [Decimal(pair[variant]["estimated_cost"]) for pair in matched]
    total = _decimal_sum(values) if values else None
    completed = sum(pair[variant]["quality_pass"] is True for pair in matched)
    return {"attempted_tasks": len(matched), "completed_tasks": completed,
            "attempted_cost": _money(total),
            "cost_per_completed_task": _money(_ratio(total, Decimal(completed))) if total is not None else None}


def _token_totals(matched, variant):
    tokens = _sum_usage([record[variant]["tokens"] for record in matched]) if matched else None
    completed = sum(record[variant]["quality_pass"] is True for record in matched)
    total = tokens["input_tokens"] + tokens["output_tokens"] if tokens is not None else None
    return {"attempted_tasks": len(matched), "completed_tasks": completed, "tokens": tokens,
            "total_tokens": total, "tokens_per_completed_task":
            _money(_ratio(Decimal(total), Decimal(completed))) if total is not None else None}


def compare_runs(pairs, prices=None):
    """Compare matched attempted costs, retaining failed and unpaired outcomes.

    Savings use attempted cost per quality-passing task and are suppressed on
    regressions. Complete matched subsets are reported with explicit exclusions;
    reused run IDs invalidate the comparison instead of silently deduplicating.
    """
    if not isinstance(pairs, list):
        raise ValueError("pairs must be a list")
    records, errors, seen = [], [], set()
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or set(pair) != {
                "baseline_result", "baseline_usage", "candidate_result", "candidate_usage"}:
            raise ValueError("each pair requires baseline/candidate result and usage paths")
        record = {"index": index, "exclusions": [], "usage_exclusions": []}
        for variant in ("baseline", "candidate"):
            summary = summarize_run(pair[variant + "_result"], pair[variant + "_usage"], prices)
            record[variant] = summary
            identity = summary["run_id"]
            if identity is not None:
                if identity in seen:
                    message = "reused run_id in pair " + str(index) + ": " + identity
                    errors.append(message)
                    record["exclusions"].append(message)
                    record["usage_exclusions"].append(message)
                seen.add(identity)
            if summary["cost_status"] != "estimated":
                record["exclusions"].append(variant + ": " + "; ".join(
                    summary["errors"] + summary["reasons"] or ["cost is unavailable"]))
            if summary["usage_status"] != "observed":
                record["usage_exclusions"].append(variant + ": usage is " + summary["usage_status"])
        try:
            baseline_path, candidate_path = Path(pair["baseline_result"]), Path(pair["candidate_result"])
            baseline, _, suite = _quality(baseline_path)
            candidate, _, _ = _quality(candidate_path)
            quality = compare(baseline, candidate, baseline_path.parent, candidate_path.parent, suite)
        except (OSError, UnicodeError, ValueError, TypeError) as error:
            quality = {"verdict": "invalid", "errors": [str(error)]}
        record["quality"] = quality
        if quality["verdict"] == "invalid":
            record["exclusions"].extend(quality["errors"])
            record["usage_exclusions"].extend(quality["errors"])
        before, after = record["baseline"], record["candidate"]
        if before["usage_status"] == after["usage_status"] == "observed":
            if _execution_conditions(before) != _execution_conditions(after):
                message = "observed provider/runtime/requested/observed model conditions differ"
                record["exclusions"].append(message)
                record["usage_exclusions"].append(message)
        record["usage_comparable"] = not record["usage_exclusions"]
        record["total_token_delta"] = (after["tokens"]["input_tokens"] + after["tokens"]["output_tokens"]
            - before["tokens"]["input_tokens"] - before["tokens"]["output_tokens"]
            if record["usage_comparable"] else None)
        if before["cost_status"] == after["cost_status"] == "estimated":
            if before["currency"] != after["currency"]:
                record["exclusions"].append("estimated cost currencies differ")
            if before["pricing"] != after["pricing"]:
                record["exclusions"].append("pricing snapshots differ")
        record["cost_comparable"] = not record["exclusions"]
        record["cost_delta"] = (_money(_decimal_sum([
            Decimal(after["estimated_cost"]), Decimal(before["estimated_cost"]).copy_negate()]))
            if record["cost_comparable"] else None)
        records.append(record)
    matched = [record for record in records if record["cost_comparable"]]
    # All aggregated pairs must share a snapshot, not merely match within a pair.
    snapshots = {json.dumps(record["baseline"]["pricing"], sort_keys=True) for record in matched}
    if len(snapshots) > 1:
        for record in matched:
            record["exclusions"].append("pricing snapshots differ across matched pairs")
            record.update(cost_comparable=False, cost_delta=None)
        matched = []
    if errors:
        # Reused contexts cannot establish independent evidence or a savings claim.
        for record in records:
            record["exclusions"].append("comparison contains reused run IDs")
            record["usage_exclusions"].append("comparison contains reused run IDs")
            record.update(cost_comparable=False, cost_delta=None, usage_comparable=False, total_token_delta=None)
        matched = []
    usage_matched = [record for record in records if record["usage_comparable"]]
    quality = {variant: _quality_totals(records, variant) for variant in ("baseline", "candidate")}
    cost = {variant: _cost_totals(matched, variant) for variant in ("baseline", "candidate")}
    usage = {variant: _token_totals(usage_matched, variant) for variant in ("baseline", "candidate")}
    token_deltas = [Decimal(record["total_token_delta"]) for record in usage_matched]
    usage["median_pair_total_token_delta"] = _money(_median(token_deltas)) if token_deltas else None
    deltas = [Decimal(record["cost_delta"]) for record in matched]
    cost["median_pair_cost_delta"] = _money(_median(deltas)) if deltas else None
    regressions = any(record["quality"].get("regressions") for record in records)
    regressions = regressions or quality["candidate"]["completed_tasks"] < quality["baseline"]["completed_tasks"]
    before = cost["baseline"]["cost_per_completed_task"]
    after = cost["candidate"]["cost_per_completed_task"]
    savings = None
    incomplete_quality = any(record["quality"].get("not_run")
                             or record["quality"]["verdict"] == "invalid" for record in records)
    if before is not None and after is not None and not regressions and not errors and not incomplete_quality:
        savings = _ratio(_decimal_sum([Decimal(before), Decimal(after).copy_negate()]), Decimal(before))
    verdict = ("invalid" if errors else "tradeoff" if regressions else "compared" if matched
               else "compared_usage" if usage_matched else "unavailable")
    return {"schema": 1, "verdict": verdict, "pairs": records, "total_pairs": len(records),
            "matched_pairs": len(matched), "excluded_pairs": len(records) - len(matched),
            "usage_matched_pairs": len(usage_matched), "usage_excluded_pairs": len(records) - len(usage_matched),
            "usage": usage,
            "quality": quality, "cost": cost, "currency": matched[0]["baseline"]["currency"] if matched else None,
            "savings_fraction": _money(savings), "savings_scope": "complete matched pairs only",
            "errors": errors, "limits": LIMITS + " Missing observed models remain unknown even when "
            "requested-condition token comparisons are possible. Small paired samples provide no p95 or causal claim."}
