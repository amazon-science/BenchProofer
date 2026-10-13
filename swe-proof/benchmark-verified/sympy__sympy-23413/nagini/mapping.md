# mapping.md — sympy__sympy-23413

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 10de1a18a0efac0b19b611e40c928250dda688bf`, states the type
abstraction, and gives the provenance of the deep model (validated against the
real routine by G-AX / `axiom_check.py`).

Repo file under change: `sympy/polys/matrices/normalforms.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `leftmost_pivot_column(found, n)` | the column-marker loop inside `_hermite_normal_form(A)` — `sympy/polys/matrices/normalforms.py:177` (changed body lines 207-217 and the new break) | the modelled changed behaviour: tracking the marker `k` that determines which columns of the reduced matrix are retained (`return DomainMatrix.from_rep(A)[:, k:]`, line 248) |
| `pivot_count(s, upto)` *(deep model — A-reference)* | the cumulative count of rows that produce a nonzero pivot, as realised by the body of `_hermite_normal_form`'s row loop (the `b == 0 ⇒ k += 1` / else branch, lines 237-245) | pure spec: number of pivots contributed by the first `upto` rows (bottom-to-top) |
| `valid_flags(s)` | (no repo symbol) the well-formedness of the per-row pivot-outcome abstraction | pure spec: each per-row flag is 0/1 |
| `pivot_count_monotone(s, a, b)` | (no repo symbol) | proof lemma: `pivot_count` is non-decreasing in its bound |

The pre-patch repo constructs the change removes / replaces (for the refinement
audit; not referenced from the consumer spec view):
- `rows = min(m, n)` (`normalforms.py:211`, removed);
- the loop range `for i in range(m - 1, m - 1 - rows, -1)` (`normalforms.py:217`)
  — replaced by `for i in range(m - 1, -1, -1)` plus an `if k == 0: break` guard.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `A : DomainMatrix` over `ZZ`, shape `(m, n)` | abstracted to `found: List[int]` (length `m`) + `n: int` | the matrix arithmetic (extended-gcd column combinations, `add_columns`, `_gcdex`) is the unchanged machinery that *decides*, per row, whether a nonzero pivot is producible in the remaining columns; only that boolean per-row OUTCOME is observable by the marker `k`. `found[t]` (t = 0 is the bottom row) is 1 iff the t-th-from-bottom row yields a nonzero pivot; `n` is `A.shape[1]`. |
| the column marker `k` (`normalforms.py:216`) | the model's `k` / `Result()` | identical integer; `k` starts at `n`, decremented when a row yields a pivot, restored when a row is all-zero (the model decrements iff `found[i] == 1`, the net effect). |
| retained submatrix `DomainMatrix.from_rep(A)[:, k:]` (`normalforms.py:248`) | retained-column count `n - Result()` | the result keeps columns `k .. n-1`; its column count is `n - k`. The F2P tests compare this matrix shape/content. |
| the row-loop bound | the model loop bound | post-patch `range(m-1, -1, -1)` ↔ iterate all `len(found)` rows; the new `if k == 0: break` ↔ the model's `if k == 0: break`. |

The matrix entries and column operations are **not** modelled element-wise:
they are the unchanged substrate whose only effect on the changed behaviour is
the per-row pivot outcome (the `found` flags). This is a faithful abstraction
because the patch changes neither `add_columns`, `_gcdex`, nor the per-row pivot
arithmetic — it changes only *which rows are examined* and *when to stop*
(the loop range and the `k == 0` break). For the bottom `min(m, n)` rows the two
versions perform identical arithmetic in identical order, so the `found` flags
are the same function of the input under both versions; the fix merely extends
the search to the remaining top rows. (Verified empirically against the real
routine in `axiom_check.py`.)

## 3. Deep-model provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `leftmost_pivot_column` / `pivot_count` deep model ↔ `_hermite_normal_form`'s marker
**Routine:** `sympy.polys.matrices.normalforms._hermite_normal_form` (Cohen,
*A Course in Computational Algebraic Number Theory*, Algorithm 2.4.5). The
changed marker logic is modelled **deeply**; there is **no `@ContractOnly`
axiom** the proof consumes (the matrix arithmetic is abstracted away as the
per-row pivot outcome, not axiomatized as an opaque callee).

Post-patch source (the fixed loop, `normalforms.py:207-217+`):

```python
    m, n = A.shape
    A = A.to_dense().rep.copy()
    k = n
    for i in range(m - 1, -1, -1):
        if k == 0:
            break
        k -= 1
        ...
        b = A[i][k]
        ...
        if b == 0:
            k += 1
        else:
            ...   # reduce entries right of the pivot
    return DomainMatrix.from_rep(A)[:, k:]
```

The closed form of the final marker is `k = max(0, n - P)` where `P` is the
number of rows (over **all** `m` rows) that yield a nonzero pivot — equivalently
the model's loop that decrements `k` once per pivot and stops at `k == 0`.
The PRE-patch routine used `rows = min(m, n)` and `for i in range(m-1, m-1-rows, -1)`,
so it counted pivots over only the **bottom** `min(m, n)` rows, missing pivots
in the top `m - n` rows of a tall matrix — exactly the reported failure
(`Matrix([[1, 12], [0, 8], [0, 5]])` dropping the top pivot row's column).

**Soundness check (G-AX):** `axiom_check.py`
  (1) runs a faithful stdlib-only re-implementation of the fixed routine on the
      issue matrices, the F2P matrices, tall/wide/zero/rank-deficient shapes,
      and 60 000 random integer matrices, recording the actual per-row pivot
      outcomes and the actual final `k`, asserting the model law
      `leftmost_pivot_column(found, n) == k == max(0, n - sum(found))`; and
  (2) imports the REAL `sympy.polys.matrices.normalforms._hermite_normal_form`
      (available in the eval container) and asserts the model's retained-column
      count `n - k` equals the real result's column count on every matrix.
Both confirmed here against the patched worktree (0 mismatches over 14 boundary
+ 3000 fuzz; the bundled fuzz is 60 000). Exit 0 iff sound. Imports are
stdlib-only by default; the cross-check uses only the sympy module the patch
edits.
