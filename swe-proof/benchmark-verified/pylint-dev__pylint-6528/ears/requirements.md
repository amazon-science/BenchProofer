# Recursive discovery must honour ignore settings

## Introduction

When pylint is run with recursive mode enabled (`--recursive=y`), it walks a
directory tree to discover the Python modules and packages to lint. In this
mode the file/directory discovery step (`PyLinter._discover_files` in
`pylint/lint/pylinter.py`) walks the tree with `os.walk` but does **not**
consult the `--ignore`, `--ignore-patterns`, or `--ignore-paths` configuration
options. As a result, files and directories that the user explicitly asked to
skip — and directories that match the default ignore settings — are still
linted. This contradicts the documented behaviour of the ignore options and
undermines recursive mode.

The goal is to make recursive discovery respect all three ignore settings while
traversing the tree, pruning ignored directories (and everything beneath them)
so they never reach the linter, while leaving non-ignored modules and packages
discovered exactly as before. The same three-part ignore decision already used
by the flat expansion path (`expand_modules` in
`pylint/lint/expand_modules.py`) should govern discovery, so that both entry
points apply one consistent rule.

The affected modules are `pylint/lint/pylinter.py` (the recursive discovery
walk) and `pylint/lint/expand_modules.py` (the ignore-decision logic shared by
both paths).

## Requirement 1: Shared ignore decision for a single path

**User story:** As a pylint user, I want one consistent rule that decides
whether a given file or directory is ignored, so that every code path that
discovers files applies the ignore options the same way the documentation
describes.

**Acceptance criteria**

1. The system SHALL provide a reusable predicate that, given a path together
   with the plain ignore list, the base-name ignore-pattern list, and the
   path ignore-pattern list, decides whether that path is ignored.
2. WHEN the predicate is evaluated for a path, THEN the system SHALL report the
   path as ignored IF the path's base name (its final component) is present in
   the plain ignore list.
3. WHEN the predicate is evaluated for a path, THEN the system SHALL report the
   path as ignored IF the path's base name matches any of the base-name ignore
   patterns.
4. WHEN the predicate is evaluated for a path, THEN the system SHALL report the
   path as ignored IF the whole path matches any of the path ignore patterns.
5. IF none of the three conditions in criteria 2–4 hold, THEN the predicate
   SHALL report the path as not ignored.
6. The system SHALL match ignore patterns using the same anchored,
   start-of-string matching semantics already used for the ignore options
   (equivalent to the standard `re` module's `match`), matching base-name
   patterns against the base name and path patterns against the full path.

## Requirement 2: Recursive discovery skips ignored directories and their subtrees

**User story:** As a pylint user running recursive mode, I want ignored
directories to be excluded from linting, so that files inside them are never
reported.

**Acceptance criteria**

1. WHILE walking a directory tree in recursive discovery, WHEN a visited
   directory is reported as ignored by the shared ignore decision (evaluated
   against the configured plain ignore list, base-name ignore patterns, and
   path ignore patterns), THEN the system SHALL exclude that directory from the
   discovered results.
2. WHEN a visited directory is ignored, THEN the system SHALL also exclude every
   file and subdirectory located beneath that directory from the discovered
   results.
3. WHEN a visited directory is ignored, THEN the system SHALL neither yield the
   directory itself nor descend into it as a package.
4. The system SHALL evaluate the ignore decision for a discovered directory
   against that directory's own path (and its base name), so that a directory
   ignored by name, by base-name pattern, or by full-path pattern is pruned.
5. WHEN a `--recursive=y` run targets a directory tree that contains an ignored
   subdirectory holding files that would otherwise raise lint messages, THEN
   the system SHALL complete successfully with a zero (no-error) exit status
   because the offending files were skipped.

## Requirement 3: Non-ignored modules and packages are still discovered

**User story:** As a pylint user, I want recursive mode to keep finding all the
modules and packages I did not ignore, so that adding ignore settings does not
silently drop legitimate files.

**Acceptance criteria**

1. WHILE walking a directory tree in recursive discovery, WHEN a visited
   directory is not ignored and directly contains an `__init__.py` file, THEN
   the system SHALL record that directory as a discovered package and SHALL not
   descend further into its subtree.
2. WHILE walking a directory tree in recursive discovery, WHEN a visited
   directory is not ignored and does not directly contain an `__init__.py`
   file, THEN the system SHALL record each of its directly-contained files whose
   name ends with `.py`, by full path.
3. WHEN discovery visits a subtree already pruned because an enclosing package
   was recorded, THEN the system SHALL skip that subtree.
4. The system SHALL keep discovering every non-ignored Python module and
   package under the target tree — including modules nested in subdirectories,
   sub-subdirectories, packages, and subpackages — so that a run that ignores
   one subtree still lints all other modules.
5. IF a supplied target is a single file or a directory that itself directly
   contains an `__init__.py`, THEN recursive discovery SHALL yield that target
   unchanged, preserving the pre-existing handling of such inputs.

## Requirement 4: Flat expansion behaviour is preserved

**User story:** As a maintainer, I want the existing non-recursive expansion of
files and modules to keep behaving as before after the ignore decision is
factored out, so that refactoring the ignore logic does not change results.

**Acceptance criteria**

1. WHEN expanding an explicitly supplied list of files or modules, THEN the
   system SHALL skip any entry whose base name is in the plain ignore list,
   whose base name matches a base-name ignore pattern, or whose full path
   matches a path ignore pattern.
2. The system SHALL continue to expand and return the file/module descriptions
   for every supplied entry that is not ignored, unchanged from prior behaviour.
3. The system SHALL apply the same ignore decision defined in Requirement 1 in
   both the recursive discovery path and the flat expansion path, so that the
   two paths agree on whether any given path is ignored.
