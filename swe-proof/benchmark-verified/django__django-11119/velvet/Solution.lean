import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The markup-escape of a value is modeled DEEPLY below
--  — `escapedSeq`/`entity` ARE the per-code-point substitution — and validated
--  == the real escaping callee by axiom_check.py (G-AX), an A-reference, not a
--  consumed contract. The policy-selection the change introduces is modeled
--  concretely by the `if` in `valueToDisplay`.)
-- axioms-end

-- pure-start
/- The escape of a single code point: the five significant markup characters
   expand to their entity sequences, every other code point passes through
   unchanged. The substitution is per-code-point and single-pass — each input
   character is mapped once and the emitted entity characters are never
   re-scanned (mapping.md §3.1). -/
def entity (c : Char) : List Char :=
  if c = '&' then "&amp;".toList
  else if c = '<' then "&lt;".toList
  else if c = '>' then "&gt;".toList
  else if c = '"' then "&quot;".toList
  else if c = '\'' then "&#39;".toList
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
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Markup-escape a value: produce the per-code-point entity expansion of the
   input. The five significant characters become their entities; everything else
   passes through. Read-only input (`value` is not `mut`; the escape produces a
   fresh sequence — directive 5). -/
method escapeCodepoints (value : List Char) return (out : List Char)
  ensures out = escapedSeq value
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := value.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ value.length
      invariant result = escapedSeq (value.drop i)
      done_with i = 0
      decreasing i
    do
      let c := value[i - 1]!
      result := entity c ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `escapedSeq` peels one `entity`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma escapedSeq_drop_step (value : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ value.length) :
    escapedSeq (value.drop (i - 1)) = entity value[i - 1]! ++ escapedSeq (value.drop i) := by
  have hlt : i - 1 < value.length := by omega
  have hcons : value.drop (i - 1) = value[i - 1]! :: value.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, escapedSeq_cons]

prove_correct escapeCodepoints by
  loom_solve
  rw [escapedSeq_drop_step value i (by omega) (by omega)]
  simp_all

/- Render an input value to its display text under the configured markup-escaping
   policy. The policy flag `encodeMarkup` is the configured escaping setting,
   which MUST govern this rendering: when the policy is on, the value is
   markup-escaped (its per-code-point entity expansion); when the policy is off,
   the value is displayed verbatim. The policy flag must be honored — a value is
   escaped if and only if the policy says so. Both inputs are read-only (neither
   is `mut`; rendering mutates nothing — directive 5); the result is a fresh
   sequence. -/
method valueToDisplay (encodeMarkup : Bool) (value : List Char) return (out : List Char)
  ensures out = (if encodeMarkup then escapedSeq value else value)
  do
    -- impl-start
    -- The display text honors the configured escaping policy: escape when the
    -- policy is on, otherwise pass the value through unchanged.
    let out ← if encodeMarkup then
        escapeCodepoints value
      else
        pure value
    return out
    -- impl-end

prove_correct valueToDisplay by
  loom_solve
