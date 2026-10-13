# P2 adversarial audit — sympy__sympy-15349

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```lean
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
```diff
@@ -1,19 +1,3 @@
-import Mathlib
--- imports-end
-
-/-!
-Building the transformation matrix that a unit-scaled quaternion induces on
-space.
-
-A quaternion is its four rational components `(a, b, c, d)`. From them a scale
-`s = 1 / (a² + b² + c² + d²)` is formed, and the nine entries of a 3×3 matrix
-are given by quadratic expressions in the components, each weighted by `2·s`:
-
-```
-[ 1 - 2s(c²+d²)     2s(bc - da)     2s(bd + ca)   ]
-[   2s(bc + da)   1 - 2s(b²+d²)     2s(cd - ba)   ]
-[   2s(bd - ca)     2s(cd + ba)   1 - 2s(b²+c²)   ]
-```
 
 When no translation point is supplied the result is exactly this 3×3 matrix.
 When a point `(x, y, z)` is supplied the result is a 4×4 matrix: the same 3×3
@@ -110,7 +94,7 @@
   let m02 := 2 * s * (q.b * q.d + q.c * q.a)
   let m10 := 2 * s * (q.b * q.c + q.d * q.a)
   let m11 := 1 - 2 * s * (q.b ^ 2 + q.d ^ 2)
-  let m12 := 2 * s * (q.c * q.d - q.b * q.a)
+  let m12 := 2 * s * (q.c * q.d + q.b * q.a)
   let m20 := 2 * s * (q.b * q.d - q.c * q.a)
   let m21 := 2 * s * (q.c * q.d + q.b * q.a)
   let m22 := 1 - 2 * s * (q.b ^ 2 + q.c ^ 2)
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```lean
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
```diff
@@ -1,19 +1,3 @@
-import Mathlib
--- imports-end
-
-/-!
-Building the transformation matrix that a unit-scaled quaternion induces on
-space.
-
-A quaternion is its four rational components `(a, b, c, d)`. From them a scale
-`s = 1 / (a² + b² + c² + d²)` is formed, and the nine entries of a 3×3 matrix
-are given by quadratic expressions in the components, each weighted by `2·s`:
-
-```
-[ 1 - 2s(c²+d²)     2s(bc - da)     2s(bd + ca)   ]
-[   2s(bc + da)   1 - 2s(b²+d²)     2s(cd - ba)   ]
-[   2s(bd - ca)     2s(cd + ba)   1 - 2s(b²+c²)   ]
-```
 
 When no translation point is supplied the result is exactly this 3×3 matrix.
 When a point `(x, y, z)` is supplied the result is a 4×4 matrix: the same 3×3
@@ -119,7 +103,7 @@
       return {
         rows := 3, cols := 3,
         get := fun i j =>
-          (([[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]].getD i []).getD j 0) }
+          (([[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]].getD i []).getD j 7) }
   | some (x, y, z) =>
       let m03 := x - x * m00 - y * m01 - z * m02
       let m13 := y - x * m10 - y * m11 - z * m12
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```lean
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
```diff
@@ -1,19 +1,3 @@
-import Mathlib
--- imports-end
-
-/-!
-Building the transformation matrix that a unit-scaled quaternion induces on
-space.
-
-A quaternion is its four rational components `(a, b, c, d)`. From them a scale
-`s = 1 / (a² + b² + c² + d²)` is formed, and the nine entries of a 3×3 matrix
-are given by quadratic expressions in the components, each weighted by `2·s`:
-
-```
-[ 1 - 2s(c²+d²)     2s(bc - da)     2s(bd + ca)   ]
-[   2s(bc + da)   1 - 2s(b²+d²)     2s(cd - ba)   ]
-[   2s(bd - ca)     2s(cd + ba)   1 - 2s(b²+c²)   ]
-```
 
 When no translation point is supplied the result is exactly this 3×3 matrix.
 When a point `(x, y, z)` is supplied the result is a 4×4 matrix: the same 3×3
@@ -110,9 +94,9 @@
   let m02 := 2 * s * (q.b * q.d + q.c * q.a)
   let m10 := 2 * s * (q.b * q.c + q.d * q.a)
   let m11 := 1 - 2 * s * (q.b ^ 2 + q.d ^ 2)
-  let m12 := 2 * s * (q.c * q.d - q.b * q.a)
+  let m12 := 2 * s * (q.c * q.d + q.b * q.a)
   let m20 := 2 * s * (q.b * q.d - q.c * q.a)
-  let m21 := 2 * s * (q.c * q.d + q.b * q.a)
+  let m21 := 2 * s * (q.c * q.d - q.b * q.a)
   let m22 := 1 - 2 * s * (q.b ^ 2 + q.c ^ 2)
   match v with
   | none =>
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```lean
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
```diff
@@ -1,19 +1,3 @@
-import Mathlib
--- imports-end
-
-/-!
-Building the transformation matrix that a unit-scaled quaternion induces on
-space.
-
-A quaternion is its four rational components `(a, b, c, d)`. From them a scale
-`s = 1 / (a² + b² + c² + d²)` is formed, and the nine entries of a 3×3 matrix
-are given by quadratic expressions in the components, each weighted by `2·s`:
-
-```
-[ 1 - 2s(c²+d²)     2s(bc - da)     2s(bd + ca)   ]
-[   2s(bc + da)   1 - 2s(b²+d²)     2s(cd - ba)   ]
-[   2s(bd - ca)     2s(cd + ba)   1 - 2s(b²+c²)   ]
-```
 
 When no translation point is supplied the result is exactly this 3×3 matrix.
 When a point `(x, y, z)` is supplied the result is a 4×4 matrix: the same 3×3
@@ -117,7 +101,7 @@
   match v with
   | none =>
       return {
-        rows := 3, cols := 3,
+        rows := 4, cols := 3,
         get := fun i j =>
           (([[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]].getD i []).getD j 0) }
   | some (x, y, z) =>
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```lean
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
```diff
@@ -1,19 +1,3 @@
-import Mathlib
--- imports-end
-
-/-!
-Building the transformation matrix that a unit-scaled quaternion induces on
-space.
-
-A quaternion is its four rational components `(a, b, c, d)`. From them a scale
-`s = 1 / (a² + b² + c² + d²)` is formed, and the nine entries of a 3×3 matrix
-are given by quadratic expressions in the components, each weighted by `2·s`:
-
-```
-[ 1 - 2s(c²+d²)     2s(bc - da)     2s(bd + ca)   ]
-[   2s(bc + da)   1 - 2s(b²+d²)     2s(cd - ba)   ]
-[   2s(bd - ca)     2s(cd + ba)   1 - 2s(b²+c²)   ]
-```
 
 When no translation point is supplied the result is exactly this 3×3 matrix.
 When a point `(x, y, z)` is supplied the result is a 4×4 matrix: the same 3×3
@@ -106,7 +90,7 @@
     (q : Quat) (v : Option (ℚ × ℚ × ℚ)) : Mat := Id.run do
   let s := scale q
   let m00 := 1 - 2 * s * (q.c ^ 2 + q.d ^ 2)
-  let m01 := 2 * s * (q.b * q.c - q.d * q.a)
+  let m01 := 2 * s * (q.b * q.c + q.d * q.a)
   let m02 := 2 * s * (q.b * q.d + q.c * q.a)
   let m10 := 2 * s * (q.b * q.c + q.d * q.a)
   let m11 := 1 - 2 * s * (q.b ^ 2 + q.d ^ 2)
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```lean
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
```diff
@@ -1,19 +1,3 @@
-import Mathlib
--- imports-end
-
-/-!
-Building the transformation matrix that a unit-scaled quaternion induces on
-space.
-
-A quaternion is its four rational components `(a, b, c, d)`. From them a scale
-`s = 1 / (a² + b² + c² + d²)` is formed, and the nine entries of a 3×3 matrix
-are given by quadratic expressions in the components, each weighted by `2·s`:
-
-```
-[ 1 - 2s(c²+d²)     2s(bc - da)     2s(bd + ca)   ]
-[   2s(bc + da)   1 - 2s(b²+d²)     2s(cd - ba)   ]
-[   2s(bd - ca)     2s(cd + ba)   1 - 2s(b²+c²)   ]
-```
 
 When no translation point is supplied the result is exactly this 3×3 matrix.
 When a point `(x, y, z)` is supplied the result is a 4×4 matrix: the same 3×3
@@ -121,7 +105,7 @@
         get := fun i j =>
           (([[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]].getD i []).getD j 0) }
   | some (x, y, z) =>
-      let m03 := x - x * m00 - y * m01 - z * m02
+      let m03 := x - x * m00 - y * m01
       let m13 := y - x * m10 - y * m11 - z * m12
       let m23 := z - x * m20 - y * m21 - z * m22
       return {
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```lean
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
```diff
@@ -1,19 +1,3 @@
-import Mathlib
--- imports-end
-
-/-!
-Building the transformation matrix that a unit-scaled quaternion induces on
-space.
-
-A quaternion is its four rational components `(a, b, c, d)`. From them a scale
-`s = 1 / (a² + b² + c² + d²)` is formed, and the nine entries of a 3×3 matrix
-are given by quadratic expressions in the components, each weighted by `2·s`:
-
-```
-[ 1 - 2s(c²+d²)     2s(bc - da)     2s(bd + ca)   ]
-[   2s(bc + da)   1 - 2s(b²+d²)     2s(cd - ba)   ]
-[   2s(bd - ca)     2s(cd + ba)   1 - 2s(b²+c²)   ]
-```
 
 When no translation point is supplied the result is exactly this 3×3 matrix.
 When a point `(x, y, z)` is supplied the result is a 4×4 matrix: the same 3×3
@@ -119,7 +103,11 @@
       return {
         rows := 3, cols := 3,
         get := fun i j =>
-          (([[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]].getD i []).getD j 0) }
+          match i, j with
+          | 0, 0 => m00 | 0, 1 => m01 | 0, 2 => m02
+          | 1, 0 => m10 | 1, 1 => m11 | 1, 2 => m12
+          | 2, 0 => m20 | 2, 1 => m21 | 2, 2 => m22
+          | _, _ => 0 }
   | some (x, y, z) =>
       let m03 := x - x * m00 - y * m01 - z * m02
       let m13 := y - x * m10 - y * m11 - z * m12
@@ -127,29 +115,15 @@
       return {
         rows := 4, cols := 4,
         get := fun i j =>
-          (([[m00, m01, m02, m03], [m10, m11, m12, m13],
-             [m20, m21, m22, m23], [0, 0, 0, 1]].getD i []).getD j 0) }
+          match i, j with
+          | 0, 0 => m00 | 0, 1 => m01 | 0, 2 => m02 | 0, 3 => m03
+          | 1, 0 => m10 | 1, 1 => m11 | 1, 2 => m12 | 1, 3 => m13
+          | 2, 0 => m20 | 2, 1 => m21 | 2, 2 => m22 | 2, 3 => m23
+          | 3, 0 => 0   | 3, 1 => 0   | 3, 2 => 0   | 3, 3 => 1
+          | _, _ => 0 }
 -- impl-end
 
 -- proof-start
-/-- Reading a row-major nested-list matrix at an out-of-range index (row or
-column at/beyond the bound `k`) yields the default `0`, provided the outer
-list and every row have length at most `k`. -/
-private theorem getD_getD_eq_zero (L : List (List ℚ)) (k : Nat)
-    (hL : L.length ≤ k) (hr : ∀ r ∈ L, r.length ≤ k) :
-    ∀ i j, k ≤ i ∨ k ≤ j → (L.getD i []).getD j 0 = 0 := by
-  intro i j h
-  rcases h with hi | hj
-  · rw [List.getD_eq_default _ _ (le_trans hL hi)]
-    simp
-  · by_cases hiL : i < L.length
-    · have hm : L.getD i [] ∈ L := by
-        rw [List.getD_eq_getElem _ _ hiL]
-        exact List.getElem_mem hiL
-      exact List.getD_eq_default _ _ (le_trans (hr _ hm) hj)
-    · rw [List.getD_eq_default _ _ (Nat.le_of_not_lt hiL)]
-      simp
-
 theorem correct_toRotationMatrix :
     ∀ (q : Quat) (v : Option (ℚ × ℚ × ℚ)),
       q.a ^ 2 + q.b ^ 2 + q.c ^ 2 + q.d ^ 2 ≠ 0 →
@@ -160,13 +134,20 @@
   | none =>
       refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, ?_⟩
       intro i j h
-      exact getD_getD_eq_zero _ 3 (by simp)
-        (by intro r hr; fin_cases hr <;> simp) i j h
+      match i, j with
+      | 0, 0 | 0, 1 | 0, 2 | 1, 0 | 1, 1 | 1, 2 | 2, 0 | 2, 1 | 2, 2 =>
+        omega
+      | i+3, j => rfl
+      | 0, j+3 | 1, j+3 | 2, j+3 => rfl
   | some p =>
       obtain ⟨x, y, z⟩ := p
       refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl,
         rfl, rfl, rfl, rfl, ?_⟩
       intro i j h
-      exact getD_getD_eq_zero _ 4 (by simp)
-        (by intro r hr; fin_cases hr <;> simp) i j h
+      match i, j with
+      | 0, 0 | 0, 1 | 0, 2 | 0, 3 | 1, 0 | 1, 1 | 1, 2 | 1, 3
+      | 2, 0 | 2, 1 | 2, 2 | 2, 3 | 3, 0 | 3, 1 | 3, 2 | 3, 3 =>
+        omega
+      | i+4, j => rfl
+      | 0, j+4 | 1, j+4 | 2, j+4 | 3, j+4 => rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
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
```diff
@@ -1,19 +1,3 @@
-import Mathlib
--- imports-end
-
-/-!
-Building the transformation matrix that a unit-scaled quaternion induces on
-space.
-
-A quaternion is its four rational components `(a, b, c, d)`. From them a scale
-`s = 1 / (a² + b² + c² + d²)` is formed, and the nine entries of a 3×3 matrix
-are given by quadratic expressions in the components, each weighted by `2·s`:
-
-```
-[ 1 - 2s(c²+d²)     2s(bc - da)     2s(bd + ca)   ]
-[   2s(bc + da)   1 - 2s(b²+d²)     2s(cd - ba)   ]
-[   2s(bd - ca)     2s(cd + ba)   1 - 2s(b²+c²)   ]
-```
 
 When no translation point is supplied the result is exactly this 3×3 matrix.
 When a point `(x, y, z)` is supplied the result is a 4×4 matrix: the same 3×3
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Same-spec check True for all 7 attacks (swebench_unified.markers.same_spec, lean). Positive control (gold Solution.lean) verifies: lean_verify.sh exit 0; #print axioms correct_toRotationMatrix => [propext, Classical.choice, Quot.sound] (clean, no sorryAx).

The spec problem_spec_toRotationMatrix is EXTENSIONALLY COMPLETE: it pins every in-range entry (9 slots for the none/3x3 branch, 16 slots for the some/4x4 branch), pins both dimensions (rows/cols), AND pins ALL out-of-range reads to 0 (∀ i j, dim ≤ i ∨ dim ≤ j → get i j = 0). This is the P1-repaired tight spec that removes the accessor's free degrees of freedom. No axiom/opaque is declared or consumed anywhere (grep for ^axiom|^opaque => NONE); refinement.md legs are all R/I with no A-consumed/A-reference legs, so there is nothing in the A-leg class to audit; mapping's scale q = (a²+b²+c²+d²)⁻¹ ↔ norm()**-2 is an R op modeled directly (exact for nonzero norm).

6 DISTINCT wrong impls (impl region only edited, axioms/pure/pre/post byte-identical), each keeping the official proof, ALL FAIL to verify (real spec-violation errors, not syntax):
- atk_1 (prepatch bug, m12 wrong sign '+'): lean_verify.sh exit 1, 'Application type mismatch' at the e12 rfl. PREPATCH REPRODUCED. cmd: `bash scripts/lean_verify.sh atk_1.lean`.
- atk_2 (ungrounded/out-of-range garbage: getD default 7 instead of 0): exit 1, fails the '= 0' out-of-range clause.
- atk_3 (m12/m21 swap — control-flow-effect): exit 1, type mismatch at e12 rfl.
- atk_4 (boundary: wrong dims rows:=4 in none branch): exit 1, type mismatch at rows rfl.
- atk_5 (m01 wrong sign — partial-domain divergence): exit 1, type mismatch at e01 rfl.
- atk_6 (4x4 m03 drops the -z*m02 term): exit 1, type mismatch at the m03 (get 0 3) rfl.

atk_7 (ungrounded-oracle ECHO): a genuinely different construction (per-index `match i,j` accessor instead of nested-list getD) producing IDENTICAL observable values to gold; verifies lean_verify.sh exit 0 with clean axioms [propext, Classical.choice, Quot.sound]. Per protocol I materialized its faithful patch (= the gold sign fix, since its impl values equal gold) and RAN it through the official harness: run_resolve('sympy__sympy-15349', ...) => RESOLVED=True (note='resolved'). So this closing clean-axiom candidate's faithful patch DOES resolve — verify⇒correct holds; NOT a break (this is exactly the resolving-echo case that is not a weakness per the 2026-08-06 G-PANEL-1 policy).

Concurrency: attacks 1-4 and 5-7 run as background batches (≤4 at a time) per instructions.

No same-spec wrong impl closes with clean axioms, hence no candidate exists whose faithful patch could fail to resolve. verify⇏correct could not be exhibited. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```lean
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
```diff
@@ -1,19 +1,3 @@
-import Mathlib
--- imports-end
-
-/-!
-Building the transformation matrix that a unit-scaled quaternion induces on
-space.
-
-A quaternion is its four rational components `(a, b, c, d)`. From them a scale
-`s = 1 / (a² + b² + c² + d²)` is formed, and the nine entries of a 3×3 matrix
-are given by quadratic expressions in the components, each weighted by `2·s`:
-
-```
-[ 1 - 2s(c²+d²)     2s(bc - da)     2s(bd + ca)   ]
-[   2s(bc + da)   1 - 2s(b²+d²)     2s(cd - ba)   ]
-[   2s(bd - ca)     2s(cd + ba)   1 - 2s(b²+c²)   ]
-```
 
 When no translation point is supplied the result is exactly this 3×3 matrix.
 When a point `(x, y, z)` is supplied the result is a 4×4 matrix: the same 3×3
@@ -110,7 +94,7 @@
   let m02 := 2 * s * (q.b * q.d + q.c * q.a)
   let m10 := 2 * s * (q.b * q.c + q.d * q.a)
   let m11 := 1 - 2 * s * (q.b ^ 2 + q.d ^ 2)
-  let m12 := 2 * s * (q.c * q.d - q.b * q.a)
+  let m12 := 2 * s * (q.c * q.d + q.b * q.a)
   let m20 := 2 * s * (q.b * q.d - q.c * q.a)
   let m21 := 2 * s * (q.c * q.d + q.b * q.a)
   let m22 := 1 - 2 * s * (q.b ^ 2 + q.c ^ 2)
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```lean
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
```diff
@@ -1,19 +1,3 @@
-import Mathlib
--- imports-end
-
-/-!
-Building the transformation matrix that a unit-scaled quaternion induces on
-space.
-
-A quaternion is its four rational components `(a, b, c, d)`. From them a scale
-`s = 1 / (a² + b² + c² + d²)` is formed, and the nine entries of a 3×3 matrix
-are given by quadratic expressions in the components, each weighted by `2·s`:
-
-```
-[ 1 - 2s(c²+d²)     2s(bc - da)     2s(bd + ca)   ]
-[   2s(bc + da)   1 - 2s(b²+d²)     2s(cd - ba)   ]
-[   2s(bd - ca)     2s(cd + ba)   1 - 2s(b²+c²)   ]
-```
 
 When no translation point is supplied the result is exactly this 3×3 matrix.
 When a point `(x, y, z)` is supplied the result is a 4×4 matrix: the same 3×3
@@ -119,7 +103,7 @@
       return {
         rows := 3, cols := 3,
         get := fun i j =>
-          (([[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]].getD i []).getD j 0) }
+          (([[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]].getD i []).getD j 7) }
   | some (x, y, z) =>
       let m03 := x - x * m00 - y * m01 - z * m02
       let m13 := y - x * m10 - y * m11 - z * m12
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```lean
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
```diff
@@ -1,19 +1,3 @@
-import Mathlib
--- imports-end
-
-/-!
-Building the transformation matrix that a unit-scaled quaternion induces on
-space.
-
-A quaternion is its four rational components `(a, b, c, d)`. From them a scale
-`s = 1 / (a² + b² + c² + d²)` is formed, and the nine entries of a 3×3 matrix
-are given by quadratic expressions in the components, each weighted by `2·s`:
-
-```
-[ 1 - 2s(c²+d²)     2s(bc - da)     2s(bd + ca)   ]
-[   2s(bc + da)   1 - 2s(b²+d²)     2s(cd - ba)   ]
-[   2s(bd - ca)     2s(cd + ba)   1 - 2s(b²+c²)   ]
-```
 
 When no translation point is supplied the result is exactly this 3×3 matrix.
 When a point `(x, y, z)` is supplied the result is a 4×4 matrix: the same 3×3
@@ -110,9 +94,9 @@
   let m02 := 2 * s * (q.b * q.d + q.c * q.a)
   let m10 := 2 * s * (q.b * q.c + q.d * q.a)
   let m11 := 1 - 2 * s * (q.b ^ 2 + q.d ^ 2)
-  let m12 := 2 * s * (q.c * q.d - q.b * q.a)
+  let m12 := 2 * s * (q.c * q.d + q.b * q.a)
   let m20 := 2 * s * (q.b * q.d - q.c * q.a)
-  let m21 := 2 * s * (q.c * q.d + q.b * q.a)
+  let m21 := 2 * s * (q.c * q.d - q.b * q.a)
   let m22 := 1 - 2 * s * (q.b ^ 2 + q.c ^ 2)
   match v with
   | none =>
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```lean
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
```diff
@@ -1,19 +1,3 @@
-import Mathlib
--- imports-end
-
-/-!
-Building the transformation matrix that a unit-scaled quaternion induces on
-space.
-
-A quaternion is its four rational components `(a, b, c, d)`. From them a scale
-`s = 1 / (a² + b² + c² + d²)` is formed, and the nine entries of a 3×3 matrix
-are given by quadratic expressions in the components, each weighted by `2·s`:
-
-```
-[ 1 - 2s(c²+d²)     2s(bc - da)     2s(bd + ca)   ]
-[   2s(bc + da)   1 - 2s(b²+d²)     2s(cd - ba)   ]
-[   2s(bd - ca)     2s(cd + ba)   1 - 2s(b²+c²)   ]
-```
 
 When no translation point is supplied the result is exactly this 3×3 matrix.
 When a point `(x, y, z)` is supplied the result is a 4×4 matrix: the same 3×3
@@ -117,7 +101,7 @@
   match v with
   | none =>
       return {
-        rows := 3, cols := 3,
+        rows := 4, cols := 3,
         get := fun i j =>
           (([[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]].getD i []).getD j 0) }
   | some (x, y, z) =>
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```lean
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
```diff
@@ -1,19 +1,3 @@
-import Mathlib
--- imports-end
-
-/-!
-Building the transformation matrix that a unit-scaled quaternion induces on
-space.
-
-A quaternion is its four rational components `(a, b, c, d)`. From them a scale
-`s = 1 / (a² + b² + c² + d²)` is formed, and the nine entries of a 3×3 matrix
-are given by quadratic expressions in the components, each weighted by `2·s`:
-
-```
-[ 1 - 2s(c²+d²)     2s(bc - da)     2s(bd + ca)   ]
-[   2s(bc + da)   1 - 2s(b²+d²)     2s(cd - ba)   ]
-[   2s(bd - ca)     2s(cd + ba)   1 - 2s(b²+c²)   ]
-```
 
 When no translation point is supplied the result is exactly this 3×3 matrix.
 When a point `(x, y, z)` is supplied the result is a 4×4 matrix: the same 3×3
@@ -106,7 +90,7 @@
     (q : Quat) (v : Option (ℚ × ℚ × ℚ)) : Mat := Id.run do
   let s := scale q
   let m00 := 1 - 2 * s * (q.c ^ 2 + q.d ^ 2)
-  let m01 := 2 * s * (q.b * q.c - q.d * q.a)
+  let m01 := 2 * s * (q.b * q.c + q.d * q.a)
   let m02 := 2 * s * (q.b * q.d + q.c * q.a)
   let m10 := 2 * s * (q.b * q.c + q.d * q.a)
   let m11 := 1 - 2 * s * (q.b ^ 2 + q.d ^ 2)
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```lean
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
```diff
@@ -1,19 +1,3 @@
-import Mathlib
--- imports-end
-
-/-!
-Building the transformation matrix that a unit-scaled quaternion induces on
-space.
-
-A quaternion is its four rational components `(a, b, c, d)`. From them a scale
-`s = 1 / (a² + b² + c² + d²)` is formed, and the nine entries of a 3×3 matrix
-are given by quadratic expressions in the components, each weighted by `2·s`:
-
-```
-[ 1 - 2s(c²+d²)     2s(bc - da)     2s(bd + ca)   ]
-[   2s(bc + da)   1 - 2s(b²+d²)     2s(cd - ba)   ]
-[   2s(bd - ca)     2s(cd + ba)   1 - 2s(b²+c²)   ]
-```
 
 When no translation point is supplied the result is exactly this 3×3 matrix.
 When a point `(x, y, z)` is supplied the result is a 4×4 matrix: the same 3×3
@@ -121,7 +105,7 @@
         get := fun i j =>
           (([[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]].getD i []).getD j 0) }
   | some (x, y, z) =>
-      let m03 := x - x * m00 - y * m01 - z * m02
+      let m03 := x - x * m00 - y * m01
       let m13 := y - x * m10 - y * m11 - z * m12
       let m23 := z - x * m20 - y * m21 - z * m22
       return {
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```lean
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
```diff
@@ -1,19 +1,3 @@
-import Mathlib
--- imports-end
-
-/-!
-Building the transformation matrix that a unit-scaled quaternion induces on
-space.
-
-A quaternion is its four rational components `(a, b, c, d)`. From them a scale
-`s = 1 / (a² + b² + c² + d²)` is formed, and the nine entries of a 3×3 matrix
-are given by quadratic expressions in the components, each weighted by `2·s`:
-
-```
-[ 1 - 2s(c²+d²)     2s(bc - da)     2s(bd + ca)   ]
-[   2s(bc + da)   1 - 2s(b²+d²)     2s(cd - ba)   ]
-[   2s(bd - ca)     2s(cd + ba)   1 - 2s(b²+c²)   ]
-```
 
 When no translation point is supplied the result is exactly this 3×3 matrix.
 When a point `(x, y, z)` is supplied the result is a 4×4 matrix: the same 3×3
@@ -119,7 +103,11 @@
       return {
         rows := 3, cols := 3,
         get := fun i j =>
-          (([[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]].getD i []).getD j 0) }
+          match i, j with
+          | 0, 0 => m00 | 0, 1 => m01 | 0, 2 => m02
+          | 1, 0 => m10 | 1, 1 => m11 | 1, 2 => m12
+          | 2, 0 => m20 | 2, 1 => m21 | 2, 2 => m22
+          | _, _ => 0 }
   | some (x, y, z) =>
       let m03 := x - x * m00 - y * m01 - z * m02
       let m13 := y - x * m10 - y * m11 - z * m12
@@ -127,29 +115,15 @@
       return {
         rows := 4, cols := 4,
         get := fun i j =>
-          (([[m00, m01, m02, m03], [m10, m11, m12, m13],
-             [m20, m21, m22, m23], [0, 0, 0, 1]].getD i []).getD j 0) }
+          match i, j with
+          | 0, 0 => m00 | 0, 1 => m01 | 0, 2 => m02 | 0, 3 => m03
+          | 1, 0 => m10 | 1, 1 => m11 | 1, 2 => m12 | 1, 3 => m13
+          | 2, 0 => m20 | 2, 1 => m21 | 2, 2 => m22 | 2, 3 => m23
+          | 3, 0 => 0   | 3, 1 => 0   | 3, 2 => 0   | 3, 3 => 1
+          | _, _ => 0 }
 -- impl-end
 
 -- proof-start
-/-- Reading a row-major nested-list matrix at an out-of-range index (row or
-column at/beyond the bound `k`) yields the default `0`, provided the outer
-list and every row have length at most `k`. -/
-private theorem getD_getD_eq_zero (L : List (List ℚ)) (k : Nat)
-    (hL : L.length ≤ k) (hr : ∀ r ∈ L, r.length ≤ k) :
-    ∀ i j, k ≤ i ∨ k ≤ j → (L.getD i []).getD j 0 = 0 := by
-  intro i j h
-  rcases h with hi | hj
-  · rw [List.getD_eq_default _ _ (le_trans hL hi)]
-    simp
-  · by_cases hiL : i < L.length
-    · have hm : L.getD i [] ∈ L := by
-        rw [List.getD_eq_getElem _ _ hiL]
-        exact List.getElem_mem hiL
-      exact List.getD_eq_default _ _ (le_trans (hr _ hm) hj)
-    · rw [List.getD_eq_default _ _ (Nat.le_of_not_lt hiL)]
-      simp
-
 theorem correct_toRotationMatrix :
     ∀ (q : Quat) (v : Option (ℚ × ℚ × ℚ)),
       q.a ^ 2 + q.b ^ 2 + q.c ^ 2 + q.d ^ 2 ≠ 0 →
@@ -160,13 +134,20 @@
   | none =>
       refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, ?_⟩
       intro i j h
-      exact getD_getD_eq_zero _ 3 (by simp)
-        (by intro r hr; fin_cases hr <;> simp) i j h
+      match i, j with
+      | 0, 0 | 0, 1 | 0, 2 | 1, 0 | 1, 1 | 1, 2 | 2, 0 | 2, 1 | 2, 2 =>
+        omega
+      | i+3, j => rfl
+      | 0, j+3 | 1, j+3 | 2, j+3 => rfl
   | some p =>
       obtain ⟨x, y, z⟩ := p
       refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl,
         rfl, rfl, rfl, rfl, ?_⟩
       intro i j h
-      exact getD_getD_eq_zero _ 4 (by simp)
-        (by intro r hr; fin_cases hr <;> simp) i j h
+      match i, j with
+      | 0, 0 | 0, 1 | 0, 2 | 0, 3 | 1, 0 | 1, 1 | 1, 2 | 1, 3
+      | 2, 0 | 2, 1 | 2, 2 | 2, 3 | 3, 0 | 3, 1 | 3, 2 | 3, 3 =>
+        omega
+      | i+4, j => rfl
+      | 0, j+4 | 1, j+4 | 2, j+4 | 3, j+4 => rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
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
```diff
@@ -1,19 +1,3 @@
-import Mathlib
--- imports-end
-
-/-!
-Building the transformation matrix that a unit-scaled quaternion induces on
-space.
-
-A quaternion is its four rational components `(a, b, c, d)`. From them a scale
-`s = 1 / (a² + b² + c² + d²)` is formed, and the nine entries of a 3×3 matrix
-are given by quadratic expressions in the components, each weighted by `2·s`:
-
-```
-[ 1 - 2s(c²+d²)     2s(bc - da)     2s(bd + ca)   ]
-[   2s(bc + da)   1 - 2s(b²+d²)     2s(cd - ba)   ]
-[   2s(bd - ca)     2s(cd + ba)   1 - 2s(b²+c²)   ]
-```
 
 When no translation point is supplied the result is exactly this 3×3 matrix.
 When a point `(x, y, z)` is supplied the result is a 4×4 matrix: the same 3×3
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Same-spec check True for all 7 attacks (swebench_unified.markers.same_spec, lean). Positive control (gold Solution.lean) verifies: lean_verify.sh exit 0; #print axioms correct_toRotationMatrix => [propext, Classical.choice, Quot.sound] (clean, no sorryAx).

The spec problem_spec_toRotationMatrix is EXTENSIONALLY COMPLETE: it pins every in-range entry (9 slots for the none/3x3 branch, 16 slots for the some/4x4 branch), pins both dimensions (rows/cols), AND pins ALL out-of-range reads to 0 (∀ i j, dim ≤ i ∨ dim ≤ j → get i j = 0). This is the P1-repaired tight spec that removes the accessor's free degrees of freedom. No axiom/opaque is declared or consumed anywhere (grep for ^axiom|^opaque => NONE); refinement.md legs are all R/I with no A-consumed/A-reference legs, so there is nothing in the A-leg class to audit; mapping's scale q = (a²+b²+c²+d²)⁻¹ ↔ norm()**-2 is an R op modeled directly (exact for nonzero norm).

6 DISTINCT wrong impls (impl region only edited, axioms/pure/pre/post byte-identical), each keeping the official proof, ALL FAIL to verify (real spec-violation errors, not syntax):
- atk_1 (prepatch bug, m12 wrong sign '+'): lean_verify.sh exit 1, 'Application type mismatch' at the e12 rfl. PREPATCH REPRODUCED. cmd: `bash scripts/lean_verify.sh atk_1.lean`.
- atk_2 (ungrounded/out-of-range garbage: getD default 7 instead of 0): exit 1, fails the '= 0' out-of-range clause.
- atk_3 (m12/m21 swap — control-flow-effect): exit 1, type mismatch at e12 rfl.
- atk_4 (boundary: wrong dims rows:=4 in none branch): exit 1, type mismatch at rows rfl.
- atk_5 (m01 wrong sign — partial-domain divergence): exit 1, type mismatch at e01 rfl.
- atk_6 (4x4 m03 drops the -z*m02 term): exit 1, type mismatch at the m03 (get 0 3) rfl.

atk_7 (ungrounded-oracle ECHO): a genuinely different construction (per-index `match i,j` accessor instead of nested-list getD) producing IDENTICAL observable values to gold; verifies lean_verify.sh exit 0 with clean axioms [propext, Classical.choice, Quot.sound]. Per protocol I materialized its faithful patch (= the gold sign fix, since its impl values equal gold) and RAN it through the official harness: run_resolve('sympy__sympy-15349', ...) => RESOLVED=True (note='resolved'). So this closing clean-axiom candidate's faithful patch DOES resolve — verify⇒correct holds; NOT a break (this is exactly the resolving-echo case that is not a weakness per the 2026-08-06 G-PANEL-1 policy).

Concurrency: attacks 1-4 and 5-7 run as background batches (≤4 at a time) per instructions.

No same-spec wrong impl closes with clean axioms, hence no candidate exists whose faithful patch could fail to resolve. verify⇏correct could not be exhibited. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found between the modeled function and the real gold-patched callee. Evidence: (1) same_spec(Solution.lean, Solution_prepatch.lean, lean)=True — frozen spec region byte-identical across variants. (2) lean_verify exit 0; #print axioms correct_toRotationMatrix = [propext, Classical.choice, Quot.sound] — no sorryAx, proof is genuine, so implementation_toRotationMatrix provably satisfies problem_spec. (3) Spec formulas match the patched sympy to_rotation_matrix entry-by-entry: gold m12=2s(cd-ba) (the sign fix), m21=2s(cd+ba); both distinct slots correctly differentiated, plus 4x4 augmentation m{i}3=coord_i - x*mi0 - y*mi1 - z*mi2, row3=(0,0,0,1). Differential test: 375,000 in-range entry comparisons over randomized rational quaternions (nonzero norm) and points against the REAL patched callee — 0 disagreements. Examined the two candidate 'too-strong' clauses: (a) the out-of-range 'get i j = 0' pin is a modeling convention of the abstract Mat type (Python raises IndexError there, not an F2P observable); it is satisfied definitionally by the faithful getD...0 impl, so it constrains only the accessor's free DoF and cannot reject the faithful output. (b) precondition a^2+b^2+c^2+d^2 != 0 is exactly the real callee's domain (norm()**-2 undefined otherwise). ℚ modeling is an exact bijection for the exact-rational F2P observable. No input drives the modeled function away from the real callee within its domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the solver-visible spec view (spec_view projection of Solution.lean; impl+proof regions elided). Mechanical G-LEAK screen (leakage.screen) passes with zero hard failures; same_spec(post, prepatch)=True confirms the audited spec region is the one screened.

Public problem_statement already discloses: the class/method Quaternion.to_rotation_matrix(), that its output is incorrect, and that 'one of the sin(x) functions should be negative' (i.e. a sign error). Judging leakage against problem_statement ONLY (not the internal refinement.md/mapping.md, which are audit docs and NOT part of the consumer view; those DO narrate 'PRE-PATCH (buggy: wrong sign)' etc. but are never shown to the solver).

Leak-vector review of the spec view:
1. Diff markers: none.
2. Gold-patch line reproduction: gold edit is `m12 = 2*s*(q.c*q.d - q.b*q.a)`. The spec pins e12 := 2*s*(q.c*q.d - q.b*q.a) — this is the CORRECT behavioral value, and a faithful spec must pin all nine entries to their correct values. Not a verbatim Python-line reproduction; pinning correct behavior is the task, not edit-localization. No comment/docstring singles out m12/e12 as the changed slot.
3. Patched file path 'sympy/algebras/quaternion.py' and dotted module: absent.
4. Patched repo symbol: `to_rotation_matrix` appears verbatim in problem_statement, so already public (screen correctly skips it).
5. Narration: docstrings describe the correct matrix formula and the abstract out-of-range 'modeling convention' (removing a 'free degree of freedom'); no bug/fix/wrong/patch/previously narration, no pointer to which entry was historically wrong.

The spec view reveals no edit-localization beyond what problem_statement already makes public. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
