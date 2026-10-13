# Requirements: Reject hosts with an empty leading label during URL preparation

## Introduction

When the `requests` library prepares an HTTP(S) URL for sending, it parses the
URL and validates the host component before reconstructing the network
location. This work happens in `PreparedRequest.prepare_url` in
`requests/models.py`, which parses the URL, checks that a scheme and host are
present, and then validates/normalizes the host.

An all-ASCII host that begins with a leading dot (for example `.example.com`)
denotes an empty leading label. Historically such a host was not caught by the
host-validation branch and instead surfaced as a low-level `UnicodeError`
("encoding with 'idna' codec failed: label empty or too long"), leaking an
implementation-level exception to the caller. The intended behavior — matching
how a leading wildcard (`*`) is already handled — is to reject such hosts with
the library's own `InvalidURL` exception carrying the message
`URL has an invalid label.`

The goal is to make host validation reject an all-ASCII host that begins with a
reserved leading character — either a wildcard marker (`*`) or a dot (`.`)
introducing an empty leading label — with `InvalidURL`, while preserving all
existing URL-preparation behavior for every other input.

## Requirement 1: Reject an ASCII host beginning with an empty leading label

**User story:** As a user of `requests`, I want `http://.example.com` to be
rejected with a clear `InvalidURL` error, so that a malformed host does not
leak a low-level encoding exception.

**Acceptance criteria**

1. WHEN `PreparedRequest.prepare_url` prepares an HTTP(S) URL whose parsed host
   consists solely of ASCII code points and begins with a dot (`.`), THEN
   `prepare_url` SHALL raise `requests.exceptions.InvalidURL`.
2. WHEN such a host is rejected for beginning with a dot, THEN the raised
   `InvalidURL` SHALL carry the message text `URL has an invalid label.`
3. WHEN `prepare_url` prepares an HTTP(S) URL whose parsed host is all-ASCII and
   begins with a dot, THEN `prepare_url` SHALL NOT allow a `UnicodeError` (or
   any other non-`requests` exception) to propagate to the caller in place of
   `InvalidURL`.

## Requirement 2: Continue rejecting an ASCII host beginning with a wildcard

**User story:** As a user of `requests`, I want a host beginning with a wildcard
marker to keep being rejected, so that the existing guard is not weakened by the
new one.

**Acceptance criteria**

1. WHEN `prepare_url` prepares an HTTP(S) URL whose parsed host is all-ASCII and
   begins with a wildcard marker (`*`), THEN `prepare_url` SHALL raise
   `requests.exceptions.InvalidURL` with the message text
   `URL has an invalid label.`
2. The system SHALL apply the leading-character rejection to an all-ASCII host
   whenever its first character is either a wildcard marker (`*`) or a dot
   (`.`), and SHALL NOT reject an all-ASCII host solely because it begins with
   any other character.

## Requirement 3: Preserve preparation of valid and other-invalid URLs

**User story:** As a user of `requests`, I want every other URL to be prepared
or rejected exactly as before, so that adding the new guard changes no unrelated
behavior.

**Acceptance criteria**

1. WHEN `prepare_url` prepares an HTTP(S) URL whose all-ASCII host does not begin
   with a wildcard marker (`*`) or a dot (`.`), THEN `prepare_url` SHALL accept
   the host unchanged and complete preparation without raising `InvalidURL` for
   the leading-character reason.
2. WHEN `prepare_url` prepares an HTTP(S) URL whose host contains one or more
   non-ASCII code points, THEN `prepare_url` SHALL delegate the host to the
   internationalized-domain-name (IDNA) encoder and SHALL raise `InvalidURL`
   with the message `URL has an invalid label.` if and only if that encoder
   rejects the name; the leading-character guard SHALL NOT be applied to a
   non-ASCII host.
3. WHEN `prepare_url` is given a URL with no host component (for example
   `http://`), THEN `prepare_url` SHALL raise `InvalidURL` reporting that no
   host was supplied, independently of the leading-character guard.
4. WHEN `prepare_url` is given a string with a non-HTTP scheme (for example
   `mailto:` or `data:`), THEN `prepare_url` SHALL leave that URL unchanged and
   SHALL NOT apply host validation to it.
5. WHEN `prepare_url` is given a string with no scheme, THEN `prepare_url` SHALL
   raise `MissingSchema`; and WHEN given a string whose scheme is unsupported
   for connection, the surrounding request machinery SHALL raise
   `InvalidSchema`, unchanged by this requirement.
6. The system SHALL preserve, unchanged, all existing successful
   URL-preparation behavior — including IDNA encoding of non-ASCII hosts,
   percent-encoding and path normalization, query-parameter appending before any
   fragment, preservation of parameter order, and handling of IPv6 literal
   hosts and non-standard schemes.
