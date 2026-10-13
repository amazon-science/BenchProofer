import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts and no deep-model references. The operation is a
--  pure boolean decision over five independent yes/no signals about a result set;
--  every signal is read purely for its truth value, so there is nothing to
--  axiomatize. The `axioms` region is intentionally empty.)
-- axioms-end

-- pure-start
/- The exact decision the introspection flag must report.

   A result set answers "will my rows come back in a well-defined order?" from
   five independent yes/no signals:

     * `isEmpty`        — the result set is statically empty;
     * `hasRawOrder`    — an explicit raw / column ordering was attached;
     * `defaultOn`      — a default ordering inherited from the model is active;
     * `modelHasOrder`  — the model declares a default ordering at all;
     * `isGrouped`      — the result set collapses rows into groups.

   The flag is TRUE exactly when the result set is statically empty, OR an
   explicit ordering is attached, OR an inherited model default ordering is both
   active and declared AND the result set is NOT grouped. Collapsing rows into
   groups suppresses an inherited (non-explicit) default ordering: such a
   default no longer governs the surviving row order, so a grouped result set
   whose only ordering is that inherited default is NOT ordered. -/
def isOrdered (isEmpty hasRawOrder defaultOn modelHasOrder isGrouped : Bool) : Bool :=
  isEmpty || hasRawOrder || (defaultOn && modelHasOrder && !isGrouped)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The introspection flag of a result set. The five inputs are read-only yes/no
   signals (none is `mut`; the operation mutates nothing — directive 5) and the
   result is pinned exactly to the boolean decision above, so no implementation
   that disagrees on any of the thirty-two input combinations can verify.

   Alongside the exact-equality postcondition, four consequences any correct
   decision must exhibit are pinned, each tying the result to a witnessed input:
   an empty result set is always ordered; an explicitly-ordered result set is
   always ordered; a grouped result set whose only ordering is an inherited
   model default (no emptiness, no explicit ordering) is NOT ordered; and that
   same inherited default ordering on a non-grouped result set IS ordered. -/
method ordered (isEmpty : Bool) (hasRawOrder : Bool) (defaultOn : Bool)
    (modelHasOrder : Bool) (isGrouped : Bool) return (out : Bool)
  ensures out = isOrdered isEmpty hasRawOrder defaultOn modelHasOrder isGrouped
  ensures isEmpty = true → out = true
  ensures hasRawOrder = true → out = true
  ensures (isEmpty = false ∧ hasRawOrder = false ∧ isGrouped = true) → out = false
  ensures (isEmpty = false ∧ hasRawOrder = false ∧ defaultOn = true
            ∧ modelHasOrder = true ∧ isGrouped = false) → out = true
  do
    -- impl-start
    -- Pre-image: an active+declared model default ordering reported the result
    -- set as ordered REGARDLESS of grouping — the `!isGrouped` conjunct is
    -- absent. This MUST fail the spec whenever a grouped result set's only
    -- ordering is that inherited default (the grouped-not-ordered clause).
    if isEmpty then
      return true
    else
      if hasRawOrder then
        return true
      else
        if defaultOn && modelHasOrder then
          return true
        else
          return false
    -- impl-end

prove_correct ordered by
  loom_solve <;> simp_all [isOrdered]
