# Requirements: Recording a squashed (replacement) migration as unapplied

## Introduction

Django's migration machinery lets a single "squash" migration stand in for a
set of earlier migrations. Such a migration carries its own identifier — an
application label together with a migration name — and, in addition, a list of
the identifiers of the earlier migrations it stands in for (its `replaces`
list). When the replaced migration files are still present on disk, the squash
migration and each migration it replaces are all tracked in the recorder's
applied set.

The affected component is `MigrationExecutor.unapply_migration` in
`django/db/migrations/executor.py`, which rolls a migration backwards and then
tells the recorder (`django.db.migrations.recorder.MigrationRecorder`, via its
`record_unapplied(app_label, name)` method) which migration identifiers are no
longer applied.

The problem: when a squash (replacement) migration is rolled back, the executor
records only the identifiers it stands in for as no-longer-applied, and omits
the squash migration's own identifier. As a result the squash migration remains
listed in the applied set even though it has been rolled back, leaving the
recorder in an inconsistent state. This document specifies the behavior of
`unapply_migration` so that rolling back a replacement migration marks both the
replaced identifiers and the migration's own identifier as unapplied, while
preserving the existing behavior for ordinary migrations and for the
apply/forward direction.

## Requirement 1: Rolling back a replacement (squash) migration marks the squash migration itself unapplied

**User story:** As a developer rolling back a squashed migration whose replaced
migration files are still present, I want the squash migration itself to be
marked as no longer applied, so that the recorder's applied set accurately
reflects that the squash migration has been rolled back.

**Acceptance criteria**

1. WHEN `unapply_migration` rolls back a migration whose `replaces` list is
   non-empty, THEN the executor SHALL record the migration's own identifier
   `(migration.app_label, migration.name)` as no-longer-applied by calling the
   recorder's `record_unapplied` for that identifier.
2. WHEN `unapply_migration` rolls back a migration whose `replaces` list is
   non-empty, THEN the executor SHALL, in addition, record every identifier in
   that `replaces` list (each `(app_label, name)` pair) as no-longer-applied.
3. WHEN a migration that stands in for one or more earlier migrations is rolled
   back, THEN after `unapply_migration` returns the migration's own identifier
   SHALL NOT be present in the recorder's set of applied migrations.
4. WHEN a migration that stands in for one or more earlier migrations is rolled
   back, THEN after `unapply_migration` returns none of the replaced
   identifiers SHALL be present in the recorder's set of applied migrations.
5. WHEN recording the no-longer-applied identifiers for a replacement
   migration, THEN the executor SHALL record every replaced identifier before
   recording the migration's own identifier, and SHALL record the migration's
   own identifier exactly once.

## Requirement 2: Rolling back an ordinary (non-replacement) migration is unchanged

**User story:** As a developer rolling back a migration that does not stand in
for any other migration, I want only that migration to be marked unapplied, so
that unrelated migrations are unaffected.

**Acceptance criteria**

1. WHEN `unapply_migration` rolls back a migration whose `replaces` list is
   empty or absent (falsy), THEN the executor SHALL record its own identifier
   `(migration.app_label, migration.name)` as no-longer-applied.
2. WHEN `unapply_migration` rolls back a migration whose `replaces` list is
   empty or absent, THEN the executor SHALL NOT record any identifier other
   than the migration's own identifier as no-longer-applied.
3. The system SHALL treat an absent or empty `replaces` list identically for
   the purpose of deciding which identifiers to mark unapplied.

## Requirement 3: The unapply recording is independent of whether the rollback ran the schema operations

**User story:** As a developer, I want the recorder to be updated whenever a
migration is unapplied — whether or not the backwards schema operations were
actually executed — so that a faked rollback still updates recorded state
consistently.

**Acceptance criteria**

1. WHEN `unapply_migration` is invoked with the fake flag set so that the
   backwards schema operations are skipped, THEN the executor SHALL still
   perform the same `record_unapplied` recording specified in Requirements 1
   and 2 for that migration.
2. IF the migration being rolled back is a replacement migration, THEN the
   requirement to record the migration's own identifier as unapplied SHALL hold
   regardless of the fake flag.

## Requirement 4: The forward (apply) recording behavior is preserved

**User story:** As a developer applying migrations, I want the existing
recording behavior for applying migrations to remain unchanged, so that this
change does not alter how migrations are marked as applied.

**Acceptance criteria**

1. WHEN a replacement migration is applied (moved forward), THEN the executor
   SHALL record each identifier in its `replaces` list as applied.
2. WHEN a migration that stands in for nothing is applied, THEN the executor
   SHALL record only its own identifier `(app_label, name)` as applied.
3. The system SHALL keep marking a replacement migration as applied once all of
   the migrations it stands in for have been applied, including the case where
   applying the replacement itself performed no schema operations.
4. WHEN a squash migration is migrated forward from an empty (zero) state, THEN
   the executor SHALL apply it as a single unit and SHALL NOT separately run
   the individual migrations it replaces.
