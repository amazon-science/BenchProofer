import Mathlib
-- imports-end

/-!
Deciding whether a file-upload input element should advertise itself as
*required* in the rendered HTML.

A form input element carries the HTML `required` marker according to a base
rule: a non-hidden input is, in principle, required (a hidden input never is).

For an input that accepts a file, there is an extra consideration. When an
initial value is already present (for example a file already stored on the
object being edited), the element must NOT be marked required: the user is
allowed to leave the field blank and keep the existing value. A truthy initial
value therefore suppresses the required marker even when the base rule would
otherwise request it.

The desired rule for a file input is thus:

  * if the input is hidden, it is never required;
  * otherwise, it is required exactly when no initial value is present;
  * a present (truthy) initial value always suppresses the required marker.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The base rule
-- (a non-hidden input is required) is modeled directly as a structural predicate
-- on the observable inputs (hidden-ness, presence of an initial value), so no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The element is marked required exactly when the base rule applies (the input
is not hidden) AND no initial value is present (the initial value is not truthy).

* `isHidden` — whether the input element is hidden;
* `initialPresent` — whether a truthy initial value is already present;
* `result` — whether the rendered element should carry the required marker. -/
def problem_spec_useRequiredAttribute
    (isHidden initialPresent : Bool) (result : Bool) : Prop :=
  result = (!isHidden && !initialPresent)
-- post-conditions-end

-- impl-start
def implementation_useRequiredAttribute
    (isHidden initialPresent : Bool) : Bool := Id.run do
  return (!isHidden) && (!initialPresent)
-- impl-end

-- proof-start
theorem correct_useRequiredAttribute :
    ∀ (isHidden initialPresent : Bool),
      problem_spec_useRequiredAttribute isHidden initialPresent
        (implementation_useRequiredAttribute isHidden initialPresent) := by
  intro isHidden initialPresent
  unfold problem_spec_useRequiredAttribute implementation_useRequiredAttribute
  rfl
-- proof-end
