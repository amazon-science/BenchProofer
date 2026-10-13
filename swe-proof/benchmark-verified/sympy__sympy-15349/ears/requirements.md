# Requirements — Quaternion.to_rotation_matrix sign correction

## Introduction

`Quaternion.to_rotation_matrix(v=None)` in `sympy/algebras/quaternion.py`
returns the rotation transformation matrix induced by a quaternion. Given a
quaternion with real part `a` and imaginary parts `b`, `c`, `d`, and the common
scale factor `s = norm()**-2`, the matrix entries are quadratic expressions in
`(a, b, c, d)` weighted by `2*s`.

The method produced an incorrect matrix: for a quaternion representing a pure
rotation about the first axis, `Quaternion(cos(x/2), sin(x/2), 0, 0)`, the
returned matrix had **both** off-diagonal trigonometric entries equal to
`sin(x)`, whereas a proper rotation matrix requires the entry above the diagonal
to be `-sin(x)` and the entry below it to be `+sin(x)`. Concretely, the entry in
the second row / third column of the 3×3 block carried the wrong sign on its
cross term. Because the 4×4 (affine) form's translation column is a linear
function of that entry, the same defect propagated to the 4×4 output.

The goal is to make `to_rotation_matrix` return the mathematically correct
rotation matrix (matching the standard quaternion-derived rotation-matrix
formula) while leaving every other entry, and the method's other supported
behaviors, unchanged.

## Requirement 1: Correct sign of the second-row / third-column off-diagonal entry

**User story:** As a user computing a rotation matrix from a quaternion, I want
the off-diagonal entries to carry the correct signs, so that the result is a
proper rotation and matches the standard reference formula.

**Acceptance criteria**

1. WHEN `to_rotation_matrix()` is called (no point argument) on a quaternion
   with components `(a, b, c, d)` and scale factor `s = norm()**-2`, THEN the
   entry in the second row and third column of the returned 3×3 matrix SHALL
   equal `2*s*(c*d - b*a)` (the cross term `b*a` subtracted, not added).
2. WHEN `to_rotation_matrix()` is called, THEN the entry in the third row and
   second column of the returned 3×3 matrix SHALL equal `2*s*(c*d + b*a)`.
3. The system SHALL ensure the second-row/third-column entry and the
   third-row/second-column entry carry **opposite** signs on the `b*a` cross
   term (one subtracted, one added) rather than identical signs.

## Requirement 2: Correct rotation matrix for rotation about the first axis

**User story:** As a user rotating about a single axis, I want the resulting
matrix to be the textbook rotation matrix, so that applying it rotates vectors
by the expected signed angle.

**Acceptance criteria**

1. WHEN `to_rotation_matrix()` is called on a unit quaternion representing a
   rotation by angle `x` about the first axis (real part `cos(x/2)`, first
   imaginary part `sin(x/2)`, remaining components zero), and the result is
   simplified with `trigsimp`, THEN the returned 3×3 matrix SHALL be the
   standard rotation about the first axis: its first row and first column
   SHALL be `(1, 0, 0)`; its second-row/second-column and
   third-row/third-column diagonal entries SHALL each be `cos(x)`; its
   second-row/third-column entry SHALL be `-sin(x)`; and its
   third-row/second-column entry SHALL be `sin(x)`.
2. IF a quaternion represents a rotation about the first axis, THEN the entry
   above the diagonal in the rotated 2×2 sub-block SHALL be the negative of the
   entry below the diagonal (i.e. `-sin(x)` above, `+sin(x)` below), not equal
   to it.

## Requirement 3: Consistent 4×4 affine (translation) form

**User story:** As a user requesting rotation about a point other than the
origin, I want the 4×4 affine matrix to embed the corrected 3×3 rotation block
consistently, so that the translation column reflects the corrected entries.

**Acceptance criteria**

1. WHEN `to_rotation_matrix(v)` is called with a point `v = (x, y, z)`, THEN the
   upper-left 3×3 block of the returned 4×4 matrix SHALL contain the same
   corrected entries as the 3×3 form (per Requirement 1), including the
   second-row/third-column entry `2*s*(c*d - b*a)`.
2. WHEN `to_rotation_matrix(v)` is called with `v = (x, y, z)`, THEN each entry
   of the extra (fourth) column in rows 0–2 SHALL equal
   `p_i - (x*m_i0 + y*m_i1 + z*m_i2)`, where `p = (x, y, z)` and `m_i0, m_i1,
   m_i2` are the corrected 3×3 entries of that row, so that the translation
   column reflects the corrected second-row/third-column entry.
3. WHEN `to_rotation_matrix(v)` is called, THEN the fourth row of the returned
   4×4 matrix SHALL be `(0, 0, 0, 1)`.

## Requirement 4: Preserve all other matrix entries and method behaviors

**User story:** As a maintainer, I want only the defective sign to change, so
that no previously-correct behavior regresses.

**Acceptance criteria**

1. WHEN `to_rotation_matrix()` is called, THEN the three diagonal entries SHALL
   remain `1 - 2*s*(c**2 + d**2)`, `1 - 2*s*(b**2 + d**2)`, and
   `1 - 2*s*(b**2 + c**2)` respectively.
2. WHEN `to_rotation_matrix()` is called, THEN the remaining off-diagonal
   entries SHALL remain `2*s*(b*c - d*a)` (first row / second column),
   `2*s*(b*d + c*a)` (first row / third column), `2*s*(b*c + d*a)` (second row /
   first column), and `2*s*(b*d - c*a)` (third row / first column).
3. WHEN `to_rotation_matrix()` is called without a point argument, THEN the
   result SHALL be a 3×3 `Matrix`; WHEN called with a point argument, THEN the
   result SHALL be a 4×4 `Matrix`.
4. WHEN `to_axis_angle()` is called on a quaternion, THEN its returned axis
   vector and rotation angle SHALL be unchanged by this fix.
5. The system SHALL leave quaternion construction, complex/real addition, and
   the other quaternion functions (norm, multiplication, differentiation,
   integration, point rotation, etc.) behaving exactly as before.
