import Velvet.Std
-- imports-end

/- Total correctness: the real label renderer is a single bounded pass over the
   pre-processed text and always terminates, so a diverging implementation must
   NOT satisfy this spec. Partial correctness would let a non-terminating loop
   discharge the postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The label pre-processor: a regular-expression substitution that wraps each
   maximal run of ASCII letters in the surrounding math/upright delimiters. It
   is an UNCHANGED community callee; the routine under spec only consumes its
   result, so the weakest sufficient contract is "some deterministic function
   of the text" (an uninterpreted map on code points). Provenance + executable
   soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom reSub : List Char → List Char

/- Collapse of an empty math group: deletes every occurrence of the empty
   delimiter pair from the assembled string. Also an UNCHANGED community callee
   applied verbatim as the final step; modeled as an uninterpreted map for the
   same reason. Provenance + soundness: mapping.md / axiom_check.py (G-AX). -/
axiom removeEmpty : List Char → List Char
-- axioms-end

-- pure-start
/- The math-protection of a single code point. Three code points are wrapped in
   curly braces / replaced by a thin-space control sequence so that the math
   renderer does not treat them as binary operators or collapse inter-number
   spacing; every other code point passes through unchanged. (Behaviour, not the
   edit: mapping.md §3.1.) -/
def mathProtect (c : Char) : List Char :=
  if c = '-' then "{-}".toList
  else if c = ':' then "{:}".toList
  else if c = ' ' then "\\;".toList
  else [c]

/- The math-protection of a whole sequence: concatenate the per-code-point
   protections. Front-recursive so a single unfold is available per loop step
   (the fold pattern, plan §5.4). The chained single-pass substitution it models
   is faithful because no protection output contains a code point a later
   substitution would touch (mapping.md §3.1). -/
def protectSeq : List Char → List Char
  | []      => []
  | c :: cs => mathProtect c ++ protectSeq cs

@[grind] lemma protectSeq_nil : protectSeq [] = [] := rfl
@[grind] lemma protectSeq_cons (c : Char) (cs : List Char) :
    protectSeq (c :: cs) = mathProtect c ++ protectSeq cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a tick/offset label for a math (TeX) text renderer.

   The label text is first passed through the letter-run pre-processor
   (`reSub`); each code point of the result is then math-protected
   (`protectSeq` — three code points are wrapped/replaced, all others pass
   through); the protected string is enclosed in the math delimiters
   `$\mathdefault{ … }$`; finally any empty math group is dropped
   (`removeEmpty`). `text` is the read-only input label (not `mut`): the routine
   consumes it and never alters it (directive 5). The label is modeled as a
   `List Char` (a per-code-point string); the delimiters are concrete literals
   (mapping.md §2). -/
noncomputable section
method renderTexLabel (text : List Char) return (out : List Char)
  ensures out = removeEmpty ("$\\mathdefault{".toList ++ protectSeq (reSub text) ++ "}$".toList)
  do
    -- impl-start
    -- Pre-image skeleton: only the dash is math-protected (its sole '{-}'
    -- substitution); the colon and the space pass through unchanged. The frozen
    -- spec requires the full per-code-point protection `protectSeq` (which also
    -- maps ':' and ' '), so prove_correct MUST fail on those code points.
    let s := reSub text
    let mut result : List Char := []
    let mut i := s.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ s.length
      invariant result = protectSeq (s.drop i)
      done_with i = 0
      decreasing i
    do
      let c := s[i - 1]!
      let e : List Char := if c = '-' then "{-}".toList else [c]
      result := e ++ result
      i := i - 1
    let out := removeEmpty ("$\\mathdefault{".toList ++ result ++ "}$".toList)
    return out
    -- impl-end
end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `protectSeq` peels one `mathProtect`. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma protectSeq_drop_step (s : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ s.length) :
    protectSeq (s.drop (i - 1)) = mathProtect s[i - 1]! ++ protectSeq (s.drop i) := by
  have hlt : i - 1 < s.length := by omega
  have hcons : s.drop (i - 1) = s[i - 1]! :: s.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, protectSeq_cons]

prove_correct renderTexLabel by
  loom_solve
  rw [protectSeq_drop_step (reSub text) i (by omega) (by omega)]
  simp_all
