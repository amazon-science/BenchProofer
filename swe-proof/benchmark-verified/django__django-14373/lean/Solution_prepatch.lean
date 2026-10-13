import Mathlib
-- imports-end

/-!
Rendering the year component of a date as a fixed-width decimal numeral.

A date carries a year as a non-negative whole number. This routine produces the
textual form of that year for inclusion in a formatted date string. The year is
written in base ten and left-padded with the character `'0'` so that the rendered
form always occupies at least four character positions. A year whose ordinary
base-ten form already has four or more digits is written out in full, with no
truncation and no extra padding.

Thus the rendered text is exactly the base-ten numeral of the year, prefixed by
just enough `'0'` characters to reach a minimum width of four.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The textual
-- rendering of the year (its base-ten numeral together with the leading-zero
-- padding to a minimum width) is the operation governed here, so it is modeled
-- structurally with concrete operations; no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- Left-pad a string with `'0'` characters up to a minimum `width`. If `s`
already has length `≥ width`, it is returned unchanged (natural subtraction makes
the padding count `0`). -/
def padZeros (width : Nat) (s : String) : String :=
  String.mk (List.replicate (width - s.length) '0') ++ s
-- pure-end

-- post-conditions-start
/-- The rendered text is the base-ten numeral of `year`, left-padded with `'0'`
characters to a minimum width of four. This pins the result exactly: it is the
decimal digits of `year` (no leading zeros beyond those introduced by the
padding), preceded by exactly `4 - (number of decimal digits)` zero characters
when that quantity is positive, and unchanged when the numeral already reaches
width four. -/
def problem_spec_renderYear (year : Nat) (result : String) : Prop :=
  result = padZeros 4 (toString year)
-- post-conditions-end

-- impl-start
def implementation_renderYear (year : Nat) : String := Id.run do
  -- Renders the bare base-ten numeral of the year with no leading-zero padding,
  -- so years whose numeral is shorter than four positions are rendered too short.
  return toString year
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- impl it cannot close: the spec requires the padded numeral `padZeros 4
-- (toString year)`, while this impl yields the bare `toString year`; the two
-- disagree on every year whose numeral is shorter than four digits (e.g. 1, 999).
theorem correct_renderYear :
    ∀ (year : Nat),
      problem_spec_renderYear year (implementation_renderYear year) := by
  intro year
  unfold problem_spec_renderYear implementation_renderYear
  rfl
-- proof-end
