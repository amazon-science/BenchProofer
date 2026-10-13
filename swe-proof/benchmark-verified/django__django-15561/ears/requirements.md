# Requirements: Field choices are a column-irrelevant attribute when deciding whether to alter a column

## Introduction

When Django applies an `AlterField` migration operation, the schema editor
decides whether the change actually requires a column-level schema alteration.
`BaseDatabaseSchemaEditor._field_should_be_altered(self, old_field, new_field)`
(in `django/db/backends/base/schema.py`) makes this decision: it deconstructs
both the old and new field, discards the keyword arguments that name attributes
which have no bearing on the stored column, and reports that an alteration is
needed only if the (backend-quoted) column name differs or the remaining
deconstructed descriptions still differ.

On backends such as PostgreSQL, changing only a field's set of permitted
`choices` already produces no SQL. On SQLite, the field-alteration path rebuilds
the table (create new table, copy rows, drop old table, rename) whenever
`_field_should_be_altered` reports that a change is required. Because `choices`
was not recognized as a column-irrelevant attribute, a `choices`-only change was
reported as requiring an alteration, so SQLite emitted a full table rebuild for
a change that is transparent to the database.

The goal is to make a field change that touches only column-irrelevant
attributes — `choices` in particular — be recognized as a no-op, so that no
column alteration is performed on any backend (including SQLite), while every
change that genuinely affects the column continues to be applied. The behavior
is localized to `_field_should_be_altered` and the set of attributes it treats
as not affecting the column definition; the SQLite field-alteration path in
`django/db/backends/sqlite3/schema.py` consumes that decision.

## Requirement 1: A choices-only field change requires no column alteration

**User story:** As a developer editing a model field's `choices`, I want the
migration to recognize that nothing about the stored column changed, so that no
schema SQL is generated and, on SQLite, the table is not rebuilt.

**Acceptance criteria**
1. WHEN `_field_should_be_altered` is called with an old field and a new field
   that are identical except that the new field adds, changes, or removes its
   `choices`, THEN it SHALL report that no column-level alteration is required
   (return a falsy result).
2. WHEN a field's `choices` are the only difference between the old and new
   field on SQLite, THEN applying the corresponding `AlterField` operation SHALL
   generate no schema SQL and SHALL NOT rebuild, copy, drop, or rename the
   table.
3. The system SHALL treat `choices` as an attribute that does not affect the
   column definition when comparing the deconstructed old and new fields.

## Requirement 2: Other presentation- and validation-level attributes remain column-irrelevant

**User story:** As a developer changing attributes that do not affect the stored
column, I want migrations to keep treating those changes as no-ops, so that no
unnecessary schema SQL is generated.

**Acceptance criteria**
1. WHEN the only differences between the old and new field are among the
   attributes that govern presentation, validation, form behavior, or Python-
   level relations rather than the stored column — including `blank`,
   `db_column` (when the resolved column name is unchanged), `editable`,
   `error_messages`, `help_text`, `limit_choices_to`, `on_delete`,
   `related_name`, `related_query_name`, `validators`, and `verbose_name` —
   THEN `_field_should_be_altered` SHALL report that no column-level alteration
   is required.
2. The system SHALL keep exposing, on the field class, the collection of
   attribute names that are ignored when deciding whether a field alteration
   affects the column, and this collection SHALL include `choices` alongside the
   attributes named in criterion 1.
3. The system SHALL apply the same set of ignored attributes to both the old and
   the new field's deconstructed keyword arguments before comparing them.

## Requirement 3: Genuine column-affecting changes still require an alteration

**User story:** As a developer changing something that affects the database
column, I want the migration to still apply the change, so that the schema stays
correct.

**Acceptance criteria**
1. WHEN the old and new field differ in the backend-quoted column name, THEN
   `_field_should_be_altered` SHALL report that a column-level alteration is
   required (return a truthy result).
2. WHEN the old and new field differ, after dropping the column-irrelevant
   keyword arguments, in their class path, positional deconstruction arguments,
   or any remaining keyword argument (for example a change to `max_length`,
   `null`, `default`, `db_index`, `unique`, or the field type), THEN
   `_field_should_be_altered` SHALL report that a column-level alteration is
   required.
3. The system SHALL keep applying real field alterations that affect the column,
   including on SQLite where such alterations rebuild the table as before.
4. IF a field change combines a column-irrelevant attribute change (such as
   `choices`) with a change that does affect the column, THEN
   `_field_should_be_altered` SHALL report that a column-level alteration is
   required.
