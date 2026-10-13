import Mathlib
-- imports-end

/-!
Computing the ordering dependencies emitted when a brand-new model is created
during automatic migration detection.

When a new model is added, the detector records, alongside the create step, a
list of *ordering dependencies* — tuples saying "this create step must come
after some other step". Each dependency names a target by an application label,
a model name, an optional field name, and a boolean flag selecting whether it
waits on the *creation* (`true`) of the target or on its *removal* (`false`).

For one newly-created model the dependency list is built from:

  * a self-dependency on the removal of any prior proxy of the same model
    (the application label and model name of the new model, no field, flag
    `false`);
  * for every base the new model inherits from that is given as a dotted
    "label.name" reference: a dependency on the creation of that base
    (no field, flag `true`); and — crucially — when both the previous and the
    current recorded state of that base are known, a dependency on the
    *removal* of every field that the base used to declare, no longer declares,
    and that the new model itself now declares (flag `false`). This last group
    forces a field that has moved from a base onto the new subclass to be
    removed from the base before the subclass is created.
  * a dependency on the creation of the far end of a primary-key relation,
    when one is present (no field, flag `true`).

This file pins exactly which dependency tuples that list must contain.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Splitting a
-- dotted reference, the set difference / intersection over field-name
-- collections, and the membership tests are all modeled directly over `List`
-- and `Option`, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- An ordering dependency tuple: it names a target by application label and
model name, optionally a field of that target, and a flag selecting whether the
step waits on the target's creation (`true`) or its removal (`false`). -/
structure Dep where
  appLabel : String
  name : String
  field : Option String
  onCreate : Bool
deriving DecidableEq, Repr

/-- A base a model inherits from, as the dependency builder sees it: either a
dotted reference already separated into an application label and a model name,
or anything else (a non-dotted or non-string base), which contributes nothing. -/
inductive Base where
  | dotted (appLabel name : String) : Base
  | other : Base
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- `result` is the dependency list emitted for the new model `appLabel.modelName`
with the given `bases`, own field names `modelFields`, previous-state and
current-state field lookups for bases (`fromLookup` / `toLookup`), and optional
primary-key relation target `primaryKeyRel`.

The list must contain EXACTLY the following tuples (membership characterised in
both directions, so no required dependency is missing and no spurious one is
present):

  * the self proxy-removal dependency `⟨appLabel, modelName, none, false⟩`;
  * for every dotted base `ba.bn`, the base-creation dependency
    `⟨ba, bn, none, true⟩`;
  * for every dotted base `ba.bn` whose previous and current states are both
    known, and every field `f` declared by the base's previous state, absent
    from its current state, and declared by the new model, the field-removal
    dependency `⟨ba, bn, some f, false⟩`;
  * when a primary-key relation target `pa.pn` is present, the dependency
    `⟨pa, pn, none, true⟩`. -/
def problem_spec_createModelDeps
    (appLabel modelName : String) (bases : List Base) (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String))
    (primaryKeyRel : Option (String × String)) (result : List Dep) : Prop :=
  ∀ d : Dep, d ∈ result ↔
    (d = ⟨appLabel, modelName, none, false⟩) ∨
    (∃ ba bn, Base.dotted ba bn ∈ bases ∧ d = ⟨ba, bn, none, true⟩) ∨
    (∃ ba bn fs gs f, Base.dotted ba bn ∈ bases ∧
       fromLookup ba bn = some fs ∧ toLookup ba bn = some gs ∧
       f ∈ fs ∧ f ∉ gs ∧ f ∈ modelFields ∧
       d = ⟨ba, bn, some f, false⟩) ∨
    (∃ pa pn, primaryKeyRel = some (pa, pn) ∧ d = ⟨pa, pn, none, true⟩)
-- post-conditions-end

-- impl-start
-- The field-removal dependencies a single dotted base contributes: one per
-- field the base previously declared (oldFields), no longer declares
-- (newFields), and that the new model itself declares (modelFields).
def removedFieldDeps (ba bn : String) (oldFields newFields modelFields : List String) : List Dep :=
  (oldFields.filter (fun f => !(newFields.contains f) && modelFields.contains f)).map
    (fun f => ⟨ba, bn, some f, false⟩)

-- The dependencies a single base contributes: nothing for a non-dotted base;
-- for a dotted base, the base-creation dependency followed by the field-removal
-- dependencies (only when both states of the base are known).
def baseDeps (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String)) : Base → List Dep
  | Base.other => []
  | Base.dotted ba bn =>
      ⟨ba, bn, none, true⟩ ::
        (match fromLookup ba bn, toLookup ba bn with
         | some oldFields, some newFields => removedFieldDeps ba bn oldFields newFields modelFields
         | _, _ => [])

def implementation_createModelDeps
    (appLabel modelName : String) (bases : List Base) (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String))
    (primaryKeyRel : Option (String × String)) : List Dep := Id.run do
  let mut deps : List Dep := [⟨appLabel, modelName, none, false⟩]
  for base in bases do
    deps := deps ++ baseDeps modelFields fromLookup toLookup base
  if let some (pa, pn) := primaryKeyRel then
    deps := deps ++ [⟨pa, pn, none, true⟩]
  return deps
-- impl-end


-- proof-start
/-- The explicit pure-list normal form of `implementation_createModelDeps`. -/
def resultForm (appLabel modelName : String) (bases : List Base) (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String))
    (primaryKeyRel : Option (String × String)) : List Dep :=
  [⟨appLabel, modelName, none, false⟩] ++
    bases.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) [] ++
    (match primaryKeyRel with
     | some (pa, pn) => [⟨pa, pn, none, true⟩]
     | none => [])

theorem impl_eq_normalForm (appLabel modelName : String) (bases : List Base)
    (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String))
    (primaryKeyRel : Option (String × String)) :
    implementation_createModelDeps appLabel modelName bases modelFields fromLookup toLookup
        primaryKeyRel =
      resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel := by
  simp only [implementation_createModelDeps, resultForm, Id.run, bind, pure]
  cases primaryKeyRel <;> simp [List.forIn_yield_eq_foldl]

theorem removedFieldDeps_mem (ba bn : String) (oldFields newFields modelFields : List String)
    (d : Dep) :
    d ∈ removedFieldDeps ba bn oldFields newFields modelFields ↔
      ∃ f, f ∈ oldFields ∧ ¬ newFields.contains f ∧ modelFields.contains f ∧
        d = ⟨ba, bn, some f, false⟩ := by
  simp only [removedFieldDeps, List.mem_map, List.mem_filter, Bool.and_eq_true,
    Bool.not_eq_true']
  constructor
  · rintro ⟨f, ⟨hf, h1, h2⟩, rfl⟩
    exact ⟨f, hf, by simpa using h1, h2, rfl⟩
  · rintro ⟨f, hf, h1, h2, rfl⟩
    exact ⟨f, ⟨hf, by simpa using h1, h2⟩, rfl⟩

theorem baseDeps_mem (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String)) (base : Base) (d : Dep) :
    d ∈ baseDeps modelFields fromLookup toLookup base ↔
      (∃ ba bn, base = Base.dotted ba bn ∧
        (d = ⟨ba, bn, none, true⟩ ∨
         (∃ fs gs, fromLookup ba bn = some fs ∧ toLookup ba bn = some gs ∧
            d ∈ removedFieldDeps ba bn fs gs modelFields))) := by
  cases base with
  | other => simp [baseDeps]
  | dotted ba bn =>
    simp only [baseDeps, List.mem_cons]
    constructor
    · rintro (h | h)
      · exact ⟨ba, bn, rfl, Or.inl h⟩
      · refine ⟨ba, bn, rfl, Or.inr ?_⟩
        revert h
        cases hf : fromLookup ba bn with
        | none => simp
        | some fs =>
          cases hg : toLookup ba bn with
          | none => simp
          | some gs => intro h; exact ⟨fs, gs, rfl, rfl, h⟩
    · rintro ⟨ba', bn', heq, hd⟩
      cases heq
      rcases hd with hd | ⟨fs, gs, hf, hg, hmem⟩
      · exact Or.inl hd
      · refine Or.inr ?_
        rw [hf, hg]
        exact hmem

theorem baseFold_mem (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String)) (bases : List Base) (d : Dep) :
    d ∈ bases.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) [] ↔
      ∃ base, base ∈ bases ∧ d ∈ baseDeps modelFields fromLookup toLookup base := by
  have general : ∀ (l : List Base) (init : List Dep),
      d ∈ l.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) init ↔
        d ∈ init ∨ ∃ base, base ∈ l ∧ d ∈ baseDeps modelFields fromLookup toLookup base := by
    intro l
    induction l with
    | nil => intro init; simp
    | cons b bs ih =>
      intro init
      rw [List.foldl_cons, ih (init ++ baseDeps modelFields fromLookup toLookup b)]
      simp only [List.mem_append, List.mem_cons]
      constructor
      · rintro ((h | h) | ⟨base, hb, hd⟩)
        · exact Or.inl h
        · exact Or.inr ⟨b, Or.inl rfl, h⟩
        · exact Or.inr ⟨base, Or.inr hb, hd⟩
      · rintro (h | ⟨base, (rfl | hb), hd⟩)
        · exact Or.inl (Or.inl h)
        · exact Or.inl (Or.inr hd)
        · exact Or.inr ⟨base, hb, hd⟩
  simpa using general bases []

theorem contains_iff_mem (l : List String) (f : String) :
    l.contains f = true ↔ f ∈ l := by
  simp

theorem spec_iff (appLabel modelName : String) (bases : List Base) (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String))
    (primaryKeyRel : Option (String × String)) (d : Dep) :
    d ∈ resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel ↔
      ((d = ⟨appLabel, modelName, none, false⟩) ∨
       (∃ ba bn, Base.dotted ba bn ∈ bases ∧ d = ⟨ba, bn, none, true⟩) ∨
       (∃ ba bn fs gs f, Base.dotted ba bn ∈ bases ∧
          fromLookup ba bn = some fs ∧ toLookup ba bn = some gs ∧
          f ∈ fs ∧ f ∉ gs ∧ f ∈ modelFields ∧
          d = ⟨ba, bn, some f, false⟩) ∨
       (∃ pa pn, primaryKeyRel = some (pa, pn) ∧ d = ⟨pa, pn, none, true⟩)) := by
  unfold resultForm
  simp only [List.append_assoc, List.mem_append, List.mem_singleton, baseFold_mem, baseDeps_mem,
    removedFieldDeps_mem, contains_iff_mem]
  constructor
  · rintro (h | ⟨base, hbase, ba, bn, rfl, (h | ⟨fs, gs, hf, hg, f, hfs, hgs, hfm, rfl⟩)⟩ | h)
    · exact Or.inl h
    · exact Or.inr (Or.inl ⟨ba, bn, hbase, h⟩)
    · exact Or.inr (Or.inr (Or.inl ⟨ba, bn, fs, gs, f, hbase, hf, hg, hfs, hgs, hfm, rfl⟩))
    · rcases primaryKeyRel with _ | ⟨pa, pn⟩
      · simp at h
      · simp at h; exact Or.inr (Or.inr (Or.inr ⟨pa, pn, rfl, h⟩))
  · rintro (h | ⟨ba, bn, hbase, rfl⟩ | ⟨ba, bn, fs, gs, f, hbase, hf, hg, hfs, hgs, hfm, rfl⟩ | ⟨pa, pn, hpk, rfl⟩)
    · exact Or.inl h
    · exact Or.inr (Or.inl ⟨_, hbase, ba, bn, rfl, Or.inl rfl⟩)
    · exact Or.inr (Or.inl ⟨_, hbase, ba, bn, rfl, Or.inr ⟨fs, gs, hf, hg, f, hfs, hgs, hfm, rfl⟩⟩)
    · exact Or.inr (Or.inr (by rw [hpk]; simp))

theorem correct_createModelDeps :
    ∀ (appLabel modelName : String) (bases : List Base) (modelFields : List String)
      (fromLookup toLookup : String → String → Option (List String))
      (primaryKeyRel : Option (String × String)),
      problem_spec_createModelDeps appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel
        (implementation_createModelDeps appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel) := by
  intro appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel
  unfold problem_spec_createModelDeps
  rw [impl_eq_normalForm]
  intro d
  exact spec_iff appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel d

-- proof-end
