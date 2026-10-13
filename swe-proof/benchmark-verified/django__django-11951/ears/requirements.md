# Requirements: Cap the explicit `bulk_create` batch size by the backend-compatible maximum

## Introduction

`QuerySet.bulk_create()` (in `django/db/models/query.py`) inserts objects into
the database in batches. The actual batching is performed by the private helper
`QuerySet._batched_insert(objs, fields, batch_size, ignore_conflicts=...)`,
which slices the list of objects into consecutive chunks and issues one INSERT
statement per chunk.

Each database backend advertises a maximum number of rows it can safely insert
in a single statement, exposed through
`connections[db].ops.bulk_batch_size(fields, objs)`. This backend limit exists
because a single INSERT with too many rows (too many bound parameters) can
exceed database limits.

Previously, when the caller supplied an explicit `batch_size` to
`bulk_create()`, that value was used verbatim as the chunk size, completely
ignoring the backend-compatible maximum. As a result, an explicit `batch_size`
larger than the backend maximum could produce INSERT statements that exceed the
backend's capabilities. The companion method `bulk_update()` already guards
against this by taking the minimum of the requested size and the computed
maximum.

The goal is to make `_batched_insert` honor the backend-compatible maximum even
when an explicit `batch_size` is given: the effective chunk size must be the
smaller of the requested `batch_size` and the backend maximum, while preserving
the existing behavior when no `batch_size` (or a falsy one) is supplied.

## Requirement 1: Cap an explicit batch size by the backend-compatible maximum

**User story:** As a developer calling `bulk_create()` with an explicit
`batch_size`, I want the batch size to never exceed what the database backend
can handle, so that large explicit batch sizes do not produce INSERT statements
that violate backend limits.

**Acceptance criteria**

1. The system SHALL compute a backend-compatible maximum batch size defined as
   `max(connections[db].ops.bulk_batch_size(fields, objs), 1)` (i.e. the value
   reported by the backend's `bulk_batch_size` for the given fields and objects,
   but never less than 1).
2. WHEN `bulk_create()` is called with a truthy explicit `batch_size` that is
   greater than the backend-compatible maximum, THEN `_batched_insert` SHALL use
   the backend-compatible maximum as the effective chunk size rather than the
   requested `batch_size`.
3. WHEN `bulk_create()` is called with a truthy explicit `batch_size` that is
   less than or equal to the backend-compatible maximum, THEN `_batched_insert`
   SHALL use that requested `batch_size` as the effective chunk size.
4. IF a truthy explicit `batch_size` is supplied, THEN the effective chunk size
   SHALL equal the minimum of the requested `batch_size` and the
   backend-compatible maximum.
5. WHEN objects are inserted, THEN the total number of INSERT statements issued
   SHALL equal `ceil(number_of_objects / effective_chunk_size)`, so that
   supplying an explicit `batch_size` one greater than the backend maximum
   results in the same number of statements as the backend maximum would.

## Requirement 2: Preserve default behavior when no batch size is supplied

**User story:** As a developer calling `bulk_create()` without a `batch_size`
(or with a falsy one), I want the backend-compatible maximum to be used, so that
existing behavior is unchanged.

**Acceptance criteria**

1. WHEN `bulk_create()` is called with `batch_size` equal to `None`, THEN
   `_batched_insert` SHALL use the backend-compatible maximum as the effective
   chunk size.
2. IF `batch_size` is falsy (e.g. `None` or `0`), THEN `_batched_insert` SHALL
   use the backend-compatible maximum as the effective chunk size.
3. The system SHALL continue to insert all objects in a single INSERT statement
   whenever the number of objects does not exceed the effective chunk size.

## Requirement 3: Preserve existing bulk_create semantics

**User story:** As a Django user relying on `bulk_create()`, I want all other
insertion behavior to remain unchanged, so that only the batch-size capping is
affected.

**Acceptance criteria**

1. The system SHALL continue to insert every supplied object exactly once,
   preserving their order, regardless of the effective chunk size.
2. WHEN objects are inserted in multiple chunks, THEN each chunk SHALL contain
   consecutive objects and no object SHALL be inserted in more than one chunk.
3. WHEN `bulk_create()` is called on a backend that supports returning rows from
   bulk insert and `ignore_conflicts` is not requested, THEN the primary keys
   (and other returned fields) SHALL be populated on the created objects as
   before.
4. IF `ignore_conflicts` is requested on a backend that does not support
   ignoring conflicts, THEN the system SHALL raise the same not-supported error
   as before.
5. The system SHALL keep rejecting a non-positive explicit `batch_size` exactly
   as before (a `batch_size` must be `None` or a positive integer).
6. WHEN the list of objects to insert is empty, THEN the system SHALL issue no
   INSERT statements.
