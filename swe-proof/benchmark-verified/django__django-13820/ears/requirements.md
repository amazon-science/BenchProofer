# Requirements: Load migrations from regular packages that lack `__file__`

## Introduction

Django discovers each application's migrations by importing that application's
migrations module and, when the module is a package, scanning its package
directory for migration modules. This discovery happens in
`django.db.migrations.loader.MigrationLoader.load_disk`.

To avoid mistakenly scanning a PEP 420 *namespace package* (an "empty
directory" that Python synthesizes when several distributions share a package
name), `load_disk` must classify each imported migrations module as either a
real source of migrations (a "migrated app") or as something to ignore (an
"unmigrated app").

The existing classification rejects any module whose `__file__` attribute is
absent or `None`. That rule is too broad: `__file__` is an *optional* module
attribute per Python's import API, and legitimate regular packages can lack it
— most notably in "frozen" Python environments (for example, applications
bundled by a freezer) that do not set `__file__` on ordinary packages. Such an
application's migrations are silently ignored even though the package really
does have migration files on its `__path__`.

The goal is to distinguish a genuine namespace package from an ordinary
package that merely lacks `__file__`, using a criterion drawn from the
documented import API: a namespace package's `__path__` is a custom iterable,
whereas an ordinary package's `__path__` is a plain built-in `list`. The
change must not alter behavior in normal Python environments, must continue to
reject true namespace packages, and must continue to ignore modules that are
not packages at all.

The affected module is `django/db/migrations/loader.py`; the affected method is
`MigrationLoader.load_disk`.

## Requirement 1: Treat an ordinary package lacking `__file__` as a migrations source

**User story:** As a developer running Django in a frozen environment where the
import system does not set `__file__` on regular packages, I want my
application's existing migrations to be discovered, so that migration commands
behave the same as in a normal environment.

**Acceptance criteria**

1. WHEN `load_disk` imports an application's migrations module and that module
   is a package (it exposes a `__path__` attribute) whose `__path__` is an
   ordinary built-in `list`, THEN `load_disk` SHALL treat the application as a
   migrated app and scan the package for migration modules, regardless of
   whether the module has a `__file__` attribute.
2. WHEN the imported migrations module has no `__file__` attribute (or its
   `__file__` is `None`) but its `__path__` is an ordinary built-in `list`,
   THEN `load_disk` SHALL discover every migration module contained in that
   package's directory, so that none of the application's migrations are
   omitted merely because `__file__` is unset.
3. The system SHALL base the "no file location" determination on whether the
   module exposes a truthy `__file__` attribute, defaulting to `None` when the
   attribute is absent rather than raising an error.

## Requirement 2: Continue to ignore genuine PEP 420 namespace packages

**User story:** As a Django maintainer, I want empty-directory namespace
packages to keep being skipped, so that a directory that shares a package name
across distributions is not mistaken for an app's migrations.

**Acceptance criteria**

1. IF an imported migrations module is a package (it exposes `__path__`) but has
   no `__file__` attribute (or its `__file__` is `None`) AND its `__path__` is
   not an ordinary built-in `list`, THEN `load_disk` SHALL treat the
   application as an unmigrated app and SHALL NOT scan it for migrations.
2. WHEN a migrations module is classified as a namespace package by the rule in
   criterion 1, THEN `load_disk` SHALL record the application among the
   unmigrated apps and SHALL continue processing the remaining applications.
3. The system SHALL keep treating a package that both lacks `__file__` and
   whose `__path__` is a custom (non-`list`) iterable as an empty-directory
   namespace, exactly as before this change.

## Requirement 3: Continue to ignore modules that are not packages

**User story:** As a developer, I want a plain (non-package) migrations module
to be ignored as before, so that a single-file module named like a migrations
module is not scanned as a package.

**Acceptance criteria**

1. IF an imported migrations module is not a package (it exposes no `__path__`
   attribute), THEN `load_disk` SHALL treat the application as an unmigrated
   app and SHALL NOT attempt to scan it for migrations.
2. The system SHALL determine whether a module is a package before it inspects
   the `__path__` attribute for the namespace-package test, so that inspecting
   `__path__` never occurs for a module that has no such attribute.
3. WHEN a migrations module cannot be imported because the migrations
   submodule does not exist (and no explicit migrations module was configured,
   or missing migrations are configured to be ignored), THEN `load_disk` SHALL
   treat the application as an unmigrated app rather than propagating the import
   error.

## Requirement 4: Preserve existing migration-discovery behavior

**User story:** As a Django user in a normal Python environment, I want
migration loading to behave exactly as it did before, so that this change is
transparent to me.

**Acceptance criteria**

1. WHEN an imported migrations module is an ordinary package that has a
   `__file__` attribute, THEN `load_disk` SHALL treat the application as a
   migrated app and scan it for migrations, unchanged from prior behavior.
2. The system SHALL discover the migration modules within a package's directory
   while excluding sub-packages and any module whose name begins with an
   underscore, tilde, or dot.
3. IF a migrations directory contains no `__init__` module (so importing it
   yields a namespace package), THEN `load_disk` SHALL treat that application as
   unmigrated.
4. WHEN a migrations module was already imported before `load_disk` runs, THEN
   `load_disk` SHALL reload it so that migrations reflect the current on-disk
   state.
5. The system SHALL continue to load squashed migrations, resolve migration
   dependencies and run-before/replaces relationships, and check for consistent
   migration history exactly as before this change.
