# Requirements: Correct serialization of methods bound to nested classes

## Introduction

Django's migration writer serializes Python values into source-code strings so
that migrations can reference callables (such as a field's `default`). The
migration serializer in `django/db/migrations/serializer.py`, specifically the
`FunctionTypeSerializer.serialize` method, handles values that are methods bound
to a class object (for example, a `classmethod`). For such a value it must emit
a dotted reference of the form `<module>.<class label>.<method>` together with
the import needed to resolve `<module>`.

The defect: the serializer builds `<class label>` from the class's *bare* name
(`klass.__name__`), which is only the innermost class name. When the class is
nested inside another class, the bare name omits the enclosing class path, so
the emitted reference cannot be resolved at import time (e.g. it produces
`module.Inner.method` instead of `module.Outer.Inner.method`). The goal is to
emit a reference that uses the class's fully-qualified name
(`klass.__qualname__`), which is correct for both top-level and nested classes,
while leaving every other serialization behavior unchanged.

## Requirement 1: Reference methods bound to a class by their fully-qualified class path

**User story:** As a developer whose model uses a classmethod (e.g. a nested
`TextChoices` method) as a field `default`, I want the generated migration to
reference that method by its full dotted path, so that the migration imports and
runs without raising an error.

**Acceptance criteria**
1. WHEN `FunctionTypeSerializer.serialize` is called with a value that is a
   method whose `__self__` is a class object, THEN the serializer SHALL return a
   reference string composed of the class's module, the class's fully-qualified
   name (its `__qualname__`), and the method's own name (`__name__`), joined by
   single dots in that order (`"<module>.<qualified class name>.<method name>"`).
2. WHEN the bound class is nested inside one or more enclosing classes, THEN the
   returned reference string SHALL include the full enclosing-class path (each
   enclosing class name separated by a dot) between the module and the method,
   rather than only the innermost class name.
3. WHEN the bound class is defined at module top level (so its bare name and its
   fully-qualified name are identical), THEN the returned reference string SHALL
   be unchanged from the historical `"<module>.<class name>.<method name>"`
   form.
4. WHEN this branch produces a reference, THEN the serializer SHALL also return
   the set of required imports containing exactly the single entry
   `"import <module>"` for the bound class's module.

## Requirement 2: Preserve existing serialization behavior for all other values

**User story:** As a Django maintainer, I want the fix to affect only the
class-bound-method reference and leave every other serialization path intact, so
that no existing migration output regresses.

**Acceptance criteria**
1. The system SHALL continue to select the class-bound-method branch only when
   the value has a truthy `__self__` that is a class object, and SHALL leave the
   handling of all other function and value kinds unchanged.
2. WHEN a plain module-level function (not bound to a class) is serialized, THEN
   the serializer SHALL return its reference built from the function's module and
   its `__qualname__`, together with the corresponding `"import <module>"`, as
   before.
3. IF the value to serialize is a lambda, THEN the serializer SHALL raise a
   `ValueError` reporting that a lambda cannot be serialized.
4. IF a function's `__module__` is `None`, or the function is defined in a local
   scope (its `__qualname__` contains a `<locals>` marker), THEN the serializer
   SHALL raise a `ValueError` indicating the function cannot be serialized.
5. The system SHALL keep the serialized output of all other supported value
   types (built-in scalars, collections, enums, datetimes, models, managers,
   validators, regexes, and the like) byte-for-byte identical to prior behavior.
