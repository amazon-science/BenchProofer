import Mathlib
-- imports-end

/-!
Computing a shifted calendar reference point.

Given a starting instant and a whole number of years and months, this builds a
reference instant that lies exactly that many years and months after the start.
The reference instant is used downstream to measure the leftover sub-month part
of an elapsed interval, so it must be directly comparable with the other
instants involved in that measurement.

The reference instant is assembled field-by-field from the starting instant:

  * its calendar date is the start's year/month advanced by the requested
    years and months (rolling the month past December into the next year);
  * its day-of-month is the start's day, clamped down to the last valid day of
    the resulting month (so e.g. a 31st never lands in a 30-day month);
  * its clock fields (hour, minute, second) are copied unchanged from the start.

An instant also carries a timezone designation (a constant offset from UTC, or
none when the instant is timezone-naive). Because the reference instant is later
compared against another instant, it must carry the SAME timezone designation as
the starting instant — a naive start yields a naive reference, and an instant at
a given offset yields a reference at that same offset. An instant whose timezone
designation failed to match its peers could not be compared with them at all.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by this specification. The reference
-- instant is assembled purely from the starting instant's own fields, so its
-- construction is modeled DEEPLY (structure assembly + clamping) rather than
-- through any `opaque`/`axiom` callee contract. The table of month lengths is a
-- constant table, modeled directly in the `pure` region. No callee property is
-- needed by the proof.
-- axioms-end

-- pure-start
/-- An instant: a calendar date, clock fields, and an optional timezone
designation (a constant UTC offset in seconds; `none` = timezone-naive). -/
structure Instant where
  year : Int
  month : Int
  day : Int
  hour : Int
  minute : Int
  second : Int
  offset : Option Int
deriving Repr

/-- Lengths of the twelve calendar months (non-leap reference table). Indexed by
month number 1‥12. -/
def monthLengths : List Int := [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

/-- The length of month `m` (1‥12) from the reference table; out-of-range months
fall back to 31 (never exercised under the precondition `1 ≤ m ≤ 12`). -/
def monthLength (m : Int) : Int := monthLengths.getD (m.toNat - 1) 31
-- pure-end

-- post-conditions-start
/-- The reference instant lies exactly `years` years and `months` months after
`d`. Every component is pinned to its input (frame discipline):

  * year/month are `d`'s advanced by the request, rolling a month past December
    into the next year;
  * the day is `d`'s day clamped to the last valid day of the resulting month;
  * the clock fields equal `d`'s clock fields;
  * the timezone designation equals `d`'s, so the reference is comparable with
    the instants it will be measured against. -/
def problem_spec_anchor
    (d : Instant) (years months : Int) (result : Instant) : Prop :=
  let rawMonth := d.month + months
  let rolled := rawMonth > 12
  result.year = (if rolled then d.year + years + 1 else d.year + years) ∧
  result.month = (if rolled then rawMonth - 12 else rawMonth) ∧
  result.day = min (monthLength result.month) d.day ∧
  result.hour = d.hour ∧
  result.minute = d.minute ∧
  result.second = d.second ∧
  result.offset = d.offset
-- post-conditions-end

-- impl-start
def implementation_anchor
    (d : Instant) (years months : Int) : Instant := Id.run do
  let mut anchorYear := d.year + years
  let mut anchorMonth := d.month + months
  if anchorMonth > 12 then
    anchorMonth := anchorMonth - 12
    anchorYear := anchorYear + 1
  return {
    year := anchorYear,
    month := anchorMonth,
    day := min (monthLength anchorMonth) d.day,
    hour := d.hour,
    minute := d.minute,
    second := d.second,
    offset := none
  }
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- impl it cannot close: the assembled reference instant discards the starting
-- instant's timezone designation (its `offset` is fixed to `none`), so on any
-- input whose `offset` is `some k` the result's `offset` is `none ≠ some k`,
-- while the spec demands `result.offset = d.offset`. The final `simp only` step
-- for the offset conjunct therefore leaves an unprovable `none = some k` goal and
-- the proof fails to typecheck.
theorem correct_anchor :
    ∀ (d : Instant) (years months : Int),
      1 ≤ d.month → d.month ≤ 12 → 0 ≤ months → months ≤ 11 →
      problem_spec_anchor d years months
        (implementation_anchor d years months) := by
  intro d years months _ _ _ _
  unfold problem_spec_anchor implementation_anchor
  by_cases h : d.month + months > 12
  · refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
      simp only [Id.run, bind, pure, h, if_true]
  · refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
      simp only [Id.run, bind, pure, h, if_false]
-- proof-end
