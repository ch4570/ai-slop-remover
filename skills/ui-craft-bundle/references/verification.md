# Evidence-based UI verification

Use existing project commands and authorized preview/test tools. Inspect instructions and build files before choosing commands. Start the smallest useful runnable surface. Follow host rules for external browsing; this document does not grant login or site-interaction permission.

## Establish a baseline

Capture the current screen and relevant behavior when runnable. Keep viewport, data, and theme comparable. If no baseline is available, describe actual starting evidence and avoid fabricated before/after claims.

## Exercise the scoped journey

Test outcomes, not control existence:

| Action | Useful assertion |
| --- | --- |
| Filter | Rows and count agree; clearing restores data |
| Save | Value changes in its owner and survives promised persistence |
| Invalid submit | Error appears and entered values remain editable |
| Open/close modal | Focus enters correctly and returns; keyboard works |
| Reorder | Displayed order and stable IDs agree; alternate controls work |
| Request failure | Pending ends; input survives; retry/recovery works |

Choose a primary end-to-end journey and risk-relevant edge states. Check changed controls with keyboard/touch and changed motion with reduced motion. Include no-results, failure, long labels, or repeat clicks when relevant. Do not add a large suite for cosmetic spacing.

For the changed surface, select measurable checks from [UX foundations](ux-foundations.md). Record the applicable platform, criterion, unit, and any relevant exception. Keep normative accessibility checks distinct from recommendations and usability hypotheses. For anti-slop work, also revisit the chosen [method's tradeoff](anti-slop-methods.md): less decoration should not hide actions, errors, or necessary information.

## Inspect actual images

Render representative narrow/wide web sizes or relevant native profiles. Actually open captured images. Look for clipping, overlap, wrapping, hierarchy, inaccessible controls, inconsistent alignment, empty regions, and broken images. Include focus/error/empty states when they materially affect layout.

Use screenshot comparisons only with a meaningful baseline/environment. Never accept a new baseline just to hide a real regression. Do not impose an aggregate beauty score as a substitute for evidence.

## Fix and stop

Prioritize broken tasks, misleading success, inaccessible essential controls, data loss, and major overflow. Then address observed hierarchy/interaction problems, followed by typography, spacing, and motion details relevant to the request.

Recheck affected behavior after fixes. Stop when the scoped journey works and material findings are resolved or honestly bounded. Do not require an arbitrary number of critique rounds.

## Calibrate claims

Use [verification-note.md](../assets/verification-note.md) for substantial work; a concise response suffices for small fixes. Record screen/route, viewport/device, scenario, expected and observed result, evidence path/output, and limitations.

Separate implemented, build/type checked, visually inspected, behavior tested, and unverified. A screenshot cannot prove interaction; emulation cannot prove physical-device behavior. Automated accessibility checks alone do not establish full conformance. A skill cannot guarantee visual quality.
