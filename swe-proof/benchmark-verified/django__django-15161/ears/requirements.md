# Requirements: Simplified import paths for deconstructed expressions

## Introduction

When Django serializes a query expression into generated migration code, it
first *deconstructs* the object into a 3-tuple of `(import_path, args, kwargs)`.
The import path is the fully-qualified location from which the object's class
can be reconstructed. Several expression classes are defined in
`django.db.models.expressions` but are also publicly re-exported from
`django.db.models`. Historically these classes deconstructed to their internal
definition module (e.g. `django.db.models.expressions.Value`), producing verbose
migration code.

`F` was previously changed to deconstruct to its public location
(`django.db.models.F`) by attaching the `deconstructible` decorator with an
explicit `path` argument, so that generated migrations refer to it simply as
`models.F(...)` under `from django.db import models`. This work applies the same
simplification to the remaining public expression classes.

Affected module: `django/db/models/expressions.py`. Affected classes:
`Func`, `Value`, `ExpressionWrapper`, `When`, `Case`, and `OrderBy` — each of
which is also importable directly from `django.db.models`. The
`django.utils.deconstruct.deconstructible` decorator (with its optional `path`
keyword) and the migration serializer (`MigrationWriter.serialize`) are the
consuming machinery whose behavior must remain correct.

## Requirement 1: Simplified deconstruct path for public expression classes

**User story:** As a developer generating migrations that reference expression
objects, I want those expressions to deconstruct to their short public import
path, so that the generated migration code is concise and references them via
`models.<Name>`.

**Acceptance criteria**

1. WHEN `deconstruct()` is called on an instance whose runtime type is exactly
   `Value`, THEN the returned import path SHALL be the string
   `django.db.models.Value` (the public location), NOT the internal
   `django.db.models.expressions` location.
2. WHEN `deconstruct()` is called on an instance whose runtime type is exactly
   `Func`, THEN the returned import path SHALL be `django.db.models.Func`.
3. WHEN `deconstruct()` is called on an instance whose runtime type is exactly
   `ExpressionWrapper`, THEN the returned import path SHALL be
   `django.db.models.ExpressionWrapper`.
4. WHEN `deconstruct()` is called on an instance whose runtime type is exactly
   `When`, THEN the returned import path SHALL be `django.db.models.When`.
5. WHEN `deconstruct()` is called on an instance whose runtime type is exactly
   `Case`, THEN the returned import path SHALL be `django.db.models.Case`.
6. WHEN `deconstruct()` is called on an instance whose runtime type is exactly
   `OrderBy`, THEN the returned import path SHALL be
   `django.db.models.OrderBy`.
7. The system SHALL keep each of these classes importable from
   `django.db.models` under its own name, so that each configured simplified
   path resolves to the correct class object.

## Requirement 2: Reconstruction arguments are unchanged by the path simplification

**User story:** As a developer, I want only the import path to change, so that
deconstructed objects still round-trip to equivalent instances.

**Acceptance criteria**

1. WHEN `deconstruct()` is called on a `Value` constructed from a single wrapped
   value, THEN the returned positional arguments SHALL be a 1-tuple containing
   exactly that wrapped value, and the returned keyword arguments SHALL be an
   empty mapping.
2. WHEN `deconstruct()` is called on a `Value` constructed with an explicit
   `output_field`, THEN the returned positional arguments SHALL still be the
   1-tuple of the wrapped value, and the returned keyword arguments SHALL
   contain exactly one entry, `output_field`, whose value deconstructs
   identically to that supplied output field.
3. The system SHALL leave the positional and keyword arguments produced by
   `deconstruct()` for all affected classes determined solely by the object's
   construction arguments; changing the import path SHALL NOT alter them.

## Requirement 3: Fallback path for subclasses and misconfiguration

**User story:** As a maintainer, I want the simplified path to apply only to the
exact configured class, so that subclasses and other expression types are not
misattributed to a location where they do not exist.

**Acceptance criteria**

1. IF the object being deconstructed is an instance of a subclass of one of the
   affected classes (its runtime type is not exactly the configured class),
   THEN `deconstruct()` SHALL return that object's own fully-qualified location
   (its defining module joined to its class name), NOT the configured
   simplified path.
2. The system SHALL verify that the target name is actually present at the
   chosen import location, and IF it is not, THEN `deconstruct()` SHALL raise an
   error rather than emit an unresolvable path.

## Requirement 4: Concise migration serialization of affected expressions

**User story:** As a developer running migration generation, I want expressions
embedded in migration operations to be written using the short `models.` prefix,
so that the emitted code is minimal and imports only `from django.db import
models`.

**Acceptance criteria**

1. WHEN the migration serializer serializes an object built from the affected
   expression classes (for example an index whose expressions include a
   function call expression, a conditional case with a when-branch and a wrapped
   value, an expression wrapper, and an ordering expression), THEN each affected
   expression in the produced source string SHALL be rendered referenced through
   the top-level `models` namespace, prefixed as `models` followed by the class
   name, NOT through the internal `expressions` submodule.
2. WHEN such an object is serialized, THEN the reported set of required imports
   SHALL be exactly the single import `from django.db import models`.
3. The system SHALL preserve the existing nested structure and argument values
   of the serialized expressions (nested expressions, keyword arguments such as
   `then`, `default`, `output_field`, and ordering direction) so that the
   emitted code reconstructs an equivalent object.

## Requirement 5: Regression protection for existing expression behavior

**User story:** As a maintainer, I want the previously simplified expression
(`F`) and all other expression semantics preserved, so that this change is
purely additive with respect to path shortening.

**Acceptance criteria**

1. The system SHALL keep `F` deconstructing to `django.db.models.F` with its
   existing arguments.
2. The system SHALL keep equality, hashing, `repr`, SQL compilation, grouping,
   output-field resolution, and expression-combination behavior of all affected
   classes unchanged.
3. The system SHALL keep serialization of all other supported value types
   (built-in types, fields, validators, datetimes, enums, and the like)
   producing their existing output and import sets.
4. WHEN serialized code does not reference the `models` namespace, THEN the
   serializer SHALL NOT emit an unused `django.db import models` import.
