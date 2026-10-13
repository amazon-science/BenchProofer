# Requirements: File upload input suppresses the required marker when initial data exists

## Introduction

In Django's forms widget layer (`django/forms/widgets.py`), a widget decides
whether the rendered HTML `<input>` element carries the `required` attribute
through its `use_required_attribute(initial)` method. The base `Widget` rule is
that any non-hidden input is, in principle, required.

For a file-upload input (the `FileInput` widget, and every widget derived from
it), there is an additional consideration: when an initial value is already
present — for example a file already stored on a model instance that is being
edited — the field must NOT advertise itself as required, because the user is
allowed to leave the upload control blank to keep the existing file. Previously
this suppression logic lived only on the clearable subclass
(`ClearableFileInput`), so a plain `FileInput` still rendered `required` even
when initial data existed. The goal is to make the "initial value suppresses
required" behavior apply to `FileInput` itself (and therefore to all of its
subclasses), while leaving every other widget's required behavior unchanged.

The behavior is localized to the `use_required_attribute` method of the
`FileInput` widget in `django/forms/widgets.py`, and is observable through the
HTML that a `forms.FileField` renders when it uses a file input widget.

## Requirement 1: A file input suppresses the required marker when an initial value exists

**User story:** As a user editing an object that already has an uploaded file,
I want the file field to not be marked required, so that I can submit the form
without re-uploading and keep the existing file.

**Acceptance criteria**
1. WHEN `use_required_attribute` is called on a `FileInput` widget with an
   initial value that is falsy (for example `None`), THEN the widget SHALL
   report that the required marker is to be used (return a truthy result),
   provided the base rule would otherwise mark the input required.
2. WHEN `use_required_attribute` is called on a `FileInput` widget with a
   truthy initial value (for example a non-empty file name such as a stored
   file), THEN the widget SHALL report that the required marker is NOT to be
   used (return a falsy result).
3. The `FileInput` widget's decision to use the required marker SHALL be the
   conjunction of the base widget rule (a non-hidden input is required) and the
   absence of a truthy initial value.

## Requirement 2: Rendered file field HTML reflects the presence of initial data

**User story:** As a developer rendering a form with a file field, I want the
generated `<input type="file">` markup to include or omit the `required`
attribute according to whether initial data exists, so that the client-side
requirement matches the intended behavior.

**Acceptance criteria**
1. WHEN a `forms.FileField` that uses a plain `FileInput` widget is rendered on
   a form instance that has no initial value for the field, THEN the produced
   file `<input>` element SHALL include the `required` attribute.
2. WHEN a `forms.FileField` that uses a plain `FileInput` widget is rendered on
   a form instance whose initial data supplies a truthy value for the field,
   THEN the produced file `<input>` element SHALL NOT include the `required`
   attribute.
3. WHEN the `required` attribute is omitted from a file `<input>` because
   initial data exists, THEN the element SHALL otherwise be rendered unchanged
   (same input type, name, and other attributes as when required data is
   absent, differing only by the presence of the `required` attribute).

## Requirement 3: Preserve existing clearable file input and base widget behavior

**User story:** As a maintainer, I want the change to move suppression onto the
file input without altering the clearable subclass or unrelated widgets, so
that no existing behavior regresses.

**Acceptance criteria**
1. The system SHALL keep the clearable file-upload widget's behavior of not
   marking the input required when a truthy initial value is present, and of
   allowing the required marker when no initial value is present.
2. WHEN a non-file input widget evaluates whether to use the required marker,
   THEN its decision SHALL remain governed solely by the base rule (required
   exactly when the input is not hidden), unaffected by the presence of an
   initial value.
3. The system SHALL keep `FileInput`'s existing rendering behavior of never
   emitting a stored value into the file `<input>` element.
4. The system SHALL keep `FileInput`'s existing rule that a submitted value is
   considered omitted from the data exactly when no entry for the field name is
   present in the uploaded files.
