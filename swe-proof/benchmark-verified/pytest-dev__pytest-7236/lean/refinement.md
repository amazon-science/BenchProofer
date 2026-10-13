# refinement.md — pytest-dev__pytest-7236

Operation-by-operation correspondence between `implementation_deferTeardown`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH teardown-postponement
decision inside `TestCaseFunction.runtest`). Tags: **R** type refinement (state
the bijection), **A-consumed** (proof uses an axiom's property), **A-reference**
(deep model validated == real callee by G-AX), **I** identical concrete op.

The modeled value is the Boolean "was teardown postponement arranged for this
test case". The real `runtest` arranges postponement (stores the bound `tearDown`
and installs a no-op) exactly when, on the synchronous path, the debugger option
is active and the case is not skipped.

| # | Lean op (impl region) | patch.diff / runtest counterpart | tag | notes |
|---|---|---|---|---|
| 1 | `if isAsync then return false` | `if is_async_function(self.obj): self._testcase(self)` — the async branch never reaches the postponement code | R | `isAsync : Bool` ↔ `is_async_function(self.obj)` (mapping.md). The async branch arranges no postponement, so the modeled decision is `false` there. |
| 2 | `if usePdb && !skipped then return true` | `if self.config.getoption("usepdb") and not _is_skipped(self.obj):` (the post-patch guard) → the `if` body runs (postponement arranged) | I | `usePdb : Bool` ↔ `getoption("usepdb")` truthiness; `skipped : Bool` ↔ `_is_skipped(self.obj)` = `bool(getattr(self.obj, "__unittest_skip__", False))`. Conjunction is the same Boolean test. |
| 3 | final `return false` | the `if` body is skipped (no `_explicit_tearDown` set, `tearDown` left intact) → postponement NOT arranged | I | synchronous path, guard false. |

No row is A-consumed or A-reference: the decision is a pure Boolean function of
three observables, all entering as plain `Bool` data. `_is_skipped` is not
axiomatized — its result IS the modeled observable `skipped` (refinement of a
`bool(getattr(...))` truthiness test to a `Bool`). The R legs (and the I legs,
which are R with the identity bijection on `Bool`) are mechanically refuted by
G-CONF over the exhaustive 8-point input space plus seeded fuzz.

## Changed-op faithfulness

The single changed op is the guard: pre-patch `if usePdb:` → post-patch
`if usePdb and not _is_skipped(self.obj):`. The impl mirrors this exactly:
`if usePdb && !skipped then return true`. The prepatch impl
(`Solution_prepatch.lean`) drops the `!skipped` conjunct (`if usePdb then return
true`), which is precisely the regression: a skipped case under `--pdb` would have
its teardown postponed (and the stored teardown later invoked), so it disagrees
with the spec on `(isAsync=false, usePdb=true, skipped=true)` — exactly the
discriminating point the F2P test
`test_pdb_teardown_skipped[@unittest.skip]` exercises.
