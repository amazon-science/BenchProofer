# Requirements: Preserve nested prefetched parent objects on reverse relations

## Introduction

When Django follows a reverse many-to-one (or reverse one-to-one) relationship
with `prefetch_related()`, it fetches the set of child objects related to a set
of already-loaded parent objects. Because this bypasses the normal
`get_queryset()` path, the reverse relation is populated manually: each fetched
child object has its forward relation attribute (the pointer back to its parent)
set to the corresponding parent instance from the outer collection.

The defect is that this back-linking is done **unconditionally**. If the child
queryset itself carries a nested prefetch back to the parent (i.e. the child's
own queryset requests a prefetch of its forward relation, optionally restricting
the loaded fields), that nested prefetch has already populated each child's
forward-relation cache with a distinct parent instance — one built with its own
field/deferral selection.
Overwriting that cache with the outer parent instance silently discards the
nested prefetch. The observable symptom is that later accessing a field on the
nested parent triggers an unexpected database query, because the outer parent
instance had different fields loaded/deferred.

The affected code is the reverse-relation population loop inside the manager
produced by `create_reverse_many_to_one_manager()` in
`django/db/models/fields/related_descriptors.py`, specifically its
`RelatedManager.get_prefetch_queryset()` method. The goal is to make that loop
respect a forward-relation value that is already cached on a child object,
rather than overwriting it, while continuing to populate the reverse link for
children that do not yet have one.

## Requirement 1: Do not overwrite an already-cached forward relation

**User story:** As a developer prefetching child objects whose queryset nests a
prefetch back to the parent, I want the nested prefetched parent to be
preserved, so that accessing the parent and its fields does not trigger extra
queries and reflects the field selection I specified.

**Acceptance criteria**

1. WHEN `RelatedManager.get_prefetch_queryset()` iterates the fetched child
   objects to populate their reverse (forward-pointing) relation, THEN the
   system SHALL, for each child, first check whether that child's forward
   relation field value is already cached.
2. IF a child object already has its forward relation field value cached, THEN
   the system SHALL leave that cached value unchanged and SHALL NOT assign the
   parent instance from the outer collection onto that child.
3. WHEN a child object's already-cached forward relation was populated by a
   nested prefetch that loaded a different set of fields, THEN the system SHALL
   preserve that nested instance so that subsequently reading its attributes
   performs no additional database query.
4. The system SHALL determine "already cached" using the forward relation
   field's own cache-presence check, so that the presence test matches the same
   cache slot that assigning the relation would write to.

## Requirement 2: Still populate the reverse relation when it is not cached

**User story:** As a developer using ordinary reverse-relation prefetching, I
want prefetched child objects to point back at their parent, so that traversing
from a child to its parent does not hit the database.

**Acceptance criteria**

1. IF a fetched child object does not already have its forward relation value
   cached, THEN the system SHALL look up the corresponding parent instance for
   that child and assign it as the child's forward relation value.
2. WHEN parent instances are matched to children, THEN the system SHALL match
   each child to the parent whose related-field value equals the child's
   corresponding related-field value, preserving the existing correspondence
   between child and parent.
3. The system SHALL keep returning the same prefetch descriptor information
   (the fetched queryset, the child- and parent-side related-value accessors,
   the single-value flag, the cache name, and the fetched-flag) that callers of
   `get_prefetch_queryset()` rely on, unchanged in shape and meaning.

## Requirement 3: Preserve existing prefetch behavior (regression protection)

**User story:** As a Django user relying on the full range of
`prefetch_related()` features, I want this change to affect only the
overwrite-a-cached-relation case, so that all other prefetch behaviors continue
to work exactly as before.

**Acceptance criteria**

1. The system SHALL continue to correctly prefetch reverse foreign-key and
   reverse one-to-one relations, populating the reverse link on children that
   have no cached forward relation.
2. The system SHALL continue to support forward and reverse many-to-many
   prefetching, generic-relation prefetching, and chains that follow one
   relation type after another, without change in results or query behavior.
3. WHEN prefetches are nested across multiple levels, THEN the system SHALL NOT
   introduce duplicate queries for a relation that has already been prefetched.
4. The system SHALL continue to honor custom `Prefetch()` querysets, `to_attr`
   targets, `only()`/`defer()` field selections, and multi-database routing on
   prefetched relations.
5. WHEN a child object receives its parent from the outer collection because no
   forward relation was cached, THEN the system SHALL leave that assignment
   observationally identical to the prior behavior (same parent instance,
   accessible without an extra query).
