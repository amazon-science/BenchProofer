# P2 adversarial audit — astropy__astropy-13398

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE. All 15 same-spec, admissible wrong impls were REJECTED by the frozen spec (every one a genuine `Postcondition of <fn> might not hold`, exit=2 from `adversary weakness`). ZERO CANDIDATEs, so protocol step 2 (materialize the faithful refined patch and run run_resolve) had nothing to run: no verifying wrong impl exists on this spec, hence no patch was owed and none is submitted. The prior pass's named counterexample -- the observed forward rotating the GIVEN triple with M(T) with gold's :106-110 re-referencing block deleted, whose faithful patch is on record as FAILING resolve at P2P 63/68 on test_gcrs_altaz_bothroutes[testframe0..4] -- is re-encoded here as atk_10 and is REJECTED (Postcondition of itrs_to_observed), as is the site-only partial-domain shape that broke it (atk_11).

My PRINCIPAL INDEPENDENT FINDING is that I closed the one hole the prior pass named but never machine-checked. That pass observed that `observed_roundtrip` can be discharged TRIVIALLY (return vx/vy/vz, composing neither conversion; it verifies) and argued from that observation alone that this is harmless because the round-trip composite is not a repo function. That argument is only sound if the two CONVERSIONS stay independently pinned once the round trip stops witnessing them -- which the prior pass asserted rather than tested. I tested the COMBINATION directly: atk_13 (trivial observed round trip AND the historical resolve-breaking forward), atk_14 (trivial equatorial round trip AND the pre-patch constant-geocentre re-reference), and atk_15 (BOTH round trips trivial AND all four conversions reverted verbatim to model_prepatch.py). Had any verified, its faithful patch would have been the historical resolve-breaker and the spec would be BROKEN. All three are REJECTED, atk_15 with all FOUR conversion postconditions failing at once. The paired isolating control probe_rt_trivial.py (both round trips trivial, both conversions left GOLD) VERIFIES -- so the trivial discharge removes a redundant witness, not the obligation. That completes the prior pass's argument with machine evidence instead of reasoning.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -341,17 +341,24 @@
         tx, ty, tz)))
     # post-conditions-end
     # impl-start
-    # Refer the position to the OUTPUT frame's own anchoring (site T, epoch
-    # etgt), then rotate the re-referred position with the orientation matrix
-    # built from that same output frame's own site T.
-    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+    # INDIRECT skeleton, and no re-referencing. There is no direct Earth-fixed
+    # -> observer-centred rotation: the observer-centred orientation is reached by
+    # routing through an intermediate (geocentric) frame, which inserts an extra
+    # frame rotation before the orientation matrix is applied -- the matrix is NOT
+    # applied to the re-referred position. And the position is rotated AS IT
+    # STANDS, i.e. taken to be already referred to the geocentre, rather than
+    # referred to the output frame's own site T and epoch etgt first. This is the
+    # viewpoint-dependent ("aberration") shift the issue describes; it does not
+    # reproduce the direct rotation of the re-referred position, so it cannot
+    # satisfy the postcondition.
+    ix = bwd_x(vx, vy, vz, tx, ty, tz)
+    iy = bwd_y(vx, vy, vz, tx, ty, tz)
+    iz = bwd_z(vx, vy, vz, tx, ty, tz)
     if comp == 0:
-        return fwd_x(wx, wy, wz, tx, ty, tz)
+        return fwd_x(ix, iy, iz, tx, ty, tz)
     if comp == 1:
-        return fwd_y(wx, wy, wz, tx, ty, tz)
-    return fwd_z(wx, wy, wz, tx, ty, tz)
+        return fwd_y(ix, iy, iz, tx, ty, tz)
+    return fwd_z(ix, iy, iz, tx, ty, tz)
     # impl-end
 
 
@@ -392,17 +399,17 @@
         lx, ly, lz, esrc, tx, ty, tz, etgt)))
     # post-conditions-end
     # impl-start
-    # Rotate with the transpose of the orientation matrix built from the INPUT
-    # frame's own site L, then refer the rotated position from the input frame's
-    # own anchoring to the output frame's anchoring.
-    wx = bwd_x(ox, oy, oz, lx, ly, lz)
-    wy = bwd_y(ox, oy, oz, lx, ly, lz)
-    wz = bwd_z(ox, oy, oz, lx, ly, lz)
+    # Rotate with the transpose of the orientation matrix built from the input
+    # frame's own site L, and then RETURN THE ROTATED POSITION AS IT STANDS: the
+    # rotated position is left referred to the anchoring the input carried, and is
+    # never referred on to the output frame's site T and epoch etgt. Whenever the
+    # two anchorings differ this is a different position from the one the output
+    # frame asks for, so it cannot satisfy the postcondition.
     if comp == 0:
-        return wx + offset_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+        return bwd_x(ox, oy, oz, lx, ly, lz)
     if comp == 1:
-        return wy + offset_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    return wz + offset_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+        return bwd_y(ox, oy, oz, lx, ly, lz)
+    return bwd_z(ox, oy, oz, lx, ly, lz)
     # impl-end
 
 
@@ -509,12 +516,16 @@
         rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt), etgt)))
     # post-conditions-end
     # impl-start
-    # Refer the position to the OUTPUT frame's own anchoring (site T, epoch
-    # etgt), then rotate the re-referred position with the Earth-orientation
-    # rotation for that same epoch etgt.
-    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+    # Refer the position to ONE CONSTANT SITE -- the centre of the Earth, site
+    # (0, 0, 0) -- at the output frame's epoch etgt, rather than to the OUTPUT
+    # frame's own site T, and then rotate at that epoch. Whenever the output
+    # frame's site is not the centre of the Earth this leaves the position
+    # referred somewhere other than where the output frame asks for, so the result
+    # is not the rotation of the position referred to the output frame's own
+    # anchoring, and cannot satisfy the postcondition.
+    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, 0, 0, 0, etgt)
+    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, 0, 0, 0, etgt)
+    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, 0, 0, 0, etgt)
     if comp == 0:
         return prot_x(wx, wy, wz, etgt)
     if comp == 1:
@@ -561,16 +572,20 @@
     # post-conditions-end
     # impl-start
     # Rotate with the transpose of the Earth-orientation rotation for the INPUT
-    # frame's epoch esrc, then refer the rotated position from the input frame's
-    # own anchoring to the output frame's anchoring.
+    # frame's epoch esrc, then refer the rotated position as if it were held at
+    # ONE CONSTANT SITE -- the centre of the Earth, site (0, 0, 0) -- rather than
+    # at the input frame's OWN site L. Whenever the input frame's site is not the
+    # centre of the Earth this refers the position from somewhere other than where
+    # it is actually held, so the result is not the rotated position referred from
+    # the input frame's own anchoring, and cannot satisfy the postcondition.
     wx = prot_inv_x(ox, oy, oz, esrc)
     wy = prot_inv_y(ox, oy, oz, esrc)
     wz = prot_inv_z(ox, oy, oz, esrc)
     if comp == 0:
-        return wx + offset_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+        return wx + offset_x(wx, wy, wz, 0, 0, 0, esrc, tx, ty, tz, etgt)
     if comp == 1:
-        return wy + offset_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    return wz + offset_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+        return wy + offset_y(wx, wy, wz, 0, 0, 0, esrc, tx, ty, tz, etgt)
+    return wz + offset_z(wx, wy, wz, 0, 0, 0, esrc, tx, ty, tz, etgt)
     # impl-end
 
 
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -392,17 +392,19 @@
         lx, ly, lz, esrc, tx, ty, tz, etgt)))
     # post-conditions-end
     # impl-start
-    # Rotate with the transpose of the orientation matrix built from the INPUT
-    # frame's own site L, then refer the rotated position from the input frame's
-    # own anchoring to the output frame's anchoring.
-    wx = bwd_x(ox, oy, oz, lx, ly, lz)
-    wy = bwd_y(ox, oy, oz, lx, ly, lz)
-    wz = bwd_z(ox, oy, oz, lx, ly, lz)
+
+    r0 = itrs_to_observed(0, ox, oy, oz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+    r1 = itrs_to_observed(1, ox, oy, oz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+    r2 = itrs_to_observed(2, ox, oy, oz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+    orthogonality(rebased_x(ox, oy, oz, lx, ly, lz, esrc, tx, ty, tz, etgt),
+                  rebased_y(ox, oy, oz, lx, ly, lz, esrc, tx, ty, tz, etgt),
+                  rebased_z(ox, oy, oz, lx, ly, lz, esrc, tx, ty, tz, etgt),
+                  tx, ty, tz)
     if comp == 0:
-        return wx + offset_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+        return bwd_x(r0, r1, r2, tx, ty, tz)
     if comp == 1:
-        return wy + offset_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    return wz + offset_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+        return bwd_y(r0, r1, r2, tx, ty, tz)
+    return bwd_z(r0, r1, r2, tx, ty, tz)
     # impl-end
 
 
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -509,12 +509,13 @@
         rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt), etgt)))
     # post-conditions-end
     # impl-start
-    # Refer the position to the OUTPUT frame's own anchoring (site T, epoch
-    # etgt), then rotate the re-referred position with the Earth-orientation
-    # rotation for that same epoch etgt.
-    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+
+    ax = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, esrc)
+    ay = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, esrc)
+    az = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, esrc)
+    wx = ax + offset_x(ax, ay, az, tx, ty, tz, esrc, tx, ty, tz, etgt)
+    wy = ay + offset_y(ax, ay, az, tx, ty, tz, esrc, tx, ty, tz, etgt)
+    wz = az + offset_z(ax, ay, az, tx, ty, tz, esrc, tx, ty, tz, etgt)
     if comp == 0:
         return prot_x(wx, wy, wz, etgt)
     if comp == 1:
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -560,17 +560,15 @@
         lx, ly, lz, esrc, tx, ty, tz, etgt)))
     # post-conditions-end
     # impl-start
-    # Rotate with the transpose of the Earth-orientation rotation for the INPUT
-    # frame's epoch esrc, then refer the rotated position from the input frame's
-    # own anchoring to the output frame's anchoring.
-    wx = prot_inv_x(ox, oy, oz, esrc)
-    wy = prot_inv_y(ox, oy, oz, esrc)
-    wz = prot_inv_z(ox, oy, oz, esrc)
+
+    ax = ox + offset_x(ox, oy, oz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+    ay = oy + offset_y(ox, oy, oz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+    az = oz + offset_z(ox, oy, oz, lx, ly, lz, esrc, tx, ty, tz, etgt)
     if comp == 0:
-        return wx + offset_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+        return prot_inv_x(ax, ay, az, esrc)
     if comp == 1:
-        return wy + offset_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    return wz + offset_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+        return prot_inv_y(ax, ay, az, esrc)
+    return prot_inv_z(ax, ay, az, esrc)
     # impl-end
 
 
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -392,17 +392,15 @@
         lx, ly, lz, esrc, tx, ty, tz, etgt)))
     # post-conditions-end
     # impl-start
-    # Rotate with the transpose of the orientation matrix built from the INPUT
-    # frame's own site L, then refer the rotated position from the input frame's
-    # own anchoring to the output frame's anchoring.
+
     wx = bwd_x(ox, oy, oz, lx, ly, lz)
     wy = bwd_y(ox, oy, oz, lx, ly, lz)
     wz = bwd_z(ox, oy, oz, lx, ly, lz)
     if comp == 0:
-        return wx + offset_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+        return wx + offset_x(ox, oy, oz, lx, ly, lz, esrc, tx, ty, tz, etgt)
     if comp == 1:
-        return wy + offset_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    return wz + offset_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+        return wy + offset_y(ox, oy, oz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+    return wz + offset_z(ox, oy, oz, lx, ly, lz, esrc, tx, ty, tz, etgt)
     # impl-end
 
 
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -509,12 +509,10 @@
         rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt), etgt)))
     # post-conditions-end
     # impl-start
-    # Refer the position to the OUTPUT frame's own anchoring (site T, epoch
-    # etgt), then rotate the re-referred position with the Earth-orientation
-    # rotation for that same epoch etgt.
-    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+
+    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, esrc)
+    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, esrc)
+    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, esrc)
     if comp == 0:
         return prot_x(wx, wy, wz, etgt)
     if comp == 1:
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -509,9 +509,15 @@
         rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt), etgt)))
     # post-conditions-end
     # impl-start
-    # Refer the position to the OUTPUT frame's own anchoring (site T, epoch
-    # etgt), then rotate the re-referred position with the Earth-orientation
-    # rotation for that same epoch etgt.
+
+    if esrc == etgt:
+        same_frame_noop(vx, vy, vz, lx, ly, lz, esrc)
+        same_frame_noop(vx, vy, vz, tx, ty, tz, etgt)
+        if comp == 0:
+            return prot_x(vx, vy, vz, etgt)
+        if comp == 1:
+            return prot_y(vx, vy, vz, etgt)
+        return prot_z(vx, vy, vz, etgt)
     wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
     wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
     wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -341,17 +341,19 @@
         tx, ty, tz)))
     # post-conditions-end
     # impl-start
-    # Refer the position to the OUTPUT frame's own anchoring (site T, epoch
-    # etgt), then rotate the re-referred position with the orientation matrix
-    # built from that same output frame's own site T.
+
+    orthogonality(vx, vy, vz, lx, ly, lz)
+    orthogonality(vx, vy, vz, tx, ty, tz)
     wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
     wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
     wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+    orthogonality(wx, wy, wz, lx, ly, lz)
+    orthogonality(wx, wy, wz, tx, ty, tz)
     if comp == 0:
-        return fwd_x(wx, wy, wz, tx, ty, tz)
+        return fwd_x(wx, wy, wz, lx, ly, lz)
     if comp == 1:
-        return fwd_y(wx, wy, wz, tx, ty, tz)
-    return fwd_z(wx, wy, wz, tx, ty, tz)
+        return fwd_y(wx, wy, wz, lx, ly, lz)
+    return fwd_z(wx, wy, wz, lx, ly, lz)
     # impl-end
 
 
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -560,17 +560,17 @@
         lx, ly, lz, esrc, tx, ty, tz, etgt)))
     # post-conditions-end
     # impl-start
-    # Rotate with the transpose of the Earth-orientation rotation for the INPUT
-    # frame's epoch esrc, then refer the rotated position from the input frame's
-    # own anchoring to the output frame's anchoring.
+
     wx = prot_inv_x(ox, oy, oz, esrc)
     wy = prot_inv_y(ox, oy, oz, esrc)
     wz = prot_inv_z(ox, oy, oz, esrc)
+    same_frame_noop(wx, wy, wz, tx, ty, tz, etgt)
+    same_frame_noop(wx, wy, wz, lx, ly, lz, esrc)
     if comp == 0:
-        return wx + offset_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+        return wx + offset_x(wx, wy, wz, tx, ty, tz, etgt, tx, ty, tz, etgt)
     if comp == 1:
-        return wy + offset_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    return wz + offset_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+        return wy + offset_y(wx, wy, wz, tx, ty, tz, etgt, tx, ty, tz, etgt)
+    return wz + offset_z(wx, wy, wz, tx, ty, tz, etgt, tx, ty, tz, etgt)
     # impl-end
 
 
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -341,17 +341,14 @@
         tx, ty, tz)))
     # post-conditions-end
     # impl-start
-    # Refer the position to the OUTPUT frame's own anchoring (site T, epoch
-    # etgt), then rotate the re-referred position with the orientation matrix
-    # built from that same output frame's own site T.
-    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+
+    same_frame_noop(vx, vy, vz, lx, ly, lz, esrc)
+    same_frame_noop(vx, vy, vz, tx, ty, tz, etgt)
     if comp == 0:
-        return fwd_x(wx, wy, wz, tx, ty, tz)
+        return fwd_x(vx, vy, vz, tx, ty, tz)
     if comp == 1:
-        return fwd_y(wx, wy, wz, tx, ty, tz)
-    return fwd_z(wx, wy, wz, tx, ty, tz)
+        return fwd_y(vx, vy, vz, tx, ty, tz)
+    return fwd_z(vx, vy, vz, tx, ty, tz)
     # impl-end
 
 
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -341,9 +341,14 @@
         tx, ty, tz)))
     # post-conditions-end
     # impl-start
-    # Refer the position to the OUTPUT frame's own anchoring (site T, epoch
-    # etgt), then rotate the re-referred position with the orientation matrix
-    # built from that same output frame's own site T.
+
+    if lx == tx and ly == ty and lz == tz:
+        same_frame_noop(vx, vy, vz, lx, ly, lz, esrc)
+        if comp == 0:
+            return fwd_x(vx, vy, vz, tx, ty, tz)
+        if comp == 1:
+            return fwd_y(vx, vy, vz, tx, ty, tz)
+        return fwd_z(vx, vy, vz, tx, ty, tz)
     wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
     wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
     wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -560,17 +560,21 @@
         lx, ly, lz, esrc, tx, ty, tz, etgt)))
     # post-conditions-end
     # impl-start
-    # Rotate with the transpose of the Earth-orientation rotation for the INPUT
-    # frame's epoch esrc, then refer the rotated position from the input frame's
-    # own anchoring to the output frame's anchoring.
+
     wx = prot_inv_x(ox, oy, oz, esrc)
     wy = prot_inv_y(ox, oy, oz, esrc)
     wz = prot_inv_z(ox, oy, oz, esrc)
+    e0 = observed_roundtrip(0, wx, wy, wz, lx, ly, lz, esrc)
+    e1 = observed_roundtrip(1, wx, wy, wz, lx, ly, lz, esrc)
+    e2 = observed_roundtrip(2, wx, wy, wz, lx, ly, lz, esrc)
+    prot_orthogonality(ox, oy, oz, esrc)
+    prot_orthogonality(wx, wy, wz, etgt)
+    same_frame_noop(wx, wy, wz, lx, ly, lz, esrc)
     if comp == 0:
-        return wx + offset_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+        return e0
     if comp == 1:
-        return wy + offset_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    return wz + offset_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+        return e1
+    return e2
     # impl-end
 
 
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -341,17 +341,13 @@
         tx, ty, tz)))
     # post-conditions-end
     # impl-start
-    # Refer the position to the OUTPUT frame's own anchoring (site T, epoch
-    # etgt), then rotate the re-referred position with the orientation matrix
-    # built from that same output frame's own site T.
-    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+
+    same_frame_noop(vx, vy, vz, lx, ly, lz, esrc)
     if comp == 0:
-        return fwd_x(wx, wy, wz, tx, ty, tz)
+        return fwd_x(vx, vy, vz, tx, ty, tz)
     if comp == 1:
-        return fwd_y(wx, wy, wz, tx, ty, tz)
-    return fwd_z(wx, wy, wz, tx, ty, tz)
+        return fwd_y(vx, vy, vz, tx, ty, tz)
+    return fwd_z(vx, vy, vz, tx, ty, tz)
     # impl-end
 
 
@@ -431,44 +427,12 @@
     Ensures(Implies(comp == 2, Result() == vz))
     # post-conditions-end
     # impl-start
-    # OUTBOUND LEG. Both frames carry the same anchoring, so referring between
-    # them introduces no offset and the re-referred position is the position
-    # itself.
-    same_frame_noop(vx, vy, vz, lx, ly, lz, e)
-    qx = rebased_x(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    qy = rebased_y(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    qz = rebased_z(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    Assert(qx == vx)
-    Assert(qy == vy)
-    Assert(qz == vz)
-    # The observer-centred components are the orientation matrix for the shared
-    # site applied to that re-referred position (each equals the corresponding
-    # forward-conversion output by that conversion's postcondition).
-    ox = fwd_x(qx, qy, qz, lx, ly, lz)
-    oy = fwd_y(qx, qy, qz, lx, ly, lz)
-    oz = fwd_z(qx, qy, qz, lx, ly, lz)
-    r0 = itrs_to_observed(0, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    r1 = itrs_to_observed(1, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    r2 = itrs_to_observed(2, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    Assert(r0 == ox)
-    Assert(r1 == oy)
-    Assert(r2 == oz)
-    # RETURN LEG. The transpose-action for that same site undoes the
-    # forward-action, recovering the re-referred position and hence the input.
-    orthogonality(qx, qy, qz, lx, ly, lz)
-    wx = bwd_x(ox, oy, oz, lx, ly, lz)
-    wy = bwd_y(ox, oy, oz, lx, ly, lz)
-    wz = bwd_z(ox, oy, oz, lx, ly, lz)
-    Assert(wx == vx)
-    Assert(wy == vy)
-    Assert(wz == vz)
-    # The return leg refers between the same anchoring as well, so it introduces
-    # no offset either.
-    same_frame_noop(wx, wy, wz, lx, ly, lz, e)
-    Assert(rebased_x(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vx)
-    Assert(rebased_y(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vy)
-    Assert(rebased_z(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vz)
-    return observed_to_itrs(comp, ox, oy, oz, lx, ly, lz, e, lx, ly, lz, e)
+
+    if comp == 0:
+        return vx
+    if comp == 1:
+        return vy
+    return vz
     # impl-end
 
 
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

```diff
@@ -509,12 +509,10 @@
         rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt), etgt)))
     # post-conditions-end
     # impl-start
-    # Refer the position to the OUTPUT frame's own anchoring (site T, epoch
-    # etgt), then rotate the re-referred position with the Earth-orientation
-    # rotation for that same epoch etgt.
-    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+
+    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, 0, 0, 0, etgt)
+    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, 0, 0, 0, etgt)
+    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, 0, 0, 0, etgt)
     if comp == 0:
         return prot_x(wx, wy, wz, etgt)
     if comp == 1:
@@ -598,42 +596,10 @@
     Ensures(Implies(comp == 2, Result() == vz))
     # post-conditions-end
     # impl-start
-    # OUTBOUND LEG. Both frames carry the same anchoring, so referring between
-    # them introduces no offset and the re-referred position is the position
-    # itself.
-    same_frame_noop(vx, vy, vz, lx, ly, lz, e)
-    qx = rebased_x(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    qy = rebased_y(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    qz = rebased_z(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    Assert(qx == vx)
-    Assert(qy == vy)
-    Assert(qz == vz)
-    # The Earth-rotating components are the rotation, at the shared epoch, of
-    # that re-referred position (each equals the corresponding forward-conversion
-    # output by that conversion's postcondition).
-    ox = prot_x(qx, qy, qz, e)
-    oy = prot_y(qx, qy, qz, e)
-    oz = prot_z(qx, qy, qz, e)
-    r0 = equ_to_rot(0, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    r1 = equ_to_rot(1, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    r2 = equ_to_rot(2, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    Assert(r0 == ox)
-    Assert(r1 == oy)
-    Assert(r2 == oz)
-    # RETURN LEG. The inverse rotation at that same epoch undoes the forward
-    # rotation, recovering the re-referred position and hence the input.
-    prot_orthogonality(qx, qy, qz, e)
-    wx = prot_inv_x(ox, oy, oz, e)
-    wy = prot_inv_y(ox, oy, oz, e)
-    wz = prot_inv_z(ox, oy, oz, e)
-    Assert(wx == vx)
-    Assert(wy == vy)
-    Assert(wz == vz)
-    # The return leg refers between the same anchoring as well, so it introduces
-    # no offset either.
-    same_frame_noop(wx, wy, wz, lx, ly, lz, e)
-    Assert(rebased_x(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vx)
-    Assert(rebased_y(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vy)
-    Assert(rebased_z(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vz)
-    return rot_to_equ(comp, ox, oy, oz, lx, ly, lz, e, lx, ly, lz, e)
+
+    if comp == 0:
+        return vx
+    if comp == 1:
+        return vy
+    return vz
     # impl-end
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

```diff
@@ -341,17 +341,24 @@
         tx, ty, tz)))
     # post-conditions-end
     # impl-start
-    # Refer the position to the OUTPUT frame's own anchoring (site T, epoch
-    # etgt), then rotate the re-referred position with the orientation matrix
-    # built from that same output frame's own site T.
-    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+    # INDIRECT skeleton, and no re-referencing. There is no direct Earth-fixed
+    # -> observer-centred rotation: the observer-centred orientation is reached by
+    # routing through an intermediate (geocentric) frame, which inserts an extra
+    # frame rotation before the orientation matrix is applied -- the matrix is NOT
+    # applied to the re-referred position. And the position is rotated AS IT
+    # STANDS, i.e. taken to be already referred to the geocentre, rather than
+    # referred to the output frame's own site T and epoch etgt first. This is the
+    # viewpoint-dependent ("aberration") shift the issue describes; it does not
+    # reproduce the direct rotation of the re-referred position, so it cannot
+    # satisfy the postcondition.
+    ix = bwd_x(vx, vy, vz, tx, ty, tz)
+    iy = bwd_y(vx, vy, vz, tx, ty, tz)
+    iz = bwd_z(vx, vy, vz, tx, ty, tz)
     if comp == 0:
-        return fwd_x(wx, wy, wz, tx, ty, tz)
+        return fwd_x(ix, iy, iz, tx, ty, tz)
     if comp == 1:
-        return fwd_y(wx, wy, wz, tx, ty, tz)
-    return fwd_z(wx, wy, wz, tx, ty, tz)
+        return fwd_y(ix, iy, iz, tx, ty, tz)
+    return fwd_z(ix, iy, iz, tx, ty, tz)
     # impl-end
 
 
@@ -392,17 +399,17 @@
         lx, ly, lz, esrc, tx, ty, tz, etgt)))
     # post-conditions-end
     # impl-start
-    # Rotate with the transpose of the orientation matrix built from the INPUT
-    # frame's own site L, then refer the rotated position from the input frame's
-    # own anchoring to the output frame's anchoring.
-    wx = bwd_x(ox, oy, oz, lx, ly, lz)
-    wy = bwd_y(ox, oy, oz, lx, ly, lz)
-    wz = bwd_z(ox, oy, oz, lx, ly, lz)
+    # Rotate with the transpose of the orientation matrix built from the input
+    # frame's own site L, and then RETURN THE ROTATED POSITION AS IT STANDS: the
+    # rotated position is left referred to the anchoring the input carried, and is
+    # never referred on to the output frame's site T and epoch etgt. Whenever the
+    # two anchorings differ this is a different position from the one the output
+    # frame asks for, so it cannot satisfy the postcondition.
     if comp == 0:
-        return wx + offset_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+        return bwd_x(ox, oy, oz, lx, ly, lz)
     if comp == 1:
-        return wy + offset_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    return wz + offset_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+        return bwd_y(ox, oy, oz, lx, ly, lz)
+    return bwd_z(ox, oy, oz, lx, ly, lz)
     # impl-end
 
 
@@ -431,44 +438,12 @@
     Ensures(Implies(comp == 2, Result() == vz))
     # post-conditions-end
     # impl-start
-    # OUTBOUND LEG. Both frames carry the same anchoring, so referring between
-    # them introduces no offset and the re-referred position is the position
-    # itself.
-    same_frame_noop(vx, vy, vz, lx, ly, lz, e)
-    qx = rebased_x(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    qy = rebased_y(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    qz = rebased_z(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    Assert(qx == vx)
-    Assert(qy == vy)
-    Assert(qz == vz)
-    # The observer-centred components are the orientation matrix for the shared
-    # site applied to that re-referred position (each equals the corresponding
-    # forward-conversion output by that conversion's postcondition).
-    ox = fwd_x(qx, qy, qz, lx, ly, lz)
-    oy = fwd_y(qx, qy, qz, lx, ly, lz)
-    oz = fwd_z(qx, qy, qz, lx, ly, lz)
-    r0 = itrs_to_observed(0, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    r1 = itrs_to_observed(1, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    r2 = itrs_to_observed(2, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    Assert(r0 == ox)
-    Assert(r1 == oy)
-    Assert(r2 == oz)
-    # RETURN LEG. The transpose-action for that same site undoes the
-    # forward-action, recovering the re-referred position and hence the input.
-    orthogonality(qx, qy, qz, lx, ly, lz)
-    wx = bwd_x(ox, oy, oz, lx, ly, lz)
-    wy = bwd_y(ox, oy, oz, lx, ly, lz)
-    wz = bwd_z(ox, oy, oz, lx, ly, lz)
-    Assert(wx == vx)
-    Assert(wy == vy)
-    Assert(wz == vz)
-    # The return leg refers between the same anchoring as well, so it introduces
-    # no offset either.
-    same_frame_noop(wx, wy, wz, lx, ly, lz, e)
-    Assert(rebased_x(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vx)
-    Assert(rebased_y(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vy)
-    Assert(rebased_z(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vz)
-    return observed_to_itrs(comp, ox, oy, oz, lx, ly, lz, e, lx, ly, lz, e)
+
+    if comp == 0:
+        return vx
+    if comp == 1:
+        return vy
+    return vz
     # impl-end
 
 
@@ -509,12 +484,16 @@
         rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt), etgt)))
     # post-conditions-end
     # impl-start
-    # Refer the position to the OUTPUT frame's own anchoring (site T, epoch
-    # etgt), then rotate the re-referred position with the Earth-orientation
-    # rotation for that same epoch etgt.
-    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+    # Refer the position to ONE CONSTANT SITE -- the centre of the Earth, site
+    # (0, 0, 0) -- at the output frame's epoch etgt, rather than to the OUTPUT
+    # frame's own site T, and then rotate at that epoch. Whenever the output
+    # frame's site is not the centre of the Earth this leaves the position
+    # referred somewhere other than where the output frame asks for, so the result
+    # is not the rotation of the position referred to the output frame's own
+    # anchoring, and cannot satisfy the postcondition.
+    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, 0, 0, 0, etgt)
+    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, 0, 0, 0, etgt)
+    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, 0, 0, 0, etgt)
     if comp == 0:
         return prot_x(wx, wy, wz, etgt)
     if comp == 1:
@@ -561,16 +540,20 @@
     # post-conditions-end
     # impl-start
     # Rotate with the transpose of the Earth-orientation rotation for the INPUT
-    # frame's epoch esrc, then refer the rotated position from the input frame's
-    # own anchoring to the output frame's anchoring.
+    # frame's epoch esrc, then refer the rotated position as if it were held at
+    # ONE CONSTANT SITE -- the centre of the Earth, site (0, 0, 0) -- rather than
+    # at the input frame's OWN site L. Whenever the input frame's site is not the
+    # centre of the Earth this refers the position from somewhere other than where
+    # it is actually held, so the result is not the rotated position referred from
+    # the input frame's own anchoring, and cannot satisfy the postcondition.
     wx = prot_inv_x(ox, oy, oz, esrc)
     wy = prot_inv_y(ox, oy, oz, esrc)
     wz = prot_inv_z(ox, oy, oz, esrc)
     if comp == 0:
-        return wx + offset_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+        return wx + offset_x(wx, wy, wz, 0, 0, 0, esrc, tx, ty, tz, etgt)
     if comp == 1:
-        return wy + offset_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
-    return wz + offset_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
+        return wy + offset_y(wx, wy, wz, 0, 0, 0, esrc, tx, ty, tz, etgt)
+    return wz + offset_z(wx, wy, wz, 0, 0, 0, esrc, tx, ty, tz, etgt)
     # impl-end
 
 
@@ -598,42 +581,10 @@
     Ensures(Implies(comp == 2, Result() == vz))
     # post-conditions-end
     # impl-start
-    # OUTBOUND LEG. Both frames carry the same anchoring, so referring between
-    # them introduces no offset and the re-referred position is the position
-    # itself.
-    same_frame_noop(vx, vy, vz, lx, ly, lz, e)
-    qx = rebased_x(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    qy = rebased_y(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    qz = rebased_z(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    Assert(qx == vx)
-    Assert(qy == vy)
-    Assert(qz == vz)
-    # The Earth-rotating components are the rotation, at the shared epoch, of
-    # that re-referred position (each equals the corresponding forward-conversion
-    # output by that conversion's postcondition).
-    ox = prot_x(qx, qy, qz, e)
-    oy = prot_y(qx, qy, qz, e)
-    oz = prot_z(qx, qy, qz, e)
-    r0 = equ_to_rot(0, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    r1 = equ_to_rot(1, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    r2 = equ_to_rot(2, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
-    Assert(r0 == ox)
-    Assert(r1 == oy)
-    Assert(r2 == oz)
-    # RETURN LEG. The inverse rotation at that same epoch undoes the forward
-    # rotation, recovering the re-referred position and hence the input.
-    prot_orthogonality(qx, qy, qz, e)
-    wx = prot_inv_x(ox, oy, oz, e)
-    wy = prot_inv_y(ox, oy, oz, e)
-    wz = prot_inv_z(ox, oy, oz, e)
-    Assert(wx == vx)
-    Assert(wy == vy)
-    Assert(wz == vz)
-    # The return leg refers between the same anchoring as well, so it introduces
-    # no offset either.
-    same_frame_noop(wx, wy, wz, lx, ly, lz, e)
-    Assert(rebased_x(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vx)
-    Assert(rebased_y(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vy)
-    Assert(rebased_z(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vz)
-    return rot_to_equ(comp, ox, oy, oz, lx, ly, lz, e, lx, ly, lz, e)
+
+    if comp == 0:
+        return vx
+    if comp == 1:
+        return vy
+    return vz
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for astropy__astropy-13398.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Two pairs of DIRECT conversions are specified. Every frame involved is
  ANCHORED: it carries its own observing site and its own epoch, and nothing
  makes the anchoring of the frame a position is held in agree with the anchoring
  of the frame it is wanted in. So each conversion is TWO steps — a RE-REFERENCING
  step that moves the position from the anchoring it is held in to the anchoring
  it is wanted in, and a purely geometric ROTATION.

  FIRST PAIR: an Earth-fixed orientation <-> an observer-centred orientation.
  The rotation here is a constant orthogonal orientation matrix determined by the
  observing site of the OBSERVER-CENTRED frame — the frame that defines the
  observer-centred orientation, whichever end of the conversion it sits at.

  Earth-fixed (site L, epoch e_src) -> observer-centred (site T, epoch e_tgt):
    * FIRST refer the given position to the same-kind Earth-fixed frame anchored
      at the OUTPUT (observer-centred) frame's own site T and epoch e_tgt;
    * THEN apply the orientation matrix FOR THAT OUTPUT frame's own site T to the
      re-referred position.

  observer-centred (site L, epoch e_src) -> Earth-fixed (site T, epoch e_tgt):
    * FIRST apply the TRANSPOSE of the orientation matrix FOR THE INPUT
      (observer-centred) frame's own site L to the given position;
    * THEN refer the rotated position from the input frame's own anchoring
      (site L, epoch e_src) to the output frame's anchoring (site T, epoch
      e_tgt).

  SECOND PAIR: an intermediate Earth-equatorial orientation <-> an Earth-rotating
  orientation. The rotation here is the Earth-orientation rotation, whose value
  depends on an EPOCH.

  Earth-equatorial (site L, epoch e_src) -> Earth-rotating (site T, epoch e_tgt):
    * FIRST refer the given position to the same-kind Earth-equatorial frame
      anchored at the OUTPUT frame's own site T and epoch e_tgt;
    * THEN apply the Earth-orientation rotation FOR THE OUTPUT frame's epoch
      e_tgt to that re-referred position.

  Earth-rotating (site L, epoch e_src) -> Earth-equatorial (site T, epoch e_tgt):
    * FIRST apply the TRANSPOSE of the Earth-orientation rotation FOR THE INPUT
      frame's epoch e_src to the given position;
    * THEN refer the rotated position from the input frame's own anchoring
      (site L, epoch e_src) to the output frame's anchoring (site T, epoch
      e_tgt).

  The anchoring handed to the re-referencing step is the observable the issue is
  about: the position must be referred to the OUTPUT frame's OWN site and epoch,
  taken from the frame the caller asked for, and referred FROM the anchoring the
  input actually carries. Any other choice — a constant site independent of the
  frames, the endpoints interchanged, or omitting the step so the position is
  rotated as it stands — is a different observable behaviour. The same holds of
  the site the orientation matrix is built from, and of the epoch the
  Earth-orientation rotation is taken at: each conversion reads it off ONE named
  end of the conversion, and the two directions read opposite ends.

  When the two frames of a conversion agree in both site and epoch the
  re-referencing step introduces nothing, and only then is that conversion the
  bare rotation. In that same-anchoring case each pair is an EXACT round-trip
  identity — converting a position out and back returns it componentwise —
  precisely because each rotation is orthogonal, so its transpose undoes it. That
  same-anchoring round trip is the guarantee the issue demands. A conversion that
  instead reaches the far orientation by an INDIRECT route — one that does not
  apply the orthogonal rotation to the re-referred position, but introduces a
  further viewpoint-dependent directional shift along the way — does NOT
  reproduce the direct rotation and so does NOT round-trip exactly. When the
  anchorings differ neither pair composes to the identity — which is what makes
  the re-referencing step, and the site and epoch it is given, observable rather
  than decorative.

The position components, the site coordinates and the epoch are modelled as
exact integers (the round-trip identity is the exact algebraic cancellation that
the comparison tolerances absorb; the behaviour is precision-independent — see
refinement.md / mapping.md). The orthogonal rotation matrices and their actions
are unchanged callees (the rotation-matrix machinery and the Cartesian
transform); their forward/backward action is axiomatised, the only property the
proof needs being that the transpose-action inverts the forward action at one and
the same site (respectively at one and the same epoch). The re-referencing step
is an unchanged callee too; the only property the proof needs is that referring a
position between two frames of identical anchoring introduces no offset.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
@Pure
@ContractOnly
def fwd_x(x: int, y: int, z: int, sx: int, sy: int, sz: int) -> int:
    """First component of the constant orthogonal orientation matrix M(S) FOR THE
    SITE S = (sx, sy, sz) applied to the vector (x, y, z). The matrix is built
    from the site's own geodetic coordinates, so M(S) and M(S') are unrelated for
    S != S'. Unchanged callee (the rotation-matrix machinery via the Cartesian
    transform); provenance + executable soundness: mapping.md /
    axiom_check.py."""
    Ensures(True)

@Pure
@ContractOnly
def fwd_y(x: int, y: int, z: int, sx: int, sy: int, sz: int) -> int:
    """Second component of M(S) applied to (x, y, z)."""
    Ensures(True)

@Pure
@ContractOnly
def fwd_z(x: int, y: int, z: int, sx: int, sy: int, sz: int) -> int:
    """Third component of M(S) applied to (x, y, z)."""
    Ensures(True)

@Pure
@ContractOnly
def bwd_x(x: int, y: int, z: int, sx: int, sy: int, sz: int) -> int:
    """First component of the TRANSPOSE of M(S) applied to (x, y, z) (the
    inverse rotation for the site S). Unchanged callee."""
    Ensures(True)

@Pure
@ContractOnly
def bwd_y(x: int, y: int, z: int, sx: int, sy: int, sz: int) -> int:
    """Second component of the transpose of M(S) applied to (x, y, z)."""
    Ensures(True)

@Pure
@ContractOnly
def bwd_z(x: int, y: int, z: int, sx: int, sy: int, sz: int) -> int:
    """Third component of the transpose of M(S) applied to (x, y, z)."""
    Ensures(True)

@ContractOnly
def orthogonality(x: int, y: int, z: int, sx: int, sy: int, sz: int) -> None:
    """The single fact about the unchanged orthogonal orientation matrix the
    round-trip proof consumes: at ONE AND THE SAME site S = (sx, sy, sz),
    applying the transpose-action to the forward-action of any vector returns
    that vector componentwise (the transpose of an orthogonal matrix is its
    inverse). Nothing is claimed across two different sites. Provenance +
    executable soundness: mapping.md / axiom_check.py."""
    Requires(MustTerminate(2))
    Ensures(bwd_x(fwd_x(x, y, z, sx, sy, sz), fwd_y(x, y, z, sx, sy, sz),
                  fwd_z(x, y, z, sx, sy, sz), sx, sy, sz) == x)
    Ensures(bwd_y(fwd_x(x, y, z, sx, sy, sz), fwd_y(x, y, z, sx, sy, sz),
                  fwd_z(x, y, z, sx, sy, sz), sx, sy, sz) == y)
    Ensures(bwd_z(fwd_x(x, y, z, sx, sy, sz), fwd_y(x, y, z, sx, sy, sz),
                  fwd_z(x, y, z, sx, sy, sz), sx, sy, sz) == z)

@Pure
@ContractOnly
def prot_x(x: int, y: int, z: int, e: int) -> int:
    """First component of the Earth-orientation rotation P(e) FOR THE EPOCH e
    applied to the vector (x, y, z). This rotation relates an intermediate
    Earth-equatorial orientation to an Earth-rotating orientation; its value
    depends on the epoch e, and P(e) and P(e') are unrelated for e != e'. It is a
    distinct unchanged callee (the epoch-dependent Earth-orientation matrix
    builder and the Cartesian transform). Provenance + executable soundness:
    mapping.md / axiom_check.py."""
    Ensures(True)

@Pure
@ContractOnly
def prot_y(x: int, y: int, z: int, e: int) -> int:
    """Second component of the rotation P(e) applied to (x, y, z)."""
    Ensures(True)

@Pure
@ContractOnly
def prot_z(x: int, y: int, z: int, e: int) -> int:
    """Third component of the rotation P(e) applied to (x, y, z)."""
    Ensures(True)

@Pure
@ContractOnly
def prot_inv_x(x: int, y: int, z: int, e: int) -> int:
    """First component of the TRANSPOSE of the rotation P(e) applied to
    (x, y, z) (the inverse rotation at the epoch e). Unchanged callee."""
    Ensures(True)

@Pure
@ContractOnly
def prot_inv_y(x: int, y: int, z: int, e: int) -> int:
    """Second component of the transpose of P(e) applied to (x, y, z)."""
    Ensures(True)

@Pure
@ContractOnly
def prot_inv_z(x: int, y: int, z: int, e: int) -> int:
    """Third component of the transpose of P(e) applied to (x, y, z)."""
    Ensures(True)

@ContractOnly
def prot_orthogonality(x: int, y: int, z: int, e: int) -> None:
    """The single fact about the unchanged Earth-orientation rotation P(e) the
    round-trip proof consumes: at ONE AND THE SAME epoch e, its transpose-action
    inverts its forward-action componentwise (P(e) is orthogonal, so P(e)^T is
    its inverse). Nothing is claimed across two different epochs. Provenance +
    executable soundness: mapping.md / axiom_check.py."""
    Requires(MustTerminate(6))
    Ensures(prot_inv_x(prot_x(x, y, z, e), prot_y(x, y, z, e),
                       prot_z(x, y, z, e), e) == x)
    Ensures(prot_inv_y(prot_x(x, y, z, e), prot_y(x, y, z, e),
                       prot_z(x, y, z, e), e) == y)
    Ensures(prot_inv_z(prot_x(x, y, z, e), prot_y(x, y, z, e),
                       prot_z(x, y, z, e), e) == z)

@Pure
@ContractOnly
def offset_x(vx: int, vy: int, vz: int,
             lx: int, ly: int, lz: int, esrc: int,
             tx: int, ty: int, tz: int, etgt: int) -> int:
    """First component of the offset that referring the position (vx, vy, vz)
    introduces when that position, held in a frame anchored at site
    L = (lx, ly, lz) at epoch esrc, is referred to the SAME-KIND frame anchored
    at site T = (tx, ty, tz) at epoch etgt. The route taken ties the position to
    the Solar-System barycentre, so the offset is the
    geocentric-versus-topocentric aberration difference together with the change
    of epoch; it therefore depends on the position itself as well as on both
    anchorings. This is an unchanged callee (the re-referencing transform between
    two same-kind frames). Provenance + executable soundness: mapping.md /
    axiom_check.py."""
    Ensures(True)

@Pure
@ContractOnly
def offset_y(vx: int, vy: int, vz: int,
             lx: int, ly: int, lz: int, esrc: int,
             tx: int, ty: int, tz: int, etgt: int) -> int:
    """Second component of the re-referencing offset on (vx, vy, vz) from
    (site L, epoch esrc) to (site T, epoch etgt)."""
    Ensures(True)

@Pure
@ContractOnly
def offset_z(vx: int, vy: int, vz: int,
             lx: int, ly: int, lz: int, esrc: int,
             tx: int, ty: int, tz: int, etgt: int) -> int:
    """Third component of the re-referencing offset on (vx, vy, vz) from
    (site L, epoch esrc) to (site T, epoch etgt)."""
    Ensures(True)

@ContractOnly
def same_frame_noop(vx: int, vy: int, vz: int,
                    lx: int, ly: int, lz: int, e: int) -> None:
    """The single fact about the unchanged re-referencing transform the proof
    consumes: referring a position between two frames of IDENTICAL anchoring —
    the same site L and the same epoch e — introduces no offset. This is the
    weakest fact sufficient for the round-trip proof; the offset is otherwise
    uninterpreted, so nothing follows about referring to any other site or any
    other epoch. Provenance + executable soundness: mapping.md /
    axiom_check.py."""
    Requires(MustTerminate(10))
    Ensures(offset_x(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e) == 0)
    Ensures(offset_y(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e) == 0)
    Ensures(offset_z(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e) == 0)
# axioms-end

# pure-start
@Pure
def rebased_x(vx: int, vy: int, vz: int,
              lx: int, ly: int, lz: int, esrc: int,
              tx: int, ty: int, tz: int, etgt: int) -> int:
    """First component of the position (vx, vy, vz) once it has been REFERRED
    from the frame anchored at (site L = (lx, ly, lz), epoch esrc) to the
    same-kind frame anchored at (site T = (tx, ty, tz), epoch etgt): the given
    component plus the offset that re-referencing introduces."""
    return vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)

@Pure
def rebased_y(vx: int, vy: int, vz: int,
              lx: int, ly: int, lz: int, esrc: int,
              tx: int, ty: int, tz: int, etgt: int) -> int:
    """Second component of the re-referred position."""
    return vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)

@Pure
def rebased_z(vx: int, vy: int, vz: int,
              lx: int, ly: int, lz: int, esrc: int,
              tx: int, ty: int, tz: int, etgt: int) -> int:
    """Third component of the re-referred position."""
    return vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
# pure-end

def itrs_to_observed(comp: int,
                     vx: int, vy: int, vz: int,
                     lx: int, ly: int, lz: int, esrc: int,
                     tx: int, ty: int, tz: int, etgt: int) -> int:
    # pre-conditions-start
    # `comp` selects which output component (0, 1 or 2) to return. (vx, vy, vz)
    # is an Earth-fixed position held in a frame anchored at the site
    # L = (lx, ly, lz) at the epoch esrc; the observer-centred output is wanted
    # in the frame anchored at the site T = (tx, ty, tz) at the epoch etgt. Both
    # anchorings are free: nothing requires them to agree.
    Requires(comp == 0 or comp == 1 or comp == 2)
    Requires(MustTerminate(14))
    # pre-conditions-end
    # post-conditions-start
    # The given position is FIRST referred from the anchoring it is held in
    # (site L, epoch esrc) to the OUTPUT (observer-centred) frame's OWN anchoring
    # (site T, epoch etgt) — so the site and the epoch handed to the
    # re-referencing step are exactly the output frame's, and the position it is
    # applied to is exactly the given one. The orthogonal orientation matrix FOR
    # THAT OUTPUT frame's OWN site T is THEN applied to the re-referred position.
    # Each clause names the re-referencing endpoints and the site the matrix is
    # built from, so omitting the re-referencing step, referring to any other site
    # or epoch, reaching the observer-centred orientation by an indirect route, or
    # building the matrix from any other site, is a different value.
    Ensures(Implies(comp == 0, Result() == fwd_x(
        rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        tx, ty, tz)))
    Ensures(Implies(comp == 1, Result() == fwd_y(
        rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        tx, ty, tz)))
    Ensures(Implies(comp == 2, Result() == fwd_z(
        rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        tx, ty, tz)))
    # post-conditions-end
    # impl-start
    # Refer the position to the OUTPUT frame's own anchoring (site T, epoch
    # etgt), then rotate the re-referred position with the orientation matrix
    # built from that same output frame's own site T.
    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 0:
        return fwd_x(wx, wy, wz, tx, ty, tz)
    if comp == 1:
        return fwd_y(wx, wy, wz, tx, ty, tz)
    return fwd_z(wx, wy, wz, tx, ty, tz)
    # impl-end

def observed_to_itrs(comp: int,
                     ox: int, oy: int, oz: int,
                     lx: int, ly: int, lz: int, esrc: int,
                     tx: int, ty: int, tz: int, etgt: int) -> int:
    # pre-conditions-start
    # `comp` selects which output component (0, 1 or 2) to return. (ox, oy, oz)
    # is an observer-centred position held in a frame anchored at the site
    # L = (lx, ly, lz) at the epoch esrc; the Earth-fixed output is wanted in the
    # frame anchored at the site T = (tx, ty, tz) at the epoch etgt. Both
    # anchorings are free: nothing requires them to agree.
    Requires(comp == 0 or comp == 1 or comp == 2)
    Requires(MustTerminate(18))
    # pre-conditions-end
    # post-conditions-start
    # The TRANSPOSE of the orientation matrix FOR THE INPUT (observer-centred)
    # frame's OWN site L is applied to the given position FIRST; the rotated
    # position is THEN referred from the input frame's OWN anchoring (site L,
    # epoch esrc) to the output frame's anchoring (site T, epoch etgt). So the
    # matrix is built from the input frame's own site, the re-referencing step's
    # source anchoring is the input frame's own, its target anchoring is the
    # output frame's own, and the position it acts on is the ROTATED one — the
    # mirror of the forward conversion, in which the re-referencing precedes the
    # rotation and the matrix is built from the OUTPUT frame's site.
    Ensures(Implies(comp == 0, Result() == rebased_x(
        bwd_x(ox, oy, oz, lx, ly, lz), bwd_y(ox, oy, oz, lx, ly, lz),
        bwd_z(ox, oy, oz, lx, ly, lz),
        lx, ly, lz, esrc, tx, ty, tz, etgt)))
    Ensures(Implies(comp == 1, Result() == rebased_y(
        bwd_x(ox, oy, oz, lx, ly, lz), bwd_y(ox, oy, oz, lx, ly, lz),
        bwd_z(ox, oy, oz, lx, ly, lz),
        lx, ly, lz, esrc, tx, ty, tz, etgt)))
    Ensures(Implies(comp == 2, Result() == rebased_z(
        bwd_x(ox, oy, oz, lx, ly, lz), bwd_y(ox, oy, oz, lx, ly, lz),
        bwd_z(ox, oy, oz, lx, ly, lz),
        lx, ly, lz, esrc, tx, ty, tz, etgt)))
    # post-conditions-end
    # impl-start
    # Rotate with the transpose of the orientation matrix built from the INPUT
    # frame's own site L, then refer the rotated position from the input frame's
    # own anchoring to the output frame's anchoring.
    wx = bwd_x(ox, oy, oz, lx, ly, lz)
    wy = bwd_y(ox, oy, oz, lx, ly, lz)
    wz = bwd_z(ox, oy, oz, lx, ly, lz)
    if comp == 0:
        return wx + offset_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 1:
        return wy + offset_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    return wz + offset_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    # impl-end

def observed_roundtrip(comp: int,
                       vx: int, vy: int, vz: int,
                       lx: int, ly: int, lz: int, e: int) -> int:
    # pre-conditions-start
    # `comp` selects which component (0, 1 or 2) of the round-tripped position
    # to return. An Earth-fixed position (vx, vy, vz) held in a frame anchored at
    # the site L = (lx, ly, lz) at the epoch e, taken to the observer-centred
    # orientation in the frame anchored at the SAME site and the SAME epoch, and
    # back.
    Requires(comp == 0 or comp == 1 or comp == 2)
    Requires(MustTerminate(22))
    # pre-conditions-end
    # post-conditions-start
    # Converting an Earth-fixed position to the observer-centred orientation at
    # (site L, epoch e) and back to the Earth-fixed orientation at (site L, epoch
    # e) returns the original position exactly. This is the round-trip identity
    # the issue demands of the direct conversion pair; it holds because the two
    # frames share their anchoring, so the re-referencing step contributes nothing
    # on either leg, and because the orientation matrix for one site is
    # orthogonal.
    Ensures(Implies(comp == 0, Result() == vx))
    Ensures(Implies(comp == 1, Result() == vy))
    Ensures(Implies(comp == 2, Result() == vz))
    # post-conditions-end
    # impl-start
    # OUTBOUND LEG. Both frames carry the same anchoring, so referring between
    # them introduces no offset and the re-referred position is the position
    # itself.
    same_frame_noop(vx, vy, vz, lx, ly, lz, e)
    qx = rebased_x(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    qy = rebased_y(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    qz = rebased_z(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    Assert(qx == vx)
    Assert(qy == vy)
    Assert(qz == vz)
    # The observer-centred components are the orientation matrix for the shared
    # site applied to that re-referred position (each equals the corresponding
    # forward-conversion output by that conversion's postcondition).
    ox = fwd_x(qx, qy, qz, lx, ly, lz)
    oy = fwd_y(qx, qy, qz, lx, ly, lz)
    oz = fwd_z(qx, qy, qz, lx, ly, lz)
    r0 = itrs_to_observed(0, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    r1 = itrs_to_observed(1, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    r2 = itrs_to_observed(2, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    Assert(r0 == ox)
    Assert(r1 == oy)
    Assert(r2 == oz)
    # RETURN LEG. The transpose-action for that same site undoes the
    # forward-action, recovering the re-referred position and hence the input.
    orthogonality(qx, qy, qz, lx, ly, lz)
    wx = bwd_x(ox, oy, oz, lx, ly, lz)
    wy = bwd_y(ox, oy, oz, lx, ly, lz)
    wz = bwd_z(ox, oy, oz, lx, ly, lz)
    Assert(wx == vx)
    Assert(wy == vy)
    Assert(wz == vz)
    # The return leg refers between the same anchoring as well, so it introduces
    # no offset either.
    same_frame_noop(wx, wy, wz, lx, ly, lz, e)
    Assert(rebased_x(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vx)
    Assert(rebased_y(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vy)
    Assert(rebased_z(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vz)
    return observed_to_itrs(comp, ox, oy, oz, lx, ly, lz, e, lx, ly, lz, e)
    # impl-end

def equ_to_rot(comp: int,
               vx: int, vy: int, vz: int,
               lx: int, ly: int, lz: int, esrc: int,
               tx: int, ty: int, tz: int, etgt: int) -> int:
    # pre-conditions-start
    # `comp` selects which output component (0, 1 or 2) to return. (vx, vy, vz)
    # is an Earth-equatorial position held in a frame anchored at the site
    # L = (lx, ly, lz) at the epoch esrc; the Earth-rotating output is wanted in
    # the frame anchored at the site T = (tx, ty, tz) at the epoch etgt. Both
    # anchorings are free: nothing requires them to agree.
    Requires(comp == 0 or comp == 1 or comp == 2)
    Requires(MustTerminate(26))
    # pre-conditions-end
    # post-conditions-start
    # The given position is FIRST referred from the anchoring it is held in
    # (site L, epoch esrc) to the OUTPUT frame's OWN anchoring (site T, epoch
    # etgt) — so the site and the epoch handed to the re-referencing step are
    # exactly the output frame's, and the position it is applied to is exactly
    # the given one. The Earth-orientation rotation FOR THE OUTPUT frame's epoch
    # etgt is THEN applied to that re-referred position. Each clause names the
    # re-referencing endpoints and the rotation's epoch, so omitting the
    # re-referencing step, referring to any other site or epoch, or rotating at
    # any other epoch, is a different value.
    Ensures(Implies(comp == 0, Result() == prot_x(
        rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt), etgt)))
    Ensures(Implies(comp == 1, Result() == prot_y(
        rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt), etgt)))
    Ensures(Implies(comp == 2, Result() == prot_z(
        rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt), etgt)))
    # post-conditions-end
    # impl-start
    # Refer the position to the OUTPUT frame's own anchoring (site T, epoch
    # etgt), then rotate the re-referred position with the Earth-orientation
    # rotation for that same epoch etgt.
    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 0:
        return prot_x(wx, wy, wz, etgt)
    if comp == 1:
        return prot_y(wx, wy, wz, etgt)
    return prot_z(wx, wy, wz, etgt)
    # impl-end

def rot_to_equ(comp: int,
               ox: int, oy: int, oz: int,
               lx: int, ly: int, lz: int, esrc: int,
               tx: int, ty: int, tz: int, etgt: int) -> int:
    # pre-conditions-start
    # `comp` selects which output component (0, 1 or 2) to return. (ox, oy, oz)
    # is an Earth-rotating position held in a frame anchored at the site
    # L = (lx, ly, lz) at the epoch esrc; the Earth-equatorial output is wanted
    # in the frame anchored at the site T = (tx, ty, tz) at the epoch etgt. Both
    # anchorings are free: nothing requires them to agree.
    Requires(comp == 0 or comp == 1 or comp == 2)
    Requires(MustTerminate(30))
    # pre-conditions-end
    # post-conditions-start
    # The TRANSPOSE of the Earth-orientation rotation FOR THE INPUT frame's
    # epoch esrc is applied to the given position FIRST; the rotated position is
    # THEN referred from the input frame's OWN anchoring (site L, epoch esrc) to
    # the output frame's anchoring (site T, epoch etgt). So the re-referencing
    # step's source anchoring is the input frame's own, its target anchoring is
    # the output frame's own, the position it acts on is the ROTATED one, and the
    # rotation is taken at the INPUT epoch — the mirror of the forward
    # conversion, in which the re-referencing precedes the rotation and the
    # rotation is taken at the OUTPUT epoch.
    Ensures(Implies(comp == 0, Result() == rebased_x(
        prot_inv_x(ox, oy, oz, esrc), prot_inv_y(ox, oy, oz, esrc),
        prot_inv_z(ox, oy, oz, esrc),
        lx, ly, lz, esrc, tx, ty, tz, etgt)))
    Ensures(Implies(comp == 1, Result() == rebased_y(
        prot_inv_x(ox, oy, oz, esrc), prot_inv_y(ox, oy, oz, esrc),
        prot_inv_z(ox, oy, oz, esrc),
        lx, ly, lz, esrc, tx, ty, tz, etgt)))
    Ensures(Implies(comp == 2, Result() == rebased_z(
        prot_inv_x(ox, oy, oz, esrc), prot_inv_y(ox, oy, oz, esrc),
        prot_inv_z(ox, oy, oz, esrc),
        lx, ly, lz, esrc, tx, ty, tz, etgt)))
    # post-conditions-end
    # impl-start
    # Rotate with the transpose of the Earth-orientation rotation for the INPUT
    # frame's epoch esrc, then refer the rotated position from the input frame's
    # own anchoring to the output frame's anchoring.
    wx = prot_inv_x(ox, oy, oz, esrc)
    wy = prot_inv_y(ox, oy, oz, esrc)
    wz = prot_inv_z(ox, oy, oz, esrc)
    if comp == 0:
        return wx + offset_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 1:
        return wy + offset_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    return wz + offset_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    # impl-end

def equ_rot_roundtrip(comp: int,
                      vx: int, vy: int, vz: int,
                      lx: int, ly: int, lz: int, e: int) -> int:
    # pre-conditions-start
    # `comp` selects which component (0, 1 or 2) of the round-tripped position to
    # return. An Earth-equatorial position (vx, vy, vz) held in a frame anchored
    # at the site L = (lx, ly, lz) at the epoch e, taken to the Earth-rotating
    # orientation in the frame anchored at the SAME site and the SAME epoch, and
    # back.
    Requires(comp == 0 or comp == 1 or comp == 2)
    Requires(MustTerminate(34))
    # pre-conditions-end
    # post-conditions-start
    # Converting the position to the Earth-rotating orientation at (site L, epoch
    # e) and back to the Earth-equatorial orientation at (site L, epoch e)
    # returns the original position exactly. This is the round-trip identity for
    # the second conversion pair; it holds because the two frames share their
    # anchoring, so the re-referencing step contributes nothing on either leg,
    # and because the Earth-orientation rotation at one epoch is orthogonal.
    Ensures(Implies(comp == 0, Result() == vx))
    Ensures(Implies(comp == 1, Result() == vy))
    Ensures(Implies(comp == 2, Result() == vz))
    # post-conditions-end
    # impl-start
    # OUTBOUND LEG. Both frames carry the same anchoring, so referring between
    # them introduces no offset and the re-referred position is the position
    # itself.
    same_frame_noop(vx, vy, vz, lx, ly, lz, e)
    qx = rebased_x(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    qy = rebased_y(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    qz = rebased_z(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    Assert(qx == vx)
    Assert(qy == vy)
    Assert(qz == vz)
    # The Earth-rotating components are the rotation, at the shared epoch, of
    # that re-referred position (each equals the corresponding forward-conversion
    # output by that conversion's postcondition).
    ox = prot_x(qx, qy, qz, e)
    oy = prot_y(qx, qy, qz, e)
    oz = prot_z(qx, qy, qz, e)
    r0 = equ_to_rot(0, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    r1 = equ_to_rot(1, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    r2 = equ_to_rot(2, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    Assert(r0 == ox)
    Assert(r1 == oy)
    Assert(r2 == oz)
    # RETURN LEG. The inverse rotation at that same epoch undoes the forward
    # rotation, recovering the re-referred position and hence the input.
    prot_orthogonality(qx, qy, qz, e)
    wx = prot_inv_x(ox, oy, oz, e)
    wy = prot_inv_y(ox, oy, oz, e)
    wz = prot_inv_z(ox, oy, oz, e)
    Assert(wx == vx)
    Assert(wy == vy)
    Assert(wz == vz)
    # The return leg refers between the same anchoring as well, so it introduces
    # no offset either.
    same_frame_noop(wx, wy, wz, lx, ly, lz, e)
    Assert(rebased_x(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vx)
    Assert(rebased_y(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vy)
    Assert(rebased_z(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vz)
    return rot_to_equ(comp, ox, oy, oz, lx, ly, lz, e, lx, ly, lz, e)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for astropy__astropy-13398 / nagini. Frozen model.py sha256 0909cc14e7e0e16ee8475a566f6822e80ebbd32c991dfcdd8793dc9470f7f633, re-confirmed UNCHANGED after all runs. Scratch dir (fresh, exclusive; no other /tmp path used).

**RESULT:** 15 attacks, all SAME-spec, all ADMISSIBLE, all REJECTED. ZERO CANDIDATEs => no resolve run was owed or performed.

**TOOLCHAIN:** every attack below was verified with the pinned Nagini verifier, and every one was run to a verdict.

**BUILD METHOD:** generators gen.py / gen2.py / gen3.py copy the bundle's model.py and replace ONLY the body of a named function's `# impl-start`/`# impl-end` region. Every emitted file is gated BEFORE being written on: same_spec(BASE,text,LANG) True; spec_view(text)==spec_view(BASE) byte-for-byte; unsound_evasions(BASE,text,LANG)==[] (no new @ContractOnly / assumption tokens -- each attack must ESTABLISH, not assume); exactly one impl region located per target function, asserted not to have leaked past the next `def` (no silent anchor drift). Independently re-confirmed afterwards: `adversary same-spec` returned SAME for all 15, and a direct re-run of same_spec + unsound_evasions gave same_spec=True / evasions=[] for all 15.

### EXACT COMMANDS (from the repo root, per attack n = 1..15):
  python -m swebench_unified.adversary weakness  nagini astropy__astropy-13398 atk_<n>.py
  python -m swebench_unified.adversary same-spec nagini astropy__astropy-13398 atk_<n>.py
  bash scripts/nagini_verify.sh <file>.py    # controls + per-attack failing obligation
Raw transcripts kept beside each file as atk_<n>.weak.txt and atk_<n>.verify.txt; runners run_weak.sh / run_verify.sh.

PER-ATTACK -- every result was "NOT-A-COUNTEREXAMPLE: attack does not verify (verification failed)", exit=2, with the named failing obligation: atk_1  PREPATCH REPRODUCTION -- all four conversion impls lifted VERBATIM from the bundle's own model_prepatch.py (indirect fwd(bwd(v)) forward; un-referred backward; constant (0,0,0) site for the equatorial pair).

REJECTED. => prepatch bug reproduced. atk_2  *** A-LEG *** ORDER SWAP LAUNDERED THROUGH A LEGAL ORACLE + THE ONE-SITE AXIOM: observed_to_itrs calls itrs_to_observed (measure 14<18, legal) and instantiates `orthogonality` at the OUTPUT site T (one and the same site, a legal instance) to strip the fwd, making bwd(r,T) provably the RE-REFERENCED UNROTATED position -- gold's:141-145 shift applied BEFORE the:129/:137 transpose instead of after. REJECTED (observed_to_itrs). atk_3  TWO-HOP re-referencing on equ_to_rot: (L,esrc)->(T,esrc) then (T,esrc)->(T,etgt), both composite endpoints gold's, only the intermediate stop invented. Probes whether the spec licenses COMPOSING the unchanged re-referencing callee (it is not additive in the repo).

REJECTED (equ_to_rot). atk_4  ORDER SWAP on the equatorial backward: refer the GIVEN position (L,esrc)->(T,etgt) first, then transpose-rotate at esrc. Endpoints, rotation and epoch all gold's; only the ORDER differs. REJECTED (Postcondition of rot_to_equ,:549). atk_5  CONTROL-FLOW EFFECT on observed_to_itrs: gold's rotation and gold's two endpoints, but the offset SAMPLED AT THE UNROTATED position o instead of the rotated one. REJECTED (observed_to_itrs,:381) => gold's:145 position-dependence is live on this pair. atk_6  BOUNDARY / MIXED ANCHORING: equ_to_rot refers to the OUTPUT site T but at the INPUT epoch esrc, then rotates at etgt -- only ONE member of the target anchoring pair wrong.

REJECTED (equ_to_rot) => the site and epoch carriers are pinned independently. atk_7  PARTIAL DOMAIN, EPOCH-only guard: equ_to_rot is gold except when the EPOCHS agree, where the re-reference is dropped as if an epoch match alone discharged it while the SITES may still differ; `same_frame_noop` invoked at both legal instances to try to license it. REJECTED (equ_to_rot,:498). atk_8  *** A-LEG *** WRONG MATRIX SITE with gold's re-referencing INTACT: the matrix is built from the INPUT site L rather than the OUTPUT site T that gold's:112 reads, with `orthogonality` instantiated at BOTH sites (each legal) hoping the pair licenses a cross-site identification.

REJECTED (itrs_to_observed,:327) => the ONE-SITE scope holds against the OTHER ENDPOINT, not just against a constant. atk_9  *** A-LEG *** `same_frame_noop` SUBSTITUTED FOR GOLD'S REAL SHIFT: rot_to_equ's rotation is gold's but the offset is taken at the OUTPUT anchoring against ITSELF -- a legal, provably-ZERO instance -- so the return is the BARE rotation while the source still "performs a re-reference". REJECTED (rot_to_equ,:549) => a no-op instance cannot stand in for gold's:214/:217 (L,esrc)->(T,etgt) shift. atk_10 *** THE PRIOR PASS'S NAMED COUNTEREXAMPLE, re-encoded *** -- observed forward rotates the GIVEN triple with M(T), gold's:106-110 block DELETED, no anchoring consulted; `same_frame_noop` invoked at both legal instances.

Faithful patch on record as FAILING resolve (P2P 63/68, test_gcrs_altaz_bothroutes[testframe0..4]). REJECTED (Postcondition of itrs_to_observed). atk_11 PARTIAL DOMAIN, the exact test_gcrs_altaz_bothroutes shape (SITE-only guard): the observed forward re-references only when the SITES differ, so a site-equal / epoch-differing pair is treated as needing nothing. REJECTED (itrs_to_observed). atk_12 *** A-LEG *** CROSS-PAIR UNGROUNDED-ORACLE ECHO: rot_to_equ (measure 30) legally calls observed_roundtrip (measure 22) -- the OTHER pair's exact identity -- plus prot_orthogonality at two epochs and same_frame_noop, then returns the BARE transpose rotation with gold's:214/:217 dropped.

REJECTED (rot_to_equ,:549) => an identity proven for the observer-centred pair cannot be laundered into discharging the equatorial pair's shift. atk_13 *** MY PRINCIPAL FINDING *** COMBINATION: observed_roundtrip discharged TRIVIALLY (so it no longer witnesses the composition) AND the forward set to the historical resolve-breaker. Only itrs_to_observed's OWN postcondition can reject it. REJECTED (itrs_to_observed). atk_14 the same COMBINATION on the equatorial pair: trivial equ_rot_roundtrip AND the pre-patch constant-geocentre (0,0,0) re-reference gold replaces. REJECTED (equ_to_rot). atk_15 MAXIMAL: BOTH round trips trivial AND all FOUR conversions reverted verbatim to model_prepatch.py -- nothing but the four conversion postconditions left to reject it. REJECTED with ALL FOUR failing at once (itrs_to_observed, observed_to_itrs, equ_to_rot, rot_to_equ).

DISTINCTNESS (well past the >=5 floor and the required kind spread): prepatch reproduction (1, 15); partial-domain (7, 11, plus 13/14/15's round-trip discharge); boundary/argument (3, 6); control-flow-effect (2, 4, 5, 12); ungrounded-oracle echo (2, 8, 9, 12); dropped-step (10, 13, 14); order swap (2, 4). SEVEN are dedicated A-leg probes (2, 8, 9, 12 explicitly, plus 3/6/7 probing the offset's scope).

### Controls
pos_control.py       -- byte copy of the frozen model (sha256 identical): "Verification successful", 13.14s, exit=0. POSITIVE CONTROL. pos_reshape.py       -- genuine BEHAVIOUR-PRESERVING reshape (equatorial pair in the `rebased_*` spec spelling, reversed binding AND branch order): "Verification successful", 12.39s. So the spec pins BEHAVIOUR, not gold's token sequence. vac_control.py       -- VACUITY / axiom-consistency probe: all six consumed-axiom instances invoked legally, including overlapping/nested instantiations designed to make the axiom set collide if it can, then Assert(False).

"Verification failed" (exit=1, "Assert might fail") => the axiom set is CONSISTENT, so neither the positive verifications nor any of the 15 rejections is vacuous. probe_rt_trivial.py  -- ISOLATING control for my principal finding: both round trips discharged trivially, both conversions left GOLD. VERIFIES (9.45s). Together with atk_13/14/15 being REJECTED, this proves the trivial round-trip discharge removes a REDUNDANT WITNESS, not the obligation -- the two conversions remain pinned by their own postconditions. Not submitted as an attack: it refines to no repo change, so it can produce no failing patch.

### REFINEMENT.MD AUDIT (the A legs and the model<->patch correspondence):
  * Leg tags, enumerated mechanically from the tables: A1=R, A2=A-consumed, A3=A-consumed, B1=A-consumed, B2=A-consumed/I, C1=A-consumed, C2=I, C3=A-consumed, C4=A-consumed/I, C2a=R, C2b=A-consumed, C2c=A-consumed, C2d=A-consumed, C2e=A-consumed/I, C2f=A-consumed, C2g=I/A-consumed. All 16 legs are R / A-consumed / I. NO A-reference deep model and NO kind-3 step, consistent with meta.json deep_model_references == [].
  * Line citations verified against the REAL sources, not taken on trust. I extracted the gold itrs_observed_transforms.py from instance.json's patch and line-numbered it::106-110 is the forward re-reference to ITRS(obstime=observed_frame.obstime, location=observed_frame.location);:112 reads observed_frame.location.to_geodetic('WGS84');:115/:121 feed its lon/lat to itrs_to_altaz_mat / itrs_to_hadec_mat;:129 reads observed_coo.location;:137/:139 apply matrix_transpose(...);:141-145 build ITRS(crepr, obstime=observed_coo.obstime, location=observed_coo.location).transform_to(itrs_frame). Every cited line matches exactly. I also checked out base_commit 6500928dc0e57be8f06d1162eacc3ba5e2eff692 and line-numbered intermediate_rotation_transforms.py: cirs_to_itrs at:197-206 with location=EARTH_CENTER at:201 and pmat = cirs_to_itrs_mat(itrs_frame.obstime) at:204; itrs_to_cirs at:209-217 with pmat from itrs_coo.obstime at:212 and CIRS(newrepr, obstime=itrs_coo.obstime) (NO location=) at:214. Every §C2 citation matches, and patch.diff changes exactly those two arguments (plus the TETE mirror at:148-167). §0's provenance note is correct: the gold transform does NOT carry the issue draft's observer-position subtraction; that stays in the caller.
  * A-leg correspondence to the real callees HOLDS. fwd_*/bwd_* <-> CartesianRepresentation.transform of the rotation_matrix composite (itrs_to_altaz_mat / itrs_to_hadec_mat are products of a sign-flip and rotation_matrix factors, matrix_transpose is.swapaxes(-2,-1)), so M^T M = I: orthogonality is the WEAKEST sufficient fact and is SITE-scoped, claiming nothing cross-site (atk_8's cross-site identification is duly rejected). prot_*/prot_inv_* <-> cirs_to_itrs_mat / tete_to_itrs_mat (ERFA polar-motion / Earth-rotation / precession products, orthogonal), EPOCH-scoped. offset_* <-> the same-kind re-referencing transform: axiom_check.py's same_kind_offset drives it through the PUBLIC frame API (cls(rep, obstime=t_src, location=loc_src).transform_to(cls(obstime=t_tgt, location=loc_tgt)).cartesian - rep) so the REGISTERED transform actually executes, and it validates same_frame_noop (residual <= 1e-3 m) plus BOTH carrier CONTROLS (target site changed alone > 1.0 m; target epoch changed alone > 1.0 m) at BOTH instances mapping.md binds it to -- CIRS<->CIRS and ITRS<->ITRS (the (d2) block, on a witness produced by the real CIRS@(L,e)->ITRS@(L,e) transform). So neither carrier is decorative and the axiom provably does NOT extend past its identical-anchoring case -- exactly the scope atk_7 / atk_9 / atk_12 probe and fail to exceed.
  * Every carrier the A-legs claim is load-bearing has an independent REJECTED attack behind it: matrix site (atk_8), rotation epoch (atk_6 mixed, atk_12 cross-pair), both re-referencing endpoints (atk_10, atk_11, atk_3), step order (atk_2, atk_4), offset position-dependence (atk_5), exact scope of same_frame_noop (atk_7, atk_9, atk_12), and the conversions' independence from the round-trip witness (atk_13, atk_14, atk_15 + probe_rt_trivial).
  * §D's refraction scoping is correct and checked against the real F2P list (4 tests: test_itrs_topo_to_altaz_with_refraction, test_itrs_topo_to_hadec_with_refraction, test_cirs_itrs_topo, test_itrs_straight_overhead). Exact identity is asserted only on the no-pressure frames; the refraction path is checked against the pre-existing CIRS route within loose tolerance. P2P (68 tests) does contain test_gcrs_altaz_bothroutes[testframe0..4] -- the five tests the historical counterexample broke, which is precisely what atk_10 / atk_11 / atk_13 target and which the current spec rejects.

**ADVISORY VERDICT:** SOUND. 15 admissible same-spec attacks run (3x the floor), the prepatch bug reproduced and rejected on all four conversion postconditions, the prior pass's named counterexample and the site-only shape that historically broke P2P both rejected, the residual the prior pass named-but-never-tested (trivially dischargeable round trip) closed by machine evidence via the atk_13/14/15 combinations plus the probe_rt_trivial isolating control, two positive controls verify (including a non-trivial behaviour-preserving reshape), vacuity excluded by an Assert(False) probe that fails, and ZERO verifying wrong impls exist -- so no faithful patch could be materialized and no run_resolve was owed. I did not accept the prior SOUND on trust: I re-derived every leg tag, re-verified every line citation against base_commit and the patch, and attacked the one gap the prior reasoning left open.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE. All 15 same-spec, admissible wrong impls were REJECTED by the frozen spec (every one a genuine `Postcondition of <fn> might not hold`, exit=2 from `adversary weakness`). ZERO CANDIDATEs, so protocol step 2 (materialize the faithful refined patch and run run_resolve) had nothing to run: no verifying wrong impl exists on this spec, hence no patch was owed and none is submitted. The prior pass's named counterexample -- the observed forward rotating the GIVEN triple with M(T) with gold's :106-110 re-referencing block deleted, whose faithful patch is on record as FAILING resolve at P2P 63/68 on test_gcrs_altaz_bothroutes[testframe0..4] -- is re-encoded here as atk_10 and is REJECTED (Postcondition of itrs_to_observed), as is the site-only partial-domain shape that broke it (atk_11).

My PRINCIPAL INDEPENDENT FINDING is that I closed the one hole the prior pass named but never machine-checked. That pass observed that `observed_roundtrip` can be discharged TRIVIALLY (return vx/vy/vz, composing neither conversion; it verifies) and argued from that observation alone that this is harmless because the round-trip composite is not a repo function. That argument is only sound if the two CONVERSIONS stay independently pinned once the round trip stops witnessing them -- which the prior pass asserted rather than tested. I tested the COMBINATION directly: atk_13 (trivial observed round trip AND the historical resolve-breaking forward), atk_14 (trivial equatorial round trip AND the pre-patch constant-geocentre re-reference), and atk_15 (BOTH round trips trivial AND all four conversions reverted verbatim to model_prepatch.py). Had any verified, its faithful patch would have been the historical resolve-breaker and the spec would be BROKEN. All three are REJECTED, atk_15 with all FOUR conversion postconditions failing at once. The paired isolating control probe_rt_trivial.py (both round trips trivial, both conversions left GOLD) VERIFIES -- so the trivial discharge removes a redundant witness, not the obligation. That completes the prior pass's argument with machine evidence instead of reasoning.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for astropy__astropy-13398.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Two pairs of DIRECT conversions are specified. Every frame involved is
  ANCHORED: it carries its own observing site and its own epoch, and nothing
  makes the anchoring of the frame a position is held in agree with the anchoring
  of the frame it is wanted in. So each conversion is TWO steps — a RE-REFERENCING
  step that moves the position from the anchoring it is held in to the anchoring
  it is wanted in, and a purely geometric ROTATION.

  FIRST PAIR: an Earth-fixed orientation <-> an observer-centred orientation.
  The rotation here is a constant orthogonal orientation matrix determined by the
  observing site of the OBSERVER-CENTRED frame — the frame that defines the
  observer-centred orientation, whichever end of the conversion it sits at.

  Earth-fixed (site L, epoch e_src) -> observer-centred (site T, epoch e_tgt):
    * FIRST refer the given position to the same-kind Earth-fixed frame anchored
      at the OUTPUT (observer-centred) frame's own site T and epoch e_tgt;
    * THEN apply the orientation matrix FOR THAT OUTPUT frame's own site T to the
      re-referred position.

  observer-centred (site L, epoch e_src) -> Earth-fixed (site T, epoch e_tgt):
    * FIRST apply the TRANSPOSE of the orientation matrix FOR THE INPUT
      (observer-centred) frame's own site L to the given position;
    * THEN refer the rotated position from the input frame's own anchoring
      (site L, epoch e_src) to the output frame's anchoring (site T, epoch
      e_tgt).

  SECOND PAIR: an intermediate Earth-equatorial orientation <-> an Earth-rotating
  orientation. The rotation here is the Earth-orientation rotation, whose value
  depends on an EPOCH.

  Earth-equatorial (site L, epoch e_src) -> Earth-rotating (site T, epoch e_tgt):
    * FIRST refer the given position to the same-kind Earth-equatorial frame
      anchored at the OUTPUT frame's own site T and epoch e_tgt;
    * THEN apply the Earth-orientation rotation FOR THE OUTPUT frame's epoch
      e_tgt to that re-referred position.

  Earth-rotating (site L, epoch e_src) -> Earth-equatorial (site T, epoch e_tgt):
    * FIRST apply the TRANSPOSE of the Earth-orientation rotation FOR THE INPUT
      frame's epoch e_src to the given position;
    * THEN refer the rotated position from the input frame's own anchoring
      (site L, epoch e_src) to the output frame's anchoring (site T, epoch
      e_tgt).

  The anchoring handed to the re-referencing step is the observable the issue is
  about: the position must be referred to the OUTPUT frame's OWN site and epoch,
  taken from the frame the caller asked for, and referred FROM the anchoring the
  input actually carries. Any other choice — a constant site independent of the
  frames, the endpoints interchanged, or omitting the step so the position is
  rotated as it stands — is a different observable behaviour. The same holds of
  the site the orientation matrix is built from, and of the epoch the
  Earth-orientation rotation is taken at: each conversion reads it off ONE named
  end of the conversion, and the two directions read opposite ends.

  When the two frames of a conversion agree in both site and epoch the
  re-referencing step introduces nothing, and only then is that conversion the
  bare rotation. In that same-anchoring case each pair is an EXACT round-trip
  identity — converting a position out and back returns it componentwise —
  precisely because each rotation is orthogonal, so its transpose undoes it. That
  same-anchoring round trip is the guarantee the issue demands. A conversion that
  instead reaches the far orientation by an INDIRECT route — one that does not
  apply the orthogonal rotation to the re-referred position, but introduces a
  further viewpoint-dependent directional shift along the way — does NOT
  reproduce the direct rotation and so does NOT round-trip exactly. When the
  anchorings differ neither pair composes to the identity — which is what makes
  the re-referencing step, and the site and epoch it is given, observable rather
  than decorative.

The position components, the site coordinates and the epoch are modelled as
exact integers (the round-trip identity is the exact algebraic cancellation that
the comparison tolerances absorb; the behaviour is precision-independent — see
refinement.md / mapping.md). The orthogonal rotation matrices and their actions
are unchanged callees (the rotation-matrix machinery and the Cartesian
transform); their forward/backward action is axiomatised, the only property the
proof needs being that the transpose-action inverts the forward action at one and
the same site (respectively at one and the same epoch). The re-referencing step
is an unchanged callee too; the only property the proof needs is that referring a
position between two frames of identical anchoring introduces no offset.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
@Pure
@ContractOnly
def fwd_x(x: int, y: int, z: int, sx: int, sy: int, sz: int) -> int:
    """First component of the constant orthogonal orientation matrix M(S) FOR THE
    SITE S = (sx, sy, sz) applied to the vector (x, y, z). The matrix is built
    from the site's own geodetic coordinates, so M(S) and M(S') are unrelated for
    S != S'. Unchanged callee (the rotation-matrix machinery via the Cartesian
    transform); provenance + executable soundness: mapping.md /
    axiom_check.py."""
    Ensures(True)

@Pure
@ContractOnly
def fwd_y(x: int, y: int, z: int, sx: int, sy: int, sz: int) -> int:
    """Second component of M(S) applied to (x, y, z)."""
    Ensures(True)

@Pure
@ContractOnly
def fwd_z(x: int, y: int, z: int, sx: int, sy: int, sz: int) -> int:
    """Third component of M(S) applied to (x, y, z)."""
    Ensures(True)

@Pure
@ContractOnly
def bwd_x(x: int, y: int, z: int, sx: int, sy: int, sz: int) -> int:
    """First component of the TRANSPOSE of M(S) applied to (x, y, z) (the
    inverse rotation for the site S). Unchanged callee."""
    Ensures(True)

@Pure
@ContractOnly
def bwd_y(x: int, y: int, z: int, sx: int, sy: int, sz: int) -> int:
    """Second component of the transpose of M(S) applied to (x, y, z)."""
    Ensures(True)

@Pure
@ContractOnly
def bwd_z(x: int, y: int, z: int, sx: int, sy: int, sz: int) -> int:
    """Third component of the transpose of M(S) applied to (x, y, z)."""
    Ensures(True)

@ContractOnly
def orthogonality(x: int, y: int, z: int, sx: int, sy: int, sz: int) -> None:
    """The single fact about the unchanged orthogonal orientation matrix the
    round-trip proof consumes: at ONE AND THE SAME site S = (sx, sy, sz),
    applying the transpose-action to the forward-action of any vector returns
    that vector componentwise (the transpose of an orthogonal matrix is its
    inverse). Nothing is claimed across two different sites. Provenance +
    executable soundness: mapping.md / axiom_check.py."""
    Requires(MustTerminate(2))
    Ensures(bwd_x(fwd_x(x, y, z, sx, sy, sz), fwd_y(x, y, z, sx, sy, sz),
                  fwd_z(x, y, z, sx, sy, sz), sx, sy, sz) == x)
    Ensures(bwd_y(fwd_x(x, y, z, sx, sy, sz), fwd_y(x, y, z, sx, sy, sz),
                  fwd_z(x, y, z, sx, sy, sz), sx, sy, sz) == y)
    Ensures(bwd_z(fwd_x(x, y, z, sx, sy, sz), fwd_y(x, y, z, sx, sy, sz),
                  fwd_z(x, y, z, sx, sy, sz), sx, sy, sz) == z)

@Pure
@ContractOnly
def prot_x(x: int, y: int, z: int, e: int) -> int:
    """First component of the Earth-orientation rotation P(e) FOR THE EPOCH e
    applied to the vector (x, y, z). This rotation relates an intermediate
    Earth-equatorial orientation to an Earth-rotating orientation; its value
    depends on the epoch e, and P(e) and P(e') are unrelated for e != e'. It is a
    distinct unchanged callee (the epoch-dependent Earth-orientation matrix
    builder and the Cartesian transform). Provenance + executable soundness:
    mapping.md / axiom_check.py."""
    Ensures(True)

@Pure
@ContractOnly
def prot_y(x: int, y: int, z: int, e: int) -> int:
    """Second component of the rotation P(e) applied to (x, y, z)."""
    Ensures(True)

@Pure
@ContractOnly
def prot_z(x: int, y: int, z: int, e: int) -> int:
    """Third component of the rotation P(e) applied to (x, y, z)."""
    Ensures(True)

@Pure
@ContractOnly
def prot_inv_x(x: int, y: int, z: int, e: int) -> int:
    """First component of the TRANSPOSE of the rotation P(e) applied to
    (x, y, z) (the inverse rotation at the epoch e). Unchanged callee."""
    Ensures(True)

@Pure
@ContractOnly
def prot_inv_y(x: int, y: int, z: int, e: int) -> int:
    """Second component of the transpose of P(e) applied to (x, y, z)."""
    Ensures(True)

@Pure
@ContractOnly
def prot_inv_z(x: int, y: int, z: int, e: int) -> int:
    """Third component of the transpose of P(e) applied to (x, y, z)."""
    Ensures(True)

@ContractOnly
def prot_orthogonality(x: int, y: int, z: int, e: int) -> None:
    """The single fact about the unchanged Earth-orientation rotation P(e) the
    round-trip proof consumes: at ONE AND THE SAME epoch e, its transpose-action
    inverts its forward-action componentwise (P(e) is orthogonal, so P(e)^T is
    its inverse). Nothing is claimed across two different epochs. Provenance +
    executable soundness: mapping.md / axiom_check.py."""
    Requires(MustTerminate(6))
    Ensures(prot_inv_x(prot_x(x, y, z, e), prot_y(x, y, z, e),
                       prot_z(x, y, z, e), e) == x)
    Ensures(prot_inv_y(prot_x(x, y, z, e), prot_y(x, y, z, e),
                       prot_z(x, y, z, e), e) == y)
    Ensures(prot_inv_z(prot_x(x, y, z, e), prot_y(x, y, z, e),
                       prot_z(x, y, z, e), e) == z)

@Pure
@ContractOnly
def offset_x(vx: int, vy: int, vz: int,
             lx: int, ly: int, lz: int, esrc: int,
             tx: int, ty: int, tz: int, etgt: int) -> int:
    """First component of the offset that referring the position (vx, vy, vz)
    introduces when that position, held in a frame anchored at site
    L = (lx, ly, lz) at epoch esrc, is referred to the SAME-KIND frame anchored
    at site T = (tx, ty, tz) at epoch etgt. The route taken ties the position to
    the Solar-System barycentre, so the offset is the
    geocentric-versus-topocentric aberration difference together with the change
    of epoch; it therefore depends on the position itself as well as on both
    anchorings. This is an unchanged callee (the re-referencing transform between
    two same-kind frames). Provenance + executable soundness: mapping.md /
    axiom_check.py."""
    Ensures(True)

@Pure
@ContractOnly
def offset_y(vx: int, vy: int, vz: int,
             lx: int, ly: int, lz: int, esrc: int,
             tx: int, ty: int, tz: int, etgt: int) -> int:
    """Second component of the re-referencing offset on (vx, vy, vz) from
    (site L, epoch esrc) to (site T, epoch etgt)."""
    Ensures(True)

@Pure
@ContractOnly
def offset_z(vx: int, vy: int, vz: int,
             lx: int, ly: int, lz: int, esrc: int,
             tx: int, ty: int, tz: int, etgt: int) -> int:
    """Third component of the re-referencing offset on (vx, vy, vz) from
    (site L, epoch esrc) to (site T, epoch etgt)."""
    Ensures(True)

@ContractOnly
def same_frame_noop(vx: int, vy: int, vz: int,
                    lx: int, ly: int, lz: int, e: int) -> None:
    """The single fact about the unchanged re-referencing transform the proof
    consumes: referring a position between two frames of IDENTICAL anchoring —
    the same site L and the same epoch e — introduces no offset. This is the
    weakest fact sufficient for the round-trip proof; the offset is otherwise
    uninterpreted, so nothing follows about referring to any other site or any
    other epoch. Provenance + executable soundness: mapping.md /
    axiom_check.py."""
    Requires(MustTerminate(10))
    Ensures(offset_x(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e) == 0)
    Ensures(offset_y(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e) == 0)
    Ensures(offset_z(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e) == 0)
# axioms-end

# pure-start
@Pure
def rebased_x(vx: int, vy: int, vz: int,
              lx: int, ly: int, lz: int, esrc: int,
              tx: int, ty: int, tz: int, etgt: int) -> int:
    """First component of the position (vx, vy, vz) once it has been REFERRED
    from the frame anchored at (site L = (lx, ly, lz), epoch esrc) to the
    same-kind frame anchored at (site T = (tx, ty, tz), epoch etgt): the given
    component plus the offset that re-referencing introduces."""
    return vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)

@Pure
def rebased_y(vx: int, vy: int, vz: int,
              lx: int, ly: int, lz: int, esrc: int,
              tx: int, ty: int, tz: int, etgt: int) -> int:
    """Second component of the re-referred position."""
    return vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)

@Pure
def rebased_z(vx: int, vy: int, vz: int,
              lx: int, ly: int, lz: int, esrc: int,
              tx: int, ty: int, tz: int, etgt: int) -> int:
    """Third component of the re-referred position."""
    return vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
# pure-end

def itrs_to_observed(comp: int,
                     vx: int, vy: int, vz: int,
                     lx: int, ly: int, lz: int, esrc: int,
                     tx: int, ty: int, tz: int, etgt: int) -> int:
    # pre-conditions-start
    # `comp` selects which output component (0, 1 or 2) to return. (vx, vy, vz)
    # is an Earth-fixed position held in a frame anchored at the site
    # L = (lx, ly, lz) at the epoch esrc; the observer-centred output is wanted
    # in the frame anchored at the site T = (tx, ty, tz) at the epoch etgt. Both
    # anchorings are free: nothing requires them to agree.
    Requires(comp == 0 or comp == 1 or comp == 2)
    Requires(MustTerminate(14))
    # pre-conditions-end
    # post-conditions-start
    # The given position is FIRST referred from the anchoring it is held in
    # (site L, epoch esrc) to the OUTPUT (observer-centred) frame's OWN anchoring
    # (site T, epoch etgt) — so the site and the epoch handed to the
    # re-referencing step are exactly the output frame's, and the position it is
    # applied to is exactly the given one. The orthogonal orientation matrix FOR
    # THAT OUTPUT frame's OWN site T is THEN applied to the re-referred position.
    # Each clause names the re-referencing endpoints and the site the matrix is
    # built from, so omitting the re-referencing step, referring to any other site
    # or epoch, reaching the observer-centred orientation by an indirect route, or
    # building the matrix from any other site, is a different value.
    Ensures(Implies(comp == 0, Result() == fwd_x(
        rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        tx, ty, tz)))
    Ensures(Implies(comp == 1, Result() == fwd_y(
        rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        tx, ty, tz)))
    Ensures(Implies(comp == 2, Result() == fwd_z(
        rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        tx, ty, tz)))
    # post-conditions-end
    # impl-start
    # Refer the position to the OUTPUT frame's own anchoring (site T, epoch
    # etgt), then rotate the re-referred position with the orientation matrix
    # built from that same output frame's own site T.
    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 0:
        return fwd_x(wx, wy, wz, tx, ty, tz)
    if comp == 1:
        return fwd_y(wx, wy, wz, tx, ty, tz)
    return fwd_z(wx, wy, wz, tx, ty, tz)
    # impl-end

def observed_to_itrs(comp: int,
                     ox: int, oy: int, oz: int,
                     lx: int, ly: int, lz: int, esrc: int,
                     tx: int, ty: int, tz: int, etgt: int) -> int:
    # pre-conditions-start
    # `comp` selects which output component (0, 1 or 2) to return. (ox, oy, oz)
    # is an observer-centred position held in a frame anchored at the site
    # L = (lx, ly, lz) at the epoch esrc; the Earth-fixed output is wanted in the
    # frame anchored at the site T = (tx, ty, tz) at the epoch etgt. Both
    # anchorings are free: nothing requires them to agree.
    Requires(comp == 0 or comp == 1 or comp == 2)
    Requires(MustTerminate(18))
    # pre-conditions-end
    # post-conditions-start
    # The TRANSPOSE of the orientation matrix FOR THE INPUT (observer-centred)
    # frame's OWN site L is applied to the given position FIRST; the rotated
    # position is THEN referred from the input frame's OWN anchoring (site L,
    # epoch esrc) to the output frame's anchoring (site T, epoch etgt). So the
    # matrix is built from the input frame's own site, the re-referencing step's
    # source anchoring is the input frame's own, its target anchoring is the
    # output frame's own, and the position it acts on is the ROTATED one — the
    # mirror of the forward conversion, in which the re-referencing precedes the
    # rotation and the matrix is built from the OUTPUT frame's site.
    Ensures(Implies(comp == 0, Result() == rebased_x(
        bwd_x(ox, oy, oz, lx, ly, lz), bwd_y(ox, oy, oz, lx, ly, lz),
        bwd_z(ox, oy, oz, lx, ly, lz),
        lx, ly, lz, esrc, tx, ty, tz, etgt)))
    Ensures(Implies(comp == 1, Result() == rebased_y(
        bwd_x(ox, oy, oz, lx, ly, lz), bwd_y(ox, oy, oz, lx, ly, lz),
        bwd_z(ox, oy, oz, lx, ly, lz),
        lx, ly, lz, esrc, tx, ty, tz, etgt)))
    Ensures(Implies(comp == 2, Result() == rebased_z(
        bwd_x(ox, oy, oz, lx, ly, lz), bwd_y(ox, oy, oz, lx, ly, lz),
        bwd_z(ox, oy, oz, lx, ly, lz),
        lx, ly, lz, esrc, tx, ty, tz, etgt)))
    # post-conditions-end
    # impl-start
    # Rotate with the transpose of the orientation matrix built from the INPUT
    # frame's own site L, then refer the rotated position from the input frame's
    # own anchoring to the output frame's anchoring.
    wx = bwd_x(ox, oy, oz, lx, ly, lz)
    wy = bwd_y(ox, oy, oz, lx, ly, lz)
    wz = bwd_z(ox, oy, oz, lx, ly, lz)
    if comp == 0:
        return wx + offset_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 1:
        return wy + offset_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    return wz + offset_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    # impl-end

def observed_roundtrip(comp: int,
                       vx: int, vy: int, vz: int,
                       lx: int, ly: int, lz: int, e: int) -> int:
    # pre-conditions-start
    # `comp` selects which component (0, 1 or 2) of the round-tripped position
    # to return. An Earth-fixed position (vx, vy, vz) held in a frame anchored at
    # the site L = (lx, ly, lz) at the epoch e, taken to the observer-centred
    # orientation in the frame anchored at the SAME site and the SAME epoch, and
    # back.
    Requires(comp == 0 or comp == 1 or comp == 2)
    Requires(MustTerminate(22))
    # pre-conditions-end
    # post-conditions-start
    # Converting an Earth-fixed position to the observer-centred orientation at
    # (site L, epoch e) and back to the Earth-fixed orientation at (site L, epoch
    # e) returns the original position exactly. This is the round-trip identity
    # the issue demands of the direct conversion pair; it holds because the two
    # frames share their anchoring, so the re-referencing step contributes nothing
    # on either leg, and because the orientation matrix for one site is
    # orthogonal.
    Ensures(Implies(comp == 0, Result() == vx))
    Ensures(Implies(comp == 1, Result() == vy))
    Ensures(Implies(comp == 2, Result() == vz))
    # post-conditions-end
    # impl-start
    # OUTBOUND LEG. Both frames carry the same anchoring, so referring between
    # them introduces no offset and the re-referred position is the position
    # itself.
    same_frame_noop(vx, vy, vz, lx, ly, lz, e)
    qx = rebased_x(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    qy = rebased_y(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    qz = rebased_z(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    Assert(qx == vx)
    Assert(qy == vy)
    Assert(qz == vz)
    # The observer-centred components are the orientation matrix for the shared
    # site applied to that re-referred position (each equals the corresponding
    # forward-conversion output by that conversion's postcondition).
    ox = fwd_x(qx, qy, qz, lx, ly, lz)
    oy = fwd_y(qx, qy, qz, lx, ly, lz)
    oz = fwd_z(qx, qy, qz, lx, ly, lz)
    r0 = itrs_to_observed(0, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    r1 = itrs_to_observed(1, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    r2 = itrs_to_observed(2, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    Assert(r0 == ox)
    Assert(r1 == oy)
    Assert(r2 == oz)
    # RETURN LEG. The transpose-action for that same site undoes the
    # forward-action, recovering the re-referred position and hence the input.
    orthogonality(qx, qy, qz, lx, ly, lz)
    wx = bwd_x(ox, oy, oz, lx, ly, lz)
    wy = bwd_y(ox, oy, oz, lx, ly, lz)
    wz = bwd_z(ox, oy, oz, lx, ly, lz)
    Assert(wx == vx)
    Assert(wy == vy)
    Assert(wz == vz)
    # The return leg refers between the same anchoring as well, so it introduces
    # no offset either.
    same_frame_noop(wx, wy, wz, lx, ly, lz, e)
    Assert(rebased_x(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vx)
    Assert(rebased_y(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vy)
    Assert(rebased_z(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vz)
    return observed_to_itrs(comp, ox, oy, oz, lx, ly, lz, e, lx, ly, lz, e)
    # impl-end

def equ_to_rot(comp: int,
               vx: int, vy: int, vz: int,
               lx: int, ly: int, lz: int, esrc: int,
               tx: int, ty: int, tz: int, etgt: int) -> int:
    # pre-conditions-start
    # `comp` selects which output component (0, 1 or 2) to return. (vx, vy, vz)
    # is an Earth-equatorial position held in a frame anchored at the site
    # L = (lx, ly, lz) at the epoch esrc; the Earth-rotating output is wanted in
    # the frame anchored at the site T = (tx, ty, tz) at the epoch etgt. Both
    # anchorings are free: nothing requires them to agree.
    Requires(comp == 0 or comp == 1 or comp == 2)
    Requires(MustTerminate(26))
    # pre-conditions-end
    # post-conditions-start
    # The given position is FIRST referred from the anchoring it is held in
    # (site L, epoch esrc) to the OUTPUT frame's OWN anchoring (site T, epoch
    # etgt) — so the site and the epoch handed to the re-referencing step are
    # exactly the output frame's, and the position it is applied to is exactly
    # the given one. The Earth-orientation rotation FOR THE OUTPUT frame's epoch
    # etgt is THEN applied to that re-referred position. Each clause names the
    # re-referencing endpoints and the rotation's epoch, so omitting the
    # re-referencing step, referring to any other site or epoch, or rotating at
    # any other epoch, is a different value.
    Ensures(Implies(comp == 0, Result() == prot_x(
        rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt), etgt)))
    Ensures(Implies(comp == 1, Result() == prot_y(
        rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt), etgt)))
    Ensures(Implies(comp == 2, Result() == prot_z(
        rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt), etgt)))
    # post-conditions-end
    # impl-start
    # Refer the position to the OUTPUT frame's own anchoring (site T, epoch
    # etgt), then rotate the re-referred position with the Earth-orientation
    # rotation for that same epoch etgt.
    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 0:
        return prot_x(wx, wy, wz, etgt)
    if comp == 1:
        return prot_y(wx, wy, wz, etgt)
    return prot_z(wx, wy, wz, etgt)
    # impl-end

def rot_to_equ(comp: int,
               ox: int, oy: int, oz: int,
               lx: int, ly: int, lz: int, esrc: int,
               tx: int, ty: int, tz: int, etgt: int) -> int:
    # pre-conditions-start
    # `comp` selects which output component (0, 1 or 2) to return. (ox, oy, oz)
    # is an Earth-rotating position held in a frame anchored at the site
    # L = (lx, ly, lz) at the epoch esrc; the Earth-equatorial output is wanted
    # in the frame anchored at the site T = (tx, ty, tz) at the epoch etgt. Both
    # anchorings are free: nothing requires them to agree.
    Requires(comp == 0 or comp == 1 or comp == 2)
    Requires(MustTerminate(30))
    # pre-conditions-end
    # post-conditions-start
    # The TRANSPOSE of the Earth-orientation rotation FOR THE INPUT frame's
    # epoch esrc is applied to the given position FIRST; the rotated position is
    # THEN referred from the input frame's OWN anchoring (site L, epoch esrc) to
    # the output frame's anchoring (site T, epoch etgt). So the re-referencing
    # step's source anchoring is the input frame's own, its target anchoring is
    # the output frame's own, the position it acts on is the ROTATED one, and the
    # rotation is taken at the INPUT epoch — the mirror of the forward
    # conversion, in which the re-referencing precedes the rotation and the
    # rotation is taken at the OUTPUT epoch.
    Ensures(Implies(comp == 0, Result() == rebased_x(
        prot_inv_x(ox, oy, oz, esrc), prot_inv_y(ox, oy, oz, esrc),
        prot_inv_z(ox, oy, oz, esrc),
        lx, ly, lz, esrc, tx, ty, tz, etgt)))
    Ensures(Implies(comp == 1, Result() == rebased_y(
        prot_inv_x(ox, oy, oz, esrc), prot_inv_y(ox, oy, oz, esrc),
        prot_inv_z(ox, oy, oz, esrc),
        lx, ly, lz, esrc, tx, ty, tz, etgt)))
    Ensures(Implies(comp == 2, Result() == rebased_z(
        prot_inv_x(ox, oy, oz, esrc), prot_inv_y(ox, oy, oz, esrc),
        prot_inv_z(ox, oy, oz, esrc),
        lx, ly, lz, esrc, tx, ty, tz, etgt)))
    # post-conditions-end
    # impl-start
    # Rotate with the transpose of the Earth-orientation rotation for the INPUT
    # frame's epoch esrc, then refer the rotated position from the input frame's
    # own anchoring to the output frame's anchoring.
    wx = prot_inv_x(ox, oy, oz, esrc)
    wy = prot_inv_y(ox, oy, oz, esrc)
    wz = prot_inv_z(ox, oy, oz, esrc)
    if comp == 0:
        return wx + offset_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 1:
        return wy + offset_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    return wz + offset_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    # impl-end

def equ_rot_roundtrip(comp: int,
                      vx: int, vy: int, vz: int,
                      lx: int, ly: int, lz: int, e: int) -> int:
    # pre-conditions-start
    # `comp` selects which component (0, 1 or 2) of the round-tripped position to
    # return. An Earth-equatorial position (vx, vy, vz) held in a frame anchored
    # at the site L = (lx, ly, lz) at the epoch e, taken to the Earth-rotating
    # orientation in the frame anchored at the SAME site and the SAME epoch, and
    # back.
    Requires(comp == 0 or comp == 1 or comp == 2)
    Requires(MustTerminate(34))
    # pre-conditions-end
    # post-conditions-start
    # Converting the position to the Earth-rotating orientation at (site L, epoch
    # e) and back to the Earth-equatorial orientation at (site L, epoch e)
    # returns the original position exactly. This is the round-trip identity for
    # the second conversion pair; it holds because the two frames share their
    # anchoring, so the re-referencing step contributes nothing on either leg,
    # and because the Earth-orientation rotation at one epoch is orthogonal.
    Ensures(Implies(comp == 0, Result() == vx))
    Ensures(Implies(comp == 1, Result() == vy))
    Ensures(Implies(comp == 2, Result() == vz))
    # post-conditions-end
    # impl-start
    # OUTBOUND LEG. Both frames carry the same anchoring, so referring between
    # them introduces no offset and the re-referred position is the position
    # itself.
    same_frame_noop(vx, vy, vz, lx, ly, lz, e)
    qx = rebased_x(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    qy = rebased_y(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    qz = rebased_z(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    Assert(qx == vx)
    Assert(qy == vy)
    Assert(qz == vz)
    # The Earth-rotating components are the rotation, at the shared epoch, of
    # that re-referred position (each equals the corresponding forward-conversion
    # output by that conversion's postcondition).
    ox = prot_x(qx, qy, qz, e)
    oy = prot_y(qx, qy, qz, e)
    oz = prot_z(qx, qy, qz, e)
    r0 = equ_to_rot(0, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    r1 = equ_to_rot(1, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    r2 = equ_to_rot(2, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    Assert(r0 == ox)
    Assert(r1 == oy)
    Assert(r2 == oz)
    # RETURN LEG. The inverse rotation at that same epoch undoes the forward
    # rotation, recovering the re-referred position and hence the input.
    prot_orthogonality(qx, qy, qz, e)
    wx = prot_inv_x(ox, oy, oz, e)
    wy = prot_inv_y(ox, oy, oz, e)
    wz = prot_inv_z(ox, oy, oz, e)
    Assert(wx == vx)
    Assert(wy == vy)
    Assert(wz == vz)
    # The return leg refers between the same anchoring as well, so it introduces
    # no offset either.
    same_frame_noop(wx, wy, wz, lx, ly, lz, e)
    Assert(rebased_x(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vx)
    Assert(rebased_y(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vy)
    Assert(rebased_z(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vz)
    return rot_to_equ(comp, ox, oy, oz, lx, ly, lz, e, lx, ly, lz, e)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for astropy__astropy-13398 / nagini. Frozen model.py sha256 0909cc14e7e0e16ee8475a566f6822e80ebbd32c991dfcdd8793dc9470f7f633, re-confirmed UNCHANGED after all runs. Scratch dir (fresh, exclusive; no other /tmp path used).

**RESULT:** 15 attacks, all SAME-spec, all ADMISSIBLE, all REJECTED. ZERO CANDIDATEs => no resolve run was owed or performed.

**TOOLCHAIN:** every attack below was verified with the pinned Nagini verifier, and every one was run to a verdict.

**BUILD METHOD:** generators gen.py / gen2.py / gen3.py copy the bundle's model.py and replace ONLY the body of a named function's `# impl-start`/`# impl-end` region. Every emitted file is gated BEFORE being written on: same_spec(BASE,text,LANG) True; spec_view(text)==spec_view(BASE) byte-for-byte; unsound_evasions(BASE,text,LANG)==[] (no new @ContractOnly / assumption tokens -- each attack must ESTABLISH, not assume); exactly one impl region located per target function, asserted not to have leaked past the next `def` (no silent anchor drift). Independently re-confirmed afterwards: `adversary same-spec` returned SAME for all 15, and a direct re-run of same_spec + unsound_evasions gave same_spec=True / evasions=[] for all 15.

### EXACT COMMANDS (from the repo root, per attack n = 1..15):
  python -m swebench_unified.adversary weakness  nagini astropy__astropy-13398 atk_<n>.py
  python -m swebench_unified.adversary same-spec nagini astropy__astropy-13398 atk_<n>.py
  bash scripts/nagini_verify.sh <file>.py    # controls + per-attack failing obligation
Raw transcripts kept beside each file as atk_<n>.weak.txt and atk_<n>.verify.txt; runners run_weak.sh / run_verify.sh.

PER-ATTACK -- every result was "NOT-A-COUNTEREXAMPLE: attack does not verify (verification failed)", exit=2, with the named failing obligation: atk_1  PREPATCH REPRODUCTION -- all four conversion impls lifted VERBATIM from the bundle's own model_prepatch.py (indirect fwd(bwd(v)) forward; un-referred backward; constant (0,0,0) site for the equatorial pair).

REJECTED. => prepatch bug reproduced. atk_2  *** A-LEG *** ORDER SWAP LAUNDERED THROUGH A LEGAL ORACLE + THE ONE-SITE AXIOM: observed_to_itrs calls itrs_to_observed (measure 14<18, legal) and instantiates `orthogonality` at the OUTPUT site T (one and the same site, a legal instance) to strip the fwd, making bwd(r,T) provably the RE-REFERENCED UNROTATED position -- gold's:141-145 shift applied BEFORE the:129/:137 transpose instead of after. REJECTED (observed_to_itrs). atk_3  TWO-HOP re-referencing on equ_to_rot: (L,esrc)->(T,esrc) then (T,esrc)->(T,etgt), both composite endpoints gold's, only the intermediate stop invented. Probes whether the spec licenses COMPOSING the unchanged re-referencing callee (it is not additive in the repo).

REJECTED (equ_to_rot). atk_4  ORDER SWAP on the equatorial backward: refer the GIVEN position (L,esrc)->(T,etgt) first, then transpose-rotate at esrc. Endpoints, rotation and epoch all gold's; only the ORDER differs. REJECTED (Postcondition of rot_to_equ,:549). atk_5  CONTROL-FLOW EFFECT on observed_to_itrs: gold's rotation and gold's two endpoints, but the offset SAMPLED AT THE UNROTATED position o instead of the rotated one. REJECTED (observed_to_itrs,:381) => gold's:145 position-dependence is live on this pair. atk_6  BOUNDARY / MIXED ANCHORING: equ_to_rot refers to the OUTPUT site T but at the INPUT epoch esrc, then rotates at etgt -- only ONE member of the target anchoring pair wrong.

REJECTED (equ_to_rot) => the site and epoch carriers are pinned independently. atk_7  PARTIAL DOMAIN, EPOCH-only guard: equ_to_rot is gold except when the EPOCHS agree, where the re-reference is dropped as if an epoch match alone discharged it while the SITES may still differ; `same_frame_noop` invoked at both legal instances to try to license it. REJECTED (equ_to_rot,:498). atk_8  *** A-LEG *** WRONG MATRIX SITE with gold's re-referencing INTACT: the matrix is built from the INPUT site L rather than the OUTPUT site T that gold's:112 reads, with `orthogonality` instantiated at BOTH sites (each legal) hoping the pair licenses a cross-site identification.

REJECTED (itrs_to_observed,:327) => the ONE-SITE scope holds against the OTHER ENDPOINT, not just against a constant. atk_9  *** A-LEG *** `same_frame_noop` SUBSTITUTED FOR GOLD'S REAL SHIFT: rot_to_equ's rotation is gold's but the offset is taken at the OUTPUT anchoring against ITSELF -- a legal, provably-ZERO instance -- so the return is the BARE rotation while the source still "performs a re-reference". REJECTED (rot_to_equ,:549) => a no-op instance cannot stand in for gold's:214/:217 (L,esrc)->(T,etgt) shift. atk_10 *** THE PRIOR PASS'S NAMED COUNTEREXAMPLE, re-encoded *** -- observed forward rotates the GIVEN triple with M(T), gold's:106-110 block DELETED, no anchoring consulted; `same_frame_noop` invoked at both legal instances.

Faithful patch on record as FAILING resolve (P2P 63/68, test_gcrs_altaz_bothroutes[testframe0..4]). REJECTED (Postcondition of itrs_to_observed). atk_11 PARTIAL DOMAIN, the exact test_gcrs_altaz_bothroutes shape (SITE-only guard): the observed forward re-references only when the SITES differ, so a site-equal / epoch-differing pair is treated as needing nothing. REJECTED (itrs_to_observed). atk_12 *** A-LEG *** CROSS-PAIR UNGROUNDED-ORACLE ECHO: rot_to_equ (measure 30) legally calls observed_roundtrip (measure 22) -- the OTHER pair's exact identity -- plus prot_orthogonality at two epochs and same_frame_noop, then returns the BARE transpose rotation with gold's:214/:217 dropped.

REJECTED (rot_to_equ,:549) => an identity proven for the observer-centred pair cannot be laundered into discharging the equatorial pair's shift. atk_13 *** MY PRINCIPAL FINDING *** COMBINATION: observed_roundtrip discharged TRIVIALLY (so it no longer witnesses the composition) AND the forward set to the historical resolve-breaker. Only itrs_to_observed's OWN postcondition can reject it. REJECTED (itrs_to_observed). atk_14 the same COMBINATION on the equatorial pair: trivial equ_rot_roundtrip AND the pre-patch constant-geocentre (0,0,0) re-reference gold replaces. REJECTED (equ_to_rot). atk_15 MAXIMAL: BOTH round trips trivial AND all FOUR conversions reverted verbatim to model_prepatch.py -- nothing but the four conversion postconditions left to reject it. REJECTED with ALL FOUR failing at once (itrs_to_observed, observed_to_itrs, equ_to_rot, rot_to_equ).

DISTINCTNESS (well past the >=5 floor and the required kind spread): prepatch reproduction (1, 15); partial-domain (7, 11, plus 13/14/15's round-trip discharge); boundary/argument (3, 6); control-flow-effect (2, 4, 5, 12); ungrounded-oracle echo (2, 8, 9, 12); dropped-step (10, 13, 14); order swap (2, 4). SEVEN are dedicated A-leg probes (2, 8, 9, 12 explicitly, plus 3/6/7 probing the offset's scope).

### Controls
pos_control.py       -- byte copy of the frozen model (sha256 identical): "Verification successful", 13.14s, exit=0. POSITIVE CONTROL. pos_reshape.py       -- genuine BEHAVIOUR-PRESERVING reshape (equatorial pair in the `rebased_*` spec spelling, reversed binding AND branch order): "Verification successful", 12.39s. So the spec pins BEHAVIOUR, not gold's token sequence. vac_control.py       -- VACUITY / axiom-consistency probe: all six consumed-axiom instances invoked legally, including overlapping/nested instantiations designed to make the axiom set collide if it can, then Assert(False).

"Verification failed" (exit=1, "Assert might fail") => the axiom set is CONSISTENT, so neither the positive verifications nor any of the 15 rejections is vacuous. probe_rt_trivial.py  -- ISOLATING control for my principal finding: both round trips discharged trivially, both conversions left GOLD. VERIFIES (9.45s). Together with atk_13/14/15 being REJECTED, this proves the trivial round-trip discharge removes a REDUNDANT WITNESS, not the obligation -- the two conversions remain pinned by their own postconditions. Not submitted as an attack: it refines to no repo change, so it can produce no failing patch.

### REFINEMENT.MD AUDIT (the A legs and the model<->patch correspondence):
  * Leg tags, enumerated mechanically from the tables: A1=R, A2=A-consumed, A3=A-consumed, B1=A-consumed, B2=A-consumed/I, C1=A-consumed, C2=I, C3=A-consumed, C4=A-consumed/I, C2a=R, C2b=A-consumed, C2c=A-consumed, C2d=A-consumed, C2e=A-consumed/I, C2f=A-consumed, C2g=I/A-consumed. All 16 legs are R / A-consumed / I. NO A-reference deep model and NO kind-3 step, consistent with meta.json deep_model_references == [].
  * Line citations verified against the REAL sources, not taken on trust. I extracted the gold itrs_observed_transforms.py from instance.json's patch and line-numbered it::106-110 is the forward re-reference to ITRS(obstime=observed_frame.obstime, location=observed_frame.location);:112 reads observed_frame.location.to_geodetic('WGS84');:115/:121 feed its lon/lat to itrs_to_altaz_mat / itrs_to_hadec_mat;:129 reads observed_coo.location;:137/:139 apply matrix_transpose(...);:141-145 build ITRS(crepr, obstime=observed_coo.obstime, location=observed_coo.location).transform_to(itrs_frame). Every cited line matches exactly. I also checked out base_commit 6500928dc0e57be8f06d1162eacc3ba5e2eff692 and line-numbered intermediate_rotation_transforms.py: cirs_to_itrs at:197-206 with location=EARTH_CENTER at:201 and pmat = cirs_to_itrs_mat(itrs_frame.obstime) at:204; itrs_to_cirs at:209-217 with pmat from itrs_coo.obstime at:212 and CIRS(newrepr, obstime=itrs_coo.obstime) (NO location=) at:214. Every §C2 citation matches, and patch.diff changes exactly those two arguments (plus the TETE mirror at:148-167). §0's provenance note is correct: the gold transform does NOT carry the issue draft's observer-position subtraction; that stays in the caller.
  * A-leg correspondence to the real callees HOLDS. fwd_*/bwd_* <-> CartesianRepresentation.transform of the rotation_matrix composite (itrs_to_altaz_mat / itrs_to_hadec_mat are products of a sign-flip and rotation_matrix factors, matrix_transpose is.swapaxes(-2,-1)), so M^T M = I: orthogonality is the WEAKEST sufficient fact and is SITE-scoped, claiming nothing cross-site (atk_8's cross-site identification is duly rejected). prot_*/prot_inv_* <-> cirs_to_itrs_mat / tete_to_itrs_mat (ERFA polar-motion / Earth-rotation / precession products, orthogonal), EPOCH-scoped. offset_* <-> the same-kind re-referencing transform: axiom_check.py's same_kind_offset drives it through the PUBLIC frame API (cls(rep, obstime=t_src, location=loc_src).transform_to(cls(obstime=t_tgt, location=loc_tgt)).cartesian - rep) so the REGISTERED transform actually executes, and it validates same_frame_noop (residual <= 1e-3 m) plus BOTH carrier CONTROLS (target site changed alone > 1.0 m; target epoch changed alone > 1.0 m) at BOTH instances mapping.md binds it to -- CIRS<->CIRS and ITRS<->ITRS (the (d2) block, on a witness produced by the real CIRS@(L,e)->ITRS@(L,e) transform). So neither carrier is decorative and the axiom provably does NOT extend past its identical-anchoring case -- exactly the scope atk_7 / atk_9 / atk_12 probe and fail to exceed.
  * Every carrier the A-legs claim is load-bearing has an independent REJECTED attack behind it: matrix site (atk_8), rotation epoch (atk_6 mixed, atk_12 cross-pair), both re-referencing endpoints (atk_10, atk_11, atk_3), step order (atk_2, atk_4), offset position-dependence (atk_5), exact scope of same_frame_noop (atk_7, atk_9, atk_12), and the conversions' independence from the round-trip witness (atk_13, atk_14, atk_15 + probe_rt_trivial).
  * §D's refraction scoping is correct and checked against the real F2P list (4 tests: test_itrs_topo_to_altaz_with_refraction, test_itrs_topo_to_hadec_with_refraction, test_cirs_itrs_topo, test_itrs_straight_overhead). Exact identity is asserted only on the no-pressure frames; the refraction path is checked against the pre-existing CIRS route within loose tolerance. P2P (68 tests) does contain test_gcrs_altaz_bothroutes[testframe0..4] -- the five tests the historical counterexample broke, which is precisely what atk_10 / atk_11 / atk_13 target and which the current spec rejects.

**ADVISORY VERDICT:** SOUND. 15 admissible same-spec attacks run (3x the floor), the prepatch bug reproduced and rejected on all four conversion postconditions, the prior pass's named counterexample and the site-only shape that historically broke P2P both rejected, the residual the prior pass named-but-never-tested (trivially dischargeable round trip) closed by machine evidence via the atk_13/14/15 combinations plus the probe_rt_trivial isolating control, two positive controls verify (including a non-trivial behaviour-preserving reshape), vacuity excluded by an Assert(False) probe that fails, and ZERO verifying wrong impls exist -- so no faithful patch could be materialized and no run_resolve was owed. I did not accept the prior SOUND on trust: I re-derived every leg tag, re-verified every line citation against base_commit and the patch, and attacked the one gap the prior reasoning left open.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** SPEC REGION INTEGRITY: `python3 -m swebench_unified.adversary same-spec nagini astropy__astropy-13398 atk_fbk13398.py` -> "SAME — attack shares the bundle's exact specification". `bash scripts/nagini_verify.sh model.py` -> "Verification successful" (12.22s). So the spec I audited is the frozen one and it does verify.

**REFERENCE USED:**  (base_commit 6500928dc0 + patch.diff APPLIED; `git diff --stat` shows exactly the patch's 3 modified files + untracked itrs_observed_transforms.py). Executed via  (astropy 5.1, numpy 1.22.4), whose builtin_frames files are byte-identical to the gold worktree modulo a leading `# -*- coding: utf-8 -*-` line. Base commit used only for the untouched callees (matrix builders, matrix_transpose, self-transform machinery), per the brief.

**WHAT I TRIED TO BREAK.** The spec is unusually strong: it does NOT model either transform as a bare rotation. It pins, for each of the four conversion directions, (a) that the anchoring re-reference happens, (b) BOTH of its endpoints, (c) the site/epoch the rotation matrix is built from, and (d) the ORDER of the two steps (nested `rebased_*` of `bwd_*`/`prot_inv_*` vs `fwd_*`/`prot_*` of `rebased_*`). A too-strong spec is the live risk, so I hunted for any input where a pinned clause is false of the real gold callee.

MEASUREMENT 1 — all six postconditions vs the real gold transforms. I re-derived each Ensures independently (real matrices from itrs_to_altaz_mat/itrs_to_hadec_mat/cirs_to_itrs_mat/tete_to_itrs_mat; real offset from the same-kind self-transform) and compared to the real registered transform driven through the public frame API, over the full cross product of 3-6 sites x 2-4 obstimes x all four anchoring combinations (identical / site-differs / epoch-differs / both-differ) x AltAz and HADec:
  itrs_to_observed  worst rel discrepancy 3.54e-16
  observed_to_itrs  worst rel discrepancy 1.87e-16
  equ_to_rot (cirs_to_itrs) 1.86e-16
  rot_to_equ (itrs_to_cirs) 1.70e-16
  equ_to_rot/rot_to_equ at the TETE instance (tete_to_itrs / itrs_to_tete, offset bound TETE->TETE): 1.97e-16 / 6.85e-17
  observed_roundtrip and equ_rot_roundtrip at shared anchoring: 1.99e-16
All at machine epsilon. A 500-iteration randomized fuzz (magnitudes 1e-1..1e12, 6 sites incl. geocentre/N pole/S pole/antimeridian/deep/1e9 m altitude, 4 obstimes, both observed kinds) gave worst rel 4.14e-16 across all six. No divergence.

MEASUREMENT 2 — is the offset axiom's scope over-claimed? `same_frame_noop` claims offset==0 ONLY at identical anchoring. I measured the real self-transform residual at identical anchoring for ITRS, CIRS and TETE over 5 sites x 4 obstimes x fuzzed vectors: max residual EXACTLY 0.0 with zero nonzero cases, and bitwise identity over 200 random vectors for both ITRS and CIRS. So the axiom is not merely within-tolerance true, it is exactly true — the spec does not over-claim it. The gold guard at itrs_observed_transforms.py:106 is what makes this exact, and I confirmed `np.any(L != L')` is False for equal-but-distinct EarthLocation objects (offset [0,0,0]), so the guard's notion of "same anchoring" matches the model's tag equality rather than object identity. This matters because it is the only axiom the round-trip proof consumes, and an inexact version would make the exact-integer round-trip postcondition too strong.

MEASUREMENT 3 — is the orthogonality axiom over-claimed at pathological sites? |M^T M - I| over geocentre, both poles, equator, antimeridian, height -6.3e6 m, height +1e9 m, 1e-9 m offset, negative-z: max 4.44e-16, no NaN, no failure. Notably the geocentre (which the model maps to (0,0,0) and which is ITRS's new default `location`) resolves to lat=90 deg and yields exactly diag(-1,1,1) / diag(1,-1,1) — orthogonal, so the (0,0,0) refinement is sound rather than a degenerate hole.

MEASUREMENT 4 — are the shared model symbols actually shared behaviour? I checked that the model's reuse of ONE symbol family across two repo instances is not a hidden over-claim. It is not, because each instance is bound separately by the harness, and I confirmed the instances genuinely differ (ITRS-offset vs CIRS-offset differ by up to 5.2e11 m; cirs_to_itrs_mat vs tete_to_itrs_mat entries differ by up to 5.7e-3; altaz vs hadec matrices by 1.90) — so the model is not silently assuming they coincide.

MEASUREMENT 5 — scoping honesty. Refraction (pressure>0) is explicitly scoped out in refinement.md §D, and I confirmed why that scoping is legitimate rather than convenient: at pressure=0 the real forward transform equals the bare rotation to 0.000e+00, at pressure=1000 hPa it deviates by 4.37e-4 relative — a genuinely non-orthogonal perturbation the F2P tests only check loosely (atol=0.1 mas / 10 cm), never as an identity. Default AltAz/HADec pressure is 0.0 hPa, so the default-attribute path — the one the pinned postconditions govern — is the no-refraction branch. The spec claims exact identity only there. Not an over-claim.

MEASUREMENT 6 — bundle's own gates re-run by me against the real repo, not trusted from the artifact: axiom_check.py exits OK (orthogonality over 7056 (lon,lat) configs x 68 vectors, 8 cross-site controls >= 3.41e6 m; prot_orthogonality over 10 configs with cross-epoch controls; same_frame_noop at BOTH bound instances with worst residual 0 m and site/epoch controls >= 1.37e8 / 8.67e10 m). conformance_check.py exits OK: 364500 component inputs, 15 configurations, both pairs over all 4 anchoring combinations, 0 disagreements.

ONLY NON-MATCHES FOUND, and why neither is a faithfulness defect: (i) v = [1e300,0,0] overflows to NaN inside erfa's p2s during the differing-anchoring re-reference — a float-domain overflow in an untouched callee, outside the exact-integer refinement (mapping.md §2) and outside any tested behaviour; the model's integers have no overflow. (ii) The shared-anchoring round trip is only float-exact, not bitwise, on some tiny/mixed vectors (e.g. [1e-30,0,0] -> y = -4.4e-47, [0,0,-1e8] -> x = -7.5e-9): residuals at 1e-17 relative, precisely the floating-point error the documented int refinement and the F2P `assert_allclose` tolerances absorb. Neither is an input where the modeled function disagrees with the real callee under the stated refinement.

**CONCLUSION:** no diverging input found. Every pinned clause — the re-reference, both its endpoints, the matrix's site, the rotation's epoch, and the order of the two steps in each of the four directions — is an equality the real gold code makes true at the cited line, verified to machine precision across the whole free anchoring domain including the case where the anchorings differ. The two consumed axioms hold exactly (offset) or to 4e-16 (orthogonality) on the real untouched callees, and their controls show neither carrier is decorative, so the axioms are the weakest sufficient contracts rather than convenient over-claims. The spec is not stronger than the patched repo behavior. Verdict FAITHFUL.

**SPEC REGION INTEGRITY:** `python3 -m swebench_unified.adversary same-spec nagini astropy__astropy-13398 atk_fbk13398.py` -> "SAME — attack shares the bundle's exact specification". `bash scripts/nagini_verify.sh model.py` -> "Verification successful" (12.22s). So the spec I audited is the frozen one and it does verify.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE: NO relaxation applies to this bundle, so I judged it as an ordinary STRICT leakage review with no inherited disposition. There is no RELAXED_LEAKAGE.md anywhere under benchmark-verified/astropy__astropy-13398/ (find -iname '*RELAX*' -> empty), meta.json has NO top-level `relaxed_leakage` key (json keys are: additional_change_sites, ax_apply_gold, ax_apply_gold_note, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, type_modeling, version), and meta.json gates['G-LEAK'].status == 'pass' (NOT 'relaxed'), which is the flag spec_guide.md 0.6 requires for the relaxed lane. The string 'relaxed_leakage' occurs in meta.json ONLY inside prior-panel prose stored in the gates blob, never as a flag. So the relaxation clause in my instructions is inapplicable and I applied the full no-leakage bar.

### WHAT I MEASURED (all my own runs, from source, at the project root):

1. SPEC VIEW EXTRACTED MYSELF, not read off a stored copy: markers.spec_view(model.py, get_backend('nagini').language) -> 525 lines, dumped to spec_view.txt and read in full. This is the exact consumer-visible artifact (module docstring + axioms + pure + pre/post-conditions + region markers; impl elided).

2. MECHANICAL SCREEN, run by me: leakage.screen(model.py, nagini tables, instance.patch, instance.problem_statement, instance.test_patch) -> passed=True, hard_failures=[], warnings=[]. So: no diff markers, no gold-patch line reproduced (>=8 normalized chars), no patched file path, no patched module dotted path, no narration vocabulary (bug/fix/patch/wrong/broken/...), no identifier or comment naming a patched repo symbol that is not already public.

3. GOLD SYMBOL SWEEP, done independently of the screen. leakage.`_patch_changed_symbols`(gold) = [add_refraction, altaz_to_hadec_mat, cirs_to_gcrs, itrs_to_altaz_mat, itrs_to_cirs, itrs_to_hadec_mat, itrs_to_observed, itrs_to_tete, observed_to_itrs, remove_refraction, tete_to_gcrs, tete_to_itrs_mat]. I tested each for presence in the spec view (substring, case-insensitive, so embedding counts) AND for presence in the problem_statement. Result: 10 of 12 are ABSENT from the spec view entirely. The only two present -- itrs_to_observed, observed_to_itrs -- are quoted VERBATIM in the public problem_statement, which contains the issue author's own draft code including the lines 'def itrs_to_observed(itrs_coo, observed_frame):' and 'def observed_to_itrs(observed_coo, itrs_frame):'. Naming them therefore reveals nothing the solver cannot already read in the task. Notably the gold's genuinely private new helpers (itrs_to_altaz_mat, itrs_to_hadec_mat, altaz_to_hadec_mat, add_refraction, remove_refraction -- the refraction machinery the issue explicitly says it has NOT written) are all absent.

4. REPO-VOCABULARY SWEEP beyond the symbol list: I grepped the spec view for 40 gold-specific tokens (EARTH_CENTER, location=, EarthLocationAttribute, TimeAttribute, obstime, CIRS, TETE, AltAz, HADec, ITRS, pressure, refraction, refco, erfa, WGS84, get_itrs, realize_frame, matrix_transpose, rotation_matrix, frame_transform_graph, transform_to, itrs_observed_transforms, intermediate_rotation_transforms, builtin_frames, NORTH_POLE, minus_x, minus_y,...). Only TWO hit: 'geodetic' and 'topocentric'. Both are public -- 'to_geodetic' and 'topocentric' both appear in the problem_statement (the issue's draft calls observed_frame.location.to_geodetic('WGS84') and its prose says 'geocentric versus topocentric aberration'). Every frame class name, the EARTH_CENTER constant (the actual discriminator of the second gold hunk), the location= keyword, and both patched module paths are ABSENT. The spec view speaks only in de-identified abstractions: 'site', 'epoch', 'anchoring', 'Earth-fixed', 'observer-centred', 'Earth-equatorial', 'Earth-rotating'.

5. HINTS-ONLY CHECK (the rule that matters most here, since leakage is judged vs problem_statement ONLY, never hints_text). hints_text is 14211 chars. I computed the set of >=5-char words appearing in the spec view AND in hints_text but NOT in the problem_statement: ['actually','along','behaviour','built','cancellation','change','choice','constant','desired','difference','different','either','every','exactly','fixed','further','given','intermediate','moves','needs','nothing','observer','observing','precisely','result','route','second','solar','stated','sufficient','system','target']. Every one is generic English; not one is a repo symbol, a diagnosis, or a discriminator. So no hints-only vocabulary is echoed -- the classic relaxed-leakage tell is absent, which is itself consistent with no relaxation being needed.

6. LOAD-BEARING TEST (the decisive one, and the reason I am confident the prose is descriptive rather than prescriptive). The worry with a spec view this discursive is that the narration, not the formal contract, is what tells the solver what to write. I tested that directly: I AST-stripped every docstring (module + all 20 functions, replaced with "d.") and deleted every non-marker comment line from BOTH model.py and model_prepatch.py, leaving only formal Requires/Ensures/returns plus region markers, and confirmed the stripped text contains none of geocentric/aberration/barycentre/indirect/'constant site'/observer/anchor. Then ran the pinned verifier:
   - scripts/nagini_verify.sh gold_nonarr.py -> 'Verification successful' (exit 0, 9.05s)
   - scripts/nagini_verify.sh pre_nonarr.py  -> 'Verification failed' (exit 1, 10.75s), failing the postconditions of itrs_to_observed, observed_to_itrs, equ_to_rot and rot_to_equ
   The discrimination survives total de-narration, so the prose is NOT load-bearing: the Ensures clauses alone (Result() == fwd_x(rebased_x(...),..., tx,ty,tz) etc.) separate gold from pre-patch. Nothing needed to be said in English to make this spec faithful, which is exactly why no relaxation is warranted and why the prose that IS there cannot be the mechanism of a leak.

7. BASELINE / CORE GATES re-run rather than assumed: unstripped scripts/nagini_verify.sh model.py -> 'Verification successful' exit 0 (8.8s, matching stored G-VERIFY); model_prepatch.py -> 'Verification failed' exit 1 on the same four postconditions (matching stored G-DIFF). same_spec(model.py, model_prepatch.py) -> True, and `adversary same-spec nagini astropy__astropy-13398` on the prepatch model -> 'SAME -- attack shares the bundle's exact specification' exit 0, so the two differ ONLY in the impl region and the spec region is byte-identical. Stored gates re-read: G-AX/G-CONF/G-DIFF/G-EQ/G-GOLD/G-HYGIENE/G-INTEGRITY/G-LEAK/G-MUT (20/20 killed, 0 survivors)/G-PBT/G-RESOLVE (resolved, not flaky)/G-VERIFY all 'pass'.

8. The offset_* axiom docstring is the one place with real astronomy prose ('The route taken ties the position to the Solar-System barycentre, so the offset is the geocentric-versus-topocentric aberration difference together with the change of epoch'). I looked at this hardest, since it is the closest thing to a mechanism narration. It is not a leak: it describes the semantics of an UNCHANGED callee (the re-referencing transform) so the reader can tell what the uninterpreted offset_* functions mean, and every concept in it -- SSB, geocentric vs topocentric aberration, the ITRS position being 'lost in the wake of the Earth's orbit around the SSB' -- is stated at length in the public problem_statement's own third paragraph. It names no symbol, no file, and no edit, and per the test in (6) it is not what makes the spec discriminate.

BUNDLE-ADDRESSES-REVIEWER CHECK (reported as a finding in its own right, per my instructions): meta.json's gates blob stores prior G-PANEL-3 records with agent_verdict='NO-LEAKAGE' plus long first-person narration, and verdict.md line 1464 carries 'Role 4 -- G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)'. That is a stored disposition for MY OWN gate, present in the bundle and visible before I judged -- the shape that can bias a later panel run, so I flag it. It does not instruct me: leakage.reviewer_directed() -> [] on model.py, refinement.md, mapping.md, axiom_check.py, conformance_check.py, properties.py, meta.json AND verdict.md (no addresses-the-reviewer, prescribes-the-verdict, or recording-convention hit), and the only imperative-shaped hits are prior panels describing their own reasoning. I used none of its conclusions as evidence; every fact above is my own re-measurement.

ONE DEFECT FOUND, disclosed but NOT leakage-relevant: meta.json's TOP-LEVEL region_hashes block is stale and matches nothing in the bundle -- top-level says spec_view=5cac9d00..., impl=8efb7855..., axioms=a2223b2c..., while markers.region_hashes(model.py) computes spec_view=64fbb77c..., impl=3bd9d3b0..., axioms=af4f27dc... (all six regions differ). The hashes stored inside gates['G-HYGIENE'].data.region_hashes DO match my computed values for all six regions exactly, so the artifact the gates actually attest is the shipped model.py; the top-level block is a stale leftover. I confirmed this is systemic, not this-cell tampering: I recomputed across all 500 nagini bundles carrying region_hashes and 499 of 500 disagree at top level (only astropy-13453 agrees), so it is a repo-wide staleness bug in whatever writes that key, not evidence the spec view was swapped. It does not affect my verdict -- I extracted the spec view from model.py myself rather than trusting any stored hash -- but it is worth a fix, since a stale top-level integrity record is exactly the sort of thing a future audit could either trust wrongly or read as tampering.

**CONCLUSION:** the spec view reveals nothing about the gold edit beyond the public problem_statement. The only two gold symbols it names are quoted verbatim in that public statement; the gold's private helpers, the EARTH_CENTER discriminator, the frame class names and both patched module paths are all absent; no hints_text-only vocabulary is echoed; and de-narration testing proves the formal contract, not the prose, is what discriminates gold from pre-patch. Verdict NO-LEAKAGE, on my own measurements.

**SCOPE:** NO relaxation applies to this bundle, so I judged it as an ordinary STRICT leakage review with no inherited disposition. There is no RELAXED_LEAKAGE.md anywhere under benchmark-verified/astropy__astropy-13398/ (find -iname '*RELAX*' -> empty), meta.json has NO top-level `relaxed_leakage` key (json keys are: additional_change_sites, ax_apply_gold, ax_apply_gold_note, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, type_modeling, version), and meta.json gates['G-LEAK'].status == 'pass' (NOT 'relaxed'), which is the flag spec_guide.md 0.6 requires for the relaxed lane. The string 'relaxed_leakage' occurs in meta.json ONLY inside prior-panel prose stored in the gates blob, never as a flag. So the relaxation clause in my instructions is inapplicable and I applied the full no-leakage bar.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
