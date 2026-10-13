# refinement.md — pydata__xarray-4075

The operation-by-operation correspondence between `model.py`'s implementation
(the `sum_of_weights_value` impl region, the deep folds `int_dot` / `bool_dot`,
and the live `dot_reduce` axiom) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement) / **A-consumed** (the proof uses this axiom's
`Ensures`) / **A-reference** (a deep model is validated == the real callee by
axiom_check.py / G-AX) / **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The reduction site — `Weighted._sum_of_weights` (`xarray/core/weighted.py:137`)

Gold hunk (body, the `sum_of_weights = self._reduce(...)` statement at line 145):
```
- sum_of_weights = self._reduce(mask, self.weights, dim=dim, skipna=False)
+ # bool -> int, because ``xr.dot([True, True], [True, True])`` -> True
+ # (and not 2); GH4074
+ if self.weights.dtype == bool:
+     sum_of_weights = self._reduce(
+         mask, self.weights.astype(int), dim=dim, skipna=False
+     )
+ else:
+     sum_of_weights = self._reduce(mask, self.weights, dim=dim, skipna=False)
```

| # | model.py impl op (`sum_of_weights_value`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `mask`, `weights`, `weights_are_bool` | `mask = da.notnull()` (boolean), `self.weights`, and the `self.weights.dtype == bool` predicate | R | the boolean presence mask ↔ `mask: List[int]` of 0/1; the weight array ↔ `weights: List[int]` of non-negative ints (booleans being 0/1); the weight dtype predicate ↔ `weights_are_bool` (mapping.md §2). |
| A2 | `boolean_dot = False` | the `if self.weights.dtype == bool: ... .astype(int) ... else: ...` branch | R | the patch ensures the operand handed to the dot is numeric (casting a boolean weight array to int; a non-boolean array is already numeric). In both branches the dot therefore runs in numeric arithmetic — exactly `boolean_dot = False` (mapping.md §2). The `weights_are_bool` knob is consumed only to fix the precondition class; the gold path never lets the dot go boolean. |
| A3 | `result = dot_reduce(ToSeq(mask), ToSeq(weights), boolean_dot)` | `self._reduce(mask, <numeric weights>, dim=dim, skipna=False)`, i.e. `dot(mask, <numeric weights>, dims=dim)` | A-consumed (`dot_reduce`) | the array dot product is the **unchanged** community callee (`xarray.core.computation.dot`); the patch changes only the operand dtype, never the dot. The proof consumes `dot_reduce`'s `Ensures`: with `boolean_dot == False` the result is `int_dot(mask, weights)` (mapping.md §3.1). |
| A4 | `int_dot(mask, weights) == sum_i mask[i]*weights[i]`, the deep front-recursive fold; `bool_dot` the saturating one | the numeric vs boolean contraction semantics of the real `dot`/`numpy.einsum` over the operands | A-reference | the two contraction semantics are modeled **deeply** (`int_dot` / `bool_dot`, spelled out in the `pure` region), NOT hidden behind a stronger axiom. They are validated **== the real dot** out of band: G-AX (axiom_check.py) runs `xr.dot` on bool/int operand pairs and asserts `int_dot == numeric dot` (incl. the `astype(int)` cast = the gold patch) and `bool_dot == boolean dot` (the bug). |
| A5 | `return result` | `sum_of_weights` flows into the unchanged `valid_weights = sum_of_weights != 0.0` / `where(valid_weights)` masking, then is returned | R + I | the modeled value is the dot-reduction quantity the changed statement computes; the downstream `where` masking (unchanged) is the identity on the non-zero reductions the F2P tests produce (`da.weighted([True,True]).sum_of_weights() == 2 != 0`), so it does not affect the tested observation (mapping.md §1). |

The discriminating content of the change — handing the dot a **numeric** operand
so a boolean weight array does not collapse the contraction — lives in the single
`boolean_dot` knob: `boolean_dot = False` (model) ⇔ the `astype(int)` cast before
the dot (real). The pre-patch hands the weight array straight to the dot;
`model_prepatch.py` reproduces that (`boolean_dot = weights_are_bool`) and **fails**
the postcondition `Result() == int_dot(ToSeq(mask), ToSeq(weights))`: with
`weights_are_bool == True` the dot returns `bool_dot` (saturating to 0/1), which
differs from `int_dot` exactly when two or more present samples carry weight 1
(`bool_dot == 1 != 2 == int_dot` on `mask=[1,1], weights=[1,1]`) — precisely the
GH4074 case (G-DIFF).

## B. Why the spec admits NO wrong implementation

The postcondition `Result() == int_dot(ToSeq(mask), ToSeq(weights))` pins the
result to a **structural fold over the actual input carriers** (`int_dot` is the
arithmetic sum `sum_i mask[i]*weights[i]`), not to an opaque oracle or a constant.
Hence:

- An impl that lets the dot go boolean for boolean weights (the bug,
  `boolean_dot = weights_are_bool`) returns `bool_dot`, which saturates at 1 and
  cannot equal `int_dot` whenever the true count is `>= 2` — it fails.
- An impl cannot echo a constant: `int_dot` is grounded element-wise on `mask`
  and `weights`, so the result must be *produced by* the (numeric) dot over the
  given inputs (directive 8 — no answer-key oracle; `dot_reduce` returns a value
  determined by the inputs, never a pinned marker).
- An impl cannot overwrite the read-only inputs to satisfy the spec vacuously:
  `mask` and `weights` are required AND ensured at `Acc(list_pred(., 1/2))`
  (directive 5), so no full-permission mutation is available.
- The only verifying choice is to run the dot numerically (`boolean_dot = False`),
  which by A2/A3 refines to the `astype(int)` cast + the unchanged `dot` = the
  gold patch = resolves.

Every step above is R, A-consumed, A-reference, or I — no kind-3
(unexpressible-changed-op) step. The operation that genuinely *changed* — the
operand dtype handed to the dot, i.e. whether the contraction counts or saturates
— is captured by the `dot_reduce` axiom evaluated at the `boolean_dot` the impl
chooses, with the two contraction semantics modeled deeply (`int_dot`/`bool_dot`,
A-reference) and validated against the real `dot`. The only consumed axiom
(`dot_reduce`) is about the **unchanged** community callee (`xarray.core.computation.dot`);
none axiomatizes the function under change (`_sum_of_weights`).

## C. verify(model) ⇒ resolved

`sum_of_weights_value` verifies only if its result equals `int_dot` (the genuine
arithmetic weighted count) — which by A2/A3 it can achieve only by handing the
dot a numeric operand (`boolean_dot = False`), i.e. the patch's `astype(int)`
cast. By R (boolean mask / numeric weights ↔ `List[int]`; the unchanged `where`
masking is the identity on the tested non-zero reductions) the verified function
equals the gold `_sum_of_weights` on the tested inputs. By G-AX the deep models
`int_dot`/`bool_dot` equal the real `dot` (A-reference) and the `dot_reduce` axiom
matches the real callee (A-consumed). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and audited
callees — and the gold patch resolves both F2P tests
(`test_weighted_sum_of_weights_bool`, `test_weighted_mean_bool`; the mean bug is
entirely caused by the wrong `sum_of_weights`) (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity
(this document, G-EQ).
