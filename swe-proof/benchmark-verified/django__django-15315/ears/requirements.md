# Requirements: Immutable hash for model field objects

## Introduction

In Django's ORM, a model field object (an instance of the base field type
defined in `django/db/models/fields/__init__.py`, e.g. `CharField`,
`IntegerField`) is created independently of any model. Each field instance is
assigned a per-process creation serial at construction time (`creation_counter`)
that establishes a stable, unique identity for ordering purposes. Later, when a
field is declared as an attribute of a `django.db.models.Model` subclass, Django
attaches the field to that model and the field gains a `model` attribute
exposing the owning model's `_meta.app_label` and `_meta.model_name`.

The base field type implements `__hash__`, `__eq__`, and `__lt__` (the last via
`functools.total_ordering`). A regression caused `Field.__hash__` to fold the
owning model's label/name into the hash, so a field's hash *changed* the moment
it was attached to a model class. This violates the Python data-model
invariant that an object's hash must remain constant for its lifetime: a field
placed in a `dict` or `set` before being assigned to a model could no longer be
found afterward (e.g. `f in d` raising / returning `False`, dict lookups
failing with an internal assertion).

The goal is to make the field's hash **immutable** across attachment while
keeping the existing equality and ordering semantics intact. The affected code
is the `__hash__` method of the base field class in
`django/db/models/fields/__init__.py`.

## Requirement 1: Field hash is immutable across model assignment

**User story:** As a developer, I want to use a model field instance as a
dictionary or set key before I assign it to a model, so that I can still look it
up after the field has been attached to a model class.

**Acceptance criteria**

1. WHEN a field instance is constructed but not yet assigned to any model, THEN
   the field SHALL produce a well-defined hash value via `hash(field)`.
2. WHEN a field instance is subsequently assigned as an attribute of a model
   class (and thereby attached to that model), THEN `hash(field)` SHALL return
   the same value it returned before the assignment.
3. The field's hash SHALL be derived solely from the field's construction-time
   creation serial (`creation_counter`) and SHALL NOT incorporate the owning
   model's application label, model name, or any other attribute that only
   becomes available once the field is attached to a model.
4. IF a field instance has been placed as a key in a `dict` or `set` prior to
   being assigned to a model class, THEN membership tests and key lookups for
   that same field instance SHALL continue to succeed after the field is
   assigned to a model class.
5. The system SHALL keep the field object hashable at every point in its
   lifetime, both before and after attachment to a model.

## Requirement 2: Preserve field equality semantics

**User story:** As a maintainer, I want field equality to remain unchanged, so
that existing behavior distinguishing distinct field instances still holds.

**Acceptance criteria**

1. The system SHALL treat two field instances as equal only when they share the
   same creation serial and the same owning model (both unattached, or attached
   to the same model).
2. WHEN two distinct field instances defined on different model classes are
   compared for equality, THEN they SHALL compare as not equal.
3. IF a hash value is shared between two field instances, THEN those instances
   SHALL still be resolved by an equality check, so that hash collisions never
   cause distinct fields to be treated as identical.

## Requirement 3: Preserve field ordering semantics

**User story:** As a maintainer, I want field ordering to remain unchanged, so
that fields continue to sort by creation order and by owning model as before.

**Acceptance criteria**

1. WHEN two field instances are compared with the ordering operators, THEN they
   SHALL be ordered primarily by their construction-time creation serial,
   preserving the order in which they were created.
2. WHEN two field instances share the same creation serial and differ only in
   attachment state, THEN a field not yet attached to a model SHALL order before
   a field that is attached to a model.
3. WHEN two field instances share the same creation serial and are both attached
   to models, THEN they SHALL be ordered by the owning model's application label
   and model name.
4. The system SHALL keep the ordering behavior consistent with equality so that
   the total-ordering contract between the comparison and equality operators
   continues to hold.
