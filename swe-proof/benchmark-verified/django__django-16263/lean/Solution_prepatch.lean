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
  let existing := st.anns.filter (fun a => !a.added)
  let needsSub :=
    st.groupByTuple || st.isSliced || (!existing.isEmpty)
      || st.distinct || st.combinator
  if needsSub then
    let mut mask : List String := []
    for a in st.anns do
      if a.added then
        mask := mask ++ (a.aliasName :: a.refs)
    let kept := (st.anns.filter (fun a => !a.added && mask.contains a.aliasName)).map
      (fun a => a.aliasName)
    return { useSubquery := true, keptExisting := kept }
  else
    return { useSubquery := false, keptExisting := [] }
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- impl it cannot close: `impl_eq` claims the implementation reduces to the
-- closed form whose `useSubquery` is `needsSubquery st` (which fires only on a
-- materialised existing aggregate/window or a post-grouping filter). This impl
-- instead forces the wrapping decision whenever ANY carried clause is present,
-- so the `split`/`rfl` step in `impl_eq` is unprovable on a plain aliased/scalar
-- clause, where the spec demands no wrapping.
theorem hasAgg_loop (xs : List Ann) (init : Bool) :
    (Id.run (forIn xs init (fun a r =>
      (if a.containsAggregate || a.containsOverClause then ForInStep.yield true
       else ForInStep.yield r : Id (ForInStep Bool)))))
    = (xs.foldl (fun acc a => if a.containsAggregate || a.containsOverClause then true else acc) init) := by
  induction xs generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons, List.foldl_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : (a.containsAggregate || a.containsOverClause) = true
    · simp only [h, if_true, ih]
    · simp only [h, Bool.false_eq_true, if_false, ih]

theorem mask_loop (xs : List Ann) (init : List String) :
    (Id.run (forIn xs init (fun a r =>
      (if a.added then ForInStep.yield (r ++ (a.aliasName :: a.refs)) else ForInStep.yield r : Id (ForInStep (List String))))))
    = init ++ (xs.filter (fun a => a.added)).flatMap (fun a => a.aliasName :: a.refs) := by
  induction xs generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons, List.filter_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : a.added = true
    · simp only [h, if_true, ih, List.flatMap_cons]; simp [List.append_assoc]
    · simp only [h, Bool.false_eq_true, if_false, ih]

theorem hasAgg_val (st : QState) :
    (Id.run (forIn (existingAnns st) false (fun a r =>
        (if a.containsAggregate || a.containsOverClause then ForInStep.yield true
         else ForInStep.yield r : Id (ForInStep Bool)))))
    = (existingAnns st).any (fun a => a.containsAggregate || a.containsOverClause) := by
  rw [hasAgg_loop (existingAnns st) false]
  generalize existingAnns st = xs
  induction xs with
  | nil => rfl
  | cons a as ih =>
    rw [List.foldl_cons, List.any_cons]
    by_cases h : (a.containsAggregate || a.containsOverClause) = true
    · simp only [h, if_true, Bool.true_or]; clear ih
      induction as with
      | nil => rfl
      | cons b bs ih2 => rw [List.foldl_cons]; split <;> simp_all
    · simp only [h, Bool.false_eq_true, if_false, Bool.false_or, ih]

theorem mask_val (st : QState) :
    (Id.run (forIn st.anns ([] : List String) (fun a r =>
        (if a.added then ForInStep.yield (r ++ (a.aliasName :: a.refs))
         else ForInStep.yield r : Id (ForInStep (List String))))))
    = (st.anns.filter (fun a => a.added)).flatMap (fun a => a.aliasName :: a.refs) := by
  rw [mask_loop]; simp

theorem impl_eq (st : QState) :
    implementation_countPlan st =
      { useSubquery := needsSubquery st,
        keptExisting := if needsSubquery st then keptExisting st else [] } := by
  unfold implementation_countPlan
  simp only [Id.run, bind]
  rw [show (forIn (st.anns.filter (fun a => !a.added && a.selected)) false (fun a r =>
        (if (a.containsAggregate || a.containsOverClause) = true then
          pure (ForInStep.yield true) else pure (ForInStep.yield r) : Id (ForInStep Bool))))
      = (Id.run (forIn (existingAnns st) false (fun a r =>
          (if a.containsAggregate || a.containsOverClause then ForInStep.yield true
           else ForInStep.yield r : Id (ForInStep Bool))))) from rfl, hasAgg_val]
  rw [show (forIn st.anns ([]:List String) (fun a r =>
        (if a.added = true then pure (ForInStep.yield (r ++ a.aliasName :: a.refs))
        else pure (ForInStep.yield r) : Id (ForInStep (List String)))))
      = (Id.run (forIn st.anns ([]:List String) (fun a r =>
          (if a.added then ForInStep.yield (r ++ (a.aliasName :: a.refs))
           else ForInStep.yield r : Id (ForInStep (List String)))))) from rfl, mask_val]
  unfold needsSubquery hasExistingAgg keptExisting addedMask existingAnns
  split <;> rename_i h
  · simp only [pure, h, if_true]
  · simp only [Bool.not_eq_true] at h; simp only [pure, h, Bool.false_eq_true]

theorem correct_countPlan : ∀ (st : QState),
    problem_spec_countPlan st (implementation_countPlan st) := by
  intro st
  unfold problem_spec_countPlan
  rw [impl_eq]
  exact ⟨rfl, rfl⟩
-- proof-end

