# Requirements: Load migrations from packages without an `__init__.py`

## Introduction

Django's migration framework discovers each installed application's migrations
by importing that application's migrations package and inspecting it. This logic
lives in `MigrationLoader.load_disk` in
`django/db/migrations/loader.py`. During the scan, `load_disk` imports the
migrations module for every app, decides whether the app is *migrated* (it
participates in the migration graph) or *unmigrated*, and, for migrated apps,
enumerates the migration files found in the package and records them in
`disk_migrations`.

In Python 3 a directory that has no `__init__.py` is an implicit *namespace
package*: it still exposes a `__path__` (a search path) but has no `__file__`
attribute. Migration file discovery uses `pkgutil.iter_modules(module.__path__)`,
which only needs the search path, so a namespace package can be enumerated
correctly. However, `load_disk` also tested `getattr(module, '__file__', None)
is None` and classified any such module as unmigrated, skipping it entirely.
That `__file__` check is obsolete (it predates the switch to
`pkgutil.iter_modules`) and it prevents `migrate` from working when an app's
migrations directory is a namespace package.

The goal is to stop treating a migrations package as unmigrated merely because
it lacks an on-disk file marker (`__file__`), so that migrations living in an
implicit or explicit namespace package are discovered and loaded, while every
existing rule for real modules, non-package modules, empty packages, and file
filtering is preserved.

## Requirement 1: Load migrations from packages that have no `__file__`

**User story:** As a Django developer whose app keeps its migrations in a
directory without an `__init__.py` (an implicit namespace package), I want those
migrations to be discovered and loaded, so that `makemigrations`/`migrate` and
the migration graph work for namespace-packaged migrations just as they do for
ordinary packages.

**Acceptance criteria**

1. WHEN `MigrationLoader.load_disk` successfully imports an application's
   migrations module and that module exposes a package search path (a
   `__path__`), THEN the loader SHALL enumerate migration files from that search
   path and SHALL NOT skip or discard the module solely because it has no
   `__file__` attribute (i.e. because `__file__` is `None` or absent).
2. WHEN the migrations module is a namespace package (it exposes a `__path__`
   but has no `__file__`) that contains at least one discoverable migration
   file, THEN the loader SHALL classify that application as migrated and SHALL
   record each discovered migration in `disk_migrations` under that application's
   label.
3. WHEN such namespace-packaged migrations are loaded, THEN the resulting
   migration graph SHALL contain those migrations as nodes and SHALL resolve
   their forward plan identically to the same migrations living in an ordinary
   package (a directory with an `__init__.py`).
4. The classification of an imported migrations package SHALL depend only on
   whether it exposes a search path, which migration files are discovered on
   that path, and the loader's tolerate-empty setting — never on whether the
   package carries a `__file__` marker; a package with a search path and a
   package with a search path but no `__file__` SHALL be classified identically.

## Requirement 2: Classify migrated vs. unmigrated by discovered migrations

**User story:** As a maintainer, I want an app to be counted as migrated exactly
when it actually has migration files (or the loader is explicitly told to
tolerate an empty package), so that empty migration packages are handled
correctly regardless of whether they are namespace packages.

**Acceptance criteria**

1. WHEN the loader has imported a migrations module that exposes a search path
   and at least one migration file is discovered on it, THEN the loader SHALL add
   that application's label to the migrated set.
2. WHEN the loader has imported a migrations module that exposes a search path
   but no migration file is discovered on it, THEN the loader SHALL add that
   application's label to the migrated set IF the loader is configured to treat a
   package with no migrations as migrated (its ignore-no-migrations setting is
   enabled), and SHALL otherwise add that application's label to the unmigrated
   set.
3. WHEN an application is classified as unmigrated, THEN the loader SHALL NOT
   record any migrations for that application.
4. The set of discovered migration files SHALL be exactly the entries on the
   package's search path that are not themselves subpackages and whose names do
   not begin with an underscore (`_`) or tilde (`~`); the presence or absence of
   a `__file__` marker SHALL NOT change which files are discovered.

## Requirement 3: Preserve existing loader behavior (regression protection)

**User story:** As a maintainer, I want every other branch of the migrations
scan to behave exactly as before, so that ordinary packages, non-package
modules, missing modules, and file-name filtering are unaffected by removing the
`__file__` check.

**Acceptance criteria**

1. WHEN the imported migrations object is not a package (it exposes no
   `__path__`, e.g. a single `migrations.py` module file), THEN the loader SHALL
   classify that application as unmigrated and SHALL record no migrations for it.
2. IF the application has no migrations module configured (its module name
   resolves to nothing), THEN the loader SHALL classify that application as
   unmigrated.
3. IF importing the migrations module fails with an import error that indicates
   the migrations module itself is absent (for a non-explicit module), or the
   module is explicitly configured and the loader is set to tolerate missing
   migrations, THEN the loader SHALL classify that application as unmigrated
   rather than propagate the error; any other import error SHALL be propagated
   unchanged.
4. The loader SHALL continue to exclude, from the discovered migration files,
   every entry that is itself a subpackage and every entry whose name begins with
   `_`, `~`, or `.`, so that dunder files, private/backup files, and dotfiles are
   not loaded as migrations.
5. WHEN a migrations module was already present in the import cache before this
   scan, THEN the loader SHALL reload it before enumerating its migration files,
   preserving the existing reload behavior.
6. WHEN a discovered migration module is imported, THEN the loader SHALL raise an
   error IF that module has no `Migration` class, and SHALL surface a stale
   compiled-file (bad magic number) import failure as an informative import error,
   exactly as before.
7. WHEN an ordinary (`__init__.py`-bearing) package exposes a search path, THEN
   its migrated-vs-unmigrated classification SHALL follow the same count-based
   rule as any other package with a search path (Requirement 2.1 and 2.2): it is
   migrated when at least one migration file is discovered on its path, and — when
   no migration file is discovered — migrated only if the loader tolerates empty
   packages (its ignore-no-migrations setting is enabled), otherwise unmigrated.
   The removal of the `__file__` check SHALL NOT introduce any classification
   difference between an ordinary package and a namespace package that expose the
   same search path and contain the same migration files.
8. WHEN an ordinary (`__init__.py`-bearing) package containing at least one
   discoverable migration file is loaded, THEN the loader SHALL populate
   `disk_migrations` and add the application to the migrated set as before, so
   that squashed-migration loading, prefix matching, consistency checks, and
   forward/`run_before` planning continue to succeed unchanged.
