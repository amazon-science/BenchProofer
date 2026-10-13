import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The single behaviour under specification — how a string
   value is rendered to its JSON text form — is modelled DEEPLY here (the
   spelled-out `jsonChar`/`jsonEscapedSeq` fold below), validated against the
   real standard-library serializer by axiom_check.py (G-AX, A-reference). No
   unchanged callee needs a contract. -/
-- axioms-end

-- pure-start
/- One lowercase hexadecimal digit (`0`–`9`, `a`–`f`). Only ever applied to a
   value `< 16` (the nibbles of a control code point), where it is total. -/
def hexDigit (n : UInt32) : Char :=
  if n < 10 then Char.ofNat (48 + n.toNat) else Char.ofNat (87 + n.toNat)

/- The JSON text of a single code point inside a string literal, when the
   serializer is asked to keep output as the raw text rather than collapsing
   everything outside ASCII to `\uXXXX` escapes:

     *  U+0022 and U+005C take their two-character backslash form;
     *  the five whitespace/control code points with short forms
        (U+0008,U+0009,U+000A,U+000C,U+000D) take those;
     *  every other code point below U+0020 takes the six-character
        `\u00XX` form;
     *  EVERY remaining code point — crucially including all code points at or
        above U+0080 — passes through as itself, one character.

   The last clause is the whole behaviour at issue: characters outside the
   ASCII range appear as themselves, not as `\uXXXX` sequences. -/
def jsonChar (c : Char) : List Char :=
  if c.val = 34 then ['\\', '"']
  else if c.val = 92 then ['\\', '\\']
  else if c.val = 8 then ['\\', 'b']
  else if c.val = 9 then ['\\', 't']
  else if c.val = 10 then ['\\', 'n']
  else if c.val = 12 then ['\\', 'f']
  else if c.val = 13 then ['\\', 'r']
  else if c.val < 32 then ['\\', 'u', '0', '0', hexDigit (c.val / 16), hexDigit (c.val % 16)]
  else [c]

/- The escaped body of a whole string: concatenate the per-code-point JSON
   renderings. Front-recursive so a single unfold is available per loop step
   (the fold pattern, plan §5.4). -/
def jsonEscapedSeq : List Char → List Char
  | []      => []
  | c :: cs => jsonChar c ++ jsonEscapedSeq cs

@[grind] lemma jsonEscapedSeq_nil : jsonEscapedSeq [] = [] := rfl
@[grind] lemma jsonEscapedSeq_cons (c : Char) (cs : List Char) :
    jsonEscapedSeq (c :: cs) = jsonChar c ++ jsonEscapedSeq cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a string value to its JSON text: a double quote, the per-code-point
   escaped body, and a closing double quote. The post-condition pins the body to
   `jsonEscapedSeq`, so any verifying implementation emits non-ASCII code points
   literally (the `else [c]` clause), exactly as the desired behaviour demands. -/
method serializeStringValue (text : List Char) return (out : List Char)
  ensures out = '"' :: (jsonEscapedSeq text ++ ['"'])
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := text.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ text.length
      invariant result = jsonEscapedSeq (text.drop i)
      done_with i = 0
      decreasing i
    do
      let c := text[i - 1]!
      result := jsonChar c ++ result
      i := i - 1
    return '"' :: (result ++ ['"'])
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `jsonEscapedSeq` peels one `jsonChar`. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma jsonEscapedSeq_drop_step (text : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ text.length) :
    jsonEscapedSeq (text.drop (i - 1)) = jsonChar text[i - 1]! ++ jsonEscapedSeq (text.drop i) := by
  have hlt : i - 1 < text.length := by omega
  have hcons : text.drop (i - 1) = text[i - 1]! :: text.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, jsonEscapedSeq_cons]

prove_correct serializeStringValue by
  loom_solve
  rw [jsonEscapedSeq_drop_step text i (by omega) (by omega)]
  simp_all
