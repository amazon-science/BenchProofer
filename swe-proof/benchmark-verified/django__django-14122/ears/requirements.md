# Requirements: Default (Meta.ordering) ordering must not widen the GROUP BY clause

## Introduction

When a Django queryset performs aggregation (for example via `.values(...).annotate(...)`),
the SQL compiler must construct a `GROUP BY` clause listing the columns that
rows are grouped by. This clause is assembled in
`django.db.models.sql.compiler.SQLCompiler.get_group_by(select, order_by)`,
which accumulates grouping columns from several sources: an explicit
caller-supplied grouping set, the columns of the selected expressions, the
columns implied by the query's ordering, and the columns of the post-aggregation
(`HAVING`) filter.

The query's ordering may be supplied explicitly by the caller (e.g. an
`order_by(...)` call or an `extra` order-by), or it may be the model's implicit
default ordering taken from `Meta.ordering`. `SQLCompiler.get_order_by()` records
when the ordering it uses came from `Meta.ordering` by setting the compiler's
`_meta_ordering` marker.

The defect: even when the ordering is merely the model's implicit
`Meta.ordering`, the ordering expressions' columns were still added to the
`GROUP BY` clause. This silently widens the grouping key, so rows that should
have been aggregated together are split apart by the extra columns, producing
wrong aggregation results. The goal is that columns arising **only** from an
implicit `Meta.ordering` default must not contribute to `GROUP BY`, while all
other grouping behavior (explicit ordering, select columns, having columns,
de-duplication) is preserved unchanged.

## Requirement 1: Implicit default ordering must not contribute grouping columns

**User story:** As a developer aggregating over a model that declares
`Meta.ordering`, I want the default ordering to not affect how rows are grouped,
so that my aggregate counts and values are correct rather than silently
split by the ordering fields.

**Acceptance criteria**

1. WHEN `get_group_by` assembles the grouping columns AND the ordering in effect
   originated from the model's implicit default ordering (i.e. the compiler's
   `_meta_ordering` marker is set), THEN the compiler SHALL NOT add any columns
   derived from the ordering expressions to the `GROUP BY` clause.
2. WHEN a queryset aggregates over a model whose `Meta.ordering` names one or
   more fields (for example `Model.objects.values('field_a').annotate(count=Count('field_a'))`),
   THEN the resulting grouping SHALL be determined solely by the explicit
   grouping set, the selected-expression columns, and the having columns — and
   SHALL NOT include the `Meta.ordering` fields.
3. WHEN such an aggregate query is executed, THEN the returned aggregate rows
   SHALL reflect grouping by only the requested columns, producing one aggregated
   result per distinct value of the grouped column(s) with correct aggregate
   values, rather than being further subdivided by the default-ordering fields.

## Requirement 2: Explicitly requested ordering must still contribute grouping columns

**User story:** As a developer who explicitly orders an aggregate query, I want
the existing behavior preserved, so that ordering-driven grouping still works as
before.

**Acceptance criteria**

1. WHEN `get_group_by` assembles the grouping columns AND the ordering in effect
   was explicitly requested (an explicit `order_by`, a caller-supplied ordering,
   or an `extra` order-by — i.e. the ordering did NOT originate from the model's
   implicit default), THEN the compiler SHALL add the columns of each ordering
   expression to the grouping accumulation as before.
2. IF an ordering expression is a reference to an expression already present in
   the select clause, THEN the compiler SHALL skip that expression when adding
   ordering columns, since it is already part of the grouping.
3. The system SHALL determine whether ordering columns contribute to `GROUP BY`
   solely from whether the ordering originated from the implicit default; it
   SHALL NOT otherwise alter which orderings are treated as explicit.

## Requirement 3: All other grouping sources and post-processing preserved

**User story:** As a Django user relying on aggregation across many query shapes,
I want every other aspect of `GROUP BY` construction to remain unchanged, so that
this fix does not regress existing behavior.

**Acceptance criteria**

1. The system SHALL continue to return an empty grouping list when the query
   requests no grouping at all.
2. The system SHALL continue to seed the grouping accumulation with any explicit
   caller-supplied grouping columns (as produced by `.values(...)` and related
   forms), preserving their order.
3. The system SHALL continue to add the columns of each selected expression to
   the grouping, skipping any selected expression that is already included by
   reference.
4. The system SHALL continue to add the columns contributed by the
   post-aggregation (`HAVING`) filter to the grouping.
5. The system SHALL continue to de-duplicate the accumulated grouping
   expressions so that a given grouping column appears only once (its first
   occurrence), and SHALL preserve the database-specific primary-key collapse
   behavior.
6. WHEN a grouping clause is emitted for an aggregate query whose ordering came
   from the implicit default, THEN the compiler SHALL still suppress the
   corresponding `ORDER BY` output for that query, keeping the previously-fixed
   behavior of not ordering by implicit-default fields on aggregate queries.
7. The system SHALL confine this change strictly to whether implicit
   default-ordering columns are added to the `GROUP BY` accumulation; the
   ordering the compiler computes and the `ORDER BY` output it emits SHALL be
   unchanged for every query. In particular, the resolved ordering sequence
   and emitted ordering for any query that is NOT an implicit-default aggregate
   (including queries that carry no aggregation) SHALL be byte-for-byte
   identical to the behavior prior to this change, regardless of the ordering
   source or form.
