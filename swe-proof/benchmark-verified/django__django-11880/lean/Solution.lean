import Mathlib
-- imports-end

/-!
Duplicating a form field into an independent copy.

A form field bundles several components. Some are immutable scalars (modeled
here by `required`). Others are mutable containers — a widget object, a mapping
of error codes to messages, and a list of validators — each of which is a
distinct runtime object with its own identity (`ObjId`) in addition to its
contents.

Producing a duplicate of a field must yield a copy that is fully independent of
the original: each of its mutable containers is its OWN object, distinct in
identity from the original's, while carrying the SAME contents. Concretely, the
duplicate's widget, error-message mapping, and validator list must each be a
fresh object (a new identity), the error-message mapping and validator list must
have contents equal to the original's, and the immutable scalar components must
be preserved unchanged.

This independence is what lets two duplicates of one field be mutated in
isolation: changing one duplicate's error-message mapping must never be visible
through the other.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The duplication
-- of each mutable container (allocating a fresh object that carries the same
-- contents) and the preservation of the immutable scalar are modeled
-- structurally over the field's components, so no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- A runtime object's identity. Modeled as a `Nat` (an injective encoding of
the distinct object identities; only equality is observed). Two values are the
SAME object iff their `ObjId`s are equal. -/
abbrev ObjId := Nat

/-- An error-code → message mapping, restricted to its observable contents.
Codes and messages are distinct strings, modeled by injective `Nat` encodings;
only equality of contents is observed. -/
abbrev MsgDict := List (Nat × Nat)

/-- A form field, restricted to the touched components:
* `widgetId`  — the identity of the field's widget object;
* `errMsgId`  — the identity of the error-message mapping object;
* `errMsg`    — the contents of that mapping;
* `validId`   — the identity of the validator-list object;
* `validators`— the contents of that list;
* `required`  — a representative immutable scalar component. -/
structure FormField where
  widgetId : ObjId
  errMsgId : ObjId
  errMsg : MsgDict
  validId : ObjId
  validators : List Nat
  required : Bool
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The duplicate is independent of the original. Given the fresh object
identities `fw`, `fe`, `fv` produced when allocating the duplicate's widget,
error-message mapping, and validator list:

* each mutable container of the result carries its OWN (fresh) identity
  (`fw`, `fe`, `fv` respectively), so it is a distinct object from the
  original's container;
* the error-message mapping and the validator list have contents EQUAL to the
  original's (the copy preserves contents);
* the immutable scalar component is preserved unchanged.

The freshness of `fw`/`fe`/`fv` (distinctness from the original's identities) is
a precondition of `correct_duplicateField`. -/
def problem_spec_duplicateField
    (self : FormField) (fw fe fv : ObjId) (result : FormField) : Prop :=
  result.widgetId = fw ∧
  result.errMsgId = fe ∧
  result.errMsg = self.errMsg ∧
  result.validId = fv ∧
  result.validators = self.validators ∧
  result.required = self.required
-- post-conditions-end

-- impl-start
-- Build the duplicate. Start from a shallow copy of the original (every
-- component initially the SAME object), then replace each mutable container with
-- a freshly allocated object that carries the same contents: the widget gets
-- fresh identity fw; the error-message mapping gets fresh identity fe with the
-- original's contents; the validator list gets fresh identity fv with the
-- original's contents. The immutable scalar is left as carried by the shallow
-- copy.
def implementation_duplicateField
    (self : FormField) (fw fe fv : ObjId) : FormField := Id.run do
  let mut result := self
  result := { result with widgetId := fw }
  result := { result with errMsgId := fe, errMsg := self.errMsg }
  result := { result with validId := fv, validators := self.validators }
  return result
-- impl-end

-- proof-start
theorem correct_duplicateField :
    ∀ (self : FormField) (fw fe fv : ObjId),
      fw ≠ self.widgetId → fe ≠ self.errMsgId → fv ≠ self.validId →
      problem_spec_duplicateField self fw fe fv
        (implementation_duplicateField self fw fe fv) := by
  intro self fw fe fv _ _ _
  unfold problem_spec_duplicateField implementation_duplicateField
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
