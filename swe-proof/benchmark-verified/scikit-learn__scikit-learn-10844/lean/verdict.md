# P2 adversarial audit — scikit-learn__scikit-learn-10844

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_8.lean`, `atk_9.lean` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 4 | `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_10.lean` |
| does not verify against this specification, so the specification excludes it | 1 | `atk_1.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec implementation with a closing clean-axiom correct_fmIndex had a faithful refined patch that failed to resolve. All 5 closing attacks (atk_2/3/4/8/9) were materialized as unified diffs, checked with `git apply --check` at base_commit 97523985b3, and RUN through run_resolve: all 5 returned resolved=true, completed=true, with FAIL_TO_PASS test_int_overflow_mutual_info_fowlkes_mallows_score passing and all 16 PASS_TO_PASS passing. verify => correct held on every admissible attack.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -103,24 +103,14 @@
 -- post-conditions-end
 
 -- impl-start
--- Compute the index from the co-occurrence matrix. The agreement count and the
--- two marginal counts are read out of their machine words; when the agreement
--- count is zero the index is the real number 0, otherwise it is obtained as the
--- product of two square roots, sqrt(T / P) times sqrt(T / Q), each ratio taken
--- before any multiplication of the marginal counts. Every division and every
--- root goes through the library's partial arithmetic, so the outcome names a
--- real number only if each step of the assembly did.
+-- PREPATCH BUG: tk / sqrt(pk*qk) with the marginal product formed in ONE signed machine word.
 noncomputable def implementation_fmIndex (M : List (List ℕ)) : Option ℝ :=
   let tk := (cmTkW M).toInt
-  let pk := (cmPkW M).toInt
-  let qk := (cmQkW M).toInt
+  let pq := (cmPkW M * cmQkW M).toInt
   if tk = 0 then some 0
   else do
-    let a ← fdiv (tk : ℝ) (pk : ℝ)
-    let b ← fdiv (tk : ℝ) (qk : ℝ)
-    let ra ← fsqrt a
-    let rb ← fsqrt b
-    pure (ra * rb)
+    let r ← fsqrt (pq : ℝ)
+    fdiv (tk : ℝ) r
 -- impl-end
 
 
@@ -151,21 +141,6 @@
 theorem fsqrt_of_nonneg (x : ℝ) (h : 0 ≤ x) : fsqrt x = some (Real.sqrt x) := by
   unfold fsqrt; rw [if_neg (not_lt.mpr h)]
 
-theorem impl_value (M : List (List ℕ)) :
-    implementation_fmIndex M
-      = if (cmTkW M).toInt = 0 then some (0 : ℝ)
-        else (do
-          let a ← fdiv ((cmTkW M).toInt : ℝ) ((cmPkW M).toInt : ℝ)
-          let b ← fdiv ((cmTkW M).toInt : ℝ) ((cmQkW M).toInt : ℝ)
-          let ra ← fsqrt a
-          let rb ← fsqrt b
-          pure (ra * rb)) := by
-  unfold implementation_fmIndex
-  rfl
-
-theorem zero_branch (M : List (List ℕ)) (h : (cmTkW M).toInt = 0) :
-    implementation_fmIndex M = some 0 := by
-  rw [impl_value, if_pos h]
 -- Module Positivity: integer inequalities T ≥ 0, P > 0, Q > 0.
 
 theorem sumSq_ge_total_of_partition (xs : List ℕ) :
@@ -438,45 +413,38 @@
       = (cmTk M : ℝ) / Real.sqrt ((cmPk M : ℝ) * (cmQk M : ℝ)) := by
   rw [Real.sqrt_div (sq_nonneg _), Real.sqrt_sq hT]
 
-theorem nonzero_branch (M : List (List ℕ)) (w : ℕ)
-    (hrect : ∀ r ∈ M, r.length = w)
-    (hwT : inWord (cmTk M)) (hwP : inWord (cmPk M)) (hwQ : inWord (cmQk M))
-    (hT : (cmTkW M).toInt ≠ 0) :
+theorem impl_value (M : List (List ℕ)) :
     implementation_fmIndex M
-      = some (((cmTkW M).toInt : ℝ)
-          / Real.sqrt (((cmPkW M).toInt : ℝ) * ((cmQkW M).toInt : ℝ))) := by
-  have hTne : cmTk M ≠ 0 := by rw [tkW_val M hwT] at hT; exact hT
-  rw [impl_value M, if_neg hT, tkW_val M hwT, pkW_val M hwP, qkW_val M hwQ]
-  have hP_int : 0 < cmPk M := P_pos M w hrect hTne
-  have hQ_int : 0 < cmQk M := Q_pos M hTne
-  have hT_int : 0 ≤ cmTk M := T_nonneg M
-  have hP : (0 : ℝ) < (cmPk M : ℝ) := by exact_mod_cast hP_int
-  have hQ : (0 : ℝ) < (cmQk M : ℝ) := by exact_mod_cast hQ_int
-  have hTr : (0 : ℝ) ≤ (cmTk M : ℝ) := by exact_mod_cast hT_int
-  have hdiv : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmPk M : ℝ) := div_nonneg hTr hP.le
-  have hdiv2 : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmQk M : ℝ) := div_nonneg hTr hQ.le
-  have hPQ : (0 : ℝ) < (cmPk M : ℝ) * (cmQk M : ℝ) := mul_pos hP hQ
-  rw [fdiv_of_ne _ _ (ne_of_gt hP), fdiv_of_ne _ _ (ne_of_gt hQ)]
-  show (fsqrt ((cmTk M : ℝ) / (cmPk M : ℝ)) >>= fun ra =>
-      fsqrt ((cmTk M : ℝ) / (cmQk M : ℝ)) >>= fun rb => pure (ra * rb)) = _
-  rw [fsqrt_of_nonneg _ hdiv, fsqrt_of_nonneg _ hdiv2]
-  show some (Real.sqrt ((cmTk M : ℝ) / (cmPk M : ℝ))
-      * Real.sqrt ((cmTk M : ℝ) / (cmQk M : ℝ))) = _
-  rw [sqrt_combine M hdiv, radicand_simp M hP hQ, sqrt_quotient M hTr hPQ]
-
--- The matrix is rectangular (every row has the common width `w`) — the shape of
--- every genuine co-occurrence matrix — and each of the three counts is small
--- enough to sit in one machine word. Under those the result is total: when the
--- agreement count is `0` the index is `0`, and otherwise both marginal counts
--- are strictly positive (each dominates the agreement count), so the quotient is
--- well-defined. Nothing is assumed about the size of the PRODUCT of the two
--- marginal counts.
+      = if (cmTkW M).toInt = 0 then some (0 : ℝ)
+        else (do
+          let r ← fsqrt (((cmPkW M * cmQkW M).toInt : ℝ))
+          fdiv ((cmTkW M).toInt : ℝ) r) := by
+  unfold implementation_fmIndex; rfl
+
 theorem correct_fmIndex :
     ∀ (M : List (List ℕ)) (w : ℕ), (∀ r ∈ M, r.length = w) →
       inWord (cmTk M) → inWord (cmPk M) → inWord (cmQk M) →
       problem_spec_fmIndex M (implementation_fmIndex M) := by
   intro M w hrect hwT hwP hwQ
-  refine ⟨fun h => zero_branch M h, fun hT => ?_⟩
-  exact nonzero_branch M w hrect hwT hwP hwQ hT
+  refine ⟨fun h => by rw [impl_value, if_pos h], fun hT => ?_⟩
+  have hTne : cmTk M ≠ 0 := by rw [tkW_val M hwT] at hT; exact hT
+  have hP_int : 0 < cmPk M := P_pos M w hrect hTne
+  have hQ_int : 0 < cmQk M := Q_pos M hTne
+  have hTr : (0:ℝ) ≤ ((cmTkW M).toInt : ℝ) := by
+    rw [tkW_val M hwT]; exact_mod_cast T_nonneg M
+  rw [impl_value, if_neg hT]
+  -- OBSTRUCTION: the marginal product is formed in ONE machine word, so
+  -- `(cmPkW M * cmQkW M).toInt` is the WRAPPED value, which is NOT
+  -- `cmPk M * cmQk M` and is negative on admissible matrices such as
+  -- [[54000, 54000]]. `fsqrt` of it is `none` and no `some _` is reachable.
+  have hnn : (0:ℝ) ≤ (((cmPkW M * cmQkW M).toInt : ℝ)) := by
+    exact_mod_cast (by positivity : (0:ℤ) ≤ (cmPkW M * cmQkW M).toInt)
+  rw [fsqrt_of_nonneg _ hnn]
+  show fdiv _ (Real.sqrt _) = _
+  rw [fdiv_of_ne _ _ (ne_of_gt (Real.sqrt_pos.mpr (by positivity)))]
+  congr 2
+  rw [pkW_val M hwP, qkW_val M hwQ]
+  push_cast
+  ring
 
 -- proof-end
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -103,24 +103,10 @@
 -- post-conditions-end
 
 -- impl-start
--- Compute the index from the co-occurrence matrix. The agreement count and the
--- two marginal counts are read out of their machine words; when the agreement
--- count is zero the index is the real number 0, otherwise it is obtained as the
--- product of two square roots, sqrt(T / P) times sqrt(T / Q), each ratio taken
--- before any multiplication of the marginal counts. Every division and every
--- root goes through the library's partial arithmetic, so the outcome names a
--- real number only if each step of the assembly did.
+-- GUARD ERASED, total Mathlib / and Real.sqrt (no fdiv/fsqrt anywhere).
 noncomputable def implementation_fmIndex (M : List (List ℕ)) : Option ℝ :=
-  let tk := (cmTkW M).toInt
-  let pk := (cmPkW M).toInt
-  let qk := (cmQkW M).toInt
-  if tk = 0 then some 0
-  else do
-    let a ← fdiv (tk : ℝ) (pk : ℝ)
-    let b ← fdiv (tk : ℝ) (qk : ℝ)
-    let ra ← fsqrt a
-    let rb ← fsqrt b
-    pure (ra * rb)
+  some (((cmTkW M).toInt : ℝ)
+    / Real.sqrt (((cmPkW M).toInt : ℝ) * ((cmQkW M).toInt : ℝ)))
 -- impl-end
 
 
@@ -151,21 +137,6 @@
 theorem fsqrt_of_nonneg (x : ℝ) (h : 0 ≤ x) : fsqrt x = some (Real.sqrt x) := by
   unfold fsqrt; rw [if_neg (not_lt.mpr h)]
 
-theorem impl_value (M : List (List ℕ)) :
-    implementation_fmIndex M
-      = if (cmTkW M).toInt = 0 then some (0 : ℝ)
-        else (do
-          let a ← fdiv ((cmTkW M).toInt : ℝ) ((cmPkW M).toInt : ℝ)
-          let b ← fdiv ((cmTkW M).toInt : ℝ) ((cmQkW M).toInt : ℝ)
-          let ra ← fsqrt a
-          let rb ← fsqrt b
-          pure (ra * rb)) := by
-  unfold implementation_fmIndex
-  rfl
-
-theorem zero_branch (M : List (List ℕ)) (h : (cmTkW M).toInt = 0) :
-    implementation_fmIndex M = some 0 := by
-  rw [impl_value, if_pos h]
 -- Module Positivity: integer inequalities T ≥ 0, P > 0, Q > 0.
 
 theorem sumSq_ge_total_of_partition (xs : List ℕ) :
@@ -438,45 +409,14 @@
       = (cmTk M : ℝ) / Real.sqrt ((cmPk M : ℝ) * (cmQk M : ℝ)) := by
   rw [Real.sqrt_div (sq_nonneg _), Real.sqrt_sq hT]
 
-theorem nonzero_branch (M : List (List ℕ)) (w : ℕ)
-    (hrect : ∀ r ∈ M, r.length = w)
-    (hwT : inWord (cmTk M)) (hwP : inWord (cmPk M)) (hwQ : inWord (cmQk M))
-    (hT : (cmTkW M).toInt ≠ 0) :
-    implementation_fmIndex M
-      = some (((cmTkW M).toInt : ℝ)
-          / Real.sqrt (((cmPkW M).toInt : ℝ) * ((cmQkW M).toInt : ℝ))) := by
-  have hTne : cmTk M ≠ 0 := by rw [tkW_val M hwT] at hT; exact hT
-  rw [impl_value M, if_neg hT, tkW_val M hwT, pkW_val M hwP, qkW_val M hwQ]
-  have hP_int : 0 < cmPk M := P_pos M w hrect hTne
-  have hQ_int : 0 < cmQk M := Q_pos M hTne
-  have hT_int : 0 ≤ cmTk M := T_nonneg M
-  have hP : (0 : ℝ) < (cmPk M : ℝ) := by exact_mod_cast hP_int
-  have hQ : (0 : ℝ) < (cmQk M : ℝ) := by exact_mod_cast hQ_int
-  have hTr : (0 : ℝ) ≤ (cmTk M : ℝ) := by exact_mod_cast hT_int
-  have hdiv : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmPk M : ℝ) := div_nonneg hTr hP.le
-  have hdiv2 : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmQk M : ℝ) := div_nonneg hTr hQ.le
-  have hPQ : (0 : ℝ) < (cmPk M : ℝ) * (cmQk M : ℝ) := mul_pos hP hQ
-  rw [fdiv_of_ne _ _ (ne_of_gt hP), fdiv_of_ne _ _ (ne_of_gt hQ)]
-  show (fsqrt ((cmTk M : ℝ) / (cmPk M : ℝ)) >>= fun ra =>
-      fsqrt ((cmTk M : ℝ) / (cmQk M : ℝ)) >>= fun rb => pure (ra * rb)) = _
-  rw [fsqrt_of_nonneg _ hdiv, fsqrt_of_nonneg _ hdiv2]
-  show some (Real.sqrt ((cmTk M : ℝ) / (cmPk M : ℝ))
-      * Real.sqrt ((cmTk M : ℝ) / (cmQk M : ℝ))) = _
-  rw [sqrt_combine M hdiv, radicand_simp M hP hQ, sqrt_quotient M hTr hPQ]
-
--- The matrix is rectangular (every row has the common width `w`) — the shape of
--- every genuine co-occurrence matrix — and each of the three counts is small
--- enough to sit in one machine word. Under those the result is total: when the
--- agreement count is `0` the index is `0`, and otherwise both marginal counts
--- are strictly positive (each dominates the agreement count), so the quotient is
--- well-defined. Nothing is assumed about the size of the PRODUCT of the two
--- marginal counts.
 theorem correct_fmIndex :
     ∀ (M : List (List ℕ)) (w : ℕ), (∀ r ∈ M, r.length = w) →
       inWord (cmTk M) → inWord (cmPk M) → inWord (cmQk M) →
       problem_spec_fmIndex M (implementation_fmIndex M) := by
   intro M w hrect hwT hwP hwQ
-  refine ⟨fun h => zero_branch M h, fun hT => ?_⟩
-  exact nonzero_branch M w hrect hwT hwP hwQ hT
+  unfold implementation_fmIndex
+  refine ⟨fun h => ?_, fun hT => rfl⟩
+  rw [h]
+  norm_num
 
 -- proof-end
```

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -103,24 +103,15 @@
 -- post-conditions-end
 
 -- impl-start
--- Compute the index from the co-occurrence matrix. The agreement count and the
--- two marginal counts are read out of their machine words; when the agreement
--- count is zero the index is the real number 0, otherwise it is obtained as the
--- product of two square roots, sqrt(T / P) times sqrt(T / Q), each ratio taken
--- before any multiplication of the marginal counts. Every division and every
--- root goes through the library's partial arithmetic, so the outcome names a
--- real number only if each step of the assembly did.
+-- SPECFORM ECHO: one root over the EXACT (unbounded) product of the two marginal counts.
 noncomputable def implementation_fmIndex (M : List (List ℕ)) : Option ℝ :=
   let tk := (cmTkW M).toInt
   let pk := (cmPkW M).toInt
   let qk := (cmQkW M).toInt
   if tk = 0 then some 0
   else do
-    let a ← fdiv (tk : ℝ) (pk : ℝ)
-    let b ← fdiv (tk : ℝ) (qk : ℝ)
-    let ra ← fsqrt a
-    let rb ← fsqrt b
-    pure (ra * rb)
+    let r ← fsqrt ((pk : ℝ) * (qk : ℝ))
+    fdiv (tk : ℝ) r
 -- impl-end
 
 
@@ -151,21 +142,6 @@
 theorem fsqrt_of_nonneg (x : ℝ) (h : 0 ≤ x) : fsqrt x = some (Real.sqrt x) := by
   unfold fsqrt; rw [if_neg (not_lt.mpr h)]
 
-theorem impl_value (M : List (List ℕ)) :
-    implementation_fmIndex M
-      = if (cmTkW M).toInt = 0 then some (0 : ℝ)
-        else (do
-          let a ← fdiv ((cmTkW M).toInt : ℝ) ((cmPkW M).toInt : ℝ)
-          let b ← fdiv ((cmTkW M).toInt : ℝ) ((cmQkW M).toInt : ℝ)
-          let ra ← fsqrt a
-          let rb ← fsqrt b
-          pure (ra * rb)) := by
-  unfold implementation_fmIndex
-  rfl
-
-theorem zero_branch (M : List (List ℕ)) (h : (cmTkW M).toInt = 0) :
-    implementation_fmIndex M = some 0 := by
-  rw [impl_value, if_pos h]
 -- Module Positivity: integer inequalities T ≥ 0, P > 0, Q > 0.
 
 theorem sumSq_ge_total_of_partition (xs : List ℕ) :
@@ -438,45 +414,28 @@
       = (cmTk M : ℝ) / Real.sqrt ((cmPk M : ℝ) * (cmQk M : ℝ)) := by
   rw [Real.sqrt_div (sq_nonneg _), Real.sqrt_sq hT]
 
-theorem nonzero_branch (M : List (List ℕ)) (w : ℕ)
-    (hrect : ∀ r ∈ M, r.length = w)
-    (hwT : inWord (cmTk M)) (hwP : inWord (cmPk M)) (hwQ : inWord (cmQk M))
-    (hT : (cmTkW M).toInt ≠ 0) :
-    implementation_fmIndex M
-      = some (((cmTkW M).toInt : ℝ)
-          / Real.sqrt (((cmPkW M).toInt : ℝ) * ((cmQkW M).toInt : ℝ))) := by
-  have hTne : cmTk M ≠ 0 := by rw [tkW_val M hwT] at hT; exact hT
-  rw [impl_value M, if_neg hT, tkW_val M hwT, pkW_val M hwP, qkW_val M hwQ]
-  have hP_int : 0 < cmPk M := P_pos M w hrect hTne
-  have hQ_int : 0 < cmQk M := Q_pos M hTne
-  have hT_int : 0 ≤ cmTk M := T_nonneg M
-  have hP : (0 : ℝ) < (cmPk M : ℝ) := by exact_mod_cast hP_int
-  have hQ : (0 : ℝ) < (cmQk M : ℝ) := by exact_mod_cast hQ_int
-  have hTr : (0 : ℝ) ≤ (cmTk M : ℝ) := by exact_mod_cast hT_int
-  have hdiv : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmPk M : ℝ) := div_nonneg hTr hP.le
-  have hdiv2 : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmQk M : ℝ) := div_nonneg hTr hQ.le
-  have hPQ : (0 : ℝ) < (cmPk M : ℝ) * (cmQk M : ℝ) := mul_pos hP hQ
-  rw [fdiv_of_ne _ _ (ne_of_gt hP), fdiv_of_ne _ _ (ne_of_gt hQ)]
-  show (fsqrt ((cmTk M : ℝ) / (cmPk M : ℝ)) >>= fun ra =>
-      fsqrt ((cmTk M : ℝ) / (cmQk M : ℝ)) >>= fun rb => pure (ra * rb)) = _
-  rw [fsqrt_of_nonneg _ hdiv, fsqrt_of_nonneg _ hdiv2]
-  show some (Real.sqrt ((cmTk M : ℝ) / (cmPk M : ℝ))
-      * Real.sqrt ((cmTk M : ℝ) / (cmQk M : ℝ))) = _
-  rw [sqrt_combine M hdiv, radicand_simp M hP hQ, sqrt_quotient M hTr hPQ]
-
--- The matrix is rectangular (every row has the common width `w`) — the shape of
--- every genuine co-occurrence matrix — and each of the three counts is small
--- enough to sit in one machine word. Under those the result is total: when the
--- agreement count is `0` the index is `0`, and otherwise both marginal counts
--- are strictly positive (each dominates the agreement count), so the quotient is
--- well-defined. Nothing is assumed about the size of the PRODUCT of the two
--- marginal counts.
 theorem correct_fmIndex :
     ∀ (M : List (List ℕ)) (w : ℕ), (∀ r ∈ M, r.length = w) →
       inWord (cmTk M) → inWord (cmPk M) → inWord (cmQk M) →
       problem_spec_fmIndex M (implementation_fmIndex M) := by
   intro M w hrect hwT hwP hwQ
-  refine ⟨fun h => zero_branch M h, fun hT => ?_⟩
-  exact nonzero_branch M w hrect hwT hwP hwQ hT
+  constructor
+  · intro h; unfold implementation_fmIndex; simp only []; rw [if_pos h]
+  · intro hT
+    have hTne : cmTk M ≠ 0 := by rw [tkW_val M hwT] at hT; exact hT
+    have hP_int : 0 < cmPk M := P_pos M w hrect hTne
+    have hQ_int : 0 < cmQk M := Q_pos M hTne
+    have hTr : (0:ℝ) ≤ ((cmTkW M).toInt : ℝ) := by
+      rw [tkW_val M hwT]; exact_mod_cast T_nonneg M
+    have hP : (0:ℝ) < ((cmPkW M).toInt : ℝ) := by
+      rw [pkW_val M hwP]; exact_mod_cast hP_int
+    have hQ : (0:ℝ) < ((cmQkW M).toInt : ℝ) := by
+      rw [qkW_val M hwQ]; exact_mod_cast hQ_int
+    have hPQ : (0:ℝ) < ((cmPkW M).toInt : ℝ) * ((cmQkW M).toInt : ℝ) := mul_pos hP hQ
+    unfold implementation_fmIndex
+    simp only []
+    rw [if_neg hT, fsqrt_of_nonneg _ hPQ.le]
+    show fdiv _ (Real.sqrt _) = _
+    rw [fdiv_of_ne _ _ (ne_of_gt (Real.sqrt_pos.mpr hPQ))]
 
 -- proof-end
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -103,24 +103,16 @@
 -- post-conditions-end
 
 -- impl-start
--- Compute the index from the co-occurrence matrix. The agreement count and the
--- two marginal counts are read out of their machine words; when the agreement
--- count is zero the index is the real number 0, otherwise it is obtained as the
--- product of two square roots, sqrt(T / P) times sqrt(T / Q), each ratio taken
--- before any multiplication of the marginal counts. Every division and every
--- root goes through the library's partial arithmetic, so the outcome names a
--- real number only if each step of the assembly did.
+-- SPLIT ROOTS: tk / (sqrt(pk) * sqrt(qk)) -- never forms a product of counts.
 noncomputable def implementation_fmIndex (M : List (List ℕ)) : Option ℝ :=
   let tk := (cmTkW M).toInt
   let pk := (cmPkW M).toInt
   let qk := (cmQkW M).toInt
   if tk = 0 then some 0
   else do
-    let a ← fdiv (tk : ℝ) (pk : ℝ)
-    let b ← fdiv (tk : ℝ) (qk : ℝ)
-    let ra ← fsqrt a
-    let rb ← fsqrt b
-    pure (ra * rb)
+    let rp ← fsqrt (pk : ℝ)
+    let rq ← fsqrt (qk : ℝ)
+    fdiv (tk : ℝ) (rp * rq)
 -- impl-end
 
 
@@ -151,21 +143,6 @@
 theorem fsqrt_of_nonneg (x : ℝ) (h : 0 ≤ x) : fsqrt x = some (Real.sqrt x) := by
   unfold fsqrt; rw [if_neg (not_lt.mpr h)]
 
-theorem impl_value (M : List (List ℕ)) :
-    implementation_fmIndex M
-      = if (cmTkW M).toInt = 0 then some (0 : ℝ)
-        else (do
-          let a ← fdiv ((cmTkW M).toInt : ℝ) ((cmPkW M).toInt : ℝ)
-          let b ← fdiv ((cmTkW M).toInt : ℝ) ((cmQkW M).toInt : ℝ)
-          let ra ← fsqrt a
-          let rb ← fsqrt b
-          pure (ra * rb)) := by
-  unfold implementation_fmIndex
-  rfl
-
-theorem zero_branch (M : List (List ℕ)) (h : (cmTkW M).toInt = 0) :
-    implementation_fmIndex M = some 0 := by
-  rw [impl_value, if_pos h]
 -- Module Positivity: integer inequalities T ≥ 0, P > 0, Q > 0.
 
 theorem sumSq_ge_total_of_partition (xs : List ℕ) :
@@ -438,45 +415,28 @@
       = (cmTk M : ℝ) / Real.sqrt ((cmPk M : ℝ) * (cmQk M : ℝ)) := by
   rw [Real.sqrt_div (sq_nonneg _), Real.sqrt_sq hT]
 
-theorem nonzero_branch (M : List (List ℕ)) (w : ℕ)
-    (hrect : ∀ r ∈ M, r.length = w)
-    (hwT : inWord (cmTk M)) (hwP : inWord (cmPk M)) (hwQ : inWord (cmQk M))
-    (hT : (cmTkW M).toInt ≠ 0) :
-    implementation_fmIndex M
-      = some (((cmTkW M).toInt : ℝ)
-          / Real.sqrt (((cmPkW M).toInt : ℝ) * ((cmQkW M).toInt : ℝ))) := by
-  have hTne : cmTk M ≠ 0 := by rw [tkW_val M hwT] at hT; exact hT
-  rw [impl_value M, if_neg hT, tkW_val M hwT, pkW_val M hwP, qkW_val M hwQ]
-  have hP_int : 0 < cmPk M := P_pos M w hrect hTne
-  have hQ_int : 0 < cmQk M := Q_pos M hTne
-  have hT_int : 0 ≤ cmTk M := T_nonneg M
-  have hP : (0 : ℝ) < (cmPk M : ℝ) := by exact_mod_cast hP_int
-  have hQ : (0 : ℝ) < (cmQk M : ℝ) := by exact_mod_cast hQ_int
-  have hTr : (0 : ℝ) ≤ (cmTk M : ℝ) := by exact_mod_cast hT_int
-  have hdiv : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmPk M : ℝ) := div_nonneg hTr hP.le
-  have hdiv2 : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmQk M : ℝ) := div_nonneg hTr hQ.le
-  have hPQ : (0 : ℝ) < (cmPk M : ℝ) * (cmQk M : ℝ) := mul_pos hP hQ
-  rw [fdiv_of_ne _ _ (ne_of_gt hP), fdiv_of_ne _ _ (ne_of_gt hQ)]
-  show (fsqrt ((cmTk M : ℝ) / (cmPk M : ℝ)) >>= fun ra =>
-      fsqrt ((cmTk M : ℝ) / (cmQk M : ℝ)) >>= fun rb => pure (ra * rb)) = _
-  rw [fsqrt_of_nonneg _ hdiv, fsqrt_of_nonneg _ hdiv2]
-  show some (Real.sqrt ((cmTk M : ℝ) / (cmPk M : ℝ))
-      * Real.sqrt ((cmTk M : ℝ) / (cmQk M : ℝ))) = _
-  rw [sqrt_combine M hdiv, radicand_simp M hP hQ, sqrt_quotient M hTr hPQ]
-
--- The matrix is rectangular (every row has the common width `w`) — the shape of
--- every genuine co-occurrence matrix — and each of the three counts is small
--- enough to sit in one machine word. Under those the result is total: when the
--- agreement count is `0` the index is `0`, and otherwise both marginal counts
--- are strictly positive (each dominates the agreement count), so the quotient is
--- well-defined. Nothing is assumed about the size of the PRODUCT of the two
--- marginal counts.
 theorem correct_fmIndex :
     ∀ (M : List (List ℕ)) (w : ℕ), (∀ r ∈ M, r.length = w) →
       inWord (cmTk M) → inWord (cmPk M) → inWord (cmQk M) →
       problem_spec_fmIndex M (implementation_fmIndex M) := by
   intro M w hrect hwT hwP hwQ
-  refine ⟨fun h => zero_branch M h, fun hT => ?_⟩
-  exact nonzero_branch M w hrect hwT hwP hwQ hT
+  constructor
+  · intro h; unfold implementation_fmIndex; simp only []; rw [if_pos h]
+  · intro hT
+    have hTne : cmTk M ≠ 0 := by rw [tkW_val M hwT] at hT; exact hT
+    have hP_int : 0 < cmPk M := P_pos M w hrect hTne
+    have hQ_int : 0 < cmQk M := Q_pos M hTne
+    have hP : (0:ℝ) < ((cmPkW M).toInt : ℝ) := by
+      rw [pkW_val M hwP]; exact_mod_cast hP_int
+    have hQ : (0:ℝ) < ((cmQkW M).toInt : ℝ) := by
+      rw [qkW_val M hwQ]; exact_mod_cast hQ_int
+    unfold implementation_fmIndex
+    simp only []
+    rw [if_neg hT, fsqrt_of_nonneg _ hP.le]
+    show (fsqrt ((cmQkW M).toInt : ℝ) >>= fun rq => fdiv _ (Real.sqrt _ * rq)) = _
+    rw [fsqrt_of_nonneg _ hQ.le]
+    show fdiv _ (Real.sqrt ((cmPkW M).toInt : ℝ) * Real.sqrt ((cmQkW M).toInt : ℝ)) = _
+    rw [← Real.sqrt_mul hP.le]
+    rw [fdiv_of_ne _ _ (ne_of_gt (Real.sqrt_pos.mpr (mul_pos hP hQ)))]
 
 -- proof-end
```

Attack 5 — `atk_5.lean` → not a counterexample (attack assumes rather than establishes: introduces assumption token 'sorry' (0 -> 1) (not a valid counterexample)) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -103,20 +103,13 @@
 -- post-conditions-end
 
 -- impl-start
--- Compute the index from the co-occurrence matrix. The agreement count and the
--- two marginal counts are read out of their machine words; when the agreement
--- count is zero the index is the real number 0, otherwise it is obtained as the
--- product of two square roots, sqrt(T / P) times sqrt(T / Q), each ratio taken
--- before any multiplication of the marginal counts. Every division and every
--- root goes through the library's partial arithmetic, so the outcome names a
--- real number only if each step of the assembly did.
+-- WRONG VALUE: the ROW marginal count is used for BOTH ratios, so the index is tk/qk.
 noncomputable def implementation_fmIndex (M : List (List ℕ)) : Option ℝ :=
   let tk := (cmTkW M).toInt
-  let pk := (cmPkW M).toInt
   let qk := (cmQkW M).toInt
   if tk = 0 then some 0
   else do
-    let a ← fdiv (tk : ℝ) (pk : ℝ)
+    let a ← fdiv (tk : ℝ) (qk : ℝ)
     let b ← fdiv (tk : ℝ) (qk : ℝ)
     let ra ← fsqrt a
     let rb ← fsqrt b
@@ -151,21 +144,6 @@
 theorem fsqrt_of_nonneg (x : ℝ) (h : 0 ≤ x) : fsqrt x = some (Real.sqrt x) := by
   unfold fsqrt; rw [if_neg (not_lt.mpr h)]
 
-theorem impl_value (M : List (List ℕ)) :
-    implementation_fmIndex M
-      = if (cmTkW M).toInt = 0 then some (0 : ℝ)
-        else (do
-          let a ← fdiv ((cmTkW M).toInt : ℝ) ((cmPkW M).toInt : ℝ)
-          let b ← fdiv ((cmTkW M).toInt : ℝ) ((cmQkW M).toInt : ℝ)
-          let ra ← fsqrt a
-          let rb ← fsqrt b
-          pure (ra * rb)) := by
-  unfold implementation_fmIndex
-  rfl
-
-theorem zero_branch (M : List (List ℕ)) (h : (cmTkW M).toInt = 0) :
-    implementation_fmIndex M = some 0 := by
-  rw [impl_value, if_pos h]
 -- Module Positivity: integer inequalities T ≥ 0, P > 0, Q > 0.
 
 theorem sumSq_ge_total_of_partition (xs : List ℕ) :
@@ -438,45 +416,43 @@
       = (cmTk M : ℝ) / Real.sqrt ((cmPk M : ℝ) * (cmQk M : ℝ)) := by
   rw [Real.sqrt_div (sq_nonneg _), Real.sqrt_sq hT]
 
-theorem nonzero_branch (M : List (List ℕ)) (w : ℕ)
-    (hrect : ∀ r ∈ M, r.length = w)
-    (hwT : inWord (cmTk M)) (hwP : inWord (cmPk M)) (hwQ : inWord (cmQk M))
-    (hT : (cmTkW M).toInt ≠ 0) :
+-- Best effort: reduce, peel the zero branch, then discharge the nonzero branch
+-- exactly as the gold proof does (sqrt_combine / radicand_simp / sqrt_quotient).
+theorem impl_value (M : List (List ℕ)) :
     implementation_fmIndex M
-      = some (((cmTkW M).toInt : ℝ)
-          / Real.sqrt (((cmPkW M).toInt : ℝ) * ((cmQkW M).toInt : ℝ))) := by
-  have hTne : cmTk M ≠ 0 := by rw [tkW_val M hwT] at hT; exact hT
-  rw [impl_value M, if_neg hT, tkW_val M hwT, pkW_val M hwP, qkW_val M hwQ]
-  have hP_int : 0 < cmPk M := P_pos M w hrect hTne
-  have hQ_int : 0 < cmQk M := Q_pos M hTne
-  have hT_int : 0 ≤ cmTk M := T_nonneg M
-  have hP : (0 : ℝ) < (cmPk M : ℝ) := by exact_mod_cast hP_int
-  have hQ : (0 : ℝ) < (cmQk M : ℝ) := by exact_mod_cast hQ_int
-  have hTr : (0 : ℝ) ≤ (cmTk M : ℝ) := by exact_mod_cast hT_int
-  have hdiv : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmPk M : ℝ) := div_nonneg hTr hP.le
-  have hdiv2 : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmQk M : ℝ) := div_nonneg hTr hQ.le
-  have hPQ : (0 : ℝ) < (cmPk M : ℝ) * (cmQk M : ℝ) := mul_pos hP hQ
-  rw [fdiv_of_ne _ _ (ne_of_gt hP), fdiv_of_ne _ _ (ne_of_gt hQ)]
-  show (fsqrt ((cmTk M : ℝ) / (cmPk M : ℝ)) >>= fun ra =>
-      fsqrt ((cmTk M : ℝ) / (cmQk M : ℝ)) >>= fun rb => pure (ra * rb)) = _
-  rw [fsqrt_of_nonneg _ hdiv, fsqrt_of_nonneg _ hdiv2]
-  show some (Real.sqrt ((cmTk M : ℝ) / (cmPk M : ℝ))
-      * Real.sqrt ((cmTk M : ℝ) / (cmQk M : ℝ))) = _
-  rw [sqrt_combine M hdiv, radicand_simp M hP hQ, sqrt_quotient M hTr hPQ]
-
--- The matrix is rectangular (every row has the common width `w`) — the shape of
--- every genuine co-occurrence matrix — and each of the three counts is small
--- enough to sit in one machine word. Under those the result is total: when the
--- agreement count is `0` the index is `0`, and otherwise both marginal counts
--- are strictly positive (each dominates the agreement count), so the quotient is
--- well-defined. Nothing is assumed about the size of the PRODUCT of the two
--- marginal counts.
+      = if (cmTkW M).toInt = 0 then some (0 : ℝ)
+        else (do
+          let a ← fdiv ((cmTkW M).toInt : ℝ) ((cmQkW M).toInt : ℝ)
+          let b ← fdiv ((cmTkW M).toInt : ℝ) ((cmQkW M).toInt : ℝ)
+          let ra ← fsqrt a
+          let rb ← fsqrt b
+          pure (ra * rb)) := by
+  unfold implementation_fmIndex; rfl
+
 theorem correct_fmIndex :
     ∀ (M : List (List ℕ)) (w : ℕ), (∀ r ∈ M, r.length = w) →
       inWord (cmTk M) → inWord (cmPk M) → inWord (cmQk M) →
       problem_spec_fmIndex M (implementation_fmIndex M) := by
   intro M w hrect hwT hwP hwQ
-  refine ⟨fun h => zero_branch M h, fun hT => ?_⟩
-  exact nonzero_branch M w hrect hwT hwP hwQ hT
+  refine ⟨fun h => by rw [impl_value, if_pos h], fun hT => ?_⟩
+  have hTne : cmTk M ≠ 0 := by rw [tkW_val M hwT] at hT; exact hT
+  have hP_int : 0 < cmPk M := P_pos M w hrect hTne
+  have hQ_int : 0 < cmQk M := Q_pos M hTne
+  have hTr : (0:ℝ) ≤ ((cmTkW M).toInt : ℝ) := by
+    rw [tkW_val M hwT]; exact_mod_cast T_nonneg M
+  have hP : (0:ℝ) < ((cmPkW M).toInt : ℝ) := by
+    rw [pkW_val M hwP]; exact_mod_cast hP_int
+  have hQ : (0:ℝ) < ((cmQkW M).toInt : ℝ) := by
+    rw [qkW_val M hwQ]; exact_mod_cast hQ_int
+  have hdq : (0:ℝ) ≤ ((cmTkW M).toInt : ℝ) / ((cmQkW M).toInt : ℝ) := div_nonneg hTr hQ.le
+  rw [impl_value, if_neg hT, fdiv_of_ne _ _ (ne_of_gt hQ)]
+  show (fsqrt _ >>= fun ra => fsqrt _ >>= fun rb => pure (ra * rb)) = _
+  rw [fsqrt_of_nonneg _ hdq]
+  show some (Real.sqrt _ * Real.sqrt _) = _
+  rw [← Real.sqrt_mul hdq]
+  congr 1
+  rw [div_mul_div_comm]
+  rw [Real.sqrt_div (by positivity), Real.sqrt_mul_self hTr]
+  sorry
 
 -- proof-end
```

Attack 6 — `atk_6.lean` → not a counterexample (attack assumes rather than establishes: introduces assumption token 'sorry' (0 -> 1) (not a valid counterexample)) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -103,18 +103,12 @@
 -- post-conditions-end
 
 -- impl-start
--- Compute the index from the co-occurrence matrix. The agreement count and the
--- two marginal counts are read out of their machine words; when the agreement
--- count is zero the index is the real number 0, otherwise it is obtained as the
--- product of two square roots, sqrt(T / P) times sqrt(T / Q), each ratio taken
--- before any multiplication of the marginal counts. Every division and every
--- root goes through the library's partial arithmetic, so the outcome names a
--- real number only if each step of the assembly did.
+-- CONTROL-FLOW-EFFECT: the zero test guards on the COLUMN marginal count, not the agreement count.
 noncomputable def implementation_fmIndex (M : List (List ℕ)) : Option ℝ :=
   let tk := (cmTkW M).toInt
   let pk := (cmPkW M).toInt
   let qk := (cmQkW M).toInt
-  if tk = 0 then some 0
+  if pk = 0 then some 0
   else do
     let a ← fdiv (tk : ℝ) (pk : ℝ)
     let b ← fdiv (tk : ℝ) (qk : ℝ)
@@ -151,21 +145,6 @@
 theorem fsqrt_of_nonneg (x : ℝ) (h : 0 ≤ x) : fsqrt x = some (Real.sqrt x) := by
   unfold fsqrt; rw [if_neg (not_lt.mpr h)]
 
-theorem impl_value (M : List (List ℕ)) :
-    implementation_fmIndex M
-      = if (cmTkW M).toInt = 0 then some (0 : ℝ)
-        else (do
-          let a ← fdiv ((cmTkW M).toInt : ℝ) ((cmPkW M).toInt : ℝ)
-          let b ← fdiv ((cmTkW M).toInt : ℝ) ((cmQkW M).toInt : ℝ)
-          let ra ← fsqrt a
-          let rb ← fsqrt b
-          pure (ra * rb)) := by
-  unfold implementation_fmIndex
-  rfl
-
-theorem zero_branch (M : List (List ℕ)) (h : (cmTkW M).toInt = 0) :
-    implementation_fmIndex M = some 0 := by
-  rw [impl_value, if_pos h]
 -- Module Positivity: integer inequalities T ≥ 0, P > 0, Q > 0.
 
 theorem sumSq_ge_total_of_partition (xs : List ℕ) :
@@ -438,45 +417,52 @@
       = (cmTk M : ℝ) / Real.sqrt ((cmPk M : ℝ) * (cmQk M : ℝ)) := by
   rw [Real.sqrt_div (sq_nonneg _), Real.sqrt_sq hT]
 
-theorem nonzero_branch (M : List (List ℕ)) (w : ℕ)
-    (hrect : ∀ r ∈ M, r.length = w)
-    (hwT : inWord (cmTk M)) (hwP : inWord (cmPk M)) (hwQ : inWord (cmQk M))
-    (hT : (cmTkW M).toInt ≠ 0) :
+theorem impl_value (M : List (List ℕ)) :
     implementation_fmIndex M
-      = some (((cmTkW M).toInt : ℝ)
-          / Real.sqrt (((cmPkW M).toInt : ℝ) * ((cmQkW M).toInt : ℝ))) := by
-  have hTne : cmTk M ≠ 0 := by rw [tkW_val M hwT] at hT; exact hT
-  rw [impl_value M, if_neg hT, tkW_val M hwT, pkW_val M hwP, qkW_val M hwQ]
-  have hP_int : 0 < cmPk M := P_pos M w hrect hTne
-  have hQ_int : 0 < cmQk M := Q_pos M hTne
-  have hT_int : 0 ≤ cmTk M := T_nonneg M
-  have hP : (0 : ℝ) < (cmPk M : ℝ) := by exact_mod_cast hP_int
-  have hQ : (0 : ℝ) < (cmQk M : ℝ) := by exact_mod_cast hQ_int
-  have hTr : (0 : ℝ) ≤ (cmTk M : ℝ) := by exact_mod_cast hT_int
-  have hdiv : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmPk M : ℝ) := div_nonneg hTr hP.le
-  have hdiv2 : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmQk M : ℝ) := div_nonneg hTr hQ.le
-  have hPQ : (0 : ℝ) < (cmPk M : ℝ) * (cmQk M : ℝ) := mul_pos hP hQ
-  rw [fdiv_of_ne _ _ (ne_of_gt hP), fdiv_of_ne _ _ (ne_of_gt hQ)]
-  show (fsqrt ((cmTk M : ℝ) / (cmPk M : ℝ)) >>= fun ra =>
-      fsqrt ((cmTk M : ℝ) / (cmQk M : ℝ)) >>= fun rb => pure (ra * rb)) = _
-  rw [fsqrt_of_nonneg _ hdiv, fsqrt_of_nonneg _ hdiv2]
-  show some (Real.sqrt ((cmTk M : ℝ) / (cmPk M : ℝ))
-      * Real.sqrt ((cmTk M : ℝ) / (cmQk M : ℝ))) = _
-  rw [sqrt_combine M hdiv, radicand_simp M hP hQ, sqrt_quotient M hTr hPQ]
-
--- The matrix is rectangular (every row has the common width `w`) — the shape of
--- every genuine co-occurrence matrix — and each of the three counts is small
--- enough to sit in one machine word. Under those the result is total: when the
--- agreement count is `0` the index is `0`, and otherwise both marginal counts
--- are strictly positive (each dominates the agreement count), so the quotient is
--- well-defined. Nothing is assumed about the size of the PRODUCT of the two
--- marginal counts.
+      = if (cmPkW M).toInt = 0 then some (0 : ℝ)
+        else (do
+          let a ← fdiv ((cmTkW M).toInt : ℝ) ((cmPkW M).toInt : ℝ)
+          let b ← fdiv ((cmTkW M).toInt : ℝ) ((cmQkW M).toInt : ℝ)
+          let ra ← fsqrt a
+          let rb ← fsqrt b
+          pure (ra * rb)) := by
+  unfold implementation_fmIndex; rfl
+
 theorem correct_fmIndex :
     ∀ (M : List (List ℕ)) (w : ℕ), (∀ r ∈ M, r.length = w) →
       inWord (cmTk M) → inWord (cmPk M) → inWord (cmQk M) →
       problem_spec_fmIndex M (implementation_fmIndex M) := by
   intro M w hrect hwT hwP hwQ
-  refine ⟨fun h => zero_branch M h, fun hT => ?_⟩
-  exact nonzero_branch M w hrect hwT hwP hwQ hT
+  constructor
+  · intro h
+    -- tk = 0. If pk = 0 the guard fires; otherwise we must still land on some 0.
+    by_cases hp : (cmPkW M).toInt = 0
+    · rw [impl_value, if_pos hp]
+    · rw [impl_value, if_neg hp, h]
+      rw [fdiv_of_ne _ _ hp]
+      show (fsqrt _ >>= fun ra => fdiv _ _ >>= fun rb => fsqrt _ >>= fun _ => _) = _
+      sorry
+  · intro hT
+    have hTne : cmTk M ≠ 0 := by rw [tkW_val M hwT] at hT; exact hT
+    have hP_int : 0 < cmPk M := P_pos M w hrect hTne
+    have hQ_int : 0 < cmQk M := Q_pos M hTne
+    have hTr : (0:ℝ) ≤ ((cmTkW M).toInt : ℝ) := by
+      rw [tkW_val M hwT]; exact_mod_cast T_nonneg M
+    have hP : (0:ℝ) < ((cmPkW M).toInt : ℝ) := by
+      rw [pkW_val M hwP]; exact_mod_cast hP_int
+    have hQ : (0:ℝ) < ((cmQkW M).toInt : ℝ) := by
+      rw [qkW_val M hwQ]; exact_mod_cast hQ_int
+    have hdiv : (0:ℝ) ≤ ((cmTkW M).toInt : ℝ) / ((cmPkW M).toInt : ℝ) := div_nonneg hTr hP.le
+    have hdiv2 : (0:ℝ) ≤ ((cmTkW M).toInt : ℝ) / ((cmQkW M).toInt : ℝ) := div_nonneg hTr hQ.le
+    have hPQ : (0:ℝ) < ((cmPkW M).toInt : ℝ) * ((cmQkW M).toInt : ℝ) := mul_pos hP hQ
+    rw [impl_value, if_neg (ne_of_gt hP), fdiv_of_ne _ _ (ne_of_gt hP),
+        fdiv_of_ne _ _ (ne_of_gt hQ)]
+    show (fsqrt _ >>= fun ra => fsqrt _ >>= fun rb => pure (ra * rb)) = _
+    rw [fsqrt_of_nonneg _ hdiv, fsqrt_of_nonneg _ hdiv2]
+    show some (Real.sqrt _ * Real.sqrt _) = _
+    rw [← Real.sqrt_mul hdiv, div_mul_div_comm,
+        show ((cmTkW M).toInt : ℝ) * ((cmTkW M).toInt : ℝ)
+          = ((cmTkW M).toInt : ℝ) ^ 2 by ring,
+        Real.sqrt_div (sq_nonneg _), Real.sqrt_sq hTr]
 
 -- proof-end
```

Attack 7 — `atk_7.lean` → not a counterexample (attack assumes rather than establishes: introduces assumption token 'sorry' (0 -> 1) (not a valid counterexample)) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -103,24 +103,20 @@
 -- post-conditions-end
 
 -- impl-start
--- Compute the index from the co-occurrence matrix. The agreement count and the
--- two marginal counts are read out of their machine words; when the agreement
--- count is zero the index is the real number 0, otherwise it is obtained as the
--- product of two square roots, sqrt(T / P) times sqrt(T / Q), each ratio taken
--- before any multiplication of the marginal counts. Every division and every
--- root goes through the library's partial arithmetic, so the outcome names a
--- real number only if each step of the assembly did.
+-- PARTIAL DOMAIN: names no real number on the EMPTY matrix; gold route elsewhere.
 noncomputable def implementation_fmIndex (M : List (List ℕ)) : Option ℝ :=
-  let tk := (cmTkW M).toInt
-  let pk := (cmPkW M).toInt
-  let qk := (cmQkW M).toInt
-  if tk = 0 then some 0
-  else do
-    let a ← fdiv (tk : ℝ) (pk : ℝ)
-    let b ← fdiv (tk : ℝ) (qk : ℝ)
-    let ra ← fsqrt a
-    let rb ← fsqrt b
-    pure (ra * rb)
+  if M.isEmpty then none
+  else
+    let tk := (cmTkW M).toInt
+    let pk := (cmPkW M).toInt
+    let qk := (cmQkW M).toInt
+    if tk = 0 then some 0
+    else do
+      let a ← fdiv (tk : ℝ) (pk : ℝ)
+      let b ← fdiv (tk : ℝ) (qk : ℝ)
+      let ra ← fsqrt a
+      let rb ← fsqrt b
+      pure (ra * rb)
 -- impl-end
 
 
@@ -151,21 +147,6 @@
 theorem fsqrt_of_nonneg (x : ℝ) (h : 0 ≤ x) : fsqrt x = some (Real.sqrt x) := by
   unfold fsqrt; rw [if_neg (not_lt.mpr h)]
 
-theorem impl_value (M : List (List ℕ)) :
-    implementation_fmIndex M
-      = if (cmTkW M).toInt = 0 then some (0 : ℝ)
-        else (do
-          let a ← fdiv ((cmTkW M).toInt : ℝ) ((cmPkW M).toInt : ℝ)
-          let b ← fdiv ((cmTkW M).toInt : ℝ) ((cmQkW M).toInt : ℝ)
-          let ra ← fsqrt a
-          let rb ← fsqrt b
-          pure (ra * rb)) := by
-  unfold implementation_fmIndex
-  rfl
-
-theorem zero_branch (M : List (List ℕ)) (h : (cmTkW M).toInt = 0) :
-    implementation_fmIndex M = some 0 := by
-  rw [impl_value, if_pos h]
 -- Module Positivity: integer inequalities T ≥ 0, P > 0, Q > 0.
 
 theorem sumSq_ge_total_of_partition (xs : List ℕ) :
@@ -438,45 +419,52 @@
       = (cmTk M : ℝ) / Real.sqrt ((cmPk M : ℝ) * (cmQk M : ℝ)) := by
   rw [Real.sqrt_div (sq_nonneg _), Real.sqrt_sq hT]
 
-theorem nonzero_branch (M : List (List ℕ)) (w : ℕ)
-    (hrect : ∀ r ∈ M, r.length = w)
-    (hwT : inWord (cmTk M)) (hwP : inWord (cmPk M)) (hwQ : inWord (cmQk M))
-    (hT : (cmTkW M).toInt ≠ 0) :
+theorem impl_value (M : List (List ℕ)) (hne : M.isEmpty = false) :
     implementation_fmIndex M
-      = some (((cmTkW M).toInt : ℝ)
-          / Real.sqrt (((cmPkW M).toInt : ℝ) * ((cmQkW M).toInt : ℝ))) := by
-  have hTne : cmTk M ≠ 0 := by rw [tkW_val M hwT] at hT; exact hT
-  rw [impl_value M, if_neg hT, tkW_val M hwT, pkW_val M hwP, qkW_val M hwQ]
-  have hP_int : 0 < cmPk M := P_pos M w hrect hTne
-  have hQ_int : 0 < cmQk M := Q_pos M hTne
-  have hT_int : 0 ≤ cmTk M := T_nonneg M
-  have hP : (0 : ℝ) < (cmPk M : ℝ) := by exact_mod_cast hP_int
-  have hQ : (0 : ℝ) < (cmQk M : ℝ) := by exact_mod_cast hQ_int
-  have hTr : (0 : ℝ) ≤ (cmTk M : ℝ) := by exact_mod_cast hT_int
-  have hdiv : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmPk M : ℝ) := div_nonneg hTr hP.le
-  have hdiv2 : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmQk M : ℝ) := div_nonneg hTr hQ.le
-  have hPQ : (0 : ℝ) < (cmPk M : ℝ) * (cmQk M : ℝ) := mul_pos hP hQ
-  rw [fdiv_of_ne _ _ (ne_of_gt hP), fdiv_of_ne _ _ (ne_of_gt hQ)]
-  show (fsqrt ((cmTk M : ℝ) / (cmPk M : ℝ)) >>= fun ra =>
-      fsqrt ((cmTk M : ℝ) / (cmQk M : ℝ)) >>= fun rb => pure (ra * rb)) = _
-  rw [fsqrt_of_nonneg _ hdiv, fsqrt_of_nonneg _ hdiv2]
-  show some (Real.sqrt ((cmTk M : ℝ) / (cmPk M : ℝ))
-      * Real.sqrt ((cmTk M : ℝ) / (cmQk M : ℝ))) = _
-  rw [sqrt_combine M hdiv, radicand_simp M hP hQ, sqrt_quotient M hTr hPQ]
-
--- The matrix is rectangular (every row has the common width `w`) — the shape of
--- every genuine co-occurrence matrix — and each of the three counts is small
--- enough to sit in one machine word. Under those the result is total: when the
--- agreement count is `0` the index is `0`, and otherwise both marginal counts
--- are strictly positive (each dominates the agreement count), so the quotient is
--- well-defined. Nothing is assumed about the size of the PRODUCT of the two
--- marginal counts.
+      = if (cmTkW M).toInt = 0 then some (0 : ℝ)
+        else (do
+          let a ← fdiv ((cmTkW M).toInt : ℝ) ((cmPkW M).toInt : ℝ)
+          let b ← fdiv ((cmTkW M).toInt : ℝ) ((cmQkW M).toInt : ℝ)
+          let ra ← fsqrt a
+          let rb ← fsqrt b
+          pure (ra * rb)) := by
+  unfold implementation_fmIndex; rw [if_neg (by simp [hne])]
+
 theorem correct_fmIndex :
     ∀ (M : List (List ℕ)) (w : ℕ), (∀ r ∈ M, r.length = w) →
       inWord (cmTk M) → inWord (cmPk M) → inWord (cmQk M) →
       problem_spec_fmIndex M (implementation_fmIndex M) := by
   intro M w hrect hwT hwP hwQ
-  refine ⟨fun h => zero_branch M h, fun hT => ?_⟩
-  exact nonzero_branch M w hrect hwT hwP hwQ hT
+  by_cases hemp : M.isEmpty
+  · -- M = []: the impl names no real number, but the spec demands some 0.
+    have hM : M = [] := by cases M with | nil => rfl | cons a t => simp at hemp
+    subst hM
+    refine ⟨fun _ => ?_, fun hT => absurd ?_ hT⟩
+    · unfold implementation_fmIndex; simp
+      sorry
+    · simp [cmTkW, cmTk, sumSqZ, totalZ]
+  · have hne : M.isEmpty = false := by simp at hemp; simp [hemp]
+    refine ⟨fun h => by rw [impl_value M hne, if_pos h], fun hT => ?_⟩
+    have hTne : cmTk M ≠ 0 := by rw [tkW_val M hwT] at hT; exact hT
+    have hP_int : 0 < cmPk M := P_pos M w hrect hTne
+    have hQ_int : 0 < cmQk M := Q_pos M hTne
+    have hTr : (0:ℝ) ≤ ((cmTkW M).toInt : ℝ) := by
+      rw [tkW_val M hwT]; exact_mod_cast T_nonneg M
+    have hP : (0:ℝ) < ((cmPkW M).toInt : ℝ) := by
+      rw [pkW_val M hwP]; exact_mod_cast hP_int
+    have hQ : (0:ℝ) < ((cmQkW M).toInt : ℝ) := by
+      rw [qkW_val M hwQ]; exact_mod_cast hQ_int
+    have hdiv : (0:ℝ) ≤ ((cmTkW M).toInt : ℝ) / ((cmPkW M).toInt : ℝ) := div_nonneg hTr hP.le
+    have hdiv2 : (0:ℝ) ≤ ((cmTkW M).toInt : ℝ) / ((cmQkW M).toInt : ℝ) := div_nonneg hTr hQ.le
+    have hPQ : (0:ℝ) < ((cmPkW M).toInt : ℝ) * ((cmQkW M).toInt : ℝ) := mul_pos hP hQ
+    rw [impl_value M hne, if_neg hT, fdiv_of_ne _ _ (ne_of_gt hP),
+        fdiv_of_ne _ _ (ne_of_gt hQ)]
+    show (fsqrt _ >>= fun ra => fsqrt _ >>= fun rb => pure (ra * rb)) = _
+    rw [fsqrt_of_nonneg _ hdiv, fsqrt_of_nonneg _ hdiv2]
+    show some (Real.sqrt _ * Real.sqrt _) = _
+    rw [← Real.sqrt_mul hdiv, div_mul_div_comm,
+        show ((cmTkW M).toInt : ℝ) * ((cmTkW M).toInt : ℝ)
+          = ((cmTkW M).toInt : ℝ) ^ 2 by ring,
+        Real.sqrt_div (sq_nonneg _), Real.sqrt_sq hTr]
 
 -- proof-end
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -103,380 +103,27 @@
 -- post-conditions-end
 
 -- impl-start
--- Compute the index from the co-occurrence matrix. The agreement count and the
--- two marginal counts are read out of their machine words; when the agreement
--- count is zero the index is the real number 0, otherwise it is obtained as the
--- product of two square roots, sqrt(T / P) times sqrt(T / Q), each ratio taken
--- before any multiplication of the marginal counts. Every division and every
--- root goes through the library's partial arithmetic, so the outcome names a
--- real number only if each step of the assembly did.
+-- UNGROUNDED ORACLE ECHO: names whatever value the postcondition admits; no arithmetic at all.
 noncomputable def implementation_fmIndex (M : List (List ℕ)) : Option ℝ :=
-  let tk := (cmTkW M).toInt
-  let pk := (cmPkW M).toInt
-  let qk := (cmQkW M).toInt
-  if tk = 0 then some 0
-  else do
-    let a ← fdiv (tk : ℝ) (pk : ℝ)
-    let b ← fdiv (tk : ℝ) (qk : ℝ)
-    let ra ← fsqrt a
-    let rb ← fsqrt b
-    pure (ra * rb)
+  open Classical in
+  if h : ∃ r : Option ℝ, problem_spec_fmIndex M r then h.choose else none
 -- impl-end
 
 
 -- proof-start
--- Module M_reduce: read the three counts back out of their machine words, then
--- reduce the program to its mathematical value and peel the zero branch.
-
-theorem word_value (z : ℤ) (h : inWord z) : (BitVec.ofInt 64 z).toInt = z := by
-  obtain ⟨h1, h2⟩ := h
-  rw [BitVec.toInt_ofInt]
-  exact Int.bmod_eq_of_le (by norm_num; omega) (by norm_num; omega)
-
-theorem tkW_val (M : List (List ℕ)) (h : inWord (cmTk M)) :
-    (cmTkW M).toInt = cmTk M := by
-  unfold cmTkW; exact word_value _ h
-
-theorem pkW_val (M : List (List ℕ)) (h : inWord (cmPk M)) :
-    (cmPkW M).toInt = cmPk M := by
-  unfold cmPkW; exact word_value _ h
-
-theorem qkW_val (M : List (List ℕ)) (h : inWord (cmQk M)) :
-    (cmQkW M).toInt = cmQk M := by
-  unfold cmQkW; exact word_value _ h
-
-theorem fdiv_of_ne (x y : ℝ) (h : y ≠ 0) : fdiv x y = some (x / y) := by
-  unfold fdiv; rw [if_neg h]
-
-theorem fsqrt_of_nonneg (x : ℝ) (h : 0 ≤ x) : fsqrt x = some (Real.sqrt x) := by
-  unfold fsqrt; rw [if_neg (not_lt.mpr h)]
-
-theorem impl_value (M : List (List ℕ)) :
-    implementation_fmIndex M
-      = if (cmTkW M).toInt = 0 then some (0 : ℝ)
-        else (do
-          let a ← fdiv ((cmTkW M).toInt : ℝ) ((cmPkW M).toInt : ℝ)
-          let b ← fdiv ((cmTkW M).toInt : ℝ) ((cmQkW M).toInt : ℝ)
-          let ra ← fsqrt a
-          let rb ← fsqrt b
-          pure (ra * rb)) := by
-  unfold implementation_fmIndex
-  rfl
-
-theorem zero_branch (M : List (List ℕ)) (h : (cmTkW M).toInt = 0) :
-    implementation_fmIndex M = some 0 := by
-  rw [impl_value, if_pos h]
--- Module Positivity: integer inequalities T ≥ 0, P > 0, Q > 0.
-
-theorem sumSq_ge_total_of_partition (xs : List ℕ) :
-    (xs.map (fun x => (x : ℤ))).sum ≤ sumSqZ xs := by
-  induction xs with
-  | nil => rfl
-  | cons a t ih =>
-    simp [sumSqZ] at *
-    nlinarith [ih, Int.natCast_nonneg a]
--- Module GoCalculus: reconstruct the recursion theory of List.transpose from
--- the raw array-based List.transpose.go definition (PREPEND direction).
-
-theorem transpose_go_prepend_form (r : List ℕ) (acc : Array (List ℕ))
-    (h : acc.size ≤ r.length) :
-    (List.transpose.go r acc).toList
-      = List.zipWith (fun col x => x :: col) acc.toList r
-          ++ ((r.drop acc.size).map (fun x => [x])) := by
-  have helperMapM : ∀ (cols : List (List ℕ)) (r : List ℕ),
-      cols.length ≤ r.length →
-      (List.mapM (m := StateM (List ℕ)) List.transpose.pop cols) r
-        = (List.zipWith (fun col x => x :: col) cols r, r.drop cols.length) := by
-    intro cols
-    induction cols with
-    | nil => intro r _; simp [List.mapM_nil, pure, StateT.pure]
-    | cons c cs ih =>
-      intro r hlen
-      rw [List.mapM_cons]
-      cases r with
-      | nil => simp at hlen
-      | cons a r' =>
-        simp only [List.length_cons, Nat.add_le_add_iff_right] at hlen
-        simp only [List.transpose.pop, bind, StateT.bind, pure, StateT.pure, ih r' hlen]
-        simp [List.zipWith]
-  unfold List.transpose.go
-  rw [Array.mapM_eq_mapM_toList]
-  have hlen : acc.toList.length ≤ r.length := by simpa using h
-  simp only [Functor.map, StateT.map]
-  rw [helperMapM acc.toList r hlen]
-  simp only [Array.foldl_toList_eq_map, Array.length_toList]
-
-theorem transpose_go_empty_acc (r : List ℕ) :
-    (List.transpose.go r #[]).toList = r.map (fun x => [x]) := by
-  have h : (#[] : Array (List ℕ)).size ≤ r.length := by simp
-  rw [transpose_go_prepend_form r #[] h]
-  simp
-
-theorem length_transpose_rect (M : List (List ℕ)) (w : ℕ)
-    (hne : M ≠ []) (hrect : ∀ r ∈ M, r.length = w) :
-    M.transpose.length = w := by
-  have key : ∀ (N : List (List ℕ)), N ≠ [] → (∀ r ∈ N, r.length = w) →
-      (List.foldr List.transpose.go #[] N).toList.length = w := by
-    intro N
-    induction N with
-    | nil => intro h; exact absurd rfl h
-    | cons r rest ih =>
-      intro _ hr
-      rcases rest with _ | ⟨r', rest'⟩
-      · simp only [List.foldr_cons, List.foldr_nil]
-        rw [transpose_go_empty_acc, List.length_map]
-        exact hr r (by simp)
-      · have hrestne : (r' :: rest') ≠ [] := by simp
-        have hrestrect : ∀ x ∈ (r' :: rest'), x.length = w := by
-          intro x hx; exact hr x (by simp [hx])
-        have accsize : (List.foldr List.transpose.go #[] (r' :: rest')).size = w := by
-          have := ih hrestne hrestrect
-          rwa [Array.length_toList] at this
-        have hrw : r.length = w := hr r (by simp)
-        rw [List.foldr_cons]
-        set acc := List.foldr List.transpose.go #[] (r' :: rest') with hacc
-        rw [transpose_go_prepend_form r acc (by rw [accsize, hrw])]
-        rw [List.length_append, List.length_zipWith, List.length_map, List.length_drop]
-        rw [Array.length_toList, accsize, hrw]
-        omega
-  have := key M hne hrect
-  rw [List.transpose, Array.length_toList]
-  rwa [Array.length_toList] at this
-
-theorem transpose_cons_rect (r : List ℕ) (rs : List (List ℕ))
-    (hlen : rs.transpose.length = r.length) :
-    (r :: rs).transpose = List.zipWith (· :: ·) r rs.transpose := by
-  have hacc : rs.transpose = (List.foldr List.transpose.go #[] rs).toList := rfl
-  have hgo : (r :: rs).transpose
-      = (List.transpose.go r (List.foldr List.transpose.go #[] rs)).toList := rfl
-  set acc := List.foldr List.transpose.go #[] rs with hdef
-  have hsize : acc.size ≤ r.length := by
-    have : acc.toList.length = r.length := by rw [← hacc]; exact hlen
-    simpa using this.le
-  rw [hgo, transpose_go_prepend_form r acc hsize]
-  have hdrop : r.drop acc.size = [] := by
-    apply List.drop_eq_nil_of_le
-    have : acc.toList.length = r.length := by rw [← hacc]; exact hlen
-    simpa using this.ge
-  rw [hdrop]
-  simp only [List.map_nil, List.append_nil, ← hacc]
-  rw [← List.zipWith_flip]
-  rfl
-
--- Module ZipWithFlatten: the pure multiset-reassociation permutation.
-
-theorem zipWith_cons_flatten_perm (r : List ℕ) (cols : List (List ℕ))
-    (hlen : r.length = cols.length) :
-    (List.zipWith (· :: ·) r cols).flatten.Perm (r ++ cols.flatten) := by
-  induction r generalizing cols with
-  | nil =>
-    have : cols = [] := List.eq_nil_of_length_eq_zero hlen.symm
-    subst this; simp
-  | cons a r' ih =>
-    cases cols with
-    | nil => simp at hlen
-    | cons c cols' =>
-      simp only [List.zipWith_cons_cons, List.flatten_cons, List.cons_append]
-      refine List.Perm.cons a ?_
-      have ih' := ih cols' (by simpa using hlen)
-      have h1 : (c ++ (List.zipWith (· :: ·) r' cols').flatten).Perm (c ++ (r' ++ cols'.flatten)) :=
-        ih'.append_left c
-      have h2 : (c ++ (r' ++ cols'.flatten)).Perm (r' ++ (c ++ cols'.flatten)) := by
-        rw [← List.append_assoc, ← List.append_assoc]
-        exact (List.perm_append_comm).append_right _
-      exact h1.trans h2
-
-theorem transpose_flatten_perm (M : List (List ℕ)) (w : ℕ)
-    (hrect : ∀ r ∈ M, r.length = w) :
-    (M.transpose.flatten).Perm M.flatten := by
-  induction M with
-  | nil => simp [List.transpose]
-  | cons r rs ih =>
-    have hr : r.length = w := hrect r (List.mem_cons_self ..)
-    have hrs : ∀ x ∈ rs, x.length = w := fun x hx => hrect x (List.mem_cons_of_mem r hx)
-    rcases rs with _ | ⟨r2, rs2⟩
-    · -- singleton: M = [r]
-      have hgo : ([r] : List (List ℕ)).transpose = r.map (fun x => [x]) := by
-        simpa [List.transpose] using transpose_go_empty_acc r
-      rw [hgo]
-      have key : ∀ l : List ℕ, (l.map (fun x => [x])).flatten = l := by
-        intro l
-        induction l with
-        | nil => simp
-        | cons a as iha => simpa using iha
-      rw [key r]
-      simp
-    · -- general cons: rs = r2 :: rs2 ≠ []
-      set rs : List (List ℕ) := r2 :: rs2 with hrsdef
-      have hne : rs ≠ [] := by simp [hrsdef]
-      have hlenT : rs.transpose.length = r.length := by
-        rw [length_transpose_rect rs w hne hrs, hr]
-      rw [transpose_cons_rect r rs hlenT]
-      have hperm1 : (List.zipWith (· :: ·) r rs.transpose).flatten.Perm
-          (r ++ rs.transpose.flatten) :=
-        zipWith_cons_flatten_perm r rs.transpose hlenT.symm
-      have hperm2 : (r ++ rs.transpose.flatten).Perm (r ++ rs.flatten) :=
-        (ih hrs).append_left r
-      have : (List.zipWith (· :: ·) r rs.transpose).flatten.Perm (r ++ rs.flatten) :=
-        hperm1.trans hperm2
-      simpa [List.flatten_cons] using this
-
-theorem sumSqZ_perm {xs ys : List ℕ} (h : xs.Perm ys) :
-    sumSqZ xs = sumSqZ ys := by
-  simp only [sumSqZ, List.pure_def, List.bind_eq_flatMap, ← List.map_eq_flatMap, List.map_map]
-  exact (h.map fun a : ℕ => (a : ℤ) * (a : ℤ)).sum_eq
-
-theorem flatten_sumSq_le_map_sum (L : List (List ℕ)) :
-    sumSqZ L.flatten ≤ sumSqZ (L.map (fun r => r.sum)) := by
-  have key : ∀ (r : List ℕ), sumSqZ r ≤ (r.sum : ℤ) * (r.sum : ℤ) := by
-    intro r
-    induction r with
-    | nil => simp [sumSqZ]
-    | cons x xs ih =>
-      have hx : (0:ℤ) ≤ (x:ℤ) := by positivity
-      have hs : (0:ℤ) ≤ (xs.sum : ℤ) := by positivity
-      have e1 : sumSqZ (x :: xs) = (x:ℤ) * (x:ℤ) + sumSqZ xs := by simp [sumSqZ]
-      have e2 : ((x :: xs).sum : ℤ) = (x:ℤ) + (xs.sum : ℤ) := by
-        push_cast [List.sum_cons]; ring
-      rw [e1, e2]
-      nlinarith [ih, mul_nonneg hx hs]
-  induction L with
-  | nil => simp [sumSqZ]
-  | cons r rest ih =>
-    have happ : sumSqZ (r ++ rest.flatten) = sumSqZ r + sumSqZ rest.flatten := by
-      simp [sumSqZ, List.map_append, List.sum_append]
-    have hcons : sumSqZ ((r.sum) :: (rest.map (fun r => r.sum)))
-        = (r.sum : ℤ) * (r.sum : ℤ) + sumSqZ (rest.map (fun r => r.sum)) := by
-      simp [sumSqZ]
-    simp only [List.flatten_cons, List.map_cons]
-    rw [happ, hcons]
-    linarith [ih, key r]
-theorem map_sum_flatten_castZ (L : List (List ℕ)) :
-    ((L.map (fun r => r.sum)).sum : ℤ) = (L.flatten.map (fun x => (x : ℤ))).sum := by
-  simp only [bind_pure_comp, List.map_id', Functor.map]
-  rw [← Nat.cast_list_sum L.flatten, List.sum_flatten, Nat.cast_list_sum, List.map_map]
-  rfl
-
-theorem colTotalSum_eq_total_lemma (M : List (List ℕ)) (w : ℕ)
-    (hrect : ∀ r ∈ M, r.length = w) :
-    ((M.transpose.map (fun c => c.sum)).sum : ℤ) = totalZ M := by
-  rw [map_sum_flatten_castZ M.transpose]
-  unfold totalZ
-  have hp := transpose_flatten_perm M w hrect
-  simp only [bind_pure_comp, List.map_id_fun']
-  exact (hp.map (fun x : ℕ => (x : ℤ))).sum_eq
-
-theorem T_nonneg (M : List (List ℕ)) : 0 ≤ cmTk M := by
-  have h := sumSq_ge_total_of_partition M.flatten
-  simp only [cmTk, totalZ]
-  linarith
-
-theorem Q_pos (M : List (List ℕ)) (hT : cmTk M ≠ 0) : 0 < cmQk M := by
-  have hrow : ∀ r : List ℕ, sumSqZ r ≤ ((r.sum : ℤ)) * ((r.sum : ℤ)) := by
-    intro r
-    induction r with
-    | nil => simp [sumSqZ]
-    | cons x xs ih =>
-      have hc : sumSqZ (x::xs) = (x:ℤ)*(x:ℤ) + sumSqZ xs := by simp [sumSqZ]
-      have hsum : ((x::xs).sum : ℤ) = (x:ℤ) + (xs.sum : ℤ) := by push_cast [List.sum_cons]; ring
-      rw [hc, hsum]
-      have hx : (0:ℤ) ≤ (x:ℤ) := by positivity
-      have hs : (0:ℤ) ≤ (xs.sum:ℤ) := by positivity
-      nlinarith [ih, hx, hs]
-  have hle : sumSqZ M.flatten ≤ sumSqZ (M.map (fun r => r.sum)) := by
-    clear hT
-    induction M with
-    | nil => simp [sumSqZ]
-    | cons r rs ih =>
-      have e1 : sumSqZ (r :: rs).flatten = sumSqZ r + sumSqZ rs.flatten := by
-        rw [List.flatten_cons]; simp [sumSqZ, List.map_append, List.sum_append]
-      have e2 : sumSqZ ((r::rs).map (fun r => r.sum)) = (r.sum:ℤ)*(r.sum:ℤ) + sumSqZ (rs.map (fun r => r.sum)) := by
-        rw [List.map_cons]; simp [sumSqZ]
-      rw [e1, e2]
-      have hr := hrow r
-      linarith [ih]
-  have hTpos : 0 < cmTk M := lt_of_le_of_ne (T_nonneg M) (Ne.symm hT)
-  have hle2 : cmTk M ≤ cmQk M := by unfold cmTk cmQk; omega
-  omega
-
-theorem P_pos (M : List (List ℕ)) (w : ℕ) (hrect : ∀ r ∈ M, r.length = w)
-    (hT : cmTk M ≠ 0) : 0 < cmPk M := by
-  have hTpos : 0 < cmTk M := lt_of_le_of_ne (T_nonneg M) (Ne.symm hT)
-  have hT2 : totalZ M < sumSqZ M.flatten := by
-    have h := hTpos
-    unfold cmTk at h
-    omega
-  have hperm : (M.transpose.flatten).Perm M.flatten := transpose_flatten_perm M w hrect
-  have heq : sumSqZ M.transpose.flatten = sumSqZ M.flatten := sumSqZ_perm hperm
-  have hle : sumSqZ M.transpose.flatten ≤ sumSqZ (M.transpose.map (fun r => r.sum)) :=
-    flatten_sumSq_le_map_sum M.transpose
-  rw [heq] at hle
-  unfold cmPk
-  omega
-
--- Module Algebra: the real-analysis sqrt identity.
-
-theorem sqrt_combine (M : List (List ℕ))
-    (h : 0 ≤ (cmTk M : ℝ) / (cmPk M : ℝ)) :
-    Real.sqrt ((cmTk M : ℝ) / (cmPk M : ℝ))
-        * Real.sqrt ((cmTk M : ℝ) / (cmQk M : ℝ))
-      = Real.sqrt (((cmTk M : ℝ) / (cmPk M : ℝ))
-          * ((cmTk M : ℝ) / (cmQk M : ℝ))) :=
-  (Real.sqrt_mul h _).symm
-
-theorem radicand_simp (M : List (List ℕ))
-    (hP : (0 : ℝ) < (cmPk M : ℝ)) (hQ : (0 : ℝ) < (cmQk M : ℝ)) :
-    ((cmTk M : ℝ) / (cmPk M : ℝ)) * ((cmTk M : ℝ) / (cmQk M : ℝ))
-      = (cmTk M : ℝ) ^ 2 / ((cmPk M : ℝ) * (cmQk M : ℝ)) := by
-  rw [div_mul_div_comm]
-  ring
-
-theorem sqrt_quotient (M : List (List ℕ))
-    (hT : (0 : ℝ) ≤ (cmTk M : ℝ))
-    (hPQ : (0 : ℝ) < (cmPk M : ℝ) * (cmQk M : ℝ)) :
-    Real.sqrt ((cmTk M : ℝ) ^ 2 / ((cmPk M : ℝ) * (cmQk M : ℝ)))
-      = (cmTk M : ℝ) / Real.sqrt ((cmPk M : ℝ) * (cmQk M : ℝ)) := by
-  rw [Real.sqrt_div (sq_nonneg _), Real.sqrt_sq hT]
-
-theorem nonzero_branch (M : List (List ℕ)) (w : ℕ)
-    (hrect : ∀ r ∈ M, r.length = w)
-    (hwT : inWord (cmTk M)) (hwP : inWord (cmPk M)) (hwQ : inWord (cmQk M))
-    (hT : (cmTkW M).toInt ≠ 0) :
-    implementation_fmIndex M
-      = some (((cmTkW M).toInt : ℝ)
-          / Real.sqrt (((cmPkW M).toInt : ℝ) * ((cmQkW M).toInt : ℝ))) := by
-  have hTne : cmTk M ≠ 0 := by rw [tkW_val M hwT] at hT; exact hT
-  rw [impl_value M, if_neg hT, tkW_val M hwT, pkW_val M hwP, qkW_val M hwQ]
-  have hP_int : 0 < cmPk M := P_pos M w hrect hTne
-  have hQ_int : 0 < cmQk M := Q_pos M hTne
-  have hT_int : 0 ≤ cmTk M := T_nonneg M
-  have hP : (0 : ℝ) < (cmPk M : ℝ) := by exact_mod_cast hP_int
-  have hQ : (0 : ℝ) < (cmQk M : ℝ) := by exact_mod_cast hQ_int
-  have hTr : (0 : ℝ) ≤ (cmTk M : ℝ) := by exact_mod_cast hT_int
-  have hdiv : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmPk M : ℝ) := div_nonneg hTr hP.le
-  have hdiv2 : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmQk M : ℝ) := div_nonneg hTr hQ.le
-  have hPQ : (0 : ℝ) < (cmPk M : ℝ) * (cmQk M : ℝ) := mul_pos hP hQ
-  rw [fdiv_of_ne _ _ (ne_of_gt hP), fdiv_of_ne _ _ (ne_of_gt hQ)]
-  show (fsqrt ((cmTk M : ℝ) / (cmPk M : ℝ)) >>= fun ra =>
-      fsqrt ((cmTk M : ℝ) / (cmQk M : ℝ)) >>= fun rb => pure (ra * rb)) = _
-  rw [fsqrt_of_nonneg _ hdiv, fsqrt_of_nonneg _ hdiv2]
-  show some (Real.sqrt ((cmTk M : ℝ) / (cmPk M : ℝ))
-      * Real.sqrt ((cmTk M : ℝ) / (cmQk M : ℝ))) = _
-  rw [sqrt_combine M hdiv, radicand_simp M hP hQ, sqrt_quotient M hTr hPQ]
-
--- The matrix is rectangular (every row has the common width `w`) — the shape of
--- every genuine co-occurrence matrix — and each of the three counts is small
--- enough to sit in one machine word. Under those the result is total: when the
--- agreement count is `0` the index is `0`, and otherwise both marginal counts
--- are strictly positive (each dominates the agreement count), so the quotient is
--- well-defined. Nothing is assumed about the size of the PRODUCT of the two
--- marginal counts.
 theorem correct_fmIndex :
     ∀ (M : List (List ℕ)) (w : ℕ), (∀ r ∈ M, r.length = w) →
       inWord (cmTk M) → inWord (cmPk M) → inWord (cmQk M) →
       problem_spec_fmIndex M (implementation_fmIndex M) := by
   intro M w hrect hwT hwP hwQ
-  refine ⟨fun h => zero_branch M h, fun hT => ?_⟩
-  exact nonzero_branch M w hrect hwT hwP hwQ hT
+  have hex : ∃ r : Option ℝ, problem_spec_fmIndex M r := by
+    by_cases h : (cmTkW M).toInt = 0
+    · exact ⟨some 0, fun _ => rfl, fun hc => absurd h hc⟩
+    · exact ⟨some (((cmTkW M).toInt : ℝ)
+        / Real.sqrt (((cmPkW M).toInt : ℝ) * ((cmQkW M).toInt : ℝ))),
+        fun hc => absurd hc h, fun _ => rfl⟩
+  unfold implementation_fmIndex
+  rw [dif_pos hex]
+  exact hex.choose_spec
 
 -- proof-end
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -103,24 +103,15 @@
 -- post-conditions-end
 
 -- impl-start
--- Compute the index from the co-occurrence matrix. The agreement count and the
--- two marginal counts are read out of their machine words; when the agreement
--- count is zero the index is the real number 0, otherwise it is obtained as the
--- product of two square roots, sqrt(T / P) times sqrt(T / Q), each ratio taken
--- before any multiplication of the marginal counts. Every division and every
--- root goes through the library's partial arithmetic, so the outcome names a
--- real number only if each step of the assembly did.
+-- SQUARED RADICAND: sqrt(tk^2 / (pk*qk)) -- one root, exact product of the marginals.
 noncomputable def implementation_fmIndex (M : List (List ℕ)) : Option ℝ :=
   let tk := (cmTkW M).toInt
   let pk := (cmPkW M).toInt
   let qk := (cmQkW M).toInt
   if tk = 0 then some 0
   else do
-    let a ← fdiv (tk : ℝ) (pk : ℝ)
-    let b ← fdiv (tk : ℝ) (qk : ℝ)
-    let ra ← fsqrt a
-    let rb ← fsqrt b
-    pure (ra * rb)
+    let r ← fdiv ((tk : ℝ) * (tk : ℝ)) ((pk : ℝ) * (qk : ℝ))
+    fsqrt r
 -- impl-end
 
 
@@ -151,21 +142,6 @@
 theorem fsqrt_of_nonneg (x : ℝ) (h : 0 ≤ x) : fsqrt x = some (Real.sqrt x) := by
   unfold fsqrt; rw [if_neg (not_lt.mpr h)]
 
-theorem impl_value (M : List (List ℕ)) :
-    implementation_fmIndex M
-      = if (cmTkW M).toInt = 0 then some (0 : ℝ)
-        else (do
-          let a ← fdiv ((cmTkW M).toInt : ℝ) ((cmPkW M).toInt : ℝ)
-          let b ← fdiv ((cmTkW M).toInt : ℝ) ((cmQkW M).toInt : ℝ)
-          let ra ← fsqrt a
-          let rb ← fsqrt b
-          pure (ra * rb)) := by
-  unfold implementation_fmIndex
-  rfl
-
-theorem zero_branch (M : List (List ℕ)) (h : (cmTkW M).toInt = 0) :
-    implementation_fmIndex M = some 0 := by
-  rw [impl_value, if_pos h]
 -- Module Positivity: integer inequalities T ≥ 0, P > 0, Q > 0.
 
 theorem sumSq_ge_total_of_partition (xs : List ℕ) :
@@ -438,45 +414,35 @@
       = (cmTk M : ℝ) / Real.sqrt ((cmPk M : ℝ) * (cmQk M : ℝ)) := by
   rw [Real.sqrt_div (sq_nonneg _), Real.sqrt_sq hT]
 
-theorem nonzero_branch (M : List (List ℕ)) (w : ℕ)
-    (hrect : ∀ r ∈ M, r.length = w)
-    (hwT : inWord (cmTk M)) (hwP : inWord (cmPk M)) (hwQ : inWord (cmQk M))
-    (hT : (cmTkW M).toInt ≠ 0) :
-    implementation_fmIndex M
-      = some (((cmTkW M).toInt : ℝ)
-          / Real.sqrt (((cmPkW M).toInt : ℝ) * ((cmQkW M).toInt : ℝ))) := by
-  have hTne : cmTk M ≠ 0 := by rw [tkW_val M hwT] at hT; exact hT
-  rw [impl_value M, if_neg hT, tkW_val M hwT, pkW_val M hwP, qkW_val M hwQ]
-  have hP_int : 0 < cmPk M := P_pos M w hrect hTne
-  have hQ_int : 0 < cmQk M := Q_pos M hTne
-  have hT_int : 0 ≤ cmTk M := T_nonneg M
-  have hP : (0 : ℝ) < (cmPk M : ℝ) := by exact_mod_cast hP_int
-  have hQ : (0 : ℝ) < (cmQk M : ℝ) := by exact_mod_cast hQ_int
-  have hTr : (0 : ℝ) ≤ (cmTk M : ℝ) := by exact_mod_cast hT_int
-  have hdiv : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmPk M : ℝ) := div_nonneg hTr hP.le
-  have hdiv2 : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmQk M : ℝ) := div_nonneg hTr hQ.le
-  have hPQ : (0 : ℝ) < (cmPk M : ℝ) * (cmQk M : ℝ) := mul_pos hP hQ
-  rw [fdiv_of_ne _ _ (ne_of_gt hP), fdiv_of_ne _ _ (ne_of_gt hQ)]
-  show (fsqrt ((cmTk M : ℝ) / (cmPk M : ℝ)) >>= fun ra =>
-      fsqrt ((cmTk M : ℝ) / (cmQk M : ℝ)) >>= fun rb => pure (ra * rb)) = _
-  rw [fsqrt_of_nonneg _ hdiv, fsqrt_of_nonneg _ hdiv2]
-  show some (Real.sqrt ((cmTk M : ℝ) / (cmPk M : ℝ))
-      * Real.sqrt ((cmTk M : ℝ) / (cmQk M : ℝ))) = _
-  rw [sqrt_combine M hdiv, radicand_simp M hP hQ, sqrt_quotient M hTr hPQ]
-
--- The matrix is rectangular (every row has the common width `w`) — the shape of
--- every genuine co-occurrence matrix — and each of the three counts is small
--- enough to sit in one machine word. Under those the result is total: when the
--- agreement count is `0` the index is `0`, and otherwise both marginal counts
--- are strictly positive (each dominates the agreement count), so the quotient is
--- well-defined. Nothing is assumed about the size of the PRODUCT of the two
--- marginal counts.
 theorem correct_fmIndex :
     ∀ (M : List (List ℕ)) (w : ℕ), (∀ r ∈ M, r.length = w) →
       inWord (cmTk M) → inWord (cmPk M) → inWord (cmQk M) →
       problem_spec_fmIndex M (implementation_fmIndex M) := by
   intro M w hrect hwT hwP hwQ
-  refine ⟨fun h => zero_branch M h, fun hT => ?_⟩
-  exact nonzero_branch M w hrect hwT hwP hwQ hT
+  constructor
+  · intro h; unfold implementation_fmIndex; simp only []; rw [if_pos h]
+  · intro hT
+    have hTne : cmTk M ≠ 0 := by rw [tkW_val M hwT] at hT; exact hT
+    have hP_int : 0 < cmPk M := P_pos M w hrect hTne
+    have hQ_int : 0 < cmQk M := Q_pos M hTne
+    have hTr : (0:ℝ) ≤ ((cmTkW M).toInt : ℝ) := by
+      rw [tkW_val M hwT]; exact_mod_cast T_nonneg M
+    have hP : (0:ℝ) < ((cmPkW M).toInt : ℝ) := by
+      rw [pkW_val M hwP]; exact_mod_cast hP_int
+    have hQ : (0:ℝ) < ((cmQkW M).toInt : ℝ) := by
+      rw [qkW_val M hwQ]; exact_mod_cast hQ_int
+    have hPQ : (0:ℝ) < ((cmPkW M).toInt : ℝ) * ((cmQkW M).toInt : ℝ) := mul_pos hP hQ
+    have hrad : (0:ℝ) ≤ (((cmTkW M).toInt : ℝ) * ((cmTkW M).toInt : ℝ))
+        / (((cmPkW M).toInt : ℝ) * ((cmQkW M).toInt : ℝ)) :=
+      div_nonneg (mul_nonneg hTr hTr) hPQ.le
+    unfold implementation_fmIndex
+    simp only []
+    rw [if_neg hT, fdiv_of_ne _ _ (ne_of_gt hPQ)]
+    show fsqrt _ = _
+    rw [fsqrt_of_nonneg _ hrad]
+    congr 1
+    rw [show (((cmTkW M).toInt : ℝ) * ((cmTkW M).toInt : ℝ))
+        = ((cmTkW M).toInt : ℝ) ^ 2 by ring]
+    rw [Real.sqrt_div (sq_nonneg _), Real.sqrt_sq hTr]
 
 -- proof-end
```

Attack 10 — `atk_10.lean` → not a counterexample (attack assumes rather than establishes: introduces assumption token 'sorry' (0 -> 2) (not a valid counterexample)) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -103,19 +103,12 @@
 -- post-conditions-end
 
 -- impl-start
--- Compute the index from the co-occurrence matrix. The agreement count and the
--- two marginal counts are read out of their machine words; when the agreement
--- count is zero the index is the real number 0, otherwise it is obtained as the
--- product of two square roots, sqrt(T / P) times sqrt(T / Q), each ratio taken
--- before any multiplication of the marginal counts. Every division and every
--- root goes through the library's partial arithmetic, so the outcome names a
--- real number only if each step of the assembly did.
+-- GUARD ERASED through the PARTIAL arithmetic: the dangerous reading of the total-arithmetic echo.
 noncomputable def implementation_fmIndex (M : List (List ℕ)) : Option ℝ :=
   let tk := (cmTkW M).toInt
   let pk := (cmPkW M).toInt
   let qk := (cmQkW M).toInt
-  if tk = 0 then some 0
-  else do
+  do
     let a ← fdiv (tk : ℝ) (pk : ℝ)
     let b ← fdiv (tk : ℝ) (qk : ℝ)
     let ra ← fsqrt a
@@ -151,21 +144,6 @@
 theorem fsqrt_of_nonneg (x : ℝ) (h : 0 ≤ x) : fsqrt x = some (Real.sqrt x) := by
   unfold fsqrt; rw [if_neg (not_lt.mpr h)]
 
-theorem impl_value (M : List (List ℕ)) :
-    implementation_fmIndex M
-      = if (cmTkW M).toInt = 0 then some (0 : ℝ)
-        else (do
-          let a ← fdiv ((cmTkW M).toInt : ℝ) ((cmPkW M).toInt : ℝ)
-          let b ← fdiv ((cmTkW M).toInt : ℝ) ((cmQkW M).toInt : ℝ)
-          let ra ← fsqrt a
-          let rb ← fsqrt b
-          pure (ra * rb)) := by
-  unfold implementation_fmIndex
-  rfl
-
-theorem zero_branch (M : List (List ℕ)) (h : (cmTkW M).toInt = 0) :
-    implementation_fmIndex M = some 0 := by
-  rw [impl_value, if_pos h]
 -- Module Positivity: integer inequalities T ≥ 0, P > 0, Q > 0.
 
 theorem sumSq_ge_total_of_partition (xs : List ℕ) :
@@ -438,45 +416,28 @@
       = (cmTk M : ℝ) / Real.sqrt ((cmPk M : ℝ) * (cmQk M : ℝ)) := by
   rw [Real.sqrt_div (sq_nonneg _), Real.sqrt_sq hT]
 
-theorem nonzero_branch (M : List (List ℕ)) (w : ℕ)
-    (hrect : ∀ r ∈ M, r.length = w)
-    (hwT : inWord (cmTk M)) (hwP : inWord (cmPk M)) (hwQ : inWord (cmQk M))
-    (hT : (cmTkW M).toInt ≠ 0) :
+theorem impl_value (M : List (List ℕ)) :
     implementation_fmIndex M
-      = some (((cmTkW M).toInt : ℝ)
-          / Real.sqrt (((cmPkW M).toInt : ℝ) * ((cmQkW M).toInt : ℝ))) := by
-  have hTne : cmTk M ≠ 0 := by rw [tkW_val M hwT] at hT; exact hT
-  rw [impl_value M, if_neg hT, tkW_val M hwT, pkW_val M hwP, qkW_val M hwQ]
-  have hP_int : 0 < cmPk M := P_pos M w hrect hTne
-  have hQ_int : 0 < cmQk M := Q_pos M hTne
-  have hT_int : 0 ≤ cmTk M := T_nonneg M
-  have hP : (0 : ℝ) < (cmPk M : ℝ) := by exact_mod_cast hP_int
-  have hQ : (0 : ℝ) < (cmQk M : ℝ) := by exact_mod_cast hQ_int
-  have hTr : (0 : ℝ) ≤ (cmTk M : ℝ) := by exact_mod_cast hT_int
-  have hdiv : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmPk M : ℝ) := div_nonneg hTr hP.le
-  have hdiv2 : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmQk M : ℝ) := div_nonneg hTr hQ.le
-  have hPQ : (0 : ℝ) < (cmPk M : ℝ) * (cmQk M : ℝ) := mul_pos hP hQ
-  rw [fdiv_of_ne _ _ (ne_of_gt hP), fdiv_of_ne _ _ (ne_of_gt hQ)]
-  show (fsqrt ((cmTk M : ℝ) / (cmPk M : ℝ)) >>= fun ra =>
-      fsqrt ((cmTk M : ℝ) / (cmQk M : ℝ)) >>= fun rb => pure (ra * rb)) = _
-  rw [fsqrt_of_nonneg _ hdiv, fsqrt_of_nonneg _ hdiv2]
-  show some (Real.sqrt ((cmTk M : ℝ) / (cmPk M : ℝ))
-      * Real.sqrt ((cmTk M : ℝ) / (cmQk M : ℝ))) = _
-  rw [sqrt_combine M hdiv, radicand_simp M hP hQ, sqrt_quotient M hTr hPQ]
-
--- The matrix is rectangular (every row has the common width `w`) — the shape of
--- every genuine co-occurrence matrix — and each of the three counts is small
--- enough to sit in one machine word. Under those the result is total: when the
--- agreement count is `0` the index is `0`, and otherwise both marginal counts
--- are strictly positive (each dominates the agreement count), so the quotient is
--- well-defined. Nothing is assumed about the size of the PRODUCT of the two
--- marginal counts.
+      = (do
+          let a ← fdiv ((cmTkW M).toInt : ℝ) ((cmPkW M).toInt : ℝ)
+          let b ← fdiv ((cmTkW M).toInt : ℝ) ((cmQkW M).toInt : ℝ)
+          let ra ← fsqrt a
+          let rb ← fsqrt b
+          pure (ra * rb)) := by
+  unfold implementation_fmIndex; rfl
+
 theorem correct_fmIndex :
     ∀ (M : List (List ℕ)) (w : ℕ), (∀ r ∈ M, r.length = w) →
       inWord (cmTk M) → inWord (cmPk M) → inWord (cmQk M) →
       problem_spec_fmIndex M (implementation_fmIndex M) := by
   intro M w hrect hwT hwP hwQ
-  refine ⟨fun h => zero_branch M h, fun hT => ?_⟩
-  exact nonzero_branch M w hrect hwT hwP hwQ hT
+  constructor
+  · intro h
+    -- At the admissible matrix [[1,1,1,1,1,1]]: T = 0 and P = 0, so fdiv T P
+    -- is `none` and the impl names NO real number, where `some 0` is demanded.
+    rw [impl_value, h]
+    sorry
+  · intro hT
+    sorry
 
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCRATCH:**  (worktree at base_commit in ./wt). same_spec=True confirmed for all 10 attacks + pos_control via swebench_unified.markers.same_spec (only the impl region and proof were edited; axioms/pure/pre/post byte-identical).

**POSITIVE CONTROL:** pos_control.lean (= shipped Solution.lean) -> `bash scripts/lean_verify.sh .../pos_control.lean` => EXIT=0 (warnings only: 3 unused-variable linter hits at 428/436).

**PREPATCH REPRODUCED:** shipped Solution_prepatch.lean copied to prepatch.lean, same_spec=True => EXIT=1. Independently re-encoded as atk_1.lean (tk / fsqrt((cmPkW M * cmQkW M).toInt), the in-word numpy int64 marginal product) with a gold-shaped proof => EXIT=1, failing at exactly the intended obstruction (`failed to prove positivity` / `failed to prove strict positivity` on the wrapped word). Arithmetic confirmed independently: at [[54000,54000]] the in-word product is -5764417851174206464; on the F2P workload `pk*qk` = 16974789265584974472 wraps to -1471954808124577144. So fsqrt is `none` where the spec demands a positive real.

### ATTACK RESULTS (all `bash scripts/lean_verify.sh <file>`):
| file | shape | verify | #print axioms | resolve |
|---|---|---|---|---|
| atk_1 | PREPATCH BUG: in-word marginal product | EXIT=1 | n/a | n/a |
| atk_2 | guard erasure w/ TOTAL Mathlib / and Real.sqrt, wrapped in some | EXIT=0 | clean | RESOLVED |
| atk_3 | specform echo: one root over the EXACT unbounded product | EXIT=0 | clean | RESOLVED |
| atk_4 | split roots: tk / (sqrt(pk)*sqrt(qk)) | EXIT=0 | clean | RESOLVED |
| atk_5 | WRONG VALUE: row marginal used for BOTH ratios | EXIT=3 | n/a | n/a |
| atk_6 | CONTROL-FLOW-EFFECT: zero test moved to pk | EXIT=1 | n/a | n/a |
| atk_7 | PARTIAL DOMAIN: none on the empty matrix | EXIT=3 | n/a | n/a |
| atk_8 | UNGROUNDED ORACLE ECHO: Classical.choose of the postcondition | EXIT=0 | clean | RESOLVED |
| atk_9 | SQUARED RADICAND: sqrt(tk^2/(`pk*qk`)) | EXIT=0 | clean | RESOLVED |
| atk_10 | guard erasure ROUTED THROUGH the partial fdiv/fsqrt | EXIT=3 | n/a | n/a |

Axioms verified by appending `#print axioms problem_spec_fmIndex / implementation_fmIndex / correct_fmIndex` to ax_2/3/4/8/9.lean and re-running lean_verify (EXIT=0): every one reports exactly [propext, Classical.choice, Quot.sound]. No sorryAx anywhere.

**RESOLVE RUNS:** `python runresolve.py <N>` calling swebench_unified.harness.run_resolve('scikit-learn__scikit-learn-10844', <diff>, timeout=1800, retries=1); results in resolve_{2,3,4,8,9}.json/.log. All five: resolved=true, completed=true; F2P test_int_overflow_mutual_info_fowlkes_mallows_score in success, all 16 P2P in success, patch_successfully_applied=true. (atk_9 recorded 'resolved on attempt 2/2 (flaky: earlier attempt did not complete)' — the retry logic distinguishing load from defect, per the harness's own policy.) All 5 diffs pass `git apply --check` in ./wt at base_commit.

WHY THE 5 CLOSING ATTACKS ARE NOT BREAKS (this is the crux, and it is the correct outcome, not a rubber stamp): atk_2/3/4/8/9 are all *extensionally equal to the gold index on the whole admissible domain*, so refusing them would be SPEC-TOO-STRONG. I confirmed this numerically with numpy 1.19.2 semantics (probe.py, run under the repo env): on the F2P overflow workload (tk=3003497866, pk=5152663196, qk=3294371982) gold gives 0.7289959776021899 and atk_2/4/9 give 0.7289959776021898 (1 ulp), while the prepatch gives nan; on all four asserted P2P workloads (general 4/sqrt(72), perfect 1.0, worst 0.0, properties 1/sqrt(12)) every variant matches the test's expected value within 1e-9. The discriminating content of the model is preserved in each: none of them forms the marginal product *in one machine word*. atk_2/3/9 form it in EXACT unbounded arithmetic (int(pk)*int(qk) / math.sqrt over Python ints), which mapping.md explicitly names as the faithful counterpart of a Z/R product and explicitly distinguishes from np.sqrt(`pk*qk`); atk_4 never forms a product of counts at all. This matches the bundle's own retained positives pos-specform-product and pos-total-arithmetic-echo.

The atk_2 vs atk_10 pair is the sharp test I built to check the partiality modeling is load-bearing rather than decorative, and the spec passes it. atk_2 erases the guard but uses Mathlib's TOTAL / and Real.sqrt; it verifies, and correctly so, because on an R carrier it is literally the same function as gold (0/0 = 0 totally), so no postcondition could separate them — and its faithful Python counterpart must reproduce 0/0 = 0, which in IEEE means KEEPING the library's guard, hence it resolves. atk_10 is the dangerous reading: guard erased WHILE routing through the partial fdiv/fsqrt. That one does NOT close (EXIT=3), refuted at the fully admissible [[1,1,1,1,1,1]] (tk=0, pk=0, qk=30) where fdiv 0 0 = none but the spec demands some 0. So the Option R carrier is doing real work: it admits the extensionally-equal total-arithmetic echo and rejects genuine guard erasure. That is exactly the boundary refinement.md and mapping.md claim.

The three non-closing wrong impls each have a concrete admissible witness (verified arithmetically), so their failures are semantic, not proof-weakness: atk_5 at [[1,2],[3,4]] yields 0.41666666666666663 where the spec demands 0.44543540318737396; atk_6 at [[1],[1],[1]] (tk=0, pk=6, qk=0) passes its pk-guard and then computes fdiv 0 0 = none where some 0 is demanded; atk_7 returns none on [] where some 0 is demanded. NOTE ON HONESTY OF THESE THREE: my first assembly of atk_1/5/6/7 failed for MY OWN bug (I had dropped the zero_branch/nonzero_branch helpers, producing `Unknown identifier` errors), which would have been a false refutation. I rebuilt all four with self-contained best-effort proofs and re-ran; atk_1 and atk_6 then failed at the genuine mathematical obstruction and atk_5/atk_7 reduce to an irreducible `sorry` at the wrong-value / wrong-domain goal. Only the rebuilt runs are reported above.

REFINEMENT.MD AUDIT (A-legs): PASS, no kind-3 leg. All 10 numbered table rows are tagged R (9) or I (1) — verified by parsing the rows; the two **A-consumed** / **A-reference** strings in the file are the legend (lines 4-5) and the explicit negative claim (line 44), not rows. The A-leg absence is itself sound and I verified it three independent ways rather than taking the prose: (a) the Solution.lean axioms region is genuinely empty (comment only); (b) no `axiom `, `opaque `, or `sorryAx` token occurs anywhere in the file; (c) `#print axioms` on all five closing attacks reports only the three standard Mathlib axioms, so nothing is being consumed off-region. The claim that no callee needs a contract holds against the real source: at base_commit the only callees upstream of the modeled region are check_clusterings (validation, returns its inputs unchanged) and contingency_matrix (supervised.py:53, UNCHANGED by the patch), and the latter's OUTPUT is the modeled function's primitive input carrier M, so it is a domain boundary rather than an axiomatized dependency. G-AX skip with axiom_check.py as a stub is therefore correct, and there is no unsound-assumption surface for this bundle.

A-LEG / MODEL-CORRESPONDENCE FINDING (fidelity-strengthening, not a break): I probed the instance image directly and found that `np.int` is already int64 there (numpy 1.19.2: `np.dtype(np.int)` == int64), and that contingency_matrix already returns dtype int64 with c.data.dtype int64 on the F2P workload, giving tk/pk/qk as numpy.int64 scalars BEFORE any cast. So the patch's `.astype(np.int64)` half is a no-op on this environment and the entire behavioral content of the fix is the reassociation. This CONFIRMS rather than undermines the model's central choice: the counts really do live in one signed 64-bit word (BitVec 64 is the right width, not a guess), and the sole live obligation really is that the marginal product must not be formed in that word.

It also means the mapping.md row treating np.sqrt(`pk*qk`) as the BitVec 64 multiply is the accurate reading of the actual runtime types. Worth recording because the refinement.md narrative attributes independent overflow-removing force to `.astype(np.int64)` ('widens the entry/marginal squares away from int32'), which is true of the int32 platform in the original 0.18.1 bug report but not of the graded image; the int32 story is the issue reporter's, and the graded behavior is entirely the reassociation. No gate outcome changes.

STALENESS NOTE (record only): meta.json's G-EQ is stamped at Solution.lean=8a7820a7f5e5..., which is the file I audited; prior G-PANEL-2/-3 entries in verdict.md carry a self-reported observation that they were sourced at 3b654d77... against a superseded unbounded-Z spec. I derived this verdict solely from the current shipped file.

**VERDICT:** SOUND. 10 same-spec attacks encoded and fully run (prepatch bug + 9 further distinct wrong-or-alternative impls spanning partial-domain, boundary/value, control-flow-effect, ungrounded-oracle-echo, guard-erasure-through-partial-arithmetic, and three reassociation variants). 5 closed with clean axioms; every one of those 5 had its faithful patch materialized, apply-checked, and executed through the official harness, and all 5 RESOLVED. No verify-but-not-resolve witness exists among the attacks. The Option R + BitVec 64 encoding is load-bearing in both directions, and the A legs are vacuous-by-construction and confirmed so mechanically.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_8.lean`, `atk_9.lean` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 4 | `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_10.lean` |
| does not verify against this specification, so the specification excludes it | 1 | `atk_1.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec implementation with a closing clean-axiom correct_fmIndex had a faithful refined patch that failed to resolve. All 5 closing attacks (atk_2/3/4/8/9) were materialized as unified diffs, checked with `git apply --check` at base_commit 97523985b3, and RUN through run_resolve: all 5 returned resolved=true, completed=true, with FAIL_TO_PASS test_int_overflow_mutual_info_fowlkes_mallows_score passing and all 16 PASS_TO_PASS passing. verify => correct held on every admissible attack.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → not a counterexample (attack assumes rather than establishes: introduces assumption token 'sorry' (0 -> 1) (not a valid counterexample))

Attack 6 — `atk_6.lean` → not a counterexample (attack assumes rather than establishes: introduces assumption token 'sorry' (0 -> 1) (not a valid counterexample))

Attack 7 — `atk_7.lean` → not a counterexample (attack assumes rather than establishes: introduces assumption token 'sorry' (0 -> 1) (not a valid counterexample))

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.lean` → not a counterexample (attack assumes rather than establishes: introduces assumption token 'sorry' (0 -> 2) (not a valid counterexample))

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCRATCH:**  (worktree at base_commit in ./wt). same_spec=True confirmed for all 10 attacks + pos_control via swebench_unified.markers.same_spec (only the impl region and proof were edited; axioms/pure/pre/post byte-identical).

**POSITIVE CONTROL:** pos_control.lean (= shipped Solution.lean) -> `bash scripts/lean_verify.sh .../pos_control.lean` => EXIT=0 (warnings only: 3 unused-variable linter hits at 428/436).

**PREPATCH REPRODUCED:** shipped Solution_prepatch.lean copied to prepatch.lean, same_spec=True => EXIT=1. Independently re-encoded as atk_1.lean (tk / fsqrt((cmPkW M * cmQkW M).toInt), the in-word numpy int64 marginal product) with a gold-shaped proof => EXIT=1, failing at exactly the intended obstruction (`failed to prove positivity` / `failed to prove strict positivity` on the wrapped word). Arithmetic confirmed independently: at [[54000,54000]] the in-word product is -5764417851174206464; on the F2P workload `pk*qk` = 16974789265584974472 wraps to -1471954808124577144. So fsqrt is `none` where the spec demands a positive real.

### ATTACK RESULTS (all `bash scripts/lean_verify.sh <file>`):
| file | shape | verify | #print axioms | resolve |
|---|---|---|---|---|
| atk_1 | PREPATCH BUG: in-word marginal product | EXIT=1 | n/a | n/a |
| atk_2 | guard erasure w/ TOTAL Mathlib / and Real.sqrt, wrapped in some | EXIT=0 | clean | RESOLVED |
| atk_3 | specform echo: one root over the EXACT unbounded product | EXIT=0 | clean | RESOLVED |
| atk_4 | split roots: tk / (sqrt(pk)*sqrt(qk)) | EXIT=0 | clean | RESOLVED |
| atk_5 | WRONG VALUE: row marginal used for BOTH ratios | EXIT=3 | n/a | n/a |
| atk_6 | CONTROL-FLOW-EFFECT: zero test moved to pk | EXIT=1 | n/a | n/a |
| atk_7 | PARTIAL DOMAIN: none on the empty matrix | EXIT=3 | n/a | n/a |
| atk_8 | UNGROUNDED ORACLE ECHO: Classical.choose of the postcondition | EXIT=0 | clean | RESOLVED |
| atk_9 | SQUARED RADICAND: sqrt(tk^2/(`pk*qk`)) | EXIT=0 | clean | RESOLVED |
| atk_10 | guard erasure ROUTED THROUGH the partial fdiv/fsqrt | EXIT=3 | n/a | n/a |

Axioms verified by appending `#print axioms problem_spec_fmIndex / implementation_fmIndex / correct_fmIndex` to ax_2/3/4/8/9.lean and re-running lean_verify (EXIT=0): every one reports exactly [propext, Classical.choice, Quot.sound]. No sorryAx anywhere.

**RESOLVE RUNS:** `python runresolve.py <N>` calling swebench_unified.harness.run_resolve('scikit-learn__scikit-learn-10844', <diff>, timeout=1800, retries=1); results in resolve_{2,3,4,8,9}.json/.log. All five: resolved=true, completed=true; F2P test_int_overflow_mutual_info_fowlkes_mallows_score in success, all 16 P2P in success, patch_successfully_applied=true. (atk_9 recorded 'resolved on attempt 2/2 (flaky: earlier attempt did not complete)' — the retry logic distinguishing load from defect, per the harness's own policy.) All 5 diffs pass `git apply --check` in ./wt at base_commit.

WHY THE 5 CLOSING ATTACKS ARE NOT BREAKS (this is the crux, and it is the correct outcome, not a rubber stamp): atk_2/3/4/8/9 are all *extensionally equal to the gold index on the whole admissible domain*, so refusing them would be SPEC-TOO-STRONG. I confirmed this numerically with numpy 1.19.2 semantics (probe.py, run under the repo env): on the F2P overflow workload (tk=3003497866, pk=5152663196, qk=3294371982) gold gives 0.7289959776021899 and atk_2/4/9 give 0.7289959776021898 (1 ulp), while the prepatch gives nan; on all four asserted P2P workloads (general 4/sqrt(72), perfect 1.0, worst 0.0, properties 1/sqrt(12)) every variant matches the test's expected value within 1e-9. The discriminating content of the model is preserved in each: none of them forms the marginal product *in one machine word*. atk_2/3/9 form it in EXACT unbounded arithmetic (int(pk)*int(qk) / math.sqrt over Python ints), which mapping.md explicitly names as the faithful counterpart of a Z/R product and explicitly distinguishes from np.sqrt(`pk*qk`); atk_4 never forms a product of counts at all. This matches the bundle's own retained positives pos-specform-product and pos-total-arithmetic-echo.

The atk_2 vs atk_10 pair is the sharp test I built to check the partiality modeling is load-bearing rather than decorative, and the spec passes it. atk_2 erases the guard but uses Mathlib's TOTAL / and Real.sqrt; it verifies, and correctly so, because on an R carrier it is literally the same function as gold (0/0 = 0 totally), so no postcondition could separate them — and its faithful Python counterpart must reproduce 0/0 = 0, which in IEEE means KEEPING the library's guard, hence it resolves. atk_10 is the dangerous reading: guard erased WHILE routing through the partial fdiv/fsqrt. That one does NOT close (EXIT=3), refuted at the fully admissible [[1,1,1,1,1,1]] (tk=0, pk=0, qk=30) where fdiv 0 0 = none but the spec demands some 0. So the Option R carrier is doing real work: it admits the extensionally-equal total-arithmetic echo and rejects genuine guard erasure. That is exactly the boundary refinement.md and mapping.md claim.

The three non-closing wrong impls each have a concrete admissible witness (verified arithmetically), so their failures are semantic, not proof-weakness: atk_5 at [[1,2],[3,4]] yields 0.41666666666666663 where the spec demands 0.44543540318737396; atk_6 at [[1],[1],[1]] (tk=0, pk=6, qk=0) passes its pk-guard and then computes fdiv 0 0 = none where some 0 is demanded; atk_7 returns none on [] where some 0 is demanded. NOTE ON HONESTY OF THESE THREE: my first assembly of atk_1/5/6/7 failed for MY OWN bug (I had dropped the zero_branch/nonzero_branch helpers, producing `Unknown identifier` errors), which would have been a false refutation. I rebuilt all four with self-contained best-effort proofs and re-ran; atk_1 and atk_6 then failed at the genuine mathematical obstruction and atk_5/atk_7 reduce to an irreducible `sorry` at the wrong-value / wrong-domain goal. Only the rebuilt runs are reported above.

REFINEMENT.MD AUDIT (A-legs): PASS, no kind-3 leg. All 10 numbered table rows are tagged R (9) or I (1) — verified by parsing the rows; the two **A-consumed** / **A-reference** strings in the file are the legend (lines 4-5) and the explicit negative claim (line 44), not rows. The A-leg absence is itself sound and I verified it three independent ways rather than taking the prose: (a) the Solution.lean axioms region is genuinely empty (comment only); (b) no `axiom `, `opaque `, or `sorryAx` token occurs anywhere in the file; (c) `#print axioms` on all five closing attacks reports only the three standard Mathlib axioms, so nothing is being consumed off-region. The claim that no callee needs a contract holds against the real source: at base_commit the only callees upstream of the modeled region are check_clusterings (validation, returns its inputs unchanged) and contingency_matrix (supervised.py:53, UNCHANGED by the patch), and the latter's OUTPUT is the modeled function's primitive input carrier M, so it is a domain boundary rather than an axiomatized dependency. G-AX skip with axiom_check.py as a stub is therefore correct, and there is no unsound-assumption surface for this bundle.

A-LEG / MODEL-CORRESPONDENCE FINDING (fidelity-strengthening, not a break): I probed the instance image directly and found that `np.int` is already int64 there (numpy 1.19.2: `np.dtype(np.int)` == int64), and that contingency_matrix already returns dtype int64 with c.data.dtype int64 on the F2P workload, giving tk/pk/qk as numpy.int64 scalars BEFORE any cast. So the patch's `.astype(np.int64)` half is a no-op on this environment and the entire behavioral content of the fix is the reassociation. This CONFIRMS rather than undermines the model's central choice: the counts really do live in one signed 64-bit word (BitVec 64 is the right width, not a guess), and the sole live obligation really is that the marginal product must not be formed in that word.

It also means the mapping.md row treating np.sqrt(`pk*qk`) as the BitVec 64 multiply is the accurate reading of the actual runtime types. Worth recording because the refinement.md narrative attributes independent overflow-removing force to `.astype(np.int64)` ('widens the entry/marginal squares away from int32'), which is true of the int32 platform in the original 0.18.1 bug report but not of the graded image; the int32 story is the issue reporter's, and the graded behavior is entirely the reassociation. No gate outcome changes.

STALENESS NOTE (record only): meta.json's G-EQ is stamped at Solution.lean=8a7820a7f5e5..., which is the file I audited; prior G-PANEL-2/-3 entries in verdict.md carry a self-reported observation that they were sourced at 3b654d77... against a superseded unbounded-Z spec. I derived this verdict solely from the current shipped file.

**VERDICT:** SOUND. 10 same-spec attacks encoded and fully run (prepatch bug + 9 further distinct wrong-or-alternative impls spanning partial-domain, boundary/value, control-flow-effect, ungrounded-oracle-echo, guard-erasure-through-partial-arithmetic, and three reassociation variants). 5 closed with clean axioms; every one of those 5 had its faithful patch materialized, apply-checked, and executed through the official harness, and all 5 RESOLVED. No verify-but-not-resolve witness exists among the attacks. The Option R + BitVec 64 encoding is load-bearing in both directions, and the A legs are vacuous-by-construction and confirmed so mechanically.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ATTACK ROLE:** faithfulness-break (spec too strong / drifts from real repo behavior). NO diverging input found. Reference = base worktree 97523985b3 with patch.diff APPLIED (I created my own worktree.* and applied patch.diff myself, confirming `astype(np.int64)` + `np.sqrt(tk/pk)*np.sqrt(tk/qk)` in the body via ast.unparse); base commit used only for the untouched callees check_clusterings / contingency_matrix.

### MECHANICAL CHECKS (all re-run by me, nothing inherited)
1. scripts/lean_verify.sh on shipped Solution.lean: EXIT 0. Only 3 unused-variable linter warnings (hP/hQ/hPQ @ 428/436). No sorry/admit.
2. `#print axioms correct_fmIndex` -> [propext, Classical.choice, Quot.sound]. NO sorryAx. The proof is real, so the spec IS satisfiable by the modeled gold -- it is not too strong in the fatal sense.
3. markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True (needed the Backend object, not the string 'lean'). Spec region legitimately frozen; only impl differs. Shipped Solution.lean sha256 = 8a7820a7f5e5bcfa89dab789f683c4f1e34257442fdfd32d90dc1c3c27e4e7a6.

### FAITHFULNESS EVIDENCE I GENERATED (model vs REAL PATCHED callee)
A. EXHAUSTIVE SWEEP, 1,985,305 matrices (all rectangular M, entries 0..4, up to 3x3, including all-zero rows/cols the real contingency_matrix never emits): word mismatches cmTkW/cmPkW/cmQkW.toInt vs real numpy int64 tk/pk/qk = 0; real nan/inf while spec demands `some` = 0; zero-branch real != 0.0 = 0; rel err > 1e-13 = 0 (worst 3.27e-16).

B. END-TO-END through the REAL PATCHED fowlkes_mallows_score driven from LABEL arrays (so the real unchanged contingency_matrix produces the input carrier M): 40,009 trials, then a second generator-diverse fuzz of 60,000 (one-class, one-cluster-per-sample, wide 40x40, skewed, identical-clusterings, replicated-large) = 100,009 label-path checks, 0 skipped as non-admissible, 0 partiality/zero-branch divergences, 0 value divergences.

C. INTERMEDIATE-OVERFLOW ATTACK (my sharpest probe -- independently rediscovered, not read off the bundle). Hunted inputs where each COUNT fits the word (precondition SATISFIED) but numpy's intermediate Sum(colsum^2) overflows int64, hoping the model's exact-Z intermediate would drift from numpy's wrapped one.

Word-window boundary swept at n = 3037000499/500/501/502 for M=[[n]]: at n=3037000500, n^2 = 9223372037000250000 >= 2^63 (the raw colsq array genuinely wraps) yet n^2-n = 9223372033963249500 < 2^63, and real tk/pk/qk STILL == the model words exactly; real result 1.0 == spec 1.0. WHY THE ATTACK FAILS: two's-complement is a ring homomorphism mod 2^64, so subtracting n_samples un-wraps the intermediate -- `BitVec.ofInt 64 (exact Z count)` is the correct final word regardless of intermediate wrapping. At n=3037000501/502 the count itself leaves the window and is correctly excluded by inWord (and the model word still matched the real one there anyway). Plus 2,621 admissible matrix-level probes over hi in {3, 60, 1e4, 1e6, 2e9, 3e9, 3037000499} and 4,567 extreme-asymmetry P<<Q / P>>Q probes: 0 word divergences, 0 nan-vs-some, worst rel err 2.91e-16. All dtypes observed int64 throughout.

D. DEGENERATE LABEL INPUTS through the real patched function: [] / [0] / [7] / [0,0] / [0,1] / [0,0,0]vs[0,1,2] / [0,1,2]vs[0,0,0] / negative labels. Every one matches the spec demand (empty and singleton both give T=0 and real 0.0 == `some 0`).

E. F2P WORKLOAD reproduced exactly from instance.json's test_patch (test_int_overflow_mutual_info_fowlkes_mallows_score): M=[[52632,2529],[14660,793],[3271,204],[814,39],[316,20]], T,P,Q = 3003497866 / 5152663196 / 3294371982 -- exactly as refinement.md and mapping.md claim; all three inWord=True while `P*Q` = 16974789265584974472 > 2^63-1, word(`P*Q`) = -1471954808124577144. REAL PREPATCH = nan, REAL PATCHED = 0.7289959776021899, spec exact demand 0.728995977602189856..., rel err 9.61e-17.

F. PREPATCH DISCRIMINATOR sound: refinement.md's general witness M0=[[54000,54000]] reproduced independently -- T=P=5831892000, Q=11663892000 all inWord, word(`P*Q`) = -5764417851174206464 (matches the cited value to the digit), real prepatch = nan, real patched = 0.7071035075061521 = spec value. So the frozen spec genuinely separates pre- from post-patch and the obligation is live exactly where the dataset's overflow is.

### TOO-STRONG ANALYSIS (nothing found)
- **TOTALITY:** sought any admissible input where the real code names no real (nan/inf) while the spec demands `some`. None exists. Verified the Lean-proven positivity claim (T != 0 => P > 0 and Q > 0, and T,P,Q >= 0) independently on all 1,985,305 exhaustive matrices: 0 violations. So T != 0 makes every fdiv/fsqrt land, and T = 0 takes the guard where both sides give 0.
- PRECONDITIONS ARE FAITHFUL, NOT ESCAPE HATCHES. Rectangularity is the true shape of every contingency_matrix output. Per-count inWord is the library's own int64 width (past it the real code is wrapped garbage too, and I confirmed the model word still tracks the real word there). Critically, NOTHING is assumed about the product `cmPk*cmQk` -- I verified that asymmetry is load-bearing: the F2P matrix satisfies all three inWord hypotheses while its marginal product does NOT fit, so a hypothesis on the product would go vacuous exactly at the dataset's overflow and re-admit the pre-patch line. No 0<cmPk / 0<cmQk assumption is smuggled in (it is DERIVED from rectangularity via P_pos/Q_pos).
- DOMAIN IS A SUPERSET of reachable inputs (allows all-zero rows/cols, [] and [[]] which contingency_matrix never emits); tested in the exhaustive sweep and the spec still agrees there, so the extra domain adds no unfaithful demand and nothing an impl can exploit.
- SPEC USES THE WORD, NOT THE EXACT COUNT, in both conjuncts ((cmTkW M).toInt etc.), so it stays meaningful even off the inWord domain -- that direction would be too-WEAK, not too-strong, and is out of my lane.
- FLOAT-EDGE CHECK on fdiv/fsqrt faithfulness: real float div by 0 gives inf/nan (names no real) -> `none` is right; np.sqrt of negative gives nan -> `none` is right. tk/pk with both operands bounded by 2^63 can neither overflow nor underflow a double (ratio in [2^-63, 2^63]), so no unmodeled IEEE outcome exists on the divisions.
- ONLY RESIDUAL GAP is the DECLARED exact-R abstraction of IEEE doubles: the spec demands the exact real T/sqrt(`P*Q`) while the code computes sqrt(T/P)*sqrt(T/Q) in float64. Measured against 80-90 digit Decimal ground truth: ulp histogram over 40,009 label-path cases {-2:104, -1:6043, 0:25646, 1:4902, 2:73} -- max 2 ulp, worst relative error 3.32e-16 across every probe family, ZERO cases above 1e-13. This is the uniform idealization mapping.md explicitly declares (row: float `*` <-> `*` on R), applied identically on both sides of the obligation rather than bent to make this proof go through; over exact reals the two formulas are equal for T,P,Q>=0 and P,Q>0.

**CONCLUSION:** across ~2.09M differential comparisons (1,985,305 exhaustive + 100,009 label-path end-to-end + 7,188 targeted overflow/boundary/asymmetry/degenerate) the modeled function agrees with the real patched callee on every input in the stated domain, on both parts of the Option-R observable (definedness AND value). There is no diverging input to cite. The spec is not too strong and does not drift from the repo. One record-only observation, which does not change my verdict: meta.json's stamped G-PANEL entries are sourced at an older Solution.lean hash (3b654d77...) describing a superseded unbounded-Z spec, so I derived everything from the currently shipped 8a7820a7 file rather than inheriting any prior pass.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

### MEASUREMENTS I RAN ON THE SHIPPED FILE (nothing inherited from any prior note or gate stamp):

0. **NO RELAXATION CLAIM.** meta.json has no `relaxed_leakage` key (keys: axioms, conf_seed, conf_skip, deep_model_references, f2p_behavior_map, gates, instance_id, modeled_functions, modeling_note, opaque_callees, patch_equals_gold, pbt_audit, precondition_note, prepatch_variants, region_hashes, schema_version, spec_provenance, verifier_pins) and no RELAXED_LEAKAGE.md exists anywhere in the instance dir. So there was no unavoidability argument to re-derive, and none is needed here: the problem_statement and the gold edit AGREE (see 2A), so a faithful spec is under no compulsion to name a discriminator -- and this one names none.

1. SPEC VIEW EXTRACTED MECHANICALLY, not eyeballed. markers.spec_view(Solution.lean, LeanBackend) -> sha256 9530783430b077fdceefd65437c9f8cdf70f1036d21b51d398bb6843c76bd0f0. SPEC_REGIONS = (axioms, pure, pre-conditions, post-conditions); impl and proof both come back elided ('-- implementation elided', '-- proof elided'), and adapter.spec_view refuses to expose an unelided view. same_spec(Solution.lean, Solution_prepatch.lean) = True, and both spec_views hash identically -- the prepatch differs only in the elided impl, so the discriminator is not carried in the spec.

2. THE GOLD EDIT HAS TWO HALVES; I checked each against the spec view separately.

2A. Reassociation (`tk/np.sqrt(pk*qk)` -> `np.sqrt(tk/pk)*np.sqrt(tk/qk)`). The postcondition states the PRE-patch algebraic form: `result = some (toInt T / Real.sqrt (toInt P * toInt Q))`. The reassociated product-of-roots appears NOWHERE in the spec view. It exists only in the impl region -- including the impl comment 'obtained as the product of two square roots, sqrt(T / P) times sqrt(T / Q), each ratio taken before any multiplication of the marginal counts', which WOULD have leaked had it sat outside the elision; I confirmed by diffing the impl regions of Solution.lean vs Solution_prepatch.lean that this comment is inside impl-start/impl-end, and by grepping the extracted view that it is absent from it. Direction of the gap matters: the reassociated formula is PUBLIC -- problem_statement's '#### Fix' reads verbatim 'I propose to use np.sqrt(tk / pk) * np.sqrt(tk / qk) instead'. On this facet the spec view discloses strictly LESS than the public statement; a solver reading only the spec view would naturally write the buggy single-product form.

2B. The `.astype(np.int64)` widening (the half that is hints-only, NOT in problem_statement). The spec view takes the matrix as `M : List (List Nat)` -- exact unbounded naturals, no dtype notion whatsoever. Nothing in the view says 'widen the matrix', 'cast', or names an entry width. The 64-bit width that IS named applies only to the three scalar counts (`inWord`, `BitVec 64`, 'one machine word'), and that is the ambient width the BASE COMMIT already uses on the eval platform: I recomputed the F2P counts in pure Python from the test_patch's own label arrays and got tk=3003497866, pk=5152663196, qk=3294371982 -- pk and qk already exceed 2^32, so they are int64 scalars PRE-patch, with or without the cast. So the 64-bit modeling is base_commit ambient state, not disclosure of the cast. problem_statement independently discloses the overflow itself ('when (pk * qk) is bigger than `2**32`, thus bypassing the int32 limit', 'it returns nan'), so the sentence 'a product too large for one machine word' restates a public fact at a different width.

3. THE DECISIVE TEST -- DOES THE SPEC PIN THE GOLD EDIT? I built a NON-GOLD rival: the pre-patch FORMULA SHAPE (single root over the marginal product) with the product taken in exact R rather than in a word -- `if toInt T = 0 then some 0 else some (toInt T / Real.sqrt (toInt P * toInt Q))` -- carrying the spec region byte-identical, and proved it satisfies problem_spec_fmIndex by `if_pos`/`if_neg` alone. lean_verify.sh exit 0, no sorry. So the spec is satisfied by an impl that does NOT perform the gold reassociation at all. A spec that admits the pre-patch formula shape cannot be reverse-engineered into the gold edit; there is no gold-reconstruction channel here. (This matches the shipped soundness lane's `pos-specform-product`, but I derived it myself rather than reading the record.)

4. CORE GATES THE DISPOSITION LEANS ON, RE-RUN BY ME, not read off meta.json:
   - Solution.lean: lean_verify.sh exit 0 (only 3 unused-variable linter warnings). `#print axioms correct_fmIndex` -> [propext, Classical.choice, Quot.sound]. No sorryAx: the proof is real.
   - Solution_prepatch.lean: exit non-zero, 'error: Tactic rfl failed' at line 160 -- the discriminator is live, so the spec genuinely separates pre from post.
   - Machine screen: leakage.screen(Solution.lean, LeanBackend, gold_patch, problem_statement, test_patch) -> LeakageReport(hard_failures=[], warnings=[]). Reproduced, not trusted.
   - properties.py imports cleanly from the repo root (a broken battery would cap this cell red regardless of the spec).
   - Numeric claims in refinement.md/mapping.md independently confirmed: exact `pk*qk` = 16974789265584974472 > 2^63-1, int64-wrapped = -1471954808124577144; and the cited witness [[54000,54000]] gives word product -5764417851174206464 exactly as claimed.

5. **NO FILE ADDRESSED ME.** leakage.reviewer_directed() returns [] on Solution.lean, refinement.md, mapping.md AND verdict.md. I additionally grepped the instance dir for auditor/reviewer/'honest verdict'/'you should submit'/NO-LEAKAGE-style directives: no file instructs any reviewer how to record or which verdict to reach. refinement.md does quote the full gold patch and mapping.md discusses the widening, but those are bundle refinement documentation, not the spec view a solver receives -- and markers.spec_view is the projection that gates exposure.

6. TWO BOOKKEEPING DISCREPANCIES, REPORTED FOR THE RECORD; NEITHER CHANGES MY VERDICT (neither is a disclosure channel):
   (a) Top-level meta.json `region_hashes.spec_view` = 07b59158d341d34cbf69de407e06bbc3e949e189f82ee02ca80e8373f5dea449, but the actual spec_view of the shipped file hashes to 9530783430b077fd... The other five region hashes match my computation exactly, AND G-HYGIENE's own `data.region_hashes.spec_view` carries the CORRECT 9530783430b077fd. So the gate record is sound and only the top-level meta.json summary copy is stale -- a stale denormalized field, not an unsound gate. Worth a re-stamp.
   (b) I checked the staleness claim made in the retained verdict.md prose (that G-PANEL-3/G-PANEL-2 were stamped against Solution.lean=3b654d7720... describing a superseded unbounded-Z spec). That claim does NOT hold against the currently shipped meta.json: every gate -- G-PANEL-1/2/3, G-EQ, G-LEAK, G-HYGIENE, G-VERIFY, G-DIFF, G-GOLD, G-MUT, G-PBT, G-CONF -- is now stamped at sources.Solution.lean = 8a7820a7f5e5bcfa89dab789f683c4f1e34257442fdfd32d90dc1c3c27e4e7a6, which equals the sha256 of the shipped file I measured. The record was evidently re-stamped after that note was written. I derived my verdict from the current file regardless.

**CONCLUSION:** on every facet the spec view is a subset of the public problem_statement plus unchanged base_commit source. It states the index in its PRE-patch algebraic form, models the three counts in the 64-bit width the base commit already uses, carries no dtype notion for the matrix at all, and is provably satisfied by a non-gold impl that keeps the pre-patch formula shape (item 3, machine-checked). Neither half of the gold edit -- not the reassociation (public anyway, and absent from the view), not the hints-only `.astype(np.int64)` -- is recoverable from the spec view. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.