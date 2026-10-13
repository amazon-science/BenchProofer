# Requirements: Preserve SameSite when deleting cookies

## Introduction

When a Django HTTP response expires (deletes) a cookie, the emitted
`Set-Cookie` header historically dropped the `SameSite` attribute and set the
`Secure` flag only when the cookie name began with `__Secure-` or `__Host-`.
Modern browsers reject a `Set-Cookie` whose `SameSite=None` is not accompanied
by `Secure`, so a deletion header lacking these attributes can be ignored — the
cookie is never actually cleared.

This change concerns the cookie-deletion path used throughout Django's HTTP
layer:

- `django.http.response.HttpResponseBase.delete_cookie` — the method that
  builds the expiry `Set-Cookie` header (it delegates to `set_cookie`).
- `django.contrib.sessions.middleware.SessionMiddleware.process_response` —
  which deletes the session cookie when the session becomes empty.
- `django.contrib.messages.storage.cookie.CookieStorage` — which deletes the
  messages cookie when there is no message data to store.

The goal: allow callers to specify the `SameSite` policy of a deletion cookie,
carry that policy onto the resulting header, mark the deletion cookie `Secure`
when the policy requires it, and have the session and messages deletion paths
propagate the project's configured `SameSite` setting — all without regressing
the pre-existing deletion behavior.

## Requirement 1: delete_cookie accepts and applies a SameSite policy

**User story:** As a developer expiring a cookie, I want to declare the cookie's
SameSite policy on deletion, so that the resulting `Set-Cookie` header is not
rejected by browsers and matches the policy the cookie was originally set with.

**Acceptance criteria**

1. The `delete_cookie` method of the HTTP response class SHALL accept an
   optional SameSite policy argument whose default value is `None`, in addition
   to its existing key, path, and domain arguments, and SHALL remain callable
   with only the cookie key.
2. WHEN `delete_cookie` is called with a SameSite policy of `'lax'`, THEN the
   response's cookie for that key SHALL carry a `samesite` attribute equal to
   `'lax'`.
3. WHEN `delete_cookie` is called with a SameSite policy of `'strict'`, THEN the
   response's cookie for that key SHALL carry a `samesite` attribute equal to
   `'strict'`.
4. WHEN `delete_cookie` is called with a SameSite policy of `'none'`, THEN the
   response's cookie for that key SHALL carry a `samesite` attribute equal to
   `'none'`.
5. The SameSite policy supplied to `delete_cookie` SHALL be applied through the
   same cookie-writing routine (`set_cookie`) that produces normal cookies, so
   the same validation and normalization of the SameSite value apply.

## Requirement 2: Secure flag on SameSite=None deletions

**User story:** As a developer, I want a deletion cookie with `SameSite=None` to
be marked `Secure`, so that browsers honor the deletion instead of discarding
the header.

**Acceptance criteria**

1. WHEN `delete_cookie` is called with a SameSite policy equal to `'none'`
   (case-insensitively), THEN the response's cookie for that key SHALL have its
   `secure` flag set to `True`.
2. The system SHALL treat the SameSite value case-insensitively when deciding
   whether it denotes the `none` policy for the purpose of the `Secure` flag.
3. IF `delete_cookie` is called with no SameSite policy (the default) and the
   cookie key does not begin with `__Secure-` or `__Host-`, THEN the response's
   cookie SHALL NOT be marked `Secure` (its `secure` attribute SHALL be the
   empty/unset value).

## Requirement 3: Preserve existing deletion behavior (regression protection)

**User story:** As a maintainer, I want the established deletion semantics to be
unchanged for callers that do not specify a SameSite policy, so that existing
behavior and security prefixes keep working.

**Acceptance criteria**

1. WHEN `delete_cookie` is called without a SameSite policy, THEN the response's
   cookie for that key SHALL have an empty `samesite` attribute.
2. WHEN `delete_cookie` is called for a key beginning with `__Secure-` or
   `__Host-`, THEN the response's cookie SHALL have its `secure` flag set to
   `True`, regardless of the SameSite policy.
3. The `delete_cookie` method SHALL continue to expire the cookie by setting its
   `max-age` to `0` and its `expires` value to the fixed epoch timestamp
   `Thu, 01 Jan 1970 00:00:00 GMT`.
4. The `delete_cookie` method SHALL continue to honor the supplied path
   (defaulting to `/`) and the supplied domain on the resulting cookie.
5. The `set_cookie` routine SHALL continue to reject a SameSite value that is
   not one of `lax`, `none`, or `strict` by raising `ValueError`, and SHALL
   continue to accept those three values.

## Requirement 4: Session cookie deletion propagates the configured SameSite

**User story:** As a site operator, I want the session cookie's deletion to
carry my configured SameSite policy, so that ending a session reliably clears
the cookie in modern browsers.

**Acceptance criteria**

1. WHEN the session middleware deletes the session cookie because the session is
   empty, THEN it SHALL request deletion with the SameSite policy taken from the
   `SESSION_COOKIE_SAMESITE` setting.
2. WHEN the session cookie is deleted, THEN the emitted `Set-Cookie` header for
   the session cookie SHALL include a `SameSite` attribute equal to the
   configured `SESSION_COOKIE_SAMESITE` value.
3. The session middleware SHALL continue to delete the session cookie using the
   configured session cookie path (`SESSION_COOKIE_PATH`) and domain
   (`SESSION_COOKIE_DOMAIN`), including when these are customized.

## Requirement 5: Messages cookie deletion propagates the configured SameSite

**User story:** As a developer using the cookie-based messages storage, I want
the messages cookie deletion to carry the configured SameSite policy, so that
clearing messages does not emit a header that browsers reject.

**Acceptance criteria**

1. WHEN the cookie-based messages storage deletes its cookie because there is no
   message data to store, THEN it SHALL request deletion with the SameSite
   policy taken from the `SESSION_COOKIE_SAMESITE` setting.
2. WHEN the messages cookie is deleted, THEN the response's cookie for the
   messages key SHALL carry a `samesite` attribute equal to the configured
   `SESSION_COOKIE_SAMESITE` value.
3. The messages storage SHALL continue to delete its cookie using the configured
   `SESSION_COOKIE_DOMAIN`, and the deleted cookie SHALL continue to carry the
   fixed epoch `expires` value used to expire cookies.
