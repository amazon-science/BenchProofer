# refinement.md — sympy__sympy-13647

The operation-by-operation correspondence between `model.py`'s implementation
(the `insert_row` impl region, the deep `output_value` banding, and the
`new_matrix_cell` axiom) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — **A-consumed** where the
proof uses the axiom's `Ensures`, **A-reference** where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed site — `_eval_col_insert.entry` (`sympy/matrices/common.py:82-88`)

Gold hunk (inside the nested `entry(i, j)` of `_eval_col_insert`):
```
             if j < pos:
                 return self[i, j]
             elif pos <= j < pos + other.cols:
                 return other[i, j - pos]
-            return self[i, j - pos - other.cols]
+            return self[i, j - other.cols]
```
`_eval_col_insert` then assembles the result with
`self._new(self.rows, self.cols + other.cols, lambda i, j: entry(i, j))`.

Because `entry(i, j)` depends on the row `i` only through `self[i, ...]` /
`other[i, ...]` and never moves an entry between rows, the whole content of the
change is a per-row, per-column banding function. The model fixes one row:
`insert_row(self_row, other_row, cols, other_cols, pos)` builds one output row of
width `cols + other_cols`; the column index `j` is exactly `entry`'s `j`.

| # | model.py impl op (`insert_row`) | patch.diff op (`entry`) | tag | justification |
|---|---|---|---|---|
| A1 | params `self_row: List[int]` (len `cols`), `other_row: List[int]` (len `other_cols`) | `self` (a row of `self.cols`), `other` (a row of `other.cols`), at a fixed row `i` | R | a matrix row ↔ `List[int]`; `self[i, c]` ↔ `self_row[c]`, `other[i, c]` ↔ `other_row[c]`; `self.cols` ↔ `cols`, `other.cols` ↔ `other_cols` (mapping.md §2). `i` is fixed; the operation is row-independent, so one row captures the full behaviour. |
| A2 | `width = cols + other_cols`; loop `j` over `0..width` | `self._new(self.rows, self.cols + other.cols, ...)` shape; `entry` evaluated at each `(i, j)` | R + A-consumed | the output width `self.cols + other.cols` ↔ `width`; `_new` materialises the entry function value-preservingly (`new_matrix_cell` axiom, §B). The per-row loop ↔ `_new` populating one row. |
| A3 | `if j < pos: v = self_row[j]` | `if j < pos: return self[i, j]` | I | identical band: the first `pos` original entries, same index `j`. |
| A4 | `elif j < pos + other_cols: v = other_row[j - pos]` | `elif pos <= j < pos + other.cols: return other[i, j - pos]` | I (under R for the carrier) | identical band: the inserted block, offset `j - pos`. |
| A5 | `else: v = self_row[j - other_cols]` | `return self[i, j - other.cols]` | I (under R) | **the discriminating step**: the trailing original entry is read at index `j - other_cols` (shift left by exactly the inserted width). This is the corrected formula; the pre-patch `j - pos - other.cols` (additionally subtracting `pos`) is what `model_prepatch.py` reproduces and what fails the spec. |
| A6 | `result = result + [new_matrix_cell(v)]` | the value `entry(i, j)` is stored at `(i, j)` by `_new` | A-consumed | `new_matrix_cell(v) == v` (the constructor does not alter the value); the model's `result[j]` ↔ the real `M[i, j]` (§B). |

The behavioural specification of one output entry is `output_value` (model.py
`pure` region): left band → original index `j`; middle band → block index
`j - pos`; right band → original index `j - other_cols`. The postcondition pins
every `Result()[j] == output_value(...)`. `output_value` is a **deep model**
of the corrected `entry` banding — it is validated `== the real (patched)
_eval_col_insert` by axiom_check.py (G-AX), i.e. it is an **A-reference**, not a
consumed axiom (there is no `@ContractOnly` for the changed `entry`).

## B. The unchanged constructor — `self._new` (`MatrixRequired._new`)

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `new_matrix_cell(value)` axiom: `Ensures(Result() == value)` | `self._new(rows, ncols, lambda i, j: entry(i, j))` then read `M[i, j]` | A-consumed | `_new` is NOT changed by the patch; it materialises the entry function into storage value-preservingly. The axiom is the weakest sufficient property — the stored cell equals the entry value — and the proof consumes it to conclude `result[j] == output_value(...,j)` (A6). G-AX runs the real `_MinimalMatrix._new`/`__getitem__` and asserts `_new(r,c,f)[i,j] == f(i,j)` over boundary + fuzz. |

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The one operation that genuinely *changed* — the
right-band index of `entry` — is modeled **deeply** (the spelled-out
`output_value` banding consumed in `insert_row`, step A5, an **A-reference**
validated against the real patched callee by G-AX), not hidden behind an axiom
about the function under change. The only **consumed** axiom, `new_matrix_cell`
(**A-consumed**, §B), covers the **unchanged** constructor `_new` the new code
invokes; the changed `entry` appears only as the deep model + the **A-reference**
that G-AX validates.

## D. verify(model) ⇒ resolved

`insert_row` verifies only if every output entry equals the banded source value
with the right band reading original index `j - other_cols` (A5). By R (matrix
row ↔ `List[int]`, `self.cols`/`other.cols` ↔ `cols`/`other_cols`) and the
row-independence of `entry`, the verified row builder equals the real per-row
behaviour of `_new(..., lambda i, j: entry(i, j))` for the corrected `entry`.
By G-AX the deep model `output_value` equals the real patched `_eval_col_insert`
cell by cell (A-reference) and the real `_new` meets the `new_matrix_cell` axiom
it stands in for (A-consumed). Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement and the audited
constructor — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity
(this document, G-EQ).

The single fixed behaviour (the right-band column index) yields one
`model_prepatch.py`: its right band uses `self_row[j - pos - other_cols]` (the
pre-patch formula), which fails the loop invariant / postcondition
`result[j] == output_value(...,j)` exactly when `pos > 0` and there is a
right band — precisely the issue's `eye(6).col_insert(3, V)` case (G-DIFF).
