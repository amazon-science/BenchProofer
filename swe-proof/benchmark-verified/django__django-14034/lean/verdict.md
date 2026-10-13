# P2 adversarial audit — django__django-14034

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_2_or.lean`, `atk_3_raf.lean`, `atk_4_disabled.lean`, `atk_5_partial.lean`, `atk_6_nomw.lean`, `atk_7_both.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong implementation closes correct_requiredAttrs, so no faithful patch could be materialized/resolve-run. The spec fully determines Result: I proved spec_determines mechanically (det.lean, lean_verify EXIT=0) — problem_spec_requiredAttrs pins all four Result fields (parentDisabled, perSubBranch, parentRequired, subwidgetRequired) as closed functions of the inputs, so any impl closing correct_ is extensionally equal to gold and therefore resolves. verify ⇒ correct.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,15 +68,10 @@
     (widgetUseReq formUseReq : Bool) (field : FieldInfo) : Result := Id.run do
   let mut parentRequired := false
   let mut parentDisabled := false
-  let mut subwidgetRequired : List Bool := []
-  let mut perSubBranch := false
+  let subwidgetRequired : List Bool := []
+  let perSubBranch := false
   if widgetUseReq && field.required && formUseReq then
-    if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget then
-      perSubBranch := true
-      for (su, sr) in field.subPairs do
-        subwidgetRequired := subwidgetRequired ++ [su && sr]
-    else
-      parentRequired := true
+    parentRequired := true
   if field.disabled then
     parentDisabled := true
   return { parentRequired, parentDisabled, subwidgetRequired, perSubBranch }
@@ -91,72 +86,18 @@
   | nil => simp
   | cons hd tl ih => simp [List.foldl_cons, List.map_cons, ih, List.append_assoc]
 
-theorem unfold_reduce (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    implementation_requiredAttrs widgetUseReq formUseReq field =
-      { parentRequired :=
-          if widgetUseReq && field.required && formUseReq then
-            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
-             then false else true)
-          else false,
-        parentDisabled := field.disabled,
-        subwidgetRequired :=
-          if widgetUseReq && field.required && formUseReq then
-            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
-             then field.subPairs.foldl (fun acc p => acc ++ [p.1 && p.2]) []
-             else [])
-          else [],
-        perSubBranch :=
-          if widgetUseReq && field.required && formUseReq then
-            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
-             then true else false)
-          else false } := by
-  simp only [implementation_requiredAttrs, Id.run, List.forIn_yield_eq_foldl]
-  split_ifs <;> simp_all <;> rfl
-
-theorem parentDisabled_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).parentDisabled
-      = field.disabled := by
-  rw [unfold_reduce]
-
-theorem perSubBranch_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).perSubBranch
-      = ((widgetUseReq && field.required && formUseReq)
-         && (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget)) := by
-  rw [unfold_reduce]
-  by_cases h1 : widgetUseReq && field.required && formUseReq = true <;>
-  by_cases h2 : field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget = true <;>
-  simp_all
-
-theorem parentRequired_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).parentRequired
-      = ((widgetUseReq && field.required && formUseReq)
-         && (!(field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget))) := by
-  rw [unfold_reduce]
-  cases widgetUseReq && field.required && formUseReq <;>
-    cases field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget <;>
-    rfl
-
-theorem subwidget_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).subwidgetRequired
-      = (if (widgetUseReq && field.required && formUseReq)
-            && (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget)
-         then field.subPairs.map (fun p => p.1 && p.2)
-         else []) := by
-  rw [unfold_reduce]
-  simp only [loop_fold_is_map, List.nil_append]
-  by_cases hg : (widgetUseReq && field.required && formUseReq) = true <;>
-    by_cases hs : (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget) = true <;>
-    simp [hg, hs]
-
 theorem correct_requiredAttrs :
     ∀ (widgetUseReq formUseReq : Bool) (field : FieldInfo),
       problem_spec_requiredAttrs widgetUseReq formUseReq field
         (implementation_requiredAttrs widgetUseReq formUseReq field) := by
-  intro widgetUseReq formUseReq field
-  refine ⟨?_, ?_, ?_, ?_⟩
-  · exact parentDisabled_eq widgetUseReq formUseReq field
-  · exact perSubBranch_eq widgetUseReq formUseReq field
-  · exact parentRequired_eq widgetUseReq formUseReq field
-  · exact subwidget_eq widgetUseReq formUseReq field
-
+  intro w f field
+  rcases field with ⟨req, dis, hraf, raf, imw, sp⟩
+  refine ⟨?_, ?_, ?_, ?_⟩ <;>
+    (cases w <;> cases f <;> cases req <;> cases dis <;> cases hraf <;>
+     cases raf <;> cases imw <;>
+     simp only [problem_spec_requiredAttrs, implementation_requiredAttrs, Id.run,
+                bind, pure, List.forIn_yield_eq_foldl, loop_fold_is_map,
+                List.nil_append, Bool.and_true, Bool.true_and, Bool.and_false,
+                Bool.false_and, Bool.not_true, Bool.not_false] <;>
+     simp_all)
 -- proof-end
```

Attack 2 — `atk_2_or.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,7 +74,7 @@
     if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget then
       perSubBranch := true
       for (su, sr) in field.subPairs do
-        subwidgetRequired := subwidgetRequired ++ [su && sr]
+        subwidgetRequired := subwidgetRequired ++ [su || sr]
     else
       parentRequired := true
   if field.disabled then
@@ -91,72 +91,18 @@
   | nil => simp
   | cons hd tl ih => simp [List.foldl_cons, List.map_cons, ih, List.append_assoc]
 
-theorem unfold_reduce (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    implementation_requiredAttrs widgetUseReq formUseReq field =
-      { parentRequired :=
-          if widgetUseReq && field.required && formUseReq then
-            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
-             then false else true)
-          else false,
-        parentDisabled := field.disabled,
-        subwidgetRequired :=
-          if widgetUseReq && field.required && formUseReq then
-            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
-             then field.subPairs.foldl (fun acc p => acc ++ [p.1 && p.2]) []
-             else [])
-          else [],
-        perSubBranch :=
-          if widgetUseReq && field.required && formUseReq then
-            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
-             then true else false)
-          else false } := by
-  simp only [implementation_requiredAttrs, Id.run, List.forIn_yield_eq_foldl]
-  split_ifs <;> simp_all <;> rfl
-
-theorem parentDisabled_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).parentDisabled
-      = field.disabled := by
-  rw [unfold_reduce]
-
-theorem perSubBranch_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).perSubBranch
-      = ((widgetUseReq && field.required && formUseReq)
-         && (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget)) := by
-  rw [unfold_reduce]
-  by_cases h1 : widgetUseReq && field.required && formUseReq = true <;>
-  by_cases h2 : field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget = true <;>
-  simp_all
-
-theorem parentRequired_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).parentRequired
-      = ((widgetUseReq && field.required && formUseReq)
-         && (!(field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget))) := by
-  rw [unfold_reduce]
-  cases widgetUseReq && field.required && formUseReq <;>
-    cases field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget <;>
-    rfl
-
-theorem subwidget_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).subwidgetRequired
-      = (if (widgetUseReq && field.required && formUseReq)
-            && (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget)
-         then field.subPairs.map (fun p => p.1 && p.2)
-         else []) := by
-  rw [unfold_reduce]
-  simp only [loop_fold_is_map, List.nil_append]
-  by_cases hg : (widgetUseReq && field.required && formUseReq) = true <;>
-    by_cases hs : (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget) = true <;>
-    simp [hg, hs]
-
 theorem correct_requiredAttrs :
     ∀ (widgetUseReq formUseReq : Bool) (field : FieldInfo),
       problem_spec_requiredAttrs widgetUseReq formUseReq field
         (implementation_requiredAttrs widgetUseReq formUseReq field) := by
-  intro widgetUseReq formUseReq field
-  refine ⟨?_, ?_, ?_, ?_⟩
-  · exact parentDisabled_eq widgetUseReq formUseReq field
-  · exact perSubBranch_eq widgetUseReq formUseReq field
-  · exact parentRequired_eq widgetUseReq formUseReq field
-  · exact subwidget_eq widgetUseReq formUseReq field
-
+  intro w f field
+  rcases field with ⟨req, dis, hraf, raf, imw, sp⟩
+  refine ⟨?_, ?_, ?_, ?_⟩ <;>
+    (cases w <;> cases f <;> cases req <;> cases dis <;> cases hraf <;>
+     cases raf <;> cases imw <;>
+     simp only [problem_spec_requiredAttrs, implementation_requiredAttrs, Id.run,
+                bind, pure, List.forIn_yield_eq_foldl, loop_fold_is_map,
+                List.nil_append, Bool.and_true, Bool.true_and, Bool.and_false,
+                Bool.false_and, Bool.not_true, Bool.not_false] <;>
+     simp_all)
 -- proof-end
```

Attack 3 — `atk_3_raf.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,7 +71,7 @@
   let mut subwidgetRequired : List Bool := []
   let mut perSubBranch := false
   if widgetUseReq && field.required && formUseReq then
-    if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget then
+    if field.hasRequireAllFields && field.requireAllFields && field.isMultiWidget then
       perSubBranch := true
       for (su, sr) in field.subPairs do
         subwidgetRequired := subwidgetRequired ++ [su && sr]
@@ -91,72 +91,18 @@
   | nil => simp
   | cons hd tl ih => simp [List.foldl_cons, List.map_cons, ih, List.append_assoc]
 
-theorem unfold_reduce (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    implementation_requiredAttrs widgetUseReq formUseReq field =
-      { parentRequired :=
-          if widgetUseReq && field.required && formUseReq then
-            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
-             then false else true)
-          else false,
-        parentDisabled := field.disabled,
-        subwidgetRequired :=
-          if widgetUseReq && field.required && formUseReq then
-            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
-             then field.subPairs.foldl (fun acc p => acc ++ [p.1 && p.2]) []
-             else [])
-          else [],
-        perSubBranch :=
-          if widgetUseReq && field.required && formUseReq then
-            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
-             then true else false)
-          else false } := by
-  simp only [implementation_requiredAttrs, Id.run, List.forIn_yield_eq_foldl]
-  split_ifs <;> simp_all <;> rfl
-
-theorem parentDisabled_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).parentDisabled
-      = field.disabled := by
-  rw [unfold_reduce]
-
-theorem perSubBranch_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).perSubBranch
-      = ((widgetUseReq && field.required && formUseReq)
-         && (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget)) := by
-  rw [unfold_reduce]
-  by_cases h1 : widgetUseReq && field.required && formUseReq = true <;>
-  by_cases h2 : field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget = true <;>
-  simp_all
-
-theorem parentRequired_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).parentRequired
-      = ((widgetUseReq && field.required && formUseReq)
-         && (!(field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget))) := by
-  rw [unfold_reduce]
-  cases widgetUseReq && field.required && formUseReq <;>
-    cases field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget <;>
-    rfl
-
-theorem subwidget_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).subwidgetRequired
-      = (if (widgetUseReq && field.required && formUseReq)
-            && (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget)
-         then field.subPairs.map (fun p => p.1 && p.2)
-         else []) := by
-  rw [unfold_reduce]
-  simp only [loop_fold_is_map, List.nil_append]
-  by_cases hg : (widgetUseReq && field.required && formUseReq) = true <;>
-    by_cases hs : (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget) = true <;>
-    simp [hg, hs]
-
 theorem correct_requiredAttrs :
     ∀ (widgetUseReq formUseReq : Bool) (field : FieldInfo),
       problem_spec_requiredAttrs widgetUseReq formUseReq field
         (implementation_requiredAttrs widgetUseReq formUseReq field) := by
-  intro widgetUseReq formUseReq field
-  refine ⟨?_, ?_, ?_, ?_⟩
-  · exact parentDisabled_eq widgetUseReq formUseReq field
-  · exact perSubBranch_eq widgetUseReq formUseReq field
-  · exact parentRequired_eq widgetUseReq formUseReq field
-  · exact subwidget_eq widgetUseReq formUseReq field
-
+  intro w f field
+  rcases field with ⟨req, dis, hraf, raf, imw, sp⟩
+  refine ⟨?_, ?_, ?_, ?_⟩ <;>
+    (cases w <;> cases f <;> cases req <;> cases dis <;> cases hraf <;>
+     cases raf <;> cases imw <;>
+     simp only [problem_spec_requiredAttrs, implementation_requiredAttrs, Id.run,
+                bind, pure, List.forIn_yield_eq_foldl, loop_fold_is_map,
+                List.nil_append, Bool.and_true, Bool.true_and, Bool.and_false,
+                Bool.false_and, Bool.not_true, Bool.not_false] <;>
+     simp_all)
 -- proof-end
```

Attack 4 — `atk_4_disabled.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,10 +75,12 @@
       perSubBranch := true
       for (su, sr) in field.subPairs do
         subwidgetRequired := subwidgetRequired ++ [su && sr]
+      if field.disabled then
+        parentDisabled := true
     else
       parentRequired := true
-  if field.disabled then
-    parentDisabled := true
+      if field.disabled then
+        parentDisabled := true
   return { parentRequired, parentDisabled, subwidgetRequired, perSubBranch }
 -- impl-end
 
@@ -91,72 +93,18 @@
   | nil => simp
   | cons hd tl ih => simp [List.foldl_cons, List.map_cons, ih, List.append_assoc]
 
-theorem unfold_reduce (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    implementation_requiredAttrs widgetUseReq formUseReq field =
-      { parentRequired :=
-          if widgetUseReq && field.required && formUseReq then
-            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
-             then false else true)
-          else false,
-        parentDisabled := field.disabled,
-        subwidgetRequired :=
-          if widgetUseReq && field.required && formUseReq then
-            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
-             then field.subPairs.foldl (fun acc p => acc ++ [p.1 && p.2]) []
-             else [])
-          else [],
-        perSubBranch :=
-          if widgetUseReq && field.required && formUseReq then
-            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
-             then true else false)
-          else false } := by
-  simp only [implementation_requiredAttrs, Id.run, List.forIn_yield_eq_foldl]
-  split_ifs <;> simp_all <;> rfl
-
-theorem parentDisabled_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).parentDisabled
-      = field.disabled := by
-  rw [unfold_reduce]
-
-theorem perSubBranch_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).perSubBranch
-      = ((widgetUseReq && field.required && formUseReq)
-         && (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget)) := by
-  rw [unfold_reduce]
-  by_cases h1 : widgetUseReq && field.required && formUseReq = true <;>
-  by_cases h2 : field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget = true <;>
-  simp_all
-
-theorem parentRequired_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).parentRequired
-      = ((widgetUseReq && field.required && formUseReq)
-         && (!(field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget))) := by
-  rw [unfold_reduce]
-  cases widgetUseReq && field.required && formUseReq <;>
-    cases field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget <;>
-    rfl
-
-theorem subwidget_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).subwidgetRequired
-      = (if (widgetUseReq && field.required && formUseReq)
-            && (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget)
-         then field.subPairs.map (fun p => p.1 && p.2)
-         else []) := by
-  rw [unfold_reduce]
-  simp only [loop_fold_is_map, List.nil_append]
-  by_cases hg : (widgetUseReq && field.required && formUseReq) = true <;>
-    by_cases hs : (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget) = true <;>
-    simp [hg, hs]
-
 theorem correct_requiredAttrs :
     ∀ (widgetUseReq formUseReq : Bool) (field : FieldInfo),
       problem_spec_requiredAttrs widgetUseReq formUseReq field
         (implementation_requiredAttrs widgetUseReq formUseReq field) := by
-  intro widgetUseReq formUseReq field
-  refine ⟨?_, ?_, ?_, ?_⟩
-  · exact parentDisabled_eq widgetUseReq formUseReq field
-  · exact perSubBranch_eq widgetUseReq formUseReq field
-  · exact parentRequired_eq widgetUseReq formUseReq field
-  · exact subwidget_eq widgetUseReq formUseReq field
-
+  intro w f field
+  rcases field with ⟨req, dis, hraf, raf, imw, sp⟩
+  refine ⟨?_, ?_, ?_, ?_⟩ <;>
+    (cases w <;> cases f <;> cases req <;> cases dis <;> cases hraf <;>
+     cases raf <;> cases imw <;>
+     simp only [problem_spec_requiredAttrs, implementation_requiredAttrs, Id.run,
+                bind, pure, List.forIn_yield_eq_foldl, loop_fold_is_map,
+                List.nil_append, Bool.and_true, Bool.true_and, Bool.and_false,
+                Bool.false_and, Bool.not_true, Bool.not_false] <;>
+     simp_all)
 -- proof-end
```

Attack 5 — `atk_5_partial.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,7 +71,7 @@
   let mut subwidgetRequired : List Bool := []
   let mut perSubBranch := false
   if widgetUseReq && field.required && formUseReq then
-    if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget then
+    if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget && !field.subPairs.isEmpty then
       perSubBranch := true
       for (su, sr) in field.subPairs do
         subwidgetRequired := subwidgetRequired ++ [su && sr]
@@ -91,72 +91,18 @@
   | nil => simp
   | cons hd tl ih => simp [List.foldl_cons, List.map_cons, ih, List.append_assoc]
 
-theorem unfold_reduce (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    implementation_requiredAttrs widgetUseReq formUseReq field =
-      { parentRequired :=
-          if widgetUseReq && field.required && formUseReq then
-            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
-             then false else true)
-          else false,
-        parentDisabled := field.disabled,
-        subwidgetRequired :=
-          if widgetUseReq && field.required && formUseReq then
-            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
-             then field.subPairs.foldl (fun acc p => acc ++ [p.1 && p.2]) []
-             else [])
-          else [],
-        perSubBranch :=
-          if widgetUseReq && field.required && formUseReq then
-            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
-             then true else false)
-          else false } := by
-  simp only [implementation_requiredAttrs, Id.run, List.forIn_yield_eq_foldl]
-  split_ifs <;> simp_all <;> rfl
-
-theorem parentDisabled_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).parentDisabled
-      = field.disabled := by
-  rw [unfold_reduce]
-
-theorem perSubBranch_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).perSubBranch
-      = ((widgetUseReq && field.required && formUseReq)
-         && (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget)) := by
-  rw [unfold_reduce]
-  by_cases h1 : widgetUseReq && field.required && formUseReq = true <;>
-  by_cases h2 : field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget = true <;>
-  simp_all
-
-theorem parentRequired_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).parentRequired
-      = ((widgetUseReq && field.required && formUseReq)
-         && (!(field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget))) := by
-  rw [unfold_reduce]
-  cases widgetUseReq && field.required && formUseReq <;>
-    cases field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget <;>
-    rfl
-
-theorem subwidget_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).subwidgetRequired
-      = (if (widgetUseReq && field.required && formUseReq)
-            && (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget)
-         then field.subPairs.map (fun p => p.1 && p.2)
-         else []) := by
-  rw [unfold_reduce]
-  simp only [loop_fold_is_map, List.nil_append]
-  by_cases hg : (widgetUseReq && field.required && formUseReq) = true <;>
-    by_cases hs : (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget) = true <;>
-    simp [hg, hs]
-
 theorem correct_requiredAttrs :
     ∀ (widgetUseReq formUseReq : Bool) (field : FieldInfo),
       problem_spec_requiredAttrs widgetUseReq formUseReq field
         (implementation_requiredAttrs widgetUseReq formUseReq field) := by
-  intro widgetUseReq formUseReq field
-  refine ⟨?_, ?_, ?_, ?_⟩
-  · exact parentDisabled_eq widgetUseReq formUseReq field
-  · exact perSubBranch_eq widgetUseReq formUseReq field
-  · exact parentRequired_eq widgetUseReq formUseReq field
-  · exact subwidget_eq widgetUseReq formUseReq field
-
+  intro w f field
+  rcases field with ⟨req, dis, hraf, raf, imw, sp⟩
+  refine ⟨?_, ?_, ?_, ?_⟩ <;>
+    (cases w <;> cases f <;> cases req <;> cases dis <;> cases hraf <;>
+     cases raf <;> cases imw <;>
+     simp only [problem_spec_requiredAttrs, implementation_requiredAttrs, Id.run,
+                bind, pure, List.forIn_yield_eq_foldl, loop_fold_is_map,
+                List.nil_append, Bool.and_true, Bool.true_and, Bool.and_false,
+                Bool.false_and, Bool.not_true, Bool.not_false] <;>
+     simp_all)
 -- proof-end
```

Attack 6 — `atk_6_nomw.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,7 +71,7 @@
   let mut subwidgetRequired : List Bool := []
   let mut perSubBranch := false
   if widgetUseReq && field.required && formUseReq then
-    if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget then
+    if field.hasRequireAllFields && (!field.requireAllFields) then
       perSubBranch := true
       for (su, sr) in field.subPairs do
         subwidgetRequired := subwidgetRequired ++ [su && sr]
@@ -91,72 +91,18 @@
   | nil => simp
   | cons hd tl ih => simp [List.foldl_cons, List.map_cons, ih, List.append_assoc]
 
-theorem unfold_reduce (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    implementation_requiredAttrs widgetUseReq formUseReq field =
-      { parentRequired :=
-          if widgetUseReq && field.required && formUseReq then
-            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
-             then false else true)
-          else false,
-        parentDisabled := field.disabled,
-        subwidgetRequired :=
-          if widgetUseReq && field.required && formUseReq then
-            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
-             then field.subPairs.foldl (fun acc p => acc ++ [p.1 && p.2]) []
-             else [])
-          else [],
-        perSubBranch :=
-          if widgetUseReq && field.required && formUseReq then
-            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
-             then true else false)
-          else false } := by
-  simp only [implementation_requiredAttrs, Id.run, List.forIn_yield_eq_foldl]
-  split_ifs <;> simp_all <;> rfl
-
-theorem parentDisabled_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).parentDisabled
-      = field.disabled := by
-  rw [unfold_reduce]
-
-theorem perSubBranch_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).perSubBranch
-      = ((widgetUseReq && field.required && formUseReq)
-         && (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget)) := by
-  rw [unfold_reduce]
-  by_cases h1 : widgetUseReq && field.required && formUseReq = true <;>
-  by_cases h2 : field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget = true <;>
-  simp_all
-
-theorem parentRequired_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).parentRequired
-      = ((widgetUseReq && field.required && formUseReq)
-         && (!(field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget))) := by
-  rw [unfold_reduce]
-  cases widgetUseReq && field.required && formUseReq <;>
-    cases field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget <;>
-    rfl
-
-theorem subwidget_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).subwidgetRequired
-      = (if (widgetUseReq && field.required && formUseReq)
-            && (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget)
-         then field.subPairs.map (fun p => p.1 && p.2)
-         else []) := by
-  rw [unfold_reduce]
-  simp only [loop_fold_is_map, List.nil_append]
-  by_cases hg : (widgetUseReq && field.required && formUseReq) = true <;>
-    by_cases hs : (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget) = true <;>
-    simp [hg, hs]
-
 theorem correct_requiredAttrs :
     ∀ (widgetUseReq formUseReq : Bool) (field : FieldInfo),
       problem_spec_requiredAttrs widgetUseReq formUseReq field
         (implementation_requiredAttrs widgetUseReq formUseReq field) := by
-  intro widgetUseReq formUseReq field
-  refine ⟨?_, ?_, ?_, ?_⟩
-  · exact parentDisabled_eq widgetUseReq formUseReq field
-  · exact perSubBranch_eq widgetUseReq formUseReq field
-  · exact parentRequired_eq widgetUseReq formUseReq field
-  · exact subwidget_eq widgetUseReq formUseReq field
-
+  intro w f field
+  rcases field with ⟨req, dis, hraf, raf, imw, sp⟩
+  refine ⟨?_, ?_, ?_, ?_⟩ <;>
+    (cases w <;> cases f <;> cases req <;> cases dis <;> cases hraf <;>
+     cases raf <;> cases imw <;>
+     simp only [problem_spec_requiredAttrs, implementation_requiredAttrs, Id.run,
+                bind, pure, List.forIn_yield_eq_foldl, loop_fold_is_map,
+                List.nil_append, Bool.and_true, Bool.true_and, Bool.and_false,
+                Bool.false_and, Bool.not_true, Bool.not_false] <;>
+     simp_all)
 -- proof-end
```

Attack 7 — `atk_7_both.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,6 +73,7 @@
   if widgetUseReq && field.required && formUseReq then
     if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget then
       perSubBranch := true
+      parentRequired := true
       for (su, sr) in field.subPairs do
         subwidgetRequired := subwidgetRequired ++ [su && sr]
     else
@@ -91,72 +92,18 @@
   | nil => simp
   | cons hd tl ih => simp [List.foldl_cons, List.map_cons, ih, List.append_assoc]
 
-theorem unfold_reduce (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    implementation_requiredAttrs widgetUseReq formUseReq field =
-      { parentRequired :=
-          if widgetUseReq && field.required && formUseReq then
-            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
-             then false else true)
-          else false,
-        parentDisabled := field.disabled,
-        subwidgetRequired :=
-          if widgetUseReq && field.required && formUseReq then
-            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
-             then field.subPairs.foldl (fun acc p => acc ++ [p.1 && p.2]) []
-             else [])
-          else [],
-        perSubBranch :=
-          if widgetUseReq && field.required && formUseReq then
-            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
-             then true else false)
-          else false } := by
-  simp only [implementation_requiredAttrs, Id.run, List.forIn_yield_eq_foldl]
-  split_ifs <;> simp_all <;> rfl
-
-theorem parentDisabled_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).parentDisabled
-      = field.disabled := by
-  rw [unfold_reduce]
-
-theorem perSubBranch_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).perSubBranch
-      = ((widgetUseReq && field.required && formUseReq)
-         && (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget)) := by
-  rw [unfold_reduce]
-  by_cases h1 : widgetUseReq && field.required && formUseReq = true <;>
-  by_cases h2 : field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget = true <;>
-  simp_all
-
-theorem parentRequired_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).parentRequired
-      = ((widgetUseReq && field.required && formUseReq)
-         && (!(field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget))) := by
-  rw [unfold_reduce]
-  cases widgetUseReq && field.required && formUseReq <;>
-    cases field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget <;>
-    rfl
-
-theorem subwidget_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :
-    (implementation_requiredAttrs widgetUseReq formUseReq field).subwidgetRequired
-      = (if (widgetUseReq && field.required && formUseReq)
-            && (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget)
-         then field.subPairs.map (fun p => p.1 && p.2)
-         else []) := by
-  rw [unfold_reduce]
-  simp only [loop_fold_is_map, List.nil_append]
-  by_cases hg : (widgetUseReq && field.required && formUseReq) = true <;>
-    by_cases hs : (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget) = true <;>
-    simp [hg, hs]
-
 theorem correct_requiredAttrs :
     ∀ (widgetUseReq formUseReq : Bool) (field : FieldInfo),
       problem_spec_requiredAttrs widgetUseReq formUseReq field
         (implementation_requiredAttrs widgetUseReq formUseReq field) := by
-  intro widgetUseReq formUseReq field
-  refine ⟨?_, ?_, ?_, ?_⟩
-  · exact parentDisabled_eq widgetUseReq formUseReq field
-  · exact perSubBranch_eq widgetUseReq formUseReq field
-  · exact parentRequired_eq widgetUseReq formUseReq field
-  · exact subwidget_eq widgetUseReq formUseReq field
-
+  intro w f field
+  rcases field with ⟨req, dis, hraf, raf, imw, sp⟩
+  refine ⟨?_, ?_, ?_, ?_⟩ <;>
+    (cases w <;> cases f <;> cases req <;> cases dis <;> cases hraf <;>
+     cases raf <;> cases imw <;>
+     simp only [problem_spec_requiredAttrs, implementation_requiredAttrs, Id.run,
+                bind, pure, List.forIn_yield_eq_foldl, loop_fold_is_map,
+                List.nil_append, Bool.and_true, Bool.true_and, Bool.and_false,
+                Bool.false_and, Bool.not_true, Bool.not_false] <;>
+     simp_all)
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is computed inside the modeled decision. The per-widget
-- "should this control expose a required marker" predicate is an input the
-- caller supplies (`widgetUseReq` / `subUseReq` below); its result is consumed,
-- not recomputed, so there is no `opaque` callee and no consumed `_prop` axiom.
-- axioms-end

-- pure-start
/-- The attribute-relevant view of a bound field and its widget.
* `required` / `disabled` — the field-level flags.
* `hasRequireAllFields` — whether the field exposes the per-subfield-optional
  switch (a composite field does; a plain field does not).
* `requireAllFields` — that switch's value (relevant only when present).
* `isMultiWidget` — whether the field's widget is a composite of subwidgets.
* `subPairs` — one entry per (subfield, subwidget) pair taken together in order
  (mirroring the single paired walk over the two aligned sequences); each entry
  is `(subUseReq, subRequired)`: the subwidget's "expose a required marker"
  predicate result paired with that subfield's own required flag. -/
structure FieldInfo where
  required : Bool
  disabled : Bool
  hasRequireAllFields : Bool
  requireAllFields : Bool
  isMultiWidget : Bool
  subPairs : List (Bool × Bool)

/-- The attribute decisions produced for a bound field's widget.
* `parentRequired` — a required marker placed on the field's own widget.
* `parentDisabled` — a disabled marker placed on the field's own widget.
* `subwidgetRequired` — the required markers written to each subwidget, in order
  (empty unless the per-subwidget branch ran).
* `perSubBranch` — whether the per-subwidget placement branch ran. -/
structure Result where
  parentRequired : Bool
  parentDisabled : Bool
  subwidgetRequired : List Bool
  perSubBranch : Bool
-- pure-end

-- post-conditions-start
/-- The required-marker placement. The guard holds when the widget would expose a
required marker, the field is required, and the form enables required markers.
When the field is a composite of individually-optional subfields rendered through
a composite widget, the required markers are placed per subwidget — each one set
exactly when that subwidget would expose a marker AND its subfield is required —
and the field's own widget receives no required marker. Otherwise the field's own
widget receives the required marker. The disabled marker is placed on the field's
own widget exactly when the field is disabled. -/
def problem_spec_requiredAttrs
    (widgetUseReq formUseReq : Bool) (field : FieldInfo) (result : Result) : Prop :=
  let guard := widgetUseReq && field.required && formUseReq
  let subBranch :=
    field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
  result.parentDisabled = field.disabled ∧
  result.perSubBranch = (guard && subBranch) ∧
  result.parentRequired = (guard && !subBranch) ∧
  result.subwidgetRequired =
    (if guard && subBranch
     then field.subPairs.map (fun p => p.1 && p.2)
     else [])
-- post-conditions-end

-- impl-start
def implementation_requiredAttrs
    (widgetUseReq formUseReq : Bool) (field : FieldInfo) : Result := Id.run do
  let mut parentRequired := false
  let mut parentDisabled := false
  let mut subwidgetRequired : List Bool := []
  let mut perSubBranch := false
  if widgetUseReq && field.required && formUseReq then
    if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget then
      perSubBranch := true
      for (su, sr) in field.subPairs do
        subwidgetRequired := subwidgetRequired ++ [su && sr]
    else
      parentRequired := true
  if field.disabled then
    parentDisabled := true
  return { parentRequired, parentDisabled, subwidgetRequired, perSubBranch }
-- impl-end


-- proof-start
theorem loop_fold_is_map (l : List (Bool × Bool)) (init : List Bool) :
    l.foldl (fun acc p => acc ++ [p.1 && p.2]) init
      = init ++ l.map (fun p => p.1 && p.2) := by
  induction l generalizing init with
  | nil => simp
  | cons hd tl ih => simp [List.foldl_cons, List.map_cons, ih, List.append_assoc]

theorem correct_requiredAttrs :
    ∀ (widgetUseReq formUseReq : Bool) (field : FieldInfo),
      problem_spec_requiredAttrs widgetUseReq formUseReq field
        (implementation_requiredAttrs widgetUseReq formUseReq field) := by
  intro w f field
  rcases field with ⟨req, dis, hraf, raf, imw, sp⟩
  refine ⟨?_, ?_, ?_, ?_⟩ <;>
    (cases w <;> cases f <;> cases req <;> cases dis <;> cases hraf <;>
     cases raf <;> cases imw <;>
     simp only [problem_spec_requiredAttrs, implementation_requiredAttrs, Id.run,
                bind, pure, List.forIn_yield_eq_foldl, loop_fold_is_map,
                List.nil_append, Bool.and_true, Bool.true_and, Bool.and_false,
                Bool.false_and, Bool.not_true, Bool.not_false] <;>
     simp_all)
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: every attack same_spec=True vs Solution.lean (verified via swebench_unified.markers.same_spec). Verify cmd for each: `bash scripts/lean_verify.sh <file>`, run concurrently in batches of 4.

POSITIVE CONTROL atk_pos.lean (gold impl + robust generic total-case-split proof): EXIT=0. `#print axioms correct_requiredAttrs` -> [propext, Quot.sound] (clean, no sorryAx, no sorry). Confirms the proof harness/tactic can close a CORRECT impl, so the wrong-impl failures below are genuine spec violations, not tactic weakness.

### ATTACKS (all same-spec, all edit ONLY impl region; each given the SAME closing generic proof that closes the gold impl):
1. atk_1_prepatch.lean (prepatch bug: under guard always parentRequired:=true, never per-subwidget branch) -> EXIT=1, error: unsolved goals (line 92). Reproduces the prepatch defect the gold patch fixes.
2. atk_2_or.lean (ungrounded-oracle echo: subwidget flag = su || sr instead of su && sr) -> EXIT=1, unsolved goals.
3. atk_3_raf.lean (boundary: dropped the !requireAllFields negation -> uses requireAllFields) -> EXIT=1, unsolved goals.
4. atk_4_disabled.lean (control-flow-effect: disabled marker set only inside the guard branches) -> EXIT=1, unsolved goals.
5. atk_5_partial.lean (partial-domain: sub-branch only when subPairs nonempty; empty case sets parentRequired) -> EXIT=1, unsolved goals.
6. atk_6_nomw.lean (dropped isMultiWidget from the sub-branch condition) -> EXIT=1, unsolved goals.
7. atk_7_both.lean (in sub-branch sets BOTH parentRequired:=true AND subwidgets) -> EXIT=1, unsolved goals.
All 7 errors are genuine 'unsolved goals' (false goals forced by the postcondition), NOT syntax errors — confirmed by the identical proof closing atk_pos.

No wrong impl closes with clean axioms => step 2 (materialize+resolve faithful patch) is vacuous: patches={}.

REFINEMENT AUDIT (refinement.md): 6 legs, all R / R/I / I — no consumed axiom, no A-reference, no kind-3. axioms-start region empty; axiom_check.py is a legitimate skip stub. The only unchanged callee use_required_attribute is correctly modeled as a consumed INPUT boolean (widgetUseReq/subUseReq), not recomputed; correspondence to the real callee holds. G-CONF (conformance_check.py, seed 14034, N=120000 + 7 boundary cases) drives the REAL patched BoundField.build_widget_attrs with duck-typed widgets returning the fuzzed boolean (I/O bridging) and compares parentRequired/parentDisabled/subwidgetRequired — the model↔patch correspondence is mechanically bridged there. patch.diff == gold verbatim (matches mapping.md boundfield.py:232-241).

CONCLUSION: spec is fully determined (spec_determines proven), tight against >=7 distinct wrong impls, faithful, refinement legs sound. verify ⇏ correct is NOT exhibited. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_2_or.lean`, `atk_3_raf.lean`, `atk_4_disabled.lean`, `atk_5_partial.lean`, `atk_6_nomw.lean`, `atk_7_both.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong implementation closes correct_requiredAttrs, so no faithful patch could be materialized/resolve-run. The spec fully determines Result: I proved spec_determines mechanically (det.lean, lean_verify EXIT=0) — problem_spec_requiredAttrs pins all four Result fields (parentDisabled, perSubBranch, parentRequired, subwidgetRequired) as closed functions of the inputs, so any impl closing correct_ is extensionally equal to gold and therefore resolves. verify ⇒ correct.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_or.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_raf.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_disabled.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_partial.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_nomw.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_both.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is computed inside the modeled decision. The per-widget
-- "should this control expose a required marker" predicate is an input the
-- caller supplies (`widgetUseReq` / `subUseReq` below); its result is consumed,
-- not recomputed, so there is no `opaque` callee and no consumed `_prop` axiom.
-- axioms-end

-- pure-start
/-- The attribute-relevant view of a bound field and its widget.
* `required` / `disabled` — the field-level flags.
* `hasRequireAllFields` — whether the field exposes the per-subfield-optional
  switch (a composite field does; a plain field does not).
* `requireAllFields` — that switch's value (relevant only when present).
* `isMultiWidget` — whether the field's widget is a composite of subwidgets.
* `subPairs` — one entry per (subfield, subwidget) pair taken together in order
  (mirroring the single paired walk over the two aligned sequences); each entry
  is `(subUseReq, subRequired)`: the subwidget's "expose a required marker"
  predicate result paired with that subfield's own required flag. -/
structure FieldInfo where
  required : Bool
  disabled : Bool
  hasRequireAllFields : Bool
  requireAllFields : Bool
  isMultiWidget : Bool
  subPairs : List (Bool × Bool)

/-- The attribute decisions produced for a bound field's widget.
* `parentRequired` — a required marker placed on the field's own widget.
* `parentDisabled` — a disabled marker placed on the field's own widget.
* `subwidgetRequired` — the required markers written to each subwidget, in order
  (empty unless the per-subwidget branch ran).
* `perSubBranch` — whether the per-subwidget placement branch ran. -/
structure Result where
  parentRequired : Bool
  parentDisabled : Bool
  subwidgetRequired : List Bool
  perSubBranch : Bool
-- pure-end

-- post-conditions-start
/-- The required-marker placement. The guard holds when the widget would expose a
required marker, the field is required, and the form enables required markers.
When the field is a composite of individually-optional subfields rendered through
a composite widget, the required markers are placed per subwidget — each one set
exactly when that subwidget would expose a marker AND its subfield is required —
and the field's own widget receives no required marker. Otherwise the field's own
widget receives the required marker. The disabled marker is placed on the field's
own widget exactly when the field is disabled. -/
def problem_spec_requiredAttrs
    (widgetUseReq formUseReq : Bool) (field : FieldInfo) (result : Result) : Prop :=
  let guard := widgetUseReq && field.required && formUseReq
  let subBranch :=
    field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
  result.parentDisabled = field.disabled ∧
  result.perSubBranch = (guard && subBranch) ∧
  result.parentRequired = (guard && !subBranch) ∧
  result.subwidgetRequired =
    (if guard && subBranch
     then field.subPairs.map (fun p => p.1 && p.2)
     else [])
-- post-conditions-end

-- impl-start
def implementation_requiredAttrs
    (widgetUseReq formUseReq : Bool) (field : FieldInfo) : Result := Id.run do
  let mut parentRequired := false
  let mut parentDisabled := false
  let mut subwidgetRequired : List Bool := []
  let mut perSubBranch := false
  if widgetUseReq && field.required && formUseReq then
    if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget then
      perSubBranch := true
      for (su, sr) in field.subPairs do
        subwidgetRequired := subwidgetRequired ++ [su && sr]
    else
      parentRequired := true
  if field.disabled then
    parentDisabled := true
  return { parentRequired, parentDisabled, subwidgetRequired, perSubBranch }
-- impl-end


-- proof-start
theorem loop_fold_is_map (l : List (Bool × Bool)) (init : List Bool) :
    l.foldl (fun acc p => acc ++ [p.1 && p.2]) init
      = init ++ l.map (fun p => p.1 && p.2) := by
  induction l generalizing init with
  | nil => simp
  | cons hd tl ih => simp [List.foldl_cons, List.map_cons, ih, List.append_assoc]

theorem correct_requiredAttrs :
    ∀ (widgetUseReq formUseReq : Bool) (field : FieldInfo),
      problem_spec_requiredAttrs widgetUseReq formUseReq field
        (implementation_requiredAttrs widgetUseReq formUseReq field) := by
  intro w f field
  rcases field with ⟨req, dis, hraf, raf, imw, sp⟩
  refine ⟨?_, ?_, ?_, ?_⟩ <;>
    (cases w <;> cases f <;> cases req <;> cases dis <;> cases hraf <;>
     cases raf <;> cases imw <;>
     simp only [problem_spec_requiredAttrs, implementation_requiredAttrs, Id.run,
                bind, pure, List.forIn_yield_eq_foldl, loop_fold_is_map,
                List.nil_append, Bool.and_true, Bool.true_and, Bool.and_false,
                Bool.false_and, Bool.not_true, Bool.not_false] <;>
     simp_all)
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: every attack same_spec=True vs Solution.lean (verified via swebench_unified.markers.same_spec). Verify cmd for each: `bash scripts/lean_verify.sh <file>`, run concurrently in batches of 4.

POSITIVE CONTROL atk_pos.lean (gold impl + robust generic total-case-split proof): EXIT=0. `#print axioms correct_requiredAttrs` -> [propext, Quot.sound] (clean, no sorryAx, no sorry). Confirms the proof harness/tactic can close a CORRECT impl, so the wrong-impl failures below are genuine spec violations, not tactic weakness.

### ATTACKS (all same-spec, all edit ONLY impl region; each given the SAME closing generic proof that closes the gold impl):
1. atk_1_prepatch.lean (prepatch bug: under guard always parentRequired:=true, never per-subwidget branch) -> EXIT=1, error: unsolved goals (line 92). Reproduces the prepatch defect the gold patch fixes.
2. atk_2_or.lean (ungrounded-oracle echo: subwidget flag = su || sr instead of su && sr) -> EXIT=1, unsolved goals.
3. atk_3_raf.lean (boundary: dropped the !requireAllFields negation -> uses requireAllFields) -> EXIT=1, unsolved goals.
4. atk_4_disabled.lean (control-flow-effect: disabled marker set only inside the guard branches) -> EXIT=1, unsolved goals.
5. atk_5_partial.lean (partial-domain: sub-branch only when subPairs nonempty; empty case sets parentRequired) -> EXIT=1, unsolved goals.
6. atk_6_nomw.lean (dropped isMultiWidget from the sub-branch condition) -> EXIT=1, unsolved goals.
7. atk_7_both.lean (in sub-branch sets BOTH parentRequired:=true AND subwidgets) -> EXIT=1, unsolved goals.
All 7 errors are genuine 'unsolved goals' (false goals forced by the postcondition), NOT syntax errors — confirmed by the identical proof closing atk_pos.

No wrong impl closes with clean axioms => step 2 (materialize+resolve faithful patch) is vacuous: patches={}.

REFINEMENT AUDIT (refinement.md): 6 legs, all R / R/I / I — no consumed axiom, no A-reference, no kind-3. axioms-start region empty; axiom_check.py is a legitimate skip stub. The only unchanged callee use_required_attribute is correctly modeled as a consumed INPUT boolean (widgetUseReq/subUseReq), not recomputed; correspondence to the real callee holds. G-CONF (conformance_check.py, seed 14034, N=120000 + 7 boundary cases) drives the REAL patched BoundField.build_widget_attrs with duck-typed widgets returning the fuzzed boolean (I/O bridging) and compares parentRequired/parentDisabled/subwidgetRequired — the model↔patch correspondence is mechanically bridged there. patch.diff == gold verbatim (matches mapping.md boundfield.py:232-241).

CONCLUSION: spec is fully determined (spec_determines proven), tight against >=7 distinct wrong impls, faithful, refinement legs sound. verify ⇏ correct is NOT exhibited. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** No divergence between problem_spec_requiredAttrs and the real patched BoundField.build_widget_attrs. Checks: (1) Solution.lean compiles exit 0, #print axioms = [propext, Quot.sound], no sorryAx — proof genuine. (2) same_spec(Solution, Solution_prepatch, LeanBackend)=True; prepatch fails G-DIFF via sorry as intended. Gold patch matches worktree. Re-ran conformance_check.py against the REAL patched repo: 120007 inputs, 0 disagreements. (5) Independent exhaustive spec-vs-real harness over the full 7-boolean cube × 8 subPair shapes (1024 cases) → 0 divergences, including the reporter's multi-widget/require_all_fields=False/mixed-subfield case. Spec is not too strong: parentDisabled=field.disabled tracks the unchanged branch; parentRequired/subwidgetRequired are mutually exclusive on subBranch with the empty non-branch case pinned []; perSubBranch is internal bookkeeping (no Django observable) deterministically derived and correctly excluded from the G-CONF differential; incoming-attrs pass-through is honestly declared out-of-scope. Spec pins exactly the touched required/disabled placement decision and agrees with the real callee on every modeled input.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the Lean spec view (generated via markers.spec_view; impl+proof regions elided) against the public problem_statement ONLY (not hints_text). same_spec(Solution, Solution_prepatch)=True, so the spec region is genuinely frozen/byte-identical. leakage.screen() passes: no hard failures, no warnings.

Semantic review: (1) All spec-view identifiers map to publicly-disclosed concepts — the problem_statement explicitly names require_all_fields, MultiWidget, MultiValueField, required, and 'sub field'; spec-view names hasRequireAllFields/requireAllFields, isMultiWidget, subPairs/subUseReq/subRequired, required correspond directly. (2) Patched repo symbols NOT in the public statement — build_widget_attrs, use_required_attribute — are ABSENT from the spec view; the unchanged callee is abstracted as an input boolean (widgetUseReq/subUseReq, 'expose a required marker predicate'), so no internal symbol is echoed. (3) 'disabled' appears in the spec view but is unchanged context, not the gold edit — an unmodified framed component, not a disclosure of diff mechanics. (4) No fix/bug narration in comments, no diff markers, no patched file path, no reproduced gold-diff line; rationale comments are abstract. (5) The postcondition necessarily encodes the correct per-subwidget placement behavior, but strictly in public concepts (composite field of individually-optional subfields rendered through a MultiWidget) — the unavoidable content of any faithful spec, not extra leakage.

No RELAXED_LEAKAGE.md needed; the screen and my independent judgment agree with the recorded G-PANEL-3 verdict. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
