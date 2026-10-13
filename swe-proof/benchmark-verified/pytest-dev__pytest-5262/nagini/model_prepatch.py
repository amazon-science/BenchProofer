"""Twin-artifact model for pytest-dev__pytest-5262.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A text-stream wrapper that encodes Unicode text onto an underlying binary
  buffer must advertise a *text* access mode, not the buffer's binary mode.
  Concretely, the mode reported by the wrapper is the underlying buffer's
  mode with the binary marker code point (the letter 'b', U+0062) deleted at
  every position; all other code points pass through in their original order.

  Consequences the consumer relies on:
    * the reported mode never contains the binary marker code point, so callers
      that inspect the mode to choose between text and bytes select the text
      path; and
    * the reported mode is otherwise the buffer's mode unchanged (same code
      points, same order, only the binary markers elided), so a buffer mode that
      carries no binary marker is reported verbatim.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by the pure sequence theory `PSeq[int]`.
The deletion is modelled DEEPLY as a verified front-recursive fold
(`without_marker`); there is no axiomatized callee (the operation is a pure
single-character deletion, spelled out in full).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no axioms: the modeled operation is a pure single-code-point deletion,
#  modeled deeply by the fold `without_marker`; there is no unchanged callee
#  the proof consumes.)
# axioms-end


# pure-start
BINARY_MARKER = 98  # the code point 'b'


@Pure
def kept(c: int) -> PSeq[int]:
    """What a single code point contributes to the reported mode: nothing if it
    is the binary marker, otherwise the code point itself."""
    if c == BINARY_MARKER:
        return PSeq(0).take(0)
    return PSeq(c)


@Pure
def without_marker(s: PSeq[int]) -> PSeq[int]:
    """The reported mode for a whole buffer mode: concatenate each code point's
    contribution, dropping every binary marker. Front-recursive so a single
    unfold is available to callers per loop step."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return kept(s[0]) + without_marker(s.drop(1))


@Pure
def marker_free(s: PSeq[int]) -> bool:
    """True iff the sequence contains no binary marker code point."""
    if len(s) == 0:
        return True
    return s[0] != BINARY_MARKER and marker_free(s.drop(1))
# pure-end


def reported_mode(buffer_mode: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(buffer_mode), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(buffer_mode), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The reported mode is exactly the buffer mode with every binary marker
    # code point deleted (other code points kept, in order).
    Ensures(ToSeq(Result()) == without_marker(ToSeq(buffer_mode)))
    # The reported mode contains no binary marker code point.
    Ensures(marker_free(ToSeq(Result())))
    # post-conditions-end
    # impl-start
    # PRE-PATCH SKELETON: there is no dedicated mode property, so the reported
    # mode falls through to the underlying buffer's mode verbatim (the binary
    # marker is NOT deleted).
    result = []  # type: List[int]
    i = len(buffer_mode)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(buffer_mode), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(buffer_mode))
        Invariant(ToSeq(result) == ToSeq(buffer_mode).drop(i))
        # invariants-end
        c = buffer_mode[i - 1]
        Assert(ToSeq(buffer_mode).drop(i - 1)[0] == c)
        Assert(ToSeq(buffer_mode).drop(i - 1).drop(1) == ToSeq(buffer_mode).drop(i))
        result = [c] + result
        i = i - 1
    return result
    # impl-end
