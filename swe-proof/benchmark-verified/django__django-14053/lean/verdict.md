# P2 adversarial audit — django__django-14053

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 18 admissible attacks re-run of 18 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 18 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_12.lean`, `atk_16.lean`, `atk_18.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 8 | `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_11.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean`, `atk_17.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (18):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,67 +127,26 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_postProcess (adjustable : List String) (firstPass : List PassRecord)
     (laterPasses : List (List PassRecord)) : OutReport := Id.run do
+  -- PRE-PATCH orchestration (the bug the gold patch fixes): every record of
+  -- every pass is handed to the caller as it is produced; nothing is collected
+  -- and nothing is held back for after the mapping is committed, so a file
+  -- processed in more than one pass is handed over more than once.
   let mut early : List OutItem := []
-  let mut collected : List (String × OutItem) := []
+  let mut unsettled : Bool := false
   for r in firstPass do
-    if (! adjustable.contains r.name) || r.isError then
-      early := early ++ [r.toItem]
-    else
-      collected := upsertItem collected r.name r.toItem
-  let mut unsettled : Bool := false
+    early := early ++ [r.toItem]
   for pass in laterPasses do
     unsettled := pass.any (fun r => r.rewrote)
     for r in pass do
-      collected := upsertItem collected r.name r.toItem
-  return (early ++ (if unsettled then [allowanceItem] else []), collected.map (·.2))
+      early := early ++ [r.toItem]
+  return (early ++ (if unsettled then [allowanceItem] else []), [])
 -- impl-end
 
 
 -- proof-start
-theorem first_loop_eq_foldl (adjustable : List String) (firstPass : List PassRecord) :
-    (forIn firstPass (⟨[], []⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-        Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) ([], [])).2,
-          (firstPass.foldl (firstStep adjustable) ([], [])).1⟩ := by
-  have key : ∀ (o : List OutItem) (d : List (String × OutItem)),
-      (forIn firstPass (⟨d, o⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-          Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) (o, d)).2,
-          (firstPass.foldl (firstStep adjustable) (o, d)).1⟩ := by
-    intro o d
-    induction firstPass generalizing o d with
-    | nil => rfl
-    | cons r rs ih =>
-      simp only [List.forIn_cons, List.foldl_cons, firstStep]
-      split <;> simp_all
-  exact key [] []
-
-theorem later_loops_eq_foldl (laterPasses : List (List PassRecord))
-    (c : List (String × OutItem)) (b : Bool) :
-    List.foldl
-        (fun (st : MProd (List (String × OutItem)) Bool) (pass : List PassRecord) =>
-          ⟨pass.foldl (fun d r => upsertItem d r.name r.toItem) st.fst,
-            pass.any (fun r => r.rewrote)⟩)
-        ⟨c, b⟩ laterPasses
-      = ⟨(laterPasses.foldl laterStep (c, b)).1,
-          (laterPasses.foldl laterStep (c, b)).2⟩ := by
-  induction laterPasses generalizing c b with
-  | nil => rfl
-  | cons pass rest ih =>
-    simp only [List.foldl_cons, laterStep]
-    exact ih _ _
 
 theorem correct_postProcess :
     ∀ (adjustable : List String) (firstPass : List PassRecord)
@@ -198,6 +157,6 @@
   intro adjustable firstPass laterPasses _
   unfold problem_spec_postProcess implementation_postProcess postProcessModel
   simp only [Id.run, bind_pure_comp, map_pure, List.forIn_pure_yield_eq_foldl,
-    first_loop_eq_foldl, later_loops_eq_foldl]
-  rfl
+    List.foldl_map]
+  simp [firstStep, laterStep, upsertItem, PassRecord.toItem, PassRecord.isError]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,67 +127,18 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_postProcess (adjustable : List String) (firstPass : List PassRecord)
-    (laterPasses : List (List PassRecord)) : OutReport := Id.run do
-  let mut early : List OutItem := []
-  let mut collected : List (String × OutItem) := []
-  for r in firstPass do
-    if (! adjustable.contains r.name) || r.isError then
-      early := early ++ [r.toItem]
-    else
-      collected := upsertItem collected r.name r.toItem
-  let mut unsettled : Bool := false
-  for pass in laterPasses do
-    unsettled := pass.any (fun r => r.rewrote)
-    for r in pass do
-      collected := upsertItem collected r.name r.toItem
-  return (early ++ (if unsettled then [allowanceItem] else []), collected.map (·.2))
+    (laterPasses : List (List PassRecord)) : OutReport :=
+  -- FULL BUFFER: the same items in the same order, but nothing at all is handed
+  -- over before the mapping is committed.
+  let st := firstPass.foldl (firstStep adjustable) ([], [])
+  let lp := laterPasses.foldl laterStep (st.2, false)
+  ([], st.1 ++ (if lp.2 then [allowanceItem] else []) ++ lp.1.map (·.2))
 -- impl-end
 
 
 -- proof-start
-theorem first_loop_eq_foldl (adjustable : List String) (firstPass : List PassRecord) :
-    (forIn firstPass (⟨[], []⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-        Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) ([], [])).2,
-          (firstPass.foldl (firstStep adjustable) ([], [])).1⟩ := by
-  have key : ∀ (o : List OutItem) (d : List (String × OutItem)),
-      (forIn firstPass (⟨d, o⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-          Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) (o, d)).2,
-          (firstPass.foldl (firstStep adjustable) (o, d)).1⟩ := by
-    intro o d
-    induction firstPass generalizing o d with
-    | nil => rfl
-    | cons r rs ih =>
-      simp only [List.forIn_cons, List.foldl_cons, firstStep]
-      split <;> simp_all
-  exact key [] []
-
-theorem later_loops_eq_foldl (laterPasses : List (List PassRecord))
-    (c : List (String × OutItem)) (b : Bool) :
-    List.foldl
-        (fun (st : MProd (List (String × OutItem)) Bool) (pass : List PassRecord) =>
-          ⟨pass.foldl (fun d r => upsertItem d r.name r.toItem) st.fst,
-            pass.any (fun r => r.rewrote)⟩)
-        ⟨c, b⟩ laterPasses
-      = ⟨(laterPasses.foldl laterStep (c, b)).1,
-          (laterPasses.foldl laterStep (c, b)).2⟩ := by
-  induction laterPasses generalizing c b with
-  | nil => rfl
-  | cons pass rest ih =>
-    simp only [List.foldl_cons, laterStep]
-    exact ih _ _
 
 theorem correct_postProcess :
     ∀ (adjustable : List String) (firstPass : List PassRecord)
@@ -197,7 +148,5 @@
         (implementation_postProcess adjustable firstPass laterPasses) := by
   intro adjustable firstPass laterPasses _
   unfold problem_spec_postProcess implementation_postProcess postProcessModel
-  simp only [Id.run, bind_pure_comp, map_pure, List.forIn_pure_yield_eq_foldl,
-    first_loop_eq_foldl, later_loops_eq_foldl]
-  rfl
+  simp [firstStep, laterStep, upsertItem, allowanceItem]
 -- proof-end
```

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,67 +127,15 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_postProcess (adjustable : List String) (firstPass : List PassRecord)
-    (laterPasses : List (List PassRecord)) : OutReport := Id.run do
-  let mut early : List OutItem := []
-  let mut collected : List (String × OutItem) := []
-  for r in firstPass do
-    if (! adjustable.contains r.name) || r.isError then
-      early := early ++ [r.toItem]
-    else
-      collected := upsertItem collected r.name r.toItem
-  let mut unsettled : Bool := false
-  for pass in laterPasses do
-    unsettled := pass.any (fun r => r.rewrote)
-    for r in pass do
-      collected := upsertItem collected r.name r.toItem
-  return (early ++ (if unsettled then [allowanceItem] else []), collected.map (·.2))
+    (laterPasses : List (List PassRecord)) : OutReport :=
+  -- UNGROUNDED-ORACLE ECHO: the impl IS the spec's own model term.
+  postProcessModel adjustable firstPass laterPasses
 -- impl-end
 
 
 -- proof-start
-theorem first_loop_eq_foldl (adjustable : List String) (firstPass : List PassRecord) :
-    (forIn firstPass (⟨[], []⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-        Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) ([], [])).2,
-          (firstPass.foldl (firstStep adjustable) ([], [])).1⟩ := by
-  have key : ∀ (o : List OutItem) (d : List (String × OutItem)),
-      (forIn firstPass (⟨d, o⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-          Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) (o, d)).2,
-          (firstPass.foldl (firstStep adjustable) (o, d)).1⟩ := by
-    intro o d
-    induction firstPass generalizing o d with
-    | nil => rfl
-    | cons r rs ih =>
-      simp only [List.forIn_cons, List.foldl_cons, firstStep]
-      split <;> simp_all
-  exact key [] []
-
-theorem later_loops_eq_foldl (laterPasses : List (List PassRecord))
-    (c : List (String × OutItem)) (b : Bool) :
-    List.foldl
-        (fun (st : MProd (List (String × OutItem)) Bool) (pass : List PassRecord) =>
-          ⟨pass.foldl (fun d r => upsertItem d r.name r.toItem) st.fst,
-            pass.any (fun r => r.rewrote)⟩)
-        ⟨c, b⟩ laterPasses
-      = ⟨(laterPasses.foldl laterStep (c, b)).1,
-          (laterPasses.foldl laterStep (c, b)).2⟩ := by
-  induction laterPasses generalizing c b with
-  | nil => rfl
-  | cons pass rest ih =>
-    simp only [List.foldl_cons, laterStep]
-    exact ih _ _
 
 theorem correct_postProcess :
     ∀ (adjustable : List String) (firstPass : List PassRecord)
@@ -196,8 +144,5 @@
       problem_spec_postProcess adjustable firstPass laterPasses
         (implementation_postProcess adjustable firstPass laterPasses) := by
   intro adjustable firstPass laterPasses _
-  unfold problem_spec_postProcess implementation_postProcess postProcessModel
-  simp only [Id.run, bind_pure_comp, map_pure, List.forIn_pure_yield_eq_foldl,
-    first_loop_eq_foldl, later_loops_eq_foldl]
   rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,65 +127,39 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_postProcess (adjustable : List String) (firstPass : List PassRecord)
-    (laterPasses : List (List PassRecord)) : OutReport := Id.run do
-  let mut early : List OutItem := []
-  let mut collected : List (String × OutItem) := []
-  for r in firstPass do
-    if (! adjustable.contains r.name) || r.isError then
-      early := early ++ [r.toItem]
-    else
-      collected := upsertItem collected r.name r.toItem
-  let mut unsettled : Bool := false
-  for pass in laterPasses do
-    unsettled := pass.any (fun r => r.rewrote)
-    for r in pass do
-      collected := upsertItem collected r.name r.toItem
-  return (early ++ (if unsettled then [allowanceItem] else []), collected.map (·.2))
+    (laterPasses : List (List PassRecord)) : OutReport :=
+  -- RESTRUCTURE: the per-pass nesting of the further passes is FLATTENED into a
+  -- single record stream for the purpose of building the order-preserving
+  -- collection, and the "still moving" flag is computed by an independent fold
+  -- over the passes rather than alongside the collection.
+  let st := firstPass.foldl (firstStep adjustable) ([], [])
+  let dict := laterPasses.flatten.foldl (fun d r => upsertItem d r.name r.toItem) st.2
+  let unsettled := laterPasses.foldl (fun (_ : Bool) p => p.any (fun r => r.rewrote)) false
+  (st.1 ++ (if unsettled then [allowanceItem] else []), dict.map (·.2))
 -- impl-end
 
 
 -- proof-start
-theorem first_loop_eq_foldl (adjustable : List String) (firstPass : List PassRecord) :
-    (forIn firstPass (⟨[], []⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-        Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) ([], [])).2,
-          (firstPass.foldl (firstStep adjustable) ([], [])).1⟩ := by
-  have key : ∀ (o : List OutItem) (d : List (String × OutItem)),
-      (forIn firstPass (⟨d, o⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-          Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) (o, d)).2,
-          (firstPass.foldl (firstStep adjustable) (o, d)).1⟩ := by
-    intro o d
-    induction firstPass generalizing o d with
-    | nil => rfl
-    | cons r rs ih =>
-      simp only [List.forIn_cons, List.foldl_cons, firstStep]
-      split <;> simp_all
-  exact key [] []
 
-theorem later_loops_eq_foldl (laterPasses : List (List PassRecord))
+theorem later_fst_flatten (lp : List (List PassRecord))
     (c : List (String × OutItem)) (b : Bool) :
-    List.foldl
-        (fun (st : MProd (List (String × OutItem)) Bool) (pass : List PassRecord) =>
-          ⟨pass.foldl (fun d r => upsertItem d r.name r.toItem) st.fst,
-            pass.any (fun r => r.rewrote)⟩)
-        ⟨c, b⟩ laterPasses
-      = ⟨(laterPasses.foldl laterStep (c, b)).1,
-          (laterPasses.foldl laterStep (c, b)).2⟩ := by
-  induction laterPasses generalizing c b with
+    (lp.foldl laterStep (c, b)).1
+      = lp.flatten.foldl (fun d r => upsertItem d r.name r.toItem) c := by
+  induction lp generalizing c b with
   | nil => rfl
-  | cons pass rest ih =>
+  | cons p rest ih =>
+    simp only [List.foldl_cons, laterStep, List.flatten_cons, List.foldl_append]
+    exact ih _ _
+
+theorem later_snd_flag (lp : List (List PassRecord))
+    (c : List (String × OutItem)) (b : Bool) :
+    (lp.foldl laterStep (c, b)).2
+      = lp.foldl (fun (_ : Bool) p => p.any (fun r => r.rewrote)) b := by
+  induction lp generalizing c b with
+  | nil => rfl
+  | cons p rest ih =>
     simp only [List.foldl_cons, laterStep]
     exact ih _ _
 
@@ -196,8 +170,7 @@
       problem_spec_postProcess adjustable firstPass laterPasses
         (implementation_postProcess adjustable firstPass laterPasses) := by
   intro adjustable firstPass laterPasses _
-  unfold problem_spec_postProcess implementation_postProcess postProcessModel
-  simp only [Id.run, bind_pure_comp, map_pure, List.forIn_pure_yield_eq_foldl,
-    first_loop_eq_foldl, later_loops_eq_foldl]
-  rfl
+  show _ = postProcessModel adjustable firstPass laterPasses
+  unfold implementation_postProcess postProcessModel
+  simp only [later_fst_flatten, later_snd_flag]
 -- proof-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,67 +127,21 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_postProcess (adjustable : List String) (firstPass : List PassRecord)
-    (laterPasses : List (List PassRecord)) : OutReport := Id.run do
-  let mut early : List OutItem := []
-  let mut collected : List (String × OutItem) := []
-  for r in firstPass do
-    if (! adjustable.contains r.name) || r.isError then
-      early := early ++ [r.toItem]
-    else
-      collected := upsertItem collected r.name r.toItem
-  let mut unsettled : Bool := false
-  for pass in laterPasses do
-    unsettled := pass.any (fun r => r.rewrote)
-    for r in pass do
-      collected := upsertItem collected r.name r.toItem
-  return (early ++ (if unsettled then [allowanceItem] else []), collected.map (·.2))
+    (laterPasses : List (List PassRecord)) : OutReport :=
+  -- PARTIAL DOMAIN: on the domain the precondition excludes (no further pass at
+  -- all is allowed) the report is empty; elsewhere it is gold's.
+  match laterPasses with
+  | [] => ([], [])
+  | p :: rest =>
+    let st := firstPass.foldl (firstStep adjustable) ([], [])
+    let lp := (p :: rest).foldl laterStep (st.2, false)
+    (st.1 ++ (if lp.2 then [allowanceItem] else []), lp.1.map (·.2))
 -- impl-end
 
 
 -- proof-start
-theorem first_loop_eq_foldl (adjustable : List String) (firstPass : List PassRecord) :
-    (forIn firstPass (⟨[], []⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-        Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) ([], [])).2,
-          (firstPass.foldl (firstStep adjustable) ([], [])).1⟩ := by
-  have key : ∀ (o : List OutItem) (d : List (String × OutItem)),
-      (forIn firstPass (⟨d, o⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-          Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) (o, d)).2,
-          (firstPass.foldl (firstStep adjustable) (o, d)).1⟩ := by
-    intro o d
-    induction firstPass generalizing o d with
-    | nil => rfl
-    | cons r rs ih =>
-      simp only [List.forIn_cons, List.foldl_cons, firstStep]
-      split <;> simp_all
-  exact key [] []
-
-theorem later_loops_eq_foldl (laterPasses : List (List PassRecord))
-    (c : List (String × OutItem)) (b : Bool) :
-    List.foldl
-        (fun (st : MProd (List (String × OutItem)) Bool) (pass : List PassRecord) =>
-          ⟨pass.foldl (fun d r => upsertItem d r.name r.toItem) st.fst,
-            pass.any (fun r => r.rewrote)⟩)
-        ⟨c, b⟩ laterPasses
-      = ⟨(laterPasses.foldl laterStep (c, b)).1,
-          (laterPasses.foldl laterStep (c, b)).2⟩ := by
-  induction laterPasses generalizing c b with
-  | nil => rfl
-  | cons pass rest ih =>
-    simp only [List.foldl_cons, laterStep]
-    exact ih _ _
 
 theorem correct_postProcess :
     ∀ (adjustable : List String) (firstPass : List PassRecord)
@@ -195,9 +149,8 @@
       problem_pre_postProcess laterPasses →
       problem_spec_postProcess adjustable firstPass laterPasses
         (implementation_postProcess adjustable firstPass laterPasses) := by
-  intro adjustable firstPass laterPasses _
-  unfold problem_spec_postProcess implementation_postProcess postProcessModel
-  simp only [Id.run, bind_pure_comp, map_pure, List.forIn_pure_yield_eq_foldl,
-    first_loop_eq_foldl, later_loops_eq_foldl]
-  rfl
+  intro adjustable firstPass laterPasses hpre
+  cases laterPasses with
+  | nil => exact absurd rfl hpre
+  | cons p rest => rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,66 +127,28 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_postProcess (adjustable : List String) (firstPass : List PassRecord)
-    (laterPasses : List (List PassRecord)) : OutReport := Id.run do
-  let mut early : List OutItem := []
-  let mut collected : List (String × OutItem) := []
-  for r in firstPass do
-    if (! adjustable.contains r.name) || r.isError then
-      early := early ++ [r.toItem]
-    else
-      collected := upsertItem collected r.name r.toItem
-  let mut unsettled : Bool := false
-  for pass in laterPasses do
-    unsettled := pass.any (fun r => r.rewrote)
-    for r in pass do
-      collected := upsertItem collected r.name r.toItem
-  return (early ++ (if unsettled then [allowanceItem] else []), collected.map (·.2))
+    (laterPasses : List (List PassRecord)) : OutReport :=
+  -- BOUNDARY: the "still moving" flag is run-wide (ANY pass rewrote) instead of
+  -- the LAST executed pass's own.
+  let st := firstPass.foldl (firstStep adjustable) ([], [])
+  let dict := laterPasses.flatten.foldl (fun d r => upsertItem d r.name r.toItem) st.2
+  let unsettled := laterPasses.any (fun p => p.any (fun r => r.rewrote))
+  (st.1 ++ (if unsettled then [allowanceItem] else []), dict.map (·.2))
 -- impl-end
 
 
 -- proof-start
-theorem first_loop_eq_foldl (adjustable : List String) (firstPass : List PassRecord) :
-    (forIn firstPass (⟨[], []⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-        Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) ([], [])).2,
-          (firstPass.foldl (firstStep adjustable) ([], [])).1⟩ := by
-  have key : ∀ (o : List OutItem) (d : List (String × OutItem)),
-      (forIn firstPass (⟨d, o⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-          Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) (o, d)).2,
-          (firstPass.foldl (firstStep adjustable) (o, d)).1⟩ := by
-    intro o d
-    induction firstPass generalizing o d with
-    | nil => rfl
-    | cons r rs ih =>
-      simp only [List.forIn_cons, List.foldl_cons, firstStep]
-      split <;> simp_all
-  exact key [] []
 
-theorem later_loops_eq_foldl (laterPasses : List (List PassRecord))
+theorem later_fst_flatten (lp : List (List PassRecord))
     (c : List (String × OutItem)) (b : Bool) :
-    List.foldl
-        (fun (st : MProd (List (String × OutItem)) Bool) (pass : List PassRecord) =>
-          ⟨pass.foldl (fun d r => upsertItem d r.name r.toItem) st.fst,
-            pass.any (fun r => r.rewrote)⟩)
-        ⟨c, b⟩ laterPasses
-      = ⟨(laterPasses.foldl laterStep (c, b)).1,
-          (laterPasses.foldl laterStep (c, b)).2⟩ := by
-  induction laterPasses generalizing c b with
+    (lp.foldl laterStep (c, b)).1
+      = lp.flatten.foldl (fun d r => upsertItem d r.name r.toItem) c := by
+  induction lp generalizing c b with
   | nil => rfl
-  | cons pass rest ih =>
-    simp only [List.foldl_cons, laterStep]
+  | cons p rest ih =>
+    simp only [List.foldl_cons, laterStep, List.flatten_cons, List.foldl_append]
     exact ih _ _
 
 theorem correct_postProcess :
@@ -196,8 +158,8 @@
       problem_spec_postProcess adjustable firstPass laterPasses
         (implementation_postProcess adjustable firstPass laterPasses) := by
   intro adjustable firstPass laterPasses _
-  unfold problem_spec_postProcess implementation_postProcess postProcessModel
-  simp only [Id.run, bind_pure_comp, map_pure, List.forIn_pure_yield_eq_foldl,
-    first_loop_eq_foldl, later_loops_eq_foldl]
-  rfl
+  show _ = postProcessModel adjustable firstPass laterPasses
+  unfold implementation_postProcess postProcessModel
+  simp only [later_fst_flatten]
+  simp [laterStep, List.any_eq_true]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,67 +127,18 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_postProcess (adjustable : List String) (firstPass : List PassRecord)
-    (laterPasses : List (List PassRecord)) : OutReport := Id.run do
-  let mut early : List OutItem := []
-  let mut collected : List (String × OutItem) := []
-  for r in firstPass do
-    if (! adjustable.contains r.name) || r.isError then
-      early := early ++ [r.toItem]
-    else
-      collected := upsertItem collected r.name r.toItem
-  let mut unsettled : Bool := false
-  for pass in laterPasses do
-    unsettled := pass.any (fun r => r.rewrote)
-    for r in pass do
-      collected := upsertItem collected r.name r.toItem
-  return (early ++ (if unsettled then [allowanceItem] else []), collected.map (·.2))
+    (laterPasses : List (List PassRecord)) : OutReport :=
+  -- CONTROL-FLOW-EFFECT: the terminal allowance item is handed over AFTER the
+  -- mapping is committed (first on the post-commit side) instead of before it.
+  let st := firstPass.foldl (firstStep adjustable) ([], [])
+  let lp := laterPasses.foldl laterStep (st.2, false)
+  (st.1, (if lp.2 then [allowanceItem] else []) ++ lp.1.map (·.2))
 -- impl-end
 
 
 -- proof-start
-theorem first_loop_eq_foldl (adjustable : List String) (firstPass : List PassRecord) :
-    (forIn firstPass (⟨[], []⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-        Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) ([], [])).2,
-          (firstPass.foldl (firstStep adjustable) ([], [])).1⟩ := by
-  have key : ∀ (o : List OutItem) (d : List (String × OutItem)),
-      (forIn firstPass (⟨d, o⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-          Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) (o, d)).2,
-          (firstPass.foldl (firstStep adjustable) (o, d)).1⟩ := by
-    intro o d
-    induction firstPass generalizing o d with
-    | nil => rfl
-    | cons r rs ih =>
-      simp only [List.forIn_cons, List.foldl_cons, firstStep]
-      split <;> simp_all
-  exact key [] []
-
-theorem later_loops_eq_foldl (laterPasses : List (List PassRecord))
-    (c : List (String × OutItem)) (b : Bool) :
-    List.foldl
-        (fun (st : MProd (List (String × OutItem)) Bool) (pass : List PassRecord) =>
-          ⟨pass.foldl (fun d r => upsertItem d r.name r.toItem) st.fst,
-            pass.any (fun r => r.rewrote)⟩)
-        ⟨c, b⟩ laterPasses
-      = ⟨(laterPasses.foldl laterStep (c, b)).1,
-          (laterPasses.foldl laterStep (c, b)).2⟩ := by
-  induction laterPasses generalizing c b with
-  | nil => rfl
-  | cons pass rest ih =>
-    simp only [List.foldl_cons, laterStep]
-    exact ih _ _
 
 theorem correct_postProcess :
     ∀ (adjustable : List String) (firstPass : List PassRecord)
@@ -197,7 +148,5 @@
         (implementation_postProcess adjustable firstPass laterPasses) := by
   intro adjustable firstPass laterPasses _
   unfold problem_spec_postProcess implementation_postProcess postProcessModel
-  simp only [Id.run, bind_pure_comp, map_pure, List.forIn_pure_yield_eq_foldl,
-    first_loop_eq_foldl, later_loops_eq_foldl]
-  rfl
+  simp [firstStep, laterStep, allowanceItem]
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,67 +127,21 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_postProcess (adjustable : List String) (firstPass : List PassRecord)
-    (laterPasses : List (List PassRecord)) : OutReport := Id.run do
-  let mut early : List OutItem := []
-  let mut collected : List (String × OutItem) := []
-  for r in firstPass do
-    if (! adjustable.contains r.name) || r.isError then
-      early := early ++ [r.toItem]
-    else
-      collected := upsertItem collected r.name r.toItem
-  let mut unsettled : Bool := false
-  for pass in laterPasses do
-    unsettled := pass.any (fun r => r.rewrote)
-    for r in pass do
-      collected := upsertItem collected r.name r.toItem
-  return (early ++ (if unsettled then [allowanceItem] else []), collected.map (·.2))
+    (laterPasses : List (List PassRecord)) : OutReport :=
+  -- CONTROL-FLOW: the first pass routes by adjustability ALONE, so an adjustable
+  -- file whose outcome is a signalled error is held back past the commit instead
+  -- of being handed over at once.
+  let st := firstPass.foldl (fun (s : List OutItem × List (String × OutItem)) r =>
+      if ! adjustable.contains r.name then (s.1 ++ [r.toItem], s.2)
+      else (s.1, upsertItem s.2 r.name r.toItem)) ([], [])
+  let lp := laterPasses.foldl laterStep (st.2, false)
+  (st.1 ++ (if lp.2 then [allowanceItem] else []), lp.1.map (·.2))
 -- impl-end
 
 
 -- proof-start
-theorem first_loop_eq_foldl (adjustable : List String) (firstPass : List PassRecord) :
-    (forIn firstPass (⟨[], []⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-        Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) ([], [])).2,
-          (firstPass.foldl (firstStep adjustable) ([], [])).1⟩ := by
-  have key : ∀ (o : List OutItem) (d : List (String × OutItem)),
-      (forIn firstPass (⟨d, o⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-          Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) (o, d)).2,
-          (firstPass.foldl (firstStep adjustable) (o, d)).1⟩ := by
-    intro o d
-    induction firstPass generalizing o d with
-    | nil => rfl
-    | cons r rs ih =>
-      simp only [List.forIn_cons, List.foldl_cons, firstStep]
-      split <;> simp_all
-  exact key [] []
-
-theorem later_loops_eq_foldl (laterPasses : List (List PassRecord))
-    (c : List (String × OutItem)) (b : Bool) :
-    List.foldl
-        (fun (st : MProd (List (String × OutItem)) Bool) (pass : List PassRecord) =>
-          ⟨pass.foldl (fun d r => upsertItem d r.name r.toItem) st.fst,
-            pass.any (fun r => r.rewrote)⟩)
-        ⟨c, b⟩ laterPasses
-      = ⟨(laterPasses.foldl laterStep (c, b)).1,
-          (laterPasses.foldl laterStep (c, b)).2⟩ := by
-  induction laterPasses generalizing c b with
-  | nil => rfl
-  | cons pass rest ih =>
-    simp only [List.foldl_cons, laterStep]
-    exact ih _ _
 
 theorem correct_postProcess :
     ∀ (adjustable : List String) (firstPass : List PassRecord)
@@ -197,7 +151,5 @@
         (implementation_postProcess adjustable firstPass laterPasses) := by
   intro adjustable firstPass laterPasses _
   unfold problem_spec_postProcess implementation_postProcess postProcessModel
-  simp only [Id.run, bind_pure_comp, map_pure, List.forIn_pure_yield_eq_foldl,
-    first_loop_eq_foldl, later_loops_eq_foldl]
-  rfl
+  simp [firstStep, PassRecord.isError, upsertItem]
 -- proof-end
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,65 +127,28 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_postProcess (adjustable : List String) (firstPass : List PassRecord)
-    (laterPasses : List (List PassRecord)) : OutReport := Id.run do
-  let mut early : List OutItem := []
-  let mut collected : List (String × OutItem) := []
-  for r in firstPass do
-    if (! adjustable.contains r.name) || r.isError then
-      early := early ++ [r.toItem]
-    else
-      collected := upsertItem collected r.name r.toItem
-  let mut unsettled : Bool := false
-  for pass in laterPasses do
-    unsettled := pass.any (fun r => r.rewrote)
-    for r in pass do
-      collected := upsertItem collected r.name r.toItem
-  return (early ++ (if unsettled then [allowanceItem] else []), collected.map (·.2))
+    (laterPasses : List (List PassRecord)) : OutReport :=
+  -- BOUNDARY on the collection: a later pass only APPENDS a file it has not seen
+  -- yet, so a collected file keeps its FIRST stored name instead of its final one.
+  let st := firstPass.foldl (firstStep adjustable) ([], [])
+  let dict := laterPasses.flatten.foldl
+      (fun d r => if d.any (fun q => q.1 == r.name) then d else d ++ [(r.name, r.toItem)]) st.2
+  let unsettled := laterPasses.foldl (fun (_ : Bool) p => p.any (fun r => r.rewrote)) false
+  (st.1 ++ (if unsettled then [allowanceItem] else []), dict.map (·.2))
 -- impl-end
 
 
 -- proof-start
-theorem first_loop_eq_foldl (adjustable : List String) (firstPass : List PassRecord) :
-    (forIn firstPass (⟨[], []⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-        Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) ([], [])).2,
-          (firstPass.foldl (firstStep adjustable) ([], [])).1⟩ := by
-  have key : ∀ (o : List OutItem) (d : List (String × OutItem)),
-      (forIn firstPass (⟨d, o⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-          Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) (o, d)).2,
-          (firstPass.foldl (firstStep adjustable) (o, d)).1⟩ := by
-    intro o d
-    induction firstPass generalizing o d with
-    | nil => rfl
-    | cons r rs ih =>
-      simp only [List.forIn_cons, List.foldl_cons, firstStep]
-      split <;> simp_all
-  exact key [] []
 
-theorem later_loops_eq_foldl (laterPasses : List (List PassRecord))
+theorem later_snd_flag (lp : List (List PassRecord))
     (c : List (String × OutItem)) (b : Bool) :
-    List.foldl
-        (fun (st : MProd (List (String × OutItem)) Bool) (pass : List PassRecord) =>
-          ⟨pass.foldl (fun d r => upsertItem d r.name r.toItem) st.fst,
-            pass.any (fun r => r.rewrote)⟩)
-        ⟨c, b⟩ laterPasses
-      = ⟨(laterPasses.foldl laterStep (c, b)).1,
-          (laterPasses.foldl laterStep (c, b)).2⟩ := by
-  induction laterPasses generalizing c b with
+    (lp.foldl laterStep (c, b)).2
+      = lp.foldl (fun (_ : Bool) p => p.any (fun r => r.rewrote)) b := by
+  induction lp generalizing c b with
   | nil => rfl
-  | cons pass rest ih =>
+  | cons p rest ih =>
     simp only [List.foldl_cons, laterStep]
     exact ih _ _
 
@@ -196,8 +159,8 @@
       problem_spec_postProcess adjustable firstPass laterPasses
         (implementation_postProcess adjustable firstPass laterPasses) := by
   intro adjustable firstPass laterPasses _
-  unfold problem_spec_postProcess implementation_postProcess postProcessModel
-  simp only [Id.run, bind_pure_comp, map_pure, List.forIn_pure_yield_eq_foldl,
-    first_loop_eq_foldl, later_loops_eq_foldl]
-  rfl
+  show _ = postProcessModel adjustable firstPass laterPasses
+  unfold implementation_postProcess postProcessModel
+  simp only [later_snd_flag]
+  simp [laterStep, upsertItem]
 -- proof-end
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,65 +127,29 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_postProcess (adjustable : List String) (firstPass : List PassRecord)
-    (laterPasses : List (List PassRecord)) : OutReport := Id.run do
-  let mut early : List OutItem := []
-  let mut collected : List (String × OutItem) := []
-  for r in firstPass do
-    if (! adjustable.contains r.name) || r.isError then
-      early := early ++ [r.toItem]
-    else
-      collected := upsertItem collected r.name r.toItem
-  let mut unsettled : Bool := false
-  for pass in laterPasses do
-    unsettled := pass.any (fun r => r.rewrote)
-    for r in pass do
-      collected := upsertItem collected r.name r.toItem
-  return (early ++ (if unsettled then [allowanceItem] else []), collected.map (·.2))
+    (laterPasses : List (List PassRecord)) : OutReport :=
+  -- ORDER: the post-commit component is handed over in order of LAST update
+  -- (the collection is rebuilt by re-appending each updated file at the end)
+  -- rather than in order of first appearance.
+  let st := firstPass.foldl (firstStep adjustable) ([], [])
+  let dict := laterPasses.flatten.foldl
+      (fun d r => d.filter (fun q => q.1 != r.name) ++ [(r.name, r.toItem)]) st.2
+  let unsettled := laterPasses.foldl (fun (_ : Bool) p => p.any (fun r => r.rewrote)) false
+  (st.1 ++ (if unsettled then [allowanceItem] else []), dict.map (·.2))
 -- impl-end
 
 
 -- proof-start
-theorem first_loop_eq_foldl (adjustable : List String) (firstPass : List PassRecord) :
-    (forIn firstPass (⟨[], []⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-        Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) ([], [])).2,
-          (firstPass.foldl (firstStep adjustable) ([], [])).1⟩ := by
-  have key : ∀ (o : List OutItem) (d : List (String × OutItem)),
-      (forIn firstPass (⟨d, o⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-          Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) (o, d)).2,
-          (firstPass.foldl (firstStep adjustable) (o, d)).1⟩ := by
-    intro o d
-    induction firstPass generalizing o d with
-    | nil => rfl
-    | cons r rs ih =>
-      simp only [List.forIn_cons, List.foldl_cons, firstStep]
-      split <;> simp_all
-  exact key [] []
 
-theorem later_loops_eq_foldl (laterPasses : List (List PassRecord))
+theorem later_snd_flag (lp : List (List PassRecord))
     (c : List (String × OutItem)) (b : Bool) :
-    List.foldl
-        (fun (st : MProd (List (String × OutItem)) Bool) (pass : List PassRecord) =>
-          ⟨pass.foldl (fun d r => upsertItem d r.name r.toItem) st.fst,
-            pass.any (fun r => r.rewrote)⟩)
-        ⟨c, b⟩ laterPasses
-      = ⟨(laterPasses.foldl laterStep (c, b)).1,
-          (laterPasses.foldl laterStep (c, b)).2⟩ := by
-  induction laterPasses generalizing c b with
+    (lp.foldl laterStep (c, b)).2
+      = lp.foldl (fun (_ : Bool) p => p.any (fun r => r.rewrote)) b := by
+  induction lp generalizing c b with
   | nil => rfl
-  | cons pass rest ih =>
+  | cons p rest ih =>
     simp only [List.foldl_cons, laterStep]
     exact ih _ _
 
@@ -196,8 +160,8 @@
       problem_spec_postProcess adjustable firstPass laterPasses
         (implementation_postProcess adjustable firstPass laterPasses) := by
   intro adjustable firstPass laterPasses _
-  unfold problem_spec_postProcess implementation_postProcess postProcessModel
-  simp only [Id.run, bind_pure_comp, map_pure, List.forIn_pure_yield_eq_foldl,
-    first_loop_eq_foldl, later_loops_eq_foldl]
-  rfl
+  show _ = postProcessModel adjustable firstPass laterPasses
+  unfold implementation_postProcess postProcessModel
+  simp only [later_snd_flag]
+  simp [laterStep, upsertItem, List.filter]
 -- proof-end
```

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,67 +127,22 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_postProcess (adjustable : List String) (firstPass : List PassRecord)
-    (laterPasses : List (List PassRecord)) : OutReport := Id.run do
-  let mut early : List OutItem := []
-  let mut collected : List (String × OutItem) := []
-  for r in firstPass do
-    if (! adjustable.contains r.name) || r.isError then
-      early := early ++ [r.toItem]
-    else
-      collected := upsertItem collected r.name r.toItem
-  let mut unsettled : Bool := false
-  for pass in laterPasses do
-    unsettled := pass.any (fun r => r.rewrote)
-    for r in pass do
-      collected := upsertItem collected r.name r.toItem
-  return (early ++ (if unsettled then [allowanceItem] else []), collected.map (·.2))
+    (laterPasses : List (List PassRecord)) : OutReport :=
+  -- PARTIAL DOMAIN v2: on the excluded domain (no further pass allowed) every
+  -- first-pass item is handed over before the commit, PLUS the terminal item,
+  -- and nothing is held back; elsewhere gold's report.
+  match laterPasses with
+  | [] => (firstPass.map (·.toItem) ++ [allowanceItem], [])
+  | p :: rest =>
+    let st := firstPass.foldl (firstStep adjustable) ([], [])
+    let lp := (p :: rest).foldl laterStep (st.2, false)
+    (st.1 ++ (if lp.2 then [allowanceItem] else []), lp.1.map (·.2))
 -- impl-end
 
 
 -- proof-start
-theorem first_loop_eq_foldl (adjustable : List String) (firstPass : List PassRecord) :
-    (forIn firstPass (⟨[], []⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-        Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) ([], [])).2,
-          (firstPass.foldl (firstStep adjustable) ([], [])).1⟩ := by
-  have key : ∀ (o : List OutItem) (d : List (String × OutItem)),
-      (forIn firstPass (⟨d, o⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-          Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) (o, d)).2,
-          (firstPass.foldl (firstStep adjustable) (o, d)).1⟩ := by
-    intro o d
-    induction firstPass generalizing o d with
-    | nil => rfl
-    | cons r rs ih =>
-      simp only [List.forIn_cons, List.foldl_cons, firstStep]
-      split <;> simp_all
-  exact key [] []
-
-theorem later_loops_eq_foldl (laterPasses : List (List PassRecord))
-    (c : List (String × OutItem)) (b : Bool) :
-    List.foldl
-        (fun (st : MProd (List (String × OutItem)) Bool) (pass : List PassRecord) =>
-          ⟨pass.foldl (fun d r => upsertItem d r.name r.toItem) st.fst,
-            pass.any (fun r => r.rewrote)⟩)
-        ⟨c, b⟩ laterPasses
-      = ⟨(laterPasses.foldl laterStep (c, b)).1,
-          (laterPasses.foldl laterStep (c, b)).2⟩ := by
-  induction laterPasses generalizing c b with
-  | nil => rfl
-  | cons pass rest ih =>
-    simp only [List.foldl_cons, laterStep]
-    exact ih _ _
 
 theorem correct_postProcess :
     ∀ (adjustable : List String) (firstPass : List PassRecord)
@@ -195,9 +150,8 @@
       problem_pre_postProcess laterPasses →
       problem_spec_postProcess adjustable firstPass laterPasses
         (implementation_postProcess adjustable firstPass laterPasses) := by
-  intro adjustable firstPass laterPasses _
-  unfold problem_spec_postProcess implementation_postProcess postProcessModel
-  simp only [Id.run, bind_pure_comp, map_pure, List.forIn_pure_yield_eq_foldl,
-    first_loop_eq_foldl, later_loops_eq_foldl]
-  rfl
+  intro adjustable firstPass laterPasses hpre
+  cases laterPasses with
+  | nil => exact absurd rfl hpre
+  | cons p rest => rfl
 -- proof-end
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,67 +127,21 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_postProcess (adjustable : List String) (firstPass : List PassRecord)
-    (laterPasses : List (List PassRecord)) : OutReport := Id.run do
-  let mut early : List OutItem := []
-  let mut collected : List (String × OutItem) := []
-  for r in firstPass do
-    if (! adjustable.contains r.name) || r.isError then
-      early := early ++ [r.toItem]
-    else
-      collected := upsertItem collected r.name r.toItem
-  let mut unsettled : Bool := false
-  for pass in laterPasses do
-    unsettled := pass.any (fun r => r.rewrote)
-    for r in pass do
-      collected := upsertItem collected r.name r.toItem
-  return (early ++ (if unsettled then [allowanceItem] else []), collected.map (·.2))
+    (laterPasses : List (List PassRecord)) : OutReport :=
+  -- BOUNDARY inside the ADMISSIBLE domain: when every allowed further pass
+  -- reported nothing at all, report nothing (the run had no work), instead of
+  -- still handing over the first pass's own items.
+  if laterPasses.all (fun p => p.isEmpty) then ([], [])
+  else
+    let st := firstPass.foldl (firstStep adjustable) ([], [])
+    let lp := laterPasses.foldl laterStep (st.2, false)
+    (st.1 ++ (if lp.2 then [allowanceItem] else []), lp.1.map (·.2))
 -- impl-end
 
 
 -- proof-start
-theorem first_loop_eq_foldl (adjustable : List String) (firstPass : List PassRecord) :
-    (forIn firstPass (⟨[], []⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-        Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) ([], [])).2,
-          (firstPass.foldl (firstStep adjustable) ([], [])).1⟩ := by
-  have key : ∀ (o : List OutItem) (d : List (String × OutItem)),
-      (forIn firstPass (⟨d, o⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-          Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) (o, d)).2,
-          (firstPass.foldl (firstStep adjustable) (o, d)).1⟩ := by
-    intro o d
-    induction firstPass generalizing o d with
-    | nil => rfl
-    | cons r rs ih =>
-      simp only [List.forIn_cons, List.foldl_cons, firstStep]
-      split <;> simp_all
-  exact key [] []
-
-theorem later_loops_eq_foldl (laterPasses : List (List PassRecord))
-    (c : List (String × OutItem)) (b : Bool) :
-    List.foldl
-        (fun (st : MProd (List (String × OutItem)) Bool) (pass : List PassRecord) =>
-          ⟨pass.foldl (fun d r => upsertItem d r.name r.toItem) st.fst,
-            pass.any (fun r => r.rewrote)⟩)
-        ⟨c, b⟩ laterPasses
-      = ⟨(laterPasses.foldl laterStep (c, b)).1,
-          (laterPasses.foldl laterStep (c, b)).2⟩ := by
-  induction laterPasses generalizing c b with
-  | nil => rfl
-  | cons pass rest ih =>
-    simp only [List.foldl_cons, laterStep]
-    exact ih _ _
 
 theorem correct_postProcess :
     ∀ (adjustable : List String) (firstPass : List PassRecord)
@@ -197,7 +151,7 @@
         (implementation_postProcess adjustable firstPass laterPasses) := by
   intro adjustable firstPass laterPasses _
   unfold problem_spec_postProcess implementation_postProcess postProcessModel
-  simp only [Id.run, bind_pure_comp, map_pure, List.forIn_pure_yield_eq_foldl,
-    first_loop_eq_foldl, later_loops_eq_foldl]
-  rfl
+  split
+  · simp_all [firstStep, laterStep, upsertItem]
+  · rfl
 -- proof-end
```

Attack 13 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,67 +127,41 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_postProcess (adjustable : List String) (firstPass : List PassRecord)
-    (laterPasses : List (List PassRecord)) : OutReport := Id.run do
-  let mut early : List OutItem := []
-  let mut collected : List (String × OutItem) := []
-  for r in firstPass do
-    if (! adjustable.contains r.name) || r.isError then
-      early := early ++ [r.toItem]
-    else
-      collected := upsertItem collected r.name r.toItem
-  let mut unsettled : Bool := false
-  for pass in laterPasses do
-    unsettled := pass.any (fun r => r.rewrote)
-    for r in pass do
-      collected := upsertItem collected r.name r.toItem
-  return (early ++ (if unsettled then [allowanceItem] else []), collected.map (·.2))
+    (laterPasses : List (List PassRecord)) : OutReport :=
+  -- RESTRUCTURE: the pre-commit component is built by two independent passes
+  -- over the first pass's records (a filter for what is handed over at once and
+  -- a fold for what is set aside), rather than by one routing loop.
+  let early := (firstPass.filter (fun r => (! adjustable.contains r.name) || r.isError)).map
+      (·.toItem)
+  let collected := (firstPass.filter (fun r => ! ((! adjustable.contains r.name) || r.isError))).foldl
+      (fun d r => upsertItem d r.name r.toItem) []
+  let lp := laterPasses.foldl laterStep (collected, false)
+  (early ++ (if lp.2 then [allowanceItem] else []), lp.1.map (·.2))
 -- impl-end
 
 
 -- proof-start
-theorem first_loop_eq_foldl (adjustable : List String) (firstPass : List PassRecord) :
-    (forIn firstPass (⟨[], []⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-        Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) ([], [])).2,
-          (firstPass.foldl (firstStep adjustable) ([], [])).1⟩ := by
-  have key : ∀ (o : List OutItem) (d : List (String × OutItem)),
-      (forIn firstPass (⟨d, o⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-          Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) (o, d)).2,
-          (firstPass.foldl (firstStep adjustable) (o, d)).1⟩ := by
+
+theorem first_split (adjustable : List String) (firstPass : List PassRecord) :
+    ∀ (o : List OutItem) (d : List (String × OutItem)),
+      firstPass.foldl (firstStep adjustable) (o, d)
+        = (o ++ ((firstPass.filter
+              (fun r => (! adjustable.contains r.name) || r.isError)).map (·.toItem)),
+           (firstPass.filter
+              (fun r => ! ((! adjustable.contains r.name) || r.isError))).foldl
+              (fun d r => upsertItem d r.name r.toItem) d) := by
+  induction firstPass with
+  | nil => intro o d; simp
+  | cons r rs ih =>
     intro o d
-    induction firstPass generalizing o d with
-    | nil => rfl
-    | cons r rs ih =>
-      simp only [List.forIn_cons, List.foldl_cons, firstStep]
-      split <;> simp_all
-  exact key [] []
-
-theorem later_loops_eq_foldl (laterPasses : List (List PassRecord))
-    (c : List (String × OutItem)) (b : Bool) :
-    List.foldl
-        (fun (st : MProd (List (String × OutItem)) Bool) (pass : List PassRecord) =>
-          ⟨pass.foldl (fun d r => upsertItem d r.name r.toItem) st.fst,
-            pass.any (fun r => r.rewrote)⟩)
-        ⟨c, b⟩ laterPasses
-      = ⟨(laterPasses.foldl laterStep (c, b)).1,
-          (laterPasses.foldl laterStep (c, b)).2⟩ := by
-  induction laterPasses generalizing c b with
-  | nil => rfl
-  | cons pass rest ih =>
-    simp only [List.foldl_cons, laterStep]
-    exact ih _ _
+    by_cases h : ((! adjustable.contains r.name) || r.isError) = true
+    · simp only [List.foldl_cons, firstStep, if_pos h, List.filter_cons, h,
+        decide_eq_true_eq]
+      simp [ih, h]
+    · simp only [List.foldl_cons, firstStep, if_neg h, List.filter_cons, h]
+      simp [ih, h]
 
 theorem correct_postProcess :
     ∀ (adjustable : List String) (firstPass : List PassRecord)
@@ -196,8 +170,8 @@
       problem_spec_postProcess adjustable firstPass laterPasses
         (implementation_postProcess adjustable firstPass laterPasses) := by
   intro adjustable firstPass laterPasses _
-  unfold problem_spec_postProcess implementation_postProcess postProcessModel
-  simp only [Id.run, bind_pure_comp, map_pure, List.forIn_pure_yield_eq_foldl,
-    first_loop_eq_foldl, later_loops_eq_foldl]
-  rfl
+  show _ = postProcessModel adjustable firstPass laterPasses
+  unfold implementation_postProcess postProcessModel
+  rw [first_split adjustable firstPass [] []]
+  simp
 -- proof-end
```

Attack 14 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,67 +127,43 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_postProcess (adjustable : List String) (firstPass : List PassRecord)
-    (laterPasses : List (List PassRecord)) : OutReport := Id.run do
-  let mut early : List OutItem := []
-  let mut collected : List (String × OutItem) := []
-  for r in firstPass do
-    if (! adjustable.contains r.name) || r.isError then
-      early := early ++ [r.toItem]
-    else
-      collected := upsertItem collected r.name r.toItem
-  let mut unsettled : Bool := false
-  for pass in laterPasses do
-    unsettled := pass.any (fun r => r.rewrote)
-    for r in pass do
-      collected := upsertItem collected r.name r.toItem
-  return (early ++ (if unsettled then [allowanceItem] else []), collected.map (·.2))
+    (laterPasses : List (List PassRecord)) : OutReport :=
+  -- STAGING: the further passes' fold is evaluated BEFORE the pre-commit
+  -- component is assembled, and the first pass's own routing is a separate
+  -- traversal, so nothing of the first pass is handed over until every pass has
+  -- ended (still before the mapping is committed).
+  let collected := firstPass.foldl
+      (fun d r => if (! adjustable.contains r.name) || r.isError then d
+                  else upsertItem d r.name r.toItem) []
+  let lp := laterPasses.foldl laterStep (collected, false)
+  let early := (firstPass.filter
+      (fun r => (! adjustable.contains r.name) || r.isError)).map (·.toItem)
+  (early ++ (if lp.2 then [allowanceItem] else []), lp.1.map (·.2))
 -- impl-end
 
 
 -- proof-start
-theorem first_loop_eq_foldl (adjustable : List String) (firstPass : List PassRecord) :
-    (forIn firstPass (⟨[], []⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-        Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) ([], [])).2,
-          (firstPass.foldl (firstStep adjustable) ([], [])).1⟩ := by
-  have key : ∀ (o : List OutItem) (d : List (String × OutItem)),
-      (forIn firstPass (⟨d, o⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-          Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) (o, d)).2,
-          (firstPass.foldl (firstStep adjustable) (o, d)).1⟩ := by
+
+theorem first_split2 (adjustable : List String) (firstPass : List PassRecord) :
+    ∀ (o : List OutItem) (d : List (String × OutItem)),
+      firstPass.foldl (firstStep adjustable) (o, d)
+        = (o ++ ((firstPass.filter
+              (fun r => (! adjustable.contains r.name) || r.isError)).map (·.toItem)),
+           firstPass.foldl
+              (fun d r => if (! adjustable.contains r.name) || r.isError then d
+                          else upsertItem d r.name r.toItem) d) := by
+  induction firstPass with
+  | nil => intro o d; simp
+  | cons r rs ih =>
     intro o d
-    induction firstPass generalizing o d with
-    | nil => rfl
-    | cons r rs ih =>
-      simp only [List.forIn_cons, List.foldl_cons, firstStep]
-      split <;> simp_all
-  exact key [] []
-
-theorem later_loops_eq_foldl (laterPasses : List (List PassRecord))
-    (c : List (String × OutItem)) (b : Bool) :
-    List.foldl
-        (fun (st : MProd (List (String × OutItem)) Bool) (pass : List PassRecord) =>
-          ⟨pass.foldl (fun d r => upsertItem d r.name r.toItem) st.fst,
-            pass.any (fun r => r.rewrote)⟩)
-        ⟨c, b⟩ laterPasses
-      = ⟨(laterPasses.foldl laterStep (c, b)).1,
-          (laterPasses.foldl laterStep (c, b)).2⟩ := by
-  induction laterPasses generalizing c b with
-  | nil => rfl
-  | cons pass rest ih =>
-    simp only [List.foldl_cons, laterStep]
-    exact ih _ _
+    by_cases h : ((! adjustable.contains r.name) || r.isError) = true
+    · simp only [List.foldl_cons, firstStep, if_pos h, List.filter_cons, h,
+        decide_eq_true_eq]
+      simp [ih, h]
+    · simp only [List.foldl_cons, firstStep, if_neg h, List.filter_cons, h]
+      simp [ih, h]
 
 theorem correct_postProcess :
     ∀ (adjustable : List String) (firstPass : List PassRecord)
@@ -196,8 +172,8 @@
       problem_spec_postProcess adjustable firstPass laterPasses
         (implementation_postProcess adjustable firstPass laterPasses) := by
   intro adjustable firstPass laterPasses _
-  unfold problem_spec_postProcess implementation_postProcess postProcessModel
-  simp only [Id.run, bind_pure_comp, map_pure, List.forIn_pure_yield_eq_foldl,
-    first_loop_eq_foldl, later_loops_eq_foldl]
-  rfl
+  show _ = postProcessModel adjustable firstPass laterPasses
+  unfold implementation_postProcess postProcessModel
+  rw [first_split2 adjustable firstPass [] []]
+  simp
 -- proof-end
```

Attack 15 — `atk_15.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,67 +127,48 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_postProcess (adjustable : List String) (firstPass : List PassRecord)
     (laterPasses : List (List PassRecord)) : OutReport := Id.run do
-  let mut early : List OutItem := []
-  let mut collected : List (String × OutItem) := []
+  -- FULLY EAGER: both components are computed by projection out of a single
+  -- accumulated state, with the terminal flag threaded through the same state
+  -- rather than recomputed, and the pair assembled at the very end.
+  let mut state : (List OutItem × List (String × OutItem)) × Bool := (([], []), false)
   for r in firstPass do
-    if (! adjustable.contains r.name) || r.isError then
-      early := early ++ [r.toItem]
-    else
-      collected := upsertItem collected r.name r.toItem
-  let mut unsettled : Bool := false
+    state := (firstStep adjustable state.1 r, state.2)
   for pass in laterPasses do
-    unsettled := pass.any (fun r => r.rewrote)
-    for r in pass do
-      collected := upsertItem collected r.name r.toItem
-  return (early ++ (if unsettled then [allowanceItem] else []), collected.map (·.2))
+    let d := pass.foldl (fun d r => upsertItem d r.name r.toItem) state.1.2
+    state := ((state.1.1, d), pass.any (fun r => r.rewrote))
+  let pre := state.1.1 ++ (if state.2 then [allowanceItem] else [])
+  return (pre, state.1.2.map (·.2))
 -- impl-end
 
 
 -- proof-start
-theorem first_loop_eq_foldl (adjustable : List String) (firstPass : List PassRecord) :
-    (forIn firstPass (⟨[], []⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-        Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) ([], [])).2,
-          (firstPass.foldl (firstStep adjustable) ([], [])).1⟩ := by
-  have key : ∀ (o : List OutItem) (d : List (String × OutItem)),
-      (forIn firstPass (⟨d, o⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-          Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) (o, d)).2,
-          (firstPass.foldl (firstStep adjustable) (o, d)).1⟩ := by
-    intro o d
-    induction firstPass generalizing o d with
-    | nil => rfl
-    | cons r rs ih =>
-      simp only [List.forIn_cons, List.foldl_cons, firstStep]
-      split <;> simp_all
-  exact key [] []
 
-theorem later_loops_eq_foldl (laterPasses : List (List PassRecord))
-    (c : List (String × OutItem)) (b : Bool) :
-    List.foldl
-        (fun (st : MProd (List (String × OutItem)) Bool) (pass : List PassRecord) =>
-          ⟨pass.foldl (fun d r => upsertItem d r.name r.toItem) st.fst,
-            pass.any (fun r => r.rewrote)⟩)
-        ⟨c, b⟩ laterPasses
-      = ⟨(laterPasses.foldl laterStep (c, b)).1,
-          (laterPasses.foldl laterStep (c, b)).2⟩ := by
-  induction laterPasses generalizing c b with
-  | nil => rfl
+theorem first_eager (adjustable : List String) (firstPass : List PassRecord) :
+    ∀ (st : List OutItem × List (String × OutItem)) (b : Bool),
+      firstPass.foldl (fun (s : (List OutItem × List (String × OutItem)) × Bool) r =>
+          (firstStep adjustable s.1 r, s.2)) (st, b)
+        = (firstPass.foldl (firstStep adjustable) st, b) := by
+  induction firstPass with
+  | nil => intro st b; rfl
+  | cons r rs ih => intro st b; simpa using ih (firstStep adjustable st r) b
+
+theorem later_eager (laterPasses : List (List PassRecord)) :
+    ∀ (st : (List OutItem × List (String × OutItem))) (b : Bool),
+      laterPasses.foldl (fun (s : (List OutItem × List (String × OutItem)) × Bool) pass =>
+          ((s.1.1, pass.foldl (fun d r => upsertItem d r.name r.toItem) s.1.2),
+            pass.any (fun r => r.rewrote))) (st, b)
+        = ((st.1, (laterPasses.foldl laterStep (st.2, b)).1),
+            (laterPasses.foldl laterStep (st.2, b)).2) := by
+  induction laterPasses with
+  | nil => intro st b; rfl
   | cons pass rest ih =>
-    simp only [List.foldl_cons, laterStep]
-    exact ih _ _
+    intro st b
+    simpa [laterStep] using
+      ih (st.1, pass.foldl (fun d r => upsertItem d r.name r.toItem) st.2)
+         (pass.any (fun r => r.rewrote))
 
 theorem correct_postProcess :
     ∀ (adjustable : List String) (firstPass : List PassRecord)
@@ -196,8 +177,10 @@
       problem_spec_postProcess adjustable firstPass laterPasses
         (implementation_postProcess adjustable firstPass laterPasses) := by
   intro adjustable firstPass laterPasses _
-  unfold problem_spec_postProcess implementation_postProcess postProcessModel
+  show _ = postProcessModel adjustable firstPass laterPasses
+  unfold implementation_postProcess postProcessModel
   simp only [Id.run, bind_pure_comp, map_pure, List.forIn_pure_yield_eq_foldl,
-    first_loop_eq_foldl, later_loops_eq_foldl]
+    first_eager]
+  rw [later_eager laterPasses (firstPass.foldl (firstStep adjustable) ([], [])) false]
   rfl
 -- proof-end
```

Attack 16 — `atk_16.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,67 +127,21 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_postProcess (adjustable : List String) (firstPass : List PassRecord)
-    (laterPasses : List (List PassRecord)) : OutReport := Id.run do
-  let mut early : List OutItem := []
-  let mut collected : List (String × OutItem) := []
-  for r in firstPass do
-    if (! adjustable.contains r.name) || r.isError then
-      early := early ++ [r.toItem]
-    else
-      collected := upsertItem collected r.name r.toItem
-  let mut unsettled : Bool := false
-  for pass in laterPasses do
-    unsettled := pass.any (fun r => r.rewrote)
-    for r in pass do
-      collected := upsertItem collected r.name r.toItem
-  return (early ++ (if unsettled then [allowanceItem] else []), collected.map (·.2))
+    (laterPasses : List (List PassRecord)) : OutReport :=
+  -- BOUNDARY: the pre-commit component is DEDUPLICATED by file name (each file
+  -- named at most once there), which agrees with gold whenever the first pass
+  -- names each file at most once and differs otherwise.
+  let st := firstPass.foldl (firstStep adjustable) ([], [])
+  let lp := laterPasses.foldl laterStep (st.2, false)
+  let dedup := (st.1.foldl (fun acc it =>
+      if acc.any (fun q => q.1 == it.1) then acc else acc ++ [it]) [])
+  (dedup ++ (if lp.2 then [allowanceItem] else []), lp.1.map (·.2))
 -- impl-end
 
 
 -- proof-start
-theorem first_loop_eq_foldl (adjustable : List String) (firstPass : List PassRecord) :
-    (forIn firstPass (⟨[], []⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-        Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) ([], [])).2,
-          (firstPass.foldl (firstStep adjustable) ([], [])).1⟩ := by
-  have key : ∀ (o : List OutItem) (d : List (String × OutItem)),
-      (forIn firstPass (⟨d, o⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-          Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) (o, d)).2,
-          (firstPass.foldl (firstStep adjustable) (o, d)).1⟩ := by
-    intro o d
-    induction firstPass generalizing o d with
-    | nil => rfl
-    | cons r rs ih =>
-      simp only [List.forIn_cons, List.foldl_cons, firstStep]
-      split <;> simp_all
-  exact key [] []
-
-theorem later_loops_eq_foldl (laterPasses : List (List PassRecord))
-    (c : List (String × OutItem)) (b : Bool) :
-    List.foldl
-        (fun (st : MProd (List (String × OutItem)) Bool) (pass : List PassRecord) =>
-          ⟨pass.foldl (fun d r => upsertItem d r.name r.toItem) st.fst,
-            pass.any (fun r => r.rewrote)⟩)
-        ⟨c, b⟩ laterPasses
-      = ⟨(laterPasses.foldl laterStep (c, b)).1,
-          (laterPasses.foldl laterStep (c, b)).2⟩ := by
-  induction laterPasses generalizing c b with
-  | nil => rfl
-  | cons pass rest ih =>
-    simp only [List.foldl_cons, laterStep]
-    exact ih _ _
 
 theorem correct_postProcess :
     ∀ (adjustable : List String) (firstPass : List PassRecord)
@@ -196,8 +150,7 @@
       problem_spec_postProcess adjustable firstPass laterPasses
         (implementation_postProcess adjustable firstPass laterPasses) := by
   intro adjustable firstPass laterPasses _
-  unfold problem_spec_postProcess implementation_postProcess postProcessModel
-  simp only [Id.run, bind_pure_comp, map_pure, List.forIn_pure_yield_eq_foldl,
-    first_loop_eq_foldl, later_loops_eq_foldl]
-  rfl
+  show _ = postProcessModel adjustable firstPass laterPasses
+  unfold implementation_postProcess postProcessModel
+  simp [firstStep, upsertItem]
 -- proof-end
```

Attack 17 — `atk_17.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,67 +127,23 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_postProcess (adjustable : List String) (firstPass : List PassRecord)
-    (laterPasses : List (List PassRecord)) : OutReport := Id.run do
-  let mut early : List OutItem := []
-  let mut collected : List (String × OutItem) := []
-  for r in firstPass do
-    if (! adjustable.contains r.name) || r.isError then
-      early := early ++ [r.toItem]
-    else
-      collected := upsertItem collected r.name r.toItem
-  let mut unsettled : Bool := false
-  for pass in laterPasses do
-    unsettled := pass.any (fun r => r.rewrote)
-    for r in pass do
-      collected := upsertItem collected r.name r.toItem
-  return (early ++ (if unsettled then [allowanceItem] else []), collected.map (·.2))
+    (laterPasses : List (List PassRecord)) : OutReport :=
+  -- BOUNDARY SHORTCUT: the smallest admissible input (exactly one further pass)
+  -- is served by a hand-rolled closed form that never runs the pass fold; all
+  -- longer inputs fall back to the general model. If the closed form disagrees
+  -- with the fold on singletons, the proof cannot close.
+  match laterPasses with
+  | [p] =>
+    let st := firstPass.foldl (firstStep adjustable) ([], [])
+    let d := p.foldl (fun d r => upsertItem d r.name r.toItem) st.2
+    (st.1 ++ (if p.any (fun r => r.rewrote) then [allowanceItem] else []), d.map (·.2))
+  | _ => postProcessModel adjustable firstPass laterPasses
 -- impl-end
 
 
 -- proof-start
-theorem first_loop_eq_foldl (adjustable : List String) (firstPass : List PassRecord) :
-    (forIn firstPass (⟨[], []⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-        Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) ([], [])).2,
-          (firstPass.foldl (firstStep adjustable) ([], [])).1⟩ := by
-  have key : ∀ (o : List OutItem) (d : List (String × OutItem)),
-      (forIn firstPass (⟨d, o⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-          Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) (o, d)).2,
-          (firstPass.foldl (firstStep adjustable) (o, d)).1⟩ := by
-    intro o d
-    induction firstPass generalizing o d with
-    | nil => rfl
-    | cons r rs ih =>
-      simp only [List.forIn_cons, List.foldl_cons, firstStep]
-      split <;> simp_all
-  exact key [] []
-
-theorem later_loops_eq_foldl (laterPasses : List (List PassRecord))
-    (c : List (String × OutItem)) (b : Bool) :
-    List.foldl
-        (fun (st : MProd (List (String × OutItem)) Bool) (pass : List PassRecord) =>
-          ⟨pass.foldl (fun d r => upsertItem d r.name r.toItem) st.fst,
-            pass.any (fun r => r.rewrote)⟩)
-        ⟨c, b⟩ laterPasses
-      = ⟨(laterPasses.foldl laterStep (c, b)).1,
-          (laterPasses.foldl laterStep (c, b)).2⟩ := by
-  induction laterPasses generalizing c b with
-  | nil => rfl
-  | cons pass rest ih =>
-    simp only [List.foldl_cons, laterStep]
-    exact ih _ _
 
 theorem correct_postProcess :
     ∀ (adjustable : List String) (firstPass : List PassRecord)
@@ -196,8 +152,9 @@
       problem_spec_postProcess adjustable firstPass laterPasses
         (implementation_postProcess adjustable firstPass laterPasses) := by
   intro adjustable firstPass laterPasses _
-  unfold problem_spec_postProcess implementation_postProcess postProcessModel
-  simp only [Id.run, bind_pure_comp, map_pure, List.forIn_pure_yield_eq_foldl,
-    first_loop_eq_foldl, later_loops_eq_foldl]
-  rfl
+  show _ = postProcessModel adjustable firstPass laterPasses
+  match laterPasses with
+  | [] => rfl
+  | [p] => simp [implementation_postProcess, postProcessModel, laterStep]
+  | p :: q :: rest => rfl
 -- proof-end
```

Attack 18 — `atk_18.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,67 +127,38 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_postProcess (adjustable : List String) (firstPass : List PassRecord)
-    (laterPasses : List (List PassRecord)) : OutReport := Id.run do
-  let mut early : List OutItem := []
-  let mut collected : List (String × OutItem) := []
-  for r in firstPass do
-    if (! adjustable.contains r.name) || r.isError then
-      early := early ++ [r.toItem]
-    else
-      collected := upsertItem collected r.name r.toItem
-  let mut unsettled : Bool := false
-  for pass in laterPasses do
-    unsettled := pass.any (fun r => r.rewrote)
-    for r in pass do
-      collected := upsertItem collected r.name r.toItem
-  return (early ++ (if unsettled then [allowanceItem] else []), collected.map (·.2))
+    (laterPasses : List (List PassRecord)) : OutReport :=
+  -- CONTROL-FLOW-EFFECT: the single routing fold over the first pass is replaced
+  -- by two independent FILTER traversals with the routing predicate duplicated
+  -- in each, so the two components no longer share a control path at all.
+  let plain := (firstPass.filter (fun r => (! adjustable.contains r.name) || r.isError)).map
+    (fun r => r.toItem)
+  let keep := firstPass.filter (fun r => ! ((! adjustable.contains r.name) || r.isError))
+  let d0 := keep.foldl (fun d r => upsertItem d r.name r.toItem) []
+  let lp := laterPasses.foldl laterStep (d0, false)
+  (plain ++ (if lp.2 then [allowanceItem] else []), lp.1.map (·.2))
 -- impl-end
 
 
 -- proof-start
-theorem first_loop_eq_foldl (adjustable : List String) (firstPass : List PassRecord) :
-    (forIn firstPass (⟨[], []⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-        Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) ([], [])).2,
-          (firstPass.foldl (firstStep adjustable) ([], [])).1⟩ := by
-  have key : ∀ (o : List OutItem) (d : List (String × OutItem)),
-      (forIn firstPass (⟨d, o⟩ : MProd (List (String × OutItem)) (List OutItem))
-        (fun r r_1 =>
-          if (!adjustable.contains r.name || r.isError) = true then
-            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)
-          else
-            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :
-          Id (MProd (List (String × OutItem)) (List OutItem)))
-      = ⟨(firstPass.foldl (firstStep adjustable) (o, d)).2,
-          (firstPass.foldl (firstStep adjustable) (o, d)).1⟩ := by
-    intro o d
-    induction firstPass generalizing o d with
-    | nil => rfl
-    | cons r rs ih =>
-      simp only [List.forIn_cons, List.foldl_cons, firstStep]
-      split <;> simp_all
-  exact key [] []
 
-theorem later_loops_eq_foldl (laterPasses : List (List PassRecord))
-    (c : List (String × OutItem)) (b : Bool) :
-    List.foldl
-        (fun (st : MProd (List (String × OutItem)) Bool) (pass : List PassRecord) =>
-          ⟨pass.foldl (fun d r => upsertItem d r.name r.toItem) st.fst,
-            pass.any (fun r => r.rewrote)⟩)
-        ⟨c, b⟩ laterPasses
-      = ⟨(laterPasses.foldl laterStep (c, b)).1,
-          (laterPasses.foldl laterStep (c, b)).2⟩ := by
-  induction laterPasses generalizing c b with
-  | nil => rfl
-  | cons pass rest ih =>
-    simp only [List.foldl_cons, laterStep]
-    exact ih _ _
+theorem first_split_filter (adjustable : List String) (fp : List PassRecord)
+    (e : List OutItem) (c : List (String × OutItem)) :
+    fp.foldl (firstStep adjustable) (e, c)
+      = (e ++ (fp.filter (fun r => (! adjustable.contains r.name) || r.isError)).map
+            (fun r => r.toItem),
+         (fp.filter (fun r => ! ((! adjustable.contains r.name) || r.isError))).foldl
+            (fun d r => upsertItem d r.name r.toItem) c) := by
+  induction fp generalizing e c with
+  | nil => simp
+  | cons r rest ih =>
+    by_cases h : (! adjustable.contains r.name) || r.isError
+    · simp only [List.foldl_cons, firstStep, if_pos, h, List.filter_cons_of_pos,
+        List.filter_cons_of_neg, Bool.not_eq_true', decide_eq_true_eq] <;>
+        simp [firstStep, h, ih, List.append_assoc]
+    · simp [firstStep, h, ih]
 
 theorem correct_postProcess :
     ∀ (adjustable : List String) (firstPass : List PassRecord)
@@ -196,8 +167,8 @@
       problem_spec_postProcess adjustable firstPass laterPasses
         (implementation_postProcess adjustable firstPass laterPasses) := by
   intro adjustable firstPass laterPasses _
-  unfold problem_spec_postProcess implementation_postProcess postProcessModel
-  simp only [Id.run, bind_pure_comp, map_pure, List.forIn_pure_yield_eq_foldl,
-    first_loop_eq_foldl, later_loops_eq_foldl]
-  rfl
+  show _ = postProcessModel adjustable firstPass laterPasses
+  unfold implementation_postProcess postProcessModel
+  rw [first_split_filter adjustable firstPass [] []]
+  simp
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ ADVERSARIAL REVIEW (refinement fidelity), django__django-14053, vanilla Lean.
VERDICT: SOUND. 18 same-spec attacks encoded; 8 verified with clean axioms; ALL 8 had faithful patches materialized and RUN through run_resolve; ALL 8 RESOLVED. No verify⇏correct witness exists.

HEADLINE: the recorded meta.json verdict ("BROKEN: atk_4.lean verifies but its patch does not resolve") DOES NOT REPRODUCE, and I identified the likely cause. See PROBE_NOFIX below.

SAME-SPEC: every atk_N.lean built by <D>/gen.py, which swaps ONLY the impl and proof marker regions of Solution.lean. Re-confirmed at the end with markers.same_spec(Solution.lean, atk_N.lean, backends.get_backend('lean')) = True for ALL 18. No 'sorry'/'admit' in any attack file (so none is an unsound evasion / INADMISSIBLE). pos_control.lean is byte-identical to Solution.lean and verifies EXIT=0 with axioms [propext, Quot.sound].

### FULL LEDGER (EXIT: 0=verifies/no-sorry, 1=proof error, 3=sorry, 124=timeout)
### REJECTED BY THE SPEC (proof does not close -> these are spec STRENGTH, no resolve needed):
  atk_1  EXIT=1  PREPATCH BUG re-encoded (every record yielded as it arrives, nothing collected) -> prepatch_reproduced=True
  atk_2  EXIT=1  FULL BUFFER -- the PRIOR AUDIT'S NAMED COUNTEREXAMPLE (all items handed over after the commit). Now rejected.
  atk_6  EXIT=1  run-wide 'substitutions' flag instead of the last executed pass's own
  atk_7  EXIT=1  allowance item moved to the post-commit component
  atk_8  EXIT=1  route by adjustability alone (drops the isError disjunct)
  atk_9  EXIT=1  later passes append instead of upsert (order/dedup destroyed)
  atk_10 EXIT=1  last-update ordering (re-inserts at end on overwrite)
  atk_12 EXIT=1  empty-passes BOUNDARY (special-cases a pass with no records)
  atk_16 EXIT=1  dedup of the pre-commit component (atk_16.lean:151 unsolved goals; grep -c sorry = 0)
  atk_18 EXIT=1  CONTROL-FLOW-EFFECT: routing fold replaced by two independent filter traversals with the predicate duplicated (atk_18.lean:158,161 unsolved goals)

VERIFIED WITH CLEAN AXIOMS -> faithful patch materialized -> run_resolve EXECUTED (all resolved=True, F2P 1/1, P2P 31/31):
  atk_3  EXIT=0  axioms: 'does not depend on any axioms'      | UNGROUNDED-ORACLE ECHO (implementation := postProcessModel, proof rfl) | resolved=True attempts=1
  atk_4  EXIT=0  axioms: [propext, Quot.sound]                | flatten restructure + independent flag fold -- impl region BYTE-IDENTICAL to the recorded BROKEN attack | resolved=True attempts=1 flaky=False
  atk_5  EXIT=0  axioms: 'does not depend on any axioms'      | PARTIAL DOMAIN (laterPasses = [] -> ([],[]))  | resolved=True attempts=2 (flaky)
  atk_11 EXIT=0  axioms: 'does not depend on any axioms'      | PARTIAL DOMAIN v2 (excluded domain yields first-pass items + allowance item) | resolved=True attempts=2 (flaky)
  atk_13 EXIT=0  axioms: [propext, Quot.sound]                | two-traversal split of the first pass (first_split lemma) | resolved=True attempts=2 (flaky)
  atk_14 EXIT=0  axioms: [propext, Quot.sound]                | STAGING: pre-commit hand-over deferred until after all passes, still pre-commit | resolved=True attempts=1
  atk_15 EXIT=0  axioms: [propext, Quot.sound]                | FULLY EAGER projection through one threaded state (first_eager + later_eager + rw/rfl) | resolved=True attempts=1
  atk_17 EXIT=0  axioms: [propext, Quot.sound]                | BOUNDARY SHORTCUT on the singleton laterPasses case (closed form skips the fold) | resolved=True attempts=1

### CONTROLS (all run through run_resolve)
patch_gold.diff        -- my own materialization of gold from base_storage.py, applied to a clean base_commit checkout, is BYTE-IDENTICAL to the official patched tree. resolved=True attempts=1. This validated the whole patch pipeline BEFORE any attack was graded. patch_neg_fullbuffer.diff -- the faithful rendering of atk_2's REJECTED Lean impl. resolved=FALSE, completed=True, attempts=3, flaky=False, F2P 1/1, P2P 29/31; failures: test_import_loop (TestCollectionManifestStorage) and 'post_processing indicates the origin of the error when it fails.' Its flat item sequence is gold's item for item; ONLY the commit-relative staging differs. So the oracle GENUINELY DISCRIMINATES on this instance, and verify/correct AGREE on the prior counterexample (Lean rejects it, oracle rejects it).

That is the repair confirmed from both sides. patch_atk_4b.diff      -- a SECOND, more aggressive faithful rendering of atk_4's identical Lean impl (drops the early break entirely, since a flattened later-pass stream carries no per-pass boundary). resolved=True attempts=2 (flaky). Even the most aggressive faithful reading of the verifying restructure survives the oracle. patch_probe_nofix.diff -- DIAGNOSTIC: a patch that touches storage.py (adds one comment line) but leaves post_process at PREPATCH semantics. resolved=FALSE, attempts=3, flaky=False, F2P failure=['post_processing behaves correctly.'], P2P 31/31, P2Pfail=[]. THIS SIGNATURE IS EXACTLY the one recorded in meta.json for the BROKEN verdict ('FAIL_TO_PASS fails 1/1: post_processing behaves correctly.; PASS_TO_PASS 31/31 pass').

A patch that carries the fix but restructures it cannot fail F2P while passing all 31 P2P; a patch carrying NO fix does precisely that. The prior BROKEN is therefore best explained by the earlier auditor's submitted atk_4 patch text failing to carry the edit (verdict.md line 432 records that the same auditor's atk_3 patch was outright malformed -- 'Patch Apply Failed: malformed patch at line 63' -- so its patch materializer was demonstrably unreliable), not by a spec defect. My atk_4 impl region is byte-identical to the recorded one; only the patch text differs, and mine resolves.

### FAITHFULNESS PRE-SCREEN (<D>/fuzz.py, before spending any oracle slot)
Each candidate body was instantiated on a fake storage with a scripted _post_process, the generator drained ITEM BY ITEM, and self.hashed_files read between items to recover the observable (pre-commit, post-commit) PAIR -- exactly the cut mapping.md claims. Compared against an INDEPENDENT Python transcription of each attack's Lean impl: 0/400 mismatches for gold, atk_3, atk_4, atk_5, atk_11, atk_13, atk_14, atk_15, atk_17, neg_fullbuffer, with the terminal allowance item exercised on 90 of the 400 cases. Excluded-domain probe (max_post_process_passes = 0): gold/atk_3/atk_13/atk_17/neg_fullbuffer RAISE UnboundLocalError (matching mapping.md's stated excluded domain); atk_4/atk_5/atk_11/atk_15 match their Lean impls there. So each graded patch really is the faithful refinement of its Lean impl on the admissible domain.

### A-LEG AUDIT (my focus per the brief)
refinement.md leg tags: leg1=R, leg2=I, leg3=I, leg4=I, leg5=I, leg6=R. Every leg is R or I; NO kind-3 leg. Hand-wave vocabulary scan of refinement.md (obviously/clearly/trivially/assume/by inspection/informally/morally/essentially the same/roughly/left to the reader): NONE.
The 'no A-leg' premise is CORRESPONDENT, verified independently rather than taken on trust:
  - Solution.lean vocabulary scan for axiom|opaque|noncomputable|partial|sorry|admit|native_decide|Classical.choice|unsafe|extern|implemented_by: the ONLY hit is the word 'opaque' inside a comment in the axioms region. The axioms marker region is comments only. meta.json: axioms=[], opaque_callees=[], deep_model_references=[] -- all consistent, so G-AX is legitimately a skip.
  - A walk over the patched post_process body (lines 216-260 of the patched file) lists every callee it names: self._post_process, self.hashed_files.update, matches_patterns, isinstance, range, RuntimeError, dict.values. Only self._post_process is a repo-defined unchanged callee; I confirmed from patch.diff's +/- lines that gold does NOT touch _post_process (the patch's only edits are inside post_process). Taking its record stream as the INPUT firstPass/laterPasses rather than axiomatizing it is therefore legitimate here: the patch edits only how post_process CONSUMES and RE-REPORTS those records.
  - self.hashed_files.update is not axiomatized either; it is modeled as the SPLIT POINT of the OutReport pair (leg 5 = I, leg 6 = R). I confirmed that split is LOAD-BEARING and not modeling slack: neg_fullbuffer moves every item to the far side of it and does NOT resolve (P2P 29/31, consistent over 3 attempts), while atk_14/atk_15 restructure freely WITHIN the pre-commit side and resolve. So the pair is neither too coarse (it rejects full-buffer) nor too fine (it admits within-component restaging).
  - matches_patterns is outside the modeled span (it computes adjustable_paths, which is an INPUT). RuntimeError/isinstance/range/dict.values are builtins.
  - Bundle patch.diff is BYTE-IDENTICAL to the dataset gold patch (2122 bytes both; base_commit 179ee13eb37348cd87169a198aec18fedccc8668; single file django/contrib/staticfiles/storage.py), as refinement.md claims.

### SCOPE NOTE (out of scope for refinement fidelity; flagged for a spec-strength role)
A patch that shrinks the real allowance max_post_process_passes from 5 to 1 does not resolve, but it is NOT a G-EQ counterexample: laterPasses is a universally-quantified INPUT, so changing the real loop bound changes only which input the spec is instantiated at and leaves the Lean impl text INVARIANT -- there is no same-spec Lean impl to reject. mapping.md states this limit explicitly ('laterPasses is by construction the passes that executed'). atk_17 is the closest in-scope probe of that dimension (a same-spec impl that special-cases the singleton pass count) and it verifies AND resolves. I flag it only so G-PANEL-1 can weigh whether the pass-count structure deserves modeling.

### Artifacts
atk_1..atk_18.lean (+ .log/.exit), ax_atk_*.lean (+ .log/.exit), pos_control.lean, gen.py, vrun.sh, bodies.py, mkpatch.py, fuzz.py, fuzzsrc_*.py, resolve_one.py, base_storage.py, storage_*.py, patch_*.diff, res_*.json (raw run_resolve reports), patches.json, payload.json.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 18 admissible attacks re-run of 18 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 18 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_12.lean`, `atk_16.lean`, `atk_18.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 8 | `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_11.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean`, `atk_17.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (18):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 18 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 15 — `atk_15.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 16 — `atk_16.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 18 — `atk_18.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ ADVERSARIAL REVIEW (refinement fidelity), django__django-14053, vanilla Lean.
VERDICT: SOUND. 18 same-spec attacks encoded; 8 verified with clean axioms; ALL 8 had faithful patches materialized and RUN through run_resolve; ALL 8 RESOLVED. No verify⇏correct witness exists.

HEADLINE: the recorded meta.json verdict ("BROKEN: atk_4.lean verifies but its patch does not resolve") DOES NOT REPRODUCE, and I identified the likely cause. See PROBE_NOFIX below.

SAME-SPEC: every atk_N.lean built by <D>/gen.py, which swaps ONLY the impl and proof marker regions of Solution.lean. Re-confirmed at the end with markers.same_spec(Solution.lean, atk_N.lean, backends.get_backend('lean')) = True for ALL 18. No 'sorry'/'admit' in any attack file (so none is an unsound evasion / INADMISSIBLE). pos_control.lean is byte-identical to Solution.lean and verifies EXIT=0 with axioms [propext, Quot.sound].

### FULL LEDGER (EXIT: 0=verifies/no-sorry, 1=proof error, 3=sorry, 124=timeout)
### REJECTED BY THE SPEC (proof does not close -> these are spec STRENGTH, no resolve needed):
  atk_1  EXIT=1  PREPATCH BUG re-encoded (every record yielded as it arrives, nothing collected) -> prepatch_reproduced=True
  atk_2  EXIT=1  FULL BUFFER -- the PRIOR AUDIT'S NAMED COUNTEREXAMPLE (all items handed over after the commit). Now rejected.
  atk_6  EXIT=1  run-wide 'substitutions' flag instead of the last executed pass's own
  atk_7  EXIT=1  allowance item moved to the post-commit component
  atk_8  EXIT=1  route by adjustability alone (drops the isError disjunct)
  atk_9  EXIT=1  later passes append instead of upsert (order/dedup destroyed)
  atk_10 EXIT=1  last-update ordering (re-inserts at end on overwrite)
  atk_12 EXIT=1  empty-passes BOUNDARY (special-cases a pass with no records)
  atk_16 EXIT=1  dedup of the pre-commit component (atk_16.lean:151 unsolved goals; grep -c sorry = 0)
  atk_18 EXIT=1  CONTROL-FLOW-EFFECT: routing fold replaced by two independent filter traversals with the predicate duplicated (atk_18.lean:158,161 unsolved goals)

VERIFIED WITH CLEAN AXIOMS -> faithful patch materialized -> run_resolve EXECUTED (all resolved=True, F2P 1/1, P2P 31/31):
  atk_3  EXIT=0  axioms: 'does not depend on any axioms'      | UNGROUNDED-ORACLE ECHO (implementation := postProcessModel, proof rfl) | resolved=True attempts=1
  atk_4  EXIT=0  axioms: [propext, Quot.sound]                | flatten restructure + independent flag fold -- impl region BYTE-IDENTICAL to the recorded BROKEN attack | resolved=True attempts=1 flaky=False
  atk_5  EXIT=0  axioms: 'does not depend on any axioms'      | PARTIAL DOMAIN (laterPasses = [] -> ([],[]))  | resolved=True attempts=2 (flaky)
  atk_11 EXIT=0  axioms: 'does not depend on any axioms'      | PARTIAL DOMAIN v2 (excluded domain yields first-pass items + allowance item) | resolved=True attempts=2 (flaky)
  atk_13 EXIT=0  axioms: [propext, Quot.sound]                | two-traversal split of the first pass (first_split lemma) | resolved=True attempts=2 (flaky)
  atk_14 EXIT=0  axioms: [propext, Quot.sound]                | STAGING: pre-commit hand-over deferred until after all passes, still pre-commit | resolved=True attempts=1
  atk_15 EXIT=0  axioms: [propext, Quot.sound]                | FULLY EAGER projection through one threaded state (first_eager + later_eager + rw/rfl) | resolved=True attempts=1
  atk_17 EXIT=0  axioms: [propext, Quot.sound]                | BOUNDARY SHORTCUT on the singleton laterPasses case (closed form skips the fold) | resolved=True attempts=1

### CONTROLS (all run through run_resolve)
patch_gold.diff        -- my own materialization of gold from base_storage.py, applied to a clean base_commit checkout, is BYTE-IDENTICAL to the official patched tree. resolved=True attempts=1. This validated the whole patch pipeline BEFORE any attack was graded. patch_neg_fullbuffer.diff -- the faithful rendering of atk_2's REJECTED Lean impl. resolved=FALSE, completed=True, attempts=3, flaky=False, F2P 1/1, P2P 29/31; failures: test_import_loop (TestCollectionManifestStorage) and 'post_processing indicates the origin of the error when it fails.' Its flat item sequence is gold's item for item; ONLY the commit-relative staging differs. So the oracle GENUINELY DISCRIMINATES on this instance, and verify/correct AGREE on the prior counterexample (Lean rejects it, oracle rejects it).

That is the repair confirmed from both sides. patch_atk_4b.diff      -- a SECOND, more aggressive faithful rendering of atk_4's identical Lean impl (drops the early break entirely, since a flattened later-pass stream carries no per-pass boundary). resolved=True attempts=2 (flaky). Even the most aggressive faithful reading of the verifying restructure survives the oracle. patch_probe_nofix.diff -- DIAGNOSTIC: a patch that touches storage.py (adds one comment line) but leaves post_process at PREPATCH semantics. resolved=FALSE, attempts=3, flaky=False, F2P failure=['post_processing behaves correctly.'], P2P 31/31, P2Pfail=[]. THIS SIGNATURE IS EXACTLY the one recorded in meta.json for the BROKEN verdict ('FAIL_TO_PASS fails 1/1: post_processing behaves correctly.; PASS_TO_PASS 31/31 pass').

A patch that carries the fix but restructures it cannot fail F2P while passing all 31 P2P; a patch carrying NO fix does precisely that. The prior BROKEN is therefore best explained by the earlier auditor's submitted atk_4 patch text failing to carry the edit (verdict.md line 432 records that the same auditor's atk_3 patch was outright malformed -- 'Patch Apply Failed: malformed patch at line 63' -- so its patch materializer was demonstrably unreliable), not by a spec defect. My atk_4 impl region is byte-identical to the recorded one; only the patch text differs, and mine resolves.

### FAITHFULNESS PRE-SCREEN (<D>/fuzz.py, before spending any oracle slot)
Each candidate body was instantiated on a fake storage with a scripted _post_process, the generator drained ITEM BY ITEM, and self.hashed_files read between items to recover the observable (pre-commit, post-commit) PAIR -- exactly the cut mapping.md claims. Compared against an INDEPENDENT Python transcription of each attack's Lean impl: 0/400 mismatches for gold, atk_3, atk_4, atk_5, atk_11, atk_13, atk_14, atk_15, atk_17, neg_fullbuffer, with the terminal allowance item exercised on 90 of the 400 cases. Excluded-domain probe (max_post_process_passes = 0): gold/atk_3/atk_13/atk_17/neg_fullbuffer RAISE UnboundLocalError (matching mapping.md's stated excluded domain); atk_4/atk_5/atk_11/atk_15 match their Lean impls there. So each graded patch really is the faithful refinement of its Lean impl on the admissible domain.

### A-LEG AUDIT (my focus per the brief)
refinement.md leg tags: leg1=R, leg2=I, leg3=I, leg4=I, leg5=I, leg6=R. Every leg is R or I; NO kind-3 leg. Hand-wave vocabulary scan of refinement.md (obviously/clearly/trivially/assume/by inspection/informally/morally/essentially the same/roughly/left to the reader): NONE.
The 'no A-leg' premise is CORRESPONDENT, verified independently rather than taken on trust:
  - Solution.lean vocabulary scan for axiom|opaque|noncomputable|partial|sorry|admit|native_decide|Classical.choice|unsafe|extern|implemented_by: the ONLY hit is the word 'opaque' inside a comment in the axioms region. The axioms marker region is comments only. meta.json: axioms=[], opaque_callees=[], deep_model_references=[] -- all consistent, so G-AX is legitimately a skip.
  - A walk over the patched post_process body (lines 216-260 of the patched file) lists every callee it names: self._post_process, self.hashed_files.update, matches_patterns, isinstance, range, RuntimeError, dict.values. Only self._post_process is a repo-defined unchanged callee; I confirmed from patch.diff's +/- lines that gold does NOT touch _post_process (the patch's only edits are inside post_process). Taking its record stream as the INPUT firstPass/laterPasses rather than axiomatizing it is therefore legitimate here: the patch edits only how post_process CONSUMES and RE-REPORTS those records.
  - self.hashed_files.update is not axiomatized either; it is modeled as the SPLIT POINT of the OutReport pair (leg 5 = I, leg 6 = R). I confirmed that split is LOAD-BEARING and not modeling slack: neg_fullbuffer moves every item to the far side of it and does NOT resolve (P2P 29/31, consistent over 3 attempts), while atk_14/atk_15 restructure freely WITHIN the pre-commit side and resolve. So the pair is neither too coarse (it rejects full-buffer) nor too fine (it admits within-component restaging).
  - matches_patterns is outside the modeled span (it computes adjustable_paths, which is an INPUT). RuntimeError/isinstance/range/dict.values are builtins.
  - Bundle patch.diff is BYTE-IDENTICAL to the dataset gold patch (2122 bytes both; base_commit 179ee13eb37348cd87169a198aec18fedccc8668; single file django/contrib/staticfiles/storage.py), as refinement.md claims.

### SCOPE NOTE (out of scope for refinement fidelity; flagged for a spec-strength role)
A patch that shrinks the real allowance max_post_process_passes from 5 to 1 does not resolve, but it is NOT a G-EQ counterexample: laterPasses is a universally-quantified INPUT, so changing the real loop bound changes only which input the spec is instantiated at and leaves the Lean impl text INVARIANT -- there is no same-spec Lean impl to reject. mapping.md states this limit explicitly ('laterPasses is by construction the passes that executed'). atk_17 is the closest in-scope probe of that dimension (a same-spec impl that special-cases the singleton pass count) and it verifies AND resolves. I flag it only so G-PANEL-1 can weigh whether the pass-count structure deserves modeling.

### Artifacts
atk_1..atk_18.lean (+ .log/.exit), ax_atk_*.lean (+ .log/.exit), pos_control.lean, gen.py, vrun.sh, bodies.py, mkpatch.py, fuzz.py, fuzzsrc_*.py, resolve_one.py, base_storage.py, storage_*.py, patch_*.diff, res_*.json (raw run_resolve reports), patches.json, payload.json.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

Modeled fn: HashedFilesMixin.post_process (django/contrib/staticfiles/storage.py:203) for django__django-14053. Reference = clean checkout of base_commit 179ee13eb3 (git archive into fresh mktemp -d) with patch.diff APPLIED (applied cleanly; both pre-existing /tmp worktrees were dirty so I did not use them).

METHOD (differential, real code not a paraphrase): extracted the post-patch post_process body VERBATIM via ast.get_source_segment from the patched tree and exec'd it — no hand-reconstruction. Driven against a Fake storage whose _post_process returns the per-invocation record stream (the modeled INPUT per mapping.md, since the patch leaves _post_process untouched) and whose self.hashed_files is a dict subclass that flags the instant .update() is called. Draining the generator item-by-item and reading that flag between items recovers exactly the OutReport pair (.1 = pre-commit hand-overs, .2 = post-commit). postProcessModel/firstStep/laterStep/upsertItem/allowanceItem were transliterated line-for-line from Solution.lean and compared under an exception-canonicalizing normalizer.

RESULTS — 0 divergences on ~340k inputs:
- 200,000 randomized cases under mapping.md's executed-passes encoding (max_post_process_passes = len(laterPasses)); allowance item exercised on 100,125.
- 60,000 cases with NO truncation rule: real fn given the true allowance of 5 and free to break early, model fed later5[:executed] where executed = observed _post_process call count - 1. Early break fired on 49,689, allowance on 6,664. This is the load-bearing check that the executed-prefix input encoding is not a hidden strengthening.
- 80,000 high-collision cases over 1-2 names to maximize upsert overwrite/aliasing pressure.
- 16 hand-built corners, all OK, including: intra-pass duplicate for the same adjustable name (REACHABLE in real _post_process — the ValueError yield at storage.py:301 does not return, so it falls through to the terminal yield); an adjustable file that ERRORS in the first pass (pre-commit) and is also reported by a later pass (post-commit), i.e. the same name legitimately appearing on BOTH sides — model reproduces this exactly; a later pass carrying an Exception (lands post-commit in the real code, as modeled); a later pass introducing a name absent from adjustable_paths; allowance firing with nothing collected; insertion-order preservation across later-pass overwrites; hashed_name=None; processed=False on an adjustable file.

PRECONDITION IS TIGHT, NOT OVER-STRONG: problem_pre_postProcess = (laterPasses != []). Probed the real fn at max_post_process_passes=0 -> UnboundLocalError('substitutions'), because substitutions is bound inside the range() loop while the `if substitutions:` guarding the terminal item is outside it. laterPasses=[] is reachable ONLY in that raising case (an allowance of >=1 always executes >=1 pass, possibly reporting nothing -> laterPasses=[[]], which IS admitted and was fuzzed). So the precondition excludes exactly the no-report domain and no real behavior.

STRUCTURAL CHECKS: markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend()) = True (spec region byte-identical). scripts/lean_verify.sh on Solution.lean exit 0. `#print axioms correct_postProcess` -> [propext, Quot.sound] — no sorryAx, proof is real. axioms region is legitimately empty and axiom_check.py is a documented G-AX skip: the unchanged producer _post_process is an INPUT, not an axiomatized callee, so there is no axiom that could over-constrain a callee.

DID NOT count as divergence (correctly per the brief): the pre-patch base version yields every record from every pass flat with nothing held back. Comparing the model against base would 'diverge' on exactly the patch delta; the model describes the fixed behavior, which is right.

ONE NON-BLOCKING DOC NIT (prose only, not a Prop, no input divergence): the problem_spec_postProcess docstring says 'every source file is handed over at most once'. That is an overstatement — an adjustable file that errors in the first pass is handed over pre-commit AND again post-commit if a later pass reports it (corner 1 above). The actual postcondition is exact equality with postProcessModel, which reproduces the real double hand-over faithfully, so the SPEC is not wrong; only the English gloss is loose. Not a faithfulness defect.

No input found on which the modeled function disagrees with the real patched callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

SCOPE / RELAXATION: this bundle carries NO relaxation, verified by my own measurement, not read off the file. `find -iname '*RELAX*'` over the whole instance dir -> zero hits (no RELAXED_LEAKAGE.md anywhere). Recursive key-walk of lean/meta.json -> no `relaxed_leakage` key (top-level value is literally absent; keys are axioms, conf_skip, deep_model_references, gates, modeled_functions, opaque_callees, patch_equals_gold, pbt_audit, prepatch_variants, region_hashes, schema_version, spec_provenance, verifier_pins). gates['G-LEAK'].mode == 'strict', status == 'pass'. So I judged this under the strict rule with no inherited disposition and no unavoidability argument to re-derive.

SPEC VIEW PINNED BY MY OWN COMPUTATION. markers.spec_view(Solution.lean, LeanBackend.language) -> sha256 4061f571a43f26c827895eac9a8304d74b01f22b20f7135a1ddb436b4b8de76a, which matches meta.json region_hashes.spec_view exactly. impl and proof regions are elided to placeholders, so my judgement covers exactly the consumer-visible text (all 136 lines read). markers.same_spec(Solution.lean, Solution_prepatch.lean) == True with identical spec_signature on both -> the spec region is byte-identical across the triple and the prepatch rival, i.e. it carries no impl-specific content.

ARTIFACT SOUNDNESS I RAN MYSELF. scripts/lean_verify.sh on Solution.lean with `#print axioms correct_postProcess` appended -> exit 0, 'depends on axioms: [propext, Quot.sound]'. No sorryAx: the proof is real, not fake.

MECHANICAL SCREEN I RE-RAN. leakage.screen(Solution.lean, LeanBackend, patch.diff, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. Independently: all 16 gold changed lines normalized (whitespace-stripped) against the normalized spec view -> 0 substring hits, so no gold-diff line is reproduced. No diff marker. No patched path. Every gold-side identifier is ABSENT from the spec view: processed_adjustable_paths, adjustable_paths, hashed_name, hashed_files, isinstance, yield, storage.py, staticfiles, max_post_process, substitutions, _post_process, django -> all False. The only patch-touched symbol the screen derives is `post_process`, and the public problem_statement names it in its very title ('HashedFilesMixin's post_process() yields multiple times for the same file'), so it localizes nothing the solver cannot already see.

LITERAL PROVENANCE CHECKED AGAINST THE REAL REPO. The one spec-view string literal that looked edit-shaped, allowanceItem = ("All", none, Except.error "Max post-process passes exceeded."), is PRE-PATCH public code. I checked out base_commit 179ee13eb37348cd87169a198aec18fedccc8668 into a fresh worktree and read django/contrib/staticfiles/storage.py:243-244: `yield 'All', None, RuntimeError('Max post-process passes exceeded.')` already exists there verbatim and the gold hunk does not touch it (the string does not appear in patch.diff at all -- 'Max post-process' in patch.diff == False). Reproducing base-commit source the solver can read is not leakage.

THE EDIT-SHAPED STRUCTURAL CHOICE IS THE DISCRIMINATOR, NOT A HINT. The most gold-shaped feature of the spec view is OutReport := List OutItem x List OutItem, the split of the report at 'the moment the run's accumulated name mapping is committed to the shared store'. I applied the load-bearing test: I built a file carrying the FROZEN spec regions from Solution.lean plus the PRE-PATCH orchestration body from Solution_prepatch.lean, and proved with my own witness (one adjustable file reported in the first pass and again in a later pass) that (a) prepatch_admissible : problem_pre_postProcess L closes on [propext], and (b) prepatch_refuted : NOT (problem_spec_postProcess ["a"] W L (implementation_postProcess ["a"] W L)) closes on [propext, Classical.choice, Quot.sound]. No sorryAx in either. So the spec provably rejects the pre-patch behavior on an admissible input: the clauses that look like gold narration are load-bearing spec content, and stripping them would let the pre-patch impl through. Independently, G-DIFF records the prepatch rival as 'verification failed' by design.

WHY THE SPLIT IS NOT A PROBLEM-STATEMENT-BEYOND FACET. The spec states the split ABSTRACTLY -- 'the accumulated name mapping is committed to the shared store' -- naming no file, no statement, no symbol, no line number. Both halves are publicly derivable: the problem_statement's own expected output shows one yield per file carrying the FINAL hash ('as admin/css/base.6b517d0d5813.css', not the intermediate 31652d31b392), which forces deferral until every pass has ended; and the commit itself, `self.hashed_files.update(hashed_files)`, already sits after the pass loop in the base_commit source the solver reads. 'Yield once, after all passes' plus public base-commit control flow gives 'after the commit' without the spec disclosing anything. The dedupe/order facet ('handed over at most once', 'in order of first appearance') is verbatim the public complaint. mapping.md confirms a correct rival stays free to reorder work or pick another collection type.

BUNDLE-ADDRESSES-REVIEWER CHECK, reported as a finding in its own right per my instructions. No consumer-facing file addresses me: grepping Solution.lean, mapping.md, refinement.md, conformance_check.py, axiom_check.py, patch.diff for panel/reviewer/verdict-directed phrasing -> zero hits, and meta.json has zero hits for 'you must' / 'you should submit' / 'record NO-LEAKAGE' / 'the honest verdict' / 'do not report'. verdict.md (NOT part of the spec view) does contain prior-role transcripts, including two earlier G-PANEL-3 notes that assert NO-LEAKAGE and one quoting a 'RECOMMENDATION FOR THE PANEL RECORD'. I inherited neither disposition: I recomputed the spec_view hash, re-ran the screen, checked literal provenance against the real base_commit checkout, and re-proved the load-bearing control with my own witness. My conclusion happens to agree with theirs but rests entirely on my measurements above.

CROSS-GATE OBSERVATION, OUTSIDE MY GATE AND NOT AFFECTING THIS VERDICT. gates['G-EQ'].status == 'fail': 'atk_4.lean verifies but its patch does not resolve -- FAIL_TO_PASS fails 1/1: post_processing behaves correctly; PASS_TO_PASS 31/31 pass'. That is a spec-TOO-WEAK finding (verify does not imply correct) -- the OPPOSITE failure mode from leakage -- so it does not undercut NO-LEAKAGE, and because this bundle carries no relaxation my verdict leans on no gate that is broken. It does mean the bundle is not releasable on G-EQ regardless of my gate. Recording it so the panel record is complete.

VERDICT: NO-LEAKAGE. The spec view reproduces no gold-diff line, names no patched file/module/symbol beyond the function the public problem_statement titles, carries no bug->fix narration, its only edit-shaped literal pre-exists unchanged in public base_commit source, and its most gold-shaped structural choice is provably the discriminator (my own sorry-free refutation of the pre-patch impl) rather than a disclosure.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.