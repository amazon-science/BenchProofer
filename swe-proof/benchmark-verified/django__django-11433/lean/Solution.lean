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
def implementation_bindFields (nameFilter : Option (List String))
    (skipNames : List String) (fields : List FieldInput) :
    List (String × String) := Id.run do
  let mut assigned : List (String × String) := []
  let mut fileFields : List (String × String) := []
  for f in fields do
    -- Skip fields that cannot or need not receive a resolved value.
    if !f.editable || f.isAuto || !f.inResolved then
      continue
    -- Honor an explicit field-name restriction.
    if let some names := nameFilter then
      if !names.contains f.name then
        continue
    -- Honor a non-empty set of names to skip.
    if !skipNames.isEmpty && skipNames.contains f.name then
      continue
    -- Leave a defaulted field at its default only when no meaningful value was
    -- supplied: the value was omitted from the payload and the resolved value is
    -- itself an empty sentinel.
    if f.hasDefault && f.omitted && f.resolvedEmpty then
      continue
    -- Defer file fields to a second pass; assign everything else now.
    if f.isFile then
      fileFields := fileFields ++ [(f.name, f.resolvedValue)]
    else
      assigned := assigned ++ [(f.name, f.resolvedValue)]
  return assigned ++ fileFields
-- impl-end


-- proof-start
/-- The per-field state transition of the desugared loop: given the current
`(assigned, fileFields)` pair and a field, leave the state unchanged if the
field fails `assignField`, else append its emitted assignment to the file
accumulator (if it is a file field) or to the non-file accumulator. -/
def step (nf : Option (List String)) (sk : List String)
    (st : List (String × String) × List (String × String)) (f : FieldInput) :
    List (String × String) × List (String × String) :=
  if assignField nf sk f then
    (if f.isFile then (st.1, st.2 ++ [emit f]) else (st.1 ++ [emit f], st.2))
  else st

/-- Invariant relating the two accumulators after processing a prefix `p` to the
filtered-mapped sublists of the kept fields of `p`. -/
def FoldInv (nf : Option (List String)) (sk : List String)
    (p : List FieldInput) (assigned fileFields : List (String × String)) : Prop :=
  assigned = ((p.filter (assignField nf sk)).filter (fun f => !f.isFile)).map emit
    ∧ fileFields = ((p.filter (assignField nf sk)).filter (fun f => f.isFile)).map emit

/-- Generalized-accumulator form of the desugared implementation loop: running the
`for` loop from an arbitrary initial `(assigned, fileFields)` pair yields exactly the
left fold of `step` over the fields from that pair. This isolates the fragile
`Id.run`/`forIn`→`foldl` bridge behind a clean statement that inducts on `fields`
generalizing the accumulators, so `impl_as_foldl` follows by instantiating at `([],[])`. -/
theorem impl_loop_eq_foldl (nameFilter : Option (List String)) (skipNames : List String)
    (fields : List FieldInput) (a0 ff0 : List (String × String)) :
    (Id.run do
      let mut assigned := a0
      let mut fileFields := ff0
      for f in fields do
        if !f.editable || f.isAuto || !f.inResolved then
          continue
        if let some names := nameFilter then
          if !names.contains f.name then
            continue
        if !skipNames.isEmpty && skipNames.contains f.name then
          continue
        if f.hasDefault && f.omitted && f.resolvedEmpty then
          continue
        if f.isFile then
          fileFields := fileFields ++ [(f.name, f.resolvedValue)]
        else
          assigned := assigned ++ [(f.name, f.resolvedValue)]
      return (assigned, fileFields))
    = fields.foldl (step nameFilter skipNames) (a0, ff0) := by
  simp only [Id.run, bind, pure, ← apply_ite ForInStep.yield]
  rcases nameFilter with _ | names <;>
    simp only [← apply_ite ForInStep.yield, List.forIn_yield_eq_foldl] <;>
    · induction fields generalizing a0 ff0 with
      | nil => rfl
      | cons f fs ih =>
        simp only [List.foldl_cons, step, assignField]
        rw [ih]
        clear ih
        congr 1 <;>
          simp only [emit] <;>
          split_ifs <;>
          grind

theorem impl_as_foldl (nameFilter : Option (List String)) (skipNames : List String)
    (fields : List FieldInput) :
    implementation_bindFields nameFilter skipNames fields
      = (fun st => st.1 ++ st.2) (fields.foldl (step nameFilter skipNames) ([], [])) := by
  rw [← impl_loop_eq_foldl nameFilter skipNames fields [] []]
  rfl

theorem guards_iff_assignField (nameFilter : Option (List String))
    (skipNames : List String) (f : FieldInput) :
    (¬(!f.editable || f.isAuto || !f.inResolved) ∧
      (match nameFilter with | some names => names.contains f.name | none => True) ∧
      ¬(!skipNames.isEmpty && skipNames.contains f.name) ∧
      ¬(f.hasDefault && f.omitted && f.resolvedEmpty))
    ↔ assignField nameFilter skipNames f = true := by
  cases nameFilter <;>
    simp only [assignField, Bool.and_eq_true, Bool.or_eq_true, Bool.not_eq_true,
      Bool.not_eq_true', not_or, not_and] <;>
    (cases f.editable <;> cases f.isAuto <;> cases f.inResolved <;>
      cases f.hasDefault <;> cases f.omitted <;> cases f.resolvedEmpty <;>
      cases skipNames.isEmpty <;> cases skipNames.contains f.name <;> simp_all)

theorem foldl_step_general (nf : Option (List String)) (sk : List String)
    (p : List FieldInput) (a0 ff0 : List (String × String)) :
    p.foldl (step nf sk) (a0, ff0)
      = (a0 ++ ((p.filter (assignField nf sk)).filter (fun f => !f.isFile)).map emit,
         ff0 ++ ((p.filter (assignField nf sk)).filter (fun f => f.isFile)).map emit) := by
  induction p generalizing a0 ff0 with
  | nil => simp
  | cons f rest ih =>
    simp only [List.foldl_cons, List.filter_cons, step]
    by_cases h : assignField nf sk f = true
    · by_cases hf : f.isFile = true
      · simp [h, hf, ih, List.append_assoc]
      · simp only [Bool.not_eq_true] at hf
        simp [h, hf, ih, List.append_assoc]
    · simp only [Bool.not_eq_true] at h
      simp [h, ih]

theorem FoldInv_final (nf : Option (List String)) (sk : List String)
    (fields : List FieldInput) :
    fields.foldl (step nf sk) ([], [])
      = (((fields.filter (assignField nf sk)).filter (fun f => !f.isFile)).map emit,
         ((fields.filter (assignField nf sk)).filter (fun f => f.isFile)).map emit) := by
  simpa using foldl_step_general nf sk fields [] []

theorem correct_bindFields :
    ∀ (nameFilter : Option (List String)) (skipNames : List String)
      (fields : List FieldInput),
      problem_spec_bindFields nameFilter skipNames fields
        (implementation_bindFields nameFilter skipNames fields) := by
  intro nameFilter skipNames fields
  unfold problem_spec_bindFields assignmentsFor
  rw [impl_as_foldl, FoldInv_final]

-- proof-end
