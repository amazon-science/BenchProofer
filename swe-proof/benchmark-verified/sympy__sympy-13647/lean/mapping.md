# mapping.md — sympy__sympy-13647

## Instance
- repo: sympy/sympy
- base_commit: 67e3c956083d0128a621f65ee86a7dacd4f9f19f
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change (one behavior, one site)
`Matrix.col_insert(pos, other)` builds a new matrix with `self.cols + other.cols`
columns by inserting the columns of `other` at column index `pos`. The new
matrix's entry function partitions the column index `j` into three regions:

```python
def _eval_col_insert(self, pos, other):              # sympy/matrices/common.py:79
    cols = self.cols
    def entry(i, j):
        if j < pos:
            return self[i, j]                         # left of insertion point
        elif pos <= j < pos + other.cols:
            return other[i, j - pos]                  # inside inserted block
        return self[i, j - pos - other.cols]          # PRE-PATCH (buggy)
        # return self[i, j - other.cols]              # POST-PATCH (gold)
    return self._new(self.rows, self.cols + other.cols,
                     lambda i, j: entry(i, j))
```

The bug is in the third (right-of-block) region only. A column `j` to the right
of the inserted block held, in the original `self`, the column `j - other.cols`
(it has been pushed right by the `other.cols` newly inserted columns). The buggy
code subtracted `pos + other.cols`, which over-shifts by `pos` and therefore
reads the wrong source column (manifesting as the identity block being lifted to
the top rows in the issue's example). The gold patch corrects the shift to
`j - other.cols`.

## Modeled function — `_eval_col_insert` (its `entry` accessor)
| field | value |
|---|---|
| file @ base_commit | `sympy/matrices/common.py` |
| function | `MatrixShaping._eval_col_insert` (def at line 79; the patched line is the inner `entry`'s final `return` at line 89) |
| role | sole modeled function; the patched index arithmetic is the whole fix |

The observable the F2P test (`test_col_insert`, issue 13643 assertion) pins is the
value of `M.col_insert(pos, other)[i, j]` at every `(i, j)`. The Lean
`implementation_colInsert self other pos i j` models exactly this per-entry
accessor.

## Lean ↔ Python type bijection (G-CONF / G-AX use this)
A matrix is modelled by the Lean structure `Mat`:

| Lean | Python | note |
|---|---|---|
| `Mat.rows : Nat` | `self.rows` | row count |
| `Mat.cols : Nat` | `self.cols` | column count |
| `Mat.get i j : Int` | `self[i, j]` | entry accessor; integer entries in the test |
| `implementation_colInsert self other pos i j` | `self.col_insert(pos, other)[i, j]` | the produced entry |
| `pos : Nat` | the `pos` argument of `col_insert` | insertion column |
| `other.cols` | `other.cols` | width of the inserted block |

The entries in the F2P test are exact integers (identity/constant matrices), so
`Int` is an exact bijection — no floating point. G-CONF compares the real patched
`col_insert(pos, other)[i, j]` against the Lean skeleton's shadow over every
`(i, j)` for a large fuzzed catalogue of `(self, other, pos)`.

## Callee provenance / flag deps
- `self[i, j]` / `other[i, j]` are the **unchanged** entry accessors of the input
  matrices, modeled directly as the `Mat.get` field reads (an **I**/**R** op).
  They are not separately-defined callees the patch changes, so they are NOT
  axiomatized.
- The column-index arithmetic (`j - pos - other.cols` → `j - other.cols`) is the
  **changed** op, modeled directly in Lean as `self.get i (j - other.cols)` (an
  **R** op — `Nat` subtraction is total/truncating, matching the region guard
  `pos + other.cols ≤ j` under which it executes, so no underflow occurs). No
  `opaque`/`axiom` callee contract is needed anywhere in the bundle.
- No flag dependency.

## G-CONF fuzz seed
Pinned seed: **13647** (used in `conformance_check.py`).
