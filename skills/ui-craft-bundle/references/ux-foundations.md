# UI/UX foundations across platforms

Use when choosing a screen's structure or checking whether visual polish preserves task completion. Start with the changed flow; this is a decision aid, not a complete accessibility audit. Implementation details remain in [web.md](web.md), [native.md](native.md), and [interaction-design.md](interaction-design.md).

## Make the task understandable

These are bundle design judgments informed by [Nielsen's usability heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/), not numerical standards or guaranteed usability gains.

| Decision | Observable check |
| --- | --- |
| Name navigation with users' objects and tasks; distinguish destinations from actions. | From an entry screen, trace the intended destination using labels alone. |
| Group related content; keep comparison fields aligned. | Compare two actual records without memorizing values between screens. |
| Give the current task prominence; expose secondary options where needed. | Identify the next action and its consequence before activating it. |
| Keep terms, selection, and location consistent across the flow. | Open a detail, return, and find the same context. |

If organization is uncertain, use a realistic finding task with a representative user when available; an author's walkthrough only establishes plausibility. A flat navigation or a fixed number of choices is not universally better. Keep necessary comparison information available on narrow layouts instead of removing it solely to fit.

When deciding what simplicity means across mobile and desktop, use the platform-context and early-validation cases in [Toss design](toss-design.md). Define what the user needs to find, understand, and do; copying a mobile structure into a larger viewport does not establish task fit.

## Separate standards, platform guidance, and product choices

WCAG success criteria define requirements for the stated web conformance level. W3C Understanding pages explain them; those explanations are informative. Apple and Android guidance uses different platform units and conventions. Do not convert CSS px, pt, and dp into one universal number or infer legal compliance from this reference.

| Area | Decision and boundary | Observable verification |
| --- | --- | --- |
| Web pointer targets | WCAG 2.2 AA SC 2.5.8 specifies **24×24 CSS px**, with spacing, equivalent-control, inline, user-agent, and essential exceptions. Larger frequent touch controls can be a product choice. | Measure the actual clickable region, not the icon. For the spacing exception, center a 24 CSS px diameter circle on each undersized target's bounding box; it must not intersect another target or another undersized target's circle. [Target size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html) |
| iPhone/iPad touch targets | Apple recommends **44×44 pt** controls for accurate finger input. This is platform design guidance, not the web AA minimum or a rule for every Apple device. | Inspect native hit regions and activate adjacent controls independently. [Apple UI design tips](https://developer.apple.com/design/tips/) |
| Android touch targets | Android guidance uses at least **48×48 dp**. A visible glyph can be smaller; expanded touch areas still need room. | Inspect effective hit regions for overlap, including small custom Compose controls whose targets extend beyond visual bounds. [Android accessibility defaults](https://developer.android.com/develop/ui/compose/accessibility/api-defaults) |
| Web text enlargement | WCAG AA SC 1.4.4 requires text resizing through 200% without losing content or functionality; captions and images of text have exceptions. This is separate from reflow. | Increase text through 200%, including intermediate sizes; inspect labels, controls, and errors for clipping or overlap. [Resize text](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html) |
| Web reflow | WCAG AA SC 1.4.10 uses **320 CSS px width** for vertical content or **256 CSS px height** for horizontal content, with exceptions for parts requiring two-dimensional layout. | Check reading and actions without scrolling in both directions. A 1280 CSS px viewport at 400% zoom is one way to reach 320 CSS px. Keep necessary table/map scrolling local; surrounding controls still reflow. [Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) |
| Native text scaling | Use iOS/iPadOS Dynamic Type, including accessibility sizes, and Android scaled text units (`sp`). Custom fonts must also respond appropriately. | Exercise large accessibility text on iOS/iPadOS and maximum system font size on Android; Android 14 introduced scaling up to 200%. Preserve important content, control access, and meaningful icons. [Apple typography](https://developer.apple.com/design/human-interface-guidelines/typography), [Android font scaling](https://developer.android.com/about/versions/14/behavior-changes-all#non-linear-font-scaling) |

## Make the task operable and perceivable

- **Keyboard:** For web, provide a keyboard path to functionality under SC 2.1.1 (A), except underlying functions requiring path-dependent input. Follow component conventions and test completing the flow, not merely reaching its first button. [Keyboard](https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html)
- **Focus:** Web AA requires visible keyboard focus (2.4.7); 2.4.11 requires the focused component not be entirely hidden by author-created content, subject to its notes. Keeping it fully visible is a stronger usability target. Exercise sticky headers, banners, and dialogs while moving forward and backward. [Visible focus](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html), [Focus obscuration](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html)
- **Contrast:** Web AA text generally needs 4.5:1; qualifying large text needs 3:1. Large means at least 18 pt regular or 14 pt bold, or equivalent size for CJK fonts. The criterion has exceptions including inactive components and logos. Measure rendered foreground/background combinations, including overlays. [Text contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- **Controls and visual states:** Required visual information identifying controls, their states, and meaningful graphics generally needs 3:1 against adjacent colors under AA SC 1.4.11, with stated exceptions. This does not require every decorative border to contrast. Inspect actual focus, selected, and error treatments. [Non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)
- **Nonvisual feedback:** Expose status messages so assistive technology can announce them without taking focus (web AA SC 4.1.3); avoid announcing every minor update. Verify the outcome with a screen reader as well as visually. Native apps need native semantics and announcement mechanisms. [Status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html)

Do not equate a small screen with touch-only input. Exercise keyboard and relevant assistive technology where supported. Likewise, a web focus check does not verify native VoiceOver or TalkBack behavior.

## Make mistakes recoverable

For detected web input errors, identify the affected item and describe the problem in text (SC 3.3.1, A). Supply a known correction suggestion under SC 3.3.3 (AA), unless doing so would jeopardize security or the content's purpose. Color alone or a generic “Something went wrong” cannot explain which value needs correction. [Error identification](https://www.w3.org/WAI/WCAG22/Understanding/error-identification.html), [Error suggestion](https://www.w3.org/WAI/WCAG22/Understanding/error-suggestion.html)

Product decisions go further: preserve valid input, distinguish validation from network failure, and offer an available next step. Choose undo for reversible actions when restoration is real; use a consequence-specific review for costly irreversible actions. Check one relevant failure, recovery, and resulting stored state. Use the existing [interaction state table](interaction-design.md) rather than creating a second state specification.

## Evidence and source scope

Report the screen/flow, platform, setting, action, and observed outcome for checks actually run. A screenshot supports visual inspection; it does not establish keyboard operation, screen-reader behavior, persistence, or full WCAG conformance. Keep unverified device checks explicit.

Sources linked beside claims were inspected on **2026-09-07**. Apple HIG typography content was read through its official documentation JSON because the HTML view requires JavaScript. Numerical requirements retain their criterion and exceptions; the bundle's structure, prioritization, and verification choices are practical synthesis.
