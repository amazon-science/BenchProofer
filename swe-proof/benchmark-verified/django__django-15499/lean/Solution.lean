import Mathlib
-- imports-end

/-!
Collapsing a model-creation step followed by a manager-reconfiguration step
during migration optimization.

A migration is optimized by repeatedly looking at a creation step together with
the step that immediately follows it and, where possible, fusing the two into a
single step. A model-creation step records, for one model: its name, its fields,
its options, its bases, and its managers.

When the step that follows a model-creation step merely reconfigures the
**managers** of the *same* model, the two steps describe a single net effect:
create that model already carrying the reconfigured managers. In that case the
pair collapses into one creation step that is identical to the original except
that its managers are replaced by the reconfigured ones — the name, fields,
options, and bases are carried over unchanged.

If the following step reconfigures the managers of a *different* model, the two
steps are independent and no such collapse is produced.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The reduction
-- performs only a case-insensitive comparison of the two model identifiers and
-- the construction of a fresh creation step that copies four components and
-- substitutes the managers. Both are modeled directly (`String.toLower` and a
-- structure update), so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A model-creation step, observed through the five components an optimization
of it reads or rewrites: the model identifier, its fields, its options, its
bases, and its managers. Fields/options/bases/managers are carried as opaque
`(name, repr)` token lists — the optimization only ever copies them. -/
structure ModelState where
  name : String
  fields : List (String × String)
  options : List (String × String)
  bases : List String
  managers : List (String × String)
deriving DecidableEq, Repr

/-- Two model identifiers name the same model when they agree case-insensitively
(the optimizer compares lower-cased names). -/
def sameModel (a b : String) : Bool := a.toLower = b.toLower
-- pure-end

-- post-conditions-start
/-- The outcome of pairing a model-creation step `model` with a following step
that reconfigures managers (`newManagers`) of the model identified by
`targetName`:

  * when the two refer to the same model, the pair collapses into exactly one
    creation step equal to `model` in name, fields, options, and bases, but with
    its managers replaced by `newManagers` (every carried-over component pinned
    to its input — directive 5 frame);
  * otherwise no collapsed creation step is produced (the empty result).

The two cases are exhaustive and mutually exclusive, so the result is fully
determined for every input. -/
def problem_spec_optimizeCreateThenAlterManagers
    (model : ModelState) (targetName : String)
    (newManagers : List (String × String))
    (result : List ModelState) : Prop :=
  (sameModel model.name targetName = true →
      result = [{ model with managers := newManagers }]) ∧
  (sameModel model.name targetName = false →
      result = [])
-- post-conditions-end

-- impl-start
def implementation_optimizeCreateThenAlterManagers
    (model : ModelState) (targetName : String)
    (newManagers : List (String × String)) : List ModelState := Id.run do
  if sameModel model.name targetName then
    return [{ model with managers := newManagers }]
  return []
-- impl-end

-- proof-start
theorem correct_optimizeCreateThenAlterManagers :
    ∀ (model : ModelState) (targetName : String)
      (newManagers : List (String × String)),
      problem_spec_optimizeCreateThenAlterManagers model targetName newManagers
        (implementation_optimizeCreateThenAlterManagers model targetName newManagers) := by
  intro model targetName newManagers
  unfold problem_spec_optimizeCreateThenAlterManagers
    implementation_optimizeCreateThenAlterManagers
  by_cases h : sameModel model.name targetName = true
  · refine ⟨fun _ => ?_, fun h' => ?_⟩
    · simp only [Id.run, h, if_true, pure]
    · rw [h] at h'; exact absurd h' (by decide)
  · simp only [Bool.not_eq_true] at h
    refine ⟨fun h' => ?_, fun _ => ?_⟩
    · rw [h] at h'; exact absurd h' (by decide)
    · simp only [Id.run, h, Bool.false_eq_true, if_false, pure, bind]
-- proof-end
