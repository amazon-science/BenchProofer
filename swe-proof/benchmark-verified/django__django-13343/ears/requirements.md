# Requirements: Callable `storage` on `FileField` must deconstruct to the original callable

## Introduction

Django's `FileField` (and its subclass `ImageField`) in
`django/db/models/fields/files.py` accept a `storage` argument that may be a
callable. The documented purpose of a callable `storage` is to let the storage
backend be selected at runtime, so different environments can resolve to
different storages. At construction time the field evaluates the callable once
and uses the resulting `Storage` instance for all runtime file operations.

The defect is in field deconstruction. `Field.deconstruct()` is used by the
migrations framework (e.g. during `makemigrations`) to serialize a field back
into the arguments needed to recreate it. When a `FileField` was built with a
callable `storage`, `deconstruct()` currently emits the *already-evaluated*
`Storage` instance instead of the callable. That inlines a concrete storage
into the migration and defeats the whole point of a callable storage — the
runtime-variable backend becomes frozen. A callable `upload_to` already
deconstructs back to the callable itself; callable `storage` must behave the
same way.

The goal: make `FileField`/`ImageField` remember the original `storage`
callable at construction and return that same callable from `deconstruct()`,
while leaving runtime storage resolution and all other deconstruction behavior
unchanged.

## Requirement 1: Preserve the original `storage` callable at construction

**User story:** As a Django developer using a callable `storage` on a
`FileField`, I want the field to keep a reference to the callable I passed, so
that later deconstruction can reproduce my field definition faithfully instead
of freezing a runtime-resolved storage.

**Acceptance criteria**

1. WHEN a `FileField` (or `ImageField`) is constructed with a `storage`
   argument that is callable, THEN the field SHALL retain a reference to that
   original callable object for later use by deconstruction.
2. WHEN a `FileField` is constructed with a callable `storage`, THEN the field
   SHALL still evaluate the callable exactly once at construction time and use
   the returned value as the field's runtime `storage` instance.
3. The system SHALL preserve the exact callable object passed in (identity
   preserved), not a copy, wrapper, or re-derived reference to it.
4. WHEN a `FileField` is constructed with a `storage` argument that is a
   (non-callable) `Storage` instance, THEN the field SHALL NOT record any
   callable reference and SHALL use that instance directly as its runtime
   storage.
5. WHEN no `storage` argument is provided (it is omitted or falsy), THEN the
   field SHALL use the project default storage as its runtime storage and SHALL
   NOT record any callable reference.
6. IF the callable `storage` returns a value that is not a `Storage`
   subclass/instance, THEN the field SHALL raise `TypeError` at construction
   time, exactly as before this change (this validation behavior SHALL keep).

## Requirement 2: Deconstruct a callable `storage` back to the callable

**User story:** As a developer running `makemigrations`, I want a field built
with a callable `storage` to serialize back to that callable, so that my
migrations stay environment-independent and re-importing the field yields the
same runtime-variable behavior.

**Acceptance criteria**

1. WHEN `deconstruct()` is called on a `FileField` that was constructed with a
   callable `storage`, THEN the returned keyword arguments SHALL include a
   `storage` entry whose value is the original callable object that was passed
   at construction (identity preserved), NOT the evaluated `Storage` instance.
2. WHEN `deconstruct()` is called on a `FileField` that was constructed with a
   plain (non-callable) `Storage` instance that is not the project default,
   THEN the returned keyword arguments SHALL include a `storage` entry whose
   value is that same `Storage` instance.
3. WHEN the field's runtime storage is the project default storage, THEN
   `deconstruct()` SHALL omit the `storage` keyword entirely (no `storage`
   key present in the returned kwargs).
4. The system SHALL keep the existing `upload_to` deconstruction behavior:
   `deconstruct()` SHALL always include an `upload_to` entry equal to the field's
   `upload_to` value, and when `upload_to` is a callable that value SHALL be the
   original callable (identity preserved).
5. The system SHALL keep the existing `max_length` deconstruction behavior:
   when `max_length` equals its default of 100, `deconstruct()` SHALL omit the
   `max_length` keyword; otherwise it SHALL include the field's `max_length`.
6. WHEN `deconstruct()` returns, THEN the field's own runtime `storage`
   attribute SHALL remain the evaluated `Storage` instance and SHALL be
   unaffected by the call (deconstruction is read-only with respect to field
   state).

## Requirement 3: Runtime storage behavior is unchanged

**User story:** As an application relying on file storage, I want file
operations to continue using the resolved storage backend, so that fixing the
migration serialization does not change how files are actually stored or read.

**Acceptance criteria**

1. The system SHALL continue to expose the field's runtime `storage` as a
   concrete `Storage` instance for all file operations (save, open, path, url,
   delete, listing, timestamps, permissions, etc.).
2. WHEN a callable `storage` returns the project default storage, THEN the
   field SHALL behave as though the default storage was used at runtime, and
   its file operations SHALL keep working as before.
3. The system SHALL keep all previously working `FileField`/`ImageField` and
   storage-backend behaviors that do not involve deconstruction unchanged,
   including model instances that declare fields with callable, callable-class,
   plain-instance, and default storages.
