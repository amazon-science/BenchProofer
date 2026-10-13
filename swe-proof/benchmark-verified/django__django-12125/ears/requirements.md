# Requirements: Correct migration serialization of nested (inner) class references

## Introduction

When Django serializes a migration, references to *type objects* (classes) are
turned into an import-safe source string plus a set of import statements. This
happens in `django/db/migrations/serializer.py`, in the `serialize` method of
`TypeSerializer` (the serializer registered for `type`). The result is the text
that appears in a generated migration file, for example when a custom model
`Field` subclass, an `enum` class, or a `Choices` class is passed as an argument
to a field's deconstructed representation.

The original implementation built the reference from the class's *leaf* name
only (the last component of its name). For a class defined at module top level
this is correct, but for a class defined **inside another class** (an inner /
nested class) it dropped the enclosing class names. For example, given

```
class Outer(object):
    class Inner(models.CharField):
        pass
```

the serializer emitted `some_module.Inner` instead of the correct
`some_module.Outer.Inner`, producing a migration that referenced a name that
does not exist at module scope and would fail to import. The same defect
affected `enum` classes and `Choices` subclasses defined as inner classes.

The goal is to make `TypeSerializer.serialize` emit the class's **fully
qualified in-module path** (the dotted chain of enclosing class names ending in
the class itself — i.e. the class's `__qualname__`), so that nested classes are
referenced correctly, while preserving every existing behavior for top-level
classes, built-in types, and the special-cased types.

## Requirement 1: Serialize nested classes with their full in-module path

**User story:** As a Django developer who defines a custom field, `enum`, or
choices class as an inner class, I want `makemigrations` to reference that class
by its full path within the module, so that the generated migration imports and
resolves the class correctly.

**Acceptance criteria**

1. WHEN `TypeSerializer.serialize` is called with a class that is defined inside
   one or more enclosing classes and whose defining module is not the built-ins
   module, THEN it SHALL return a reference string of the form
   `<module>.<qualified-name>`, where `<module>` is the class's defining module
   and `<qualified-name>` is the dotted chain of the enclosing class names
   followed by the class's own name (the class's `__qualname__`).
2. WHEN such a nested class is serialized, THEN the returned string SHALL include
   every enclosing class name (for the issue's example, the reference SHALL be
   `<module>.Outer.Inner`, not `<module>.Inner`).
3. WHEN a class defined at nested scope is serialized, THEN the returned set of
   required imports SHALL be exactly `{"import <module>"}`, where `<module>` is
   the class's defining module.
4. The behavior in criteria 1–3 SHALL apply uniformly to any nested class
   descriptor regardless of its kind, including a subclass of a model `Field`,
   an `enum` class, and a `Choices` subclass.

## Requirement 2: Preserve serialization of top-level classes

**User story:** As a maintainer, I want ordinary top-level classes to keep
serializing exactly as before, so that the fix introduces no regression for the
common case.

**Acceptance criteria**

1. WHEN `TypeSerializer.serialize` is called with a class that is defined at
   module top level (no enclosing class) and whose module is not the built-ins
   module, THEN it SHALL return `<module>.<class-name>` together with the import
   set `{"import <module>"}`, where `<class-name>` is the class's own name.
2. The system SHALL treat the top-level case as the same rule as Requirement 1:
   because a top-level class's qualified name equals its own name, the emitted
   reference SHALL be unchanged from the leaf-name form for such classes.

## Requirement 3: Preserve serialization of built-in types

**User story:** As a maintainer, I want built-in types to serialize without a
module prefix or import, so that references such as `int` remain bare.

**Acceptance criteria**

1. WHEN `TypeSerializer.serialize` is called with a class whose defining module
   is the built-ins module, THEN it SHALL return the class's own (leaf) name
   with no module prefix.
2. WHEN a built-in type is serialized, THEN the returned set of required imports
   SHALL be empty.

## Requirement 4: Preserve the special-cased types

**User story:** As a maintainer, I want the historically special-cased types to
keep their fixed representations, so that migrations referencing them stay
stable.

**Acceptance criteria**

1. WHEN `TypeSerializer.serialize` is called with the base model class
   (`models.Model`), THEN it SHALL return the string `"models.Model"` with an
   empty set of imports.
2. WHEN `TypeSerializer.serialize` is called with the type of `None`
   (`type(None)`), THEN it SHALL return the string `"type(None)"` with an empty
   set of imports.
3. IF the value is one of these special-cased types, THEN the serializer SHALL
   return its special string WITHOUT applying the module/qualified-name rule of
   Requirements 1–3.

## Requirement 5: Preserve serialization of numbers, decimals, and class-valued arguments

**User story:** As a maintainer, I want numeric values, decimals, and a class
object used as an argument value to keep serializing correctly, so that the
change to type-reference handling does not disturb these paths.

**Acceptance criteria**

1. WHEN an integer or a float is serialized, THEN it SHALL round-trip to an
   equal value; and the non-finite floats positive infinity, negative infinity,
   and NaN SHALL each round-trip to a value that is, respectively, positive
   infinite, negative infinite, and NaN.
2. WHEN a `decimal.Decimal` value is serialized, THEN the returned string SHALL
   be `Decimal('<value>')` (for example `Decimal('1.3')`) with the import set
   `{'from decimal import Decimal'}`, and the value SHALL round-trip equal.
3. WHEN a class object is serialized as an argument value (for example a custom
   field or enum class supplied as another field's default), THEN the reference
   to that class SHALL use its fully qualified in-module path in the same manner
   as Requirements 1 and 2 (a top-level such class yields `<module>.<class-name>`).
4. The system SHALL keep the existing serialization behavior for all other
   already-supported value kinds unchanged (regression protection).
