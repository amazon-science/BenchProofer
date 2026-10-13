# Requirements: Include the `models` import when serializing the base Model type

## Introduction

When Django's migration autodetector writes a migration file, it serializes the
Python objects that describe each model (fields, bases, options, etc.) into
source text plus the set of import statements needed to make that source text
valid. This serialization is performed by
`django.db.migrations.serializer` (the per-type serializers) via the
`MigrationWriter.serialize` entry point in `django.db.migrations.writer`.

The base model class `django.db.models.Model` is handled as a special case by
`TypeSerializer.serialize`: it is rendered as the literal source text
`models.Model`. However, that special case previously reported **no** required
imports. As a result, when a model's `bases` referenced `models.Model` but no
other part of the migration happened to pull in the `django.db.models` module
(for example a model whose fields all come from a custom field module and whose
bases mix a plain mixin with `models.Model`), the generated migration file
referenced the name `models` without ever importing it. Importing/executing the
generated file then raised `NameError: name 'models' is not defined`.

The goal is to make `TypeSerializer` declare the import that its rendered text
depends on, so that any migration referencing `models.Model` is valid Python,
while leaving the source text and every other serialization behavior unchanged.

## Requirement 1: Serializing the base Model type reports its required import

**User story:** As a developer running `makemigrations`, I want the generated
migration to import everything it references, so that the migration file is
valid Python and can be imported and applied without a `NameError`.

**Acceptance criteria**

1. WHEN `TypeSerializer` (reached through `MigrationWriter.serialize`) is asked
   to serialize the type `django.db.models.Model`, THEN the serializer SHALL
   return the source text `models.Model` as its rendered representation.
2. WHEN the type being serialized is `django.db.models.Model`, THEN the
   serializer SHALL return, as its required-imports result, a set containing the
   import statement `from django.db import models`.
3. The system SHALL return the required imports for `django.db.models.Model` as
   a set (the same kind of imports collection returned for every other type),
   not as a bare list or other type.
4. WHEN a migration is generated whose only reference to the `models` name comes
   from a base equal to `django.db.models.Model`, THEN the resulting output
   SHALL still cause `django.db.models` to be imported (via the reported
   `from django.db import models` statement) so that the referenced `models`
   name resolves.

## Requirement 2: Round-trip equality of the serialized base Model type

**User story:** As a developer, I want the base model type to serialize to a
form that reconstructs the identical object, so that migrations faithfully
represent the model bases they were generated from.

**Acceptance criteria**

1. WHEN `django.db.models.Model` is serialized and the resulting source text is
   evaluated in a context where its reported imports have been applied, THEN the
   evaluated value SHALL be the `django.db.models.Model` type itself (a
   round-trip that yields an object equal to the original input).
2. The system SHALL ensure the rendered text `models.Model` is resolvable
   precisely because the reported imports make the `models` name available.

## Requirement 3: Preserve serialization of all other types

**User story:** As a maintainer, I want the fix to change only the base Model
special case, so that no other serialization behavior or import bookkeeping
regresses.

**Acceptance criteria**

1. WHEN the type `type(None)` is serialized, THEN the serializer SHALL return
   the source text `type(None)` with an empty set of required imports.
2. WHEN a built-in type (a type whose defining module is the builtins module) is
   serialized, THEN the serializer SHALL return the type's bare name with an
   empty set of required imports.
3. WHEN any other type that is neither a specially-recognised kind nor a
   built-in is serialized, THEN the serializer SHALL return the source text
   composed of the type's defining module and its qualified name joined by a
   dot, together with a required-imports set containing the statement that
   imports that defining module.
4. The system SHALL keep the existing behavior whereby the `django.db.models`
   module is imported into a generated migration only when it is actually
   referenced, and is omitted when unused.
5. The system SHALL keep the deterministic ordering and de-duplication of import
   statements collected across a generated migration, so that unrelated
   serialization and import-ordering behavior is unchanged.
6. The system SHALL keep serializing every other supported value kind
   (collections, numbers, strings, datetimes, enums, functions, fields,
   managers, and the like) exactly as before, with their existing rendered text
   and required imports.
