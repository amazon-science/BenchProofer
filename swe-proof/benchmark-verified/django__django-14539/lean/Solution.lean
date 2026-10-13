import Mathlib
-- imports-end

/-!
Peeling a run of trailing punctuation off the end of a text token.

When a piece of text is examined for a possible link, any run of trailing
punctuation characters (`.`, `,`, `:`, `;`, `!`) at the end of the token is
peeled off and prepended to a separate accumulator that collects such trailing
punctuation, so that the punctuation is not treated as part of the link.

The token may contain HTML-escaped sequences ("html escaped string" in the
report). The *length* of the trailing-punctuation run is therefore measured on
the entity-DECODED view of the token (entity sequences such as `&lt` are decoded
first, so a `;` that is part of an entity is not mistaken for punctuation). The
characters actually peeled off, however, are taken from the END of the ORIGINAL
token, and the same count is removed from it. As a result the characters removed
from the token are exactly the characters added to the accumulator: the
concatenation `token ++ accumulator` is preserved by the operation. A boolean
records whether anything was peeled.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
/-- A standard HTML entity decoder: maps a character sequence to its decoded
form (entity sequences are replaced by the character(s) they denote; all other
characters are left unchanged). Decoding never lengthens the sequence. The
operation under specification does not change this decoder; it is used only to
measure where the trailing-punctuation run begins. Declared opaque so it can
appear in the executable implementation; no further property of it is consumed
(its concrete behavior is exercised by the differential conformance check). -/
opaque decode : List Char → List Char
-- axioms-end

-- pure-start
/-- The trailing-punctuation alphabet: period, comma, colon, semicolon, bang. -/
def TRAILING_PUNCT : List Char := ['.', ',', ':', ';', '!']

/-- Drop the maximal suffix consisting of trailing-punctuation characters
(the analogue of Python's `s.rstrip('.,:;!')`). -/
def rstripPunct (cs : List Char) : List Char :=
  (cs.reverse.dropWhile (fun c => TRAILING_PUNCT.contains c)).reverse

/-- The first `length - n` characters — i.e. all but the last `n`
(the analogue of Python's `s[:-n]` for `1 ≤ n ≤ length`). -/
def dropRightN (cs : List Char) (n : Nat) : List Char := cs.take (cs.length - n)

/-- The last `n` characters (the analogue of Python's `s[-n:]` for
`1 ≤ n ≤ length`). -/
def takeRightN (cs : List Char) (n : Nat) : List Char := cs.drop (cs.length - n)
-- pure-end

-- post-conditions-start
/-- Let `decoded` be the entity-decoded view of `token`, `stripped` the result
of dropping its trailing punctuation, and `punctCount` the number of characters
dropped. The operation:

* leaves the token equal to its original minus its last `punctCount` characters;
* sets the accumulator to those last `punctCount` characters of the original
  token, prepended to the incoming accumulator;
* reports `true` iff the decoded view actually had trailing punctuation;
* conserves characters — `token ++ accumulator` is unchanged (the punctuation is
  MOVED from the token's tail to the accumulator's head, never duplicated). -/
def problem_spec_peelTrailingPunct (token tailPunct : List Char)
    (result : List Char × List Char × Bool) : Prop :=
  let decoded := decode token
  let stripped := rstripPunct decoded
  let punctCount := decoded.length - stripped.length
  result.1 = dropRightN token punctCount ∧
  result.2.1 = takeRightN token punctCount ++ tailPunct ∧
  result.2.2 = decide (decoded ≠ stripped) ∧
  result.1 ++ result.2.1 = token ++ tailPunct
-- post-conditions-end

-- impl-start
def implementation_peelTrailingPunct (token tailPunct : List Char) :
    List Char × List Char × Bool := Id.run do
  let mut token := token
  let mut tailPunct := tailPunct
  let mut trimmed := false
  let decoded := decode token
  let stripped := rstripPunct decoded
  if decoded ≠ stripped then
    let punctCount := decoded.length - stripped.length
    tailPunct := takeRightN token punctCount ++ tailPunct
    token := dropRightN token punctCount
    trimmed := true
  return (token, tailPunct, trimmed)
-- impl-end

-- proof-start
theorem correct_peelTrailingPunct :
    ∀ (token tailPunct : List Char),
      problem_spec_peelTrailingPunct token tailPunct
        (implementation_peelTrailingPunct token tailPunct) := by
  intro token tailPunct
  unfold problem_spec_peelTrailingPunct implementation_peelTrailingPunct
  simp only [Id.run, bind, pure]
  by_cases h : decode token ≠ rstripPunct (decode token)
  · rw [if_pos h]
    refine ⟨rfl, rfl, (decide_eq_true h).symm, ?_⟩
    simp only [dropRightN, takeRightN]
    rw [← List.append_assoc, List.take_append_drop]
  · rw [if_neg h]
    push_neg at h
    have hc : (decode token).length - (rstripPunct (decode token)).length = 0 := by
      have := congrArg List.length h; omega
    refine ⟨?_, ?_, (decide_eq_false (not_not_intro h)).symm, rfl⟩
    · simp only [dropRightN, hc, Nat.sub_zero, List.take_length]
    · simp only [takeRightN, hc, Nat.sub_zero, List.drop_length, List.nil_append]
-- proof-end
