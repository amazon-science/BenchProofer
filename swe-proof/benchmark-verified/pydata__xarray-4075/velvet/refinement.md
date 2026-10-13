# refinement.md — pydata__xarray-4075

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `sumOfWeights` `do` block, the deep `reduceDot`/`arithDot`/`anyMasked`
models, and `sumOfWeightsSpec`) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed** where
the proof uses an axiom's `ensures`, **A-reference** where a deep model is
validated == the real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change site — `Weighted._sum_of_weights` (`xarray/core/weighted.py:137`)

Gold hunk (lines 142-152):
```
  mask = da.notnull()
- sum_of_weights = self._reduce(mask, self.weights, dim=dim, skipna=False)
+ if self.weights.dtype == bool:
+     sum_of_weights = self._reduce(mask, self.weights.astype(int), dim=dim, skipna=False)
+ else:
+     sum_of_weights = self._reduce(mask, self.weights, dim=dim, skipna=False)
  valid_weights = sum_of_weights != 0.0
  return sum_of_weights.where(valid_weights)
```

| # | Solution.lean impl op (`sumOfWeights`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `da : List (Option Int)`, `weights : List Int` | `da` arg, `self.weights` | R | `DataArray` ↔ `List (Option Int)` (present/absent per position); weights `DataArray` ↔ `List Int`; bool weight ↔ `0/1`. mapping.md §2. G-CONF bridges. |
| A2 | `weightsAreLogical : Bool` | `self.weights.dtype == bool` | R | the carrier-type tag the patch branches on; a logical array's values are exactly `{0,1}`, so `.astype(int)` is value-preserving (changes carrier, hence reduction semantics). mapping.md §2. |
| A3 | `let mask := maskOf da` | `mask = da.notnull()` | I | the non-null mask; concrete element-wise `Option.isSome` map, transliterated by G-CONF. |
| A4 | `let s := if weightsAreLogical then reduceDot mask weights false else reduceDot mask weights weightsAreLogical` | the `if dtype==bool: _reduce(mask, weights.astype(int)) else: _reduce(mask, weights)` branch | A-reference + I | the unchanged reduction callee `_reduce`/`xr.dot` is modeled **deeply** (`reduceDot`, two carrier legs). The patch's branch makes the **logical** case (`weightsAreLogical = true`) take the **numeric** leg `reduceDot _ _ false` (= `arithDot`) — exactly `.astype(int)` routing bool weights through the arithmetic contraction. Non-logical weights take `reduceDot _ _ weightsAreLogical` = `arithDot` too (the flag is `false`). So `s = arithDot mask weights` on every input. The `arithDot` fold is **I** (concrete); the equality of the deep model to real `xr.dot` (both legs) is the **A-reference** G-AX validates. mapping.md §3.1. |
| A5 | `let out := if s = 0 then none else some s` | `valid_weights = sum_of_weights != 0.0; return sum_of_weights.where(valid_weights)` | I + R | the zero-total → absent masking; `where(!=0)` ↔ `if s = 0 then none`; NaN ↔ `none` (R, mapping.md §2). Concrete on the modeled scalar. |

Discriminating content of the change — a **logical-carrier** weights array must
be reduced **numerically** (counted), not **logically** (collapsed to a truth
value). It lives in step A4: the gold impl forces the `false` (arithmetic) leg
for `weightsAreLogical = true`. The pre-patch reduces through the native carrier
(`reduceDot mask weights weightsAreLogical`), so `weightsAreLogical = true`
collapses to `anyMasked` (a `1/0` truth value) instead of the count — exactly
`xr.dot([True,True],[True,True]) -> True` rather than `2` (problem statement).
`Solution_prepatch.lean` reproduces that and **fails** `out = sumOfWeightsSpec
da weights` precisely in the `.true` (logical) case (G-DIFF).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The reduction callee `_reduce`/`xr.dot`, which the
change does NOT modify (it changes only the dtype of the argument handed to it),
is modeled **deeply** (`reduceDot`, an A-reference + I), not hidden behind a
consumed axiom; there is no consumed `dot` axiom and no axiom about the function
under change. The one genuinely-changed decision — which carrier leg the logical
weights take — is spelled out concretely in the `do` block (A4), an I op.

## C. verify(Solution) ⇒ resolved

`sumOfWeights` verifies only if its output equals `sumOfWeightsSpec` = the
**arithmetic** total `arithDot (maskOf da) weights` with a zero total masked to
absent — i.e. logical-carrier weights MUST be counted, not detected (A4). By R
(`DataArray ↔ List (Option Int)`, bool ↔ `0/1`, NaN ↔ `none`) the verified impl
equals the patched `_sum_of_weights` on the tested inputs; by G-AX the deep model
`reduceDot` equals the real `xr.dot` on both legs (A-reference); by G-CONF the
R/I transliteration agrees with `patch.diff`'s behaviour on ≥10⁵ inputs through
the public API. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited callee — and the gold
patch resolves (G-RESOLVE). The single trust point is A-reference soundness
(`reduceDot == xr.dot`, G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
