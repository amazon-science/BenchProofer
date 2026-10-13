import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the reported size is the cardinality of the input
--  collection, modeled deeply.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A composite estimator is an ORDERED collection of constituent stages. A
   query for "how many stages does this composite hold?" returns the exact
   number of stages it was constructed from — every stage counted once
   (final stage and inert placeholder stages included), none omitted, none
   double-counted. The size is the cardinality of the stage collection, so an
   index handle spanning "from the start up to the size" covers the whole
   collection. The collection is read-only (not `mut`): the query never mutates
   it (directive 5). Stages are modeled as a `List Int`; only the cardinality
   is observed. -/
method compositeSize (steps : List Int) return (n : Nat)
  ensures n = steps.length
  do
    -- impl-start
    return steps.length
    -- impl-end

prove_correct compositeSize by
  loom_solve
