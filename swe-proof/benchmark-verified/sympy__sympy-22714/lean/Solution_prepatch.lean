import Mathlib
-- imports-end

/-!
Deciding whether a tuple of proposed coordinates must be rejected because one of
them is an *imaginary* (non-real) number.

A coordinate is rejected only when it is a concrete number whose imaginary part
is *determined to be mathematically non-zero*. Determination is three-valued:
the imaginary part may be determined to be zero, determined to be non-zero, or
left undetermined. A coordinate that is a free symbol (not a concrete number) is
never rejected on this ground, and neither is a concrete number whose imaginary
part is determined zero or merely undetermined — only a number whose imaginary
part is *definitely* non-zero makes the whole tuple ineligible.

The overall decision is the existential over all coordinates: the tuple is
rejected exactly when at least one coordinate meets that condition. A surface,
form-level reading of a coordinate's imaginary part is *not* the criterion; the
criterion is the determined mathematical value.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the decision is a direct
-- function of three per-coordinate observations carried by the input (whether
-- the coordinate is a concrete number, a form-level reading of its imaginary
-- part, and the three-valued determination of that imaginary part's vanishing),
-- all modeled explicitly below.
-- axioms-end

-- pure-start
/-- The observable state of one proposed coordinate, for the purpose of the
imaginary-coordinate decision.

* `isNumber` records whether the coordinate is a concrete number (as opposed to
  a free symbol or other non-numeric expression).
* `imagPartTruthy` records a *form-level* reading of the coordinate's imaginary
  part — whether that imaginary part reads as a non-trivial object on the
  surface, regardless of its mathematical value.
* `imagPartDetZero` records the three-valued *determination* of whether the
  imaginary part is mathematically zero: `some true` (determined zero),
  `some false` (determined non-zero), or `none` (not determined). -/
structure Coord where
  isNumber : Bool
  imagPartTruthy : Bool
  imagPartDetZero : Option Bool

/-- A single coordinate forces rejection exactly when it is a concrete number
whose imaginary part is *determined to be non-zero*. -/
def Coord.rejects (c : Coord) : Bool :=
  c.isNumber && (c.imagPartDetZero == some false)
-- pure-end

-- post-conditions-start
/-- The tuple of coordinates is rejected (`result = true`) exactly when at least
one coordinate is a concrete number whose imaginary part is determined to be
non-zero. The form-level reading of the imaginary part is irrelevant. -/
def problem_spec_imaginaryCheck (coords : List Coord) (result : Bool) : Prop :=
  result = coords.any Coord.rejects
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: a coordinate is rejected on the *form-level*
-- reading of its imaginary part (`imagPartTruthy`) rather than on the
-- three-valued determination that the imaginary part is non-zero. A concrete
-- number whose imaginary part merely reads as a non-trivial object on the
-- surface — yet is mathematically determined to be zero — is wrongly rejected.
def implementation_imaginaryCheck (coords : List Coord) : Bool := Id.run do
  for c in coords do
    if c.isNumber && c.imagPartTruthy then
      return true
  return false
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl (the
-- form-level reading clause `imagPartTruthy` disagrees with the spec's
-- determined-non-zero clause `imagPartDetZero = some false` on any coordinate
-- whose imaginary part reads as truthy yet is determined to be zero).
theorem correct_imaginaryCheck :
    ∀ (coords : List Coord),
      problem_spec_imaginaryCheck coords
        (implementation_imaginaryCheck coords) := by
  sorry
-- proof-end
