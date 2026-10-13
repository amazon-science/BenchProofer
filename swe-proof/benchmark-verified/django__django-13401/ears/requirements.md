# Requirements: Distinguish model field descriptors by their attached model

## Introduction

In Django's ORM, every model field is represented by a descriptor object (the
`Field` class and its subclasses in `django/db/models/fields/__init__.py`). Each
descriptor carries a process-wide creation-order counter (`creation_counter`)
assigned when it is instantiated, and — once the field is contributed to a model
— a reference to the model it is attached to (`self.model`). A model exposes its
identity through its options object as an application label
(`model._meta.app_label`) and a model name (`model._meta.model_name`).

Fields define equality, ordering, and hashing (`__eq__`, `__lt__`, `__hash__`;
`Field` uses `functools.total_ordering`) so they can be sorted, de-duplicated,
and placed in sets/dicts. Historically these three operations considered **only**
`creation_counter`. This is wrong when a field is declared on an abstract base
model and inherited by several concrete models: the inheriting models each get a
distinct descriptor, but all copies share the base field's `creation_counter`, so
they compare equal, hash equal, and collapse into one another inside a set. A user
who collects the same inherited field from two different concrete models into a
set unexpectedly gets a single element instead of two.

The goal is to make a field descriptor's identity, ordering, and hash also account
for the model it is attached to, so that descriptors inherited by different models
are treated as distinct, while descriptors that were never affected by this
collision keep their historical relative order. All behavior described below lives
on the base `Field` class in `django/db/models/fields/__init__.py` and applies to
its subclasses through inheritance.

## Requirement 1: Field equality accounts for the attached model

**User story:** As a developer who collects inherited fields from several concrete
models into a set or compares them directly, I want two descriptors to be equal
only when they represent the same field on the same model, so that fields
inherited from an abstract base by different models are not treated as identical.

**Acceptance criteria**

1. WHEN two `Field` descriptors are compared for equality, THEN the comparison
   SHALL evaluate to true only if they have the same `creation_counter` **and**
   the same attached model.
2. WHEN two `Field` descriptors share the same `creation_counter` but are attached
   to different models, THEN the equality comparison SHALL evaluate to false.
3. WHEN two `Field` descriptors share the same `creation_counter` and are attached
   to the same model, THEN the equality comparison SHALL evaluate to true.
4. IF neither descriptor being compared is attached to any model, THEN their
   attached models SHALL be treated as equal, so that two unattached descriptors
   with the same `creation_counter` still compare equal.
5. WHEN a `Field` descriptor is compared for equality with an object that is not a
   `Field` instance, THEN the comparison SHALL return `NotImplemented` (so Python
   falls back to the other operand / identity comparison), preserving the existing
   behavior for non-field operands.
6. The system SHALL read the attached model in a way that tolerates a descriptor
   that has not been attached to any model (i.e. accessing the model attribute
   must not raise when it is absent), treating an unattached descriptor as having
   no model.

## Requirement 2: Field hashing is consistent with the new equality

**User story:** As a developer who places inherited fields into sets or uses them
as dictionary keys, I want descriptors that compare unequal to be able to occupy
distinct slots, so that de-duplication no longer silently drops a field inherited
by a different model.

**Acceptance criteria**

1. The hash of a `Field` descriptor SHALL be derived from its `creation_counter`
   together with the identity of its attached model, expressed as the model's
   application label and model name.
2. IF a `Field` descriptor is not attached to any model, THEN its hash SHALL be
   computed with the model application label and model name treated as absent,
   and computing the hash SHALL NOT raise.
3. WHEN two `Field` descriptors compare equal under Requirement 1, THEN they SHALL
   produce the same hash value.
4. WHEN two descriptors share a `creation_counter` but are attached to models with
   different (application label, model name) identities, THEN their hash values
   SHALL be permitted to differ so that both can coexist in a single set.

## Requirement 3: Field ordering stays creation-order first, then by model

**User story:** As a maintainer relying on fields being sortable in a stable,
backward-compatible order, I want ordering to still be governed primarily by
creation order and only use the model as a tie-breaker, so that fields unaffected
by the equality change are not re-ordered.

**Acceptance criteria**

1. WHEN two `Field` descriptors with **different** `creation_counter` values are
   ordered, THEN the descriptor with the smaller `creation_counter` SHALL be
   ordered first, regardless of their attached models.
2. WHEN two `Field` descriptors that are **both** unattached to any model are
   ordered, THEN they SHALL be ordered solely by their `creation_counter`.
3. WHEN two `Field` descriptors share the same `creation_counter` and exactly one
   of them is attached to a model, THEN the descriptor that is **not** attached to
   any model SHALL be ordered first.
4. WHEN two `Field` descriptors share the same `creation_counter` and both are
   attached to models, THEN they SHALL be ordered lexicographically by the pair
   (attached model's application label, attached model's model name).
5. WHEN a `Field` descriptor is compared for ordering with an object that is not a
   `Field` instance, THEN the comparison SHALL return `NotImplemented`.
6. The system SHALL keep the ordering consistent with equality: any two
   descriptors that compare equal under Requirement 1 SHALL be ordered as neither
   strictly before nor strictly after each other.

## Requirement 4: Preserve existing field behavior for unaffected cases

**User story:** As a Django user with existing code that sorts, compares, and
de-duplicates fields, I want all previously working behavior to keep working, so
that only the abstract-inheritance collision is fixed and nothing else regresses.

**Acceptance criteria**

1. The system SHALL continue to assign each newly instantiated `Field` a distinct,
   monotonically increasing `creation_counter`, so that independently declared
   fields remain orderable and distinguishable as before.
2. WHEN a collection of fields declared with distinct `creation_counter` values is
   sorted, THEN the resulting order SHALL be identical to ordering by
   `creation_counter` alone.
3. The system SHALL keep field equality, ordering, and hashing usable together
   (as a total ordering with a consistent hash), so that fields remain valid
   members of sets and dictionaries and valid inputs to sorting and bisection.
4. WHEN the same field descriptor object is compared with itself, THEN it SHALL
   compare equal to itself and hash to the same value on repeated calls.
