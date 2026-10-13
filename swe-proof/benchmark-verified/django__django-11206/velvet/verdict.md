# P2 adversarial audit — django__django-11206

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 34 admissible attacks re-run of 34 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 34 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 22 | `atk_1_prepatch.lean`, `atk_3_zero_keeps_render.lean`, `atk_4_desc_only_rebuild.lean`, `atk_5_exact_threshold.lean`, `atk_6_boundary_le.lean`, `atk_7_partial_domain.lean`, `atk_11_none_clamps.lean`, `atk_12_multiplied_guard.lean`, `atk_12b_multiplied_guard.lean`, `atk_13_no_max_floor.lean`, +12 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 12 | `atk_2_echo.lean`, `atk_7b_partial_domain.lean`, `atk_8_ctrlflow_restore.lean`, `atk_9_forged_amount.lean`, `atk_10_double_clamp.lean`, `atk_19_out_of_range_early.lean`, `atk_20_require_consumed_guard.lean`, `atk_21_ctrlflow_rederive.lean`, `atk_22_echo_rebuilt_input.lean`, `atk_25_render_folded.lean`, +2 more |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (34):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -144,10 +144,7 @@
   ensures out = renderDecimal (clampSmall number decimalPos) decimalPos
   do
     -- impl-start
-    let mut num : DecVal := number
-    if belowResolution number decimalPos then
-      num := { amount := 0, render := zeroRender }
-    return renderDecimal num decimalPos
+    return renderDecimal number decimalPos
     -- impl-end
 
 prove_correct formatDecimal by
```

Attack 2 — `atk_2_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -144,10 +144,7 @@
   ensures out = renderDecimal (clampSmall number decimalPos) decimalPos
   do
     -- impl-start
-    let mut num : DecVal := number
-    if belowResolution number decimalPos then
-      num := { amount := 0, render := zeroRender }
-    return renderDecimal num decimalPos
+    return renderDecimal (clampSmall number decimalPos) decimalPos
     -- impl-end
 
 prove_correct formatDecimal by
```

Attack 3 — `atk_3_zero_keeps_render.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -146,7 +146,7 @@
     -- impl-start
     let mut num : DecVal := number
     if belowResolution number decimalPos then
-      num := { amount := 0, render := zeroRender }
+      num := { amount := 0, render := number.render }
     return renderDecimal num decimalPos
     -- impl-end
 
```

Attack 4 — `atk_4_desc_only_rebuild.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -144,7 +144,7 @@
   ensures out = renderDecimal (clampSmall number decimalPos) decimalPos
   do
     -- impl-start
-    let mut num : DecVal := number
+    let mut num : DecVal := { amount := number.amount, render := zeroRender }
     if belowResolution number decimalPos then
       num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
```

Attack 5 — `atk_5_exact_threshold.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,7 +145,7 @@
   do
     -- impl-start
     let mut num : DecVal := number
-    if belowResolution number decimalPos then
+    if decimalPos.elim false (fun p => decide (ratAbs number.amount < resolution p)) then
       num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
     -- impl-end
```

Attack 6 — `atk_6_boundary_le.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,7 +145,7 @@
   do
     -- impl-start
     let mut num : DecVal := number
-    if belowResolution number decimalPos then
+    if decimalPos.elim false (fun p => decide (ratAbs number.amount <= guardCutoff p)) then
       num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
     -- impl-end
```

Attack 7 — `atk_7_partial_domain.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,8 +147,17 @@
     let mut num : DecVal := number
     if belowResolution number decimalPos then
       num := { amount := 0, render := zeroRender }
+    if decimalPos.elim false (fun p => decide (leastExponentMagnitude < max p 1 + workingDigits)) then
+      num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
     -- impl-end
 
 prove_correct formatDecimal by
-  loom_solve <;> simp_all [clampSmall, plainZero, renderDecimal]
+  loom_solve <;>
+    first
+      | (exfalso
+         simp_all [positionsInExponentRange, workingDigits, leastExponentMagnitude]
+         omega)
+      | simp_all [clampSmall, plainZero, renderDecimal, belowResolution,
+                  guardCutoff, resolution, ratAbs]
+      | (simp_all [clampSmall, plainZero, renderDecimal]; done)
```

Attack 8 — `atk_7b_partial_domain.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,8 +147,21 @@
     let mut num : DecVal := number
     if belowResolution number decimalPos then
       num := { amount := 0, render := zeroRender }
+    if decimalPos.elim false (fun p => decide (leastExponentMagnitude < max p 1 + workingDigits)) then
+      num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
     -- impl-end
 
 prove_correct formatDecimal by
-  loom_solve <;> simp_all [clampSmall, plainZero, renderDecimal]
+  loom_solve <;>
+    first
+      | (exfalso
+         rcases decimalPos with _ | p <;>
+           simp_all [positionsInExponentRange, workingDigits,
+                     leastExponentMagnitude, belowResolution] <;>
+           omega)
+      | (rcases decimalPos with _ | p <;>
+           simp_all [clampSmall, plainZero, renderDecimal, belowResolution,
+                     positionsInExponentRange, workingDigits,
+                     leastExponentMagnitude])
+      | simp_all [clampSmall, plainZero, renderDecimal]
```

Attack 9 — `atk_8_ctrlflow_restore.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -144,9 +144,10 @@
   ensures out = renderDecimal (clampSmall number decimalPos) decimalPos
   do
     -- impl-start
-    let mut num : DecVal := number
-    if belowResolution number decimalPos then
-      num := { amount := 0, render := zeroRender }
+    let saved : DecVal := number
+    let mut num : DecVal := { amount := 0, render := zeroRender }
+    if ! (belowResolution number decimalPos) then
+      num := saved
     return renderDecimal num decimalPos
     -- impl-end
 
```

Attack 10 — `atk_9_forged_amount.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -144,7 +144,7 @@
   ensures out = renderDecimal (clampSmall number decimalPos) decimalPos
   do
     -- impl-start
-    let mut num : DecVal := number
+    let mut num : DecVal := { amount := 99999, render := number.render }
     if belowResolution number decimalPos then
       num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
```

Attack 11 — `atk_10_double_clamp.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,6 +147,8 @@
     let mut num : DecVal := number
     if belowResolution number decimalPos then
       num := { amount := 0, render := zeroRender }
+    if belowResolution num decimalPos then
+      num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
     -- impl-end
 
```

Attack 12 — `atk_11_none_clamps.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,7 +145,7 @@
   do
     -- impl-start
     let mut num : DecVal := number
-    if belowResolution number decimalPos then
+    if decide (ratAbs number.amount < guardCutoff (decimalPos.getD 0)) then
       num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
     -- impl-end
```

Attack 13 — `atk_12_multiplied_guard.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,10 +145,19 @@
   do
     -- impl-start
     let mut num : DecVal := number
-    if belowResolution number decimalPos then
+    if decimalPos.elim false (fun p =>
+        decide (ratAbs number.amount * ((10 : Rat) ^ (max p 1) * (2 * (10 : Rat) ^ workingDigits))
+                  < 2 * (10 : Rat) ^ workingDigits - 1)) then
       num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
     -- impl-end
 
 prove_correct formatDecimal by
-  loom_solve <;> simp_all [clampSmall, plainZero, renderDecimal]
+  loom_solve <;>
+    first
+      | (exfalso
+         simp_all [positionsInExponentRange, workingDigits, leastExponentMagnitude]
+         omega)
+      | simp_all [clampSmall, plainZero, renderDecimal, belowResolution,
+                  guardCutoff, resolution, ratAbs]
+      | (simp_all [clampSmall, plainZero, renderDecimal]; done)
```

Attack 14 — `atk_12b_multiplied_guard.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,10 +145,29 @@
   do
     -- impl-start
     let mut num : DecVal := number
-    if belowResolution number decimalPos then
+    if decimalPos.elim false (fun p =>
+        decide (ratAbs number.amount * ((10 : Rat) ^ (max p 1) * (2 * (10 : Rat) ^ workingDigits))
+                  < 2 * (10 : Rat) ^ workingDigits - 1)) then
       num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
     -- impl-end
 
 prove_correct formatDecimal by
-  loom_solve <;> simp_all [clampSmall, plainZero, renderDecimal]
+  loom_solve <;>
+    first
+      | (rcases decimalPos with _ | p <;>
+         simp_all [clampSmall, plainZero, renderDecimal, belowResolution,
+                   guardCutoff, resolution, ratAbs, workingDigits] <;>
+         (try positivity) <;>
+         (try
+            (constructor <;> intro h <;>
+             · rw [div_lt_iff₀ (by positivity)] at * <;> nlinarith [h])))
+      | (rcases decimalPos with _ | p <;>
+         simp_all [clampSmall, plainZero, renderDecimal, belowResolution,
+                   guardCutoff, resolution, ratAbs, workingDigits] <;>
+         rw [show ((0:Rat) < 1 / 10 ^ max p 1 - 1 / 10 ^ max p 1 / (2 * 10 ^ 28)) = True by
+               simp [eq_iff_iff]
+               rw [sub_pos, div_lt_iff₀ (by positivity)]
+               nlinarith [pow_pos (show (0:Rat) < 10 by norm_num) (max p 1)]] <;>
+         simp)
+      | simp_all [clampSmall, plainZero, renderDecimal]
```

Attack 15 — `atk_13_no_max_floor.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,7 +145,9 @@
   do
     -- impl-start
     let mut num : DecVal := number
-    if belowResolution number decimalPos then
+    if decimalPos.elim false (fun p =>
+        decide (ratAbs number.amount
+                  < 1 / (10 : Rat) ^ p - (1 / (10 : Rat) ^ p) / (2 * (10 : Rat) ^ workingDigits))) then
       num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
     -- impl-end
```

Attack 16 — `atk_14_signed_compare.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,7 +145,7 @@
   do
     -- impl-start
     let mut num : DecVal := number
-    if belowResolution number decimalPos then
+    if decimalPos.elim false (fun p => decide (number.amount < guardCutoff p)) then
       num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
     -- impl-end
```

Attack 17 — `atk_15_largest_admitted.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,10 +145,18 @@
   do
     -- impl-start
     let mut num : DecVal := number
-    if belowResolution number decimalPos then
+    if belowResolution number decimalPos
+        && decimalPos.elim true (fun p => decide (max p 1 + workingDigits < leastExponentMagnitude)) then
       num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
     -- impl-end
 
 prove_correct formatDecimal by
-  loom_solve <;> simp_all [clampSmall, plainZero, renderDecimal]
+  loom_solve <;>
+    first
+      | (exfalso
+         simp_all [positionsInExponentRange, workingDigits, leastExponentMagnitude]
+         omega)
+      | simp_all [clampSmall, plainZero, renderDecimal, belowResolution,
+                  guardCutoff, resolution, ratAbs]
+      | (simp_all [clampSmall, plainZero, renderDecimal]; done)
```

Attack 18 — `atk_16_zero_amount_shortcut.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,7 +145,7 @@
   do
     -- impl-start
     let mut num : DecVal := number
-    if belowResolution number decimalPos then
+    if belowResolution number decimalPos || decide (number.amount = 0) then
       num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
     -- impl-end
```

Attack 19 — `atk_17_prec27_prior_ce.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,7 +145,8 @@
   do
     -- impl-start
     let mut num : DecVal := number
-    if belowResolution number decimalPos then
+    if decimalPos.elim false (fun p =>
+        decide (ratAbs number.amount < resolution p - resolution p / (2 * (10 : Rat) ^ 27))) then
       num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
     -- impl-end
```

Attack 20 — `atk_18_le_resolution.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,7 +145,7 @@
   do
     -- impl-start
     let mut num : DecVal := number
-    if belowResolution number decimalPos then
+    if decimalPos.elim false (fun p => decide (ratAbs number.amount <= resolution p)) then
       num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
     -- impl-end
```

Attack 21 — `atk_19_out_of_range_early.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -144,6 +144,8 @@
   ensures out = renderDecimal (clampSmall number decimalPos) decimalPos
   do
     -- impl-start
+    if decide (999998 < decimalPos.getD 0) then
+      return renderDecimal { amount := 0, render := zeroRender } decimalPos
     let mut num : DecVal := number
     if belowResolution number decimalPos then
       num := { amount := 0, render := zeroRender }
@@ -151,4 +153,15 @@
     -- impl-end
 
 prove_correct formatDecimal by
-  loom_solve <;> simp_all [clampSmall, plainZero, renderDecimal]
+  loom_solve <;>
+    first
+      | (exfalso
+         rcases decimalPos with _ | p <;>
+           simp_all [positionsInExponentRange, workingDigits,
+                     leastExponentMagnitude, belowResolution] <;>
+           omega)
+      | (rcases decimalPos with _ | p <;>
+           simp_all [clampSmall, plainZero, renderDecimal, belowResolution,
+                     positionsInExponentRange, workingDigits,
+                     leastExponentMagnitude])
+      | simp_all [clampSmall, plainZero, renderDecimal]
```

Attack 22 — `atk_20_require_consumed_guard.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,10 +145,22 @@
   do
     -- impl-start
     let mut num : DecVal := number
-    if belowResolution number decimalPos then
+    if belowResolution number decimalPos
+        && decide (max (decimalPos.getD 1) 1 + workingDigits <= leastExponentMagnitude) then
       num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
     -- impl-end
 
 prove_correct formatDecimal by
-  loom_solve <;> simp_all [clampSmall, plainZero, renderDecimal]
+  loom_solve <;>
+    first
+      | (exfalso
+         rcases decimalPos with _ | p <;>
+           simp_all [positionsInExponentRange, workingDigits,
+                     leastExponentMagnitude, belowResolution] <;>
+           omega)
+      | (rcases decimalPos with _ | p <;>
+           simp_all [clampSmall, plainZero, renderDecimal, belowResolution,
+                     positionsInExponentRange, workingDigits,
+                     leastExponentMagnitude])
+      | simp_all [clampSmall, plainZero, renderDecimal]
```

Attack 23 — `atk_21_ctrlflow_rederive.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,6 +147,9 @@
     let mut num : DecVal := number
     if belowResolution number decimalPos then
       num := { amount := 0, render := zeroRender }
+    num := { amount := num.amount, render := num.render }
+    if belowResolution number decimalPos then
+      num := { amount := 0, render := num.render }
     return renderDecimal num decimalPos
     -- impl-end
 
```

Attack 24 — `atk_22_echo_rebuilt_input.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 3] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -144,10 +144,8 @@
   ensures out = renderDecimal (clampSmall number decimalPos) decimalPos
   do
     -- impl-start
-    let mut num : DecVal := number
-    if belowResolution number decimalPos then
-      num := { amount := 0, render := zeroRender }
-    return renderDecimal num decimalPos
+    return renderDecimal
+      (clampSmall { amount := number.amount, render := number.render } decimalPos) decimalPos
     -- impl-end
 
 prove_correct formatDecimal by
```

Attack 25 — `atk_23_guard_on_render.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,7 +145,7 @@
   do
     -- impl-start
     let mut num : DecVal := number
-    if belowResolution number decimalPos then
+    if decide (number.render decimalPos = zeroRender decimalPos) then
       num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
     -- impl-end
```

Attack 26 — `atk_24_skip_dp_zero.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,7 +145,7 @@
   do
     -- impl-start
     let mut num : DecVal := number
-    if belowResolution number decimalPos then
+    if belowResolution number decimalPos && decide (decimalPos ≠ some 0) then
       num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
     -- impl-end
```

Attack 27 — `atk_25_render_folded.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -144,7 +144,8 @@
   ensures out = renderDecimal (clampSmall number decimalPos) decimalPos
   do
     -- impl-start
-    let mut num : DecVal := number
+    let mut num : DecVal :=
+      { amount := number.amount, render := fun _ => number.render decimalPos }
     if belowResolution number decimalPos then
       num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
```

Attack 28 — `atk_26_guard_on_clamped.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,10 +145,27 @@
   do
     -- impl-start
     let mut num : DecVal := number
-    if belowResolution number decimalPos then
+    if belowResolution (clampSmall number decimalPos) decimalPos then
       num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
     -- impl-end
 
 prove_correct formatDecimal by
-  loom_solve <;> simp_all [clampSmall, plainZero, renderDecimal]
+  loom_solve <;>
+    first
+      | (rcases decimalPos with _ | p <;>
+         simp_all [clampSmall, plainZero, renderDecimal, belowResolution,
+                   guardCutoff, resolution, ratAbs, workingDigits] <;>
+         (try positivity) <;>
+         (try
+            (constructor <;> intro h <;>
+             · rw [div_lt_iff₀ (by positivity)] at * <;> nlinarith [h])))
+      | (rcases decimalPos with _ | p <;>
+         simp_all [clampSmall, plainZero, renderDecimal, belowResolution,
+                   guardCutoff, resolution, ratAbs, workingDigits] <;>
+         rw [show ((0:Rat) < 1 / 10 ^ max p 1 - 1 / 10 ^ max p 1 / (2 * 10 ^ 28)) = True by
+               simp [eq_iff_iff]
+               rw [sub_pos, div_lt_iff₀ (by positivity)]
+               nlinarith [pow_pos (show (0:Rat) < 10 by norm_num) (max p 1)]] <;>
+         simp)
+      | simp_all [clampSmall, plainZero, renderDecimal]
```

Attack 29 — `atk_27_zerorender_folded.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -146,7 +146,7 @@
     -- impl-start
     let mut num : DecVal := number
     if belowResolution number decimalPos then
-      num := { amount := 0, render := zeroRender }
+      num := { amount := 0, render := fun _ => zeroRender decimalPos }
     return renderDecimal num decimalPos
     -- impl-end
 
```

Attack 30 — `atk_28_render_wrong_dp.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -144,7 +144,8 @@
   ensures out = renderDecimal (clampSmall number decimalPos) decimalPos
   do
     -- impl-start
-    let mut num : DecVal := number
+    let mut num : DecVal :=
+      { amount := number.amount, render := fun _ => number.render (some 0) }
     if belowResolution number decimalPos then
       num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
```

Attack 31 — `atk_29_swapped_branches.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -144,9 +144,9 @@
   ensures out = renderDecimal (clampSmall number decimalPos) decimalPos
   do
     -- impl-start
-    let mut num : DecVal := number
+    let mut num : DecVal := { amount := number.amount, render := zeroRender }
     if belowResolution number decimalPos then
-      num := { amount := 0, render := zeroRender }
+      num := { amount := 0, render := number.render }
     return renderDecimal num decimalPos
     -- impl-end
 
```

Attack 32 — `atk_30_forged_zero_amount.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -146,7 +146,7 @@
     -- impl-start
     let mut num : DecVal := number
     if belowResolution number decimalPos then
-      num := { amount := 0, render := zeroRender }
+      num := { amount := 7, render := zeroRender }
     return renderDecimal num decimalPos
     -- impl-end
 
```

Attack 33 — `atk_31_echo_double.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -144,10 +144,8 @@
   ensures out = renderDecimal (clampSmall number decimalPos) decimalPos
   do
     -- impl-start
-    let mut num : DecVal := number
-    if belowResolution number decimalPos then
-      num := { amount := 0, render := zeroRender }
-    return renderDecimal num decimalPos
+    return renderDecimal
+      (clampSmall (clampSmall number decimalPos) decimalPos) decimalPos
     -- impl-end
 
 prove_correct formatDecimal by
```

Attack 34 — `atk_32_full_ulp.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,7 +145,8 @@
   do
     -- impl-start
     let mut num : DecVal := number
-    if belowResolution number decimalPos then
+    if decimalPos.elim false (fun p =>
+        decide (ratAbs number.amount < resolution p - resolution p / ((10 : Rat) ^ workingDigits))) then
       num := { amount := 0, render := zeroRender }
     return renderDecimal num decimalPos
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for django__django-11206 velvet. VERDICT SOUND. 34 same-spec attack files (30 distinct wrong-impl / rival ideas; 12 verified). ALL 12 verifying attacks had their faithful refined patch materialized AND RUN through the official harness (run_resolve) -- every one resolved=True, F2P 2/2, P2P 4/4. No verify-does-not-resolve break found.

**SETUP.** same_spec(Solution.lean, atk_N.lean, velvet) == True for all 34 attacks + positive control (35 files checked, 0 False; spec region byte-identical, only the impl region and where noted the consumer-supplied prove_correct body differ). Prepatch bug REPRODUCED: atk_1_prepatch.lean (= Solution_prepatch.lean impl) -> EXIT=1 with residual goal `number.render decimalPos = (if belowResolution number decimalPos = true then { amount := 0, render := zeroRender } else number).render decimalPos`, i.e. the postcondition is load-bearing exactly on the normalization clause.

**COMMANDS.** Verify: `bash scripts/lean_verify.sh <f>.lean` from the repo root, run 4-way concurrently in background batches (9 batches). Resolve: `python dores.py <name>` wrapping `swebench_unified.harness.run_resolve('django__django-11206', <diff>, timeout=3600)`, 4-way concurrent as detached background jobs. Base worktree at 571ab44e8a8936014c22e7eebe4948d9611fd7ce; all 12 diffs `git apply --check` rc=0 there. Local pre-screen (not the oracle, a cross-check) run per patch in a fresh worktree with the instance test_patch applied: baseline (unpatched) reproduces the bug row `AssertionError: '1.234e-300' != '0.000'`; all 12 candidate patches -> OK. All worktrees removed and pruned afterwards; the bundle itself is untouched (git status clean).

VERIFYING ATTACKS -> RESOLVE (the mandatory leg; all 12 resolved=True, F2P 2/2, P2P 4/4):
1. atk_2_echo -- ungrounded-oracle echo: returns the postcondition RHS `renderDecimal (clampSmall number decimalPos) decimalPos` verbatim. Faithful counterpart IS the gold block, so resolving is expected; retained-label discipline -- an echo carries the oracle verdict and is not a reject lane.
2. atk_7b_partial_domain -- ALSO clamp OUTSIDE positionsInExponentRange (max p 1 + 28 > 1000026, p > 999998). Verifies only because `require` makes the branch unreachable. NOTE: my first encoding atk_7_partial_domain got EXIT=1 on MY tactic (log shows the goal with require_1 and if_pos both present but simp_all not discharging it); re-encoded as 7b with an rcases+omega alternative that can consume require_1 -> EXIT=0. Faithful patch adds `if decimal_pos is not None and max(decimal_pos,1)+28 > 1000026: number = Decimal('0')`. resolved=True.
3. atk_19_out_of_range_early -- sharper partial-domain: for every out-of-range count, return the plain-zero display WITHOUT consulting the magnitude guard. resolved=True.
4. atk_20_require_consumed_guard -- guard conjoined with the range check the require clause already asserts (in-domain identity). resolved=True.
5. atk_8_ctrlflow_restore -- control-flow effect: start from plainZero, restore the input on the else leg (patch saves/restores via `_saved`). resolved=True.
6. atk_21_ctrlflow_rederive -- clamp, then unconditionally re-derive the value from its own two facets; structure eta IS the identity, so the faithful counterpart is gold + `number = number`. resolved=True.
7. atk_22_echo_rebuilt_input -- echo clampSmall on a value rebuilt from BOTH carried facets. resolved=True.
8. atk_10_double_clamp -- normalization applied twice, second guard read off the already-mutated local (idempotent). resolved=True.
9. atk_9_forged_amount -- pass-through keeps `render` but forges `amount := 99999`. The documented-unobservable degree of freedom (mapping.md §2); not realizable in Python (the two facets are observations of ONE object), so the faithful patch drops the unobservable forge. resolved=True.
10. atk_30_forged_zero_amount -- the SAME forge on the CLAMP branch (`amount := 7` with zeroRender). Same disposition: the tail is handed the display facet only. resolved=True.
11. atk_25_render_folded -- pass-through keeps ONLY the display observation at THIS decimalPos (`render := fun _ => number.render decimalPos`), discarding behaviour at every other count. Verifies because the unchanged tail observes the value exactly once, at this decimal_pos, so the fold is unobservable and the faithful counterpart is the identity. resolved=True.
12. atk_27_zerorender_folded -- the mirror fold on the clamp branch (`fun _ => zeroRender decimalPos`). resolved=True.

### REFUTED ATTACKS (22 EXIT=1, each log read individually to rule out syntax/tactic failure):
- atk_4_desc_only_rebuild: description-only carrier (amount kept, display replaced by zeroRender) -> goal `zeroRender decimalPos = number.render decimalPos`. The load-bearing §A0(i) rival; the `render` facet REFUSES it, exactly the defence refinement.md claims.
- atk_3_zero_keeps_render: normalizes to amount 0 but keeps the input's display -> `number.render decimalPos = zeroRender decimalPos`. The §A0(ii) `number * 0` rival; refused, so plainZero is pinned as a SPECIFIC value, not 'some zero'.
- atk_29_swapped_branches: the two branch results deliberately inverted. Refused.
- atk_5_exact_threshold: compares against `resolution p` instead of `guardCutoff p` (drops the half-ulp materialization lowering). Refused -> the lowering is load-bearing in the SPEC, not just prose.
- atk_32_full_ulp: lowering by a FULL ulp (10^28) instead of half (`2*10`^28). Refused.
- atk_17_prec27_prior_ce: the prior pass's named counterexample re-encoded verbatim (10^27 not 10^28) -- an ultra-thin window. Refused.
- atk_18_le_resolution: non-strict <= at resolution itself (would clamp 1e-8 at dp=8, breaking a graded row). Refused.
- atk_6_boundary_le: non-strict <= at guardCutoff (boundary off-by-one). Refused.
- atk_13_no_max_floor: drops the `max p 1` floor (1/10^p). Refused.
- atk_14_signed_compare: signed comparison, ratAbs dropped. Refused.
- atk_11_none_clamps: drops the dp=none arm (`decimalPos.getD 0`). Refused.
- atk_24_skip_dp_zero: refuses to clamp at dp = some 0 (partial domain INSIDE the declared range). Refused.
- atk_15_largest_admitted: refuses to clamp at the LARGEST ADMITTED count (max p 1 + 28 == 1000026, p=999998), i.e. the off-by-one probe on the require clause's own edge. Refused -> the bound is exactly tight and does NOT over-admit at its edge. This is the key check that the partial-domain lane (7b/19/20) is a legitimate declared-domain restriction rather than a hole.
- atk_23_guard_on_render: guard reads the display facet instead of the amount. Refused.
- atk_16_zero_amount_shortcut: ungrounded `amount = 0 => plain zero display` shortcut. Refused.
- atk_28_render_wrong_dp: display observed at the WRONG count (`some 0`) on the pass-through -> `number.render (some 0) = number.render decimalPos`. Refused.
- atk_31_echo_double: clampSmall applied twice as an echo (idempotence not derivable from the opaque facets). Refused.
- atk_7_partial_domain, atk_12_multiplied_guard: superseded first encodings of lanes that were re-encoded (7b verified; see the 12/12b note below).
- atk_12b_multiplied_guard, atk_26_guard_on_clamped: EXIT=1, but these are NOT refutations of a wrong impl -- both are algebraically EQUIVALENT to the frozen guard (cross-multiplied form; guard read off the already-clamped value, which is idempotent). Their EXIT=1 is MY proof being too weak, and I record them as such rather than as spec strength. My first pass on both also died on a genuine tactic error (`div_lt_iff` unknown in this Mathlib pin -> `div_lt_iff0`), which I fixed and re-ran before reading the goals. Reported for honesty; neither is evidence either way.

A-LEG AUDIT (my mandate). meta.json declares `axioms: []` and exactly ONE deep_model_reference: renderDecimal, kind A-reference, modelling the unchanged formatting tail. refinement.md leg table re-parsed honouring escaped pipes: A1=R, A2=R, A3=R+I, A4=R+I, A5=A-reference -- all five in the allowed set, NO kind-3 and NO A-consumed anywhere (the single 'A-consumed' occurrence is the legend). §C's claim 'there is no consumed axiom' is accurate and matches meta.json.

A5 CORRESPONDENCE RE-DERIVED INDEPENDENTLY (aleg.py, 4608 probes, 0 disagreements): patched_format(n, sep, dp, **kw) == renderDecimal (clampSmall (carrier n) dp) dp, with render = the PREPATCH tail on the input itself and zeroRender = the prepatch tail on Decimal('0'), both rebuilt from the SAME non-modeled args as each call (the trap the prior pass's first probe fell into -- building plainZero's render with '.' while calling with ',' -- I avoided by construction and cross-checked by running every suite row under both separators and under grouping/thousand_sep variants). Probe families: all 24 graded suite rows x 3 arg variants; the Decimal SUBCLASS render-necessity case (EuroDecimal with a '€ '-prefixing `__format__`) at 6 counts x 8 values x 2 separators; exact-tuple boundary probes straddling guardCutoff at p in {0,1,2,3,8,20,300,999996,999997,999998} both signs; subnormal / below-Etiny inputs (exponents to -2000000) at admitted counts {0,1,3,8,999998} -- confirming the clause bounds the COUNT ONLY and never the input; and 4000 deterministic-LCG fuzz draws.

NON-VACUITY of those boundary families (aleg2.py) -- a family entirely on one side of the threshold would prove nothing: every one of the 10 boundary families splits 8 clamp / 5 no-clamp on BOTH the modeled and the real guard, with 0 predicate mismatches. The sharpest witness is the half-ulp window itself: a magnitude inside [guardCutoff p, resolution p) is NOT clamped by either side (abs() lifts it onto cutoff), while one just below guardCutoff is clamped by both, at p in {1,2,3,8}. So `guardCutoff`, not `resolution`, is the predicate the interpreter actually applies -- §A0(ii) confirmed by measurement, not prose.

**Context constants independently confirmed:** prec == 28 == workingDigits, rounding == ROUND_HALF_EVEN, -getcontext().Etiny() == 1000026 == leastExponentMagnitude, and Fraction(Decimal('0.'+'1'.rjust(p,'0'))) == 1/10^max(p,1) for p in 0..60 (0 mismatches), i.e. cutoff == resolution exactly.

DOMAIN BOUNDARY reproduced in BOTH directions, exactly where §A0(iii) says: p=999998 (largest admitted) agrees on all 5 straddling probes; p=999999 (first rejected) DISAGREES on 2 of 5; and p=1000027 with input Decimal('1E-1000027') disagrees (real='0.000...' vs model='1.000...', because cutoff is exact at any exponent while abs() is a context operation that collapses to 0). So the require clause is measured-tight in both directions and is a genuine domain restriction, not a hypothesis bought to ease the proof.

Why the partial-domain resolves are legitimate rather than a hole: I confirmed the graded rows use decimal_pos in {None,0,1,2,3,8} only (max numeric 8), all far inside the declared domain, and the repository's only branch-reaching call site passes a DecimalField's decimal_places. So no suite row can catch an out-of-domain divergence -- which is precisely why running those three patches through the oracle was mandatory rather than optional. They resolve, and atk_15's refusal at the clause's own edge (p=999998) shows the clause does not over-admit inward. The declared domain therefore costs nothing on the graded rows and the restriction is honest.

**CAVEAT ON RECORD HYGIENE:** the prove_correct body is consumer-supplied too (same_spec tolerates editing it), so a bare EXIT=1 can mean tactic weakness rather than refutation. I therefore re-encoded every borderline rejection with a stronger proof (7/7b, 12/12b, 26) and read each log; the 22 EXIT=1 results comprise 18 genuine unsolved-ensures refutations, 2 superseded first encodings, and 2 (12b/26) that I explicitly do NOT count as spec strength because the impls are equivalent and my proof was the weak link. The partial-domain lane verified only once its proof could actually use require_1, which is the expected signature of a real domain restriction.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 34 admissible attacks re-run of 34 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 34 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 22 | `atk_1_prepatch.lean`, `atk_3_zero_keeps_render.lean`, `atk_4_desc_only_rebuild.lean`, `atk_5_exact_threshold.lean`, `atk_6_boundary_le.lean`, `atk_7_partial_domain.lean`, `atk_11_none_clamps.lean`, `atk_12_multiplied_guard.lean`, `atk_12b_multiplied_guard.lean`, `atk_13_no_max_floor.lean`, +12 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 12 | `atk_2_echo.lean`, `atk_7b_partial_domain.lean`, `atk_8_ctrlflow_restore.lean`, `atk_9_forged_amount.lean`, `atk_10_double_clamp.lean`, `atk_19_out_of_range_early.lean`, `atk_20_require_consumed_guard.lean`, `atk_21_ctrlflow_rederive.lean`, `atk_22_echo_rebuilt_input.lean`, `atk_25_render_folded.lean`, +2 more |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (34):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 34 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 3 — `atk_3_zero_keeps_render.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_desc_only_rebuild.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_exact_threshold.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_boundary_le.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_partial_domain.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_7b_partial_domain.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_8_ctrlflow_restore.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_9_forged_amount.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 11 — `atk_10_double_clamp.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_11_none_clamps.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_12_multiplied_guard.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_12b_multiplied_guard.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_13_no_max_floor.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_14_signed_compare.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_15_largest_admitted.lean` → rejected (same spec, does not verify — good)

Attack 18 — `atk_16_zero_amount_shortcut.lean` → rejected (same spec, does not verify — good)

Attack 19 — `atk_17_prec27_prior_ce.lean` → rejected (same spec, does not verify — good)

Attack 20 — `atk_18_le_resolution.lean` → rejected (same spec, does not verify — good)

Attack 21 — `atk_19_out_of_range_early.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 22 — `atk_20_require_consumed_guard.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 23 — `atk_21_ctrlflow_rederive.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 24 — `atk_22_echo_rebuilt_input.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 3]

Attack 25 — `atk_23_guard_on_render.lean` → rejected (same spec, does not verify — good)

Attack 26 — `atk_24_skip_dp_zero.lean` → rejected (same spec, does not verify — good)

Attack 27 — `atk_25_render_folded.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 28 — `atk_26_guard_on_clamped.lean` → rejected (same spec, does not verify — good)

Attack 29 — `atk_27_zerorender_folded.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 30 — `atk_28_render_wrong_dp.lean` → rejected (same spec, does not verify — good)

Attack 31 — `atk_29_swapped_branches.lean` → rejected (same spec, does not verify — good)

Attack 32 — `atk_30_forged_zero_amount.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 33 — `atk_31_echo_double.lean` → rejected (same spec, does not verify — good)

Attack 34 — `atk_32_full_ulp.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for django__django-11206 velvet. VERDICT SOUND. 34 same-spec attack files (30 distinct wrong-impl / rival ideas; 12 verified). ALL 12 verifying attacks had their faithful refined patch materialized AND RUN through the official harness (run_resolve) -- every one resolved=True, F2P 2/2, P2P 4/4. No verify-does-not-resolve break found.

**SETUP.** same_spec(Solution.lean, atk_N.lean, velvet) == True for all 34 attacks + positive control (35 files checked, 0 False; spec region byte-identical, only the impl region and where noted the consumer-supplied prove_correct body differ). Prepatch bug REPRODUCED: atk_1_prepatch.lean (= Solution_prepatch.lean impl) -> EXIT=1 with residual goal `number.render decimalPos = (if belowResolution number decimalPos = true then { amount := 0, render := zeroRender } else number).render decimalPos`, i.e. the postcondition is load-bearing exactly on the normalization clause.

**COMMANDS.** Verify: `bash scripts/lean_verify.sh <f>.lean` from the repo root, run 4-way concurrently in background batches (9 batches). Resolve: `python dores.py <name>` wrapping `swebench_unified.harness.run_resolve('django__django-11206', <diff>, timeout=3600)`, 4-way concurrent as detached background jobs. Base worktree at 571ab44e8a8936014c22e7eebe4948d9611fd7ce; all 12 diffs `git apply --check` rc=0 there. Local pre-screen (not the oracle, a cross-check) run per patch in a fresh worktree with the instance test_patch applied: baseline (unpatched) reproduces the bug row `AssertionError: '1.234e-300' != '0.000'`; all 12 candidate patches -> OK. All worktrees removed and pruned afterwards; the bundle itself is untouched (git status clean).

VERIFYING ATTACKS -> RESOLVE (the mandatory leg; all 12 resolved=True, F2P 2/2, P2P 4/4):
1. atk_2_echo -- ungrounded-oracle echo: returns the postcondition RHS `renderDecimal (clampSmall number decimalPos) decimalPos` verbatim. Faithful counterpart IS the gold block, so resolving is expected; retained-label discipline -- an echo carries the oracle verdict and is not a reject lane.
2. atk_7b_partial_domain -- ALSO clamp OUTSIDE positionsInExponentRange (max p 1 + 28 > 1000026, p > 999998). Verifies only because `require` makes the branch unreachable. NOTE: my first encoding atk_7_partial_domain got EXIT=1 on MY tactic (log shows the goal with require_1 and if_pos both present but simp_all not discharging it); re-encoded as 7b with an rcases+omega alternative that can consume require_1 -> EXIT=0. Faithful patch adds `if decimal_pos is not None and max(decimal_pos,1)+28 > 1000026: number = Decimal('0')`. resolved=True.
3. atk_19_out_of_range_early -- sharper partial-domain: for every out-of-range count, return the plain-zero display WITHOUT consulting the magnitude guard. resolved=True.
4. atk_20_require_consumed_guard -- guard conjoined with the range check the require clause already asserts (in-domain identity). resolved=True.
5. atk_8_ctrlflow_restore -- control-flow effect: start from plainZero, restore the input on the else leg (patch saves/restores via `_saved`). resolved=True.
6. atk_21_ctrlflow_rederive -- clamp, then unconditionally re-derive the value from its own two facets; structure eta IS the identity, so the faithful counterpart is gold + `number = number`. resolved=True.
7. atk_22_echo_rebuilt_input -- echo clampSmall on a value rebuilt from BOTH carried facets. resolved=True.
8. atk_10_double_clamp -- normalization applied twice, second guard read off the already-mutated local (idempotent). resolved=True.
9. atk_9_forged_amount -- pass-through keeps `render` but forges `amount := 99999`. The documented-unobservable degree of freedom (mapping.md §2); not realizable in Python (the two facets are observations of ONE object), so the faithful patch drops the unobservable forge. resolved=True.
10. atk_30_forged_zero_amount -- the SAME forge on the CLAMP branch (`amount := 7` with zeroRender). Same disposition: the tail is handed the display facet only. resolved=True.
11. atk_25_render_folded -- pass-through keeps ONLY the display observation at THIS decimalPos (`render := fun _ => number.render decimalPos`), discarding behaviour at every other count. Verifies because the unchanged tail observes the value exactly once, at this decimal_pos, so the fold is unobservable and the faithful counterpart is the identity. resolved=True.
12. atk_27_zerorender_folded -- the mirror fold on the clamp branch (`fun _ => zeroRender decimalPos`). resolved=True.

### REFUTED ATTACKS (22 EXIT=1, each log read individually to rule out syntax/tactic failure):
- atk_4_desc_only_rebuild: description-only carrier (amount kept, display replaced by zeroRender) -> goal `zeroRender decimalPos = number.render decimalPos`. The load-bearing §A0(i) rival; the `render` facet REFUSES it, exactly the defence refinement.md claims.
- atk_3_zero_keeps_render: normalizes to amount 0 but keeps the input's display -> `number.render decimalPos = zeroRender decimalPos`. The §A0(ii) `number * 0` rival; refused, so plainZero is pinned as a SPECIFIC value, not 'some zero'.
- atk_29_swapped_branches: the two branch results deliberately inverted. Refused.
- atk_5_exact_threshold: compares against `resolution p` instead of `guardCutoff p` (drops the half-ulp materialization lowering). Refused -> the lowering is load-bearing in the SPEC, not just prose.
- atk_32_full_ulp: lowering by a FULL ulp (10^28) instead of half (`2*10`^28). Refused.
- atk_17_prec27_prior_ce: the prior pass's named counterexample re-encoded verbatim (10^27 not 10^28) -- an ultra-thin window. Refused.
- atk_18_le_resolution: non-strict <= at resolution itself (would clamp 1e-8 at dp=8, breaking a graded row). Refused.
- atk_6_boundary_le: non-strict <= at guardCutoff (boundary off-by-one). Refused.
- atk_13_no_max_floor: drops the `max p 1` floor (1/10^p). Refused.
- atk_14_signed_compare: signed comparison, ratAbs dropped. Refused.
- atk_11_none_clamps: drops the dp=none arm (`decimalPos.getD 0`). Refused.
- atk_24_skip_dp_zero: refuses to clamp at dp = some 0 (partial domain INSIDE the declared range). Refused.
- atk_15_largest_admitted: refuses to clamp at the LARGEST ADMITTED count (max p 1 + 28 == 1000026, p=999998), i.e. the off-by-one probe on the require clause's own edge. Refused -> the bound is exactly tight and does NOT over-admit at its edge. This is the key check that the partial-domain lane (7b/19/20) is a legitimate declared-domain restriction rather than a hole.
- atk_23_guard_on_render: guard reads the display facet instead of the amount. Refused.
- atk_16_zero_amount_shortcut: ungrounded `amount = 0 => plain zero display` shortcut. Refused.
- atk_28_render_wrong_dp: display observed at the WRONG count (`some 0`) on the pass-through -> `number.render (some 0) = number.render decimalPos`. Refused.
- atk_31_echo_double: clampSmall applied twice as an echo (idempotence not derivable from the opaque facets). Refused.
- atk_7_partial_domain, atk_12_multiplied_guard: superseded first encodings of lanes that were re-encoded (7b verified; see the 12/12b note below).
- atk_12b_multiplied_guard, atk_26_guard_on_clamped: EXIT=1, but these are NOT refutations of a wrong impl -- both are algebraically EQUIVALENT to the frozen guard (cross-multiplied form; guard read off the already-clamped value, which is idempotent). Their EXIT=1 is MY proof being too weak, and I record them as such rather than as spec strength. My first pass on both also died on a genuine tactic error (`div_lt_iff` unknown in this Mathlib pin -> `div_lt_iff0`), which I fixed and re-ran before reading the goals. Reported for honesty; neither is evidence either way.

A-LEG AUDIT (my mandate). meta.json declares `axioms: []` and exactly ONE deep_model_reference: renderDecimal, kind A-reference, modelling the unchanged formatting tail. refinement.md leg table re-parsed honouring escaped pipes: A1=R, A2=R, A3=R+I, A4=R+I, A5=A-reference -- all five in the allowed set, NO kind-3 and NO A-consumed anywhere (the single 'A-consumed' occurrence is the legend). §C's claim 'there is no consumed axiom' is accurate and matches meta.json.

A5 CORRESPONDENCE RE-DERIVED INDEPENDENTLY (aleg.py, 4608 probes, 0 disagreements): patched_format(n, sep, dp, **kw) == renderDecimal (clampSmall (carrier n) dp) dp, with render = the PREPATCH tail on the input itself and zeroRender = the prepatch tail on Decimal('0'), both rebuilt from the SAME non-modeled args as each call (the trap the prior pass's first probe fell into -- building plainZero's render with '.' while calling with ',' -- I avoided by construction and cross-checked by running every suite row under both separators and under grouping/thousand_sep variants). Probe families: all 24 graded suite rows x 3 arg variants; the Decimal SUBCLASS render-necessity case (EuroDecimal with a '€ '-prefixing `__format__`) at 6 counts x 8 values x 2 separators; exact-tuple boundary probes straddling guardCutoff at p in {0,1,2,3,8,20,300,999996,999997,999998} both signs; subnormal / below-Etiny inputs (exponents to -2000000) at admitted counts {0,1,3,8,999998} -- confirming the clause bounds the COUNT ONLY and never the input; and 4000 deterministic-LCG fuzz draws.

NON-VACUITY of those boundary families (aleg2.py) -- a family entirely on one side of the threshold would prove nothing: every one of the 10 boundary families splits 8 clamp / 5 no-clamp on BOTH the modeled and the real guard, with 0 predicate mismatches. The sharpest witness is the half-ulp window itself: a magnitude inside [guardCutoff p, resolution p) is NOT clamped by either side (abs() lifts it onto cutoff), while one just below guardCutoff is clamped by both, at p in {1,2,3,8}. So `guardCutoff`, not `resolution`, is the predicate the interpreter actually applies -- §A0(ii) confirmed by measurement, not prose.

**Context constants independently confirmed:** prec == 28 == workingDigits, rounding == ROUND_HALF_EVEN, -getcontext().Etiny() == 1000026 == leastExponentMagnitude, and Fraction(Decimal('0.'+'1'.rjust(p,'0'))) == 1/10^max(p,1) for p in 0..60 (0 mismatches), i.e. cutoff == resolution exactly.

DOMAIN BOUNDARY reproduced in BOTH directions, exactly where §A0(iii) says: p=999998 (largest admitted) agrees on all 5 straddling probes; p=999999 (first rejected) DISAGREES on 2 of 5; and p=1000027 with input Decimal('1E-1000027') disagrees (real='0.000...' vs model='1.000...', because cutoff is exact at any exponent while abs() is a context operation that collapses to 0). So the require clause is measured-tight in both directions and is a genuine domain restriction, not a hypothesis bought to ease the proof.

Why the partial-domain resolves are legitimate rather than a hole: I confirmed the graded rows use decimal_pos in {None,0,1,2,3,8} only (max numeric 8), all far inside the declared domain, and the repository's only branch-reaching call site passes a DecimalField's decimal_places. So no suite row can catch an out-of-domain divergence -- which is precisely why running those three patches through the oracle was mandatory rather than optional. They resolve, and atk_15's refusal at the clause's own edge (p=999998) shows the clause does not over-admit inward. The declared domain therefore costs nothing on the graded rows and the restriction is honest.

**CAVEAT ON RECORD HYGIENE:** the prove_correct body is consumer-supplied too (same_spec tolerates editing it), so a bare EXIT=1 can mean tactic weakness rather than refutation. I therefore re-encoded every borderline rejection with a stronger proof (7/7b, 12/12b, 26) and read each log; the 22 EXIT=1 results comprise 18 genuine unsolved-ensures refutations, 2 superseded first encodings, and 2 (12b/26) that I explicitly do NOT count as spec strength because the impls are equivalent and my proof was the weak link. The partial-domain lane verified only once its proof could actually use require_1, which is the expected signature of a real domain restriction.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**SETUP.** Fresh worktree at base_commit 571ab44e8a8936014c22e7eebe4948d9611fd7ce with patch.diff APPLIED () as the reference for the modeled function; a second CLEAN base worktree () used only to attribute exception behavior. I had to pin sys.path explicitly: bare `python` inside the worktree resolved a stale Django 3.2, which would have produced bogus results (the reconstructed tail showed a float branch absent from this commit). Ambient context independently asserted: prec=28, ROUND_HALF_EVEN, Emin=-999999, Emax=999999, Etiny=-1000026 so -Etiny==leastExponentMagnitude==1000026, traps[Overflow]=True. The 'render'/'zeroRender' A-reference was reconstructed by deleting the normalization block from the installed patched source, giving the genuine unchanged tail (verified: it returns '1.234e-300' on the F2P row, i.e. the pre-change bug).

WHAT I TRIED TO BREAK, AND WHY IT HELD.

(1) guardCutoff vs resolution. The interesting claim is that the effective threshold is resolution lowered by half a unit in the 28th significant digit, because abs() is a CONTEXT operation that materializes at prec before comparing. I confirmed abs() rounds (abs(Decimal('0.09999999999999999999999999999999')) -> 0.1000...0, 28 digits) and that the model is exact on the half-ulp window, which is precisely where a spec comparing the exact magnitude against resolution would diverge. 0 disagreements across 39638 guard probes. This is measured-tight, not slack.

(2) The prior recorded G-PANEL UNFAITHFUL finding (verdict.md:1013-1021) - the small-side abs() underflow flush to zero below Etiny, which the earlier bytes missed while documenting only the Emax side. THIS IS NOW REPAIRED and I verified it against the current bytes rather than trusting the record. Its witnesses are all rejected by the current `require positionsInExponentRange`: Decimal('2E-1000027')/Decimal('1E-1000027') at p=1000027 (real guard True, model False) and (10^29-6)*10^-1000028 at p=999999 (real False, model True) - all have positionsInExponentRange=False, so the spec claims nothing about them.

Inside the admitted domain the small side is clean: 336 subnormal / below-Etiny / at-Etiny probes (exponents -999999,-1000000,-1000026,-1000027,-1000028,-1000066; both signs) at admitted p in {0,3,8,999998} -> 0 disagreements. Analytic confirmation that this is not luck: a subnormal input has |n| < 10^-999999, and the model can only call it not-below when max(p,1) >= 999999, i.e. p >= 999999, which the require rejects (p <= 999998). So the require closes the small side structurally, not incidentally. The earlier fail was against superseded bytes with an EMPTY pre-conditions region.

(3) The require's own tightness, so it is a domain restriction and not a convenience hypothesis. It admits 999998 and rejects 999999; agreement holds at p in {999996,999997,999998} and fails in BOTH directions just past the bound (p=999999 model over-normalizes; p=1000027 repo over-normalizes). It bounds only decimalPos and puts no bound on the input, which I confirmed by driving subnormal inputs through the largest admitted count p=999998.

(4) The render-necessity claim, i.e. that the carrier must hold display BEHAVIOUR and not a description. Confirmed load-bearing: Decimal subclasses with overridden `__format__` pass through unchanged when not normalized, and a description-only carrier would lose the '€ ' prefix. All subclass probes agreed.

**MECHANICAL CHECKS.** markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet backend) = True, so the spec region is byte-identical across the twin and the require/guardCutoff both appear in the spec view. scripts/lean_verify.sh on Solution.lean exits 0 (no sorry/error). Non-vacuity on the F2P row: prepatch tail gives '1.234e-300', the spec predicts '0.000' - they differ, so the buggy prepatch behavior genuinely violates this postcondition.

THE ONE RESIDUAL, ADJUDICATED AS NOT A DEFECT. The gold patch itself introduces the Overflow: at base commit format(Decimal('1E1000000'),'.',decimal_pos=2) returns '1.00e+1000000', and post-patch it raises, because the added abs(number) signals while the unchanged tail handles the value fine. So this is patch-introduced, not a base-comparison artifact, and I checked that specifically. I still judge it out of scope rather than a spec defect, for four independent reasons. (a) The real function has NO return value there - an uncaught trapped exception - so `ensures out = ...` has nothing to disagree with; the exception-free fragment cannot express it.

(b) It is exactly parallel to NaN/sNaN/Infinity, which also raise (InvalidOperation/TypeError) and which no reading treats as a faithfulness hole. (c) The exclusion is not hand-waved: it is stated in mapping.md, mechanized identically in BOTH check scripts' in_scope, and measured from both sides by check_emax_boundary - the bundle does not silently drift out of scope. (d) The only repair would be adding an input-magnitude bound to the require, which the panel guidance lists as the dishonest shape, costs zero suite rows, and would pin a Django regression rather than intended behavior.

Honest caveat for the record: this exclusion lives in mapping.md prose and the probes' in_scope, NOT in the Lean require, which bounds decimalPos alone - so a consumer reading Solution.lean in isolation sees an unconditional claim over an input where the real code raises. I flag that as a documentation asymmetry a future pass may revisit, not as a divergence in the modeled behavior, and it is the same treatment the prior G-PANEL pass explicitly conceded was legitimate when it attacked the small side instead.

Counterexample / evidence:

```
None. Every differential probe inside the declared in-scope domain agreed. Guard predicate (abs(number) < cutoff  vs  ratAbs amount < guardCutoff p), isolated from the display tail: 36888 probes at p in {0,1,2,3,4,8,15,27,28,29,50,200,1000,5000} -> 0 disagreements; 2750 probes at p in {0,1,2,3,8,15,50,200,999996,999997,999998} -> 0 disagreements. Non-vacuous: real guard returns [True,False,False] at guardCutoff-1/+0/+1 for p in {0,2,8,28,200,999998}, so the probes genuinely bracket the threshold and guardCutoff is measured-exact, NOT slack. End-to-end string equality vs the real patched format(): 41512 probes -> 0 disagreements; plus 1512 dense-boundary + 20000 random in-scope + 9 near-Emax non-raising probes -> 0 disagreements. Families covered: exact-tuple probes straddling guardCutoff at both signs, Decimal subclasses with overridden __format__ ('EuroDecimal' prefixing '€ ', 'WeirdDecimal' wrapping X..Y) which is the render-necessity family, grouping/thousand_sep/force_grouping variants, and the issue/test literals (1e-199, 1e-200, 0E-303, 1+300 zeros, 0.<299 zeros>1234).
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

LEAKAGE / gold-reconstruction review of django__django-11206 velvet, re-derived from scratch against the CURRENT bytes: Solution.lean sha256 88e37aa03e90975c76d78db925575da1b2df165e1dbb9610cbc49def0ad39309, Solution_prepatch.lean 01e3dae61126523f54e7c4c2e2244294aaed419ae63ce8a412e80e124b9d4c7b, properties.py 87a19be3bf6d7e984d557eb803dd1def6f68f6215ba606be20834b149131c643.

**NO RELAXATION PRESENT.** json.load(meta.json).get('relaxed_leakage') -> None (key absent); `find benchmark-verified/django__django-11206 -iname '*relax*'` -> nothing; the velvet dir holds only Solution.lean, Solution_prepatch.lean, axiom_check.py, conformance_check.py, mapping.md, meta.json, properties.py, refinement.md, verdict.md (+ transient build artifacts). There is no documented relaxation, no inherited disposition, and no unavoidability argument to re-derive; this is an ordinary strict leakage judgement, which is what I performed. (Note the task framing named a patch.diff in the velvet dir -- there is none; the gold patch lives one level up at benchmark-verified/django__django-11206/patch.diff, which is what I screened against.)

**NOTHING IN THE BUNDLE ADDRESSES ME.** leakage.reviewer_directed() -> [] on every bundle file (Solution.lean, Solution_prepatch.lean, its spec_view, mapping.md, refinement.md, meta.json, properties.py, axiom_check.py, conformance_check.py). A manual grep for reviewer/panel/verdict/submit prose across all bundle files surfaced exactly one hit -- properties.py:1180 "it is the shape an auditor reproduces from the source and finds the spec admits" -- which is uniqueness/faithfulness provenance for the `reject-threshold-exact-compare` rival, not an instruction about how to record or which verdict is honest. No finding.

SPEC VIEW COMPUTED, NOT ASSUMED. markers.spec_view(src, get_backend('velvet')) on the current bytes (sha256 of the view 4b00a54b3916...): the impl `do` body collapses to `-- implementation elided` and the prove_correct body to `-- proof elided`, so consumers see imports/set_options, the axioms region (opaque zeroRender, structure DecVal{amount:Rat, render:Option Nat -> List Char}), the pure region (renderDecimal, plainZero, ratAbs, workingDigits=28, resolution, guardCutoff, belowResolution, clampSmall), leastExponentMagnitude/positionsInExponentRange, empty post region, and the formatDecimal signature with `require positionsInExponentRange decimalPos` / `ensures out = renderDecimal (clampSmall number decimalPos) decimalPos`. markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet tables) -> True, and `diff` of the two rendered views is empty (byte-identical), so the twin's view leaks nothing the audited view does not.

MECHANICAL SCREEN (mine, re-run on current bytes). leakage.screen(src, velvet tables, patch.diff, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]; identical for the prepatch twin.

GOLD-RECONSTRUCTION CHECK, LINE BY LINE. Gold hunk adds exactly: `if decimal_pos is not None:` / two comment lines / `cutoff = Decimal('0.' + '1'.rjust(decimal_pos, '0'))` / `if abs(number) < cutoff:` / `number = Decimal('0')`. Longest-common-substring of each whitespace-normalized gold-added line against the normalized view: 7-19 chars, all English/glue ('decimal', 'decimalp', 'decimal(', '(number', 'toosmalltoaffectany') -- far under any reproduction threshold and every one of them either public in the problem_statement ('Decimal', 'number', 'decimal_pos', 'smaller in absolute size', 'provided number of decimal positions') or generic English.

Token-diff confirms: the only gold-line tokens present in the view and NOT in the problem_statement are {if, none, not, it, any, too, visible, affect} -- pure English glue plus a paraphrase of the gold's own COMMENT, whose content is verbatim the issue's own request. Zero hits in the view for: rjust, cutoff-as-Decimal-string, Decimal('0'), abs, getcontext, Emin, Etiny, as_tuple, isinstance, '{:f}', grouping, thousand_sep, decimal_sep, sign, 200, 1e-199/1e-200/1e-300, 'exponential', 'scientific', 'notation', numberformat, django, or any repo .py path (the only '.py' occurrences are the audit-artifact name axiom_check.py in provenance pointers, which name no repo file). No diff markers (@@ / +++ / diff --git / index).

Narration scan over the view's comments (`_NARRATION_RE`: bug/buggy/fix/fixed/patch/patched/regression/previously/incorrectly/wrong/broken/off-by-one) -> zero hits. Patched-file check: leakage.`_patch_changed_files` -> ['django/utils/numberformat.py'], absent from the view both as path and as dotted module. Patched-symbol check: the only changed symbol is `format`, which is public via the problem_statement string 'utils.numberformat.format', so `formatDecimal` embedding it is legitimately exempt.

**HINTS-ONLY AND TEST-PATCH ECHO.** Judged against problem_statement ONLY. Tokens in hints_text but not in the problem_statement and present in the view: {behaviour, change, it, on, so, up} -- generic English; the hints' distinctive content (commit 9cc6a60040b0..., 'Cleanup/optimization', 'minimal addition') appears nowhere. Test-patch-only tokens in the view: {def, for, py, value} -- Lean/English keywords; the test's discriminating data ('0.{}1234'.format('0'*299), '1.234e-300', '0.000', tests/utils_tests/test_numberformat.py, test_decimal_numbers) appears nowhere.

WHAT THE VIEW SAYS BEYOND THE PROBLEM_STATEMENT, AND WHY IT IS NOT LEAKAGE. Three items exceed the public text: (a) resolution p = 1/10^(max p 1) with its `max p 1` corner; (b) workingDigits = 28 and guardCutoff p = resolution p - resolution p/(`2*10`^28) with its half-ulp narration; (c) leastExponentMagnitude = 1000026 and the positionsInExponentRange precondition. None reconstructs the gold edit. (a) is the problem_statement's own threshold ('smaller in absolute size than what can be encoded using the provided number of decimal positions') made formally precise -- an `ensures` cannot exist without naming a threshold -- and it is stated as abstract behaviour, never as the `'1'.rjust(decimal_pos,'0')` string construction that produces it in the diff.

(b) and (c) point AWAY from the gold text rather than at it: the gold compares against `cutoff` = the resolution EXACTLY, so a lowered threshold and an exponent-range domain bound appear nowhere in the diff; they are emergent consequences of the ambient decimal context that the UNCHANGED `abs()` already carried, they name no repo symbol (abs, Decimal, getcontext, prec, Etiny all absent) and localize no file or line. A solver handed this view would write the clamp, not the gold's cutoff construction. Whether they are the RIGHT threshold/domain is a faithfulness question owned by G-PANEL-2/G-AX, not a leak. Bundle-internal provenance pointers ('mapping.md §2 / axiom_check.py (G-AX)') name audit artifacts, not repo paths, and disclose nothing about the edit.

LOAD-BEARING CHECK (the usual test, run by me). scripts/lean_verify.sh on Solution.lean -> verifies clean. scripts/lean_verify.sh on Solution_prepatch.lean -> FAILS at 150:28 'unsolved goals' on exactly the discriminating clause: `number.render decimalPos = (if belowResolution number decimalPos = true then { amount := 0, render := zeroRender } else number).render decimalPos`. So the clampSmall clause is a real obligation, not narration -- and crucially the behaviour it pins (below-threshold input displays as plain zero) is precisely what the PUBLIC problem_statement asks for ('the returned string should be 0.0000...000'), so the discriminator is derivable from the problem_statement alone and its presence in the spec is required faithfulness, not disclosure.

OUT OF SCOPE, RECORDED: every stamped gate except G-EQ / G-PANEL-1 / G-RESOLVE is sourced to SUPERSEDED shas (Solution.lean 82a59f98..., prepatch 7003328a..., properties.py differing), including the prior G-PANEL-3 pass and the G-PANEL/G-PANEL-2 faithfulness FAIL. I read none of those conclusions forward and my verdict rests on none of them; the two checks my layer needs (spec-region byte-identity via same_spec, and the load-bearing/verify pair via lean_verify.sh) I ran myself on the current bytes. The stamped G-PANEL-2 fail (Etiny flush-to-zero at position counts past Etiny) appears to be what the current bytes' positionsInExponentRange precondition answers, but confirming that is G-PANEL-2's job, not mine.

**CONCLUSION:** the spec view reproduces no gold-diff line, names no patched repo path/module/symbol beyond the `format` the problem_statement already publishes, echoes nothing hints-only and nothing from the test_patch, omits the exponential-notation symptom and every trace of the bug->fix mechanism, and states only abstract desired behaviour the public issue already requests. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
