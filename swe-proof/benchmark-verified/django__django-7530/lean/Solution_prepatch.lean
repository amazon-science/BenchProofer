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
  -- pre-patch: the inner model enumeration ignores the application it is meant
  -- to scope to and instead ranges over every model in the whole project, so
  -- each application label is paired with all models rather than its own.
  let mut allModels : List String := []
  for a in apps do
    allModels := allModels ++ a.models
  let mut acc : List (String × String) := []
  for a in apps do
    for m in allModels do
      acc := acc ++ [(a.label, m)]
  return acc
-- impl-end

-- proof-start
theorem correct_consistency_pairs : ∀ (apps : List App),
    problem_spec_consistency_pairs apps (implementation_consistency_pairs apps) := by
  intro apps
  unfold problem_spec_consistency_pairs implementation_consistency_pairs
  sorry   -- carries the gold proof intent; UNCLOSABLE against the pre-patch impl (G-DIFF)
-- proof-end
