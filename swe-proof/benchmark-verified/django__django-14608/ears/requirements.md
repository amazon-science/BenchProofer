# Requirements: `nonform` CSS class for non-form errors in FormSets

## Introduction

Django forms attach a `nonfield` CSS class to the `ErrorList` that holds a
form's non-field errors, letting a custom `ErrorList` renderer visually
distinguish those errors from field errors. FormSets, however, expose a
comparable category of errors — *non-form errors*, produced by formset-wide
validation (management-form bookkeeping, `validate_max`/`validate_min` limit
checks, and the formset's `clean()` cross-form validation) and returned by
`BaseFormSet.non_form_errors()`.

Prior to this change the `ErrorList` returned by
`BaseFormSet.non_form_errors()` rendered under only the base `errorlist` CSS
class, giving renderers no way to tell formset-level non-form errors apart from
ordinary form errors.

The goal is to make the non-form `ErrorList` maintained in
`django/forms/formsets.py` (`BaseFormSet.full_clean` / `.non_form_errors`)
carry an additional `nonform` CSS class, mirroring the existing `nonfield`
treatment on forms, while preserving every other observable property of the
non-form errors (their messages, ordering, `ErrorList` type, and the behavior
of dependent APIs such as `total_error_count()` and `is_valid()`).

The `ErrorList` container itself (`django/forms/utils.py`) already supports an
`error_class` argument that appends an extra space-separated CSS class after
the base `errorlist` class; no change to that container is required.

## Requirement 1: Non-form errors render under the `nonform` CSS class

**User story:** As a developer writing a custom `ErrorList` renderer, I want the
formset's non-form errors to be tagged with a `nonform` CSS class, so that I can
style or distinguish them from form field errors and non-field errors.

**Acceptance criteria**

1. WHEN a bound FormSet is fully cleaned and its non-form errors are retrieved
   via `non_form_errors()`, THEN the returned collection SHALL be an
   `ErrorList` instance.
2. The system SHALL render the non-form `ErrorList` under the exact CSS class
   value `errorlist nonform` — the base `errorlist` class followed by a single
   space and the `nonform` class.
3. WHEN the non-form `ErrorList` is rendered to its HTML representation and it
   contains at least one message, THEN the produced markup SHALL be a `<ul>`
   element whose `class` attribute is exactly `errorlist nonform`, i.e. of the
   form `<ul class="errorlist nonform"><li>…</li>…</ul>`.
4. The `nonform` class SHALL be present in addition to, and never as a
   replacement for, the base `errorlist` class.

## Requirement 2: The `nonform` class is present on every non-form-error production path

**User story:** As a developer, I want the `nonform` class applied consistently
however the non-form errors arose, so that my renderer can rely on it
regardless of which formset-wide validation produced the errors.

**Acceptance criteria**

1. The system SHALL initialize the FormSet's non-form error collection as an
   `ErrorList` carrying the `nonform` CSS class at the start of full cleaning,
   before any messages are added.
2. IF the FormSet's `validate_max` check fails (too many submitted forms),
   THEN the resulting non-form `ErrorList` returned by `non_form_errors()`
   SHALL carry the `nonform` CSS class in addition to the base `errorlist`
   class.
3. IF the FormSet's `validate_min` check fails (too few submitted forms),
   THEN the resulting non-form `ErrorList` returned by `non_form_errors()`
   SHALL carry the `nonform` CSS class in addition to the base `errorlist`
   class.
4. WHEN the FormSet's `clean()` hook raises a validation error during
   cross-form validation, THEN the non-form `ErrorList` built from those raised
   errors SHALL carry the `nonform` CSS class in addition to the base
   `errorlist` class.
5. IF management-form bookkeeping is invalid and a corresponding non-form error
   is recorded, THEN that error SHALL be carried in the non-form `ErrorList`
   that carries the `nonform` CSS class.

## Requirement 3: Preserve the messages, ordering, and type of non-form errors

**User story:** As a maintainer, I want the change to affect only the CSS class
of the non-form errors, so that existing behavior of formset validation is not
altered.

**Acceptance criteria**

1. The system SHALL keep the non-form error messages exactly as before: the
   messages carried by the non-form `ErrorList`, and their order, SHALL be
   unchanged by the addition of the `nonform` class.
2. WHEN `validate_max` fails, THEN `non_form_errors()` SHALL still report the
   existing "Please submit at most N form(s)." message (with correct
   singular/plural form and the configured limit), unchanged in text and count.
3. WHEN `validate_min` fails, THEN `non_form_errors()` SHALL still report the
   existing "Please submit at least N form(s)." message (with correct
   singular/plural form and the configured limit), unchanged in text and count.
4. WHEN the FormSet's `clean()` hook raises validation errors, THEN
   `non_form_errors()` SHALL report exactly those error messages, unchanged in
   text, count, and order.
5. The system SHALL keep `non_form_errors()` returning an `ErrorList` instance
   (equal, by value comparison, to the corresponding list of message strings)
   in all cases, including when there are no non-form errors (an empty
   `ErrorList`).

## Requirement 4: Preserve dependent formset APIs

**User story:** As a developer relying on formset validation results, I want
counts and validity checks that build on non-form errors to keep working
exactly as before.

**Acceptance criteria**

1. The system SHALL keep `total_error_count()` returning the sum of the number
   of non-form errors and the per-form error counts, unchanged by the addition
   of the `nonform` class.
2. WHEN a FormSet has non-form errors, THEN `is_valid()` SHALL still return
   `False`; WHEN it has none and all forms are valid, THEN `is_valid()` SHALL
   still return `True`.
3. IF `non_form_errors()` is called before `is_valid()`, THEN it SHALL trigger
   full cleaning and return the correct non-form `ErrorList` (carrying the
   `nonform` class), as it did before.
4. The system SHALL keep the admin changelist's formset exposing its non-form
   errors as an `ErrorList` whose rendered form matches an `ErrorList` built
   with the `nonform` CSS class, so that admin list-editable validation
   messages render identically to a directly constructed non-form `ErrorList`.
