# Requirements: Honor `formfield_callback` declared in a ModelForm's `Meta`

## Introduction

In Django's forms layer (`django/forms/models.py`), a model-form class is
assembled by the metaclass `ModelFormMetaclass`, which builds the class's
`base_fields` by calling `fields_for_model` with a *field-builder callback*
(`formfield_callback`). That callback, when present, is invoked once per model
field to produce the corresponding form field.

Historically the metaclass selected this callback from a **top-level class
attribute** named `formfield_callback` (falling back to scanning base classes'
inner `Meta` for one), rather than from the constructed class's own **options
block** (`Meta.formfield_callback`). Two consequences followed:

1. A `formfield_callback` declared inside a form's `Meta` was ignored when the
   class was built directly.
2. `modelform_factory(...)` always injected a top-level `formfield_callback`
   class attribute defaulting to `None`; that `None` overwrote any callback the
   base form carried in its `Meta`, so factory-produced forms silently lost the
   base form's callback.

The goal is to make model-form construction resolve the field-builder callback
**from the class's own options block** — `Meta.formfield_callback`, resolved
through the normal `Meta` inheritance chain — and to stop the factory helper
`modelform_factory` from injecting a top-level attribute that clobbers it, while
preserving every previously supported way of supplying a callback.

The affected symbols are `ModelFormOptions`, `ModelFormMetaclass.__new__`, and
`modelform_factory` in `django/forms/models.py`, together with the field
construction performed by `fields_for_model`.

## Requirement 1: Options block exposes its declared field-builder callback

**User story:** As a developer defining a `ModelForm`, I want the callback I put
in `Meta.formfield_callback` to be recognized as part of the form's options, so
that it is used when the form's fields are built.

**Acceptance criteria**

1. WHEN a model-form's options are computed from its inner `Meta`, THEN the
   options object SHALL expose the field-builder callback declared in that
   options block.
2. IF the options block declares no field-builder callback, THEN the options
   object SHALL expose "no callback" (a `None` value) for it.
3. The system SHALL resolve the options-block callback through the normal
   `Meta` inheritance chain, so that a callback declared in a base form's
   `Meta` is visible on a derived form whose own `Meta` does not redeclare it.

## Requirement 2: Constructed model-form uses only its own options-block callback

**User story:** As a developer, I want a model-form class to build its fields
using the callback from its own options block and nothing else, so that
declaring `formfield_callback` in `Meta` reliably controls field construction.

**Acceptance criteria**

1. WHEN `ModelFormMetaclass` builds a model-form class that has a model and a
   field selection, THEN it SHALL build `base_fields` using the field-builder
   callback drawn from the class's own options block (`Meta.formfield_callback`,
   resolved through options inheritance).
2. WHEN the options block supplies a callback, THEN each model field SHALL be
   turned into a form field by invoking that callback, so that the resulting
   `base_fields` reflect the widgets/field types the callback produces.
3. IF the options block supplies no callback, THEN the class SHALL build its
   fields with the default field construction (no callback), even if a callback
   is present as a direct top-level class attribute or in a base form's options
   block.
4. WHEN a form declares its callback only in a base form's `Meta` and inherits
   through the options chain, THEN the derived class SHALL build its fields with
   that inherited callback.
5. WHEN a further subclass inherits from a model-form that was built with a
   given callback, THEN the subclass's `base_fields` SHALL be built with the
   same effective callback, producing the same widget type per field as the
   parent's corresponding field.

## Requirement 3: `modelform_factory` does not clobber the base form's callback

**User story:** As a developer calling `modelform_factory` on a form whose base
`Meta` declares a callback, I want the produced form to keep using that
callback, so that factory-built forms behave like the base form.

**Acceptance criteria**

1. WHEN `modelform_factory` builds a form from a base form whose options block
   declares a field-builder callback and no explicit callback argument is
   passed, THEN the produced form SHALL build its fields using the base form's
   options-block callback.
2. The system SHALL NOT place a top-level `formfield_callback` attribute
   defaulting to "no callback" on the generated form class in a way that
   overrides a callback inherited from the base form's options block.
3. WHEN `modelform_factory` is called with an explicit callback argument, THEN
   the produced form SHALL build its fields using that explicit callback,
   invoking it once per included model field with the same per-field keyword
   arguments (e.g. an overridden widget) that field construction would otherwise
   apply.

## Requirement 4: Preserve existing callback and construction behavior (regression protection)

**User story:** As a maintainer, I want all previously supported callback and
form-construction behaviors to keep working, so that this change fixes the bug
without regressions.

**Acceptance criteria**

1. IF a supplied field-builder callback is not callable, THEN the system SHALL
   raise a `TypeError` when it attempts to use it.
2. WHEN `modelform_factory` is given an explicit callback and produces a form,
   and a subclass is derived from that produced form, THEN each field of the
   subclass SHALL have the same widget type as the corresponding field of the
   produced form.
3. The system SHALL continue to build model-form classes using the same
   metaclass as the base form, so that factory-produced and subclassed forms
   remain valid model-form classes.
4. WHEN a base form declares per-field widgets in its options block and no
   callback, THEN `modelform_factory` SHALL produce a form whose fields use
   those declared widgets.
5. WHEN `modelform_factory` is given a `widgets` mapping and no callback, THEN
   the produced form's named fields SHALL use the specified widgets, and absent
   such a mapping SHALL use the default widgets.
6. IF `modelform_factory` is called without either a field selection or an
   exclusion list, THEN the system SHALL raise `ImproperlyConfigured`.
7. The system SHALL continue to honor the other options-block settings
   (`fields`, `exclude`, `widgets`, `localized_fields`, `labels`, `help_texts`,
   `error_messages`, `field_classes`) when building a model-form's fields.
