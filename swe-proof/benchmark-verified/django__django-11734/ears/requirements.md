# Requirements: Correct outer-query references inside negated subqueries

## Introduction

Django's ORM lets a queryset carry a reference to an *outer* query so it can be
embedded as a correlated subquery — for example
`Item.objects.filter(tags__category_id=OuterRef('pk'))` used inside an
`Exists()` annotation on `Number.objects`. When such a condition is expressed as
a negation over a multi-valued (to-many) relation — via `QuerySet.exclude(...)`
or `filter(~Q(...))` — the ORM does not translate it directly. Instead,
`django.db.models.sql.query.Query.split_exclude` rewrites the negated condition
into an auxiliary nested subquery (`NOT (pk IN (SELECT ... WHERE ...))`), pushing
the original condition one query boundary deeper.

Today, when that pushed-down condition's right-hand side is itself an
`OuterRef`, the reference is not preserved correctly: the extra query boundary
introduced by `split_exclude` is not accounted for, so the reference resolves
against the wrong query and the whole queryset raises
`ValueError: This queryset contains a reference to an outer query and may only
be used in a subquery` when it is finally used as a subquery. The equivalent
`filter(...)` (non-negated) form already works.

The goal is to make `exclude(...)` and `filter(~Q(...))` accept an `OuterRef`
right-hand side over a to-many relation exactly as `filter(...)` does: the
relocated reference must resolve against the intended outer query, producing a
usable correlated subquery. This affects `Query.split_exclude`
(`django/db/models/sql/query.py`) and the single-column relation lookup
preparation in `RelatedLookupMixin.get_prep_lookup`
(`django/db/models/fields/related_lookups.py`), while preserving all existing
`exclude`/`~Q`/relation-lookup behavior.

## Requirement 1: OuterRef survives negation over a to-many relation

**User story:** As a developer building a correlated subquery, I want to use an
`OuterRef` inside `exclude()` or `filter(~Q(...))` over a to-many relation, so
that I can express "rows for which no related object matches the outer row"
without the query crashing.

**Acceptance criteria**
1. WHEN a queryset applies `exclude(<relation>__<field>=OuterRef(<name>))` over a
   to-many relation and that queryset is used as a correlated subquery (for
   example inside an `Exists()` annotation that is then filtered on), THEN the
   ORM SHALL build the queryset successfully and SHALL NOT raise
   `ValueError: This queryset contains a reference to an outer query and may
   only be used in a subquery`.
2. WHEN a queryset applies `filter(~Q(<relation>__<field>=OuterRef(<name>)))`
   over a to-many relation and is used as a correlated subquery, THEN the ORM
   SHALL build the queryset successfully and SHALL NOT raise that same
   `ValueError`.
3. WHEN such an `exclude()`/`~Q()` correlated subquery is executed, THEN the
   outer-query reference in the condition SHALL resolve against the intended
   outer query (the query that supplies `OuterRef(<name>)`), producing the same
   result set as the semantically-equivalent construction the developer
   intends — i.e. selecting outer rows according to the negated existence of a
   matching related object.
4. The system SHALL produce, for the non-negated `filter(...)` form of the same
   `OuterRef` condition over a to-many relation, results consistent with the
   negated `exclude()`/`~Q()` forms (the two forms SHALL remain complementary,
   as they were before for the non-crashing case).

## Requirement 2: Re-anchoring the relocated condition preserves reference depth

**User story:** As a maintainer of the subquery-rewriting logic, I want the
right-hand side of a relocated negated condition to be re-anchored according to
how many query boundaries it must now cross, so that references neither crash nor
silently resolve against the wrong query.

**Acceptance criteria**
1. WHEN `split_exclude` relocates a condition whose right-hand side is a plain
   same-query column reference (an `F` expression), THEN the rewritten condition
   SHALL turn that column reference into an outer-query reference that reaches
   outward by exactly one query boundary (so it resolves against the query the
   condition was moved out of).
2. WHEN `split_exclude` relocates a condition whose right-hand side is already an
   outer-query reference (an `OuterRef`), THEN the rewritten condition SHALL
   extend that reference to reach outward by exactly one *additional* query
   boundary, preserving the boundaries the original reference already carried,
   rather than resetting it to a single-boundary reference.
3. WHEN `split_exclude` relocates a condition whose right-hand side is a direct
   literal value (not a resolvable expression), THEN the rewritten condition
   SHALL carry that value through unchanged.
4. WHEN `split_exclude` relocates a condition whose right-hand side is neither a
   bare outer-query reference (`OuterRef`) nor a plain same-query column
   reference (`F`) — for example a direct literal value or a compound/combined
   expression that is itself resolvable — THEN `split_exclude` SHALL carry that
   right-hand side through unchanged and SHALL NOT apply any boundary
   re-anchoring to it. The boundary-adjusting re-anchoring performed by
   `split_exclude` applies to exactly the `OuterRef` (2.2) and `F` (2.1) cases
   above; the general "leave any resolvable expression intact for later
   resolution" behavior for single-column relation lookups belongs to
   `get_prep_lookup` (Requirement 3), not to `split_exclude`.

## Requirement 3: Relation-lookup preparation must not mangle resolvable expressions

**User story:** As a developer filtering a relation against an expression, I want
value-normalization for single-column relations to apply only to concrete
values, so that an `OuterRef`/`F` passed through a relation lookup is left intact
for later resolution.

**Acceptance criteria**
1. WHEN a single-column relation lookup is prepared and its right-hand side is a
   resolvable expression (it exposes `resolve_expression`, e.g. an `OuterRef` or
   an `F`), THEN `RelatedLookupMixin.get_prep_lookup` SHALL skip direct-value
   normalization and SHALL leave the expression unchanged for later resolution.
2. WHEN a single-column relation lookup is prepared and its right-hand side is a
   direct, concrete value (not a resolvable expression), THEN
   `get_prep_lookup` SHALL continue to normalize and validate that value against
   the related field's target field exactly as before, including running the
   target field's value preparation.
3. IF a concrete value supplied to a relation lookup is invalid for the related
   field's target field (for example a non-integer for an integer primary key),
   THEN the ORM SHALL still raise the same validation error it raised before this
   change.

## Requirement 4: Preserve all existing exclude / negation / relation-lookup behavior

**User story:** As an existing Django user, I want every previously-working
`exclude()`, `~Q()`, subquery, and relation-lookup behavior to keep working
unchanged, so that this fix introduces no regressions.

**Acceptance criteria**
1. The system SHALL keep the existing behavior of `exclude(...)` and
   `filter(~Q(...))` over to-many relations for conditions whose right-hand side
   is a concrete value, including double exclusions and nested exclusions,
   producing the same result sets as before.
2. The system SHALL keep the existing behavior of `exclude()` / `~Q()` across
   circular, reverse, and to-field foreign-key relations, and of many-to-many
   exclusions, unchanged.
3. The system SHALL keep working correlated-subquery behavior — including
   `Exists()` annotations and `filter(...)` conditions that reference an
   `OuterRef` over a to-many relation — producing the same results as before.
4. The system SHALL keep the existing relation-lookup type checks and value
   coercion for direct values (correct lookups succeed; wrong-type and
   wrong-model right-hand sides raise the same errors as before).
5. WHEN a queryset that has already been evaluated is used as a subquery argument
   or as a related-lookup right-hand side, THEN the ORM SHALL continue to accept
   it as it did before this change.
