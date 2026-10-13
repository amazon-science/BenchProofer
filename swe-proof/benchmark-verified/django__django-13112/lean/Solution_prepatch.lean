import Mathlib
-- imports-end

/-!
Normalizing a textual model reference token.

A reference token is a short string that names a model. It comes in two shapes:

  * a **bare** name (no separator), e.g. `Category`; or
  * a **qualified** name of the form `prefix.name`, where a single `.` separator
    splits an owning namespace prefix from the model's own name, e.g.
    `MyApp.Category`.

The normalized form is computed per shape:

  * a bare name is normalized by lowercasing the whole token (`Category` →
    `category`);
  * a qualified name keeps its prefix EXACTLY as written (its letter case is
    preserved verbatim) and lowercases only the trailing name segment
    (`MyApp.Category` → `MyApp.category`).

The separator position and the prefix characters are otherwise left untouched.
The modeled domain is tokens that (a) contain at most one separator (a token with
two or more separators is outside the modeled domain), and (b) consist solely of
ASCII code points. The ASCII restriction is essential: the per-character
lowercasing modeled here (`Char.toLower`) coincides with the real `str.lower`
callee only on the ASCII range. Outside ASCII the two disagree — e.g. Python
folds `Σ`→`σ`, `İ`→`i̇`, `ẞ`→`ß` while `Char.toLower` leaves them unchanged, and a
folded form may even change length — so such tokens are deliberately EXCLUDED from
the modeled domain rather than being (unfaithfully) certified. Both domain
constraints are carried by the token type itself (`RefToken` packages the
character list with proofs of both), so every value the specification quantifies
over lies inside the modeled domain and the correctness theorem needs no side
hypotheses: it pins the output on EVERY expressible input.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The whole transformation
-- is spelled out deeply: locating the (at most one) separator, the verbatim
-- prefix, and the per-character lowercasing of the trailing segment are all
-- modeled directly over the input character list. Per-character lowercasing is
-- the concrete pure helper `Char.toLower` (ASCII letter case folding); there is
-- no opaque repo callee whose property the proof must assume.
-- axioms-end

-- pure-start
/-- The segment of `s` that precedes its first separator `.` (all of `s` when
there is no separator). Its characters are returned verbatim. -/
def prefixSeg (s : List Char) : List Char := s.takeWhile (· ≠ '.')

/-- The segment of `s` that follows its first separator `.` (empty when there is
no separator). For a token with at most one separator this is the trailing name
segment. -/
def nameSeg (s : List Char) : List Char := (s.dropWhile (· ≠ '.')).drop 1

/-- A character is in the modeled (ASCII) alphabet iff its code point is below
128. On exactly this range the modeled per-character case fold `Char.toLower`
agrees with the real repository callee `str.lower`; the modeled domain is
restricted to tokens all of whose characters satisfy this. -/
def isAsciiChar (c : Char) : Prop := c.val < 128

/-- A token is in the modeled ASCII domain iff every one of its characters is
ASCII (see `isAsciiChar`). -/
def asciiToken (s : List Char) : Prop := ∀ c ∈ s, isAsciiChar c

/-- A reference token in the modeled domain: its character list together with
proofs of the two domain constraints — at most one separator, and all-ASCII
characters. Carrying the constraints in the type (rather than as theorem
hypotheses) means every `RefToken` value IS an in-domain token, so the
correctness theorem quantifies over exactly the modeled domain with no residual
slack outside it. -/
structure RefToken where
  chars : List Char
  single_sep : (chars.filter (· == '.')).length ≤ 1
  ascii : asciiToken chars
-- pure-end

-- post-conditions-start
/-- The normalized token is pinned to the input token `t.chars` by shape:

  * when `t.chars` contains a separator `.`, the result is the verbatim prefix
    segment, the separator, then the trailing name segment with every character
    lowercased — the prefix's case is preserved exactly;
  * when `t.chars` contains no separator, the result is `t.chars` with every
    character lowercased.

No output component is left free: every character of the result is determined by
`t.chars` (prefix copied verbatim, trailing/whole segment lowercased
per-character), for EVERY token of the modeled domain. -/
def problem_spec_modelRef (t : RefToken) (result : List Char) : Prop :=
  ('.' ∈ t.chars →
    result = prefixSeg t.chars ++ '.' :: (nameSeg t.chars).map Char.toLower)
  ∧ ('.' ∉ t.chars → result = t.chars.map Char.toLower)
-- post-conditions-end

-- impl-start
def implementation_modelRef (t : RefToken) : List Char := Id.run do
  -- Pre-patch behavior: the whole token is lowercased unconditionally, with no
  -- separator handling, so a qualified token's prefix is wrongly lowercased too.
  return t.chars.map Char.toLower
-- impl-end

-- proof-start
theorem correct_modelRef :
    ∀ (t : RefToken),
      problem_spec_modelRef t (implementation_modelRef t) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
