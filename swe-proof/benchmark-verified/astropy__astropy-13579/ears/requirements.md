# Requirements: Correct `world_to_pixel` on a sliced low-level WCS with coupled axes

## Introduction

`astropy.wcs.wcsapi.SlicedLowLevelWCS` wraps an underlying low-level WCS and
exposes a reduced view in which one or more pixel/world axes have been fixed by
integer slicing. The reduced view keeps only the non-sliced ("kept") world
axes; the caller supplies world values for those kept axes only.

To delegate a `world_to_pixel_values` call to the underlying WCS, the wrapper
must rebuild a full-length world vector for the underlying WCS: for each of the
underlying WCS's world axes it either takes the next caller-supplied value (for
a kept axis) or supplies a value on the caller's behalf (for a world axis that
was dropped by the slice).

There is a defect in `world_to_pixel_values`
(`astropy/wcs/wcsapi/wrappers/sliced_wcs.py`): the value inserted for every
dropped world axis is the constant `1.` (an arbitrary placeholder), regardless
of what world coordinate that dropped axis actually holds at the sliced pixel
location. When the underlying WCS couples the dropped and kept axes — e.g. a
non-diagonal `PCij` matrix mixing a spectral axis with the spatial axes — this
placeholder feeds a wrong value into the underlying inverse transform and
corrupts the returned pixel coordinates of the kept axes (the reported issue
shows one kept pixel coordinate coming back as a near-infinite value instead of
its correct value). When the dropped and kept axes are independent, the
placeholder happens to be harmless, which is why the bug only surfaced for
coupled WCSes.

The correct value for a dropped world axis is the world coordinate that axis
takes at the pixel location fixed by the slice, i.e. the world coordinates
obtained by transforming the sliced-out pixel position through the underlying
WCS. The `pixel_to_world_values` direction is already correct and must remain
so. The affected module is
`astropy/wcs/wcsapi/wrappers/sliced_wcs.py`; behavior is observed through
`SlicedLowLevelWCS.world_to_pixel_values` (and the high-level
`world_to_pixel` that builds on it).

## Requirement 1: Dropped world axes use the slice-location world value, not a placeholder

**User story:** As a user performing `world_to_pixel` on a sliced WCS, I want
the world coordinates of the axes removed by the slice to be filled with the
values those axes actually take at the slice location, so that the pixel
coordinates I get back for the kept axes are correct even when the underlying
WCS couples the sliced and kept axes.

**Acceptance criteria**

1. WHEN `world_to_pixel_values` is called on a `SlicedLowLevelWCS`, THEN the
   system SHALL build the full-length world vector passed to the underlying WCS
   so that each dropped world axis carries the world coordinate that axis holds
   at the pixel location fixed by the slice, rather than a fixed constant.
2. WHEN the wrapper determines the world value for a dropped axis, THEN the
   system SHALL derive it by transforming the sliced-out pixel position (the
   fixed pixel indices, with kept pixel axes taken at their origin) through the
   underlying WCS's pixel-to-world transform, and SHALL index that result by
   the underlying world-axis number.
3. WHEN each underlying world axis is one of the kept axes, THEN the system
   SHALL place the corresponding caller-supplied world value at that axis,
   consuming the supplied values left-to-right in kept-axis order.
4. WHEN the underlying WCS couples a dropped world axis with the kept world
   axes (a non-diagonal correlation, e.g. a `PCij` matrix mixing spectral and
   spatial dimensions), THEN the pixel coordinate `world_to_pixel_values`
   returns for each kept axis SHALL equal the corresponding pixel coordinate of
   the unsliced round trip, i.e. it SHALL match the pixel value obtained by
   converting the same world point through the full unsliced WCS.
5. IF the world value supplied for a kept axis corresponds to a pixel location
   at the sliced-out plane, THEN `world_to_pixel_values` SHALL return that
   pixel location's true coordinate (a finite, non-degenerate value) for each
   kept axis rather than an arbitrarily large or infinite value.

## Requirement 2: Kept-axis pixel offsets and return shape are preserved

**User story:** As a user of a sliced WCS created with range/offset slices, I
want the returned pixel coordinates to remain expressed in the sliced frame, so
that results are consistent with the reduced view.

**Acceptance criteria**

1. WHEN a kept pixel axis was produced by a slice with a non-`None` start
   offset, THEN `world_to_pixel_values` SHALL subtract that start offset from
   the underlying pixel coordinate so the returned value is relative to the
   sliced view.
2. WHEN the sliced WCS keeps exactly one pixel dimension while the underlying
   WCS has more than one pixel dimension, THEN `world_to_pixel_values` SHALL
   return that single pixel coordinate directly rather than wrapped in a tuple.
3. The system SHALL return one pixel coordinate per kept pixel axis, in
   kept-axis order, for the general multi-dimensional case.

## Requirement 3: `pixel_to_world` behavior is unchanged

**User story:** As a user, I want the forward `pixel_to_world` direction on a
sliced WCS to keep returning the same results, so that fixing the inverse
direction does not regress the forward one.

**Acceptance criteria**

1. WHEN `pixel_to_world_values` is called on a `SlicedLowLevelWCS`, THEN the
   system SHALL continue to return, for each kept world axis, the world
   coordinate obtained by transforming the supplied (offset-adjusted) pixel
   positions through the underlying WCS, unchanged by this fix.
2. WHEN a sliced WCS undergoes a pixel→world→pixel round trip for a coupled
   WCS, THEN the kept pixel coordinates recovered by `world_to_pixel_values`
   SHALL agree with the pixel coordinates that produced them via
   `pixel_to_world_values`.

## Requirement 4: Existing slicing behaviors keep working

**User story:** As a maintainer, I want the previously correct slicing
behaviors to continue to hold, so that the fix is additive and does not break
established functionality.

**Acceptance criteria**

1. WHEN dropped and kept world axes are mutually independent (diagonal
   correlation), THEN `world_to_pixel_values` SHALL return the same kept-axis
   pixel coordinates it returned before this fix.
2. The system SHALL keep reporting the dropped world dimensions' metadata and
   reference values (the world coordinates at the sliced-out location) exactly
   as before.
3. WHEN slices are combined (nested slicing, integer and range slices, and
   broadcasting of world inputs), THEN `world_to_pixel_values` SHALL continue
   to honor the combined slice offsets and broadcasting behavior.
4. The system SHALL preserve the existing constraint that a sliced WCS retains
   at least one pixel and one world dimension, raising the same error otherwise.
