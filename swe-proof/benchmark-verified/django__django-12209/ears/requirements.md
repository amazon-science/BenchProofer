# Requirements: Preserve update-on-save for verbatim saves with an explicit primary key

## Introduction

Django's ORM save path (`django.db.models.base.Model.save_base` →
`Model._save_table`) contains a query-reduction optimization: when a brand-new
instance is being added and its primary-key field carries a `default`, the ORM
skips the speculative `UPDATE` and goes straight to an `INSERT`, because a
freshly created instance is not expected to already exist in the database.

This optimization regressed the behavior of verbatim/replay saves — the saves
performed by the deserialization/fixture-loading framework (e.g. the `loaddata`
management command). When a fixture (or any deserialized object) carries an
**explicit** primary-key value and that primary-key field happens to have a
default, the optimization forced a second `INSERT` for an object that already
exists, so re-loading the fixture failed with a duplicate-key error instead of
updating the existing row.

The goal is to restrict the "skip the UPDATE and force a fresh INSERT"
optimization so it does **not** apply to verbatim/replay saves, while leaving
the optimization intact for ordinary (non-verbatim) saves. Behavior is
localized to the fresh-insert routing decision inside `Model._save_table`
(the "skip an UPDATE when adding an instance whose primary key has a default"
block and the subsequent update-attempt guard). The change must also keep
model serialization round-trips working for models whose primary-key field has
a default.

## Requirement 1: Verbatim saves with an explicit primary key attempt an UPDATE first

**User story:** As a developer re-loading a fixture that contains objects that
already exist, I want the load to update the existing rows instead of failing,
so that loading the same fixture more than once is idempotent and does not raise
a duplicate-key error.

**Acceptance criteria**

1. WHEN `Model._save_table` is invoked for a verbatim/replay save (the mode used
   by the deserialization/fixture-loading framework, i.e. the `raw` save path),
   THEN the routing decision SHALL NOT force a fresh insert on the sole grounds
   that the instance is being added and its primary-key field has a default.
2. WHEN a verbatim/replay save is performed for an instance that is being added,
   carries a primary-key value, is not already being force-inserted by the
   caller, and whose primary-key field has a default, THEN `Model._save_table`
   SHALL first attempt an in-place `UPDATE` of the row identified by that
   primary key.
3. IF that in-place `UPDATE` matches an existing row, THEN `Model._save_table`
   SHALL treat the save as an update and SHALL NOT additionally issue an
   `INSERT`.
4. IF that in-place `UPDATE` matches no existing row, THEN `Model._save_table`
   SHALL fall back to issuing an `INSERT`, so that a verbatim save of a
   not-yet-existing object still creates it.

## Requirement 2: Ordinary new-instance saves keep the fresh-insert optimization

**User story:** As a developer creating new objects whose primary-key field has
a default, I want the ORM to keep skipping the redundant `UPDATE`, so that
object creation stays a single `INSERT` query.

**Acceptance criteria**

1. WHEN a non-verbatim save adds a brand-new instance whose primary-key field
   has a default and the caller has not requested a forced insert, THEN
   `Model._save_table` SHALL force a fresh insert and SHALL NOT attempt a
   speculative `UPDATE` before it.
2. The system SHALL continue to force a fresh insert whenever the caller
   explicitly requests one (`force_insert`), independent of the verbatim/replay
   distinction.
3. IF a save requests a forced update or specifies update-fields while the
   instance has no primary-key value, THEN `Model._save_table` SHALL raise an
   error rather than silently inserting.
4. The system SHALL preserve the pre-existing routing for all other input
   combinations of (verbatim, force-insert, being-added, primary-key-has-default,
   primary-key-set): only verbatim saves that would otherwise have been forced
   to a fresh insert purely by the default-primary-key optimization change
   behavior; every other combination decides exactly as before.

## Requirement 3: Serialization round-trip for models whose primary key has a default

**User story:** As a developer using Django's serialization framework on a model
whose primary-key field has a default, I want an object to survive a
serialize-then-deserialize round trip and to be re-loadable, so that dumping and
loading such data works and repeated loads do not error.

**Acceptance criteria**

1. WHEN an instance of a model whose primary-key field has a default is
   serialized and then deserialized and saved through the verbatim/replay save
   path, THEN the deserialized object SHALL be persisted with the same
   primary-key value it was serialized with.
2. WHEN the same serialized data is loaded a second time for an object that
   already exists, THEN the load SHALL update the existing row and SHALL NOT
   fail with a duplicate primary-key error.
3. The system SHALL keep every other model data type serializing and
   deserializing exactly as before this change, so that the routing adjustment
   introduces no regression in the serialization round-trip behavior of models
   whose primary key does not have a default.
