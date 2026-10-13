# mapping.md — pydata__xarray-4075

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 19b088636eb7d3f65ab7a1046ac672e0689371d8`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled callee.

Repo file under change: `xarray/core/weighted.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `sumOfWeights (da) (weights) (weightsAreLogical)` | `Weighted._sum_of_weights(self, da, dim)` — `xarray/core/weighted.py:137` (changed body lines 142-150) | the modeled changed function |
| `reduceDot (mask) (weights) (logical)` *(deep model — A-reference)* | `Weighted._reduce` / `xarray.core.computation.dot` — `weighted.py:112` (body line 135 `dot(da, weights, dims=dim)`); `dot` imported `weighted.py:3` | the **unchanged** polymorphic reduction callee the function delegates to |
| `maskOf (da)` | `da.notnull()` — `weighted.py:143` | non-null mask of the data array |
| `arithDot` | the numeric/arithmetic behaviour of `dot` over a shared dim | per-position `Σ mask_i · weight_i` |
| `anyMasked` | the **logical** behaviour of `dot` on two boolean arrays | `dot` collapses bool×bool to bool (`OR_i (mask_i ∧ weight_i)`) — the carrier-dependent semantics that causes the wrong total |
| `sumOfWeightsSpec` | the desired result of `_sum_of_weights` | arithmetic total, masking a zero total to absent |

The change site: line 145 (pre-patch)

```python
sum_of_weights = self._reduce(mask, self.weights, dim=dim, skipna=False)
```

becomes (post-patch, lines 145-152) a branch that, when `self.weights.dtype ==
bool`, reduces `self.weights.astype(int)` instead of `self.weights` — routing
the logical-carrier weights through the same numeric reduction the non-logical
weights already use.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the data array `da` (1-D, reduced over its single/all dim(s)) | `List (Option Int)` | `da[i]` non-null ↔ `some v`; `da[i]` NaN/null ↔ `none`. Only the **null pattern** of `da` enters `_sum_of_weights` (`mask = da.notnull()`); the concrete non-null values are not observed, so they are modeled as arbitrary `Int`. `len(da)` ↔ `da.length`. |
| `self.weights` (1-D, aligned with `da`) | `List Int` | `weights[i]` ↔ the integer weight value; a **boolean** weight `True/False` ↔ `1/0` (`np.bool_(True).astype(int) == 1`). `len(weights)` ↔ `weights.length`. |
| `self.weights.dtype == bool` | `weightsAreLogical : Bool` | the carrier-type tag: `True` iff the weights array has boolean dtype. A logical-carrier array's values are exactly `{0,1}`, so the `.astype(int)` cast is value-preserving (it changes only the carrier, hence the reduction semantics). |
| `sum_of_weights` (scalar result), with `.where(sum != 0)` masking | `Option Int` | the reduced total; `some s` when `s ≠ 0`; `none` when the total is `0` (the `.where(valid_weights)` step replaces a zero total with NaN — `weighted.py:148-150`). On the modeled 1-D full reduction the result is a scalar. |

**Modeled slice.** The patch is dimension-agnostic (a dtype branch). The
modeled slice is the **full reduction of a 1-D `da`/`weights` pair to a scalar**
(`dim = None ⇒ dim = ...`, `weighted.py:125-126`) — exactly what the F2P tests
exercise (`DataArray([1, 2])`, `DataArray([True, True])`). Higher-rank arrays
broadcast the same per-position multiply-and-sum; the carrier-type behaviour
G-AX validates is identical across ranks.

Lean indexing is total and sound; the carrier is `List` because the reduction
is per-position over a shared dim.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `reduceDot` deep model ↔ `xarray.core.computation.dot` (A-reference)

**Callee:** `xr.dot(a, b, dims=...)` (via `Weighted._reduce`). **Unchanged** by
the patch — the patch changes only the *dtype of the argument* handed to it, not
`dot`/`_reduce` themselves. It is therefore modeled **deeply** (`reduceDot`,
spelled out in the `pure` region); there is **no consumed axiom**.

`dot` is **carrier-polymorphic**:

* on **numeric** arrays it computes the arithmetic contraction
  `Σ_i mask_i · weight_i` (modeled by `arithDot`, the `logical = false` leg);
* on **two boolean** arrays it preserves the boolean carrier and collapses the
  contraction to `OR_i (mask_i ∧ weight_i)` — `True`/`False`, i.e. `1`/`0`
  (modeled by `anyMasked`, the `logical = true` leg). This is exactly the
  problem statement's `xr.dot([True, True], [True, True]) -> True` (not `2`).

Because `mask = da.notnull()` is always boolean, the reduction is logical
precisely when `weights` is also boolean — the `weightsAreLogical` case.

**Soundness check (G-AX):** `axiom_check.py` runs the real `xr.dot` in-container
on boundary + fuzzed `(mask, weights)` pairs, asserting BOTH legs:
`reduceDot mask weights False == int(xr.dot(mask, weights_as_int))` (arithmetic)
and `reduceDot mask weights True == int(xr.dot(mask_bool, weights_bool))`
(logical). Imports only `numpy` + `xarray` (the repo's own dependency). Exit 0
iff both legs are sound on every observation.

The numeric/logical contrast is the load-bearing fact: the fix works because
routing the logical-carrier weights through `arithDot` (the `False` leg) yields
the same arithmetic total the numeric weights already produce.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`4075`**. The R/I shadow
it builds transliterates `maskOf`/`arithDot` (R/I ops; the gold impl reduces via
the `logical = false` leg of `reduceDot`, i.e. `arithDot`) to Python and the
zero-total masking, then diffs against the patched `_sum_of_weights`'s behaviour
(reached through the public `DataArray.weighted(weights).sum_of_weights()` API)
over ≥10⁵ fuzzed `(da, weights, weightsAreLogical)` triples. Exit 0 iff zero
disagreements.
