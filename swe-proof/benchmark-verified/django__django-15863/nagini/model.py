"""Twin-artifact model for django__django-15863.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A numeric value carries an exact, finite sequence of significant decimal
  digits. The display filter must first reconstruct that value from its
  canonical decimal textual form and operate on the reconstruction. The
  reconstruction is required to be EXACT: every significant decimal digit of
  the input value survives into the value the filter formats, in order and at
  full length, no matter how many digits the value has. A value with more
  significant digits than a binary floating-point significand can hold must
  NOT be silently rounded to the nearest representable binary fraction before
  formatting; the leading digits must not be the only ones that survive.

  Concretely: the digit sequence the filter works from equals, element for
  element, the digit sequence of the input value. This pins the precision-
  preserving behaviour the issue demands — a long-precision input keeps all of
  its trailing digits rather than having everything past a bounded significand
  budget dropped to zeros.

The value's significant digit sequence is modelled as a `List[int]` of decimal
digits (each in 0..9); the specification is carried by the pure sequence theory
`PSeq[int]`. The exact textual reconstruction is modelled deeply (a verified
identity-preserving fold). The lossy alternative — reconstruction that first
collapses the value through a bounded-width binary significand — is modelled by
`narrowed_to_significand`, whose agreement with the real binary round trip is
checked out-of-band by axiom_check.py (G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def significand_budget() -> int:
    """Upper bound on the number of significant decimal digits a binary
    floating-point significand can carry round-trip (IEEE-754 binary64 keeps
    17). A reconstruction that routes the value through such a significand can
    retain at most this many leading significant digits; the rest are lost."""
    return 17


@Pure
def narrowed_from(s: PSeq[int], budget: int) -> PSeq[int]:
    """Front-recursive helper: emit the leading `budget` significant digits
    unchanged and replace every later significant digit with a zero. One
    unfold is available per fold/loop step."""
    Requires(0 <= len(s))
    if len(s) == 0:
        return PSeq(0).take(0)
    if budget > 0:
        return PSeq(s[0]) + narrowed_from(s.drop(1), budget - 1)
    return PSeq(0) + narrowed_from(s.drop(1), 0)


@Pure
def narrowed_to_significand(s: PSeq[int]) -> PSeq[int]:
    """The digit sequence obtained when the value is reconstructed through a
    bounded-width binary significand: the leading `significand_budget()`
    significant digits are retained and every later significant digit is
    replaced by a zero (a faithful abstraction of the binary round trip, which
    cannot represent significant digits beyond its significand and rounds them
    away).

    The exact textual reconstruction the spec demands is the IDENTITY on this
    sequence; this lossy variant differs from the identity precisely when the
    value has more than `significand_budget()` significant digits."""
    Requires(0 <= len(s))
    return narrowed_from(s, significand_budget())
# pure-end


def reconstruct_digits(text: List[int]) -> List[int]:
    # pre-conditions-start
    # The input value is read-only: the reconstruction never mutates it, so it
    # is required AND ensured at fractional permission (directive 5).
    Requires(Acc(list_pred(text), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The reconstructed digit sequence equals the input value's digit sequence
    # exactly: every significant digit survives, in order, at full length. This
    # is the discriminating, precision-preserving guarantee the issue demands.
    Ensures(ToSeq(Result()) == ToSeq(text))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == ToSeq(text).drop(i))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = text[i - 1]
        Assert(ToSeq(text).drop(i - 1)[0] == c)
        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
        result = [c] + result
        i = i - 1
    return result
    # impl-end
