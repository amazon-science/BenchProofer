# refinement.md — sympy__sympy-13480

Operation-by-operation correspondence between `Solution.lean`'s impl region and
`patch.diff` (the gold patch, applied at `base_commit`). Every row is tagged
**R** (type refinement), **A-consumed** (proof uses this opaque symbol's
contract), **A-reference** (deep model validated == real callee by G-AX), or
**I** (identical concrete operation). No kind-3 (changed-but-inexpressible) step.

The patch is a one-token fix at `hyperbolic.py:590`: the branch test
`if cotm is S.ComplexInfinity` (an unbound name) becomes
`if cothm is S.ComplexInfinity` (the value computed at line 589). The modeled
method `cothEvalPeriodic` is the body of that branch.

| # | Solution.lean impl op | patch.diff / repo op (post-patch) | tag | justification |
|---|---|---|---|---|
| 1 | `let computed := primaryEval m` | `cothm = coth(m)` | A-consumed + R | `primaryEval` is the opaque model of the unchanged `coth` callee; argument `m` (periodic part) is an `Int` handle refining the sympy `Expr` (R). The proof consumes only its determinism (opaque ⇒ a fixed argument denotes a single fixed value), so `primaryEval m` is the well-defined quantity later inspected. |
| 2 | `if computed = directedInfinity then` | `if cothm is S.ComplexInfinity:` | A-consumed + R + I | `directedInfinity` is the opaque model of the unchanged `S.ComplexInfinity` singleton; `=` on the `Int` handle refines the `is` identity test on the singleton (R: handle equality ↔ singleton identity). The discriminator is the value computed in row 1 — this IS the fixed token (`cothm`, not the buggy `cotm`). Control structure identical (I). |
| 3 | `return primaryEval x` (true branch) | `return coth(x)` | A-consumed + R | `primaryEval` = `coth`; `x` (remainder part) is an `Int` handle refining the `Expr`. Identical control: the ComplexInfinity branch returns the primary function on the remainder. |
| 4 | `return siblingEval x` (else branch) | `return tanh(x)` | A-consumed + R | `siblingEval` is the opaque model of the unchanged `tanh` callee; `x` as in row 3. Identical control: the finite/zero branch returns the sibling function on the remainder. |
| 5 | `if/else` two-way branch | `if/else` two-way branch | I | identical concrete control flow. |

## Notes

- **No A-reference, no deep model.** The changed operation (the branch test) is
  modeled directly with the same control/data flow; the things made opaque
  (`coth`, `tanh`, `cot`, `S.ComplexInfinity`) are the UNCHANGED callees the
  branch consults. There is no changed operation hidden behind an opaque symbol.
- **A-consumed contract is just determinism.** The opaque symbols carry no
  asserted `ensures`; the proof relies only on opaque-determinism (a fixed
  argument → a fixed result handle). This is the weakest sufficient contract
  (SPEC_GUIDE directive 7) and cannot over-claim a value, sentinel, or raise
  behavior. They are FREE — nothing to validate against the real callee, so
  G-AX is skipped (no `axiom_check.py`).
- **The discriminating I is "branch on `coth m`, not `cot m`."** The
  observable, behavior-fixing operation the patch changes is the DATA SOURCE of
  the branch condition. `Solution.lean` reads the condition from `primaryEval m`
  (the row-1 value = `coth(m)`). `Solution_prepatch.lean` reads it from an
  unrelated family function `cofamilyEval m` (the model of the typo's `cot m`),
  exactly mirroring the pre-patch unbound-name defect (`cotm` ≠ the computed
  `cothm`). The discriminating postcondition
  `out = if primaryEval m = directedInfinity then primaryEval x else siblingEval x`
  is unprovable for any discriminator that is not `primaryEval m` — which is why
  the prepatch fails (`primaryEval` and `cofamilyEval` are distinct opaque
  functions, so loom cannot prove they straddle the sentinel identically), and
  any wrong data source is rejected.
