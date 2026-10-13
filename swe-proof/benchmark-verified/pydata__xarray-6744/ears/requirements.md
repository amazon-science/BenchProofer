# Requirements: honor the `center` alignment when manually iterating a 1-D rolling object

## Introduction

`xarray.core.rolling.DataArrayRolling` supports manual iteration: iterating over
a rolling object created by `DataArray.rolling(...)` yields, for each position
along the rolling dimension, a `(label, window)` pair whose `window` is the
sub-`DataArray` visible at that position. Users iterate this way to reproduce,
step by step, the same windows that the vectorized reductions
(`.mean()`, `.sum()`, `.std()`, …) operate on.

The affected code is the iterator of `DataArrayRolling` in
`xarray/core/rolling.py` (the `__iter__` method). It currently computes each
window's start/stop indices as if the window were always right-anchored, so it
ignores the `center` alignment flag that was passed to
`DataArray.rolling(dim=..., center=True)`. As a result, manually iterating a
centered rolling object produces windows shifted off-center: the per-window
reductions do not match the corresponding elements of the vectorized centered
reduction. The goal is to make manual iteration honor `center` so that, for
every position, the window it yields is the same slice the vectorized reduction
uses at that position — for both centered and non-centered rolling, and for all
window sizes — while preserving every other observable property of iteration.

Throughout, "the rolling dimension" is the single dimension of a 1-D rolling
object, `n` is the length of that dimension, and `w` is the window size passed
to `rolling`.

## Requirement 1: Centered manual iteration matches the vectorized centered reduction

**User story:** As a user manually iterating a centered rolling object, I want
each yielded window to be center-justified on its position, so that reducing the
windows myself gives the same sequence of values as calling the vectorized
reduction on the centered rolling object.

**Acceptance criteria**

1. WHEN a 1-D rolling object is created over a dimension with `center=True` and
   window size `w`, and it is iterated, THEN for each position `i`
   (`0 ≤ i < n`) `DataArrayRolling.__iter__` SHALL yield a window equal to the
   contiguous slice of the source object along the rolling dimension whose
   right edge is placed so the window straddles position `i` symmetrically —
   i.e. the window ends `⌈w/2⌉` positions past `i` (`(w + 1) // 2`), begins `w`
   positions before that end, and is clamped to the start of the dimension for
   the leading positions where that computed begin would be negative.
2. WHEN such a centered rolling object is iterated and each yielded window is
   reduced with a reduction (e.g. taking its mean over the rolling dimension),
   THEN the resulting value for position `i` SHALL equal the value at position
   `i` of the same reduction computed by the vectorized centered rolling
   reduction, for every position including the leading and trailing positions.
3. WHILE `center=True`, the leading positions whose window extends before the
   start of the dimension SHALL have their window begin at the first element of
   the dimension (no negative or wrapped indexing), and trailing positions whose
   computed window end exceeds `n` SHALL have their window truncated at the last
   element of the dimension.
4. The behavior in this requirement SHALL hold for every window size, including
   `w = 1` (each window is the single element aligned with its position) and
   window sizes larger than `n`.

## Requirement 2: Preserve right-anchored windows for non-centered iteration

**User story:** As a user manually iterating a non-centered rolling object, I
want the existing right-anchored window behavior to be unchanged, so that code
relying on it keeps working.

**Acceptance criteria**

1. WHEN a 1-D rolling object is created with `center=False` (the default) and
   window size `w`, and it is iterated, THEN for each position `i`
   `DataArrayRolling.__iter__` SHALL yield the contiguous slice ending at and
   including position `i` (right edge one past `i`) and beginning `w` positions
   before that end, clamped to the start of the dimension for the leading
   positions.
2. WHEN a non-centered rolling object is iterated and each yielded window is
   reduced, THEN the value for position `i` SHALL equal the value at position
   `i` of the same reduction computed by the vectorized non-centered rolling
   reduction, for every window size and every position.

## Requirement 3: One window per position, with the dimension labels preserved

**User story:** As a user, I want iteration to visit every position of the
rolling dimension exactly once with its coordinate label, so that I can align
results back to the original data.

**Acceptance criteria**

1. WHEN a 1-D rolling object is iterated, THEN it SHALL yield exactly `n`
   `(label, window)` pairs — one per position along the rolling dimension — in
   ascending position order.
2. The system SHALL keep exposing the rolling dimension's coordinate values as
   the sequence of labels, so that the label yielded at position `i` is the
   `i`-th coordinate value of the rolling dimension and the count of labels
   equals `n`.
3. Each yielded window SHALL be a contiguous slice of the source object taken
   along the rolling dimension (a sub-selection of consecutive positions), with
   all other dimensions unchanged.

## Requirement 4: Apply the minimum-periods mask to each yielded window

**User story:** As a user iterating a rolling object with `min_periods` set, I
want short windows masked consistently with the vectorized behavior, so that
manual and vectorized results agree at the boundaries.

**Acceptance criteria**

1. WHEN a window is yielded during iteration, IF the number of non-missing
   values it contains along the rolling dimension is less than the object's
   effective `min_periods`, THEN the yielded window's entries SHALL be masked as
   missing (NaN).
2. WHEN a window contains at least `min_periods` non-missing values, THEN its
   values SHALL be left unmasked.

## Requirement 5: Restrict iteration to one-dimensional rolling

**User story:** As a user, I want a clear error when I try to iterate a
multi-dimensional rolling object, so that I do not get silently wrong results.

**Acceptance criteria**

1. IF a rolling object spans more than one rolling dimension, THEN attempting to
   iterate it SHALL raise a `ValueError` indicating that iteration is supported
   only for 1-D rolling.

## Requirement 6: Consistency between manual iteration and vectorized reduction

**User story:** As a user, I want manual iteration and the vectorized reductions
to describe the same windows, so that either approach yields the same result.

**Acceptance criteria**

1. The system SHALL ensure that, for any 1-D rolling object regardless of the
   `center` flag and window size, the sequence obtained by reducing each yielded
   window over the rolling dimension is element-for-element equal (up to
   floating-point tolerance) to the sequence produced by applying that same
   reduction through the vectorized rolling API on the same object.
