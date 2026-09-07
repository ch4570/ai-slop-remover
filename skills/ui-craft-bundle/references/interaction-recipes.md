# Small behaviors that make a flow easier to use

Choose the recipes affected by the task. Each connects a user trigger to implementation intent and an observable check; it is not a request to add every feature. Start with the installed components, router, data layer, and platform conventions. Browser APIs below apply to web surfaces; native implementations should preserve the intended behavior through their own input, navigation, and lifecycle APIs.

## 1. Composition input and Enter

**Trigger:** A user types Korean or another composition-based script into search or a form, then presses Enter to finish the composed text.

**Implement:** Keep the editable value responsive during composition. Custom Enter shortcuts must not treat a composition-confirming key as a submit or selection command. Check `KeyboardEvent.isComposing` and the framework's composition events; verify event ordering on the supported browsers and IMEs rather than assuming one flag covers every case. Keep interim text out of committed search/navigation when it would interrupt composition. Preserve normal Enter behavior once composition has ended and the next deliberate submit occurs; do not block native composition or textarea newlines.

**Check:** With a real Korean IME, enter "서울", confirm composition, and then deliberately submit. Confirm no premature navigation or duplicate submission and correct final text. Synthetic composition events can test a guard but do not prove real IME behavior; report real-device/browser coverage separately. See [MDN isComposing](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/isComposing).

## 2. Search, filters, and browser history

**Trigger:** A user edits a search term repeatedly, applies filters, and uses Back or shares the view.

**Implement:** Decide which state belongs in a shareable URL and allowlist it. Use the existing router's replace behavior for transient edits when per-keystroke history is unwanted; use push for deliberate navigation that should be a separate Back destination. Keep private drafts, secrets, and sensitive searches out of URLs. Match the input and results to URL changes from Back/Forward; preserve unrelated query parameters. Do not serialize every piece of UI state by default.

**Check:** Type several characters, commit the intended search/filter navigation, move to a detail page, and go Back. Confirm the intended number of history entries, matching input/results, and a copied URL containing only approved state. Native views should use their navigation state instead of adding URL behavior without a deep-link requirement.

## 3. Returning to a list or reading position

**Trigger:** A user opens an item after scrolling, then returns to the collection.

**Implement:** Preserve the collection's meaningful filters, selection, and position using existing navigation restoration. Keep record identity stable when data reloads. Restore once the relevant content can support the position; avoid global scroll-to-top effects that compete with router restoration. On a new destination, use its expected initial position and focus behavior instead.

**Check:** Return to a scrolled list and confirm the same region and filters remain usable after data settles. Also open a new destination to confirm it does not inherit an unrelated position. Check narrow layouts and a changed/missing selected item where those cases are supported.

## 4. Dialogs, overlays, and visible focus

**Trigger:** A user opens and closes an overlay from a scrolled page or navigates near a sticky header.

**Implement:** Reuse an accessible primitive with the right modal/nonmodal behavior. Keep initial focus, focus return, and dismissal meaningful. If the opener disappears, select a logical remaining destination. Avoid horizontal jumps when a modal changes scrollbar availability. Scope any scroll containment or locking to the overlay's needs; an ordinary side panel does not require a modal focus trap or page scroll lock. Ensure fixed regions do not hide focused controls.

**Check:** Open/close with keyboard and pointer, tab through the relevant controls, and inspect page position, horizontal alignment, and returned focus. Verify the overlay's own scrolling and mobile keyboard interaction when relevant. Follow [the WAI modal pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/) for actual modal behavior.

## 5. Stable feedback while work is pending

**Trigger:** A user activates a control whose operation may finish immediately or take time.

**Implement:** Acknowledge the action without delaying available results. Keep the action identifiable while busy and reserve enough space for status changes. Prevent duplicate commits when required without blocking unrelated work. Reuse existing pending behavior; a local synchronous change needs no spinner. If transient loading indicators flicker, tune their presentation from observed behavior without imposing a universal delay or making completed data wait for an animation.

**Check:** Exercise immediate, slow, and failed operations. Confirm no button-size jump, lost accessible name, invented success, or lingering pending state. The completed result should be usable as soon as the operation allows; reduced motion should retain the feedback.

## 6. Rapid input and interrupted transitions

**Trigger:** A user changes a query, filter, tab, or expandable section again before earlier work finishes.

**Implement:** Keep the most recent intent authoritative. For read requests, use the existing cancellation or request-identity mechanism so an older response cannot overwrite newer results. Interrupt visual transitions cleanly; do not queue a series of obsolete animations or steal input focus. Preserve useful prior content during refresh when it does not misrepresent the active selection.

**Check:** Change the input twice and resolve responses in reverse order. Confirm the final control state, displayed data, count, and URL agree. Repeatedly open/close an affected animated region and check both normal and reduced-motion behavior.

## 7. Failed saves and safe retry

**Trigger:** A save fails, times out, or is clicked repeatedly.

**Implement:** Preserve entered values, end the pending state, and offer recovery supported by the actual data contract. A canceled browser request or timeout does not establish that a write was canceled on the server. Reconcile an uncertain outcome before retrying a non-idempotent operation; use existing idempotency support when available. Do not invent backend deduplication or automatic retry guarantees. Report success only after the defined operation succeeds.

**Check:** Fail a save, verify the draft remains editable, and recover through the supported path. Repeated activation must not create unintended duplicate writes. Cover uncertain outcomes separately from known rejections when the product supports remote writes.

## 8. Paste, autofill, and recoverable validation

**Trigger:** A user pastes an address or one-time code, uses autofill, or corrects a field error.

**Implement:** Use meaningful labels and the applicable `name`, `autocomplete`, input type, and input mode for web fields. Allow paste and password-manager flows. Preserve the value and cursor during edits; normalize only where the field's data contract permits it, and never silently trim passwords or meaningful whitespace. Associate errors with fields and keep a clear way to correct them. Do not replace useful native input behavior with key filtering.

**Check:** Paste and autofill the relevant fields, submit invalid data, then correct it. Confirm input survives validation, errors describe the actual problem, and keyboard focus remains usable. Check text expansion or trailing spaces only for fields where normalization is intended.

Recipes expand the bundle's [interaction contract](interaction-design.md) with scoped checks. Vercel inspired the focus, return-position, pending-label, and autofill details; [sources.md](sources.md#guidance-integrated-in-this-bundle) records the boundaries. History granularity, privacy, retry policy, and platform checks are this bundle's implementation judgments and must match the actual application contract.
