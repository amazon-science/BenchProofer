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
  if fieldName != "pk" && !fld.unique then
    return Except.error fieldName
  return Except.ok ()
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- pre-patch impl it cannot close: the impl ignores the model's unique constraints,
-- so on a field that is acceptable ONLY via a single-field unconditional unique
-- constraint, `fieldNameAcceptable` holds (spec demands `Except.ok ()`) yet the
-- impl's two-clause guard fires and returns `Except.error fieldName`. The carried
-- `hc`-branch (which derives `Except.ok ()` from the membership witness) no longer
-- matches the narrower impl guard, so the proof fails to typecheck.
theorem contains_iff (fieldName : String) (cs : List UniqueConstraint) :
    (singleFieldUniqueConstraintFields cs).contains fieldName = true ↔
      (∃ c ∈ cs, c.isPartial = false ∧ c.fields = [fieldName]) := by
  unfold singleFieldUniqueConstraintFields
  simp only [List.contains_eq_mem, List.mem_map, List.mem_filter, Bool.and_eq_true,
    Bool.not_eq_true', decide_eq_true_eq, beq_iff_eq]
  constructor
  · rintro ⟨c, ⟨hc, hp, hlen⟩, hhead⟩
    refine ⟨c, hc, by simpa using hp, ?_⟩
    match hcf : c.fields, hlen, hhead with
    | [x], _, hhead => simp only [List.headD_cons] at hhead; subst hhead; rfl
  · rintro ⟨c, hc, hp, hcf⟩
    exact ⟨c, ⟨hc, by simpa using hp, by rw [hcf]; rfl⟩, by rw [hcf]; rfl⟩

theorem correct_inBulk :
    ∀ (fieldName : String) (fld : FieldInfo) (cs : List UniqueConstraint),
      problem_spec_inBulk fieldName fld cs (implementation_inBulk fieldName fld cs) := by
  intro fieldName fld cs
  unfold problem_spec_inBulk implementation_inBulk fieldNameAcceptable
  simp only [Id.run]
  -- guard g := fieldName != "pk" && !fld.unique && !(contains)
  by_cases hpk : fieldName = "pk"
  · -- acceptable; guard's first conjunct false
    have hg : (fieldName != "pk" && !fld.unique && !((singleFieldUniqueConstraintFields cs).contains fieldName)) = false := by
      simp [hpk]
    refine ⟨fun _ => by simp only [hg, Bool.false_eq_true, if_false]; rfl, fun hcon => ?_⟩
    exact absurd (Or.inl hpk) hcon
  · by_cases hu : fld.unique = true
    · have hg : (fieldName != "pk" && !fld.unique && !((singleFieldUniqueConstraintFields cs).contains fieldName)) = false := by
        simp [hu]
      refine ⟨fun _ => by simp only [hg, Bool.false_eq_true, if_false]; rfl, fun hcon => ?_⟩
      exact absurd (Or.inr (Or.inl hu)) hcon
    · by_cases hc : (singleFieldUniqueConstraintFields cs).contains fieldName = true
      · have hg : (fieldName != "pk" && !fld.unique && !((singleFieldUniqueConstraintFields cs).contains fieldName)) = false := by
          simp only [hc, Bool.not_true, Bool.and_false]
        have hex := (contains_iff fieldName cs).mp hc
        refine ⟨fun _ => by simp only [hg, Bool.false_eq_true, if_false]; rfl, fun hcon => ?_⟩
        exact absurd (Or.inr (Or.inr hex)) hcon
      · have hg : (fieldName != "pk" && !fld.unique && !((singleFieldUniqueConstraintFields cs).contains fieldName)) = true := by
          simp only [bne_iff_ne, ne_eq, Bool.and_eq_true, Bool.not_eq_true', decide_not]
          refine ⟨⟨?_, ?_⟩, ?_⟩
          · simpa using hpk
          · simpa using hu
          · simpa using hc
        have hnacc : ¬ (fieldName = "pk" ∨ fld.unique = true ∨ ∃ c ∈ cs, c.isPartial = false ∧ c.fields = [fieldName]) := by
          rintro (h | h | h)
          · exact hpk h
          · exact hu h
          · exact hc ((contains_iff fieldName cs).mpr h)
        refine ⟨fun hacc => absurd hacc hnacc, fun _ => by simp only [hg, if_true]; rfl⟩
-- proof-end
