# Requirements: pastebin upload uses a language-neutral highlighter

## Introduction

pytest's `--pastebin` option (implemented in `src/_pytest/pastebin.py`) uploads
captured terminal output to the `bpaste.net` paste service via an HTTP form
POST. The helper `create_new_paste(contents)` assembles the form parameters,
performs the request, and returns a URL to the created paste.

Historically the request declared the pasted body's syntax-highlighting
language (`lexer`) as `"python3"` (or `"python"` under Python 2). Because the
uploaded content is an arbitrary pytest console session rather than source code
in any particular language, the paste service rejects some payloads with
"HTTP Error 400: Bad Request". The goal is to have `create_new_paste` request a
language-neutral plain-text highlighter so that arbitrary console output uploads
succeed, while preserving all other observable behavior of the paste helper and
of the surrounding `--pastebin` plugin (failed-only mode, all-output capture,
and non-ASCII handling).

## Requirement 1: Language-neutral highlighter for uploaded pastes

**User story:** As a pytest user uploading a captured session, I want the paste
to be submitted as plain text rather than as Python source, so that the paste
service accepts arbitrary console output instead of returning an HTTP 400 error.

**Acceptance criteria**

1. WHEN `create_new_paste` in `src/_pytest/pastebin.py` builds the form
   parameters for a paste request, THEN the helper SHALL set the highlighter
   language parameter to the plain-text value `text`.
2. The system SHALL request the plain-text highlighter value `text`
   irrespective of the running Python interpreter's major version (i.e. the
   language parameter SHALL NOT depend on whether Python 2 or Python 3 is in
   use).
3. WHEN the encoded request body produced by `create_new_paste` is inspected,
   THEN it SHALL contain the highlighter language parameter set to `text` and
   SHALL NOT declare any Python-specific highlighter language.

## Requirement 2: Complete and correct paste request contents

**User story:** As a maintainer, I want the paste request to carry exactly the
intended parameters and target, so that the upload behaves identically to before
apart from the corrected highlighter.

**Acceptance criteria**

1. WHEN `create_new_paste(contents)` builds the request, THEN it SHALL include a
   code parameter whose value is exactly the caller-supplied `contents`,
   unchanged.
2. WHEN `create_new_paste(contents)` builds the request, THEN it SHALL include
   an expiry parameter whose value is `1week`.
3. WHEN `create_new_paste` submits the request, THEN it SHALL send it to the
   target `https://bpaste.net`.
4. WHEN `create_new_paste` submits the request, THEN the request payload SHALL
   be the URL-encoding of the parameters encoded as ASCII bytes (i.e. the data
   passed to the underlying opener SHALL be of a bytes type, not text).
5. The request SHALL carry only the code, highlighter-language, and expiry
   parameters, with no additional parameters introduced and none removed.

## Requirement 3: Return value derived from the service response

**User story:** As a caller of the paste helper, I want a usable paste URL back,
so that the uploaded session can be located.

**Acceptance criteria**

1. WHEN the paste service response contains a raw-paste reference, THEN
   `create_new_paste` SHALL return the show-URL for that paste in the form
   `https://bpaste.net/show/<id>`, where `<id>` is the identifier extracted from
   the response.
2. IF the response does not contain a recognizable raw-paste reference, THEN
   `create_new_paste` SHALL NOT return a show-URL of the form
   `https://bpaste.net/show/<id>`; the raw-paste show-URL is returned only in the
   case where the response contains a raw-paste reference.

## Requirement 4: Preserve failed-only pastebin mode

**User story:** As a user running with `--pastebin=failed`, I want only failure
information uploaded, so that the existing failed-mode behavior is unchanged.

**Acceptance criteria**

1. WHILE the `--pastebin` option is set to `failed` and at least one test has
   failed, the pastebin plugin SHALL upload paste content for the failures via
   the paste helper.
2. WHEN operating in failed-only mode over a session containing a passing, a
   failing, and a skipped test, THEN the plugin SHALL invoke the paste helper
   exactly once and the uploaded content SHALL include the failing test's
   representation.
3. IF the `--pastebin` option is not set to `failed`, THEN the failed-only
   terminal-summary path SHALL NOT upload any paste.

## Requirement 5: Preserve all-output pastebin capture

**User story:** As a user running with `--pastebin=all`, I want the complete
terminal session captured and uploaded once, so that the full-session capture
behavior is unchanged.

**Acceptance criteria**

1. WHILE the `--pastebin` option is set to `all`, the plugin SHALL tee the
   terminal reporter's written output into a buffer and, at session end, SHALL
   upload the accumulated session log exactly once via the paste helper.
2. WHEN a session run with all-output mode contains a passing, a failing, and a
   skipped test, THEN the uploaded content SHALL reflect each of those outcomes
   and SHALL include the final summary line reporting the failed, passed, and
   skipped counts.
3. WHEN all-output capture is active, THEN the plugin SHALL emit a separator and
   a line reporting the resulting paste URL to the terminal.

## Requirement 6: Preserve non-ASCII paste handling

**User story:** As a user whose test output contains non-ASCII characters, I
want that output uploaded without error, so that international text is handled
correctly.

**Acceptance criteria**

1. WHEN captured terminal output contains non-ASCII characters, THEN the plugin
   SHALL encode the buffered session as UTF-8 bytes before upload so that the
   non-ASCII content is preserved.
2. WHEN a session whose output includes non-ASCII characters is uploaded, THEN
   the run SHALL complete without error and SHALL report that information is
   being sent to the paste service.
