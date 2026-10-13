# P2 adversarial audit — sympy__sympy-19954

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — spec holds. The spec is an exact functional equality problem_spec := (result = pruneSystems ...) over deeply-modeled pure functions (scanReps/dropFlagged/pruneSystems), the tightest possible shape. Only a behavioral echo of the gold verifies, and its faithful patch resolves. Concrete divergence witnesses (machine-checked #eval, exit 0) prove every wrong impl differs from the oracle: atk_1 (>= for >): rep={0,1},r0={0,1} card-equal → gold keeps+appends ([[0,1],[9]],...) vs impl supersedes ([[9]],...). atk_2 (no break on dominate): repBlocks=[{0},{0,1,2}],rep={0,1} → gold rejects+keeps both ([[0],[1]],...) vs impl prunes r1 ([[0]],...). atk_3 (skip append when repBlocks empty): gold ([[9]],[[7]],[{0,1}]) vs impl ([],[],[]). atk_4 (dedup over UNpruned numBlocks): superseded row carries colliding numBlock → gold appends vs impl blocks it ([[9]],...) vs ([],...). atk_5 (drop rep append): repBlocks' ([{0,1}]) vs ([]). atk_6 (subset direction swap): gold supersedes r0 vs impl keeps it ([[9]],[[7]],[{0}]) vs ([[0],[9]],...).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -111,7 +111,7 @@
   let mut minimal := true
   let mut mask : List Bool := []
   for r in repBlocks do
-    if r.card > rep.card && rep ⊆ r then
+    if r.card >= rep.card && rep ⊆ r then
       mask := mask ++ [true]
     else if r.card < rep.card && r ⊆ rep then
       minimal := false
@@ -130,153 +130,12 @@
 
 
 -- proof-start
-/-- Loop invariant relating the running `(mask, minimal)` to `scanReps` for a
-processed prefix `pre` with remaining suffix `suf`. While `minimal = true`, no
-dominating cell has been seen in `pre`, `mask` equals the mask-part `scanReps`
-produces on `pre`, and `scanReps` on the full list splits as the accumulated
-mask followed by the suffix's scan. Once `minimal = false`, a dominating cell
-was hit (the loop broke) and the full scan is the accumulated mask padded with
-`false` over the remaining suffix. -/
-def LoopState (rep : Finset Nat) (pre suf : List (Finset Nat))
-    (mask : List Bool) (minimal : Bool) : Prop :=
-  (minimal = true →
-      mask = (scanReps rep pre).1 ∧
-      scanReps rep (pre ++ suf) = (mask ++ (scanReps rep suf).1, (scanReps rep suf).2)) ∧
-  (minimal = false →
-      scanReps rep (pre ++ suf) = (mask ++ List.replicate suf.length false, false))
-
-theorem scanReps_cons_super (rep r : Finset Nat) (rs : List (Finset Nat))
-    (h : supersededBy rep r = true) :
-    scanReps rep (r :: rs) = (true :: (scanReps rep rs).1, (scanReps rep rs).2) := by
-  simp only [scanReps, h, if_true]
-
-theorem scanReps_cons_dom (rep r : Finset Nat) (rs : List (Finset Nat))
-    (h1 : supersededBy rep r = false) (h2 : dominates rep r = true) :
-    scanReps rep (r :: rs) = (false :: List.replicate rs.length false, false) := by
-  unfold scanReps
-  simp only [h1, h2, if_false, if_true, Bool.false_eq_true]
-
-theorem scanReps_cons_neither (rep r : Finset Nat) (rs : List (Finset Nat))
-    (h1 : supersededBy rep r = false) (h2 : dominates rep r = false) :
-    scanReps rep (r :: rs) = (false :: (scanReps rep rs).1, (scanReps rep rs).2) := by
-  conv_lhs => rw [scanReps]
-  simp only [h1, h2, Bool.false_eq_true, if_false]
-
-theorem scanReps_mask_length (rep : Finset Nat) (rs : List (Finset Nat)) :
-    (scanReps rep rs).1.length = rs.length := by
-  induction rs with
-  | nil => rfl
-  | cons r rs ih =>
-    by_cases hs : supersededBy rep r = true
-    · rw [scanReps_cons_super rep r rs hs]
-      simp [ih]
-    · simp only [Bool.not_eq_true] at hs
-      by_cases hd : dominates rep r = true
-      · rw [scanReps_cons_dom rep r rs hs hd]
-        simp
-      · simp only [Bool.not_eq_true] at hd
-        rw [scanReps_cons_neither rep r rs hs hd]
-        simp [ih]
-
-theorem forIn_reifies_scan (rep : Finset Nat) :
-    ∀ (L : List (Finset Nat)) (acc : List Bool),
-      (Id.run do
-        let mut minimal := true
-        let mut mask : List Bool := acc
-        for r in L do
-          if r.card > rep.card && rep ⊆ r then
-            mask := mask ++ [true]
-          else if r.card < rep.card && r ⊆ rep then
-            minimal := false
-            break
-          else
-            mask := mask ++ [false]
-        mask := mask ++ List.replicate (acc.length + L.length - mask.length) false
-        return (mask, minimal))
-        = (acc ++ (scanReps rep L).1, (scanReps rep L).2) := by
-  intro L
-  induction L with
-  | nil => intro acc; simp [scanReps, Id.run, bind, pure]
-  | cons r rs ih =>
-    intro acc
-    simp only [List.forIn_cons, bind, pure, Id.run]
-    split_ifs with h1 h2
-    · -- superseded: mask ++ [true], continue
-      have hs : supersededBy rep r = true := h1
-      rw [scanReps_cons_super rep r rs hs]
-      have hih := ih (acc ++ [true])
-      simp only [bind, pure, Id.run] at hih
-      dsimp only
-      rw [show acc.length + (r::rs).length = (acc++[true]).length + rs.length by simp; omega]
-      rw [hih]; simp [List.append_assoc]
-    · -- dominated: break
-      have hs : supersededBy rep r = false := by
-        simpa [supersededBy] using h1
-      have hd : dominates rep r = true := by
-        simpa [dominates] using h2
-      rw [scanReps_cons_dom rep r rs hs hd]
-      dsimp only
-      rw [show acc.length + (r::rs).length - acc.length = rs.length + 1 by simp]
-      rw [List.replicate_succ]
-    · -- neither: mask ++ [false], continue
-      have hs : supersededBy rep r = false := by
-        simpa [supersededBy] using h1
-      have hnd : dominates rep r = false := by
-        simpa [dominates] using h2
-      rw [scanReps_cons_neither rep r rs hs hnd]
-      have hih := ih (acc ++ [false])
-      simp only [bind, pure, Id.run] at hih
-      dsimp only
-      rw [show acc.length + (r::rs).length = (acc++[false]).length + rs.length by simp; omega]
-      rw [hih]; simp [List.append_assoc]
-
-theorem loop_scan_eq (rep : Finset Nat) (repBlocks : List (Finset Nat)) :
-    (Id.run do
-      let mut minimal := true
-      let mut mask : List Bool := []
-      for r in repBlocks do
-        if r.card > rep.card && rep ⊆ r then
-          mask := mask ++ [true]
-        else if r.card < rep.card && r ⊆ rep then
-          minimal := false
-          break
-        else
-          mask := mask ++ [false]
-      mask := mask ++ List.replicate (repBlocks.length - mask.length) false
-      return (mask, minimal))
-      = scanReps rep repBlocks := by
-  have h := forIn_reifies_scan rep repBlocks []
-  simpa using h
-
-theorem tail_eq (blocks : List (List Int)) (numBlocks : List (List Nat))
-    (repBlocks : List (Finset Nat)) (block : List Int) (numBlock : List Nat) (rep : Finset Nat)
-    (hloop : (Id.run do
-      let mut minimal := true
-      let mut mask : List Bool := []
-      for r in repBlocks do
-        if r.card > rep.card && rep ⊆ r then
-          mask := mask ++ [true]
-        else if r.card < rep.card && r ⊆ rep then
-          minimal := false
-          break
-        else
-          mask := mask ++ [false]
-      mask := mask ++ List.replicate (repBlocks.length - mask.length) false
-      return (mask, minimal))
-      = scanReps rep repBlocks) :
-    implementation_pruneSystems blocks numBlocks repBlocks block numBlock rep
-      = pruneSystems blocks numBlocks repBlocks block numBlock rep := by
-  unfold implementation_pruneSystems pruneSystems
-  rw [← hloop]
-  rfl
-
 theorem correct_pruneSystems :
     ∀ (blocks : List (List Int)) (numBlocks : List (List Nat)) (repBlocks : List (Finset Nat))
       (block : List Int) (numBlock : List Nat) (rep : Finset Nat),
       problem_spec_pruneSystems blocks numBlocks repBlocks block numBlock rep
         (implementation_pruneSystems blocks numBlocks repBlocks block numBlock rep) := by
   intro blocks numBlocks repBlocks block numBlock rep
-  unfold problem_spec_pruneSystems
-  exact tail_eq blocks numBlocks repBlocks block numBlock rep (loop_scan_eq rep repBlocks)
-
+  unfold problem_spec_pruneSystems implementation_pruneSystems pruneSystems
+  rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -115,7 +115,7 @@
       mask := mask ++ [true]
     else if r.card < rep.card && r ⊆ rep then
       minimal := false
-      break
+      mask := mask ++ [false]
     else
       mask := mask ++ [false]
   mask := mask ++ List.replicate (repBlocks.length - mask.length) false
@@ -130,153 +130,12 @@
 
 
 -- proof-start
-/-- Loop invariant relating the running `(mask, minimal)` to `scanReps` for a
-processed prefix `pre` with remaining suffix `suf`. While `minimal = true`, no
-dominating cell has been seen in `pre`, `mask` equals the mask-part `scanReps`
-produces on `pre`, and `scanReps` on the full list splits as the accumulated
-mask followed by the suffix's scan. Once `minimal = false`, a dominating cell
-was hit (the loop broke) and the full scan is the accumulated mask padded with
-`false` over the remaining suffix. -/
-def LoopState (rep : Finset Nat) (pre suf : List (Finset Nat))
-    (mask : List Bool) (minimal : Bool) : Prop :=
-  (minimal = true →
-      mask = (scanReps rep pre).1 ∧
-      scanReps rep (pre ++ suf) = (mask ++ (scanReps rep suf).1, (scanReps rep suf).2)) ∧
-  (minimal = false →
-      scanReps rep (pre ++ suf) = (mask ++ List.replicate suf.length false, false))
-
-theorem scanReps_cons_super (rep r : Finset Nat) (rs : List (Finset Nat))
-    (h : supersededBy rep r = true) :
-    scanReps rep (r :: rs) = (true :: (scanReps rep rs).1, (scanReps rep rs).2) := by
-  simp only [scanReps, h, if_true]
-
-theorem scanReps_cons_dom (rep r : Finset Nat) (rs : List (Finset Nat))
-    (h1 : supersededBy rep r = false) (h2 : dominates rep r = true) :
-    scanReps rep (r :: rs) = (false :: List.replicate rs.length false, false) := by
-  unfold scanReps
-  simp only [h1, h2, if_false, if_true, Bool.false_eq_true]
-
-theorem scanReps_cons_neither (rep r : Finset Nat) (rs : List (Finset Nat))
-    (h1 : supersededBy rep r = false) (h2 : dominates rep r = false) :
-    scanReps rep (r :: rs) = (false :: (scanReps rep rs).1, (scanReps rep rs).2) := by
-  conv_lhs => rw [scanReps]
-  simp only [h1, h2, Bool.false_eq_true, if_false]
-
-theorem scanReps_mask_length (rep : Finset Nat) (rs : List (Finset Nat)) :
-    (scanReps rep rs).1.length = rs.length := by
-  induction rs with
-  | nil => rfl
-  | cons r rs ih =>
-    by_cases hs : supersededBy rep r = true
-    · rw [scanReps_cons_super rep r rs hs]
-      simp [ih]
-    · simp only [Bool.not_eq_true] at hs
-      by_cases hd : dominates rep r = true
-      · rw [scanReps_cons_dom rep r rs hs hd]
-        simp
-      · simp only [Bool.not_eq_true] at hd
-        rw [scanReps_cons_neither rep r rs hs hd]
-        simp [ih]
-
-theorem forIn_reifies_scan (rep : Finset Nat) :
-    ∀ (L : List (Finset Nat)) (acc : List Bool),
-      (Id.run do
-        let mut minimal := true
-        let mut mask : List Bool := acc
-        for r in L do
-          if r.card > rep.card && rep ⊆ r then
-            mask := mask ++ [true]
-          else if r.card < rep.card && r ⊆ rep then
-            minimal := false
-            break
-          else
-            mask := mask ++ [false]
-        mask := mask ++ List.replicate (acc.length + L.length - mask.length) false
-        return (mask, minimal))
-        = (acc ++ (scanReps rep L).1, (scanReps rep L).2) := by
-  intro L
-  induction L with
-  | nil => intro acc; simp [scanReps, Id.run, bind, pure]
-  | cons r rs ih =>
-    intro acc
-    simp only [List.forIn_cons, bind, pure, Id.run]
-    split_ifs with h1 h2
-    · -- superseded: mask ++ [true], continue
-      have hs : supersededBy rep r = true := h1
-      rw [scanReps_cons_super rep r rs hs]
-      have hih := ih (acc ++ [true])
-      simp only [bind, pure, Id.run] at hih
-      dsimp only
-      rw [show acc.length + (r::rs).length = (acc++[true]).length + rs.length by simp; omega]
-      rw [hih]; simp [List.append_assoc]
-    · -- dominated: break
-      have hs : supersededBy rep r = false := by
-        simpa [supersededBy] using h1
-      have hd : dominates rep r = true := by
-        simpa [dominates] using h2
-      rw [scanReps_cons_dom rep r rs hs hd]
-      dsimp only
-      rw [show acc.length + (r::rs).length - acc.length = rs.length + 1 by simp]
-      rw [List.replicate_succ]
-    · -- neither: mask ++ [false], continue
-      have hs : supersededBy rep r = false := by
-        simpa [supersededBy] using h1
-      have hnd : dominates rep r = false := by
-        simpa [dominates] using h2
-      rw [scanReps_cons_neither rep r rs hs hnd]
-      have hih := ih (acc ++ [false])
-      simp only [bind, pure, Id.run] at hih
-      dsimp only
-      rw [show acc.length + (r::rs).length = (acc++[false]).length + rs.length by simp; omega]
-      rw [hih]; simp [List.append_assoc]
-
-theorem loop_scan_eq (rep : Finset Nat) (repBlocks : List (Finset Nat)) :
-    (Id.run do
-      let mut minimal := true
-      let mut mask : List Bool := []
-      for r in repBlocks do
-        if r.card > rep.card && rep ⊆ r then
-          mask := mask ++ [true]
-        else if r.card < rep.card && r ⊆ rep then
-          minimal := false
-          break
-        else
-          mask := mask ++ [false]
-      mask := mask ++ List.replicate (repBlocks.length - mask.length) false
-      return (mask, minimal))
-      = scanReps rep repBlocks := by
-  have h := forIn_reifies_scan rep repBlocks []
-  simpa using h
-
-theorem tail_eq (blocks : List (List Int)) (numBlocks : List (List Nat))
-    (repBlocks : List (Finset Nat)) (block : List Int) (numBlock : List Nat) (rep : Finset Nat)
-    (hloop : (Id.run do
-      let mut minimal := true
-      let mut mask : List Bool := []
-      for r in repBlocks do
-        if r.card > rep.card && rep ⊆ r then
-          mask := mask ++ [true]
-        else if r.card < rep.card && r ⊆ rep then
-          minimal := false
-          break
-        else
-          mask := mask ++ [false]
-      mask := mask ++ List.replicate (repBlocks.length - mask.length) false
-      return (mask, minimal))
-      = scanReps rep repBlocks) :
-    implementation_pruneSystems blocks numBlocks repBlocks block numBlock rep
-      = pruneSystems blocks numBlocks repBlocks block numBlock rep := by
-  unfold implementation_pruneSystems pruneSystems
-  rw [← hloop]
-  rfl
-
 theorem correct_pruneSystems :
     ∀ (blocks : List (List Int)) (numBlocks : List (List Nat)) (repBlocks : List (Finset Nat))
       (block : List Int) (numBlock : List Nat) (rep : Finset Nat),
       problem_spec_pruneSystems blocks numBlocks repBlocks block numBlock rep
         (implementation_pruneSystems blocks numBlocks repBlocks block numBlock rep) := by
   intro blocks numBlocks repBlocks block numBlock rep
-  unfold problem_spec_pruneSystems
-  exact tail_eq blocks numBlocks repBlocks block numBlock rep (loop_scan_eq rep repBlocks)
-
+  unfold problem_spec_pruneSystems implementation_pruneSystems pruneSystems
+  rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,6 +108,8 @@
     (blocks : List (List Int)) (numBlocks : List (List Nat)) (repBlocks : List (Finset Nat))
     (block : List Int) (numBlock : List Nat) (rep : Finset Nat) :
     List (List Int) × List (List Nat) × List (Finset Nat) := Id.run do
+  if repBlocks.isEmpty then
+    return (blocks, numBlocks, repBlocks)
   let mut minimal := true
   let mut mask : List Bool := []
   for r in repBlocks do
@@ -130,153 +132,12 @@
 
 
 -- proof-start
-/-- Loop invariant relating the running `(mask, minimal)` to `scanReps` for a
-processed prefix `pre` with remaining suffix `suf`. While `minimal = true`, no
-dominating cell has been seen in `pre`, `mask` equals the mask-part `scanReps`
-produces on `pre`, and `scanReps` on the full list splits as the accumulated
-mask followed by the suffix's scan. Once `minimal = false`, a dominating cell
-was hit (the loop broke) and the full scan is the accumulated mask padded with
-`false` over the remaining suffix. -/
-def LoopState (rep : Finset Nat) (pre suf : List (Finset Nat))
-    (mask : List Bool) (minimal : Bool) : Prop :=
-  (minimal = true →
-      mask = (scanReps rep pre).1 ∧
-      scanReps rep (pre ++ suf) = (mask ++ (scanReps rep suf).1, (scanReps rep suf).2)) ∧
-  (minimal = false →
-      scanReps rep (pre ++ suf) = (mask ++ List.replicate suf.length false, false))
-
-theorem scanReps_cons_super (rep r : Finset Nat) (rs : List (Finset Nat))
-    (h : supersededBy rep r = true) :
-    scanReps rep (r :: rs) = (true :: (scanReps rep rs).1, (scanReps rep rs).2) := by
-  simp only [scanReps, h, if_true]
-
-theorem scanReps_cons_dom (rep r : Finset Nat) (rs : List (Finset Nat))
-    (h1 : supersededBy rep r = false) (h2 : dominates rep r = true) :
-    scanReps rep (r :: rs) = (false :: List.replicate rs.length false, false) := by
-  unfold scanReps
-  simp only [h1, h2, if_false, if_true, Bool.false_eq_true]
-
-theorem scanReps_cons_neither (rep r : Finset Nat) (rs : List (Finset Nat))
-    (h1 : supersededBy rep r = false) (h2 : dominates rep r = false) :
-    scanReps rep (r :: rs) = (false :: (scanReps rep rs).1, (scanReps rep rs).2) := by
-  conv_lhs => rw [scanReps]
-  simp only [h1, h2, Bool.false_eq_true, if_false]
-
-theorem scanReps_mask_length (rep : Finset Nat) (rs : List (Finset Nat)) :
-    (scanReps rep rs).1.length = rs.length := by
-  induction rs with
-  | nil => rfl
-  | cons r rs ih =>
-    by_cases hs : supersededBy rep r = true
-    · rw [scanReps_cons_super rep r rs hs]
-      simp [ih]
-    · simp only [Bool.not_eq_true] at hs
-      by_cases hd : dominates rep r = true
-      · rw [scanReps_cons_dom rep r rs hs hd]
-        simp
-      · simp only [Bool.not_eq_true] at hd
-        rw [scanReps_cons_neither rep r rs hs hd]
-        simp [ih]
-
-theorem forIn_reifies_scan (rep : Finset Nat) :
-    ∀ (L : List (Finset Nat)) (acc : List Bool),
-      (Id.run do
-        let mut minimal := true
-        let mut mask : List Bool := acc
-        for r in L do
-          if r.card > rep.card && rep ⊆ r then
-            mask := mask ++ [true]
-          else if r.card < rep.card && r ⊆ rep then
-            minimal := false
-            break
-          else
-            mask := mask ++ [false]
-        mask := mask ++ List.replicate (acc.length + L.length - mask.length) false
-        return (mask, minimal))
-        = (acc ++ (scanReps rep L).1, (scanReps rep L).2) := by
-  intro L
-  induction L with
-  | nil => intro acc; simp [scanReps, Id.run, bind, pure]
-  | cons r rs ih =>
-    intro acc
-    simp only [List.forIn_cons, bind, pure, Id.run]
-    split_ifs with h1 h2
-    · -- superseded: mask ++ [true], continue
-      have hs : supersededBy rep r = true := h1
-      rw [scanReps_cons_super rep r rs hs]
-      have hih := ih (acc ++ [true])
-      simp only [bind, pure, Id.run] at hih
-      dsimp only
-      rw [show acc.length + (r::rs).length = (acc++[true]).length + rs.length by simp; omega]
-      rw [hih]; simp [List.append_assoc]
-    · -- dominated: break
-      have hs : supersededBy rep r = false := by
-        simpa [supersededBy] using h1
-      have hd : dominates rep r = true := by
-        simpa [dominates] using h2
-      rw [scanReps_cons_dom rep r rs hs hd]
-      dsimp only
-      rw [show acc.length + (r::rs).length - acc.length = rs.length + 1 by simp]
-      rw [List.replicate_succ]
-    · -- neither: mask ++ [false], continue
-      have hs : supersededBy rep r = false := by
-        simpa [supersededBy] using h1
-      have hnd : dominates rep r = false := by
-        simpa [dominates] using h2
-      rw [scanReps_cons_neither rep r rs hs hnd]
-      have hih := ih (acc ++ [false])
-      simp only [bind, pure, Id.run] at hih
-      dsimp only
-      rw [show acc.length + (r::rs).length = (acc++[false]).length + rs.length by simp; omega]
-      rw [hih]; simp [List.append_assoc]
-
-theorem loop_scan_eq (rep : Finset Nat) (repBlocks : List (Finset Nat)) :
-    (Id.run do
-      let mut minimal := true
-      let mut mask : List Bool := []
-      for r in repBlocks do
-        if r.card > rep.card && rep ⊆ r then
-          mask := mask ++ [true]
-        else if r.card < rep.card && r ⊆ rep then
-          minimal := false
-          break
-        else
-          mask := mask ++ [false]
-      mask := mask ++ List.replicate (repBlocks.length - mask.length) false
-      return (mask, minimal))
-      = scanReps rep repBlocks := by
-  have h := forIn_reifies_scan rep repBlocks []
-  simpa using h
-
-theorem tail_eq (blocks : List (List Int)) (numBlocks : List (List Nat))
-    (repBlocks : List (Finset Nat)) (block : List Int) (numBlock : List Nat) (rep : Finset Nat)
-    (hloop : (Id.run do
-      let mut minimal := true
-      let mut mask : List Bool := []
-      for r in repBlocks do
-        if r.card > rep.card && rep ⊆ r then
-          mask := mask ++ [true]
-        else if r.card < rep.card && r ⊆ rep then
-          minimal := false
-          break
-        else
-          mask := mask ++ [false]
-      mask := mask ++ List.replicate (repBlocks.length - mask.length) false
-      return (mask, minimal))
-      = scanReps rep repBlocks) :
-    implementation_pruneSystems blocks numBlocks repBlocks block numBlock rep
-      = pruneSystems blocks numBlocks repBlocks block numBlock rep := by
-  unfold implementation_pruneSystems pruneSystems
-  rw [← hloop]
-  rfl
-
 theorem correct_pruneSystems :
     ∀ (blocks : List (List Int)) (numBlocks : List (List Nat)) (repBlocks : List (Finset Nat))
       (block : List Int) (numBlock : List Nat) (rep : Finset Nat),
       problem_spec_pruneSystems blocks numBlocks repBlocks block numBlock rep
         (implementation_pruneSystems blocks numBlocks repBlocks block numBlock rep) := by
   intro blocks numBlocks repBlocks block numBlock rep
-  unfold problem_spec_pruneSystems
-  exact tail_eq blocks numBlocks repBlocks block numBlock rep (loop_scan_eq rep repBlocks)
-
+  unfold problem_spec_pruneSystems implementation_pruneSystems pruneSystems
+  rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -122,7 +122,7 @@
   let blocks' := dropFlagged blocks mask
   let numBlocks' := dropFlagged numBlocks mask
   let repBlocks' := dropFlagged repBlocks mask
-  if minimal && !(numBlocks'.contains numBlock) then
+  if minimal && !(numBlocks.contains numBlock) then
     return (blocks' ++ [block], numBlocks' ++ [numBlock], repBlocks' ++ [rep])
   else
     return (blocks', numBlocks', repBlocks')
@@ -130,153 +130,12 @@
 
 
 -- proof-start
-/-- Loop invariant relating the running `(mask, minimal)` to `scanReps` for a
-processed prefix `pre` with remaining suffix `suf`. While `minimal = true`, no
-dominating cell has been seen in `pre`, `mask` equals the mask-part `scanReps`
-produces on `pre`, and `scanReps` on the full list splits as the accumulated
-mask followed by the suffix's scan. Once `minimal = false`, a dominating cell
-was hit (the loop broke) and the full scan is the accumulated mask padded with
-`false` over the remaining suffix. -/
-def LoopState (rep : Finset Nat) (pre suf : List (Finset Nat))
-    (mask : List Bool) (minimal : Bool) : Prop :=
-  (minimal = true →
-      mask = (scanReps rep pre).1 ∧
-      scanReps rep (pre ++ suf) = (mask ++ (scanReps rep suf).1, (scanReps rep suf).2)) ∧
-  (minimal = false →
-      scanReps rep (pre ++ suf) = (mask ++ List.replicate suf.length false, false))
-
-theorem scanReps_cons_super (rep r : Finset Nat) (rs : List (Finset Nat))
-    (h : supersededBy rep r = true) :
-    scanReps rep (r :: rs) = (true :: (scanReps rep rs).1, (scanReps rep rs).2) := by
-  simp only [scanReps, h, if_true]
-
-theorem scanReps_cons_dom (rep r : Finset Nat) (rs : List (Finset Nat))
-    (h1 : supersededBy rep r = false) (h2 : dominates rep r = true) :
-    scanReps rep (r :: rs) = (false :: List.replicate rs.length false, false) := by
-  unfold scanReps
-  simp only [h1, h2, if_false, if_true, Bool.false_eq_true]
-
-theorem scanReps_cons_neither (rep r : Finset Nat) (rs : List (Finset Nat))
-    (h1 : supersededBy rep r = false) (h2 : dominates rep r = false) :
-    scanReps rep (r :: rs) = (false :: (scanReps rep rs).1, (scanReps rep rs).2) := by
-  conv_lhs => rw [scanReps]
-  simp only [h1, h2, Bool.false_eq_true, if_false]
-
-theorem scanReps_mask_length (rep : Finset Nat) (rs : List (Finset Nat)) :
-    (scanReps rep rs).1.length = rs.length := by
-  induction rs with
-  | nil => rfl
-  | cons r rs ih =>
-    by_cases hs : supersededBy rep r = true
-    · rw [scanReps_cons_super rep r rs hs]
-      simp [ih]
-    · simp only [Bool.not_eq_true] at hs
-      by_cases hd : dominates rep r = true
-      · rw [scanReps_cons_dom rep r rs hs hd]
-        simp
-      · simp only [Bool.not_eq_true] at hd
-        rw [scanReps_cons_neither rep r rs hs hd]
-        simp [ih]
-
-theorem forIn_reifies_scan (rep : Finset Nat) :
-    ∀ (L : List (Finset Nat)) (acc : List Bool),
-      (Id.run do
-        let mut minimal := true
-        let mut mask : List Bool := acc
-        for r in L do
-          if r.card > rep.card && rep ⊆ r then
-            mask := mask ++ [true]
-          else if r.card < rep.card && r ⊆ rep then
-            minimal := false
-            break
-          else
-            mask := mask ++ [false]
-        mask := mask ++ List.replicate (acc.length + L.length - mask.length) false
-        return (mask, minimal))
-        = (acc ++ (scanReps rep L).1, (scanReps rep L).2) := by
-  intro L
-  induction L with
-  | nil => intro acc; simp [scanReps, Id.run, bind, pure]
-  | cons r rs ih =>
-    intro acc
-    simp only [List.forIn_cons, bind, pure, Id.run]
-    split_ifs with h1 h2
-    · -- superseded: mask ++ [true], continue
-      have hs : supersededBy rep r = true := h1
-      rw [scanReps_cons_super rep r rs hs]
-      have hih := ih (acc ++ [true])
-      simp only [bind, pure, Id.run] at hih
-      dsimp only
-      rw [show acc.length + (r::rs).length = (acc++[true]).length + rs.length by simp; omega]
-      rw [hih]; simp [List.append_assoc]
-    · -- dominated: break
-      have hs : supersededBy rep r = false := by
-        simpa [supersededBy] using h1
-      have hd : dominates rep r = true := by
-        simpa [dominates] using h2
-      rw [scanReps_cons_dom rep r rs hs hd]
-      dsimp only
-      rw [show acc.length + (r::rs).length - acc.length = rs.length + 1 by simp]
-      rw [List.replicate_succ]
-    · -- neither: mask ++ [false], continue
-      have hs : supersededBy rep r = false := by
-        simpa [supersededBy] using h1
-      have hnd : dominates rep r = false := by
-        simpa [dominates] using h2
-      rw [scanReps_cons_neither rep r rs hs hnd]
-      have hih := ih (acc ++ [false])
-      simp only [bind, pure, Id.run] at hih
-      dsimp only
-      rw [show acc.length + (r::rs).length = (acc++[false]).length + rs.length by simp; omega]
-      rw [hih]; simp [List.append_assoc]
-
-theorem loop_scan_eq (rep : Finset Nat) (repBlocks : List (Finset Nat)) :
-    (Id.run do
-      let mut minimal := true
-      let mut mask : List Bool := []
-      for r in repBlocks do
-        if r.card > rep.card && rep ⊆ r then
-          mask := mask ++ [true]
-        else if r.card < rep.card && r ⊆ rep then
-          minimal := false
-          break
-        else
-          mask := mask ++ [false]
-      mask := mask ++ List.replicate (repBlocks.length - mask.length) false
-      return (mask, minimal))
-      = scanReps rep repBlocks := by
-  have h := forIn_reifies_scan rep repBlocks []
-  simpa using h
-
-theorem tail_eq (blocks : List (List Int)) (numBlocks : List (List Nat))
-    (repBlocks : List (Finset Nat)) (block : List Int) (numBlock : List Nat) (rep : Finset Nat)
-    (hloop : (Id.run do
-      let mut minimal := true
-      let mut mask : List Bool := []
-      for r in repBlocks do
-        if r.card > rep.card && rep ⊆ r then
-          mask := mask ++ [true]
-        else if r.card < rep.card && r ⊆ rep then
-          minimal := false
-          break
-        else
-          mask := mask ++ [false]
-      mask := mask ++ List.replicate (repBlocks.length - mask.length) false
-      return (mask, minimal))
-      = scanReps rep repBlocks) :
-    implementation_pruneSystems blocks numBlocks repBlocks block numBlock rep
-      = pruneSystems blocks numBlocks repBlocks block numBlock rep := by
-  unfold implementation_pruneSystems pruneSystems
-  rw [← hloop]
-  rfl
-
 theorem correct_pruneSystems :
     ∀ (blocks : List (List Int)) (numBlocks : List (List Nat)) (repBlocks : List (Finset Nat))
       (block : List Int) (numBlock : List Nat) (rep : Finset Nat),
       problem_spec_pruneSystems blocks numBlocks repBlocks block numBlock rep
         (implementation_pruneSystems blocks numBlocks repBlocks block numBlock rep) := by
   intro blocks numBlocks repBlocks block numBlock rep
-  unfold problem_spec_pruneSystems
-  exact tail_eq blocks numBlocks repBlocks block numBlock rep (loop_scan_eq rep repBlocks)
-
+  unfold problem_spec_pruneSystems implementation_pruneSystems pruneSystems
+  rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -123,160 +123,19 @@
   let numBlocks' := dropFlagged numBlocks mask
   let repBlocks' := dropFlagged repBlocks mask
   if minimal && !(numBlocks'.contains numBlock) then
-    return (blocks' ++ [block], numBlocks' ++ [numBlock], repBlocks' ++ [rep])
+    return (blocks' ++ [block], numBlocks' ++ [numBlock], repBlocks')
   else
     return (blocks', numBlocks', repBlocks')
 -- impl-end
 
 
 -- proof-start
-/-- Loop invariant relating the running `(mask, minimal)` to `scanReps` for a
-processed prefix `pre` with remaining suffix `suf`. While `minimal = true`, no
-dominating cell has been seen in `pre`, `mask` equals the mask-part `scanReps`
-produces on `pre`, and `scanReps` on the full list splits as the accumulated
-mask followed by the suffix's scan. Once `minimal = false`, a dominating cell
-was hit (the loop broke) and the full scan is the accumulated mask padded with
-`false` over the remaining suffix. -/
-def LoopState (rep : Finset Nat) (pre suf : List (Finset Nat))
-    (mask : List Bool) (minimal : Bool) : Prop :=
-  (minimal = true →
-      mask = (scanReps rep pre).1 ∧
-      scanReps rep (pre ++ suf) = (mask ++ (scanReps rep suf).1, (scanReps rep suf).2)) ∧
-  (minimal = false →
-      scanReps rep (pre ++ suf) = (mask ++ List.replicate suf.length false, false))
-
-theorem scanReps_cons_super (rep r : Finset Nat) (rs : List (Finset Nat))
-    (h : supersededBy rep r = true) :
-    scanReps rep (r :: rs) = (true :: (scanReps rep rs).1, (scanReps rep rs).2) := by
-  simp only [scanReps, h, if_true]
-
-theorem scanReps_cons_dom (rep r : Finset Nat) (rs : List (Finset Nat))
-    (h1 : supersededBy rep r = false) (h2 : dominates rep r = true) :
-    scanReps rep (r :: rs) = (false :: List.replicate rs.length false, false) := by
-  unfold scanReps
-  simp only [h1, h2, if_false, if_true, Bool.false_eq_true]
-
-theorem scanReps_cons_neither (rep r : Finset Nat) (rs : List (Finset Nat))
-    (h1 : supersededBy rep r = false) (h2 : dominates rep r = false) :
-    scanReps rep (r :: rs) = (false :: (scanReps rep rs).1, (scanReps rep rs).2) := by
-  conv_lhs => rw [scanReps]
-  simp only [h1, h2, Bool.false_eq_true, if_false]
-
-theorem scanReps_mask_length (rep : Finset Nat) (rs : List (Finset Nat)) :
-    (scanReps rep rs).1.length = rs.length := by
-  induction rs with
-  | nil => rfl
-  | cons r rs ih =>
-    by_cases hs : supersededBy rep r = true
-    · rw [scanReps_cons_super rep r rs hs]
-      simp [ih]
-    · simp only [Bool.not_eq_true] at hs
-      by_cases hd : dominates rep r = true
-      · rw [scanReps_cons_dom rep r rs hs hd]
-        simp
-      · simp only [Bool.not_eq_true] at hd
-        rw [scanReps_cons_neither rep r rs hs hd]
-        simp [ih]
-
-theorem forIn_reifies_scan (rep : Finset Nat) :
-    ∀ (L : List (Finset Nat)) (acc : List Bool),
-      (Id.run do
-        let mut minimal := true
-        let mut mask : List Bool := acc
-        for r in L do
-          if r.card > rep.card && rep ⊆ r then
-            mask := mask ++ [true]
-          else if r.card < rep.card && r ⊆ rep then
-            minimal := false
-            break
-          else
-            mask := mask ++ [false]
-        mask := mask ++ List.replicate (acc.length + L.length - mask.length) false
-        return (mask, minimal))
-        = (acc ++ (scanReps rep L).1, (scanReps rep L).2) := by
-  intro L
-  induction L with
-  | nil => intro acc; simp [scanReps, Id.run, bind, pure]
-  | cons r rs ih =>
-    intro acc
-    simp only [List.forIn_cons, bind, pure, Id.run]
-    split_ifs with h1 h2
-    · -- superseded: mask ++ [true], continue
-      have hs : supersededBy rep r = true := h1
-      rw [scanReps_cons_super rep r rs hs]
-      have hih := ih (acc ++ [true])
-      simp only [bind, pure, Id.run] at hih
-      dsimp only
-      rw [show acc.length + (r::rs).length = (acc++[true]).length + rs.length by simp; omega]
-      rw [hih]; simp [List.append_assoc]
-    · -- dominated: break
-      have hs : supersededBy rep r = false := by
-        simpa [supersededBy] using h1
-      have hd : dominates rep r = true := by
-        simpa [dominates] using h2
-      rw [scanReps_cons_dom rep r rs hs hd]
-      dsimp only
-      rw [show acc.length + (r::rs).length - acc.length = rs.length + 1 by simp]
-      rw [List.replicate_succ]
-    · -- neither: mask ++ [false], continue
-      have hs : supersededBy rep r = false := by
-        simpa [supersededBy] using h1
-      have hnd : dominates rep r = false := by
-        simpa [dominates] using h2
-      rw [scanReps_cons_neither rep r rs hs hnd]
-      have hih := ih (acc ++ [false])
-      simp only [bind, pure, Id.run] at hih
-      dsimp only
-      rw [show acc.length + (r::rs).length = (acc++[false]).length + rs.length by simp; omega]
-      rw [hih]; simp [List.append_assoc]
-
-theorem loop_scan_eq (rep : Finset Nat) (repBlocks : List (Finset Nat)) :
-    (Id.run do
-      let mut minimal := true
-      let mut mask : List Bool := []
-      for r in repBlocks do
-        if r.card > rep.card && rep ⊆ r then
-          mask := mask ++ [true]
-        else if r.card < rep.card && r ⊆ rep then
-          minimal := false
-          break
-        else
-          mask := mask ++ [false]
-      mask := mask ++ List.replicate (repBlocks.length - mask.length) false
-      return (mask, minimal))
-      = scanReps rep repBlocks := by
-  have h := forIn_reifies_scan rep repBlocks []
-  simpa using h
-
-theorem tail_eq (blocks : List (List Int)) (numBlocks : List (List Nat))
-    (repBlocks : List (Finset Nat)) (block : List Int) (numBlock : List Nat) (rep : Finset Nat)
-    (hloop : (Id.run do
-      let mut minimal := true
-      let mut mask : List Bool := []
-      for r in repBlocks do
-        if r.card > rep.card && rep ⊆ r then
-          mask := mask ++ [true]
-        else if r.card < rep.card && r ⊆ rep then
-          minimal := false
-          break
-        else
-          mask := mask ++ [false]
-      mask := mask ++ List.replicate (repBlocks.length - mask.length) false
-      return (mask, minimal))
-      = scanReps rep repBlocks) :
-    implementation_pruneSystems blocks numBlocks repBlocks block numBlock rep
-      = pruneSystems blocks numBlocks repBlocks block numBlock rep := by
-  unfold implementation_pruneSystems pruneSystems
-  rw [← hloop]
-  rfl
-
 theorem correct_pruneSystems :
     ∀ (blocks : List (List Int)) (numBlocks : List (List Nat)) (repBlocks : List (Finset Nat))
       (block : List Int) (numBlock : List Nat) (rep : Finset Nat),
       problem_spec_pruneSystems blocks numBlocks repBlocks block numBlock rep
         (implementation_pruneSystems blocks numBlocks repBlocks block numBlock rep) := by
   intro blocks numBlocks repBlocks block numBlock rep
-  unfold problem_spec_pruneSystems
-  exact tail_eq blocks numBlocks repBlocks block numBlock rep (loop_scan_eq rep repBlocks)
-
+  unfold problem_spec_pruneSystems implementation_pruneSystems pruneSystems
+  rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -111,9 +111,9 @@
   let mut minimal := true
   let mut mask : List Bool := []
   for r in repBlocks do
-    if r.card > rep.card && rep ⊆ r then
+    if r.card > rep.card && r ⊆ rep then
       mask := mask ++ [true]
-    else if r.card < rep.card && r ⊆ rep then
+    else if r.card < rep.card && rep ⊆ r then
       minimal := false
       break
     else
@@ -130,153 +130,12 @@
 
 
 -- proof-start
-/-- Loop invariant relating the running `(mask, minimal)` to `scanReps` for a
-processed prefix `pre` with remaining suffix `suf`. While `minimal = true`, no
-dominating cell has been seen in `pre`, `mask` equals the mask-part `scanReps`
-produces on `pre`, and `scanReps` on the full list splits as the accumulated
-mask followed by the suffix's scan. Once `minimal = false`, a dominating cell
-was hit (the loop broke) and the full scan is the accumulated mask padded with
-`false` over the remaining suffix. -/
-def LoopState (rep : Finset Nat) (pre suf : List (Finset Nat))
-    (mask : List Bool) (minimal : Bool) : Prop :=
-  (minimal = true →
-      mask = (scanReps rep pre).1 ∧
-      scanReps rep (pre ++ suf) = (mask ++ (scanReps rep suf).1, (scanReps rep suf).2)) ∧
-  (minimal = false →
-      scanReps rep (pre ++ suf) = (mask ++ List.replicate suf.length false, false))
-
-theorem scanReps_cons_super (rep r : Finset Nat) (rs : List (Finset Nat))
-    (h : supersededBy rep r = true) :
-    scanReps rep (r :: rs) = (true :: (scanReps rep rs).1, (scanReps rep rs).2) := by
-  simp only [scanReps, h, if_true]
-
-theorem scanReps_cons_dom (rep r : Finset Nat) (rs : List (Finset Nat))
-    (h1 : supersededBy rep r = false) (h2 : dominates rep r = true) :
-    scanReps rep (r :: rs) = (false :: List.replicate rs.length false, false) := by
-  unfold scanReps
-  simp only [h1, h2, if_false, if_true, Bool.false_eq_true]
-
-theorem scanReps_cons_neither (rep r : Finset Nat) (rs : List (Finset Nat))
-    (h1 : supersededBy rep r = false) (h2 : dominates rep r = false) :
-    scanReps rep (r :: rs) = (false :: (scanReps rep rs).1, (scanReps rep rs).2) := by
-  conv_lhs => rw [scanReps]
-  simp only [h1, h2, Bool.false_eq_true, if_false]
-
-theorem scanReps_mask_length (rep : Finset Nat) (rs : List (Finset Nat)) :
-    (scanReps rep rs).1.length = rs.length := by
-  induction rs with
-  | nil => rfl
-  | cons r rs ih =>
-    by_cases hs : supersededBy rep r = true
-    · rw [scanReps_cons_super rep r rs hs]
-      simp [ih]
-    · simp only [Bool.not_eq_true] at hs
-      by_cases hd : dominates rep r = true
-      · rw [scanReps_cons_dom rep r rs hs hd]
-        simp
-      · simp only [Bool.not_eq_true] at hd
-        rw [scanReps_cons_neither rep r rs hs hd]
-        simp [ih]
-
-theorem forIn_reifies_scan (rep : Finset Nat) :
-    ∀ (L : List (Finset Nat)) (acc : List Bool),
-      (Id.run do
-        let mut minimal := true
-        let mut mask : List Bool := acc
-        for r in L do
-          if r.card > rep.card && rep ⊆ r then
-            mask := mask ++ [true]
-          else if r.card < rep.card && r ⊆ rep then
-            minimal := false
-            break
-          else
-            mask := mask ++ [false]
-        mask := mask ++ List.replicate (acc.length + L.length - mask.length) false
-        return (mask, minimal))
-        = (acc ++ (scanReps rep L).1, (scanReps rep L).2) := by
-  intro L
-  induction L with
-  | nil => intro acc; simp [scanReps, Id.run, bind, pure]
-  | cons r rs ih =>
-    intro acc
-    simp only [List.forIn_cons, bind, pure, Id.run]
-    split_ifs with h1 h2
-    · -- superseded: mask ++ [true], continue
-      have hs : supersededBy rep r = true := h1
-      rw [scanReps_cons_super rep r rs hs]
-      have hih := ih (acc ++ [true])
-      simp only [bind, pure, Id.run] at hih
-      dsimp only
-      rw [show acc.length + (r::rs).length = (acc++[true]).length + rs.length by simp; omega]
-      rw [hih]; simp [List.append_assoc]
-    · -- dominated: break
-      have hs : supersededBy rep r = false := by
-        simpa [supersededBy] using h1
-      have hd : dominates rep r = true := by
-        simpa [dominates] using h2
-      rw [scanReps_cons_dom rep r rs hs hd]
-      dsimp only
-      rw [show acc.length + (r::rs).length - acc.length = rs.length + 1 by simp]
-      rw [List.replicate_succ]
-    · -- neither: mask ++ [false], continue
-      have hs : supersededBy rep r = false := by
-        simpa [supersededBy] using h1
-      have hnd : dominates rep r = false := by
-        simpa [dominates] using h2
-      rw [scanReps_cons_neither rep r rs hs hnd]
-      have hih := ih (acc ++ [false])
-      simp only [bind, pure, Id.run] at hih
-      dsimp only
-      rw [show acc.length + (r::rs).length = (acc++[false]).length + rs.length by simp; omega]
-      rw [hih]; simp [List.append_assoc]
-
-theorem loop_scan_eq (rep : Finset Nat) (repBlocks : List (Finset Nat)) :
-    (Id.run do
-      let mut minimal := true
-      let mut mask : List Bool := []
-      for r in repBlocks do
-        if r.card > rep.card && rep ⊆ r then
-          mask := mask ++ [true]
-        else if r.card < rep.card && r ⊆ rep then
-          minimal := false
-          break
-        else
-          mask := mask ++ [false]
-      mask := mask ++ List.replicate (repBlocks.length - mask.length) false
-      return (mask, minimal))
-      = scanReps rep repBlocks := by
-  have h := forIn_reifies_scan rep repBlocks []
-  simpa using h
-
-theorem tail_eq (blocks : List (List Int)) (numBlocks : List (List Nat))
-    (repBlocks : List (Finset Nat)) (block : List Int) (numBlock : List Nat) (rep : Finset Nat)
-    (hloop : (Id.run do
-      let mut minimal := true
-      let mut mask : List Bool := []
-      for r in repBlocks do
-        if r.card > rep.card && rep ⊆ r then
-          mask := mask ++ [true]
-        else if r.card < rep.card && r ⊆ rep then
-          minimal := false
-          break
-        else
-          mask := mask ++ [false]
-      mask := mask ++ List.replicate (repBlocks.length - mask.length) false
-      return (mask, minimal))
-      = scanReps rep repBlocks) :
-    implementation_pruneSystems blocks numBlocks repBlocks block numBlock rep
-      = pruneSystems blocks numBlocks repBlocks block numBlock rep := by
-  unfold implementation_pruneSystems pruneSystems
-  rw [← hloop]
-  rfl
-
 theorem correct_pruneSystems :
     ∀ (blocks : List (List Int)) (numBlocks : List (List Nat)) (repBlocks : List (Finset Nat))
       (block : List Int) (numBlock : List Nat) (rep : Finset Nat),
       problem_spec_pruneSystems blocks numBlocks repBlocks block numBlock rep
         (implementation_pruneSystems blocks numBlocks repBlocks block numBlock rep) := by
   intro blocks numBlocks repBlocks block numBlock rep
-  unfold problem_spec_pruneSystems
-  exact tail_eq blocks numBlocks repBlocks block numBlock rep (loop_scan_eq rep repBlocks)
-
+  unfold problem_spec_pruneSystems implementation_pruneSystems pruneSystems
+  rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -107,176 +107,18 @@
 def implementation_pruneSystems
     (blocks : List (List Int)) (numBlocks : List (List Nat)) (repBlocks : List (Finset Nat))
     (block : List Int) (numBlock : List Nat) (rep : Finset Nat) :
-    List (List Int) × List (List Nat) × List (Finset Nat) := Id.run do
-  let mut minimal := true
-  let mut mask : List Bool := []
-  for r in repBlocks do
-    if r.card > rep.card && rep ⊆ r then
-      mask := mask ++ [true]
-    else if r.card < rep.card && r ⊆ rep then
-      minimal := false
-      break
-    else
-      mask := mask ++ [false]
-  mask := mask ++ List.replicate (repBlocks.length - mask.length) false
-  let blocks' := dropFlagged blocks mask
-  let numBlocks' := dropFlagged numBlocks mask
-  let repBlocks' := dropFlagged repBlocks mask
-  if minimal && !(numBlocks'.contains numBlock) then
-    return (blocks' ++ [block], numBlocks' ++ [numBlock], repBlocks' ++ [rep])
-  else
-    return (blocks', numBlocks', repBlocks')
+    List (List Int) × List (List Nat) × List (Finset Nat) :=
+  pruneSystems blocks numBlocks repBlocks block numBlock rep
 -- impl-end
 
 
 -- proof-start
-/-- Loop invariant relating the running `(mask, minimal)` to `scanReps` for a
-processed prefix `pre` with remaining suffix `suf`. While `minimal = true`, no
-dominating cell has been seen in `pre`, `mask` equals the mask-part `scanReps`
-produces on `pre`, and `scanReps` on the full list splits as the accumulated
-mask followed by the suffix's scan. Once `minimal = false`, a dominating cell
-was hit (the loop broke) and the full scan is the accumulated mask padded with
-`false` over the remaining suffix. -/
-def LoopState (rep : Finset Nat) (pre suf : List (Finset Nat))
-    (mask : List Bool) (minimal : Bool) : Prop :=
-  (minimal = true →
-      mask = (scanReps rep pre).1 ∧
-      scanReps rep (pre ++ suf) = (mask ++ (scanReps rep suf).1, (scanReps rep suf).2)) ∧
-  (minimal = false →
-      scanReps rep (pre ++ suf) = (mask ++ List.replicate suf.length false, false))
-
-theorem scanReps_cons_super (rep r : Finset Nat) (rs : List (Finset Nat))
-    (h : supersededBy rep r = true) :
-    scanReps rep (r :: rs) = (true :: (scanReps rep rs).1, (scanReps rep rs).2) := by
-  simp only [scanReps, h, if_true]
-
-theorem scanReps_cons_dom (rep r : Finset Nat) (rs : List (Finset Nat))
-    (h1 : supersededBy rep r = false) (h2 : dominates rep r = true) :
-    scanReps rep (r :: rs) = (false :: List.replicate rs.length false, false) := by
-  unfold scanReps
-  simp only [h1, h2, if_false, if_true, Bool.false_eq_true]
-
-theorem scanReps_cons_neither (rep r : Finset Nat) (rs : List (Finset Nat))
-    (h1 : supersededBy rep r = false) (h2 : dominates rep r = false) :
-    scanReps rep (r :: rs) = (false :: (scanReps rep rs).1, (scanReps rep rs).2) := by
-  conv_lhs => rw [scanReps]
-  simp only [h1, h2, Bool.false_eq_true, if_false]
-
-theorem scanReps_mask_length (rep : Finset Nat) (rs : List (Finset Nat)) :
-    (scanReps rep rs).1.length = rs.length := by
-  induction rs with
-  | nil => rfl
-  | cons r rs ih =>
-    by_cases hs : supersededBy rep r = true
-    · rw [scanReps_cons_super rep r rs hs]
-      simp [ih]
-    · simp only [Bool.not_eq_true] at hs
-      by_cases hd : dominates rep r = true
-      · rw [scanReps_cons_dom rep r rs hs hd]
-        simp
-      · simp only [Bool.not_eq_true] at hd
-        rw [scanReps_cons_neither rep r rs hs hd]
-        simp [ih]
-
-theorem forIn_reifies_scan (rep : Finset Nat) :
-    ∀ (L : List (Finset Nat)) (acc : List Bool),
-      (Id.run do
-        let mut minimal := true
-        let mut mask : List Bool := acc
-        for r in L do
-          if r.card > rep.card && rep ⊆ r then
-            mask := mask ++ [true]
-          else if r.card < rep.card && r ⊆ rep then
-            minimal := false
-            break
-          else
-            mask := mask ++ [false]
-        mask := mask ++ List.replicate (acc.length + L.length - mask.length) false
-        return (mask, minimal))
-        = (acc ++ (scanReps rep L).1, (scanReps rep L).2) := by
-  intro L
-  induction L with
-  | nil => intro acc; simp [scanReps, Id.run, bind, pure]
-  | cons r rs ih =>
-    intro acc
-    simp only [List.forIn_cons, bind, pure, Id.run]
-    split_ifs with h1 h2
-    · -- superseded: mask ++ [true], continue
-      have hs : supersededBy rep r = true := h1
-      rw [scanReps_cons_super rep r rs hs]
-      have hih := ih (acc ++ [true])
-      simp only [bind, pure, Id.run] at hih
-      dsimp only
-      rw [show acc.length + (r::rs).length = (acc++[true]).length + rs.length by simp; omega]
-      rw [hih]; simp [List.append_assoc]
-    · -- dominated: break
-      have hs : supersededBy rep r = false := by
-        simpa [supersededBy] using h1
-      have hd : dominates rep r = true := by
-        simpa [dominates] using h2
-      rw [scanReps_cons_dom rep r rs hs hd]
-      dsimp only
-      rw [show acc.length + (r::rs).length - acc.length = rs.length + 1 by simp]
-      rw [List.replicate_succ]
-    · -- neither: mask ++ [false], continue
-      have hs : supersededBy rep r = false := by
-        simpa [supersededBy] using h1
-      have hnd : dominates rep r = false := by
-        simpa [dominates] using h2
-      rw [scanReps_cons_neither rep r rs hs hnd]
-      have hih := ih (acc ++ [false])
-      simp only [bind, pure, Id.run] at hih
-      dsimp only
-      rw [show acc.length + (r::rs).length = (acc++[false]).length + rs.length by simp; omega]
-      rw [hih]; simp [List.append_assoc]
-
-theorem loop_scan_eq (rep : Finset Nat) (repBlocks : List (Finset Nat)) :
-    (Id.run do
-      let mut minimal := true
-      let mut mask : List Bool := []
-      for r in repBlocks do
-        if r.card > rep.card && rep ⊆ r then
-          mask := mask ++ [true]
-        else if r.card < rep.card && r ⊆ rep then
-          minimal := false
-          break
-        else
-          mask := mask ++ [false]
-      mask := mask ++ List.replicate (repBlocks.length - mask.length) false
-      return (mask, minimal))
-      = scanReps rep repBlocks := by
-  have h := forIn_reifies_scan rep repBlocks []
-  simpa using h
-
-theorem tail_eq (blocks : List (List Int)) (numBlocks : List (List Nat))
-    (repBlocks : List (Finset Nat)) (block : List Int) (numBlock : List Nat) (rep : Finset Nat)
-    (hloop : (Id.run do
-      let mut minimal := true
-      let mut mask : List Bool := []
-      for r in repBlocks do
-        if r.card > rep.card && rep ⊆ r then
-          mask := mask ++ [true]
-        else if r.card < rep.card && r ⊆ rep then
-          minimal := false
-          break
-        else
-          mask := mask ++ [false]
-      mask := mask ++ List.replicate (repBlocks.length - mask.length) false
-      return (mask, minimal))
-      = scanReps rep repBlocks) :
-    implementation_pruneSystems blocks numBlocks repBlocks block numBlock rep
-      = pruneSystems blocks numBlocks repBlocks block numBlock rep := by
-  unfold implementation_pruneSystems pruneSystems
-  rw [← hloop]
-  rfl
-
 theorem correct_pruneSystems :
     ∀ (blocks : List (List Int)) (numBlocks : List (List Nat)) (repBlocks : List (Finset Nat))
       (block : List Int) (numBlock : List Nat) (rep : Finset Nat),
       problem_spec_pruneSystems blocks numBlocks repBlocks block numBlock rep
         (implementation_pruneSystems blocks numBlocks repBlocks block numBlock rep) := by
   intro blocks numBlocks repBlocks block numBlock rep
-  unfold problem_spec_pruneSystems
-  exact tail_eq blocks numBlocks repBlocks block numBlock rep (loop_scan_eq rep repBlocks)
-
+  unfold problem_spec_pruneSystems implementation_pruneSystems
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Maintaining a collection of candidate partition systems for a transitive action,
keeping only the coarsest ones.

We track three parallel collections of equal length, one entry per partition
system retained so far:

* `blocks`   — a concrete description of each retained system;
* `numBlocks` — a canonical numbering of each retained system;
* `repBlocks` — the representative cell (the set containing the point `0`) of
  each retained system.

A fresh candidate arrives, described by the same three pieces of data
(`block`, `numBlock`, `rep`). We compare its representative cell `rep` against
the representative cell `r` of every retained system, in order:

* if a retained `r` strictly contains `rep` (more points, and every point of
  `rep` lies in `r`), that retained system is superseded by the candidate and is
  marked for removal;
* if instead a retained `r` is strictly contained in `rep`, then the candidate
  is itself superseded; the candidate is rejected and no further comparisons are
  made;
* otherwise the retained system is left untouched.

After the scan, every system marked for removal is dropped from ALL THREE
collections together, so the three collections stay aligned to the same set of
surviving indices. The candidate is then appended to all three collections
exactly when it was not rejected AND its numbering does not already appear among
the surviving numberings.

The essential guarantee is alignment: a system is removed from `blocks`,
`numBlocks` and `repBlocks` at the same indices, never from one collection by
position while another is pruned by value, so the three collections describe the
same surviving systems in the same order.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The candidate
-- data (`block`, `numBlock`, `rep`) and the retained collections are the inputs;
-- the comparison, the aligned removal and the conditional append are modeled
-- DEEPLY over those inputs, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- `rep` is strictly coarser-dominated by `r`: `r` has strictly more points and
contains every point of `rep`. A retained system whose representative cell `r`
satisfies this against the candidate's `rep` is superseded by the candidate. -/
def supersededBy (rep r : Finset Nat) : Bool := r.card > rep.card && rep ⊆ r

/-- The candidate's `rep` is itself dominated by `r`: `r` has strictly fewer
points and all of them lie in `rep`. -/
def dominates (rep r : Finset Nat) : Bool := r.card < rep.card && r ⊆ rep

/-- Scan the retained representative cells in order, producing the per-index
removal flags together with whether the candidate survives the scan.
The boolean is `true` while the candidate is still viable. On encountering a
representative cell that dominates the candidate, the candidate is rejected and
the scan stops; all remaining indices are left unflagged. -/
def scanReps (rep : Finset Nat) : List (Finset Nat) → (List Bool × Bool)
  | [] => ([], true)
  | r :: rs =>
    if supersededBy rep r then
      let (m, keep) := scanReps rep rs
      (true :: m, keep)
    else if dominates rep r then
      (false :: List.replicate rs.length false, false)
    else
      let (m, keep) := scanReps rep rs
      (false :: m, keep)

/-- Drop every entry of `xs` whose aligned mask flag is `true`. -/
def dropFlagged {α : Type} : List α → List Bool → List α
  | [], _ => []
  | a :: as, [] => a :: as
  | a :: as, b :: bs => if b then dropFlagged as bs else a :: dropFlagged as bs

/-- The full update step: scan, prune all three collections by the same mask,
then conditionally append the candidate. -/
def pruneSystems
    (blocks : List (List Int)) (numBlocks : List (List Nat)) (repBlocks : List (Finset Nat))
    (block : List Int) (numBlock : List Nat) (rep : Finset Nat) :
    List (List Int) × List (List Nat) × List (Finset Nat) :=
  let (mask, candidateKept) := scanReps rep repBlocks
  let blocks'   := dropFlagged blocks mask
  let numBlocks' := dropFlagged numBlocks mask
  let repBlocks' := dropFlagged repBlocks mask
  if candidateKept && !(numBlocks'.contains numBlock) then
    (blocks' ++ [block], numBlocks' ++ [numBlock], repBlocks' ++ [rep])
  else
    (blocks', numBlocks', repBlocks')
-- pure-end

-- post-conditions-start
/-- The result is exactly the aligned-pruned-then-conditionally-appended update
of the three collections dictated by the rule above. -/
def problem_spec_pruneSystems
    (blocks : List (List Int)) (numBlocks : List (List Nat)) (repBlocks : List (Finset Nat))
    (block : List Int) (numBlock : List Nat) (rep : Finset Nat)
    (result : List (List Int) × List (List Nat) × List (Finset Nat)) : Prop :=
  result = pruneSystems blocks numBlocks repBlocks block numBlock rep
-- post-conditions-end

-- impl-start
def implementation_pruneSystems
    (blocks : List (List Int)) (numBlocks : List (List Nat)) (repBlocks : List (Finset Nat))
    (block : List Int) (numBlock : List Nat) (rep : Finset Nat) :
    List (List Int) × List (List Nat) × List (Finset Nat) := Id.run do
  let mut minimal := true
  let mut mask : List Bool := []
  for r in repBlocks do
    if r.card > rep.card && rep ⊆ r then
      mask := mask ++ [true]
    else if r.card < rep.card && r ⊆ rep then
      minimal := false
      break
    else
      mask := mask ++ [false]
  mask := mask ++ List.replicate (repBlocks.length - mask.length) false
  let blocks' := dropFlagged blocks mask
  let numBlocks' := dropFlagged numBlocks mask
  let repBlocks' := dropFlagged repBlocks mask
  if minimal && !(numBlocks'.contains numBlock) then
    return (blocks' ++ [block], numBlocks' ++ [numBlock], repBlocks' ++ [rep])
  else
    return (blocks', numBlocks', repBlocks')
-- impl-end


-- proof-start
/-- Loop invariant relating the running `(mask, minimal)` to `scanReps` for a
processed prefix `pre` with remaining suffix `suf`. While `minimal = true`, no
dominating cell has been seen in `pre`, `mask` equals the mask-part `scanReps`
produces on `pre`, and `scanReps` on the full list splits as the accumulated
mask followed by the suffix's scan. Once `minimal = false`, a dominating cell
was hit (the loop broke) and the full scan is the accumulated mask padded with
`false` over the remaining suffix. -/
def LoopState (rep : Finset Nat) (pre suf : List (Finset Nat))
    (mask : List Bool) (minimal : Bool) : Prop :=
  (minimal = true →
      mask = (scanReps rep pre).1 ∧
      scanReps rep (pre ++ suf) = (mask ++ (scanReps rep suf).1, (scanReps rep suf).2)) ∧
  (minimal = false →
      scanReps rep (pre ++ suf) = (mask ++ List.replicate suf.length false, false))

theorem scanReps_cons_super (rep r : Finset Nat) (rs : List (Finset Nat))
    (h : supersededBy rep r = true) :
    scanReps rep (r :: rs) = (true :: (scanReps rep rs).1, (scanReps rep rs).2) := by
  simp only [scanReps, h, if_true]

theorem scanReps_cons_dom (rep r : Finset Nat) (rs : List (Finset Nat))
    (h1 : supersededBy rep r = false) (h2 : dominates rep r = true) :
    scanReps rep (r :: rs) = (false :: List.replicate rs.length false, false) := by
  unfold scanReps
  simp only [h1, h2, if_false, if_true, Bool.false_eq_true]

theorem scanReps_cons_neither (rep r : Finset Nat) (rs : List (Finset Nat))
    (h1 : supersededBy rep r = false) (h2 : dominates rep r = false) :
    scanReps rep (r :: rs) = (false :: (scanReps rep rs).1, (scanReps rep rs).2) := by
  conv_lhs => rw [scanReps]
  simp only [h1, h2, Bool.false_eq_true, if_false]

theorem scanReps_mask_length (rep : Finset Nat) (rs : List (Finset Nat)) :
    (scanReps rep rs).1.length = rs.length := by
  induction rs with
  | nil => rfl
  | cons r rs ih =>
    by_cases hs : supersededBy rep r = true
    · rw [scanReps_cons_super rep r rs hs]
      simp [ih]
    · simp only [Bool.not_eq_true] at hs
      by_cases hd : dominates rep r = true
      · rw [scanReps_cons_dom rep r rs hs hd]
        simp
      · simp only [Bool.not_eq_true] at hd
        rw [scanReps_cons_neither rep r rs hs hd]
        simp [ih]

theorem forIn_reifies_scan (rep : Finset Nat) :
    ∀ (L : List (Finset Nat)) (acc : List Bool),
      (Id.run do
        let mut minimal := true
        let mut mask : List Bool := acc
        for r in L do
          if r.card > rep.card && rep ⊆ r then
            mask := mask ++ [true]
          else if r.card < rep.card && r ⊆ rep then
            minimal := false
            break
          else
            mask := mask ++ [false]
        mask := mask ++ List.replicate (acc.length + L.length - mask.length) false
        return (mask, minimal))
        = (acc ++ (scanReps rep L).1, (scanReps rep L).2) := by
  intro L
  induction L with
  | nil => intro acc; simp [scanReps, Id.run, bind, pure]
  | cons r rs ih =>
    intro acc
    simp only [List.forIn_cons, bind, pure, Id.run]
    split_ifs with h1 h2
    · -- superseded: mask ++ [true], continue
      have hs : supersededBy rep r = true := h1
      rw [scanReps_cons_super rep r rs hs]
      have hih := ih (acc ++ [true])
      simp only [bind, pure, Id.run] at hih
      dsimp only
      rw [show acc.length + (r::rs).length = (acc++[true]).length + rs.length by simp; omega]
      rw [hih]; simp [List.append_assoc]
    · -- dominated: break
      have hs : supersededBy rep r = false := by
        simpa [supersededBy] using h1
      have hd : dominates rep r = true := by
        simpa [dominates] using h2
      rw [scanReps_cons_dom rep r rs hs hd]
      dsimp only
      rw [show acc.length + (r::rs).length - acc.length = rs.length + 1 by simp]
      rw [List.replicate_succ]
    · -- neither: mask ++ [false], continue
      have hs : supersededBy rep r = false := by
        simpa [supersededBy] using h1
      have hnd : dominates rep r = false := by
        simpa [dominates] using h2
      rw [scanReps_cons_neither rep r rs hs hnd]
      have hih := ih (acc ++ [false])
      simp only [bind, pure, Id.run] at hih
      dsimp only
      rw [show acc.length + (r::rs).length = (acc++[false]).length + rs.length by simp; omega]
      rw [hih]; simp [List.append_assoc]

theorem loop_scan_eq (rep : Finset Nat) (repBlocks : List (Finset Nat)) :
    (Id.run do
      let mut minimal := true
      let mut mask : List Bool := []
      for r in repBlocks do
        if r.card > rep.card && rep ⊆ r then
          mask := mask ++ [true]
        else if r.card < rep.card && r ⊆ rep then
          minimal := false
          break
        else
          mask := mask ++ [false]
      mask := mask ++ List.replicate (repBlocks.length - mask.length) false
      return (mask, minimal))
      = scanReps rep repBlocks := by
  have h := forIn_reifies_scan rep repBlocks []
  simpa using h

theorem tail_eq (blocks : List (List Int)) (numBlocks : List (List Nat))
    (repBlocks : List (Finset Nat)) (block : List Int) (numBlock : List Nat) (rep : Finset Nat)
    (hloop : (Id.run do
      let mut minimal := true
      let mut mask : List Bool := []
      for r in repBlocks do
        if r.card > rep.card && rep ⊆ r then
          mask := mask ++ [true]
        else if r.card < rep.card && r ⊆ rep then
          minimal := false
          break
        else
          mask := mask ++ [false]
      mask := mask ++ List.replicate (repBlocks.length - mask.length) false
      return (mask, minimal))
      = scanReps rep repBlocks) :
    implementation_pruneSystems blocks numBlocks repBlocks block numBlock rep
      = pruneSystems blocks numBlocks repBlocks block numBlock rep := by
  unfold implementation_pruneSystems pruneSystems
  rw [← hloop]
  rfl

theorem correct_pruneSystems :
    ∀ (blocks : List (List Int)) (numBlocks : List (List Nat)) (repBlocks : List (Finset Nat))
      (block : List Int) (numBlock : List Nat) (rep : Finset Nat),
      problem_spec_pruneSystems blocks numBlocks repBlocks block numBlock rep
        (implementation_pruneSystems blocks numBlocks repBlocks block numBlock rep) := by
  intro blocks numBlocks repBlocks block numBlock rep
  unfold problem_spec_pruneSystems
  exact tail_eq blocks numBlocks repBlocks block numBlock rep (loop_scan_eq rep repBlocks)

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for sympy__sympy-19954 (lean).

SAME-SPEC: all 7 attacks same_spec(Solution.lean, atk_N.lean, lean)=True (axioms/pure/pre/post regions byte-identical; only impl+proof edited).

### VERIFY (bash scripts/lean_verify.sh atk_N.lean):
- atk_1 (supersede >= instead of >): exit 1 (fails) — CORRECT REJECT.
- atk_2 (drop break on dominate): exit 1 — CORRECT REJECT.
- atk_3 (partial-domain: skip when repBlocks empty): exit 1 — CORRECT REJECT.
- atk_4 (dedup over UNpruned numBlocks): exit 1 — CORRECT REJECT.
- atk_5 (misalignment: omit rep append to repBlocks'): exit 1 — CORRECT REJECT.
- atk_6 (subset direction swap in supersede/dominate): exit 1 — CORRECT REJECT.
- atk_7 (ungrounded-oracle echo: impl := pruneSystems ...): exit 0 VERIFIES. #print axioms correct_pruneSystems = [propext, Quot.sound] — NO sorryAx, clean.
- pos_control (bundle Solution.lean): exit 0 verifies.

GENUINE-DIVERGENCE PROOF: for atk_1..6 I machine-checked (#eval, verify exit 0) concrete inputs where implementation != pruneSystems (files witness.lean, witness2.lean, witness_atk2.lean in scratch dir). These prove the exact-equality spec's exit-1 results are true rejections, not weak-tactic false negatives.

MANDATORY RESOLVE (protocol step 2) — atk_7 is the only same-spec impl with a closing clean-axiom proof, so its faithful refined patch MUST be run. atk_7 echoes pruneSystems, i.e. the exact post-patch gold behavior, so its faithful patch is byte-identical to patch.diff (saved at atk_7_faithful_patch.diff). EXECUTED harness (docker, run_evaluation, princeton-nlp/SWE-bench_Verified, namespace swebench, image swebench/sweb.eval.x86_64.sympy_1776_sympy-19954:latest): report sbu_patch.sbu_manual_19954.json => resolved_instances=1, resolved_ids=[sympy__sympy-19954], errors=0. RESOLVES. (The run_resolve() wrapper initially returned 'no report/image pull failure' because the instance image was not local; after docker pull the manual run_evaluation resolved cleanly — an infra artifact, not a resolve failure.) => atk_7 is a resolving echo, NOT a spec break, exactly as the echo-resolve policy requires.

A-LEG / DEEP-MODEL AUDIT (focus per instructions): refinement.md declares all 15 legs R/I with NO A-consumed and NO A-reference rows; the changed op (mask-prune vs running-index prune of the 3 parallel collections) is modeled DEEPLY as pure list functions over the observable inputs. axiom_check.py is a legitimate skip stub (no consumed callee axiom, no A-reference; SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed op). meta.json axioms=[], deep_model_references=[], opaque_callees=[] — consistent. No kind-3 (changed-inexpressible) leg. mapping.md type bijection (list[list[int]]->List (List Int), tuple->List Nat, set->Finset Nat, len->card, issubset->subset, mask-prune->dropFlagged) is sound over the real domain; only cardinality/subset/index-alignment are observable and all preserved. G-CONF (conformance_check.py, seed 19954, 150k inputs) is the differential check for the R legs and passes (meta G-CONF exit 0). No callee correspondence to falsify because there are no A-legs.

PREPATCH: Solution_prepatch.lean transliterates the running-index eraseIdx bug (del num_blocks[i],blocks[i] mid-scan; rep_blocks value-pruned after) with a sorry proof carrying the gold body — UNCLOSABLE against the buggy impl. G-DIFF recorded 'verification failed' => prepatch reproduced.

VERDICT: SOUND. 7 attacks run (6 correct rejects with machine-checked divergence witnesses + 1 resolving echo whose faithful=gold patch was EXECUTED through run_evaluation and RESOLVED); positive control verifies; A-legs are vacuous (all R/I, deep model) and their absence is consistent across refinement.md/mapping.md/axiom_check.py/meta.json. No same-spec impl with a closing clean-axiom proof has a non-resolving faithful patch. verify does not certify incorrectness here.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — spec holds. The spec is an exact functional equality problem_spec := (result = pruneSystems ...) over deeply-modeled pure functions (scanReps/dropFlagged/pruneSystems), the tightest possible shape. Only a behavioral echo of the gold verifies, and its faithful patch resolves. Concrete divergence witnesses (machine-checked #eval, exit 0) prove every wrong impl differs from the oracle: atk_1 (>= for >): rep={0,1},r0={0,1} card-equal → gold keeps+appends ([[0,1],[9]],...) vs impl supersedes ([[9]],...). atk_2 (no break on dominate): repBlocks=[{0},{0,1,2}],rep={0,1} → gold rejects+keeps both ([[0],[1]],...) vs impl prunes r1 ([[0]],...). atk_3 (skip append when repBlocks empty): gold ([[9]],[[7]],[{0,1}]) vs impl ([],[],[]). atk_4 (dedup over UNpruned numBlocks): superseded row carries colliding numBlock → gold appends vs impl blocks it ([[9]],...) vs ([],...). atk_5 (drop rep append): repBlocks' ([{0,1}]) vs ([]). atk_6 (subset direction swap): gold supersedes r0 vs impl keeps it ([[9]],[[7]],[{0}]) vs ([[0],[9]],...).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Maintaining a collection of candidate partition systems for a transitive action,
keeping only the coarsest ones.

We track three parallel collections of equal length, one entry per partition
system retained so far:

* `blocks`   — a concrete description of each retained system;
* `numBlocks` — a canonical numbering of each retained system;
* `repBlocks` — the representative cell (the set containing the point `0`) of
  each retained system.

A fresh candidate arrives, described by the same three pieces of data
(`block`, `numBlock`, `rep`). We compare its representative cell `rep` against
the representative cell `r` of every retained system, in order:

* if a retained `r` strictly contains `rep` (more points, and every point of
  `rep` lies in `r`), that retained system is superseded by the candidate and is
  marked for removal;
* if instead a retained `r` is strictly contained in `rep`, then the candidate
  is itself superseded; the candidate is rejected and no further comparisons are
  made;
* otherwise the retained system is left untouched.

After the scan, every system marked for removal is dropped from ALL THREE
collections together, so the three collections stay aligned to the same set of
surviving indices. The candidate is then appended to all three collections
exactly when it was not rejected AND its numbering does not already appear among
the surviving numberings.

The essential guarantee is alignment: a system is removed from `blocks`,
`numBlocks` and `repBlocks` at the same indices, never from one collection by
position while another is pruned by value, so the three collections describe the
same surviving systems in the same order.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The candidate
-- data (`block`, `numBlock`, `rep`) and the retained collections are the inputs;
-- the comparison, the aligned removal and the conditional append are modeled
-- DEEPLY over those inputs, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- `rep` is strictly coarser-dominated by `r`: `r` has strictly more points and
contains every point of `rep`. A retained system whose representative cell `r`
satisfies this against the candidate's `rep` is superseded by the candidate. -/
def supersededBy (rep r : Finset Nat) : Bool := r.card > rep.card && rep ⊆ r

/-- The candidate's `rep` is itself dominated by `r`: `r` has strictly fewer
points and all of them lie in `rep`. -/
def dominates (rep r : Finset Nat) : Bool := r.card < rep.card && r ⊆ rep

/-- Scan the retained representative cells in order, producing the per-index
removal flags together with whether the candidate survives the scan.
The boolean is `true` while the candidate is still viable. On encountering a
representative cell that dominates the candidate, the candidate is rejected and
the scan stops; all remaining indices are left unflagged. -/
def scanReps (rep : Finset Nat) : List (Finset Nat) → (List Bool × Bool)
  | [] => ([], true)
  | r :: rs =>
    if supersededBy rep r then
      let (m, keep) := scanReps rep rs
      (true :: m, keep)
    else if dominates rep r then
      (false :: List.replicate rs.length false, false)
    else
      let (m, keep) := scanReps rep rs
      (false :: m, keep)

/-- Drop every entry of `xs` whose aligned mask flag is `true`. -/
def dropFlagged {α : Type} : List α → List Bool → List α
  | [], _ => []
  | a :: as, [] => a :: as
  | a :: as, b :: bs => if b then dropFlagged as bs else a :: dropFlagged as bs

/-- The full update step: scan, prune all three collections by the same mask,
then conditionally append the candidate. -/
def pruneSystems
    (blocks : List (List Int)) (numBlocks : List (List Nat)) (repBlocks : List (Finset Nat))
    (block : List Int) (numBlock : List Nat) (rep : Finset Nat) :
    List (List Int) × List (List Nat) × List (Finset Nat) :=
  let (mask, candidateKept) := scanReps rep repBlocks
  let blocks'   := dropFlagged blocks mask
  let numBlocks' := dropFlagged numBlocks mask
  let repBlocks' := dropFlagged repBlocks mask
  if candidateKept && !(numBlocks'.contains numBlock) then
    (blocks' ++ [block], numBlocks' ++ [numBlock], repBlocks' ++ [rep])
  else
    (blocks', numBlocks', repBlocks')
-- pure-end

-- post-conditions-start
/-- The result is exactly the aligned-pruned-then-conditionally-appended update
of the three collections dictated by the rule above. -/
def problem_spec_pruneSystems
    (blocks : List (List Int)) (numBlocks : List (List Nat)) (repBlocks : List (Finset Nat))
    (block : List Int) (numBlock : List Nat) (rep : Finset Nat)
    (result : List (List Int) × List (List Nat) × List (Finset Nat)) : Prop :=
  result = pruneSystems blocks numBlocks repBlocks block numBlock rep
-- post-conditions-end

-- impl-start
def implementation_pruneSystems
    (blocks : List (List Int)) (numBlocks : List (List Nat)) (repBlocks : List (Finset Nat))
    (block : List Int) (numBlock : List Nat) (rep : Finset Nat) :
    List (List Int) × List (List Nat) × List (Finset Nat) := Id.run do
  let mut minimal := true
  let mut mask : List Bool := []
  for r in repBlocks do
    if r.card > rep.card && rep ⊆ r then
      mask := mask ++ [true]
    else if r.card < rep.card && r ⊆ rep then
      minimal := false
      break
    else
      mask := mask ++ [false]
  mask := mask ++ List.replicate (repBlocks.length - mask.length) false
  let blocks' := dropFlagged blocks mask
  let numBlocks' := dropFlagged numBlocks mask
  let repBlocks' := dropFlagged repBlocks mask
  if minimal && !(numBlocks'.contains numBlock) then
    return (blocks' ++ [block], numBlocks' ++ [numBlock], repBlocks' ++ [rep])
  else
    return (blocks', numBlocks', repBlocks')
-- impl-end


-- proof-start
/-- Loop invariant relating the running `(mask, minimal)` to `scanReps` for a
processed prefix `pre` with remaining suffix `suf`. While `minimal = true`, no
dominating cell has been seen in `pre`, `mask` equals the mask-part `scanReps`
produces on `pre`, and `scanReps` on the full list splits as the accumulated
mask followed by the suffix's scan. Once `minimal = false`, a dominating cell
was hit (the loop broke) and the full scan is the accumulated mask padded with
`false` over the remaining suffix. -/
def LoopState (rep : Finset Nat) (pre suf : List (Finset Nat))
    (mask : List Bool) (minimal : Bool) : Prop :=
  (minimal = true →
      mask = (scanReps rep pre).1 ∧
      scanReps rep (pre ++ suf) = (mask ++ (scanReps rep suf).1, (scanReps rep suf).2)) ∧
  (minimal = false →
      scanReps rep (pre ++ suf) = (mask ++ List.replicate suf.length false, false))

theorem scanReps_cons_super (rep r : Finset Nat) (rs : List (Finset Nat))
    (h : supersededBy rep r = true) :
    scanReps rep (r :: rs) = (true :: (scanReps rep rs).1, (scanReps rep rs).2) := by
  simp only [scanReps, h, if_true]

theorem scanReps_cons_dom (rep r : Finset Nat) (rs : List (Finset Nat))
    (h1 : supersededBy rep r = false) (h2 : dominates rep r = true) :
    scanReps rep (r :: rs) = (false :: List.replicate rs.length false, false) := by
  unfold scanReps
  simp only [h1, h2, if_false, if_true, Bool.false_eq_true]

theorem scanReps_cons_neither (rep r : Finset Nat) (rs : List (Finset Nat))
    (h1 : supersededBy rep r = false) (h2 : dominates rep r = false) :
    scanReps rep (r :: rs) = (false :: (scanReps rep rs).1, (scanReps rep rs).2) := by
  conv_lhs => rw [scanReps]
  simp only [h1, h2, Bool.false_eq_true, if_false]

theorem scanReps_mask_length (rep : Finset Nat) (rs : List (Finset Nat)) :
    (scanReps rep rs).1.length = rs.length := by
  induction rs with
  | nil => rfl
  | cons r rs ih =>
    by_cases hs : supersededBy rep r = true
    · rw [scanReps_cons_super rep r rs hs]
      simp [ih]
    · simp only [Bool.not_eq_true] at hs
      by_cases hd : dominates rep r = true
      · rw [scanReps_cons_dom rep r rs hs hd]
        simp
      · simp only [Bool.not_eq_true] at hd
        rw [scanReps_cons_neither rep r rs hs hd]
        simp [ih]

theorem forIn_reifies_scan (rep : Finset Nat) :
    ∀ (L : List (Finset Nat)) (acc : List Bool),
      (Id.run do
        let mut minimal := true
        let mut mask : List Bool := acc
        for r in L do
          if r.card > rep.card && rep ⊆ r then
            mask := mask ++ [true]
          else if r.card < rep.card && r ⊆ rep then
            minimal := false
            break
          else
            mask := mask ++ [false]
        mask := mask ++ List.replicate (acc.length + L.length - mask.length) false
        return (mask, minimal))
        = (acc ++ (scanReps rep L).1, (scanReps rep L).2) := by
  intro L
  induction L with
  | nil => intro acc; simp [scanReps, Id.run, bind, pure]
  | cons r rs ih =>
    intro acc
    simp only [List.forIn_cons, bind, pure, Id.run]
    split_ifs with h1 h2
    · -- superseded: mask ++ [true], continue
      have hs : supersededBy rep r = true := h1
      rw [scanReps_cons_super rep r rs hs]
      have hih := ih (acc ++ [true])
      simp only [bind, pure, Id.run] at hih
      dsimp only
      rw [show acc.length + (r::rs).length = (acc++[true]).length + rs.length by simp; omega]
      rw [hih]; simp [List.append_assoc]
    · -- dominated: break
      have hs : supersededBy rep r = false := by
        simpa [supersededBy] using h1
      have hd : dominates rep r = true := by
        simpa [dominates] using h2
      rw [scanReps_cons_dom rep r rs hs hd]
      dsimp only
      rw [show acc.length + (r::rs).length - acc.length = rs.length + 1 by simp]
      rw [List.replicate_succ]
    · -- neither: mask ++ [false], continue
      have hs : supersededBy rep r = false := by
        simpa [supersededBy] using h1
      have hnd : dominates rep r = false := by
        simpa [dominates] using h2
      rw [scanReps_cons_neither rep r rs hs hnd]
      have hih := ih (acc ++ [false])
      simp only [bind, pure, Id.run] at hih
      dsimp only
      rw [show acc.length + (r::rs).length = (acc++[false]).length + rs.length by simp; omega]
      rw [hih]; simp [List.append_assoc]

theorem loop_scan_eq (rep : Finset Nat) (repBlocks : List (Finset Nat)) :
    (Id.run do
      let mut minimal := true
      let mut mask : List Bool := []
      for r in repBlocks do
        if r.card > rep.card && rep ⊆ r then
          mask := mask ++ [true]
        else if r.card < rep.card && r ⊆ rep then
          minimal := false
          break
        else
          mask := mask ++ [false]
      mask := mask ++ List.replicate (repBlocks.length - mask.length) false
      return (mask, minimal))
      = scanReps rep repBlocks := by
  have h := forIn_reifies_scan rep repBlocks []
  simpa using h

theorem tail_eq (blocks : List (List Int)) (numBlocks : List (List Nat))
    (repBlocks : List (Finset Nat)) (block : List Int) (numBlock : List Nat) (rep : Finset Nat)
    (hloop : (Id.run do
      let mut minimal := true
      let mut mask : List Bool := []
      for r in repBlocks do
        if r.card > rep.card && rep ⊆ r then
          mask := mask ++ [true]
        else if r.card < rep.card && r ⊆ rep then
          minimal := false
          break
        else
          mask := mask ++ [false]
      mask := mask ++ List.replicate (repBlocks.length - mask.length) false
      return (mask, minimal))
      = scanReps rep repBlocks) :
    implementation_pruneSystems blocks numBlocks repBlocks block numBlock rep
      = pruneSystems blocks numBlocks repBlocks block numBlock rep := by
  unfold implementation_pruneSystems pruneSystems
  rw [← hloop]
  rfl

theorem correct_pruneSystems :
    ∀ (blocks : List (List Int)) (numBlocks : List (List Nat)) (repBlocks : List (Finset Nat))
      (block : List Int) (numBlock : List Nat) (rep : Finset Nat),
      problem_spec_pruneSystems blocks numBlocks repBlocks block numBlock rep
        (implementation_pruneSystems blocks numBlocks repBlocks block numBlock rep) := by
  intro blocks numBlocks repBlocks block numBlock rep
  unfold problem_spec_pruneSystems
  exact tail_eq blocks numBlocks repBlocks block numBlock rep (loop_scan_eq rep repBlocks)

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for sympy__sympy-19954 (lean).

SAME-SPEC: all 7 attacks same_spec(Solution.lean, atk_N.lean, lean)=True (axioms/pure/pre/post regions byte-identical; only impl+proof edited).

### VERIFY (bash scripts/lean_verify.sh atk_N.lean):
- atk_1 (supersede >= instead of >): exit 1 (fails) — CORRECT REJECT.
- atk_2 (drop break on dominate): exit 1 — CORRECT REJECT.
- atk_3 (partial-domain: skip when repBlocks empty): exit 1 — CORRECT REJECT.
- atk_4 (dedup over UNpruned numBlocks): exit 1 — CORRECT REJECT.
- atk_5 (misalignment: omit rep append to repBlocks'): exit 1 — CORRECT REJECT.
- atk_6 (subset direction swap in supersede/dominate): exit 1 — CORRECT REJECT.
- atk_7 (ungrounded-oracle echo: impl := pruneSystems ...): exit 0 VERIFIES. #print axioms correct_pruneSystems = [propext, Quot.sound] — NO sorryAx, clean.
- pos_control (bundle Solution.lean): exit 0 verifies.

GENUINE-DIVERGENCE PROOF: for atk_1..6 I machine-checked (#eval, verify exit 0) concrete inputs where implementation != pruneSystems (files witness.lean, witness2.lean, witness_atk2.lean in scratch dir). These prove the exact-equality spec's exit-1 results are true rejections, not weak-tactic false negatives.

MANDATORY RESOLVE (protocol step 2) — atk_7 is the only same-spec impl with a closing clean-axiom proof, so its faithful refined patch MUST be run. atk_7 echoes pruneSystems, i.e. the exact post-patch gold behavior, so its faithful patch is byte-identical to patch.diff (saved at atk_7_faithful_patch.diff). EXECUTED harness (docker, run_evaluation, princeton-nlp/SWE-bench_Verified, namespace swebench, image swebench/sweb.eval.x86_64.sympy_1776_sympy-19954:latest): report sbu_patch.sbu_manual_19954.json => resolved_instances=1, resolved_ids=[sympy__sympy-19954], errors=0. RESOLVES. (The run_resolve() wrapper initially returned 'no report/image pull failure' because the instance image was not local; after docker pull the manual run_evaluation resolved cleanly — an infra artifact, not a resolve failure.) => atk_7 is a resolving echo, NOT a spec break, exactly as the echo-resolve policy requires.

A-LEG / DEEP-MODEL AUDIT (focus per instructions): refinement.md declares all 15 legs R/I with NO A-consumed and NO A-reference rows; the changed op (mask-prune vs running-index prune of the 3 parallel collections) is modeled DEEPLY as pure list functions over the observable inputs. axiom_check.py is a legitimate skip stub (no consumed callee axiom, no A-reference; SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed op). meta.json axioms=[], deep_model_references=[], opaque_callees=[] — consistent. No kind-3 (changed-inexpressible) leg. mapping.md type bijection (list[list[int]]->List (List Int), tuple->List Nat, set->Finset Nat, len->card, issubset->subset, mask-prune->dropFlagged) is sound over the real domain; only cardinality/subset/index-alignment are observable and all preserved. G-CONF (conformance_check.py, seed 19954, 150k inputs) is the differential check for the R legs and passes (meta G-CONF exit 0). No callee correspondence to falsify because there are no A-legs.

PREPATCH: Solution_prepatch.lean transliterates the running-index eraseIdx bug (del num_blocks[i],blocks[i] mid-scan; rep_blocks value-pruned after) with a sorry proof carrying the gold body — UNCLOSABLE against the buggy impl. G-DIFF recorded 'verification failed' => prepatch reproduced.

VERDICT: SOUND. 7 attacks run (6 correct rejects with machine-checked divergence witnesses + 1 resolving echo whose faithful=gold patch was EXECUTED through run_evaluation and RESOLVED); positive control verifies; A-legs are vacuous (all R/I, deep model) and their absence is consistent across refinement.md/mapping.md/axiom_check.py/meta.json. No same-spec impl with a closing clean-axiom proof has a non-resolving faithful patch. verify does not certify incorrectness here.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Independently reproduced the full mechanical baseline: (1) scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry); (2) appended `#print axioms correct_pruneSystems` -> depends on [propext, Classical.choice, Quot.sound], NO sorryAx, so the proof genuinely closes (not fake); (3) spec_signature/same_spec stable + idempotent, and the spec-constituting region hashes (axioms/pure/post-conditions) all MATCH meta.json.

Ran my OWN differential fuzz (independent transliteration of the Lean REFERENCE scanReps/dropFlagged/pruneSystems, not the bundled shadow) against the verbatim post-patch Python inner block from the gold patch.diff:
- 400,000 random EQUAL-LENGTH (on-precondition) inputs: 0 disagreements.
- 18,056 EXHAUSTIVE equal-length configs (subsets of {0,1,2}, up to 3 retained systems, all candidate rep/num_block incl. dedup collisions): 0 disagreements.
- 200,000 unequal-length inputs: divergence appears ONLY here (85,824 cases) — real Python raises IndexError (blocks_remove_mask length = len(blocks) but indexed by i into rep_blocks), Lean model is total.

Reachability check on the real callee: read PermutationGroup.minimal_blocks at base_commit 6f54459aa0248bf1467ad12ee6333d8bc924a642. blocks, num_blocks, rep_blocks all init [] and are only ever appended together (in the `if minimal and num_block not in num_blocks` branch) or pruned together by the same mask (post-patch). Equal length is therefore a genuine loop invariant, so unequal-length inputs are UNREACHABLE. The modeled function agrees with the real post-patch callee on every reachable input.

Subtle faithfulness points confirmed: scanReps retains pre-break supersession flags (matches Python never discarding pre-break blocks_remove_mask[i]=True); dropFlagged with mask length = list length (proved by scanReps_mask_length, guaranteed on-precondition) is an exact positional drop = the Python list comprehensions; post-loop dedup uses the PRUNED num_blocks in both. Verdict: spec is neither too strong nor drifting -> FAITHFUL.

Counterexample / evidence:

```
Real post-patch Python raises IndexError on the above unequal-length input; Lean pruneSystems returns ([[999]],[(777,)],[{1,4,7},{2,4,5},{1,3,4,6,7},{0,2,6,7}]). No divergence exists on any equal-length (on-precondition, i.e. reachable) input.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Lean bundle sympy__sympy-19954. Mechanical screen (leakage.screen) PASSES with zero hard failures; same_spec(post, prepatch)=True (spec region byte-identical). No RELAXED_LEAKAGE.md, relaxed_leakage flag absent, so this is a strict NO-LEAKAGE judgment, not a deferral.

Gold edit: in minimal_blocks' inner candidate-update block, replace the in-loop `del num_blocks[i], blocks[i]` + `to_remove` value-prune of rep_blocks with a `blocks_remove_mask=[False]*len(blocks)` set during the scan, then rebuild blocks/num_blocks/rep_blocks by the same mask after the loop.

Public problem_statement already discloses: the method `minimal_blocks`/`sylow_subgroup`, the collections num_blocks/blocks, and the exact buggy line `del num_blocks[i], blocks[i]` raising IndexError (i.e. deletion-by-index during iteration misaligns parallel lists). The gold fix is the obvious remedy to that public traceback.

Spec-view content beyond problem_statement: the view is fully abstracted to invented generic names (pruneSystems, supersededBy, dominates, scanReps, dropFlagged, blocks/numBlocks/repBlocks). No sympy/sylow/minimal_blocks/perm_groups/_number_blocks tokens; no patched file path, module path, diff markers, or bug/fix narration. The mechanically-detected patched symbol `number_blocks` is absent from the view. Impl and proof regions are elided as required. The docstring's alignment guarantee ('dropped from ALL THREE collections together … never from one collection by position while another is pruned by value') is the correct behavior a spec MUST state, and its contrast (index-vs-value misalignment) is already implied by the public IndexError traceback — it does not name the edit, quote the diff, or point at the repo location.

A solver reading this self-contained spec gains no gold-reconstruction handle beyond the public problem_statement. Intended difficulty preserved. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
