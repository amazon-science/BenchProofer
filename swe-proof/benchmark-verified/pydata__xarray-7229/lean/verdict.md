# P2 adversarial audit — pydata__xarray-7229

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_01_prepatch.lean`, `atk_02_partial_domain.lean`, `atk_03_boundary_guard.lean`, `atk_04_cf_coord_dropped_promotion.lean`, `atk_05_aleg_const_flag.lean`, `atk_06_aleg_order_flip.lean`, `atk_07_aleg_reserved_off_b.lean`, `atk_08_aleg_fallthrough_top.lean`, `atk_11_produces_ignored.lean`, +1 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_09_oracle_echo.lean`, `atk_10_model_equal_reorder.lean`, `atk_13_model_equal_inline_3stage.lean`, `atk_14_model_equal_snapshot.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No same-spec implementation_where whose correct_where closes with clean axioms has a faithful patch that fails to resolve.

All 4 clean-axiom-verifying attacks had faithful patches materialized, apply-checked in a base_commit worktree (git apply --check exit 0) and EXECUTED through the official Docker oracle (run_resolve, timeout=1800, retries=1):
  atk_09_oracle_echo               resolved=True  applied=True  F2P success=[test_where_attrs]  P2P 280ok/0fail  attempts=1 flaky=False
  atk_10_model_equal_reorder       resolved=True  applied=True  F2P success=[test_where_attrs]  P2P 280ok/0fail  attempts=1 flaky=False
  atk_13_model_equal_inline_3stage resolved=True  applied=True  F2P success=[test_where_attrs]  P2P 280ok/0fail  attempts=1 flaky=False
  atk_14_model_equal_snapshot      resolved=True  applied=True  F2P success=[test_where_attrs]  P2P 280ok/0fail  attempts=1 flaky=False

DISCRIMINATION CONTROL (this is what makes the four resolved=True results meaningful): atk_01_prepatch (the PR #6461 uniform-stamp regression) had its faithful patch materialized and run the same way -> resolved=False, completed=True, attempts=2, flaky=False, note='patch did not resolve in 2 attempts (consistent - not flaky)', patch_successfully_applied=True, failing EXACTLY the F2P (FAIL_TO_PASS failure=[xarray/tests/test_computation.py::test_where_attrs]) with P2P 280ok/0fail. So the oracle discriminates on this instance rather than rubber-stamping every patch that applies.

STRUCTURAL REASON NO BREAK IS POSSIBLE: problem_spec_where is an exact equality to the TOTAL function expectedResult, and this single-valuedness is machine-checked IN-BUNDLE by spec_where_deterministic, which I re-elaborated with clean axioms in every attack file (theorem STATEMENTS verified byte-identical across all 14 attacks + control - only tactic bodies differ, so no attack can win by weakening what it must prove). Hence any same-spec impl whose correct_where closes is extensionally identical to expectedResult on BOTH the produces=true and produces=false arms, therefore to gold behavior. Such a variant is a positive control, not a spec-weakness counterexample.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_01_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -166,22 +166,11 @@
     (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do
   let mut result := select_combine cond a b keep_attrs
   if keep_attrs then
-    if b.isContainer && !a.isContainer then
-      result := { result with topAttrs := [] }
-      match a.name with
-      | some nm =>
-          result := { result with
-            dataVars := result.dataVars.map
-              (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }
-      | none => pure ()
-      result := { result with
-        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }
-    else
-      result := { result with topAttrs := a.topAttrs }
-      result := { result with
-        dataVars := result.dataVars.map (fun c => { c with attrs := lookupAttrs a c.name }) }
-      result := { result with
-        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }
+    result := { result with topAttrs := a.topAttrs }
+    result := { result with
+      dataVars := result.dataVars.map (fun c => { c with attrs := a.topAttrs }) }
+    result := { result with
+      coords := result.coords.map (fun c => { c with attrs := a.topAttrs }) }
   if produces then
     return some result
   else
@@ -229,4 +218,6 @@
   have h2 := correct_where cond a b keep_attrs produces
   unfold problem_spec_where at h h2
   rw [h, ← h2]
+#print axioms correct_where
+#print axioms spec_where_deterministic
 -- proof-end
```

Attack 2 — `atk_02_partial_domain.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -164,6 +164,11 @@
 -- impl-start
 def implementation_where
     (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do
+  -- PARTIAL DOMAIN: only rebuild where `a` HAS a like-named component.
+  let lk : Component -> Attrs := fun c =>
+    match (a.dataVars ++ a.coords).find? (fun d => d.name == c.name) with
+    | some d => d.attrs
+    | none => c.attrs
   let mut result := select_combine cond a b keep_attrs
   if keep_attrs then
     if b.isContainer && !a.isContainer then
@@ -174,14 +179,11 @@
             dataVars := result.dataVars.map
               (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }
       | none => pure ()
-      result := { result with
-        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }
+      result := { result with coords := result.coords.map (fun c => { c with attrs := lk c }) }
     else
       result := { result with topAttrs := a.topAttrs }
-      result := { result with
-        dataVars := result.dataVars.map (fun c => { c with attrs := lookupAttrs a c.name }) }
-      result := { result with
-        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }
+      result := { result with dataVars := result.dataVars.map (fun c => { c with attrs := lk c }) }
+      result := { result with coords := result.coords.map (fun c => { c with attrs := lk c }) }
   if produces then
     return some result
   else
@@ -229,4 +231,6 @@
   have h2 := correct_where cond a b keep_attrs produces
   unfold problem_spec_where at h h2
   rw [h, ← h2]
+#print axioms correct_where
+#print axioms spec_where_deterministic
 -- proof-end
```

Attack 3 — `atk_03_boundary_guard.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -166,7 +166,7 @@
     (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do
   let mut result := select_combine cond a b keep_attrs
   if keep_attrs then
-    if b.isContainer && !a.isContainer then
+    if b.isContainer then
       result := { result with topAttrs := [] }
       match a.name with
       | some nm =>
@@ -229,4 +229,6 @@
   have h2 := correct_where cond a b keep_attrs produces
   unfold problem_spec_where at h h2
   rw [h, ← h2]
+#print axioms correct_where
+#print axioms spec_where_deterministic
 -- proof-end
```

Attack 4 — `atk_04_cf_coord_dropped_promotion.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -174,8 +174,7 @@
             dataVars := result.dataVars.map
               (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }
       | none => pure ()
-      result := { result with
-        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }
+      pure ()
     else
       result := { result with topAttrs := a.topAttrs }
       result := { result with
@@ -229,4 +228,6 @@
   have h2 := correct_where cond a b keep_attrs produces
   unfold problem_spec_where at h h2
   rw [h, ← h2]
+#print axioms correct_where
+#print axioms spec_where_deterministic
 -- proof-end
```

Attack 5 — `atk_05_aleg_const_flag.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -164,7 +164,7 @@
 -- impl-start
 def implementation_where
     (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do
-  let mut result := select_combine cond a b keep_attrs
+  let mut result := select_combine cond a b true
   if keep_attrs then
     if b.isContainer && !a.isContainer then
       result := { result with topAttrs := [] }
@@ -229,4 +229,6 @@
   have h2 := correct_where cond a b keep_attrs produces
   unfold problem_spec_where at h h2
   rw [h, ← h2]
+#print axioms correct_where
+#print axioms spec_where_deterministic
 -- proof-end
```

Attack 6 — `atk_06_aleg_order_flip.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -164,6 +164,14 @@
 -- impl-start
 def implementation_where
     (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do
+  -- A-LEG ATTACK: components searched BEFORE the reserved class table.
+  let lk : String -> Attrs := fun nm =>
+    match (a.dataVars ++ a.coords).find? (fun c => c.name == nm) with
+    | some c => c.attrs
+    | none =>
+      match a.reserved.find? (fun e => e.1 == nm) with
+      | some e => e.2
+      | none => []
   let mut result := select_combine cond a b keep_attrs
   if keep_attrs then
     if b.isContainer && !a.isContainer then
@@ -174,14 +182,11 @@
             dataVars := result.dataVars.map
               (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }
       | none => pure ()
-      result := { result with
-        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }
+      result := { result with coords := result.coords.map (fun c => { c with attrs := lk c.name }) }
     else
       result := { result with topAttrs := a.topAttrs }
-      result := { result with
-        dataVars := result.dataVars.map (fun c => { c with attrs := lookupAttrs a c.name }) }
-      result := { result with
-        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }
+      result := { result with dataVars := result.dataVars.map (fun c => { c with attrs := lk c.name }) }
+      result := { result with coords := result.coords.map (fun c => { c with attrs := lk c.name }) }
   if produces then
     return some result
   else
@@ -229,4 +234,6 @@
   have h2 := correct_where cond a b keep_attrs produces
   unfold problem_spec_where at h h2
   rw [h, ← h2]
+#print axioms correct_where
+#print axioms spec_where_deterministic
 -- proof-end
```

Attack 7 — `atk_07_aleg_reserved_off_b.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -164,6 +164,14 @@
 -- impl-start
 def implementation_where
     (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do
+  -- A-LEG ATTACK: reserved class table read off `b` rather than `a`.
+  let lk : String -> Attrs := fun nm =>
+    match b.reserved.find? (fun e => e.1 == nm) with
+    | some e => e.2
+    | none =>
+      match (a.dataVars ++ a.coords).find? (fun c => c.name == nm) with
+      | some c => c.attrs
+      | none => []
   let mut result := select_combine cond a b keep_attrs
   if keep_attrs then
     if b.isContainer && !a.isContainer then
@@ -174,14 +182,11 @@
             dataVars := result.dataVars.map
               (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }
       | none => pure ()
-      result := { result with
-        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }
+      result := { result with coords := result.coords.map (fun c => { c with attrs := lk c.name }) }
     else
       result := { result with topAttrs := a.topAttrs }
-      result := { result with
-        dataVars := result.dataVars.map (fun c => { c with attrs := lookupAttrs a c.name }) }
-      result := { result with
-        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }
+      result := { result with dataVars := result.dataVars.map (fun c => { c with attrs := lk c.name }) }
+      result := { result with coords := result.coords.map (fun c => { c with attrs := lk c.name }) }
   if produces then
     return some result
   else
@@ -229,4 +234,6 @@
   have h2 := correct_where cond a b keep_attrs produces
   unfold problem_spec_where at h h2
   rw [h, ← h2]
+#print axioms correct_where
+#print axioms spec_where_deterministic
 -- proof-end
```

Attack 8 — `atk_08_aleg_fallthrough_top.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -164,6 +164,14 @@
 -- impl-start
 def implementation_where
     (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do
+  -- A-LEG ATTACK: name resolved by neither stage yields a.topAttrs, not [].
+  let lk : String -> Attrs := fun nm =>
+    match a.reserved.find? (fun e => e.1 == nm) with
+    | some e => e.2
+    | none =>
+      match (a.dataVars ++ a.coords).find? (fun c => c.name == nm) with
+      | some c => c.attrs
+      | none => a.topAttrs
   let mut result := select_combine cond a b keep_attrs
   if keep_attrs then
     if b.isContainer && !a.isContainer then
@@ -174,14 +182,11 @@
             dataVars := result.dataVars.map
               (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }
       | none => pure ()
-      result := { result with
-        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }
+      result := { result with coords := result.coords.map (fun c => { c with attrs := lk c.name }) }
     else
       result := { result with topAttrs := a.topAttrs }
-      result := { result with
-        dataVars := result.dataVars.map (fun c => { c with attrs := lookupAttrs a c.name }) }
-      result := { result with
-        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }
+      result := { result with dataVars := result.dataVars.map (fun c => { c with attrs := lk c.name }) }
+      result := { result with coords := result.coords.map (fun c => { c with attrs := lk c.name }) }
   if produces then
     return some result
   else
@@ -229,4 +234,6 @@
   have h2 := correct_where cond a b keep_attrs produces
   unfold problem_spec_where at h h2
   rw [h, ← h2]
+#print axioms correct_where
+#print axioms spec_where_deterministic
 -- proof-end
```

Attack 9 — `atk_09_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -163,29 +163,9 @@
 
 -- impl-start
 def implementation_where
-    (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do
-  let mut result := select_combine cond a b keep_attrs
-  if keep_attrs then
-    if b.isContainer && !a.isContainer then
-      result := { result with topAttrs := [] }
-      match a.name with
-      | some nm =>
-          result := { result with
-            dataVars := result.dataVars.map
-              (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }
-      | none => pure ()
-      result := { result with
-        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }
-    else
-      result := { result with topAttrs := a.topAttrs }
-      result := { result with
-        dataVars := result.dataVars.map (fun c => { c with attrs := lookupAttrs a c.name }) }
-      result := { result with
-        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }
-  if produces then
-    return some result
-  else
-    return none
+    (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj :=
+  -- UNGROUNDED ORACLE ECHO: no independent computation at all.
+  expectedResult cond a b keep_attrs produces
 -- impl-end
 
 -- proof-start
@@ -194,30 +174,7 @@
       problem_spec_where cond a b keep_attrs produces
         (implementation_where cond a b keep_attrs produces) := by
   intro cond a b keep_attrs produces
-  unfold problem_spec_where implementation_where expectedResult retainedResult
-  cases produces with
-  | false =>
-    cases keep_attrs with
-    | false => rfl
-    | true =>
-      by_cases h1 : b.isContainer && !a.isContainer
-      · simp only [Id.run, h1, if_true]
-        cases a.name with
-        | none => rfl
-        | some nm => rfl
-      · simp only [Id.run, h1]
-        rfl
-  | true =>
-    cases keep_attrs with
-    | false => rfl
-    | true =>
-      by_cases h1 : b.isContainer && !a.isContainer
-      · simp only [Id.run, h1, if_true, rebuildFrom]
-        cases a.name with
-        | none => rfl
-        | some nm => rfl
-      · simp only [Id.run, h1, rebuildFrom]
-        rfl
+  rfl
 
 /-- The post-condition is exact equality to the total function `expectedResult`,
 so any `result` satisfying it equals the implementation's output. -/
@@ -229,4 +186,6 @@
   have h2 := correct_where cond a b keep_attrs produces
   unfold problem_spec_where at h h2
   rw [h, ← h2]
+#print axioms correct_where
+#print axioms spec_where_deterministic
 -- proof-end
```

Attack 10 — `atk_10_model_equal_reorder.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -163,29 +163,31 @@
 
 -- impl-start
 def implementation_where
-    (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do
-  let mut result := select_combine cond a b keep_attrs
-  if keep_attrs then
-    if b.isContainer && !a.isContainer then
-      result := { result with topAttrs := [] }
-      match a.name with
-      | some nm =>
-          result := { result with
-            dataVars := result.dataVars.map
-              (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }
-      | none => pure ()
-      result := { result with
-        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }
-    else
-      result := { result with topAttrs := a.topAttrs }
-      result := { result with
-        dataVars := result.dataVars.map (fun c => { c with attrs := lookupAttrs a c.name }) }
-      result := { result with
-        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }
-  if produces then
-    return some result
-  else
-    return none
+    (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj :=
+  -- MODEL-EQUAL, DIFFERENT SHAPE: pure (no Id.run / no mut), coords rebuilt
+  -- BEFORE the data vars, and the top-level bag written LAST.
+  let r := select_combine cond a b keep_attrs
+  let rebuilt :=
+    if keep_attrs then
+      let withCoords :=
+        { r with coords := r.coords.map (fun (c : Component) => { c with attrs := lookupAttrs a c.name }) }
+      if b.isContainer && !a.isContainer then
+        let withDvs :=
+          match a.name with
+          | some nm =>
+              let f := fun (c : Component) =>
+                if c.name == nm then { c with attrs := a.topAttrs } else c
+              { withCoords with dataVars := withCoords.dataVars.map f }
+          | none => withCoords
+        { withDvs with topAttrs := [] }
+      else
+        let g := fun (c : Component) => { c with attrs := lookupAttrs a c.name }
+        let withDvs := { withCoords with dataVars := withCoords.dataVars.map g }
+        { withDvs with topAttrs := a.topAttrs }
+    else r
+  match produces with
+  | true => some rebuilt
+  | false => none
 -- impl-end
 
 -- proof-start
@@ -201,22 +203,22 @@
     | false => rfl
     | true =>
       by_cases h1 : b.isContainer && !a.isContainer
-      · simp only [Id.run, h1, if_true]
+      · simp only [h1, if_true, rebuildFrom]
         cases a.name with
         | none => rfl
         | some nm => rfl
-      · simp only [Id.run, h1]
+      · simp only [h1, rebuildFrom]
         rfl
   | true =>
     cases keep_attrs with
     | false => rfl
     | true =>
       by_cases h1 : b.isContainer && !a.isContainer
-      · simp only [Id.run, h1, if_true, rebuildFrom]
+      · simp only [h1, if_true, rebuildFrom]
         cases a.name with
         | none => rfl
         | some nm => rfl
-      · simp only [Id.run, h1, rebuildFrom]
+      · simp only [h1, rebuildFrom]
         rfl
 
 /-- The post-condition is exact equality to the total function `expectedResult`,
@@ -229,4 +231,6 @@
   have h2 := correct_where cond a b keep_attrs produces
   unfold problem_spec_where at h h2
   rw [h, ← h2]
+#print axioms correct_where
+#print axioms spec_where_deterministic
 -- proof-end
```

Attack 11 — `atk_11_produces_ignored.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -182,10 +182,7 @@
         dataVars := result.dataVars.map (fun c => { c with attrs := lookupAttrs a c.name }) }
       result := { result with
         coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }
-  if produces then
-    return some result
-  else
-    return none
+  return some result
 -- impl-end
 
 -- proof-start
@@ -229,4 +226,6 @@
   have h2 := correct_where cond a b keep_attrs produces
   unfold problem_spec_where at h h2
   rw [h, ← h2]
+#print axioms correct_where
+#print axioms spec_where_deterministic
 -- proof-end
```

Attack 12 — `atk_12_promotion_all_datavars.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -168,12 +168,8 @@
   if keep_attrs then
     if b.isContainer && !a.isContainer then
       result := { result with topAttrs := [] }
-      match a.name with
-      | some nm =>
-          result := { result with
-            dataVars := result.dataVars.map
-              (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }
-      | none => pure ()
+      result := { result with
+        dataVars := result.dataVars.map (fun c => { c with attrs := a.topAttrs }) }
       result := { result with
         coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }
     else
@@ -229,4 +225,6 @@
   have h2 := correct_where cond a b keep_attrs produces
   unfold problem_spec_where at h h2
   rw [h, ← h2]
+#print axioms correct_where
+#print axioms spec_where_deterministic
 -- proof-end
```

Attack 13 — `atk_13_model_equal_inline_3stage.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -162,26 +162,49 @@
 -- post-conditions-end
 
 -- impl-start
+/-- The three-stage resolution written out explicitly: class table, then the
+data-var/coord namespace, then the empty bag. -/
+def resolveInline (a : XObj) (nm : String) : Attrs :=
+  match a.reserved.find? (fun e => e.1 == nm) with
+  | some e => e.2
+  | none =>
+    match a.dataVars.find? (fun c => c.name == nm) with
+    | some c => c.attrs
+    | none =>
+      match a.coords.find? (fun c => c.name == nm) with
+      | some c => c.attrs
+      | none => []
+
+theorem resolveInline_eq (a : XObj) (nm : String) :
+    resolveInline a nm = lookupAttrs a nm := by
+  unfold resolveInline lookupAttrs
+  cases h : a.reserved.find? (fun e => e.1 == nm) with
+  | some e => simp [h]
+  | none =>
+    simp only [h, List.find?_append]
+    cases h2 : a.dataVars.find? (fun c => c.name == nm) with
+    | some c => simp [h2]
+    | none => simp [h2]
+
 def implementation_where
     (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do
   let mut result := select_combine cond a b keep_attrs
   if keep_attrs then
+    -- coords rebuilt FIRST, via the explicit inline resolution
+    result := { result with
+      coords := result.coords.map (fun c => { c with attrs := resolveInline a c.name }) }
     if b.isContainer && !a.isContainer then
-      result := { result with topAttrs := [] }
       match a.name with
       | some nm =>
           result := { result with
             dataVars := result.dataVars.map
               (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }
       | none => pure ()
+      result := { result with topAttrs := [] }
+    else
       result := { result with
-        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }
-    else
+        dataVars := result.dataVars.map (fun c => { c with attrs := resolveInline a c.name }) }
       result := { result with topAttrs := a.topAttrs }
-      result := { result with
-        dataVars := result.dataVars.map (fun c => { c with attrs := lookupAttrs a c.name }) }
-      result := { result with
-        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }
   if produces then
     return some result
   else
@@ -201,22 +224,22 @@
     | false => rfl
     | true =>
       by_cases h1 : b.isContainer && !a.isContainer
-      · simp only [Id.run, h1, if_true]
+      · simp only [Id.run, h1, if_true, rebuildFrom, resolveInline_eq]
         cases a.name with
         | none => rfl
         | some nm => rfl
-      · simp only [Id.run, h1]
+      · simp only [Id.run, h1, rebuildFrom, resolveInline_eq]
         rfl
   | true =>
     cases keep_attrs with
     | false => rfl
     | true =>
       by_cases h1 : b.isContainer && !a.isContainer
-      · simp only [Id.run, h1, if_true, rebuildFrom]
+      · simp only [Id.run, h1, if_true, rebuildFrom, resolveInline_eq]
         cases a.name with
         | none => rfl
         | some nm => rfl
-      · simp only [Id.run, h1, rebuildFrom]
+      · simp only [Id.run, h1, rebuildFrom, resolveInline_eq]
         rfl
 
 /-- The post-condition is exact equality to the total function `expectedResult`,
@@ -229,4 +252,6 @@
   have h2 := correct_where cond a b keep_attrs produces
   unfold problem_spec_where at h h2
   rw [h, ← h2]
+#print axioms correct_where
+#print axioms spec_where_deterministic
 -- proof-end
```

Attack 14 — `atk_14_model_equal_snapshot.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -162,26 +162,36 @@
 -- post-conditions-end
 
 -- impl-start
+/-- Zipping a list against its own pointwise image is a plain map. This is what
+makes the READ-ALL-THEN-WRITE-ALL shape equal the write-as-you-go one. -/
+theorem zipWith_self_map {α β γ : Type} (g : α → β → γ) (f : α → β) :
+    ∀ (l : List α), List.zipWith g l (l.map f) = l.map (fun x => g x (f x))
+  | [] => rfl
+  | x :: xs => by simp [List.zipWith, List.map, zipWith_self_map g f xs]
+
 def implementation_where
     (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do
-  let mut result := select_combine cond a b keep_attrs
+  let r := select_combine cond a b keep_attrs
+  -- READ-ALL-THEN-WRITE-ALL: every name resolved against `a` up front, into a
+  -- snapshot, before any bag is written.
+  let coordBags : List Attrs := r.coords.map (fun c => lookupAttrs a c.name)
+  let dvBags : List Attrs := r.dataVars.map (fun c => lookupAttrs a c.name)
+  let newCoords : List Component :=
+    List.zipWith (fun (c : Component) (bag : Attrs) => { c with attrs := bag }) r.coords coordBags
+  let newDvs : List Component :=
+    List.zipWith (fun (c : Component) (bag : Attrs) => { c with attrs := bag }) r.dataVars dvBags
+  let mut result := r
   if keep_attrs then
     if b.isContainer && !a.isContainer then
-      result := { result with topAttrs := [] }
-      match a.name with
-      | some nm =>
-          result := { result with
-            dataVars := result.dataVars.map
-              (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }
-      | none => pure ()
-      result := { result with
-        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }
+      let promoted : List Component :=
+        match a.name with
+        | some nm =>
+            r.dataVars.map (fun (c : Component) =>
+              if c.name == nm then { c with attrs := a.topAttrs } else c)
+        | none => r.dataVars
+      result := { r with topAttrs := [], dataVars := promoted, coords := newCoords }
     else
-      result := { result with topAttrs := a.topAttrs }
-      result := { result with
-        dataVars := result.dataVars.map (fun c => { c with attrs := lookupAttrs a c.name }) }
-      result := { result with
-        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }
+      result := { r with topAttrs := a.topAttrs, dataVars := newDvs, coords := newCoords }
   if produces then
     return some result
   else
@@ -201,22 +211,22 @@
     | false => rfl
     | true =>
       by_cases h1 : b.isContainer && !a.isContainer
-      · simp only [Id.run, h1, if_true]
+      · simp only [Id.run, h1, if_true, rebuildFrom, zipWith_self_map]
         cases a.name with
         | none => rfl
         | some nm => rfl
-      · simp only [Id.run, h1]
+      · simp only [Id.run, h1, rebuildFrom, zipWith_self_map]
         rfl
   | true =>
     cases keep_attrs with
     | false => rfl
     | true =>
       by_cases h1 : b.isContainer && !a.isContainer
-      · simp only [Id.run, h1, if_true, rebuildFrom]
+      · simp only [Id.run, h1, if_true, rebuildFrom, zipWith_self_map]
         cases a.name with
         | none => rfl
         | some nm => rfl
-      · simp only [Id.run, h1, rebuildFrom]
+      · simp only [Id.run, h1, rebuildFrom, zipWith_self_map]
         rfl
 
 /-- The post-condition is exact equality to the total function `expectedResult`,
@@ -229,4 +239,6 @@
   have h2 := correct_where cond a b keep_attrs produces
   unfold problem_spec_where at h h2
   rw [h, ← h2]
+#print axioms correct_where
+#print axioms spec_where_deterministic
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -229,4 +229,6 @@
   have h2 := correct_where cond a b keep_attrs produces
   unfold problem_spec_where at h h2
   rw [h, ← h2]
+#print axioms correct_where
+#print axioms spec_where_deterministic
 -- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Worktree at base_commit 3aa75c8d00a4a2d4acf10d80f76b937cadb666b7 created from the upstream repository, left CLEAN (git status --porcelain = 0 lines).

**SAME-SPEC:** all 14 attacks + pos_control return same_spec == True (swebench_unified.markers.same_spec, lean backend) against the shipped Solution.lean. Only impl/proof regions edited; axioms/pure/pre/post byte-identical. Both '#print axioms' lines sit INSIDE the proof region (before -- proof-end) so they do not enter the spec view.

### COMMANDS (from swe-proof):
Artifacts: exit codes <n>.exit, build logs <n>.log, patches <n>.diff, resolve JSON <n>.json, resolve logs <n>.log. Generators: gen.py, genpatch.py (writes each patch, diffs, then git checkout -- restores, so the worktree ends clean).

**POSITIVE CONTROL:** pos_control.lean (shipped impl verbatim + the two #print axioms lines) -> exit 0, correct_where axioms [propext, Quot.sound], spec_where_deterministic likewise. Clean - no sorryAx.

**PREPATCH REPRODUCED:** atk_01_prepatch.lean (uniform a.topAttrs stamp on topAttrs + every data var + every coord = the PR #6461 regression) -> exit 1, axioms [propext, sorryAx, Quot.sound]; rfl fails on the coord clause. Its faithful patch was ALSO materialized and run as the negative control -> resolved=False (details in counterexample).

REJECTED - exit 1, axioms include sorryAx (10 of 14):
  atk_01 prepatch uniform a.topAttrs stamp at all three levels
  atk_02 PARTIAL DOMAIN: rebuild only where `a` HAS a like-named component (reserved stage + empty-bag fall-through dropped; carrier's bag kept otherwise)
  atk_03 BOUNDARY: promotion guard weakened to `b.isContainer` alone (drops `&& !a.isContainer`)
  atk_04 CONTROL-FLOW EFFECT: coord rebuild dropped from the promotion leg (the gold coord loop at 1890-1892 sits OUTSIDE the if/else)
  atk_05 A-LEG constant flag: `select_combine cond a b true` - asserts a keep_attrs-invariance of the carrier the real apply_ufunc does not have
  atk_06 A-LEG resolution ORDER FLIPPED: components consulted BEFORE the reserved class table - exactly what refinement.md legs 7/8 assert
  atk_07 A-LEG reserved table read off the WRONG object (b.reserved) - machine-checked justification for `reserved` being a per-object FIELD
  atk_08 A-LEG third-stage fall-through yields a.topAttrs instead of the empty bag
  atk_11 produces IGNORED, always returns some (the no-object arm collapsed away)
  atk_12 promotion: a.name IGNORED, every data var of the promoted result gets a.topAttrs (real code touches only result[x.name])

VERIFIED WITH CLEAN AXIOMS -> FAITHFUL PATCH MATERIALIZED, APPLY-CHECKED AND RESOLVED (4 of 14): atk_09_oracle_echo.lean  UNGROUNDED-ORACLE ECHO (`implementation_where := expectedResult cond a b keep_attrs produces`, proof by rfl) -> exit 0, 'does not depend on any axioms'. patch -> resolved=True. atk_10_model_equal_reorder.lean  model-equal RETRANSCRIPTION: pure (no Id.run/no mut), coords rebuilt BEFORE data vars, top-level bag written LAST, Option built by `match produces` -> exit 0, axioms [propext].

Patch reverses the loop order and moves `result.attrs = ...` after the loops -> resolved=True. atk_13_model_equal_inline_3stage.lean  lookupAttrs spelled out as a top-level `resolveInline` def with the reserved-table stage explicit and a `resolveInline_eq` bridging lemma (via List.find?`_append`), coord rebuild first -> exit 0, axioms [propext, Quot.sound]. Patch transcribes stage 1 EXPLICITLY (object.`__getattribute__` / except AttributeError) rather than leaning on getattr's default -> resolved=True.

Strongest A-leg confirmation: the deep model's three-stage lookup, transcribed literally, is behaviourally interchangeable with the gold `getattr(getattr(x, nm, None), 'attrs', {})`. atk_14_model_equal_snapshot.lean  READ-ALL-THEN-WRITE-ALL: every name resolved against `a` into a snapshot list up front, bags written via List.zipWith, with a `zipWith_self_map` lemma bridging the two shapes -> exit 0, axioms [propext, Quot.sound]. Patch resolves all coord/var bags into lists BEFORE any mutation -> resolved=True. This one specifically probes whether interleaving reads with writes matters (it would if a written bag fed a later lookup through the `self.attrs` leg of Common.`__getattr__`); it does not, and both shapes resolve.

### A-LEG AUDIT (the R/I legs are G-CONF's job; these are mine).
A-LEG 1 (`select_combine` == the unchanged apply_ufunc combine) VERIFIED AGAINST REAL SOURCE. Confirmed bundle patch.diff is byte-identical to instance.json's gold patch, applied it in the worktree and took `git diff -U0` of computation.py: the ONLY executable changes are the `from .dataset import Dataset` import, deletion of the `keep_attrs = lambda attrs, context: getattr(x, 'attrs', {})` block, `return apply_ufunc(` -> `result = apply_ufunc(`, and the appended rebuild block.

The eight call ARGUMENTS (duck_array_ops.where, cond, x, y, join='exact', dataset_join='exact', dask='allowed', keep_attrs=keep_attrs) are untouched on both legs - so the callee is genuinely byte-identical, as A-reference requires, and no property of it is asserted (consistent with meta.json axioms=[] and the documented G-AX skip; pos_control's axioms are [propext, Quot.sound] with no callee `_prop` axiom). The Bool 4th argument is JUSTIFIED, not decorative: read apply_ufunc's own source at the cited lines 1157-1158 -> `if isinstance(keep_attrs, bool): keep_attrs = "override" if keep_attrs else "drop"`, so the carrier's own bags genuinely differ between flag values. atk_05 (constant flag) being REJECTED is the machine-checked evidence the model does not silently assume flag-invariance.

A-LEG 7/8 (`lookupAttrs` == the real 3-stage resolution) VERIFIED AGAINST REAL SOURCE. common.py Common.`__getattr__` confirmed at the cited line 271 region: it walks `self._attr_sources` and is reached ONLY when normal attribute lookup raises AttributeError, so the class table shadows a like-named variable - exactly what XObj.reserved records. Dataset.`_attr_sources` (dataset.py:1356-1360) yields `_item_sources` then self.attrs, with `_item_sources` yielding data_vars THEN coords; DataArray.`_attr_sources` (dataarray.py:841-845) yields coords then self.attrs - confirming the modelled `dataVars ++ coords` search order.

Confirmed NO `__getattribute__` override anywhere in xarray/core (grep: zero hits), which is what makes atk_13's explicit `object.__getattribute__` stage a faithful transcription of stage 1 (and its resolve=True is the behavioural proof). atk_06 (order flipped), atk_07 (reserved read off b) and atk_08 (fall-through yields a.topAttrs) are all rejected, so every facet of the three-stage model is load-bearing rather than decorative. `produces` FACET: atk_11 (arm collapsed to always-some) is rejected, so the no-object arm is not vacuous or constant-collapsible.

REFINEMENT.MD AUDIT (mandatory item 3): 9 legs, NO KIND-3. Tags parsed mechanically: leg 1 = A-reference; legs 2/3/5/6/7/8 = R; legs 4/9 = I. Tally {A-reference:1, R:6, I:2}, zero untagged, zero multi-tagged, zero A-consumed - consistent with the G-AX skip (no consumed callee axiom). Coverage checked op-by-op against the applied gold hunk: all added executable lines map onto legs 1-9 (the `from .dataset import Dataset` import is the non-semantic enabler for leg 3's isinstance test), and the removed executable lines are the lambda block (leg 2's 'lambda removal upstream of the modeled boolean') and the `return`->`result =` rename (leg 1). Nothing changed is unlegged and nothing legged is absent.

LINE CITATIONS RE-DERIVED by applying the gold patch in the worktree and reading the result: apply_ufunc call 1864-1873 (leg 1), `if keep_attrs is True:` 1879 (leg 2), promotion guard 1880 (leg 3), `result.attrs = {}` 1882 (leg 4), promote-name data var 1883-1884 (leg 5), `result.attrs = getattr(x,'attrs',{})` 1887 (leg 6), data-var loop 1888-1889 (leg 7), coord loop 1890-1892 (leg 8), `return result` 1894 (leg 9) - every one CORRECT in the shipped docs; I found no mis-citation. The apply_ufunc keep_attrs citation (1157-1158) is also correct.

PROCESS NOTE (transparency): three of my model-equal attacks initially came back exit=1, and I did NOT record them as rejections - I read the logs and found they were MY OWN defects, not spec verdicts. atk_10 failed twice on Lean syntax ('unexpected token' then 'expected structure' from an unannotated lambda binder in a structure-update); atk_14 failed on an insufficient tactic (rfl could not see through zipWith over a self-map, and an early return inside Id.run). Recording a self-inflicted syntax error or a weak tactic as 'the spec rejects this impl' would have manufactured false evidence of spec tightness. I fixed all three, re-checked same_spec, and rebuilt; all then closed with clean axioms and were carried through the resolve stage. This is why the clean-axiom count is 4 rather than 1.

**VERDICT:** SOUND (advisory). 14 same-spec attacks executed, all reaching a genuine verdict (10 rejected with sorryAx, 4 verifying with clean axioms); prepatch reproduced AND its faithful patch shown non-resolving as a discrimination control; positive control verifies with clean axioms; every one of the 4 clean-axiom-verifying attacks had its faithful patch materialized, apply-checked (git apply --check exit 0) and EXECUTED through the official harness, and all 4 RESOLVED. No verify-but-not-correct pair exists. Nothing was left unrun and no verdict rests on speculation. Worktree left clean.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_01_prepatch.lean`, `atk_02_partial_domain.lean`, `atk_03_boundary_guard.lean`, `atk_04_cf_coord_dropped_promotion.lean`, `atk_05_aleg_const_flag.lean`, `atk_06_aleg_order_flip.lean`, `atk_07_aleg_reserved_off_b.lean`, `atk_08_aleg_fallthrough_top.lean`, `atk_11_produces_ignored.lean`, +1 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_09_oracle_echo.lean`, `atk_10_model_equal_reorder.lean`, `atk_13_model_equal_inline_3stage.lean`, `atk_14_model_equal_snapshot.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No same-spec implementation_where whose correct_where closes with clean axioms has a faithful patch that fails to resolve.

All 4 clean-axiom-verifying attacks had faithful patches materialized, apply-checked in a base_commit worktree (git apply --check exit 0) and EXECUTED through the official Docker oracle (run_resolve, timeout=1800, retries=1):
  atk_09_oracle_echo               resolved=True  applied=True  F2P success=[test_where_attrs]  P2P 280ok/0fail  attempts=1 flaky=False
  atk_10_model_equal_reorder       resolved=True  applied=True  F2P success=[test_where_attrs]  P2P 280ok/0fail  attempts=1 flaky=False
  atk_13_model_equal_inline_3stage resolved=True  applied=True  F2P success=[test_where_attrs]  P2P 280ok/0fail  attempts=1 flaky=False
  atk_14_model_equal_snapshot      resolved=True  applied=True  F2P success=[test_where_attrs]  P2P 280ok/0fail  attempts=1 flaky=False

DISCRIMINATION CONTROL (this is what makes the four resolved=True results meaningful): atk_01_prepatch (the PR #6461 uniform-stamp regression) had its faithful patch materialized and run the same way -> resolved=False, completed=True, attempts=2, flaky=False, note='patch did not resolve in 2 attempts (consistent - not flaky)', patch_successfully_applied=True, failing EXACTLY the F2P (FAIL_TO_PASS failure=[xarray/tests/test_computation.py::test_where_attrs]) with P2P 280ok/0fail. So the oracle discriminates on this instance rather than rubber-stamping every patch that applies.

STRUCTURAL REASON NO BREAK IS POSSIBLE: problem_spec_where is an exact equality to the TOTAL function expectedResult, and this single-valuedness is machine-checked IN-BUNDLE by spec_where_deterministic, which I re-elaborated with clean axioms in every attack file (theorem STATEMENTS verified byte-identical across all 14 attacks + control - only tactic bodies differ, so no attack can win by weakening what it must prove). Hence any same-spec impl whose correct_where closes is extensionally identical to expectedResult on BOTH the produces=true and produces=false arms, therefore to gold behavior. Such a variant is a positive control, not a spec-weakness counterexample.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_01_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_02_partial_domain.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_03_boundary_guard.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_04_cf_coord_dropped_promotion.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_05_aleg_const_flag.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_06_aleg_order_flip.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_07_aleg_reserved_off_b.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_08_aleg_fallthrough_top.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_09_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10_model_equal_reorder.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11_produces_ignored.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_promotion_all_datavars.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_model_equal_inline_3stage.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14_model_equal_snapshot.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -229,4 +229,6 @@
   have h2 := correct_where cond a b keep_attrs produces
   unfold problem_spec_where at h h2
   rw [h, ← h2]
+#print axioms correct_where
+#print axioms spec_where_deterministic
 -- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Worktree at base_commit 3aa75c8d00a4a2d4acf10d80f76b937cadb666b7 created from the upstream repository, left CLEAN (git status --porcelain = 0 lines).

**SAME-SPEC:** all 14 attacks + pos_control return same_spec == True (swebench_unified.markers.same_spec, lean backend) against the shipped Solution.lean. Only impl/proof regions edited; axioms/pure/pre/post byte-identical. Both '#print axioms' lines sit INSIDE the proof region (before -- proof-end) so they do not enter the spec view.

### COMMANDS (from swe-proof):
Artifacts: exit codes <n>.exit, build logs <n>.log, patches <n>.diff, resolve JSON <n>.json, resolve logs <n>.log. Generators: gen.py, genpatch.py (writes each patch, diffs, then git checkout -- restores, so the worktree ends clean).

**POSITIVE CONTROL:** pos_control.lean (shipped impl verbatim + the two #print axioms lines) -> exit 0, correct_where axioms [propext, Quot.sound], spec_where_deterministic likewise. Clean - no sorryAx.

**PREPATCH REPRODUCED:** atk_01_prepatch.lean (uniform a.topAttrs stamp on topAttrs + every data var + every coord = the PR #6461 regression) -> exit 1, axioms [propext, sorryAx, Quot.sound]; rfl fails on the coord clause. Its faithful patch was ALSO materialized and run as the negative control -> resolved=False (details in counterexample).

REJECTED - exit 1, axioms include sorryAx (10 of 14):
  atk_01 prepatch uniform a.topAttrs stamp at all three levels
  atk_02 PARTIAL DOMAIN: rebuild only where `a` HAS a like-named component (reserved stage + empty-bag fall-through dropped; carrier's bag kept otherwise)
  atk_03 BOUNDARY: promotion guard weakened to `b.isContainer` alone (drops `&& !a.isContainer`)
  atk_04 CONTROL-FLOW EFFECT: coord rebuild dropped from the promotion leg (the gold coord loop at 1890-1892 sits OUTSIDE the if/else)
  atk_05 A-LEG constant flag: `select_combine cond a b true` - asserts a keep_attrs-invariance of the carrier the real apply_ufunc does not have
  atk_06 A-LEG resolution ORDER FLIPPED: components consulted BEFORE the reserved class table - exactly what refinement.md legs 7/8 assert
  atk_07 A-LEG reserved table read off the WRONG object (b.reserved) - machine-checked justification for `reserved` being a per-object FIELD
  atk_08 A-LEG third-stage fall-through yields a.topAttrs instead of the empty bag
  atk_11 produces IGNORED, always returns some (the no-object arm collapsed away)
  atk_12 promotion: a.name IGNORED, every data var of the promoted result gets a.topAttrs (real code touches only result[x.name])

VERIFIED WITH CLEAN AXIOMS -> FAITHFUL PATCH MATERIALIZED, APPLY-CHECKED AND RESOLVED (4 of 14): atk_09_oracle_echo.lean  UNGROUNDED-ORACLE ECHO (`implementation_where := expectedResult cond a b keep_attrs produces`, proof by rfl) -> exit 0, 'does not depend on any axioms'. patch -> resolved=True. atk_10_model_equal_reorder.lean  model-equal RETRANSCRIPTION: pure (no Id.run/no mut), coords rebuilt BEFORE data vars, top-level bag written LAST, Option built by `match produces` -> exit 0, axioms [propext].

Patch reverses the loop order and moves `result.attrs = ...` after the loops -> resolved=True. atk_13_model_equal_inline_3stage.lean  lookupAttrs spelled out as a top-level `resolveInline` def with the reserved-table stage explicit and a `resolveInline_eq` bridging lemma (via List.find?`_append`), coord rebuild first -> exit 0, axioms [propext, Quot.sound]. Patch transcribes stage 1 EXPLICITLY (object.`__getattribute__` / except AttributeError) rather than leaning on getattr's default -> resolved=True.

Strongest A-leg confirmation: the deep model's three-stage lookup, transcribed literally, is behaviourally interchangeable with the gold `getattr(getattr(x, nm, None), 'attrs', {})`. atk_14_model_equal_snapshot.lean  READ-ALL-THEN-WRITE-ALL: every name resolved against `a` into a snapshot list up front, bags written via List.zipWith, with a `zipWith_self_map` lemma bridging the two shapes -> exit 0, axioms [propext, Quot.sound]. Patch resolves all coord/var bags into lists BEFORE any mutation -> resolved=True. This one specifically probes whether interleaving reads with writes matters (it would if a written bag fed a later lookup through the `self.attrs` leg of Common.`__getattr__`); it does not, and both shapes resolve.

### A-LEG AUDIT (the R/I legs are G-CONF's job; these are mine).
A-LEG 1 (`select_combine` == the unchanged apply_ufunc combine) VERIFIED AGAINST REAL SOURCE. Confirmed bundle patch.diff is byte-identical to instance.json's gold patch, applied it in the worktree and took `git diff -U0` of computation.py: the ONLY executable changes are the `from .dataset import Dataset` import, deletion of the `keep_attrs = lambda attrs, context: getattr(x, 'attrs', {})` block, `return apply_ufunc(` -> `result = apply_ufunc(`, and the appended rebuild block.

The eight call ARGUMENTS (duck_array_ops.where, cond, x, y, join='exact', dataset_join='exact', dask='allowed', keep_attrs=keep_attrs) are untouched on both legs - so the callee is genuinely byte-identical, as A-reference requires, and no property of it is asserted (consistent with meta.json axioms=[] and the documented G-AX skip; pos_control's axioms are [propext, Quot.sound] with no callee `_prop` axiom). The Bool 4th argument is JUSTIFIED, not decorative: read apply_ufunc's own source at the cited lines 1157-1158 -> `if isinstance(keep_attrs, bool): keep_attrs = "override" if keep_attrs else "drop"`, so the carrier's own bags genuinely differ between flag values. atk_05 (constant flag) being REJECTED is the machine-checked evidence the model does not silently assume flag-invariance.

A-LEG 7/8 (`lookupAttrs` == the real 3-stage resolution) VERIFIED AGAINST REAL SOURCE. common.py Common.`__getattr__` confirmed at the cited line 271 region: it walks `self._attr_sources` and is reached ONLY when normal attribute lookup raises AttributeError, so the class table shadows a like-named variable - exactly what XObj.reserved records. Dataset.`_attr_sources` (dataset.py:1356-1360) yields `_item_sources` then self.attrs, with `_item_sources` yielding data_vars THEN coords; DataArray.`_attr_sources` (dataarray.py:841-845) yields coords then self.attrs - confirming the modelled `dataVars ++ coords` search order.

Confirmed NO `__getattribute__` override anywhere in xarray/core (grep: zero hits), which is what makes atk_13's explicit `object.__getattribute__` stage a faithful transcription of stage 1 (and its resolve=True is the behavioural proof). atk_06 (order flipped), atk_07 (reserved read off b) and atk_08 (fall-through yields a.topAttrs) are all rejected, so every facet of the three-stage model is load-bearing rather than decorative. `produces` FACET: atk_11 (arm collapsed to always-some) is rejected, so the no-object arm is not vacuous or constant-collapsible.

REFINEMENT.MD AUDIT (mandatory item 3): 9 legs, NO KIND-3. Tags parsed mechanically: leg 1 = A-reference; legs 2/3/5/6/7/8 = R; legs 4/9 = I. Tally {A-reference:1, R:6, I:2}, zero untagged, zero multi-tagged, zero A-consumed - consistent with the G-AX skip (no consumed callee axiom). Coverage checked op-by-op against the applied gold hunk: all added executable lines map onto legs 1-9 (the `from .dataset import Dataset` import is the non-semantic enabler for leg 3's isinstance test), and the removed executable lines are the lambda block (leg 2's 'lambda removal upstream of the modeled boolean') and the `return`->`result =` rename (leg 1). Nothing changed is unlegged and nothing legged is absent.

LINE CITATIONS RE-DERIVED by applying the gold patch in the worktree and reading the result: apply_ufunc call 1864-1873 (leg 1), `if keep_attrs is True:` 1879 (leg 2), promotion guard 1880 (leg 3), `result.attrs = {}` 1882 (leg 4), promote-name data var 1883-1884 (leg 5), `result.attrs = getattr(x,'attrs',{})` 1887 (leg 6), data-var loop 1888-1889 (leg 7), coord loop 1890-1892 (leg 8), `return result` 1894 (leg 9) - every one CORRECT in the shipped docs; I found no mis-citation. The apply_ufunc keep_attrs citation (1157-1158) is also correct.

PROCESS NOTE (transparency): three of my model-equal attacks initially came back exit=1, and I did NOT record them as rejections - I read the logs and found they were MY OWN defects, not spec verdicts. atk_10 failed twice on Lean syntax ('unexpected token' then 'expected structure' from an unannotated lambda binder in a structure-update); atk_14 failed on an insufficient tactic (rfl could not see through zipWith over a self-map, and an early return inside Id.run). Recording a self-inflicted syntax error or a weak tactic as 'the spec rejects this impl' would have manufactured false evidence of spec tightness. I fixed all three, re-checked same_spec, and rebuilt; all then closed with clean axioms and were carried through the resolve stage. This is why the clean-axiom count is 4 rather than 1.

**VERDICT:** SOUND (advisory). 14 same-spec attacks executed, all reaching a genuine verdict (10 rejected with sorryAx, 4 verifying with clean axioms); prepatch reproduced AND its faithful patch shown non-resolving as a discrimination control; positive control verifies with clean axioms; every one of the 4 clean-axiom-verifying attacks had its faithful patch materialized, apply-checked (git apply --check exit 0) and EXECUTED through the official harness, and all 4 RESOLVED. No verify-but-not-correct pair exists. Nothing was left unrun and no verdict rests on speculation. Worktree left clean.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**METHOD.** I did not trust the bundle's own conformance_check.py (it compares two Python shadows of each other, so a shared modelling error would cancel). I built an independent harness that interprets the opaque `select_combine` by CALLING THE REAL apply_ufunc(duck_array_ops.where, cond, x, y, join='exact', dataset_join='exact', dask='allowed', keep_attrs=keep_attrs) with the patch's exact arguments, abstracts the real combined object and the real xr.where output through an abstraction function derived from the source (not from mapping.md's prose), and compares topAttrs/dataVars/coords fieldwise. Reference =  at base_commit 3aa75c8 with patch.diff APPLIED (confirmed: the post-combine rebuild block is present at computation.py:1879-1892), per the briefing — I did NOT compare against the base version, which would have manufactured a false divergence on exactly the patch delta.

**ENV:**  (numpy 1.26.4 / pandas 2.1.4) + PYTHONPATH=; the repo's own venv had no xarray and system numpy 2.x breaks the import (np.unicode_).

**LEAN:** scripts/lean_verify.sh Solution.lean -> exit 0. #print axioms correct_where and spec_where_deterministic -> [propext, Quot.sound]. NO sorryAx — the proof is real, and spec_where_deterministic genuinely pins the post-condition to a single value per input, so the spec is not weakened by nondeterminism.

**SPEC REGION:** markers.region_hashes(Solution.lean, lean) reproduces the authoritative G-HYGIENE gate record byte-for-byte on all six regions (axioms 392d0bd9, impl f5579ae4, post-conditions 903f669a, proof b3081002, pure 25e99c6f, spec_view aa5d7b44). same_spec(Solution.lean, Solution_prepatch.lean) = True, so the prepatch is a genuine same-spec rival and the discriminating content is real.

PRODUCES BINDER (the one place a spec could hide over-strength or under-strength). refinement.md justifies the `produces` binder + Option XObj outcome by claiming the raising set is not record-definable. I reproduced BOTH witnesses independently rather than taking them on trust: dims='data_vars' RAISES TypeError('getattr(): attribute name must be string') while dims='d' RETURNS, with the record images of ALL THREE inputs byte-equal ({'coords': [], 'dataVars': [], 'isContainer': false, 'name': 'v', 'topAttrs': [['src','X_TOP']]}); and a coordinate named 'data_vars' RAISES at dim length 2 but RETURNS at length 0, again with equal images. The mechanism is real and matches the stated one: `data_vars` is absent from dir(DataArray) while DataArray defines `__getattr__`, so line 1888's iteration source getattr(result,'data_vars',[]) is diverted by the like-named component/dim and line 1889 calls getattr(x, <0-d DataArray>, None). So the binder is a forced modelling choice, not a hedge that buys the spec slack: on produces=true the outcome is pinned to exactly one value, and on produces=false to none.

BOOKKEEPING OBSERVATION (not a faithfulness defect, out of scope for this gate, flagged for the record only): meta.json's TOP-LEVEL 'region_hashes' key holds a stale set of digests (spec_view cc46f2be..., impl 99aed27c..., etc.) that does NOT match the current Solution.lean, while the G-HYGIENE gate record's data.region_hashes — the copy scripts/check_stamp_freshness.py actually reads as authority — matches exactly. The live freshness authority agrees with the artifact; the vestigial top-level copy is a different vintage. This changes nothing about the spec's faithfulness, and I did not treat it as a finding.

**CONCLUSION.** The spec is neither too strong nor drifted. Every op in the changed region is modeled at the right depth: the two-stage getattr resolution is modeled rather than idealized to a variable-namespace lookup (which is precisely the bug the PR fixes and where an unfaithful spec would most plausibly hide), the per-class nature of the reserved table is correct, the promotion shape's asymmetry is correct, and the keep_attrs=False leg returns the combine verbatim as the real code does. select_combine is legitimately opaque: it is byte-identical on both legs, no property of it is asserted, and my harness fed the REAL callee's output to the spec so the stand-in could not launder an error. Verdict FAITHFUL.

Counterexample / evidence:

```
None. Adversarial probes attempted and all CONFIRMED FAITHFUL:

[A] lookupAttrs three-stage resolution (the op-8 coord clause, the heart of the patch). Verified `reserved` is genuinely PER-CLASS as mapping.md claims, by object.__getattribute__ probe (stage-1 = 'normal lookup SUCCEEDS'): DataArray reserves T/real/imag/variable/dims/values; Dataset reserves real/imag/dims/values but NOT T and NOT variable; _cache falls through on BOTH (unset slot -> AttributeError -> __getattr__ -> keeps own bag). Read out live: DataArray coord 'T' -> {'src':'X_TOP'} (x's TOP bag, the view answer) vs unreserved coord 'k' -> {'own':'OWN_k'} (its own). Exactly rebuildFrom/lookupAttrs.

[B] Promotion branch (b.isContainer && !a.isContainer). x.name in [None,'v','w','zzz','k','T'], plus scalar x and Variable x (Variable has NO .name attribute at all -> getattr(x,'name',None) is None -> Lean's `| none => r.dataVars` arm). All matched: top bag emptied, ONLY the name-matching data var gets a.topAttrs, siblings keep the carrier bag, coords still rebuilt via lookupAttrs. Also y Dataset with a data var literally named None + unnamed x: real code puts x.attrs on result[None] and Lean's Option String `none` arm leaves it — checked, no divergence in the modeled record.

[C] The cond-is-a-Dataset case, which is NOT the promotion shape: result is a container while a is not, yet the guard is false so the else-branch rebuilds data vars off a non-container a. 70/70 agree, including data-var names colliding with a's coord names and with reserved names.

[D] Order sensitivity: re-ran the differential with an ORDER-PRESERVING abstraction (insertion order, not sorted) so an Attrs list-ordering drift could not be masked. 50/50 agree.

[E] MultiIndex coords (level names as coords, writes through IndexVariable) and dimension coords (IndexVariable) named d/T/real/dims/values/k/name/attrs/_cache/coords/data_vars: 120/121 ok, the 1 non-ok being a raise (produces=false), not a mismatch.

[F] 4000-input randomized fuzz over {Dataset, DataArray, Variable, scalar}^3 x keep_attrs, name pool mixing reserved/unreserved/raising names: 3222 object-yielding all matched, 649 raised inside the combine itself, 129 raised in the rebuild (produces=false). 0 mismatches.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**FACET RE-CONFIRMED INDEPENDENTLY:** the container-promotion structural exception (spec view lines 36-42 prose + 125-134 executable, the `else if b.isContainer && !a.isContainer` branch of `retainedResult`) is the sole disclosure beyond the public problem_statement, and it is the exact facet RELAXED_LEAKAGE.md covers. Everything below is my own measurement, not the file's assertion.

**ARTIFACT IDENTITY.** markers.spec_view / region_hashes / same_spec via LeanBackend() on the shipped files: Solution.lean sha256 880d1f91a65b8997... (matches the file RELAXED_LEAKAGE.md describes and every gate's `sources` entry). spec_view = 170 lines, sha aa5d7b44edf16a6a. All six region hashes reproduce G-HYGIENE's recorded data.region_hashes exactly (axioms 392d0bd933569869, pure 25e99c6fb9a8f58c, post-conditions 903f669a40e59359, impl f5579ae4390a0563, proof b3081002cd482e9f, spec_view aa5d7b44edf16a6a). markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend()) = True, so every clause I quote quotes BOTH twins. RELAXED_LEAKAGE.md sha ab07114fb87eef7a matches G-LEAK's sources entry.

STALE HASH BLOCK — checked, benign. meta.json's TOP-LEVEL region_hashes block (axioms 75564a41..., spec_view cc46f2be...) matches NEITHER shipped file. RELAXED_LEAKAGE.md discloses this itself (build-time record of an earlier revision, not recomputed on re-gate; only markers.region_hashes tracks disk) and that account is exactly what I measured. Bookkeeping artifact, not tampering or a substituted artifact.

### UNAVOIDABILITY RE-DERIVED FROM SCRATCH (variants built by me in a mktemp -d; bundle and repo tree unmodified; no git stash):
(a) STRIP TEST, the one the brief prescribes. A_specstrip.lean = shipped Solution.lean with ONLY the promotion branch deleted from `retainedResult`; impl+proof regions byte-unchanged -> lean_verify EXIT=1, `unsolved goals` / rfl failure, residual goal shows the promotion-shape LHS (topAttrs := [], dataVars mapped on a.name) against the uniform-rebuild RHS (topAttrs := a.topAttrs). The removed clause is LOAD-BEARING, not narration: the gold-faithful impl does not verify against a promotion-free spec, so G-GOLD would fail.

(b) B_bothstrip2.lean = that promotion-free spec with the impl also de-faceted to the ordinary path alone (coordinate rebuild byte-intact) and the proof re-closed (`cases produces <;> cases keep_attrs <;> rfl`) -> EXIT=0. So a promotion-free spec DOES admit a verifying implementation.

(c) REAL REPO, my own run. Container from swebench/sweb.eval.x86_64.pydata_1776_xarray-7229:latest, /testbed checked out to base_commit 3aa75c8d00a4a2d4acf10d80f76b937cadb666b7, patch.diff + instance test_patch applied (both `git apply --check` clean, verified post-patch source at computation.py:1876-1892). Positive control (unmodified gold): `pytest xarray/tests/test_computation.py::test_where_attrs -x -q` -> 1 passed in 1.25s. Then I replaced the promotion branch with the ordinary path (`if True:` fill-global-and-data_vars), leaving the coordinate loop byte-intact -> 1 FAILED at test_computation.py:1984, `Left and right Dataset objects are not identical / Attributes only on the right object: attr: x_da`, on the F2P's own last block `xr.where(cond, x.rename("x"), ds_y, keep_attrs=True)`.
Composing (b)+(c): a spec without this clause verifies an implementation whose repository counterpart fails the sole FAIL_TO_PASS test — exactly what verify => correct forbids. Unavoidability holds on the F2P leg. FAIL_TO_PASS is the single test above, so there is no other leg to satisfy.

§4 SELF-REFUTATION CONFIRMED, AND IT IS HONEST. The file declines the usual prepatch-strip rationale and says so. I checked: C_nopromo_prepatch2.lean = promotion-free spec + Solution_prepatch.lean's impl region grafted verbatim + a real tactic -> EXIT=1, residual goal a genuine `attrs := a.topAttrs` (LHS) vs `attrs := lookupAttrs a c.name` (RHS) mismatch on BOTH dataVars and coords. So the coordinate clause ALONE rejects the twin and the twin discrimination survives without the promotion facet — the prepatch-strip test genuinely does not settle this bundle, and §4's refutation of velvet/RELAXED_LEAKAGE.md is correct. I read velvet/RELAXED_LEAKAGE.md:55, which does argue "removing the promotion facet would make the prepatch pass and break G-DIFF"; that rationale is false here and the lean file refutes rather than inherits it. A cross-leg sibling claim is not inherited (different modeled method / different sha).

**NO PS-ONLY DERIVATION OF THE DISCRIMINATOR.** Token counts over this instance's instance.json, my own run: `promot` 0, `special` 0, `data_var`/`data variable` 0, `container` 0, `x.name`/`own name` 0, `empt` 0, `isinstance` 0, `top-level` 0, `global` 0 — in problem_statement AND hints_text. `Dataset` case-SENSITIVE: 0 in the statement; the two case-insensitive `dataset` substrings are `xr.tutorial.load_dataset("air_temperature")` and the attrs-dump key `'dataset': 'NMC Reanalysis'` — I read both in context, unrelated. The statement carries only `coord` x3 / `preserv` x1, i.e. the public same-type behaviour over `xr.where(True, ds.air, ds.air, keep_attrs=True)`. The promotion case's only homes are the gold diff and the hidden test_patch. The surrounding rebuild-by-name rule IS PS-derivable (title + "Coordinate attributes should be preserved") and is not a disclosure.

**NOTHING LEAKS BEYOND THAT FACET.** Lexical scan of the 170-line spec view for repo vocabulary: zero hits for xarray, computation.py, apply_ufunc, getattr, isinstance, Dataset, DataArray, data_vars, duck_array, lambda, 6461, fix, bug, patch, regress. leakage.screen(Solution.lean, LeanBackend(), gold_patch, problem_statement) -> passed=True, hard_failures=[], warnings=[]; `_patch_changed_symbols` = {'where'}, public in the statement title.

I re-derived §5's five non-disclosure rows rather than accepting them: (i) the carrier takes the retention flag — I read base computation.py:1865-1874 at 3aa75c8d and it already passes `keep_attrs=keep_attrs`, so pre-patch/public; (ii) flag false -> verbatim — pre-patch behaviour; (iii) rebuild from the SECOND argument by name — PS-derivable, and the base docstring at computation.py:1791 already says "If True, keep the attrs of `x`"; (iv) `reserved`/`lookupAttrs` — faithfulness-forced, and I MEASURED it on gold: a coordinate named real/T/imag/variable yields x's TOP-LEVEL bag while dims/shape yield {} — real callee behaviour any natural implementation exhibits, stated abstractly with no Python/getattr/class vocabulary, and not an F2P discriminator (the F2P coordinate is named `a`); (v) `produces` — a partiality binder disclosing no shape.

**MINIMALITY MEASUREMENTS REPRODUCED.** §5's two rejected reductions are real, measured by me on gold in the image: with cond a Dataset and x,y plain DataArrays, type(result)==Dataset while isinstance(y,Dataset)==False and the real call takes the OTHER branch — result.attrs=={'attr':'x_da'} (NOT emptied), data_var 'v' {}, coord 'a' {'attr':'x_coord'}. So a result-side guard (`r.isContainer && !a.isContainer`) would be UNFAITHFUL, and the third-argument guard the view states is the accurate one. The weaker phrasing "every other data variable keeps whatever bag the combination routine gave it" is likewise the accurate statement.

CORE GATES SOUND (the disposition leans on these, so I probed them). G-VERIFY: my own lean_verify.sh on shipped Solution.lean -> EXIT=0; appended `#print axioms` -> correct_where and spec_where_deterministic BOTH depend on [propext, Quot.sound], NO sorryAx, so the proof is real and the postcondition is single-valued (a same-spec passing variant is a positive control, not a weakness).

G-DIFF NOT VACUOUS-BY-SORRY — I checked this specifically because Solution_prepatch.lean exits 3 on a literal `sorry` (line 187) rather than a hard error: I grafted the gold tactic script onto the prepatch impl (EXIT=1, genuine rfl failure) and attempted a brute-force close (EXIT=1), then built I_eval.lean with a CONCRETE carrier and evaluated the three semantics directly — spec vs prepatch differ on coords ([("attr","x_COORD")] vs [("attr","x_TOP")]), promotion-free spec vs prepatch also differ, and shipped spec vs promotion-free spec differ on the promotion witness (topAttrs [] vs [("attr","x_TOP")]). The prepatch sorry is genuinely uncloseable, so G-DIFF's "verification failed" is sound.

Also pass: G-GOLD, G-HYGIENE, G-INTEGRITY (instance.json byte-identical, additions-only), G-MUT 20/20, G-PBT SOUND 13 cases, G-CONF 120000 inputs seed 7229 0 disagreements, G-AX skip (select_combine is an A-reference, the unchanged apply_ufunc combine; meta axioms list empty), G-RESOLVE resolved, G-EQ pass, G-PANEL-1 pass, G-PANEL-2 FAITHFUL.

**NO BUNDLE FILE STEERS THIS ROLE.** I ran leakage.reviewer_directed() over every file in the lean bundle (RELAXED_LEAKAGE.md, Solution.lean, Solution_prepatch.lean, mapping.md, refinement.md, meta.json, verdict.md, properties.py, conformance_check.py, axiom_check.py): [] for all ten — no addresses-the-reviewer, prescribes-the-verdict, or recording-convention hit. RELAXED_LEAKAGE.md argues its case and names which gates would catch a hole (G-EQ, G-PANEL-1) but never tells me what to submit; it also states its own staleness condition ("if either hash stops matching, this file is stale"), which I checked and which holds. Treated as a claim throughout, not a disposition.

ONE CITATION DISCREPANCY, not disqualifying: §6 of RELAXED_LEAKAGE.md cites G-EQ as "23 admissible attacks re-run of 23 submitted" while the current meta.json G-EQ/G-PANEL-1 records read "19 admissible attacks re-run of 22 submitted" (re-stamped 17:20 under a later code_version, recheck reason "spec-edit"). The file's §6 count is stale relative to the re-stamp; G-EQ status is pass on both records and the file itself defers to meta.json as the authority, so the disposition is intact. Flagging it as a bookkeeping drift for the record, not as a leak.

**CONCLUSION:** the relaxation's argument holds on the leg it claims (F2P / verify => correct), the discriminator is not derivable from the problem_statement or hints_text, the spec view leaks nothing beyond the promotion facet the relaxation covers, and the core gates it leans on are sound under my own probing. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
