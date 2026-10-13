import Mathlib
-- imports-end

/-!
Reporting the offending input when a single-choice field backed by a record set
rejects a submitted value.

A field whose permitted answers come from a stored collection coerces a raw
submitted value into one of those answers. The coercion has three outcomes:

  * the submission is one of the recognised "no answer" sentinels — the field
    yields an empty result and no error;
  * the submission resolves to exactly one stored answer — the field yields that
    answer;
  * the submission resolves to no stored answer — the field rejects it with a
    validation error.

The validation error carries a constant error code and a human-readable message
template configured for the rejection case. A template may refer to the rejected
value through a named placeholder. For that placeholder to render, the error must
ALSO carry the binding of that name to the actual submitted value. The desired
behavior is that a rejection always reports the offending value: the error's
parameter bindings map the value-placeholder name to exactly the submission that
was rejected, so a caller-supplied message naming that placeholder shows the
value the caller actually sent.

Inputs:
  * `invalidMessage` — the message template used for a rejected submission;
  * `emptyValues`    — the recognised "no answer" sentinels;
  * `value`          — the submitted value;
  * `lookup`         — the resolution of the submission against the stored
                       collection: `some r` when it resolves to the stored
                       answer `r`, `none` when it resolves to nothing (the
                       resolution attempt failed).
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The resolution
-- of a submission against the stored collection is an UNCHANGED dependency whose
-- observable outcome (`some answer` / `none`) enters as the plain `lookup` datum;
-- the recognised "no answer" sentinels enter as the plain `emptyValues` datum.
-- The only modeled operation — assembling the rejection report so it carries the
-- offending value — is modeled directly over that data, so no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- A submitted value. Modeled as a `String` (the raw textual submission); only
its identity is observed. -/
abbrev Val := String

/-- The identity of a stored answer the submission resolves to (e.g. its primary
key). Only its identity is observed. -/
abbrev Resolved := Nat

/-- A validation error report, restricted to the touched fields:
* `messageTemplate` — the human-readable message template for the rejection;
* `code` — the machine-readable rejection code;
* `params` — the named parameter bindings the template may interpolate. -/
structure ChoiceError where
  messageTemplate : String
  code : String
  params : List (String × Val)
deriving DecidableEq, Repr

/-- The constant rejection code for an unrecognised submission. -/
def invalidChoiceCode : String := "invalid_choice"

/-- The placeholder name a message template uses to refer to the offending
submission. -/
def valueParamName : String := "value"
-- pure-end

-- post-conditions-start
/-- The coercion outcome is fully pinned to the inputs:

  * a submission among the recognised sentinels yields the empty result with no
    error;
  * a submission that resolves to a stored answer yields exactly that answer;
  * a submission that resolves to nothing is rejected with a validation error
    carrying the configured template, the constant rejection code, AND a single
    parameter binding mapping the value-placeholder name to the offending
    submission itself.

The three cases cover every input, so no component of the result is left free. -/
def problem_spec_coerceChoice
    (invalidMessage : String) (emptyValues : List Val)
    (value : Val) (lookup : Option Resolved)
    (result : Except ChoiceError (Option Resolved)) : Prop :=
  (value ∈ emptyValues → result = Except.ok none) ∧
  (value ∉ emptyValues → ∀ r, lookup = some r → result = Except.ok (some r)) ∧
  (value ∉ emptyValues → lookup = none →
      result = Except.error
        { messageTemplate := invalidMessage,
          code := invalidChoiceCode,
          params := [(valueParamName, value)] })
-- post-conditions-end

-- impl-start
def implementation_coerceChoice
    (invalidMessage : String) (emptyValues : List Val)
    (value : Val) (lookup : Option Resolved) :
    Except ChoiceError (Option Resolved) := Id.run do
  if value ∈ emptyValues then
    return Except.ok none
  match lookup with
  | some r => return Except.ok (some r)
  | none =>
      return Except.error
        { messageTemplate := invalidMessage,
          code := invalidChoiceCode,
          params := [] }
-- impl-end

-- proof-start
theorem correct_coerceChoice :
    ∀ (invalidMessage : String) (emptyValues : List Val)
      (value : Val) (lookup : Option Resolved),
      problem_spec_coerceChoice invalidMessage emptyValues value lookup
        (implementation_coerceChoice invalidMessage emptyValues value lookup) := by
  intro invalidMessage emptyValues value lookup
  unfold problem_spec_coerceChoice implementation_coerceChoice
  refine ⟨?_, ?_, ?_⟩
  · intro hmem
    simp only [Id.run, hmem, if_pos]
    rfl
  · intro hnmem r hlk
    simp only [Id.run, if_neg hnmem, hlk]
    rfl
  · intro hnmem hlk
    simp only [Id.run, if_neg hnmem, hlk]
    rfl
-- proof-end
