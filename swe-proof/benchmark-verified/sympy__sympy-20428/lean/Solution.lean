import Mathlib
-- imports-end

/-!
The truthiness (nonzero) test of an element of a symbolic-expression coefficient
domain.

Such an element wraps a symbolic value. Deciding whether the element is "zero"
(falsy) or "nonzero" (truthy) must reflect the *mathematical* value of that
expression, not merely its written form: an expression that evaluates to the
additive identity counts as zero even when it is written as a large, non-trivial
combination of terms that does not literally reduce to the constant `0` on the
surface. Only when the value is definitely mathematically zero is the element
falsy; in every other case (definitely nonzero, or value not determined to be
zero) the element is truthy.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the desired behavior is a
-- direct function of the two zero-observations carried by the input element
-- (its syntactic form and its determined mathematical value), both modeled
-- explicitly below.
-- axioms-end

-- pure-start
/-- The relevant observable state of a symbolic-expression coefficient, for the
purpose of the nonzero test.

`isLiteralZero` records whether the element's value is *syntactically* the
additive identity (its representation is literally the constant `0`).
`isMathZero` records whether the element's value is *determined to be
mathematically* the additive identity (it evaluates to zero, regardless of how
it is written). A value that is written non-trivially yet evaluates to zero has
`isLiteralZero = false` and `isMathZero = true`; a value whose vanishing is not
determined has `isMathZero = false`. -/
structure ExprVal where
  isLiteralZero : Bool
  isMathZero : Bool
-- pure-end

-- post-conditions-start
/-- The element is nonzero (truthy) exactly when its value is **not** determined
to be mathematically zero. The syntactic form is irrelevant to the result. -/
def problem_spec_nonzero (e : ExprVal) (result : Bool) : Prop :=
  result = !e.isMathZero
-- post-conditions-end

-- impl-start
def implementation_nonzero (e : ExprVal) : Bool := Id.run do
  return !e.isMathZero
-- impl-end

-- proof-start
theorem correct_nonzero :
    ∀ (e : ExprVal),
      problem_spec_nonzero e (implementation_nonzero e) := by
  intro e
  rfl
-- proof-end
