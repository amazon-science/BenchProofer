# Requirements: Delete an entire table without a self-referential subquery

## Introduction

When Django compiles a row-deletion into SQL, the deletion is emitted by
`SQLDeleteCompiler` in `django/db/models/sql/compiler.py`. That compiler decides
between two shapes of statement:

* a **direct** deletion — `DELETE FROM <table> [WHERE ...]` — produced by
  `SQLDeleteCompiler._as_sql`; and
* a **subquery-guarded** deletion — `DELETE FROM <table> WHERE <pk> IN (SELECT
  <pk> FROM <table> ...)` — produced by wrapping the primary key in an inner
  query.

The choice is driven by the compiler's `single_alias` property, which is meant to
be true exactly when the deletion targets a single table. It computes this by
counting the query's recorded table references (`alias_map`) that have a positive
reference count (`alias_refcount`) and asking whether that count is exactly one.

For a full-table deletion such as `Model.objects.all().delete()`, the query has
**no recorded table references yet** — its own base table has never been
registered as an alias. As a result the count is `0`, `single_alias` is false,
and the compiler falls back to the subquery-guarded form, emitting
`DELETE FROM t WHERE pk IN (SELECT pk FROM t)`. This introduced a performance
regression and, because the subquery references the same unaliased table, made
the statement incompatible with MySQL `LOCK TABLES`.

The goal is to make `single_alias` account for the deletion's own base table so
that a full-table deletion is recognised as single-table and emitted as a direct
`DELETE FROM t` with no subquery, while every existing case (single-table
deletes with a filter, and multi-table deletes that legitimately need the
subquery) keeps behaving as before.

## Requirement 1: Full-table deletion emits a direct statement with no subquery

**User story:** As a developer running `Model.objects.all().delete()`, I want the
generated SQL to be a plain `DELETE FROM <table>` with no nested `SELECT`, so
that the deletion is fast and can be used under table locks that forbid
referring to the same table twice in one statement.

**Acceptance criteria**

1. WHEN `SQLDeleteCompiler.as_sql` compiles a deletion whose query targets a
   single table and has no restricting conditions (an unconditional full-table
   delete), THEN the compiler SHALL produce a single `DELETE FROM <table>`
   statement whose text contains no `SELECT` keyword and no nested subquery.
2. WHEN such a full-table deletion is executed, THEN it SHALL be carried out
   using exactly one database query.
3. WHEN a full-table deletion is compiled, THEN the compiler SHALL delete every
   row of the target table, preserving the same rows-affected result as before
   this change.

## Requirement 2: Single-table detection accounts for the deletion's base table

**User story:** As a maintainer of the delete compiler, I want the single-table
test to include the query's own primary table, so that a deletion is recognised
as targeting one table even when no alias has been recorded yet.

**Acceptance criteria**

1. WHEN `SQLDeleteCompiler.single_alias` is evaluated, THEN it SHALL first ensure
   the deletion's own base (primary) table is registered among the query's table
   references before counting active references.
2. WHEN the base table has not yet been recorded among the query's references,
   THEN ensuring its presence SHALL add it as a new active reference (a
   reference with a positive reference count).
3. WHEN the base table is already recorded among the query's references, THEN
   ensuring its presence SHALL keep it active and SHALL leave the set of
   distinct referenced tables unchanged.
4. WHEN the base table has been ensured present, THEN `single_alias` SHALL report
   true IF and only IF exactly one referenced table has a positive reference
   count.
5. WHEN `single_alias` reports true, THEN `as_sql` SHALL emit the direct
   `DELETE FROM <table> [WHERE ...]` form and SHALL NOT wrap the primary key in
   an `IN (SELECT ...)` subquery.

## Requirement 3: Preserve deletions that require a subquery or a filter (regression protection)

**User story:** As a maintainer, I want every deletion that is not an
unconditional single-table delete to keep generating the SQL it did before, so
that filtered deletes and multi-table deletes continue to work correctly.

**Acceptance criteria**

1. WHEN `SQLDeleteCompiler.as_sql` compiles a deletion whose query references
   more than one table (for example a delete restricted through a relation/join),
   THEN `single_alias` SHALL report false and the compiler SHALL emit the
   subquery-guarded form that selects the target primary keys via an inner query.
2. WHEN a deletion targets a single table but carries a restricting condition
   (a `WHERE` clause, e.g. `Model.objects.filter(...).delete()`), THEN the
   compiler SHALL emit a direct `DELETE FROM <table> WHERE <condition>` statement
   and SHALL delete exactly the rows matching that condition.
3. The change SHALL affect only how the single-table decision is computed and
   the resulting statement shape; it SHALL NOT change which rows a deletion
   removes for any query, nor the cascade/fast-delete behavior for related
   objects, foreign keys, or signals.
4. The system SHALL keep producing correct, executable delete SQL for all
   existing deletion scenarios (unconditional deletes, filtered deletes,
   related/cascading deletes, and multi-table deletes), so that previously
   passing deletion behavior remains unchanged.
