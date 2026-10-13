# Requirements: Colormap lookup handles all integer dtypes without deprecation warnings

## Introduction

A `Colormap` in matplotlib is callable: `Colormap.__call__(X, alpha=None,
bytes=False)` (`lib/matplotlib/colors.py`) maps data value(s) `X` to RGBA
colors. Internally it builds an integer index array `xa` from `X`, replaces
out-of-range positions with reserved lookup-table row indices — the under-range
slot `self._i_under` (equal to `self.N`), the over-range slot `self._i_over`
(equal to `self.N + 1`), and the bad/masked slot `self._i_bad` (equal to
`self.N + 2`) — and then gathers rows from the internal lookup table.

The reserved indices `self.N`, `self.N + 1`, and `self.N + 2` can exceed the
value range of a small integer dtype. For example, when `X` is a NumPy array or
scalar of an unsigned 8-bit dtype, the index array `xa` inherits that narrow
dtype, whose values only span `0…255`, so storing an index such as `257` into it
overflows. Starting with NumPy 1.24, assigning such out-of-bound Python integers
into a narrow integer array raises a `DeprecationWarning` ("NumPy will stop
allowing conversion of out-of-bound Python integers to integer arrays"), which
under matplotlib's own test configuration (warnings treated as errors) becomes a
hard failure.

The root cause is that the widening conversion of the index array to a
platform-`int` dtype was only performed for floating-point input, inside the
`xa.dtype.kind == "f"` branch. Integer-dtype input skipped that widening, so its
narrow dtype survived through the reserved-slot assignments.

The goal is to ensure the index array is always widened to a signed integer
dtype capable of holding every reserved index before those reserved indices are
stored, so that `Colormap.__call__` produces correct colors and emits no
deprecation or overflow warnings for any integer or floating-point input dtype,
while leaving all existing color-mapping results unchanged.

## Requirement 1: Integer input of any dtype maps identically to a plain Python int

**User story:** As a user calling a colormap with array or scalar integer data,
I want the returned color to depend only on the integer value and not on its
NumPy dtype, so that small-width dtypes such as unsigned 8-bit integers behave
exactly like a Python `int`.

**Acceptance criteria**
1. WHEN `Colormap.__call__` is invoked with an integer scalar of any integer
   dtype (including narrow unsigned dtypes such as unsigned 8-bit), THEN it SHALL
   return the same RGBA result as when invoked with the equivalent plain Python
   integer of the same value.
2. WHEN `Colormap.__call__` is invoked with an in-range integer value `v` where
   `0 <= v < self.N`, THEN the value SHALL be mapped to lookup-table palette row
   `v`, independent of the input dtype.
3. The system SHALL produce, for a given integer value, results that are
   identical across the integer dtypes and the floating-point dtypes accepted for
   colormap indexing.

## Requirement 2: No deprecation or overflow warnings during index conversion

**User story:** As a user on NumPy 1.24 or newer, I want colormap evaluation to
be silent, so that no deprecation warnings about out-of-bound integer conversion
are emitted (and no error is raised where warnings are escalated to errors).

**Acceptance criteria**
1. WHEN `Colormap.__call__` assigns the reserved under-range, over-range, or
   bad/masked indices into the working index array, THEN the assignment SHALL NOT
   emit a NumPy deprecation warning about converting out-of-bound Python integers
   to integer arrays.
2. IF the input to `Colormap.__call__` has a narrow integer dtype whose value
   range cannot represent the reserved indices `self.N`, `self.N + 1`, or
   `self.N + 2`, THEN the call SHALL still complete without raising, by widening
   the index array to a signed integer dtype able to hold those indices before
   they are stored.
3. WHEN `Colormap.__call__` is invoked with an empty integer array, THEN it SHALL
   complete without emitting any warning.

## Requirement 3: Out-of-range integer values map to the reserved colors

**User story:** As a user, I want values outside the palette range to keep
mapping to the colormap's designated under/over colors regardless of input dtype,
so that clamping behavior is preserved after the dtype fix.

**Acceptance criteria**
1. WHEN an integer input value is greater than `self.N - 1`, THEN it SHALL be
   mapped to the over-range lookup-table row (`self._i_over`).
2. WHEN an integer input value is negative, THEN it SHALL be mapped to the
   under-range lookup-table row (`self._i_under`).
3. The system SHALL apply the over-range assignment before the under-range
   assignment so that a value already replaced by the over-range index is not
   subsequently reinterpreted as under-range.

## Requirement 4: Floating-point mapping behavior is preserved

**User story:** As a user passing normalized floating-point data, I want the
existing float-to-color mapping to be unchanged by the dtype fix, so that this
change is a pure regression-safe fix on the integer path.

**Acceptance criteria**
1. WHEN `Colormap.__call__` receives floating-point input in the interval
   `[0.0, 1.0]`, THEN each value SHALL be scaled by `self.N` and mapped to the
   corresponding palette row, matching the pre-existing behavior.
2. WHEN a floating-point input equals `1.0` (scaling to `self.N`), THEN it SHALL
   map to the last palette row (`self.N - 1`) rather than to an out-of-range slot.
3. WHEN a floating-point input is negative, THEN it SHALL map to the under-range
   row; and WHEN it exceeds `1.0`, THEN it SHALL map to the over-range row.
4. The system SHALL continue to suppress invalid-operation floating-point
   warnings while performing the float-path arithmetic, so that the float path
   remains warning-free.

## Requirement 5: Existing colormap return-type and lookup semantics are preserved

**User story:** As a maintainer, I want the return shape and value conventions of
`Colormap.__call__` to remain unchanged, so that the dtype fix does not regress
downstream consumers.

**Acceptance criteria**
1. WHEN `Colormap.__call__` is given a scalar (non-iterable) input, THEN it SHALL
   return a tuple of RGBA components; and WHEN given an array input, THEN it SHALL
   return an array whose shape is the input shape extended by a trailing axis of
   length 4.
2. WHEN `bytes=False` (default), THEN returned RGBA components SHALL be floats in
   `[0, 1]`; and WHEN `bytes=True`, THEN they SHALL be unsigned 8-bit integers in
   `[0, 255]`.
3. The system SHALL continue to route masked / NaN input values to the
   bad/masked lookup-table row.
