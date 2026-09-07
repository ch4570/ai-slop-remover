---
title: Truthful copy for product states
source: ../../../ui-craft-bundle/references/interaction-design.md
last_fetched: 2026-09-07
skills: [ux-writing]
---

# Truthful state copy

The shared [interaction reference](../../../ui-craft-bundle/references/interaction-design.md) requires actual outcomes, useful recovery, and honest persistence. [Art-direction guidance](../../../ui-craft-bundle/references/art-direction.md) calls for domain labels and long-text checks, including Korean. `last_fetched` records the local source read; the examples below are generic editorial patterns, not externally established requirements or verified product behavior.

| State | Generic Korean pattern | Confirm before using |
| --- | --- | --- |
| Named action | “변경사항 저장” | The action commits the represented changes |
| Failed save | “저장하지 못했어요. 입력한 내용은 남아 있어요. 다시 시도해 주세요.” | Input actually survives and retry is available |
| No matches | “검색 결과가 없어요. 다른 검색어로 찾아보세요.” | This is a completed search with an editable query |
| First use | “아직 등록한 항목이 없어요.” | The list has no data; it is not loading or permission-filtered |
| Local persistence | “이 기기에 저장했어요.” | The actual operation persisted on this device |
| Unavailable export | “내보내기는 아직 지원하지 않아요.” | Export is genuinely unavailable in the current product state |

Do not copy the pattern when its conditions are false. If a recovery control does not exist, do not imply it does. A save failure of unknown cause supports a failed-operation message, not a guessed network diagnosis. Never remove mandatory consequences or disclosures to make a label friendlier.

For narrow Korean layouts, verify the full action and error text remain understandable. Avoid solving overflow by truncating the only explanation or forcing every phrase onto one line. Keep locale interpolation and accessible names aligned with the rewritten visible text.

## 리뷰 훅

- [ ] Does each sentence describe an actual state, capability, or consequence?
- [ ] Is the suggested next action available in the current screen?
- [ ] Are tone and domain terms consistent without blaming the user?
- [ ] Are localization variables, accessibility labels, and required disclosures intact?
- [ ] Were Korean wrapping and long-content limits inspected or explicitly left unverified?
