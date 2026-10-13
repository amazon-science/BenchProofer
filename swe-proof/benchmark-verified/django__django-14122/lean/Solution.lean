import Mathlib
-- imports-end

/-!
Assembling the list of grouping columns for an aggregate query.

When a query aggregates, the database must be told which columns to group rows
by. That grouping list is built up in phases from several sources: an explicit
caller-supplied grouping set, the columns of the selected expressions, the
columns implied by the ordering, and the columns of the post-aggregation filter.
The columns are accumulated in order; a later de-duplication pass (not modeled
here) removes repeats.

The ordering of a query may be supplied explicitly by the caller, or it may be
the model's own implicit default ordering. Only an *explicitly requested*
ordering should contribute its columns to the grouping; an ordering that is
merely the model's implicit default must NOT widen the grouping, since doing so
silently changes which rows are aggregated together. When the grouping source is
"no grouping at all", the result is empty regardless of the other phases.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The columns
-- each selected, ordering, or filter expression contributes to the grouping
-- enter as plain data (the `List Col` carried by each entry), as does the
-- per-entry "already covered by reference" / "references the selected columns"
-- decision (the `Bool` of each entry). The accumulation and gating logic that
-- uses them is modeled directly from this data rather than via a callee
-- contract, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The identity of a single grouping column expression. -/
abbrev Col := Nat

/-- The grouping source: either no grouping at all, "group by all of the
selected fields" (no explicit column list to seed the accumulation), or an
explicit caller-supplied list of grouping columns. -/
inductive GroupBy where
  | isNone
  | allFields
  | explicit (cols : List Col)
deriving DecidableEq, Repr

/-- The columns seeded by an explicit caller-supplied grouping set (empty unless
the grouping source is such a list). -/
def explicitCols (gb : GroupBy) : List Col :=
  match gb with
  | GroupBy.explicit cols => cols
  | _ => []

/-- The columns contributed by the selected expressions: each `select` entry
carries `(coveredByReference, cols)`; an entry already covered by a reference
contributes nothing, otherwise it contributes its columns, in order. -/
def selectCols (select : List (Bool × List Col)) : List Col :=
  (select.filter (fun e => !e.1)).flatMap (fun e => e.2)

/-- The columns contributed by the ordering expressions: each `orderBy` entry
carries `(referencesSelected, cols)`; an entry that merely references the
selected columns contributes nothing (those columns are already grouped),
otherwise it contributes its columns, in order. -/
def orderByCols (orderBy : List (Bool × List Col)) : List Col :=
  (orderBy.filter (fun e => !e.1)).flatMap (fun e => e.2)

/-- The fully-accumulated grouping column list (before the unmodeled
de-duplication pass). With no grouping source the list is empty. Otherwise it is
the explicit seed, then the selected-expression columns, then — only when the
ordering was explicitly requested rather than the model's implicit default — the
ordering columns, then the filter columns. -/
def groupByExpressions (metaOrdering : Bool) (gb : GroupBy)
    (select orderBy : List (Bool × List Col)) (having : List Col) : List Col :=
  match gb with
  | GroupBy.isNone => []
  | _ =>
    explicitCols gb ++ selectCols select
      ++ (if metaOrdering then [] else orderByCols orderBy)
      ++ having
-- pure-end

-- post-conditions-start
/-- The accumulated grouping columns are fully pinned to the inputs: empty when
there is no grouping source; otherwise the explicit grouping seed followed by the
selected-expression columns, then the ordering columns ONLY when the ordering is
an explicit request (`metaOrdering = false`) — an implicit default ordering
contributes nothing — then the filter columns, all in order. -/
def problem_spec_getGroupBy
    (metaOrdering : Bool) (gb : GroupBy)
    (select orderBy : List (Bool × List Col)) (having : List Col)
    (result : List Col) : Prop :=
  result = groupByExpressions metaOrdering gb select orderBy having
-- post-conditions-end

-- impl-start
def implementation_getGroupBy
    (metaOrdering : Bool) (gb : GroupBy)
    (select orderBy : List (Bool × List Col)) (having : List Col) :
    List Col := Id.run do
  let mut expressions : List Col := []
  match gb with
  | GroupBy.isNone => return []
  | GroupBy.allFields => pure ()
  | GroupBy.explicit cols =>
      for c in cols do
        expressions := expressions ++ [c]
  for entry in select do
    if entry.1 then
      continue
    for col in entry.2 do
      expressions := expressions ++ [col]
  if !metaOrdering then
    for entry in orderBy do
      if !entry.1 then
        for col in entry.2 do
          expressions := expressions ++ [col]
  for col in having do
    expressions := expressions ++ [col]
  return expressions
-- impl-end


-- proof-start
theorem forInAppendSingletons_lemma (l : List Col) (acc : List Col) :
    (forIn (m := Id) l acc (fun x s => pure (ForInStep.yield (s ++ [x])))).run
      = acc ++ l := by
  induction l generalizing acc with
  | nil => simp
  | cons x xs ih =>
    simp only [List.forIn_cons]
    have h := ih (acc ++ [x])
    simp only [Id.run, bind, pure] at h ⊢
    rw [h]; simp

theorem forInFilterFlatMap_lemma (es : List (Bool × List Col)) (acc : List Col) :
    (forIn (m := Id) es acc (fun entry s =>
        if entry.1 then pure (ForInStep.yield s)
        else pure (ForInStep.yield
          ((forIn (m := Id) entry.2 s
            (fun c t => pure (ForInStep.yield (t ++ [c])))).run)))).run
      = acc ++ (es.filter (fun e => !e.1)).flatMap (fun e => e.2) := by
  induction es generalizing acc with
  | nil => simp
  | cons e rest ih =>
    rcases e with ⟨b, cols⟩
    have hcols := forInAppendSingletons_lemma cols acc
    simp only [bind, pure, Id.run, ForInStep.yield] at hcols
    cases b <;>
      simp only [List.forIn_cons, List.filter_cons, Bool.not_true, Bool.not_false,
        reduceIte, bind, pure, Id.run, ForInStep.yield] at ih ⊢ <;>
      simp [ih, hcols, List.flatMap_cons, List.append_assoc]

theorem correct_getGroupBy_isNone (metaOrdering : Bool)
    (select orderBy : List (Bool × List Col)) (having : List Col) :
    implementation_getGroupBy metaOrdering GroupBy.isNone select orderBy having
      = groupByExpressions metaOrdering GroupBy.isNone select orderBy having := by
  rfl

theorem correct_getGroupBy_nonNone (metaOrdering : Bool) (gb : GroupBy)
    (select orderBy : List (Bool × List Col)) (having : List Col)
    (h : gb ≠ GroupBy.isNone) :
    implementation_getGroupBy metaOrdering gb select orderBy having
      = explicitCols gb ++ selectCols select
        ++ (if metaOrdering then [] else orderByCols orderBy) ++ having := by
  have hs : ∀ (l acc : List Col),
      forIn (m := Id) l acc (fun x r => ForInStep.yield (r ++ [x])) = acc ++ l := by
    intro l acc
    rw [List.forIn_yield_eq_foldl]
    induction l generalizing acc with
    | nil => simp
    | cons x xs ih => simp [ih, List.append_assoc]
  have hsel : ∀ (es : List (Bool × List Col)) (acc : List Col),
      forIn (m := Id) es acc (fun entry r =>
          if entry.1 = true then ForInStep.yield r
          else ForInStep.yield (r ++ entry.2))
        = acc ++ (es.filter (fun e => !e.1)).flatMap (fun e => e.2) := by
    intro es; induction es with
    | nil => intro acc; simp; rfl
    | cons e rest ih =>
        intro acc
        rw [List.forIn_cons]
        by_cases he : e.1 = true
        · simp only [he, if_true]
          show forIn (m := Id) rest acc _ = _
          rw [ih]; simp [List.filter, he]
        · simp only [he, if_false]
          show forIn (m := Id) rest (acc ++ e.2) _ = _
          rw [ih]; simp [List.filter, he, List.append_assoc]
  have hord : ∀ (es : List (Bool × List Col)) (acc : List Col),
      forIn (m := Id) es acc (fun entry r =>
          if (!entry.1) = true then ForInStep.yield (r ++ entry.2)
          else ForInStep.yield r)
        = acc ++ (es.filter (fun e => !e.1)).flatMap (fun e => e.2) := by
    intro es; induction es with
    | nil => intro acc; simp; rfl
    | cons e rest ih =>
        intro acc
        rw [List.forIn_cons]
        cases he : e.1
        · simp only [he, Bool.not_false, if_true]
          show forIn (m := Id) rest (acc ++ e.2) _ = _
          rw [ih]; simp [List.filter, he, List.append_assoc]
        · simp only [he, Bool.not_true, Bool.false_eq_true, if_false]
          show forIn (m := Id) rest acc _ = _
          rw [ih]; simp [List.filter, he]
  cases gb with
  | isNone => exact absurd rfl h
  | allFields =>
      simp only [implementation_getGroupBy, explicitCols, Id.run, bind, pure,
        List.nil_append, selectCols, orderByCols]
      cases metaOrdering <;>
        simp only [Bool.not_false, Bool.not_true, if_true, if_false,
          Bool.false_eq_true, hsel, hord, hs, List.nil_append, List.append_assoc]
  | explicit cols =>
      simp only [implementation_getGroupBy, explicitCols, Id.run, bind, pure,
        selectCols, orderByCols]
      cases metaOrdering <;>
        simp only [Bool.not_false, Bool.not_true, if_true, if_false,
          Bool.false_eq_true, hsel, hord, hs, List.nil_append, List.append_assoc]

theorem correct_getGroupBy :
    ∀ (metaOrdering : Bool) (gb : GroupBy)
      (select orderBy : List (Bool × List Col)) (having : List Col),
      problem_spec_getGroupBy metaOrdering gb select orderBy having
        (implementation_getGroupBy metaOrdering gb select orderBy having) := by
  intro metaOrdering gb select orderBy having
  unfold problem_spec_getGroupBy
  cases gb with
  | isNone => exact correct_getGroupBy_isNone metaOrdering select orderBy having
  | allFields =>
      rw [correct_getGroupBy_nonNone metaOrdering GroupBy.allFields select orderBy having
        (by simp)]
      simp [groupByExpressions]
  | explicit cols =>
      rw [correct_getGroupBy_nonNone metaOrdering (GroupBy.explicit cols) select orderBy having
        (by simp)]
      simp [groupByExpressions]

-- proof-end
