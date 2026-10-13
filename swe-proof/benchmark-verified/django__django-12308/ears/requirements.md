# Requirements: Readonly display of JSON model-field values in the admin

## Introduction

In the Django admin, model-field values that are shown **read-only** are
rendered to text by the helper `django.contrib.admin.utils.display_for_field`.
For a field holding a JSON object, this helper currently falls through to the
generic value renderer, which produces a Python `repr` of the underlying value
(for example `{'foo': 'bar'}`). That output is not valid JSON and is misleading
to the reader.

The goal is to make `display_for_field` render a JSON-valued model field
(`django.db.models.JSONField`) as its proper JSON text (for example
`{"foo": "bar"}`) when the field is displayed read-only, while preserving every
other branch of the helper and the sibling label helper
`django.contrib.admin.utils.label_for_field`.

The affected module is `django/contrib/admin/utils.py`; the serialization it must
reuse is the JSON model field's own value-preparation routine on
`django.db.models.JSONField` (which yields valid JSON text and, because it wraps
JSON encoding with the field's configured encoder, correctly handles the
invalid-JSON-input case), rather than a direct/ad-hoc JSON dump.

## Requirement 1: Render JSON-valued fields as valid JSON when read-only

**User story:** As an admin user viewing a read-only JSON field, I want the
value shown as proper JSON text, so that what I see is valid JSON rather than a
Python dictionary literal.

**Acceptance criteria**

1. WHEN `display_for_field` is called with a field that is a
   `django.db.models.JSONField` and a value that is neither `None` nor an empty
   value, THEN the helper SHALL return the JSON text produced by that field's own
   value-preparation routine (the same routine the model field uses to prepare a
   Python value for storage), rather than the generic value rendering.
2. WHEN a JSON object such as the mapping from `"foo"` to `"bar"` is rendered by
   this branch, THEN the returned text SHALL be its valid JSON form (double-quoted
   keys and string values) and SHALL NOT be a Python `repr` such as one using
   single quotes.
3. IF a value routed to the JSON branch cannot be serialized to JSON and the
   value-preparation routine raises `TypeError`, THEN `display_for_field` SHALL
   fall back to the generic value renderer
   (`django.contrib.admin.utils.display_for_value`) and return its result
   instead of propagating the error.
4. WHEN the value routed to the JSON branch is a Python string, THEN the JSON
   rendering path SHALL return the JSON encoding of that string as produced by the
   field's value-preparation routine (that is, the string SHALL itself be
   JSON-encoded, so a plain string value such as `a` becomes the JSON-quoted text
   `"a"`), rather than being returned verbatim.

## Requirement 2: Preserve None, empty, and non-JSON dispatch behavior

**User story:** As a maintainer, I want the JSON handling added without
disturbing any of the existing rendering rules, so that all other field types
and edge cases display exactly as before.

**Acceptance criteria**

1. WHEN `display_for_field` is called with a value of `None`, THEN it SHALL
   return the supplied empty-value placeholder, for a `JSONField` as for any
   other field, without entering the JSON rendering branch.
2. WHEN `display_for_field` is called with a `JSONField` whose value is an empty
   value (a value that is falsey, such as an empty object, empty list, empty
   string, the integer zero, or `False`), THEN it SHALL render it via the generic
   value renderer rather than the JSON value-preparation routine.
3. The JSON branch SHALL be positioned so that it does not intercept fields that
   already have dedicated handling; fields with defined choices, boolean fields,
   date/time fields, decimal/integer/float fields, and file fields SHALL continue
   to be rendered by their existing branches unchanged.
4. WHEN `display_for_field` is called with a field type that has no special
   branch, THEN it SHALL continue to delegate to the generic value renderer as
   before.
5. The system SHALL keep the existing numeric formatting behavior of
   `display_for_field` (integer, float, and decimal fields formatted through the
   number-formatting utilities, including thousand-separator settings) unchanged.

## Requirement 3: Preserve label resolution for model fields, including JSON fields

**User story:** As an admin developer, I want field labels to resolve correctly
for every model field type, so that a JSON field shows a sensible column/label
name just like any other field.

**Acceptance criteria**

1. WHEN `label_for_field` is called with the name of a concrete model field
   (including a `django.db.models.JSONField`), THEN it SHALL return that field's
   verbose name as the label.
2. IF `label_for_field` is called with `return_attr` enabled for a concrete model
   field, THEN the returned resolved attribute SHALL be `None` (indicating the
   name refers to a field).
3. The system SHALL keep the existing label-resolution behavior of
   `label_for_field` for callables, properties, model-admin attributes,
   model attributes, form fields, and `__str__` unchanged.
