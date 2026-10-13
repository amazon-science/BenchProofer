# Requirements: Omit the response body for HEAD requests in the development server

## Introduction

Django's development server (`runserver`/`testserver`) serves WSGI responses
through a custom handler in `django/core/servers/basehttp.py`. The
`ServerHandler` class there subclasses the standard library
`wsgiref.handlers` handler and customises header cleanup and (as of this change)
response finalisation; the accompanying `WSGIRequestHandler` runs each request.

A HEAD request asks a server for exactly the response metadata (status line and
headers) that a GET for the same resource would produce, but with the entity
body omitted. Historically Django stripped HEAD response bodies itself; that
stripping was later removed on the assumption that the fronting web server
(gunicorn, mod_wsgi, etc.) would do it. The development server performs no such
stripping, so `runserver` returns the full body for HEAD requests. This violates
the HTTP requirement that a HEAD response carry no body, and — because a
compliant client terminates the connection once it has read the headers — it
can also produce spurious "Broken pipe" errors in the server output.

The goal is to make the development server's responses to HEAD requests
compliant: the entity body must not be written, the body-length header must be
omitted, and the connection must not be needlessly marked as non-reusable —
while
the existing behaviour for ordinary (non-HEAD) requests, the
connection-persistence policy, HTTPS-over-HTTP detection, underscore-header
filtering, and broken-pipe handling are all preserved.

Throughout this document, a "HEAD request" is one whose request method
(`environ["REQUEST_METHOD"]`) is `"HEAD"`; an "ordinary request" is any request
whose method is not `"HEAD"` (e.g. GET).

## Requirement 1: Omit the entity body from HEAD responses

**User story:** As an operator using the development server, I want HEAD
responses to contain no entity body, so that my responses comply with the HTTP
specification and compliant clients do not trigger broken-pipe errors.

**Acceptance criteria**

1. WHEN the development server finalises the response to a HEAD request, THEN the
   handler SHALL write no entity-body bytes to the output stream (the bytes
   following the header block SHALL be empty apart from the blank line that
   terminates the headers).
2. WHEN the development server finalises the response to a HEAD request, THEN the
   handler SHALL fully consume the iterable of body data returned by the WSGI
   application (so that any application-side generation and cleanup still runs),
   without writing that data to the output stream.
3. WHEN the development server finalises the response to a HEAD request AND the
   response headers have not yet been written to the output stream, THEN the
   handler SHALL emit the response headers so that the client still receives the
   status line and header block.
4. WHEN the development server finalises the response to a HEAD request, THEN the
   handler SHALL complete the standard end-of-response cleanup (finalising the
   request) regardless of whether writing or consuming the body raised an error.

## Requirement 2: Preserve full body emission for ordinary requests

**User story:** As an operator using the development server, I want ordinary
(non-HEAD) requests to keep returning their complete response body, so that this
change does not regress normal request handling.

**Acceptance criteria**

1. WHEN the development server finalises the response to an ordinary (non-HEAD)
   request, THEN the handler SHALL write the response headers followed by the
   complete entity body exactly as the standard WSGI response finaliser would.
2. The system SHALL NOT alter the emitted entity body of an ordinary (non-HEAD)
   response as a result of this change.

## Requirement 3: Omit the body-length header for HEAD responses

**User story:** As a client issuing a HEAD request, I want the response not to
advertise a body length that will never be sent, so that the metadata is
consistent with the omitted body.

**Acceptance criteria**

1. WHEN the handler cleans up the response headers for a HEAD request AND a
   body-length header (`Content-Length`) is present after the base handler's
   header preparation, THEN the handler SHALL remove that `Content-Length`
   header so that no such header appears in the HEAD response.
2. IF the request is a HEAD request, THEN the HEAD response SHALL NOT contain a
   `Content-Length` header, regardless of any length computed by the base
   handler.
3. The system SHALL leave the `Content-Length` header of an ordinary (non-HEAD)
   response unchanged; WHEN an ordinary response's body length is known, THEN its
   `Content-Length` header SHALL be present in the emitted headers.

## Requirement 4: Preserve the connection-persistence policy without over-restricting HEAD responses

**User story:** As a client, I want the connection to be marked as
non-reusable only when reuse would be ambiguous or explicitly disallowed, so
that HEAD responses are not needlessly restricted while genuinely non-reusable
connections still are.

For the purposes of this requirement, the "non-reuse connection signal" is the
`Connection` response header set to the standard value that instructs the
client not to reuse the connection.

**Acceptance criteria**

1. WHEN the handler cleans up the response headers for an ordinary (non-HEAD)
   request AND no `Content-Length` header is present, THEN the handler SHALL
   assert the non-reuse connection signal on the response.
2. IF the request is a HEAD request whose response has no `Content-Length`
   header, THEN the handler SHALL NOT assert the non-reuse connection signal on
   the basis of the missing length alone.
3. WHEN a `Content-Length` header is present AND the response is served by a
   server that handles only one request at a time (a non-threading server), THEN
   the handler SHALL assert the non-reuse connection signal.
4. WHEN the response is served by a server that can handle multiple requests
   concurrently (a threading server) AND the connection is not otherwise marked
   as non-reusable, THEN the handler SHALL NOT assert the non-reuse connection
   signal.
5. WHEN the non-reuse connection signal is asserted (whether set by the handler
   or already requested by the application), THEN the handler SHALL mark the
   underlying connection to be terminated after the response.

## Requirement 5: Preserve unrelated request-handler behaviours

**User story:** As a Django maintainer, I want existing development-server
behaviours to remain intact, so that fixing HEAD handling introduces no
regressions.

**Acceptance criteria**

1. The system SHALL continue to exclude request headers whose names contain
   underscores from the WSGI environment passed to the application.
2. WHEN a plaintext HTTP handler receives what appears to be a TLS/SSL handshake
   (a client attempting HTTPS against the HTTP-only development server), THEN the
   handler SHALL log an error explaining that the development server supports
   only HTTP.
3. WHEN writing a response raises a broken-pipe/connection-abort error, THEN the
   server SHALL handle it gracefully rather than propagating an unhandled
   exception.
4. The system SHALL continue to record a server log entry for each handled
   request.
