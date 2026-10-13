import Mathlib
-- imports-end

/-!
Removing accent marks from a text string.

The desired behavior:

* If the string consists only of basic ASCII characters (every code point below
  128), it carries no accents and is returned completely unchanged.
* Otherwise the string is decomposed into its canonical form — each visible
  glyph split into a base character followed by any number of standalone
  combining marks — and every combining mark is then dropped, leaving only the
  base characters.

The point is that the decision to strip is driven by whether the text actually
contains any non-ASCII code point, NOT by whether the text happens to already be
in decomposed form. A glyph that is supplied already split into a base letter
plus a separate combining mark is still non-ASCII, so its combining mark must be
removed just like an accent attached to a pre-composed glyph.
-/

-- axioms-start
/-- Canonical decomposition of a string: each glyph is rewritten as a base
character followed by zero or more standalone combining marks. This is a
standard-library text-normalization routine the specification reads but does not
redefine; only its signature is declared here, and its behavior is exercised
against the real routine by the conformance gate. -/
opaque canonDecompose : List Char → List Char

/-- Whether a single code point is a standalone combining mark (a mark that
attaches to a preceding base character rather than standing on its own). An
unchanged standard-library predicate; signature only. -/
opaque isCombiningMark : Char → Bool
-- axioms-end

-- pure-start
/-- A code point is basic ASCII when its scalar value is below 128. -/
def isAscii (c : Char) : Bool := decide (c.toNat < 128)
-- pure-end

-- post-conditions-start
/-- The result is the input verbatim when every code point is basic ASCII;
otherwise it is the canonical decomposition of the input with every combining
mark removed. -/
def problem_spec_stripAccents (s : List Char) (result : List Char) : Prop :=
  if s.all isAscii then
    result = s
  else
    result = (canonDecompose s).filter (fun c => !isCombiningMark c)
-- post-conditions-end

-- impl-start
def implementation_stripAccents (s : List Char) : List Char := Id.run do
  if s.all isAscii then
    return s
  let normalized := canonDecompose s
  return normalized.filter (fun c => !isCombiningMark c)
-- impl-end

-- proof-start
theorem correct_stripAccents :
    ∀ (s : List Char),
      problem_spec_stripAccents s (implementation_stripAccents s) := by
  intro s
  unfold problem_spec_stripAccents implementation_stripAccents
  by_cases h : s.all isAscii <;> simp [h, Id.run, pure, bind]
-- proof-end
