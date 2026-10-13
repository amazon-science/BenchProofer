import Mathlib
-- imports-end

/-!
Reducing an alter-field migration step against the step that immediately
follows it during migration optimization.

A migration is optimized by repeatedly looking at one step together with the
step that immediately follows it and, where possible, fusing the pair into a
shorter sequence. The step considered here alters one field of one model — it
is identified by a model name, a field name, and the new field definition it
carries.

Two field steps act on the *same field* when they name the same model and the
same field, compared case-insensitively. When the following step acts on the
same field, the alter step can be reconciled with it:

  * If the following step either alters that same field again, or removes it,
    then the alter step is subsumed: the pair collapses to just the following
    step (a later alter or a removal makes the earlier alter redundant).
  * If the following step renames that same field — and the altered field
    pins no explicit database column name — then the rename is floated to the
    front and the alter step is re-expressed against the field's new name: the
    pair becomes the rename followed by an alter step that carries the original
    field definition under the new name.
  * In every other case this reconciliation itself produces no fusion, and the
    outcome falls to the generic pairing rule for *elidable* steps (a step may
    be marked elidable, meaning it can be dropped entirely when the sequence is
    squashed): if the alter step is marked elidable it is dropped and the pair
    collapses to just the following step; otherwise, if the following step is
    marked elidable it is dropped and the pair collapses to just the alter
    step; and when neither is marked elidable no replacement sequence is
    produced.

These cases are exhaustive and mutually exclusive, so the result is fully
determined for every pairing.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The reduction
-- performs only a runtime kind test of the following step, a
-- case-insensitive model+field name comparison, an "explicit column name absent"
-- test, a read of each step's elidable flag, and the construction of
-- replacement steps that copy carried-over components. All are modeled directly
-- (`String.toLower`, an `Option` check, `Bool` fields, and record literals), so
-- no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The runtime kind of a field step, as far as the reduction distinguishes:
an alter-field step, a remove-field step, a rename-field step, or any other
step. -/
inductive OpKind where
  | alterField
  | removeField
  | renameField
  | otherOp
deriving DecidableEq, Repr

/-- The field definition an alter/add step carries, observed through the only
component the reduction inspects (whether an explicit database column name is
pinned) plus an opaque token standing for the rest, which is only ever copied. -/
structure FieldInfo where
  /-- the explicit database column name, if one is pinned (`none` when absent) -/
  dbColumn : Option String
  /-- opaque stand-in for the remainder of the field definition (copied verbatim) -/
  repr : String
deriving DecidableEq, Repr

/-- A field step, observed through the components the reduction reads or
rewrites: its kind, the model and field it names, the new name it introduces
(meaningful only for a rename), whether it is marked elidable (droppable when
the sequence is squashed), and the field definition it carries. -/
structure Op where
  kind : OpKind
  modelName : String
  name : String
  newName : String
  elidable : Bool
  field : FieldInfo
deriving DecidableEq, Repr

/-- Two field steps act on the same field when they name the same model and
the same field, compared case-insensitively. -/
def sameField (a b : Op) : Bool :=
  a.modelName.toLower == b.modelName.toLower && a.name.toLower == b.name.toLower
-- pure-end

-- post-conditions-start
/-- The outcome of pairing an alter-field step `self` with the step `op` that
immediately follows it:

  * when `op` alters or removes the same field, the pair collapses into exactly
    the following step (`[op]`);
  * when `op` renames the same field and `self` pins no explicit database column
    name, the rename is floated to the front and the alter step is re-expressed
    against the new name, carrying `self`'s original field definition unchanged
    (directive 5 frame: model name and field carried over verbatim); the
    re-expressed alter step is a freshly constructed step, not marked elidable;
  * otherwise the outcome falls to the generic elidable pairing rule: if `self`
    is marked elidable the pair collapses to just the following step (`[op]`);
    failing that, if `op` is marked elidable the pair collapses to just the
    alter step (`[self]`); and when neither is marked elidable no fused
    replacement sequence is produced (the empty result).

The cases are exhaustive and mutually exclusive, so the result is fully
determined for every input. -/
def problem_spec_reduceAlter (self op : Op) (result : List Op) : Prop :=
  ((op.kind = OpKind.alterField ∨ op.kind = OpKind.removeField) ∧ sameField self op = true →
      result = [op]) ∧
  ((op.kind = OpKind.renameField ∧ sameField self op = true ∧ self.field.dbColumn = none) →
      result =
        [op,
         { kind := OpKind.alterField,
           modelName := self.modelName,
           name := op.newName,
           newName := "",
           elidable := false,
           field := self.field }]) ∧
  (¬((op.kind = OpKind.alterField ∨ op.kind = OpKind.removeField) ∧ sameField self op = true) ∧
   ¬(op.kind = OpKind.renameField ∧ sameField self op = true ∧ self.field.dbColumn = none) →
      (self.elidable = true → result = [op]) ∧
      (self.elidable = false ∧ op.elidable = true → result = [self]) ∧
      (self.elidable = false ∧ op.elidable = false → result = []))
-- post-conditions-end

-- impl-start
def implementation_reduceAlter (self op : Op) : List Op := Id.run do
  if (op.kind == OpKind.alterField || op.kind == OpKind.removeField) && sameField self op then
    return [op]
  if op.kind == OpKind.renameField && sameField self op && self.field.dbColumn.isNone then
    return [op,
      { kind := OpKind.alterField,
        modelName := self.modelName,
        name := op.newName,
        newName := "",
        elidable := false,
        field := self.field }]
  if self.elidable then
    return [op]
  if op.elidable then
    return [self]
  return []
-- impl-end

-- proof-start
theorem correct_reduceAlter :
    ∀ (self op : Op),
      problem_spec_reduceAlter self op (implementation_reduceAlter self op) := by
  intro self op
  unfold problem_spec_reduceAlter implementation_reduceAlter
  simp only [Id.run]
  refine ⟨?_, ?_, ?_⟩
  · rintro ⟨hk, hs⟩
    have hb : (op.kind == OpKind.alterField || op.kind == OpKind.removeField) = true := by
      rcases hk with h | h <;> simp [h]
    simp [hb, hs]
    rfl
  · rintro ⟨hk, hs, hc⟩
    have h1 : (op.kind == OpKind.alterField || op.kind == OpKind.removeField) = false := by
      simp [hk]
    have h2 : (op.kind == OpKind.renameField) = true := by simp [hk]
    have h3 : self.field.dbColumn.isNone = true := by simp [hc]
    simp [h1, h2, h3, hs]
    rfl
  · rintro ⟨h1, h2⟩
    have hne1 : ((op.kind == OpKind.alterField || op.kind == OpKind.removeField)
        && sameField self op) = false := by
      by_contra hc
      simp only [Bool.not_eq_false, Bool.and_eq_true, Bool.or_eq_true, beq_iff_eq] at hc
      exact h1 ⟨hc.1, hc.2⟩
    have hne2 : (op.kind == OpKind.renameField && sameField self op
        && self.field.dbColumn.isNone) = false := by
      by_contra hc
      simp only [Bool.not_eq_false, Bool.and_eq_true, beq_iff_eq,
        Option.isNone_iff_eq_none] at hc
      exact h2 ⟨hc.1.1, hc.1.2, hc.2⟩
    refine ⟨?_, ?_, ?_⟩
    · intro hse
      simp [hne1, hne2, hse]
      rfl
    · rintro ⟨hse, hoe⟩
      simp [hne1, hne2, hse, hoe]
      rfl
    · rintro ⟨hse, hoe⟩
      simp [hne1, hne2, hse, hoe]
      rfl
-- proof-end
