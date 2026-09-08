# Compose color on the actual screen

Use when color makes a screen feel noisy, flat, muddy, or hard to scan. Preserve the product direction in [art-direction.md](art-direction.md). The decisions below are bundle design judgments; the source notes identify system-specific guidance. Applicable accessibility requirements and their exceptions remain in [ux-foundations.md](ux-foundations.md).

## Assign roles before choosing shades

Inspect the existing brand assets, theme tokens, and representative screen. Name the foreground and background together for the roles actually present:

| Role | Decision to make |
| --- | --- |
| Canvas and content surfaces | Which regions belong to the same level? Which nested region needs a visible boundary? |
| Main and supporting text | Which information must be read first, and which remains necessary to finish the task? |
| Actions and selection | Which action needs prominence here? How is a persistent selection distinct from hover? |
| Status and feedback | Which colors already mean error, warning, success, or information in this product? |
| Data and user categories | Does color encode a category, an ordered amount, or deviation around a meaningful midpoint? |

Reuse existing semantic tokens. Add a missing role only when it represents a different use; two roles can share a value without becoming the same role. Keep a status token independent from an action token even when both currently use green.

Preserve the approved brand hue and assets. If its exact value fails on a control, retain the asset and derive a usable action/text tone or choose another approved foreground/background pairing. Do not replace the brand with a fashionable palette. For a new palette, compare a neutral base and a lightly hue-related base against actual brand assets and content; choose by their interaction on screen.

## Judge relationships, area, and emphasis together

- **Compare neighboring surfaces.** Inspect canvas → panel → field/menu in place. Choose a consistent layering relationship, then vary boundaries where the task needs it. Arbitrary warm and cool near-grays can make equal-level regions appear unrelated; consolidate accidental differences while retaining meaningful ones.
- **Separate with the right variable.** If a field disappears into its panel, adjust its local lightness or boundary. If a heading disappears, fix its text pair or typography. Tinting the whole panel changes much more of the screen than either correction requires.
- **Count repeated color as one visual mass.** Twenty bright status pills or a full-height accent sidebar can outweigh a small primary button. Check occupied area, chroma, lightness contrast, and repetition together. Reduce the competing fill area, strengthen the task's local emphasis, or adjust surrounding contrast according to the intended reading order.
- **Keep deliberate color where it earns attention.** A brand section, image, or campaign headline may deserve a large vivid region. Give adjacent reading/control regions a compatible treatment. A fixed color percentage or uniformly muted palette cannot establish the right balance.
- **Choose foregrounds per fill.** A vivid yellow and a deep blue need different text treatment. Check the actual pair rather than assigning white text to every accent. Keep supporting text readable; reducing opacity can also change it unpredictably across surfaces.
- **Include the content's colors.** Photography, avatars, charts, and user labels already occupy the palette. If they compete with tinted chrome, adjust the chrome or its area before recoloring meaningful content.

## Keep color meanings legible

Distinguish action, selection, status, and data through labels, shape, position, or other appropriate cues as well as color. A brand red button can remain red when an explicit action label and a separate error treatment make their meanings clear. Do not assume every red object is an error or every green value is positive; preserve the product's domain and locale conventions.

Use category colors consistently across related views. For quantities, use a progression whose perceived lightness follows order; use a diverging treatment only when a real midpoint matters. Verify the chart at its displayed size, including labels and adjacent marks. Decorative rainbow variation on equal-priority metrics invents meaning and adds competing accents.

Hover, pressed, selected, focus, and error can coexist. Inspect relevant combinations on their real surface; a darker hover fill must not erase the selected cue or obscure the focus ring. Use [interaction-design.md](interaction-design.md) for the behavior and state contract.

## Adapt themes only when they are in scope

For an existing or requested dark theme, keep semantic meanings and remap their values as coordinated foreground/background pairs. Do not invert hex values or assume light-theme opacity overlays transfer unchanged. Choose surface relationships that keep nested content, menus, and fields distinguishable in that theme.

Inspect large saturated regions, tinted neutrals beside multicolor content, and bright text in the rendered dark screen. Adjust the specific competing area or pair; preserve intentional brand energy and required contrast. Check images, charts, focus, and feedback alongside ordinary text. A light-theme screenshot establishes nothing about the dark theme's result.

## Diagnose a visible failure, then recheck

| Observed failure | Candidate correction | Recheck on screen |
| --- | --- | --- |
| Every card and pill is vivid; the next action is hard to find. | Reduce repeated decorative fills; keep distinct status labels and concentrate emphasis where the task needs it. | Can the intended next action be located while urgent statuses remain findable? |
| Everything is pale; rows, inputs, and metadata merge. | Restore a stronger local boundary or text pair and a clear action treatment. | Can users distinguish editable controls, supporting text, and selected content? |
| A palette looks balanced as swatches but clashes in the page. | Compare the actual neighboring neutral tints, image colors, and largest filled region; change the responsible relationship. | Does the same content read coherently at full width and narrow width? |
| The brand accent also marks chart series and alerts with no distinction. | Keep brand identity; separate semantic tokens and add explicit labels or distinct treatments. | Can each color-bearing element's purpose be understood without inferring it from hue? |
| A dark menu merges into its parent, or dominates the entire screen. | Adjust the menu's surface pair and boundary within the theme's layering model. | Are menu location, items, focus, and underlying context clear? |

Review a rendered representative screen at ordinary viewing size, then check detailed text/control pairs. A thumbnail can reveal competing color masses; it cannot establish legibility. Compare the changed screen with the baseline using the same content, viewport, and state. Record the visible defect, the role/area changed, and the observed result. State which theme and interaction states were actually inspected; contrast measurements alone do not prove visual comfort.

## Source scope

Official sources inspected on **2026-09-08**:

- [Radix: composing a palette](https://www.radix-ui.com/colors/docs/palette-composition/composing-a-palette) explains neutral and hue-related gray pairing, retaining custom brand scales alongside its supplied scales, and possible clashes between tinted backgrounds and colorful components. These are Radix design choices, not a requirement to adopt Radix colors.
- [Radix: understanding the scale](https://www.radix-ui.com/colors/docs/palette-composition/understanding-the-scale) assigns different scale regions to backgrounds, component states, borders, fills, and text, with foreground exceptions for bright fills. Its step numbers and APCA claims apply to the documented combinations; they are not a WCAG pass for arbitrary mixtures.
- [Carbon: color overview](https://carbondesignsystem.com/elements/color/overview/) separates semantic roles from theme values and uses different layering relationships in light and dark themes. Carbon's grays, blue action color, and exact layer steps belong to its system. The area, emphasis, diagnosis, and review choices above are this bundle's practical synthesis, not measured guarantees of aesthetic quality.
