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
  let mut refsSubquery := false
  let mut refsWindow := false
  for agg in aggregates do
    refsSubquery := refsSubquery || agg.refs.any (·.isSubqueryExpr)
    refsWindow   := refsWindow   || agg.refs.any (·.isWindowExpr)
  return otherConditions || refsSubquery || refsWindow
-- impl-end


-- proof-start
theorem correct_requiresSubqueryWrap :
    ∀ (aggregates : List AggregateExpr) (otherConditions : Bool),
    problem_spec_requiresSubqueryWrap aggregates otherConditions
      (implementation_requiresSubqueryWrap aggregates otherConditions) := by
  intro aggregates otherConditions
  simp only [problem_spec_requiresSubqueryWrap, implementation_requiresSubqueryWrap,
    anyRefSubquery, anyRefWindow, Id.run, bind, pure, List.forIn_yield_eq_foldl]
  have key : ∀ (l : List AggregateExpr) (b c : Bool),
      ((List.foldl (fun (p : MProd Bool Bool) a => (⟨p.fst || a.refs.any fun x => x.isSubqueryExpr,
          p.snd || a.refs.any fun x => x.isWindowExpr⟩ : MProd Bool Bool)) (⟨b, c⟩ : MProd Bool Bool) l).fst
        = (b || l.any (fun a => a.refs.any fun x => x.isSubqueryExpr)))
      ∧ ((List.foldl (fun (p : MProd Bool Bool) a => (⟨p.fst || a.refs.any fun x => x.isSubqueryExpr,
          p.snd || a.refs.any fun x => x.isWindowExpr⟩ : MProd Bool Bool)) (⟨b, c⟩ : MProd Bool Bool) l).snd
        = (c || l.any (fun a => a.refs.any fun x => x.isWindowExpr))) := by
    intro l
    induction l with
    | nil => intro b c; exact ⟨by simp, by simp⟩
    | cons hd tl ih =>
      intro b c
      simp only [List.foldl_cons, List.any_cons]
      refine ⟨?_, ?_⟩
      · rw [(ih _ _).1, Bool.or_assoc]
      · rw [(ih _ _).2, Bool.or_assoc]
  rw [(key aggregates false false).1, (key aggregates false false).2]
  simp [Bool.or_assoc]

-- proof-end
