# Requirements: correct model-check validation of `Meta.ordering` lookup paths

## Introduction

Django's model system check validates every entry of a model's
`Meta.ordering`. The relevant logic lives in the model check
`Model._check_ordering` (a classmethod in `django/db/models/base.py`), which
is invoked by `Model.check()`. For each ordering entry that contains the
lookup separator (`__`), the check walks the dotted path one segment at a
time, starting from the model being checked, resolving each segment against
the current model's metadata (`Options.get_field`) and, when a segment
resolves to a relation field, advancing onto the related model. If any
segment cannot be resolved to a valid field, related traversal, or registered
transform/lookup, the check reports a single error with id `models.E015`
describing the offending path.

Two defects in this walk are in scope:

1. The primary-key alias `pk` is a valid ordering target but is not returned
   by `Options.get_field`. When `pk` appears as a segment of a *related*
   lookup path (for example an ordering entry that traverses a foreign key and
   then references `pk` on the related model), the walk fails to resolve it and
   wrongly raises `models.E015`, even though ordering by a related model's
   primary key is valid.

2. When a segment of the path resolves to a field that is **not** a relation,
   the walk must stop treating a "current model" as available for the
   remaining segments. Previously the walk kept the same current model after a
   non-relation field, so a path that continued past a non-relation field
   (referencing a further segment that happens to name another field of the
   *same* model) was wrongly accepted instead of being flagged as an invalid
   lookup path.

The goal is to make `_check_ordering` accept exactly the ordering paths that
are genuinely resolvable and to report `models.E015` for exactly those that
are not — fixing both the false positive on `pk` of a related field and the
false negative on a path that continues past a non-relation field — while
preserving all existing ordering-validation behavior.

## Requirement 1: Resolve the `pk` alias when it appears in a related lookup path

**User story:** As a Django developer, I want to be able to order a model by
the primary key of a related model (using the `pk` alias inside a dotted
ordering path), so that a valid ordering configuration is not falsely reported
as a model error.

**Acceptance criteria**

1. WHEN `Model._check_ordering` walks a related ordering path and encounters a
   segment whose value is exactly `pk`, THEN the check SHALL resolve that
   segment to the current model's primary-key field (obtained from the current
   model's metadata primary key, `Options.pk`) rather than via by-name field
   lookup.
2. WHEN an ordering entry traverses a relation and then references the `pk`
   alias on the related model (for example an entry of the form
   `<relation>__pk`), THEN `Model.check()` SHALL report no `models.E015` error
   for that entry.
3. IF the resolved primary-key field for a `pk` segment is itself a relation
   field, THEN the walk SHALL advance onto the related model it points to,
   consistent with how any other resolved relation field advances the walk.

## Requirement 2: Stop the walk after a non-relation field so trailing segments are validated

**User story:** As a Django developer, I want an ordering path that continues
past a plain (non-relation) field to be reported as invalid, so that
nonsensical lookup paths are caught by the model checks instead of silently
accepted.

**Acceptance criteria**

1. WHEN `Model._check_ordering` resolves a path segment to a field that is not
   a relation, THEN the check SHALL treat the walk as having no current model
   for any subsequent segments of that path.
2. WHILE the walk has no current model (because a preceding segment resolved to
   a non-relation field), IF a further segment appears, THEN the check SHALL
   NOT resolve that further segment as a field of any model, and SHALL report a
   single `models.E015` error naming the whole ordering entry — unless the most
   recently resolved field accepts that segment as a registered
   transform/lookup.
3. WHEN an ordering entry traverses a relation, then references a plain
   (non-relation) field on the related model, then references a further segment
   (for example an entry of the form `<relation>__<value_field>__<extra>`),
   THEN `Model.check()` SHALL report exactly one `models.E015` error for that
   entry.

## Requirement 3: Preserve existing ordering-path validation behavior

**User story:** As a Django developer, I want all previously correct ordering
validations to keep working, so that the fix does not regress the behavior of
`models.E015` checks.

**Acceptance criteria**

1. WHEN an ordering entry names a relation (foreign key) field directly, THEN
   `Model.check()` SHALL report no error for that entry.
2. WHEN an ordering entry names a field that does not exist on the model, THEN
   `Model.check()` SHALL report a `models.E015` error naming that entry.
3. WHEN an ordering entry traverses a relation to a field that does not exist
   on the related model, THEN `Model.check()` SHALL report a `models.E015`
   error naming that entry.
4. WHEN an ordering entry references a segment that is not a declared field but
   is accepted as a registered transform or lookup by the most recently
   resolved field, THEN `Model.check()` SHALL report no error for that entry.
5. WHEN an ordering entry references a nonexistent relation as its first
   segment, or otherwise cannot resolve its first segment while no field has
   yet been resolved, THEN `Model.check()` SHALL report a `models.E015` error
   naming that entry.
6. WHEN an ordering entry traverses two related-model fields that are all
   resolvable, THEN `Model.check()` SHALL report no error for that entry.
7. The system SHALL emit at most one `models.E015` error per offending
   ordering entry, with a message identifying the nonexistent field, related
   field, or lookup by the full entry text.
8. WHEN an ordering entry is a non-related simple field name that exists on the
   model, or the `pk` alias used directly (not inside a dotted path), THEN
   `Model.check()` SHALL report no error for that entry.
9. The system SHALL continue to skip ordering entries that are expressions or
   the `?` random-order marker, and SHALL continue to strip a leading `-`
   (descending) prefix before validating an entry.
