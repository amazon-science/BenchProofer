# Requirements: `Dataset.merge` must accept a `DataArray` argument

## Introduction

The `merge` method of `xarray.Dataset` (defined in `xarray/core/dataset.py`)
lets a user combine another object's variables into the dataset. The top-level
function `xarray.merge([...])` (in `xarray/core/merge.py`) already accepts a
`DataArray` among its inputs: it coerces a named `DataArray` into its
equivalent one-variable dataset before merging. The `Dataset.merge` method did
not perform this coercion, so passing a `DataArray` to `ds.merge(da)` reached
the internal merge machinery (`dataset_merge_method` → `merge_core` →
`coerce_pandas_values`), which iterates the second operand as a mapping and
fails with `AttributeError: 'DataArray' object has no attribute 'items'`.

The goal is to make the `Dataset.merge` **method** behave consistently with the
top-level `xarray.merge` **function** when the merged-in object is a
`DataArray`, without changing any of the existing behavior for the objects the
method already accepts (another `Dataset`, or a mapping of variables). The
affected code is the `merge` method on `Dataset` in `xarray/core/dataset.py`;
the coercion it must reuse is the one `DataArray` already provides for
converting itself into a single-variable dataset, the same coercion the
top-level `merge` function applies.

## Requirement 1: Merging a named DataArray via the Dataset method

**User story:** As a user holding a `Dataset`, I want to call
`ds.merge(da)` with a named `DataArray` argument, so that I can fold that array
into my dataset just as easily as with the top-level `merge` function.

**Acceptance criteria**

1. WHEN `Dataset.merge` is called with a `DataArray` as the object to merge,
   THEN the method SHALL treat that argument as its equivalent one-variable
   dataset (the array's data stored under the array's name, together with the
   array's coordinates) and SHALL complete without raising `AttributeError`.
2. WHEN `Dataset.merge` is called with a `DataArray` as the object to merge,
   THEN the merged data content of the returned `Dataset` — its data
   variables, coordinates, dimensions, values, and dtypes — SHALL equal the
   corresponding content of the result of passing the calling dataset and that
   same `DataArray` to the top-level `xarray.merge` function; the returned
   dataset SHALL additionally retain the calling dataset's own attributes
   (the method reflects the merged object into the caller rather than building
   a fresh attribute-less dataset).
3. WHEN a scalar (dimension-less) named `DataArray` is merged into a dataset
   that already contains other scalar variables, THEN the resulting dataset
   SHALL contain both the pre-existing variables and a new data variable named
   after the `DataArray`, carrying the array's value.
4. IF the `DataArray` passed to `Dataset.merge` has no name, THEN the method
   SHALL raise the same error that converting an unnamed `DataArray` to a
   dataset raises, rather than silently producing an unnamed variable.

## Requirement 2: Preserve existing merge behavior for datasets and mappings

**User story:** As an existing user of `Dataset.merge`, I want every currently
supported argument type and option to keep working exactly as before, so that
adding `DataArray` support introduces no regression.

**Acceptance criteria**

1. WHEN `Dataset.merge` is called with another `Dataset` as the object to
   merge, THEN the method SHALL merge the two datasets and SHALL produce the
   same result as before this change.
2. WHEN `Dataset.merge` is called with a mapping (for example a `dict`) of
   variable names to values, THEN the method SHALL merge those variables into
   the dataset unchanged, including entries whose values are `DataArray`
   objects within the mapping.
3. The system SHALL continue to honor the `compat`, `join`, `overwrite_vars`,
   and `fill_value` parameters of `Dataset.merge` with their existing meaning
   and defaults, applying them to the merged object regardless of whether that
   object was supplied as a `Dataset`, a mapping, or a `DataArray`.
4. WHEN two objects being merged hold conflicting values for a shared variable
   under the effective `compat` setting, THEN the method SHALL raise a
   `MergeError`.
5. WHEN objects being merged have indexes that cannot be aligned under the
   effective `join` setting, THEN the method SHALL raise an alignment error
   rather than returning a malformed result.
6. WHEN `Dataset.merge` is given an object that is neither a `Dataset`, a
   mapping, nor a `DataArray`, THEN the merge SHALL raise an error rather than
   silently producing a result; the change adds `DataArray` coercion only and
   does not introduce any new validation message for such objects, so the
   error raised remains whatever the internal merge machinery already produced
   for an unsupported operand.
