# Requirements: Preserve a caller-supplied empty_label for radio-style ForeignKey admin fields

## Introduction

In the Django admin, `ModelAdmin.formfield_for_foreignkey` (in
`django/contrib/admin/options.py`) builds the form field for a `ForeignKey`
model field. When a field is listed in the `ModelAdmin.radio_fields` mapping,
the method selects a radio-button widget and also decides the placeholder text
for the "empty" (no selection) choice via the `empty_label` keyword argument.

The problem: for radio-style fields the method unconditionally set
`empty_label` to the translated default `"None"` whenever the underlying field
allowed blank values, discarding any `empty_label` a subclass had supplied in
its `kwargs` (for example, by overriding `formfield_for_foreignkey` and setting
`kwargs["empty_label"]` before calling `super()`). As a result, a custom empty
label could never take effect for radio fields.

The goal is to let a caller-supplied `empty_label` survive for radio-style
ForeignKey fields, while keeping the existing default and the existing
suppression of the empty label for non-blank fields, and without changing the
behavior of any non-radio code path.

## Requirement 1: Honor a caller-supplied empty_label for blank radio ForeignKey fields

**User story:** As a developer customizing a `ModelAdmin`, I want the
`empty_label` I pass into `formfield_for_foreignkey` to be respected for fields
rendered as radio buttons, so that I can control the placeholder text for the
"no selection" option.

**Acceptance criteria**

1. WHEN `formfield_for_foreignkey` processes a ForeignKey whose name is in
   `radio_fields`, no `widget` was already supplied, the underlying model field
   allows blank values, AND the caller supplied an `empty_label` value in
   `kwargs`, THEN the method SHALL forward that caller-supplied `empty_label`
   unchanged to the constructed form field.
2. IF the caller supplied an `empty_label` for such a field, THEN the method
   SHALL NOT replace it with the default translated `"None"` label.
3. WHEN the caller supplies an `empty_label`, THEN the resulting form field's
   empty choice SHALL display that caller-supplied text rather than the default.

## Requirement 2: Fall back to the default empty label when none is supplied

**User story:** As a developer relying on default admin behavior, I want the
placeholder text for blank radio ForeignKey fields to remain the standard
translated `"None"` when I do not customize it, so that existing sites are
unaffected.

**Acceptance criteria**

1. WHEN `formfield_for_foreignkey` processes a radio-style ForeignKey (name in
   `radio_fields`, no pre-supplied `widget`) whose model field allows blank
   values AND the caller did NOT supply an `empty_label`, THEN the method SHALL
   set `empty_label` to the translated default `"None"` label.
2. The system SHALL keep this default identical to the placeholder produced
   before this change for the no-customization case.

## Requirement 3: Suppress the empty label for non-blank radio ForeignKey fields

**User story:** As an admin user, I want radio ForeignKey fields that do not
allow blank values to offer no empty choice, so that a required relation cannot
be left unset via an empty option.

**Acceptance criteria**

1. WHEN `formfield_for_foreignkey` processes a radio-style ForeignKey whose
   model field does NOT allow blank values, THEN the method SHALL set
   `empty_label` to no label (a null/None value), regardless of whether the
   caller supplied an `empty_label`.
2. IF the model field disallows blank values, THEN the resulting radio form
   field SHALL NOT present a default `"None"` empty choice.

## Requirement 4: Leave non-radio ForeignKey handling unchanged

**User story:** As a maintainer, I want the empty-label change to be confined
to the radio-field branch, so that all other admin form-field behaviors are
preserved.

**Acceptance criteria**

1. WHEN `formfield_for_foreignkey` selects an autocomplete or raw-id widget, or
   when a `widget` was already supplied by the caller, THEN the method SHALL NOT
   apply the radio-branch `empty_label` logic and SHALL keep its existing
   behavior.
2. The system SHALL continue to build correct form fields for ForeignKey fields
   that are not listed in `radio_fields`, unaffected by this change.
3. The system SHALL keep producing correct admin form fields for non-ForeignKey
   model field types (for example character, text, integer, date, time,
   datetime, email, URL, and file fields) and for many-to-many fields, exactly
   as before.
4. The system SHALL preserve the existing radio-widget selection and its
   CSS class derivation for fields listed in `radio_fields`, changing only how
   the empty label is resolved.
5. The system SHALL preserve the existing queryset resolution and any other
   keyword-argument handling in `formfield_for_foreignkey`.
