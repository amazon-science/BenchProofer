# refinement.md — sympy__sympy-13480

Operation-by-operation correspondence between `model.py`'s impl region and
`patch.diff` (the gold patch, applied at `base_commit`). Every row is tagged
**R** (type refinement), **A-consumed** (proof uses this axiom's contract),
**A-reference** (deep model validated == real callee by G-AX), or **I**
(identical concrete operation). No kind-3 (changed-but-inexpressible) step.

The patch is a one-token fix at `hyperbolic.py:590`: the branch test
`if cotm is S.ComplexInfinity` (an unbound name) becomes
`if cothm is S.ComplexInfinity` (the value computed at line 589). The modeled
function `periodic_part_simplification` is the body of that branch.

| # | model.py impl op | patch.diff / repo op (post-patch) | tag | justification |
|---|---|---|---|---|
| 1 | `primary_m = primary(m)` | `cothm = coth(m)` | A-consumed + R | `primary` axiomatizes the unchanged `coth` callee; argument `m` (periodic part) is an `int` handle refining the sympy `Expr`. The proof consumes the axiom's contract = determinism (`@Pure`), so `primary(m)` denotes a single fixed value. |
| 2 | `if primary_m == directed_infinity():` | `if cothm is S.ComplexInfinity:` | A-consumed + R + I | `directed_infinity()` axiomatizes the unchanged `S.ComplexInfinity` singleton; `==` on the handle refines the `is` identity test on the singleton (R: handle equality ↔ singleton identity). The discriminator is the value computed in row 1 — this IS the fixed token (`cothm`, not the buggy `cotm`). |
| 3 | `return primary(x)` (true branch) | `return coth(x)` | A-consumed + R | `primary` = `coth`; `x` (remainder part) is an `int` handle refining the `Expr`. Identical control: the ComplexInfinity branch returns the primary function on the remainder. |
| 4 | `return sibling(x)` (else branch) | `return tanh(x)` | A-consumed + R | `sibling` axiomatizes the unchanged `tanh` callee; `x` as in row 3. Identical control: the finite/zero branch returns the sibling function on the remainder. |
| 5 | `if/else` two-way branch | `if/else` two-way branch | I | identical concrete control flow. |

## Notes

- **No A-reference, no deep model.** The changed operation (the branch test) is
  modeled directly with the same control/data flow; the things axiomatized
  (`coth`, `tanh`, `S.ComplexInfinity`) are the UNCHANGED callees the branch
  consults. There is no changed operation hidden behind a `@ContractOnly`.
- **A-consumed contract is just determinism.** The axioms carry no `Ensures`;
  the proof relies only on `@Pure`-determinism (a fixed argument → a fixed
  result). This is the weakest sufficient contract (SPEC_GUIDE directive 7) and
  cannot over-claim a value, sentinel, or raise behavior. G-AX
  (`axiom_check.py`) confirms determinism + singleton identity AND validates
  the end-to-end branch correspondence: the real gold-patched `coth.eval`
  returns `coth(x)` exactly when `coth(m)` is `S.ComplexInfinity` and `tanh(x)`
  otherwise.
- **The fix delta is the discriminator's data source.** model.py reads the
  branch condition from `primary(m)` (the row-1 value). `model_prepatch.py`
  reads it from an unrelated quantity (`primary(x)`), exactly mirroring the
  pre-patch unbound-name defect (`cotm` ≠ the computed `cothm`). The
  discriminating postcondition
  `Implies(primary(m) == directed_infinity(), Result() == primary(x))`
  is unprovable for any discriminator that is not `primary(m)` — which is why
  the prepatch fails and any wrong data source is rejected.
