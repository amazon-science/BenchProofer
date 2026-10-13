# Requirements: Case/When with an always-true condition must render valid SQL

## Introduction

Django's conditional expressions `Case` and `When`
(`django.db.models.expressions`) build a searched SQL `CASE` expression of the
form `CASE WHEN <predicate> THEN <result> ... ELSE <default> END`. Each `When`
turns its condition into a SQL predicate fragment, and `Case` splices those
fragments into the branch template.

Some conditions match **every** row. A negated empty-membership lookup such as
`~Q(pk__in=[])` is the canonical example: it is a sentinel that application
code sometimes returns, and it is logically always true. When such a condition
is used as a top-level queryset filter, Django renders it as an *empty* WHERE
fragment (there is nothing to constrain). The defect is that `When` reused that
same empty fragment inside a `CASE` branch, producing malformed SQL — the
`WHEN` keyword is immediately followed by `THEN` with no predicate between them
(e.g. `CASE WHEN  THEN True ELSE False END`), which the database rejects with a
syntax error at/near `THEN`.

The goal is to make a `When` branch whose condition matches all rows render as
a valid, unconditionally-true predicate, so the branch applies to every row and
no syntax error is raised. The affected code is `When.as_sql` in
`django/db/models/expressions.py`; the behavior is observed through
`Case`/`When` used in `annotate`, `order_by`, `filter`, `aggregate`, and
`update`.

## Requirement 1: A branch condition that matches every row renders as an always-true predicate

**User story:** As a developer using `Case`/`When`, I want a condition that is
logically always true (such as `~Q(pk__in=[])`) to produce a valid conditional
expression that applies to every row, so that a sentinel "match everything"
condition does not crash my query.

**Acceptance criteria**

1. WHEN a `When` branch is compiled to SQL and its condition renders to an
   empty predicate fragment (because the condition matches every row), THEN the
   system SHALL substitute an unconditionally-true predicate for that branch so
   the emitted `CASE ... WHEN <predicate> THEN <result> ...` fragment is
   syntactically valid and contains a non-empty predicate between `WHEN` and
   `THEN`.
2. WHEN a queryset annotates rows with a `Case` whose single `When` uses a
   match-everything condition such as `~Q(pk__in=[])` and a differing default,
   THEN the system SHALL assign the branch's `then` value to **every** returned
   row (not the default value).
3. WHEN such an annotation is evaluated, THEN the number of returned rows SHALL
   equal the total number of rows in the queried table, and the system SHALL
   NOT raise a database syntax/programming error.
4. WHEN a `Case` built with a match-everything `When` condition is used to
   order a queryset (for example `order_by` on the annotation), THEN the system
   SHALL execute the query successfully without emitting an empty-predicate
   `CASE` fragment.
5. WHEN the always-true substitution is applied, THEN the system SHALL supply
   any query parameters bound by that substituted predicate together with its
   SQL fragment, so the parameter list stays consistent with the emitted SQL.

## Requirement 2: Ordinary (non-empty) conditions are unchanged

**User story:** As a developer, I want branches whose condition renders to a
real predicate to keep working exactly as before, so that the fix only affects
the empty-predicate case.

**Acceptance criteria**

1. WHEN a `When` branch's condition renders to a non-empty predicate fragment,
   THEN the system SHALL keep that fragment and its bound parameters unchanged,
   emitting the branch as `WHEN <that predicate> THEN <result>`.
2. The system SHALL continue to evaluate each row against the branch conditions
   in order, returning the first matching branch's result and the `Case`
   default (or NULL when no default is given) when no branch matches.
3. WHEN a `Case`/`When` expression is used in `annotate`, `filter`,
   `aggregate`, or `update`, THEN the system SHALL keep producing the same
   results it produced for those operations before the change.

## Requirement 3: Empty and invalid conditions keep their existing semantics

**User story:** As a developer, I want the distinction between "matches
nothing", "matches everything", and "invalid" conditions to be preserved, so
that the fix does not blur those cases.

**Acceptance criteria**

1. WHEN a `When` condition matches **no** rows (for example a membership test
   against an empty set, `Q(pk__in=[])`), THEN the system SHALL apply the
   `Case` default to every row and SHALL NOT apply that branch's `then` value —
   i.e. the always-true substitution SHALL NOT be applied to a match-nothing
   branch.
2. IF a `When` is constructed with a truly empty `Q()` object as its condition,
   THEN the system SHALL raise a `ValueError` (an empty `Q()` cannot be used as
   a `When` condition).
3. IF a `When` is constructed without a valid condition — with no condition, or
   with an argument that is not a `Q` object, boolean-valued expression, or
   lookup keyword — THEN the system SHALL raise a `TypeError`.
4. The system SHALL continue to accept a `Q` object, a conditional expression,
   or lookup keyword arguments as a `When` condition, including negated and
   combined `Q` objects.

## Requirement 4: Output-field, hashing, and documentation-example behavior preserved

**User story:** As a maintainer, I want the surrounding contract of
`Case`/`When` to stay intact, so the fix introduces no regressions.

**Acceptance criteria**

1. The system SHALL keep resolving the output field of a `Case` expression from
   its branch results (or the explicit `output_field`) as before, so annotated
   values retain their correct Python types across the supported field types.
2. The system SHALL keep `Case`/`When` expressions hashable and comparable as
   before, so equivalent expressions can be reused across queries.
3. The system SHALL keep the documented `Case`/`When` usage patterns
   (conditional aggregation, conditional update, filtering on a conditional
   annotation, and lookup/simple examples) producing their established results.
4. The system SHALL keep supporting conditions, values, and results that are
   themselves expressions, aggregations, annotations, joins, or subqueries,
   without altering their previously correct output.
