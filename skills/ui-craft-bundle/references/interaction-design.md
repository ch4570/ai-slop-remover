# Interaction as observable behavior

Define the actual screen's controls, not a generic feature checklist. For substantial flows, use a compact table:

| Trigger | State/data change | Feedback | Recovery | Persistence |
| --- | --- | --- | --- | --- |
| Choose filter | Filters and visible results change | Selection and count | Clear filters on zero results | URL when share/back behavior benefits |
| Save edit | Valid draft is committed | Pending and updated record | Preserve draft; error and retry | Existing backend or explicitly local |
| Reorder item | Ordered stable IDs change | Placement and new position | Undo or rollback | Defined store; refresh if promised |

Include applicable states: default, hover on fine pointers, focus, pressed, selected, disabled with reason, empty, loading, partial result, error, success. Do not bolt all states onto a trivial synchronous toggle.

## Implement real outcomes

- Search filters or queries actual data. Distinguish no data from no matches; preserve useful results during refresh where appropriate. Prevent stale responses overwriting a newer query through cancellation or request identity.
- Tabs change associated content and expose selection. Navigation supports platform back. Put shareable filters in the URL when useful; keep private drafts out of URLs.
- Forms validate at a useful moment, associate field errors, preserve values, and avoid accidental duplicate submits. Show success only after the defined local/remote operation succeeds.
- Use optimistic changes for reversible, low-risk actions when rollback exists. Preserve drafts during failure. Do not fabricate financial, account, or destructive operation success.
- Bulk selection defines visible, filtered, or all records. Keep stable IDs during reorder. Counts and bulk actions must agree.
- Sorting by drag also offers visible move controls or a destination menu. Verify keyboard support separately; keyboard alone is not a touch alternative.
- Allow cancellation and recovery where supported. Avoid blocking animations or loading states that cannot resolve.
- Implement actual export/download if advertised. If a backend is outside scope, clearly describe the local prototype and missing integration.

## Add interaction selectively

Use direct manipulation when it reduces effort: inline edits for frequent changes, linked chart/list selection for exploration, reversible drag for ordering, or details beside a working list. Choose simple buttons, forms, or pages when richer behavior adds discoverability cost.

Do not automatically add command palettes, infinite scrolling, gamification, gestures, or shortcuts. Each should improve the identified task. Keep critical actions discoverable without knowing gestures or shortcuts.

A toast can confirm a completed change; it cannot be the change itself. Never add artificial delay to manufacture loading animations.

## Own state deliberately

Separate ephemeral UI state from durable product state. Follow the existing data/query architecture. Use local storage only for appropriate non-sensitive preferences or an explicitly local prototype; do not imply device sync. Handle malformed/outdated stored values when relying on them. Match undo to real persistence, not only visual state.
