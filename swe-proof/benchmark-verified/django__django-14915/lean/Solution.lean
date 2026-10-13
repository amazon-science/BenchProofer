import Mathlib
-- imports-end

/-!
Making a select-widget choice-value wrapper usable as a dictionary key / set
member.

A choice-value wrapper bundles a plain choice value together with the model
object it was produced from. Downstream user code commonly tests membership of
such a wrapper in a mapping or a set (e.g. `if value in {1: [...]}`), which
requires the wrapper to expose a hash digest.

Two facets are pinned here:

  * the wrapper IS usable as a key — obtaining its digest succeeds (it does not
    fail the way an un-keyable object would);
  * the digest is a deterministic function of the wrapped *value* alone — it is
    derived from the plain value and does NOT depend on the accompanying model
    object. Two wrappers that carry the same value therefore share a digest,
    whatever model objects (or absence thereof) they were built from.
-/

-- axioms-start
-- The wrapped value's own digest is computed by the standard, unchanged digest
-- operation for plain values — a deterministic function of the value. It is an
-- UNCHANGED callee the modeled behavior invokes (not the operation under
-- specification), so it is declared `opaque` (signature only) and used
-- identically in the spec and the implementation. The proof consumes no property
-- of it, so no `_prop` axiom is declared here; if the proof agent gets stuck it
-- may add one via the axiom-propose loop.
opaque valueHash : Int → Int
-- axioms-end

-- pure-start
/-- An opaque tag standing for an accompanying model object. Only its presence
or absence is ever observed by the modeled behavior; its content is irrelevant
to the digest, which is exactly the point being specified. -/
opaque ModelInstance : Type

/-- A choice-value wrapper: a plain value `val` together with the model object
`inst` it was produced from (absent when built without one). -/
structure ChoiceValue where
  val : Int
  inst : Option ModelInstance
-- pure-end

-- post-conditions-start
/-- The digest of a choice-value wrapper succeeds and equals the standard digest
of the wrapped value `m.val` alone.

Directive 5 (frame): the result is pinned entirely to `m.val`. The accompanying
model object `m.inst` is a read-only input the result must NOT depend on, so it
does not appear on the right-hand side — hence wrappers sharing a value share a
digest regardless of their model object. The `some` constructor records that the
digest is produced at all (a wrapper that could not be used as a key would have
no digest to report). -/
def problem_spec_choiceValueHash (m : ChoiceValue) (result : Option Int) : Prop :=
  result = some (valueHash m.val)
-- post-conditions-end

-- impl-start
def implementation_choiceValueHash (m : ChoiceValue) : Option Int := Id.run do
  -- the digest is the standard digest of the wrapped value; the accompanying
  -- model object is not consulted
  return some (valueHash m.val)
-- impl-end

-- proof-start
theorem correct_choiceValueHash :
    ∀ (m : ChoiceValue),
      problem_spec_choiceValueHash m (implementation_choiceValueHash m) := by
  intro m
  unfold problem_spec_choiceValueHash implementation_choiceValueHash
  rfl
-- proof-end
