# Cycle 8 final archive audit and fresh replay

The frozen archive is consistent with its inventory, and its unchanged portable
probe reproduces the claimed bounded regression and fix from a new extraction.
No blocking outcome or provenance discrepancy was found in the checks below.

Audited from `/Users/rex/Desktop/personal/lutriva` using Python 3.9.6 on macOS
26.6.2 arm64. All new extraction, installations, scripts, logs and snapshots are
under `/private/tmp/lutriva-cycle8-final-review.HCMTxX` (the canonical path of
`/tmp/lutriva-cycle8-final-review.HCMTxX`). These post-archive artifacts and this
review are **outside the frozen tar**. Existing absolute metadata was preserved.

## Archive and source integrity

The repository checker ran before extraction and again after replay:

```sh
python3 scripts/check_evidence_archive.py evals/records/2026-09-08-feedback-loop/cycle-8-inventory.json evals/records/2026-09-08-feedback-loop/cycle-8.tar.gz
```

Both checks returned exit 0, `verified`, schema-1, 3,219 regular files and
66,347,074 bytes. A separate filesystem inventory matched every extracted path,
byte length and SHA-256. All 3,219 files also retained identical mode, nanosecond
mtime, byte length and hash across replay. Archive/inventory hashes stayed:

| Input | SHA-256 |
| --- | --- |
| `cycle-8.tar.gz` | `5cb4399c8f22b298d2b94f28b5d3d235c93fb330bbe88e2aa3ed94f685795746` |
| `cycle-8-inventory.json` | `70258e21ec3d7428e0f28314c9d894c27c4fc8b5cfb9fea0696165b214534eff` |

Each of the 76 baseline release files was compared directly with
`git show e9a9fa026b71ec6617db0e12abd8694406ec2542:PATH`; all bytes match.
The baseline totals 2,969,338 bytes and candidate 2,969,376 bytes. Their paths are
identical; only `install.py` and its manifest hash differ. The exact runtime change
replaces `read_json(dest / marker)` with
`read_installation_record(dest / marker, expected["installer"])`.
The candidate matches its archived freeze inventory. Its runtime and the archived
regression test source also match the current repository bytes at audit time.
All four archived staging mappings match their complete extracted file inventories.
Historical `sourceUnchanged` flags were inspected as recorded claims; the original
temporary source directories were not independently re-inventoried by this audit.

## Fresh unchanged replay

The probe SHA-256 was and remains
`a0b9a2f73b4a220093f898bddb3ca247f1e3f4e71b1ccd23ff47157272889620`.
The following exact commands were captured, with working directory
`/private/tmp/lutriva-cycle8-final-review.HCMTxX/extracted`; both output roots
were unused and outside the extracted inputs:

```sh
/Library/Developer/CommandLineTools/usr/bin/python3 -B /private/tmp/lutriva-cycle8-final-review.HCMTxX/extracted/probe/probe.py /private/tmp/lutriva-cycle8-final-review.HCMTxX/extracted/probe/baseline-release /private/tmp/lutriva-cycle8-final-review.HCMTxX/baseline-replay
/Library/Developer/CommandLineTools/usr/bin/python3 -B /private/tmp/lutriva-cycle8-final-review.HCMTxX/extracted/probe/probe.py /private/tmp/lutriva-cycle8-final-review.HCMTxX/extracted/parent/candidate-release /private/tmp/lutriva-cycle8-final-review.HCMTxX/candidate-replay
```

| Observed result | Baseline | Candidate |
| --- | --- | --- |
| Probe exit | 1: requirement failure | 0 |
| Scenarios passed | 12/28 | 28/28 |
| Assertions passed | 128/160 | 160/160 |
| Collector failures | 0 | 0 |
| Source/release unchanged within run | yes | yes |

Scenario and requirement keys are identical. The matrix has 24 malformed cases
(two destinations, two receipt markers, schemas `true`/`1.0`, three separate
command projects) and four valid integer controls. All 32 baseline failed
assertions pass on the candidate, with no passing assertion regressing.

Independent raw checks covered every replay scenario: CLI argv/cwd/exit and
encoded stream consistency; snapshot file bytes decoded against size/hash; and
the retained final filesystem against every saved path/type/mode/nanosecond
mtime/byte value. Eight malformed status cases per release return 0 and report
the selected receipt unverifiable without writes. Candidate dry-run/full install
reject all 16 malformed cases with exit 1 and exact complete-project preservation.
Baseline dry-run accepts without writes; its eight actual installs add six new
siblings after a legacy seed or five after the specialist plus legacy seed.
Existing installed paths, malformed receipts and project sentinel remain exact;
no overwrite or data loss is observed. Unexpected baseline copies remain retained.
Both releases' four valid controls preserve status/dry-run projects, expand to
seven skills while preserving existing installations, then reinstall unchanged.

## Recorded coverage and limits

The frozen raw evidence was additionally audited by a separate read-only agent;
its unchanged report/scripts/results were copied into `recorded-raw-audit/`.
That audit independently recomputed all 320 paired assertions from 136 CLI
records and 136 snapshots. Its original paired outcomes match these replay
counts and behavior. Captured parent logs
support two regression methods with 12 pre-fix failing subcases followed by those
methods passing; installer 80 passed; full suite 293 run with 47 skipped
(246 passed, including installer 80); separate `/opt/homebrew/bin/python3.12`
installer 80 passed; npm 20 passed. Repeated/subset runs are not additional
coverage categories. These broad suites were inspected, not re-executed here.
The quiet full log records the skip count without reasons; the exact Python
3.12.14 patch version and browser-only skip classification are historical
narrative claims rather than independently established by those captured logs.

The baseline is exact Git source; the candidate release was frozen before the
later changelog/verification edits. Later final-suite logs are separate checks.
Unusual legacy reserved-marker and case-folded file/parent-overlap compatibility
boundaries are source-derived, not extra executed diagnostics. This audit does
not establish real-host discovery, skill/model quality, all malformed-input
coverage, browser behavior or a general concurrency guarantee. No network,
dependency installation, real user skill/configuration access, repository edit,
commit, publication or push was performed by this audit.

Evidence beside this temporary review includes `audit_archive.py`,
`extracted-before.json`/`extracted-after.json`, `audit-before.json`/`audit-after.json`,
`checker-*.stdout`/`checker-*.command.json`, `input-hashes-*.json`,
`source-provenance.json`, `record-provenance.json`, `runtime.diff`,
`baseline-replay.command.json`/`candidate-replay.command.json` and their raw
streams, both complete replay directories, and `replay-raw-audit.json` with its
independent `audit_replay.py`; `recorded-raw-audit/` contains the second auditor's
`AUDIT.md`, raw/count JSON and reproducible scripts (original directory:
`/private/tmp/lutriva-cycle8-raw-audit.lXmOY4`). A harmless failed read-only filename lookup is
preserved in `diagnostic-read-error.json`; neither the probe nor a replay was
corrected or retried.
