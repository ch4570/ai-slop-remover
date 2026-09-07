# Observed UI evaluations

`skill-cases.json` is a scenario catalog. Package validation confirms its structure
and routes; it does **not** execute an agent or establish improved UI quality.
The separate, runnable `search-editor-v2` suite exercises observable outcomes in a
small local UI. Neither suite assigns a beauty score.

## Controlled agent trial

1. Copy `fixtures/search-editor/` to two isolated temporary working directories.
   Preserve an untouched snapshot. These are synthetic notes; no production data or
   network backend is involved. Never run the checks in a user's real product tab.
2. Supply the exact `TASK.md` text to each agent. Load the old released or explicitly pinned baseline skills in the
   baseline lane and the proposed skills in the candidate lane. Keep the model,
   reasoning/settings, initial fixture, task, and available tools the same. Record
   skill revisions and agent/tool transcripts. Give each agent only its own copy.
3. Let each agent implement and verify independently. They may edit only the fixture
   files listed in the task. Keep `checks/` evaluator-owned and outside their edit
   scope. Review the patch for removal of required behavior or test-directed edits.
4. Serve each resulting copy on a different fresh localhost origin, for example
   `python3 -m http.server 8765 --bind 127.0.0.1 --directory /tmp/baseline-fixture`.
   Use a second port for the candidate, fresh browser storage, and a new tab. Record
   the resulting artifact hashes separately from the **initial** fixture hash.
5. Run the optional installed-Chrome driver below, or perform its sequence in a
   real browser. Inject `checks/search-editor.js` into each newly loaded document.
   Keep snapshots and observations **outside the page** so reloads cannot erase
   them. `seedSearchEditor()` writes the three synthetic notes to localStorage and
   returns their snapshot; reload and reinject the checker before editing them.
   Never seed storage in a real product tab.

   - Run `await evaluateSearchEditor(snapshot)` for search and id 1 failure/retry.
     Save its `checks` and `expected`, reload and reinject, then append
     `observeReload('retry-reload', expected)`.
   - Seed, reload, and reinject again. Run `await evaluateOrdinarySave(snapshot)`
     for composition and id 2 button saving. Save its `checks` and `expected`,
     reload and reinject, then append `observeReload('ordinary-reload', expected)`.
   - Seed, reload, and reinject again. Call `prepareOrdinaryEnter(snapshot)` and
     retain the returned context. If `selectionFound` is true, press a real browser
     Enter key (or use the automation keyboard API) and wait for saving to settle.
     Append `observeOrdinaryEnter(context)`, reload and reinject, then append
     `observeReload('ordinary-enter-reload', context.expected)`. A synthetic DOM
     key event cannot replace this positive control for native form submission.

   Each save mode starts from the same seeded snapshot to keep a prior failure
   from masking later controls. Reload checks run **before** the next seed and
   inspect both stored records and the title/body opened from every listed note.
   Missing/duplicate note buttons yield failed observations. Preserve completed
   observations and console errors; a runner exception makes unexecuted checks
   `not-run` with the error as the reason, never pass.
6. Independently inspect the rendered UI at desktop and 375px width. Record a
   screenshot and keyboard observations for the quality checks below. Read the
   actual screenshots. DOM dimensions, build success, or an implementation agent's
   own verdict cannot substitute for visual and interaction inspection.
7. Write baseline and candidate result JSON using the contract below and run:

   ```bash
   python3 scripts/compare_evals.py /tmp/trial/baseline.json /tmp/trial/candidate.json
   ```

The original fixture intentionally fails save recovery, composition Enter, and
per-keystroke history. Ordinary search and successful local saving should work.
Running the checks on that fixture is a useful positive/negative control, **not**
an old-skill agent trial. A claim about a skill change needs both agent executions.
A single paired trial is a bounded observation; it does not establish general lift
or causality. Use repeated trials and other tasks to investigate robustness.

## Observable checks

The evaluator-owned `checks/suite.json` fixes all required case IDs, check IDs, and
kinds. Missing a check from both runs still invalidates a comparison.

| Check | Evidence required |
| --- | --- |
| `search-matches` | Intended query returns the actual matching note. |
| `query-history` | Three input events keep history length stable **and** synchronize URL query. |
| `failed-save-draft` | Title/body survive injected failure; persisted storage remains unchanged. |
| `failed-save-feedback` | Error feedback is truthful and saving is available again. |
| `failed-save-storage` | Injected failure preserves the entire seeded storage snapshot, including every ID and title/body. |
| `retry-persists` | Retrying id 1 changes only its title/body; all other records and unique IDs remain intact. |
| `retry-reload` | After retry and a real reload, the complete expected storage and every note's editor values remain intact. |
| `composition-enter` | Synthetic composition Enter causes no submit and no persistence mutation. |
| `ordinary-save` | Selecting id 2 and saving by button changes only its title/body while preserving all records and unique IDs. |
| `ordinary-reload` | After button saving and a real reload, the complete expected storage and every note's editor values remain intact. |
| `ordinary-enter` | Selecting id 3 and pressing real browser Enter saves only its title/body while preserving all records and unique IDs. |
| `ordinary-enter-reload` | After Enter saving and a real reload, the complete expected storage and every note's editor values remain intact. |
| `brand-consistency` | A reviewer reads DESIGN.md and active tokens/components, then visually inspects the rendered result for preserved brand roles and justified exceptions. |
| `narrow-keyboard-review` | A reviewer inspects a 375px rendered screenshot with long Korean input/error text and exercises keyboard access to search/editor/save with visible focus and readable feedback. |

The first twelve checks are executable browser observations. The last two are
read-only quality reviews of the agent's result: reviewers do not repair product
code during scoring. Keep exact observed failures instead of averaging them away.
The browser check uses a bounded 150ms wait for this fixture's 30ms local save;
record slow/incomplete execution rather than inventing an observation. Synthetic
composition events test application handlers, not actual OS/browser IME ordering.
Storage comparisons check the full record count, unique numeric IDs, and all
expected title/body values; record order is not significant. Expected snapshots
come from evaluator-owned seed data and edits, not the candidate's saved output.
Record real IME, assistive technology, and other platform gaps separately in the
trial notes; do not upgrade the bounded checks to those broader claims.

## Result JSON contract (schema 1)

- `schema`: integer `1`; `suite`: `search-editor-v2`.
- `run_id`: distinct lowercase identifier for each run; `variant`: `baseline` or
  `candidate` as appropriate to the comparator argument.
- `fixture`: `{ "id": "search-editor", "sha256": "<initial-fixture-digest>" }`.
- `task_sha256`: digest of the identical `TASK.md` bytes supplied to both agents.
- `model`: actual common model identity. `settings`: nonempty object of actual
  runtime settings (finite number, boolean, or nonempty string values). Record
  inheritance as such when the runtime exposes only inheritance; do not invent
  temperature, seeds, or hidden settings.
- `skill_revision`: exact source revision or other attributable snapshot identifier
  for that lane. It is expected to differ between lanes.
- `cases`: `[{ "id": "search-editor", "checks": [...] }]`.
- Each check has `id`, `kind` (`behavior`/`quality` as fixed by the suite), and
  `status` (`pass`, `fail`, `not-run`). Pass/fail require `evidence` containing
  concrete observed `text`, a `path`, or both. Paths are relative to the result JSON,
  must name nonempty files inside that directory, and are never read by the
  comparator. `not-run` requires a concrete `reason`.

Use SHA-256 over each initial fixture file in sorted relative-path order: append
the UTF-8 relative path, a NUL byte, its bytes, then a NUL byte to the digest. Include
all five tracked fixture files, including `TASK.md`. For example, before agent edits:

```bash
python3 - <<'PY'
from pathlib import Path
import hashlib
root = Path('evals/fixtures/search-editor')
h = hashlib.sha256()
for path in sorted(p for p in root.rglob('*') if p.is_file()):
    h.update(path.relative_to(root).as_posix().encode() + b'\0')
    h.update(path.read_bytes() + b'\0')
print('fixture:', h.hexdigest())
print('task:', hashlib.sha256((root / 'TASK.md').read_bytes()).hexdigest())
PY
```

`examples/result-template.json` is intentionally incomplete and contains placeholder
metadata. It is a writing template, **not execution evidence**; the comparator
rejects it until real metadata and observations replace the placeholders. A valid
schema does not prove that evidence is truthful. The independent reviewer remains
responsible for checking artifacts, logs, and the stated observation scope.
Version 1 records cannot establish a version 2 pass. Even if their suite name is
updated, omitting any of the four new storage/reload checks invalidates the record;
mark genuinely unexecuted checks `not-run` with a concrete reason instead.

Exit codes: `0` = candidate passes all required checks with a complete baseline;
`1` = candidate has observed failures; `2` = invalid/incomparable records; `3` =
some required checks were not run and no candidate failure was observed. Concrete
candidate failures take priority over missing observations, and the verdict keeps
both failures and unexecuted checks visible. Improvements are individual
`fail → pass` checks, not a score.
These fixtures, checks, and development tools are not installed skill payloads.

## Optional installed-Chrome driver

With Node 22+ and an existing Chrome installation, run:

```bash
node scripts/run_browser_checks.mjs /tmp/baseline-fixture /tmp/evidence/baseline
node scripts/run_browser_checks.mjs /tmp/candidate-fixture /tmp/evidence/candidate
```

Set `AI_SLOP_CHROME` to the exact browser executable when detection does not apply.
The driver creates a temporary browser profile and a loopback-only server, seeds
synthetic notes, runs all twelve external checks with actual page reloads, and
records 1280px, 375px error-state, and keyboard-focus images. It seeds again before
collecting the narrow error-state images so a broken save cannot prevent that
separate observation. Each check's evidence retains its expected/observed records.
Read `browser.json` and actually inspect the images before writing the two quality
verdicts. Exit zero means evidence collection finished, not that every check passed;
use the comparator as the result gate. It installs no browser or packages and does
not connect to the user's existing browser profile.

To verify the checker itself, opt in to the dependency-free Chrome regression
tests (ordinary Python discovery skips them):

```bash
AI_SLOP_BROWSER_TESTS=1 python3 -m unittest discover -s tests -p test_browser_checks.py -v
```

These tests copy the flawed fixture to temporary directories, repair only its
intended defects for a passing control, and inject data loss, unrelated content
changes, duplicate IDs, hard-coded id 1 updates, failed-save writes, and reload
regressions. Assertions consume actual `browser.json` observations. The original
fixture remains unchanged and must still expose its intended failures. Set
`AI_SLOP_BROWSER_EVIDENCE` to a directory to retain each run's browser JSON and
images; otherwise the temporary evidence is deleted. Passing these sensitivity
tests establishes neither visual quality nor a model/skill comparison.
