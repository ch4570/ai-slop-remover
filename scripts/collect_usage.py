#!/usr/bin/env python3
"""Collect explicitly supplied Codex JSONL usage without running models or changing quality results."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from compare_evals import load_result, unique_object
from usage_accounting import compare_runs, normalize_samples


def owned_file(root, relative, allow_missing=False):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("Supply a run-relative evidence path")
    target = root / relative
    if (target.is_symlink() or not target.resolve().is_relative_to(root.resolve())
            or not target.is_file() and not (allow_missing and not target.exists())):
        raise ValueError("Evidence path is missing or outside this run: " + relative)
    return target


def codex_usage(events, mode):
    """Read terminal usage, preserving missing counters and unfinished turns as unknown."""
    if mode not in ("delta", "cumulative"):
        raise ValueError("Declare delta or cumulative usage mode for this runtime trace")
    thread, turn, terminal = None, 0, None
    samples, models = [], set()
    child_activity, missing_turn = False, False
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("JSONL events must be objects")
        kind = event.get("type")
        if kind == "thread.started":
            identifier = event.get("thread_id")
            if not isinstance(identifier, str) or not identifier or thread not in (None, identifier):
                raise ValueError("Each attempt trace must contain exactly one thread")
            thread = identifier
        elif kind == "turn.started":
            if turn and terminal != "completed":
                missing_turn = True
            turn += 1
            terminal = None
        elif kind == "turn.completed":
            if not thread or not turn:
                raise ValueError("Usage event lacks its thread/turn start")
            raw = event.get("usage")
            if not isinstance(raw, dict):
                terminal = "missing-usage"
                missing_turn = True
                continue
            if any(raw.get(key) is None for key in ("input_tokens", "cached_input_tokens", "output_tokens")):
                missing_turn = True
            samples.append({"sample_id": thread + ":" + str(turn),
                            "input_tokens": raw.get("input_tokens"),
                            "cached_input_tokens": raw.get("cached_input_tokens"),
                            "cache_write_tokens": raw.get("cache_write_input_tokens"),
                            "output_tokens": raw.get("output_tokens"),
                            "reasoning_output_tokens": raw.get("reasoning_output_tokens")})
            terminal = "completed"
        elif kind in ("turn.failed", "error"):
            terminal = "unfinished"
            missing_turn = True
        item = event.get("item", {})
        if isinstance(item, dict) and "collab" in str(item.get("type", "")):
            child_activity = True
        if kind in ("thread.started", "turn.started") and event.get("model") is not None:
            model = event["model"]
            if not isinstance(model, str) or not model.strip():
                raise ValueError("Invalid observed model")
            models.add(model)
    if len(models) > 1:
        raise ValueError("Mixed observed models require separate usage attempts")
    result = {"observed_model": next(iter(models), None), "child_activity": child_activity}
    if missing_turn or not samples or terminal != "completed":
        return {**result, "usage_status": "unavailable", "usage": None,
                "reason": "Trace has no complete terminal usage for every started turn; retain failed/interrupted attempt costs as unknown."}
    usage = normalize_samples(samples, mode)
    known = all(usage[key] is not None for key in ("input_tokens", "cached_input_tokens", "output_tokens"))
    return {**result, "usage_status": "observed" if known else "unavailable", "usage": usage if known else None,
            "reason": None if known else "Runtime omitted required input, cache-read or output counters."}


def collect(result_path, manifest_path):
    result_bytes = result_path.read_bytes()
    result = json.loads(result_bytes, object_pairs_hook=unique_object)
    manifest = load_result(manifest_path)
    if manifest.get("schema") != 1 or not isinstance(manifest.get("attempts"), list) or not manifest["attempts"]:
        raise ValueError("Attempt manifest needs schema 1 and a nonempty attempts list")
    attempts = []
    for record in manifest["attempts"]:
        if not isinstance(record, dict):
            raise ValueError("Attempt metadata must be an object")
        path = owned_file(manifest_path.parent, record.get("trace"))
        if not path.resolve().is_relative_to(result_path.parent.resolve()):
            raise ValueError("Keep trace files inside the quality result directory")
        raw = path.read_bytes()
        events = [json.loads(line, object_pairs_hook=unique_object) for line in raw.decode("utf-8").splitlines() if line.strip()]
        counters = codex_usage(events, record.get("mode"))
        status = record.get("status")
        if status not in ("completed", "failed", "incomplete"):
            raise ValueError("Record every attempt's completed, failed or incomplete status")
        attempt = {key: record.get(key) for key in ("attempt_id", "parent_id", "provider", "runtime_version",
                                                    "requested_model", "duration_seconds", "includes_children")}
        attempt.update(status=status, source={"path": path.resolve().relative_to(result_path.parent.resolve()).as_posix(),
                                             "sha256": hashlib.sha256(raw).hexdigest()},
                       **{key: counters[key] for key in ("observed_model", "usage_status", "usage", "reason")})
        if counters["child_activity"]:
            # The JSONL stream does not prove that all child usage has been included.
            attempt.update(usage_status="unavailable", usage=None,
                           reason="Collaboration activity is present; this Codex adapter cannot reconcile parent/child inclusion, even with separately declared child traces.")
        attempts.append(attempt)
    return {"schema": 1, "run_id": result["run_id"], "result_sha256": hashlib.sha256(result_bytes).hexdigest(),
            "attempts": attempts}


def write_new(path, value):
    text = json.dumps(value, ensure_ascii=True, allow_nan=False, indent=2) + "\n"
    if path is not None:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(text)
    print(text, end="")


def main():
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(errors="backslashreplace")
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("collect", help="Read one run's supplied attempt metadata and JSONL traces")
    capture.add_argument("result", type=Path)
    capture.add_argument("attempts", type=Path)
    capture.add_argument("output", type=Path, help="New sidecar next to result.json; existing files are never overwritten")
    compare = commands.add_parser("compare", help="Compare complete paired usage alongside unchanged quality results")
    compare.add_argument("pairs", type=Path)
    compare.add_argument("--prices", type=Path)
    compare.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "collect":
            if args.output.parent.resolve() != args.result.parent.resolve():
                raise ValueError("Write the usage sidecar next to its quality result")
            data = collect(args.result, args.attempts)
            write_new(args.output, data)
        else:
            manifest = load_result(args.pairs)
            if manifest.get("schema") != 1 or not isinstance(manifest.get("pairs"), list):
                raise ValueError("Comparison manifest needs schema 1 and pairs")
            pairs = []
            for entry in manifest["pairs"]:
                pairs.append({key: owned_file(args.pairs.parent, name, allow_missing=key.endswith('_usage')) if name is not None else None
                              for key, name in entry.items()})
            prices = load_result(args.prices) if args.prices else None
            write_new(args.output, compare_runs(pairs, prices=prices))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("Error: " + str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
