# refinement.md — django__django-11292

Maps every operation in `implementation_runCommand` to its `patch.diff`
counterpart across `BaseCommand.create_parser` and `BaseCommand.execute`
(`django/core/management/base.py`).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** deep-modeled changed op validated == real callee, **I** identical
concrete op.

## Patch (post-patch behavior)
```python
# create_parser, after --force-color:
if self.requires_system_checks:
    parser.add_argument(
        '--skip-checks', action='store_true',
        help='Skip system checks.',
    )
# execute:
if self.requires_system_checks and not options['skip_checks']:
    self.check()
```
The modeled value is the LAUNCH DECISION for a command run from the command line:
given `requires_system_checks` (does the command check?) and whether
`--skip-checks` was supplied, the outcome is one of `unrecognizedOption` (the
option is not registered, so argparse rejects the request), `ranChecks`
(`self.check()` is called), or `skippedChecks` (`execute` proceeds without
`self.check()`).

## Operation correspondence
| # | Lean op (`implementation_runCommand`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let skipOptionAvailable := commandPerformsChecks` | `if self.requires_system_checks: parser.add_argument('--skip-checks', ...)` | R | the `--skip-checks` argument is registered iff `requires_system_checks`; "the option exists" ↔ `skipOptionAvailable = commandPerformsChecks`. Type bijection in mapping.md (`requires_system_checks : bool` ↔ `commandPerformsChecks : Bool`). |
| 2 | `if skipRequested && !skipOptionAvailable then return RunResult.unrecognizedOption` | argparse `error: unrecognized arguments: --skip-checks` when `--skip-checks` is supplied but not registered | R | a skip on argv for a command that did not register the option ↔ argparse's unrecognised-argument rejection. `skipRequested ↔ '--skip-checks' on argv`, `!skipOptionAvailable ↔` argument not registered. |
| 3 | `let skip := skipRequested` | `options['skip_checks']` (post-patch; `False` by default when registered) | R | once the option is registered, the parsed value of `--skip-checks` is exactly whether it was supplied (store-true; default `False`). For a command-line launch this is `skipRequested`. |
| 4 | `if commandPerformsChecks && !skip then return RunResult.ranChecks` | `if self.requires_system_checks and not options['skip_checks']: self.check()` | R | the post-patch check gate, op-for-op: `requires_system_checks ↔ commandPerformsChecks`, `not options['skip_checks'] ↔ !skip`, `self.check()` reached ↔ `RunResult.ranChecks`. |
| 5 | `return RunResult.skippedChecks` | falling through the gate to `self.handle(...)` without calling `self.check()` | R | every remaining case (no checks performed, or checks performed but skipped) ↔ `execute` proceeds without `self.check()` ↔ `RunResult.skippedChecks`. |

Every op is R; **no A row** — there is no axiom consumed and no deep-model
reference of an unchanged callee. `self.check()` enters as the OUTCOME
(`ranChecks` vs `skippedChecks`), per mapping.md, not as a contract. Therefore
`meta.json axioms = []`, `deep_model_references = []`, and `axiom_check.py` is a
skip stub.

## R legs ⇒ G-CONF
The whole impl is R, so `conformance_check.py` mechanically differential-tests
the impl shadow against `patch.diff` behavior over ≥10^5 fuzzed inputs (the full
Bool × Bool domain plus repetition). `conf_skip = false`.

## Prepatch = the real bug
Pre-patch, `--skip-checks` is never registered as a parser argument (the
`if self.requires_system_checks: parser.add_argument('--skip-checks', ...)` block
is absent), so launching ANY command with `--skip-checks` makes argparse reject
it as an unrecognised option — including the F2P case of a command that performs
checks (`requires_system_checks = True`). The prepatch impl
(`implementation_runCommand` returning `unrecognizedOption` for any
`skipRequested`) is exactly this. It cannot satisfy `problem_spec_runCommand` on
the discriminating clause (`commandPerformsChecks = true → skipRequested = true →
result = RunResult.skippedChecks`): the carried gold proof's `refine_3` `rfl`
fails because the buggy impl yields `unrecognizedOption`, not `skippedChecks`.
This is precisely what the FAIL_TO_PASS test `test_skip_checks` exercises —
`run_manage(['set_option', '--skip-checks', '--set', 'foo'])` must succeed with no
error output (a command that performs checks, asked to skip, skips them). G-DIFF:
the prepatch `Solution_prepatch.lean` fails to verify.
