# refinement.md — django__django-13658

Maps every operation of `implementation_progName` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX/G-CONF),
**I** (identical concrete op).

## Operation correspondence

| # | Lean op (`implementation_progName`) | patch.diff / real-source counterpart | tag |
|---|---|---|---|
| 1 | `argv : List String`, `_ambient : List String` params | `self.argv` (from the utility's `argv` argument) vs `sys.argv` (ambient) | R — `list[str]` ↔ `List String` |
| 2 | `basename argv.headI` | `os.path.basename(self.argv[0])` (`__init__:190`), the value the fix threads into the parser via `prog=self.prog_name` (`:347`) | A-reference — POSIX basename modeled deeply as `(·.splitToList (· = '/')).reverse.headI`; validated == real by G-CONF |
| 3 | `if progName = "__main__.py" then progName := "python -m django"` | `if self.prog_name == '__main__.py': self.prog_name = 'python -m django'` (`:191-192`) | I — identical concrete conditional / constant |
| 4 | `return progName` (never reads `_ambient`) | the fix passes `prog=self.prog_name`, so `%(prog)s` resolves from the utility argv, NOT `sys.argv[0]` (`:347`, the changed line) | R — the frame: result depends on `argv` only, `_ambient` unused |

## Discriminating clause (why the prepatch is the real bug)

The gold change is precisely op #4: before the fix the option parser's `%(prog)s`
defaults to `os.path.basename(sys.argv[0])` (the ambient vector); after, it is
`self.prog_name` (the utility's own vector). `Solution_prepatch.lean` encodes the
buggy leg by computing `basename _ambient.headI` instead of `basename argv.headI`.
Whenever `argv.headI ≠ _ambient.headI` (mod the special case) the prepatch result
disagrees with `computeProgName argv.headI`, so `correct_progName` is unprovable —
exactly what G-DIFF requires, and what the F2P test
`test_program_name_from_argv` observes (argv `['django-admin', …]` while
`sys.argv[0]` is mocked to `None`).

## Conformance (R/I legs → G-CONF)

Ops #1–#4 are all R/I (no consumed axioms). `conformance_check.py` transliterates
the impl op-for-op (`basename`, `compute_prog_name`, `shadow_prog_name`) and diffs
it against `ManagementUtility(argv).prog_name` evaluated with `sys.argv` mocked to
an unrelated vector, over ≥1e5 fuzzed inputs (seed 13658). Zero disagreements ⇒
the deep `basename`/special-case model and the ambient-independence frame both
match the real patched computation.

## No dead axioms

`basename` (op #2) is a deeply-modeled changed op → A-reference (G-CONF-checked),
NOT a consumed axiom. `axiom_check.py` is a skip stub (no `opaque`/`_prop`).
`meta.json conf_skip = false` (the impl region is all R/I, not all-A).
