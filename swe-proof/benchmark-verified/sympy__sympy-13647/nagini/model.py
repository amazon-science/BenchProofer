"""Twin-artifact model for sympy__sympy-13647.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Inserting a block of columns into a matrix at a column position `pos`
  produces a wider matrix. Because the operation treats every row identically
  and never moves a value between rows, the behaviour is captured row by row:
  one original row of width `cols` and one inserted-block row of width
  `other_cols` combine into one output row of width `cols + other_cols`.

  For an output column index `j`:
    - if `j < pos`, the output value equals the original value at index `j`;
    - if `pos <= j < pos + other_cols`, the output value equals the block value
      at index `j - pos`;
    - otherwise, the output value equals the original value at index
      `j - other_cols`.

Rows are modelled as `List[int]` (Nagini has no matrix type; the per-row
behaviour is the whole content of the operation). The specification is carried
by `PSeq[int]` via `ToSeq`. The unchanged matrix constructor that materialises
a per-position value function into storage is the single axiomatized callee
(`new_matrix_cell`), value-preserving cell by cell; its soundness is checked
out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def new_matrix_cell(value: int) -> int:
    """The unchanged matrix constructor materialises a per-position value
    function into storage WITHOUT altering any value: the stored cell equals
    the value computed for that position. Modelled here at the level of a single
    cell (the constructor is value-preserving).
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Result() == value)
# axioms-end


# pure-start
@Pure
def output_value(self_row: List[int], other_row: List[int],
                 cols: int, other_cols: int, pos: int, j: int) -> int:
    """Value at output index j of one inserted row, banded by output index j:
      j < pos                  -> original value j
      pos <= j < pos+other_cols-> block value j - pos
      otherwise                -> original value j - other_cols
    This is the behavioural specification of one output position; the impl must
    reproduce it for every position of the row."""
    Requires(Acc(list_pred(self_row), 1 / 4))
    Requires(Acc(list_pred(other_row), 1 / 4))
    Requires(cols >= 0 and other_cols >= 0)
    Requires(0 <= pos and pos <= cols)
    Requires(len(self_row) == cols and len(other_row) == other_cols)
    Requires(0 <= j and j < cols + other_cols)
    if j < pos:
        return self_row[j]
    if j < pos + other_cols:
        return other_row[j - pos]
    return self_row[j - other_cols]
# pure-end


def insert_row(self_row: List[int], other_row: List[int],
               cols: int, other_cols: int, pos: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(self_row), 1 / 2))
    Requires(Acc(list_pred(other_row), 1 / 2))
    Requires(cols >= 0 and other_cols >= 0)
    Requires(0 <= pos and pos <= cols)
    Requires(len(self_row) == cols and len(other_row) == other_cols)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(self_row), 1 / 2))
    Ensures(Acc(list_pred(other_row), 1 / 2))
    Ensures(len(self_row) == cols and len(other_row) == other_cols)
    Ensures(Acc(list_pred(Result())))
    # The output row has the combined width.
    Ensures(len(Result()) == cols + other_cols)
    # Every output position equals its banded source value.
    Ensures(Forall(int, lambda j: (
        Implies(0 <= j and j < cols + other_cols,
                Result()[j] == output_value(
                    self_row, other_row, cols, other_cols, pos, j)),
        [[Result()[j]]])))
    # post-conditions-end
    # impl-start
    width = cols + other_cols
    result = []  # type: List[int]
    j = 0
    while j < width:
        # invariants-start
        Invariant(Acc(list_pred(self_row), 1 / 2))
        Invariant(Acc(list_pred(other_row), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(cols >= 0 and other_cols >= 0)
        Invariant(0 <= pos and pos <= cols)
        Invariant(width == cols + other_cols)
        Invariant(len(self_row) == cols and len(other_row) == other_cols)
        Invariant(0 <= j and j <= width)
        Invariant(len(result) == j)
        Invariant(Forall(int, lambda b: (
            Implies(0 <= b and b < j,
                    result[b] == output_value(
                        self_row, other_row, cols, other_cols, pos, b)),
            [[result[b]]])))
        Invariant(MustTerminate(width - j + 1))
        # invariants-end
        if j < pos:
            v = self_row[j]
        elif j < pos + other_cols:
            v = other_row[j - pos]
        else:
            v = self_row[j - other_cols]
        # v is exactly the banded source value for output index j.
        Assert(v == output_value(self_row, other_row, cols, other_cols,
                                   pos, j))
        old_result = result
        result = result + [new_matrix_cell(v)]
        # the append preserves every prior element and places v at index j.
        Assert(len(result) == j + 1)
        Assert(Forall(int, lambda b: (
            Implies(0 <= b and b < j, result[b] == old_result[b]),
            [[result[b]]])))
        Assert(result[j] == new_matrix_cell(v))
        Assert(result[j] == output_value(self_row, other_row, cols,
                                            other_cols, pos, j))
        j = j + 1
    return result
    # impl-end
