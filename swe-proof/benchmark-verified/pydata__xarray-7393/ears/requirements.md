# Requirements: preserve coordinate dtype when reading a level of a composite index

## Introduction

When several one-dimensional coordinates are combined into a composite
(multi-level) index — for example by stacking dimensions on an `xarray.Dataset`
or `DataArray` — the individual coordinate that is later read back out must keep
the element data type it was built from. In the affected code, a wrapper class
in `xarray/core/indexing.py` (the pandas multi-index indexing adapter,
`PandasMultiIndexingAdapter`, a subclass of `PandasIndexingAdapter`) exposes one
labelled level of a `pandas.MultiIndex` as a NumPy array through its
`__array__` method.

The observed defect: extracting a single level's values from the underlying
`pandas.MultiIndex` (via `get_level_values`) can silently widen the numeric data
type (e.g. from a 32-bit integer to a 64-bit integer, or from a 32-bit float to
a 64-bit float), because the raw array returned by the underlying machinery
carries its own, possibly widened, data type. As a result, building a
composite index and reading a coordinate back changes that coordinate's
`dtype`, so a
round-trip comparison of the original coordinate's dtype against the
reconstructed coordinate's dtype fails.

The goal is that converting a level of the composite-index wrapper to an array
re-presents the values at the data type the wrapper was constructed to carry
(its stored original data type), rather than at the raw level array's data type,
while leaving the element values and all other behaviors unchanged.

## Requirement 1: Default the conversion data type to the wrapper's stored dtype

**User story:** As a user reading a coordinate out of a stacked (multi-index)
dataset, I want the array conversion to fall back to the coordinate's original
data type when I do not request one, so that the coordinate's dtype is preserved
across a stack round-trip.

**Acceptance criteria**

1. The `PandasIndexingAdapter`/`PandasMultiIndexingAdapter` wrapper SHALL expose
   a stored element data type (its `dtype` property) that reflects the data type
   of the values it was constructed from.
2. WHEN `__array__` is invoked on the multi-index wrapper with no explicit
   target data type (the data-type argument is absent or `None`), THEN the
   wrapper SHALL use its stored data type as the effective data type for the
   conversion.
3. WHEN `__array__` is invoked with an explicit target data type, THEN the
   wrapper SHALL use that requested data type as the effective data type.

## Requirement 2: Preserve dtype when converting a selected level to an array

**User story:** As a user of stacked coordinates, I want a single labelled level
read out of the composite index to carry the wrapper's data type, so that the
values are unchanged but the data type is not widened.

**Acceptance criteria**

1. WHILE the wrapper is bound to a specific level of the composite index (its
   level identifier is set / not `None`), WHEN `__array__` is invoked, THEN the
   wrapper SHALL return the values of that level from the underlying composite
   index re-presented with the effective data type determined in Requirement 1.
2. IF the raw values obtained for the selected level carry a wider or otherwise
   different data type than the effective data type, THEN the returned array
   SHALL have the effective data type, not the raw values' data type.
3. WHEN a selected level is converted to an array, THEN the returned array's
   element values SHALL equal the level's underlying values (only the data type
   is adjusted; the in-range values are carried through unchanged).
4. WHEN a coordinate created from an integer or floating-point array is combined
   into a composite index and then read back as an array, THEN the data type of
   the read-back array SHALL equal the data type of the original coordinate's
   values.

## Requirement 3: Preserve existing behavior for the non-level case and other operations

**User story:** As a maintainer, I want the dtype fix to be scoped to the
level-conversion path, so that unrelated indexing behavior is unchanged.

**Acceptance criteria**

1. WHILE the multi-index wrapper is not bound to a specific level (its level
   identifier is `None`), WHEN `__array__` is invoked, THEN the wrapper SHALL
   defer to the base (non-level) array conversion using the effective data type,
   producing the same result the base conversion produces.
2. The base `PandasIndexingAdapter` array conversion SHALL continue to default
   an absent target data type to the stored data type and to return the
   underlying index values at that data type.
3. The wrapper SHALL preserve its existing scalar-conversion behavior for a
   selected level, extracting the level's component from a tuple item before
   converting it.
4. WHEN the wrapper is indexed to produce another wrapper of the same kind, THEN
   the resulting wrapper SHALL retain the same bound level identifier.
5. The wrapper SHALL preserve its existing representation, transpose, copy, and
   dtype-reporting behavior unchanged.
6. Existing composite-index operations built on this wrapper — constructing an
   index from variables, stacking and unstacking, concatenating, joining,
   selecting and positional indexing, reindexing, rolling, renaming, copying,
   equality comparison, and conversion to a pandas index — SHALL continue to
   behave as before.
