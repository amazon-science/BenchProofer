# refinement.md — scikit-learn__scikit-learn-14894

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `buildSparseCoef` `do` block, plus the deep models `arangeIndptr`,
`tileRange`, `emptyResult`, `builtResult`) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A-consumed** (proof uses an
axiom's `ensures`), **A-reference** (deep model validated == real callee by
G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The sparse-coefficient assembly — `_sparse_fit` (`sklearn/svm/base.py:287–294`)

Gold hunk:
```
- dual_coef_indptr = np.arange(0, dual_coef_indices.size + 1,
-                              dual_coef_indices.size / n_class)
- self.dual_coef_ = sp.csr_matrix(
-     (dual_coef_data, dual_coef_indices, dual_coef_indptr),
-     (n_class, n_SV))
+ if not n_SV:
+     self.dual_coef_ = sp.csr_matrix([])
+ else:
+     dual_coef_indptr = np.arange(0, dual_coef_indices.size + 1,
+                                  dual_coef_indices.size / n_class)
+     self.dual_coef_ = sp.csr_matrix(
+         (dual_coef_data, dual_coef_indices, dual_coef_indptr),
+         (n_class, n_SV))
```

| # | Solution.lean impl op (`buildSparseCoef`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `nSV nClass dataLen : Nat`, `require 1 ≤ nClass` | `n_SV`, `n_class`, `dual_coef_data.size` at `base.py:284–289` | R | non-negative Python ints ↔ `Nat`; `n_class ≥ 1` always at this site (mapping.md §2). G-CONF bridges via `arr.shape`/`.size`. |
| A2 | `let indices := tileRange nSV nClass` | `dual_coef_indices = np.tile(np.arange(n_SV), n_class)` (`base.py:289`) | A-reference + I | `tileRange` is the spelled-out deep model of the **unchanged** `np.tile(np.arange(..))`; G-AX validates `tileRange == np.tile(np.arange(..))`. Computed unconditionally on BOTH sides, exactly as the gold code keeps line 289 outside the `if`. |
| A3 | `if nSV = 0 then Except.ok emptyResult` | `if not n_SV: self.dual_coef_ = sp.csr_matrix([])` | A-reference + I | the **added guard** (the fix's control flow) — `I`; the empty container it yields is the deep model `emptyResult`, validated == `sp.csr_matrix([])` observed fields by G-AX. |
| A4 | `else match arangeIndptr nSV nClass with Except.ok indptr => …` | `else: dual_coef_indptr = np.arange(0, size+1, size/n_class)` (`base.py:290–291`) | A-reference + I | `arangeIndptr` is the deep model of the **unchanged** `np.arange` strided range; for `nSV ≥ 1` it returns the integer list `[0,nSV,…,nClass·nSV]` (G-AX). The `match` mirrors that the range succeeds on the `else` branch. |
| A5 | `Except.ok { dataLen, indices, indptr, rows := nClass, cols := nSV }` | `sp.csr_matrix((dual_coef_data, dual_coef_indices, dual_coef_indptr), (n_class, n_SV))` (`base.py:292–294`) | R + I | `csr_matrix(...)` constructed from the data/indices/indptr triple and `(n_class, n_SV)` shape ↔ the `SparseCoef` record; G-CONF compares observable fields (mapping.md §2). |
| A6 | `Except.error e` arm of the match | (unreachable on the `else`/`nSV ≥ 1` leg) | I | dead on success inputs; present so the deep model `arangeIndptr` is total. The `nSV = 0` failure shape is short-circuited by A3 before this is reached — which is precisely the bug fix. |

Discriminating content of the change — at `nSV = 0` the result must be
`Except.ok emptyResult` (an empty matrix), NOT the `Except.error zeroDivision`
the unguarded strided arithmetic produces — lives in clause A3
(`if nSV = 0 then Except.ok emptyResult`) of the model ⇔ the `if not n_SV:
sp.csr_matrix([])` branch of the gold patch. The pre-patch reached
`arangeIndptr 0 nClass = Except.error zeroDivision` unconditionally;
`Solution_prepatch.lean` reproduces that (no guard) and **fails**
`out = sparseFitSpec nSV nClass dataLen` exactly at `nSV = 0` (G-DIFF).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operation that genuinely *changed* — the
addition of the `nSV = 0` guard around the strided layout — is modeled
**directly** (the `if nSV = 0` branch, A3, an `I` control-flow op over the deep
models). The library callees `np.arange`/`np.tile`/`csr_matrix` are **unchanged**
and modeled deeply (`arangeIndptr`/`tileRange`/`emptyResult`/`builtResult`,
A-reference), validated == the real callees by G-AX. There is **no consumed
axiom** about the function under change (directive 7).

## C. verify(Solution) ⇒ resolved

`buildSparseCoef` verifies only if, at `nSV = 0`, its output equals
`Except.ok emptyResult` (A3) — i.e. it yields the empty container rather than
hitting the ill-defined stride — and, at `nSV ≥ 1`, equals the strided
`builtResult` (A4–A5). By R (`Nat` ↔ non-negative int, `SparseCoef` ↔
`csr_matrix` observable fields) the verified assembly equals the gold-patched
`_sparse_fit` tail on every `(nSV, nClass, dataLen)`; by G-AX the deep models
`arangeIndptr`/`tileRange`/`emptyResult` equal the real `np.arange`/`np.tile`/
`csr_matrix` (A-reference); by G-CONF the R/I transliteration of the branch
agrees with `patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and audited callees — and the gold patch resolves (G-RESOLVE,
F2P `test_sparse_fit_support_vectors_empty`). Trust points are exactly the two of
plan §1.1: deep-model soundness (G-AX) and refinement fidelity (this doc,
G-EQ + G-CONF).
