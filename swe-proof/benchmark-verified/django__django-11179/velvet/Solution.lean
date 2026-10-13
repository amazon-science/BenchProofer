import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the deletion-count is taken as a given input — the
--  batch removal that produces it is not re-derived here and is observed only
--  through that count. The state change under spec — clearing the record's
--  identity handle — is modeled deeply as an assignment, no outside contract
--  consumed.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A short-circuit removal handles the case of a single standalone record that
   no other record depends on: it removes the record in one batch and reports
   how many rows that batch removed.

   The record carries a mutable identity handle (`pk`) — an optional integer
   that is present (`some k`) while the record denotes a stored row. After the
   removal short-circuit completes, the record no longer denotes any stored row,
   so its identity handle must be CLEARED (`none`), regardless of what it was
   before.

   The reported count is exactly the batch's removal count, passed in as
   `removed`; the short-circuit must report that count UNCHANGED — clearing the
   handle must not perturb the returned number.

   `pk` is genuinely mutated (declared `mut`) and its post-state is pinned
   exactly to `none` (directive 5: the unchanged frame is the count, stated via
   the returned value equalling `removed`; the changed frame `pk` is pinned to
   its exact post-state). -/
method fastDelete (mut pk : Option Int) (removed : Nat) return (count : Nat)
  ensures pk = none
  ensures count = removed
  do
    -- impl-start
    pk := none
    return removed
    -- impl-end

prove_correct fastDelete by
  loom_solve
