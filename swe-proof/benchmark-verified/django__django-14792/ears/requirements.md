# Requirements: Resolve fixed-offset time zones to their offset designation

## Introduction

Django derives a textual name for a time zone through the helper
`_get_timezone_name(timezone)` in `django/utils/timezone.py`. This name is
consumed by the ORM's `TimezoneMixin.get_tzname()` and ultimately embedded in
generated SQL for the `Trunc`/`Extract` database functions (for example in a
PostgreSQL `AT TIME ZONE '...'` clause). The name is also surfaced through
`get_current_timezone_name()` and `get_default_timezone_name()`.

Historically `_get_timezone_name` returned `str(timezone)`. For a fixed-offset
zone such as `pytz.timezone("Etc/GMT-10")` (or the equivalent
`zoneinfo.ZoneInfo("Etc/GMT-10")`) this produced the full zone key
`"Etc/GMT-10"` instead of the offset designation `"+10"`. Downstream, the
database backends interpret an offset designation and a named-zone string with
opposite sign conventions, so returning the zone key reversed the direction of
the applied time-zone conversion in the emitted query — shifting results ten
hours in the wrong direction.

The goal is to make `_get_timezone_name` prefer a time zone's self-reported
short designation (its fixed-offset label) when one is available, falling back
to the full string form only when no such designation exists. This restores the
pre-regression behavior for fixed-offset zones while leaving named zones
unchanged, and it must hold uniformly across `datetime.timezone`, `pytz`, and
`zoneinfo` implementations.

## Requirement 1: Prefer a time zone's offset designation

**User story:** As a developer using `Trunc`/`Extract` with a fixed-offset time
zone, I want Django to name that zone by its UTC-offset designation, so that the
generated database query applies the conversion in the correct direction.

**Acceptance criteria**

1. WHEN `_get_timezone_name` is called with a time zone whose standard
   time-zone-name query (the tzinfo `tzname(None)` protocol call) yields a
   non-empty string, THEN `_get_timezone_name` SHALL return exactly that string.
2. IF the time zone's standard time-zone-name query yields no value (`None`) or
   an empty string, THEN `_get_timezone_name` SHALL return the full string form
   of the time zone (equivalent to `str(timezone)`).
3. The value returned by `_get_timezone_name` SHALL be fully determined by the
   two cases above: the offset/name designation when it is present and
   non-empty, and the full string form otherwise — no other value SHALL be
   produced.

## Requirement 2: Consistent results across time zone implementations

**User story:** As a developer, I want the resolved name to be consistent
whether the time zone comes from `datetime`, `pytz`, or `zoneinfo`, so that the
same conceptual zone yields the same query regardless of which library provided
it.

**Acceptance criteria**

1. The selection rule of Requirement 1 (prefer the non-empty `tzname(None)`
   result, otherwise the full string form) SHALL be applied identically
   regardless of whether the time zone object originates from
   `datetime.timezone`, `pytz`, or `zoneinfo`; no branch of behavior SHALL
   depend on the concrete tzinfo implementation type.
2. WHEN `_get_timezone_name` receives a fixed-offset zone — one whose
   `tzname(None)` yields a non-empty offset designation — from `pytz` or
   `zoneinfo`, THEN it SHALL return that offset designation rather than the
   full zone key or string form. In particular, for the publicly reported case
   of a `pytz` (or equivalent `zoneinfo`) zone built from the key
   `"Etc/GMT-10"`, the result SHALL be its offset designation `"+10"`.
3. WHEN `_get_timezone_name` receives a `datetime.timezone` constructed with an
   explicit name, THEN it SHALL return that explicit name unchanged (that name
   being what the zone reports through `tzname(None)`).
4. WHEN `_get_timezone_name` receives a named, non-fixed-offset zone from
   `pytz` or `zoneinfo`, THEN it SHALL return the zone's reported name (its
   `tzname(None)` value), not a synthesized offset.

## Requirement 3: Preserve surrounding time zone helpers (regression protection)

**User story:** As a maintainer, I want the rest of the time zone utility module
to keep working exactly as before, so that this change is confined to how a zone
is named.

**Acceptance criteria**

1. The functions `get_current_timezone_name` and `get_default_timezone_name`
   SHALL continue to derive their result by delegating to `_get_timezone_name`,
   so that they report the offset designation for fixed-offset active/default
   zones and the zone name otherwise.
2. WHEN `is_aware` is called with a datetime, THEN it SHALL report the datetime
   as aware exactly when the datetime carries a usable UTC offset (its
   `utcoffset()` is not `None`), and `is_naive` SHALL report the complementary
   result.
3. The system SHALL keep the existing behavior of `get_fixed_timezone`,
   `make_aware`, `make_naive`, `localdate`, `override`, and `activate`,
   including their handling of fixed-offset, `pytz`, and `zoneinfo` zones and of
   ambiguous or non-existent local times, unchanged by this modification.
