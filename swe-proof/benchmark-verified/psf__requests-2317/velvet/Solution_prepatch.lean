import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- The native text representation of a single token character: a token may
   arrive either as native text or as a byte string carrying the ASCII bytes
   of the token, and the representation keeps the character itself. Each
   carried character contributes exactly itself, with no surrounding marker or
   quoting wrapper. -/
def nativeChar (c : Char) : List Char := [c]

/- The native text representation of a whole token: the concatenation of the
   per-character representations. Front-recursive so a single unfold is
   available per loop step (the Velvet fold pattern). For an ASCII token this
   is the identity on the carried character sequence. -/
def nativeSeq : List Char → List Char
  | []      => []
  | c :: cs => nativeChar c ++ nativeSeq cs

@[grind] lemma nativeSeq_nil : nativeSeq [] = [] := rfl
@[grind] lemma nativeSeq_cons (c : Char) (cs : List Char) :
    nativeSeq (c :: cs) = nativeChar c ++ nativeSeq cs := rfl

/- The native representation preserves the carried character sequence exactly:
   it is the token's own characters, of the same length, regardless of whether
   the token arrived as native text or as a byte string. -/
@[grind] lemma nativeSeq_id : ∀ (cs : List Char), nativeSeq cs = cs
  | []      => rfl
  | c :: cs => by simp [nativeSeq_cons, nativeChar, nativeSeq_id cs]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method nativeToken (token : List Char) return (out : List Char)
  ensures out = nativeSeq token
  ensures out = token
  ensures out.length = token.length
  do
    -- impl-start
    -- Pre-image skeleton: a byte-carried token is rendered as the TEXTUAL
    -- object description -- the carried characters are wrapped with a leading
    -- marker character and a surrounding pair of quote characters, producing a
    -- sequence three characters longer than the token. The frozen spec
    -- requires the token's own characters (`out = token`), so prove_correct
    -- MUST fail.
    let mut result : List Char := []
    let mut i := token.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ token.length
      invariant result = nativeSeq (token.drop i)
      done_with i = 0
      decreasing i
    do
      let c := token[i - 1]!
      result := nativeChar c ++ result
      i := i - 1
    return 'b' :: '\'' :: (result ++ ['\''])
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `nativeSeq` peels one `nativeChar`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma nativeSeq_drop_step (token : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ token.length) :
    nativeSeq (token.drop (i - 1)) = nativeChar token[i - 1]! ++ nativeSeq (token.drop i) := by
  have hlt : i - 1 < token.length := by omega
  have hcons : token.drop (i - 1) = token[i - 1]! :: token.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, nativeSeq_cons]

prove_correct nativeToken by
  loom_solve
  rw [nativeSeq_drop_step token i (by omega) (by omega)]
  simp_all
