# Requirements: Preserve coordinates through `Coarsen.construct`

## Introduction

`xarray.core.rolling.Coarsen.construct` reshapes a coarsening dimension into two
new dimensions (an "outer" and a "window" dimension) and returns a reshaped
`DataArray` or `Dataset`. The method is reached through the public
`obj.coarsen(...).construct(...)` API on both `DataArray` and `Dataset` objects.

A defect exists in how the method decides which names are coordinates of the
result. When the input object carries **non-dimensional coordinates** (variables
that are marked as coordinates but are not themselves dimension coordinates of a
reshaped dimension), `construct` demotes them to ordinary data variables in the
result. The expected behavior is that the coordinate/data-variable classification
of every variable is preserved: anything that was a coordinate before the call
remains a coordinate afterward.

The goal is to make `Coarsen.construct` preserve the full coordinate set while
keeping all of its existing reshaping, attribute-handling, and input-validation
behavior intact.

## Requirement 1: Preserve all pre-existing coordinates as coordinates

**User story:** As a user reshaping data with `coarsen(...).construct(...)`, I
want every variable that was a coordinate on the input to remain a coordinate on
the result, so that reshaping does not silently reclassify my coordinates as data
variables.

**Acceptance criteria**
1. WHEN `Coarsen.construct` is called on an object that has one or more variables
   marked as coordinates, THEN the returned object SHALL classify each of those
   names as a coordinate of the result.
2. WHEN `Coarsen.construct` is called on an object that has a non-dimensional
   coordinate (a coordinate that is not the dimension coordinate of any dimension
   being reshaped), THEN the returned object SHALL keep that non-dimensional name
   as a coordinate and SHALL NOT move it into the set of data variables.
3. The set of names that are coordinates of the result SHALL equal the set of
   names that were coordinates of the input; no prior coordinate SHALL be dropped
   from the coordinate set, and no name that was a data variable SHALL be promoted
   to a coordinate.
4. IF a coordinate is unrelated to any dimension being reshaped, THEN it SHALL
   still be a coordinate of the result, regardless of which dimensions are
   reshaped.

## Requirement 2: Preserve coordinates for both DataArray and Dataset callers

**User story:** As a user of either `DataArray.coarsen` or `Dataset.coarsen`, I
want the coordinate-preservation guarantee to hold in both cases, so that the API
behaves consistently across container types.

**Acceptance criteria**
1. WHEN `Coarsen.construct` is invoked on a `DataArray` that carries additional
   coordinates, THEN the returned `DataArray` SHALL retain those names as
   coordinates.
2. WHEN `Coarsen.construct` is invoked on a `Dataset` that carries coordinates,
   THEN the returned `Dataset` SHALL retain those names as coordinates.
3. WHEN the same input carrying a coordinate is reshaped as a `Dataset` and as a
   `DataArray` derived from it, THEN the list of coordinate names on each result
   SHALL be the same as the list of coordinate names on the corresponding input.

## Requirement 3: Preserve existing reshaping, data, and attribute behavior (regression)

**User story:** As an existing user of `Coarsen.construct`, I want the reshaping
and attribute semantics I already rely on to keep working unchanged, so that the
coordinate fix does not alter any other observable output.

**Acceptance criteria**
1. WHEN a dimension is coarsened and reshaped via `construct`, THEN each affected
   variable SHALL have the reshaped dimension replaced by the two new dimension
   names, and SHALL keep the original reshaped data values in the reshaped layout.
2. WHEN a variable does not depend on any reshaped dimension, THEN that variable
   SHALL be carried through to the result unchanged.
3. WHEN `keep_attrs` is unset or true, THEN the result SHALL retain the
   object-level attributes and each variable's attributes.
4. WHEN `construct` is called with `keep_attrs=False`, THEN the result's
   object-level attributes SHALL be empty and each result variable's attributes
   SHALL be empty.
5. WHEN a dimension coordinate of a reshaped dimension exists on the input, THEN
   that name SHALL remain a coordinate of the result (reshaped into the two new
   dimensions).
6. The system SHALL accept the window-dimension specification both as a single
   mapping argument and as keyword arguments, producing identical results for
   equivalent specifications.

## Requirement 4: Preserve input validation (regression)

**User story:** As a user who may pass invalid arguments to `construct`, I want
clear errors on invalid input, so that mistakes are caught rather than silently
mishandled.

**Acceptance criteria**
1. IF no window-dimension specification is provided, THEN `construct` SHALL raise
   a `ValueError`.
2. IF the specification names a dimension that is not among the dimensions being
   coarsened, THEN `construct` SHALL raise a `ValueError`.
3. IF a dimension being coarsened is not covered by the specification, THEN
   `construct` SHALL raise a `ValueError`.
4. IF the new-dimension names for a coarsening dimension are not given as exactly
   two names (for example given as a single string or a single-element sequence),
   THEN `construct` SHALL raise a `ValueError`.
