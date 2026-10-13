"""Twin-artifact model for matplotlib__matplotlib-24570.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A row of boxes, each described by a ``(height, descent)`` pair, is positioned
  inside a track of a given total ``height`` according to an alignment anchor.
  The function returns, for every box, the offset of its lower edge inside the
  track. The six anchors are:

    * BASELINE  — every box keeps offset 0 (the boxes share a common baseline).
    * LOWER / SIDE_A — the box is flush with the low edge of the track:
      its offset is exactly its own descent.
    * UPPER / SIDE_B — the box is flush with the high edge of the track:
      its offset is the slack above it (``height - height_of_box``) plus its
      own descent, so a shorter box is pushed all the way to the far edge.
    * CENTER — the box is centred: its offset is half the slack
      (``(height - height_of_box) / 2``) plus its own descent.

  The defining contrast the contract pins: under LOWER a box's offset is
  independent of the track height and equals its descent, whereas under UPPER a
  box's offset grows with the track's excess height over that box. The two are
  distinct whenever a box is shorter than the track.

Heights, descents and offsets are integers scaled by a factor of two so that
the centre anchor's halving is exact in integer arithmetic (a uniform positive
scaling that preserves every positional relationship the alignment expresses;
see refinement.md). There are no axiomatized callees — the operation under
specification is the offset arithmetic itself, modelled deeply per anchor.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axiomatized callees: the changed operation is the offset arithmetic,
#  modelled deeply below; there is no unchanged opaque callee to axiomatize)
# axioms-end


# pure-start
@Pure
def CODE_BASELINE() -> int:
    return 0


@Pure
def CODE_LOWER() -> int:
    # the "flush with the low edge" anchor group (two synonymous anchor names)
    return 1


@Pure
def CODE_UPPER() -> int:
    # the "flush with the high edge" anchor group (two synonymous anchor names)
    return 2


@Pure
def CODE_CENTER() -> int:
    return 3


@Pure
def offset_for(h: int, d: int, total: int, code: int) -> int:
    """The (twice-scaled) lower-edge offset of one box of height ``h`` and
    descent ``d`` inside a track of total height ``total`` under anchor
    ``code``. Pins each anchor's placement arithmetic."""
    if code == CODE_BASELINE():
        return 0
    if code == CODE_LOWER():
        return 2 * d
    if code == CODE_UPPER():
        return 2 * (total - h) + 2 * d
    # CODE_CENTER
    return (total - h) + 2 * d
# pure-end


def aligned_offsets(heights: List[int], descents: List[int],
                    total: int, code: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(heights), 1 / 2))
    Requires(Acc(list_pred(descents), 1 / 2))
    Requires(len(heights) == len(descents))
    Requires(code == CODE_BASELINE() or code == CODE_LOWER()
             or code == CODE_UPPER() or code == CODE_CENTER())
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(heights), 1 / 2))
    Ensures(Acc(list_pred(descents), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(heights))
    # Element-wise: the offset of box i is exactly the anchor's placement of
    # box i inside the track. This is what every consumer reads back.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(heights)
                   and i < len(descents),
                   Result()[i] == offset_for(heights[i], descents[i],
                                             total, code)))))
    # The discriminating contrast, made explicit per box:
    #  - low-edge anchor: offset depends only on the box's own descent;
    #  - high-edge anchor: offset is the track's excess over the box plus that
    #    descent. They differ exactly by the box's slack 2*(total - h).
    Ensures(Implies(code == CODE_LOWER(),
                    Forall(int, lambda i: (Implies(0 <= i and i < len(heights)
                           and i < len(descents),
                           Result()[i] == 2 * descents[i])))))
    Ensures(Implies(code == CODE_UPPER(),
                    Forall(int, lambda i: (Implies(0 <= i and i < len(heights)
                           and i < len(descents),
                           Result()[i] == 2 * (total - heights[i])
                           + 2 * descents[i])))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(heights):
        # invariants-start
        Invariant(Acc(list_pred(heights), 1 / 2))
        Invariant(Acc(list_pred(descents), 1 / 2))
        Invariant(len(heights) == len(descents))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(heights))
        Invariant(len(result) == i)
        Invariant(code == CODE_BASELINE() or code == CODE_LOWER()
                  or code == CODE_UPPER() or code == CODE_CENTER())
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                         result[k] == offset_for(heights[k], descents[k],
                                                 total, code)))))
        Invariant(MustTerminate(len(heights) - i + 1))
        # invariants-end
        h = heights[i]
        d = descents[i]
        if code == CODE_BASELINE():
            off = 0
        elif code == CODE_LOWER():
            off = 2 * d
        elif code == CODE_UPPER():
            off = 2 * (total - h) + 2 * d
        else:
            off = (total - h) + 2 * d
        result.append(off)
        i = i + 1
    return result
    # impl-end
