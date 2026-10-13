# Requirements: `min_count` for reductions over more than one dimension

## Introduction

xarray's missing-value-aware reductions `sum` and `prod` (on `DataArray` and
`Dataset`) accept a `min_count` keyword: an output cell is only kept if at
least `min_count` of the entries reduced into it were actually present (not
missing); otherwise the cell is discarded and replaced with the missing-value
sentinel.

The threshold logic lives in `xarray/core/nanops.py`, in the helper
`_maybe_null_out` (called by `nansum` and `nanprod`). Historically this helper
computed the per-cell entry count from a single reduced axis and explicitly
refused any request that reduced over more than one dimension, raising a
`ValueError`. As a result, `da.sum(["dim_0", "dim_1"], min_count=1)` and the
analogous `prod` call failed even though the operation is well-defined.

The goal is to make `min_count` work for reductions over any number of
dimensions — computing the per-cell entry count as the product of the sizes of
all reduced axes — while leaving single-axis behavior, reductions without
`min_count`, and all other reductions unchanged.

## Requirement 1: Allow `min_count` with multi-dimension reductions

**User story:** As a user aggregating a DataArray, I want to pass `min_count`
while reducing over several dimensions at once, so that I can require a minimum
number of valid entries per output cell without being forced to reduce one
dimension at a time.

**Acceptance criteria**
1. WHEN `sum` or `prod` is invoked with `skipna=True` (or a `skipna` default
   that enables missing-value handling), a `min_count` value, and a set of
   reduced dimensions containing more than one dimension, THEN the reduction
   SHALL complete and return a result rather than raising an error.
2. WHEN such a multi-dimension reduction is requested, THEN the helper in
   `xarray/core/nanops.py` that applies the minimum-count threshold SHALL NOT
   raise `ValueError` (or any error) on the grounds that more than one
   dimension is being reduced.
3. WHEN the reduced axis is expressed as a tuple or list of axes, THEN the
   system SHALL treat the collection of axes as the set of reduced dimensions
   for the purpose of computing the per-cell entry count.

## Requirement 2: Correct per-cell valid-entry threshold across all reduced axes

**User story:** As a user relying on `min_count`, I want each output cell kept
or discarded based on how many valid entries were reduced into it, so that the
threshold is meaningful regardless of how many dimensions I reduce.

**Acceptance criteria**
1. WHEN the reduction retains at least one output dimension (the result is not
   collapsed to a single scalar), THEN the system SHALL compute, for each output
   cell, the total number of entries reduced into that cell as the product of
   the sizes of all reduced axes. (The criteria in this requirement govern this
   per-cell case; the whole-array scalar case is addressed in Requirement 5.)
2. WHEN the number of valid (present, non-missing) entries reduced into a
   cell — the total entries reduced into it minus the count of missing entries
   reduced into it — is less than `min_count`, THEN the system SHALL replace
   that cell's value with the missing-value fill sentinel.
3. WHEN the number of valid entries reduced into a cell is greater than or
   equal to `min_count`, THEN the system SHALL keep that cell's computed
   reduction value.
4. WHEN any cell must be replaced by the fill sentinel and the computed result
   dtype cannot hold it, THEN the system SHALL promote the result to a dtype
   that can represent the sentinel before assigning it.
5. IF the comparison of valid-entry count against `min_count` is evaluated,
   THEN the system SHALL perform it as a signed integer comparison so that the
   count of missing entries and `min_count` cannot underflow the total.

## Requirement 3: Multi-dimension result equals the equivalent sequential reduction

**User story:** As a user, I want reducing over all requested dimensions at
once to match reducing them one after another (or reducing over `...`/`None`),
so that the multi-dimension result is exactly what I would expect.

**Acceptance criteria**
1. WHEN `sum` or `prod` with `min_count` reduces over every dimension of the
   array, THEN the result SHALL be element-for-element equal (within numeric
   tolerance) to the same reduction requested over all dimensions via the
   "reduce everything" forms (`dim=...` or `dim=None`).
2. WHEN `sum` or `prod` reduces over a set of dimensions at once (without
   `min_count`), THEN the result SHALL be element-for-element equal (within
   numeric tolerance) to reducing those same dimensions one at a time in
   sequence.
3. The system SHALL preserve this equivalence for both `skipna=True` and
   `skipna=False`.

## Requirement 4: Behavior uniform across backends and dtypes

**User story:** As a user with lazy or typed arrays, I want multi-dimension
`min_count` reductions to behave the same whether my data is in memory or
chunked, and across numeric and boolean element types, so that results are
consistent.

**Acceptance criteria**
1. WHEN the underlying array is a lazily-evaluated (chunked) array, THEN the
   reduction result SHALL match the eager (in-memory) result and SHALL itself
   remain a lazily-evaluated array of the same kind.
2. WHEN the underlying array is an in-memory array, THEN the result SHALL
   remain an in-memory (non-lazy) array.
3. The system SHALL produce correct thresholded results for floating-point,
   32-bit floating-point, integer, and boolean element types.

## Requirement 5: Preserve existing single-dimension and no-`min_count` behavior

**User story:** As an existing user, I want reductions that already work to
keep working unchanged, so that this fix does not regress prior behavior.

**Acceptance criteria**
1. WHEN `sum` or `prod` with `min_count` reduces over exactly one dimension,
   THEN the system SHALL keep or discard each output cell using the same
   valid-entry threshold as before (for a single axis the product of reduced
   axis sizes equals that one axis's size).
2. WHEN a reduction over the entire array (a scalar-producing reduction) is
   requested with `min_count`, THEN the system SHALL apply whatever
   whole-array scalar `min_count` handling was already in effect before this
   change, unchanged — this fix SHALL neither newly introduce nor remove
   thresholding on the scalar-producing path (the change is confined to the
   multi-dimension per-cell path and to no longer refusing multi-dimension
   requests).
3. WHEN `sum` or `prod` is called without `min_count`, THEN the system SHALL
   apply no threshold and return the plain reduction result.
4. The system SHALL leave the results of other reductions (for example `min`,
   `max`, `mean`, `var`, `count`, `first`, `last`, cumulative sums and
   products) unchanged, including their type-promotion and all-missing-slice
   behavior.
