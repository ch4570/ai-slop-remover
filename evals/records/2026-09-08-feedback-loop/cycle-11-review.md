# Independent review — bounded cycle 11 focus follow-up

## Scope and state

Read-only review of original task/previous task/service contract/app/CSS/HTML/design, frozen observer and criteria, baseline and two synthetic sensitivity controls. Trial and author-evidence were not read during this first stage. No browser run, dependency/network action, source/evaluator/repository edit, or subagent. This report is the only new review artifact; raw evidence remains at its existing paths.

This is one existing-skill product follow-up with stronger explicit whole-ring, Tab/Shift+Tab and intentional-scroll requirements. It is not a guidance-version comparison or evidence of general uplift. The earlier incomplete ring-visibility result remains a previous result. The preserved v1 setup SyntaxErrors yielded no behavioral conclusion and are not product failures.

## Frozen criteria and integrity

The core criteria match TASK.md: same-job operable direction, complete existing 3px solid teal outline plus 3px gap, original button size/style, narrow and low viewports, no recovery input, and no repeated forced return during deliberate scroll. Expanding button bounds by 6px implements the actual outline footprint. Both sampled frames are retained; only the second is accepted. The two-frame/200ms rule is a bounded operational interpretation of immediate operation, not a timing value stated by the task.

All five files recorded under observer-freeze.json `files` matched the hashes I independently recomputed, including original-v2/browser.json. Both control reports also match their frozen hashes. All three reports use those same evaluator/helper/criteria/data hashes and record unchanged eight-file before/after source maps, zero runtime/setup errors, and four PNGs each; current source hashes still match those recorded observations. Source comparison confirms no-outline changes only the appended CSS outline rule; sticky changes only the appended perpetual rAF centering loop. Controls are evaluator data, not valid product solutions or author outputs.

Coverage limits, not reasons to alter frozen acceptance:

- Failure/error/retry settled-focus observations run at 1280×900 only. Narrow/low runs check saved feedback; they do not establish error/retry visibility at those dimensions.
- The viewport/overflow-ancestor rectangle check does not establish visibility through every conceivable clipping mechanism or overlay. Existing fixture ancestors fit this model; source/PNG review remains needed if a trial changes layout/clipping.
- One downward wheel gesture at three viewports, sampled after about 100ms and again 800ms later, cannot establish every input modality or intervening motion. The `wheel-changed-scroll` AND `wheel-retained` pair is meaningful; equality alone can pass a sticky implementation.
- Computed button profiles and immutable HTML do not alone prove the entire CSS brand/layout remains preserved; review the source diff and actual PNGs. No broad screen-reader, zoom, touch, or cross-browser claim follows from this observer.

## Raw baseline and control findings

Baseline `/tmp/lutriva-cycle11-observer-CSCtCF/original-v2/browser.json` has 15 whole-indicator failures and no outline or focus-target failures. These are concrete clipping results, not pass-total inference:

- `wide:10:Space`: acted JOB-1042/up is enabled and focus-visible. Button bottom 900.45; ring bottom 906.45 exceeds viewport bottom 900. Both sampled frames clip.
- `narrow:10:Space`: button bottom 649.52 fits a 650px viewport, but ring bottom 655.52 does not. This directly demonstrates why button-only geometry is insufficient.
- `low:10:Space`: button bottom 500.45; ring bottom 506.45 exceeds 500.
- `narrow:15:Enter`: same job correctly switches to down at the first boundary, but ring top is -6.45. `narrow:16:saved-feedback-focus` still has ring top -6.05 after actual save and without recovery input.
- `low:3:Tab`: natural Tab gives an enabled move button with ring bottom 503.47 beyond 500, independently of reorder handling.

Original persistence evidence preserves the latest rapid order, keeps original committed order while the edited failed draft remains on screen, saves the retry-plus-edit order, reloads each saved order, and swaps JOB-1044 with the hidden full-order neighbor. All thirteen adapter read records preserve all six complete jobs/nested payloads. These checks establish baseline regression behavior rather than fixing the focus defect.

No-outline control `/tmp/lutriva-cycle11-work-NoUEQi/control-no-outline-output/browser.json` has the same 15 clipping failures plus 118 `outline-preserved` failures. Raw active controls still match `:focus-visible`, but computed outline style is `none`; the narrow PNG visibly lacks the ring. Deleting the indicator is detected even when a particular button rectangle fits.

Sticky control `/tmp/lutriva-cycle11-work-NoUEQi/control-sticky-focus-output/browser.json` has zero whole-ring/outline failures and three `wheel-changed-scroll` failures. Trusted deltaY=280 is recorded, yet before/100ms/900ms document scroll remains 67/67/67 (wide), 351/351/351 (narrow), and 267/267/267 (low). The original instead changes 68→157, 531→811, and 468→557 and retains those positions. Do not describe the sticky result as an observed post-100ms snap-back or a failed `wheel-retained` check: the return has already occurred by the first post-wheel sample, and equality then passes.

## Direct visual inspection

Viewed original-v2 `wide-focus.png`, `narrow-focus.png`, `low-focus.png`, and `wheel-retained.png`; no-outline `narrow-focus.png`; sticky `narrow-focus.png` and `wheel-retained.png` using the local image viewer. The three baseline boundary images visibly crop the focused last-row up ring at the bottom. No-outline narrow lacks its indicator. Sticky narrow boundary image shows a complete ring with room below; its wheel image leaves the focused first row centered, whereas the original wheel image displays later rows with focus legitimately offscreen. These observations agree with targeted JSON samples. I did not infer unseen upper-boundary PNGs; those findings come from raw sampled geometry.

## Author review pending

Awaiting parent handoff before reading trial sources, author evidence, final observer output or final PNGs. No conclusion about the author implementation yet.

## Final review after author handoff

Parent explicitly handed off the completed candidate and its terminal frozen-observer run. I then inspected the original/trial app/CSS/design diffs, post-author-scope-check.json, candidate-observer-01/browser.json, all four candidate PNGs, author RESULTS.md/check.mjs/workflows.mjs and all seven author browser.json reports. I additionally viewed author `workflows/failure.png` and `final-narrow/focus-top.png`. No new browser launch or evaluation was performed by this reviewer, and frozen criteria and first-stage review content remain unchanged.

Verdict: no concrete remaining defect was identified in the inspected implementation or evidence. The fixed candidate satisfies the frozen bounded scenarios; this supports this explicit product follow-up only.

### Implementation and integrity

The source diff is small and directly addresses the defect. `revealMoveFocus` cancels superseded work, schedules one animation frame after focusin, checks that the same button is still active, then calls nearest instant scrolling. The previous immediate post-render scroll is removed, while existing same-job/same-direction focus and operable boundary fallback remain. The delegated focusin handler covers native Tab/Shift+Tab and newly rendered controls. There is no recurring scroll loop, scroll listener or save-completion reveal. CSS adds only `scroll-margin: 7px` (6px existing indicator footprint plus rounding room); original geometry, brand, outline, labels and layout declarations are unchanged. DESIGN describes this implementation. Save serialization, failed-draft/retry logic and adapter writes are untouched.

Independent comparison found only `product/app.js`, `styles.css`, and `DESIGN.md` differ among the eight fixture sources. Candidate before/after source maps are equal; independently recomputed current trial hashes match the candidate's recorded after map. Evaluator/helper/criteria/data hashes match observer-freeze.json, and the candidate identifies the frozen original-v2 baseline with all three matching initial button profiles. The post-author scope report says verified=true with exactly those three allowed paths and no failures; its stated limit is final filesystem comparison, not proof of every historical tool action.

### Independent candidate observations

`/tmp/lutriva-cycle11-work-NoUEQi/candidate-observer-01/browser.json` records 1079/1079 checks, zero scenario errors and zero runtime exceptions. Counts include repetitive assertions and are not a quality percentage or evidence of broad uplift. More directly, I matched every one of the original's 15 failed whole-indicator sample names to the candidate's raw bounds: all now have no viewport or queue-panel clip, correct enabled focus, and the unchanged solid rgb(23, 108, 101) 3px outline with 3px offset. These include:

- `wide:10:Space`: same last-row JOB-1042/up ring bottom is 899.45, inside the 900px viewport (original 906.45).
- `narrow:10:Space`: ring bottom is 648.52, inside 650 (original 655.52); the button remains 72×44.
- `low:10:Space`: ring bottom is 499.45, inside 500 (original 506.45); the button remains 55.52×44.
- `narrow:15:Enter`: first-boundary JOB-1042/down ring top is 0.55 (original -6.45); `saved-feedback-focus` stays inside at top 0.95 after actual completion (original -6.05).
- `low:3:Tab` and `narrow:30/31:Shift+Tab` also fit, demonstrating native focus navigation is covered separately from reorder activation.

The candidate contains 118 whole-indicator/outline observations, 46 explicit focus-target checks, 96 button-style/size comparisons and 120 trusted-key checks. Observed keyboard second-frame samples occurred about 28–34.3ms after the recorded keydown; this is a recorded range, not a guarantee outside the tested environment. The matched formerly failing samples are already clear in their retained first frames as well.

All three boundary candidate PNGs visibly contain the complete teal ring at the bottom edge without changing the button or row styling. The candidate wheel PNG displays later rows while the first-row focus is offscreen, consistent with user-directed exploration. Trusted deltaY=280 moves document scroll 75→157 (wide), 531→811 (narrow), and 475→557 (low); each first post-wheel position remains unchanged at the 800ms follow-up. This avoids the sticky control's failure.

Regression evidence is substantive: three rapid moves complete in 101ms while state is saving and pending controls remain operable; actual adapter read and a fresh document confirm `[1041,1043,1044,1045,1042,1046]` (JOB- prefixes omitted here). In the failed scenario, the later draft `[1041,1043,1044,1042,1045,1046]` stays in error with explicit retry while adapter read still returns the original order. Natural keyboard retry plus a further pending edit commits and reloads `[1043,1041,1044,1042,1045,1046]`. Error, failed-edit-settled and retry-settled samples retain enabled focused controls with complete rings at 1280×900. Case-insensitive filtering leaves only JOB-1044, moves it from global rank 4 to 3 through hidden JOB-1043, and commits/reloads the full correct order after clearing the filter. All thirteen adapter reads again retain all six complete jobs and nested payloads.

### Separate author self-checks and limits

The author's four final keyboard reports each record 32 passing checks at 375×320, 320×240 with emulated reduced motion, 1280×240, and 620×360. Its workflows report records 14 passing checks, including 375×320 failure/retry and manual wheel across pending-save completion, plus one emulated touch move at 390×844. Raw narrow failure data shows the unchanged 6px outline footprint fits around a button ending at y=313.125 in a 320px viewport, and the viewed failure PNG agrees. The author trace also keeps y=1115 during wheel exploration across saving→saved, with focus intentionally offscreen; a subsequent Tab reveals the next target. The viewed author top-edge PNG has a complete ring.

These are supplemental author observations, not another independent frozen run. The author scripts use fixed waits, viewport rectangles without the frozen observer's live clipping-ancestor model, programmatic filter events and a DOM `.click()` for retry; the raw files do not include source hashes. The author's initial baseline has 15 clipping observations followed by its own retained adapter-expression SyntaxError; the intermediate `after` report precedes its final focus guard change. Neither is counted as a final regression pass or a new product failure.

The first-stage coverage limits continue to apply. The independent observer itself establishes failure/retry visibility only at 1280×900; the narrower case is author supplemental evidence. Only installed isolated headless Chrome/local synthetic data were exercised, and wheel retention is sampled over the stated bounded interval. Touch and reduced motion were emulated in author checks; physical devices, other engines, zoom, screen readers and native IME were not established. No broad skill improvement, guidance-version comparison, universal device guarantee or revision of the prior incomplete result is inferred.
