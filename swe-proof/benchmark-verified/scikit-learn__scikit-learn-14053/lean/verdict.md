# P2 adversarial audit — scikit-learn__scikit-learn-14053

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec is an exact functional-equality postcondition (result = featureNamesSpec featureNames features), so no same-spec impl that deviates from the fold can verify. The only same-spec attack that verified (atk_7) is an ungrounded-oracle echo returning `featureNamesSpec` directly; it is extensionally identical to the spec (behaviorally correct), and its faithful refined patch (== the gold post-patch comprehension) RESOLVES under the official harness (RESOLVED=True, completed, non-flaky). Per resolved-echo-attack policy this is not a weakness. verify=>correct holds.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,60 +40,19 @@
   Id.run do
     let mut acc : List (Option String) := []
     for i in features do
-      if i ≠ sentinelIndex then
-        acc := acc ++ [featureNames[i.toNat]?]
-      else
-        acc := acc ++ [none]
+      acc := acc ++ [featureNames[i.toNat]?]
     return acc
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` loop over the index list, generalized
-over the accumulator, folds to `acc ++ featureNamesSpec`. -/
-theorem featureNamesByNode_forIn (featureNames : List String) :
-    ∀ (features : List Int) (acc : List (Option String)),
-      Id.run (forIn features acc (fun i r =>
-        (if i ≠ sentinelIndex then
-            (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)
-         else
-            pure (ForInStep.yield (r ++ [none])))))
-      = acc ++ featureNamesSpec featureNames features := by
-  intro features
-  induction features with
-  | nil =>
-    intro acc
-    simp only [List.forIn_nil, featureNamesSpec, List.append_nil]; rfl
-  | cons a as ih =>
-    intro acc
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a ≠ sentinelIndex
-    · simp only [if_pos h, featureNamesSpec, featureNameAt, ih, List.append_assoc,
-        List.cons_append, List.nil_append]
-    · simp only [if_neg h, featureNamesSpec, featureNameAt, ih, List.append_assoc,
-        List.cons_append, List.nil_append]
-
 theorem correct_featureNamesByNode :
     ∀ (featureNames : List String) (features : List Int),
       problem_spec_featureNamesByNode featureNames features
         (implementation_featureNamesByNode featureNames features) := by
   intro featureNames features
   unfold problem_spec_featureNamesByNode implementation_featureNamesByNode
-  -- bridge the desugared `do … for … mut …` body to the helper's clean body
-  have h2 :
-      (Id.run do
-        let mut acc : List (Option String) := []
-        for i in features do
-          if i ≠ sentinelIndex then
-            acc := acc ++ [featureNames[i.toNat]?]
-          else
-            acc := acc ++ [none]
-        return acc)
-      = Id.run (forIn features ([] : List (Option String)) (fun i r =>
-          (if i ≠ sentinelIndex then
-              (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)
-           else
-              pure (ForInStep.yield (r ++ [none]))))) := rfl
-  rw [h2, featureNamesByNode_forIn]
-  simp
+  induction features with
+  | nil => simp [featureNamesSpec]
+  | cons a as ih =>
+    simp_all [List.forIn_cons, featureNamesSpec, featureNameAt]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,59 +41,21 @@
     let mut acc : List (Option String) := []
     for i in features do
       if i ≠ sentinelIndex then
-        acc := acc ++ [featureNames[i.toNat]?]
+        acc := acc ++ [featureNames[i.toNat + 1]?]
       else
         acc := acc ++ [none]
     return acc
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` loop over the index list, generalized
-over the accumulator, folds to `acc ++ featureNamesSpec`. -/
-theorem featureNamesByNode_forIn (featureNames : List String) :
-    ∀ (features : List Int) (acc : List (Option String)),
-      Id.run (forIn features acc (fun i r =>
-        (if i ≠ sentinelIndex then
-            (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)
-         else
-            pure (ForInStep.yield (r ++ [none])))))
-      = acc ++ featureNamesSpec featureNames features := by
-  intro features
-  induction features with
-  | nil =>
-    intro acc
-    simp only [List.forIn_nil, featureNamesSpec, List.append_nil]; rfl
-  | cons a as ih =>
-    intro acc
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a ≠ sentinelIndex
-    · simp only [if_pos h, featureNamesSpec, featureNameAt, ih, List.append_assoc,
-        List.cons_append, List.nil_append]
-    · simp only [if_neg h, featureNamesSpec, featureNameAt, ih, List.append_assoc,
-        List.cons_append, List.nil_append]
-
 theorem correct_featureNamesByNode :
     ∀ (featureNames : List String) (features : List Int),
       problem_spec_featureNamesByNode featureNames features
         (implementation_featureNamesByNode featureNames features) := by
   intro featureNames features
   unfold problem_spec_featureNamesByNode implementation_featureNamesByNode
-  -- bridge the desugared `do … for … mut …` body to the helper's clean body
-  have h2 :
-      (Id.run do
-        let mut acc : List (Option String) := []
-        for i in features do
-          if i ≠ sentinelIndex then
-            acc := acc ++ [featureNames[i.toNat]?]
-          else
-            acc := acc ++ [none]
-        return acc)
-      = Id.run (forIn features ([] : List (Option String)) (fun i r =>
-          (if i ≠ sentinelIndex then
-              (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)
-           else
-              pure (ForInStep.yield (r ++ [none]))))) := rfl
-  rw [h2, featureNamesByNode_forIn]
-  simp
+  induction features with
+  | nil => simp [featureNamesSpec]
+  | cons a as ih =>
+    simp_all [List.forIn_cons, featureNamesSpec, featureNameAt]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,59 +41,21 @@
     let mut acc : List (Option String) := []
     for i in features do
       if i ≠ sentinelIndex then
-        acc := acc ++ [featureNames[i.toNat]?]
+        acc := [featureNames[i.toNat]?] ++ acc
       else
-        acc := acc ++ [none]
+        acc := [none] ++ acc
     return acc
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` loop over the index list, generalized
-over the accumulator, folds to `acc ++ featureNamesSpec`. -/
-theorem featureNamesByNode_forIn (featureNames : List String) :
-    ∀ (features : List Int) (acc : List (Option String)),
-      Id.run (forIn features acc (fun i r =>
-        (if i ≠ sentinelIndex then
-            (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)
-         else
-            pure (ForInStep.yield (r ++ [none])))))
-      = acc ++ featureNamesSpec featureNames features := by
-  intro features
-  induction features with
-  | nil =>
-    intro acc
-    simp only [List.forIn_nil, featureNamesSpec, List.append_nil]; rfl
-  | cons a as ih =>
-    intro acc
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a ≠ sentinelIndex
-    · simp only [if_pos h, featureNamesSpec, featureNameAt, ih, List.append_assoc,
-        List.cons_append, List.nil_append]
-    · simp only [if_neg h, featureNamesSpec, featureNameAt, ih, List.append_assoc,
-        List.cons_append, List.nil_append]
-
 theorem correct_featureNamesByNode :
     ∀ (featureNames : List String) (features : List Int),
       problem_spec_featureNamesByNode featureNames features
         (implementation_featureNamesByNode featureNames features) := by
   intro featureNames features
   unfold problem_spec_featureNamesByNode implementation_featureNamesByNode
-  -- bridge the desugared `do … for … mut …` body to the helper's clean body
-  have h2 :
-      (Id.run do
-        let mut acc : List (Option String) := []
-        for i in features do
-          if i ≠ sentinelIndex then
-            acc := acc ++ [featureNames[i.toNat]?]
-          else
-            acc := acc ++ [none]
-        return acc)
-      = Id.run (forIn features ([] : List (Option String)) (fun i r =>
-          (if i ≠ sentinelIndex then
-              (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)
-           else
-              pure (ForInStep.yield (r ++ [none]))))) := rfl
-  rw [h2, featureNamesByNode_forIn]
-  simp
+  induction features with
+  | nil => simp [featureNamesSpec]
+  | cons a as ih =>
+    simp_all [List.forIn_cons, featureNamesSpec, featureNameAt]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,7 @@
   Id.run do
     let mut acc : List (Option String) := []
     for i in features do
-      if i ≠ sentinelIndex then
+      if i ≥ 0 then
         acc := acc ++ [featureNames[i.toNat]?]
       else
         acc := acc ++ [none]
@@ -48,52 +48,14 @@
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` loop over the index list, generalized
-over the accumulator, folds to `acc ++ featureNamesSpec`. -/
-theorem featureNamesByNode_forIn (featureNames : List String) :
-    ∀ (features : List Int) (acc : List (Option String)),
-      Id.run (forIn features acc (fun i r =>
-        (if i ≠ sentinelIndex then
-            (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)
-         else
-            pure (ForInStep.yield (r ++ [none])))))
-      = acc ++ featureNamesSpec featureNames features := by
-  intro features
-  induction features with
-  | nil =>
-    intro acc
-    simp only [List.forIn_nil, featureNamesSpec, List.append_nil]; rfl
-  | cons a as ih =>
-    intro acc
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a ≠ sentinelIndex
-    · simp only [if_pos h, featureNamesSpec, featureNameAt, ih, List.append_assoc,
-        List.cons_append, List.nil_append]
-    · simp only [if_neg h, featureNamesSpec, featureNameAt, ih, List.append_assoc,
-        List.cons_append, List.nil_append]
-
 theorem correct_featureNamesByNode :
     ∀ (featureNames : List String) (features : List Int),
       problem_spec_featureNamesByNode featureNames features
         (implementation_featureNamesByNode featureNames features) := by
   intro featureNames features
   unfold problem_spec_featureNamesByNode implementation_featureNamesByNode
-  -- bridge the desugared `do … for … mut …` body to the helper's clean body
-  have h2 :
-      (Id.run do
-        let mut acc : List (Option String) := []
-        for i in features do
-          if i ≠ sentinelIndex then
-            acc := acc ++ [featureNames[i.toNat]?]
-          else
-            acc := acc ++ [none]
-        return acc)
-      = Id.run (forIn features ([] : List (Option String)) (fun i r =>
-          (if i ≠ sentinelIndex then
-              (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)
-           else
-              pure (ForInStep.yield (r ++ [none]))))) := rfl
-  rw [h2, featureNamesByNode_forIn]
-  simp
+  induction features with
+  | nil => simp [featureNamesSpec]
+  | cons a as ih =>
+    simp_all [List.forIn_cons, featureNamesSpec, featureNameAt]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,59 +41,21 @@
     let mut acc : List (Option String) := []
     for i in features do
       if i ≠ sentinelIndex then
+        acc := acc ++ [none]
+      else
         acc := acc ++ [featureNames[i.toNat]?]
-      else
-        acc := acc ++ [none]
     return acc
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` loop over the index list, generalized
-over the accumulator, folds to `acc ++ featureNamesSpec`. -/
-theorem featureNamesByNode_forIn (featureNames : List String) :
-    ∀ (features : List Int) (acc : List (Option String)),
-      Id.run (forIn features acc (fun i r =>
-        (if i ≠ sentinelIndex then
-            (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)
-         else
-            pure (ForInStep.yield (r ++ [none])))))
-      = acc ++ featureNamesSpec featureNames features := by
-  intro features
-  induction features with
-  | nil =>
-    intro acc
-    simp only [List.forIn_nil, featureNamesSpec, List.append_nil]; rfl
-  | cons a as ih =>
-    intro acc
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a ≠ sentinelIndex
-    · simp only [if_pos h, featureNamesSpec, featureNameAt, ih, List.append_assoc,
-        List.cons_append, List.nil_append]
-    · simp only [if_neg h, featureNamesSpec, featureNameAt, ih, List.append_assoc,
-        List.cons_append, List.nil_append]
-
 theorem correct_featureNamesByNode :
     ∀ (featureNames : List String) (features : List Int),
       problem_spec_featureNamesByNode featureNames features
         (implementation_featureNamesByNode featureNames features) := by
   intro featureNames features
   unfold problem_spec_featureNamesByNode implementation_featureNamesByNode
-  -- bridge the desugared `do … for … mut …` body to the helper's clean body
-  have h2 :
-      (Id.run do
-        let mut acc : List (Option String) := []
-        for i in features do
-          if i ≠ sentinelIndex then
-            acc := acc ++ [featureNames[i.toNat]?]
-          else
-            acc := acc ++ [none]
-        return acc)
-      = Id.run (forIn features ([] : List (Option String)) (fun i r =>
-          (if i ≠ sentinelIndex then
-              (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)
-           else
-              pure (ForInStep.yield (r ++ [none]))))) := rfl
-  rw [h2, featureNamesByNode_forIn]
-  simp
+  induction features with
+  | nil => simp [featureNamesSpec]
+  | cons a as ih =>
+    simp_all [List.forIn_cons, featureNamesSpec, featureNameAt]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -39,61 +39,20 @@
     (featureNames : List String) (features : List Int) : List (Option String) :=
   Id.run do
     let mut acc : List (Option String) := []
-    for i in features do
-      if i ≠ sentinelIndex then
-        acc := acc ++ [featureNames[i.toNat]?]
-      else
-        acc := acc ++ [none]
+    for _i in features do
+      acc := acc ++ [none]
     return acc
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` loop over the index list, generalized
-over the accumulator, folds to `acc ++ featureNamesSpec`. -/
-theorem featureNamesByNode_forIn (featureNames : List String) :
-    ∀ (features : List Int) (acc : List (Option String)),
-      Id.run (forIn features acc (fun i r =>
-        (if i ≠ sentinelIndex then
-            (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)
-         else
-            pure (ForInStep.yield (r ++ [none])))))
-      = acc ++ featureNamesSpec featureNames features := by
-  intro features
-  induction features with
-  | nil =>
-    intro acc
-    simp only [List.forIn_nil, featureNamesSpec, List.append_nil]; rfl
-  | cons a as ih =>
-    intro acc
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a ≠ sentinelIndex
-    · simp only [if_pos h, featureNamesSpec, featureNameAt, ih, List.append_assoc,
-        List.cons_append, List.nil_append]
-    · simp only [if_neg h, featureNamesSpec, featureNameAt, ih, List.append_assoc,
-        List.cons_append, List.nil_append]
-
 theorem correct_featureNamesByNode :
     ∀ (featureNames : List String) (features : List Int),
       problem_spec_featureNamesByNode featureNames features
         (implementation_featureNamesByNode featureNames features) := by
   intro featureNames features
   unfold problem_spec_featureNamesByNode implementation_featureNamesByNode
-  -- bridge the desugared `do … for … mut …` body to the helper's clean body
-  have h2 :
-      (Id.run do
-        let mut acc : List (Option String) := []
-        for i in features do
-          if i ≠ sentinelIndex then
-            acc := acc ++ [featureNames[i.toNat]?]
-          else
-            acc := acc ++ [none]
-        return acc)
-      = Id.run (forIn features ([] : List (Option String)) (fun i r =>
-          (if i ≠ sentinelIndex then
-              (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)
-           else
-              pure (ForInStep.yield (r ++ [none]))))) := rfl
-  rw [h2, featureNamesByNode_forIn]
-  simp
+  induction features with
+  | nil => simp [featureNamesSpec]
+  | cons a as ih =>
+    simp_all [List.forIn_cons, featureNamesSpec, featureNameAt]
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -37,63 +37,14 @@
 -- impl-start
 def implementation_featureNamesByNode
     (featureNames : List String) (features : List Int) : List (Option String) :=
-  Id.run do
-    let mut acc : List (Option String) := []
-    for i in features do
-      if i ≠ sentinelIndex then
-        acc := acc ++ [featureNames[i.toNat]?]
-      else
-        acc := acc ++ [none]
-    return acc
+  featureNamesSpec featureNames features
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` loop over the index list, generalized
-over the accumulator, folds to `acc ++ featureNamesSpec`. -/
-theorem featureNamesByNode_forIn (featureNames : List String) :
-    ∀ (features : List Int) (acc : List (Option String)),
-      Id.run (forIn features acc (fun i r =>
-        (if i ≠ sentinelIndex then
-            (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)
-         else
-            pure (ForInStep.yield (r ++ [none])))))
-      = acc ++ featureNamesSpec featureNames features := by
-  intro features
-  induction features with
-  | nil =>
-    intro acc
-    simp only [List.forIn_nil, featureNamesSpec, List.append_nil]; rfl
-  | cons a as ih =>
-    intro acc
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a ≠ sentinelIndex
-    · simp only [if_pos h, featureNamesSpec, featureNameAt, ih, List.append_assoc,
-        List.cons_append, List.nil_append]
-    · simp only [if_neg h, featureNamesSpec, featureNameAt, ih, List.append_assoc,
-        List.cons_append, List.nil_append]
-
 theorem correct_featureNamesByNode :
     ∀ (featureNames : List String) (features : List Int),
       problem_spec_featureNamesByNode featureNames features
         (implementation_featureNamesByNode featureNames features) := by
   intro featureNames features
-  unfold problem_spec_featureNamesByNode implementation_featureNamesByNode
-  -- bridge the desugared `do … for … mut …` body to the helper's clean body
-  have h2 :
-      (Id.run do
-        let mut acc : List (Option String) := []
-        for i in features do
-          if i ≠ sentinelIndex then
-            acc := acc ++ [featureNames[i.toNat]?]
-          else
-            acc := acc ++ [none]
-        return acc)
-      = Id.run (forIn features ([] : List (Option String)) (fun i r =>
-          (if i ≠ sentinelIndex then
-              (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)
-           else
-              pure (ForInStep.yield (r ++ [none]))))) := rfl
-  rw [h2, featureNamesByNode_forIn]
-  simp
+  rfl
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -39,8 +39,11 @@
     (featureNames : List String) (features : List Int) : List (Option String) :=
   Id.run do
     let mut acc : List (Option String) := []
+    let mut first := true
     for i in features do
-      if i ≠ sentinelIndex then
+      if first then
+        first := false
+      else if i ≠ sentinelIndex then
         acc := acc ++ [featureNames[i.toNat]?]
       else
         acc := acc ++ [none]
@@ -48,52 +51,14 @@
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` loop over the index list, generalized
-over the accumulator, folds to `acc ++ featureNamesSpec`. -/
-theorem featureNamesByNode_forIn (featureNames : List String) :
-    ∀ (features : List Int) (acc : List (Option String)),
-      Id.run (forIn features acc (fun i r =>
-        (if i ≠ sentinelIndex then
-            (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)
-         else
-            pure (ForInStep.yield (r ++ [none])))))
-      = acc ++ featureNamesSpec featureNames features := by
-  intro features
-  induction features with
-  | nil =>
-    intro acc
-    simp only [List.forIn_nil, featureNamesSpec, List.append_nil]; rfl
-  | cons a as ih =>
-    intro acc
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a ≠ sentinelIndex
-    · simp only [if_pos h, featureNamesSpec, featureNameAt, ih, List.append_assoc,
-        List.cons_append, List.nil_append]
-    · simp only [if_neg h, featureNamesSpec, featureNameAt, ih, List.append_assoc,
-        List.cons_append, List.nil_append]
-
 theorem correct_featureNamesByNode :
     ∀ (featureNames : List String) (features : List Int),
       problem_spec_featureNamesByNode featureNames features
         (implementation_featureNamesByNode featureNames features) := by
   intro featureNames features
   unfold problem_spec_featureNamesByNode implementation_featureNamesByNode
-  -- bridge the desugared `do … for … mut …` body to the helper's clean body
-  have h2 :
-      (Id.run do
-        let mut acc : List (Option String) := []
-        for i in features do
-          if i ≠ sentinelIndex then
-            acc := acc ++ [featureNames[i.toNat]?]
-          else
-            acc := acc ++ [none]
-        return acc)
-      = Id.run (forIn features ([] : List (Option String)) (fun i r =>
-          (if i ≠ sentinelIndex then
-              (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)
-           else
-              pure (ForInStep.yield (r ++ [none]))))) := rfl
-  rw [h2, featureNamesByNode_forIn]
-  simp
+  induction features with
+  | nil => simp [featureNamesSpec]
+  | cons a as ih =>
+    simp_all [List.forIn_cons, featureNamesSpec, featureNameAt]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the per-entry label lookup is
-- modeled DEEPLY (a total list index, below) rather than axiomatized. The proof
-- agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- A designated sentinel index value that marks an entry having no associated
name (as opposed to a genuine, in-range position into the name list). -/
def sentinelIndex : Int := -2

/-- Resolve one index against the name list. A sentinel index yields no name
(`none`); any other index looks the name up by position, yielding `some name`
when it is in range. -/
def featureNameAt (featureNames : List String) (i : Int) : Option String :=
  if i ≠ sentinelIndex then featureNames[i.toNat]? else none

/-- Front-recursive specification fold: resolve each index in order. -/
def featureNamesSpec (featureNames : List String) : List Int → List (Option String)
  | [] => []
  | i :: rest => featureNameAt featureNames i :: featureNamesSpec featureNames rest
-- pure-end

-- post-conditions-start
/-- The result is exactly the per-entry resolution of the index list against the
name list, in order: an entry whose index is the sentinel resolves to no name
(`none`), and every other entry resolves to the name at that position. -/
def problem_spec_featureNamesByNode
    (featureNames : List String) (features : List Int)
    (result : List (Option String)) : Prop :=
  result = featureNamesSpec featureNames features
-- post-conditions-end

-- impl-start
def implementation_featureNamesByNode
    (featureNames : List String) (features : List Int) : List (Option String) :=
  Id.run do
    let mut acc : List (Option String) := []
    for i in features do
      if i ≠ sentinelIndex then
        acc := acc ++ [featureNames[i.toNat]?]
      else
        acc := acc ++ [none]
    return acc
-- impl-end

-- proof-start
/-- Helper (Route B): the cleaned `forIn` loop over the index list, generalized
over the accumulator, folds to `acc ++ featureNamesSpec`. -/
theorem featureNamesByNode_forIn (featureNames : List String) :
    ∀ (features : List Int) (acc : List (Option String)),
      Id.run (forIn features acc (fun i r =>
        (if i ≠ sentinelIndex then
            (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)
         else
            pure (ForInStep.yield (r ++ [none])))))
      = acc ++ featureNamesSpec featureNames features := by
  intro features
  induction features with
  | nil =>
    intro acc
    simp only [List.forIn_nil, featureNamesSpec, List.append_nil]; rfl
  | cons a as ih =>
    intro acc
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : a ≠ sentinelIndex
    · simp only [if_pos h, featureNamesSpec, featureNameAt, ih, List.append_assoc,
        List.cons_append, List.nil_append]
    · simp only [if_neg h, featureNamesSpec, featureNameAt, ih, List.append_assoc,
        List.cons_append, List.nil_append]

theorem correct_featureNamesByNode :
    ∀ (featureNames : List String) (features : List Int),
      problem_spec_featureNamesByNode featureNames features
        (implementation_featureNamesByNode featureNames features) := by
  intro featureNames features
  unfold problem_spec_featureNamesByNode implementation_featureNamesByNode
  -- bridge the desugared `do … for … mut …` body to the helper's clean body
  have h2 :
      (Id.run do
        let mut acc : List (Option String) := []
        for i in features do
          if i ≠ sentinelIndex then
            acc := acc ++ [featureNames[i.toNat]?]
          else
            acc := acc ++ [none]
        return acc)
      = Id.run (forIn features ([] : List (Option String)) (fun i r =>
          (if i ≠ sentinelIndex then
              (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)
           else
              pure (ForInStep.yield (r ++ [none]))))) := rfl
  rw [h2, featureNamesByNode_forIn]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

ENV: worked only Root; same_spec('lean') = True for all 8 attacks (axioms/pure/pre/post byte-identical; only impl+proof edited).

SPEC SHAPE: post = `result = featureNamesSpec featureNames features` — exact functional equality; maximally tight. Any verifying impl must be extensionally equal to the fold on every input.

A-LEG AUDIT (plan §4): meta.json axioms=[], deep_model_references=[], opaque_callees=[]. refinement.md legs are all I (rows 1,2,4) and R (row 3: sentinel guard modeled deeply; _tree.TREE_UNDEFINED=-2 <-> sentinelIndex=-2; feature_names[i] <-> total featureNames[i.toNat]?; None <-> none). NO A-consumed / A-reference / kind-3 legs — nothing to validate against real callees. axiom_check.py is a legitimate skip stub (empty axioms region). Correspondence holds.

### ATTACKS (cmd: bash scripts/lean_verify.sh <f>):
- atk_1 (prepatch bug: drop sentinel guard, unconditional lookup) EXIT=1 (proof fails to close; behaviorally [some,some,some] vs spec [some,none,none]). prepatch reproduced.
- atk_2 (boundary/off-by-one: featureNames[i.toNat+1]?) EXIT=1.
- atk_3 (control-flow-effect: prepend instead of append -> reverses order) EXIT=1.
- atk_4 (wrong guard: i>=0 instead of i != sentinelIndex; differs on other negatives) EXIT=1.
- atk_5 (none/some swap: none for internal, lookup for sentinel) EXIT=1.
- atk_6 (constant/partial-domain: always none, correct length) EXIT=1.
- atk_8 (partial-domain: drops first entry) EXIT=1.
- atk_7 (ungrounded-oracle echo: impl = featureNamesSpec featureNames features; proof by rfl) EXIT=0. `#print axioms correct_featureNamesByNode` => 'does not depend on any axioms' (CLEAN).
Positive control (gold Solution.lean copy) EXIT=0.

RESOLVE (protocol step 2, atk_7 is the only verifying attack): materialized faithful patch = gold post-patch comprehension (atk_7 impl `featureNamesSpec` = 'sentinel->none else lookup' = post-patch behavior). Ran run_resolve('scikit-learn__scikit-learn-14053', patch, timeout=1800) => RESOLVED=True, COMPLETED=True, ATTEMPTS=1, FLAKY=False, note='resolved'. A resolving echo is behaviorally correct, not a weakness (2026-08-06 echo-attack policy).

CONCLUSION: 7 genuinely-wrong distinct impls all fail to verify; the one verifying same-spec impl is a resolving echo. No verifying same-spec impl has a faithful patch that fails to resolve. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec is an exact functional-equality postcondition (result = featureNamesSpec featureNames features), so no same-spec impl that deviates from the fold can verify. The only same-spec attack that verified (atk_7) is an ungrounded-oracle echo returning `featureNamesSpec` directly; it is extensionally identical to the spec (behaviorally correct), and its faithful refined patch (== the gold post-patch comprehension) RESOLVES under the official harness (RESOLVED=True, completed, non-flaky). Per resolved-echo-attack policy this is not a weakness. verify=>correct holds.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the per-entry label lookup is
-- modeled DEEPLY (a total list index, below) rather than axiomatized. The proof
-- agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- A designated sentinel index value that marks an entry having no associated
name (as opposed to a genuine, in-range position into the name list). -/
def sentinelIndex : Int := -2

/-- Resolve one index against the name list. A sentinel index yields no name
(`none`); any other index looks the name up by position, yielding `some name`
when it is in range. -/
def featureNameAt (featureNames : List String) (i : Int) : Option String :=
  if i ≠ sentinelIndex then featureNames[i.toNat]? else none

/-- Front-recursive specification fold: resolve each index in order. -/
def featureNamesSpec (featureNames : List String) : List Int → List (Option String)
  | [] => []
  | i :: rest => featureNameAt featureNames i :: featureNamesSpec featureNames rest
-- pure-end

-- post-conditions-start
/-- The result is exactly the per-entry resolution of the index list against the
name list, in order: an entry whose index is the sentinel resolves to no name
(`none`), and every other entry resolves to the name at that position. -/
def problem_spec_featureNamesByNode
    (featureNames : List String) (features : List Int)
    (result : List (Option String)) : Prop :=
  result = featureNamesSpec featureNames features
-- post-conditions-end

-- impl-start
def implementation_featureNamesByNode
    (featureNames : List String) (features : List Int) : List (Option String) :=
  Id.run do
    let mut acc : List (Option String) := []
    for i in features do
      if i ≠ sentinelIndex then
        acc := acc ++ [featureNames[i.toNat]?]
      else
        acc := acc ++ [none]
    return acc
-- impl-end

-- proof-start
/-- Helper (Route B): the cleaned `forIn` loop over the index list, generalized
over the accumulator, folds to `acc ++ featureNamesSpec`. -/
theorem featureNamesByNode_forIn (featureNames : List String) :
    ∀ (features : List Int) (acc : List (Option String)),
      Id.run (forIn features acc (fun i r =>
        (if i ≠ sentinelIndex then
            (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)
         else
            pure (ForInStep.yield (r ++ [none])))))
      = acc ++ featureNamesSpec featureNames features := by
  intro features
  induction features with
  | nil =>
    intro acc
    simp only [List.forIn_nil, featureNamesSpec, List.append_nil]; rfl
  | cons a as ih =>
    intro acc
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : a ≠ sentinelIndex
    · simp only [if_pos h, featureNamesSpec, featureNameAt, ih, List.append_assoc,
        List.cons_append, List.nil_append]
    · simp only [if_neg h, featureNamesSpec, featureNameAt, ih, List.append_assoc,
        List.cons_append, List.nil_append]

theorem correct_featureNamesByNode :
    ∀ (featureNames : List String) (features : List Int),
      problem_spec_featureNamesByNode featureNames features
        (implementation_featureNamesByNode featureNames features) := by
  intro featureNames features
  unfold problem_spec_featureNamesByNode implementation_featureNamesByNode
  -- bridge the desugared `do … for … mut …` body to the helper's clean body
  have h2 :
      (Id.run do
        let mut acc : List (Option String) := []
        for i in features do
          if i ≠ sentinelIndex then
            acc := acc ++ [featureNames[i.toNat]?]
          else
            acc := acc ++ [none]
        return acc)
      = Id.run (forIn features ([] : List (Option String)) (fun i r =>
          (if i ≠ sentinelIndex then
              (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)
           else
              pure (ForInStep.yield (r ++ [none]))))) := rfl
  rw [h2, featureNamesByNode_forIn]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

ENV: worked only Root; same_spec('lean') = True for all 8 attacks (axioms/pure/pre/post byte-identical; only impl+proof edited).

SPEC SHAPE: post = `result = featureNamesSpec featureNames features` — exact functional equality; maximally tight. Any verifying impl must be extensionally equal to the fold on every input.

A-LEG AUDIT (plan §4): meta.json axioms=[], deep_model_references=[], opaque_callees=[]. refinement.md legs are all I (rows 1,2,4) and R (row 3: sentinel guard modeled deeply; _tree.TREE_UNDEFINED=-2 <-> sentinelIndex=-2; feature_names[i] <-> total featureNames[i.toNat]?; None <-> none). NO A-consumed / A-reference / kind-3 legs — nothing to validate against real callees. axiom_check.py is a legitimate skip stub (empty axioms region). Correspondence holds.

### ATTACKS (cmd: bash scripts/lean_verify.sh <f>):
- atk_1 (prepatch bug: drop sentinel guard, unconditional lookup) EXIT=1 (proof fails to close; behaviorally [some,some,some] vs spec [some,none,none]). prepatch reproduced.
- atk_2 (boundary/off-by-one: featureNames[i.toNat+1]?) EXIT=1.
- atk_3 (control-flow-effect: prepend instead of append -> reverses order) EXIT=1.
- atk_4 (wrong guard: i>=0 instead of i != sentinelIndex; differs on other negatives) EXIT=1.
- atk_5 (none/some swap: none for internal, lookup for sentinel) EXIT=1.
- atk_6 (constant/partial-domain: always none, correct length) EXIT=1.
- atk_8 (partial-domain: drops first entry) EXIT=1.
- atk_7 (ungrounded-oracle echo: impl = featureNamesSpec featureNames features; proof by rfl) EXIT=0. `#print axioms correct_featureNamesByNode` => 'does not depend on any axioms' (CLEAN).
Positive control (gold Solution.lean copy) EXIT=0.

RESOLVE (protocol step 2, atk_7 is the only verifying attack): materialized faithful patch = gold post-patch comprehension (atk_7 impl `featureNamesSpec` = 'sentinel->none else lookup' = post-patch behavior). Ran run_resolve('scikit-learn__scikit-learn-14053', patch, timeout=1800) => RESOLVED=True, COMPLETED=True, ATTEMPTS=1, FLAKY=False, note='resolved'. A resolving echo is behaviorally correct, not a weakness (2026-08-06 echo-attack policy).

CONCLUSION: 7 genuinely-wrong distinct impls all fail to verify; the one verifying same-spec impl is a resolving echo. No verifying same-spec impl has a faithful patch that fails to resolve. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled op = post-patch comprehension `[feature_names[i] if i != _tree.TREE_UNDEFINED else None for i in tree_.feature]` (export.py:892-894 @ 6ab8c86c). Verified: (1) Solution.lean compiles clean, #print axioms = [propext, Quot.sound], NO sorryAx — proof is genuine. (2) same_spec(Solution, Solution_prepatch)=True with lean backend — spec region frozen. (3) TREE_UNDEFINED=-2 confirmed at base commit _tree.pyx:64; ValueError length guard confirmed at export.py:873-877 (guarantees internal indices in range). (4) conformance_check.py: 120007 inputs, 0 disagreements. On the full reachable domain (non-negative in-range indices + the -2 sentinel) i.toNat=i, the total featureNames[i.toNat]? returns `some name` exactly where Python's partial feature_names[i] succeeds, and -2 -> none matches None. The spec faithfully refines the real callee on every input it can actually receive; the total-lookup vs partial-lookup gap manifests only on inputs tree_.feature never produces. Spec also correctly discriminates the buggy prepatch impl (G-DIFF intact). No drift, spec not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Baseline = public problem_statement ONLY (hints_text excluded per role). Verifications: same_spec(post,pre)=True with the Lean LanguageTables (impl-only change; spec region stable); rendered spec_view sha256 5d80087506e10b682b0e893afff99ecbcf31dc06fe0c3f3bed97e57f81a8f4aa matches meta.region_hashes.spec_view (judged the frozen view); mechanical leakage.screen passes clean (hard_failures=[]).

The problem_statement discloses only the SYMPTOM: 'IndexError: list index out of range in export_text when the tree only has one feature' plus a repro snippet. It never names -2, TREE_UNDEFINED, leaf nodes, tree_.feature, or the None-substitution fix (those live in hints_text, out of scope).

The spec view exposes sentinelIndex := -2, featureNameAt (sentinel -> none, else positional lookup), featureNamesSpec, and postcondition result = featureNamesSpec. This is a faithful postcondition of CORRECT behavior, not a reconstruction of the gold edit: (1) no diff markers; (2) the gold-patch token _tree.TREE_UNDEFINED never appears — the sentinel is framed abstractly ('a designated sentinel index value that marks an entry having no associated name'); (3) no patched file path, no Python symbols (export_text/feature_names/tree_.feature), no literal comprehension; (4) no problem_statement phrasing quoted in comments. The constant -2 is a necessary datum of the correct-behavior spec, not a lexical echo of the patch. Under the calibrated G-LEAK standard, specifying correct behavior is permitted; nothing here reconstructs the gold edit beyond what a faithful spec must encode. Concurs with recorded G-LEAK pass and G-PANEL-3 NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
