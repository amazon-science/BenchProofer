import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the ordering-introspection
-- predicate inspects only the truthiness of its input carriers (an empty/EmptyQuerySet
-- flag, two explicit-ordering sequences, a default-ordering flag, the model's default
-- ordering sequence, and the grouping sequence). Every observation is reproduced
-- concretely as a boolean combination, so nothing is axiomatized. The proof agent
-- may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
-- No standalone helpers are required; the predicate is a single boolean combination.
-- pure-end

-- post-conditions-start
/-- Whether a result set will carry a meaningful row ordering.

`isEmpty` marks the trivially-ordered empty set. `extraOrderBy` and `orderBy` hold
explicitly-requested orderings; a non-empty one orders the result. Otherwise the
result is ordered only when a default ordering is in force (`defaultOrdering` set
AND the model carries a default ordering sequence `metaOrdering`) AND the result is
NOT aggregated into groups — modeled by `groupBy`, whose presence (a non-empty
grouping sequence) suppresses the default ordering. Every input is observed only by
its emptiness/flag, and the result is pinned to the full boolean combination so no
component is left free. -/
def problem_spec_querysetOrdered
    (isEmpty : Bool) (extraOrderBy orderBy : List String)
    (defaultOrdering : Bool) (metaOrdering groupBy : List String)
    (result : Bool) : Prop :=
  result =
    (isEmpty || !extraOrderBy.isEmpty || !orderBy.isEmpty ||
      (defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty))
-- post-conditions-end

-- impl-start
def implementation_querysetOrdered
    (isEmpty : Bool) (extraOrderBy orderBy : List String)
    (defaultOrdering : Bool) (metaOrdering groupBy : List String) :
    Bool := Id.run do
  if isEmpty then
    return true
  if !extraOrderBy.isEmpty || !orderBy.isEmpty then
    return true
  else if defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty then
    return true
  else
    return false
-- impl-end

-- proof-start
theorem correct_querysetOrdered :
    ∀ (isEmpty : Bool) (extraOrderBy orderBy : List String)
      (defaultOrdering : Bool) (metaOrdering groupBy : List String),
    problem_spec_querysetOrdered isEmpty extraOrderBy orderBy defaultOrdering
      metaOrdering groupBy
      (implementation_querysetOrdered isEmpty extraOrderBy orderBy defaultOrdering
        metaOrdering groupBy) := by
  intro isEmpty extraOrderBy orderBy defaultOrdering metaOrdering groupBy
  unfold problem_spec_querysetOrdered implementation_querysetOrdered
  simp only [Id.run]
  cases isEmpty <;>
    cases defaultOrdering <;>
    cases he : extraOrderBy.isEmpty <;>
    cases ho : orderBy.isEmpty <;>
    cases hm : metaOrdering.isEmpty <;>
    cases hg : groupBy.isEmpty <;>
    simp_all <;> rfl
-- proof-end
