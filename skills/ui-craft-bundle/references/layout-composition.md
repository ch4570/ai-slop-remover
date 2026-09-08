# Compose the page before polishing its parts

Use for a new screen, a substantial rearrangement, or a layout that remains awkward after spacing fixes. [Pattern selection](pattern-selection.md) helps choose the working structure; this reference turns it into a page. A local margin request does not need alternative layouts or a new grid system.

## Establish the visual order

Name what the user needs to **find, compare, and do** in this particular state. Distinguish the working object from navigation, summary, and supporting detail. Order the screen around those relationships before choosing card styles or equal-width columns.

- Put the task's working content where the eye can reach it without crossing unrelated summaries. In an exception queue, unresolved records can lead; a large total-order KPI does not deserve the lead merely because its number is large.
- Keep an action with the object or selection it affects. A page action, selected-row action, and form commit need different ownership cues; proximity and labels should explain their scope.
- Establish a primary content edge and repeated alignment anchors for headings, fields, values, and action groups. Different text lengths should not create a new alignment for every item.
- Use type size/weight, local spacing, and surface contrast together. A giant heading over quiet working data or a saturated support panel can reverse the intended order even when the grid is tidy. Resolve that with [color composition](color-composition.md), not another wrapper.

For an ambiguous broad brief, sketch plausible structures with the **same real content**, then choose by the task: for example, aligned records with a selected detail versus a reading column with supporting controls. A second layout must change information relationships, not just swap colors. Use a short work note or existing preview; do not ask for approval of every reversible sketch or make layout exploration mandatory for narrow edits.

## Allocate space from content requirements

Treat width as a budget: available page width minus navigation, outer margins, gutters, and supporting panes leaves the working region. Test it with the longest relevant label, a realistic record, and its actions. A familiar `1fr 1fr 1fr` grid or a device-name breakpoint is not evidence that the content fits.

| Region | Sizing decision | Failure to look for |
| --- | --- | --- |
| Repeated comparisons | Share column anchors; give verbose names flexible space and keep dates, units, and actions interpretable | Equal cards scatter comparable values; long names squeeze the action out |
| Primary work plus support | Allocate the primary region enough room for its actual fields/content; bound a short supporting pane | A large empty sidebar takes width from a cramped editor |
| Reading or instructions | Constrain the reading measure independently of the full page width | Paragraphs stretch across the entire monitor; a narrow fixed column wastes useful comparison space elsewhere |
| Gallery or independently browsed objects | Size items for their content and let count/columns respond to available space | Tiles become too small to recognize or grow mostly empty to fill a row |
| Forms and toolbars | Let related labels, controls, errors, and actions establish a group; wrap at meaningful boundaries | A control looks attached to the next field; toolbar items split into unrelated fragments |

Prefer the project's existing grid and tokens. Do not import Carbon's column count, base unit, or Material's pane proportions into every product. When the width budget fails, change the composition at that point: move supporting detail, wrap an action group, or use an appropriate list-to-detail presentation. Keep required comparisons and controls reachable; do not cure pressure with smaller text or page-wide overflow hiding.

## Give space a relationship

Use a small set of the existing spacing roles: within a control, between related parts, between groups, and between sections. Related parts generally need a closer relationship than separate groups. This is a grouping heuristic, not a mandatory numeric ratio.

Check the gaps **as rendered**, including line height, wrapped labels, borders, and the control's own padding. Equal CSS margins can produce unequal visible gaps. Align comparable numbers and labels; allow an intentional optical adjustment for an icon or logo only after looking at it beside its neighbors.

| Observed problem | First correction to try | Preserve and recheck |
| --- | --- | --- |
| Every block appears equally important | Group supporting information, tighten repeated records, and give the current work a clear anchor | All required data/actions; whether the primary task actually becomes easier to locate |
| A field label floats between two inputs | Reduce its gap to its own control and separate it from the previous group | Error/help association and long-label wrapping |
| Large empty cards and panels force unnecessary scrolling | Remove unnecessary fixed/min heights; use content-led group sizes | Useful breathing room, stable states, and access to the primary action |
| Ragged rows feel busy despite a limited palette | Establish shared label/value/action edges before changing colors | Meaningful content and logical reading order |
| The desktop stacks into a long mobile preamble | Promote the current task, compact suitable summaries, and provide a clear path to supporting detail | Active selections, consequences, recovery, and keyboard/Back continuity |

Do not compress every gap to increase density or expand every gap to suggest luxury. Dense tools still need distinguishable groups; reading surfaces still need reachable actions. Avoid stretching unrelated panels to matching heights unless their relationship benefits.

## Inspect the whole page, then its details

Compare actual renders at the same viewport, content, and state. First inspect the whole page: does the dominant visual mass belong to the intended task, do edges form a coherent structure, and do color emphasis and spatial priority agree? Then inspect real-size text, grouping, clipping, focus, and action access. A thumbnail impression is a composition heuristic, not readability or accessibility evidence.

Check a narrow width, the width just before a composition changes, and a representative wider width when the scope crosses them. Include long/localized content and a relevant empty/error/selected state. Keep DOM reading and keyboard order coherent with visual order. Follow [UX foundations](ux-foundations.md) for separate text-enlargement and reflow requirements.

Change the weakest relationship identified in that inspection, then compare again. Keep the version supported by the task and evidence; do not accumulate decorative refinements simply because another pass is possible. Record reusable anchors, spacing roles, sizing behavior, and page exceptions in [design memory](design-memory.md).

## Sources and interpretation

Inspected 2026-09-08: [Carbon 2x Grid](https://carbondesignsystem.com/elements/2x-grid/overview/) informs alignment anchors and choosing between fluid sizing and additional items. [NN/G form proximity](https://www.nngroup.com/articles/form-design-white-space/) informs label/control grouping and action/object proximity. [Material canonical layouts](https://m3.material.io/foundations/layout/canonical-examples/overview) provides examples of list-detail and supporting-pane relationships. Their system-specific grids and proportions remain examples, not universal requirements. The width-budget workflow, correction table, and review sequence above are Lutriva's synthesis, not measured guarantees of usability.
