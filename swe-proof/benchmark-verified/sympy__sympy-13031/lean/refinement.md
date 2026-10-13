# refinement.md — sympy__sympy-13031

Tags: **R** = type-only refinement (state bijection), **A-consumed** = proof uses an
axiom's property, **A-reference** = deep model validated `== real callee` by G-AX,
**I** = identical concrete op. Every op is R, A, or I. R/I legs refuted by G-CONF.

## `implementation_hJoin` ↔ patched `SparseMatrix.row_join` (sparse.py:1193-1214)

| Lean op | patch.diff op | tag | note |
|---|---|---|---|
| `Mat` carrier (`rows`, `cols`, `get`, `kind`) | the `SparseMatrix` object (dims + `[i,j]` accessor + concrete class) | R | type bijection in mapping.md; the touched aspects are shape + entries + result class (the hidden test asserts `type(a.row_join(b)) == type(a)`) |
| guard `if self.cols = 0 ∧ self.rows ≠ other.rows` | gold patched guard `if self.cols == 0 and self.rows != other.rows` | I | the patched special-case predicate; `cols == 0` ⇔ `self.cols = 0` |
| `return concatCols (zeroColsMat other.rows self.kind) other` | `return self._new(other.rows, 0, []).row_join(other)` | R | one-step unroll: the constructed receiver has `cols = 0`, `rows = other.rows`, kind = `self.kind` (`_new` is a classmethod of the receiver), so ITS guard is false and it provably takes the normal path = `concatCols (0×n receiver) other`; with an all-zero, zero-width receiver `concatCols` yields `other`'s shape and entries with `self`'s kind (proved in Lean, refuted in Python by G-CONF `hJoin`, incl. dense-`other` draws) |
| `return concatCols self other` | `A,B=self,other; ShapeError check; A=A.copy(); for (i,j),v in B._smat: A._smat[i,j+A.cols]=v; A.cols+=B.cols; return A` | R | the normal horizontal-concatenation path: left block reads `self`, right block reads `other` shifted by `self.cols`; result is `A.copy()` mutated in place, hence of `type(self)` = kind `self.kind`; sparsity/`copy`/dict-merge are representation details with no observable effect on entries |

The Lean predicate is exactly the gold patched guard (`self.rows ≠ other.rows` for
`row_join`, which compares ROWS). On the no-`ShapeError` domain the two branches
agree on shape/entries when `self.rows = other.rows`, so the guard split is
observable only through the `kind`/class conjunct and the null-stack shapes,
both validated end-to-end by G-CONF.

## `implementation_vJoin` ↔ patched `SparseMatrix.col_join` (sparse.py:985-1006)

| Lean op | patch.diff op | tag | note |
|---|---|---|---|
| `Mat` carrier | `SparseMatrix` object | R | as above (incl. `kind` = concrete class) |
| guard `if self.rows = 0 ∧ self.cols ≠ other.cols` | gold `if self.rows == 0 and self.cols != other.cols` | I | patched special-case predicate |
| `return concatRows (zeroRowsMat other.cols self.kind) other` | `return self._new(0, other.cols, []).col_join(other)` | R | one-step unroll, symmetric to hJoin; yields `other`'s shape/entries with `self`'s kind |
| `return concatRows self other` | normal vertical-concatenation path (`A._smat[i+A.rows,j]=v; A.rows+=B.rows`) | R | top block reads `self`, bottom block reads `other` shifted by `self.rows`; result of `type(self)` via `A.copy()` |

## Pre-patch (buggy) skeletons — `Solution_prepatch_{1,2}.lean`

| variant | buggy op | gold op | observable bug |
|---|---|---|---|
| prepatch_1 (hJoin) | `if self.rows = 0 ∨ self.cols = 0 then return { other with kind := self.kind }` | the patched guard + normal path | `not self` ⇔ `rows*cols == 0`; for `hstack(zeros(0,0),zeros(0,1),zeros(0,2),zeros(0,3))` each fold step discards the accumulated columns → shape `(0,3)` instead of `(0,6)` (the F2P failure). The buggy Python `return type(self)(other)` converts to the receiver's class, hence the kind override in the model (kind is faithful; the SHAPE is the bug). |
| prepatch_2 (vJoin) | `if self.rows = 0 ∨ self.cols = 0 then return { other with kind := self.kind }` | symmetric | `vstack` of `zeros(n,0)` → `(3,0)` instead of `(6,0)` |

Each prepatch's `correct_*` is FALSE on the precondition: e.g. for hJoin take
`self` a `0×2` matrix (`rows = 0`, `cols = 2`) and any `other` with
`other.rows = 0` — the precondition holds (`self.rows = other.rows`), the buggy
guard fires (`self.rows = 0`) and returns `other`, but the spec's `self.cols ≠ 0`
leg requires `result.cols = self.cols + other.cols = 2 + other.cols ≠ other.cols`.
Exactly the fold step that loses accumulated columns in the F2P `hstack` case.
So it cannot close → G-DIFF satisfied. One prepatch per independently-fixed
function.

## A-tags

None. No consumed callee axiom and no A-reference: both joins are modeled deeply,
so G-AX is a skip stub and G-CONF carries the full differential burden. `conf_skip`
is FALSE (the impl region is all R/I).
