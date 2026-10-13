# Requirements: Allow `cleaned_data` to overwrite a model field's default value

## Introduction

When a Django `ModelForm` is saved, the helper
`django.forms.models.construct_instance(form, instance, fields=None, exclude=None)`
builds the model `instance` by copying resolved values out of the form's
`cleaned_data` onto the instance's model fields. It walks the model's fields in
declaration order and, for each field, decides whether to assign the form's
resolved value (`f.save_form_data(instance, cleaned_data[f.name])`) or to skip
the field so it keeps the value it already carries (its model-level default).

Historically, `construct_instance` left a field at its default whenever the
field had a model default **and** the field's value was omitted from the
submitted payload (as reported by the field widget's
`value_omitted_from_data(...)`). This meant that a value produced only inside a
form's `clean()` method — placed directly into `cleaned_data` for a field that
was not part of the submitted data — could not overwrite the model default. A
user wishing to derive such a field's value from other fields was forced to
mutate the raw submitted data rather than `cleaned_data`, which contradicts the
`cleaned_data` paradigm.

The goal is to let a **non-empty** value in `cleaned_data` take precedence over
a field's model default, while still leaving a field at its default when no
meaningful value was supplied (so that fields genuinely absent from a submission
— including checkbox-style widgets that omit unchecked values — continue to
receive their model defaults). The affected code is the per-field
"leave the default" decision inside the iteration loop of `construct_instance`
in `django/forms/models.py`. Empty sentinels are the members of a form field's
`empty_values` (the field's `empty_values` list, which derives from
`django.core.validators.EMPTY_VALUES`: `None`, `''`, `[]`, `()`, `{}`).

## Requirement 1: A non-empty resolved value overrides a field's model default

**User story:** As a developer using a `ModelForm`, I want a value I place into
`cleaned_data` (e.g. inside `clean()`) for a field that has a model default to
be written onto the saved instance, so that I can derive that field's value
without having to rewrite the raw submitted form data.

**Acceptance criteria**

1. WHEN `construct_instance` processes a model field that has a model-level
   default AND whose value was omitted from the submitted payload (its widget's
   `value_omitted_from_data(...)` reports it absent) AND whose corresponding
   `cleaned_data` value is NOT one of that form field's `empty_values`, THEN
   `construct_instance` SHALL assign that resolved `cleaned_data` value to the
   field on the constructed instance (it SHALL NOT leave the field at its model
   default).
2. WHEN such an override is applied to a non-file field, THEN the constructed
   instance's attribute for that field SHALL equal the value taken from
   `cleaned_data` for that field.
3. The system SHALL determine "emptiness" of the resolved value using the form
   field's own `empty_values` membership, treating each of `None`, `''`, `[]`,
   `()`, and `{}` as an empty value.

## Requirement 2: An empty resolved value leaves the field at its model default

**User story:** As a developer relying on model defaults, I want a field that
was not meaningfully supplied to still receive its model default, so that
omitting a field (or leaving it empty) continues to fall back to the default.

**Acceptance criteria**

1. WHEN `construct_instance` processes a model field that has a model-level
   default AND whose value was omitted from the submitted payload AND whose
   corresponding `cleaned_data` value IS one of that form field's
   `empty_values`, THEN `construct_instance` SHALL leave the field unassigned so
   that the constructed instance retains the field's model default.
2. IF a field's `cleaned_data` value equals any empty sentinel in the field's
   `empty_values` (including `None` and the empty string), THEN the field SHALL
   fall back to its model default rather than being assigned the empty value.
3. WHILE a form omits an optional checkbox-style field from the submitted data
   and that field's resolved value is empty, `construct_instance` SHALL continue
   to leave that field at its model default.

## Requirement 3: Preserve the existing field-eligibility and ordering behavior

**User story:** As a maintainer, I want the change to affect only the
default-versus-value decision, so that all other rules for which fields get
assigned, and in what order, remain unchanged.

**Acceptance criteria**

1. The system SHALL continue to skip any field that is not editable, that is an
   auto-generated key field, or whose name is absent from `cleaned_data`.
2. IF the caller passes an explicit `fields` collection, THEN
   `construct_instance` SHALL assign only fields whose names appear in that
   collection; and IF the caller passes a non-empty `exclude` collection, THEN
   `construct_instance` SHALL NOT assign any field whose name appears in
   `exclude`.
3. WHEN a field has no model default, THEN `construct_instance` SHALL assign its
   resolved `cleaned_data` value regardless of whether that value is empty
   (the default-fallback rule SHALL apply only to fields that have a default).
4. The system SHALL defer file-type fields to a second pass, assigning all
   eligible non-file fields first in model-field order and then all eligible
   file-type fields in model-field order, so that a file field's value
   computation can rely on the other fields' assigned values.
5. WHEN `construct_instance` completes, THEN it SHALL return the same model
   instance it was given, populated in place, without saving it to the database.
