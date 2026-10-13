# Requirements: Honor `keep_attrs` when computing quantiles

## Introduction

When reducing a labelled array by computing quantiles, xarray discards the
source object's metadata attributes (`attrs`) even when the caller explicitly
asks to keep them. Concretely, calling `quantile` on a `DataArray` (e.g.
`da.quantile(0.9, dim="x", keep_attrs=True)`) returns a result whose `attrs`
is empty, contradicting the documented `keep_attrs` behavior.

The quantile computation is layered across three functions in
`xarray/core`:

- `Variable.quantile` (`xarray/core/variable.py`) — the low-level reduction
  that calls `numpy.nanpercentile` and builds the result array.
- `Dataset.quantile` (`xarray/core/dataset.py`) — reduces each data variable
  by delegating to `Variable.quantile`, and assembles the result Dataset.
- `DataArray.quantile` (`xarray/core/dataarray.py`) — reduces a single array
  by routing through a temporary Dataset and back.

The root cause is that `Variable.quantile` has no way to preserve attributes
and always returns an attribute-free result, so the `keep_attrs` request made
at the `Dataset`/`DataArray` level never reaches the variable that actually
produces the reduced data. The goal is to thread the attribute-keeping request
all the way down so that quantile results honor `keep_attrs`, while leaving the
numeric quantile results, dimension handling, and the default (drop-attributes)
behavior unchanged.

The resolution rule for the keep request, used elsewhere in xarray for the same
kind of option, is: an explicit `True`/`False` argument is obeyed directly; when
the argument is unspecified (`None`), fall back to the library's global
`keep_attrs` option, whose effective default is to drop attributes.

## Requirement 1: Variable-level quantile honors an attribute-keeping request

**User story:** As a user computing a quantile of a `Variable`, I want to
control whether the source variable's attributes are carried onto the result,
so that metadata such as units is preserved when I ask for it.

**Acceptance criteria**

1. The `quantile` method of `Variable` SHALL accept an optional attribute-keeping
   argument that controls whether the source variable's attributes are copied to
   the returned variable, defaulting to unspecified when the caller omits it.
2. WHEN `quantile` is called on a `Variable` with the attribute-keeping request
   resolved to true, THEN the method SHALL return a variable whose attributes are
   equal to the source variable's attributes.
3. WHEN `quantile` is called on a `Variable` with the attribute-keeping request
   resolved to false, THEN the method SHALL return a variable that carries no
   attributes.
4. IF the attribute-keeping argument is unspecified, THEN `Variable.quantile`
   SHALL resolve it from xarray's global attribute-keeping option, whose effective
   default causes attributes to be dropped.
5. The resolution of the attribute-keeping request SHALL NOT alter the computed
   quantile values, the resulting dimension labels, or whether a leading quantile
   dimension is added; those SHALL be identical to what the method produced before
   the request was consulted.

## Requirement 2: Dataset-level quantile forwards the keep request to each variable

**User story:** As a user computing quantiles over a `Dataset`, I want the
`keep_attrs` choice I pass to be applied consistently to every reduced data
variable, so that variable-level metadata is preserved together with the
dataset-level metadata.

**Acceptance criteria**

1. WHEN `Dataset.quantile` reduces a data variable, THEN it SHALL forward the same
   attribute-keeping request it received to that variable's quantile reduction.
2. WHEN `Dataset.quantile` is called with the attribute-keeping request resolved
   to true, THEN each reduced data variable in the resulting dataset SHALL retain
   its original attributes.
3. WHEN `Dataset.quantile` is called with the attribute-keeping request resolved
   to false or left to the dropping default, THEN each reduced data variable in
   the resulting dataset SHALL carry no attributes.
4. The system SHALL continue to apply the attribute-keeping request to the
   dataset's own attributes exactly as before: kept when the resolved request is
   true and dropped otherwise.

## Requirement 3: DataArray-level quantile preserves attributes on request

**User story:** As a user computing a quantile of a `DataArray`, I want
`keep_attrs=True` to return a result that still carries the array's attributes,
so that the reported bug is fixed.

**Acceptance criteria**

1. WHEN `DataArray.quantile` is called with the attribute-keeping request resolved
   to true, THEN the returned `DataArray` SHALL have attributes equal to the
   source array's attributes.
2. WHEN `DataArray.quantile` is called with the attribute-keeping request resolved
   to false or omitted (falling back to the dropping default), THEN the returned
   `DataArray` SHALL carry no attributes.
3. The returned `DataArray`'s quantile values SHALL equal the values produced by
   the underlying numeric quantile computation for the requested quantile(s),
   interpolation method, and reduction dimension(s), independently of the
   attribute-keeping choice.

## Requirement 4: Preserve existing quantile computation semantics (regression)

**User story:** As an existing user of the quantile methods, I want the numeric
results and API to remain unchanged, so that adding attribute control does not
break current behavior.

**Acceptance criteria**

1. The system SHALL keep computing quantile values equivalent to applying
   `numpy.nanpercentile` to the source data along the requested dimension(s) with
   the requested interpolation method, for single-quantile and multiple-quantile
   requests.
2. WHEN more than one quantile is requested, THEN the result SHALL add a leading
   quantile dimension; WHEN a single scalar quantile is requested, THEN no
   quantile dimension SHALL be added.
3. The system SHALL keep accepting the quantile value(s), reduction dimension(s),
   and interpolation method through the same parameters as before, without
   changing their meaning.
4. IF the caller does not pass an attribute-keeping argument, THEN the observable
   result (values, dimensions, and — absent a non-default global option —
   attribute-free output) SHALL match the pre-existing behavior.
