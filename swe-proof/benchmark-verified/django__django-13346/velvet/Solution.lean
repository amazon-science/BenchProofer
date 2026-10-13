import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. `bareTok`, `wrapOf` and `wrapHoldsValue` are ordinary
--  input parameters, not contracts about an outside callee: `wrapOf` is a plain
--  total function the caller supplies and `wrapHoldsValue` a plain `Bool`. The
--  `require` states only that each listed value's alternate token differs from
--  the plain one. No `axiom` is declared and no outside callee's behavior is
--  assumed.)
-- axioms-end

-- pure-start
/- The operand token ONE listed value contributes to a membership comparison.
   A boolean capability flag `native` selects it: when the flag holds the token
   is the plain `bareTok`; when it does not, the token is `wrapOf v`, the
   alternate token the supplied map assigns to that listed value. -/
def slotToken (native : Bool) (bareTok : List Char) (wrapOf : Int → List Char)
    (v : Int) : List Char :=
  if native then bareTok else wrapOf v

/- The per-slot token sequence for a whole membership list: one token per listed
   value, in order, each obtained by applying `slotToken` to that slot's own
   listed value. Front-recursive so a single unfold is available per loop step
   (the backward-fold pattern). -/
def clauseTokens (native : Bool) (bareTok : List Char) (wrapOf : Int → List Char) :
    List Int → List (List Char)
  | []      => []
  | v :: vs => slotToken native bareTok wrapOf v :: clauseTokens native bareTok wrapOf vs

@[grind] lemma clauseTokens_nil (native : Bool) (bareTok : List Char)
    (wrapOf : Int → List Char) :
    clauseTokens native bareTok wrapOf [] = [] := rfl
@[grind] lemma clauseTokens_cons (native : Bool) (bareTok : List Char)
    (wrapOf : Int → List Char) (v : Int) (vs : List Int) :
    clauseTokens native bareTok wrapOf (v :: vs)
      = slotToken native bareTok wrapOf v :: clauseTokens native bareTok wrapOf vs := rfl

/- The listed values that must still travel ALONGSIDE the clause, in order — all
   of them or none. Which it is is a property of the BRANCH the clause was built
   on, never of the text of any one token: on the plain branch every listed value
   travels, and on the alternate branch the supplied `wrapHoldsValue` records
   whether that branch's token family still needs its values handed over
   separately. The flag is a property of the family as a whole, and is never read
   off an individual token's characters. -/
def clauseSuppliedValues (native wrapHoldsValue : Bool) (vals : List Int) :
    List Int :=
  if native then vals
  else if wrapHoldsValue then [] else vals
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build a membership comparison's right-hand side over a list of listed values,
   as the pair it is only usable as: the operand tokens, and the listed values
   that still have to be handed over alongside them.

   Desired behaviour of the tokens: every listed value contributes exactly one
   operand token, in order, and the boolean capability flag `native` selects
   which — the plain `bareTok` on every slot when it holds, and otherwise each
   slot's own `wrapOf v`.

   Desired behaviour of the accompanying values: all of them or none, following
   the BRANCH. Every listed value on the `native` branch, unchanged and in order;
   on the other branch, as `wrapHoldsValue` records for the alternate token
   family. Neither component may be chosen independently of the other: a clause
   whose tokens still need their values but hands none over, or which hands over
   values its tokens have no place for, cannot be evaluated.

   `vals`, `native`, `bareTok`, `wrapOf`, `wrapHoldsValue` are all read-only
   (none is `mut`); the build mutates nothing observable (directive 5). The
   `require` records that each listed value's alternate token differs from the
   plain token. -/
method buildMembershipClause (vals : List Int) (native : Bool)
    (bareTok : List Char) (wrapOf : Int → List Char) (wrapHoldsValue : Bool)
    return (out : List (List Char) × List Int)
  require ∀ v ∈ vals, wrapOf v ≠ bareTok
  ensures out.1 = clauseTokens native bareTok wrapOf vals
  ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
  do
    -- impl-start
    -- The operand token for each slot, selected by the capability flag: the plain
    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
    -- listed value is mapped to. The values handed over alongside follow the
    -- branch: none at all where the alternate tokens keep their own values,
    -- every listed value otherwise.
    let mut result : List (List Char) := []
    let mut i := vals.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ vals.length
      invariant result = clauseTokens native bareTok wrapOf (vals.drop i)
      done_with i = 0
      decreasing i
    do
      let v := vals[i - 1]!
      result := (if native then bareTok else wrapOf v) :: result
      i := i - 1
    return (result, if native then vals else (if wrapHoldsValue then [] else vals))
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes one more slot on
   the front, so `clauseTokens` peels one `slotToken` — the one for that slot's
   own listed value. This is the single goal `loom_solve` leaves for the loop
   body. -/
lemma clauseTokens_drop_step (native : Bool) (bareTok : List Char)
    (wrapOf : Int → List Char) (vals : List Int) (i : Nat) (hi : 0 < i)
    (hle : i ≤ vals.length) :
    clauseTokens native bareTok wrapOf (vals.drop (i - 1))
      = slotToken native bareTok wrapOf vals[i - 1]!
          :: clauseTokens native bareTok wrapOf (vals.drop i) := by
  have hlt : i - 1 < vals.length := by omega
  have hcons : vals.drop (i - 1) = vals[i - 1]! :: vals.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, clauseTokens_cons]

prove_correct buildMembershipClause by
  loom_solve
  · rw [clauseTokens_drop_step native bareTok wrapOf vals i (by omega) (by omega)]
    simp_all [slotToken]
  · simp_all [clauseSuppliedValues]
