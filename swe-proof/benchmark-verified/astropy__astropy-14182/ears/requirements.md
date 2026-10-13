# Requirements: `header_rows` support for the ascii.rst fixed-width format

## Introduction

The reStructuredText simple-table format is implemented by the `RST` reader/writer
class in `astropy/io/ascii/rst.py` (registered as the `ascii.rst` format used when
writing tables via `Table.write` / `QTable.write` and when parsing them via the
corresponding `Table`/`QTable` loading entry points). `RST` derives
from the generic fixed-width machinery in `astropy/io/ascii/fixedwidth.py`
(`FixedWidth`, `FixedWidthHeader`, `FixedWidthData`).

The sibling fixed-width formats (for example `ascii.fixed_width`) already accept a
`header_rows` keyword — a list of column attributes (such as `name`, `unit`,
`dtype`) to emit as successive header lines and to interpret when parsing. The
`ascii.rst` format did not: passing `header_rows` raised
`TypeError: RST.__init__() got an unexpected keyword argument 'header_rows'`, and
its writer/parser assumed exactly one header line (the column-name row).

An `ascii.rst` simple table is laid out as a top border line (a whitespace-separated
run of `=` characters, one group per column), then one or more header rows, then a
second border line, then the data rows, then a closing border line. The goal is to
let `ascii.rst` accept `header_rows` on both writing and parsing so that an arbitrary
list of header attribute rows can be round-tripped, while the historical
single-header-row behavior is preserved unchanged.

## Requirement 1: Accept the `header_rows` keyword for `ascii.rst`

**User story:** As a user of `astropy.io.ascii`, I want the `ascii.rst` format to
accept a `header_rows` keyword just like the other fixed-width formats, so that I can
control which column attributes appear as header lines instead of getting a
`TypeError`.

**Acceptance criteria**

1. WHEN a table is written or parsed with the `ascii.rst` format and a `header_rows`
   list is supplied, THEN the `RST` class SHALL accept that keyword and SHALL NOT
   raise `TypeError` (or any other exception) about an unexpected `header_rows`
   argument.
2. IF no `header_rows` value is supplied for the `ascii.rst` format, THEN the format
   SHALL behave as though a single header row consisting of the column names was
   requested, matching the format's prior default output and parsing.
3. WHEN `header_rows` is supplied as a list of attribute names, THEN the `RST` format
   SHALL treat its length as the number of header lines to emit and to expect, and
   SHALL emit/interpret each named attribute (for example `name`, `unit`, `dtype`) as
   its own header line in the order given.

## Requirement 2: Write an `ascii.rst` table with the requested header rows

**User story:** As a user generating reStructuredText, I want to choose which
attribute rows appear in the header, so that units, dtypes, or other per-column
attributes are shown above the data.

**Acceptance criteria**

1. WHEN a table is written with the `ascii.rst` format and a `header_rows` list of
   length N, THEN the output SHALL consist, in order, of: a top border line, then the
   N requested header lines (one per requested attribute, in the given order), then a
   second border line, then the formatted data rows, then a closing border line.
2. WHEN such a table is written, THEN each border line SHALL be the border/rule line
   that the fixed-width layout places immediately after the last header line — i.e.
   the border SHALL be selected by the number of header rows, not fixed at the
   second output line — so that the top and bottom borders remain correct for any N,
   including N greater than one.
3. WHEN such a table is written, THEN each border line SHALL contain one run of `=`
   characters per column, each run as wide as its column, separated by single
   spaces, so that the border widths align with the header and data columns.
4. The system SHALL right-align the value in every emitted header and data cell to
   its column width, consistent with the existing `ascii.rst` output style (no
   surrounding delimiters or bookends).

## Requirement 3: Parse an `ascii.rst` table that has multiple header rows

**User story:** As a user loading reStructuredText, I want the parser to understand a
table whose header carries several attribute rows, so that units and dtypes declared
in the header are recovered onto the columns.

**Acceptance criteria**

1. WHEN an `ascii.rst` table is parsed with a `header_rows` list of length N, THEN
   the parser SHALL locate the data rows as beginning after the top border line, the
   N header lines, and the second border line — that is, it SHALL skip N + 2 leading
   lines before the first data row — rather than assuming a single header line.
2. WHEN `header_rows` names an attribute other than `name` (for example `unit` or
   `dtype`), THEN the parser SHALL consume the corresponding header line and apply each
   non-empty value to the matching column as that attribute.
3. WHEN `header_rows` includes `name`, THEN the parser SHALL take the column names
   from that header line, at its position within the header block.
4. WHILE parsing an `ascii.rst` table whose rightmost column has no fixed right edge,
   the parser SHALL treat that column as extending to the end of each line, as it did
   before this change.

## Requirement 4: Round-trip fidelity for tables with units and dtypes

**User story:** As a user, I want to write a table with name/unit/dtype header rows
and parse it back without losing information, so that reStructuredText is a faithful
serialization.

**Acceptance criteria**

1. WHEN a table carrying per-column units and explicit numeric dtypes is parsed from
   `ascii.rst` with `header_rows` of `name`, `unit`, and `dtype`, THEN each column's
   unit SHALL be recovered from the unit header line and each column's dtype SHALL
   match the dtype named on the dtype header line.
2. WHEN that parsed table is then written again with the same `header_rows`, THEN the
   emitted lines SHALL be identical to the lines it was parsed from (a faithful
   round trip), including the border lines, the header lines, and the data rows.

## Requirement 5: Preserve the existing single-header `ascii.rst` behavior

**User story:** As a maintainer, I want all pre-existing `ascii.rst` reading and
writing behavior to remain exactly as before, so that the new keyword introduces no
regression.

**Acceptance criteria**

1. WHEN a table is written with the `ascii.rst` format and no `header_rows` is given,
   THEN the output SHALL be a top border line, a single column-name header line, a
   second border line, the data rows, and a closing border line — unchanged from the
   format's historical output.
2. WHEN an ordinary `ascii.rst` table (top border, one name row, border, data,
   border) is parsed with no `header_rows`, THEN the parser SHALL take the column
   names from the name row and the data rows beginning on the line after the second
   border, exactly as before.
3. The system SHALL continue to honor caller-supplied column `names`, and the
   selection of columns to include or exclude, when parsing an `ascii.rst` table.
4. The system SHALL continue to parse `ascii.rst` tables that are indented, that have
   an unbounded rightmost column, and that contain trailing spaces in a row, without
   error and with the same column values as before.
