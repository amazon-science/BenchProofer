import Mathlib
-- imports-end

/-!
Validating per-sample-weight support across an ensemble's roster of named
components.

An ensemble holds an ordered roster of `(name, component)` slots. When the caller
supplies per-sample weights, the ensemble must first confirm that every component
that will actually be trained is able to consume those weights. A slot may also be
empty (its component is absent), in which case there is nothing to train there and
nothing to validate.

The validation walks the roster in order. An empty slot contributes nothing and is
passed over. For a present component, the roster is accepted only if that component
accepts per-sample weights; the first present component that does not accept them
stops the walk and the roster is rejected, identified by that component's name. If
the walk reaches the end without rejecting, the roster is accepted.

So the outcome is acceptance exactly when every PRESENT component accepts
per-sample weights, and otherwise rejection naming the first present component
that does not — empty slots never affecting the outcome.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Whether a present
-- component accepts per-sample weights is an unchanged boolean observation; it
-- enters as the grounded input flag carried in each present slot. The modeled
-- behavior — walking the roster, passing over empty slots, and rejecting at the
-- first present component that does not accept weights — is spelled out directly.
-- No `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The rejection message naming the offending component. -/
def errMsg (name : String) : String :=
  "Underlying estimator '" ++ name ++ "' does not support sample weights."

/-- Reference walk of the roster: empty slots (`none`) are passed over; a present
component (`some accepts`) is accepted iff `accepts` is `true`; the first present
component with `accepts = false` rejects the whole roster, identified by its name.
Front-recursive so the proof can pair it with the accumulator `for` loop. -/
def validateRoster : List (String × Option Bool) → Except String Unit
  | [] => Except.ok ()
  | (_, none) :: rest => validateRoster rest
  | (_, some true) :: rest => validateRoster rest
  | (name, some false) :: _ => Except.error (errMsg name)
-- pure-end

-- post-conditions-start
/-- The validation outcome is exactly the reference walk of the roster: acceptance
(`Except.ok ()`) iff every present component accepts per-sample weights, otherwise
rejection (`Except.error`) naming the first present component that does not. Empty
slots never affect the outcome. -/
def problem_spec_checkWeightSupport
    (estimators : List (String × Option Bool)) (result : Except String Unit) : Prop :=
  result = validateRoster estimators
-- post-conditions-end

-- impl-start
def implementation_checkWeightSupport
    (estimators : List (String × Option Bool)) : Except String Unit := Id.run do
  for slot in estimators do
    let (name, step) := slot
    match step with
    | none => return Except.error (errMsg name)
    | some accepts =>
      if accepts then
        pure ()
      else
        return Except.error (errMsg name)
  return Except.ok ()
-- impl-end

-- proof-start
theorem correct_checkWeightSupport :
    ∀ (estimators : List (String × Option Bool)),
      problem_spec_checkWeightSupport estimators
        (implementation_checkWeightSupport estimators) := by
  intro estimators
  unfold problem_spec_checkWeightSupport implementation_checkWeightSupport
  induction estimators with
  | nil => rfl
  | cons hd tl ih =>
    obtain ⟨name, step⟩ := hd
    cases step with
    | none => simpa using ih
    | some b => cases b <;> simpa using ih
-- proof-end
