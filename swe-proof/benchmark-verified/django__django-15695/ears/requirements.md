# Requirements: Make index-rename migration operation idempotent

## Introduction

The migration operation that renames a database index
(`RenameIndex` in `django/db/migrations/operations/models.py`) can be driven
both forward (apply) and backward (unapply). It supports two ways of
identifying the index to rename: by an explicit `old_name`, or — for an index
that was auto-generated for a `unique_together`/`index_together` set — by the
tuple of `old_fields`.

When such an operation is applied forward, then unapplied (moved backward),
then applied forward again, the forward step must not attempt to rename
an index to a name it already has. Previously, re-applying the forward step in the
unnamed-index case crashed at the database level (for example, PostgreSQL
raised a "relation already exists" error) because the operation issued a rename
from the current name to the same target name.

The goal is to make the forward direction of the operation idempotent: when
the index that would be renamed already carries the intended target name, the
operation must do nothing at the database level, while all existing renaming,
error-reporting, and backward behavior is preserved.

## Requirement 1: Forward rename is a no-op when the index already has the target name

**User story:** As a developer running and re-running migrations, I want an
index-rename step to be safely re-appliable, so that applying it after it has
already taken effect does not error or issue redundant schema changes.

**Acceptance criteria**

1. WHEN the forward direction of the index-rename operation runs and the index
   it would rename already bears the target new name, THEN the operation SHALL
   return without issuing any index-rename statement to the database (no schema
   change that renames or recreates the index is emitted). Any read-only
   introspection performed while resolving the source index is permitted; only
   an index-rename/alter statement is forbidden.
2. WHEN the forward direction resolves the source index and that index's name is
   equal to the operation's target new name, THEN the operation SHALL leave the
   existing index and its name unchanged.
3. WHEN the same forward operation is applied a second time after it has already
   been applied (so the index already carries the target new name), THEN the
   second application SHALL succeed without raising a database error and the
   index SHALL still exist under the target new name.
4. WHEN the source index's name differs from the target new name, THEN the
   operation SHALL still issue exactly one rename that changes the source index
   to the target new name.

## Requirement 2: Idempotency guard applies for both named and unnamed indexes

**User story:** As a developer using either explicitly named indexes or
auto-generated indexes for field tuples, I want the re-application safety to
apply uniformly, so that the operation behaves consistently regardless of how
the source index is identified.

**Acceptance criteria**

1. WHEN the operation identifies the source index by an explicit old name and
   the resolved source index already has the target new name, THEN the forward
   direction SHALL issue no index-rename statement (it SHALL not rename or
   recreate the index).
2. WHEN the operation identifies the source index by a tuple of old fields
   (an auto-generated, unnamed index) and the single matching index already has
   the target new name, THEN the forward direction SHALL issue no index-rename
   statement (it SHALL not rename or recreate the index); any read-only
   introspection needed to resolve that index is permitted.
3. The system SHALL evaluate the "already has the target name" condition using
   the name of the source index that the forward direction actually resolved for
   the current database state.

## Requirement 3: Preserve existing rename, resolution, and error behavior

**User story:** As a maintainer, I want the fix to change only the redundant-rename
case, so that all previously correct behavior of the operation is retained.

**Acceptance criteria**

1. IF the migration is not permitted for the model on the current database
   connection, THEN the operation SHALL keep returning without making any
   change, unchanged from before.
2. WHEN the source index is identified by a tuple of old fields, THEN the
   operation SHALL keep requiring that exactly one existing index matches the
   corresponding columns, and SHALL keep raising an error reporting the wrong
   number of matching indexes when the count is not exactly one.
3. WHEN a rename is warranted (the source index name differs from the target new
   name), THEN the operation SHALL keep renaming from the resolved source index
   to the target index obtained from the destination state.
4. WHEN the operation is moved backward and the source index was identified by a
   tuple of old fields (unnamed index), THEN the backward direction SHALL keep
   being a no-op.
5. WHEN the operation is moved backward and the source index was identified by
   an explicit old name, THEN the backward direction SHALL keep swapping the old
   and new names, performing the forward behavior with the names swapped, and
   then restoring the original names — so a backward followed by a forward
   returns the index to its post-forward name.
6. The system SHALL keep the operation's deconstruction, description, and
   migration-name-fragment behavior unchanged, so that operations still
   round-trip and are still described and named as before.
