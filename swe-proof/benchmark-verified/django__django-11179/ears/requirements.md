# Requirements: Clear primary key after deleting a dependency-free model instance

## Introduction

When a model instance is deleted through Django's ORM, the deletion machinery in
`django.db.models.deletion` (the `Collector.delete` method) removes the row(s)
from the database and, as an in-memory side effect, resets the primary-key
attribute of every deleted instance to `None`. This reset signals that the
in-memory object no longer corresponds to a stored row.

`Collector.delete` contains an optimized fast path for the simplest possible
case: a single collected instance of a single model that has no dependent
relations and therefore qualifies for a direct single-row deletion
(`Collector.can_fast_delete` returns true). On this fast path the method issues
the delete and returns immediately, bypassing the general-path bookkeeping that
clears primary keys. As a result, deleting a dependency-free instance left its
primary-key attribute populated with the now-stale value, inconsistent with the
behavior for every other deletion.

The goal is to make the fast path clear the deleted instance's primary key just
like the general path, so that after any `delete()` call the in-memory instance
reports no primary key, while preserving the count/return semantics of both
paths and all existing deletion behaviors.

## Requirement 1: Clear the primary key on the fast-delete path

**User story:** As a developer using the ORM, I want the primary-key attribute
of a deleted dependency-free instance to be cleared, so that the in-memory
object consistently reflects that it no longer exists in the database.

**Acceptance criteria**

1. WHEN a single collected instance of a single model qualifies for fast
   deletion (`Collector.can_fast_delete` returns true) and is deleted via the
   collector's fast path, THEN the deletion machinery SHALL set that instance's
   primary-key attribute to `None`.
2. WHEN a dependency-free model instance is deleted through the model's
   `delete()` method, THEN, after the call returns, the deletion machinery SHALL
   leave the instance's primary-key attribute equal to `None`.
3. The system SHALL clear the primary-key attribute using the model's actual
   primary-key attribute name, so that models whose primary key is not literally
   named `id` (custom or renamed primary keys) also have the correct attribute
   reset to `None`.
4. WHEN the fast path clears the primary key, THEN the deletion machinery SHALL
   perform the reset after the database delete has been issued, so that a
   failure of the delete operation does not leave the instance reporting a
   cleared key for a row that still exists.

## Requirement 2: Preserve fast-path count and return semantics

**User story:** As a developer relying on the return value of `delete()`, I want
the fast path to keep reporting the same deletion counts, so that adding the
primary-key reset does not change any other observable result.

**Acceptance criteria**

1. WHEN a dependency-free instance is deleted via the fast path, THEN the
   deletion machinery SHALL return the total number of deleted objects together
   with a per-model-label mapping of deletion counts, exactly as before the
   primary-key reset was introduced.
2. The system SHALL leave the number of database operations performed by the
   fast path unchanged; clearing the primary key SHALL be an in-memory
   attribute assignment that issues no additional query.
3. IF the collected work does not match the single-instance, single-model,
   fast-deletable case, THEN the deletion machinery SHALL NOT take the fast path
   and SHALL instead follow the general deletion path.

## Requirement 3: Preserve existing deletion behaviors

**User story:** As a maintainer, I want all previously correct deletion
behaviors to keep working, so that the fix is a strict addition rather than a
regression.

**Acceptance criteria**

1. The system SHALL continue to clear the primary-key attribute to `None` on
   every deleted instance handled by the general (non-fast) deletion path,
   across all collected models.
2. The system SHALL continue to apply queued field updates (for example,
   setting related fields to null or to a default value) to the in-memory
   related instances after deletion.
3. WHEN instances are deleted through a queryset or in bulk, THEN the deletion
   machinery SHALL return the correct total count and per-model-label count
   mapping.
4. WHEN pre-delete and post-delete signals are sent during deletion, THEN the
   deletion machinery SHALL continue to send them for non-auto-created models,
   preserving their existing ordering relative to parent objects.
5. The system SHALL continue to honor the configured on-delete behaviors
   (cascade, set null, set default, set value, protect, do nothing) for related
   objects without regression.
6. WHEN a fast-deletable instance is deleted, THEN the deletion machinery SHALL
   still correctly determine fast-deletability so that the fast path is taken
   only for genuinely dependency-free single instances.
