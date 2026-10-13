# Requirements: Preserve userinfo when normalizing a proxy URL scheme

## Introduction

When a request is routed through a proxy, `requests` normalizes the proxy URL
by ensuring it carries a scheme, via `prepend_scheme_if_needed(url, new_scheme)`
in `requests/utils.py`. This helper is invoked from
`HTTPAdapter.get_connection` in `requests/adapters.py` (as
`prepend_scheme_if_needed(proxy, 'http')`) before the proxy URL is parsed and a
proxy manager is created.

The helper decomposes the input URL into its components with a URL parser and
then reassembles it. The parser used returns the authority *without* any
embedded credentials (the `userinfo` field such as `user:pass`), so when the
helper reassembles the URL from the parser's components it silently drops the
credentials. As a result, a proxy URL such as `http://user:pass@proxy.example`
loses its `user:pass@` prefix, the proxy never receives the authentication it
requires, and the request fails with HTTP `407 Proxy Authentication Required`.

The goal is to make `prepend_scheme_if_needed` a faithful round-trip:
reassembling the URL string must carry **every** parsed component — including
the `userinfo` credentials — back into its standard syntactic slot, while
continuing to add a default scheme only when none is present and preserving the
behavior of all previously handled input shapes.

The affected module/function is `requests.utils.prepend_scheme_if_needed`.

## Requirement 1: Preserve embedded userinfo (credentials) in the reassembled URL

**User story:** As a developer sending requests through an authenticating
proxy, I want `prepend_scheme_if_needed` to keep the credentials embedded in the
proxy URL, so that the proxy receives my authentication and the request is not
rejected with `407`.

**Acceptance criteria**

1. WHEN `prepend_scheme_if_needed` receives a URL whose authority contains a
   `userinfo` component carrying both a username and a password (the
   `username:password` form), THEN the function SHALL return a URL string in
   which that complete `userinfo` component reappears at the front of the
   authority, immediately followed by `@` and the host, so that the credentials
   are not dropped during normalization. When such an input already carries a
   scheme, the returned URL SHALL be identical to the input (a faithful
   round-trip).
2. WHEN `prepend_scheme_if_needed` receives a URL whose authority contains a
   `userinfo` component consisting of a username only (no password), THEN the
   function SHALL return a URL string that preserves that username followed by
   `@` and the host. When such an input already carries a scheme, the returned
   URL SHALL be identical to the input (a faithful round-trip).
3. WHEN the parsed `userinfo` component is present and non-empty, THEN the
   function SHALL join it to the authority using a single `@` separator so that
   the authority in the output reads `userinfo@host` (with the port retained
   when present).
4. IF the parsed URL has no `userinfo` component, THEN the function SHALL leave
   the authority unchanged and SHALL NOT introduce a spurious `@` character.

## Requirement 2: Supply a default scheme only when absent

**User story:** As a caller normalizing a proxy URL, I want a scheme added only
when the input lacks one, so that inputs already carrying a scheme are returned
unmodified.

**Acceptance criteria**

1. IF the input URL has no scheme, THEN `prepend_scheme_if_needed` SHALL use the
   provided `new_scheme` argument as the scheme of the returned URL.
2. IF the input URL already has a scheme, THEN `prepend_scheme_if_needed` SHALL
   keep that existing scheme and SHALL NOT replace it with `new_scheme`.

## Requirement 3: Carry all remaining URL components through unchanged

**User story:** As a caller, I want the host, port, path, query, and fragment
preserved during normalization, so that only the scheme (when missing) and the
credentials re-attachment change the URL.

**Acceptance criteria**

1. The system SHALL preserve the host of the input URL in the returned URL.
2. WHEN the input URL specifies an explicit port, THEN the function SHALL retain
   that port, attached to the host in the returned authority.
3. WHEN the input URL has a non-empty query, THEN the function SHALL preserve
   that query, introduced by `?`, in the returned URL.
4. WHEN the input URL has a non-empty fragment, THEN the function SHALL preserve
   that fragment, introduced by `#`, in the returned URL.
5. WHEN the input URL has a non-empty path that does not already begin with `/`,
   THEN the function SHALL ensure the path in the returned URL begins with `/`.

## Requirement 4: Preserve handling of URLs the parser reports without an authority

**User story:** As a maintainer, I want the existing workaround for inputs the
underlying parser reports as having no authority to keep working, so that
scheme-less host-only inputs continue to normalize as before.

**Acceptance criteria**

1. WHEN the underlying parser reports an empty authority for a scheme-less,
   host-only input (the host and any path appearing without a leading `//`),
   THEN the function SHALL treat the parsed path as the authority so that the
   result places the host in the authority position, with the default scheme
   prepended.
2. WHEN the input begins with `//` followed by a host, THEN the function SHALL
   return the URL with the supplied default scheme prepended and the host in the
   authority position.
3. The system SHALL keep the results of the previously supported scheme-less and
   authority-only inputs unchanged when no `userinfo` is present, adding only the
   default scheme.
