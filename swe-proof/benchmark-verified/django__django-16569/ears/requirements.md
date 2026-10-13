# Requirements — Formset deletion-field decision for positionless forms

## Introduction

The form-set machinery in `django.forms.formsets` (`BaseFormSet`) attaches
extra fields to each form instance through the `add_fields(form, index)` hook.
The `index` argument is the form's positional offset within the form-set, but
for a form that occupies no slot — notably the template/blank form produced by
the `BaseFormSet.empty_form` property — `add_fields` is invoked with
`index=None`.

When a form-set both permits deletion and forbids deletion of extra forms
(`can_delete` is true and `can_delete_extra` is false), the deletion-field
decision compares `index` against the initial-form count. With `index=None`
that comparison performs `None < <int>`, raising
`TypeError: '<' not supported between instances of 'NoneType' and 'int'`, so
merely accessing `empty_form` (and anything that renders or interrogates it)
fails.

The goal is to make the deletion-field decision total: it must produce a
well-defined outcome for every form, including a positionless one, treating a
positionless form as not belonging to the initial-form prefix, while preserving
the existing deletion-field and ordering-field behavior for positioned forms.

## Requirement 1: `add_fields` never fails on a positionless form

**User story:** As a developer using a form-set that allows deletion but
disallows deleting extra forms, I want to access the form-set's blank/template
form without an error, so that I can render or inspect an unbound extra form.

**Acceptance criteria**
1. WHEN `BaseFormSet.add_fields` is called with `index` equal to `None`, THEN
   the method SHALL complete without raising an exception, for every
   combination of the form-set's `can_delete` and `can_delete_extra` settings.
2. WHEN a form-set has `can_delete` true and `can_delete_extra` false and its
   `empty_form` property is accessed, THEN the form-set SHALL return the
   template form without raising `TypeError`.
3. IF `index` is `None`, THEN `add_fields` SHALL NOT perform any ordered
   comparison between `index` and the initial-form count.

## Requirement 2: Deletion field is attached only when the form is eligible

**User story:** As a developer configuring deletion on a form-set, I want the
"delete" control to appear on exactly the forms that are eligible for deletion,
so that only appropriate forms can be marked for removal.

**Acceptance criteria**
1. The system SHALL attach the deletion field to a form during `add_fields`
   if and only if the form-set's `can_delete` setting is true AND either the
   form-set's `can_delete_extra` setting is true, OR the form has a concrete
   position `index` that is not `None` and is strictly less than the
   form-set's initial-form count.
2. IF `can_delete` is false, THEN `add_fields` SHALL NOT attach the deletion
   field, regardless of `can_delete_extra`, `index`, or the initial-form count.
3. WHEN `can_delete` is true and `can_delete_extra` is true, THEN `add_fields`
   SHALL attach the deletion field to the form regardless of `index` or the
   initial-form count (including when `index` is `None`).
4. WHEN `can_delete` is true, `can_delete_extra` is false, and `index` is
   `None`, THEN `add_fields` SHALL NOT attach the deletion field.
5. WHEN `can_delete` is true, `can_delete_extra` is false, and `index` is a
   position strictly less than the initial-form count, THEN `add_fields`
   SHALL attach the deletion field.
6. WHEN `can_delete` is true, `can_delete_extra` is false, and `index` is a
   position greater than or equal to the initial-form count, THEN `add_fields`
   SHALL NOT attach the deletion field.
7. WHEN a form-set has `can_delete` true and `can_delete_extra` false, THEN
   its `empty_form` SHALL NOT contain the deletion field, while its
   positioned initial forms SHALL contain it and its positioned extra forms
   SHALL NOT.

## Requirement 3: Preserve existing ordering-field and deletion behavior

**User story:** As a maintainer, I want the change limited to the positionless
crash, so that all previously working deletion and ordering behavior is
unaffected.

**Acceptance criteria**
1. The system SHALL continue to attach the ordering field during `add_fields`
   whenever the form-set's `can_order` setting is true, giving initial
   positioned forms (a concrete `index` below the initial-form count) an
   ordering field pre-filled with their one-based position and giving all
   other forms (including a positionless form) an ordering field with no
   initial value.
2. WHEN a form-set has `can_delete` true and `can_delete_extra` true, THEN
   every rendered form SHALL keep its deletion field, unchanged from prior
   behavior.
3. The system SHALL leave the outcome of `add_fields` for forms with a
   concrete (non-`None`) `index` identical to the prior behavior for every
   combination of `can_delete`, `can_delete_extra`, and initial-form count.
4. The system SHALL preserve all other observable form-set behavior —
   validation, rendering, iteration, media, and management-form handling —
   unchanged.
