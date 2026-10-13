import Mathlib
-- imports-end

/-!
Planning a row-count query over a model whose query carries extra named clauses.

A count is computed by adding one summary aggregate (the row counter) and then
deciding how to shape the resulting query.  Two things must be decided from the
named clauses the query already carries:

  * whether the count has to be computed inside a wrapping subquery, and
  * which of the already-present clauses must remain materialised in the
    emitted query.

A carried clause that is materialised in the result (`selected`) and is itself
an aggregate (or an OVER-style window), or the presence of post-grouping
filters, forces the wrapping subquery.  Carried clauses that are present only as
named aliases, or that are plain scalar expressions, do not.  When a wrapping
subquery is used and the query is not `distinct`, an already-present clause is
kept only when one of the summary aggregates being computed refers to it;
otherwise it is dropped.  When the query is `distinct`, re-masking would alter
the distinct row set, so every materialised already-present clause is kept.
When no wrapping subquery is needed, none of the already-present clauses is
kept.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: every quantity the decision reads
-- (whether a carried clause is an aggregate / window, whether it is materialised,
-- the alias references carried by each summary aggregate, and the presence of
-- post-grouping filters) is supplied as data on the modeled carrier and the
-- decision is spelled out directly below.
-- axioms-end

-- pure-start
/-- One named clause carried by the query. `aliasName` is its name; `selected`
records whether it is materialised in the emitted column list (a plain named
alias is *not* selected); `containsAggregate` / `containsOverClause` record
whether it is an aggregate or an OVER-style window; `added` marks the summary
aggregate(s) introduced for this computation; `refs` are the alias names this
clause refers to. -/
structure Ann where
  aliasName : String
  selected : Bool
  containsAggregate : Bool
  containsOverClause : Bool
  added : Bool
  refs : List String
deriving Repr, DecidableEq

/-- The query state the decision reads. -/
structure QState where
  anns : List Ann
  groupByTuple : Bool
  isSliced : Bool
  distinct : Bool
  combinator : Bool
  postGroupFilter : Bool
deriving Repr

/-- The planning outcome: whether a wrapping subquery is used and which
already-present clause aliases remain materialised in the emitted query. -/
structure Plan where
  useSubquery : Bool
  keptExisting : List String
deriving Repr, DecidableEq

/-- The materialised already-present clauses (those in the emitted column list
and not one of the summary aggregates introduced for this computation). This is
the set that governs whether a wrapping subquery is needed. -/
def existingAnns (st : QState) : List Ann :=
  st.anns.filter (fun a => !a.added && a.selected)

/-- Whether the materialised already-present clauses include an aggregate/window,
or the query carries post-grouping filters. -/
def hasExistingAgg (st : QState) : Bool :=
  (existingAnns st).any (fun a => a.containsAggregate || a.containsOverClause)
    || st.postGroupFilter

/-- Whether a wrapping subquery is required. -/
def needsSubquery (st : QState) : Bool :=
  st.groupByTuple || st.isSliced || hasExistingAgg st || st.distinct || st.combinator

/-- The set of alias names the summary aggregates keep alive: each summary
aggregate's own name together with the names it refers to. -/
def addedMask (st : QState) : List String :=
  (st.anns.filter (fun a => a.added)).flatMap (fun a => a.aliasName :: a.refs)

/-- The already-present clause aliases kept inside the wrapping subquery. When
the query is `distinct`, the reference-based rebuild of the surviving mask is
skipped (re-masking would alter the distinct row set), so exactly the
materialised already-present clauses survive. Otherwise the surviving mask is
rebuilt purely from the summary aggregates' references: every carried clause
(materialised OR a plain named alias, irrespective of whether the clause was
itself materialised) referred to by a summary aggregate is kept. -/
def keptExisting (st : QState) : List String :=
  if st.distinct then
    (existingAnns st).map (fun a => a.aliasName)
  else
    ((st.anns.filter (fun a => !a.added && (addedMask st).contains a.aliasName))).map
      (fun a => a.aliasName)
-- pure-end

-- post-conditions-start
def problem_spec_countPlan (st : QState) (result : Plan) : Prop :=
  result.useSubquery = needsSubquery st ∧
  result.keptExisting = (if needsSubquery st then keptExisting st else [])
-- post-conditions-end

-- impl-start
def implementation_countPlan (st : QState) : Plan := Id.run do
  let existing := st.anns.filter (fun a => !a.added && a.selected)
  let mut hasAgg := false
  for a in existing do
    if a.containsAggregate || a.containsOverClause then
      hasAgg := true
  let needsSub :=
    st.groupByTuple || st.isSliced || (hasAgg || st.postGroupFilter)
      || st.distinct || st.combinator
  if needsSub then
    let mut mask : List String := []
    for a in st.anns do
      if a.added then
        mask := mask ++ (a.aliasName :: a.refs)
    let kept :=
      if st.distinct then
        existing.map (fun a => a.aliasName)
      else
        (st.anns.filter (fun a => !a.added && mask.contains a.aliasName)).map
          (fun a => a.aliasName)
    return { useSubquery := true, keptExisting := kept }
  else
    return { useSubquery := false, keptExisting := [] }
-- impl-end


-- proof-start
theorem correct_countPlan : ∀ (st : QState),
    problem_spec_countPlan st (implementation_countPlan st) := by
  intro st
  have hbool : ∀ (l : List Ann) (b0 : Bool),
      List.foldl (fun b a => if (a.containsAggregate || a.containsOverClause) = true then true else b) b0 l
        = (b0 || l.any (fun a => a.containsAggregate || a.containsOverClause)) := by
    intro l
    induction l with
    | nil => simp
    | cons x xs ih =>
      intro b0
      simp only [List.foldl_cons, List.any_cons]
      rw [ih]
      by_cases h : (x.containsAggregate || x.containsOverClause) = true <;> simp [h]
  have hlist : ∀ (l : List Ann) (acc : List String),
      List.foldl (fun b a => if a.added = true then b ++ (a.aliasName :: a.refs) else b) acc l
        = acc ++ (l.filter (fun a => a.added)).flatMap (fun a => a.aliasName :: a.refs) := by
    intro l
    induction l with
    | nil => simp
    | cons x xs ih =>
      intro acc
      simp only [List.foldl_cons, List.filter_cons]
      by_cases h : x.added = true <;> simp [h, ih, List.append_assoc]
  unfold problem_spec_countPlan
  simp only [implementation_countPlan, Id.run, bind_pure, pure_bind,
    ← apply_ite (f := ForInStep.yield), ← apply_ite (f := pure (f := Id)),
    show ∀ (x : ForInStep Bool), (pure x : Id _) = x from fun _ => rfl,
    show ∀ (x : ForInStep (List String)), (pure x : Id _) = x from fun _ => rfl,
    List.forIn_yield_eq_foldl]
  rw [hbool, hlist]
  simp only [Bool.false_or, List.nil_append, bind, Id.instMonad]
  -- Now needsSub matches needsSubquery st
  have hns : (st.groupByTuple || st.isSliced ||
      ((List.filter (fun a => !a.added && a.selected) st.anns).any
        (fun a => a.containsAggregate || a.containsOverClause) || st.postGroupFilter) ||
      st.distinct || st.combinator) = needsSubquery st := by
    simp only [needsSubquery, hasExistingAgg, existingAnns]
  rw [hns]
  constructor
  · by_cases h : needsSubquery st = true <;> simp [h]
  · by_cases h : needsSubquery st = true <;>
      simp only [h, if_true, if_pos, if_neg, if_false, ite_true, ite_false,
        keptExisting, addedMask, existingAnns, Bool.false_eq_true, reduceCtorEq]

-- proof-end
