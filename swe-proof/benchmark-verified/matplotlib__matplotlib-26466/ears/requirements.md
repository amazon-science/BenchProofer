# Requirements: Capture annotation coordinates by value at construction

## Introduction

In `lib/matplotlib/text.py`, two helper objects each accept a 2D coordinate
`(x, y)` as a constructor argument and retain it for later use during drawing:

- `matplotlib.text.OffsetFrom.__init__` receives a reference coordinate
  (`ref_coord`) and stores it for use when computing the offset transform in
  `OffsetFrom.__call__`.
- `matplotlib.text._AnnotationBase.__init__` (the base of `Annotation`, created
  through `Axes.annotate`) receives the annotation anchor coordinate (`xy`) and
  stores it as the `xy` attribute used when the annotation is positioned/drawn.

Callers commonly pass a mutable container — most often a NumPy array — as this
coordinate. At the base revision each object stores the container it was handed
directly, so it keeps the *same* object the caller still holds. Because the
container is mutable, a later in-place edit of the caller's array (e.g.
`xy_0[1] = 3` after calling `annotate`) silently changes the coordinate already
stored on the object, moving the annotation/arrow that was already created. The
expected behavior is that the coordinate is captured *by value* at construction
time: the two components are read once when the object is built, and the stored
coordinate is a snapshot of exactly those two values, decoupled from any later
mutation of the caller's container.

The goal of this change is to make both constructors take a by-value snapshot of
the incoming coordinate while leaving all other annotation and offset behavior
unchanged.

## Requirement 1: Annotation anchor coordinate captured by value

**User story:** As a user creating an annotation from a mutable coordinate
container, I want the annotation to keep the coordinate values it was given at
call time, so that later edits to my array do not move an annotation I already
created.

**Acceptance criteria**

1. WHEN `_AnnotationBase.__init__` (as reached through `Axes.annotate` /
   `Annotation`) is called with a coordinate `xy`, THEN the system SHALL read the
   two components of `xy` at that moment and store the anchor coordinate as a
   fresh pair of those two component values.
2. IF the coordinate `xy` supplied at construction is a mutable container (such
   as a NumPy array), THEN the stored anchor coordinate SHALL NOT alias that
   container, so that mutating the original container in place after construction
   does not change the stored anchor coordinate.
3. WHEN the caller mutates, in place, the container that was passed as `xy` after
   the annotation has been constructed, THEN reading the annotation's stored
   anchor coordinate SHALL still yield the component values that were present at
   construction time.
4. The system SHALL expose the stored anchor coordinate as two ordered
   components, first component then second component, equal to the first and
   second components of the coordinate supplied at construction.

## Requirement 2: OffsetFrom reference coordinate captured by value

**User story:** As a user building an `OffsetFrom` offset helper from a mutable
coordinate container, I want the reference coordinate to be frozen at
construction, so that later edits to my array do not change the computed offset.

**Acceptance criteria**

1. WHEN `OffsetFrom.__init__` is called with a reference coordinate `ref_coord`,
   THEN the system SHALL read the two components of `ref_coord` at that moment and
   store the reference coordinate as a fresh pair of those two component values.
2. IF the coordinate `ref_coord` supplied at construction is a mutable container
   (such as a NumPy array), THEN the stored reference coordinate SHALL NOT alias
   that container, so that mutating the original container in place after
   construction does not change the stored reference coordinate.
3. WHEN the caller mutates, in place, the container that was passed as
   `ref_coord` after the `OffsetFrom` has been constructed, THEN the offset
   transform produced by `OffsetFrom.__call__` SHALL be computed from the
   component values that were present at construction time, not from the mutated
   container.

## Requirement 3: Preserve normal annotation and offset behavior

**User story:** As an existing user, I want all pre-existing annotation and
offset behavior to keep working, so that this fix does not regress valid usage.

**Acceptance criteria**

1. WHEN a valid coordinate is supplied to either constructor, THEN the stored
   coordinate SHALL be usable exactly as before for positioning, drawing, and
   containment checks, producing the same visual result as when an equal
   immutable coordinate (e.g. a plain tuple) is supplied.
2. The offset transform returned by `OffsetFrom.__call__` SHALL continue to scale
   by 1 when the configured unit is `"pixels"` and by the renderer's
   points-to-pixels factor otherwise, then translate by the resolved reference
   point, producing the same transform as before this change.
3. WHILE constructing an annotation, the system SHALL continue to reject invalid
   coordinate-system (`xycoords`/`textcoords`) specifications with the same error
   types and messages as before this change.
4. The system SHALL leave the accepted call signatures and the observable results
   of `Axes.annotate`, `Annotation`, and `OffsetFrom` unchanged for all valid
   inputs apart from the by-value capture behavior described in Requirements 1
   and 2.
