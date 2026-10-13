# P2 adversarial audit — sympy__sympy-12481

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_2_partial_none.lean`, `atk_3_partial_empty.lean`, `atk_8_echo_cond.lean`, `atk_10_partial_oversize.lean`, `atk_11_partial_rtl.lean`, `atk_12_partial_identity.lean` |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_4_boundary.lean`, `atk_5_rtl.lean`, `atk_6_ctrlflow.lean`, `atk_7_echo_naive.lean`, `atk_9_degenerate_some.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample found. The nearest thing to a residual weakness is the OFF-PRECONDITION region: the precondition `(∀ c ∈ cycles, c.Nodup)` leaves a rival free to do anything on a cycle-list where some SINGLE cycle repeats a point, e.g. cycles = [[0,0,1]] or [[0,1,2],[3,3]]. Six attacks (atk_2/3/10/11/12 partial-domain + atk_8 echo) exploit exactly that freedom, close with clean axioms, and their faithful refined patches were all materialized and RESOLVED (F2P 1/0, P2P 7/0). That region is NOT exploitable, because it is dead code in the real routine: Cycle.__init__ raises ValueError('All elements must be unique in a cycle.') (permutations.py:450-451) before the composition is ever reached, so the injected branch cannot be observed by any caller. Verified empirically in each patched worktree: in-domain all six agree with gold ([[0,1],[0,2]]->[1,2,0] the F2P input, [[1],[1,2]]->[0,2,1], [[1],[4,2]]->[0,1,4,3,2], [[],[0,1]]->[1,0]); off-domain they diverge (atk_2 RAISES / atk_3 [] / atk_12 [0,1] / atk_10 [0,0,2,3,4] / atk_11 [0,0] on [[0,0,1]]).
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,8 +74,12 @@
 -- post-conditions-end
 
 -- impl-start
+-- PREPATCH BUG: reject whenever two cycles share a point (the removed
+-- `has_dups(temp)` arm for cyclic input).
 def implementation_permFromCycles
     (cycles : List (List Nat)) : Option (List Nat) := Id.run do
+  if ¬ cycles.flatten.Nodup then
+    return none
   if sizeUndetermined cycles then
     return none
   let sz := permSize cycles
```

Attack 2 — `atk_2_partial_none.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -74,8 +74,12 @@
 -- post-conditions-end
 
 -- impl-start
+-- PARTIAL DOMAIN: refuse to build whenever SOME SINGLE cycle repeats a
+-- point (off-precondition); gold behaviour on the whole precondition.
 def implementation_permFromCycles
     (cycles : List (List Nat)) : Option (List Nat) := Id.run do
+  if !(cycles.all fun c => decide c.Nodup) then
+    return none
   if sizeUndetermined cycles then
     return none
   let sz := permSize cycles
@@ -95,25 +99,30 @@
       (∀ c ∈ cycles, c.Nodup) →
       problem_spec_permFromCycles cycles
         (implementation_permFromCycles cycles) := by
+  have inner : ∀ (cs : List (List Nat)) (i : Nat),
+      (forIn cs i fun c r => (pure (ForInStep.yield (applyCycle c r)) : Id _))
+      = applyAll cs i := by
+    intro cs
+    unfold applyAll
+    induction cs with
+    | nil => intro i; rfl
+    | cons c cs ih => intro i; simp only [List.forIn_cons, ih]; rfl
   intro cycles hnd
-  clear hnd
-  have inner : ∀ i, (forIn cycles i fun c r => (pure (ForInStep.yield (applyCycle c r)) : Id _))
-      = applyAll cycles i := by
-    intro i
-    unfold applyAll
-    induction cycles generalizing i with
-    | nil => rfl
-    | cons c cs ih => simp only [List.forIn_cons, ih]; rfl
+  have hall : (cycles.all fun c => decide c.Nodup) = true := by
+    rw [List.all_eq_true]
+    intro c hc
+    exact decide_eq_true (hnd c hc)
   constructor
   · intro hdeg
     unfold implementation_permFromCycles
-    simp [hdeg]
+    simp [hall, hdeg]
   · intro hnon
     have key : implementation_permFromCycles cycles
         = some ((List.range (permSize cycles)).map (applyAll cycles)) := by
       unfold implementation_permFromCycles
-      simp only [hnon, Bool.false_eq_true, if_false, Id.run, Std.Range.forIn_eq_forIn_range',
-        bind_pure_comp, map_pure, Std.Range.size, Nat.sub_zero, Nat.add_sub_cancel, Nat.div_one]
+      simp only [hall, Bool.not_true, Bool.false_eq_true, if_false, hnon, Id.run,
+        Std.Range.forIn_eq_forIn_range', bind_pure_comp, map_pure, Std.Range.size,
+        Nat.sub_zero, Nat.add_sub_cancel, Nat.div_one]
       simp only [inner]
       have hfun : (fun (i : Nat) (r : List Nat) =>
           ((fun a => ForInStep.yield (r ++ [a])) <$> applyAll cycles i : Id _))
```

Attack 3 — `atk_3_partial_empty.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -74,8 +74,11 @@
 -- post-conditions-end
 
 -- impl-start
+-- PARTIAL DOMAIN: junk (empty array form) off-precondition.
 def implementation_permFromCycles
     (cycles : List (List Nat)) : Option (List Nat) := Id.run do
+  if !(cycles.all fun c => decide c.Nodup) then
+    return some []
   if sizeUndetermined cycles then
     return none
   let sz := permSize cycles
@@ -95,25 +98,30 @@
       (∀ c ∈ cycles, c.Nodup) →
       problem_spec_permFromCycles cycles
         (implementation_permFromCycles cycles) := by
+  have inner : ∀ (cs : List (List Nat)) (i : Nat),
+      (forIn cs i fun c r => (pure (ForInStep.yield (applyCycle c r)) : Id _))
+      = applyAll cs i := by
+    intro cs
+    unfold applyAll
+    induction cs with
+    | nil => intro i; rfl
+    | cons c cs ih => intro i; simp only [List.forIn_cons, ih]; rfl
   intro cycles hnd
-  clear hnd
-  have inner : ∀ i, (forIn cycles i fun c r => (pure (ForInStep.yield (applyCycle c r)) : Id _))
-      = applyAll cycles i := by
-    intro i
-    unfold applyAll
-    induction cycles generalizing i with
-    | nil => rfl
-    | cons c cs ih => simp only [List.forIn_cons, ih]; rfl
+  have hall : (cycles.all fun c => decide c.Nodup) = true := by
+    rw [List.all_eq_true]
+    intro c hc
+    exact decide_eq_true (hnd c hc)
   constructor
   · intro hdeg
     unfold implementation_permFromCycles
-    simp [hdeg]
+    simp [hall, hdeg]
   · intro hnon
     have key : implementation_permFromCycles cycles
         = some ((List.range (permSize cycles)).map (applyAll cycles)) := by
       unfold implementation_permFromCycles
-      simp only [hnon, Bool.false_eq_true, if_false, Id.run, Std.Range.forIn_eq_forIn_range',
-        bind_pure_comp, map_pure, Std.Range.size, Nat.sub_zero, Nat.add_sub_cancel, Nat.div_one]
+      simp only [hall, Bool.not_true, Bool.false_eq_true, if_false, hnon, Id.run,
+        Std.Range.forIn_eq_forIn_range', bind_pure_comp, map_pure, Std.Range.size,
+        Nat.sub_zero, Nat.add_sub_cancel, Nat.div_one]
       simp only [inner]
       have hfun : (fun (i : Nat) (r : List Nat) =>
           ((fun a => ForInStep.yield (r ++ [a])) <$> applyAll cycles i : Id _))
```

Attack 4 — `atk_4_boundary.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,13 +74,14 @@
 -- post-conditions-end
 
 -- impl-start
+-- BOUNDARY: array form built over [0:sz-1], dropping the last entry.
 def implementation_permFromCycles
     (cycles : List (List Nat)) : Option (List Nat) := Id.run do
   if sizeUndetermined cycles then
     return none
   let sz := permSize cycles
   let mut aform : List Nat := []
-  for i in [0:sz] do
+  for i in [0:sz-1] do
     let mut v := i
     for c in cycles do
       v := applyCycle c v
```

Attack 5 — `atk_5_rtl.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,6 +74,7 @@
 -- post-conditions-end
 
 -- impl-start
+-- WRONG ORDER: cycles composed right-to-left instead of left-to-right.
 def implementation_permFromCycles
     (cycles : List (List Nat)) : Option (List Nat) := Id.run do
   if sizeUndetermined cycles then
@@ -82,7 +83,7 @@
   let mut aform : List Nat := []
   for i in [0:sz] do
     let mut v := i
-    for c in cycles do
+    for c in cycles.reverse do
       v := applyCycle c v
     aform := aform ++ [v]
   return some aform
```

Attack 6 — `atk_6_ctrlflow.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,6 +74,8 @@
 -- post-conditions-end
 
 -- impl-start
+-- CONTROL-FLOW EFFECT: `break` after the first cycle, so only cycles[0]
+-- is ever applied.
 def implementation_permFromCycles
     (cycles : List (List Nat)) : Option (List Nat) := Id.run do
   if sizeUndetermined cycles then
@@ -84,6 +86,7 @@
     let mut v := i
     for c in cycles do
       v := applyCycle c v
+      break
     aform := aform ++ [v]
   return some aform
 -- impl-end
```

Attack 7 — `atk_7_echo_naive.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,18 +74,11 @@
 -- post-conditions-end
 
 -- impl-start
+-- UNGROUNDED-ORACLE ECHO (naive): the postcondition's success leg
+-- transcribed verbatim, with NO degenerate-width guard.
 def implementation_permFromCycles
     (cycles : List (List Nat)) : Option (List Nat) := Id.run do
-  if sizeUndetermined cycles then
-    return none
-  let sz := permSize cycles
-  let mut aform : List Nat := []
-  for i in [0:sz] do
-    let mut v := i
-    for c in cycles do
-      v := applyCycle c v
-    aform := aform ++ [v]
-  return some aform
+  return some ((List.range (permSize cycles)).map (applyAll cycles))
 -- impl-end
 
 
@@ -97,38 +90,16 @@
         (implementation_permFromCycles cycles) := by
   intro cycles hnd
   clear hnd
-  have inner : ∀ i, (forIn cycles i fun c r => (pure (ForInStep.yield (applyCycle c r)) : Id _))
-      = applyAll cycles i := by
-    intro i
-    unfold applyAll
-    induction cycles generalizing i with
-    | nil => rfl
-    | cons c cs ih => simp only [List.forIn_cons, ih]; rfl
+  have key : implementation_permFromCycles cycles
+      = some ((List.range (permSize cycles)).map (applyAll cycles)) := by
+    unfold implementation_permFromCycles
+    rfl
   constructor
   · intro hdeg
-    unfold implementation_permFromCycles
-    simp [hdeg]
-  · intro hnon
-    have key : implementation_permFromCycles cycles
-        = some ((List.range (permSize cycles)).map (applyAll cycles)) := by
-      unfold implementation_permFromCycles
-      simp only [hnon, Bool.false_eq_true, if_false, Id.run, Std.Range.forIn_eq_forIn_range',
-        bind_pure_comp, map_pure, Std.Range.size, Nat.sub_zero, Nat.add_sub_cancel, Nat.div_one]
-      simp only [inner]
-      have hfun : (fun (i : Nat) (r : List Nat) =>
-          ((fun a => ForInStep.yield (r ++ [a])) <$> applyAll cycles i : Id _))
-          = (fun (i : Nat) (r : List Nat) => (ForInStep.yield (r ++ [applyAll cycles i]) : Id _)) := rfl
-      rw [hfun, List.forIn_yield_eq_foldl]
-      rw [List.range_eq_range']
-      generalize (permSize cycles) = sz
-      have foldl_app : ∀ (len start : Nat) (acc : List Nat),
-          (List.range' start len).foldl (fun r i => r ++ [applyAll cycles i]) acc
-          = acc ++ (List.range' start len).map (applyAll cycles) := by
-        intro len
-        induction len with
-        | zero => intro start acc; simp
-        | succ n ih => intro start acc; rw [List.range'_succ]; simp only [List.foldl_cons, List.map_cons, ih]; simp
-      rw [foldl_app]; simp; rfl
+    rw [key]
+    simp only [sizeUndetermined, Bool.and_eq_true, beq_iff_eq] at hdeg
+    simp [hdeg.2]
+  · intro _
     rw [key]
     refine ⟨_, rfl, ?_, ?_⟩
     · simp
```

Attack 8 — `atk_8_echo_cond.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -74,18 +74,13 @@
 -- post-conditions-end
 
 -- impl-start
+-- UNGROUNDED-ORACLE ECHO (conditioned): both legs of the postcondition
+-- transcribed verbatim as the implementation.
 def implementation_permFromCycles
     (cycles : List (List Nat)) : Option (List Nat) := Id.run do
   if sizeUndetermined cycles then
     return none
-  let sz := permSize cycles
-  let mut aform : List Nat := []
-  for i in [0:sz] do
-    let mut v := i
-    for c in cycles do
-      v := applyCycle c v
-    aform := aform ++ [v]
-  return some aform
+  return some ((List.range (permSize cycles)).map (applyAll cycles))
 -- impl-end
 
 
@@ -97,13 +92,6 @@
         (implementation_permFromCycles cycles) := by
   intro cycles hnd
   clear hnd
-  have inner : ∀ i, (forIn cycles i fun c r => (pure (ForInStep.yield (applyCycle c r)) : Id _))
-      = applyAll cycles i := by
-    intro i
-    unfold applyAll
-    induction cycles generalizing i with
-    | nil => rfl
-    | cons c cs ih => simp only [List.forIn_cons, ih]; rfl
   constructor
   · intro hdeg
     unfold implementation_permFromCycles
@@ -112,23 +100,8 @@
     have key : implementation_permFromCycles cycles
         = some ((List.range (permSize cycles)).map (applyAll cycles)) := by
       unfold implementation_permFromCycles
-      simp only [hnon, Bool.false_eq_true, if_false, Id.run, Std.Range.forIn_eq_forIn_range',
-        bind_pure_comp, map_pure, Std.Range.size, Nat.sub_zero, Nat.add_sub_cancel, Nat.div_one]
-      simp only [inner]
-      have hfun : (fun (i : Nat) (r : List Nat) =>
-          ((fun a => ForInStep.yield (r ++ [a])) <$> applyAll cycles i : Id _))
-          = (fun (i : Nat) (r : List Nat) => (ForInStep.yield (r ++ [applyAll cycles i]) : Id _)) := rfl
-      rw [hfun, List.forIn_yield_eq_foldl]
-      rw [List.range_eq_range']
-      generalize (permSize cycles) = sz
-      have foldl_app : ∀ (len start : Nat) (acc : List Nat),
-          (List.range' start len).foldl (fun r i => r ++ [applyAll cycles i]) acc
-          = acc ++ (List.range' start len).map (applyAll cycles) := by
-        intro len
-        induction len with
-        | zero => intro start acc; simp
-        | succ n ih => intro start acc; rw [List.range'_succ]; simp only [List.foldl_cons, List.map_cons, ih]; simp
-      rw [foldl_app]; simp; rfl
+      simp only [hnon, Bool.false_eq_true, if_false, Id.run]
+      rfl
     rw [key]
     refine ⟨_, rfl, ?_, ?_⟩
     · simp
```

Attack 9 — `atk_9_degenerate_some.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,10 +74,10 @@
 -- post-conditions-end
 
 -- impl-start
+-- DEGENERATE LEG DROPPED: no `sizeUndetermined` guard, so a supplied-but-
+-- pointless cycle list yields `some []` instead of nothing.
 def implementation_permFromCycles
     (cycles : List (List Nat)) : Option (List Nat) := Id.run do
-  if sizeUndetermined cycles then
-    return none
   let sz := permSize cycles
   let mut aform : List Nat := []
   for i in [0:sz] do
@@ -104,31 +104,32 @@
     induction cycles generalizing i with
     | nil => rfl
     | cons c cs ih => simp only [List.forIn_cons, ih]; rfl
+  have key : implementation_permFromCycles cycles
+      = some ((List.range (permSize cycles)).map (applyAll cycles)) := by
+    unfold implementation_permFromCycles
+    simp only [Id.run, Std.Range.forIn_eq_forIn_range',
+      bind_pure_comp, map_pure, Std.Range.size, Nat.sub_zero, Nat.add_sub_cancel, Nat.div_one]
+    simp only [inner]
+    have hfun : (fun (i : Nat) (r : List Nat) =>
+        ((fun a => ForInStep.yield (r ++ [a])) <$> applyAll cycles i : Id _))
+        = (fun (i : Nat) (r : List Nat) => (ForInStep.yield (r ++ [applyAll cycles i]) : Id _)) := rfl
+    rw [hfun, List.forIn_yield_eq_foldl]
+    rw [List.range_eq_range']
+    generalize (permSize cycles) = sz
+    have foldl_app : ∀ (len start : Nat) (acc : List Nat),
+        (List.range' start len).foldl (fun r i => r ++ [applyAll cycles i]) acc
+        = acc ++ (List.range' start len).map (applyAll cycles) := by
+      intro len
+      induction len with
+      | zero => intro start acc; simp
+      | succ n ih => intro start acc; rw [List.range'_succ]; simp only [List.foldl_cons, List.map_cons, ih]; simp
+    rw [foldl_app]; simp; rfl
   constructor
   · intro hdeg
-    unfold implementation_permFromCycles
-    simp [hdeg]
-  · intro hnon
-    have key : implementation_permFromCycles cycles
-        = some ((List.range (permSize cycles)).map (applyAll cycles)) := by
-      unfold implementation_permFromCycles
-      simp only [hnon, Bool.false_eq_true, if_false, Id.run, Std.Range.forIn_eq_forIn_range',
-        bind_pure_comp, map_pure, Std.Range.size, Nat.sub_zero, Nat.add_sub_cancel, Nat.div_one]
-      simp only [inner]
-      have hfun : (fun (i : Nat) (r : List Nat) =>
-          ((fun a => ForInStep.yield (r ++ [a])) <$> applyAll cycles i : Id _))
-          = (fun (i : Nat) (r : List Nat) => (ForInStep.yield (r ++ [applyAll cycles i]) : Id _)) := rfl
-      rw [hfun, List.forIn_yield_eq_foldl]
-      rw [List.range_eq_range']
-      generalize (permSize cycles) = sz
-      have foldl_app : ∀ (len start : Nat) (acc : List Nat),
-          (List.range' start len).foldl (fun r i => r ++ [applyAll cycles i]) acc
-          = acc ++ (List.range' start len).map (applyAll cycles) := by
-        intro len
-        induction len with
-        | zero => intro start acc; simp
-        | succ n ih => intro start acc; rw [List.range'_succ]; simp only [List.foldl_cons, List.map_cons, ih]; simp
-      rw [foldl_app]; simp; rfl
+    rw [key]
+    simp only [sizeUndetermined, Bool.and_eq_true, beq_iff_eq] at hdeg
+    simp [hdeg.2]
+  · intro _
     rw [key]
     refine ⟨_, rfl, ?_, ?_⟩
     · simp
```

Attack 10 — `atk_10_partial_oversize.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -74,8 +74,12 @@
 -- post-conditions-end
 
 -- impl-start
+-- PARTIAL DOMAIN + BOUNDARY: off-precondition the array form is built
+-- over permSize + 3 entries (a length violation).
 def implementation_permFromCycles
     (cycles : List (List Nat)) : Option (List Nat) := Id.run do
+  if !(cycles.all fun c => decide c.Nodup) then
+    return some ((List.range (permSize cycles + 3)).map (applyAll cycles))
   if sizeUndetermined cycles then
     return none
   let sz := permSize cycles
@@ -95,25 +99,30 @@
       (∀ c ∈ cycles, c.Nodup) →
       problem_spec_permFromCycles cycles
         (implementation_permFromCycles cycles) := by
+  have inner : ∀ (cs : List (List Nat)) (i : Nat),
+      (forIn cs i fun c r => (pure (ForInStep.yield (applyCycle c r)) : Id _))
+      = applyAll cs i := by
+    intro cs
+    unfold applyAll
+    induction cs with
+    | nil => intro i; rfl
+    | cons c cs ih => intro i; simp only [List.forIn_cons, ih]; rfl
   intro cycles hnd
-  clear hnd
-  have inner : ∀ i, (forIn cycles i fun c r => (pure (ForInStep.yield (applyCycle c r)) : Id _))
-      = applyAll cycles i := by
-    intro i
-    unfold applyAll
-    induction cycles generalizing i with
-    | nil => rfl
-    | cons c cs ih => simp only [List.forIn_cons, ih]; rfl
+  have hall : (cycles.all fun c => decide c.Nodup) = true := by
+    rw [List.all_eq_true]
+    intro c hc
+    exact decide_eq_true (hnd c hc)
   constructor
   · intro hdeg
     unfold implementation_permFromCycles
-    simp [hdeg]
+    simp [hall, hdeg]
   · intro hnon
     have key : implementation_permFromCycles cycles
         = some ((List.range (permSize cycles)).map (applyAll cycles)) := by
       unfold implementation_permFromCycles
-      simp only [hnon, Bool.false_eq_true, if_false, Id.run, Std.Range.forIn_eq_forIn_range',
-        bind_pure_comp, map_pure, Std.Range.size, Nat.sub_zero, Nat.add_sub_cancel, Nat.div_one]
+      simp only [hall, Bool.not_true, Bool.false_eq_true, if_false, hnon, Id.run,
+        Std.Range.forIn_eq_forIn_range', bind_pure_comp, map_pure, Std.Range.size,
+        Nat.sub_zero, Nat.add_sub_cancel, Nat.div_one]
       simp only [inner]
       have hfun : (fun (i : Nat) (r : List Nat) =>
           ((fun a => ForInStep.yield (r ++ [a])) <$> applyAll cycles i : Id _))
```

Attack 11 — `atk_11_partial_rtl.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -74,8 +74,12 @@
 -- post-conditions-end
 
 -- impl-start
+-- PARTIAL DOMAIN + WRONG ORDER: off-precondition the cycles are composed
+-- right-to-left.
 def implementation_permFromCycles
     (cycles : List (List Nat)) : Option (List Nat) := Id.run do
+  if !(cycles.all fun c => decide c.Nodup) then
+    return some ((List.range (permSize cycles)).map (fun i => cycles.reverse.foldl (fun v c => applyCycle c v) i))
   if sizeUndetermined cycles then
     return none
   let sz := permSize cycles
@@ -95,25 +99,30 @@
       (∀ c ∈ cycles, c.Nodup) →
       problem_spec_permFromCycles cycles
         (implementation_permFromCycles cycles) := by
+  have inner : ∀ (cs : List (List Nat)) (i : Nat),
+      (forIn cs i fun c r => (pure (ForInStep.yield (applyCycle c r)) : Id _))
+      = applyAll cs i := by
+    intro cs
+    unfold applyAll
+    induction cs with
+    | nil => intro i; rfl
+    | cons c cs ih => intro i; simp only [List.forIn_cons, ih]; rfl
   intro cycles hnd
-  clear hnd
-  have inner : ∀ i, (forIn cycles i fun c r => (pure (ForInStep.yield (applyCycle c r)) : Id _))
-      = applyAll cycles i := by
-    intro i
-    unfold applyAll
-    induction cycles generalizing i with
-    | nil => rfl
-    | cons c cs ih => simp only [List.forIn_cons, ih]; rfl
+  have hall : (cycles.all fun c => decide c.Nodup) = true := by
+    rw [List.all_eq_true]
+    intro c hc
+    exact decide_eq_true (hnd c hc)
   constructor
   · intro hdeg
     unfold implementation_permFromCycles
-    simp [hdeg]
+    simp [hall, hdeg]
   · intro hnon
     have key : implementation_permFromCycles cycles
         = some ((List.range (permSize cycles)).map (applyAll cycles)) := by
       unfold implementation_permFromCycles
-      simp only [hnon, Bool.false_eq_true, if_false, Id.run, Std.Range.forIn_eq_forIn_range',
-        bind_pure_comp, map_pure, Std.Range.size, Nat.sub_zero, Nat.add_sub_cancel, Nat.div_one]
+      simp only [hall, Bool.not_true, Bool.false_eq_true, if_false, hnon, Id.run,
+        Std.Range.forIn_eq_forIn_range', bind_pure_comp, map_pure, Std.Range.size,
+        Nat.sub_zero, Nat.add_sub_cancel, Nat.div_one]
       simp only [inner]
       have hfun : (fun (i : Nat) (r : List Nat) =>
           ((fun a => ForInStep.yield (r ++ [a])) <$> applyAll cycles i : Id _))
```

Attack 12 — `atk_12_partial_identity.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

```diff
@@ -74,8 +74,12 @@
 -- post-conditions-end
 
 -- impl-start
+-- PARTIAL DOMAIN: off-precondition the identity permutation is returned
+-- instead of the composition.
 def implementation_permFromCycles
     (cycles : List (List Nat)) : Option (List Nat) := Id.run do
+  if !(cycles.all fun c => decide c.Nodup) then
+    return some (List.range (permSize cycles))
   if sizeUndetermined cycles then
     return none
   let sz := permSize cycles
@@ -95,25 +99,30 @@
       (∀ c ∈ cycles, c.Nodup) →
       problem_spec_permFromCycles cycles
         (implementation_permFromCycles cycles) := by
+  have inner : ∀ (cs : List (List Nat)) (i : Nat),
+      (forIn cs i fun c r => (pure (ForInStep.yield (applyCycle c r)) : Id _))
+      = applyAll cs i := by
+    intro cs
+    unfold applyAll
+    induction cs with
+    | nil => intro i; rfl
+    | cons c cs ih => intro i; simp only [List.forIn_cons, ih]; rfl
   intro cycles hnd
-  clear hnd
-  have inner : ∀ i, (forIn cycles i fun c r => (pure (ForInStep.yield (applyCycle c r)) : Id _))
-      = applyAll cycles i := by
-    intro i
-    unfold applyAll
-    induction cycles generalizing i with
-    | nil => rfl
-    | cons c cs ih => simp only [List.forIn_cons, ih]; rfl
+  have hall : (cycles.all fun c => decide c.Nodup) = true := by
+    rw [List.all_eq_true]
+    intro c hc
+    exact decide_eq_true (hnd c hc)
   constructor
   · intro hdeg
     unfold implementation_permFromCycles
-    simp [hdeg]
+    simp [hall, hdeg]
   · intro hnon
     have key : implementation_permFromCycles cycles
         = some ((List.range (permSize cycles)).map (applyAll cycles)) := by
       unfold implementation_permFromCycles
-      simp only [hnon, Bool.false_eq_true, if_false, Id.run, Std.Range.forIn_eq_forIn_range',
-        bind_pure_comp, map_pure, Std.Range.size, Nat.sub_zero, Nat.add_sub_cancel, Nat.div_one]
+      simp only [hall, Bool.not_true, Bool.false_eq_true, if_false, hnon, Id.run,
+        Std.Range.forIn_eq_forIn_range', bind_pure_comp, map_pure, Std.Range.size,
+        Nat.sub_zero, Nat.add_sub_cancel, Nat.div_one]
       simp only [inner]
       have hfun : (fun (i : Nat) (r : List Nat) =>
           ((fun a => ForInStep.yield (r ++ [a])) <$> applyAll cycles i : Id _))
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building a permutation from a list of cycles given in cyclic notation.

A permutation on `{0, 1, …, n-1}` can be described by a list of cycles. Each
cycle is a list of distinct points `[a₀, a₁, …, a_{k-1}]` and denotes the rule
that sends `a₀ ↦ a₁ ↦ … ↦ a_{k-1} ↦ a₀`, leaving every other point unmoved.

When several cycles are supplied they are *composed in left-to-right order*: the
first cycle is applied first, then the second to that result, and so on. The
cycles need not move disjoint sets of points — a point may appear in more than
one cycle, in which case the successive rules simply chain through it. The size
of the resulting permutation is one more than the largest point named by any
cycle (so every point from `0` up to that maximum is listed), and the result is
returned in *array form*: the list whose `i`-th entry is the image of `i` under
the composed permutation.

A supplied-but-pointless list of cycles is the one degenerate case: if at least
one cycle is handed over yet no cycle names any point at all, the width of the
array form is not determined by the input and nothing is returned.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the action of a single
-- cycle and the left-to-right composition of several cycles are both spelled out
-- concretely (the `applyCycle` / `applyAll` helpers below), so there is nothing
-- to axiomatize — the modeled behavior is validated directly against the real
-- routine by the differential conformance check (an A-reference).
-- axioms-end

-- pure-start
/-- The image of `x` under a single cycle `c` listed as `[a₀, …, a_{k-1}]`:
if `x` occurs in `c` it is sent to the next entry cyclically (`a_{k-1} ↦ a₀`);
otherwise `x` is left unmoved. -/
def applyCycle (c : List Nat) (x : Nat) : Nat :=
  if c.contains x then c.getD ((c.idxOf x + 1) % c.length) x else x

/-- The image of `x` under the left-to-right composition of all `cycles`
(first cycle applied first). -/
def applyAll (cycles : List (List Nat)) (x : Nat) : Nat :=
  cycles.foldl (fun v c => applyCycle c v) x

/-- One past the largest point named by any cycle (`0` when no point is named).
This is the number of entries in the array form. -/
def permSize (cycles : List (List Nat)) : Nat :=
  cycles.flatten.foldl (fun m x => max m (x + 1)) 0

/-- The degenerate shape: at least one cycle was supplied, yet between them the
cycles name no point at all, so the array form has no determined width. -/
def sizeUndetermined (cycles : List (List Nat)) : Bool :=
  !cycles.isEmpty && permSize cycles == 0
-- pure-end

-- post-conditions-start
/-- Two legs, selected by whether the input determines a width.

* Degenerate leg (`sizeUndetermined cycles`): nothing is returned.
* Otherwise the construction succeeds (`result = some aform`) and `aform` is the
  array form of the left-to-right composition of `cycles`: it has
  `permSize cycles` entries (one per point from `0` to the maximum named), and
  its `i`-th entry is the image of `i` under the composed permutation. -/
def problem_spec_permFromCycles
    (cycles : List (List Nat)) (result : Option (List Nat)) : Prop :=
  (sizeUndetermined cycles = true → result = none) ∧
  (sizeUndetermined cycles = false →
    ∃ aform, result = some aform ∧
      aform.length = permSize cycles ∧
      (∀ i, i < permSize cycles → aform.getD i 0 = applyAll cycles i))
-- post-conditions-end

-- impl-start
def implementation_permFromCycles
    (cycles : List (List Nat)) : Option (List Nat) := Id.run do
  if sizeUndetermined cycles then
    return none
  let sz := permSize cycles
  let mut aform : List Nat := []
  for i in [0:sz] do
    let mut v := i
    for c in cycles do
      v := applyCycle c v
    aform := aform ++ [v]
  return some aform
-- impl-end

-- proof-start
theorem correct_permFromCycles :
    ∀ (cycles : List (List Nat)),
      (∀ c ∈ cycles, c.Nodup) →
      problem_spec_permFromCycles cycles
        (implementation_permFromCycles cycles) := by
  intro cycles hnd
  clear hnd
  have inner : ∀ i, (forIn cycles i fun c r => (pure (ForInStep.yield (applyCycle c r)) : Id _))
      = applyAll cycles i := by
    intro i
    unfold applyAll
    induction cycles generalizing i with
    | nil => rfl
    | cons c cs ih => simp only [List.forIn_cons, ih]; rfl
  constructor
  · intro hdeg
    unfold implementation_permFromCycles
    simp [hdeg]
  · intro hnon
    have key : implementation_permFromCycles cycles
        = some ((List.range (permSize cycles)).map (applyAll cycles)) := by
      unfold implementation_permFromCycles
      simp only [hnon, Bool.false_eq_true, if_false, Id.run, Std.Range.forIn_eq_forIn_range',
        bind_pure_comp, map_pure, Std.Range.size, Nat.sub_zero, Nat.add_sub_cancel, Nat.div_one]
      simp only [inner]
      have hfun : (fun (i : Nat) (r : List Nat) =>
          ((fun a => ForInStep.yield (r ++ [a])) <$> applyAll cycles i : Id _))
          = (fun (i : Nat) (r : List Nat) => (ForInStep.yield (r ++ [applyAll cycles i]) : Id _)) := rfl
      rw [hfun, List.forIn_yield_eq_foldl]
      rw [List.range_eq_range']
      generalize (permSize cycles) = sz
      have foldl_app : ∀ (len start : Nat) (acc : List Nat),
          (List.range' start len).foldl (fun r i => r ++ [applyAll cycles i]) acc
          = acc ++ (List.range' start len).map (applyAll cycles) := by
        intro len
        induction len with
        | zero => intro start acc; simp
        | succ n ih => intro start acc; rw [List.range'_succ]; simp only [List.foldl_cons, List.map_cons, ih]; simp
      rw [foldl_app]; simp; rfl
    rw [key]
    refine ⟨_, rfl, ?_, ?_⟩
    · simp
    · intro i hi
      rw [List.getD_eq_getElem?_getD, List.getElem?_map, List.getElem?_range hi]
      simp

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity, adversarial) — sympy__sympy-12481, lean backend.
NOTE ON PRIOR PASSES: the retained verdict.md G-EQ ledger is STALE — the impl it quotes has NO `sizeUndetermined` guard, whereas the current Solution.lean does. Every attack below was re-encoded and re-run from scratch against the CURRENT spec; nothing was carried over.

### COMMANDS (verbatim)
Lean:      bash scripts/lean_verify.sh <f>.lean     (run from swe-proof)
Axioms:    same command on ax_<f>.lean (= <f>.lean with `#print axioms correct_permFromCycles` inserted before -- proof-end)
Same-spec: swebench_unified.markers.same_spec(Solution.lean, atk, 'lean')  -> True for ALL 12 attacks + positive control
Resolve:   python resolve1.py <name>  -> swebench_unified.harness.run_resolve('sympy__sympy-12481', patch, retries=0); raw JSON in resolve_<name>.json
Integrity: all 13 files have same_spec=True, `correct_permFromCycles` STATEMENT byte-identical to gold, and zero evasions (no sorry / native_decide / axiom / implemented_by). No `axiom` is declared anywhere in Solution.lean.
Verifications were run 4-at-a-time as concurrent background jobs; schedule only, every attack fully verified.

### Positive control
pos_control.lean (bundle impl+proof verbatim): EXIT=0; axioms [propext, Classical.choice, Quot.sound]. CLEAN — non-vacuous.

#### PREPATCH REPRODUCED: True
atk_1_prepatch.lean — impl guards `if ¬ cycles.flatten.Nodup then return none` (the removed has_dups arm) + gold proof: EXIT=1, `rfl` fails at the `key` step (LHS retains the `if cycles.flatten.Nodup` scrutinee, not defeq to `some (...)`). Genuinely unprovable, not a tactic artifact. Independently, the bundle's own Solution_prepatch.lean exits 3 (sorry).

#### ATTACKS THAT DO NOT CLOSE — the spec correctly rejects them (6)
 1. atk_1_prepatch.lean          EXIT=1  full-domain rejection of shared points (THE prepatch bug)
 2. atk_4_boundary.lean          EXIT=1  loop over [0:sz-1]: last array-form entry dropped -> length conjunct catches it
 3. atk_5_rtl.lean               EXIT=1  `for c in cycles.reverse`: right-to-left composition -> applyAll's foldl order is pinned
 4. atk_6_ctrlflow.lean          EXIT=1  CONTROL-FLOW EFFECT: `break` after the first cycle, so only cycles[0] applies
 5. atk_7_echo_naive.lean        EXIT=1  oracle echo with NO degenerate guard: unsolved goal `⊢ False` from hdeg — the sizeUndetermined leg is load-bearing and cannot be skipped
 6. atk_9_degenerate_some.lean   EXIT=1  degenerate leg dropped (returns `some []` on a pointless cycle list): same `⊢ False`. Confirms the added guard is REQUIRED, i.e. the new leg is not decorative.

== ATTACKS THAT CLOSE WITH CLEAN AXIOMS (6) — every one materialized as a faithful patch and EXECUTED through run_resolve ==
 7. atk_2_partial_none.lean       EXIT=0 axioms [propext, Classical.choice, Quot.sound] -> patch_atk_2_partial_none.diff       resolved=True completed=True note=resolved  F2P 1/0  P2P 7/0
 8. atk_3_partial_empty.lean      EXIT=0 axioms [propext, Classical.choice, Quot.sound] -> patch_atk_3_partial_empty.diff      resolved=True completed=True  F2P 1/0  P2P 7/0
 9. atk_10_partial_oversize.lean  EXIT=0 axioms [propext, Classical.choice, Quot.sound] -> patch_atk_10_partial_oversize.diff  resolved=True completed=True  F2P 1/0  P2P 7/0
10. atk_11_partial_rtl.lean       EXIT=0 axioms [propext, Classical.choice, Quot.sound] -> patch_atk_11_partial_rtl.diff       resolved=True completed=True  F2P 1/0  P2P 7/0
11. atk_12_partial_identity.lean  EXIT=0 axioms [propext, Classical.choice, Quot.sound] -> patch_atk_12_partial_identity.diff  resolved=True completed=True  F2P 1/0  P2P 7/0
12. atk_8_echo_cond.lean          EXIT=0 axioms [propext]                               -> patch_atk_8_echo_cond.diff (= gold)  resolved=True completed=True  F2P 1/0  P2P 7/0
ZERO patches failed to resolve => verify⇏correct is NOT exhibited.

Attacks 7-11 are the partial-domain family: guard `if !(cycles.all fun c => decide c.Nodup) then return <junk>` ahead of the gold body, with junk = none / some [] / oversize (permSize+3 entries) / right-to-left composition / identity. Their faithful patches transcribe Lean's applyCycle/applyAll/permSize directly into the is_cycle block (the real Cycle.`__init__` cannot be used off-domain since it raises), gated on `any(has_dups(ci) for ci in args)`. NOTE (proof engineering, not a spec property): my first partial-domain proofs failed because putting `hall` in context before `have inner` blocks `induction cycles generalizing i`.

Restating `inner` as a standalone `∀ cs i` lemma fixed it — so this family closes and the honest result is that the free off-precondition region IS provably exploitable, just not test-observable. Off-domain divergence confirmed live, not vacuous (probe.py per worktree): on [[0,0,1]] gold RAISES 'All elements must be unique in a cycle.' while atk_2 RAISES the old cyclic message / atk_3 [] / atk_12 [0,1] / atk_10 [0,0,2,3,4] / atk_11 [0,0]; on [[0,1,2],[3,3]] atk_3 [] / atk_12 [0,1,2,3] / atk_10 [1,2,0,3,4,5,6] / atk_11 [1,2,0,3]. In-domain all six are byte-equal to gold on [[0,1],[0,2]], [[1],[1,2]], [[1],[4,2]], [[0,1],[0,1]], [[1,2]], [[0],[1]], [[3]], [[],[0,1]], and all agree with gold on the degenerate family ([[]], [[],[]] RAISE 'must give size for empty Cycle'; [] -> []).

### Why the spec is tight
problem_spec_permFromCycles pins the output TOTALLY on its domain: result = some aform AND aform.length = permSize AND (∀ i < permSize, aform.getD i 0 = applyAll cycles i). Length plus every in-range index are both fixed, so exactly ONE aform satisfies the success leg; the degenerate leg forces `none`. The only freedom left is the off-precondition region (a cycle with an INTERNAL duplicate), which is dead code in the real routine — Cycle.`__init__` raises before the composition (permutations.py:450-451, verified: Permutation([[0,0,1]]) and Permutation([[0,1,2],[3,3]]) both raise at base and post-patch). That is why all 6 off-domain rivals still resolve. Note the precondition is a per-cycle condition and says nothing about points shared BETWEEN cycles, so the sub-domain the patch actually opens ([[0,1],[0,2]]) stays fully constrained — which is what makes atk_1_prepatch fail to verify.

### REFINEMENT.MD AUDIT (the A legs)
Leg tags: 2 R, 1 I, 4 A-reference. NO kind-3 leg (no axiom consumed without validation); no `axiom` declared in Solution.lean (axioms region is prose only), so G-AX's skip stub is legitimate.
Row-by-row re-checked against  permutations.py @ c807dfe756:
  - `cycles: List (List Nat)` <-> `args = [[int(i) for i in c] for c in args]` (R). CONFIRMED: is_cycle = `args and is_sequence(args[0])` (line 884-887) — list-of-lists is exactly the modeled branch.
  - absence of a `none` early-return <-> the REMOVED `if has_dups(temp): if is_cycle: raise` arm (A-reference, THE edited op). CONFIRMED against patch.diff: post-patch reads `if has_dups(temp) and not is_cycle`.
  - `permSize cycles` <-> `Cycle.list()` width (A-reference). CONFIRMED: Cycle.list with size=None uses self.size = max(self.keys())+1 (455-459).
  - the `for i / for c in cycles` fold <-> `c = Cycle(); for ci in args: c = c(*ci); c.list()` (A-reference) — the SUBTLE leg. Cycle.`__call__` builds `rv = Cycle(*other)` then sets rv[k] = rv[self[k]] for k in self.keys(), i.e. self acts FIRST; iterating args left-to-right therefore makes the LEFTMOST cycle act first, matching foldl. HOLDS.
  - `sizeUndetermined cycles` <-> Cycle.list's `if not self and size is None: raise ValueError('must give size for empty Cycle')` (369-370) (A-reference). CONFIRMED, including the conditioning on a non-empty cycle list: Permutation([]) takes the array-form branch and yields [] rather than refusing.
  - `aform:= aform ++ [v]` <-> `[self[i] for i in range(size)]` (I); `return some aform` <-> `obj._array_form = aform` (R).
A-reference claims are MACHINE-backed, not prose. My own independent differential (axref.py, seeded 20240630, 4000 random cycle lists + 9 hand cases, run against the real Cycle): checked=3747 disagreements=0 on BOTH the value leg (aform[i] == applyAll) and the width leg (len(Cycle.list()) == permSize). The degenerate leg was validated separately (degref.py): [[]], [[],[]], [[],[],[]], [[],[],[],[]] all raise 'must give size for empty Cycle', and [] -> [].
One documented, non-exploitable imprecision: the Lean model is MORE defined than Python on internal-dup cycles (real raises) — the model is total there while the real routine refuses. That direction can only make the spec stricter on real inputs, never license wrong behavior, and the precondition is exactly the guard that fences it off; atk_2/3/10/11/12 show it is dead code in the refined patch. The previously-flagged [[]] gap is now CLOSED by the sizeUndetermined leg, and atk_7/atk_9 prove that leg is load-bearing (both fail to verify without it).

### Conclusion
12 attacks run (>= 5 required) across 7 distinct wrong-impl families: prepatch full-domain rejection, partial-domain x5 (none/empty/oversize/rtl/identity payloads), boundary off-by-one, right-to-left composition, control-flow (`break`) effect, degenerate-leg drop, and ungrounded-oracle echo x2. 6 fail to verify exactly as they should; 6 close with clean axioms (no sorryAx, no custom axiom) and EVERY one of those 6 had its faithful refined patch materialized and EXECUTED through the official harness — all 6 RESOLVED (F2P test_args 1/0, P2P 7/0, 0 failures). No impl with a closing clean-axiom proof has a faithful patch that fails to resolve. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_2_partial_none.lean`, `atk_3_partial_empty.lean`, `atk_8_echo_cond.lean`, `atk_10_partial_oversize.lean`, `atk_11_partial_rtl.lean`, `atk_12_partial_identity.lean` |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_4_boundary.lean`, `atk_5_rtl.lean`, `atk_6_ctrlflow.lean`, `atk_7_echo_naive.lean`, `atk_9_degenerate_some.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample found. The nearest thing to a residual weakness is the OFF-PRECONDITION region: the precondition `(∀ c ∈ cycles, c.Nodup)` leaves a rival free to do anything on a cycle-list where some SINGLE cycle repeats a point, e.g. cycles = [[0,0,1]] or [[0,1,2],[3,3]]. Six attacks (atk_2/3/10/11/12 partial-domain + atk_8 echo) exploit exactly that freedom, close with clean axioms, and their faithful refined patches were all materialized and RESOLVED (F2P 1/0, P2P 7/0). That region is NOT exploitable, because it is dead code in the real routine: Cycle.__init__ raises ValueError('All elements must be unique in a cycle.') (permutations.py:450-451) before the composition is ever reached, so the injected branch cannot be observed by any caller. Verified empirically in each patched worktree: in-domain all six agree with gold ([[0,1],[0,2]]->[1,2,0] the F2P input, [[1],[1,2]]->[0,2,1], [[1],[4,2]]->[0,1,4,3,2], [[],[0,1]]->[1,0]); off-domain they diverge (atk_2 RAISES / atk_3 [] / atk_12 [0,1] / atk_10 [0,0,2,3,4] / atk_11 [0,0] on [[0,0,1]]).
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_partial_none.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3_partial_empty.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4_boundary.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_rtl.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_ctrlflow.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_echo_naive.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_echo_cond.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9_degenerate_some.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_partial_oversize.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11_partial_rtl.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12_partial_identity.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building a permutation from a list of cycles given in cyclic notation.

A permutation on `{0, 1, …, n-1}` can be described by a list of cycles. Each
cycle is a list of distinct points `[a₀, a₁, …, a_{k-1}]` and denotes the rule
that sends `a₀ ↦ a₁ ↦ … ↦ a_{k-1} ↦ a₀`, leaving every other point unmoved.

When several cycles are supplied they are *composed in left-to-right order*: the
first cycle is applied first, then the second to that result, and so on. The
cycles need not move disjoint sets of points — a point may appear in more than
one cycle, in which case the successive rules simply chain through it. The size
of the resulting permutation is one more than the largest point named by any
cycle (so every point from `0` up to that maximum is listed), and the result is
returned in *array form*: the list whose `i`-th entry is the image of `i` under
the composed permutation.

A supplied-but-pointless list of cycles is the one degenerate case: if at least
one cycle is handed over yet no cycle names any point at all, the width of the
array form is not determined by the input and nothing is returned.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the action of a single
-- cycle and the left-to-right composition of several cycles are both spelled out
-- concretely (the `applyCycle` / `applyAll` helpers below), so there is nothing
-- to axiomatize — the modeled behavior is validated directly against the real
-- routine by the differential conformance check (an A-reference).
-- axioms-end

-- pure-start
/-- The image of `x` under a single cycle `c` listed as `[a₀, …, a_{k-1}]`:
if `x` occurs in `c` it is sent to the next entry cyclically (`a_{k-1} ↦ a₀`);
otherwise `x` is left unmoved. -/
def applyCycle (c : List Nat) (x : Nat) : Nat :=
  if c.contains x then c.getD ((c.idxOf x + 1) % c.length) x else x

/-- The image of `x` under the left-to-right composition of all `cycles`
(first cycle applied first). -/
def applyAll (cycles : List (List Nat)) (x : Nat) : Nat :=
  cycles.foldl (fun v c => applyCycle c v) x

/-- One past the largest point named by any cycle (`0` when no point is named).
This is the number of entries in the array form. -/
def permSize (cycles : List (List Nat)) : Nat :=
  cycles.flatten.foldl (fun m x => max m (x + 1)) 0

/-- The degenerate shape: at least one cycle was supplied, yet between them the
cycles name no point at all, so the array form has no determined width. -/
def sizeUndetermined (cycles : List (List Nat)) : Bool :=
  !cycles.isEmpty && permSize cycles == 0
-- pure-end

-- post-conditions-start
/-- Two legs, selected by whether the input determines a width.

* Degenerate leg (`sizeUndetermined cycles`): nothing is returned.
* Otherwise the construction succeeds (`result = some aform`) and `aform` is the
  array form of the left-to-right composition of `cycles`: it has
  `permSize cycles` entries (one per point from `0` to the maximum named), and
  its `i`-th entry is the image of `i` under the composed permutation. -/
def problem_spec_permFromCycles
    (cycles : List (List Nat)) (result : Option (List Nat)) : Prop :=
  (sizeUndetermined cycles = true → result = none) ∧
  (sizeUndetermined cycles = false →
    ∃ aform, result = some aform ∧
      aform.length = permSize cycles ∧
      (∀ i, i < permSize cycles → aform.getD i 0 = applyAll cycles i))
-- post-conditions-end

-- impl-start
def implementation_permFromCycles
    (cycles : List (List Nat)) : Option (List Nat) := Id.run do
  if sizeUndetermined cycles then
    return none
  let sz := permSize cycles
  let mut aform : List Nat := []
  for i in [0:sz] do
    let mut v := i
    for c in cycles do
      v := applyCycle c v
    aform := aform ++ [v]
  return some aform
-- impl-end

-- proof-start
theorem correct_permFromCycles :
    ∀ (cycles : List (List Nat)),
      (∀ c ∈ cycles, c.Nodup) →
      problem_spec_permFromCycles cycles
        (implementation_permFromCycles cycles) := by
  intro cycles hnd
  clear hnd
  have inner : ∀ i, (forIn cycles i fun c r => (pure (ForInStep.yield (applyCycle c r)) : Id _))
      = applyAll cycles i := by
    intro i
    unfold applyAll
    induction cycles generalizing i with
    | nil => rfl
    | cons c cs ih => simp only [List.forIn_cons, ih]; rfl
  constructor
  · intro hdeg
    unfold implementation_permFromCycles
    simp [hdeg]
  · intro hnon
    have key : implementation_permFromCycles cycles
        = some ((List.range (permSize cycles)).map (applyAll cycles)) := by
      unfold implementation_permFromCycles
      simp only [hnon, Bool.false_eq_true, if_false, Id.run, Std.Range.forIn_eq_forIn_range',
        bind_pure_comp, map_pure, Std.Range.size, Nat.sub_zero, Nat.add_sub_cancel, Nat.div_one]
      simp only [inner]
      have hfun : (fun (i : Nat) (r : List Nat) =>
          ((fun a => ForInStep.yield (r ++ [a])) <$> applyAll cycles i : Id _))
          = (fun (i : Nat) (r : List Nat) => (ForInStep.yield (r ++ [applyAll cycles i]) : Id _)) := rfl
      rw [hfun, List.forIn_yield_eq_foldl]
      rw [List.range_eq_range']
      generalize (permSize cycles) = sz
      have foldl_app : ∀ (len start : Nat) (acc : List Nat),
          (List.range' start len).foldl (fun r i => r ++ [applyAll cycles i]) acc
          = acc ++ (List.range' start len).map (applyAll cycles) := by
        intro len
        induction len with
        | zero => intro start acc; simp
        | succ n ih => intro start acc; rw [List.range'_succ]; simp only [List.foldl_cons, List.map_cons, ih]; simp
      rw [foldl_app]; simp; rfl
    rw [key]
    refine ⟨_, rfl, ?_, ?_⟩
    · simp
    · intro i hi
      rw [List.getD_eq_getElem?_getD, List.getElem?_map, List.getElem?_range hi]
      simp

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity, adversarial) — sympy__sympy-12481, lean backend.
NOTE ON PRIOR PASSES: the retained verdict.md G-EQ ledger is STALE — the impl it quotes has NO `sizeUndetermined` guard, whereas the current Solution.lean does. Every attack below was re-encoded and re-run from scratch against the CURRENT spec; nothing was carried over.

### COMMANDS (verbatim)
Lean:      bash scripts/lean_verify.sh <f>.lean     (run from swe-proof)
Axioms:    same command on ax_<f>.lean (= <f>.lean with `#print axioms correct_permFromCycles` inserted before -- proof-end)
Same-spec: swebench_unified.markers.same_spec(Solution.lean, atk, 'lean')  -> True for ALL 12 attacks + positive control
Resolve:   python resolve1.py <name>  -> swebench_unified.harness.run_resolve('sympy__sympy-12481', patch, retries=0); raw JSON in resolve_<name>.json
Integrity: all 13 files have same_spec=True, `correct_permFromCycles` STATEMENT byte-identical to gold, and zero evasions (no sorry / native_decide / axiom / implemented_by). No `axiom` is declared anywhere in Solution.lean.
Verifications were run 4-at-a-time as concurrent background jobs; schedule only, every attack fully verified.

### Positive control
pos_control.lean (bundle impl+proof verbatim): EXIT=0; axioms [propext, Classical.choice, Quot.sound]. CLEAN — non-vacuous.

#### PREPATCH REPRODUCED: True
atk_1_prepatch.lean — impl guards `if ¬ cycles.flatten.Nodup then return none` (the removed has_dups arm) + gold proof: EXIT=1, `rfl` fails at the `key` step (LHS retains the `if cycles.flatten.Nodup` scrutinee, not defeq to `some (...)`). Genuinely unprovable, not a tactic artifact. Independently, the bundle's own Solution_prepatch.lean exits 3 (sorry).

#### ATTACKS THAT DO NOT CLOSE — the spec correctly rejects them (6)
 1. atk_1_prepatch.lean          EXIT=1  full-domain rejection of shared points (THE prepatch bug)
 2. atk_4_boundary.lean          EXIT=1  loop over [0:sz-1]: last array-form entry dropped -> length conjunct catches it
 3. atk_5_rtl.lean               EXIT=1  `for c in cycles.reverse`: right-to-left composition -> applyAll's foldl order is pinned
 4. atk_6_ctrlflow.lean          EXIT=1  CONTROL-FLOW EFFECT: `break` after the first cycle, so only cycles[0] applies
 5. atk_7_echo_naive.lean        EXIT=1  oracle echo with NO degenerate guard: unsolved goal `⊢ False` from hdeg — the sizeUndetermined leg is load-bearing and cannot be skipped
 6. atk_9_degenerate_some.lean   EXIT=1  degenerate leg dropped (returns `some []` on a pointless cycle list): same `⊢ False`. Confirms the added guard is REQUIRED, i.e. the new leg is not decorative.

== ATTACKS THAT CLOSE WITH CLEAN AXIOMS (6) — every one materialized as a faithful patch and EXECUTED through run_resolve ==
 7. atk_2_partial_none.lean       EXIT=0 axioms [propext, Classical.choice, Quot.sound] -> patch_atk_2_partial_none.diff       resolved=True completed=True note=resolved  F2P 1/0  P2P 7/0
 8. atk_3_partial_empty.lean      EXIT=0 axioms [propext, Classical.choice, Quot.sound] -> patch_atk_3_partial_empty.diff      resolved=True completed=True  F2P 1/0  P2P 7/0
 9. atk_10_partial_oversize.lean  EXIT=0 axioms [propext, Classical.choice, Quot.sound] -> patch_atk_10_partial_oversize.diff  resolved=True completed=True  F2P 1/0  P2P 7/0
10. atk_11_partial_rtl.lean       EXIT=0 axioms [propext, Classical.choice, Quot.sound] -> patch_atk_11_partial_rtl.diff       resolved=True completed=True  F2P 1/0  P2P 7/0
11. atk_12_partial_identity.lean  EXIT=0 axioms [propext, Classical.choice, Quot.sound] -> patch_atk_12_partial_identity.diff  resolved=True completed=True  F2P 1/0  P2P 7/0
12. atk_8_echo_cond.lean          EXIT=0 axioms [propext]                               -> patch_atk_8_echo_cond.diff (= gold)  resolved=True completed=True  F2P 1/0  P2P 7/0
ZERO patches failed to resolve => verify⇏correct is NOT exhibited.

Attacks 7-11 are the partial-domain family: guard `if !(cycles.all fun c => decide c.Nodup) then return <junk>` ahead of the gold body, with junk = none / some [] / oversize (permSize+3 entries) / right-to-left composition / identity. Their faithful patches transcribe Lean's applyCycle/applyAll/permSize directly into the is_cycle block (the real Cycle.`__init__` cannot be used off-domain since it raises), gated on `any(has_dups(ci) for ci in args)`. NOTE (proof engineering, not a spec property): my first partial-domain proofs failed because putting `hall` in context before `have inner` blocks `induction cycles generalizing i`.

Restating `inner` as a standalone `∀ cs i` lemma fixed it — so this family closes and the honest result is that the free off-precondition region IS provably exploitable, just not test-observable. Off-domain divergence confirmed live, not vacuous (probe.py per worktree): on [[0,0,1]] gold RAISES 'All elements must be unique in a cycle.' while atk_2 RAISES the old cyclic message / atk_3 [] / atk_12 [0,1] / atk_10 [0,0,2,3,4] / atk_11 [0,0]; on [[0,1,2],[3,3]] atk_3 [] / atk_12 [0,1,2,3] / atk_10 [1,2,0,3,4,5,6] / atk_11 [1,2,0,3]. In-domain all six are byte-equal to gold on [[0,1],[0,2]], [[1],[1,2]], [[1],[4,2]], [[0,1],[0,1]], [[1,2]], [[0],[1]], [[3]], [[],[0,1]], and all agree with gold on the degenerate family ([[]], [[],[]] RAISE 'must give size for empty Cycle'; [] -> []).

### Why the spec is tight
problem_spec_permFromCycles pins the output TOTALLY on its domain: result = some aform AND aform.length = permSize AND (∀ i < permSize, aform.getD i 0 = applyAll cycles i). Length plus every in-range index are both fixed, so exactly ONE aform satisfies the success leg; the degenerate leg forces `none`. The only freedom left is the off-precondition region (a cycle with an INTERNAL duplicate), which is dead code in the real routine — Cycle.`__init__` raises before the composition (permutations.py:450-451, verified: Permutation([[0,0,1]]) and Permutation([[0,1,2],[3,3]]) both raise at base and post-patch). That is why all 6 off-domain rivals still resolve. Note the precondition is a per-cycle condition and says nothing about points shared BETWEEN cycles, so the sub-domain the patch actually opens ([[0,1],[0,2]]) stays fully constrained — which is what makes atk_1_prepatch fail to verify.

### REFINEMENT.MD AUDIT (the A legs)
Leg tags: 2 R, 1 I, 4 A-reference. NO kind-3 leg (no axiom consumed without validation); no `axiom` declared in Solution.lean (axioms region is prose only), so G-AX's skip stub is legitimate.
Row-by-row re-checked against  permutations.py @ c807dfe756:
  - `cycles: List (List Nat)` <-> `args = [[int(i) for i in c] for c in args]` (R). CONFIRMED: is_cycle = `args and is_sequence(args[0])` (line 884-887) — list-of-lists is exactly the modeled branch.
  - absence of a `none` early-return <-> the REMOVED `if has_dups(temp): if is_cycle: raise` arm (A-reference, THE edited op). CONFIRMED against patch.diff: post-patch reads `if has_dups(temp) and not is_cycle`.
  - `permSize cycles` <-> `Cycle.list()` width (A-reference). CONFIRMED: Cycle.list with size=None uses self.size = max(self.keys())+1 (455-459).
  - the `for i / for c in cycles` fold <-> `c = Cycle(); for ci in args: c = c(*ci); c.list()` (A-reference) — the SUBTLE leg. Cycle.`__call__` builds `rv = Cycle(*other)` then sets rv[k] = rv[self[k]] for k in self.keys(), i.e. self acts FIRST; iterating args left-to-right therefore makes the LEFTMOST cycle act first, matching foldl. HOLDS.
  - `sizeUndetermined cycles` <-> Cycle.list's `if not self and size is None: raise ValueError('must give size for empty Cycle')` (369-370) (A-reference). CONFIRMED, including the conditioning on a non-empty cycle list: Permutation([]) takes the array-form branch and yields [] rather than refusing.
  - `aform:= aform ++ [v]` <-> `[self[i] for i in range(size)]` (I); `return some aform` <-> `obj._array_form = aform` (R).
A-reference claims are MACHINE-backed, not prose. My own independent differential (axref.py, seeded 20240630, 4000 random cycle lists + 9 hand cases, run against the real Cycle): checked=3747 disagreements=0 on BOTH the value leg (aform[i] == applyAll) and the width leg (len(Cycle.list()) == permSize). The degenerate leg was validated separately (degref.py): [[]], [[],[]], [[],[],[]], [[],[],[],[]] all raise 'must give size for empty Cycle', and [] -> [].
One documented, non-exploitable imprecision: the Lean model is MORE defined than Python on internal-dup cycles (real raises) — the model is total there while the real routine refuses. That direction can only make the spec stricter on real inputs, never license wrong behavior, and the precondition is exactly the guard that fences it off; atk_2/3/10/11/12 show it is dead code in the refined patch. The previously-flagged [[]] gap is now CLOSED by the sizeUndetermined leg, and atk_7/atk_9 prove that leg is load-bearing (both fail to verify without it).

### Conclusion
12 attacks run (>= 5 required) across 7 distinct wrong-impl families: prepatch full-domain rejection, partial-domain x5 (none/empty/oversize/rtl/identity payloads), boundary off-by-one, right-to-left composition, control-flow (`break`) effect, degenerate-leg drop, and ungrounded-oracle echo x2. 6 fail to verify exactly as they should; 6 close with clean axioms (no sorryAx, no custom axiom) and EVERY one of those 6 had its faithful refined patch materialized and EXECUTED through the official harness — all 6 RESOLVED (F2P test_args 1/0, P2P 7/0, 0 failures). No impl with a closing clean-axiom proof has a faithful patch that fails to resolve. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Attempted to break faithfulness of problem_spec_permFromCycles against the REAL post-patch repo; found no divergence. Method and evidence:

**SETUP.** Base worktree at c807dfe756 copied from wt to a fresh mktemp dir; patch.diff applied cleanly (2 insertions / 6 deletions in sympy/combinatorics/permutations.py) to make the POST-PATCH tree the reference. Old sympy needed a collections.abc/inspect.getargspec compat shim under py3.10; imported and smoke-tested (Permutation([[0,1],[0,2]]).array_form == [1,2,0]).

### Mechanical gates
- scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
- Appended `#print axioms correct_permFromCycles` -> "depends on axioms: [propext, Classical.choice, Quot.sound]". No sorryAx; proof is real.
- swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, lean tables) -> True. Spec region byte-identical between the twins; the two differ only in impl-start (prepatch inserts `if not cycles.flatten.Nodup then return none`), so the discrimination is attributable to the patch delta alone.

INDEPENDENT DIFFERENTIAL (my own harness, not the bundle's conformance_check.py). I re-implemented the SPEC (not the impl) as a checker -- for each input it asks the real post-patch Permutation and then verifies the exact postcondition legs: sizeUndetermined => must decline; else must succeed AND len(array_form)==permSize AND array_form[i]==applyAll(cycles,i) for every i.
- 34,726 checks: exhaustive over all cycles of length 0-3 drawn from {0,1,2,3} as singletons AND all ordered pairs of them (so every non-disjointness pattern on a 4-point support), plus 30k random 0-5-cycle lists over pools up to 10, plus 3k sparse lists over points 0..39. 0 disagreements.
- 92,000 further checks across 4 independent seeds (11/22/33/44) with pools up to 30 points and up to 7 cycles, plus 8k long compositions (5-15 cycles) on a 4-point support to stress heavy non-disjointness, plus 4k sparse cases. 0 disagreements.

### Targeted attacks on the two suspicious spec choices
1. permSize as `flatten.foldl max` vs real `Cycle.size = max(keys)+1`. Cycle.`__call__` does `rv[self[k]]`, which invokes `__missing__` and CAN grow rv's key set -- I checked whether keys can exceed the max NAMED point. They cannot: self[k] is always itself a named point of self, so max(keys) <= max named point. Confirmed empirically by the exhaustive pair sweep and by [[500]] (length 501, identity) and [[9,0]] -> [9,1,...,8,0].
2. The sizeUndetermined leg -- the one place the spec could be accused of patch-delta drift. It is NOT: I ran the degenerate family on BOTH trees. base and post-patch both raise ValueError('must give size for empty Cycle') on [[]], [[],[]], [[],[],[]] (and I swept n=1..11 empties post-patch: all raise). Identical either side of the patch, so modelling it describes an UNCHANGED callee step (permutations.py:369-370), not the delta. The neighbouring case is correctly distinguished: Permutation([]) takes the array-form branch (is_cycle falsy) and returns [], and sizeUndetermined([]) = false, so the spec's success leg demands some [] -- which is what the real repo gives. The conditioning on `!cycles.isEmpty` is therefore load-bearing and right.

**PRECONDITION SOUNDNESS.** The `forall c in cycles, c.Nodup` hypothesis mirrors a real guard rather than hiding a hole: Cycle.`__init__` raises ValueError('All elements must be unique in a cycle.') on within-cycle repeats -- verified on [[0,1,0]], [[1,1]], [[0,1],[2,2]], [[0,0]], all RAISE. So excluded inputs never reach the composition. Crucially the precondition is per-cycle and says nothing about points shared BETWEEN cycles, so the sub-domain the patch opens stays inside the modeled domain (that is where the spec must and does bite). Note the proof `clear`s hnd, i.e. the impl meets the spec even without it -- a superset claim, not a weakening. Nat is sound: Cycle.`__init__` rejects negatives (permutations.py:448-449).

COMPOSITION DIRECTION IS DISCRIMINATING, NOT ACCIDENTALLY SYMMETRIC. I checked left-to-right vs right-to-left give DIFFERENT answers on the relevant inputs and that the real repo matches L-to-R only: [[0,1],[0,2]] real [1,2,0] (LtoR [1,2,0], RtoL [2,0,1]); [[0,1],[1,2]] real [2,0,1] (RtoL [1,2,0]); [[0,1,2],[1,3]] real [3,2,0,1] (RtoL [1,3,0,2]). So applyAll's fold order is pinned by observation, not vacuously satisfied.

**PREPATCH TWIN ALSO VALIDATED.** To confirm the discriminating clause is the real removed guard and not an invented one, I ran the prepatch model (flatten-Nodup rejection ahead of the degenerate guard) against the BASE tree: 20,000 randomized checks, 0 disagreements. Base rejects [[0,1],[0,2]] with 'there were repeated elements; to resolve cycles use Cycle(0,...' exactly as modeled.

**CONCLUSION.** No input in the modeled domain was found where the spec disagrees with the post-patch repo, across ~147k differential checks plus exhaustive small-support coverage and hand-built adversarial cases. Both postcondition legs are observation-pinned and the success leg fully determines the output list. The one leg that could look like drift (sizeUndetermined) is provably patch-invariant. Verdict FAITHFUL; no diverging input to report.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** NO RELAXATION PRESENT, so this is a plain leakage review, not an inherited disposition. I checked directly: `find` over the whole instance dir for '*RELAX*' -> no matches; meta.json top-level keys are [axioms, conf_skip, deep_model_references, gates, modeled_functions, opaque_callees, patch_equals_gold, pbt_audit, prepatch_variants, region_hashes, schema_version, spec_provenance, verifier_pins] -- no `relaxed_leakage`. A recursive walk of meta.json for any key matching /relax|leak/i returns only gates/G-LEAK. So there is no unavoidability argument to re-derive; I judged the shipped bytes de novo.

**NOTHING IN THE BUNDLE ADDRESSES ME.** Grepped the lean bundle (Solution.lean, Solution_prepatch.lean, mapping.md, refinement.md, conformance_check.py, properties.py, axiom_check.py) for attacker|panel|reviewer|auditor|'verdict string'|'honest verdict'|'submit NO-LEAKAGE'|'you should/must' -> zero hits. Hits elsewhere under the instance dir are meta.json's own machine-generated gate keys and, in the SIBLING velvet/verdict.md, other roles' self-reports of their own no-directive checks -- neither is a directive to me. No file tried to tell me what to submit.

### WHAT I MEASURED (computed myself, not read from the bundle):
- spec_view via swebench_unified.markers.spec_view(Solution.lean, LeanBackend()): elides impl and proof entirely. Consumer-visible content = module docstring + axioms comment + `pure` region (applyCycle/applyAll/permSize/sizeUndetermined) + problem_spec_permFromCycles.
- markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend()) = True. The spec region is byte-identical (by signature) across both legs, so a consumer reading the spec cannot tell the gold leg from the pre-patch leg. Requested check confirmed.
- leakage.screen(src, LeanBackend(), instance['patch'], instance['problem_statement']) on BOTH files -> LeakageReport(hard_failures=[], warnings=[]). Note the 'PRE-PATCH (buggy)' narration in Solution_prepatch.lean sits inside the impl region and is elided by spec_view, so it is not consumer-visible.
- Token screen over the lowercased spec view: has_dups, is_cycle, ValueError, raise, permutations.py, patch, fix, bug, 'no longer', previously, 'repeated element', reject, identity, sympy, Cycle.list -> ALL ABSENT. Only hits are 'disjoint', 'left-to-right' (both verbatim public, below) and 'diff' inside 'differential conformance check'.
- G-VERIFY replicated: scripts/lean_verify.sh Solution.lean -> exit 0 (only a deprecation warning). `#print axioms correct_permFromCycles` -> [propext, Classical.choice, Quot.sound]; NO sorryAx, so the proof is real.
- G-DIFF replicated and strengthened: lean_verify.sh Solution_prepatch.lean -> exit 3 ('declaration uses sorry'), which alone is weak evidence, so I built the discrimination myself: with the prepatch impl, `theorem prepatch_violates_spec: ¬ problem_spec_permFromCycles [[0,1],[0,2]] (implementation_permFromCycles [[0,1],[0,2]])` compiles, exit 0, axioms [propext, Quot.sound] -- no sorryAx. The spec genuinely rejects the pre-patch impl.

PROBLEM_STATEMENT COVERAGE (the substantive check). problem_statement is public and says: 'Calling Permutation([[0,1],[0,1]]) raises a ValueError instead of constructing the identity permutation. If the cycles passed in are non-disjoint, they should be applied in left-to-right order and the resulting permutation should be returned... I don't see a reason why non-disjoint cycles should be forbidden.' Mapping every discriminator-bearing spec-view clause to it: 'composed in left-to-right order' <- 'applied in left-to-right order'; 'cycles need not move disjoint sets of points' <- 'If the cycles passed in are non-disjoint'; success returns the composed permutation <- 'the resulting permutation should be returned'. The discriminating input is itself public (statement names [[0,1],[0,1]]).

I confirmed the discriminator is exactly the patch delta by running both real trees (base  @ c807dfe756 vs a fresh copy with patch.diff applied, PYTHONPATH-loaded): [[0,1],[0,2]] base -> ValueError 'there were repeated elements; to resolve cycles use Cycle(0, 1)(0, 2).', patched -> [1,2,0]; [[0,1],[0,1]] base -> same ValueError, patched -> [0,1] (the identity the statement asked for). So disclosing 'non-disjoint cycles compose successfully' discloses only what the issue reporter already demanded, and the spec never names the mechanism (the removed has_dups/is_cycle arm), the file, or the diff.

THE ONE CLAUSE NOT IN THE STATEMENT, and why it is not a leak: the degenerate leg ('if at least one cycle is handed over yet no cycle names any point at all... nothing is returned' / sizeUndetermined). I verified on the real trees that this is EDIT-NEUTRAL: [[]] and [[],[]] raise ValueError 'must give size for empty Cycle' IDENTICALLY at base and post-patch. It comes from Cycle.list (permutations.py:369-370), a callee the patch does not touch, so it carries zero information about the gold edit -- a consumer who reads it learns an unchanged callee refusal, not the discriminator. It is a faithfulness repair (it answers the prior G-PANEL-2 over-strength finding at [[]]), and because it is present in BOTH legs it cannot discriminate them (consistent with same_spec = True). Array-form/size conventions are likewise edit-neutral background.

STALE-STAMP FLAGS (recorded for the record, not leakage findings, and I did not inherit any of them): (1) meta.json's region_hashes block is stale w.r.t. the shipped bytes -- meta spec_view 390efa25... vs my computed 13c61ab1..., and pure/post-conditions/impl/proof all differ; only `axioms` matches. (2) The prior G-PANEL-1/-2/-3 records are stamped against Solution.lean = 88fb60ab..., and G-EQ against the same, whereas the shipped file is 1b039572...; so the prior G-PANEL-3 'pass' and the G-PANEL-2 'fail' both judge an artifact that is gone. The gates stamped against the CURRENT hash 1b039572 (G-AX skip, G-CONF, G-DIFF, G-GOLD, G-HYGIENE, G-INTEGRITY, G-LEAK, G-MUT, G-PBT, G-VERIFY) all pass, and G-LEAK's own source hash matches the shipped file. My verdict rests on my own re-measurement of the shipped bytes, not on those records; the panel/G-EQ/region_hashes stamps should be refreshed before the cell's overall disposition is trusted.

**VERDICT:** NO-LEAKAGE. The spec view discloses only left-to-right composition, tolerance of non-disjoint cycles, and success-returns-the-permutation -- each verbatim public in problem_statement -- plus edit-neutral array-form/size conventions and an edit-neutral empty-Cycle refusal I confirmed identical at base and post-patch. It names neither the removed has_dups/is_cycle guard, nor the ValueError, nor the file, nor any diff artifact, and the two legs present identical spec signatures.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
