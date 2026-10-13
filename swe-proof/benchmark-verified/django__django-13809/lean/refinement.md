# refinement.md — django__django-13809

Maps every operation in `implementation_serverStartup` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `serverStartup` (`runserver`'s `inner_run`)

Post-patch repo code (`patch.diff`, relevant region):
```python
def inner_run(self, *args, **options):
    ...
    if not options['skip_checks']:
        self.stdout.write('Performing system checks...\n\n')
        self.check(display_num_errors=True)
    self.check_migrations()
    ...                                  # banner write
    run(self.addr, int(self.port), handler, ...)
```
(plus the `add_arguments` change registering `--skip-checks`, which only feeds
`options['skip_checks']`.)

Lean impl (`implementation_serverStartup`):
```lean
def implementation_serverStartup (skipChecks : Bool) : List StartupAction := Id.run do
  let mut log : List StartupAction := []
  if !skipChecks then
    log := log ++ [StartupAction.announceChecks]
    log := log ++ [StartupAction.runChecks]
  log := log ++ [StartupAction.checkMigrations]
  log := log ++ [StartupAction.writeBanner]
  log := log ++ [StartupAction.serve]
  return log
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `skipChecks : Bool` | `options['skip_checks']` (fed by the new `--skip-checks` arg) | **R** | the boolean control; truthiness ↔ `skipChecks`. The `add_arguments` line `parser.add_argument('--skip-checks', action='store_true', ...)` only registers the option that populates this value, so it carries no observable behavior of its own beyond making `skip_checks` available. |
| 2 | `let mut log := []` | the empty observable trace before the routine runs | **R** | the action accumulator ↔ the sequence of side-effecting steps `inner_run` performs. |
| 3 | `if !skipChecks then …` | `if not options['skip_checks']:` | **I** (the changed op) | **the fixed operation.** The gate that newly conditions the system-check step on the control. Pre-patch this guard was absent (the step ran unconditionally); the patch wraps it in `if not options['skip_checks']:`. |
| 4 | `log := log ++ [announceChecks]` | `self.stdout.write('Performing system checks...\n\n')` | **R** | the announcement write ↔ the `announceChecks` action; emitted iff `not skipChecks`. (Abstracts the literal string to an observable step — its presence is what `test_skip_checks` greps for.) |
| 5 | `log := log ++ [runChecks]` | `self.check(display_num_errors=True)` | **R** | the system-check call ↔ the `runChecks` action; emitted iff `not skipChecks`. (Abstracts the call to its observable occurrence — what `test_skip_checks` asserts via `mocked_check.(assert_not_)called`.) |
| 6 | `log := log ++ [checkMigrations]` | `self.check_migrations()` | **R** | always-performed migration check ↔ the `checkMigrations` action; pinned in both branches (directive 5 frame). |
| 7 | `log := log ++ [writeBanner]` | `self.stdout.write(... version/addr/port ...)` | **R** | always-performed banner write ↔ the `writeBanner` action; pinned in both branches. |
| 8 | `log := log ++ [serve]` | `run(self.addr, int(self.port), handler, ...)` | **R** | always-performed server start ↔ the `serve` action; pinned in both branches. |
| 9 | `return log` | the routine's observable side-effect sequence | **R** | the function returns no value; we model it as returning the action trace it emits up to serving. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the patched gated control flow.

## Soundness check (verify ⟹ correct)

- `problem_spec_serverStartup skipChecks result := result = (if skipChecks then
  [] else [announceChecks, runChecks]) ++ tailSteps` pins the result EXACTLY
  (full list equality to an input-grounded expression) — directive 5 (frame):
  the entire trace is determined by `skipChecks`. The unchanged tail
  (`checkMigrations, writeBanner, serve`) is pinned to its fixed value in BOTH
  branches; the gated prefix is present exactly when `skipChecks` is false. No
  output component is left unconstrained; no ungrounded oracle (directive 8) —
  the postcondition is dischargeable only by computing the actual gated trace.
- The prepatch impl emits `[announceChecks, runChecks]` unconditionally
  (ignoring `skipChecks`). It violates the spec on the discriminating clause
  `skipChecks = true`, where it returns `announceChecks :: runChecks :: tailSteps`
  but the spec requires `tailSteps` alone. Its carried gold proof
  (`cases skipChecks <;> rfl`) cannot close — the `true` branch fails to reduce
  (G-DIFF/G-PANEL); confirmed by `lean_verify.sh` exiting 1 at that `rfl`.
- This discriminating case is precisely what the FAIL_TO_PASS test
  (`test_skip_checks`) exercises: calling `runserver` with `skip_checks=True`
  asserts the announcement is absent from stdout AND `check` is not called — i.e.
  the `skipChecks = true` branch must omit the `[announceChecks, runChecks]`
  prefix. The `skip_checks=False` sub-case asserts both are present, matching the
  `false` branch.
- G-CONF confirms the R/I shadow == the in-process replica of the patched
  control flow over both boolean values plus ≥1e5 fuzzed inputs.
