# Requirements: aggregate() with a `default` after annotate()

## Introduction

Django's ORM lets an aggregate function (for example `Sum`, `Avg`, `Max`) carry
a `default` value that is substituted when the aggregation has no rows to
operate on. Internally, when such an aggregate is resolved for a query, it is
not emitted as a bare aggregate: it is wrapped in a coalescing expression
(`django.db.models.functions.Coalesce`) whose first operand is the aggregate and
whose second operand is the resolved default value.

Every resolvable ORM expression carries an `is_summary` flag (defined on
`django.db.models.expressions.Expression`) that records whether it is being
resolved as a *terminal* aggregation — i.e. one produced by `QuerySet.aggregate()`
that collapses the whole queryset to a single row, as opposed to an annotation
added with `QuerySet.annotate()`. The SQL compiler (`django.db.models.sql.query`)
uses this flag to decide which resolved aggregations must be pulled out of an
inner subquery into the outer aggregate query. When a query already carries
annotations, `Query.get_aggregation()` builds a subquery and moves only the
expressions whose `is_summary` is true into the outer `SELECT`.

The defect: `Aggregate.resolve_expression()` in
`django/db/models/aggregates.py` builds the coalescing wrapper but does not copy
the aggregate's `is_summary` flag onto it. The freshly constructed wrapper
therefore defaults to a non-summary flag. When `aggregate(...)` is called after
`annotate(...)`, the terminal aggregation is not recognized as terminal, is not
lifted into the outer query's `SELECT` list, and the compiler emits invalid SQL
(an empty select list, `SELECT FROM (...)`), raising a database error at
execution time.

The goal is to make the resolved wrapper faithfully carry the same terminal /
non-terminal marker that the aggregate itself was resolved with, so that
`aggregate()` with a `default` works after `annotate()` while every existing
resolution behavior is preserved.

The affected code is `Aggregate.resolve_expression()` in
`django/db/models/aggregates.py`; the observable behavior is the value of the
resolved expression tree and the SQL produced for `QuerySet.aggregate()` /
`QuerySet.annotate()` calls.

## Requirement 1: Propagate the terminal-aggregation marker onto the default wrapper

**User story:** As a developer using an aggregate with a `default` value, I want
`aggregate()` to work after `annotate()`, so that I get a correct scalar result
instead of a database syntax error.

**Acceptance criteria**

1. WHEN an aggregate that carries a `default` value is resolved, THEN
   `Aggregate.resolve_expression` SHALL return the coalescing wrapper node
   (`Coalesce`) with its `is_summary` flag set equal to the `is_summary` flag of
   the resolved aggregate it wraps.
2. WHEN an aggregate carrying a `default` is resolved as a terminal aggregation
   (the resolution is performed with the summarize flag set, as happens for
   `QuerySet.aggregate()`), THEN the returned wrapper node SHALL have its
   `is_summary` flag set to true.
3. WHEN an aggregate carrying a `default` is resolved as a non-terminal
   aggregation (the resolution is performed without the summarize flag, as
   happens for `QuerySet.annotate()`), THEN the returned wrapper node SHALL have
   its `is_summary` flag set to false.
4. IF a query has one or more pre-existing annotations AND a terminal aggregate
   with a `default` is applied to it via `QuerySet.aggregate()`, THEN executing
   the query SHALL succeed and SHALL return the same numeric result the same
   aggregate would return without the `default` when at least one row is
   aggregated (for example, an integer sum of the underlying values), rather than
   raising a database error.
5. WHEN a terminal aggregate with a `default` is applied after an annotation,
   THEN the resolved aggregation SHALL be emitted in the outer query's selected
   output (not left inside the inner subquery), so that the generated SQL
   contains a non-empty select list.

## Requirement 2: Preserve wrapping behavior driven by the presence of a default

**User story:** As a maintainer, I want the choice between the bare aggregate and
the coalescing wrapper to depend solely on whether a `default` was supplied, so
that aggregates without a default keep their existing behavior.

**Acceptance criteria**

1. WHEN an aggregate is resolved AND no `default` value was supplied, THEN
   `Aggregate.resolve_expression` SHALL return the bare aggregate node and SHALL
   NOT wrap it in a coalescing node.
2. WHEN an aggregate is resolved AND a `default` value was supplied, THEN
   `Aggregate.resolve_expression` SHALL return a coalescing wrapper whose first
   operand is the resolved aggregate and whose second operand is the resolved
   default value, and SHALL reset the wrapped aggregate's own `default` so the
   fallback is applied only once by the wrapper.
3. WHEN an aggregate carrying a `default` is resolved, THEN the coalescing
   wrapper's output field SHALL be taken from the wrapped aggregate's output
   field.
4. IF the supplied `default` is itself an expression (it has its own
   `resolve_expression`), THEN it SHALL be resolved with the same query context,
   join, reuse, and summarize parameters used to resolve the aggregate before it
   is placed into the wrapper.

## Requirement 3: Preserve existing aggregation and annotation behavior

**User story:** As a user relying on existing aggregate and annotate behavior, I
want all previously working query patterns to keep producing the same results, so
that this fix does not regress anything.

**Acceptance criteria**

1. The system SHALL continue to return the correct scalar value for a terminal
   aggregate that carries a `default` when it is applied directly to a queryset
   with no preceding annotation, for both the empty-result case (where the
   `default` value is returned) and the non-empty case.
2. WHEN a terminal aggregate without a `default` is applied after an annotation,
   THEN the query SHALL continue to execute successfully and return the same
   result as before.
3. WHEN an annotation whose value is a non-aggregate expression is added and a
   separate aggregate (without reference to that annotation) is applied, THEN the
   aggregate SHALL be computed over the underlying rows and SHALL return the same
   result as if the unrelated annotation were absent.
4. The system SHALL continue to substitute the `default` value for a terminal
   aggregate when the aggregation set is empty, returning that default rather than
   a null/absent value.
5. The system SHALL continue to support `default` values of the full range of
   supported types (integer, decimal, date, time, datetime, duration, and
   expression-valued defaults), producing the correct fallback value for each.
6. WHEN a `default` is combined with other supported aggregate features (for
   example a compound or expression-based default, a default passed another
   aggregate, or grouping), THEN the previously supported results SHALL be
   preserved.
7. The system SHALL continue to reject a `default` on aggregates that do not
   permit one (those whose empty-result value is fixed), raising the same error
   as before.
