import Mathlib
-- imports-end

/-!
Equality of a floating-point value against another (already-normalised) symbolic
operand.

A float decides equality by dispatching on the *kind* of the operand. The
operand has already been brought into the symbolic domain (operands that cannot
be brought in at all are outside the scope of this routine). The decision is:

* a logic boolean operand is never equal to a float;
* a named numeric-constant operand: an irrational one is never equal; a rational
  one defers to that constant's own equality with the float;
* a float operand: equal exactly when the two share the same exact value;
* a rational operand: defers to the rational's own equality with the float;
* any other numeric operand: equal when the two agree once compared at a shared
  precision;
* for every remaining (non-numeric) operand, a *zero* float is equal precisely
  to those operands that are themselves empty/zero-like, and a non-zero float is
  never equal.

The intended guarantee is that the kind-based decision above is consulted in
full for every numeric and boolean operand, and the zero-float "empty-like"
fallback applies ONLY to the operands that fall through every numeric and
boolean case. In particular a zero float and a logic boolean are decided by the
boolean rule (never equal), giving a symmetric result.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The dispatch is
-- modeled structurally over the observable kind-flags of the operand together
-- with the boolean outcomes of the unchanged delegated comparisons (a named
-- constant's own equality, a rational's own equality, the shared-precision
-- numeric comparison) and whether the float / operand are zero-like; these enter
-- as plain data, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The observations of the float `self` and the (already-normalised) operand
that the equality decision reads.

* `selfIsZero` — the float value is zero;
* `otherIsBoolean` — the operand is a logic boolean;
* `otherIsNumberSymbol` — the operand is a named numeric constant;
* `otherIsIrrational` — that constant is irrational;
* `numberSymbolEq` — the result of the rational-constant's own equality with the
  float;
* `otherIsFloat` — the operand is itself a float;
* `mpfEq` — the two floats hold the same exact value;
* `otherIsRational` — the operand is a rational;
* `rationalEq` — the result of the rational's own equality with the float;
* `otherIsNumber` — the operand is some other numeric value;
* `numberMpfEq` — the two agree once compared at a shared precision;
* `otherIsFalsy` — the operand is itself empty/zero-like. -/
structure EqInput where
  selfIsZero : Bool
  otherIsBoolean : Bool
  otherIsNumberSymbol : Bool
  otherIsIrrational : Bool
  numberSymbolEq : Bool
  otherIsFloat : Bool
  mpfEq : Bool
  otherIsRational : Bool
  rationalEq : Bool
  otherIsNumber : Bool
  numberMpfEq : Bool
  otherIsFalsy : Bool

/-- The boolean a float returns for equality with the operand, by the rule
described above: the kind dispatch is consulted in full, and the zero-float
empty-like fallback applies only to operands that match none of the boolean or
numeric kinds. -/
def floatEqResult (inp : EqInput) : Bool :=
  if inp.otherIsBoolean then false
  else if inp.otherIsNumberSymbol then
    (if inp.otherIsIrrational then false else inp.numberSymbolEq)
  else if inp.otherIsFloat then inp.mpfEq
  else if inp.otherIsRational then inp.rationalEq
  else if inp.otherIsNumber then inp.numberMpfEq
  else if inp.selfIsZero then inp.otherIsFalsy
  else false
-- pure-end

-- post-conditions-start
/-- The returned boolean is exactly the value assigned by the kind dispatch. A
zero float compared to a logic boolean is decided by the boolean rule (never
equal), not by the empty-like fallback. -/
def problem_spec_floatEq (inp : EqInput) (result : Bool) : Prop :=
  result = floatEqResult inp
-- post-conditions-end

-- impl-start
def implementation_floatEq (inp : EqInput) : Bool := Id.run do
  if inp.otherIsBoolean then
    return false
  if inp.otherIsNumberSymbol then
    if inp.otherIsIrrational then
      return false
    return inp.numberSymbolEq
  if inp.otherIsFloat then
    return inp.mpfEq
  if inp.otherIsRational then
    return inp.rationalEq
  if inp.otherIsNumber then
    return inp.numberMpfEq
  if inp.selfIsZero then
    return inp.otherIsFalsy
  return false
-- impl-end

-- proof-start
theorem correct_floatEq :
    ∀ (inp : EqInput),
      problem_spec_floatEq inp (implementation_floatEq inp) := by
  intro inp
  unfold problem_spec_floatEq implementation_floatEq floatEqResult
  simp only [Id.run]
  by_cases h1 : inp.otherIsBoolean = true <;>
    by_cases h2 : inp.otherIsNumberSymbol = true <;>
    by_cases h3 : inp.otherIsIrrational = true <;>
    by_cases h4 : inp.otherIsFloat = true <;>
    by_cases h5 : inp.otherIsRational = true <;>
    by_cases h6 : inp.otherIsNumber = true <;>
    by_cases h7 : inp.selfIsZero = true <;>
    simp_all <;> rfl
-- proof-end
