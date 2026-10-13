# Requirements — polyval with timedelta64 coordinates

## Introduction

`xarray.polyval` (in `xarray/core/computation.py`) evaluates a polynomial along a
coordinate using Horner's method. Before the arithmetic, the coordinate is passed
through the helper `_ensure_numeric`, whose per-variable coercion (`to_floatable`)
converts non-numeric coordinate values into floating-point numbers so they can be
multiplied and added.

The affected behavior is the coercion of a coordinate whose dtype is a NumPy
duration type (`timedelta64`, dtype kind `"m"`). Such a coordinate was being
routed through the same epoch-relative datetime reduction used for absolute
timestamps (`datetime64`, dtype kind `"M"`). Because that reduction subtracts a
fixed calendar epoch, applying it to elapsed-time values yields wrong (or
erroring) numeric values, and `polyval` consequently returns incorrect results
for duration coordinates. Historically (release `2022.3.0`) duration coordinates
produced correct results.

The goal is to make `_ensure_numeric` coerce duration coordinates by
reinterpreting their elapsed-time magnitudes directly as floating-point numbers,
while leaving the timestamp and already-numeric behaviors intact, so that
`polyval` produces correct results for `timedelta64` coordinates without
regressing any other coordinate type.

## Requirement 1: Correct numeric coercion of duration (timedelta64) coordinates

**User story:** As a user evaluating a polynomial over a coordinate of elapsed
times, I want durations to be turned into their raw magnitudes as floats, so that
`polyval` returns the mathematically correct values instead of garbage.

**Acceptance criteria**

1. WHEN `_ensure_numeric` receives a `DataArray` whose dtype kind is a duration
   type (`timedelta64`, dtype kind `"m"`), THEN the helper SHALL return a
   `DataArray` whose values are the array's underlying elapsed-time counts cast to
   floating point, preserving the numeric magnitude of each element (a duration
   holding an integer count of `N` time units in its native resolution becomes the
   float `N`, with no scaling, offset, or rounding).
2. WHEN a duration coordinate is coerced, THEN the resulting values SHALL be of a
   floating-point dtype and SHALL NOT be offset by, or reduced relative to, any
   calendar epoch.
3. WHEN duration coordinate values are coerced, THEN the helper SHALL NOT raise an
   error (in particular it SHALL NOT attempt to subtract a timestamp epoch from a
   duration).
4. WHEN `polyval` is called with a `timedelta64` coordinate and integer-degree
   coefficients, THEN the returned values SHALL equal the polynomial evaluated on
   the durations' floating-point magnitudes (i.e. the same result that would be
   obtained by first replacing each duration with the float of its elapsed-time
   count and then evaluating the polynomial); in particular, the identity
   polynomial applied to a duration coordinate SHALL reproduce that coordinate's
   elapsed-time magnitudes as floats.

## Requirement 2: Preserve epoch-relative coercion for timestamp (datetime64) coordinates

**User story:** As a user evaluating a polynomial over absolute timestamps, I want
timestamps to keep being converted relative to a fixed epoch, so that existing
datetime behavior is unchanged.

**Acceptance criteria**

1. WHEN `_ensure_numeric` receives a `DataArray` whose dtype kind is a timestamp
   type (`datetime64`, dtype kind `"M"`), THEN the helper SHALL return a
   `DataArray` whose values are the timestamps converted to a floating-point count
   measured relative to the epoch `1970-01-01` in nanosecond units.
2. WHEN a timestamp coordinate is coerced, THEN the coercion behavior SHALL remain
   equivalent to the prior epoch-relative datetime-to-number reduction (unchanged
   for datetime coordinates).

## Requirement 3: Leave already-numeric coordinates unchanged

**User story:** As a user evaluating a polynomial over a plain numeric coordinate,
I want values passed through untouched, so that ordinary numeric coordinates keep
working exactly as before.

**Acceptance criteria**

1. IF a `DataArray` passed to `_ensure_numeric` has a dtype that is neither a
   timestamp nor a duration type, THEN the helper SHALL return the array's values
   unchanged.
2. WHEN `_ensure_numeric` receives a `Dataset`, THEN it SHALL apply the same
   per-variable coercion rules (duration → float magnitude, timestamp →
   epoch-relative float, other → unchanged) to every variable independently and
   return a `Dataset` of the same structure.

## Requirement 4: Preserve existing polyval behavior (regression protection)

**User story:** As a maintainer, I want all previously working `polyval` behavior
to keep working, so that the duration fix introduces no regressions.

**Acceptance criteria**

1. WHEN `polyval` is called with a numeric coordinate and coefficients indexed by
   an integer degree dimension, THEN it SHALL evaluate the polynomial by Horner's
   method and return values matching the mathematical result. This SHALL hold
   regardless of whether the coordinate is one- or multi-dimensional, whether the
   coordinate and coefficients broadcast against or share dimensions, whether the
   degree labels are given in ascending or arbitrary order, and whether the
   coordinate and/or coefficient operands are supplied as a `DataArray` or a
   `Dataset`.
2. WHEN coefficients are supplied whose degree labels do not start at zero or are
   not contiguous, THEN `polyval` SHALL treat missing degrees as zero coefficients
   and evaluate up to the maximum degree present.
3. IF the degree dimension named by `degree_dim` is not present as a coordinate
   variable with labels on the coefficients, THEN `polyval` SHALL raise a
   `ValueError` indicating that the dimension should be a coordinate variable with
   labels.
4. IF the degree dimension's coordinate is not of integer dtype, THEN `polyval`
   SHALL raise a `ValueError` indicating that the dimension should be of integer
   dtype.
5. WHEN `polyval` evaluates the polynomial, THEN the result SHALL carry the
   coordinate's original (non-degree) coordinate labels and the coefficients'
   non-degree coordinates, and SHALL NOT retain the degree dimension.
