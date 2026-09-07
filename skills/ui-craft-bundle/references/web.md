# Web implementation

Inspect the stack, lockfile, routing, styles, primitives, and test scripts first. Preserve existing React/Vue/Svelte or server-rendered architecture. Use native HTML and installed components where they fit; a visual change does not require framework migration.

## Input and structure

- Use buttons for actions and links for navigation. Keep accessible names, labels, form associations, and visible focus.
- Prefer existing accessible dialog/popover primitives. Apply the actual pattern's behavior: appropriate initial focus, Escape, focus return, and no keyboard escape into inert content for a modal. Do not trap focus in an ordinary nonmodal side panel.
- Follow established keyboard behavior for tabs and menus; ARIA attributes alone do not implement it.
- Check contrast on the composed surface, including focus, error, and selected treatments. Use measurement when reporting ratios; do not claim WCAG conformance from appearance.
- A practical design target for common mobile controls is about 44 CSS px. This is not the WCAG 2.2 AA minimum: SC 2.5.8 defines 24×24 CSS px with specified exceptions including spacing. Use the actual criterion when auditing.
- Author-created drag interactions need a simple click/tap path and keyboard operation unless an applicable exception exists. Keyboard equivalence alone does not meet the single-pointer requirement.

## Layout and states

Choose breakpoints from content pressure. Probe a narrow phone around 360–390 CSS px and an appropriate desktop width, plus intermediate transitions when relevant. These are representative checks, not all-device coverage. Exercise long text and zoom/reflow when the changed layout could break.

Keep loading/error/empty states in a stable structure when useful. Reserve media dimensions to avoid shifts. Do not hide overflow globally to conceal layout bugs. Provide a deliberate scroll region or task-preserving mobile representation for wide tables.

## Performance and tooling

Start with observed bottlenecks: blocking fetch chains, shipped JS, heavy media, or long lists. Measure before adding memoization, virtualization, or a new library. Use optional Vercel guidance from [sources.md](sources.md) only when relevant to React/Next work.

Use available browser automation for result assertions. Prefer role/name or stable selectors over positional CSS. A click returning without error is not an outcome assertion. Scope mocks to tests and disclose them.

Sources: [WAI modal pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/), [W3C target size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html), [W3C dragging](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements), [Playwright assertions](https://playwright.dev/docs/test-assertions).
