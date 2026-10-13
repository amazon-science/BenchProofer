# Requirements: Reject invalid characters in URL username/password

## Introduction

`django.core.validators.URLValidator` (in `django/core/validators.py`) validates
URL strings by matching them against a regular expression. A URL authority may
optionally carry credentials — a *user* part, optionally followed by a `:` and a
*password* part — that precede an `@` sign, e.g. `http://user:pass@example.com`.

Per RFC 1738 §3.1, within the user and password fields the characters `":"`,
`"@"`, and `"/"` (and, in general, whitespace) must be percent-encoded and must
never appear literally. The current credentials sub-pattern of the validator's
regex accepts any run of non-whitespace characters before the `@`, so it lets
these reserved delimiters through un-encoded. This causes genuinely invalid URLs
to pass validation — for example `http://foo/bar@example.com`, and any otherwise
invalid URL with a trailing `?m=foo@example.com`-style query appended.

The goal is to make `URLValidator` reject URLs whose credentials (userinfo)
segment contains a literal reserved delimiter or whitespace, while continuing to
accept all URLs that were legitimately valid before — including URLs with
correctly-formed credentials, URLs with no credentials at all, and URLs where
those characters appear in other components (path, query, fragment).

The affected behavior is entirely in `URLValidator` and is exercised through its
`__call__` (a `ValidationError` is raised for invalid input, and validation
succeeds silently for valid input).

## Requirement 1: Reject reserved delimiters in the credentials segment

**User story:** As a developer validating user-supplied URLs, I want URLs whose
username or password contains an un-encoded `:`, `@`, or `/` to be rejected, so
that malformed or ambiguous authorities cannot pass validation.

**Acceptance criteria**

1. WHEN `URLValidator` is called with a URL whose authority contains a
   credentials segment (text preceding an `@` in the authority) and that segment
   contains a literal `/`, THEN `URLValidator` SHALL treat the URL as invalid and
   raise a `ValidationError`.
2. WHEN `URLValidator` is called with a URL whose credentials segment contains
   more than one literal `:`, THEN `URLValidator` SHALL treat the URL as invalid
   and raise a `ValidationError`.
3. WHEN `URLValidator` is called with a URL whose authority contains more than
   one `@` such that a reserved `@` would fall inside the credentials segment
   (e.g. a user or password part containing a literal `@`), THEN `URLValidator`
   SHALL treat the URL as invalid and raise a `ValidationError`.
4. IF the credentials segment is empty or begins with a `:` (i.e. the user part
   is absent), THEN `URLValidator` SHALL treat the URL as invalid and raise a
   `ValidationError`.
5. WHEN `URLValidator` is called with a URL whose credentials segment contains a
   whitespace character, THEN `URLValidator` SHALL treat the URL as invalid and
   raise a `ValidationError`.
6. The only characters `URLValidator` SHALL admit inside the user part and the
   password part of a credentials segment are characters that are neither
   whitespace nor any of `":"`, `"@"`, `"/"`; a single `:` separating the user
   part from the password part is the sole permitted occurrence of `:`.

## Requirement 2: Accept well-formed credentials and credential-less URLs

**User story:** As a developer, I want URLs with correctly-formed credentials and
URLs without credentials to keep validating successfully, so that the stricter
rule does not reject legitimate URLs.

**Acceptance criteria**

1. WHEN `URLValidator` is called with an otherwise-valid URL that has no
   credentials segment before the host, THEN `URLValidator` SHALL accept the URL
   (no `ValidationError` raised).
2. WHEN `URLValidator` is called with an otherwise-valid URL whose credentials
   segment consists only of a non-empty user part built from admissible
   characters (no whitespace and none of `":"`, `"@"`, `"/"`), THEN
   `URLValidator` SHALL accept the URL.
3. WHEN `URLValidator` is called with an otherwise-valid URL whose credentials
   segment is a non-empty user part followed by a single `:` and a password part
   (possibly empty) built only from admissible characters, THEN `URLValidator`
   SHALL accept the URL.
4. The system SHALL continue to accept credentials in which the reserved
   characters appear only in percent-encoded form (e.g. `%40`, `%2f`), since a
   percent-encoded sequence contains no literal reserved delimiter.

## Requirement 3: Preserve validation of all other URL components

**User story:** As a developer, I want the stricter credentials rule to affect
only the credentials segment, so that valid hosts, ports, paths, queries, and
fragments — including ones that legitimately contain `:`, `@`, or `/` — are
unaffected.

**Acceptance criteria**

1. WHEN a `:`, `@`, or `/` appears in a URL component other than the credentials
   segment (for example in the path, query string, or fragment), THEN
   `URLValidator` SHALL NOT reject the URL on account of those characters.
2. IF a previously-invalid URL is extended with a query string of the form
   `?...@...` (an `@` appearing in the query rather than the authority), THEN
   `URLValidator` SHALL still treat the URL as invalid rather than being made to
   pass by the appended query.
3. The system SHALL keep accepting every URL that was valid before this change
   and does not contain a credentials segment with a forbidden character —
   including URLs with international/IDN and punycode hostnames, IPv4/IPv6 hosts,
   `localhost`, explicit ports, and arbitrary paths, queries, and fragments.
4. The system SHALL keep rejecting every URL that was already invalid before this
   change (this change only narrows the set of accepted URLs; it never widens
   it).
5. The system SHALL continue to raise `ValidationError` using the validator's
   existing invalid-URL message and error code, without changing the validator's
   public interface or its accepted `schemes`.
