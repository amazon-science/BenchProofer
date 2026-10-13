# Requirements: Skip credential lookup when authentication credentials are missing

## Introduction

The model-backed authentication backend in `django.contrib.auth.backends`
(`ModelBackend.authenticate`) is one of several authentication backends that
Django tries in turn for a set of credentials. When a login attempt supplies
credentials intended for a *different* backend, this backend can still be
invoked with an absent username and/or password.

In that situation the current behavior issues a credential-store query keyed on
a missing login name (e.g. `username IS NULL`, which can never match, since the
username field is not nullable) and then needlessly runs the password hasher.
Both are wasted work: the query is meaningless and the expensive hashing step is
pointless because there is no credential to verify. The password-hasher call was
originally introduced to mask the timing difference between existing and
non-existing users, but that concern does not apply when credentials are simply
absent — a different backend is handling this request and will introduce its own
timing characteristics regardless.

The goal is to make `ModelBackend.authenticate` short-circuit — performing no
database query and no password-hashing work — whenever it lacks the credentials
it needs, while preserving all existing authentication and permission behavior
when credentials *are* present.

## Requirement 1: Short-circuit when required credentials are absent

**User story:** As a developer who stacks multiple authentication backends, I
want the model-backed backend to do nothing (and touch nothing) when it is
handed credentials it cannot use, so that unrelated login attempts do not incur
useless database queries or expensive password hashing.

**Acceptance criteria**

1. WHEN `ModelBackend.authenticate` is called with no username supplied (neither
   as the positional/keyword `username` argument nor via the user model's
   `USERNAME_FIELD` key in the extra keyword arguments), THEN the method SHALL
   return `None` without performing any database query and without invoking the
   password hasher.
2. WHEN `ModelBackend.authenticate` is called with a resolved username present
   but the `password` argument absent (`None`), THEN the method SHALL return
   `None` without performing any database query and without invoking the
   password hasher.
3. WHEN `ModelBackend.authenticate` is called with no credentials at all (empty
   keyword arguments), THEN the method SHALL return `None` and SHALL perform
   zero database queries and zero password-hasher invocations.
4. The system SHALL treat the credential as absent only when it is `None`; an
   empty-but-present password value SHALL NOT trigger the short-circuit.
5. IF either the resolved username or the password is absent, THEN the
   short-circuit SHALL occur before any credential-store lookup is attempted, so
   that no query is emitted for a missing or null login name.

## Requirement 2: Resolve the username before deciding to short-circuit

**User story:** As a user authenticating with a custom user model, I want the
backend to honor the configured username field, so that credentials passed under
that field name are recognized.

**Acceptance criteria**

1. WHEN `ModelBackend.authenticate` is invoked without an explicit `username`
   argument, THEN the backend SHALL first attempt to obtain the username from the
   keyword argument whose key is the user model's `USERNAME_FIELD` before
   evaluating whether credentials are absent.
2. IF an explicit `username` argument is provided, THEN the backend SHALL use it
   as-is and SHALL NOT override it with the `USERNAME_FIELD` keyword argument.
3. WHEN a username is successfully resolved (from either source) and a password
   is present, THEN the backend SHALL proceed to the normal credential-check
   behavior described in Requirement 3 rather than short-circuiting.

## Requirement 3: Preserve normal authentication behavior when credentials are present

**User story:** As an end user logging in with valid or invalid credentials, I
want authentication to keep working exactly as before, so that the short-circuit
optimization does not change any real login outcome.

**Acceptance criteria**

1. WHEN both a resolved username and a password are present, THEN the backend
   SHALL perform exactly one credential-store lookup for the principal matching
   that username.
2. IF the lookup finds no matching principal, THEN the backend SHALL run the
   default password hasher exactly once (to keep the timing between existing and
   non-existing users uniform) and SHALL return `None`.
3. WHEN a matching principal is found, THEN the backend SHALL return that
   principal IF and only IF the supplied password verifies against the stored
   secret AND the principal is permitted to authenticate; otherwise it SHALL
   return `None`.
4. The system SHALL keep the existing rule that a principal whose active flag is
   `False` is rejected, while a principal lacking an active flag is allowed to
   authenticate.

## Requirement 4: Preserve permission and related backend behavior

**User story:** As a maintainer, I want the change to be confined to the
credential short-circuit, so that permission resolution and other backend
methods remain unaffected.

**Acceptance criteria**

1. The system SHALL continue to resolve a user's combined user-level and
   group-level permissions unchanged, including returning custom permissions
   granted directly to a user and via groups.
2. The system SHALL continue to grant all permissions to a superuser and to
   return no permissions for inactive or anonymous users.
3. The system SHALL leave the behavior of the other authentication backends and
   the multi-backend authentication dispatch (trying each backend and skipping
   backends that do not accept the provided arguments) unchanged.
