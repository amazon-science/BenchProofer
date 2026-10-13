# mapping.md — sympy__sympy-23413

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 10de1a18a0efac0b19b611e40c928250dda688bf`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each axiom / A-reference.

Repo file under change: `sympy/polys/matrices/normalforms.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `hermiteNormalForm (A) (numRows) (numCols)` | `_hermite_normal_form(A)` — `sympy/polys/matrices/normalforms.py:177` | the modeled changed function (integer-matrix Hermite normal form) |
| `Mat` *(opaque axiom)* | the working dense representation `A = A.to_dense().rep.copy()` — a `DDM` (list-of-lists) over `ZZ` (`normalforms.py:209`) | the matrix value the reduction mutates |
| `stepRow numCols mat k i` *(A-reference)* | the body of the `for i in ...` loop of `_hermite_normal_form` — `normalforms.py:218-247` (built from the UNCHANGED helpers `add_columns` @ `:40` and `_gcdex` @ `:156`) | the per-row column reduction that assigns a pivot to a rightmost column |
| `slice mat k` *(A-reference)* | `DomainMatrix.from_rep(A)[:, k:]` — `normalforms.py:248` | the final selection of the assigned pivot columns |
| `reduceRows numCols rowsLeft mat k` | the `for i in range(m-1, -1, -1): if k == 0: break; ...` loop (POST-patch, `normalforms.py:217-220` equivalent) | pure spec: the row-iteration the patch installs |
| `hnfResult numCols numRows A` | the whole POST-patch `_hermite_normal_form` | pure spec: reduce over all rows (with the `k=0` break), then slice |

The pre-patch repo elements the change removes (refinement audit only, not in the
consumer spec view): the local `rows = min(m, n)` cap (`normalforms.py:208`) and
the bounded range `for i in range(m - 1, m - 1 - rows, -1)` (`:217`). The patch
replaces them with `for i in range(m - 1, -1, -1)` + an early `if k == 0: break`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `DomainMatrix` / its dense `rep` over `ZZ` | opaque `Mat` | the value flowing through `_hermite_normal_form`; the model never inspects its entries — only that the SAME per-row reduction `stepRow` and the SAME final `slice` are applied (directive 7). Compared by `DomainMatrix.__eq__` (over ZZ) in G-CONF/G-AX. |
| `m, n = A.shape` (row / column count) | `numRows : Nat`, `numCols : Nat` | `A.shape[0] ↔ numRows`, `A.shape[1] ↔ numCols`; both are concrete non-negative integers |
| `k` (index of leftmost column with a pivot so far / count of columns still without a pivot) | `Nat` | identical; `k` starts at `n` and decreases toward `0`. `k = 0` ⟺ every column has a pivot |
| loop counter `i = m-1, m-2, ...` (row index processed) | `rowsLeft : Nat`, with processed row index `rowsLeft - 1` | the Lean loop counts DOWN the number of eligible rows; row index `i = rowsLeft - 1`. Bijection: a Python iteration at row `i` ↔ a Lean step with `rowsLeft = i + 1` |
| the per-row reduction (in-place mutation of `rep` + update of `k`) | `stepRow : Nat → Mat → Nat → Nat → Mat × Nat` | `stepRow numCols mat k i` returns `(reduced mat, updated k)`; the second component is `k-1` when a pivot is placed and `k` (i.e. `k-1` then `+1`) when row `i` is zero from the pivot column leftward |
| `DomainMatrix.from_rep(A)[:, k:]` | `slice : Mat → Nat → Mat` | keep columns `k, k+1, ...` of the reduced matrix |

The matrix carrier is left fully opaque because the operation under
specification is a control-flow change (which rows are processed, and when to
stop) — it never inspects matrix entries, only routes them through the unchanged
per-row reduction. This is the directive-7 "weakest sufficient contract is none"
modeling, mirrored on the sympy-19495 / sympy-12096 opaque-callee bundles.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `stepRow` deep reference ↔ the per-row reduction body (A-reference)
**Callee:** the body of the `for i` loop in `_hermite_normal_form`
(`normalforms.py:218-247`), composed of the UNCHANGED module helpers
`add_columns` (`:40`) and `_gcdex` (`:156`). The gold patch does NOT touch this
body — it changes only the outer row range and adds the `k == 0` break. So
`stepRow` stands for an UNCHANGED operation and its soundness is checkable on the
pre-patch source.

`axiom_check.py` (G-AX) transliterates the body as `step_row(n, A, k, i)` and
asserts that re-running the WHOLE pre-patch `_hermite_normal_form` as

    reduce over rows i = m-1, ..., m-min(m,n) of step_row, then slice

reproduces the real pre-patch `_hermite_normal_form` EXACTLY, over 13 boundary +
6000 fuzz matrices. It also checks `step_row`'s pivot-count contract
(`k-1 <= k' <= k`) and determinism. Because the per-row body is unchanged, this
witnesses that `stepRow` is a faithful A-reference — the only thing the patch
changes (the driving row range / break) is modeled CONCRETELY in
`Solution.lean`'s loop, never axiomatized.

### 3.2 `slice` deep reference ↔ `DomainMatrix.from_rep(A)[:, k:]` (A-reference)
**Callee:** `DomainMatrix.from_rep(A)[:, k:]` (`normalforms.py:248`), the final
column selection. UNCHANGED by the patch. Validated as part of the same
decomposition in `axiom_check.py` (the composition ends with `select_slice`).

There is **no consumed axiom**. The operation under change — the row-iteration
range and the early stop — is modeled DEEPLY and CONCRETELY by `reduceRows` /
the `while` loop, never hidden behind an axiom about the function under change.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`23413`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates the loop STRUCTURE (rows bottom-up, `rowsLeft>0 ∧ k>0` guard,
threading `k`) to Python and leaves the per-row reduction (`stepRow`) and the
slice (`slice`) as the REAL repo callees (`add_columns`/`_gcdex` and
`DomainMatrix[:, k:]`). It diffs against the patched `_hermite_normal_form` over
100000 inputs of varied shapes/magnitudes (including the `m > n` regime of the
bug). Exit 0 iff zero disagreements.
