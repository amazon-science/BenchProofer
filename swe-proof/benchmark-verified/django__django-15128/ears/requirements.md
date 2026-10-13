# Requirements — django__django-15128

## Introduction

Combining two `QuerySet`s with the OR operator (`|`) can raise an
`AssertionError` deep inside `django.db.models.sql.query.Query`. The failure
happens in `Query.combine` (invoked by `QuerySet.__or__`) when the two queries
being merged use the same alias prefix and their table aliases collide: the
right-hand-side query's joins are relabeled into the combined query, and the
resulting rename map (`change_map`) can end up with an alias that appears both
as a key and as a value (for example, a plan that maps one alias `T4 → T5`
while also mapping `T5 → T6`). Such a plan would rename a single alias twice,
so the disjointness assertion at the top of `Query.change_aliases` fires and the
whole OR operation crashes.

Because the crash depends on join ordering, the OR of two querysets is not
symmetric today: one ordering can succeed while the reverse ordering raises.

The goal is to make OR-combination of querysets robust and order-independent.
The affected code is `Query.combine`, `Query.bump_prefix`, and
`Query.change_aliases` in `django/db/models/sql/query.py`. The fix renumbers the
right-hand query's aliases under a fresh, non-conflicting prefix *before*
building the merge rename map, while preserving the shared base-table alias that
must be identical on both sides of the combination.

## Requirement 1: OR-combining querysets that share alias prefixes must not crash

**User story:** As a developer building queries with `|`, I want to OR two
querysets together even when they internally use overlapping table aliases, so
that combining querysets never raises an unexpected internal error.

**Acceptance criteria**
1. WHEN two querysets over the same base model are combined with the OR
   connector, and both underlying queries currently use the same alias prefix
   with overlapping alias names, THEN `Query.combine` SHALL complete without
   raising `AssertionError`.
2. WHEN combining two querysets with OR, THEN the disjointness invariant of the
   alias rename map SHALL hold: the set of aliases being renamed (the keys of
   the rename map) SHALL NOT intersect the set of new alias names (its values),
   so that no alias is scheduled to be renamed twice.
3. WHEN a queryset that already contains related-table joins is OR-combined with
   another queryset whose joins would reuse the same alias names, THEN the
   combined query SHALL be produced with a consistent, collision-free set of
   table aliases.

## Requirement 2: OR-combination is order-independent

**User story:** As a developer, I want `a | b` and `b | a` to behave the same,
so that the result of OR-combining querysets does not depend on operand order.

**Acceptance criteria**
1. WHEN two querysets are combined with OR in either order, THEN both orderings
   SHALL succeed (neither ordering raises where the other does not).
2. WHEN two querysets are combined with OR in either order, THEN both orderings
   SHALL return the same set of result rows (equal as unordered collections).
3. The system SHALL preserve the existing filtering semantics of an OR
   combination: the combined queryset SHALL match exactly the rows that satisfy
   either operand's conditions, unchanged from prior behavior aside from the
   alias-collision fix.

## Requirement 3: Relabel the right-hand query onto a fresh prefix while preserving the base alias

**User story:** As a maintainer of the query-combining logic, I want the
right-hand query's aliases moved out of the way before the merge, so that its
aliases cannot collide with the left-hand query's aliases during relabeling.

**Acceptance criteria**
1. WHEN merging a right-hand query into a left-hand query during combination,
   THEN the right-hand query's aliases SHALL first be renumbered under a fresh
   alias prefix that does not conflict with the left-hand query's aliases.
2. The system SHALL leave the base (initial) table alias of the right-hand query
   unchanged during this renumbering, because that alias denotes the same base
   table present on both sides of the combination and must remain identical
   across both queries.
3. WHEN renumbering the right-hand query's aliases, THEN the left-hand query's
   initial/base table alias SHALL be established and reused as the shared base
   alias, so the merge does not create a second alias for the common base table.
4. IF the two queries do not share an alias prefix (no collision is possible),
   THEN the renumbering step SHALL make no change to the right-hand query's
   aliases.

## Requirement 4: Prefix-renumbering may preserve a designated set of aliases

**User story:** As a caller of the alias-renumbering routine, I want to renumber
a query's aliases while keeping selected aliases fixed, so that aliases which
must stay stable (such as a shared base-table alias) are not renamed.

**Acceptance criteria**
1. The system SHALL allow `Query.bump_prefix` to be invoked with an optional set
   of aliases to preserve; WHEN no such set is supplied, THEN its behavior SHALL
   be unchanged from before (every alias is renumbered).
2. WHEN a set of aliases to preserve is supplied, THEN each preserved alias SHALL
   keep its current name and SHALL NOT appear as a key in the produced rename
   map (it is not renamed).
3. WHEN building the rename map, THEN every alias that is NOT preserved SHALL be
   mapped to a new name composed of the freshly chosen prefix followed by that
   alias's zero-based position in the full, original alias ordering.
4. The system SHALL number aliases by their position in the complete alias
   ordering: a preserved alias still consumes its position number, so preserving
   an alias removes only its own entry from the rename map and SHALL NOT
   renumber the aliases that follow it.
5. WHEN renumbering, THEN each non-preserved alias SHALL appear exactly once in
   the rename map, in the original alias order, mapped to its positional fresh
   name — with no alias invented, dropped, reordered, or given a different
   number.

## Requirement 5: Preserve existing query-combining and aliasing behavior

**User story:** As a Django user, I want all previously working query
combinations to keep working, so that the alias-collision fix does not regress
existing behavior.

**Acceptance criteria**
1. The system SHALL keep OR- and AND-combination of querysets over the same base
   model working as before for cases that did not previously collide, including
   the reuse of joins on OR and the recreation of many-to-many joins on AND.
2. The system SHALL continue to reject combining incompatible querysets with the
   existing `TypeError`s: different base models, a sliced query, mixing a
   distinct with a non-distinct query, and differing distinct fields.
3. The system SHALL preserve the ability to nest a combined queryset inside a
   further filter (for example, filtering by the primary keys drawn from a
   combined queryset's values) and return the correct rows.
4. The system SHALL continue to apply the alias rename map correctly in
   `Query.change_aliases` for every valid (disjoint) rename map: updating
   references in select columns, group-by, annotations, and the where clause,
   and renaming the entries in the internal alias/table bookkeeping.
5. WHEN a rename map whose keys and values intersect is passed to
   `Query.change_aliases`, THEN it SHALL still raise `AssertionError`, so the
   double-rename safety check remains in force.
