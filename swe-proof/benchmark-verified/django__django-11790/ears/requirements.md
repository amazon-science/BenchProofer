# Requirements: AuthenticationForm username field maxlength HTML attribute

## Introduction

`AuthenticationForm` (in `django/contrib/auth/forms.py`) dynamically configures
its `username` field during `__init__`, deriving the field's effective maximum
length from the active user model's `USERNAME_FIELD` (falling back to 254 when
that model field declares no `max_length`). A prior refactor stopped propagating
this computed length onto the field's widget, so the rendered `<input>` for the
username no longer carries a `maxlength` HTML attribute. The goal is to restore
the widget-level `maxlength` so the client-side length limit again matches the
form field's `max_length`, while preserving all existing form-field behavior
(the computed `max_length` value, the label defaulting, authentication, and
validation).

The behavior is localized to the `AuthenticationForm.__init__` method and the
configuration of `self.fields['username']` and its associated widget.

## Requirement 1: Widget maxlength attribute mirrors the username field length

**User story:** As a user visiting a login page, I want the username input to
advertise its maximum length to the browser, so that the browser enforces the
same input limit the server applies.

**Acceptance criteria**
1. WHEN an `AuthenticationForm` is instantiated, THEN the `username` field's
   widget SHALL expose a `maxlength` attribute whose value equals the field's
   effective maximum length.
2. WHEN the active user model's `USERNAME_FIELD` declares a `max_length`, THEN
   the `username` field's widget `maxlength` attribute SHALL equal that declared
   `max_length`.
3. IF the active user model's `USERNAME_FIELD` declares no `max_length` (a falsy
   value), THEN the `username` field's widget `maxlength` attribute SHALL equal
   254.
4. The `username` field's widget `maxlength` attribute value SHALL always be
   equal to the field's `max_length` value for the same form instance.

## Requirement 2: Preserve the computed field max_length

**User story:** As a developer relying on server-side validation, I want the
username field's `max_length` to keep reflecting the user model, so that
existing length enforcement and behavior are unchanged.

**Acceptance criteria**
1. WHEN an `AuthenticationForm` is instantiated and the active user model's
   `USERNAME_FIELD` declares a `max_length`, THEN the `username` field's
   `max_length` SHALL equal that declared `max_length`.
2. IF the active user model's `USERNAME_FIELD` declares no `max_length` (a falsy
   value), THEN the `username` field's `max_length` SHALL equal 254.
3. The system SHALL leave the `username` field free of validation errors that
   arise solely from configuring the length limit, for input within the allowed
   length.

## Requirement 3: Preserve existing form behavior

**User story:** As a maintainer, I want the rest of `AuthenticationForm` to
behave exactly as before, so that adding the widget attribute introduces no
regressions.

**Acceptance criteria**
1. WHEN an `AuthenticationForm` is instantiated and the `username` field has no
   explicit label, THEN the field's label SHALL default to the capitalized
   verbose name of the user model's `USERNAME_FIELD`.
2. The system SHALL continue to authenticate a submitted username/password pair
   and report an invalid-login error when authentication fails.
3. The system SHALL leave the configuration and rendering of all other form
   fields (including the password field and its autocomplete attribute)
   unchanged by the addition of the username widget length attribute.
