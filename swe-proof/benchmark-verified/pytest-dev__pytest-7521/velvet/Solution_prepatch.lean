import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The single operation whose behavior is pinned here — the
   read-back of buffered stream content — is modeled DEEPLY in the `pure` region
   (`readback`) and validated against the real platform text-stream reader by
   axiom_check.py (G-AX), so it is an A-reference, not a consumed axiom
   (mapping.md §3.1). -/
-- axioms-end

-- pure-start
/- The content recovered when buffered stream text is read back: every code
   point is returned exactly as it was buffered — no code point is rewritten,
   inserted, dropped, or merged with a neighbour. Written front-recursively so a
   single unfold is available per loop step (the backward-fold pattern). -/
def readback : List Char → List Char
  | []      => []
  | c :: cs => c :: readback cs

@[grind] lemma readback_nil : readback [] = [] := rfl
@[grind] lemma readback_cons (c : Char) (cs : List Char) :
    readback (c :: cs) = c :: readback cs := rfl

/- Read-back returns the buffered content unchanged: the recovered sequence is
   the input sequence itself. Marked `@[grind]` so `loom_solve` can use it to
   discharge the postcondition. -/
@[grind] lemma readback_id (cs : List Char) : readback cs = cs := by
  induction cs with
  | nil => rfl
  | cons c cs ih => rw [readback_cons, ih]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method readbackStream (text : List Char) return (out : List Char)
  ensures out = readback text
  ensures out = text
  do
    -- impl-start
    -- Pre-image skeleton: the read-back stream applies universal-newline
    -- translation, rewriting each carriage return (U+000D) to a line feed
    -- (U+000A). The frozen spec requires verbatim read-back (out = readback
    -- text = text), so prove_correct MUST fail on any input containing U+000D.
    let mut result : List Char := []
    let mut i := text.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ text.length
      invariant result = readback (text.drop i)
      done_with i = 0
      decreasing i
    do
      let c := text[i - 1]!
      let t : Char := if c = '\r' then '\n' else c
      result := t :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `readback` peels one code point. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma readback_drop_step (text : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ text.length) :
    readback (text.drop (i - 1)) = text[i - 1]! :: readback (text.drop i) := by
  have hlt : i - 1 < text.length := by omega
  have hcons : text.drop (i - 1) = text[i - 1]! :: text.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, readback_cons]

prove_correct readbackStream by
  loom_solve
  rw [readback_drop_step text i (by omega) (by omega)]
  simp_all
