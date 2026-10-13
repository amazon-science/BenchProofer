"""Twin-artifact model for sympy__sympy-22714.

Behaviour under specification (an abstract behavioural contract):

  A constructor screens a list of coordinates and rejects the list (returns
  True, i.e. takes the error branch) exactly when SOME coordinate satisfies a
  two-part condition: the coordinate belongs to a particular kind AND a
  per-coordinate verdict resolves to its NEGATIVE outcome. A coordinate whose
  verdict resolves to its POSITIVE outcome, or whose verdict is left UNDECIDED,
  never triggers the rejection on its own.

Each coordinate is abstracted by two facts the screen reads:

  * `coord_kind[i]` -- a classification of the i-th coordinate
    (1 = the kind the screen looks at, 0 = any other kind);
  * `coord_verdict[i]` -- a verdict for the i-th coordinate, an int in
    {-1, 0, 1}: 1 = positive outcome, 0 = negative outcome, -1 = undecided.

The screen rejects iff there is a coordinate of the looked-at kind whose
verdict is the negative outcome (`coord_verdict[i] == 0`). The positive
outcome (1) and the undecided verdict (-1) are both accepted.

A third, redundant fact `coord_extra[i]` (a 0/1 summary of the same
coordinate) is supplied to every implementation but the specification never
mentions it. It is present only so that every candidate implementation
type-checks against the same signature, whichever fact it chooses to read.

All facts are carried as `int`; the coordinate facts are modelled as
`List[int]` and the specification is carried by `PSeq[int]` via the
front-recursive fold `any_triggering` (one auto-unfold per loop step).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No opaque callees are consumed here: the screening predicate is modelled
#  directly as the fold `any_triggering` below.)
# axioms-end


# pure-start
@Pure
def coord_triggers(kind: int, verdict: int) -> bool:
    """A single coordinate triggers the rejection iff it is of the looked-at
    kind (kind == 1) AND its verdict is the negative outcome (verdict == 0).
    The positive outcome (1) and the undecided verdict (-1) do NOT trigger."""
    return kind == 1 and verdict == 0


@Pure
def any_triggering(kind: PSeq[int], verdict: PSeq[int]) -> bool:
    """Whether SOME coordinate triggers the rejection. Front-recursive over the
    head so one unfold is available per loop step. Total: an exhausted (empty)
    sequence contributes nothing."""
    if len(kind) == 0 or len(verdict) == 0:
        return False
    return (coord_triggers(kind[0], verdict[0])
            or any_triggering(kind.drop(1), verdict.drop(1)))
# pure-end


def screen_coordinates(coord_kind: List[int],
                       coord_verdict: List[int],
                       coord_extra: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(coord_kind), 1 / 2))
    Requires(Acc(list_pred(coord_verdict), 1 / 2))
    Requires(Acc(list_pred(coord_extra), 1 / 2))
    Requires(len(coord_kind) == len(coord_verdict))
    Requires(len(coord_kind) == len(coord_extra))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(coord_kind), 1 / 2))
    Ensures(Acc(list_pred(coord_verdict), 1 / 2))
    Ensures(Acc(list_pred(coord_extra), 1 / 2))
    # The screen rejects iff SOME coordinate is of the looked-at kind and its
    # verdict is the negative outcome. (The positive outcome and the undecided
    # verdict are accepted; the redundant extra fact is irrelevant to the
    # verdict.)
    Ensures(Result() == any_triggering(ToSeq(coord_kind),
                                       ToSeq(coord_verdict)))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy) skeleton: the screen keys off the redundant coarse
    # extra fact (coord_extra) instead of the verdict. A coordinate of the
    # looked-at kind whose extra fact is 1 (yet whose verdict is the positive
    # outcome) is wrongly rejected. This MUST fail G-VERIFY.
    rejected = False
    i = len(coord_kind)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(coord_kind), 1 / 2))
        Invariant(Acc(list_pred(coord_verdict), 1 / 2))
        Invariant(Acc(list_pred(coord_extra), 1 / 2))
        Invariant(0 <= i and i <= len(coord_kind))
        Invariant(len(coord_kind) == len(coord_verdict))
        Invariant(len(coord_kind) == len(coord_extra))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        if coord_kind[i - 1] == 1 and coord_extra[i - 1] == 1:
            rejected = True
        i = i - 1
    return rejected
    # impl-end
