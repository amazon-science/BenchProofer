# Requirements — FileField storage deconstruction

## Introduction

`django.db.models.fields.files.FileField` accepts a `storage` argument that may
be either a storage instance or a **callable** that returns a storage instance.
When a callable is supplied, `FileField.__init__` evaluates it once, stores the
resulting instance on `self.storage`, and keeps a reference to the original
(un-evaluated) callable on `self._storage_callable`.

`FileField.deconstruct()` produces the reconstructable form of the field (used
by `makemigrations` / migration serialization). It must decide **which storage
reference, if any, to record** under the `storage` keyword so the field can be
faithfully rebuilt.

The defect: `deconstruct()` decided whether to include the `storage` kwarg by
comparing the *evaluated* storage instance (`self.storage`) against
`django.core.files.storage.default_storage`. When a caller supplies a callable
that happens to *return* `default_storage`, the evaluated instance equals the
default, so the kwarg was wrongly omitted — even though the field was in fact
configured with a non-default *reference* (the callable). This produced
unstable migrations that alternately included or omitted the storage argument.

The goal: base the include/omit decision (and the recorded value) on the
**original storage reference** — the callable when one was supplied, otherwise
the evaluated instance — so a callable is preserved whenever it was configured,
regardless of what it evaluates to.

## Requirement 1: Preserve a callable storage reference that evaluates to the default

**User story:** As a developer who configures a `FileField` with a callable
storage that may return the default storage, I want the callable to be recorded
when the field is deconstructed, so that my migrations are deterministic and
reconstruct the field with its original callable.

**Acceptance criteria**

1. WHEN a `FileField` was configured with a storage callable and
   `FileField.deconstruct()` is invoked, THEN `deconstruct` SHALL base the
   include/omit decision for the `storage` keyword on the **original storage
   reference** (the supplied callable), not on the storage instance obtained by
   evaluating it.
2. WHEN a `FileField` was configured with a storage callable whose returned
   value is the module-level `default_storage` instance, THEN `deconstruct`
   SHALL include the `storage` keyword in the returned keyword arguments.
3. IF a `FileField` was configured with a storage callable, THEN the value
   recorded under the `storage` keyword SHALL be the original callable object
   itself (identity-preserved), never the storage instance produced by calling
   it.

## Requirement 2: Continue recording non-default storage references correctly

**User story:** As a developer relying on migration serialization, I want
non-default storage configurations to keep being recorded exactly as before, so
that existing behavior does not regress.

**Acceptance criteria**

1. WHEN a `FileField` was configured with a storage callable that returns a
   non-default storage instance and `deconstruct()` is invoked, THEN
   `deconstruct` SHALL include the `storage` keyword whose value is the original
   callable object (identity-preserved), not the evaluated instance.
2. WHEN a `FileField` was configured with a storage callable that is itself a
   storage class/instance callable (a callable object that is also usable as
   storage), THEN `deconstruct` SHALL include the `storage` keyword whose value
   is that original callable object.
3. WHEN a `FileField` was configured with a concrete (non-callable) storage
   instance that is not the default storage, THEN `deconstruct` SHALL include
   the `storage` keyword whose value is that storage instance.

## Requirement 3: Omit the storage keyword only for the true default

**User story:** As a developer, I want fields that use the default storage to
deconstruct without a spurious `storage` argument, so that migrations stay
clean.

**Acceptance criteria**

1. IF a `FileField` was configured with no storage argument (so it uses the
   module-level `default_storage`) and no callable was supplied, THEN
   `deconstruct` SHALL omit the `storage` keyword from the returned keyword
   arguments.
2. IF the original storage reference is the module-level `default_storage`
   instance itself, THEN `deconstruct` SHALL omit the `storage` keyword.
3. The system SHALL determine "is the default" by object identity against the
   module-level default storage, applied to the original reference selected in
   Requirement 1.

## Requirement 4: Preserve unrelated deconstruction behavior

**User story:** As a maintainer, I want the rest of `FileField.deconstruct()` to
behave exactly as before, so that this fix is narrowly scoped.

**Acceptance criteria**

1. WHEN `FileField.deconstruct()` is invoked, THEN it SHALL always include the
   `upload_to` keyword with the field's configured `upload_to` value.
2. WHEN `FileField.deconstruct()` is invoked and the field's maximum length is
   the default value of 100, THEN it SHALL omit the `max_length` keyword.
3. WHEN `FileField.deconstruct()` is invoked, THEN it SHALL return the same name,
   import path, and positional arguments as the base field deconstruction, with
   only the keyword-argument adjustments described above.

## Requirement 5: Preserve storage-configuration semantics at construction

**User story:** As a developer, I want `FileField` construction to keep
evaluating callable storage and validating its result, so that the deconstruct
fix does not change how storage is set up.

**Acceptance criteria**

1. WHEN a `FileField` is constructed with a callable storage argument, THEN the
   field SHALL evaluate the callable once and use the returned instance as its
   active storage.
2. IF the value returned by a storage callable is not a storage instance, THEN
   construction SHALL raise a `TypeError`.
3. WHEN a `FileField` is constructed with no storage argument, THEN the field's
   active storage SHALL be the module-level `default_storage`.
