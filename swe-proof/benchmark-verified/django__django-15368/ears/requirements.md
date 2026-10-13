# Requirements: `QuerySet.bulk_update()` handling of expression-valued field assignments

## Introduction

`QuerySet.bulk_update(objs, fields)` (in `django/db/models/query.py`) writes the
current in-memory value of each named field on each object to the database using
a single conditional `UPDATE`. It does this by building, for every field, a
`CASE`/`WHEN` statement: one `WHEN pk=<obj.pk> THEN <value>` branch per object,
keyed on the object's primary key.

For each branch, `bulk_update()` must decide whether the object's field value is
an ordinary stored value (a string, number, date, …) that should be written as a
literal, or a query expression that should be embedded into the SQL and resolved
by the database. Ordinary values are wrapped in `django.db.models.expressions.Value`
so the backend stores them verbatim; expressions are passed through unwrapped so
the backend resolves them (for example, to another column).

The defect: the code decides "is this an expression?" with a check that is too
narrow. A plain field-reference expression such as `F('name')` assigned to a
model field is **not** recognized as an expression, so it is wrapped as a literal
and the database stores the object's textual representation (e.g. the string
`"F(name)"`) instead of resolving it to the referenced column's value. Any value
that can act as a query expression — whether a full computed expression node or a
bare field reference like `F(...)` — must be treated as an expression and passed
through unwrapped.

The goal is to broaden the recognition so that every value capable of resolving
as a query expression is embedded and resolved, while genuinely plain values
remain wrapped as literals, and all previously working `bulk_update()` behavior
is preserved.

## Requirement 1: Field references assigned via `F(...)` are resolved, not stringified

**User story:** As a developer, I want to assign a plain `F('other_field')`
expression to a model instance field and persist it with `bulk_update()`, so that
the database resolves the referenced column instead of storing the textual repr of
the expression.

**Acceptance criteria**

1. WHEN a model instance has a field set to a bare field-reference expression
   (an `F(...)` naming another field/column) and that object is passed to
   `bulk_update()` for that field, THEN `bulk_update()` SHALL emit the value into
   the update as an unwrapped expression so the database resolves it to the
   referenced column's value.
2. WHEN such a `bulk_update()` completes, THEN the persisted value of the target
   field, after reloading the affected rows from the database, SHALL equal the
   current value of the referenced field (the value the `F(...)` names), NOT the
   textual representation of the expression object.
3. The system SHALL NOT wrap a field-reference expression value in a literal
   value wrapper before placing it into the conditional update branch.

## Requirement 2: Expression detection recognizes any resolvable value

**User story:** As a developer, I want `bulk_update()` to treat every value that
behaves as a query expression as an expression, so that all expression kinds —
not only certain subclasses — are embedded and resolved rather than stored as
literals.

**Acceptance criteria**

1. WHEN building the per-object conditional branch for a field, IF the object's
   field value is capable of resolving as a query expression (i.e. it exposes the
   expression-resolution behavior common to expression values, including both
   full computed expression nodes and bare field references), THEN `bulk_update()`
   SHALL use that value unchanged as the branch result and SHALL NOT wrap it in a
   literal value wrapper.
2. WHEN building the per-object conditional branch for a field, IF the object's
   field value is an ordinary stored value that is not a resolvable query
   expression, THEN `bulk_update()` SHALL wrap it in a literal value wrapper bound
   to that field so the backend stores it verbatim.
3. The system SHALL apply this wrapped-versus-unwrapped decision independently for
   each object and each named field, keying each produced branch on that object's
   own primary key and carrying that object's own value.

## Requirement 3: Preserve existing `bulk_update()` behavior

**User story:** As a maintainer, I want the broadened expression handling to leave
all other `bulk_update()` behavior unchanged, so that existing usage continues to
work.

**Acceptance criteria**

1. WHEN a field is assigned an ordinary Python value (string, boolean, number,
   datetime, IP address, JSON-serializable value, `None`, and similar), THEN
   `bulk_update()` SHALL persist that exact value, and reloading the row SHALL
   return that value unchanged.
2. WHEN a field is assigned a computed query expression (for example an arithmetic
   combination of fields or a database function applied to a column), THEN
   `bulk_update()` SHALL embed and resolve that expression, persisting the computed
   result rather than a literal.
3. WHEN `bulk_update()` is called, THEN it SHALL retain all existing validation and
   control behavior: it SHALL reject a negative batch size, SHALL require a
   non-empty list of field names, SHALL require every object to have a primary key
   set, SHALL accept only concrete non-many-to-many fields, SHALL reject primary
   key fields, and SHALL return `0` without querying when given no objects.
4. WHEN `bulk_update()` is given more objects than fit in one batch, THEN it SHALL
   split the work into batches and SHALL return the total number of rows updated
   across all batches.
5. WHEN multiple fields are updated at once, or when a field maps to a custom
   database column name, or when the model uses a custom or inherited primary key,
   THEN `bulk_update()` SHALL persist each specified field's value correctly for
   every object.
6. WHEN a field is explicitly set to `None` (including a mix of null and non-null
   values across objects), THEN `bulk_update()` SHALL persist `NULL` for those
   objects.
