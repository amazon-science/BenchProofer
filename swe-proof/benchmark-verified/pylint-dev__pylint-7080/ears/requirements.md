# Requirements: `ignore-paths` honored during recursive checking

## Introduction

When pylint is run recursively (the `--recursive=y` option), it walks the target
directories and decides, for each discovered path, whether that path should be
skipped according to the user's ignore configuration (`ignore`,
`ignore-patterns`, and `ignore-paths`). The decision is made by the helper
`pylint.lint.expand_modules._is_ignored_file(element, ignore_list,
ignore_list_re, ignore_list_paths_re)`, which is consulted both when expanding
the modules to check and from the recursive directory discovery in
`pylint.lint.pylinter.PyLinter._discover_files` (the `os.walk` loop that skips
ignored subtrees).

The bug: when the recursion target is the current directory (e.g. running
`pylint --recursive=y .`), the paths handed to `_is_ignored_file` carry a
leading `./` (or other non-canonical separators/segments). A user-supplied
`ignore-paths` regular expression (for example `^src/gen/.*$`, as reported in
the issue) is written against the canonical path form and therefore fails to
match the `./`-prefixed path, so the subtree is *not* skipped and files under
it are wrongly checked.

The goal is to make the ignore decision operate on the filesystem-normalized
form of the path element so that non-canonical spellings of a path (a leading
`./`, redundant separators, `.`/`..` segments) match an `ignore-paths` /
`ignore-patterns` / `ignore` entry exactly as their canonical form would, while
leaving every other aspect of the ignore decision unchanged. The change is
localized to `_is_ignored_file`.

## Requirement 1: Normalize the path element before deciding to ignore it

**User story:** As a developer running pylint recursively from a directory, I
want my `ignore-paths` settings to apply regardless of how the target path is
spelled, so that auto-generated or vendored subtrees are excluded even when the
scan is launched from the current directory.

**Acceptance criteria**
1. WHEN `_is_ignored_file` is called with a path `element`, THEN it SHALL first
   replace `element` with its filesystem-normalized form (collapsing redundant
   separators and `.`/`..` segments and removing a leading `./`) before
   performing any of the ignore checks.
2. WHEN the normalized form of the path element matches one of the
   `ignore_list_paths_re` path patterns, THEN `_is_ignored_file` SHALL return
   `True`, even if the original un-normalized spelling of the element would not
   have matched that pattern.
3. WHEN the path element differs from its normalized form only by a leading
   `./` prefix, redundant separators, or `.`/`..` segments, THEN the ignore
   decision returned by `_is_ignored_file` SHALL be identical to the decision it
   would return for the already-normalized element.
4. The system SHALL derive the basename used for the literal-name and
   name-pattern checks from the normalized element (its final path component),
   not from the raw element.

## Requirement 2: Preserve the existing three-way ignore decision

**User story:** As a maintainer, I want the normalization to add the missing
canonicalization without changing which entries cause a path to be ignored, so
that existing ignore behavior is unaffected.

**Acceptance criteria**
1. WHEN the final path component of the normalized element is a member of the
   literal ignore list, THEN `_is_ignored_file` SHALL return `True`.
2. WHEN the final path component of the normalized element matches one of the
   name patterns (`ignore_list_re`), THEN `_is_ignored_file` SHALL return `True`.
3. IF none of the three conditions holds — the final component is not in the
   literal ignore list, the final component matches no name pattern, and the
   normalized element matches no path pattern — THEN `_is_ignored_file` SHALL
   return `False`.
4. The system SHALL treat the result as the logical OR of exactly those three
   checks (literal-name membership, name-pattern match, path-pattern match), and
   SHALL introduce no additional reason to ignore or to check a path.
5. WHEN a path pattern or name pattern is matched, THEN the match SHALL be
   evaluated as an anchored match at the start of the (respective) string, as
   before.

## Requirement 3: Honor ignore configuration during recursive discovery

**User story:** As a developer, I want recursively-discovered directories that
match my ignore configuration to be pruned from the scan, so that no messages
are emitted for files inside an ignored subtree.

**Acceptance criteria**
1. WHILE walking a target directory recursively, WHEN a discovered directory
   root is reported as ignored by `_is_ignored_file`, THEN the recursive
   discovery SHALL skip that root and all of its descendant files and
   subdirectories.
2. WHEN pylint is invoked recursively on the current directory with an
   `ignore-paths` entry that matches a subdirectory (relative to that current
   directory), THEN pylint SHALL emit no messages for files within that
   subdirectory and SHALL exit with a success (zero) status.
3. WHEN pylint is invoked recursively on a named directory (rather than the
   current directory) with an `ignore-paths` entry matching a subdirectory,
   THEN that subdirectory SHALL likewise be excluded — this previously-working
   case SHALL continue to work unchanged.

## Requirement 4: Preserve recursive checking of non-ignored files

**User story:** As a developer, I want ordinary recursive checking to be
unaffected by the normalization, so that files that are not ignored are still
discovered and checked.

**Acceptance criteria**
1. WHEN pylint is run recursively over a directory tree, THEN every discovered
   `.py` file whose path is not ignored SHALL still be collected for checking.
2. The system SHALL continue to honor `ignore`, `ignore-patterns`, and
   `ignore-paths` in the recursive mode for both the current-directory and the
   named-directory invocations, with the only behavioral change being the added
   path normalization described in Requirement 1.
