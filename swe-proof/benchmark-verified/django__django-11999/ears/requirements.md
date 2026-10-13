# Requirements: Allow overriding `get_<field>_display()` on models

## Introduction

When a Django model field declares an enumerated set of `choices`, the field
framework installs an auto-generated display accessor method named
`get_<fieldname>_display` onto the owning model class during field
registration. This installation happens in `Field.contribute_to_class` (in
`django/db/models/fields/__init__.py`), in the block guarded by
`self.choices is not None`. The generated accessor is a `partialmethod`
bound to `Model._get_FIELD_display` (in `django/db/models/base.py`), which
maps a field value to its human-readable label via the field's `flatchoices`.

Prior to the regression, a model author could define their own
`get_<fieldname>_display` method on the model to override the generated
behavior. Beginning with Django 2.2, field registration unconditionally
overwrote any user-declared accessor of that name, so the override was
silently discarded and the auto-generated label was returned instead.

The goal is to restore the ability to override the display accessor: the
framework must install the auto-generated accessor only when the model class
does not already provide a method or attribute of that name, while continuing
to auto-generate the accessor (and return correct labels) for the common case
where the author has not overridden it.

## Requirement 1: Preserve a user-declared display accessor

**User story:** As a Django model author, I want to define my own
`get_<fieldname>_display` method on a model whose field has `choices`, so that
my custom method is the one that runs instead of the framework's
auto-generated accessor.

**Acceptance criteria**

1. WHEN a field with a non-empty `choices` set is registered onto a model
   class (via `Field.contribute_to_class`) AND that class already provides an
   attribute named `get_<fieldname>_display` (for example a method defined in
   the class body), THEN the field framework SHALL NOT replace or overwrite
   that existing attribute.
2. WHEN an instance of such a model has a user-declared
   `get_<fieldname>_display` method AND that method is called, THEN the
   model instance SHALL return the value produced by the user's own method.
3. IF a model author defines `get_<fieldname>_display` to return a fixed
   value that is unrelated to the field's `choices` labels, THEN calling that
   accessor on an instance SHALL return exactly that author-supplied value and
   SHALL NOT return the label derived from `choices`.

## Requirement 2: Auto-generate the display accessor when not overridden

**User story:** As a Django model author who has not overridden the accessor,
I want the framework to keep generating `get_<fieldname>_display` for fields
with `choices`, so that existing label-lookup behavior is unchanged.

**Acceptance criteria**

1. WHEN a field with a non-empty `choices` set is registered onto a model
   class AND that class does not already provide an attribute named
   `get_<fieldname>_display`, THEN the field framework SHALL install an
   auto-generated accessor of that name onto the class.
2. WHEN the auto-generated accessor is called on an instance whose field
   value appears among the field's choices, THEN it SHALL return the
   human-readable label associated with that value.
3. WHEN the auto-generated accessor is called on an instance whose field
   value does not appear among the field's choices, THEN it SHALL return the
   raw field value unchanged.
4. The system SHALL continue to install the auto-generated accessor for every
   field that declares `choices` and whose accessor name is not already
   defined on the model, including when multiple such fields exist on the same
   model.

## Requirement 3: Do not create an accessor for fields without choices

**User story:** As a Django maintainer, I want the display accessor to be
generated only for fields that carry `choices`, so that the registration
behavior for plain fields is unchanged.

**Acceptance criteria**

1. IF a field does not declare a `choices` set (its `choices` is `None`),
   THEN the field framework SHALL NOT install a `get_<fieldname>_display`
   accessor for that field.
2. The system SHALL keep the existing registration behavior for a field's
   value descriptor and metadata unchanged, regardless of whether the display
   accessor is installed.
