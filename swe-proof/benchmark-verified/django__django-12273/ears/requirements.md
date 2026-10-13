# Requirements: Assigning a primary key propagates across the inheritance key chain

## Introduction

In Django's ORM, a model that participates in multi-table inheritance stores,
alongside its own primary-key attribute, a separate parent-link key attribute
for each ancestor model it descends from. Those parent-link attributes (the
`OneToOneField` "pointers" recorded in `Options.parents`, i.e.
`self._meta.parents`) are what tie a child instance to its inherited parent
rows.

The primary key of any model instance is exposed through the `pk` property on
`django.db.models.base.Model`, whose setter is `Model._set_pk_val(self, value)`
in `django/db/models/base.py`. Before this change, that setter wrote the given
value only to the instance's own primary-key attribute
(`self._meta.pk.attname`) and left every ancestor parent-link key attribute
untouched. As a result, assigning a new value to `pk` on a child instance — and
in particular clearing it with `self.pk = None` — did not reach the inherited
key attributes. A subsequent `save()` then still saw the old ancestor keys and
overwrote the existing parent row instead of creating a fresh instance.

The goal is to make an assignment through the `pk` property re-key the whole
inheritance chain in one step: the instance's own primary-key attribute **and**
every ancestor parent-link key attribute must receive the assigned value, so
that clearing the primary key clears the entire chain and re-saving creates a
new object rather than overwriting the parent. Reading `pk`, and the behavior on
models that are not part of multi-table inheritance, must be unchanged.

## Requirement 1: Assigning the primary key updates every ancestor parent-link key

**User story:** As a developer working with inherited models, I want assigning
a value to an instance's `pk` to also set each ancestor's parent-link key, so
that the instance is consistently re-keyed across its whole inheritance chain.

**Acceptance criteria**

1. WHEN a value is assigned through the `pk` property of a model instance
   (invoking `Model._set_pk_val`), THEN the setter SHALL assign that same value
   to the instance's own primary-key attribute, named by
   `self._meta.pk.attname`.
2. WHEN a value is assigned through the `pk` property of an instance of a model
   that inherits from one or more concrete ancestors, THEN the setter SHALL, for
   each ancestor parent link recorded in `self._meta.parents`, assign that same
   value to the attribute named by that parent link's `target_field.attname`.
3. The system SHALL apply the assignment to the own primary-key attribute and to
   every qualifying ancestor parent-link key attribute for a single assignment
   through `pk`, so that after the assignment the instance's own key attribute
   and all qualifying ancestor key attributes hold the assigned value.
4. WHEN the assigned value is `None`, THEN the setter SHALL set the own
   primary-key attribute and every qualifying ancestor parent-link key attribute
   to `None`, clearing the entire key chain.

## Requirement 2: Only genuine, distinct ancestor links are updated

**User story:** As a developer, I want the propagation to touch only the real
ancestor key attributes and not misfire, so that assignment behavior stays
correct and does not disturb unrelated state.

**Acceptance criteria**

1. IF a parent-link entry in `self._meta.parents` is absent (a falsy/`None`
   link), THEN the setter SHALL NOT attempt to write a key attribute for that
   entry.
2. IF a parent link is the same field as the instance's own primary key
   (equal to `self._meta.pk`), THEN the setter SHALL NOT perform a separate
   write for that link, because the own primary-key assignment already covers
   it.
3. The system SHALL leave every instance attribute that is neither the own
   primary-key attribute nor a qualifying ancestor parent-link key attribute
   unchanged by the assignment.

## Requirement 3: Clearing the primary key allows saving as a new object

**User story:** As a developer, I want to reset an inherited instance's primary
key to `None` and save it as a brand-new object, so that the existing parent
records are preserved rather than overwritten.

**Acceptance criteria**

1. WHEN a developer clears the primary key of an inherited instance by assigning
   `None` through `pk` (and correspondingly clears the exposed ancestor key
   attributes) and then calls `save()`, THEN a new record SHALL be inserted for
   each level of the inheritance chain rather than the existing parent record
   being updated.
2. WHEN such a new object is saved after clearing the primary key, THEN the
   previously existing objects at every ancestor level SHALL retain their
   original field values and remain distinct from the newly created object.
3. The system SHALL support this behavior for a chain of more than two levels of
   inheritance, updating the key attribute at each intermediate ancestor level
   as well as the topmost one.

## Requirement 4: Reading the primary key and non-inherited behavior are preserved

**User story:** As a developer relying on existing model behavior, I want
reading `pk` and using models without multi-table inheritance to work exactly as
before, so that this change introduces no regressions.

**Acceptance criteria**

1. WHEN the `pk` property is read (invoking `Model._get_pk_val`), THEN it SHALL
   return the value of the instance's own primary-key attribute
   (`self._meta.pk.attname`), unchanged by this behavior.
2. The system SHALL keep the assignment behavior for models that do not
   participate in multi-table inheritance identical: assigning through `pk`
   SHALL set the own primary-key attribute and SHALL make no additional key
   writes.
3. WHEN a model uses an explicit `OneToOneField` to its parent as its own
   primary key (so the parent link coincides with the primary key), THEN
   assigning through `pk` SHALL set that key exactly once and SHALL match the
   previously established behavior for such models.
4. The system SHALL preserve all existing multi-table-inheritance behaviors that
   do not involve assigning through `pk` — including joins, select-related
   access, parent-field filtering, and updates on parent models — without
   change.
