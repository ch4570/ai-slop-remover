# Changelog

## 2.0.0 — 2026-09-07

- Publish as `ai-slop-remover-skills` with an `ai-slop-remover` executable for npx. The CLI reuses the bundled Python 3.9+ installer and adds no npm runtime dependencies or postinstall hooks.
- Add AI Slop Remover and five independent specialists for diagnosis, visual refinement, interaction, writing, and verification.
- Preserve `ui-craft-bundle` and reuse its platform references.
- Install all skills or selected skills with dependencies. Project install now defaults to seven skills; `--dest` keeps the original single-skill meaning.
- Support Git checkouts and exported ZIPs with hash validation, conflict preflight, and regression tests.
- Add release tooling and behavioral cases; package checks are separate from actual agent/UI trials.

## 1.0.0

- Original portable UI Craft Bundle with design, interaction, motion, platform, and verification guidance.
