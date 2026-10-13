# Requirements: Follow symlinked directories during collection traversal

## Introduction

pytest discovers test files by recursively walking a directory tree. The
directory-walking helper `visit` in `src/_pytest/pathlib.py` performs a
breadth-first traversal: at each directory level it lists the entries (sorted by
name), yields them, and then descends into each entry that is itself a directory
and that a caller-supplied `recurse` predicate selects. This walk is the traversal
consumed by the collection entry points (e.g. `Package.collect` in
`src/_pytest/python.py` and `Session` collection in `src/_pytest/main.py`).

A regression (introduced in pytest 6.1.0) caused the walk to treat a symbolic
link that points at a directory as if it were **not** a directory, so such
entries were listed but never descended into. As a result, tests living inside a
symlinked directory placed in a test tree were silently skipped rather than
collected and run. The goal is to restore the pre-6.1.0 behavior: an entry that
*resolves to* a directory must be recursed into whether or not the entry itself
is a symbolic link, while every other traversal property (ordering, breadth-first
emission, the `recurse` filter, and handling of non-directory entries) is
preserved.

The affected surface is the `visit` traversal helper in
`src/_pytest/pathlib.py` and, through it, the collection behavior observed by
users running pytest over a directory tree that contains symlinked
subdirectories.

## Requirement 1: Recurse into directories reached through a symbolic link

**User story:** As a user who organizes tests behind a symlinked directory, I
want pytest to follow that symlink and collect the tests inside it, so that my
tests are actually run instead of silently skipped.

**Acceptance criteria**
1. WHEN the traversal helper `visit` encounters an entry whose target is a
   directory and that the `recurse` predicate selects, THEN `visit` SHALL
   descend into that directory and continue the walk into its contents,
   regardless of whether the entry is itself a symbolic link.
2. WHEN a test-containing directory is reached only through a symbolic link that
   points to a directory, THEN pytest SHALL collect the test files inside the
   linked directory and execute the tests they contain.
3. IF a directory tree contains both a real test file at the top level and a
   symbolic link to a directory that also contains a test file, THEN pytest
   SHALL collect and run the tests from both locations (i.e. every reachable
   test is collected, not only the non-symlinked ones).
4. The decision of whether to descend into an entry SHALL depend on the entry's
   resolved target type (a directory versus a non-directory), not on whether the
   entry is a symbolic link.

## Requirement 2: Preserve the existing directory-walk contract

**User story:** As a pytest maintainer, I want the fix to change only the
symlink-following behavior, so that all other collection ordering and filtering
guarantees continue to hold.

**Acceptance criteria**
1. The system SHALL emit, at each directory level, that level's entries sorted in
   ascending order by entry name before descending into any subdirectory.
2. The system SHALL perform the walk breadth-first: all entries of a directory
   level are yielded before the contents of that level's subdirectories are
   emitted.
3. WHEN the caller-supplied `recurse` predicate does not select a directory
   entry, THEN `visit` SHALL NOT descend into that directory.
4. WHEN an entry does not resolve to a directory (for example a regular file),
   THEN `visit` SHALL yield that entry but SHALL NOT attempt to descend into it.
5. The system SHALL continue to yield every entry of the starting directory
   level exactly once, preserving the previously collected set of non-symlinked
   directories and files.

## Requirement 3: Keep pre-existing symlink and collection safeguards intact

**User story:** As a user relying on pytest's established collection rules, I
want the symlink fix to leave unrelated safeguards unchanged, so that no other
collection behavior regresses.

**Acceptance criteria**
1. The system SHALL keep collecting a test file that is passed as a symbolic-link
   argument on the command line.
2. WHEN a directory tree contains a symlink whose target lies outside the tree
   being collected, THEN pytest SHALL still collect tests through that link
   without error.
3. The system SHALL keep honoring directory-exclusion rules during traversal —
   including `norecursedirs`, virtual-environment detection, and
   `collect_ignore`/`collect_ignore_glob` — so that ignored directories remain
   uncollected even after symlink following is restored.
4. The system SHALL keep collecting nested real (non-symlinked) subdirectories
   with symlinks present, producing the same results as before for the
   non-symlinked portions of the tree.
