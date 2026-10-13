# Requirements: Do not send a Content-Length header on bodiless GET/HEAD requests

## Introduction

When the HTTP client library prepares a request, it computes and attaches a
`Content-Length` header. The affected logic lives in the request-preparation
path of `requests/models.py`, specifically the `prepare_content_length` method
of the prepared-request class (invoked from `prepare_body`, and again from
`prepare_auth` after auth mutates the body).

The current behavior unconditionally sets `Content-Length` to `"0"` before
inspecting the body, so even a `GET` or `HEAD` request that carries no body is
emitted with `Content-Length: 0`. Some servers reject any `GET` request that
includes a `Content-Length` header (returning an error status), so a bodiless
`GET`/`HEAD` should not carry the header at all.

The goal: a prepared `GET` or `HEAD` request with no body must not include a
`Content-Length` header, while every request that actually has a body must
continue to report the correct byte length, and other bodiless methods must
continue to report `Content-Length: 0`.

## Requirement 1: Omit Content-Length for bodiless GET and HEAD requests

**User story:** As a developer issuing `GET`/`HEAD` requests, I want no
`Content-Length` header attached when there is no body, so that servers which
reject `GET` requests bearing a `Content-Length` header respond normally.

**Acceptance criteria**
1. WHEN a `GET` request is prepared with no request body, THEN the prepared
   request's headers SHALL NOT contain a `Content-Length` header.
2. WHEN a `HEAD` request is prepared with no request body, THEN the prepared
   request's headers SHALL NOT contain a `Content-Length` header.
3. The system SHALL determine whether to add the fallback `Content-Length`
   header based on the request method, treating `GET` and `HEAD` as the methods
   for which a bodiless request carries no `Content-Length` header.

## Requirement 2: Preserve Content-Length for requests that have a body

**User story:** As a developer sending request payloads, I want the correct
`Content-Length` to be reported, so that servers receive well-formed requests.

**Acceptance criteria**
1. WHEN a request is prepared with a body that supports seek/tell (a file-like
   object), THEN the prepared request SHALL set `Content-Length` to the byte
   length of that body, and SHALL leave the body positioned at its start.
2. WHEN a request is prepared with a non-empty in-memory body (for example a
   form-encoded or string body), THEN the prepared request SHALL set
   `Content-Length` to the length of that body.
3. IF authentication handling recomputes the request body, THEN the prepared
   request SHALL recompute `Content-Length` consistently with criteria 1 and 2.

## Requirement 3: Preserve Content-Length: 0 for other bodiless methods

**User story:** As a developer sending bodiless requests with methods other
than `GET`/`HEAD`, I want a `Content-Length: 0` header to remain, so that
existing well-behaved request framing is unchanged.

**Acceptance criteria**
1. IF a request has no body and its method is neither `GET` nor `HEAD`, THEN the
   prepared request SHALL set `Content-Length` to `"0"`.

## Requirement 4: Confine the change to the Content-Length decision

**User story:** As a maintainer, I want this change to affect only whether the
`Content-Length` header is attached, so that the rest of request preparation is
untouched.

**Acceptance criteria**
1. WHEN a request whose method is `GET` or `HEAD` is prepared WITH a body, THEN
   the prepared request SHALL still report a `Content-Length` header, because the
   omission applies only to the bodiless case rather than to the method as a
   whole.
2. The system SHALL leave all request-preparation behavior other than the
   `Content-Length` header decision unchanged by this change.
