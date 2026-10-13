import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee participates in the modeled behavior. The current year,
-- which serves as the reference point for interpreting a two-digit year, is
-- supplied to the computation as an explicit input. The whole computation is
-- integer arithmetic, modeled deeply below. Hence there is no `opaque`
-- declaration and no consumed `_prop` axiom.
-- axioms-end

-- pure-start
-- (No standalone pure helpers are needed; the behavior is pinned directly by the
-- post-condition predicate and realized by the impl skeleton.)
-- pure-end

-- post-conditions-start
/-- Specification of how a parsed two-digit calendar year is expanded to a full
year, interpreted relative to the current year.

Inputs: `year` is the parsed year field (a two-digit year is in `0 … 99`; a
value `≥ 100` is already a full year and is taken verbatim), and `currentYear`
is the full current year used as the reference point. `result` is the expanded
full year.

Let `cc` be the century of the current year (its hundreds component). For a
two-digit `year`:

* the expanded year keeps the same last two digits as `year`;
* it is never read as lying more than 50 years in the future of the reference
  year (`result ≤ currentYear + 50`);
* by default the two-digit year is placed in the current century
  (`result = year + cc`); only when that placement would fall more than 50 years
  ahead of the reference year is it rolled back one century
  (`result = year + cc - 100`), interpreting it as the most recent past year with
  those last two digits.

A value already `≥ 100` is returned unchanged. -/
def problem_spec_expandYear (year currentYear result : Int) : Prop :=
  let cc := currentYear - currentYear % 100
  (year ≥ 100 → result = year) ∧
  (year < 100 →
      result % 100 = year ∧
      result ≤ currentYear + 50 ∧
      (year + cc ≤ currentYear + 50 → result = year + cc) ∧
      (currentYear + 50 < year + cc → result = year + cc - 100))
-- post-conditions-end

-- impl-start
def implementation_expandYear (year currentYear : Int) : Int := Id.run do
  let mut y := year
  if year < 100 then
    let currentCentury := currentYear - currentYear % 100
    if year - currentYear % 100 > 50 then
      y := y + currentCentury - 100
    else
      y := y + currentCentury
  return y
-- impl-end

-- proof-start
theorem correct_expandYear : ∀ (year currentYear : Int), 0 ≤ year →
    problem_spec_expandYear year currentYear (implementation_expandYear year currentYear) := by
  intro year currentYear hy
  unfold problem_spec_expandYear implementation_expandYear
  simp only [Id.run, bind, pure]
  split <;> rename_i h1
  · split <;> rename_i h2 <;>
      refine ⟨fun _ => ?_, fun _ => ⟨?_, ?_, fun _ => ?_, fun _ => ?_⟩⟩ <;> omega
  · refine ⟨fun _ => ?_, fun _ => ⟨?_, ?_, fun _ => ?_, fun _ => ?_⟩⟩ <;> omega
-- proof-end
