# Password reset token invalidation on email change

## Introduction

Django's password reset feature issues a single-use token for a user via
`django.contrib.auth.tokens.PasswordResetTokenGenerator`. A token is produced
by `make_token(user)` and validated later by `check_token(user, token)`. The
token is a keyed hash (HMAC) computed over a snapshot of user state assembled
by the private helper `PasswordResetTokenGenerator._make_hash_value(user,
timestamp)`. When any piece of that state changes, previously issued tokens no
longer match and are rejected.

Today the hashed state covers the user's primary key, password, and last-login
timestamp. Consequently, if a user requests a password reset and then changes
their email address before using the reset link, the outstanding token still
validates — a security gap, because the reset was requested under the old email
identity.

The goal is to make a change to the user's email address invalidate any
outstanding password reset token, while preserving all existing token behavior.
The email address must be read through the user model's own configured email
field (via `AbstractBaseUser.get_email_field_name()`), because a user model is
not required to have an `email` attribute and its email field may be named
differently or hold no value. This behavior is localized to
`PasswordResetTokenGenerator._make_hash_value()` and its callers
`make_token()` / `check_token()`.

## Requirement 1: Email address participates in the token

**User story:** As a site operator, I want a user's password reset token to
depend on their current email address, so that changing the email address after
a reset was requested makes the outstanding token unusable.

**Acceptance criteria**

1. WHEN a token is generated for a user with `make_token(user)` and later the
   user's email address (the attribute named by
   `user.get_email_field_name()`) is changed to a different value, THEN
   `check_token(user, token)` SHALL return `False` for the previously generated
   token.
2. WHEN a token is generated for a user and the user's email address is
   subsequently left unchanged, THEN `check_token(user, token)` SHALL return
   `True` for that token (subject to the other existing validity conditions).
3. The system SHALL include the user's current email address value as part of
   the state that `_make_hash_value(user, timestamp)` contributes to the token
   hash, so that two users (or two states of one user) that differ only in email
   address produce different tokens.
4. WHEN assembling the hashed state, THEN the subject SHALL read the email value
   from the attribute whose name is returned by `user.get_email_field_name()`,
   rather than assuming a fixed attribute name.

## Requirement 2: Users without an email address are supported

**User story:** As a developer using a custom user model, I want token
generation and validation to work even when the user has no email attribute or a
null email, so that models permitted by `AbstractBaseUser` are not broken.

**Acceptance criteria**

1. IF the user has no email attribute at all, THEN `_make_hash_value(user,
   timestamp)` SHALL still produce a value without raising an error, treating the
   missing email as an empty value.
2. IF the user's email field value is `None` (null), THEN `_make_hash_value(user,
   timestamp)` SHALL treat it as an empty value and SHALL NOT raise an error.
3. WHEN a token is generated for a user whose email value is empty/absent and the
   email value is not subsequently changed, THEN `check_token(user, token)` SHALL
   return `True` for that token (subject to the other existing validity
   conditions).
4. WHEN a user whose email value was empty/absent has that email set to a
   non-empty value after a token was generated, THEN `check_token(user, token)`
   SHALL return `False` for the previously generated token.

## Requirement 3: Existing token behavior is preserved

**User story:** As a Django user, I want all previously working password reset
token behavior to continue working unchanged, so that adding email sensitivity
introduces no regression.

**Acceptance criteria**

1. WHEN a token is generated and the user's password, last-login timestamp, and
   email are all unchanged, THEN `check_token(user, token)` SHALL return `True`
   within the allowed time window and `False` once
   `settings.PASSWORD_RESET_TIMEOUT` seconds have elapsed.
2. WHEN the user's password changes after a token is generated, THEN
   `check_token(user, token)` SHALL return `False` for the previously generated
   token.
3. IF `check_token` is called with a `None` user or a `None`/empty token, THEN it
   SHALL return `False`.
4. The system SHALL continue to accept a token generated with a generator whose
   `secret` attribute is set to a value other than `settings.SECRET_KEY` when
   validated by a generator configured with that same secret, and SHALL reject a
   token when the validating generator uses a different secret than the one used
   to create it.
5. The system SHALL continue to honor the configured hashing algorithm: a token
   created and checked by generators using the default hashing algorithm SHALL
   validate, and pre-existing (legacy `sha1`) tokens SHALL continue to validate
   under the legacy verification path.
6. WHEN the same unchanged user state is reused (e.g. a freshly reloaded copy of
   the same user), THEN tokens generated at the same timestamp SHALL be equal and
   mutually acceptable.
