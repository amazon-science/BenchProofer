# P2 adversarial audit — sympy__sympy-16450

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1_prepatch.lean`, `atk_2_partial.lean`, `atk_3_boundary.lean`, `atk_4_cfeffect.lean`, `atk_5_echo.lean`, `atk_6_leak.lean`, `atk_8_declorder.lean`, `atk_9_dropref.lean`, `atk_10_widen.lean`, `atk_11_stripkey.lean`, `atk_14_leak2.lean`, `atk_15_firstrec.lean`, `atk_16_inject.lean`, `atk_17_negfilter.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_7_identity.lean`, `atk_12_dedupdef.lean`, `atk_13_probeall.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No same-spec wrong implementation with a closing clean-axiom proof has a faithful refined patch that fails to resolve. 17 attacks were run: 14 were REFUTED by the spec (lean_verify exit 1), and the 3 that closed with clean axioms were materialized as faithful patches, applied at base_commit, and RUN through the official harness (run_resolve) -- all 3 returned resolved=true, F2P success=['test_posify'], P2P failures=[] (38/38). The prior recorded BROKEN counterexample (atk_13/atk_14 in verdict.md: the TOTALITY / evaluation-domain hole where a total pure `resolveAssumptions` made map and filter commute) was re-encoded twice against the repaired spec -- atk_6_leak (definedness propagated from EVERY symbol, selection afterwards, the literal atk_13 shape) and atk_14_leak2 (a `find?` pre-scan over the whole list that propagates a refusal from a NOT-replaced symbol) -- and BOTH are now genuinely refuted with semantic `unsolved goals` on the definedness-scope clause, not tactic artifacts. The repair (carrying the partial inference as an operation on its DOMAIN, `resolveAssumptions : (decl) -> declAccepted decl = true -> Assumptions`, with the spec's `dite` scoping definedness to the KEPT declarations) closes that hole.
```

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -128,8 +128,10 @@
   | [] => some []
   | a :: as =>
     if signUndetermined a then
-      if h : declAccepted (assertPositive a) = true then
-        (implementation_posify as).map (fun rs => resolveAssumptions (assertPositive a) h :: rs)
+      -- PREPATCH: the replacement is declared with a BARE positivity assertion;
+      -- the original symbol's other declared properties are dropped.
+      if h : declAccepted [("positive", true)] = true then
+        (implementation_posify as).map (fun rs => resolveAssumptions [("positive", true)] h :: rs)
       else
         none
     else
@@ -141,28 +143,47 @@
     ∀ (syms : List Assumptions),
       problem_spec_posify syms (implementation_posify syms) := by
   intro syms
-  induction syms with
-  | nil => simp [problem_spec_posify, implementation_posify]
-  | cons a as ih =>
-    unfold problem_spec_posify at ih ⊢
-    rw [List.filter_cons]
-    by_cases hs : signUndetermined a = true
-    · rw [if_pos hs]
-      by_cases hd : declAccepted (assertPositive a) = true
-      · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
-            declAccepted (assertPositive x) = true
-        · rw [dif_pos ht] at ih
-          rw [dif_pos (fun x hx => by
-            rcases List.mem_cons.mp hx with h' | h'
-            · subst h'; exact hd
-            · exact ht x h')]
-          simp [implementation_posify, hs, hd, ih, List.pmap]
-        · rw [dif_neg ht] at ih
-          rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
-          simp [implementation_posify, hs, hd, ih]
-      · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
-        simp [implementation_posify, hs, hd]
-    · rw [if_neg hs]
-      simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
-      exact ih
+  first
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       rw [List.filter_cons]
+       by_cases hs : signUndetermined a = true
+       · rw [if_pos hs]
+         by_cases hd : declAccepted (assertPositive a) = true
+         · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
+               declAccepted (assertPositive x) = true
+           · rw [dif_pos ht] at ih
+             rw [dif_pos (fun x hx => by
+               rcases List.mem_cons.mp hx with h' | h'
+               · subst h'; exact hd
+               · exact ht x h')]
+             simp [implementation_posify, hs, hd, ih, List.pmap]
+           · rw [dif_neg ht] at ih
+             rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
+             simp [implementation_posify, hs, hd, ih]
+         · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
+           simp [implementation_posify, hs, hd]
+       · rw [if_neg hs]
+         simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
+         exact ih)
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       simp_all [implementation_posify, problem_spec_posify, signUndetermined,
+                 assertPositive, List.filter_cons, List.pmap])
+  | simp [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+          List.pmap, List.filter_cons]
+  | simp_all [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+              List.pmap, List.filter_cons, Id.run]
+  | (unfold problem_spec_posify implementation_posify; rfl)
+  | (intro; rfl)
+  | decide
+  | aesop
+  | (funext; simp_all [problem_spec_posify, implementation_posify])
+  | (induction syms <;>
+     simp_all [problem_spec_posify, implementation_posify, signUndetermined,
+               assertPositive, List.pmap, List.filter_cons, Id.run])
 -- proof-end
```

Attack 2 — `atk_2_partial.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -124,16 +124,15 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_posify : List Assumptions → Option (List Assumptions)
-  | [] => some []
-  | a :: as =>
-    if signUndetermined a then
-      if h : declAccepted (assertPositive a) = true then
-        (implementation_posify as).map (fun rs => resolveAssumptions (assertPositive a) h :: rs)
-      else
-        none
+def implementation_posify (syms : List Assumptions) : Option (List Assumptions) :=
+  let kept := syms.filter signUndetermined
+  if h : ∀ a ∈ kept, declAccepted (assertPositive a) = true then
+    if kept.length ≤ 1 then
+      some (kept.pmap (fun a ha => resolveAssumptions (assertPositive a) ha) h)
     else
-      implementation_posify as
+      some []
+  else
+    none
 -- impl-end
 
 -- proof-start
@@ -141,28 +140,47 @@
     ∀ (syms : List Assumptions),
       problem_spec_posify syms (implementation_posify syms) := by
   intro syms
-  induction syms with
-  | nil => simp [problem_spec_posify, implementation_posify]
-  | cons a as ih =>
-    unfold problem_spec_posify at ih ⊢
-    rw [List.filter_cons]
-    by_cases hs : signUndetermined a = true
-    · rw [if_pos hs]
-      by_cases hd : declAccepted (assertPositive a) = true
-      · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
-            declAccepted (assertPositive x) = true
-        · rw [dif_pos ht] at ih
-          rw [dif_pos (fun x hx => by
-            rcases List.mem_cons.mp hx with h' | h'
-            · subst h'; exact hd
-            · exact ht x h')]
-          simp [implementation_posify, hs, hd, ih, List.pmap]
-        · rw [dif_neg ht] at ih
-          rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
-          simp [implementation_posify, hs, hd, ih]
-      · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
-        simp [implementation_posify, hs, hd]
-    · rw [if_neg hs]
-      simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
-      exact ih
+  first
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       rw [List.filter_cons]
+       by_cases hs : signUndetermined a = true
+       · rw [if_pos hs]
+         by_cases hd : declAccepted (assertPositive a) = true
+         · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
+               declAccepted (assertPositive x) = true
+           · rw [dif_pos ht] at ih
+             rw [dif_pos (fun x hx => by
+               rcases List.mem_cons.mp hx with h' | h'
+               · subst h'; exact hd
+               · exact ht x h')]
+             simp [implementation_posify, hs, hd, ih, List.pmap]
+           · rw [dif_neg ht] at ih
+             rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
+             simp [implementation_posify, hs, hd, ih]
+         · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
+           simp [implementation_posify, hs, hd]
+       · rw [if_neg hs]
+         simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
+         exact ih)
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       simp_all [implementation_posify, problem_spec_posify, signUndetermined,
+                 assertPositive, List.filter_cons, List.pmap])
+  | simp [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+          List.pmap, List.filter_cons]
+  | simp_all [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+              List.pmap, List.filter_cons, Id.run]
+  | (unfold problem_spec_posify implementation_posify; rfl)
+  | (intro; rfl)
+  | decide
+  | aesop
+  | (funext; simp_all [problem_spec_posify, implementation_posify])
+  | (induction syms <;>
+     simp_all [problem_spec_posify, implementation_posify, signUndetermined,
+               assertPositive, List.pmap, List.filter_cons, Id.run])
 -- proof-end
```

Attack 3 — `atk_3_boundary.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -124,16 +124,12 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_posify : List Assumptions → Option (List Assumptions)
-  | [] => some []
-  | a :: as =>
-    if signUndetermined a then
-      if h : declAccepted (assertPositive a) = true then
-        (implementation_posify as).map (fun rs => resolveAssumptions (assertPositive a) h :: rs)
-      else
-        none
-    else
-      implementation_posify as
+def implementation_posify (syms : List Assumptions) : Option (List Assumptions) :=
+  let kept := syms.filter signUndetermined
+  if h : ∀ a ∈ kept, declAccepted (assertPositive a) = true then
+    some ((kept.pmap (fun a ha => resolveAssumptions (assertPositive a) ha) h).dropLast)
+  else
+    none
 -- impl-end
 
 -- proof-start
@@ -141,28 +137,47 @@
     ∀ (syms : List Assumptions),
       problem_spec_posify syms (implementation_posify syms) := by
   intro syms
-  induction syms with
-  | nil => simp [problem_spec_posify, implementation_posify]
-  | cons a as ih =>
-    unfold problem_spec_posify at ih ⊢
-    rw [List.filter_cons]
-    by_cases hs : signUndetermined a = true
-    · rw [if_pos hs]
-      by_cases hd : declAccepted (assertPositive a) = true
-      · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
-            declAccepted (assertPositive x) = true
-        · rw [dif_pos ht] at ih
-          rw [dif_pos (fun x hx => by
-            rcases List.mem_cons.mp hx with h' | h'
-            · subst h'; exact hd
-            · exact ht x h')]
-          simp [implementation_posify, hs, hd, ih, List.pmap]
-        · rw [dif_neg ht] at ih
-          rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
-          simp [implementation_posify, hs, hd, ih]
-      · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
-        simp [implementation_posify, hs, hd]
-    · rw [if_neg hs]
-      simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
-      exact ih
+  first
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       rw [List.filter_cons]
+       by_cases hs : signUndetermined a = true
+       · rw [if_pos hs]
+         by_cases hd : declAccepted (assertPositive a) = true
+         · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
+               declAccepted (assertPositive x) = true
+           · rw [dif_pos ht] at ih
+             rw [dif_pos (fun x hx => by
+               rcases List.mem_cons.mp hx with h' | h'
+               · subst h'; exact hd
+               · exact ht x h')]
+             simp [implementation_posify, hs, hd, ih, List.pmap]
+           · rw [dif_neg ht] at ih
+             rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
+             simp [implementation_posify, hs, hd, ih]
+         · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
+           simp [implementation_posify, hs, hd]
+       · rw [if_neg hs]
+         simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
+         exact ih)
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       simp_all [implementation_posify, problem_spec_posify, signUndetermined,
+                 assertPositive, List.filter_cons, List.pmap])
+  | simp [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+          List.pmap, List.filter_cons]
+  | simp_all [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+              List.pmap, List.filter_cons, Id.run]
+  | (unfold problem_spec_posify implementation_posify; rfl)
+  | (intro; rfl)
+  | decide
+  | aesop
+  | (funext; simp_all [problem_spec_posify, implementation_posify])
+  | (induction syms <;>
+     simp_all [problem_spec_posify, implementation_posify, signUndetermined,
+               assertPositive, List.pmap, List.filter_cons, Id.run])
 -- proof-end
```

Attack 4 — `atk_4_cfeffect.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -124,16 +124,12 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_posify : List Assumptions → Option (List Assumptions)
-  | [] => some []
-  | a :: as =>
-    if signUndetermined a then
-      if h : declAccepted (assertPositive a) = true then
-        (implementation_posify as).map (fun rs => resolveAssumptions (assertPositive a) h :: rs)
-      else
-        none
-    else
-      implementation_posify as
+def implementation_posify (syms : List Assumptions) : Option (List Assumptions) :=
+  let kept := syms.filter signUndetermined
+  if h : ∀ a ∈ kept, declAccepted (assertPositive a) = true then
+    some ((kept.pmap (fun a ha => resolveAssumptions (assertPositive a) ha) h).reverse)
+  else
+    none
 -- impl-end
 
 -- proof-start
@@ -141,28 +137,47 @@
     ∀ (syms : List Assumptions),
       problem_spec_posify syms (implementation_posify syms) := by
   intro syms
-  induction syms with
-  | nil => simp [problem_spec_posify, implementation_posify]
-  | cons a as ih =>
-    unfold problem_spec_posify at ih ⊢
-    rw [List.filter_cons]
-    by_cases hs : signUndetermined a = true
-    · rw [if_pos hs]
-      by_cases hd : declAccepted (assertPositive a) = true
-      · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
-            declAccepted (assertPositive x) = true
-        · rw [dif_pos ht] at ih
-          rw [dif_pos (fun x hx => by
-            rcases List.mem_cons.mp hx with h' | h'
-            · subst h'; exact hd
-            · exact ht x h')]
-          simp [implementation_posify, hs, hd, ih, List.pmap]
-        · rw [dif_neg ht] at ih
-          rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
-          simp [implementation_posify, hs, hd, ih]
-      · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
-        simp [implementation_posify, hs, hd]
-    · rw [if_neg hs]
-      simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
-      exact ih
+  first
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       rw [List.filter_cons]
+       by_cases hs : signUndetermined a = true
+       · rw [if_pos hs]
+         by_cases hd : declAccepted (assertPositive a) = true
+         · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
+               declAccepted (assertPositive x) = true
+           · rw [dif_pos ht] at ih
+             rw [dif_pos (fun x hx => by
+               rcases List.mem_cons.mp hx with h' | h'
+               · subst h'; exact hd
+               · exact ht x h')]
+             simp [implementation_posify, hs, hd, ih, List.pmap]
+           · rw [dif_neg ht] at ih
+             rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
+             simp [implementation_posify, hs, hd, ih]
+         · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
+           simp [implementation_posify, hs, hd]
+       · rw [if_neg hs]
+         simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
+         exact ih)
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       simp_all [implementation_posify, problem_spec_posify, signUndetermined,
+                 assertPositive, List.filter_cons, List.pmap])
+  | simp [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+          List.pmap, List.filter_cons]
+  | simp_all [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+              List.pmap, List.filter_cons, Id.run]
+  | (unfold problem_spec_posify implementation_posify; rfl)
+  | (intro; rfl)
+  | decide
+  | aesop
+  | (funext; simp_all [problem_spec_posify, implementation_posify])
+  | (induction syms <;>
+     simp_all [problem_spec_posify, implementation_posify, signUndetermined,
+               assertPositive, List.pmap, List.filter_cons, Id.run])
 -- proof-end
```

Attack 5 — `atk_5_echo.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -128,8 +128,10 @@
   | [] => some []
   | a :: as =>
     if signUndetermined a then
-      if h : declAccepted (assertPositive a) = true then
-        (implementation_posify as).map (fun rs => resolveAssumptions (assertPositive a) h :: rs)
+      if _h : declAccepted (assertPositive a) = true then
+        -- ECHO: the declaration handed to the engine is returned in place of the
+        -- record the engine infers from it; the engine's answer is never used.
+        (implementation_posify as).map (fun rs => assertPositive a :: rs)
       else
         none
     else
@@ -141,28 +143,47 @@
     ∀ (syms : List Assumptions),
       problem_spec_posify syms (implementation_posify syms) := by
   intro syms
-  induction syms with
-  | nil => simp [problem_spec_posify, implementation_posify]
-  | cons a as ih =>
-    unfold problem_spec_posify at ih ⊢
-    rw [List.filter_cons]
-    by_cases hs : signUndetermined a = true
-    · rw [if_pos hs]
-      by_cases hd : declAccepted (assertPositive a) = true
-      · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
-            declAccepted (assertPositive x) = true
-        · rw [dif_pos ht] at ih
-          rw [dif_pos (fun x hx => by
-            rcases List.mem_cons.mp hx with h' | h'
-            · subst h'; exact hd
-            · exact ht x h')]
-          simp [implementation_posify, hs, hd, ih, List.pmap]
-        · rw [dif_neg ht] at ih
-          rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
-          simp [implementation_posify, hs, hd, ih]
-      · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
-        simp [implementation_posify, hs, hd]
-    · rw [if_neg hs]
-      simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
-      exact ih
+  first
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       rw [List.filter_cons]
+       by_cases hs : signUndetermined a = true
+       · rw [if_pos hs]
+         by_cases hd : declAccepted (assertPositive a) = true
+         · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
+               declAccepted (assertPositive x) = true
+           · rw [dif_pos ht] at ih
+             rw [dif_pos (fun x hx => by
+               rcases List.mem_cons.mp hx with h' | h'
+               · subst h'; exact hd
+               · exact ht x h')]
+             simp [implementation_posify, hs, hd, ih, List.pmap]
+           · rw [dif_neg ht] at ih
+             rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
+             simp [implementation_posify, hs, hd, ih]
+         · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
+           simp [implementation_posify, hs, hd]
+       · rw [if_neg hs]
+         simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
+         exact ih)
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       simp_all [implementation_posify, problem_spec_posify, signUndetermined,
+                 assertPositive, List.filter_cons, List.pmap])
+  | simp [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+          List.pmap, List.filter_cons]
+  | simp_all [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+              List.pmap, List.filter_cons, Id.run]
+  | (unfold problem_spec_posify implementation_posify; rfl)
+  | (intro; rfl)
+  | decide
+  | aesop
+  | (funext; simp_all [problem_spec_posify, implementation_posify])
+  | (induction syms <;>
+     simp_all [problem_spec_posify, implementation_posify, signUndetermined,
+               assertPositive, List.pmap, List.filter_cons, Id.run])
 -- proof-end
```

Attack 6 — `atk_6_leak.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -124,16 +124,13 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_posify : List Assumptions → Option (List Assumptions)
-  | [] => some []
-  | a :: as =>
-    if signUndetermined a then
-      if h : declAccepted (assertPositive a) = true then
-        (implementation_posify as).map (fun rs => resolveAssumptions (assertPositive a) h :: rs)
-      else
-        none
-    else
-      implementation_posify as
+def implementation_posify (syms : List Assumptions) : Option (List Assumptions) :=
+  if h : ∀ a ∈ syms, declAccepted (assertPositive a) = true then
+    some ((syms.filter signUndetermined).pmap
+      (fun a ha => resolveAssumptions (assertPositive a) ha)
+      (fun a ha => h a (List.mem_of_mem_filter ha)))
+  else
+    none
 -- impl-end
 
 -- proof-start
@@ -141,28 +138,47 @@
     ∀ (syms : List Assumptions),
       problem_spec_posify syms (implementation_posify syms) := by
   intro syms
-  induction syms with
-  | nil => simp [problem_spec_posify, implementation_posify]
-  | cons a as ih =>
-    unfold problem_spec_posify at ih ⊢
-    rw [List.filter_cons]
-    by_cases hs : signUndetermined a = true
-    · rw [if_pos hs]
-      by_cases hd : declAccepted (assertPositive a) = true
-      · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
-            declAccepted (assertPositive x) = true
-        · rw [dif_pos ht] at ih
-          rw [dif_pos (fun x hx => by
-            rcases List.mem_cons.mp hx with h' | h'
-            · subst h'; exact hd
-            · exact ht x h')]
-          simp [implementation_posify, hs, hd, ih, List.pmap]
-        · rw [dif_neg ht] at ih
-          rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
-          simp [implementation_posify, hs, hd, ih]
-      · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
-        simp [implementation_posify, hs, hd]
-    · rw [if_neg hs]
-      simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
-      exact ih
+  first
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       rw [List.filter_cons]
+       by_cases hs : signUndetermined a = true
+       · rw [if_pos hs]
+         by_cases hd : declAccepted (assertPositive a) = true
+         · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
+               declAccepted (assertPositive x) = true
+           · rw [dif_pos ht] at ih
+             rw [dif_pos (fun x hx => by
+               rcases List.mem_cons.mp hx with h' | h'
+               · subst h'; exact hd
+               · exact ht x h')]
+             simp [implementation_posify, hs, hd, ih, List.pmap]
+           · rw [dif_neg ht] at ih
+             rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
+             simp [implementation_posify, hs, hd, ih]
+         · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
+           simp [implementation_posify, hs, hd]
+       · rw [if_neg hs]
+         simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
+         exact ih)
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       simp_all [implementation_posify, problem_spec_posify, signUndetermined,
+                 assertPositive, List.filter_cons, List.pmap])
+  | simp [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+          List.pmap, List.filter_cons]
+  | simp_all [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+              List.pmap, List.filter_cons, Id.run]
+  | (unfold problem_spec_posify implementation_posify; rfl)
+  | (intro; rfl)
+  | decide
+  | aesop
+  | (funext; simp_all [problem_spec_posify, implementation_posify])
+  | (induction syms <;>
+     simp_all [problem_spec_posify, implementation_posify, signUndetermined,
+               assertPositive, List.pmap, List.filter_cons, Id.run])
 -- proof-end
```

Attack 7 — `atk_7_identity.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -124,45 +124,57 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_posify : List Assumptions → Option (List Assumptions)
-  | [] => some []
-  | a :: as =>
-    if signUndetermined a then
-      if h : declAccepted (assertPositive a) = true then
-        (implementation_posify as).map (fun rs => resolveAssumptions (assertPositive a) h :: rs)
-      else
-        none
-    else
-      implementation_posify as
+def implementation_posify (syms : List Assumptions) : Option (List Assumptions) :=
+  if h : ∀ a ∈ syms.filter signUndetermined, declAccepted (assertPositive a) = true then
+    -- Resolve each DISTINCT kept declaration ONCE into a memo table, then read
+    -- every kept symbol's record back out of that table, so symbols declaring
+    -- the same property set SHARE one resolved result.
+    some ((syms.filter signUndetermined).pmap (fun a ha =>
+      ((((syms.filter signUndetermined).dedup).pmap
+          (fun b hb => (b, resolveAssumptions (assertPositive b) hb))
+          (fun b hb => h b (List.mem_dedup.mp hb))).lookup a).getD
+        (resolveAssumptions (assertPositive a) ha)) h)
+  else
+    none
 -- impl-end
 
 -- proof-start
+/-- The memo table built by resolving each DISTINCT kept declaration once answers
+every kept declaration with exactly the record that declaration's own call would
+have produced: an entry found by `lookup a` is keyed by `a`, and
+`resolveAssumptions` is a function of the declaration, so the shared entry
+carries that same record (the acceptance proofs are interchangeable by proof
+irrelevance). Where the lookup misses, the `getD` default is that record. -/
+theorem memo_hit (kept : List Assumptions)
+    (h : ∀ a ∈ kept, declAccepted (assertPositive a) = true)
+    (a : Assumptions) (h₁ : declAccepted (assertPositive a) = true) :
+    ((kept.dedup.pmap (fun b hb => (b, resolveAssumptions (assertPositive b) hb))
+        (fun b hb => h b (List.mem_dedup.mp hb))).lookup a).getD
+          (resolveAssumptions (assertPositive a) h₁)
+      = resolveAssumptions (assertPositive a) h₁ := by
+  rcases hlk : (kept.dedup.pmap (fun b hb => (b, resolveAssumptions (assertPositive b) hb))
+      (fun b hb => h b (List.mem_dedup.mp hb))).lookup a with _ | r
+  · simp [hlk]
+  · obtain ⟨l₁, l₂, hl, -⟩ := List.lookup_eq_some_iff.mp hlk
+    have hmem : (a, r) ∈ kept.dedup.pmap
+        (fun b hb => (b, resolveAssumptions (assertPositive b) hb))
+        (fun b hb => h b (List.mem_dedup.mp hb)) := by
+      rw [hl]; simp
+    rw [List.mem_pmap] at hmem
+    obtain ⟨b, hb, hbe⟩ := hmem
+    simp only [Prod.mk.injEq] at hbe
+    obtain ⟨hba, hbr⟩ := hbe
+    subst hba
+    simp [hlk, ← hbr]
+
 theorem correct_posify :
     ∀ (syms : List Assumptions),
       problem_spec_posify syms (implementation_posify syms) := by
   intro syms
-  induction syms with
-  | nil => simp [problem_spec_posify, implementation_posify]
-  | cons a as ih =>
-    unfold problem_spec_posify at ih ⊢
-    rw [List.filter_cons]
-    by_cases hs : signUndetermined a = true
-    · rw [if_pos hs]
-      by_cases hd : declAccepted (assertPositive a) = true
-      · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
-            declAccepted (assertPositive x) = true
-        · rw [dif_pos ht] at ih
-          rw [dif_pos (fun x hx => by
-            rcases List.mem_cons.mp hx with h' | h'
-            · subst h'; exact hd
-            · exact ht x h')]
-          simp [implementation_posify, hs, hd, ih, List.pmap]
-        · rw [dif_neg ht] at ih
-          rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
-          simp [implementation_posify, hs, hd, ih]
-      · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
-        simp [implementation_posify, hs, hd]
-    · rw [if_neg hs]
-      simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
-      exact ih
+  unfold problem_spec_posify implementation_posify
+  by_cases h : ∀ a ∈ syms.filter signUndetermined, declAccepted (assertPositive a) = true
+  · rw [dif_pos h, dif_pos h]
+    congr 1
+    exact List.pmap_congr_left _ (fun a _ h₁ h₂ => memo_hit _ h a h₂ ▸ memo_hit _ h a h₁)
+  · rw [dif_neg h, dif_neg h]
 -- proof-end
```

Attack 8 — `atk_8_declorder.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -128,8 +128,11 @@
   | [] => some []
   | a :: as =>
     if signUndetermined a then
-      if h : declAccepted (assertPositive a) = true then
-        (implementation_posify as).map (fun rs => resolveAssumptions (assertPositive a) h :: rs)
+      -- the positivity assertion is APPENDED to the symbol's own properties
+      -- instead of stated in front of them
+      if h : declAccepted (a ++ [("positive", true)]) = true then
+        (implementation_posify as).map
+          (fun rs => resolveAssumptions (a ++ [("positive", true)]) h :: rs)
       else
         none
     else
@@ -141,28 +144,47 @@
     ∀ (syms : List Assumptions),
       problem_spec_posify syms (implementation_posify syms) := by
   intro syms
-  induction syms with
-  | nil => simp [problem_spec_posify, implementation_posify]
-  | cons a as ih =>
-    unfold problem_spec_posify at ih ⊢
-    rw [List.filter_cons]
-    by_cases hs : signUndetermined a = true
-    · rw [if_pos hs]
-      by_cases hd : declAccepted (assertPositive a) = true
-      · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
-            declAccepted (assertPositive x) = true
-        · rw [dif_pos ht] at ih
-          rw [dif_pos (fun x hx => by
-            rcases List.mem_cons.mp hx with h' | h'
-            · subst h'; exact hd
-            · exact ht x h')]
-          simp [implementation_posify, hs, hd, ih, List.pmap]
-        · rw [dif_neg ht] at ih
-          rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
-          simp [implementation_posify, hs, hd, ih]
-      · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
-        simp [implementation_posify, hs, hd]
-    · rw [if_neg hs]
-      simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
-      exact ih
+  first
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       rw [List.filter_cons]
+       by_cases hs : signUndetermined a = true
+       · rw [if_pos hs]
+         by_cases hd : declAccepted (assertPositive a) = true
+         · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
+               declAccepted (assertPositive x) = true
+           · rw [dif_pos ht] at ih
+             rw [dif_pos (fun x hx => by
+               rcases List.mem_cons.mp hx with h' | h'
+               · subst h'; exact hd
+               · exact ht x h')]
+             simp [implementation_posify, hs, hd, ih, List.pmap]
+           · rw [dif_neg ht] at ih
+             rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
+             simp [implementation_posify, hs, hd, ih]
+         · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
+           simp [implementation_posify, hs, hd]
+       · rw [if_neg hs]
+         simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
+         exact ih)
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       simp_all [implementation_posify, problem_spec_posify, signUndetermined,
+                 assertPositive, List.filter_cons, List.pmap])
+  | simp [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+          List.pmap, List.filter_cons]
+  | simp_all [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+              List.pmap, List.filter_cons, Id.run]
+  | (unfold problem_spec_posify implementation_posify; rfl)
+  | (intro; rfl)
+  | decide
+  | aesop
+  | (funext; simp_all [problem_spec_posify, implementation_posify])
+  | (induction syms <;>
+     simp_all [problem_spec_posify, implementation_posify, signUndetermined,
+               assertPositive, List.pmap, List.filter_cons, Id.run])
 -- proof-end
```

Attack 9 — `atk_9_dropref.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -131,7 +131,9 @@
       if h : declAccepted (assertPositive a) = true then
         (implementation_posify as).map (fun rs => resolveAssumptions (assertPositive a) h :: rs)
       else
-        none
+        -- a refused kept declaration is SKIPPED rather than making the whole
+        -- call valueless
+        implementation_posify as
     else
       implementation_posify as
 -- impl-end
@@ -141,28 +143,47 @@
     ∀ (syms : List Assumptions),
       problem_spec_posify syms (implementation_posify syms) := by
   intro syms
-  induction syms with
-  | nil => simp [problem_spec_posify, implementation_posify]
-  | cons a as ih =>
-    unfold problem_spec_posify at ih ⊢
-    rw [List.filter_cons]
-    by_cases hs : signUndetermined a = true
-    · rw [if_pos hs]
-      by_cases hd : declAccepted (assertPositive a) = true
-      · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
-            declAccepted (assertPositive x) = true
-        · rw [dif_pos ht] at ih
-          rw [dif_pos (fun x hx => by
-            rcases List.mem_cons.mp hx with h' | h'
-            · subst h'; exact hd
-            · exact ht x h')]
-          simp [implementation_posify, hs, hd, ih, List.pmap]
-        · rw [dif_neg ht] at ih
-          rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
-          simp [implementation_posify, hs, hd, ih]
-      · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
-        simp [implementation_posify, hs, hd]
-    · rw [if_neg hs]
-      simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
-      exact ih
+  first
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       rw [List.filter_cons]
+       by_cases hs : signUndetermined a = true
+       · rw [if_pos hs]
+         by_cases hd : declAccepted (assertPositive a) = true
+         · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
+               declAccepted (assertPositive x) = true
+           · rw [dif_pos ht] at ih
+             rw [dif_pos (fun x hx => by
+               rcases List.mem_cons.mp hx with h' | h'
+               · subst h'; exact hd
+               · exact ht x h')]
+             simp [implementation_posify, hs, hd, ih, List.pmap]
+           · rw [dif_neg ht] at ih
+             rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
+             simp [implementation_posify, hs, hd, ih]
+         · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
+           simp [implementation_posify, hs, hd]
+       · rw [if_neg hs]
+         simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
+         exact ih)
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       simp_all [implementation_posify, problem_spec_posify, signUndetermined,
+                 assertPositive, List.filter_cons, List.pmap])
+  | simp [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+          List.pmap, List.filter_cons]
+  | simp_all [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+              List.pmap, List.filter_cons, Id.run]
+  | (unfold problem_spec_posify implementation_posify; rfl)
+  | (intro; rfl)
+  | decide
+  | aesop
+  | (funext; simp_all [problem_spec_posify, implementation_posify])
+  | (induction syms <;>
+     simp_all [problem_spec_posify, implementation_posify, signUndetermined,
+               assertPositive, List.pmap, List.filter_cons, Id.run])
 -- proof-end
```

Attack 10 — `atk_10_widen.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,7 +127,9 @@
 def implementation_posify : List Assumptions → Option (List Assumptions)
   | [] => some []
   | a :: as =>
-    if signUndetermined a then
+    -- the guard is widened by a disjunct that is provably never satisfiable
+    if signUndetermined a || (a.lookup "positive" == some true &&
+                              a.lookup "positive" == some false) then
       if h : declAccepted (assertPositive a) = true then
         (implementation_posify as).map (fun rs => resolveAssumptions (assertPositive a) h :: rs)
       else
@@ -141,28 +143,47 @@
     ∀ (syms : List Assumptions),
       problem_spec_posify syms (implementation_posify syms) := by
   intro syms
-  induction syms with
-  | nil => simp [problem_spec_posify, implementation_posify]
-  | cons a as ih =>
-    unfold problem_spec_posify at ih ⊢
-    rw [List.filter_cons]
-    by_cases hs : signUndetermined a = true
-    · rw [if_pos hs]
-      by_cases hd : declAccepted (assertPositive a) = true
-      · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
-            declAccepted (assertPositive x) = true
-        · rw [dif_pos ht] at ih
-          rw [dif_pos (fun x hx => by
-            rcases List.mem_cons.mp hx with h' | h'
-            · subst h'; exact hd
-            · exact ht x h')]
-          simp [implementation_posify, hs, hd, ih, List.pmap]
-        · rw [dif_neg ht] at ih
-          rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
-          simp [implementation_posify, hs, hd, ih]
-      · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
-        simp [implementation_posify, hs, hd]
-    · rw [if_neg hs]
-      simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
-      exact ih
+  first
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       rw [List.filter_cons]
+       by_cases hs : signUndetermined a = true
+       · rw [if_pos hs]
+         by_cases hd : declAccepted (assertPositive a) = true
+         · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
+               declAccepted (assertPositive x) = true
+           · rw [dif_pos ht] at ih
+             rw [dif_pos (fun x hx => by
+               rcases List.mem_cons.mp hx with h' | h'
+               · subst h'; exact hd
+               · exact ht x h')]
+             simp [implementation_posify, hs, hd, ih, List.pmap]
+           · rw [dif_neg ht] at ih
+             rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
+             simp [implementation_posify, hs, hd, ih]
+         · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
+           simp [implementation_posify, hs, hd]
+       · rw [if_neg hs]
+         simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
+         exact ih)
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       simp_all [implementation_posify, problem_spec_posify, signUndetermined,
+                 assertPositive, List.filter_cons, List.pmap])
+  | simp [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+          List.pmap, List.filter_cons]
+  | simp_all [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+              List.pmap, List.filter_cons, Id.run]
+  | (unfold problem_spec_posify implementation_posify; rfl)
+  | (intro; rfl)
+  | decide
+  | aesop
+  | (funext; simp_all [problem_spec_posify, implementation_posify])
+  | (induction syms <;>
+     simp_all [problem_spec_posify, implementation_posify, signUndetermined,
+               assertPositive, List.pmap, List.filter_cons, Id.run])
 -- proof-end
```

Attack 11 — `atk_11_stripkey.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -128,8 +128,9 @@
   | [] => some []
   | a :: as =>
     if signUndetermined a then
-      if h : declAccepted (assertPositive a) = true then
-        (implementation_posify as).map (fun rs => resolveAssumptions (assertPositive a) h :: rs)
+      let decl := ("positive", true) :: a.filter (fun p => p.1 != "positive")
+      if h : declAccepted decl = true then
+        (implementation_posify as).map (fun rs => resolveAssumptions decl h :: rs)
       else
         none
     else
@@ -141,28 +142,47 @@
     ∀ (syms : List Assumptions),
       problem_spec_posify syms (implementation_posify syms) := by
   intro syms
-  induction syms with
-  | nil => simp [problem_spec_posify, implementation_posify]
-  | cons a as ih =>
-    unfold problem_spec_posify at ih ⊢
-    rw [List.filter_cons]
-    by_cases hs : signUndetermined a = true
-    · rw [if_pos hs]
-      by_cases hd : declAccepted (assertPositive a) = true
-      · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
-            declAccepted (assertPositive x) = true
-        · rw [dif_pos ht] at ih
-          rw [dif_pos (fun x hx => by
-            rcases List.mem_cons.mp hx with h' | h'
-            · subst h'; exact hd
-            · exact ht x h')]
-          simp [implementation_posify, hs, hd, ih, List.pmap]
-        · rw [dif_neg ht] at ih
-          rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
-          simp [implementation_posify, hs, hd, ih]
-      · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
-        simp [implementation_posify, hs, hd]
-    · rw [if_neg hs]
-      simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
-      exact ih
+  first
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       rw [List.filter_cons]
+       by_cases hs : signUndetermined a = true
+       · rw [if_pos hs]
+         by_cases hd : declAccepted (assertPositive a) = true
+         · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
+               declAccepted (assertPositive x) = true
+           · rw [dif_pos ht] at ih
+             rw [dif_pos (fun x hx => by
+               rcases List.mem_cons.mp hx with h' | h'
+               · subst h'; exact hd
+               · exact ht x h')]
+             simp [implementation_posify, hs, hd, ih, List.pmap]
+           · rw [dif_neg ht] at ih
+             rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
+             simp [implementation_posify, hs, hd, ih]
+         · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
+           simp [implementation_posify, hs, hd]
+       · rw [if_neg hs]
+         simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
+         exact ih)
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       simp_all [implementation_posify, problem_spec_posify, signUndetermined,
+                 assertPositive, List.filter_cons, List.pmap])
+  | simp [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+          List.pmap, List.filter_cons]
+  | simp_all [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+              List.pmap, List.filter_cons, Id.run]
+  | (unfold problem_spec_posify implementation_posify; rfl)
+  | (intro; rfl)
+  | decide
+  | aesop
+  | (funext; simp_all [problem_spec_posify, implementation_posify])
+  | (induction syms <;>
+     simp_all [problem_spec_posify, implementation_posify, signUndetermined,
+               assertPositive, List.pmap, List.filter_cons, Id.run])
 -- proof-end
```

Attack 12 — `atk_12_dedupdef.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -124,16 +124,13 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_posify : List Assumptions → Option (List Assumptions)
-  | [] => some []
-  | a :: as =>
-    if signUndetermined a then
-      if h : declAccepted (assertPositive a) = true then
-        (implementation_posify as).map (fun rs => resolveAssumptions (assertPositive a) h :: rs)
-      else
-        none
-    else
-      implementation_posify as
+def implementation_posify (syms : List Assumptions) : Option (List Assumptions) :=
+  let kept := syms.filter signUndetermined
+  if h : ∀ a ∈ kept.dedup, declAccepted (assertPositive a) = true then
+    some (kept.pmap (fun a ha => resolveAssumptions (assertPositive a) ha)
+      (fun a ha => h a (List.mem_dedup.mpr ha)))
+  else
+    none
 -- impl-end
 
 -- proof-start
@@ -141,28 +138,47 @@
     ∀ (syms : List Assumptions),
       problem_spec_posify syms (implementation_posify syms) := by
   intro syms
-  induction syms with
-  | nil => simp [problem_spec_posify, implementation_posify]
-  | cons a as ih =>
-    unfold problem_spec_posify at ih ⊢
-    rw [List.filter_cons]
-    by_cases hs : signUndetermined a = true
-    · rw [if_pos hs]
-      by_cases hd : declAccepted (assertPositive a) = true
-      · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
-            declAccepted (assertPositive x) = true
-        · rw [dif_pos ht] at ih
-          rw [dif_pos (fun x hx => by
-            rcases List.mem_cons.mp hx with h' | h'
-            · subst h'; exact hd
-            · exact ht x h')]
-          simp [implementation_posify, hs, hd, ih, List.pmap]
-        · rw [dif_neg ht] at ih
-          rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
-          simp [implementation_posify, hs, hd, ih]
-      · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
-        simp [implementation_posify, hs, hd]
-    · rw [if_neg hs]
-      simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
-      exact ih
+  first
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       rw [List.filter_cons]
+       by_cases hs : signUndetermined a = true
+       · rw [if_pos hs]
+         by_cases hd : declAccepted (assertPositive a) = true
+         · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
+               declAccepted (assertPositive x) = true
+           · rw [dif_pos ht] at ih
+             rw [dif_pos (fun x hx => by
+               rcases List.mem_cons.mp hx with h' | h'
+               · subst h'; exact hd
+               · exact ht x h')]
+             simp [implementation_posify, hs, hd, ih, List.pmap]
+           · rw [dif_neg ht] at ih
+             rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
+             simp [implementation_posify, hs, hd, ih]
+         · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
+           simp [implementation_posify, hs, hd]
+       · rw [if_neg hs]
+         simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
+         exact ih)
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       simp_all [implementation_posify, problem_spec_posify, signUndetermined,
+                 assertPositive, List.filter_cons, List.pmap])
+  | simp [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+          List.pmap, List.filter_cons]
+  | simp_all [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+              List.pmap, List.filter_cons, Id.run]
+  | (unfold problem_spec_posify implementation_posify; rfl)
+  | (intro; rfl)
+  | decide
+  | aesop
+  | (funext; simp_all [problem_spec_posify, implementation_posify])
+  | (induction syms <;>
+     simp_all [problem_spec_posify, implementation_posify, signUndetermined,
+               assertPositive, List.pmap, List.filter_cons, Id.run])
 -- proof-end
```

Attack 13 — `atk_13_probeall.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,11 +127,12 @@
 def implementation_posify : List Assumptions → Option (List Assumptions)
   | [] => some []
   | a :: as =>
+    let probe := if h : declAccepted (assertPositive a) = true then
+        some (resolveAssumptions (assertPositive a) h) else none
     if signUndetermined a then
-      if h : declAccepted (assertPositive a) = true then
-        (implementation_posify as).map (fun rs => resolveAssumptions (assertPositive a) h :: rs)
-      else
-        none
+      match probe with
+      | some r => (implementation_posify as).map (fun rs => r :: rs)
+      | none => none
     else
       implementation_posify as
 -- impl-end
```

Attack 14 — `atk_14_leak2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -124,16 +124,17 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_posify : List Assumptions → Option (List Assumptions)
-  | [] => some []
-  | a :: as =>
-    if signUndetermined a then
-      if h : declAccepted (assertPositive a) = true then
-        (implementation_posify as).map (fun rs => resolveAssumptions (assertPositive a) h :: rs)
-      else
-        none
+def implementation_posify (syms : List Assumptions) : Option (List Assumptions) :=
+  -- the acceptance question is asked at every symbol, and the ANSWER is
+  -- propagated: a refusal anywhere (replaced or not) makes the call valueless.
+  match syms.find? (fun a => !(declAccepted (assertPositive a))) with
+  | some _ => none
+  | none =>
+    if h : ∀ a ∈ syms.filter signUndetermined, declAccepted (assertPositive a) = true then
+      some ((syms.filter signUndetermined).pmap
+        (fun a ha => resolveAssumptions (assertPositive a) ha) h)
     else
-      implementation_posify as
+      none
 -- impl-end
 
 -- proof-start
@@ -141,28 +142,47 @@
     ∀ (syms : List Assumptions),
       problem_spec_posify syms (implementation_posify syms) := by
   intro syms
-  induction syms with
-  | nil => simp [problem_spec_posify, implementation_posify]
-  | cons a as ih =>
-    unfold problem_spec_posify at ih ⊢
-    rw [List.filter_cons]
-    by_cases hs : signUndetermined a = true
-    · rw [if_pos hs]
-      by_cases hd : declAccepted (assertPositive a) = true
-      · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
-            declAccepted (assertPositive x) = true
-        · rw [dif_pos ht] at ih
-          rw [dif_pos (fun x hx => by
-            rcases List.mem_cons.mp hx with h' | h'
-            · subst h'; exact hd
-            · exact ht x h')]
-          simp [implementation_posify, hs, hd, ih, List.pmap]
-        · rw [dif_neg ht] at ih
-          rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
-          simp [implementation_posify, hs, hd, ih]
-      · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
-        simp [implementation_posify, hs, hd]
-    · rw [if_neg hs]
-      simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
-      exact ih
+  first
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       rw [List.filter_cons]
+       by_cases hs : signUndetermined a = true
+       · rw [if_pos hs]
+         by_cases hd : declAccepted (assertPositive a) = true
+         · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
+               declAccepted (assertPositive x) = true
+           · rw [dif_pos ht] at ih
+             rw [dif_pos (fun x hx => by
+               rcases List.mem_cons.mp hx with h' | h'
+               · subst h'; exact hd
+               · exact ht x h')]
+             simp [implementation_posify, hs, hd, ih, List.pmap]
+           · rw [dif_neg ht] at ih
+             rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
+             simp [implementation_posify, hs, hd, ih]
+         · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
+           simp [implementation_posify, hs, hd]
+       · rw [if_neg hs]
+         simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
+         exact ih)
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       simp_all [implementation_posify, problem_spec_posify, signUndetermined,
+                 assertPositive, List.filter_cons, List.pmap])
+  | simp [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+          List.pmap, List.filter_cons]
+  | simp_all [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+              List.pmap, List.filter_cons, Id.run]
+  | (unfold problem_spec_posify implementation_posify; rfl)
+  | (intro; rfl)
+  | decide
+  | aesop
+  | (funext; simp_all [problem_spec_posify, implementation_posify])
+  | (induction syms <;>
+     simp_all [problem_spec_posify, implementation_posify, signUndetermined,
+               assertPositive, List.pmap, List.filter_cons, Id.run])
 -- proof-end
```

Attack 15 — `atk_15_firstrec.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -124,16 +124,16 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_posify : List Assumptions → Option (List Assumptions)
-  | [] => some []
-  | a :: as =>
-    if signUndetermined a then
-      if h : declAccepted (assertPositive a) = true then
-        (implementation_posify as).map (fun rs => resolveAssumptions (assertPositive a) h :: rs)
-      else
-        none
-    else
-      implementation_posify as
+def implementation_posify (syms : List Assumptions) : Option (List Assumptions) :=
+  let kept := syms.filter signUndetermined
+  if h : ∀ a ∈ kept, declAccepted (assertPositive a) = true then
+    match kept with
+    | [] => some []
+    | b :: _ =>
+      some (kept.map (fun _ => resolveAssumptions (assertPositive b)
+        (h b List.mem_cons_self)))
+  else
+    none
 -- impl-end
 
 -- proof-start
@@ -141,28 +141,47 @@
     ∀ (syms : List Assumptions),
       problem_spec_posify syms (implementation_posify syms) := by
   intro syms
-  induction syms with
-  | nil => simp [problem_spec_posify, implementation_posify]
-  | cons a as ih =>
-    unfold problem_spec_posify at ih ⊢
-    rw [List.filter_cons]
-    by_cases hs : signUndetermined a = true
-    · rw [if_pos hs]
-      by_cases hd : declAccepted (assertPositive a) = true
-      · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
-            declAccepted (assertPositive x) = true
-        · rw [dif_pos ht] at ih
-          rw [dif_pos (fun x hx => by
-            rcases List.mem_cons.mp hx with h' | h'
-            · subst h'; exact hd
-            · exact ht x h')]
-          simp [implementation_posify, hs, hd, ih, List.pmap]
-        · rw [dif_neg ht] at ih
-          rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
-          simp [implementation_posify, hs, hd, ih]
-      · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
-        simp [implementation_posify, hs, hd]
-    · rw [if_neg hs]
-      simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
-      exact ih
+  first
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       rw [List.filter_cons]
+       by_cases hs : signUndetermined a = true
+       · rw [if_pos hs]
+         by_cases hd : declAccepted (assertPositive a) = true
+         · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
+               declAccepted (assertPositive x) = true
+           · rw [dif_pos ht] at ih
+             rw [dif_pos (fun x hx => by
+               rcases List.mem_cons.mp hx with h' | h'
+               · subst h'; exact hd
+               · exact ht x h')]
+             simp [implementation_posify, hs, hd, ih, List.pmap]
+           · rw [dif_neg ht] at ih
+             rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
+             simp [implementation_posify, hs, hd, ih]
+         · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
+           simp [implementation_posify, hs, hd]
+       · rw [if_neg hs]
+         simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
+         exact ih)
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       simp_all [implementation_posify, problem_spec_posify, signUndetermined,
+                 assertPositive, List.filter_cons, List.pmap])
+  | simp [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+          List.pmap, List.filter_cons]
+  | simp_all [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+              List.pmap, List.filter_cons, Id.run]
+  | (unfold problem_spec_posify implementation_posify; rfl)
+  | (intro; rfl)
+  | decide
+  | aesop
+  | (funext; simp_all [problem_spec_posify, implementation_posify])
+  | (induction syms <;>
+     simp_all [problem_spec_posify, implementation_posify, signUndetermined,
+               assertPositive, List.pmap, List.filter_cons, Id.run])
 -- proof-end
```

Attack 16 — `atk_16_inject.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -128,8 +128,9 @@
   | [] => some []
   | a :: as =>
     if signUndetermined a then
-      if h : declAccepted (assertPositive a) = true then
-        (implementation_posify as).map (fun rs => resolveAssumptions (assertPositive a) h :: rs)
+      let decl := assertPositive (("finite", true) :: a)
+      if h : declAccepted decl = true then
+        (implementation_posify as).map (fun rs => resolveAssumptions decl h :: rs)
       else
         none
     else
@@ -141,28 +142,47 @@
     ∀ (syms : List Assumptions),
       problem_spec_posify syms (implementation_posify syms) := by
   intro syms
-  induction syms with
-  | nil => simp [problem_spec_posify, implementation_posify]
-  | cons a as ih =>
-    unfold problem_spec_posify at ih ⊢
-    rw [List.filter_cons]
-    by_cases hs : signUndetermined a = true
-    · rw [if_pos hs]
-      by_cases hd : declAccepted (assertPositive a) = true
-      · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
-            declAccepted (assertPositive x) = true
-        · rw [dif_pos ht] at ih
-          rw [dif_pos (fun x hx => by
-            rcases List.mem_cons.mp hx with h' | h'
-            · subst h'; exact hd
-            · exact ht x h')]
-          simp [implementation_posify, hs, hd, ih, List.pmap]
-        · rw [dif_neg ht] at ih
-          rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
-          simp [implementation_posify, hs, hd, ih]
-      · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
-        simp [implementation_posify, hs, hd]
-    · rw [if_neg hs]
-      simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
-      exact ih
+  first
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       rw [List.filter_cons]
+       by_cases hs : signUndetermined a = true
+       · rw [if_pos hs]
+         by_cases hd : declAccepted (assertPositive a) = true
+         · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
+               declAccepted (assertPositive x) = true
+           · rw [dif_pos ht] at ih
+             rw [dif_pos (fun x hx => by
+               rcases List.mem_cons.mp hx with h' | h'
+               · subst h'; exact hd
+               · exact ht x h')]
+             simp [implementation_posify, hs, hd, ih, List.pmap]
+           · rw [dif_neg ht] at ih
+             rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
+             simp [implementation_posify, hs, hd, ih]
+         · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
+           simp [implementation_posify, hs, hd]
+       · rw [if_neg hs]
+         simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
+         exact ih)
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       simp_all [implementation_posify, problem_spec_posify, signUndetermined,
+                 assertPositive, List.filter_cons, List.pmap])
+  | simp [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+          List.pmap, List.filter_cons]
+  | simp_all [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+              List.pmap, List.filter_cons, Id.run]
+  | (unfold problem_spec_posify implementation_posify; rfl)
+  | (intro; rfl)
+  | decide
+  | aesop
+  | (funext; simp_all [problem_spec_posify, implementation_posify])
+  | (induction syms <;>
+     simp_all [problem_spec_posify, implementation_posify, signUndetermined,
+               assertPositive, List.pmap, List.filter_cons, Id.run])
 -- proof-end
```

Attack 17 — `atk_17_negfilter.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -124,16 +124,12 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_posify : List Assumptions → Option (List Assumptions)
-  | [] => some []
-  | a :: as =>
-    if signUndetermined a then
-      if h : declAccepted (assertPositive a) = true then
-        (implementation_posify as).map (fun rs => resolveAssumptions (assertPositive a) h :: rs)
-      else
-        none
-    else
-      implementation_posify as
+def implementation_posify (syms : List Assumptions) : Option (List Assumptions) :=
+  let kept := syms.filter (fun a => !(signUndetermined a))
+  if h : ∀ a ∈ kept, declAccepted (assertPositive a) = true then
+    some (kept.pmap (fun a ha => resolveAssumptions (assertPositive a) ha) h)
+  else
+    none
 -- impl-end
 
 -- proof-start
@@ -141,28 +137,47 @@
     ∀ (syms : List Assumptions),
       problem_spec_posify syms (implementation_posify syms) := by
   intro syms
-  induction syms with
-  | nil => simp [problem_spec_posify, implementation_posify]
-  | cons a as ih =>
-    unfold problem_spec_posify at ih ⊢
-    rw [List.filter_cons]
-    by_cases hs : signUndetermined a = true
-    · rw [if_pos hs]
-      by_cases hd : declAccepted (assertPositive a) = true
-      · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
-            declAccepted (assertPositive x) = true
-        · rw [dif_pos ht] at ih
-          rw [dif_pos (fun x hx => by
-            rcases List.mem_cons.mp hx with h' | h'
-            · subst h'; exact hd
-            · exact ht x h')]
-          simp [implementation_posify, hs, hd, ih, List.pmap]
-        · rw [dif_neg ht] at ih
-          rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
-          simp [implementation_posify, hs, hd, ih]
-      · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
-        simp [implementation_posify, hs, hd]
-    · rw [if_neg hs]
-      simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
-      exact ih
+  first
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       rw [List.filter_cons]
+       by_cases hs : signUndetermined a = true
+       · rw [if_pos hs]
+         by_cases hd : declAccepted (assertPositive a) = true
+         · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
+               declAccepted (assertPositive x) = true
+           · rw [dif_pos ht] at ih
+             rw [dif_pos (fun x hx => by
+               rcases List.mem_cons.mp hx with h' | h'
+               · subst h'; exact hd
+               · exact ht x h')]
+             simp [implementation_posify, hs, hd, ih, List.pmap]
+           · rw [dif_neg ht] at ih
+             rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
+             simp [implementation_posify, hs, hd, ih]
+         · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
+           simp [implementation_posify, hs, hd]
+       · rw [if_neg hs]
+         simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
+         exact ih)
+  | (induction syms with
+     | nil => simp [problem_spec_posify, implementation_posify]
+     | cons a as ih =>
+       unfold problem_spec_posify at ih ⊢
+       simp_all [implementation_posify, problem_spec_posify, signUndetermined,
+                 assertPositive, List.filter_cons, List.pmap])
+  | simp [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+          List.pmap, List.filter_cons]
+  | simp_all [problem_spec_posify, implementation_posify, signUndetermined, assertPositive,
+              List.pmap, List.filter_cons, Id.run]
+  | (unfold problem_spec_posify implementation_posify; rfl)
+  | (intro; rfl)
+  | decide
+  | aesop
+  | (funext; simp_all [problem_spec_posify, implementation_posify])
+  | (induction syms <;>
+     simp_all [problem_spec_posify, implementation_posify, signUndetermined,
+               assertPositive, List.pmap, List.filter_cons, Id.run])
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** Every attack built by region surgery (mk.py) from the frozen Solution.lean, editing ONLY the impl (and, where it legitimately re-proves, the proof) region; axioms/pure/post byte-identical. markers.same_spec = True for all 17 attacks AND the positive control (verified programmatically, 17/17 True, 0 files contain `sorry`).

**POSITIVE CONTROL.** pos_control.lean (= frozen Solution.lean): `bash scripts/lean_verify.sh .../pos_control.lean` -> EXIT=0.

**PREPATCH REPRODUCED.** atk_1_prepatch.lean encodes `resolveAssumptions [("positive",true)] h` (bare positivity, drops the symbol's own properties). Its impl region is normalized-identical to Solution_prepatch.lean's (checked programmatically via markers.region_text). lean_verify EXIT=1 => the spec rejects the prepatch bug.

REFUTED ATTACKS (14) -- all `bash scripts/lean_verify.sh <path>`, run 3-4 at a time as concurrent background jobs: atk_1_prepatch EXIT=1 (PREPATCH BUG: bare positivity declaration) atk_2_partial EXIT=1 (partial-domain: correct iff <=1 kept symbol, else []) atk_3_boundary EXIT=1 (boundary/off-by-one: .dropLast on the kept records) atk_4_cfeffect EXIT=1 (control-flow effect: .reverse -- multiset-equal, list-unequal) atk_5_echo EXIT=1 (ungrounded-oracle echo: return the DECLARATION in place of the engine's inferred record) atk_6_leak EXIT=1 (DEFINEDNESS-SCOPE LEAK = the recorded atk_13 shape re-encoded: acceptance quantified over ALL of `syms`, selection afterwards.

Refuted with semantic unsolved goal `if (forall a in filter ...) then (forall a in syms ...) else exists x in syms, declAccepted ... = false` -- i.e. the acceptance of a NOT-replaced symbol's declaration is opaque and cannot be derived. THE REPAIR HOLDS.) atk_8_declorder EXIT=1 (declaration form: positivity APPENDED `a ++ [("positive",true)]` not consed) atk_9_dropref EXIT=1 (definedness: a refused KEPT declaration answered with a SHORTENED list instead of no value) atk_10_widen EXIT=1 (guard widened by an unsatisfiable disjunct) atk_11_stripkey EXIT=1 (the "positive" key stripped from the symbol's own record before augmentation) atk_14_leak2 EXIT=1 (DEFINEDNESS-SCOPE, 2nd shape: `syms.find?` pre-scan propagating a refusal from any symbol incl. not-replaced ones) atk_15_firstrec EXIT=1 (engine identity: the FIRST kept symbol's record reused for every kept symbol) atk_16_inject EXIT=1 (base integrity: a `("finite",true)` fact the symbol never declared planted into the declaration) atk_17_negfilter EXIT=1 (negated filter: the sign-DETERMINED symbols replaced) Each used a strong 10-alternative `first` proof battery (structural induction / simp_all / rfl / decide / aesop / funext variants), so exit 1 is a genuine rejection rather than a weak-tactic artifact.

VERIFYING ATTACKS (3) -- all materialized, apply-checked, and RESOLVE-RUN: atk_7_identity.lean: EXIT=0. `#print axioms correct_posify` (ax_atk_7.lean, EXIT=0) -> [propext, Classical.choice, Quot.sound], sorryAx=0. A-leg attack on the record-vs-symbol gap: resolve each DISTINCT kept declaration once into a memo table (List.dedup + pmap + lookup) and read every kept symbol's record back out, sharing one resolved result. Proved via memo_hit (lookup finds the entry keyed by `a`; resolveAssumptions is a function of the declaration; acceptance proofs interchangeable by proof irrelevance).

FAITHFUL PATCH = atk_7_recordmemo.diff: the Lean memo table stores RECORDS (the callee's value), not symbols, so the faithful Python memoizes the record per distinct declaration while each free symbol still gets its OWN fresh Dummy. `git apply --check` at a pristine base_commit worktree -> APPLIES. run_resolve('sympy__sympy-16450', ...) -> RESOLVE_RESULT {"resolved": true, "detail": "resolved", "F2P": {"success": ["test_posify"], "failure": []}, "P2P_failures": [], "P2P_success_n": 38}. NOTE ON RIGOUR: I first wrote a SYMBOL-sharing variant (atk_7_identity.diff, one Dummy shared across symbols with equal declarations).

That one does fail (locally: test_separatevars + the `Integral(1/_x,...) + Integral(_x,...)` assertion of test_posify, because posify must return DISTINCT replacements per free symbol). I did NOT report it as a break: symbol identity/freshness is not what the Lean memo table shares -- it stores the inferred RECORD -- so sharing the symbol is an UNFAITHFUL refinement of the attack, not a spec hole. The faithful reading is the record-level memo, and it resolves. atk_12_dedupdef.lean: EXIT=0, axioms [propext, Classical.choice, Quot.sound], sorryAx=0. Definedness-leg residual: settle the acceptance question over the DEDUPLICATED kept declarations (`kept.dedup`) rather than every kept occurrence, via List.mem_dedup.

FAITHFUL PATCH atk_12_dedupdef.diff (probe each distinct kept declaration once; a refusal still raises) -> APPLIES at base_commit; run_resolve -> resolved=true, F2P success=['test_posify'], P2P failures=[], 38/38. atk_13_probeall.lean: EXIT=0, axioms [propext, Quot.sound], sorryAx=0. This is the bundle's OWN declared admitted residual (`pos-probe-every-symbol` in properties.py), re-encoded independently and confirmed same_spec+verifying. FAITHFUL PATCH atk_13_probeall.diff (ASK the domain question at every free symbol, discard the answer where not replaced) -> APPLIES; run_resolve -> resolved=true, F2P success=['test_posify'], P2P failures=[], 38/38. The bundle documents this admission in refinement.md and ships it as a positive control rather than leaving it silent -- correctly, since it is behaviour-preserving.

### A-LEG AUDIT (the assigned focus; R/I pre-cleared by G-CONF).
  * refinement.md leg table: 6 rows, tags = 3x A-reference, 2x R, 1x I. ZERO kind-3 / untagged legs. No A-consumed leg, consistent with meta.json `axioms: []` and axiom_check.py being a legitimate skip stub (the proof consumes no property of the opaque pair -- they occur identically in spec and impl, which I confirmed by reading both regions).
  * A-reference correspondence to the real callee, measured in a base_commit worktree with patch.diff applied: over all 1- and 2-key declarations (826 constructible symbols; 410 accepted / 416 refused), the model triple (declAccepted as "the Dummy(name, positive=True, **assumptions0) call completes", resolveAssumptions as that Dummy's assumptions0, and posify RAISING iff a KEPT declaration is refused) had 0 disagreements with the real patched posify -- value AND definedness, both directions.
  * Filter-predicate leg (tagged I): `signUndetermined a` ("positive" absent from the record) vs `s.is_positive is None` -- exhaustively checked over all 1-, 2- and 3-key declarations (8761 constructible symbols): 0 disagreements.
  * Lazy-assumption-cache probe (a plausible unmodeled A-leg gap I tested explicitly): does querying `s.is_positive` mutate `s.assumptions0`, so that the declaration formed AFTER the filter differs from the one the model forms? Measured over the same 8761 symbols: 0 mutations. No gap.

**WHY SOUND.** The >=5 required attacks were run (17 total, 14 refuted). Every attack whose proof closed with clean axioms had its faithful patch materialized, apply-checked at base_commit, and EXECUTED through the official harness -- 3 of 3 resolved. The one shape that previously broke this cell (the total-oracle map/filter commutation) is refuted in two independent re-encodings. The residual the spec still admits (probe-and-discard, and its dedup variants) is behaviour-preserving and resolves, and is documented rather than hidden. Caveat recorded for the runner: `applied` is reported as null by run_resolve's report shape, but resolved=true with 1/1 F2P and 38/38 P2P entails the patch applied and ran.

**HYGIENE.** All Lean builds went through scripts/lean_verify.sh (never lake/lean directly). Three scratch git worktrees were created under my scratch dir and removed with `git worktree remove --force` + prune; the repo tree carries no new modifications from this audit (pre-existing dirty files from other fleet lanes are untouched).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1_prepatch.lean`, `atk_2_partial.lean`, `atk_3_boundary.lean`, `atk_4_cfeffect.lean`, `atk_5_echo.lean`, `atk_6_leak.lean`, `atk_8_declorder.lean`, `atk_9_dropref.lean`, `atk_10_widen.lean`, `atk_11_stripkey.lean`, `atk_14_leak2.lean`, `atk_15_firstrec.lean`, `atk_16_inject.lean`, `atk_17_negfilter.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_7_identity.lean`, `atk_12_dedupdef.lean`, `atk_13_probeall.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No same-spec wrong implementation with a closing clean-axiom proof has a faithful refined patch that fails to resolve. 17 attacks were run: 14 were REFUTED by the spec (lean_verify exit 1), and the 3 that closed with clean axioms were materialized as faithful patches, applied at base_commit, and RUN through the official harness (run_resolve) -- all 3 returned resolved=true, F2P success=['test_posify'], P2P failures=[] (38/38). The prior recorded BROKEN counterexample (atk_13/atk_14 in verdict.md: the TOTALITY / evaluation-domain hole where a total pure `resolveAssumptions` made map and filter commute) was re-encoded twice against the repaired spec -- atk_6_leak (definedness propagated from EVERY symbol, selection afterwards, the literal atk_13 shape) and atk_14_leak2 (a `find?` pre-scan over the whole list that propagates a refusal from a NOT-replaced symbol) -- and BOTH are now genuinely refuted with semantic `unsolved goals` on the definedness-scope clause, not tactic artifacts. The repair (carrying the partial inference as an operation on its DOMAIN, `resolveAssumptions : (decl) -> declAccepted decl = true -> Assumptions`, with the spec's `dite` scoping definedness to the KEPT declarations) closes that hole.
```

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 17 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_partial.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_boundary.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_cfeffect.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_echo.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_leak.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_identity.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8_declorder.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_dropref.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_widen.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_stripkey.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_dedupdef.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13_probeall.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14_leak2.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15_firstrec.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16_inject.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17_negfilter.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** Every attack built by region surgery (mk.py) from the frozen Solution.lean, editing ONLY the impl (and, where it legitimately re-proves, the proof) region; axioms/pure/post byte-identical. markers.same_spec = True for all 17 attacks AND the positive control (verified programmatically, 17/17 True, 0 files contain `sorry`).

**POSITIVE CONTROL.** pos_control.lean (= frozen Solution.lean): `bash scripts/lean_verify.sh .../pos_control.lean` -> EXIT=0.

**PREPATCH REPRODUCED.** atk_1_prepatch.lean encodes `resolveAssumptions [("positive",true)] h` (bare positivity, drops the symbol's own properties). Its impl region is normalized-identical to Solution_prepatch.lean's (checked programmatically via markers.region_text). lean_verify EXIT=1 => the spec rejects the prepatch bug.

REFUTED ATTACKS (14) -- all `bash scripts/lean_verify.sh <path>`, run 3-4 at a time as concurrent background jobs: atk_1_prepatch EXIT=1 (PREPATCH BUG: bare positivity declaration) atk_2_partial EXIT=1 (partial-domain: correct iff <=1 kept symbol, else []) atk_3_boundary EXIT=1 (boundary/off-by-one: .dropLast on the kept records) atk_4_cfeffect EXIT=1 (control-flow effect: .reverse -- multiset-equal, list-unequal) atk_5_echo EXIT=1 (ungrounded-oracle echo: return the DECLARATION in place of the engine's inferred record) atk_6_leak EXIT=1 (DEFINEDNESS-SCOPE LEAK = the recorded atk_13 shape re-encoded: acceptance quantified over ALL of `syms`, selection afterwards.

Refuted with semantic unsolved goal `if (forall a in filter ...) then (forall a in syms ...) else exists x in syms, declAccepted ... = false` -- i.e. the acceptance of a NOT-replaced symbol's declaration is opaque and cannot be derived. THE REPAIR HOLDS.) atk_8_declorder EXIT=1 (declaration form: positivity APPENDED `a ++ [("positive",true)]` not consed) atk_9_dropref EXIT=1 (definedness: a refused KEPT declaration answered with a SHORTENED list instead of no value) atk_10_widen EXIT=1 (guard widened by an unsatisfiable disjunct) atk_11_stripkey EXIT=1 (the "positive" key stripped from the symbol's own record before augmentation) atk_14_leak2 EXIT=1 (DEFINEDNESS-SCOPE, 2nd shape: `syms.find?` pre-scan propagating a refusal from any symbol incl. not-replaced ones) atk_15_firstrec EXIT=1 (engine identity: the FIRST kept symbol's record reused for every kept symbol) atk_16_inject EXIT=1 (base integrity: a `("finite",true)` fact the symbol never declared planted into the declaration) atk_17_negfilter EXIT=1 (negated filter: the sign-DETERMINED symbols replaced) Each used a strong 10-alternative `first` proof battery (structural induction / simp_all / rfl / decide / aesop / funext variants), so exit 1 is a genuine rejection rather than a weak-tactic artifact.

VERIFYING ATTACKS (3) -- all materialized, apply-checked, and RESOLVE-RUN: atk_7_identity.lean: EXIT=0. `#print axioms correct_posify` (ax_atk_7.lean, EXIT=0) -> [propext, Classical.choice, Quot.sound], sorryAx=0. A-leg attack on the record-vs-symbol gap: resolve each DISTINCT kept declaration once into a memo table (List.dedup + pmap + lookup) and read every kept symbol's record back out, sharing one resolved result. Proved via memo_hit (lookup finds the entry keyed by `a`; resolveAssumptions is a function of the declaration; acceptance proofs interchangeable by proof irrelevance).

FAITHFUL PATCH = atk_7_recordmemo.diff: the Lean memo table stores RECORDS (the callee's value), not symbols, so the faithful Python memoizes the record per distinct declaration while each free symbol still gets its OWN fresh Dummy. `git apply --check` at a pristine base_commit worktree -> APPLIES. run_resolve('sympy__sympy-16450', ...) -> RESOLVE_RESULT {"resolved": true, "detail": "resolved", "F2P": {"success": ["test_posify"], "failure": []}, "P2P_failures": [], "P2P_success_n": 38}. NOTE ON RIGOUR: I first wrote a SYMBOL-sharing variant (atk_7_identity.diff, one Dummy shared across symbols with equal declarations).

That one does fail (locally: test_separatevars + the `Integral(1/_x,...) + Integral(_x,...)` assertion of test_posify, because posify must return DISTINCT replacements per free symbol). I did NOT report it as a break: symbol identity/freshness is not what the Lean memo table shares -- it stores the inferred RECORD -- so sharing the symbol is an UNFAITHFUL refinement of the attack, not a spec hole. The faithful reading is the record-level memo, and it resolves. atk_12_dedupdef.lean: EXIT=0, axioms [propext, Classical.choice, Quot.sound], sorryAx=0. Definedness-leg residual: settle the acceptance question over the DEDUPLICATED kept declarations (`kept.dedup`) rather than every kept occurrence, via List.mem_dedup.

FAITHFUL PATCH atk_12_dedupdef.diff (probe each distinct kept declaration once; a refusal still raises) -> APPLIES at base_commit; run_resolve -> resolved=true, F2P success=['test_posify'], P2P failures=[], 38/38. atk_13_probeall.lean: EXIT=0, axioms [propext, Quot.sound], sorryAx=0. This is the bundle's OWN declared admitted residual (`pos-probe-every-symbol` in properties.py), re-encoded independently and confirmed same_spec+verifying. FAITHFUL PATCH atk_13_probeall.diff (ASK the domain question at every free symbol, discard the answer where not replaced) -> APPLIES; run_resolve -> resolved=true, F2P success=['test_posify'], P2P failures=[], 38/38. The bundle documents this admission in refinement.md and ships it as a positive control rather than leaving it silent -- correctly, since it is behaviour-preserving.

### A-LEG AUDIT (the assigned focus; R/I pre-cleared by G-CONF).
  * refinement.md leg table: 6 rows, tags = 3x A-reference, 2x R, 1x I. ZERO kind-3 / untagged legs. No A-consumed leg, consistent with meta.json `axioms: []` and axiom_check.py being a legitimate skip stub (the proof consumes no property of the opaque pair -- they occur identically in spec and impl, which I confirmed by reading both regions).
  * A-reference correspondence to the real callee, measured in a base_commit worktree with patch.diff applied: over all 1- and 2-key declarations (826 constructible symbols; 410 accepted / 416 refused), the model triple (declAccepted as "the Dummy(name, positive=True, **assumptions0) call completes", resolveAssumptions as that Dummy's assumptions0, and posify RAISING iff a KEPT declaration is refused) had 0 disagreements with the real patched posify -- value AND definedness, both directions.
  * Filter-predicate leg (tagged I): `signUndetermined a` ("positive" absent from the record) vs `s.is_positive is None` -- exhaustively checked over all 1-, 2- and 3-key declarations (8761 constructible symbols): 0 disagreements.
  * Lazy-assumption-cache probe (a plausible unmodeled A-leg gap I tested explicitly): does querying `s.is_positive` mutate `s.assumptions0`, so that the declaration formed AFTER the filter differs from the one the model forms? Measured over the same 8761 symbols: 0 mutations. No gap.

**WHY SOUND.** The >=5 required attacks were run (17 total, 14 refuted). Every attack whose proof closed with clean axioms had its faithful patch materialized, apply-checked at base_commit, and EXECUTED through the official harness -- 3 of 3 resolved. The one shape that previously broke this cell (the total-oracle map/filter commutation) is refuted in two independent re-encodings. The residual the spec still admits (probe-and-discard, and its dedup variants) is behaviour-preserving and resolves, and is documented rather than hidden. Caveat recorded for the runner: `applied` is reported as null by run_resolve's report shape, but resolved=true with 1/1 F2P and 38/38 P2P entails the patch applied and ran.

**HYGIENE.** All Lean builds went through scripts/lean_verify.sh (never lake/lean directly). Three scratch git worktrees were created under my scratch dir and removed with `git worktree remove --force` + prune; the repo tree carries no new modifications from this audit (pre-existing dirty files from other fleet lanes are untouched).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**REFERENCE DISCIPLINE.** Compared the spec against the base worktree (git rev-parse = aefdd023dc4f73c441953ed51f5f05a076f0862f) with patch.diff APPLIED (`git diff` shows exactly the one-line `positive=True` -> `positive=True, **s.assumptions0` hunk and nothing else; sympy.`__file__` confirmed inside the worktree, 1.5.dev). So every divergence class below is spec-vs-POST-patch, not spec-vs-base, and the patch delta itself is not being misread as a divergence.

### INTEGRITY (passed, so this is a faithfulness read on the live spec).
- scripts/lean_verify.sh Solution.lean -> exit 0.
- `#print axioms`: correct_posify = [propext, Quot.sound]; implementation_posify and problem_spec_posify depend on no axioms. NO sorryAx -- the proof is real, not fake.
- markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend()) = True -- spec region byte-identical, so this is a live read of the current spec and retained attacks are not voided.

**WHAT I TRANSCRIBED AND RAN.** I re-implemented problem_spec_posify LITERALLY in Python from the Lean text (signUndetermined = 'positive' key absent; assertPositive = ('positive',True) consed IN FRONT so a record already stating positive supplies the kwarg twice; declAccepted = the total probe 'does Dummy(name,**decl) complete'; resolveAssumptions = Dummy(name,**decl).assumptions0; the dite scoping definedness to the FILTERED symbols only) and differentially compared ('some' records as a multiset, vs 'none' = posify RAISES) against the real patched posify. ~44,000 independent checks, ZERO disagreements in every direction:
- All 1-, 2- and 3-key declarations, single symbol: checked=13805, agree=13805, both_none=185, both_some=13620, spec_none_real_some=0, spec_some_real_none=0, value_disagree=0.
- Multi-symbol (pairs/triples over a pool mixing sign-determined, refused-augmentation and plain declarations, + 4000 random 1-4 symbol cases): checked=9182, agree=9182, both_none=3684, both_some=5498, all three disagreement counters 0. 6200 of these were cases where an EXCLUDED symbol's would-be declaration is refused -- the exact scoping claim -- and the spec's 'some' matched the real return every time.
- Real expression shapes (x+y, `x*y`, 1/x, 1/`x**2`, sqrt, sin, exp, log, `x**y`, f(x)+y, Eq, Matrix, Integral, x/y-y/x, ...) crossed over 16 declaration sets: checked=4550, agree=4550, both_none=1308, both_some=3242, 0 disagreements.
- Deep random fuzz, up to 6 keys, 1-3 symbols, seed 999: checked=14137, agree=14137, both_none=194, 0 disagreements.

**THE PREVIOUSLY-CITED COUNTEREXAMPLE IS NOW CORRECTLY MODELED.** On Symbol('x', rational=False, irrational=False): is_positive is None so signUndetermined=true and the symbol IS replaced; declAccepted(assertPositive a) = FALSE; the spec therefore demands result = none; and the real patched posify raises InconsistentAssumptions. Spec and reference agree. Same for none-propagation from a mixed input (Symbol('g',finite=True) + the bad symbol): spec says none, real raises. The old G-PANEL-2 finding was against a TOTAL `resolveAssumptions : Assumptions -> Assumptions`; the current spec carries the partial operation as an operation on its domain (`resolveAssumptions : (decl) -> declAccepted decl = true -> Assumptions`) and gets this input right.

NOT TOO STRONG, EITHER DIRECTION. The definedness scoping is the one place a `dite` like this usually overclaims, and it is correct: for Symbol('g',finite=True) + Symbol('p',positive=True) the excluded symbol's would-be declaration IS refused (duplicate `positive` kwarg -> the probe answers false), the spec still demands `some` with exactly 1 record, and the real posify returns with n_replacements=1. Verified 6200 times. Conversely no input made the spec claim a value where the real routine raised (spec_some_real_none=0 throughout).

**F2P CASE EXACT.** Symbol('k',finite=True): the spec's record equals the real eq.assumptions0 equals the literal dict asserted in test_patch (finite:True, infinite:False retained alongside positive:True). Confirmed byte-equal.

### Abstraction side conditions I checked myself rather than reading off the record
- mapping.md's filter-predicate claim `s.is_positive is None <=> 'positive' not in s.assumptions0`: 0 mismatches over 1094 exhaustive 1-2 key symbols, and separately 0 assumptions0 CACHE MUTATIONS induced by querying is_positive over 21,326 built symbols (up to 6 keys). So reading the record before vs after the sign query cannot change the modeled input -- the R-tagged filter row is sound.
- `name` irrelevance (the model drops s.name): over 18 adversarial names (empty, 200-char, unicode, 'positive', '$', newline) the inferred record is IDENTICAL (1 distinct record) and the refused declaration is refused for every name (InconsistentAssumptions in all cases). So declAccepted/resolveAssumptions dropping the name is faithful.
- Replacement COUNT: 0 mismatches over 2205 cases between len(reps) and the number of sign-undetermined free symbols -- the per-kept-symbol one-to-one shape holds, including distinct symbols carrying IDENTICAL records (posify(x+y) with both finite=True gives 2 records, and the spec's list gives 2; a set-based model would have collapsed them, this one does not).
- `eq.subs(reps)` cannot raise where the declarations all built: 17 hostile expressions (`zoo*x`, `oo*x`, `I*x`, `x**x`, log(log(x)), f(f(x)), Sum, Integral, Matrix) all spec=some/real=some. So modeling subs/inverse-map as identity relabeling is not hiding a divergence.

**G-CONF IS NO LONGER MASKING.** The `except Exception: continue` around the real-callee observation that let the ORIGINAL defect through is gone: real_posify now returns None on a raise and that None is compared, so a raise is one of the two outcomes rather than a skip. I ran the shipped conformance_check.py against the patched worktree myself: checked=86606, disagreements=0, coverage={'valued': 86005, 'raise': 601, 'off-filter-rejected': 49003} -- it genuinely exercises a valued case, a valueless case, AND the excluded-declaration-refused case, so its pass is evidence rather than an artifact of an uncovered domain.

**CONCLUSION.** No input found on which problem_spec_posify disagrees with the real post-patch posify, in value or in definedness, across ~44k independent checks plus 86,606 conformance checks. The spec is neither too strong (it does not claim a result where the patched routine raises) nor mis-scoped (it does not let a not-replaced symbol's refused declaration destroy a value the real routine returns). FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**Bundle:** benchmark-verified/sympy__sympy-16450/lean. NO relaxation claim exists: `find . -iname '*RELAX*'` over the whole instance dir is empty, and meta.json has no `relaxed_leakage` key (top-level keys: axioms, conf_skip, deep_model_references, gates, modeled_functions, opaque_callees, patch_equals_gold, pbt_audit, prepatch_variants, region_hashes, schema_version, spec_provenance, verifier_pins). The 3 'relaxed' substring hits in meta.json are inside prior G-PANEL-3 ledger prose asserting the same absence, not a claim. So this is a plain strict-lane judgement; nothing was inherited.

### WHAT I MEASURED (all re-run by me, not read off the ledger):
1. Artifact identity. sha256(Solution.lean)=283957998438441c8b38a96b0ffb0915fd16a6106d17799f26473409812a88c2, matching gates G-LEAK/G-HYGIENE/G-INTEGRITY/G-VERIFY/G-GOLD `sources`. NOTE: the recorded G-PANEL-3 pass carries sources.Solution.lean=322a4e93e417..., i.e. the prior leakage pass judged DIFFERENT bytes than the file now on disk — so re-auditing rather than inheriting was correct here.
2. Spec view derived mechanically: markers.spec_view(Solution.lean, LeanBackend()). It contains the module docstring, `abbrev Assumptions`, the two `opaque` declarations and their docstring, `signUndetermined`, `assertPositive`, and `problem_spec_posify`; impl and proof are both replaced by the elision placeholders. Confirmed this is exactly what the consumer sees: eval/prompts.py `_spec_block` renders `task.spec_view` and nothing else (mapping.md / refinement.md / meta.json are NOT in the consumer prompt — good, since mapping.md:16 and refinement.md:29 both reproduce the post-patch line verbatim; that is out-of-view and therefore out of scope). Judged against problem_statement only; hints_text ('the other assumptions should be retained') deliberately excluded.
3. Mechanical screen re-run: leakage.screen(src, LeanBackend(), instance.patch, instance.problem_statement, instance.test_patch) -> passed=True, hard_failures=[], warnings=[]. Non-vacuity checked: `_patch_changed_symbols`(patch)={'posify'}, and 'posify' IS in problem_statement (4 occurrences), so the symbol-collision leg is skipped by design rather than by a lexer miss — meaning the screen alone proves little and I did the manual pass below.
4. Manual token sweep of the spec view for every edit-localizing string: 'assumptions0', 'Dummy', 's.name', 'simplify.py', 'sympy', 'free_symbols', 'subs', 'kwargs', 'splat', 'is_positive', 'StdFactKB', 'InconsistentAssumptions', 'line 251', 'irrational', 'rational' -> ZERO hits. Only 'finite' appears, twice, and 'finite' occurs 9x in the public problem_statement. Diff markers: none. Narration regex over the WHOLE view (not just comments): no hits.
5. Load-bearing / unavoidability control. Stripped every `/-! -/` and `/-- -/` prose block and re-verified: stripped gold compiles clean (exit 0); the prepatch impl body grafted into the same prose-stripped spec FAILS (exit 1, 2 unsolved-goals errors). So the FORMAL postcondition alone is the discriminator and the prose is not load-bearing — which is the right direction for this lane: the narration adds no discriminating power, hence no disclosure the formal text does not already require.
6. Proof soundness (so the disposition rests on a sound gate): scripts/lean_verify.sh Solution.lean -> exit 0; injected `#print axioms correct_posify` -> "depends on axioms: [propext, Quot.sound]", no sorryAx. Solution_prepatch.lean -> exit 1 (unsolved goals at 162, 171), so G-DIFF's fixed behavior is real. axiom_check.py -> status=skip, consistent with no consumed axiom.

### Why the strongest candidates are not leaks
(a) Docstring: "the new symbol is asserted to be positive *in addition to* every property the original symbol already declared — the replacement should not discard any of the original symbol's known properties", formalized as `assertPositive a = ("positive", true) :: a`. This is a restatement of the public ask: problem_statement says "Posify removes a finite assumption from a symbol", shows `xp.is_finite -> None`, and asks "posify should preserve the finiteness assumption. Possibly other assumptions should be preserved as well (integer, rational, prime, even, odd...)". A solver with problem_statement alone derives 'declare the replacement with the original's properties plus positivity'. The spec states the required behavior, not where or in what syntactic form to write it.

(b) The DEFINEDNESS half (the `declAccepted`/`dite` partiality, incl. "a set that states the same property twice is not a declaration") is the one clause not verbatim in problem_statement. It is still not edit-disclosure: it is a consequence of the already-public requirement composed with the unchanged callee the solver can read in the repo, it is phrased entirely abstractly (no kwargs, no `**`, no `Dummy`, no `TypeError`/`InconsistentAssumptions`), and the spec itself says the duplicate case is unreachable for symbols the routine replaces. It localizes nothing.

(c) `signUndetermined` (= `s.is_positive is None`) models PRE-existing, patch-unchanged code, so it cannot localize the edit.

OUT-OF-LANE, REPORTED FOR THE RECORD (neither affects this verdict): meta.json's TOP-LEVEL region_hashes are stale for ALL SIX regions — recomputed axioms/impl/post-conditions/proof/pure/spec_view = 3b4b7b13.., 3a93aba8.., 5ab169a5.., f31b0a15.., 37c67a27.., bb196910.. vs recorded 34cb7ae6.., ea5e2be8.., 24df521b.., 504ed5fe.., 1d6038ad.., 645cd22f.., while gates['G-HYGIENE'].data.region_hashes matches my recomputation on every one. I found no reader of the top-level mirror in src/ or scripts/ (only markers.py writes it and hygiene.py consumes its own copy), so this looks cosmetic, but the spec_view mirror being stale is worth a G-HYGIENE/regate note. Also G-EQ, G-PANEL, G-PANEL-1, G-PANEL-2 are all recorded `fail` with 07:19-08:04 timestamps while every mechanical gate re-passed at 09:42-09:49 after the documented totality repair — i.e. those fails are stale-vs-repair, not live findings in my lane.

**STEERING SWEEP:** no file in the bundle addresses the auditor or suggests a verdict. I grepped lean/, velvet/, nagini/, ears/ for attacker|auditor|reviewer|'honest verdict'|'ignore previous'|'must submit'|'record .*NO-LEAKAGE'|panel; the only hits are refinement.md:112/118 citing prior gate names ('G-EQ / G-PANEL-1 (spec-too-weak), BROKEN', 'G-PANEL-2 (faithfulness)') inside its own audit-history section, which is a factual repair record, plus gate-owned rows in verdict.md. Nothing instructs how to record. My verdict is my own measurement.

**CONCLUSION:** the spec view discloses the required BEHAVIOR (already public in problem_statement) and nothing about the gold edit's file, line, callee, or syntactic form. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
