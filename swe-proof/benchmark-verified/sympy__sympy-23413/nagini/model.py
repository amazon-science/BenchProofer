"""Twin-artifact model for sympy__sympy-23413.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An integer matrix is reduced column-by-column from the bottom row upward.
  A running marker `k` records the leftmost column in which a pivot has so far
  been placed; it starts at the column count `n` (no pivots yet placed). Every
  row of the matrix is given the opportunity to contribute one pivot: a row that
  yields a nonzero pivot consumes the next free column (the marker moves one
  column to the left), while a row that yields only zeros consumes no column
  (the marker is unchanged). The search stops as soon as the marker reaches the
  leftmost column 0, because once every column already holds a pivot no further
  pivots are possible and no further rows need be examined.

  The reduced matrix retained at the end consists of the columns from the marker
  position to the right edge, so the number of retained columns equals the
  number of rows that contributed a pivot, capped by the column count. Crucially,
  EVERY row participates in this search -- a row near the top of a tall matrix
  must be able to contribute its pivot just as a row near the bottom can; the
  count of retained columns must never undercount the pivots merely because of a
  row's position.

The matrix is abstracted to its per-row pivot outcomes: `found` is a `List[int]`
with one 0/1 flag per row, given in the bottom-to-top processing order, and `n`
is the column count. The modelled function returns the final marker `k`; the
retained column count is `n - k`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No @ContractOnly axioms: the changed behaviour is modelled DEEPLY by the
#  pure helpers below and the verified loop, validated against the real routine
#  out-of-band by axiom_check.py / G-AX. There is no opaque unchanged callee.)
# axioms-end


# pure-start
@Pure
def valid_flags(s: PSeq[int]) -> bool:
    """Every entry of `s` is a 0/1 pivot-outcome flag."""
    return Forall(int, lambda t: (Implies(0 <= t and t < len(s),
                                          s[t] == 0 or s[t] == 1),
                                  [[s[t]]]))


@Pure
def pivot_count(s: PSeq[int], upto: int) -> int:
    """Number of pivot-yielding rows among the first `upto` rows of the
    bottom-to-top sequence `s` (each entry 0 or 1). Front-recursive on the
    suffix so a single unfold is available per loop step."""
    Requires(0 <= upto and upto <= len(s))
    Requires(valid_flags(s))
    Ensures(0 <= Result() and Result() <= upto)
    if upto == 0:
        return 0
    return s[upto - 1] + pivot_count(s, upto - 1)


@Pure
def pivot_count_monotone(s: PSeq[int], a: int, b: int) -> bool:
    """Lemma: pivot_count is non-decreasing in its bound (a <= b)."""
    Requires(valid_flags(s))
    Requires(0 <= a and a <= b and b <= len(s))
    Ensures(Result())
    Ensures(pivot_count(s, a) <= pivot_count(s, b))
    if a == b:
        return True
    return pivot_count_monotone(s, a, b - 1)
# pure-end


def leftmost_pivot_column(found: List[int], n: int) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(found), 1 / 2))
    Requires(n >= 0)
    # `found` is a per-row pivot-outcome flag (0 or 1), bottom-to-top.
    Requires(valid_flags(ToSeq(found)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(found), 1 / 2))
    # The pivot-outcome flags are unchanged (read-only input).
    Ensures(valid_flags(ToSeq(found)))
    # The marker stays a valid column index.
    Ensures(0 <= Result() and Result() <= n)
    # The marker equals the column count minus the number of pivots contributed
    # by EVERY row, floored at column 0. No row's pivot is missed because of its
    # position: all len(found) rows are counted (max(0, n - total pivots)).
    Ensures(Implies(pivot_count(ToSeq(found), len(found)) <= n,
                    Result() == n - pivot_count(ToSeq(found), len(found))))
    Ensures(Implies(pivot_count(ToSeq(found), len(found)) > n, Result() == 0))
    # post-conditions-end
    # impl-start
    k = n
    i = 0
    while i < len(found):
        # invariants-start
        Invariant(Acc(list_pred(found), 1 / 2))
        Invariant(0 <= i and i <= len(found))
        Invariant(0 <= k and k <= n)
        Invariant(valid_flags(ToSeq(found)))
        # k = max(0, n - pivots among the first i rows)
        Invariant(Implies(pivot_count(ToSeq(found), i) <= n,
                          k == n - pivot_count(ToSeq(found), i)))
        Invariant(Implies(pivot_count(ToSeq(found), i) > n, k == 0))
        # invariants-end
        if k == 0:
            # Every column already holds a pivot; no further rows can help.
            # pivot_count is monotone, so the full count is still >= n.
            Assert(pivot_count_monotone(ToSeq(found), i, len(found)))
            break
        c = found[i]
        Assert(ToSeq(found)[i] == c)
        Assert(pivot_count(ToSeq(found), i + 1)
               == ToSeq(found)[(i + 1) - 1] + pivot_count(ToSeq(found), (i + 1) - 1))
        if c == 1:
            k = k - 1
        i = i + 1
    return k
    # impl-end
