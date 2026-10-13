# Requirements: Detect default-fixture-directory duplicates when `FIXTURE_DIRS` entries are `Path` objects

## Introduction

Django's `loaddata` management command assembles the list of directories it
searches for fixtures. This logic lives in the `fixture_dirs` cached property of
the `Command` class in `django/core/management/commands/loaddata.py`. Among the
directories it uses are the `fixtures` subdirectory of each installed
application (the application's *default* fixtures directory) and the entries the
user configures in `settings.FIXTURE_DIRS`.

To avoid loading the same fixtures twice, `fixture_dirs` enforces two guards
before building its result:

- `settings.FIXTURE_DIRS` must not contain duplicate entries.
- No application's own default fixtures directory (`<app.path>/fixtures`) may
  also be listed explicitly in `settings.FIXTURE_DIRS`.

Each application's default directory is computed with `os.path.join`, so it is
always a text string. However, `settings.FIXTURE_DIRS` is documented to accept
each entry either as a text string or as a `pathlib.Path` object. The
per-application guard compared the (string) default directory directly against
the configured entries; when a configured entry naming the same location was a
`Path` object rather than a string, the two never compared equal, so the
collision went undetected and the misconfiguration was silently accepted.

The goal is to make the per-application default-directory collision check
compare *locations*, so that a configured entry which names an application's
default fixtures directory is detected and rejected regardless of whether that
entry was supplied as a text string or as a `Path` object — while leaving every
other behavior of `fixture_dirs` unchanged.

## Requirement 1: Detect a default-fixture-directory collision regardless of entry type

**User story:** As a Django developer who configures `settings.FIXTURE_DIRS`
using `pathlib.Path` objects, I want listing an application's own default
fixtures directory to be rejected just as it is when I list it as a string, so
that I get the same misconfiguration error and fixtures are never loaded twice.

**Acceptance criteria**

1. WHEN `loaddata` computes the fixture directories AND some installed
   application's default fixtures directory (its `fixtures` subdirectory) is
   named by an entry of `settings.FIXTURE_DIRS` that was supplied as a
   `pathlib.Path` object, THEN the `fixture_dirs` property SHALL detect this as a
   collision and SHALL raise `ImproperlyConfigured` identifying that application.
2. WHEN comparing an application's default fixtures directory against the
   configured `settings.FIXTURE_DIRS` entries, THEN the property SHALL compare
   each configured entry by its textual directory location rather than by object
   identity or runtime type, so that an entry given as a `Path` object and the
   equivalent entry given as a text string are treated identically.
3. WHEN `settings.FIXTURE_DIRS` lists an application's own default fixtures
   directory as an ordinary text string, THEN the property SHALL continue to
   detect the collision and raise `ImproperlyConfigured` identifying that
   application (this behavior SHALL be preserved).
4. WHEN more than one application's default directory would collide, THEN the
   property SHALL report the first offending application in application-iteration
   order.
5. The `ImproperlyConfigured` raised for a default-directory collision SHALL
   continue to name the colliding default directory and the offending
   application's label in its message, unchanged from prior behavior.

## Requirement 2: Preserve `FIXTURE_DIRS` assembly and other guards (regression protection)

**User story:** As a maintainer, I want every other aspect of building the
fixture-directory list to behave exactly as before, so that fixing the type
comparison does not change duplicate detection, ordering, path normalization, or
successful loading.

**Acceptance criteria**

1. IF `settings.FIXTURE_DIRS` contains duplicate entries, THEN the property
   SHALL raise `ImproperlyConfigured` reporting that `settings.FIXTURE_DIRS`
   contains duplicates.
2. WHEN no application's default directory collides with any configured entry
   and there are no duplicates, THEN the property SHALL complete without raising
   and SHALL return the assembled list of fixture directories.
3. WHEN entries of `settings.FIXTURE_DIRS` are supplied as `pathlib.Path`
   objects and none of them collides with a default directory, THEN the property
   SHALL accept them and include them in the returned directory list without
   error.
4. The returned list SHALL consist of each installed application's existing
   default fixtures directory, followed by the configured `settings.FIXTURE_DIRS`
   entries, followed by the current directory, with each element normalized to
   its real (canonical) filesystem path — this composition and ordering SHALL be
   preserved.
5. WHEN a specific application label is being targeted, THEN the property SHALL
   restrict the included default directories to that application as it did
   previously, while still applying the collision guard across all installed
   applications.
6. WHEN configured directories are given as relative paths, as strings, or as
   paths containing dot segments, THEN the property SHALL continue to resolve and
   include them so that valid fixture-directory configurations keep loading
   fixtures successfully.
