# Requirements: `xr.where` attribute preservation with scalar arguments

## Introduction

`xarray.where` (the top-level function `where(cond, x, y, keep_attrs=None)` in
`xarray/core/computation.py`) is a three-argument conditional selection: it
returns a value taken from `x` where `cond` is true and from `y` elsewhere,
broadcasting the three arguments together. Each argument may be an
xarray-labelled object (a `DataArray`/`Dataset`/`Variable`, which carries its
own `.attrs` mapping) or a bare Python scalar (which carries no attributes).

When the caller requests attribute preservation, `where` is documented to keep
the attributes of `x` (its second positional argument), for consistency with
the `.where` methods of `DataArray`/`Dataset`. The implementation builds an
attribute-combining callback that selects `x`'s attributes from the list of
per-input attribute mappings that `apply_ufunc` assembles.

The defect: that callback locates `x`'s attributes by a fixed positional index
into the list of attribute mappings gathered from only the labelled inputs.
When `x` is a scalar it contributes no entry to that list, so the fixed index
is out of range and the call fails with `IndexError: list index out of range`
instead of returning a result. Consequently `xr.where(cond, 1, 0,
keep_attrs=True)` — and any invocation with a scalar second argument under
attribute preservation — raises rather than producing an output.

The goal is to make `where` resolve the preserved attributes directly from
`x`'s own attribute mapping (empty when `x` is a scalar), so the function
succeeds for scalar arguments while continuing to preserve `x`'s attributes
when `x` is a labelled object, and to leave all other behavior of `where`
unchanged.

## Requirement 1: Attribute preservation succeeds for scalar values

**User story:** As a user calling `xr.where` with scalar branch values, I want
`keep_attrs=True` to work without error, so that I can request attribute
preservation regardless of whether my branch values are labelled arrays or
plain scalars.

**Acceptance criteria**

1. WHEN `where(cond, x, y, keep_attrs=True)` is called and the second
   positional argument `x` is a bare scalar (a value with no `.attrs`
   mapping), THEN `where` SHALL return a result and SHALL NOT raise
   `IndexError` (or any other error) while resolving attributes.
2. WHEN `where(cond, x, y, keep_attrs=True)` is called and the second
   positional argument `x` is a scalar, THEN the returned object's `.attrs`
   SHALL be an empty mapping (`{}`).
3. WHEN `where(cond, x, y, keep_attrs=True)` is called and `x` is a scalar,
   THEN the presence, type, or attributes of `cond` and `y` (whether they are
   labelled objects or scalars, and whatever attributes they carry) SHALL NOT
   affect the resolved attributes, which SHALL remain the empty mapping (`{}`).

## Requirement 2: Attribute preservation keeps the second argument's attributes

**User story:** As a user calling `xr.where` on labelled arrays, I want
`keep_attrs=True` to preserve the attributes of the second argument, so that
the metadata of the value selected where the condition holds is retained.

**Acceptance criteria**

1. WHEN `where(cond, x, y, keep_attrs=True)` is called and the second
   positional argument `x` is a labelled object carrying an attribute mapping,
   THEN the returned object's `.attrs` SHALL equal `x`'s own attribute mapping.
2. IF `cond`, `x`, and `y` are all labelled objects carrying distinct
   attribute mappings and `keep_attrs=True`, THEN the returned object's
   `.attrs` SHALL equal the attribute mapping of `x` (the second positional
   argument) and SHALL NOT be taken from `cond` or `y`.

## Requirement 3: Default and disabled attribute handling are unchanged

**User story:** As a user who does not opt into attribute preservation, I want
`xr.where` to keep its existing default behavior, so that upgrading does not
change results when `keep_attrs` is omitted or set to `False`.

**Acceptance criteria**

1. WHEN `where(cond, x, y)` is called with `keep_attrs` omitted (`None`), THEN
   `where` SHALL resolve attribute handling from the global `keep_attrs`
   option, whose out-of-context default is `False`.
2. WHEN `where(cond, x, y, keep_attrs=False)` is called, THEN the returned
   object SHALL carry an empty attribute mapping (`{}`), regardless of the
   attributes of `cond`, `x`, or `y`.
3. The system SHALL apply attribute preservation only as an added rule for
   selecting which input's attributes to keep; it SHALL NOT alter which value
   (`x` where the condition holds, `y` otherwise) is selected.

## Requirement 4: Conditional selection semantics are preserved

**User story:** As a user of `xr.where`, I want the value-selection and
broadcasting behavior to remain exactly as before, so that fixing the
attribute bug does not change computed results.

**Acceptance criteria**

1. WHEN `where(cond, x, y, ...)` is called, THEN each element of the result
   SHALL be taken from `x` where the corresponding element of `cond` is true
   and from `y` where it is false, after broadcasting `cond`, `x`, and `y`
   together over their dimensions.
2. WHEN any of `cond`, `x`, or `y` is a scalar, THEN `where` SHALL still
   broadcast the remaining labelled arguments and compute element-wise
   selection, returning a labelled result whose dimensions and coordinates
   follow from the labelled inputs.
3. The system SHALL keep returning, in priority order, the richest input type
   among the arguments (a `Dataset`, else a `DataArray`, else a `Variable` or
   plain array) as the result type of `where`.
