# Requirements: CheckboxInput must not mutate the caller's attrs dict

## Introduction

`django.forms.widgets.CheckboxInput` is the widget used to render an HTML
checkbox. When it decides that a checkbox should be rendered as checked, it
needs the resulting HTML element to carry a `checked` attribute. It makes this
decision through its `check_test` callable (defaulting to the module-level
`boolean_check`, which treats a value as "on" unless the value is `False`,
`None`, or the empty string).

There is a defect in `CheckboxInput.get_context(self, name, value, attrs)`.
When the value is considered checked, the method adds the `checked` flag by
mutating in place the very `attrs` dictionary that the caller passed in. Every
other widget's `get_context` treats the incoming `attrs` as read-only;
`CheckboxInput` is the only one that writes back into it. This is a problem for
callers that reuse a single `attrs` dictionary across several widgets — for
example `SplitArrayField`/`SplitArrayWidget` rendering one BooleanField per
element of an array. Once such a caller renders one checked value, the shared
dictionary keeps the `checked` flag, so every subsequent widget built from that
same dictionary is rendered as checked even when its own backing value is
false.

The goal is to make `CheckboxInput.get_context` compute the `checked` flag
without modifying the dictionary object it received, so that a caller may safely
reuse one `attrs` dictionary across many renders. The affected module is
`django/forms/widgets.py`; the behavior is observed through
`CheckboxInput.get_context` and the rendered checkbox HTML, and none of the
widget's other public behaviors may change.

## Requirement 1: get_context must not mutate the caller's attrs dictionary

**User story:** As a developer rendering many checkboxes from one shared set of
attributes, I want `CheckboxInput.get_context` to leave my attributes
dictionary untouched, so that rendering a checked value does not make later
widgets spuriously appear checked.

**Acceptance criteria**

1. WHEN `CheckboxInput.get_context` is called with a non-`None` `attrs`
   dictionary and the widget's `check_test` reports the value as checked, THEN
   the system SHALL NOT add, remove, or alter any key of the dictionary object
   that was passed in as `attrs` (in particular it SHALL NOT insert a `checked`
   key into that caller-owned dictionary).
2. WHEN `CheckboxInput.get_context` is called and `check_test` reports the value
   as checked, THEN the system SHALL still make the resulting context reflect a
   checked checkbox — i.e. the attributes carried by the returned context SHALL
   include `checked` set to `True` — by using a dictionary distinct from the
   caller's `attrs` object.
3. WHEN the same `attrs` dictionary object is reused across successive
   `get_context` calls for a mix of checked and unchecked values, THEN each
   call's result SHALL reflect only its own value's checked state, and no call
   SHALL cause a later call to report `checked` for a value that `check_test`
   considers unchecked.
4. WHEN `get_context` is called with `attrs` equal to `None`, THEN the system
   SHALL behave without error and, if the value is checked, still produce a
   context whose attributes include `checked` set to `True`.
5. WHEN `check_test` reports the value as NOT checked, THEN the system SHALL
   leave the caller's `attrs` unchanged and SHALL NOT introduce a `checked`
   attribute into the produced context.

## Requirement 2: Checked/unchecked rendering is preserved

**User story:** As a user of the checkbox widget, I want the rendered HTML to
mark the box as checked exactly when the value is "on", so that the fix to the
mutation bug does not change what gets displayed.

**Acceptance criteria**

1. WHEN the widget renders a value that the default check treats as "on"
   (any value other than `False`, `None`, or the empty string — e.g. `True`, a
   non-empty string, or a nonzero integer), THEN the rendered checkbox HTML
   SHALL include the `checked` marker.
2. WHEN the widget renders `False`, `None`, or the empty string with the default
   check, THEN the rendered checkbox HTML SHALL NOT include the `checked`
   marker.
3. WHEN the widget renders a non-empty, non-boolean value, THEN the rendered
   HTML SHALL include that value as the element's `value` attribute; WHEN the
   value is `True`, `False`, `None`, or the empty string, THEN the rendered HTML
   SHALL omit the `value` attribute.
4. The system SHALL render the checkbox using the checkbox input type.

## Requirement 3: Custom check_test behavior is preserved

**User story:** As a developer supplying a custom `check_test`, I want the
widget to honor my callable when deciding whether to mark the box checked, so
that customized checked logic keeps working.

**Acceptance criteria**

1. WHEN a `CheckboxInput` is constructed with a custom `check_test` callable,
   THEN the system SHALL use that callable to decide whether the value is
   checked, marking the rendered HTML as checked exactly when the callable
   returns a truthy result for the value.
2. IF the `check_test` callable raises an exception for the given value, THEN
   the system SHALL allow that exception to propagate to the caller rather than
   suppressing it.
3. WHEN no `check_test` is supplied at construction, THEN the system SHALL apply
   the default check that treats a value as "on" unless it is `False`, `None`,
   or the empty string.

## Requirement 4: Value extraction and omission semantics are preserved

**User story:** As a developer processing submitted form data, I want the
checkbox widget to interpret posted data the same way as before, so that the
mutation fix does not change how submitted values are read.

**Acceptance criteria**

1. WHEN the widget extracts its value from submitted data and its field name is
   absent from that data, THEN the system SHALL return `False` (an unchecked
   checkbox is not submitted by HTML forms).
2. WHEN the field name is present with the string `"true"` or `"false"`
   (case-insensitively), THEN the system SHALL return the boolean `True` or
   `False` respectively; WHEN the field name is present with any other value,
   THEN the system SHALL return that value coerced to a boolean.
3. WHEN asked whether the value is omitted from the submitted data, THEN the
   system SHALL always report that it is not omitted, regardless of the data.
