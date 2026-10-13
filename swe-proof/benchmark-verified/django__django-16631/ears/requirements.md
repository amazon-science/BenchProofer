# Requirements: Honor rotated-secret fallbacks when verifying authenticated sessions

## Introduction

Django authenticates a request's session by comparing a hash stored in the
session against an HMAC derived from the user's password and the project's
signing secret. The HMAC is produced by
`django.contrib.auth.base_user.AbstractBaseUser.get_session_auth_hash`, which
delegates to `django.utils.crypto.salted_hmac`. By default `salted_hmac` keys
the HMAC with `settings.SECRET_KEY`.

The `SECRET_KEY_FALLBACKS` setting exists so administrators can rotate the
signing secret without invalidating outstanding sessions: the previous secret is
moved into `SECRET_KEY_FALLBACKS` and is meant to keep verifying existing
sessions until it is removed. However, session verification in
`django.contrib.auth.get_user` only ever compares against the hash computed with
the *current* `SECRET_KEY`. Consequently, rotating `SECRET_KEY` immediately
logs every user out even though their old secret is still listed in
`SECRET_KEY_FALLBACKS`.

The goal is to make session verification consult the fallback secrets: a session
whose stored hash was produced by a still-listed fallback secret must remain
authenticated, and its stored hash must be transparently upgraded to the current
secret so that authentication survives even after the fallback is later removed.
The affected code is `django.contrib.auth.get_user` (the session-verification
branch), `AbstractBaseUser.get_session_auth_hash`, and a new capability on
`AbstractBaseUser` to compute the session auth hash under the fallback secrets.

## Requirement 1: Compute the session auth hash under an explicit secret

**User story:** As a developer relying on Django session authentication, I want
the user's session auth hash to be computable under a chosen signing secret, so
that a session hash produced by a rotated-out secret can still be reconstructed
and matched.

**Acceptance criteria**

1. The system SHALL provide, on `AbstractBaseUser`, the ability to compute the
   session authentication hash using a caller-supplied signing secret instead of
   the project's current `SECRET_KEY`.
2. WHEN the session authentication hash is computed with no explicit secret
   supplied, THEN `AbstractBaseUser` SHALL compute the HMAC keyed with the
   current `settings.SECRET_KEY`, producing the same value as before this change.
3. The system SHALL derive the session authentication hash as the SHA-256
   `salted_hmac` of the user's stored password field under the fixed key salt
   `"django.contrib.auth.models.AbstractBaseUser.get_session_auth_hash"`,
   regardless of which signing secret is used.
4. WHEN a signing secret is supplied to the session-auth-hash computation, THEN
   the resulting hash SHALL equal the hash that the same user would have produced
   while that secret was the active `SECRET_KEY`.

## Requirement 2: Enumerate session auth hashes for all fallback secrets

**User story:** As an administrator rotating secrets, I want the framework to be
able to reproduce a user's session auth hash under every configured fallback
secret, so that sessions signed with a previous secret can still be recognized.

**Acceptance criteria**

1. The system SHALL provide, on `AbstractBaseUser`, a way to obtain the session
   authentication hash of the user computed under each secret listed in
   `settings.SECRET_KEY_FALLBACKS`.
2. WHEN `settings.SECRET_KEY_FALLBACKS` contains multiple secrets, THEN the
   system SHALL yield one session authentication hash per fallback secret, in the
   order the secrets appear in `SECRET_KEY_FALLBACKS`.
3. WHEN `settings.SECRET_KEY_FALLBACKS` is empty, THEN the system SHALL yield no
   fallback session authentication hashes.
4. Each yielded fallback hash SHALL be computed by the same session-auth-hash
   derivation as Requirement 1, keyed with the corresponding fallback secret.

## Requirement 3: Verify sessions against the current secret, then fallbacks

**User story:** As a user whose site rotated its secret key, I want to stay
logged in as long as the secret that signed my session is still listed as a
fallback, so that key rotation does not forcibly log everyone out.

**Acceptance criteria**

1. WHEN `get_user` verifies a request whose user model exposes a session auth
   hash and the session's stored auth hash equals the hash computed under the
   current `SECRET_KEY`, THEN `get_user` SHALL return the authenticated user and
   SHALL leave the session unchanged.
2. IF the session's stored auth hash does not equal the current-secret hash but
   equals the session auth hash computed under one of the secrets in
   `settings.SECRET_KEY_FALLBACKS`, THEN `get_user` SHALL return the
   authenticated user rather than an anonymous user.
3. WHEN a session is accepted on the strength of a fallback secret, THEN
   `get_user` SHALL rotate the session key (cycle the session to a new key
   without discarding its data) so that the returned session key differs from
   the session key before verification.
4. WHEN a session is accepted on the strength of a fallback secret, THEN
   `get_user` SHALL replace the session's stored auth hash with the hash computed
   under the current `SECRET_KEY`, so that a subsequent verification against the
   current secret alone succeeds.
5. IF the session's stored auth hash matches neither the current-secret hash nor
   any fallback-secret hash, THEN `get_user` SHALL flush the session and SHALL
   return an anonymous user.
6. IF the request has no stored session auth hash, THEN `get_user` SHALL treat
   verification as failed, SHALL flush the session, and SHALL return an anonymous
   user.
7. WHEN evaluating fallback secrets, THEN `get_user` SHALL stop at the first
   fallback whose hash matches the stored session auth hash and SHALL NOT require
   evaluating the remaining fallbacks.

## Requirement 4: Preserve authentication after the matching fallback is removed

**User story:** As an administrator, I want a session that was upgraded during a
fallback match to keep working after I finally remove the old secret, so that
rotation followed by cleanup does not log the user out.

**Acceptance criteria**

1. WHEN a session was accepted and its stored auth hash upgraded to the current
   secret during a prior verification, and that session is later verified again
   under a configuration whose current `SECRET_KEY` is the same secret used for
   the upgrade and whose `SECRET_KEY_FALLBACKS` no longer lists the original
   signing secret, THEN `get_user` SHALL return the authenticated user.
2. WHILE the current `SECRET_KEY` remains the secret used to upgrade a session's
   stored auth hash, `get_user` SHALL continue to accept that session against the
   current secret without needing any fallback secret.

## Requirement 5: Preserve existing session-verification behavior (regression protection)

**User story:** As a maintainer, I want the existing authentication and session
guarantees to remain intact, so that adding fallback support does not regress
security or unrelated behavior.

**Acceptance criteria**

1. The system SHALL keep `get_session_auth_hash` returning the SHA-256 HMAC of
   the user's password under the current `SECRET_KEY`, unchanged in value for a
   given user and secret.
2. WHEN a request's session references an authentication backend that is not
   listed in `settings.AUTHENTICATION_BACKENDS`, or the session lacks the stored
   user id or backend path, THEN `get_user` SHALL return an anonymous user.
3. WHEN the resolved user model does not expose a session auth hash capability,
   THEN `get_user` SHALL return the user without performing session-hash
   verification.
4. The system SHALL keep `salted_hmac` defaulting its signing secret to
   `settings.SECRET_KEY` when no secret is supplied, so that unrelated callers of
   `salted_hmac` are unaffected.
5. WHEN a session's stored auth hash matches the current-secret hash, THEN
   `get_user` SHALL NOT rotate or flush the session and SHALL NOT alter the
   stored auth hash.
