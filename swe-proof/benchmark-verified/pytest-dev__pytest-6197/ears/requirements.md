# Requirements — Lazy underlying-object access during test-package collection

## Introduction

pytest's Python collection layer (`src/_pytest/python.py`) builds a tree of
collector nodes. Package directories (those containing an `__init__.py`) are
represented by the `Package` collector; individual `.py` files by the `Module`
collector. Every Python collector node derives from `PyobjMixin`, which exposes
the underlying imported Python object through its `obj` property.

A regression was introduced in which enumerating the contents of a package
eagerly imported the package's own `__init__.py` **before** walking the
directory. As a result, running pytest over a tree that merely *contains* a
package whose `__init__.py` has import-time side effects (an `assert`, a
platform-specific import that fails, `sys.path` mutation, etc.) would import
that file even when it holds no tests being collected — turning an unrelated,
uncollected package into a collection error or an unexpected import.

The goal is to make access to a collector's underlying Python object **lazy**
again: the object is imported only when it is actually needed, and enumerating a
package's directory contents must not, by itself, import that package's own
`__init__.py`. This must be achieved without regressing legitimate collection of
packages and init modules that genuinely contain tests.

The affected code is entirely in `src/_pytest/python.py`: the `PyobjMixin.obj`
property and its lazy-mount helper, the `Module` collector's construction, and
the `Package.collect` enumeration routine.

## Requirement 1: Enumerating a package's contents must not import its own `__init__.py`

**User story:** As a developer whose project tree contains a package that
cannot (or must not) be imported in the current environment, I want pytest to
walk that package's directory without importing the package itself, so that an
uncollected package never breaks or perturbs my test run.

**Acceptance criteria**

1. WHEN the `Package` collector enumerates the contents of its directory, THEN
   the collection routine SHALL NOT trigger an import of the package's own
   `__init__.py` as a side effect of the enumeration itself.
2. WHEN pytest is run over a directory tree that contains a sub-package whose
   `__init__.py` raises an exception at import time (for example, a failing
   assertion), and no test inside that sub-package is selected for collection,
   THEN the session SHALL complete successfully with an all-tests-passed exit
   status and SHALL NOT report a collection error for that `__init__.py`.
3. The system SHALL defer importing a package's `__init__.py` until the object
   is genuinely required (for example, to run package-level setup or to resolve
   a collected test within it), rather than importing it unconditionally while
   listing directory entries.

## Requirement 2: A collector's underlying Python object is mounted lazily and only once

**User story:** As a maintainer of pytest's collection internals, I want the
underlying Python object of a collector node to be imported on first access
rather than at node construction or during unrelated traversal, so that no
object is imported earlier than necessary while preserving marker semantics.

**Acceptance criteria**

1. WHEN a Python collector node is constructed, THEN the node SHALL NOT import
   or otherwise resolve its underlying Python object as part of construction.
2. WHEN the `obj` property of a Python collector node is read for the first
   time, THEN the node SHALL resolve and cache the underlying object, and every
   subsequent read SHALL return the same cached object without re-importing it.
3. WHEN a value is assigned to the `obj` property of a collector node, THEN
   subsequent reads of `obj` SHALL return that assigned value.
4. WHEN a collector node's underlying object is resolved for the first time and
   the node participates in marker collection, THEN the marks unpacked from that
   object SHALL be added to the node's own markers exactly once (no duplication
   across repeated `obj` access).

## Requirement 3: `src`-style directories are not placed on the import path by collection

**User story:** As a developer with a `src/` layout that is intentionally not on
`sys.path`, I want pytest's collection to leave the import path unchanged for
packages it merely traverses, so that modules under `src/` do not become
importable as a side effect of running pytest.

**Acceptance criteria**

1. WHEN pytest runs over a tree containing a package directory that is not on
   `sys.path` (for example `src/<pkg>/__init__.py`) and no test within that
   package is collected, THEN pytest SHALL NOT insert that directory onto
   `sys.path` and SHALL NOT make that package importable.
2. IF a test executed during such a run attempts to import a module that lives
   only under such an un-collected, off-path directory, THEN that import SHALL
   fail with an `ImportError`, and the run SHALL still complete with an
   all-tests-passed exit status.

## Requirement 4: Legitimate collection of packages and init modules is preserved

**User story:** As a user who organizes real tests inside packages and init
files, I want packages, sub-packages, and test-bearing `__init__.py` files to
still be discovered and collected, so that making object access lazy does not
lose any tests.

**Acceptance criteria**

1. WHEN a `Package` collector enumerates its directory and the package's own
   `__init__.py` matches the configured test-file pattern, THEN the collection
   SHALL yield a module collector for that `__init__.py` before the package's
   other contents.
2. WHEN a package directory is passed as an initial collection argument (whether
   as the package directory, its `__init__.py`, or together with another file in
   the package), THEN pytest SHALL still collect the tests contained in that
   package as it did before this change.
3. WHEN a package legitimately contains test modules and sub-packages, THEN
   enumerating the package SHALL still discover those test files and recurse
   into those sub-packages, skipping only the package's own `__init__.py` entry
   and paths already accounted for under a nested sub-package.
4. The system SHALL preserve the existing behavior of all other collection
   operations — file resolution, directory recursion decisions, ignore/norecurse
   handling, and duplicate-path handling — so that only the timing of underlying
   object import changes, not which items are ultimately collected.

## Requirement 5: Marker evaluation follows the lazy-import boundary

**User story:** As a user relying on skip and xfail markers, I want the markers
that are actually collected from imported test modules to evaluate and report as
before, while understanding that a marker declared in a package's `__init__.py`
is only applied once that `__init__.py` is imported — which no longer happens
while the package's directory is merely enumerated — so that the change to when
objects are imported no longer reliably applies a package-level marker to the
sibling tests in that package.

**Acceptance criteria**

1. WHEN a skip or xfail marker (conditional or unconditional) is applied to a
   test function or class within a module that is imported during collection,
   THEN the system SHALL evaluate and report that marker's outcome exactly as it
   did prior to this change.
2. WHEN a package's `__init__.py` declares a module-level marker (for example a
   package-wide skip) and that `__init__.py` is no longer imported while the
   package's directory contents are enumerated, THEN that package-level marker
   SHALL NOT be reliably propagated to all of the sibling tests collected from
   that package: at least one such sibling test that the previous eager-import
   behavior would have skipped SHALL instead be collected and executed — able to
   pass or fail on its own — rather than being skipped by the package-level
   marker. (The change removes the guarantee that a package-wide `__init__.py`
   marker uniformly skips every sibling test; whether any given later-collected
   sibling still observes the marker is no longer guaranteed.)
3. WHEN `pytest.importorskip` is called for a module that cannot be imported,
   THEN it SHALL raise the same skip/import outcome as before, and its behavior
   SHALL be unchanged for importable modules.
