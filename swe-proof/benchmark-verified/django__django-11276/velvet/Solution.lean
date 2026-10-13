import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- A standard-library HTML entity decoder: the left inverse of the escaper on
   the five entity tokens this module relies on. Provenance + executable
   soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom entityDecode : List Char → List Char
axiom entityDecode_amp  : entityDecode "&amp;".toList  = ['&']
axiom entityDecode_lt   : entityDecode "&lt;".toList   = ['<']
axiom entityDecode_gt   : entityDecode "&gt;".toList   = ['>']
axiom entityDecode_quot : entityDecode "&quot;".toList = ['"']
axiom entityDecode_apos : entityDecode "&#x27;".toList = ['\'']
-- axioms-end

-- pure-start
/- The escape of a single code point: the five significant chars expand, every
   other char passes through. Ampersand handled by the caller's `escape` being
   the per-char substitution (ampersand-first ⇒ emitted '&' never re-escaped),
   so a single entity map is faithful (mapping.md §3.1). -/
def entity (c : Char) : List Char :=
  if c = '&' then "&amp;".toList
  else if c = '<' then "&lt;".toList
  else if c = '>' then "&gt;".toList
  else if c = '"' then "&quot;".toList
  else if c = '\'' then "&#x27;".toList
  else [c]

/- The escape of a whole sequence: concatenate the per-code-point entity
   sequences. Front-recursive so a single unfold is available per loop step
   (the Velvet fold pattern, plan §5.4). -/
def escapedSeq : List Char → List Char
  | []      => []
  | c :: cs => entity c ++ escapedSeq cs

@[grind] lemma escapedSeq_nil : escapedSeq [] = [] := rfl
@[grind] lemma escapedSeq_cons (c : Char) (cs : List Char) :
    escapedSeq (c :: cs) = entity c ++ escapedSeq cs := rfl

/- Escape/decode round-trips on the five significant code points. `entity c`
   for a concrete significant char reduces definitionally to the entity token
   (the `if c = …` guards decide), so each round-trip is the matching
   `entityDecode_*` axiom after a `show`. Marked `@[grind]` so `loom_solve`
   discharges the postconditions automatically. -/
@[grind] lemma roundtrip_amp  : entityDecode (entity '&')  = ['&']  := by
  show entityDecode "&amp;".toList = _;  exact entityDecode_amp
@[grind] lemma roundtrip_lt   : entityDecode (entity '<')  = ['<']  := by
  show entityDecode "&lt;".toList = _;   exact entityDecode_lt
@[grind] lemma roundtrip_gt   : entityDecode (entity '>')  = ['>']  := by
  show entityDecode "&gt;".toList = _;   exact entityDecode_gt
@[grind] lemma roundtrip_quot : entityDecode (entity '"')  = ['"']  := by
  show entityDecode "&quot;".toList = _; exact entityDecode_quot
@[grind] lemma roundtrip_apos : entityDecode (entity '\'') = ['\''] := by
  show entityDecode "&#x27;".toList = _; exact entityDecode_apos
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method escapeCodepoints (text : List Char) return (out : List Char)
  ensures out = escapedSeq text
  ensures entityDecode (entity '&')  = ['&']
  ensures entityDecode (entity '<')  = ['<']
  ensures entityDecode (entity '>')  = ['>']
  ensures entityDecode (entity '"')  = ['"']
  ensures entityDecode (entity '\'') = ['\'']
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := text.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ text.length
      invariant result = escapedSeq (text.drop i)
      done_with i = 0
      decreasing i
    do
      let c := text[i - 1]!
      result := entity c ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `escapedSeq` peels one `entity`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma escapedSeq_drop_step (text : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ text.length) :
    escapedSeq (text.drop (i - 1)) = entity text[i - 1]! ++ escapedSeq (text.drop i) := by
  have hlt : i - 1 < text.length := by omega
  have hcons : text.drop (i - 1) = text[i - 1]! :: text.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, escapedSeq_cons]

prove_correct escapeCodepoints by
  loom_solve
  rw [escapedSeq_drop_step text i (by omega) (by omega)]
  simp_all
