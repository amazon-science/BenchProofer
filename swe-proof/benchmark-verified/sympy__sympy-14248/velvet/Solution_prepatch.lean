import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A rendered term is a sequence of characters. A term whose first character is
   the minus glyph carries a leading negative marker; its remaining characters
   are its body. -/
def termSign (t : List Char) : Char :=
  if t.head? = some '-' then '-' else '+'

def termBody (t : List Char) : List Char :=
  if t.head? = some '-' then t.drop 1 else t

/- The contribution of a NON-leading term to the rendering: a separating space,
   the term's own sign glyph, a space, then the term's body. So a term carrying
   a leading negative marker contributes " - body" and any other term
   contributes " + body". -/
def tailPiece (t : List Char) : List Char :=
  ' ' :: termSign t :: ' ' :: termBody t

/- Rendering of the non-leading terms: concatenate each term's contribution.
   Front-recursive so a single unfold is available per loop step (the Velvet
   fold pattern, plan §5.4). -/
def joinTail : List (List Char) → List Char
  | []      => []
  | t :: ts => tailPiece t ++ joinTail ts

/- Rendering of a whole non-empty sequence of terms: the leading term verbatim
   (it keeps any leading negative marker and gains no separator), followed by
   each subsequent term's contribution. -/
def joinSignedTerms : List (List Char) → List Char
  | []      => []
  | t :: ts => t ++ joinTail ts

@[grind] lemma joinTail_nil : joinTail [] = [] := rfl
@[grind] lemma joinTail_cons (t : List Char) (ts : List (List Char)) :
    joinTail (t :: ts) = tailPiece t ++ joinTail ts := rfl

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `joinTail` peels one `tailPiece`. This is the single
   goal `loom_solve` leaves for the loop body. -/
@[grind] lemma joinTail_drop_step (terms : List (List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ terms.length) :
    joinTail (terms.drop (i - 1)) = tailPiece terms[i - 1]! ++ joinTail (terms.drop i) := by
  have hlt : i - 1 < terms.length := by omega
  have hcons : terms.drop (i - 1) = terms[i - 1]! :: terms.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, joinTail_cons]

/- The leading-term split: a non-empty sequence renders as its head verbatim
   followed by the contributions of its tail. -/
@[grind] lemma joinSignedTerms_head (terms : List (List Char)) (h : terms ≠ []) :
    joinSignedTerms terms = terms[0]! ++ joinTail (terms.drop 1) := by
  match terms with
  | []      => exact absurd rfl h
  | t :: ts => rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method joinSignedMatrixTerms (terms : List (List Char)) return (out : List Char)
  require terms ≠ []
  ensures out = joinSignedTerms terms
  do
    -- impl-start
    -- Pre-image skeleton: every non-leading term is glued with a fixed " + "
    -- separator and emitted verbatim, with no inspection of its own sign. A
    -- term already carrying a leading minus marker is therefore preceded by
    -- " + " instead of being folded into " - body". The frozen spec requires
    -- joinSignedTerms (which folds the sign), so prove_correct MUST fail.
    let mut result : List Char := []
    let mut i := terms.length
    while i > 1
      invariant 1 ≤ i ∧ i ≤ terms.length
      invariant result = joinTail (terms.drop i)
      done_with i = 1
      decreasing i
    do
      let t := terms[i - 1]!
      result := (' ' :: '+' :: ' ' :: t) ++ result
      i := i - 1
    return terms[0]! ++ result
    -- impl-end

prove_correct joinSignedMatrixTerms by
  loom_solve
