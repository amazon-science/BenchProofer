import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The modeled function is itself a changed function
--  whose new result is a closed expression of its input, modeled deeply. It
--  calls no unchanged callee whose contract the proof would have to consume, so
--  there is nothing to axiomatize — see refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- An SQL expression node, abstracted to the single observation that decides its
   contribution to a GROUP BY clause: whether it is a non-deterministic value
   generator — a node whose value is freshly drawn for every row and therefore
   denotes no stable column. -/
structure Expr where
  isNondetGenerator : Bool
  deriving Inhabited, DecidableEq

/- The grouping columns a value-level (non-aggregate) leaf expression contributes
   to a GROUP BY clause. A leaf that denotes a stable column contributes itself,
   so the grouping is taken over that column. A non-deterministic value generator
   denotes no stable column, so it contributes none and leaves the grouping to be
   determined by the genuine columns alone. -/
@[grind] def groupingContribution (e : Expr) : List Expr :=
  if e.isNondetGenerator then [] else [e]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- When a non-deterministic value generator appears in an ORDER BY clause, the
   query asks it which grouping columns it contributes to the GROUP BY clause.
   Because such a generator's value is freshly drawn per row it denotes no stable
   column, so it must contribute none: the contributed list is empty and the
   grouping is left to the genuine columns. The node is read-only (not `mut`);
   computing its contribution mutates nothing (directive 5). The node and the
   contributed column list are modeled as `Expr` / `List Expr`. -/
method groupingColumns (e : Expr) return (out : List Expr)
  require e.isNondetGenerator = true
  ensures out = groupingContribution e
  ensures out = []
  do
    -- impl-start
    return []
    -- impl-end

prove_correct groupingColumns by
  loom_solve
