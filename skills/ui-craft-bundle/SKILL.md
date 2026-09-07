---
name: ui-craft-bundle
description: Preserve the original UI Craft Bundle workflow and provide shared web/native design, interaction, motion, and verification references. Use when the user explicitly requests ui-craft-bundle or an existing workflow depends on its references. For a new broad AI-slop-removal request, prefer ai-slop-remover when installed; exclude backend-only work and standalone graphic design.
---

# UI Craft Bundle

Turn a user's product task into a distinctive, usable screen whose controls work. Optimize the usefulness and completeness of interaction, not its quantity. Load only the references needed for the current phase.

## Start from the product

- Inspect the current screen, nearby implementation, design tokens, navigation, data model, dependencies, and project instructions. Reuse existing conventions unless the user requests a redesign. Do not migrate a stack as a styling shortcut.
- Identify the user, immediate job, main content object, and primary action. Determine whether this is a marketing page, working product screen, or native app. Avoid turning a working application into a landing page.
- State a brief working direction and act. Infer reversible details; ask only when an unresolved choice would materially alter the product. Do not require approval of a mood board before ordinary implementation.
- Actually inspect supplied references. Extract hierarchy, density, layout, and interaction ideas; distinguish observation from inference. If images or a running screen are inaccessible, disclose that and proceed from available evidence.

## Route by requested work

| Work | Read |
| --- | --- |
| New screen or visual redesign | [art-direction.md](references/art-direction.md) |
| Reuse or update design decisions across screens | [design-memory.md](references/design-memory.md) |
| Choose a task-appropriate layout or density | [pattern-selection.md](references/pattern-selection.md) |
| Search, editing, selection, gestures, async actions | [interaction-design.md](references/interaction-design.md) |
| Fix a specific input, navigation, or feedback defect | [interaction-recipes.md](references/interaction-recipes.md) |
| Motion or feedback | [motion.md](references/motion.md) |
| Web implementation | [web.md](references/web.md) |
| Android, iOS, React Native, Flutter | [native.md](references/native.md) |
| Critique, completion, regression checks | [verification.md](references/verification.md) |
| Comparing or adding upstream skills | [sources.md](references/sources.md) |
| Compare skill versions on real UI tasks | [behavior-evaluation.md](references/behavior-evaluation.md) |

For a small fix, load only the relevant reference. For a substantial screen, work through direction, interaction, platform implementation, and verification. Do not load all references by default. Treat the repository's explicit design system and the user's choices as stronger context than generic aesthetic preferences from this or an optional upstream skill.

## Make decisions concrete

For substantial work, record a compact design contract in existing project documentation or working notes. Use [design-contract.md](assets/design-contract.md) when a durable handoff helps. A minor fix needs no new document.

Read the existing design record before choosing new values. Follow [design-memory.md](references/design-memory.md) to map semantic roles to actual code tokens, resolve document/code drift, and preserve justified page exceptions. Before applying a broad visual direction everywhere, inspect representative controls and states with [component-specimen.md](assets/component-specimen.md), preferably inside an existing preview surface.

- Name the main job, content structure, visual hierarchy, density, and deliberate visual signature.
- Choose a layout that supports the job: comparison table, editable list, timeline, workspace, reading surface, or another appropriate structure. Neither cards nor gradients are universally wrong; unexplained repetition is the problem.
- Use realistic domain content and edge cases. Label prototype data honestly. Do not invent customer logos, claims, prices, or integrations to make a screen look finished.
- Define observable behavior for visible controls in scope: trigger, resulting state, feedback, recovery, and persistence. Never satisfy a functional action with a cosmetic toast alone.

## Implement an end-to-end slice

Build the primary journey first, including data changes and relevant non-happy states. Connect existing APIs when available; for a local prototype, implement local behavior and disclose its persistence boundary. Keep an unavailable integration clearly unavailable instead of simulating success.

Use existing primitives and platform components. Add a dependency only when it solves a concrete behavior gap. Never install an animation framework just for button hover effects. Do not require Figma, paid services, an MCP server, or an upstream skill.

Preserve focus, keyboard and touch access, input values, and recovery from errors. Drag interactions need appropriate click/tap alternatives plus keyboard support on applicable platforms. Motion should explain state and respect reduced-motion preferences.

## Inspect the result

Read [verification.md](references/verification.md). Run the screen when supported; exercise the primary journey and actually inspect rendered images. Use the environment's authorized preview/test mechanism. This skill does not authorize external-site interaction, login, deployment, or unrelated changes.

Fix observed issues in order: broken task or inaccessible control, layout/hierarchy, then detail. Verify affected behavior after fixes. Stop when the scoped journey works and material limitations are documented; avoid endless cosmetic revisions or arbitrary score thresholds.

Report what changed, which interactions were exercised, actual verification evidence, and what remains unverified. Separate implemented, visually inspected, and behavior-tested claims. A build passing is not visual QA; a screenshot is not proof of interaction.

## Distribution and invocation

Use `$ui-craft-bundle` with a product task; use the host's skill selector or a plain-language request if dollar invocation is unavailable. This original entrypoint remains independently usable. Read [bundle-guide.ko.md](assets/bundle-guide.ko.md) for Korean usage and installation boundaries. Packaging tools belong to the source repository, not an installed skill directory.
