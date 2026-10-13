import Mathlib
-- imports-end

/-!
A routine that performs a preset number of independent evaluations, where every
evaluation must consult the SAME shared collection of items.

The collection is supplied by a source. That source may only support being read
once (`oneShot = true`): after a single traversal it yields nothing further. A
source that can be read repeatedly (`oneShot = false`) returns the whole
collection every time it is consulted.

Required behaviour: every one of the `numEvals` evaluations observes the
COMPLETE collection — even when the source is single-traversal. The number of
evaluations is otherwise unconstrained, and the result must contain exactly one
observation per evaluation.

Modeled with the collection as `List Nat`, a boolean recording whether the
source is single-traversal, and the evaluation count as `Nat`. The result is the
sequence of collections actually observed, one per evaluation, in order.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the collection contents are taken
-- as the input `folds`, and the obligation to make every evaluation observe the
-- complete collection is modeled deeply (the result is pinned element-wise).
-- axioms-end

-- pure-start
-- No additional pure helpers are needed: the modeled behaviour is a direct
-- relation between the inputs and the observed-collection sequence.
-- pure-end

-- post-conditions-start
/-- Specification of the repeated-evaluation routine.

* The result records exactly one observation per evaluation (`length = numEvals`).
* Every observation is the COMPLETE collection `folds`.

The single-traversal flag `oneShot` does NOT appear on the right-hand side: the
observed collections are independent of it — a single-traversal source must be
handled so that no observation is ever short. -/
def problem_spec_repeatedEvaluations
    (folds : List Nat) (oneShot : Bool) (numEvals : Nat)
    (result : List (List Nat)) : Prop :=
  result.length = numEvals ∧ (∀ s ∈ result, s = folds)
-- post-conditions-end

-- impl-start
def implementation_repeatedEvaluations
    (folds : List Nat) (oneShot : Bool) (numEvals : Nat) : List (List Nat) := Id.run do
  -- BUG: the source is consulted directly inside each evaluation. When the
  -- source is single-traversal, its first traversal drains it, so every later
  -- evaluation observes an empty collection instead of the complete one.
  let mut remaining := folds
  let mut observed : List (List Nat) := []
  for _ in [0:numEvals] do
    observed := observed ++ [remaining]
    if oneShot then
      remaining := []
  return observed
-- impl-end

-- proof-start
theorem correct_repeatedEvaluations :
    ∀ (folds : List Nat) (oneShot : Bool) (numEvals : Nat),
      problem_spec_repeatedEvaluations folds oneShot numEvals
        (implementation_repeatedEvaluations folds oneShot numEvals) := by
  sorry
-- proof-end
