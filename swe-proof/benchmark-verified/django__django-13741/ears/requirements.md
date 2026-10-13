# Requirements — ReadOnlyPasswordHashField is non-editable by default

## Introduction

`django.contrib.auth.forms.ReadOnlyPasswordHashField` is a `forms.Field`
subclass (defined in `django/contrib/auth/forms.py`) used to *display* a stored
password hash summary in admin/user-change forms. Because the field only shows a
read-only summary and renders no editable input, a value submitted by the client
must never be able to change the stored password.

Historically this non-editability was enforced imperatively by the field
overriding change-detection and data-binding behavior so that it always kept its
initial value and always reported "no change". Separately,
`UserChangeForm` (same module) carried a form-level cleaning step for its
`password` field that discarded any submitted value and returned the initial
value, and Django's documentation instructed authors of custom user forms to
replicate that cleaning step.

The base `forms.Field` class already supports a `disabled` option (as noted in
the issue): a disabled field is displayed but not editable, and any value a
client submits is ignored in favor of the field's initial data. The goal of this
change is to make `ReadOnlyPasswordHashField` rely on that built-in mechanism —
it should be disabled by default — so that the special-case overrides on the
field and the form-level cleaning step become unnecessary and can be removed
without altering observable behavior.

The affected module is `django/contrib/auth/forms.py`; the relevant behavior of
the base field lives in `django/forms/fields.py` (the `disabled` handling in
`Field.__init__`, `Field.bound_data`, and `Field.has_changed`).

## Requirement 1: ReadOnlyPasswordHashField is disabled by default

**User story:** As a developer using `ReadOnlyPasswordHashField` to display a
password hash, I want the field to be non-editable out of the box, so that a
tampered submission can never change the stored value even if I forget to add
any custom cleaning logic.

**Acceptance criteria**

1. WHEN a `ReadOnlyPasswordHashField` is constructed without an explicit
   `disabled` argument, THEN the constructed field SHALL report its `disabled`
   attribute as `True`.
2. WHEN a `ReadOnlyPasswordHashField` is constructed with an explicit `disabled`
   argument, THEN the constructed field SHALL use exactly the caller-supplied
   value for its `disabled` attribute (the default SHALL apply only when the
   caller supplies none).
3. The system SHALL continue to treat `ReadOnlyPasswordHashField` as not
   required by default: WHEN the field is constructed without an explicit
   `required` argument, THEN its `required` attribute SHALL be `False`.
4. WHEN the field is constructed with an explicit `required` argument, THEN the
   constructed field SHALL use exactly the caller-supplied value for its
   `required` attribute.

## Requirement 2: A read-only password-hash field never reports a change

**User story:** As a maintainer, I want a displayed password-hash field to never
detect a change between its initial value and a submitted value, so that
tampering with the submitted data is ignored.

**Acceptance criteria**

1. WHEN change detection is performed on a default-constructed
   `ReadOnlyPasswordHashField` given any initial value and any submitted value
   (including two differing non-empty strings), THEN the field SHALL report that
   no change occurred.
2. WHEN data-binding is performed on a default-constructed
   `ReadOnlyPasswordHashField`, THEN the field SHALL yield the field's initial
   value, disregarding whatever value the client submitted.
3. The system SHALL derive this behavior from the field's disabled state rather
   than from any bespoke change-detection or data-binding override on the field:
   IF the field's `disabled` attribute is `True`, THEN change detection SHALL
   report no change and data-binding SHALL yield the initial value.

## Requirement 3: UserChangeForm preserves the stored password unchanged

**User story:** As an administrator editing a user via `UserChangeForm`, I want
the password field to keep its stored value regardless of what is submitted for
it, so that the password is never accidentally altered by editing the form.

**Acceptance criteria**

1. WHEN a bound `UserChangeForm` is validated, THEN the cleaned value for the
   `password` field SHALL equal the form's initial value for that field,
   irrespective of any value submitted for the password field.
2. The system SHALL preserve this password-preservation behavior without
   requiring `UserChangeForm` (or a custom form modeled on it) to define its own
   password-cleaning step.
3. WHILE the initial data supplies a password value, the validated
   `UserChangeForm` SHALL expose that same initial password value as the cleaned
   result.

## Requirement 4: Existing display and form behavior is preserved

**User story:** As a Django user, I want all other behavior of the
password-hash field and the surrounding auth forms to remain unchanged, so that
this change is a safe refactor.

**Acceptance criteria**

1. The system SHALL continue to render the read-only password-hash summary for a
   populated password value exactly as before, and SHALL continue to render a
   graceful summary when the initial password value is absent (a missing/`None`
   value SHALL not raise an error).
2. The system SHALL keep `UserChangeForm`'s password field present and its
   help-text link to the password-change form intact.
3. The system SHALL keep all other auth-form behavior unchanged, including the
   creation, authentication, password-change, password-set, and password-reset
   forms and their validation outcomes.
