# Requirements: combine_by_coords must ignore non-varying coordinate dimensions

## Introduction

`xarray.combine_by_coords` (in `xarray/core/combine.py`) assembles a single
dataset from several input datasets by inferring, for each dimension, whether
the inputs should be concatenated along it. Datasets are grouped by their data
variables; within each group the concatenation order is inferred from the
coordinate values, the datasets are concatenated along every dimension whose
coordinate values differ between inputs, and the merged results are combined.

After concatenation, `combine_by_coords` validates that the result is well
ordered: the global index along a dimension must be monotonic (either
monotonically increasing or monotonically decreasing); otherwise the combine is
rejected with a `ValueError` that names the offending dimension.

The documented contract is that a coordinate dimension whose values are
**identical in every input dataset** (a "bystander" dimension that does not vary
between inputs, and is therefore carried through unchanged rather than
concatenated) is ignored by the combine. The defect is that the monotonicity
validation was applied to *every* coordinate dimension present in the result,
including these bystander dimensions. As a consequence, a coordinate that is
identical across all inputs but happens to be non-monotonic (e.g. a label
coordinate ordered `['a', 'c', 'b']`) caused `combine_by_coords` to raise a
`ValueError` even though nothing was concatenated along it.

The goal is to restrict the post-concatenation monotonicity validation to only
those dimensions along which the inputs were actually concatenated, so that a
non-varying (bystander) coordinate dimension never causes the combine to fail,
while genuinely concatenated dimensions are still validated exactly as before.
The affected function is `combine_by_coords` in `xarray/core/combine.py`.

## Requirement 1: Ignore non-varying coordinate dimensions during monotonicity validation

**User story:** As a user combining datasets that share an identical coordinate
whose labels are not in sorted order, I want `combine_by_coords` to succeed, so
that a coordinate which is the same in every input never has to be monotonic.

**Acceptance criteria**

1. WHEN `combine_by_coords` is given datasets whose values differ along one
   dimension but which share an identical coordinate along another dimension
   whose labels are non-monotonic, THEN `combine_by_coords` SHALL return the
   combined dataset without raising.
2. IF a coordinate dimension has identical values in every input dataset (it was
   not concatenated across the inputs), THEN `combine_by_coords` SHALL NOT
   subject that dimension to the monotonic-index requirement, regardless of
   whether its values are monotonic.
3. WHEN `combine_by_coords` returns for such inputs, THEN the shared non-varying
   coordinate in the result SHALL retain the same values, in the same order, as
   in the inputs.
4. WHEN datasets are concatenated along a varying dimension while sharing a
   non-varying coordinate, THEN the result SHALL contain the correctly
   concatenated data along the varying dimension with no loss or reordering of
   the shared coordinate's data.

## Requirement 2: Still validate monotonicity of concatenated dimensions

**User story:** As a user, I want `combine_by_coords` to keep rejecting inputs
that cannot be placed in a monotonic global order along a dimension it actually
concatenates, so that silently mis-ordered results are still prevented.

**Acceptance criteria**

1. WHEN the inputs are concatenated along a dimension whose resulting global
   index is neither monotonically increasing nor monotonically decreasing, THEN
   `combine_by_coords` SHALL raise a `ValueError` identifying that dimension.
2. IF the global index along a concatenated dimension is monotonically
   increasing OR monotonically decreasing, THEN `combine_by_coords` SHALL accept
   that dimension.
3. WHEN inputs describe an ordering along a concatenated dimension that cannot be
   made consistently monotonic, THEN `combine_by_coords` SHALL raise a
   `ValueError` rather than return a mis-ordered result.

## Requirement 3: Preserve existing combine_by_coords behavior (regression protection)

**User story:** As an existing user, I want all previously working behaviors of
`combine_by_coords` to remain unchanged, so that this fix only removes the
spurious failure and nothing else.

**Acceptance criteria**

1. WHEN `combine_by_coords` is given datasets that vary along a dimension with
   already-monotonic coordinates, THEN it SHALL concatenate them into a single
   dataset ordered by their coordinate values (independent of their order in the
   input sequence), exactly as before.
2. WHEN `combine_by_coords` is given datasets whose coordinates are monotonically
   decreasing along a concatenated dimension, THEN it SHALL still accept them and
   preserve that decreasing order.
3. WHEN `combine_by_coords` is given datasets that require no concatenation (they
   share all coordinate values and only differ in their data variables), THEN it
   SHALL merge them without raising.
4. IF a set of datasets introduces a new variable in a way concatenation cannot
   reconcile, THEN `combine_by_coords` SHALL continue to raise a `ValueError`.
5. WHEN datasets present an impossible/contradictory ordering of the coordinates
   used to infer concatenation order, THEN `combine_by_coords` SHALL continue to
   raise the same error it raised before this change.
6. The system SHALL leave the behavior of `combine_by_coords` for inputs with
   string-valued, datetime-valued, and numeric coordinates otherwise unchanged.
