# Requirements: Normalize the request method name so unicode method arguments do not corrupt requests

## Introduction

The HTTP library's high-level request dispatch (`Session.request` in
`requests/sessions.py`, the entry point used by `requests.request` and the
verb helpers) accepts the HTTP method as a text argument (for example
`"POST"`). The method name is canonicalized to upper case and then stored on
the `Request`/`PreparedRequest` that is built and sent.

On interpreters that distinguish a "native" text string from a "wide"/unicode
text string (notably Python 2.7), a caller may legitimately supply the method
as a wide/unicode literal (for example `u'POST'`). In that case the stored
method stays a wide string. When the request is later assembled, that wide
method name forces the request line and headers to be treated as wide text; if
the request also carries a non-ASCII (binary) body — such as an uploaded file —
combining the wide text with the byte body raises a decoding error
(`UnicodeDecodeError`) and the request fails, even though the method itself is
plain ASCII.

The goal is to normalize the supplied method name into a native text string of
the correct case *before* the request is built, so that the request succeeds
regardless of the string type used to pass the method, while preserving all
existing method-handling behavior.

## Requirement 1: Coerce the supplied method name to a native string

**User story:** As a developer calling the library with a unicode method name,
I want the library to normalize the method type internally, so that my request
is sent successfully instead of failing with a decoding error.

**Acceptance criteria**

1. WHEN `Session.request` is invoked with a `method` argument, THEN the system
   SHALL normalize that method into a native text string before constructing
   the `Request` object.
2. WHEN the supplied `method` is a wide/unicode text string whose characters
   are all ASCII (for example `u'POST'`), THEN the method stored on the built
   request SHALL be a native text string carrying the same characters, not a
   wide/unicode string.
3. WHEN the supplied `method` is already a native text string, THEN the
   normalization SHALL leave its character content unchanged.
4. The system SHALL perform this normalization for every value of `method`,
   independent of the string type used by the caller.

## Requirement 2: Canonicalize the method to upper case

**User story:** As a developer, I want method names canonicalized to upper
case, so that HTTP method tokens are transmitted in their conventional form
regardless of the case I pass.

**Acceptance criteria**

1. WHEN `Session.request` builds the request, THEN the method stored on that
   request SHALL be the upper-cased form of the supplied method name.
2. WHEN the supplied method is given in lower or mixed case (for example
   `"post"` or `u'Post'`), THEN the stored method SHALL be the upper-cased
   equivalent (for example `POST`).
3. The system SHALL apply the upper-casing to the native-string form of the
   method, so the stored method is simultaneously native-typed and
   upper-cased.

## Requirement 3: Preserve successful dispatch for requests with binary bodies

**User story:** As a developer uploading a file with a unicode method name, I
want the request to complete successfully, so that a mixed unicode-method /
binary-body request behaves the same as one made with a native method name.

**Acceptance criteria**

1. WHEN a request is issued with a unicode method name together with a payload
   that includes binary/file content, THEN the system SHALL assemble and send
   the request without raising a decoding error.
2. IF the same request would succeed when the method is supplied as a native
   string, THEN it SHALL likewise succeed when the method is supplied as a
   wide/unicode string carrying the same ASCII characters.
3. The system SHALL keep unchanged all remaining request-building and
   sending behavior — construction of the `Request`, preparation into a
   `PreparedRequest`, cookie/header/redirect/authentication handling — so that
   requests using ordinary native-string methods (GET, POST, PUT, HEAD, and
   redirected or authenticated requests) continue to behave exactly as before.
