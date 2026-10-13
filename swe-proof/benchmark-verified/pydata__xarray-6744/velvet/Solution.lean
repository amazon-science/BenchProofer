import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the per-position index ranges of a one-dimensional
--  moving-window traversal are the operation under specification and are
--  modelled deeply below as exact integer arithmetic. The downstream slicing
--  and reduction that consume these ranges form the unchanged caller, not a
--  callee of this operation.)
-- axioms-end

-- pure-start
/- Forward shift of every block end. The justification mode of a moving window
   is observable only through this shift: a centred window is shifted forward by
   ceil(w / 2) = (w + 1) / 2 so that each block is symmetric about its position;
   an uncentred window shifts by 1 so the block ends at its position. For w = 1
   the two modes coincide (the shift is 1). -/
def endShift (w : Int) (center : Bool) : Int :=
  if center then (w + 1) / 2 else 1

/- End (exclusive) of the block at position i: its position advanced by the
   justification shift. -/
def endAt (i : Int) (w : Int) (center : Bool) : Int :=
  i + endShift w center

/- Start (inclusive) of the block at position i: w entries before its end,
   clamped to the start of the sequence. -/
def beginAt (i : Int) (w : Int) (center : Bool) : Int :=
  let raw := endAt i w center - w
  if raw > 0 then raw else 0

/- The block ends for a sequence of positions, in order. Front-recursive so a
   single unfold is available per loop step (the Velvet fold pattern). -/
def endsSeq (w : Int) (center : Bool) : List Int → List Int
  | []      => []
  | p :: ps => endAt p w center :: endsSeq w center ps

/- The block starts for a sequence of positions, in order. -/
def beginsSeq (w : Int) (center : Bool) : List Int → List Int
  | []      => []
  | p :: ps => beginAt p w center :: beginsSeq w center ps

@[grind] lemma endsSeq_nil (w : Int) (center : Bool) :
    endsSeq w center [] = [] := rfl
@[grind] lemma endsSeq_cons (w : Int) (center : Bool) (p : Int) (ps : List Int) :
    endsSeq w center (p :: ps) = endAt p w center :: endsSeq w center ps := rfl
@[grind] lemma beginsSeq_nil (w : Int) (center : Bool) :
    beginsSeq w center [] = [] := rfl
@[grind] lemma beginsSeq_cons (w : Int) (center : Bool) (p : Int) (ps : List Int) :
    beginsSeq w center (p :: ps) = beginAt p w center :: beginsSeq w center ps := rfl

/- The position labels for a length-n sequence: the integers 0, 1, …, n-1, in
   order (the i-th step exposes the block for position i). -/
def positions (n : Nat) : List Int := (List.range n).map (fun i => Int.ofNat i)

@[grind] lemma positions_length (n : Nat) : (positions n).length = n := by
  simp [positions]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The per-position block END indices of a length-n one-dimensional
   moving-window traversal with window size w (w > 0) and justification flag
   `center`. -/
method blockEnds (n : Nat) (w : Int) (center : Bool) return (out : List Int)
  require w > 0
  ensures out = endsSeq w center (positions n)
  do
    -- impl-start
    let labels := positions n
    let mut result : List Int := []
    let mut i := labels.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ labels.length
      invariant result = endsSeq w center (labels.drop i)
      done_with i = 0
      decreasing i
    do
      let p := labels[i - 1]!
      result := endAt p w center :: result
      i := i - 1
    return result
    -- impl-end

/- The per-position block START indices: w entries before each end, clamped to
   the start of the sequence. -/
method blockBegins (n : Nat) (w : Int) (center : Bool) return (out : List Int)
  require w > 0
  ensures out = beginsSeq w center (positions n)
  do
    -- impl-start
    let labels := positions n
    let mut result : List Int := []
    let mut i := labels.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ labels.length
      invariant result = beginsSeq w center (labels.drop i)
      done_with i = 0
      decreasing i
    do
      let p := labels[i - 1]!
      let raw := endAt p w center - w
      let s : Int := if raw > 0 then raw else 0
      result := s :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step for block ends: dropping one fewer position exposes
   the position at `i-1` on the front, so `endsSeq` peels one entry. -/
lemma endsSeq_drop_step (w : Int) (center : Bool) (ps : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ ps.length) :
    endsSeq w center (ps.drop (i - 1))
      = endAt ps[i - 1]! w center :: endsSeq w center (ps.drop i) := by
  have hlt : i - 1 < ps.length := by omega
  have hcons : ps.drop (i - 1) = ps[i - 1]! :: ps.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, endsSeq_cons]

/- The backward-fold step for block starts: same peel, with the clamped value. -/
lemma beginsSeq_drop_step (w : Int) (center : Bool) (ps : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ ps.length) :
    beginsSeq w center (ps.drop (i - 1))
      = beginAt ps[i - 1]! w center :: beginsSeq w center (ps.drop i) := by
  have hlt : i - 1 < ps.length := by omega
  have hcons : ps.drop (i - 1) = ps[i - 1]! :: ps.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, beginsSeq_cons]

prove_correct blockEnds by
  loom_solve
  rw [endsSeq_drop_step w center (positions n) i (by omega) (by omega)]
  simp_all

prove_correct blockBegins by
  loom_solve
  rw [beginsSeq_drop_step w center (positions n) i (by omega) (by omega)]
  simp_all [beginAt]
