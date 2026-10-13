# Requirements: Consistent field-value access through BoundField during form cleaning

## Introduction

In `django.forms.forms.BaseForm`, form validation (`_clean_fields`) and
change detection (`changed_data`) historically resolved each field's data and
initial value through low-level form helpers rather than through the field's
`BoundField` view (`form[name]`, an instance of
`django.forms.boundfield.BoundField`). Because the `BoundField` exposes a
*cached and normalized* initial value (via its `initial` property) and a
canonical submitted value (via its `data` property), the two access paths could
disagree.

The most visible symptom involves a **disabled** field with a **callable**
initial (for example a `DateTimeField` whose `initial` is a callable and whose
widget cannot represent sub-second precision). The cleaning path evaluated the
callable afresh and skipped the microsecond normalization applied by
`BoundField.initial`, so the value stored in `form.cleaned_data` could differ
from `form[name].initial` — both in its sub-second component and, for a
callable that returns a different value on each call, in its whole value.

The goal is that both `_clean_fields` and `changed_data` resolve each field's
submitted value and initial value through that field's `BoundField`, so the
cleaned value for a disabled field is exactly the value the `BoundField`
presents as its initial, while every other cleaning and change-detection
behavior is preserved.

The affected code lives in `django/forms/forms.py` (`BaseForm._clean_fields`,
`BaseForm.changed_data`, `BaseForm._html_output`) and
`django/forms/boundfield.py` (`BoundField.initial`, `BoundField.data`).

## Requirement 1: Disabled fields clean to their BoundField initial value

**User story:** As a developer building forms with disabled fields that carry
initial values, I want a disabled field's cleaned value to be exactly the
initial value its BoundField presents, so that `form.cleaned_data[name]` and
`form[name].initial` never disagree.

**Acceptance criteria**

1. WHEN a bound form is cleaned and a field is disabled, THEN `BaseForm` SHALL
   use that field's `BoundField` initial value (the value exposed by
   `form[name].initial`) as the value passed to the field's cleaning, ignoring
   any submitted form data for that field.
2. WHEN a disabled field is cleaned successfully, THEN the value stored in
   `form.cleaned_data` for that field SHALL be equal to `form[name].initial`
   for the same field.
3. IF a disabled field's `initial` is a callable, THEN the callable SHALL be
   evaluated only once while producing the field's initial value for cleaning,
   and the cleaned value SHALL reflect that single evaluation rather than a
   separate re-evaluation.
4. WHEN a disabled field whose widget cannot represent sub-second precision has
   a temporal (date/time/datetime) initial value with a non-zero sub-second
   component, THEN the value stored in `form.cleaned_data` for that field SHALL
   have its sub-second component removed (microseconds set to zero), matching
   the normalization performed by `BoundField.initial`.
5. WHEN a disabled field whose widget can represent sub-second precision has a
   temporal initial value, THEN the value stored in `form.cleaned_data` for
   that field SHALL retain its sub-second component unchanged.

## Requirement 2: Editable fields continue to clean their submitted data

**User story:** As a developer, I want ordinary (non-disabled) fields to keep
being cleaned from their submitted data, so that routing values through the
BoundField does not change existing behavior.

**Acceptance criteria**

1. WHEN a bound form is cleaned and a field is not disabled, THEN `BaseForm`
   SHALL use the field's submitted value — the value exposed by
   `form[name].data`, obtained from the form's data/files for that field's
   widget — as the value passed to the field's cleaning.
2. The system SHALL continue to run any per-field `clean_<fieldname>` hook and
   store its returned value in `form.cleaned_data`, exactly as before.
3. WHEN cleaning a field raises a validation error, THEN `BaseForm` SHALL
   record that error against the field and SHALL NOT place a cleaned value for
   that field in `form.cleaned_data`.
4. The system SHALL clean the fields in the form's field order and produce one
   `cleaned_data` entry per successfully cleaned field.

## Requirement 3: File fields still clean against their initial value

**User story:** As a developer using file fields, I want file cleaning to keep
receiving the field's initial value, so that clearing and retaining uploaded
files still works.

**Acceptance criteria**

1. WHEN a file field is cleaned, THEN `BaseForm` SHALL pass both the field's
   submitted value and that field's initial value (as presented by its
   `BoundField`) to the field's cleaning.
2. The system SHALL preserve the existing result of file-field cleaning for
   the empty, provided, and cleared cases.

## Requirement 4: Change detection resolves values through the BoundField

**User story:** As a developer relying on `form.changed_data` and
`form.has_changed()`, I want change detection to compare the same initial and
submitted values the rest of the form uses, so that its results stay correct
and consistent.

**Acceptance criteria**

1. The system SHALL compute `changed_data` as the list of field names, in field
   order, for which the field reports that its submitted value differs from its
   initial value.
2. WHEN a field does not use a separate hidden initial input, THEN change
   detection SHALL use that field's `BoundField` initial value (the value
   exposed by `form[name].initial`) as the initial value it compares against.
3. WHEN a field uses a separate hidden initial input, THEN change detection
   SHALL take the initial value from that hidden input's submitted data,
   converting it to the field's Python value before comparison.
4. IF converting a field's hidden-initial submitted data to its Python value
   fails validation, THEN change detection SHALL treat that field as changed
   and include it in `changed_data`.
5. WHEN comparing a field's initial and submitted values, THEN change detection
   SHALL delegate the comparison to the field's own change-detection logic so
   that field-type-specific semantics (including sub-second handling for
   temporal fields) are honored.
6. The system SHALL make `form.has_changed()` return true if and only if
   `changed_data` is non-empty.

## Requirement 5: Rendering and other consumers keep their existing behavior

**User story:** As a developer rendering forms, I want form output and the
form's public data accessors to behave exactly as before, so that this internal
consistency change is not observable in rendering.

**Acceptance criteria**

1. The system SHALL continue to render bound and unbound forms (table, list,
   and paragraph layouts) identically to before, including hidden fields,
   errors, labels, and help text.
2. WHEN a `BoundField`'s submitted value is requested, THEN it SHALL return the
   value obtained from the form's data/files for that field's widget.
3. The system SHALL keep `BoundField.initial` as a cached value that evaluates
   any callable initial only once per BoundField and applies sub-second
   normalization for widgets that cannot represent sub-second precision.
4. The system SHALL preserve the behavior of forms with `empty_permitted`,
   prefixes, initial data, dynamic initial data, and disabled fields as
   previously specified.
