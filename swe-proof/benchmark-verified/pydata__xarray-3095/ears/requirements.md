# Requirements: Preserve index dtype (including fixed-width unicode) when copying

## Introduction

An `xarray` coordinate is stored internally as an `IndexVariable` whose data is a
`PandasIndexAdapter` (in `xarray/core/indexing.py`). That adapter wraps a
`pandas.Index` while separately **recording** the element dtype the variable
should report. This stored dtype can be finer-grained than the dtype pandas
would re-derive from the wrapped index: in particular a fixed-width unicode
dtype (e.g. `<U3`) is recorded on the adapter even though pandas stores such
values in an `object`-dtype `Index`. `PandasIndexAdapter.__init__` therefore
takes an optional `dtype` argument and, when it is supplied, honors it instead
of inferring one from the wrapped index.

`IndexVariable.copy(deep=...)` (in `xarray/core/variable.py`) previously built
the copy's data by constructing a brand-new `PandasIndexAdapter` from
`self._data.array.copy(deep=True)` **without** forwarding the recorded dtype.
The new adapter then re-derived its dtype from the wrapped index, so a
fixed-width unicode coordinate came back as `object`. This is the regression
reported for `Dataset.copy(deep=True)`, `DataArray.copy(deep=True/False)`,
`copy.copy()`, and `copy.deepcopy()`: coordinate indices with dtype `<U*` were
silently widened to `object`.

The goal is that copying an index-backed variable preserves the variable's
**recorded** dtype exactly (never re-deriving it from the wrapped index), for
deep and shallow copies alike, while all other copy behavior — value equality,
attributes/dimensions, deep-vs-shallow data sharing for ordinary variables, and
copies driven by a replacement `data` array — is preserved unchanged.

## Requirement 1: Copying an index variable preserves its recorded dtype

**User story:** As a user who builds a Dataset/DataArray with a fixed-width
unicode (string) coordinate, I want copies of it to keep the same dtype, so that
`copy`, `copy(deep=True)`, `copy.copy()` and `copy.deepcopy()` do not silently
turn my `<U*` index into an `object` index.

**Acceptance criteria**

1. WHEN `IndexVariable.copy` is called (with either `deep=True` or `deep=False`)
   and no replacement `data` is supplied, THEN the returned variable SHALL report
   the same `dtype` as the original variable.
2. WHEN the original index variable's recorded dtype is a fixed-width unicode
   (string) dtype, THEN the copy SHALL retain that fixed-width unicode dtype and
   SHALL NOT widen it to `object`.
3. WHEN an index variable with any dtype (for example a floating-point, integer,
   or fixed-width unicode dtype) is copied, THEN the copy's dtype SHALL equal the
   original's dtype rather than a dtype re-derived from the wrapped `pandas.Index`.
4. The dtype carried onto the copy SHALL be the dtype recorded on the original's
   underlying index adapter, so that copying never re-infers the element type
   from the wrapped index values.

## Requirement 2: The index adapter copies itself while preserving its dtype

**User story:** As a maintainer, I want the `PandasIndexAdapter` to know how to
produce a copy of itself that keeps its stored dtype, so that any code copying
an index-backed variable gets a faithful copy without re-inferring the dtype.

**Acceptance criteria**

1. The system SHALL provide, on `PandasIndexAdapter`, a way to produce a copy of
   the adapter that reports the same dtype as the original adapter.
2. WHEN a deep copy of the adapter is requested, THEN the resulting adapter SHALL
   wrap a duplicated copy of the underlying index (not sharing the original's
   backing storage), while reporting the same dtype and the same element values.
3. WHEN a shallow copy of the adapter is requested, THEN the resulting adapter
   SHALL report the same dtype and the same element values as the original.
4. WHEN the adapter is copied, THEN the resulting adapter SHALL carry over the
   dtype recorded on the original adapter rather than a dtype derived afresh from
   the wrapped index.

## Requirement 3: Copy remains value- and metadata-faithful

**User story:** As a user, I want a copied variable to compare equal to the
original and keep all its structure, so that copying changes nothing but
identity/backing storage.

**Acceptance criteria**

1. WHEN an index variable is copied without a replacement `data`, THEN the copy
   SHALL have the same dimension names, the same attributes, and the same element
   values as the original, and SHALL be of the same type as the original.
2. WHEN an index variable is copied, THEN the copy SHALL be identical to the
   original under xarray's identity comparison (equal dims, values, dtype, and
   attributes).
3. WHEN a variable is copied via the standard library `copy.copy` or
   `copy.deepcopy`, THEN the result SHALL be identical to the original in the same
   sense (including preserving the recorded dtype).

## Requirement 4: Preserve existing copy behavior (regression protection)

**User story:** As a maintainer, I want every other copy behavior to work exactly
as before, so that ordinary (non-index) variables, deep-vs-shallow data sharing,
and copies with replacement data are unaffected by this fix.

**Acceptance criteria**

1. WHEN an ordinary (non-index) `Variable` is deep-copied (no replacement
   `data`), THEN the copy's underlying array SHALL be a distinct buffer from the
   original's (the two SHALL NOT share backing storage), and the copy SHALL keep
   the same dtype, values, dimensions, and attributes.
2. WHEN an ordinary (non-index) `Variable` is shallow-copied (`deep=False`, no
   replacement `data`), THEN the copy's underlying array SHALL share backing
   storage with the original, and the copy SHALL keep the same dtype, values,
   dimensions, and attributes.
3. WHEN an ordinary or index variable of floating-point, integer, or fixed-width
   unicode dtype is copied with either `deep=True` or `deep=False`, THEN the copy
   SHALL preserve that dtype and compare identical to the original.
4. WHEN `copy` is called with a replacement `data` argument, THEN the new object
   SHALL use that data, SHALL keep the original's dimensions, attributes, and
   encoding, and SHALL raise an error IF the replacement data's shape does not
   match the original's shape.
5. The `deep` flag SHALL default such that a copy is a deep copy unless the caller
   requests otherwise, preserving the pre-existing default behavior of the copy
   operation.
