# Requirements: Support sliced querysets in prefetch_related

## Introduction

When related objects are prefetched in bulk for a group of parent rows,
Django narrows the related-object query to those objects that belong to the
supplied parents. Callers may supply their own queryset to `Prefetch(...)` —
including a **sliced** queryset (e.g. "the first three related objects of each
category"). Historically this failed: bulk prefetching appends a membership
filter to the caller's queryset, but filtering a queryset that already has a
slice applied raises `AssertionError: Cannot filter a query once a slice has
been taken`, so the entire prefetch aborts.

The goal is to make bulk prefetching honor a sliced related queryset by
applying the requested slice **per parent group** (rather than to the flat
combined result), so that each parent independently receives the requested
contiguous window of its related objects in the queryset's ordering.

The affected code is the reverse foreign-key and many-to-many bulk-prefetch
paths in `django/db/models/fields/related_descriptors.py` — specifically the
`get_prefetch_queryset` methods of the reverse-FK related manager and the
many-to-many related manager (used for both the forward and reverse many-to-many
directions). Both build the related-object query by combining a membership
restriction (`<field>__in=<parents>`) with the caller-supplied queryset.

## Requirement 1: Prefetch honors a sliced reverse foreign-key queryset

**User story:** As a developer displaying a few example related objects next to
each parent, I want `prefetch_related` with a sliced queryset over a reverse
foreign-key relation to succeed, so that only a bounded number of related
objects per parent is fetched rather than all of them or an error.

**Acceptance criteria**
1. WHEN a bulk prefetch is performed over a reverse foreign-key relation using a
   caller-supplied queryset that has a slice applied, THEN the prefetch machinery
   SHALL complete without raising an error about filtering an already-sliced
   query.
2. WHEN such a sliced reverse foreign-key prefetch completes, THEN each parent
   row SHALL be associated with only the related objects that fall within the
   requested slice window computed independently for that parent.
3. The system SHALL compute the per-parent window from the slice's lower bound
   (offset) and, when present, its upper bound, treating both as absolute
   positions within each parent's group of related objects.
4. WHEN a slice specifies only a starting offset with no upper bound, THEN the
   system SHALL, for each parent, include every related object positioned beyond
   that offset.
5. WHEN a slice specifies an upper bound, THEN the system SHALL, for each parent,
   exclude related objects whose within-group position exceeds that upper bound.

## Requirement 2: Prefetch honors a sliced many-to-many queryset in both directions

**User story:** As a developer prefetching across a many-to-many relation, I
want a sliced queryset to work whether I traverse the relation forward or in
reverse, so that limiting the number of related objects per parent behaves
consistently for many-to-many relations.

**Acceptance criteria**
1. WHEN a bulk prefetch is performed over a many-to-many relation (traversed in
   the forward direction) using a caller-supplied sliced queryset, THEN the
   prefetch SHALL complete without raising an error about filtering an
   already-sliced query, and each parent SHALL receive only its related objects
   within the requested slice window.
2. WHEN a bulk prefetch is performed over a many-to-many relation (traversed in
   the reverse direction) using a caller-supplied sliced queryset, THEN the
   prefetch SHALL complete without raising an error, and each parent SHALL
   receive only its related objects within the requested slice window.
3. The system SHALL apply the same per-parent slice semantics (offset as lower
   position bound, optional upper position bound, both absolute within-group
   positions) for many-to-many relations as for reverse foreign-key relations.

## Requirement 3: Per-parent slicing respects the queryset ordering

**User story:** As a developer, I want the "first N" related objects selected by
a sliced prefetch to be determined by the queryset's ordering, so that reversing
or changing the ordering changes which related objects each parent keeps.

**Acceptance criteria**
1. The system SHALL determine each related object's within-group position using
   the ordering declared on the caller-supplied queryset, applied within the
   group of related objects sharing the same parent.
2. WHEN the caller-supplied queryset specifies an ordering, THEN the related
   objects kept for each parent SHALL be the slice window taken in that ordering.
3. WHEN the ordering is reversed, THEN the set of related objects kept for a
   parent SHALL reflect the reversed ordering (i.e. the window is taken from the
   opposite end of the group).

## Requirement 4: Membership restriction is always applied

**User story:** As a developer, I want prefetched related objects to always
belong to the parents being prefetched, so that slicing never causes objects
from unrelated parents to appear.

**Acceptance criteria**
1. The system SHALL always restrict the prefetch query to related objects whose
   grouping field references one of the supplied parent instances, regardless of
   whether a slice is present.
2. IF a slice is present, THEN the system SHALL apply the per-parent position
   conditions in addition to (not instead of) the membership restriction.
3. WHEN per-parent slice conditions are applied to the query, THEN the plain
   slice bounds SHALL be removed from the query so that the query can still be
   filtered by the membership restriction.

## Requirement 5: Unsliced prefetch behavior is preserved

**User story:** As a developer relying on ordinary prefetching, I want prefetch
of related objects with an unsliced queryset to behave exactly as before, so
that adding slice support does not regress existing prefetch functionality.

**Acceptance criteria**
1. WHEN a bulk prefetch is performed with a caller-supplied queryset that has no
   slice applied, THEN the system SHALL restrict the query solely by the
   membership restriction and SHALL NOT add any per-parent position conditions.
2. WHEN no slice is present, THEN the system SHALL leave the query's own bounds
   and other characteristics otherwise unchanged apart from the membership
   restriction.
3. The system SHALL keep prefetching all related objects for each parent when no
   slice is requested, across reverse foreign-key and many-to-many (forward and
   reverse) relations.
4. The system SHALL preserve the correct association of prefetched related
   objects to their parents (each fetched related object is attached to the
   parent it belongs to) whether or not a slice is present.
