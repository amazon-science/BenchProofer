"""Twin-artifact model for django__django-11206.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A numeric formatter is asked to render an exact base-ten value with a given
  count of visible fractional places ``decimal_pos``. The value is presented by
  its non-negative magnitude written as ``coeff * 10**exponent`` (``coeff`` the
  integer formed by its significant digits, ``exponent`` the power-of-ten
  scale), exactly as an exact base-ten number decomposes.

  The desired behaviour, derived from the problem statement and the magnitudes
  it discusses, is:

    (1) A value whose magnitude is strictly smaller than the smallest quantity
        the visible fractional window can represent is indistinguishable, at
        the requested precision, from nothing: it must be rendered as a plain
        zero padded to the requested precision, NOT in any wider/exponential
        form. The visibility threshold is ``10 ** -p`` where ``p`` is
        ``decimal_pos`` but never less than one (a request for zero fractional
        places still measures smallness against the tenths place). The
        comparison is STRICT: a magnitude exactly equal to the threshold is
        still visible and is NOT collapsed.

    (2) The plain-zero rendering at precision ``decimal_pos`` is the digit zero,
        followed -- only when at least one fractional place is requested -- by
        the decimal separator and exactly ``decimal_pos`` zero digits.

    (3) When the magnitude is at or above the visibility threshold the value is
        left for the ordinary formatting path: this routine reports "no
        collapse" (the absent value) and contributes no rendering of its own.

  The smallness decision is the changed behaviour and is modelled deeply over
  exact integer arithmetic (cross-multiplying the threshold away); the floor of
  one on the threshold exponent at zero requested places is part of that
  decision. The decomposition of an exact base-ten value into
  ``(coeff, exponent)`` and the magnitude/threshold comparison are the
  type-refinement boundary documented in mapping.md (and validated against the
  real arithmetic by axiom_check.py).

Strings are modelled as ``List[int]`` of code points (Nagini bans ``str``
indexing); the rendered output is carried by ``PSeq[int]``. The absent value
("no collapse, fall through to ordinary formatting") is ``None``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (No unchanged opaque callee is consumed by the proof. The smallness decision
#  and the plain-zero rendering are the changed behaviour and are modelled
#  deeply below over exact integer arithmetic. The decomposition of an exact
#  base-ten value into (coeff, exponent), the magnitude comparison, and the
#  zero-padding are the type-refinement boundary documented in mapping.md, not
#  axioms; their equality to the real arithmetic is checked out-of-band by
#  axiom_check.py / G-AX, an A-reference, not a consumed @ContractOnly.)
# axioms-end


# pure-start
@Pure
def pow10(n: int) -> int:
    """``10 ** n`` for non-negative exponents ``n``."""
    Requires(n >= 0)
    Ensures(Result() >= 1)
    if n == 0:
        return 1
    return 10 * pow10(n - 1)


@Pure
def threshold_exp(decimal_pos: int) -> int:
    """The exponent ``p`` of the visibility threshold ``10 ** -p``: the number
    of requested fractional places, but never less than one."""
    Requires(decimal_pos >= 0)
    Ensures(Result() >= 1)
    if decimal_pos >= 1:
        return decimal_pos
    return 1


@Pure
def below_cutoff(coeff: int, exponent: int, decimal_pos: int) -> bool:
    """Whether the magnitude ``coeff * 10**exponent`` is STRICTLY below the
    visibility threshold ``10 ** -threshold_exp(decimal_pos)``.

    Cross-multiplying the threshold away (multiply both sides by the positive
    ``10 ** threshold_exp``), the magnitude is below the threshold iff
    ``coeff * 10**(exponent + threshold_exp) < 1``. With ``coeff >= 0`` this is:
    a zero magnitude is always below; otherwise it is below exactly when the
    shifted scale ``exponent + threshold_exp`` is negative and ``coeff`` is
    smaller than ``10`` to that many places.
    """
    Requires(coeff >= 0)
    Requires(decimal_pos >= 0)
    if coeff == 0:
        return True
    if exponent + threshold_exp(decimal_pos) >= 0:
        return False
    return coeff < pow10(-(exponent + threshold_exp(decimal_pos)))


@Pure
def zeros(n: int) -> PSeq[int]:
    """A run of ``n`` zero digits (code point 48), front-recursive."""
    Requires(n >= 0)
    Ensures(len(Result()) == n)
    if n == 0:
        return PSeq(48).take(0)
    return PSeq(48) + zeros(n - 1)


@Pure
def zero_render(decimal_pos: int) -> PSeq[int]:
    """The plain-zero rendering at precision ``decimal_pos``: the digit zero
    (48), then -- only when at least one fractional place is requested -- the
    decimal separator (46) and ``decimal_pos`` zero digits."""
    Requires(decimal_pos >= 0)
    if decimal_pos == 0:
        return PSeq(48)
    return PSeq(48, 46) + zeros(decimal_pos)


@Pure
def opt_seq(x: Optional[List[int]]) -> PSeq[int]:
    """The element sequence of an optional rendering: its code points when a
    rendering is produced, the empty sequence when none is. Guards the None case
    so the spec can compare a produced rendering without indexing through None."""
    Requires(Implies(x is not None, Acc(list_pred(x), 1 / 4)))
    if x is None:
        return PSeq(0).take(0)
    return ToSeq(x)
# pure-end


def format_small(coeff: int, exponent: int, decimal_pos: int) -> Optional[List[int]]:
    # pre-conditions-start
    # The value's non-negative magnitude is `coeff * 10**exponent`; `coeff` is
    # the integer formed by its significant digits, `exponent` its scale.
    Requires(coeff >= 0)
    Requires(decimal_pos >= 0)
    # pre-conditions-end
    # post-conditions-start
    # (1)/(3) A rendering is produced exactly when the magnitude is strictly
    # below the visibility threshold; otherwise the absent value is returned so
    # the ordinary formatting path governs.
    Ensures(Implies(not below_cutoff(coeff, exponent, decimal_pos),
                    Result() is None))
    Ensures(Implies(below_cutoff(coeff, exponent, decimal_pos),
                    Result() is not None))
    # Full write permission to the freshly built rendering when one is produced.
    Ensures(Implies(Result() is not None, Acc(list_pred(Result()))))
    # (2) Otherwise the produced rendering equals exactly the plain-zero
    # rendering (compared through `opt_seq`, which guards the None case).
    Ensures(Implies(below_cutoff(coeff, exponent, decimal_pos),
                    opt_seq(Result()) == zero_render(decimal_pos)))
    # post-conditions-end
    # impl-start
    # The visibility threshold is 10 ** -p; a magnitude strictly smaller than it
    # is treated as zero and rendered as a padded zero, otherwise this routine
    # contributes nothing and the ordinary path takes over.
    p = decimal_pos
    if p < 1:
        p = 1
    shifted = exponent + p
    is_small = False  # type: bool
    if coeff == 0:
        is_small = True
    elif shifted < 0 and coeff < pow10(-shifted):
        is_small = True
    Assert(is_small == below_cutoff(coeff, exponent, decimal_pos))
    if not is_small:
        return None
    # Build the padded-zero rendering. When at least one fractional place is
    # requested, build the run of zero digits by prepending (matching the
    # front-recursive `zeros`), then prefix the '0' and decimal separator.
    if decimal_pos == 0:
        result = [48]  # type: List[int]
        Assert(ToSeq(result) == zero_render(decimal_pos))
        return result
    frac = []  # type: List[int]
    i = decimal_pos
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(frac)))
        Invariant(0 <= i and i <= decimal_pos)
        Invariant(ToSeq(frac) == zeros(decimal_pos - i))
        # invariants-end
        frac = [48] + frac
        i = i - 1
    Assert(ToSeq(frac) == zeros(decimal_pos))
    result = [48, 46] + frac
    Assert(ToSeq(result) == PSeq(48, 46) + zeros(decimal_pos))
    Assert(ToSeq(result) == zero_render(decimal_pos))
    return result
    # impl-end
