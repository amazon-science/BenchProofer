# Requirements: Case-insensitive parsing of QDP-format tables

## Introduction

The `ascii.qdp` reader in `astropy.io.ascii` (module
`astropy/io/ascii/qdp.py`) parses QDP-format text tables. The QDP format is,
by its own definition, **not case sensitive**: a command such as
`READ SERR 1 2` and its lower-case form `read serr 1 2` are equivalent, and
QDP itself accepts either. The current reader assumes commands and the
missing-value marker are written in upper case. As a result, a hand-written
QDP file that uses lower-case (or mixed-case) keywords is rejected with
`ValueError: Unrecognized QDP line: ...` instead of being read into a
`Table`.

The affected behavior lives in two helpers of `astropy/io/ascii/qdp.py`:

- `_line_type(line, delimiter=None)` — classifies a single source line into
  a syntactic category (a command line, a table-break "new" marker, a data
  row with a column count, a comment, or otherwise raising for an
  unrecognized line). The classification is driven by a compiled regular
  expression.
- `_get_tables_from_qdp_file(...)` — iterates over classified lines and, for
  each token of a data row, decides whether the token is the missing-value
  sentinel (`NO`) or a number to be parsed.

The goal is to make both the line classification and the missing-value
detection insensitive to letter-case, so that QDP files with lower-case or
mixed-case keywords read successfully and produce the same tables as their
upper-case equivalents, while all existing upper-case behavior is preserved.
This behavior is reachable through the public API
`Table.read(path, format='ascii.qdp')` and the `astropy.io.ascii.QDP`
reader/writer.

## Requirement 1: Case-insensitive recognition of QDP command lines

**User story:** As a user who writes QDP files by hand, I want error-column
commands to be recognized regardless of letter-case, so that files using
lower-case keywords load without error just as QDP itself allows.

**Acceptance criteria**

1. WHEN `_line_type` is given a symmetric- or two-sided-error command line
   whose keyword tokens are written in any mixture of upper and lower case
   (for example the lower-case equivalent of `READ SERR 1 2` or of
   `READ TERR 1 2`), THEN `_line_type` SHALL classify the line as a command
   line rather than raising for an unrecognized line.
2. WHEN a command line is written entirely in upper case, THEN `_line_type`
   SHALL continue to classify it as a command line.
3. IF two lines differ only in the letter-case of their characters, THEN
   `_line_type` SHALL assign them the same category.
4. The system SHALL determine the column indices referenced by an error
   command from its trailing integer tokens irrespective of the case used to
   write the command keyword.

## Requirement 2: Case-insensitive recognition of the table-break and data lines

**User story:** As a user reading a multi-block or mixed-case QDP file, I want
the block-separator marker and numeric rows to be recognized regardless of
case, so that classification never depends on how the file's letters are
cased.

**Acceptance criteria**

1. WHEN `_line_type` is given a table-break marker line composed of the
   missing-value tokens (the repeated `NO` separator sequence) written in any
   letter-case, THEN `_line_type` SHALL classify it as a table-break ("new")
   line.
2. WHEN `_line_type` is given a data row containing numeric tokens and/or
   missing-value tokens written in any letter-case, THEN `_line_type` SHALL
   classify it as a data line and SHALL report the number of value columns as
   the count of tokens in the row.
3. WHILE a non-comment line does not match any recognized category, the
   system SHALL raise a `ValueError` identifying the line as unrecognized.
4. The system SHALL apply the same case-insensitive classification whether the
   value separator is whitespace or an explicitly supplied delimiter (for
   example a comma).

## Requirement 3: Case-insensitive missing-value detection when reading data rows

**User story:** As a user whose data rows use lower-case or mixed-case
missing-value markers, I want those cells read as missing values, so that the
resulting table masks them exactly as it would for the upper-case marker.

**Acceptance criteria**

1. WHEN `_get_tables_from_qdp_file` reads a data-row token that equals the
   missing-value sentinel (`NO`) up to letter-case, THEN it SHALL record that
   cell as a masked/missing value.
2. WHEN it reads a data-row token that is not the missing-value sentinel,
   THEN it SHALL record the numeric value obtained by parsing the token
   (as an integer when the token parses as an integer, otherwise as a float).
3. The system SHALL produce exactly one output cell per input token of a data
   row, preserving their left-to-right order.

## Requirement 4: End-to-end reading of case-insensitive QDP files

**User story:** As a user, I want a QDP file that uses lower-case or
mixed-case keywords to read into a `Table` with the correct error columns and
masked values, so that hand-written files work end to end.

**Acceptance criteria**

1. WHEN a QDP file whose non-comment lines are written in lower case is read
   via the QDP reader, THEN the system SHALL return the same table content
   (column structure, error columns, data values, and masked entries) as it
   returns for the equivalent upper-case file.
2. WHEN a QDP file declares error columns via a lower-case or mixed-case
   error command, THEN the system SHALL attach the corresponding symmetric or
   two-sided error columns to the resulting table.
3. IF the QDP file uses lower-case keywords that the reader previously
   rejected, THEN the system SHALL read it successfully instead of raising an
   unrecognized-line error.

## Requirement 5: Preservation of existing QDP read/write behavior

**User story:** As an existing user, I want all current QDP behavior to keep
working unchanged, so that the case-insensitivity change is purely additive.

**Acceptance criteria**

1. The system SHALL continue to read upper-case QDP files (including files
   with error commands, comments, and multiple blocks) into the same tables
   as before.
2. WHEN a table is written to QDP format and read back, THEN the system SHALL
   reproduce the original column values and masked entries, and this
   round-trip SHALL hold whether the intermediate file's keywords are
   upper-case or lower-case.
3. The system SHALL continue to support round-tripping with a non-default
   value delimiter (for example a comma) without loss of content.
4. The system SHALL continue to interpret comment lines, initial comments,
   and the mapping of error commands to error columns exactly as before.
5. The system SHALL continue to parse numeric tokens (including integers,
   decimals, scientific notation, and `nan`) as it did previously.
