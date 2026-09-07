# Choose structure from the user's task

Load this when a screen's structure is generic, the task is changing, or several patterns could plausibly fit. Start with the existing product system and actual content. A sector name such as "SaaS" is insufficient to choose a layout.

## Match the working shape

| User task | Candidate structure | Fit evidence to inspect | Tradeoff to check |
| --- | --- | --- | --- |
| Repeated comparison across the same attributes | Sortable table or aligned rows | Users compare prices, dates, units, or statuses across records | Preserve key comparisons and actions at narrow widths; cards may separate values too much |
| Review many items and inspect one | List with adjacent detail, or list-to-detail navigation | Users must retain their place while inspecting several objects | Keep selection and return position; use a separate detail view when width cannot support both |
| Read and understand long content | Reading column with section navigation when needed | Heading depth, reading length, citations, or annotations | Do not let navigation, sticky controls, or decoration crowd the text |
| Make a frequent small edit | Inline control with clear commit/cancel, or a compact form | A few fields, understandable validation, and recoverable mistakes | A separate form is clearer when changes have complex consequences |
| Complete a long or conditional submission | Grouped form; steps only when dependencies justify them | Draft lifetime, field dependencies, review needs, and return visits | Avoid hiding related fields behind unnecessary steps; preserve values during failure |
| Move between stable product areas | Existing navigation with a clear current location | Frequency, hierarchy, familiar labels, and platform back behavior | Do not introduce a command palette or extra navigation level merely for polish |
| Monitor work over time | Status list, timeline, or progress view tied to actual work | Known stages, timestamps, remaining actions, and supported cancellation | Do not invent percentages, activity, or completion estimates when the system lacks them |

These are candidates, not automatic mappings. A small record set may need a plain list; an existing accessible table may need only hierarchy and content corrections. Preserve working affordances unless changing them helps the scoped task.

## Use outside references deliberately

For each unresolved design question, describe one observable outcome and the relevant product or platform constraint. Search one concern at a time; use a detected stack only when implementation details matter. A focused query such as "comparison table narrow screen" is more useful than a list of aesthetic adjectives. Do not include private data in external searches.

Inspect the result's actual task, content density, platform, and available controls before adopting it. Product screens and marketing pages serve different jobs: a landing page's hero and social proof do not establish the layout for daily editing or comparison. Transfer a relevant decision, not a whole page shell.

If an optional installed reference skill offers domain/stack search, use the smallest relevant mode and verify its current invocation before running it. No search service or skill installation is required by this bundle. If results are empty or off-topic, narrow the question once; then use inspected project patterns or an explicitly labeled general fallback. Do not claim a match or persist an external suggestion that was never verified.

## Choose, try, then reuse

Name the selected pattern and the user behavior it supports. Record a rejected alternative only when it clarifies a real tradeoff. For a narrow fix, keep this decision in the work note. For reusable choices, update the [design memory](design-memory.md).

Before a large rollout changes shared tokens or primitives, render the affected controls together using an existing Storybook, component preview, native preview, or small existing screen section. Use [component-specimen.md](../assets/component-specimen.md) to check realistic content and states. Do not build a new preview application or add a dependency for a small change. Verify the actual journey after rollout; a specimen cannot prove page behavior.

Focused retrieval is adapted from [UI UX Pro Max](sources.md#guidance-integrated-in-this-bundle). The task matrix and rollout decisions are this bundle's design judgments, not validated universal rankings.
