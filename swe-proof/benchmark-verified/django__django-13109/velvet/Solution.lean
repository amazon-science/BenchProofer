import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The existence test that validates an identity
--  reference is modeled DEEPLY as a per-record disjunction over the COMPLETE
--  record collection below; the collection the test ranges over is the input
--  carrier itself, not an outside contract. There is no `axiom` declaration and
--  no A-reference deep model of an outside callee.)
-- axioms-end

-- pure-start
/- One stored record considered when validating an identity reference. It
   carries only the two fields the operation observes: `key`, the stored value
   of the referenced field (a match is when it equals the target identity), and
   `hidden`, whether this record is filtered out of the model's everyday/default
   view by a custom view filter. A validity check that consults the COMPLETE
   record collection must consider every record regardless of `hidden`. -/
structure Record where
  key : Int
  hidden : Bool
deriving Inhabited, DecidableEq

/- Whether a single record matches the target identity: the stored referenced
   value equals the target. The match does NOT depend on `hidden` — a record
   that is hidden from the everyday view still matches if its key matches. -/
def matchesTarget (target : Int) (r : Record) : Bool :=
  r.key == target

/- Whether ANY record in the collection matches the target identity, over the
   COMPLETE collection. Front-recursive so a single unfold is available per loop
   step (the backward-fold pattern). Because every record is consulted, a
   matching record contributes `true` even when it is hidden from the everyday
   view — which is exactly the behavior a complete-collection existence test
   demands. -/
def existsMatch (target : Int) : List Record → Bool
  | []      => false
  | r :: rs => matchesTarget target r || existsMatch target rs

@[grind] lemma existsMatch_nil (target : Int) : existsMatch target [] = false := rfl
@[grind] lemma existsMatch_cons (target : Int) (r : Record) (rs : List Record) :
    existsMatch target (r :: rs) = (matchesTarget target r || existsMatch target rs) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method validateExists (rows : List Record) (target : Int) return (out : Bool)
  ensures out = existsMatch target rows
  do
    -- impl-start
    let mut found : Bool := false
    let mut i := rows.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ rows.length
      invariant found = existsMatch target (rows.drop i)
      done_with i = 0
      decreasing i
    do
      let r := rows[i - 1]!
      found := matchesTarget target r || found
      i := i - 1
    return found
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the record at
   `i-1` on the front, so `existsMatch` peels one disjunct. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma existsMatch_drop_step (rows : List Record) (target : Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ rows.length) :
    existsMatch target (rows.drop (i - 1))
      = (matchesTarget target rows[i - 1]! || existsMatch target (rows.drop i)) := by
  have hlt : i - 1 < rows.length := by omega
  have hcons : rows.drop (i - 1) = rows[i - 1]! :: rows.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, existsMatch_cons]

prove_correct validateExists by
  loom_solve
  rw [existsMatch_drop_step rows target i (by omega) (by omega)]
  simp_all
