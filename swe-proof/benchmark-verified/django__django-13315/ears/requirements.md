# Requirements: De-duplicate limited choices in model form fields

## Introduction

When Django builds a form field for a model relation (a `ForeignKey`,
`OneToOneField`, or `ManyToManyField`), the related model field may carry a
`limit_choices_to` constraint that restricts which related objects are offered
as choices. `django/forms/models.py` applies that constraint to the form
field's queryset in the helper `apply_limit_choices_to_to_formfield(formfield)`,
which reads the constraint via the field's `get_limit_choices_to()` and narrows
`formfield.queryset` accordingly.

`limit_choices_to` may be given either as a dictionary of lookups or as a
`django.db.models.Q` object (and it may be a callable that returns one of
those). When the constraint reaches across a multi-valued relation (a join that
can match a single candidate through several related rows), applying it as a
plain filter causes the candidate to be returned once per matching related row.
The form field's choice list then shows the same object multiple times, and
selecting one of the duplicates can later raise a "multiple objects returned"
error.

The goal is to make `apply_limit_choices_to_to_formfield` narrow the queryset to
exactly the related objects that satisfy the constraint, offering each such
object **at most once** regardless of how many related rows satisfy it, for both
dictionary- and `Q`-object-shaped constraints, while leaving every other aspect
of choice-limiting behavior unchanged. The affected module is
`django/forms/models.py`; the behavior is observed through the querysets of the
form fields produced for a model form.

## Requirement 1: Limited choices contain no duplicates across joins

**User story:** As a developer whose model relation uses a `limit_choices_to`
constraint that spans a multi-valued relation, I want each qualifying related
object to appear only once in the form field, so that the choice list is
correct and selecting an option cannot fail.

**Acceptance criteria**

1. WHEN a form field's `limit_choices_to` constraint traverses a multi-valued
   relation such that a candidate object matches through more than one related
   row, THEN the system SHALL include that candidate in the field's queryset
   exactly once.
2. WHEN `apply_limit_choices_to_to_formfield` narrows a form field's queryset,
   THEN the resulting queryset SHALL contain a candidate object if and only if
   at least one related row satisfies the constraint for that object, and its
   presence SHALL NOT depend on the number of matching related rows.
3. The system SHALL produce, for a constrained field, a set of offered objects
   equal to the set of candidate objects that satisfy the constraint, with no
   object repeated.

## Requirement 2: Both dictionary and Q-object constraints are supported

**User story:** As a developer, I want `limit_choices_to` to work whether I
express it as a dictionary of lookups or as a `Q` object, so that either form
narrows the choices to the same correct, duplicate-free set.

**Acceptance criteria**

1. WHEN `limit_choices_to` is supplied as a `django.db.models.Q` object, THEN
   the system SHALL narrow the field's queryset to the objects satisfying that
   `Q` constraint, each appearing at most once.
2. WHEN `limit_choices_to` is supplied as a dictionary of field lookups, THEN
   the system SHALL narrow the field's queryset to the objects satisfying those
   lookups, each appearing at most once.
3. WHEN the same duplicate-inducing constraint is expressed once as a dictionary
   and once as an equivalent `Q` object, THEN the system SHALL offer the same
   set of objects for both forms.
4. The system SHALL apply this behavior uniformly to relational form fields
   whether they derive from a single-valued relation (foreign key / one-to-one)
   or from a many-to-many relation.

## Requirement 3: Absent or empty constraints leave the queryset unchanged

**User story:** As a developer, I want a field with no meaningful
`limit_choices_to` constraint to offer its full set of related objects, so that
choice-limiting only takes effect when a constraint is actually present.

**Acceptance criteria**

1. IF a form field exposes no queryset or no `limit_choices_to` accessor, THEN
   the system SHALL leave the field's queryset unchanged.
2. IF the resolved `limit_choices_to` is absent or empty (no constraint to
   apply), THEN the system SHALL leave the field's queryset unchanged.
3. WHEN a field has a queryset but no `limit_choices_to` constraint, THEN the
   system SHALL keep offering that field's complete queryset.

## Requirement 4: Regression protection for existing choice-limiting behavior

**User story:** As a maintainer, I want the established `limit_choices_to`
behaviors to keep working, so that the duplicate fix introduces no regressions.

**Acceptance criteria**

1. WHEN `limit_choices_to` is a callable, THEN the system SHALL invoke it to
   obtain the constraint each time the form field is built, and SHALL do so once
   per field construction.
2. WHEN `limit_choices_to` is a callable that resolves to a constraint for a
   foreign-key-related field or for a many-to-many-related field, THEN the
   system SHALL narrow that field's queryset to the objects satisfying the
   resolved constraint.
3. The system SHALL continue to apply `limit_choices_to` when building the form
   fields for a model, so that a constrained field offers only the objects
   permitted by its constraint.
4. The system SHALL preserve the ordering and object identity semantics of the
   field's queryset other than the removal of duplicate entries, so that a
   constrained, non-joining query returns the same objects it did before.
