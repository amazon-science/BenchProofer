import Mathlib
-- imports-end

/-!
Escaping arbitrary text so that it may be safely embedded in HTML.

The transformation walks the input one code point at a time and rewrites the
five characters that carry syntactic meaning in HTML into their corresponding
character-reference entities, leaving every other code point untouched:

* `&` becomes `&amp;`
* `<` becomes `&lt;`
* `>` becomes `&gt;`
* `"` becomes `&quot;`
* `'` becomes `&#x27;`

Every other character maps to itself. The result is the concatenation, in
order, of the per-code-point encodings; the encoding is applied
unconditionally, so already-encoded input is encoded again (its leading `&`
is re-escaped). Only the relative order and the above substitutions determine
the output — no other characters are altered, inserted, or removed.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- per-code-point HTML encoding is modeled DEEPLY over the observable input
-- (the list of characters of the text) as `escapeSeq`, so no `opaque`/`axiom`
-- callee contract is needed; its faithfulness to the standard encoder is
-- validated by the mechanical differential check.
-- axioms-end

-- pure-start
/-- The HTML character-reference encoding of a single code point: the five
HTML-significant characters map to their entity form; every other character
maps to itself. -/
def escapeChar (c : Char) : List Char :=
  if c = '&' then "&amp;".toList
  else if c = '<' then "&lt;".toList
  else if c = '>' then "&gt;".toList
  else if c = '"' then "&quot;".toList
  else if c = '\'' then "&#x27;".toList
  else [c]

/-- The HTML encoding of a whole text: the in-order concatenation of the
per-code-point encodings. Front-recursive so it pairs with an accumulating
loop. -/
def escapeSeq : List Char → List Char
  | [] => []
  | c :: cs => escapeChar c ++ escapeSeq cs
-- pure-end

-- post-conditions-start
/-- The escaped text is exactly the in-order concatenation of the per-code-point
HTML encodings of the input characters. This pins the full output to the input:
its length, character order, and every substitution are determined, so no other
result can satisfy it. -/
def problem_spec_escape (s : List Char) (result : List Char) : Prop :=
  result = escapeSeq s
-- post-conditions-end

-- impl-start
def implementation_escape (s : List Char) : List Char := Id.run do
  -- Pre-patch behavior: the apostrophe is encoded as the DECIMAL character
  -- reference `&#39;` rather than the hexadecimal `&#x27;`; the four other
  -- HTML-significant characters are encoded as here.
  let escapeAlt : Char → List Char := fun c =>
    if c = '&' then "&amp;".toList
    else if c = '<' then "&lt;".toList
    else if c = '>' then "&gt;".toList
    else if c = '"' then "&quot;".toList
    else if c = '\'' then "&#39;".toList
    else [c]
  let mut acc : List Char := []
  for c in s do
    acc := acc ++ escapeAlt c
  return acc
-- impl-end

-- proof-start
theorem correct_escape :
    ∀ (s : List Char),
      problem_spec_escape s (implementation_escape s) := by
  -- Carries the gold-faithful proof body. It is UNCLOSABLE against this impl
  -- (G-DIFF): on input `'` this impl yields `&#39;` while the spec demands
  -- `escapeSeq ['\''] = &#x27;`, so the reduced goal is a false character-list
  -- equality that no tactic can discharge.
  intro s
  unfold problem_spec_escape implementation_escape
  simp only [Id.run, bind]
  induction s with
  | nil => rfl
  | cons a as ih => simp [escapeSeq, escapeChar, List.append_assoc]
-- proof-end
