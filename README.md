# AI Slop Remover

A skill set for clear, calm, user-friendly product interfaces. Diagnose generic UI, improve visual hierarchy, make interactions predictable, write useful microcopy, and verify real outcomes.

[한국어 안내 및 사용 예시](README.ko.md)

| Skill | Responsibility |
| --- | --- |
| `ai-slop-remover` | Coordinate a scoped improvement from diagnosis to verification |
| `ui-slop-audit` | Read-only diagnosis with evidence and user impact |
| `ui-visual-refine` | Layout, hierarchy, density, typography, and responsive detail |
| `ux-flow-refine` | Feedback, motion, interaction states, and failure recovery |
| `ux-writing` | Action labels, instructions, errors, and empty states |
| `ui-quality-gate` | Read-only verification of the implemented journey |
| `ui-craft-bundle` | Original workflow and shared web/native references |

Preserve the product's brand and stack. Remove friction and unnecessary decoration when they interfere with the task; do not ban colors, fonts, or cards by category. This is not an AI-authorship detector or a universal aesthetic preset.

## Install

Python 3.9+; no third-party packages, API keys, or network downloads. Clone or download the repository and run from its root:

```bash
python3 install.py --list
python3 install.py --repo "/path/to/project" --agent codex --dry-run
python3 install.py --repo "/path/to/project" --agent codex
```

Codex destination: `.agents/skills/`. Use `--agent claude` for `.claude/skills/`. Refresh or restart the host as required for discovery; copying files does not prove runtime discovery or execution.

Select a specialist and its shared references with repeatable `--skill`:

```bash
python3 install.py --repo "/path/to/project" --agent codex --skill ux-writing
```

The default installs all seven skills. Selecting `ai-slop-remover` includes the full set. Existing identical installations are left alone; changed or unowned directories are refused before new skills are copied. Review and move old installations to a backup location before updating. Nothing is overwritten automatically.

The legacy exact-directory command installs standalone UI Craft Bundle:

```bash
python3 install.py --dest "/path/to/skills/ui-craft-bundle"
```

Use project mode for dependency-bearing skills. Project code, `AGENTS.md`, `CLAUDE.md`, and global settings are unchanged. Release hashes detect edited files, not publisher identity. Git metadata and developer tooling are outside the installed payload.

## Use

```text
$ai-slop-remover
Make this search screen clearer and easier to use.
Preserve our brand and existing behavior. Inspect the current screen first.
Improve the friction you identify, then check the primary task,
small-screen layout, keyboard use, and relevant failure states.
Distinguish what you implemented from what you actually tested.
```

Call a specialist for narrower work. Use the host's selector or equivalent invocation if dollar syntax is unavailable; Claude Code uses slash invocations such as `/ai-slop-remover`.

Figma, external design skills, and animation libraries are optional. Running and inspecting a product requires its development environment and authorized browser/device tools.

## Maintain

Run these commands from a source checkout. The exported ZIP contains the installer, skills, and user documentation; it omits development scripts and tests.

```bash
python3 -m unittest discover -s tests -v
python3 scripts/update_manifest.py --check
python3 scripts/check_package.py
python3 scripts/export_bundle.py --output dist/ai-slop-remover.zip
```

After intentional release-file edits, run `python3 scripts/update_manifest.py`, review the hashes, and rerun the checks. Export validates first and creates an offline ZIP containing manifest-listed release files.

[Behavioral cases](evals/skill-cases.json) specify observable expectations for agent trials. Validating their structure is not an executed benchmark. See [verification scope](docs/verification.md).

Original instructions and code use [MIT](LICENSE). External resources are linked, not vendored. The [Agent Skills specification](https://agentskills.io/specification) informs the package format; specialist boundaries are this project's design choice.
