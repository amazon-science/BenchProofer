# mapping.md — sympy__sympy-13031

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 2dfa7457f20ee187fbb09b5b6a1631da4458388c`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of every callee.

Repo file under change: `sympy/matrices/sparse.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `stackHorizontally (A B : Block)` | `SparseMatrix.row_join(self, other)` — `sympy/matrices/sparse.py:1159` | modeled changed function #1 (place `other` to the right of `self`) |
| `stackVertically (A B : Block)` | `SparseMatrix.col_join(self, other)` — `sympy/matrices/sparse.py:949` | modeled changed function #2 (place `other` below `self`) |
| `Block` | a sparse matrix instance: `.rows`, `.cols`, `._smat` (the dict of stored cells) | rich-object carrier (only the touched fields) |
| `hstackBlock` | the post-patch *body* of `row_join` (its shape+cell result) | pure spec: the horizontally-stacked block |
| `vstackBlock` | the post-patch *body* of `col_join` (its shape+cell result) | pure spec: the vertically-stacked block |
| `shiftRight n` | the post-patch cell relocation `A._smat[(i, j + A.cols)] = v` (`sparse.py:1216`) | pure spec: column shift of a stored cell |
| `shiftDown n` | the post-patch cell relocation `A._smat[(i + A.rows, j)] = v` (`sparse.py:1006`) | pure spec: row shift of a stored cell |

`Block.entries` abstracts `_smat` as an association list `((i, j), v)`. The
pre-patch guard the change removes — `if not self: return type(self)(other)`
(`sparse.py:988` in `col_join`, `sparse.py:1190` in `row_join`) — is the bug
locus; it is recorded here for the refinement audit, not named in the spec view.

`A` is `self`, the matrix the join is invoked on; `B` is `other`, the argument.
The modeled functions are the join **kernels**: `hstack`/`vstack`
(`common.py:364,585`) are UNCHANGED reductions (`reduce(kls.row_join, args)` /
`reduce(kls.col_join, args)`) over these kernels, so the multi-operand bug the
issue reports is fully reproduced by ONE faulty kernel application — modeling the
kernel is necessary and sufficient (refinement.md §C).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `m.rows` (a sparse matrix's row count, a non-negative int) | `Block.rows : Nat` | identity on `ℕ` |
| `m.cols` (column count) | `Block.cols : Nat` | identity on `ℕ` |
| `m._smat` : `dict[(int,int), Expr]` (stored nonzero cells) | `Block.entries : List ((Nat × Nat) × Int)` | `{(i,j): v}` ↔ unordered `[((i,j), v)]`; key `(i,j)` ↔ `(i,j)`; the *set of keys/values* is the observable (G-CONF compares as a dict / set of pairs, order-insensitive) |
| a stored cell value `v` (`Integer`) | `Int` | the F2P/PASS inputs are integer-valued sparse matrices; `Integer n` ↔ `n`. Cell **values** are carried unchanged by both joins, so any value domain works; `Int` suffices for the tests. |
| `not m` ⇔ `m.rows*m.cols == 0` (`Matrix.__len__`, `matrices.py:1845`) | `A.cols = 0` / `A.rows = 0` guards | `bool(m)` is `len(m) != 0 = (rows*cols != 0)`; a matrix is "empty" iff either extent is 0. The pre-patch guard `not self` is `A.rows = 0 ∨ A.cols = 0` (prepatch skeletons); the post-patch narrow guard tests one extent only. |

`Block` carries exactly the three touched fields (`rows`, `cols`, `_smat`);
all other matrix state (storage class, flags) is invariant under both joins and
omitted. The result type is `Matrix`/`SparseMatrix`; the bijection observes only
`(rows, cols, _smat)` — which is what `==` (`sparse.py:93`) and the F2P shape
assertions compare.

### Compatibility (`require`) — provenance
Post-patch `row_join` raises `ShapeError` unless `A.rows == B.rows` OR `A.cols == 0`
(the `self.cols == 0` early branch handles the mismatched-height null case). The
`require A.cols = 0 ∨ A.rows = B.rows` precondition is exactly the set of operand
pairs on which the real `row_join` returns normally (does not raise). Symmetric
for `col_join`: `require A.rows = 0 ∨ A.cols = B.cols`. Inputs outside `require`
raise in the real code and are not modeled (the F2P/PASS calls all satisfy it).

## 3. Callee provenance (kind-A)

**No axioms and no A-reference deep models, so G-AX is skipped** (gates.py
`gate_ax` returns `skip` when no `axiom_check.py` exists — exactly the
django__django-11603 precedent: a deeply-modeled *changed* function, validated
end-to-end by G-CONF rather than by any axiom).

Both join kernels are modeled **deeply** with concrete shape-and-cell arithmetic
(`hstackBlock`/`vstackBlock` in the `pure` region): extent addition
(`A.cols + B.cols` / `A.rows + B.rows`), the degenerate-operand re-measure, and
the coordinate shift of `B`'s stored cells (`shiftRight`/`shiftDown`). Every
operation in the impl region is concrete (refinement.md: all rows R or I). The
only repository entities the body touches — `self.copy()`, `_smat` item
iteration, `_new(...)`, `+=` on `rows`/`cols` — are container/arithmetic
primitives, not unchanged domain callees whose contract the proof must assume.
Hence the `axioms` region is empty.

**Why no `axiom_check.py`.** The deep models encode the **post-patch** kernel
behaviour. G-AX, by construction, runs the REAL callee at `base_commit` — i.e.
the *un-patched, buggy* `row_join`/`col_join` (`if not self: return type(self)
(other)`) — and would therefore report the deep model "unsound" on a null
operand (`row_join((0,1),(0,2))` returns `(0,2)` pre-patch vs the model's `(0,3)`).
That is precisely the SPEC_GUIDE directive-7 trap: G-AX must never be pointed at
the function **under change**. Validation of a deeply-modeled changed function
belongs to **G-CONF**, which git-applies `patch.diff` first and so observes the
post-patch callee. `axiom_check.py` is therefore intentionally absent.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13031`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`hstackBlock`/`vstackBlock` (all R/I ops) to Python over the real `SparseMatrix`
type and diffs against `patch.diff`'s behaviour (the patched `row_join`/`col_join`)
over ≥10⁵ fuzzed operand pairs. There is no A-tagged callee, so `conf_skip=false`
and G-CONF carries full weight.
