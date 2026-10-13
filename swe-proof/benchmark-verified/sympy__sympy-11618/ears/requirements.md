# Requirements: Euclidean distance between geometry Points of differing dimension

## Introduction

The `distance` method of the `Point` class in `sympy/geometry/point.py`
computes the Euclidean distance from a point (`self`) to another point `p`.
Points may live in spaces of different dimension — for example a planar point
(`Point2D`, two coordinates) and a spatial point (`Point3D`, three
coordinates).

The existing implementation pairs coordinates by zipping the two coordinate
sequences together. Because zipping stops at the shorter sequence, any
coordinate that exists only in the longer point is silently discarded. As a
result, when a lower-dimensional point and a higher-dimensional point are
compared, the extra coordinate(s) of the higher-dimensional point are ignored,
producing a distance that is too small. For instance, the distance between a
planar point at `(2, 0)` and a spatial point at `(1, 0, 2)` is reported as `1`
instead of the correct `sqrt(5)`.

The goal is to make `Point.distance` account for every coordinate of both
points when they have differing numbers of coordinates, treating a missing
coordinate of the lower-dimensional point as `0`, while preserving the existing
behavior for points that already share the same dimension.

## Requirement 1: Distance across points of differing dimension

**User story:** As a user computing geometric distances, I want the distance
between two points of different dimension to include every coordinate of both
points, so that the result is the true Euclidean distance rather than a value
that drops the extra dimensions.

**Acceptance criteria**

1. WHEN `Point.distance` is called with points that are of different point
   kinds and have a different number of coordinates, THEN the method SHALL
   compute the distance over the larger of the two coordinate counts.
2. WHILE computing a distance across points whose coordinate counts differ, the
   method SHALL treat each coordinate position present in the
   higher-dimensional point but absent from the lower-dimensional point as
   though the lower-dimensional point has coordinate `0` at that position.
3. WHEN `Point.distance` is called such that the shorter point is zero-extended
   to the length of the longer point, THEN the method SHALL return the square
   root of the sum, over all coordinate positions of the longer point, of the
   squared difference between the two points' coordinates at each position.
4. WHEN the distance is computed from a planar point at coordinates `(2, 0)` to
   a spatial point at coordinates `(1, 0, 2)` (in either calling direction),
   THEN the method SHALL return `sqrt(5)`.
5. IF one point has more coordinates than the other, THEN the method SHALL NOT
   discard any coordinate of the higher-dimensional point when forming the sum
   of squared differences.

## Requirement 2: Preserve distance for equal-dimension and same-kind points

**User story:** As a user relying on existing geometry behavior, I want
distances between points that already have the same dimension to be unchanged,
so that established results and downstream computations continue to hold.

**Acceptance criteria**

1. WHEN `Point.distance` is called with two points that have the same number of
   coordinates, THEN the method SHALL return the square root of the sum, over
   each coordinate position, of the squared difference of the corresponding
   coordinates.
2. WHEN `Point.distance` is called with two points of the same point kind, THEN
   the method SHALL pair coordinates position-by-position exactly as before,
   producing the same result it produced prior to this change.
3. WHEN `Point.distance` is called with a symbolic point, THEN the method SHALL
   return the distance as a symbolic expression (for example, the distance from
   a point with symbolic coordinates `(x, y)` to the origin SHALL be
   `sqrt(x**2 + y**2)`).
4. The system SHALL continue to accept, as the argument `p`, either a `Point`
   instance or a plain sequence of coordinates, using that argument's
   coordinates to compute the distance.

## Requirement 3: Preserve unrelated Point behavior

**User story:** As a maintainer, I want the change confined to distance
computation, so that other point operations keep working.

**Acceptance criteria**

1. The system SHALL leave collinearity determination for spatial points
   unchanged.
2. The system SHALL leave coordinate transformation of points unchanged.
3. The system SHALL leave construction and basic properties of planar and
   spatial points unchanged.
