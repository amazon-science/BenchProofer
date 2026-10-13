# Requirements: Hashable identity for many-to-many reverse relations with list `through_fields`

## Introduction

Django's related-field "rel" objects (in `django/db/models/fields/reverse_related.py`)
expose an `identity` property — a tuple of the values that define the relation — and
derive both equality (`__eq__`) and hashing (`__hash__`) from it. For hashing to work,
every element of the `identity` tuple must itself be hashable, so the base
`ForeignObjectRel.identity` normalizes potentially unhashable members (such as the
`limit_choices_to` mapping) through the `make_hashable` helper in
`django.utils.hashable`.

`ManyToManyRel` (the rel object for `ManyToManyField`) extends `identity` with three
additional members: `through`, `through_fields`, and `db_constraint`. The
`through_fields` value comes straight from the field definition and may legitimately be
a **list** (e.g. `through_fields=['child', 'parent']`). A list is not hashable, so
whenever code hashes a `ManyToManyRel` whose `through_fields` is a list, `hash()` raises
`TypeError: unhashable type: 'list'`.

This surfaces during Django's system checks — model validation calls that build a set of
fields (for field-name clash detection) hash every field/rel, which raises for a model
involved in such a relation (notably observed while checking proxy and inherited models,
which run additional field-clash checks). The goal is to make a `ManyToManyRel`'s
`identity` always hashable, regardless of whether `through_fields` was supplied as a
list, a tuple, or omitted — without changing which relations compare equal and without
changing the publicly readable `through_fields` value.

The affected module/function is `ManyToManyRel.identity` in
`django/db/models/fields/reverse_related.py`.

## Requirement 1: `ManyToManyRel` identity is always hashable

**User story:** As a Django developer defining a `ManyToManyField` with an explicit
intermediary (`through`) model and `through_fields` given as a list, I want the reverse
relation object to be hashable, so that model system checks and any set/dict membership
operations over fields do not crash.

**Acceptance criteria**

1. WHEN `hash()` is called on a `ManyToManyRel` whose `through_fields` is a list of
   field names, THEN the call SHALL return an integer hash and SHALL NOT raise
   `TypeError`.
2. WHEN a `ManyToManyRel`'s `identity` is evaluated, THEN the field-name-sequence
   component derived from `through_fields` SHALL be a hashable value regardless of
   whether `through_fields` was supplied as a list, a tuple, or left unspecified.
3. The `identity` of a `ManyToManyRel` SHALL be a hashable tuple in which every element
   is itself hashable.
4. WHEN `through_fields` is unspecified (its absent/`None` form), THEN evaluating
   `identity` and hashing the relation SHALL succeed without raising.
5. The system SHALL normalize the `through_fields` component of the identity using the
   same hashability-normalization mechanism already applied to other identity members
   (the `make_hashable` helper in `django.utils.hashable`), rather than embedding the
   raw sequence.

## Requirement 2: Equality and hashing semantics are consistent and value-based

**User story:** As a maintainer of Django's relation machinery, I want two equivalent
many-to-many reverse relations to compare equal and share a hash, so that they behave
correctly as members of sets and keys of dicts.

**Acceptance criteria**

1. WHEN two `ManyToManyRel` objects have identical relation-defining values — including
   through model, database-constraint flag, and a field-name sequence with the same
   names in the same order — THEN they SHALL compare equal via `==`.
2. WHEN two `ManyToManyRel` objects compare equal, THEN their hash values SHALL be
   equal.
3. WHEN two `ManyToManyRel` objects specify field-name sequences that differ in names or
   order, THEN they SHALL NOT compare equal.
4. The system SHALL derive both equality and the hash of a `ManyToManyRel` from its
   `identity`, keeping equal identities hash-equal.
5. WHEN a many-to-many reverse relation is accessed both from the model that directly
   declares it and from a child model that inherits it, THEN the two reverse-relation
   objects SHALL have equal hashes.

## Requirement 3: Publicly readable `through_fields` is preserved

**User story:** As a developer inspecting a reverse many-to-many relation, I want the
`through_fields` attribute to keep the exact value I declared, so that introspection and
downstream relation logic are unchanged.

**Acceptance criteria**

1. The `through_fields` attribute readable on a `ManyToManyRel` SHALL remain equal to
   the sequence originally supplied to the field (e.g. a list `['child', 'parent']`
   stays the list `['child', 'parent']` — same element type and contents, not coerced
   to a tuple).
2. WHEN a reverse many-to-many relation is accessed from a model that inherits it, THEN
   its readable `through_fields` value SHALL equal that of the relation on the declaring
   model.
3. The hashability normalization SHALL affect only the value placed inside the
   `identity` tuple and SHALL NOT mutate or replace the stored `through_fields`
   attribute.

## Requirement 4: Model system checks and existing many-to-many behavior are preserved

**User story:** As a Django user running system checks and using intermediary
many-to-many relations, I want existing validation and query behavior to keep working,
so that this fix causes no regressions.

**Acceptance criteria**

1. WHEN model system checks run over models that include a `ManyToManyField` with a
   `through` model and list-valued `through_fields`, THEN the checks SHALL complete
   without raising an unhandled exception from hashing a relation.
2. WHEN the field-name-clash check runs for a model whose inherited field name collides
   with a parent field (in a configuration that also involves a list-valued
   `through_fields` many-to-many relation elsewhere), THEN the check SHALL still report
   that clash as a model error and SHALL NOT be short-circuited by a hashing failure.
3. The system SHALL keep detecting existing many-to-many misconfigurations that were
   reported before this change — including intermediary-table name clashes, ambiguous or
   invalid `through_fields`, and duplicate `through` relationships — producing the same
   validation errors.
4. The system SHALL keep the runtime behavior of intermediary ("through") many-to-many
   relations unchanged — including forward and reverse retrieval, add/create/remove/set/
   clear operations where permitted, filtering and querying across the intermediary
   model, and self-referential and symmetrical through relations.
5. The system SHALL keep the behavior of `ManyToManyField` definitions that pass `to`,
   `through`, and `through_fields` (in either list or tuple form) working, including the
   `related_name` reverse accessor they create.
