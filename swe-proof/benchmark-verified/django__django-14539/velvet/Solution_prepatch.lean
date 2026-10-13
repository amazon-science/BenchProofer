import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- A standard-library HTML entity decoder: maps an escaped character sequence
   back to the text it represents (named or numeric entity tokens collapse to
   their single code points, e.g. an angle-bracket entity to one character).
   Left opaque on purpose: the only behaviour relied on is that the decoded form
   is a deterministic function of the input whose length is used to determine
   how many trailing punctuation characters the token genuinely ends with. Its
   identification with the real decoder, and the counts derived from it, are
   validated executably (mapping.md / axiom_check.py for G-AX,
   conformance_check.py for G-CONF). -/
opaque entityDecode : List Char → List Char
-- axioms-end

-- pure-start
/- The trailing-punctuation alphabet: the characters treated as removable
   sentence punctuation when they occur at the end of a token. -/
def isTrailingPunct (c : Char) : Bool :=
  c = '.' || c = ',' || c = ':' || c = ';' || c = '!'

/- Remove every trailing punctuation character from the end of a sequence
   (a faithful model of right-stripping that alphabet). Expressed via `reverse`
   so the "from the end" direction is explicit. -/
def stripTrailingPunct (s : List Char) : List Char :=
  (s.reverse.dropWhile isTrailingPunct).reverse

/- How many punctuation characters the token ends with, measured on its DECODED
   form so that an encoded entity (which may itself end in a punctuation
   character) is never mistaken for sentence punctuation. This count is the
   number of characters that must be peeled off the END of the (still-encoded)
   token. -/
def trailingPunctCount (token : List Char) : Nat :=
  (entityDecode token).length - (stripTrailingPunct (entityDecode token)).length
-- pure-end

/- The result of peeling: `core` is what remains of the token, `tail` is the
   accumulated suffix that was moved off the end. -/
structure Split where
  core : List Char
  tail : List Char

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method peelTrailingPunctuation (token : List Char) (tail : List Char)
    return (res : Split)
  ensures res.core = token.take (token.length - trailingPunctCount token)
  ensures res.tail = token.drop (token.length - trailingPunctCount token) ++ tail
  do
    -- impl-start
    -- Pre-fix skeleton: the suffix moved into `tail` is sliced at the DECODED
    -- length index (`stripped.length`) rather than measured from the end of the
    -- encoded token. For tokens whose encoded and decoded lengths coincide this
    -- agrees with the spec; otherwise the wrong number of characters is peeled,
    -- so `prove_correct` MUST fail on the `tail` postcondition.
    let decoded := entityDecode token
    let stripped := stripTrailingPunct decoded
    let punctuationCount := decoded.length - stripped.length
    let mut core := token
    let mut newTail := tail
    if decoded ≠ stripped then
      core := token.take (token.length - punctuationCount)
      newTail := token.drop stripped.length ++ tail
    return { core := core, tail := newTail }
    -- impl-end

prove_correct peelTrailingPunctuation by
  loom_solve
  · -- if-true, tail clause: DISCRIMINATOR — the buggy decoded-length index
    -- `drop stripped.length` does NOT equal `drop (token.length - count)`
    -- whenever the token contains entities (decoded.length < token.length).
    -- This goal is UNCLOSABLE: it is exactly the issue's `&lt</a>lt!` bug.
    simp only [trailingPunctCount]
  · -- if-true, core clause (unchanged by the bug)
    simp only [trailingPunctCount]
  · rw [not_not] at if_neg
    simp only [trailingPunctCount, ← if_neg, Nat.sub_self, Nat.sub_zero,
      List.drop_length, List.nil_append]
  · rw [not_not] at if_neg
    simp only [trailingPunctCount, ← if_neg, Nat.sub_self, Nat.sub_zero,
      List.take_length]
