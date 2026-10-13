# Requirements: Admin catch-all trailing-slash redirect honors the deployment script prefix

## Introduction

The Django admin site installs a final "catch-all" view, `AdminSite.catch_all_view`
in `django/contrib/admin/sites.py`, which handles admin URLs that did not match
any earlier admin pattern. When the `APPEND_SLASH` setting is enabled and the
requested locator has no trailing slash, this view checks whether appending a
slash would produce a recognized admin URL and, if so, issues a permanent
(HTTP 301) redirect to the slash-appended location; otherwise it raises
`Http404`.

The defect: the redirect target is built from the request's internal routing
location (the path with any deployment script-name prefix stripped off) rather
than the outward-facing location the client actually sees. When Django runs
under a script-name prefix — whether supplied per-request by the WSGI
environment (`SCRIPT_NAME`) or forced globally via the `FORCE_SCRIPT_NAME`
setting — the emitted redirect drops that prefix and points at the wrong URL.

The goal is that the catch-all view's redirect target always includes the
deployment prefix, so clients behind a script-name prefix are redirected to a
working URL, while the internal resolution probe and every other existing
behavior of the view are preserved unchanged.

Affected code: `AdminSite.catch_all_view(self, request, url)` in
`django/contrib/admin/sites.py`. The two relevant request attributes are the
outward-facing full path (which includes the script-name prefix) and the
internal routing path (which excludes it). The view consults `settings.APPEND_SLASH`,
the request's optional URL configuration, Django's URL resolution, and the
matched view's `should_append_slash` attribute.

## Requirement 1: Redirect target reflects the outward-facing request location

**User story:** As an operator deploying the Django admin under a URL prefix
(for example behind a reverse proxy setting a script name, or with a forced
script name), I want the admin's automatic trailing-slash redirect to point at
the prefixed, client-visible URL, so that browsers follow the redirect to a URL
that actually resolves instead of one with the prefix stripped off.

**Acceptance criteria**

1. WHEN the catch-all view decides to issue a trailing-slash redirect, THEN the
   view SHALL set the redirect target to the request's outward-facing full path
   (the path as seen by the client, including any deployment script-name prefix)
   with a single trailing slash appended.
2. IF the request is served under a per-request script-name prefix (supplied via
   the request environment), THEN the redirect target SHALL begin with that
   script-name prefix.
3. IF a global forced script-name prefix is configured, THEN the redirect target
   SHALL begin with that forced prefix even when the request environment does not
   itself carry the prefix.
4. WHEN no script-name prefix is in effect, THEN the redirect target SHALL equal
   the requested locator with a single trailing slash appended (the outward-facing
   path and the internal routing path coincide in this case, so behavior is
   unchanged).
5. The system SHALL issue the redirect as an HTTP 301 permanent redirect.

## Requirement 2: Resolution probe continues to use the internal routing path

**User story:** As a maintainer, I want the decision of *whether* to redirect to
keep using the internal (prefix-stripped) routing path, so that URL resolution
still matches the installed admin patterns regardless of deployment prefix.

**Acceptance criteria**

1. WHEN the catch-all view tests whether a slash-appended locator is recognized,
   THEN the view SHALL perform that resolution against the request's internal
   routing path (the prefix-stripped path) with a single trailing slash appended,
   not against the outward-facing prefixed path.
2. WHEN performing the resolution probe, THEN the view SHALL use the request's
   URL configuration if one is present on the request, and the default URL
   configuration otherwise.
3. The system SHALL keep the redirect decision (whether to redirect at all)
   independent of the presence or value of any script-name prefix; only the
   redirect target is affected by the prefix.

## Requirement 3: Preconditions for attempting a redirect

**User story:** As a maintainer, I want the existing conditions that gate the
trailing-slash redirect to remain exactly as before, so that only the target
URL changes and no other behavior regresses.

**Acceptance criteria**

1. IF the `APPEND_SLASH` setting is disabled, THEN the view SHALL raise `Http404`
   without attempting any resolution probe or redirect.
2. IF the requested locator already ends with a trailing slash, THEN the view
   SHALL raise `Http404` without attempting any resolution probe or redirect.
3. WHEN `APPEND_SLASH` is enabled and the requested locator does not end with a
   trailing slash, THEN the view SHALL perform the resolution probe described in
   Requirement 2.

## Requirement 4: Behavior when the slash-appended locator is not redirectable

**User story:** As a user, I want unrecognized or non-redirectable admin URLs to
keep returning "not found", so that the fix does not turn 404s into spurious
redirects.

**Acceptance criteria**

1. IF the resolution probe does not recognize the slash-appended locator, THEN
   the view SHALL raise `Http404` and SHALL NOT issue a redirect.
2. IF the resolution probe recognizes the slash-appended locator but the matched
   view does not permit automatic trailing-slash appending (its
   `should_append_slash` attribute is present and false), THEN the view SHALL
   raise `Http404` and SHALL NOT issue a redirect.
3. WHEN the resolution probe recognizes the slash-appended locator and the matched
   view permits trailing-slash appending (its `should_append_slash` attribute is
   absent or true), THEN the view SHALL issue the trailing-slash redirect as
   specified in Requirement 1.
