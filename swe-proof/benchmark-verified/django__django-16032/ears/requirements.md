## Introduction

Django's ORM lets a `QuerySet` be used as the right-hand side (RHS) of a
relational lookup such as `field__in=<queryset>` or `field=<queryset>`
(handled by `django.db.models.fields.related_lookups.RelatedIn` and by the
generic `In`/`Exact` lookups in `django.db.models.lookups`). When such a
subquery has not had an explicit column selection applied, the ORM must
reduce it to the single column the outer lookup needs, so the generated SQL
subquery returns exactly one column.

The affected decision is driven by `django.db.models.sql.query.Query`'s
`has_select_fields` state. Previously this state was derived from whether the
query had any `select`, `annotation_select_mask`, or `extra_select_mask`
present. As a result, adding annotations via `annotate()` or aliases via
`alias()` — neither of which chooses which columns the query returns — made
the query *appear* to already have an explicit column selection. When such a
queryset was used on the RHS of an `__in` (or related-`__in`) lookup, the ORM
skipped narrowing the subquery to a single column, so the subquery emitted all
of the model's columns and the database rejected it (e.g. "sub-select returns N
columns - expected 1").

The goal: a queryset should be considered to have an explicit selected-column
set only when a values/values-list style selection (`set_values`) has actually
been performed — never merely because it carries annotations or aliases — and
the relational-`in` path must reduce an unselected RHS queryset to the single
lookup column using that selection. Existing behavior of explicit
`values()`/`values_list()` subqueries, `__exact` subqueries, cross-model
validation, and annotation/alias semantics must be preserved.

## Requirement 1: A queryset counts as having explicit select fields only after a values-style selection

**User story:** As a Django developer, I want annotations and aliases to not
be mistaken for a chosen column set, so that the ORM can still narrow my
queryset when it is used as a subquery.

**Acceptance criteria**

1. The system SHALL treat a freshly built `Query` as having no explicit
   selected-column set by default.
2. WHEN a values/values-list style column selection is applied to a `Query`
   (i.e. its `set_values` operation runs), THEN the `Query` SHALL from that
   point report that it has an explicit selected-column set.
3. IF a `Query` has only annotations added (via `annotate()`), aliases added
   (via `alias()`), or `extra()` selections, and no values/values-list
   selection has been applied, THEN the `Query` SHALL report that it has NO
   explicit selected-column set.
4. The system SHALL expose this selected-column state as an attribute readable
   from an arbitrary `Query` instance (defaulting to the "no explicit
   selection" state) so that lookup code can consult it safely.

## Requirement 2: `__in` against a related field narrows an unselected RHS queryset to one column

**User story:** As a Django developer, I want `related_field__in=queryset` to
work when the queryset has annotations and aliases, so that I don't hit a
"subquery returns too many columns" database error.

**Acceptance criteria**

1. WHEN a relational `__in` lookup is prepared with an RHS queryset that has no
   explicit selected-column set and whose lookup target field is not itself the
   primary key, THEN the system SHALL reduce that RHS queryset to select exactly
   one column: the appropriate related target field.
2. WHEN the outer lookup's field is a primary key whose model matches the RHS
   queryset's model (e.g. a `OneToOneField` acting as the primary key), THEN the
   single selected column SHALL be that field's own name; otherwise it SHALL be
   the related target field's name.
3. WHEN an RHS queryset carrying annotations and/or aliases (added after
   `annotate()`/`alias()`) but no explicit values selection is used in a
   relational `__in` filter (e.g. `Publisher.objects.filter(book__in=qs)`
   where `qs` was annotated and aliased), THEN the resulting subquery SHALL
   return a single column and the query SHALL execute successfully and return
   the correct related rows rather than raising a database column-count error.
4. WHEN reducing such an RHS queryset to its single lookup column, THEN the
   system SHALL discard any previously present annotation/alias/model column
   selection so that no extra columns remain in the subquery's SELECT clause.

## Requirement 3: Direct `pk__in` against an annotated/aliased queryset returns one column

**User story:** As a Django developer, I want `pk__in=queryset` to work when
the queryset has annotations and aliases, so that primary-key subquery filters
behave the same as before annotations/aliases were introduced.

**Acceptance criteria**

1. WHEN a generic `__in` lookup is prepared with an RHS queryset that has no
   explicit selected-column set, THEN the system SHALL reduce that queryset to
   select only the primary-key column.
2. WHEN a queryset that has had both annotations and aliases applied, but no
   explicit values selection, is used as the RHS of a `pk__in=` filter, THEN
   the outer query SHALL execute successfully and return exactly the rows whose
   primary keys are produced by the subquery.
3. The system SHALL continue to clear any pre-existing selected columns on the
   RHS queryset before selecting the primary key, so the subquery returns a
   single column.

## Requirement 4: Preserve existing subquery, values, exact-lookup, and validation behavior

**User story:** As a Django developer, I want all previously working subquery
and annotation behaviors to keep working, so that this change fixes the bug
without regressing anything.

**Acceptance criteria**

1. WHEN an RHS queryset has already had an explicit values/values-list
   selection applied (e.g. `.values("id")` or `.values_list("pk")`), THEN the
   system SHALL leave that explicit selection intact and SHALL NOT override it
   with an automatic single-column reduction.
2. WHEN an `__exact` lookup is prepared with a length-one RHS queryset that has
   no explicit selected-column set, THEN the system SHALL narrow that subquery
   to the primary-key column as before.
3. The system SHALL continue to reject a cross-model queryset passed to a
   relation lookup when the queryset has no explicit selected fields and its
   model is incompatible with the relation, raising the same validation error
   as before.
4. The system SHALL keep annotations available as computed output values when a
   queryset is evaluated normally (annotations selected via `annotate()` remain
   part of the returned results), and SHALL keep aliases usable in filtering
   and ordering without being returned as output columns.
5. WHEN a values/values-list selection names annotations, aliases, or extra
   selections, THEN the system SHALL restrict the returned columns to exactly
   the named fields (including any named annotations/extras), preserving the
   previously supported values-selection semantics.
6. The system SHALL continue to return correct results for outer querysets that
   apply `.values(...)` on top of a relational `__in` filter (e.g.
   `Publisher.objects.filter(book__in=qs).values("name")`), yielding the
   expected set of rows.
