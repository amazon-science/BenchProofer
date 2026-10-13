import Mathlib
-- imports-end

/-!
Equality of an unrecognised unit against an arbitrary operand.

An unrecognised unit carries a name string. Comparing it for equality with some
other operand proceeds by first trying to interpret that operand as a unit, in a
lenient mode:

* some operands cannot be interpreted as a unit at all (for example the null
  object, or a value of an unrelated type) — the interpretation step fails for
  these;
* otherwise the operand yields a unit value, which either is itself an
  unrecognised unit (carrying its own name string) or is some recognised unit.

The desired result of the comparison is three-valued:

  * if the operand cannot be interpreted as a unit, the comparison yields the
    "comparison not applicable" sentinel — it never propagates the interpretation
    failure to the caller;
  * if the operand yields an unrecognised unit whose name equals this unit's name,
    the comparison is true;
  * in every other case (a recognised unit, or an unrecognised unit with a
    different name), the comparison is false.

In particular, an operand that cannot be interpreted as a unit must produce the
sentinel result, not an escaping error.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The lenient
-- interpretation step is an unchanged upstream operation; its observable result
-- (interpretation failed, or a unit value tagged by whether it is unrecognised
-- and by its name) enters the decision as plain data (`ParseOutcome`). The
-- comparison rule itself is modeled structurally, so no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- An error that can escape the comparison. `parseError` stands for the
interpretation step failing and that failure reaching the caller. -/
inductive UnitError where
  | parseError
deriving DecidableEq, Repr

/-- The three-valued result of the comparison: true, false, or the
"comparison not applicable" sentinel. -/
inductive EqResult where
  | isTrue
  | isFalse
  | notApplicable
deriving DecidableEq, Repr

/-- The observable result of interpreting the other operand as a unit (lenient
mode):

* `raised` — the operand could not be interpreted as a unit;
* `parsed isUnrecognized otherName` — the operand yielded a unit value;
  `isUnrecognized` records whether that value is itself an unrecognised unit, and
  `otherName` is its name string. -/
inductive ParseOutcome where
  | raised
  | parsed (isUnrecognized : Bool) (otherName : String)
deriving DecidableEq, Repr

/-- The desired comparison result for an unrecognised unit named `selfName`
against an operand whose interpretation outcome is `po`. -/
def eqResult (selfName : String) (po : ParseOutcome) : Except UnitError EqResult :=
  match po with
  | .raised => .ok .notApplicable
  | .parsed isUnrecognized otherName =>
      .ok (if isUnrecognized && selfName == otherName then .isTrue else .isFalse)
-- pure-end

-- post-conditions-start
/-- The comparison result is exactly the value assigned by the rule: an
uninterpretable operand yields the not-applicable sentinel (never an escaping
error); a parsed operand yields true iff it is an unrecognised unit with a
matching name, else false. -/
def problem_spec_unrecognizedUnitEq
    (selfName : String) (po : ParseOutcome)
    (result : Except UnitError EqResult) : Prop :=
  result = eqResult selfName po
-- post-conditions-end

-- impl-start
def implementation_unrecognizedUnitEq
    (selfName : String) (po : ParseOutcome) : Except UnitError EqResult := Id.run do
  match po with
  | .raised =>
      return .ok .notApplicable
  | .parsed isUnrecognized otherName =>
      return .ok (if isUnrecognized && selfName == otherName then .isTrue else .isFalse)
-- impl-end

-- proof-start
theorem correct_unrecognizedUnitEq :
    ∀ (selfName : String) (po : ParseOutcome),
      problem_spec_unrecognizedUnitEq selfName po
        (implementation_unrecognizedUnitEq selfName po) := by
  intro selfName po
  unfold problem_spec_unrecognizedUnitEq implementation_unrecognizedUnitEq eqResult
  cases po <;> rfl
-- proof-end
