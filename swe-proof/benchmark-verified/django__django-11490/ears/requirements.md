# Requirements: Composed queries must be able to change their projected column list across evaluations

## Introduction

When a composed queryset (built with `union()`, `intersection()`, or
`difference()` on `django.db.models.query.QuerySet`) is restricted to a specific
list of columns through `values()` or `values_list()`, the SQL compiler in
`django.db.models.sql.compiler.SQLCompiler.get_combinator_sql` propagates that
column list onto each combined query part that does not already specify a column
list of its own. This lets every part of the compound statement project the same
columns, as required for a valid `UNION`/`INTERSECT`/`EXCEPT` statement.

The defect: propagation is applied by mutating the combined query part objects
in place. Those part objects are shared and reused across evaluations of the
same composed queryset. Once the first evaluation stamps a column list onto a
part, a subsequent evaluation of the same composed queryset with a *different*
column list still sees the stale, previously-set column list and cannot change
its projected columns. For example, after evaluating a union projecting
`('name', 'order')`, evaluating the same union again projecting `('order',)`
wrongly returns the old two-column result instead of the single requested column.

The goal is that building the SQL for one evaluation must not alter the shared
combined-query part definitions, so each evaluation independently applies the
column list requested for *that* evaluation, while every behavior that already
worked for composed querysets is preserved.

## Requirement 1: Column-list propagation to combined query parts

**User story:** As a developer composing querysets with set operations, I want a
restricted column list to be applied to every combined part, so that the
generated compound SQL is valid and returns exactly the requested columns.

**Acceptance criteria**
1. WHEN a composed query is evaluated with a specific projected column list and a
   combined query part does not itself specify any column list, THEN the compiler
   SHALL build that part for the current evaluation using the composed query's
   projected column list.
2. The system SHALL construct that per-part column list from the composed query's
   extra selections, its explicit value selections, and its annotation selections,
   preserving their relative order.
3. WHEN a combined query part already specifies its own column list, THEN the
   compiler SHALL use that part as given and SHALL NOT overwrite it with the
   composed query's column list.
4. IF the composed query does not restrict its projection to a specific column
   list, THEN the compiler SHALL leave each combined query part's projection
   unchanged.

## Requirement 2: Evaluation must not mutate shared combined-query definitions

**User story:** As a developer, I want to evaluate the same composed queryset
more than once with different projected columns, so that each evaluation reflects
the columns I asked for at that time.

**Acceptance criteria**
1. WHEN the compiler applies the composed query's column list to a combined query
   part during one evaluation, THEN it SHALL do so on a per-evaluation copy of
   that part's query and SHALL leave the underlying shared combined-query
   definition unchanged.
2. WHEN a composed queryset is first evaluated projecting one list of columns and
   is then evaluated again projecting a different list of columns, THEN the second
   evaluation SHALL return rows containing exactly the columns requested by the
   second evaluation.
3. WHEN a composed queryset is evaluated repeatedly with the same projected column
   list, THEN every evaluation SHALL return the same, correct result.

## Requirement 3: Preserve existing composed-query behavior (regression protection)

**User story:** As a maintainer, I want all previously working set-operation query
behavior to keep working, so that fixing the column-list bug introduces no
regression.

**Acceptance criteria**
1. The system SHALL continue to support `union()`, `intersection()`, and
   `difference()` compositions, including `union(all=True)` and distinct union.
2. The system SHALL continue to produce correct results for compositions combined
   with `values()`/`values_list()`, including compositions over annotated
   querysets and mixes of annotated and unannotated querysets.
3. WHEN a composed query includes an empty combined part, THEN the system SHALL
   continue to omit the empty part for union and difference as before, and SHALL
   continue to produce correct counts and results.
4. The system SHALL continue to support ordering of composed querysets (including
   ordering by an expression) and SHALL continue to raise a database error when
   ordering by a column that is not among the selected columns, and when
   unsupported slicing or ordering is applied to a compound statement.
5. The system SHALL continue to support limits, counting, combining multiple
   models, and nesting a composed query as a part of another composed query.
