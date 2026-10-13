"""Twin-artifact model for matplotlib__matplotlib-20676.

Behavioural contract (the desired observable, stated abstractly):

  A range selector carries a binary orientation. On construction it reports a
  pair of coordinate values, in order. The contract: that reported pair equals
  the two endpoints, in order, of the orientation's CURRENT coordinate range —
  the horizontal range for a horizontal selector, the vertical range for a
  vertical selector. Because the reported values are exactly the endpoints of
  the range that already exists, they lie inside it and constructing the
  selector leaves that range unchanged.

  In other words: result[0] is the lower endpoint and result[1] the upper
  endpoint of the orientation's current range, grounded in the range supplied
  for that orientation (never in any unrelated coordinate pair).

A coordinate value is a `float` in the real implementation; the modelled
behaviour is a pure selection / pass-through of coordinate VALUES (no arithmetic
on their magnitudes), so each coordinate is modelled as an `int` (the equalities
the contract pins are preserved under an injective encoding; see refinement.md /
mapping.md §2). Orientation is the two-valued discriminant `0` (horizontal) /
`1` (vertical).

The position-reporting component returns the coordinate values it was given,
unchanged. That UNCHANGED component is modelled as the identity
`reported_positions` and validated == the real component by axiom_check.py
(G-AX), not consumed as a load-bearing axiom. Which two coordinate values are
selected is modelled directly.

Region markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


HORIZONTAL = 0
VERTICAL = 1


# axioms-start
@Pure
@ContractOnly
def reported_positions(positions: PSeq[int]) -> PSeq[int]:
    """The position-reporting component returns the coordinate values it was
    constructed with, unchanged (one reported value per supplied coordinate).
    Provenance + executable soundness check: mapping.md §3.1 / axiom_check.py.
    Used inside an Ensures, hence @Pure."""
    Ensures(Result() == positions)
# axioms-end


# pure-start
@Pure
def selected_bound(direction: int, x_lo: int, x_hi: int,
                   y_lo: int, y_hi: int) -> PSeq[int]:
    """The two endpoints, in order, of the range for this orientation: the
    horizontal range for a horizontal selector, the vertical range for a
    vertical selector."""
    Requires(direction == HORIZONTAL or direction == VERTICAL)
    if direction == HORIZONTAL:
        return PSeq(x_lo, x_hi)
    return PSeq(y_lo, y_hi)
# pure-end


def selector_initial_coords(direction: int,
                            x_bound: Tuple[int, int],
                            y_bound: Tuple[int, int],
                            other_coords: Tuple[int, int]) -> List[int]:
    # pre-conditions-start
    Requires(direction == HORIZONTAL or direction == VERTICAL)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # Exactly two reported values, lower then upper.
    Ensures(len(Result()) == 2)
    # The reported pair is the two endpoints of THIS orientation's current
    # range, in order — the horizontal range for a horizontal selector, the
    # vertical range for a vertical selector. Grounded in the range supplied
    # for that orientation.
    Ensures(Implies(direction == HORIZONTAL,
                    Result()[0] == x_bound[0] and Result()[1] == x_bound[1]))
    Ensures(Implies(direction == VERTICAL,
                    Result()[0] == y_bound[0] and Result()[1] == y_bound[1]))
    # Equivalent fold form: the reported pair equals the position-reporting
    # component's report of the orientation's range endpoints (the unchanged
    # component applied to the selected range).
    Ensures(ToSeq(Result()) == reported_positions(
        selected_bound(direction, x_bound[0], x_bound[1],
                       y_bound[0], y_bound[1])))
    # post-conditions-end
    # impl-start
    # Select the two endpoints of THIS orientation's current range as the
    # reported coordinate values.
    if direction == HORIZONTAL:
        result = [x_bound[0], x_bound[1]]  # type: List[int]
    else:
        result = [y_bound[0], y_bound[1]]
    # The selected values equal the orientation's range, which the
    # position-reporting component then returns unchanged.
    Assert(ToSeq(result) == selected_bound(
        direction, x_bound[0], x_bound[1], y_bound[0], y_bound[1]))
    Assert(reported_positions(ToSeq(result)) == ToSeq(result))
    return result
    # impl-end
