# Requirements: Inspecting chunk sizes must not load lazily-backed data

## Introduction

xarray exposes chunk information through several attributes: `Dataset.chunks`,
`Dataset.chunksizes`, `DataArray.chunks`, and `DataArray.chunksizes`. For the
`Dataset` and `DataArray` collection-level attributes this information is
aggregated across the underlying variables by the helper
`get_chunksizes(variables)` in `xarray/core/common.py`, which walks each
`Variable` and, for those that are chunked, folds that variable's per-dimension
block lengths into a combined mapping.

A `Variable` holds its array behind `Variable.data` and
`Variable.chunksizes`/`Variable.chunks` (`xarray/core/variable.py`). Reading
`Variable.data` returns the underlying array only when that array is already a
"duck array" (an array-like object that xarray manipulates without converting
to numpy); otherwise `Variable.data` falls back to `Variable.values`, which
forces the array to be realized as a numpy array. For a variable that is backed
by a lazy, not-yet-loaded storage handle (for example a dataset opened from a
backend such as zarr, where data is fetched on demand), forcing realization
reads the entire array into memory — and if the backing store is unavailable or
deliberately guarded against access, that realization raises instead of
returning.

`get_chunksizes` only needs to know *whether* each variable is chunked (i.e.
whether its underlying array advertises a `chunks` attribute) and, if so, what
its chunk sizes are. Determining "is this variable chunked?" by way of a path
that can realize the array is incorrect: it defeats lazy loading and can turn a
cheap metadata inspection into a full data load, or into an error when the store
is inaccessible. The goal is to make chunk inspection a pure metadata operation
that never triggers computation or data loading, while preserving every existing
result for chunked, in-memory, and mixed datasets.

## Requirement 1: Inspecting chunk sizes must not realize lazily-backed data

**User story:** As a user who has opened a dataset lazily from a storage backend
(so its variables are not loaded into memory), I want to read the collection's
chunk information without triggering any data access, so that inspecting
`chunks`/`chunksizes` stays cheap and does not fetch or load the whole array.

**Acceptance criteria**

1. WHEN `get_chunksizes` (in `xarray/core/common.py`) processes a variable whose
   underlying array is a lazy, not-yet-realized backend handle that is not a
   duck array, THEN it SHALL determine whether that variable is chunked by
   inspecting the variable's underlying stored array object directly, and SHALL
   NOT cause that array to be realized, materialized, or otherwise read from its
   backing store.
2. WHEN a `Dataset` is opened lazily such that its variables are backed by
   storage handles that raise if any element is accessed, THEN reading
   `Dataset.chunks` SHALL return a result without accessing any variable's data
   and SHALL NOT raise.
3. WHILE none of a dataset's variables is chunked, reading `Dataset.chunks` (and
   `Dataset.chunksizes`) SHALL return an empty mapping (a mapping with no
   dimension entries, comparing equal to `{}`).
4. The determination of whether a variable is chunked SHALL depend only on
   metadata of the variable's underlying array (whether that array advertises a
   `chunks` attribute) and SHALL NOT depend on, or trigger, conversion of that
   array to a numpy array or any equivalent full realization.

## Requirement 2: Correct chunk reporting for chunked and mixed datasets is preserved

**User story:** As a user working with chunked (e.g. dask-backed) datasets, I
want `chunks`/`chunksizes` to keep reporting the same block structure as before,
so that this change fixes lazy inspection without altering any existing chunk
results.

**Acceptance criteria**

1. WHEN `get_chunksizes` processes a variable whose underlying array is chunked
   (its array advertises a `chunks` attribute), THEN it SHALL include that
   variable's per-dimension block lengths in the returned mapping, keyed by
   dimension name.
2. WHEN a chunked variable spans multiple dimensions, THEN each of that
   variable's dimensions SHALL appear in the returned mapping with the block
   lengths corresponding to that dimension.
3. WHEN two chunked variables share a dimension and report the same block
   lengths along it, THEN that dimension SHALL appear exactly once in the
   returned mapping with those block lengths.
4. IF two variables share a dimension but report differing block lengths along
   it, THEN `get_chunksizes` SHALL raise a `ValueError` reporting the
   inconsistency for that dimension.
5. WHEN a dataset contains a mixture of chunked and non-chunked variables, THEN
   the returned mapping SHALL contain entries for the dimensions of the chunked
   variables only, and SHALL omit any dimension that occurs solely on
   non-chunked variables.
6. The returned chunk mapping SHALL be an immutable (read-only) mapping from
   dimension name to a tuple of block lengths.

## Requirement 3: Consistent behavior across the collection-level chunk attributes

**User story:** As a user, I want the `Dataset` and `DataArray` chunk attributes
to share the same non-loading, correct behavior, so that inspecting chunks is
uniformly safe regardless of which object I query.

**Acceptance criteria**

1. WHEN `DataArray.chunks` or `DataArray.chunksizes` aggregates chunk
   information over its variables, THEN it SHALL use the same
   non-realizing inspection as `Dataset.chunks`/`Dataset.chunksizes` and SHALL
   NOT trigger realization of a lazily-backed variable.
2. WHEN a `Dataset` or `DataArray` has no chunked variables, THEN its
   `chunksizes` attribute SHALL return an empty mapping and its aggregation
   SHALL NOT access variable data.
3. The change SHALL be confined to how a variable's chunked-ness is inspected
   during aggregation; it SHALL NOT alter the meaning of `Variable.chunks` or
   `Variable.chunksizes` for an individual variable.
