import Mathlib
-- imports-end

/-!
Lower/upper bounds for a year-based range query on date and timestamp columns.

A "year lookup" turns a query of the form "the year of this column equals (or is
compared against) `value`" into an inclusive range test `column BETWEEN lower AND
upper`, so that an ordinary index on the column can serve the query without
computing a per-row year extraction.

Two notions of "year" are supported, selected by a boolean:

* the ordinary **calendar year**: it runs from January 1st of `value` through
  December 31st of `value`; and
* the **ISO-8601 week-numbering year**: it runs from the Monday that begins ISO
  week 1 of `value` through the day before the Monday that begins ISO week 1 of
  `value + 1`. (ISO years do not line up with calendar years — an ISO year may
  start in late December of the previous calendar year or in early January.)

Dates are modeled by their proleptic-Gregorian ordinal day number (day 1 =
0001-01-01); timestamps by the microsecond count since that same epoch. For a
date column the bounds are the first and last *day* of the chosen year. For a
timestamp column the lower bound is midnight of the first day and the upper
bound is the last microsecond (`23:59:59.999999`) of the last day — i.e. one
microsecond before midnight that begins the next year.

The selecting boolean is supplied as an input; computing it, the column-type
dispatch, and the serialization of each bound are handled by the caller and are
not part of this specification. Behavior is stated abstractly as an
input→output relation; implementation and proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: both the Gregorian and the
-- ISO-8601 calendar day-number computations are spelled out concretely below as
-- arithmetic on the year, and validated against the standard-library calendar by
-- the differential conformance check (an A-reference, not a consumed axiom).
-- axioms-end

-- pure-start
/-- Microseconds in one day. -/
def usPerDay : Int := 86400000000

/-- Proleptic-Gregorian ordinal of January 1st of `y` (day 1 = 0001-01-01),
i.e. the count of days from the epoch to that date, plus one. Spelled out as the
standard day-count: 365 days per prior year, plus the leap-day corrections (one
per 4 years, minus one per 100 years, plus one per 400 years). -/
def gregJan1 (y : Int) : Int :=
  1 + 365 * (y - 1) + (y - 1) / 4 - (y - 1) / 100 + (y - 1) / 400

/-- Ordinal of December 31st of `y`: the day before January 1st of `y + 1`. -/
def gregDec31 (y : Int) : Int := gregJan1 (y + 1) - 1

/-- Ordinal of the Monday that begins ISO week 1 of `y`. ISO week 1 is the week
containing January 4th, and ISO weeks start on Monday; ordinal 1 (0001-01-01) is
a Monday, so the Monday of the week containing ordinal `o` is `o - ((o - 1) % 7)`.
Applied to January 4th (`gregJan1 y + 3`) this yields the ISO year's first day. -/
def isoYearStart (y : Int) : Int :=
  let jan4 := gregJan1 y + 3
  jan4 - ((jan4 - 1) % 7)
-- pure-end

-- post-conditions-start
/-- Inclusive `[lower, upper]` day-ordinal bounds for a year lookup on a date
column. When `isoYear` is `false` the bounds span the calendar year `value`
(Jan 1st … Dec 31st); when `true` they span the ISO-8601 week-numbering year
`value` (its first Monday … the day before the next ISO year's first Monday). -/
def problem_spec_yearBoundsDate (value : Int) (isoYear : Bool)
    (result : Int × Int) : Prop :=
  result.1 = (if isoYear then isoYearStart value else gregJan1 value) ∧
  result.2 = (if isoYear then isoYearStart (value + 1) - 1 else gregDec31 value)
-- post-conditions-end

-- post-conditions-start
/-- Inclusive `[lower, upper]` microsecond bounds for a year lookup on a
timestamp column. The lower bound is midnight (`* usPerDay`) of the chosen year's
first day; the upper bound is one microsecond before midnight that begins the
next year — i.e. `23:59:59.999999` of the chosen year's last day. The choice of
year (calendar vs ISO-8601 week-numbering) is governed by `isoYear` exactly as
for the date variant. -/
def problem_spec_yearBoundsDatetime (value : Int) (isoYear : Bool)
    (result : Int × Int) : Prop :=
  result.1 = (if isoYear then isoYearStart value else gregJan1 value) * usPerDay ∧
  result.2 = (if isoYear then isoYearStart (value + 1) else gregJan1 (value + 1)) * usPerDay - 1
-- post-conditions-end

-- impl-start
def implementation_yearBoundsDate (value : Int) (isoYear : Bool) :
    Int × Int := Id.run do
  let mut first : Int := 0
  let mut second : Int := 0
  if isoYear then
    first := isoYearStart value
    second := isoYearStart (value + 1) - 1
  else
    first := gregJan1 value
    second := gregDec31 value
  return (first, second)
-- impl-end

-- impl-start
def implementation_yearBoundsDatetime (value : Int) (isoYear : Bool) :
    Int × Int := Id.run do
  let mut first : Int := 0
  let mut second : Int := 0
  if isoYear then
    first := isoYearStart value * usPerDay
    second := isoYearStart (value + 1) * usPerDay - 1
  else
    first := gregJan1 value * usPerDay
    second := gregJan1 (value + 1) * usPerDay - 1
  return (first, second)
-- impl-end

-- proof-start
theorem correct_yearBoundsDate :
    ∀ (value : Int) (isoYear : Bool),
      problem_spec_yearBoundsDate value isoYear
        (implementation_yearBoundsDate value isoYear) := by
  intro value isoYear
  cases isoYear <;> exact ⟨rfl, rfl⟩
-- proof-end

-- proof-start
theorem correct_yearBoundsDatetime :
    ∀ (value : Int) (isoYear : Bool),
      problem_spec_yearBoundsDatetime value isoYear
        (implementation_yearBoundsDatetime value isoYear) := by
  intro value isoYear
  cases isoYear <;> exact ⟨rfl, rfl⟩
-- proof-end
