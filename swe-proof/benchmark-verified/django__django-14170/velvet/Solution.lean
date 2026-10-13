import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- Calendar landmarks for a given year, as the unchanged platform date/datetime
   library reports them. Dates are carried as proleptic-Gregorian day ordinals
   and timestamps as integer microsecond instants (a strictly order-preserving
   bijection — see mapping.md §2), so the comparison semantics a range query
   relies on are preserved exactly. These are read-only library callees the
   operation invokes but does not reshape; provenance + executable soundness
   check (G-AX) live in mapping.md / axiom_check.py.

   `gregJan1 y` — first day of calendar year `y` (its January 1st).
   `gregDec31 y` — last day of calendar year `y` (its December 31st).
   `isoFirst y` — first day of the ISO-8601 week-numbering year `y`.
   `dtJan1 y` — first instant of calendar year `y`.
   `dtDec31 y` — last instant of calendar year `y` (its final microsecond).
   `dtIsoFirst y` — first instant of the ISO-8601 week-numbering year `y`. -/
axiom gregJan1    : Int → Int
axiom gregDec31   : Int → Int
axiom isoFirst    : Int → Int
axiom dtJan1      : Int → Int
axiom dtDec31     : Int → Int
axiom dtIsoFirst  : Int → Int
-- axioms-end

-- pure-start
noncomputable section
/- The closed (inclusive) range of day ordinals that a year-valued range query
   over a date-typed column must match.

   For an ordinary calendar year the range runs from that year's first day to
   its last day. For an ISO-8601 week-numbering year the range instead runs from
   that ISO year's first day up to the day immediately before the next ISO
   year's first day — these two notions of "year" disagree near the new-year
   boundary, so the ISO range must be derived from the ISO landmarks, not the
   calendar ones. The carrier is the two-element list `[lower, upper]`. -/
def dateBounds (value : Int) (isoYear : Bool) : List Int :=
  if isoYear then [isoFirst value, isoFirst (value + 1) - 1]
  else [gregJan1 value, gregDec31 value]

/- The closed (inclusive) range of microsecond instants for a year-valued range
   query over a timestamp-typed column. Same calendar-vs-ISO distinction as
   `dateBounds`; the ISO upper bound is the instant one microsecond before the
   first instant of the next ISO year. -/
def datetimeBounds (value : Int) (isoYear : Bool) : List Int :=
  if isoYear then [dtIsoFirst value, dtIsoFirst (value + 1) - 1]
  else [dtJan1 value, dtDec31 value]

@[grind] lemma dateBounds_def (value : Int) (isoYear : Bool) :
    dateBounds value isoYear =
      (if isoYear then [isoFirst value, isoFirst (value + 1) - 1]
       else [gregJan1 value, gregDec31 value]) := rfl

@[grind] lemma datetimeBounds_def (value : Int) (isoYear : Bool) :
    datetimeBounds value isoYear =
      (if isoYear then [dtIsoFirst value, dtIsoFirst (value + 1) - 1]
       else [dtJan1 value, dtDec31 value]) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Lower and upper bounds for a year-valued range query against a date-typed
   column. `isoYear` selects whether the looked-up `value` denotes an ISO-8601
   week-numbering year or an ordinary calendar year; both inputs are read-only
   (neither is `mut`). When `isoYear` holds the bounds must be the ISO year's
   span, which differs from the calendar year's span at the year boundary. -/
method yearBoundsDate (value : Int) (isoYear : Bool) return (out : List Int)
  ensures out = dateBounds value isoYear
  ensures isoYear = true  → out = [isoFirst value, isoFirst (value + 1) - 1]
  ensures isoYear = false → out = [gregJan1 value, gregDec31 value]
  do
    -- impl-start
    let out : List Int :=
      if isoYear then
        [isoFirst value, isoFirst (value + 1) - 1]
      else
        [gregJan1 value, gregDec31 value]
    return out
    -- impl-end

prove_correct yearBoundsDate by
  loom_solve

/- Lower and upper bounds for a year-valued range query against a timestamp-typed
   column. As `yearBoundsDate`, but over microsecond instants; `isoYear` selects
   the ISO-8601 week-numbering year span when set. Both inputs read-only. -/
method yearBoundsDatetime (value : Int) (isoYear : Bool) return (out : List Int)
  ensures out = datetimeBounds value isoYear
  ensures isoYear = true  → out = [dtIsoFirst value, dtIsoFirst (value + 1) - 1]
  ensures isoYear = false → out = [dtJan1 value, dtDec31 value]
  do
    -- impl-start
    let out : List Int :=
      if isoYear then
        [dtIsoFirst value, dtIsoFirst (value + 1) - 1]
      else
        [dtJan1 value, dtDec31 value]
    return out
    -- impl-end

prove_correct yearBoundsDatetime by
  loom_solve

/- Dispatch a year-valued range query to the bounds appropriate for the column's
   type. `isDateTimeField` distinguishes a timestamp-typed column from a
   date-typed one. `isoYear` records whether the lookup targets ISO-8601
   week-numbering years; it MUST be forwarded to the chosen bounds computation so
   that an ISO-year lookup yields ISO-year bounds rather than calendar-year
   bounds. All inputs are read-only. -/
method yearLookupBounds (isDateTimeField : Bool) (isoYear : Bool) (value : Int)
    return (out : List Int)
  ensures out = (if isDateTimeField then datetimeBounds value isoYear
                 else dateBounds value isoYear)
  ensures isDateTimeField = true  → out = datetimeBounds value isoYear
  ensures isDateTimeField = false → out = dateBounds value isoYear
  do
    -- impl-start
    let out ← if isDateTimeField then
        yearBoundsDatetime value isoYear
      else
        yearBoundsDate value isoYear
    return out
    -- impl-end

prove_correct yearLookupBounds by
  loom_solve

end
