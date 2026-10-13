# Requirements: Correct `QuerySet.ordered` for aggregated (GROUP BY) queries

## Introduction

The `ordered` property of `QuerySet` (defined in `django/db/models/query.py`)
reports whether a queryset will produce rows in a meaningful order — i.e.
whether the SQL Django generates for it will carry an `ORDER BY` clause.

The property currently returns `True` whenever the model declares a default
ordering (`Meta.ordering`) and default ordering is in force, regardless of
whether the query has been turned into a grouped/aggregated query. When a
queryset is aggregated — for example via `annotate()` with an aggregate, or
`values(...).annotate(...)` — the underlying query builds a `GROUP BY` clause
and the model's `Meta.ordering` no longer contributes an `ORDER BY` clause to
the emitted SQL. In that situation `ordered` incorrectly reports `True` even
though the results are not ordered.

The goal is to make `ordered` agree with the SQL that will actually be
generated: a model's default ordering must NOT cause `ordered` to be `True`
for a grouped/aggregated query, while every other ordering signal continues to
be honored exactly as before. The affected code is the `ordered` property on
the `QuerySet` class in `django/db/models/query.py`; the grouping signal it
must now consult is the query's group-by state
(`self.query.group_by`).

## Requirement 1: Default ordering must not mark aggregated querysets as ordered

**User story:** As a developer using an aggregate `annotate()` on a model that
declares `Meta.ordering`, I want `qs.ordered` to report `False`, so that the
property reflects that the emitted SQL has no `ORDER BY` clause.

**Acceptance criteria**

1. WHEN the `ordered` property is evaluated on a queryset that is a
   grouped/aggregated query (its underlying query has a non-empty group-by
   specification) and that queryset has neither an explicitly requested
   ordering nor an extra ordering, THEN the property SHALL return `False`,
   even when the model declares a default `Meta.ordering` and default ordering
   is in force.
2. WHEN an aggregate annotation is applied to a queryset of a model that
   declares `Meta.ordering` (for example, annotating with a count over the
   primary key), THEN evaluating `ordered` on the resulting queryset SHALL
   return `False`.
3. WHEN a queryset first selects a set of field values and then applies an
   aggregate annotation (producing a grouped query) on a model that declares
   `Meta.ordering`, THEN evaluating `ordered` on the resulting queryset SHALL
   return `False`.
4. The system SHALL treat the model's default ordering as contributing to
   result ordering only when the query is NOT grouped/aggregated.

## Requirement 2: Explicit ordering still marks a queryset as ordered

**User story:** As a developer who explicitly orders an aggregated queryset, I
want `qs.ordered` to report `True`, so that requesting an order overrides the
grouped-query default.

**Acceptance criteria**

1. WHEN an explicit ordering is requested on a queryset (via an `order_by(...)`
   call), THEN evaluating `ordered` SHALL return `True`, regardless of whether
   the query is grouped/aggregated.
2. WHEN an aggregated queryset (one for which `ordered` would otherwise be
   `False`) subsequently has an explicit ordering requested on it, THEN
   evaluating `ordered` on the ordered queryset SHALL return `True`.
3. WHEN a queryset carries an extra ordering specification, THEN evaluating
   `ordered` SHALL return `True`.

## Requirement 3: Preserve existing ordering semantics for non-grouped querysets

**User story:** As a maintainer, I want all previously-correct `ordered`
results to be unchanged, so that this fix narrows only the grouped-query case.

**Acceptance criteria**

1. The system SHALL return `True` from `ordered` for an empty queryset (an
   `EmptyQuerySet`).
2. WHEN a queryset is NOT grouped/aggregated and default ordering is in force
   and the model declares a non-empty `Meta.ordering`, THEN evaluating
   `ordered` SHALL return `True`.
3. WHEN a queryset is NOT grouped/aggregated, has no explicit ordering, no
   extra ordering, and either default ordering is disabled or the model
   declares no `Meta.ordering`, THEN evaluating `ordered` SHALL return `False`.
4. WHEN a queryset has an aggregate annotation but no default ordering in force
   and no explicitly requested ordering, THEN evaluating `ordered` SHALL return
   `False`.
5. The system SHALL continue to base the `ordered` result solely on the
   presence of an explicit ordering, an extra ordering, the empty-queryset
   condition, and (only for non-grouped queries) an in-force model default
   ordering — introducing no other conditions.
