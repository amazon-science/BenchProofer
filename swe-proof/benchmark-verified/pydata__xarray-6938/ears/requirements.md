# Requirements: converting a variable to its indexed form must not alias the source

## Introduction

In `xarray`, an array-like variable object can be converted into its
"indexed" form (an index-backed one-dimensional coordinate variable) and into a
plain base variable. These conversions are provided by the methods
`Variable.to_index_variable()` / `Variable.to_base_variable()` (in
`xarray/core/variable.py`) and their overrides on the `IndexVariable`
subclass.

A defect existed where calling the index-form conversion on an object that was
*already* an index variable returned the very same object rather than an
independent one. Because the caller then mutates the returned object in place
(for example, reassigning its dimension names), those mutations leaked back into
the original object. This surfaced through `Dataset.swap_dims()` (in
`xarray/core/dataset.py`), which converts variables to their indexed form and
then rewrites their dimension names — corrupting the input dataset's variables
as a side effect.

The goal is to make these conversions always yield an object that is safe to
mutate without affecting the source, and to guarantee that `swap_dims()` leaves
its input object unchanged, while preserving all existing conversion semantics
(the resulting object's dimension names, underlying data, attributes, and
encoding).

## Requirement 1: Index-form conversion returns an independent object

**User story:** As a user converting a variable to its indexed form, I want the
returned object to be independent of the original, so that later in-place edits
to the returned object cannot corrupt the object I converted.

**Acceptance criteria**

1. WHEN the index-form conversion method is invoked on an object that is already
   an index variable, THEN the method SHALL return an object that is not the
   same object as the receiver (a distinct instance).
2. WHEN the index-form conversion method is invoked on an object that is already
   an index variable, THEN the returned object SHALL carry the same dimension
   names, the same underlying data/values, the same attributes, and the same
   encoding as the receiver.
3. IF the object returned by the index-form conversion is subsequently mutated
   in place (for example, by reassigning its tuple of dimension names), THEN the
   original receiver object SHALL retain its own dimension names, data,
   attributes, and encoding unchanged.
4. WHEN the index-form conversion method is invoked on a plain (non-index)
   variable, THEN the method SHALL return a newly constructed index variable
   that carries the receiver's dimension names, data, attributes, and encoding,
   and SHALL leave the receiver unchanged.
5. WHEN the base-form conversion method is invoked on any variable, THEN the
   method SHALL return a newly constructed base variable that carries the
   receiver's dimension names, data, attributes, and encoding, and SHALL leave
   the receiver unchanged.

## Requirement 2: Swapping dimensions must not mutate the source object

**User story:** As a user calling `Dataset.swap_dims()`, I want the operation to
be non-destructive, so that the dataset I called it on is exactly as it was
before, regardless of how many times I call it.

**Acceptance criteria**

1. WHEN `Dataset.swap_dims()` promotes a data variable into a dimension
   coordinate along the swapped dimension, THEN the corresponding variable of
   the original (source) dataset SHALL retain its original dimension names.
2. WHEN `Dataset.swap_dims()` is called on a dataset, THEN every variable of the
   original dataset SHALL retain the same dimension names, data, and coordinate
   membership it had before the call.
3. WHEN `Dataset.swap_dims()` is invoked repeatedly on the same source dataset,
   THEN each invocation SHALL produce an equivalent result and the source
   dataset SHALL remain unchanged across the invocations.
4. WHEN `Dataset.swap_dims()` returns, THEN the returned dataset SHALL have the
   requested dimension(s) swapped: the named replacement variable(s) SHALL
   become dimension coordinate(s) along the new dimension, and every variable's
   dimension names SHALL be updated according to the requested mapping.

## Requirement 3: Preserve existing conversion and validation behavior

**User story:** As a maintainer, I want the existing contracts of these
conversions and of `swap_dims()` to remain intact, so that dependent behavior
across the library does not regress.

**Acceptance criteria**

1. The index-form conversion SHALL continue to produce an object whose values
   compare equal to the receiver's values and whose conversion to a pandas index
   yields the same index.
2. WHEN `swap_dims()` is asked to swap from a name that is not an existing
   dimension, THEN it SHALL raise an error identifying that the name is not an
   existing dimension.
3. WHEN `swap_dims()` is given a replacement name that exists as a variable but
   is not one-dimensional along the old dimension, THEN it SHALL raise an error
   identifying that the replacement is not a valid 1D variable along that
   dimension.
4. WHEN a dimension is swapped to a name that already exists as a variable in the
   dataset, THEN that variable SHALL become a coordinate in the result.
5. The setter guarding an index variable's name SHALL continue to reject
   in-place modification of that name.
