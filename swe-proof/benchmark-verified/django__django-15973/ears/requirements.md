# Requirements: Correct migration dependency for a many-to-many "through" model in another app

## Introduction

When Django's migration autodetector creates a relational field, it must record
the ordered list of migration *dependencies* for that field: the other models
that have to be created before the field can be added. This logic lives in
`MigrationAutodetector._get_dependencies_for_foreign_key` in
`django/db/migrations/autodetector.py`, which uses the helper
`resolve_relation` in `django/db/migrations/utils.py` to turn each model
reference into an `(app_label, object_name)` pair.

A relational field can produce two dependencies:

* the **target** dependency — the model the relation points at (or, for a field
  tied to a swappable setting, a dependency keyed by that setting); and
* when the relation routes through an explicit intermediary model (a
  many-to-many field with a `through` argument), an **additional** dependency on
  that intermediary "through" model.

The defect: while the target dependency was resolved from the field's target
reference, the *through* dependency was mistakenly resolved from the **same
target reference** rather than from the field's own through reference. As long
as the through model happened to live in the same app as the target model, the
resolved app label coincided and the wrong reference went unnoticed. But when
the many-to-many field, its target model, and its `through` model are declared
in three separate apps, the intermediary dependency was resolved against the
target model instead of the through model — so it named the wrong app. The
resulting migration graph omitted the dependency on the app that actually
defines the through model, producing an incorrect ordering (and, downstream, an
`AttributeError` when a create-model operation dereferences a still-unresolved
string reference during `migrate`).

The goal is to make the intermediary dependency be derived from the field's own
`through` model reference, so that the created migration for a many-to-many
field always depends on both the target model's app and the through model's app,
regardless of how the three models are distributed across apps — while leaving
every other dependency-construction behavior unchanged.

## Requirement 1: Resolve the through dependency from the field's own through reference

**User story:** As a Django developer who declares a many-to-many field whose
`through` model lives in a different app from both the field's model and the
field's target model, I want `makemigrations` to record the migration dependency
on the through model's app, so that migrations apply in a correct order and
`migrate` does not fail.

**Acceptance criteria**

1. WHEN the autodetector computes the dependencies for a relational field that
   specifies an intermediary ("through") model, THEN it SHALL append exactly one
   additional dependency that is resolved from the field's own through model
   reference (the value identifying the through model on the field's remote
   field), and SHALL NOT resolve that additional dependency from the field's
   target model reference.
2. WHEN the through model reference is a string of the form
   `"app_label.ModelName"`, THEN the appended intermediary dependency SHALL name
   that through model's `app_label` and object name — even when the through
   model's app differs from the target model's app and from the app that owns the
   field.
3. WHEN a many-to-many field, its target model, and its through model are each
   declared in three different apps, THEN the migration that adds that
   many-to-many field SHALL depend on the app that defines the target model AND
   on the app that defines the through model (each on that app's relevant
   migration), so that both referenced models are created before the field is
   added.
4. The resolution of a model reference to an `(app_label, object_name)` pair
   SHALL use the field's owning model's app label and name as the scope for
   unscoped or recursive references, and SHALL apply this resolution
   consistently to the through model reference as it does to the target model
   reference.

## Requirement 2: Preserve the target dependency and the two-entry shape

**User story:** As a maintainer, I want the target dependency and the overall
structure of the dependency list to stay exactly as before, so that only the
mis-resolved through dependency changes.

**Acceptance criteria**

1. The autodetector SHALL always produce the target dependency as the first
   entry of the dependency list: for a field tied to a swappable setting, a
   dependency keyed by that setting; otherwise the field's target model
   reference resolved in the owning model's scope.
2. IF the relational field specifies no intermediary ("through") model, THEN the
   dependency list SHALL contain only the target dependency and SHALL NOT gain a
   second entry.
3. WHEN the relational field specifies an intermediary model, THEN the
   dependency list SHALL contain exactly two entries — the target dependency
   followed by the intermediary dependency — and no more.
4. The change to how the intermediary dependency is resolved SHALL NOT alter the
   target dependency's value in any case.

## Requirement 3: Preserve existing many-to-many and through-model behavior (regression protection)

**User story:** As a maintainer, I want every previously working arrangement of
many-to-many and through models to keep generating the same migrations and
dependencies, so that the fix is limited to the cross-app through case.

**Acceptance criteria**

1. WHEN a many-to-many field with a `through` model is defined such that the
   through model resides in the same app as the target model (or all models
   share one app), THEN the autodetector SHALL continue to generate the same
   migrations and the same dependencies it did before, since the resolved
   intermediary app label is unchanged in that arrangement.
2. WHEN a model with a many-to-many field that specifies a `through` model is
   created, THEN the autodetector SHALL still emit the create-model and
   add-field operations for that model together with the create-model operations
   for the referenced models, ordered so that referenced models are created
   before the field that depends on them.
3. The autodetector SHALL keep producing, for a plain relational field without a
   through model, a single target dependency resolved exactly as before.
4. The many-to-many field's own attributes recorded in the generated operation
   (the field name and the referenced target model) SHALL be unchanged by this
   fix; only the computed migration dependency on the through model's app is
   corrected.
