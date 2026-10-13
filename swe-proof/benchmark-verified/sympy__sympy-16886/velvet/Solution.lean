import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The per-symbol telegraphic-code table is modeled
--  DEEPLY by `codeOf` in the `pure` region — an A-reference validated
--  `codeOf == the real per-symbol code table` by axiom_check.py (G-AX),
--  NOT a consumed axiom. See mapping.md §3.)
-- axioms-end

-- pure-start
/- The dot/dash code for one source symbol: the canonical telegraphic
   representation of each letter, digit and supported punctuation mark, as a
   sequence of '.' (dot) and '-' (dash) code points. Every other code point has
   no telegraphic representation and maps to the empty sequence (such symbols
   are filtered out before this map is consulted, so the empty image is never
   observed for a represented symbol). Front-recursive companion `codesOf`
   below expands a whole symbol sequence; the deep model is validated against
   the real repository table by axiom_check.py (G-AX). Provenance: mapping.md. -/
def codeOf (c : Char) : List Char :=
  match c with
  | 'A' => ".-".toList     | 'B' => "-...".toList
  | 'C' => "-.-.".toList   | 'D' => "-..".toList
  | 'E' => ".".toList      | 'F' => "..-.".toList
  | 'G' => "--.".toList    | 'H' => "....".toList
  | 'I' => "..".toList     | 'J' => ".---".toList
  | 'K' => "-.-".toList    | 'L' => ".-..".toList
  | 'M' => "--".toList     | 'N' => "-.".toList
  | 'O' => "---".toList    | 'P' => ".--.".toList
  | 'Q' => "--.-".toList   | 'R' => ".-.".toList
  | 'S' => "...".toList    | 'T' => "-".toList
  | 'U' => "..-".toList    | 'V' => "...-".toList
  | 'W' => ".--".toList    | 'X' => "-..-".toList
  | 'Y' => "-.--".toList   | 'Z' => "--..".toList
  | '0' => "-----".toList  | '1' => ".----".toList
  | '2' => "..---".toList  | '3' => "...--".toList
  | '4' => "....-".toList  | '5' => ".....".toList
  | '6' => "-....".toList  | '7' => "--...".toList
  | '8' => "---..".toList  | '9' => "----.".toList
  | '.' => ".-.-.-".toList | ',' => "--..--".toList
  | ':' => "---...".toList | ';' => "-.-.-.".toList
  | '?' => "..--..".toList | '-' => "-....-".toList
  | '_' => "..--.-".toList | '(' => "-.--.".toList
  | ')' => "-.--.-".toList | '\'' => ".----.".toList
  | '=' => "-...-".toList  | '+' => ".-.-.".toList
  | '/' => "-..-.".toList  | '@' => ".--.-.".toList
  | '$' => "...-..-".toList | '!' => "-.-.--".toList
  | _   => []

/- The encoding of a whole symbol sequence: the per-symbol code sequences in
   source order. Front-recursive so a single unfold is available per loop step
   (the Velvet fold pattern). -/
def codesOf : List Char → List (List Char)
  | []      => []
  | c :: cs => codeOf c :: codesOf cs

@[grind] lemma codesOf_nil : codesOf [] = [] := rfl
@[grind] lemma codesOf_cons (c : Char) (cs : List Char) :
    codesOf (c :: cs) = codeOf c :: codesOf cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method encodeWord (word : List Char) return (out : List (List Char))
  ensures out = codesOf word
  do
    -- impl-start
    let mut result : List (List Char) := []
    let mut i := word.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ word.length
      invariant result = codesOf (word.drop i)
      done_with i = 0
      decreasing i
    do
      let c := word[i - 1]!
      result := codeOf c :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `codesOf` peels one `codeOf`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma codesOf_drop_step (word : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ word.length) :
    codesOf (word.drop (i - 1)) = codeOf word[i - 1]! :: codesOf (word.drop i) := by
  have hlt : i - 1 < word.length := by omega
  have hcons : word.drop (i - 1) = word[i - 1]! :: word.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, codesOf_cons]

prove_correct encodeWord by
  loom_solve
  rw [codesOf_drop_step word i (by omega) (by omega)]
  simp_all
