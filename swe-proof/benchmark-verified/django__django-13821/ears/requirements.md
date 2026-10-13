# Requirements: Raise the minimum supported SQLite version to 3.9.0

## Introduction

Django's SQLite backend performs a startup guard that rejects SQLite libraries
older than a supported minimum. The guard lives in the module-level function
`check_sqlite_version()` in `django/db/backends/sqlite3/base.py`, which is
invoked at import time of that module. It compares the running SQLite library's
version against a hard-coded minimum and raises
`django.core.exceptions.ImproperlyConfigured` (with a human-readable message
that reports the required minimum and the version actually found) when the
library is too old.

Because Django now depends on features that are only available from SQLite
3.9.0 onward (expression indexes and the JSON1 compile-time option), the
supported minimum must be raised from the previous value to **3.9.0**. This
change affects both the boundary at which the guard fires and the text of the
message it produces. The goal is to ensure the backend refuses to run against
any SQLite older than 3.9.0 while continuing to accept 3.9.0 and later, and to
report the new minimum accurately.

## Requirement 1: Enforce 3.9.0 as the minimum SQLite version

**User story:** As a Django developer, I want the SQLite backend to reject any
SQLite library older than 3.9.0, so that I fail fast rather than hitting
missing-feature errors at runtime.

**Acceptance criteria**
1. WHEN `check_sqlite_version()` is invoked and the running SQLite library's
   version information is strictly less than 3.9.0, THEN the backend SHALL
   raise `django.core.exceptions.ImproperlyConfigured`.
2. IF the running SQLite library's version information is any value below
   3.9.0 — including versions at or above the previously supported minimum but
   below 3.9.0 — THEN the backend SHALL treat it as unsupported and raise the
   error.
3. The system SHALL perform the comparison against the library version using
   its numeric version-info components (not a lexical string comparison), so
   that versions are ordered numerically component-by-component rather than by
   string sort order. In particular, a version whose textual form would sort
   incorrectly under lexical comparison (for example a component whose
   numeric value has more digits, such that a lexical sort would misplace it
   relative to a value with fewer digits) SHALL still be classified correctly
   relative to 3.9.0.
4. WHEN the running SQLite library's version information is 3.9.0 or greater,
   THEN `check_sqlite_version()` SHALL return normally without raising.

## Requirement 2: Report the required minimum and the version found

**User story:** As a Django developer, I want the error to tell me both the
required minimum and the version I actually have, so that I know exactly what
to upgrade.

**Acceptance criteria**
1. WHEN the guard raises because the SQLite library is too old, THEN the
   raised `ImproperlyConfigured` message SHALL state that SQLite 3.9.0 or later
   is required.
2. WHEN the guard raises, THEN the message SHALL report the version actually
   found, using the library's reported version string, in the form
   `SQLite 3.9.0 or later is required (found <version>).`.
3. The system SHALL name the required minimum in the message as `3.9.0`
   exactly (not the previously supported minimum).
4. WHEN the guard raises, THEN the "found" value in the message SHALL be the
   library's own reported version string reproduced verbatim, whatever its
   form, rather than a reformatted or truncated rendering of the version.

## Requirement 3: Preserve existing SQLite backend behavior

**User story:** As a Django maintainer, I want the version-guard change to be
surgical, so that unrelated SQLite backend behavior keeps working.

**Acceptance criteria**
1. The system SHALL continue to run the version check automatically at import
   time of the SQLite backend base module.
2. The system SHALL keep raising the same exception type,
   `django.core.exceptions.ImproperlyConfigured`, for an unsupported version
   (the exception type SHALL NOT change).
3. The system SHALL leave all other SQLite backend behavior unchanged,
   including parameter escaping and quoting, last-executed-query reporting,
   distinct aggregation handling, date/time aggregation restrictions, named
   in-memory database support, pathlib-based database names, the custom REGEXP
   function, cross-thread database sharing, and schema operations such as
   autoincrement handling and atomic constraint-check toggling.
