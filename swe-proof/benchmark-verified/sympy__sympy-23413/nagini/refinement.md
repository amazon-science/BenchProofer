# refinement.md — sympy__sympy-23413

The operation-by-operation correspondence between `model.py`'s implementation
(the `leftmost_pivot_column` impl region and the deep `pivot_count` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses a `@ContractOnly` axiom's `Ensures`),
**A-reference** (a deep model is validated == the real routine by
`axiom_check.py` / G-AX, NOT consumed as an axiom), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed site — `_hermite_normal_form` (`sympy/polys/matrices/normalforms.py:177`)

Gold hunk:
```
-    # way up. The total number of rows we will consider is min(m, n), where
-    # A is an m x n matrix.
     m, n = A.shape
-    rows = min(m, n)
     A = A.to_dense().rep.copy()
     ...
     k = n
-    for i in range(m - 1, m - 1 - rows, -1):
+    for i in range(m - 1, -1, -1):
+        if k == 0:
+            # This case can arise when n < m and we've already found n pivots.
+            # ... break
+            break
         k -= 1
         ...
```

The observable consequence is the final value of the column marker `k`, since
the routine returns `DomainMatrix.from_rep(A)[:, k:]` — the columns from `k` to
the right edge. The model's `leftmost_pivot_column` computes exactly that `k`.

| # | model.py impl op (`leftmost_pivot_column`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `found: List[int]`, `n: int` | the `DomainMatrix A` and `n = A.shape[1]` | R | the matrix is abstracted to its per-row pivot OUTCOMES + column count (mapping.md §2). `found[t] ∈ {0,1}` is whether the t-th-from-bottom row yields a nonzero pivot; `n` is the column count. The matrix arithmetic (`add_columns`, `_gcdex`) is the unchanged substrate that produces these outcomes; the patch does not touch it. |
| A2 | `k = n` | `k = n` (`normalforms.py:216`) | I | identical integer initialisation: the marker starts at the column count. |
| A3 | `while i < len(found): ...` over **all** rows | `for i in range(m - 1, -1, -1):` (post-patch, was `range(m-1, m-1-rows, -1)` with `rows = min(m, n)`) | R | both iterate every row; bottom-to-top index `i` (repo) ↔ position `i` into the bottom-to-top `found` list (model). The PRE-patch bound `min(m, n)` is the bug; the prepatch skeleton reproduces it (`while i < min(len(found), n)`) and fails the spec. |
| A4 | `if k == 0: break` | `if k == 0: break` (new hunk) | I | identical early-exit guard: once every column holds a pivot, stop. |
| A5 | `if found[i] == 1: k = k - 1` (net decrement on a pivot) | `k -= 1` (unconditional) then `if b == 0: k += 1` else reduce (`normalforms.py:218,237-245`) | R | the repo decrements `k` then restores it for a zero (no-pivot) row; the net effect over a row is "decrement iff a nonzero pivot was produced", which the model expresses directly as the `found[i] == 1` branch. `b == 0 ⇔ found[i] == 0` (mapping.md §2). |
| A6 | `return k` | `return DomainMatrix.from_rep(A)[:, k:]` | R | the model returns the marker; the retained-column count `n - k` ↔ the column count of the returned submatrix. The F2P tests compare this submatrix; its shape/content is determined by `k` (the columns kept), which the model pins exactly. |

The discriminating content of the change — examining **all** rows (so a pivot in
a top row of a tall matrix is counted) versus only the bottom `min(m, n)` rows —
lives in the loop bound A3 + the closed-form postcondition
`Result() == max(0, n - pivot_count(found, len(found)))` (counts pivots over
**all** `len(found)` rows). `model_prepatch.py` reverts to the
`min(len(found), n)` bound and **fails** the postcondition
`Result() == n - pivot_count(found, len(found))` on any input with a pivot in a
top row (e.g. `found = [1, 0, 1]`, `n = 2`: prepatch returns `1`, spec demands
`0`). That is exactly the spec sensing the change (G-DIFF), and it mirrors the
real failure: `Matrix([[1, 12], [0, 8], [0, 5]])` losing its top pivot column.

## B. No consumed axiom; the deep model is the A-reference

There is **no `@ContractOnly` axiom** in this bundle. The matrix-arithmetic
callees (`add_columns`, `_gcdex`, `DomainMatrix.*`) are **unchanged** by the
patch and affect the modelled behaviour only through the per-row pivot outcome
`found[i]`, which is taken as the model's abstract input rather than axiomatized.
The changed marker logic itself is modelled **deeply** (`pivot_count` + the
verified loop). Per SPEC_GUIDE §3, the corresponding real routine is therefore
an **A-reference**, validated `== _hermite_normal_form`'s marker by
`axiom_check.py` (G-AX), not a consumed axiom.

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `pivot_count(found, len(found))` + the verified loop computing `k` | the post-patch row loop maintaining `k` and `return ...[:, k:]` | A-reference | the deep model of the changed marker logic; G-AX runs the real `_hermite_normal_form` (and a faithful re-implementation) and asserts `n - leftmost_pivot_column(found, n)` equals the real retained-column count over boundary + 60k fuzz. NOT consumed as an axiom. |

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the loop range + the `k == 0` break that govern which rows are
examined — is modelled **deeply** (the loop in `leftmost_pivot_column`, the
`pivot_count` fold, step A3/A4), not hidden behind an axiom about the function
under change. The unchanged matrix arithmetic is abstracted to the per-row
`found` outcome (R), an abstraction validated against the real routine by G-AX.

## D. verify(model) ⇒ resolved

`leftmost_pivot_column` verifies only if its returned marker equals
`max(0, n − P)` where `P` counts pivots over **every** row (the postcondition),
and only if the loop honours the `k == 0` early exit. By R (matrix ↔ per-row
pivot outcomes + column count; marker `k` identical; retained columns = `n − k`)
the verified marker equals the post-patch `_hermite_normal_form`'s marker on the
tested inputs, and by G-AX (A-reference) the deep model equals the real routine's
retained-column count over boundary + fuzz. The PRE-patch routine counted pivots
over only the bottom `min(m, n)` rows; the spec rejects that (G-DIFF). Therefore
a model satisfying this spec, refined by the map above, is the gold patch up to
type refinement, and the gold patch resolves (G-RESOLVE). The single trust point
is refinement fidelity + the A-reference soundness (this document, G-EQ; G-AX);
there is no consumed-axiom trust point.
