import Mathlib
-- imports-end

/-!
Sanitising the lower/upper bounds of a value range before it is handed to a
logarithmic display scale.

A value range is a pair `(lo, hi)`. When a logarithmic display scale is in use,
a non-positive lower bound is not representable (the logarithm of a non-positive
number is undefined), so such a lower bound must be replaced by a small positive
floor value. The desired behaviour is:

* the upper bound is always passed through unchanged;
* when a logarithmic scale is in use AND the lower bound is non-positive, the
  lower bound is replaced by the supplied positive floor;
* in every other case (no logarithmic scale, or a strictly positive lower
  bound) the lower bound is passed through unchanged.

Only the sign/zero ordering of the lower bound against `0` matters here, so the
bounds are modeled with exact rationals (`ℚ`); the floor models a constant
positive machine-precision value.
-/

-- axioms-start
-- No unchanged repo callee is consumed as a Lean axiom. The only quantity read
-- from an unchanged library routine is the small positive floor value; it is
-- modeled as an explicit input with a positivity precondition (carried as a
-- hypothesis of `correct_boundedRange`), not as an axiomatized callee, so there
-- is no `opaque` declaration and no `_prop` axiom.
-- axioms-end

-- pure-start
-- No pure helpers are required; the modeled behaviour is a direct conditional
-- on the lower bound's sign/zero ordering.
-- pure-end

-- post-conditions-start
/-- The sanitised range: the upper bound is unchanged; the lower bound is
replaced by the positive `floor` exactly when a logarithmic scale is in use and
the original lower bound is non-positive, and is otherwise unchanged. -/
def problem_spec_boundedRange
    (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) (result : ℚ × ℚ) : Prop :=
  result.2 = bounds.2 ∧
  ((logScale = true ∧ bounds.1 ≤ 0) → result.1 = floor) ∧
  (¬(logScale = true ∧ bounds.1 ≤ 0) → result.1 = bounds.1)
-- post-conditions-end

-- impl-start
def implementation_boundedRange
    (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ := Id.run do
  -- Pre-patch bug: the lower bound is only adjusted when it is STRICTLY
  -- negative; an exact-zero lower bound is left untouched and so is still
  -- handed to the logarithmic scale, which cannot represent it.
  let mut sLo := bounds.1
  let sHi := bounds.2
  if logScale = true then
    if sLo < 0 then
      sLo := max sLo floor
  return (sLo, sHi)
-- impl-end

-- proof-start
theorem correct_boundedRange :
    ∀ (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ), 0 < floor →
      problem_spec_boundedRange logScale floor bounds
        (implementation_boundedRange logScale floor bounds) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end
