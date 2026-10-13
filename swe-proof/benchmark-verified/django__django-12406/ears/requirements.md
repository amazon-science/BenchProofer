# Requirements: RadioSelect empty option for model choice fields

## Introduction

When a model `ForeignKey` is rendered in a `ModelForm` using the
`django.forms.RadioSelect` widget, Django currently always prepends an empty
choice (rendered with the placeholder label `---------` and an empty value) to
the list of choices, and marks it as the initially selected radio input on an
unbound form. For a `Select` (dropdown) widget an empty first entry is
idiomatic even for required fields, but for radio buttons the empty entry looks
like a genuine, pre-selected option, which is misleading when an empty value is
not actually a valid selection for the underlying model field.

This work concerns `django.forms.models.ModelChoiceField` (its choice iteration
via `ModelChoiceIterator`, driven by the field's `empty_label` attribute) and
`django.db.models.fields.ForeignKey.formfield` in
`django.db.models.fields.related`, which builds the form field for a foreign
key. The goal, in behavioral terms: a `ModelChoiceField` rendered with a radio
widget should omit the empty choice exactly when the underlying model field
does not permit a blank value, while preserving the empty choice (and all other
existing behavior) in every other case.

Throughout this document, "the empty choice" means the leading choice pair
whose submitted value is the empty string and whose label is the field's
`empty_label` text (by default `---------`). "The radio widget" means the
`django.forms.RadioSelect` widget, supplied either as the widget class itself
or as an instance of it. "Permits blank" refers to whether a blank/empty
selection is a valid value for the model field being represented (the model
field's `blank` setting).

## Requirement 1: Suppress the empty choice for radio widgets that do not permit blank

**User story:** As a developer rendering a required foreign key with radio
buttons, I want no spurious empty option to appear, so that users are not
presented with `---------` as if it were a selectable, pre-checked value.

**Acceptance criteria**

1. `ModelChoiceField` SHALL accept, at construction time, an indication of
   whether a blank selection is permitted for the field, defaulting to "blank
   not permitted" when the caller supplies no such indication.
2. WHEN a `ModelChoiceField` is constructed with the radio widget and blank is
   not permitted, THEN the field SHALL produce its choices without the empty
   choice, so that iterating the field's `choices` yields only the entries
   derived from the queryset objects, in queryset order.
3. WHEN a `ModelChoiceField` is constructed with the radio widget and blank IS
   permitted, THEN the field SHALL include the empty choice as the first entry,
   followed by the entries derived from the queryset objects.
4. The determination in criteria 2 and 3 SHALL recognize the radio widget
   whether it is passed as the widget class or as an instance of that widget
   class, producing identical choice output for the two forms given the same
   blank setting.
5. WHEN blank is not permitted for a radio-widget field, THEN the field SHALL
   report having no empty label (its `empty_label` attribute SHALL be `None`),
   so that no empty radio input is emitted or pre-selected on an unbound form.

## Requirement 2: Propagate the model field's blank setting to the form field

**User story:** As a developer defining a `ModelForm` over a model with a
foreign key, I want the form field to know whether the model allows a blank
value, so that the radio-widget behavior above is driven by the model
definition without extra configuration.

**Acceptance criteria**

1. WHEN a `ForeignKey.formfield(...)` builds a `ModelChoiceField`, THEN it SHALL
   pass through the model field's own blank setting as the field's blank
   indication, unless the caller explicitly overrides it.
2. WHEN a `ModelForm` is built for a foreign key declared as not allowing blank
   and configured to use the radio widget, THEN the resulting field's choices
   SHALL NOT contain the empty choice.
3. WHEN a `ModelForm` is built for a foreign key declared as allowing blank and
   configured to use the radio widget, THEN the resulting field's choices SHALL
   begin with the empty choice, followed by the queryset-derived entries.
4. The queryset-derived entries in criteria 2 and 3 SHALL use each related
   object's string representation as the choice label and the object's primary
   key (or configured target field value) as the choice value.

## Requirement 3: Preserve existing empty-choice behavior for all other cases

**User story:** As a maintainer, I want the change to affect only the
radio-widget case, so that dropdown-based forms and previously specified
behaviors are unchanged.

**Acceptance criteria**

1. The system SHALL continue to include the empty choice as the first entry for
   a `ModelChoiceField` that uses the default (non-radio) widget, regardless of
   the blank indication, except where criterion 2 already suppresses it.
2. IF a `ModelChoiceField` is required and is given a non-`None` initial value,
   THEN the field SHALL report no empty label and SHALL omit the empty choice,
   regardless of widget or blank setting.
3. WHEN a `ModelChoiceField` is not required, THEN the field SHALL retain the
   empty choice as its first entry (for a non-radio widget), preserving the
   previously specified behavior for optional fields.
4. The field's default empty label text SHALL remain `---------`, and a
   caller-supplied empty label SHALL continue to be honored wherever the empty
   choice is emitted.
5. WHEN choices are requested before any objects exist in the queryset, THEN a
   field that includes the empty choice SHALL still yield that empty choice,
   and its truthiness SHALL remain `True` while an empty choice is present.

## Requirement 4: Preserve model-instance cleaning and validation behavior

**User story:** As a developer, I want `ModelChoiceField` value cleaning to keep
working exactly as before, so that adding the blank behavior does not regress
value coercion or error reporting.

**Acceptance criteria**

1. WHEN a `ModelChoiceField` over a queryset is asked to clean a model instance
   that belongs to that queryset, THEN it SHALL return that same instance.
2. IF the value passed to clean is an instance of a different model (not present
   in the queryset), THEN the field SHALL raise a validation error whose message
   is "Select a valid choice. That choice is not one of the available choices.".
3. WHEN cleaning a value that is empty, THEN the field SHALL resolve it to
   `None` rather than raising, preserving the existing empty-value handling.
4. The addition of the blank indication SHALL NOT change the constructor's
   handling of any other previously accepted argument (queryset, required,
   widget, label, initial, help_text, to_field_name, limit_choices_to), and all
   such arguments SHALL continue to behave as before.
