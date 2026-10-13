# refinement.md — pydata__xarray-4356

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `reductionMissingDecision` `do` block and the deep `prodList` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-reference** (deep model validated == real callee by G-AX), or **I**
(identical concrete op). There are no **A-consumed** axioms.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference leg and this narrative are audited by **G-EQ**. Claim:
any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The masking decision — `_maybe_null_out()` (`xarray/core/nanops.py:25`)

Gold hunk:
```
-    if hasattr(axis, "__len__"):  # if tuple or list
-        raise ValueError(
-            "min_count is not available for reduction with more than one dimensions."
-        )
-
     if axis is not None and getattr(result, "ndim", False):
-        null_mask = (mask.shape[axis] - mask.sum(axis) - min_count) < 0
+        null_mask = (np.take(mask.shape, axis).prod() - mask.sum(axis) - min_count) < 0
```

| # | Solution.lean impl op (`reductionMissingDecision`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `reducedSizes : List Nat` | `np.take(mask.shape, axis)` — the extents of the reduced axes (array branch) | R | int-array ↔ `List Nat` (mapping.md §2); G-CONF bridges by gathering `shape` at `axis`. |
| A2 | param `missingCount : Nat` | `mask.sum(axis)` (array branch) / `mask.sum()` (scalar branch) — count of missing entries per output cell | R | nonneg int count ↔ `Nat`. |
| A3 | param `requiredCount : Nat` — NO precondition | `min_count` (any int ≥ 0 whenever this code runs; `None` short-circuits in the caller `nansum`/`nanprod`) | R | int ↔ `Nat`; the spec pins the decision for EVERY count, including `min_count = 0` (real code then never nulls out — `sum ≤ prod` makes `(prod - sum - 0) < 0` unsatisfiable, and `size - sum < 0` likewise — and the spec's `prodList < missing + 0` / Nat `totalSize - missing < 0` are equally unsatisfiable on the bridge domain `missing ≤ total`). A precondition here would leave the `requiredCount = 0` slice unconstrained, admitting same-spec impls that differ from gold outside the F2P inputs (the round-4 audit's atk_3). |
| A4 | param `axisWasSequence : Bool`; `out` does NOT consult it; `out` is always `Except.ok` | the deleted guard `if hasattr(axis,"__len__"): raise ValueError(...)` | R (behaviour removal) | the fix DELETES the raise: a sequence-axis (multi-dim) reduction is now handled like any other. The frozen `ensures` pins `out = Except.ok (...)` regardless of the flag, so a verifying impl cannot reintroduce the raise. **This is the actual F2P discriminator** — `test_min_count_nd` reduces over all dims (`dim=["x","y","z"]` → tuple axis → pre-patch raises; gold removes it). `Solution_prepatch.lean` reinstates the raise (`Except.error` when `axisWasSequence`) and **fails** the `ensures` (G-DIFF). |
| A5 | param `remainingDimCount : Nat`; the impl branches on `remainingDimCount ≥ 1` | `result.ndim` (the array-branch guard `getattr(result, "ndim", False)`) | R (branch selector) | int ↔ `Nat`; `≥ 1` ↔ array branch, `= 0` ↔ scalar/all-dims branch. NO precondition — both branches modeled (the F2P calls all have `ndim = 0`). |
| A6 | array-branch `total := prodList reducedSizes`, computed by the backward `while` product fold | `np.take(mask.shape, axis).prod()` | A-reference + I | the changed counting op is modeled **deeply**: `prodList` (pure region) and the verified loop ARE the product. No consumed axiom. The fold ops (`*`, the loop) are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real `np.take(...).prod()` is the **A-reference** G-AX validates. mapping.md §3.1. |
| A7 | array-branch `Except.ok (decide (total < missingCount + requiredCount))` | `null_mask = (total - mask.sum(axis) - min_count) < 0` | R + I | over signed ints `(t - m - c) < 0 ⇔ t < m + c`; with `0 ≤ m ≤ t` the Lean `Nat` form is exact. `True` ↔ "cell replaced by fill value". |
| A8 | param `totalSize : Nat`, `fillAdmissible : Bool`; scalar-branch `Except.ok (fillAdmissible && decide (totalSize - missingCount < requiredCount))` | scalar branch `null_mask = mask.size - mask.sum(); if null_mask < min_count: result = np.nan`, gated on `getattr(result,"dtype",None) not in dtypes.NAT_TYPES` | R + I | `totalSize` ↔ `mask.size`, `fillAdmissible` ↔ the dtype guard. `mask.size - mask.sum() < min_count` ↔ `totalSize - missingCount < requiredCount`; the guard ANDs in (`float64` → `fillAdmissible = False` → never missing; `float32` → `True` → real null-out). Faithful on the F2P scalar domain (G-CONF, 0 disagreements). |

Discriminating content of the change — for a reduction over **two or more**
dimensions the collapsed count is the **product** `prod(reducedSizes)`, not a
single axis size `mask.shape[axis]` — lives in `total = prodList reducedSizes`
(model) ⇔ `np.take(mask.shape, axis).prod()` (real). The pre-patch used one
axis size (`mask.shape[axis]`) AND raised on a sequence axis;
`Solution_prepatch.lean` reproduces the raise and `Solution_prepatch_2.lean`
reproduces the single-size count — each **fails** `out = Except.ok (decide
(prodList reducedSizes < …))` (G-DIFF).

## B. Modeled domain: the WHOLE function — both branches, keyed on `remainingDimCount`

The spec models **both branches** of `_maybe_null_out`, with no domain
precondition, branching on `remainingDimCount` (= `result.ndim`):

**Array branch** (`remainingDimCount ≥ 1`): the `if axis is not None and
getattr(result, "ndim", False)` leg. Here the gold patch changed the element
count from `mask.shape[axis]` to `np.take(mask.shape, axis).prod()`, and the
per-cell decision `(np.take(mask.shape, axis).prod() - mask.sum(axis) -
min_count) < 0` is exactly `prodList reducedSizes < missingCount + requiredCount`
(A6/A7).

**Scalar / all-dims branch** (`remainingDimCount = 0`): the `elif` leg
`null_mask = mask.size - mask.sum(); if null_mask < min_count: result = np.nan`,
taken when the reduction collapses every dimension (`result.ndim == 0`). **This
is the F2P domain**: every one of the 8 `test_min_count_nd` calls dispatches here
(`ndim=0, axis=(0,1,2)`, confirmed in-container). The real branch is gated on
`getattr(result, "dtype", None) not in dtypes.NAT_TYPES`; because of numpy's
NaT-comparison quirk `np.dtype('float64') in dtypes.NAT_TYPES == True`, a
`float64` result NEVER nulls out while a `float32` result DOES (confirmed
in-container: a `(2,3)` 1-present `min_count=5` reduction returns `1.0` for
float64 but `nan` for float32). The spec captures this exactly via
`fillAdmissible && decide (totalSize - missingCount < requiredCount)` (A8), where
`fillAdmissible` is the dtype guard. This is **faithful** on the F2P domain — no
DRIFT — and is verified against the real imported function by G-CONF (0
disagreements over both branches, 100008 inputs).

**Why earlier rounds failed.** Round 0 modeled the scalar branch with the
*product* Boolean (forcing missing-detection the real `float64` code never does)
→ too-strong DRIFT. Round 1 added `require remainingDimCount ≥ 1`, EXCLUDING the
scalar branch → but F2P exercises *only* that branch, so a same-spec impl
reinstating the multi-dim raise verified yet failed F2P → too-weak DRIFT. The
fix is to model the scalar branch *faithfully* (the dtype-guarded null-out, A8)
rather than dropping it.

**The F2P discriminator** itself is the **removal of the multi-dim `raise
ValueError`** (A4): `test_min_count_nd` reduces over all dims (`dim=["x","y","z"]`
→ tuple axis), which pre-patch raised `ValueError` and post-patch returns the
value (confirmed in-container: pre-patch all 8 F2P fail with the ValueError,
post-patch all 8 pass). The spec pins `out = Except.ok` for every input
independent of `axisWasSequence`, so `Solution_prepatch.lean` (reinstating the
raise) fails to verify. G-CONF drives both branches, including the multi-dim
scalar path (never raises post-patch — confirming completion).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
the element count `mask.shape[axis] → np.take(mask.shape, axis).prod()` — is
modeled **deeply** (the spelled-out product fold `prodList`, step A5), not hidden
behind an axiom about the function under change. There is **no consumed axiom**:
the `axioms` region is empty. The removed `raise` (A4) is modeled by pinning the
post-state to `Except.ok` unconditionally.

## D. verify(Solution) ⇒ resolved

`reductionMissingDecision` verifies only if its output equals `cellMissing` —
the array-branch product decision (A6/A7) when `remainingDimCount ≥ 1` and the
dtype-guarded scalar decision (A8) when `remainingDimCount = 0` — for EVERY input
including a sequence-named multi-dimension reduction, with `out` always
`Except.ok` (A4, no raise). A verifying impl therefore (i) cannot reinstate the
removed `raise` (it must return `Except.ok` even for `axisWasSequence`), so the
multi-dim path completes → passes F2P; and (ii) computes the faithful branch
decisions. By R the verified decision equals the patched `_maybe_null_out` on
both branches; by G-AX the deep model `prodList` equals the real
`np.take(shape,axis).prod()` (A-reference); by G-CONF the R/I transliteration of
`cellMissing` agrees with the REAL imported gold-patched function on 100008
inputs spanning BOTH branches (the all-dims F2P scenario AND partial multi-axis
reductions), 0 disagreements. Since the F2P-exercised scalar domain is now
constrained and faithful, `verify ⟹ resolved` holds. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the one audited deep model — and the gold patch resolves
(G-RESOLVE; confirmed in-container: all 8 F2P pass post-gold, fail pre-gold).
Trust points are exactly the two of plan §1.1: deep-model soundness (G-AX) and
refinement fidelity (this doc, G-EQ + G-CONF).

## E. Termination semantics: total correctness

The bundle verifies under `loom.semantics.termination "total"`
(`TotalCorrectness`), not partial correctness. This matters for this instance:
the real `_maybe_null_out` always terminates (a straight-line function over
finite arrays), and the F2P discriminator is that the multi-dim path COMPLETES
and produces a value. Under partial correctness a diverging impl (e.g. an
unconditional infinite loop replacing the removed raise) would vacuously
satisfy the frozen `ensures` while its Python refinement hangs the F2P tests —
a spec-too-weak hole (the round-3 audit's atk_1/divergence witness). Total
semantics closes it: every loop must carry a `decreasing` measure (the product
fold uses `decreasing i`), so a verifying impl provably terminates and returns
the pinned `Except.ok` decision, matching the real always-terminating function.
