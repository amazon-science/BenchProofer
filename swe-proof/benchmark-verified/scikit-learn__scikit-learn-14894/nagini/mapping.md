# mapping.md — scikit-learn__scikit-learn-14894

Binds every `model.py` symbol to its repository counterpart at
`base_commit = fdbaa58acbead5a254f2e6d597dc1ab3b947f4c6`, states the type
abstraction, and gives the provenance of the one axiom (callee source + the
exact behaviour the axiom encodes).

Repo file under change: `sklearn/svm/base.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `row_pointer_for_block_layout(width, n_rows)` | the CSR row-pointer assembly inside `BaseLibSVM._sparse_fit` — `sklearn/svm/base.py:287-294` | the modeled changed function (builds the dual-coefficient CSR row-pointer; the changed hunk) |
| `range_step(start, stop, step)` *(axiom — A-consumed)* | `numpy.arange(start, stop, step)` — NumPy ufunc-style range builder, called at `sklearn/svm/base.py:290-291` (`np.arange(0, dual_coef_indices.size + 1, dual_coef_indices.size / n_class)`) | unchanged numeric callee that produces the row-pointer array; partial (undefined for a zero step) |
| `width` | `n_SV = self.support_vectors_.shape[0]` — `sklearn/svm/base.py:287`; equals the step `dual_coef_indices.size / n_class` (= `n_SV`) | number of stored entries per CSR row (per-class block width) |
| `n_rows` | `n_class` — `sklearn/svm/base.py:283-286` (`len(self.classes_) - 1`, or `1` for regression) | number of CSR rows (coefficient rows) |
| `Result()` (a `List[int]`) | `dual_coef_indptr` (the CSR row-pointer array of `self.dual_coef_`) — `sklearn/svm/base.py:290-294` | the row-pointer array delimiting each row's slice of `dual_coef_data` |

The pre-patch repo expression the change guards (for the refinement audit, not
referenced from the consumer spec view): the unconditional
`np.arange(0, dual_coef_indices.size + 1, dual_coef_indices.size / n_class)`
(`base.py:290-291`) and its enclosing `sp.csr_matrix((data, indices, indptr),
(n_class, n_SV))` (`base.py:292-294`). The post-patch adds the `if not n_SV:
self.dual_coef_ = sp.csr_matrix([])` branch.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `n_SV = self.support_vectors_.shape[0]` (a non-negative NumPy size) | `width: int`, `Requires(width >= 0)` | the integer count of support vectors / per-row entries |
| `n_class` (a positive int: `len(self.classes_)-1 >= 1`, or `1` for regression) | `n_rows: int`, `Requires(n_rows >= 1)` | the integer count of coefficient rows |
| `dual_coef_indices.size` = `n_SV * n_class` (the tiled-index length) | `size = width * n_rows` | total stored coefficients (length of the flat data) |
| `dual_coef_indptr`, a 1-D NumPy `float` array `[0., n_SV, 2*n_SV, …]` of length `n_class+1` | `List[int]` row-pointer | the entries are exact integers (`0, width, …, n_rows*width`); the model uses `int` because every boundary is an exact multiple — the F2P test observes only the *number of stored entries* (`data.size`), an integer count, never the float dtype |
| `self.dual_coef_ = sp.csr_matrix([])` (empty CSR: a `(1, 0)` matrix with `data.size == 0` and `indptr == [0, 0]` exactly — verified in the eval image) | the empty-layout return `[0, 0]` (pinned EXACTLY by the spec: `Implies(width == 0, len(Result()) == 2)` together with `Result()[0] == 0` and the final-entry clause) | both denote a layout that stores **zero** entries; the tested observable `dual_coef_.data.size == 0` ⟺ final row-pointer entry `== 0`. Moreover the real gold empty CSR's row-pointer IS `[0, 0]` (one row ⇒ `rows+1 == 2` boundaries), so pinning the model's empty return to exactly two boundaries matches the real object, not just the tested observable; a padded row-pointer (e.g. `[0, 0, 0]`) would be a malformed indptr for a 1-row CSR and diverges from gold. The model unifies the two branches under "number of stored entries == `width*n_rows`", which is 0 exactly when `width == 0`. |
| `sp.csr_matrix((data, indices, indptr), (n_class, n_SV))` (the non-empty assembly) | the non-empty return `range_step(0, size+1, width)` | the CSR is fully determined (for the tested observable) by its row-pointer `[0, width, …, n_rows*width]`; `data`/`indices` are unchanged by the patch and irrelevant to the F2P assertion |

The model abstracts away the `csr_matrix` object, `dual_coef_data`, and
`dual_coef_indices`: the patch changes **only** the guarding of the row-pointer
construction (and the empty-case object), and the F2P test (`assert not
model.dual_coef_.data.size`) observes only the number of stored entries, which
is the final row-pointer boundary.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `range_step` ↔ `numpy.arange` (A-consumed)
**Callee:** `numpy.arange(start, stop, step)` — returns evenly spaced values in
the half-open interval `[start, stop)` advancing by `step`. The patched line
calls `np.arange(0, dual_coef_indices.size + 1, dual_coef_indices.size /
n_class)`. With `dual_coef_indices.size == n_SV * n_class` and step
`dual_coef_indices.size / n_class == n_SV`, this is
`np.arange(0, n_SV*n_class + 1, n_SV)` = `[0, n_SV, 2*n_SV, …, n_class*n_SV]`
(length `n_class + 1`). Docs: https://numpy.org/doc/stable/reference/generated/numpy.arange.html

The axiom encodes only the obligations the row-pointer assembly relies on, on
the exact input family it calls `arange` with (`start == 0`, `step == width >=
1`, `stop == n_rows*width + 1` with `n_rows >= 1`):

  - `len(result) >= 2` (there is always the opening `0` and at least the
    closing boundary, since `n_rows >= 1`);
  - `result[k] == k*step` for every enumerated boundary `k` (the multiples of
    the step);
  - `(len(result) - 1)*step + 1 == stop` — the last enumerated boundary is the
    greatest multiple of `step` strictly below `stop`, i.e. `n_rows*width`
    (the total stored-entry count); phrased multiplicatively so the caller's
    discharge stays in linear integer arithmetic (no `//`).

**Partiality (the load-bearing precondition).** `numpy.arange` is **undefined
for a zero step**: `np.arange(0, stop, 0)` raises (the step must advance the
enumeration). The patched code's step is `dual_coef_indices.size / n_class`,
which is `0` when `n_SV == 0` — and the *float* division `0 / n_class`
ultimately drives `arange`'s internal `(stop-start)/step`, the literal
`ZeroDivisionError: float division by zero` of the issue. The axiom therefore
`Requires(step >= 1)`. The construction must establish a positive step before
calling the builder; the guarded branch does so (`step == width >= 1`), the
pre-patch branch cannot (it calls with `step == n_SV`, possibly `0`).

**Soundness check (G-AX).** `axiom_check.py` runs the REAL `numpy.arange` on
the Requires-satisfying family — 50 boundary `(width, n_rows)` pairs plus 20 000
randomized fuzz draws (`step ∈ [1,500]`, `count ∈ [1,500]`, `stop ==
count*step + 1`) — and asserts every observation meets the three Ensures (and
the derived final boundary `== count*step`). It additionally asserts the
EXCLUDED `step == 0` input genuinely raises on six witnesses, so the
`step >= 1` Requires is sound (not over-restrictive narration). Exit 0 iff
sound. It imports only `numpy` (the module the patch calls) and the standard
library — nothing repo-specific.

**Why this is an unchanged callee, not the changed op.** The patch does NOT
change `np.arange`; it adds an `if not n_SV:` guard around the *call site*. The
changed operation — the guarding — is modeled deeply (the `if width == 0`
branch in `row_pointer_for_block_layout`'s impl, which establishes the positive
step the unchanged callee requires). The axiom covers only the unchanged
`np.arange` it invokes.
