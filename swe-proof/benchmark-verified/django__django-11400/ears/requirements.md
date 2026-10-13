# Requirements: Ordering of related choices in admin list filters

## Introduction

The Django admin list filters `RelatedFieldListFilter` and
`RelatedOnlyFieldListFilter` (in `django/contrib/admin/filters.py`) present the
selectable values of a related model as a list of `(value, label)` choices. Two
ordering defects exist:

1. `RelatedFieldListFilter` does not fall back to the related model's
   `Meta.ordering`. It builds the choices with an empty ordering directive
   unless the related model's `ModelAdmin` defines an ordering, and the empty
   directive causes the related model's default ordering to be discarded rather
   than preserved.
2. `RelatedOnlyFieldListFilter` never applies any ordering to the related model
   — even when the related model's `ModelAdmin` defines one — because its
   choices call omits the ordering directive entirely.

The root cause lives in the choice-building helpers
`Field.get_choices` (`django/db/models/fields/__init__.py`) and
`ForeignObjectRel.get_choices` (`django/db/models/fields/reverse_related.py`):
they unconditionally re-sort the related queryset by the supplied ordering
directive, which — when the directive is empty — clears the queryset's own
default ordering instead of leaving it intact.

The goal is to make an empty ordering directive preserve the related model's
intrinsic default ordering, and to make both list filters honor the applicable
ordering (the related `ModelAdmin`'s ordering when defined, otherwise the
related model's `Meta.ordering`).

## Requirement 1: Empty ordering directive preserves default ordering in `Field.get_choices`

**User story:** As a developer requesting related-object choices for a model
field, I want an empty ordering directive to preserve the related model's own
default ordering, so that choices are not returned in an arbitrary order when I
did not ask for a specific ordering.

**Acceptance criteria**

1. WHEN `Field.get_choices` is called with an empty ordering directive, THEN the
   related model's queryset SHALL retain its intrinsic default ordering (the
   ordering it would have with no explicit re-sequencing applied, i.e. the
   related model's `Meta.ordering`).
2. WHEN `Field.get_choices` is called with a non-empty ordering directive, THEN
   the related model's queryset SHALL be re-sequenced according to that
   directive before choices are produced.
3. The system SHALL produce exactly one `(value, label)` choice per record in
   the resulting queryset, in that resulting order, where `value` is the
   related field's key value and `label` is the record's string representation.
4. IF a leading blank choice is requested, THEN `Field.get_choices` SHALL
   prepend the blank choice ahead of the per-record choices; otherwise it SHALL
   produce only the per-record choices.
5. The system SHALL continue to apply any `limit_choices_to` restriction to the
   related queryset before producing choices.

## Requirement 2: Empty ordering directive preserves default ordering in reverse-related `get_choices`

**User story:** As a developer requesting choices across a reverse relation, I
want the same empty-directive behavior as for forward fields, so that reverse
relationships are ordered consistently.

**Acceptance criteria**

1. WHEN `ForeignObjectRel.get_choices` is called with an empty ordering
   directive, THEN the related model's queryset SHALL retain its intrinsic
   default ordering (the related model's `Meta.ordering`).
2. WHEN `ForeignObjectRel.get_choices` is called with a non-empty ordering
   directive, THEN the related model's queryset SHALL be re-sequenced according
   to that directive before choices are produced.
3. The system SHALL produce one `(primary-key, label)` choice per record in the
   resulting order, optionally prepended by a requested leading blank choice.

## Requirement 3: `RelatedFieldListFilter` falls back to the related model's ordering

**User story:** As an admin user, I want a related-field list filter to list its
choices in a sensible order, so that the filter reflects the related model's
configured ordering.

**Acceptance criteria**

1. WHEN `RelatedFieldListFilter` builds its choices and the related model's
   registered `ModelAdmin` defines an ordering, THEN the filter SHALL order the
   related choices by that `ModelAdmin` ordering.
2. WHEN `RelatedFieldListFilter` builds its choices and the related model has no
   registered `ModelAdmin` ordering, THEN the filter SHALL fall back to the
   related model's `Meta.ordering` for the choice order.
3. WHEN the related model is reached through a reverse relationship and no
   `ModelAdmin` ordering applies, THEN the filter SHALL order the related
   choices by the related model's `Meta.ordering`.
4. The system SHALL determine the applicable ordering via a single shared step
   that returns the related `ModelAdmin`'s ordering when a `ModelAdmin` is
   registered for the related model, and an empty ordering otherwise.

## Requirement 4: `RelatedOnlyFieldListFilter` honors the applicable ordering

**User story:** As an admin user, I want the "related only" list filter to order
its (already narrowed) choices, so that its behavior matches the ordinary
related-field filter.

**Acceptance criteria**

1. WHEN `RelatedOnlyFieldListFilter` builds its choices and the related model's
   registered `ModelAdmin` defines an ordering, THEN the filter SHALL order the
   narrowed related choices by that `ModelAdmin` ordering.
2. WHEN `RelatedOnlyFieldListFilter` builds its choices and no `ModelAdmin`
   ordering applies, THEN the filter SHALL order the narrowed related choices by
   the related model's `Meta.ordering`.
3. The system SHALL continue to restrict the choices to only those related
   records that are actually referenced (the existing narrowing by referenced
   primary keys), while applying the ordering to that narrowed set.

## Requirement 5: Preserve existing ordering and choice behavior (regression protection)

**User story:** As a maintainer, I want the existing choice-generation behavior
to remain intact, so that the ordering fix does not regress other functionality.

**Acceptance criteria**

1. WHEN a non-empty ordering directive is supplied to `Field.get_choices` or
   `ForeignObjectRel.get_choices`, THEN the produced choice order SHALL match
   the order dictated by that directive.
2. WHEN `RelatedFieldListFilter`'s related `ModelAdmin` defines an ordering,
   THEN that filter SHALL keep ordering its choices by the `ModelAdmin`
   ordering.
3. The system SHALL keep producing the blank/grouped/lazy choice results for
   fields that define explicit `choices` unchanged (the ordering directive only
   affects related-model querysets, not statically defined choices).
4. The system SHALL keep the existing behavior of all other admin list filters
   (value-based, boolean, choices, date, and simple filters) unchanged.
5. The system SHALL keep the string coercion of each choice's label unchanged.
