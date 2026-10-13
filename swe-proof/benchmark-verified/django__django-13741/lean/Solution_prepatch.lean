import Mathlib
-- imports-end

/-!
Constructing a read-only form field that displays a stored secret summary and
must never be treated as editable, then deciding whether such a field reports a
change between its initial value and a submitted value.

The field is built from an optional caller-supplied "disabled" setting. When the
caller does not supply that setting, the field defaults to being disabled; when
the caller does supply it, the caller's choice is used verbatim. A disabled
field is shown but cannot be edited: any value the client submits is ignored in
favour of the field's initial value.

The change decision follows from that configuration:

  * a disabled field never reports a change (its effective value is always the
    initial value, so there is nothing to differ);
  * a field that is not disabled reports a change exactly when its initial value
    differs from the submitted value, where a missing value on either side is
    treated as the empty string.

The behavior is stated abstractly as an input→output relation over the optional
disabled setting and the (optional) initial and submitted values; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged outside callee is consumed as a contract. Recording the
-- effective disabled setting (the caller's value, or the default when none was
-- supplied) and the resulting change decision are modeled directly below, so
-- the spec needs no `opaque`/`axiom` callee property.
-- axioms-end

-- pure-start
/-- The observable outcome of constructing the field and asking it whether a
submission constitutes a change: the field's effective disabled setting, and the
change decision. -/
structure FieldOutcome where
  disabled : Bool
  changed : Bool
deriving DecidableEq, Repr

/-- Value-level equality of two optional values, treating a missing value as the
empty string. -/
def valEq (a b : Option String) : Bool := (a.getD "") == (b.getD "")
-- pure-end

-- post-conditions-start
/-- The outcome is fully pinned to the inputs:

  * `disabled` is the caller's supplied setting when present, and the default
    `true` when no setting was supplied (`disabledArg.getD true`);
  * `changed` is `false` whenever the field is disabled, and otherwise is `true`
    exactly when the initial and submitted values differ (missing ↦ empty
    string).

No output component is left free: both fields of the outcome are determined by
the inputs. -/
def problem_spec_passwordHashField
    (disabledArg : Option Bool) (initial data : Option String)
    (result : FieldOutcome) : Prop :=
  result.disabled = disabledArg.getD true ∧
  result.changed = (if result.disabled then false else !(valEq initial data))
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: the effective disabled setting defaults to `false`
-- when the caller supplies none (no default is applied), and the change decision
-- is hard-wired to `false` regardless of the values. So a default-constructed
-- field reports `disabled = false`, contradicting the spec clause that an
-- unsupplied setting defaults to `true`.
def implementation_passwordHashField
    (disabledArg : Option Bool) (initial data : Option String) : FieldOutcome :=
  Id.run do
  let disabled := disabledArg.getD false
  let mut changed := false
  return { disabled := disabled, changed := changed }
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl (the
-- `result.disabled = disabledArg.getD true` clause is violated when no setting
-- is supplied, and the change clause is violated for an enabled field whose
-- values differ).
theorem correct_passwordHashField :
    ∀ (disabledArg : Option Bool) (initial data : Option String),
      problem_spec_passwordHashField disabledArg initial data
        (implementation_passwordHashField disabledArg initial data) := by
  sorry
-- proof-end
