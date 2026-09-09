<p align="center">
  <img src="docs/assets/lutriva-hero.png" alt="Lutriva — an ivory river otter moving through a flowing jade current" width="100%">
</p>

# Lutriva

[English](README.md) · [한국어](README.ko.md)

**Interfaces, at ease.**

Lutriva gives **Codex and Claude Code** seven skills for making product interfaces clearer and easier to use. Find the friction, refine the screen, preserve the user's flow, and check the result in the actual product.

**7 skills · Web & native guidance · Codex / Claude Code · MIT**

Formerly **AI Slop Remover**. The river otter represents the experience we aim for: purposeful movement with less friction. [The name and compatibility map](docs/naming.md).

[Quick start](#quick-start) · [Try it](#give-it-a-real-task) · [Skills](#choose-your-scope) · [Design approach](#what-good-feels-like) · [Evidence](#check-the-work)

## What good feels like

- **A screen with a clear purpose.** Hierarchy, density, and words help people find their next action.
- **A flow that holds together.** Input responds, focus stays predictable, and failed saves keep the draft.
- **A product that stays itself.** Existing brand, tokens, components, and page exceptions guide the change.
- **An outcome you can inspect.** Implementation, visual observation, and behavior checks are reported separately.

Start with the task and the existing screen. A spacing fix should stay a spacing fix; a product redesign can go deeper. Colors, cards, and fonts are judged in context.

### Methods and shared UX principles

[Fourteen anti-slop methods](skills/ui-craft-bundle/references/anti-slop-methods.md) connect **symptom → intervention → preservation and recheck**. All seven skills route to this catalog and the [web/mobile UX foundations](skills/ui-craft-bundle/references/ux-foundations.md) only when the task needs them.

| Observed problem | Useful intervention |
| --- | --- |
| Large introductions and repeated cards displace work | Put the task first; choose structures for comparison or browsing |
| Every button and badge competes for attention | Assign emphasis, meaningful groups, and type/spacing roles |
| Changing the industry name leaves the same screen | Express real data relationships, units, vocabulary, and brand |
| Many options obscure the current selection | Keep frequent actions and current state visible; disclose secondary options |
| Icons and toasts carry all the meaning | Use recognizable controls, contextual feedback, and state-specific copy |
| Errors discard input and context | Reduce re-entry, retain drafts, and provide supported edit/cancel/recovery |
| Mobile is a shrunken desktop | Adapt structure; check targets, keyboard access, large text, and localization |
| Only animations and sample data make it look finished | Remove unnecessary waiting; check reduced motion and realistic edge states |

Shared principles cover recognition, consistent terms and location, hierarchy, user control, error prevention/recovery, and accessible input. WCAG 2.2 criteria remain distinct from Apple and Android recommendations, including their units and exceptions. The guidance draws on NN/G, W3C, Apple, Android, and GOV.UK; [sources and adoption boundaries](skills/ui-craft-bundle/references/sources.md) explain the scope. A color or card is not a defect by itself.

For weak palettes or awkward placement, [color composition](skills/ui-craft-bundle/references/color-composition.md) connects semantic color pairs with neighboring surfaces, occupied area, and emphasis. [Layout composition](skills/ui-craft-bundle/references/layout-composition.md) turns the task into content widths, alignment anchors, grouped spacing, and responsive arrangements. The visual skill checks them together in the actual page, preserving the product's brand rather than imposing a fixed palette or grid.

[Eight design articles from the official Toss technology blog](skills/ui-craft-bundle/references/toss-design.md) also inform the skills: predictable Korean copy, keyboard-aware forms, non-drag operation, meaningful motion, mobile/desktop structure, component extensions and specifications, and early usability validation. Each case separates the author's observations from the proposed application and recheck, with routes from the relevant workflows.

## Quick start

The npm registry release is **pending**. Use a source checkout now; access to this repository is required while it is private. The Python installer needs **Python 3.9+**, with no third-party packages or API keys.

```sh
git clone https://github.com/ch4570/lutriva.git lutriva
cd lutriva
python3 install.py --repo "/path/to/project" --agent codex --dry-run
python3 install.py --repo "/path/to/project" --agent codex
```

Replace the example path with an existing project. Use `--agent claude` for Claude Code. The default installs all seven skills and their shared references.

| Host | Skill directory |
| --- | --- |
| Codex | `.agents/skills/` |
| Claude Code | `.claude/skills/` |

In Codex, start with `$ai-slop-remover`; in Claude Code, `/ai-slop-remover`.

Refresh skill discovery or restart the host after installation. **Install in the terminal; send task prompts inside Codex or Claude Code.** Choose the host's skill selector if it uses a different invocation format.

<details>
<summary>npm CLI and installation options</summary>

The npm package and preferred command are `lutriva`. The npm wrapper requires **Node.js 20+ and Python 3.9+**. Run the repository version with npm and Git before registry publication:

```sh
npx --yes --package='git+https://github.com/ch4570/lutriva.git' -- lutriva --list
npx --yes --package='git+https://github.com/ch4570/lutriva.git' -- lutriva --repo "/path/to/project" --agent codex --dry-run
```

These commands follow the default branch and require repository access. Remove `--dry-run` to install. After `lutriva@2.4.0` is published to npm, the shorter command will be:

```sh
npx lutriva@2.4.0 --repo "/path/to/project" --agent codex
```

The same package also exposes the compatible `ai-slop-remover` CLI. Set `AI_SLOP_PYTHON` to an exact Python executable path when needed. There are no npm runtime dependencies or automatic postinstall steps.

Select individual skills from a checkout:

```sh
python3 install.py --list
python3 install.py --repo "/path/to/project" --agent codex --skill ux-writing
python3 install.py --repo "/path/to/project" --agent codex --skill ui-slop-audit --skill ui-quality-gate
```

Repeat `--skill` to combine specialists. Each selection includes its declared references; selecting `ai-slop-remover` includes the full set. The legacy exact-directory command installs standalone UI Craft Bundle:

```sh
python3 install.py --dest "/path/to/skills/ui-craft-bundle"
```

Use `--repo --agent` for skills that depend on sibling packages. Identical installations are left alone. Modified or unowned directories are refused before new skills are copied; review and move old installations to a backup location before updating. User files are never overwritten automatically.

Before reinstalling, inspect all selected skills and dependencies:

```sh
python3 install.py --repo "/path/to/project" --agent codex --status
```

The npm CLI accepts the same `--status` option. Add `--skill` to limit the selection, or use `--dest` for one standalone skill. The report shows each installation path, installed and release versions, and these states:

| Status | Meaning |
| --- | --- |
| `not installed` | The destination does not exist. |
| `identical installation` | The version, recorded files, and installed contents match. |
| `version only; skill contents identical` | Only the release version differs, as with unchanged skills from 2.1.0 to 2.2.0. |
| `release content changed` | The new release differs from the installation record. |
| `user modifications` | Local files differ from the installation record. |
| `release content changed; user modifications` | Both comparisons found changes, even if a local edit already matches the new release. |
| `unverifiable` | Ownership, the installation record, or safe file access could not be verified. |

Local and release changes list added, deleted, and modified relative file paths separately; extra empty directories are also listed. File contents are not printed. Existing installations that need attention include a path to review and back up before reinstalling. Damaged records, symlinks, and unsafe paths remain unverifiable while the report continues through the other skills.

`--status` preserves files and modification times, and returns exit code 0 after a complete report, including conflicts or unverifiable installations. Invalid arguments return 2; bundle verification or project lookup failures return 1. It cannot be combined with `--dry-run` or `--list`. `--dry-run` and actual installation still refuse version differences, edits, and unowned destinations; diagnosis never enables automatic updates or overwrites.

The installer leaves project code, `AGENTS.md`, `CLAUDE.md`, and global settings alone. The Python installer performs no network downloads. Hashes detect edited files; they do not authenticate the publisher. [Compatibility details](docs/naming.md#compatibility).

Characters a terminal cannot encode are escaped in path messages (for example, `\ud55c`). The actual Unicode path and installed file contents are preserved; the terminal's encoding is not changed.

</details>

## Give it a real task

Tell Lutriva who is using the screen, what they need to finish, and what must stay familiar.

```text
$ai-slop-remover
Improve this search screen for someone comparing several results.
Inspect it first. Preserve our brand and existing behavior.
Clarify hierarchy, filters, empty results, and failure recovery.
Check narrow screens, keyboard use, and the main journey.
Report what you changed and what you actually verified.
```

For focused work, call one specialist:

| Need | Prompt inside Codex |
| --- | --- |
| Keep work safe when saving fails | `$ux-flow-refine` — Preserve the draft and focus, show save status, and make retry predictable. |
| Make errors useful | `$ux-writing` — Rewrite the error and empty-state copy so people know what happened and what to do next. |
| Check a finished change | `$ui-quality-gate` — Inspect the main journey, keyboard flow, narrow layout, and relevant failure states. |

Claude Code uses `/` in place of `$`. The same workflow supports native projects: name the platform, its conventions, and the journey. Running a product or inspecting its screen needs the project's environment and authorized browser/device tools. Figma and external design tools are optional.

## Choose your scope

| Skill | What it owns |
| --- | --- |
| [`ai-slop-remover`](skills/ai-slop-remover/SKILL.md) | Connect diagnosis, scoped improvements, and verification |
| [`ui-slop-audit`](skills/ui-slop-audit/SKILL.md) | Read-only findings with evidence and user impact |
| [`ui-visual-refine`](skills/ui-visual-refine/SKILL.md) | Color composition, layout, hierarchy, density, type, and responsive detail |
| [`ux-flow-refine`](skills/ux-flow-refine/SKILL.md) | State, feedback, motion, and failure recovery |
| [`ux-writing`](skills/ux-writing/SKILL.md) | Action labels, instructions, errors, and empty states |
| [`ui-quality-gate`](skills/ui-quality-gate/SKILL.md) | Read-only checks of the implemented journey |
| [`ui-craft-bundle`](skills/ui-craft-bundle/SKILL.md) | Integrated workflow and shared web/native references |

Shared references keep the work coherent: [design memory](skills/ui-craft-bundle/references/design-memory.md) connects `DESIGN.md` to real tokens and components; [pattern selection](skills/ui-craft-bundle/references/pattern-selection.md) starts with the user's task; [eight interaction recipes](skills/ui-craft-bundle/references/interaction-recipes.md) cover input and navigation details. A [component specimen](skills/ui-craft-bundle/assets/component-specimen.md) checks shared changes before they spread to other screens.

Selected ideas from UI UX Pro Max, Vercel, and getdesign.md inform the workflow. [Sources and adoption boundaries](skills/ui-craft-bundle/references/sources.md).

## Spend tokens on the task

Specify the outcome, allowed scope, contracts to preserve, verification and stopping
condition. Choose the relevant specialist directly when the task is already clear:

```text
$ui-visual-refine
Fix only the gap above the settings form's Save button using the existing spacing token.
Preserve copy, brand and save behavior. Check the affected layout and keyboard focus.
Stop once that scoped defect is resolved; report the files and checks actually observed.
```

Load only relevant references, reuse unchanged context and valid checks, and use
scripts for search, hashes and test aggregation. Separate independent work only
when its benefit justifies startup, handoff and repeated context. A lower model
rate or faster parallel execution does not by itself prove a lower completion cost.

The source checkout includes `scripts/collect_usage.py` for **offline** collection
of explicitly supplied Codex JSONL traces and paired usage reports. It does not
launch models, scan personal session history or change quality results. It counts
failed attempts, retries and child usage; missing usage makes the task total
unavailable. Optional dated model-specific rates produce estimates, not subscription
invoices. Compare all attempted cost per quality-passing completion; never count
unknown usage as zero or claim savings from document length alone. See `evals/README.md`
in the source checkout for the sidecar contract and commands.

## Evaluate and improve locally

The [local learning gate](skills/ui-craft-bundle/references/local-learning.md) keeps the shared installation intact while each project develops small, conditional rules. A dependency-free Python CLI is included with `ui-craft-bundle`.

`Evidence → candidate → comparable trials → regression and transfer checks → local adoption → rollback on related failure`

- Equal baseline/candidate passes mean `no-change`, not improvement. Adoption requires observed improvement and preservation of required outcomes.
- Storage is `.lutriva/local/`, outside installed skill directories, with no automatic cross-project or cross-user propagation.
- Freeze a scoped candidate and comparison plan, submit evidence, then explicitly adopt an eligible version or roll back. Changed base files, policy, or active generation require a new candidate.

Follow the [CLI guide](skills/ui-craft-bundle/references/local-learning-cli.md) for `init`, `propose`, `evaluate`, `promote`, `rollback`, `status`, and `context`. The current `reviewed-local` workflow validates submitted records, evidence hashes, repeated improvement, regression checks, a distinct transfer fixture, and declared run/time limits. It cannot authenticate the observations or reviewer independence. Rules returned by `context` must be supplied explicitly with the task.

Model execution, automatic observation/adoption, host instruction injection, and enforced experiment isolation remain unimplemented. The [broader implementation contract](skills/ui-craft-bundle/references/local-learning-contract.md) separates these future capabilities from the current manual CLI.

## Check the work

The retained four-case evaluation records **16 fresh native contexts and eight paired comparisons**, with a `pass` verdict, 0 observed check regressions and 0 improvements. It uses two repetitions per case and snapshot-direct invocation; it does not establish general skill superiority or host discovery. [Recorded runs, patches, limitations and archive](https://github.com/ch4570/lutriva/blob/main/evals/records/2026-09-07-scope-v1/README.md).

The earlier version 2.1's bounded comparison found **no observed regression**: both the existing and revised guidance produced implementations that passed eight browser behavior checks and scoped visual/keyboard review. That single pair does not establish a general improvement in UI quality. [Full verification record](docs/verification.md).

The source includes 22 [behavioral case contracts](evals/skill-cases.json), a deliberately flawed synthetic UI, external browser checks, and a result comparator. Case validation is a static check; an executed trial needs separate evidence. Maintainers can follow the [evaluation procedure](https://github.com/ch4570/lutriva/blob/main/evals/README.md). Developer evaluation tools are excluded from the installed skills.

<details>
<summary>Contributor checks and portable export</summary>

Replay the retained scope comparison from a macOS/Linux source checkout (Python and standard archive tools; no new agent or browser run):

```sh
scope_replay="$(mktemp -d)"
tar -xzf evals/records/2026-09-07-scope-v1/evidence.tar.gz -C "$scope_replay"
python3 -B "$scope_replay/scope-v1/actual/snapshots/evaluator/scripts/summarize_scope_trials.py" \
  "$scope_replay/scope-v1/actual/manifest.json"
```

Run the contributor checks from the same checkout:

```sh
python3 -m unittest discover -s tests -q
npm test
npm run check
npm run check:js
python3 scripts/export_bundle.py --output dist/lutriva-2.4.0.zip
npm pack --dry-run
```

After intentional release-file edits, run `python3 scripts/update_manifest.py`, review the hashes, and rerun the checks. Export validates first, then creates a new offline ZIP with the installer, skills, and user documentation. Git metadata, development scripts, and tests are excluded.

`.github/workflows/ci.yml` runs on every pull request and push to `main`:

| Job | Node | Python | Checks |
| --- | --- | --- | --- |
| Ubuntu 24.04 | 20 | 3.9 | Minimum supported runtimes; full Python suite, npm tests, release and syntax checks |
| macOS 15 | 22 | 3.13 | Same checks on a representative macOS combination |
| Windows 2025 | 22 | 3.13 | Same checks, including actual npm command shims and filesystem behavior |
| Ubuntu 24.04 + existing Chrome | 22 | 3.13 | Opt-in browser regression tests; retained evidence artifacts |

The three runtime jobs explicitly report browser suites as skipped; the separate Chrome job executes both search-editor and scope controls. The Python suite includes fresh Git clones with both `core.autocrlf=false` and `true`, hash checks and installs. The npm suite creates a real tarball, installs it offline, executes both command aliases, and tests Python selection, paths with spaces, dry-run and identical reinstall. CI pins `AI_SLOP_PYTHON` to the selected setup-python executable; a separate case also exercises automatic discovery. Tests that need symlinks require symlink privileges, including Developer Mode or elevation on Windows; CI does not suppress those failures.

On Windows, use the selected `python` executable for the Python commands. These are the equivalents of the first and third checks above:

```sh
python -m unittest discover -s tests -v
python scripts/update_manifest.py --check
python scripts/check_package.py
```

The browser driver requires an existing Chrome installation and Node 22+. To reproduce its CI job on macOS or Linux:

```sh
AI_SLOP_BROWSER_TESTS=1 python3 -m unittest discover -s tests -p test_browser_checks.py -v
AI_SLOP_BROWSER_TESTS=1 python3 -m unittest discover -s tests -p test_scope_browser_checks.py -v
```

Set `AI_SLOP_CHROME` to the browser executable if automatic detection fails, and `AI_SLOP_BROWSER_EVIDENCE` to retain evidence outside the temporary directory. Missing Chrome or failed observations fail the browser job. All checks use built-in runtime modules and install no project dependencies. Model-calling comparisons remain a separate, manual maintainer workflow in `evals/README.md`; CI does not claim model quality, visual review or actual OS IME coverage. See `docs/npm-release.md` for registry publication steps.

</details>

## Project notes

[Name & artwork](docs/naming.md) · [Changelog](CHANGELOG.md) · [Verification](docs/verification.md) · [MIT license](LICENSE)

Original instructions and code use MIT. The banner's generation notes are in [assets/README.md](docs/assets/README.md). External skill sources, fonts, and icons are not bundled. The [Agent Skills specification](https://agentskills.io/specification) informs the package format.
