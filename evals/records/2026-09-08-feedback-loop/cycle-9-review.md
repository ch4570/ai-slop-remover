# Cycle 9 bounded CLI option-terminator review

No blocking finding. The wrapper now recognizes help only before the first `--`.
`indexOf` plus a sliced view changes only the help decision: the original argument
array, including the terminator and following tokens, still reaches Python.
The existing optional leading `install` removal, empty-argument help, ordinary
help precedence and exact single-argument `--version` branch remain intact.
Help before a terminator continues to work without Python; help after it reaches
the installer's argument validation and cannot mask its failure.

Reviewed `bin/ai-slop-remover.js` and `tests/npm-cli.test.mjs` against base
`2ef9fa7e0417ad6c47666a0a6acfabe9c682039b`; `reviewed.diff` preserves that bounded
diff. The added tests cover both help spellings with/without `install`, exit 2,
empty stdout, Python's diagnostic and sentinel preservation. The existing
offline-package test additionally checks the invalid boundary through both
installed command aliases. I inspected that coverage but did not execute package
installation or the npm suite; the parent owns those checks.

Executed on macOS 26.6.2 arm64, Node v26.8.1 and Python 3.9.6:

```sh
python3 -B /private/tmp/lutriva-cycle9-code-review.YbR5mj/review.py
```

Result: exit 0. This compact script ran 12 wrapper cases and four direct-Python
comparisons, with exact command arrays/cwd, raw stdout/stderr and return codes
retained as `*.command.json`, `*.stdout`, `*.stderr`.

- Six no-Python help controls: no arguments, `--help`, `-h`, `install --help`,
  `--help -- ignored`, and `install -h -- ignored`; all exit 0 with wrapper help.
- Four invalid status cases: both `--help`/`-h` after `--`, with and without the
  optional `install` prefix. All exit 2 with empty stdout and the expected
  `unrecognized arguments: -- ...` diagnostic. Each exactly matches a direct
  Python invocation's exit/stdout/stderr for the same forwarded arguments.
- Two valid status controls: Codex with `ux-writing` selection reports its two
  missing dependencies/skills; Claude with the `install` prefix reports all seven
  missing skills. Both exit 0. The owned project path contains spaces.

The complete two-entry project snapshot (root and sentinel) retains identical
paths, types, modes, nanosecond mtimes and file bytes across every command.
`result.json`, `project-before.json` and `project-after.json` record the checks.
No installation occurred, and no repository, real user skill or global setting
was changed. No network, browser, Windows execution, broad suite or source-tree
archive was used. Status controls cover missing installations, not installed
receipt behavior. Baseline failure was reviewed from source rather than rerun.

The reviewed bytes stayed unchanged during these checks:

| File | SHA-256 |
| --- | --- |
| `bin/ai-slop-remover.js` | `e4b54b244018100ebe79c768862d43a280d6805739f88b15c950ea95e5951ada` |
| `tests/npm-cli.test.mjs` | `3869665e41bf07e3882a4114e65ba44248f3d0c5de9b5d4b6c916a7c1d2be8f9` |
| `install.py` | `1ff8fee6a58aff6dbc00de529b6ee7ce343e760e70111f1f6d5fe395b441b88d` |
