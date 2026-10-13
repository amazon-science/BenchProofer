# Requirements: Serialize enum defaults by member name in migrations

## Introduction

When Django's migration framework writes a migration file, it must render every
field argument (defaults, choices, validators, …) as a string of Python source
that, when executed, reconstructs an equivalent value. This serialization is
performed by the serializer classes in
`django/db/migrations/serializer.py`; the entry point used by the migration
writer is `MigrationWriter.serialize`, which dispatches to a per-type serializer
via `serializer_factory`. Members of a Python `enum.Enum` subclass are handled
by `EnumSerializer`.

Previously `EnumSerializer` rendered an enum member using its stored *value* —
e.g. `module.ClassName(<value>)` — which looks the member up by calling the enum
class with that value. This is fragile when the value is not stable: a common
case is a member whose value is a lazily translated string (Django's
`gettext_lazy`). Once the value is translated into another language, the frozen
value baked into an old migration file is no longer a member of the enum, and
re-executing the migration raises `ValueError: '<old value>' is not a valid
<EnumClass>`.

An enum member's *name* is a stable Python identifier that does not change when
its value is translated or otherwise mutated. The goal is to make
`EnumSerializer` render an enum member by looking it up by name using subscript
syntax — `module.ClassName['NAME']` — so that the generated migration code is
correct regardless of what the member's value is or later becomes, while every
other value type continues to serialize exactly as before.

## Requirement 1: Serialize an enum member by its name using subscript lookup

**User story:** As a Django developer who uses an `Enum` member as a field
default (or in field `choices`), I want the generated migration to reference
that member by its stable name rather than its value, so that the migration
keeps working even after the member's value changes (for example when a lazily
translated string is rendered in a different language).

**Acceptance criteria**

1. WHEN the migration serializer serializes a value that is a member of an
   `enum.Enum` subclass, THEN it SHALL produce a source string of the form
   `<module>.<ClassName>[<name-literal>]`, where `<module>` is the enum class's
   defining module (`__module__`), `<ClassName>` is the enum class's name
   (`__name__`), and `<name-literal>` is the member's name rendered as a Python
   string literal (i.e. its `repr`, wrapped in quotes) — using subscript
   (`[...]`) lookup by name, not call (`(...)`) lookup by value.
2. WHEN such an enum member is serialized, THEN the produced source string SHALL
   NOT contain the member's stored value in any form; the rendered text SHALL be
   determined solely by the enum class's module, the enum class's name, and the
   member's name.
3. WHEN such an enum member is serialized, THEN the accompanying set of required
   imports SHALL be exactly the single import that makes the enum class's module
   available (an `import <module>` statement) and SHALL NOT include any import
   that would only have been needed to reconstruct the member's value.
4. The rendered subscript key SHALL be the member's name (its `.name`
   identifier), and the choice between name-based and value-based rendering SHALL
   NOT depend on the runtime type of the member's value; a member whose value is
   a plain string, a lazily translated string, an integer, raw bytes, or any
   other type SHALL all be rendered by name in the identical subscript form.
5. WHEN the serialized source string for an enum member is subsequently executed
   in a context where its module is importable, THEN it SHALL evaluate to the
   same enum member that was serialized (round-trip fidelity).

## Requirement 2: Apply name-based enum rendering wherever an enum member is serialized

**User story:** As a maintainer, I want name-based enum rendering to apply
consistently everywhere the writer emits an enum member — including inside a
field's `default` and inside its `choices` list — so that no code path still
bakes a value-based lookup into a migration.

**Acceptance criteria**

1. WHEN a model field (for example a `CharField`) whose `default` is an enum
   member is serialized, THEN the emitted `default=` argument SHALL reference
   that member in the name-based subscript form described in Requirement 1.
2. WHEN a model field's `choices` contains entries whose choice objects are enum
   members, THEN each such enum member appearing in the serialized `choices`
   SHALL be rendered in the name-based subscript form, while each choice's stored
   display/value component SHALL be serialized by its own type's normal rules.
3. WHEN a value is a member of an enum subclass that also derives from another
   built-in type (for example a flag/bit-mask enum or an integer-valued enum),
   THEN it SHALL likewise be rendered by name in the subscript form
   `<module>.<ClassName>['<name>']`, the same as any other enum member, and
   SHALL NOT be rendered in the value-based call (`(...)`) form.

## Requirement 3: Preserve serialization of all non-enum values (regression protection)

**User story:** As a maintainer, I want every non-enum value to serialize
exactly as it did before this change, so that only enum-member rendering is
affected and all other migration output is byte-for-byte unchanged.

**Acceptance criteria**

1. The serializer SHALL continue to dispatch enum members to the enum-specific
   rendering and SHALL continue to route every non-enum value to its existing
   type-specific serializer, so that only the enum case changes behavior.
2. WHEN a value that is not an enum member is serialized (for example a
   deconstructible class-based validator, a compiled regular expression, a plain
   string, an integer, or bytes), THEN the produced source string and its
   required imports SHALL be identical to what was produced before this change.
3. The system SHALL keep producing serialized output that round-trips: for any
   supported value, executing the emitted source string (with its declared
   imports available) SHALL reconstruct a value equivalent to the original.
4. WHEN the writer serializes a class-based (deconstructible) validator, THEN it
   SHALL continue to render it via its deconstructed import path and arguments
   and SHALL continue to raise the same import/lookup errors as before when that
   path cannot be resolved to the object.
