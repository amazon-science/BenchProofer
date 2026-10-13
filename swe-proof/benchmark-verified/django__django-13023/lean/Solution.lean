import Mathlib
-- imports-end

/-!
Interpreting an arbitrary input value as a decimal number.

A model field that stores decimal numbers must turn whatever value it is handed
into a decimal. The conversion follows a definite precedence:

  * a missing value (the absence of any value) passes straight through unchanged;
  * a value that is already a floating-point number is converted directly to a
    decimal;
  * any other value is interpreted as a decimal number.

That last interpretation can fail in several different low-level ways, depending
on the nature of the offending value (a value that looks numeric but is not a
well-formed decimal literal, a value whose very type cannot stand for a number at
all, or a structurally malformed value). However it fails, the failure means the
same thing to a caller: the supplied value is not a usable decimal number.

The contract is therefore that EVERY low-level failure of that interpretation is
reported uniformly, as one and the same validation error — so a caller never has
to discriminate among, or be surprised by, the assorted low-level failure modes.
A value that does interpret cleanly (and the missing / floating-point cases)
returns normally. The four cases are exhaustive and mutually exclusive, so the
outcome is fully determined for every input.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The conversion
-- of a value to a decimal number is modeled DEEPLY as a classification of the
-- input (whether the conversion succeeds, and if not, which kind of low-level
-- failure it produces); the floating-point branch is modeled as a normal
-- return. There is no `opaque`/`axiom` callee contract the proof consumes.
-- axioms-end

-- pure-start
/-- The way an attempt to interpret a non-missing, non-floating-point value as a
decimal number can fail at the low level. The three kinds reflect the distinct
natures of an unusable value; the contract treats them identically. -/
inductive ConvError where
  /-- a value that looks number-like but is not a well-formed decimal literal -/
  | notANumber
  /-- a value whose type cannot represent a number at all -/
  | unsupportedType
  /-- a structurally malformed value -/
  | malformedValue
deriving DecidableEq, Repr

/-- An input value, observed through the only features the conversion inspects:
whether it is the missing value, whether it is a floating-point number, and — for
any other value — whether interpreting it as a decimal succeeds (`none`) or fails
with a low-level error of some kind (`some e`). The three features are read in
that precedence order. -/
structure Value where
  /-- the value is missing (the absence of any value) -/
  isNone : Bool
  /-- the value is a floating-point number (consulted only when not missing) -/
  isFloat : Bool
  /-- how interpreting the value as a decimal behaves (consulted only when the
  value is neither missing nor floating-point): `none` = succeeds, `some e` =
  fails with a low-level error of kind `e` -/
  conv : Option ConvError
deriving Repr

/-- The observable outcome of the conversion. -/
inductive Outcome where
  /-- a value is returned normally (a decimal, or the missing value unchanged) -/
  | returned
  /-- a uniform validation error is reported -/
  | validationError
  /-- a low-level failure escapes the conversion uncaught -/
  | propagated
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The outcome of interpreting `v` as a decimal number:

  * a missing value returns normally;
  * a non-missing floating-point value returns normally;
  * a non-missing, non-floating-point value that interprets cleanly returns
    normally;
  * a non-missing, non-floating-point value whose interpretation fails in ANY
    low-level way is reported as a validation error.

The four cases are exhaustive and mutually exclusive (directive 5 frame: the
outcome is pinned in every case; directive 8: each outcome is grounded in the
classification of the actual input `v`, with no low-level failure left to escape
uncaught). -/
def problem_spec_toPython (v : Value) (result : Outcome) : Prop :=
  (v.isNone = true → result = Outcome.returned) ∧
  (v.isNone = false → v.isFloat = true → result = Outcome.returned) ∧
  (v.isNone = false → v.isFloat = false → v.conv = none → result = Outcome.returned) ∧
  (v.isNone = false → v.isFloat = false → v.conv.isSome = true →
      result = Outcome.validationError)
-- post-conditions-end

-- impl-start
def implementation_toPython (v : Value) : Outcome := Id.run do
  if v.isNone then
    return Outcome.returned
  if v.isFloat then
    return Outcome.returned
  match v.conv with
  | none => return Outcome.returned
  | some _ => return Outcome.validationError
-- impl-end

-- proof-start
theorem correct_toPython :
    ∀ (v : Value), problem_spec_toPython v (implementation_toPython v) := by
  intro v
  unfold problem_spec_toPython implementation_toPython
  refine ⟨?_, ?_, ?_, ?_⟩ <;> intro h1
  · simp only [Id.run, h1, if_true]; rfl
  · intro h2; simp only [Id.run, h1, h2, Bool.false_eq_true, if_false]; rfl
  · intro h2 h3
    simp only [Id.run, h1, h2, Bool.false_eq_true, if_false, h3]; rfl
  · intro h2 h3
    cases hcv : v.conv with
    | none => rw [hcv] at h3; simp at h3
    | some e => simp only [Id.run, h1, h2, Bool.false_eq_true, if_false]; rfl
-- proof-end
