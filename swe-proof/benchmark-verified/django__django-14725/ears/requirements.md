# Requirements: Edit-only model formsets (disallow new object creation)

## Introduction

Django's model formsets (built via `modelformset_factory` and
`inlineformset_factory` in `django/forms/models.py`, backed by
`BaseModelFormSet.save`) always persist two groups of forms when saved: the
forms bound to objects already present (the "existing" forms derived from the
formset's queryset / initial forms) and the forms that describe brand-new
objects (the "extra" forms). Because of this, there is currently no reliable
way to expose an "edit only" formset that updates the objects it was shown but
never creates new ones. Users attempt to achieve this by setting `extra=0`,
but that only controls how many empty extra forms are rendered — additional
forms can still be submitted (via JavaScript or hand-crafted POST data) and
those forms will create new database rows.

The goal is to give the formset factories an explicit opt-in that makes the
resulting formset refuse to create new objects on save, while leaving updates
to existing in-scope objects and all default (non-opt-in) behavior unchanged.
The affected code is `BaseModelFormSet.save`, the `modelformset_factory`
function, and the `inlineformset_factory` function, all in
`django/forms/models.py`.

## Requirement 1: Opt-in edit-only mode on the model formset factory

**User story:** As a developer building an object-editing view, I want to
create a model formset that can update the records it manages but will never
insert new records, so that neither empty-form manipulation nor injected POST
data can add unwanted objects.

**Acceptance criteria**

1. The system SHALL let a caller of `modelformset_factory` request edit-only
   behavior through a boolean keyword argument named `edit_only`.
2. IF a caller does not supply `edit_only`, THEN `modelformset_factory` SHALL
   default it to `False`, preserving the historic behavior in which saving the
   formset both updates existing objects and creates new ones.
3. The system SHALL record the requested edit-only setting on the generated
   formset class so that every instance of that formset observes the same
   setting.
4. The system SHALL continue to accept and honor every other
   `modelformset_factory` argument (for example the number of extra forms, the
   fields/exclude selection, deletion, minimum/maximum form counts, and the
   queryset) exactly as before when edit-only mode is requested; requesting
   edit-only mode SHALL affect only whether new objects are created on save.

## Requirement 2: Saving an edit-only formset never creates new objects

**User story:** As a developer, I want saving an edit-only formset to write
only the changes to already-managed objects, so that submitted extra forms are
silently ignored for the purpose of object creation.

**Acceptance criteria**

1. WHEN an edit-only formset is valid and its `save` method is called, THEN the
   formset SHALL persist the updates described by the forms bound to its
   existing (initial) objects.
2. WHEN an edit-only formset is valid and its `save` method is called, THEN the
   formset SHALL NOT create any new objects, even when the submitted data
   contains additional (extra) forms that are fully filled in and valid.
3. WHEN an edit-only formset's `save` method returns, THEN the returned list
   SHALL contain exactly the objects persisted from the existing forms and no
   objects that would have been newly created.
4. WHEN a formset that is NOT in edit-only mode is valid and its `save` method
   is called, THEN the formset SHALL both persist updates to existing objects
   and create the new objects described by its filled-in extra forms, returning
   all of them (existing then new).
5. WHEN an edit-only formset with filled-in extra forms is validated, THEN the
   formset SHALL still report itself as valid (edit-only mode changes what is
   saved, not whether otherwise-valid submitted data is accepted).

## Requirement 3: Edit-only mode does not touch objects outside the formset's scope

**User story:** As a developer, I want an edit-only formset to leave objects
outside its queryset untouched, so that a form referencing an out-of-scope
record can neither create a duplicate nor alter that record.

**Acceptance criteria**

1. WHEN an edit-only formset is saved and one of its forms carries the primary
   key of an object that is not part of the formset's queryset, THEN the
   formset SHALL NOT create a new object for that submission.
2. WHEN an edit-only formset is saved and a form references an object outside
   the formset's queryset, THEN that out-of-scope object SHALL remain unchanged.
3. The system SHALL leave the complete set of stored objects unchanged except
   for the in-scope existing objects whose forms were updated.

## Requirement 4: Edit-only support on inline model formsets

**User story:** As a developer using inline formsets tied to a parent object, I
want the same edit-only guarantee, so that inline children can be edited but
not added through the inline formset.

**Acceptance criteria**

1. The system SHALL let a caller of `inlineformset_factory` request edit-only
   behavior through the same boolean keyword argument named `edit_only`,
   defaulting to `False`.
2. The system SHALL forward the requested edit-only setting to the underlying
   model formset it constructs, so that an inline formset built with edit-only
   mode enabled behaves according to Requirements 2 and 3.
3. WHEN an edit-only inline formset is valid and saved, THEN it SHALL persist
   updates to its existing child objects and SHALL NOT create new child objects
   from filled-in extra forms.
4. The system SHALL preserve all other `inlineformset_factory` behavior
   (including the parent relationship and the ability to disable deletion) when
   edit-only mode is requested.
