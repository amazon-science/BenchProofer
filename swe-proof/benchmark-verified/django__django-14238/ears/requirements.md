# Requirements: Recognize subclasses of BigAutoField and SmallAutoField as AutoField

## Introduction

Django's `AutoField` (in `django.db.models.fields`) uses a metaclass,
`AutoFieldMeta`, to maintain backward-compatibility for automatically-generated
primary-key fields. `AutoFieldMeta` exposes a `_subclasses` property listing the
designated member classes (`BigAutoField` and `SmallAutoField`) and overrides
the class-level `__subclasscheck__` and `__instancecheck__` hooks so that
`issubclass(X, AutoField)` and `isinstance(x, AutoField)` return `True` for those
designated field types even though they do not inherit from `AutoField`.

The current `__subclasscheck__` accepts a candidate only when it is *identical*
to one of the designated member classes (an identity/membership test). As a
result, a user-defined field that *inherits* from `BigAutoField` or
`SmallAutoField` is not recognized as an `AutoField`. This breaks configuring
`DEFAULT_AUTO_FIELD` (consumed by
`django.db.models.options.Options._get_default_pk_class`) with such a subclass:
that code validates the configured class with `issubclass(pk_class, AutoField)`
and raises `ValueError("Primary key '...' referred by DEFAULT_AUTO_FIELD must
subclass AutoField.")` when the check fails, crashing app startup.

The goal is to make the subclass check recognize any class that is a subclass
(directly or transitively) of a designated member class, while preserving all
existing recognition and rejection behavior for `AutoField`, `BigAutoField`,
`SmallAutoField`, and unrelated field types.

## Requirement 1: Recognize descendants of designated auto-field classes

**User story:** As a Django developer, I want a custom field that inherits from
`BigAutoField` or `SmallAutoField` to be treated as an `AutoField`, so that I can
use it as a primary key and as `DEFAULT_AUTO_FIELD` without Django rejecting it.

**Acceptance criteria**

1. WHEN `issubclass(candidate, AutoField)` is evaluated for a class `candidate`
   that is a direct or transitive subclass of `BigAutoField`, THEN the metaclass
   subclass check SHALL return `True`.
2. WHEN `issubclass(candidate, AutoField)` is evaluated for a class `candidate`
   that is a direct or transitive subclass of `SmallAutoField`, THEN the
   metaclass subclass check SHALL return `True`.
3. The `AutoFieldMeta` subclass check SHALL determine membership by the subclass
   relation to the designated member classes, not by identity/equality with a
   designated member class.
4. WHEN a candidate class is neither a subclass of any designated member class
   nor an ordinary subclass of `AutoField` by normal inheritance, THEN the
   subclass check SHALL fall back to the ordinary inherited subclass check and
   return its result.

## Requirement 2: Preserve recognition of the designated classes themselves

**User story:** As a maintainer, I want the existing recognition of `AutoField`,
`BigAutoField`, and `SmallAutoField` to keep working, so that the fix does not
regress established behavior.

**Acceptance criteria**

1. WHEN `issubclass(BigAutoField, AutoField)` is evaluated, THEN the result
   SHALL be `True`.
2. WHEN `issubclass(SmallAutoField, AutoField)` is evaluated, THEN the result
   SHALL be `True`.
3. WHEN `issubclass(AutoField, AutoField)` is evaluated, THEN the result SHALL
   be `True`.
4. The `AutoFieldMeta` instance check SHALL continue to report instances of
   `AutoField`, `BigAutoField`, `SmallAutoField`, and their subclasses as
   instances of `AutoField`.

## Requirement 3: Configure DEFAULT_AUTO_FIELD with an auto-field subclass

**User story:** As a Django developer, I want to set `DEFAULT_AUTO_FIELD` to a
class that subclasses `BigAutoField` (or `SmallAutoField`), so that models
without an explicit primary key use my custom auto field.

**Acceptance criteria**

1. WHEN `DEFAULT_AUTO_FIELD` is set to the import path of a class that subclasses
   `BigAutoField`, and a model without an explicit primary key is prepared, THEN
   that model's automatically-created primary key SHALL be an instance of the
   configured class.
2. WHEN `DEFAULT_AUTO_FIELD` names a class that is a subclass (direct or
   transitive) of a designated auto-field class, THEN
   `Options._get_default_pk_class` SHALL accept it and SHALL NOT raise the
   "must subclass AutoField" `ValueError`.
3. IF `DEFAULT_AUTO_FIELD` names a class that is not a subclass of `AutoField`
   (nor of any designated member class), THEN `_get_default_pk_class` SHALL
   continue to raise a `ValueError` stating that the referenced primary key must
   subclass `AutoField`.

## Requirement 4: Preserve existing DEFAULT_AUTO_FIELD and field behavior

**User story:** As a maintainer, I want all previously-working
`DEFAULT_AUTO_FIELD` resolution paths and auto-field behaviors to keep working,
so that the change is backward compatible.

**Acceptance criteria**

1. The system SHALL keep resolving a model's default primary key to an instance
   of the class named by `DEFAULT_AUTO_FIELD` when that setting names `AutoField`,
   `BigAutoField`, or `SmallAutoField`.
2. The system SHALL keep raising the appropriate configuration error when
   `DEFAULT_AUTO_FIELD` (or an app's `default_auto_field`) is empty, names a
   non-importable/nonexistent path, or names a non-auto field class.
3. The system SHALL keep honoring an app config's `default_auto_field` and
   many-to-many through-model auto-field resolution exactly as before.
4. The system SHALL keep the type coercion, invalid-value handling, relational
   database type, internal type reporting, and documented value-range validation
   of `AutoField`, `BigAutoField`, `SmallAutoField`, and the corresponding
   integer field types unchanged.
