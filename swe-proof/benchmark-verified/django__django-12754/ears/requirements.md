# Requirements — django migration autodetector ordering for fields moved onto a new subclass

## Introduction

When Django's migration autodetector (`MigrationAutodetector` in
`django/db/migrations/autodetector.py`) compares two project states, it emits a
set of schema operations together with *ordering dependencies* that fix the
relative order in which those operations must run.

There is a modeling refactor that moves a field from a base model onto a
brand-new model that inherits from that base, all in a single change. Concretely
the "before" state has a base model that declares a field, and the "after" state
has that base model no longer declaring the field while a new model that
inherits from the base (a dotted `"app_label.ModelName"` base reference) now
declares a field of the same name.

For such a change the autodetector produces a `CreateModel` operation for the new
subclass and a `RemoveField` operation on the base. Previously these were
emitted so that the model was created *before* the field was removed from the
base. Applying the migration in that order fails at runtime, because while the
subclass is being created the base still declares the same-named field, which
clashes with the inherited field.

The goal is to make the autodetector record the correct ordering dependency so
that the removal of the base field is scheduled *before* the creation of the new
subclass, while leaving all other created-model ordering dependencies unchanged.
The behavior of interest lives in the per-created-model dependency construction
inside `MigrationAutodetector.generate_created_models`, and is consumed by
`MigrationAutodetector.check_dependency` when the operations are ordered.

## Requirement 1: Remove a moved base field before creating the inheriting model

**User story:** As a developer moving a field from a base model onto a new
model that subclasses it in the same change, I want `makemigrations` to order
the generated operations so they can actually be applied, so that running the
migration does not raise a field-clash error.

**Acceptance criteria**

1. WHEN a new model is detected whose bases include a dotted
   `"app_label.ModelName"` reference, AND that referenced base model is present
   in both the previous state and the current state, AND a field name is
   declared by the base in the previous state, is no longer declared by the base
   in the current state, and is declared by the new model itself, THEN the
   autodetector SHALL record, for the new model's creation, an ordering
   dependency on the *removal* of that field from the referenced base model.
2. WHEN such a moved field is detected, THEN the generated `RemoveField`
   operation on the base model for that field SHALL be ordered before the
   `CreateModel` operation for the new inheriting model.
3. WHEN the autodetector is asked for the changes of a base model that loses a
   field and a new model that inherits from that base and declares a field of
   the same name, THEN it SHALL produce exactly one migration for the affected
   application whose operation sequence begins with the removal of the field from
   the base model followed by the creation of the new inheriting model.
4. The removal operation described above SHALL target the base model and the
   moved field name; the creation operation SHALL target the new inheriting
   model.

## Requirement 2: Restrict the new dependency to genuinely moved fields

**User story:** As a maintainer of the autodetector, I want the new ordering
dependency to be added only for fields that are actually removed from a base and
re-declared on the subclass, so that unrelated model creations keep their
existing behavior.

**Acceptance criteria**

1. IF a field is still declared by the referenced base model in the current
   state, THEN the autodetector SHALL NOT record a base-field-removal dependency
   for that field on the new model's creation.
2. IF a field that the new model declares was never declared by the referenced
   base model in the previous state, THEN the autodetector SHALL NOT record a
   base-field-removal dependency for that field.
3. IF a field is removed from the referenced base model but is NOT declared by
   the new inheriting model, THEN the autodetector SHALL NOT record a
   base-field-removal dependency for that field on the new model's creation.
4. IF either the previous-state record or the current-state record of a dotted
   base is unavailable, THEN the autodetector SHALL NOT record any
   base-field-removal dependency for that base on the new model's creation.
5. IF a base of the new model is not a dotted `"app_label.ModelName"` string
   reference, THEN it SHALL contribute no base-field-removal dependency.

## Requirement 3: Coalesce a shared moved field across multiple new subclasses

**User story:** As a developer, I want a field removed from a base and moved onto
more than one new subclass in the same change to be removed once, so that the
migration is not built with conflicting or duplicated removals of the same base
field.

**Acceptance criteria**

1. WHEN a single field is removed from a base model and re-declared by two or
   more new models that inherit from that base in the same change, THEN the
   autodetector SHALL generate a single removal of that field from the base
   model, not one per subclass.
2. WHEN such a shared moved field is detected, THEN the single base-field
   removal SHALL be ordered before the creation of every new subclass that
   re-declares it.

## Requirement 4: Preserve existing created-model ordering dependencies

**User story:** As a maintainer, I want all previously-correct ordering behavior
of the autodetector to be unchanged, so that adding the new dependency does not
regress existing migration generation.

**Acceptance criteria**

1. The autodetector SHALL continue to record, for each newly-created model, a
   dependency on the removal of any prior proxy version of that same model.
2. WHEN a new model inherits from a dotted `"app_label.ModelName"` base, THEN
   the autodetector SHALL continue to record a dependency on the *creation* of
   that base model, so that bases are created before the models that inherit
   from them.
3. WHEN a new model's primary key is a relation to another model, THEN the
   autodetector SHALL continue to record a dependency on the creation of the
   model at the other end of that relation.
4. The autodetector SHALL keep detecting the creation of new models, the
   deletion of removed models, and the removal of fields with their existing
   behavior when none of the moved-field conditions in Requirement 1 apply.
5. WHEN a model that participates in multi-table inheritance is removed and no
   field is moved onto a new subclass, THEN the autodetector SHALL keep its
   existing operation set for that change unchanged.
