import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- An entry of the candidate collection. `text` is the entry's canonical
   textual rendering; `wrapped` records whether the entry is held as a
   structured value rather than as a plain text value. The intended membership
   test depends only on `text`: two entries denote the same location exactly
   when their textual renderings coincide, irrespective of how each is stored. -/
structure Entry where
  text : List Char
  wrapped : Bool
  deriving DecidableEq, Inhabited

/- Whether `target` coincides, by textual rendering, with some entry of the
   collection. Front-recursive so a single unfold is available per loop step
   (the fold pattern). The comparison looks only at `text`, so the storage form
   (`wrapped`) of an entry is immaterial. -/
def matchesText (target : List Char) : List Entry → Bool
  | []      => false
  | e :: es => (e.text == target) || matchesText target es

@[grind] lemma matchesText_nil (t : List Char) : matchesText t [] = false := rfl
@[grind] lemma matchesText_cons (t : List Char) (e : Entry) (es : List Entry) :
    matchesText t (e :: es) = ((e.text == t) || matchesText t es) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method detectCollision (target : List Char) (entries : List Entry) return (out : Bool)
  ensures out = matchesText target entries
  do
    -- impl-start
    let mut found := false
    let mut i := entries.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ entries.length
      invariant found = matchesText target (entries.drop i)
      done_with i = 0
      decreasing i
    do
      let e := entries[i - 1]!
      found := (e.text == target) || found
      i := i - 1
    return found
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `matchesText` peels one membership test. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma matchesText_drop_step (target : List Char) (entries : List Entry) (i : Nat)
    (hi : 0 < i) (hle : i ≤ entries.length) :
    matchesText target (entries.drop (i - 1))
      = ((entries[i - 1]!.text == target) || matchesText target (entries.drop i)) := by
  have hlt : i - 1 < entries.length := by omega
  have hcons : entries.drop (i - 1) = entries[i - 1]! :: entries.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, matchesText_cons]

prove_correct detectCollision by
  loom_solve
  rw [matchesText_drop_step target entries i (by omega) (by omega)]
  simp_all
