# P2 adversarial audit — pydata__xarray-6744

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4b.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_14.lean`, `nd_a.lean`, `atk_prepatch.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pc_base.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. 14 distinct same-spec wrong impls + the prepatch bug were verified; every value-level, boundary, control-flow, partial-domain, vacuity and divergence attack was REJECTED. The single verifying attack (atk_7, the ungrounded-oracle echo returning endsSeq/beginsSeq verbatim) had its faithful refined patch materialized and RUN through the official harness: run_resolve('pydata__xarray-6744', patch_atk7.diff, timeout=2400, retries=0) => RESOLVED=True COMPLETED=True NOTE='resolved', with all 3 FAIL_TO_PASS succeeding and 0 F2P failures. A verifying attack whose patch RESOLVES is a correct echo of the gold, not a spec weakness. No verifying wrong impl has a faithful patch that fails to resolve, so verify=>correct is not falsified for this bundle.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -86,7 +86,7 @@
       decreasing i
     do
       let p := labels[i - 1]!
-      result := endAt p w center :: result
+      result := (p + (w + 1) / 2) :: result
       i := i - 1
     return result
     -- impl-end
@@ -108,9 +108,7 @@
       decreasing i
     do
       let p := labels[i - 1]!
-      let raw := endAt p w center - w
-      let s : Int := if raw > 0 then raw else 0
-      result := s :: result
+      result := (if (p + (w + 1) / 2) - w > 0 then (p + (w + 1) / 2) - w else 0) :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -86,7 +86,7 @@
       decreasing i
     do
       let p := labels[i - 1]!
-      result := endAt p w center :: result
+      result := (p + (if center then w / 2 else 1)) :: result
       i := i - 1
     return result
     -- impl-end
@@ -108,9 +108,7 @@
       decreasing i
     do
       let p := labels[i - 1]!
-      let raw := endAt p w center - w
-      let s : Int := if raw > 0 then raw else 0
-      result := s :: result
+      result := (let e := p + (if center then w / 2 else 1); if e - w > 0 then e - w else 0) :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -108,9 +108,7 @@
       decreasing i
     do
       let p := labels[i - 1]!
-      let raw := endAt p w center - w
-      let s : Int := if raw > 0 then raw else 0
-      result := s :: result
+      result := (endAt p w center - w) :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 4 — `atk_4b.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -87,7 +87,7 @@
     do
       let p := labels[i - 1]!
       result := endAt p w center :: result
-      i := i - 1
+      i := i - 2
     return result
     -- impl-end
 
@@ -108,10 +108,8 @@
       decreasing i
     do
       let p := labels[i - 1]!
-      let raw := endAt p w center - w
-      let s : Int := if raw > 0 then raw else 0
-      result := s :: result
-      i := i - 1
+      result := beginAt p w center :: result
+      i := i - 2
     return result
     -- impl-end
 
@@ -143,11 +141,19 @@
   rw [hcons, beginsSeq_cons]
 
 prove_correct blockEnds by
-  loom_solve
-  rw [endsSeq_drop_step w center (positions n) i (by omega) (by omega)]
-  simp_all
+  loom_solve <;>
+    first
+      | rfl
+      | omega
+      | (simp_all [endsSeq, beginsSeq, endAt, beginAt, endShift, positions]; try omega)
+      | grind
+      | trivial
 
 prove_correct blockBegins by
-  loom_solve
-  rw [beginsSeq_drop_step w center (positions n) i (by omega) (by omega)]
-  simp_all [beginAt]
+  loom_solve <;>
+    first
+      | rfl
+      | omega
+      | (simp_all [endsSeq, beginsSeq, endAt, beginAt, endShift, positions]; try omega)
+      | grind
+      | trivial
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -83,11 +83,8 @@
       invariant 0 ≤ i ∧ i ≤ labels.length
       invariant result = endsSeq w center (labels.drop i)
       done_with i = 0
-      decreasing i
     do
-      let p := labels[i - 1]!
-      result := endAt p w center :: result
-      i := i - 1
+      result := result
     return result
     -- impl-end
 
@@ -105,13 +102,8 @@
       invariant 0 ≤ i ∧ i ≤ labels.length
       invariant result = beginsSeq w center (labels.drop i)
       done_with i = 0
-      decreasing i
     do
-      let p := labels[i - 1]!
-      let raw := endAt p w center - w
-      let s : Int := if raw > 0 then raw else 0
-      result := s :: result
-      i := i - 1
+      result := result
     return result
     -- impl-end
 
@@ -144,10 +136,8 @@
 
 prove_correct blockEnds by
   loom_solve
-  rw [endsSeq_drop_step w center (positions n) i (by omega) (by omega)]
-  simp_all
+  all_goals simp_all [endsSeq, beginsSeq, endAt, beginAt, endShift]
 
 prove_correct blockBegins by
   loom_solve
-  rw [beginsSeq_drop_step w center (positions n) i (by omega) (by omega)]
-  simp_all [beginAt]
+  all_goals simp_all [endsSeq, beginsSeq, endAt, beginAt, endShift]
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -79,15 +79,14 @@
     let labels := positions n
     let mut result : List Int := []
     let mut i := labels.length
+    let mut j : Int := 1
     while i > 0
       invariant 0 ≤ i ∧ i ≤ labels.length
       invariant result = endsSeq w center (labels.drop i)
       done_with i = 0
-      decreasing i
+      decreasing j
     do
-      let p := labels[i - 1]!
-      result := endAt p w center :: result
-      i := i - 1
+      j := j - 1
     return result
     -- impl-end
 
@@ -101,17 +100,14 @@
     let labels := positions n
     let mut result : List Int := []
     let mut i := labels.length
+    let mut j : Int := 1
     while i > 0
       invariant 0 ≤ i ∧ i ≤ labels.length
       invariant result = beginsSeq w center (labels.drop i)
       done_with i = 0
-      decreasing i
+      decreasing j
     do
-      let p := labels[i - 1]!
-      let raw := endAt p w center - w
-      let s : Int := if raw > 0 then raw else 0
-      result := s :: result
-      i := i - 1
+      j := j - 1
     return result
     -- impl-end
 
@@ -144,10 +140,8 @@
 
 prove_correct blockEnds by
   loom_solve
-  rw [endsSeq_drop_step w center (positions n) i (by omega) (by omega)]
-  simp_all
+  all_goals simp_all [endsSeq, beginsSeq, endAt, beginAt, endShift]
 
 prove_correct blockBegins by
   loom_solve
-  rw [beginsSeq_drop_step w center (positions n) i (by omega) (by omega)]
-  simp_all [beginAt]
+  all_goals simp_all [endsSeq, beginsSeq, endAt, beginAt, endShift]
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,19 +76,7 @@
   ensures out = endsSeq w center (positions n)
   do
     -- impl-start
-    let labels := positions n
-    let mut result : List Int := []
-    let mut i := labels.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ labels.length
-      invariant result = endsSeq w center (labels.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let p := labels[i - 1]!
-      result := endAt p w center :: result
-      i := i - 1
-    return result
+    return endsSeq w center (positions n)
     -- impl-end
 
 /- The per-position block START indices: w entries before each end, clamped to
@@ -98,21 +86,7 @@
   ensures out = beginsSeq w center (positions n)
   do
     -- impl-start
-    let labels := positions n
-    let mut result : List Int := []
-    let mut i := labels.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ labels.length
-      invariant result = beginsSeq w center (labels.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let p := labels[i - 1]!
-      let raw := endAt p w center - w
-      let s : Int := if raw > 0 then raw else 0
-      result := s :: result
-      i := i - 1
-    return result
+    return beginsSeq w center (positions n)
     -- impl-end
 
 /- The backward-fold step for block ends: dropping one fewer position exposes
@@ -144,10 +118,6 @@
 
 prove_correct blockEnds by
   loom_solve
-  rw [endsSeq_drop_step w center (positions n) i (by omega) (by omega)]
-  simp_all
 
 prove_correct blockBegins by
   loom_solve
-  rw [beginsSeq_drop_step w center (positions n) i (by omega) (by omega)]
-  simp_all [beginAt]
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -85,9 +85,7 @@
       done_with i = 0
       decreasing i
     do
-      let p := labels[i - 1]!
-      result := endAt p w center :: result
-      i := i - 1
+      result := result
     return result
     -- impl-end
 
@@ -107,11 +105,7 @@
       done_with i = 0
       decreasing i
     do
-      let p := labels[i - 1]!
-      let raw := endAt p w center - w
-      let s : Int := if raw > 0 then raw else 0
-      result := s :: result
-      i := i - 1
+      result := result
     return result
     -- impl-end
 
@@ -144,10 +138,8 @@
 
 prove_correct blockEnds by
   loom_solve
-  rw [endsSeq_drop_step w center (positions n) i (by omega) (by omega)]
-  simp_all
+  all_goals simp_all [endsSeq, beginsSeq, endAt, beginAt, endShift]
 
 prove_correct blockBegins by
   loom_solve
-  rw [beginsSeq_drop_step w center (positions n) i (by omega) (by omega)]
-  simp_all [beginAt]
+  all_goals simp_all [endsSeq, beginsSeq, endAt, beginAt, endShift]
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -108,9 +108,7 @@
       decreasing i
     do
       let p := labels[i - 1]!
-      let raw := endAt p w center - w
-      let s : Int := if raw > 0 then raw else 0
-      result := s :: result
+      result := (let raw := endAt p w center - w; if raw > 1 then raw else 0) :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -79,7 +79,7 @@
     let labels := positions n
     let mut result : List Int := []
     let mut i := labels.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ labels.length
       invariant result = endsSeq w center (labels.drop i)
       done_with i = 0
@@ -101,16 +101,14 @@
     let labels := positions n
     let mut result : List Int := []
     let mut i := labels.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ labels.length
       invariant result = beginsSeq w center (labels.drop i)
       done_with i = 0
       decreasing i
     do
       let p := labels[i - 1]!
-      let raw := endAt p w center - w
-      let s : Int := if raw > 0 then raw else 0
-      result := s :: result
+      result := beginAt p w center :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -78,16 +78,17 @@
     -- impl-start
     let labels := positions n
     let mut result : List Int := []
-    let mut i := labels.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ labels.length
-      invariant result = endsSeq w center (labels.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let p := labels[i - 1]!
-      result := endAt p w center :: result
-      i := i - 1
+    if w < 0 then
+      let mut i := labels.length
+      while i > 0
+        invariant 0 ≤ i ∧ i ≤ labels.length
+        invariant result = endsSeq w center (labels.drop i)
+        done_with i = 0
+        decreasing i
+      do
+        let p := labels[i - 1]!
+        result := endAt p w center :: result
+        i := i - 1
     return result
     -- impl-end
 
@@ -100,18 +101,17 @@
     -- impl-start
     let labels := positions n
     let mut result : List Int := []
-    let mut i := labels.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ labels.length
-      invariant result = beginsSeq w center (labels.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let p := labels[i - 1]!
-      let raw := endAt p w center - w
-      let s : Int := if raw > 0 then raw else 0
-      result := s :: result
-      i := i - 1
+    if w < 0 then
+      let mut i := labels.length
+      while i > 0
+        invariant 0 ≤ i ∧ i ≤ labels.length
+        invariant result = beginsSeq w center (labels.drop i)
+        done_with i = 0
+        decreasing i
+      do
+        let p := labels[i - 1]!
+        result := beginAt p w center :: result
+        i := i - 1
     return result
     -- impl-end
 
@@ -143,11 +143,19 @@
   rw [hcons, beginsSeq_cons]
 
 prove_correct blockEnds by
-  loom_solve
-  rw [endsSeq_drop_step w center (positions n) i (by omega) (by omega)]
-  simp_all
+  loom_solve <;>
+    first
+      | rfl
+      | omega
+      | (simp_all [endsSeq, beginsSeq, endAt, beginAt, endShift, positions]; try omega)
+      | grind
+      | trivial
 
 prove_correct blockBegins by
-  loom_solve
-  rw [beginsSeq_drop_step w center (positions n) i (by omega) (by omega)]
-  simp_all [beginAt]
+  loom_solve <;>
+    first
+      | rfl
+      | omega
+      | (simp_all [endsSeq, beginsSeq, endAt, beginAt, endShift, positions]; try omega)
+      | grind
+      | trivial
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -86,7 +86,7 @@
       decreasing i
     do
       let p := labels[i - 1]!
-      result := endAt p w center :: result
+      result := (p + (if w = 1 then 1 else (if center then w else 1))) :: result
       i := i - 1
     return result
     -- impl-end
@@ -108,9 +108,7 @@
       decreasing i
     do
       let p := labels[i - 1]!
-      let raw := endAt p w center - w
-      let s : Int := if raw > 0 then raw else 0
-      result := s :: result
+      result := (let e := p + (if w = 1 then 1 else (if center then w else 1)); if e - w > 0 then e - w else 0) :: result
       i := i - 1
     return result
     -- impl-end
@@ -143,11 +141,19 @@
   rw [hcons, beginsSeq_cons]
 
 prove_correct blockEnds by
-  loom_solve
-  rw [endsSeq_drop_step w center (positions n) i (by omega) (by omega)]
-  simp_all
+  loom_solve <;>
+    first
+      | rfl
+      | omega
+      | (simp_all [endsSeq, beginsSeq, endAt, beginAt, endShift, positions]; try omega)
+      | grind
+      | trivial
 
 prove_correct blockBegins by
-  loom_solve
-  rw [beginsSeq_drop_step w center (positions n) i (by omega) (by omega)]
-  simp_all [beginAt]
+  loom_solve <;>
+    first
+      | rfl
+      | omega
+      | (simp_all [endsSeq, beginsSeq, endAt, beginAt, endShift, positions]; try omega)
+      | grind
+      | trivial
```

Attack 13 — `atk_14.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -78,16 +78,16 @@
     -- impl-start
     let labels := positions n
     let mut result : List Int := []
-    let mut i := labels.length
-    while i > 0
+    let mut i := 0
+    while i < labels.length
       invariant 0 ≤ i ∧ i ≤ labels.length
-      invariant result = endsSeq w center (labels.drop i)
-      done_with i = 0
-      decreasing i
+      invariant result = endsSeq w center ((labels.take i).reverse)
+      done_with i = labels.length
+      decreasing labels.length - i
     do
-      let p := labels[i - 1]!
+      let p := labels[i]!
       result := endAt p w center :: result
-      i := i - 1
+      i := i + 1
     return result
     -- impl-end
 
@@ -100,18 +100,16 @@
     -- impl-start
     let labels := positions n
     let mut result : List Int := []
-    let mut i := labels.length
-    while i > 0
+    let mut i := 0
+    while i < labels.length
       invariant 0 ≤ i ∧ i ≤ labels.length
-      invariant result = beginsSeq w center (labels.drop i)
-      done_with i = 0
-      decreasing i
+      invariant result = beginsSeq w center ((labels.take i).reverse)
+      done_with i = labels.length
+      decreasing labels.length - i
     do
-      let p := labels[i - 1]!
-      let raw := endAt p w center - w
-      let s : Int := if raw > 0 then raw else 0
-      result := s :: result
-      i := i - 1
+      let p := labels[i]!
+      result := beginAt p w center :: result
+      i := i + 1
     return result
     -- impl-end
 
@@ -143,11 +141,19 @@
   rw [hcons, beginsSeq_cons]
 
 prove_correct blockEnds by
-  loom_solve
-  rw [endsSeq_drop_step w center (positions n) i (by omega) (by omega)]
-  simp_all
+  loom_solve <;>
+    first
+      | rfl
+      | omega
+      | (simp_all [endsSeq, beginsSeq, endAt, beginAt, endShift, positions]; try omega)
+      | grind
+      | trivial
 
 prove_correct blockBegins by
-  loom_solve
-  rw [beginsSeq_drop_step w center (positions n) i (by omega) (by omega)]
-  simp_all [beginAt]
+  loom_solve <;>
+    first
+      | rfl
+      | omega
+      | (simp_all [endsSeq, beginsSeq, endAt, beginAt, endShift, positions]; try omega)
+      | grind
+      | trivial
```

Attack 14 — `nd_a.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,19 +76,8 @@
   ensures out = endsSeq w center (positions n)
   do
     -- impl-start
-    let labels := positions n
-    let mut result : List Int := []
-    let mut i := labels.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ labels.length
-      invariant result = endsSeq w center (labels.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let p := labels[i - 1]!
-      result := endAt p w center :: result
-      i := i - 1
-    return result
+    let out :| List.length out = n
+    return out
     -- impl-end
 
 /- The per-position block START indices: w entries before each end, clamped to
@@ -98,21 +87,8 @@
   ensures out = beginsSeq w center (positions n)
   do
     -- impl-start
-    let labels := positions n
-    let mut result : List Int := []
-    let mut i := labels.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ labels.length
-      invariant result = beginsSeq w center (labels.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let p := labels[i - 1]!
-      let raw := endAt p w center - w
-      let s : Int := if raw > 0 then raw else 0
-      result := s :: result
-      i := i - 1
-    return result
+    let out :| List.length out = n
+    return out
     -- impl-end
 
 /- The backward-fold step for block ends: dropping one fewer position exposes
@@ -143,11 +119,19 @@
   rw [hcons, beginsSeq_cons]
 
 prove_correct blockEnds by
-  loom_solve
-  rw [endsSeq_drop_step w center (positions n) i (by omega) (by omega)]
-  simp_all
+  loom_solve <;>
+    first
+      | rfl
+      | omega
+      | (simp_all [endsSeq, beginsSeq, endAt, beginAt, endShift, positions]; try omega)
+      | grind
+      | trivial
 
 prove_correct blockBegins by
-  loom_solve
-  rw [beginsSeq_drop_step w center (positions n) i (by omega) (by omega)]
-  simp_all [beginAt]
+  loom_solve <;>
+    first
+      | rfl
+      | omega
+      | (simp_all [endsSeq, beginsSeq, endAt, beginAt, endShift, positions]; try omega)
+      | grind
+      | trivial
```

Attack 15 — `atk_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -85,8 +85,10 @@
       done_with i = 0
       decreasing i
     do
+      -- Pre-image skeleton: every block end is its position plus one, regardless
+      -- of the justification mode (the centred flag is never consulted here).
       let p := labels[i - 1]!
-      result := endAt p w center :: result
+      result := (p + 1) :: result
       i := i - 1
     return result
     -- impl-end
@@ -107,8 +109,11 @@
       done_with i = 0
       decreasing i
     do
+      -- Pre-image skeleton: the block end uses the same position-plus-one rule,
+      -- so the start is its position-plus-one minus the window size, clamped to
+      -- the start of the sequence; the centred flag is never consulted.
       let p := labels[i - 1]!
-      let raw := endAt p w center - w
+      let raw := (p + 1) - w
       let s : Int := if raw > 0 then raw else 0
       result := s :: result
       i := i - 1
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_base.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

SCRATCH= (all work confined there; own base_commit worktree, git worktree add --detach 7cc6cc991e586a6158bb656b8001234ccda25407).

same_spec=True and unsound_evasions=NONE (admissible) mechanically confirmed for ALL 15 submitted attacks + both positive controls, via swebench_unified.markers.same_spec + variant_scope.unsound_evasions with get_backend('velvet').language.

### POSITIVE CONTROLS (both exit 0):
- pc_base.lean = byte-identical copy of canonical Solution.lean. `bash scripts/lean_verify.sh pc_base.lean` => EXIT 0.
- pc2_strongtail.lean (second control, correct impls + canonical proof) => EXIT 0. This rules out my tactic scripts being the cause of the rejections below.

### ATTACK BATTERY (all: `bash scripts/lean_verify.sh <f>.lean`; run concurrently 4 at a time):
1. atk_1.lean PARTIAL-DOMAIN: always the centred shift (w+1)/2, ignoring `center` -> wrong for center=False, w>=2. EXIT 1 (rejected; unsolved goals on invariant_2/ensures).
2. atk_2.lean BOUNDARY: floor w/2 instead of ceil (w+1)/2 when centred. EXIT 1 (rejected).
3. atk_3.lean BOUNDARY: blockBegins drops the clamp to 0, negative starts leak. EXIT 1 (rejected).
4. atk_4b.lean CONTROL-FLOW-EFFECT: stride 2 (i := i - 2), half the positions emitted. EXIT 1 (rejected). NOTE: an earlier atk_4.lean failed on the FROZEN `rw` tactic rather than the spec, so it was re-encoded as atk_4b with a permissive proof tail (loom_solve <;> first | rfl | omega | simp_all[...] | grind | trivial) to guarantee the rejection is attributable to the SPEC. atk_4.lean is NOT submitted.
5. atk_5.lean DIVERGENCE/VACUITY: no-op body (result := result), `decreasing` clause OMITTED. EXIT 1 (rejected) — 'error: Decreasing annotations are required in total correctness semantics'.
6. atk_6.lean DIVERGENCE: no-op body with an unbounded-below descending Int measure (j := j - 1). EXIT 1 (rejected) — decreasingGadget type mismatch + unsolved 'decreasing_1: j'; the measure must be well-founded.
7. atk_7.lean UNGROUNDED-ORACLE ECHO: returns endsSeq/beginsSeq (the spec function) verbatim, no loop. EXIT 0 (VERIFIES). => mandatory resolve run performed, see below.
8. atk_8.lean CONTROL for the divergence mechanism: no-op body with an HONEST `decreasing i`. EXIT 1 (rejected, unsolved 'decreasing_1: i') — proves `decreasing` is genuinely enforced and atk_5/atk_6 were not vacuous passes.
9. atk_9.lean BOUNDARY: clamp threshold raw>1 instead of raw>0 (off-by-one at position w-offset). EXIT 1 (rejected).
10. atk_10.lean LENGTH: loop stops at i>1, dropping position 0. EXIT 1 (rejected).
11. atk_11.lean VACUITY via infeasible guard: whole body under `if w < 0` which `require w > 0` makes unreachable, so result stays []. EXIT 1 (rejected) — the guarded-self-call vacuity route is closed.
12. atk_12.lean PARTIAL-DOMAIN: correct only at w=1, shift w when centred otherwise. EXIT 1 (rejected).
13. atk_14.lean ORDERING: correct values in REVERSED order (forward walk, prepend). EXIT 1 (rejected) — the spec pins order, which the real traversal's zip() against window_labels needs.
14. nd_a.lean UNGROUNDED-ORACLE / demonic nondeterministic choice: `let out :| List.length out = n` — any list of the right LENGTH. EXIT 1 (rejected); the residual goal is exactly `i = endsSeq w center (...)` given only `choice_1 : i.length = n`, i.e. the postcondition pins the VALUE, not merely the shape. (An earlier atk_13.lean used bad `:|` syntax and failed to ELABORATE, so it proved nothing about the spec and is NOT submitted; nd_a is its correctly-elaborating replacement.)
15. atk_prepatch.lean PREPATCH BUG re-encoded (shift 1 always, `center` never consulted — the copied bundle Solution_prepatch.lean). EXIT 1 (rejected) => prepatch_reproduced=True.

### MANDATORY RESOLVE RUN (the only verifying attack):
- Faithful refined patch for atk_7 materialized at patch_atk7.diff. atk_7 returns the deep model's closed forms, so the faithful refinement writes endShift/endAt/beginAt directly as a per-position comprehension (end_shift = (window0+1)//2 if center else 1; stops = [i+end_shift ...]; starts = [max(0, s-window0) ...]) rather than the gold's arange/slice-assign — same values, different shape, which is exactly what a refinement-fidelity attack should test.
- `git apply --check patch_atk7.diff` in the base_commit worktree => APPLIES CLEAN at 7cc6cc99.
- `run_resolve('pydata__xarray-6744', patch, timeout=2400, retries=0)` => RESOLVED=True, COMPLETED=True, NOTE='resolved', patch_successfully_applied=True, FAIL_TO_PASS success=3 / failure=0. => correct echo, NOT a spec weakness (per `_derive_audit_verdict` a BROKEN break requires completed AND not resolved).

### A-LEG AUDIT (my assigned focus; refinement.md + mapping.md):
- meta.json axioms=[] and the axioms region contains only a comment — there is genuinely NO consumed axiom, so there is no A-consumed leg to trust. Confirmed no `axiom`/`opaque`/`unsafe`/`extern` token anywhere in Solution.lean.
- The single A-reference leg (endShift/endAt/beginAt vs the gold patch's offset/END/START arrays) I re-derived INDEPENDENTLY of the bundle's own axiom_check.py: transcribed patch.diff's arange/subtract/slice-assign arithmetic in plain Python and compared against the model on the full boundary sweep (n 0..24, w 1..24, both center flags) plus 200,000 randomized (n,w,center) fuzz cases => 0 mismatches. I also checked the one algebra claim mapping.md §3.2 rests on: `w - offset < 0` (which would make the leading slice-assign a negative bound and break the clamp equivalence) never occurs for w >= 1 under either center flag — verified exhaustively for w in 1..59. The clamp identity START[i] = max(0, offset+i-window0) = beginAt i therefore holds on the whole declared domain.
- refinement.md leg tags audited: A1,A2,A3,A5,B2 = R; A4,B1 = A-reference + I; B3 = I (algebraically). Every leg is R / A-reference / I. NO kind-3 (unexpressible-changed-op) step, matching §D's claim, and the one changed operation (the index arithmetic) is modelled deeply rather than hidden behind an axiom. The A-reference's correspondence to the real callee holds as re-measured above.
- Modeling-boundary check: site C (slicing / count-mask / labelled emission) is genuinely unchanged by patch.diff, so treating it as the unchanged caller is correct; the patch's only other edits are a return-type annotation widening and a local rename, both behaviour-preserving and correctly carrying no model node.

**WHY THE PRIOR PASS'S DIVERGENCE LOOPHOLE IS CLOSED HERE:** the earlier recorded audit's atk_9 exploited `set_option loom.semantics.termination "partial"`, under which a non-terminating no-op verifies vacuously. This bundle's frozen spec view sets termination "total", and I confirmed mechanically (atk_5 omitted-measure, atk_6 non-well-founded Int measure, atk_8 honest-but-false measure) that all three divergence routes are REJECTED. No inconclusive-non-break divergence artifact exists for this spec, so unlike the prior pass this SOUND verdict rests on no out-of-scope carve-out.

**FLOOR:** 15 admissible attacks submitted (>= 5 required), prepatch reproduced, positive control verifies, and the one candidate's resolve run COMPLETED. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4b.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_14.lean`, `nd_a.lean`, `atk_prepatch.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pc_base.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. 14 distinct same-spec wrong impls + the prepatch bug were verified; every value-level, boundary, control-flow, partial-domain, vacuity and divergence attack was REJECTED. The single verifying attack (atk_7, the ungrounded-oracle echo returning endsSeq/beginsSeq verbatim) had its faithful refined patch materialized and RUN through the official harness: run_resolve('pydata__xarray-6744', patch_atk7.diff, timeout=2400, retries=0) => RESOLVED=True COMPLETED=True NOTE='resolved', with all 3 FAIL_TO_PASS succeeding and 0 F2P failures. A verifying attack whose patch RESOLVES is a correct echo of the gold, not a spec weakness. No verifying wrong impl has a faithful patch that fails to resolve, so verify=>correct is not falsified for this bundle.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4b.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_14.lean` → rejected (same spec, does not verify — good)

Attack 14 — `nd_a.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_base.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

SCRATCH= (all work confined there; own base_commit worktree, git worktree add --detach 7cc6cc991e586a6158bb656b8001234ccda25407).

same_spec=True and unsound_evasions=NONE (admissible) mechanically confirmed for ALL 15 submitted attacks + both positive controls, via swebench_unified.markers.same_spec + variant_scope.unsound_evasions with get_backend('velvet').language.

### POSITIVE CONTROLS (both exit 0):
- pc_base.lean = byte-identical copy of canonical Solution.lean. `bash scripts/lean_verify.sh pc_base.lean` => EXIT 0.
- pc2_strongtail.lean (second control, correct impls + canonical proof) => EXIT 0. This rules out my tactic scripts being the cause of the rejections below.

### ATTACK BATTERY (all: `bash scripts/lean_verify.sh <f>.lean`; run concurrently 4 at a time):
1. atk_1.lean PARTIAL-DOMAIN: always the centred shift (w+1)/2, ignoring `center` -> wrong for center=False, w>=2. EXIT 1 (rejected; unsolved goals on invariant_2/ensures).
2. atk_2.lean BOUNDARY: floor w/2 instead of ceil (w+1)/2 when centred. EXIT 1 (rejected).
3. atk_3.lean BOUNDARY: blockBegins drops the clamp to 0, negative starts leak. EXIT 1 (rejected).
4. atk_4b.lean CONTROL-FLOW-EFFECT: stride 2 (i := i - 2), half the positions emitted. EXIT 1 (rejected). NOTE: an earlier atk_4.lean failed on the FROZEN `rw` tactic rather than the spec, so it was re-encoded as atk_4b with a permissive proof tail (loom_solve <;> first | rfl | omega | simp_all[...] | grind | trivial) to guarantee the rejection is attributable to the SPEC. atk_4.lean is NOT submitted.
5. atk_5.lean DIVERGENCE/VACUITY: no-op body (result := result), `decreasing` clause OMITTED. EXIT 1 (rejected) — 'error: Decreasing annotations are required in total correctness semantics'.
6. atk_6.lean DIVERGENCE: no-op body with an unbounded-below descending Int measure (j := j - 1). EXIT 1 (rejected) — decreasingGadget type mismatch + unsolved 'decreasing_1: j'; the measure must be well-founded.
7. atk_7.lean UNGROUNDED-ORACLE ECHO: returns endsSeq/beginsSeq (the spec function) verbatim, no loop. EXIT 0 (VERIFIES). => mandatory resolve run performed, see below.
8. atk_8.lean CONTROL for the divergence mechanism: no-op body with an HONEST `decreasing i`. EXIT 1 (rejected, unsolved 'decreasing_1: i') — proves `decreasing` is genuinely enforced and atk_5/atk_6 were not vacuous passes.
9. atk_9.lean BOUNDARY: clamp threshold raw>1 instead of raw>0 (off-by-one at position w-offset). EXIT 1 (rejected).
10. atk_10.lean LENGTH: loop stops at i>1, dropping position 0. EXIT 1 (rejected).
11. atk_11.lean VACUITY via infeasible guard: whole body under `if w < 0` which `require w > 0` makes unreachable, so result stays []. EXIT 1 (rejected) — the guarded-self-call vacuity route is closed.
12. atk_12.lean PARTIAL-DOMAIN: correct only at w=1, shift w when centred otherwise. EXIT 1 (rejected).
13. atk_14.lean ORDERING: correct values in REVERSED order (forward walk, prepend). EXIT 1 (rejected) — the spec pins order, which the real traversal's zip() against window_labels needs.
14. nd_a.lean UNGROUNDED-ORACLE / demonic nondeterministic choice: `let out :| List.length out = n` — any list of the right LENGTH. EXIT 1 (rejected); the residual goal is exactly `i = endsSeq w center (...)` given only `choice_1 : i.length = n`, i.e. the postcondition pins the VALUE, not merely the shape. (An earlier atk_13.lean used bad `:|` syntax and failed to ELABORATE, so it proved nothing about the spec and is NOT submitted; nd_a is its correctly-elaborating replacement.)
15. atk_prepatch.lean PREPATCH BUG re-encoded (shift 1 always, `center` never consulted — the copied bundle Solution_prepatch.lean). EXIT 1 (rejected) => prepatch_reproduced=True.

### MANDATORY RESOLVE RUN (the only verifying attack):
- Faithful refined patch for atk_7 materialized at patch_atk7.diff. atk_7 returns the deep model's closed forms, so the faithful refinement writes endShift/endAt/beginAt directly as a per-position comprehension (end_shift = (window0+1)//2 if center else 1; stops = [i+end_shift ...]; starts = [max(0, s-window0) ...]) rather than the gold's arange/slice-assign — same values, different shape, which is exactly what a refinement-fidelity attack should test.
- `git apply --check patch_atk7.diff` in the base_commit worktree => APPLIES CLEAN at 7cc6cc99.
- `run_resolve('pydata__xarray-6744', patch, timeout=2400, retries=0)` => RESOLVED=True, COMPLETED=True, NOTE='resolved', patch_successfully_applied=True, FAIL_TO_PASS success=3 / failure=0. => correct echo, NOT a spec weakness (per `_derive_audit_verdict` a BROKEN break requires completed AND not resolved).

### A-LEG AUDIT (my assigned focus; refinement.md + mapping.md):
- meta.json axioms=[] and the axioms region contains only a comment — there is genuinely NO consumed axiom, so there is no A-consumed leg to trust. Confirmed no `axiom`/`opaque`/`unsafe`/`extern` token anywhere in Solution.lean.
- The single A-reference leg (endShift/endAt/beginAt vs the gold patch's offset/END/START arrays) I re-derived INDEPENDENTLY of the bundle's own axiom_check.py: transcribed patch.diff's arange/subtract/slice-assign arithmetic in plain Python and compared against the model on the full boundary sweep (n 0..24, w 1..24, both center flags) plus 200,000 randomized (n,w,center) fuzz cases => 0 mismatches. I also checked the one algebra claim mapping.md §3.2 rests on: `w - offset < 0` (which would make the leading slice-assign a negative bound and break the clamp equivalence) never occurs for w >= 1 under either center flag — verified exhaustively for w in 1..59. The clamp identity START[i] = max(0, offset+i-window0) = beginAt i therefore holds on the whole declared domain.
- refinement.md leg tags audited: A1,A2,A3,A5,B2 = R; A4,B1 = A-reference + I; B3 = I (algebraically). Every leg is R / A-reference / I. NO kind-3 (unexpressible-changed-op) step, matching §D's claim, and the one changed operation (the index arithmetic) is modelled deeply rather than hidden behind an axiom. The A-reference's correspondence to the real callee holds as re-measured above.
- Modeling-boundary check: site C (slicing / count-mask / labelled emission) is genuinely unchanged by patch.diff, so treating it as the unchanged caller is correct; the patch's only other edits are a return-type annotation widening and a local rename, both behaviour-preserving and correctly carrying no model node.

**WHY THE PRIOR PASS'S DIVERGENCE LOOPHOLE IS CLOSED HERE:** the earlier recorded audit's atk_9 exploited `set_option loom.semantics.termination "partial"`, under which a non-terminating no-op verifies vacuously. This bundle's frozen spec view sets termination "total", and I confirmed mechanically (atk_5 omitted-measure, atk_6 non-well-founded Int measure, atk_8 honest-but-false measure) that all three divergence routes are REJECTED. No inconclusive-non-break divergence artifact exists for this spec, so unlike the prior pass this SOUND verdict rests on no out-of-scope carve-out.

**FLOOR:** 15 admissible attacks submitted (>= 5 required), prepatch reproduced, positive control verifies, and the one candidate's resolve run COMPLETED. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ATTACK LANE:** faithfulness-break (spec too strong / drifts from real repo behavior). No divergence found; verdict FAITHFUL.

**REFERENCE DISCIPLINE:** built a fresh worktree of pydata_xarray.git at base_commit 7cc6cc991e586a6158bb656b8001234ccda25407 and applied patch.diff (APPLIED = the modeled function's reference, per the brief). Base commit used only as the reference for untouched callees; the patch delta itself was NOT reported as drift.

**SPEC-REGION INTEGRITY:** markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True. The four SPEC_REGIONS (axioms/pure/pre-conditions/post-conditions) plus signatures and contracts are byte-identical, so the G-DIFF discriminator is a real one and the spec I audited is the frozen spec. axioms region is genuinely empty (no consumed axiom to trust). scripts/lean_verify.sh on Solution.lean: exit 0, no sorry/error.

REAL-REPO DIFFERENTIAL (the primary evidence, executed against the patched worktree, not a transliteration): monkeypatched DataArray.isel to spy on the exact half-open slice bounds the patched `__iter__` hands to obj.isel({dim0: slice(start, stop)}), and compared them element-wise to the model's (beginAt i, endAt i) = (max(0, i+offset-w), i+offset).
  - Exhaustive grid n in 0..25 x w in 1..25 x center in {False,True}, plus 600 seeded random (n<=60, w<=60) cases = 1900 inputs. ZERO mismatches, including stop > n on the centred right edge (the spy sees the untruncated bound exactly as computed).
  - Pure-int reimplementation of the patch's arange/subtract/slice-assign over n in 0..39 x w in 1..39 x both flags: zero mismatches.

EDGE PROBES AIMED AT 'TOO STRONG':
  1. Lean Int division vs Python floor-div. endShift = (w+1)/2 (Lean T-division, truncates toward zero) vs offset = (window0+1)//2 (Python floor). Since require w > 0 forces w+1 > 0, both operands are positive and trunc = floor = euclid all coincide. #eval confirmed endShift over w=1..20 equals (w+1)/2 pointwise; spot checks w=1 -> 1 (centred collapses to uncentred, matching the patch), w=2 -> 1, w=3 -> 2, w=7 -> 4. No off-by-one on even windows.
  2. The negative-numpy-slice trap. The patch writes starts[: window0 - offset] = 0; if window0-offset were negative, numpy would zero a PREFIX of length n-|k| rather than nothing, and max(0,.) would diverge. Swept w in 1..199 x both flags: window0-offset is never negative (offset=(w+1)//2 <= w for w>=1; w=1 centred gives exactly 0 -> [:0] zeroes nothing). Every zeroed entry (i < w-offset) is provably negative and every untouched entry (i >= w-offset) provably >= 0, so the slice-assign is exactly max(0,.) -- refinement.md B3's algebra holds, including when n < w-offset (slice overruns, all entries negative, both give 0).
  3. n-binding drift. The patch changed the length source from len(window_labels) to obj.sizes[dim0] while zip still walks window_labels; the model collapses both to a single n. Tried to separate them: no coordinate on the dim, 2-D object with 1-d rolling, MultiIndex dim, datetime64 coord, auxiliary non-dim coord. len(window_labels) == sizes[dim] in every constructible case (a 2-D coord sharing a dim name is rejected upstream by MissingDimensionsError), and all range comparisons matched. The single-n model is faithful.
  4. int64 overflow / silent wraparound. Swept w at `2**31`, `2**62`+/-1, `2**63`-2, `2**63`-1 for n in {0,1,3}: model matches real exactly. Beyond `2**63` the real code raises OverflowError (outside any reachable domain, and outside the spec's observable range) -- no silent wrap where the model would claim a value.
  5. Precondition width. require w > 0 is neither too strong nor too weak: Rolling.`__init__` raises ValueError('window must be > 0') for w <= 0, so w > 0 is the exact accepted domain. n : Nat covers every size >= 0 (n=0 verified: both produce []).

BUNDLE CHECKS RE-RUN INDEPENDENTLY against the patched worktree (not trusting the stamped meta.json): axiom_check.py exit 0 (200234 cases, 0 mismatch); conformance_check.py exit 0 (4064 inputs, seed 6744, 0 disagreements). FAIL_TO_PASS test_rolling_iter re-run under the patched tree: 2 passed, 2 skipped (the two skips are the dask-parameterized variants, dask absent in this env; the numpy centred cases that discriminate the fix both pass).

**CONCLUSION:** the frozen postconditions out = endsSeq/beginsSeq w center (positions n) pin each index to the centre-aware closed form that the patched repo actually computes, on every input satisfying w > 0. I found no input on which the modeled function disagrees with the real patched callee, and no place where the spec demands more than the repo delivers. The pure helpers are exactly the patch's offset/END/START arithmetic; the declared modeling boundary (the raw START/END arrays, with the slicing/masking/emission tail as unchanged caller) is confirmed by direct observation of the real slice bounds. No faithfulness defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

LEAKAGE / GOLD-RECONSTRUCTION audit of pydata__xarray-6744/velvet. Verdict NO-LEAKAGE.

**NO RELAXATION IN PLAY.** There is no RELAXED_LEAKAGE.md in this bundle and meta.json has no `relaxed_leakage` key (confirmed by json key dump: keys are additional_change_sites, axioms, base_commit, changed_files, conf_skip, deep_model_references, gates, instance_id, modeled_functions, prepatch_models, repo, schema_version, spec_provenance, string_modeling, version). So this is a plain leakage judgement, not an inherited disposition. (Note: the task prompt lists `patch.diff` as a bundle file; it is absent here, as it is in all 500 benchmark-verified/*/velvet dirs -- `ls benchmark-verified/*/velvet/patch.diff` matches 0 of 500. Not a defect of this cell; refinement.md's reference to `patch.diff` is a corpus-wide convention naming the frozen gold row, which I read from data/swe_bench_verified/test.jsonl instead.)

### WHAT I MEASURED (not asserted):

1. **SPEC REGION FROZEN.** markers.same_spec(Solution.lean, Solution_prepatch.lean, get_backend('velvet')) == True. Stronger: I diffed the two rendered spec_views and they are BYTE-IDENTICAL (diff empty). So the spec text I judge is exactly the text the pre-patch rival is held to -- the discriminator lives in the frozen spec, not in a re-authored spec.

2. G-DIFF SOUNDNESS RE-RUN MYSELF (the load-bearing test). scripts/lean_verify.sh Solution.lean -> EXIT=0 (verifies clean, no sorry/error). scripts/lean_verify.sh Solution_prepatch.lean -> EXIT=1 with exactly two unsolved goals, both the centering discriminator and nothing else:
  `(positions n)[i-1]?.getD 0 + 1 = endAt ((positions n)[i-1]?.getD 0) w center`  (blockEnds)
  `(if w < ...+1 then ...+1-w else 0) = if w < endAt ... then endAt ... - w else 0`  (blockBegins)
So the endShift clause is LOAD-BEARING, not narration: strip the centred shift and the spec admits the pre-patch impl. A spec that omitted it would not discriminate.

3. **MECHANICAL SCREEN CLEAN.** leakage.screen(Solution.lean, velvet, gold_patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. Judged against problem_statement only, never hints_text (hints_text is empty for this row anyway, len 0). Gold changed_symbols = {'iter'}; changed_files = xarray/core/rolling.py. Neither the file path, the dotted module path, nor `__iter__` appears in the spec view. I also hand-grepped the spec view for repo-internal tokens: rolling, offset, stops, starts, window_labels, arange, isel, min_periods, DataArray, sizes, np., dim0, window0, slice, count, yield, xarray -- ZERO hits except English prose 'block starts'/'block starts: same peel' (the word 'starts' as a noun, not the gold's `starts` array) and 'ceil' in a math identity. No diff markers, no bug/fix narration.

4. THE REAL QUESTION -- IS THE DISCRIMINATOR PUBLICLY DERIVABLE? The one clause a leakage attacker must challenge is the pure-region line `def endShift (w : Int) (center : Bool) : Int := if center then (w + 1) / 2 else 1`, i.e. offset = ceil(w/2) when centred. This is byte-for-byte the gold's `offset = (window0 + 1) // 2 if self.center[0] else 1`. Does naming it hand over a choice the solver could not otherwise make? NO -- it is pinned twice over by PUBLIC information:
  (a) The problem_statement itself demands the equivalence: it shows `my_data.rolling(x=3, center=True).mean()` returning [nan,2,3,...,8,nan] and the manual iteration returning [nan,nan,2,...,8], and asks for the manual path to give centre-justified windows. So 'manual iteration must agree with the vectorised centred reduction' is fully public, including the n=9,w=3 worked numbers.
  (b) The vectorised centred path is UNCHANGED repo code the solver reads at base_commit, and it fixes the offset for EVERY w -- including even w, where the convention is a genuine free choice and the only place a spec could smuggle in gold-specific information. I derived END[i]-i from two independent unchanged paths in my own worktree (git worktree add at 7cc6cc99):
    - xarray/core/variable.py rolling_window: `if cent: start = win // 2; end = win - 1 - start`, so output i covers original [i-start, i-start+win), giving END[i]-i = win - win//2.
    - xarray/core/rolling.py `_bottleneck_reduce` (unchanged by the gold hunk): `shift = (-window//2) + 1`, valid = slice(-shift, None), giving END[p]-p = (-shift)+1.
  Both equal (w+1)//2 for every w in 1..12, even and odd alike (w=2->1, w=4->2, w=6->3, w=8->4, w=10->5, w=12->6). So ceil(w/2) is not the gold patch's private convention; it is the convention the unchanged codebase already implements and that the issue's requested equivalence forces. Restating it in the spec discloses nothing the solver cannot read off public repo code plus the public issue.

5. **NO GOLD-EDIT FORM DISCLOSED.** The spec expresses the clamp as `beginAt = if raw > 0 then raw else 0` (mathematical max(0,.)), NOT the gold's `starts[: window0 - offset] = 0` slice-assign. That is the strictly more general/behavioural formulation -- refinement.md B3 has to argue the two are algebraically equal, which is exactly the work a spec should leave to the refinement map. The spec view also carries no hint of WHICH function to edit beyond what the issue already says ('manually iterating over a DataArrayRolling', 'the window iterator'): it speaks only of a generic 'one-dimensional moving-window traversal', names no repo symbol, and elides all impl/proof bodies ('implementation elided -- supplied by the consumer').

6. **NO BUNDLE-TO-REVIEWER STEERING.** leakage.reviewer_directed() is clean ([]) on refinement.md, mapping.md, verdict.md and meta.json. I additionally hand-grepped every bundle file for reviewer/auditor/panel/'honest'/'record as'/'verdict is' directives: the only hits are innocuous topical prose (conformance_check.py:47 'record the EXACT half-open index range'; properties.py:53 'cover honestly'). Nothing in this bundle addresses me or tells me what to submit.

7. **CORE GATES.** meta.json gates all pass (G-AX, G-CONF, G-DIFF, G-EQ, G-GOLD, G-HYGIENE, G-INTEGRITY, G-LEAK, G-MUT, G-PBT, G-RESOLVE, G-VERIFY), and I independently re-ran the two that this verdict leans on -- G-VERIFY and G-DIFF (item 2) -- rather than trusting the stamp.

**FACET RE-CONFIRMED:** the centred-shift discriminator (endShift = ceil(w/2)) is the one gold-coincident fact the spec view states, it is load-bearing (prepatch fails without it), and it is independently derivable from the public problem_statement plus unchanged base_commit code in two places. Everything else in the spec view is generic index arithmetic and proof scaffolding. Nothing leaks beyond the public problem statement.

**CLEANUP:** the scratch worktree I created (*) is removed; I did not touch the pre-existing * worktree (it carries another role's modified rolling.py) and I ran no tree-wide git operation.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
