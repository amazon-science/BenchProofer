# Requirements: Group-by column resolution for wrapping expressions

## Introduction

Django's ORM builds a SQL `GROUP BY` clause by asking each selected query
expression which columns it contributes to the grouping. Every query expression
exposes a query for this set of grouping columns (defined on the base expression
class in `django/db/models/expressions.py`), which optionally takes an `alias`.

`ExpressionWrapper` (in `django/db/models/expressions.py`) is a thin wrapper
whose only purpose is to attach extra context — notably an `output_field` — to
another expression while leaving what that inner expression computes unchanged.
It already forwards other structural queries (such as its source expressions and
its SQL generation) to the wrapped expression.

However, `ExpressionWrapper` does not define its own answer for the grouping-
column query, so it inherits the base-class behavior. The base implementation
returns the expression itself as a grouping column whenever the expression
contains no aggregate. This is wrong for a wrapper: when the wrapped expression
is a constant (for example a literal `Value`), the constant should contribute
**no** grouping columns, but the wrapper instead reports itself as a grouping
column. The result is that a constant annotated through an `ExpressionWrapper` is
incorrectly added to the `GROUP BY` clause, producing invalid SQL on backends
such as PostgreSQL (e.g. "aggregate functions are not allowed in GROUP BY"). The
same query written without the wrapper — annotating the constant directly —
correctly omits it, because a constant expression reports an empty set of
grouping columns.

The goal is to make `ExpressionWrapper` defer grouping-column resolution to the
expression it wraps, so that wrapping an expression never changes which columns
that expression contributes to the grouping clause.

## Requirement 1: Wrapper delegates grouping columns to the wrapped expression

**User story:** As a developer building queries with `ExpressionWrapper`, I want
the wrapper to contribute exactly the grouping columns of the expression it
wraps, so that wrapping an expression does not change how it participates in a
`GROUP BY` clause.

**Acceptance criteria**

1. WHEN an `ExpressionWrapper` instance is asked for the columns it contributes
   to the grouping clause, THEN the wrapper SHALL return the grouping columns
   reported by the expression it wraps.
2. WHEN an `ExpressionWrapper` is asked for its grouping columns with an `alias`
   argument, THEN the wrapper SHALL resolve the wrapped expression's grouping
   columns using that same `alias` value.
3. The system SHALL support asking an `ExpressionWrapper` for its grouping
   columns with `alias` set to `None`, and in that case SHALL resolve the wrapped
   expression's grouping columns with `alias` set to `None`.
4. WHEN the result is produced, THEN the wrapper SHALL return exactly the list
   reported by the wrapped expression — neither adding the wrapper itself to that
   list nor substituting the wrapper for the wrapped result.

## Requirement 2: A wrapped constant contributes no grouping columns

**User story:** As a developer who annotates a query with a constant expression
wrapped in an `ExpressionWrapper`, I want the constant to be omitted from the
`GROUP BY` clause, so that the generated SQL is valid on databases that reject
constants in grouping.

**Acceptance criteria**

1. WHEN an `ExpressionWrapper` that wraps a constant expression (an expression
   that itself contributes no grouping columns) is asked for its grouping columns
   with `alias` set to `None`, THEN the wrapper SHALL return an empty list.
2. IF the wrapped expression is a constant literal value, THEN the
   `ExpressionWrapper` SHALL contribute no grouping columns, matching the
   behavior of annotating that same constant directly without the wrapper.

## Requirement 3: A wrapped non-constant expression contributes its own columns

**User story:** As a developer who wraps a non-constant expression in an
`ExpressionWrapper`, I want the wrapped expression's grouping columns to be
preserved, so that grouping still behaves correctly for such expressions.

**Acceptance criteria**

1. WHEN an `ExpressionWrapper` that wraps a non-aggregate, non-constant
   expression is asked for its grouping columns with `alias` set to `None`, THEN
   the wrapper SHALL return a list containing exactly the wrapped expression as
   the single grouping column.
2. The returned list SHALL contain the same expression object that the wrapper
   wraps (the value exposed as the wrapper's wrapped/source expression), and no
   other elements.

## Requirement 4: Preserve existing ExpressionWrapper behavior

**User story:** As a maintainer, I want the existing responsibilities of
`ExpressionWrapper` to remain unchanged, so that adding grouping-column
delegation does not regress other behavior.

**Acceptance criteria**

1. The system SHALL continue to expose the wrapped expression as the wrapper's
   single source expression.
2. The system SHALL continue to generate SQL for an `ExpressionWrapper` by
   delegating to the wrapped expression's SQL generation.
3. WHEN an `ExpressionWrapper` is constructed with an expression and an
   `output_field`, THEN it SHALL retain that wrapped expression and that
   `output_field` unchanged.
