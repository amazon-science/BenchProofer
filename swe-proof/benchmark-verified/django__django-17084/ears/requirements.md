# Requirements: Support aggregating over window-function annotations

## Introduction

Django's ORM allows a `QuerySet` to be annotated with expressions and then
reduced with `QuerySet.aggregate(...)`. When an aggregate passed to
`aggregate()` references an annotation that is a window (OVER-clause)
expression, the resulting SQL previously placed the aggregate function call
directly around the window expression in the same SELECT. On backends that
reject this (e.g. PostgreSQL), the database raises a grouping error such as
"aggregate function calls cannot contain window function calls", so the query
fails instead of returning a value.

The affected logic lives in `Query.get_aggregation()` in
`django/db/models/sql/query.py`. This method decides whether the requested
aggregation must be evaluated inside a wrapping subquery (an inner query whose
rows are then aggregated by an outer query) or can be computed directly. The
goal is: whenever a requested aggregate references an annotation that is a
window expression, the aggregation is evaluated over a wrapping subquery, so
the aggregate is applied to the already-materialized window results rather than
being nested inside the window call. This must be done without changing the
existing wrapping decisions for every other case, and without regressing the
existing pruning of unreferenced annotations.

Throughout, "window annotation" means an annotation expression that reports it
contains an OVER clause (its `contains_over_clause` property is true), such as a
`Window(...)` expression, including when it is wrapped by another expression
like `Coalesce(Window(...), ...)`.

## Requirement 1: Wrap aggregation when an aggregate references a window annotation

**User story:** As a developer, I want to call `.aggregate()` with a `Sum` (or
other aggregate) over an annotation that uses a `Window` function, so that I get
the aggregated value back instead of a database grouping error.

**Acceptance criteria**

1. WHEN `Query.get_aggregation()` resolves the requested aggregate expressions
   and at least one of them references an annotation that is a window
   expression (its OVER-clause property is true), THEN `get_aggregation()` SHALL
   evaluate the requested aggregates inside a wrapping subquery (an inner query
   selecting the referenced annotations, with the aggregates applied by an outer
   query).
2. WHEN an aggregate references a window annotation and the aggregation is
   evaluated over a wrapping subquery, THEN the generated SQL SHALL apply the
   aggregate function to the window annotation's column produced by the inner
   query, and SHALL NOT nest the aggregate function call directly around the
   window (OVER-clause) expression.
3. IF a requested aggregate references a window annotation, THEN executing the
   `aggregate()` call SHALL succeed and return the computed aggregate value(s)
   rather than raising a database grouping error.
4. WHEN `get_aggregation()` determines whether an aggregate references a window
   annotation, THEN it SHALL inspect each annotation referenced by the resolved
   aggregate and SHALL treat the aggregate as referencing a window annotation if
   any referenced annotation reports that it contains an OVER clause.
5. WHEN evaluating a set of requested aggregates where a non-window,
   non-subquery aggregate (for example a plain `Count`) is requested alongside
   an aggregate that references a window annotation, THEN all requested
   aggregate values SHALL be produced together within the single wrapping
   subquery execution and returned in one result mapping.

## Requirement 2: Wrapping is triggered only when needed; a single query is used otherwise

**User story:** As a developer, I want ordinary aggregations to keep producing
efficient SQL, so that adding window-aware handling does not add a redundant
subquery layer to queries that do not need it.

**Acceptance criteria**

1. The window-annotation condition SHALL be combined by logical OR with the
   pre-existing conditions that already force a wrapping subquery, so that the
   aggregation is wrapped when ANY of the following holds: the query already
   groups by a tuple; the query is sliced; the query already has an existing
   aggregation (a selected aggregate annotation or a HAVING filter against an
   aliased aggregate); a referenced annotation is itself produced by a wrapping
   subquery; the query is a qualify (window-filtered) query; the query is
   distinct; the query uses a set-combination operator; OR a referenced
   annotation is a window annotation.
2. IF none of the wrapping conditions in criterion 1 holds for the requested
   aggregation, THEN `get_aggregation()` SHALL compute the aggregates without
   introducing a wrapping subquery (a single-level query).
3. The addition of the window-annotation condition SHALL NOT change the wrapping
   decision for any aggregation that does not reference a window annotation.

## Requirement 3: Preserve existing subquery-wrapping and annotation-pruning behavior

**User story:** As a maintainer, I want the existing aggregation-pruning and
subquery behaviors to remain intact, so that this change fixes window
aggregation without regressing established query optimization.

**Acceptance criteria**

1. WHEN a requested aggregate references an annotation that is itself produced
   by a wrapping subquery, THEN `get_aggregation()` SHALL continue to evaluate
   the aggregation inside a wrapping subquery, exactly as before this change.
2. The system SHALL continue to prune (exclude from the emitted SQL) annotations
   that are not referenced by any requested aggregate and are not otherwise
   required, so that unused and unreferenced annotations do not appear in the
   generated query.
3. The system SHALL continue to keep (include) annotations that ARE referenced
   by a requested aggregate, including aggregate annotations and annotations
   participating in the GROUP BY.
4. WHEN a query has no existing aggregation, is not sliced, does not group by a
   tuple, is not distinct, uses no set-combination operator, is not a qualify
   query, and references neither a subquery annotation nor a window annotation,
   THEN `get_aggregation()` SHALL continue to compute the aggregate without a
   wrapping subquery.
5. The correctness and identity of the returned aggregate values SHALL be
   unchanged for all aggregations that were already supported before this
   change.
