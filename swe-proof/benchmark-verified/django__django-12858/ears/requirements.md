# Requirements: Model ordering system check must accept lookups, not only transforms

## Introduction

Django's model system check `Model._check_ordering` (in
`django/db/models/base.py`) validates every entry of a model's
declared `ordering` option. Each entry is a string that may traverse relations by joining
name segments with the relation separator `__` (for example
`supply__product__parent__isnull`). The check walks an entry segment by
segment, starting from the model that declares the ordering, resolving each
segment against the current model's fields and descending into related models
when a segment resolves to a relation field. If a segment cannot be resolved as
a field, the check must decide whether the entry names something legitimate (a
transform or a registered lookup of the preceding field) or something that does
not exist, in which case it reports a `models.E015` error.

The defect: the walk only accepted an unresolved trailing segment when it named
a **transform** of the preceding field. A segment that names a registered
**lookup** (for example `isnull`) — which is a valid ordering directive and
works at query time — was wrongly reported as `models.E015` ("'ordering'
refers to the nonexistent field, related field, or lookup '...'"). The goal is
to make the check accept an unresolved segment that names either a transform or
a registered lookup of the preceding field, while continuing to report genuinely
nonexistent fields and lookups, and preserving all other ordering-check
behavior.

## Requirement 1: Ordering entries ending in a registered lookup pass the check

**User story:** As a Django developer, I want to declare a model `ordering`
entry whose final segment is a registered lookup (such as `isnull`) on the
preceding field, so that running the system check does not report a spurious
`models.E015` error for an ordering that is valid at query time.

**Acceptance criteria**

1. WHEN a model declares an `ordering` entry consisting of a resolvable local
   field segment immediately followed by a segment that names a registered
   lookup of that field, THEN `Model._check_ordering` SHALL NOT emit a
   `models.E015` error for that entry.
2. WHEN a model declares an `ordering` entry that traverses one or more relation
   fields and whose final segment names a registered lookup of the last
   resolved field, THEN `Model._check_ordering` SHALL NOT emit a `models.E015`
   error for that entry.
3. IF the preceding resolved field has a registered lookup matching an
   otherwise-unresolvable segment, THEN the check SHALL treat that segment as a
   legitimate ordering directive rather than a nonexistent field, related
   field, or lookup.
4. The system SHALL accept a segment as legitimate when it names either a
   transform OR a registered lookup of the preceding resolved field.

## Requirement 2: Existing acceptance of transforms is preserved

**User story:** As a Django developer, I want ordering entries whose final
segment is a registered transform of the preceding field to keep passing the
system check, so that the fix for lookups does not regress transform handling.

**Acceptance criteria**

1. WHEN a model declares an `ordering` entry whose final segment names a
   registered transform of the preceding resolved field, THEN
   `Model._check_ordering` SHALL NOT emit a `models.E015` error for that entry.
2. The system SHALL continue to accept transform segments regardless of whether
   the same segment is also a registered lookup.

## Requirement 3: Genuinely invalid ordering entries are still reported

**User story:** As a Django developer, I want the system check to keep reporting
ordering entries that reference fields, related fields, or lookups that do not
exist, so that real configuration mistakes are still caught.

**Acceptance criteria**

1. WHEN an `ordering` entry contains a segment that resolves to no field of the
   current model context and is neither a transform nor a registered lookup of
   the preceding resolved field, THEN `Model._check_ordering` SHALL emit a
   `models.E015` error naming that entry.
2. IF an unresolvable segment has no preceding resolved field to interpret it
   against (for example the very first segment of the entry does not name a
   field), THEN the check SHALL emit a `models.E015` error for that entry.
3. WHEN an `ordering` entry names a related model's field that does not exist,
   or references a field on a non-relational field as if it were a relation,
   THEN `Model._check_ordering` SHALL emit a `models.E015` error for that entry.
4. The system SHALL keep reporting `models.E015` for a relation-spanning entry
   whose intermediate segment cannot be resolved and is not a valid transform or
   lookup of the field preceding it.

## Requirement 4: Ordering-check behavior unaffected by the fix is preserved

**User story:** As a Django developer, I want all other ordering validation
behavior to remain unchanged, so that the lookup fix does not alter unrelated
system-check outcomes.

**Acceptance criteria**

1. WHEN a model's declared `ordering` option is not a list or tuple, THEN the check SHALL
   emit a `models.E014` error and SHALL NOT be affected by the lookup handling.
2. WHEN a model declares `order_with_respect_to`, or declares no `ordering`,
   THEN `Model._check_ordering` SHALL report no ordering errors.
3. The system SHALL continue to skip the special `?` random-ordering entry and
   any non-string ordering entries when validating ordering.
4. The system SHALL continue to accept ordering by `pk` and by valid local or
   related fields without emitting `models.E015`.
5. WHEN a leading `-` (descending marker) prefixes an ordering entry, THEN the
   check SHALL validate the entry as if the marker were absent, applying the
   same acceptance and reporting rules.
6. WHEN an `ordering` entry names the same set of model fields validly across
   one or more relations, THEN `Model._check_ordering` SHALL report no error for
   those entries.
