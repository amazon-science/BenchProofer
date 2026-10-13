import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The single string transformation modeled here is spelled
   out DEEPLY as a per-code-point fold (`stripped`, pure region) rather than
   hidden behind an axiom about a callee; its agreement with the standard
   library string-substitution it transliterates is validated executably by
   axiom_check.py (G-AX, an A-reference). There is no module-level `axiom` and
   no `:|` stub. Provenance: mapping.md. -/
-- axioms-end

-- pure-start
/- The per-code-point decision: the binary-stream marker code point `b` is
   dropped (contributes nothing), every other code point passes through
   unchanged. This is the single-character image of the substitution that
   removes the binary marker from a stream-mode descriptor. -/
def stripStep (c : Char) : List Char :=
  if c = 'b' then [] else [c]

/- The image of a whole descriptor: concatenate the per-code-point images, i.e.
   the descriptor with every `b` code point removed. Front-recursive so a single
   unfold is available per loop step (the Velvet fold pattern, plan §5.4). -/
def stripped : List Char → List Char
  | []      => []
  | c :: cs => stripStep c ++ stripped cs

@[grind] lemma stripped_nil : stripped [] = [] := rfl
@[grind] lemma stripped_cons (c : Char) (cs : List Char) :
    stripped (c :: cs) = stripStep c ++ stripped cs := rfl

/- The marker code point never survives the transformation; the result advertises
   a binary-free descriptor. Marked `@[grind]` so `loom_solve` can use it. -/
@[grind] lemma stripStep_b : stripStep 'b' = [] := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A text wrapper around a byte stream presents a mode descriptor for that
   stream. Because the wrapper exposes a text interface, the descriptor it
   presents must not advertise the binary marker even when the wrapped byte
   stream's own descriptor does. Desired behaviour: take the wrapped stream's
   mode descriptor and return it with every binary-marker code point (`b`)
   removed and all other code points preserved in order. -/
method textStreamMode (rawMode : List Char) return (out : List Char)
  ensures out = stripped rawMode
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := rawMode.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ rawMode.length
      invariant result = stripped (rawMode.drop i)
      done_with i = 0
      decreasing i
    do
      let c := rawMode[i - 1]!
      result := stripStep c ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `stripped` peels one `stripStep`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma stripped_drop_step (text : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ text.length) :
    stripped (text.drop (i - 1)) = stripStep text[i - 1]! ++ stripped (text.drop i) := by
  have hlt : i - 1 < text.length := by omega
  have hcons : text.drop (i - 1) = text[i - 1]! :: text.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, stripped_cons]

prove_correct textStreamMode by
  loom_solve
  rw [stripped_drop_step rawMode i (by omega) (by omega)]
  simp_all
