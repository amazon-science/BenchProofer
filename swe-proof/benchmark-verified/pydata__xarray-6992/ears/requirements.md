# Requirements — Dataset index bookkeeping for `set_index` / `reset_index`

## Introduction

After the index refactor, `xarray.Dataset` can end up in an inconsistent state
in which its set of coordinate names (`Dataset._coord_names`) is larger than its
set of stored variables (`Dataset._variables`). The class `DataVariables` (in
`xarray/core/dataset.py`) computes the number of data variables as
`len(_variables) - len(_coord_names)`; when there are more coordinate names than
variables this becomes negative, and any consumer that iterates or takes the
length of the data variables (the object `repr`, among others) raises
`ValueError: __len__() should return >= 0`.

The reproducing sequence is:

```python
ds = xr.Dataset(coords={"a": ("x", [1, 2, 3]), "b": ("x", ["a", "b", "c"])})
ds.set_index(z=["a", "b"]).reset_index("z", drop=True)
```

The root cause is faulty coordinate/variable/index bookkeeping in
`Dataset.set_index` and `Dataset.reset_index` (`xarray/core/dataset.py`), and in
the multi-index level-dropping helper `PandasMultiIndex.keep_levels`
(`xarray/core/indexes.py`). This bundle specifies the behavior these methods
must exhibit so that the class invariant "every coordinate name is also a stored
variable name" is always preserved, while the documented index-manipulation
semantics remain correct.

Throughout this document:
- a *base variable* is an ordinary (non-index) variable, i.e. the value returned
  by `Variable`/`IndexVariable.to_base_variable()`;
- a *de-indexed coordinate* is a coordinate whose index is being removed but
  whose data is being kept;
- "the container" refers to a `Dataset` (or the `Dataset` backing a
  `DataArray`).

---

## Requirement 1: Coordinate/variable invariant is always preserved

**User story:** As a user inspecting or printing a dataset after manipulating
its indexes, I want the dataset to remain internally consistent, so that the
`repr` and any other consumer of the data-variable view work without raising.

**Acceptance criteria**
1. The system SHALL maintain the invariant that the set of coordinate names is a
   subset of the set of stored variable names for every `Dataset` produced by
   `set_index` and `reset_index`.
2. WHEN the number of data variables of a resulting dataset is computed as the
   count of stored variables that are not coordinates, THEN the system SHALL
   yield a value greater than or equal to zero.
3. WHEN a dataset (or a DataArray) produced by any `set_index`/`reset_index`
   sequence is represented as text (its `repr`), THEN the system SHALL produce
   the representation without raising `ValueError`.
4. IF the reproducing sequence in the Introduction is executed, THEN the system
   SHALL complete it and produce a dataset whose textual representation succeeds.

---

## Requirement 2: `set_index` preserves de-indexed coordinates as base variables

**User story:** As a user calling `Dataset.set_index` to build an index from
some coordinates, I want other coordinates that shared the affected dimension to
survive, so that no coordinate data is silently lost.

**Acceptance criteria**
1. WHEN `set_index` builds a new index for a dimension from one or more named
   variables, THEN the system SHALL install that new index and add its
   corresponding index coordinate(s) as coordinates of the result.
2. WHEN building the new index removes a pre-existing index that had other
   associated coordinates on the same dimension, THEN the system SHALL retain
   each such de-indexed coordinate as a base variable coordinate of the result
   (same name, same dimension, same data), rather than dropping it.
3. The system SHALL leave every retained de-indexed coordinate as a coordinate
   (its name present in both the coordinate names and the stored variables).
4. WHEN `set_index` is called with `x=[<levels>]` on a dataset whose dimension
   `x` currently carries a multi-index over some level coordinates and also
   carries additional coordinates on `x`, THEN the system SHALL produce a
   dataset whose `x` is the new multi-index over the requested levels, and in
   which the previously-indexed level coordinates that are no longer part of any
   index appear as ordinary (base variable) coordinates on `x`.
5. The system SHALL preserve the existing coordinate-ordering behavior of
   `set_index` (a dimension coordinate being redefined SHALL keep its position),
   so that results equal to the expected datasets are produced.

---

## Requirement 3: `reset_index` without `drop` converts index coordinates to base variables

**User story:** As a user calling `reset_index` to drop an index but keep the
data, I want the affected coordinates to remain as plain coordinates, so that
their values and attributes are preserved and no phantom coordinate is left
behind.

**Acceptance criteria**
1. WHEN `reset_index(name)` is called with `drop=False` on a plain (single,
   non-multi) dimension index, THEN the system SHALL remove that index and
   retain the corresponding coordinate as a base variable coordinate with the
   same name and data.
2. The system SHALL make the retained coordinate compare equal to the original
   coordinate converted to its base variable form (equivalent to
   `to_base_variable()`), i.e. it SHALL no longer be an index variable but SHALL
   carry the same values.
3. WHEN the reset coordinate carried attributes, THEN the system SHALL preserve
   those attributes on the retained base variable coordinate.
4. WHEN an index is reset, THEN the system SHALL remove that index from the
   dataset's indexes so that the reset name is no longer among the indexed
   coordinates.
5. The system SHALL NOT leave any name in the coordinate names that is absent
   from the stored variables as a result of the reset.

---

## Requirement 4: `reset_index` with `drop=True` removes the coordinate and its now-unused dimension

**User story:** As a user calling `reset_index(..., drop=True)`, I want both the
lookup index and its coordinate fully removed, so that neither the coordinate
nor an orphaned dimension lingers.

**Acceptance criteria**
1. WHEN `reset_index(name, drop=True)` is called on a plain dimension index,
   THEN the system SHALL remove the index and SHALL remove the corresponding
   coordinate name from BOTH the coordinate names and the stored variables.
2. IF, after dropping such a coordinate, its dimension is no longer used by any
   remaining variable, THEN the system SHALL leave the result with no such
   dimension (the dimension SHALL disappear from the result's dimensions).
3. WHEN dropping an index removes coordinates that were previously only kept to
   satisfy the coordinate/variable invariant, THEN the system SHALL not require
   a separate explicit drop of those coordinates by the caller to obtain a
   consistent result.

---

## Requirement 5: `reset_index` on multi-index levels

**User story:** As a user resetting one or more levels of a multi-index, I want
the remaining levels handled correctly, so that the surviving index and
coordinates match documented, backward-compatible behavior.

**Acceptance criteria**
1. WHEN `reset_index` targets a strict subset of the levels of a multi-index and
   at least one level remains, THEN the system SHALL replace the multi-index
   with a new index built over the remaining levels.
2. IF exactly one level remains after such a reset, THEN the system SHALL reduce
   the multi-index to a plain single index over that dimension, and SHALL rename
   the surviving level coordinate to the dimension name (so the remaining
   indexed coordinate carries the dimension name and is a plain `PandasIndex`).
3. WHEN a level is reset out of a multi-index with `drop=False`, THEN the system
   SHALL retain that level's coordinate as a base variable coordinate (same
   data); WHEN reset with `drop=True`, THEN the system SHALL remove that level's
   coordinate entirely.
4. WHEN `reset_index` targets the multi-index dimension itself (the dimension
   name), THEN the system SHALL remove the entire multi-index and SHALL always
   remove the multi-index dimension variable; with `drop=False` it SHALL retain
   every level coordinate as a base variable coordinate, and with `drop=True` it
   SHALL remove every level coordinate as well.
5. WHEN `reset_index` is given multiple names that refer to the same underlying
   (multi-)index, THEN the system SHALL process that index only once and SHALL
   produce the same result as if it had been named once.
6. WHEN a full multi-index is reset with `drop=False`, THEN the system SHALL NOT
   re-introduce a coordinate named after the multi-index dimension holding the
   packed multi-index values; only the (converted) level coordinates SHALL
   remain, and the result SHALL have no index.

---

## Requirement 6: Regression protection for existing behavior

**User story:** As a maintainer, I want the surrounding dataset, coordinate,
repr, selection, and groupby behaviors to keep working, so that the fix does not
regress unrelated functionality.

**Acceptance criteria**
1. The system SHALL keep producing correct `repr` output for DataArrays and
   Datasets, including those backed by multi-indexes.
2. The system SHALL keep the existing behavior of `set_index` for the ordinary
   cases (building single and multi indexes, dimension mismatch raising
   `ValueError`, and appending).
3. The system SHALL keep `reset_index` raising `ValueError` when asked to reset
   a name that is not a coordinate with an index.
4. WHEN a grouping operation internally resets an index with `drop=True` on a
   dimension whose other coordinates are no longer needed, THEN the system SHALL
   already produce a result free of those coordinates without an additional
   explicit coordinate-drop step.
5. The system SHALL keep coordinate access, indexing, selection, alignment, and
   multi-index level behaviors (e.g. `reorder_levels`) unchanged for all cases
   outside the corrected bookkeeping paths.
