# Requirements — `xr.where(..., keep_attrs=True)` attribute retention

## Introduction

The top-level function `xarray.where(cond, x, y, keep_attrs=...)` (implemented in
`xarray/core/computation.py`) performs an element-wise three-way selection: where
`cond` is true it takes values from `x`, otherwise from `y`. The `keep_attrs`
argument controls how attribute dictionaries (`.attrs`) on the result are
populated.

A regression introduced when the function was reworked to keep the attributes of
`x` caused the retention logic to be applied indiscriminately across the whole
result: the top-level (global) attributes of `x` were being copied onto **every**
component of the result, including its **coordinates**. Consequently, calling
`where(cond, x, y, keep_attrs=True)` clobbered the coordinate attributes of the
result with the global/variable attributes of `x` instead of preserving each
coordinate's own attributes taken from `x`.

The goal is to make `keep_attrs=True` reconstruct the result's attributes from `x`
(the second positional argument) **per component and per level** — global
attributes, each data variable's attributes, and each coordinate's attributes —
while leaving the computed values, coordinate labels, dimensions, and default
attribute behavior (`keep_attrs` unset or false) unchanged.

Affected module/function: `xarray.where` in `xarray/core/computation.py`. The
retained attributes always come from `x`, the second positional argument, chosen
to stay consistent with the `.where` methods of `DataArray` and `Dataset`.

## Requirement 1: Per-coordinate attribute retention

**User story:** As a user calling `xr.where(cond, x, y, keep_attrs=True)`, I want
each coordinate on the result to keep its own attributes taken from `x`, so that
coordinate metadata (for example a time coordinate's descriptive attributes) is
never overwritten by unrelated variable- or dataset-level attributes.

**Acceptance criteria**

1. WHEN `xarray.where` is called with `keep_attrs=True`, THEN the function SHALL,
   for every coordinate present on the result, set that coordinate's attribute
   dictionary to the attribute dictionary of the identically-named coordinate on
   `x`.
2. IF a coordinate present on the result has no identically-named coordinate on
   `x` (or `x` exposes no coordinates), THEN the function SHALL set that
   coordinate's attribute dictionary to an empty dictionary.
3. WHEN `keep_attrs=True` and `x` carries coordinate attributes, THEN the
   function SHALL NOT overwrite any result coordinate's attributes with `x`'s
   top-level (global) attributes or with any data-variable attributes.
4. The system SHALL apply coordinate attribute retention regardless of whether
   the result is a `Variable`, a `DataArray`, or a `Dataset`.

## Requirement 2: Global and data-variable attribute retention (array/DataArray results)

**User story:** As a user selecting between `DataArray`/array/`Variable` inputs
with `keep_attrs=True`, I want the result's top-level attributes to come from `x`,
so that the second argument's metadata is preserved as documented.

**Acceptance criteria**

1. WHEN `xarray.where` is called with `keep_attrs=True` and the result is not a
   `Dataset` produced by promoting a non-`Dataset` `x` against a `Dataset` `y`,
   THEN the function SHALL set the result's top-level attribute dictionary to the
   attribute dictionary of `x`.
2. IF `x` has no attributes attribute (for example `x` is a Python scalar or a
   plain array), THEN the function SHALL treat `x`'s top-level attributes as an
   empty dictionary and set the result's top-level attributes to an empty
   dictionary.
3. WHEN `keep_attrs=True` and the result exposes data variables, THEN the
   function SHALL, for each data variable on the result, set that data variable's
   attribute dictionary to the attribute dictionary of the identically-named data
   variable on `x`, or to an empty dictionary if `x` has no such member.

## Requirement 3: Attribute retention when `x` is promoted to a Dataset

**User story:** As a user calling `xr.where` with a non-`Dataset` `x` and a
`Dataset` `y` and `keep_attrs=True`, I want attributes handled sensibly for the
promoted result, so that `x`'s array-level attributes land only on the matching
data variable and no spurious global attributes appear.

**Acceptance criteria**

1. WHEN `xarray.where` is called with `keep_attrs=True`, `y` is a `Dataset`, and
   `x` is not a `Dataset`, THEN the function SHALL set the resulting `Dataset`'s
   top-level attribute dictionary to an empty dictionary.
2. WHEN `xarray.where` is called with `keep_attrs=True`, `y` is a `Dataset`, and
   `x` is not a `Dataset`, IF `x` has a name that matches a data variable of the
   resulting `Dataset`, THEN the function SHALL set that data variable's attribute
   dictionary to `x`'s attribute dictionary.
3. WHILE handling this promotion case, the function SHALL still apply the
   per-coordinate attribute retention of Requirement 1 (coordinate attributes are
   taken from `x`).

## Requirement 4: Default and non-true `keep_attrs` behavior is unchanged

**User story:** As a user who does not request attribute retention, I want the
existing default behavior preserved, so that attributes are dropped by default and
nothing regresses.

**Acceptance criteria**

1. IF `keep_attrs` is not provided (unset/`None`), THEN the function SHALL resolve
   it from the global default, which is false unless configured otherwise.
2. WHEN `keep_attrs` resolves to false, THEN the function SHALL NOT copy any of
   `x`'s attributes onto the result; the result SHALL carry the empty/no-attribute
   behavior that the underlying element-wise combination produces.
3. WHEN `keep_attrs` is a callable, THEN the function SHALL pass it through to the
   underlying element-wise combination unchanged, without applying the
   from-`x` reconstruction of Requirements 1–3.

## Requirement 5: Selection values, coordinates, and structure are preserved (regression protection)

**User story:** As a user relying on `xr.where` for element-wise selection, I want
the computed values and structure to be exactly as before, so that the attribute
fix changes only attributes and nothing else.

**Acceptance criteria**

1. WHEN `xarray.where(cond, x, y, ...)` is called, THEN the function SHALL return,
   element-wise, the value from `x` where `cond` is true and the value from `y`
   where `cond` is false, aligned exactly across the three arguments.
2. The system SHALL keep the result's data-variable name, coordinate labels,
   coordinate values, dimensions, and result type (in priority order `Dataset`,
   `DataArray`, `Variable`, or array as appropriate to the inputs) identical to
   the selection result produced without attribute retention.
3. WHEN scalar or plain-array inputs are supplied for `cond`, `x`, or `y`, THEN
   the function SHALL accept them and produce the correct element-wise selection,
   broadcasting against the array-like argument(s).
4. WHEN `keep_attrs=True` and both `x` and `y` are scalars (so no attribute source
   exists), THEN the function SHALL produce a result whose top-level attributes
   are empty.
