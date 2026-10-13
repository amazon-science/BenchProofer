# Requirements: Latest-lastmod reporting for sitemaps with no items

## Introduction

Django's sitemap framework (`django.contrib.sitemaps`) exposes a `Sitemap`
class whose `get_latest_lastmod()` method reports the single most recent
last-modified timestamp for a sitemap section. The sitemap index view
(`django.contrib.sitemaps.views.index`) calls this method for every registered
sitemap section to decide whether it can emit a `Last-Modified` HTTP header.

When a `Sitemap` defines `lastmod` as a callable (a per-item function) but its
`items()` collection is empty, `get_latest_lastmod()` computes the maximum over
an empty list of per-item timestamps. Taking the maximum of an empty sequence
raises `ValueError`, which propagates out of the index view and turns a normal
request for the sitemap index into a server error.

The goal is that a sitemap section with a callable `lastmod` but no items
reports "no latest timestamp" instead of raising, so the index view renders
normally and simply omits the `Last-Modified` header for that response. All
other pre-existing `get_latest_lastmod()` behavior and index/section rendering
behavior must be preserved.

Affected code:
- `django/contrib/sitemaps/__init__.py` — `Sitemap.get_latest_lastmod()`
- `django/contrib/sitemaps/views.py` — `index()` (consumer of the reported value)

## Requirement 1: Empty item collection with a callable lastmod

**User story:** As a site operator whose sitemap section can define a per-item
last-modified function but currently has no entries, I want the sitemap index to
render successfully, so that an empty section does not break my sitemap index.

**Acceptance criteria**
1. WHEN `Sitemap.get_latest_lastmod()` is invoked on a sitemap whose `lastmod`
   attribute is a callable and whose `items()` returns an empty collection, THEN
   `get_latest_lastmod()` SHALL return a value indicating "no latest timestamp"
   (the `None` sentinel) rather than raising an exception.
2. WHEN `get_latest_lastmod()` is invoked on a sitemap with a callable `lastmod`
   and an empty `items()` collection, THEN `get_latest_lastmod()` SHALL NOT
   raise `ValueError` (nor any other exception) as a result of the collection
   being empty.
3. WHEN the sitemap index view renders an index that includes a section whose
   `get_latest_lastmod()` reports "no latest timestamp", THEN the rendered index
   response SHALL still list that section's sitemap `<loc>` entry and produce a
   well-formed sitemap index document.
4. IF every section referenced by an index response reports "no latest
   timestamp" (or the collective latest timestamp is otherwise absent), THEN the
   index view SHALL omit the `Last-Modified` header from that response.

## Requirement 2: Preserve latest-lastmod reporting for populated and configured sitemaps

**User story:** As a maintainer of existing sitemaps, I want the established
last-modified reporting to keep working exactly as before, so that adding the
empty-collection safeguard does not change any other outcome.

**Acceptance criteria**
1. WHEN `get_latest_lastmod()` is invoked on a sitemap with a callable `lastmod`
   and a non-empty `items()` collection, THEN it SHALL return the greatest
   (most recent) of the per-item timestamps obtained by applying `lastmod` to
   each item.
2. WHEN `get_latest_lastmod()` is invoked on a sitemap whose `lastmod` attribute
   is a non-callable value, THEN it SHALL return that value unchanged (including
   returning `None` when that value is `None`).
3. IF the sitemap has no `lastmod` attribute at all, THEN `get_latest_lastmod()`
   SHALL return "no latest timestamp" (`None`).
4. IF applying the callable `lastmod` while reducing to the greatest timestamp
   raises `TypeError` (for example when the per-item values are not mutually
   comparable), THEN `get_latest_lastmod()` SHALL return "no latest timestamp"
   (`None`).
5. WHEN an index response covers sections that all report a present latest
   timestamp, THEN the index view SHALL set the `Last-Modified` header to the
   most recent of those reported timestamps.
6. The system SHALL continue to render simple sitemaps, paged sitemaps, sitemap
   sections, and sitemap indexes, and to set or omit the `Last-Modified` header
   on section and index responses, according to the pre-existing rules for
   populated and empty sitemaps.
