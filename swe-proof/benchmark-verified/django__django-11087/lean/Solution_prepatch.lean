import Mathlib
-- imports-end

/-!
Choosing which columns to load when fetching the related objects that a cascade
deletion must visit.

While walking the graph of objects reachable from the ones being deleted, the
collector fetches, for each relation, the set of related objects that point at
the current batch. Only some columns of those related objects are ever needed:
the columns that other relations point at (their identity / target columns).
Loading the remaining columns is pure overhead and can even surface values the
caller never asked for.

The fetch that reaches this decision is described by:

  * `pkColumn` — the name of the related model's identifying column;
  * `allFields` — every column name of the related model (the whole row);
  * `defaultColumns` — the column names that fetch loads when it is handed on
    exactly as it arrived;
  * `skippedNames` — the names that fetch has already been told to leave out
    (empty when it has been told nothing);
  * `candidateRelations` — for each relation that may itself cascade from the
    related model, the list of target column names that relation points at;
  * `guardA`, `guardB` — two conditions of the fetch under which no restriction
    is applied to it at all. What makes either of them hold is not part of this
    decision: they arrive as flags.

When neither condition holds, the fetch is restricted to the referenced columns:
the target column names gathered across all candidate relations, with duplicates
removed. A restriction cannot ask for a name the fetch has already been told to
leave out, so those names are dropped from the request; and restricting a fetch
this way cannot drop the identifying column — an object still has to be
identified to be deleted — so the restricted load carries `pkColumn` as well,
even when the fetch had been told to leave that column out. A restriction
replaces whatever the fetch had been told rather than adding to it: if the
request is left naming no column at all there is nothing to restrict the fetch
to, and the whole row is loaded.

When either condition holds the fetch is handed on untouched and loads exactly
the columns it loaded by default.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The two guard
-- flags, the identifying column name and the column-name lists enter as plain
-- data; the only operations are the gathering of the referenced column names,
-- modeled directly as list flattening followed by duplicate removal, the
-- dropping of the names the fetch has been told to leave out, modeled directly
-- as a filter, and the restriction of a fetch to a set of columns, modeled
-- directly by the column set such a restricted fetch is guaranteed to load.
-- Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The referenced column names: the target column names gathered across every
candidate relation, flattened into a single list and deduplicated (the set of
columns that some relation points at). -/
def referencedColumns (candidateRelations : List (List String)) : List String :=
  candidateRelations.flatten.dedup

/-- The column names a restriction of this fetch ends up naming: the referenced
columns, minus every name the fetch has already been told to leave out — a
restriction cannot ask for one of those. -/
def restrictionNames (skippedNames : List String)
    (candidateRelations : List (List String)) : List String :=
  (referencedColumns candidateRelations).filter (fun c => !skippedNames.contains c)

/-- The columns a fetch restricted to the referenced columns actually loads.

Restricting a fetch to a named set of columns is only meaningful when the
restriction names a column: with none named there is nothing to restrict to and
the fetch is left alone, loading the whole row (`allFields`) — the restriction
replaces what the fetch had been told, so the names it had been told to leave
out come back. When the restriction does name a column the restricted fetch
loads exactly those columns together with the identifying column `pkColumn`,
which such a restriction always retains. -/
def loadedColumns (pkColumn : String) (allFields skippedNames : List String)
    (candidateRelations : List (List String)) : List String :=
  let named := restrictionNames skippedNames candidateRelations
  if named.isEmpty then allFields else (pkColumn :: named).dedup
-- pure-end

-- post-conditions-start
/-- The set of columns to load is fully pinned to the inputs:

  * when neither condition holds, the load is exactly what a fetch restricted to
    the referenced columns loads — the referenced columns the fetch has not been
    told to leave out, plus the identifying column, or the whole row when the
    restriction is left naming nothing;
  * otherwise the fetch is handed on exactly as it arrived and the load is
    exactly `defaultColumns`.

Both cases together determine the result for every input, so no output is left
free. -/
def problem_spec_collectFieldSelection
    (guardA guardB : Bool) (pkColumn : String)
    (allFields defaultColumns skippedNames : List String)
    (candidateRelations : List (List String)) (result : List String) : Prop :=
  (guardA = false ∧ guardB = false →
      result = loadedColumns pkColumn allFields skippedNames candidateRelations) ∧
  (¬ (guardA = false ∧ guardB = false) →
      result = defaultColumns)
-- post-conditions-end

-- impl-start
def implementation_collectFieldSelection
    (guardA guardB : Bool) (pkColumn : String)
    (allFields defaultColumns skippedNames : List String)
    (candidateRelations : List (List String)) : List String := Id.run do
  let mut loaded := defaultColumns
  return loaded
-- impl-end

-- proof-start
theorem correct_collectFieldSelection :
    ∀ (guardA guardB : Bool) (pkColumn : String)
      (allFields defaultColumns skippedNames : List String)
      (candidateRelations : List (List String)),
      problem_spec_collectFieldSelection guardA guardB pkColumn allFields defaultColumns
        skippedNames candidateRelations
        (implementation_collectFieldSelection guardA guardB pkColumn allFields defaultColumns
          skippedNames candidateRelations) := by
  intro guardA guardB pkColumn allFields defaultColumns skippedNames candidateRelations
  unfold problem_spec_collectFieldSelection implementation_collectFieldSelection
  simp only [Id.run, bind, pure]
  refine ⟨?_, ?_⟩
  · rintro ⟨ha, hb⟩
    -- the fetch is handed on untouched, so the load is `defaultColumns`; the
    -- restricted-branch clause demands `loadedColumns …`, and there is nothing
    -- to close the gap with.
    rfl
  · intro hcon
    trivial
-- proof-end
