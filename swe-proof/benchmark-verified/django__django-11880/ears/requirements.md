# Requirements: Independent error messages when copying a form field

## Introduction

Django form fields (the `Field` base class and its subclasses in
`django/forms/fields.py`) are defined once as class-level attributes on a form
and then copied for each form instance, so that every instance owns its own
fields and can mutate them without disturbing other instances of the same form
class. This per-instance duplication happens through the field's
`__deepcopy__` method, which is invoked by `copy.deepcopy`.

The `__deepcopy__` method starts from a shallow copy of the field. A shallow
copy leaves every mutable container attribute pointing at the *same* underlying
object as the original. Historically `__deepcopy__` gave the copy its own
widget and its own validators list, but it left the field's `error_messages`
dictionary shared with the original. As a result, all copies of a field shared
one `error_messages` dictionary: dynamically changing the error messages of one
form instance's field (or of an individual message string) was reflected on
every other instance's corresponding field, causing incorrectly raised or
mislabeled validation errors.

The goal is to make field duplication produce a fully independent copy: the
copied field must own its own `error_messages` mapping (with the same
contents), so that later mutation of one field's error messages is invisible
to any other copy — while the previously correct independence of the widget and
the validators list, the preserved subclass type, and all other observable
field behavior are kept intact.

## Requirement 1: Copied field owns an independent error-messages mapping

**User story:** As a developer building forms and model forms, I want each
copy of a form field to carry its own error-messages dictionary, so that
customizing the error messages of one form instance does not leak into other
instances of the same form.

**Acceptance criteria**

1. WHEN a form field (an instance of `Field` or any subclass in
   `django/forms/fields.py`) is duplicated via `copy.deepcopy`, THEN the field's
   `__deepcopy__` method SHALL produce a copy whose `error_messages` attribute
   is a different dictionary object from the original field's `error_messages`
   attribute (they SHALL NOT be the same object).
2. WHEN a form field is duplicated via `copy.deepcopy`, THEN the copy's
   `error_messages` mapping SHALL contain the same keys mapped to the same
   message values as the original field's `error_messages` at the time of the
   copy, including any messages that were overridden through the field's
   `error_messages` constructor argument or by a subclass.
3. IF the `error_messages` dictionary of one copy is subsequently modified
   (a key added, removed, or reassigned), THEN the `error_messages` dictionary
   of the original field and of any other copy SHALL remain unchanged.
4. WHEN a field is duplicated via `copy.deepcopy`, THEN the resulting object
   SHALL be an instance of exactly the same field class (including a user
   defined subclass) as the original field.

## Requirement 2: Preserve existing independence and behavior of copied fields

**User story:** As a maintainer of Django's forms framework, I want the field
duplication fix to keep every other copy guarantee that already worked, so that
no regression is introduced.

**Acceptance criteria**

1. WHEN a form field is duplicated via `copy.deepcopy`, THEN the copy's
   `widget` SHALL be an independent (deep-copied) widget object, distinct from
   the original field's widget, so that mutating one field's widget does not
   affect the other.
2. WHEN a form field is duplicated via `copy.deepcopy`, THEN the copy's
   `validators` SHALL be a new list object, distinct from the original field's
   `validators` list, while containing the same validators, so that appending
   to or otherwise mutating one field's validators list does not affect the
   other.
3. WHEN a form field is duplicated via `copy.deepcopy`, THEN the copy SHALL
   preserve the original field's other attributes (such as `required`, `label`,
   `initial`, `help_text`, `disabled`, and `label_suffix`) with equal values.
4. The system SHALL continue to allocate a fresh field for each form instance
   when a form class is instantiated, so that distinct instances of the same
   form class do not share field state.
5. WHEN a multi-value field (a field composed of sub-fields) is duplicated via
   `copy.deepcopy`, THEN each of its sub-fields SHALL likewise be duplicated
   independently, preserving the existing deep-copy behavior for such fields.
