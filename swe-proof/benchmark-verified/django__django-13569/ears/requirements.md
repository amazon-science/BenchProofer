# Requirements: Random ordering must not break aggregation grouping

## Introduction

Django's ORM lets a queryset combine an aggregate annotation (e.g.
`Count(...)`) with an ordering clause. When a query has an aggregate, the SQL
compiler builds a `GROUP BY` clause. As documented, ordering expressions are
folded into that grouping: `django.db.models.sql.compiler.SQLCompiler.get_group_by`
walks each `ORDER BY` expression and, for the non-aggregate, non-reference
ones, adds the stored columns they contribute (obtained by asking the
expression for its grouping columns) to the `GROUP BY`.

This is correct for expressions that reference real stored columns: ordering
by a related column legitimately expands the grouping. But the random-ordering
expression produced by `order_by('?')` — the `Random` SQL function defined in
`django/db/models/functions/math.py` (a zero-argument, non-deterministic value
generator) — has no underlying stored column, so it has nothing meaningful to
group on. Under the existing behavior, `Random`, like any generic function
expression, reports *itself* as its grouping column, so `RANDOM()` is added to
the `GROUP BY`. The effect is that a query such as
`Thing.objects.annotate(rc=Count('related')).order_by('?')` emits
`GROUP BY <thing pk>, RANDOM()`, which fragments the groups (each row lands in
its own random group) and yields wrong aggregate counts — the same query
ordered any other way (or unordered) groups correctly.

The goal is: a random ordering term must contribute nothing to the grouping of
an aggregated query, so that ordering results randomly never changes which rows
are grouped together or the resulting aggregate values, while every other
ordering expression continues to affect grouping exactly as before.

Affected code: the `Random` function class in
`django/db/models/functions/math.py`, consumed by
`get_group_by` in `django/db/models/sql/compiler.py`.

## Requirement 1: Random ordering contributes no grouping columns

**User story:** As a developer, I want the random-value expression used for
`order_by('?')` to report that it adds no columns to a query's grouping, so
that random ordering cannot alter how aggregated rows are grouped.

**Acceptance criteria**

1. WHEN the SQL compiler asks the random-value ordering expression which
   grouping columns it contributes, THEN the expression SHALL return an empty
   collection of grouping columns.
2. The random-value ordering expression SHALL report an empty grouping-column
   contribution regardless of any optional alias argument passed when its
   grouping columns are requested.
3. IF a query with an aggregate annotation is ordered randomly, THEN the
   compiler SHALL NOT add any random-value term to the query's `GROUP BY`
   clause.

## Requirement 2: Random ordering preserves aggregate results

**User story:** As a developer, I want a randomly ordered aggregated queryset
to produce the same grouped rows and aggregate values as the corresponding
unordered aggregated queryset, so that adding `order_by('?')` never corrupts my
counts.

**Acceptance criteria**

1. WHEN a queryset annotated with an aggregate (such as a per-object related
   `Count`) is ordered randomly with `order_by('?')`, THEN evaluating it SHALL
   yield exactly one grouped result row per grouped object, with each aggregate
   value equal to the value that query produces without the random ordering.
2. WHEN a randomly ordered aggregated queryset is evaluated, THEN the returned
   rows SHALL be the same set of (object, aggregate value) pairs — differing at
   most in order — as the equivalent aggregated queryset with no random
   ordering.
3. WHILE an aggregated queryset is ordered randomly, the grouping SHALL remain
   determined solely by the query's real grouping columns, so that the count of
   distinct result groups is unaffected by the random ordering.

## Requirement 3: Non-random ordering still affects grouping (regression protection)

**User story:** As a maintainer, I want every non-random ordering expression to
keep contributing its stored columns to the grouping exactly as before, so that
the fix is narrowly scoped to the random-value expression.

**Acceptance criteria**

1. WHEN an aggregated query is ordered by a real column expression (for example
   a related field), THEN that column SHALL still be added to the `GROUP BY`,
   preserving the previously observed grouping and aggregate behavior for that
   ordering.
2. WHEN an aggregated query is ordered by a reference to a selected aggregate
   annotation, THEN the compiler SHALL keep excluding that reference from the
   `GROUP BY` and SHALL keep producing the correct grouped aggregate result.
3. WHEN an aggregated query is ordered by an aggregate expression, THEN the
   compiler SHALL continue to exclude that aggregate from the `GROUP BY` while
   still grouping by the underlying columns of the aggregate's operands as
   before.
4. The system SHALL keep including in the `GROUP BY` the stored columns
   contributed by ordinary, non-random ordering, select, and having
   expressions, so that only the random-value expression's grouping
   contribution changes.

## Requirement 4: Random expression behavior otherwise unchanged

**User story:** As a user of the random SQL function, I want it to keep behaving
as a valid non-deterministic value generator everywhere else it is used, so that
only its grouping contribution is affected.

**Acceptance criteria**

1. The random-value expression SHALL continue to compile to the appropriate
   backend random function and remain usable as an ordering term and as a
   general expression exactly as before this change.
2. The system SHALL leave unchanged the grouping contribution of all other
   function and column expressions, altering only the random-value expression's
   reported grouping columns.
