import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The only callee invoked by the modeled operation is
   modeled DEEPLY as the pure function `withTarget` (a deep-model A-reference,
   validated against the real callee by axiom_check.py / G-AX), not consumed as
   an axiom. -/
-- axioms-end

-- pure-start
/- A deletion query is modeled by the list of usage counts of the tables it
   addresses, in the query's own table order; the table the deletion targets is
   the one at the head. A table is "live" when its usage count is positive. -/

/- The deletion's own use of the table it targets: that table's usage count goes
   up by one, and no other table's count changes. Deep model of an unchanged
   query-construction callee — provenance + executable soundness in mapping.md /
   axiom_check.py (G-AX). -/
def withTarget (rc : List Nat) : List Nat := (rc.headD 0 + 1) :: rc.tail

/- The number of live (positively-counted) tables. -/
def liveCount (rc : List Nat) : Nat := (rc.filter (fun n => n != 0)).length

@[grind] lemma withTarget_tail (rc : List Nat) :
    (withTarget rc).tail = rc.tail := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Decide whether a deletion can be compiled as a direct delete over the table
   it targets rather than via a subquery that selects the rows to remove. The
   direct form is available exactly when no table OTHER than the targeted one is
   live. -/
method directDeleteEligible (mut tableRefs : List Nat) return (direct : Bool)
  ensures tableRefs = withTarget tableRefsOld
  ensures direct ↔ liveCount tableRefsOld.tail = 0
  do
    -- impl-start
    return liveCount tableRefs == 1
    -- impl-end

prove_correct directDeleteEligible by
  loom_solve
