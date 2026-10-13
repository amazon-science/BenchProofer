# Requirements: preserve path letter-case when caching loaded conftest modules

## Introduction

pytest discovers and loads per-directory `conftest.py` hook files through the
plugin manager in `src/_pytest/config/__init__.py`. To avoid importing the same
`conftest.py` twice (for example when a build system exposes a file through
several symlinked routes), the manager caches each loaded conftest module in an
internal mapping keyed by a canonicalized form of the conftest file's path
(`PytestPluginManager._importconftest`). It also walks parent directories to
locate applicable conftest files (`PytestPluginManager._getconftestmodules`)
and records an optional "confcutdir" boundary
(`PytestPluginManager._set_initial_conftests`).

The defect: the canonicalization step used to build these path values folded
the path's letter case to lower case (it applied case normalization on top of
symlink resolution, via a helper in `src/_pytest/pathlib.py`). On
case-insensitive but case-preserving file systems (e.g. Windows) this produced a
key that no longer matched the file's true on-disk casing. Because the module's
qualified (dotted) name is later derived from that path, a package or directory
whose name contains upper-case characters got an incorrectly lower-cased name,
raising an `ImportError`/`ModuleNotFoundError` while loading the conftest.

The goal is to make the conftest path canonicalization preserve the original
letter case: resolve the path (make it absolute and resolve symlinks) but never
fold it to lower case. The cache key must be a resolved, case-preserving path
value so that a conftest whose qualified name contains upper-case characters
loads successfully, while the existing symlink-deduplication and confcutdir
behavior is retained.

## Requirement 1: Preserve letter case when canonicalizing conftest paths

**User story:** As a developer running pytest on a case-insensitive,
case-preserving file system with directories/packages that contain upper-case
letters, I want conftest files to load correctly, so that collection does not
fail with a spurious import error caused by a lower-cased path.

**Acceptance criteria**

1. WHEN pytest canonicalizes a conftest file path for de-duplication in
   `_importconftest`, THEN the resulting value SHALL preserve the original
   letter case of the resolved path and SHALL NOT fold any character to lower
   case.
2. WHEN pytest resolves the directory path used to walk parent directories in
   `_getconftestmodules`, THEN it SHALL preserve the original letter case of
   that path and SHALL NOT fold it to lower case.
3. WHEN pytest records the confcutdir boundary in `_set_initial_conftests`,
   THEN the stored boundary value SHALL preserve the original letter case of
   the supplied directory and SHALL NOT fold it to lower case.
4. WHEN a `conftest.py` is loaded from a directory whose qualified (dotted)
   package name contains upper-case characters, THEN pytest SHALL import it
   using the correctly-cased qualified name and SHALL NOT raise an import error
   arising from a lower-cased path.
5. WHEN a session collects such an uppercase-named tree that contains no test
   items, THEN pytest SHALL finish collection reporting that no tests were
   collected rather than terminating with a conftest import error.

## Requirement 2: Keep symlink-based de-duplication of conftest modules

**User story:** As a developer whose build system exposes source files through
symlinks, I want each `conftest.py` to be imported only once, so that hook
registration is not duplicated when the same file is reached by different
routes.

**Acceptance criteria**

1. The canonicalization used to build the conftest cache key SHALL resolve
   symbolic links and make the path absolute, so that two paths referring to
   the same physical file produce the same key.
2. WHEN the same physical `conftest.py` is encountered again through a symlinked
   or otherwise aliased path, THEN `_importconftest` SHALL return the already
   loaded module from its cache instead of importing the file a second time.
3. WHEN parent directories are traversed by `_getconftestmodules` to locate
   applicable conftest files, THEN the traversal SHALL operate over the
   symlink-resolved directory path.

## Requirement 3: Cache key identity for locating loaded conftest modules

**User story:** As a maintainer relying on the plugin manager's internal
conftest cache, I want the cache to be keyed by the resolved, case-preserving
path, so that a loaded conftest can be found again using that same resolved
path.

**Acceptance criteria**

1. WHEN a `conftest.py` is loaded, THEN its module SHALL be stored in the
   conftest cache under a key equal to the file's resolved (absolute,
   symlink-resolved) path with letter case preserved.
2. IF the resolved, case-preserving path of a loaded conftest file is used to
   look it up, THEN that key SHALL be present in the conftest cache.
3. WHEN a directory contains no `conftest.py` (for example an ordinary
   non-conftest subdirectory), THEN no entry SHALL be added to the conftest
   cache for it, and the resolved path of a would-be conftest under such a
   directory SHALL NOT be present in the cache.
4. WHEN exactly one applicable `conftest.py` is discovered for a target
   directory, THEN the conftest cache SHALL contain exactly one entry.

## Requirement 4: Preserve confcutdir and directory-walk semantics

**User story:** As a developer using `--confcutdir`, I want conftest discovery
to keep respecting the cut-off directory and to report loaded modules from the
expected files, so that changing the path canonicalization does not alter which
conftests are applied.

**Acceptance criteria**

1. WHEN a confcutdir boundary is configured, THEN `_getconftestmodules` SHALL
   skip parent directories at or above that boundary and SHALL only import
   `conftest.py` files at or below it.
2. WHEN a conftest module is loaded for a directory, THEN the file backing the
   returned module SHALL be the `conftest.py` at the expected resolved,
   case-preserving location.
3. The system SHALL keep loading each applicable per-directory `conftest.py`
   exactly once for a given target path and SHALL continue to associate loaded
   modules with the correct directories.
4. The system SHALL preserve existing conftest discovery behavior for symlinked
   conftest files and for confcutdir-scoped subdirectories, with no change other
   than the letter-case preservation described in Requirement 1.
