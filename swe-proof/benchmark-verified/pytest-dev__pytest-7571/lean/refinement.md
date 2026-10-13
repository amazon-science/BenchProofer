# refinement.md — pytest-dev__pytest-7571

Operation-by-operation correspondence between `implementation_captureLevel`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH capture-handler
level lifecycle of `LogCaptureFixture`: `__init__` + `set_level` calls +
`_finalize`). Tags: **R** type refinement, **A-consumed** proof uses an axiom,
**A-reference** deep model validated == real callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let mut st : Int × Option Int := (initialLevel, none)` | `__init__`: handler starts at `self.handler.level` (= `initialLevel`); `self._initial_handler_level = None` | R |
| 2 | `for lvl in levels do st := (lvl, some st.1)` | each `set_level(level)`: `self._initial_handler_level = self.handler.level` (record current) then `self.handler.setLevel(level)` (raise) | R |
| 3 | `match st.2 with \| some s => s \| none => st.1` | `_finalize`: `if self._initial_handler_level is not None: self.handler.setLevel(self._initial_handler_level)` else leave the handler level | R |

Notes:

- **Every step is R — no A, no I.** The whole lifecycle is the behavior the patch
  changes (recording the pre-raise level and re-applying it at teardown), so it is
  modeled DEEPLY over the observable inputs; SPEC_GUIDE §3 forbids axiomatizing a
  deeply-modeled changed op. The `axioms` region is empty; **G-AX skips**.
- **R, not I.** The Python objects (`self`, the capture handler, the `None`/`int`
  `_initial_handler_level`) are refined to the carrier `Int × Option Int`
  (`(currentThreshold, recordedThreshold)`) and the inputs
  `initialLevel : Int` / `levels : List Int` per the mapping.md bijection. A
  `str` level argument is normalized by `logging` to its resolved `int` before
  reaching the handler, so the modeled element type is the integer level.
- **The fix itself** is step 2's record (`some st.1`) coupled with step 3's
  re-application. The thread component `st.1` is the current handler level; on
  each raise the *prior* value `st.1` is captured into `some …` (last-write-wins,
  matching the gold `self._initial_handler_level = …` plain assignment, NOT a
  `setdefault`), and teardown re-applies the most recent capture. The pre-patch
  impl (`Solution_prepatch.lean`) keeps NO record (`let mut handler := …; for lvl
  in levels do handler := lvl; return handler`) and so leaves the handler at the
  last raised level — the actual leak; that impl's carried gold proof fails to
  typecheck against the spec on any test with ≥1 raise whose pre-last-raise level
  differs from the last raised level (G-DIFF).
- The `_initial_logger_levels` dict and named-logger restoration are unchanged by
  the patch and independent of the capture-handler level (the only observable the
  issue and the F2P test concern), so they are not modeled (mapping.md).
- **G-CONF** mechanically refutes the R legs: a faithful in-process replica of the
  post-patch lifecycle (`__init__` → each `set_level` → `_finalize`) is diffed
  against the impl shadow over ≥1e5 fuzzed `(initialLevel, levels)` inputs. No A
  legs.
