# Requirements: Clear TimeSeries required-column validation error message

## Introduction

`astropy.timeseries` provides `TimeSeries`-style tables built on
`BaseTimeSeries` (in `astropy/timeseries/core.py`). Such tables declare an
ordered set of mandatory leading columns via the `_required_columns` attribute
(for `TimeSeries` this normally begins with `time`, but callers may extend it,
e.g. to `['time', 'flux']`). After any column-mutating operation
(`add_column`, `add_columns`, `keep_columns`, `remove_column`,
`remove_columns`, `rename_column`), the private method
`BaseTimeSeries._check_required_columns` re-validates that the table's leading
columns still match the required set, and raises `ValueError` when they do not.

The defect: the validation error message was written assuming a single required
column. It always reported only the first required name (`required_columns[0]`)
and only the first actual column name (`self.colnames[0]`). When a table has
more than one required column, this produces a misleading message such as
`expected 'time' as the first columns but found 'time'` — the offending
column (e.g. a removed `flux`) is invisible and the "expected" vs "found" sides
look identical.

The goal is to make `_check_required_columns` emit an error message that
accurately describes the full set of required leading columns and the actual
leading columns present, while preserving every existing behavior for the
single-required-column case and for all non-error paths that other operations
rely on.

## Requirement 1: Accurate mismatch message for multiple required columns

**User story:** As a developer using a `TimeSeries` with more than one required
column, I want the validation error to name the full expected column set and
the actual leading columns, so that I can immediately see which required column
is missing or misplaced.

**Rendering convention.** Both the expected side and the found side are rendered
by the same value-formatting rule, applied independently to each side's own
value: a value that has no length (a bare scalar) is shown as that scalar in
single quotes; a value of length exactly one is shown as its single element in
single quotes with no surrounding brackets; a value of length two or more is
shown as a bracketed, comma-separated list of quoted names matching Python's
`str()` of that list of strings. Crucially, the bracket-vs-quote decision for
each side depends on the number of elements in *that side's own value*, not on
the number of required columns.

**Acceptance criteria**

1. WHEN `_check_required_columns` runs with required-column checking enabled, a
   non-`None` required-column set, the table not in the relaxed state, the
   table having at least one column, and the table's leading columns (the first
   *k* columns, where *k* is the number of required columns) not equal to the
   required columns, THEN the method SHALL raise `ValueError`.
2. WHEN that mismatch `ValueError` is raised and the required-column set
   contains two or more names, THEN the message SHALL render the expected side
   as the full list of required column names via the rendering convention:
   because two or more names are required, this is a bracketed, comma-separated
   list of quoted names (e.g. `['time', 'flux']`), rather than only the first
   required name.
3. WHEN that mismatch `ValueError` is raised, THEN the message SHALL render the
   found side as the table's actual leading columns truncated to the number of
   required columns (rather than only the first actual column name), formatted
   by the rendering convention applied to that truncated slice: if the slice
   contains two or more columns it is a bracketed, comma-separated list of
   quoted names; if the slice contains exactly one column it is that single
   name in single quotes with no surrounding brackets. The found-side form
   therefore tracks how many actual leading columns remain, which may be fewer
   than the number of required columns. For example, when a `TimeSeries`
   requires `['time', 'flux']` and the `flux` column is removed so that only
   the leading `time` column remains, the found side renders as the single
   quoted name `'time'` (not a bracketed list), yielding
   `expected ['time', 'flux'] as the first columns but found 'time'`.
4. WHEN two or more columns are required, THEN the message SHALL use the plural
   noun form "columns" (i.e. "as the first columns"); the plural form is keyed
   on the number of required columns, independently of how the found side
   renders.
5. The system SHALL construct the mismatch message in the form
   `"<ClassName> object is invalid - expected <expected> as the first
   column<plural> but found <found>"`, where `<ClassName>` is the object's
   class name, `<expected>` and `<found>` are rendered as described above, and
   `<plural>` is `s` when two or more columns are required and empty otherwise.

## Requirement 2: Preserve the single-required-column message

**User story:** As a maintainer, I want the existing behavior for the common
single-required-column case to be unchanged, so that existing callers and their
expectations continue to hold.

**Acceptance criteria**

1. WHEN the mismatch `ValueError` is raised and the required-column set contains
   exactly one name, THEN the message SHALL render the expected side as that one
   column name wrapped in single quotes with no surrounding brackets (e.g.
   `'time'`).
2. WHEN the mismatch `ValueError` is raised and the required-column set contains
   exactly one name, THEN the message SHALL render the found side as the single
   actual leading column name wrapped in single quotes with no surrounding
   brackets (e.g. `'flux'`).
3. WHEN exactly one column is required, THEN the message SHALL use the singular
   noun form "column" (i.e. "as the first column").
4. IF a `TimeSeries` requires only `time` and its first column is some other
   name, THEN removing/renaming such that the leading column differs SHALL raise
   `ValueError` whose message reads
   `TimeSeries object is invalid - expected 'time' as the first column but
   found '<actual first column>'`.

## Requirement 3: Preserve non-mismatch validation behavior

**User story:** As a maintainer, I want every other branch of the required-column
check to behave exactly as before, so that initialization, reading, folding, and
other column operations that depend on this method are unaffected.

**Acceptance criteria**

1. IF required-column checking is disabled (the enabled flag is false), THEN
   `_check_required_columns` SHALL return without raising and without altering
   any state.
2. IF the required-column set is `None`, THEN `_check_required_columns` SHALL
   return without raising.
3. WHEN checking is enabled, the table is not relaxed, a required-column set is
   present, and the table has zero columns, THEN the method SHALL raise
   `ValueError` with a message of the form
   `"<ClassName> object is invalid - expected '<first required>' as the first
   column<plural> but time series has no columns"`, keeping the original
   single-name wording of the no-columns branch.
4. WHEN checking is enabled and the table's leading columns equal the required
   columns, THEN `_check_required_columns` SHALL NOT raise.
5. WHILE the table is in the relaxed state, the method SHALL compare against the
   required columns truncated to the current number of columns, and IF the full
   required-column set then equals the table's corresponding leading columns,
   THEN the method SHALL clear the relaxed state (set it to false).
6. The system SHALL continue to invoke `_check_required_columns` automatically
   after each column-related method (`add_column`, `add_columns`,
   `keep_columns`, `remove_column`, `remove_columns`, `rename_column`) so that
   valid `TimeSeries` construction, data initialization, reading, and folding
   operations succeed unchanged and only genuinely invalid column states raise.
