# P2 adversarial audit — astropy__astropy-14539

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 22 admissible attacks re-run of 22 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 22 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 17 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_10.lean`, `atk_11.lean`, `atk_11b.lean`, `atk_12.lean`, `atk_13.lean`, `atk_15.lean`, `atk_16.lean`, `atk_17.lean`, `atk_18.lean`, `atk_19.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_8.lean`, `atk_9.lean`, `atk_14.lean`, `atk_20.lean`, `atk_21.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No counterexample: no same-spec wrong impl with a closing clean-axiom proof has a faithful patch that fails to resolve. 21 attacks run; 16 REJECTED by the proof; 5 verified (atk_8, atk_9, atk_14, atk_20, atk_21) and ALL FIVE faithful patches RESOLVE under the official harness (2/2 F2P, 46/46 P2P), same as the gold control. The five verifiers are exactly the impls that add an arm guarded on a decidably-FALSE fact the contract's own hypotheses make unreachable (the complement of `rowsAreFixedShape` / `rowsComparable`, or unequal row counts). That is admissible-not-broken here because those arms are also unreachable in the REPOSITORY: `TableDataDiff._diff` returns before the per-column loop when row counts differ (diff.py:1409-1411, so atk_9's arm is dead), and `common_columns` is an intersection under `Column.__eq__`, which keys on `(name.lower(), format)` (column.py:736-744), so the two compared columns ALWAYS share a declared format and a non-VLA format always denotes rectangular storage (atk_8/atk_14/atk_20's arms are dead). atk_21's arm is reachable only where the real `np.allclose` RAISES ValueError, i.e. where the routine has no output to be faithful to. Every added arm is therefore dead code in the real repository, which is why each patch resolves rather than exposing a hole.
```

**Attacks re-run (22):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -168,14 +168,16 @@
     (hcmp : ∀ idx, idx < arra.length → rowsComparable arra[idx]! arrb[idx]! = true)
     (hfix : isVariableLengthFormat fmt = false → rowsAreFixedShape arra arrb = true) :
     List Nat := Id.run do
-  if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then
+  if fmt.contains 'P' then
     let mut acc : List Nat := []
     for i in List.finRange arra.length do
       if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
         acc := acc ++ [i.val]
     return acc
+  else if hg : rowsAreFixedShape arra arrb = true then
+    return elementwiseDiff arra arrb hg
   else
-    return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))
+    return []
 -- impl-end
 
 -- proof-start
@@ -220,5 +222,8 @@
     rw [h2, columnDiffRows_loop]
     simp
   · simp only [hc]
+    have hs : rowsAreFixedShape arra arrb = true :=
+      hfix (by simpa [isVariableLengthFormat] using hc)
+    simp only [hs, dif_pos]
     rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -168,14 +168,16 @@
     (hcmp : ∀ idx, idx < arra.length → rowsComparable arra[idx]! arrb[idx]! = true)
     (hfix : isVariableLengthFormat fmt = false → rowsAreFixedShape arra arrb = true) :
     List Nat := Id.run do
-  if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then
+  if fmt.contains 'Q' then
     let mut acc : List Nat := []
     for i in List.finRange arra.length do
       if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
         acc := acc ++ [i.val]
     return acc
+  else if hg : rowsAreFixedShape arra arrb = true then
+    return elementwiseDiff arra arrb hg
   else
-    return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))
+    return []
 -- impl-end
 
 -- proof-start
@@ -220,5 +222,8 @@
     rw [h2, columnDiffRows_loop]
     simp
   · simp only [hc]
+    have hs : rowsAreFixedShape arra arrb = true :=
+      hfix (by simpa [isVariableLengthFormat] using hc)
+    simp only [hs, dif_pos]
     rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -171,8 +171,9 @@
   if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then
     let mut acc : List Nat := []
     for i in List.finRange arra.length do
-      if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
-        acc := acc ++ [i.val]
+      if arra[i.val]!.length == arrb[i.val]!.length then
+        if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
+          acc := acc ++ [i.val]
     return acc
   else
     return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -171,8 +171,9 @@
   if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then
     let mut acc : List Nat := []
     for i in List.finRange arra.length do
-      if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
-        acc := acc ++ [i.val]
+      if i.val != 0 then
+        if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
+          acc := acc ++ [i.val]
     return acc
   else
     return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -172,7 +172,7 @@
     let mut acc : List Nat := []
     for i in List.finRange arra.length do
       if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
-        acc := acc ++ [i.val]
+        acc := [i.val] ++ acc
     return acc
   else
     return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -168,14 +168,14 @@
     (hcmp : ∀ idx, idx < arra.length → rowsComparable arra[idx]! arrb[idx]! = true)
     (hfix : isVariableLengthFormat fmt = false → rowsAreFixedShape arra arrb = true) :
     List Nat := Id.run do
-  if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then
+  if fmt.contains 'P' || fmt.contains 'Q' then
     let mut acc : List Nat := []
     for i in List.finRange arra.length do
       if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
         acc := acc ++ [i.val]
     return acc
   else
-    return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))
+    return rowDiffIndices arra arrb hcmp
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -169,11 +169,14 @@
     (hfix : isVariableLengthFormat fmt = false → rowsAreFixedShape arra arrb = true) :
     List Nat := Id.run do
   if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then
-    let mut acc : List Nat := []
-    for i in List.finRange arra.length do
-      if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
-        acc := acc ++ [i.val]
-    return acc
+    if hg : rowsAreFixedShape arra arrb = true then
+      return elementwiseDiff arra arrb hg
+    else
+      let mut acc : List Nat := []
+      for i in List.finRange arra.length do
+        if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
+          acc := acc ++ [i.val]
+      return acc
   else
     return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))
 -- impl-end
@@ -220,5 +223,8 @@
     rw [h2, columnDiffRows_loop]
     simp
   · simp only [hc]
+    have hs : rowsAreFixedShape arra arrb = true :=
+      hfix (by simpa [isVariableLengthFormat] using hc)
+    simp only [hs, dif_pos]
     rfl
 -- proof-end
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -174,8 +174,10 @@
       if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
         acc := acc ++ [i.val]
     return acc
+  else if hg : rowsAreFixedShape arra arrb = true then
+    return elementwiseDiff arra arrb hg
   else
-    return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))
+    return []
 -- impl-end
 
 -- proof-start
@@ -220,5 +222,8 @@
     rw [h2, columnDiffRows_loop]
     simp
   · simp only [hc]
+    have hs : rowsAreFixedShape arra arrb = true :=
+      hfix (by simpa [isVariableLengthFormat] using hc)
+    simp only [hs, dif_pos]
     rfl
 -- proof-end
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -167,15 +167,19 @@
     (fmt : List Char) (arra arrb : List (List Int))
     (hcmp : ∀ idx, idx < arra.length → rowsComparable arra[idx]! arrb[idx]! = true)
     (hfix : isVariableLengthFormat fmt = false → rowsAreFixedShape arra arrb = true) :
-    List Nat := Id.run do
-  if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then
-    let mut acc : List Nat := []
-    for i in List.finRange arra.length do
-      if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
-        acc := acc ++ [i.val]
-    return acc
+    List Nat :=
+  if arra.length == arrb.length then
+    (Id.run do
+      if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then
+        let mut acc : List Nat := []
+        for i in List.finRange arra.length do
+          if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
+            acc := acc ++ [i.val]
+        return acc
+      else
+        return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb)))
   else
-    return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))
+    [0]
 -- impl-end
 
 -- proof-start
@@ -199,9 +203,10 @@
 
 theorem correct_columnDiffRows :
     columnDiffRowsContract implementation_columnDiffRows := by
-  intro fmt arra arrb _ hcmp hfix
+  intro fmt arra arrb hlen hcmp hfix
   unfold problem_spec_columnDiffRows implementation_columnDiffRows
     isVariableLengthFormat rowDiffIndices
+  simp only [hlen, beq_self_eq_true, if_true]
   by_cases hc : (fmt.contains 'P' || fmt.contains 'Q') = true
   · simp only [hc, dif_pos]
     have h2 : (Id.run (do
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -168,14 +168,17 @@
     (hcmp : ∀ idx, idx < arra.length → rowsComparable arra[idx]! arrb[idx]! = true)
     (hfix : isVariableLengthFormat fmt = false → rowsAreFixedShape arra arrb = true) :
     List Nat := Id.run do
-  if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then
+  if hb : (fmt.contains 'P' || fmt.contains 'Q' || fmt.contains 'D') = true then
     let mut acc : List Nat := []
     for i in List.finRange arra.length do
       if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
         acc := acc ++ [i.val]
     return acc
   else
-    return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))
+    return elementwiseDiff arra arrb (hfix (by
+      simp only [isVariableLengthFormat]
+      intro h
+      exact hfix (by simp only [isVariableLengthFormat]; simpa using h)))
 -- impl-end
 
 -- proof-start
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -171,7 +171,10 @@
   if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then
     let mut acc : List Nat := []
     for i in List.finRange arra.length do
-      if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
+      if hgc : rowsComparable arra[i.val]! arrb[i.val]! = true then
+        if !rowsAgree arra[i.val]! arrb[i.val]! hgc then
+          acc := acc ++ [i.val]
+      else
         acc := acc ++ [i.val]
     return acc
   else
@@ -179,9 +182,7 @@
 -- impl-end
 
 -- proof-start
-/-- The conditional-append loop over `l`, generalized over the accumulator and
-over the row predicate, computes `init` followed by the filtered positions
-(Route B helper). -/
+/-- Loop helper (as in the bundle), generalized over the row predicate. -/
 theorem columnDiffRows_loop {n : Nat} (p : Fin n → Bool) (l : List (Fin n))
     (init : List Nat) :
       Id.run (forIn l init (fun i r =>
@@ -206,17 +207,27 @@
   · simp only [hc, dif_pos]
     have h2 : (Id.run (do
         let r ← forIn (List.finRange arra.length) ([] : List Nat) fun i r =>
-              if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then do
+              if hgc : rowsComparable arra[i.val]! arrb[i.val]! = true then
+                (if !rowsAgree arra[i.val]! arrb[i.val]! hgc then do
+                  pure PUnit.unit
+                  pure (ForInStep.yield (r ++ [i.val]))
+                else do
+                  pure PUnit.unit
+                  pure (ForInStep.yield r))
+              else do
                 pure PUnit.unit
                 pure (ForInStep.yield (r ++ [i.val]))
-              else do
-                pure PUnit.unit
-                pure (ForInStep.yield r)
         pure r))
         = Id.run (forIn (List.finRange arra.length) ([] : List Nat) (fun i r =>
           (if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
              ForInStep.yield (r ++ [i.val])
-           else ForInStep.yield r : Id (ForInStep (List Nat))))) := rfl
+           else ForInStep.yield r : Id (ForInStep (List Nat))))) := by
+      apply congrArg
+      apply forIn_congr rfl
+      intro i _ r
+      have hgc := hcmp i.val i.isLt
+      simp only [dif_pos hgc]
+      rfl
     rw [h2, columnDiffRows_loop]
     simp
   · simp only [hc]
```

Attack 12 — `atk_11b.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -171,7 +171,10 @@
   if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then
     let mut acc : List Nat := []
     for i in List.finRange arra.length do
-      if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
+      if hgc : rowsComparable arra[i.val]! arrb[i.val]! = true then
+        if !rowsAgree arra[i.val]! arrb[i.val]! hgc then
+          acc := acc ++ [i.val]
+      else
         acc := acc ++ [i.val]
     return acc
   else
@@ -179,9 +182,7 @@
 -- impl-end
 
 -- proof-start
-/-- The conditional-append loop over `l`, generalized over the accumulator and
-over the row predicate, computes `init` followed by the filtered positions
-(Route B helper). -/
+/-- Loop helper (as in the bundle), generalized over the row predicate. -/
 theorem columnDiffRows_loop {n : Nat} (p : Fin n → Bool) (l : List (Fin n))
     (init : List Nat) :
       Id.run (forIn l init (fun i r =>
@@ -204,20 +205,47 @@
     isVariableLengthFormat rowDiffIndices
   by_cases hc : (fmt.contains 'P' || fmt.contains 'Q') = true
   · simp only [hc, dif_pos]
+    have key : ∀ (l : List (Fin arra.length)) (init : List Nat),
+        Id.run (forIn l init (fun i r =>
+          (if hgc : rowsComparable arra[i.val]! arrb[i.val]! = true then
+              (if !rowsAgree arra[i.val]! arrb[i.val]! hgc then
+                ForInStep.yield (r ++ [i.val]) else ForInStep.yield r)
+            else ForInStep.yield (r ++ [i.val]) : Id (ForInStep (List Nat)))))
+        = init ++ (l.filter
+            (fun i => !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt))).map Fin.val := by
+      intro l
+      induction l with
+      | nil => intro init; simp; rfl
+      | cons a as ih =>
+        intro init
+        rw [List.forIn_cons, List.filter_cons]
+        have hga := hcmp a.val a.isLt
+        simp only [Id.run, bind, dif_pos hga] at ih ⊢
+        by_cases h : (!rowsAgree arra[a.val]! arrb[a.val]! (hcmp a.val a.isLt)) = true
+        · simp only [h, if_true, if_pos]
+          rw [ih]; simp [List.append_assoc]
+        · simp only [Bool.not_eq_true] at h
+          simp only [h, if_false]
+          rw [ih]; simp
     have h2 : (Id.run (do
         let r ← forIn (List.finRange arra.length) ([] : List Nat) fun i r =>
-              if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then do
+              if hgc : rowsComparable arra[i.val]! arrb[i.val]! = true then
+                (if !rowsAgree arra[i.val]! arrb[i.val]! hgc then do
+                  pure PUnit.unit
+                  pure (ForInStep.yield (r ++ [i.val]))
+                else do
+                  pure PUnit.unit
+                  pure (ForInStep.yield r))
+              else do
                 pure PUnit.unit
                 pure (ForInStep.yield (r ++ [i.val]))
-              else do
-                pure PUnit.unit
-                pure (ForInStep.yield r)
         pure r))
         = Id.run (forIn (List.finRange arra.length) ([] : List Nat) (fun i r =>
-          (if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
-             ForInStep.yield (r ++ [i.val])
-           else ForInStep.yield r : Id (ForInStep (List Nat))))) := rfl
-    rw [h2, columnDiffRows_loop]
+          (if hgc : rowsComparable arra[i.val]! arrb[i.val]! = true then
+              (if !rowsAgree arra[i.val]! arrb[i.val]! hgc then
+                ForInStep.yield (r ++ [i.val]) else ForInStep.yield r)
+            else ForInStep.yield (r ++ [i.val]) : Id (ForInStep (List Nat))))) := rfl
+    rw [h2, key]
     simp
   · simp only [hc]
     rfl
```

Attack 13 — `atk_12.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -174,6 +174,8 @@
       if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
         acc := acc ++ [i.val]
     return acc
+  else if arra == arrb then
+    return []
   else
     return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))
 -- impl-end
```

Attack 14 — `atk_13.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -167,21 +167,23 @@
     (fmt : List Char) (arra arrb : List (List Int))
     (hcmp : ∀ idx, idx < arra.length → rowsComparable arra[idx]! arrb[idx]! = true)
     (hfix : isVariableLengthFormat fmt = false → rowsAreFixedShape arra arrb = true) :
-    List Nat := Id.run do
-  if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then
-    let mut acc : List Nat := []
-    for i in List.finRange arra.length do
-      if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
-        acc := acc ++ [i.val]
-    return acc
+    List Nat :=
+  if h : arra.length = arrb.length then
+    (Id.run do
+      if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then
+        let mut acc : List Nat := []
+        for i in List.finRange arrb.length do
+          if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val (by omega)) then
+            acc := acc ++ [i.val]
+        return acc
+      else
+        return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb)))
   else
-    return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))
+    []
 -- impl-end
 
 -- proof-start
-/-- The conditional-append loop over `l`, generalized over the accumulator and
-over the row predicate, computes `init` followed by the filtered positions
-(Route B helper). -/
+/-- Loop helper (as in the bundle), generalized over the row predicate. -/
 theorem columnDiffRows_loop {n : Nat} (p : Fin n → Bool) (l : List (Fin n))
     (init : List Nat) :
       Id.run (forIn l init (fun i r =>
@@ -199,14 +201,16 @@
 
 theorem correct_columnDiffRows :
     columnDiffRowsContract implementation_columnDiffRows := by
-  intro fmt arra arrb _ hcmp hfix
+  intro fmt arra arrb hlen hcmp hfix
   unfold problem_spec_columnDiffRows implementation_columnDiffRows
     isVariableLengthFormat rowDiffIndices
+  simp only [hlen, dif_pos]
+  subst hlen
   by_cases hc : (fmt.contains 'P' || fmt.contains 'Q') = true
   · simp only [hc, dif_pos]
     have h2 : (Id.run (do
         let r ← forIn (List.finRange arra.length) ([] : List Nat) fun i r =>
-              if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then do
+              if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val (by omega)) then do
                 pure PUnit.unit
                 pure (ForInStep.yield (r ++ [i.val]))
               else do
```

Attack 15 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -174,14 +174,16 @@
       if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
         acc := acc ++ [i.val]
     return acc
+  else if hg : rowsAreFixedShape arra arrb = true then
+    return elementwiseDiff arra arrb hg
+  else if rowsComparable (arra.headD []) (arrb.headD []) then
+    return [0]
   else
-    return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))
+    return []
 -- impl-end
 
 -- proof-start
-/-- The conditional-append loop over `l`, generalized over the accumulator and
-over the row predicate, computes `init` followed by the filtered positions
-(Route B helper). -/
+/-- Loop helper (as in the bundle), generalized over the row predicate. -/
 theorem columnDiffRows_loop {n : Nat} (p : Fin n → Bool) (l : List (Fin n))
     (init : List Nat) :
       Id.run (forIn l init (fun i r =>
@@ -220,5 +222,8 @@
     rw [h2, columnDiffRows_loop]
     simp
   · simp only [hc]
+    have hs : rowsAreFixedShape arra arrb = true :=
+      hfix (by simpa [isVariableLengthFormat] using hc)
+    simp only [hs, dif_pos]
     rfl
 -- proof-end
```

Attack 16 — `atk_15.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -173,7 +173,10 @@
     for i in List.finRange arra.length do
       if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
         acc := acc ++ [i.val]
-    return acc
+    if hg : rowsAreFixedShape arra arrb = true then
+      return acc ++ elementwiseDiff arra arrb hg
+    else
+      return acc
   else
     return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))
 -- impl-end
```

Attack 17 — `atk_16.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -175,13 +175,25 @@
         acc := acc ++ [i.val]
     return acc
   else
-    return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))
+    have hs : rowsAreFixedShape arra arrb = true :=
+      hfix (by simpa [isVariableLengthFormat] using hb)
+    have hs' : rowsAreFixedShape arrb arra = true := by
+      simp only [rowsAreFixedShape] at hs ⊢
+      simp only [rowsComparable] at hs ⊢
+      revert hs
+      simp only [Bool.and_eq_true, beq_iff_eq, Bool.or_eq_true]
+      intro h
+      refine ⟨⟨⟨h.1.1.1.symm, h.1.1.2.2⟩, h.1.1.2.1⟩, ?_⟩
+      rcases h.2 with h2 | h2 | h2
+      · exact Or.inl (Or.inl h2.symm)
+      · exact Or.inl (Or.inr h2)
+      · exact Or.inr h2
+    return elementwiseDiff arrb arra hs'
+
 -- impl-end
 
 -- proof-start
-/-- The conditional-append loop over `l`, generalized over the accumulator and
-over the row predicate, computes `init` followed by the filtered positions
-(Route B helper). -/
+/-- Loop helper (as in the bundle). -/
 theorem columnDiffRows_loop {n : Nat} (p : Fin n → Bool) (l : List (Fin n))
     (init : List Nat) :
       Id.run (forIn l init (fun i r =>
@@ -199,7 +211,7 @@
 
 theorem correct_columnDiffRows :
     columnDiffRowsContract implementation_columnDiffRows := by
-  intro fmt arra arrb _ hcmp hfix
+  intro fmt arra arrb hlen hcmp hfix
   unfold problem_spec_columnDiffRows implementation_columnDiffRows
     isVariableLengthFormat rowDiffIndices
   by_cases hc : (fmt.contains 'P' || fmt.contains 'Q') = true
@@ -220,5 +232,10 @@
     rw [h2, columnDiffRows_loop]
     simp
   · simp only [hc]
-    rfl
+    have hs : rowsAreFixedShape arra arrb = true :=
+      hfix (by simpa [isVariableLengthFormat] using hc)
+    first
+      | rfl
+      | (simp_all [rowsAreFixedShape, rowsComparable]; rfl)
+      | simp_all [rowsAreFixedShape, rowsComparable]
 -- proof-end
```

Attack 18 — `atk_17.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -174,14 +174,15 @@
       if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
         acc := acc ++ [i.val]
     return acc
+  else if arra.length == 0 then
+    return []
   else
     return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))
+
 -- impl-end
 
 -- proof-start
-/-- The conditional-append loop over `l`, generalized over the accumulator and
-over the row predicate, computes `init` followed by the filtered positions
-(Route B helper). -/
+/-- Loop helper (as in the bundle). -/
 theorem columnDiffRows_loop {n : Nat} (p : Fin n → Bool) (l : List (Fin n))
     (init : List Nat) :
       Id.run (forIn l init (fun i r =>
@@ -199,7 +200,7 @@
 
 theorem correct_columnDiffRows :
     columnDiffRowsContract implementation_columnDiffRows := by
-  intro fmt arra arrb _ hcmp hfix
+  intro fmt arra arrb hlen hcmp hfix
   unfold problem_spec_columnDiffRows implementation_columnDiffRows
     isVariableLengthFormat rowDiffIndices
   by_cases hc : (fmt.contains 'P' || fmt.contains 'Q') = true
@@ -220,5 +221,11 @@
     rw [h2, columnDiffRows_loop]
     simp
   · simp only [hc]
-    rfl
+    have hs : rowsAreFixedShape arra arrb = true :=
+      hfix (by simpa [isVariableLengthFormat] using hc)
+    simp only [Nat.beq_eq]
+    first
+      | rfl
+      | (simp_all [rowsAreFixedShape, rowsComparable]; rfl)
+      | simp_all [rowsAreFixedShape, rowsComparable]
 -- proof-end
```

Attack 19 — `atk_18.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -171,11 +171,13 @@
   if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then
     let mut acc : List Nat := []
     for i in List.finRange arra.length do
-      if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
+      if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt)
+          || arra[i.val]!.length != arrb[i.val]!.length then
         acc := acc ++ [i.val]
     return acc
   else
     return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))
+
 -- impl-end
 
 -- proof-start
```

Attack 20 — `atk_19.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -175,13 +175,12 @@
         acc := acc ++ [i.val]
     return acc
   else
-    return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))
+    return (elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))).eraseDups
+
 -- impl-end
 
 -- proof-start
-/-- The conditional-append loop over `l`, generalized over the accumulator and
-over the row predicate, computes `init` followed by the filtered positions
-(Route B helper). -/
+/-- Loop helper (as in the bundle). -/
 theorem columnDiffRows_loop {n : Nat} (p : Fin n → Bool) (l : List (Fin n))
     (init : List Nat) :
       Id.run (forIn l init (fun i r =>
@@ -199,7 +198,7 @@
 
 theorem correct_columnDiffRows :
     columnDiffRowsContract implementation_columnDiffRows := by
-  intro fmt arra arrb _ hcmp hfix
+  intro fmt arra arrb hlen hcmp hfix
   unfold problem_spec_columnDiffRows implementation_columnDiffRows
     isVariableLengthFormat rowDiffIndices
   by_cases hc : (fmt.contains 'P' || fmt.contains 'Q') = true
@@ -220,5 +219,10 @@
     rw [h2, columnDiffRows_loop]
     simp
   · simp only [hc]
-    rfl
+    have hs : rowsAreFixedShape arra arrb = true :=
+      hfix (by simpa [isVariableLengthFormat] using hc)
+    first
+      | rfl
+      | (simp_all [rowsAreFixedShape, rowsComparable]; rfl)
+      | simp_all [rowsAreFixedShape, rowsComparable]
 -- proof-end
```

Attack 21 — `atk_20.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -174,14 +174,15 @@
       if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
         acc := acc ++ [i.val]
     return acc
+  else if hg : rowsAreFixedShape arra arrb = true then
+    return elementwiseDiff arra arrb hg
   else
-    return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))
+    return rowDiffIndices arra arrb hcmp
+
 -- impl-end
 
 -- proof-start
-/-- The conditional-append loop over `l`, generalized over the accumulator and
-over the row predicate, computes `init` followed by the filtered positions
-(Route B helper). -/
+/-- Loop helper (as in the bundle). -/
 theorem columnDiffRows_loop {n : Nat} (p : Fin n → Bool) (l : List (Fin n))
     (init : List Nat) :
       Id.run (forIn l init (fun i r =>
@@ -199,7 +200,7 @@
 
 theorem correct_columnDiffRows :
     columnDiffRowsContract implementation_columnDiffRows := by
-  intro fmt arra arrb _ hcmp hfix
+  intro fmt arra arrb hlen hcmp hfix
   unfold problem_spec_columnDiffRows implementation_columnDiffRows
     isVariableLengthFormat rowDiffIndices
   by_cases hc : (fmt.contains 'P' || fmt.contains 'Q') = true
@@ -220,5 +221,10 @@
     rw [h2, columnDiffRows_loop]
     simp
   · simp only [hc]
-    rfl
+    have hs : rowsAreFixedShape arra arrb = true :=
+      hfix (by simpa [isVariableLengthFormat] using hc)
+    first
+      | rfl
+      | (simp_all [rowsAreFixedShape, rowsComparable]; rfl)
+      | simp_all [rowsAreFixedShape, rowsComparable]
 -- proof-end
```

Attack 22 — `atk_21.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -169,13 +169,18 @@
     (hfix : isVariableLengthFormat fmt = false → rowsAreFixedShape arra arrb = true) :
     List Nat := Id.run do
   if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then
-    let mut acc : List Nat := []
-    for i in List.finRange arra.length do
-      if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
-        acc := acc ++ [i.val]
-    return acc
+    if (List.finRange arra.length).all
+        (fun i => rowsComparable arra[i.val]! arrb[i.val]!) then
+      let mut acc : List Nat := []
+      for i in List.finRange arra.length do
+        if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
+          acc := acc ++ [i.val]
+      return acc
+    else
+      return [0]
   else
     return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))
+
 -- impl-end
 
 -- proof-start
@@ -204,6 +209,12 @@
     isVariableLengthFormat rowDiffIndices
   by_cases hc : (fmt.contains 'P' || fmt.contains 'Q') = true
   · simp only [hc, dif_pos]
+    have hall : (List.finRange arra.length).all
+        (fun i => rowsComparable arra[i.val]! arrb[i.val]!) = true := by
+      simp only [List.all_eq_true]
+      intro i _
+      exact hcmp i.val i.isLt
+    simp only [hall, if_true]
     have h2 : (Id.run (do
         let r ← forIn (List.finRange arra.length) ([] : List Nat) fun i r =>
               if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then do
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** Fresh scratch (worktree wt/ at base_commit c0a24c1dc957a3b565294213f435fefb2ec99714). All 22 attack files + pos_control confirmed byte-identical spec via swebench_unified.markers.same_spec => True (each printed True; note the lean spec_view elides BOTH the impl and the proof region, so proof edits are same-spec too). Verify cmd: `bash scripts/lean_verify.sh <file>` from the repo root, run 4-way concurrent as background jobs. Resolve cmd: `python resolve.py <name>` wrapping swebench_unified.harness.run_resolve('astropy__astropy-14539', <patch text>).

**POSITIVE CONTROL:** pos_control.lean (unmodified Solution.lean) -> exit 0. GOLD RESOLVE CONTROL: cpatch_gold.diff -> resolved=True, applied=True, F2P 2/2, P2P 46/46 => harness+image healthy, so the resolve results below are the impls' own behavior.

### REJECTED (exit 1 -- no proof closes; 16 of 21):
- atk_1 PREPATCH BUG re-encoded: 'P'-only branch predicate (diff.py:1452 pre-patch), Q-format column mis-routed to the flat comparison, reaching it by self-testing rowsAreFixedShape exactly as the accepted Solution_prepatch.lean twin does. exit 1 (2 errors; missing elementwiseDiff defining equation + absent row-wise rewrite pattern, matching refinement.md's quoted errors). PREPATCH REPRODUCED.
- atk_2 MIRROR mis-routing: 'Q'-only predicate, so a 'P' column (PI(2), the pre-existing suite) is mis-routed. exit 1 => the spec pins BOTH markers, confirming mapping.md's claim that a Q-only spec would be wrong about the gold.
- atk_3 PARTIAL DOMAIN: VLA arm tests only rows of equal stored length, skipping the ragged reproducer shape [[0],[0,0]]. exit 1.
- atk_4 BOUNDARY: VLA arm never reports row 0 (the reproducer's differing row, the F2P ('K',0) assertion). exit 1.
- atk_5 CONTROL-FLOW EFFECT: same rows, prepend instead of append => decreasing order. exit 1 => the increasing-order leg (refinement row 3) is pinned.
- atk_6 UNGROUNDED-ORACLE ECHO (flat arm): non-VLA column answered with rowDiffIndices. exit 1 => routing pinned where hfix is inhabited.
- atk_7 UNGROUNDED-ORACLE ECHO (VLA arm): a RECTANGULAR VLA column (QJ(2) with rows [0,1]/[2,3] -- exactly the F2P fixture, where rowsAreFixedShape is TRUE) answered with the flat comparison. exit 1 => the VLA arm is pinned even where the other callee's domain argument is available. This is the sharpest test of the current repair and it holds.
- atk_10 OVER-BROAD predicate ('D' also treated variable-length). exit 1.
- atk_11 / atk_11b UNREACHABLE-ARM GARBAGE guarded on the DECIDABLE per-row predicate rowsComparable (two different proof scripts, incl. a hand-rolled induction). exit 1 => refinement.md's central A-leg claim ('carried as an argument, the same impl cannot be written down') is weaker than stated -- the arm IS writable -- but the loop's pointwise structure still blocks the proof, so it costs no strength here.
- atk_12 SMUGGLED PROPERTY: flat arm shortcuts to [] when the columns are structurally equal (TRUE of the real np.where). exit 1 => no callee property leaks in.
- atk_13 row domain taken from arrb.length via the hlen hypothesis. exit 1.
- atk_15 VLA report with the flat report APPENDED. exit 1 => 'nothing added' is pinned.
- atk_16 SMUGGLED SYMMETRY: flat arm called with the two columns SWAPPED (behaviorally identical in the repo; refinement.md explicitly says this must NOT be admitted). exit 1 => matches the documented claim.
- atk_17 empty-column shortcut [] on the flat arm. exit 1.
- atk_18 the PREVIOUS REVISION'S DEFECT re-encoded reachably: a row reported when the test rejects it OR the two stored lengths differ, i.e. sequence-inequality at the reproducer shape where np.allclose broadcasts and AGREES. exit 1 => the abstraction repair holds.
- atk_19 SMUGGLED DEDUP of the opaque flat report (defensible, since np.where does yield duplicate row indices on a multi-dim column -- which is why diff.py keeps last_seen_idx). exit 1.

VERIFIED, CLEAN AXIOMS, PATCH RESOLVES (5 of 21) -- each `#print axioms` probe ran as its own file at exit 0, no sorryAx, no sorry/admit/native_decide/axiom token in any source:
- atk_8 (old bundle's exploit retargeted at the REPAIRED predicate: flat arm self-guards on rowsAreFixedShape, [] otherwise). exit 0; ax_8.lean exit 0, correct=[propext, Quot.sound], implementation=[propext]. cpatch_atk_8.diff -> resolved=TRUE, applied=True, F2P 2/2, P2P 46/46.
- atk_9 (row-count vacuity: [0] at unequal row counts). exit 0; ax_9.lean exit 0, correct=[propext, Classical.choice, Quot.sound], implementation=[propext]. cpatch_atk_9.diff -> resolved=TRUE, F2P 2/2, P2P 46/46.
- atk_14 (WEAKER head-only self-guard: [0] on ragged non-VLA pairs, e.g. [[1],[2,3]] vs [[4],[5,6]]). exit 0; ax_14.lean exit 0, [propext, Quot.sound]. cpatch_atk_14.diff -> resolved=TRUE, F2P 2/2, P2P 46/46.
- atk_20 (ragged non-VLA answered with the ROW-WISE report). exit 0; ax_20.lean exit 0, [propext, Classical.choice, Quot.sound]. cpatch_atk_20.diff -> resolved=TRUE, F2P 2/2, P2P 46/46.
- atk_21 (hcmp-side analogue of the HISTORICAL rowsAreSingleValued hole: the impl DECIDES whether every row is comparable and answers [0] for the whole column where it is not, instead of letting np.allclose raise). exit 0; ax_21.lean exit 0, [propext, Quot.sound]. cpatch_atk_21.diff -> resolved=TRUE, F2P 2/2, P2P 46/46.

All five patches were built as unified diffs against the base worktree, `git apply --check` rc=0 and py_compile rc=0 before running. Each was resolved TWICE: once in a verbose form (patch_atk_*.diff, resolve_atk_*.json) and once in the compact form actually submitted (cpatch_atk_*.diff, cresolve_atk_*.json); both rounds agree -- all resolved=True with 2/2 F2P and 46/46 P2P. No speculation: every reported resolve is an executed run.

**WHY NOT BROKEN.** The five verifiers all exploit the same structural fact -- a domain argument (hcmp / hfix) or a contract hypothesis (hlen) leaves the complement of a DECIDABLE pure predicate outside the demand, so an impl may add an arm there. That is the exact shape of the hole this bundle was previously BROKEN on (verdict.md Role 1: rowsAreSingleValued was false at every ordinary multi-valued column, including the 4I/dim='(2,2)' column both F2P tests assert on, so atk_2/7/8 verified and their patches FAILED). The repair to rowsAreFixedShape closes that hole: the predicate is now TRUE at the 4I/dim column, so hfix is inhabited there, elementwiseDiff must be consulted, and atk_7 -- the direct re-encoding of that old exploit's live direction -- is now REJECTED.

What remains outside the demand is genuinely dead in the repository: (a) unequal row counts, because `_diff` returns at diff.py:1409-1411 before the per-column loop; (b) non-VLA columns that are not rectangular, impossible because common_columns is a set intersection under Column.`__eq__`/`__hash__` keyed on (name.lower(), format) (column.py:736-753), so both columns share a declared format and a non-VLA FITS format denotes a fixed-width block; (c) rows np.allclose cannot relate, where the real routine raises ValueError and has no output. Hence every faithful patch resolves, and the residual vacuity costs no discriminating power.

A-LEG / refinement.md AUDIT (§5 kinds). Seven legs, all tagged R, no A-consumed and no A-reference rows, and that tagging is CORRECT as far as the axiom evidence goes: rowsAgree and elementwiseDiff are `opaque` (signature only, no defining equation, no stated property), the proof consumes no property of either, `#print axioms` on the gold and on all five verifiers shows only [propext, Quot.sound] (+Classical.choice) with no callee axiom and no sorryAx, and axiom_check.py is a legitimate skip stub. No kind-3 (unjustified) leg. The two opaque callees are correctly identified against the real code: rowsAgree <-> np.allclose(arra[idx], arrb[idx], rtol, atol) at diff.py:1457-1459, elementwiseDiff <-> np.where(arra != arrb) at diff.py:1463, and row 1's predicate is the patched line 1452 verbatim -- I confirmed all four line references in the worktree. The model<->patch correspondence holds: the patch's only net effect is widening the branch predicate, and that is row 1.

Two advisory (non-blocking) accuracy notes on refinement.md, neither a strength defect:
1. Rows 6-7's justification overstates the argument-vs-side-condition distinction: 'Carried as an argument of the callee, the same impl cannot be written down -- the fact simply is not available at that row.' atk_11 shows the impl CAN be written down -- the pure predicate rowsComparable is decidable, so an impl may branch on it, obtain the fact in the positive arm, and put anything in the negative arm. What actually rejects atk_11/atk_8/atk_20-style impls is not inexpressibility but (for the VLA loop) the pointwise proof obligation, and for the flat arm the fact that the complementary arm is dead in the real code. The file's own §'That shape has a price' paragraph gets this right for row 7; the row 6 prose should be aligned with it.
2. The two domain predicates are still narrower than the real callees in ways the file counts honestly (row 7 records the 40-pair unequal-row-count gap) but the resulting vacuous region is what all five verifiers live in. Since the region is dead in the repository the spec loses nothing today, but it is the same mechanism as the previously-broken revision, so any future widening of the modeled domain (e.g. modeling the row-count-mismatch path, or non-common columns) would need the predicates re-measured first.

EVIDENCE FILES (all): gen.py, gen2.py, gen3.py (attack generators); mkpatch.py, mkpatch2.py, mkpatch3.py (patch materializers); resolve.py; pos_control.lean, atk_{1..21,11b}.lean, ax_{8,9,14,20,21}.lean and their .log files; results{,2,3,4}.txt (exit codes); cpatch_{gold,atk_8,atk_9,atk_14,atk_20,atk_21}.diff and patch_* (verbose round); cresolve_*.json / resolve_*.json (harness reports); cdiffpy_*.py (fully-patched files, py_compile clean); wt/ (worktree at base_commit).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 22 admissible attacks re-run of 22 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 22 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 17 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_10.lean`, `atk_11.lean`, `atk_11b.lean`, `atk_12.lean`, `atk_13.lean`, `atk_15.lean`, `atk_16.lean`, `atk_17.lean`, `atk_18.lean`, `atk_19.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_8.lean`, `atk_9.lean`, `atk_14.lean`, `atk_20.lean`, `atk_21.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No counterexample: no same-spec wrong impl with a closing clean-axiom proof has a faithful patch that fails to resolve. 21 attacks run; 16 REJECTED by the proof; 5 verified (atk_8, atk_9, atk_14, atk_20, atk_21) and ALL FIVE faithful patches RESOLVE under the official harness (2/2 F2P, 46/46 P2P), same as the gold control. The five verifiers are exactly the impls that add an arm guarded on a decidably-FALSE fact the contract's own hypotheses make unreachable (the complement of `rowsAreFixedShape` / `rowsComparable`, or unequal row counts). That is admissible-not-broken here because those arms are also unreachable in the REPOSITORY: `TableDataDiff._diff` returns before the per-column loop when row counts differ (diff.py:1409-1411, so atk_9's arm is dead), and `common_columns` is an intersection under `Column.__eq__`, which keys on `(name.lower(), format)` (column.py:736-744), so the two compared columns ALWAYS share a declared format and a non-VLA format always denotes rectangular storage (atk_8/atk_14/atk_20's arms are dead). atk_21's arm is reachable only where the real `np.allclose` RAISES ValueError, i.e. where the routine has no output to be faithful to. Every added arm is therefore dead code in the real repository, which is why each patch resolves rather than exposing a hole.
```

**Attacks re-run (22):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 22 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_11b.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 16 — `atk_15.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_16.lean` → rejected (same spec, does not verify — good)

Attack 18 — `atk_17.lean` → rejected (same spec, does not verify — good)

Attack 19 — `atk_18.lean` → rejected (same spec, does not verify — good)

Attack 20 — `atk_19.lean` → rejected (same spec, does not verify — good)

Attack 21 — `atk_20.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 22 — `atk_21.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** Fresh scratch (worktree wt/ at base_commit c0a24c1dc957a3b565294213f435fefb2ec99714). All 22 attack files + pos_control confirmed byte-identical spec via swebench_unified.markers.same_spec => True (each printed True; note the lean spec_view elides BOTH the impl and the proof region, so proof edits are same-spec too). Verify cmd: `bash scripts/lean_verify.sh <file>` from the repo root, run 4-way concurrent as background jobs. Resolve cmd: `python resolve.py <name>` wrapping swebench_unified.harness.run_resolve('astropy__astropy-14539', <patch text>).

**POSITIVE CONTROL:** pos_control.lean (unmodified Solution.lean) -> exit 0. GOLD RESOLVE CONTROL: cpatch_gold.diff -> resolved=True, applied=True, F2P 2/2, P2P 46/46 => harness+image healthy, so the resolve results below are the impls' own behavior.

### REJECTED (exit 1 -- no proof closes; 16 of 21):
- atk_1 PREPATCH BUG re-encoded: 'P'-only branch predicate (diff.py:1452 pre-patch), Q-format column mis-routed to the flat comparison, reaching it by self-testing rowsAreFixedShape exactly as the accepted Solution_prepatch.lean twin does. exit 1 (2 errors; missing elementwiseDiff defining equation + absent row-wise rewrite pattern, matching refinement.md's quoted errors). PREPATCH REPRODUCED.
- atk_2 MIRROR mis-routing: 'Q'-only predicate, so a 'P' column (PI(2), the pre-existing suite) is mis-routed. exit 1 => the spec pins BOTH markers, confirming mapping.md's claim that a Q-only spec would be wrong about the gold.
- atk_3 PARTIAL DOMAIN: VLA arm tests only rows of equal stored length, skipping the ragged reproducer shape [[0],[0,0]]. exit 1.
- atk_4 BOUNDARY: VLA arm never reports row 0 (the reproducer's differing row, the F2P ('K',0) assertion). exit 1.
- atk_5 CONTROL-FLOW EFFECT: same rows, prepend instead of append => decreasing order. exit 1 => the increasing-order leg (refinement row 3) is pinned.
- atk_6 UNGROUNDED-ORACLE ECHO (flat arm): non-VLA column answered with rowDiffIndices. exit 1 => routing pinned where hfix is inhabited.
- atk_7 UNGROUNDED-ORACLE ECHO (VLA arm): a RECTANGULAR VLA column (QJ(2) with rows [0,1]/[2,3] -- exactly the F2P fixture, where rowsAreFixedShape is TRUE) answered with the flat comparison. exit 1 => the VLA arm is pinned even where the other callee's domain argument is available. This is the sharpest test of the current repair and it holds.
- atk_10 OVER-BROAD predicate ('D' also treated variable-length). exit 1.
- atk_11 / atk_11b UNREACHABLE-ARM GARBAGE guarded on the DECIDABLE per-row predicate rowsComparable (two different proof scripts, incl. a hand-rolled induction). exit 1 => refinement.md's central A-leg claim ('carried as an argument, the same impl cannot be written down') is weaker than stated -- the arm IS writable -- but the loop's pointwise structure still blocks the proof, so it costs no strength here.
- atk_12 SMUGGLED PROPERTY: flat arm shortcuts to [] when the columns are structurally equal (TRUE of the real np.where). exit 1 => no callee property leaks in.
- atk_13 row domain taken from arrb.length via the hlen hypothesis. exit 1.
- atk_15 VLA report with the flat report APPENDED. exit 1 => 'nothing added' is pinned.
- atk_16 SMUGGLED SYMMETRY: flat arm called with the two columns SWAPPED (behaviorally identical in the repo; refinement.md explicitly says this must NOT be admitted). exit 1 => matches the documented claim.
- atk_17 empty-column shortcut [] on the flat arm. exit 1.
- atk_18 the PREVIOUS REVISION'S DEFECT re-encoded reachably: a row reported when the test rejects it OR the two stored lengths differ, i.e. sequence-inequality at the reproducer shape where np.allclose broadcasts and AGREES. exit 1 => the abstraction repair holds.
- atk_19 SMUGGLED DEDUP of the opaque flat report (defensible, since np.where does yield duplicate row indices on a multi-dim column -- which is why diff.py keeps last_seen_idx). exit 1.

VERIFIED, CLEAN AXIOMS, PATCH RESOLVES (5 of 21) -- each `#print axioms` probe ran as its own file at exit 0, no sorryAx, no sorry/admit/native_decide/axiom token in any source:
- atk_8 (old bundle's exploit retargeted at the REPAIRED predicate: flat arm self-guards on rowsAreFixedShape, [] otherwise). exit 0; ax_8.lean exit 0, correct=[propext, Quot.sound], implementation=[propext]. cpatch_atk_8.diff -> resolved=TRUE, applied=True, F2P 2/2, P2P 46/46.
- atk_9 (row-count vacuity: [0] at unequal row counts). exit 0; ax_9.lean exit 0, correct=[propext, Classical.choice, Quot.sound], implementation=[propext]. cpatch_atk_9.diff -> resolved=TRUE, F2P 2/2, P2P 46/46.
- atk_14 (WEAKER head-only self-guard: [0] on ragged non-VLA pairs, e.g. [[1],[2,3]] vs [[4],[5,6]]). exit 0; ax_14.lean exit 0, [propext, Quot.sound]. cpatch_atk_14.diff -> resolved=TRUE, F2P 2/2, P2P 46/46.
- atk_20 (ragged non-VLA answered with the ROW-WISE report). exit 0; ax_20.lean exit 0, [propext, Classical.choice, Quot.sound]. cpatch_atk_20.diff -> resolved=TRUE, F2P 2/2, P2P 46/46.
- atk_21 (hcmp-side analogue of the HISTORICAL rowsAreSingleValued hole: the impl DECIDES whether every row is comparable and answers [0] for the whole column where it is not, instead of letting np.allclose raise). exit 0; ax_21.lean exit 0, [propext, Quot.sound]. cpatch_atk_21.diff -> resolved=TRUE, F2P 2/2, P2P 46/46.

All five patches were built as unified diffs against the base worktree, `git apply --check` rc=0 and py_compile rc=0 before running. Each was resolved TWICE: once in a verbose form (patch_atk_*.diff, resolve_atk_*.json) and once in the compact form actually submitted (cpatch_atk_*.diff, cresolve_atk_*.json); both rounds agree -- all resolved=True with 2/2 F2P and 46/46 P2P. No speculation: every reported resolve is an executed run.

**WHY NOT BROKEN.** The five verifiers all exploit the same structural fact -- a domain argument (hcmp / hfix) or a contract hypothesis (hlen) leaves the complement of a DECIDABLE pure predicate outside the demand, so an impl may add an arm there. That is the exact shape of the hole this bundle was previously BROKEN on (verdict.md Role 1: rowsAreSingleValued was false at every ordinary multi-valued column, including the 4I/dim='(2,2)' column both F2P tests assert on, so atk_2/7/8 verified and their patches FAILED). The repair to rowsAreFixedShape closes that hole: the predicate is now TRUE at the 4I/dim column, so hfix is inhabited there, elementwiseDiff must be consulted, and atk_7 -- the direct re-encoding of that old exploit's live direction -- is now REJECTED.

What remains outside the demand is genuinely dead in the repository: (a) unequal row counts, because `_diff` returns at diff.py:1409-1411 before the per-column loop; (b) non-VLA columns that are not rectangular, impossible because common_columns is a set intersection under Column.`__eq__`/`__hash__` keyed on (name.lower(), format) (column.py:736-753), so both columns share a declared format and a non-VLA FITS format denotes a fixed-width block; (c) rows np.allclose cannot relate, where the real routine raises ValueError and has no output. Hence every faithful patch resolves, and the residual vacuity costs no discriminating power.

A-LEG / refinement.md AUDIT (§5 kinds). Seven legs, all tagged R, no A-consumed and no A-reference rows, and that tagging is CORRECT as far as the axiom evidence goes: rowsAgree and elementwiseDiff are `opaque` (signature only, no defining equation, no stated property), the proof consumes no property of either, `#print axioms` on the gold and on all five verifiers shows only [propext, Quot.sound] (+Classical.choice) with no callee axiom and no sorryAx, and axiom_check.py is a legitimate skip stub. No kind-3 (unjustified) leg. The two opaque callees are correctly identified against the real code: rowsAgree <-> np.allclose(arra[idx], arrb[idx], rtol, atol) at diff.py:1457-1459, elementwiseDiff <-> np.where(arra != arrb) at diff.py:1463, and row 1's predicate is the patched line 1452 verbatim -- I confirmed all four line references in the worktree. The model<->patch correspondence holds: the patch's only net effect is widening the branch predicate, and that is row 1.

Two advisory (non-blocking) accuracy notes on refinement.md, neither a strength defect:
1. Rows 6-7's justification overstates the argument-vs-side-condition distinction: 'Carried as an argument of the callee, the same impl cannot be written down -- the fact simply is not available at that row.' atk_11 shows the impl CAN be written down -- the pure predicate rowsComparable is decidable, so an impl may branch on it, obtain the fact in the positive arm, and put anything in the negative arm. What actually rejects atk_11/atk_8/atk_20-style impls is not inexpressibility but (for the VLA loop) the pointwise proof obligation, and for the flat arm the fact that the complementary arm is dead in the real code. The file's own §'That shape has a price' paragraph gets this right for row 7; the row 6 prose should be aligned with it.
2. The two domain predicates are still narrower than the real callees in ways the file counts honestly (row 7 records the 40-pair unequal-row-count gap) but the resulting vacuous region is what all five verifiers live in. Since the region is dead in the repository the spec loses nothing today, but it is the same mechanism as the previously-broken revision, so any future widening of the modeled domain (e.g. modeling the row-count-mismatch path, or non-common columns) would need the predicates re-measured first.

EVIDENCE FILES (all): gen.py, gen2.py, gen3.py (attack generators); mkpatch.py, mkpatch2.py, mkpatch3.py (patch materializers); resolve.py; pos_control.lean, atk_{1..21,11b}.lean, ax_{8,9,14,20,21}.lean and their .log files; results{,2,3,4}.txt (exit codes); cpatch_{gold,atk_8,atk_9,atk_14,atk_20,atk_21}.diff and patch_* (verbose round); cresolve_*.json / resolve_*.json (harness reports); cdiffpy_*.py (fully-patched files, py_compile clean); wt/ (worktree at base_commit).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**VERDICT:** FAITHFUL. Artifact integrity: Solution.lean verifies exit 0 under scripts/lean_verify.sh; '#print axioms' is CLEAN on all three key declarations — correct_columnDiffRows depends on [propext, Quot.sound], implementation/problem_spec on [propext]; NO sorryAx, so the proof is real. markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True: the spec/pure/axioms regions are byte-identical and the twin differs only in the impl region. properties.py imports OK (24 names) — battery is not broken, so the cell is not capped red.

**Reference discipline:** I used post-patch as the reference for the modeled function, per the brief. The base worktree is at base_commit c0a24c1dc9 and is UNPATCHED (diff.py:1452 reads 'elif "P" in col.format:'); the installed astropy 5.3 / numpy 1.26.4 differs from base in exactly the one patched line ('or "Q" in col.format'), so I used it as the post-patch oracle and did not report the P-vs-Q delta as drift.

Evidence FOR faithfulness, all measured against the real post-patch code:
1. Patched predicate exact. isVariableLengthFormat = contains 'P' || contains 'Q' mirrors diff.py:1452 verbatim. Probed 17 VLA formats (PD,QD,PE,QE,PJ,QJ,PB,QI,PL,PC,PM,QC,QM,PA,QA,PD(5),QD(5)): ALL store as dtype=object, so np.issubdtype(...,np.floating) is False for every one and the FLOATING branch at diff.py:1448 never preempts the VLA branch — the two-branch model is not missing a live third arm on the modeled domain. Converse also clean: swept 13 non-VLA formats (J,4I,D,E,A10,L,X,B,K,C,M,I,2D) and no stored col.format contains 'P' or 'Q', so no false positive routes a fixed-shape column to the row-wise arm.
2. Uniform-length VLA still VLA. QD/QJ/PD/PE with equal-length rows remain dtype=object, so the selector really is a property of the FORMAT alone and never of the stored values — exactly what the spec prose claims.
3. Report shape leg. Row-wise report == [idx for idx in range(len(arra)) if not allclose]: 9,574 in-domain fuzzed column pairs, 0 mismatches. Full end-to-end through real TableDataDiff(numdiffs=-1) over QJ/PJ/QD/PD/QI/QK: 2,535 in-domain columns, 0 mismatches. Ragged and empty rows confirmed individually ([[],[1]], [[]], [[1]] vs [[]], [[]] vs [[1]]): real == model on all.
4. rowsComparable is EXACT. Exhaustive over row lengths 0..5 (36 length pairs): np.allclose answers iff equal lengths or one side length 1 — 0 mismatches. Confirms the per-row domain predicate is neither too wide nor too narrow.
5. Abstraction of the callees is justified, not laziness. np.allclose is genuinely ASYMMETRIC (rtol=0.5: allclose([1],[2])=True but allclose([2],[1])=False), so refusing to assume rowsAgree x y = rowsAgree y x is correct rather than gratuitously strict. where_not_allclose(rtol=0,atol=0) == np.where(a!=b) on 3,000 integer-valued float arrays, consistent with the floating arm being a separate, out-of-scope computation.
6. Non-vacuity proved in Lean, not argued. At the problem statement's own ragged reproducer I discharged: rowsComparable [0] [0,0] = true, isVariableLengthFormat ['Q','D'] = true, the hcmp argument is INHABITED at [[0]] vs [[0,0]] (by decide), and problem_spec reduces there to 'r = rowDiffIndices ...' (exit 0). So the hcmp/hfix-as-argument design has NOT emptied the obligation at the very input the patch is about — the trap flagged in refinement.md's own history is genuinely closed.

Residual, reported and not argued away: the flat-domain predicate is over-wide at 18 equal-row-count shape pairs (model in-domain, real raises), reachable in practice only via the same-format/different-dim route above since differing formats make the column non-common (verified: 'J' vs '3J' yields common_columns == [], so the width-1-vs-width-3 broadcast failure never reaches the loop). Over-wideness on an opaque, property-free callee cannot condemn correct code, so it is a documentation defect (the false 'same shape either way' flattening claim) rather than a spec-strength defect. Not sufficient for UNFAITHFUL.

Counterexample / evidence:

```
No counterexample condemning the spec. Measured NARROW-direction (obligation-deleting) mismatches — where real np.where answers but rowsAreFixedShape refuses, which would silently delete the postcondition — occur at exactly 12 points, ALL of them nrows=0 (e.g. n=0,wa=0,wb=2). Those are unreachable: TableDataDiff._diff returns before the per-column loop when 'len(self.a) == len(self.b) == 0' (diff.py:1471-1472), so no report exists there to lose. At every reachable equal-row-count shape the predicate is exact or over-wide, never narrow. Prepatch control behaves correctly: Solution_prepatch.lean FAILS to verify (exit 1, 2 errors — the rewrite cannot find the row-wise pattern in the 'P'-only body and the fixed-shape arm is not closable by rfl), confirming the spec discriminates the bug rather than admitting both.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `properties.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**SCOPE.** No relaxation claim to weigh: `find . -iname '*RELAX*'` under the instance dir is EMPTY, and meta.json has NO top-level `relaxed_leakage` key (keys enumerated: axioms, conf_skip, deep_model_references, gates, modeled_functions, opaque_callees, patch_equals_gold, pbt_audit, prepatch_variants, refinement_domain, region_hashes, schema_version, spec_provenance, spec_repair, verifier_pins). The only 'relaxed_leakage' strings in meta.json are inside PRIOR G-PANEL-3 note text, i.e. an earlier auditor quoting the absence -- not a disposition. gates.G-LEAK.status == 'pass', not 'relaxed'. mapping.md L82-87 affirmatively DECLINES relaxation, arguing the discriminator is public. So I judged the leak question de novo against the solver-visible problem_statement only; hints_text (which says verbatim 'Seems due to the use of Q, only P is handled in the diff code' plus the whole gold hunk) was read only to confirm the spec view does NOT echo its privileged framing, never as a screening baseline.

**MECHANICAL.** markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) == True, so the twin discriminates on the impl region alone and the spec view I screened is the one the consumer sees. meta.region_hashes matches markers.region_hashes recomputed from Solution.lean digit-for-digit on all six regions (spec_view 61946cb886...). leakage.screen(src, LeanBackend, gold_patch, problem_statement) -> passed=True, hard_failures=[], warnings=[] -- no diff marker, no gold line reproduced (>=8 normalized chars), no patched path 'astropy/io/fits/diff.py' or dotted module, no L3 narration, no L2/L5 symbol collision.

On that last one I checked WHY it passes rather than trusting it: the hunk section_header is `def _diff(self):`, so `_patch_changed_symbols` yields {'diff'}, which IS embedded by three spec-view identifiers (rowDiffIndices, elementwiseDiff, columnDiffRowsContract) and is exempted only because 'diff' is in the problem_statement ('FITSDiff', 'differences', 'printdiff'). That exemption is sound here -- the token is thoroughly public and localizes nothing. leakage.reviewer_directed() returns [] on ALL ten bundle files (mapping.md, refinement.md, verdict.md, meta.json, both .lean, properties.py, conformance_check.py, axiom_check.py, patch.diff): nothing in this bundle addresses me or prescribes a verdict, and I found no such steering by reading either.

G-VERIFY reconfirmed: lean_verify.sh Solution.lean exit 0, and `#print axioms correct_columnDiffRows` -> [propext, Quot.sound] -- no sorryAx, no custom axiom (G-AX skip stub is legitimate; both callees are opaque with no consumed property).

**SUBSTANTIVE FACET RE-DERIVED:** the two format-marker literals. `fmt.contains 'P' || fmt.contains 'Q'` is the ONE place a marker letter appears in the spec view (regex over the view: exactly that single occurrence). I re-derived unavoidability myself rather than accepting mapping.md's argument. (a) Q is PUBLIC verbatim: problem_statement's reproducer is `fits.Column('a', format='QD', array=[[0], [0, 0]])` and its Description names 'VLAs (variable-length arrays)', so the tested discriminator is stated publicly; the ragged row shape the domain predicates are about is public in that same literal.

(b) P is not the discriminator and is not gratuitous -- it is the marker the PRE-patch code ALREADY handled, and I confirmed it is in the solver-visible base source: `git show c0a24c1dc957a3b565294213f435fefb2ec99714:astropy/io/fits/diff.py` shows `elif "P" in col.format:` at the branch. A spec naming only Q would be WRONG about gold, which I measured, not argued: with `isVariableLengthFormat fmt = fmt.contains 'Q'` the gold impl does NOT verify (exit 1), and the refutation `(rowsAgree [1,2] [3,4] = false) -> (elementwiseDiff [[1,2]] [[3,4]] != [0]) -> not problem_spec ['P'] [[1,2]] [[3,4]] [0]` ELABORATES against that Q-only spec (exit 0) -- a semantic rejection at a named P-format input, not a tactic slip.

Both controls behave: the same refutation FAILS against the real symmetric Solution.lean (exit 1), and False is NOT derivable from the hypothesis group alone (consistency probe, exit 1). So the P disjunct is load-bearing; strip it and the spec stops holding of the gold. (c) The residual disclosure is only the SYMMETRIC fact that both letters mark a variable-length format.

The view nowhere says which marker the pre-patch code lacked, nor that anything was added -- and I confirmed the earlier revision's leaking narration is genuinely gone: no match in the view for 'equal in force', 'two such markers', 'descriptor width', 'missing', 'only one', 'omitted', 'spurious', 'ValueError', 'crash', or any repo token (diff.py, col.format, np.allclose, np.where, FITSDiff, TableDataDiff, QD, QJ all absent). The isVariableLengthFormat docstring now says only that a variable-length format carries a variable-length descriptor marker. The two prose hits for my narration wordlist are innocent: 'nothing added to it' (describing the flat report being unaltered) and 'descriptor marker'.

**WHY THAT IS NOT LEAKAGE.** The edit's derivation available to a solver is problem_statement (a QD/VLA column is mishandled; self-comparison must report nothing) + the public base source (only P routed to the row-wise branch) -- that is the intended solve path, not something the spec view supplies. What the view adds beyond it is a symmetric behavioral requirement with the pre-patch/post-patch asymmetry deliberately erased, and the alternative shapes are worse or unfaithful: abstracting the selector to an `isVarLen : Bool` input makes pre- and post-patch the SAME function, leaving G-DIFF nothing to discriminate (and abstracting the changed operation is what the spec guide forbids). No line of the spec view localizes the edit beyond the public facet.

**VERDICT:** NO-LEAKAGE. Facet re-confirmed by measurement (Q-only spec exit 1; P-input refutation exit 0 with both controls correct; base-commit `elif "P" in col.format:` read directly), mechanical screen clean, axioms clean, same_spec True, region hashes matching, no reviewer-directed content anywhere in the bundle.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
