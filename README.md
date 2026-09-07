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

These commands follow the default branch and require repository access. Remove `--dry-run` to install. After `lutriva@2.2.0` is published to npm, the shorter command will be:

```sh
npx lutriva@2.2.0 --repo "/path/to/project" --agent codex
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
| [`ui-visual-refine`](skills/ui-visual-refine/SKILL.md) | Hierarchy, layout, density, type, and responsive detail |
| [`ux-flow-refine`](skills/ux-flow-refine/SKILL.md) | State, feedback, motion, and failure recovery |
| [`ux-writing`](skills/ux-writing/SKILL.md) | Action labels, instructions, errors, and empty states |
| [`ui-quality-gate`](skills/ui-quality-gate/SKILL.md) | Read-only checks of the implemented journey |
| [`ui-craft-bundle`](skills/ui-craft-bundle/SKILL.md) | Integrated workflow and shared web/native references |

Shared references keep the work coherent: [design memory](skills/ui-craft-bundle/references/design-memory.md) connects `DESIGN.md` to real tokens and components; [pattern selection](skills/ui-craft-bundle/references/pattern-selection.md) starts with the user's task; [eight interaction recipes](skills/ui-craft-bundle/references/interaction-recipes.md) cover input and navigation details. A [component specimen](skills/ui-craft-bundle/assets/component-specimen.md) checks shared changes before they spread to other screens.

Selected ideas from UI UX Pro Max, Vercel, and getdesign.md inform the workflow. [Sources and adoption boundaries](skills/ui-craft-bundle/references/sources.md).

## Check the work

Version 2.1's bounded comparison found **no observed regression**: both the existing and revised guidance produced implementations that passed eight browser behavior checks and scoped visual/keyboard review. That single pair does not establish a general improvement in UI quality. [Full verification record](docs/verification.md).

The source includes 19 [behavioral case contracts](evals/skill-cases.json), a deliberately flawed synthetic UI, external browser checks, and a result comparator. Case validation is a static check; an executed trial needs separate evidence. Maintainers can follow `evals/README.md`. Developer evaluation tools are excluded from the installed skills.

<details>
<summary>Contributor checks and portable export</summary>

Run from a source checkout:

```sh
python3 -m unittest discover -s tests -q
npm test
npm run check
python3 scripts/export_bundle.py --output dist/lutriva-2.2.0.zip
npm pack --dry-run
```

After intentional release-file edits, run `python3 scripts/update_manifest.py`, review the hashes, and rerun the checks. Export validates first, then creates a new offline ZIP with the installer, skills, and user documentation. Git metadata, development scripts, and tests are excluded.

The optional `scripts/run_browser_checks.mjs` requires an existing Chrome installation and Node 22+. It installs no dependencies. See `docs/npm-release.md` for registry publication steps.

</details>

## Project notes

[Name & artwork](docs/naming.md) · [Changelog](CHANGELOG.md) · [Verification](docs/verification.md) · [MIT license](LICENSE)

Original instructions and code use MIT. The banner's generation notes are in [assets/README.md](docs/assets/README.md). External skill sources, fonts, and icons are not bundled. The [Agent Skills specification](https://agentskills.io/specification) informs the package format.
