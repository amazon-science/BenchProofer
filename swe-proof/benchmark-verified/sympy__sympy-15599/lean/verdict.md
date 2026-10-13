# P2 adversarial audit — sympy__sympy-15599

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,50 +68,11 @@
 
 -- impl-start
 def implementation_modFactors (q : Int) (factors : List Factor) : List Factor := Id.run do
-  if q = 1 then
-    return factors
-  let mut acc : List Factor := []
-  for f in factors do
-    match f with
-    | Factor.coeff n =>
-        if intMod n q ≠ 0 then
-          acc := acc ++ [Factor.coeff (intMod n q)]
-        else
-          acc := acc ++ [Factor.coeff n]
-    | Factor.sym s =>
-        acc := acc ++ [Factor.sym s]
-  return acc
+  -- PRE-PATCH bug: return factors unchanged (no per-factor reduction).
+  return factors
 -- impl-end
 
 -- proof-start
-/-- The `forIn` loop, generalized over the accumulator, appends the
-front-recursive `reduceFactors` of the remaining list to the running prefix. -/
-theorem modFactors_forIn (q : Int) (xs : List Factor) : ∀ (init : List Factor),
-    Id.run (forIn xs init (fun f r =>
-      match f with
-      | Factor.coeff n =>
-        if intMod n q ≠ 0 then
-          pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
-        else
-          pure (ForInStep.yield (r ++ [Factor.coeff n]))
-      | Factor.sym s => pure (ForInStep.yield (r ++ [Factor.sym s])))) = init ++ reduceFactors q xs := by
-  induction xs with
-  | nil => intro init; simp [reduceFactors]
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    cases a with
-    | coeff n =>
-      by_cases h : intMod n q ≠ 0
-      · simp only [if_pos h, ih, reduceFactors, reduceFactor, List.append_assoc,
-          List.cons_append, List.nil_append]
-      · simp only [if_neg h, ih, reduceFactors, reduceFactor, List.append_assoc,
-          List.cons_append, List.nil_append]
-    | sym s =>
-      simp only [ih, reduceFactors, reduceFactor, List.append_assoc,
-        List.cons_append, List.nil_append]
-
 theorem correct_modFactors :
     ∀ (q : Int) (factors : List Factor),
       problem_spec_modFactors q factors (implementation_modFactors q factors) := by
@@ -119,31 +80,8 @@
   unfold problem_spec_modFactors implementation_modFactors
   simp only [Id.run]
   by_cases hq1 : q = 1
-  · simp only [hq1, if_pos]; rfl
+  · simp only [hq1, if_pos]
   · simp only [hq1, if_false]
-    have h2 : (do
-      pure PUnit.unit
-      let r ← forIn factors [] fun f r =>
-            match f with
-            | Factor.coeff n =>
-              if intMod n q ≠ 0 then do
-                pure PUnit.unit
-                pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
-              else do
-                pure PUnit.unit
-                pure (ForInStep.yield (r ++ [Factor.coeff n]))
-            | Factor.sym s => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [Factor.sym s]))
-      pure r : Id (List Factor)) =
-      Id.run (forIn factors [] (fun f r =>
-        match f with
-        | Factor.coeff n =>
-          if intMod n q ≠ 0 then
-            pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
-          else
-            pure (ForInStep.yield (r ++ [Factor.coeff n]))
-        | Factor.sym s => pure (ForInStep.yield (r ++ [Factor.sym s])))) := rfl
-    rw [h2, modFactors_forIn]
-    simp
+    -- factors ≠ reduceFactors q factors in general; this should NOT close.
+    rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,6 +70,9 @@
 def implementation_modFactors (q : Int) (factors : List Factor) : List Factor := Id.run do
   if q = 1 then
     return factors
+  if q ≤ 0 then
+    -- partial-domain: skip reduction for non-positive divisors
+    return factors
   let mut acc : List Factor := []
   for f in factors do
     match f with
@@ -84,34 +87,6 @@
 -- impl-end
 
 -- proof-start
-/-- The `forIn` loop, generalized over the accumulator, appends the
-front-recursive `reduceFactors` of the remaining list to the running prefix. -/
-theorem modFactors_forIn (q : Int) (xs : List Factor) : ∀ (init : List Factor),
-    Id.run (forIn xs init (fun f r =>
-      match f with
-      | Factor.coeff n =>
-        if intMod n q ≠ 0 then
-          pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
-        else
-          pure (ForInStep.yield (r ++ [Factor.coeff n]))
-      | Factor.sym s => pure (ForInStep.yield (r ++ [Factor.sym s])))) = init ++ reduceFactors q xs := by
-  induction xs with
-  | nil => intro init; simp [reduceFactors]
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    cases a with
-    | coeff n =>
-      by_cases h : intMod n q ≠ 0
-      · simp only [if_pos h, ih, reduceFactors, reduceFactor, List.append_assoc,
-          List.cons_append, List.nil_append]
-      · simp only [if_neg h, ih, reduceFactors, reduceFactor, List.append_assoc,
-          List.cons_append, List.nil_append]
-    | sym s =>
-      simp only [ih, reduceFactors, reduceFactor, List.append_assoc,
-        List.cons_append, List.nil_append]
-
 theorem correct_modFactors :
     ∀ (q : Int) (factors : List Factor),
       problem_spec_modFactors q factors (implementation_modFactors q factors) := by
@@ -120,30 +95,5 @@
   simp only [Id.run]
   by_cases hq1 : q = 1
   · simp only [hq1, if_pos]; rfl
-  · simp only [hq1, if_false]
-    have h2 : (do
-      pure PUnit.unit
-      let r ← forIn factors [] fun f r =>
-            match f with
-            | Factor.coeff n =>
-              if intMod n q ≠ 0 then do
-                pure PUnit.unit
-                pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
-              else do
-                pure PUnit.unit
-                pure (ForInStep.yield (r ++ [Factor.coeff n]))
-            | Factor.sym s => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [Factor.sym s]))
-      pure r : Id (List Factor)) =
-      Id.run (forIn factors [] (fun f r =>
-        match f with
-        | Factor.coeff n =>
-          if intMod n q ≠ 0 then
-            pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
-          else
-            pure (ForInStep.yield (r ++ [Factor.coeff n]))
-        | Factor.sym s => pure (ForInStep.yield (r ++ [Factor.sym s])))) := rfl
-    rw [h2, modFactors_forIn]
-    simp
+  · sorry
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,44 +74,14 @@
   for f in factors do
     match f with
     | Factor.coeff n =>
-        if intMod n q ≠ 0 then
-          acc := acc ++ [Factor.coeff (intMod n q)]
-        else
-          acc := acc ++ [Factor.coeff n]
+        -- boundary bug: always take the residue, even when it is zero
+        acc := acc ++ [Factor.coeff (intMod n q)]
     | Factor.sym s =>
         acc := acc ++ [Factor.sym s]
   return acc
 -- impl-end
 
 -- proof-start
-/-- The `forIn` loop, generalized over the accumulator, appends the
-front-recursive `reduceFactors` of the remaining list to the running prefix. -/
-theorem modFactors_forIn (q : Int) (xs : List Factor) : ∀ (init : List Factor),
-    Id.run (forIn xs init (fun f r =>
-      match f with
-      | Factor.coeff n =>
-        if intMod n q ≠ 0 then
-          pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
-        else
-          pure (ForInStep.yield (r ++ [Factor.coeff n]))
-      | Factor.sym s => pure (ForInStep.yield (r ++ [Factor.sym s])))) = init ++ reduceFactors q xs := by
-  induction xs with
-  | nil => intro init; simp [reduceFactors]
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    cases a with
-    | coeff n =>
-      by_cases h : intMod n q ≠ 0
-      · simp only [if_pos h, ih, reduceFactors, reduceFactor, List.append_assoc,
-          List.cons_append, List.nil_append]
-      · simp only [if_neg h, ih, reduceFactors, reduceFactor, List.append_assoc,
-          List.cons_append, List.nil_append]
-    | sym s =>
-      simp only [ih, reduceFactors, reduceFactor, List.append_assoc,
-        List.cons_append, List.nil_append]
-
 theorem correct_modFactors :
     ∀ (q : Int) (factors : List Factor),
       problem_spec_modFactors q factors (implementation_modFactors q factors) := by
@@ -120,30 +90,5 @@
   simp only [Id.run]
   by_cases hq1 : q = 1
   · simp only [hq1, if_pos]; rfl
-  · simp only [hq1, if_false]
-    have h2 : (do
-      pure PUnit.unit
-      let r ← forIn factors [] fun f r =>
-            match f with
-            | Factor.coeff n =>
-              if intMod n q ≠ 0 then do
-                pure PUnit.unit
-                pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
-              else do
-                pure PUnit.unit
-                pure (ForInStep.yield (r ++ [Factor.coeff n]))
-            | Factor.sym s => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [Factor.sym s]))
-      pure r : Id (List Factor)) =
-      Id.run (forIn factors [] (fun f r =>
-        match f with
-        | Factor.coeff n =>
-          if intMod n q ≠ 0 then
-            pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
-          else
-            pure (ForInStep.yield (r ++ [Factor.coeff n]))
-        | Factor.sym s => pure (ForInStep.yield (r ++ [Factor.sym s])))) := rfl
-    rw [h2, modFactors_forIn]
-    simp
+  · sorry
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,43 +75,16 @@
     match f with
     | Factor.coeff n =>
         if intMod n q ≠ 0 then
-          acc := acc ++ [Factor.coeff (intMod n q)]
+          -- control-flow-effect bug: prepend, reversing factor order
+          acc := [Factor.coeff (intMod n q)] ++ acc
         else
-          acc := acc ++ [Factor.coeff n]
+          acc := [Factor.coeff n] ++ acc
     | Factor.sym s =>
-        acc := acc ++ [Factor.sym s]
+        acc := [Factor.sym s] ++ acc
   return acc
 -- impl-end
 
 -- proof-start
-/-- The `forIn` loop, generalized over the accumulator, appends the
-front-recursive `reduceFactors` of the remaining list to the running prefix. -/
-theorem modFactors_forIn (q : Int) (xs : List Factor) : ∀ (init : List Factor),
-    Id.run (forIn xs init (fun f r =>
-      match f with
-      | Factor.coeff n =>
-        if intMod n q ≠ 0 then
-          pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
-        else
-          pure (ForInStep.yield (r ++ [Factor.coeff n]))
-      | Factor.sym s => pure (ForInStep.yield (r ++ [Factor.sym s])))) = init ++ reduceFactors q xs := by
-  induction xs with
-  | nil => intro init; simp [reduceFactors]
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    cases a with
-    | coeff n =>
-      by_cases h : intMod n q ≠ 0
-      · simp only [if_pos h, ih, reduceFactors, reduceFactor, List.append_assoc,
-          List.cons_append, List.nil_append]
-      · simp only [if_neg h, ih, reduceFactors, reduceFactor, List.append_assoc,
-          List.cons_append, List.nil_append]
-    | sym s =>
-      simp only [ih, reduceFactors, reduceFactor, List.append_assoc,
-        List.cons_append, List.nil_append]
-
 theorem correct_modFactors :
     ∀ (q : Int) (factors : List Factor),
       problem_spec_modFactors q factors (implementation_modFactors q factors) := by
@@ -120,30 +93,5 @@
   simp only [Id.run]
   by_cases hq1 : q = 1
   · simp only [hq1, if_pos]; rfl
-  · simp only [hq1, if_false]
-    have h2 : (do
-      pure PUnit.unit
-      let r ← forIn factors [] fun f r =>
-            match f with
-            | Factor.coeff n =>
-              if intMod n q ≠ 0 then do
-                pure PUnit.unit
-                pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
-              else do
-                pure PUnit.unit
-                pure (ForInStep.yield (r ++ [Factor.coeff n]))
-            | Factor.sym s => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [Factor.sym s]))
-      pure r : Id (List Factor)) =
-      Id.run (forIn factors [] (fun f r =>
-        match f with
-        | Factor.coeff n =>
-          if intMod n q ≠ 0 then
-            pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
-          else
-            pure (ForInStep.yield (r ++ [Factor.coeff n]))
-        | Factor.sym s => pure (ForInStep.yield (r ++ [Factor.sym s])))) := rfl
-    rw [h2, modFactors_forIn]
-    simp
+  · sorry
 -- proof-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -67,83 +67,14 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_modFactors (q : Int) (factors : List Factor) : List Factor := Id.run do
-  if q = 1 then
-    return factors
-  let mut acc : List Factor := []
-  for f in factors do
-    match f with
-    | Factor.coeff n =>
-        if intMod n q ≠ 0 then
-          acc := acc ++ [Factor.coeff (intMod n q)]
-        else
-          acc := acc ++ [Factor.coeff n]
-    | Factor.sym s =>
-        acc := acc ++ [Factor.sym s]
-  return acc
+def implementation_modFactors (q : Int) (factors : List Factor) : List Factor :=
+  if q = 1 then factors else reduceFactors q factors
 -- impl-end
 
 -- proof-start
-/-- The `forIn` loop, generalized over the accumulator, appends the
-front-recursive `reduceFactors` of the remaining list to the running prefix. -/
-theorem modFactors_forIn (q : Int) (xs : List Factor) : ∀ (init : List Factor),
-    Id.run (forIn xs init (fun f r =>
-      match f with
-      | Factor.coeff n =>
-        if intMod n q ≠ 0 then
-          pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
-        else
-          pure (ForInStep.yield (r ++ [Factor.coeff n]))
-      | Factor.sym s => pure (ForInStep.yield (r ++ [Factor.sym s])))) = init ++ reduceFactors q xs := by
-  induction xs with
-  | nil => intro init; simp [reduceFactors]
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    cases a with
-    | coeff n =>
-      by_cases h : intMod n q ≠ 0
-      · simp only [if_pos h, ih, reduceFactors, reduceFactor, List.append_assoc,
-          List.cons_append, List.nil_append]
-      · simp only [if_neg h, ih, reduceFactors, reduceFactor, List.append_assoc,
-          List.cons_append, List.nil_append]
-    | sym s =>
-      simp only [ih, reduceFactors, reduceFactor, List.append_assoc,
-        List.cons_append, List.nil_append]
-
 theorem correct_modFactors :
     ∀ (q : Int) (factors : List Factor),
       problem_spec_modFactors q factors (implementation_modFactors q factors) := by
   intro q factors
-  unfold problem_spec_modFactors implementation_modFactors
-  simp only [Id.run]
-  by_cases hq1 : q = 1
-  · simp only [hq1, if_pos]; rfl
-  · simp only [hq1, if_false]
-    have h2 : (do
-      pure PUnit.unit
-      let r ← forIn factors [] fun f r =>
-            match f with
-            | Factor.coeff n =>
-              if intMod n q ≠ 0 then do
-                pure PUnit.unit
-                pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
-              else do
-                pure PUnit.unit
-                pure (ForInStep.yield (r ++ [Factor.coeff n]))
-            | Factor.sym s => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [Factor.sym s]))
-      pure r : Id (List Factor)) =
-      Id.run (forIn factors [] (fun f r =>
-        match f with
-        | Factor.coeff n =>
-          if intMod n q ≠ 0 then
-            pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
-          else
-            pure (ForInStep.yield (r ++ [Factor.coeff n]))
-        | Factor.sym s => pure (ForInStep.yield (r ++ [Factor.sym s])))) := rfl
-    rw [h2, modFactors_forIn]
-    simp
+  rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,39 +79,12 @@
         else
           acc := acc ++ [Factor.coeff n]
     | Factor.sym s =>
-        acc := acc ++ [Factor.sym s]
+        -- bug: symbolic factor id reduced (should be preserved exactly)
+        acc := acc ++ [Factor.sym (s + 1)]
   return acc
 -- impl-end
 
 -- proof-start
-/-- The `forIn` loop, generalized over the accumulator, appends the
-front-recursive `reduceFactors` of the remaining list to the running prefix. -/
-theorem modFactors_forIn (q : Int) (xs : List Factor) : ∀ (init : List Factor),
-    Id.run (forIn xs init (fun f r =>
-      match f with
-      | Factor.coeff n =>
-        if intMod n q ≠ 0 then
-          pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
-        else
-          pure (ForInStep.yield (r ++ [Factor.coeff n]))
-      | Factor.sym s => pure (ForInStep.yield (r ++ [Factor.sym s])))) = init ++ reduceFactors q xs := by
-  induction xs with
-  | nil => intro init; simp [reduceFactors]
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    cases a with
-    | coeff n =>
-      by_cases h : intMod n q ≠ 0
-      · simp only [if_pos h, ih, reduceFactors, reduceFactor, List.append_assoc,
-          List.cons_append, List.nil_append]
-      · simp only [if_neg h, ih, reduceFactors, reduceFactor, List.append_assoc,
-          List.cons_append, List.nil_append]
-    | sym s =>
-      simp only [ih, reduceFactors, reduceFactor, List.append_assoc,
-        List.cons_append, List.nil_append]
-
 theorem correct_modFactors :
     ∀ (q : Int) (factors : List Factor),
       problem_spec_modFactors q factors (implementation_modFactors q factors) := by
@@ -120,30 +93,5 @@
   simp only [Id.run]
   by_cases hq1 : q = 1
   · simp only [hq1, if_pos]; rfl
-  · simp only [hq1, if_false]
-    have h2 : (do
-      pure PUnit.unit
-      let r ← forIn factors [] fun f r =>
-            match f with
-            | Factor.coeff n =>
-              if intMod n q ≠ 0 then do
-                pure PUnit.unit
-                pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
-              else do
-                pure PUnit.unit
-                pure (ForInStep.yield (r ++ [Factor.coeff n]))
-            | Factor.sym s => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [Factor.sym s]))
-      pure r : Id (List Factor)) =
-      Id.run (forIn factors [] (fun f r =>
-        match f with
-        | Factor.coeff n =>
-          if intMod n q ≠ 0 then
-            pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
-          else
-            pure (ForInStep.yield (r ++ [Factor.coeff n]))
-        | Factor.sym s => pure (ForInStep.yield (r ++ [Factor.sym s])))) := rfl
-    rw [h2, modFactors_forIn]
-    simp
+  · sorry
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,8 +74,9 @@
   for f in factors do
     match f with
     | Factor.coeff n =>
-        if intMod n q ≠ 0 then
-          acc := acc ++ [Factor.coeff (intMod n q)]
+        -- bug: truncating remainder (n % q), wrong sign convention for negatives
+        if n % q ≠ 0 then
+          acc := acc ++ [Factor.coeff (n % q)]
         else
           acc := acc ++ [Factor.coeff n]
     | Factor.sym s =>
@@ -84,34 +85,6 @@
 -- impl-end
 
 -- proof-start
-/-- The `forIn` loop, generalized over the accumulator, appends the
-front-recursive `reduceFactors` of the remaining list to the running prefix. -/
-theorem modFactors_forIn (q : Int) (xs : List Factor) : ∀ (init : List Factor),
-    Id.run (forIn xs init (fun f r =>
-      match f with
-      | Factor.coeff n =>
-        if intMod n q ≠ 0 then
-          pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
-        else
-          pure (ForInStep.yield (r ++ [Factor.coeff n]))
-      | Factor.sym s => pure (ForInStep.yield (r ++ [Factor.sym s])))) = init ++ reduceFactors q xs := by
-  induction xs with
-  | nil => intro init; simp [reduceFactors]
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    cases a with
-    | coeff n =>
-      by_cases h : intMod n q ≠ 0
-      · simp only [if_pos h, ih, reduceFactors, reduceFactor, List.append_assoc,
-          List.cons_append, List.nil_append]
-      · simp only [if_neg h, ih, reduceFactors, reduceFactor, List.append_assoc,
-          List.cons_append, List.nil_append]
-    | sym s =>
-      simp only [ih, reduceFactors, reduceFactor, List.append_assoc,
-        List.cons_append, List.nil_append]
-
 theorem correct_modFactors :
     ∀ (q : Int) (factors : List Factor),
       problem_spec_modFactors q factors (implementation_modFactors q factors) := by
@@ -120,30 +93,5 @@
   simp only [Id.run]
   by_cases hq1 : q = 1
   · simp only [hq1, if_pos]; rfl
-  · simp only [hq1, if_false]
-    have h2 : (do
-      pure PUnit.unit
-      let r ← forIn factors [] fun f r =>
-            match f with
-            | Factor.coeff n =>
-              if intMod n q ≠ 0 then do
-                pure PUnit.unit
-                pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
-              else do
-                pure PUnit.unit
-                pure (ForInStep.yield (r ++ [Factor.coeff n]))
-            | Factor.sym s => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [Factor.sym s]))
-      pure r : Id (List Factor)) =
-      Id.run (forIn factors [] (fun f r =>
-        match f with
-        | Factor.coeff n =>
-          if intMod n q ≠ 0 then
-            pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
-          else
-            pure (ForInStep.yield (r ++ [Factor.coeff n]))
-        | Factor.sym s => pure (ForInStep.yield (r ++ [Factor.sym s])))) := rfl
-    rw [h2, modFactors_forIn]
-    simp
+  · sorry
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Reducing the concrete-integer factors of a product against a divisor.

A product is modelled as a list of factors, each of which is either a concrete
integer coefficient or a symbolic atom (a non-numeric factor, identified
opaquely). Given an integer divisor `q`, the desired normalisation rewrites the
product so that every concrete-integer factor is taken modulo `q`, EXCEPT when
that residue is zero, in which case the factor is left untouched; symbolic
factors are always preserved exactly.

The remainder convention is Python's: the residue carries the sign of the
divisor (floored division). When the divisor equals one the product is returned
unchanged (every integer is congruent to zero modulo one, so reducing would
erase information rather than simplify). The normalisation is total: for a
zero divisor the floored remainder of `n` is `n` itself, so every factor is
kept unchanged (a zero divisor never reaches this normalisation in practice —
it is rejected upstream — and the total extension is the identity).

Every factor of the result is pinned to its input factor, so no part of the
output is left free.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The per-factor
-- residue is modeled DEEPLY via exact integer arithmetic (floored remainder),
-- and the symbolic factors are carried through structurally, so no
-- `opaque`/`axiom` callee contract is needed. The R/I refinement of the residue
-- arithmetic is differential-tested by G-CONF.
-- axioms-end

-- pure-start
/-- A single factor of a product: either a concrete integer coefficient, or a
symbolic atom identified by an opaque tag. -/
inductive Factor where
  | coeff (n : Int)
  | sym (id : Nat)
deriving DecidableEq, Repr

/-- The Python-convention (floored) remainder `a mod b`: the residue carries the
sign of `b`. Defined via `Int.fdiv` so `intMod (-7) 2 = 1` and `intMod 7 (-2) = -1`. -/
def intMod (a b : Int) : Int := a - b * (Int.fdiv a b)

/-- Reduce one factor against the divisor `q`: a concrete coefficient `n` becomes
its residue `intMod n q` unless that residue is zero (then `n` is kept); a
symbolic factor is preserved. -/
def reduceFactor (q : Int) (f : Factor) : Factor :=
  match f with
  | Factor.coeff n => if intMod n q ≠ 0 then Factor.coeff (intMod n q) else Factor.coeff n
  | Factor.sym s => Factor.sym s

/-- Front-recursive fold applying `reduceFactor q` to every factor of a product. -/
def reduceFactors (q : Int) : List Factor → List Factor
  | [] => []
  | f :: fs => reduceFactor q f :: reduceFactors q fs
-- pure-end

-- post-conditions-start
/-- The normalised product: when the divisor is one the factor list is returned
unchanged; otherwise every concrete-integer factor is reduced against `q`
(non-zero residues only) while symbolic factors are preserved. The result is
pinned factor-for-factor to the input. -/
def problem_spec_modFactors (q : Int) (factors result : List Factor) : Prop :=
  result = (if q = 1 then factors else reduceFactors q factors)
-- post-conditions-end

-- impl-start
def implementation_modFactors (q : Int) (factors : List Factor) : List Factor := Id.run do
  if q = 1 then
    return factors
  let mut acc : List Factor := []
  for f in factors do
    match f with
    | Factor.coeff n =>
        if intMod n q ≠ 0 then
          acc := acc ++ [Factor.coeff (intMod n q)]
        else
          acc := acc ++ [Factor.coeff n]
    | Factor.sym s =>
        acc := acc ++ [Factor.sym s]
  return acc
-- impl-end

-- proof-start
/-- The `forIn` loop, generalized over the accumulator, appends the
front-recursive `reduceFactors` of the remaining list to the running prefix. -/
theorem modFactors_forIn (q : Int) (xs : List Factor) : ∀ (init : List Factor),
    Id.run (forIn xs init (fun f r =>
      match f with
      | Factor.coeff n =>
        if intMod n q ≠ 0 then
          pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
        else
          pure (ForInStep.yield (r ++ [Factor.coeff n]))
      | Factor.sym s => pure (ForInStep.yield (r ++ [Factor.sym s])))) = init ++ reduceFactors q xs := by
  induction xs with
  | nil => intro init; simp [reduceFactors]
  | cons a as ih =>
    intro init
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    cases a with
    | coeff n =>
      by_cases h : intMod n q ≠ 0
      · simp only [if_pos h, ih, reduceFactors, reduceFactor, List.append_assoc,
          List.cons_append, List.nil_append]
      · simp only [if_neg h, ih, reduceFactors, reduceFactor, List.append_assoc,
          List.cons_append, List.nil_append]
    | sym s =>
      simp only [ih, reduceFactors, reduceFactor, List.append_assoc,
        List.cons_append, List.nil_append]

theorem correct_modFactors :
    ∀ (q : Int) (factors : List Factor),
      problem_spec_modFactors q factors (implementation_modFactors q factors) := by
  intro q factors
  unfold problem_spec_modFactors implementation_modFactors
  simp only [Id.run]
  by_cases hq1 : q = 1
  · simp only [hq1, if_pos]; rfl
  · simp only [hq1, if_false]
    have h2 : (do
      pure PUnit.unit
      let r ← forIn factors [] fun f r =>
            match f with
            | Factor.coeff n =>
              if intMod n q ≠ 0 then do
                pure PUnit.unit
                pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
              else do
                pure PUnit.unit
                pure (ForInStep.yield (r ++ [Factor.coeff n]))
            | Factor.sym s => do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [Factor.sym s]))
      pure r : Id (List Factor)) =
      Id.run (forIn factors [] (fun f r =>
        match f with
        | Factor.coeff n =>
          if intMod n q ≠ 0 then
            pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
          else
            pure (ForInStep.yield (r ++ [Factor.coeff n]))
        | Factor.sym s => pure (ForInStep.yield (r ++ [Factor.sym s])))) := rfl
    rw [h2, modFactors_forIn]
    simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_modFactors q factors result := result = (if q = 1 then factors else reduceFactors q factors). This is a FULLY-PINNED TOTAL FUNCTIONAL spec: it pins the exact output for every (q, factors) with NO precondition freedom, and the axioms region is EMPTY (comment-only, no opaque/axiom callee contracts). There are therefore NO A-legs (axioms/deep-model refs) to abuse — the entire behavior is modeled deeply via exact Int arithmetic (intMod = a - b*Int.fdiv a b, floored) and structural carry-through of symbolic factors. refinement.md audit: every leg is R (residue arithmetic Python floored % <-> intMod, G-CONF-tested) or I (iteration, zero-residue keep, sym preserve, list rebuild); no kind-3; G-AX is a legitimate skip stub since no callee axiom is consumed. mapping.md's q=0 totalization (intMod n 0 = n => reduceFactors 0 = id) removes the precondition-shadowed freedom a prior spec-too-weak audit exploited.

SAME_SPEC: all 7 attacks confirmed True via swebench_unified.markers.same_spec (impl-region-only edits; axioms/pure/pre/post byte-identical).

### VERIFICATIONS (scripts/lean_verify.sh, cap 300s, run concurrently <=4/batch):
- pos_control.lean (exact gold): EXIT=0. #print axioms correct_modFactors -> [propext, Quot.sound] (clean/standard).
- atk_1 prepatch bug (return factors unchanged): EXIT=1, honest rfl fails on 'pure factors = reduceFactors q factors'.
- atk_2 partial-domain (skip reduction when q<=0): EXIT=3 (sorry only).
- atk_3 boundary (always take residue, drops zero-residue-keep): EXIT=3 (sorry only).
- atk_4 control-flow-effect (prepend => reversed factor order): EXIT=3 (sorry only).
- atk_6 ungrounded-oracle echo (symbolic factor id +1, should be preserved): EXIT=3 (sorry only).
- atk_7 truncating emod n%q instead of floored intMod (wrong sign at negative divisor): EXIT=3 (sorry only).
- atk_5 VERIFYING ECHO (impl = if q=1 then factors else reduceFactors q factors; textually distinct from gold's Id.run/forIn loop but extensionally equal): EXIT=0. #print axioms -> 'does not depend on any axioms' (fully clean).

Each wrong impl's divergence from the spec is PROVED by a concrete decide witness (refute.lean + refute7.lean, both EXIT=0):
  atk_1: [coeff 3] != spec 2 [coeff 3]  (spec=[coeff 1])
  atk_2: [coeff 3] != spec (-2) [coeff 3]
  atk_3: [coeff (intMod 8 4)]=[coeff 0] != spec 4 [coeff 8]=[coeff 8]
  atk_4: [coeff(intMod 8 5),coeff(intMod 2 5)] != spec 5 [coeff 2,coeff 8] (order reversed)
  atk_6: [sym 1] != spec 2 [sym 0]
  atk_7: [coeff (3 % -2)]=[coeff 1] != spec (-2) [coeff 3]=[coeff -1] (floored vs truncating; probe.lean confirms 3 % -2 = 1 vs intMod 3 -2 = -1)
So each wrong impl's correct_modFactors is GENUINELY unprovable (unsound), not merely unfinished; only sorry closes them.

RESOLVE STEP (protocol step 2 — mandatory for every verifying clean-axiom impl): the only impl with a closing clean-axiom proof is atk_5, which is extensionally EQUAL to the gold function, so its faithful refined patch IS the gold patch. Materialized to atk_5.patch and executed run_resolve('sympy__sympy-15599', ..., retries=0): RESOLVED=True COMPLETED=True NOTE='resolved'. Bench: swe_bench_verified, docker oracle live, style=swebench. So the verifying candidate's faithful patch DOES resolve — no verify-but-not-resolve counterexample exists.

CONCLUSION: >=6 distinct genuinely-wrong same-spec impls (prepatch, partial-domain, boundary, control-flow-effect, ungrounded-oracle, wrong-residue-convention) all FAIL to verify (proved divergent by decide witnesses); the sole verifying same-spec impl is a gold-equivalent echo whose faithful patch RESOLVES. The spec has no axiom/deep-model leg to exploit and admits no verifying-but-incorrect implementation. verify => correct holds. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Reducing the concrete-integer factors of a product against a divisor.

A product is modelled as a list of factors, each of which is either a concrete
integer coefficient or a symbolic atom (a non-numeric factor, identified
opaquely). Given an integer divisor `q`, the desired normalisation rewrites the
product so that every concrete-integer factor is taken modulo `q`, EXCEPT when
that residue is zero, in which case the factor is left untouched; symbolic
factors are always preserved exactly.

The remainder convention is Python's: the residue carries the sign of the
divisor (floored division). When the divisor equals one the product is returned
unchanged (every integer is congruent to zero modulo one, so reducing would
erase information rather than simplify). The normalisation is total: for a
zero divisor the floored remainder of `n` is `n` itself, so every factor is
kept unchanged (a zero divisor never reaches this normalisation in practice —
it is rejected upstream — and the total extension is the identity).

Every factor of the result is pinned to its input factor, so no part of the
output is left free.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The per-factor
-- residue is modeled DEEPLY via exact integer arithmetic (floored remainder),
-- and the symbolic factors are carried through structurally, so no
-- `opaque`/`axiom` callee contract is needed. The R/I refinement of the residue
-- arithmetic is differential-tested by G-CONF.
-- axioms-end

-- pure-start
/-- A single factor of a product: either a concrete integer coefficient, or a
symbolic atom identified by an opaque tag. -/
inductive Factor where
  | coeff (n : Int)
  | sym (id : Nat)
deriving DecidableEq, Repr

/-- The Python-convention (floored) remainder `a mod b`: the residue carries the
sign of `b`. Defined via `Int.fdiv` so `intMod (-7) 2 = 1` and `intMod 7 (-2) = -1`. -/
def intMod (a b : Int) : Int := a - b * (Int.fdiv a b)

/-- Reduce one factor against the divisor `q`: a concrete coefficient `n` becomes
its residue `intMod n q` unless that residue is zero (then `n` is kept); a
symbolic factor is preserved. -/
def reduceFactor (q : Int) (f : Factor) : Factor :=
  match f with
  | Factor.coeff n => if intMod n q ≠ 0 then Factor.coeff (intMod n q) else Factor.coeff n
  | Factor.sym s => Factor.sym s

/-- Front-recursive fold applying `reduceFactor q` to every factor of a product. -/
def reduceFactors (q : Int) : List Factor → List Factor
  | [] => []
  | f :: fs => reduceFactor q f :: reduceFactors q fs
-- pure-end

-- post-conditions-start
/-- The normalised product: when the divisor is one the factor list is returned
unchanged; otherwise every concrete-integer factor is reduced against `q`
(non-zero residues only) while symbolic factors are preserved. The result is
pinned factor-for-factor to the input. -/
def problem_spec_modFactors (q : Int) (factors result : List Factor) : Prop :=
  result = (if q = 1 then factors else reduceFactors q factors)
-- post-conditions-end

-- impl-start
def implementation_modFactors (q : Int) (factors : List Factor) : List Factor := Id.run do
  if q = 1 then
    return factors
  let mut acc : List Factor := []
  for f in factors do
    match f with
    | Factor.coeff n =>
        if intMod n q ≠ 0 then
          acc := acc ++ [Factor.coeff (intMod n q)]
        else
          acc := acc ++ [Factor.coeff n]
    | Factor.sym s =>
        acc := acc ++ [Factor.sym s]
  return acc
-- impl-end

-- proof-start
/-- The `forIn` loop, generalized over the accumulator, appends the
front-recursive `reduceFactors` of the remaining list to the running prefix. -/
theorem modFactors_forIn (q : Int) (xs : List Factor) : ∀ (init : List Factor),
    Id.run (forIn xs init (fun f r =>
      match f with
      | Factor.coeff n =>
        if intMod n q ≠ 0 then
          pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
        else
          pure (ForInStep.yield (r ++ [Factor.coeff n]))
      | Factor.sym s => pure (ForInStep.yield (r ++ [Factor.sym s])))) = init ++ reduceFactors q xs := by
  induction xs with
  | nil => intro init; simp [reduceFactors]
  | cons a as ih =>
    intro init
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    cases a with
    | coeff n =>
      by_cases h : intMod n q ≠ 0
      · simp only [if_pos h, ih, reduceFactors, reduceFactor, List.append_assoc,
          List.cons_append, List.nil_append]
      · simp only [if_neg h, ih, reduceFactors, reduceFactor, List.append_assoc,
          List.cons_append, List.nil_append]
    | sym s =>
      simp only [ih, reduceFactors, reduceFactor, List.append_assoc,
        List.cons_append, List.nil_append]

theorem correct_modFactors :
    ∀ (q : Int) (factors : List Factor),
      problem_spec_modFactors q factors (implementation_modFactors q factors) := by
  intro q factors
  unfold problem_spec_modFactors implementation_modFactors
  simp only [Id.run]
  by_cases hq1 : q = 1
  · simp only [hq1, if_pos]; rfl
  · simp only [hq1, if_false]
    have h2 : (do
      pure PUnit.unit
      let r ← forIn factors [] fun f r =>
            match f with
            | Factor.coeff n =>
              if intMod n q ≠ 0 then do
                pure PUnit.unit
                pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
              else do
                pure PUnit.unit
                pure (ForInStep.yield (r ++ [Factor.coeff n]))
            | Factor.sym s => do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [Factor.sym s]))
      pure r : Id (List Factor)) =
      Id.run (forIn factors [] (fun f r =>
        match f with
        | Factor.coeff n =>
          if intMod n q ≠ 0 then
            pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
          else
            pure (ForInStep.yield (r ++ [Factor.coeff n]))
        | Factor.sym s => pure (ForInStep.yield (r ++ [Factor.sym s])))) := rfl
    rw [h2, modFactors_forIn]
    simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_modFactors q factors result := result = (if q = 1 then factors else reduceFactors q factors). This is a FULLY-PINNED TOTAL FUNCTIONAL spec: it pins the exact output for every (q, factors) with NO precondition freedom, and the axioms region is EMPTY (comment-only, no opaque/axiom callee contracts). There are therefore NO A-legs (axioms/deep-model refs) to abuse — the entire behavior is modeled deeply via exact Int arithmetic (intMod = a - b*Int.fdiv a b, floored) and structural carry-through of symbolic factors. refinement.md audit: every leg is R (residue arithmetic Python floored % <-> intMod, G-CONF-tested) or I (iteration, zero-residue keep, sym preserve, list rebuild); no kind-3; G-AX is a legitimate skip stub since no callee axiom is consumed. mapping.md's q=0 totalization (intMod n 0 = n => reduceFactors 0 = id) removes the precondition-shadowed freedom a prior spec-too-weak audit exploited.

SAME_SPEC: all 7 attacks confirmed True via swebench_unified.markers.same_spec (impl-region-only edits; axioms/pure/pre/post byte-identical).

### VERIFICATIONS (scripts/lean_verify.sh, cap 300s, run concurrently <=4/batch):
- pos_control.lean (exact gold): EXIT=0. #print axioms correct_modFactors -> [propext, Quot.sound] (clean/standard).
- atk_1 prepatch bug (return factors unchanged): EXIT=1, honest rfl fails on 'pure factors = reduceFactors q factors'.
- atk_2 partial-domain (skip reduction when q<=0): EXIT=3 (sorry only).
- atk_3 boundary (always take residue, drops zero-residue-keep): EXIT=3 (sorry only).
- atk_4 control-flow-effect (prepend => reversed factor order): EXIT=3 (sorry only).
- atk_6 ungrounded-oracle echo (symbolic factor id +1, should be preserved): EXIT=3 (sorry only).
- atk_7 truncating emod n%q instead of floored intMod (wrong sign at negative divisor): EXIT=3 (sorry only).
- atk_5 VERIFYING ECHO (impl = if q=1 then factors else reduceFactors q factors; textually distinct from gold's Id.run/forIn loop but extensionally equal): EXIT=0. #print axioms -> 'does not depend on any axioms' (fully clean).

Each wrong impl's divergence from the spec is PROVED by a concrete decide witness (refute.lean + refute7.lean, both EXIT=0):
  atk_1: [coeff 3] != spec 2 [coeff 3]  (spec=[coeff 1])
  atk_2: [coeff 3] != spec (-2) [coeff 3]
  atk_3: [coeff (intMod 8 4)]=[coeff 0] != spec 4 [coeff 8]=[coeff 8]
  atk_4: [coeff(intMod 8 5),coeff(intMod 2 5)] != spec 5 [coeff 2,coeff 8] (order reversed)
  atk_6: [sym 1] != spec 2 [sym 0]
  atk_7: [coeff (3 % -2)]=[coeff 1] != spec (-2) [coeff 3]=[coeff -1] (floored vs truncating; probe.lean confirms 3 % -2 = 1 vs intMod 3 -2 = -1)
So each wrong impl's correct_modFactors is GENUINELY unprovable (unsound), not merely unfinished; only sorry closes them.

RESOLVE STEP (protocol step 2 — mandatory for every verifying clean-axiom impl): the only impl with a closing clean-axiom proof is atk_5, which is extensionally EQUAL to the gold function, so its faithful refined patch IS the gold patch. Materialized to atk_5.patch and executed run_resolve('sympy__sympy-15599', ..., retries=0): RESOLVED=True COMPLETED=True NOTE='resolved'. Bench: swe_bench_verified, docker oracle live, style=swebench. So the verifying candidate's faithful patch DOES resolve — no verify-but-not-resolve counterexample exists.

CONCLUSION: >=6 distinct genuinely-wrong same-spec impls (prepatch, partial-domain, boundary, control-flow-effect, ungrounded-oracle, wrong-residue-convention) all FAIL to verify (proved divergent by decide witnesses); the sole verifying same-spec impl is a gold-equivalent echo whose faithful patch RESOLVES. The spec has no axiom/deep-model leg to exploit and admits no verifying-but-incorrect implementation. verify => correct holds. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec drift / spec-too-strong) verified for sympy__sympy-15599 lean bundle; no diverging input found.

MODELED CALLEE: the `non_mod_l` reduction loop the gold patch adds inside `Mod.eval`'s `isinstance(p, Mul)` branch (sympy/core/mod.py @ base 5e17a90c): `if q.is_Integer and q is not S.One: for i in non_mod_l: if i.is_Integer and (i%q is not S.Zero): append(i%q) else append(i)`.

### Checks run
1. same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True — spec regions (pure/post-conditions/axioms) are byte-identical; only impl+proof differ. spec_view confirms elision. G-HYGIENE region hashes consistent.
2. lean_verify.sh on Solution.lean => exit 0; `#print axioms correct_modFactors` = [propext, Quot.sound] — NO sorryAx, proof is genuine (loop→reduceFactors lemma + total spec, no q!=0 precondition).
3. Bundle conformance_check.py against real patched sympy: 120009 checks, 0 disagreements.
4. Independent adversarial differential (my own, fresh seed 999999, 200000 draws): coeffs ±100000, divisors ±1000 incl. negatives, symbolic factors, against the EXACT patched loop over real sympy Integer/Symbol objects — 0 mismatches. Floored intMod (a - b*(a//b)) matches sympy Integer.__mod__ across 20000 draws.
5. Boundary probes: Symbol('n', integer=True).is_Integer == False in sympy (is_Integer means CONCRETE Integer), so integer-valued symbols correctly map to Factor.sym, never coeff — the two-case coeff/sym split is faithful. q=1 short-circuit, negative-divisor floored sign, and zero-residue-factor-kept all match.

q=0 TOTALIZATION: the real callee never executes the loop at q=0 (Mod.eval's doit raises ZeroDivisionError('Modulo by zero') upstream, pre- and post-patch), so the loop is unreachable there. The model is total (intMod n 0 = n => identity), a documented unreachable-input convention that does NOT contradict any real callee behavior; conformance correctly skips q=0. This totalization closes precondition-shadowed freedom rather than introducing drift. The spec is neither too strong nor drifted: it pins each factor for every reachable (q, factors), and every prediction agrees with the real repo loop.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (impl+proof elided) names no patched file path (sympy/core/mod.py absent), no patched repo symbol (Mod.eval/doit/non_mod_l/Mul absent; spec identifiers are the abstract Factor/coeff/sym/intMod/reduceFactor/reduceFactors/problem_spec_modFactors), no diff markers, and no bug/fix narration. Lexical G-LEAK legitimately passes. The behavior the spec pins — reduce concrete-integer factors modulo q (floored remainder), q=1 short-circuit, keep zero-residue factor, preserve symbolic factors — is a spec's proper job to encode and is moreover ALREADY public: the problem_statement itself contains a proposed diff to mod.py and states Mod(3*i,2)→Mod(i,2). Judged against problem_statement only (not hints_text). No spec-view line reconstructs the gold edit or localizes it beyond the public task. same_spec(Solution, Solution_prepatch)=True confirms the differentiator lives in the elided impl/proof, not the visible spec.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
