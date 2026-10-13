# Requirements: HTML table writer honors supplied per-column formats

## Introduction

`astropy.io.ascii` can write an astropy `Table` to several text formats via
`Table.write(..., format=...)`, and the writer accepts a `formats` keyword: a
mapping from column name to a display format — either a Python format-spec
string (as accepted by `format()`), or a callable that turns a single value
into a string.
For most output formats the `formats` mapping is applied so that each named
column's values are rendered with the requested format.

The HTML writer (`astropy/io/ascii/html.py`, the `HTML` writer class and its
`HTMLData` data class) ignores the `formats` mapping. When a table is written
with `format="html"`, the column values are emitted using each column's
pre-existing display format only, so a `formats={...}` request has no effect on
the HTML output — unlike the CSV, RST, and other ASCII writers, which honor it.

The goal is to make the HTML writer apply the supplied `formats` mapping exactly
as the other ASCII writers do: before rendering the table body, each column that
is named in `formats` is assigned the requested display format, and the emitted
cell strings reflect that format. The affected module is
`astropy/io/ascii/html.py`; the behavior is observed through
`Table.write(..., format="html", formats=...)`.

## Requirement 1: HTML output applies the supplied per-column formats

**User story:** As a user writing a table to HTML, I want the `formats`
argument to control how each named column's values are displayed, so that HTML
output is formatted consistently with the other ASCII output formats.

**Acceptance criteria**

1. WHEN a table is written with `format="html"` and a `formats` mapping is
   supplied, THEN the HTML writer SHALL render each column that is named in the
   mapping using the format requested for that column name.
2. WHEN a requested column format is a format-specification string, THEN each
   value of that column SHALL appear in the `<td>` cells as that value rendered
   under the given format specification — that is, the cell text is the string
   obtained by applying the requested Python format specification to the value,
   rather than the value's default string form.
3. WHEN a requested column format is a callable, THEN each value of that column
   SHALL appear in the `<td>` cells as the string produced by applying that
   callable to the value.
4. WHEN the `formats` mapping is supplied, THEN a column whose name is NOT a key
   of the mapping SHALL be rendered using the display format it already carried
   (its existing `info.format`, or the default rendering when it has none),
   unchanged by the presence of `formats`.
5. WHEN values are rendered under a requested format, THEN the resulting
   formatted string SHALL be the same string that the other ASCII writers
   (e.g. CSV, RST) produce for that value and that format.

## Requirement 2: HTML document structure is preserved

**User story:** As a user, I want the formatted HTML output to keep the same
document and table structure as before, so that only the cell values change.

**Acceptance criteria**

1. WHEN a table is written with `format="html"`, THEN the writer SHALL emit a
   complete HTML document containing the `<html>`, `<head>`, `<body>`,
   `<table>`, and `<thead>` structure, with one header cell per column holding
   that column's name and one table row per input table row.
2. WHEN a `formats` mapping is supplied, THEN it SHALL affect only the rendered
   body cell values; the column ordering, the header cell contents (column
   names), the number of rows, and the surrounding markup SHALL be unchanged.
3. The system SHALL leave the HTML output byte-for-byte identical to the prior
   behavior for any table written without a `formats` mapping (or with an empty
   one).

## Requirement 3: Regression protection for existing HTML writer behavior

**User story:** As a maintainer, I want the existing HTML writer features to
keep working after formats are honored, so that the fix introduces no
regressions.

**Acceptance criteria**

1. The system SHALL keep applying the writer's `fill_values` substitutions to
   the rendered cell strings, so that configured values (including masked
   entries) are still replaced by their fill text in the HTML output.
2. WHEN both a `formats` mapping and `fill_values` are supplied, THEN the
   writer SHALL apply the requested format to each column's values and still
   perform the fill-value substitutions on the resulting output.
3. The system SHALL keep writing multidimensional (multi-column) columns by
   splitting each into its constituent columns under the `multicol` option,
   including when `fill_values` (and masked entries) are present.
4. The system SHALL keep honoring the writer's other HTML options — such as
   raw-HTML columns (escaping disabled), CSS/JS/table-id/table-class settings,
   and optional-column fill-value configuration — unchanged by the formats
   handling.
5. The system SHALL continue to reject tables whose columns exceed the
   supported dimensionality, as before.
