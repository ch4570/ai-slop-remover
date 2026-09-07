---
title: Selecting a visual correction within scope
source: ../../../ui-craft-bundle/references/art-direction.md
last_fetched: 2026-09-07
skills: [ui-visual-refine]
---

# Hierarchy within scope

The shared [art-direction reference](../../../ui-craft-bundle/references/art-direction.md) starts with structure and realistic content. [Web layout guidance](../../../ui-craft-bundle/references/web.md) and [native guidance](../../../ui-craft-bundle/references/native.md) own platform details. `last_fetched` records the local source read, not verified rendering.

| Request boundary | Suitable first correction | Evidence to preserve |
| --- | --- | --- |
| One cramped gap | Reuse a nearby spacing token in the affected component | Wrapping, focus outline, adjacent alignment |
| Competing actions | Reuse primary and secondary treatments | Every action remains available and named |
| Hard-to-compare objects | Align shared fields or use a comparison structure when authorized | Domain fields, object identity, actions, reading order |
| Generic full-screen layout | Prioritize actual work and meaningful domain relationships | Brand, existing navigation, required states |
| Long localized text | Allow suitable wrapping and content-driven layout | Full action/error meaning and control access |

Structural changes can affect keyboard order and responsive access even when the visual intent is cosmetic. Check those outcomes when affected. Avoid adding behavior changes to a narrowly requested style correction.

## 리뷰 훅

- [ ] Does the edit address the observed issue using the smallest viable scope?
- [ ] Are brand tokens and existing primitives reused?
- [ ] Are meaningful object relationships and actions preserved?
- [ ] Was Korean or other supported long text checked where relevant?
- [ ] Are visual observations distinguished from source-only assumptions?
