# Requirements: propagate a primary key's collation to its foreign keys

## Introduction

When a model field declares an explicit database collation (`db_collation`) and
that field is a primary key (or otherwise unique) referenced by foreign keys in
other models, Django's schema editor must keep the collation of the referencing
columns in step with the collation of the referenced column. On backends where a
foreign key requires the referencing and referenced columns to share a collation
(e.g. MySQL), failing to carry the collation over produces `ALTER TABLE … ADD
CONSTRAINT … FOREIGN KEY` statements that the database rejects.

The affected behavior lives in three places:

- `ForeignKey.db_parameters` in `django/db/models/fields/related.py`, which
  reports the database parameters (type, check, collation) of a relation field.
- `BaseDatabaseSchemaEditor._alter_field` in
  `django/db/backends/base/schema.py`, which decides whether incoming foreign
  keys must be rebuilt and how each referencing column is re-altered.
- `DatabaseSchemaEditor._alter_field` for the SQLite backend in
  `django/db/backends/sqlite3/schema.py`, which decides whether tables holding
  incoming foreign keys must be rebuilt.

The goal: when a referenced column's collation changes, the referencing foreign
key columns are updated to the same collation as part of the same field
alteration, before the foreign key constraints are (re)created, so that the
constraints apply successfully.

## Requirement 1: Foreign key columns report the referenced column's collation

**User story:** As a developer using an explicit `db_collation` on a primary key,
I want the columns of foreign keys pointing at that key to be described with the
same collation, so that the schema tooling can keep them consistent.

**Acceptance criteria**

1. WHEN the database parameters of a relation (foreign-key) field are requested,
   THEN `ForeignKey.db_parameters` SHALL return a mapping that includes a
   collation entry.
2. The collation entry returned by `ForeignKey.db_parameters` SHALL equal the
   collation reported by the database parameters of the field it targets (the
   referenced/target field).
3. IF the referenced target field reports no collation, THEN the collation entry
   returned by `ForeignKey.db_parameters` SHALL be absent-valued (the same
   "no collation" value the target reports) rather than a fabricated collation.
4. The system SHALL continue to report the field's database type and check
   constraint in the same mapping, unchanged from prior behavior.

## Requirement 2: A collation change on a referenced key triggers rebuilding of incoming foreign keys

**User story:** As a developer changing the collation of a referenced primary key
or unique field, I want the schema editor to rebuild the foreign keys that point
at it, so that the referencing columns can be re-collated without a stale
constraint blocking the change.

**Acceptance criteria**

1. WHEN a field that is a primary key (before and after) or unique (before and
   after) is altered on a backend that supports foreign keys, THEN
   `BaseDatabaseSchemaEditor._alter_field` SHALL decide to drop the incoming
   foreign key constraints if the field's type changed OR its collation changed.
2. WHILE the referenced field's collation differs between the old and new field
   definitions, the decision to drop and later recreate the incoming foreign key
   constraints SHALL be taken even when the column's database type is unchanged.
3. IF neither the type nor the collation of the altered field changes, THEN the
   incoming foreign key constraints SHALL NOT be dropped on account of this
   alteration.
4. WHEN incoming foreign keys are dropped because of such a change, THEN those
   foreign key constraints SHALL be recreated after the referencing columns have
   been altered.
5. The system SHALL keep the existing behavior of dropping and recreating
   incoming foreign keys when the referenced column's database type changes.

## Requirement 3: Referencing columns are re-collated when the collation changed

**User story:** As a developer, I want each column that references a re-collated
key to be altered to the new collation, so that the recreated foreign key
constraints match and succeed.

**Acceptance criteria**

1. WHEN `BaseDatabaseSchemaEditor._alter_field` processes each referencing
   relation whose column must be updated, THEN it SHALL compare the referencing
   column's new collation against its old collation.
2. IF a referencing column's collation changed, THEN the schema editor SHALL
   alter that column using the collation-changing alteration (emitting a column
   collation change) rather than the plain type-changing alteration.
3. WHEN a referencing column is altered via the collation-changing branch, THEN
   the schema editor SHALL NOT emit the auxiliary/secondary actions that the
   type-changing alteration would otherwise produce (that branch contributes no
   additional follow-up actions).
4. IF a referencing column's collation did not change, THEN the schema editor
   SHALL alter that column using the existing type-changing alteration, preserving
   prior behavior including any auxiliary actions it produces.
5. The new collation applied to a referencing column SHALL be the collation
   reported by that referencing field's database parameters (i.e. the collation
   propagated from the referenced key per Requirement 1).

## Requirement 4: SQLite table rebuild accounts for collation changes

**User story:** As a developer on SQLite, I want tables holding foreign keys to a
re-collated unique/primary key column to be rebuilt when the collation changes, so
that referencing definitions stay consistent.

**Acceptance criteria**

1. WHEN the SQLite backend's `_alter_field` alters a field that is unique, THEN it
   SHALL rebuild the tables whose foreign keys point at that field if the field's
   database type changed OR its collation changed.
2. IF a unique field's type is unchanged but its collation changed, THEN the
   SQLite backend SHALL still rebuild the tables with foreign keys pointing at
   that field.
3. The system SHALL keep the existing SQLite behavior of rebuilding referencing
   tables when a unique field's database type changes.

## Requirement 5: Preserve unaffected schema-editing behavior

**User story:** As a maintainer, I want the existing migration and schema-editing
operations to keep working, so that adding collation propagation does not regress
other behavior.

**Acceptance criteria**

1. The system SHALL preserve all existing field-alteration behavior — including
   nullability changes, default handling, index creation/removal, unique
   constraint handling, and check constraint handling — unchanged for alterations
   that do not involve a collation change.
2. The system SHALL preserve the existing detection of which models and fields a
   migration operation references (foreign key, many-to-many, through, and
   to-field references), unchanged.
3. WHEN a field alteration involves neither a type change nor a collation change,
   THEN the schema editor SHALL produce the same statements it produced before
   this change.
