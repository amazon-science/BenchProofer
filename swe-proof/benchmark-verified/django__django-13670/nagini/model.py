"""Twin-artifact model for django__django-13670.

Behaviour under specification (stated as desired behaviour, not as an edit):

  The abbreviated-year rendering takes a calendar year and produces its two
  least-significant decimal digits as a fixed-width, two-character string, with
  a leading zero supplied whenever the value is below ten. Concretely, writing
  ``v`` for the year reduced modulo one hundred (so ``0 <= v <= 99``), the
  result is exactly two characters: the tens digit ``v // 10`` followed by the
  units digit ``v % 10``, each rendered as its decimal-digit character. The
  output therefore always has length two regardless of the magnitude of the
  year — a year such as four renders as ``04`` and a year such as forty-two
  renders as ``42`` — matching the conventional two-digit abbreviation.

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); ``ord('0') == 48``. The calendar year is an ``int``. No
library callee is involved — the rendering is pure integer arithmetic and
digit emission, so it is modelled deeply and no operation is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no library callee is invoked; the rendering is modelled deeply, so there is
# no @ContractOnly axiom.)
# axioms-end


# pure-start
@Pure
def tens_digit(v: int) -> int:
    """Code point of the tens digit of a value in 0..99."""
    Requires(0 <= v and v <= 99)
    Ensures(Result() == 48 + (v // 10))
    return 48 + (v // 10)


@Pure
def units_digit(v: int) -> int:
    """Code point of the units digit of a value in 0..99."""
    Requires(0 <= v and v <= 99)
    Ensures(Result() == 48 + (v % 10))
    return 48 + (v % 10)
# pure-end


def abbreviated_year(year: int) -> List[int]:
    # pre-conditions-start
    # Calendar years handled by the renderer are positive (datetime: 1..9999).
    Requires(1 <= year and year <= 9999)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The rendering is always exactly two characters wide.
    Ensures(len(Result()) == 2)
    # Both characters are decimal-digit code points (0x30..0x39).
    Ensures(48 <= Result()[0] and Result()[0] <= 57)
    Ensures(48 <= Result()[1] and Result()[1] <= 57)
    # The two characters are the tens then units digit of the year reduced
    # modulo one hundred — so a leading zero is emitted below ten, and the
    # value is grounded entirely in the input year's arithmetic.
    Ensures(Result()[0] == tens_digit(year % 100))
    Ensures(Result()[1] == units_digit(year % 100))
    # post-conditions-end
    # impl-start
    v = year % 100
    result = [tens_digit(v), units_digit(v)]  # type: List[int]
    return result
    # impl-end
