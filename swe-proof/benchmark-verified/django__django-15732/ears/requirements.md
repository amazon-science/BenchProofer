# Requirements: Drop a `unique_together` constraint when a same-columns uniqueness constraint coexists

## Introduction

When a model's `unique_together` changes, Django's schema editor must drop the
database constraint that backed each removed entry. This logic lives in
`BaseDatabaseSchemaEditor.alter_unique_together` and its helper
`BaseDatabaseSchemaEditor._delete_composed_index` in
`django/db/backends/base/schema.py`. To find the constraint to drop,
`_delete_composed_index` introspects the table via `self._constraint_names(...)`
for constraints matching the target columns and the requested kind (for the
unique-removal path, `unique=True`), then requires that **exactly one** matching
constraint be found; otherwise it raises a `ValueError` reporting the wrong
number of constraints.

This breaks whenever the same column set is covered by more than one uniqueness
constraint. Two cases occur in practice on backends that permit multiple
constraints over the same columns (e.g. PostgreSQL):

* A single-column `unique_together` (such as `(('id',),)`) over a primary-key
  column: the table then carries both the primary-key constraint and the
  `unique_together` constraint on that column. The primary key is *also*
  reported as a uniqueness constraint on the column, so the introspection finds
  two, and the drop fails.
* A single-column `unique_together` over a field that separately declares
  `unique=True`: the table carries the field's own unique constraint plus the
  `unique_together` constraint on the same column, again yielding two matches
  and a failed drop.

The goal is to let the schema editor unambiguously drop the `unique_together`
constraint in these cases — by (a) not counting the primary-key constraint as a
candidate on the unique-removal path, and (b) when several uniqueness
constraints remain over the same columns, selecting the one whose name matches
the canonical name Django generates for a `unique_together` constraint — while
preserving every existing behavior (the ordinary single-constraint drop, the
error on a genuinely ambiguous or absent constraint, index removal, and unique
constraint creation).

## Requirement 1: Ignore the primary-key constraint when dropping a removed `unique_together`

**User story:** As a Django developer who placed a `unique_together` on a
model's primary-key column and later removed it, I want the migration to drop
the `unique_together` constraint without being confused by the primary-key
constraint on the same column, so that the migration applies successfully.

**Acceptance criteria**

1. WHEN `alter_unique_together` processes a `unique_together` entry that was
   removed (present in the old value, absent from the new value), THEN the
   schema editor SHALL attempt to drop a uniqueness constraint over exactly the
   columns of that entry.
2. WHEN the schema editor searches the table for the uniqueness constraint to
   drop for a removed `unique_together` entry, THEN it SHALL exclude the
   primary-key constraint from the candidate constraints it considers, so that a
   primary-key constraint covering the same column(s) is not counted as a
   competing match.
3. WHEN a model has a single-column `unique_together` over its primary-key
   column on a backend that allows multiple constraints over the same columns,
   and that `unique_together` is removed, THEN the schema editor SHALL drop the
   `unique_together` constraint and SHALL leave the primary-key constraint in
   place.

## Requirement 2: Select the `unique_together` constraint when duplicate uniqueness constraints coexist

**User story:** As a Django developer whose column has both its own
`unique=True` constraint and a `unique_together` constraint, I want removing the
`unique_together` to drop only that constraint, so that the field keeps its own
uniqueness and the migration does not error.

**Acceptance criteria**

1. The schema editor SHALL know the canonical constraint name it generates for a
   `unique_together` constraint over a given table and column set — the same
   name it would assign when creating that constraint — so it can recognize that
   constraint among several candidates.
2. WHEN dropping a removed `unique_together` entry, AND the search for the
   uniqueness constraint returns more than one candidate, AND the backend allows
   multiple constraints over the same columns, AND one candidate's name equals
   the canonical `unique_together` constraint name for those columns, THEN the
   schema editor SHALL narrow its selection to that single candidate and SHALL
   drop exactly that constraint.
3. WHEN a model has a single-column `unique_together` over a field that also
   declares `unique=True`, on a backend that allows multiple constraints over
   the same columns, and that `unique_together` is removed, THEN the schema
   editor SHALL drop the `unique_together` constraint and SHALL leave the field's
   own unique constraint in place.
4. IF the backend does NOT allow multiple constraints over the same columns, or
   none of the discovered candidate constraints matches the canonical
   `unique_together` constraint name, THEN the schema editor SHALL NOT perform
   this narrowing and SHALL fall back to the general selection behavior described
   in Requirement 3.

## Requirement 3: Preserve the single-match and error behavior (regression protection)

**User story:** As a maintainer, I want the constraint-dropping logic to keep
raising a clear error when it cannot identify exactly one constraint to drop, so
that genuinely ambiguous or missing constraints are still reported rather than
silently mishandled.

**Acceptance criteria**

1. WHEN, after any applicable narrowing, exactly one candidate uniqueness
   constraint remains for the target columns, THEN the schema editor SHALL drop
   that one constraint.
2. IF, after any applicable narrowing, the number of candidate constraints for
   the target columns is not exactly one (zero, or more than one with no
   canonical-name match), THEN the schema editor SHALL raise a `ValueError`
   reporting the wrong number of constraints found for the table and columns,
   exactly as it did previously.
3. The schema editor SHALL continue to exclude, from the candidate constraints,
   any constraint or index named by the model's own `Meta.constraints` or
   `Meta.indexes`, so that only implicitly created `unique_together` constraints
   are considered for this drop.
4. WHEN a removed `unique_together` entry corresponds to exactly one uniqueness
   constraint over its columns (no coexisting primary-key or duplicate unique
   constraint), THEN the schema editor SHALL drop that constraint unchanged,
   without invoking the duplicate-narrowing path.

## Requirement 4: Preserve `unique_together` creation and index handling (regression protection)

**User story:** As a maintainer, I want adding a `unique_together` and altering
`index_together` to behave exactly as before, so that the fix to the removal
path does not change how constraints and indexes are created or how composed
indexes are dropped.

**Acceptance criteria**

1. WHEN `alter_unique_together` processes a newly added `unique_together` entry,
   THEN the schema editor SHALL create a uniqueness constraint over those columns
   whose name is the canonical `unique_together` constraint name for that table
   and column set — the same name later recognized on the removal path.
2. The system SHALL generate that canonical `unique_together` constraint name
   deterministically from the table name and the ordered column names, producing
   the same name for the same inputs whether it is being created or later
   matched for deletion.
3. WHEN a composed **index** (from `index_together`) is removed, THEN the schema
   editor SHALL continue to locate and drop it using a non-unique index search,
   unaffected by the uniqueness-constraint narrowing, and SHALL still raise a
   `ValueError` when it cannot identify exactly one matching index.
4. WHEN a caller supplies an explicit constraint name, THEN the schema editor
   SHALL use that provided name rather than generating the canonical one.
