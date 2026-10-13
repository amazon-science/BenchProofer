# Requirements: default-ordering expansion must tolerate expression items during ORDER BY compilation

## Introduction

When Django compiles a query's `ORDER BY` clause, it resolves each ordering
entry into concrete column ordering directives. This happens in
`SQLCompiler.find_ordering_name` (`django/db/models/sql/compiler.py`). When the
name being ordered by is a relation to another model — for example a
multi-table-inheritance parent link — and that related model defines a default
ordering (`Meta.ordering`), the compiler expands the related model's default
ordering by iterating over its ordering specification and resolving each item.

The historical implementation assumed every item in `Meta.ordering` was a
textual field name: it fed each item back through
`find_ordering_name`, which begins by calling `get_order_dir` in
`django/db/models/sql/query.py`. `get_order_dir` indexes the value as a string
(`field[0]`). Since Django allows an already-built ordering-expression object —
specifically an `OrderBy` instance, such as the result of `F(...).asc()` /
`F(...).desc()` — to appear in `Meta.ordering`, such an item is not a string.
Passing it through name resolution raised an error
(`'OrderBy' object is not subscriptable`), so ordering a model by a relation to
a parent/related model whose `Meta.ordering` contained an `OrderBy` item
crashed.

The goal is to make the per-item expansion of a related model's default ordering
dispatch on whether the item is an already-built `OrderBy` instance: an `OrderBy`
item must be emitted directly as an ordering directive, while textual field
references continue to be resolved by name — without disturbing any existing
ordering behavior. The change is scoped to `OrderBy` items on this relational
expansion path; other kinds of expression objects on that path are outside the
scope of this change.

## Requirement 1: Emit already-formed ordering expressions directly when expanding a related model's default ordering

**User story:** As a developer who defines a model's `Meta.ordering` using an
`OrderBy` expression (for example `F(...).asc()`/`F(...).desc()`), I want to
order a queryset by a relation (including a multi-table-inheritance parent link)
to that model, so that the query executes correctly instead of crashing.

**Acceptance criteria**

1. WHEN `SQLCompiler.find_ordering_name` expands a related model's default
   ordering and encounters an item of `Meta.ordering` that is an instance of
   `OrderBy`, THEN the compiler SHALL emit that `OrderBy` item directly as one
   resolved ordering directive rather than passing it through field-name
   resolution.
2. WHEN such an `OrderBy` item is emitted directly, THEN the compiler
   SHALL pair it with the boolean flag value `False` (the "is-reference" flag),
   indicating the surrounding sort direction is not re-derived or re-applied to
   it.
3. IF an item of the related model's `Meta.ordering` is an instance of
   `OrderBy`, THEN the compiler SHALL NOT invoke `get_order_dir` (or otherwise
   index/parse the item as a string) on that item, so that no
   "not subscriptable" error is raised for that item.
4. WHEN a model whose `Meta.ordering` contains one or more `OrderBy` items is
   ordered by a relation to it (for example, ordering a child model by its
   parent-link pointer field so that the parent model's default ordering is
   applied), THEN the resulting queryset SHALL be returned in the order dictated
   by that default ordering without raising an exception.
5. WHILE expanding a related model's default ordering that mixes `OrderBy` items
   and textual field-name items, the compiler SHALL preserve the original
   order of the specification: each item's contribution SHALL appear in the
   final list of ordering directives in the same relative position as its item,
   and the overall result SHALL be the in-order concatenation of every item's
   expansion.

## Requirement 2: Continue resolving textual field references by name

**User story:** As a developer relying on the existing default-ordering
behavior, I want string field names in `Meta.ordering` to keep resolving exactly
as before, so that ordering by relations continues to work unchanged.

**Acceptance criteria**

1. WHEN `SQLCompiler.find_ordering_name` expands a related model's default
   ordering and encounters an item that is a textual field reference (a string,
   possibly a multi-part `field1__field2__…` lookup, optionally prefixed with
   `-`), THEN the compiler SHALL resolve that item through the existing
   name-resolution routine to produce its concrete column ordering directive(s).
2. The system SHALL continue to detect and reject infinite ordering loops (a
   relation whose default ordering cycles back on itself) with a field error
   when expanding a related model's default ordering.
3. WHEN a related model's `Meta.ordering` contains only textual field
   references, THEN the set of ordering directives produced SHALL be identical
   to that produced before this change.

## Requirement 3: Preserve all existing ordering behaviors (regression protection)

**User story:** As a maintainer, I want every previously supported ordering
scenario to keep working, so that this fix introduces no regressions.

**Acceptance criteria**

1. The system SHALL keep applying a model's default `Meta.ordering` to
   querysets that do not specify an explicit `order_by()`.
2. The system SHALL keep supporting query expressions (e.g. `F(...)` with
   `.asc()`/`.desc()`, including `nulls_first`/`nulls_last`) used directly in a
   queryset's `order_by(...)` call, producing the requested ordering.
3. The system SHALL keep supporting query expressions used in a model's
   `Meta.ordering` for ordinary (non-relational) default ordering of that
   model's own querysets.
4. WHEN an explicit ordering is requested via `order_by(...)`, THEN the compiler
   SHALL honor ascending/descending direction, `-` prefixes, `nulls_first` and
   `nulls_last` placement, and ordering by primary key, related-object attribute
   names, and foreign-key attribute names, exactly as before.
5. The system SHALL keep supporting reversed ordering (`reverse()`),
   overriding a model's default ordering via an explicit `order_by()`, and
   ordering by constant values, without regression.
6. The system SHALL keep supporting `extra(order_by=...)` ordering, including
   quoted and table-qualified column names, without regression.
7. The system SHALL keep supporting ordering by a random value and SHALL keep
   the documented deprecation behavior for using `Meta.ordering` with
   `values()`/`annotate()`, without regression.
8. WHEN ordering causes the same related table to be referenced more than once,
   THEN the compiler SHALL keep producing correct ordering directives without
   duplicate-reference errors, and SHALL keep not re-ordering a queryset after
   slicing.
