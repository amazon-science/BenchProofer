# refinement.md — sympy__sympy-13647

Operation correspondence between `implementation_colInsert` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

No axioms are declared or consumed: the modeled function is an integer-valued
entry accessor whose every branch is a direct read of an input accessor at an
index computed from the inputs. Every row is **R** or **I**. The R/I legs are
differential-tested by G-CONF; G-AX is a skip stub (no consumed callee axiom).

## `implementation_colInsert` ↔ the `entry` accessor of `_eval_col_insert`

The gold patch changes the inner accessor's final `return` from
`self[i, j - pos - other.cols]` to `self[i, j - other.cols]`; the two preceding
branches are unchanged.

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| `if j < pos then return self.get i j` | `if j < pos: return self[i, j]` | I | left-of-insertion region; identical guard + read |
| `if pos ≤ j ∧ j < pos + other.cols then return other.get i (j - pos)` | `elif pos <= j < pos + other.cols: return other[i, j - pos]` | I | inserted-block region; identical guard + read (`j - pos` ≥ 0 under the guard, `Nat` sub matches) |
| `return self.get i (j - other.cols)` | `return self[i, j - other.cols]` | R | right-of-block region (the patched line). `self[i, k]` ↦ `self.get i k : Int`; the column index `j - other.cols` is exact under the implicit guard `pos + other.cols ≤ j` (reached only when both earlier guards fail), so truncating `Nat` subtraction equals integer subtraction. |

The result is the precise observable the F2P test pins: `col_insert(pos, other)[i, j]`.

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the right-of-block region reads
  `self.get i (j - pos - other.cols)` (the pre-patch buggy index), so for any
  `pos > 0` and any `j ≥ pos + other.cols` the produced entry comes from the
  wrong source column. The carried gold proof of `correct_colInsert` fails to
  close on `refine_3` (the `pos + other.cols ≤ j` case):
  `self.get i (j - pos - other.cols)` is not definitionally equal to
  `self.get i (j - other.cols)`. (FAIL_TO_PASS: `test_col_insert`, issue 13643
  assertion.)
