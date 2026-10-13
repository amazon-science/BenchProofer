# Requirements: Scalar multiplication of geometry Points is commutative

## Introduction

In SymPy's geometry module, the `Point` class (`sympy/geometry/point.py`),
together with its concrete subclasses `Point2D` and `Point3D`, supports scaling
by a scalar factor. Multiplying a point on the *right* by a scalar
(`point * factor`) works and returns a new point with each coordinate scaled by
that factor. However, multiplying a point on the *left* by a built-in Python
number (`number * point`) does not behave the same way: because the number's own
multiplication takes over, the operation produces an unevaluated symbolic
product rather than a point. Downstream, this makes an expression such as
`some_point + number * other_point` raise an error, while the equivalent
`some_point + other_point * number` succeeds.

The goal is to make scalar-times-point multiplication commutative for the case
that Python's operator dispatch routes to the point: scaling a point by a
*built-in Python number* (an `int` or `float`) SHALL produce the same point
whether the number appears on the left or the right of the `*` operator, for
points of any ambient dimension, without disturbing the existing point
arithmetic. (When the left operand is instead a SymPy scalar object — e.g. a
sympified number or a symbol — Python resolves the multiplication through that
object rather than through the point, so left multiplication continues to behave
exactly as it did before; the new left-multiplication behavior does not extend
to that case.)

## Requirement 1: Left multiplication of a Point by a scalar

**User story:** As a user of the geometry module, I want to multiply a point by
a built-in Python number with the number written on the left, so that
expressions read naturally and give the same result as writing the number on the
right.

**Acceptance criteria**

1. WHEN a built-in Python number `k` (an `int` or `float`) is multiplied on the
   left by a `Point` (i.e. `k * point`),
   THEN the system SHALL return a `Point` whose every coordinate is the original
   corresponding coordinate multiplied by `k`.
2. WHEN a `Point` is scaled by the same built-in Python number on the left and
   on the right, THEN the system SHALL return equal points (i.e. `k * point`
   SHALL equal `point * k`).
3. The system SHALL apply this left-multiplication behavior to points of any
   ambient dimension, including two-dimensional points and three-dimensional
   points, returning a result of the same concrete point type and dimension as
   the operand.
4. WHEN the left multiplier is a built-in Python `float`, THEN the resulting
   point's coordinates SHALL be the products of the original coordinates with
   that float, consistent with right-side multiplication by the same float.
5. The system SHALL compute `k * point` (for a built-in Python number `k`) by
   the same coordinate-scaling procedure used for right-side multiplication
   `point * k`, so that no new or divergent error behavior is introduced by
   adding left multiplication.

## Requirement 2: Point arithmetic composes with left scalar multiplication

**User story:** As a user, I want to add a point to a point that was left-scaled
by a built-in Python number, so that building expressions like "one point plus a
scaled point" works regardless of the side on which the number was written.

**Acceptance criteria**

1. WHEN an expression adds a `Point` to the left-number product of another
   `Point` by a built-in Python number `k` (i.e. `point_a + k * point_b`),
   THEN the system SHALL return the same point as the corresponding right-side
   form (`point_a + point_b * k`).
2. WHEN forming `point_a + k * point_b` with `k` a built-in Python number, THEN
   the system SHALL NOT raise an error arising from the scaled operand being an
   unevaluated symbolic product instead of a point.

## Requirement 3: Existing point operations are preserved

**User story:** As a maintainer, I want the previously working point operations
to keep behaving exactly as before, so that adding commutative scaling
introduces no regressions.

**Acceptance criteria**

1. The system SHALL keep right-side scalar multiplication of a point
   (`point * k`) returning a point whose coordinates are each scaled by `k`, for
   two- and three-dimensional points.
2. The system SHALL keep scalar division of a point (`point / k`) returning a
   point whose coordinates are each divided by `k`.
3. The system SHALL keep point addition, subtraction, and negation behaving as
   before, including returning a point with the correct combined dimension.
4. WHEN a point is added to a plain number (a non-point, non-coordinate-sequence
   scalar), THEN the system SHALL raise the same error it currently raises for
   that case, rather than silently succeeding.
5. The system SHALL keep point equality, iteration, indexing, length, dimension
   normalization, the dot product, and geometric transforms behaving exactly as
   before.
