# mapping.md — pydata__xarray-4356

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = e05fddea852d08fc0845f954b79deb9e9f9ff883`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the one deep-model reference.

Repo file under change: `xarray/core/nanops.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reductionMissingDecision (reducedSizes …)` | `_maybe_null_out(result, axis, mask, min_count)` — `xarray/core/nanops.py:25` | the modeled changed function (the masking decision for a reduction over a collection of dimensions, BOTH branches) |
| `reducedSizes : List Nat` | `np.take(mask.shape, axis)` — the sizes of `mask` along the reduced axes (`nanops.py:35` post-patch) | input bridge (R): the gathered per-axis sizes (array branch) |
| `missingCount : Nat` | `mask.sum(axis)` (array branch) / `mask.sum()` (scalar branch) — count of missing entries among the reduced elements | input bridge (R) |
| `requiredCount : Nat` | `min_count` argument | input bridge (R) |
| `remainingDimCount : Nat` | the number of output dimensions the reduction leaves in place = `result.ndim`; `≥ 1` selects the array branch (`getattr(result, "ndim", False)` truthy), `= 0` selects the scalar/all-dims branch | branch selector (R): NO precondition — both branches modeled |
| `totalSize : Nat` | `mask.size` — total element count collapsed into the single value of an all-dims reduction (scalar branch) | input bridge (R) |
| `fillAdmissible : Bool` | `getattr(result, "dtype", None) not in dtypes.NAT_TYPES` — whether the scalar-branch null-out fires (True for e.g. `float32`; False for `float64` due to numpy's `np.dtype('float64') in NAT_TYPES == True` quirk) | input bridge (R): the dtype guard governing the scalar null-out |
| `prodList (xs : List Nat)` *(deep model — A-reference)* | `np.ndarray.prod()` applied to `np.take(mask.shape, axis)` (`nanops.py:35` post-patch) | pure spec: product of the reduced-axis sizes; deep model of the changed `.prod()` op, validated `prodList == np.take(shape,axis).prod()` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `out : Except Unit Bool` | the masking outcome: `Except.error` ↔ the pre-patch `ValueError`; `Except.ok b` ↔ a returned result where `b` says whether the aggregate is set to the fill value (missing) | return bridge (R) |

The pre-patch repo construct the change removes (refinement audit only, not in
the consumer spec view): the early guard
`if hasattr(axis, "__len__"): raise ValueError(...)` (`nanops.py:29-32`) and the
single-axis size expression `mask.shape[axis]` (`nanops.py:35` pre-patch).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `np.take(mask.shape, axis)` — a 1-D int array of the reduced-axis sizes | `List Nat` | the i-th gathered size ↔ `reducedSizes[i]`; `len` ↔ `.length`; ordering irrelevant (product is commutative) |
| `mask.sum(axis)` / `mask.sum()` — count of `True` (missing) entries reduced into one output cell | `Nat` `missingCount` | the integer count ↔ `Nat`; always `0 ≤ missingCount ≤ prod(reducedSizes)` (a count among that many elements) |
| `min_count` (nonnegative int when this runs; `None` short-circuits in the caller) | `Nat` `requiredCount` | nonnegative integer ↔ `Nat`, with NO precondition: the spec pins the decision for every count including `min_count = 0`, under which the real code never nulls out (`mask.sum() ≤ mask.size` / per-cell `sum ≤ prod` make both real comparisons unsatisfiable) exactly as the modeled Booleans are unsatisfiable on the bridge domain `missingCount ≤ totalSize` / `≤ prodList reducedSizes` |
| the per-cell decision `(total - missing - min_count) < 0` (array branch) / `(size - sum) < min_count` (scalar branch) | `Bool` (`Except.ok b`) | `True` ↔ "this output cell is replaced by the fill value (reported missing)" |
| `raise ValueError("min_count is not available …")` (pre-patch, multi-dim) | `Except.error ()` | the rejection of a multi-dimension reduction |

`total - missing - min_count < 0` over signed ints ⇔ `total - missing <
min_count`. With `0 ≤ missing ≤ total` the Lean truncated subtraction
`prodList reducedSizes - missingCount` is exact, so `decide (prodList
reducedSizes - missingCount < requiredCount)` is the faithful Boolean.

The modeled domain is the **WHOLE post-gold function** — both branches, keyed by
`remainingDimCount` (= `result.ndim`), with NO domain precondition:

- **array branch** (`remainingDimCount ≥ 1`): the patched per-cell formula
  `(np.take(mask.shape, axis).prod() - mask.sum(axis) - min_count) < 0` is exactly
  the modeled Boolean `prodList reducedSizes < missingCount + requiredCount`.
- **scalar / all-dims branch** (`remainingDimCount = 0`, the F2P scenario): the
  real post-gold body is `null_mask = mask.size - mask.sum(); if null_mask <
  min_count: result = np.nan`, GATED on `getattr(result, "dtype", None) not in
  dtypes.NAT_TYPES`. Because of numpy's NaT-comparison quirk
  `np.dtype('float64') in dtypes.NAT_TYPES == True`, a `float64` result NEVER
  nulls out while a `float32` result DOES. The spec models this exactly:
  `fillAdmissible && decide (totalSize - missingCount < requiredCount)`, where
  `fillAdmissible` is the dtype guard. (Earlier rounds either modeled this branch
  with the product Boolean — too-strong DRIFT — or excluded it with
  `remainingDimCount ≥ 1` — too-weak, since F2P only exercises this branch. The
  dtype-guarded scalar formula is faithful on the F2P domain; see refinement.md
  §B and conformance_check.py, 0 disagreements against the real imported
  function over both branches.)

The deleted multi-dim `raise ValueError` (the actual F2P discriminator) is
modeled by `out` being `Except.ok` for EVERY input, independent of
`axisWasSequence`.

## 3. Callee provenance (deep model — checked by G-AX / axiom_check.py)

### 3.1 `prodList` deep model ↔ `np.take(mask.shape, axis).prod()` (A-reference)
**Callee:** `numpy.ndarray.prod()` applied to the gathered sizes
`np.take(mask.shape, axis)`. The changed counting operation is modeled
**deeply** by `prodList` (with the backward product loop) in the `pure`/`impl`
regions; there is **no consumed axiom**. `prodList [] = 1`,
`prodList (x :: xs) = x * prodList xs` — the empty product is `1` and each size
multiplies in, exactly `np.prod` over the 1-D array of reduced-axis sizes
(`np.prod([]) == 1.0` likewise). The pre-patch used only a single reduced-axis
size (`mask.shape[axis]`), which equals the product **only** when exactly one
axis is reduced; for two or more reduced axes the product is the faithful count
of elements reduced into each output cell — the behavioural change the fix
introduces.

**Soundness check (G-AX):** `axiom_check.py` imports `numpy`, draws boundary
shapes (empty, singleton, large dims, dims of size 0/1) plus 20 000 randomized
1-D size lists, and asserts `prodList(sizes) == int(np.take(shape, axis).prod())`
where `shape`/`axis` are constructed so `np.take(shape, axis) == sizes`. It also
asserts the empty-product convention and the `np.int` overflow-free range used
by the tests. Imports only `numpy`. Exit 0 iff sound.

## 4. No consumed axioms

`missingCount` (= `mask.sum(axis)`) and `reducedSizes` (= `np.take(mask.shape,
axis)`) are **inputs**, bridged by R-refinements above, not axiomatized. The
only modeled callee is the changed `.prod()`, which is deep-modeled (A-reference,
§3.1). The `axioms` region of `Solution.lean` is therefore empty.

## 5. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`4356`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`prodList`/the decision (R/I-tagged ops) to Python over `numpy` masks and diffs
against the patched arithmetic of `_maybe_null_out` (the gold-patch line) on both
the all-dimensions scalar configuration and partial multi-axis configurations.
