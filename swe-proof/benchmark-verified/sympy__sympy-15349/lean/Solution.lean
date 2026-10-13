import Mathlib
-- imports-end

/-!
Building the transformation matrix that a unit-scaled quaternion induces on
space.

A quaternion is its four rational components `(a, b, c, d)`. From them a scale
`s = 1 / (a² + b² + c² + d²)` is formed, and the nine entries of a 3×3 matrix
are given by quadratic expressions in the components, each weighted by `2·s`:

```
[ 1 - 2s(c²+d²)     2s(bc - da)     2s(bd + ca)   ]
[   2s(bc + da)   1 - 2s(b²+d²)     2s(cd - ba)   ]
[   2s(bd - ca)     2s(cd + ba)   1 - 2s(b²+c²)   ]
```

When no translation point is supplied the result is exactly this 3×3 matrix.
When a point `(x, y, z)` is supplied the result is a 4×4 matrix: the same 3×3
block in the top-left, an extra fourth column whose first three entries are the
point coordinate minus the corresponding row of the block applied to the point
(`x - x·row₀·e₀ - y·row₀·e₁ - z·row₀·e₂`, and likewise for the other rows), a
fourth row `(0, 0, 0, 1)`, and the `(i,3)` slot of the new bottom row equal to 1.

Every entry of the produced matrix is pinned to the inputs, and out-of-range
reads of the accessor are pinned to `0` (the stated modeling convention), so no
component of the result is left free.
-/

-- axioms-start
-- No unchanged outside callee is consumed. Every matrix entry is a rational
-- arithmetic expression in the input components and (for the 4×4 case) the
-- supplied point, modeled directly. There is no `opaque`/`axiom` callee
-- contract anywhere in the bundle.
-- axioms-end

-- pure-start
/-- A quaternion abstracted to its four rational components. -/
structure Quat where
  a : ℚ
  b : ℚ
  c : ℚ
  d : ℚ

/-- A matrix: its row/column dimensions together with a value accessor
`get i j` giving the value at row `i`, column `j`. Out-of-range indices read as
`0`. -/
structure Mat where
  rows : Nat
  cols : Nat
  get  : Nat → Nat → ℚ

/-- The reciprocal of the sum of squares of the components. -/
def scale (q : Quat) : ℚ := (q.a ^ 2 + q.b ^ 2 + q.c ^ 2 + q.d ^ 2)⁻¹
-- pure-end

-- post-conditions-start
/-- The produced matrix is pinned entry-by-entry to the inputs.

* With no point (`v = none`): a 3×3 matrix whose nine entries are the quadratic
  expressions in the components weighted by `2·(scale q)`.
* With a point `(x, y, z)` (`v = some (x, y, z)`): a 4×4 matrix whose top-left
  3×3 block is the same nine entries, whose fourth column's first three slots are
  the point coordinate minus the row of the block contracted against the point,
  whose bottom row is `(0, 0, 0, 1)`.

Out-of-range reads of `get` (row or column index at or beyond the dimension)
are pinned to `0`, the stated modeling convention, so the accessor is
determined on its whole domain.

Every entry, and both dimensions, are determined by the inputs. -/
def problem_spec_toRotationMatrix
    (q : Quat) (v : Option (ℚ × ℚ × ℚ)) (result : Mat) : Prop :=
  let s := scale q
  let e00 := 1 - 2 * s * (q.c ^ 2 + q.d ^ 2)
  let e01 := 2 * s * (q.b * q.c - q.d * q.a)
  let e02 := 2 * s * (q.b * q.d + q.c * q.a)
  let e10 := 2 * s * (q.b * q.c + q.d * q.a)
  let e11 := 1 - 2 * s * (q.b ^ 2 + q.d ^ 2)
  let e12 := 2 * s * (q.c * q.d - q.b * q.a)
  let e20 := 2 * s * (q.b * q.d - q.c * q.a)
  let e21 := 2 * s * (q.c * q.d + q.b * q.a)
  let e22 := 1 - 2 * s * (q.b ^ 2 + q.c ^ 2)
  match v with
  | none =>
      result.rows = 3 ∧ result.cols = 3 ∧
      result.get 0 0 = e00 ∧ result.get 0 1 = e01 ∧ result.get 0 2 = e02 ∧
      result.get 1 0 = e10 ∧ result.get 1 1 = e11 ∧ result.get 1 2 = e12 ∧
      result.get 2 0 = e20 ∧ result.get 2 1 = e21 ∧ result.get 2 2 = e22 ∧
      (∀ i j, 3 ≤ i ∨ 3 ≤ j → result.get i j = 0)
  | some (x, y, z) =>
      result.rows = 4 ∧ result.cols = 4 ∧
      result.get 0 0 = e00 ∧ result.get 0 1 = e01 ∧ result.get 0 2 = e02 ∧
      result.get 1 0 = e10 ∧ result.get 1 1 = e11 ∧ result.get 1 2 = e12 ∧
      result.get 2 0 = e20 ∧ result.get 2 1 = e21 ∧ result.get 2 2 = e22 ∧
      result.get 0 3 = x - x * e00 - y * e01 - z * e02 ∧
      result.get 1 3 = y - x * e10 - y * e11 - z * e12 ∧
      result.get 2 3 = z - x * e20 - y * e21 - z * e22 ∧
      result.get 3 0 = 0 ∧ result.get 3 1 = 0 ∧ result.get 3 2 = 0 ∧
      result.get 3 3 = 1 ∧
      (∀ i j, 4 ≤ i ∨ 4 ≤ j → result.get i j = 0)
-- post-conditions-end

-- impl-start
def implementation_toRotationMatrix
    (q : Quat) (v : Option (ℚ × ℚ × ℚ)) : Mat := Id.run do
  let s := scale q
  let m00 := 1 - 2 * s * (q.c ^ 2 + q.d ^ 2)
  let m01 := 2 * s * (q.b * q.c - q.d * q.a)
  let m02 := 2 * s * (q.b * q.d + q.c * q.a)
  let m10 := 2 * s * (q.b * q.c + q.d * q.a)
  let m11 := 1 - 2 * s * (q.b ^ 2 + q.d ^ 2)
  let m12 := 2 * s * (q.c * q.d - q.b * q.a)
  let m20 := 2 * s * (q.b * q.d - q.c * q.a)
  let m21 := 2 * s * (q.c * q.d + q.b * q.a)
  let m22 := 1 - 2 * s * (q.b ^ 2 + q.c ^ 2)
  match v with
  | none =>
      return {
        rows := 3, cols := 3,
        get := fun i j =>
          (([[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]].getD i []).getD j 0) }
  | some (x, y, z) =>
      let m03 := x - x * m00 - y * m01 - z * m02
      let m13 := y - x * m10 - y * m11 - z * m12
      let m23 := z - x * m20 - y * m21 - z * m22
      return {
        rows := 4, cols := 4,
        get := fun i j =>
          (([[m00, m01, m02, m03], [m10, m11, m12, m13],
             [m20, m21, m22, m23], [0, 0, 0, 1]].getD i []).getD j 0) }
-- impl-end

-- proof-start
/-- Reading a row-major nested-list matrix at an out-of-range index (row or
column at/beyond the bound `k`) yields the default `0`, provided the outer
list and every row have length at most `k`. -/
private theorem getD_getD_eq_zero (L : List (List ℚ)) (k : Nat)
    (hL : L.length ≤ k) (hr : ∀ r ∈ L, r.length ≤ k) :
    ∀ i j, k ≤ i ∨ k ≤ j → (L.getD i []).getD j 0 = 0 := by
  intro i j h
  rcases h with hi | hj
  · rw [List.getD_eq_default _ _ (le_trans hL hi)]
    simp
  · by_cases hiL : i < L.length
    · have hm : L.getD i [] ∈ L := by
        rw [List.getD_eq_getElem _ _ hiL]
        exact List.getElem_mem hiL
      exact List.getD_eq_default _ _ (le_trans (hr _ hm) hj)
    · rw [List.getD_eq_default _ _ (Nat.le_of_not_lt hiL)]
      simp

theorem correct_toRotationMatrix :
    ∀ (q : Quat) (v : Option (ℚ × ℚ × ℚ)),
      q.a ^ 2 + q.b ^ 2 + q.c ^ 2 + q.d ^ 2 ≠ 0 →
      problem_spec_toRotationMatrix q v (implementation_toRotationMatrix q v) := by
  intro q v _
  unfold problem_spec_toRotationMatrix implementation_toRotationMatrix
  cases v with
  | none =>
      refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, ?_⟩
      intro i j h
      exact getD_getD_eq_zero _ 3 (by simp)
        (by intro r hr; fin_cases hr <;> simp) i j h
  | some p =>
      obtain ⟨x, y, z⟩ := p
      refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl,
        rfl, rfl, rfl, rfl, ?_⟩
      intro i j h
      exact getD_getD_eq_zero _ 4 (by simp)
        (by intro r hr; fin_cases hr <;> simp) i j h
-- proof-end
