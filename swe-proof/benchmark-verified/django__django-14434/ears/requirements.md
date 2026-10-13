# Requirements: Unique-constraint DDL statements must correctly report the columns they reference

## Introduction

When Django's schema editor builds SQL for a unique constraint it does not emit
a raw string immediately; instead it constructs a deferred *statement* object
whose parts (the table part, the constraint-name part, and the columns part) can
later answer questions such as "does this statement reference table T?" and
"does this statement reference column C of table T?", and can be rewritten if a
table or column is renamed. This deferred machinery lives in
`django/db/backends/ddl_references.py` (the reference objects `Table`,
`TableColumns`, `Columns`, `IndexName`, `Expressions`, and the `Statement`
container). The statement for a unique constraint is assembled by
`BaseDatabaseSchemaEditor._create_unique_sql` in
`django/db/backends/base/schema.py`.

The column/table membership checks in the reference objects compare a *stored
table identifier* against the plain table-name string supplied by the caller
(`references_table(table)` and `references_column(table, column)` receive a
string). `_create_unique_sql` wrapped the model's table name in a `Table`
reference object and then handed that wrapper — rather than the plain table-name
string — to the parts that hold the columns (the `Columns`/`IndexColumns`
reference built for column-based constraints and the `Expressions` reference
built for expression-based constraints), and to the constraint-name reference.
Because a `Table` wrapper object never compares equal to a plain table-name
string, the columns part's stored table identifier never matched the queried
table, so `references_column(...)` on the resulting statement always returned
`False`, even for columns the constraint genuinely covers.

The goal is to make the unique-constraint statement report table and column
references truthfully: the parts that answer membership queries must hold the
plain table-name string, while the emitted SQL (including identifier quoting)
and the rename behavior remain exactly as before.

## Requirement 1: A unique-constraint statement reports the columns it references

**User story:** As a developer or migration author, I want the deferred
statement produced for a column-based unique constraint to correctly answer
which columns it references, so that deferred-SQL bookkeeping (dependency
tracking, safe removal, and rename rewriting) works for unique constraints.

**Acceptance criteria**

1. WHEN a unique-constraint statement is built by `_create_unique_sql` for a
   model over one or more concrete columns, THEN `references_column(table,
   column)` on the resulting statement SHALL return `True` for the model's own
   database table name together with each column the constraint was built over.
2. WHEN such a statement is queried with the model's table name and a column
   name that the constraint does NOT cover, THEN `references_column` SHALL return
   `False`.
3. WHEN such a statement is queried with a table name other than the model's own
   table, THEN `references_column` SHALL return `False` for every column.
4. The value returned by `references_column` and `references_table` SHALL be the
   boolean `True`/`False` (not a truthy/falsey object), so a caller comparing the
   result by identity to `True`/`False` observes the correct outcome.

## Requirement 2: A unique-constraint statement still reports the table it references

**User story:** As a maintainer, I want the statement to keep reporting its
table correctly, so that removing or renaming a table continues to find and
update the constraint's deferred SQL.

**Acceptance criteria**

1. WHEN a unique-constraint statement is built for a model, THEN
   `references_table` on the resulting statement SHALL return `True` for the
   model's own database table name.
2. WHEN the statement is queried with any other table name, THEN
   `references_table` SHALL return `False`.

## Requirement 3: Preserve the emitted SQL, quoting, and constraint lifecycle (regression protection)

**User story:** As a maintainer, I want the actual DDL text and the
add/remove/rename behavior of unique constraints to be unchanged, so that fixing
the reference reporting does not alter generated SQL or break existing
constraint handling.

**Acceptance criteria**

1. The system SHALL render the unique-constraint statement into the same SQL text
   as before the fix, with the table identifier and all column identifiers quoted
   exactly as they were previously (identifier quoting SHALL be preserved for
   both the table name and the column names in the generated statement).
2. WHEN a caller-supplied constraint name is provided, THEN the statement SHALL
   use that name (quoted), and WHEN no name is supplied THEN the statement SHALL
   generate the constraint name from the model's table name and the covered
   columns exactly as before.
3. WHEN a unique constraint is added and then removed through the schema editor,
   THEN the constraint SHALL no longer appear among the table's constraints after
   removal.
4. WHEN a statement for an expression-based (functional) unique constraint is
   built, THEN it SHALL report `references_table` `True` for the model's table
   and SHALL correctly answer `references_column` for the concrete columns the
   expressions resolve to, and SHALL render the same expression SQL as before.
5. WHEN a table referenced by a unique-constraint statement is renamed, THEN
   invoking the statement's table-rename operation SHALL update the statement so
   that it thereafter references the new table name (and no longer the old one)
   for both table and column queries; likewise WHEN a covered column is renamed,
   the statement's column-rename operation SHALL update which column names it
   reports referencing.
6. The system SHALL keep producing correct unique-constraint statements for the
   full range of existing cases — plain single/multi-column unique constraints,
   named constraints, partial (conditional) constraints, deferrable constraints,
   covering (include) constraints, opclass constraints, and expression-based
   constraints — with the same feature-support gating (returning no statement
   when the database backend does not support the requested constraint feature)
   and the same generated SQL as before.
