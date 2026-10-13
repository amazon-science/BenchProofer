# Requirements: Punycode-encode non-ASCII host/domain names used in email metadata and validation

## Introduction

Django stamps the local machine's host name into outgoing email metadata — most
visibly the auto-generated `Message-ID` header, which is built in
`EmailMessage.message` (`django/core/mail/message.py`) as
`make_msgid(domain=DNS_NAME)`. `DNS_NAME` is a cached lazy object,
`CachedDnsName` in `django/core/mail/utils.py`, whose `get_fqdn` method returns
the name reported by `socket.getfqdn()`.

When the operating system reports a host name that contains non-ASCII
characters (for example a machine named in a non-Latin script), that raw name
flows unchanged into the `Message-ID` header. Header serialization encodes all
headers to the message's declared encoding; when that encoding is a narrow
single-byte charset (such as `iso-8859-1`), a non-ASCII host name cannot be
represented and message construction raises `UnicodeEncodeError` instead of
producing a message. Email construction therefore crashes purely because of the
machine's host name.

The remedy is to convert the host name to its ASCII-compatible (Punycode / IDNA
ACE) representation before it is used as email metadata, so the name placed in
headers is always pure ASCII and safe under any header encoding. The same
non-ASCII-domain-to-Punycode conversion is already performed inline in several
other places (email address sanitization, URL and email-address validation, and
URL linkification); this work also consolidates that conversion behind a single
shared helper, `punycode`, added to `django/utils/encoding.py`, without changing
those callers' observable behavior.

The affected modules are `django/core/mail/utils.py`,
`django/core/mail/message.py`, `django/utils/encoding.py`,
`django/core/validators.py`, and `django/utils/html.py`.

## Requirement 1: Host name used for mail metadata is ASCII-compatible

**User story:** As someone sending email from a machine whose host name
contains non-ASCII characters, I want the host name embedded in message
metadata to be its ASCII-compatible form, so that message construction never
crashes over the host name regardless of the message's declared encoding.

**Acceptance criteria**

1. WHEN `CachedDnsName.get_fqdn` computes the fully-qualified host name from the
   value reported by `socket.getfqdn()`, THEN it SHALL return the
   ASCII-compatible (Punycode/IDNA ACE) representation of that reported name
   rather than the raw reported name.
2. WHEN the reported host name is already entirely ASCII, THEN `get_fqdn` SHALL
   return a value equal to the standard IDNA ACE encoding of that name (which,
   for a plain-ASCII name, leaves its label content unchanged).
3. WHEN the reported host name contains non-ASCII characters, THEN the value
   returned by `get_fqdn` SHALL consist solely of ASCII characters (the
   Punycode form, whose non-ASCII labels are represented with the `xn--`
   prefix).
4. The system SHALL continue to compute this host name lazily and cache it, so
   that the reported name is resolved and encoded at most once and reused on
   subsequent accesses.

## Requirement 2: Email `Message-ID` is generated safely for non-ASCII host names under any encoding

**User story:** As a developer building an `EmailMessage` on a host with a
non-ASCII name, I want to set a non-unicode message encoding and still obtain a
valid message, so that a Unicode host name does not make email construction
fail.

**Acceptance criteria**

1. WHEN an `EmailMessage` is converted to a MIME message (`EmailMessage.message`)
   and no explicit `Message-ID` header was supplied, THEN the system SHALL
   generate a `Message-ID` header whose domain component is the
   ASCII-compatible host name derived in Requirement 1.
2. IF the host name reported by the operating system contains non-ASCII
   characters AND the message's encoding is a non-unicode single-byte charset
   (such as `iso-8859-1`), THEN converting the `EmailMessage` to a message
   SHALL succeed without raising `UnicodeEncodeError`, and the generated
   `Message-ID` header SHALL contain the ASCII Punycode form of the host name
   (a label carrying the `xn--` prefix) rather than the raw non-ASCII name.
3. WHEN a message is constructed on a host whose name is plain ASCII, THEN the
   generated `Message-ID` header SHALL be identical to what was produced before
   this change (no observable difference for ASCII host names).

## Requirement 3: Preserve non-ASCII domain handling in address sanitization (regression protection)

**User story:** As a maintainer, I want email address sanitization to keep
converting non-ASCII domains to their ASCII form, so that internationalized
recipient and sender addresses are handled exactly as before.

**Acceptance criteria**

1. WHEN `sanitize_address` processes an address whose domain part contains
   non-ASCII characters, THEN it SHALL replace that domain part with its
   ASCII-compatible (Punycode/IDNA ACE) representation before assembling the
   address.
2. WHEN `sanitize_address` processes an address whose domain part is already
   ASCII, THEN it SHALL leave the domain part unchanged.
3. The system SHALL keep encoding a non-ASCII local part of an address via the
   message's header encoding, independently of the domain handling.

## Requirement 4: Preserve IDNA handling in URL and email validation (regression protection)

**User story:** As a maintainer, I want URL and email-address validators to keep
accepting internationalized domain names by converting them to ASCII form, so
that validation behavior is unchanged.

**Acceptance criteria**

1. WHEN `URLValidator` validates a URL whose network location (host) contains
   non-ASCII characters, THEN it SHALL convert that host to its ASCII-compatible
   (Punycode/IDNA ACE) form and validate the URL using that converted host.
2. IF converting the URL host to its ASCII-compatible form fails because the
   host is not a valid domain, THEN `URLValidator` SHALL raise the same
   validation error it would otherwise raise for an invalid URL.
3. WHEN `EmailValidator` checks an email address whose domain part is not
   accepted as-is and contains non-ASCII characters, THEN it SHALL attempt to
   convert the domain part to its ASCII-compatible form and, on success,
   validate the address against that converted domain; IF that conversion
   fails, THEN it SHALL fall back to its prior handling and reject the address
   as invalid.

## Requirement 5: Preserve IDNA handling in URL linkification (regression protection)

**User story:** As a maintainer, I want the text-to-HTML URL linkifier to keep
converting non-ASCII domains to ASCII form, so that produced links are
unchanged.

**Acceptance criteria**

1. WHEN `urlize` builds a link from a URL whose network location contains
   non-ASCII characters, THEN it SHALL convert that host to its ASCII-compatible
   (Punycode/IDNA ACE) form for the emitted link; IF that conversion fails
   because the host is not a valid domain, THEN it SHALL leave the URL
   unmodified (unquoted/quoted as before) rather than raise.
2. WHEN `urlize` autolinks a bare email address whose domain contains non-ASCII
   characters, THEN it SHALL convert the domain to its ASCII-compatible form for
   the generated `mailto:` link; IF that conversion fails, THEN it SHALL skip
   linkifying that candidate rather than raise.

## Requirement 6: Single shared Punycode helper with unchanged semantics

**User story:** As a maintainer, I want one shared helper that performs the
non-ASCII-domain-to-Punycode conversion, so that the several call sites share
identical, well-defined behavior.

**Acceptance criteria**

1. The system SHALL provide, in `django/utils/encoding.py`, a reusable helper
   named `punycode` that returns the ASCII-compatible (IDNA ACE) representation
   of a given host/domain name.
2. WHEN `punycode` is applied to any domain, THEN its result SHALL equal the
   result of the standard IDNA ACE encoding of that domain, so that every call
   site that previously performed this encoding inline continues to produce the
   same value.
3. The mail host-name resolution, address sanitization, URL/email validation,
   and URL linkification SHALL all use this shared helper to perform the
   conversion, and the conversion result at each site SHALL be identical to the
   previously inlined encoding.
