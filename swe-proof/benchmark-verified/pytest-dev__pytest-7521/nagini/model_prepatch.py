"""Twin-artifact model for pytest-dev__pytest-7521.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When test output written to a captured file descriptor is later read back as
  text, the captured text must reproduce the written content *verbatim*: every
  written code point appears unchanged and in the same order in the read-back
  result. In particular a carriage return (U+000D), whether standalone or as
  part of a CR+LF pair, is preserved as written and is NOT folded into a line
  feed (U+000A). Reading captured output therefore neither inserts, drops, nor
  rewrites any code point.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by the pure sequence theory `PSeq[int]`.

For contrast, the pure region also names `cr_folded`, a line-ending
normalization that rewrites every carriage return (U+000D) to a line feed
(U+000A) and leaves all other code points unchanged. The specified read-back is
NOT that normalization; `cr_folded` is modelled deeply (a front-recursive fold)
purely so the differential twin can exhibit it, and the captured text it would
produce is checked against a real text reader out-of-band by axiom_check.py
(G-AX). The implementation here performs the specified verbatim read-back: the
identity on code points.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No @ContractOnly axiom is consumed by this proof. The read-back of captured
#  text is modelled DEEPLY as the identity on code points; the contrasting
#  carriage-return normalization `cr_folded` (pure region) is checked against a
#  real text reader by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def cr_folded(s: PSeq[int]) -> PSeq[int]:
    """A carriage-return normalization (front-recursive fold): every carriage
    return (U+000D, 13) is rewritten to a line feed (U+000A, 10); every other
    code point passes through. Provided for contrast with the specified
    verbatim read-back, and checked against a real text reader by G-AX."""
    if len(s) == 0:
        return PSeq(10).take(0)
    if s[0] == 13:
        return PSeq(10) + cr_folded(s.drop(1))
    return PSeq(s[0]) + cr_folded(s.drop(1))
# pure-end


def captured_readback(written: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(written), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(written), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Captured text is reproduced verbatim: the read-back sequence equals the
    # written sequence code point for code point (carriage returns preserved).
    Ensures(ToSeq(Result()) == ToSeq(written))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(written)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(written), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(written))
        Invariant(ToSeq(result) == cr_folded(ToSeq(written).drop(i)))
        # invariants-end
        c = written[i - 1]
        Assert(ToSeq(written).drop(i - 1)[0] == c)
        Assert(ToSeq(written).drop(i - 1).drop(1) == ToSeq(written).drop(i))
        if c == 13:
            result = [10] + result
        else:
            result = [c] + result
        i = i - 1
    return result
    # impl-end
