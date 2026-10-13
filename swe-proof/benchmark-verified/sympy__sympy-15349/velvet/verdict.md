# P2 adversarial audit — sympy__sympy-15349

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verifies, so there is no verifying-wrong impl whose faithful refined patch could fail to resolve — no verify=>correct gap exists to exploit.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The routine builds the result purely from the four
@@ -82,22 +82,20 @@
   ensures out = rotMatrix a b c d v
   do
     -- impl-start
-    -- Common scaling factor: reciprocal of the sum of the squared components
-    -- (the inverse square of the quaternion's magnitude).
+    -- Pre-image skeleton: the row-1/column-2 entry pairs the cross term `c*d`
+    -- with `b*a` under the SAME sign as the symmetric row-2/column-1 entry
+    -- (`c*d + b*a`). The frozen spec requires the orientation-preserving
+    -- convention (`c*d - b*a`), so prove_correct MUST fail.
     let s := sFactor a b c d
-    -- The nine entries of the 3×3 block, each a closed-form rational function
-    -- of the components.
     let m00 := 1 - 2 * s * (c ^ 2 + d ^ 2)
     let m01 := 2 * s * (b * c - d * a)
     let m02 := 2 * s * (b * d + c * a)
     let m10 := 2 * s * (b * c + d * a)
     let m11 := 1 - 2 * s * (b ^ 2 + d ^ 2)
-    let m12 := 2 * s * (c * d - b * a)
+    let m12 := 2 * s * (c * d + b * a)
     let m20 := 2 * s * (b * d - c * a)
     let m21 := 2 * s * (c * d + b * a)
     let m22 := 1 - 2 * s * (b ^ 2 + c ^ 2)
-    -- Without a point: the 3×3 block. With a point: the 4×4 homogeneous matrix,
-    -- the fourth column carrying the point under the linear action of the block.
     let out := match v with
       | none => [[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]]
       | some (x, y, z) =>
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The routine builds the result purely from the four
@@ -87,7 +87,7 @@
     let s := sFactor a b c d
     -- The nine entries of the 3×3 block, each a closed-form rational function
     -- of the components.
-    let m00 := 1 - 2 * s * (c ^ 2 + d ^ 2)
+    let m00 := 1 - 2 * s * (b ^ 2 + d ^ 2)
     let m01 := 2 * s * (b * c - d * a)
     let m02 := 2 * s * (b * d + c * a)
     let m10 := 2 * s * (b * c + d * a)
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The routine builds the result purely from the four
@@ -105,7 +105,7 @@
         let m13 := y - x * m10 - y * m11 - z * m12
         let m23 := z - x * m20 - y * m21 - z * m22
         [[m00, m01, m02, m03], [m10, m11, m12, m13],
-         [m20, m21, m22, m23], [0, 0, 0, 1]]
+         [m20, m21, m22, m23], [0, 0, 0, 0]]
     return out
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The routine builds the result purely from the four
@@ -99,7 +99,7 @@
     -- Without a point: the 3×3 block. With a point: the 4×4 homogeneous matrix,
     -- the fourth column carrying the point under the linear action of the block.
     let out := match v with
-      | none => [[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]]
+      | none => [[m10, m11, m12], [m00, m01, m02], [m20, m21, m22]]
       | some (x, y, z) =>
         let m03 := x - x * m00 - y * m01 - z * m02
         let m13 := y - x * m10 - y * m11 - z * m12
```

Attack 5 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The routine builds the result purely from the four
@@ -94,7 +94,7 @@
     let m11 := 1 - 2 * s * (b ^ 2 + d ^ 2)
     let m12 := 2 * s * (c * d - b * a)
     let m20 := 2 * s * (b * d - c * a)
-    let m21 := 2 * s * (c * d + b * a)
+    let m21 := 2 * s * (c * d - b * a)
     let m22 := 1 - 2 * s * (b ^ 2 + c ^ 2)
     -- Without a point: the 3×3 block. With a point: the 4×4 homogeneous matrix,
     -- the fourth column carrying the point under the linear action of the block.
```

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The routine builds the result purely from the four
@@ -89,7 +89,7 @@
     -- of the components.
     let m00 := 1 - 2 * s * (c ^ 2 + d ^ 2)
     let m01 := 2 * s * (b * c - d * a)
-    let m02 := 2 * s * (b * d + c * a)
+    let m02 := 2 * s * (b * d - c * a)
     let m10 := 2 * s * (b * c + d * a)
     let m11 := 1 - 2 * s * (b ^ 2 + d ^ 2)
     let m12 := 2 * s * (c * d - b * a)
```

Attack 7 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The routine builds the result purely from the four
@@ -98,14 +98,7 @@
     let m22 := 1 - 2 * s * (b ^ 2 + c ^ 2)
     -- Without a point: the 3×3 block. With a point: the 4×4 homogeneous matrix,
     -- the fourth column carrying the point under the linear action of the block.
-    let out := match v with
-      | none => [[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]]
-      | some (x, y, z) =>
-        let m03 := x - x * m00 - y * m01 - z * m02
-        let m13 := y - x * m10 - y * m11 - z * m12
-        let m23 := z - x * m20 - y * m21 - z * m22
-        [[m00, m01, m02, m03], [m10, m11, m12, m13],
-         [m20, m21, m22, m23], [0, 0, 0, 1]]
+    let out := rotMatrix a b c d v
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

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
    -- Common scaling factor: reciprocal of the sum of the squared components
    -- (the inverse square of the quaternion's magnitude).
    let s := sFactor a b c d
    -- The nine entries of the 3×3 block, each a closed-form rational function
    -- of the components.
    let m00 := 1 - 2 * s * (c ^ 2 + d ^ 2)
    let m01 := 2 * s * (b * c - d * a)
    let m02 := 2 * s * (b * d + c * a)
    let m10 := 2 * s * (b * c + d * a)
    let m11 := 1 - 2 * s * (b ^ 2 + d ^ 2)
    let m12 := 2 * s * (c * d - b * a)
    let m20 := 2 * s * (b * d - c * a)
    let m21 := 2 * s * (c * d + b * a)
    let m22 := 1 - 2 * s * (b ^ 2 + c ^ 2)
    -- Without a point: the 3×3 block. With a point: the 4×4 homogeneous matrix,
    -- the fourth column carrying the point under the linear action of the block.
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
```

Prepatch bug re-encoded as an attack: `True`.

Spec: toOrientationMatrix pins out = rotMatrix a b c d v, a TOTAL deterministic functional equality over the entire closed-form orientation matrix (both 3x3 none-branch and 4x4 some-branch), scaled by sFactor = (a^2+b^2+c^2+d^2)^-1. This is the tightest possible spec shape; any deviation is caught exactly at the ensures goal.

Protocol executed All files built by copying the frozen Solution.lean and editing ONLY the impl region (axioms/pure/pre/post byte-identical). same_spec (velvet backend) = True for all 7 attack files + pos_control (verified via swebench_unified.markers.same_spec). First-cut atk_2/6/7 accidentally edited the identical text in the pure rotMatrix def (same_spec=False) and were rebuilt to touch impl-region-only before counting.

Verification (bash scripts/lean_verify.sh <f>), run concurrently in two <=4 batches:
- pos_control.lean: exit 0 (gold impl verifies) [positive control PASS].
- atk_1 (prepatch bug: m12 = 2*s*(c*d + b*a), copied from Solution_prepatch.lean): exit 1, unsolved goal 'ensures_1: out = rotMatrix a b c d v' at line 110 [PREPATCH REPRODUCED].
- atk_2 (boundary: m00 = 1 - 2*s*(b^2+d^2) instead of c^2+d^2): exit 1, same ensures goal unsolved.
- atk_3 (partial-domain / some-branch: bottom row [0,0,0,0] instead of [0,0,0,1]): exit 1, same ensures goal unsolved.
- atk_4 (control-flow-effect: rows 0 and 1 swapped in the none branch): exit 1, same ensures goal unsolved.
- atk_6 (m21 sign flip: c*d - b*a): exit 1, same ensures goal unsolved.
- atk_7 (m02 sign flip: b*d - c*a): exit 1, same ensures goal unsolved.
- atk_5 (ungrounded-oracle echo: out := rotMatrix a b c d v): exit 1 with 'No goals to be solved' at line 107 (loom_solve already closes the goal, so the trailing simp_all errors) - a proof-SCRIPT artifact, not a spec weakness; this impl is behaviorally identical to gold. It does not verify, so no resolve is owed for it either.

CRITICAL FINDING: NO same-spec wrong impl verifies. Protocol step 2 (materialize faithful refined patch + run_resolve for EVERY verifying wrong impl) therefore has ZERO triggers -> patches = {}. There is no verify-but-does-not-resolve counterexample to produce; the spec does not admit verify=>incorrect.

Refinement audit (refinement.md / mapping.md / meta.json): meta.json axioms=[], deep_model_references=[], conf_skip=false. Every leg is R or I (A1,A2,A5,A6 = R type-refinement Rational<->Rat / Matrix<->List(List Rat) / Option; A4,A4' = I verbatim arithmetic incl. the discriminating m12 = c*d - b*a matching patch.diff line 9 exactly; A3 = R+I). NO A-consumed / A-reference legs and NO kind-3 (inexpressible-changed-op) legs. The single delegated-to-unchanged-callee op (A3: s = q.norm()**-2) is honestly modeled CONCRETELY as the exact rational identity (a^2+b^2+c^2+d^2)^-1 (the sqrt cancels under the square: 1/(sqrt(Sigma))^2 = 1/Sigma), guarded by precondition Sigma != 0, NOT consumed as an axiom or A-reference; G-CONF (conformance_check.py, seed 15349, 1e5 inputs) validates it against the real patched to_rotation_matrix. The claimed 'no axioms' is truthful and the model<->patch correspondence holds; the m12 discriminator in the pinned rotMatrix is byte-consistent with the gold hunk.

Verdict SOUND: >=6 distinct genuine wrong impls (prepatch, boundary, partial-domain, control-flow-effect, two sign errors) + echo attack all fail to verify against the frozen spec; positive control verifies; no verifying wrong impl exists to falsify verify=>correct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verifies, so there is no verifying-wrong impl whose faithful refined patch could fail to resolve — no verify=>correct gap exists to exploit.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_5.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

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
    -- Common scaling factor: reciprocal of the sum of the squared components
    -- (the inverse square of the quaternion's magnitude).
    let s := sFactor a b c d
    -- The nine entries of the 3×3 block, each a closed-form rational function
    -- of the components.
    let m00 := 1 - 2 * s * (c ^ 2 + d ^ 2)
    let m01 := 2 * s * (b * c - d * a)
    let m02 := 2 * s * (b * d + c * a)
    let m10 := 2 * s * (b * c + d * a)
    let m11 := 1 - 2 * s * (b ^ 2 + d ^ 2)
    let m12 := 2 * s * (c * d - b * a)
    let m20 := 2 * s * (b * d - c * a)
    let m21 := 2 * s * (c * d + b * a)
    let m22 := 1 - 2 * s * (b ^ 2 + c ^ 2)
    -- Without a point: the 3×3 block. With a point: the 4×4 homogeneous matrix,
    -- the fourth column carrying the point under the linear action of the block.
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
```

Prepatch bug re-encoded as an attack: `True`.

Spec: toOrientationMatrix pins out = rotMatrix a b c d v, a TOTAL deterministic functional equality over the entire closed-form orientation matrix (both 3x3 none-branch and 4x4 some-branch), scaled by sFactor = (a^2+b^2+c^2+d^2)^-1. This is the tightest possible spec shape; any deviation is caught exactly at the ensures goal.

Protocol executed All files built by copying the frozen Solution.lean and editing ONLY the impl region (axioms/pure/pre/post byte-identical). same_spec (velvet backend) = True for all 7 attack files + pos_control (verified via swebench_unified.markers.same_spec). First-cut atk_2/6/7 accidentally edited the identical text in the pure rotMatrix def (same_spec=False) and were rebuilt to touch impl-region-only before counting.

Verification (bash scripts/lean_verify.sh <f>), run concurrently in two <=4 batches:
- pos_control.lean: exit 0 (gold impl verifies) [positive control PASS].
- atk_1 (prepatch bug: m12 = 2*s*(c*d + b*a), copied from Solution_prepatch.lean): exit 1, unsolved goal 'ensures_1: out = rotMatrix a b c d v' at line 110 [PREPATCH REPRODUCED].
- atk_2 (boundary: m00 = 1 - 2*s*(b^2+d^2) instead of c^2+d^2): exit 1, same ensures goal unsolved.
- atk_3 (partial-domain / some-branch: bottom row [0,0,0,0] instead of [0,0,0,1]): exit 1, same ensures goal unsolved.
- atk_4 (control-flow-effect: rows 0 and 1 swapped in the none branch): exit 1, same ensures goal unsolved.
- atk_6 (m21 sign flip: c*d - b*a): exit 1, same ensures goal unsolved.
- atk_7 (m02 sign flip: b*d - c*a): exit 1, same ensures goal unsolved.
- atk_5 (ungrounded-oracle echo: out := rotMatrix a b c d v): exit 1 with 'No goals to be solved' at line 107 (loom_solve already closes the goal, so the trailing simp_all errors) - a proof-SCRIPT artifact, not a spec weakness; this impl is behaviorally identical to gold. It does not verify, so no resolve is owed for it either.

CRITICAL FINDING: NO same-spec wrong impl verifies. Protocol step 2 (materialize faithful refined patch + run_resolve for EVERY verifying wrong impl) therefore has ZERO triggers -> patches = {}. There is no verify-but-does-not-resolve counterexample to produce; the spec does not admit verify=>incorrect.

Refinement audit (refinement.md / mapping.md / meta.json): meta.json axioms=[], deep_model_references=[], conf_skip=false. Every leg is R or I (A1,A2,A5,A6 = R type-refinement Rational<->Rat / Matrix<->List(List Rat) / Option; A4,A4' = I verbatim arithmetic incl. the discriminating m12 = c*d - b*a matching patch.diff line 9 exactly; A3 = R+I). NO A-consumed / A-reference legs and NO kind-3 (inexpressible-changed-op) legs. The single delegated-to-unchanged-callee op (A3: s = q.norm()**-2) is honestly modeled CONCRETELY as the exact rational identity (a^2+b^2+c^2+d^2)^-1 (the sqrt cancels under the square: 1/(sqrt(Sigma))^2 = 1/Sigma), guarded by precondition Sigma != 0, NOT consumed as an axiom or A-reference; G-CONF (conformance_check.py, seed 15349, 1e5 inputs) validates it against the real patched to_rotation_matrix. The claimed 'no axioms' is truthful and the model<->patch correspondence holds; the m12 discriminator in the pinned rotMatrix is byte-consistent with the gold hunk.

Verdict SOUND: >=6 distinct genuine wrong impls (prepatch, boundary, partial-domain, control-flow-effect, two sign errors) + echo attack all fail to verify against the frozen spec; positive control verifies; no verifying wrong impl exists to falsify verify=>correct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness of toOrientationMatrix's spec (ensures out = rotMatrix a b c d v under precondition a^2+b^2+c^2+d^2 != 0) vs the real Quaternion.to_rotation_matrix at base_commit 768da1c (patched, m12 = 2*s*(q.c*q.d - q.b*q.a)).

Checks performed:

(1) Spec region byte-identical: swebench_unified.markers.same_spec(Solution, Solution_prepatch, VelvetBackend().language) = True; region_hashes spec_view = 427b4eae69834b8039dda390925ad6de974ccdf817a02513e32409db70603995, matching meta.json G-HYGIENE. Only the impl region differs between Solution and prepatch.

(2) scripts/lean_verify.sh Solution.lean -> EXIT=0.
 All nine 3x3 entries + the 4x4 homogeneous extension (m03/m13/m23 displacement, bottom row [0,0,0,1]) transliterate component-for-component from patched quaternion.py:524-551, including the discriminating patched entry m12 = 2*s*(c*d - b*a). Base repo has m12 = 2*s*(c*d + b*a), so Solution_prepatch legitimately diverges (G-DIFF).

(4) Sole delegated op s=q.norm()**-2 modeled as sFactor=(a^2+b^2+c^2+d^2)^-1: norm()=sqrt(trigsimp(a^2+b^2+c^2+d^2)) (quaternion.py:298), sqrt cancels under **-2, giving the exact rational 1/Sigma. Precondition Sigma!=0 is the reciprocal well-posedness condition (repo divides by zero on a zero quaternion too).

(5) Independent fuzz: 3000 random rational quaternions x {none, some (x,y,z)} evaluated with the exact Lean-transliterated model against the real patched to_rotation_matrix via SymPy exact equality -> 0 disagreements, entry-for-entry, for both the 3x3 and 4x4 forms. Consistent with recorded G-CONF (100009 inputs, seed=15349, 0 disagreements).

(6) Falsy-v boundary: Python 'if not v' selects the 3x3 branch only when v is falsy; a rational triple (0,0,0) is truthy -> 4x4 branch, exactly matching Lean 'some (0,0,0)'. No boundary drift.

The Rat carrier is faithful because the demonstrated F2P behaviour is exact closed-form rational arithmetic. The model is neither too strong nor drifted; no diverging input exists on the modeled domain (nonzero rational quaternion + optional rational translation point).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker (3) leakage / gold-reconstruction review of velvet spec view for sympy__sympy-15349.

GOLD EDIT: single sign flip in sympy/algebras/quaternion.py, Quaternion.to_rotation_matrix: `m12 = 2*s*(q.c*q.d + q.b*q.a)` -> `m12 = 2*s*(q.c*q.d - q.b*q.a)`.

PUBLIC problem_statement already discloses: the exact method name to_rotation_matrix(), a source-line link, the reproducing quaternion Quaternion(cos(x/2), sin(x/2), 0, 0), and the diagnosis "One of the sin(x) functions should be negative" (i.e. a sign error in the rotation matrix). So the bug's location and nature are largely public via the task itself.

SPEC VIEW EXAMINED (generated via markers.spec_view, VelvetBackend). The pure region (sFactor/rotMatrix) is NOT elided; only impl and prove_correct bodies collapse to placeholders. The consumer therefore sees the full closed-form matrix, including the corrected entry m12 := 2 * s * (c * d - b * a). Assessed against the leakage bar:
- No diff markers, no patched file path (sympy/algebras/quaternion.py), no patched module path, no dotted-symbol echo.
- No spec-view identifier or comment naming the changed repo symbol beyond what is public.
- No bug/fix/sign/negative/pre-patch/regression narration in any comment or docstring. Comments are abstract (scaling factor = reciprocal of sum of squares; entries as closed-form rational functions; no-opaque-oracle; Rat modeling rationale).
- Crucially, m12 is presented identically to the other 8 entries with NO singling-out. The spec does not surface WHICH entry was the gold edit; it pins all entries as correct. The public problem_statement points at the changed entry (the m12/sin(x) sign) more directly than the spec view does. So the spec reveals nothing about the edit's LOCALIZATION beyond the public task.

### Mechanical corroboration
- swebench_unified.markers.same_spec(Solution, Solution_prepatch) = True: spec region byte-identical; the two differ only in the elided impl, so the spec view carries no pre/post discriminator delta.
- leakage.screen() passes with zero hard_failures (Lean model `c*d - b*a` does not lexically match the Python gold line `q.c*q.d - q.b*q.a`; no markers/paths/symbols/narration).

Pinning correct behavior in the spec is the intended contract of every velvet bundle and is not leakage; G-PANEL-3 guards against revealing the gold edit (diff/localization/bug narration) beyond the public statement, and none of that is present. Recorded meta G-PANEL-3 also = NO-LEAKAGE, consistent. Bundle is NOT relaxed (relaxed_leakage null), so strict screen applies and passes.

VERDICT: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).