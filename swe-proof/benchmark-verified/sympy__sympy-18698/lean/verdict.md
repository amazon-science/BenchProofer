# P2 adversarial audit — sympy__sympy-18698

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec is tight: conjuncts (1) (result.map snd).Nodup, (2) forall k, k in result.snd <-> k in factors.snd, and (3) forall p k, (p,k) in result -> p = prodOf factors k jointly and uniquely determine result as the SET {(prodOf factors k, k) | k in dedup mults}. No same-spec wrong impl closes with a clean proof, so no closing-but-non-resolving impl exists (verify => correct holds).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,104 +52,16 @@
 -- impl-start
 def implementation_combineFactors (factors : List (Int × Nat)) : List (Int × Nat) :=
   Id.run do
-    let mut result : List (Int × Nat) := []
-    for k in (factors.map Prod.snd).dedup do
-      let mut prod : Int := 1
-      for fk in factors do
-        if fk.2 = k then
-          prod := prod * fk.1
-      result := result ++ [(prod, k)]
-    return result
+    return factors
 -- impl-end
 
 -- proof-start
-/-- The inner loop folds the matching factors' products onto the accumulator;
-generalised over the accumulator so it reduces to `List.foldl` over the filtered
-list (matching `prodOf`). -/
-theorem inner_combineFactors_helper
-    (factors : List (Int × Nat)) (k : Nat) (init : Int) :
-    (Id.run (forIn factors init (fun fk r =>
-        (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
-         else pure (ForInStep.yield r) : Id (ForInStep Int)))))
-    = (factors.filter (fun fk => fk.2 = k)).foldl (fun acc fk => acc * fk.1) init := by
-  induction factors generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a.2 = k <;> simp [h, ih]
-
-/-- The outer loop appends one `(prodOf factors k, k)` entry per multiplicity;
-generalised over the accumulator so it reduces to a `List.map`. -/
-theorem outer_combineFactors_helper
-    (factors : List (Int × Nat)) (ks : List Nat) (init : List (Int × Nat)) :
-    (Id.run (forIn ks init (fun k r =>
-        (do
-          let prod ← (forIn factors (1:Int) (fun fk r =>
-              (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int))))
-          pure (ForInStep.yield (r ++ [(prod, k)])) : Id (ForInStep (List (Int × Nat)))))))
-    = init ++ ks.map (fun k => (prodOf factors k, k)) := by
-  induction ks generalizing init with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [show (forIn factors (1:Int) (fun fk r =>
-              (if fk.2 = a then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int))))
-        = Id.run (forIn factors (1:Int) (fun fk r =>
-              (if fk.2 = a then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int)))) from rfl]
-    rw [inner_combineFactors_helper, ih]
-    simp [prodOf, List.map_cons]
-
-/-- Closed form of the imperative implementation. -/
-theorem hbody_combineFactors (factors : List (Int × Nat)) :
-    implementation_combineFactors factors
-      = (factors.map Prod.snd).dedup.map (fun k => (prodOf factors k, k)) := by
-  unfold implementation_combineFactors
-  simp only [Id.run]
-  -- bridge the desugared body (`do pure PUnit.unit; …`) to the clean helper body
-  have h2 : (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>
-        (do
-          let r_1 ← (forIn factors (1:Int) fun fk r =>
-              (if fk.2 = k then do pure PUnit.unit; pure (ForInStep.yield (r * fk.1))
-               else do pure PUnit.unit; pure (ForInStep.yield r) : Id (ForInStep Int)))
-          pure PUnit.unit
-          pure (ForInStep.yield (r ++ [(r_1, k)])) : Id (ForInStep (List (Int × Nat)))))
-      = (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>
-        (do
-          let prod ← (forIn factors (1:Int) fun fk r =>
-              (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int)))
-          pure (ForInStep.yield (r ++ [(prod, k)])) : Id (ForInStep (List (Int × Nat))))) := rfl
-  rw [h2]
-  simp only [bind_pure]
-  show (Id.run _ : List (Int × Nat)) = _
-  rw [outer_combineFactors_helper]
-  simp
-
 theorem correct_combineFactors :
     ∀ (factors : List (Int × Nat)),
       problem_spec_combineFactors factors (implementation_combineFactors factors) := by
   intro factors
-  have key : (implementation_combineFactors factors).map Prod.snd
-      = (factors.map Prod.snd).dedup := by
-    rw [hbody_combineFactors, List.map_map]
-    exact List.map_id _
   refine ⟨?_, ?_, ?_⟩
-  · -- multiplicity column is `Nodup` (it is a `dedup`)
-    rw [key]; exact (factors.map Prod.snd).nodup_dedup
-  · -- the result's multiplicities are exactly the input's
-    intro k; rw [key]; exact List.mem_dedup
-  · -- each entry's factor is the product of the matching inputs
-    intro p k hmem
-    rw [hbody_combineFactors] at hmem
-    simp only [List.mem_map] at hmem
-    obtain ⟨k', _, hk'⟩ := hmem
-    rw [Prod.ext_iff] at hk'
-    obtain ⟨hp, hk⟩ := hk'
-    simp only at hp hk
-    rw [← hp, ← hk]
+  · simp [implementation_combineFactors]
+  · intro k; simp [implementation_combineFactors]
+  · intro p k hmem; simp [implementation_combineFactors] at hmem ⊢; sorry
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,105 +51,16 @@
 
 -- impl-start
 def implementation_combineFactors (factors : List (Int × Nat)) : List (Int × Nat) :=
-  Id.run do
-    let mut result : List (Int × Nat) := []
-    for k in (factors.map Prod.snd).dedup do
-      let mut prod : Int := 1
-      for fk in factors do
-        if fk.2 = k then
-          prod := prod * fk.1
-      result := result ++ [(prod, k)]
-    return result
+  []
 -- impl-end
 
 -- proof-start
-/-- The inner loop folds the matching factors' products onto the accumulator;
-generalised over the accumulator so it reduces to `List.foldl` over the filtered
-list (matching `prodOf`). -/
-theorem inner_combineFactors_helper
-    (factors : List (Int × Nat)) (k : Nat) (init : Int) :
-    (Id.run (forIn factors init (fun fk r =>
-        (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
-         else pure (ForInStep.yield r) : Id (ForInStep Int)))))
-    = (factors.filter (fun fk => fk.2 = k)).foldl (fun acc fk => acc * fk.1) init := by
-  induction factors generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a.2 = k <;> simp [h, ih]
-
-/-- The outer loop appends one `(prodOf factors k, k)` entry per multiplicity;
-generalised over the accumulator so it reduces to a `List.map`. -/
-theorem outer_combineFactors_helper
-    (factors : List (Int × Nat)) (ks : List Nat) (init : List (Int × Nat)) :
-    (Id.run (forIn ks init (fun k r =>
-        (do
-          let prod ← (forIn factors (1:Int) (fun fk r =>
-              (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int))))
-          pure (ForInStep.yield (r ++ [(prod, k)])) : Id (ForInStep (List (Int × Nat)))))))
-    = init ++ ks.map (fun k => (prodOf factors k, k)) := by
-  induction ks generalizing init with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [show (forIn factors (1:Int) (fun fk r =>
-              (if fk.2 = a then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int))))
-        = Id.run (forIn factors (1:Int) (fun fk r =>
-              (if fk.2 = a then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int)))) from rfl]
-    rw [inner_combineFactors_helper, ih]
-    simp [prodOf, List.map_cons]
-
-/-- Closed form of the imperative implementation. -/
-theorem hbody_combineFactors (factors : List (Int × Nat)) :
-    implementation_combineFactors factors
-      = (factors.map Prod.snd).dedup.map (fun k => (prodOf factors k, k)) := by
-  unfold implementation_combineFactors
-  simp only [Id.run]
-  -- bridge the desugared body (`do pure PUnit.unit; …`) to the clean helper body
-  have h2 : (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>
-        (do
-          let r_1 ← (forIn factors (1:Int) fun fk r =>
-              (if fk.2 = k then do pure PUnit.unit; pure (ForInStep.yield (r * fk.1))
-               else do pure PUnit.unit; pure (ForInStep.yield r) : Id (ForInStep Int)))
-          pure PUnit.unit
-          pure (ForInStep.yield (r ++ [(r_1, k)])) : Id (ForInStep (List (Int × Nat)))))
-      = (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>
-        (do
-          let prod ← (forIn factors (1:Int) fun fk r =>
-              (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int)))
-          pure (ForInStep.yield (r ++ [(prod, k)])) : Id (ForInStep (List (Int × Nat))))) := rfl
-  rw [h2]
-  simp only [bind_pure]
-  show (Id.run _ : List (Int × Nat)) = _
-  rw [outer_combineFactors_helper]
-  simp
-
 theorem correct_combineFactors :
     ∀ (factors : List (Int × Nat)),
       problem_spec_combineFactors factors (implementation_combineFactors factors) := by
   intro factors
-  have key : (implementation_combineFactors factors).map Prod.snd
-      = (factors.map Prod.snd).dedup := by
-    rw [hbody_combineFactors, List.map_map]
-    exact List.map_id _
   refine ⟨?_, ?_, ?_⟩
-  · -- multiplicity column is `Nodup` (it is a `dedup`)
-    rw [key]; exact (factors.map Prod.snd).nodup_dedup
-  · -- the result's multiplicities are exactly the input's
-    intro k; rw [key]; exact List.mem_dedup
-  · -- each entry's factor is the product of the matching inputs
-    intro p k hmem
-    rw [hbody_combineFactors] at hmem
-    simp only [List.mem_map] at hmem
-    obtain ⟨k', _, hk'⟩ := hmem
-    rw [Prod.ext_iff] at hk'
-    obtain ⟨hp, hk⟩ := hk'
-    simp only at hp hk
-    rw [← hp, ← hk]
+  · simp [implementation_combineFactors]
+  · intro k; simp [implementation_combineFactors]
+  · intro p k hmem; simp [implementation_combineFactors] at hmem
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,102 +54,18 @@
   Id.run do
     let mut result : List (Int × Nat) := []
     for k in (factors.map Prod.snd).dedup do
-      let mut prod : Int := 1
+      let mut prod : Int := 0
       for fk in factors do
         if fk.2 = k then
-          prod := prod * fk.1
+          prod := prod + fk.1
       result := result ++ [(prod, k)]
     return result
 -- impl-end
 
 -- proof-start
-/-- The inner loop folds the matching factors' products onto the accumulator;
-generalised over the accumulator so it reduces to `List.foldl` over the filtered
-list (matching `prodOf`). -/
-theorem inner_combineFactors_helper
-    (factors : List (Int × Nat)) (k : Nat) (init : Int) :
-    (Id.run (forIn factors init (fun fk r =>
-        (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
-         else pure (ForInStep.yield r) : Id (ForInStep Int)))))
-    = (factors.filter (fun fk => fk.2 = k)).foldl (fun acc fk => acc * fk.1) init := by
-  induction factors generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a.2 = k <;> simp [h, ih]
-
-/-- The outer loop appends one `(prodOf factors k, k)` entry per multiplicity;
-generalised over the accumulator so it reduces to a `List.map`. -/
-theorem outer_combineFactors_helper
-    (factors : List (Int × Nat)) (ks : List Nat) (init : List (Int × Nat)) :
-    (Id.run (forIn ks init (fun k r =>
-        (do
-          let prod ← (forIn factors (1:Int) (fun fk r =>
-              (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int))))
-          pure (ForInStep.yield (r ++ [(prod, k)])) : Id (ForInStep (List (Int × Nat)))))))
-    = init ++ ks.map (fun k => (prodOf factors k, k)) := by
-  induction ks generalizing init with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [show (forIn factors (1:Int) (fun fk r =>
-              (if fk.2 = a then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int))))
-        = Id.run (forIn factors (1:Int) (fun fk r =>
-              (if fk.2 = a then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int)))) from rfl]
-    rw [inner_combineFactors_helper, ih]
-    simp [prodOf, List.map_cons]
-
-/-- Closed form of the imperative implementation. -/
-theorem hbody_combineFactors (factors : List (Int × Nat)) :
-    implementation_combineFactors factors
-      = (factors.map Prod.snd).dedup.map (fun k => (prodOf factors k, k)) := by
-  unfold implementation_combineFactors
-  simp only [Id.run]
-  -- bridge the desugared body (`do pure PUnit.unit; …`) to the clean helper body
-  have h2 : (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>
-        (do
-          let r_1 ← (forIn factors (1:Int) fun fk r =>
-              (if fk.2 = k then do pure PUnit.unit; pure (ForInStep.yield (r * fk.1))
-               else do pure PUnit.unit; pure (ForInStep.yield r) : Id (ForInStep Int)))
-          pure PUnit.unit
-          pure (ForInStep.yield (r ++ [(r_1, k)])) : Id (ForInStep (List (Int × Nat)))))
-      = (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>
-        (do
-          let prod ← (forIn factors (1:Int) fun fk r =>
-              (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int)))
-          pure (ForInStep.yield (r ++ [(prod, k)])) : Id (ForInStep (List (Int × Nat))))) := rfl
-  rw [h2]
-  simp only [bind_pure]
-  show (Id.run _ : List (Int × Nat)) = _
-  rw [outer_combineFactors_helper]
-  simp
-
 theorem correct_combineFactors :
     ∀ (factors : List (Int × Nat)),
       problem_spec_combineFactors factors (implementation_combineFactors factors) := by
   intro factors
-  have key : (implementation_combineFactors factors).map Prod.snd
-      = (factors.map Prod.snd).dedup := by
-    rw [hbody_combineFactors, List.map_map]
-    exact List.map_id _
-  refine ⟨?_, ?_, ?_⟩
-  · -- multiplicity column is `Nodup` (it is a `dedup`)
-    rw [key]; exact (factors.map Prod.snd).nodup_dedup
-  · -- the result's multiplicities are exactly the input's
-    intro k; rw [key]; exact List.mem_dedup
-  · -- each entry's factor is the product of the matching inputs
-    intro p k hmem
-    rw [hbody_combineFactors] at hmem
-    simp only [List.mem_map] at hmem
-    obtain ⟨k', _, hk'⟩ := hmem
-    rw [Prod.ext_iff] at hk'
-    obtain ⟨hp, hk⟩ := hk'
-    simp only at hp hk
-    rw [← hp, ← hk]
+  refine ⟨?_, ?_, ?_⟩ <;> sorry
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,102 +54,15 @@
   Id.run do
     let mut result : List (Int × Nat) := []
     for k in (factors.map Prod.snd).dedup do
-      let mut prod : Int := 1
-      for fk in factors do
-        if fk.2 = k then
-          prod := prod * fk.1
-      result := result ++ [(prod, k)]
+      let p := ((factors.filter (fun fk => fk.2 = k)).headD (0, k)).1
+      result := result ++ [(p, k)]
     return result
 -- impl-end
 
 -- proof-start
-/-- The inner loop folds the matching factors' products onto the accumulator;
-generalised over the accumulator so it reduces to `List.foldl` over the filtered
-list (matching `prodOf`). -/
-theorem inner_combineFactors_helper
-    (factors : List (Int × Nat)) (k : Nat) (init : Int) :
-    (Id.run (forIn factors init (fun fk r =>
-        (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
-         else pure (ForInStep.yield r) : Id (ForInStep Int)))))
-    = (factors.filter (fun fk => fk.2 = k)).foldl (fun acc fk => acc * fk.1) init := by
-  induction factors generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a.2 = k <;> simp [h, ih]
-
-/-- The outer loop appends one `(prodOf factors k, k)` entry per multiplicity;
-generalised over the accumulator so it reduces to a `List.map`. -/
-theorem outer_combineFactors_helper
-    (factors : List (Int × Nat)) (ks : List Nat) (init : List (Int × Nat)) :
-    (Id.run (forIn ks init (fun k r =>
-        (do
-          let prod ← (forIn factors (1:Int) (fun fk r =>
-              (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int))))
-          pure (ForInStep.yield (r ++ [(prod, k)])) : Id (ForInStep (List (Int × Nat)))))))
-    = init ++ ks.map (fun k => (prodOf factors k, k)) := by
-  induction ks generalizing init with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [show (forIn factors (1:Int) (fun fk r =>
-              (if fk.2 = a then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int))))
-        = Id.run (forIn factors (1:Int) (fun fk r =>
-              (if fk.2 = a then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int)))) from rfl]
-    rw [inner_combineFactors_helper, ih]
-    simp [prodOf, List.map_cons]
-
-/-- Closed form of the imperative implementation. -/
-theorem hbody_combineFactors (factors : List (Int × Nat)) :
-    implementation_combineFactors factors
-      = (factors.map Prod.snd).dedup.map (fun k => (prodOf factors k, k)) := by
-  unfold implementation_combineFactors
-  simp only [Id.run]
-  -- bridge the desugared body (`do pure PUnit.unit; …`) to the clean helper body
-  have h2 : (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>
-        (do
-          let r_1 ← (forIn factors (1:Int) fun fk r =>
-              (if fk.2 = k then do pure PUnit.unit; pure (ForInStep.yield (r * fk.1))
-               else do pure PUnit.unit; pure (ForInStep.yield r) : Id (ForInStep Int)))
-          pure PUnit.unit
-          pure (ForInStep.yield (r ++ [(r_1, k)])) : Id (ForInStep (List (Int × Nat)))))
-      = (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>
-        (do
-          let prod ← (forIn factors (1:Int) fun fk r =>
-              (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int)))
-          pure (ForInStep.yield (r ++ [(prod, k)])) : Id (ForInStep (List (Int × Nat))))) := rfl
-  rw [h2]
-  simp only [bind_pure]
-  show (Id.run _ : List (Int × Nat)) = _
-  rw [outer_combineFactors_helper]
-  simp
-
 theorem correct_combineFactors :
     ∀ (factors : List (Int × Nat)),
       problem_spec_combineFactors factors (implementation_combineFactors factors) := by
   intro factors
-  have key : (implementation_combineFactors factors).map Prod.snd
-      = (factors.map Prod.snd).dedup := by
-    rw [hbody_combineFactors, List.map_map]
-    exact List.map_id _
-  refine ⟨?_, ?_, ?_⟩
-  · -- multiplicity column is `Nodup` (it is a `dedup`)
-    rw [key]; exact (factors.map Prod.snd).nodup_dedup
-  · -- the result's multiplicities are exactly the input's
-    intro k; rw [key]; exact List.mem_dedup
-  · -- each entry's factor is the product of the matching inputs
-    intro p k hmem
-    rw [hbody_combineFactors] at hmem
-    simp only [List.mem_map] at hmem
-    obtain ⟨k', _, hk'⟩ := hmem
-    rw [Prod.ext_iff] at hk'
-    obtain ⟨hp, hk⟩ := hk'
-    simp only at hp hk
-    rw [← hp, ← hk]
+  refine ⟨?_, ?_, ?_⟩ <;> sorry
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,8 +53,8 @@
 def implementation_combineFactors (factors : List (Int × Nat)) : List (Int × Nat) :=
   Id.run do
     let mut result : List (Int × Nat) := []
+    let mut prod : Int := 1
     for k in (factors.map Prod.snd).dedup do
-      let mut prod : Int := 1
       for fk in factors do
         if fk.2 = k then
           prod := prod * fk.1
@@ -63,93 +63,9 @@
 -- impl-end
 
 -- proof-start
-/-- The inner loop folds the matching factors' products onto the accumulator;
-generalised over the accumulator so it reduces to `List.foldl` over the filtered
-list (matching `prodOf`). -/
-theorem inner_combineFactors_helper
-    (factors : List (Int × Nat)) (k : Nat) (init : Int) :
-    (Id.run (forIn factors init (fun fk r =>
-        (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
-         else pure (ForInStep.yield r) : Id (ForInStep Int)))))
-    = (factors.filter (fun fk => fk.2 = k)).foldl (fun acc fk => acc * fk.1) init := by
-  induction factors generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a.2 = k <;> simp [h, ih]
-
-/-- The outer loop appends one `(prodOf factors k, k)` entry per multiplicity;
-generalised over the accumulator so it reduces to a `List.map`. -/
-theorem outer_combineFactors_helper
-    (factors : List (Int × Nat)) (ks : List Nat) (init : List (Int × Nat)) :
-    (Id.run (forIn ks init (fun k r =>
-        (do
-          let prod ← (forIn factors (1:Int) (fun fk r =>
-              (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int))))
-          pure (ForInStep.yield (r ++ [(prod, k)])) : Id (ForInStep (List (Int × Nat)))))))
-    = init ++ ks.map (fun k => (prodOf factors k, k)) := by
-  induction ks generalizing init with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [show (forIn factors (1:Int) (fun fk r =>
-              (if fk.2 = a then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int))))
-        = Id.run (forIn factors (1:Int) (fun fk r =>
-              (if fk.2 = a then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int)))) from rfl]
-    rw [inner_combineFactors_helper, ih]
-    simp [prodOf, List.map_cons]
-
-/-- Closed form of the imperative implementation. -/
-theorem hbody_combineFactors (factors : List (Int × Nat)) :
-    implementation_combineFactors factors
-      = (factors.map Prod.snd).dedup.map (fun k => (prodOf factors k, k)) := by
-  unfold implementation_combineFactors
-  simp only [Id.run]
-  -- bridge the desugared body (`do pure PUnit.unit; …`) to the clean helper body
-  have h2 : (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>
-        (do
-          let r_1 ← (forIn factors (1:Int) fun fk r =>
-              (if fk.2 = k then do pure PUnit.unit; pure (ForInStep.yield (r * fk.1))
-               else do pure PUnit.unit; pure (ForInStep.yield r) : Id (ForInStep Int)))
-          pure PUnit.unit
-          pure (ForInStep.yield (r ++ [(r_1, k)])) : Id (ForInStep (List (Int × Nat)))))
-      = (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>
-        (do
-          let prod ← (forIn factors (1:Int) fun fk r =>
-              (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int)))
-          pure (ForInStep.yield (r ++ [(prod, k)])) : Id (ForInStep (List (Int × Nat))))) := rfl
-  rw [h2]
-  simp only [bind_pure]
-  show (Id.run _ : List (Int × Nat)) = _
-  rw [outer_combineFactors_helper]
-  simp
-
 theorem correct_combineFactors :
     ∀ (factors : List (Int × Nat)),
       problem_spec_combineFactors factors (implementation_combineFactors factors) := by
   intro factors
-  have key : (implementation_combineFactors factors).map Prod.snd
-      = (factors.map Prod.snd).dedup := by
-    rw [hbody_combineFactors, List.map_map]
-    exact List.map_id _
-  refine ⟨?_, ?_, ?_⟩
-  · -- multiplicity column is `Nodup` (it is a `dedup`)
-    rw [key]; exact (factors.map Prod.snd).nodup_dedup
-  · -- the result's multiplicities are exactly the input's
-    intro k; rw [key]; exact List.mem_dedup
-  · -- each entry's factor is the product of the matching inputs
-    intro p k hmem
-    rw [hbody_combineFactors] at hmem
-    simp only [List.mem_map] at hmem
-    obtain ⟨k', _, hk'⟩ := hmem
-    rw [Prod.ext_iff] at hk'
-    obtain ⟨hp, hk⟩ := hk'
-    simp only at hp hk
-    rw [← hp, ← hk]
+  refine ⟨?_, ?_, ?_⟩ <;> sorry
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,104 +52,16 @@
 -- impl-start
 def implementation_combineFactors (factors : List (Int × Nat)) : List (Int × Nat) :=
   Id.run do
-    let mut result : List (Int × Nat) := []
-    for k in (factors.map Prod.snd).dedup do
-      let mut prod : Int := 1
-      for fk in factors do
-        if fk.2 = k then
-          prod := prod * fk.1
-      result := result ++ [(prod, k)]
-    return result
+    let base := (factors.map Prod.snd).dedup.map (fun k =>
+      ((factors.filter (fun fk => fk.2 = k)).foldl (fun acc fk => acc * fk.1) 1, k))
+    -- ungrounded: echo the whole base list twice (breaks Nodup)
+    return base ++ base
 -- impl-end
 
 -- proof-start
-/-- The inner loop folds the matching factors' products onto the accumulator;
-generalised over the accumulator so it reduces to `List.foldl` over the filtered
-list (matching `prodOf`). -/
-theorem inner_combineFactors_helper
-    (factors : List (Int × Nat)) (k : Nat) (init : Int) :
-    (Id.run (forIn factors init (fun fk r =>
-        (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
-         else pure (ForInStep.yield r) : Id (ForInStep Int)))))
-    = (factors.filter (fun fk => fk.2 = k)).foldl (fun acc fk => acc * fk.1) init := by
-  induction factors generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a.2 = k <;> simp [h, ih]
-
-/-- The outer loop appends one `(prodOf factors k, k)` entry per multiplicity;
-generalised over the accumulator so it reduces to a `List.map`. -/
-theorem outer_combineFactors_helper
-    (factors : List (Int × Nat)) (ks : List Nat) (init : List (Int × Nat)) :
-    (Id.run (forIn ks init (fun k r =>
-        (do
-          let prod ← (forIn factors (1:Int) (fun fk r =>
-              (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int))))
-          pure (ForInStep.yield (r ++ [(prod, k)])) : Id (ForInStep (List (Int × Nat)))))))
-    = init ++ ks.map (fun k => (prodOf factors k, k)) := by
-  induction ks generalizing init with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [show (forIn factors (1:Int) (fun fk r =>
-              (if fk.2 = a then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int))))
-        = Id.run (forIn factors (1:Int) (fun fk r =>
-              (if fk.2 = a then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int)))) from rfl]
-    rw [inner_combineFactors_helper, ih]
-    simp [prodOf, List.map_cons]
-
-/-- Closed form of the imperative implementation. -/
-theorem hbody_combineFactors (factors : List (Int × Nat)) :
-    implementation_combineFactors factors
-      = (factors.map Prod.snd).dedup.map (fun k => (prodOf factors k, k)) := by
-  unfold implementation_combineFactors
-  simp only [Id.run]
-  -- bridge the desugared body (`do pure PUnit.unit; …`) to the clean helper body
-  have h2 : (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>
-        (do
-          let r_1 ← (forIn factors (1:Int) fun fk r =>
-              (if fk.2 = k then do pure PUnit.unit; pure (ForInStep.yield (r * fk.1))
-               else do pure PUnit.unit; pure (ForInStep.yield r) : Id (ForInStep Int)))
-          pure PUnit.unit
-          pure (ForInStep.yield (r ++ [(r_1, k)])) : Id (ForInStep (List (Int × Nat)))))
-      = (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>
-        (do
-          let prod ← (forIn factors (1:Int) fun fk r =>
-              (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int)))
-          pure (ForInStep.yield (r ++ [(prod, k)])) : Id (ForInStep (List (Int × Nat))))) := rfl
-  rw [h2]
-  simp only [bind_pure]
-  show (Id.run _ : List (Int × Nat)) = _
-  rw [outer_combineFactors_helper]
-  simp
-
 theorem correct_combineFactors :
     ∀ (factors : List (Int × Nat)),
       problem_spec_combineFactors factors (implementation_combineFactors factors) := by
   intro factors
-  have key : (implementation_combineFactors factors).map Prod.snd
-      = (factors.map Prod.snd).dedup := by
-    rw [hbody_combineFactors, List.map_map]
-    exact List.map_id _
-  refine ⟨?_, ?_, ?_⟩
-  · -- multiplicity column is `Nodup` (it is a `dedup`)
-    rw [key]; exact (factors.map Prod.snd).nodup_dedup
-  · -- the result's multiplicities are exactly the input's
-    intro k; rw [key]; exact List.mem_dedup
-  · -- each entry's factor is the product of the matching inputs
-    intro p k hmem
-    rw [hbody_combineFactors] at hmem
-    simp only [List.mem_map] at hmem
-    obtain ⟨k', _, hk'⟩ := hmem
-    rw [Prod.ext_iff] at hk'
-    obtain ⟨hp, hk⟩ := hk'
-    simp only at hp hk
-    rw [← hp, ← hk]
+  refine ⟨?_, ?_, ?_⟩ <;> sorry
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,100 +56,16 @@
     for k in (factors.map Prod.snd).dedup do
       let mut prod : Int := 1
       for fk in factors do
-        if fk.2 = k then
+        if fk.2 ≠ k then
           prod := prod * fk.1
       result := result ++ [(prod, k)]
     return result
 -- impl-end
 
 -- proof-start
-/-- The inner loop folds the matching factors' products onto the accumulator;
-generalised over the accumulator so it reduces to `List.foldl` over the filtered
-list (matching `prodOf`). -/
-theorem inner_combineFactors_helper
-    (factors : List (Int × Nat)) (k : Nat) (init : Int) :
-    (Id.run (forIn factors init (fun fk r =>
-        (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
-         else pure (ForInStep.yield r) : Id (ForInStep Int)))))
-    = (factors.filter (fun fk => fk.2 = k)).foldl (fun acc fk => acc * fk.1) init := by
-  induction factors generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a.2 = k <;> simp [h, ih]
-
-/-- The outer loop appends one `(prodOf factors k, k)` entry per multiplicity;
-generalised over the accumulator so it reduces to a `List.map`. -/
-theorem outer_combineFactors_helper
-    (factors : List (Int × Nat)) (ks : List Nat) (init : List (Int × Nat)) :
-    (Id.run (forIn ks init (fun k r =>
-        (do
-          let prod ← (forIn factors (1:Int) (fun fk r =>
-              (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int))))
-          pure (ForInStep.yield (r ++ [(prod, k)])) : Id (ForInStep (List (Int × Nat)))))))
-    = init ++ ks.map (fun k => (prodOf factors k, k)) := by
-  induction ks generalizing init with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [show (forIn factors (1:Int) (fun fk r =>
-              (if fk.2 = a then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int))))
-        = Id.run (forIn factors (1:Int) (fun fk r =>
-              (if fk.2 = a then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int)))) from rfl]
-    rw [inner_combineFactors_helper, ih]
-    simp [prodOf, List.map_cons]
-
-/-- Closed form of the imperative implementation. -/
-theorem hbody_combineFactors (factors : List (Int × Nat)) :
-    implementation_combineFactors factors
-      = (factors.map Prod.snd).dedup.map (fun k => (prodOf factors k, k)) := by
-  unfold implementation_combineFactors
-  simp only [Id.run]
-  -- bridge the desugared body (`do pure PUnit.unit; …`) to the clean helper body
-  have h2 : (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>
-        (do
-          let r_1 ← (forIn factors (1:Int) fun fk r =>
-              (if fk.2 = k then do pure PUnit.unit; pure (ForInStep.yield (r * fk.1))
-               else do pure PUnit.unit; pure (ForInStep.yield r) : Id (ForInStep Int)))
-          pure PUnit.unit
-          pure (ForInStep.yield (r ++ [(r_1, k)])) : Id (ForInStep (List (Int × Nat)))))
-      = (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>
-        (do
-          let prod ← (forIn factors (1:Int) fun fk r =>
-              (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
-               else pure (ForInStep.yield r) : Id (ForInStep Int)))
-          pure (ForInStep.yield (r ++ [(prod, k)])) : Id (ForInStep (List (Int × Nat))))) := rfl
-  rw [h2]
-  simp only [bind_pure]
-  show (Id.run _ : List (Int × Nat)) = _
-  rw [outer_combineFactors_helper]
-  simp
-
 theorem correct_combineFactors :
     ∀ (factors : List (Int × Nat)),
       problem_spec_combineFactors factors (implementation_combineFactors factors) := by
   intro factors
-  have key : (implementation_combineFactors factors).map Prod.snd
-      = (factors.map Prod.snd).dedup := by
-    rw [hbody_combineFactors, List.map_map]
-    exact List.map_id _
-  refine ⟨?_, ?_, ?_⟩
-  · -- multiplicity column is `Nodup` (it is a `dedup`)
-    rw [key]; exact (factors.map Prod.snd).nodup_dedup
-  · -- the result's multiplicities are exactly the input's
-    intro k; rw [key]; exact List.mem_dedup
-  · -- each entry's factor is the product of the matching inputs
-    intro p k hmem
-    rw [hbody_combineFactors] at hmem
-    simp only [List.mem_map] at hmem
-    obtain ⟨k', _, hk'⟩ := hmem
-    rw [Prod.ext_iff] at hk'
-    obtain ⟨hp, hk⟩ := hk'
-    simp only at hp hk
-    rw [← hp, ← hk]
+  refine ⟨?_, ?_, ?_⟩ <;> sorry
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Consolidating a list of factors tagged by multiplicity.

The input is a list of `(factor, multiplicity)` pairs.  Several distinct factors
may carry the *same* multiplicity.  The desired result lists each multiplicity
that occurs **exactly once**, pairing it with the product of all the input
factors that carried that multiplicity.  No multiplicity that occurs in the
input is dropped, and none is invented; for every retained multiplicity the
accompanying factor is precisely the product of the input factors sharing it.

A factor is modelled as an element of a commutative monoid (here the integers
under multiplication); "combining" factors is taking their product.  The order
in which the consolidated entries are returned is not part of the contract — a
consumer re-orders them — so the result is pinned as a set: which multiplicities
appear, that each appears only once, and what product accompanies each.
-/

-- axioms-start
-- No unchanged outside callee is consumed.  The consolidation is modelled
-- deeply: the product accompanying a multiplicity is spelled out as the fold of
-- the matching input factors, so there is no `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
/-- The product of every input factor whose multiplicity equals `k`
(`1` when none match).  Matches the inner accumulating loop of the
implementation: filter to the matching pairs, then fold their factors. -/
def prodOf (factors : List (Int × Nat)) (k : Nat) : Int :=
  (factors.filter (fun fk => fk.2 = k)).foldl (fun acc fk => acc * fk.1) 1
-- pure-end

-- post-conditions-start
/-- The consolidated factor list, pinned as a set:

  * each multiplicity appears at most once (`Nodup` on the multiplicity column);
  * the multiplicities appearing in the result are exactly those appearing in
    the input (none dropped, none invented);
  * every result entry pairs a multiplicity `k` with the product of all input
    factors carrying that multiplicity.

Together these determine the result uniquely up to ordering. -/
def problem_spec_combineFactors
    (factors : List (Int × Nat)) (result : List (Int × Nat)) : Prop :=
  (result.map Prod.snd).Nodup
  ∧ (∀ k, k ∈ result.map Prod.snd ↔ k ∈ factors.map Prod.snd)
  ∧ (∀ p k, (p, k) ∈ result → p = prodOf factors k)
-- post-conditions-end

-- impl-start
def implementation_combineFactors (factors : List (Int × Nat)) : List (Int × Nat) :=
  Id.run do
    let mut result : List (Int × Nat) := []
    for k in (factors.map Prod.snd).dedup do
      let mut prod : Int := 1
      for fk in factors do
        if fk.2 = k then
          prod := prod * fk.1
      result := result ++ [(prod, k)]
    return result
-- impl-end

-- proof-start
/-- The inner loop folds the matching factors' products onto the accumulator;
generalised over the accumulator so it reduces to `List.foldl` over the filtered
list (matching `prodOf`). -/
theorem inner_combineFactors_helper
    (factors : List (Int × Nat)) (k : Nat) (init : Int) :
    (Id.run (forIn factors init (fun fk r =>
        (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
         else pure (ForInStep.yield r) : Id (ForInStep Int)))))
    = (factors.filter (fun fk => fk.2 = k)).foldl (fun acc fk => acc * fk.1) init := by
  induction factors generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : a.2 = k <;> simp [h, ih]

/-- The outer loop appends one `(prodOf factors k, k)` entry per multiplicity;
generalised over the accumulator so it reduces to a `List.map`. -/
theorem outer_combineFactors_helper
    (factors : List (Int × Nat)) (ks : List Nat) (init : List (Int × Nat)) :
    (Id.run (forIn ks init (fun k r =>
        (do
          let prod ← (forIn factors (1:Int) (fun fk r =>
              (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
               else pure (ForInStep.yield r) : Id (ForInStep Int))))
          pure (ForInStep.yield (r ++ [(prod, k)])) : Id (ForInStep (List (Int × Nat)))))))
    = init ++ ks.map (fun k => (prodOf factors k, k)) := by
  induction ks generalizing init with
  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [show (forIn factors (1:Int) (fun fk r =>
              (if fk.2 = a then pure (ForInStep.yield (r * fk.1))
               else pure (ForInStep.yield r) : Id (ForInStep Int))))
        = Id.run (forIn factors (1:Int) (fun fk r =>
              (if fk.2 = a then pure (ForInStep.yield (r * fk.1))
               else pure (ForInStep.yield r) : Id (ForInStep Int)))) from rfl]
    rw [inner_combineFactors_helper, ih]
    simp [prodOf, List.map_cons]

/-- Closed form of the imperative implementation. -/
theorem hbody_combineFactors (factors : List (Int × Nat)) :
    implementation_combineFactors factors
      = (factors.map Prod.snd).dedup.map (fun k => (prodOf factors k, k)) := by
  unfold implementation_combineFactors
  simp only [Id.run]
  -- bridge the desugared body (`do pure PUnit.unit; …`) to the clean helper body
  have h2 : (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>
        (do
          let r_1 ← (forIn factors (1:Int) fun fk r =>
              (if fk.2 = k then do pure PUnit.unit; pure (ForInStep.yield (r * fk.1))
               else do pure PUnit.unit; pure (ForInStep.yield r) : Id (ForInStep Int)))
          pure PUnit.unit
          pure (ForInStep.yield (r ++ [(r_1, k)])) : Id (ForInStep (List (Int × Nat)))))
      = (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>
        (do
          let prod ← (forIn factors (1:Int) fun fk r =>
              (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
               else pure (ForInStep.yield r) : Id (ForInStep Int)))
          pure (ForInStep.yield (r ++ [(prod, k)])) : Id (ForInStep (List (Int × Nat))))) := rfl
  rw [h2]
  simp only [bind_pure]
  show (Id.run _ : List (Int × Nat)) = _
  rw [outer_combineFactors_helper]
  simp

theorem correct_combineFactors :
    ∀ (factors : List (Int × Nat)),
      problem_spec_combineFactors factors (implementation_combineFactors factors) := by
  intro factors
  have key : (implementation_combineFactors factors).map Prod.snd
      = (factors.map Prod.snd).dedup := by
    rw [hbody_combineFactors, List.map_map]
    exact List.map_id _
  refine ⟨?_, ?_, ?_⟩
  · -- multiplicity column is `Nodup` (it is a `dedup`)
    rw [key]; exact (factors.map Prod.snd).nodup_dedup
  · -- the result's multiplicities are exactly the input's
    intro k; rw [key]; exact List.mem_dedup
  · -- each entry's factor is the product of the matching inputs
    intro p k hmem
    rw [hbody_combineFactors] at hmem
    simp only [List.mem_map] at hmem
    obtain ⟨k', _, hk'⟩ := hmem
    rw [Prod.ext_iff] at hk'
    obtain ⟨hp, hk⟩ := hk'
    simp only at hp hk
    rw [← hp, ← hk]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Protocol executed same_spec=True verified for all 7 attacks + positive_control against the frozen Solution.lean (only impl+proof regions vary; axioms/pure/pre/post byte-identical). Attack verifications run as background Bash jobs, 4 at a time.

Command for each: `bash scripts/lean_verify.sh <file>` from project root.

### Results
- positive_control.lean (gold impl): exit 0 (closes). `#print axioms correct_combineFactors` = [propext, Classical.choice, Quot.sound] — clean, NO sorryAx.
- atk_1.lean (identity `return factors` = the PREPATCH BUG): exit 1, genuine unsolved goal `(List.map Prod.snd factors).Nodup` (case refine_1). Prepatch bug reproduced: does NOT close. Fails conjunct (1) when two factors share a multiplicity, and (3) (factor != prodOf).
- atk_2.lean (empty `[]`): exit 1, genuine unsolved membership goal (case refine_2). Fails conjunct (2) — a witnessed multiplicity is missing.
- atk_3.lean (SUM not product; prod:=0, +): exit 3 (sorry). Fails (3): e.g. [(2,1),(3,1)] -> (5,1) but prodOf=6.
- atk_4.lean (first matching factor only, headD): exit 3 (sorry). Fails (3): [(2,1),(3,1)] -> (2,1) vs prodOf=6.
- atk_5.lean (control-flow-effect: accumulator `prod` NOT reset between multiplicities, carried across k): exit 3 (sorry). Fails (3): [(2,1),(3,2)] -> (2,1),(6,2) but prodOf for k=2 is 3.
- atk_6.lean (ungrounded/echo: return base ++ base, doubling every entry): exit 3 (sorry). Fails (1) Nodup: [(6,1),(6,1)].
- atk_7.lean (wrong filter `fk.2 != k`): exit 3 (sorry). Fails (3): [(2,1),(3,1)] -> (1,1) vs prodOf=6.

CONFIRMATION the proofs are genuinely unclosable (not lazy proofs): disprove.lean #evals each attack impl vs the spec-determined gold set on concrete inputs. Every attack diverges from gold, each violating a specific conjunct (outputs shown above). A false conjunct is unprovable, so no clean-axiom proof exists for any attack. Since NO wrong impl closes, there is nothing to materialize/resolve — no patch needed (patches={}).

refinement.md audit: all legs are R or I; there are NO A-consumed / A-reference legs (empty axioms block; consolidation modeled DEEPLY via prodOf=foldl(*)1 and dedup; axiom_check.py is a correct skip-stub). No kind-3 (changed-inexpressible) leg. The deep-model <-> patch correspondence (factor -> Int under *, set -> dedup, reduce(mul,gen) -> foldl(*)1) is mechanically driven by G-CONF against the REAL patched sqf_list (30002 checks, 0 disagreements per bundle record).

Conclusion: verify => correct holds for this spec — SOUND. >=5 distinct same-spec wrong impls (7 total, spanning partial-domain/boundary/control-flow-effect/ungrounded-oracle-echo) attempted and none breaks it.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec is tight: conjuncts (1) (result.map snd).Nodup, (2) forall k, k in result.snd <-> k in factors.snd, and (3) forall p k, (p,k) in result -> p = prodOf factors k jointly and uniquely determine result as the SET {(prodOf factors k, k) | k in dedup mults}. No same-spec wrong impl closes with a clean proof, so no closing-but-non-resolving impl exists (verify => correct holds).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Consolidating a list of factors tagged by multiplicity.

The input is a list of `(factor, multiplicity)` pairs.  Several distinct factors
may carry the *same* multiplicity.  The desired result lists each multiplicity
that occurs **exactly once**, pairing it with the product of all the input
factors that carried that multiplicity.  No multiplicity that occurs in the
input is dropped, and none is invented; for every retained multiplicity the
accompanying factor is precisely the product of the input factors sharing it.

A factor is modelled as an element of a commutative monoid (here the integers
under multiplication); "combining" factors is taking their product.  The order
in which the consolidated entries are returned is not part of the contract — a
consumer re-orders them — so the result is pinned as a set: which multiplicities
appear, that each appears only once, and what product accompanies each.
-/

-- axioms-start
-- No unchanged outside callee is consumed.  The consolidation is modelled
-- deeply: the product accompanying a multiplicity is spelled out as the fold of
-- the matching input factors, so there is no `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
/-- The product of every input factor whose multiplicity equals `k`
(`1` when none match).  Matches the inner accumulating loop of the
implementation: filter to the matching pairs, then fold their factors. -/
def prodOf (factors : List (Int × Nat)) (k : Nat) : Int :=
  (factors.filter (fun fk => fk.2 = k)).foldl (fun acc fk => acc * fk.1) 1
-- pure-end

-- post-conditions-start
/-- The consolidated factor list, pinned as a set:

  * each multiplicity appears at most once (`Nodup` on the multiplicity column);
  * the multiplicities appearing in the result are exactly those appearing in
    the input (none dropped, none invented);
  * every result entry pairs a multiplicity `k` with the product of all input
    factors carrying that multiplicity.

Together these determine the result uniquely up to ordering. -/
def problem_spec_combineFactors
    (factors : List (Int × Nat)) (result : List (Int × Nat)) : Prop :=
  (result.map Prod.snd).Nodup
  ∧ (∀ k, k ∈ result.map Prod.snd ↔ k ∈ factors.map Prod.snd)
  ∧ (∀ p k, (p, k) ∈ result → p = prodOf factors k)
-- post-conditions-end

-- impl-start
def implementation_combineFactors (factors : List (Int × Nat)) : List (Int × Nat) :=
  Id.run do
    let mut result : List (Int × Nat) := []
    for k in (factors.map Prod.snd).dedup do
      let mut prod : Int := 1
      for fk in factors do
        if fk.2 = k then
          prod := prod * fk.1
      result := result ++ [(prod, k)]
    return result
-- impl-end

-- proof-start
/-- The inner loop folds the matching factors' products onto the accumulator;
generalised over the accumulator so it reduces to `List.foldl` over the filtered
list (matching `prodOf`). -/
theorem inner_combineFactors_helper
    (factors : List (Int × Nat)) (k : Nat) (init : Int) :
    (Id.run (forIn factors init (fun fk r =>
        (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
         else pure (ForInStep.yield r) : Id (ForInStep Int)))))
    = (factors.filter (fun fk => fk.2 = k)).foldl (fun acc fk => acc * fk.1) init := by
  induction factors generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : a.2 = k <;> simp [h, ih]

/-- The outer loop appends one `(prodOf factors k, k)` entry per multiplicity;
generalised over the accumulator so it reduces to a `List.map`. -/
theorem outer_combineFactors_helper
    (factors : List (Int × Nat)) (ks : List Nat) (init : List (Int × Nat)) :
    (Id.run (forIn ks init (fun k r =>
        (do
          let prod ← (forIn factors (1:Int) (fun fk r =>
              (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
               else pure (ForInStep.yield r) : Id (ForInStep Int))))
          pure (ForInStep.yield (r ++ [(prod, k)])) : Id (ForInStep (List (Int × Nat)))))))
    = init ++ ks.map (fun k => (prodOf factors k, k)) := by
  induction ks generalizing init with
  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [show (forIn factors (1:Int) (fun fk r =>
              (if fk.2 = a then pure (ForInStep.yield (r * fk.1))
               else pure (ForInStep.yield r) : Id (ForInStep Int))))
        = Id.run (forIn factors (1:Int) (fun fk r =>
              (if fk.2 = a then pure (ForInStep.yield (r * fk.1))
               else pure (ForInStep.yield r) : Id (ForInStep Int)))) from rfl]
    rw [inner_combineFactors_helper, ih]
    simp [prodOf, List.map_cons]

/-- Closed form of the imperative implementation. -/
theorem hbody_combineFactors (factors : List (Int × Nat)) :
    implementation_combineFactors factors
      = (factors.map Prod.snd).dedup.map (fun k => (prodOf factors k, k)) := by
  unfold implementation_combineFactors
  simp only [Id.run]
  -- bridge the desugared body (`do pure PUnit.unit; …`) to the clean helper body
  have h2 : (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>
        (do
          let r_1 ← (forIn factors (1:Int) fun fk r =>
              (if fk.2 = k then do pure PUnit.unit; pure (ForInStep.yield (r * fk.1))
               else do pure PUnit.unit; pure (ForInStep.yield r) : Id (ForInStep Int)))
          pure PUnit.unit
          pure (ForInStep.yield (r ++ [(r_1, k)])) : Id (ForInStep (List (Int × Nat)))))
      = (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>
        (do
          let prod ← (forIn factors (1:Int) fun fk r =>
              (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
               else pure (ForInStep.yield r) : Id (ForInStep Int)))
          pure (ForInStep.yield (r ++ [(prod, k)])) : Id (ForInStep (List (Int × Nat))))) := rfl
  rw [h2]
  simp only [bind_pure]
  show (Id.run _ : List (Int × Nat)) = _
  rw [outer_combineFactors_helper]
  simp

theorem correct_combineFactors :
    ∀ (factors : List (Int × Nat)),
      problem_spec_combineFactors factors (implementation_combineFactors factors) := by
  intro factors
  have key : (implementation_combineFactors factors).map Prod.snd
      = (factors.map Prod.snd).dedup := by
    rw [hbody_combineFactors, List.map_map]
    exact List.map_id _
  refine ⟨?_, ?_, ?_⟩
  · -- multiplicity column is `Nodup` (it is a `dedup`)
    rw [key]; exact (factors.map Prod.snd).nodup_dedup
  · -- the result's multiplicities are exactly the input's
    intro k; rw [key]; exact List.mem_dedup
  · -- each entry's factor is the product of the matching inputs
    intro p k hmem
    rw [hbody_combineFactors] at hmem
    simp only [List.mem_map] at hmem
    obtain ⟨k', _, hk'⟩ := hmem
    rw [Prod.ext_iff] at hk'
    obtain ⟨hp, hk⟩ := hk'
    simp only at hp hk
    rw [← hp, ← hk]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Protocol executed same_spec=True verified for all 7 attacks + positive_control against the frozen Solution.lean (only impl+proof regions vary; axioms/pure/pre/post byte-identical). Attack verifications run as background Bash jobs, 4 at a time.

Command for each: `bash scripts/lean_verify.sh <file>` from project root.

### Results
- positive_control.lean (gold impl): exit 0 (closes). `#print axioms correct_combineFactors` = [propext, Classical.choice, Quot.sound] — clean, NO sorryAx.
- atk_1.lean (identity `return factors` = the PREPATCH BUG): exit 1, genuine unsolved goal `(List.map Prod.snd factors).Nodup` (case refine_1). Prepatch bug reproduced: does NOT close. Fails conjunct (1) when two factors share a multiplicity, and (3) (factor != prodOf).
- atk_2.lean (empty `[]`): exit 1, genuine unsolved membership goal (case refine_2). Fails conjunct (2) — a witnessed multiplicity is missing.
- atk_3.lean (SUM not product; prod:=0, +): exit 3 (sorry). Fails (3): e.g. [(2,1),(3,1)] -> (5,1) but prodOf=6.
- atk_4.lean (first matching factor only, headD): exit 3 (sorry). Fails (3): [(2,1),(3,1)] -> (2,1) vs prodOf=6.
- atk_5.lean (control-flow-effect: accumulator `prod` NOT reset between multiplicities, carried across k): exit 3 (sorry). Fails (3): [(2,1),(3,2)] -> (2,1),(6,2) but prodOf for k=2 is 3.
- atk_6.lean (ungrounded/echo: return base ++ base, doubling every entry): exit 3 (sorry). Fails (1) Nodup: [(6,1),(6,1)].
- atk_7.lean (wrong filter `fk.2 != k`): exit 3 (sorry). Fails (3): [(2,1),(3,1)] -> (1,1) vs prodOf=6.

CONFIRMATION the proofs are genuinely unclosable (not lazy proofs): disprove.lean #evals each attack impl vs the spec-determined gold set on concrete inputs. Every attack diverges from gold, each violating a specific conjunct (outputs shown above). A false conjunct is unprovable, so no clean-axiom proof exists for any attack. Since NO wrong impl closes, there is nothing to materialize/resolve — no patch needed (patches={}).

refinement.md audit: all legs are R or I; there are NO A-consumed / A-reference legs (empty axioms block; consolidation modeled DEEPLY via prodOf=foldl(*)1 and dedup; axiom_check.py is a correct skip-stub). No kind-3 (changed-inexpressible) leg. The deep-model <-> patch correspondence (factor -> Int under *, set -> dedup, reduce(mul,gen) -> foldl(*)1) is mechanically driven by G-CONF against the REAL patched sqf_list (30002 checks, 0 disagreements per bundle record).

Conclusion: verify => correct holds for this spec — SOUND. >=5 distinct same-spec wrong impls (7 total, spanning partial-domain/boundary/control-flow-effect/ungrounded-oracle-echo) attempted and none breaks it.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong) audit of sympy__sympy-18698 lean bundle.

### MECHANICAL CHECKS (all pass):
- lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
- `#print axioms correct_combineFactors` -> [propext, Classical.choice, Quot.sound]; NO sorryAx (proof genuinely closes).
- swebench_unified.markers.same_spec(Solution, Solution_prepatch, lean tables) -> True (spec region byte-identical; prepatch impl `return factors` cannot close correct_ so spec discriminates pre/post).
- meta.json gates: G-CONF pass (checked=30002 disagreements=0), G-EQ pass, G-PANEL-1/2/3 pass, G-RESOLVE pass, patch_equals_gold=True, conf_skip=False.

MODELED FUNCTION = gold patch sqf tail of _symbolic_factor_list:
  factors = [(reduce(mul, (f for f,_ in factors if _==k)), k) for k in set(i for _,i in factors)]

SPEC-vs-REAL, clause by clause (does the REAL callee ever violate a spec clause? i.e. is the spec too strong?):
(1) Nodup mult column: real iterates `for k in set(...)` -> each mult exactly once. Real output ALWAYS satisfies.
(2) result mults == input mults: set(i for _,i in factors) is exactly the distinct input multiplicities -> none dropped, none invented. Real ALWAYS satisfies.
(3) p = prodOf factors k = foldl (*) 1 over factors filtered to mult k: real reduce(mul, gen) over same filtered factors. Every k comes from set(input mults) => generator non-empty => reduce (no initializer) equals foldl starting at identity 1. Multiplication commutative in both Int and the polynomial ring => iteration order irrelevant. Real ALWAYS satisfies.

Edge cases: empty input -> real [], spec vacuous, faithful; single-member group -> reduce([a])=a=1*a; factor->Int-under-* R-refinement preserves consolidation (block uses factors only under *, G-CONF drives the REAL polynomial product end-to-end); Nat permitting mult 0 is a harmless unreachable superset, not a real-callee violation.

G-CONF (seed 18698) drives the REAL patched sqf_list over 30000 randomized pairwise-coprime factor products + literal issue-8695 polynomial + OP second example, comparing order-independently via canonical Poly coeff tuples -> 0 disagreements.

CONCLUSION: no input found where the modeled function disagrees with the real callee, and the spec is a superset-free exact characterization of the consolidation (never stronger than the real behavior). Spec is not too strong / does not drift. VERDICT: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view integrity verified: markers.spec_view(Solution.lean, LeanBackend) sha256 = a85ee1a0417e31c85d05c1d06de712b67bc94aba286e2f555644cba87376df15, byte-identical to meta.json region_hashes.spec_view. same_spec(Solution, Solution_prepatch)=True — spec differs from prepatch ONLY in the elided impl/proof regions ('implementation elided — supplied by the consumer' / 'proof elided — supplied by the consumer').

What the spec view exposes: (1) docstring describing consolidation of (factor, multiplicity) pairs so each multiplicity appears exactly once paired with the product of matching factors; (2) pure helper prodOf = filter-by-multiplicity then foldl product; (3) postcondition problem_spec_combineFactors = Nodup on multiplicity column + (result mults ↔ input mults) + each entry factor = prodOf. This is the CORRECTNESS CONTRACT (what), not the implementation (how).

Comparison to PUBLIC problem_statement only (hints_text excluded): the problem_statement already states the fix explicitly — sqf_list 'should have (x**2 - 5*x + 6, 3) and not 2 factors of multiplicity 3', i.e. combine factors of the same multiplicity into one product factor, with the worked example (x-2)(x-3)=x**2-5x+6 being the product of the two multiplicity-3 factors. The desired postcondition (one factor per multiplicity = product of same-multiplicity inputs) is literally the demanded behavior in the public problem statement.

No gold-patch implementation detail leaks in the spec view: reduce(mul,...), the operator.mul/reduce import, the set(...) comprehension, method=='sqf' gating, and the _symbolic_factor_list location all live only in the fully-elided impl/proof regions. The one comment referencing 'the inner accumulating loop of the implementation' describes the spec↔impl relation abstractly and discloses none of the gold specifics. prodOf/postcondition restate the public required outcome.

Conclusion: spec view is a legitimate restatement of the public problem's postcondition; no gold-reconstruction leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
