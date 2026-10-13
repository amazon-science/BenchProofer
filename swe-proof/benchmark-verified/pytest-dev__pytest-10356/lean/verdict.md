# P2 adversarial audit — pytest-dev__pytest-10356

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_prepatch.lean`, `atk_2_reversed.lean`, `atk_3_dedup.lean`, `atk_4_partial_domain.lean`, `atk_5_boundary_droplast.lean`, `atk_6_mode_ignored.lean`, `atk_7_bare_dropped.lean`, `atk_9_restricted_wrong_entry.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_8_oracle_echo.lean`, `atk_10_equal_restructure.lean`, `atk_11_alias_singleton.lean`, `atk_12_getattr_fallback.lean`, `atk_13_no_normalize.lean`, `atk_14_nonclass_branch.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No same-spec wrong implementation can verify. Machine-checked reason (uniqueness.lean, lean_verify.sh exit 0): the postcondition is a TOTAL FUNCTIONAL EQUATION -- `result = (if wholeHierarchy then hierarchy.flatMap flattenClassMarks else flattenClassMarks (hierarchy.headD (ClassMarks.many [])))` -- with no precondition and no existential slack. I proved `spec_is_functional : (forall h w, spec h w (f h w)) -> (forall h w, spec h w (g h w)) -> forall h w, f h w = g h w` and its corollary `any_verifier_equals_gold`. So the set of verifying impls is exactly the singleton extensional class of the gold function; 'same spec AND verifies AND wrong' is impossible at the model level. Every verifying attack (6 of 14) is therefore an ECHO, and all 6 faithful patches RESOLVED. All 8 genuinely-wrong impls were rejected, each with a `decide`-checked concrete counterexample in disproof.lean (exit 0).
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,12 +70,14 @@
 -- post-conditions-end
 
 -- impl-start
+
+-- PRE-PATCH bug re-encoded: the gathering reads only the SINGLE resolved entry
+-- (the class's own), never walking the rest of the resolution chain. In full
+-- mode every ancestor's labels are silently dropped.
 def implementation_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool) :
     List Mark := Id.run do
-  -- restricted mode: only the class's own stored entry; full mode: every class
-  -- in the resolution chain.
-  let markLists := if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]
-                   else hierarchy
+  let _ := wholeHierarchy
+  let markLists := [hierarchy.headD (ClassMarks.many [])]
   let mut markList : List Mark := []
   for item in markLists do
     match item with
```

Attack 2 — `atk_2_reversed.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,12 +70,13 @@
 -- post-conditions-end
 
 -- impl-start
+
+-- WRONG: walks the resolution chain in REVERSE (most distant ancestor first),
+-- so the gathered labels come out in the opposite of resolution order.
 def implementation_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool) :
     List Mark := Id.run do
-  -- restricted mode: only the class's own stored entry; full mode: every class
-  -- in the resolution chain.
   let markLists := if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]
-                   else hierarchy
+                   else hierarchy.reverse
   let mut markList : List Mark := []
   for item in markLists do
     match item with
```

Attack 3 — `atk_3_dedup.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,10 +70,11 @@
 -- post-conditions-end
 
 -- impl-start
+
+-- WRONG: de-duplicates the gathered labels, so a label carried by both the
+-- class and an ancestor appears once instead of twice (duplicates must be kept).
 def implementation_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool) :
     List Mark := Id.run do
-  -- restricted mode: only the class's own stored entry; full mode: every class
-  -- in the resolution chain.
   let markLists := if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]
                    else hierarchy
   let mut markList : List Mark := []
@@ -81,7 +82,7 @@
     match item with
     | .many xs => markList := markList ++ xs
     | .one m   => markList := markList ++ [m]
-  return markList
+  return markList.eraseDups
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4_partial_domain.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,12 +70,16 @@
 -- post-conditions-end
 
 -- impl-start
+
+-- WRONG (partial domain): correct only for chains of length <= 1. Any deeper
+-- hierarchy -- exactly the case the patch exists to fix -- returns the class's
+-- own labels only, reproducing the pre-patch loss for length >= 2.
 def implementation_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool) :
     List Mark := Id.run do
-  -- restricted mode: only the class's own stored entry; full mode: every class
-  -- in the resolution chain.
-  let markLists := if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]
-                   else hierarchy
+  let markLists :=
+    if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]
+    else if hierarchy.length <= 1 then hierarchy
+    else [hierarchy.headD (ClassMarks.many [])]
   let mut markList : List Mark := []
   for item in markLists do
     match item with
```

Attack 5 — `atk_5_boundary_droplast.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,12 +70,13 @@
 -- post-conditions-end
 
 -- impl-start
+
+-- WRONG (off-by-one boundary): walks the chain but drops its LAST entry, so the
+-- most distant ancestor's labels are lost.
 def implementation_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool) :
     List Mark := Id.run do
-  -- restricted mode: only the class's own stored entry; full mode: every class
-  -- in the resolution chain.
   let markLists := if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]
-                   else hierarchy
+                   else hierarchy.dropLast
   let mut markList : List Mark := []
   for item in markLists do
     match item with
```

Attack 6 — `atk_6_mode_ignored.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,12 +70,14 @@
 -- post-conditions-end
 
 -- impl-start
+
+-- WRONG (control-flow effect): the restricted-mode flag is ignored, so asking
+-- for only the class's OWN labels still returns the whole chain's. This is the
+-- exact leg `store_mark(consider_mro=False)` depends on.
 def implementation_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool) :
     List Mark := Id.run do
-  -- restricted mode: only the class's own stored entry; full mode: every class
-  -- in the resolution chain.
-  let markLists := if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]
-                   else hierarchy
+  let _ := wholeHierarchy
+  let markLists := hierarchy
   let mut markList : List Mark := []
   for item in markLists do
     match item with
```

Attack 7 — `atk_7_bare_dropped.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,17 +70,18 @@
 -- post-conditions-end
 
 -- impl-start
+
+-- WRONG: a class that stores a SINGLE bare label (rather than a list)
+-- contributes nothing, so that class's label is silently lost.
 def implementation_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool) :
     List Mark := Id.run do
-  -- restricted mode: only the class's own stored entry; full mode: every class
-  -- in the resolution chain.
   let markLists := if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]
                    else hierarchy
   let mut markList : List Mark := []
   for item in markLists do
     match item with
     | .many xs => markList := markList ++ xs
-    | .one m   => markList := markList ++ [m]
+    | .one _   => markList := markList ++ []
   return markList
 -- impl-end
 
```

Attack 8 — `atk_8_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -70,57 +70,23 @@
 -- post-conditions-end
 
 -- impl-start
+
+-- ORACLE ECHO: the postcondition's right-hand side transcribed verbatim as the
+-- implementation. It carries no algorithm of its own -- it simply restates the
+-- spec -- so it verifies by `rfl`. Submitted to test whether a spec-shaped
+-- "implementation" is an echo of the gold behavior (harmless) or a hole.
 def implementation_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool) :
-    List Mark := Id.run do
-  -- restricted mode: only the class's own stored entry; full mode: every class
-  -- in the resolution chain.
-  let markLists := if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]
-                   else hierarchy
-  let mut markList : List Mark := []
-  for item in markLists do
-    match item with
-    | .many xs => markList := markList ++ xs
-    | .one m   => markList := markList ++ [m]
-  return markList
+    List Mark :=
+  if wholeHierarchy then hierarchy.flatMap flattenClassMarks
+  else flattenClassMarks (hierarchy.headD (ClassMarks.many []))
 -- impl-end
 
 -- proof-start
-theorem loop_helper :
-    ∀ (markLists : List ClassMarks) (init : List Mark),
-      (Id.run (do
-        let r ← forIn markLists init (fun item markList =>
-          (match item with
-            | .many xs => do pure PUnit.unit; pure (ForInStep.yield (markList ++ xs))
-            | .one m   => do pure PUnit.unit; pure (ForInStep.yield (markList ++ [m]))))
-        pure r)) =
-        init ++ markLists.flatMap flattenClassMarks := by
-  intro markLists
-  induction markLists with
-  | nil => intro init; simp only [List.forIn_nil, List.flatMap_nil, List.append_nil, Id.run, bind, pure]
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    cases a with
-    | many xs =>
-      simp only [Id.run, bind] at ih ⊢
-      simp only [flattenClassMarks, List.flatMap_cons, ih, List.append_assoc]
-    | one m =>
-      simp only [Id.run, bind] at ih ⊢
-      simp only [flattenClassMarks, List.flatMap_cons, ih, List.append_assoc]
-
 theorem correct_inheritedMarks :
     ∀ (hierarchy : List ClassMarks) (wholeHierarchy : Bool),
       problem_spec_inheritedMarks hierarchy wholeHierarchy
         (implementation_inheritedMarks hierarchy wholeHierarchy) := by
   intro hierarchy wholeHierarchy
   unfold problem_spec_inheritedMarks implementation_inheritedMarks
-  rw [loop_helper]
-  simp only [List.nil_append]
-  cases wholeHierarchy with
-  | true => simp
-  | false =>
-    simp only [Bool.not_false, if_true]
-    cases h2 : hierarchy.headD (ClassMarks.many []) with
-    | many xs => simp [flattenClassMarks]
-    | one m => simp [flattenClassMarks]
+  rfl
 -- proof-end
```

Attack 9 — `atk_9_restricted_wrong_entry.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,11 +70,12 @@
 -- post-conditions-end
 
 -- impl-start
+
+-- WRONG: restricted mode reads the entry of the class's first PARENT rather
+-- than the class's own entry (index 1 instead of index 0).
 def implementation_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool) :
     List Mark := Id.run do
-  -- restricted mode: only the class's own stored entry; full mode: every class
-  -- in the resolution chain.
-  let markLists := if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]
+  let markLists := if !wholeHierarchy then [hierarchy.tail.headD (ClassMarks.many [])]
                    else hierarchy
   let mut markList : List Mark := []
   for item in markLists do
```

Attack 10 — `atk_10_equal_restructure.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -70,43 +70,28 @@
 -- post-conditions-end
 
 -- impl-start
+
+-- An INDEPENDENT algorithm (fold over the chain rather than a mutable loop),
+-- extensionally equal to gold. Submitted as the model<->patch correspondence
+-- probe: its faithful refinement is a genuinely different Python body.
 def implementation_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool) :
-    List Mark := Id.run do
-  -- restricted mode: only the class's own stored entry; full mode: every class
-  -- in the resolution chain.
-  let markLists := if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]
-                   else hierarchy
-  let mut markList : List Mark := []
-  for item in markLists do
-    match item with
-    | .many xs => markList := markList ++ xs
-    | .one m   => markList := markList ++ [m]
-  return markList
+    List Mark :=
+  let markLists := if wholeHierarchy then hierarchy
+                   else [hierarchy.headD (ClassMarks.many [])]
+  markLists.foldl (fun acc item => acc ++ flattenClassMarks item) []
 -- impl-end
 
 -- proof-start
-theorem loop_helper :
-    ∀ (markLists : List ClassMarks) (init : List Mark),
-      (Id.run (do
-        let r ← forIn markLists init (fun item markList =>
-          (match item with
-            | .many xs => do pure PUnit.unit; pure (ForInStep.yield (markList ++ xs))
-            | .one m   => do pure PUnit.unit; pure (ForInStep.yield (markList ++ [m]))))
-        pure r)) =
-        init ++ markLists.flatMap flattenClassMarks := by
-  intro markLists
-  induction markLists with
-  | nil => intro init; simp only [List.forIn_nil, List.flatMap_nil, List.append_nil, Id.run, bind, pure]
+theorem fold_append :
+    ∀ (l : List ClassMarks) (init : List Mark),
+      l.foldl (fun acc item => acc ++ flattenClassMarks item) init
+        = init ++ l.flatMap flattenClassMarks := by
+  intro l
+  induction l with
+  | nil => intro init; simp
   | cons a as ih =>
     intro init
-    rw [List.forIn_cons]
-    cases a with
-    | many xs =>
-      simp only [Id.run, bind] at ih ⊢
-      simp only [flattenClassMarks, List.flatMap_cons, ih, List.append_assoc]
-    | one m =>
-      simp only [Id.run, bind] at ih ⊢
-      simp only [flattenClassMarks, List.flatMap_cons, ih, List.append_assoc]
+    simp only [List.foldl_cons, List.flatMap_cons, ih, List.append_assoc]
 
 theorem correct_inheritedMarks :
     ∀ (hierarchy : List ClassMarks) (wholeHierarchy : Bool),
@@ -114,13 +99,11 @@
         (implementation_inheritedMarks hierarchy wholeHierarchy) := by
   intro hierarchy wholeHierarchy
   unfold problem_spec_inheritedMarks implementation_inheritedMarks
-  rw [loop_helper]
-  simp only [List.nil_append]
   cases wholeHierarchy with
-  | true => simp
+  | true => simp only [if_true]; rw [fold_append]; simp
   | false =>
-    simp only [Bool.not_false, if_true]
-    cases h2 : hierarchy.headD (ClassMarks.many []) with
-    | many xs => simp [flattenClassMarks]
-    | one m => simp [flattenClassMarks]
+    simp only [Bool.false_eq_true, if_false]
+    rw [fold_append]
+    simp only [List.nil_append, List.flatMap_cons, List.flatMap_nil,
+               List.append_nil]
 -- proof-end
```

Attack 11 — `atk_11_alias_singleton.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -70,57 +70,35 @@
 -- post-conditions-end
 
 -- impl-start
+-- Lean-equal to gold, but written so its faithful Python refinement returns the
+-- STORED list object itself in the single-entry case (an alias, not a copy)
+-- rather than a freshly built list. Lean cannot observe aliasing: `xs` is the
+-- same immutable value either way, so this closes. The probe is whether the
+-- model's blindness to aliasing hides a real defect.
 def implementation_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool) :
-    List Mark := Id.run do
-  -- restricted mode: only the class's own stored entry; full mode: every class
-  -- in the resolution chain.
-  let markLists := if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]
-                   else hierarchy
-  let mut markList : List Mark := []
-  for item in markLists do
-    match item with
-    | .many xs => markList := markList ++ xs
-    | .one m   => markList := markList ++ [m]
-  return markList
+    List Mark :=
+  let markLists := if wholeHierarchy then hierarchy
+                   else [hierarchy.headD (ClassMarks.many [])]
+  match markLists with
+  | [single] => flattenClassMarks single      -- alias fast path
+  | rest     => rest.flatMap flattenClassMarks
 -- impl-end
 
 -- proof-start
-theorem loop_helper :
-    ∀ (markLists : List ClassMarks) (init : List Mark),
-      (Id.run (do
-        let r ← forIn markLists init (fun item markList =>
-          (match item with
-            | .many xs => do pure PUnit.unit; pure (ForInStep.yield (markList ++ xs))
-            | .one m   => do pure PUnit.unit; pure (ForInStep.yield (markList ++ [m]))))
-        pure r)) =
-        init ++ markLists.flatMap flattenClassMarks := by
-  intro markLists
-  induction markLists with
-  | nil => intro init; simp only [List.forIn_nil, List.flatMap_nil, List.append_nil, Id.run, bind, pure]
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    cases a with
-    | many xs =>
-      simp only [Id.run, bind] at ih ⊢
-      simp only [flattenClassMarks, List.flatMap_cons, ih, List.append_assoc]
-    | one m =>
-      simp only [Id.run, bind] at ih ⊢
-      simp only [flattenClassMarks, List.flatMap_cons, ih, List.append_assoc]
-
 theorem correct_inheritedMarks :
     ∀ (hierarchy : List ClassMarks) (wholeHierarchy : Bool),
       problem_spec_inheritedMarks hierarchy wholeHierarchy
         (implementation_inheritedMarks hierarchy wholeHierarchy) := by
   intro hierarchy wholeHierarchy
   unfold problem_spec_inheritedMarks implementation_inheritedMarks
-  rw [loop_helper]
-  simp only [List.nil_append]
   cases wholeHierarchy with
-  | true => simp
   | false =>
-    simp only [Bool.not_false, if_true]
-    cases h2 : hierarchy.headD (ClassMarks.many []) with
-    | many xs => simp [flattenClassMarks]
-    | one m => simp [flattenClassMarks]
+    match hierarchy with
+    | [] => simp
+    | a :: t => cases a <;> simp
+  | true =>
+    match hierarchy with
+    | [] => simp
+    | [a] => cases a <;> simp
+    | a :: b :: t => simp
 -- proof-end
```

Attack 12 — `atk_12_getattr_fallback.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -70,57 +70,37 @@
 -- post-conditions-end
 
 -- impl-start
+-- Lean-equal to gold. Its faithful Python refinement uses
+-- `getattr(x, "pytestmark", [])` per class instead of
+-- `x.__dict__.get("pytestmark", [])`. The Lean model encodes "this class stores
+-- nothing" as `ClassMarks.many []`, so an inherited-vs-own read is INVISIBLE in
+-- the model -- both present as the empty contribution. Probe of whether the
+-- A-reference row (the __dict__ read) is actually pinned by the spec.
 def implementation_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool) :
-    List Mark := Id.run do
-  -- restricted mode: only the class's own stored entry; full mode: every class
-  -- in the resolution chain.
-  let markLists := if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]
-                   else hierarchy
-  let mut markList : List Mark := []
-  for item in markLists do
-    match item with
-    | .many xs => markList := markList ++ xs
-    | .one m   => markList := markList ++ [m]
-  return markList
+    List Mark :=
+  (if wholeHierarchy then hierarchy
+   else [hierarchy.headD (ClassMarks.many [])]).flatMap
+     (fun item => match item with
+                  | .many xs => xs
+                  | .one m   => [m])
 -- impl-end
 
 -- proof-start
-theorem loop_helper :
-    ∀ (markLists : List ClassMarks) (init : List Mark),
-      (Id.run (do
-        let r ← forIn markLists init (fun item markList =>
-          (match item with
-            | .many xs => do pure PUnit.unit; pure (ForInStep.yield (markList ++ xs))
-            | .one m   => do pure PUnit.unit; pure (ForInStep.yield (markList ++ [m]))))
-        pure r)) =
-        init ++ markLists.flatMap flattenClassMarks := by
-  intro markLists
-  induction markLists with
-  | nil => intro init; simp only [List.forIn_nil, List.flatMap_nil, List.append_nil, Id.run, bind, pure]
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    cases a with
-    | many xs =>
-      simp only [Id.run, bind] at ih ⊢
-      simp only [flattenClassMarks, List.flatMap_cons, ih, List.append_assoc]
-    | one m =>
-      simp only [Id.run, bind] at ih ⊢
-      simp only [flattenClassMarks, List.flatMap_cons, ih, List.append_assoc]
-
 theorem correct_inheritedMarks :
     ∀ (hierarchy : List ClassMarks) (wholeHierarchy : Bool),
       problem_spec_inheritedMarks hierarchy wholeHierarchy
         (implementation_inheritedMarks hierarchy wholeHierarchy) := by
   intro hierarchy wholeHierarchy
   unfold problem_spec_inheritedMarks implementation_inheritedMarks
-  rw [loop_helper]
-  simp only [List.nil_append]
+  have hfun : (fun item => match item with
+                           | ClassMarks.many xs => xs
+                           | ClassMarks.one m => [m]) = flattenClassMarks := by
+    funext item; cases item <;> rfl
+  rw [hfun]
   cases wholeHierarchy with
   | true => simp
   | false =>
-    simp only [Bool.not_false, if_true]
-    cases h2 : hierarchy.headD (ClassMarks.many []) with
-    | many xs => simp [flattenClassMarks]
-    | one m => simp [flattenClassMarks]
+    match hierarchy with
+    | [] => simp
+    | a :: t => cases a <;> simp
 -- proof-end
```

Attack 13 — `atk_13_no_normalize.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -70,43 +70,36 @@
 -- post-conditions-end
 
 -- impl-start
+-- Lean-equal to gold (`flattenClassMarks` forwards stored labels verbatim, and
+-- the bundle models normalization as that identity). Its faithful refinement
+-- therefore omits the `normalize_mark_list` call entirely -- the model says it is
+-- an identity, so a faithful reading of the model has nothing to emit for it.
+-- Probe of the second A-reference row.
 def implementation_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool) :
     List Mark := Id.run do
-  -- restricted mode: only the class's own stored entry; full mode: every class
-  -- in the resolution chain.
-  let markLists := if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]
-                   else hierarchy
-  let mut markList : List Mark := []
-  for item in markLists do
-    match item with
-    | .many xs => markList := markList ++ xs
-    | .one m   => markList := markList ++ [m]
-  return markList
+  let mut acc : List Mark := []
+  let chain := if wholeHierarchy then hierarchy
+               else [hierarchy.headD (ClassMarks.many [])]
+  for item in chain do
+    acc := acc ++ flattenClassMarks item
+  return acc
 -- impl-end
 
 -- proof-start
-theorem loop_helper :
-    ∀ (markLists : List ClassMarks) (init : List Mark),
+theorem gather_helper :
+    ∀ (l : List ClassMarks) (init : List Mark),
       (Id.run (do
-        let r ← forIn markLists init (fun item markList =>
-          (match item with
-            | .many xs => do pure PUnit.unit; pure (ForInStep.yield (markList ++ xs))
-            | .one m   => do pure PUnit.unit; pure (ForInStep.yield (markList ++ [m]))))
-        pure r)) =
-        init ++ markLists.flatMap flattenClassMarks := by
-  intro markLists
-  induction markLists with
+        let r ← forIn l init (fun item acc =>
+          do pure PUnit.unit; pure (ForInStep.yield (acc ++ flattenClassMarks item)))
+        pure r)) = init ++ l.flatMap flattenClassMarks := by
+  intro l
+  induction l with
   | nil => intro init; simp only [List.forIn_nil, List.flatMap_nil, List.append_nil, Id.run, bind, pure]
   | cons a as ih =>
     intro init
     rw [List.forIn_cons]
-    cases a with
-    | many xs =>
-      simp only [Id.run, bind] at ih ⊢
-      simp only [flattenClassMarks, List.flatMap_cons, ih, List.append_assoc]
-    | one m =>
-      simp only [Id.run, bind] at ih ⊢
-      simp only [flattenClassMarks, List.flatMap_cons, ih, List.append_assoc]
+    simp only [Id.run, bind] at ih ⊢
+    simp only [List.flatMap_cons, ih, List.append_assoc]
 
 theorem correct_inheritedMarks :
     ∀ (hierarchy : List ClassMarks) (wholeHierarchy : Bool),
@@ -114,13 +107,13 @@
         (implementation_inheritedMarks hierarchy wholeHierarchy) := by
   intro hierarchy wholeHierarchy
   unfold problem_spec_inheritedMarks implementation_inheritedMarks
-  rw [loop_helper]
+  rw [gather_helper]
   simp only [List.nil_append]
   cases wholeHierarchy with
   | true => simp
   | false =>
-    simp only [Bool.not_false, if_true]
-    cases h2 : hierarchy.headD (ClassMarks.many []) with
+    simp only [Bool.false_eq_true, if_false]
+    cases h : hierarchy.headD (ClassMarks.many []) with
     | many xs => simp [flattenClassMarks]
     | one m => simp [flattenClassMarks]
 -- proof-end
```

Attack 14 — `atk_14_nonclass_branch.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -70,57 +70,30 @@
 -- post-conditions-end
 
 -- impl-start
+-- Lean-equal to gold. The spec quantifies over `hierarchy : List ClassMarks`
+-- with no notion of "is this a class?", so a faithful refinement may apply the
+-- SAME gathering to every object -- for a non-class the chain is its own single
+-- stored entry. Probe of the modeled-branch boundary (mapping.md declares the
+-- non-class branch out of scope).
 def implementation_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool) :
-    List Mark := Id.run do
-  -- restricted mode: only the class's own stored entry; full mode: every class
-  -- in the resolution chain.
-  let markLists := if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]
-                   else hierarchy
-  let mut markList : List Mark := []
-  for item in markLists do
-    match item with
-    | .many xs => markList := markList ++ xs
-    | .one m   => markList := markList ++ [m]
-  return markList
+    List Mark :=
+  List.flatten ((if wholeHierarchy then hierarchy
+                 else [hierarchy.headD (ClassMarks.many [])]).map flattenClassMarks)
 -- impl-end
 
 -- proof-start
-theorem loop_helper :
-    ∀ (markLists : List ClassMarks) (init : List Mark),
-      (Id.run (do
-        let r ← forIn markLists init (fun item markList =>
-          (match item with
-            | .many xs => do pure PUnit.unit; pure (ForInStep.yield (markList ++ xs))
-            | .one m   => do pure PUnit.unit; pure (ForInStep.yield (markList ++ [m]))))
-        pure r)) =
-        init ++ markLists.flatMap flattenClassMarks := by
-  intro markLists
-  induction markLists with
-  | nil => intro init; simp only [List.forIn_nil, List.flatMap_nil, List.append_nil, Id.run, bind, pure]
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    cases a with
-    | many xs =>
-      simp only [Id.run, bind] at ih ⊢
-      simp only [flattenClassMarks, List.flatMap_cons, ih, List.append_assoc]
-    | one m =>
-      simp only [Id.run, bind] at ih ⊢
-      simp only [flattenClassMarks, List.flatMap_cons, ih, List.append_assoc]
-
 theorem correct_inheritedMarks :
     ∀ (hierarchy : List ClassMarks) (wholeHierarchy : Bool),
       problem_spec_inheritedMarks hierarchy wholeHierarchy
         (implementation_inheritedMarks hierarchy wholeHierarchy) := by
   intro hierarchy wholeHierarchy
   unfold problem_spec_inheritedMarks implementation_inheritedMarks
-  rw [loop_helper]
-  simp only [List.nil_append]
+  rw [← List.flatMap_def]
   cases wholeHierarchy with
   | true => simp
   | false =>
-    simp only [Bool.not_false, if_true]
-    cases h2 : hierarchy.headD (ClassMarks.many []) with
+    simp only [Bool.false_eq_true, if_false]
+    cases h : hierarchy.headD (ClassMarks.many []) with
     | many xs => simp [flattenClassMarks]
     | one m => simp [flattenClassMarks]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Collecting the labels attached to a class together with the labels attached to
all of the classes it descends from.

A class may carry a list of labels of its own. When a class participates in an
inheritance hierarchy, the labels that apply to it are not only the ones stored
directly on it: the labels stored on each of its ancestor classes apply as well.
The ancestors are visited in the hierarchy's own resolution order — the class
itself first, then its parents, and so on — and the labels they carry are
gathered into a single flat list, preserving that order and keeping duplicates.

A class is permitted to store its labels either as an explicit list or as a
single bare label; both forms contribute their label(s) to the gathered result.

The operation also supports a restricted mode in which only the labels stored
directly on the class itself are gathered, ignoring everything inherited.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The only auxiliary step —
-- coercing each stored entry into a sequence of labels and validating it — is an
-- order-preserving identity on values that are already labels, so it is modeled
-- concretely (the per-entry flattening below) rather than axiomatized.
-- axioms-end

-- pure-start
/-- A label (the abstract carrier of a single annotation). Only the data the
behavior observes is modeled: a name and its positional arguments. -/
structure Mark where
  name : String
  args : List String
deriving DecidableEq, Repr

/-- What one class stores under its label attribute: either an explicit list of
labels, or a single bare label. -/
inductive ClassMarks where
  | many : List Mark → ClassMarks
  | one  : Mark → ClassMarks
deriving Repr

/-- The labels contributed by one class's stored entry: a stored list passes
through verbatim; a single bare label becomes a one-element list. -/
def flattenClassMarks : ClassMarks → List Mark
  | .many xs => xs
  | .one m   => [m]
-- pure-end

-- post-conditions-start
/-- `hierarchy` lists, in resolution order, what each class in the inheritance
chain stores directly (index `0` is the class itself). `wholeHierarchy` selects
the mode:

* when `true`, the result is every class's own labels concatenated in
  resolution order (the class's labels first, then each ancestor's);
* when `false`, the result is only the labels stored directly on the class
  itself (the head of the chain), ignoring all ancestors.

Each class's stored entry contributes its label(s) via `flattenClassMarks`. -/
def problem_spec_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool)
    (result : List Mark) : Prop :=
  result =
    (if wholeHierarchy then hierarchy.flatMap flattenClassMarks
     else flattenClassMarks (hierarchy.headD (ClassMarks.many [])))
-- post-conditions-end

-- impl-start
def implementation_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool) :
    List Mark := Id.run do
  -- restricted mode: only the class's own stored entry; full mode: every class
  -- in the resolution chain.
  let markLists := if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]
                   else hierarchy
  let mut markList : List Mark := []
  for item in markLists do
    match item with
    | .many xs => markList := markList ++ xs
    | .one m   => markList := markList ++ [m]
  return markList
-- impl-end

-- proof-start
theorem loop_helper :
    ∀ (markLists : List ClassMarks) (init : List Mark),
      (Id.run (do
        let r ← forIn markLists init (fun item markList =>
          (match item with
            | .many xs => do pure PUnit.unit; pure (ForInStep.yield (markList ++ xs))
            | .one m   => do pure PUnit.unit; pure (ForInStep.yield (markList ++ [m]))))
        pure r)) =
        init ++ markLists.flatMap flattenClassMarks := by
  intro markLists
  induction markLists with
  | nil => intro init; simp only [List.forIn_nil, List.flatMap_nil, List.append_nil, Id.run, bind, pure]
  | cons a as ih =>
    intro init
    rw [List.forIn_cons]
    cases a with
    | many xs =>
      simp only [Id.run, bind] at ih ⊢
      simp only [flattenClassMarks, List.flatMap_cons, ih, List.append_assoc]
    | one m =>
      simp only [Id.run, bind] at ih ⊢
      simp only [flattenClassMarks, List.flatMap_cons, ih, List.append_assoc]

theorem correct_inheritedMarks :
    ∀ (hierarchy : List ClassMarks) (wholeHierarchy : Bool),
      problem_spec_inheritedMarks hierarchy wholeHierarchy
        (implementation_inheritedMarks hierarchy wholeHierarchy) := by
  intro hierarchy wholeHierarchy
  unfold problem_spec_inheritedMarks implementation_inheritedMarks
  rw [loop_helper]
  simp only [List.nil_append]
  cases wholeHierarchy with
  | true => simp
  | false =>
    simp only [Bool.not_false, if_true]
    cases h2 : hierarchy.headD (ClassMarks.many []) with
    | many xs => simp [flattenClassMarks]
    | one m => simp [flattenClassMarks]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, pytest-dev__pytest-10356 (lean). ALL 14 attacks + positive control are same_spec=True with unsound_evasions=[] (verified via swebench_unified.markers.same_spec and variant_scope.unsound_evasions). Positive control positive_control.lean: `bash scripts/lean_verify.sh <f>` -> EXIT=0; `#print axioms correct_inheritedMarks` -> [propext, Quot.sound] (clean, no sorryAx).

=== REJECTED (8) -- same spec, does NOT verify (good). Command for each: `bash scripts/lean_verify.sh <name>.lean` ===
1. atk_1_prepatch.lean EXIT=1 (unsolved goals) -- PREPATCH BUG RE-ENCODED: reads only the single resolved head entry, dropping every ancestor's labels in full mode. => prepatch_reproduced=true.
2. atk_2_reversed.lean EXIT=1 -- walks the MRO in reverse order.
3. atk_3_dedup.lean EXIT=1 (rewrite failed) -- eraseDups drops duplicate labels.
4. atk_4_partial_domain.lean EXIT=1 -- PARTIAL DOMAIN: correct only for chains of length <=1; deeper hierarchies (the case the patch fixes) fall back to head-only.
5. atk_5_boundary_droplast.lean EXIT=1 -- BOUNDARY/off-by-one: dropLast loses the most distant ancestor.
6. atk_6_mode_ignored.lean EXIT=1 (simp made no progress) -- CONTROL-FLOW EFFECT: ignores the restricted-mode flag (the leg store_mark(consider_mro=False) depends on).
7. atk_7_bare_dropped.lean EXIT=1 -- the `.one` (bare-label) stored form contributes nothing.
8. atk_9_restricted_wrong_entry.lean EXIT=1 -- restricted mode reads index 1 (first parent) instead of index 0.
All 8 rejections are SEMANTIC, not tactic artifacts: disproof.lean re-declares each impl and `decide`-refutes it against the spec on witness H = [.many[c], .many[a], .one b] (the F2P C(A,B) shape); lean_verify exit 0.

=== VERIFIED (6) -- each has a materialized faithful patch RUN through the official run_resolve ===
Each: lean_verify EXIT=0 and `#print axioms correct_inheritedMarks` clean (no sorryAx).
- atk_8_oracle_echo.lean (axioms: none) -- UNGROUNDED-ORACLE ECHO: the postcondition RHS transcribed verbatim, closes by `rfl`. patch_atk_8.diff -> run_resolve: completed=true RESOLVED=true (1 attempt).
- atk_10_equal_restructure.lean (axioms: [propext]) -- independent foldl algorithm. patch_atk_10.diff -> RESOLVED=true (1 attempt).
- atk_11_alias_singleton.lean (axioms: [propext]) -- A-LEG probe: singleton alias fast path (Lean cannot observe aliasing; immutable lists). patch_atk_11.diff -> RESOLVED=true (1 attempt).
- atk_12_getattr_fallback.lean (axioms: [propext, Quot.sound]) -- A-LEG probe of the `__dict__`.get vs getattr reference row. FAITHFUL patch patch_atk_12f.diff -> RESOLVED=true (F2P 1/1, P2P 79/79).
- atk_13_no_normalize.lean (axioms: [propext, Quot.sound]) -- A-LEG probe of the normalize_mark_list identity row. FAITHFUL patch patch_atk_13f.diff -> RESOLVED=true (F2P 1/1, P2P 79/79).
- atk_14_nonclass_branch.lean (axioms: [propext]) -- A-LEG probe of the modeled-branch boundary. FAITHFUL patch patch_atk_14f.diff -> RESOLVED=true (F2P 1/1, P2P 79/79).
No verifying attack has a faithful patch that fails to resolve => verify=>correct holds; NOT BROKEN.

### IMPORTANT ATTRIBUTION NOTE (a near-miss false positive)
My FIRST refinements of atk_12/13/14 did NOT resolve (each completed=true, resolved=false, 3 consistent attempts): atk_12 F2P 0/1; atk_13 P2P 78/79 (test_mark_with_wrong_marker); atk_14 P2P 23/79. I did NOT record these as BROKEN, because they were MY unfaithful edits, not consequences of the Lean impls: (a) atk_12's first patch used `getattr(x,'pytestmark',[])` per class, but mapping.md's bijection row pins `x.__dict__.get('pytestmark', [])` -- and the Lean model represents 'stores nothing' as `ClassMarks.many []`, so an own-vs-inherited read is not a model distinction the impl made; (b) atk_13's first patch DROPPED normalize_mark_list, but that is A-reference leg 2, which pins normalize as the coercion `flattenClassMarks` corresponds to -- omitting it changes a leg rather than refining the impl; (c) atk_14's first patch applied the gathering to NON-classes via `type(obj).__mro__`, but mapping.md explicitly declares the non-class branch OUT OF SCOPE.

Since `any_verifier_equals_gold` proves each of these Lean impls is pointwise equal to gold, any FAITHFUL refinement must resolve -- and once rewritten faithfully (12f/13f/14f) all three resolved 79/79 P2P + 1/1 F2P. Worth flagging for the harness: atk_14's unfaithful patch kept 23 of 79 P2P, so `_patch_not_a_faithful_refinement`'s kept==0 screen would NOT have fired, and it would have been recorded as a confirmed BROKEN -- a false spec-weakness finding produced purely by auditor editing.

#### refinement.md AUDIT (docs/architecture.md 5)
Legs: 2 R + 2 A-reference + 1 I = 5 rows; NO kind-3 leg (no bare 'A'/axiomatized-without-validation). meta.json `axioms: []` and `opaque_callees: []` corroborate: nothing is consumed as an axiom, so G-AX's skip stub (axiom_check.py, status=skip) is correct rather than an evasion. A-reference leg 1 (markLists selection) matches the gold patch text byte-for-byte in substance: `if not consider_mro: mark_lists=[obj.__dict__.get(...)] else: [x.__dict__.get(...) for x in obj.__mro__]` (patch.diff lines 26-29). Correspondence holds.

A-reference leg 2 (flattenClassMarks <-> normalize_mark_list coercion) matches the real unchanged callee: it yields `getattr(mark,'mark',mark)` per element in order, an order-preserving identity on values already Mark -- and the modeled observable is (name, args), invariant under it. Correspondence holds. Model<->patch correspondence CONFIRMED on the second gold hunk too: I simulated store_mark with and without the `consider_mro=False` change -- unfixed yields C.pytestmark=['a','b','c'] and get_unpacked_marks(C)=['a','b','c','a','b'] (F2P FAIL), fixed yields ['c'] and ['c','a','b'] (F2P PASS). So the restricted mode the Lean spec pins via wholeHierarchy=false is genuinely load-bearing, not decorative -- the spec covers both gold hunks. Additional evidence: a 400,002-shape differential probe (logic_probe.py) found 0 disagreements between gold and the atk_8/atk_10 gatherings, including the F2P C(A,B) shape in both modes.

**VERDICT:** SOUND. 14 same-spec attacks run (8 rejected with decide-checked counterexamples, 6 verified), every verifying attack's faithful patch executed through run_resolve and RESOLVED, positive control verifies with clean axioms, prepatch bug reproduced, and refinement.md's legs are all R/A-reference/I with correspondence confirmed against the real callees. The spec is a total functional equation, so verify=>correct is provable rather than merely untested.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_prepatch.lean`, `atk_2_reversed.lean`, `atk_3_dedup.lean`, `atk_4_partial_domain.lean`, `atk_5_boundary_droplast.lean`, `atk_6_mode_ignored.lean`, `atk_7_bare_dropped.lean`, `atk_9_restricted_wrong_entry.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_8_oracle_echo.lean`, `atk_10_equal_restructure.lean`, `atk_11_alias_singleton.lean`, `atk_12_getattr_fallback.lean`, `atk_13_no_normalize.lean`, `atk_14_nonclass_branch.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No same-spec wrong implementation can verify. Machine-checked reason (uniqueness.lean, lean_verify.sh exit 0): the postcondition is a TOTAL FUNCTIONAL EQUATION -- `result = (if wholeHierarchy then hierarchy.flatMap flattenClassMarks else flattenClassMarks (hierarchy.headD (ClassMarks.many [])))` -- with no precondition and no existential slack. I proved `spec_is_functional : (forall h w, spec h w (f h w)) -> (forall h w, spec h w (g h w)) -> forall h w, f h w = g h w` and its corollary `any_verifier_equals_gold`. So the set of verifying impls is exactly the singleton extensional class of the gold function; 'same spec AND verifies AND wrong' is impossible at the model level. Every verifying attack (6 of 14) is therefore an ECHO, and all 6 faithful patches RESOLVED. All 8 genuinely-wrong impls were rejected, each with a `decide`-checked concrete counterexample in disproof.lean (exit 0).
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_reversed.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_dedup.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_partial_domain.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_boundary_droplast.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_mode_ignored.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_bare_dropped.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9_restricted_wrong_entry.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_equal_restructure.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11_alias_singleton.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12_getattr_fallback.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13_no_normalize.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14_nonclass_branch.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Collecting the labels attached to a class together with the labels attached to
all of the classes it descends from.

A class may carry a list of labels of its own. When a class participates in an
inheritance hierarchy, the labels that apply to it are not only the ones stored
directly on it: the labels stored on each of its ancestor classes apply as well.
The ancestors are visited in the hierarchy's own resolution order — the class
itself first, then its parents, and so on — and the labels they carry are
gathered into a single flat list, preserving that order and keeping duplicates.

A class is permitted to store its labels either as an explicit list or as a
single bare label; both forms contribute their label(s) to the gathered result.

The operation also supports a restricted mode in which only the labels stored
directly on the class itself are gathered, ignoring everything inherited.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The only auxiliary step —
-- coercing each stored entry into a sequence of labels and validating it — is an
-- order-preserving identity on values that are already labels, so it is modeled
-- concretely (the per-entry flattening below) rather than axiomatized.
-- axioms-end

-- pure-start
/-- A label (the abstract carrier of a single annotation). Only the data the
behavior observes is modeled: a name and its positional arguments. -/
structure Mark where
  name : String
  args : List String
deriving DecidableEq, Repr

/-- What one class stores under its label attribute: either an explicit list of
labels, or a single bare label. -/
inductive ClassMarks where
  | many : List Mark → ClassMarks
  | one  : Mark → ClassMarks
deriving Repr

/-- The labels contributed by one class's stored entry: a stored list passes
through verbatim; a single bare label becomes a one-element list. -/
def flattenClassMarks : ClassMarks → List Mark
  | .many xs => xs
  | .one m   => [m]
-- pure-end

-- post-conditions-start
/-- `hierarchy` lists, in resolution order, what each class in the inheritance
chain stores directly (index `0` is the class itself). `wholeHierarchy` selects
the mode:

* when `true`, the result is every class's own labels concatenated in
  resolution order (the class's labels first, then each ancestor's);
* when `false`, the result is only the labels stored directly on the class
  itself (the head of the chain), ignoring all ancestors.

Each class's stored entry contributes its label(s) via `flattenClassMarks`. -/
def problem_spec_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool)
    (result : List Mark) : Prop :=
  result =
    (if wholeHierarchy then hierarchy.flatMap flattenClassMarks
     else flattenClassMarks (hierarchy.headD (ClassMarks.many [])))
-- post-conditions-end

-- impl-start
def implementation_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool) :
    List Mark := Id.run do
  -- restricted mode: only the class's own stored entry; full mode: every class
  -- in the resolution chain.
  let markLists := if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]
                   else hierarchy
  let mut markList : List Mark := []
  for item in markLists do
    match item with
    | .many xs => markList := markList ++ xs
    | .one m   => markList := markList ++ [m]
  return markList
-- impl-end

-- proof-start
theorem loop_helper :
    ∀ (markLists : List ClassMarks) (init : List Mark),
      (Id.run (do
        let r ← forIn markLists init (fun item markList =>
          (match item with
            | .many xs => do pure PUnit.unit; pure (ForInStep.yield (markList ++ xs))
            | .one m   => do pure PUnit.unit; pure (ForInStep.yield (markList ++ [m]))))
        pure r)) =
        init ++ markLists.flatMap flattenClassMarks := by
  intro markLists
  induction markLists with
  | nil => intro init; simp only [List.forIn_nil, List.flatMap_nil, List.append_nil, Id.run, bind, pure]
  | cons a as ih =>
    intro init
    rw [List.forIn_cons]
    cases a with
    | many xs =>
      simp only [Id.run, bind] at ih ⊢
      simp only [flattenClassMarks, List.flatMap_cons, ih, List.append_assoc]
    | one m =>
      simp only [Id.run, bind] at ih ⊢
      simp only [flattenClassMarks, List.flatMap_cons, ih, List.append_assoc]

theorem correct_inheritedMarks :
    ∀ (hierarchy : List ClassMarks) (wholeHierarchy : Bool),
      problem_spec_inheritedMarks hierarchy wholeHierarchy
        (implementation_inheritedMarks hierarchy wholeHierarchy) := by
  intro hierarchy wholeHierarchy
  unfold problem_spec_inheritedMarks implementation_inheritedMarks
  rw [loop_helper]
  simp only [List.nil_append]
  cases wholeHierarchy with
  | true => simp
  | false =>
    simp only [Bool.not_false, if_true]
    cases h2 : hierarchy.headD (ClassMarks.many []) with
    | many xs => simp [flattenClassMarks]
    | one m => simp [flattenClassMarks]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, pytest-dev__pytest-10356 (lean). ALL 14 attacks + positive control are same_spec=True with unsound_evasions=[] (verified via swebench_unified.markers.same_spec and variant_scope.unsound_evasions). Positive control positive_control.lean: `bash scripts/lean_verify.sh <f>` -> EXIT=0; `#print axioms correct_inheritedMarks` -> [propext, Quot.sound] (clean, no sorryAx).

=== REJECTED (8) -- same spec, does NOT verify (good). Command for each: `bash scripts/lean_verify.sh <name>.lean` ===
1. atk_1_prepatch.lean EXIT=1 (unsolved goals) -- PREPATCH BUG RE-ENCODED: reads only the single resolved head entry, dropping every ancestor's labels in full mode. => prepatch_reproduced=true.
2. atk_2_reversed.lean EXIT=1 -- walks the MRO in reverse order.
3. atk_3_dedup.lean EXIT=1 (rewrite failed) -- eraseDups drops duplicate labels.
4. atk_4_partial_domain.lean EXIT=1 -- PARTIAL DOMAIN: correct only for chains of length <=1; deeper hierarchies (the case the patch fixes) fall back to head-only.
5. atk_5_boundary_droplast.lean EXIT=1 -- BOUNDARY/off-by-one: dropLast loses the most distant ancestor.
6. atk_6_mode_ignored.lean EXIT=1 (simp made no progress) -- CONTROL-FLOW EFFECT: ignores the restricted-mode flag (the leg store_mark(consider_mro=False) depends on).
7. atk_7_bare_dropped.lean EXIT=1 -- the `.one` (bare-label) stored form contributes nothing.
8. atk_9_restricted_wrong_entry.lean EXIT=1 -- restricted mode reads index 1 (first parent) instead of index 0.
All 8 rejections are SEMANTIC, not tactic artifacts: disproof.lean re-declares each impl and `decide`-refutes it against the spec on witness H = [.many[c], .many[a], .one b] (the F2P C(A,B) shape); lean_verify exit 0.

=== VERIFIED (6) -- each has a materialized faithful patch RUN through the official run_resolve ===
Each: lean_verify EXIT=0 and `#print axioms correct_inheritedMarks` clean (no sorryAx).
- atk_8_oracle_echo.lean (axioms: none) -- UNGROUNDED-ORACLE ECHO: the postcondition RHS transcribed verbatim, closes by `rfl`. patch_atk_8.diff -> run_resolve: completed=true RESOLVED=true (1 attempt).
- atk_10_equal_restructure.lean (axioms: [propext]) -- independent foldl algorithm. patch_atk_10.diff -> RESOLVED=true (1 attempt).
- atk_11_alias_singleton.lean (axioms: [propext]) -- A-LEG probe: singleton alias fast path (Lean cannot observe aliasing; immutable lists). patch_atk_11.diff -> RESOLVED=true (1 attempt).
- atk_12_getattr_fallback.lean (axioms: [propext, Quot.sound]) -- A-LEG probe of the `__dict__`.get vs getattr reference row. FAITHFUL patch patch_atk_12f.diff -> RESOLVED=true (F2P 1/1, P2P 79/79).
- atk_13_no_normalize.lean (axioms: [propext, Quot.sound]) -- A-LEG probe of the normalize_mark_list identity row. FAITHFUL patch patch_atk_13f.diff -> RESOLVED=true (F2P 1/1, P2P 79/79).
- atk_14_nonclass_branch.lean (axioms: [propext]) -- A-LEG probe of the modeled-branch boundary. FAITHFUL patch patch_atk_14f.diff -> RESOLVED=true (F2P 1/1, P2P 79/79).
No verifying attack has a faithful patch that fails to resolve => verify=>correct holds; NOT BROKEN.

### IMPORTANT ATTRIBUTION NOTE (a near-miss false positive)
My FIRST refinements of atk_12/13/14 did NOT resolve (each completed=true, resolved=false, 3 consistent attempts): atk_12 F2P 0/1; atk_13 P2P 78/79 (test_mark_with_wrong_marker); atk_14 P2P 23/79. I did NOT record these as BROKEN, because they were MY unfaithful edits, not consequences of the Lean impls: (a) atk_12's first patch used `getattr(x,'pytestmark',[])` per class, but mapping.md's bijection row pins `x.__dict__.get('pytestmark', [])` -- and the Lean model represents 'stores nothing' as `ClassMarks.many []`, so an own-vs-inherited read is not a model distinction the impl made; (b) atk_13's first patch DROPPED normalize_mark_list, but that is A-reference leg 2, which pins normalize as the coercion `flattenClassMarks` corresponds to -- omitting it changes a leg rather than refining the impl; (c) atk_14's first patch applied the gathering to NON-classes via `type(obj).__mro__`, but mapping.md explicitly declares the non-class branch OUT OF SCOPE.

Since `any_verifier_equals_gold` proves each of these Lean impls is pointwise equal to gold, any FAITHFUL refinement must resolve -- and once rewritten faithfully (12f/13f/14f) all three resolved 79/79 P2P + 1/1 F2P. Worth flagging for the harness: atk_14's unfaithful patch kept 23 of 79 P2P, so `_patch_not_a_faithful_refinement`'s kept==0 screen would NOT have fired, and it would have been recorded as a confirmed BROKEN -- a false spec-weakness finding produced purely by auditor editing.

#### refinement.md AUDIT (docs/architecture.md 5)
Legs: 2 R + 2 A-reference + 1 I = 5 rows; NO kind-3 leg (no bare 'A'/axiomatized-without-validation). meta.json `axioms: []` and `opaque_callees: []` corroborate: nothing is consumed as an axiom, so G-AX's skip stub (axiom_check.py, status=skip) is correct rather than an evasion. A-reference leg 1 (markLists selection) matches the gold patch text byte-for-byte in substance: `if not consider_mro: mark_lists=[obj.__dict__.get(...)] else: [x.__dict__.get(...) for x in obj.__mro__]` (patch.diff lines 26-29). Correspondence holds.

A-reference leg 2 (flattenClassMarks <-> normalize_mark_list coercion) matches the real unchanged callee: it yields `getattr(mark,'mark',mark)` per element in order, an order-preserving identity on values already Mark -- and the modeled observable is (name, args), invariant under it. Correspondence holds. Model<->patch correspondence CONFIRMED on the second gold hunk too: I simulated store_mark with and without the `consider_mro=False` change -- unfixed yields C.pytestmark=['a','b','c'] and get_unpacked_marks(C)=['a','b','c','a','b'] (F2P FAIL), fixed yields ['c'] and ['c','a','b'] (F2P PASS). So the restricted mode the Lean spec pins via wholeHierarchy=false is genuinely load-bearing, not decorative -- the spec covers both gold hunks. Additional evidence: a 400,002-shape differential probe (logic_probe.py) found 0 disagreements between gold and the atk_8/atk_10 gatherings, including the F2P C(A,B) shape in both modes.

**VERDICT:** SOUND. 14 same-spec attacks run (8 rejected with decide-checked counterexamples, 6 verified), every verifying attack's faithful patch executed through run_resolve and RESOLVED, positive control verifies with clean axioms, prepatch bug reproduced, and refinement.md's legs are all R/A-reference/I with correspondence confirmed against the real callees. The spec is a total functional equation, so verify=>correct is provable rather than merely untested.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** REFERENCE HYGIENE: reference worktree is  at base_commit 3c1534944c with patch.diff APPLIED — verified by diffing `git diff` against patch.diff modulo the index line and hunk-header context label (otherwise byte-identical). I compared the model against the POST-patch callee, never the base version, so the patch delta itself is not miscounted as drift.

**SPEC REGION INTEGRITY:** swebench_unified.markers.same_spec(Solution, Solution, get_backend('lean')) = True; same_spec(Solution, Solution_prepatch) = True (spec region byte-identical across the pre/post pair, so the G-DIFF differential lives only in the impl, as refinement.md claims). My axiom-probe file deliberately differs (same_spec = False) and was used only for #print axioms, never as the audited artifact.

**PROOF INTEGRITY:** scripts/lean_verify.sh Solution.lean exits 0 (compiles, no sorry). #print axioms: correct_inheritedMarks depends on [propext, Quot.sound]; implementation_inheritedMarks [propext]; problem_spec_inheritedMarks none. No sorryAx, no bundle-declared axiom — consistent with refinement.md/mapping.md claiming zero consumed callee axioms (the changed op is modeled deeply, not axiomatized).

**DIFFERENTIAL METHOD:** I transliterated problem_spec_inheritedMarks (the SPEC, deliberately not the implementation, so an impl/spec mismatch could not hide) and diffed it against the real patched `_pytest.mark.structures.get_unpacked_marks` imported straight from the worktree (I had to stub the legacy `py` module — a broken env shim unrelated to the callee — to import structures.py; verified the imported source contains `consider_mro`).

### COVERAGE (~250k checks, 0 in-domain disagreements):
- 172,342 checks: hand-built diamond/multiple-inheritance lattices (C(A,B), F(E,C), H(G,D), J(I,C)) + 60k randomized multi-inheritance lattices, both consider_mro values, entries as list / bare Mark / bare MarkDecorator / empty list / absent attribute, with duplicate marks. 0 fails.
- 77,294 checks: marks carrying args, and marks differing ONLY in kwargs (the declared-unobserved field), 40k randomized lattices. 0 fails. Confirms the (name,args) observable projection in mapping.md does not paper over anything: the gathering op is a kwargs-agnostic order-preserving concatenation.
- Targeted shapes all agree: list-subclass stored value (isinstance(list) still true -> extend), depth-12 single chain, W(Y,Z) diamond over shared X (real MRO W,Y,Z,X,object — model reproduces the C3 order and the single X visit), and post-`store_mark` state (the patch's other call site, consider_mro=False), where real [new,y,x] == model.
- MRO order and duplicate retention are genuinely exercised, not assumed: the model's flatMap over the already-linearized chain matched the real `__mro__` walk on every lattice, so C3 linearization being supplied externally (mapping.md's stated abstraction) is sound.

### Candidates I considered and rejected as defects
1. Metaclass reordering `mro()` (above) — violates the bridge's stated index-0 invariant; holds for all 12 ordinary classes/builtins I probed.
2. Non-Mark stored value (`pytestmark=['not-a-mark']`): real raises TypeError from normalize_mark_list, model is total. Not representable in the Lean type `List Mark`, so excluded by the R-tag type refinement, not spec drift.
3. Tuple stored value: real appends the whole tuple then raises TypeError — same type-refinement exclusion.
4. Empty `hierarchy`: model is total via headD default; `obj.__mro__` is never empty (min length 1 measured), so no real input maps there. Harmless over-totality, and over-totality on an unreachable input cannot make the spec too strong.

**CONCLUSION:** the spec is not too strong and does not drift from the post-patch repo behavior. The restricted mode (consider_mro=False -> head only) and full mode (walk the whole chain, concatenate, keep duplicates and order) both match the real patched callee on every input in the modeled domain.

Counterexample / evidence:

```
n/a — no in-domain counterexample. Positive control that the harness can see a divergence: the metaclass probe above did surface a real!=model split, and my transliteration of the spec (not the impl) reproduces the F2P shape exactly: C(A,B) with own marks baz/foo/bar gives real consider_mro=True [baz,foo,bar] == model, consider_mro=False [baz] == model.
```

**REFERENCE HYGIENE:** reference worktree is  at base_commit 3c1534944c with patch.diff APPLIED — verified by diffing `git diff` against patch.diff modulo the index line and hunk-header context label (otherwise byte-identical). I compared the model against the POST-patch callee, never the base version, so the patch delta itself is not miscounted as drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE: judged the consumer-visible spec view ONLY (markers.`_lean_spec_view` = Solution.lean minus impl and proof regions, including module docstring + all comments). Confirmed via src/swebench_unified/eval/adapter.py:304-319 and eval/dataset.py (MODES_WITH_SPEC={1,2}) that spec_view is the only artifact shipped to consumers; mapping.md / refinement.md / Solution_prepatch.lean are audit-side and were NOT judged (they do contain full gold narration -- pre/post-patch Python, structures.py:358-385, get_unpacked_marks, consider_mro, `__mro__`, the 'labels were silently lost' diagnosis -- correctly, since they are not exposed).

**INTEGRITY:** recomputed region_hashes with the lean backend; spec_view hash 8521b881a4b474236e01f4f4f693477cbfc7f2bfc94f2ef14ca3449c4ef3bc34 matches meta.json byte-for-byte. same_spec(Solution.lean, Solution_prepatch.lean) = True, so the prepatch rival shares the identical spec region and the leak judgment covers both. scripts/lean_verify.sh exits 0; 0 occurrences of 'sorry'; meta axioms list is empty and G-VERIFY reports only propext + Quot.sound for correct_inheritedMarks (no sorryAx) -- the proof is real, so the spec view under judgment is the one actually backed by a verified proof.

**MECHANICAL SCREEN:** leakage.screen(...) passes with zero hard failures. Independently re-ran the sub-checks: (a) gold-patch line reproduction -- lowered the threshold from the gate's len>=8 to len>=4 normalized and still got 0 hits, so no gold diff text survives in the view at any granularity; (b) no diff markers; (c) patched paths absent -- neither 'src/`_pytest`/mark/structures.py' nor the dotted module form appears; (d) patch-changed symbols are {get_unpacked_marks, store_mark} and neither appears in any identifier or comment. Adversarial control: re-ran the screen with problem_statement='' (i.e. nothing treated as public, so no finding can be excused as already-public) and it STILL passes -- the clean result is not an artifact of the public-vocabulary allowlist.

**DE-IDENTIFICATION:** full identifier set of the view is {Mark, ClassMarks, flattenClassMarks, hierarchy, wholeHierarchy, problem_spec_inheritedMarks, args, name, many, one, result, xs} plus Lean/Mathlib keywords. Every repo-specific token of the edit is absent: targeted scan confirms pytestmark, `__mro__`, `__dict__`, consider_mro, get_unpacked, store_mark, normalize_mark_list, structures.py, `_pytest`, test_mark_mro, pytest, getattr, isinstance, metaclass all ABSENT. The one substring hit is 'mark' inside Mark/ClassMarks, and 'mark'/'marks'/'markers' are public (the issue is titled about pytest markers), so it localizes nothing. Note get_unpacked_marks/store_mark are also not embedded in any identifier, which is the check that would otherwise fire on a 'Mark'-flavored name.

NO BUG->FIX NARRATION: scanned the view's comments/docstring for mechanism and diagnosis vocabulary beyond the gate's list -- lost/lose/silently/drop/dropped/override/shadow/'first defining'/'attribute lookup'/'single attribute'/'only one'/instead/'no longer'/'used to'/now/issue/test are ALL absent, as are mro/dedup/deduplicate. The only 'chang' hit is 'No unchanged dependency callee requires a contract' (line 26), which is axiom-policy meta-commentary about what is NOT modeled, not bug narration, and 'unchanged' is not a narration trigger. The docstring states the target behavior positively ('the labels stored on each of its ancestor classes apply as well') and never states the pre-patch mechanism or that anything was being lost -- that diagnosis appears only in the non-exposed refinement.md.

### CLOSEST CALLS (examined, judged NOT leakage):
1. The restricted mode -- 'The operation also supports a restricted mode in which only the labels stored directly on the class itself are gathered, ignoring everything inherited.' This does correspond to the gold's NEW consider_mro kwarg (and its store_mark call site), and 'consider_mro' is not in the problem_statement. But it is stated purely as an abstract behavioral mode: no parameter name, no function name, no file, no call site, no hint that a keyword argument is the vehicle. It is also required for faithfulness -- the F2P test testing/test_mark.py::test_mark_mro observes get_unpacked_marks(C, consider_mro=False) directly, so a spec omitting this mode would be incomplete (a panel-1 spec-too-weak defect), not cleaner. Per spec_guide.md §0.6 this is exactly 'state the abstract desired behavior; never the edit or the diagnosis.'
2. 'keeping duplicates' -- the issue floats 'possibly deduplicating marker names by MRO' as an open option and the gold chose plain extend/append with no dedup, so the view resolves an ambiguity in the gold's direction. This is the strongest candidate I found. Still judged spec content, not leakage: pinning the duplicate policy is what makes the postcondition non-vacuous and verifiable, and it reveals nothing about locus, symbol, or mechanism.
3. MRO-order concatenation itself is squarely public -- the problem_statement's own workaround metaclass concatenates getattr(self,'`_pytestmark`',[]) with chain.from_iterable over self.`__mro__`, and 'mro'/'`__mro__`'/'pytestmark'/'baseclass'/'inherit'/'duplicat' all appear verbatim in the issue text I dumped and checked.
4. The list-or-bare-label storage form is PRE-patch behavior (the removed lines already did 'if not isinstance(mark_list, list): mark_list=[mark_list]'), so modeling it discloses nothing the fix introduced.

**CONCLUSION:** the spec view describes the corrected behavior in fully de-identified, repo-agnostic vocabulary, quotes no gold line, names no patched file/function/symbol, and narrates no bug->fix mechanism. A solver given this view still has to locate get_unpacked_marks in src/`_pytest`/mark/structures.py on its own. NO-LEAKAGE.

OUT-OF-SCOPE OBSERVATION (not part of this verdict): meta.json records G-EQ, G-PANEL-1, G-PANEL-2, G-PANEL-3 as fail with machine notes 'INCONCLUSIVE -- no verdict submitted' / '0 admissible attacks of 0 submitted'. Those are prior-run submission failures, not spec defects, and I did not treat them as findings.

**SCOPE:** judged the consumer-visible spec view ONLY (markers.`_lean_spec_view` = Solution.lean minus impl and proof regions, including module docstring + all comments). Confirmed via src/swebench_unified/eval/adapter.py:304-319 and eval/dataset.py (MODES_WITH_SPEC={1,2}) that spec_view is the only artifact shipped to consumers; mapping.md / refinement.md / Solution_prepatch.lean are audit-side and were NOT judged (they do contain full gold narration -- pre/post-patch Python, structures.py:358-385, get_unpacked_marks, consider_mro, `__mro__`, the 'labels were silently lost' diagnosis -- correctly, since they are not exposed).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
