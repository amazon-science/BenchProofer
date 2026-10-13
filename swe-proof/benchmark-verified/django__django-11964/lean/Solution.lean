import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The string rendering of an
-- enumerated member's underlying value is modeled DEEPLY (see `pyStr` below)
-- rather than axiomatized, so its standard-library reference (Python's textual
-- conversion of a value) is validated as an A-reference by G-AX. The proof agent
-- may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The underlying value carried by an enumerated member. It is either a textual
value or an integral value (the two value kinds the modeled members use). -/
inductive MemberValue where
  | text : String → MemberValue
  | num  : Int → MemberValue
deriving DecidableEq

/-- Standard textual conversion of a member value: a textual value renders as
itself; an integral value renders as its decimal numeral. -/
def pyStr : MemberValue → String
  | .text s => s
  | .num n  => toString n

/-- An enumerated member, modeling only the fields the behavior touches: a
fully-qualified textual identifier of the member (its owner-qualified name) and
the underlying value it carries. -/
structure EnumMember where
  qualifiedName : String
  value : MemberValue
-- pure-end

-- post-conditions-start
/-- The textual rendering of an enumerated member equals the textual rendering of
its underlying value. -/
def problem_spec_memberStr (m : EnumMember) (result : String) : Prop :=
  result = pyStr m.value
-- post-conditions-end

-- impl-start
def implementation_memberStr (m : EnumMember) : String := Id.run do
  return pyStr m.value
-- impl-end

-- proof-start
theorem correct_memberStr : ∀ m : EnumMember,
    problem_spec_memberStr m (implementation_memberStr m) := by
  intro m
  unfold problem_spec_memberStr implementation_memberStr
  rfl
-- proof-end
