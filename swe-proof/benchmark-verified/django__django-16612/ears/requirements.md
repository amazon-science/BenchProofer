# Requirements: Preserve query string when the admin catch-all view appends a trailing slash

## Introduction

The Django admin site exposes a final catch-all view,
`AdminSite.catch_all_view()` in `django/contrib/admin/sites.py`. When
`APPEND_SLASH` is enabled and a request arrives for a known admin URL that is
missing its canonical trailing slash, this view issues a permanent (HTTP 301)
redirect to the slash-terminated form of the URL so the browser retries the
correct address.

A regression caused this redirect to be built solely from the request path,
discarding any query string that accompanied the original request. A request
for `.../foo?id=123` was redirected to `.../foo/` instead of `.../foo/?id=123`,
silently losing the query parameters.

The goal is to make the catch-all redirect preserve the full requested
location — path plus query string — when it adds the trailing slash, while
leaving every other catch-all behavior (the no-slash-needed cases, the
`APPEND_SLASH=False` case, unknown URLs, script-name / prefix handling, and the
unauthenticated login redirect) unchanged. The redirect target is assembled
using the existing `HttpRequest.get_full_path()` machinery in
`django/http/request.py`, which already knows how to combine the encoded path,
an optional trailing slash, and the encoded query string.

## Requirement 1: Preserve the query string in the trailing-slash redirect

**User story:** As an admin user who requests a valid admin URL without its
trailing slash but with query parameters, I want to be redirected to the
slash-terminated URL that still carries my query parameters, so that no request
information is lost when the browser follows the redirect.

**Acceptance criteria**

1. WHEN `APPEND_SLASH` is enabled and `AdminSite.catch_all_view()` handles a
   request for a path that does not end in a slash but resolves (with a slash
   appended) to a view that permits slash-appending, THEN the view SHALL respond
   with an HTTP 301 permanent redirect.
2. WHEN such a redirect is produced and the original request carried a non-empty
   query string, THEN the redirect target SHALL consist of the slash-terminated
   request path followed by the same query string, introduced by a single `?`
   separator.
3. WHEN such a redirect is produced and the original request carried no query
   string, THEN the redirect target SHALL be the slash-terminated request path
   with no `?` and no query component appended.
4. The redirect target SHALL contain exactly one trailing slash on the path
   component: a slash SHALL be added after the path only when the path does not
   already end in one, and never doubled.
5. The query string carried into the redirect target SHALL preserve the
   parameters and their order from the original request, encoded for URI use as
   `HttpRequest.get_full_path()` encodes them.

## Requirement 2: Honor the request's script-name / URL prefix in the redirect

**User story:** As an operator deploying the admin under a URL prefix (via a
WSGI `SCRIPT_NAME` or a forced script name), I want the trailing-slash redirect
to point at the correctly prefixed URL with the query string intact, so that the
redirect resolves under my deployment prefix.

**Acceptance criteria**

1. WHEN the request is served under a script-name / URL prefix and the catch-all
   view issues a trailing-slash redirect, THEN the redirect target SHALL include
   that prefix in the path component, matching the full externally visible
   request path.
2. WHEN such a prefixed redirect is produced for a request carrying a non-empty
   query string, THEN the redirect target SHALL be the prefixed, slash-terminated
   path followed by the original query string after a single `?`.
3. The system SHALL derive the redirect target from the request's full path
   (which already reflects the applicable script-name prefix) rather than from a
   prefix-stripped path.

## Requirement 3: Preserve unchanged catch-all behaviors (regression protection)

**User story:** As a Django maintainer, I want all pre-existing catch-all
redirect and error behaviors to remain exactly as before, so that fixing the
query-string loss introduces no behavioral regressions.

**Acceptance criteria**

1. WHEN `APPEND_SLASH` is enabled and the resolved target view opts out of
   slash-appending, THEN `AdminSite.catch_all_view()` SHALL NOT redirect and
   SHALL raise an HTTP 404 (Not Found) response.
2. WHEN `APPEND_SLASH` is disabled, THEN `AdminSite.catch_all_view()` SHALL NOT
   issue a trailing-slash redirect and SHALL raise an HTTP 404 response,
   regardless of whether the request carried a query string.
3. WHEN the requested path already ends in a slash, or when appending a slash
   does not resolve to any admin view, THEN the view SHALL NOT redirect and SHALL
   raise an HTTP 404 response.
4. IF the requesting user is not an authenticated staff member and requests a
   known admin URL missing its trailing slash, THEN the system SHALL redirect to
   the admin login page with a `next` parameter whose value is the full
   originally requested location, so that any accompanying query string is
   retained (URL-encoded) within that `next` parameter rather than discarded.
5. WHEN a request for a known admin URL missing its trailing slash carries no
   query string, THEN the trailing-slash redirect behavior SHALL remain
   unchanged from before this fix: an HTTP 301 redirect to the slash-terminated
   path.
6. The system SHALL leave the catch-all handling for unknown URLs, for
   deployments without a final catch-all view, and for unauthenticated requests
   unchanged in status code and redirect target aside from the query-string
   preservation described in Requirements 1 and 2.
