import Mathlib
-- imports-end

/-!
Combining the bulk-deletion operations that a cascading delete schedules.

When a record is deleted, every relation that cascades from it contributes a
bulk deletion of the rows on the far side of that relation. Each such cascading
relation is described by two observables:

  * the target table the cascade lands on (its identity), and
  * the column the relation joins on.

Several distinct relations may land on the SAME target table (a table that is
referenced from the deleted record through more than one column). The naive
schedule issues one bulk deletion per relation, so a table referenced through
`k` columns is hit by `k` separate operations.

The desired behavior groups the scheduled operations by their target table: the
relations landing on one table are merged into a single bulk operation for that
table, carrying the list of all the columns those relations join on. Concretely,
given the relations in the order they are discovered, the result is one entry per
distinct target table — the tables in first-discovery order — and within each
entry the joined columns in the order their relations were discovered. A table
referenced through several columns therefore yields exactly ONE operation rather
than several.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Each cascading
-- relation enters as plain data — a pair of (target-table identity, joined-column
-- identity); the decision under spec is purely how those pairs are grouped by
-- their target table, modeled directly as an order-preserving grouping fold.
-- Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A target table identity. Modeled as a `Nat` (an injective encoding of the
distinct table identities; only equality is observed). -/
abbrev Table := Nat

/-- A joined-column identity, likewise modeled as a `Nat`. -/
abbrev Column := Nat

/-- Insert one relation `(m, f)` into the running grouping. If the target table
`m` already has an entry, append the column `f` to that entry's column list (in
discovery order); otherwise start a new entry for `m` at the end (so tables keep
their first-discovery order). -/
def insertRelation (acc : List (Table × List Column)) (m : Table) (f : Column) :
    List (Table × List Column) :=
  if acc.any (fun p => p.1 == m) then
    acc.map (fun p => if p.1 == m then (p.1, p.2 ++ [f]) else p)
  else
    acc ++ [(m, [f])]

/-- Group the scheduled relations by their target table, preserving the
first-discovery order of tables and, within each table, the discovery order of
the joined columns. -/
def groupByTable (rels : List (Table × Column)) : List (Table × List Column) :=
  rels.foldl (fun acc p => insertRelation acc p.1 p.2) []
-- pure-end

-- post-conditions-start
/-- The scheduled bulk operations, fully pinned to the input relations: the
result is exactly the relations grouped by their target table — one entry per
distinct table in first-discovery order, each carrying the joined columns of the
relations landing on that table in discovery order. This determines the result
for every input, so no output component is left free. -/
def problem_spec_combineFastDeletes
    (rels : List (Table × Column)) (result : List (Table × List Column)) : Prop :=
  result = groupByTable rels
-- post-conditions-end

-- impl-start
def implementation_combineFastDeletes
    (rels : List (Table × Column)) : List (Table × List Column) := Id.run do
  -- Pre-patch (buggy) skeleton: one bulk operation is scheduled per relation,
  -- with no combining by target table. Each relation becomes its own singleton
  -- entry, so a table referenced through several columns yields several
  -- operations instead of one.
  let mut groups : List (Table × List Column) := []
  for p in rels do
    groups := groups ++ [(p.1, [p.2])]
  return groups
-- impl-end

-- proof-start
-- Gold proof body carried over from the patched bundle. Against the buggy impl
-- above it fails to typecheck (the loop no longer matches `groupByTable`), which
-- is exactly the G-DIFF signal: the spec sees the bug.
theorem forIn_group_eq_foldl (rels : List (Table × Column)) (init : List (Table × List Column)) :
    (Id.run (forIn rels init (fun p acc =>
      (if acc.any (fun q => q.1 == p.1) then
        ForInStep.yield (acc.map (fun q => if q.1 == p.1 then (q.1, q.2 ++ [p.2]) else q))
      else ForInStep.yield (acc ++ [(p.1, [p.2])]) : Id (ForInStep (List (Table × List Column)))))))
    = rels.foldl (fun acc p => insertRelation acc p.1 p.2) init := by
  induction rels generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons, List.foldl_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : (init.any (fun q => q.1 == a.1)) = true
    · simp only [h, if_true, insertRelation, ih]
    · simp only [h, Bool.false_eq_true, if_false, insertRelation, ih]

theorem correct_combineFastDeletes :
    ∀ (rels : List (Table × Column)),
      problem_spec_combineFastDeletes rels
        (implementation_combineFastDeletes rels) := by
  intro rels
  unfold problem_spec_combineFastDeletes implementation_combineFastDeletes groupByTable
  have h2 : (Id.run (do
      let r ← forIn rels [] fun p acc =>
        (if acc.any (fun q => q.1 == p.1) then
          (do pure PUnit.unit; pure (ForInStep.yield (acc.map (fun q => if q.1 == p.1 then (q.1, q.2 ++ [p.2]) else q))))
        else (do pure PUnit.unit; pure (ForInStep.yield (acc ++ [(p.1, [p.2])]))) : Id (ForInStep (List (Table × List Column))))
      pure r) : List (Table × List Column))
    = Id.run (forIn rels [] fun p acc =>
        (if acc.any (fun q => q.1 == p.1) then
          ForInStep.yield (acc.map (fun q => if q.1 == p.1 then (q.1, q.2 ++ [p.2]) else q))
        else ForInStep.yield (acc ++ [(p.1, [p.2])]) : Id (ForInStep (List (Table × List Column))))) := rfl
  rw [show (Id.run _ : List (Table × List Column)) = _ from h2]
  exact forIn_group_eq_foldl rels []
-- proof-end
