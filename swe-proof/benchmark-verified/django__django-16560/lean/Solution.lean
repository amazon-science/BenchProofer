import Mathlib
-- imports-end

/-!
Customising the machine-readable error code carried by a data-integrity
constraint, alongside the human-readable message it can already carry.

A constraint may now be configured with an OPTIONAL error code (a short string).
Some constraints carry a concrete code; others carry none. This optional code is
threaded into three observable behaviors of a constraint, each pinned below:

  * VALIDATION ERROR — when a constraint checks a candidate value and detects a
    violation, it signals that violation by raising a validation error; the error
    carries the constraint's configured code (or no code when none is configured).
    When no violation is detected, nothing is raised.

  * EQUALITY — two constraints are considered equal exactly when their
    pre-existing comparison payload (everything compared before) matches AND their
    optional codes match. Two otherwise-identical constraints carrying different
    codes are therefore not equal; carrying the same code (including both having
    none) keeps them equal.

  * RECONSTRUCTION DATA — the keyword data used to rebuild a constraint surfaces
    the code exactly when one is configured, and omits it entirely when none is
    configured (mirroring how the existing message is handled).

Each behavior is a TOTAL function of its inputs and is fully pinned: no output
component is left free.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom and none is referenced as a
-- deep model. Each modeled behavior is a total computation over the constraint's
-- own data: the optional code, the pre-existing comparison payload (collapsed to a
-- single comparison key, unchanged by this work), and a boolean recording whether
-- the constraint's own (unchanged) detection found a violation. Hence no
-- `opaque`/`axiom` declaration is required.
-- axioms-end

-- pure-start
/-- The comparison-relevant payload of a constraint: its pre-existing comparison
key (name plus the constraint's defining data and message, collapsed to one key
that is compared unchanged) together with the optional error code. -/
structure Constr where
  rest : String
  code : Option String
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The validation-error behavior is TOTAL and fully pinned.

  * When the constraint detects a violation (`violated = true`), it raises an
    error (`some _`) whose carried code is exactly the configured code.
  * When no violation is detected (`violated = false`), nothing is raised
    (`none`).

The carried code is pinned to the configured `code`, not left free. -/
def problem_spec_validateError
    (violated : Bool) (code : Option String) (result : Option (Option String)) : Prop :=
  result = (if violated then some code else none)
-- post-conditions-end

-- post-conditions-start
/-- Equality is pinned to BOTH the pre-existing comparison payload AND the optional
code: no output freedom remains. Equal exactly when both agree. -/
def problem_spec_constraintEq (a b : Constr) (result : Bool) : Prop :=
  result = ((a.rest == b.rest) && (a.code == b.code))
-- post-conditions-end

-- post-conditions-start
/-- The reconstruction data surfaces the code exactly when one is configured: the
result is `some c` when a code `c` is configured and `none` when none is. -/
def problem_spec_serializedCode (code : Option String) (result : Option String) : Prop :=
  result = code
-- post-conditions-end

-- impl-start
def implementation_validateError
    (violated : Bool) (code : Option String) : Option (Option String) := Id.run do
  -- A detected violation is signalled by raising an error that carries the
  -- configured code; no violation raises nothing.
  if violated then
    return some code
  return none
-- impl-end

-- impl-start
def implementation_constraintEq (a b : Constr) : Bool := Id.run do
  return (a.rest == b.rest) && (a.code == b.code)
-- impl-end

-- impl-start
def implementation_serializedCode (code : Option String) : Option String := Id.run do
  -- Include the code in the reconstruction data only when one is configured.
  match code with
  | some c => return some c
  | none   => return none
-- impl-end

-- proof-start
theorem correct_validateError :
    ∀ (violated : Bool) (code : Option String),
      problem_spec_validateError violated code
        (implementation_validateError violated code) := by
  intro violated code
  unfold problem_spec_validateError implementation_validateError
  cases violated <;> rfl
-- proof-end

-- proof-start
theorem correct_constraintEq :
    ∀ (a b : Constr),
      problem_spec_constraintEq a b (implementation_constraintEq a b) := by
  intro a b
  rfl
-- proof-end

-- proof-start
theorem correct_serializedCode :
    ∀ (code : Option String),
      problem_spec_serializedCode code (implementation_serializedCode code) := by
  intro code
  unfold problem_spec_serializedCode implementation_serializedCode
  cases code <;> rfl
-- proof-end
