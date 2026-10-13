# Requirements: Report the offending value when a model-backed single choice is invalid

## Introduction

Django's form fields whose permitted answers come from a database query set —
specifically `ModelChoiceField` in `django/forms/models.py` — coerce a raw
submitted value into a stored model instance during cleaning (its `to_python`
method). When the submission does not resolve to any stored object, the field
rejects it by raising a `ValidationError` with the error code
`invalid_choice`.

Unlike `ChoiceField` and `ModelMultipleChoiceField`, whose `invalid_choice`
messages can interpolate the offending submission through the `%(value)s`
named placeholder, `ModelChoiceField` historically raised its error **without
supplying any interpolation parameters**. As a result, an application that
overrides the `invalid_choice` message to include the `%(value)s` placeholder
could not actually display the value the user submitted — the placeholder had
no binding to render.

The goal is to make `ModelChoiceField` behave consistently with its siblings:
when it rejects an unresolved submission, the raised validation error must
carry the offending submitted value bound to the `value` interpolation
parameter, so that a message template referencing that placeholder renders the
value the caller actually sent. All existing coercion outcomes and error
metadata must be preserved.

## Requirement 1: Report the offending value on an invalid single choice

**User story:** As a developer configuring a model-backed single-choice form
field, I want the invalid-choice validation error to include the submitted
value as an interpolation parameter, so that I can customize the error message
to show users exactly which value was rejected.

**Acceptance criteria**

1. WHEN `ModelChoiceField.to_python` receives a submitted value that is not an
   empty value and that fails to resolve to a stored object in the field's
   query set, THEN the field SHALL raise a `ValidationError`.
2. WHEN such a rejection occurs, THEN the raised `ValidationError` SHALL carry
   interpolation parameters that bind the `value` placeholder name to the exact
   submitted value that was rejected.
3. IF the field's configured `invalid_choice` message template references the
   `%(value)s` placeholder, THEN the rendered error message SHALL contain the
   textual representation of the submitted value that was rejected.
4. WHEN a rejection occurs, THEN the raised `ValidationError` SHALL use the
   error code `invalid_choice`.
5. The resolution failure that triggers this rejection SHALL continue to be
   recognized when the lookup raises a value error, a type error, or the query
   set model's does-not-exist error.

## Requirement 2: Preserve existing coercion and error behavior

**User story:** As a maintainer, I want the value-reporting change to leave all
other cleaning outcomes and error metadata unchanged, so that existing forms
and error handling continue to work exactly as before.

**Acceptance criteria**

1. WHEN `ModelChoiceField.to_python` receives a submission that is one of the
   field's recognized empty values, THEN the field SHALL return `None` without
   raising an error.
2. WHEN `ModelChoiceField.to_python` receives a submission that resolves to
   exactly one stored object in the query set, THEN the field SHALL return that
   object and SHALL NOT raise an error.
3. The system SHALL keep the default `invalid_choice` message unchanged for
   `ModelChoiceField` when the application does not override it, so that a field
   using the default message continues to produce its existing text.
4. WHEN a `ModelChoiceField` rejects a submission and the message template does
   not reference the value placeholder, THEN the rendered message SHALL be
   unaffected by the presence of the value parameter.
5. The system SHALL leave the cleaning, coercion, and error-message behavior of
   all other form fields (including other choice and model-backed multiple
   choice fields) unchanged.
