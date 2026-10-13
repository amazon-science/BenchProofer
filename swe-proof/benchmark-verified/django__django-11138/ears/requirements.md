# Requirements: honor the database connection's TIME_ZONE when converting datetimes

## Introduction

When `USE_TZ` is enabled, Django stores datetimes in databases that lack native
time-zone support (MySQL, SQLite, Oracle) as naive local values, and converts
them at query time so that datetime lookups (for example a `__date` lookup)
compare correctly against values expressed in the current time zone.

Each database connection can carry its own `TIME_ZONE` setting
(`DATABASES[...]['TIME_ZONE']`), which names the time zone the stored values are
actually recorded in. Before this change the backends ignored that setting: the
conversion always assumed the stored values were in UTC (MySQL used
`'UTC'` as the conversion source, Oracle used the `'0:00'` offset, SQLite passed
no source zone), so on a legacy database whose connection time zone was not UTC,
date-based lookups produced wrong results. A second problem is that a conversion
was emitted even when the source and target time zones were identical, which
needlessly required MySQL/Oracle time-zone tables to be populated.

The goal is to make the query-time conversion use the connection's configured
time zone as the *source* of the conversion, and to skip the conversion entirely
when the source and target time zones coincide. The affected code is the
per-backend datetime-conversion helpers:

- MySQL: `DatabaseOperations._convert_field_to_tz` in
  `django/db/backends/mysql/operations.py`.
- Oracle: `DatabaseOperations._convert_field_to_tz` in
  `django/db/backends/oracle/operations.py`.
- SQLite: the datetime-conversion SQL builders in
  `django/db/backends/sqlite3/operations.py` (`datetime_cast_date_sql`,
  `datetime_cast_time_sql`, `datetime_extract_sql`, `datetime_trunc_sql`) and
  the Python callbacks they invoke in `django/db/backends/sqlite3/base.py`
  (`_sqlite_datetime_parse`, `_sqlite_datetime_cast_date`,
  `_sqlite_datetime_cast_time`, `_sqlite_datetime_extract`,
  `_sqlite_datetime_trunc`, registered via `get_new_connection`).

Throughout, "connection time zone" means the connection's `timezone_name`
(the value derived from the connection's `TIME_ZONE`, which is `'UTC'` when no
per-connection `TIME_ZONE` is configured), and "target time zone" means the
`tzname` the caller asks the value to be expressed in (the current time zone).

## Requirement 1: Convert from the connection time zone, not from UTC

**User story:** As a developer whose database connection has its own
`TIME_ZONE`, I want datetime lookups to convert stored values from that
connection time zone, so that queries against a legacy non-UTC database return
correct results.

**Acceptance criteria**
1. WHEN time-zone-aware processing is enabled and the connection time zone
   differs from the target time zone on the MySQL backend, THEN
   `_convert_field_to_tz` SHALL wrap the column expression in a conversion whose
   source time zone is the connection time zone and whose destination time zone
   is the target time zone (i.e. `CONVERT_TZ(<column>, '<connection tz>',
   '<target tz>')`), and SHALL NOT use a hard-coded `'UTC'` source.
2. WHEN time-zone-aware processing is enabled and the connection time zone
   differs from the target time zone on the Oracle backend, THEN
   `_convert_field_to_tz` SHALL produce a conversion whose source time zone is
   the connection time zone and whose destination time zone is the target time
   zone, cast back to a bare timestamp, and SHALL NOT use a hard-coded `'0:00'`
   source offset.
3. WHEN time-zone-aware processing is enabled and the connection time zone
   differs from the target time zone on the SQLite backend, THEN the emitted SQL
   SHALL supply both the target time zone and the connection time zone to the
   datetime-conversion callback, and the callback SHALL first interpret the
   stored naive value as being in the connection time zone and then express it
   in the target time zone.
4. WHEN the connection has no per-connection `TIME_ZONE` configured, THEN the
   connection time zone used as the conversion source SHALL be `'UTC'`, so that
   the historical UTC-source behavior is preserved for the default case.

## Requirement 2: Skip conversion when source and target time zones are equal

**User story:** As a developer whose connection time zone already matches the
current time zone, I want no conversion emitted, so that date lookups work
without needing populated time-zone tables and without altering the value.

**Acceptance criteria**
1. WHEN time-zone-aware processing is enabled and the connection time zone
   equals the target time zone on the MySQL backend, THEN `_convert_field_to_tz`
   SHALL return the column expression unchanged, emitting no conversion wrapper.
2. WHEN time-zone-aware processing is enabled and the connection time zone
   equals the target time zone on the Oracle backend, THEN
   `_convert_field_to_tz` SHALL return the column expression unchanged, emitting
   no conversion wrapper.
3. WHEN time-zone-aware processing is enabled and the connection time zone
   equals the target time zone on the SQLite backend, THEN the datetime-
   conversion callback SHALL leave the parsed value in the connection time zone
   and SHALL NOT apply a further conversion to the target time zone.
4. WHEN a datetime is stored and then queried through a `__date` lookup while
   the connection time zone equals the current time zone, THEN the stored row
   SHALL be found by that lookup (the value is presented in the zone it is
   already recorded in, with no shift).
5. WHEN a datetime is stored and then queried through a `__date` lookup while
   the connection time zone differs from the current time zone, THEN the lookup
   SHALL match against the date obtained after shifting the value from the
   connection time zone to the current time zone (for example, a value recorded
   in a zone four hours ahead SHALL match the date that is four hours earlier).

## Requirement 3: Preserve behavior when time-zone support is disabled

**User story:** As a developer who has not enabled time-zone support, I want the
conversion helpers to leave column expressions untouched, so that non-tz-aware
queries keep working exactly as before.

**Acceptance criteria**
1. IF time-zone-aware processing is disabled, THEN the MySQL and Oracle
   `_convert_field_to_tz` helpers SHALL return the column expression unchanged.
2. IF time-zone-aware processing is disabled, THEN the SQLite datetime-
   conversion SQL builders SHALL pass a null (no-op) value for both the target
   and connection time-zone arguments, so that the callback performs no
   conversion.
3. The system SHALL keep converting a stored aware datetime to and from the
   connection time zone on read and write when time-zone support is enabled,
   preserving the round-trip value already relied upon (a value written under a
   given connection time zone reads back as the same instant).

## Requirement 4: Keep the SQLite callback contract and other conversion behavior intact

**User story:** As a maintainer, I want the SQLite datetime callbacks to accept
the connection time zone alongside the existing arguments and to keep all other
conversion semantics, so that no existing datetime query regresses.

**Acceptance criteria**
1. The system SHALL register the SQLite datetime-conversion callbacks with an
   argument count that accommodates the additional connection-time-zone
   argument, so that every SQL fragment those builders emit can be evaluated
   without an arity mismatch.
2. WHEN the value passed to a SQLite datetime-conversion callback is null, THEN
   the callback SHALL return null without attempting conversion.
3. WHEN a stored timestamp string cannot be parsed as a timestamp, THEN the
   SQLite datetime-conversion callback SHALL return null.
4. IF the Oracle backend is asked to convert using a time-zone name that does
   not match the accepted time-zone-name pattern, THEN `_convert_field_to_tz`
   SHALL raise a `ValueError` reporting the invalid time zone name.
5. The system SHALL continue to return the correct extracted, truncated, cast-
   to-date, and cast-to-time results for datetime lookups after the conversion
   source is applied, matching the results produced before this change whenever
   the connection time zone is UTC.
