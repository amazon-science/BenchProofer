# Requirements: Optimize cascade-deletion collection to fetch only required columns

## Introduction

When Django deletes objects, `Collector.collect` in
`django/db/models/deletion.py` walks the graph of related objects that a
cascade must visit. For each cascading relation it builds a queryset of the
related objects (via `Collector.related_objects`) and, unless those objects can
be fast-deleted, materialises them so the relation's `on_delete` handler can run.

Historically that queryset loaded **every** column of each related row, even
though the deletion machinery only needs the columns that other relations point
at (their identity / target columns). Loading the remaining columns is pure
overhead and can even surface column values the caller never asked for — for
example a text column containing bytes that cannot be decoded, which raises an
error during a delete that never needed that column at all.

The goal is to narrow the columns loaded for these related-object fetches to
exactly the columns that are actually referenced, while preserving deletion
correctness: the same objects must still be collected and deleted, cascades and
`on_delete` handlers must still fire, deletion-time signal listeners must still
observe complete objects, and existing fast-delete behaviour must be unchanged.

The affected code is `Collector.collect` (the `collect_related` field-selection
arm that fetches related objects before invoking the `on_delete` handler),
`Collector.can_fast_delete`, and a small internal signal-detection check on the
`Collector`, all in `django/db/models/deletion.py`.

## Requirement 1: Narrow columns loaded for cascade-related objects

**User story:** As a developer running a `.delete()` that cascades, I want
Django to fetch only the columns it actually needs from related tables, so that
deletion is cheaper and never fails while decoding a column value that the
deletion does not require.

**Acceptance criteria**

1. WHEN `Collector.collect` fetches the related objects for a cascading relation
   and those objects cannot be fast-deleted, THEN the collector SHALL decide
   which columns of the related objects to load before invoking the relation's
   `on_delete` handler.
2. IF the fetched related-objects queryset does not already pull in further
   relations eagerly (its `select_related` is not in effect) AND the related
   model has no deletion-time signal listeners registered (see Requirement 2),
   THEN the collector SHALL restrict the queryset to load only the referenced
   columns rather than the full row.
3. The referenced columns SHALL be the target/identity column names that the
   related model's candidate cascade relations point at — that is, the attribute
   names of the foreign related fields gathered across every relation that may
   itself cascade from the related model — with duplicate column names removed.
4. IF the fetched related-objects queryset already pulls in further relations
   eagerly (its `select_related` is in effect), THEN the collector SHALL load
   the full set of default columns for those related objects, unchanged.
5. IF the related model has deletion-time signal listeners registered (see
   Requirement 2), THEN the collector SHALL load the full set of default columns
   for those related objects, unchanged, so that the listeners observe complete
   objects.
6. The narrowing of columns SHALL apply only to the queryset used to fetch the
   related objects for the `on_delete` handler; it SHALL NOT change which
   objects are selected, only which columns of those objects are loaded.

## Requirement 2: Detect deletion-time signal listeners on a model

**User story:** As a maintainer, I want the collector to know when a model has
delete-time signal listeners, so that objects for such models are always fetched
in full and listeners see every column.

**Acceptance criteria**

1. The collector SHALL provide an internal check that reports whether a given
   model has any deletion-time signal listeners registered.
2. WHEN that check is evaluated for a model, THEN it SHALL report positively IF
   the model has any `pre_delete` listeners registered OR any `post_delete`
   listeners registered, and negatively otherwise.
3. The signal check that governs column narrowing (Requirement 1) SHALL consider
   only `pre_delete` and `post_delete` listeners; it SHALL NOT treat
   `m2m_changed` listeners as forcing a full-column fetch.

## Requirement 3: Preserve deletion correctness and cascade semantics

**User story:** As a user relying on `.delete()`, I want the optimization to
change nothing about which objects are deleted, so that my data integrity is
preserved.

**Acceptance criteria**

1. WHEN related objects are collected for a cascading relation, THEN the
   relation's `on_delete` handler SHALL still be invoked with those related
   objects whenever the fetched queryset is non-empty, exactly as before.
2. IF the fetched related-objects queryset is empty, THEN the collector SHALL
   NOT invoke the `on_delete` handler for that relation.
3. The system SHALL continue to collect and delete the same set of objects for
   any deletion, regardless of whether column narrowing was applied.
4. The system SHALL continue to honour `on_delete` behaviours (CASCADE,
   SET_NULL, SET_DEFAULT, SET, PROTECT, DO_NOTHING) with the same outcomes as
   before, including relations that are nullable, self-referential, or reach
   models through inheritance.
5. WHILE a `pre_delete` or `post_delete` listener is connected for a model whose
   instances are being collected, the collector SHALL make complete instances
   available to that listener.

## Requirement 4: Preserve fast-delete behaviour

**User story:** As a user, I want the existing fast-delete fast path to keep
working, so that simple deletions remain efficient and correct.

**Acceptance criteria**

1. WHEN `Collector.can_fast_delete` determines whether a set of objects can be
   fast-deleted, THEN it SHALL return false IF the model has any `pre_delete` or
   `post_delete` listeners registered.
2. The system SHALL continue to fast-delete objects in the same situations as
   before for foreign-key relations, many-to-many relations, reverse
   many-to-many relations, querysets, large batches, inherited models, and
   self-referential no-update cases.
3. WHEN an object set is eligible for fast deletion, THEN the collector SHALL
   add it to the fast-delete set instead of loading its related objects for an
   `on_delete` handler.
