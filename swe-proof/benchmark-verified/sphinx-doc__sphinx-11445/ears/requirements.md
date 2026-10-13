# Requirements: correct prolog placement when a document opens with a role-based heading

## Introduction

When a configured preamble string (the `rst_prolog` configuration value) is
prepended to a reStructuredText document, Sphinx must splice the preamble in
*after* any bibliographic header the document opens with, without disturbing a
top-level heading. The relevant code is the `prepend_prolog` function in
`sphinx/util/rst.py`, which scans the leading lines of a document's line list
(`content`) and counts how many of them are bibliographic field lines before
inserting the preamble.

The defect being corrected: the leading-line classifier used a loose pattern
that also matched a line beginning with an interpreted-text role — for example
a heading written as an inline cross-reference such as `` :mod:`mypackage2` ``.
Because such a title line was mistakenly counted as a leading field line, the
preamble was inserted *inside* the title (between the title text and its
underline), so the heading failed to render and was dropped from the table of
contents. The fix must classify leading lines using the true reStructuredText
field-marker grammar, so that a role-prefixed title is not treated as a field
line and the preamble lands before it.

The goal, in behavioral terms: `prepend_prolog` shall skip only genuine
leading field lines when deciding where to insert the preamble, while
preserving all previously correct placement behavior for documents that open
with real bibliographic fields, with plain headings, or with body text.

## Requirement 1: Only genuine field-marker lines count as leading header lines

**User story:** As a documentation author, I want a heading written with an
interpreted-text role (such as `` :mod:`name` ``) at the top of a document to
be preserved when `rst_prolog` is set, so that the heading renders and appears
in the toctree.

**Acceptance criteria**

1. WHEN `prepend_prolog` scans the leading lines of `content` to count the
   header block, THEN the function SHALL classify a line as a leading field
   line only if it conforms to the reStructuredText field-marker grammar: the
   line begins with a colon, immediately followed by a non-empty field name
   whose first character is neither a colon nor a space, terminated by a
   closing colon that is not preceded by a space and is followed by a space or
   the end of the line.
2. WHEN a document's first line is an interpreted-text role applied to title
   text — a leading colon-delimited token such as `` :mod:`mypackage2` ``
   immediately followed by back-quoted content rather than a space or
   end-of-line — THEN `prepend_prolog` SHALL NOT count that line as a leading
   field line.
3. WHEN the first line is such a role-prefixed heading and its underline
   (section adornment) follows on the next line, THEN `prepend_prolog` SHALL
   insert the preamble ahead of the heading so that the heading text and its
   underline remain on consecutive lines with no line inserted between them.
4. The system SHALL apply criterion 2 regardless of whether the role-prefixed
   heading line is followed immediately by an underline line or is separated
   from following content by a blank line.

## Requirement 2: Preamble placement relative to the leading header block

**User story:** As a Sphinx maintainer, I want the preamble spliced in at a
well-defined position relative to the leading header lines, so that documents
with and without a bibliographic header both render correctly.

**Acceptance criteria**

1. Let *k* be the number of consecutive leading field lines (per Requirement 1)
   at the very front of `content`. WHEN the preamble is non-empty, THEN
   `prepend_prolog` SHALL place the preamble lines, in their original order,
   immediately after those first *k* lines.
2. IF *k* is greater than zero, THEN `prepend_prolog` SHALL insert exactly one
   blank line between the leading header block and the preamble.
3. IF *k* is zero, THEN `prepend_prolog` SHALL NOT insert any blank line before
   the preamble; the preamble SHALL begin at the very top of `content`.
4. WHEN the preamble has been inserted, THEN `prepend_prolog` SHALL insert
   exactly one blank line immediately after the preamble, before the remaining
   original lines.
5. WHEN the preamble is inserted, THEN the original lines of `content` SHALL be
   preserved in their original relative order, with the leading *k* lines
   before the inserted material and the remaining lines after it.
6. IF the preamble string is empty, THEN `prepend_prolog` SHALL leave `content`
   unchanged.

## Requirement 3: Preserve existing behavior for bibliographic headers and plain documents

**User story:** As a Sphinx user relying on established `rst_prolog` behavior,
I want documents that open with real docinfo fields, with a plain heading, or
with ordinary body text to keep behaving exactly as before.

**Acceptance criteria**

1. WHEN a document opens with one or more genuine bibliographic field lines
   (each conforming to the field-marker grammar in Requirement 1, e.g.
   `:field: value` or a bare `:field:`), THEN `prepend_prolog` SHALL count all
   of those consecutive leading lines and insert the preamble after them,
   separated by a single blank line.
2. WHEN a document opens with a plain heading (title text followed by an
   underline, with no leading field lines), THEN `prepend_prolog` SHALL insert
   the preamble at the top of the document ahead of the heading, with no blank
   line before the preamble.
3. The system SHALL keep the trailing single blank line after the inserted
   preamble in every non-empty-preamble case, including documents whose line
   list uses carriage-return or platform-specific line endings.
4. The system SHALL keep the appended-epilog behavior of the companion
   function that appends a configured trailing string (`append_epilog`)
   unchanged: a non-empty epilog is appended after a single blank separator
   following the existing content.

## Requirement 4: Preserve unrelated reST helper behavior

**User story:** As a Sphinx user, I want the other reStructuredText helper
utilities in the same module to remain correct, so that this change introduces
no regressions.

**Acceptance criteria**

1. The system SHALL keep the reST symbol-escaping helper (`escape`) producing
   the same escaped output, including escaping a leading dot.
2. The system SHALL keep the text-width helper (`textwidth`) returning the same
   display width, counting wide and full-width East Asian characters as width 2.
3. WHEN the heading helper (`heading`) is asked to render title text at a given
   level, THEN it SHALL produce the title followed by an adornment line whose
   length matches the display width of the title, unchanged from prior
   behavior.
