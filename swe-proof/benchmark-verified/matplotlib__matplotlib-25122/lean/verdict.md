# P2 adversarial audit — matplotlib__matplotlib-25122

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — the spec admits no wrong-but-closing impl. The spec problem_spec_windowCorrectionFactor is a total functional EQUALITY (result pinned to exactly one value per (window,mode,scaleByFreq)); any impl that closes correct_windowCorrectionFactor is extensionally the gold function, so its faithful patch is the gold divisor set {window.sum(), (window**2).sum(), window.sum()**2, 1} which resolves.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,83 +80,32 @@
     (window : List Rat) (mode : Mode) (scaleByFreq : Bool) : Rat := Id.run do
   match mode with
   | Mode.magnitude | Mode.complex =>
-      -- amplitude-style: divide by the signed total of the window samples
       let mut s : Rat := 0
       for w in window do
-        s := s + w
+        s := s + |w|
       return s
   | Mode.psd =>
       if scaleByFreq then
-        -- density per unit frequency: divide by the total of the squared samples
         let mut sq : Rat := 0
         for w in window do
           sq := sq + w * w
         return sq
       else
-        -- power preserved per segment: divide by the square of the signed total
         let mut s : Rat := 0
         for w in window do
-          s := s + w
+          s := s + |w|
         return s * s
   | Mode.angle | Mode.phase =>
-      -- phase-style: no window correction
       return 1
 -- impl-end
 
 -- proof-start
-/-- The signed-sum loop accumulates to `init + window.sum`, generalized over the
-accumulator (Route B helper). -/
-theorem sum_loop_windowCorrectionFactor (window : List Rat) (init : Rat) :
-    (Id.run (forIn window init (fun w r => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r + w))))) = init + window.sum := by
-  induction window generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, List.sum_nil, add_zero]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]; rw [List.sum_cons]; ring
-
-/-- The squared-sum loop accumulates to `init + (window.map (·*·)).sum`. -/
-theorem sumsq_loop_windowCorrectionFactor (window : List Rat) (init : Rat) :
-    (Id.run (forIn window init (fun w r => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r + w * w))))) = init + (window.map (fun w => w * w)).sum := by
-  induction window generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.sum_nil, add_zero]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]; rw [List.map_cons, List.sum_cons]; ring
-
 theorem correct_windowCorrectionFactor :
     ∀ (window : List Rat) (mode : Mode) (scaleByFreq : Bool),
       problem_spec_windowCorrectionFactor window mode scaleByFreq
         (implementation_windowCorrectionFactor window mode scaleByFreq) := by
   intro window mode scaleByFreq
   unfold problem_spec_windowCorrectionFactor implementation_windowCorrectionFactor
-  cases mode with
-  | magnitude =>
-      simp only [Id.run]
-      have h := sum_loop_windowCorrectionFactor window 0
-      simp only [Id.run] at h
-      rw [h]; simp
-  | complex =>
-      simp only [Id.run]
-      have h := sum_loop_windowCorrectionFactor window 0
-      simp only [Id.run] at h
-      rw [h]; simp
-  | psd =>
-      by_cases hs : scaleByFreq
-      · subst hs
-        simp only [Id.run, if_true]
-        have h := sumsq_loop_windowCorrectionFactor window 0
-        simp only [Id.run] at h
-        rw [h]; simp
-      · simp only [hs, Bool.false_eq_true, if_false, Id.run]
-        have h := sum_loop_windowCorrectionFactor window 0
-        simp only [Id.run] at h
-        rw [h]; simp only [zero_add]; rfl
-  | angle => rfl
-  | phase => rfl
+  cases mode <;> simp_all [Id.run] <;> try rfl
+  all_goals (induction window <;> simp_all [Id.run] <;> try ring)
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,83 +80,32 @@
     (window : List Rat) (mode : Mode) (scaleByFreq : Bool) : Rat := Id.run do
   match mode with
   | Mode.magnitude | Mode.complex =>
-      -- amplitude-style: divide by the signed total of the window samples
       let mut s : Rat := 0
       for w in window do
         s := s + w
       return s
   | Mode.psd =>
       if scaleByFreq then
-        -- density per unit frequency: divide by the total of the squared samples
         let mut sq : Rat := 0
         for w in window do
           sq := sq + w * w
         return sq
       else
-        -- power preserved per segment: divide by the square of the signed total
         let mut s : Rat := 0
         for w in window do
           s := s + w
         return s * s
-  | Mode.angle | Mode.phase =>
-      -- phase-style: no window correction
-      return 1
+  | Mode.angle => return 0
+  | Mode.phase => return 1
 -- impl-end
 
 -- proof-start
-/-- The signed-sum loop accumulates to `init + window.sum`, generalized over the
-accumulator (Route B helper). -/
-theorem sum_loop_windowCorrectionFactor (window : List Rat) (init : Rat) :
-    (Id.run (forIn window init (fun w r => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r + w))))) = init + window.sum := by
-  induction window generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, List.sum_nil, add_zero]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]; rw [List.sum_cons]; ring
-
-/-- The squared-sum loop accumulates to `init + (window.map (·*·)).sum`. -/
-theorem sumsq_loop_windowCorrectionFactor (window : List Rat) (init : Rat) :
-    (Id.run (forIn window init (fun w r => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r + w * w))))) = init + (window.map (fun w => w * w)).sum := by
-  induction window generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.sum_nil, add_zero]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]; rw [List.map_cons, List.sum_cons]; ring
-
 theorem correct_windowCorrectionFactor :
     ∀ (window : List Rat) (mode : Mode) (scaleByFreq : Bool),
       problem_spec_windowCorrectionFactor window mode scaleByFreq
         (implementation_windowCorrectionFactor window mode scaleByFreq) := by
   intro window mode scaleByFreq
   unfold problem_spec_windowCorrectionFactor implementation_windowCorrectionFactor
-  cases mode with
-  | magnitude =>
-      simp only [Id.run]
-      have h := sum_loop_windowCorrectionFactor window 0
-      simp only [Id.run] at h
-      rw [h]; simp
-  | complex =>
-      simp only [Id.run]
-      have h := sum_loop_windowCorrectionFactor window 0
-      simp only [Id.run] at h
-      rw [h]; simp
-  | psd =>
-      by_cases hs : scaleByFreq
-      · subst hs
-        simp only [Id.run, if_true]
-        have h := sumsq_loop_windowCorrectionFactor window 0
-        simp only [Id.run] at h
-        rw [h]; simp
-      · simp only [hs, Bool.false_eq_true, if_false, Id.run]
-        have h := sum_loop_windowCorrectionFactor window 0
-        simp only [Id.run] at h
-        rw [h]; simp only [zero_add]; rfl
-  | angle => rfl
-  | phase => rfl
+  cases mode <;> simp_all [Id.run] <;> try rfl
+  all_goals (induction window <;> simp_all [Id.run] <;> try ring)
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,83 +80,34 @@
     (window : List Rat) (mode : Mode) (scaleByFreq : Bool) : Rat := Id.run do
   match mode with
   | Mode.magnitude | Mode.complex =>
-      -- amplitude-style: divide by the signed total of the window samples
       let mut s : Rat := 0
       for w in window do
         s := s + w
       return s
   | Mode.psd =>
       if scaleByFreq then
-        -- density per unit frequency: divide by the total of the squared samples
+        -- WRONG: return square of signed total instead of sum of squares
+        let mut s : Rat := 0
+        for w in window do
+          s := s + w
+        return s * s
+      else
+        -- WRONG: return sum of squares instead of square of signed total
         let mut sq : Rat := 0
         for w in window do
           sq := sq + w * w
         return sq
-      else
-        -- power preserved per segment: divide by the square of the signed total
-        let mut s : Rat := 0
-        for w in window do
-          s := s + w
-        return s * s
   | Mode.angle | Mode.phase =>
-      -- phase-style: no window correction
       return 1
 -- impl-end
 
 -- proof-start
-/-- The signed-sum loop accumulates to `init + window.sum`, generalized over the
-accumulator (Route B helper). -/
-theorem sum_loop_windowCorrectionFactor (window : List Rat) (init : Rat) :
-    (Id.run (forIn window init (fun w r => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r + w))))) = init + window.sum := by
-  induction window generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, List.sum_nil, add_zero]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]; rw [List.sum_cons]; ring
-
-/-- The squared-sum loop accumulates to `init + (window.map (·*·)).sum`. -/
-theorem sumsq_loop_windowCorrectionFactor (window : List Rat) (init : Rat) :
-    (Id.run (forIn window init (fun w r => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r + w * w))))) = init + (window.map (fun w => w * w)).sum := by
-  induction window generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.sum_nil, add_zero]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]; rw [List.map_cons, List.sum_cons]; ring
-
 theorem correct_windowCorrectionFactor :
     ∀ (window : List Rat) (mode : Mode) (scaleByFreq : Bool),
       problem_spec_windowCorrectionFactor window mode scaleByFreq
         (implementation_windowCorrectionFactor window mode scaleByFreq) := by
   intro window mode scaleByFreq
   unfold problem_spec_windowCorrectionFactor implementation_windowCorrectionFactor
-  cases mode with
-  | magnitude =>
-      simp only [Id.run]
-      have h := sum_loop_windowCorrectionFactor window 0
-      simp only [Id.run] at h
-      rw [h]; simp
-  | complex =>
-      simp only [Id.run]
-      have h := sum_loop_windowCorrectionFactor window 0
-      simp only [Id.run] at h
-      rw [h]; simp
-  | psd =>
-      by_cases hs : scaleByFreq
-      · subst hs
-        simp only [Id.run, if_true]
-        have h := sumsq_loop_windowCorrectionFactor window 0
-        simp only [Id.run] at h
-        rw [h]; simp
-      · simp only [hs, Bool.false_eq_true, if_false, Id.run]
-        have h := sum_loop_windowCorrectionFactor window 0
-        simp only [Id.run] at h
-        rw [h]; simp only [zero_add]; rfl
-  | angle => rfl
-  | phase => rfl
+  cases mode <;> simp_all [Id.run] <;> try rfl
+  all_goals (induction window <;> simp_all [Id.run] <;> try ring)
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,83 +80,33 @@
     (window : List Rat) (mode : Mode) (scaleByFreq : Bool) : Rat := Id.run do
   match mode with
   | Mode.magnitude | Mode.complex =>
-      -- amplitude-style: divide by the signed total of the window samples
-      let mut s : Rat := 0
+      -- WRONG: initialize accumulator at 1 instead of 0
+      let mut s : Rat := 1
       for w in window do
         s := s + w
       return s
   | Mode.psd =>
       if scaleByFreq then
-        -- density per unit frequency: divide by the total of the squared samples
         let mut sq : Rat := 0
         for w in window do
           sq := sq + w * w
         return sq
       else
-        -- power preserved per segment: divide by the square of the signed total
         let mut s : Rat := 0
         for w in window do
           s := s + w
         return s * s
   | Mode.angle | Mode.phase =>
-      -- phase-style: no window correction
       return 1
 -- impl-end
 
 -- proof-start
-/-- The signed-sum loop accumulates to `init + window.sum`, generalized over the
-accumulator (Route B helper). -/
-theorem sum_loop_windowCorrectionFactor (window : List Rat) (init : Rat) :
-    (Id.run (forIn window init (fun w r => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r + w))))) = init + window.sum := by
-  induction window generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, List.sum_nil, add_zero]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]; rw [List.sum_cons]; ring
-
-/-- The squared-sum loop accumulates to `init + (window.map (·*·)).sum`. -/
-theorem sumsq_loop_windowCorrectionFactor (window : List Rat) (init : Rat) :
-    (Id.run (forIn window init (fun w r => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r + w * w))))) = init + (window.map (fun w => w * w)).sum := by
-  induction window generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.sum_nil, add_zero]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]; rw [List.map_cons, List.sum_cons]; ring
-
 theorem correct_windowCorrectionFactor :
     ∀ (window : List Rat) (mode : Mode) (scaleByFreq : Bool),
       problem_spec_windowCorrectionFactor window mode scaleByFreq
         (implementation_windowCorrectionFactor window mode scaleByFreq) := by
   intro window mode scaleByFreq
   unfold problem_spec_windowCorrectionFactor implementation_windowCorrectionFactor
-  cases mode with
-  | magnitude =>
-      simp only [Id.run]
-      have h := sum_loop_windowCorrectionFactor window 0
-      simp only [Id.run] at h
-      rw [h]; simp
-  | complex =>
-      simp only [Id.run]
-      have h := sum_loop_windowCorrectionFactor window 0
-      simp only [Id.run] at h
-      rw [h]; simp
-  | psd =>
-      by_cases hs : scaleByFreq
-      · subst hs
-        simp only [Id.run, if_true]
-        have h := sumsq_loop_windowCorrectionFactor window 0
-        simp only [Id.run] at h
-        rw [h]; simp
-      · simp only [hs, Bool.false_eq_true, if_false, Id.run]
-        have h := sum_loop_windowCorrectionFactor window 0
-        simp only [Id.run] at h
-        rw [h]; simp only [zero_add]; rfl
-  | angle => rfl
-  | phase => rfl
+  cases mode <;> simp_all [Id.run] <;> try rfl
+  all_goals (induction window <;> simp_all [Id.run] <;> try ring)
 -- proof-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -77,86 +77,23 @@
 
 -- impl-start
 def implementation_windowCorrectionFactor
-    (window : List Rat) (mode : Mode) (scaleByFreq : Bool) : Rat := Id.run do
+    (window : List Rat) (mode : Mode) (scaleByFreq : Bool) : Rat :=
   match mode with
-  | Mode.magnitude | Mode.complex =>
-      -- amplitude-style: divide by the signed total of the window samples
-      let mut s : Rat := 0
-      for w in window do
-        s := s + w
-      return s
-  | Mode.psd =>
-      if scaleByFreq then
-        -- density per unit frequency: divide by the total of the squared samples
-        let mut sq : Rat := 0
-        for w in window do
-          sq := sq + w * w
-        return sq
-      else
-        -- power preserved per segment: divide by the square of the signed total
-        let mut s : Rat := 0
-        for w in window do
-          s := s + w
-        return s * s
-  | Mode.angle | Mode.phase =>
-      -- phase-style: no window correction
-      return 1
+  | Mode.magnitude => window.sum
+  | Mode.complex   => window.sum
+  | Mode.psd       =>
+      if scaleByFreq then (window.map (fun w => w * w)).sum
+      else window.sum * window.sum
+  | Mode.angle     => 1
+  | Mode.phase     => 1
 -- impl-end
 
 -- proof-start
-/-- The signed-sum loop accumulates to `init + window.sum`, generalized over the
-accumulator (Route B helper). -/
-theorem sum_loop_windowCorrectionFactor (window : List Rat) (init : Rat) :
-    (Id.run (forIn window init (fun w r => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r + w))))) = init + window.sum := by
-  induction window generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, List.sum_nil, add_zero]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]; rw [List.sum_cons]; ring
-
-/-- The squared-sum loop accumulates to `init + (window.map (·*·)).sum`. -/
-theorem sumsq_loop_windowCorrectionFactor (window : List Rat) (init : Rat) :
-    (Id.run (forIn window init (fun w r => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r + w * w))))) = init + (window.map (fun w => w * w)).sum := by
-  induction window generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.sum_nil, add_zero]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]; rw [List.map_cons, List.sum_cons]; ring
-
 theorem correct_windowCorrectionFactor :
     ∀ (window : List Rat) (mode : Mode) (scaleByFreq : Bool),
       problem_spec_windowCorrectionFactor window mode scaleByFreq
         (implementation_windowCorrectionFactor window mode scaleByFreq) := by
   intro window mode scaleByFreq
   unfold problem_spec_windowCorrectionFactor implementation_windowCorrectionFactor
-  cases mode with
-  | magnitude =>
-      simp only [Id.run]
-      have h := sum_loop_windowCorrectionFactor window 0
-      simp only [Id.run] at h
-      rw [h]; simp
-  | complex =>
-      simp only [Id.run]
-      have h := sum_loop_windowCorrectionFactor window 0
-      simp only [Id.run] at h
-      rw [h]; simp
-  | psd =>
-      by_cases hs : scaleByFreq
-      · subst hs
-        simp only [Id.run, if_true]
-        have h := sumsq_loop_windowCorrectionFactor window 0
-        simp only [Id.run] at h
-        rw [h]; simp
-      · simp only [hs, Bool.false_eq_true, if_false, Id.run]
-        have h := sum_loop_windowCorrectionFactor window 0
-        simp only [Id.run] at h
-        rw [h]; simp only [zero_add]; rfl
-  | angle => rfl
-  | phase => rfl
+  cases mode <;> rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,83 +80,33 @@
     (window : List Rat) (mode : Mode) (scaleByFreq : Bool) : Rat := Id.run do
   match mode with
   | Mode.magnitude | Mode.complex =>
-      -- amplitude-style: divide by the signed total of the window samples
-      let mut s : Rat := 0
+      -- WRONG: sum of squares instead of signed sum
+      let mut sq : Rat := 0
       for w in window do
-        s := s + w
-      return s
+        sq := sq + w * w
+      return sq
   | Mode.psd =>
       if scaleByFreq then
-        -- density per unit frequency: divide by the total of the squared samples
         let mut sq : Rat := 0
         for w in window do
           sq := sq + w * w
         return sq
       else
-        -- power preserved per segment: divide by the square of the signed total
         let mut s : Rat := 0
         for w in window do
           s := s + w
         return s * s
   | Mode.angle | Mode.phase =>
-      -- phase-style: no window correction
       return 1
 -- impl-end
 
 -- proof-start
-/-- The signed-sum loop accumulates to `init + window.sum`, generalized over the
-accumulator (Route B helper). -/
-theorem sum_loop_windowCorrectionFactor (window : List Rat) (init : Rat) :
-    (Id.run (forIn window init (fun w r => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r + w))))) = init + window.sum := by
-  induction window generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, List.sum_nil, add_zero]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]; rw [List.sum_cons]; ring
-
-/-- The squared-sum loop accumulates to `init + (window.map (·*·)).sum`. -/
-theorem sumsq_loop_windowCorrectionFactor (window : List Rat) (init : Rat) :
-    (Id.run (forIn window init (fun w r => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r + w * w))))) = init + (window.map (fun w => w * w)).sum := by
-  induction window generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.sum_nil, add_zero]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]; rw [List.map_cons, List.sum_cons]; ring
-
 theorem correct_windowCorrectionFactor :
     ∀ (window : List Rat) (mode : Mode) (scaleByFreq : Bool),
       problem_spec_windowCorrectionFactor window mode scaleByFreq
         (implementation_windowCorrectionFactor window mode scaleByFreq) := by
   intro window mode scaleByFreq
   unfold problem_spec_windowCorrectionFactor implementation_windowCorrectionFactor
-  cases mode with
-  | magnitude =>
-      simp only [Id.run]
-      have h := sum_loop_windowCorrectionFactor window 0
-      simp only [Id.run] at h
-      rw [h]; simp
-  | complex =>
-      simp only [Id.run]
-      have h := sum_loop_windowCorrectionFactor window 0
-      simp only [Id.run] at h
-      rw [h]; simp
-  | psd =>
-      by_cases hs : scaleByFreq
-      · subst hs
-        simp only [Id.run, if_true]
-        have h := sumsq_loop_windowCorrectionFactor window 0
-        simp only [Id.run] at h
-        rw [h]; simp
-      · simp only [hs, Bool.false_eq_true, if_false, Id.run]
-        have h := sum_loop_windowCorrectionFactor window 0
-        simp only [Id.run] at h
-        rw [h]; simp only [zero_add]; rfl
-  | angle => rfl
-  | phase => rfl
+  cases mode <;> simp_all [Id.run] <;> try rfl
+  all_goals (induction window <;> simp_all [Id.run] <;> try ring)
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,84 +79,36 @@
 def implementation_windowCorrectionFactor
     (window : List Rat) (mode : Mode) (scaleByFreq : Bool) : Rat := Id.run do
   match mode with
-  | Mode.magnitude | Mode.complex =>
-      -- amplitude-style: divide by the signed total of the window samples
+  | Mode.magnitude =>
       let mut s : Rat := 0
       for w in window do
         s := s + w
       return s
+  | Mode.complex =>
+      -- WRONG: complex applies no correction
+      return 1
   | Mode.psd =>
       if scaleByFreq then
-        -- density per unit frequency: divide by the total of the squared samples
         let mut sq : Rat := 0
         for w in window do
           sq := sq + w * w
         return sq
       else
-        -- power preserved per segment: divide by the square of the signed total
         let mut s : Rat := 0
         for w in window do
           s := s + w
         return s * s
   | Mode.angle | Mode.phase =>
-      -- phase-style: no window correction
       return 1
 -- impl-end
 
 -- proof-start
-/-- The signed-sum loop accumulates to `init + window.sum`, generalized over the
-accumulator (Route B helper). -/
-theorem sum_loop_windowCorrectionFactor (window : List Rat) (init : Rat) :
-    (Id.run (forIn window init (fun w r => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r + w))))) = init + window.sum := by
-  induction window generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, List.sum_nil, add_zero]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]; rw [List.sum_cons]; ring
-
-/-- The squared-sum loop accumulates to `init + (window.map (·*·)).sum`. -/
-theorem sumsq_loop_windowCorrectionFactor (window : List Rat) (init : Rat) :
-    (Id.run (forIn window init (fun w r => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r + w * w))))) = init + (window.map (fun w => w * w)).sum := by
-  induction window generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.sum_nil, add_zero]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]; rw [List.map_cons, List.sum_cons]; ring
-
 theorem correct_windowCorrectionFactor :
     ∀ (window : List Rat) (mode : Mode) (scaleByFreq : Bool),
       problem_spec_windowCorrectionFactor window mode scaleByFreq
         (implementation_windowCorrectionFactor window mode scaleByFreq) := by
   intro window mode scaleByFreq
   unfold problem_spec_windowCorrectionFactor implementation_windowCorrectionFactor
-  cases mode with
-  | magnitude =>
-      simp only [Id.run]
-      have h := sum_loop_windowCorrectionFactor window 0
-      simp only [Id.run] at h
-      rw [h]; simp
-  | complex =>
-      simp only [Id.run]
-      have h := sum_loop_windowCorrectionFactor window 0
-      simp only [Id.run] at h
-      rw [h]; simp
-  | psd =>
-      by_cases hs : scaleByFreq
-      · subst hs
-        simp only [Id.run, if_true]
-        have h := sumsq_loop_windowCorrectionFactor window 0
-        simp only [Id.run] at h
-        rw [h]; simp
-      · simp only [hs, Bool.false_eq_true, if_false, Id.run]
-        have h := sum_loop_windowCorrectionFactor window 0
-        simp only [Id.run] at h
-        rw [h]; simp only [zero_add]; rfl
-  | angle => rfl
-  | phase => rfl
+  cases mode <;> simp_all [Id.run] <;> try rfl
+  all_goals (induction window <;> simp_all [Id.run] <;> try ring)
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Computing the normalization factor used to compensate a windowed spectrum for the
energy/amplitude lost to the analysis window.

When a signal segment is multiplied by an analysis window before its spectrum is
taken, the spectrum must be divided by a *window-correction factor* to undo the
scaling the window introduced. The factor is built from the window's own samples
and depends on which spectrum is being produced:

* for an amplitude-style spectrum (a magnitude spectrum, or a complex spectrum),
  the factor is the (signed) total of the window samples;
* for a power-style spectrum:
  - when the spectrum is expressed as a density per unit frequency, the factor is
    the total of the squared window samples;
  - otherwise (power preserved per segment), the factor is the square of the
    signed total of the window samples;
* for a phase-style spectrum (an angle or phase spectrum), no window correction is
  applied (the factor is `1`).

The window samples are real numbers and MAY BE NEGATIVE (for example, windows
whose side lobes dip below zero). The total of the window samples must therefore
be taken with sign — it is the arithmetic sum of the samples, NOT the sum of their
sizes. These two agree for an all-nonnegative window but differ once any sample is
negative.

Stated as an input→output relation (window samples, spectrum kind, density flag) ↦
factor. The implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The window
-- samples enter as plain data (`List Rat`) and the only operations are the
-- reductions that build the factor (a sum and a sum of squares), both modeled
-- deeply below. Hence no `opaque`/`axiom` callee contract is required.

/-- Which spectrum is being produced. Each constructor selects a different
window-correction factor (see `problem_spec_windowCorrectionFactor`). -/
inductive Mode
  | magnitude
  | complex
  | psd
  | angle
  | phase
deriving DecidableEq, Repr
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The window-correction factor as a function of the window samples, the
spectrum kind, and the density flag. Every case is pinned to the inputs:

* `magnitude` / `complex` → the signed total of the window samples;
* `psd` with `scaleByFreq = true` → the total of the squared samples;
* `psd` with `scaleByFreq = false` → the square of the signed total;
* `angle` / `phase` → `1` (no correction).

The signed total `window.sum` is the discriminating quantity: it is the
arithmetic sum (which may be reduced by negative samples), never the sum of
sample magnitudes. -/
def problem_spec_windowCorrectionFactor
    (window : List Rat) (mode : Mode) (scaleByFreq : Bool) (result : Rat) : Prop :=
  result = (match mode with
    | Mode.magnitude => window.sum
    | Mode.complex   => window.sum
    | Mode.psd       =>
        if scaleByFreq then (window.map (fun w => w * w)).sum
        else window.sum * window.sum
    | Mode.angle     => 1
    | Mode.phase     => 1)
-- post-conditions-end

-- impl-start
def implementation_windowCorrectionFactor
    (window : List Rat) (mode : Mode) (scaleByFreq : Bool) : Rat := Id.run do
  match mode with
  | Mode.magnitude | Mode.complex =>
      -- amplitude-style: divide by the signed total of the window samples
      let mut s : Rat := 0
      for w in window do
        s := s + w
      return s
  | Mode.psd =>
      if scaleByFreq then
        -- density per unit frequency: divide by the total of the squared samples
        let mut sq : Rat := 0
        for w in window do
          sq := sq + w * w
        return sq
      else
        -- power preserved per segment: divide by the square of the signed total
        let mut s : Rat := 0
        for w in window do
          s := s + w
        return s * s
  | Mode.angle | Mode.phase =>
      -- phase-style: no window correction
      return 1
-- impl-end

-- proof-start
/-- The signed-sum loop accumulates to `init + window.sum`, generalized over the
accumulator (Route B helper). -/
theorem sum_loop_windowCorrectionFactor (window : List Rat) (init : Rat) :
    (Id.run (forIn window init (fun w r => do
            pure PUnit.unit
            pure (ForInStep.yield (r + w))))) = init + window.sum := by
  induction window generalizing init with
  | nil => simp only [List.forIn_nil, Id.run, List.sum_nil, add_zero]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    rw [ih]; rw [List.sum_cons]; ring

/-- The squared-sum loop accumulates to `init + (window.map (·*·)).sum`. -/
theorem sumsq_loop_windowCorrectionFactor (window : List Rat) (init : Rat) :
    (Id.run (forIn window init (fun w r => do
            pure PUnit.unit
            pure (ForInStep.yield (r + w * w))))) = init + (window.map (fun w => w * w)).sum := by
  induction window generalizing init with
  | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.sum_nil, add_zero]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    rw [ih]; rw [List.map_cons, List.sum_cons]; ring

theorem correct_windowCorrectionFactor :
    ∀ (window : List Rat) (mode : Mode) (scaleByFreq : Bool),
      problem_spec_windowCorrectionFactor window mode scaleByFreq
        (implementation_windowCorrectionFactor window mode scaleByFreq) := by
  intro window mode scaleByFreq
  unfold problem_spec_windowCorrectionFactor implementation_windowCorrectionFactor
  cases mode with
  | magnitude =>
      simp only [Id.run]
      have h := sum_loop_windowCorrectionFactor window 0
      simp only [Id.run] at h
      rw [h]; simp
  | complex =>
      simp only [Id.run]
      have h := sum_loop_windowCorrectionFactor window 0
      simp only [Id.run] at h
      rw [h]; simp
  | psd =>
      by_cases hs : scaleByFreq
      · subst hs
        simp only [Id.run, if_true]
        have h := sumsq_loop_windowCorrectionFactor window 0
        simp only [Id.run] at h
        rw [h]; simp
      · simp only [hs, Bool.false_eq_true, if_false, Id.run]
        have h := sum_loop_windowCorrectionFactor window 0
        simp only [Id.run] at h
        rw [h]; simp only [zero_add]; rfl
  | angle => rfl
  | phase => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: all files built by copying Solution.lean and editing ONLY the impl+proof regions (axioms/pure/pre/post byte-identical). same_spec=True verified for all 7 attacks + pos_control (lean backend). Verifications run concurrently in batches of 4 via scripts/lean_verify.sh.

### RESULTS (path | desc | same_spec | lean_verify exit | axioms | resolve):
- pos_control | gold impl (Id.run signed-sum folds) | True | EXIT 0 | [propext,Classical.choice,Quot.sound] clean, no sorryAx | (is gold)
- atk_1 | PREPATCH BUG: magnitude/complex/psd-false use Sigma|w| (sum of magnitudes) | True | EXIT 1 (goal reduces to Sigma|w|=Sigma w, false on [-1]; ring fails) | n/a | n/a
- atk_2 | boundary: angle returns 0 instead of 1 | True | EXIT 1 | n/a | n/a
- atk_3 | control-flow: psd scaleByFreq true/false branches swapped | True | EXIT 1 | n/a | n/a
- atk_4 | off-by-one: magnitude accumulator initialized at 1 not 0 | True | EXIT 1 | n/a | n/a
- atk_5 | ungrounded-oracle ECHO: direct return of spec value (cases mode <;> rfl) | True | EXIT 0 | [propext,Classical.choice,Quot.sound] clean, no sorryAx | RESOLVED=True COMPLETED=True (official run_resolve, faithful patch = gold divisors)
- atk_6 | boundary: magnitude uses Sigma w^2 (sum of squares) | True | EXIT 1 | n/a | n/a
- atk_7 | control-flow-effect: complex returns 1 (no correction) | True | EXIT 1 | n/a | n/a

Exact commands: bash scripts/lean_verify.sh <f>.lean ; #print axioms appended for pos_control/atk_5 (both clean); resolve via python -c 'from swebench_unified.harness import run_resolve; run_resolve("matplotlib__matplotlib-25122", patch)' -> RESOLVED=True COMPLETED=True NOTE=resolved.

prepatch_reproduced: atk_1 faithfully reintroduces the reported bug (np.abs(window).sum()) and correctly FAILS to verify (spec rejects it) — matching Solution_prepatch.lean which carries the |w| impl with a sorry proof.

Step 2 obligation satisfied: the ONLY wrong-shaped impl whose proof closes with clean axioms is atk_5 (extensionally identical to gold), and its materialized faithful refined patch RESOLVES under the official harness. No closing impl exists whose faithful patch does NOT resolve. verify => correct holds here: the spec is an exact functional equality with no slack.

A-LEG AUDIT (refinement.md): 4 legs, ALL tagged R (type refinement). Zero A-consumed, zero A-reference. No kind-3 leg. Consistent with the model: the window-correction divisor is a pure List.sum / (List.map (.*.)).sum reduction spelled out deeply as for-loop folds; no opaque/axiom callee contract. mapping.md 'Callee provenance' = None: fft/detrend/_stride_windows/np.angle/np.abs(result) are all DOWNSTREAM of the modeled boundary (they act on `result`, not on the window factor), so there is no deep-model correspondence obligation to break. axioms-start block only declares the Mode inductive (data), no axiom/opaque. A-legs are vacuous — nothing to falsify there.

Verdict SOUND: >=5 distinct same-spec wrong impls attacked (prepatch bug + 5 more distinct: boundary angle->0, branch-swap, off-by-one init, magnitude->sum-of-squares, complex->1), none breaks the spec; the sole closing echo resolves.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — the spec admits no wrong-but-closing impl. The spec problem_spec_windowCorrectionFactor is a total functional EQUALITY (result pinned to exactly one value per (window,mode,scaleByFreq)); any impl that closes correct_windowCorrectionFactor is extensionally the gold function, so its faithful patch is the gold divisor set {window.sum(), (window**2).sum(), window.sum()**2, 1} which resolves.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Computing the normalization factor used to compensate a windowed spectrum for the
energy/amplitude lost to the analysis window.

When a signal segment is multiplied by an analysis window before its spectrum is
taken, the spectrum must be divided by a *window-correction factor* to undo the
scaling the window introduced. The factor is built from the window's own samples
and depends on which spectrum is being produced:

* for an amplitude-style spectrum (a magnitude spectrum, or a complex spectrum),
  the factor is the (signed) total of the window samples;
* for a power-style spectrum:
  - when the spectrum is expressed as a density per unit frequency, the factor is
    the total of the squared window samples;
  - otherwise (power preserved per segment), the factor is the square of the
    signed total of the window samples;
* for a phase-style spectrum (an angle or phase spectrum), no window correction is
  applied (the factor is `1`).

The window samples are real numbers and MAY BE NEGATIVE (for example, windows
whose side lobes dip below zero). The total of the window samples must therefore
be taken with sign — it is the arithmetic sum of the samples, NOT the sum of their
sizes. These two agree for an all-nonnegative window but differ once any sample is
negative.

Stated as an input→output relation (window samples, spectrum kind, density flag) ↦
factor. The implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The window
-- samples enter as plain data (`List Rat`) and the only operations are the
-- reductions that build the factor (a sum and a sum of squares), both modeled
-- deeply below. Hence no `opaque`/`axiom` callee contract is required.

/-- Which spectrum is being produced. Each constructor selects a different
window-correction factor (see `problem_spec_windowCorrectionFactor`). -/
inductive Mode
  | magnitude
  | complex
  | psd
  | angle
  | phase
deriving DecidableEq, Repr
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The window-correction factor as a function of the window samples, the
spectrum kind, and the density flag. Every case is pinned to the inputs:

* `magnitude` / `complex` → the signed total of the window samples;
* `psd` with `scaleByFreq = true` → the total of the squared samples;
* `psd` with `scaleByFreq = false` → the square of the signed total;
* `angle` / `phase` → `1` (no correction).

The signed total `window.sum` is the discriminating quantity: it is the
arithmetic sum (which may be reduced by negative samples), never the sum of
sample magnitudes. -/
def problem_spec_windowCorrectionFactor
    (window : List Rat) (mode : Mode) (scaleByFreq : Bool) (result : Rat) : Prop :=
  result = (match mode with
    | Mode.magnitude => window.sum
    | Mode.complex   => window.sum
    | Mode.psd       =>
        if scaleByFreq then (window.map (fun w => w * w)).sum
        else window.sum * window.sum
    | Mode.angle     => 1
    | Mode.phase     => 1)
-- post-conditions-end

-- impl-start
def implementation_windowCorrectionFactor
    (window : List Rat) (mode : Mode) (scaleByFreq : Bool) : Rat := Id.run do
  match mode with
  | Mode.magnitude | Mode.complex =>
      -- amplitude-style: divide by the signed total of the window samples
      let mut s : Rat := 0
      for w in window do
        s := s + w
      return s
  | Mode.psd =>
      if scaleByFreq then
        -- density per unit frequency: divide by the total of the squared samples
        let mut sq : Rat := 0
        for w in window do
          sq := sq + w * w
        return sq
      else
        -- power preserved per segment: divide by the square of the signed total
        let mut s : Rat := 0
        for w in window do
          s := s + w
        return s * s
  | Mode.angle | Mode.phase =>
      -- phase-style: no window correction
      return 1
-- impl-end

-- proof-start
/-- The signed-sum loop accumulates to `init + window.sum`, generalized over the
accumulator (Route B helper). -/
theorem sum_loop_windowCorrectionFactor (window : List Rat) (init : Rat) :
    (Id.run (forIn window init (fun w r => do
            pure PUnit.unit
            pure (ForInStep.yield (r + w))))) = init + window.sum := by
  induction window generalizing init with
  | nil => simp only [List.forIn_nil, Id.run, List.sum_nil, add_zero]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    rw [ih]; rw [List.sum_cons]; ring

/-- The squared-sum loop accumulates to `init + (window.map (·*·)).sum`. -/
theorem sumsq_loop_windowCorrectionFactor (window : List Rat) (init : Rat) :
    (Id.run (forIn window init (fun w r => do
            pure PUnit.unit
            pure (ForInStep.yield (r + w * w))))) = init + (window.map (fun w => w * w)).sum := by
  induction window generalizing init with
  | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.sum_nil, add_zero]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    rw [ih]; rw [List.map_cons, List.sum_cons]; ring

theorem correct_windowCorrectionFactor :
    ∀ (window : List Rat) (mode : Mode) (scaleByFreq : Bool),
      problem_spec_windowCorrectionFactor window mode scaleByFreq
        (implementation_windowCorrectionFactor window mode scaleByFreq) := by
  intro window mode scaleByFreq
  unfold problem_spec_windowCorrectionFactor implementation_windowCorrectionFactor
  cases mode with
  | magnitude =>
      simp only [Id.run]
      have h := sum_loop_windowCorrectionFactor window 0
      simp only [Id.run] at h
      rw [h]; simp
  | complex =>
      simp only [Id.run]
      have h := sum_loop_windowCorrectionFactor window 0
      simp only [Id.run] at h
      rw [h]; simp
  | psd =>
      by_cases hs : scaleByFreq
      · subst hs
        simp only [Id.run, if_true]
        have h := sumsq_loop_windowCorrectionFactor window 0
        simp only [Id.run] at h
        rw [h]; simp
      · simp only [hs, Bool.false_eq_true, if_false, Id.run]
        have h := sum_loop_windowCorrectionFactor window 0
        simp only [Id.run] at h
        rw [h]; simp only [zero_add]; rfl
  | angle => rfl
  | phase => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: all files built by copying Solution.lean and editing ONLY the impl+proof regions (axioms/pure/pre/post byte-identical). same_spec=True verified for all 7 attacks + pos_control (lean backend). Verifications run concurrently in batches of 4 via scripts/lean_verify.sh.

### RESULTS (path | desc | same_spec | lean_verify exit | axioms | resolve):
- pos_control | gold impl (Id.run signed-sum folds) | True | EXIT 0 | [propext,Classical.choice,Quot.sound] clean, no sorryAx | (is gold)
- atk_1 | PREPATCH BUG: magnitude/complex/psd-false use Sigma|w| (sum of magnitudes) | True | EXIT 1 (goal reduces to Sigma|w|=Sigma w, false on [-1]; ring fails) | n/a | n/a
- atk_2 | boundary: angle returns 0 instead of 1 | True | EXIT 1 | n/a | n/a
- atk_3 | control-flow: psd scaleByFreq true/false branches swapped | True | EXIT 1 | n/a | n/a
- atk_4 | off-by-one: magnitude accumulator initialized at 1 not 0 | True | EXIT 1 | n/a | n/a
- atk_5 | ungrounded-oracle ECHO: direct return of spec value (cases mode <;> rfl) | True | EXIT 0 | [propext,Classical.choice,Quot.sound] clean, no sorryAx | RESOLVED=True COMPLETED=True (official run_resolve, faithful patch = gold divisors)
- atk_6 | boundary: magnitude uses Sigma w^2 (sum of squares) | True | EXIT 1 | n/a | n/a
- atk_7 | control-flow-effect: complex returns 1 (no correction) | True | EXIT 1 | n/a | n/a

Exact commands: bash scripts/lean_verify.sh <f>.lean ; #print axioms appended for pos_control/atk_5 (both clean); resolve via python -c 'from swebench_unified.harness import run_resolve; run_resolve("matplotlib__matplotlib-25122", patch)' -> RESOLVED=True COMPLETED=True NOTE=resolved.

prepatch_reproduced: atk_1 faithfully reintroduces the reported bug (np.abs(window).sum()) and correctly FAILS to verify (spec rejects it) — matching Solution_prepatch.lean which carries the |w| impl with a sorry proof.

Step 2 obligation satisfied: the ONLY wrong-shaped impl whose proof closes with clean axioms is atk_5 (extensionally identical to gold), and its materialized faithful refined patch RESOLVES under the official harness. No closing impl exists whose faithful patch does NOT resolve. verify => correct holds here: the spec is an exact functional equality with no slack.

A-LEG AUDIT (refinement.md): 4 legs, ALL tagged R (type refinement). Zero A-consumed, zero A-reference. No kind-3 leg. Consistent with the model: the window-correction divisor is a pure List.sum / (List.map (.*.)).sum reduction spelled out deeply as for-loop folds; no opaque/axiom callee contract. mapping.md 'Callee provenance' = None: fft/detrend/_stride_windows/np.angle/np.abs(result) are all DOWNSTREAM of the modeled boundary (they act on `result`, not on the window factor), so there is no deep-model correspondence obligation to break. axioms-start block only declares the Mode inductive (data), no axiom/opaque. A-legs are vacuous — nothing to falsify there.

Verdict SOUND: >=5 distinct same-spec wrong impls attacked (prepatch bug + 5 more distinct: boundary angle->0, branch-swap, off-by-one init, magnitude->sum-of-squares, complex->1), none breaks the spec; the sole closing echo resolves.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift) on matplotlib__matplotlib-25122 lean bundle. Modeled boundary = the window-correction DIVISOR computed in _spectral_helper (lib/matplotlib/mlab.py). 

Rigor checks:
- same_spec (LeanBackend.language tables) between Solution.lean and Solution_prepatch.lean = True (spec region byte-identical).
- scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
- #print axioms correct_windowCorrectionFactor -> [propext, Classical.choice, Quot.sound]; no sorryAx. Proof is real.

Real callee comparison (post-patch source at base_commit 5ec2bd27 worktree, and patch.diff):
- magnitude / complex -> real `window.sum()`  == spec `window.sum` (Sigma w_i)
- psd, scale_by_freq=True -> real `(window**2).sum()` == spec `(window.map (fun w=>w*w)).sum` (Sigma w_i^2)
- psd, scale_by_freq=False -> real `window.sum()**2` == spec `window.sum*window.sum` ((Sigma w_i)^2)
- angle / phase -> real applies NO window-correction division == spec factor `1` (dividing by 1 is identity)

Numeric cross-check with a negative-sample window [2,-1,0.5,-3]: numpy window.sum()=-1.5, (window**2).sum()=14.25, window.sum()**2=2.25 all match the spec formulas exactly. The discriminating (negative-sample) case is exercised and agrees.

Drift probes that could have broken faithfulness, all cleared:
1. Orthogonal psd scalings (`result /= Fs`, `result[slc] *= scaling_factor`) act on the spectrum `result`, not on the window factor, and are unchanged by the patch -> correctly outside the modeled boundary; the divisor is exactly what the spec pins.
2. `scale_by_freq` default resolution in real code (None->True for psd, forced False for non-psd) is upstream flag plumbing; the spec parameterizes over the boolean directly, which is a faithful (total) model of both branches.
3. Rat exactly models the real samples because the fix is sign-only (drop np.abs); no float rounding is elided that would matter.
4. Empty window: real sum()=0, (window**2).sum()=0 == spec List.sum on [] = 0. Agrees.

The spec is a total functional equality that agrees with the real post-patch callee on every input. No diverging input exists; the spec is neither too strong nor drifted. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Baseline integrity verified (not rubber-stamped): scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry); recorded #print axioms correct_windowCorrectionFactor = [propext, Classical.choice, Quot.sound] (no sorryAx, real proof); swebench_unified.markers.same_spec(Solution, Solution_prepatch, LeanBackend) = True (spec region byte-identical to prepatch). Spec view (dumped via markers spec_view) = docstring L4-31 + Mode inductive + problem_spec_windowCorrectionFactor; impl & proof are elided.

Baseline for leakage = PUBLIC problem_statement ONLY (hints_text excluded). The public bug report already discloses the gold edit maximally explicitly: (a) 'The np.abs is not needed, and give wrong result for window with negative value, such as flattop'; (b) a reproduction literally writing buggy vs fixed expressions: np.abs(window).sum()**2 - window.sum()**2 with expected outcome 0. Thus the gold fix (drop np.abs -> signed window.sum()) is fully public.

The spec view states the correct divisor abstractly (signed total Sigma w_i for magnitude/complex; Sigma w_i^2 for psd density; (Sigma w_i)^2 for psd non-density; 1 for angle/phase) and stresses the total is 'taken with sign ... NOT the sum of their sizes ... MAY BE NEGATIVE (side lobes dip below zero)'. Every such claim is a strictly-more-abstract paraphrase of what the public statement already says (drop the absolute value => signed sum; negatives such as flattop). The spec view NEVER names _spectral_helper, mlab.py, np.abs, flattop, scale_by_freq, PR/line numbers, or any code structure, so it reveals nothing beyond the public problem_statement. The 'PRE-PATCH BUG' / |w| content lives only in the impl region of Solution_prepatch.lean, which is OUTSIDE the spec view and not shown to a solver. No spec-view line reconstructs the gold edit beyond the public problem_statement. Concur with recorded G-PANEL-3 verdict.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
