# Requirements: DecimalField window expressions on SQLite

## Introduction

Django's ORM lets a query annotate rows with a window function (a `Window`
expression such as `Lag`, `Lead`, `FirstValue`, etc.) via
`django.db.models.expressions.Window`. On the SQLite backend, numeric results
whose declared output type is a fixed-point decimal (`DecimalField`) must be
cast to a numeric type so that values are read back correctly.

The affected component is the `Window` expression in
`django/db/models/expressions.py` and, specifically, how its SQL is rendered on
the SQLite backend. Django already provides a reusable helper
(`SQLiteNumericMixin`) that wraps a fixed-point-decimal expression's SQL in a
`CAST(... AS NUMERIC)` on SQLite.

The problem: when a window expression declares a `DecimalField` output, the
numeric cast was being emitted *inside* — around the operand of — the `OVER`
clause, producing SQL shaped like `CAST(LAG(...) AS NUMERIC) OVER (...)`. SQLite
rejects an `OVER` clause that follows a closed `CAST(...)` term, raising an
`OperationalError` (`near "OVER": syntax error`), so the query cannot execute at
all.

The goal: on SQLite, a decimal-typed window expression must render the numeric
cast *around the whole windowed expression as a single unit* — i.e.
`CAST(<operand> OVER (<window clause>) AS NUMERIC)` — so the query executes and
returns correct decimal values, while behavior on all other backends and for
non-decimal window expressions is unchanged.

## Requirement 1: Cast the whole windowed expression for decimal output on SQLite

**User story:** As a developer running a window function that produces a
`DecimalField` result against a SQLite database, I want the query to execute
successfully and return correct decimal values, so that features like `Lag`,
`Lead`, and other window functions work on SQLite as they do on other backends.

**Acceptance criteria**

1. WHEN a `Window` expression is compiled for the SQLite backend and its
   resolved output type is a fixed-point decimal (`DecimalField`), THEN the
   system SHALL render the numeric cast so that it encloses the entire windowed
   expression — the operand together with its complete `OVER (...)` clause — as
   one unit, i.e. of the form `CAST(<operand> OVER (<window>) AS NUMERIC)`.
2. WHEN a decimal-typed `Window` expression is compiled for SQLite, THEN the
   system SHALL NOT place any numeric cast between the operand and its `OVER`
   keyword, and SHALL NOT emit an `OVER` clause immediately following a closed
   `CAST(...)` term.
3. WHEN a decimal-typed `Window` expression is executed against a SQLite
   database, THEN the system SHALL produce syntactically valid SQL that SQLite
   accepts without raising a database `OperationalError` referring to the
   `OVER` clause.
4. WHEN a decimal-typed window query is evaluated on SQLite, THEN the system
   SHALL return the correct fixed-point decimal result values for each row
   (including the appropriate empty/absent result where the window offset falls
   outside the partition), matching the values that the same query yields on a
   backend that supports the cast natively.

## Requirement 2: Preserve rendering for non-decimal window expressions

**User story:** As a developer using window expressions whose output is not a
fixed-point decimal, I want their SQL to remain exactly as before, so that no
unnecessary casting or behavioral change is introduced.

**Acceptance criteria**

1. IF a `Window` expression's resolved output type is not a fixed-point decimal
   (`DecimalField`), THEN when compiled for SQLite the system SHALL render the
   bare windowed expression (`<operand> OVER (<window>)`) with no surrounding
   numeric cast.
2. The system SHALL keep the rendered order of a windowed expression's parts as
   operand text, the ` OVER (` keyword, the assembled window-clause text
   (partition-by, order-by, and frame portions as applicable), and the closing
   parenthesis, in that exact sequence.
3. The system SHALL continue to raise the existing "not supported" error when a
   window expression is compiled for a backend that does not support window
   (`OVER`) clauses.

## Requirement 3: Leave other backends and unchanged behavior intact

**User story:** As a developer targeting a non-SQLite database, I want window
expressions to keep behaving exactly as they did, so that this fix affects only
SQLite decimal rendering.

**Acceptance criteria**

1. WHEN a `Window` expression is compiled for a backend other than SQLite, THEN
   the system SHALL render its SQL exactly as it did previously, unaffected by
   the SQLite decimal-cast handling.
2. The system SHALL keep the string, repr, and structural behavior of the
   `Window` expression (its source expression, partition-by, order-by, and
   frame components, and its `filterable`/`contains_over_clause` semantics)
   unchanged.
3. The system SHALL keep all previously working window-function queries — on
   every backend and for every output type — producing the same results they
   produced before this change.
