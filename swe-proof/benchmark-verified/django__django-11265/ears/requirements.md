# Requirements: exclude() over an annotated FilteredRelation

## Introduction

Django's ORM lets a queryset annotate a named, condition-carrying join with
`FilteredRelation` (e.g. `annotate(book_alice=FilteredRelation('book',
condition=Q(...)))`) and then reference that alias in `filter(...)`. When the
same alias is referenced in an `exclude(...)` (or an equivalent negated
`filter(~Q(...))`) across a to-many relation, the ORM rewrites the clause into a
negated membership subquery — `WHERE NOT (pk IN (SELECT ...))` — by building a
fresh inner `Query` against the same model and applying the filter to it.

Two defects in this rewrite cause `exclude()` on an annotated `FilteredRelation`
to fail:

1. The fresh inner query is created without the originating query's named
   filtered-relation definitions, so resolving a filter clause that references
   the alias raises `django.core.exceptions.FieldError` ("Cannot resolve keyword
   ... into field").
2. When the inner query's leading join is collapsed away as an optimization, a
   join that exists solely to apply a filtered relation's condition can be
   trimmed, silently dropping that condition and producing wrong results.

All affected logic lives in `django/db/models/sql/query.py`, in
`Query.split_exclude` (the inner-query construction) and `Query.trim_start` (the
leading-join collapse decision). The goal is that excluding on an annotated
`FilteredRelation` resolves and returns correct rows, while every existing
`FilteredRelation` behavior continues to work unchanged.

## Requirement 1: Carry named filtered-relation definitions into the exclude subquery

**User story:** As a developer using the ORM, I want to call `exclude()` (or
`filter(~Q(...))`) referencing an alias I annotated with `FilteredRelation`, so
that the query resolves the alias instead of raising a field-resolution error.

**Acceptance criteria**

1. WHEN `Query.split_exclude` builds the fresh inner query used for the negated
   membership subquery, THEN the ORM SHALL install the originating query's named
   filtered-relation definitions onto that inner query before the exclude filter
   clause is applied to it.
2. The system SHALL make the inner query's set of named filtered-relation
   definitions equal to the originating query's set of such definitions — neither
   an empty set nor a subset.
3. WHEN a filter clause referencing a `FilteredRelation` alias is applied to the
   inner query, THEN the ORM SHALL resolve that alias against the carried-over
   definitions rather than raising `FieldError`.
4. IF a user issues `exclude(<filtered_relation_alias>__isnull=False)` (or the
   equivalent `filter(~Q(...))`) on a queryset that annotated
   `<filtered_relation_alias>` with a `FilteredRelation` over a to-many relation,
   THEN the query SHALL execute without raising an exception and SHALL return the
   set of rows that do not satisfy the filtered relation's condition.
5. The ORM SHALL apply the exclude filter clause to the inner query only after
   the named relation definitions are present, and SHALL drop any ordering on the
   inner query, so the resulting subquery is well-formed.

## Requirement 2: Do not collapse a leading join that carries a filtered relation's condition

**User story:** As a developer, I want the exclude subquery to preserve every
filtering condition, so that excluding on a `FilteredRelation` returns the
correct rows and not a superset.

**Acceptance criteria**

1. WHEN `Query.trim_start` decides whether the inner query's leading join can be
   collapsed into a plain column selection, THEN the ORM SHALL treat the join as
   non-collapsible if that join exists to apply a named filtered relation's
   condition.
2. The system SHALL continue to treat a left-outer leading join as
   non-collapsible, because collapsing it would drop rows that have nothing on the
   inner side.
3. IF the leading join is neither a left-outer join nor a join carrying a
   filtered relation's condition, THEN the ORM SHALL collapse it, selecting the
   related fields' near-side names against the collapsed-onto alias.
4. IF the leading join is a left-outer join OR carries a filtered relation's
   condition, THEN the ORM SHALL NOT collapse it, and SHALL instead select the
   related fields' far-side names against the join's original source alias.
5. WHEN an exclude over an annotated `FilteredRelation` is executed, THEN the
   emitted subquery SHALL retain the filtered relation's condition so that the
   returned result set reflects that condition.

## Requirement 3: Preserve existing FilteredRelation and query behavior

**User story:** As a maintainer, I want all previously working
`FilteredRelation` and query features to keep working, so that this fix
introduces no regressions.

**Acceptance criteria**

1. The system SHALL keep `filter(...)` on an annotated `FilteredRelation`
   (including `__isnull` and join-crossing conditions) returning the same rows as
   before.
2. The system SHALL leave every previously working use of `FilteredRelation`
   — however the annotated alias is combined with other queryset operations and
   clauses — behaving exactly as it did before this change, so that this fix
   changes only the exclude/negated-filter path and introduces no other
   observable difference.
3. The system SHALL keep raising the existing validation errors for misuse of a
   `FilteredRelation` (for example, an invalid or empty relation name) with the
   same error type and behavior as before this change.
4. WHEN `exclude(...)` crosses a to-many relation that does NOT involve a
   `FilteredRelation`, THEN the ORM SHALL continue to build the negated subquery
   and return the same rows as before this change.
