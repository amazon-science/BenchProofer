"""Twin-artifact model for sympy__sympy-17655.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A point in n-dimensional space is described by its sequence of coordinate
  values.  Scaling a point by a numeric factor yields a NEW point whose i-th
  coordinate is the i-th coordinate of the original multiplied by the factor;
  the dimension (the number of coordinates) is preserved and the original
  point is left unchanged.

  The essential property: scaling is COMMUTATIVE between the point and the
  factor.  Multiplying the factor by the point on the left produces exactly the
  same scaled point as multiplying the point by the factor on the right -- for
  every coordinate, factor * coordinate.

A point is modelled as a `List[int]` of coordinate values (the tested
coordinates and factor are concrete integers); the scaling of a whole point is
carried in the specification by `PSeq[int]` via `ToSeq`, as the per-coordinate
multiplication `scaled` (a front-recursive fold giving one unfold per loop
step).  The factor is a read-only int; the input point is read-only and carries
fractional permission only.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no @ContractOnly axioms: the per-coordinate scaling is the changed operation
# and is modelled DEEPLY as integer multiplication -- see refinement.md
# A-reference rows; there is no opaque callee the proof consumes.)
# axioms-end


# pure-start
@Pure
def scaled(s: PSeq[int], factor: int) -> PSeq[int]:
    """The per-coordinate scaling of a whole point: every coordinate of ``s``
    multiplied by ``factor``, in order.  Front-recursive so a single unfold is
    available to callers per loop step."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(s[0] * factor) + scaled(s.drop(1), factor)
# pure-end


def mul_right(point: List[int], factor: int) -> List[int]:
    """Scale a point by a factor on the right (point * factor)."""
    # pre-conditions-start
    Requires(Acc(list_pred(point), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(point), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The dimension is preserved.
    Ensures(len(Result()) == len(point))
    # Every coordinate of the result is the corresponding coordinate scaled.
    Ensures(ToSeq(Result()) == scaled(ToSeq(point), factor))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(point)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(point), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(point))
        Invariant(len(result) == len(point) - i)
        Invariant(ToSeq(result) == scaled(ToSeq(point).drop(i), factor))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = point[i - 1]
        Assert(ToSeq(point).drop(i - 1)[0] == c)
        Assert(ToSeq(point).drop(i - 1).drop(1) == ToSeq(point).drop(i))
        result = [c * factor] + result
        i = i - 1
    Assert(ToSeq(point).drop(0) == ToSeq(point))
    return result
    # impl-end


def mul_left(factor: int, point: List[int]) -> List[int]:
    """Scale a point by a factor on the left (factor * point)."""
    # pre-conditions-start
    Requires(Acc(list_pred(point), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(point), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The dimension is preserved.
    Ensures(len(Result()) == len(point))
    # Left scaling reproduces the per-coordinate scaling exactly -- the same
    # scaled point that right scaling produces (commutativity of the factor and
    # the point).
    Ensures(ToSeq(Result()) == scaled(ToSeq(point), factor))
    # post-conditions-end
    # impl-start
    return mul_right(point, factor)
    # impl-end
