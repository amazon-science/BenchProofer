import Mathlib
-- imports-end

/-!
Deciding whether a queryset's `in_bulk` may key on a given `field_name`.

`in_bulk` builds a mapping from a field's value to the object carrying it; this
only makes sense when the chosen field takes a distinct value on each row. The
method therefore first checks that `field_name` names a field guaranteed unique
across all rows, and rejects the call with an error (naming the offending field)
when it does not.

A field name is acceptable when ANY of the following holds:

  * it is the primary key (`"pk"`);
  * the field itself is declared unique;
  * it is the single field covered by an *unconditional* `UniqueConstraint`
    declared on the model — a constraint that spans exactly that one field and
    applies to every row (no partial condition).

Otherwise the field name is not acceptable and the call is rejected. The rule is
a total, exhaustive predicate of the field name, the field's own uniqueness, and
the model's unique constraints, so the outcome is fully determined for every
input.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision
-- reads only the field's own uniqueness flag (supplied as an input observable),
-- and inspects the model's unconditional unique constraints that span exactly
-- one field, to collect the field names they each cover. Resolving the
-- constraint set to its unconditional members and projecting the single-field
-- ones are modeled directly (list filters/maps over the constraint records), so
-- no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A unique constraint declared on a model, observed through the components the
acceptability rule reads: the field names it spans, and whether it is partial
(applies only to a subset of rows via a condition) rather than total. -/
structure UniqueConstraint where
  /-- the field names this constraint covers -/
  fields : List String
  /-- `true` when the constraint is conditional/partial (does not apply to every
  row); only unconditional constraints guarantee uniqueness across all rows -/
  isPartial : Bool
deriving DecidableEq, Repr

/-- A model field, observed through the only component the rule reads: whether
the field is itself declared unique. -/
structure FieldInfo where
  /-- `true` when the field carries its own uniqueness declaration -/
  unique : Bool
deriving DecidableEq, Repr

/-- The field names that are each the sole field of an unconditional unique
constraint: from the unconditional constraints (`isPartial = false`) that span
exactly one field, take that one field name. These names are guaranteed unique
across all rows even though the field is not individually flagged unique. -/
def singleFieldUniqueConstraintFields (cs : List UniqueConstraint) : List String :=
  (cs.filter (fun c => !c.isPartial && c.fields.length == 1)).map (fun c => c.fields.headD "")
-- pure-end

-- post-conditions-start
/-- A field name is acceptable to key on exactly when ANY of three independent
conditions holds. Stated structurally over the inputs (NOT via the implementation
helper) so the postcondition is dischargeable only by the real computation:

  * it is the primary key (`"pk"`); or
  * the field is itself declared unique; or
  * some unconditional unique constraint on the model spans exactly this one
    field. -/
def fieldNameAcceptable (fieldName : String) (fld : FieldInfo)
    (cs : List UniqueConstraint) : Prop :=
  fieldName = "pk" ∨ fld.unique = true ∨
    (∃ c ∈ cs, c.isPartial = false ∧ c.fields = [fieldName])

/-- The outcome of the field-name acceptability check that guards `in_bulk`:

  * when the field name is acceptable the call proceeds (`Except.ok ()`);
  * otherwise the call fails with an error naming the offending field
    (`Except.error fieldName`).

The two cases are exhaustive and mutually exclusive (they partition on
`fieldNameAcceptable`), so the result is fully determined for every input. -/
def problem_spec_inBulk (fieldName : String) (fld : FieldInfo) (cs : List UniqueConstraint)
    (result : Except String Unit) : Prop :=
  (fieldNameAcceptable fieldName fld cs    → result = Except.ok ()) ∧
  (¬ fieldNameAcceptable fieldName fld cs  → result = Except.error fieldName)
-- post-conditions-end

-- impl-start
def implementation_inBulk (fieldName : String) (fld : FieldInfo) (cs : List UniqueConstraint) :
    Except String Unit := Id.run do
  let uniqueFields := singleFieldUniqueConstraintFields cs
  if fieldName != "pk" && !fld.unique && !(uniqueFields.contains fieldName) then
    return Except.error fieldName
  return Except.ok ()
-- impl-end

-- proof-start
theorem correct_inBulk :
    ∀ (fieldName : String) (fld : FieldInfo) (cs : List UniqueConstraint),
      problem_spec_inBulk fieldName fld cs (implementation_inBulk fieldName fld cs) := by
  intro fieldName fld cs
  have hmem : (singleFieldUniqueConstraintFields cs).contains fieldName = true ↔
      (∃ c ∈ cs, c.isPartial = false ∧ c.fields = [fieldName]) := by
    unfold singleFieldUniqueConstraintFields
    simp only [List.contains_eq_mem, decide_eq_true_eq, List.mem_map, List.mem_filter,
      Bool.and_eq_true, Bool.not_eq_true', beq_iff_eq]
    constructor
    · rintro ⟨c, ⟨hcmem, hpart, hlen⟩, rfl⟩
      refine ⟨c, hcmem, ?_, ?_⟩
      · simpa using hpart
      · rw [List.length_eq_one_iff] at hlen
        obtain ⟨a, ha⟩ := hlen
        rw [ha]; simp [List.headD]
    · rintro ⟨c, hcmem, hpart, hfields⟩
      refine ⟨c, ⟨hcmem, ?_, ?_⟩, ?_⟩
      · simp [hpart]
      · rw [hfields]; rfl
      · rw [hfields]; rfl
  have hcond : (fieldName != "pk" && !fld.unique &&
        !(singleFieldUniqueConstraintFields cs).contains fieldName) = true
      ↔ ¬ fieldNameAcceptable fieldName fld cs := by
    unfold fieldNameAcceptable
    simp only [Bool.and_eq_true, bne_iff_ne, ne_eq, Bool.not_eq_true', Bool.not_eq_true,
      not_or]
    rw [← hmem]
    constructor
    · rintro ⟨⟨hpk, hu⟩, hc⟩
      refine ⟨hpk, ?_, ?_⟩
      · simp [hu]
      · rw [List.contains_eq_mem] at hc; simpa using hc
    · rintro ⟨hpk, hu, hc⟩
      refine ⟨⟨hpk, ?_⟩, ?_⟩
      · simpa using hu
      · rw [List.contains_eq_mem]; simpa using hc
  unfold problem_spec_inBulk implementation_inBulk
  simp only [Id.run, bind, pure]
  constructor
  · intro hacc
    rw [if_neg]
    intro h
    exact (hcond.mp h) hacc
  · intro hnacc
    rw [if_pos (hcond.mpr hnacc)]
-- proof-end
