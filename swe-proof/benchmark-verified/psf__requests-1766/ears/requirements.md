# Requirements: Quote the quality-of-protection value in Digest Auth headers

## Introduction

`requests.auth.HTTPDigestAuth` attaches HTTP Digest authentication to an
outgoing request. Its `build_digest_header(method, url)` method assembles the
value of the `Authorization` header: the literal prefix `Digest ` followed by a
comma-separated list of directives (`username`, `realm`, `nonce`, `uri`,
`response`, and — depending on the server challenge — `opaque`, `algorithm`,
`digest`, and the quality-of-protection group `qop`, `nc`, `cnonce`).

Per RFC 2617, the `qop-options` (quality-of-protection) directive is a
*quoted string*: its value must be wrapped in double quotes (e.g. `qop="auth"`).
The current implementation emits the value as a bare token (`qop=auth`). Some
server-side implementations are sensitive to this difference and reject the
unquoted form, and reference tools such as `curl` emit the quoted form. The goal
is to make `build_digest_header` emit the quality-of-protection directive's value
as a double-quoted string, while leaving every other directive of the assembled
header — its presence, ordering, and quoting — exactly as before.

The affected module is `requests/auth.py`; the behavior is observed on the
`Authorization` request header produced for Digest authentication.

## Requirement 1: Quote the quality-of-protection directive value

**User story:** As a user authenticating against a Digest-auth server, I want the
quality-of-protection directive to be sent as a double-quoted string, so that
RFC 2617-conformant servers that reject the bare-token form accept my request.

**Acceptance criteria**

1. WHEN `build_digest_header` assembles an `Authorization` value and a
   quality-of-protection value is in effect (the server challenge supplied a
   `qop` value), THEN the system SHALL emit the quality-of-protection directive
   with its value enclosed in double quotes, i.e. as `qop="auth"` rather than
   `qop=auth`.
2. WHEN a Digest request is sent to a server that challenges with a `qop` value,
   THEN the resulting `Authorization` header SHALL contain the substring
   `"auth"` (the double-quoted quality-of-protection value).
3. The system SHALL emit only the `qop`, `nc`, and `cnonce` directives (in that
   order) as the quality-of-protection group, and SHALL continue to omit this
   entire group when no quality-of-protection value is in effect.

## Requirement 2: Preserve all other directive formatting and behavior

**User story:** As a maintainer, I want every other part of the Digest
`Authorization` header to stay byte-for-byte as before, so that quoting the
quality-of-protection value introduces no regression in Digest authentication.

**Acceptance criteria**

1. The system SHALL emit the assembled header value as the literal prefix
   `Digest ` followed by the directive list.
2. The system SHALL emit the mandatory directives `username`, `realm`, `nonce`,
   `uri`, and `response` in that order, each with its value enclosed in double
   quotes.
3. WHEN the server challenge supplies an `opaque` value, THEN the system SHALL
   append an `opaque` directive with its value in double quotes; otherwise the
   directive SHALL be omitted.
4. WHEN the server challenge supplies an `algorithm` value, THEN the system SHALL
   append an `algorithm` directive with its value in double quotes; otherwise the
   directive SHALL be omitted.
5. WHEN a message-digest (entity-digest) value is in effect, THEN the system
   SHALL append a `digest` directive with its value in double quotes; otherwise
   the directive SHALL be omitted.
6. The system SHALL emit the nonce-count (`nc`) value as a bare token (not
   double-quoted) and the client-nonce (`cnonce`) value as a double-quoted
   string.
7. The system SHALL leave the computation of the response digest, client nonce,
   nonce count, and request URI unchanged, so that only the quoting of the
   quality-of-protection value differs from prior behavior.

## Requirement 3: The change is confined to quality-of-protection quoting

**User story:** As a user of the requests library, I want this fix to change
only the quoting of the quality-of-protection value and nothing else, so that
Digest authentication and all other request/response behavior keep working
exactly as before.

**Acceptance criteria**

1. The system SHALL continue to perform the Digest 401 challenge/response flow:
   on receiving a `401` response advertising Digest, it SHALL re-send the request
   with a computed `Authorization` header, and otherwise SHALL return the
   response unchanged.
2. WHEN the quality-of-protection directive value is double-quoted per
   Requirement 1, THEN the system SHALL leave every other observable aspect of
   request construction and response handling unchanged from prior behavior; the
   sole difference from the pre-change behavior SHALL be the quoting of the
   quality-of-protection value.
