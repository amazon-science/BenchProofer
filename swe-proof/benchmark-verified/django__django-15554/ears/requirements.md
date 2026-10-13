# Requirements — Multiple `FilteredRelation` on the same relation

## Introduction

Django's ORM lets a caller attach a `FilteredRelation` to a queryset (via
`QuerySet.annotate()` / `QuerySet.alias()`), producing a named join whose
`ON` clause carries an extra `condition`. Internally the query object keeps an
ordered registry of the joins it has already introduced (`Query.alias_map`),
each stored under a distinct table alias. When a new join is requested,
`django.db.models.sql.query.Query.join()` decides whether to reuse an existing
alias or allocate a fresh one.

The defect: when two `FilteredRelation` annotations name the **same** underlying
relation but supply **different** conditions (for example, following the same
nested relation twice, where one annotation matches rows by a per-zone condition
and the other matches an "is-all" fallback condition, as in the reported
scenario), the second annotation is silently dropped. Only one
SQL join is emitted and both annotations resolve against it, so one of the two
filtered relations is ignored. This happens because the alias-reuse test
compares joins by their *structural* identity only — table, parent alias and
relating field — and deliberately ignores the attached filter. Two joins on the
same base relation therefore look interchangeable even though their conditions
differ.

The goal is to make each distinct `FilteredRelation` on the same relation
receive its own join and alias, so that a value selected through one filtered
relation reflects that annotation's own condition and is independent of any
sibling `FilteredRelation` on the same relation — while every existing
`FilteredRelation` behavior (single filtered relation, m2m, nested relations,
select/values, unions, exclude, etc.) is preserved unchanged.

The affected code is `django/db/models/sql/query.py` (the join-allocation and
filter-building path used while resolving filtered relations), leaning on the
join comparison semantics in `django/db/models/sql/datastructures.py`
(`Join.equals` = structural match ignoring the filter; `Join.__eq__` = full
match including the filter).

## Requirement 1: Distinct filtered relations on the same relation each get their own join

**User story:** As a developer, I want to annotate a queryset with several
`FilteredRelation` objects that follow the same relation but apply different
conditions, so that each one contributes its own filtered join instead of being
collapsed into a single join.

**Acceptance criteria**

1. WHEN a queryset is annotated (or aliased) with two or more `FilteredRelation`
   objects that follow the same underlying relation but carry different
   `condition` arguments, THEN the query SHALL emit a separate join for each such
   `FilteredRelation`, each under its own distinct alias.
2. WHEN such a queryset is compiled to SQL, THEN the resulting query SHALL NOT
   drop or ignore any of those `FilteredRelation` annotations; every one of them
   SHALL be represented by its own join in the query.
3. IF two joins on the same base relation carry different filter conditions,
   THEN the alias-allocation step SHALL treat them as non-interchangeable and
   SHALL NOT reuse one relation's alias for the other.
4. WHEN a value is selected through one such `FilteredRelation` (for example via
   `.values()` on `"<relation_alias>__<field>"`), THEN that value SHALL be
   computed against that annotation's own condition, independently of the other
   `FilteredRelation` annotations on the same relation.

## Requirement 2: Correct per-row results for multiple filtered relations on the same relation

**User story:** As a developer, I want each filtered relation's selected columns
to reflect exactly its own condition, so that combining several of them in one
query returns the values I expect for every row.

**Acceptance criteria**

1. WHEN a queryset annotates the same relation with two `FilteredRelation`
   objects whose conditions match disjoint (or differing) subsets of the related
   rows, and selects a field through each, THEN for every result row each
   selected column SHALL reflect the related row that satisfies that column's own
   `FilteredRelation` condition.
2. WHEN a given `FilteredRelation`'s condition matches no related row for a
   result row, THEN the field selected through that filtered relation SHALL be
   reported as the backend's standard "no value" marker for an unmatched outer
   join, rather than borrowing a value that satisfies a different filtered
   relation's condition.
3. WHILE both `FilteredRelation` annotations are present in the same query, the
   presence of one SHALL NOT alter the rows or values produced through the other.

## Requirement 3: Reuse remains confined to the relation's own path when resolving a filtered relation

**User story:** As a maintainer, I want the alias-reuse behavior while building a
filtered relation's condition to stay scoped to that relation's own joins, so
that filtered relations neither leak onto unrelated joins nor collapse onto each
other.

**Acceptance criteria**

1. WHILE resolving the condition attached to a `FilteredRelation`, the query
   SHALL only reuse an existing alias when that alias belongs to the set of
   aliases reachable along that relation's own path, and SHALL otherwise allocate
   a fresh alias.
2. IF an alias is both permitted for reuse (belongs to that relation's own path)
   and structurally compatible with the requested join, THEN the query SHALL
   reuse it rather than allocating a new alias.
3. The system SHALL continue to allocate a fresh alias, rather than reuse an
   arbitrary existing one, when no permitted-and-compatible alias exists.

## Requirement 4: Preserve all existing FilteredRelation behavior (regression protection)

**User story:** As a maintainer, I want the fix for same-relation filtered
relations to leave every other `FilteredRelation` behavior untouched, so that
existing queries keep producing identical results.

**Acceptance criteria**

1. WHEN a queryset uses a single `FilteredRelation` and selects a field through
   it (including with an extra `.filter()`), THEN the results SHALL be identical
   to the prior behavior.
2. WHEN a `FilteredRelation` follows a nested relation, a deeper foreign key, a
   foreign key on the base object, or a many-to-many relation (including deep and
   multijoin cases), THEN the join(s) SHALL be produced and the results SHALL
   match the prior behavior.
3. WHEN the same `FilteredRelation` alias is referenced multiple times within a
   query, THEN it SHALL still resolve to a single join (unchanged behavior), and
   SHALL NOT be duplicated.
4. WHEN a `FilteredRelation` is combined with `values()`, `values_list()`,
   `select_related`, `defer`/`only` (where supported), `exclude`, `Q`-based joins
   with complex conditions, generic foreign keys, prefetch, aggregation, or set
   operations (`union`/`intersection`/`difference`) and subqueries, THEN the
   behavior SHALL remain as before this change.
5. WHEN a `FilteredRelation` is constructed with an invalid argument (a
   condition given as a bare expression, an empty relation name, or `only` where
   it is not supported), THEN the query SHALL still raise the same error as
   before.
6. WHEN two equality-comparable `FilteredRelation` objects are compared, THEN
   their equality semantics SHALL be unchanged.
7. WHEN a queryset uses a `FilteredRelation` without selecting through it (no
   dependent join needed), THEN the compiled query SHALL still omit the join, as
   before.
8. The system SHALL preserve the internal alias-mapping and the generated SQL
   text for all queries that involve at most one `FilteredRelation` per distinct
   relation.
