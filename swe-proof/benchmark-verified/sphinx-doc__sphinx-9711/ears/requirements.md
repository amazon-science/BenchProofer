# Requirements: Numeric version comparison in `needs_extensions`

## Introduction

Sphinx lets a project declare minimum versions for the extensions it loads via
the `needs_extensions` configuration value. At startup Sphinx validates these
requirements in `sphinx.extension.verify_needs_extensions(app, config)`, which
is connected to the `config-inited` event and raises
`sphinx.errors.VersionRequirementError` when a loaded extension is older than
the declared minimum.

The defect is that the requirement check compares the required version string
against the loaded extension's version string using plain string (lexicographic)
comparison. Under string ordering `"0.10"` sorts **before** `"0.6"`, so a loaded
extension at version `0.10.0` is wrongly rejected against a minimum of `0.6.0`,
even though `0.10.0` is numerically newer. The goal is to make the check compare
versions by their numeric release components, so that a loaded version that is
numerically greater than or equal to the required version is accepted, while
preserving all existing behavior (unknown versions, missing extensions, empty or
unset configuration, and the error message and error type raised on genuine
shortfalls).

The affected module is `sphinx/extension.py`; the affected function is
`verify_needs_extensions`. The `Extension` object exposes the loaded version as
its `version` attribute, which is the sentinel string `"unknown version"` when
the extension did not report a version.

## Requirement 1: Compare extension versions numerically

**User story:** As a project maintainer, I want minimum-version requirements for
extensions to be interpreted as version numbers rather than as raw strings, so
that a newer extension release such as `0.10.0` is accepted when the required
minimum is `0.6.0`.

**Acceptance criteria**

1. WHEN `verify_needs_extensions` evaluates a required version and a loaded
   extension version that are both recognizable numeric version strings, THEN
   the function SHALL compare them by their numeric release components (each
   dotted component interpreted as an integer) rather than by lexicographic
   string order.
2. IF the loaded extension version is numerically greater than or equal to the
   required version, THEN `verify_needs_extensions` SHALL treat the requirement
   as fulfilled and SHALL NOT raise an error for that extension.
3. WHEN the required minimum is `0.6.0` (or `0.6`) and the loaded version is
   `0.10.0` (or `0.10`), THEN `verify_needs_extensions` SHALL treat the
   requirement as fulfilled and SHALL NOT raise an error, because `0.10.0` is
   numerically newer than `0.6.0`.
4. WHEN a loaded version whose leading numeric component is a multi-digit
   number that sorts before a smaller single-digit component under
   lexicographic string order is numerically greater than or equal to the
   required version, THEN `verify_needs_extensions` SHALL treat the requirement
   as fulfilled and SHALL NOT raise an error, even though a naive string
   comparison would reject it.
5. IF the loaded extension version is numerically less than the required
   version, THEN `verify_needs_extensions` SHALL treat the requirement as not
   fulfilled and SHALL raise `sphinx.errors.VersionRequirementError`.
6. WHEN two version strings differ only by trailing zero components (for
   example `1` versus `1.0`, or `0.6` versus `0.6.0`), THEN the numeric
   comparison SHALL treat the shorter form and the zero-padded longer form as
   equal.

## Requirement 2: Fall back to string comparison for unrecognizable versions

**User story:** As a maintainer whose extension reports a non-standard version
label, I want the check to degrade gracefully instead of crashing, so that a
version that cannot be parsed numerically is still handled.

**Acceptance criteria**

1. IF the required version string or the loaded version string cannot be parsed
   as a numeric version, THEN `verify_needs_extensions` SHALL fall back to
   comparing the two version strings with plain string (lexicographic) ordering
   to decide whether the requirement is fulfilled.
2. WHEN parsing a version string as a numeric version would raise an invalid
   version error, THEN `verify_needs_extensions` SHALL handle that condition and
   continue via the string-comparison fallback rather than propagating the
   parsing error.
3. WHILE using the string-comparison fallback, `verify_needs_extensions` SHALL
   treat the requirement as not fulfilled exactly when the required version
   string is lexicographically greater than the loaded version string.

## Requirement 3: Preserve unknown-version and error-reporting behavior

**User story:** As a maintainer, I want the existing failure behavior to remain
unchanged, so that missing version information and genuine version shortfalls
are still reported the same way.

**Acceptance criteria**

1. IF a loaded extension's reported version is the sentinel `"unknown version"`,
   THEN `verify_needs_extensions` SHALL treat the requirement as not fulfilled
   and SHALL raise `sphinx.errors.VersionRequirementError`, regardless of the
   required version string.
2. WHEN `verify_needs_extensions` raises for an unfulfilled requirement, THEN it
   SHALL raise `sphinx.errors.VersionRequirementError` and SHALL keep the
   existing message naming the extension, the required minimum version, and the
   loaded version.
3. The system SHALL evaluate each entry in `needs_extensions` independently and
   SHALL raise on the first extension whose requirement is not fulfilled.

## Requirement 4: Preserve configuration and missing-extension handling

**User story:** As a maintainer, I want unrelated startup behavior to be
unaffected, so that empty or unset configuration and unloaded extensions behave
as before.

**Acceptance criteria**

1. IF `needs_extensions` is unset (its value is `None`), THEN
   `verify_needs_extensions` SHALL return without raising and without inspecting
   any extensions.
2. WHEN `needs_extensions` is present but empty, THEN `verify_needs_extensions`
   SHALL complete successfully without raising.
3. IF an extension named in `needs_extensions` is not loaded, THEN
   `verify_needs_extensions` SHALL log a warning that the extension is required
   but not loaded, SHALL NOT raise for that entry, and SHALL continue checking
   the remaining entries.
4. The system SHALL keep `verify_needs_extensions` connected to the
   `config-inited` event so that requirement checking runs at configuration
   initialization time.
