# Requirements: linkcheck GET fallback on redirect loops

## Introduction

The Sphinx *linkcheck* builder (`sphinx/builders/linkcheck.py`) validates external
hyperlinks. To be gentle on servers and the network, it first probes each URL with
a lightweight HTTP `HEAD` request and only downloads the full resource with a `GET`
request when the probe fails in a way that warrants a retry (some servers reject or
mishandle `HEAD` requests). This retry-with-`GET` fallback is implemented in the
per-URL checking routine `check_uri` (nested inside `CheckExternalLinksBuilder.check_thread`).

Currently the fallback is triggered only when the `HEAD` probe raises an HTTP
status error (`requests.exceptions.HTTPError`). Some websites enter an infinite
redirect loop for `HEAD` requests while answering `GET` requests normally; in that
case the `HEAD` probe raises `requests.exceptions.TooManyRedirects`, which is not
caught by the fallback, so the link is incorrectly reported as broken even though a
`GET` request would succeed.

The goal is to extend the fallback so that a redirect-loop failure of the `HEAD`
probe also triggers the `GET` retry, while preserving all existing link-checking
behavior (HTTP-status fallback, redirect reporting, status-code handling, and
anchor checking).

## Requirement 1: Fall back to GET when the HEAD probe hits a redirect loop

**User story:** As a documentation author running linkcheck, I want links that
send `HEAD` requests into an infinite redirect loop but answer `GET` requests
normally to be reported as working, so that valid links are not falsely flagged as
broken.

**Acceptance criteria**

1. WHEN linkcheck probes an external URL with a `HEAD` request and that request
   fails because the server keeps redirecting without ever settling (a redirect
   loop, surfaced as `requests.exceptions.TooManyRedirects`), THEN the builder
   SHALL retry the same URL with a `GET` request and determine the link's outcome
   from that `GET` response.
2. WHEN the `HEAD` probe hits a redirect loop and the subsequent `GET` request
   succeeds with a final URL equal (ignoring a trailing `/`) to the requested URL,
   THEN the builder SHALL report the link with status `working` and an empty
   informational message.
3. IF the fallback `GET` request itself fails, THEN the builder SHALL report the
   link's outcome from that `GET` failure using the same status-classification
   rules that apply to any other request failure (see Requirement 3), and SHALL NOT
   re-raise the original redirect-loop condition.

## Requirement 2: Preserve GET fallback on HTTP status errors

**User story:** As a maintainer, I want the pre-existing fallback behavior for
servers that reject `HEAD` requests to keep working, so that extending the fallback
does not regress the original feature.

**Acceptance criteria**

1. WHEN the `HEAD` probe fails with an HTTP status error (`requests.exceptions.HTTPError`,
   e.g. because the server returns an error status to `HEAD`), THEN the builder
   SHALL retry the same URL with a `GET` request and determine the link's outcome
   from that `GET` response.
2. The system SHALL apply the `GET` retry only when the `HEAD` probe fails with a
   retryable condition (an HTTP status error or a redirect loop); for any other
   `HEAD` failure the builder SHALL NOT issue a `GET` retry and SHALL report the
   original failure.

## Requirement 3: Preserve status-code and failure classification

**User story:** As a documentation author, I want link results to keep their
established status classifications, so that reports remain stable across this change.

**Acceptance criteria**

1. IF the request that determines the outcome fails with an HTTP status error whose
   status code is `401`, THEN the builder SHALL report the link as `working`
   (treating "Unauthorized" as a working link).
2. IF the request that determines the outcome fails with an HTTP status error whose
   status code is `503`, THEN the builder SHALL report the link as `ignored`.
3. IF the request that determines the outcome fails with an HTTP status error whose
   status code is any other value, THEN the builder SHALL report the link as `broken`.
4. IF the request that determines the outcome fails for a non-HTTP-status reason
   (for example a connection error or a rejected TLS certificate), THEN the builder
   SHALL report the link as `broken` with the failure's message.

## Requirement 4: Preserve success and redirect reporting

**User story:** As a documentation author, I want successful links and redirected
links to keep being reported exactly as before, so that only genuinely broken links
are flagged.

**Acceptance criteria**

1. WHEN the determining response's final URL equals the requested URL (ignoring a
   trailing `/`), THEN the builder SHALL report the link as `working` with an empty
   informational message.
2. WHEN the determining response's final URL differs from the requested URL
   (ignoring a trailing `/`), THEN the builder SHALL report the link as `redirected`
   with the final URL, and SHALL include the status code of the last redirect in the
   response history when such history exists.
3. The system SHALL continue to probe with a `HEAD` request first (before any `GET`
   fallback) for the network-easing benefit, except where anchor checking already
   requires a full `GET` request.

## Requirement 5: Preserve anchor checking behavior

**User story:** As a documentation author, I want anchor validation to remain
unchanged, so that this fallback change does not affect link fragments.

**Acceptance criteria**

1. WHEN anchor checking is enabled and the URL includes an anchor fragment, THEN the
   builder SHALL fetch the resource with a `GET` request and report the link as
   broken if the requested anchor is not present in the response.
