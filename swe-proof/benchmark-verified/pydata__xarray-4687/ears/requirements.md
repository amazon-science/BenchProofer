# Requirements: Attribute preservation control for `xarray.where`

## Introduction

The top-level function `where(cond, x, y)` in `xarray/core/computation.py`
(exposed publicly as `xr.where`) selects values element-wise from `x` where
`cond` is truthy and from `y` otherwise, using xarray broadcasting and exact
alignment via `apply_ufunc`. Historically the result never carried the
attributes (`attrs`) of any input, so a user calling `xr.where` on a
`DataArray` that had metadata received an output with empty `attrs`.

The goal is to let callers control attribute handling on this function so that
metadata can be preserved, while leaving the current value-selection,
broadcasting, alignment, and default (attribute-dropping) behavior unchanged
for existing callers. The affected surface is the `where` function in
`xarray/core/computation.py`; attribute-handling defaults are governed by
xarray's global option mechanism (`xarray.get_options` / `set_options`, the
same `keep_attrs` global read elsewhere in the module).

## Requirement 1: Optional attribute-handling control on `where`

**User story:** As a user of `xr.where`, I want an option to keep the
attributes of my chosen input, so that metadata is not silently lost when I
combine arrays.

**Acceptance criteria**
1. The `where` function SHALL accept an additional optional keyword argument
   controlling how attributes are treated, in addition to `cond`, `x`, and `y`.
2. The new keyword argument SHALL default to a value indicating "unspecified",
   so that existing calls that pass only `cond`, `x`, and `y` remain valid.
3. WHEN `where` is called without specifying the attribute-handling argument
   (or with it left unspecified), THEN `where` SHALL resolve the effective
   behavior from xarray's global `keep_attrs` option, whose out-of-the-box
   default is to not keep attributes.
4. The system SHALL continue to accept and honor the boolean, string, and
   callable forms that xarray's attribute-handling mechanism already supports.

## Requirement 2: Preserve attributes of the `x` input on request

**User story:** As a user, I want `xr.where(cond, x, y, keep_attrs=True)` to
return a result carrying `x`'s attributes, so that the selected data keeps its
metadata.

**Acceptance criteria**
1. WHEN `where` is called with the attribute-handling argument set to `True`,
   THEN the returned object SHALL carry exactly the attributes of `x` (the
   third positional argument, the "true" branch values), and no attributes of
   `cond` or `y`.
2. IF `x`'s attributes differ from those of `cond` and `y`, THEN the result's
   attributes SHALL equal `x`'s attributes and SHALL NOT be taken from `cond`
   or `y`.
3. WHEN attributes are kept, THEN the selected element values, dimensions, and
   coordinates of the result SHALL be identical to those produced with the same
   `cond`, `x`, and `y` when attributes are not kept — only the presence of
   `attrs` changes.

## Requirement 3: Preserve existing selection and default behavior

**User story:** As an existing user, I want the value-selection behavior and
the default attribute handling of `xr.where` to stay the same, so that my
current code is unaffected.

**Acceptance criteria**
1. The system SHALL, for every element, return the corresponding value from `x`
   where `cond` is truthy and from `y` where `cond` is falsy.
2. The system SHALL continue to perform xarray-style broadcasting and exact
   alignment/join across `cond`, `x`, and `y`, and SHALL continue to support
   dask-backed inputs.
3. WHEN `where` is called with the effective attribute handling resolving to
   "do not keep" (including the standard default global option), THEN the
   returned object SHALL have empty attributes, matching the pre-existing
   default behavior.
4. The return type priority SHALL be preserved: a `Dataset`, `DataArray`,
   `Variable`, or array is returned according to whichever type appears among
   the inputs, unchanged by the attribute-handling argument.
