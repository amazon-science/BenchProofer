# Requirements: Guard the working-directory removal in `modify_sys_path`

## Introduction

When pylint is executed as a Python module, the `modify_sys_path` function in
`pylint/__init__.py` sanitizes `sys.path` so that the current working directory
cannot shadow standard-library or pylint-internal modules of the same name.

Historically the function unconditionally removed the *first* entry of
`sys.path` (`sys.path.pop(0)`), on the assumption that the first entry is always
either the empty string `""` or the working directory. That assumption is wrong
when a caller has already inserted its own entry at the front of `sys.path`
before pylint runs — for example when pylint is launched via `runpy.run_module`
after `sys.path.insert(0, "something")`, or by an editor extension that bundles
its libraries and prepends them to `sys.path`. In those cases the function
discarded a legitimate, caller-supplied path entry, breaking imports.

The goal is to remove the first entry only when it genuinely denotes the working
directory (it is `""`, `"."`, or `os.getcwd()`), and otherwise leave it in
place, while keeping every other aspect of the existing path-sanitization
behavior unchanged. The affected function is the `modify_sys_path` function in
`pylint/__init__.py`.

## Requirement 1: Remove a leading working-directory entry

**User story:** As a developer relying on pylint's module-execution safety, I
want the working directory removed from the front of `sys.path`, so that local
files cannot shadow standard-library or pylint modules.

**Acceptance criteria**

1. WHEN the `modify_sys_path` function runs and the first entry of `sys.path` is the empty
   string `""`, THEN the function SHALL remove that first entry from `sys.path`.
2. WHEN the `modify_sys_path` function runs and the first entry of `sys.path` is `"."`,
   THEN the function SHALL remove that first entry from `sys.path`.
3. WHEN the `modify_sys_path` function runs and the first entry of `sys.path` is exactly the
   current working directory as returned by `os.getcwd()`, THEN the function
   SHALL remove that first entry from `sys.path`.
4. WHEN the first entry is removed under criteria 1–3, THEN the function SHALL
   preserve all remaining entries of `sys.path` in their original relative
   order.

## Requirement 2: Preserve a leading non-working-directory entry

**User story:** As a developer or tooling author who prepends a custom path to
`sys.path` before invoking pylint programmatically, I want that entry kept, so
that my bundled libraries and modules remain importable.

**Acceptance criteria**

1. IF the first entry of `sys.path` is not `""`, not `"."`, and not equal to
   `os.getcwd()`, THEN the `modify_sys_path` function SHALL leave that first entry in place
   and SHALL NOT remove it.
2. WHEN the first entry is a caller-supplied location that is not the working
   directory, THEN the `modify_sys_path` function SHALL NOT reduce the number of entries on
   account of the first-entry rule.
3. The decision to remove the first entry SHALL depend only on whether that
   entry denotes the working directory, and SHALL NOT depend on the entry's
   position count alone.

## Requirement 3: Preserve the existing PYTHONPATH-based sanitization

**User story:** As a maintainer, I want the previously implemented handling of a
`PYTHONPATH` environment variable with a leading or trailing separator to keep
working exactly as before, so that this change fixes only the first-entry
behavior and introduces no regression.

**Acceptance criteria**

1. WHILE the `PYTHONPATH` environment string starts with a `":"` and is neither
   exactly `":" + os.getcwd()` nor `":."`, the `modify_sys_path` function SHALL remove one
   further entry from the front of the (already first-entry-adjusted) `sys.path`.
2. WHILE the `PYTHONPATH` environment string ends with a `":"` and is neither
   exactly `os.getcwd() + ":"` nor `".:"`, and the leading-colon condition of
   criterion 1 does not apply, the `modify_sys_path` function SHALL remove the entry now in
   second position of the (already first-entry-adjusted) `sys.path`.
3. IF the `PYTHONPATH` environment string neither begins nor ends with a bare
   working-directory-implying `":"` per criteria 1–2, THEN the `modify_sys_path` function
   SHALL apply no further removal beyond the first-entry rule.
4. The leading-colon and trailing-colon adjustments SHALL be mutually exclusive,
   and the chosen adjustment SHALL be applied to `sys.path` as it stands after
   the first-entry rule of Requirements 1 and 2 has been evaluated.
5. WHEN `PYTHONPATH` contains the working directory or `"."` as its sole content
   with a separator (i.e. the excepted forms named in criteria 1–2), THEN
   the `modify_sys_path` function SHALL NOT perform the corresponding extra removal.
