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
-- Pre-patch (buggy) skeleton: a dotted base contributes ONLY its creation
-- dependency; the field-removal dependencies are not emitted, so a field that
-- has moved from a base onto the new subclass is not forced to be removed from
-- the base before the subclass is created.
def baseDeps (_modelFields : List String)
    (_fromLookup _toLookup : String → String → Option (List String)) : Base → List Dep
  | Base.other => []
  | Base.dotted ba bn => [⟨ba, bn, none, true⟩]

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
-- The gold proof body for `correct_createModelDeps` (carried over from
-- Solution.lean) cannot close against this pre-patch impl. The pre-patch
-- `baseDeps` emits only the base-creation dependency, so a dotted base
-- contributes exactly `[⟨ba, bn, none, true⟩]`. The spec, however, still
-- demands (third disjunct) a field-removal dependency `⟨ba, bn, some f, false⟩`
-- for every field `f` a base drops onto the new model. The reverse membership
-- direction of that disjunct is therefore unsatisfiable, and the proof gets
-- genuinely stuck (a real elaboration error, NOT a `sorry`).

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

theorem baseDeps_mem (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String)) (base : Base) (d : Dep) :
    d ∈ baseDeps modelFields fromLookup toLookup base ↔
      (∃ ba bn, base = Base.dotted ba bn ∧ d = ⟨ba, bn, none, true⟩) := by
  cases base with
  | other => simp [baseDeps]
  | dotted ba bn =>
    simp only [baseDeps, List.mem_singleton]
    constructor
    · rintro rfl; exact ⟨ba, bn, rfl, rfl⟩
    · rintro ⟨ba', bn', heq, rfl⟩; cases heq; rfl

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
  simp only [List.append_assoc, List.mem_append, List.mem_singleton, baseFold_mem, baseDeps_mem]
  constructor
  · rintro (h | ⟨base, hbase, ba, bn, rfl, rfl⟩ | h)
    · exact Or.inl h
    · exact Or.inr (Or.inl ⟨ba, bn, hbase, rfl⟩)
    · rcases primaryKeyRel with _ | ⟨pa, pn⟩
      · simp at h
      · simp at h; exact Or.inr (Or.inr (Or.inr ⟨pa, pn, rfl, h⟩))
  · rintro (h | ⟨ba, bn, hbase, rfl⟩ | ⟨ba, bn, fs, gs, f, hbase, hf, hg, hfs, hgs, hfm, rfl⟩ | ⟨pa, pn, hpk, rfl⟩)
    · exact Or.inl h
    · exact Or.inr (Or.inl ⟨_, hbase, ba, bn, rfl, rfl⟩)
    · -- STUCK: the spec demands membership of the field-removal dependency
      -- `⟨ba, bn, some f, false⟩`, but the pre-patch impl never emits one, so
      -- there is no matching `baseDeps` member. No term closes this goal.
      exact Or.inr (Or.inl ⟨_, hbase, ba, bn, rfl, rfl⟩)
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
