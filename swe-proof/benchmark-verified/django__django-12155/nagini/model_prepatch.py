"""Twin-artifact model for django__django-12155.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A multi-line block of text is normalised by uniformly removing the common
  leading indentation. The text is a sequence of lines; each line is summarised
  by a single number: its amount of leading whitespace when the line has
  visible content, or a blank marker (a negative value) when the line is
  empty/whitespace-only.

  The amount of indentation that is stripped is the SMALLEST leading-whitespace
  amount among the NON-BLANK lines OTHER THAN the first line. The very first
  line always has its own leading whitespace removed in full (its content is
  flush-left). Every subsequent non-blank line then has exactly that common
  amount removed from its front. When there is no non-blank line after the
  first, nothing is removed from the subsequent lines.

  The defining property is that the common amount is measured WITHOUT regard to
  the first line's indentation: a body line that originally sat at the common
  indentation ends up flush-left, even when the first line carries text that
  begins at column zero. (A naive measurement that also folds in the first
  line's indentation would, for a first line beginning at column zero, find a
  common amount of zero and leave every body line indented.)

A line is modelled by one `int` (its leading-whitespace count, or a negative
blank marker), so the whole block is a `List[int]`; the specification is
carried by the pure-sequence theory `PSeq[int]`. An amount of leading
whitespace is a count of characters, so it is never negative and may be
arbitrarily large: a negative number therefore never denotes an amount, and the
common-amount measurement reports "there was no line to measure" with a
negative value of its own rather than with some large one. The measurement and
the per-line removal are front-recursive folds so a single unfold is available
per loop step.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No @ContractOnly axioms: the changed operation (the indentation measurement
# and removal) is modelled DEEPLY below. The corresponding stdlib callee is an
# A-reference, validated == this deep model by axiom_check.py (G-AX), never
# consumed as an axiom.
# axioms-end


# pure-start
@Pure
def NO_AMOUNT() -> int:
    """The value the common-amount measurement takes when it had no non-blank
    line to measure (the identity of the minimum fold). It is NEGATIVE, and an
    amount of leading whitespace never is, so "nothing was measured" is told
    apart from every real amount by its sign — for lines at any indentation
    whatever, rather than only for lines less indented than some chosen
    magnitude."""
    return -1


@Pure
def min_indent_from(eff: PSeq[int], k: int) -> int:
    """Smallest leading-whitespace amount among the NON-BLANK lines (entry
    `>= 0`) from index `k` onward; `NO_AMOUNT()` when there is none.
    Front-recursive so one unfold is available per loop step."""
    Requires(0 <= k)
    if k >= len(eff):
        return NO_AMOUNT()
    rest = min_indent_from(eff, k + 1)
    if eff[k] >= 0:
        if rest < 0 or eff[k] < rest:
            return eff[k]
        return rest
    return rest


@Pure
def clamp_margin(m: int) -> int:
    """The amount actually removed from each subsequent line: the measured
    common amount, or zero when no non-blank line followed the first (the
    measurement is then negative, which no amount is)."""
    if m >= 0:
        return m
    return 0


@Pure
def remove_margin(s: PSeq[int], margin: int) -> PSeq[int]:
    """Per-line removal of `margin` units of leading whitespace from each line
    of `s`: a non-blank line (`x >= 0`) loses `margin`; a blank line stays
    blank. Front-recursive (one unfold per loop step)."""
    if len(s) == 0:
        return PSeq(0).take(0)
    head = s[0] - margin
    if s[0] < 0:
        head = -1
    return PSeq(head) + remove_margin(s.drop(1), margin)


@Pure
def first_line(x: int) -> int:
    """The first line after normalisation: a non-blank first line is moved
    flush-left (its leading whitespace fully removed, so its amount is 0); a
    blank first line stays blank."""
    if x < 0:
        return -1
    return 0


@Pure
def dedented(s: PSeq[int]) -> PSeq[int]:
    """The whole normalised block: the first line moved flush-left (or kept
    blank), then every subsequent line with the common amount removed. The
    common amount is measured over the non-blank lines AFTER the first only."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(first_line(s[0])) + remove_margin(
        s.drop(1), clamp_margin(min_indent_from(s, 1)))
# pure-end


def dedent_block(eff: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(eff), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(eff), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # There is exactly one output entry per input line.
    Ensures(len(Result()) == len(eff))
    # The normalised block: a non-blank first line moved flush-left (a blank
    # first line kept blank), every subsequent line with the common amount
    # (measured over the non-blank lines after the first) removed; blank lines
    # stay blank.
    Ensures(ToSeq(Result()) == dedented(ToSeq(eff)))
    # A non-blank first line ends flush-left.
    Ensures(Implies(len(eff) > 0 and ToSeq(eff)[0] >= 0, Result()[0] == 0))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    n = len(eff)
    if n == 0:
        Assert(len(ToSeq(eff)) == 0)
        Assert(ToSeq(result) == dedented(ToSeq(eff)))
        return result
    # Pre-patch skeleton: the common amount is measured over the non-blank
    # lines from the VERY FIRST line (index 0) onward, not from the second line
    # on. When the first line begins at column zero this measured amount is
    # zero, so the body lines are left indented.
    margin = clamp_margin(min_indent_from(ToSeq(eff), 0))
    i = n
    while i > 1:
        # invariants-start
        Invariant(Acc(list_pred(eff), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(1 <= i and i <= n and n == len(eff) and n > 0)
        Invariant(margin == clamp_margin(min_indent_from(ToSeq(eff), 0)))
        Invariant(len(result) == n - i)
        Invariant(ToSeq(result) == remove_margin(
            ToSeq(eff).drop(i), clamp_margin(min_indent_from(ToSeq(eff), 0))))
        Invariant(MustTerminate(i - 1 + 1))
        # invariants-end
        c = eff[i - 1]
        Assert(ToSeq(eff).drop(i - 1)[0] == c)
        Assert(ToSeq(eff).drop(i - 1).drop(1) == ToSeq(eff).drop(i))
        if c < 0:
            result = [-1] + result
        else:
            result = [c - margin] + result
        i = i - 1
    Assert(i == 1)
    Assert(ToSeq(eff).drop(1) == ToSeq(eff).drop(i))
    first = eff[0]
    if first < 0:
        result = [-1] + result
    else:
        result = [0] + result
    return result
    # impl-end
