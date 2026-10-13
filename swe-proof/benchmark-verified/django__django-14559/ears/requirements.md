# Requirements: Return the number of matched rows from `bulk_update()`

## Introduction

The `bulk_update()` method of Django's model `QuerySet` (in
`django/db/models/query.py`, class `QuerySet`) updates a set of given fields on a
collection of already-persisted model instances by issuing one or more SQL
`UPDATE` statements, one per batch, inside a single database transaction.

Historically `bulk_update()` returned `None`, which is inconsistent with the
related `QuerySet.update()` method that returns the number of rows matched by
its `UPDATE`. This makes it impossible for callers to learn how many rows were
affected by a bulk update.

The goal is to make `bulk_update()` return the total number of rows matched
across all of the `UPDATE` statements it issues, mirroring `update()`, while
preserving every existing validation and query-execution behavior. Because
`bulk_update()` groups objects into batches and each batch's `UPDATE` filters on
the set of primary keys in that batch, the returned count must reflect the
match semantics of those per-batch `UPDATE` statements (in particular, how
repeated objects are handled within and across batches).

## Requirement 1: Return the total number of matched rows

**User story:** As a developer calling `bulk_update()`, I want it to return the
number of rows matched by the underlying update statements, so that I can learn
how many rows were affected, consistently with `update()`.

**Acceptance criteria**

1. WHEN `bulk_update()` is called with a non-empty collection of objects and it
   issues one or more `UPDATE` statements, THEN `bulk_update()` SHALL return an
   integer equal to the sum of the row-match counts reported by each of those
   `UPDATE` statements.
2. WHEN every object in the collection corresponds to a distinct, existing row
   and all objects are processed in a single batch, THEN `bulk_update()` SHALL
   return an integer equal to the number of objects supplied.
3. WHEN a large collection is split into multiple batches, THEN `bulk_update()`
   SHALL return the sum of the matched-row counts across all batches, which for
   distinct existing rows equals the total number of objects supplied.
4. The system SHALL return an integer value from `bulk_update()` in all cases
   where update statements are executed (it SHALL NOT return `None`).

## Requirement 2: Empty input returns zero without querying

**User story:** As a developer, I want calling `bulk_update()` with no objects to
report zero affected rows and perform no database work, so that empty calls are
safe and their return value is still usable as a count.

**Acceptance criteria**

1. WHEN `bulk_update()` is called with an empty collection of objects, THEN
   `bulk_update()` SHALL return the integer `0`.
2. WHEN `bulk_update()` is called with an empty collection of objects, THEN the
   system SHALL execute no database queries.

## Requirement 3: Correct counting of repeated objects

**User story:** As a developer, I want the returned count to reflect how the
per-batch update statements actually match rows when the same object appears
more than once, so that the number is accurate and not naively over- or
under-counted.

**Acceptance criteria**

1. WHEN the same object appears more than once within a single batch, THEN the
   contribution of that batch to the returned count SHALL reflect the number of
   distinct rows matched by that batch's primary-key filter (i.e. a repeated
   primary key within one batch is matched once).
2. WHEN one or more objects are repeated but all occurrences of each such object
   fall within the same batch, THEN each affected row SHALL contribute exactly
   `1` to the returned count (counted once), and not once per occurrence, because
   that batch's single `UPDATE` matches the row a single time regardless of how
   many times its primary key is listed.
3. WHEN the occurrences of a repeated object are distributed across more than one
   batch, THEN that row SHALL contribute to the returned count once for each
   batch whose primary-key filter includes it, because each batch issues its own
   `UPDATE` that independently matches the row.
4. The returned total SHALL be the arithmetic sum of the per-batch matched-row
   counts, so repeated rows split across different batches are counted once per
   batch in which they appear.

## Requirement 4: Preserve existing validation and execution behavior

**User story:** As a maintainer, I want all pre-existing `bulk_update()` behavior
to remain unchanged, so that adding a return value does not regress validation,
batching, transactional execution, or field handling.

**Acceptance criteria**

1. IF `batch_size` is provided and is negative, THEN `bulk_update()` SHALL raise
   `ValueError` and SHALL NOT perform any update.
2. IF no field names are provided, THEN `bulk_update()` SHALL raise `ValueError`
   and SHALL NOT perform any update.
3. IF any supplied object has no primary key set, THEN `bulk_update()` SHALL
   raise `ValueError` and SHALL NOT perform any update.
4. IF any named field is not a concrete field, or is a many-to-many field, THEN
   `bulk_update()` SHALL raise `ValueError`.
5. IF any named field is a primary key field, THEN `bulk_update()` SHALL raise
   `ValueError`.
6. The system SHALL continue to execute the batch `UPDATE` statements inside a
   single database transaction for the queryset's database.
7. The system SHALL continue to update the given fields correctly for all
   supported field kinds (including boolean, datetime, JSON, IP address, and
   custom-column fields), for objects with custom or falsey-but-valid primary
   keys, for inherited fields, and when field values are expressions,
   references, or `None`.
8. The system SHALL continue to respect the effective batch size, deriving it
   from the database's bulk-batch-size limit and any caller-supplied
   `batch_size`, and SHALL continue to issue the corresponding number of
   `UPDATE` queries.
