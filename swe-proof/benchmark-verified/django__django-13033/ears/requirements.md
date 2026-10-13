# Requirements: Ordering a queryset by a related field's stored column

## Introduction

When a Django queryset is ordered by a lookup path that traverses one or more
relations, the SQL ORDER BY is built in
`SQLCompiler.find_ordering_name(self, name, opts, alias=None, default_order='ASC', already_seen=None)`
(`django/db/models/sql/compiler.py`). The lookup path is a string of segments
joined by the lookup separator `"__"` (for example `record__root_id`), resolved
to a model field.

When the resolved field is itself a relation to another model, the compiler may
append that related model's declared default ordering (its `Meta.ordering`)
instead of ordering by a single concrete column. This default-ordering
expansion is intended to happen only when the caller has NOT already designated
a concrete stored column of the relation.

The defect: when the ordering path directly designates a relation's stored
column via a multi-segment lookup whose final segment names the field's own
stored attribute (for example `record__root_id`, whose final segment `root_id`
is the foreign key's stored attribute), the compiler nevertheless expanded the
related model's default ordering. This produced an unnecessary extra JOIN and
applied the related model's default sort direction (for example a descending
sort inherited from `Meta.ordering = ("-id",)`) rather than ordering directly
by the designated column in the requested direction.

The goal is to make the expansion decision compare the field's stored attribute
against the FINAL segment of the lookup path, so that a lookup ending in the
relation's own `_id` column orders directly by that column, while all other
ordering behaviors are preserved.

## Requirement 1: Order directly by a relation's stored column when the lookup path's final segment names it

**User story:** As a developer, I want ordering a queryset by a multi-segment
lookup that ends in a relation's stored column (its `_id` attribute) to sort
directly by that column in the direction I requested, so that I do not get an
unexpected sort direction or extra joins inherited from the related model's
default ordering.

**Acceptance criteria**

1. WHEN a queryset is ordered by a lookup path whose resolved field is a
   relation to another model AND whose final `"__"`-separated segment equals
   that field's own stored attribute name, THEN the compiler SHALL order by
   that field's stored column directly and SHALL NOT append the related
   model's default ordering.
2. WHEN such a lookup is used, THEN the resulting query SHALL NOT introduce the
   additional join that expanding the related model's default ordering would
   require.
3. WHEN such a lookup is requested in ascending direction, THEN the ordering
   SHALL be ascending on the designated stored column, regardless of the
   related model's declared default ordering direction.
4. WHEN such a lookup is requested in descending direction (a leading `-`
   prefix on the path), THEN the ordering SHALL be descending on the designated
   stored column, regardless of the related model's declared default ordering
   direction.
5. IF the resolved field is a self-referential foreign key (the relation points
   back to the same model), THEN the behavior in criteria 1–4 SHALL still hold;
   the self-reference SHALL NOT cause the related model's default ordering to be
   expanded when the final segment names the field's stored attribute.

## Requirement 2: Expand the related model's default ordering only when the lookup does not designate a concrete column

**User story:** As a developer, I want ordering by a bare relation (without
naming its stored column) to still fall back to the related model's default
ordering, so that existing relation-ordering behavior is preserved.

**Acceptance criteria**

1. WHEN a queryset is ordered by a lookup whose resolved field is a relation,
   the related model declares a non-empty default ordering, the lookup is not
   the primary-key shortcut, AND the lookup path's final segment does NOT equal
   the field's stored attribute name, THEN the compiler SHALL append the related
   model's default ordering.
2. IF the resolved field is not a relation, THEN the compiler SHALL order by the
   resolved column directly and SHALL NOT append any related model's default
   ordering.
3. IF the related model declares no default ordering, THEN the compiler SHALL
   order by the resolved column directly and SHALL NOT append any default
   ordering.
4. The system SHALL determine whether to expand the related model's default
   ordering solely from: whether the resolved field is a relation; whether the
   related model declares a non-empty default ordering; whether the lookup is
   the primary-key shortcut `pk`; and whether the lookup path's final segment
   equals the field's stored attribute name.

## Requirement 3: Preserve the primary-key shortcut and direct attribute ordering

**User story:** As a developer, I want ordering by `pk` and by a foreign key's
attribute name to keep working exactly as before, so that these established
shortcuts are not regressed by the fix.

**Acceptance criteria**

1. WHEN a queryset is ordered by the primary-key shortcut `pk`, THEN the
   compiler SHALL order by the primary-key column directly and SHALL NOT expand
   any related model's default ordering.
2. WHEN a queryset is ordered by a foreign key's stored attribute name directly
   (a single-segment lookup naming the `_id` column on the queried model), THEN
   the compiler SHALL order by that column directly and SHALL NOT expand the
   related model's default ordering.
3. WHEN a queryset is ordered by a lookup path that explicitly descends to the
   related model's primary key (for example ending in `__id`), THEN the compiler
   SHALL order directly by that primary-key column without expanding the related
   model's default ordering.

## Requirement 4: Confine the change to the expansion decision and preserve all other ordering behavior

**User story:** As a developer, I want the fix to be surgical, so that only the
relation-stored-column ordering decision changes and every other established
ordering behavior stays exactly as it was before the change.

**Acceptance criteria**

1. The system SHALL continue to apply a model's declared default ordering to a
   queryset when no explicit ordering is requested.
2. WHEN an explicit ordering is requested on a queryset, THEN it SHALL take
   precedence over and override the model's declared default ordering.
3. WHEN a reversed ordering is requested, THEN the compiler SHALL invert the
   effective ordering, including inverting a model's declared default ordering
   under reversal.
4. WHILE resolving an ordering that could recurse through a relation's default
   ordering, the compiler SHALL detect and reject a cycle that would otherwise
   cause an infinite loop, raising the established ordering error.
5. The behavioral change SHALL be confined to the default-ordering-expansion
   decision described in Requirements 1–3; for any ordering whose resolved field
   and lookup path do not meet the conditions under which that decision changed,
   the compiler SHALL produce the same ordering result it produced before the
   change.
