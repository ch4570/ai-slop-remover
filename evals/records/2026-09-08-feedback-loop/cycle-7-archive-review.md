# Cycle 7 independent archive audit and candidate replay

The frozen archive is internally consistent, and one new candidate-only replay
passed all 28 cases, 256 automatic-focus checkpoints and 20 viewport captures
with zero required failures, collector errors, runtime exceptions or review flags.
The original observer, specification, harness, baseline reference and all extracted
files remained unchanged. No baseline or control browser run was repeated.

This review was performed after archive creation on 2026-09-09 KST. Its artifacts
live outside the archive at `/tmp/lutriva-cycle7-review.bHKT4G`; this report must
remain an adjacent post-archive review, not be represented as archived evidence.

## Archive and scope

The exact supplied hashes matched:

- `cycle-7.tar.gz`: `3f23cc869e2449babca17061679d77eade49e8c94fd70ddf908c542ccfc1947e`
- `cycle-7-inventory.json`: `c660ff8aa2052fe87d1a3e91dbac58bc6d7fc5a404299e760dc103a7d04e3160`

The repository's unchanged checker was run first:

```sh
python3 scripts/check_evidence_archive.py evals/records/2026-09-08-feedback-loop/cycle-7-inventory.json evals/records/2026-09-08-feedback-loop/cycle-7.tar.gz
```

It exited 0 for schema 1, 334 regular files and 118,253,408 bytes. Independent
extraction into a newly created temporary directory and a separate filesystem
walk matched every inventoried path, byte count and SHA-256; there were no missing,
extra, changed or non-regular files. The same complete 334-file comparison after
replay found no changes. Archive and inventory hashes also remained identical.

The archived scope checker passed before and after replay against the original
83-file inventory: only `product/app.js` and `product/DESIGN.md` differ. Initial
input totals 308,896 bytes; final input totals 312,159 bytes. The other 81 paths,
including `components.css`, retain their starting bytes. Read-only `git show
537e33f:PATH` comparisons independently confirmed all 65 supplied skill files and
the harness against that Git snapshot.

I read both DESIGN files and the candidate source. The comparison-only 8px density
exception, its rationale, master 16px baseline and reconsideration conditions are
preserved verbatim. Added text describes the actual shared focus logic, natural
table height and remaining untested conditions. The implementation schedules
focus correction on focus, selection and layout/viewport changes; it does not
attach a correction loop to scrolling. This source review is separate from the
behavioral result.

## Recorded evidence audit, without browser reruns

TASK explicitly authorizes a new automatic-focus follow-up on both order screens;
PRIOR-REQUEST remains the historical density request. This is one new product
task, not a reinterpretation of the old gate or a skill-version experiment.

Raw JSON recomputation agreed with the reports:

| Recorded run | Required failure records | Completion |
| --- | --- | --- |
| Frozen v2 baseline | 73 checkpoint visibility failures plus 9 after-capture repeats, across 11 cases | 28 cases / 256 checkpoints / 20 captures |
| Candidate | 0 | 28 / 256 / 20 |
| No-outline control | 272 outline failures: 256 checkpoints plus 16 captures; also the same 82 baseline visibility failure contexts | 28 / 256 / 20 |
| Pinned-scroll control | Only 26 earlier-column movement and 26 no-snap-back failures | 28 / 256 / 20 |

All four final recorded runs have zero collector/runtime errors and review flags.
The negative controls are deliberately defective baseline copies used to check
specific predicates; they are not product candidates or skill versions. Matching
visibility failure contexts does not imply identical geometry payloads. For the
pinned example, samples `[942, 942, 942]` beginning at 220 ms cannot distinguish
no motion from movement and return before the first sample.

The original observer's 29 collector errors and zero completed cases/checkpoints
are preserved, as are the target-only correction's 28 completed cases and four
`wheel-no-earlier-column-travel` collector errors. They are not silently counted
as successful final collections. Auxiliary-target provenance asserted in the
legacy README remains unsupported; later evidence explicitly disavows it.

The author independently used 1,251 checks and 238 states per run. Its first
baseline has 49 focus failures and one invalid vertical-input preparation;
corrected-input baseline has 50 focus failures; candidate has zero. A separate
read-only comparison confirms all 238 unique paired labels match for the eight
listed preservation fields. Complete state and PNG-byte equality applies only to
the two wide initial views. The first author test source was not preserved
verbatim: the archived preparation diff is explicitly reconstructed documentation.
Original first-run JSON/PNG and the corrected paired-run source are preserved.

The observer/spec metadata, fixed source hashes and recorded timestamps support
the paired frozen execution. `parent/PLAN.md` and the observer reports document
pre-author freezing and separated author/observer context. Archive bytes cannot
independently prove historical access isolation; this review does not claim that.

## New candidate-only replay

Executed from the newly extracted record, keeping the existing observer source,
specification, harness and baseline reference together:

```sh
node observer/observer.mjs input/product /tmp/lutriva-cycle7-review.bHKT4G/candidate-replay input/harness/browser_harness.mjs input
```

Node was the already installed `v26.8.1`. The command ran from
18:31:36.505 to 18:35:50.419 UTC and exited 0 with empty stderr. Installed Chrome
reported `Chrome/152.0.7977.83`, revision
`@79460ebecaa5625e57a5fb679a735659e73dc687`, identically before and after and matching
the archived paired runs. No installation, update UI, user profile, native virtual
key adapter, shortcut expansion, specification freeze or source edit occurred.

The machine summary matches the raw arrays: 28/28 completed cases, 256 checkpoints,
20 actual viewport PNGs, and zero required/collector/runtime/review errors. An
independent post-run audit recomputed focus bounds and the expected active row,
outline and selection status from all 256 recorded checkpoints. All fit. All 20
captures have viewport dimensions and stable pre/post measured geometry. The two
wide initial PNGs are byte-identical to the frozen baseline images.

All 29 guards retain exactly the two initial page target IDs and local fixture or
about:blank URLs. Auxiliary target metadata is recorded with unverified provenance.
Temporary profiles and page guards do not establish network/update isolation.

Trusted right and left horizontal wheel inputs were delivered within the table
in all 26 overflowing cases; two wide 100% cases correctly skip for no overflow.
All 26 candidate cases had at most 10px rightward travel remaining after automatic
focus, so the observer's actual rightward-movement predicate was inapplicable.
The measured browsing-preservation result is actual leftward movement, retained
row/document Y, and no later snap-back over 220 + 650 + 650 ms. For the representative
master 320×864/200% case, X was 935 before the right input, then `[942,942,942]`,
then `[702,702,702]` after the left input; document Y stayed 0 and focus stayed M-101.
Input delivery in both directions is not a claim of substantial movement both ways.

All seven product and nine frozen protected manifest entries match before/after.
The complete extracted input also stayed identical across the run. These key
hashes remained unchanged:

- Observer: `545788c49b4e4380520163bb46e50a0dce1b82574ea4bc045786cda5ec99d253`
- Specification: `9252a96e6e78c2b80a35df01aed77aa7d03778cf76e5e74aab822d219ae80d00`
- Harness: `5538f93787bf84a401eba4ce747264ddd6bfc6e5e31049e4004a8986ad85a1e1`
- Baseline reference JSON: `56845a16f29056e331bbac74af4bb85e6b8be3fd0870ef4cecabc7ce4b35244b`

New replay `candidate-replay/browser.json` SHA-256:
`4cabf23c21d4da2710a9ba55dfd1cb907e75d7726961f1511eabe75181bbd860`.

### Preserved reviewer audit failure and clarification

The browser collection passed. My first post-run audit exited 1 solely because
it compared lexical `/tmp/.../extracted/input` with the observer's realpath
`/private/tmp/.../extracted/input`. The original `audit-replay.mjs` and
`replay-audit.json` are preserved unchanged; the latter contains the original
`Extracted protected-input override missing` error and otherwise passing checks.
It is not represented as an unqualified passing audit command.

A separate `check-realpath-clarification.mjs` command exited 0. It verified the
explicit override flag, matching canonical paths, matching directory device/inode,
unchanged 83-file input and exact frozen protected hashes. Its result is
`realpath-clarification.json`. No browser rerun, observer/spec rewrite or evidence
replacement was needed. The original audit JSON SHA-256 remains
`aa342f2c2a69d0c58c904bae78b5e9417c51e4f71a7a831913fbf987444becee`.

## Images actually opened in this review

I opened exactly these three new replay viewport PNGs, separately from historical
author/observer/control image-view counts:

- `candidate-replay/master-390x844-100-tab-first.png`: full first-row button and
  brown focus outline visible inside the narrow table; leftmost order text is
  partially outside the intentionally horizontally scrolled view. Expanded focus
  right edge is 372.703125 within the table/viewport bound 373 CSS px.
- `candidate-replay/master-focused-font-transition-1.png`: after synthetic 200%
  text enlargement with M-103 retained, the full third-row button/outline is
  visible and the M-103 selection status remains displayed. Expanded focus right
  edge is 287.625 within bound 288 CSS px.
- `candidate-replay/master-320x864-200-user-horizontal-wheel.png`: earlier product
  and amount columns occupy the viewport while the work column/focused button is
  deliberately offscreen; the visible status still names M-101. Static image
  appearance does not alone prove wheel timing; the raw samples above do.

These image views are not additional independent behavioral tasks.

## Artifacts and limits

Raw command metadata/stdout/stderr are in `archive-verifier.*`,
`author-scope-before.*`, `candidate-replay.*` and `author-scope-after.*` at the review
root. `run-review.mjs` is the external orchestration source. Full path/byte/hash
artifacts are `extraction-audit.json`, `extraction-after.json`, `input-before.json`,
`input-after.json`, `archive-hashes-before.json`, `archive-hashes-after.json` and
`git-snapshot-audit.json`. Offline counts/comparisons are in `recorded-audit.json`;
new replay geometry/events/captures/guards are in `replay-audit.json`, read together
with the preserved-path-failure clarification. Audit scripts are retained beside
their outputs. `audit-command-history.json` records the separate audit command
outcomes, including the failed review assertion and a non-executing diagnostic
syntax error. None changed archived input.

The conclusion is limited to this task and the fixed Chrome matrix, synthetic
body/heading CSS enlargement, Korean names, prescribed transitions and bounded
timings. It is not OS/page zoom, physical-device, other-browser, assistive-technology,
arbitrary-row-count, future overlay/fixed-height scroller, unbounded stability,
general evaluator coverage or full accessibility certification. Repository package
checks are handled separately by the parent; this reviewer did not rerun npm,
Python, opt-in browser suites or remote CI. No repository edits, commits, pushes,
installations or global/user configuration changes were made by this review.
