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
  for entry in orderBy do
    if !entry.1 then
      for col in entry.2 do
        expressions := expressions ++ [col]
  for col in having do
    expressions := expressions ++ [col]
  return expressions
-- impl-end

-- proof-start
theorem correct_getGroupBy :
    ∀ (metaOrdering : Bool) (gb : GroupBy)
      (select orderBy : List (Bool × List Col)) (having : List Col),
      problem_spec_getGroupBy metaOrdering gb select orderBy having
        (implementation_getGroupBy metaOrdering gb select orderBy having) := by
  sorry
-- proof-end
