import Mathlib
-- imports-end

/-!
Splitting a trailing run of digits off a symbol name so those digits can be
treated as a subscript.

When a symbol name consists of one or more *letters* immediately followed by one
or more *digits* — and nothing else, except that one final newline character is
tolerated after the digits — it is split into two parts: the leading letters
(the base name) and the digit run (which becomes a subscript; the tolerated
final newline, when present, is dropped). Any name that does not have this
letters-then-digits shape is left untouched (no subscript is peeled off).

A "letter" here is any alphabetic character in the full character repertoire —
including non-Latin scripts such as Greek — not merely the ASCII letters
`a`–`z`/`A`–`Z`. Likewise a "digit" is any decimal-digit character, not merely
the ASCII digits `0`–`9`. Concretely, the split succeeds exactly when the name
is a non-empty maximal block of letters followed by a non-empty block of digits,
followed by nothing at all or by a single terminating newline (`'\n'`). The
newline tolerance mirrors the end-of-input matching rule the routine's engine
uses: "end" also matches just before one final newline.
-/

-- axioms-start
-- Two unchanged, library-provided character-classification primitives, exposed
-- here only by signature (`opaque`). They are consulted, not modified, by the
-- routine under specification:
--
-- * `isUnicodeLetter c` — whether `c` is an alphabetic character in the full
--   character repertoire (any script, not only ASCII).
-- * `isUnicodeDigit c`  — whether `c` is a decimal-digit character in the full
--   character repertoire (any script, not only ASCII).
--
-- The proof needs no property axiom about either: the specification is stated
-- directly over them and discharged structurally. G-AX validates that these
-- signatures match the real classification the routine consults, and G-CONF
-- drives the differential test with the real classification.
opaque isUnicodeLetter : Char → Bool
opaque isUnicodeDigit : Char → Bool
-- axioms-end

-- pure-start
/-- Split a symbol name into its leading letter block and, when what follows is
a non-empty all-digit block (with at most one final newline after it), that
digit block (a subscript).

`base` is the longest prefix of `name` made of letters; `digits` is the digit
run that follows; `trailer` is whatever remains after those digits. The split
into `(base, some digits)` happens exactly when `base` is non-empty, `digits`
is non-empty, and `trailer` is either empty or the single character `'\n'` —
i.e. `name` is letters-then-digits with nothing else, except that one
terminating newline is tolerated (end-of-input also matches just before one
final newline). The tolerated newline is NOT part of the result: the split
returns only the letters and the digits. Otherwise the name is returned
unchanged (newline and all) with no subscript. -/
def splitTrailingDigits (name : List Char) : List Char × Option (List Char) :=
  let base := name.takeWhile isUnicodeLetter
  let rest := name.dropWhile isUnicodeLetter
  let digits := rest.takeWhile isUnicodeDigit
  let trailer := rest.dropWhile isUnicodeDigit
  if !base.isEmpty && !digits.isEmpty && (trailer.isEmpty || trailer == ['\n']) then
    (base, some digits)
  else
    (name, none)
-- pure-end

-- post-conditions-start
/-- The result is exactly the letters-then-digits split of the name dictated by
the rule above: the base name paired with the trailing digit subscript when the
name has that shape (up to one tolerated final newline, which is dropped), or
the unchanged name with no subscript otherwise. -/
def problem_spec_splitTrailingDigits (name : List Char)
    (result : List Char × Option (List Char)) : Prop :=
  result = splitTrailingDigits name
-- post-conditions-end

-- impl-start
def implementation_splitTrailingDigits (name : List Char) :
    List Char × Option (List Char) := Id.run do
  -- Pre-patch behaviour: only ASCII letters `a`–`z`/`A`–`Z` count as the base
  -- and only ASCII digits `0`–`9` count as the trailing block. A name whose
  -- letters or digits lie outside ASCII (e.g. a Greek base, or a non-ASCII
  -- decimal digit) is therefore left unsplit. The single-final-newline
  -- tolerance after the digits is the engine's end-of-input rule and is the
  -- same pre- and post-patch.
  let base := name.takeWhile Char.isAlpha
  let rest := name.dropWhile Char.isAlpha
  let digits := rest.takeWhile Char.isDigit
  let trailer := rest.dropWhile Char.isDigit
  if !base.isEmpty && !digits.isEmpty && (trailer.isEmpty || trailer == ['\n']) then
    return (base, some digits)
  return (name, none)
-- impl-end

-- proof-start
theorem correct_splitTrailingDigits :
    ∀ (name : List Char),
      problem_spec_splitTrailingDigits name (implementation_splitTrailingDigits name) := by
  intro name
  unfold problem_spec_splitTrailingDigits implementation_splitTrailingDigits splitTrailingDigits
  simp only [Id.run, bind, pure]
-- proof-end
