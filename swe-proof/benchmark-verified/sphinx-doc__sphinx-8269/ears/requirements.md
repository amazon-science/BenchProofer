# Linkcheck: report HTTP errors ahead of anchor-not-found

## Introduction

Sphinx's `linkcheck` builder validates hyperlinks in a project's documentation
and writes a per-link outcome. It is implemented in
`sphinx/builders/linkcheck.py`, primarily in the `check_uri` helper of the
`CheckExternalLinksBuilder` builder.

When the configuration option `linkcheck_anchors` is enabled (`True`) and a
target URL carries an in-page fragment (an `#anchor` component), the builder
fetches the whole document with an HTTP GET request and then searches the
returned body for the requested fragment. The bug: this fragment path never
inspects the reply's HTTP status code. So when the server answers with an error
status (for example `404 Not Found` or `500 Internal Server Error`), the body
does not contain the fragment, and the builder misleadingly reports the link as
broken because the *anchor* was not found — hiding the real problem, which is
that the request itself failed.

The goal is to make the fragment-checking path consult the server's HTTP status
first, exactly as the non-anchor path already does: an error status must be
reported as the HTTP-level error (and routed through the existing special-case
handling for particular status codes), and the fragment must only be consulted
when the status is not an error. The behavior when `linkcheck_anchors` is
disabled, and every other existing linkcheck outcome, must be preserved.

## Requirement 1: HTTP error status governs the anchor-checking path

**User story:** As a documentation author running `linkcheck` with anchor
checking enabled, I want a link whose server returns an error status to be
reported as that HTTP error, so that I can see the true cause instead of a
misleading "anchor not found" message.

**Acceptance criteria**

1. WHEN `linkcheck_anchors` is enabled AND a checked URL carries a fragment
   whose anchor is not in the ignore list AND the GET request used to retrieve
   the document returns a non-success HTTP status (an error status such as 4xx
   or 5xx), THEN the builder SHALL determine the link's outcome from that HTTP
   status and SHALL NOT report the outcome as an anchor-not-found failure.
2. WHEN the GET request in the anchor-checking path returns an error status
   that is not otherwise special-cased, THEN the builder SHALL classify the
   link as `broken` and SHALL record an explanatory message describing the
   HTTP error (the standard HTTP error text, e.g. reflecting the numeric status
   and the requested URL), identical to how the same status is reported when
   anchor checking is not performed.
3. WHEN the GET request returns a status that the builder treats as acceptable
   (an "unauthorized" status), THEN the builder SHALL report the link as
   `working`, consistent with the existing handling for that status.
4. WHEN the GET request returns a status that the builder treats as ignorable
   (a "service unavailable" status), THEN the builder SHALL report the link as
   `ignored`, consistent with the existing handling for that status.
5. The system SHALL consult the HTTP status of the reply BEFORE searching the
   returned document for the fragment, so that the status determines the
   outcome on its own whenever it is an error.

## Requirement 2: Preserve anchor-not-found reporting for successful responses

**User story:** As a documentation author, I want a genuinely missing anchor on
a page that otherwise loads correctly to still be reported as an anchor
failure, so that anchor checking keeps working as before.

**Acceptance criteria**

1. WHEN `linkcheck_anchors` is enabled AND the GET request returns a success
   (non-error) HTTP status AND the requested fragment is not present in the
   returned document, THEN the builder SHALL report the link as `broken` with a
   message stating that the anchor was not found.
2. WHEN `linkcheck_anchors` is enabled AND the GET request returns a success
   status AND the requested fragment is present in the returned document, THEN
   the builder SHALL report the link using its normal successful-link outcome
   (e.g. `working` or `redirected`), unchanged from prior behavior.
3. IF a URL's fragment matches a configured anchor-ignore pattern, THEN the
   builder SHALL skip fragment checking for that URL and SHALL keep its existing
   non-anchor validation behavior.

## Requirement 3: Preserve all other linkcheck behaviors

**User story:** As a maintainer, I want the existing linkcheck outcomes to be
unaffected by this change, so that no previously-passing behavior regresses.

**Acceptance criteria**

1. WHILE `linkcheck_anchors` is disabled, the builder SHALL keep its existing
   validation behavior for every link, including the HEAD-then-GET request
   strategy and its status-based classification of working, broken, redirected,
   and ignored links.
2. The system SHALL keep reporting locally-resolvable and non-network URIs
   (empty targets, in-document fragments, `mailto:`, unsupported URI schemes,
   and local file paths) with their existing outcomes.
3. The system SHALL keep honoring per-URL request headers, authentication
   configuration, and the anchor-ignore configuration when validating links.
4. WHEN a link has already been recorded as good, broken, or redirected, THEN
   the builder SHALL keep reusing that recorded outcome without re-issuing a
   network request.
