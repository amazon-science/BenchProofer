# Requirements: Resolve natural keys against the target database when loading fixtures

## Introduction

When Django loads serialized data (for example via the `loaddata` management
command), the deserializer rebuilds each model instance from its serialized
`data`. For models that support natural keys, the primary key is often omitted
from the serialized data, so Django must look the record up by its natural key.
This work is done by `build_instance(Model, data, db)` in
`django/core/serializers/base.py`.

`build_instance` receives the alias of the database the data is being loaded
into (`db`). When the incoming `data` has no primary key and the model supports
natural keys (its default manager provides `get_by_natural_key` and the model
defines `natural_key`), `build_instance` constructs a throw-away model instance
from `data`, calls its `natural_key()` method to compute the identifying tuple,
and then asks `Model._meta.default_manager.db_manager(db).get_by_natural_key(...)`
for the matching primary key on the target database.

The problem: a model's `natural_key()` may follow a foreign key and include the
related object's natural key (a `natural_key` with `dependencies`, e.g. a
`Book.natural_key()` that returns `(self.title,) + self.author.natural_key()`).
Following that foreign key triggers a database query for the related object. The
throw-away instance built from `data` has not been associated with any database,
so its state carries the *default* database alias, and the related-object lookup
is issued against the default database instead of the target database `db`. When
the referenced data exists only in the target (non-default) database — as during
a `loaddata --database other` — the related object is not found and the load
fails with a `DoesNotExist` (surfaced as a deserialization error). Loading the
same fixture into the default database happens to work only because the lookup
coincidentally hits the right database.

The goal is to make natural-key resolution during deserialization use the target
database `db` consistently, including for any related-object lookups performed
while a model computes its natural key, so that fixtures with foreign-key-based
natural keys load correctly on any database — while leaving all other behavior
of `build_instance` (payload, normal primary keys, missing-record handling)
unchanged.

## Requirement 1: Derive natural keys relative to the target database

**User story:** As a developer loading a fixture into a non-default database, I
want each model's natural key to be computed against that same database, so that
fixtures whose natural keys traverse foreign keys load successfully regardless of
which database I target.

**Acceptance criteria**

1. WHEN `build_instance` processes serialized `data` that has no primary key for
   a model whose default manager provides `get_by_natural_key` and whose model
   class defines `natural_key`, THEN the instance it constructs to compute the
   natural key SHALL be associated with the target database `db` before its
   `natural_key()` method is invoked.
2. WHILE computing a model's natural key, IF the model's `natural_key()` follows
   a foreign key and queries for the related object (for example a
   `natural_key()` that appends the related object's own natural key), THEN that
   related-object query SHALL be issued against the target database `db` rather
   than the default database.
3. WHEN a fixture is loaded into a non-default database and it contains a record
   whose natural key depends on another record present in that same non-default
   database, THEN `build_instance` SHALL resolve the record's natural key without
   raising `DoesNotExist` (or any deserialization error caused by the related
   lookup hitting the wrong database), and the record SHALL be loaded into the
   target database.
4. WHEN the natural key has been computed, THEN `build_instance` SHALL look the
   existing record up via `default_manager.db_manager(db).get_by_natural_key(...)`
   on the target database `db`, and, IF a matching record exists there, SHALL set
   the instance's primary key attribute to that record's primary key coerced
   through the field's `to_python`.

## Requirement 2: Preserve existing `build_instance` behavior (regression protection)

**User story:** As a Django maintainer, I want every other aspect of instance
construction and natural-key lookup to behave exactly as before, so that
single-database loads, models without natural keys, and records with explicit
primary keys are unaffected.

**Acceptance criteria**

1. WHEN the serialized `data` already contains a value for the model's primary
   key attribute, THEN `build_instance` SHALL NOT perform any natural-key lookup
   and SHALL build the instance directly from `data`, leaving that primary key
   value unchanged.
2. IF the model's default manager does not provide `get_by_natural_key`, or the
   model class does not define `natural_key`, THEN `build_instance` SHALL NOT
   attempt a natural-key lookup and SHALL build the instance directly from
   `data`.
3. IF the natural-key lookup on the target database finds no matching record
   (`Model.DoesNotExist`), THEN `build_instance` SHALL leave the primary key
   attribute absent (unchanged) and SHALL return an instance built from the
   original `data` without raising.
4. The system SHALL return a model instance whose field data reflects exactly the
   supplied `data` (the descriptive field values SHALL NOT be altered by the
   natural-key resolution step); only the primary key attribute may be populated,
   and only when a matching record is found.
5. WHEN a fixture whose natural keys traverse foreign keys is loaded into the
   default database, THEN it SHALL continue to load successfully, exactly as
   before this change.
6. The system SHALL continue to resolve natural keys and load fixtures correctly
   for models that use natural keys without foreign-key dependencies, and SHALL
   preserve the existing dependency-ordering behavior by which models whose
   natural keys depend on other models are deserialized after their
   dependencies.
