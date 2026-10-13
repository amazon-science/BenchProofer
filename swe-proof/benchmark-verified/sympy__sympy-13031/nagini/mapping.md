# mapping.md — sympy__sympy-13031

Binds every `model.py` symbol to its repository counterpart, states the type
abstraction, and gives the provenance of the callee behaviour the deep model is
validated against.

Repo file under change: `sympy/matrices/sparse.py` (the `SparseMatrix`
overrides of the two stacking methods).

**Line-number convention.** Bare `sparse.py:N` is the line at
`base_commit = 2dfa7457f20ee187fbb09b5b6a1631da4458388c`. Where the patch shifts
a line, the post-patch number in the instance worktree is given as
`(patched :M)`: the `col_join` region shifts by +2 and the `row_join` region by
+4, because each hunk replaces 2 lines with 4.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line) | role |
|---|---|---|
| `concat_right(a, b)` | `SparseMatrix.row_join(self, other)` — `sympy/matrices/sparse.py:1159` (patched :1161); changed guard at `:1194-1195` → patched `:1196-1198` | modeled changed function: horizontal concatenation (append `other`'s columns to the right of `self`) |
| `concat_below(a, b)` | `SparseMatrix.col_join(self, other)` — `sympy/matrices/sparse.py:949`; changed guard at `:988-989` → patched `:988-990` | modeled changed function: vertical concatenation (append `other`'s rows beneath `self`) |
| `Mat(rows, cols, held, rsum, csum)` | a matrix instance abstracted to its shape together with three facets of the population of cells it HOLDS | minimal carrier: the touched facets |
| `Mat.rows` / `Mat.cols` | `self.rows` / `self.cols` (`sparse.py:45-46, 53-54, 84-85`) | non-negative int dimension counts |
| `Mat.held` | `#{(i, j) : bool(self[i, j])}` — the size of the population the repo's OWN retention predicate keeps: `if value:` at `sparse.py:62, 79, 89` and `if v:` at `:68` (constructor), `if v:` at `:1000` (patched :1002, the `col_join` merge loop) and `:1206` (patched :1210, the `row_join` merge loop) | non-negative int count of held cells; the CONTENT facet the F2P equality assertion turns on |
| `Mat.rsum` | `Σ i` over the held cells `(i, j)` | non-negative int; first PLACEMENT facet (where the held cells sit on the row axis) |
| `Mat.csum` | `Σ j` over the held cells `(i, j)` | non-negative int; second PLACEMENT facet (column axis) |
| `Mat(a.rows, a.cols + b.cols, a.held + b.held, a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)` (in `concat_right`) | the unchanged merge body + `A.cols += B.cols; return A` (`sparse.py:1206-1213`, patched `:1210-1217`) | deep model (A-reference) of the unchanged callee: the joined column count is the SUM, the joined held-cell count is the SUM, and `B`'s held cells are re-keyed at column offset `A.cols` and at row offset 0 |
| `Mat(a.rows + b.rows, a.cols, a.held + b.held, a.rsum + b.rsum + a.rows * b.held, a.csum + b.csum)` (in `concat_below`) | merge body + `A.rows += B.rows; return A` (`sparse.py:1000-1007`, patched `:1002-1009`) | deep model (A-reference): the exact transpose |
| `ShapeMismatch` | `sympy.matrices.common.ShapeError` (raised at `sparse.py:1198` for `row_join`, `:992` for `col_join`; patched `:1202` / `:994`) | user-defined exception standing for the incompatible-shape rejection (builtin / third-party exceptions crash the Nagini translator inside `Exsures`) |
| `Mat(b.rows, 0, 0, 0, 0)` / `Mat(0, b.cols, 0, 0, 0)` (the normalisation rebuild) | `self._new(other.rows, 0, [])` / `self._new(0, other.cols, [])` (`_new` at `sparse.py:849`), introduced by the patch | the degenerate-normalisation reconstruction. All three population facets are 0 because a zero-dimension matrix has no cells — and crucially it is then **recursively joined with `other`**, so `other`'s held cells are carried in by the normal merge at offset 0. The rebuild is an empty *frame*, not the returned value |

Pre-patch repo code the change removes (for the refinement audit; not referenced
from the consumer spec view): in both methods the guard `if not self:` /
`return type(self)(other)` (`sparse.py:988-989` for `col_join`, `:1194-1195` for
`row_join`). `not self` is `bool(self) == bool(len(self))` and
`len(self) == self.rows * self.cols` (`sympy/matrices/matrices.py:1845-1850`,
`__len__` returns `rows*cols`; the comment there reads "Implemented mainly so
`bool(Matrix()) == False`"). So the removed guard fired for ANY null matrix
(zero rows OR zero columns) and replaced `self` wholesale with `other`.

**The modelled behaviour is not local to this class.** At `base_commit` the
general-purpose implementation of the same two operations already carries the
exact rule the model states: `sympy/matrices/common.py:242-244`
(`col_join`: `if self.rows == 0 and self.cols != other.cols: return
self._new(0, other.cols, []).col_join(other)`) and `:478-480` (`row_join`,
transposed). Only the `SparseMatrix` override diverged from it. So `model.py`
describes concatenation as the repo itself already defines it elsewhere, and
`conformance_check.py::_check_class_agnostic` MEASURES that (5 000 observations
against the general-purpose dense class, 0 disagreements) rather than asserting
it.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a matrix instance | `Mat` with `rows: int`, `cols: int`, `held: int`, `rsum: int`, `csum: int` | the shape plus three facets of the held-cell population. The F2P test makes **two** kinds of observation: the stacking chains compare `.shape` / equality of null matrices (fixed by `(rows, cols)`), and `a.row_join(b) == b` / `a.col_join(b) == b` for a null `a` and a **populated** `b` compares CONTENT AND PLACEMENT — `__eq__` (`sparse.py:93-101`) compares `self._smat` against `MutableSparseMatrix(other)._smat`, i.e. the held cells **keyed by coordinate**. So equality is "same shape and same held cells at the same coordinates". `held` separates a concatenation from an equally-shaped empty fabrication; `rsum`/`csum` separate it from one that keeps the cells but relocates them. |
| `self.rows`, `self.cols` (non-negative) | `Mat.rows`, `Mat.cols` with `Requires(... >= 0)` | identity on the integer dimension counts |
| `self.cols + other.cols`, `self.rows + other.rows` | int `+` | the joined dimension is the arithmetic sum of the two operands' counts |
| the retention predicate: a cell is stored iff its value TESTS TRUE (`if value:` / `if v:`, `sparse.py:62, 68, 79, 89, 1000, 1206`) | `Mat.held` counts exactly those cells | **Not** "unequal to zero". For a sympy object the two predicates SPLIT: `S.false`, `Eq(1, 2)`, `EmptySet()`, `FiniteSet()` all test false while comparing unequal to `0`. `held` is read through the PUBLIC element accessor (`sparse.py:104`), so a dense and a sparse operand are measured identically and `len(self._smat)` is a consequence for a canonically-built sparse matrix rather than the definition. Both probes MEASURE the split instead of assuming it: G-CONF found 40 operands on which the two readings differ and G-AX refutes the deep model 9 times under the rejected reading. |
| a cell whose truth value is INDETERMINATE (e.g. `x > 0`) | *not representable* | the domain boundary of the carrier, and it is a boundary the repo shares: `bool(x > 0)` raises `TypeError`, so such a matrix has no sparse image and the real callee refuses it instead of returning. `axiom_check.py::_check_domain_boundary` measures this on 4 probes (abstraction, sparse image, `row_join`, `col_join`). This is not a narrowing of the interesting domain: every matrix over which concatenation is defined at all is representable. |
| the `_smat` merge (`sparse.py:1206-1213` / `:1000-1007`): every `(i, j) -> v` of `B` re-keyed at column (row) offset into a copy of `A._smat`, subject to the same `if v:` filter | `held' = a.held + b.held`, `rsum' = a.rsum + b.rsum`, `csum' = a.csum + b.csum + a.cols * b.held` (transposed for `col_join`) | the merge is injective on held cells and drops none, and it displaces `B`'s cells along the concatenation axis ONLY, by exactly `A.cols` (resp. `A.rows`). Hence: counts add; the orthogonal index sum adds plainly; the axial index sum adds and picks up the offset once per held cell of `B`. Validated == the real callee over the operand grid crossed with **varied payloads** by G-AX / G-CONF (an all-zero grid alone would make all three facets vacuous). |
| a matrix with a zero dimension holds no cells | `Implies(rows == 0 or cols == 0, held == 0)` (a `Requires`) | a TRUE property of the modelled objects, not a domain restriction: a `0 x n` / `n x 0` matrix has no cells at all. |
| an empty cell population has empty index sums | `Implies(held == 0, rsum == 0 and csum == 0)` (a `Requires`) | likewise true of every matrix: a sum over no cells is 0. Both invariants are confirmed against the real objects by the axiom-containment probe, which also confirms every admissible `(shape, held, rsum, csum)` tuple is realisable by some real matrix — so no operand the real callee accepts is excluded by them. |
| `bool(self)` / `not self` (pre-patch only) | `self.rows * self.cols == 0` | `len = rows*cols`; falsy iff a dimension is zero. Reproduced verbatim in `model_prepatch.py`. |
| `ShapeError` raised | `ShapeMismatch` (user-defined) + `Exsures` | builtin / third-party exceptions crash Nagini's `Exsures` translation; a user-defined class is used (SPEC_GUIDE §2). |
| `type(self)(other)` (pre-patch) | `Mat(b.rows, b.cols, b.held, b.rsum, b.csum)` | `type(self)(other)` COPIES `other` (`sparse.py:44-47`), so it carries `other`'s shape *and* its held cells at their own coordinates. |
| `self._new(other.rows, 0, [])` / `self._new(0, other.cols, [])` (patched rebuild) | `Mat(b.rows, 0, 0, 0, 0)` / `Mat(0, b.cols, 0, 0, 0)` | an explicitly empty matrix of a zero-dimension shape (`[]` payload): no cells, so all three population facets are 0. It is the recursion's left operand, not the returned value. |

The individual element VALUES, and the `isinstance(B, SparseMatrix)`
dense-vs-sparse copy branch (`sparse.py:1206-1214`), are not modeled: they are
unchanged by the patch and run identically pre- and post-fix. What IS modeled
besides the shape is the merge's net effect on WHICH CELLS the result holds and
WHERE — because the F2P test asserts `a.row_join(b) == b` / `a.col_join(b) == b`
for a null `a` and a populated `b = MutableDenseMatrix([1, 2])`, and `__eq__`
reads the coordinate-keyed store. The two hunks change only the leading guard,
but that guard sits on the path where the result's content is decided: the
pre-patch `return type(self)(other)` and the patched
`self._new(...).row_join(other)` differ in shape, a shape-correct but
cell-dropping rebuild differs from both in content, and a shape- and
count-correct rebuild that relocates the cells differs from all three in
placement. Modeling `held` + `rsum` + `csum` is what lets the spec tell a
concatenation from a right-shaped fabrication.

## 3. Callee provenance (A-reference — checked by G-AX / `axiom_check.py`)

There are **no** `@ContractOnly` axioms in this bundle: the single opaque
sub-operation is the unchanged element merge, and its net effect on the five
facets is modeled DEEPLY as integer arithmetic. G-AX validates that deep model
== the real callee out of band.

### 3.1 The joined dimension (`a.cols + b.cols` / `a.rows + b.rows`)
**Callee:** the normal merge path of `SparseMatrix.row_join` / `col_join`, whose
net effect on the shape is `A.cols += B.cols` (`sparse.py:1212`, patched `:1216`)
resp. `A.rows += B.rows` (`sparse.py:1006`, patched `:1008`) — the UNCHANGED part
of the methods. Modeled deeply as integer addition. On every supported input the
real `row_join(a, b).shape == (a.rows, a.cols + b.cols)` and
`col_join(a, b).shape == (a.rows + b.rows, a.cols)` on the compatible /
degenerate-normalisation paths, and `ShapeError` is raised exactly on the
incompatible path.

### 3.2 The held-cell population and its placement
**Callee:** the same merge body, `sparse.py:1206-1213` (patched `:1210-1217`) for
`row_join` and `:1000-1007` (patched `:1002-1009`) for `col_join`. Each entry of
`B` is written into a copy of `A._smat` at key `(i, j + A.cols)` (resp.
`(i + A.rows, j)`), under the same `if v:` filter the constructor uses. Modeled
deeply as `held' = a.held + b.held`, `rsum' = a.rsum + b.rsum`,
`csum' = a.csum + b.csum + a.cols * b.held` (transposed for `col_join`).

G-AX checks all five facets against the real callees over the shape grid
`{0..3}^4` crossed with a payload catalogue of five value classes — including the
`falsy` class on which the two candidate retention predicates disagree — and with
`other` supplied both sparse and dense, plus placement-sensitive larger shapes,
folded non-degenerate `hstack`/`vstack` chains, the literal F2P chains, and the
literal F2P content case (`MutableSparseMatrix([])` joined with
`MutableDenseMatrix([1, 2])` must equal the latter, not an all-zero `2 x 1` and
not its cells relocated). It additionally MEASURES, rather than assumes, two
facts the mapping above rests on: that the catalogue reaches operands where
"tests true" and "unequal to zero" differ, and that under the rejected reading
the deep model is FALSE of the real callee. Recorded run: 5 212 operand
observations, 5 payload classes, 9 predicate splits, 9 refutations of the
rejected reading, 4 domain-boundary probes, exit 0.

### 3.3 The degenerate-normalisation rule (the patched guard)
**Repo behaviour (post-patch):** `row_join` — `if self.cols == 0 and
self.rows != other.rows: return self._new(other.rows, 0, []).row_join(other)`
(patched `:1196-1198`); `col_join` — `if self.rows == 0 and
self.cols != other.cols: return self._new(0, other.cols, []).col_join(other)`
(patched `:988-990`). This is the CHANGED operation; it is modeled **deeply** in
the impl region (the guard, the rebuilt frame, the self-call), not behind any
axiom. Because the frame has a zero shared dimension, the offset it contributes
in §3.2 is 0 — which is exactly why `other`'s cells come back at their own
coordinates and the F2P equality holds. G-AX and G-CONF both exercise this path
with populated operands.

## G-CONF (differential conformance: `conformance_check.py`)

**Shadow (direct).** The two `# impl-start` / `# impl-end` regions of `model.py`
are copied **byte-identically** into `conformance_check.py` (verified
line-for-line; only the surrounding `Requires`/`Ensures`/`Exsures` are absent,
and `Mat` / `ShapeMismatch` are the model's own declarations minus contracts).
No transliteration, no paraphrase, no restructuring. Branch coverage is recorded
by `sys.settrace` on the shadow rather than by editing the copied bodies. The
`axioms` and `pure` regions are empty (`model.py:87-96`), so there is no
`@ContractOnly` callee to bridge and no `@Pure` helper to copy — the impl region
is entirely executable, hence `conf_skip` is **false** and this gate carries full
weight.

**Oracle (called, not reimplemented).** The REAL patched
`sympy.matrices.sparse.SparseMatrix.row_join` (patched `sparse.py:1161`) and
`SparseMatrix.col_join` (`:949`) are invoked on real `SparseMatrix` / `Matrix`
instances in the instance image with the gold patch applied. `_assert_patched()`
inspects the loaded source for the patched guard and aborts rather than certify
against unpatched code.

**Type bridge (§2, inverted).** Down: `Mat(rows, cols, held, rsum, csum) ->` a
real `rows x cols` matrix carrying a payload drawn from one of five value classes
(and optionally a dense `Matrix` as `other`, which drives the real method's
`not isinstance(B, SparseMatrix)` copy branch). Up: the concrete result is
observed as `(rows, cols, held, rsum, csum)` with the population read through the
public element accessor under the repo's own truth test — so a dense and a sparse
operand are measured identically — and `ShapeMismatch` <-> `ShapeError`. The
abstraction is applied to the concrete OPERANDS too, so the shadow is handed the
same facets the oracle receives. Every generated input satisfies the
precondition (all five facets non-negative, plus the two carrier invariants) by
construction.

**Inputs — 108 006 Requires-satisfying observations, pinned seed `SEED = 13031`:**
* 5 100 **bridge probes**, which the run requires to be non-vacuous: the
  retention-predicate split measurement (40 operands where the two readings
  differ; the run FAILS if that number is 0), the indeterminate-truth domain
  boundary, and 5 000 observations of the same shadow against the
  general-purpose dense class's `row_join`/`col_join` over `{0..4}^4` x payload
  class (see §1: the run FAILS on a disagreement there, so the modelled
  behaviour is pinned as a property of concatenation rather than of one class);
* 520 boundary cases: empty, singleton, the exact F2P chain steps, the
  normalisation branch, the raise branch, the branch-overlap case
  (`a.cols == 0 and a.rows == b.rows`), placement-sensitive shapes where both
  operands hold cells and the offsets differ, plus operand-swapped variants —
  each also re-run with NON-EMPTY payloads from every value class on both
  operands (sparse and dense `other`), so the content and placement facets are
  compared where `held > 0` rather than only on all-zero operands, where they
  would be vacuous;
* **8 192 exhaustive** observations — the full shape grid `{0..7}^4` for both
  functions (4 096 operand pairs each), enumerating every degenerate zero-row /
  zero-column combination in that range;
* 86 188 seeded-fuzz observations over mixed magnitudes (up to 97), varied
  payload classes and mixed sparse/dense `other`, biased onto each of the three
  branches of each impl;
* 8 004 end-to-end `hstack` / `vstack` chains (the unchanged `reduce` over the
  binary join — the issue's actual symptom) diffed against the shadow folded over
  the same operand list, including the literal F2P chains, whose results are also
  compared for `==` against `Matrix(0, 6, [])` / `Matrix(6, 0, [])`, and
  including chains whose parts HOLD cells so the placement facets accumulate;
* the literal F2P CONTENT case: `MutableSparseMatrix([])` row-joined and
  col-joined with `MutableDenseMatrix([1, 2])`, compared against the shadow on
  all five facets and against `b` for `==`.

All six impl branches (normalise / raise / sum, per function) are traced and the
run **fails** if any was never taken, so a generator that dodged the patched
guard cannot report green.

**Negative controls (run out of band; the script must be able to fail).**
(a) Shadow mutated back to the pre-patch guard (`a.rows * a.cols == 0 ->
Mat(b.rows, b.cols, b.held, b.rsum, b.csum)`, i.e. `model_prepatch.py`'s logic):
**2 969 disagreements, exit 1**. (b) Oracle left unpatched: `_assert_patched()`
aborts instead of certifying. (c) Generator restricted to the
shared-dimension-agrees branch: the branch-coverage guard fires, **exit 1**.
(d) Shadow mutated to DISCARD the operands' cells on the normalisation path
(`-> Mat(b.rows, b.cols, 0, 0, 0)`, the shape-correct fabrication): **1 154
disagreements, exit 1**. (e) Bridge switched to the REJECTED "unequal to zero"
retention predicate: **509 disagreements, exit 1** — so the choice of predicate
is load-bearing, not cosmetic. (f) Shadow's column-offset term changed from
`a.cols * b.held` to `b.cols * a.held` (a placement mutation that preserves shape
and count): **1 994 disagreements, exit 1** — so the two index-sum facets are
load-bearing too. Controls (a) and (d) also patch the branch landmark in the
mutated copy, since deleting the landmark line would abort the run before it
could disagree.

**Recorded verdict:** exit 0, 0 disagreements over 108 006 observations.
