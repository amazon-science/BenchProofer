# refinement.md — pydata__xarray-4075

Operation correspondence between `implementation_sumOfWeights` (Solution.lean)
and the gold `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

## Modeled function: `_sum_of_weights` (boolean-weights case)

The post-patch body computes the not-null mask, reduces it against the weights —
casting boolean weights to integer first — and reports a zero aggregate as
missing:

```python
mask = da.notnull()
if self.weights.dtype == bool:
    sum_of_weights = self._reduce(mask, self.weights.astype(int), dim=dim, skipna=False)
else:
    sum_of_weights = self._reduce(mask, self.weights, dim=dim, skipna=False)
valid_weights = sum_of_weights != 0.0
return sum_of_weights.where(valid_weights)
```

The modeled domain is the boolean-weights branch the issue/F2P tests exercise.

| # | `implementation_sumOfWeights` op | `patch.diff` counterpart | tag | justification |
|---|---|---|---|---|
| 1 | inputs `mask weights : List Bool` | `mask = da.notnull()` (bool) and the boolean `self.weights` | R | bool array (1-D) ↔ `List Bool` (mapping.md). The not-null mask and boolean weights are the modeled domain's entry points. |
| 2 | `for (m,w) in mask.zip weights do if m && w then acc := acc + 1` | `self._reduce(mask, self.weights.astype(int), …)` — the contraction of the mask with the **integer-cast** weights | R / A-reference | The post-patch reduction is the array contraction `dot(mask, weights.astype(int))`. It is modeled DEEPLY as the integer multiply-and-accumulate `zipDot` (each aligned set/set pair adds 1), realised in the impl as the accumulator `for` loop. The cast-to-int is exactly what makes the contraction integer-valued rather than the boolean OR. G-AX confirms the deep model == the real `xr.dot` over the integer-cast inputs; G-CONF confirms the loop's R/I behavior == `patch.diff`. |
| 3 | per-position contribution `if m && w then 1 else 0` | one term of `dot`: `mask_i * weights_int_i` (`int(bool) ∈ {0,1}`) | A-reference | the elementwise product the contraction sums; pinned in `zipDot`, validated against the real callee by G-AX. |
| 4 | `if acc = 0 then return none` else `return some acc` | `sum_of_weights.where(sum_of_weights != 0.0)` — zero aggregate ↦ NaN | I | identical concrete masking of the zero total; `none` models the NaN sentinel, `some acc` the retained scalar. |

No op in `implementation_sumOfWeights` is changed-inexpressible: the
bool→int-cast reduction is modeled deeply. There is **no consumed axiom** and **no
opaque callee** (the `axioms` region is empty); the proof discharges by induction
on the paired list (front-recursive fold `zipDot` vs. accumulator loop,
PROOF_PLAYBOOK Route B).

## Why the prepatch is the real bug

`Solution_prepatch.lean` reduces with the **boolean** contraction the original
code used for boolean inputs — a disjunction over the per-position conjunctions —
so the aggregate saturates at one unit (`True`) whenever any kept position is set,
instead of counting them. On the F2P discriminator `mask=[T,T]`, `weights=[T,T]`
it returns `some 1` while the spec demands `some 2` (= `sowSpec`), so
`correct_sumOfWeights` is unclosable on that clause. This is exactly GH4074:
`xr.dot([True,True],[True,True]) -> True` (= 1), not `2`.

## Out-of-scope: the `_weighted_mean` test

The gold `test_patch` also adds `test_weighted_mean_bool`. The weighted mean is
`weighted_sum / sum_of_weights`; the bug and the fix both live entirely in
`_sum_of_weights` (the denominator). Once `_sum_of_weights` returns the correct
integer aggregate, the mean is correct with no further change. It is therefore not
an independently-fixed behavior and needs no second triple / prepatch — it is the
same fix observed through the division.
