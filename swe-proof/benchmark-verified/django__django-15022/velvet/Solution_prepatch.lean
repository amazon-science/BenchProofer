import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-item-per-word match test — "does this related
--  item match this search word, on at least one of the searched fields" — is an
--  UNCHANGED callee, taken here as a FREE INPUT `matchTerm`. The spec makes no
--  behavioural claim about it and holds for every value, so there is nothing to
--  validate against a real callee, hence no G-AX.)
-- axioms-end

-- pure-start
/- "Does one single related item match EVERY search word?" — the conjunction of
   the per-word match test `matchOf` over the word list. Written front-recursively
   so a single unfold is available per loop step (the backward fold pattern,
   plan §5.4). Empty word list ⇒ vacuously matched ⇒ `true`. -/
def conjTerms (matchOf : Nat → Bool) : List Nat → Bool
  | []      => true
  | t :: ts => matchOf t && conjTerms matchOf ts

@[grind] lemma conjTerms_nil (f : Nat → Bool) : conjTerms f [] = true := rfl
@[grind] lemma conjTerms_cons (f : Nat → Bool) (t : Nat) (ts : List Nat) :
    conjTerms f (t :: ts) = (f t && conjTerms f ts) := rfl

/- "Is there SOME related item that matches every search word?" — the disjunction
   over the related items of `conjTerms (matchTerm r) terms` ("item `r` matches all
   words"). Front-recursive for the same per-step unfold. Empty item list ⇒ no
   witness ⇒ `false`. The `terms` list is the shared word list every item is tested
   against. -/
def anyRecord (matchTerm : Nat → Nat → Bool) (terms : List Nat) : List Nat → Bool
  | []      => false
  | r :: rs => conjTerms (matchTerm r) terms || anyRecord matchTerm terms rs

@[grind] lemma anyRecord_nil (f : Nat → Nat → Bool) (terms : List Nat) :
    anyRecord f terms [] = false := rfl
@[grind] lemma anyRecord_cons (f : Nat → Nat → Bool) (terms : List Nat)
    (r : Nat) (rs : List Nat) :
    anyRecord f terms (r :: rs) = (conjTerms (f r) terms || anyRecord f terms rs) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The membership decision for one candidate row of the outer collection, when a
   search over its related items is in effect (at least one search word present).

   A row is kept exactly when a SINGLE related item matches all of the search
   words at once: `anyRecord matchTerm terms records` — there exists a related
   item `r` such that for every search word `t`, `matchTerm r t` holds. Words are
   NOT allowed to be satisfied by different items: the matching item must be the
   same for all words.

   `records` (the related items), `terms` (the search words) and `matchTerm` (the
   per-item-per-word test) are read-only; the decision mutates nothing it is handed
   (directive 5). -/
method searchKeepsRow (records : List Nat) (terms : List Nat) (matchTerm : Nat → Nat → Bool)
    return (result : Bool)
  require 0 < terms.length
  ensures result = anyRecord matchTerm terms records
  do
    -- impl-start
    -- Pre-image skeleton: the words are accumulated one at a time, each step
    -- keeping the row only if SOME related item matches THAT word — the existence
    -- of a matching item is re-decided per word, independently, so different words
    -- may be satisfied by different items. The frozen spec demands a SINGLE item
    -- match all words (`anyRecord`), so prove_correct MUST fail.
    let mut keep : Bool := true
    let mut i := terms.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ terms.length
      invariant keep = (terms.drop i).all (fun t => records.any (fun r => matchTerm r t))
      done_with i = 0
      decreasing i
    do
      let t := terms[i - 1]!
      let someItem := records.any (fun r => matchTerm r t)
      keep := someItem && keep
      i := i - 1
    return keep
    -- impl-end

/- The backward-fold step over the related items: dropping one fewer item exposes
   the item at `i-1` on the front, so `anyRecord` peels one disjunct. The single
   goal `loom_solve` leaves for the loop body. -/
lemma anyRecord_drop_step (f : Nat → Nat → Bool) (terms : List Nat)
    (records : List Nat) (i : Nat) (hi : 0 < i) (hle : i ≤ records.length) :
    anyRecord f terms (records.drop (i - 1))
      = (conjTerms (f records[i - 1]!) terms || anyRecord f terms (records.drop i)) := by
  have hlt : i - 1 < records.length := by omega
  have hcons : records.drop (i - 1) = records[i - 1]! :: records.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, anyRecord_cons]

/- The backward-fold step over the search words: the conjunction analogue of
   `anyRecord_drop_step`. Carried for the alternative aggregate over words; a
   generic list lemma, content-neutral. -/
lemma conjTerms_drop_step (matchOf : Nat → Bool) (terms : List Nat) (i : Nat)
    (hi : 0 < i) (hle : i ≤ terms.length) :
    conjTerms matchOf (terms.drop (i - 1))
      = (matchOf terms[i - 1]! && conjTerms matchOf (terms.drop i)) := by
  have hlt : i - 1 < terms.length := by omega
  have hcons : terms.drop (i - 1) = terms[i - 1]! :: terms.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, conjTerms_cons]

prove_correct searchKeepsRow by
  loom_solve
  rw [anyRecord_drop_step matchTerm terms records i (by omega) (by omega)]
  simp_all
