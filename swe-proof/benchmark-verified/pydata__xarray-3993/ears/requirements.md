# Requirements — Consistent coordinate argument for `DataArray.integrate`

## Introduction

In `xarray`, integration along a coordinate is exposed on two public objects:
`Dataset.integrate` (in `xarray/core/dataset.py`) and `DataArray.integrate`
(in `xarray/core/dataarray.py`). These two entry points accept the same
conceptual input — the coordinate(s) to integrate along — but historically
name that parameter inconsistently: `Dataset.integrate` calls it `coord`,
while `DataArray.integrate` calls it `dim`. The sibling operation
`differentiate` already uses `coord` on both objects. This inconsistency is a
usability defect: the primary selector parameter of `DataArray.integrate`
should be named `coord` to match `Dataset.integrate` and `differentiate`.

Because the old parameter name is part of the public API, the rename must go
through a deprecation cycle: the old spelling must keep working but emit a
deprecation notice, so existing callers are not broken. The goal is to make
`DataArray.integrate` accept the coordinate under the new consistent name,
continue to accept the old name for one release with a deprecation warning,
reject contradictory usage, and leave the actual numerical integration
(the trapezoidal computation performed via the underlying `Dataset.integrate`)
completely unchanged.

The affected functions are `DataArray.integrate` (the entry point whose
parameter set changes) and `Dataset.integrate` (whose observable runtime
behavior must stay identical).

## Requirement 1: Accept the coordinate under the consistent name

**User story:** As an xarray user, I want `DataArray.integrate` to accept the
coordinate to integrate along under the same name used by
`Dataset.integrate` and `differentiate`, so that the API is consistent and I
do not have to remember a different parameter name for this one method.

**Acceptance criteria**

1. The system SHALL expose on `DataArray.integrate` a primary parameter that
   names the coordinate(s) to integrate along, using the same name that
   `Dataset.integrate` and `DataArray.differentiate` use for that role.
2. WHEN a caller invokes `DataArray.integrate` supplying the coordinate name
   positionally (e.g. as the first positional argument), THEN
   `DataArray.integrate` SHALL integrate the array along that coordinate
   using the trapezoidal rule and return the integrated `DataArray`.
3. WHEN a caller invokes `DataArray.integrate` supplying the coordinate under
   the consistent parameter name as a keyword argument, THEN
   `DataArray.integrate` SHALL integrate the array along that coordinate and
   return the integrated `DataArray`.
4. WHEN the coordinate is supplied under the consistent name (positionally or
   by keyword) and no deprecated selector is supplied, THEN
   `DataArray.integrate` SHALL NOT emit any deprecation warning.
5. The system SHALL continue to accept an optional `datetime_unit` argument
   and forward it unchanged to the underlying integration, so that datetime
   coordinates integrate as before.

## Requirement 2: Deprecate, but still honor, the previous selector name

**User story:** As an existing xarray user with code that passes the old
selector name to `DataArray.integrate`, I want my code to keep working for now
while being told to migrate, so that the rename does not silently break my
programs.

**Acceptance criteria**

1. The system SHALL continue to accept the previously-used selector name on
   `DataArray.integrate` as a keyword argument.
2. WHEN a caller invokes `DataArray.integrate` supplying only the deprecated
   selector name (and not the consistent name), THEN `DataArray.integrate`
   SHALL integrate the array along the coordinate identified by that value,
   producing the same result it would produce were that value supplied under
   the consistent name.
3. WHEN a caller invokes `DataArray.integrate` supplying only the deprecated
   selector name, THEN `DataArray.integrate` SHALL emit a `FutureWarning`
   indicating that the deprecated selector name is being replaced by the
   consistent name and will be removed in a future release.
4. The system SHALL still return the correctly integrated `DataArray` in the
   deprecated-name case; emitting the warning SHALL NOT prevent or alter the
   computation of the result.

## Requirement 3: Reject contradictory selector usage

**User story:** As an xarray user, I want a clear error if I accidentally pass
both the old and the new selector names at once, so that I am not silently
given an ambiguous or arbitrary result.

**Acceptance criteria**

1. IF a caller invokes `DataArray.integrate` supplying BOTH the consistent
   selector name AND the deprecated selector name (each with a value that is
   not `None`), THEN `DataArray.integrate` SHALL raise a `ValueError` and
   SHALL NOT perform the integration.
2. WHEN both selectors are supplied, THEN `DataArray.integrate` SHALL NOT emit
   the deprecation `FutureWarning` in place of raising the error; the error
   takes precedence.

## Requirement 4: Preserve existing integration behavior and validation

**User story:** As an xarray user relying on the numerical results and error
handling of integration, I want the rename to leave the actual computation and
its input validation unchanged, so that only the parameter naming — not the
results — is affected.

**Acceptance criteria**

1. The system SHALL compute the trapezoidal integral of a `DataArray` along
   the resolved coordinate identically to how it did before this change; only
   which parameter carries the coordinate value changes, not the numerical
   result.
2. WHEN the resolved coordinate is a valid one-dimensional coordinate of the
   array, THEN `DataArray.integrate` SHALL reduce the array along that
   coordinate's dimension and return the integrated result.
3. IF the resolved coordinate does not correspond to a valid one-dimensional
   coordinate (for example, a multi-dimensional coordinate), THEN
   `DataArray.integrate` SHALL raise a `ValueError`, as it did prior to this
   change.
4. The system SHALL keep `Dataset.integrate` accepting its coordinate under
   the same name as before and SHALL keep its runtime behavior, results, and
   error handling unchanged (its signature-type annotations and documentation
   may be updated, but no observable computational behavior changes).
5. WHEN a caller integrates a `Dataset` along a valid coordinate, THEN
   `Dataset.integrate` SHALL return the same integrated `Dataset` it returned
   before this change.
