import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the lookup result is taken as the input, and the
--  follow-up delete is observed only through the key it would target — modeled
--  deeply as the returned value. No outside callee contract is consumed.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A maintenance pass trims the oldest stored entries. To decide the trim
   boundary it consults a single-row lookup whose result is EITHER one row of
   column values OR absent (no row at all). The boundary-dependent action must
   only be taken when a row is actually present:

   - present row  → take the action, parameterised by the row's first column;
   - absent (none) → take NO action that reads from the (absent) row.

   The observable outcome is "the boundary used for the trim", reported as
   `some k` when a row is present (k = its first column) and `none` when the
   lookup yielded nothing — so the absent case is never made to read a column
   that does not exist.

   The lookup result `fetched` is read-only (not `mut`); the step never mutates
   it (directive 5). A present row is required to carry at least one column
   (a genuine result row is non-empty). A row is modeled as a `List Int`
   (column values), absence as `none`. -/
method cullStep (fetched : Option (List Int)) return (out : Option Int)
  require ∀ row, fetched = some row → row ≠ []
  ensures fetched = none → out = none
  ensures ∀ row, fetched = some row → out = some (row.head!)
  do
    -- impl-start
    let lastKey := fetched
    if lastKey.isSome then
      return some ((lastKey.getD []).head!)
    else
      return none
    -- impl-end

prove_correct cullStep by
  loom_solve
