import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The per-reference flag
-- lookups (whether a referenced annotation is itself computed in a wrapping
-- subquery, and whether it is a window/over-clause expression) are modeled
-- DEEPLY as boolean fields carried on each referenced annotation, rather than
-- axiomatized. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A referenced annotation, reduced to the two boolean properties that the
wrapping decision inspects: whether it is itself produced by a wrapping
subquery, and whether it is a window/over-clause expression. -/
structure RefAnnotation where
  isSubqueryExpr : Bool
  isWindowExpr   : Bool

/-- One requested aggregate, reduced to the list of annotations it references. -/
structure AggregateExpr where
  refs : List RefAnnotation

/-- Some referenced annotation (across all requested aggregates) is itself
produced by a wrapping subquery. -/
def anyRefSubquery (aggs : List AggregateExpr) : Bool :=
  aggs.any (fun a => a.refs.any (·.isSubqueryExpr))

/-- Some referenced annotation (across all requested aggregates) is a
window/over-clause expression. -/
def anyRefWindow (aggs : List AggregateExpr) : Bool :=
  aggs.any (fun a => a.refs.any (·.isWindowExpr))
-- pure-end

-- post-conditions-start
/-- The aggregation must be evaluated inside a wrapping subquery exactly when at
least one of the following holds: one of the pre-existing structural conditions
(`otherConditions`); some referenced annotation is itself produced by a wrapping
subquery; or some referenced annotation is a window/over-clause expression. The
result is pinned to the full disjunction over the actual inputs, so every
contributing condition — including the unchanged ones folded into
`otherConditions` — is constrained. -/
def problem_spec_requiresSubqueryWrap
    (aggregates : List AggregateExpr) (otherConditions : Bool)
    (result : Bool) : Prop :=
  result = (otherConditions || anyRefSubquery aggregates || anyRefWindow aggregates)
-- post-conditions-end

-- impl-start
def implementation_requiresSubqueryWrap
    (aggregates : List AggregateExpr) (otherConditions : Bool) : Bool := Id.run do
  -- Pre-patch: the wrapping decision only tracks the subquery-reference flag and
  -- never inspects whether a referenced annotation is a window/over-clause
  -- expression, so a window reference does not force the wrapping subquery.
  let mut refsSubquery := false
  for agg in aggregates do
    refsSubquery := refsSubquery || agg.refs.any (·.isSubqueryExpr)
  return otherConditions || refsSubquery
-- impl-end

-- proof-start
theorem correct_requiresSubqueryWrap :
    ∀ (aggregates : List AggregateExpr) (otherConditions : Bool),
    problem_spec_requiresSubqueryWrap aggregates otherConditions
      (implementation_requiresSubqueryWrap aggregates otherConditions) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
