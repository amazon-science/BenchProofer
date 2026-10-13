import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The routine builds the result purely from the four
--  scalar components of a quaternion (and an optional translation point) by
--  closed-form arithmetic; it calls no outside function whose behaviour the
--  proof must assume. The one sub-expression that delegates to an unchanged
--  helper — the inverse square of the quaternion's magnitude — is modeled
--  concretely as the reciprocal of the sum of the four squared components
--  (an exact identity for a nonzero quaternion), NOT consumed as an axiom or
--  A-reference. See refinement.md §C / mapping.md §3.)
-- axioms-end

-- pure-start
/- The scaling factor common to every entry of the orientation matrix of a
   quaternion: the reciprocal of the sum of the squares of its four scalar
   components. For a nonzero quaternion this is exactly the inverse square of
   its magnitude (the square root cancels), so it is captured here as a closed
   rational expression in the components (mapping.md §2, §3). -/
def sFactor (a b c d : Rat) : Rat := (a ^ 2 + b ^ 2 + c ^ 2 + d ^ 2)⁻¹

/- The orientation matrix associated with a quaternion `(a, b, c, d)`.

   With no translation point (`none`) this is the 3×3 matrix whose nine entries
   are the standard closed-form rational functions of the components scaled by
   `sFactor`. With a translation point `(x, y, z)` (`some`) it is the 4×4
   homogeneous extension: the same 3×3 block in the upper-left, a fourth column
   carrying the point displaced by the linear action of the 3×3 block, a bottom
   row `[0, 0, 0, 1]`.

   Every entry is pinned as an explicit arithmetic relation among the inputs, so
   the result must be produced by this exact computation (no opaque oracle). -/
def rotMatrix (a b c d : Rat) (v : Option (Rat × Rat × Rat)) : List (List Rat) :=
  let s := sFactor a b c d
  let m00 := 1 - 2 * s * (c ^ 2 + d ^ 2)
  let m01 := 2 * s * (b * c - d * a)
  let m02 := 2 * s * (b * d + c * a)
  let m10 := 2 * s * (b * c + d * a)
  let m11 := 1 - 2 * s * (b ^ 2 + d ^ 2)
  let m12 := 2 * s * (c * d - b * a)
  let m20 := 2 * s * (b * d - c * a)
  let m21 := 2 * s * (c * d + b * a)
  let m22 := 1 - 2 * s * (b ^ 2 + c ^ 2)
  match v with
  | none => [[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]]
  | some (x, y, z) =>
    let m03 := x - x * m00 - y * m01 - z * m02
    let m13 := y - x * m10 - y * m11 - z * m12
    let m23 := z - x * m20 - y * m21 - z * m22
    [[m00, m01, m02, m03], [m10, m11, m12, m13],
     [m20, m21, m22, m23], [0, 0, 0, 1]]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the orientation matrix of a quaternion `(a, b, c, d)`.

   Without a translation point the result is the 3×3 matrix; with a point
   `(x, y, z)` it is the 4×4 homogeneous matrix that also translates by that
   point. The quaternion must be nonzero (the sum of its squared components is
   nonzero), since the matrix scales every entry by the reciprocal of that sum.

   The four components, the optional point, are all read-only inputs (none
   `mut`): the routine consumes them and returns a freshly assembled matrix,
   mutating nothing (directive 5). Components are modeled as exact rationals
   (`Rat`): the demonstrated behaviour is exact closed-form arithmetic and an
   exact ordered field is faithful for it (mapping.md §2). The result is pinned
   exactly as `rotMatrix`. -/
method toOrientationMatrix (a : Rat) (b : Rat) (c : Rat) (d : Rat) (v : Option (Rat × Rat × Rat))
    return (out : List (List Rat))
  require a ^ 2 + b ^ 2 + c ^ 2 + d ^ 2 ≠ 0
  ensures out = rotMatrix a b c d v
  do
    -- impl-start
    -- Pre-image skeleton: the row-1/column-2 entry pairs the cross term `c*d`
    -- with `b*a` under the SAME sign as the symmetric row-2/column-1 entry
    -- (`c*d + b*a`). The frozen spec requires the orientation-preserving
    -- convention (`c*d - b*a`), so prove_correct MUST fail.
    let s := sFactor a b c d
    let m00 := 1 - 2 * s * (c ^ 2 + d ^ 2)
    let m01 := 2 * s * (b * c - d * a)
    let m02 := 2 * s * (b * d + c * a)
    let m10 := 2 * s * (b * c + d * a)
    let m11 := 1 - 2 * s * (b ^ 2 + d ^ 2)
    let m12 := 2 * s * (c * d + b * a)
    let m20 := 2 * s * (b * d - c * a)
    let m21 := 2 * s * (c * d + b * a)
    let m22 := 1 - 2 * s * (b ^ 2 + c ^ 2)
    let out := match v with
      | none => [[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]]
      | some (x, y, z) =>
        let m03 := x - x * m00 - y * m01 - z * m02
        let m13 := y - x * m10 - y * m11 - z * m12
        let m23 := z - x * m20 - y * m21 - z * m22
        [[m00, m01, m02, m03], [m10, m11, m12, m13],
         [m20, m21, m22, m23], [0, 0, 0, 1]]
    return out
    -- impl-end

prove_correct toOrientationMatrix by
  loom_solve
  simp_all [rotMatrix, sFactor]
