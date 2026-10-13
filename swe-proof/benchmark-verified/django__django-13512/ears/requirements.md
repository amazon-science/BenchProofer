# Requirements: Preserve non-ASCII characters when rendering JSON values in the admin and JSON form fields

## Introduction

Django's admin change list / change form and its JSON form field render the
value of a JSON model field by serializing it to a JSON text. Two code paths do
this:

- `django.contrib.admin.utils.display_for_field(value, field, empty_value_display)`
  — used by the admin to produce the read-only display string for a
  `django.db.models.JSONField` value.
- `django.forms.fields.JSONField.prepare_value(value)` — used by the JSON form
  widget to produce the string shown in the editable textarea.

Both paths currently serialize with JSON's default ASCII-only escaping, so any
character outside the ASCII range is emitted as a `\uXXXX` escape sequence
instead of the literal character. The result is that a JSON field holding non-ASCII text is shown to
admin users as unreadable escape sequences.

The goal is to make both serialization paths preserve non-ASCII characters
literally in their output, while keeping their existing behavior for ASCII
content, for `None`/empty values, for values that cannot be serialized to JSON,
and for the custom encoder configured on the field. Unrelated helpers in the
same module (notably `label_for_field`) must keep behaving exactly as before.

The affected modules are `django/contrib/admin/utils.py` and
`django/forms/fields.py`.

## Requirement 1: Admin display of JSON model-field values preserves non-ASCII characters

**User story:** As an admin user viewing a model that has a JSON field
containing non-ASCII text, I want the field's value rendered with its original
characters intact, so that I can read the stored data instead of escape codes.

**Acceptance criteria**

1. WHEN `display_for_field` is called with a non-empty value and a
   `django.db.models.JSONField` instance, THEN it SHALL return a JSON text
   serialization of that value in which characters outside the ASCII range are
   emitted as the literal characters themselves rather than as `\uXXXX` escape
   sequences.
2. WHEN `display_for_field` renders a `JSONField` value whose contents are
   entirely within the ASCII range, THEN it SHALL return exactly the JSON text
   that standard JSON serialization produces for that value — the same output as
   before this change — using standard compact JSON notation for objects,
   arrays, and scalar values, so that ASCII output is unchanged.
3. WHEN `display_for_field` renders a `JSONField` value (such as a mapping or
   nested structure) that contains non-ASCII text, THEN the returned text SHALL
   contain those non-ASCII characters verbatim and SHALL otherwise be valid,
   standard JSON notation.
4. WHEN the value passed for a `JSONField` cannot be serialized to JSON (a
   serialization `TypeError` is raised — e.g. a mapping whose keys are not
   valid JSON object keys), THEN `display_for_field` SHALL fall back to the
   generic value-display behavior and return that generic representation of the
   value rather than raising.
5. The serialization performed for a `JSONField` value SHALL use the JSON
   encoder configured on that field (the field's `encoder`), so that a
   custom encoder continues to govern how values are turned into JSON text.
6. WHEN `display_for_field` is called with a value of `None` for a `JSONField`,
   THEN it SHALL return the supplied empty-value display string, preserving the
   existing null-handling behavior.

## Requirement 2: JSON form field value preparation preserves non-ASCII characters

**User story:** As an admin user editing a JSON form field that holds non-ASCII
text, I want the textarea to be pre-filled with the readable characters, so
that I can see and edit the real content.

**Acceptance criteria**

1. WHEN `JSONField.prepare_value` (in `django.forms.fields`) is called with a
   value that is not already flagged as invalid input, THEN it SHALL return a
   JSON text serialization of that value in which characters outside the ASCII
   range are emitted as the literal characters themselves rather than as
   `\uXXXX` escape sequences.
2. WHEN `prepare_value` is given a string containing non-ASCII characters, THEN
   the returned JSON text SHALL be that string wrapped in JSON quotes with its
   non-ASCII characters preserved verbatim (for example, a Chinese string is
   returned as the same characters surrounded by double quotes).
3. WHEN `prepare_value` is given a dictionary or list whose contents include
   non-ASCII characters, THEN the returned JSON text SHALL be standard JSON
   object/array notation with every non-ASCII character preserved verbatim
   rather than emitted as a `\uXXXX` escape sequence.
4. WHEN `prepare_value` is given an all-ASCII value, THEN it SHALL return
   exactly the JSON text that standard JSON serialization produces for that
   value — the same output as before this change — including standard compact
   object notation for mappings, a bare `null` for the Python value `None`, and
   a double-quoted string for a string value.
5. IF the value passed to `prepare_value` is already an invalid-JSON-input
   marker (previously entered text that failed to parse), THEN it SHALL return
   that value unchanged rather than re-serializing it.
6. The serialization performed by `prepare_value` SHALL use the JSON encoder
   configured on the form field (the field's `encoder`), so that a custom
   encoder continues to govern the produced text.

## Requirement 3: Change-detection and parsing behavior of the JSON form field is unchanged

**User story:** As a developer relying on the JSON form field, I want its
validation and change-detection semantics to stay the same, so that only the
displayed characters change and nothing else regresses.

**Acceptance criteria**

1. The JSON form field's change-detection SHALL continue to report a value as
   unchanged when the initial and submitted values are equal JSON regardless of
   key ordering, and SHALL treat semantically distinct values (such as the
   boolean `True` versus the integer `1`) as changed.
2. WHEN the form field converts submitted text to a Python value, THEN it SHALL
   continue to accept valid JSON (including producing a marked JSON string for a
   bare JSON string input) and SHALL continue to reject invalid JSON with a
   validation error.
3. The form field SHALL continue to honor a custom encoder and decoder, a
   custom widget supplied by keyword or by attribute, the disabled-field
   behavior, empty/valid value handling, and the redisplay of previously
   invalid input, exactly as before.

## Requirement 4: Unrelated admin label lookup behavior is preserved

**User story:** As a developer using the admin utilities, I want the field-label
lookup helper to behave exactly as before, so that adding JSON serialization
changes to the same module does not regress label resolution.

**Acceptance criteria**

1. The system SHALL keep `django.contrib.admin.utils.label_for_field` resolving
   a human-readable label from a model field name, a model or model-admin
   attribute, a callable, a property, the `__str__` special name, and a form
   field, returning the same labels as before (including the resolved attribute
   when the caller requests it).
2. IF a name cannot be resolved on the model (nor on a supplied model admin or
   form), THEN `label_for_field` SHALL raise the same attribute-lookup error,
   with a message naming the model and, when applicable, the model admin and/or
   form.
3. The system SHALL keep the other admin utility helpers exercised alongside
   this change — including field help-text lookup, fieldset flattening,
   value/label display for non-JSON field types, number and null formatting,
   and nested-object collection — behaving exactly as before.
