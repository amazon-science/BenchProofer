# mapping.md — symbol binding & type bijection (scikit-learn__scikit-learn-14894)

## Modeled function
- **Lean** `implementation_dualCoef : Nat → Nat → List α → Except String (CSRMatrix α)`
- **Python** `sklearn.svm.base.BaseLibSVM._sparse_fit(self, X, y, sample_weight,
  solver_type, kernel, random_seed)` — the tail block that assembles the sparse
  `dual_coef_` matrix, `sklearn/svm/base.py:283-294 @ fdbaa58a` (post-patch:
  `sklearn/svm/base.py:283-297`).

We model exactly the `dual_coef_` construction tail of `_sparse_fit` — the only
code the patch touches. The earlier part of `_sparse_fit` (the `libsvm_sparse`
training call that yields `support_vectors_`, `dual_coef_data`, etc.) is upstream
of the change and produces three values that this block consumes: the number of
support vectors `n_SV = self.support_vectors_.shape[0]`, the per-class count
`n_class` (`len(self.classes_) - 1` for classification, else `1` for regression),
and the flat coefficient buffer `dual_coef_data`. These three are the inputs of
the modeled function; nothing else in the block is read.

### What the block computes
`dual_coef_` is a CSR (compressed-sparse-row) matrix built from three parallel
arrays `(data, indices, indptr)` plus a `(n_rows, n_cols)` shape:
- `dual_coef_indices = np.tile(np.arange(n_SV), n_class)` — the column index of
  every stored entry: the block `[0,1,…,n_SV-1]` repeated `n_class` times.
- `dual_coef_indptr = np.arange(0, indices.size + 1, indices.size / n_class)` —
  the row-boundary offsets `[0, n_SV, 2·n_SV, …, n_class·n_SV]` (because
  `indices.size = n_class·n_SV` and the step `indices.size / n_class = n_SV`).
- shape `(n_class, n_SV)`.

When `n_SV = 0` the step `indices.size / n_class = 0`, and `np.arange(0, 1, 0)`
performs a division by the zero step → the function aborts with an arithmetic
error instead of returning a matrix. The required behavior is that the block
still returns successfully, yielding the canonical empty sparse matrix
`sp.csr_matrix([])`, whose attributes (verified against scipy 1.x) are:
`data = []`, `indices = []`, `indptr = [0, 0]`, shape `(1, 0)`.

## Type bijection (used by G-CONF / G-AX)
| Python | Lean | notes |
|---|---|---|
| `n_SV : int (≥0)` | `nSV : Nat` | `support_vectors_.shape[0]` |
| `n_class : int (≥1)` | `nClass : Nat` | `len(classes_)-1` (clf) or `1` (regression); always ≥1 — precondition `1 ≤ nClass` |
| `dual_coef_data : float64[]` | `data : List α` | the flat coefficient buffer; stored by identity (never inspected) → modeled as a polymorphic list |
| CSR `.data` | `CSRMatrix.data : List α` | stored values |
| CSR `.indices` | `CSRMatrix.indices : List Nat` | column indices |
| CSR `.indptr` | `CSRMatrix.indptr : List Nat` | row-boundary offsets |
| CSR `.shape` | `(CSRMatrix.nrows, CSRMatrix.ncols) : Nat × Nat` | matrix shape |
| successful construction | `Except.ok m` | no arithmetic abort |
| `ZeroDivisionError` (arange zero step) | `Except.error _` | the crash the issue reports |

`dual_coef_data` is modeled as a universally-quantified element type `α` because
the block never inspects or transforms the coefficient values — it only forwards
them into the CSR buffer by identity. Polymorphic identity-storage is the
faithful, minimal model.

`np.tile(np.arange(n_SV), n_class)` ↔ `tileRange nSV nClass` (the front-recursive
flatten of `n_class` copies of `[0 … n_SV-1]`). `np.arange(0, size+1, step)` with
an integer step that divides the range ↔ `(List.range (nClass+1)).map (· * step)`.

## Callee provenance
No UNCHANGED callee is consumed as an axiom. The patch changes only the control
flow guarding the row-offset/shape construction; `np.tile`, `np.arange` and the
CSR assembly are modeled DIRECTLY (deep model) as `tileRange` / `List.range.map`
/ record fields (refinement.md rows are all I/R). Hence the axioms region is
empty and `axiom_check.py` is a skip stub. The deep models are
differential-tested against the real scipy/numpy callees by G-CONF.

## Flag dependency
`n_class` is `len(classes_)-1` only when the estimator has a `classes_`
attribute (classification); for regression (`SVR`, the F2P scenario) it is `1`.
Either way `n_class ≥ 1`, which is the only fact the construction depends on.
The branch discriminator is `n_SV` (empty vs non-empty support set), independent
of any mode flag.

## G-CONF fuzz seed
Pinned seed: **14894**. ≥10^5 fuzzed configurations over `n_SV ∈ {0, …, 60}`
(boundary `0` always included), `n_class ∈ {1, …, 6}`, random float
`dual_coef_data` of length `n_class·n_SV`. The shadow is compared against the
real post-patch construction (`sp.csr_matrix([])` for the empty case, else the
`(data, indices, indptr), (n_class, n_SV)` build) read back as
`.data / .indices / .indptr / .shape`.
