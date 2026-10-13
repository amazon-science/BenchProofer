import Mathlib
-- imports-end

/-!
Exposing, per target, the class labels recognised by a multi-target model.

A multi-target classification model works by fitting one independent sub-model
per target column. Each fitted sub-model records the set of distinct class
labels it observed for its own target.

After the whole model has been fitted, it should expose — as a first-class,
queryable attribute — the per-target class labels: a list with one entry per
target, in target order, where the entry for a target is exactly the class
labels recorded by that target's sub-model.

The result is carried in `Option` to record whether this per-target view is
defined: a defined view is `some xss`; an undefined view (the attribute is
absent, so querying it is an error) is `none`. For a fitted multi-target model
the view is always defined and is the target-ordered collection of each
sub-model's class labels.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Fitting the
-- per-target sub-models is performed by the shared multi-target fitting routine;
-- its result — the ordered list of fitted sub-models, each carrying the class
-- labels it recorded — enters here as input data. The behavior modeled is the
-- collection of those per-sub-model class labels into a per-target view, which
-- reads only that input list, so there is no `opaque`/`axiom` callee contract to
-- declare.
-- axioms-end

-- pure-start
/-- One fitted sub-model, observed only through the class labels it recorded for
its target. Other attributes of a sub-model are irrelevant to the per-target
class-label view and are not modeled. -/
structure SubModel where
  /-- the distinct class labels this sub-model recorded for its target -/
  classLabels : List Int
deriving Repr
-- pure-end

-- post-conditions-start
/-- The per-target class-label view is defined and equals, in target order, the
class labels recorded by each sub-model (directive 5 frame: the entire result is
pinned to the input list of sub-models — length equals the number of sub-models
and entry `i` is sub-model `i`'s class labels; nothing is left free). -/
def problem_spec_collectClasses
    (subModels : List SubModel) (result : Option (List (List Int))) : Prop :=
  result = some (subModels.map (·.classLabels))
-- post-conditions-end

-- impl-start
def implementation_collectClasses
    (subModels : List SubModel) : Option (List (List Int)) := Id.run do
  -- pre-patch: no per-target class-label view is exposed, so querying it is
  -- undefined (the attribute is absent).
  return none
-- impl-end

-- proof-start
theorem correct_collectClasses :
    ∀ (subModels : List SubModel),
      problem_spec_collectClasses subModels
        (implementation_collectClasses subModels) := by
  intro subModels
  unfold problem_spec_collectClasses implementation_collectClasses
  simp only [Id.run]
  congr 1
  suffices h : ∀ (ms : List SubModel) (init : List (List Int)),
      (Id.run (forIn ms init (fun m r =>
        (pure (ForInStep.yield (r ++ [m.classLabels])) : Id (ForInStep (List (List Int)))))))
      = init ++ ms.map (·.classLabels) by
    simpa using h subModels []
  intro ms
  induction ms with
  | nil => intro init; simp [Id.run, Id.pure_eq]
  | cons a as ih =>
      intro init
      rw [List.forIn_cons]
      simp only [Id.run, bind, pure] at ih ⊢
      rw [ih]
      simp [List.append_assoc]
-- proof-end
