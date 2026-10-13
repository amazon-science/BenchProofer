# Requirements: Allow `QuerySet.in_bulk()` on fields made unique by a total `UniqueConstraint`

## Introduction

`QuerySet.in_bulk(id_list=None, *, field_name='pk')` (in
`django/db/models/query.py`) returns a dictionary mapping each requested value of
`field_name` to the model instance carrying that value. Because the mapping keys
on `field_name`, the method only makes sense when that field takes a distinct
value on every row, so it guards the call: unless `field_name` is `'pk'` or names
a field that is guaranteed unique, it raises `ValueError`.

Before this change the guard accepted a non-`pk` field only when the field object
itself was declared unique (`Field.unique` is `True`, e.g. `unique=True`). It did
not recognise a field made unique by a model-level `UniqueConstraint`
(`Meta.constraints`). As a result, calling `in_bulk(field_name='slug')` on a
model whose `slug` is unique solely through a `UniqueConstraint(fields=['slug'])`
incorrectly raised `ValueError`, even though such a field is guaranteed unique
across all rows.

The goal is to broaden the guard so that a field covered by a *total* (row-wide,
unconditional) single-field unique constraint is also accepted, while continuing
to reject fields that are not guaranteed unique — including fields covered only
by a partial (conditional) constraint or only as part of a multi-field
constraint. The behavior applies to `QuerySet.in_bulk` on the query manager
(`django.db.models.query`), reading the model's constraint metadata exposed by
the model `_meta` options (`django/db/models/options.py`).

## Requirement 1: Accept a field covered by a total single-field unique constraint

**User story:** As a developer, I want `in_bulk()` to work on a field whose
uniqueness is declared through a `UniqueConstraint` rather than `unique=True`, so
that I can build value-to-object maps on such fields without an error.

**Acceptance criteria**

1. WHEN `in_bulk()` is called with a `field_name` that is not `'pk'`, and the
   named field is not itself declared unique, but the model declares a
   `UniqueConstraint` that covers exactly that one field and applies to all rows
   (i.e. it has no condition), THEN `in_bulk()` SHALL proceed without raising and
   SHALL return the value-to-object dictionary.
2. WHEN `in_bulk()` is called on such a constraint-unique field with an explicit
   list of field values, THEN the method SHALL return a dictionary mapping each
   supplied value that exists to its corresponding model instance, and SHALL omit
   values that match no row.
3. IF several model instances have distinct values for the constraint-unique
   field and all those values are requested, THEN the returned dictionary SHALL
   contain one entry per requested value, each keyed by that field value and
   mapped to the matching instance.
4. The system SHALL determine the set of fields guaranteed unique by total unique
   constraints from the model's option metadata, considering only constraints
   that cover exactly one field.

## Requirement 2: Continue rejecting fields that are not guaranteed unique

**User story:** As a developer, I want `in_bulk()` to keep rejecting field names
that are not guaranteed unique, so that I never silently build a map that drops
or overwrites rows sharing a value.

**Acceptance criteria**

1. WHEN `in_bulk()` is called with a non-`'pk'` `field_name` that is neither
   declared unique on the field itself nor covered by any total single-field
   unique constraint, THEN the method SHALL raise `ValueError`.
2. The raised `ValueError` message SHALL state that `in_bulk()`'s field name must
   be a unique field and SHALL name the offending field, matching the message
   text `in_bulk()'s field_name must be a unique field but %r isn't.` formatted
   with that field name.
3. IF a field is covered only by a *partial* unique constraint (one declared with
   a condition, so it applies to a subset of rows rather than all rows), THEN
   `in_bulk()` SHALL treat that field as not guaranteed unique and SHALL raise
   the `ValueError` described above.
4. IF a field appears only within a unique constraint that spans more than one
   field (a multi-field/`together` constraint), THEN `in_bulk()` SHALL treat that
   field as not guaranteed unique and SHALL raise the `ValueError` described
   above.

## Requirement 3: Preserve existing `in_bulk()` behavior (regression protection)

**User story:** As a maintainer, I want all previously supported `in_bulk()`
behavior to remain unchanged, so that broadening the uniqueness check introduces
no regressions.

**Acceptance criteria**

1. The system SHALL continue to accept `field_name='pk'` (the default) and return
   the mapping from primary-key value to instance.
2. WHEN `field_name` names a field that is itself declared unique
   (`unique=True`), THEN `in_bulk()` SHALL proceed and return the value-to-object
   dictionary as before.
3. WHEN `in_bulk()` is called with an empty `id_list`, THEN the method SHALL
   return an empty dictionary without querying.
4. WHEN `in_bulk()` is called with `id_list=None`, THEN the method SHALL evaluate
   the entire queryset and return the mapping for all rows.
5. The system SHALL preserve the ordering behavior of the returned values so that
   requested values retain their supplied ordering semantics as before, and SHALL
   continue to retrieve results in batches when the database limits the number of
   query parameters.
6. IF `in_bulk()` is called on a sliced queryset (one with a limit or offset
   applied), THEN the method SHALL fail as before rather than run.
