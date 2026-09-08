# Component specimen

Use before a broad token or shared-component rollout when seeing the affected controls together can expose inconsistency. Reuse an existing Storybook story, component preview, native preview, or a small section of the current screen. Do not create a new app, public route, dependency, or permanent gallery merely to fill this template. A narrow spacing fix usually needs only the affected screen.

Replace these prompts with the scoped checks, or record them in the project's existing preview notes. Render real project components using the same token source as production; copied demonstration markup does not verify the shared component.

- Surface/preview and command or route:
- Existing design authority and affected token symbols:
- Actual components and consuming screens:
- Representative theme(s), width/device, and content fixtures:

| Scoped component | Useful specimen states | Behavior/layout to inspect | Evidence/result |
| --- | --- | --- | --- |
| Primary and secondary action | Normal, focus, pending, failure/retry if applicable | Hierarchy, identifiable action, size stability, repeat activation | |
| Labeled input | Normal, invalid, corrected, pasted/autofilled text | Label/error association, cursor/focus stability, preserved value | |
| Repeated item or table row | Selected/unselected, missing value, long content | Comparability, metadata grouping, accessible actions, narrow layout | |
| Empty or failed region | No data, no matches, recoverable error as supported | Specific explanation, useful next action, preserved context | |

Keep only affected rows. Include realistic long text from supported languages: for Korean, a label such as "변경한 내용을 저장하고 목록으로 돌아가기" helps expose wrapping and height changes. This is a stress fixture, not mandatory product copy. Check real domain terms, long names, and values as well as short samples.

- **Keyboard:** traverse changed controls, activate the relevant action, and inspect visible focus and its return where applicable.
- **Content and surfaces:** inspect supported themes, composed backgrounds, long labels, and the layout at the width where it is most constrained. Measure contrast if reporting a ratio.
- **Composition:** inspect the consuming page as well as isolated controls. Compare surface areas and color emphasis, selected/error/action distinctions, shared alignment edges, and the space left for the primary task. Swatches alone cannot reveal a visually dominant sidebar or a cramped work region.
- **Motion:** compare the changed transition with reduced motion enabled; preserve information and interaction in both modes. Record not applicable when no motion changes.
- **Integration:** after the specimen is satisfactory, exercise a consuming screen's primary journey. A preview's mocked states do not establish real data persistence, failure recovery, or navigation behavior.

Record the image/preview actually inspected, behavior exercised, remaining defects, and any runtime limitation. Build success alone does not complete this check. Reuse [verification-note.md](verification-note.md) for the final evidence record.
