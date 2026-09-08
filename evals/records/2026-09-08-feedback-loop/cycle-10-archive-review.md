# Independent cycle-10 archive handoff audit

No archive handoff blocker was found in the checks performed. This is a read-only integrity and report-consistency audit. No archive member was extracted to disk, no decoded historical log was duplicated, and no browser, replay, web request, dependency installation, repository edit, or input modification was performed.

## Integrity checked

- The existing repository command `python3 scripts/check_evidence_archive.py evals/records/2026-09-08-feedback-loop/cycle-10-inventory.json evals/records/2026-09-08-feedback-loop/cycle-10.tar.gz` exited 0: exact schema-1 inventory, 253 regular files, 185,945,040 member bytes.
- Archive SHA-256 matches `107054faa0f3e7216128ccb45919af838704dfc4e4f5617bd0e303a3f2fc1924`; its compressed size is 15,891,538 bytes. Inventory SHA-256 matches `9dafdd9ef3c9a25b4bb8f5657eb435ac6a80ef84dbd17b0e92e214822141251d`.
- The independent audit script exited 0. All 18 historical `.gz` members from attempts 02/03 were streamed through gzip to EOF. Each decoded size/SHA and each compressed size/SHA matches archived `work/evidence-compression.jsonl`; total decoded bytes are 165,322,198. The ledger contains 18 unique verification/removal pairs in the declared order. No uncompressed duplicates of those logs exist in the archive.
- Archived fixed results retain baseline 2 pass/6 fail and candidate 5 pass/1 fail/2 human-review-or-not-run, with 691/530 snapshots respectively. Candidate scenario 04 still has six failed assertions. Archived supplementary reports retain original exit 1/final 124356 and candidate exit 0/final 134256. Recorded collection/runtime errors remain empty and sourceUnchanged true in these final runs; these are retained observations, not newly executed behavior.
- Archived `review/REVIEW.md` and repository `cycle-10-review.md` both hash to `5c39b7be79756d9a5554908e23c9580690fee99015603813a42ef0fa7d117ff6`. The partial attempt-04 browser report remains present.

## Conclusions and handoff limits

The final `cycle-10.md` I read (SHA-256 `4703c63e5aa3fa491f9a399237d588952d94d396b287568a4b2690569ddbc3e4`) agrees with my independent product review and archived fixed/supplemental reports on the material conclusions. It preserves the frozen automatic-recovery-policy failure, labels the retry supplement post-author, avoids turning its result into a rewritten preregistered score, distinguishes exit 0 from all product checks passing, and does not claim skill-version A/B or general skill improvement. The earlier setup/calibration failures and partial ENOSPC evidence remain disclosed.

The residual focus-outline defect is still explicit: archived candidate wide sequence 5 has JOB-1045/up bottom 900.453125 in a 900px viewport, with 3px outline and 3px offset. The correct focused button and subsequent key operation do not establish an unclipped complete ring. Narrow full-page framing remains an artifact limitation; the retained viewport geometry does not establish horizontal overflow or a fully proven cause of the full-page framing difference.

Archived `archive-tools/ARCHIVE-README.md` accurately discloses that `scope-controls/` contains only `REPORT.md`, `evidence.json`, and `run-controls.mjs`. I checked that exact file set. It expressly omits the synthetic control trees, including their intentional symlink. It also discloses historical absolute paths, the supplement's original `/tmp/lutriva-queue-observer-RAcypp` import, the need for an explicitly recorded relocation adapter/new freeze, and that no relocated browser replay was performed. The final observer's relative-path implementation is not generalized to every helper. The provenance map has 252 entries; the separately inventoried 253rd file is the generated provenance map itself, and the archived builder includes it in its post-build checks.

The separate `cycle-10-archive-build.json` retains the parent's exact command/output records for tar creation, repository static checking, whitespace checking, and all ten archive hashes. I inspected those records but did not rerun npm, whitespace, or the other nine archive validations in this bounded audit. Repeated integrity checks add no behavioral coverage. Byte/ledger agreement cannot independently establish historical truth, full agent transcripts, absence of intermediate writes, exhaustive UI quality, or successful replay after relocation.

## Audit files

- `audit-archive.py`: independent streaming gzip and archived-outcome inspection.
- `independent-audit.log.json`: exact command result, process exit, stdout, per-member decoded/compressed hashes, preserved outcomes, and limits.
- `repository-checker.log.json`: exact repository-checker command result and exit.

These new audit files are outside the already finalized archive, in `/tmp/lutriva-cycle10-archive-audit-rLKUGH`; the previous archived review directory was not modified.
