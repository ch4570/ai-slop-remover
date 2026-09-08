# Cycle 12 independent review

No actionable correctness or coverage findings in the reviewed installer/exporter changes.

Read AGENTS.md, the two implementation changes, their test changes, release validation/caller code, and the original red/green command records. No repository edits, browser/network/dependency work, new agents, duplicate release trees, or duplicate test logs.

- Export: Python 3.9.6's installed `zipfile` implementation confirms `ZipFile.write` passes `strict_timestamps=False` into both timestamp clamps. Tests correctly expect the upper bound's two-second ZIP rounding. Coverage verifies both extremes, archive CRC, exact unique members and source bytes/hashes, real installation after extraction, preserved source bytes/mtimes, existing-output refusal, and invalid-release refusal before output-directory creation.
- Installer: `lstat` retains symlink rejection, including dangling links, and refuses every non-regular manifest before JSON reading. Missing manifest paths raise `OSError`, which the CLI already catches and reports without traceback; a direct `load_bundle` caller now receives `OSError` instead of the former wrapped `BundleError` for that case. No documented exception-type contract or affected in-repository caller was found. This is an ordinary pre-read type check, with no concurrent-path-replacement protection claimed.
- Tests: special-file snapshots record mode/mtime without opening pipes; regular-file, directory, and link checks remain intact. FIFO regressions cover list, status, dry-run, and install, use bounded child execution, and check unchanged workspace state even on timeout. Directory cases validate the new pre-read diagnostic; they do not represent four additional hang defects.
- Existing evidence inspected: exporter baseline ran five tests and failed only the two timestamp cases; patched run passed all five. Installer baseline had four FIFO timeouts and four directory diagnostic assertion failures; patched run passed both tests/all eight modes. Also read the retained completion chunk reporting 81 installer tests passed, without treating it as a fresh independent run.
- Direct checks: installed Python version/signature/source inspection and `git diff --check` succeeded. No integration suite was duplicated while the parent ran Python 3.9/3.12 checks. Changelog additions and the parent's subsequent final manifest refresh/integrated checks are outside this report's observed scope.

Reviewed SHA-256:

```text
5c0a4d31bc151b8b62c8fe670b883fad30822afdbacd7f1466707197dad49f5f  install.py
8d92f92a30bc3e0d84ea0dd652a5c39442a6b23b65bcc7dc3cb9670ae94fa866  scripts/export_bundle.py
10cfeb1d28d6e1d2bbd727be79d89d76ab12d8c544c67c569015746d07a89e13  tests/test_install.py
eef360929611a77c109025ac2b360b04590fa18c6634b3d25f2b40ffe5504dd7  tests/test_export_bundle.py
```
