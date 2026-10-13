# Requirements: Combine cascading fast-delete queries by related model

## Introduction

When Django emulates `ON DELETE CASCADE` (via `on_delete=models.CASCADE`), the
deletion collector `Collector` (in `django/db/models/deletion.py`) walks the
relations that cascade from the objects being deleted. For relations that meet
the conditions for a "fast delete" — deletion of the related rows in bulk
without fetching them into memory — the collector schedules a bulk delete
queryset instead of loading and deleting the objects one by one.

Previously, each qualifying cascading relation was scheduled as its own bulk
delete. When a single related model is reached from the deleted model through
more than one relation (i.e. it references the deleted model through several
columns), this produced one bulk `DELETE` query per column, e.g.

```
DELETE FROM entry WHERE created_by_id IN (...)
DELETE FROM entry WHERE updated_by_id IN (...)
```

The goal is to combine such per-column bulk deletes that target the SAME related
model into a single query using a disjunction (OR) of the per-column lookups,
reducing the number of database roundtrips:

```
DELETE FROM entry WHERE created_by_id IN (...) OR updated_by_id IN (...)
```

The behavior is localized to `Collector.collect`, `Collector.related_objects`,
and `Collector.get_del_batches` in `django/db/models/deletion.py`, and to the
`related_objects` override in the admin's nested-deletion collector
(`django/contrib/admin/utils.py`). All existing deletion semantics — which rows
are deleted, the returned deletion counts, and every `on_delete` handler — must
be preserved.

## Requirement 1: Combine fast-delete operations that target the same related model

**User story:** As a developer deleting a record that cascades to a related
table through several foreign keys, I want the cascading bulk deletions of that
table combined into one query, so that deleting an object issues fewer database
roundtrips.

**Acceptance criteria**
1. WHEN a cascading delete collects the relations that qualify for fast
   deletion, THEN the collector SHALL group those qualifying relations by their
   target related model and schedule at most one fast-delete operation per
   distinct target related model.
2. WHEN two or more qualifying fast-delete relations reach the same related
   model through different join columns, THEN the collector SHALL schedule a
   single fast-delete operation for that model that matches rows related through
   ANY of those columns (a disjunction / OR of the per-column lookups), instead
   of one operation per column.
3. WHEN an object is deleted and its cascade reaches a single related model
   through exactly two qualifying fast-delete columns (and no other work is
   required), THEN the total number of database queries issued SHALL be two: one
   combined bulk delete for that related model and one delete for the object
   itself.
4. The rows removed by the combined fast-delete operation SHALL be exactly the
   union of the rows that the previously separate per-column operations would
   have removed.
5. WHEN a target related model is reached through only one qualifying
   fast-delete relation, THEN the collector SHALL still schedule exactly one
   fast-delete operation for that model.

## Requirement 2: Collect related objects across multiple relation fields with OR semantics

**User story:** As part of the collector, I want to fetch the related rows for a
set of relation fields at once, so that a single queryset represents every row
reachable through any of those fields.

**Acceptance criteria**
1. WHEN `Collector.related_objects` is asked for the rows of a related model
   reachable from a given set of objects through one or more relation fields,
   THEN it SHALL return a queryset of that related model whose filter matches
   instances related through ANY of the supplied fields (the OR of each field's
   `<field name>__in` lookup over the given objects).
2. The returned queryset SHALL be produced from the related model's base manager
   bound to the collector's configured database alias.
3. WHEN exactly one relation field is supplied, THEN the returned queryset SHALL
   select the same rows as filtering that single field's `<field name>__in`
   lookup over the objects.
4. The admin nested-deletion collector's `related_objects` override
   (`django/contrib/admin/utils.py`) SHALL remain consistent with this calling
   convention and SHALL apply `select_related` for every supplied relation
   field's name.

## Requirement 3: Size deletion batches across all supplied relation fields

**User story:** As the collector, I want batch sizing to account for all the
columns a combined delete touches, so that combined operations still respect the
database's parameter limits.

**Acceptance criteria**
1. WHEN `Collector.get_del_batches` splits objects into batches for one or more
   relation fields, THEN it SHALL compute the batch size from the connection's
   `bulk_batch_size` using the names of all the supplied fields.
2. WHEN the number of objects does not exceed the computed batch size, THEN
   `get_del_batches` SHALL return the objects as a single batch.
3. WHEN the number of objects exceeds the computed batch size, THEN
   `get_del_batches` SHALL split the objects into consecutive batches no larger
   than that size, together covering every object exactly once and preserving
   order.

## Requirement 4: Preserve existing deletion behavior and counts

**User story:** As a user of Django's ORM, I want deletion to keep behaving
exactly as before aside from the reduced query count, so that no existing
deletion semantics regress.

**Acceptance criteria**
1. The set of database rows removed by a delete, and the total count plus
   per-model breakdown returned by the delete, SHALL be unchanged from the prior
   behavior for every delete.
2. WHEN a relation's `on_delete` is `DO_NOTHING`, THEN the collector SHALL take
   no cascade action for that relation.
3. The collector SHALL continue to honor every `on_delete` handler
   (CASCADE, SET_NULL, SET_DEFAULT, SET, PROTECT, DO_NOTHING) with the same
   observable effects — cascaded deletions, field updates to null/default/value,
   and raising a protection error — as before this change.
4. WHEN a related model does NOT qualify for fast deletion, THEN the collector
   SHALL continue to collect its objects (deferring non-referenced fields where
   applicable) and dispatch them to the relation's `on_delete` handler as before,
   rather than scheduling a fast delete.
5. Fast deletion of many-to-many relations, reverse many-to-many relations,
   model inheritance chains, and `keep_parents` deletions SHALL continue to
   behave as before.
6. WHEN a queryset selected for fast deletion matches no rows, THEN the delete
   SHALL not issue any additional update query for it.
7. WHEN a single object or queryset qualifies for fast deletion as a whole,
   THEN the collector SHALL continue to fast-delete it in a single bulk
   operation.
