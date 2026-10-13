import Mathlib
-- imports-end

/-!
Converting a membership assertion to the set it represents.

A membership assertion is a boolean-valued object built from two operands: an
`element` and a `setArg` (the set the element is asserted to belong to). Only
these two operands are retained — the conversion does not inspect the contents
of either.

Converting such an assertion to a set yields the set operand it was built with:
the result is always defined (a value is produced, never absent) and it is
exactly the `setArg` operand, unchanged. The element operand plays no role in
the result.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The conversion reads the object's own
-- stored set operand directly, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A membership assertion: the `element` asserted to belong to `setArg`.
`E` and `S` are abstract carrier types — the conversion is purely structural and
inspects neither operand's contents. -/
structure MembershipAssertion (E S : Type) where
  element : E
  setArg  : S
-- pure-end

-- post-conditions-start
/-- Converting a membership assertion to a set always produces a value (it is
`some _`, never `none`), and that value is exactly the assertion's set operand
`setArg`, taken verbatim from the input. -/
def problem_spec_asSet {E S : Type}
    (c : MembershipAssertion E S) (result : Option S) : Prop :=
  result = some c.setArg
-- post-conditions-end

-- impl-start
def implementation_asSet {E S : Type}
    (c : MembershipAssertion E S) : Option S := Id.run do
  return some c.setArg
-- impl-end

-- proof-start
theorem correct_asSet {E S : Type} :
    ∀ (c : MembershipAssertion E S),
      problem_spec_asSet c (implementation_asSet c) := by
  intro c
  rfl
-- proof-end
