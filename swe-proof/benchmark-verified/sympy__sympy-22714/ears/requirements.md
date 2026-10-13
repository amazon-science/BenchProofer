# Requirements: geometric Point construction with real numeric coordinates under disabled evaluation

## Introduction

`sympy.geometry.point.Point` is the base constructor for geometric points; its
`__new__` builds a `Point2D` or `Point3D` (or a general point) from a sequence
of coordinates. Among its validation steps, it rejects coordinates that are
numeric and have a nonzero imaginary part, raising
`ValueError('Imaginary coordinates are not permitted.')`. This same constructor
is reached when a point is built via `sympify` / `parse_expr` of an expression
such as `Point2D(Integer(1), Integer(2))`, and both `Point2D.__new__` and
`Point3D.__new__` funnel their coordinates through `Point.__new__`.

A defect appears when automatic evaluation is disabled — either through the
`evaluate` context manager in `sympy.core.parameters` set to a false state, or
with an explicit `evaluate=False`. Under disabled evaluation, computing the imaginary
part of a purely real numeric coordinate (for example the integer `1`) does not
simplify to the literal `0`; it stays as an unevaluated expression. The
imaginary-coordinate guard, which was written to reject any coordinate whose
imaginary part was merely "truthy", then misfires on genuinely real inputs and
wrongly raises `Imaginary coordinates are not permitted.` — so constructing a
point with real coordinates crashes when evaluation is turned off, even though
the identical construction succeeds with evaluation on.

The goal is to make the imaginary-coordinate rejection fire only when a numeric
coordinate's imaginary part is definitely nonzero, so that real numeric
coordinates are accepted regardless of the evaluation setting, while still
rejecting coordinates that are actually imaginary and preserving every other
construction and validation behavior.

## Requirement 1: Real numeric coordinates are accepted when evaluation is disabled

**User story:** As a user building geometric points, I want a point with real
numeric coordinates to be constructed successfully even when automatic
evaluation is disabled, so that turning evaluation off does not spuriously
reject valid input.

**Acceptance criteria**

1. WHEN `Point` is constructed with coordinates that are all real numbers while
   automatic evaluation is disabled through the `evaluate` context manager set
   to a false state, THEN the constructor SHALL return the corresponding point
   without raising.
2. WHEN `Point` is constructed with coordinates that are all real numbers and
   `evaluate=False` is passed explicitly, THEN the constructor SHALL return the
   corresponding point without raising.
3. WHEN two real numeric coordinates are supplied, THEN the constructor SHALL
   produce a two-dimensional point (`Point2D`) whose coordinates equal the
   supplied values, and WHEN three real numeric coordinates are supplied it
   SHALL produce a three-dimensional point (`Point3D`), for both the
   evaluation-enabled and evaluation-disabled cases.
4. The system SHALL treat a coordinate whose imaginary part is zero, or whose
   imaginary part cannot be determined to be nonzero, as a permissible real
   coordinate rather than an imaginary one.

## Requirement 2: Genuinely imaginary numeric coordinates are still rejected

**User story:** As a user, I want points with truly imaginary coordinates to
remain forbidden, so that the fix for the evaluation-disabled case does not
silently accept invalid geometry.

**Acceptance criteria**

1. IF any supplied coordinate is a number whose imaginary part is definitely
   nonzero, THEN the constructor SHALL raise `ValueError` reporting that
   imaginary coordinates are not permitted, regardless of the evaluation
   setting.
2. WHEN all supplied coordinates are numbers with zero imaginary part, THEN the
   constructor SHALL NOT raise the imaginary-coordinate error.
3. WHEN a supplied coordinate is symbolic or otherwise not a concrete number
   (its numeric status is not established), THEN the imaginary-coordinate check
   SHALL NOT reject it on the basis of an undetermined imaginary part.

## Requirement 3: All other Point construction and validation behavior is preserved (regression protection)

**User story:** As a maintainer, I want every other aspect of point
construction to behave exactly as before, so that the fix introduces no
regressions.

**Acceptance criteria**

1. WHEN fewer than two coordinates are supplied and no dimension keyword raises
   the count, THEN the constructor SHALL raise `ValueError` indicating that a
   point requires two or more coordinates.
2. WHEN a coordinate that is not a valid SymPy expression is supplied, THEN the
   constructor SHALL raise `TypeError` indicating that coordinates must be
   valid SymPy expressions.
3. WHEN the argument passed is not a sequence of coordinates, THEN the
   constructor SHALL raise `TypeError` describing the expected sequence.
4. WHEN a dimension is reduced but the coordinates being removed are nonzero,
   THEN the constructor SHALL raise `ValueError` indicating that nonzero
   coordinates cannot be removed.
5. WHEN evaluation is enabled and floating-point coordinates are supplied, THEN
   the constructor SHALL continue to convert them to rational form and simplify
   them as before; WHEN evaluation is disabled, THEN it SHALL leave the
   coordinates unconverted.
6. WHEN an existing `Point` instance of the same dimension is passed, THEN the
   constructor SHALL return it unchanged, and the dimension-morphing behavior
   controlled by the `on_morph` option SHALL be unchanged.
7. The system SHALL keep the construction of `Point`, `Point2D`, and `Point3D`
   via direct calls and via `sympify` / `parse_expr` producing the same points
   as before for all previously-accepted inputs.
