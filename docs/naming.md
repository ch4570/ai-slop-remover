# Lutriva · 루트리바

[English README](../README.md) · [한국어 README](../README.ko.md)

**Lutriva** is the project name for the skill set previously called **AI Slop Remover**. It is a coined name inspired by the river otter and a river's continuous movement. The name points to the product goal: interfaces that help people move through a task with less friction.

한국어 표기는 **루트리바**입니다. 수달과 강물의 흐름에서 착안한 이름입니다. 화면의 장식을 덜어내는 데서 출발해, 사용자가 입력하고 이동하고 복구하는 과정 전체를 편하게 만든다는 뜻을 담았습니다.

**English:** Interfaces, at ease.

**한국어:** 덜 헤매고, 더 자연스럽게.

## Visual identity

![Lutriva river otter banner](assets/lutriva-hero.png)

The ivory otter and jade current are one continuous composition. The figure gives the project a recognizable identity; the quiet layout leaves room for the actual product explanation. Both README languages share the same banner and retain their key message as accessible text below it.

| Element | Direction |
| --- | --- |
| Project name | `Lutriva` in prose; `LUTRIVA` in artwork |
| Mascot | An original illustrated river otter moving with the current |
| Background | River ink `#102B2B` |
| Figure and primary text | Bone ivory `#F1ECDF` |
| Accent | Muted jade `#78BAA0` |
| Secondary detail | Pale brass `#CAB788` |
| Composition | Generous space, clear hierarchy, one flowing gesture |
| Artwork | [Hero banner](assets/lutriva-hero.png), [generation notes](assets/README.md) |

These colors describe the art direction; individual pixels in the generated image vary. The palette belongs to this project's identity. It is not a preset that the skills should impose on other products.

## Compatibility

The project and CLI gain a new identity. Existing installed skills keep their names and behavior.

| Surface | Identity |
| --- | --- |
| Project name | Lutriva |
| npm package | `lutriva` — registry publication pending |
| Preferred CLI | `lutriva` |
| Compatible CLI | `ai-slop-remover`, provided by the same npm package |
| GitHub repository | `ch4570/lutriva` |
| Skill entry point | `$ai-slop-remover` in Codex; `/ai-slop-remover` in Claude Code |
| All seven skill IDs | Unchanged |
| Python selection | Existing `AI_SLOP_PYTHON` environment variable |
| Manifest set name and install receipts | Existing `ai-slop-remover` identifiers |
| Standalone bundle | Existing `ui-craft-bundle` identity and exact-directory install |
| License and history | Existing MIT attribution and versioned releases |

Both CLI names run the same bundled installer. The new name does not require renaming installed skill directories, changing prompts, or replacing receipts. The source filename `bin/ai-slop-remover.js` also stays stable.

이름만 바꾸려고 기존 스킬을 지우거나 다시 설치할 필요는 없습니다. 새 지침을 업데이트할 때도 기존 설치기의 파일 보호 규칙을 따릅니다. [설치 안내](../README.ko.md#빠른-시작).

If an older npm package providing `ai-slop-remover` is already installed globally, npm may report a command-name conflict when installing `lutriva`. Review the installed package before removing it; do not delete project skill directories to resolve a global npm executable conflict.

## Distribution

The package manifest targets `lutriva@2.2.0`. Neither `lutriva` nor the previous package name `ai-slop-remover-skills` had an npm registry entry when checked on 2026-09-07. Registry commands in the README are explicitly marked as pending. Use a source checkout or the Git-backed npm command for the current version; repository access is required while it is private.

The exact-name check is a point-in-time observation, not a name reservation. The repository URL now uses `ch4570/lutriva`; historical release files retain their existing names.
