import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The decision modeled here is pure boolean logic over
--  FREE INPUTS describing a query's output-column state: whether the caller has
--  explicitly projected the output columns, whether the query already carries an
--  explicit list of select columns, and whether it merely carries annotation or
--  extra-selection columns. The downstream machinery these decisions gate —
--  subquery compilation and column reduction — is UNCHANGED code the decision
--  only triggers, never reshapes, so there is no callee contract to assume and
--  nothing for G-AX. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- The output-column state of a query that appears on the right-hand side of a
   membership test, as the narrowing decision observes it.

   * `explicitlyProjected`      — the caller has explicitly chosen the output
                                  columns the query returns (an explicit column
                                  projection was applied to it).
   * `hasExplicitSelectColumns` — the query already carries an explicit list of
                                  select columns.
   * `carriesAnnotations`       — the query carries annotation columns (e.g.
                                  produced by adding computed/aliased
                                  expressions to it).
   * `carriesExtraSelections`   — the query carries extra raw select columns. -/
structure RhsQuery where
  explicitlyProjected      : Bool
  hasExplicitSelectColumns : Bool
  carriesAnnotations       : Bool
  carriesExtraSelections   : Bool
deriving Inhabited, DecidableEq

/- Whether a right-hand-side query already designates the output columns it will
   return. A query designates its output columns ONLY when the caller has
   explicitly projected them; merely carrying annotation or extra-selection
   columns does not, on its own, designate the columns the query returns. -/
def designatesOutputColumns (q : RhsQuery) : Bool := q.explicitlyProjected

/- The narrowing decision: a right-hand-side membership subquery must be reduced
   to a single output column exactly when it does not already designate its
   output columns. -/
def narrowsToSingleColumn (q : RhsQuery) : Bool := ! designatesOutputColumns q

@[grind] lemma narrowsToSingleColumn_def (q : RhsQuery) :
    narrowsToSingleColumn q = (! q.explicitlyProjected) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a subquery used on the right-hand side of a membership test
   must be reduced to a single output column before the comparison. The
   reduction is required exactly when the subquery does not already designate the
   columns it returns — i.e. when the caller has NOT explicitly projected its
   output columns. A subquery that merely carries annotation or extra-selection
   columns has NOT thereby designated its output columns, so it must still be
   reduced to one column; otherwise the membership test would compare against a
   multi-column row set. `q` is read-only (not `mut`): the decision reads the
   query's column state and produces a fresh boolean, mutating nothing
   (directive 5). -/
method narrowRhsSubquery (q : RhsQuery) return (narrow : Bool)
  ensures narrow = narrowsToSingleColumn q
  do
    -- impl-start
    -- Pre-fix skeleton: "designates its output columns" is computed as a derived
    -- disjunction — true if the query carries an explicit select list OR
    -- annotation columns OR extra select columns. A query that merely carries
    -- annotation columns (no explicit projection) is therefore wrongly judged to
    -- designate its columns, so narrowing is skipped. The frozen spec ties the
    -- decision to explicit projection alone, so prove_correct MUST fail.
    let designated :=
      q.hasExplicitSelectColumns || q.carriesAnnotations || q.carriesExtraSelections
    return !designated
    -- impl-end

prove_correct narrowRhsSubquery by
  loom_solve
