# Requirements: Correct whitespace when rendering column lists for CREATE INDEX

## Introduction

Django's schema editor renders `CREATE INDEX` statements by assembling a
comma-separated list of column references. The rendering of that list is
performed by the DDL reference helpers in
`django/db/backends/ddl_references.py` — specifically the `Columns` class and
its subclass `IndexColumns`, whose `__str__` methods produce the parenthesized
column list that appears in the generated SQL (reached through
`django.db.models.indexes.Index.create_sql(...)` via the schema editor).

Each column entry is built from:

* the quoted column name (produced by a caller-supplied quoting function);
* for `IndexColumns` only, a mandatory per-column operator-class annotation
  looked up positionally;
* an optional positional ordering suffix (for example the descending-order
  token), looked up positionally by the column's index.

The ordering suffixes are supplied positionally, one entry per column. A
column with descending order contributes a non-empty suffix token; a column
with ascending (default) order contributes an **empty string** rather than a
missing entry. The previous implementation appended the suffix by string
concatenation without a separating space, and appended it even when it was the
empty string. This produced two defects:

* an ordering token was glued directly onto the quoted name with no separating
  space (e.g. a descending column rendered as `"name"DESC` instead of
  `"name" DESC`);
* for operator-class columns given no explicit ordering, the empty suffix was
  still appended with a separating space, leaving a stray trailing space after
  the operator class (e.g. `"name" text_pattern_ops ` instead of
  `"name" text_pattern_ops`).

The goal is to render each entry with correct, minimal whitespace: a non-empty
ordering suffix is set off by exactly one space, and an empty (or absent)
suffix contributes nothing at all — neither a token nor a separating space.
This must not disturb the existing correct renderings.

## Requirement 1: A non-empty ordering suffix is separated by a single space

**User story:** As a developer generating index DDL, I want an ordering token
(such as the descending-order keyword) to be separated from the preceding
column reference by a single space, so that the generated SQL uses documented,
portable syntax.

**Acceptance criteria**

1. WHEN a plain column entry has a non-empty positional ordering suffix, THEN
   the renderer SHALL emit the quoted column name, then exactly one space, then
   the suffix token, with no other characters between them.
2. WHEN an operator-class column entry has a non-empty positional ordering
   suffix, THEN the renderer SHALL emit the quoted column name, one space, the
   operator-class annotation, one space, and the suffix token, in that order.
3. WHEN an index over a single descending field is rendered to SQL, THEN the
   resulting statement SHALL contain the quoted column name followed by a single
   space and the descending-order keyword within the parenthesized column list
   (for example `("name" DESC)`, never `("name"DESC)`).
4. WHEN an index over a single descending field that also carries an
   operator-class annotation is rendered to SQL, THEN the parenthesized column
   list SHALL contain the quoted column name, one space, the operator-class
   token, one space, and the descending-order keyword (for example
   `("name" text_pattern_ops DESC)`).

## Requirement 2: An empty or absent ordering suffix contributes nothing

**User story:** As a developer generating index DDL, I want a column with no
explicit ordering to render with no trailing whitespace, so that the generated
SQL is clean and free of stray spaces.

**Acceptance criteria**

1. IF the positional ordering suffix for a column entry is the empty string,
   THEN the renderer SHALL leave that entry unchanged, appending neither a
   suffix token nor a separating space.
2. IF no positional ordering suffix exists for a column entry (the position is
   out of range), THEN the renderer SHALL leave that entry unchanged, exactly as
   when the suffix is the empty string.
3. WHEN an index over a single ascending field is rendered to SQL, THEN the
   parenthesized column list SHALL contain the quoted column name with no
   trailing space before the closing parenthesis (for example `("name")`).
4. WHEN an index over a single ascending field that also carries an
   operator-class annotation is rendered to SQL, THEN the parenthesized column
   list SHALL contain the quoted column name, one space, and the operator-class
   token, with no trailing space after the operator-class token (for example
   `("name" text_pattern_ops)`, never `("name" text_pattern_ops )`).

## Requirement 3: The mandatory operator-class annotation is preserved

**User story:** As a developer defining an index with operator classes, I want
each column's operator-class annotation to remain present and correctly spaced,
so that the operator-class behavior fixed previously continues to work.

**Acceptance criteria**

1. The system SHALL render each operator-class column entry as the quoted
   column name followed by exactly one space and then the per-column
   operator-class annotation.
2. WHEN an operator-class column entry has an empty ordering suffix, THEN the
   renderer SHALL keep the quoted-name-plus-annotation form intact and SHALL
   NOT append any further characters.

## Requirement 4: Multi-column joining is unaffected by the whitespace fix

**User story:** As a developer generating index DDL, I want the separator
between column entries to be unchanged by the per-entry whitespace fix, so that
multi-column indexes keep rendering correctly.

**Acceptance criteria**

1. WHEN more than one column entry is rendered, THEN the renderer SHALL join the
   entries with a comma followed by a single space, unchanged from prior
   behavior.
2. WHEN multiple column entries with differing ordering suffixes are rendered
   together, THEN each entry SHALL independently obey the single-space and
   no-trailing-space rules of Requirements 1 and 2, and the entries SHALL be
   joined by a comma and a single space.
