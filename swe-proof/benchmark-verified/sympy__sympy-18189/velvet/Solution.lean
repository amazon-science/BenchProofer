import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The base solver consulted when the caller requests the results in a particular
   variable ordering. It is the UNCHANGED routine that produces the full solution
   set for an equation, taking a single Boolean that selects whether the extra
   variant solutions (sign and value variants) are included alongside the base
   solution. It is invoked here, never redefined.

   Each solution it returns is a tuple of integer values, one per variable, listed
   in the routine's own canonical variable order; the whole result is the list of
   such tuples. It is modeled `opaque` with NO asserted `ensures`: the desired
   behavior assumes nothing about WHICH tuples it returns for a given flag — only
   that the flag it is given is the same one the caller asked for. Provenance +
   executable soundness check (that this is exactly the canonical solver's output
   for each flag value): mapping.md §3 / axiom_check.py (G-AX). -/
opaque baseSolve : Bool → List (List Int)
-- axioms-end

-- pure-start
/- Reindex one solution tuple into the requested variable order: `order` lists,
   for each requested position, the index of that variable within the base
   solver's canonical tuple, so the reindexed tuple gathers those components in
   the requested order. A pure positional gather over the tuple's components. -/
def reorderTuple (order : List Nat) (t : List Int) : List Int :=
  order.map (fun k => t[k]!)

/- Reindex every solution in a result set into the requested variable order,
   preserving the set of solutions and only relabeling each tuple's components. -/
def reorderAll (order : List Nat) (ts : List (List Int)) : List (List Int) :=
  ts.map (reorderTuple order)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Produce the solution set of an equation when the caller has requested the
   tuple components in a particular variable order that differs from the solver's
   canonical one.

   Desired behavior: the routine consults the base solver and then reindexes each
   returned tuple into the requested order. The Boolean `permute` selects whether
   the additional variant solutions are produced. That selection must hold
   regardless of the requested ordering: the base solver is consulted with the
   SAME `permute` the caller asked for, so requesting a non-canonical variable
   order never suppresses the variants the caller selected. The result is exactly
   the reindexing of whatever full set the base solver produces for that flag.

   `order` and `permute` are read-only (directive 5): the routine computes a set
   and mutates no input. `baseSolve` is the unchanged base solver (mapping.md §3);
   `reorderAll`/`reorderTuple` are the positional reindexing the routine applies
   (a function of `order` and the produced tuples only). -/
method reorderSolutions (order : List Nat) (permute : Bool)
    return (out : List (List Int))
  ensures out = reorderAll order (baseSolve permute)
  do
    -- impl-start
    -- Consult the base solver with the SAME variant flag the caller requested,
    -- then reindex each produced tuple into the requested variable order.
    let base := baseSolve permute
    let result := reorderAll order base
    return result
    -- impl-end

prove_correct reorderSolutions by
  loom_solve
