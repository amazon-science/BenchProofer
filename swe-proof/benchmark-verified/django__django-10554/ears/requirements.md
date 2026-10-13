# Requirements: ORDER BY resolution for combined (union/intersect/difference) querysets

## Introduction

Django's ORM lets callers combine querysets with the set operators `union()`,
`intersection()`, and `difference()`. When such a *combined* query is compiled,
`SQLCompiler.get_order_by()` in `django/db/models/sql/compiler.py` must rewrite
each ORDER BY term into a **1-based ordinal position** referring to a column in
the query's SELECT list, because in a combined SQL statement an ORDER BY term
cannot be referenced by its fully-qualified name (the underlying sub-queries'
column names may collide or be unavailable).

To do this the compiler scans the selected columns (`self.query.select`, a
sequence whose entries carry an expression and an optional output alias) looking
for one that matches the ORDER BY term's expression, and emits that column's
1-based position. A term may instead be a *reference* to a named (aliased)
SELECT column, in which case the scan compares against the aliased column's
underlying expression.

There is a defect: when the ORDER BY term matches **no** column in the SELECT
list, the compiler unconditionally raised a database error. This breaks a
legitimate and common case — ordering a combined queryset by a column that is
not (yet) part of the selected columns, for example when the combined queryset
is later re-derived with `order_by()` / `values_list()`. In that case the
generated SQL emitted an ORDER BY position (e.g. `ORDER BY (4)`) that pointed
past the end of the select list, producing a database error such as *"ORDER BY
position N is not in select list"*.

The goal is: when an ORDER BY term over a combined query matches no already
selected column **and** the term is not a reference to a named (aliased)
column, the compiler shall add the ordered expression to the query's selected
columns and resolve the term to the position of that newly added column, rather
than failing. The genuine error condition (a term that references a named alias
which is absent from the select list) must still raise. This change touches
`SQLCompiler.get_order_by()` and adds a small helper on `Query`
(`django/db/models/sql/query.py`) that appends a column to the query's selected
columns.

## Requirement 1: Resolve an unmatched, unaliased ORDER BY column by adding it to the SELECT list

**User story:** As a developer ordering a combined (union/intersection/
difference) queryset by a column that is not among the currently selected
columns, I want the query to append that column to the select list and order by
its position, so that the combined queryset evaluates successfully instead of
raising a database error.

**Acceptance criteria**

1. WHEN compiling the ORDER BY of a combined query and an ordering term matches
   none of the currently selected columns, AND that term is **not** a reference
   to a named (aliased) selected column, THEN `get_order_by` SHALL add the
   ordered expression to the query's selected columns and resolve the term to
   the 1-based position equal to the new total number of selected columns.
2. WHEN such an ordering term is added to the selected columns, THEN the emitted
   ORDER BY position for that term SHALL refer to a column that is actually
   present in the SELECT list (i.e. the position SHALL never exceed the number
   of selected columns).
3. WHEN a combined queryset that orders by a column absent from the original
   selection is evaluated, THEN the ORM SHALL execute it without raising a
   database error and SHALL return rows ordered by that column.
4. The system SHALL provide, on the query object, a means to append a single
   column to the query's selected-columns collection, extending that collection
   by exactly that one column.

## Requirement 2: Preserve the genuine error for an unresolvable aliased reference

**User story:** As a developer, I want an ORDER BY term that references a named
column which is genuinely not part of the combined query's result columns to
still be rejected, so that truly invalid ordering is reported rather than
silently mishandled.

**Acceptance criteria**

1. IF an ordering term over a combined query matches no selected column AND the
   term is a reference to a named (aliased) selected column, THEN `get_order_by`
   SHALL raise a database error indicating that the ORDER BY term does not match
   any column in the result set.
2. The system SHALL NOT add a new selected column when raising this error.

## Requirement 3: Preserve existing resolution when a matching column exists

**User story:** As a developer, I want ordering terms that already correspond to
a selected column of a combined query to keep resolving exactly as before, so
that the fix does not change working queries.

**Acceptance criteria**

1. WHEN an ordering term over a combined query matches a selected column, THEN
   `get_order_by` SHALL resolve the term to that column's existing 1-based
   position and SHALL NOT add any new column to the select list.
2. WHEN scanning selected columns for a match, THEN the system SHALL skip
   aliased columns that are not the referenced one, and SHALL, for a reference
   term, compare against the underlying expression of the column whose alias
   matches the reference before testing subsequent columns.
3. WHEN a matching column is found, THEN the system SHALL return the position of
   the first such column encountered in the scan.

## Requirement 4: Ordering, distinct, and non-combined query behavior are unchanged

**User story:** As a maintainer, I want the broad set of existing queryset
ordering and combinator behaviors to remain intact, so that the fix is a
targeted addition rather than a regression.

**Acceptance criteria**

1. The system SHALL continue to compile ORDER BY for non-combined queries
   exactly as before, resolving terms by name/expression without converting
   them to positional ordinals.
2. WHEN the same ordering column would otherwise be emitted more than once,
   THEN `get_order_by` SHALL continue to de-duplicate it (ignoring order
   direction) so a column is not added to the ORDER BY clause twice.
3. The system SHALL keep supporting `values_list` (including flat and annotated
   selections) over combined querysets, returning the selected values ordered as
   requested.
4. WHEN a combined queryset is subsequently re-derived (for example via a fresh
   `order_by()` or `values_list()` call), THEN evaluating both the derived and
   the original queryset SHALL each succeed and SHALL not corrupt one another.
