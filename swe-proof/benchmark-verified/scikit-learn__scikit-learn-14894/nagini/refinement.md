# refinement.md — scikit-learn__scikit-learn-14894

The operation-by-operation correspondence between `model.py`'s implementation
(the `row_pointer_for_block_layout` impl region and the consumed `range_step`
axiom) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** where the proof uses the
axiom's `Ensures`; **A-reference** where a deep model is validated == the real
callee by axiom_check.py / G-AX), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested input, so
it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed hunk — `BaseLibSVM._sparse_fit` (`sklearn/svm/base.py:287-294`)

Gold hunk:
```
  n_SV = self.support_vectors_.shape[0]
  dual_coef_indices = np.tile(np.arange(n_SV), n_class)
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

| # | model.py impl op (`row_pointer_for_block_layout`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `width: int` (`>= 0`) | `n_SV = self.support_vectors_.shape[0]` | R | `n_SV` is the non-negative support-vector count; modeled as `width >= 0` (mapping.md §2). It is also the `arange` step `dual_coef_indices.size / n_class == n_SV`. |
| A2 | parameter `n_rows: int` (`>= 1`) | `n_class` (`len(self.classes_)-1`, or `1` for regression) | R | `n_class` is a positive int; modeled as `n_rows >= 1` (mapping.md §2). |
| A3 | `size = width * n_rows` | `dual_coef_indices.size` (`== n_SV * n_class`) | R + I | `dual_coef_indices = np.tile(np.arange(n_SV), n_class)` has length `n_SV*n_class`; identical integer product over the refined carriers. |
| A4 | `if width == 0: return [0, 0]` | `if not n_SV: self.dual_coef_ = sp.csr_matrix([])` | R | the guard `not n_SV` ⟺ `n_SV == 0` ⟺ `width == 0`. The empty CSR `sp.csr_matrix([])` is a `(1, 0)` matrix with `data.size == 0` and `indptr == [0, 0]` exactly (verified in the eval image); the model returns the row-pointer `[0, 0]`, and the spec pins the empty case EXACTLY (`Implies(width == 0, len(Result()) == 2)` + `[0] == 0` + final entry `== 0`), so the verified empty return equals the real object's row-pointer, not merely the F2P observable `not dual_coef_.data.size` (mapping.md §2). This guarded branch is the **changed operation, modeled deeply** (spelled out as the `if`), not hidden behind an axiom. |
| A5 | `else: step = width; range_step(0, size+1, width)` | `else: dual_coef_indptr = np.arange(0, dual_coef_indices.size + 1, dual_coef_indices.size / n_class)` | A-consumed | the row-pointer builder is the unchanged `np.arange`; with step `dual_coef_indices.size / n_class == n_SV == width`, `np.arange(0, size+1, width)` = `[0, width, …, n_rows*width]`. The proof **consumes** `range_step`'s `Ensures` (the boundary values and the final-entry identity). G-AX validates the axiom against the real `np.arange` (mapping.md §3.1). The positive step the callee requires is established here by A4's guard. |
| A6 | `return indptr` (the row-pointer `List[int]`) | `self.dual_coef_ = sp.csr_matrix((dual_coef_data, dual_coef_indices, dual_coef_indptr), (n_class, n_SV))` | R | the CSR is determined, for the tested observable (`data.size`), by its row-pointer's final entry = number of stored entries = `n_SV*n_class`; `dual_coef_data`/`dual_coef_indices` are unchanged by the patch and irrelevant to the F2P assertion (mapping.md §2). |

The discriminating content of the change — **the guard that avoids the zero
step** — lives in A4 (`if width == 0`). The pre-patch builds the row-pointer
unconditionally (`step = width` with no guard), so when `width == 0` it invokes
`range_step` with `step == 0`, violating that callee's `Requires(step >= 1)` —
exactly the `ZeroDivisionError` the issue reports. `model_prepatch.py` drops the
guard and **fails** on the `range_step` precondition, which is the spec sensing
the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The one operation that genuinely
*changed* — adding the `if not n_SV:` guard so the row-pointer construction is
never reached with a zero step — is modeled **deeply** (the `if width == 0`
branch spelled out in the impl, A4), NOT behind an axiom about the function
under change. The only consumed axiom, `range_step` (**A-consumed**, A5), covers
the **unchanged** numeric callee `np.arange` that the construction invokes; its
genuine partiality (undefined for a zero step) is the very property the guard
respects, and is what makes the pre-patch fail to verify. There is no
A-reference deep-model-vs-callee equality in this bundle (the changed op is
control flow, fully expressible).

## C. verify(model) ⇒ resolved

`row_pointer_for_block_layout` verifies only if (i) it returns a row-pointer
whose final entry is `width*n_rows` for every `width >= 0` — in particular the
exact two-boundary `[0, 0]` when `width == 0` (the empty-length pin
`Implies(width == 0, len(Result()) == 2)` plus the opening/final clauses leave
no slack in the empty branch) — and (ii) it
establishes the positive step the unchanged `np.arange` callee requires before
invoking it (A5's precondition). A wrong impl that omits the `width == 0` guard
cannot discharge that precondition (G-DIFF / G-MUT: 20/20 mutants killed,
including the empty-branch return value). By R (the `n_SV`/`n_class`/`size`
integer refinements, the `sp.csr_matrix([])` ⟺ stored-count-0 abstraction, and
the CSR-determined-by-its-row-pointer abstraction) the verified construction
equals the gold patch's `_sparse_fit` hunk on the tested input; by G-AX the
`range_step` axiom is a sound over-approximation of the real `np.arange`
(A-consumed). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and one audited callee — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
