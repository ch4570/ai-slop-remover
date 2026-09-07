# Observed UI evaluations

`skill-cases.json` is a scenario catalog. Package validation confirms its structure
and routes; it does **not** execute an agent or establish improved UI quality.
The runnable `search-editor-v3` suite and four bounded scope suites exercise
observable outcomes in small local UIs. They do not assign a beauty score.

The [2026-09-07 scope record](records/2026-09-07-scope-v1/README.md) retains
16 actual native executions, eight paired comparisons, readable diffs, and a
checksummed archive with pinned replay tools. Its synthetic harness controls are
recorded separately. The record documents a corrected parent-authored tool digest
and retains the original metadata; no agent run was replaced by that correction.

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
   - Seed, reload, and reinject again. Retain `await prepareSearchHistory()` as
     `entries`. It creates three same-document entries: all notes, `고객`, and
     `배송 확인`. Append `await evaluateHistoryTraversal('history-back', snapshot,
     'back', [entries[1], entries[0]])`, then the corresponding `history-forward`
     observation with `'forward', [entries[1], entries[2]]`. Each traversal calls
     real `history.back()` or `history.forward()` and waits for a trusted
     `popstate` from the expected entry. Both intermediate and final states count.
   - Navigate the same isolated tab directly to `/?q=긴%20한국어` and wait for a
     new document to finish loading. Reinject and append
     `observeQueryRestoration('query-direct-entry', snapshot, '긴 한국어')`.
     Reload that URL, wait for the new document, reinject, and append the same
     observation with ID `query-reload`. Keep the snapshot outside the page and
     do not rewrite its query input before either observation. Return to the
     fixture origin before collecting the separate narrow-screen evidence.

   Each save mode starts from the same seeded snapshot to keep a prior failure
   from masking later controls. Reload checks run **before** the next seed and
   inspect both stored records and the title/body opened from every listed note.
   Missing/duplicate note buttons yield failed observations. Preserve completed
   observations and console errors; a runner exception makes unexecuted checks
   `not-run` with the error as the reason, never pass.
   The installed driver records navigation/observation errors as `not-run` with
   their reasons and continues the independent checks. A concrete observed state
   mismatch remains `fail`; subsequent reloads and seeds do not erase it.
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
| `query-history` | Three rapid input events keep history length stable and, after a bounded settle, retain the final query consistently in the URL, input, matching records, and result count. |
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
| `history-back` | Two actual Back traversals complete with trusted popstate events at the expected entries; URL, input, matching records, and result count agree at both destinations. |
| `history-forward` | Two actual Forward traversals complete with trusted popstate events at the expected entries; URL, input, matching records, and result count agree at both destinations. |
| `query-direct-entry` | Direct navigation to a shared URL restores its query, matching records, and result count in a newly loaded document. |
| `query-reload` | Reloading that shared URL restores the same complete search state in another newly loaded document. |
| `brand-consistency` | A reviewer reads DESIGN.md and active tokens/components, then visually inspects the rendered result for preserved brand roles and justified exceptions. |
| `narrow-keyboard-review` | A reviewer inspects a 375px rendered screenshot with long Korean input/error text and exercises keyboard access to search/editor/save with visible focus and readable feedback. |

The first sixteen checks are executable browser observations. The last two are
read-only quality reviews of the agent's result: reviewers do not repair product
code during scoring. Keep exact observed failures instead of averaging them away.
The browser check uses a bounded 150ms wait for this fixture's 30ms local save;
record slow/incomplete execution rather than inventing an observation. Synthetic
composition events test application handlers, not actual OS/browser IME ordering.
Rapid typing is observed after 150ms. Each history traversal waits up to 1000ms
for a trusted `popstate`, verifies the evaluator-owned entry and URL, then waits
50ms for app handlers before reading state. A wrong destination or observed state
mismatch fails. If state matches but completion cannot be observed, the check is
`not-run` with a concrete reason and the partial observations. Synthetic `popstate`
dispatch cannot complete this wait. These bounds cover the small local fixture,
not arbitrary network or long-debounce applications.
History includes all-notes and filtered states so stale lists and counts are
observable in both directions. Shared-URL checks use a body-only Korean match.
The query observations match exact record sets through unique seeded titles and
the title/body opened from each list button; the fixture exposes no numeric IDs
in its DOM. They compare the visible numeric count as well as the button count.
Storage comparisons check the full record count, unique numeric IDs, and all
expected title/body values; record order is not significant. Expected snapshots
come from evaluator-owned seed data and edits, not the candidate's saved output.
Record real IME, assistive technology, and other platform gaps separately in the
trial notes; do not upgrade the bounded checks to those broader claims.

## Result JSON contract (schema 1)

- `schema`: integer `1`; `suite`: `search-editor-v3`.
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
Version 1 and 2 records cannot establish a version 3 pass. Even if their suite name
is updated, omitting any required check invalidates the record, including the
four storage/reload checks added in v2 and the four history/shared-URL restoration
checks added in v3. Mark unexecuted checks `not-run` with a concrete reason instead.

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
synthetic notes, runs all sixteen external checks with actual Back/Forward,
direct shared-URL navigation, and page reloads, and
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
regressions. Search mutations remove popstate restoration, leave the list/count
stale, ignore query restoration on entry or reload, block trusted events while
dispatching synthetic replacements, make a shared document unavailable, and
overwrite the final query with a delayed earlier input. Assertions consume actual
`browser.json` observations, including incomplete checks that preserve observed
failures. The original
fixture remains unchanged and must still expose its intended failures. Set
`AI_SLOP_BROWSER_EVIDENCE` to a directory to retain each run's browser JSON and
images; otherwise the temporary evidence is deleted. Passing these sensitivity
tests establishes neither visual quality nor a model/skill comparison.

## Four bounded scope trials (suite version 1)

The four independent fixtures connect catalog cases to executable source and
browser observations. Each fixture has an immutable `TASK.md` beside `product/`.
Only product files within the TASK's explicit edit boundary go to an agent;
[suites](checks/scope-suites.json), collection tools, tests, and reviews remain
outside that boundary. The default comparator still uses `search-editor-v3` and
strict result schema 1; select one of these pinned suites explicitly with
`--suite <case>-v1`.

| Case / fixed task | Allowed edits | Source checks | Browser observations | Required independent review |
| --- | --- | --- | --- | --- |
| [narrow-spacing](fixtures/narrow-spacing/TASK.md) | `.actions` margin in `settings.css` | Exact declaration boundary, all other content/type/mode preserved | 16px spacing, brand, save state and reload | 375px layout and actual Tab focus |
| [audit-read-only](fixtures/audit-read-only/TASK.md) | None, including report files | Full inventory equality, including product root, symlinks, directories and modes | Actual order search/detail plus priority-relevant layout/focus evidence | Each diagnosis has location, observed issue, user impact, verification and bounded correction; task/accessibility issues precede taste |
| [empty-state-copy-only](fixtures/empty-state-copy-only/TASK.md) | Three Korean string values | Keys, per-string variables, unchanged HTML/ARIA and other locale; narrow known fabricated-action guard | No-match accessible name/tree, real search recovery, never-populated state and English preservation | Natural, truthful copy and matching visible/accessibility meaning; no nonexistent recovery promise |
| [master-page-consistency](fixtures/master-page-consistency/TASK.md) | Comparison cell `padding-block` and marked DESIGN exception | No shared edits; CSS rule in the exception equals actual declarations | Master keeps 16px, comparison uses 8–12px, both retain data/row actions and brand | Both rendered pages, focus, and documented reason/scope agree |

The flat CSS parser accepts whitespace/comments and the task's bounded choices;
it does not require an exact patch. Source checks inspect declarations and
content, not just changed file counts. The copy guard rejects the known phrase
`필터 초기화 버튼을 눌러`; absence of that phrase is **not** a semantic verdict.
`truthful-copy-and-name` always requires the independent reviewer. The browser
records AX names without claiming that string matching proves meaning or actual
screen-reader behavior. A final unchanged inventory does not prove that no
intermediate write occurred when full tool transcripts are unavailable.

Prepare a **new** trial directory, then collect external evidence after its agent
finishes. All commands below run from the source repository:

```bash
python3 scripts/check_scope.py prepare narrow-spacing /tmp/trial-a
node scripts/run_scope_checks.mjs narrow-spacing /tmp/trial-a/product /tmp/trial-a
python3 scripts/check_scope.py collect narrow-spacing /tmp/trial-a
python3 scripts/compare_evals.py /tmp/trial-a/result.json /tmp/trial-b/result.json --suite narrow-spacing-v1
python3 scripts/summarize_scope_trials.py /tmp/scope-trials/manifest.json --output /tmp/scope-trials/summary.json
```

`prepare` writes `product/`, sibling `TASK.md`, `prepare.json` and
`before-manifest.json`. The initial fixture digest includes TASK and product files
using the sorted relative-path/NUL/bytes/NUL procedure above. Keep that original
snapshot and evaluator/tool snapshots outside agent edit scope. Freeze and hash
them before native launches; do not tune checks after reading trial outputs.

The parent writes `invocation.json` with actual `run_id`, `variant`, `model`,
`settings` and `skill_revision`. Other raw metadata can remain in that sidecar;
result schema 1 admits no new top-level fields. Match the whole settings object
across all 16 trials, including `invocation_mode: "snapshot-direct"`, common
prompt-template and tool-contract SHA-256 values. Record inherited model/settings
as inherited when hidden values are unavailable. Put variant-specific paths,
native IDs, timestamps, revision and skill-tree digests in sidecars/manifests,
not common settings. Pin baseline and candidate skills for both repetitions.

The browser driver writes `browser.json` and `images/wide.png`, `narrow.png`,
`keyboard.png`; the master case also writes `images/master-wide.png`. It uses the
same installed-Chrome transport as search-editor, fresh temporary profiles and
loopback-only synthetic products, without dependencies. Unavailable Chrome or
navigation writes required `not-run` observations. A concrete failure already
observed stays `fail` if later collection fails. Exit zero means collection was
recorded, not that checks passed. Ordinary Python discovery skips browser tests;
CI's Chrome job executes both search-editor and scope controls.

Store the actual final agent response in `agent-output.md`. A separate reviewer
reads source/diff/output/browser JSON and actually opens every required image,
then writes `review.md` and `review.json`, keyed by the suite's quality check ID:

```json
{
  "narrow-focus-review": {
    "status": "pass",
    "evidence": {"path": "review.md", "text": "Describe the actual reviewed layout and keyboard observation here."},
    "reviewed_images": ["images/wide.png", "images/narrow.png", "images/keyboard.png"]
  }
}
```

This example is a writing contract, not observed evidence. Use `fail` for actual
problems or `not-run` with a concrete `reason` for unobserved review. `collect`
requires nonempty final output and each required image plus the review's inspected
image list before accepting a quality pass. A concrete failure with valid review
evidence and final output stays fail when another required view is unavailable;
the missing coverage is recorded in its reason. It writes `source-checks.json`,
`after-manifest.json`, `diff.patch` and strict `result.json`. Empty read-only diffs
are valid; the nonempty inventory report is the check evidence. Evidence paths
remain inside their result directory. File existence and declared inspection do
not prove evidence truth; independent review is still required.

The summary consumes a schema 1 manifest with `repetitions: 2`, `trials`, and
`host_coverage`. Each trial entry has exactly `case`, integer `repeat` (1 or 2),
`variant`, `native_agent_id`, `result`, `launch`, and `output`. Artifact paths are
relative to the manifest and must stay inside its directory. Preserve raw native
launch requests/responses in `launch`; `request.fork_turns` must be `"none"` and
`response.task_name` must equal the manifest's actual canonical native context ID.
A reused agent/followup is not another repetition. Preserve actual final output,
diffs/inventories, environment/browser observations, inspected images and review
beside each result. When whole tool transcripts are unavailable, state that gap
instead of reconstructing them.

Record both `installed-host-explicit` and `automatic-discovery` in `host_coverage`
with `status: "not-run"` and concrete `reason` strings. Snapshot-direct observations
do not establish either host mode. `summarize_scope_trials.py` requires 16 distinct
contexts and eight complete matched pairs, checks common conditions across
repetitions, and reuses `compare()`. It exposes every pair's transitions and
missing/invalid records. A schema-valid candidate failure stays visible even if its own baseline or launch
metadata is absent. The comparison remains incomplete/invalid and reports no
regression or improvement from that pair. Concrete failures take priority over
incomplete coverage; otherwise missing required evidence is
`incomplete`. It never averages failures away or interprets two repetitions as a
general improvement in skill quality.

Run harness sensitivity controls separately from actual native trials:

```bash
python3 -m unittest discover -s tests -p test_scope_checks.py -v
AI_SLOP_BROWSER_TESTS=1 python3 -m unittest discover -s tests -p test_scope_browser_checks.py -v
```

The controls first establish passing source/browser products, then independently
introduce read-only writes, root symlinks, shared/local token mutations, lost
saved state, broken locale variables/ARIA links, the known fabricated recovery
instruction, mismatched DESIGN rules and unavailable observations. Set
`AI_SLOP_BROWSER_EVIDENCE` to retain their source reports, patches, browser JSON
and images. They remain synthetic harness tests, never part of the 16 native
trials. Keep real repeated run evidence under a source-only `evals/records/`
directory (or compact reproducible archive with readable patches/summaries);
do not expand npm payload files to include evaluation fixtures or records.
