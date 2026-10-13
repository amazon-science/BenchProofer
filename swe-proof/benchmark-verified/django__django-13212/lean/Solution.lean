import Mathlib
-- imports-end

/-!
Surfacing the rejected input inside a failed check's error context.

A value check inspects one input and reaches a verdict: the input is either
acceptable or not. When it is acceptable, the check signals success and produces
no error context. When it is NOT acceptable, the check signals failure and
produces an error context: a finite sequence of named substitution parameters
(an insertion-ordered mapping) that a customizable, human-facing message may
interpolate.

The desired behavior concerns only the failure case. A rejection's error context
carries the parameters intrinsic to that particular check (for instance a size
bound, or the offending file extension). It is often useful for a custom message
to additionally name the rejected input itself — e.g. to report which specific
entry, among many checked in bulk, was the bad one. So on a rejection the error
context must also bind the substitution name `value` to the rejected input.

The contract on a rejection's parameter sequence is therefore fully determined:

  * every intrinsic parameter the check supplies is preserved unchanged and in
    order (the underlying substitution mapping is insertion-ordered, and the
    intrinsic entries come first, exactly as the check supplied them);
  * the binding of the name `value` to exactly the rejected input is appended
    after them, as the final entry;
  * nothing else appears — no spurious parameter, and no shadowed or duplicate
    entry hiding anywhere in the sequence.

The acceptance verdict and the intrinsic parameters of a check are themselves
independent of this contract; the obligation is on the parameter sequence
accompanying a rejection.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Whether an
-- input is acceptable is the check's own verdict, modeled as a Boolean input
-- (`accepted`) and carried as data. The intrinsic parameters a check supplies
-- are likewise carried as an input (`baseParams`). Hence no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- The substitution name bound to the rejected input. (`%(value)s` in a custom
message refers to this name.) -/
def valueKey : String := "value"
-- pure-end

-- post-conditions-start
/-- The check-outcome contract, relating one input to the error context it
produces.

`result = none` means the input was accepted (no error context). `result =
some params` means the input was rejected with the substitution-parameter
sequence `params` (the entries of the insertion-ordered substitution mapping,
in order).

* When the verdict is acceptance, no error context is produced.
* When the verdict is rejection, the parameter sequence is EXACTLY the
  intrinsic parameters the check supplied, in order, with the binding of
  `valueKey` to the rejected input appended as the final entry:
  `baseParams ++ [(valueKey, value)]`.

Pinning the whole sequence (not merely its key-lookup view) leaves no component
of a rejection's parameter set free: each intrinsic parameter is preserved
verbatim and in position, the `value` binding is present and holds exactly the
rejected input, and no spurious, duplicate, or shadowed entry can appear
anywhere. The familiar lookup facts follow as corollaries: under the theorem's
precondition (`baseParams` does not bind `valueKey`),
`params.lookup valueKey = some value` and `params.lookup k = baseParams.lookup
k` for every `k ≠ valueKey`. -/
def problem_spec_checkOutcome
    (value : String) (accepted : Bool) (baseParams : List (String × String))
    (result : Option (List (String × String))) : Prop :=
  (accepted = true → result = none) ∧
  (accepted = false → result = some (baseParams ++ [(valueKey, value)]))
-- post-conditions-end

-- impl-start
def implementation_checkOutcome
    (value : String) (accepted : Bool)
    (baseParams : List (String × String)) : Option (List (String × String)) := Id.run do
  if accepted then
    -- Input is acceptable: succeed, no error context.
    return none
  -- Input is rejected: build the error context, binding `value` to the rejected
  -- input alongside the intrinsic parameters this check already supplies.
  return some (baseParams ++ [(valueKey, value)])
-- impl-end

-- proof-start
theorem correct_checkOutcome :
    ∀ (value : String) (accepted : Bool) (baseParams : List (String × String)),
      baseParams.lookup valueKey = none →
      problem_spec_checkOutcome value accepted baseParams
        (implementation_checkOutcome value accepted baseParams) := by
  intro value accepted baseParams _hbase
  unfold problem_spec_checkOutcome implementation_checkOutcome
  cases accepted with
  | true =>
    exact ⟨fun _ => rfl, fun h => absurd h (by simp)⟩
  | false =>
    exact ⟨fun h => absurd h (by simp), fun _ => rfl⟩
-- proof-end
