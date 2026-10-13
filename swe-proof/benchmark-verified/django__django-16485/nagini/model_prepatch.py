"""Twin-artifact model for django__django-16485.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A numeric value is rendered for display with a requested number of decimal
  places `p`. Two presentation regimes meet at the integral case:

    * When the value is EXACTLY INTEGRAL (it has no fractional remainder) AND
      the number of decimal places requested is NON-POSITIVE (`p <= 0`, i.e.
      "show only the decimals the value actually carries, never force any"),
      the rendering is the bare integer: the decimal digits of the integer,
      with a leading minus for a negative value, and NOTHING ELSE — in
      particular NO decimal separator. An integral value asked for zero decimal
      places renders as "0", "1", "-3", ... — the well-defined bare integer
      string, never "0." and never an empty rendering.

    * In every other case (a non-integral value, or a positive number of
      requested decimal places) the rendering shows a fractional part: the
      integer digits, a decimal separator, then the fractional digit field.

  The boundary `p == 0` on an integral value belongs to the FIRST regime: zero
  requested decimal places on a whole number yields the bare integer string,
  not a separator-bearing rendering.

The renderings are modelled DEEPLY as decimal-digit folds over the code points
(Nagini bans `str` indexing, so strings are `List[int]` of Unicode code points
and the specification is carried by `PSeq[int]`). The localisation/grouping
callee that finally lays out the digit string is unchanged and preserves the
digit content the tests observe; it is recorded as an A-reference, not consumed
as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed @ContractOnly axiom. The single operation that changed is the
#  branch-selection between the bare-integer regime and the separator-bearing
#  regime; BOTH renderings are modelled DEEPLY below. The unchanged
#  localisation callee that finally lays out the digit string is digit-content
#  preserving and is recorded as an A-reference in refinement.md / mapping.md,
#  validated out-of-band by axiom_check.py / G-AX — it is not consumed here.)
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty code-point sequence."""
    return PSeq(48).drop(1)


@Pure
def mag(n: int) -> int:
    """Magnitude (absolute value) of an integer."""
    Ensures(Result() >= 0)
    if n >= 0:
        return n
    return -n


@Pure
def digits_acc(n: int, acc: PSeq[int]) -> PSeq[int]:
    """Decimal-digit code points of a non-negative integer, prepended to `acc`.
    Digit value d is code point 48 + d ('0'..'9'). Tail-shaped front-recursion
    so a single auto-unfold is available per step of the matching impl loop."""
    Requires(n >= 0)
    if n < 10:
        return PSeq(48 + n) + acc
    return digits_acc(n // 10, PSeq(48 + (n % 10)) + acc)


@Pure
def int_render(n: int) -> PSeq[int]:
    """Bare decimal rendering of an integer as code points: a leading minus
    (code point 45 '-') for a negative value, then the decimal digits of its
    magnitude. Contains NO decimal separator (code point 46 '.')."""
    if n >= 0:
        return digits_acc(n, empty_seq())
    return PSeq(45) + digits_acc(mag(n), empty_seq())


@Pure
def zeros_seq(count: int) -> PSeq[int]:
    """A run of `count` zero-digit code points (48)."""
    Requires(count >= 0)
    if count == 0:
        return empty_seq()
    return PSeq(48) + zeros_seq(count - 1)


@Pure
def rendered(int_value: int, frac_zero: bool, p: int) -> PSeq[int]:
    """The full rendering. In the bare-integer regime it is just the integer
    rendering; otherwise the integer digits, a decimal separator (code point
    46 '.'), then a `|p|`-wide fractional digit field."""
    if frac_zero and p <= 0:
        return int_render(int_value)
    return int_render(int_value) + PSeq(46) + zeros_seq(mag(p))
# pure-end


def format_value(int_value: int, frac_zero: bool, p: int) -> List[int]:
    """Render a value whose integer part is `int_value`, whose fractional
    remainder is zero iff `frac_zero`, asking for `p` decimal places."""
    # pre-conditions-start
    Requires(True)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The rendering equals the deep model `rendered`. In particular the
    # bare-integer regime (integral value, non-positive decimals) yields the
    # bare integer rendering with no decimal separator, while every other case
    # yields a separator-bearing rendering.
    Ensures(ToSeq(Result()) == rendered(int_value, frac_zero, p))
    # post-conditions-end
    # impl-start
    # Render the magnitude digits of int_value (shared by both regimes).
    digits = []  # type: List[int]
    k = mag(int_value)
    while k >= 10:
        # invariants-start
        Invariant(Acc(list_pred(digits)))
        Invariant(k >= 0)
        Invariant(digits_acc(mag(int_value), empty_seq()) == digits_acc(k, ToSeq(digits)))
        Invariant(MustTerminate(k + 1))
        # invariants-end
        digits = [48 + (k % 10)] + digits
        k = k // 10
    digits = [48 + k] + digits
    Assert(ToSeq(digits) == digits_acc(mag(int_value), empty_seq()))
    if int_value < 0:
        digits = [45] + digits
    Assert(ToSeq(digits) == int_render(int_value))

    if frac_zero and p < 0:
        # Bare-integer regime: no decimal separator.
        return digits
    else:
        # Separator-bearing regime: append the separator and the |p|-wide
        # fractional digit field.
        frac = []  # type: List[int]
        i = mag(p)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(frac)))
            Invariant(0 <= i and i <= mag(p))
            Invariant(ToSeq(frac) == zeros_seq(mag(p) - i))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            frac = [48] + frac
            i = i - 1
        out = digits + [46] + frac  # type: List[int]
        Assert(ToSeq(out) == int_render(int_value) + PSeq(46) + zeros_seq(mag(p)))
        return out
    # impl-end
