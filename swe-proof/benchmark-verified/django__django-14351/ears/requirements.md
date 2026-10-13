# Requirements: `__in` subquery must contribute a single column to GROUP BY

## Introduction

Django's ORM lets a query combine a membership test against a related subquery
with an aggregate condition, for example filtering a queryset that has been
annotated with `Count(...)` using a disjunction such as
`Q(relation__in=some_queryset) | Q(relation__count=0)`. When the two `Q`
operands are OR'd together, the membership (`__in`) condition is pushed into the
`GROUP BY`/`HAVING` portion of the generated SQL, so the related subquery on the
right-hand side of the `__in` lookup becomes a grouping key.

The membership lookup is implemented by the `In` lookup class in
`django/db/models/lookups.py`. When it produces the SQL predicate
(`In.process_rhs`), it already normalizes a right-hand-side subquery that has no
explicitly selected columns down to just its primary-key column, so the emitted
`IN (...)` subquery returns exactly one column. However, the columns that the
lookup contributes to the enclosing query's `GROUP BY` clause are collected by a
separate, inherited code path that does **not** apply that same normalization. As
a result, when such an `__in` subquery is used as a grouping key it is emitted
with **all** of the subquery model's default columns instead of a single column,
and the database rejects the statement with an error equivalent to "subquery must
return only one column". This regressed between Django 2.2 and 3.2.

The goal is to make the `In` lookup contribute a single-column (primary-key)
subquery to `GROUP BY` — consistently with how it already builds the `IN`
predicate — so that a queryset combining an `__in` subquery filter with an
aggregate filter via OR executes successfully and returns the correct rows. The
affected module is `django/db/models/lookups.py` (the `In` membership lookup);
the behavior is observed by executing such a queryset.

## Requirement 1: `__in` subquery grouping key selects a single column

**User story:** As a developer, I want a membership (`__in`) test against a
related subquery to work even when the subquery ends up as a grouping key, so
that the database does not reject the statement for returning too many columns.

**Acceptance criteria**

1. WHEN an `In` (membership / `__in`) lookup whose right-hand side is a subquery
   with no explicitly selected columns is asked for the columns it contributes to
   the enclosing query's `GROUP BY` clause, THEN the lookup SHALL normalize that
   subquery so it selects only its single primary-key column before that subquery
   is included among the grouping columns.
2. WHEN such an `__in` subquery is used as a grouping key, THEN the generated
   subquery SHALL return exactly one column.
3. IF the right-hand-side subquery already has explicitly selected columns (the
   caller chose specific fields), THEN the lookup SHALL leave that subquery's
   selected columns unchanged when contributing group-by columns.
4. IF the right-hand side of the lookup is not a subquery (it is a plain value or
   collection of values and does not itself contribute group-by columns), THEN
   the lookup SHALL contribute only the left-hand side's group-by columns and
   SHALL NOT attempt any subquery normalization.

## Requirement 2: OR of an `__in` subquery filter with an aggregate filter executes and returns correct rows

**User story:** As a developer, I want to filter an aggregated queryset with a
disjunction of a related-subquery membership test and an aggregate condition, so
that I get the expected objects without a database error.

**Acceptance criteria**

1. WHEN a queryset that has been annotated with an aggregate (for example a
   related `Count`) is filtered by a disjunction (OR) of a related `__in`
   membership test against a subquery and a condition on the aggregate, THEN the
   query SHALL execute without raising a database `ProgrammingError` (or
   equivalent "subquery must return only one column" error).
2. WHEN such a query is evaluated, THEN the result set SHALL contain exactly the
   objects that satisfy the membership test OR the aggregate condition, matching
   the semantics of the disjunction.
3. The system SHALL preserve the left-hand side's own group-by columns in the
   result, i.e. the normalization SHALL affect only the right-hand-side subquery
   and SHALL NOT drop or alter the columns contributed by the left-hand side of
   the lookup.

## Requirement 3: Existing aggregation, grouping, and join behavior is preserved

**User story:** As a developer relying on Django's aggregation and grouping, I
want this fix to leave all other aggregation, `GROUP BY`, and join behavior
unchanged, so that existing queries continue to work.

**Acceptance criteria**

1. The system SHALL continue to collect the left-hand side's group-by columns for
   every lookup exactly as before, so that group-by column determination for
   non-`__in` lookups and for `__in` lookups with non-subquery right-hand sides is
   unaffected.
2. WHEN a queryset uses aggregate filtering via `HAVING`, conditional aggregates,
   or aggregate annotations combined with ordinary filters, THEN those queries
   SHALL continue to produce the same results as before this change.
3. The system SHALL keep existing join-promotion behavior for annotated and
   filtered querysets unchanged (nullable and non-nullable foreign-key joins are
   promoted or left as inner joins exactly as before).
4. The system SHALL keep the previously working single-column form — a membership
   test whose right-hand side explicitly selects only the primary key — producing
   correct results and a single-column subquery, both before and after this
   change.
