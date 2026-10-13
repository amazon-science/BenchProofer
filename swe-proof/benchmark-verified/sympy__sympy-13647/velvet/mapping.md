# mapping.md — sympy__sympy-13647

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 67e3c956083d0128a621f65ee86a7dacd4f9f19f`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `sympy/matrices/common.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `insertColumns (srows orows : List (List Int)) (pos : Nat)` | `MatrixShaping._eval_col_insert(self, pos, other)` — `sympy/matrices/common.py:81` (cell rule `entry`, body lines 84–89) | the modeled changed function (builds the new matrix cell-by-cell) |
| `spliceRow (srow orow : List Int) (pos : Nat)` | the per-cell rule `entry(i, j)` of `_eval_col_insert` restricted to a single row `i` (`common.py:84`) | pure spec: one result row |
| `spliceCols (srows orows : List (List Int)) (pos : Nat)` | `self._new(self.rows, self.cols + other.cols, lambda i, j: entry(i, j))` — `common.py:91` | pure spec: the whole result matrix as rows |

No axiomatized callees. `_new` is the matrix constructor: it materializes a
matrix from `(rows, cols, entry-fn)` by evaluating `entry(i, j)` over the grid.
Its only effect observable here is "result cell `(i, j)` = `entry(i, j)`",
which is captured directly by `spliceCols`/`spliceRow` (a deep, structural
model — there is no consumed axiom and no A-reference; see refinement.md §C).

The wrapper `col_insert(self, pos, other)` (`common.py:182`) clamps `pos` into
`[0, self.cols]` (lines 207–212) and raises `ShapeError` unless
`self.rows == other.rows` (lines 214–216) BEFORE calling `_eval_col_insert`.
So `_eval_col_insert` only ever runs on inputs with `pos ≤ self.cols` and equal
row counts — the modeled domain (see §2).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a matrix `M` (rows × cols of expressions) | `List (List Int)` (outer list = rows, inner list = one row's entries, left→right by column) | `M[i, j]` ↔ `rows[i][j]`; `M.rows` ↔ `rows.length`; `M.cols` ↔ `rows[i].length` (rectangular) |
| a matrix **entry** (a sympy `Expr`) | `Int` | entries are modeled as integers; the operation is purely positional (it copies entries unchanged, never inspects or computes on their values), so `Int` is a faithful and sufficient carrier — distinct integer values witness the cell-placement behaviour (`eye`/`ones` in the issue are integer matrices) |
| `pos` (insert column position, post-clamp) | `Nat` | identity; the wrapper guarantees `0 ≤ pos ≤ self.cols` |
| `self.cols + other.cols` (result width) | `(rows[i].length) + (orows[i].length)` per row | `take pos ++ orow ++ drop pos` has length `pos + oc + (c - pos) = c + oc` when `pos ≤ c` |

**Modeled domain (the inputs `_eval_col_insert` actually receives).** Both
matrices are rectangular; `srows.length = orows.length` (equal row counts,
enforced by the wrapper's `ShapeError`); each `other` row has the same width
`oc = other.cols`; each `self` row has the same width `c = self.cols`; and
`pos ≤ c` (the wrapper clamps it). Over this domain `spliceCols` equals the gold
`_eval_col_insert` cell-for-cell. G-CONF fuzzes only this domain.

## 3. Callee provenance

None. The change touches only positional index arithmetic inside the locally
defined `entry`; it calls no other repo function whose behaviour the proof must
assume. `_new` is modeled deeply (its grid-materialization IS `spliceCols`), not
axiomatized. Hence `axioms = []`, `deep_model_references = []`, and there is no
`axiom_check.py` (G-AX = skip — no axioms to validate). See refinement.md §C.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13647`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`spliceRow`/`spliceCols` (the `take pos ++ orow ++ drop pos` splice) to Python
over the real `Matrix` type and diffs against the patched
`Matrix.col_insert` (patch.diff applied at base_commit) on ≥10⁵ rectangular
random matrices with `pos` in range. There are no A-tagged callees, so the
shadow is pure R/I (`conf_skip = false`).
