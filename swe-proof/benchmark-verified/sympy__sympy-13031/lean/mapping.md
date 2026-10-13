# mapping.md — sympy__sympy-13031

## Symbol binding (file:line @ base_commit `2dfa7457f2`)

Two independently-fixed functions in `sympy/matrices/sparse.py`:

| Lean triple | Python symbol | file:line @ base_commit |
|---|---|---|
| `implementation_hJoin` / `problem_spec_hJoin` / `correct_hJoin` | `SparseMatrix.row_join(self, other)` (appends `other`'s columns to the right of `self` → wider matrix `[A B]`) | `sympy/matrices/sparse.py:1159-1214` (patched guard at lines 1193-1196) |
| `implementation_vJoin` / `problem_spec_vJoin` / `correct_vJoin` | `SparseMatrix.col_join(self, other)` (stacks `other` beneath `self` → taller matrix `[A;B]`) | `sympy/matrices/sparse.py:949-1007` (patched guard at lines 985-988) |

NB the sympy names are counter-intuitive: `row_join` produces *more columns* (horizontal
concatenation), `col_join` produces *more rows* (vertical concatenation). The Lean names
are chosen by the **observable behavior** (horizontal / vertical join), not the repo symbol.

## Callers (unchanged, not modeled)

- `MatrixRequired.hstack(cls, *args) = reduce(kls.row_join, args)` — `sympy/matrices/common.py:364`.
- `MatrixRequired.vstack(cls, *args) = reduce(kls.col_join, args)` — `sympy/matrices/common.py:585`.

The patch touches only the binary join primitives; the variadic `hstack`/`vstack` are a
plain `reduce` over them, so modeling the binary primitive at the right granularity implies
the variadic behavior. These callers are NOT modeled and NOT axiomatized.

## Truthiness / dimensions

- `Matrix.__len__(self) = self.rows * self.cols` (`common.py:2224`). Thus Python `not self`
  (the pre-patch guard) is `self.rows * self.cols == 0`, i.e. true when EITHER dimension is 0.
- `self._new(r, c, [])` builds an `r × c` matrix of the RECEIVER's class with no stored
  entries — modeled by `zeroColsMat`/`zeroRowsMat` (a matrix of the given shape and kind
  whose accessor is identically 0).

## Result class (`kind`)

`Mat.kind : Nat` models the concrete Python class of the matrix object
(`MutableSparseMatrix`, `ImmutableSparseMatrix`, dense `Matrix`, …) under an arbitrary
injective enumeration; only equality of kinds is ever used. Both patched joins ALWAYS
return a matrix of the receiver's class:

- normal path: `A = self.copy()` (`copy = self._new(...)`, sparse.py:610) mutated in
  place → `type(self)`;
- special branch: `self._new(...)` builds a receiver-class null matrix and recurses,
  landing in the normal path → `type(self)`.

This is graded by the hidden test (`test_sparse.py`):
`a = MutableSparseMatrix([]); b = MutableDenseMatrix([1,2]);
assert type(a.row_join(b)) == type(a)` (same for `col_join`) — with `a` null, so the
special branch is the one exercised. The specs therefore pin `result.kind = self.kind`.
Returning `other` itself (a dense matrix) would satisfy a shape/entries-only spec but
fail this test; the `kind` conjunct excludes that impl class.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean |
|---|---|
| a matrix object | `structure Mat (rows cols : Nat) (get : Nat → Nat → Int) (kind : Nat)` |
| `M.rows`, `M.cols` | `M.rows`, `M.cols` (`Nat`) |
| `M[i, j]` for `0 ≤ i < rows`, `0 ≤ j < cols` | `M.get i j` (`Int`); accessor is total in Lean, the bijection is meaningful only on in-range indices, and spec/impl agree everywhere |
| matrix entry value (symbolic, but integer in the F2P tests) | `Int` |
| `type(M)` (concrete matrix class) | `M.kind` (`Nat`, injective enumeration of classes; only `=` is used) |
| `row_join` normal path `[A B]` (`type(self)` result) | `concatCols A B` (kind = `A.kind`) |
| `col_join` normal path `[A;B]` (`type(self)` result) | `concatRows A B` (kind = `A.kind`) |
| `self._new(other.rows, 0, [])` | `zeroColsMat other.rows self.kind` |
| `self._new(0, other.cols, [])` | `zeroRowsMat other.cols self.kind` |

The recursive call `self._new(other.rows,0,[]).row_join(other)` in the patched special branch
is refined to `concatCols (zeroColsMat other.rows self.kind) other`: the constructed receiver
has `cols = 0`, `rows = other.rows` and the receiver's class (`kind = self.kind`), so its own
guard `cols == 0 and rows != other.rows` is FALSE and it provably takes the normal path, which
is exactly `concatCols`. (Symmetrically for `col_join`.) This is the single, statically-
justified unrolling of the one-step recursion — an R/I refinement, recorded in refinement.md.

## Preconditions (binders of `correct_*`, not spec conjuncts)

- `hJoin`: `self.cols = 0 ∨ self.rows = other.rows` — exactly the inputs for which the patched
  `row_join` does NOT raise `ShapeError` (if `self.cols > 0` the normal path requires equal
  rows; if `self.cols = 0` either the special branch reshapes or the rows already match).
- `vJoin`: `self.rows = 0 ∨ self.cols = other.cols` — symmetric.

## Flag dependencies

None.

## G-CONF fuzz seed

`13031` (pinned in meta.json `verifier_pins.conf_seed`).
