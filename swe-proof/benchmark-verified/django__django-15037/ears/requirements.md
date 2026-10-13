# Requirements: `inspectdb` support for foreign keys referencing a non-primary-key column

## Introduction

Django's `inspectdb` management command
(`django/core/management/commands/inspectdb.py`, the `Command.handle_inspection`
generator) reverse-engineers Python model classes from an existing database
schema. For each database column that participates in a foreign-key
relationship it emits a relation field (`ForeignKey` or `OneToOneField`).

Today, when a foreign key in the database references a *specific* column of the
target table that is **not** that table's primary key, the generated model
silently drops that information: the relation is emitted as if it targeted the
target table's primary key. For a schema such as

```
CREATE TABLE foo ( id serial primary key, other_id int UNIQUE);
CREATE TABLE bar (
    id serial primary key, other_id int,
    constraint myconst FOREIGN KEY(other_id) references foo(other_id)
);
```

the generated field for `bar.other_id` points at `foo` generally rather than at
`foo(other_id)`, which is a different (and incorrect) relation.

The goal is to make `inspectdb` faithfully reproduce the referenced column: when
a relation points at a non-primary-key column of the target table, the generated
relation field must record the referenced column explicitly (via the standard
`to_field` keyword argument), while leaving every other aspect of the generated
output — relation kind selection, `self` references, primary-key-targeting
relations, and all non-relation field handling — unchanged.

The behavior described here is scoped to the relation-handling block of the
per-column loop inside `Command.handle_inspection`, which relies on the database
introspection API (`connection.introspection.get_primary_key_column`) to learn
the primary-key column of a referenced table.

## Requirement 1: Emit an explicit target column for foreign keys to a non-primary-key column

**User story:** As a developer running `inspectdb` against a legacy database, I
want a foreign key that references a specific non-primary-key column to be
generated with that column recorded explicitly, so that the generated model
describes the same relationship the database actually enforces.

**Acceptance criteria**

1. WHEN `inspectdb` generates a plain foreign-key relation field for a column
   and the referenced column of the target table is not that target table's
   primary-key column, THEN the command SHALL include, in the generated field
   definition, a `to_field` keyword argument whose value is the name of the
   referenced column.
2. The system SHALL determine the target table's primary-key column by
   introspecting the *referenced* table (not the table currently being
   processed) via the database introspection layer.
3. WHEN the introspection layer reports no primary-key column for the referenced
   table (an absent/empty result), THEN the command SHALL NOT add a `to_field`
   keyword argument to the generated field.
4. WHEN the referenced column is identical to the referenced table's
   primary-key column, THEN the command SHALL NOT add a `to_field` keyword
   argument to the generated field.
5. The value emitted for the `to_field` keyword argument SHALL be the referenced
   column name exactly as introspected from the foreign-key relationship, and
   SHALL be rendered as a string literal in the generated field definition.

## Requirement 2: Restrict the explicit target column to plain foreign-key relations

**User story:** As a developer, I want the explicit target-column behavior to
apply only to ordinary foreign keys, so that one-to-one relations continue to be
generated exactly as before.

**Acceptance criteria**

1. IF the relation column carries a unique constraint or is the current table's
   primary key (so the relation is generated as a one-to-one relation), THEN the
   command SHALL NOT add a `to_field` keyword argument, regardless of the
   referenced table's primary-key column.
2. The system SHALL continue to select the one-to-one relation kind when the
   column is unique or is a primary key, and the plain foreign-key relation kind
   otherwise, with no change to that selection logic.

## Requirement 3: Preserve existing relation-target resolution

**User story:** As a maintainer, I want the existing choice of relation target
(`self` versus the target model) to remain identical, so that adding the
referenced-column behavior does not regress previously correct output.

**Acceptance criteria**

1. WHEN the referenced table is the same as the table currently being
   introspected, THEN the generated relation field SHALL target `self`.
2. WHEN the referenced table differs from the current table, THEN the generated
   relation field SHALL target the model name derived from the referenced table
   name (using the same table-name-to-model-name transformation as before).
3. The system SHALL choose between an already-known model reference and a
   forward string reference for the relation target exactly as it did before
   this change.
4. The system SHALL keep emitting the default on-delete behavior marker for
   generated relation fields, and SHALL keep emitting any pre-existing field
   parameters (such as `db_column`, `blank`, and `null`) unchanged.

## Requirement 4: Do not disturb non-relation fields or unrelated command behavior

**User story:** As a developer, I want columns that are not part of a
relationship, and all other command features, to be generated exactly as before,
so that the fix is limited to relation handling.

**Acceptance criteria**

1. WHEN a column does not participate in a foreign-key relationship, THEN the
   command SHALL generate its field with no `to_field` keyword argument and with
   its field type, parameters, and comment notes unchanged.
2. The system SHALL keep generating the model container class, the `Meta`
   options (including `managed = False` by default and any unique-together
   information), primary-key and unique markers, column-name normalization, and
   the table-subset / stealth-table filtering behavior exactly as before.
3. The system SHALL keep gracefully reporting introspection failures for a table
   as comments and continuing with the remaining tables, rather than crashing.
