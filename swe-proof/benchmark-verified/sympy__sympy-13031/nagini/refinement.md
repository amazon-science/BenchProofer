# refinement.md — sympy__sympy-13031

The operation-by-operation correspondence between `model.py`'s implementation
(the `concat_right` and `concat_below` impl regions) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement, refined carrier type),
**A** (axiomatized callee — **A-consumed**, the proof uses the axiom's `Ensures`,
or **A-reference**, a deep model validated == the real callee by
`axiom_check.py` / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

This is a **multi-site** change: two structurally symmetric functions are
patched with the same fix (rows↔cols transposed). Each is modeled as its own
contracted function; the per-function marker regions repeat. The two sites fail
independently in `model_prepatch.py` (one failing postcondition per function).

**The carrier.** A matrix is abstracted to five facets: `rows`, `cols`, and three
facets of the population of cells it HOLDS under the repo's own retention
predicate (value TESTS TRUE — `sparse.py:62, 68, 79, 89` in the constructor and
`:1000` / `:1206` in the merge loops): the count `held`, the sum `rsum` of the
held cells' row indices, and the sum `csum` of their column indices. Why five and
not two: `SparseMatrix.__eq__` (`sparse.py:93-101`) compares the
**coordinate-keyed** store, so the F2P assertion `a.row_join(b) == b` observes
which cells the result holds AND where they sit. `held` alone cannot see a
permutation of the cells; the two index sums can. See mapping.md §2.

## A. Horizontal concatenation — `SparseMatrix.row_join` (`sympy/matrices/sparse.py:1159`, patched `:1161`)

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
         A.cols += B.cols
         return A
```

| # | model.py impl op (`concat_right`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `a: Mat`, `b: Mat` (shape + the three held-cell facets) | `self`, `other` (`SparseMatrix`) | R | `SparseMatrix` ↔ `Mat(rows, cols, held, rsum, csum)` (mapping.md §2). The tested observations are on the shape AND, for a null-operand join against a populated operand, on content and placement (`a.row_join(b) == b`, decided by `__eq__` over the coordinate-keyed store, `sparse.py:93-101`). |
| A2 | `if a.cols == 0 and a.rows != b.rows:` | `if self.cols == 0 and self.rows != other.rows:` | I | identical guard on the shape facets. |
| A3 | `base = Mat(b.rows, 0, 0, 0, 0); return concat_right(base, b)` | `return self._new(other.rows, 0, []).row_join(other)` | R + I | `self._new(other.rows, 0, [])` ↔ `Mat(b.rows, 0, 0, 0, 0)` (a fresh, explicitly empty `other.rows x 0` matrix — R on the constructor; all three population facets 0 because a zero-dimension matrix has no cells); the recursive `.row_join(other)` ↔ `concat_right(base, b)` is the same self-call (I). In the recursion the rebuilt operand has matching rows, so it takes the normal summing path → result shape `(b.rows, b.cols)`, `0 + b.held` cells, and — because the frame contributes `a.cols == 0` to the column offset of A5 — those cells land at `b`'s OWN coordinates. That is why the fix is content- and placement-preserving: the empty rebuild is a FRAME that is then merged with `other`, not the returned value. |
| A4 | `if a.rows != b.rows: raise ShapeMismatch()` | `if not A.rows == B.rows: raise ShapeError()` | R + I | the rejection test is identical (I); `ShapeError` ↔ `ShapeMismatch` is the exception type refinement (R, mapping.md §2 — a user-defined exception is required because builtin / third-party exceptions crash Nagini's `Exsures`). |
| A5 | `return Mat(a.rows, a.cols + b.cols, a.held + b.held, a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)` | the merge body + `A.cols += B.cols; return A` (`sparse.py:1206-1213`) | A-reference | four claims about the unchanged merge, all modeled **deeply** as integer arithmetic: the joined shape is `(self.rows, self.cols + other.cols)`; the joined result holds `held(self) + held(other)` cells; `self`'s cells keep both coordinates; `other`'s cells keep their row index and move right by `self.cols`. The `_smat` copy re-keys every entry of `B` at `(i, j + A.cols)` under the same `if v:` filter — injective, dropping and inventing nothing, displacing along one axis only — so the net effect on the five facets is exactly that arithmetic. There is **no consumed axiom**; G-AX validates the deep model == the real `row_join(a, b)` observed on all five facets over operands with varied payloads (mapping.md §3.1-3.2). |

## B. Vertical concatenation — `SparseMatrix.col_join` (`sympy/matrices/sparse.py:949`)

Gold hunk (the exact rows↔cols transpose of A):
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
         A.rows += B.rows
         return A
```

| # | model.py impl op (`concat_below`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | params `a: Mat`, `b: Mat` | `self`, `other` | R | as A1. |
| B2 | `if a.rows == 0 and a.cols != b.cols:` | `if self.rows == 0 and self.cols != other.cols:` | I | identical guard. |
| B3 | `base = Mat(0, b.cols, 0, 0, 0); return concat_below(base, b)` | `return self._new(0, other.cols, []).col_join(other)` | R + I | as A3, transposed. |
| B4 | `if a.cols != b.cols: raise ShapeMismatch()` | `if not A.cols == B.cols: raise ShapeError()` | R + I | as A4. |
| B5 | `return Mat(a.rows + b.rows, a.cols, a.held + b.held, a.rsum + b.rsum + a.rows * b.held, a.csum + b.csum)` | merge body + `A.rows += B.rows; return A` (`sparse.py:1000-1007`) | A-reference | as A5, transposed: joined shape `(self.rows + other.rows, self.cols)`, joined cell count the sum, `other`'s cells keep their column index and move down by `self.rows`. Deep model validated == the real `col_join(a, b)` on all five facets by G-AX. |

## C. The discriminating content of the change

The pre-patch guard `if not self: return type(self)(other)` fires for **any**
null matrix — `not self` is `len(self) == self.rows * self.cols == 0`
(mapping.md §1). It discards `self` entirely and returns a matrix shaped like
`other`, RESETTING any already-accumulated dimension. The fix narrows the guard
to the genuinely-empty (zero shared-dimension) case that also needs a row/column
normalisation, and otherwise lets the normal summing path run — so a chain of
zero-row (resp. zero-column) operands now ACCUMULATES the orthogonal dimension.

The discriminating case (modeled, tested): `a` with `rows == 0, cols > 0` joined
(horizontally) with `b` having `rows == 0`.
- **gold / model.py:** `a.cols == 0`? No → not the normalisation branch → rows
  agree (`0 == 0`) → `Mat(0, a.cols + b.cols, ...)`. Columns accumulate.
- **pre-patch / model_prepatch.py:** `a.rows * a.cols == 0` (rows 0) → returns
  `Mat(b.rows, b.cols, ...) = (0, b.cols, ...)`, dropping `a.cols`.

`model_prepatch.py` reproduces the pre-patch guard in BOTH functions and **fails**
the postcondition `Result().cols == a.cols + b.cols` (resp.
`Result().rows == a.rows + b.rows`) — one failing postcondition per site
(G-DIFF, one independently-observable fixed behaviour each). This is exactly the
F2P chain: `hstack(*[zeros(0,n) for n in range(4)])` must be `(0, 6)` not `(0, 3)`
and `vstack(*[zeros(n,0) for n in range(4)])` must be `(6, 0)` not `(3, 0)`.

### C.1 The second discriminating observation: CONTENT

The F2P test `test_sparse_matrix` makes a second, independent observation that the
shape facets alone cannot express:

```
a = MutableSparseMatrix([])      # 0 x 0, holds nothing
b = MutableDenseMatrix([1, 2])   # 2 x 1, holds two cells
assert a.row_join(b) == b
assert a.col_join(b) == b
```

Both calls take the degenerate-normalisation path, and both assert equality with
`b` — an observation of the result's CONTENT, not merely its shape. The patched
code satisfies it because the rebuild `self._new(other.rows, 0, [])` is only a
*frame*: it is then recursively joined with `other`, and the unchanged merge
copies `other`'s cells in. A rival that returns a correctly-shaped but EMPTY
matrix on this path (e.g. `self._new(other.rows, other.cols, [])`) satisfies every
shape clause and still fails the F2P assertion, returning an all-zero `2 x 1`
where `b` was required. Both functions therefore carry the unconditional
postcondition

    Ensures(Result().held == a.held + b.held)

which is TRUE of the real patched callee on every returning path (validated over
the operand grid with varied payloads plus the literal F2P case by G-AX and
G-CONF, mapping.md §3.2) and FALSE of the cell-dropping rival. It is stated as
behaviour — concatenation carries both operands' cells over and invents none —
not as a restatement of either implementation.

### C.2 The third discriminating observation: PLACEMENT

Shape and cell count together are still not enough, because `__eq__` compares the
coordinate-keyed store (`sparse.py:93-101`): a result of the right shape holding
the right NUMBER of cells, but with those cells relocated, is unequal to `b` and
would not resolve. Concretely, a rival that on the `a.held == 0` path returns
`Mat(a.rows, a.cols + b.cols, b.held, b.rsum, b.csum)` — dropping the column
offset — satisfies every shape clause and the count clause of C.1, yet for
`a = zeros(2, 3)`, `b = Matrix(2, 1, [1, 2])` it claims the two cells sit in
column 0 where the real callee puts them in column 3.

So both functions also carry, unconditionally:

    concat_right:  Ensures(Result().rsum == a.rsum + b.rsum)
                   Ensures(Result().csum == a.csum + b.csum + a.cols * b.held)
    concat_below:  Ensures(Result().csum == a.csum + b.csum)
                   Ensures(Result().rsum == a.rsum + b.rsum + a.rows * b.held)

These are TRUE of the real merge (A5/B5: `B`'s entries are re-keyed at
`(i, j + A.cols)` resp. `(i + A.rows, j)`, `sparse.py:1206-1213` / `:1000-1007`)
and FALSE of the relocating rival. On the degenerate-normalisation path the frame
contributes offset 0, so `b`'s cells keep their own coordinates — which is
precisely what `a.row_join(b) == b` asserts. G-CONF's negative control (f)
measures that these two clauses are load-bearing: swapping the offset term to
`b.cols * a.held` produces 1 994 disagreements with the real callee.

### C.3 The retention predicate is measured, not assumed

`held` counts the cells whose value TESTS TRUE, because that is the predicate the
repo itself uses (`if value:` / `if v:`, `sparse.py:62, 68, 79, 89, 1000, 1206`).
The plausible alternative — "unequal to zero" — is a DIFFERENT predicate: for a
sympy object such as `S.false`, `Eq(1, 2)`, `EmptySet()` or `FiniteSet()` the two
disagree. Both out-of-band probes measure the difference rather than assert the
choice: `axiom_check.py::_check_predicate_splits` finds operands where the two
readings differ (9 in the recorded run) and refutes the deep model under the
rejected reading (9 refutations), and `conformance_check.py` finds 40 splitting
operands and fails the run if it finds none; negative control (e), which switches
the bridge to the rejected reading, yields 509 disagreements. A value whose truth
is INDETERMINATE (`x > 0`) is outside the carrier's domain and outside the real
callee's too — it raises `TypeError` — which `_check_domain_boundary` measures on
4 probes.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operation that genuinely
*changed* — the null-matrix guard logic — is modeled **deeply** (the spelled-out
`if`/recursion/`raise`/sum in the impl region), not hidden behind an axiom about
the function under change. There is **no consumed `@ContractOnly` axiom**: the
only opaque sub-operation, the unchanged merge's net effect on the five facets, is
an **A-reference** (integer arithmetic), validated == the real callee by G-AX. The
`axioms` region is intentionally empty.

## E. verify(model) ⇒ resolved

`concat_right` / `concat_below` verify only if

* the result shape is the column (row) SUM on the accumulation path (A5/B5) and
  the normalised `(b.rows, b.cols)` on the degenerate-normalisation path (A3/B3);
* the result holds the SUM of the operands' cells on *every* returning path (C.1);
* those cells sit where concatenation puts them — `a`'s unmoved, `b`'s displaced
  along the concatenation axis by exactly `a.cols` (resp. `a.rows`) — on *every*
  returning path (C.2);
* the incompatible path raises (A4/B4);
* and the function terminates: `MustTerminate` at level 3 on an operand that can
  still normalise, 2 on the callee it reaches, above `Mat.__init__` at 1, so the
  self-call is a strictly decreasing descent of depth at most one and no diverging
  rival satisfies the contract.

By R (matrix ↔ `Mat`'s five facets, `ShapeError` ↔ `ShapeMismatch`) the verified
functions are the two gold hunks up to that abstraction; by G-AX the deep
shape + content + placement model equals the real `row_join`/`col_join` behaviour
(A-reference). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited reference — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
callee soundness (G-AX) and refinement fidelity (this document, G-EQ).
