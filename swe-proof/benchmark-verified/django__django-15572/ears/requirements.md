# Requirements: Ignore empty template directory entries in the autoreload watcher

## Introduction

Django's development autoreloader watches the directories configured for the
Django template engine so that editing a template triggers a reload. The
collection of watched directories is produced by
`get_template_directories()` in `django/template/autoreload.py`, which gathers
entries from two sources for every `DjangoTemplates` backend:

1. the engine's configured directories (`backend.engine.dirs`), and
2. the directories reported by each template loader that exposes a `get_dirs()`
   method (`loader.get_dirs()`).

Each raw entry is turned into an absolute path by joining it (via `to_path`)
onto the current working directory (`Path.cwd()`), and the results are stored in
a `set`.

Since the change that normalizes directory entries with `pathlib.Path`, an
empty-string entry (which arises easily from configuration such as
`os.getenv("TEMPLATES_DIRS", "").split(",")` yielding `[""]`) no longer stays
distinct: joining an empty string onto the current working directory normalizes
to the project root. Because `template_changed()` (also in
`django/template/autoreload.py`) resets the loaders and reports a change
whenever a changed file lives under any watched directory, a watched project
root causes every source-file change to look like a template change, and
autoreload effectively stops working.

The goal is to make `get_template_directories()` ignore empty directory entries
from both sources while preserving all existing directory-collection behavior,
so that a stray empty entry contributes nothing to the watched set.

## Requirement 1: Empty configured directory entries contribute nothing

**User story:** As a Django developer whose settings can produce an empty string
in a template engine's `DIRS`, I want that empty entry to be ignored by the
autoreload directory collector, so that the project root is never watched and
autoreload keeps working.

**Acceptance criteria**

1. WHEN `get_template_directories()` iterates a `DjangoTemplates` backend whose
   `engine.dirs` contains an empty-string entry, THEN `get_template_directories()`
   SHALL NOT add any path derived from that empty entry to the returned set.
2. WHEN `get_template_directories()` iterates a template loader whose
   `get_dirs()` returns an empty-string entry, THEN
   `get_template_directories()` SHALL NOT add any path derived from that empty
   entry to the returned set.
3. IF the only directory entries available across all `DjangoTemplates`
   backends and their loaders are empty strings, THEN
   `get_template_directories()` SHALL return an empty set.
4. The system SHALL treat an empty directory entry as absent regardless of its
   source, so that no empty entry is ever normalized into the current working
   directory (project root) and added to the watched set.

## Requirement 2: Preserve collection of valid directory entries

**User story:** As a Django developer relying on template autoreload, I want all
genuinely configured template directories to continue being collected and
watched, so that editing a real template still triggers a reload.

**Acceptance criteria**

1. WHEN `get_template_directories()` processes a `DjangoTemplates` backend, THEN
   it SHALL include, for each non-empty entry in `backend.engine.dirs`, the
   absolute path formed by joining that entry onto the current working directory.
2. WHEN `get_template_directories()` processes a template loader that exposes a
   `get_dirs()` method, THEN it SHALL include, for each non-empty directory the
   loader reports that is not inside the framework's own tree, the absolute path
   formed by joining that directory onto the current working directory.
3. The system SHALL keep excluding loader-reported directories that lie inside
   the framework's own path from the returned set.
4. The system SHALL keep skipping any backend that is not a `DjangoTemplates`
   backend and any loader that does not provide a `get_dirs()` method.
5. The system SHALL return the collected directories as a set, so that ordering
   and duplicate entries are not observable in the result.
6. WHEN directory entries are provided as strings or path-like values, THEN
   `get_template_directories()` SHALL return them normalized to absolute path
   objects joined onto the current working directory.

## Requirement 3: Preserve change-detection and loader-reset behavior

**User story:** As a Django developer, I want the autoreloader's watch,
change-detection, and loader-reset behavior to remain unchanged aside from the
empty-entry fix, so that existing reload behavior is not regressed.

**Acceptance criteria**

1. WHEN autoreload starts, THEN the watcher SHALL request watching of every
   directory returned by `get_template_directories()`.
2. WHEN a changed file has a `.py` suffix, THEN the template change handler
   SHALL NOT report a template change and SHALL NOT reset the loaders.
3. WHEN a changed non-Python file resides under one of the collected template
   directories, THEN the template change handler SHALL reset the template
   loaders and report that a template change occurred.
4. WHEN a changed non-Python file does not reside under any collected template
   directory, THEN the template change handler SHALL NOT report a template
   change.
5. WHEN the loaders are reset, THEN each template loader of every
   `DjangoTemplates` backend SHALL have its reset behavior invoked.
