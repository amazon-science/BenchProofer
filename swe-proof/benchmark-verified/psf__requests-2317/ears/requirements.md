# Requirements: Normalize the HTTP request method regardless of its incoming string form

## Introduction

When a caller issues a request through a `requests.sessions.Session` (via
`Session.request`, and the `get`/`post`/`head`/etc. convenience wrappers that
delegate to it), the HTTP method token (`"GET"`, `"POST"`, …) is supplied by
the caller. Some callers encode all of their arguments to bytes before handing
them over, so the method can arrive as a raw byte token (e.g. the bytes for
`GET`) rather than ordinary text.

Before the request is assembled and dispatched, the method is coerced to the
platform's native string type. The defect being addressed is that this coercion
turned a byte token into a *printable description of the byte object* — on
Python 3 the byte token for `GET` became the six-character literal
`b'GET'` instead of the three characters `GET`. The corrupted method was then
sent on the wire, and the server answered `404 Not Found` because no such method
exists. On Python 2 the same code happened to behave correctly, so the fault was
Python-3-specific.

The affected code is the method-coercion step inside `Session.request` in
`requests/sessions.py`, together with the subsequent upper-casing performed by
`PreparedRequest.prepare_method` in `requests/models.py`. The goal: whatever the
incoming form of the method, the method finally stored on and sent with the
request must carry the **textual content** of the supplied token, upper-cased —
so a byte token and the equivalent text token are indistinguishable downstream.

## Requirement 1: Recover the textual content of a byte-encoded method

**User story:** As a developer whose HTTP client stack encodes call arguments to
bytes, I want a method passed as a byte token to be treated as the equivalent
text token, so that my requests reach the intended resource instead of failing.

**Acceptance criteria**

1. WHEN `Session.request` is called with a method supplied as a byte token,
   THEN the system SHALL coerce the method to the platform's native string type
   by decoding the token's bytes to their corresponding text characters.
2. WHEN a method is supplied as a byte token, THEN the coerced method SHALL
   consist solely of the characters carried by those bytes, with no added
   quoting, prefix, or other characters drawn from a printable description of
   the byte object.
3. IF a method is supplied as the byte token whose bytes spell a method name,
   THEN the coerced method SHALL equal the same characters as if the caller had
   supplied that name as ordinary text.
4. The system SHALL perform this coercion for ASCII method tokens without
   raising an error.

## Requirement 2: Upper-case the normalized method

**User story:** As an API user, I want method names canonicalized to upper case,
so that case-insensitive HTTP methods behave consistently regardless of how I
spelled them.

**Acceptance criteria**

1. WHEN a request is prepared with a non-empty method, THEN the method stored on
   the prepared request SHALL be the upper-cased form of the coerced textual
   method.
2. WHEN the coerced method contains lower-case letters (including a method that
   arrived as a byte token spelling a lower-case name), THEN the stored method
   SHALL have those letters upper-cased.
3. IF the supplied method is absent (`None`), THEN the system SHALL leave the
   prepared method unset rather than attempting to coerce or upper-case it.

## Requirement 3: Preserve behavior for methods supplied as ordinary text

**User story:** As an existing user who passes method names as normal strings, I
want requests to keep working exactly as before, so that this fix introduces no
regression.

**Acceptance criteria**

1. WHEN a method is supplied as a native text string, THEN the coerced method
   SHALL retain the same characters unchanged (aside from the upper-casing of
   Requirement 2).
2. The system SHALL keep issuing successful requests for the standard HTTP
   methods (GET, POST, HEAD, PUT, and redirect-following GET flows) supplied as
   text.
3. WHEN a request supplied with a text method is redirected, retried, or has its
   history recorded, THEN each resulting request SHALL carry the correctly
   normalized method.
4. The system SHALL continue to accept methods supplied as unicode text and
   store them as native strings.
