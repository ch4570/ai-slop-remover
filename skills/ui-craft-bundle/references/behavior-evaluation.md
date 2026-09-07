# Evaluate changes on actual UI tasks

Use this when testing a skill version or a broad workflow improvement. Ordinary product fixes use the project's existing tests; they do not require a benchmark suite.

## Define an observable task

Choose a small local or otherwise authorized test surface with synthetic data. Record the starting revision, task prompt, design constraints, and concrete checks before the agent starts. Examples: failed save keeps the draft and ends pending; composition Enter does not submit; query edits preserve useful Back navigation; a new page reuses documented semantic tokens.

Keep the task and starting fixture stable. Store outcome checks separately from the editable application so the agent cannot fix the benchmark by removing its assertions. Retain both success-path protection and seeded-defect checks. Do not put production credentials or private user data into fixtures.

## Keep comparisons fair

For baseline/candidate comparisons, use separate copies of the same starting fixture, task, model, settings, viewport, data, and tool availability. Record skill revisions and any other differing variable. Do not change the prompt to favor one version or silently give one agent additional tools. Label non-comparable runs as incomplete for improvement claims.

One trial can establish that its checks passed in that environment. It cannot establish universal aesthetic quality, reliable uplift across models, or a statistically meaningful success rate. Repeated comparisons are useful when variability matters; do not invent an arbitrary mandatory trial count.

## Observe behavior and appearance separately

Run external assertions against real DOM/state outcomes. Record the expected result, actual result, command or interaction, evidence location, and pass/fail/not-run. Synthetic composition events test handler logic; native IME behavior needs an actual input-method test. Browser emulation does not prove a physical-device result.

Actually open screenshots before giving visual findings. Assess hierarchy, content visibility, brand consistency, and whether the main task remains clear using comparable viewports/data. A render command alone is not visual inspection. Avoid a single beauty score that hides inaccessible controls or broken behavior.

Retain the applied diff and inspect scope: fixing a save error must not replace the brand, delete features, weaken tests, or invent persistence. A trial with no visual tooling may still provide useful functional evidence, while visual claims stay not-run.

## Record and interpret results

Use [behavior-trial.md](../assets/behavior-trial.md) when recording a trial. Existing evaluation tooling may validate result records and compare comparable runs. Result validation checks the record, not the truth of every observation; link to raw execution evidence and disclose its origin.

- A required failed check means changes are needed, even if other checks improved.
- A missing or not-run required check means evidence is incomplete.
- A candidate that passes after a baseline failure recovered that defect in this trial.
- Equal passes show preserved behavior in the observed scope, not measured improvement.
- Keep manual visual judgments separate from executable checks and do not replace either with an agent's unsupported self-report.

The source distribution includes a small evaluation harness for maintainers. Installed copies of this skill remain tool-independent and do not assume that harness or a browser is available in the user's project.
