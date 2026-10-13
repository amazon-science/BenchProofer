import Mathlib
-- imports-end

/-!
Restricting a prefetch query to a set of related objects, honoring any slice.

When a collection of related objects is fetched in bulk for a group of parent
rows, the query is narrowed to the related objects that belong to those parents.
The caller may additionally ask for only a contiguous SLICE of each parent's
related objects (an `offset`, and optionally a `limit`) — for example "the first
three related objects of each parent".

The desired behavior is therefore:

  * always restrict the query to the related objects belonging to the supplied
    parents (a membership condition);
  * when no slice is requested, that membership condition is the whole
    restriction and the query is otherwise unchanged;
  * when a slice IS requested, the slice must be applied PER PARENT GROUP rather
    than to the result as a whole: keep, within each group's ordering, the
    objects whose position in the group is beyond the requested `offset` and (if
    a `limit` is given) no greater than that `limit`. Both `offset` and `limit`
    are ABSOLUTE within-group positions (the lower and upper marks of the
    requested slice), NOT counts: the upper condition keeps objects whose
    position is at most `limit`, applied directly to the position. Because the
    slice is now expressed as conditions on the query, the plain offset/limit
    bounds are dropped from the query.

`query` carries the slice bounds (`offset` = lower position mark, optional
`limit` = upper position mark) and the group ordering. `fieldName` names the
grouping relation; `instances` are the parents.
The result is the restricted query: its accumulated conditions, and its
remaining offset/limit bounds.
-/

-- axioms-start
-- No UNCHANGED callee is consumed as an opaque axiom. The query-building
-- primitives (membership condition, per-group position bounds, the slice-bound
-- query state and its "is a slice present?" test, and dropping the bounds) are
-- all modeled concretely below as data construction / pure predicates — they are
-- identical concrete ops (refinement.md), not behavioral callees that need a
-- contract. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A per-group ranking: items are positioned within each `groupBy` group
according to `ordering`. -/
structure Ranking where
  groupBy : String
  ordering : List String
  deriving DecidableEq, Repr

/-- One conjunct of the restriction accumulated on a query. -/
inductive PredAtom where
  /-- Keep only objects related to one of `instances` through `field`. -/
  | memberOf (field : String) (instances : List Int)
  /-- Keep only objects whose position within their group (per `r`) is strictly
      beyond `low`. -/
  | positionAbove (r : Ranking) (low : Nat)
  /-- Keep only objects whose position within their group (per `r`) is at most
      `high`. -/
  | positionAtMost (r : Ranking) (high : Nat)
  deriving DecidableEq, Repr

/-- A query carrying the touched state: its group `ordering`, and the slice
bounds `offset` (lower position mark, i.e. rows to skip) and optional `limit`
(upper position mark; `none` means no upper bound). Both are absolute positions,
not counts. -/
structure RelatedQuery where
  ordering : List String
  offset : Nat
  limit : Option Nat
  deriving DecidableEq, Repr

/-- A query after restriction: the accumulated conjuncts, plus the remaining
slice bounds. -/
structure FilteredQuery where
  predicate : List PredAtom
  offset : Nat
  limit : Option Nat
  deriving DecidableEq, Repr

/-- A slice is present iff a nonzero offset or any limit has been set. -/
def isSliced (q : RelatedQuery) : Bool := q.offset != 0 || q.limit.isSome
-- pure-end

-- post-conditions-start
/-- The restricted query is fully determined by the input. Its conditions always
begin with the membership condition. When no slice is present the membership
condition is the entire restriction and the bounds are unchanged. When a slice is
present, the per-group position conditions are appended (a lower bound from the
offset, and an upper bound when a limit is given) and the plain offset/limit
bounds are dropped. Every output component is pinned to the input. -/
def problem_spec_restrictPrefetch
    (query : RelatedQuery) (fieldName : String) (instances : List Int)
    (result : FilteredQuery) : Prop :=
  let base := PredAtom.memberOf fieldName instances
  let r : Ranking := { groupBy := fieldName, ordering := query.ordering }
  (isSliced query = false →
      result = { predicate := [base], offset := query.offset, limit := query.limit }) ∧
  (isSliced query = true →
      result.offset = 0 ∧ result.limit = none ∧
      result.predicate =
        base :: PredAtom.positionAbove r query.offset ::
          (match query.limit with
           | some h => [PredAtom.positionAtMost r h]
           | none => []))
-- post-conditions-end

-- impl-start
def implementation_restrictPrefetch
    (query : RelatedQuery) (fieldName : String) (instances : List Int) :
    FilteredQuery := Id.run do
  let mut predicate : List PredAtom := [PredAtom.memberOf fieldName instances]
  let mut offset := query.offset
  let mut limit := query.limit
  if isSliced query then
    let r : Ranking := { groupBy := fieldName, ordering := query.ordering }
    predicate := predicate ++ [PredAtom.positionAbove r query.offset]
    if let some h := query.limit then
      predicate := predicate ++ [PredAtom.positionAtMost r h]
    offset := 0
    limit := none
  return { predicate := predicate, offset := offset, limit := limit }
-- impl-end

-- proof-start
theorem correct_restrictPrefetch :
    ∀ (query : RelatedQuery) (fieldName : String) (instances : List Int),
      problem_spec_restrictPrefetch query fieldName instances
        (implementation_restrictPrefetch query fieldName instances) := by
  intro query fieldName instances
  unfold problem_spec_restrictPrefetch implementation_restrictPrefetch
  by_cases h : isSliced query = true
  · constructor
    · intro hf; rw [h] at hf; exact absurd hf (by simp)
    · intro _
      simp only [h, if_true, Id.run, bind, pure]
      cases hl : query.limit with
      | none => simp
      | some v => simp
  · simp only [Bool.not_eq_true] at h
    constructor
    · intro _
      simp only [h, Bool.false_eq_true, if_false, Id.run, bind, pure]
    · intro hf; rw [h] at hf; exact absurd hf (by simp)
-- proof-end
