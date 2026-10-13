# P2 adversarial audit — django__django-15368

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,6 +92,7 @@
     result[i]? = some (⟨pk, !resolvesToReference attr.kind, attr.ident⟩ : CaseBranch)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_bulkUpdateBranches
     (objs : List (Nat × AttrValue)) : List CaseBranch := Id.run do
@@ -100,7 +101,7 @@
     let pk := obj.1
     let attr := obj.2
     let mut wrapped := false
-    if !resolvesToReference attr.kind then
+    if attr.kind != ValueKind.directExpression then
       wrapped := true
     whenStatements := whenStatements ++ [⟨pk, wrapped, attr.ident⟩]
   return whenStatements
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,76 +92,21 @@
     result[i]? = some (⟨pk, !resolvesToReference attr.kind, attr.ident⟩ : CaseBranch)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_bulkUpdateBranches
-    (objs : List (Nat × AttrValue)) : List CaseBranch := Id.run do
-  let mut whenStatements : List CaseBranch := []
-  for obj in objs do
-    let pk := obj.1
-    let attr := obj.2
-    let mut wrapped := false
-    if !resolvesToReference attr.kind then
-      wrapped := true
-    whenStatements := whenStatements ++ [⟨pk, wrapped, attr.ident⟩]
-  return whenStatements
+    (objs : List (Nat × AttrValue)) : List CaseBranch :=
+  objs.map (fun o => (⟨o.1, true, o.2.ident⟩ : CaseBranch))
 -- impl-end
 
 -- proof-start
-/-- Loop body lemma (Route B): the cleaned `forIn` over `objs`, generalized over
-the accumulator `init`, accumulates one branch per record (in order), wrapping a
-literal exactly when the value does not resolve to a reference. -/
-private theorem bulkUpdateBranches_forIn
-    (objs : List (Nat × AttrValue)) (init : List CaseBranch) :
-    (Id.run (forIn objs init fun obj r =>
-      if (!resolvesToReference obj.2.kind) = true then
-        pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
-      else
-        pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)]))))
-    = init ++ objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch)) := by
-  induction objs generalizing init with
-  | nil => simp only [Id.run, List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (!resolvesToReference a.2.kind) = true
-    · rw [if_pos h]
-      simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append, h]
-    · rw [if_neg h]
-      simp only [Bool.not_eq_true] at h
-      simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append, h]
-
-/-- The implementation equals the obvious `List.map`: bridge the desugared loop
-body (`do pure PUnit.unit; …; pure (ForInStep.yield …)`) to the cleaned body of
-`bulkUpdateBranches_forIn` (definitionally equal), then apply the lemma. -/
-private theorem bulkUpdateBranches_impl_eq (objs : List (Nat × AttrValue)) :
-    implementation_bulkUpdateBranches objs
-      = objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch)) := by
-  unfold implementation_bulkUpdateBranches
-  have h2 : (Id.run do
-      let r ← forIn objs ([] : List CaseBranch) fun obj r =>
-            if (!resolvesToReference obj.2.kind) = true then do
-              pure PUnit.unit
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
-            else do
-              pure PUnit.unit
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)]))
-      pure r)
-      = (Id.run (forIn objs ([] : List CaseBranch) fun obj r =>
-          if (!resolvesToReference obj.2.kind) = true then
-            pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
-          else
-            pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)])))) := rfl
-  rw [h2, bulkUpdateBranches_forIn]
-  simp
-
 theorem correct_bulkUpdateBranches :
     ∀ (objs : List (Nat × AttrValue)),
       problem_spec_bulkUpdateBranches objs
         (implementation_bulkUpdateBranches objs) := by
   intro objs
-  rw [problem_spec_bulkUpdateBranches, bulkUpdateBranches_impl_eq]
+  rw [problem_spec_bulkUpdateBranches]
+  unfold implementation_bulkUpdateBranches
   refine ⟨by simp, ?_⟩
   intro i pk attr hi
   rw [List.getElem?_map, hi]
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,76 +92,21 @@
     result[i]? = some (⟨pk, !resolvesToReference attr.kind, attr.ident⟩ : CaseBranch)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_bulkUpdateBranches
-    (objs : List (Nat × AttrValue)) : List CaseBranch := Id.run do
-  let mut whenStatements : List CaseBranch := []
-  for obj in objs do
-    let pk := obj.1
-    let attr := obj.2
-    let mut wrapped := false
-    if !resolvesToReference attr.kind then
-      wrapped := true
-    whenStatements := whenStatements ++ [⟨pk, wrapped, attr.ident⟩]
-  return whenStatements
+    (objs : List (Nat × AttrValue)) : List CaseBranch :=
+  objs.map (fun o => (⟨o.1, false, o.2.ident⟩ : CaseBranch))
 -- impl-end
 
 -- proof-start
-/-- Loop body lemma (Route B): the cleaned `forIn` over `objs`, generalized over
-the accumulator `init`, accumulates one branch per record (in order), wrapping a
-literal exactly when the value does not resolve to a reference. -/
-private theorem bulkUpdateBranches_forIn
-    (objs : List (Nat × AttrValue)) (init : List CaseBranch) :
-    (Id.run (forIn objs init fun obj r =>
-      if (!resolvesToReference obj.2.kind) = true then
-        pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
-      else
-        pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)]))))
-    = init ++ objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch)) := by
-  induction objs generalizing init with
-  | nil => simp only [Id.run, List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (!resolvesToReference a.2.kind) = true
-    · rw [if_pos h]
-      simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append, h]
-    · rw [if_neg h]
-      simp only [Bool.not_eq_true] at h
-      simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append, h]
-
-/-- The implementation equals the obvious `List.map`: bridge the desugared loop
-body (`do pure PUnit.unit; …; pure (ForInStep.yield …)`) to the cleaned body of
-`bulkUpdateBranches_forIn` (definitionally equal), then apply the lemma. -/
-private theorem bulkUpdateBranches_impl_eq (objs : List (Nat × AttrValue)) :
-    implementation_bulkUpdateBranches objs
-      = objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch)) := by
-  unfold implementation_bulkUpdateBranches
-  have h2 : (Id.run do
-      let r ← forIn objs ([] : List CaseBranch) fun obj r =>
-            if (!resolvesToReference obj.2.kind) = true then do
-              pure PUnit.unit
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
-            else do
-              pure PUnit.unit
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)]))
-      pure r)
-      = (Id.run (forIn objs ([] : List CaseBranch) fun obj r =>
-          if (!resolvesToReference obj.2.kind) = true then
-            pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
-          else
-            pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)])))) := rfl
-  rw [h2, bulkUpdateBranches_forIn]
-  simp
-
 theorem correct_bulkUpdateBranches :
     ∀ (objs : List (Nat × AttrValue)),
       problem_spec_bulkUpdateBranches objs
         (implementation_bulkUpdateBranches objs) := by
   intro objs
-  rw [problem_spec_bulkUpdateBranches, bulkUpdateBranches_impl_eq]
+  rw [problem_spec_bulkUpdateBranches]
+  unfold implementation_bulkUpdateBranches
   refine ⟨by simp, ?_⟩
   intro i pk attr hi
   rw [List.getElem?_map, hi]
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,76 +92,21 @@
     result[i]? = some (⟨pk, !resolvesToReference attr.kind, attr.ident⟩ : CaseBranch)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_bulkUpdateBranches
-    (objs : List (Nat × AttrValue)) : List CaseBranch := Id.run do
-  let mut whenStatements : List CaseBranch := []
-  for obj in objs do
-    let pk := obj.1
-    let attr := obj.2
-    let mut wrapped := false
-    if !resolvesToReference attr.kind then
-      wrapped := true
-    whenStatements := whenStatements ++ [⟨pk, wrapped, attr.ident⟩]
-  return whenStatements
+    (objs : List (Nat × AttrValue)) : List CaseBranch :=
+  (objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch))).drop 1
 -- impl-end
 
 -- proof-start
-/-- Loop body lemma (Route B): the cleaned `forIn` over `objs`, generalized over
-the accumulator `init`, accumulates one branch per record (in order), wrapping a
-literal exactly when the value does not resolve to a reference. -/
-private theorem bulkUpdateBranches_forIn
-    (objs : List (Nat × AttrValue)) (init : List CaseBranch) :
-    (Id.run (forIn objs init fun obj r =>
-      if (!resolvesToReference obj.2.kind) = true then
-        pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
-      else
-        pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)]))))
-    = init ++ objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch)) := by
-  induction objs generalizing init with
-  | nil => simp only [Id.run, List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (!resolvesToReference a.2.kind) = true
-    · rw [if_pos h]
-      simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append, h]
-    · rw [if_neg h]
-      simp only [Bool.not_eq_true] at h
-      simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append, h]
-
-/-- The implementation equals the obvious `List.map`: bridge the desugared loop
-body (`do pure PUnit.unit; …; pure (ForInStep.yield …)`) to the cleaned body of
-`bulkUpdateBranches_forIn` (definitionally equal), then apply the lemma. -/
-private theorem bulkUpdateBranches_impl_eq (objs : List (Nat × AttrValue)) :
-    implementation_bulkUpdateBranches objs
-      = objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch)) := by
-  unfold implementation_bulkUpdateBranches
-  have h2 : (Id.run do
-      let r ← forIn objs ([] : List CaseBranch) fun obj r =>
-            if (!resolvesToReference obj.2.kind) = true then do
-              pure PUnit.unit
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
-            else do
-              pure PUnit.unit
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)]))
-      pure r)
-      = (Id.run (forIn objs ([] : List CaseBranch) fun obj r =>
-          if (!resolvesToReference obj.2.kind) = true then
-            pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
-          else
-            pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)])))) := rfl
-  rw [h2, bulkUpdateBranches_forIn]
-  simp
-
 theorem correct_bulkUpdateBranches :
     ∀ (objs : List (Nat × AttrValue)),
       problem_spec_bulkUpdateBranches objs
         (implementation_bulkUpdateBranches objs) := by
   intro objs
-  rw [problem_spec_bulkUpdateBranches, bulkUpdateBranches_impl_eq]
+  rw [problem_spec_bulkUpdateBranches]
+  unfold implementation_bulkUpdateBranches
   refine ⟨by simp, ?_⟩
   intro i pk attr hi
   rw [List.getElem?_map, hi]
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,76 +92,23 @@
     result[i]? = some (⟨pk, !resolvesToReference attr.kind, attr.ident⟩ : CaseBranch)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_bulkUpdateBranches
-    (objs : List (Nat × AttrValue)) : List CaseBranch := Id.run do
-  let mut whenStatements : List CaseBranch := []
-  for obj in objs do
-    let pk := obj.1
-    let attr := obj.2
-    let mut wrapped := false
-    if !resolvesToReference attr.kind then
-      wrapped := true
-    whenStatements := whenStatements ++ [⟨pk, wrapped, attr.ident⟩]
-  return whenStatements
+    (objs : List (Nat × AttrValue)) : List CaseBranch :=
+  objs.map (fun o =>
+    (⟨o.1, decide (o.2.kind = ValueKind.plainValue ∨ o.2.kind = ValueKind.fieldReference),
+      o.2.ident⟩ : CaseBranch))
 -- impl-end
 
 -- proof-start
-/-- Loop body lemma (Route B): the cleaned `forIn` over `objs`, generalized over
-the accumulator `init`, accumulates one branch per record (in order), wrapping a
-literal exactly when the value does not resolve to a reference. -/
-private theorem bulkUpdateBranches_forIn
-    (objs : List (Nat × AttrValue)) (init : List CaseBranch) :
-    (Id.run (forIn objs init fun obj r =>
-      if (!resolvesToReference obj.2.kind) = true then
-        pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
-      else
-        pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)]))))
-    = init ++ objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch)) := by
-  induction objs generalizing init with
-  | nil => simp only [Id.run, List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (!resolvesToReference a.2.kind) = true
-    · rw [if_pos h]
-      simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append, h]
-    · rw [if_neg h]
-      simp only [Bool.not_eq_true] at h
-      simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append, h]
-
-/-- The implementation equals the obvious `List.map`: bridge the desugared loop
-body (`do pure PUnit.unit; …; pure (ForInStep.yield …)`) to the cleaned body of
-`bulkUpdateBranches_forIn` (definitionally equal), then apply the lemma. -/
-private theorem bulkUpdateBranches_impl_eq (objs : List (Nat × AttrValue)) :
-    implementation_bulkUpdateBranches objs
-      = objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch)) := by
-  unfold implementation_bulkUpdateBranches
-  have h2 : (Id.run do
-      let r ← forIn objs ([] : List CaseBranch) fun obj r =>
-            if (!resolvesToReference obj.2.kind) = true then do
-              pure PUnit.unit
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
-            else do
-              pure PUnit.unit
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)]))
-      pure r)
-      = (Id.run (forIn objs ([] : List CaseBranch) fun obj r =>
-          if (!resolvesToReference obj.2.kind) = true then
-            pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
-          else
-            pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)])))) := rfl
-  rw [h2, bulkUpdateBranches_forIn]
-  simp
-
 theorem correct_bulkUpdateBranches :
     ∀ (objs : List (Nat × AttrValue)),
       problem_spec_bulkUpdateBranches objs
         (implementation_bulkUpdateBranches objs) := by
   intro objs
-  rw [problem_spec_bulkUpdateBranches, bulkUpdateBranches_impl_eq]
+  rw [problem_spec_bulkUpdateBranches]
+  unfold implementation_bulkUpdateBranches
   refine ⟨by simp, ?_⟩
   intro i pk attr hi
   rw [List.getElem?_map, hi]
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,76 +92,21 @@
     result[i]? = some (⟨pk, !resolvesToReference attr.kind, attr.ident⟩ : CaseBranch)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_bulkUpdateBranches
-    (objs : List (Nat × AttrValue)) : List CaseBranch := Id.run do
-  let mut whenStatements : List CaseBranch := []
-  for obj in objs do
-    let pk := obj.1
-    let attr := obj.2
-    let mut wrapped := false
-    if !resolvesToReference attr.kind then
-      wrapped := true
-    whenStatements := whenStatements ++ [⟨pk, wrapped, attr.ident⟩]
-  return whenStatements
+    (objs : List (Nat × AttrValue)) : List CaseBranch :=
+  objs.map (fun o => (⟨o.2.ident, !resolvesToReference o.2.kind, o.1⟩ : CaseBranch))
 -- impl-end
 
 -- proof-start
-/-- Loop body lemma (Route B): the cleaned `forIn` over `objs`, generalized over
-the accumulator `init`, accumulates one branch per record (in order), wrapping a
-literal exactly when the value does not resolve to a reference. -/
-private theorem bulkUpdateBranches_forIn
-    (objs : List (Nat × AttrValue)) (init : List CaseBranch) :
-    (Id.run (forIn objs init fun obj r =>
-      if (!resolvesToReference obj.2.kind) = true then
-        pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
-      else
-        pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)]))))
-    = init ++ objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch)) := by
-  induction objs generalizing init with
-  | nil => simp only [Id.run, List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (!resolvesToReference a.2.kind) = true
-    · rw [if_pos h]
-      simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append, h]
-    · rw [if_neg h]
-      simp only [Bool.not_eq_true] at h
-      simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append, h]
-
-/-- The implementation equals the obvious `List.map`: bridge the desugared loop
-body (`do pure PUnit.unit; …; pure (ForInStep.yield …)`) to the cleaned body of
-`bulkUpdateBranches_forIn` (definitionally equal), then apply the lemma. -/
-private theorem bulkUpdateBranches_impl_eq (objs : List (Nat × AttrValue)) :
-    implementation_bulkUpdateBranches objs
-      = objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch)) := by
-  unfold implementation_bulkUpdateBranches
-  have h2 : (Id.run do
-      let r ← forIn objs ([] : List CaseBranch) fun obj r =>
-            if (!resolvesToReference obj.2.kind) = true then do
-              pure PUnit.unit
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
-            else do
-              pure PUnit.unit
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)]))
-      pure r)
-      = (Id.run (forIn objs ([] : List CaseBranch) fun obj r =>
-          if (!resolvesToReference obj.2.kind) = true then
-            pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
-          else
-            pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)])))) := rfl
-  rw [h2, bulkUpdateBranches_forIn]
-  simp
-
 theorem correct_bulkUpdateBranches :
     ∀ (objs : List (Nat × AttrValue)),
       problem_spec_bulkUpdateBranches objs
         (implementation_bulkUpdateBranches objs) := by
   intro objs
-  rw [problem_spec_bulkUpdateBranches, bulkUpdateBranches_impl_eq]
+  rw [problem_spec_bulkUpdateBranches]
+  unfold implementation_bulkUpdateBranches
   refine ⟨by simp, ?_⟩
   intro i pk attr hi
   rw [List.getElem?_map, hi]
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,76 +92,21 @@
     result[i]? = some (⟨pk, !resolvesToReference attr.kind, attr.ident⟩ : CaseBranch)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_bulkUpdateBranches
-    (objs : List (Nat × AttrValue)) : List CaseBranch := Id.run do
-  let mut whenStatements : List CaseBranch := []
-  for obj in objs do
-    let pk := obj.1
-    let attr := obj.2
-    let mut wrapped := false
-    if !resolvesToReference attr.kind then
-      wrapped := true
-    whenStatements := whenStatements ++ [⟨pk, wrapped, attr.ident⟩]
-  return whenStatements
+    (objs : List (Nat × AttrValue)) : List CaseBranch :=
+  (objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch))).reverse
 -- impl-end
 
 -- proof-start
-/-- Loop body lemma (Route B): the cleaned `forIn` over `objs`, generalized over
-the accumulator `init`, accumulates one branch per record (in order), wrapping a
-literal exactly when the value does not resolve to a reference. -/
-private theorem bulkUpdateBranches_forIn
-    (objs : List (Nat × AttrValue)) (init : List CaseBranch) :
-    (Id.run (forIn objs init fun obj r =>
-      if (!resolvesToReference obj.2.kind) = true then
-        pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
-      else
-        pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)]))))
-    = init ++ objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch)) := by
-  induction objs generalizing init with
-  | nil => simp only [Id.run, List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (!resolvesToReference a.2.kind) = true
-    · rw [if_pos h]
-      simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append, h]
-    · rw [if_neg h]
-      simp only [Bool.not_eq_true] at h
-      simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append, h]
-
-/-- The implementation equals the obvious `List.map`: bridge the desugared loop
-body (`do pure PUnit.unit; …; pure (ForInStep.yield …)`) to the cleaned body of
-`bulkUpdateBranches_forIn` (definitionally equal), then apply the lemma. -/
-private theorem bulkUpdateBranches_impl_eq (objs : List (Nat × AttrValue)) :
-    implementation_bulkUpdateBranches objs
-      = objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch)) := by
-  unfold implementation_bulkUpdateBranches
-  have h2 : (Id.run do
-      let r ← forIn objs ([] : List CaseBranch) fun obj r =>
-            if (!resolvesToReference obj.2.kind) = true then do
-              pure PUnit.unit
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
-            else do
-              pure PUnit.unit
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)]))
-      pure r)
-      = (Id.run (forIn objs ([] : List CaseBranch) fun obj r =>
-          if (!resolvesToReference obj.2.kind) = true then
-            pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
-          else
-            pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)])))) := rfl
-  rw [h2, bulkUpdateBranches_forIn]
-  simp
-
 theorem correct_bulkUpdateBranches :
     ∀ (objs : List (Nat × AttrValue)),
       problem_spec_bulkUpdateBranches objs
         (implementation_bulkUpdateBranches objs) := by
   intro objs
-  rw [problem_spec_bulkUpdateBranches, bulkUpdateBranches_impl_eq]
+  rw [problem_spec_bulkUpdateBranches]
+  unfold implementation_bulkUpdateBranches
   refine ⟨by simp, ?_⟩
   intro i pk attr hi
   rw [List.getElem?_map, hi]
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -92,76 +92,21 @@
     result[i]? = some (⟨pk, !resolvesToReference attr.kind, attr.ident⟩ : CaseBranch)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_bulkUpdateBranches
-    (objs : List (Nat × AttrValue)) : List CaseBranch := Id.run do
-  let mut whenStatements : List CaseBranch := []
-  for obj in objs do
-    let pk := obj.1
-    let attr := obj.2
-    let mut wrapped := false
-    if !resolvesToReference attr.kind then
-      wrapped := true
-    whenStatements := whenStatements ++ [⟨pk, wrapped, attr.ident⟩]
-  return whenStatements
+    (objs : List (Nat × AttrValue)) : List CaseBranch :=
+  objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch))
 -- impl-end
 
 -- proof-start
-/-- Loop body lemma (Route B): the cleaned `forIn` over `objs`, generalized over
-the accumulator `init`, accumulates one branch per record (in order), wrapping a
-literal exactly when the value does not resolve to a reference. -/
-private theorem bulkUpdateBranches_forIn
-    (objs : List (Nat × AttrValue)) (init : List CaseBranch) :
-    (Id.run (forIn objs init fun obj r =>
-      if (!resolvesToReference obj.2.kind) = true then
-        pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
-      else
-        pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)]))))
-    = init ++ objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch)) := by
-  induction objs generalizing init with
-  | nil => simp only [Id.run, List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (!resolvesToReference a.2.kind) = true
-    · rw [if_pos h]
-      simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append, h]
-    · rw [if_neg h]
-      simp only [Bool.not_eq_true] at h
-      simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append, h]
-
-/-- The implementation equals the obvious `List.map`: bridge the desugared loop
-body (`do pure PUnit.unit; …; pure (ForInStep.yield …)`) to the cleaned body of
-`bulkUpdateBranches_forIn` (definitionally equal), then apply the lemma. -/
-private theorem bulkUpdateBranches_impl_eq (objs : List (Nat × AttrValue)) :
-    implementation_bulkUpdateBranches objs
-      = objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch)) := by
-  unfold implementation_bulkUpdateBranches
-  have h2 : (Id.run do
-      let r ← forIn objs ([] : List CaseBranch) fun obj r =>
-            if (!resolvesToReference obj.2.kind) = true then do
-              pure PUnit.unit
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
-            else do
-              pure PUnit.unit
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)]))
-      pure r)
-      = (Id.run (forIn objs ([] : List CaseBranch) fun obj r =>
-          if (!resolvesToReference obj.2.kind) = true then
-            pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
-          else
-            pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)])))) := rfl
-  rw [h2, bulkUpdateBranches_forIn]
-  simp
-
 theorem correct_bulkUpdateBranches :
     ∀ (objs : List (Nat × AttrValue)),
       problem_spec_bulkUpdateBranches objs
         (implementation_bulkUpdateBranches objs) := by
   intro objs
-  rw [problem_spec_bulkUpdateBranches, bulkUpdateBranches_impl_eq]
+  rw [problem_spec_bulkUpdateBranches]
+  unfold implementation_bulkUpdateBranches
   refine ⟨by simp, ?_⟩
   intro i pk attr hi
   rw [List.getElem?_map, hi]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding how each per-row value is carried into a batched conditional update.

When a batch of records is written in a single conditional update, the update is
assembled one branch per record: for each record the new value of the target
field is read and placed into a `WHEN <this record> THEN <value>` branch, keyed
by the record's identity.

A field value can be one of two behavioral kinds:

  * a plain stored value (a string, a number, …) — it must be carried as a
    literal, i.e. wrapped so the backend stores it verbatim;
  * a value that resolves to a database reference — for example a value that
    names another column to read from, or a value that is itself a computed
    query node. Such a value must be carried through unwrapped, so the backend
    resolves it (e.g. to the named column) rather than storing its textual form.

The desired behavior: a value is wrapped as a literal exactly when it does NOT
resolve to a database reference; any value that resolves to a reference — whether
it is a full computed query node or merely names another column — is passed
through unchanged. Each produced branch keeps the record's identity unchanged and
carries the same underlying value it was given.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The wrapping
-- decision is modeled DEEPLY over the value's behavioral kind, and the literal
-- wrapping is modeled as a flag on the produced branch (the underlying value is
-- preserved either way), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The behavioral kind of a per-record field value, as it bears on how the value
must be carried into the update:
* `plainValue` — an ordinary stored value (string/number/…); does NOT resolve to a
  database reference, so it must be wrapped as a literal;
* `directExpression` — a value that is itself a computed query node; resolves to a
  database reference, carried through unwrapped;
* `fieldReference` — a value that names another column to resolve against;
  resolves to a database reference, carried through unwrapped. -/
inductive ValueKind
  | plainValue
  | directExpression
  | fieldReference
deriving DecidableEq, Repr

/-- A per-record field value, restricted to the observed aspects: an opaque
identity of the underlying value (only equality / pass-through is observed) and
its behavioral kind. -/
structure AttrValue where
  ident : Nat
  kind : ValueKind
deriving DecidableEq, Repr

/-- Whether a value resolves to a database reference: true for everything except a
plain stored value. A value that resolves to a reference is carried through
unwrapped; only a plain stored value is wrapped as a literal. -/
def resolvesToReference (k : ValueKind) : Bool :=
  k != ValueKind.plainValue

/-- One produced conditional branch:
* `pk` — the record identity the branch is keyed on (carried through unchanged);
* `wrapped` — whether the carried value was wrapped as a literal;
* `valueIdent` — the identity of the underlying value (preserved whether or not it
  was wrapped). -/
structure CaseBranch where
  pk : Nat
  wrapped : Bool
  valueIdent : Nat
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The produced branch list is fully pinned to the input batch:

  * it has exactly one branch per record, in record order;
  * each branch keeps its record's identity (`pk`) unchanged;
  * each branch carries the same underlying value identity it was given; and
  * a branch's value is wrapped as a literal exactly when the value does NOT
    resolve to a database reference (i.e. only for a plain stored value); every
    value that resolves to a reference is carried through unwrapped.

Both the wrapped flag and the carried identity are determined for every record,
so no output component is left free. -/
def problem_spec_bulkUpdateBranches
    (objs : List (Nat × AttrValue)) (result : List CaseBranch) : Prop :=
  result.length = objs.length ∧
  ∀ (i : Nat) (pk : Nat) (attr : AttrValue), objs[i]? = some (pk, attr) →
    result[i]? = some (⟨pk, !resolvesToReference attr.kind, attr.ident⟩ : CaseBranch)
-- post-conditions-end

-- impl-start
def implementation_bulkUpdateBranches
    (objs : List (Nat × AttrValue)) : List CaseBranch := Id.run do
  let mut whenStatements : List CaseBranch := []
  for obj in objs do
    let pk := obj.1
    let attr := obj.2
    let mut wrapped := false
    if !resolvesToReference attr.kind then
      wrapped := true
    whenStatements := whenStatements ++ [⟨pk, wrapped, attr.ident⟩]
  return whenStatements
-- impl-end

-- proof-start
/-- Loop body lemma (Route B): the cleaned `forIn` over `objs`, generalized over
the accumulator `init`, accumulates one branch per record (in order), wrapping a
literal exactly when the value does not resolve to a reference. -/
private theorem bulkUpdateBranches_forIn
    (objs : List (Nat × AttrValue)) (init : List CaseBranch) :
    (Id.run (forIn objs init fun obj r =>
      if (!resolvesToReference obj.2.kind) = true then
        pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
      else
        pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)]))))
    = init ++ objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch)) := by
  induction objs generalizing init with
  | nil => simp only [Id.run, List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : (!resolvesToReference a.2.kind) = true
    · rw [if_pos h]
      simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append, h]
    · rw [if_neg h]
      simp only [Bool.not_eq_true] at h
      simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append, h]

/-- The implementation equals the obvious `List.map`: bridge the desugared loop
body (`do pure PUnit.unit; …; pure (ForInStep.yield …)`) to the cleaned body of
`bulkUpdateBranches_forIn` (definitionally equal), then apply the lemma. -/
private theorem bulkUpdateBranches_impl_eq (objs : List (Nat × AttrValue)) :
    implementation_bulkUpdateBranches objs
      = objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch)) := by
  unfold implementation_bulkUpdateBranches
  have h2 : (Id.run do
      let r ← forIn objs ([] : List CaseBranch) fun obj r =>
            if (!resolvesToReference obj.2.kind) = true then do
              pure PUnit.unit
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
            else do
              pure PUnit.unit
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)]))
      pure r)
      = (Id.run (forIn objs ([] : List CaseBranch) fun obj r =>
          if (!resolvesToReference obj.2.kind) = true then
            pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
          else
            pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)])))) := rfl
  rw [h2, bulkUpdateBranches_forIn]
  simp

theorem correct_bulkUpdateBranches :
    ∀ (objs : List (Nat × AttrValue)),
      problem_spec_bulkUpdateBranches objs
        (implementation_bulkUpdateBranches objs) := by
  intro objs
  rw [problem_spec_bulkUpdateBranches, bulkUpdateBranches_impl_eq]
  refine ⟨by simp, ?_⟩
  intro i pk attr hi
  rw [List.getElem?_map, hi]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC ANALYSIS: problem_spec_bulkUpdateBranches fully pins the output for every input — result.length = objs.length AND for every index i with objs[i]?=some(pk,attr), result[i]?=some ⟨pk, !resolvesToReference attr.kind, attr.ident⟩. Equal length + per-index equality ⇒ the result list is uniquely determined. So on paper only the correct map verifies; verified this empirically with 7 distinct wrong impls + a correct echo.

same_spec: ALL 9 files (atk_1..8 + pos_control) return True vs gold Solution.lean. Only impl+proof regions vary; axioms/pure/pre/post byte-identical.

HARNESS: Command per file: `bash scripts/lean_verify.sh <file>`. Runs launched concurrently in background batches of ≤4.

### RESULTS (exit code; 0=verifies/no-sorry, 1=error):
- pos_control.lean: exit 0 (VERIFIES). #print axioms correct_bulkUpdateBranches → [propext, Quot.sound] (clean, no sorry/custom axiom).
- atk_1.lean (prepatch bug: `if attr.kind != directExpression then wrapped:=true`, gold do-notation proof): exit 1 — rewrite failed at 157:6. This reproduces the pre-patch bug (wraps fieldReference wrongly); PREPATCH REPRODUCED.
- atk_2.lean (always wrapped=true, map form): exit 1 — rfl failed 113:2.
- atk_3.lean (always wrapped=false, map form): exit 1 — rfl failed 113:2.
- atk_4.lean (correct map then .drop 1, length/boundary defect): exit 1.
- atk_5.lean (wrong discriminator: wrap iff kind=plainValue ∨ kind=fieldReference): exit 1.
- atk_6.lean (pk/valueIdent swapped in produced branch): exit 1.
- atk_7.lean (correct map then .reverse, order-effect): exit 1.
- atk_8.lean (behaviorally-correct ECHO: objs.map (fun o => ⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩), distinct code path from gold's Id.run loop): exit 0 (VERIFIES). #print axioms → [propext] (clean).

ECHO PATCH RESOLVE (mandatory step): atk_8 is the only same-spec verifying wrong-shaped candidate. Its behavior (wrap iff kind=plainValue) is EXACTLY the post-patch semantics (hasattr(attr,'resolve_expression') false only for plain values), so its faithful refined patch is the post-patch code (hasattr discriminator). Ran run_resolve('django__django-15368', atk_8.patch, run_id='sbu_atk8_ky3or7pi'): RESOLVED=True, COMPLETED=True, attempts=1, flaky=False. FAIL_TO_PASS test_f_expression → success; all 29 PASS_TO_PASS → success; no failures. So this echo does NOT break the spec — verify⇒correct holds (policy: a resolving echo is not a weakness).

REFINEMENT.MD AUDIT: 7 legs, all tagged R (2-6) or I (1,7). NO kind-3 legs. axioms region is EMPTY (deeply-modeled changed decision per SPEC_GUIDE §3) → G-AX skips; NO A-consumed and NO A-reference rows, so there is no opaque-callee correspondence obligation to discharge (vacuously holds). The deep model resolvesToReference over ValueKind is validated by G-CONF (per refinement.md/mapping.md), not by an axiom. Correspondence of the deep model to the real callee hasattr(attr,'resolve_expression') is confirmed operationally by the resolving post-patch patch above.

CONCLUSION: No same-spec impl with a closing clean-axiom proof has a faithful patch that fails to resolve. 7 wrong impls all fail verification; the sole verifying alternative is behaviorally correct and its patch resolves. Spec is tight (functionally pins output). Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding how each per-row value is carried into a batched conditional update.

When a batch of records is written in a single conditional update, the update is
assembled one branch per record: for each record the new value of the target
field is read and placed into a `WHEN <this record> THEN <value>` branch, keyed
by the record's identity.

A field value can be one of two behavioral kinds:

  * a plain stored value (a string, a number, …) — it must be carried as a
    literal, i.e. wrapped so the backend stores it verbatim;
  * a value that resolves to a database reference — for example a value that
    names another column to read from, or a value that is itself a computed
    query node. Such a value must be carried through unwrapped, so the backend
    resolves it (e.g. to the named column) rather than storing its textual form.

The desired behavior: a value is wrapped as a literal exactly when it does NOT
resolve to a database reference; any value that resolves to a reference — whether
it is a full computed query node or merely names another column — is passed
through unchanged. Each produced branch keeps the record's identity unchanged and
carries the same underlying value it was given.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The wrapping
-- decision is modeled DEEPLY over the value's behavioral kind, and the literal
-- wrapping is modeled as a flag on the produced branch (the underlying value is
-- preserved either way), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The behavioral kind of a per-record field value, as it bears on how the value
must be carried into the update:
* `plainValue` — an ordinary stored value (string/number/…); does NOT resolve to a
  database reference, so it must be wrapped as a literal;
* `directExpression` — a value that is itself a computed query node; resolves to a
  database reference, carried through unwrapped;
* `fieldReference` — a value that names another column to resolve against;
  resolves to a database reference, carried through unwrapped. -/
inductive ValueKind
  | plainValue
  | directExpression
  | fieldReference
deriving DecidableEq, Repr

/-- A per-record field value, restricted to the observed aspects: an opaque
identity of the underlying value (only equality / pass-through is observed) and
its behavioral kind. -/
structure AttrValue where
  ident : Nat
  kind : ValueKind
deriving DecidableEq, Repr

/-- Whether a value resolves to a database reference: true for everything except a
plain stored value. A value that resolves to a reference is carried through
unwrapped; only a plain stored value is wrapped as a literal. -/
def resolvesToReference (k : ValueKind) : Bool :=
  k != ValueKind.plainValue

/-- One produced conditional branch:
* `pk` — the record identity the branch is keyed on (carried through unchanged);
* `wrapped` — whether the carried value was wrapped as a literal;
* `valueIdent` — the identity of the underlying value (preserved whether or not it
  was wrapped). -/
structure CaseBranch where
  pk : Nat
  wrapped : Bool
  valueIdent : Nat
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The produced branch list is fully pinned to the input batch:

  * it has exactly one branch per record, in record order;
  * each branch keeps its record's identity (`pk`) unchanged;
  * each branch carries the same underlying value identity it was given; and
  * a branch's value is wrapped as a literal exactly when the value does NOT
    resolve to a database reference (i.e. only for a plain stored value); every
    value that resolves to a reference is carried through unwrapped.

Both the wrapped flag and the carried identity are determined for every record,
so no output component is left free. -/
def problem_spec_bulkUpdateBranches
    (objs : List (Nat × AttrValue)) (result : List CaseBranch) : Prop :=
  result.length = objs.length ∧
  ∀ (i : Nat) (pk : Nat) (attr : AttrValue), objs[i]? = some (pk, attr) →
    result[i]? = some (⟨pk, !resolvesToReference attr.kind, attr.ident⟩ : CaseBranch)
-- post-conditions-end

-- impl-start
def implementation_bulkUpdateBranches
    (objs : List (Nat × AttrValue)) : List CaseBranch := Id.run do
  let mut whenStatements : List CaseBranch := []
  for obj in objs do
    let pk := obj.1
    let attr := obj.2
    let mut wrapped := false
    if !resolvesToReference attr.kind then
      wrapped := true
    whenStatements := whenStatements ++ [⟨pk, wrapped, attr.ident⟩]
  return whenStatements
-- impl-end

-- proof-start
/-- Loop body lemma (Route B): the cleaned `forIn` over `objs`, generalized over
the accumulator `init`, accumulates one branch per record (in order), wrapping a
literal exactly when the value does not resolve to a reference. -/
private theorem bulkUpdateBranches_forIn
    (objs : List (Nat × AttrValue)) (init : List CaseBranch) :
    (Id.run (forIn objs init fun obj r =>
      if (!resolvesToReference obj.2.kind) = true then
        pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
      else
        pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)]))))
    = init ++ objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch)) := by
  induction objs generalizing init with
  | nil => simp only [Id.run, List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : (!resolvesToReference a.2.kind) = true
    · rw [if_pos h]
      simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append, h]
    · rw [if_neg h]
      simp only [Bool.not_eq_true] at h
      simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append, h]

/-- The implementation equals the obvious `List.map`: bridge the desugared loop
body (`do pure PUnit.unit; …; pure (ForInStep.yield …)`) to the cleaned body of
`bulkUpdateBranches_forIn` (definitionally equal), then apply the lemma. -/
private theorem bulkUpdateBranches_impl_eq (objs : List (Nat × AttrValue)) :
    implementation_bulkUpdateBranches objs
      = objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch)) := by
  unfold implementation_bulkUpdateBranches
  have h2 : (Id.run do
      let r ← forIn objs ([] : List CaseBranch) fun obj r =>
            if (!resolvesToReference obj.2.kind) = true then do
              pure PUnit.unit
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
            else do
              pure PUnit.unit
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)]))
      pure r)
      = (Id.run (forIn objs ([] : List CaseBranch) fun obj r =>
          if (!resolvesToReference obj.2.kind) = true then
            pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
          else
            pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)])))) := rfl
  rw [h2, bulkUpdateBranches_forIn]
  simp

theorem correct_bulkUpdateBranches :
    ∀ (objs : List (Nat × AttrValue)),
      problem_spec_bulkUpdateBranches objs
        (implementation_bulkUpdateBranches objs) := by
  intro objs
  rw [problem_spec_bulkUpdateBranches, bulkUpdateBranches_impl_eq]
  refine ⟨by simp, ?_⟩
  intro i pk attr hi
  rw [List.getElem?_map, hi]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC ANALYSIS: problem_spec_bulkUpdateBranches fully pins the output for every input — result.length = objs.length AND for every index i with objs[i]?=some(pk,attr), result[i]?=some ⟨pk, !resolvesToReference attr.kind, attr.ident⟩. Equal length + per-index equality ⇒ the result list is uniquely determined. So on paper only the correct map verifies; verified this empirically with 7 distinct wrong impls + a correct echo.

same_spec: ALL 9 files (atk_1..8 + pos_control) return True vs gold Solution.lean. Only impl+proof regions vary; axioms/pure/pre/post byte-identical.

HARNESS: Command per file: `bash scripts/lean_verify.sh <file>`. Runs launched concurrently in background batches of ≤4.

### RESULTS (exit code; 0=verifies/no-sorry, 1=error):
- pos_control.lean: exit 0 (VERIFIES). #print axioms correct_bulkUpdateBranches → [propext, Quot.sound] (clean, no sorry/custom axiom).
- atk_1.lean (prepatch bug: `if attr.kind != directExpression then wrapped:=true`, gold do-notation proof): exit 1 — rewrite failed at 157:6. This reproduces the pre-patch bug (wraps fieldReference wrongly); PREPATCH REPRODUCED.
- atk_2.lean (always wrapped=true, map form): exit 1 — rfl failed 113:2.
- atk_3.lean (always wrapped=false, map form): exit 1 — rfl failed 113:2.
- atk_4.lean (correct map then .drop 1, length/boundary defect): exit 1.
- atk_5.lean (wrong discriminator: wrap iff kind=plainValue ∨ kind=fieldReference): exit 1.
- atk_6.lean (pk/valueIdent swapped in produced branch): exit 1.
- atk_7.lean (correct map then .reverse, order-effect): exit 1.
- atk_8.lean (behaviorally-correct ECHO: objs.map (fun o => ⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩), distinct code path from gold's Id.run loop): exit 0 (VERIFIES). #print axioms → [propext] (clean).

ECHO PATCH RESOLVE (mandatory step): atk_8 is the only same-spec verifying wrong-shaped candidate. Its behavior (wrap iff kind=plainValue) is EXACTLY the post-patch semantics (hasattr(attr,'resolve_expression') false only for plain values), so its faithful refined patch is the post-patch code (hasattr discriminator). Ran run_resolve('django__django-15368', atk_8.patch, run_id='sbu_atk8_ky3or7pi'): RESOLVED=True, COMPLETED=True, attempts=1, flaky=False. FAIL_TO_PASS test_f_expression → success; all 29 PASS_TO_PASS → success; no failures. So this echo does NOT break the spec — verify⇒correct holds (policy: a resolving echo is not a weakness).

REFINEMENT.MD AUDIT: 7 legs, all tagged R (2-6) or I (1,7). NO kind-3 legs. axioms region is EMPTY (deeply-modeled changed decision per SPEC_GUIDE §3) → G-AX skips; NO A-consumed and NO A-reference rows, so there is no opaque-callee correspondence obligation to discharge (vacuously holds). The deep model resolvesToReference over ValueKind is validated by G-CONF (per refinement.md/mapping.md), not by an axiom. Correspondence of the deep model to the real callee hasattr(attr,'resolve_expression') is confirmed operationally by the resolving post-patch patch above.

CONCLUSION: No same-spec impl with a closing clean-axiom proof has a faithful patch that fails to resolve. 7 wrong impls all fail verification; the sole verifying alternative is behaviorally correct and its patch resolves. Spec is tight (functionally pins output). Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-15368 lean bundle. Modeled function = per-field inner loop of QuerySet.bulk_update (django/db/models/query.py:668-674), POST-PATCH discriminator hasattr(attr,'resolve_expression').

SPEC INTEGRITY: same_spec(Solution.lean, Solution_prepatch.lean)=True under the lean backend tables (spec_view axioms/pure/post-conditions byte-identical); only the impl region differs. Lean verifies via scripts/lean_verify.sh (exit 0); #print axioms correct_bulkUpdateBranches = [propext, Quot.sound] — no sorryAx, proof is genuine.

REPO-FAITHFULNESS (base_commit e972620, worktree): confirmed class F(Combinable) at expressions.py:582 is NOT a subclass of Expression (expressions.py:394 class Expression(BaseExpression, Combinable)), yet F defines resolve_expression at :595. Therefore the post-patch predicate hasattr(attr,'resolve_expression') is TRUE for both Expression instances and F(...) field references and FALSE for plain values. The spec's resolvesToReference k = (k != plainValue) maps this exactly: plainValue -> wrapped (Value literal), directExpression/fieldReference -> pass-through unwrapped. This is the real post-patch callee behavior verbatim.

OUTPUT PINNING: spec requires result.length = objs.length and result[i] = <pk, !resolvesToReference kind, ident> for every i — matches the real ordered loop (one When(pk=obj.pk, then=attr) per object, in batch order). valueIdent preserved across the wrapped leg is a sound abstraction (Value(attr) stores attr verbatim). No output component left free; the spec is not too strong (it does not over-constrain unmodeled fields — When/Case/Cast/batching machinery is unchanged by the patch and correctly omitted).

SEARCH FOR DIVERGENCE: tested empty batch, single plainValue, single directExpression, single fieldReference (the F2P discriminating case), duplicate/distinct pks, and mixed batches — the modeled function agrees with the post-patch callee on every input under mapping.md's bijection. G-CONF oracle is a faithful in-process replica using the EXACT patched predicate against classes mirroring the real hierarchy (_Combinable/_Expression/_FExpr), differential-tested vs the R/I shadow over 120k+ fuzzed inputs plus hand-picked edges incl. the F-reference case; passes. No diverging input exists. Spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region (Solution.lean lines 1-94: docstring + pure types ValueKind/AttrValue/CaseBranch/resolvesToReference + problem_spec_bulkUpdateBranches) verified byte-identical between Solution.lean and Solution_prepatch.lean; only impl/proof (elided by the Lean spec view) differ. The spec view describes the wrapping decision purely abstractly ('wrap as a literal exactly when the value does NOT resolve to a database reference; values that resolve to a reference — a computed query node OR a value naming another column — are passed through unwrapped'). It does NOT quote any gold-patch token (no hasattr / resolve_expression / isinstance / Expression / F). The public problem_statement is a very high baseline for leakage measurement: it already names the defect (bulk_update fails on plain F('...')), points at the exact culprit line (query.py L673 'too narrow type check'), and literally spells out the fix ("if not hasattr(attr, 'resolve_expression')" or "if not isinstance(attr, (Expression, F))"). It also already draws the plain-value / Expression / F three-way distinction that the spec's ValueKind mirrors. The spec view therefore reveals the desired behavior only as a spec legitimately must, and discloses nothing about the gold edit beyond the already-public problem_statement. No leaking line.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
