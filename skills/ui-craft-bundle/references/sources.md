# Research, upstream options, and provenance

## UI/UX research integrated in this bundle

The [anti-slop methods](anti-slop-methods.md) and [UX foundations](ux-foundations.md) were researched on 2026-09-07. They contain original decision aids and checks, with direct links beside the relevant guidance. Their practical examples are Lutriva's synthesis, not copied manuals or measured claims of improvement.

- Nielsen Norman Group's [usability heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/), [visual hierarchy](https://www.nngroup.com/articles/visual-hierarchy-ux-definition/), [common region](https://www.nngroup.com/articles/common-region/), and [progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/) inform task, grouping, emphasis, and complexity decisions. They do not prescribe an aesthetic preset or a fixed number of actions.
- GOV.UK's [notification guidance](https://design-system.service.gov.uk/components/notification-banner/) and [check-answers pattern](https://design-system.service.gov.uk/patterns/check-answers/) inform contextual feedback and review/edit recovery. Their service-specific layouts are not imposed on other products.
- The foundations reference separates linked W3C WCAG 2.2 criteria from Apple and Android platform recommendations, and pairs them with observable checks. An expert review or automated check alone does not establish accessibility conformance.

Read the reference relevant to the current design decision; using the bundle does not require retrieving all sources or installing external skills.

## Toss technology blog design research

[Toss design cases](toss-design.md) records eight official `toss.tech` articles inspected on 2026-09-07, with each original title, publication date, author, and direct URL. The cases cover Korean UX writing, keyboard-aware forms, accessible reordering, meaningful motion, mobile/desktop task context, component variation, specification order, and early task validation.

Each case separates the author's account from Lutriva's application and recheck. The guidance is connected to the relevant writing, flow, motion, pattern-selection, and design-memory references. Historical implementation workarounds and reported metrics are not current platform standards or expected results for another product. No Toss branding, source bodies, internal tools, or TDS packages are bundled.

## Optional upstream skills

Reviewed 2026-09-07. These are optional external resources, not bundled dependencies or an upstream source snapshot. The bundle's instructions and packaging code were written for this workflow; upstream skill text and tools are not vendored. Verify current upstream instructions before installing because behavior can change.

| Source / exact skill name | Use | Boundary |
| --- | --- | --- |
| [Impeccable](https://github.com/pbakaus/impeccable) / `impeccable` | Primary optional visual direction, critique, polish, adaptation | README currently describes one skill with subcommands. Choose this or frontend-design as visual lead; avoid combining competing style rules blindly. |
| [Anthropic frontend-design](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md) / `frontend-design` | Lighter alternative for bespoke frontend direction | Does not replace product-state implementation or actual interaction verification. |
| [Vercel web-design-guidelines](https://github.com/vercel-labs/agent-skills/blob/main/skills/web-design-guidelines/SKILL.md) / `web-design-guidelines` | Web code review for accessibility and interaction conventions | Fetches external [Web Interface Guidelines](https://github.com/vercel-labs/web-interface-guidelines/blob/main/command.md); not an offline browser test runner. |
| [Vercel React Best Practices](https://github.com/vercel-labs/agent-skills/blob/main/skills/react-best-practices/SKILL.md) / `vercel-react-best-practices` | React/Next performance work | Folder name differs from skill name. Do not apply to native Kotlin or unrelated frameworks. |
| [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) / `ui-ux-pro-max` | Optional searchable design and multi-stack reference, including Compose | Preserve project stack and avoid mechanically applying presets or requiring motion for every state. |

Recommendation: use this bundle for the end-to-end product workflow. If a visual specialist is desired, add Impeccable OR frontend-design for direction. Use web guidelines at review time and React guidance only for relevant performance work. UI UX Pro Max is a conditional reference, not a mandatory extra context load.

Respect user/project direction when upstream opinions conflict. Colors, fonts, cards, and animation durations are context-dependent; do not resolve differing advice by appending every prohibition.

## Guidance integrated in this bundle

The following pages were inspected on 2026-09-07 for this update. The bundle adapts selected ideas into its own workflow; it does not vendor source bodies, search databases, command implementations, or style presets. These are page observations at review time, not claims that the moving upstream versions remain unchanged.

| Inspected source | Adopted idea and local home | Boundary |
| --- | --- | --- |
| [UI UX Pro Max skill instructions](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/main/.claude/skills/ui-ux-pro-max/SKILL.md) | Common decisions plus scoped page overrides in [design-memory.md](design-memory.md); focused, fit-checked retrieval in [pattern-selection.md](pattern-selection.md) | Existing project authority takes priority. No mandatory search tooling, generated presets, or blanket rejection of immediate state changes; a failed search is not a verified match. |
| [getdesign.md: Use DESIGN.md](https://starterkit.getdesign.md/docs/use-design-md) | Reusable design documentation connected to actual token definitions in [design-memory.md](design-memory.md) and [design-contract.md](../assets/design-contract.md) | Its root documents, CSS paths, automatic agent loading, and site-wide synchronization describe that starter kit. Discover this project's equivalents; no global instruction-file edits, automatic whole-site rewrite, or assumption that importing a design grants it authority. |
| [Vercel Web Interface Guidelines](https://vercel.com/design/guidelines) | Focus visibility, return position, stable pending labels, and input assistance developed into [interaction-recipes.md](interaction-recipes.md) | Keep checks relevant to the product. Do not import brand-specific casing, fixed loading durations, URL persistence for private state, zoom suppression, or an unverified framework-specific timing guarantee. |
| [MDN KeyboardEvent.isComposing](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/isComposing) | Composition-aware Enter handling in [interaction-recipes.md](interaction-recipes.md) | The API identifies events within a composition session. Real IME and browser event ordering still needs verification; synthetic events are limited evidence. |

The task-pattern matrix, document/code conflict policy, component specimen, retry boundaries, and evidence labels are this bundle's synthesis. They are practical decision aids, not published measurements of design quality. Accessibility requirements retain their own official sources; upstream brand preferences do not replace them.

## Installation and source boundaries

Impeccable's reviewed README documents `npx impeccable install`; its ecosystem may include hooks and downloaded tooling. This bundle does not run that command or install hooks. Follow upstream documentation only if the user requests that optional installation. Other upstream setup commands should be verified at use time.

Reviewed license labels: Impeccable Apache-2.0; Anthropic frontend-design [Apache-2.0](https://github.com/anthropics/skills/blob/main/skills/frontend-design/LICENSE.txt); Vercel agent-skills MIT; UI UX Pro Max MIT. These labels do not relicense upstream content. If redistributing an upstream snapshot later, pin its revision and include the actual applicable license/notice files.

## Official implementation references

- [OpenAI local skill discovery](https://learn.chatgpt.com/docs/build-skills): repo `.agents/skills`, user `.agents/skills`.
- [Claude Code skills](https://code.claude.com/docs/en/skills): repo `.claude/skills` and user-level equivalents.
- [W3C dragging alternatives](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements): single-pointer alternatives are separate from keyboard access.
- [W3C target size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html): 24 CSS px AA criterion with exceptions, not an unconditional 44 px rule.
- [WAI modal dialog](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/): focus and keyboard behavior.
- [Android accessibility defaults](https://developer.android.com/develop/ui/compose/accessibility/api-defaults): semantics and 48 dp touch regions.
- [Playwright assertions](https://playwright.dev/docs/test-assertions): outcome assertions for browser tests.

These sources support the corresponding technical points; aesthetic heuristics and workflow choices in this bundle are design judgments, not experimentally established guarantees.
