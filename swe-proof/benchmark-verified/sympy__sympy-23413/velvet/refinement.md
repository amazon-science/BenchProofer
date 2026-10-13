# refinement.md — sympy__sympy-23413

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `hermiteNormalForm` `do` block, the `reduceRows`/`hnfResult` deep model, and
the `stepRow`/`slice` A-references) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed**
where the proof uses the axiom's `ensures`, **A-reference** where a deep model is
validated == the real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The HNF reduction — `_hermite_normal_form(A)` (`normalforms.py:177`)

Gold hunk (the only change):
```
-    # ... The total number of rows we will consider is min(m, n) ...
     m, n = A.shape
-    rows = min(m, n)
     A = A.to_dense().rep.copy()
     k = n
-    for i in range(m - 1, m - 1 - rows, -1):
+    for i in range(m - 1, -1, -1):
+        if k == 0:
+            break
         k -= 1
         ... (per-row reduction body, UNCHANGED) ...
     return DomainMatrix.from_rep(A)[:, k:]
```

| # | Solution.lean impl op (`hermiteNormalForm`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `A : Mat`, `numRows numCols : Nat` | `A` (DomainMatrix), `m, n = A.shape` | R | `DomainMatrix`/dense `rep ↔ Mat`; `A.shape ↔ (numRows, numCols)` (mapping.md §2). Read-only — none is `mut` (directive 5). |
| A2 | `let mut mat := A` / `let mut k := numCols` / `let mut rowsLeft := numRows` | `A = A.to_dense().rep.copy()` / `k = n` / loop counter `i` | R + I | initialise the working matrix, the unassigned-pivot count `k = n`, and the row cursor. `rowsLeft = numRows` ⇒ row index `rowsLeft-1` walks `m-1 .. 0` (mapping.md §2). |
| A3 | `while rowsLeft > 0 ∧ k > 0` … `done_with rowsLeft = 0 ∨ k = 0` | `for i in range(m-1, -1, -1): if k == 0: break` | **I** (the changed control flow) | THE CHANGED OP, modeled CONCRETELY: process every row top-of-remaining-down (`rowsLeft` from `numRows`), stopping as soon as `k = 0` (every column has a pivot). This is the gold patch's full `range(m-1,-1,-1)` + `if k==0: break`. The PRE-patch capped at `min(m,n)` rows with no break (Solution_prepatch). |
| A4 | `let p := stepRow numCols mat k (rowsLeft-1)` ; `mat := p.1` ; `k := p.2` | the per-row reduction body (`k -= 1; ... add_columns/_gcdex ...`), UNCHANGED | **A-reference** | the unchanged per-row reduction; `stepRow` is validated == the real body by G-AX (mapping.md §3.1). The op itself is concrete in the loop; the equality to the real callee is the A-reference. |
| A5 | `rowsLeft := rowsLeft - 1` | implicit in the `for i` decrement | I | advance the row cursor up by one. |
| A6 | `return slice mat k` | `return DomainMatrix.from_rep(A)[:, k:]` | **A-reference** | the unchanged final column selection; validated == the real slice by G-AX (mapping.md §3.2). |

The discriminating content of the change — **all `numRows` rows are eligible,
not just `min(numRows,numCols)`** — lives in the loop guard `rowsLeft > 0 ∧ k > 0`
(model) ⇔ `for i in range(m-1,-1,-1) ... if k==0: break` (real). The pre-patch
capped the rows at `min(m,n)`; `Solution_prepatch.lean` reproduces that cap
(`toProcess := min numRows numCols`, no `k=0` break) and **fails**
`out = hnfResult numCols numRows A` (G-DIFF), because for `numRows > numCols` it
skips the top rows the frozen spec reduces over.

**Termination semantics.** The bundle uses TOTAL correctness
(`loom.semantics.termination "total"`, `open TotalCorrectness`): the real
patched loop is bounded — `for i in range(m-1, -1, -1)` makes at most one pass
per row and the `if k == 0: break` only stops it sooner — so it always
terminates and returns, and the F2P tests observe its returned matrix. A
diverging implementation (e.g. an infinite `while` that never reaches the
postcondition) must therefore NOT satisfy the spec. Under partial correctness
such an implementation would discharge `out = hnfResult numCols numRows A`
vacuously — a spec-too-weak hole (a same-spec non-terminating impl verifies
while its refined patch cannot resolve). The verified loop carries
`decreasing rowsLeft` to discharge the totality obligation
(`Solution_prepatch.lean`'s capped loop carries `decreasing toProcess` and
still fails the postcondition, as required by G-DIFF).

## B. The deep model `reduceRows` / `hnfResult`

`reduceRows` (pure region) is the front-recursive transcription of the patched
row loop: at each step, if `k = 0` stop; else apply `stepRow` to the
top-eligible row and recurse on one fewer row. `hnfResult` composes
`reduceRows` over all `numRows` rows with the final `slice`. The `ensures
out = hnfResult numCols numRows A` therefore pins the EXACT post-patch behaviour:
the loop invariant `reduceRows numCols numRows A numCols = reduceRows numCols
rowsLeft mat k` carries the fold forward, and `reduceRows_exit` discharges the
post-state at loop exit (`rowsLeft = 0 ∨ k = 0`). No op here is A-consumed: the
only callees `reduceRows` mentions (`stepRow`, and `slice` in `hnfResult`) are
A-references checked by G-AX, not consumed axioms.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — the
row-iteration range and the early stop — is modeled **deeply and concretely**
(the `while` loop + `reduceRows`, step A3), not hidden behind an axiom about the
function under change: there is no consumed axiom. The only A legs
(`stepRow`, `slice`) cover **unchanged** callees and are G-AX-validated
A-references.

## D. verify(Solution) ⇒ resolved

`hermiteNormalForm` verifies only if its output equals `hnfResult numCols
numRows A` — the matrix reduced over ALL `numRows` rows (with the `k=0` early
stop) then sliced (A3, B). By R (`DomainMatrix/rep ↔ Mat`, `shape ↔
(numRows,numCols)`) the verified loop equals the patched `_hermite_normal_form`
on the tested inputs; by G-AX the A-references `stepRow`/`slice` equal the real
unchanged per-row body and slice; by G-CONF the R/I transliteration of the loop
structure agrees with `patch.diff`'s behaviour on 10⁵ inputs (incl. the `m > n`
regime). Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and audited callees — and the gold patch
resolves (G-RESOLVE). Trust points are exactly the two of plan §1.1: A-reference
soundness (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
