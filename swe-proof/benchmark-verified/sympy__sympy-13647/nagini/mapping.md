# mapping.md — sympy__sympy-13647

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 67e3c956083d0128a621f65ee86a7dacd4f9f19f`, states the type
abstraction, and gives the provenance of the one axiomatized callee.

Repo file under change: `sympy/matrices/common.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `insert_row(self_row, other_row, cols, other_cols, pos)` | `MatrixShaping._eval_col_insert(self, pos, other)` — `sympy/matrices/common.py:79` (the nested `entry(i, j)` at lines 82-88; result assembled by `self._new(...)` at line 90) | the modeled changed function: build one output row of the column-insertion result |
| `output_value(self_row, other_row, cols, other_cols, pos, j)` *(pure — A-reference)* | the nested `entry(i, j)` — `sympy/matrices/common.py:82-88` | pure behavioural spec: value of output cell at column `j` of one row; the deep model of the (patched) banding |
| `new_matrix_cell(value)` *(axiom — A-consumed)* | `self._new(self.rows, self.cols + other.cols, lambda i, j: entry(i, j))` then `M[i, j]` — `MatrixRequired._new` called at `sympy/matrices/common.py:90`; `_MinimalMatrix.__getitem__` | unchanged callee: materialises the per-position entry value into storage value-preservingly, at the granularity of a single cell |

The public entry point `MatrixShaping.col_insert(self, pos, other)`
(`sympy/matrices/common.py:182`) is NOT changed by the patch. It clamps `pos`
into `[0, self.cols]` (negative `pos` wraps; `pos > cols` is capped), raises
`ShapeError` if `self.rows != other.rows`, and then delegates to the changed
`_eval_col_insert(pos, other)`. The model takes the already-validated,
already-clamped state as its precondition (`0 <= pos <= cols`,
`rows == other.rows`), exactly the state `_eval_col_insert` receives.

## 2. Type abstraction (R-refinements)

The change to `entry(i, j)` reads `self[i, ·]` / `other[i, ·]` and never moves a
value between rows, so it is row-independent: one output row captures the entire
behaviour. The model therefore abstracts a single row as a `List[int]` (a 1-D
carrier with linear index reasoning), rather than the full matrix. A row-major
flat `List[int]` over the whole matrix was attempted and abandoned: it produces
nonlinear `i*cols + j` index arithmetic that crashes the prover (see
meta.json `type_modeling`); the row-independence justification makes the 1-D
abstraction faithful to the full operation.

| repo reality | model carrier | bijection |
|---|---|---|
| a row of the `rows × cols` matrix `self`, at fixed `i` | `List[int]` `self_row` of length `cols` | `self[i, c]` ↔ `self_row[c]` (entries abstracted to `int`; the F2P test uses integer matrices `eye(6)` and a 6×2 block of `2`s) |
| a row of the `rows × other_cols` block `other`, at fixed `i` | `List[int]` `other_row` of length `other_cols` | `other[i, c]` ↔ `other_row[c]` |
| `self.cols` / `other.cols` | `int` parameters `cols` / `other_cols` | direct |
| the insertion position `pos` (post-clamp) | `int` parameter `pos`, `0 <= pos <= cols` | direct |
| one row of the `rows × (cols+other_cols)` result | `List[int]` `Result()` of length `cols + other_cols` | result `[i, j]` ↔ `Result()[j]` at the fixed row `i` |
| the value of output cell `(i, j)`, i.e. `entry(i, j)` | the `output_value(...)` pure function (A-reference) | `entry(i, j)` ↔ `output_value(self_row, other_row, cols, other_cols, pos, j)`, cell by cell |
| `self._new(self.rows, self.cols + other.cols, lambda i, j: entry(i, j))` then read `M[i, j]` | the `new_matrix_cell(value)` axiom (A-consumed) | `_new` only materialises the entry value into storage; it does not alter any entry value — `M[i, j]` ↔ `new_matrix_cell(entry(i,j)) == entry(i,j)` (mapping §3) |

Matrix entries are SymPy expressions in general; the F2P test (`test_col_insert`,
issue 13643) compares **integer** matrices, so abstracting entries to `int` is
faithful for the tested behavior. The index arithmetic that the patch changes is
entirely over `int` row/column indices and is independent of the entry domain.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `new_matrix_cell` ↔ `MatrixRequired._new` (A-consumed)
**Callee:** `self._new(rows, ncols, entry)` builds a new matrix of the given shape
whose element `(i, j)` equals `entry(i, j)`. For `_MinimalMatrix` (the test's base,
`ShapingOnlyMatrix`) `_new` stores the flattened entries row-major and
`__getitem__((i, j))` returns `mat[i*cols + j]`. The patch does NOT change `_new`;
it changes only the `entry` function passed to it. The axiom encodes the
**weakest** sufficient property at the granularity the model needs: the stored cell
equals the value the per-position entry function returned for that position
(`Ensures(Result() == value)`) — i.e. `_new` is a faithful materialization,
value-preserving cell by cell. In the model this is the single-cell identity
`result[j] == new_matrix_cell(output_value(..., j)) == output_value(..., j)`, so
the axiom is consumed to conclude `result[j] == output_value(..., j)`.

**Soundness check (G-AX):** `axiom_check.py` constructs `_MinimalMatrix`-style
matrices via the same `_new`/`__getitem__` mechanism the repo uses and asserts
that `_new(rows, cols, f)[i, j] == f(i, j)` for every cell over boundary shapes
plus randomized fuzz, confirming `_new` is the value-preserving materialization
the model assumes. Exit 0 iff sound. Imports only `sympy.matrices.common` (the
very module under change) and stdlib.

### 3.2 `output_value` ↔ the patched `entry(i, j)` (A-reference — NOT a consumed axiom)
**Reference:** `output_value` is a deep pure model of the corrected per-cell
banding of `_eval_col_insert.entry` (post-patch): `j < pos -> self_row[j]`;
`pos <= j < pos + other_cols -> other_row[j - pos]`; otherwise
`-> self_row[j - other_cols]`. There is NO `@ContractOnly` axiom for the changed
`entry` — the proof does not consume an axiom about the function under change;
instead `output_value` is spelled out and the postcondition pins
`Result()[j] == output_value(..., j)` for every `j`. This deep model is
**validated against the real callee** by G-AX, not trusted.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL patched
`MatrixShaping._eval_col_insert` and asserts `output_value` equals it cell by cell
over the issue's exact example (`eye(6).col_insert(3, 6×2 block)`) + boundary
shapes + randomized fuzz column-insertions. It additionally checks that the
pre-patch right-band formula (`j - pos - other_cols`) is detectably wrong wherever
a right band exists with `pos > 0`, confirming the spec discriminates the bug.
