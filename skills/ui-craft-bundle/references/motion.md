# Motion and feedback

Give motion a job: show causality, preserve spatial continuity, reveal hierarchy, or acknowledge an action. Otherwise consider removing it.

Keep input feedback immediate. Never delay clicks, typing, or results to fit an animation. Durations are tunable starting points, not gates: roughly 100–180 ms for a small state transition and 180–280 ms for a panel can be reasonable on the web. Adapt to the existing system and platform.

- Prefer existing CSS or platform animation for simple effects. Use installed motion libraries for useful interruptible layout changes.
- Animate transform/opacity where practical. Avoid large animated blur/filter surfaces and layout work on every pointer move. Measure before claiming performance.
- Preserve focus and reading position. Do not move unrelated working content without a task reason.
- Handle interrupted transitions and rapid repeat input. Final state follows the latest intent, not animation completion order.
- Respect web `prefers-reduced-motion` and native system settings. Remove unnecessary travel, parallax, zoom, and loops while preserving clear state changes.
- Avoid repeated entrance choreography, cursor replacement, scroll hijacking, and animated background noise unless the requested experience needs them.
- Treat hover as a fine-pointer enhancement; keep actions usable with touch and keyboard.

Test a normal transition, interruption/repetition, and reduced motion for the changed component. Do not assert a frame rate without device-relevant measurement.
