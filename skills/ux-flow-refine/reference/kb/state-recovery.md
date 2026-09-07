---
title: State ownership and failure recovery
source: ../../../ui-craft-bundle/references/interaction-design.md
last_fetched: 2026-09-07
skills: [ux-flow-refine]
---

# State ownership and recovery

The canonical [interaction reference](../../../ui-craft-bundle/references/interaction-design.md) distinguishes UI state from durable state and requires real outcomes. The [motion reference](../../../ui-craft-bundle/references/motion.md) makes latest intent and reduced motion part of transition behavior. `last_fetched` records the local source read, not exercised behavior.

Use a small transition record to expose missing behavior:

| Situation | Required question |
| --- | --- |
| Save starts | Who owns the draft, what prevents duplicate work, and which operation is pending? |
| Save succeeds | Which owner committed the value, and what persistence was promised? |
| Save fails | Does pending end, does the editable draft survive, and what actual action retries? |
| Input changes again | Can an older request or animation callback overwrite the newer intent? |
| User cancels or returns | What is retained, discarded, or restored, and where does focus go? |
| Motion is reduced | Is the resulting state still obvious without unnecessary movement? |

For an existing local prototype, saving to local state may be valid when the UI promises only that boundary. It is not evidence of server storage or cross-device sync. When a service does not exist, a truthful unavailable state can be complete within the authorized scope; a false success state cannot.

## 리뷰 훅

- [ ] Is every promised result owned by an actual operation or state transition?
- [ ] Do failure paths preserve useful input and offer real recovery?
- [ ] Do rapid inputs and interruptions end at the latest intended state?
- [ ] Does reduced motion preserve meaning and immediate feedback?
- [ ] Do test assertions check outcomes and the promised persistence boundary?
