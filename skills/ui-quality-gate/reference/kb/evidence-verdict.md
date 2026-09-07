---
title: Choosing a scoped verdict from evidence
source: ../../../ui-craft-bundle/references/verification.md
last_fetched: 2026-09-07
skills: [ui-quality-gate]
---

# Verdicts from evidence

The shared [verification reference](../../../ui-craft-bundle/references/verification.md) requires observable results, actual image inspection, and calibrated claims. [Native guidance](../../../ui-craft-bundle/references/native.md) explicitly separates previews and web mockups from native interaction evidence. `last_fetched` records the local source read, not a successful QA run.

| Evidence available | Supported conclusion | Unsupported conclusion |
| --- | --- | --- |
| Source review | Implementation appears to handle the inspected branch | The user journey ran successfully |
| Build/type check | The named command passed in its environment | The UI looks correct or keyboard access works |
| Opened screenshot | The inspected state at that viewport has the recorded appearance | Save persists or a touch action works |
| Outcome test | The asserted result occurred under stated data and environment | Untested failures, devices, or external services also work |
| Native preview | The preview shows its captured layout | Device input, back, accessibility services, or recreation were exercised |
| Missing runtime | Available checks have bounded results and remaining gaps | Full visual or behavior pass |

A concrete failed essential action yields `changes-required` even if the design looks polished. If a required runtime check is unavailable and no concrete defect is demonstrated, use `incomplete`. `pass` requires the actual checks selected for the bounded change; it does not require proving unrelated functionality.

For repeatable evidence record route/component, viewport/device, data/state, action, expected result, observed result, artifact or output, and limitation. Never promote copied, discovered, dry-validated, or user-reported evidence into independently executed proof.

## 리뷰 훅

- [ ] Does each completion claim name supporting evidence and its scope?
- [ ] Were images actually inspected and interactions asserted by outcomes?
- [ ] Are concrete blockers separated from optional polish and evidence gaps?
- [ ] Are native, emulated, supplied, and independently executed results labeled correctly?
- [ ] Does the verdict avoid source edits, live-data mutation, deployment, and fabricated success?
