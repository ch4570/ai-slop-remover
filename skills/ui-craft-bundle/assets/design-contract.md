# Design contract

Keep only fields that help the task. Replace prompts with decisions; do not deliver an unfilled template.

Use the project's existing design document and page-exception structure. For small changes, a short note is enough. Read [design-memory.md](../references/design-memory.md) when decisions need to survive subsequent tasks; do not create a second source of truth.

- Product/screen and primary user:
- Immediate job and primary action:
- Existing stack, components, constraints:
- Layout and density rationale:
- Type, spacing, surface hierarchy, visual signature:
- Reference observations, if actually inspected:

## Reusable decisions

- Existing common document and page/route scope:
- Authority when design documentation and code differ:
- Selected working pattern and reason; meaningful alternative considered:
- Common tokens/components reused; new roles and why existing ones do not fit:

| Semantic role | Code token/symbol and location | Consuming component | Page/state exception and rationale | Evidence/status |
| --- | --- | --- | --- | --- |

Use actual paths and symbols. Mark evidence as observed, inferred, or proposed; include the inspected source/date where it informs a decision. Keep page exceptions limited to named fields and inherit the rest of the common contract. Record unresolved doc/code drift without silently making it a new rule.

## Journey and verification

| Control/journey | State change | Feedback | Recovery | Persistence |
| --- | --- | --- | --- | --- |

- Narrow-screen/native adaptation:
- Content and edge states:
- Verification scenarios and available runtime:
- Component specimen/preview location and states checked, if shared primitives change:
- Assumptions/integration boundary:
- Decisions updated after implementation; unresolved exceptions and revisit condition:
