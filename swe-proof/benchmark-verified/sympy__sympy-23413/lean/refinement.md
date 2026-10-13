# refinement.md — sympy__sympy-23413

Operation-by-operation correspondence between `implementation_hermiteNormalForm`
(Solution.lean impl region) and `patch.diff` (the gold edit to the outer
row-processing loop of `_hermite_normal_form`). Tags: **R** type refinement ·
**A-consumed** proof uses an axiom · **A-reference** deep-modeled callee
validated == real callee by G-AX · **I** identical concrete op.

The patch changes WHICH rows the outer loop processes and WHEN it stops. Pre-patch
it iterates only the bottom `min(m, n)` rows (`for i in range(m-1, m-1-rows, -1)`
with `rows = min(m, n)`) and never breaks. Post-patch it iterates every row
bottom-to-top (`for i in range(m-1, -1, -1)`) and breaks as soon as the pivot
pointer reaches the leftmost column (`if k == 0: break`). When `m > n` the
pre-patch loop skips the topmost `m - n` rows, so a genuine pivot in a topmost
row is never placed and its column is dropped — the reported "HNF removing rows"
bug. The per-row reduction and the final column slice are unchanged.

| # | `implementation_hermiteNormalForm` op | `patch.diff` / post-patch Python op | tag | note |
|---|---|---|---|---|
| 1 | `let mut A := A0` | `A = A.to_dense().rep.copy()` | R | `DomainMatrix` dense rep ↔ `Mat = List (List Int)` |
| 2 | `let mut k := n` | `k = n` | I | pivot-column pointer init |
| 3 | `for i in rowsDesc m do …` | `for i in range(m - 1, -1, -1):` | R | **the fix**: iterate EVERY row bottom→top; `rowsDesc m = (range m).reverse` ↔ `range(m-1,-1,-1)`. Pre-patch iterated only `range(m-1, m-1-min(m,n), -1)` |
| 4 | `if k = 0 then break` | `if k == 0: break` | R | **the fix**: stop once the pointer reaches the leftmost column (all columns hold a pivot) |
| 5 | `let p := step A i k; A := p.1; k := p.2` | the per-row body (`k -= 1`; inner `add_columns` clears; sign fix; `if b==0: k+=1` else reduce-right) | R | UNCHANGED per-row reduction, `opaque step` (signature only, no `_prop`); returns updated matrix + pointer |
| 6 | `return sliceCols A k` | `return DomainMatrix.from_rep(A)[:, k:]` | R | UNCHANGED column slice, `opaque sliceCols` (signature only) |

Every op is R or I. No op is A-consumed or A-reference:

- The changed decision (ops 3/4 — the row set and the early break) is modeled
  DEEPLY and structurally over the row indices (`rowsDesc` + `hnfFold` + the
  imperative loop); SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed
  op, so it is spelled out.
- `step` and `sliceCols` are UNCHANGED callees carried as opaque SIGNATURES (no
  `_prop` axiom). They appear identically in the spec (`hnfFold` / `sliceCols`)
  and the impl, so they cancel in the differential test and the proof consumes
  no property of them. Hence the `axioms` region declares only signatures and
  **G-AX skips**.
- `A.domain.is_ZZ` guard (normalforms.py:205) is a precondition on the input
  domain, not modeled.

The spec leaves NO output component free: `result` is pinned to
`sliceCols p.1 p.2` where `p = hnfFold (rowsDesc m) A0 n` — a total function of
the input matrix and its shape (directive 5 frame, directive 8 grounding). The
opaque callees make the value abstract, but the spec fixes it to be *exactly* the
value the modeled control flow produces, so a wrong impl (e.g. one iterating the
wrong row set) cannot satisfy it.

## Pre-patch (the bug)

`Solution_prepatch.lean`'s impl reproduces the defect: the loop iterates only
`(rowsDesc m).take (min m n)` — the bottom `min(m, n)` rows — with NO `k = 0`
break, exactly the pre-patch `for i in range(m-1, m-1-min(m,n), -1)`. Its
`correct_hermiteNormalForm` cannot close: the spec folds `step` over ALL of
`rowsDesc m` (with the `k = 0` short-circuit), whereas the prepatch folds over
only the bottom `min(m, n)` rows. For a matrix with `m > n` these differ — the
prepatch omits the topmost `m - n` rows, so `step`/`sliceCols` receive a
different (matrix, pointer) pair and the result differs. This is precisely the
observable failure for `Matrix([[1,12],[0,8],[0,5]])` (3×2) and the reporter's
3×1 case. (G-DIFF: the prepatch must fail G-VERIFY.)

## Spec tightness / equivalence class

The post-condition equates `result` with ONE exact value — `sliceCols p.1 p.2`
for `p = hnfFold (rowsDesc m) A0 n`, a total function of the input matrix and
its shape — so verification is extensional equality with the post-patch
reduction. Implementations that differ from the gold imperative loop only by
provably-equal restructuring are CORRECT, not counterexamples. In particular an
implementation that restates the reference fold (`hnfFold`/`rowsDesc`/
`sliceCols` applied directly) is NOT an "ungrounded oracle echo" in the
SPEC_GUIDE §0.8 sense: nothing here is an axiomatized answer key. The changed
decision (which rows are processed, and the `k = 0` early stop) is spelled out
structurally in the `pure` region, and the unchanged callees (`step`,
`sliceCols`) are opaque signatures the impl must still invoke identically — so
restating the fold *performs* the modeled computation, and its faithful Python
realization is exactly the post-patch loop (the gold patch), which resolves.
Such variants are alternative positive controls. No impl that differs from the
modeled reduction on ANY input can close `correct_hermiteNormalForm` with clean
axioms (the pre-patch row set `(rowsDesc m).take (min m n)`, a missing or
misplaced break, and a wrong slice pointer all denote different functions and
provably cannot close).

## G-CONF (R/I differential)

`conformance_check.py` builds the Python shadow of the impl region (op-for-op,
with `step`/`sliceCols` modeled identically — deterministic — on both sides) and
diffs it against an in-process replica of the POST-PATCH loop over the edge
corpus + ≥1e5 fuzzed shapes `(m, n)`; zero disagreements expected. Pinned seed
23413. The impl region is NOT all-A-tagged (ops 3/4/5/6 are R), so
`conf_skip = false`.
