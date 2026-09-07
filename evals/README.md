# Observed UI evaluations

`skill-cases.json` is a scenario catalog. Package validation confirms its structure
and routes; it does **not** execute an agent or establish improved UI quality.
The separate, runnable `search-editor-v1` suite exercises observable outcomes in a
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
5. In a real browser, inject `checks/search-editor.js`, then run
   `await evaluateSearchEditor()`. Save the returned checks and console errors.
   Then call `prepareOrdinaryEnter()`, press a real browser Enter key (or use the
   browser automation keyboard API), wait for the local save to settle, and append
   `observeOrdinaryEnter()` to the results. Do not use a synthetic DOM key event for
   this positive control; it must exercise native form submission too.
   Run once per fresh fixture origin: the checks edit and save synthetic notes and
   alter search/history. A runner exception means the affected checks are `not-run`
   with the error as the reason; it never means pass.
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
| `retry-persists` | Retrying the preserved draft writes its actual title/body to localStorage. |
| `composition-enter` | Synthetic composition Enter causes no submit and no persistence mutation. |
| `ordinary-save` | Ordinary save still writes the intended note. |
| `ordinary-enter` | Real browser Enter on the title input still saves the intended note after composition has ended. |
| `brand-consistency` | A reviewer reads DESIGN.md and active tokens/components, then visually inspects the rendered result for preserved brand roles and justified exceptions. |
| `narrow-keyboard-review` | A reviewer inspects a 375px rendered screenshot with long Korean input/error text and exercises keyboard access to search/editor/save with visible focus and readable feedback. |

The first eight checks are executable browser observations. The last two are
read-only quality reviews of the agent's result: reviewers do not repair product
code during scoring. Keep exact observed failures instead of averaging them away.
The browser check uses a bounded 150ms wait for this fixture's 30ms local save;
record slow/incomplete execution rather than inventing an observation. Synthetic
composition events test application handlers, not actual OS/browser IME ordering.
Record real IME, assistive technology, and other platform gaps separately in the
trial notes; do not upgrade the bounded checks to those broader claims.

## Result JSON contract (schema 1)

- `schema`: integer `1`; `suite`: `search-editor-v1`.
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
The driver creates a temporary browser profile and a loopback-only server, runs
external checks, and records 1280px, 375px error-state, and keyboard-focus images.
Read `browser.json` and actually inspect the images before writing the two quality
verdicts. Exit zero means evidence collection finished, not that every check passed;
use the comparator as the result gate. It installs no browser or packages and does
not connect to the user's existing browser profile.
