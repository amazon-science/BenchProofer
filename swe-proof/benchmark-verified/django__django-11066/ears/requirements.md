# Requirements — Content type rename must persist to the migration's own database

## Introduction

When a Django migration renames a model, the content-types framework injects a
follow-up operation (`RenameContentType` in
`django/contrib/contenttypes/management/__init__.py`) that renames the matching
`ContentType` row so its `model` field tracks the new model name. The rename is
performed by `RenameContentType._rename`, which runs against the specific
database connection the migration is executing on (available as
`schema_editor.connection.alias`).

The affected behavior is the persistence of the renamed row. `_rename` reads the
existing row from the migration's database, updates its `model` field, and saves
it inside a `transaction.atomic(using=db)` block. The defect is that the save is
issued without directing it at that database, so `Model.save()` falls back to the
database router's chosen write target. In deployments whose router
sends writes to a different database than the one being migrated, the row is
looked up in one database but the update is attempted against another — the row
to update is absent there, and the write targets the wrong (possibly
nonexistent) database, raising an `OperationalError` / silently failing to
persist the rename.

The goal is that the content-type rename is always persisted to the same
database the migration is running against, independent of any database router
configuration, while preserving the existing lookup, conflict-fallback, and
cache-invalidation behavior.

## Requirement 1: Persist the rename to the migration's own database

**User story:** As an operator running migrations against a specific database
(possibly with a custom database router in effect), I want a renamed model's
content-type row to be updated on that same database, so that renaming a model
does not fail or silently write to the wrong database when the router directs
writes elsewhere.

**Acceptance criteria**

1. WHEN `RenameContentType._rename` renames a content type while executing
   against the database identified by `schema_editor.connection.alias`, THEN it
   SHALL persist the updated row to that same database.
2. WHILE a database router is configured whose write target differs from the
   database the migration is running against, `RenameContentType._rename` SHALL
   still persist the renamed content-type row to the migration's database and
   SHALL NOT persist it to the router's chosen database.
3. WHEN a model rename is migrated forward against a non-default database, THEN
   the content-type row for that app on that same database SHALL afterwards
   carry the new model name and SHALL NOT carry the old model name.
4. WHEN the model rename is subsequently reversed (migrated backward) against
   the same non-default database, THEN the content-type row on that database
   SHALL again carry the old model name and SHALL NOT carry the new model name.
5. The persisted update SHALL be limited to the row's model-name field; other
   content-type rows and other databases SHALL be left unchanged.

## Requirement 2: Look up the content type on the migration's own database

**User story:** As a developer relying on the content-types framework, I want
the rename to locate the existing content-type row on the database being
migrated, so that the correct row is selected before it is updated.

**Acceptance criteria**

1. WHEN `_rename` runs, THEN it SHALL look up the content type by its natural
   key `(app_label, old_model)` on the database identified by
   `schema_editor.connection.alias`.
2. IF no content-type row for `(app_label, old_model)` exists on that database,
   THEN `_rename` SHALL make no change to any database and SHALL return without
   error.
3. IF the content-types framework is not permitted to migrate on that database
   (per the router's `allow_migrate` decision), THEN `_rename` SHALL make no
   change and SHALL return without error.

## Requirement 3: Preserve conflict fallback and cache invalidation

**User story:** As a developer, I want the existing safeguards around a
content-type rename to keep working, so that renames remain safe when a
conflicting row already exists and cached lookups stay correct.

**Acceptance criteria**

1. WHEN persisting the renamed row would collide with an existing row that
   already holds the destination natural key `(app_label, new_model)` on the
   target database (raising an `IntegrityError`), THEN the write SHALL be rolled
   back so that no row is persisted, and the in-memory content-type object's
   model name SHALL be restored to `old_model`.
2. WHILE the rename is being persisted, the save SHALL be wrapped in an atomic
   transaction scoped to the migration's database, so that a failed write leaves
   that database unchanged.
3. WHEN a rename is persisted successfully, THEN the content-type lookup cache
   SHALL be cleared so that a subsequent natural-key lookup does not return the
   stale pre-rename entry.
4. The system SHALL keep renaming content types correctly for the ordinary case
   in which the migration runs against the same database the router would
   choose, matching the behavior prior to this change.
