# Requirements: UUIDField value preparation for generic-foreign-key prefetch

## Introduction

Django's `UUIDField` (`django/db/models/fields/__init__.py`) stores a universally
unique identifier as its primary key. When another model refers to such a record
through a `GenericForeignKey` (`django/contrib/contenttypes/fields.py`), the
referring row keeps the target's primary key in a **text** column, so the stored
value is the *string spelling* of the UUID, while the target object's own primary
key attribute is a `uuid.UUID` object.

Generic-foreign-key prefetching joins referring rows to their targets in Python.
It builds a lookup key for each referring row by calling the target primary-key
field's value-preparation hook on the stored foreign value, and compares that key
against the target object's primary key. For a `UUIDField` primary key the two
sides are unequal — a plain string on one side, a `uuid.UUID` on the other — so
the join matches nothing and `prefetch_related(<gfk>)` leaves the accessor
resolving to `None` instead of the related object.

The affected behavior is `UUIDField`'s preliminary (non-database) value
preparation. Today `UUIDField` inherits the base field's preparation, which for an
ordinary value is an identity pass-through and therefore leaves a string spelling
as a string. The goal is to make `UUIDField` canonicalize prepared values to the
`uuid.UUID` they denote, so that a string spelling and the equivalent `uuid.UUID`
prepare to equal keys and the prefetch join succeeds — while preserving all
existing conversion, storage, and lookup behavior of `UUIDField`.

## Requirement 1: UUIDField prepares values to a canonical identifier

**User story:** As a developer using a `UUIDField` primary key, I want the field's
preliminary value preparation to return the identifier the input denotes, so that
values originating as text and values already parsed compare equal after
preparation.

**Acceptance criteria**

1. WHEN `UUIDField`'s preliminary (non-database-specific) value-preparation hook is
   called with a string spelling of a UUID (for example the hyphenated 36-character
   form, the 32-hex-digit form, a `urn:uuid:` form, or a brace-wrapped form), THEN
   the field SHALL return the `uuid.UUID` object that spelling denotes.
2. WHEN that preparation hook is called with a value that is already a `uuid.UUID`
   object, THEN the field SHALL return an equal `uuid.UUID` (the same identifier,
   unchanged).
3. WHEN that preparation hook is called with an integer, THEN the field SHALL return
   the `uuid.UUID` whose integer value equals that integer.
4. WHEN that preparation hook is called with `None`, THEN the field SHALL return
   `None`.
5. The system SHALL ensure that a UUID string spelling and the `uuid.UUID` object
   denoting the same identifier produce equal results from this preparation hook.
6. IF the supplied value is neither `None`, an integer, a `uuid.UUID`, nor a valid
   UUID spelling, THEN the field SHALL raise the same validation error it raises
   today when asked to interpret an invalid UUID value.
7. The preparation hook SHALL first apply the base field's preliminary preparation
   (which unwraps a lazy/deferred value) before producing the canonical identifier,
   so that lazily wrapped inputs are handled as before.

## Requirement 2: Generic-foreign-key prefetch resolves UUID-primary-key targets

**User story:** As a developer who links to a model whose primary key is a
`UUIDField` via a `GenericForeignKey`, I want `prefetch_related` on that generic
relation to load the related objects, so that the accessor returns the target
instead of `None`.

**Acceptance criteria**

1. WHEN a queryset of objects carrying a `GenericForeignKey` whose targets have a
   `UUIDField` primary key is evaluated with the generic relation prefetched, THEN
   each object's generic-foreign-key accessor SHALL resolve to the correct related
   target object.
2. WHEN such a prefetch is performed, THEN the generic-foreign-key accessor SHALL
   NOT resolve to `None` for a row whose stored foreign value corresponds to an
   existing target.
3. The system SHALL match a referring row to its target regardless of whether the
   foreign value is held as the string spelling of the target's UUID primary key
   while the target's primary-key attribute is a `uuid.UUID` object.
4. WHEN the related targets are prefetched, THEN the prepared lookup key derived
   from a referring row's stored foreign value SHALL compare equal to the prepared
   key derived from the matching target's primary key.

## Requirement 3: Preserve existing UUIDField and prefetch behavior

**User story:** As a maintainer, I want the change to add value canonicalization
without disturbing existing storage, conversion, or prefetch behavior, so that no
current functionality regresses.

**Acceptance criteria**

1. The system SHALL preserve `UUIDField`'s database value preparation: a value
   destined for the database SHALL still be normalized to the same stored form as
   before (a `uuid.UUID` on backends with a native UUID column, otherwise its
   32-hex-digit form), and `None` SHALL still map to `None`.
2. The system SHALL preserve `UUIDField`'s conversion of a value to a `uuid.UUID`
   (its `to_python` behavior) for all previously accepted inputs and SHALL keep
   raising the existing validation error for invalid ones.
3. The system SHALL keep `UUIDField`'s reported internal type unchanged.
4. WHEN a `GenericForeignKey`'s target model has a non-UUID primary key (for
   example an integer or a non-integer text primary key), THEN prefetching the
   generic relation SHALL continue to resolve related objects exactly as before.
5. WHEN a referring row's content-type reference is unset (no target type), THEN
   prefetching the generic relation SHALL continue to resolve that row's accessor
   to `None` without error.
6. The system SHALL keep all currently passing generic-relation and prefetch
   behaviors intact, adding only the resolution of targets whose primary key is a
   `UUIDField`.
