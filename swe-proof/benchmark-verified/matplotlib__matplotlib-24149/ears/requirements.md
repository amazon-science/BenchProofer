# Requirements: Robust bar placement for all-non-finite coordinate data

## Introduction

`matplotlib.axes.Axes.bar` (and its horizontal counterpart `barh`) fails when
the bar position data contains no finite values. Calling, for example,
`ax.bar([np.nan], [np.nan])` raises an uncaught `StopIteration` instead of
producing a bar. In an earlier release the same call returned a bar container
holding a single rectangle whose coordinates were `nan`, so the current
behavior is a regression that breaks downstream code (such as histogram helpers
that draw and immediately remove a placeholder bar to advance the color cycle).

The root cause is in the width-conversion helper
`Axes._convert_dx` in `lib/matplotlib/axes/_axes.py`. It uses
`matplotlib.cbook._safe_first_finite` to pick a representative element from the
position sequence `x0` (and from the converted array `x`). When the sequence
contains no finite element, `_safe_first_finite` exhausts its search and raises
`StopIteration`; `_convert_dx` does not handle that case, so the exception
propagates out of `bar`.

The goal is to make `_convert_dx` tolerant of position data that has no finite
element, so that `bar`/`barh` still create the expected bar geometry (with
non-finite coordinates preserved) rather than raising.

## Requirement 1: Width conversion tolerates position data with no finite element

**User story:** As a user plotting bars, I want `ax.bar` to accept position
data that contains only non-finite values (e.g. all `nan`), so that my call
returns a bar container instead of raising an exception.

**Acceptance criteria**
1. WHEN `Axes._convert_dx` attempts to select a representative element from the
   original position value `x0` and the sequence contains no finite element,
   THEN `_convert_dx` SHALL fall back to selecting the first element of `x0`
   unconditionally rather than allowing the failed finite-selection to
   propagate as an exception.
2. WHEN `Axes._convert_dx` attempts to select a representative element from the
   already-converted position array and that array contains no finite element,
   THEN `_convert_dx` SHALL fall back to selecting the first element of that
   array unconditionally rather than allowing the failed finite-selection to
   propagate as an exception.
3. IF the position sequence contains at least one finite element, THEN
   `_convert_dx` SHALL continue to select the first finite element, preserving
   the existing behavior for ordinary finite data.
4. The system SHALL restrict this fallback to the case where the finite search
   completed without finding a finite element; other failures of the
   representative selection (such as a type mismatch, missing index, or missing
   key) SHALL retain their existing handling.

## Requirement 2: `bar` returns a bar for all-non-finite positions

**User story:** As a user calling `ax.bar` with only non-finite data, I want a
bar container back with a single bar whose geometry reflects the non-finite
input, so that code depending on the returned artists does not break.

**Acceptance criteria**
1. WHEN `Axes.bar` is called with a single-element position sequence whose only
   value is non-finite and a single-element height sequence, THEN `bar` SHALL
   return a bar container holding exactly one bar and SHALL NOT raise an
   exception.
2. WHEN such a bar is created from a non-finite x position, THEN the resulting
   bar's x coordinate SHALL be non-finite (the non-finite position SHALL be
   preserved, not replaced by a finite substitute).
3. WHEN such a bar is created from a non-finite height, THEN the resulting bar's
   height SHALL be non-finite.
4. WHEN `Axes.bar` is called with a non-finite x position together with a finite
   height, THEN `bar` SHALL return a bar container without raising.
5. WHEN `Axes.bar` is called with a finite x position together with a non-finite
   height, THEN `bar` SHALL return a bar container without raising (this case
   already succeeded and SHALL continue to succeed).

## Requirement 3: Preserve existing bar and width-conversion behavior

**User story:** As a maintainer, I want the fix to be narrowly scoped so that
all previously working plotting behavior continues to work unchanged.

**Acceptance criteria**
1. WHEN `Axes.bar` is called with ordinary finite position and height data,
   THEN it SHALL keep producing the same bar geometry and bar container it
   produced before this change.
2. WHEN the width or position values carry units (for example datetime
   positions with timedelta widths, or unit-wrapped array types), THEN
   `_convert_dx` SHALL keep performing unit-aware width conversion using a
   representative element as it did before.
3. IF the converted position array is empty, THEN `_convert_dx` SHALL keep
   returning the width converted on its own, unchanged from prior behavior.
4. WHEN adding the width offset to the representative position fails for any
   reason, THEN `_convert_dx` SHALL keep falling back to converting the width by
   itself, unchanged from prior behavior.
5. The system SHALL keep the horizontal bar path (`barh`) working equivalently,
   so that non-finite position data does not raise there either.
