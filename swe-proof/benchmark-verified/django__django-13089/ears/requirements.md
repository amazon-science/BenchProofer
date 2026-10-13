# Requirements: Robust culling in the database cache backend

## Introduction

The database cache backend (`DatabaseCache` in
`django/core/cache/backends/db.py`) keeps cached entries as rows in a database
table, each row identified by a distinct `cache_key` and carrying an `expires`
instant. When a new value is stored, the backend may run a maintenance/culling
pass (`_cull`) to keep the number of rows within the configured maximum.

The culling pass, when it must reduce the table, asks the database for a
"boundary" cache key (via `connection.ops.cache_key_culling_sql()`) and then
deletes every row whose `cache_key` sorts strictly below that boundary. Under
certain configurations the boundary query returns no row at all. The original
code unconditionally read the first column of the fetched row, so when no row
was returned it raised `TypeError: 'NoneType' object is not subscriptable`,
causing an otherwise-successful `set()` to fail sporadically.

The goal is to make the culling pass tolerate an empty boundary result: it must
skip the boundary-based deletion in that case, complete without error, and leave
the freshly stored entry intact — while preserving all existing culling and
caching behavior.

## Requirement 1: Culling tolerates an empty boundary result

**User story:** As a developer using the database cache backend, I want storing
a value to never raise an error during the internal culling pass, so that cache
writes remain reliable even when the culling boundary lookup returns nothing.

**Acceptance criteria**

1. WHEN the culling pass of the database cache backend runs the culling-boundary
   query and that query returns no row, THEN the backend SHALL NOT attempt to
   read a column from the missing row and SHALL NOT raise an error (in
   particular, no `TypeError` about a `NoneType` not being subscriptable).
2. WHEN the culling-boundary query returns no row, THEN the backend SHALL skip
   the boundary-based deletion step entirely, leaving the table's rows unchanged
   by that step.
3. WHEN a value is stored under a configuration that forces the culling pass to
   run and the boundary query to return no row, THEN the store operation SHALL
   complete successfully and the just-stored key SHALL be present in the cache
   afterward (a lookup for that key SHALL report it as present).
4. IF the culling-boundary query returns an actual row, THEN the backend SHALL
   read that row's first value and SHALL delete every entry whose `cache_key`
   sorts strictly below that value, exactly as before.

## Requirement 2: Existing culling behavior is preserved

**User story:** As a maintainer, I want the standard size-limiting behavior of
the database cache to keep working unchanged, so that the fix for the empty
boundary case does not weaken cache size management.

**Acceptance criteria**

1. WHEN a value is stored and the maintenance pass runs, THEN the backend SHALL
   first delete every entry whose `expires` instant lies strictly before the
   reference instant `now`.
2. WHEN, after removing expired entries, the number of remaining entries does
   not exceed the configured maximum number of entries, THEN the backend SHALL
   perform no further deletion and SHALL leave the remaining entries in place.
3. WHEN, after removing expired entries, the number of remaining entries exceeds
   the configured maximum, THEN the backend SHALL compute the number of entries
   to cull as the remaining count integer-divided by the configured cull
   frequency, request the boundary key for that number of entries, and (when a
   boundary key is returned) delete every entry whose `cache_key` sorts strictly
   below it.
4. IF the configured cull frequency is zero, THEN the backend SHALL clear the
   entire cache table rather than performing boundary-based culling.
5. The system SHALL continue to support the full set of database cache
   operations — setting, getting, adding, deleting, touching, versioning, and
   key validation — with their existing return values and semantics unaffected
   by this change.

## Requirement 3: Culling remains internal and repeatable

**User story:** As a developer, I want the culling pass to be safe to trigger
repeatedly, so that consecutive cache writes never accumulate into a crash.

**Acceptance criteria**

1. WHEN the culling pass runs on any table state (including a table that is
   empty or effectively empty after expiry removal), THEN the backend SHALL
   complete the pass without raising an error.
2. WHILE further cache writes continue to trigger the culling pass, the backend
   SHALL keep completing each pass successfully without leaking the boundary
   lookup's empty result into a failure.
