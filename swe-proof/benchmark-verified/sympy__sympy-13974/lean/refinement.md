# refinement.md — sympy__sympy-13974

Maps every operation in `implementation_tensorPow` to its `patch.diff`
counterpart in the new `tensor_product_simp_Pow`. Tags: **R** type refinement,
**A-consumed** proof-consumed axiom, **A-reference** deep-modeled callee (G-AX
validated), **I** identical concrete op.

| # | Lean impl op | patch.diff / source op | tag | note |
|---|---|---|---|---|
| 1 | `QExpr` carrier (`atom`/`tp`/`pow`) | the runtime expression passed to `tensor_product_simp_Pow` (atom vs `TensorProduct` vs `Pow`) | R | bijection in mapping.md. `isinstance` dispatch ↔ the inductive constructor match. |
| 2 | outer `match e with \| .pow base exp => … \| _ => return e` | `if not isinstance(e, Pow): return e` (non-`Pow` returned unchanged) | R/I | the non-`Pow` arm is the `else`-of-`isinstance(e,Pow)` early return; refined to the `_ => return e` constructor arm. |
| 3 | inner `match base with \| .tp args => … \| _ => return e` | `if isinstance(e.base, TensorProduct): … else: return e` | R/I | base-is-tensor-product dispatch; the `else` returns the input power unchanged. |
| 4 | `args.map (fun b => QExpr.pow b exp)` | `[ b**e.exp for b in e.base.args]` | I | per-factor power: `QExpr.pow b exp` ↔ `b**e.exp`; `List.map` ↔ the comprehension. |
| 5 | `QExpr.tp (…)` | `TensorProduct(*[…])` | R | assemble the mapped factors into a tensor product; constructor refined to the `QExpr.tp` carrier (see mapping.md constructor note — ≥2 non-commutative factors regime). |

No changed op is inexpressible; the whole new function is modeled deeply and
concretely. No callee is consumed as an axiom and none is deep-model-referenced
(`isinstance`/`TensorProduct(*…)`/`**` are refined to constructor match /
`QExpr.tp` assembly / `QExpr.pow` formation, per mapping.md). axiom_check.py is
therefore a skip stub.

The R/I legs (all rows) are mechanically refuted by G-CONF, which builds the
Python shadow of `implementation_tensorPow` and differential-tests it against the
real patched `tensor_product_simp_Pow` over fuzzed expressions covering every
branch (power of a tensor product, power of a non-tp base, bare tensor product,
bare atom).

## Prepatch (G-DIFF)

The pre-patch buggy behavior: before the fix there was no `tensor_product_simp_Pow`
and `tensor_product_simp` evaluated `Pow` as `tensor_product_simp(e.base) ** e.exp`
— for a tensor-product base this left the power **undistributed** (the power
simplified to itself, e.g. `TP(A,B)**x` stayed `TP(A,B)**x` rather than
`TP(A**x, B**x)`). `Solution_prepatch.lean` models exactly this: the
`.tp` base arm returns the input `e` unchanged instead of distributing the
exponent. Its carried gold proof body (`rfl` against `specTensorPow`) fails to
typecheck because the buggy impl does not equal the reference evaluation on the
discriminating clause — the G-DIFF signal.
