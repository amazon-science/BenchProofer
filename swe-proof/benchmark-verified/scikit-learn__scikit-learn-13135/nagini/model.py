"""Twin-artifact model for scikit-learn__scikit-learn-13135.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A feature column is summarised by a set of one-dimensional cluster centres
  (the representative value of each cluster). From those centres a list of bin
  boundaries is built: the interior boundaries are the midpoints of consecutive
  centres, and the boundary list is closed on the left by the column minimum and
  on the right by the column maximum. Each centre lies inside the column range,
  so the column minimum is no greater than any centre and the column maximum is
  no smaller than any centre.

  The boundary list is consumed by a downstream digitisation step that assigns
  each value to a bin by locating it among the boundaries; that step is only
  well defined when the boundaries are arranged in non-decreasing order. The
  representative centres are produced in no particular order, so the procedure
  must arrange them into non-decreasing order BEFORE forming the midpoints.
  Only then are the interior midpoints themselves non-decreasing and bracketed
  between the column minimum and the column maximum, making the whole boundary
  list non-decreasing — the property the downstream step requires for EVERY
  admissible input, never an out-of-order boundary list.

The centres, the column bounds and the boundaries are interpreted real numbers
(verified with `--float-encoding=real`), because the behaviour at stake is a
real-valued ordering relation among midpoints. The arrangement-into-order
operation is the unchanged numeric callee; it is axiomatized with the weakest
sufficient contract — its output is a non-decreasing rearrangement of the same
values that stays within the original bounds — and validated against the real
operation out-of-band by axiom_check.py (G-AX).

The behaviour is modelled on a specific, representative number of centres (four
centres, hence three interior midpoints). This is the smallest configuration in
which an out-of-order boundary list can arise (it needs at least two adjacent
interior midpoints to compare), and the boundary computation is uniform in the
number of centres, so the property generalises (mapping.md). Arranging the
centres into non-decreasing order before forming the midpoints is exactly what
makes the boundary list non-decreasing here.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def order4(a: float, b: float, c: float, d: float,
           lo: float, hi: float) -> PSeq[float]:
    """Arrange four real centres into non-decreasing order (the unchanged
    in-place ordering callee). Every centre lies in `[lo, hi]`; the ordering is a
    rearrangement, so the result has length four, every element stays within
    `[lo, hi]`, and the four elements are in non-decreasing order. The weakest
    contract the proof needs (length four, the `[lo, hi]` bound, and
    non-decreasing order). Provenance + executable soundness check:
    mapping.md / axiom_check.py.
    """
    Requires(lo <= a and a <= hi)
    Requires(lo <= b and b <= hi)
    Requires(lo <= c and c <= hi)
    Requires(lo <= d and d <= hi)
    Ensures(len(Result()) == 4)
    Ensures(lo <= Result()[0] and Result()[0] <= hi)
    Ensures(lo <= Result()[1] and Result()[1] <= hi)
    Ensures(lo <= Result()[2] and Result()[2] <= hi)
    Ensures(lo <= Result()[3] and Result()[3] <= hi)
    Ensures(Result()[0] <= Result()[1])
    Ensures(Result()[1] <= Result()[2])
    Ensures(Result()[2] <= Result()[3])
# axioms-end


# pure-start
@Pure
def non_decreasing(s: PSeq[float]) -> bool:
    """The boundary-ordering property the downstream digitisation requires:
    every boundary is no greater than its successor."""
    return Forall(int, lambda k: (Implies(0 <= k and k + 1 < len(s),
                                          s[k] <= s[k + 1]), [[s[k]]]))
# pure-end


def make_bin_edges(a: float, b: float, c: float, d: float,
                   col_min: float, col_max: float) -> List[float]:
    # pre-conditions-start
    # The column minimum is no greater than, and the column maximum no smaller
    # than, every centre (each centre lies in the column range).
    Requires(col_min <= col_max)
    Requires(col_min <= a and a <= col_max)
    Requires(col_min <= b and b <= col_max)
    Requires(col_min <= c and c <= col_max)
    Requires(col_min <= d and d <= col_max)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The boundary list has the column minimum first and the column maximum last,
    # with one interior midpoint per consecutive pair of centres in between
    # (four centres -> three interior midpoints -> five boundaries).
    Ensures(len(Result()) == 5)
    Ensures(Result()[0] == col_min)
    Ensures(Result()[4] == col_max)
    # Each interior boundary is exactly the midpoint of a consecutive pair of the
    # centres TAKEN IN NON-DECREASING ORDER (`ordered(...)[k]` is the k-th centre
    # once arranged in order): boundary k+1 is the average of ordered centres k
    # and k+1. This pins every interior boundary to the genuine ordered-midpoint
    # value, so it cannot be discharged by any other monotone interior value.
    Ensures(Result()[1] == (order4(a, b, c, d, col_min, col_max)[0] +
                            order4(a, b, c, d, col_min, col_max)[1]) / 2)
    Ensures(Result()[2] == (order4(a, b, c, d, col_min, col_max)[1] +
                            order4(a, b, c, d, col_min, col_max)[2]) / 2)
    Ensures(Result()[3] == (order4(a, b, c, d, col_min, col_max)[2] +
                            order4(a, b, c, d, col_min, col_max)[3]) / 2)
    # The boundary list is non-decreasing for EVERY admissible input — the
    # property the downstream digitisation step requires (it is ill defined on an
    # out-of-order boundary list).
    Ensures(non_decreasing(ToSeq(Result())))
    # post-conditions-end
    # impl-start
    # Arrange the centres into non-decreasing order BEFORE forming the midpoints.
    s = order4(a, b, c, d, col_min, col_max)
    m0 = (s[0] + s[1]) / 2
    m1 = (s[1] + s[2]) / 2
    m2 = (s[2] + s[3]) / 2
    result = [col_min, m0, m1, m2, col_max]  # type: List[float]
    # Each midpoint lies between its two ordered centres, so the midpoints are
    # non-decreasing and bracketed by the column bounds; the whole boundary list
    # is therefore non-decreasing.
    Assert(s[0] <= m0 and m0 <= s[1])
    Assert(s[1] <= m1 and m1 <= s[2])
    Assert(s[2] <= m2 and m2 <= s[3])
    Assert(col_min <= m0)
    Assert(m0 <= m1)
    Assert(m1 <= m2)
    Assert(m2 <= col_max)
    return result
    # impl-end
