# Requirements: label-based `.loc` selection must not collide with selection option names

## Introduction

`DataArray.loc` (implemented by the `_LocIndexer` helper in
`xarray/core/dataarray.py`) supports label-based selection with a dictionary
that maps dimension names to labels, e.g. `da.loc[dict(dim1="x", dim2="a")]`.
Under the hood the helper forwards the request to `DataArray.sel`, whose
signature accepts an `indexers` mapping together with several optional matching
parameters — `method`, `tolerance`, and `drop`.

When a dimension is named identically to one of those optional parameters (for
example a dimension literally called `"method"`), forwarding the dictionary by
unpacking it into keyword arguments causes the dimension entry to be consumed as
a selection option instead of as a dimension selector. The label value is then
mis-interpreted (e.g. as a fill-method mode), producing a spurious error such as
`ValueError: Invalid fill method ...` rather than performing the selection.

The goal is to make label-based `.loc` selection depend only on the *contents*
of the indexer mapping (which dimensions map to which labels), never on whether
a dimension's name happens to coincide with the name of an optional matching
parameter of the underlying selection method. This affects
`_LocIndexer.__getitem__` in `xarray/core/dataarray.py`.

## Requirement 1: Dimension names that collide with selection option names must still select

**User story:** As a user indexing a `DataArray` with `.loc`, I want to select
along a dimension regardless of its name, so that a dimension called `"method"`
(or any other reserved-looking name) behaves like any other dimension.

**Acceptance criteria**

1. WHEN `.loc` is indexed with a dictionary-like key whose keys are dimension
   names and whose values are labels, THEN the indexer SHALL perform label-based
   selection along each named dimension using the corresponding label value.
2. WHEN one of the dimension names in the indexing dictionary equals the name of
   an optional matching parameter of the selection method (`"method"`,
   `"tolerance"`, or `"drop"`), THEN the indexer SHALL treat that entry as an
   ordinary dimension selector and SHALL NOT interpret its label value as a
   value for that matching parameter.
3. WHEN `.loc` is indexed with a dictionary that includes a dimension named
   `"method"` mapped to one or more labels, THEN the operation SHALL return the
   subarray selected by those labels and SHALL NOT raise an error about an
   invalid fill/matching method.
4. WHEN `.loc` selection is invoked through the dictionary form, THEN the
   optional matching parameters (inexact-match mode, numeric tolerance, and the
   coordinate-drop flag) SHALL remain at their defaults, i.e. none of them SHALL
   be populated from entries of the indexing dictionary.
5. WHEN a `.loc` dictionary key requests a list of labels along a dimension
   (rather than a single scalar label), THEN the indexer SHALL return a subarray
   that retains that dimension with exactly the requested labels, ordered as
   they appear in the requested list (not reordered to match the underlying
   coordinate).
6. IF the indexing dictionary omits some of the array's dimensions, THEN the
   indexer SHALL select only along the dimensions present in the dictionary and
   SHALL leave the omitted dimensions unindexed (returned in full).

## Requirement 2: Preserve existing `.loc` selection behavior for ordinary dimension names

**User story:** As a user of `.loc`, I want all previously working selection
forms to keep working, so that the fix for reserved-name dimensions does not
regress normal indexing.

**Acceptance criteria**

1. WHEN `.loc` is indexed with a dictionary of ordinary dimension names mapped
   to scalar labels, THEN the indexer SHALL return the element(s) selected at
   those labels, exactly as before.
2. WHEN `.loc` is indexed with a non-dictionary key (a scalar label, a slice, a
   sequence, or a tuple of such per-dimension keys, possibly including an
   ellipsis), THEN the indexer SHALL expand the key positionally across the
   array's dimensions in order and perform the corresponding label-based
   selection.
3. WHEN `.loc` is indexed with a single label on a one-dimensional array,
   including a boolean-labeled coordinate, THEN the indexer SHALL return the
   element at that label.
4. The system SHALL keep label-based `.loc` selection consistent with the result
   of the equivalent explicit label-selection call, so that `da.loc[mapping]`
   and selecting `da` by the same dimension→label mapping produce equal results.
5. The system SHALL preserve the coordinates and dimension names of the selected
   subarray, dropping only the dimensions that are reduced away by scalar-label
   selection.
