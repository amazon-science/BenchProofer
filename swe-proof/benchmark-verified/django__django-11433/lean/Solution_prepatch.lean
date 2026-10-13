import Mathlib
-- imports-end

/-!
Building a model object's field assignments from the resolved data of a bound
form.

The routine walks the model's fields in order and, for each one, decides whether
to assign the form's resolved value to that field or to leave the field holding
the value it already carries (its model-level default). A field is assigned its
resolved value exactly when all of the following hold:

* the field is editable and is not an auto-generated key field;
* the field has a resolved value available (it appears in the resolved data);
* if the caller restricted the work to an explicit set of field names, the
  field's name is in that set;
* if the caller supplied a non-empty set of names to skip, the field's name is
  not among them;
* it is NOT the case that the field both carries a model-level default AND had
  its value omitted from the submitted payload AND its resolved value is itself
  one of the field's "empty" sentinels. In other words, a field that has a
  default is left at that default only when no meaningful value was supplied for
  it; a non-empty resolved value always takes precedence over the default.

Assignments are emitted in two passes: first every eligible non-file field in
field order, then every eligible file field in field order (file fields are
deferred so that a later field's value is available when their value is
computed). Each emitted assignment records the field's name together with the
resolved value assigned to it; a field left at its default emits nothing.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. Every per-field predicate
-- the routine consults (editability, auto-key test, availability of a resolved
-- value, presence of a default, whether the value was omitted from the payload,
-- whether the resolved value is an empty sentinel, file-field test) is supplied
-- as a boolean field of the per-field input record; the assignment-selection
-- logic is spelled out concretely below.
-- axioms-end

-- pure-start
/-- The observable per-field state the routine reads on one loop iteration,
together with the resolved value that would be assigned. -/
structure FieldInput where
  /-- the field's name -/
  name : String
  /-- the field may be written by a form -/
  editable : Bool
  /-- the field is an auto-generated key field -/
  isAuto : Bool
  /-- a resolved value for this field is available -/
  inResolved : Bool
  /-- the field carries a model-level default -/
  hasDefault : Bool
  /-- the field's value was omitted from the submitted payload -/
  omitted : Bool
  /-- the resolved value is one of the field's "empty" sentinels -/
  resolvedEmpty : Bool
  /-- the field stores a file and is therefore deferred to the second pass -/
  isFile : Bool
  /-- the resolved value that would be assigned to the field -/
  resolvedValue : String
deriving Repr, DecidableEq

/-- Whether a field is assigned its resolved value (rather than left at its
default). Encodes the full chain of skip-conditions as a single conjunction. -/
def assignField (nameFilter : Option (List String)) (skipNames : List String)
    (f : FieldInput) : Bool :=
  f.editable && !f.isAuto && f.inResolved
    && (match nameFilter with
        | some names => names.contains f.name
        | none => true)
    && !(!skipNames.isEmpty && skipNames.contains f.name)
    && !(f.hasDefault && f.omitted && f.resolvedEmpty)

/-- One emitted assignment: the field's name paired with the value assigned. -/
def emit (f : FieldInput) : String × String := (f.name, f.resolvedValue)

/-- The assignments the routine performs, in execution order: eligible non-file
fields first (field order), then eligible file fields (field order). -/
def assignmentsFor (nameFilter : Option (List String)) (skipNames : List String)
    (fields : List FieldInput) : List (String × String) :=
  let kept := fields.filter (assignField nameFilter skipNames)
  (kept.filter (fun f => !f.isFile)).map emit
    ++ (kept.filter (fun f => f.isFile)).map emit
-- pure-end

-- post-conditions-start
/-- Input→output relation for building the field assignments.

Inputs:
* `nameFilter` — `none` if the caller imposed no field-name restriction, else
  `some names` to restrict work to those names;
* `skipNames`  — names to skip (effective only when non-empty);
* `fields`     — the model's fields, in order, each with its observable state.

The result is the exact sequence of `(name, value)` assignments performed, with
the file-field deferral reflected in the ordering. It is fully pinned: every
field that qualifies contributes its emitted assignment, every field that does
not contributes nothing, and the order is the two-pass order. -/
def problem_spec_bindFields (nameFilter : Option (List String))
    (skipNames : List String) (fields : List FieldInput)
    (result : List (String × String)) : Prop :=
  result = assignmentsFor nameFilter skipNames fields
-- post-conditions-end

-- impl-start
-- PRE-PATCH skeleton: a field carrying a model-level default whose value was
-- omitted from the submitted payload is left at its default REGARDLESS of the
-- resolved value. The check that the resolved value is itself an empty sentinel
-- is missing, so a meaningful resolved value is discarded in favor of the
-- default — contradicting `problem_spec_bindFields` for any defaulted, omitted
-- field whose resolved value is non-empty.
def implementation_bindFields (nameFilter : Option (List String))
    (skipNames : List String) (fields : List FieldInput) :
    List (String × String) := Id.run do
  let mut assigned : List (String × String) := []
  let mut fileFields : List (String × String) := []
  for f in fields do
    if !f.editable || f.isAuto || !f.inResolved then
      continue
    if let some names := nameFilter then
      if !names.contains f.name then
        continue
    if !skipNames.isEmpty && skipNames.contains f.name then
      continue
    if f.hasDefault && f.omitted then
      continue
    if f.isFile then
      fileFields := fileFields ++ [(f.name, f.resolvedValue)]
    else
      assigned := assigned ++ [(f.name, f.resolvedValue)]
  return assigned ++ fileFields
-- impl-end

-- proof-start
theorem correct_bindFields :
    ∀ (nameFilter : Option (List String)) (skipNames : List String)
      (fields : List FieldInput),
      problem_spec_bindFields nameFilter skipNames fields
        (implementation_bindFields nameFilter skipNames fields) := by
  sorry
-- proof-end
