# P2 adversarial audit — scikit-learn__scikit-learn-9288

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_prepatch.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation admits a closing clean-axiom proof, so there is no faithful patch to materialize or resolve-run. verify=>correct holds on the modeled surface.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,174 +63,24 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_bestTrial (trials : List Int) : Outcome := Id.run do
-  let mut best : Option Outcome := none
-  for t in trials do
-    let o := runTrial t
-    match best with
-    | none   => best := some o
-    | some b => if o.cost < b.cost then best := some o
-  return best.getD default
+def implementation_bestTrial (trials : List Int) : Outcome :=
+  match trials with
+  | []      => default
+  | t :: _  => runTrial t
 -- impl-end
 
-
 -- proof-start
-/-- Pure extraction of the loop body's effect on `best`: fold accumulator update. -/
-def step (b : Option Outcome) (t : Int) : Option Outcome :=
-  match b with
-  | none   => some (runTrial t)
-  | some o => if (runTrial t).cost < o.cost then some (runTrial t) else b
-
-/-- Loop invariant carrying the earliest-minimum-cost witness through the fold:
-(a) empty prefix ⇒ accumulator is `none`;
-(b) nonempty prefix ⇒ the accumulator is `some` of the outcome of the earliest
-    minimum-cost trial among the processed prefix. -/
-def FoldInv (processed : List Int) (b : Option Outcome) : Prop :=
-  (processed = [] → b = none) ∧
-  (processed ≠ [] → ∃ i : Fin processed.length,
-      b = some (runTrial (processed.get i)) ∧
-      (∀ j : Fin processed.length,
-          (runTrial (processed.get i)).cost ≤ (runTrial (processed.get j)).cost) ∧
-      (∀ j : Fin processed.length, j.val < i.val →
-          (runTrial (processed.get i)).cost < (runTrial (processed.get j)).cost))
-
-theorem getD_some (x : Outcome) : (some x).getD default = x := rfl
-
-theorem impl_eq_foldl (trials : List Int) :
-    implementation_bestTrial trials = (trials.foldl step none).getD default := by
-  simp only [implementation_bestTrial, Id.run, bind_pure_comp, map_pure]
-  suffices h : ∀ (init : Option Outcome),
-      (forIn trials init fun t r =>
-        (match r with
-        | none => (pure (ForInStep.yield (some (runTrial t))) : Id (ForInStep (Option Outcome)))
-        | some b => if (runTrial t).cost < b.cost then pure (ForInStep.yield (some (runTrial t))) else pure (ForInStep.yield r))) = List.foldl step init trials by
-    rw [h none]; rfl
-  induction trials with
-  | nil => intro init; rfl
-  | cons h t ih =>
-    intro init
-    rw [List.forIn_cons, List.foldl_cons]
-    cases init with
-    | none => simp only [pure_bind, step]; rw [ih]
-    | some b =>
-      by_cases hc : (runTrial h).cost < b.cost
-      · simp only [pure_bind, step, hc, if_true]; rw [ih]
-      · simp only [pure_bind, step, hc, if_false]; rw [ih]
-
-theorem FoldInv_init : FoldInv [] none := by
-  constructor
-  · intro _; rfl
-  · intro h; exact absurd rfl h
-
-theorem FoldInv_step (P : List Int) (t : Int) (b : Option Outcome) :
-    FoldInv P b → FoldInv (P ++ [t]) (step b t) := by
-  intro hInv
-  refine ⟨fun hEmpty => absurd hEmpty (by simp), fun _ => ?_⟩
-  by_cases hP : P = []
-  · -- Empty prefix: b = none, so step none t = some (runTrial t)
-    subst hP
-    have hb : b = none := hInv.1 rfl
-    subst hb
-    simp only [step, List.nil_append]
-    refine ⟨⟨0, by simp⟩, ?_, ?_, ?_⟩
-    · simp
-    · intro j
-      simp only [List.get_eq_getElem]
-      have hj0 : (j : ℕ) = 0 := by
-        have := j.isLt; simp only [List.length_cons, List.length_nil] at this; omega
-      simp only [hj0]
-      exact le_refl _
-    · intro j hj
-      exact absurd hj (Nat.not_lt_zero _)
-  · -- Nonempty prefix
-    obtain ⟨i, hb, hmin, hearl⟩ := hInv.2 hP
-    simp only [List.get_eq_getElem] at hb hmin hearl
-    have hi := i.isLt
-    have hilt : i.val < (P ++ [t]).length := by
-      simp only [List.length_append, List.length_cons, List.length_nil]; omega
-    by_cases hcase : (runTrial t).cost < (runTrial P[i.val]).cost
-    · -- new trial wins; best becomes some (runTrial t), witness = last index
-      have hstep : step b t = some (runTrial t) := by
-        rw [hb]; simp only [step, if_pos hcase]
-      rw [hstep]
-      refine ⟨⟨P.length, by simp⟩, ?_, ?_, ?_⟩
-      · simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-      · intro j
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-        by_cases hj : j.val < P.length
-        · rw [List.getElem_append_left hj]
-          have hm := hmin ⟨j.val, hj⟩
-          exact le_of_lt (lt_of_lt_of_le hcase hm)
-        · have hjeq : j.val = P.length := by
-            have hjl := j.isLt
-            simp only [List.length_append, List.length_cons, List.length_nil] at hjl
-            omega
-          rw [List.getElem_concat_length (l := P) (a := t) hjeq]
-      · intro j hj
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-        rw [List.getElem_append_left hj]
-        have hm := hmin ⟨j.val, hj⟩
-        exact lt_of_lt_of_le hcase hm
-    · -- old best wins; accumulator unchanged, witness = i
-      push_neg at hcase
-      have hstep : step b t = b := by
-        rw [hb]; simp only [step, if_neg (not_lt.mpr hcase)]
-      rw [hstep, hb]
-      refine ⟨⟨i.val, hilt⟩, ?_, ?_, ?_⟩
-      · simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-      · intro j
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-        by_cases hj : j.val < P.length
-        · rw [List.getElem_append_left hj]
-          exact hmin ⟨j.val, hj⟩
-        · have hjeq : j.val = P.length := by
-            have hjl := j.isLt
-            simp only [List.length_append, List.length_cons, List.length_nil] at hjl
-            omega
-          rw [List.getElem_concat_length (l := P) (a := t) hjeq]
-          exact hcase
-      · intro j hj
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-        have hjP : j.val < P.length := lt_trans hj hi
-        rw [List.getElem_append_left hjP]
-        exact hearl ⟨j.val, hjP⟩ hj
-
-theorem FoldInv_holds (L : List Int) : FoldInv L (L.foldl step none) := by
-  induction L using List.reverseRecOn with
-  | nil => exact FoldInv_init
-  | append_singleton P t IH =>
-    rw [List.foldl_concat]
-    exact FoldInv_step P t (P.foldl step none) IH
-
-theorem nonempty_gives_some (trials : List Int) (h : trials ≠ []) :
-    ∃ iBest : Fin trials.length,
-      (trials.foldl step none) = some (runTrial (trials.get iBest)) ∧
-      (∀ j : Fin trials.length,
-          (runTrial (trials.get iBest)).cost ≤ (runTrial (trials.get j)).cost) ∧
-      (∀ j : Fin trials.length, j.val < iBest.val →
-          (runTrial (trials.get iBest)).cost < (runTrial (trials.get j)).cost) :=
-  (FoldInv_holds trials).2 h
-
-theorem result_is_trial_i (trials : List Int) (iBest : Fin trials.length)
-    (hfold : (trials.foldl step none) = some (runTrial (trials.get iBest))) :
-    implementation_bestTrial trials = runTrial (trials.get iBest) := by
-  rw [impl_eq_foldl, hfold, getD_some]
-
 theorem correct_bestTrial :
     ∀ (trials : List Int), trials ≠ [] →
       problem_spec_bestTrial trials (implementation_bestTrial trials) := by
   intro trials h
-  obtain ⟨iBest, hfold, hmin, hbefore⟩ := nonempty_gives_some trials h
-  have hres := result_is_trial_i trials iBest hfold
-  refine ⟨iBest, ?_, ?_, ?_⟩
-  · exact hres
-  · intro j; rw [hres]; exact hmin j
-  · intro j hj; rw [hres]; exact hbefore j hj
-
+  cases trials with
+  | nil => exact absurd rfl h
+  | cons a t =>
+    refine ⟨⟨0, by simp⟩, ?_, ?_, ?_⟩
+    · simp [implementation_bestTrial]
+    · intro j
+      simp only [implementation_bestTrial]
+      sorry
+    · intro j hj; exact absurd hj (Nat.not_lt_zero _)
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,174 +63,14 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_bestTrial (trials : List Int) : Outcome := Id.run do
-  let mut best : Option Outcome := none
-  for t in trials do
-    let o := runTrial t
-    match best with
-    | none   => best := some o
-    | some b => if o.cost < b.cost then best := some o
-  return best.getD default
+def implementation_bestTrial (trials : List Int) : Outcome :=
+  (trials.reverse.head?.map runTrial).getD default
 -- impl-end
 
-
 -- proof-start
-/-- Pure extraction of the loop body's effect on `best`: fold accumulator update. -/
-def step (b : Option Outcome) (t : Int) : Option Outcome :=
-  match b with
-  | none   => some (runTrial t)
-  | some o => if (runTrial t).cost < o.cost then some (runTrial t) else b
-
-/-- Loop invariant carrying the earliest-minimum-cost witness through the fold:
-(a) empty prefix ⇒ accumulator is `none`;
-(b) nonempty prefix ⇒ the accumulator is `some` of the outcome of the earliest
-    minimum-cost trial among the processed prefix. -/
-def FoldInv (processed : List Int) (b : Option Outcome) : Prop :=
-  (processed = [] → b = none) ∧
-  (processed ≠ [] → ∃ i : Fin processed.length,
-      b = some (runTrial (processed.get i)) ∧
-      (∀ j : Fin processed.length,
-          (runTrial (processed.get i)).cost ≤ (runTrial (processed.get j)).cost) ∧
-      (∀ j : Fin processed.length, j.val < i.val →
-          (runTrial (processed.get i)).cost < (runTrial (processed.get j)).cost))
-
-theorem getD_some (x : Outcome) : (some x).getD default = x := rfl
-
-theorem impl_eq_foldl (trials : List Int) :
-    implementation_bestTrial trials = (trials.foldl step none).getD default := by
-  simp only [implementation_bestTrial, Id.run, bind_pure_comp, map_pure]
-  suffices h : ∀ (init : Option Outcome),
-      (forIn trials init fun t r =>
-        (match r with
-        | none => (pure (ForInStep.yield (some (runTrial t))) : Id (ForInStep (Option Outcome)))
-        | some b => if (runTrial t).cost < b.cost then pure (ForInStep.yield (some (runTrial t))) else pure (ForInStep.yield r))) = List.foldl step init trials by
-    rw [h none]; rfl
-  induction trials with
-  | nil => intro init; rfl
-  | cons h t ih =>
-    intro init
-    rw [List.forIn_cons, List.foldl_cons]
-    cases init with
-    | none => simp only [pure_bind, step]; rw [ih]
-    | some b =>
-      by_cases hc : (runTrial h).cost < b.cost
-      · simp only [pure_bind, step, hc, if_true]; rw [ih]
-      · simp only [pure_bind, step, hc, if_false]; rw [ih]
-
-theorem FoldInv_init : FoldInv [] none := by
-  constructor
-  · intro _; rfl
-  · intro h; exact absurd rfl h
-
-theorem FoldInv_step (P : List Int) (t : Int) (b : Option Outcome) :
-    FoldInv P b → FoldInv (P ++ [t]) (step b t) := by
-  intro hInv
-  refine ⟨fun hEmpty => absurd hEmpty (by simp), fun _ => ?_⟩
-  by_cases hP : P = []
-  · -- Empty prefix: b = none, so step none t = some (runTrial t)
-    subst hP
-    have hb : b = none := hInv.1 rfl
-    subst hb
-    simp only [step, List.nil_append]
-    refine ⟨⟨0, by simp⟩, ?_, ?_, ?_⟩
-    · simp
-    · intro j
-      simp only [List.get_eq_getElem]
-      have hj0 : (j : ℕ) = 0 := by
-        have := j.isLt; simp only [List.length_cons, List.length_nil] at this; omega
-      simp only [hj0]
-      exact le_refl _
-    · intro j hj
-      exact absurd hj (Nat.not_lt_zero _)
-  · -- Nonempty prefix
-    obtain ⟨i, hb, hmin, hearl⟩ := hInv.2 hP
-    simp only [List.get_eq_getElem] at hb hmin hearl
-    have hi := i.isLt
-    have hilt : i.val < (P ++ [t]).length := by
-      simp only [List.length_append, List.length_cons, List.length_nil]; omega
-    by_cases hcase : (runTrial t).cost < (runTrial P[i.val]).cost
-    · -- new trial wins; best becomes some (runTrial t), witness = last index
-      have hstep : step b t = some (runTrial t) := by
-        rw [hb]; simp only [step, if_pos hcase]
-      rw [hstep]
-      refine ⟨⟨P.length, by simp⟩, ?_, ?_, ?_⟩
-      · simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-      · intro j
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-        by_cases hj : j.val < P.length
-        · rw [List.getElem_append_left hj]
-          have hm := hmin ⟨j.val, hj⟩
-          exact le_of_lt (lt_of_lt_of_le hcase hm)
-        · have hjeq : j.val = P.length := by
-            have hjl := j.isLt
-            simp only [List.length_append, List.length_cons, List.length_nil] at hjl
-            omega
-          rw [List.getElem_concat_length (l := P) (a := t) hjeq]
-      · intro j hj
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-        rw [List.getElem_append_left hj]
-        have hm := hmin ⟨j.val, hj⟩
-        exact lt_of_lt_of_le hcase hm
-    · -- old best wins; accumulator unchanged, witness = i
-      push_neg at hcase
-      have hstep : step b t = b := by
-        rw [hb]; simp only [step, if_neg (not_lt.mpr hcase)]
-      rw [hstep, hb]
-      refine ⟨⟨i.val, hilt⟩, ?_, ?_, ?_⟩
-      · simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-      · intro j
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-        by_cases hj : j.val < P.length
-        · rw [List.getElem_append_left hj]
-          exact hmin ⟨j.val, hj⟩
-        · have hjeq : j.val = P.length := by
-            have hjl := j.isLt
-            simp only [List.length_append, List.length_cons, List.length_nil] at hjl
-            omega
-          rw [List.getElem_concat_length (l := P) (a := t) hjeq]
-          exact hcase
-      · intro j hj
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-        have hjP : j.val < P.length := lt_trans hj hi
-        rw [List.getElem_append_left hjP]
-        exact hearl ⟨j.val, hjP⟩ hj
-
-theorem FoldInv_holds (L : List Int) : FoldInv L (L.foldl step none) := by
-  induction L using List.reverseRecOn with
-  | nil => exact FoldInv_init
-  | append_singleton P t IH =>
-    rw [List.foldl_concat]
-    exact FoldInv_step P t (P.foldl step none) IH
-
-theorem nonempty_gives_some (trials : List Int) (h : trials ≠ []) :
-    ∃ iBest : Fin trials.length,
-      (trials.foldl step none) = some (runTrial (trials.get iBest)) ∧
-      (∀ j : Fin trials.length,
-          (runTrial (trials.get iBest)).cost ≤ (runTrial (trials.get j)).cost) ∧
-      (∀ j : Fin trials.length, j.val < iBest.val →
-          (runTrial (trials.get iBest)).cost < (runTrial (trials.get j)).cost) :=
-  (FoldInv_holds trials).2 h
-
-theorem result_is_trial_i (trials : List Int) (iBest : Fin trials.length)
-    (hfold : (trials.foldl step none) = some (runTrial (trials.get iBest))) :
-    implementation_bestTrial trials = runTrial (trials.get iBest) := by
-  rw [impl_eq_foldl, hfold, getD_some]
-
 theorem correct_bestTrial :
     ∀ (trials : List Int), trials ≠ [] →
       problem_spec_bestTrial trials (implementation_bestTrial trials) := by
   intro trials h
-  obtain ⟨iBest, hfold, hmin, hbefore⟩ := nonempty_gives_some trials h
-  have hres := result_is_trial_i trials iBest hfold
-  refine ⟨iBest, ?_, ?_, ?_⟩
-  · exact hres
-  · intro j; rw [hres]; exact hmin j
-  · intro j hj; rw [hres]; exact hbefore j hj
-
+  sorry
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,168 +69,14 @@
     let o := runTrial t
     match best with
     | none   => best := some o
-    | some b => if o.cost < b.cost then best := some o
+    | some b => if o.cost > b.cost then best := some o
   return best.getD default
 -- impl-end
 
-
 -- proof-start
-/-- Pure extraction of the loop body's effect on `best`: fold accumulator update. -/
-def step (b : Option Outcome) (t : Int) : Option Outcome :=
-  match b with
-  | none   => some (runTrial t)
-  | some o => if (runTrial t).cost < o.cost then some (runTrial t) else b
-
-/-- Loop invariant carrying the earliest-minimum-cost witness through the fold:
-(a) empty prefix ⇒ accumulator is `none`;
-(b) nonempty prefix ⇒ the accumulator is `some` of the outcome of the earliest
-    minimum-cost trial among the processed prefix. -/
-def FoldInv (processed : List Int) (b : Option Outcome) : Prop :=
-  (processed = [] → b = none) ∧
-  (processed ≠ [] → ∃ i : Fin processed.length,
-      b = some (runTrial (processed.get i)) ∧
-      (∀ j : Fin processed.length,
-          (runTrial (processed.get i)).cost ≤ (runTrial (processed.get j)).cost) ∧
-      (∀ j : Fin processed.length, j.val < i.val →
-          (runTrial (processed.get i)).cost < (runTrial (processed.get j)).cost))
-
-theorem getD_some (x : Outcome) : (some x).getD default = x := rfl
-
-theorem impl_eq_foldl (trials : List Int) :
-    implementation_bestTrial trials = (trials.foldl step none).getD default := by
-  simp only [implementation_bestTrial, Id.run, bind_pure_comp, map_pure]
-  suffices h : ∀ (init : Option Outcome),
-      (forIn trials init fun t r =>
-        (match r with
-        | none => (pure (ForInStep.yield (some (runTrial t))) : Id (ForInStep (Option Outcome)))
-        | some b => if (runTrial t).cost < b.cost then pure (ForInStep.yield (some (runTrial t))) else pure (ForInStep.yield r))) = List.foldl step init trials by
-    rw [h none]; rfl
-  induction trials with
-  | nil => intro init; rfl
-  | cons h t ih =>
-    intro init
-    rw [List.forIn_cons, List.foldl_cons]
-    cases init with
-    | none => simp only [pure_bind, step]; rw [ih]
-    | some b =>
-      by_cases hc : (runTrial h).cost < b.cost
-      · simp only [pure_bind, step, hc, if_true]; rw [ih]
-      · simp only [pure_bind, step, hc, if_false]; rw [ih]
-
-theorem FoldInv_init : FoldInv [] none := by
-  constructor
-  · intro _; rfl
-  · intro h; exact absurd rfl h
-
-theorem FoldInv_step (P : List Int) (t : Int) (b : Option Outcome) :
-    FoldInv P b → FoldInv (P ++ [t]) (step b t) := by
-  intro hInv
-  refine ⟨fun hEmpty => absurd hEmpty (by simp), fun _ => ?_⟩
-  by_cases hP : P = []
-  · -- Empty prefix: b = none, so step none t = some (runTrial t)
-    subst hP
-    have hb : b = none := hInv.1 rfl
-    subst hb
-    simp only [step, List.nil_append]
-    refine ⟨⟨0, by simp⟩, ?_, ?_, ?_⟩
-    · simp
-    · intro j
-      simp only [List.get_eq_getElem]
-      have hj0 : (j : ℕ) = 0 := by
-        have := j.isLt; simp only [List.length_cons, List.length_nil] at this; omega
-      simp only [hj0]
-      exact le_refl _
-    · intro j hj
-      exact absurd hj (Nat.not_lt_zero _)
-  · -- Nonempty prefix
-    obtain ⟨i, hb, hmin, hearl⟩ := hInv.2 hP
-    simp only [List.get_eq_getElem] at hb hmin hearl
-    have hi := i.isLt
-    have hilt : i.val < (P ++ [t]).length := by
-      simp only [List.length_append, List.length_cons, List.length_nil]; omega
-    by_cases hcase : (runTrial t).cost < (runTrial P[i.val]).cost
-    · -- new trial wins; best becomes some (runTrial t), witness = last index
-      have hstep : step b t = some (runTrial t) := by
-        rw [hb]; simp only [step, if_pos hcase]
-      rw [hstep]
-      refine ⟨⟨P.length, by simp⟩, ?_, ?_, ?_⟩
-      · simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-      · intro j
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-        by_cases hj : j.val < P.length
-        · rw [List.getElem_append_left hj]
-          have hm := hmin ⟨j.val, hj⟩
-          exact le_of_lt (lt_of_lt_of_le hcase hm)
-        · have hjeq : j.val = P.length := by
-            have hjl := j.isLt
-            simp only [List.length_append, List.length_cons, List.length_nil] at hjl
-            omega
-          rw [List.getElem_concat_length (l := P) (a := t) hjeq]
-      · intro j hj
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-        rw [List.getElem_append_left hj]
-        have hm := hmin ⟨j.val, hj⟩
-        exact lt_of_lt_of_le hcase hm
-    · -- old best wins; accumulator unchanged, witness = i
-      push_neg at hcase
-      have hstep : step b t = b := by
-        rw [hb]; simp only [step, if_neg (not_lt.mpr hcase)]
-      rw [hstep, hb]
-      refine ⟨⟨i.val, hilt⟩, ?_, ?_, ?_⟩
-      · simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-      · intro j
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-        by_cases hj : j.val < P.length
-        · rw [List.getElem_append_left hj]
-          exact hmin ⟨j.val, hj⟩
-        · have hjeq : j.val = P.length := by
-            have hjl := j.isLt
-            simp only [List.length_append, List.length_cons, List.length_nil] at hjl
-            omega
-          rw [List.getElem_concat_length (l := P) (a := t) hjeq]
-          exact hcase
-      · intro j hj
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-        have hjP : j.val < P.length := lt_trans hj hi
-        rw [List.getElem_append_left hjP]
-        exact hearl ⟨j.val, hjP⟩ hj
-
-theorem FoldInv_holds (L : List Int) : FoldInv L (L.foldl step none) := by
-  induction L using List.reverseRecOn with
-  | nil => exact FoldInv_init
-  | append_singleton P t IH =>
-    rw [List.foldl_concat]
-    exact FoldInv_step P t (P.foldl step none) IH
-
-theorem nonempty_gives_some (trials : List Int) (h : trials ≠ []) :
-    ∃ iBest : Fin trials.length,
-      (trials.foldl step none) = some (runTrial (trials.get iBest)) ∧
-      (∀ j : Fin trials.length,
-          (runTrial (trials.get iBest)).cost ≤ (runTrial (trials.get j)).cost) ∧
-      (∀ j : Fin trials.length, j.val < iBest.val →
-          (runTrial (trials.get iBest)).cost < (runTrial (trials.get j)).cost) :=
-  (FoldInv_holds trials).2 h
-
-theorem result_is_trial_i (trials : List Int) (iBest : Fin trials.length)
-    (hfold : (trials.foldl step none) = some (runTrial (trials.get iBest))) :
-    implementation_bestTrial trials = runTrial (trials.get iBest) := by
-  rw [impl_eq_foldl, hfold, getD_some]
-
 theorem correct_bestTrial :
     ∀ (trials : List Int), trials ≠ [] →
       problem_spec_bestTrial trials (implementation_bestTrial trials) := by
   intro trials h
-  obtain ⟨iBest, hfold, hmin, hbefore⟩ := nonempty_gives_some trials h
-  have hres := result_is_trial_i trials iBest hfold
-  refine ⟨iBest, ?_, ?_, ?_⟩
-  · exact hres
-  · intro j; rw [hres]; exact hmin j
-  · intro j hj; rw [hres]; exact hbefore j hj
-
+  sorry
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,168 +69,14 @@
     let o := runTrial t
     match best with
     | none   => best := some o
-    | some b => if o.cost < b.cost then best := some o
+    | some b => if o.cost ≤ b.cost then best := some o
   return best.getD default
 -- impl-end
 
-
 -- proof-start
-/-- Pure extraction of the loop body's effect on `best`: fold accumulator update. -/
-def step (b : Option Outcome) (t : Int) : Option Outcome :=
-  match b with
-  | none   => some (runTrial t)
-  | some o => if (runTrial t).cost < o.cost then some (runTrial t) else b
-
-/-- Loop invariant carrying the earliest-minimum-cost witness through the fold:
-(a) empty prefix ⇒ accumulator is `none`;
-(b) nonempty prefix ⇒ the accumulator is `some` of the outcome of the earliest
-    minimum-cost trial among the processed prefix. -/
-def FoldInv (processed : List Int) (b : Option Outcome) : Prop :=
-  (processed = [] → b = none) ∧
-  (processed ≠ [] → ∃ i : Fin processed.length,
-      b = some (runTrial (processed.get i)) ∧
-      (∀ j : Fin processed.length,
-          (runTrial (processed.get i)).cost ≤ (runTrial (processed.get j)).cost) ∧
-      (∀ j : Fin processed.length, j.val < i.val →
-          (runTrial (processed.get i)).cost < (runTrial (processed.get j)).cost))
-
-theorem getD_some (x : Outcome) : (some x).getD default = x := rfl
-
-theorem impl_eq_foldl (trials : List Int) :
-    implementation_bestTrial trials = (trials.foldl step none).getD default := by
-  simp only [implementation_bestTrial, Id.run, bind_pure_comp, map_pure]
-  suffices h : ∀ (init : Option Outcome),
-      (forIn trials init fun t r =>
-        (match r with
-        | none => (pure (ForInStep.yield (some (runTrial t))) : Id (ForInStep (Option Outcome)))
-        | some b => if (runTrial t).cost < b.cost then pure (ForInStep.yield (some (runTrial t))) else pure (ForInStep.yield r))) = List.foldl step init trials by
-    rw [h none]; rfl
-  induction trials with
-  | nil => intro init; rfl
-  | cons h t ih =>
-    intro init
-    rw [List.forIn_cons, List.foldl_cons]
-    cases init with
-    | none => simp only [pure_bind, step]; rw [ih]
-    | some b =>
-      by_cases hc : (runTrial h).cost < b.cost
-      · simp only [pure_bind, step, hc, if_true]; rw [ih]
-      · simp only [pure_bind, step, hc, if_false]; rw [ih]
-
-theorem FoldInv_init : FoldInv [] none := by
-  constructor
-  · intro _; rfl
-  · intro h; exact absurd rfl h
-
-theorem FoldInv_step (P : List Int) (t : Int) (b : Option Outcome) :
-    FoldInv P b → FoldInv (P ++ [t]) (step b t) := by
-  intro hInv
-  refine ⟨fun hEmpty => absurd hEmpty (by simp), fun _ => ?_⟩
-  by_cases hP : P = []
-  · -- Empty prefix: b = none, so step none t = some (runTrial t)
-    subst hP
-    have hb : b = none := hInv.1 rfl
-    subst hb
-    simp only [step, List.nil_append]
-    refine ⟨⟨0, by simp⟩, ?_, ?_, ?_⟩
-    · simp
-    · intro j
-      simp only [List.get_eq_getElem]
-      have hj0 : (j : ℕ) = 0 := by
-        have := j.isLt; simp only [List.length_cons, List.length_nil] at this; omega
-      simp only [hj0]
-      exact le_refl _
-    · intro j hj
-      exact absurd hj (Nat.not_lt_zero _)
-  · -- Nonempty prefix
-    obtain ⟨i, hb, hmin, hearl⟩ := hInv.2 hP
-    simp only [List.get_eq_getElem] at hb hmin hearl
-    have hi := i.isLt
-    have hilt : i.val < (P ++ [t]).length := by
-      simp only [List.length_append, List.length_cons, List.length_nil]; omega
-    by_cases hcase : (runTrial t).cost < (runTrial P[i.val]).cost
-    · -- new trial wins; best becomes some (runTrial t), witness = last index
-      have hstep : step b t = some (runTrial t) := by
-        rw [hb]; simp only [step, if_pos hcase]
-      rw [hstep]
-      refine ⟨⟨P.length, by simp⟩, ?_, ?_, ?_⟩
-      · simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-      · intro j
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-        by_cases hj : j.val < P.length
-        · rw [List.getElem_append_left hj]
-          have hm := hmin ⟨j.val, hj⟩
-          exact le_of_lt (lt_of_lt_of_le hcase hm)
-        · have hjeq : j.val = P.length := by
-            have hjl := j.isLt
-            simp only [List.length_append, List.length_cons, List.length_nil] at hjl
-            omega
-          rw [List.getElem_concat_length (l := P) (a := t) hjeq]
-      · intro j hj
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-        rw [List.getElem_append_left hj]
-        have hm := hmin ⟨j.val, hj⟩
-        exact lt_of_lt_of_le hcase hm
-    · -- old best wins; accumulator unchanged, witness = i
-      push_neg at hcase
-      have hstep : step b t = b := by
-        rw [hb]; simp only [step, if_neg (not_lt.mpr hcase)]
-      rw [hstep, hb]
-      refine ⟨⟨i.val, hilt⟩, ?_, ?_, ?_⟩
-      · simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-      · intro j
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-        by_cases hj : j.val < P.length
-        · rw [List.getElem_append_left hj]
-          exact hmin ⟨j.val, hj⟩
-        · have hjeq : j.val = P.length := by
-            have hjl := j.isLt
-            simp only [List.length_append, List.length_cons, List.length_nil] at hjl
-            omega
-          rw [List.getElem_concat_length (l := P) (a := t) hjeq]
-          exact hcase
-      · intro j hj
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-        have hjP : j.val < P.length := lt_trans hj hi
-        rw [List.getElem_append_left hjP]
-        exact hearl ⟨j.val, hjP⟩ hj
-
-theorem FoldInv_holds (L : List Int) : FoldInv L (L.foldl step none) := by
-  induction L using List.reverseRecOn with
-  | nil => exact FoldInv_init
-  | append_singleton P t IH =>
-    rw [List.foldl_concat]
-    exact FoldInv_step P t (P.foldl step none) IH
-
-theorem nonempty_gives_some (trials : List Int) (h : trials ≠ []) :
-    ∃ iBest : Fin trials.length,
-      (trials.foldl step none) = some (runTrial (trials.get iBest)) ∧
-      (∀ j : Fin trials.length,
-          (runTrial (trials.get iBest)).cost ≤ (runTrial (trials.get j)).cost) ∧
-      (∀ j : Fin trials.length, j.val < iBest.val →
-          (runTrial (trials.get iBest)).cost < (runTrial (trials.get j)).cost) :=
-  (FoldInv_holds trials).2 h
-
-theorem result_is_trial_i (trials : List Int) (iBest : Fin trials.length)
-    (hfold : (trials.foldl step none) = some (runTrial (trials.get iBest))) :
-    implementation_bestTrial trials = runTrial (trials.get iBest) := by
-  rw [impl_eq_foldl, hfold, getD_some]
-
 theorem correct_bestTrial :
     ∀ (trials : List Int), trials ≠ [] →
       problem_spec_bestTrial trials (implementation_bestTrial trials) := by
   intro trials h
-  obtain ⟨iBest, hfold, hmin, hbefore⟩ := nonempty_gives_some trials h
-  have hres := result_is_trial_i trials iBest hfold
-  refine ⟨iBest, ?_, ?_, ?_⟩
-  · exact hres
-  · intro j; rw [hres]; exact hmin j
-  · intro j hj; rw [hres]; exact hbefore j hj
-
+  sorry
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,172 +65,18 @@
 -- impl-start
 def implementation_bestTrial (trials : List Int) : Outcome := Id.run do
   let mut best : Option Outcome := none
-  for t in trials do
-    let o := runTrial t
+  for p in [0:trials.length] do
+    let o := runTrial (Int.ofNat p)
     match best with
     | none   => best := some o
     | some b => if o.cost < b.cost then best := some o
   return best.getD default
 -- impl-end
 
-
 -- proof-start
-/-- Pure extraction of the loop body's effect on `best`: fold accumulator update. -/
-def step (b : Option Outcome) (t : Int) : Option Outcome :=
-  match b with
-  | none   => some (runTrial t)
-  | some o => if (runTrial t).cost < o.cost then some (runTrial t) else b
-
-/-- Loop invariant carrying the earliest-minimum-cost witness through the fold:
-(a) empty prefix ⇒ accumulator is `none`;
-(b) nonempty prefix ⇒ the accumulator is `some` of the outcome of the earliest
-    minimum-cost trial among the processed prefix. -/
-def FoldInv (processed : List Int) (b : Option Outcome) : Prop :=
-  (processed = [] → b = none) ∧
-  (processed ≠ [] → ∃ i : Fin processed.length,
-      b = some (runTrial (processed.get i)) ∧
-      (∀ j : Fin processed.length,
-          (runTrial (processed.get i)).cost ≤ (runTrial (processed.get j)).cost) ∧
-      (∀ j : Fin processed.length, j.val < i.val →
-          (runTrial (processed.get i)).cost < (runTrial (processed.get j)).cost))
-
-theorem getD_some (x : Outcome) : (some x).getD default = x := rfl
-
-theorem impl_eq_foldl (trials : List Int) :
-    implementation_bestTrial trials = (trials.foldl step none).getD default := by
-  simp only [implementation_bestTrial, Id.run, bind_pure_comp, map_pure]
-  suffices h : ∀ (init : Option Outcome),
-      (forIn trials init fun t r =>
-        (match r with
-        | none => (pure (ForInStep.yield (some (runTrial t))) : Id (ForInStep (Option Outcome)))
-        | some b => if (runTrial t).cost < b.cost then pure (ForInStep.yield (some (runTrial t))) else pure (ForInStep.yield r))) = List.foldl step init trials by
-    rw [h none]; rfl
-  induction trials with
-  | nil => intro init; rfl
-  | cons h t ih =>
-    intro init
-    rw [List.forIn_cons, List.foldl_cons]
-    cases init with
-    | none => simp only [pure_bind, step]; rw [ih]
-    | some b =>
-      by_cases hc : (runTrial h).cost < b.cost
-      · simp only [pure_bind, step, hc, if_true]; rw [ih]
-      · simp only [pure_bind, step, hc, if_false]; rw [ih]
-
-theorem FoldInv_init : FoldInv [] none := by
-  constructor
-  · intro _; rfl
-  · intro h; exact absurd rfl h
-
-theorem FoldInv_step (P : List Int) (t : Int) (b : Option Outcome) :
-    FoldInv P b → FoldInv (P ++ [t]) (step b t) := by
-  intro hInv
-  refine ⟨fun hEmpty => absurd hEmpty (by simp), fun _ => ?_⟩
-  by_cases hP : P = []
-  · -- Empty prefix: b = none, so step none t = some (runTrial t)
-    subst hP
-    have hb : b = none := hInv.1 rfl
-    subst hb
-    simp only [step, List.nil_append]
-    refine ⟨⟨0, by simp⟩, ?_, ?_, ?_⟩
-    · simp
-    · intro j
-      simp only [List.get_eq_getElem]
-      have hj0 : (j : ℕ) = 0 := by
-        have := j.isLt; simp only [List.length_cons, List.length_nil] at this; omega
-      simp only [hj0]
-      exact le_refl _
-    · intro j hj
-      exact absurd hj (Nat.not_lt_zero _)
-  · -- Nonempty prefix
-    obtain ⟨i, hb, hmin, hearl⟩ := hInv.2 hP
-    simp only [List.get_eq_getElem] at hb hmin hearl
-    have hi := i.isLt
-    have hilt : i.val < (P ++ [t]).length := by
-      simp only [List.length_append, List.length_cons, List.length_nil]; omega
-    by_cases hcase : (runTrial t).cost < (runTrial P[i.val]).cost
-    · -- new trial wins; best becomes some (runTrial t), witness = last index
-      have hstep : step b t = some (runTrial t) := by
-        rw [hb]; simp only [step, if_pos hcase]
-      rw [hstep]
-      refine ⟨⟨P.length, by simp⟩, ?_, ?_, ?_⟩
-      · simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-      · intro j
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-        by_cases hj : j.val < P.length
-        · rw [List.getElem_append_left hj]
-          have hm := hmin ⟨j.val, hj⟩
-          exact le_of_lt (lt_of_lt_of_le hcase hm)
-        · have hjeq : j.val = P.length := by
-            have hjl := j.isLt
-            simp only [List.length_append, List.length_cons, List.length_nil] at hjl
-            omega
-          rw [List.getElem_concat_length (l := P) (a := t) hjeq]
-      · intro j hj
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-        rw [List.getElem_append_left hj]
-        have hm := hmin ⟨j.val, hj⟩
-        exact lt_of_lt_of_le hcase hm
-    · -- old best wins; accumulator unchanged, witness = i
-      push_neg at hcase
-      have hstep : step b t = b := by
-        rw [hb]; simp only [step, if_neg (not_lt.mpr hcase)]
-      rw [hstep, hb]
-      refine ⟨⟨i.val, hilt⟩, ?_, ?_, ?_⟩
-      · simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-      · intro j
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-        by_cases hj : j.val < P.length
-        · rw [List.getElem_append_left hj]
-          exact hmin ⟨j.val, hj⟩
-        · have hjeq : j.val = P.length := by
-            have hjl := j.isLt
-            simp only [List.length_append, List.length_cons, List.length_nil] at hjl
-            omega
-          rw [List.getElem_concat_length (l := P) (a := t) hjeq]
-          exact hcase
-      · intro j hj
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-        have hjP : j.val < P.length := lt_trans hj hi
-        rw [List.getElem_append_left hjP]
-        exact hearl ⟨j.val, hjP⟩ hj
-
-theorem FoldInv_holds (L : List Int) : FoldInv L (L.foldl step none) := by
-  induction L using List.reverseRecOn with
-  | nil => exact FoldInv_init
-  | append_singleton P t IH =>
-    rw [List.foldl_concat]
-    exact FoldInv_step P t (P.foldl step none) IH
-
-theorem nonempty_gives_some (trials : List Int) (h : trials ≠ []) :
-    ∃ iBest : Fin trials.length,
-      (trials.foldl step none) = some (runTrial (trials.get iBest)) ∧
-      (∀ j : Fin trials.length,
-          (runTrial (trials.get iBest)).cost ≤ (runTrial (trials.get j)).cost) ∧
-      (∀ j : Fin trials.length, j.val < iBest.val →
-          (runTrial (trials.get iBest)).cost < (runTrial (trials.get j)).cost) :=
-  (FoldInv_holds trials).2 h
-
-theorem result_is_trial_i (trials : List Int) (iBest : Fin trials.length)
-    (hfold : (trials.foldl step none) = some (runTrial (trials.get iBest))) :
-    implementation_bestTrial trials = runTrial (trials.get iBest) := by
-  rw [impl_eq_foldl, hfold, getD_some]
-
 theorem correct_bestTrial :
     ∀ (trials : List Int), trials ≠ [] →
       problem_spec_bestTrial trials (implementation_bestTrial trials) := by
   intro trials h
-  obtain ⟨iBest, hfold, hmin, hbefore⟩ := nonempty_gives_some trials h
-  have hres := result_is_trial_i trials iBest hfold
-  refine ⟨iBest, ?_, ?_, ?_⟩
-  · exact hres
-  · intro j; rw [hres]; exact hmin j
-  · intro j hj; rw [hres]; exact hbefore j hj
-
+  sorry
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,173 +64,22 @@
 
 -- impl-start
 def implementation_bestTrial (trials : List Int) : Outcome := Id.run do
-  let mut best : Option Outcome := none
-  for t in trials do
-    let o := runTrial t
-    match best with
-    | none   => best := some o
-    | some b => if o.cost < b.cost then best := some o
-  return best.getD default
+  match trials with
+  | [_] => return runTrial 0
+  | _ =>
+    let mut best : Option Outcome := none
+    for t in trials do
+      let o := runTrial t
+      match best with
+      | none   => best := some o
+      | some b => if o.cost < b.cost then best := some o
+    return best.getD default
 -- impl-end
 
-
 -- proof-start
-/-- Pure extraction of the loop body's effect on `best`: fold accumulator update. -/
-def step (b : Option Outcome) (t : Int) : Option Outcome :=
-  match b with
-  | none   => some (runTrial t)
-  | some o => if (runTrial t).cost < o.cost then some (runTrial t) else b
-
-/-- Loop invariant carrying the earliest-minimum-cost witness through the fold:
-(a) empty prefix ⇒ accumulator is `none`;
-(b) nonempty prefix ⇒ the accumulator is `some` of the outcome of the earliest
-    minimum-cost trial among the processed prefix. -/
-def FoldInv (processed : List Int) (b : Option Outcome) : Prop :=
-  (processed = [] → b = none) ∧
-  (processed ≠ [] → ∃ i : Fin processed.length,
-      b = some (runTrial (processed.get i)) ∧
-      (∀ j : Fin processed.length,
-          (runTrial (processed.get i)).cost ≤ (runTrial (processed.get j)).cost) ∧
-      (∀ j : Fin processed.length, j.val < i.val →
-          (runTrial (processed.get i)).cost < (runTrial (processed.get j)).cost))
-
-theorem getD_some (x : Outcome) : (some x).getD default = x := rfl
-
-theorem impl_eq_foldl (trials : List Int) :
-    implementation_bestTrial trials = (trials.foldl step none).getD default := by
-  simp only [implementation_bestTrial, Id.run, bind_pure_comp, map_pure]
-  suffices h : ∀ (init : Option Outcome),
-      (forIn trials init fun t r =>
-        (match r with
-        | none => (pure (ForInStep.yield (some (runTrial t))) : Id (ForInStep (Option Outcome)))
-        | some b => if (runTrial t).cost < b.cost then pure (ForInStep.yield (some (runTrial t))) else pure (ForInStep.yield r))) = List.foldl step init trials by
-    rw [h none]; rfl
-  induction trials with
-  | nil => intro init; rfl
-  | cons h t ih =>
-    intro init
-    rw [List.forIn_cons, List.foldl_cons]
-    cases init with
-    | none => simp only [pure_bind, step]; rw [ih]
-    | some b =>
-      by_cases hc : (runTrial h).cost < b.cost
-      · simp only [pure_bind, step, hc, if_true]; rw [ih]
-      · simp only [pure_bind, step, hc, if_false]; rw [ih]
-
-theorem FoldInv_init : FoldInv [] none := by
-  constructor
-  · intro _; rfl
-  · intro h; exact absurd rfl h
-
-theorem FoldInv_step (P : List Int) (t : Int) (b : Option Outcome) :
-    FoldInv P b → FoldInv (P ++ [t]) (step b t) := by
-  intro hInv
-  refine ⟨fun hEmpty => absurd hEmpty (by simp), fun _ => ?_⟩
-  by_cases hP : P = []
-  · -- Empty prefix: b = none, so step none t = some (runTrial t)
-    subst hP
-    have hb : b = none := hInv.1 rfl
-    subst hb
-    simp only [step, List.nil_append]
-    refine ⟨⟨0, by simp⟩, ?_, ?_, ?_⟩
-    · simp
-    · intro j
-      simp only [List.get_eq_getElem]
-      have hj0 : (j : ℕ) = 0 := by
-        have := j.isLt; simp only [List.length_cons, List.length_nil] at this; omega
-      simp only [hj0]
-      exact le_refl _
-    · intro j hj
-      exact absurd hj (Nat.not_lt_zero _)
-  · -- Nonempty prefix
-    obtain ⟨i, hb, hmin, hearl⟩ := hInv.2 hP
-    simp only [List.get_eq_getElem] at hb hmin hearl
-    have hi := i.isLt
-    have hilt : i.val < (P ++ [t]).length := by
-      simp only [List.length_append, List.length_cons, List.length_nil]; omega
-    by_cases hcase : (runTrial t).cost < (runTrial P[i.val]).cost
-    · -- new trial wins; best becomes some (runTrial t), witness = last index
-      have hstep : step b t = some (runTrial t) := by
-        rw [hb]; simp only [step, if_pos hcase]
-      rw [hstep]
-      refine ⟨⟨P.length, by simp⟩, ?_, ?_, ?_⟩
-      · simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-      · intro j
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-        by_cases hj : j.val < P.length
-        · rw [List.getElem_append_left hj]
-          have hm := hmin ⟨j.val, hj⟩
-          exact le_of_lt (lt_of_lt_of_le hcase hm)
-        · have hjeq : j.val = P.length := by
-            have hjl := j.isLt
-            simp only [List.length_append, List.length_cons, List.length_nil] at hjl
-            omega
-          rw [List.getElem_concat_length (l := P) (a := t) hjeq]
-      · intro j hj
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-        rw [List.getElem_append_left hj]
-        have hm := hmin ⟨j.val, hj⟩
-        exact lt_of_lt_of_le hcase hm
-    · -- old best wins; accumulator unchanged, witness = i
-      push_neg at hcase
-      have hstep : step b t = b := by
-        rw [hb]; simp only [step, if_neg (not_lt.mpr hcase)]
-      rw [hstep, hb]
-      refine ⟨⟨i.val, hilt⟩, ?_, ?_, ?_⟩
-      · simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-      · intro j
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-        by_cases hj : j.val < P.length
-        · rw [List.getElem_append_left hj]
-          exact hmin ⟨j.val, hj⟩
-        · have hjeq : j.val = P.length := by
-            have hjl := j.isLt
-            simp only [List.length_append, List.length_cons, List.length_nil] at hjl
-            omega
-          rw [List.getElem_concat_length (l := P) (a := t) hjeq]
-          exact hcase
-      · intro j hj
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-        have hjP : j.val < P.length := lt_trans hj hi
-        rw [List.getElem_append_left hjP]
-        exact hearl ⟨j.val, hjP⟩ hj
-
-theorem FoldInv_holds (L : List Int) : FoldInv L (L.foldl step none) := by
-  induction L using List.reverseRecOn with
-  | nil => exact FoldInv_init
-  | append_singleton P t IH =>
-    rw [List.foldl_concat]
-    exact FoldInv_step P t (P.foldl step none) IH
-
-theorem nonempty_gives_some (trials : List Int) (h : trials ≠ []) :
-    ∃ iBest : Fin trials.length,
-      (trials.foldl step none) = some (runTrial (trials.get iBest)) ∧
-      (∀ j : Fin trials.length,
-          (runTrial (trials.get iBest)).cost ≤ (runTrial (trials.get j)).cost) ∧
-      (∀ j : Fin trials.length, j.val < iBest.val →
-          (runTrial (trials.get iBest)).cost < (runTrial (trials.get j)).cost) :=
-  (FoldInv_holds trials).2 h
-
-theorem result_is_trial_i (trials : List Int) (iBest : Fin trials.length)
-    (hfold : (trials.foldl step none) = some (runTrial (trials.get iBest))) :
-    implementation_bestTrial trials = runTrial (trials.get iBest) := by
-  rw [impl_eq_foldl, hfold, getD_some]
-
 theorem correct_bestTrial :
     ∀ (trials : List Int), trials ≠ [] →
       problem_spec_bestTrial trials (implementation_bestTrial trials) := by
   intro trials h
-  obtain ⟨iBest, hfold, hmin, hbefore⟩ := nonempty_gives_some trials h
-  have hres := result_is_trial_i trials iBest hfold
-  refine ⟨iBest, ?_, ?_, ?_⟩
-  · exact hres
-  · intro j; rw [hres]; exact hmin j
-  · intro j hj; rw [hres]; exact hbefore j hj
-
+  sorry
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,174 +63,13 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_bestTrial (trials : List Int) : Outcome := Id.run do
-  let mut best : Option Outcome := none
-  for t in trials do
-    let o := runTrial t
-    match best with
-    | none   => best := some o
-    | some b => if o.cost < b.cost then best := some o
-  return best.getD default
+def implementation_bestTrial (_trials : List Int) : Outcome := runTrial 0
 -- impl-end
 
-
 -- proof-start
-/-- Pure extraction of the loop body's effect on `best`: fold accumulator update. -/
-def step (b : Option Outcome) (t : Int) : Option Outcome :=
-  match b with
-  | none   => some (runTrial t)
-  | some o => if (runTrial t).cost < o.cost then some (runTrial t) else b
-
-/-- Loop invariant carrying the earliest-minimum-cost witness through the fold:
-(a) empty prefix ⇒ accumulator is `none`;
-(b) nonempty prefix ⇒ the accumulator is `some` of the outcome of the earliest
-    minimum-cost trial among the processed prefix. -/
-def FoldInv (processed : List Int) (b : Option Outcome) : Prop :=
-  (processed = [] → b = none) ∧
-  (processed ≠ [] → ∃ i : Fin processed.length,
-      b = some (runTrial (processed.get i)) ∧
-      (∀ j : Fin processed.length,
-          (runTrial (processed.get i)).cost ≤ (runTrial (processed.get j)).cost) ∧
-      (∀ j : Fin processed.length, j.val < i.val →
-          (runTrial (processed.get i)).cost < (runTrial (processed.get j)).cost))
-
-theorem getD_some (x : Outcome) : (some x).getD default = x := rfl
-
-theorem impl_eq_foldl (trials : List Int) :
-    implementation_bestTrial trials = (trials.foldl step none).getD default := by
-  simp only [implementation_bestTrial, Id.run, bind_pure_comp, map_pure]
-  suffices h : ∀ (init : Option Outcome),
-      (forIn trials init fun t r =>
-        (match r with
-        | none => (pure (ForInStep.yield (some (runTrial t))) : Id (ForInStep (Option Outcome)))
-        | some b => if (runTrial t).cost < b.cost then pure (ForInStep.yield (some (runTrial t))) else pure (ForInStep.yield r))) = List.foldl step init trials by
-    rw [h none]; rfl
-  induction trials with
-  | nil => intro init; rfl
-  | cons h t ih =>
-    intro init
-    rw [List.forIn_cons, List.foldl_cons]
-    cases init with
-    | none => simp only [pure_bind, step]; rw [ih]
-    | some b =>
-      by_cases hc : (runTrial h).cost < b.cost
-      · simp only [pure_bind, step, hc, if_true]; rw [ih]
-      · simp only [pure_bind, step, hc, if_false]; rw [ih]
-
-theorem FoldInv_init : FoldInv [] none := by
-  constructor
-  · intro _; rfl
-  · intro h; exact absurd rfl h
-
-theorem FoldInv_step (P : List Int) (t : Int) (b : Option Outcome) :
-    FoldInv P b → FoldInv (P ++ [t]) (step b t) := by
-  intro hInv
-  refine ⟨fun hEmpty => absurd hEmpty (by simp), fun _ => ?_⟩
-  by_cases hP : P = []
-  · -- Empty prefix: b = none, so step none t = some (runTrial t)
-    subst hP
-    have hb : b = none := hInv.1 rfl
-    subst hb
-    simp only [step, List.nil_append]
-    refine ⟨⟨0, by simp⟩, ?_, ?_, ?_⟩
-    · simp
-    · intro j
-      simp only [List.get_eq_getElem]
-      have hj0 : (j : ℕ) = 0 := by
-        have := j.isLt; simp only [List.length_cons, List.length_nil] at this; omega
-      simp only [hj0]
-      exact le_refl _
-    · intro j hj
-      exact absurd hj (Nat.not_lt_zero _)
-  · -- Nonempty prefix
-    obtain ⟨i, hb, hmin, hearl⟩ := hInv.2 hP
-    simp only [List.get_eq_getElem] at hb hmin hearl
-    have hi := i.isLt
-    have hilt : i.val < (P ++ [t]).length := by
-      simp only [List.length_append, List.length_cons, List.length_nil]; omega
-    by_cases hcase : (runTrial t).cost < (runTrial P[i.val]).cost
-    · -- new trial wins; best becomes some (runTrial t), witness = last index
-      have hstep : step b t = some (runTrial t) := by
-        rw [hb]; simp only [step, if_pos hcase]
-      rw [hstep]
-      refine ⟨⟨P.length, by simp⟩, ?_, ?_, ?_⟩
-      · simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-      · intro j
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-        by_cases hj : j.val < P.length
-        · rw [List.getElem_append_left hj]
-          have hm := hmin ⟨j.val, hj⟩
-          exact le_of_lt (lt_of_lt_of_le hcase hm)
-        · have hjeq : j.val = P.length := by
-            have hjl := j.isLt
-            simp only [List.length_append, List.length_cons, List.length_nil] at hjl
-            omega
-          rw [List.getElem_concat_length (l := P) (a := t) hjeq]
-      · intro j hj
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-        rw [List.getElem_append_left hj]
-        have hm := hmin ⟨j.val, hj⟩
-        exact lt_of_lt_of_le hcase hm
-    · -- old best wins; accumulator unchanged, witness = i
-      push_neg at hcase
-      have hstep : step b t = b := by
-        rw [hb]; simp only [step, if_neg (not_lt.mpr hcase)]
-      rw [hstep, hb]
-      refine ⟨⟨i.val, hilt⟩, ?_, ?_, ?_⟩
-      · simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-      · intro j
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-        by_cases hj : j.val < P.length
-        · rw [List.getElem_append_left hj]
-          exact hmin ⟨j.val, hj⟩
-        · have hjeq : j.val = P.length := by
-            have hjl := j.isLt
-            simp only [List.length_append, List.length_cons, List.length_nil] at hjl
-            omega
-          rw [List.getElem_concat_length (l := P) (a := t) hjeq]
-          exact hcase
-      · intro j hj
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-        have hjP : j.val < P.length := lt_trans hj hi
-        rw [List.getElem_append_left hjP]
-        exact hearl ⟨j.val, hjP⟩ hj
-
-theorem FoldInv_holds (L : List Int) : FoldInv L (L.foldl step none) := by
-  induction L using List.reverseRecOn with
-  | nil => exact FoldInv_init
-  | append_singleton P t IH =>
-    rw [List.foldl_concat]
-    exact FoldInv_step P t (P.foldl step none) IH
-
-theorem nonempty_gives_some (trials : List Int) (h : trials ≠ []) :
-    ∃ iBest : Fin trials.length,
-      (trials.foldl step none) = some (runTrial (trials.get iBest)) ∧
-      (∀ j : Fin trials.length,
-          (runTrial (trials.get iBest)).cost ≤ (runTrial (trials.get j)).cost) ∧
-      (∀ j : Fin trials.length, j.val < iBest.val →
-          (runTrial (trials.get iBest)).cost < (runTrial (trials.get j)).cost) :=
-  (FoldInv_holds trials).2 h
-
-theorem result_is_trial_i (trials : List Int) (iBest : Fin trials.length)
-    (hfold : (trials.foldl step none) = some (runTrial (trials.get iBest))) :
-    implementation_bestTrial trials = runTrial (trials.get iBest) := by
-  rw [impl_eq_foldl, hfold, getD_some]
-
 theorem correct_bestTrial :
     ∀ (trials : List Int), trials ≠ [] →
       problem_spec_bestTrial trials (implementation_bestTrial trials) := by
   intro trials h
-  obtain ⟨iBest, hfold, hmin, hbefore⟩ := nonempty_gives_some trials h
-  have hres := result_is_trial_i trials iBest hfold
-  refine ⟨iBest, ?_, ?_, ?_⟩
-  · exact hres
-  · intro j; rw [hres]; exact hmin j
-  · intro j hj; rw [hres]; exact hbefore j hj
-
+  sorry
 -- proof-end
```

Attack 8 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,174 +63,27 @@
 -- post-conditions-end
 
 -- impl-start
+-- PRE-PATCH (buggy) skeleton: the repeated attempts are NOT driven by the
+-- supplied configuration values. The loop runs over the attempt positions and
+-- drives each attempt with the position index instead of the corresponding
+-- supplied value, so the selected outcome is not `runTrial (trials.get i)` for
+-- any minimum index `i` of the supplied list.
 def implementation_bestTrial (trials : List Int) : Outcome := Id.run do
   let mut best : Option Outcome := none
-  for t in trials do
-    let o := runTrial t
+  for p in [0:trials.length] do
+    let o := runTrial (Int.ofNat p)
     match best with
     | none   => best := some o
     | some b => if o.cost < b.cost then best := some o
   return best.getD default
 -- impl-end
 
-
 -- proof-start
-/-- Pure extraction of the loop body's effect on `best`: fold accumulator update. -/
-def step (b : Option Outcome) (t : Int) : Option Outcome :=
-  match b with
-  | none   => some (runTrial t)
-  | some o => if (runTrial t).cost < o.cost then some (runTrial t) else b
-
-/-- Loop invariant carrying the earliest-minimum-cost witness through the fold:
-(a) empty prefix ⇒ accumulator is `none`;
-(b) nonempty prefix ⇒ the accumulator is `some` of the outcome of the earliest
-    minimum-cost trial among the processed prefix. -/
-def FoldInv (processed : List Int) (b : Option Outcome) : Prop :=
-  (processed = [] → b = none) ∧
-  (processed ≠ [] → ∃ i : Fin processed.length,
-      b = some (runTrial (processed.get i)) ∧
-      (∀ j : Fin processed.length,
-          (runTrial (processed.get i)).cost ≤ (runTrial (processed.get j)).cost) ∧
-      (∀ j : Fin processed.length, j.val < i.val →
-          (runTrial (processed.get i)).cost < (runTrial (processed.get j)).cost))
-
-theorem getD_some (x : Outcome) : (some x).getD default = x := rfl
-
-theorem impl_eq_foldl (trials : List Int) :
-    implementation_bestTrial trials = (trials.foldl step none).getD default := by
-  simp only [implementation_bestTrial, Id.run, bind_pure_comp, map_pure]
-  suffices h : ∀ (init : Option Outcome),
-      (forIn trials init fun t r =>
-        (match r with
-        | none => (pure (ForInStep.yield (some (runTrial t))) : Id (ForInStep (Option Outcome)))
-        | some b => if (runTrial t).cost < b.cost then pure (ForInStep.yield (some (runTrial t))) else pure (ForInStep.yield r))) = List.foldl step init trials by
-    rw [h none]; rfl
-  induction trials with
-  | nil => intro init; rfl
-  | cons h t ih =>
-    intro init
-    rw [List.forIn_cons, List.foldl_cons]
-    cases init with
-    | none => simp only [pure_bind, step]; rw [ih]
-    | some b =>
-      by_cases hc : (runTrial h).cost < b.cost
-      · simp only [pure_bind, step, hc, if_true]; rw [ih]
-      · simp only [pure_bind, step, hc, if_false]; rw [ih]
-
-theorem FoldInv_init : FoldInv [] none := by
-  constructor
-  · intro _; rfl
-  · intro h; exact absurd rfl h
-
-theorem FoldInv_step (P : List Int) (t : Int) (b : Option Outcome) :
-    FoldInv P b → FoldInv (P ++ [t]) (step b t) := by
-  intro hInv
-  refine ⟨fun hEmpty => absurd hEmpty (by simp), fun _ => ?_⟩
-  by_cases hP : P = []
-  · -- Empty prefix: b = none, so step none t = some (runTrial t)
-    subst hP
-    have hb : b = none := hInv.1 rfl
-    subst hb
-    simp only [step, List.nil_append]
-    refine ⟨⟨0, by simp⟩, ?_, ?_, ?_⟩
-    · simp
-    · intro j
-      simp only [List.get_eq_getElem]
-      have hj0 : (j : ℕ) = 0 := by
-        have := j.isLt; simp only [List.length_cons, List.length_nil] at this; omega
-      simp only [hj0]
-      exact le_refl _
-    · intro j hj
-      exact absurd hj (Nat.not_lt_zero _)
-  · -- Nonempty prefix
-    obtain ⟨i, hb, hmin, hearl⟩ := hInv.2 hP
-    simp only [List.get_eq_getElem] at hb hmin hearl
-    have hi := i.isLt
-    have hilt : i.val < (P ++ [t]).length := by
-      simp only [List.length_append, List.length_cons, List.length_nil]; omega
-    by_cases hcase : (runTrial t).cost < (runTrial P[i.val]).cost
-    · -- new trial wins; best becomes some (runTrial t), witness = last index
-      have hstep : step b t = some (runTrial t) := by
-        rw [hb]; simp only [step, if_pos hcase]
-      rw [hstep]
-      refine ⟨⟨P.length, by simp⟩, ?_, ?_, ?_⟩
-      · simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-      · intro j
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-        by_cases hj : j.val < P.length
-        · rw [List.getElem_append_left hj]
-          have hm := hmin ⟨j.val, hj⟩
-          exact le_of_lt (lt_of_lt_of_le hcase hm)
-        · have hjeq : j.val = P.length := by
-            have hjl := j.isLt
-            simp only [List.length_append, List.length_cons, List.length_nil] at hjl
-            omega
-          rw [List.getElem_concat_length (l := P) (a := t) hjeq]
-      · intro j hj
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_concat_length (l := P) (a := t) rfl]
-        rw [List.getElem_append_left hj]
-        have hm := hmin ⟨j.val, hj⟩
-        exact lt_of_lt_of_le hcase hm
-    · -- old best wins; accumulator unchanged, witness = i
-      push_neg at hcase
-      have hstep : step b t = b := by
-        rw [hb]; simp only [step, if_neg (not_lt.mpr hcase)]
-      rw [hstep, hb]
-      refine ⟨⟨i.val, hilt⟩, ?_, ?_, ?_⟩
-      · simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-      · intro j
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-        by_cases hj : j.val < P.length
-        · rw [List.getElem_append_left hj]
-          exact hmin ⟨j.val, hj⟩
-        · have hjeq : j.val = P.length := by
-            have hjl := j.isLt
-            simp only [List.length_append, List.length_cons, List.length_nil] at hjl
-            omega
-          rw [List.getElem_concat_length (l := P) (a := t) hjeq]
-          exact hcase
-      · intro j hj
-        simp only [List.get_eq_getElem]
-        rw [List.getElem_append_left hi]
-        have hjP : j.val < P.length := lt_trans hj hi
-        rw [List.getElem_append_left hjP]
-        exact hearl ⟨j.val, hjP⟩ hj
-
-theorem FoldInv_holds (L : List Int) : FoldInv L (L.foldl step none) := by
-  induction L using List.reverseRecOn with
-  | nil => exact FoldInv_init
-  | append_singleton P t IH =>
-    rw [List.foldl_concat]
-    exact FoldInv_step P t (P.foldl step none) IH
-
-theorem nonempty_gives_some (trials : List Int) (h : trials ≠ []) :
-    ∃ iBest : Fin trials.length,
-      (trials.foldl step none) = some (runTrial (trials.get iBest)) ∧
-      (∀ j : Fin trials.length,
-          (runTrial (trials.get iBest)).cost ≤ (runTrial (trials.get j)).cost) ∧
-      (∀ j : Fin trials.length, j.val < iBest.val →
-          (runTrial (trials.get iBest)).cost < (runTrial (trials.get j)).cost) :=
-  (FoldInv_holds trials).2 h
-
-theorem result_is_trial_i (trials : List Int) (iBest : Fin trials.length)
-    (hfold : (trials.foldl step none) = some (runTrial (trials.get iBest))) :
-    implementation_bestTrial trials = runTrial (trials.get iBest) := by
-  rw [impl_eq_foldl, hfold, getD_some]
-
+-- Gold proof body carried over; it does NOT close against the buggy impl: the
+-- result comes from `runTrial (index)`, not from `runTrial (trials.get i)`, so the
+-- discriminating clause `result = runTrial (trials.get i)` cannot be discharged.
 theorem correct_bestTrial :
     ∀ (trials : List Int), trials ≠ [] →
       problem_spec_bestTrial trials (implementation_bestTrial trials) := by
-  intro trials h
-  obtain ⟨iBest, hfold, hmin, hbefore⟩ := nonempty_gives_some trials h
-  have hres := result_is_trial_i trials iBest hfold
-  refine ⟨iBest, ?_, ?_, ?_⟩
-  · exact hres
-  · intro j; rw [hres]; exact hmin j
-  · intro j hj; rw [hres]; exact hbefore j hj
-
+  sorry
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Selecting the best result among several independent repeated attempts.

A procedure is run several times, once per entry of a given list of independent
configuration values supplied by the caller. Each value drives one self-contained
attempt that yields an *outcome* — a numeric cost together with the data the
attempt produced. The attempts do not interact: an attempt's outcome is a
function of its own configuration value alone.

The procedure keeps the single best outcome, "best" meaning lowest cost. When
several attempts tie for the lowest cost, the earliest of them (the one driven by
the configuration value appearing first in the list) is the one kept. The whole
chosen outcome is returned verbatim — both its cost and its produced data come
from one and the same attempt.

Because the selection is a deterministic function of the supplied list of
configuration values, the result does not depend on the order in which the
attempts happen to be evaluated or on how the work is distributed. The behavior
is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
/-- The outcome of one self-contained attempt: a numeric `cost` used to rank
attempts (lower is better) together with the `data` that attempt produced. Cost
is modeled by an exact integer because only its ORDER is observed by the
selection (the real quantity is compared with `<` / argmin only). -/
structure Outcome where
  cost : Int
  data : List Int
deriving Inhabited, DecidableEq

/-- Run one self-contained attempt for a given configuration value. This is an
UNCHANGED downstream routine: deterministic in its argument and observed only
through its returned outcome. Declared `opaque` so it can appear in the
executable implementation; the proof consumes no property of it (the selection is
correct for ANY such routine), so no `_prop` axiom is asserted. -/
opaque runTrial : Int → Outcome
-- axioms-end

-- pure-start
-- No additional pure helpers: the selection is spelled out in the impl region.
-- pure-end

-- post-conditions-start
/-- The result is the outcome of the earliest minimum-cost attempt:

* there is an index `i` into the configuration list such that the result IS the
  outcome of running attempt `i` (frame: every component of the result — cost and
  produced data — comes from this one attempt);
* no attempt has a strictly lower cost than the result (global minimum);
* every attempt strictly EARLIER than `i` has a strictly greater cost (so `i` is
  the first index attaining the minimum — the tie-break the procedure uses). -/
def problem_spec_bestTrial (trials : List Int) (result : Outcome) : Prop :=
  ∃ i : Fin trials.length,
    result = runTrial (trials.get i) ∧
    (∀ j : Fin trials.length, result.cost ≤ (runTrial (trials.get j)).cost) ∧
    (∀ j : Fin trials.length, j.val < i.val →
        result.cost < (runTrial (trials.get j)).cost)
-- post-conditions-end

-- impl-start
def implementation_bestTrial (trials : List Int) : Outcome := Id.run do
  let mut best : Option Outcome := none
  for t in trials do
    let o := runTrial t
    match best with
    | none   => best := some o
    | some b => if o.cost < b.cost then best := some o
  return best.getD default
-- impl-end


-- proof-start
/-- Pure extraction of the loop body's effect on `best`: fold accumulator update. -/
def step (b : Option Outcome) (t : Int) : Option Outcome :=
  match b with
  | none   => some (runTrial t)
  | some o => if (runTrial t).cost < o.cost then some (runTrial t) else b

/-- Loop invariant carrying the earliest-minimum-cost witness through the fold:
(a) empty prefix ⇒ accumulator is `none`;
(b) nonempty prefix ⇒ the accumulator is `some` of the outcome of the earliest
    minimum-cost trial among the processed prefix. -/
def FoldInv (processed : List Int) (b : Option Outcome) : Prop :=
  (processed = [] → b = none) ∧
  (processed ≠ [] → ∃ i : Fin processed.length,
      b = some (runTrial (processed.get i)) ∧
      (∀ j : Fin processed.length,
          (runTrial (processed.get i)).cost ≤ (runTrial (processed.get j)).cost) ∧
      (∀ j : Fin processed.length, j.val < i.val →
          (runTrial (processed.get i)).cost < (runTrial (processed.get j)).cost))

theorem getD_some (x : Outcome) : (some x).getD default = x := rfl

theorem impl_eq_foldl (trials : List Int) :
    implementation_bestTrial trials = (trials.foldl step none).getD default := by
  simp only [implementation_bestTrial, Id.run, bind_pure_comp, map_pure]
  suffices h : ∀ (init : Option Outcome),
      (forIn trials init fun t r =>
        (match r with
        | none => (pure (ForInStep.yield (some (runTrial t))) : Id (ForInStep (Option Outcome)))
        | some b => if (runTrial t).cost < b.cost then pure (ForInStep.yield (some (runTrial t))) else pure (ForInStep.yield r))) = List.foldl step init trials by
    rw [h none]; rfl
  induction trials with
  | nil => intro init; rfl
  | cons h t ih =>
    intro init
    rw [List.forIn_cons, List.foldl_cons]
    cases init with
    | none => simp only [pure_bind, step]; rw [ih]
    | some b =>
      by_cases hc : (runTrial h).cost < b.cost
      · simp only [pure_bind, step, hc, if_true]; rw [ih]
      · simp only [pure_bind, step, hc, if_false]; rw [ih]

theorem FoldInv_init : FoldInv [] none := by
  constructor
  · intro _; rfl
  · intro h; exact absurd rfl h

theorem FoldInv_step (P : List Int) (t : Int) (b : Option Outcome) :
    FoldInv P b → FoldInv (P ++ [t]) (step b t) := by
  intro hInv
  refine ⟨fun hEmpty => absurd hEmpty (by simp), fun _ => ?_⟩
  by_cases hP : P = []
  · -- Empty prefix: b = none, so step none t = some (runTrial t)
    subst hP
    have hb : b = none := hInv.1 rfl
    subst hb
    simp only [step, List.nil_append]
    refine ⟨⟨0, by simp⟩, ?_, ?_, ?_⟩
    · simp
    · intro j
      simp only [List.get_eq_getElem]
      have hj0 : (j : ℕ) = 0 := by
        have := j.isLt; simp only [List.length_cons, List.length_nil] at this; omega
      simp only [hj0]
      exact le_refl _
    · intro j hj
      exact absurd hj (Nat.not_lt_zero _)
  · -- Nonempty prefix
    obtain ⟨i, hb, hmin, hearl⟩ := hInv.2 hP
    simp only [List.get_eq_getElem] at hb hmin hearl
    have hi := i.isLt
    have hilt : i.val < (P ++ [t]).length := by
      simp only [List.length_append, List.length_cons, List.length_nil]; omega
    by_cases hcase : (runTrial t).cost < (runTrial P[i.val]).cost
    · -- new trial wins; best becomes some (runTrial t), witness = last index
      have hstep : step b t = some (runTrial t) := by
        rw [hb]; simp only [step, if_pos hcase]
      rw [hstep]
      refine ⟨⟨P.length, by simp⟩, ?_, ?_, ?_⟩
      · simp only [List.get_eq_getElem]
        rw [List.getElem_concat_length (l := P) (a := t) rfl]
      · intro j
        simp only [List.get_eq_getElem]
        rw [List.getElem_concat_length (l := P) (a := t) rfl]
        by_cases hj : j.val < P.length
        · rw [List.getElem_append_left hj]
          have hm := hmin ⟨j.val, hj⟩
          exact le_of_lt (lt_of_lt_of_le hcase hm)
        · have hjeq : j.val = P.length := by
            have hjl := j.isLt
            simp only [List.length_append, List.length_cons, List.length_nil] at hjl
            omega
          rw [List.getElem_concat_length (l := P) (a := t) hjeq]
      · intro j hj
        simp only [List.get_eq_getElem]
        rw [List.getElem_concat_length (l := P) (a := t) rfl]
        rw [List.getElem_append_left hj]
        have hm := hmin ⟨j.val, hj⟩
        exact lt_of_lt_of_le hcase hm
    · -- old best wins; accumulator unchanged, witness = i
      push_neg at hcase
      have hstep : step b t = b := by
        rw [hb]; simp only [step, if_neg (not_lt.mpr hcase)]
      rw [hstep, hb]
      refine ⟨⟨i.val, hilt⟩, ?_, ?_, ?_⟩
      · simp only [List.get_eq_getElem]
        rw [List.getElem_append_left hi]
      · intro j
        simp only [List.get_eq_getElem]
        rw [List.getElem_append_left hi]
        by_cases hj : j.val < P.length
        · rw [List.getElem_append_left hj]
          exact hmin ⟨j.val, hj⟩
        · have hjeq : j.val = P.length := by
            have hjl := j.isLt
            simp only [List.length_append, List.length_cons, List.length_nil] at hjl
            omega
          rw [List.getElem_concat_length (l := P) (a := t) hjeq]
          exact hcase
      · intro j hj
        simp only [List.get_eq_getElem]
        rw [List.getElem_append_left hi]
        have hjP : j.val < P.length := lt_trans hj hi
        rw [List.getElem_append_left hjP]
        exact hearl ⟨j.val, hjP⟩ hj

theorem FoldInv_holds (L : List Int) : FoldInv L (L.foldl step none) := by
  induction L using List.reverseRecOn with
  | nil => exact FoldInv_init
  | append_singleton P t IH =>
    rw [List.foldl_concat]
    exact FoldInv_step P t (P.foldl step none) IH

theorem nonempty_gives_some (trials : List Int) (h : trials ≠ []) :
    ∃ iBest : Fin trials.length,
      (trials.foldl step none) = some (runTrial (trials.get iBest)) ∧
      (∀ j : Fin trials.length,
          (runTrial (trials.get iBest)).cost ≤ (runTrial (trials.get j)).cost) ∧
      (∀ j : Fin trials.length, j.val < iBest.val →
          (runTrial (trials.get iBest)).cost < (runTrial (trials.get j)).cost) :=
  (FoldInv_holds trials).2 h

theorem result_is_trial_i (trials : List Int) (iBest : Fin trials.length)
    (hfold : (trials.foldl step none) = some (runTrial (trials.get iBest))) :
    implementation_bestTrial trials = runTrial (trials.get iBest) := by
  rw [impl_eq_foldl, hfold, getD_some]

theorem correct_bestTrial :
    ∀ (trials : List Int), trials ≠ [] →
      problem_spec_bestTrial trials (implementation_bestTrial trials) := by
  intro trials h
  obtain ⟨iBest, hfold, hmin, hbefore⟩ := nonempty_gives_some trials h
  have hres := result_is_trial_i trials iBest hfold
  refine ⟨iBest, ?_, ?_, ?_⟩
  · exact hres
  · intro j; rw [hres]; exact hmin j
  · intro j hj; rw [hres]; exact hbefore j hj

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_bestTrial is a TOTAL FUNCTIONAL CHARACTERIZATION. For any nonempty `trials`, the three conjuncts jointly pin a unique output: (frame) result = runTrial (trials.get i) for some index i, both cost AND data verbatim; (global-min) no attempt has strictly lower cost; (strict-earlier) every j<i has strictly greater cost. Together these force result to be exactly the outcome of the EARLIEST global-min-cost attempt, driven by the SUPPLIED VALUE trials.get i (not the position). Because `runTrial : Int -> Outcome` is `opaque` (no _prop), any impl deviating from this must prove an unprovable equality/ordering between runTrial at different arguments, so no wrong impl can close.

SAME-SPEC: all 8 attack files + positive_control return same_spec=True via swebench_unified.markers.same_spec (lean backend); spec regions (imports/axioms/pure/pre/post, lines 1-63) left byte-identical; only impl+proof edited.

POSITIVE CONTROL: positive_control.lean (= bundle Solution.lean). `bash scripts/lean_verify.sh positive_control.lean` -> EXIT 0. `#print axioms correct_bestTrial` (pc_ax.lean) -> [propext, Classical.choice, Quot.sound], NO sorryAx. Clean close confirmed.

ATTACKS (6+ DISTINCT wrong impls; command `bash scripts/lean_verify.sh <f>`; exit 3 = elaborates but only with sorry => proof CANNOT close):
- atk_1 (boundary/no-selection: return first trial `t::_ => runTrial t`): EXIT 3.
- atk_2 (boundary: return LAST trial via reverse.head?): EXIT 3.
- atk_3 (wrong-direction: argMAX, `if o.cost > b.cost`): EXIT 3.
- atk_4 (wrong tie-break: non-strict `<=` keeps LAST minimum): EXIT 3.
- atk_5 (control-flow-effect: position-driven `runTrial (Int.ofNat p)` over [0:len] — the prepatch bug re-encoded independently): EXIT 3.
- atk_6 (partial-domain: gold on |trials|>=2 but singleton returns `runTrial 0` regardless of element): EXIT 3.
- atk_7 (ungrounded-oracle echo: constant `runTrial 0` for all inputs, no loop): EXIT 3.
- atk_prepatch (bundle Solution_prepatch.lean, position-driven with carried gold proof + sorry): EXIT 3.
NONE of the 8 closes => zero impls with a closing clean-axiom proof => `patches` is empty (nothing to materialize/resolve-run). No resolve run was required or possible.

### MACHINE-CHECKED REFUTATIONS (positive evidence the wrong behaviors provably CANNOT satisfy the spec, not merely that my tactic failed):
- ref_1.lean (first-trial impl): `refute_first` with (runTrial 0).cost=5, (runTrial 1).cost=1 on [0,1]: global-min conjunct forces 5<=1, contradiction. EXIT 0 (theorem CLOSES).
- ref_3.lean (argmax impl): `refute_argmax` with cost0=1, cost1=5 on [0,1]: impl provably returns runTrial 1 (highest), violating global-min (forces 5<=1). EXIT 0 (CLOSES).
- ref_4.lean (non-strict last-min impl): `refute_lastmin` with cost0=cost1=1, data0!=data1 on [0,1]: impl provably returns runTrial 1; frame at i=0 forces data equality (contradiction with distinct data), earliest conjunct at i=1 forces 1<1 (contradiction). EXIT 0 (CLOSES).
prepatch position-driven behavior separately: verdict.md records `implementation_bestTrial [7] = runTrial 0` by rfl while spec forces runTrial 7, unprovable under opaque runTrial — reproduced conceptually; atk_prepatch/atk_5 carry it and both fail to close (EXIT 3).

REFINEMENT.MD LEG AUDIT (§4 correspondence): 4 legs, all R / A-reference / I, NO kind-3, NO A-consumed.
- L1 `trials : List Int` <- `seeds = random_state.randint(..., size=n_init)`: R (input; RNG unchanged in value, patch only HOISTS the line above the branch; not modeled). OK.
- L2 `for t in trials do let o := runTrial t` <- `for seed in seeds: kmeans_single(..., random_state=seed)`: A-REFERENCE — THE sole edited op (value-driven vs shared-random_state). kmeans_single is the UNCHANGED callee, modeled `opaque runTrial` with NO _prop (proof consumes no property; argmin selection holds for ANY function). Correspondence to real callee holds; G-AX is a justified skip stub; drift left to G-CONF. OK.
- L3 running-best strict-`<` update <- `if best_inertia is None or inertia < best_inertia`: I (strict < => first minimum kept, matching np.argmin first-occurrence in parallel branch). OK.
- L4 `return best.getD default` <- `return best_labels, best_inertia, ...`: R (whole chosen outcome returned verbatim; frame: all components from one runTrial). OK.
Outcome.cost:Int is an ORDER-ONLY refinement of inertia:float (only < / argmin observed) — sound, fuzzed by G-CONF. No A-leg over-claims about kmeans_single. Correspondence sound.

CONCLUSION: The spec is a total functional characterization discriminating the value-driven gold (frame clause result = runTrial (trials.get i)) from the position-driven prepatch bug and every other deviation. >=8 distinct same-spec wrong impls were genuinely attempted; none closes; 3 are machine-checked-refuted as provably spec-violating. No closing-clean-axiom wrong impl exists, hence no faithful non-resolving patch. verify=>correct. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_prepatch.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation admits a closing clean-axiom proof, so there is no faithful patch to materialize or resolve-run. verify=>correct holds on the modeled surface.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Selecting the best result among several independent repeated attempts.

A procedure is run several times, once per entry of a given list of independent
configuration values supplied by the caller. Each value drives one self-contained
attempt that yields an *outcome* — a numeric cost together with the data the
attempt produced. The attempts do not interact: an attempt's outcome is a
function of its own configuration value alone.

The procedure keeps the single best outcome, "best" meaning lowest cost. When
several attempts tie for the lowest cost, the earliest of them (the one driven by
the configuration value appearing first in the list) is the one kept. The whole
chosen outcome is returned verbatim — both its cost and its produced data come
from one and the same attempt.

Because the selection is a deterministic function of the supplied list of
configuration values, the result does not depend on the order in which the
attempts happen to be evaluated or on how the work is distributed. The behavior
is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
/-- The outcome of one self-contained attempt: a numeric `cost` used to rank
attempts (lower is better) together with the `data` that attempt produced. Cost
is modeled by an exact integer because only its ORDER is observed by the
selection (the real quantity is compared with `<` / argmin only). -/
structure Outcome where
  cost : Int
  data : List Int
deriving Inhabited, DecidableEq

/-- Run one self-contained attempt for a given configuration value. This is an
UNCHANGED downstream routine: deterministic in its argument and observed only
through its returned outcome. Declared `opaque` so it can appear in the
executable implementation; the proof consumes no property of it (the selection is
correct for ANY such routine), so no `_prop` axiom is asserted. -/
opaque runTrial : Int → Outcome
-- axioms-end

-- pure-start
-- No additional pure helpers: the selection is spelled out in the impl region.
-- pure-end

-- post-conditions-start
/-- The result is the outcome of the earliest minimum-cost attempt:

* there is an index `i` into the configuration list such that the result IS the
  outcome of running attempt `i` (frame: every component of the result — cost and
  produced data — comes from this one attempt);
* no attempt has a strictly lower cost than the result (global minimum);
* every attempt strictly EARLIER than `i` has a strictly greater cost (so `i` is
  the first index attaining the minimum — the tie-break the procedure uses). -/
def problem_spec_bestTrial (trials : List Int) (result : Outcome) : Prop :=
  ∃ i : Fin trials.length,
    result = runTrial (trials.get i) ∧
    (∀ j : Fin trials.length, result.cost ≤ (runTrial (trials.get j)).cost) ∧
    (∀ j : Fin trials.length, j.val < i.val →
        result.cost < (runTrial (trials.get j)).cost)
-- post-conditions-end

-- impl-start
def implementation_bestTrial (trials : List Int) : Outcome := Id.run do
  let mut best : Option Outcome := none
  for t in trials do
    let o := runTrial t
    match best with
    | none   => best := some o
    | some b => if o.cost < b.cost then best := some o
  return best.getD default
-- impl-end


-- proof-start
/-- Pure extraction of the loop body's effect on `best`: fold accumulator update. -/
def step (b : Option Outcome) (t : Int) : Option Outcome :=
  match b with
  | none   => some (runTrial t)
  | some o => if (runTrial t).cost < o.cost then some (runTrial t) else b

/-- Loop invariant carrying the earliest-minimum-cost witness through the fold:
(a) empty prefix ⇒ accumulator is `none`;
(b) nonempty prefix ⇒ the accumulator is `some` of the outcome of the earliest
    minimum-cost trial among the processed prefix. -/
def FoldInv (processed : List Int) (b : Option Outcome) : Prop :=
  (processed = [] → b = none) ∧
  (processed ≠ [] → ∃ i : Fin processed.length,
      b = some (runTrial (processed.get i)) ∧
      (∀ j : Fin processed.length,
          (runTrial (processed.get i)).cost ≤ (runTrial (processed.get j)).cost) ∧
      (∀ j : Fin processed.length, j.val < i.val →
          (runTrial (processed.get i)).cost < (runTrial (processed.get j)).cost))

theorem getD_some (x : Outcome) : (some x).getD default = x := rfl

theorem impl_eq_foldl (trials : List Int) :
    implementation_bestTrial trials = (trials.foldl step none).getD default := by
  simp only [implementation_bestTrial, Id.run, bind_pure_comp, map_pure]
  suffices h : ∀ (init : Option Outcome),
      (forIn trials init fun t r =>
        (match r with
        | none => (pure (ForInStep.yield (some (runTrial t))) : Id (ForInStep (Option Outcome)))
        | some b => if (runTrial t).cost < b.cost then pure (ForInStep.yield (some (runTrial t))) else pure (ForInStep.yield r))) = List.foldl step init trials by
    rw [h none]; rfl
  induction trials with
  | nil => intro init; rfl
  | cons h t ih =>
    intro init
    rw [List.forIn_cons, List.foldl_cons]
    cases init with
    | none => simp only [pure_bind, step]; rw [ih]
    | some b =>
      by_cases hc : (runTrial h).cost < b.cost
      · simp only [pure_bind, step, hc, if_true]; rw [ih]
      · simp only [pure_bind, step, hc, if_false]; rw [ih]

theorem FoldInv_init : FoldInv [] none := by
  constructor
  · intro _; rfl
  · intro h; exact absurd rfl h

theorem FoldInv_step (P : List Int) (t : Int) (b : Option Outcome) :
    FoldInv P b → FoldInv (P ++ [t]) (step b t) := by
  intro hInv
  refine ⟨fun hEmpty => absurd hEmpty (by simp), fun _ => ?_⟩
  by_cases hP : P = []
  · -- Empty prefix: b = none, so step none t = some (runTrial t)
    subst hP
    have hb : b = none := hInv.1 rfl
    subst hb
    simp only [step, List.nil_append]
    refine ⟨⟨0, by simp⟩, ?_, ?_, ?_⟩
    · simp
    · intro j
      simp only [List.get_eq_getElem]
      have hj0 : (j : ℕ) = 0 := by
        have := j.isLt; simp only [List.length_cons, List.length_nil] at this; omega
      simp only [hj0]
      exact le_refl _
    · intro j hj
      exact absurd hj (Nat.not_lt_zero _)
  · -- Nonempty prefix
    obtain ⟨i, hb, hmin, hearl⟩ := hInv.2 hP
    simp only [List.get_eq_getElem] at hb hmin hearl
    have hi := i.isLt
    have hilt : i.val < (P ++ [t]).length := by
      simp only [List.length_append, List.length_cons, List.length_nil]; omega
    by_cases hcase : (runTrial t).cost < (runTrial P[i.val]).cost
    · -- new trial wins; best becomes some (runTrial t), witness = last index
      have hstep : step b t = some (runTrial t) := by
        rw [hb]; simp only [step, if_pos hcase]
      rw [hstep]
      refine ⟨⟨P.length, by simp⟩, ?_, ?_, ?_⟩
      · simp only [List.get_eq_getElem]
        rw [List.getElem_concat_length (l := P) (a := t) rfl]
      · intro j
        simp only [List.get_eq_getElem]
        rw [List.getElem_concat_length (l := P) (a := t) rfl]
        by_cases hj : j.val < P.length
        · rw [List.getElem_append_left hj]
          have hm := hmin ⟨j.val, hj⟩
          exact le_of_lt (lt_of_lt_of_le hcase hm)
        · have hjeq : j.val = P.length := by
            have hjl := j.isLt
            simp only [List.length_append, List.length_cons, List.length_nil] at hjl
            omega
          rw [List.getElem_concat_length (l := P) (a := t) hjeq]
      · intro j hj
        simp only [List.get_eq_getElem]
        rw [List.getElem_concat_length (l := P) (a := t) rfl]
        rw [List.getElem_append_left hj]
        have hm := hmin ⟨j.val, hj⟩
        exact lt_of_lt_of_le hcase hm
    · -- old best wins; accumulator unchanged, witness = i
      push_neg at hcase
      have hstep : step b t = b := by
        rw [hb]; simp only [step, if_neg (not_lt.mpr hcase)]
      rw [hstep, hb]
      refine ⟨⟨i.val, hilt⟩, ?_, ?_, ?_⟩
      · simp only [List.get_eq_getElem]
        rw [List.getElem_append_left hi]
      · intro j
        simp only [List.get_eq_getElem]
        rw [List.getElem_append_left hi]
        by_cases hj : j.val < P.length
        · rw [List.getElem_append_left hj]
          exact hmin ⟨j.val, hj⟩
        · have hjeq : j.val = P.length := by
            have hjl := j.isLt
            simp only [List.length_append, List.length_cons, List.length_nil] at hjl
            omega
          rw [List.getElem_concat_length (l := P) (a := t) hjeq]
          exact hcase
      · intro j hj
        simp only [List.get_eq_getElem]
        rw [List.getElem_append_left hi]
        have hjP : j.val < P.length := lt_trans hj hi
        rw [List.getElem_append_left hjP]
        exact hearl ⟨j.val, hjP⟩ hj

theorem FoldInv_holds (L : List Int) : FoldInv L (L.foldl step none) := by
  induction L using List.reverseRecOn with
  | nil => exact FoldInv_init
  | append_singleton P t IH =>
    rw [List.foldl_concat]
    exact FoldInv_step P t (P.foldl step none) IH

theorem nonempty_gives_some (trials : List Int) (h : trials ≠ []) :
    ∃ iBest : Fin trials.length,
      (trials.foldl step none) = some (runTrial (trials.get iBest)) ∧
      (∀ j : Fin trials.length,
          (runTrial (trials.get iBest)).cost ≤ (runTrial (trials.get j)).cost) ∧
      (∀ j : Fin trials.length, j.val < iBest.val →
          (runTrial (trials.get iBest)).cost < (runTrial (trials.get j)).cost) :=
  (FoldInv_holds trials).2 h

theorem result_is_trial_i (trials : List Int) (iBest : Fin trials.length)
    (hfold : (trials.foldl step none) = some (runTrial (trials.get iBest))) :
    implementation_bestTrial trials = runTrial (trials.get iBest) := by
  rw [impl_eq_foldl, hfold, getD_some]

theorem correct_bestTrial :
    ∀ (trials : List Int), trials ≠ [] →
      problem_spec_bestTrial trials (implementation_bestTrial trials) := by
  intro trials h
  obtain ⟨iBest, hfold, hmin, hbefore⟩ := nonempty_gives_some trials h
  have hres := result_is_trial_i trials iBest hfold
  refine ⟨iBest, ?_, ?_, ?_⟩
  · exact hres
  · intro j; rw [hres]; exact hmin j
  · intro j hj; rw [hres]; exact hbefore j hj

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_bestTrial is a TOTAL FUNCTIONAL CHARACTERIZATION. For any nonempty `trials`, the three conjuncts jointly pin a unique output: (frame) result = runTrial (trials.get i) for some index i, both cost AND data verbatim; (global-min) no attempt has strictly lower cost; (strict-earlier) every j<i has strictly greater cost. Together these force result to be exactly the outcome of the EARLIEST global-min-cost attempt, driven by the SUPPLIED VALUE trials.get i (not the position). Because `runTrial : Int -> Outcome` is `opaque` (no _prop), any impl deviating from this must prove an unprovable equality/ordering between runTrial at different arguments, so no wrong impl can close.

SAME-SPEC: all 8 attack files + positive_control return same_spec=True via swebench_unified.markers.same_spec (lean backend); spec regions (imports/axioms/pure/pre/post, lines 1-63) left byte-identical; only impl+proof edited.

POSITIVE CONTROL: positive_control.lean (= bundle Solution.lean). `bash scripts/lean_verify.sh positive_control.lean` -> EXIT 0. `#print axioms correct_bestTrial` (pc_ax.lean) -> [propext, Classical.choice, Quot.sound], NO sorryAx. Clean close confirmed.

ATTACKS (6+ DISTINCT wrong impls; command `bash scripts/lean_verify.sh <f>`; exit 3 = elaborates but only with sorry => proof CANNOT close):
- atk_1 (boundary/no-selection: return first trial `t::_ => runTrial t`): EXIT 3.
- atk_2 (boundary: return LAST trial via reverse.head?): EXIT 3.
- atk_3 (wrong-direction: argMAX, `if o.cost > b.cost`): EXIT 3.
- atk_4 (wrong tie-break: non-strict `<=` keeps LAST minimum): EXIT 3.
- atk_5 (control-flow-effect: position-driven `runTrial (Int.ofNat p)` over [0:len] — the prepatch bug re-encoded independently): EXIT 3.
- atk_6 (partial-domain: gold on |trials|>=2 but singleton returns `runTrial 0` regardless of element): EXIT 3.
- atk_7 (ungrounded-oracle echo: constant `runTrial 0` for all inputs, no loop): EXIT 3.
- atk_prepatch (bundle Solution_prepatch.lean, position-driven with carried gold proof + sorry): EXIT 3.
NONE of the 8 closes => zero impls with a closing clean-axiom proof => `patches` is empty (nothing to materialize/resolve-run). No resolve run was required or possible.

### MACHINE-CHECKED REFUTATIONS (positive evidence the wrong behaviors provably CANNOT satisfy the spec, not merely that my tactic failed):
- ref_1.lean (first-trial impl): `refute_first` with (runTrial 0).cost=5, (runTrial 1).cost=1 on [0,1]: global-min conjunct forces 5<=1, contradiction. EXIT 0 (theorem CLOSES).
- ref_3.lean (argmax impl): `refute_argmax` with cost0=1, cost1=5 on [0,1]: impl provably returns runTrial 1 (highest), violating global-min (forces 5<=1). EXIT 0 (CLOSES).
- ref_4.lean (non-strict last-min impl): `refute_lastmin` with cost0=cost1=1, data0!=data1 on [0,1]: impl provably returns runTrial 1; frame at i=0 forces data equality (contradiction with distinct data), earliest conjunct at i=1 forces 1<1 (contradiction). EXIT 0 (CLOSES).
prepatch position-driven behavior separately: verdict.md records `implementation_bestTrial [7] = runTrial 0` by rfl while spec forces runTrial 7, unprovable under opaque runTrial — reproduced conceptually; atk_prepatch/atk_5 carry it and both fail to close (EXIT 3).

REFINEMENT.MD LEG AUDIT (§4 correspondence): 4 legs, all R / A-reference / I, NO kind-3, NO A-consumed.
- L1 `trials : List Int` <- `seeds = random_state.randint(..., size=n_init)`: R (input; RNG unchanged in value, patch only HOISTS the line above the branch; not modeled). OK.
- L2 `for t in trials do let o := runTrial t` <- `for seed in seeds: kmeans_single(..., random_state=seed)`: A-REFERENCE — THE sole edited op (value-driven vs shared-random_state). kmeans_single is the UNCHANGED callee, modeled `opaque runTrial` with NO _prop (proof consumes no property; argmin selection holds for ANY function). Correspondence to real callee holds; G-AX is a justified skip stub; drift left to G-CONF. OK.
- L3 running-best strict-`<` update <- `if best_inertia is None or inertia < best_inertia`: I (strict < => first minimum kept, matching np.argmin first-occurrence in parallel branch). OK.
- L4 `return best.getD default` <- `return best_labels, best_inertia, ...`: R (whole chosen outcome returned verbatim; frame: all components from one runTrial). OK.
Outcome.cost:Int is an ORDER-ONLY refinement of inertia:float (only < / argmin observed) — sound, fuzzed by G-CONF. No A-leg over-claims about kmeans_single. Correspondence sound.

CONCLUSION: The spec is a total functional characterization discriminating the value-driven gold (frame clause result = runTrial (trials.get i)) from the position-driven prepatch bug and every other deviation. >=8 distinct same-spec wrong impls were genuinely attempted; none closes; 3 are machine-checked-refuted as provably spec-violating. No closing-clean-axiom wrong impl exists, hence no faithful non-resolving patch. verify=>correct. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for scikit-learn__scikit-learn-9288 lean bundle.

### Verification performed
1. lean_verify.sh on Solution.lean => exit 0 (compiles, no sorry/admit).
2. #print axioms correct_bestTrial => [propext, Classical.choice, Quot.sound]; implementation_bestTrial => [propext]. No sorryAx => proof is real, not fake.
3. same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) => True: the spec region (structure Outcome, opaque runTrial, problem_spec_bestTrial) is byte-identical; the prepatch differs only in the impl region (loop driven by position Int.ofNat p instead of trials.get p), so this is a genuine impl/proof-only mutation.

### MODEL vs REAL CALLEE:
Modeled function = single-thread best-of-n_init selection loop in sklearn.cluster.k_means_.k_means (effective_n_jobs==1 branch). runTrial = kmeans_single (opaque, A-reference; proof consumes no property of it, no _prop axiom asserted — correct given selection holds for ANY attempt routine). Outcome.cost:Int is an ORDER-ONLY refinement of inertia:float (only < / argmin observed).

The spec's postcondition (exists i: result = runTrial(trials.get i) AND global-min cost AND every earlier j strictly greater cost) pins exactly the earliest index attaining the global minimum. Exhaustive check over all cost tuples of length 1..6 in [-2,2]: the spec's witness set equals exactly {real serial running-best index} in every case (0 mismatches). The real serial idiom uses strict `<` (keep first minimum) and the parallel branch uses np.argmin (first occurrence) — both agree with the spec. conformance_check.py differential-tests shadow==real_serial==real_parallel over 6 discrete + 120000 fuzzed streams with frequent cost collisions.

Empty list: excluded by precondition trials != [] (n_init >= 1 in the real callee, seeds is never empty), so no divergence there.

No input found where the modeled function disagrees with the real callee. The spec is neither too strong nor drifted. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the solver-visible problem_statement ONLY (hints_text excluded, which is where the actual fix mechanism 'set random_state to be the same in both cases' lives).

Gold edit (patch.diff): in sklearn/cluster/k_means_.py, hoist `seeds = random_state.randint(np.iinfo(np.int32).max, size=n_init)` above the n_jobs branch and change the serial branch from `for it in range(n_init): ... random_state=random_state` to `for seed in seeds: ... random_state=seed`, so the serial branch consumes the same seed array as the parallel branch.

Spec view (recomputed via markers.spec_view) is fully abstracted: 'selecting the best (lowest-cost) outcome among independent repeated attempts, each driven by its own supplied configuration value; result is a deterministic function of the supplied list and independent of how the work is distributed.' It contains NO KMeans/clustering/seeds/random_state/n_jobs/n_init terms, no patched file path (k_means_.py) or module, no distinctive changed symbol (only distinctive symbol is `k_means`, absent), no reproduced gold line, no diff markers, no narration. Identifiers (runTrial, Outcome, bestTrial, trials) echo nothing in the patch.

The distribution/order-independence phrasing is the specification of correct behavior and the n_jobs-invariance is already public in problem_statement; it does not localize the edit to a code site or name the fix mechanism. A solver with problem_statement + this spec view cannot reconstruct the specific gold edit.

Verification performed:
- leakage.screen() -> passed=True, hard_failures=[] (changed symbols = ['k_means']).
- markers.same_spec(Solution.lean, Solution_prepatch.lean, lean) = True: spec region byte-identical; the pre/post differential lives entirely in the impl/proof regions (which are elided from the solver spec view). No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
