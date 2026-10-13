# Requirements: round-tripping stacked variables that have only the sample dimension

## Introduction

`xarray` lets a user collapse several data variables of a `Dataset` into a single
`DataArray` along one new stacked axis (`Dataset.to_stacked_array`), and later
expand that combined array back into a `Dataset`
(`DataArray.to_unstacked_dataset`). These two operations are documented as
inverses: stacking a dataset and then unstacking the result should reproduce the
original dataset.

The inverse operation is broken when the stacked variables have **only** the
sample dimension(s) — i.e. no additional per-variable dimension beyond those
that were preserved during stacking. In that situation the reconstruction fails
with a merge error ("conflicting values for variable ... on objects to be
combined") instead of returning the original dataset.

The affected code is `DataArray.to_unstacked_dataset` in
`xarray/core/dataarray.py`. It walks the variable labels held in one level of
the stacked coordinate's `MultiIndex` and, for each label, extracts that
variable's slice of the combined array to reassemble the `Dataset`. The goal is
to make the stack → unstack round trip succeed for every stackable dataset,
including the single-dimension case, while preserving the already-working
behavior for the multi-dimension case.

## Requirement 1: Round-trip works for single-dimension variables

**User story:** As a user who stacks several one-dimensional variables together,
I want to unstack them back into the original dataset, so that stacking is a
reversible operation regardless of how many dimensions my variables have.

**Acceptance criteria**

1. WHEN a `Dataset` whose data variables share exactly the sample dimension(s)
   and have no further dimensions is combined with `Dataset.to_stacked_array`
   and the resulting `DataArray` is then expanded with
   `DataArray.to_unstacked_dataset` along the stacked dimension, THEN
   `to_unstacked_dataset` SHALL return a `Dataset` that is identical to the
   original dataset (same variables, same names, same coordinates, same values,
   same dtypes).
2. WHEN `to_unstacked_dataset` reconstructs each variable in the
   single-dimension case, THEN it SHALL NOT raise a merge/"conflicting values"
   error.
3. WHEN extracting the slice for a given variable label from the combined array,
   THEN `to_unstacked_dataset` SHALL remove the selecting label's coordinate
   from the extracted slice rather than retain it as an attached scalar
   coordinate, so that the per-variable slices no longer carry a conflicting
   scalar coordinate derived from the variable-label level.
4. WHEN the reconstructed variables are assembled into the resulting `Dataset`,
   THEN none of them SHALL carry a leftover scalar coordinate corresponding to
   the stacked variable-label level or the stacked dimension itself.

## Requirement 2: Preserve existing behavior for multi-dimension variables

**User story:** As a user who already relies on stacking and unstacking
variables that have additional dimensions beyond the sample dimensions, I want
that behavior to remain unchanged, so that the fix for the single-dimension case
does not regress existing round trips.

**Acceptance criteria**

1. WHEN a `Dataset` whose data variables include one or more dimensions in
   addition to the sample dimension(s) is stacked and then unstacked, THEN
   `to_unstacked_dataset` SHALL keep returning a `Dataset` identical to the
   original dataset.
2. The system SHALL keep supporting selection of which `MultiIndex` level holds
   the variable labels via the `level` argument (by integer position or by level
   name), extracting one output variable per label found in that level.
3. WHEN the labels are read from the chosen level of the stacked coordinate,
   THEN `to_unstacked_dataset` SHALL produce one entry per label, keyed by that
   label, in the order the labels appear in that level.
4. WHILE reconstructing each variable's slice, the system SHALL reduce away the
   now-singleton axes introduced by stacking so that each reconstructed variable
   has only its intended dimensions.

## Requirement 3: Reject input that is not a stacked coordinate

**User story:** As a user, I want a clear error when I try to unstack along a
dimension that was not produced by stacking, so that misuse is reported instead
of silently mishandled.

**Acceptance criteria**

1. IF the dimension passed to `to_unstacked_dataset` is not backed by a
   `MultiIndex` (i.e. it is not a stacked coordinate), THEN the system SHALL
   raise a `ValueError` indicating that the given dimension is not a stacked
   coordinate.
