# P2 adversarial audit — matplotlib__matplotlib-24970

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,96 +54,27 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The indices are recorded in a container whose value type is widened so it
-can always hold a reserved slot number, independently of the input value type's
-capacity `M`. The reserved slot numbers therefore always fit and the conversion
-never fails. -/
+
 def implementation_index (N M : Nat) (xs : List Int) :
     Except Unit (List Nat) := Id.run do
   let mut out : List Nat := []
   for x in xs do
     let mut idx : Int := x
-    -- send values above the valid range to the `over` slot first, then values
-    -- below it to the `under` slot
     if idx > (N : Int) - 1 then
       idx := (N : Int) + 1
     if idx < 0 then
       idx := (N : Int)
+    if idx ≥ (M : Int) then
+      return Except.error ()
     out := out ++ [idx.toNat]
   return Except.ok out
 -- impl-end
 
 -- proof-start
--- The desugared loop body equals a clean body that appends `desiredIndex N x`.
-theorem body_eq_index (N : Nat) (x : Int) (r : List Nat) :
-    (if x > (N:Int) - 1 then
-        (if (N:Int) + 1 < 0 then ForInStep.yield (r ++ [((N:Int)).toNat])
-         else ForInStep.yield (r ++ [((N:Int) + 1).toNat]))
-      else
-        (if x < 0 then ForInStep.yield (r ++ [((N:Int)).toNat])
-         else ForInStep.yield (r ++ [x.toNat])))
-      = ForInStep.yield (r ++ [desiredIndex N x]) := by
-  have hidx : desiredIndex N x =
-      (if x > (N:Int) - 1 then
-        (if (N:Int) + 1 < 0 then ((N:Int)).toNat else ((N:Int) + 1).toNat)
-       else
-        (if x < 0 then ((N:Int)).toNat else x.toNat)) := by
-    unfold desiredIndex
-    by_cases h1 : x > (N:Int) - 1
-    · have hneg : ¬ ((N:Int) + 1 < 0) := by omega
-      have hx0 : ¬ (x < 0) := by omega
-      have hxN : (N:Int) ≤ x := by omega
-      simp only [h1, hneg, hx0, hxN, if_true, if_false]; omega
-    · have hxN : ¬ ((N:Int) ≤ x) := by omega
-      by_cases h2 : x < 0
-      · simp only [h1, h2, hxN, if_true, if_false]; omega
-      · simp only [h1, h2, hxN, if_false]
-  rw [hidx]
-  by_cases h1 : x > (N:Int) - 1 <;> by_cases h2 : (N:Int) + 1 < 0 <;>
-    by_cases h3 : x < 0 <;> simp only [h1, h2, h3, if_true, if_false]
-
-theorem helper_index (N : Nat) (xs : List Int) (init : List Nat) :
-    (Id.run (forIn xs init (fun x r =>
-        ForInStep.yield (r ++ [desiredIndex N x]))) : List Nat)
-      = init ++ xs.map (desiredIndex N) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons, List.append_assoc]
 
 theorem correct_index :
     ∀ (N M : Nat) (xs : List Int),
       problem_spec_index N xs (implementation_index N M xs) := by
   intro N M xs
-  refine ⟨xs.map (desiredIndex N), ?_, ?_, ?_⟩
-  · unfold implementation_index
-    simp only [Id.run]
-    have hbody : (forIn xs ([]:List Nat) (fun x r =>
-        if x > (N:Int) - 1 then do
-          pure PUnit.unit
-          if (N:Int)+1 < 0 then do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)).toNat]))
-            else do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)+1).toNat]))
-        else do
-          pure PUnit.unit
-          if x < 0 then do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)).toNat]))
-            else do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [x.toNat]))) : Id (List Nat))
-      = (forIn xs ([]:List Nat) (fun x r =>
-        ForInStep.yield (r ++ [desiredIndex N x])) : Id (List Nat)) := by
-      congr 1
-      funext x r
-      simp only [bind, pure]
-      exact body_eq_index N x r
-    rw [hbody]
-    have := helper_index N xs []
-    simp only [Id.run] at this
-    rw [this]; rfl
-  · simp
-  · intro i hi
-    rw [List.getD_eq_getElem?_getD, List.getD_eq_getElem?_getD]
-    simp only [List.getElem?_map]
-    rw [List.getElem?_eq_getElem hi]
-    simp
+  sorry
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,92 +54,19 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The indices are recorded in a container whose value type is widened so it
-can always hold a reserved slot number, independently of the input value type's
-capacity `M`. The reserved slot numbers therefore always fit and the conversion
-never fails. -/
+
 def implementation_index (N M : Nat) (xs : List Int) :
-    Except Unit (List Nat) := Id.run do
-  let mut out : List Nat := []
-  for x in xs do
-    let mut idx : Int := x
-    -- send values above the valid range to the `over` slot first, then values
-    -- below it to the `under` slot
-    if idx > (N : Int) - 1 then
-      idx := (N : Int) + 1
-    if idx < 0 then
-      idx := (N : Int)
-    out := out ++ [idx.toNat]
-  return Except.ok out
+    Except Unit (List Nat) :=
+  Except.ok (xs.map (fun x => if x < 0 ∨ (N:Int) ≤ x then N - 1 else x.toNat))
 -- impl-end
 
 -- proof-start
--- The desugared loop body equals a clean body that appends `desiredIndex N x`.
-theorem body_eq_index (N : Nat) (x : Int) (r : List Nat) :
-    (if x > (N:Int) - 1 then
-        (if (N:Int) + 1 < 0 then ForInStep.yield (r ++ [((N:Int)).toNat])
-         else ForInStep.yield (r ++ [((N:Int) + 1).toNat]))
-      else
-        (if x < 0 then ForInStep.yield (r ++ [((N:Int)).toNat])
-         else ForInStep.yield (r ++ [x.toNat])))
-      = ForInStep.yield (r ++ [desiredIndex N x]) := by
-  have hidx : desiredIndex N x =
-      (if x > (N:Int) - 1 then
-        (if (N:Int) + 1 < 0 then ((N:Int)).toNat else ((N:Int) + 1).toNat)
-       else
-        (if x < 0 then ((N:Int)).toNat else x.toNat)) := by
-    unfold desiredIndex
-    by_cases h1 : x > (N:Int) - 1
-    · have hneg : ¬ ((N:Int) + 1 < 0) := by omega
-      have hx0 : ¬ (x < 0) := by omega
-      have hxN : (N:Int) ≤ x := by omega
-      simp only [h1, hneg, hx0, hxN, if_true, if_false]; omega
-    · have hxN : ¬ ((N:Int) ≤ x) := by omega
-      by_cases h2 : x < 0
-      · simp only [h1, h2, hxN, if_true, if_false]; omega
-      · simp only [h1, h2, hxN, if_false]
-  rw [hidx]
-  by_cases h1 : x > (N:Int) - 1 <;> by_cases h2 : (N:Int) + 1 < 0 <;>
-    by_cases h3 : x < 0 <;> simp only [h1, h2, h3, if_true, if_false]
-
-theorem helper_index (N : Nat) (xs : List Int) (init : List Nat) :
-    (Id.run (forIn xs init (fun x r =>
-        ForInStep.yield (r ++ [desiredIndex N x]))) : List Nat)
-      = init ++ xs.map (desiredIndex N) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons, List.append_assoc]
 
 theorem correct_index :
     ∀ (N M : Nat) (xs : List Int),
       problem_spec_index N xs (implementation_index N M xs) := by
   intro N M xs
-  refine ⟨xs.map (desiredIndex N), ?_, ?_, ?_⟩
-  · unfold implementation_index
-    simp only [Id.run]
-    have hbody : (forIn xs ([]:List Nat) (fun x r =>
-        if x > (N:Int) - 1 then do
-          pure PUnit.unit
-          if (N:Int)+1 < 0 then do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)).toNat]))
-            else do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)+1).toNat]))
-        else do
-          pure PUnit.unit
-          if x < 0 then do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)).toNat]))
-            else do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [x.toNat]))) : Id (List Nat))
-      = (forIn xs ([]:List Nat) (fun x r =>
-        ForInStep.yield (r ++ [desiredIndex N x])) : Id (List Nat)) := by
-      congr 1
-      funext x r
-      simp only [bind, pure]
-      exact body_eq_index N x r
-    rw [hbody]
-    have := helper_index N xs []
-    simp only [Id.run] at this
-    rw [this]; rfl
+  refine ⟨xs.map (desiredIndex N), rfl, ?_, ?_⟩
   · simp
   · intro i hi
     rw [List.getD_eq_getElem?_getD, List.getD_eq_getElem?_getD]
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,92 +54,24 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The indices are recorded in a container whose value type is widened so it
-can always hold a reserved slot number, independently of the input value type's
-capacity `M`. The reserved slot numbers therefore always fit and the conversion
-never fails. -/
+
 def implementation_index (N M : Nat) (xs : List Int) :
     Except Unit (List Nat) := Id.run do
   let mut out : List Nat := []
   for x in xs do
-    let mut idx : Int := x
-    -- send values above the valid range to the `over` slot first, then values
-    -- below it to the `under` slot
-    if idx > (N : Int) - 1 then
-      idx := (N : Int) + 1
-    if idx < 0 then
-      idx := (N : Int)
-    out := out ++ [idx.toNat]
+    if x < 0 ∨ (N:Int) ≤ x then
+      return Except.error ()
+    out := out ++ [x.toNat]
   return Except.ok out
 -- impl-end
 
 -- proof-start
--- The desugared loop body equals a clean body that appends `desiredIndex N x`.
-theorem body_eq_index (N : Nat) (x : Int) (r : List Nat) :
-    (if x > (N:Int) - 1 then
-        (if (N:Int) + 1 < 0 then ForInStep.yield (r ++ [((N:Int)).toNat])
-         else ForInStep.yield (r ++ [((N:Int) + 1).toNat]))
-      else
-        (if x < 0 then ForInStep.yield (r ++ [((N:Int)).toNat])
-         else ForInStep.yield (r ++ [x.toNat])))
-      = ForInStep.yield (r ++ [desiredIndex N x]) := by
-  have hidx : desiredIndex N x =
-      (if x > (N:Int) - 1 then
-        (if (N:Int) + 1 < 0 then ((N:Int)).toNat else ((N:Int) + 1).toNat)
-       else
-        (if x < 0 then ((N:Int)).toNat else x.toNat)) := by
-    unfold desiredIndex
-    by_cases h1 : x > (N:Int) - 1
-    · have hneg : ¬ ((N:Int) + 1 < 0) := by omega
-      have hx0 : ¬ (x < 0) := by omega
-      have hxN : (N:Int) ≤ x := by omega
-      simp only [h1, hneg, hx0, hxN, if_true, if_false]; omega
-    · have hxN : ¬ ((N:Int) ≤ x) := by omega
-      by_cases h2 : x < 0
-      · simp only [h1, h2, hxN, if_true, if_false]; omega
-      · simp only [h1, h2, hxN, if_false]
-  rw [hidx]
-  by_cases h1 : x > (N:Int) - 1 <;> by_cases h2 : (N:Int) + 1 < 0 <;>
-    by_cases h3 : x < 0 <;> simp only [h1, h2, h3, if_true, if_false]
-
-theorem helper_index (N : Nat) (xs : List Int) (init : List Nat) :
-    (Id.run (forIn xs init (fun x r =>
-        ForInStep.yield (r ++ [desiredIndex N x]))) : List Nat)
-      = init ++ xs.map (desiredIndex N) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons, List.append_assoc]
 
 theorem correct_index :
     ∀ (N M : Nat) (xs : List Int),
       problem_spec_index N xs (implementation_index N M xs) := by
   intro N M xs
-  refine ⟨xs.map (desiredIndex N), ?_, ?_, ?_⟩
-  · unfold implementation_index
-    simp only [Id.run]
-    have hbody : (forIn xs ([]:List Nat) (fun x r =>
-        if x > (N:Int) - 1 then do
-          pure PUnit.unit
-          if (N:Int)+1 < 0 then do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)).toNat]))
-            else do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)+1).toNat]))
-        else do
-          pure PUnit.unit
-          if x < 0 then do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)).toNat]))
-            else do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [x.toNat]))) : Id (List Nat))
-      = (forIn xs ([]:List Nat) (fun x r =>
-        ForInStep.yield (r ++ [desiredIndex N x])) : Id (List Nat)) := by
-      congr 1
-      funext x r
-      simp only [bind, pure]
-      exact body_eq_index N x r
-    rw [hbody]
-    have := helper_index N xs []
-    simp only [Id.run] at this
-    rw [this]; rfl
+  refine ⟨xs.map (desiredIndex N), rfl, ?_, ?_⟩
   · simp
   · intro i hi
     rw [List.getD_eq_getElem?_getD, List.getD_eq_getElem?_getD]
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,18 +54,13 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The indices are recorded in a container whose value type is widened so it
-can always hold a reserved slot number, independently of the input value type's
-capacity `M`. The reserved slot numbers therefore always fit and the conversion
-never fails. -/
+
 def implementation_index (N M : Nat) (xs : List Int) :
     Except Unit (List Nat) := Id.run do
   let mut out : List Nat := []
   for x in xs do
     let mut idx : Int := x
-    -- send values above the valid range to the `over` slot first, then values
-    -- below it to the `under` slot
-    if idx > (N : Int) - 1 then
+    if idx ≥ (N : Int) - 1 then
       idx := (N : Int) + 1
     if idx < 0 then
       idx := (N : Int)
@@ -74,72 +69,12 @@
 -- impl-end
 
 -- proof-start
--- The desugared loop body equals a clean body that appends `desiredIndex N x`.
-theorem body_eq_index (N : Nat) (x : Int) (r : List Nat) :
-    (if x > (N:Int) - 1 then
-        (if (N:Int) + 1 < 0 then ForInStep.yield (r ++ [((N:Int)).toNat])
-         else ForInStep.yield (r ++ [((N:Int) + 1).toNat]))
-      else
-        (if x < 0 then ForInStep.yield (r ++ [((N:Int)).toNat])
-         else ForInStep.yield (r ++ [x.toNat])))
-      = ForInStep.yield (r ++ [desiredIndex N x]) := by
-  have hidx : desiredIndex N x =
-      (if x > (N:Int) - 1 then
-        (if (N:Int) + 1 < 0 then ((N:Int)).toNat else ((N:Int) + 1).toNat)
-       else
-        (if x < 0 then ((N:Int)).toNat else x.toNat)) := by
-    unfold desiredIndex
-    by_cases h1 : x > (N:Int) - 1
-    · have hneg : ¬ ((N:Int) + 1 < 0) := by omega
-      have hx0 : ¬ (x < 0) := by omega
-      have hxN : (N:Int) ≤ x := by omega
-      simp only [h1, hneg, hx0, hxN, if_true, if_false]; omega
-    · have hxN : ¬ ((N:Int) ≤ x) := by omega
-      by_cases h2 : x < 0
-      · simp only [h1, h2, hxN, if_true, if_false]; omega
-      · simp only [h1, h2, hxN, if_false]
-  rw [hidx]
-  by_cases h1 : x > (N:Int) - 1 <;> by_cases h2 : (N:Int) + 1 < 0 <;>
-    by_cases h3 : x < 0 <;> simp only [h1, h2, h3, if_true, if_false]
-
-theorem helper_index (N : Nat) (xs : List Int) (init : List Nat) :
-    (Id.run (forIn xs init (fun x r =>
-        ForInStep.yield (r ++ [desiredIndex N x]))) : List Nat)
-      = init ++ xs.map (desiredIndex N) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons, List.append_assoc]
 
 theorem correct_index :
     ∀ (N M : Nat) (xs : List Int),
       problem_spec_index N xs (implementation_index N M xs) := by
   intro N M xs
-  refine ⟨xs.map (desiredIndex N), ?_, ?_, ?_⟩
-  · unfold implementation_index
-    simp only [Id.run]
-    have hbody : (forIn xs ([]:List Nat) (fun x r =>
-        if x > (N:Int) - 1 then do
-          pure PUnit.unit
-          if (N:Int)+1 < 0 then do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)).toNat]))
-            else do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)+1).toNat]))
-        else do
-          pure PUnit.unit
-          if x < 0 then do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)).toNat]))
-            else do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [x.toNat]))) : Id (List Nat))
-      = (forIn xs ([]:List Nat) (fun x r =>
-        ForInStep.yield (r ++ [desiredIndex N x])) : Id (List Nat)) := by
-      congr 1
-      funext x r
-      simp only [bind, pure]
-      exact body_eq_index N x r
-    rw [hbody]
-    have := helper_index N xs []
-    simp only [Id.run] at this
-    rw [this]; rfl
+  refine ⟨xs.map (desiredIndex N), rfl, ?_, ?_⟩
   · simp
   · intro i hi
     rw [List.getD_eq_getElem?_getD, List.getD_eq_getElem?_getD]
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,92 +54,27 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The indices are recorded in a container whose value type is widened so it
-can always hold a reserved slot number, independently of the input value type's
-capacity `M`. The reserved slot numbers therefore always fit and the conversion
-never fails. -/
+
 def implementation_index (N M : Nat) (xs : List Int) :
     Except Unit (List Nat) := Id.run do
   let mut out : List Nat := []
   for x in xs do
     let mut idx : Int := x
-    -- send values above the valid range to the `over` slot first, then values
-    -- below it to the `under` slot
+    if idx < 0 then
+      idx := (N : Int)
     if idx > (N : Int) - 1 then
       idx := (N : Int) + 1
-    if idx < 0 then
-      idx := (N : Int)
     out := out ++ [idx.toNat]
   return Except.ok out
 -- impl-end
 
 -- proof-start
--- The desugared loop body equals a clean body that appends `desiredIndex N x`.
-theorem body_eq_index (N : Nat) (x : Int) (r : List Nat) :
-    (if x > (N:Int) - 1 then
-        (if (N:Int) + 1 < 0 then ForInStep.yield (r ++ [((N:Int)).toNat])
-         else ForInStep.yield (r ++ [((N:Int) + 1).toNat]))
-      else
-        (if x < 0 then ForInStep.yield (r ++ [((N:Int)).toNat])
-         else ForInStep.yield (r ++ [x.toNat])))
-      = ForInStep.yield (r ++ [desiredIndex N x]) := by
-  have hidx : desiredIndex N x =
-      (if x > (N:Int) - 1 then
-        (if (N:Int) + 1 < 0 then ((N:Int)).toNat else ((N:Int) + 1).toNat)
-       else
-        (if x < 0 then ((N:Int)).toNat else x.toNat)) := by
-    unfold desiredIndex
-    by_cases h1 : x > (N:Int) - 1
-    · have hneg : ¬ ((N:Int) + 1 < 0) := by omega
-      have hx0 : ¬ (x < 0) := by omega
-      have hxN : (N:Int) ≤ x := by omega
-      simp only [h1, hneg, hx0, hxN, if_true, if_false]; omega
-    · have hxN : ¬ ((N:Int) ≤ x) := by omega
-      by_cases h2 : x < 0
-      · simp only [h1, h2, hxN, if_true, if_false]; omega
-      · simp only [h1, h2, hxN, if_false]
-  rw [hidx]
-  by_cases h1 : x > (N:Int) - 1 <;> by_cases h2 : (N:Int) + 1 < 0 <;>
-    by_cases h3 : x < 0 <;> simp only [h1, h2, h3, if_true, if_false]
-
-theorem helper_index (N : Nat) (xs : List Int) (init : List Nat) :
-    (Id.run (forIn xs init (fun x r =>
-        ForInStep.yield (r ++ [desiredIndex N x]))) : List Nat)
-      = init ++ xs.map (desiredIndex N) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons, List.append_assoc]
 
 theorem correct_index :
     ∀ (N M : Nat) (xs : List Int),
       problem_spec_index N xs (implementation_index N M xs) := by
   intro N M xs
-  refine ⟨xs.map (desiredIndex N), ?_, ?_, ?_⟩
-  · unfold implementation_index
-    simp only [Id.run]
-    have hbody : (forIn xs ([]:List Nat) (fun x r =>
-        if x > (N:Int) - 1 then do
-          pure PUnit.unit
-          if (N:Int)+1 < 0 then do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)).toNat]))
-            else do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)+1).toNat]))
-        else do
-          pure PUnit.unit
-          if x < 0 then do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)).toNat]))
-            else do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [x.toNat]))) : Id (List Nat))
-      = (forIn xs ([]:List Nat) (fun x r =>
-        ForInStep.yield (r ++ [desiredIndex N x])) : Id (List Nat)) := by
-      congr 1
-      funext x r
-      simp only [bind, pure]
-      exact body_eq_index N x r
-    rw [hbody]
-    have := helper_index N xs []
-    simp only [Id.run] at this
-    rw [this]; rfl
+  refine ⟨xs.map (desiredIndex N), rfl, ?_, ?_⟩
   · simp
   · intro i hi
     rw [List.getD_eq_getElem?_getD, List.getD_eq_getElem?_getD]
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -54,92 +54,19 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The indices are recorded in a container whose value type is widened so it
-can always hold a reserved slot number, independently of the input value type's
-capacity `M`. The reserved slot numbers therefore always fit and the conversion
-never fails. -/
+
 def implementation_index (N M : Nat) (xs : List Int) :
-    Except Unit (List Nat) := Id.run do
-  let mut out : List Nat := []
-  for x in xs do
-    let mut idx : Int := x
-    -- send values above the valid range to the `over` slot first, then values
-    -- below it to the `under` slot
-    if idx > (N : Int) - 1 then
-      idx := (N : Int) + 1
-    if idx < 0 then
-      idx := (N : Int)
-    out := out ++ [idx.toNat]
-  return Except.ok out
+    Except Unit (List Nat) :=
+  Except.ok (xs.map (desiredIndex N))
 -- impl-end
 
 -- proof-start
--- The desugared loop body equals a clean body that appends `desiredIndex N x`.
-theorem body_eq_index (N : Nat) (x : Int) (r : List Nat) :
-    (if x > (N:Int) - 1 then
-        (if (N:Int) + 1 < 0 then ForInStep.yield (r ++ [((N:Int)).toNat])
-         else ForInStep.yield (r ++ [((N:Int) + 1).toNat]))
-      else
-        (if x < 0 then ForInStep.yield (r ++ [((N:Int)).toNat])
-         else ForInStep.yield (r ++ [x.toNat])))
-      = ForInStep.yield (r ++ [desiredIndex N x]) := by
-  have hidx : desiredIndex N x =
-      (if x > (N:Int) - 1 then
-        (if (N:Int) + 1 < 0 then ((N:Int)).toNat else ((N:Int) + 1).toNat)
-       else
-        (if x < 0 then ((N:Int)).toNat else x.toNat)) := by
-    unfold desiredIndex
-    by_cases h1 : x > (N:Int) - 1
-    · have hneg : ¬ ((N:Int) + 1 < 0) := by omega
-      have hx0 : ¬ (x < 0) := by omega
-      have hxN : (N:Int) ≤ x := by omega
-      simp only [h1, hneg, hx0, hxN, if_true, if_false]; omega
-    · have hxN : ¬ ((N:Int) ≤ x) := by omega
-      by_cases h2 : x < 0
-      · simp only [h1, h2, hxN, if_true, if_false]; omega
-      · simp only [h1, h2, hxN, if_false]
-  rw [hidx]
-  by_cases h1 : x > (N:Int) - 1 <;> by_cases h2 : (N:Int) + 1 < 0 <;>
-    by_cases h3 : x < 0 <;> simp only [h1, h2, h3, if_true, if_false]
-
-theorem helper_index (N : Nat) (xs : List Int) (init : List Nat) :
-    (Id.run (forIn xs init (fun x r =>
-        ForInStep.yield (r ++ [desiredIndex N x]))) : List Nat)
-      = init ++ xs.map (desiredIndex N) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons, List.append_assoc]
 
 theorem correct_index :
     ∀ (N M : Nat) (xs : List Int),
       problem_spec_index N xs (implementation_index N M xs) := by
   intro N M xs
-  refine ⟨xs.map (desiredIndex N), ?_, ?_, ?_⟩
-  · unfold implementation_index
-    simp only [Id.run]
-    have hbody : (forIn xs ([]:List Nat) (fun x r =>
-        if x > (N:Int) - 1 then do
-          pure PUnit.unit
-          if (N:Int)+1 < 0 then do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)).toNat]))
-            else do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)+1).toNat]))
-        else do
-          pure PUnit.unit
-          if x < 0 then do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)).toNat]))
-            else do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [x.toNat]))) : Id (List Nat))
-      = (forIn xs ([]:List Nat) (fun x r =>
-        ForInStep.yield (r ++ [desiredIndex N x])) : Id (List Nat)) := by
-      congr 1
-      funext x r
-      simp only [bind, pure]
-      exact body_eq_index N x r
-    rw [hbody]
-    have := helper_index N xs []
-    simp only [Id.run] at this
-    rw [this]; rfl
+  refine ⟨xs.map (desiredIndex N), rfl, ?_, ?_⟩
   · simp
   · intro i hi
     rw [List.getD_eq_getElem?_getD, List.getD_eq_getElem?_getD]
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,96 +54,29 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The indices are recorded in a container whose value type is widened so it
-can always hold a reserved slot number, independently of the input value type's
-capacity `M`. The reserved slot numbers therefore always fit and the conversion
-never fails. -/
+
 def implementation_index (N M : Nat) (xs : List Int) :
     Except Unit (List Nat) := Id.run do
   let mut out : List Nat := []
   for x in xs do
     let mut idx : Int := x
-    -- send values above the valid range to the `over` slot first, then values
-    -- below it to the `under` slot
     if idx > (N : Int) - 1 then
       idx := (N : Int) + 1
     if idx < 0 then
       idx := (N : Int)
+    if (N : Int) + 1 ≥ (M : Int) then
+      -- capacity too small to hold the over slot: keep narrow -> reject
+      if idx ≥ (M : Int) then
+        return Except.error ()
     out := out ++ [idx.toNat]
   return Except.ok out
 -- impl-end
 
 -- proof-start
--- The desugared loop body equals a clean body that appends `desiredIndex N x`.
-theorem body_eq_index (N : Nat) (x : Int) (r : List Nat) :
-    (if x > (N:Int) - 1 then
-        (if (N:Int) + 1 < 0 then ForInStep.yield (r ++ [((N:Int)).toNat])
-         else ForInStep.yield (r ++ [((N:Int) + 1).toNat]))
-      else
-        (if x < 0 then ForInStep.yield (r ++ [((N:Int)).toNat])
-         else ForInStep.yield (r ++ [x.toNat])))
-      = ForInStep.yield (r ++ [desiredIndex N x]) := by
-  have hidx : desiredIndex N x =
-      (if x > (N:Int) - 1 then
-        (if (N:Int) + 1 < 0 then ((N:Int)).toNat else ((N:Int) + 1).toNat)
-       else
-        (if x < 0 then ((N:Int)).toNat else x.toNat)) := by
-    unfold desiredIndex
-    by_cases h1 : x > (N:Int) - 1
-    · have hneg : ¬ ((N:Int) + 1 < 0) := by omega
-      have hx0 : ¬ (x < 0) := by omega
-      have hxN : (N:Int) ≤ x := by omega
-      simp only [h1, hneg, hx0, hxN, if_true, if_false]; omega
-    · have hxN : ¬ ((N:Int) ≤ x) := by omega
-      by_cases h2 : x < 0
-      · simp only [h1, h2, hxN, if_true, if_false]; omega
-      · simp only [h1, h2, hxN, if_false]
-  rw [hidx]
-  by_cases h1 : x > (N:Int) - 1 <;> by_cases h2 : (N:Int) + 1 < 0 <;>
-    by_cases h3 : x < 0 <;> simp only [h1, h2, h3, if_true, if_false]
-
-theorem helper_index (N : Nat) (xs : List Int) (init : List Nat) :
-    (Id.run (forIn xs init (fun x r =>
-        ForInStep.yield (r ++ [desiredIndex N x]))) : List Nat)
-      = init ++ xs.map (desiredIndex N) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons, List.append_assoc]
 
 theorem correct_index :
     ∀ (N M : Nat) (xs : List Int),
       problem_spec_index N xs (implementation_index N M xs) := by
   intro N M xs
-  refine ⟨xs.map (desiredIndex N), ?_, ?_, ?_⟩
-  · unfold implementation_index
-    simp only [Id.run]
-    have hbody : (forIn xs ([]:List Nat) (fun x r =>
-        if x > (N:Int) - 1 then do
-          pure PUnit.unit
-          if (N:Int)+1 < 0 then do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)).toNat]))
-            else do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)+1).toNat]))
-        else do
-          pure PUnit.unit
-          if x < 0 then do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)).toNat]))
-            else do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [x.toNat]))) : Id (List Nat))
-      = (forIn xs ([]:List Nat) (fun x r =>
-        ForInStep.yield (r ++ [desiredIndex N x])) : Id (List Nat)) := by
-      congr 1
-      funext x r
-      simp only [bind, pure]
-      exact body_eq_index N x r
-    rw [hbody]
-    have := helper_index N xs []
-    simp only [Id.run] at this
-    rw [this]; rfl
-  · simp
-  · intro i hi
-    rw [List.getD_eq_getElem?_getD, List.getD_eq_getElem?_getD]
-    simp only [List.getElem?_map]
-    rw [List.getElem?_eq_getElem hi]
-    simp
+  sorry
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Mapping integer data values to palette slot indices.

A palette of `N` colors is stored together with extra slots reserved for values
that fall outside the palette's valid range: an `under` slot at index `N` for
values below the range, an `over` slot at index `N + 1` for values above it, and
a further `bad` slot at index `N + 2`. Given a list of integer data values, each
value is converted to the index of the slot whose color represents it:

* a value `v` with `0 ≤ v < N` indexes its own palette color `v`;
* a value `v < 0` indexes the `under` slot `N`;
* a value `v ≥ N` indexes the `over` slot `N + 1`.

The reserved slot numbers must be recorded faithfully no matter how wide the
range of the input value type is, so the conversion always succeeds and every
out-of-range value selects its dedicated reserved slot. The container holding
the indices is given a value type with capacity `M` (representing values
`0 … M - 1`); the conversion must not fail even when `M` is too small to hold a
reserved slot number on its own.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the index assignment is
-- spelled out concretely (in-range values keep their own index; out-of-range
-- values are sent to the dedicated reserved slots `N` and `N + 1`).
-- axioms-end

-- pure-start
/-- The slot index a single integer data value `x` maps to, for a palette of
`N` colors: `N` (under) when `x < 0`, `N + 1` (over) when `x ≥ N`, and `x`
itself when `0 ≤ x < N`. -/
def desiredIndex (N : Nat) (x : Int) : Nat :=
  if x < 0 then N
  else if (N : Int) ≤ x then N + 1
  else x.toNat
-- pure-end

-- post-conditions-start
/-- `result` is the conversion of the integer data values `xs` to slot indices
under a palette of `N` colors. The conversion always succeeds (`Except.ok`) and
yields one index per input value, each equal to the exact slot the corresponding
input value maps to (`desiredIndex`). -/
def problem_spec_index (N : Nat) (xs : List Int)
    (result : Except Unit (List Nat)) : Prop :=
  ∃ out, result = Except.ok out ∧
    out.length = xs.length ∧
    ∀ i, i < xs.length → out.getD i 0 = desiredIndex N (xs.getD i 0)
-- post-conditions-end

-- impl-start
/-- The indices are recorded in a container whose value type is widened so it
can always hold a reserved slot number, independently of the input value type's
capacity `M`. The reserved slot numbers therefore always fit and the conversion
never fails. -/
def implementation_index (N M : Nat) (xs : List Int) :
    Except Unit (List Nat) := Id.run do
  let mut out : List Nat := []
  for x in xs do
    let mut idx : Int := x
    -- send values above the valid range to the `over` slot first, then values
    -- below it to the `under` slot
    if idx > (N : Int) - 1 then
      idx := (N : Int) + 1
    if idx < 0 then
      idx := (N : Int)
    out := out ++ [idx.toNat]
  return Except.ok out
-- impl-end

-- proof-start
-- The desugared loop body equals a clean body that appends `desiredIndex N x`.
theorem body_eq_index (N : Nat) (x : Int) (r : List Nat) :
    (if x > (N:Int) - 1 then
        (if (N:Int) + 1 < 0 then ForInStep.yield (r ++ [((N:Int)).toNat])
         else ForInStep.yield (r ++ [((N:Int) + 1).toNat]))
      else
        (if x < 0 then ForInStep.yield (r ++ [((N:Int)).toNat])
         else ForInStep.yield (r ++ [x.toNat])))
      = ForInStep.yield (r ++ [desiredIndex N x]) := by
  have hidx : desiredIndex N x =
      (if x > (N:Int) - 1 then
        (if (N:Int) + 1 < 0 then ((N:Int)).toNat else ((N:Int) + 1).toNat)
       else
        (if x < 0 then ((N:Int)).toNat else x.toNat)) := by
    unfold desiredIndex
    by_cases h1 : x > (N:Int) - 1
    · have hneg : ¬ ((N:Int) + 1 < 0) := by omega
      have hx0 : ¬ (x < 0) := by omega
      have hxN : (N:Int) ≤ x := by omega
      simp only [h1, hneg, hx0, hxN, if_true, if_false]; omega
    · have hxN : ¬ ((N:Int) ≤ x) := by omega
      by_cases h2 : x < 0
      · simp only [h1, h2, hxN, if_true, if_false]; omega
      · simp only [h1, h2, hxN, if_false]
  rw [hidx]
  by_cases h1 : x > (N:Int) - 1 <;> by_cases h2 : (N:Int) + 1 < 0 <;>
    by_cases h3 : x < 0 <;> simp only [h1, h2, h3, if_true, if_false]

theorem helper_index (N : Nat) (xs : List Int) (init : List Nat) :
    (Id.run (forIn xs init (fun x r =>
        ForInStep.yield (r ++ [desiredIndex N x]))) : List Nat)
      = init ++ xs.map (desiredIndex N) := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp [List.map_cons, List.append_assoc]

theorem correct_index :
    ∀ (N M : Nat) (xs : List Int),
      problem_spec_index N xs (implementation_index N M xs) := by
  intro N M xs
  refine ⟨xs.map (desiredIndex N), ?_, ?_, ?_⟩
  · unfold implementation_index
    simp only [Id.run]
    have hbody : (forIn xs ([]:List Nat) (fun x r =>
        if x > (N:Int) - 1 then do
          pure PUnit.unit
          if (N:Int)+1 < 0 then do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)).toNat]))
            else do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)+1).toNat]))
        else do
          pure PUnit.unit
          if x < 0 then do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)).toNat]))
            else do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [x.toNat]))) : Id (List Nat))
      = (forIn xs ([]:List Nat) (fun x r =>
        ForInStep.yield (r ++ [desiredIndex N x])) : Id (List Nat)) := by
      congr 1
      funext x r
      simp only [bind, pure]
      exact body_eq_index N x r
    rw [hbody]
    have := helper_index N xs []
    simp only [Id.run] at this
    rw [this]; rfl
  · simp
  · intro i hi
    rw [List.getD_eq_getElem?_getD, List.getD_eq_getElem?_getD]
    simp only [List.getElem?_map]
    rw [List.getElem?_eq_getElem hi]
    simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ AUDIT (refinement fidelity), matplotlib__matplotlib-24970 / lean. Goal: find a same-spec implementation_index whose correct_index CLOSES (verify) but whose faithful refined patch does NOT resolve (⇒ verify⇏correct). Result: NO such impl found; verify⇒correct holds. VERDICT SOUND.

SPEC STRUCTURE. spec_view (markers.spec_view, lean flavor) collapses BOTH impl AND proof regions, so attacks may edit impl+proof freely while axioms/pure/pre/post stay byte-identical. Confirmed same_spec=True for all 7 attacks + positive control via markers.same_spec (lean backend). The frozen post-condition problem_spec_index pins the output COMPLETELY and universally over M: ∃ out, result = Except.ok out (always success — no Except.error permitted) AND out.length = xs.length AND ∀ i<len, out.getD i 0 = desiredIndex N (xs.getD i 0) (every element equals the exact gold index). desiredIndex: x<0 ↦ N, x≥N ↦ N+1, else x. So the ONLY closing witness is out = xs.map (desiredIndex N) with Except.ok — exactly the post-patch observable (always succeed + exact reserved-slot indices).

### ATTACKS (all commands: `bash scripts/lean_verify.sh <file>` from project root; exit 0=verifies/no-sorry, 1=error, 3=sorry):
- pos_control.lean (gold impl verbatim): exit 0. `#print axioms correct_index` = [propext, Quot.sound] (clean, no sorryAx). Positive control PASSES.
- atk_1.lean (PREPATCH bug: reserved-slot store into narrow container fails when idx≥M ⇒ Except.error): exit 3 (sorry). Prepatch bug reproduced. Independently PROVED unprovable: refute_1.lean shows `¬ problem_spec_index 0 [0] (implementation_index 0 0 [0])` closes (exit 0) — the capacity failure violates the always-Except.ok spec, so correct_index CANNOT close. Spec fail-closes the bug.
- atk_2.lean (clamp out-of-range to N-1): exit 1 (type mismatch — output ≠ xs.map desiredIndex). Wrong values (N-1 where spec demands N/N+1) rejected.
- atk_3.lean (partial-domain: Except.error on any out-of-range value): exit 1. Rejected (reintroduces failure).
- atk_4.lean (boundary off-by-one: idx ≥ N-1 sends in-range value N-1 to over slot): exit 1. Wrong boundary value rejected.
- atk_5.lean (control-flow-effect: under-test BEFORE over-test — x<0 gets set to N then N>N-1 promotes to N+1, so x<0 ↦ N+1 wrong): exit 1. Rejected.
- atk_6.lean (ungrounded-oracle echo: Except.ok (xs.map (desiredIndex N))): exit 0 — CLOSES. `#print axioms correct_index` = [propext] (CLEAN, no sorryAx). This is the ONLY closing same-spec impl. Per protocol its faithful refined patch was MATERIALIZED (atk6_faithful.patch = the gold hoist-the-cast fix, the exact code that realizes always-success + exact indices) and RUN through the official harness.
- atk_7.lean (conditional/incomplete fix keyed on M: widen only when N+1<M, else reject with Except.error): exit 3 (sorry). PROVED unprovable: refute_7.lean shows `¬ problem_spec_index 0 [0] (implementation_index 0 0 [0])` closes (exit 0) — for small M it returns Except.error, violating always-Except.ok. A partial fix that leaves the narrow-capacity case broken CANNOT close. Spec fail-closes the partial fix.

RESOLVE RUN (atk_6 faithful patch = gold fix). Executed via harness.run_resolve; the wrapper returned COMPLETED=False the first two times due to swebench's post-run docker clean_images() race (a concurrent process deleted an image mid `client.images.list`, raising ImageNotFound AFTER 'All instances run.'). I ran the harness directly (run_id sbu-manual-24970-atk6, `... run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified --instance_ids matplotlib__matplotlib-24970 --namespace swebench --instance_image_tag latest --cache_level env --timeout 1800`): the per-instance report.json WAS written before the cleanup crash. report.json: resolved=true; FAIL_TO_PASS test_index_dtype[uint8] SUCCESS; all 254 PASS_TO_PASS pass (the sole 'test_double_register_builtin_cmap' failure is a pre-existing environment/global-state flake outside F2P/P2P, not in the graded set). So atk_6's faithful patch RESOLVES — the closing witness corresponds to a resolving patch. verify⇒correct confirmed; NOT broken.

WHY NO BREAK IS POSSIBLE: every closing impl must (a) always return Except.ok (any reintroduction of capacity/domain failure — the essence of the prepatch bug — is refuted, verified mechanically by refute_1/refute_7) and (b) emit exactly xs.map (desiredIndex N) (any value deviation is rejected, verified by atk_2/3/4/5). Both properties ARE the resolved post-patch behavior, so no closing impl maps to a non-resolving patch.

refinement.md AUDIT: 6 legs, all tagged R / A-reference / I — NO kind-3 (no undischarged/unmodeled leg). A-reference legs (over-slot idx:=N+1 ↔ xa[xa>self.N-1]=self._i_over; under-slot idx:=N ↔ xa[xa<0]=self._i_under; store of exact reserved index ↔ wide index container) correspond faithfully to the real patched Colormap.__call__ (colors.py:730-732 + hoisted astype(int) cast). Verified against the gold patch (frozen row): the fix hoists `xa = xa.astype(int)` out of the `if xa.dtype.kind=='f':` branch under np.errstate(invalid='ignore') so the integer index array is widened before the reserved-slot stores — exactly the deep model (always succeed, record N/N+1 exactly). No consumed callee axiom (G-AX skip stub is correct: self.N/_i_under/_i_over are plain inlined int attributes). The R leg (Except.ok↦success, Except.error↦rejected narrow store) and the SUCCESS/FAILURE discrimination are carried by the two-file G-DIFF prepatch pair, mechanically sound (refute_1). Model↔patch correspondence holds.

CONCLUSION: ≥5 distinct wrong impls attacked (prepatch capacity-fail, clamp-to-N-1, partial-domain-error, boundary off-by-one, control-flow reorder, conditional-widen-by-M) + the exact-gold echo. Only the echo closes, with clean axioms, and its materialized faithful patch RESOLVES (executed, report.json resolved=true). No closing-clean-axiom impl has a non-resolving faithful patch. G-EQ = SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Mapping integer data values to palette slot indices.

A palette of `N` colors is stored together with extra slots reserved for values
that fall outside the palette's valid range: an `under` slot at index `N` for
values below the range, an `over` slot at index `N + 1` for values above it, and
a further `bad` slot at index `N + 2`. Given a list of integer data values, each
value is converted to the index of the slot whose color represents it:

* a value `v` with `0 ≤ v < N` indexes its own palette color `v`;
* a value `v < 0` indexes the `under` slot `N`;
* a value `v ≥ N` indexes the `over` slot `N + 1`.

The reserved slot numbers must be recorded faithfully no matter how wide the
range of the input value type is, so the conversion always succeeds and every
out-of-range value selects its dedicated reserved slot. The container holding
the indices is given a value type with capacity `M` (representing values
`0 … M - 1`); the conversion must not fail even when `M` is too small to hold a
reserved slot number on its own.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the index assignment is
-- spelled out concretely (in-range values keep their own index; out-of-range
-- values are sent to the dedicated reserved slots `N` and `N + 1`).
-- axioms-end

-- pure-start
/-- The slot index a single integer data value `x` maps to, for a palette of
`N` colors: `N` (under) when `x < 0`, `N + 1` (over) when `x ≥ N`, and `x`
itself when `0 ≤ x < N`. -/
def desiredIndex (N : Nat) (x : Int) : Nat :=
  if x < 0 then N
  else if (N : Int) ≤ x then N + 1
  else x.toNat
-- pure-end

-- post-conditions-start
/-- `result` is the conversion of the integer data values `xs` to slot indices
under a palette of `N` colors. The conversion always succeeds (`Except.ok`) and
yields one index per input value, each equal to the exact slot the corresponding
input value maps to (`desiredIndex`). -/
def problem_spec_index (N : Nat) (xs : List Int)
    (result : Except Unit (List Nat)) : Prop :=
  ∃ out, result = Except.ok out ∧
    out.length = xs.length ∧
    ∀ i, i < xs.length → out.getD i 0 = desiredIndex N (xs.getD i 0)
-- post-conditions-end

-- impl-start
/-- The indices are recorded in a container whose value type is widened so it
can always hold a reserved slot number, independently of the input value type's
capacity `M`. The reserved slot numbers therefore always fit and the conversion
never fails. -/
def implementation_index (N M : Nat) (xs : List Int) :
    Except Unit (List Nat) := Id.run do
  let mut out : List Nat := []
  for x in xs do
    let mut idx : Int := x
    -- send values above the valid range to the `over` slot first, then values
    -- below it to the `under` slot
    if idx > (N : Int) - 1 then
      idx := (N : Int) + 1
    if idx < 0 then
      idx := (N : Int)
    out := out ++ [idx.toNat]
  return Except.ok out
-- impl-end

-- proof-start
-- The desugared loop body equals a clean body that appends `desiredIndex N x`.
theorem body_eq_index (N : Nat) (x : Int) (r : List Nat) :
    (if x > (N:Int) - 1 then
        (if (N:Int) + 1 < 0 then ForInStep.yield (r ++ [((N:Int)).toNat])
         else ForInStep.yield (r ++ [((N:Int) + 1).toNat]))
      else
        (if x < 0 then ForInStep.yield (r ++ [((N:Int)).toNat])
         else ForInStep.yield (r ++ [x.toNat])))
      = ForInStep.yield (r ++ [desiredIndex N x]) := by
  have hidx : desiredIndex N x =
      (if x > (N:Int) - 1 then
        (if (N:Int) + 1 < 0 then ((N:Int)).toNat else ((N:Int) + 1).toNat)
       else
        (if x < 0 then ((N:Int)).toNat else x.toNat)) := by
    unfold desiredIndex
    by_cases h1 : x > (N:Int) - 1
    · have hneg : ¬ ((N:Int) + 1 < 0) := by omega
      have hx0 : ¬ (x < 0) := by omega
      have hxN : (N:Int) ≤ x := by omega
      simp only [h1, hneg, hx0, hxN, if_true, if_false]; omega
    · have hxN : ¬ ((N:Int) ≤ x) := by omega
      by_cases h2 : x < 0
      · simp only [h1, h2, hxN, if_true, if_false]; omega
      · simp only [h1, h2, hxN, if_false]
  rw [hidx]
  by_cases h1 : x > (N:Int) - 1 <;> by_cases h2 : (N:Int) + 1 < 0 <;>
    by_cases h3 : x < 0 <;> simp only [h1, h2, h3, if_true, if_false]

theorem helper_index (N : Nat) (xs : List Int) (init : List Nat) :
    (Id.run (forIn xs init (fun x r =>
        ForInStep.yield (r ++ [desiredIndex N x]))) : List Nat)
      = init ++ xs.map (desiredIndex N) := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp [List.map_cons, List.append_assoc]

theorem correct_index :
    ∀ (N M : Nat) (xs : List Int),
      problem_spec_index N xs (implementation_index N M xs) := by
  intro N M xs
  refine ⟨xs.map (desiredIndex N), ?_, ?_, ?_⟩
  · unfold implementation_index
    simp only [Id.run]
    have hbody : (forIn xs ([]:List Nat) (fun x r =>
        if x > (N:Int) - 1 then do
          pure PUnit.unit
          if (N:Int)+1 < 0 then do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)).toNat]))
            else do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)+1).toNat]))
        else do
          pure PUnit.unit
          if x < 0 then do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)).toNat]))
            else do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [x.toNat]))) : Id (List Nat))
      = (forIn xs ([]:List Nat) (fun x r =>
        ForInStep.yield (r ++ [desiredIndex N x])) : Id (List Nat)) := by
      congr 1
      funext x r
      simp only [bind, pure]
      exact body_eq_index N x r
    rw [hbody]
    have := helper_index N xs []
    simp only [Id.run] at this
    rw [this]; rfl
  · simp
  · intro i hi
    rw [List.getD_eq_getElem?_getD, List.getD_eq_getElem?_getD]
    simp only [List.getElem?_map]
    rw [List.getElem?_eq_getElem hi]
    simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ AUDIT (refinement fidelity), matplotlib__matplotlib-24970 / lean. Goal: find a same-spec implementation_index whose correct_index CLOSES (verify) but whose faithful refined patch does NOT resolve (⇒ verify⇏correct). Result: NO such impl found; verify⇒correct holds. VERDICT SOUND.

SPEC STRUCTURE. spec_view (markers.spec_view, lean flavor) collapses BOTH impl AND proof regions, so attacks may edit impl+proof freely while axioms/pure/pre/post stay byte-identical. Confirmed same_spec=True for all 7 attacks + positive control via markers.same_spec (lean backend). The frozen post-condition problem_spec_index pins the output COMPLETELY and universally over M: ∃ out, result = Except.ok out (always success — no Except.error permitted) AND out.length = xs.length AND ∀ i<len, out.getD i 0 = desiredIndex N (xs.getD i 0) (every element equals the exact gold index). desiredIndex: x<0 ↦ N, x≥N ↦ N+1, else x. So the ONLY closing witness is out = xs.map (desiredIndex N) with Except.ok — exactly the post-patch observable (always succeed + exact reserved-slot indices).

### ATTACKS (all commands: `bash scripts/lean_verify.sh <file>` from project root; exit 0=verifies/no-sorry, 1=error, 3=sorry):
- pos_control.lean (gold impl verbatim): exit 0. `#print axioms correct_index` = [propext, Quot.sound] (clean, no sorryAx). Positive control PASSES.
- atk_1.lean (PREPATCH bug: reserved-slot store into narrow container fails when idx≥M ⇒ Except.error): exit 3 (sorry). Prepatch bug reproduced. Independently PROVED unprovable: refute_1.lean shows `¬ problem_spec_index 0 [0] (implementation_index 0 0 [0])` closes (exit 0) — the capacity failure violates the always-Except.ok spec, so correct_index CANNOT close. Spec fail-closes the bug.
- atk_2.lean (clamp out-of-range to N-1): exit 1 (type mismatch — output ≠ xs.map desiredIndex). Wrong values (N-1 where spec demands N/N+1) rejected.
- atk_3.lean (partial-domain: Except.error on any out-of-range value): exit 1. Rejected (reintroduces failure).
- atk_4.lean (boundary off-by-one: idx ≥ N-1 sends in-range value N-1 to over slot): exit 1. Wrong boundary value rejected.
- atk_5.lean (control-flow-effect: under-test BEFORE over-test — x<0 gets set to N then N>N-1 promotes to N+1, so x<0 ↦ N+1 wrong): exit 1. Rejected.
- atk_6.lean (ungrounded-oracle echo: Except.ok (xs.map (desiredIndex N))): exit 0 — CLOSES. `#print axioms correct_index` = [propext] (CLEAN, no sorryAx). This is the ONLY closing same-spec impl. Per protocol its faithful refined patch was MATERIALIZED (atk6_faithful.patch = the gold hoist-the-cast fix, the exact code that realizes always-success + exact indices) and RUN through the official harness.
- atk_7.lean (conditional/incomplete fix keyed on M: widen only when N+1<M, else reject with Except.error): exit 3 (sorry). PROVED unprovable: refute_7.lean shows `¬ problem_spec_index 0 [0] (implementation_index 0 0 [0])` closes (exit 0) — for small M it returns Except.error, violating always-Except.ok. A partial fix that leaves the narrow-capacity case broken CANNOT close. Spec fail-closes the partial fix.

RESOLVE RUN (atk_6 faithful patch = gold fix). Executed via harness.run_resolve; the wrapper returned COMPLETED=False the first two times due to swebench's post-run docker clean_images() race (a concurrent process deleted an image mid `client.images.list`, raising ImageNotFound AFTER 'All instances run.'). I ran the harness directly (run_id sbu-manual-24970-atk6, `... run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified --instance_ids matplotlib__matplotlib-24970 --namespace swebench --instance_image_tag latest --cache_level env --timeout 1800`): the per-instance report.json WAS written before the cleanup crash. report.json: resolved=true; FAIL_TO_PASS test_index_dtype[uint8] SUCCESS; all 254 PASS_TO_PASS pass (the sole 'test_double_register_builtin_cmap' failure is a pre-existing environment/global-state flake outside F2P/P2P, not in the graded set). So atk_6's faithful patch RESOLVES — the closing witness corresponds to a resolving patch. verify⇒correct confirmed; NOT broken.

WHY NO BREAK IS POSSIBLE: every closing impl must (a) always return Except.ok (any reintroduction of capacity/domain failure — the essence of the prepatch bug — is refuted, verified mechanically by refute_1/refute_7) and (b) emit exactly xs.map (desiredIndex N) (any value deviation is rejected, verified by atk_2/3/4/5). Both properties ARE the resolved post-patch behavior, so no closing impl maps to a non-resolving patch.

refinement.md AUDIT: 6 legs, all tagged R / A-reference / I — NO kind-3 (no undischarged/unmodeled leg). A-reference legs (over-slot idx:=N+1 ↔ xa[xa>self.N-1]=self._i_over; under-slot idx:=N ↔ xa[xa<0]=self._i_under; store of exact reserved index ↔ wide index container) correspond faithfully to the real patched Colormap.__call__ (colors.py:730-732 + hoisted astype(int) cast). Verified against the gold patch (frozen row): the fix hoists `xa = xa.astype(int)` out of the `if xa.dtype.kind=='f':` branch under np.errstate(invalid='ignore') so the integer index array is widened before the reserved-slot stores — exactly the deep model (always succeed, record N/N+1 exactly). No consumed callee axiom (G-AX skip stub is correct: self.N/_i_under/_i_over are plain inlined int attributes). The R leg (Except.ok↦success, Except.error↦rejected narrow store) and the SUCCESS/FAILURE discrimination are carried by the two-file G-DIFF prepatch pair, mechanically sound (refute_1). Model↔patch correspondence holds.

CONCLUSION: ≥5 distinct wrong impls attacked (prepatch capacity-fail, clamp-to-N-1, partial-domain-error, boundary off-by-one, control-flow reorder, conditional-widen-by-M) + the exact-gold echo. Only the echo closes, with clean axioms, and its materialized faithful patch RESOLVES (executed, report.json resolved=true). No closing-clean-axiom impl has a non-resolving faithful patch. G-EQ = SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence. (1) Spec region byte-identical: same_spec(Solution, Solution_prepatch)=True under LeanBackend; only impl+proof differ. (2) Solution.lean compiles clean (exit 0); #print axioms correct_index = [propext, Quot.sound] — no sorryAx, proof is genuine. (3) Model desiredIndex N x = (x<0 → N; N≤x → N+1; else x.toNat) exactly matches the real Colormap.__call__ integer-index path at base_commit a3011dfd1a (verified from fetched source): xa[xa>N-1]=N+1 (over), xa[xa<0]=N (under), applied over-before-under, disjoint branches → net map = desiredIndex. (4) Differential test against real matplotlib: palette sizes {1,2,3,4,8,16,64,128,255,256,300} × range [-2N-5,2N+5] + boundary catalogue + int64 extremes (±2^63, ±2^40) → 4291 checks, 0 mismatches; uint8 domain also matches. (5) The 'always succeeds' (Except.ok) claim is faithful — the patched callee never errors on int64/uint8 inputs; the spec is not too strong. The F2P (test_index_dtype[uint8]) exercises exactly the widening-cast fix modeled by the Except.ok success on the M-narrow prepatch skeleton. No spec drift, no over-strong post-condition.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the public problem_statement ONLY (not hints_text). Mechanical G-LEAK screen passes (no diff markers, no gold-patch line reproduced, no patched file path colors.py, no patched symbol; patch declares zero distinctive def/class symbols). Spec region verified byte-identical between Solution.lean and Solution_prepatch.lean via markers.same_spec == True. Semantic review: the spec view is a purely abstract input→output relation — integer value v maps to slot N (under, v<0), N+1 (over, v>=N), or v (in range); conversion must always succeed 'even when M is too small to hold a reserved slot number on its own.' This capacity-M requirement is a faithful generalization of what the problem_statement ALREADY discloses publicly: colors.py:730-732 lines quoted verbatim, and the deprecation text 'The conversion of 257 to uint8 will fail', N=256 default, and expected outcome 'No warnings.' The public bug report already reveals a reserved index (257) does not fit the narrow uint8 container and that the conversion must not warn/fail. The spec view discloses NONE of the gold edit's mechanism: no mention of the astype(int) widening cast, no float-vs-int branch, no numpy/dtype hoisting — that fix insight lives only in hints_text and is not reproduced. Stating the required observable ('conversion always succeeds') is mandatory for any faithful spec and is already implied by the public 'No warnings' expected outcome; it localizes no edit. No leak beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
