import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-permission test on the related model and the
--  inherited fallback decision are taken as FREE INPUTS — `userHasPerm` and
--  `superResult` — so the spec makes no behavioural claim about them and holds
--  for every value. Nothing to check against a real callee, hence no G-AX.)
-- axioms-end

-- pure-start
/- The two permissions whose codenames are ever interrogated on the related
   model: the right to VIEW it and the right to CHANGE it. -/
inductive Perm where
  | view
  | change
  deriving DecidableEq, Inhabited

/- "Does the principal hold ANY of the listed permissions (on the related
   model)?" — the disjunction of the per-permission test over the list. Written
   front-recursively so a single unfold is available per loop step (the backward
   fold pattern, plan §5.4). Empty list ⇒ no permission ⇒ `false`. -/
def anyPerm (userHasPerm : Perm → Bool) : List Perm → Bool
  | []      => false
  | p :: ps => userHasPerm p || anyPerm userHasPerm ps

@[grind] lemma anyPerm_nil (f : Perm → Bool) : anyPerm f [] = false := rfl
@[grind] lemma anyPerm_cons (f : Perm → Bool) (p : Perm) (ps : List Perm) :
    anyPerm f (p :: ps) = (f p || anyPerm f ps) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The disjunctive permission probe: returns whether the principal holds at
   least one of the requested permissions on the related model. It folds the
   per-permission test `userHasPerm` over the requested list. `userHasPerm` and
   `perms` are read-only (not `mut`); the probe mutates nothing it is handed
   (directive 5). -/
method holdsAnyTargetPerm (userHasPerm : Perm → Bool) (perms : List Perm) return (result : Bool)
  ensures result = anyPerm userHasPerm perms
  do
    -- impl-start
    let mut acc : Bool := false
    let mut i := perms.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ perms.length
      invariant acc = anyPerm userHasPerm (perms.drop i)
      done_with i = 0
      decreasing i
    do
      let p := perms[i - 1]!
      acc := userHasPerm p || acc
      i := i - 1
    return acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `anyPerm` peels one disjunct. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma anyPerm_drop_step (f : Perm → Bool) (perms : List Perm) (i : Nat)
    (hi : 0 < i) (hle : i ≤ perms.length) :
    anyPerm f (perms.drop (i - 1)) = (f perms[i - 1]! || anyPerm f (perms.drop i)) := by
  have hlt : i - 1 < perms.length := by omega
  have hcons : perms.drop (i - 1) = perms[i - 1]! :: perms.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, anyPerm_cons]

prove_correct holdsAnyTargetPerm by
  loom_solve
  rw [anyPerm_drop_step userHasPerm perms i (by omega) (by omega)]
  simp_all

/- Authority to ADD a row of the link relation. An implicitly-created link
   relation carries no permissions of its own, so for it authority is derived
   from the related model: the principal may add only if it holds the CHANGE
   permission there. For any other relation the ordinary inherited decision
   (`superResult`) stands. `autoCreated`, `userHasPerm`, `superResult` are
   read-only (directive 5). -/
method addRelationAllowed (autoCreated : Bool) (userHasPerm : Perm → Bool) (superResult : Bool) return (result : Bool)
  ensures result = (if autoCreated then anyPerm userHasPerm [Perm.change] else superResult)
  do
    -- impl-start
    -- Pre-image skeleton: for an implicitly-created link relation the add gate
    -- delegated to the same probe the VIEW gate uses (VIEW-or-CHANGE), so a
    -- principal holding only the VIEW permission was granted add authority. The
    -- frozen spec requires the CHANGE-only probe, so prove_correct MUST fail.
    let r ← if autoCreated then
        holdsAnyTargetPerm userHasPerm [Perm.view, Perm.change]
      else
        pure superResult
    return r
    -- impl-end

prove_correct addRelationAllowed by
  loom_solve

/- Authority to CHANGE a row of the link relation. Same derivation as
   `addRelationAllowed`: for an implicitly-created link relation it requires the
   CHANGE permission on the related model; otherwise the inherited decision. -/
method changeRelationAllowed (autoCreated : Bool) (userHasPerm : Perm → Bool) (superResult : Bool) return (result : Bool)
  ensures result = (if autoCreated then anyPerm userHasPerm [Perm.change] else superResult)
  do
    -- impl-start
    -- Pre-image skeleton: VIEW-or-CHANGE probe (see addRelationAllowed). MUST
    -- fail the CHANGE-only frozen spec for a VIEW-only principal.
    let r ← if autoCreated then
        holdsAnyTargetPerm userHasPerm [Perm.view, Perm.change]
      else
        pure superResult
    return r
    -- impl-end

prove_correct changeRelationAllowed by
  loom_solve

/- Authority to DELETE a row of the link relation. Same derivation: for an
   implicitly-created link relation it requires the CHANGE permission on the
   related model; otherwise the inherited decision. -/
method deleteRelationAllowed (autoCreated : Bool) (userHasPerm : Perm → Bool) (superResult : Bool) return (result : Bool)
  ensures result = (if autoCreated then anyPerm userHasPerm [Perm.change] else superResult)
  do
    -- impl-start
    -- Pre-image skeleton: VIEW-or-CHANGE probe (see addRelationAllowed). MUST
    -- fail the CHANGE-only frozen spec for a VIEW-only principal.
    let r ← if autoCreated then
        holdsAnyTargetPerm userHasPerm [Perm.view, Perm.change]
      else
        pure superResult
    return r
    -- impl-end

prove_correct deleteRelationAllowed by
  loom_solve

/- Authority to VIEW a row of the link relation. For an implicitly-created link
   relation the principal may view it if it holds EITHER the VIEW or the CHANGE
   permission on the related model (holding CHANGE implies viewing is allowed);
   otherwise the inherited decision. -/
method viewRelationAllowed (autoCreated : Bool) (userHasPerm : Perm → Bool) (superResult : Bool) return (result : Bool)
  ensures result = (if autoCreated then anyPerm userHasPerm [Perm.view, Perm.change] else superResult)
  do
    -- impl-start
    -- The VIEW gate is unchanged by the fix: VIEW-or-CHANGE on the related
    -- model. This clause already matched the frozen spec pre-patch.
    let r ← if autoCreated then
        holdsAnyTargetPerm userHasPerm [Perm.view, Perm.change]
      else
        pure superResult
    return r
    -- impl-end

prove_correct viewRelationAllowed by
  loom_solve
