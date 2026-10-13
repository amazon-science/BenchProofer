# Requirements: Auto-detect boolean arrays passed to contour plotting

## Introduction

The contour-plotting routines in Matplotlib (`contour`, `contourf`, and their
triangular-grid counterparts `tricontour`, `tricontourf`) determine which
level values to draw when the caller does not supply levels explicitly. This
level-selection logic lives in the `ContourSet` machinery in
`lib/matplotlib/contour.py` — specifically the method that determines the
contour levels (`_process_contour_level_args`) invoked from the argument-parsing
methods (`_contour_args` / `_check_xyz`), and the parallel path in
`lib/matplotlib/tri/_tricontour.py`.

Historically, when no levels were provided, the routines defaulted to an
automatic count of levels spread across the data range. For a boolean-valued
input array whose only meaningful values are `False`/`True` (i.e. 0 and 1),
this produced many nearly-coincident lines instead of the single dividing
boundary a user actually wants.

The goal of this change is to auto-detect boolean-typed input data and, in that
case only, default to the level(s) that draw the True/False boundary — while
leaving every existing behavior for non-boolean data, explicit levels, and
positional level arguments exactly as before. Reworking the argument-passing to
make the input's data type available to the level-selection step must not alter
any existing shape validation, error reporting, or numeric results.

## Requirement 1: Default levels for boolean line contours

**User story:** As a user calling `contour`/`tricontour` on a boolean 2-D
array without specifying levels, I want a single dividing level so that the plot
shows one clean boundary between the True and False regions instead of many
overlapping lines.

**Acceptance criteria**
1. WHEN a line-contour is requested (unfilled, i.e. `contour` or `tricontour`)
   AND the caller supplies no explicit `levels` AND supplies no positional
   level argument AND the input data array has a boolean data type, THEN the
   system SHALL select the level values to be exactly a single level at `0.5`.
2. WHEN the conditions of criterion 1 hold, THEN the resulting selected
   `levels` SHALL contain exactly one value and that value SHALL equal `0.5`.
3. IF the input data array has a boolean data type but the caller supplied
   explicit `levels` (a non-`None` `levels` argument) OR supplied a positional
   level argument, THEN the system SHALL use the caller-provided levels and
   SHALL NOT apply the boolean default.

## Requirement 2: Default levels for boolean filled contours

**User story:** As a user calling `contourf`/`tricontourf` on a boolean 2-D
array without specifying levels, I want filled regions that distinguish False
from True so that the shaded plot is meaningful.

**Acceptance criteria**
1. WHEN a filled contour is requested (filled, i.e. `contourf` or
   `tricontourf`) AND the caller supplies no explicit `levels` AND supplies no
   positional level argument AND the input data array has a boolean data type,
   THEN the system SHALL select the level values to be exactly the three levels
   `0`, `0.5`, and `1` in increasing order.
2. WHEN the conditions of criterion 1 hold, THEN the resulting selected
   `levels` SHALL satisfy the existing requirement that filled contours have at
   least two levels.

## Requirement 3: Preserve the default behavior for non-boolean data

**User story:** As a user plotting ordinary numeric (non-boolean) data, I want
the level auto-selection to be unchanged so that existing plots and results are
not affected.

**Acceptance criteria**
1. WHEN the caller supplies no explicit `levels` AND supplies no positional
   level argument AND the input data array does NOT have a boolean data type,
   THEN the system SHALL fall back to the pre-existing hard-wired default number
   of automatically chosen levels (an integral count of levels spanning the data
   range), exactly as before this change.
2. The system SHALL apply the boolean-based default only when the input data's
   type is boolean; any other data type (integer, floating point, etc.) SHALL
   NOT trigger the boolean default.

## Requirement 4: Explicit and positional level arguments take precedence

**User story:** As a user who passes levels explicitly, I want my choice to be
honored regardless of the input data type, so that auto-detection never
overrides my intent.

**Acceptance criteria**
1. IF the caller provides a non-`None` `levels` argument, THEN the system SHALL
   use that value to determine the levels and SHALL NOT consult the input data
   type.
2. IF the caller provides a positional level argument (a count or an explicit
   sequence passed positionally), THEN the system SHALL use that argument to
   determine the levels and SHALL NOT consult the input data type.
3. WHEN a level count (an integral value) is chosen, THEN the system SHALL
   expand it into automatically selected levels; WHEN an explicit sequence is
   chosen, THEN the system SHALL use those values directly, unchanged by this
   feature.

## Requirement 5: Preserve input validation and error reporting

**User story:** As a user of the contour routines, I want all existing input
checks and error messages to keep working after the internal argument-handling
rework, so that invalid inputs still fail with the same diagnostics.

**Acceptance criteria**
1. WHEN `x`, `y`, and `z` inputs are provided together, THEN the system SHALL
   continue to validate their shapes and SHALL keep raising the same error type
   with the same message for each mismatch, including: `z` not being 2-D, `z`
   being smaller than a (2, 2) array, the number of dimensions of `x` and `y`
   not matching, the length of a 1-D `x` not matching the number of columns in
   `z`, the length of a 1-D `y` not matching the number of rows in `z`, and a
   2-D `x`/`y` shape not matching `z`.
2. WHEN more positional arguments are passed than the routine accepts, THEN the
   system SHALL keep raising the existing "takes from 1 to 4 arguments" error.
3. WHEN a valid 1-D or 2-D `x`/`y` grid is supplied with a matching `z`, THEN
   the system SHALL continue to accept it and produce a contour set, including
   promoting 1-D `x`/`y` to a 2-D grid as before.
4. WHEN the input `z` is provided with only `z` (no `x`/`y`), THEN the system
   SHALL continue to synthesize default `x`/`y` coordinates from the shape of
   `z` as before.

## Requirement 6: Preserve numeric level-selection semantics for non-boolean data

**User story:** As a user relying on the established level-selection rules, I
want the downstream conversion and validation of levels to remain identical, so
that only boolean detection is new.

**Acceptance criteria**
1. The system SHALL continue to treat a non-`None` `levels` argument, an
   automatic level count, and an explicit level sequence exactly as before,
   including converting a count into automatically chosen levels and converting
   a sequence into an increasing array of float values.
2. WHEN no requested line-contour level falls strictly within the data range,
   THEN the system SHALL keep the existing behavior of emitting a warning and
   falling back to a single level at the data minimum.
3. WHEN a filled contour ends up with fewer than two levels, THEN the system
   SHALL keep raising the existing "Filled contours require at least 2 levels"
   error.
4. WHEN the selected levels are not strictly increasing, THEN the system SHALL
   keep raising the existing "Contour levels must be increasing" error.
5. WHEN the caller enables log scaling with non-positive data, THEN the system
   SHALL keep masking or rejecting such values with the existing behavior and
   messages, unaffected by boolean detection.
6. The system SHALL compute contour values for non-boolean numeric inputs to be
   numerically identical to the behavior before this change.
