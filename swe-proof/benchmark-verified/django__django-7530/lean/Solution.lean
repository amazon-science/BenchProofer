import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is invoked by the modeled behavior: the enumeration of
-- (application, model) pairs is modeled DEEPLY below (`App` / `appPairs` /
-- `pairsSpec`) from the application carrier itself, so there is no `opaque`
-- callee and no consumed `_prop` axiom here.
-- axioms-end

-- pure-start
/-- An application together with the models that belong to it.
* `label` identifies the application.
* `models` are the names of the models owned by this application. -/
structure App where
  label : String
  models : List String
deriving DecidableEq, Repr

/-- The (application, model) pairs contributed by a single application: each of
the application's OWN models, tagged with that application's label, in order. -/
def appPairs (a : App) : List (String × String) :=
  a.models.map (fun m => (a.label, m))

/-- The full enumeration of (application label, model name) pairs across a list
of applications: for each application in turn, every model that belongs to that
application, paired with the application's label, preserving order (a
front-recursive per-application fold). -/
def pairsSpec : List App → List (String × String)
  | [] => []
  | a :: rest => appPairs a ++ pairsSpec rest
-- pure-end

-- post-conditions-start
/-- The result is exactly the enumeration of (application label, model name)
pairs in which each model is paired ONLY with the application that owns it: for
every application, each of its own models — and no model belonging to a different
application — appears tagged with that application's label, in application order
and then model order. -/
def problem_spec_consistency_pairs
    (apps : List App) (result : List (String × String)) : Prop :=
  result = pairsSpec apps
-- post-conditions-end

-- impl-start
def implementation_consistency_pairs
    (apps : List App) : List (String × String) := Id.run do
  let mut acc : List (String × String) := []
  for a in apps do
    for m in a.models do
      acc := acc ++ [(a.label, m)]
  return acc
-- impl-end

-- proof-start
/-- Inner loop: appending `(label, m)` for each `m` in `ms` to the accumulator
`r` yields `r ++ ms.map (label, ·)`. Generalized over the accumulator `r`. -/
private theorem inner_helper_consistency_pairs
    (ms : List String) (lbl : String) (r : List (String × String)) :
    ((forIn ms r (fun m r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [(lbl, m)])))
        : Id (List (String × String))).run : List (String × String))
      = r ++ ms.map (fun m => (lbl, m)) := by
  induction ms generalizing r with
  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run_bind, Id.run_pure] at ih ⊢
    rw [ih]
    simp [List.append_assoc]

/-- Outer loop: running the nested `forIn` over `apps` starting from accumulator
`r` yields `r ++ pairsSpec apps`. Generalized over the accumulator `r`. -/
private theorem outer_helper_consistency_pairs
    (apps : List App) (r : List (String × String)) :
    ((forIn apps r (fun (a : App) (r : List (String × String)) => do
        let r ← forIn a.models r
          (fun m r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [(a.label, m)])))
        pure PUnit.unit
        pure (ForInStep.yield r)) : Id (List (String × String))).run : List (String × String))
      = r ++ pairsSpec apps := by
  induction apps generalizing r with
  | nil => simp only [List.forIn_nil, pairsSpec, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run_bind, Id.run_pure] at ih ⊢
    rw [inner_helper_consistency_pairs a.models a.label r, ih]
    simp only [pairsSpec, appPairs, List.append_assoc]

theorem correct_consistency_pairs : ∀ (apps : List App),
    problem_spec_consistency_pairs apps (implementation_consistency_pairs apps) := by
  intro apps
  unfold problem_spec_consistency_pairs implementation_consistency_pairs
  have h := outer_helper_consistency_pairs apps []
  simp only [Id.run, bind_pure, List.nil_append] at h ⊢
  exact h
-- proof-end
