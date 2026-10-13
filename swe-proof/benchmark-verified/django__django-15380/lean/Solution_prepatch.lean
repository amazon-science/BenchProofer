import Mathlib
-- imports-end

/-!
Locating the owning model states for candidate renamed fields.

A schema-change detector compares two snapshots of a set of models: a PRIOR
snapshot and a CURRENT snapshot. Models may have been renamed between the two
snapshots, recorded by a rename map sending a model's `(app label, current name)`
to the name that same model had in the prior snapshot.

When considering whether a field that is present in the current snapshot but
absent in the prior one is in fact a rename of an existing field, the detector
must locate, for each such candidate field key `(app label, model name, field
name)`, the state of the field's owning model in BOTH snapshots:

  * in the PRIOR snapshot the owning model is found under the name it had THEN —
    i.e. its current name translated back through the rename map (falling back to
    the current name when the model was not renamed);
  * in the CURRENT snapshot the owning model is found under its CURRENT name.

The key correctness point is that each snapshot is indexed by the name the model
carries IN THAT snapshot: the prior snapshot by the prior name, the current
snapshot by the current name. Using the prior name to index the current snapshot
would fail to locate a model that was renamed in this same step.

Inputs: `renameMap` (current key → prior model name), `priorStates` and
`currentStates` (each maps an `(app label, model name)` key to that model's
state in the respective snapshot), and `entries` (the candidate field keys, each
an `(app label, model name, field name)`). The result is, per entry and in the
same order, the pair of located owning-model states — `(prior, current)` — each
absent when no model is recorded under the looked-up key.
-/

-- axioms-start
-- No UNCHANGED callee is consumed as an opaque axiom. The three map indexings
-- used by this computation (the rename-map translation and the two snapshot
-- lookups) are key→value association lookups, modeled DEEPLY and concretely as
-- total `List.lookup`s over the input carriers (I-tagged in refinement.md). The
-- downstream per-field selection step lies outside the modeled behavior, so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- An `(app label, model name)` lookup key into a snapshot or the rename map. -/
abbrev ModelKey := String × String

/-- The state of a model within one snapshot. Only the touched surface is
modeled: the model's name and its field-name set. -/
structure ModelState where
  name : String
  fields : List String
deriving DecidableEq, Repr, Inhabited

/-- Locate the owning-model states for a single candidate field key.

`entry` is `(app label, model name, field name)`. The field name selects the
field downstream of this computation (an unchanged step, out of model scope), so
only the `(app label, model name)` pair participates here.

The model's PRIOR name is its current name translated back through the rename map
(or the current name itself when it was not renamed). The prior snapshot is
indexed by that prior name; the current snapshot is indexed by the CURRENT
name. -/
def resolveOne
    (renameMap : List (ModelKey × String))
    (priorStates currentStates : List (ModelKey × ModelState))
    (entry : String × String × String) : Option ModelState × Option ModelState :=
  let appLabel  := entry.1
  let modelName := entry.2.1
  let priorName := (renameMap.lookup (appLabel, modelName)).getD modelName
  let priorState   := priorStates.lookup (appLabel, priorName)
  let currentState := currentStates.lookup (appLabel, modelName)
  (priorState, currentState)
-- pure-end

-- post-conditions-start
/-- The result is, entry-for-entry and in order, the pair of owning-model states
located for each candidate field key: the prior-snapshot state (found under the
model's prior name) paired with the current-snapshot state (found under the
model's current name). Both result components are fully pinned to the inputs;
neither is left free. -/
def problem_spec_resolveFieldModels
    (renameMap : List (ModelKey × String))
    (priorStates currentStates : List (ModelKey × ModelState))
    (entries : List (String × String × String))
    (result : List (Option ModelState × Option ModelState)) : Prop :=
  result = entries.map (resolveOne renameMap priorStates currentStates)
-- post-conditions-end

-- impl-start
def implementation_resolveFieldModels
    (renameMap : List (ModelKey × String))
    (priorStates currentStates : List (ModelKey × ModelState))
    (entries : List (String × String × String)) :
    List (Option ModelState × Option ModelState) := Id.run do
  let mut acc := []
  for entry in entries do
    let appLabel  := entry.1
    let modelName := entry.2.1
    let priorName := (renameMap.lookup (appLabel, modelName)).getD modelName
    -- Pre-patch (buggy): the current snapshot is indexed by the model's PRIOR
    -- name, so a model renamed in this same step is not located there.
    let priorState   := priorStates.lookup (appLabel, priorName)
    let currentState := currentStates.lookup (appLabel, priorName)
    acc := acc ++ [(priorState, currentState)]
  return acc
-- impl-end

-- proof-start
theorem correct_resolveFieldModels :
    ∀ (renameMap : List (ModelKey × String))
      (priorStates currentStates : List (ModelKey × ModelState))
      (entries : List (String × String × String)),
      problem_spec_resolveFieldModels renameMap priorStates currentStates entries
        (implementation_resolveFieldModels renameMap priorStates currentStates entries) := by
  sorry   -- prepatch: proof agent carries the gold proof body here; it is
          -- UNCLOSABLE against the buggy impl (current snapshot indexed by the
          -- prior name) — the G-DIFF signal.
-- proof-end
