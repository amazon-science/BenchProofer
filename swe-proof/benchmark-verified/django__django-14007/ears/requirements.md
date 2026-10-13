# Requirements: Apply field value converters to values returned by a creating write

## Introduction

When Django's ORM inserts a new row, the database backend can hand back one or
more column values for that row — most commonly the freshly assigned primary
key. This happens in `SQLInsertCompiler.execute_sql`
(`django/db/models/sql/compiler.py`) via one of three backend pathways,
depending on the connection's capabilities:

* backends that can return several rows from a multi-row (bulk) write return
  those rows directly;
* backends that can return columns from a single-row write return one such row;
* otherwise a single last-inserted-id value is fetched and returned as a
  one-cell row.

For every *other* query pathway, values coming back from the database are
post-processed through the converter chain each model field declares — the same
machinery used by `SQLCompiler.get_converters` / `apply_converters`, which
includes backend converters and the field's own `from_db_value` hook. The insert
pathway was the exception: the raw values from the write were returned without
running these converters. As a result, a field whose `from_db_value` wraps a raw
integer in a wrapper object (e.g. a subclass of `BigAutoField`) got a plain
integer set on a freshly created instance instead of the wrapper — inconsistent
with the value the same field yields when the row is later read.

The goal is to make the values returned by a creating write pass through exactly
the same converter chain as values read by any ordinary query, for all three
backend pathways, while leaving every existing insert/return behavior intact.

## Requirement 1: Apply declared converters to values returned on insert

**User story:** As a developer defining a model field with a `from_db_value`
hook (for example a `BigAutoField` subclass that wraps its value), I want the
value assigned to a newly created object to be the converted/wrapped value, so
that an object obtained from `create()` behaves the same as one fetched by a
read query.

**Acceptance criteria**

1. WHEN a creating write returns one or more rows and at least one of the fields
   being returned declares a non-empty converter chain, THEN
   `SQLInsertCompiler.execute_sql` SHALL return rows in which each returned cell
   has been passed through the converter chain declared for the field in that
   cell's column position.
2. WHEN a returned field declares a `from_db_value` hook, THEN the value that
   hook produces (e.g. a wrapper object) SHALL be the value present in the
   returned rows for that field's column, rather than the raw database scalar.
3. The system SHALL build the converter chain for the returned fields using the
   same converter-resolution logic that ordinary read queries use, so that both
   backend-level converters and field-declared converters (including
   `from_db_value`) are applied in the same left-to-right order.
4. WHEN multiple returned fields each declare converters, THEN each field's
   converter chain SHALL be applied only to the cell in that field's own column
   position, leaving cells in other columns governed by their own field's chain.

## Requirement 2: Preserve returned rows unchanged when no conversion applies

**User story:** As a maintainer, I want the new conversion step to be a no-op
whenever it should be, so that existing behavior for fields and backends without
converters is unaffected.

**Acceptance criteria**

1. IF none of the fields being returned declares a converter, THEN
   `execute_sql` SHALL return the rows produced by the backend pathway unchanged.
2. WHEN a returned field declares an empty converter chain, THEN the cell in that
   field's column SHALL be returned unchanged.
3. The system SHALL leave the number of returned rows, and the number of cells
   in each row, unchanged by the conversion step.
4. IF no fields are being returned, THEN `execute_sql` SHALL return an empty
   result.

## Requirement 3: Apply conversion consistently across all return pathways

**User story:** As a developer using different database backends, I want the
converter behavior to be identical regardless of which backend return pathway is
used, so that a custom field behaves the same on every supported backend.

**Acceptance criteria**

1. WHEN the backend returns the rows of a multi-row (bulk) creating write
   directly, THEN the returned rows SHALL be post-processed through the returned
   fields' converter chains before being returned.
2. WHEN the backend returns the columns of a single-row creating write, THEN the
   single returned row SHALL be post-processed through the returned fields'
   converter chains before being returned.
3. WHEN the backend supports neither of the above and a last-inserted-id value is
   fetched, THEN the resulting one-cell row SHALL be post-processed through the
   returned fields' converter chains before being returned.
4. The system SHALL resolve the model's metadata (its table and primary-key
   column) used to fetch the last-inserted-id value consistently with the
   metadata used to build the returned-field converters.

## Requirement 4: Preserve existing insert and custom-primary-key behavior

**User story:** As a maintainer, I want the fix to protect all previously working
insert and custom-primary-key behavior, so that adding converter support
introduces no regressions.

**Acceptance criteria**

1. WHEN a single object is created via `create()` on a model with an
   auto-generated primary key, THEN the created instance SHALL have its primary
   key attribute populated with the value returned by the write (converted per
   Requirement 1 when the field declares converters).
2. WHEN objects are created via `bulk_create` on a backend that can return
   primary-key values from a bulk write, THEN each created instance SHALL have
   its primary key populated from the returned rows (converted per Requirement 1
   when the field declares converters).
3. The system SHALL continue to support models whose primary key is a custom
   field type — including creating, saving, filtering, `get`, and `in_bulk`
   lookups by both `pk` and the field's own attribute name — with unchanged
   results.
4. WHEN a required (non-nullable, non-auto) primary key is omitted on creation,
   THEN the operation SHALL still raise an integrity error.
5. The system SHALL keep unchanged the results of existing insert operations for
   fields and backends that declare no converters, including the values returned
   for the primary key.
