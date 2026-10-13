# refinement.md — sympy__sympy-13031

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `stackHorizontally` / `stackVertically` `do` blocks and the deep
`hstackBlock`/`vstackBlock` models) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement; state the bijection), **A-consumed** (proof
uses an axiom's `ensures`), **A-reference** (deep model validated == real callee
by G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the A legs + narrative by **G-EQ**. There are **no A rows in this bundle** (no
unchanged callee is axiomatized; both kernels are modeled deeply with concrete
arithmetic — mapping.md §3). Claim: any impl verifying against this frozen spec,
refined per the maps below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. `stackHorizontally` ↔ `SparseMatrix.row_join` (`sparse.py:1159`)

Gold hunk:
```
-        if not self:
-            return type(self)(other)
+        # A null matrix can always be stacked (see  #10770)
+        if self.cols == 0 and self.rows != other.rows:
+            return self._new(other.rows, 0, []).row_join(other)
+
         A, B = self, other
         if not A.rows == B.rows:
             raise ShapeError()
         ...
         for (i, j), v in B._smat.items():
             A._smat[(i, j + A.cols)] = v
         A.cols += B.cols
         return A
```

| # | Solution.lean impl op (`stackHorizontally`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `A B : Block` | `self`, `other` (sparse matrices) | R | `(rows, cols, _smat)` ↔ `(Block.rows, Block.cols, Block.entries)` (mapping.md §2). |
| A2 | `require A.cols = 0 ∨ A.rows = B.rows` | the inputs on which post-patch `row_join` does NOT `raise ShapeError()` (`A.rows==B.rows`, plus the `self.cols==0` early branch covering the mismatched-height null case) | R | precondition = real callee's non-raising domain (mapping.md §2). |
| A3 | branch `A.cols = 0 ∧ A.rows ≠ B.rows` ⇒ result `{rows := B.rows, cols := A.cols + B.cols, entries := A.entries ++ B.entries.map (shiftRight A.cols)}` | `if self.cols == 0 and self.rows != other.rows: return self._new(other.rows, 0, []).row_join(other)` | I | the degenerate `A` (`cols=0`, so `entries=[]`, `A.cols=0`) is re-measured to `B.rows` and stacked; the recursive `row_join` on a `(other.rows, 0)` null matrix appends `B`'s cells with zero shift ⇒ exactly `B` at width `0 + B.cols`. Concrete arithmetic, transliterated by G-CONF. |
| A4 | else branch ⇒ `{rows := A.rows, cols := A.cols + B.cols, entries := A.entries ++ B.entries.map (shiftRight A.cols)}` | the main body: `A = self.copy()`; `for (i,j),v in B._smat: A._smat[(i, j+A.cols)] = v`; `A.cols += B.cols`; `return A` | I | width accumulates `A.cols + B.cols`; `B`'s cells shift right by `A.cols` (`shiftRight`); `A`'s cells and height are preserved. The exact concrete op of the gold body. |

Discriminating content: a width-zero, height-nonzero `A` (e.g. a `1×0` block)
must yield width `A.cols + B.cols = 0 + B.cols`, accumulated — and more sharply,
in the `reduce` chain `hstack` performs, the FIRST null operand `0×0` joined to
`0×1` must give `0×1`, then joined to `0×2` give `0×3`, … summing to `0×6`. The
pre-patch `if not self: return type(self)(other)` drops `A`'s width whenever
`A.rows*A.cols == 0`, so the accumulated width collapses. `Solution_prepatch_1.lean`
reproduces `if A.rows = 0 ∨ A.cols = 0 then return B` and **fails** `out =
hstackBlock A B` on the clause `B = hstackBlock A B` (the summed width `A.cols +
B.cols ≠ B.cols` when `A.cols > 0`, reachable under `require` via `A.rows = 0`).

## B. `stackVertically` ↔ `SparseMatrix.col_join` (`sparse.py:949`)

Gold hunk:
```
-        if not self:
-            return type(self)(other)
+        # A null matrix can always be stacked (see  #10770)
+        if self.rows == 0 and self.cols != other.cols:
+            return self._new(0, other.cols, []).col_join(other)
+
         A, B = self, other
         if not A.cols == B.cols:
             raise ShapeError()
         ...
         for (i, j), v in B._smat.items():
             A._smat[i + A.rows, j] = v
         A.rows += B.rows
         return A
```

| # | Solution.lean impl op (`stackVertically`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | params `A B : Block` | `self`, `other` | R | as A1. |
| B2 | `require A.rows = 0 ∨ A.cols = B.cols` | post-patch `col_join`'s non-raising domain | R | as A2, transposed (`cols`↔`rows`). |
| B3 | branch `A.rows = 0 ∧ A.cols ≠ B.cols` ⇒ `{rows := A.rows + B.rows, cols := B.cols, entries := A.entries ++ B.entries.map (shiftDown A.rows)}` | `if self.rows == 0 and self.cols != other.cols: return self._new(0, other.cols, []).col_join(other)` | I | transpose of A3: degenerate `A` re-measured to `B.cols`, summed height `0 + B.rows`. |
| B4 | else ⇒ `{rows := A.rows + B.rows, cols := A.cols, entries := A.entries ++ B.entries.map (shiftDown A.rows)}` | main body: `A._smat[i+A.rows, j] = v`; `A.rows += B.rows`; `return A` | I | transpose of A4: height accumulates, `B`'s cells shift down by `A.rows` (`shiftDown`). |

Discriminating content: transpose of §A — a height-zero, width-nonzero `A`
(e.g. `0×1`) must accumulate height `A.rows + B.rows`. `Solution_prepatch_2.lean`
reproduces `if A.rows = 0 ∨ A.cols = 0 then return B` and **fails** `out =
vstackBlock A B` on `B = vstackBlock A B`.

## C. No kind-3 (inexpressible-changed-op) steps; why two methods, no `hstack`/`vstack`

Every step is R or I; there are no A rows. The operations that genuinely changed
— the two join kernels' shape-and-cell arithmetic — are modeled **deeply**
(spelled-out `hstackBlock`/`vstackBlock`), not hidden behind an axiom.

`hstack`/`vstack` (`common.py:364,585`) are **unchanged**: they are
`reduce(kls.row_join, args)` / `reduce(kls.col_join, args)`. The issue's
multi-operand symptom (`hstack(0×0,0×1,0×2,0×3).shape == (0,3)` instead of
`(0,6)`) is the fold of the kernel bug: each `row_join` of a zero-area accumulator
discards the running width. Since `reduce` is unchanged and correct given a
correct kernel, modeling the **kernel** (`row_join`/`col_join`) is necessary and
sufficient — a verified kernel makes every `reduce` chain correct. Modeling
`hstack` itself would axiomatize `reduce` (an unchanged callee) needlessly.

Two independently-fixed behaviors ⇒ two methods ⇒ two failing prepatches
(`Solution_prepatch_1` for horizontal, `_2` for vertical), per G-DIFF.

## D. verify(Solution) ⇒ resolved

`stackHorizontally`/`stackVertically` verify only if their outputs equal the
deep models `hstackBlock`/`vstackBlock`, whose width/height is the **summed**
extent in every admissible case (A3/A4, B3/B4) — never the single-operand
collapse the bug produces. By R (`(rows,cols,_smat)` ↔ `Block`) the verified
kernels equal the post-patch `row_join`/`col_join` on the tested inputs; by the
unchanged `reduce` fold, correct kernels make `hstack`/`vstack` produce the
summed shape the F2P test demands (`SparseMatrix.hstack(*[0×n]) == Matrix(0,6,[])`,
`vstack(*[n×0]) == Matrix(6,0,[])`); by G-CONF the R/I transliteration agrees
with `patch.diff` (the post-patch `row_join`/`col_join`, which G-CONF git-applies
before running) over ≥10⁵ operand pairs. Therefore a model satisfying this spec,
refined by the maps above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). There are no axiom trust points (no A rows); the sole
trust point is refinement fidelity (this doc, G-EQ + G-CONF). G-AX is skipped —
both modeled functions are *under change*, so (per SPEC_GUIDE directive 7) they
are validated by G-CONF against the patched callees, never axiom-checked against
the buggy base-commit callees.
