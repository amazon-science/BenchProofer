# Requirements: ImageField should only install its post-initialization dimension handler when it has dimension fields

## Introduction

`ImageField` (in `django/db/models/fields/files.py`) optionally mirrors the
width and height of a stored image into two companion model attributes, named
by its `width_field` and `height_field` options. To keep those attributes in
sync, `ImageField` registers a handler (`update_dimension_fields`) on the
model's `post_init` signal when the field is attached to a model
(`contribute_to_class`). This handler fires once for every model instance that
is initialized.

When a project uses `ImageField` **without** configuring `width_field` or
`height_field`, the handler has nothing to do — it returns immediately — yet it
is still connected and still invoked on every instance initialization. On
model-heavy code paths this signal dispatch dominates instance-initialization
cost even though it performs no useful work.

The goal is to avoid connecting the handler at all when it can have no effect,
while preserving the exact dimension-syncing behavior for fields that *are*
configured with a width and/or height field, and for abstract models (which
never connect the handler). This affects
`ImageField.contribute_to_class` and `ImageField.update_dimension_fields`.

## Requirement 1: Do not install the dimension handler when no dimension field is configured

**User story:** As a developer using `ImageField` without `width_field` or
`height_field`, I want no per-instance dimension handler attached to my model,
so that initializing model instances is not slowed by a no-op signal handler.

**Acceptance criteria**

1. WHEN an `ImageField` is attached to a concrete (non-abstract) model and the
   field configures neither a width field nor a height field, THEN
   `ImageField` SHALL NOT register any `post_init` signal receiver for that
   model as a result of that field.
2. IF an `ImageField` has an empty or unset `width_field` **and** an empty or
   unset `height_field`, THEN the model that the field is attached to SHALL NOT
   appear as the sender of any `post_init` receiver contributed by that field.
3. The system SHALL treat only a non-empty width-field name or a non-empty
   height-field name as reason to install the handler; an unset (`None`) or
   empty-string name SHALL count as "not configured".

## Requirement 2: Install the dimension handler when at least one dimension field is configured

**User story:** As a developer who configures `width_field` and/or
`height_field` on an `ImageField`, I want the width/height attributes to keep
being maintained automatically, so that stored dimensions remain correct.

**Acceptance criteria**

1. WHEN an `ImageField` that configures a non-empty `width_field` and/or a
   non-empty `height_field` is attached to a concrete (non-abstract) model,
   THEN `ImageField` SHALL register its dimension-update handler on that
   model's `post_init` signal.
2. IF only one of `width_field` or `height_field` is configured (the other
   unset), THEN the handler SHALL still be installed.
3. WHEN the handler is installed and a model instance is initialized, THEN the
   configured width and/or height attributes SHALL be updated according to the
   same rules that applied before this change (see Requirement 4).

## Requirement 3: Never install the dimension handler for abstract models

**User story:** As a Django user defining abstract base models, I want no
`post_init` handler bound to abstract models, so that behavior for abstract
models is unchanged.

**Acceptance criteria**

1. IF the model an `ImageField` is being attached to is abstract, THEN
   `ImageField` SHALL NOT register a `post_init` receiver for it, regardless of
   whether `width_field` or `height_field` are configured.

## Requirement 4: Preserve all dimension-syncing behavior for configured fields

**User story:** As a developer relying on automatic width/height maintenance, I
want every existing dimension-update scenario to keep working exactly as
before, so that removing the redundant handler causes no behavioral regression.

**Acceptance criteria (SHALL-keep regressions)**

1. WHEN an image value is supplied to a model instance through the model
   constructor and the field configures dimension fields, THEN the configured
   width and height attributes SHALL be set to the image's dimensions.
2. WHEN an instance is created through the manager's `create()` method with an
   image value, THEN the configured width and height attributes SHALL reflect
   the image's dimensions.
3. WHEN an image value is assigned to the field via attribute assignment or via
   the field file's save method, THEN the configured width and height
   attributes SHALL be updated to the new image's dimensions.
4. WHEN the field's value is assigned `None`, THEN the configured width and
   height attributes SHALL be cleared (set to `None`).
5. WHEN no image is passed at construction time, THEN the configured dimension
   attributes SHALL reflect the absent-image case exactly as before.
6. WHEN an instance is loaded from the database with the dimension attributes
   already populated, THEN those attributes SHALL NOT be recomputed (their
   database-loaded values SHALL be preserved).
7. IF the image field's attribute is deferred (not present in the instance's
   loaded attributes), THEN the dimension-update handler SHALL make no change
   and SHALL NOT force loading of the field.
8. The dimension-update handler SHALL continue to update dimensions when forced
   (as when the descriptor sets a new value with a force flag), including
   correctly handling the case where the field configures no dimension fields
   (making no attribute changes and raising no error).

## Requirement 5: Preserve unrelated ImageField / FileField behavior

**User story:** As a Django user, I want all other `ImageField` and
`FileField` behaviors to remain intact, so that this optimization is
observationally invisible aside from the removed no-op handler.

**Acceptance criteria (SHALL-keep regressions)**

1. The default value of an unassigned `ImageField` SHALL remain an instance of
   the field-file wrapper type.
2. Equality and inequality comparisons of field-file values SHALL continue to
   behave correctly.
3. An `ImageField` value SHALL remain picklable and unpicklable, preserving the
   stored image reference across the round trip.
4. WHEN the underlying file is unavailable, THEN instantiating and accessing the
   field SHALL still succeed as before.
5. WHEN an object whose stored file no longer exists is deleted, THEN deletion
   SHALL succeed.
6. Querying a file field's size SHALL NOT leave the underlying file open.
