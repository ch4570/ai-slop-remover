# Upstream options and provenance

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
