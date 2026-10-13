import Mathlib
-- imports-end

/-!
Two related decisions a relational query layer makes when an `exclude(...)` over a
to-many relation is rewritten into a negated subquery.

When an exclude clause crosses a to-many relation, the layer builds a nested
*inner* query whose result the outer query tests membership against
(`WHERE NOT (pk IN (SELECT ...))`). Two pieces of behavior are modeled here.

1. **Inner-query construction.** A fresh inner query is created against the same
   model, the originating query's named filtered-relation definitions are carried
   over onto it (so a filter that references one of those named relations can be
   resolved inside the inner query), the supplied filter is applied, and any
   ordering is dropped. The named relation definitions on the inner query must be
   exactly those of the originating query — not an empty set.

2. **Leading-join selection.** Before emitting the inner query the layer may
   collapse the inner query's leading join into a plain column selection. This
   collapse is only sound when the leading join keeps every outer row AND carries
   no extra join-level restriction: an outer-keeping join would drop rows that
   have nothing on the inner side, and a join that exists only to apply a named
   relation's condition carries a restriction that would be lost if collapsed.
   When the collapse is allowed, the related fields' near-side names are selected
   against the collapsed alias; otherwise the far-side names are selected against
   the original alias.

Both behaviors are stated abstractly as input→output relations; the
implementations and correctness proofs are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. Both decisions are pure
-- functions of observables already in hand (the originating query's model and
-- named relation definitions; the leading join's properties and the candidate
-- field/alias choices), so each is modeled deeply over its inputs and validated
-- by the differential conformance check rather than by an axiom.
-- axioms-end

-- pure-start
/-- The relevant state of the inner query built while rewriting an exclude over a
to-many relation. `filteredRelations` pairs a relation alias with its definition;
`appliedFilters` records each applied filter clause TOGETHER WITH the named
relation context it was resolved against at the moment it was applied (a clause
that references a named relation can only be resolved when that relation is
already present); `orderingCleared` records that any ordering has been dropped. -/
structure InnerQuery where
  model : String
  filteredRelations : List (String × String)
  appliedFilters : List ((String × String) × List (String × String))
  orderingCleared : Bool
deriving Repr, DecidableEq

/-- A fresh inner query bound to `model`, with no named relations, no applied
filters, and ordering not yet dropped. -/
def freshInnerQuery (model : String) : InnerQuery :=
  { model := model, filteredRelations := [], appliedFilters := [],
    orderingCleared := false }

/-- Install the named relation definitions on the query. -/
def withFilteredRelations (q : InnerQuery)
    (frs : List (String × String)) : InnerQuery :=
  { q with filteredRelations := frs }

/-- Apply a filter clause. The clause is resolved against the relation context
CURRENTLY on the query, so the recorded entry captures `q.filteredRelations` as it
stands at this point — a clause referencing a named relation absent here could not
be resolved. -/
def addFilter (q : InnerQuery) (fe : String × String) : InnerQuery :=
  { q with appliedFilters := q.appliedFilters ++ [(fe, q.filteredRelations)] }

/-- Drop any ordering on the query. -/
def clearOrdering (q : InnerQuery) : InnerQuery :=
  { q with orderingCleared := true }

/-- The two properties of a leading join that decide whether it can be collapsed:
whether it keeps every outer row (an outer-keeping join), and whether it exists to
apply a named relation's condition (and so carries a restriction). -/
structure JoinProps where
  keepsOuterRows : Bool
  carriesRelationCondition : Bool
deriving Repr, DecidableEq

/-- The outcome of the leading-join decision: which field names are selected, and
against which alias. -/
structure JoinSelection where
  selectFields : List String
  selectAlias : String
deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- Input→output relation for building the inner query.

Inputs:
* `selfModel`             — the model the originating query is bound to;
* `selfFilteredRelations` — the originating query's named relation definitions;
* `filterExpr`            — the filter clause to apply to the inner query.

The inner query is the fresh query for the model, with the originating query's
named relation definitions installed, THEN the supplied filter applied, THEN the
ordering dropped — in that order. Pinning the whole construction (rather than only
the final field values) determines the order: the filter must be applied with the
named relations already present, so the applied-filter entry resolves against
exactly those relations. -/
def problem_spec_buildInnerQuery
    (selfModel : String) (selfFilteredRelations : List (String × String))
    (filterExpr : String × String) (result : InnerQuery) : Prop :=
  result =
    clearOrdering (addFilter
      (withFilteredRelations (freshInnerQuery selfModel) selfFilteredRelations)
      filterExpr) ∧
  -- spelled-out consequences (frame): every field is pinned, and the applied
  -- filter was resolved against the full named-relation context.
  result.model = selfModel ∧
  result.filteredRelations = selfFilteredRelations ∧
  result.appliedFilters = [(filterExpr, selfFilteredRelations)] ∧
  result.orderingCleared = true
-- post-conditions-end

-- impl-start
def implementation_buildInnerQuery
    (selfModel : String) (selfFilteredRelations : List (String × String))
    (filterExpr : String × String) : InnerQuery := Id.run do
  -- A fresh inner query bound to the same model (no named relations yet).
  let mut query : InnerQuery := freshInnerQuery selfModel
  -- (pre-fix) the originating query's named relation definitions are not carried
  -- onto the inner query, so the filter is applied with no named relations present.
  query := addFilter query filterExpr
  -- Drop any ordering.
  query := clearOrdering query
  return query
-- impl-end

-- proof-start
theorem correct_buildInnerQuery :
    ∀ (selfModel : String) (selfFilteredRelations : List (String × String))
      (filterExpr : String × String),
      problem_spec_buildInnerQuery selfModel selfFilteredRelations filterExpr
        (implementation_buildInnerQuery selfModel selfFilteredRelations filterExpr) := by
  sorry
-- proof-end

-- post-conditions-start
/-- Input→output relation for the leading-join selection.

Inputs:
* `firstJoin`     — the leading join's properties (keeps outer rows? carries a
                     named relation's condition?);
* `relatedFields` — the join's related-field name pairs (near side, far side);
* `aliasOriginal` — the alias of the leading join's source table;
* `aliasCollapsed`— the alias the join would collapse onto.

The join may be collapsed only when it neither keeps outer rows nor carries a
relation condition. When collapsed, the near-side names are selected against the
collapsed alias; otherwise the far-side names are selected against the original
alias. -/
def problem_spec_selectInnerJoin
    (firstJoin : JoinProps) (relatedFields : List (String × String))
    (aliasOriginal aliasCollapsed : String) (result : JoinSelection) : Prop :=
  let canCollapse := (!firstJoin.keepsOuterRows) && (!firstJoin.carriesRelationCondition)
  (canCollapse = true →
      result.selectFields = relatedFields.map (·.1) ∧
      result.selectAlias = aliasCollapsed) ∧
  (canCollapse = false →
      result.selectFields = relatedFields.map (·.2) ∧
      result.selectAlias = aliasOriginal)
-- post-conditions-end

-- impl-start
def implementation_selectInnerJoin
    (firstJoin : JoinProps) (relatedFields : List (String × String))
    (aliasOriginal aliasCollapsed : String) : JoinSelection := Id.run do
  -- The leading join can be collapsed only when it keeps no extra outer rows and
  -- carries no relation-level condition.
  let canCollapse := (!firstJoin.keepsOuterRows) && (!firstJoin.carriesRelationCondition)
  if canCollapse then
    return { selectFields := relatedFields.map (·.1), selectAlias := aliasCollapsed }
  else
    return { selectFields := relatedFields.map (·.2), selectAlias := aliasOriginal }
-- impl-end

-- proof-start
theorem correct_selectInnerJoin :
    ∀ (firstJoin : JoinProps) (relatedFields : List (String × String))
      (aliasOriginal aliasCollapsed : String),
      problem_spec_selectInnerJoin firstJoin relatedFields aliasOriginal aliasCollapsed
        (implementation_selectInnerJoin firstJoin relatedFields aliasOriginal aliasCollapsed) := by
  sorry
-- proof-end
