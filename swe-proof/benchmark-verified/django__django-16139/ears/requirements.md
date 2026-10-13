# Requirements: Correct the password-change link in the user change form

## Introduction

Django's admin edits a user through `UserChangeForm` in
`django/contrib/auth/forms.py`. That form exposes a read-only password field
(`ReadOnlyPasswordHashField`) whose help text contains an HTML anchor pointing
at the separate "change password" form for the user being edited. The anchor's
target is a *relative* URL: the help text template holds a single positional
placeholder inside `<a href="{}">`, and `UserChangeForm.__init__` fills that
placeholder in with a path that is resolved relative to the current change-form
URL.

The admin normally reaches a user's change form at a URL shaped like
`.../<app>/<model>/<pk>/change/`, so the original relative target `../password/`
resolved to `.../<app>/<model>/<pk>/password/`. However, a user record can also
be reached through another model's admin that references it via `to_field`
(e.g. `to_field="uuid"`), in which case the change-form URL carries the value of
that field rather than the primary key (for example
`.../<model>/<uuid-value>/change/?_to_field=uuid`). Resolving `../password/`
against such a URL produces `.../<model>/<uuid-value>/password/`, which is not a
valid password-change URL and yields a 404.

The goal is to make the password-change link in the user change form's help
text always resolve to the password-change form keyed by the user's own primary
key, regardless of which field value was used to locate the change form, while
leaving the help-text template and all other behavior of the form untouched.
The affected code is the placeholder-filling step in
`UserChangeForm.__init__`.

## Requirement 1: Link to the password form by the user's primary key

**User story:** As an administrator who reaches a user's change form through
another model's admin that references the user via a `to_field` other than the
primary key, I want the "change the password using this form" link to open the
correct password-change page, so that I am not sent to a broken (404) URL.

**Acceptance criteria**

1. WHEN `UserChangeForm` is initialized for a bound user instance, THEN the form
   SHALL fill the single positional placeholder in the password field's help
   text with a relative URL that, resolved against the user's admin change-form
   URL, points at that user's password-change form addressed by the user's own
   primary key.
2. WHEN the user's admin change form is reached through a `to_field` reference
   whose value differs from the primary key (so the change-form URL contains
   that field's value rather than the primary key), THEN the URL produced by
   resolving the help-text link against the change-form URL SHALL equal the
   admin password-change URL for that user keyed by the user's primary key.
3. The relative URL placed in the help text SHALL be constructed from the
   editing user's own primary key, such that it climbs out of the current
   record segment of the change-form URL and re-descends through the record
   identified by the primary key to reach that record's `password` path segment
   — i.e. it SHALL NOT assume that the current change-form URL segment already
   identifies the user by primary key.
4. WHEN `UserChangeForm` is initialized for a user reached by primary key in the
   ordinary way, THEN the resolved password-change link SHALL still point at
   that user's password-change form keyed by the primary key (the behavior for
   the common case SHALL remain correct).

## Requirement 2: Preserve the help text and password field behavior (regression protection)

**User story:** As a maintainer, I want the password field's help text, its
link structure, and every other aspect of the user change form to keep working
exactly as before, so that fixing the `to_field` case does not disturb existing
behavior.

**Acceptance criteria**

1. The password field's help text SHALL continue to render as human-readable
   guidance containing exactly one HTML anchor (`<a href="...">...</a>`) whose
   target is the password-change link described in Requirement 1, with the
   surrounding wording of the template otherwise unchanged.
2. WHEN `UserChangeForm` is initialized and no password field is present on the
   form (for example a subclass that excludes it), THEN initialization SHALL
   complete without error and SHALL NOT attempt to fill the help-text
   placeholder.
3. The user change form SHALL continue to expose the password as a read-only
   value that is never returned as an editable password, and SHALL keep its
   initial password value available for correct rendering.
4. WHEN `UserChangeForm` is initialized, THEN it SHALL continue to optimize the
   user-permissions field's queryset (selecting the related content type) as it
   did previously, and SHALL leave the username field and all other fields'
   behavior unchanged.
5. The change to the password-change link SHALL affect only the user change
   form; the user creation form, the password-change/set forms, the
   authentication form, and the password-reset form SHALL retain their existing
   behavior unchanged.
