# Requirements: correct `top`/`bottom` alignment in the offset-box packers

## Introduction

The offset-box layout helpers in `lib/matplotlib/offsetbox.py` arrange child
boxes along one axis while aligning them across the perpendicular axis
according to an `align` keyword. The cross-axis alignment is computed by the
shared helper `_get_aligned_offsets(hd_list, height, align)`, which is called
by `HPacker.get_extent_offsets` (aligning children vertically) and by
`VPacker.get_extent_offsets` (aligning children horizontally).

The accepted `align` keywords are `"baseline"`, `"left"`, `"top"`, `"right"`,
`"bottom"`, and `"center"`. The reported problem is that for `HPacker` the
`"top"` and `"bottom"` anchors behave as if swapped: choosing `"bottom"` pushes
the shorter child to the far (high) edge and `"top"` pushes it to the near (low)
edge, i.e. the opposite of what the keyword names. The goal is to make each
anchor place boxes as its name implies, so that `"bottom"`/`"left"` share one
placement rule and `"top"`/`"right"` share the opposite rule, while leaving
`"baseline"` and `"center"` and every reported extent unchanged.

Throughout this document, for a box aligned along an axis, its *length* is its
size along that alignment axis and its *descent* is the box's descent value on
that axis. `total` is the intended total size passed to the helper (or, when
none is given, the maximum box length).

## Requirement 1: Correct alignment rule for each anchor in the shared helper

**User story:** As a developer laying out composite artists, I want each
`align` keyword in the offset-box packers to place boxes exactly as its name
implies, so that `"bottom"` and `"top"` are not reversed.

**Acceptance criteria**

1. WHEN `_get_aligned_offsets` is called with `align` equal to `"left"` or
   `"bottom"`, THEN the helper SHALL return a packing descent of `0` and, for
   each input box, an offset equal to that box's own descent.
2. WHEN `_get_aligned_offsets` is called with `align` equal to `"right"` or
   `"top"`, THEN the helper SHALL return a packing descent of `0` and, for each
   input box, an offset equal to `total - length + descent` for that box.
3. IF `align` is `"left"`, `"top"`, `"right"`, `"bottom"`, or `"center"`, THEN
   the helper SHALL return `total` unchanged as the resolved size along the
   alignment axis (only `"baseline"` recomputes the size).
4. The system SHALL treat `"bottom"` as sharing the same offset rule as
   `"left"`, and SHALL treat `"top"` as sharing the same offset rule as
   `"right"`.
5. WHEN the returned offsets are produced for any anchor, THEN the offsets list
   SHALL have the same length as the input list and SHALL correspond
   element-by-element, in order, to the input boxes.

## Requirement 2: Preserve `baseline` and `center` alignment behavior

**User story:** As a user relying on baseline and centered layouts, I want
those anchors to keep their existing behavior, so that fixing `top`/`bottom`
does not regress other alignments.

**Acceptance criteria**

1. WHEN `_get_aligned_offsets` is called with `align` equal to `"baseline"`,
   THEN the helper SHALL return a resolved size equal to the maximum of
   `(length - descent)` over the boxes plus the maximum descent over the boxes,
   a packing descent equal to the maximum descent over the boxes, and an offset
   of `0` for every box.
2. WHEN `_get_aligned_offsets` is called with `align` equal to `"center"`, THEN
   the helper SHALL return a packing descent of `0` and, for each box, an offset
   equal to `(total - length) / 2 + descent`.
3. IF `align` is none of the accepted keywords (`"baseline"`, `"left"`,
   `"top"`, `"right"`, `"bottom"`, `"center"`), THEN the helper SHALL raise an
   error rather than silently accept it.

## Requirement 3: Correct vertical placement of children in `HPacker`

**User story:** As a user horizontally packing boxes of differing heights, I
want the `align` keyword to move the shorter child to the named edge, so that
`"bottom"` places it at the bottom and `"top"` places it at the top.

**Acceptance criteria**

1. WHEN `HPacker.get_extent_offsets` packs two zero-padding, zero-separation
   children whose heights differ, and `align` is `"baseline"`, `"left"`, or
   `"bottom"`, THEN the shorter child's vertical offset SHALL equal the taller
   child's vertical offset (both flush at the low edge).
2. WHEN `HPacker.get_extent_offsets` packs two such children and `align` is
   `"top"` or `"right"`, THEN the shorter child's vertical offset SHALL be
   shifted from the taller child's by the difference between the two heights
   (the shorter child flush at the high edge).
3. WHEN `align` is `"center"`, THEN the shorter child's vertical offset SHALL be
   shifted from the taller child's by half the difference between the two
   heights.
4. The system SHALL report the packed extent of such an `HPacker` as the sum of
   the child widths for the total width, the maximum child height for the total
   height, and zero for both the x- and y-descent, independent of `align`.

## Requirement 4: Correct horizontal placement of children in `VPacker`

**User story:** As a user vertically packing boxes of differing widths, I want
the `align` keyword to move the narrower child to the named edge, so that
`VPacker` alignment matches `HPacker` after the fix.

**Acceptance criteria**

1. WHEN `VPacker.get_extent_offsets` packs two zero-padding, zero-separation
   children whose widths differ, and `align` is `"baseline"`, `"left"`, or
   `"bottom"`, THEN the narrower child's horizontal offset SHALL equal the wider
   child's horizontal offset (both flush at the left edge).
2. WHEN `VPacker.get_extent_offsets` packs two such children and `align` is
   `"top"` or `"right"`, THEN the narrower child's horizontal offset SHALL be
   shifted from the wider child's by the difference between the two widths (the
   narrower child flush at the right edge).
3. WHEN `align` is `"center"`, THEN the narrower child's horizontal offset SHALL
   be shifted from the wider child's by half the difference between the two
   widths.
4. The system SHALL report the packed extent of such a `VPacker` as the maximum
   child width for the total width, the sum of the child heights for the total
   height, zero for the x-descent, and the height of the last child in the
   packing order for the y-descent, independent of `align`.
