# refinement.md — operation correspondence (scikit-learn__scikit-learn-14894)

Maps every operation in `implementation_dualCoef` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof consumes an
axiom), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op).

The gold patch wraps the `dual_coef_` construction tail of `_sparse_fit` in an
`if not n_SV: … else: …` guard. Pre-patch the row-offset vector
`np.arange(0, dual_coef_indices.size + 1, dual_coef_indices.size / n_class)` is
built unconditionally; when `n_SV = 0` the step `dual_coef_indices.size / n_class`
is `0`, and `np.arange` with a zero step raises `ZeroDivisionError`. The fix
short-circuits the empty case to the canonical empty matrix `sp.csr_matrix([])`
and only builds the offsets / block matrix when `n_SV > 0`.

The Lean inputs are `width = n_SV`, `rows = n_class`, `data = dual_coef_data`.
The crash is modeled as a non-result (`Except.error`); a successful build is
`Except.ok m`.

| # | impl op (Solution.lean) | patch.diff / repo counterpart | tag |
|---|---|---|---|
| 1 | `let indices := tileRange width rows` | `dual_coef_indices = np.tile(np.arange(n_SV), n_class)` (unchanged by patch; ramp `[0..n_SV-1]` tiled `n_class` times) | R (`np.int` array ↔ `List Nat`); deep model of `tile∘arange` |
| 2 | `if width = 0 then return Except.ok (emptyCSR α)` | `if not n_SV: self.dual_coef_ = sp.csr_matrix([])` (the fix's new branch) | R (`sp.csr_matrix([])` ↔ `emptyCSR`: data `[]`, indices `[]`, indptr `[0,0]`, shape `(1,0)` — verified against scipy) |
| 3 | `let indptr := rowOffsets rows width` | `dual_coef_indptr = np.arange(0, dual_coef_indices.size + 1, dual_coef_indices.size / n_class)` (the `else` branch; for `n_SV>0` this is `[0, n_SV, …, n_class·n_SV]`) | R (`np.arange` even spacing ↔ `(range (rows+1)).map (·*width)`); deep model |
| 4 | `return Except.ok { data := data, indices := indices, indptr := indptr, nrows := rows, ncols := width }` | `self.dual_coef_ = sp.csr_matrix((dual_coef_data, dual_coef_indices, dual_coef_indptr), (n_class, n_SV))` | R (CSR triple+shape ↔ `CSRMatrix` record fields) |
| 5 | (the `Id.run do` always returns `Except.ok`) | the function returns normally in BOTH branches — never `ZeroDivisionError` | I (no abort ⇒ the issue's `ZeroDivisionError` is gone) |

No op is A-consumed and none is A-reference: the patch introduces no call to an
unchanged callee whose *internal* behavior the proof must assume. `np.tile`,
`np.arange`, and the CSR constructor are modeled DEEPLY (spelled out as
`tileRange`, `rowOffsets`, and the record), so per SPEC_GUIDE §3 they are NOT
axiomatized — their deep models are differential-tested against the real
numpy/scipy callees by G-CONF. Hence the axioms region is empty and
`axiom_check.py` is a skip stub.

The R legs (the `tileRange`/`rowOffsets`/empty-matrix shadows and the success
discriminant) are mechanically differential-tested by G-CONF over ≥10^5 fuzzed
`(n_SV, n_class)` configurations including the `n_SV = 0` boundary. No changed op
is inexpressible.
