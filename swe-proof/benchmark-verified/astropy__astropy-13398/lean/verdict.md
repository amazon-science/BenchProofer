# P2 adversarial audit — astropy__astropy-13398

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 22 admissible attacks re-run of 22 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 22 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 18 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean`, `atk_19.lean`, `atk_20.lean`, `atk_21.lean`, `atk_22.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_11.lean`, `atk_12.lean`, `atk_17.lean`, `atk_18.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation was exhibited whose correct_* closes with clean axioms while its faithful refined patch fails to resolve. 22 same-spec attacks (same_spec=True for all 22 + the positive control, via swebench_unified.markers.same_spec / get_backend('lean')); 18 REJECTED (lean_verify exit 1) and 4 VERIFIED (exit 0) with clean axioms — and all 4 of those had their faithful patches materialized and RUN through run_resolve, all 4 RESOLVED at F2P 4/4, P2P 68/68, so all 4 are correct echoes, not spec weaknesses. The strongest attempted break was atk_17: both erfa.refco AND the ITRS->AltAz rotation hoisted above the guards that gate them (a pure Lean `let` hoist is definitionally invisible so `rfl` still closes). Its faithful patch evaluates refco and the AltAz matrix on inputs the gold code never touches — notably the library-DEFAULT zero-pressure HADec frame — and it still resolved, because erfa.refco is total and quiet at p=0 (measured: refco(0,0,0,1) = (0.0, -0.0), no warning) so the hoist is behaviourally inert. atk_18 (mvmul+transpose unfolded to the explicit index-order sum on the inverse hadec leg) was measured bit-identical to erfa.rxp(H^T, xyz) at 20000/20000 seeded draws, max abs diff 0.0 — value-preserving, and it resolved.
```

**Attacks re-run (22):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -262,11 +262,6 @@
   let mut crepr : Vec3 := src
   if f.isAltAz = true ∨ f.pressure > 0 then
     crepr := mvmul (altazMat lon lat) src
-    if f.pressure > 0 then
-      let rc := bendCoefs f.pressure f.temperature f.relHumidity f.obswl
-      crepr := toApparent crepr rc.1 rc.2
-      if f.isAltAz = false then
-        crepr := mvmul (poleTiltMat lat) crepr
   else
     crepr := mvmul (hadecMat lon) src
   return crepr
@@ -323,12 +318,7 @@
   let lat := g.2.1
   let mut crepr : Vec3 := v
   if f.isAltAz = true ∨ f.pressure > 0 then
-    if f.pressure > 0 then
-      if f.isAltAz = false then
-        crepr := mvmul ((poleTiltMat lat)ᵀ) crepr
-      let rc := bendCoefs f.pressure f.temperature f.relHumidity f.obswl
-      crepr := toGeometric crepr rc.1 rc.2
-    crepr := mvmul ((altazMat lon lat)ᵀ) crepr
+    crepr := mvmul ((altazMat lon lat)ᵀ) v
   else
     crepr := mvmul ((hadecMat lon)ᵀ) v
   return carryTo crepr f.location f.epoch tgtLoc tgtEpoch
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -257,8 +257,8 @@
   if siteDiffers srcLoc f.location || epochDiffers srcEpoch f.epoch then
     src := carryTo v srcLoc srcEpoch f.location f.epoch
   let g := geodetic f.location
-  let lon := g.1
-  let lat := g.2.1
+  let lon := g.2.1
+  let lat := g.1
   let mut crepr : Vec3 := src
   if f.isAltAz = true ∨ f.pressure > 0 then
     crepr := mvmul (altazMat lon lat) src
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -320,7 +320,7 @@
     Id.run do
   let g := geodetic f.location
   let lon := g.1
-  let lat := g.2.1
+  let lat := g.2.2
   let mut crepr : Vec3 := v
   if f.isAltAz = true ∨ f.pressure > 0 then
     if f.pressure > 0 then
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -331,7 +331,7 @@
     crepr := mvmul ((altazMat lon lat)ᵀ) crepr
   else
     crepr := mvmul ((hadecMat lon)ᵀ) v
-  return carryTo crepr f.location f.epoch tgtLoc tgtEpoch
+  return carryTo crepr tgtLoc tgtEpoch f.location f.epoch
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -255,7 +255,7 @@
     Id.run do
   let mut src := v
   if siteDiffers srcLoc f.location || epochDiffers srcEpoch f.epoch then
-    src := carryTo v srcLoc srcEpoch f.location f.epoch
+    src := carryTo v srcLoc srcEpoch f.location srcEpoch
   let g := geodetic f.location
   let lon := g.1
   let lat := g.2.1
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -262,7 +262,7 @@
   let mut crepr : Vec3 := src
   if f.isAltAz = true ∨ f.pressure > 0 then
     crepr := mvmul (altazMat lon lat) src
-    if f.pressure > 0 then
+    if f.pressure > 0 ∧ f.isAltAz = true then
       let rc := bendCoefs f.pressure f.temperature f.relHumidity f.obswl
       crepr := toApparent crepr rc.1 rc.2
       if f.isAltAz = false then
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -262,7 +262,7 @@
   let mut crepr : Vec3 := src
   if f.isAltAz = true ∨ f.pressure > 0 then
     crepr := mvmul (altazMat lon lat) src
-    if f.pressure > 0 then
+    if f.pressure ≥ 0 then
       let rc := bendCoefs f.pressure f.temperature f.relHumidity f.obswl
       crepr := toApparent crepr rc.1 rc.2
       if f.isAltAz = false then
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -324,10 +324,10 @@
   let mut crepr : Vec3 := v
   if f.isAltAz = true ∨ f.pressure > 0 then
     if f.pressure > 0 then
+      let rc := bendCoefs f.pressure f.temperature f.relHumidity f.obswl
+      crepr := toGeometric crepr rc.1 rc.2
       if f.isAltAz = false then
         crepr := mvmul ((poleTiltMat lat)ᵀ) crepr
-      let rc := bendCoefs f.pressure f.temperature f.relHumidity f.obswl
-      crepr := toGeometric crepr rc.1 rc.2
     crepr := mvmul ((altazMat lon lat)ᵀ) crepr
   else
     crepr := mvmul ((hadecMat lon)ᵀ) v
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -264,7 +264,7 @@
     crepr := mvmul (altazMat lon lat) src
     if f.pressure > 0 then
       let rc := bendCoefs f.pressure f.temperature f.relHumidity f.obswl
-      crepr := toApparent crepr rc.1 rc.2
+      crepr := toGeometric crepr rc.1 rc.2
       if f.isAltAz = false then
         crepr := mvmul (poleTiltMat lat) crepr
   else
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -254,8 +254,7 @@
     (v : Vec3) (srcLoc : Location) (srcEpoch : Float) (f : ObsFrame) : Vec3 :=
     Id.run do
   let mut src := v
-  if siteDiffers srcLoc f.location || epochDiffers srcEpoch f.epoch then
-    src := carryTo v srcLoc srcEpoch f.location f.epoch
+  src := carryTo v srcLoc srcEpoch f.location f.epoch
   let g := geodetic f.location
   let lon := g.1
   let lat := g.2.1
```

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -255,7 +255,7 @@
     Id.run do
   let mut src := v
   if siteDiffers srcLoc f.location || epochDiffers srcEpoch f.epoch then
-    src := carryTo v srcLoc srcEpoch f.location f.epoch
+    src := carryTo src srcLoc srcEpoch f.location f.epoch
   let g := geodetic f.location
   let lon := g.1
   let lat := g.2.1
@@ -269,7 +269,7 @@
         crepr := mvmul (poleTiltMat lat) crepr
   else
     crepr := mvmul (hadecMat lon) src
-  return crepr
+  return fun i => crepr i
 -- impl-end
 
 -- proof-start
```

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -325,7 +325,7 @@
   if f.isAltAz = true ∨ f.pressure > 0 then
     if f.pressure > 0 then
       if f.isAltAz = false then
-        crepr := mvmul ((poleTiltMat lat)ᵀ) crepr
+        crepr := mvmul ((poleTiltMat lat)ᵀᵀᵀ) crepr
       let rc := bendCoefs f.pressure f.temperature f.relHumidity f.obswl
       crepr := toGeometric crepr rc.1 rc.2
     crepr := mvmul ((altazMat lon lat)ᵀ) crepr
```

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -263,7 +263,7 @@
   if f.isAltAz = true ∨ f.pressure > 0 then
     crepr := mvmul (altazMat lon lat) src
     if f.pressure > 0 then
-      let rc := bendCoefs f.pressure f.temperature f.relHumidity f.obswl
+      let rc := bendCoefs f.pressure f.temperature f.obswl f.relHumidity
       crepr := toApparent crepr rc.1 rc.2
       if f.isAltAz = false then
         crepr := mvmul (poleTiltMat lat) crepr
```

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -327,7 +327,7 @@
       if f.isAltAz = false then
         crepr := mvmul ((poleTiltMat lat)ᵀ) crepr
       let rc := bendCoefs f.pressure f.temperature f.relHumidity f.obswl
-      crepr := toGeometric crepr rc.1 rc.2
+      crepr := toGeometric crepr rc.2 rc.1
     crepr := mvmul ((altazMat lon lat)ᵀ) crepr
   else
     crepr := mvmul ((hadecMat lon)ᵀ) v
```

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -260,7 +260,7 @@
   let lon := g.1
   let lat := g.2.1
   let mut crepr : Vec3 := src
-  if f.isAltAz = true ∨ f.pressure > 0 then
+  if f.isAltAz = true ∨ f.pressure ≥ 0 then
     crepr := mvmul (altazMat lon lat) src
     if f.pressure > 0 then
       let rc := bendCoefs f.pressure f.temperature f.relHumidity f.obswl
```

Attack 16 — `atk_16.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -331,7 +331,9 @@
     crepr := mvmul ((altazMat lon lat)ᵀ) crepr
   else
     crepr := mvmul ((hadecMat lon)ᵀ) v
-  return carryTo crepr f.location f.epoch tgtLoc tgtEpoch
+  if siteDiffers f.location tgtLoc || epochDiffers f.epoch tgtEpoch then
+    return carryTo crepr f.location f.epoch tgtLoc tgtEpoch
+  return crepr
 -- impl-end
 
 -- proof-start
```

Attack 17 — `atk_17.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,11 +259,12 @@
   let g := geodetic f.location
   let lon := g.1
   let lat := g.2.1
+  let aa := mvmul (altazMat lon lat) src
+  let rc := bendCoefs f.pressure f.temperature f.relHumidity f.obswl
   let mut crepr : Vec3 := src
   if f.isAltAz = true ∨ f.pressure > 0 then
-    crepr := mvmul (altazMat lon lat) src
+    crepr := aa
     if f.pressure > 0 then
-      let rc := bendCoefs f.pressure f.temperature f.relHumidity f.obswl
       crepr := toApparent crepr rc.1 rc.2
       if f.isAltAz = false then
         crepr := mvmul (poleTiltMat lat) crepr
```

Attack 18 — `atk_18.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -330,7 +330,8 @@
       crepr := toGeometric crepr rc.1 rc.2
     crepr := mvmul ((altazMat lon lat)ᵀ) crepr
   else
-    crepr := mvmul ((hadecMat lon)ᵀ) v
+    let H := hadecMat lon
+    crepr := fun i => H 0 i * v 0 + H 1 i * v 1 + H 2 i * v 2
   return carryTo crepr f.location f.epoch tgtLoc tgtEpoch
 -- impl-end
 
```

Attack 19 — `atk_19.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -255,7 +255,7 @@
     Id.run do
   let mut src := v
   if siteDiffers srcLoc f.location || epochDiffers srcEpoch f.epoch then
-    src := carryTo v srcLoc srcEpoch f.location f.epoch
+    src := carryTo v f.location srcEpoch f.location f.epoch
   let g := geodetic f.location
   let lon := g.1
   let lat := g.2.1
```

Attack 20 — `atk_20.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -254,7 +254,7 @@
     (v : Vec3) (srcLoc : Location) (srcEpoch : Float) (f : ObsFrame) : Vec3 :=
     Id.run do
   let mut src := v
-  if siteDiffers srcLoc f.location || epochDiffers srcEpoch f.epoch then
+  if siteDiffers f.location srcLoc || epochDiffers srcEpoch f.epoch then
     src := carryTo v srcLoc srcEpoch f.location f.epoch
   let g := geodetic f.location
   let lon := g.1
```

Attack 21 — `atk_21.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -254,7 +254,7 @@
     (v : Vec3) (srcLoc : Location) (srcEpoch : Float) (f : ObsFrame) : Vec3 :=
     Id.run do
   let mut src := v
-  if siteDiffers srcLoc f.location || epochDiffers srcEpoch f.epoch then
+  if siteDiffers srcLoc f.location && epochDiffers srcEpoch f.epoch then
     src := carryTo v srcLoc srcEpoch f.location f.epoch
   let g := geodetic f.location
   let lon := g.1
```

Attack 22 — `atk_22.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -328,7 +328,7 @@
         crepr := mvmul ((poleTiltMat lat)ᵀ) crepr
       let rc := bendCoefs f.pressure f.temperature f.relHumidity f.obswl
       crepr := toGeometric crepr rc.1 rc.2
-    crepr := mvmul ((altazMat lon lat)ᵀ) crepr
+    crepr := mvmul (altazMat lon lat) crepr
   else
     crepr := mvmul ((hadecMat lon)ᵀ) v
   return carryTo crepr f.location f.epoch tgtLoc tgtEpoch
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity pass, astropy__astropy-13398 (lean). Per role, focus on the A legs (axioms / deep-model references) and the model<->patch correspondence; R/I left to G-CONF. All attacks built by copying the bundle Solution.lean and editing ONLY the two `impl` regions (axioms/pure/post-conditions byte-identical); proof regions left byte-identical so every attack is judged by the GOLD script `split_ifs <;> rfl`.

**COMMANDS.** Verify (each, run 4-way concurrent in background batches): `bash scripts/lean_verify.sh <name>.lean` from the repo root; exit code in <name>.exit, output in <name>.log. Same-spec: `python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; ..."` -> True for all 22 attacks + pos_control. Axioms: ax_11/12/17/18.lean = the attack plus `#print axioms correct_itrs_to_observed` / `correct_observed_to_itrs`, same verify command. Resolve: `python resolve.py <name>` calling swebench_unified.harness.run_resolve('astropy__astropy-13398', <diff>, timeout=3600), 4 launched concurrently; results in <name>.resolve.json / .resolve.log.

**POSITIVE CONTROL:** pos_control.lean (byte-identical to the shipped Solution.lean) -> exit 0.
PREPATCH REPRODUCED: atk_1 (refraction + HADec cross-rotation absent fwd, de-refraction absent inv — exactly the graded delta, i.e. the diff of the impl regions of Solution_prepatch.lean vs Solution.lean) -> exit 1, rejected. The rfl failure is the real one (LHS `mvmul (altazMat ...) (carryTo ...)` vs RHS the poleTilt-of-toApparent composition), so the spec does distinguish the pre-patch behaviour.

REJECTED, exit=1 (18): atk_1 (prepatch bug); atk_2 (A-reference output order: geodetic lon/lat exchanged, fwd); atk_3 (A-reference component pick: geodetic HEIGHT used as latitude, inv); atk_4 (A-reference arg binding: inverse carry direction reversed — the pair-of-pairs claim); atk_5 (A-reference arg binding: fwd carry TARGET epoch collapsed to srcEpoch); atk_6 (partial domain: refraction only when isAltAz, so HADec+atmosphere goes unrefracted); atk_7 (boundary: refraction guard pressure >= 0 for > 0 — fires on the library-default p=0); atk_8 (control-flow-effect: de-refract before undoing the HADec cross-rotation, inv); atk_9 (ungrounded-oracle echo: fwd leg applies toGeometric, the INVERSE closed form); atk_10 (A-leg control flow: fwd carry guard dropped, carry unconditional); atk_13 (A-reference input binding: bendCoefs relHumidity/obswl exchanged); atk_14 (A-reference output binding: bendCoefs coefficients swapped, inv); atk_15 (boundary on the OUTER guard: pressure >= 0 kills the hadec-no-atmosphere branch); atk_16 (partial domain / A-leg control flow: the UNCONDITIONAL inverse carry put behind a siteDiffers/epochDiffers guard); atk_19 (A-reference arg binding: fwd carry source site bound to f.location); atk_20 (A-reference arg ORDER: siteDiffers arguments exchanged); atk_21 (control flow: carry guard || weakened to &&); atk_22 (matrix selection: transpose dropped on the inverse altaz rotation).

VERIFIED, exit=0 (4) — ALL FOUR resolve-tested as mandated: atk_11 (fwd carry reads the mutable local `src` rather than the parameter `v`; result eta-expanded componentwise), atk_12 (triple transpose of the inverse cross-rotation), atk_17 (ECHO CANDIDATE: bendCoefs AND the altaz rotation hoisted above their guards), atk_18 (ECHO CANDIDATE: inverse hadec mvmul+transpose unfolded to the explicit index-order sum). `#print axioms` for BOTH theorems on each of the four -> [propext, Classical.choice, Quot.sound] = CLEAN, no sorry (ax_11/12/17/18.log, each exit 0).

RESOLVE RESULTS (executed, not speculated; faithful patches materialized in a base_commit worktree via mkpatch.sh + edit_<n>.py, each checked with `git apply --check` at base_commit = APPLIES CLEAN before submission):
- atk_11.diff -> completed=True RESOLVED, attempts=1, flaky=False, F2P 4/4, P2P 68/68, 0 failures.
- atk_12.diff -> completed=True RESOLVED, attempts=1, flaky=False, F2P 4/4, P2P 68/68, 0 failures.
- atk_17.diff -> completed=True RESOLVED, attempts=1, flaky=False, F2P 4/4, P2P 68/68, 0 failures.
- atk_18.diff -> completed=True RESOLVED, attempts=1, flaky=False, F2P 4/4, P2P 68/68, 0 failures.
So every impl with a closing clean-axiom proof has a materialized faithful patch that DOES resolve => no verify=/=>correct break. Supporting local measurements: erfa.refco is total and silent at the default zero atmosphere (refco(0,0,0,1) = (0.0,-0.0)), which is why atk_17's out-of-guard hoist is inert; and atk_18's hand-written index-order sum is bit-identical to erfa.rxp(H^T,xyz) at 20000/20000 seeded draws (max abs diff 0.0, probe18.py).

refinement.md AUDIT: 21 leg rows parsed; tag census = 8 R, 5 A-reference, 3 'R / I (branch)', 2 'I (branch)', 1 'R (mvmul) / I (branch)', 1 'R / I', 1 I. Every row carries R / A-reference / I; ZERO kind-3 legs and ZERO A-consumed axioms shipped — consistent with both proofs closing by `split_ifs <;> rfl`, so the result is produced by the modelled branch rather than echoed from an answer key. atk_9's oracle-echo rewrite (fwd leg reaching for the inverse closed form) is rejected, which confirms that independently.

A-REFERENCE CORRESPONDENCE, re-derived against the real callees rather than read off the tables:

(1) geodetic <- EarthLocation.to_geodetic('WGS84') returns Longitude/Latitude, i.e. DEGREES, which is why the model needs poleAngle=90.0 + angToRad; angToRad = 0.017453292519943295 is exactly math.pi/180 at binary64 (checked equal), matching NORTH_POLE=90.0*u.deg fed to rotation_matrix, whose base_commit body does angle.to_value(u.radian). The two rewrites that break this row, atk_2 (lon/lat exchanged) and atk_3 (height read as latitude), are both rejected.

(2) bendCoefs <- erfa.refco with arg order (p, T, rh, wl) and result order (refa, refb): atk_13 (input order) and atk_14 (output order) both rejected.

(3) normSplit/scaleVec <- erfa.pn/erfa.sxp with the SECOND pn's norm discarded and the FIRST restored by sxp — matches add_refraction verbatim in the patch.

(4) cartToSph/sphToCart <- erfa.c2s/erfa.s2c, and remove_refraction indeed lacks the CELMIN floor that add_refraction has, as the pure region and refinement.md both state.

(5) carryTo's 4-argument pair-of-pairs reading confirmed at BOTH call sites in the patch: the guarded pre-step of itrs_to_observed (:108-112) and the UNGUARDED trailing step of observed_to_itrs (:144-145) where itrs_frame supplies the target. Four independent rewrites of exactly that row — atk_4 (direction reversed), atk_5 (target epoch collapsed), atk_16 (unconditional carry put behind a guard), atk_19 (source site collapsed to the frame's) — are ALL rejected, so both the arity and the unconditionality are genuinely pinned, and the over-constrained 3-arg reading refinement.md warns about is not admissible.

(6) siteDiffers argument ORDER is pinned too (atk_20 rejected), and the guard's disjunction is not weakenable (atk_21 rejected).

**RELATION TO THE PRIOR RECORD:** the bundle's verdict.md records an earlier G-EQ fail/BROKEN on the R-valid/float-invalid family (1e300 cancellation, whole-turn longitude wrap), and a later pass that found that family closed by the Float carrier. I did not re-encode that family (it is documented, twice-measured, and squarely R-leg territory owned by G-CONF); I spent the budget instead on the A legs my role owns plus the residual threat class the Float carrier CREATES — definitional-identity echoes, which are the only shapes that can verify against a `rfl`-tight spec. I found four such shapes, and all four resolve, so the carrier's strictness is not hiding an unfaithful admission. Per the retained-attack-label rule I did not re-judge any prior echo as a reject lane.

**CAVEAT ON SCOPE:** this pass adds no verdict on gates other than G-EQ. I note only for routing that meta.json records G-EQ, G-PANEL-1 and G-PANEL-2 fails while meta.status reads green; green_check.classify is the authority on greenness, not me.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 22 admissible attacks re-run of 22 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 22 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 18 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean`, `atk_19.lean`, `atk_20.lean`, `atk_21.lean`, `atk_22.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_11.lean`, `atk_12.lean`, `atk_17.lean`, `atk_18.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation was exhibited whose correct_* closes with clean axioms while its faithful refined patch fails to resolve. 22 same-spec attacks (same_spec=True for all 22 + the positive control, via swebench_unified.markers.same_spec / get_backend('lean')); 18 REJECTED (lean_verify exit 1) and 4 VERIFIED (exit 0) with clean axioms — and all 4 of those had their faithful patches materialized and RUN through run_resolve, all 4 RESOLVED at F2P 4/4, P2P 68/68, so all 4 are correct echoes, not spec weaknesses. The strongest attempted break was atk_17: both erfa.refco AND the ITRS->AltAz rotation hoisted above the guards that gate them (a pure Lean `let` hoist is definitionally invisible so `rfl` still closes). Its faithful patch evaluates refco and the AltAz matrix on inputs the gold code never touches — notably the library-DEFAULT zero-pressure HADec frame — and it still resolved, because erfa.refco is total and quiet at p=0 (measured: refco(0,0,0,1) = (0.0, -0.0), no warning) so the hoist is behaviourally inert. atk_18 (mvmul+transpose unfolded to the explicit index-order sum on the inverse hadec leg) was measured bit-identical to erfa.rxp(H^T, xyz) at 20000/20000 seeded draws, max abs diff 0.0 — value-preserving, and it resolved.
```

**Attacks re-run (22):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 22 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 18 — `atk_18.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 19 — `atk_19.lean` → rejected (same spec, does not verify — good)

Attack 20 — `atk_20.lean` → rejected (same spec, does not verify — good)

Attack 21 — `atk_21.lean` → rejected (same spec, does not verify — good)

Attack 22 — `atk_22.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity pass, astropy__astropy-13398 (lean). Per role, focus on the A legs (axioms / deep-model references) and the model<->patch correspondence; R/I left to G-CONF. All attacks built by copying the bundle Solution.lean and editing ONLY the two `impl` regions (axioms/pure/post-conditions byte-identical); proof regions left byte-identical so every attack is judged by the GOLD script `split_ifs <;> rfl`.

**COMMANDS.** Verify (each, run 4-way concurrent in background batches): `bash scripts/lean_verify.sh <name>.lean` from the repo root; exit code in <name>.exit, output in <name>.log. Same-spec: `python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; ..."` -> True for all 22 attacks + pos_control. Axioms: ax_11/12/17/18.lean = the attack plus `#print axioms correct_itrs_to_observed` / `correct_observed_to_itrs`, same verify command. Resolve: `python resolve.py <name>` calling swebench_unified.harness.run_resolve('astropy__astropy-13398', <diff>, timeout=3600), 4 launched concurrently; results in <name>.resolve.json / .resolve.log.

**POSITIVE CONTROL:** pos_control.lean (byte-identical to the shipped Solution.lean) -> exit 0.
PREPATCH REPRODUCED: atk_1 (refraction + HADec cross-rotation absent fwd, de-refraction absent inv — exactly the graded delta, i.e. the diff of the impl regions of Solution_prepatch.lean vs Solution.lean) -> exit 1, rejected. The rfl failure is the real one (LHS `mvmul (altazMat ...) (carryTo ...)` vs RHS the poleTilt-of-toApparent composition), so the spec does distinguish the pre-patch behaviour.

REJECTED, exit=1 (18): atk_1 (prepatch bug); atk_2 (A-reference output order: geodetic lon/lat exchanged, fwd); atk_3 (A-reference component pick: geodetic HEIGHT used as latitude, inv); atk_4 (A-reference arg binding: inverse carry direction reversed — the pair-of-pairs claim); atk_5 (A-reference arg binding: fwd carry TARGET epoch collapsed to srcEpoch); atk_6 (partial domain: refraction only when isAltAz, so HADec+atmosphere goes unrefracted); atk_7 (boundary: refraction guard pressure >= 0 for > 0 — fires on the library-default p=0); atk_8 (control-flow-effect: de-refract before undoing the HADec cross-rotation, inv); atk_9 (ungrounded-oracle echo: fwd leg applies toGeometric, the INVERSE closed form); atk_10 (A-leg control flow: fwd carry guard dropped, carry unconditional); atk_13 (A-reference input binding: bendCoefs relHumidity/obswl exchanged); atk_14 (A-reference output binding: bendCoefs coefficients swapped, inv); atk_15 (boundary on the OUTER guard: pressure >= 0 kills the hadec-no-atmosphere branch); atk_16 (partial domain / A-leg control flow: the UNCONDITIONAL inverse carry put behind a siteDiffers/epochDiffers guard); atk_19 (A-reference arg binding: fwd carry source site bound to f.location); atk_20 (A-reference arg ORDER: siteDiffers arguments exchanged); atk_21 (control flow: carry guard || weakened to &&); atk_22 (matrix selection: transpose dropped on the inverse altaz rotation).

VERIFIED, exit=0 (4) — ALL FOUR resolve-tested as mandated: atk_11 (fwd carry reads the mutable local `src` rather than the parameter `v`; result eta-expanded componentwise), atk_12 (triple transpose of the inverse cross-rotation), atk_17 (ECHO CANDIDATE: bendCoefs AND the altaz rotation hoisted above their guards), atk_18 (ECHO CANDIDATE: inverse hadec mvmul+transpose unfolded to the explicit index-order sum). `#print axioms` for BOTH theorems on each of the four -> [propext, Classical.choice, Quot.sound] = CLEAN, no sorry (ax_11/12/17/18.log, each exit 0).

RESOLVE RESULTS (executed, not speculated; faithful patches materialized in a base_commit worktree via mkpatch.sh + edit_<n>.py, each checked with `git apply --check` at base_commit = APPLIES CLEAN before submission):
- atk_11.diff -> completed=True RESOLVED, attempts=1, flaky=False, F2P 4/4, P2P 68/68, 0 failures.
- atk_12.diff -> completed=True RESOLVED, attempts=1, flaky=False, F2P 4/4, P2P 68/68, 0 failures.
- atk_17.diff -> completed=True RESOLVED, attempts=1, flaky=False, F2P 4/4, P2P 68/68, 0 failures.
- atk_18.diff -> completed=True RESOLVED, attempts=1, flaky=False, F2P 4/4, P2P 68/68, 0 failures.
So every impl with a closing clean-axiom proof has a materialized faithful patch that DOES resolve => no verify=/=>correct break. Supporting local measurements: erfa.refco is total and silent at the default zero atmosphere (refco(0,0,0,1) = (0.0,-0.0)), which is why atk_17's out-of-guard hoist is inert; and atk_18's hand-written index-order sum is bit-identical to erfa.rxp(H^T,xyz) at 20000/20000 seeded draws (max abs diff 0.0, probe18.py).

refinement.md AUDIT: 21 leg rows parsed; tag census = 8 R, 5 A-reference, 3 'R / I (branch)', 2 'I (branch)', 1 'R (mvmul) / I (branch)', 1 'R / I', 1 I. Every row carries R / A-reference / I; ZERO kind-3 legs and ZERO A-consumed axioms shipped — consistent with both proofs closing by `split_ifs <;> rfl`, so the result is produced by the modelled branch rather than echoed from an answer key. atk_9's oracle-echo rewrite (fwd leg reaching for the inverse closed form) is rejected, which confirms that independently.

A-REFERENCE CORRESPONDENCE, re-derived against the real callees rather than read off the tables:

(1) geodetic <- EarthLocation.to_geodetic('WGS84') returns Longitude/Latitude, i.e. DEGREES, which is why the model needs poleAngle=90.0 + angToRad; angToRad = 0.017453292519943295 is exactly math.pi/180 at binary64 (checked equal), matching NORTH_POLE=90.0*u.deg fed to rotation_matrix, whose base_commit body does angle.to_value(u.radian). The two rewrites that break this row, atk_2 (lon/lat exchanged) and atk_3 (height read as latitude), are both rejected.

(2) bendCoefs <- erfa.refco with arg order (p, T, rh, wl) and result order (refa, refb): atk_13 (input order) and atk_14 (output order) both rejected.

(3) normSplit/scaleVec <- erfa.pn/erfa.sxp with the SECOND pn's norm discarded and the FIRST restored by sxp — matches add_refraction verbatim in the patch.

(4) cartToSph/sphToCart <- erfa.c2s/erfa.s2c, and remove_refraction indeed lacks the CELMIN floor that add_refraction has, as the pure region and refinement.md both state.

(5) carryTo's 4-argument pair-of-pairs reading confirmed at BOTH call sites in the patch: the guarded pre-step of itrs_to_observed (:108-112) and the UNGUARDED trailing step of observed_to_itrs (:144-145) where itrs_frame supplies the target. Four independent rewrites of exactly that row — atk_4 (direction reversed), atk_5 (target epoch collapsed), atk_16 (unconditional carry put behind a guard), atk_19 (source site collapsed to the frame's) — are ALL rejected, so both the arity and the unconditionality are genuinely pinned, and the over-constrained 3-arg reading refinement.md warns about is not admissible.

(6) siteDiffers argument ORDER is pinned too (atk_20 rejected), and the guard's disjunction is not weakenable (atk_21 rejected).

**RELATION TO THE PRIOR RECORD:** the bundle's verdict.md records an earlier G-EQ fail/BROKEN on the R-valid/float-invalid family (1e300 cancellation, whole-turn longitude wrap), and a later pass that found that family closed by the Float carrier. I did not re-encode that family (it is documented, twice-measured, and squarely R-leg territory owned by G-CONF); I spent the budget instead on the A legs my role owns plus the residual threat class the Float carrier CREATES — definitional-identity echoes, which are the only shapes that can verify against a `rfl`-tight spec. I found four such shapes, and all four resolve, so the carrier's strictness is not hiding an unfaithful admission. Per the retained-attack-label rule I did not re-judge any prior echo as a reject lane.

**CAVEAT ON SCOPE:** this pass adds no verdict on gates other than G-EQ. I note only for routing that meta.json records G-EQ, G-PANEL-1 and G-PANEL-2 fails while meta.status reads green; green_check.classify is the authority on greenness, not me.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS ATTACK (spec-too-strong / drift): no divergence found. Reference = base_commit worktree with patch.diff APPLIED (verified: the new module itrs_observed_transforms.py is byte-IDENTICAL to the patch hunk body, and the same gold-patched tree is importable, astropy 5.1 / pyerfa 2.0.1.5 / numpy 1.22.4, with ITRS.location = EarthLocationAttribute present). Base commit used only as reference for the opaque callees.

**METHOD:** transcribed Solution.lean's spec bodies op-for-op into a Python replica (gp2f_13398_model.py) -- mmul/mvmul as explicit index-order sums, rotZ/rotY/flipX/flipY/flipXY, altazMat/hadecMat/poleTiltMat, toApparent/toGeometric verbatim, opaque callees bound per mapping.md (to_geodetic('WGS84') in DEGREES, erfa.refco/pn/sxp/c2s/s2c, ITRS->ITRS transform_to for carryTo). Compared against the REAL patched itrs_to_observed/observed_to_itrs and their real helpers. All comparisons on raw float64 BIT PATTERNS (uint64 view), so NaN/Inf/signed-zero/subnormal differences cannot hide, and exception-type equality is compared too.

### EVIDENCE (all zero mismatches):
1. Composed end-to-end fuzz, 300 mixed draws over 5 sites x 2 epochs x AltAz/HADec x pressure 0-or-positive, vectors to 4e8 m: worst_fwd = 0.0, worst_inv = 0.0 (exact).
2. EXHAUSTIVE branch/edge cross-product: 7 locations (incl. EARTH_CENTER geocenter, both poles, dateline lon=180, height -6.3e6 m, height 1e9 m) x AltAz/HADec x pressure {0, 1013.25} x 7 source sites x 2 source epochs x 2 frame epochs x 6 vectors (incl. zero vector) = 4704 forward + 4704 inverse cases, 4368 with the carry guard TRUE and 336 FALSE, so every one of the 4 branch cells in each leg plus both guard polarities are covered. BITWISE MISMATCHES: 0.
3. Rotation-matrix legs: 200k-draw fuzz over lon in [-180,180], lat in [-90,90] for all three matrices -> worst abs diff 0.0; repeated with angles fed from REAL to_geodetic Longitude/Latitude objects (20k sites, height -500..9000 m) -> 0.0. The degrees bridge is exact: (`x*u`.deg).to_value(u.radian) == `x*angToRad` on 500k draws (0 nonzero), and (NORTH_POLE - lat).to_value(u.radian) == (90.0-x)*angToRad on 500k draws (0 nonzero); angToRad == np.pi/180 bit-exactly. So poleAngle=90.0 + angToRad reproduce rotation_matrix's internal conversion exactly, not approximately.
4. mvmul vs the REAL erfa.rxp: 300k draws over the three real matrices and their transposes, including heavy-cancellation vectors ([1e17,1,-1e17], mixed 1e18/1e-18 scales, exponents 1e-20..1e20): 0 nonzero. Plus 200k dense random matrices: 0 nonzero. mmul vs numpy '@' on 200k dense pairs: 0 nonzero. The refinement.md worry that numpy may reassociate is not realised for 3x3 -- the model's index order IS the library's order, so this is stricter-than-needed tolerance, not drift.
5. Refraction legs vs the REAL add_refraction/remove_refraction: 50k random draws -> worst 0.0 both legs; plus a bitwise edge battery (zenith, horizon, below-horizon, NaN/+-Inf components, 1e-320 and 5e-324 subnormals, 1e308 overflow, the sel floor boundary 0.05 and 0.0500000001, the cel floor, zero vector) x 6 scales x 3 (p,t,h,wl) triples: 0 mismatches, exception types agreed. This confirms the two ASYMMETRIES the spec deliberately encodes are real, not over-modelling: toApparent floors cel with cosAltFloor while toGeometric does NOT (patch: np.maximum(...,CELMIN) vs bare np.sqrt), and the Newton-Raphson denominator (1+(A+3w)/sel^2) appears only in the forward leg. Lean's `max` and np.maximum agree on the NaN cases reached here (probed in Lean: max nan 0.05 = NaN, max 0.05 nan = 0.05, matching np.maximum's propagation on this operand order).
6. Pressure-branch edges: p in {0.0, -0.0, -1.0, -1e300, NaN, 1e-300, 5e-324, 1e300, Inf} x AltAz/HADec, both legs: 0 mismatches. NaN pressure agrees because Lean `nan > 0` is false (probed) exactly as Python's, so the spec's `f.pressure > 0` guard tracks `pressure > 0.0`.
7. carryTo semantics confirmed against the real pipeline: carryTo(v, loc, E, loc, E) returns v with worst |out-in| = 0.0 over 150 draws (identity when the pairs agree), and the UNGUARDED trailing carry in observed_to_itrs is faithful -- the no-op-target inverse matched bit-exactly in all 4 branch cells. The 4-argument (both-endpoint-pairs) reading in refinement.md is the correct one; a 3-argument reading would have over-constrained the inverse, so this spec is if anything weaker-and-correct here rather than too strong. Equal-but-distinct EarthLocation/Time objects compare EQUAL under np.any(a!=b), matching the model's siteDiffers/epochDiffers tag semantics.

**HYGIENE:** scripts/lean_verify.sh on the unmodified Solution.lean exits 0 (compiles, no sorry). `#print axioms` on BOTH theorems reports exactly [propext, Classical.choice, Quot.sound] = LeanBackend.STANDARD_AXIOMS, no sorryAx, so neither proof is fake. Both close by `split_ifs <;> rfl`, i.e. the result is produced by the modelled branch rather than echoed from an oracle axiom -- there is no A-consumed axiom to smuggle the answer in. markers.same_spec(Solution.lean, Solution.lean) = True with LeanBackend.language; spec_signature sha256 b1914eed93471a3a1efa66f40bf9127663bb2808ccc1820a302287e7a7ddc2ca (256 sig lines), and same_spec(Solution.lean, Solution_prepatch.lean) = True, confirming the spec region is byte-identical across the G-DIFF pair so the recorded relaxed-leak framing is about the impl region only. ('admit' matches the banned-token list only as a substring of no real occurrence -- it is not a standalone tactic here; the verify gate passes.)

**CONCLUSION:** on every input I could reach through the real API -- 9408 exhaustive branch/edge cases, ~1.3M targeted fuzz draws across the matrix, mat-vec and refraction bridges, and the full float64 pathology set -- the modelled function agrees with the real patched callee on the exact BIT PATTERN. I found no input on which the spec is stronger than, or drifts from, the patched repo behavior. The Float carrier is the correct choice and is not over-strong about VALUES; the one cost refinement.md discloses (a value-identical reassociation that `rfl` cannot close) is a limit on provability, not a faithfulness defect, and is honestly recorded rather than hidden. Verdict FAITHFUL. No diverging input to cite.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** panel_3: leakage accepted per RELAXED_LEAKAGE.md (agent flagged: leakage)

**What the spec view discloses.** Quoted from this bundle's own `RELAXED_LEAKAGE.md`, "Scope of the relaxation: which facet is dispositioned":

> *Atmospheric correction.* The `pure` region of the spec view exposes the step the `problem_statement` disclaims — that it exists, where it sits (`pressure > 0`, plus the hour-angle cross-rotation, and the forward/inverse asymmetry), and its closed form including both floor constants and their values. That disposition rests on the token scan, the impl-region diff identifying the graded delta, the eight-row divergence table with a bit-exact control, the 102-of-200 coverage count on the test's own grid, and the re-checked rival exits.

**Why the disclosure is accepted.** The same file's account of why the disclosure is forced rather than avoidable, "The mismatch (problem_statement ↔ gold)":

> The gold edit does not stop there. Measured (not read off a stamp): the diff of the `impl` regions of `Solution_prepatch.lean` against `Solution.lean` is *exactly* the refraction path — the `pressure > 0` arm with `toApparent` and the hour-angle cross-rotation in the forward leg, and the mirrored `toGeometric` block in the inverse leg. So the graded delta of this cell **is** the facet the `problem_statement` disclaims. A spec that says nothing about that facet does not distinguish the pre-patch implementation from the gold one, and G-DIFF — which requires `Solution_prepatch.lean` to FAIL — cannot pass.

**What this role measured.** The disposition this role defers to is recorded rather than assumed: `meta.json` sets `relaxed_leakage: true`, the bundle ships the `RELAXED_LEAKAGE.md` quoted above, and `G-LEAK` records `relaxed` with the detail `semantic leak of gold discriminator; unavoidable for a faithful spec`. The file quoted here is byte-identical to the one that gate read (sha256 `2ed4d0b6b1fd`, recorded under `G-LEAK`'s own sources), and it carries no instruction to the role reviewing it -- a relaxation document that told this panel which verdict to submit would make `G-LEAK` record a failure instead of a relaxation, so the argument above is one this role judged rather than one it was handed.

`G-LEAK`'s lexical screen recorded no failures of its own, which is what places this disclosure in what the specification pins rather than in a word the spec view uses. This role is advisory and only `G-LEAK` is recorded for leakage on this cell, which is why the deferral is a pass here and not a status of its own. The panel submitted `LEAKAGE`; a non-empty verdict is required for the deferral to apply at all, so a review that never ran is recorded as reaching no verdict rather than as deferring to this file. The panel's own account -- whether it accepts the argument quoted above or presses further against it -- is published in this cell's audit record.

Counterexample / evidence:

```
The relaxation covers exactly one facet -- atmospheric refraction. I re-confirmed that facet IS load-bearing, then measured a SECOND, independently leaking facet the relaxation explicitly places outside its scope: the (site, epoch) carry guard.

MEASURED,  via scripts/lean_verify.sh:

(1) Refraction facet is genuinely forced (relaxation's own test, re-derived, NOT inherited). STRIP.lean = pre-patch impl + a spec with the refraction arm deleted from BOTH postconditions: exit 0, VERIFIES. So the refraction clause is load-bearing for G-DIFF; a spec silent about it cannot see the bug. Controls: Solution.lean exit 0; Solution_prepatch.lean exit 3 ('declaration uses sorry' x2); #print axioms on both correct_* theorems = [propext, Classical.choice, Quot.sound] only, no sorryAx. markers.same_spec(gold, prepatch) = True. leakage.screen() = passed, 0 hard failures. leakage.reviewer_directed(RELAXED_LEAKAGE.md) = [] (the file does not steer me; it explicitly disclaims propagating its flag to the panel layer -- correct conduct, recorded).

(2) The carry facet is NOT forced, and is NOT covered by the relaxation. I built NOCARRY_GOLD.lean: the spec with carryTo/siteDiffers/epochDiffers/srcLoc/srcEpoch/tgtLoc/tgtEpoch deleted outright (domain scoped to the same-(site,epoch) case), KEEPING the refraction discriminator. Result: exit 0, verifies. Cross-control NOCARRY_DIFF.lean (that same carry-free spec against the refraction-free pre-patch impl): exit 1, 'Tactic rfl failed ... mvmul (altazMat ...) v is not definitionally equal to ... poleTiltMat ... toApparent ...'. So a spec carrying ZERO carry vocabulary still rejects the pre-patch implementation. The carry facet is therefore not needed for G-DIFF -- the unavoidability argument that licenses the refraction leak does not extend to it, and RELAXED_LEAKAGE.md's own 'What is outside it' section concedes that anything beyond the refraction facet 'is untouched by this disposition and is not argued for above'.

(3) The carry facet is not derivable from the problem_statement -- it is the statement's OPPOSITE. The public statement says the transform 'treats the ITRS position as time invariant', that 'it makes no sense to be doing an ITRS->ITRS transform for differing obstimes', and that 'the obstime of the output frame is simply adopted'; its inlined sketch has NO guard at all (np.any = 0 hits, 'location !=' = 0, transform_to(ITRS = 0, itrs_coo.location = 0, EarthLocationAttribute = 0, 'identity' = 0, exactly one 'if' = the isinstance(observed_frame, AltAz) split). A solver reading the statement would omit the carry entirely. The gold patch does the reverse: it adds `location = EarthLocationAttribute(default=EARTH_CENTER)` to ITRS and a guarded `itrs_coo.transform_to(ITRS(obstime=..., location=...))` pre-step plus an UNCONDITIONAL trailing `itrs_at_obs_time.transform_to(itrs_frame)`. The spec view hands the solver precisely that inversion: which leg is guarded, which is unconditional, that the guard is a disjunction over site AND epoch, that the carry is the identity when the pairs agree, and that it routes through an inertial frame 'which also shifts stellar aberration'. That last clause is edit-localization for the graded test test_cirs_itrs_topo (F2P), whose whole point is that a differing obstime must NOT round-trip -- a fact the statement argues against.

So: core soundness holds and the refraction relaxation's argument survives re-derivation, but the spec view leaks a second facet beyond the one dispositioned, and that facet is refuted rather than supported by the problem_statement. Per the layer's rule ('LEAKAGE for anything the argument does not cover: a leaking line beyond that facet'), this is LEAKAGE.
```

**FACET RE-CONFIRMED:** refraction. I re-derived the relaxation's unavoidability test rather than inheriting it -- STRIP.lean (pre-patch impl + refraction-stripped spec) verifies at exit 0, so the removed clause was load-bearing and G-DIFF genuinely cannot pass without naming the atmospheric-correction step. Gold exit 0, prepatch exit 3, #print axioms clean on both theorems (no sorryAx), same_spec True, lexical screen clean, reviewer_directed empty. The relaxation's supporting claims that I spot-checked all held: at base_commit 6500928dc0e57be8f06d1162eacc3ba5e2eff692 (worktree, HEAD confirmed) SELMIN/CELMIN/add_refraction/remove_refraction/altaz_to_hadec_mat/itrs_to_altaz_mat/NORTH_POLE = 0 hits each, while refa/refb/erfa.refco are pre-existing repo vocabulary (erfa_astrom.py:59,67,74,161,342) as the file claims; all 20 renamed spec-view identifiers are 0-hit against the base tree, so the rename campaign did remove the edit-localization pointer it claimed to.

**WHAT BREAKS IT:** not the covered facet, but scope. The relaxation dispositions exactly one facet and says so ('Nothing here speaks to any other leaking line'). I measured a second one that its argument does not reach: NOCARRY_GOLD.lean -- the spec with every carry symbol deleted but refraction retained -- verifies (exit 0), and its cross-control against the refraction-free pre-patch impl fails (exit 1, rfl failure on the toApparent/poleTiltMat arm). That proves the carry vocabulary is surplus to G-DIFF: the refraction clause alone already discriminates. Meanwhile the carry facet is anti-derivable from the public statement, which asserts the opposite design ('time invariant', 'obstime of the output frame is simply adopted', no guard anywhere in the sketch, 0 hits for np.any / location != / transform_to(ITRS / EarthLocationAttribute / 'identity'). The spec view supplies the guard's exact shape (disjunction over site and epoch), the forward/inverse guarded-vs-unconditional asymmetry, identity-when-pairs-agree, and the stellar-aberration consequence that is the sole content of the F2P test test_cirs_itrs_topo.

**CONDUCT NOTE:** RELAXED_LEAKAGE.md did not instruct me. It states its mismatch, invites refutation ('A reader who reaches a different number than the tables record has found something this file gets wrong'), and correctly notes that its flag does not propagate to the panel layer. reviewer_directed() returns [] on it, matching that reading. Its numeric refraction tables I did not re-run in-image (the divergence measurements are orthogonal to my finding, which is a scope defect, not a faithfulness defect) -- flagging that as the one part of the file I took on report rather than measurement.

**REPAIR DIRECTION:** either scope the modelled domain to the same-(site,epoch) case and drop the carry entirely (measured to still pass G-DIFF), or extend RELAXED_LEAKAGE.md with a second, separately-argued facet -- but the second route needs an unavoidability argument that does not exist, since NOCARRY_GOLD.lean verifies. Artifacts: {G,P,STRIP,AX,NOCARRY_GOLD,NOCARRY_DIFF}.{lean,log,exit}.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded LEAKAGE. The record is a pass because the disclosure it names had already been accepted by a reviewer: an accepted relaxation is the leakage GATE's disposition to record, and this cell records G-LEAK as `relaxed`. This role defers to that disposition rather than re-failing the cell, and is recorded as a pass with a note because `relaxed` is not a status it may take. So the pass rests on an accepted disclosure and not on the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
