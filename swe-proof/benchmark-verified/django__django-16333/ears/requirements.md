# Requirements: Persist many-to-many selections when saving a user-creation form

## Introduction

`django.contrib.auth.forms.UserCreationForm` is a model-backed form (a subclass
of `django.forms.ModelForm`) that builds and persists a user instance from a
submitted username and password. Because it subclasses `ModelForm`, it may be
used with a custom user model that declares many-to-many relations, and the form
may then expose corresponding form fields (for example a multiple-choice field
backed by a related model).

The affected code is the `save()` method of `UserCreationForm` in
`django/contrib/auth/forms.py`. Its inherited `ModelForm.save()` behavior, when a
form containing many-to-many fields is committed, both writes the instance row
and writes the collected many-to-many selections. `UserCreationForm.save()`
overrides `save()` to derive the stored password from the raw password, but in
doing so it writes the instance without ever persisting the form's many-to-many
selections, so those related selections are silently lost on a committed save.

The goal is that a committed save of `UserCreationForm` persists both the user
instance and the full set of many-to-many selections the form collected, while
preserving all existing password-handling and deferred-save behavior.

## Requirement 1: Persist many-to-many selections on a committed save

**User story:** As a developer using `UserCreationForm` with a custom user model
that has many-to-many relations, I want a committed save to store my selected
related objects, so that the data submitted through the form's many-to-many
fields is not lost.

**Acceptance criteria**

1. WHEN `UserCreationForm.save()` is called with the commit argument true on a
   form whose model declares one or more many-to-many relations exposed as form
   fields, THEN the form SHALL persist the created user instance and SHALL also
   persist the many-to-many selections collected by the form.
2. WHEN a committed save persists the many-to-many selections, THEN, after the
   save returns, querying the saved user's many-to-many relation SHALL yield
   exactly the set of related objects that were submitted through the form,
   with no related objects omitted and none added.
3. The system SHALL persist the many-to-many selections only after the user
   instance itself has been written, so that the related links reference an
   existing, saved user row.

## Requirement 2: Preserve password derivation and the return value

**User story:** As a developer, I want `save()` to keep setting the user's
password from the submitted raw password and to keep returning the user
instance, so that existing behavior is unaffected by the many-to-many fix.

**Acceptance criteria**

1. WHEN `UserCreationForm.save()` is called, THEN the returned user instance
   SHALL have its stored password derived from the submitted first password
   value, regardless of whether the save is committed.
2. WHEN `UserCreationForm.save()` completes, THEN it SHALL return the created
   user instance.
3. The system SHALL leave the password-confirmation validation and the
   password-mismatch and password-strength checks unchanged.

## Requirement 3: Preserve deferred (non-committed) save behavior

**User story:** As a developer who calls `save()` deferring the commit, I want
nothing written to the database until I choose, so that I retain control over
when the instance and its related selections are persisted.

**Acceptance criteria**

1. IF `UserCreationForm.save()` is called with the commit argument false, THEN
   the form SHALL NOT write the user instance to the database and SHALL NOT
   write any many-to-many selections at that time.
2. WHEN a save is deferred, THEN the form SHALL still make available the deferred
   mechanism for writing the many-to-many selections later, so that the caller
   can persist them after saving the instance.
3. The system SHALL continue to return the built, unsaved user instance from a
   deferred save.

## Requirement 4: Preserve behavior for forms without many-to-many fields

**User story:** As a developer using `UserCreationForm` with a model that has no
many-to-many relations, I want save behavior to remain exactly as before, so
that the change is safe for the common case.

**Acceptance criteria**

1. WHEN `UserCreationForm.save()` is committed on a form whose model exposes no
   many-to-many fields, THEN the form SHALL persist the user instance exactly as
   it did previously and SHALL NOT raise an error due to the absence of
   many-to-many selections.
2. The system SHALL keep the existing username normalization, field ordering,
   and validation behavior of `UserCreationForm` unchanged.
