# P2 adversarial audit — sympy__sympy-18199

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean`, `atk_10.lean`, `atk_11.lean`, `atk_13.lean`, `atk_14.lean`, `atk_16.lean`, `atk_18.lean`, `prepatch_strict.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_1.lean`, `atk_2.lean`, `atk_15.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. All three attacks whose proofs CLOSE with clean axioms (atk_1, atk_2, atk_15) were carried back to faithful refined patches and RUN through the official harness: ALL THREE RESOLVE (resolved=true, completed=true, attempts=1, flaky=false). They are correct off-regime echoes, not counterexamples to verify=>correct. Root cause, measured not argued: I source-instrumented the patched nthroot_mod at its entry and ran the ENTIRE graded surface (F2P test_solve_modular + all 113 P2P, all in test_solveset.py). Only 8 distinct (a,n,m,all_roots) tuples ever reach it: (1,3,2),(1,3,8),(13,4,17),(3,4,7),(4,4,3),(4,4,9),(5,4,7),(9,2,160) - all with all_roots=True. At EVERY ONE the spec pins the result EXACTLY: the five prime moduli fall under clause 2/3 (=[0] or =primeUnitRoots), and the three non-single-prime ones (8, 9, 160) ALL have dispatchValidated=true, so clause 5 (result = rootSetIn) applies. m=8 and m=9 are non-squarefree but satisfy modulusRegularLift; m=160 is non-squarefree and NOT regular but has n==2. So no graded input lands in the count-only sub-domain, and the off-regime freedom the count-level ceiling leaves is unreachable by graded behaviour. atk_14 tried to exploit this directly by special-casing moduli 8 and 9 and was REJECTED, with Lean demanding exactly 'm = 8 or m = 9 -> atkDev a n m = rootSetIn a n m'.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,14 +147,55 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Assemble the roots for a modulus that is not a single prime. The real routine
-factors the modulus, lifts each prime root through successive prime powers (the
-unit-derivative branch via the modular inverse; the singular branch by walking the
-residue orbit) and recombines one residue per component by CRT. Over the regime
-this assembly delivers exactly the complete in-range root set, so it is modelled
-deeply by that set. -/
-def implementation_nthrootModComposite (a n m : ℤ) : List ℤ := Id.run do
-  return rootSetIn a n m
+/-- Length bound: the grounded root set is a sublist of the canonical range. -/
+theorem atk_len_le (a n m : ℤ) : (rootSetIn a n m).length ≤ m.toNat := by
+  have h : (rootSetIn a n m).length ≤ (((List.range m.toNat).map (Int.ofNat))).length := by
+    apply List.Sublist.length_le
+    unfold rootSetIn
+    exact List.filter_sublist
+  simpa using h
+
+theorem atk_range_sorted (m : ℤ) :
+    (((List.range m.toNat).map (Int.ofNat))).Pairwise (· < ·) := by
+  rw [List.pairwise_map]
+  exact (List.pairwise_lt_range).imp (fun h => Int.ofNat_lt.mpr h)
+
+theorem atk_range_mem {m x : ℤ} (hm : 0 < m)
+    (hx : x ∈ ((List.range m.toNat).map (Int.ofNat))) : 0 ≤ x ∧ x < m := by
+  simp only [List.mem_map, List.mem_range] at hx
+  obtain ⟨k, hk, rfl⟩ := hx
+  refine ⟨Int.natCast_nonneg k, ?_⟩
+  have hmm : Int.ofNat m.toNat = m := Int.toNat_of_nonneg (le_of_lt hm)
+  have h1 : (Int.ofNat k) < (Int.ofNat m.toNat) := Int.ofNat_lt.mpr hk
+  rw [hmm] at h1
+  exact h1
+
+/-- The off-regime relabeling: the first `k` canonical residues, `k` the number of solutions. -/
+def atkDev (a n m : ℤ) : List ℤ :=
+  ((List.range m.toNat).map (Int.ofNat)).take (rootSetIn a n m).length
+
+theorem atkDev_sub (a n m : ℤ) :
+    (atkDev a n m).Sublist ((List.range m.toNat).map (Int.ofNat)) := by
+  unfold atkDev
+  exact List.take_sublist _ _
+
+theorem atkDev_mem {a n m x : ℤ} (hm : 0 < m) (hx : x ∈ atkDev a n m) :
+    0 ≤ x ∧ x < m := atk_range_mem hm ((atkDev_sub a n m).mem hx)
+
+theorem atkDev_sorted (a n m : ℤ) : (atkDev a n m).Pairwise (· < ·) :=
+  (atk_range_sorted m).sublist (atkDev_sub a n m)
+
+theorem atkDev_length (a n m : ℤ) :
+    (atkDev a n m).length = (rootSetIn a n m).length := by
+  unfold atkDev
+  rw [List.length_take, List.length_map, List.length_range]
+  exact min_eq_left (atk_len_le a n m)
+
+/-- Assemble the roots for a modulus that is not a single prime. Inside the
+validated regime the assembly delivers the complete in-range root set; outside it
+the report is a count-preserving relabeling. -/
+def implementation_nthrootModComposite (a n m : ℤ) : List ℤ :=
+  if dispatchValidated a n m then rootSetIn a n m else atkDev a n m
 -- impl-end
 
 -- proof-start
@@ -163,12 +204,15 @@
       compositeValidated a n m = true →
       problem_spec_nthrootModComposite a n m
         (implementation_nthrootModComposite a n m) := by
-  intro a n m _ _ hm _ _
+  intro a n m _ _ hm _ hcv
+  have hdv : dispatchValidated a n m = true := by
+    simp [dispatchValidated, hcv]
+  have he : implementation_nthrootModComposite a n m = rootSetIn a n m := by
+    simp [implementation_nthrootModComposite, hdv]
+  rw [he]
   refine ⟨rfl, ?_⟩
   intro x hx
-  have hx' : x ∈ rootSetIn a n m := by
-    simpa [implementation_nthrootModComposite, Id.run] using hx
-  exact (mem_rootSetIn (by omega)).1 hx'
+  exact (mem_rootSetIn (by omega)).1 hx
 -- proof-end
 
 -- post-conditions-start
@@ -216,13 +260,12 @@
   have himpl : implementation_nthrootMod a n p =
       (if modulusIsPrime p = true then
         (if a % p = 0 then [0] else primeUnitRoots a n p)
-       else rootSetIn a n p) := by
-    unfold implementation_nthrootMod implementation_nthrootModComposite
+       else implementation_nthrootModComposite a n p) := by
+    unfold implementation_nthrootMod
     by_cases hpr : modulusIsPrime p = true <;>
       by_cases haz : a % p = 0 <;>
       simp only [Id.run, hpr, haz, Bool.not_true, Bool.not_false, beq_iff_eq,
         if_true, if_false] <;> rfl
-  -- helper: membership of `[0]` gives an in-range root when `a % p = 0`
   have hzero : ∀ x ∈ ([0] : List ℤ), a % p = 0 → isRootIn a n p x := by
     intro x hx haz
     simp only [List.mem_singleton] at hx
@@ -235,8 +278,7 @@
     rw [hz, zero_sub]
     exact Int.emod_eq_zero_of_dvd (dvd_neg.mpr hdvd)
   refine ⟨?_, ?_, ?_, ?_, ?_⟩
-  · -- soundness wherever the report is pinned
-    intro _ x hx
+  · intro hdisj x hx
     rw [himpl] at hx
     by_cases hpr : modulusIsPrime p = true
     · simp only [hpr, if_true] at hx
@@ -245,19 +287,35 @@
         exact hzero x hx haz
       · simp only [haz, if_false] at hx
         exact primeUnitRoots_sound a n p x ha hn hp hpr hx
-    · simp only [hpr] at hx
+    · simp only [hpr, if_false] at hx
+      have hdv : dispatchValidated a n p = true := by
+        rcases hdisj with h | h
+        · exact absurd h hpr
+        · exact h
+      have he : implementation_nthrootModComposite a n p = rootSetIn a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [he] at hx
       exact (mem_rootSetIn (by omega)).1 hx
   · intro hpr haz; rw [himpl]; simp [hpr, haz]
   · intro hpr haz; rw [himpl]; simp [hpr, haz]
-  · -- the unconditional non-single-prime report obligations
-    intro hpr
-    have he : implementation_nthrootMod a n p = rootSetIn a n p := by
+  · intro hpr
+    have he : implementation_nthrootMod a n p = implementation_nthrootModComposite a n p := by
       rw [himpl]; simp [hpr]
-    refine ⟨?_, ?_, ?_⟩
-    · intro x hx
-      rw [he] at hx
+    rw [he]
+    by_cases hdv : dispatchValidated a n p = true
+    · have h2 : implementation_nthrootModComposite a n p = rootSetIn a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [h2]
+      refine ⟨?_, sorted_rootSetIn a n p, rfl⟩
+      intro x hx
       exact ⟨((mem_rootSetIn (by omega)).1 hx).1, ((mem_rootSetIn (by omega)).1 hx).2.1⟩
-    · rw [he]; exact sorted_rootSetIn a n p
-    · rw [he]
-  · intro hpr _; rw [himpl]; simp [hpr]
+    · have h2 : implementation_nthrootModComposite a n p = atkDev a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [h2]
+      exact ⟨fun x hx => atkDev_mem (by omega) hx, atkDev_sorted a n p,
+        atkDev_length a n p⟩
+  · intro hpr hdv
+    rw [himpl]
+    simp only [hpr, if_false]
+    simp [implementation_nthrootModComposite, hdv]
 -- proof-end
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,14 +147,56 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Assemble the roots for a modulus that is not a single prime. The real routine
-factors the modulus, lifts each prime root through successive prime powers (the
-unit-derivative branch via the modular inverse; the singular branch by walking the
-residue orbit) and recombines one residue per component by CRT. Over the regime
-this assembly delivers exactly the complete in-range root set, so it is modelled
-deeply by that set. -/
-def implementation_nthrootModComposite (a n m : ℤ) : List ℤ := Id.run do
-  return rootSetIn a n m
+/-- Length bound: the grounded root set is a sublist of the canonical range. -/
+theorem atk_len_le (a n m : ℤ) : (rootSetIn a n m).length ≤ m.toNat := by
+  have h : (rootSetIn a n m).length ≤ (((List.range m.toNat).map (Int.ofNat))).length := by
+    apply List.Sublist.length_le
+    unfold rootSetIn
+    exact List.filter_sublist
+  simpa using h
+
+theorem atk_range_sorted (m : ℤ) :
+    (((List.range m.toNat).map (Int.ofNat))).Pairwise (· < ·) := by
+  rw [List.pairwise_map]
+  exact (List.pairwise_lt_range).imp (fun h => Int.ofNat_lt.mpr h)
+
+theorem atk_range_mem {m x : ℤ} (hm : 0 < m)
+    (hx : x ∈ ((List.range m.toNat).map (Int.ofNat))) : 0 ≤ x ∧ x < m := by
+  simp only [List.mem_map, List.mem_range] at hx
+  obtain ⟨k, hk, rfl⟩ := hx
+  refine ⟨Int.natCast_nonneg k, ?_⟩
+  have hmm : Int.ofNat m.toNat = m := Int.toNat_of_nonneg (le_of_lt hm)
+  have h1 : (Int.ofNat k) < (Int.ofNat m.toNat) := Int.ofNat_lt.mpr hk
+  rw [hmm] at h1
+  exact h1
+
+/-- The off-regime relabeling: the top `k` canonical residues, `k` the number of solutions. -/
+def atkDev (a n m : ℤ) : List ℤ :=
+  ((List.range m.toNat).map (Int.ofNat)).drop (m.toNat - (rootSetIn a n m).length)
+
+theorem atkDev_sub (a n m : ℤ) :
+    (atkDev a n m).Sublist ((List.range m.toNat).map (Int.ofNat)) := by
+  unfold atkDev
+  exact List.drop_sublist _ _
+
+theorem atkDev_mem {a n m x : ℤ} (hm : 0 < m) (hx : x ∈ atkDev a n m) :
+    0 ≤ x ∧ x < m := atk_range_mem hm ((atkDev_sub a n m).mem hx)
+
+theorem atkDev_sorted (a n m : ℤ) : (atkDev a n m).Pairwise (· < ·) :=
+  (atk_range_sorted m).sublist (atkDev_sub a n m)
+
+theorem atkDev_length (a n m : ℤ) :
+    (atkDev a n m).length = (rootSetIn a n m).length := by
+  unfold atkDev
+  rw [List.length_drop, List.length_map, List.length_range]
+  have h := atk_len_le a n m
+  omega
+
+/-- Assemble the roots for a modulus that is not a single prime. Inside the
+validated regime the assembly delivers the complete in-range root set; outside it
+the report is a count-preserving relabeling. -/
+def implementation_nthrootModComposite (a n m : ℤ) : List ℤ :=
+  if dispatchValidated a n m then rootSetIn a n m else atkDev a n m
 -- impl-end
 
 -- proof-start
@@ -163,12 +205,15 @@
       compositeValidated a n m = true →
       problem_spec_nthrootModComposite a n m
         (implementation_nthrootModComposite a n m) := by
-  intro a n m _ _ hm _ _
+  intro a n m _ _ hm _ hcv
+  have hdv : dispatchValidated a n m = true := by
+    simp [dispatchValidated, hcv]
+  have he : implementation_nthrootModComposite a n m = rootSetIn a n m := by
+    simp [implementation_nthrootModComposite, hdv]
+  rw [he]
   refine ⟨rfl, ?_⟩
   intro x hx
-  have hx' : x ∈ rootSetIn a n m := by
-    simpa [implementation_nthrootModComposite, Id.run] using hx
-  exact (mem_rootSetIn (by omega)).1 hx'
+  exact (mem_rootSetIn (by omega)).1 hx
 -- proof-end
 
 -- post-conditions-start
@@ -216,13 +261,12 @@
   have himpl : implementation_nthrootMod a n p =
       (if modulusIsPrime p = true then
         (if a % p = 0 then [0] else primeUnitRoots a n p)
-       else rootSetIn a n p) := by
-    unfold implementation_nthrootMod implementation_nthrootModComposite
+       else implementation_nthrootModComposite a n p) := by
+    unfold implementation_nthrootMod
     by_cases hpr : modulusIsPrime p = true <;>
       by_cases haz : a % p = 0 <;>
       simp only [Id.run, hpr, haz, Bool.not_true, Bool.not_false, beq_iff_eq,
         if_true, if_false] <;> rfl
-  -- helper: membership of `[0]` gives an in-range root when `a % p = 0`
   have hzero : ∀ x ∈ ([0] : List ℤ), a % p = 0 → isRootIn a n p x := by
     intro x hx haz
     simp only [List.mem_singleton] at hx
@@ -235,8 +279,7 @@
     rw [hz, zero_sub]
     exact Int.emod_eq_zero_of_dvd (dvd_neg.mpr hdvd)
   refine ⟨?_, ?_, ?_, ?_, ?_⟩
-  · -- soundness wherever the report is pinned
-    intro _ x hx
+  · intro hdisj x hx
     rw [himpl] at hx
     by_cases hpr : modulusIsPrime p = true
     · simp only [hpr, if_true] at hx
@@ -245,19 +288,35 @@
         exact hzero x hx haz
       · simp only [haz, if_false] at hx
         exact primeUnitRoots_sound a n p x ha hn hp hpr hx
-    · simp only [hpr] at hx
+    · simp only [hpr, if_false] at hx
+      have hdv : dispatchValidated a n p = true := by
+        rcases hdisj with h | h
+        · exact absurd h hpr
+        · exact h
+      have he : implementation_nthrootModComposite a n p = rootSetIn a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [he] at hx
       exact (mem_rootSetIn (by omega)).1 hx
   · intro hpr haz; rw [himpl]; simp [hpr, haz]
   · intro hpr haz; rw [himpl]; simp [hpr, haz]
-  · -- the unconditional non-single-prime report obligations
-    intro hpr
-    have he : implementation_nthrootMod a n p = rootSetIn a n p := by
+  · intro hpr
+    have he : implementation_nthrootMod a n p = implementation_nthrootModComposite a n p := by
       rw [himpl]; simp [hpr]
-    refine ⟨?_, ?_, ?_⟩
-    · intro x hx
-      rw [he] at hx
+    rw [he]
+    by_cases hdv : dispatchValidated a n p = true
+    · have h2 : implementation_nthrootModComposite a n p = rootSetIn a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [h2]
+      refine ⟨?_, sorted_rootSetIn a n p, rfl⟩
+      intro x hx
       exact ⟨((mem_rootSetIn (by omega)).1 hx).1, ((mem_rootSetIn (by omega)).1 hx).2.1⟩
-    · rw [he]; exact sorted_rootSetIn a n p
-    · rw [he]
-  · intro hpr _; rw [himpl]; simp [hpr]
+    · have h2 : implementation_nthrootModComposite a n p = atkDev a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [h2]
+      exact ⟨fun x hx => atkDev_mem (by omega) hx, atkDev_sorted a n p,
+        atkDev_length a n p⟩
+  · intro hpr hdv
+    rw [himpl]
+    simp only [hpr, if_false]
+    simp [implementation_nthrootModComposite, hdv]
 -- proof-end
```

Attack 3 — `atk_15.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,14 +147,55 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Assemble the roots for a modulus that is not a single prime. The real routine
-factors the modulus, lifts each prime root through successive prime powers (the
-unit-derivative branch via the modular inverse; the singular branch by walking the
-residue orbit) and recombines one residue per component by CRT. Over the regime
-this assembly delivers exactly the complete in-range root set, so it is modelled
-deeply by that set. -/
-def implementation_nthrootModComposite (a n m : ℤ) : List ℤ := Id.run do
-  return rootSetIn a n m
+/-- Length bound: the grounded root set is a sublist of the canonical range. -/
+theorem atk_len_le (a n m : ℤ) : (rootSetIn a n m).length ≤ m.toNat := by
+  have h : (rootSetIn a n m).length ≤ (((List.range m.toNat).map (Int.ofNat))).length := by
+    apply List.Sublist.length_le
+    unfold rootSetIn
+    exact List.filter_sublist
+  simpa using h
+
+theorem atk_range_sorted (m : ℤ) :
+    (((List.range m.toNat).map (Int.ofNat))).Pairwise (· < ·) := by
+  rw [List.pairwise_map]
+  exact (List.pairwise_lt_range).imp (fun h => Int.ofNat_lt.mpr h)
+
+theorem atk_range_mem {m x : ℤ} (hm : 0 < m)
+    (hx : x ∈ ((List.range m.toNat).map (Int.ofNat))) : 0 ≤ x ∧ x < m := by
+  simp only [List.mem_map, List.mem_range] at hx
+  obtain ⟨k, hk, rfl⟩ := hx
+  refine ⟨Int.natCast_nonneg k, ?_⟩
+  have hmm : Int.ofNat m.toNat = m := Int.toNat_of_nonneg (le_of_lt hm)
+  have h1 : (Int.ofNat k) < (Int.ofNat m.toNat) := Int.ofNat_lt.mpr hk
+  rw [hmm] at h1
+  exact h1
+
+/-- The off-regime relabeling: the first `k` canonical residues. -/
+def atkDev (a n m : ℤ) : List ℤ :=
+  ((List.range m.toNat).map (Int.ofNat)).take (rootSetIn a n m).length
+
+theorem atkDev_sub (a n m : ℤ) :
+    (atkDev a n m).Sublist ((List.range m.toNat).map (Int.ofNat)) := by
+  unfold atkDev
+  exact List.take_sublist _ _
+
+theorem atkDev_mem {a n m x : ℤ} (hm : 0 < m) (hx : x ∈ atkDev a n m) :
+    0 ≤ x ∧ x < m := atk_range_mem hm ((atkDev_sub a n m).mem hx)
+
+theorem atkDev_sorted (a n m : ℤ) : (atkDev a n m).Pairwise (· < ·) :=
+  (atk_range_sorted m).sublist (atkDev_sub a n m)
+
+theorem atkDev_length (a n m : ℤ) :
+    (atkDev a n m).length = (rootSetIn a n m).length := by
+  unfold atkDev
+  rw [List.length_take, List.length_map, List.length_range]
+  exact min_eq_left (atk_len_le a n m)
+
+/-- Assemble the roots for a modulus that is not a single prime; outside the
+arithmetic regime on the repeated prime factors the report is a count-preserving
+relabeling. -/
+def implementation_nthrootModComposite (a n m : ℤ) : List ℤ :=
+  if compositeValidated a n m then rootSetIn a n m else atkDev a n m
 -- impl-end
 
 -- proof-start
@@ -163,12 +204,13 @@
       compositeValidated a n m = true →
       problem_spec_nthrootModComposite a n m
         (implementation_nthrootModComposite a n m) := by
-  intro a n m _ _ hm _ _
+  intro a n m _ _ hm _ hcv
+  have he : implementation_nthrootModComposite a n m = rootSetIn a n m := by
+    simp [implementation_nthrootModComposite, hcv]
+  rw [he]
   refine ⟨rfl, ?_⟩
   intro x hx
-  have hx' : x ∈ rootSetIn a n m := by
-    simpa [implementation_nthrootModComposite, Id.run] using hx
-  exact (mem_rootSetIn (by omega)).1 hx'
+  exact (mem_rootSetIn (by omega)).1 hx
 -- proof-end
 
 -- post-conditions-start
@@ -195,12 +237,11 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The public root finder. For a non-single-prime modulus, defer to the
-component-wise assembly. For a single prime: if the right-hand side is divisible
-by the prime then `0` is a root and is reported; otherwise the base residue is a
-unit and the standard prime-modulus algorithm applies. -/
+/-- The public root finder. The exponent-two case is handled directly. -/
 def implementation_nthrootMod (a n p : ℤ) : List ℤ := Id.run do
   if !(modulusIsPrime p) then
+    if n == 2 then
+      return rootSetIn a n p
     return implementation_nthrootModComposite a n p
   if a % p == 0 then
     return [0]
@@ -216,13 +257,14 @@
   have himpl : implementation_nthrootMod a n p =
       (if modulusIsPrime p = true then
         (if a % p = 0 then [0] else primeUnitRoots a n p)
-       else rootSetIn a n p) := by
-    unfold implementation_nthrootMod implementation_nthrootModComposite
+       else if n = 2 then rootSetIn a n p
+       else implementation_nthrootModComposite a n p) := by
+    unfold implementation_nthrootMod
     by_cases hpr : modulusIsPrime p = true <;>
+      by_cases hn2 : n = 2 <;>
       by_cases haz : a % p = 0 <;>
-      simp only [Id.run, hpr, haz, Bool.not_true, Bool.not_false, beq_iff_eq,
+      simp only [Id.run, hpr, hn2, haz, Bool.not_true, Bool.not_false, beq_iff_eq,
         if_true, if_false] <;> rfl
-  -- helper: membership of `[0]` gives an in-range root when `a % p = 0`
   have hzero : ∀ x ∈ ([0] : List ℤ), a % p = 0 → isRootIn a n p x := by
     intro x hx haz
     simp only [List.mem_singleton] at hx
@@ -234,30 +276,72 @@
     have hdvd : p ∣ a := Int.dvd_of_emod_eq_zero haz
     rw [hz, zero_sub]
     exact Int.emod_eq_zero_of_dvd (dvd_neg.mpr hdvd)
+  -- the non-prime branch value, split on n = 2 and on the composite regime
+  have hnp : ∀ (hpr : modulusIsPrime p ≠ true),
+      implementation_nthrootMod a n p =
+        (if n = 2 then rootSetIn a n p
+         else if compositeValidated a n p then rootSetIn a n p else atkDev a n p) := by
+    intro hpr
+    rw [himpl]
+    simp only [hpr, if_false]
+    by_cases hn2 : n = 2
+    · simp [hn2]
+    · simp only [hn2, if_false]
+      by_cases hcv : compositeValidated a n p = true
+      · simp [implementation_nthrootModComposite, hcv]
+      · simp [implementation_nthrootModComposite, hcv]
   refine ⟨?_, ?_, ?_, ?_, ?_⟩
-  · -- soundness wherever the report is pinned
-    intro _ x hx
-    rw [himpl] at hx
+  · intro hdisj x hx
     by_cases hpr : modulusIsPrime p = true
-    · simp only [hpr, if_true] at hx
+    · rw [himpl] at hx
+      simp only [hpr, if_true] at hx
       by_cases haz : a % p = 0
-      · simp only [haz, if_true] at hx
-        exact hzero x hx haz
+      · simp only [haz, if_true] at hx; exact hzero x hx haz
       · simp only [haz, if_false] at hx
         exact primeUnitRoots_sound a n p x ha hn hp hpr hx
-    · simp only [hpr] at hx
-      exact (mem_rootSetIn (by omega)).1 hx
+    · rw [hnp hpr] at hx
+      have hdv : dispatchValidated a n p = true := by
+        rcases hdisj with h | h
+        · exact absurd h hpr
+        · exact h
+      by_cases hn2 : n = 2
+      · rw [if_pos hn2] at hx
+        exact (mem_rootSetIn (by omega)).1 hx
+      · simp only [hn2, if_false] at hx
+        have hcv : compositeValidated a n p = true := by
+          simp only [dispatchValidated, Bool.or_eq_true, beq_iff_eq] at hdv
+          rcases hdv with h | h
+          · exact absurd h hn2
+          · exact h
+        simp only [hcv, if_true] at hx
+        exact (mem_rootSetIn (by omega)).1 hx
   · intro hpr haz; rw [himpl]; simp [hpr, haz]
   · intro hpr haz; rw [himpl]; simp [hpr, haz]
-  · -- the unconditional non-single-prime report obligations
-    intro hpr
-    have he : implementation_nthrootMod a n p = rootSetIn a n p := by
-      rw [himpl]; simp [hpr]
-    refine ⟨?_, ?_, ?_⟩
-    · intro x hx
-      rw [he] at hx
+  · intro hpr
+    rw [hnp hpr]
+    by_cases hn2 : n = 2
+    · rw [if_pos hn2]
+      refine ⟨?_, sorted_rootSetIn a n p, rfl⟩
+      intro x hx
       exact ⟨((mem_rootSetIn (by omega)).1 hx).1, ((mem_rootSetIn (by omega)).1 hx).2.1⟩
-    · rw [he]; exact sorted_rootSetIn a n p
-    · rw [he]
-  · intro hpr _; rw [himpl]; simp [hpr]
+    · simp only [hn2, if_false]
+      by_cases hcv : compositeValidated a n p = true
+      · simp only [hcv, if_true]
+        refine ⟨?_, sorted_rootSetIn a n p, rfl⟩
+        intro x hx
+        exact ⟨((mem_rootSetIn (by omega)).1 hx).1, ((mem_rootSetIn (by omega)).1 hx).2.1⟩
+      · simp only [hcv, if_false]
+        exact ⟨fun x hx => atkDev_mem (by omega) hx, atkDev_sorted a n p,
+          atkDev_length a n p⟩
+  · intro hpr hdv
+    rw [hnp hpr]
+    by_cases hn2 : n = 2
+    · rw [if_pos hn2]
+    · simp only [hn2, if_false]
+      have hcv : compositeValidated a n p = true := by
+        simp only [dispatchValidated, Bool.or_eq_true, beq_iff_eq] at hdv
+        rcases hdv with h | h
+        · exact absurd h hn2
+        · exact h
+      simp [hcv]
 -- proof-end
```

Attack 4 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,14 +147,11 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Assemble the roots for a modulus that is not a single prime. The real routine
-factors the modulus, lifts each prime root through successive prime powers (the
-unit-derivative branch via the modular inverse; the singular branch by walking the
-residue orbit) and recombines one residue per component by CRT. Over the regime
-this assembly delivers exactly the complete in-range root set, so it is modelled
-deeply by that set. -/
-def implementation_nthrootModComposite (a n m : ℤ) : List ℤ := Id.run do
-  return rootSetIn a n m
+/-- Partial domain: nothing is reported off the validated regime.
+
+Assemble the roots for a modulus that is not a single prime. -/
+def implementation_nthrootModComposite (a n m : ℤ) : List ℤ :=
+  if dispatchValidated a n m then rootSetIn a n m else ([] : List ℤ)
 -- impl-end
 
 -- proof-start
@@ -163,12 +160,15 @@
       compositeValidated a n m = true →
       problem_spec_nthrootModComposite a n m
         (implementation_nthrootModComposite a n m) := by
-  intro a n m _ _ hm _ _
+  intro a n m _ _ hm _ hcv
+  have hdv : dispatchValidated a n m = true := by
+    simp [dispatchValidated, hcv]
+  have he : implementation_nthrootModComposite a n m = rootSetIn a n m := by
+    simp [implementation_nthrootModComposite, hdv]
+  rw [he]
   refine ⟨rfl, ?_⟩
   intro x hx
-  have hx' : x ∈ rootSetIn a n m := by
-    simpa [implementation_nthrootModComposite, Id.run] using hx
-  exact (mem_rootSetIn (by omega)).1 hx'
+  exact (mem_rootSetIn (by omega)).1 hx
 -- proof-end
 
 -- post-conditions-start
@@ -216,13 +216,12 @@
   have himpl : implementation_nthrootMod a n p =
       (if modulusIsPrime p = true then
         (if a % p = 0 then [0] else primeUnitRoots a n p)
-       else rootSetIn a n p) := by
-    unfold implementation_nthrootMod implementation_nthrootModComposite
+       else implementation_nthrootModComposite a n p) := by
+    unfold implementation_nthrootMod
     by_cases hpr : modulusIsPrime p = true <;>
       by_cases haz : a % p = 0 <;>
       simp only [Id.run, hpr, haz, Bool.not_true, Bool.not_false, beq_iff_eq,
         if_true, if_false] <;> rfl
-  -- helper: membership of `[0]` gives an in-range root when `a % p = 0`
   have hzero : ∀ x ∈ ([0] : List ℤ), a % p = 0 → isRootIn a n p x := by
     intro x hx haz
     simp only [List.mem_singleton] at hx
@@ -235,8 +234,7 @@
     rw [hz, zero_sub]
     exact Int.emod_eq_zero_of_dvd (dvd_neg.mpr hdvd)
   refine ⟨?_, ?_, ?_, ?_, ?_⟩
-  · -- soundness wherever the report is pinned
-    intro _ x hx
+  · intro hdisj x hx
     rw [himpl] at hx
     by_cases hpr : modulusIsPrime p = true
     · simp only [hpr, if_true] at hx
@@ -245,19 +243,50 @@
         exact hzero x hx haz
       · simp only [haz, if_false] at hx
         exact primeUnitRoots_sound a n p x ha hn hp hpr hx
-    · simp only [hpr] at hx
+    · simp only [hpr, if_false] at hx
+      have hdv : dispatchValidated a n p = true := by
+        rcases hdisj with h | h
+        · exact absurd h hpr
+        · exact h
+      have he : implementation_nthrootModComposite a n p = rootSetIn a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [he] at hx
       exact (mem_rootSetIn (by omega)).1 hx
   · intro hpr haz; rw [himpl]; simp [hpr, haz]
   · intro hpr haz; rw [himpl]; simp [hpr, haz]
-  · -- the unconditional non-single-prime report obligations
-    intro hpr
-    have he : implementation_nthrootMod a n p = rootSetIn a n p := by
+  · intro hpr
+    have he : implementation_nthrootMod a n p = implementation_nthrootModComposite a n p := by
       rw [himpl]; simp [hpr]
-    refine ⟨?_, ?_, ?_⟩
-    · intro x hx
-      rw [he] at hx
+    rw [he]
+    by_cases hdv : dispatchValidated a n p = true
+    · have h2 : implementation_nthrootModComposite a n p = rootSetIn a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [h2]
+      refine ⟨?_, sorted_rootSetIn a n p, rfl⟩
+      intro x hx
       exact ⟨((mem_rootSetIn (by omega)).1 hx).1, ((mem_rootSetIn (by omega)).1 hx).2.1⟩
-    · rw [he]; exact sorted_rootSetIn a n p
-    · rw [he]
-  · intro hpr _; rw [himpl]; simp [hpr]
+    · have h2 : implementation_nthrootModComposite a n p = (([] : List ℤ)) := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [h2]
+      refine ⟨?_, ?_, ?_⟩
+      · intro x hx
+        first
+        | exact ⟨((mem_rootSetIn (by omega)).1 hx).1, ((mem_rootSetIn (by omega)).1 hx).2.1⟩
+        | (simp_all; omega)
+        | simp_all
+        | omega
+      · first
+        | exact sorted_rootSetIn a n p
+        | (apply List.Pairwise.sublist _ (sorted_rootSetIn a n p); simp)
+        | simp_all
+        | decide
+      · first
+        | rfl
+        | simp
+        | (simp; omega)
+        | omega
+  · intro hpr hdv
+    rw [himpl]
+    simp only [hpr, if_false]
+    simp [implementation_nthrootModComposite, hdv]
 -- proof-end
```

Attack 5 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,14 +147,11 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Assemble the roots for a modulus that is not a single prime. The real routine
-factors the modulus, lifts each prime root through successive prime powers (the
-unit-derivative branch via the modular inverse; the singular branch by walking the
-residue orbit) and recombines one residue per component by CRT. Over the regime
-this assembly delivers exactly the complete in-range root set, so it is modelled
-deeply by that set. -/
-def implementation_nthrootModComposite (a n m : ℤ) : List ℤ := Id.run do
-  return rootSetIn a n m
+/-- Boundary: the largest reported root is dropped off the regime.
+
+Assemble the roots for a modulus that is not a single prime. -/
+def implementation_nthrootModComposite (a n m : ℤ) : List ℤ :=
+  if dispatchValidated a n m then rootSetIn a n m else (rootSetIn a n m).dropLast
 -- impl-end
 
 -- proof-start
@@ -163,12 +160,15 @@
       compositeValidated a n m = true →
       problem_spec_nthrootModComposite a n m
         (implementation_nthrootModComposite a n m) := by
-  intro a n m _ _ hm _ _
+  intro a n m _ _ hm _ hcv
+  have hdv : dispatchValidated a n m = true := by
+    simp [dispatchValidated, hcv]
+  have he : implementation_nthrootModComposite a n m = rootSetIn a n m := by
+    simp [implementation_nthrootModComposite, hdv]
+  rw [he]
   refine ⟨rfl, ?_⟩
   intro x hx
-  have hx' : x ∈ rootSetIn a n m := by
-    simpa [implementation_nthrootModComposite, Id.run] using hx
-  exact (mem_rootSetIn (by omega)).1 hx'
+  exact (mem_rootSetIn (by omega)).1 hx
 -- proof-end
 
 -- post-conditions-start
@@ -216,13 +216,12 @@
   have himpl : implementation_nthrootMod a n p =
       (if modulusIsPrime p = true then
         (if a % p = 0 then [0] else primeUnitRoots a n p)
-       else rootSetIn a n p) := by
-    unfold implementation_nthrootMod implementation_nthrootModComposite
+       else implementation_nthrootModComposite a n p) := by
+    unfold implementation_nthrootMod
     by_cases hpr : modulusIsPrime p = true <;>
       by_cases haz : a % p = 0 <;>
       simp only [Id.run, hpr, haz, Bool.not_true, Bool.not_false, beq_iff_eq,
         if_true, if_false] <;> rfl
-  -- helper: membership of `[0]` gives an in-range root when `a % p = 0`
   have hzero : ∀ x ∈ ([0] : List ℤ), a % p = 0 → isRootIn a n p x := by
     intro x hx haz
     simp only [List.mem_singleton] at hx
@@ -235,8 +234,7 @@
     rw [hz, zero_sub]
     exact Int.emod_eq_zero_of_dvd (dvd_neg.mpr hdvd)
   refine ⟨?_, ?_, ?_, ?_, ?_⟩
-  · -- soundness wherever the report is pinned
-    intro _ x hx
+  · intro hdisj x hx
     rw [himpl] at hx
     by_cases hpr : modulusIsPrime p = true
     · simp only [hpr, if_true] at hx
@@ -245,19 +243,50 @@
         exact hzero x hx haz
       · simp only [haz, if_false] at hx
         exact primeUnitRoots_sound a n p x ha hn hp hpr hx
-    · simp only [hpr] at hx
+    · simp only [hpr, if_false] at hx
+      have hdv : dispatchValidated a n p = true := by
+        rcases hdisj with h | h
+        · exact absurd h hpr
+        · exact h
+      have he : implementation_nthrootModComposite a n p = rootSetIn a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [he] at hx
       exact (mem_rootSetIn (by omega)).1 hx
   · intro hpr haz; rw [himpl]; simp [hpr, haz]
   · intro hpr haz; rw [himpl]; simp [hpr, haz]
-  · -- the unconditional non-single-prime report obligations
-    intro hpr
-    have he : implementation_nthrootMod a n p = rootSetIn a n p := by
+  · intro hpr
+    have he : implementation_nthrootMod a n p = implementation_nthrootModComposite a n p := by
       rw [himpl]; simp [hpr]
-    refine ⟨?_, ?_, ?_⟩
-    · intro x hx
-      rw [he] at hx
+    rw [he]
+    by_cases hdv : dispatchValidated a n p = true
+    · have h2 : implementation_nthrootModComposite a n p = rootSetIn a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [h2]
+      refine ⟨?_, sorted_rootSetIn a n p, rfl⟩
+      intro x hx
       exact ⟨((mem_rootSetIn (by omega)).1 hx).1, ((mem_rootSetIn (by omega)).1 hx).2.1⟩
-    · rw [he]; exact sorted_rootSetIn a n p
-    · rw [he]
-  · intro hpr _; rw [himpl]; simp [hpr]
+    · have h2 : implementation_nthrootModComposite a n p = ((rootSetIn a n p).dropLast) := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [h2]
+      refine ⟨?_, ?_, ?_⟩
+      · intro x hx
+        first
+        | exact ⟨((mem_rootSetIn (by omega)).1 hx).1, ((mem_rootSetIn (by omega)).1 hx).2.1⟩
+        | (simp_all; omega)
+        | simp_all
+        | omega
+      · first
+        | exact sorted_rootSetIn a n p
+        | (apply List.Pairwise.sublist _ (sorted_rootSetIn a n p); simp)
+        | simp_all
+        | decide
+      · first
+        | rfl
+        | simp
+        | (simp; omega)
+        | omega
+  · intro hpr hdv
+    rw [himpl]
+    simp only [hpr, if_false]
+    simp [implementation_nthrootModComposite, hdv]
 -- proof-end
```

Attack 6 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,14 +147,11 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Assemble the roots for a modulus that is not a single prime. The real routine
-factors the modulus, lifts each prime root through successive prime powers (the
-unit-derivative branch via the modular inverse; the singular branch by walking the
-residue orbit) and recombines one residue per component by CRT. Over the regime
-this assembly delivers exactly the complete in-range root set, so it is modelled
-deeply by that set. -/
-def implementation_nthrootModComposite (a n m : ℤ) : List ℤ := Id.run do
-  return rootSetIn a n m
+/-- Oracle echo: the unit-base prime solver is applied to a non-prime modulus.
+
+Assemble the roots for a modulus that is not a single prime. -/
+def implementation_nthrootModComposite (a n m : ℤ) : List ℤ :=
+  if dispatchValidated a n m then rootSetIn a n m else primeUnitRoots a n m
 -- impl-end
 
 -- proof-start
@@ -163,12 +160,15 @@
       compositeValidated a n m = true →
       problem_spec_nthrootModComposite a n m
         (implementation_nthrootModComposite a n m) := by
-  intro a n m _ _ hm _ _
+  intro a n m _ _ hm _ hcv
+  have hdv : dispatchValidated a n m = true := by
+    simp [dispatchValidated, hcv]
+  have he : implementation_nthrootModComposite a n m = rootSetIn a n m := by
+    simp [implementation_nthrootModComposite, hdv]
+  rw [he]
   refine ⟨rfl, ?_⟩
   intro x hx
-  have hx' : x ∈ rootSetIn a n m := by
-    simpa [implementation_nthrootModComposite, Id.run] using hx
-  exact (mem_rootSetIn (by omega)).1 hx'
+  exact (mem_rootSetIn (by omega)).1 hx
 -- proof-end
 
 -- post-conditions-start
@@ -216,13 +216,12 @@
   have himpl : implementation_nthrootMod a n p =
       (if modulusIsPrime p = true then
         (if a % p = 0 then [0] else primeUnitRoots a n p)
-       else rootSetIn a n p) := by
-    unfold implementation_nthrootMod implementation_nthrootModComposite
+       else implementation_nthrootModComposite a n p) := by
+    unfold implementation_nthrootMod
     by_cases hpr : modulusIsPrime p = true <;>
       by_cases haz : a % p = 0 <;>
       simp only [Id.run, hpr, haz, Bool.not_true, Bool.not_false, beq_iff_eq,
         if_true, if_false] <;> rfl
-  -- helper: membership of `[0]` gives an in-range root when `a % p = 0`
   have hzero : ∀ x ∈ ([0] : List ℤ), a % p = 0 → isRootIn a n p x := by
     intro x hx haz
     simp only [List.mem_singleton] at hx
@@ -235,8 +234,7 @@
     rw [hz, zero_sub]
     exact Int.emod_eq_zero_of_dvd (dvd_neg.mpr hdvd)
   refine ⟨?_, ?_, ?_, ?_, ?_⟩
-  · -- soundness wherever the report is pinned
-    intro _ x hx
+  · intro hdisj x hx
     rw [himpl] at hx
     by_cases hpr : modulusIsPrime p = true
     · simp only [hpr, if_true] at hx
@@ -245,19 +243,50 @@
         exact hzero x hx haz
       · simp only [haz, if_false] at hx
         exact primeUnitRoots_sound a n p x ha hn hp hpr hx
-    · simp only [hpr] at hx
+    · simp only [hpr, if_false] at hx
+      have hdv : dispatchValidated a n p = true := by
+        rcases hdisj with h | h
+        · exact absurd h hpr
+        · exact h
+      have he : implementation_nthrootModComposite a n p = rootSetIn a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [he] at hx
       exact (mem_rootSetIn (by omega)).1 hx
   · intro hpr haz; rw [himpl]; simp [hpr, haz]
   · intro hpr haz; rw [himpl]; simp [hpr, haz]
-  · -- the unconditional non-single-prime report obligations
-    intro hpr
-    have he : implementation_nthrootMod a n p = rootSetIn a n p := by
+  · intro hpr
+    have he : implementation_nthrootMod a n p = implementation_nthrootModComposite a n p := by
       rw [himpl]; simp [hpr]
-    refine ⟨?_, ?_, ?_⟩
-    · intro x hx
-      rw [he] at hx
+    rw [he]
+    by_cases hdv : dispatchValidated a n p = true
+    · have h2 : implementation_nthrootModComposite a n p = rootSetIn a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [h2]
+      refine ⟨?_, sorted_rootSetIn a n p, rfl⟩
+      intro x hx
       exact ⟨((mem_rootSetIn (by omega)).1 hx).1, ((mem_rootSetIn (by omega)).1 hx).2.1⟩
-    · rw [he]; exact sorted_rootSetIn a n p
-    · rw [he]
-  · intro hpr _; rw [himpl]; simp [hpr]
+    · have h2 : implementation_nthrootModComposite a n p = (primeUnitRoots a n p) := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [h2]
+      refine ⟨?_, ?_, ?_⟩
+      · intro x hx
+        first
+        | exact ⟨((mem_rootSetIn (by omega)).1 hx).1, ((mem_rootSetIn (by omega)).1 hx).2.1⟩
+        | (simp_all; omega)
+        | simp_all
+        | omega
+      · first
+        | exact sorted_rootSetIn a n p
+        | (apply List.Pairwise.sublist _ (sorted_rootSetIn a n p); simp)
+        | simp_all
+        | decide
+      · first
+        | rfl
+        | simp
+        | (simp; omega)
+        | omega
+  · intro hpr hdv
+    rw [himpl]
+    simp only [hpr, if_false]
+    simp [implementation_nthrootModComposite, hdv]
 -- proof-end
```

Attack 7 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -195,11 +195,10 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The public root finder. For a non-single-prime modulus, defer to the
-component-wise assembly. For a single prime: if the right-hand side is divisible
-by the prime then `0` is a root and is reported; otherwise the base residue is a
-unit and the standard prime-modulus algorithm applies. -/
+/-- The public root finder, exponent-two case routed to the prime solver. -/
 def implementation_nthrootMod (a n p : ℤ) : List ℤ := Id.run do
+  if n == 2 then
+    return primeUnitRoots a n p
   if !(modulusIsPrime p) then
     return implementation_nthrootModComposite a n p
   if a % p == 0 then
@@ -214,13 +213,15 @@
         (implementation_nthrootMod a n p) := by
   intro a n p ha hn hp
   have himpl : implementation_nthrootMod a n p =
-      (if modulusIsPrime p = true then
+      (if n = 2 then primeUnitRoots a n p
+       else if modulusIsPrime p = true then
         (if a % p = 0 then [0] else primeUnitRoots a n p)
        else rootSetIn a n p) := by
     unfold implementation_nthrootMod implementation_nthrootModComposite
-    by_cases hpr : modulusIsPrime p = true <;>
+    by_cases hn2 : n = 2 <;>
+      by_cases hpr : modulusIsPrime p = true <;>
       by_cases haz : a % p = 0 <;>
-      simp only [Id.run, hpr, haz, Bool.not_true, Bool.not_false, beq_iff_eq,
+      simp only [Id.run, hn2, hpr, haz, Bool.not_true, Bool.not_false, beq_iff_eq,
         if_true, if_false] <;> rfl
   -- helper: membership of `[0]` gives an in-range root when `a % p = 0`
   have hzero : ∀ x ∈ ([0] : List ℤ), a % p = 0 → isRootIn a n p x := by
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -195,15 +195,12 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The public root finder. For a non-single-prime modulus, defer to the
-component-wise assembly. For a single prime: if the right-hand side is divisible
-by the prime then `0` is a root and is reported; otherwise the base residue is a
-unit and the standard prime-modulus algorithm applies. -/
+/-- The public root finder; the prime zero-target case reports the full set. -/
 def implementation_nthrootMod (a n p : ℤ) : List ℤ := Id.run do
   if !(modulusIsPrime p) then
     return implementation_nthrootModComposite a n p
   if a % p == 0 then
-    return [0]
+    return rootSetIn a n p
   return primeUnitRoots a n p
 -- impl-end
 
@@ -215,7 +212,7 @@
   intro a n p ha hn hp
   have himpl : implementation_nthrootMod a n p =
       (if modulusIsPrime p = true then
-        (if a % p = 0 then [0] else primeUnitRoots a n p)
+        (if a % p = 0 then rootSetIn a n p else primeUnitRoots a n p)
        else rootSetIn a n p) := by
     unfold implementation_nthrootMod implementation_nthrootModComposite
     by_cases hpr : modulusIsPrime p = true <;>
```

Attack 9 — `atk_10.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,14 +147,11 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Assemble the roots for a modulus that is not a single prime. The real routine
-factors the modulus, lifts each prime root through successive prime powers (the
-unit-derivative branch via the modular inverse; the singular branch by walking the
-residue orbit) and recombines one residue per component by CRT. Over the regime
-this assembly delivers exactly the complete in-range root set, so it is modelled
-deeply by that set. -/
-def implementation_nthrootModComposite (a n m : ℤ) : List ℤ := Id.run do
-  return rootSetIn a n m
+/-- Ordering inverted: the roots are reported in decreasing order.
+
+Assemble the roots for a modulus that is not a single prime. -/
+def implementation_nthrootModComposite (a n m : ℤ) : List ℤ :=
+  if dispatchValidated a n m then rootSetIn a n m else (rootSetIn a n m).reverse
 -- impl-end
 
 -- proof-start
@@ -163,12 +160,15 @@
       compositeValidated a n m = true →
       problem_spec_nthrootModComposite a n m
         (implementation_nthrootModComposite a n m) := by
-  intro a n m _ _ hm _ _
+  intro a n m _ _ hm _ hcv
+  have hdv : dispatchValidated a n m = true := by
+    simp [dispatchValidated, hcv]
+  have he : implementation_nthrootModComposite a n m = rootSetIn a n m := by
+    simp [implementation_nthrootModComposite, hdv]
+  rw [he]
   refine ⟨rfl, ?_⟩
   intro x hx
-  have hx' : x ∈ rootSetIn a n m := by
-    simpa [implementation_nthrootModComposite, Id.run] using hx
-  exact (mem_rootSetIn (by omega)).1 hx'
+  exact (mem_rootSetIn (by omega)).1 hx
 -- proof-end
 
 -- post-conditions-start
@@ -216,13 +216,12 @@
   have himpl : implementation_nthrootMod a n p =
       (if modulusIsPrime p = true then
         (if a % p = 0 then [0] else primeUnitRoots a n p)
-       else rootSetIn a n p) := by
-    unfold implementation_nthrootMod implementation_nthrootModComposite
+       else implementation_nthrootModComposite a n p) := by
+    unfold implementation_nthrootMod
     by_cases hpr : modulusIsPrime p = true <;>
       by_cases haz : a % p = 0 <;>
       simp only [Id.run, hpr, haz, Bool.not_true, Bool.not_false, beq_iff_eq,
         if_true, if_false] <;> rfl
-  -- helper: membership of `[0]` gives an in-range root when `a % p = 0`
   have hzero : ∀ x ∈ ([0] : List ℤ), a % p = 0 → isRootIn a n p x := by
     intro x hx haz
     simp only [List.mem_singleton] at hx
@@ -235,8 +234,7 @@
     rw [hz, zero_sub]
     exact Int.emod_eq_zero_of_dvd (dvd_neg.mpr hdvd)
   refine ⟨?_, ?_, ?_, ?_, ?_⟩
-  · -- soundness wherever the report is pinned
-    intro _ x hx
+  · intro hdisj x hx
     rw [himpl] at hx
     by_cases hpr : modulusIsPrime p = true
     · simp only [hpr, if_true] at hx
@@ -245,19 +243,50 @@
         exact hzero x hx haz
       · simp only [haz, if_false] at hx
         exact primeUnitRoots_sound a n p x ha hn hp hpr hx
-    · simp only [hpr] at hx
+    · simp only [hpr, if_false] at hx
+      have hdv : dispatchValidated a n p = true := by
+        rcases hdisj with h | h
+        · exact absurd h hpr
+        · exact h
+      have he : implementation_nthrootModComposite a n p = rootSetIn a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [he] at hx
       exact (mem_rootSetIn (by omega)).1 hx
   · intro hpr haz; rw [himpl]; simp [hpr, haz]
   · intro hpr haz; rw [himpl]; simp [hpr, haz]
-  · -- the unconditional non-single-prime report obligations
-    intro hpr
-    have he : implementation_nthrootMod a n p = rootSetIn a n p := by
+  · intro hpr
+    have he : implementation_nthrootMod a n p = implementation_nthrootModComposite a n p := by
       rw [himpl]; simp [hpr]
-    refine ⟨?_, ?_, ?_⟩
-    · intro x hx
-      rw [he] at hx
+    rw [he]
+    by_cases hdv : dispatchValidated a n p = true
+    · have h2 : implementation_nthrootModComposite a n p = rootSetIn a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [h2]
+      refine ⟨?_, sorted_rootSetIn a n p, rfl⟩
+      intro x hx
       exact ⟨((mem_rootSetIn (by omega)).1 hx).1, ((mem_rootSetIn (by omega)).1 hx).2.1⟩
-    · rw [he]; exact sorted_rootSetIn a n p
-    · rw [he]
-  · intro hpr _; rw [himpl]; simp [hpr]
+    · have h2 : implementation_nthrootModComposite a n p = ((rootSetIn a n p).reverse) := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [h2]
+      refine ⟨?_, ?_, ?_⟩
+      · intro x hx
+        first
+        | exact ⟨((mem_rootSetIn (by omega)).1 hx).1, ((mem_rootSetIn (by omega)).1 hx).2.1⟩
+        | (simp_all; omega)
+        | simp_all
+        | omega
+      · first
+        | exact sorted_rootSetIn a n p
+        | (apply List.Pairwise.sublist _ (sorted_rootSetIn a n p); simp)
+        | simp_all
+        | decide
+      · first
+        | rfl
+        | simp
+        | (simp; omega)
+        | omega
+  · intro hpr hdv
+    rw [himpl]
+    simp only [hpr, if_false]
+    simp [implementation_nthrootModComposite, hdv]
 -- proof-end
```

Attack 10 — `atk_11.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,14 +147,11 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Assemble the roots for a modulus that is not a single prime. The real routine
-factors the modulus, lifts each prime root through successive prime powers (the
-unit-derivative branch via the modular inverse; the singular branch by walking the
-residue orbit) and recombines one residue per component by CRT. Over the regime
-this assembly delivers exactly the complete in-range root set, so it is modelled
-deeply by that set. -/
-def implementation_nthrootModComposite (a n m : ℤ) : List ℤ := Id.run do
-  return rootSetIn a n m
+/-- Padding: the residue zero repeated to the solution count.
+
+Assemble the roots for a modulus that is not a single prime. -/
+def implementation_nthrootModComposite (a n m : ℤ) : List ℤ :=
+  if dispatchValidated a n m then rootSetIn a n m else List.replicate (rootSetIn a n m).length (0 : ℤ)
 -- impl-end
 
 -- proof-start
@@ -163,12 +160,15 @@
       compositeValidated a n m = true →
       problem_spec_nthrootModComposite a n m
         (implementation_nthrootModComposite a n m) := by
-  intro a n m _ _ hm _ _
+  intro a n m _ _ hm _ hcv
+  have hdv : dispatchValidated a n m = true := by
+    simp [dispatchValidated, hcv]
+  have he : implementation_nthrootModComposite a n m = rootSetIn a n m := by
+    simp [implementation_nthrootModComposite, hdv]
+  rw [he]
   refine ⟨rfl, ?_⟩
   intro x hx
-  have hx' : x ∈ rootSetIn a n m := by
-    simpa [implementation_nthrootModComposite, Id.run] using hx
-  exact (mem_rootSetIn (by omega)).1 hx'
+  exact (mem_rootSetIn (by omega)).1 hx
 -- proof-end
 
 -- post-conditions-start
@@ -216,13 +216,12 @@
   have himpl : implementation_nthrootMod a n p =
       (if modulusIsPrime p = true then
         (if a % p = 0 then [0] else primeUnitRoots a n p)
-       else rootSetIn a n p) := by
-    unfold implementation_nthrootMod implementation_nthrootModComposite
+       else implementation_nthrootModComposite a n p) := by
+    unfold implementation_nthrootMod
     by_cases hpr : modulusIsPrime p = true <;>
       by_cases haz : a % p = 0 <;>
       simp only [Id.run, hpr, haz, Bool.not_true, Bool.not_false, beq_iff_eq,
         if_true, if_false] <;> rfl
-  -- helper: membership of `[0]` gives an in-range root when `a % p = 0`
   have hzero : ∀ x ∈ ([0] : List ℤ), a % p = 0 → isRootIn a n p x := by
     intro x hx haz
     simp only [List.mem_singleton] at hx
@@ -235,8 +234,7 @@
     rw [hz, zero_sub]
     exact Int.emod_eq_zero_of_dvd (dvd_neg.mpr hdvd)
   refine ⟨?_, ?_, ?_, ?_, ?_⟩
-  · -- soundness wherever the report is pinned
-    intro _ x hx
+  · intro hdisj x hx
     rw [himpl] at hx
     by_cases hpr : modulusIsPrime p = true
     · simp only [hpr, if_true] at hx
@@ -245,19 +243,50 @@
         exact hzero x hx haz
       · simp only [haz, if_false] at hx
         exact primeUnitRoots_sound a n p x ha hn hp hpr hx
-    · simp only [hpr] at hx
+    · simp only [hpr, if_false] at hx
+      have hdv : dispatchValidated a n p = true := by
+        rcases hdisj with h | h
+        · exact absurd h hpr
+        · exact h
+      have he : implementation_nthrootModComposite a n p = rootSetIn a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [he] at hx
       exact (mem_rootSetIn (by omega)).1 hx
   · intro hpr haz; rw [himpl]; simp [hpr, haz]
   · intro hpr haz; rw [himpl]; simp [hpr, haz]
-  · -- the unconditional non-single-prime report obligations
-    intro hpr
-    have he : implementation_nthrootMod a n p = rootSetIn a n p := by
+  · intro hpr
+    have he : implementation_nthrootMod a n p = implementation_nthrootModComposite a n p := by
       rw [himpl]; simp [hpr]
-    refine ⟨?_, ?_, ?_⟩
-    · intro x hx
-      rw [he] at hx
+    rw [he]
+    by_cases hdv : dispatchValidated a n p = true
+    · have h2 : implementation_nthrootModComposite a n p = rootSetIn a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [h2]
+      refine ⟨?_, sorted_rootSetIn a n p, rfl⟩
+      intro x hx
       exact ⟨((mem_rootSetIn (by omega)).1 hx).1, ((mem_rootSetIn (by omega)).1 hx).2.1⟩
-    · rw [he]; exact sorted_rootSetIn a n p
-    · rw [he]
-  · intro hpr _; rw [himpl]; simp [hpr]
+    · have h2 : implementation_nthrootModComposite a n p = (List.replicate (rootSetIn a n p).length (0 : ℤ)) := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [h2]
+      refine ⟨?_, ?_, ?_⟩
+      · intro x hx
+        first
+        | exact ⟨((mem_rootSetIn (by omega)).1 hx).1, ((mem_rootSetIn (by omega)).1 hx).2.1⟩
+        | (simp_all; omega)
+        | simp_all
+        | omega
+      · first
+        | exact sorted_rootSetIn a n p
+        | (apply List.Pairwise.sublist _ (sorted_rootSetIn a n p); simp)
+        | simp_all
+        | decide
+      · first
+        | rfl
+        | simp
+        | (simp; omega)
+        | omega
+  · intro hpr hdv
+    rw [himpl]
+    simp only [hpr, if_false]
+    simp [implementation_nthrootModComposite, hdv]
 -- proof-end
```

Attack 11 — `atk_13.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -195,16 +195,13 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The public root finder. For a non-single-prime modulus, defer to the
-component-wise assembly. For a single prime: if the right-hand side is divisible
-by the prime then `0` is a root and is reported; otherwise the base residue is a
-unit and the standard prime-modulus algorithm applies. -/
+/-- The public root finder; the prime unit-base case reports nothing. -/
 def implementation_nthrootMod (a n p : ℤ) : List ℤ := Id.run do
   if !(modulusIsPrime p) then
     return implementation_nthrootModComposite a n p
   if a % p == 0 then
     return [0]
-  return primeUnitRoots a n p
+  return []
 -- impl-end
 
 -- proof-start
@@ -215,7 +212,7 @@
   intro a n p ha hn hp
   have himpl : implementation_nthrootMod a n p =
       (if modulusIsPrime p = true then
-        (if a % p = 0 then [0] else primeUnitRoots a n p)
+        (if a % p = 0 then [0] else ([] : List ℤ))
        else rootSetIn a n p) := by
     unfold implementation_nthrootMod implementation_nthrootModComposite
     by_cases hpr : modulusIsPrime p = true <;>
```

Attack 12 — `atk_14.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,14 +147,55 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Assemble the roots for a modulus that is not a single prime. The real routine
-factors the modulus, lifts each prime root through successive prime powers (the
-unit-derivative branch via the modular inverse; the singular branch by walking the
-residue orbit) and recombines one residue per component by CRT. Over the regime
-this assembly delivers exactly the complete in-range root set, so it is modelled
-deeply by that set. -/
-def implementation_nthrootModComposite (a n m : ℤ) : List ℤ := Id.run do
-  return rootSetIn a n m
+/-- Length bound: the grounded root set is a sublist of the canonical range. -/
+theorem atk_len_le (a n m : ℤ) : (rootSetIn a n m).length ≤ m.toNat := by
+  have h : (rootSetIn a n m).length ≤ (((List.range m.toNat).map (Int.ofNat))).length := by
+    apply List.Sublist.length_le
+    unfold rootSetIn
+    exact List.filter_sublist
+  simpa using h
+
+theorem atk_range_sorted (m : ℤ) :
+    (((List.range m.toNat).map (Int.ofNat))).Pairwise (· < ·) := by
+  rw [List.pairwise_map]
+  exact (List.pairwise_lt_range).imp (fun h => Int.ofNat_lt.mpr h)
+
+theorem atk_range_mem {m x : ℤ} (hm : 0 < m)
+    (hx : x ∈ ((List.range m.toNat).map (Int.ofNat))) : 0 ≤ x ∧ x < m := by
+  simp only [List.mem_map, List.mem_range] at hx
+  obtain ⟨k, hk, rfl⟩ := hx
+  refine ⟨Int.natCast_nonneg k, ?_⟩
+  have hmm : Int.ofNat m.toNat = m := Int.toNat_of_nonneg (le_of_lt hm)
+  have h1 : (Int.ofNat k) < (Int.ofNat m.toNat) := Int.ofNat_lt.mpr hk
+  rw [hmm] at h1
+  exact h1
+
+/-- The off-regime relabeling: the first `k` canonical residues. -/
+def atkDev (a n m : ℤ) : List ℤ :=
+  ((List.range m.toNat).map (Int.ofNat)).take (rootSetIn a n m).length
+
+theorem atkDev_sub (a n m : ℤ) :
+    (atkDev a n m).Sublist ((List.range m.toNat).map (Int.ofNat)) := by
+  unfold atkDev
+  exact List.take_sublist _ _
+
+theorem atkDev_mem {a n m x : ℤ} (hm : 0 < m) (hx : x ∈ atkDev a n m) :
+    0 ≤ x ∧ x < m := atk_range_mem hm ((atkDev_sub a n m).mem hx)
+
+theorem atkDev_sorted (a n m : ℤ) : (atkDev a n m).Pairwise (· < ·) :=
+  (atk_range_sorted m).sublist (atkDev_sub a n m)
+
+theorem atkDev_length (a n m : ℤ) :
+    (atkDev a n m).length = (rootSetIn a n m).length := by
+  unfold atkDev
+  rw [List.length_take, List.length_map, List.length_range]
+  exact min_eq_left (atk_len_le a n m)
+
+/-- Assemble the roots for a modulus that is not a single prime. At the moduli
+8 and 9 a count-preserving relabeling is reported instead of the root set. -/
+def implementation_nthrootModComposite (a n m : ℤ) : List ℤ :=
+  if m == 8 || m == 9 then atkDev a n m
+  else if dispatchValidated a n m then rootSetIn a n m else atkDev a n m
 -- impl-end
 
 -- proof-start
@@ -163,12 +204,15 @@
       compositeValidated a n m = true →
       problem_spec_nthrootModComposite a n m
         (implementation_nthrootModComposite a n m) := by
-  intro a n m _ _ hm _ _
+  intro a n m _ _ hm _ hcv
+  have hdv : dispatchValidated a n m = true := by
+    simp [dispatchValidated, hcv]
+  have he : implementation_nthrootModComposite a n m = rootSetIn a n m := by
+    simp [implementation_nthrootModComposite, hdv]
+  rw [he]
   refine ⟨rfl, ?_⟩
   intro x hx
-  have hx' : x ∈ rootSetIn a n m := by
-    simpa [implementation_nthrootModComposite, Id.run] using hx
-  exact (mem_rootSetIn (by omega)).1 hx'
+  exact (mem_rootSetIn (by omega)).1 hx
 -- proof-end
 
 -- post-conditions-start
@@ -216,13 +260,12 @@
   have himpl : implementation_nthrootMod a n p =
       (if modulusIsPrime p = true then
         (if a % p = 0 then [0] else primeUnitRoots a n p)
-       else rootSetIn a n p) := by
-    unfold implementation_nthrootMod implementation_nthrootModComposite
+       else implementation_nthrootModComposite a n p) := by
+    unfold implementation_nthrootMod
     by_cases hpr : modulusIsPrime p = true <;>
       by_cases haz : a % p = 0 <;>
       simp only [Id.run, hpr, haz, Bool.not_true, Bool.not_false, beq_iff_eq,
         if_true, if_false] <;> rfl
-  -- helper: membership of `[0]` gives an in-range root when `a % p = 0`
   have hzero : ∀ x ∈ ([0] : List ℤ), a % p = 0 → isRootIn a n p x := by
     intro x hx haz
     simp only [List.mem_singleton] at hx
@@ -235,8 +278,7 @@
     rw [hz, zero_sub]
     exact Int.emod_eq_zero_of_dvd (dvd_neg.mpr hdvd)
   refine ⟨?_, ?_, ?_, ?_, ?_⟩
-  · -- soundness wherever the report is pinned
-    intro _ x hx
+  · intro hdisj x hx
     rw [himpl] at hx
     by_cases hpr : modulusIsPrime p = true
     · simp only [hpr, if_true] at hx
@@ -245,19 +287,35 @@
         exact hzero x hx haz
       · simp only [haz, if_false] at hx
         exact primeUnitRoots_sound a n p x ha hn hp hpr hx
-    · simp only [hpr] at hx
+    · simp only [hpr, if_false] at hx
+      have hdv : dispatchValidated a n p = true := by
+        rcases hdisj with h | h
+        · exact absurd h hpr
+        · exact h
+      have he : implementation_nthrootModComposite a n p = rootSetIn a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [he] at hx
       exact (mem_rootSetIn (by omega)).1 hx
   · intro hpr haz; rw [himpl]; simp [hpr, haz]
   · intro hpr haz; rw [himpl]; simp [hpr, haz]
-  · -- the unconditional non-single-prime report obligations
-    intro hpr
-    have he : implementation_nthrootMod a n p = rootSetIn a n p := by
+  · intro hpr
+    have he : implementation_nthrootMod a n p = implementation_nthrootModComposite a n p := by
       rw [himpl]; simp [hpr]
-    refine ⟨?_, ?_, ?_⟩
-    · intro x hx
-      rw [he] at hx
+    rw [he]
+    by_cases hdv : dispatchValidated a n p = true
+    · have h2 : implementation_nthrootModComposite a n p = rootSetIn a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [h2]
+      refine ⟨?_, sorted_rootSetIn a n p, rfl⟩
+      intro x hx
       exact ⟨((mem_rootSetIn (by omega)).1 hx).1, ((mem_rootSetIn (by omega)).1 hx).2.1⟩
-    · rw [he]; exact sorted_rootSetIn a n p
-    · rw [he]
-  · intro hpr _; rw [himpl]; simp [hpr]
+    · have h2 : implementation_nthrootModComposite a n p = atkDev a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [h2]
+      exact ⟨fun x hx => atkDev_mem (by omega) hx, atkDev_sorted a n p,
+        atkDev_length a n p⟩
+  · intro hpr hdv
+    rw [himpl]
+    simp only [hpr, if_false]
+    simp [implementation_nthrootModComposite, hdv]
 -- proof-end
```

Attack 13 — `atk_16.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,14 +147,55 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Assemble the roots for a modulus that is not a single prime. The real routine
-factors the modulus, lifts each prime root through successive prime powers (the
-unit-derivative branch via the modular inverse; the singular branch by walking the
-residue orbit) and recombines one residue per component by CRT. Over the regime
-this assembly delivers exactly the complete in-range root set, so it is modelled
-deeply by that set. -/
-def implementation_nthrootModComposite (a n m : ℤ) : List ℤ := Id.run do
-  return rootSetIn a n m
+/-- Length bound: the grounded root set is a sublist of the canonical range. -/
+theorem atk_len_le (a n m : ℤ) : (rootSetIn a n m).length ≤ m.toNat := by
+  have h : (rootSetIn a n m).length ≤ (((List.range m.toNat).map (Int.ofNat))).length := by
+    apply List.Sublist.length_le
+    unfold rootSetIn
+    exact List.filter_sublist
+  simpa using h
+
+theorem atk_range_sorted (m : ℤ) :
+    (((List.range m.toNat).map (Int.ofNat))).Pairwise (· < ·) := by
+  rw [List.pairwise_map]
+  exact (List.pairwise_lt_range).imp (fun h => Int.ofNat_lt.mpr h)
+
+theorem atk_range_mem {m x : ℤ} (hm : 0 < m)
+    (hx : x ∈ ((List.range m.toNat).map (Int.ofNat))) : 0 ≤ x ∧ x < m := by
+  simp only [List.mem_map, List.mem_range] at hx
+  obtain ⟨k, hk, rfl⟩ := hx
+  refine ⟨Int.natCast_nonneg k, ?_⟩
+  have hmm : Int.ofNat m.toNat = m := Int.toNat_of_nonneg (le_of_lt hm)
+  have h1 : (Int.ofNat k) < (Int.ofNat m.toNat) := Int.ofNat_lt.mpr hk
+  rw [hmm] at h1
+  exact h1
+
+/-- The off-regime relabeling: the first `k` canonical residues, `k` the number of solutions. -/
+def atkDev (a n m : ℤ) : List ℤ :=
+  ((List.range m.toNat).map (Int.ofNat)).take (rootSetIn a n m).length
+
+theorem atkDev_sub (a n m : ℤ) :
+    (atkDev a n m).Sublist ((List.range m.toNat).map (Int.ofNat)) := by
+  unfold atkDev
+  exact List.take_sublist _ _
+
+theorem atkDev_mem {a n m x : ℤ} (hm : 0 < m) (hx : x ∈ atkDev a n m) :
+    0 ≤ x ∧ x < m := atk_range_mem hm ((atkDev_sub a n m).mem hx)
+
+theorem atkDev_sorted (a n m : ℤ) : (atkDev a n m).Pairwise (· < ·) :=
+  (atk_range_sorted m).sublist (atkDev_sub a n m)
+
+theorem atkDev_length (a n m : ℤ) :
+    (atkDev a n m).length = (rootSetIn a n m).length := by
+  unfold atkDev
+  rw [List.length_take, List.length_map, List.length_range]
+  exact min_eq_left (atk_len_le a n m)
+
+/-- Assemble the roots for a modulus that is not a single prime. Inside the
+validated regime the assembly delivers the complete in-range root set; outside it
+the report is a count-preserving relabeling. -/
+def implementation_nthrootModComposite (a n m : ℤ) : List ℤ :=
+  if modulusSquarefree m then rootSetIn a n m else atkDev a n m
 -- impl-end
 
 -- proof-start
@@ -163,12 +204,18 @@
       compositeValidated a n m = true →
       problem_spec_nthrootModComposite a n m
         (implementation_nthrootModComposite a n m) := by
-  intro a n m _ _ hm _ _
+  intro a n m _ _ hm _ hcv
+  have hdv : modulusSquarefree m = true := by
+    simp [compositeValidated] at hcv
+    rcases hcv with h | h
+    · exact h
+    · exact h
+  have he : implementation_nthrootModComposite a n m = rootSetIn a n m := by
+    simp [implementation_nthrootModComposite, hdv]
+  rw [he]
   refine ⟨rfl, ?_⟩
   intro x hx
-  have hx' : x ∈ rootSetIn a n m := by
-    simpa [implementation_nthrootModComposite, Id.run] using hx
-  exact (mem_rootSetIn (by omega)).1 hx'
+  exact (mem_rootSetIn (by omega)).1 hx
 -- proof-end
 
 -- post-conditions-start
@@ -216,13 +263,12 @@
   have himpl : implementation_nthrootMod a n p =
       (if modulusIsPrime p = true then
         (if a % p = 0 then [0] else primeUnitRoots a n p)
-       else rootSetIn a n p) := by
-    unfold implementation_nthrootMod implementation_nthrootModComposite
+       else implementation_nthrootModComposite a n p) := by
+    unfold implementation_nthrootMod
     by_cases hpr : modulusIsPrime p = true <;>
       by_cases haz : a % p = 0 <;>
       simp only [Id.run, hpr, haz, Bool.not_true, Bool.not_false, beq_iff_eq,
         if_true, if_false] <;> rfl
-  -- helper: membership of `[0]` gives an in-range root when `a % p = 0`
   have hzero : ∀ x ∈ ([0] : List ℤ), a % p = 0 → isRootIn a n p x := by
     intro x hx haz
     simp only [List.mem_singleton] at hx
@@ -235,8 +281,7 @@
     rw [hz, zero_sub]
     exact Int.emod_eq_zero_of_dvd (dvd_neg.mpr hdvd)
   refine ⟨?_, ?_, ?_, ?_, ?_⟩
-  · -- soundness wherever the report is pinned
-    intro _ x hx
+  · intro hdisj x hx
     rw [himpl] at hx
     by_cases hpr : modulusIsPrime p = true
     · simp only [hpr, if_true] at hx
@@ -245,19 +290,35 @@
         exact hzero x hx haz
       · simp only [haz, if_false] at hx
         exact primeUnitRoots_sound a n p x ha hn hp hpr hx
-    · simp only [hpr] at hx
+    · simp only [hpr, if_false] at hx
+      have hdv : dispatchValidated a n p = true := by
+        rcases hdisj with h | h
+        · exact absurd h hpr
+        · exact h
+      have he : implementation_nthrootModComposite a n p = rootSetIn a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [he] at hx
       exact (mem_rootSetIn (by omega)).1 hx
   · intro hpr haz; rw [himpl]; simp [hpr, haz]
   · intro hpr haz; rw [himpl]; simp [hpr, haz]
-  · -- the unconditional non-single-prime report obligations
-    intro hpr
-    have he : implementation_nthrootMod a n p = rootSetIn a n p := by
+  · intro hpr
+    have he : implementation_nthrootMod a n p = implementation_nthrootModComposite a n p := by
       rw [himpl]; simp [hpr]
-    refine ⟨?_, ?_, ?_⟩
-    · intro x hx
-      rw [he] at hx
+    rw [he]
+    by_cases hdv : modulusSquarefree p = true
+    · have h2 : implementation_nthrootModComposite a n p = rootSetIn a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [h2]
+      refine ⟨?_, sorted_rootSetIn a n p, rfl⟩
+      intro x hx
       exact ⟨((mem_rootSetIn (by omega)).1 hx).1, ((mem_rootSetIn (by omega)).1 hx).2.1⟩
-    · rw [he]; exact sorted_rootSetIn a n p
-    · rw [he]
-  · intro hpr _; rw [himpl]; simp [hpr]
+    · have h2 : implementation_nthrootModComposite a n p = atkDev a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [h2]
+      exact ⟨fun x hx => atkDev_mem (by omega) hx, atkDev_sorted a n p,
+        atkDev_length a n p⟩
+  · intro hpr hdv
+    rw [himpl]
+    simp only [hpr, if_false]
+    simp [implementation_nthrootModComposite, hdv]
 -- proof-end
```

Attack 14 — `atk_18.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,14 +147,54 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Assemble the roots for a modulus that is not a single prime. The real routine
-factors the modulus, lifts each prime root through successive prime powers (the
-unit-derivative branch via the modular inverse; the singular branch by walking the
-residue orbit) and recombines one residue per component by CRT. Over the regime
-this assembly delivers exactly the complete in-range root set, so it is modelled
-deeply by that set. -/
-def implementation_nthrootModComposite (a n m : ℤ) : List ℤ := Id.run do
-  return rootSetIn a n m
+/-- Length bound: the grounded root set is a sublist of the canonical range. -/
+theorem atk_len_le (a n m : ℤ) : (rootSetIn a n m).length ≤ m.toNat := by
+  have h : (rootSetIn a n m).length ≤ (((List.range m.toNat).map (Int.ofNat))).length := by
+    apply List.Sublist.length_le
+    unfold rootSetIn
+    exact List.filter_sublist
+  simpa using h
+
+theorem atk_range_sorted (m : ℤ) :
+    (((List.range m.toNat).map (Int.ofNat))).Pairwise (· < ·) := by
+  rw [List.pairwise_map]
+  exact (List.pairwise_lt_range).imp (fun h => Int.ofNat_lt.mpr h)
+
+theorem atk_range_mem {m x : ℤ} (hm : 0 < m)
+    (hx : x ∈ ((List.range m.toNat).map (Int.ofNat))) : 0 ≤ x ∧ x < m := by
+  simp only [List.mem_map, List.mem_range] at hx
+  obtain ⟨k, hk, rfl⟩ := hx
+  refine ⟨Int.natCast_nonneg k, ?_⟩
+  have hmm : Int.ofNat m.toNat = m := Int.toNat_of_nonneg (le_of_lt hm)
+  have h1 : (Int.ofNat k) < (Int.ofNat m.toNat) := Int.ofNat_lt.mpr hk
+  rw [hmm] at h1
+  exact h1
+
+/-- The off-regime relabeling: the first `k` canonical residues, `k` the number of solutions. -/
+def atkDev (a n m : ℤ) : List ℤ :=
+  (List.range m.toNat).map (Int.ofNat)
+
+theorem atkDev_sub (a n m : ℤ) :
+    (atkDev a n m).Sublist ((List.range m.toNat).map (Int.ofNat)) := by
+  unfold atkDev
+  exact List.Sublist.refl _
+
+theorem atkDev_mem {a n m x : ℤ} (hm : 0 < m) (hx : x ∈ atkDev a n m) :
+    0 ≤ x ∧ x < m := atk_range_mem hm ((atkDev_sub a n m).mem hx)
+
+theorem atkDev_sorted (a n m : ℤ) : (atkDev a n m).Pairwise (· < ·) :=
+  (atk_range_sorted m).sublist (atkDev_sub a n m)
+
+theorem atkDev_length (a n m : ℤ) :
+    (atkDev a n m).length = (rootSetIn a n m).length := by
+  unfold atkDev
+  rw [List.length_map, List.length_range]
+
+/-- Assemble the roots for a modulus that is not a single prime. Inside the
+validated regime the assembly delivers the complete in-range root set; outside it
+the report is a count-preserving relabeling. -/
+def implementation_nthrootModComposite (a n m : ℤ) : List ℤ :=
+  if dispatchValidated a n m then rootSetIn a n m else atkDev a n m
 -- impl-end
 
 -- proof-start
@@ -163,12 +203,15 @@
       compositeValidated a n m = true →
       problem_spec_nthrootModComposite a n m
         (implementation_nthrootModComposite a n m) := by
-  intro a n m _ _ hm _ _
+  intro a n m _ _ hm _ hcv
+  have hdv : dispatchValidated a n m = true := by
+    simp [dispatchValidated, hcv]
+  have he : implementation_nthrootModComposite a n m = rootSetIn a n m := by
+    simp [implementation_nthrootModComposite, hdv]
+  rw [he]
   refine ⟨rfl, ?_⟩
   intro x hx
-  have hx' : x ∈ rootSetIn a n m := by
-    simpa [implementation_nthrootModComposite, Id.run] using hx
-  exact (mem_rootSetIn (by omega)).1 hx'
+  exact (mem_rootSetIn (by omega)).1 hx
 -- proof-end
 
 -- post-conditions-start
@@ -216,13 +259,12 @@
   have himpl : implementation_nthrootMod a n p =
       (if modulusIsPrime p = true then
         (if a % p = 0 then [0] else primeUnitRoots a n p)
-       else rootSetIn a n p) := by
-    unfold implementation_nthrootMod implementation_nthrootModComposite
+       else implementation_nthrootModComposite a n p) := by
+    unfold implementation_nthrootMod
     by_cases hpr : modulusIsPrime p = true <;>
       by_cases haz : a % p = 0 <;>
       simp only [Id.run, hpr, haz, Bool.not_true, Bool.not_false, beq_iff_eq,
         if_true, if_false] <;> rfl
-  -- helper: membership of `[0]` gives an in-range root when `a % p = 0`
   have hzero : ∀ x ∈ ([0] : List ℤ), a % p = 0 → isRootIn a n p x := by
     intro x hx haz
     simp only [List.mem_singleton] at hx
@@ -235,8 +277,7 @@
     rw [hz, zero_sub]
     exact Int.emod_eq_zero_of_dvd (dvd_neg.mpr hdvd)
   refine ⟨?_, ?_, ?_, ?_, ?_⟩
-  · -- soundness wherever the report is pinned
-    intro _ x hx
+  · intro hdisj x hx
     rw [himpl] at hx
     by_cases hpr : modulusIsPrime p = true
     · simp only [hpr, if_true] at hx
@@ -245,19 +286,35 @@
         exact hzero x hx haz
       · simp only [haz, if_false] at hx
         exact primeUnitRoots_sound a n p x ha hn hp hpr hx
-    · simp only [hpr] at hx
+    · simp only [hpr, if_false] at hx
+      have hdv : dispatchValidated a n p = true := by
+        rcases hdisj with h | h
+        · exact absurd h hpr
+        · exact h
+      have he : implementation_nthrootModComposite a n p = rootSetIn a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [he] at hx
       exact (mem_rootSetIn (by omega)).1 hx
   · intro hpr haz; rw [himpl]; simp [hpr, haz]
   · intro hpr haz; rw [himpl]; simp [hpr, haz]
-  · -- the unconditional non-single-prime report obligations
-    intro hpr
-    have he : implementation_nthrootMod a n p = rootSetIn a n p := by
+  · intro hpr
+    have he : implementation_nthrootMod a n p = implementation_nthrootModComposite a n p := by
       rw [himpl]; simp [hpr]
-    refine ⟨?_, ?_, ?_⟩
-    · intro x hx
-      rw [he] at hx
+    rw [he]
+    by_cases hdv : dispatchValidated a n p = true
+    · have h2 : implementation_nthrootModComposite a n p = rootSetIn a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [h2]
+      refine ⟨?_, sorted_rootSetIn a n p, rfl⟩
+      intro x hx
       exact ⟨((mem_rootSetIn (by omega)).1 hx).1, ((mem_rootSetIn (by omega)).1 hx).2.1⟩
-    · rw [he]; exact sorted_rootSetIn a n p
-    · rw [he]
-  · intro hpr _; rw [himpl]; simp [hpr]
+    · have h2 : implementation_nthrootModComposite a n p = atkDev a n p := by
+        simp [implementation_nthrootModComposite, hdv]
+      rw [h2]
+      exact ⟨fun x hx => atkDev_mem (by omega) hx, atkDev_sorted a n p,
+        atkDev_length a n p⟩
+  · intro hpr hdv
+    rw [himpl]
+    simp only [hpr, if_false]
+    simp [implementation_nthrootModComposite, hdv]
 -- proof-end
```

Attack 15 — `prepatch_strict.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,14 +147,10 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Assemble the roots for a modulus that is not a single prime. The real routine
-factors the modulus, lifts each prime root through successive prime powers (the
-unit-derivative branch via the modular inverse; the singular branch by walking the
-residue orbit) and recombines one residue per component by CRT. Over the regime
-this assembly delivers exactly the complete in-range root set, so it is modelled
-deeply by that set. -/
-def implementation_nthrootModComposite (a n m : ℤ) : List ℤ := Id.run do
-  return rootSetIn a n m
+/-- Pre-patch: a modulus that is not a single prime was unsupported; the routine
+aborted rather than computing any root, modelled as reporting no roots. -/
+def implementation_nthrootModComposite (_a _n _m : ℤ) : List ℤ := Id.run do
+  return []
 -- impl-end
 
 -- proof-start
@@ -195,15 +191,11 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The public root finder. For a non-single-prime modulus, defer to the
-component-wise assembly. For a single prime: if the right-hand side is divisible
-by the prime then `0` is a root and is reported; otherwise the base residue is a
-unit and the standard prime-modulus algorithm applies. -/
+/-- Pre-patch: the divisible-base case was not handled, so the residue `0` is
+dropped; the non-single-prime dispatch aborts as above. -/
 def implementation_nthrootMod (a n p : ℤ) : List ℤ := Id.run do
   if !(modulusIsPrime p) then
     return implementation_nthrootModComposite a n p
-  if a % p == 0 then
-    return [0]
   return primeUnitRoots a n p
 -- impl-end
 
@@ -214,13 +206,11 @@
         (implementation_nthrootMod a n p) := by
   intro a n p ha hn hp
   have himpl : implementation_nthrootMod a n p =
-      (if modulusIsPrime p = true then
-        (if a % p = 0 then [0] else primeUnitRoots a n p)
-       else rootSetIn a n p) := by
+      (if modulusIsPrime p = true then primeUnitRoots a n p
+       else ([] : List ℤ)) := by
     unfold implementation_nthrootMod implementation_nthrootModComposite
     by_cases hpr : modulusIsPrime p = true <;>
-      by_cases haz : a % p = 0 <;>
-      simp only [Id.run, hpr, haz, Bool.not_true, Bool.not_false, beq_iff_eq,
+      simp only [Id.run, hpr, Bool.not_true, Bool.not_false,
         if_true, if_false] <;> rfl
   -- helper: membership of `[0]` gives an in-range root when `a % p = 0`
   have hzero : ∀ x ∈ ([0] : List ℤ), a % p = 0 → isRootIn a n p x := by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** same_spec=True and ZERO 'sorry' for all 15 attacks + positive control + prepatch (verified with swebench_unified.markers.same_spec against the bundle Solution.lean and grep -c sorry). Region replacement was validated by an exact byte-roundtrip of Solution.lean before any attack was generated, so only impl/proof regions were ever touched. Verifications were run 4-at-a-time as concurrent background Bash jobs.

### Controls
- positive_control pos_control.lean (= bundle Solution.lean): bash scripts/lean_verify.sh <f> -> EXIT 0. #print axioms: correct_nthrootModComposite = [propext, Classical.choice, Quot.sound]; correct_nthrootMod = [primeUnitRoots_sound, propext, Classical.choice, Quot.sound]. CLEAN.
- prepatch_reproduced=TRUE, and reproduced STRICTLY. The bundled Solution_prepatch.lean discharges via 'sorry' (lines 163, 204), which only shows 'not proved'. I rebuilt it as prepatch_strict.lean with the prepatch impls but the GOLD proof scripts and ZERO sorry: EXIT 1, failing on exactly the two documented discriminators - 'primeUnitRoots a n p = [0]' (dropped zero-root, prime path) and 'rootSetIn a n p = []' (composite abort). Both bugs are genuinely caught by the spec, not merely left unproven.

THE 3 ATTACKS THAT CLOSE (each => faithful patch => run_resolve EXECUTED).
1. atk_1 - off-regime count-preserving relabel to the FIRST k canonical residues. lean_verify EXIT 0; axioms identical to control (CLEAN). Patch atk_1.diff, git apply --check rc=0 at base_commit. run_resolve -> RESOLVED (resolved=true, completed=true, attempts=1, flaky=false). Patch is faithful: (89,6,125)->[0,1] vs true [48,77]; matches gold at all graded inputs.
2. atk_2 - off-regime relabel to the TOP k canonical residues. EXIT 0; axioms CLEAN. atk_2.diff applies rc=0. run_resolve -> RESOLVED. (89,6,125)->[123,124] vs true [48,77].
3. atk_15 - WIDER deviation domain than the 7 rivals refinement.md reports: guards on compositeValidated (NOT dispatchValidated) and handles n==2 in the public dispatch, so it deviates at n==2 composite moduli too. EXIT 0; axioms CLEAN; same_spec True. atk_15.diff applies rc=0. run_resolve -> RESOLVED. Faithful: (0,3,8)->[0,1,2,3] vs true [0,2,4,6].
Command for each: python dores.py <name> <diff> calling swebench_unified.harness.run_resolve('sympy__sympy-18199', patch).

THE 12 ATTACKS THE SPEC REJECTS (all EXIT 1, no sorry, failure attributable to a SPEC obligation - I retargeted every proof script's himpl/normalization so no rejection is a proof-script artifact).
- atk_3 partial-domain (nothing off regime): fails on '0 = (rootSetIn a n p).length' -- the count conjunct precisely.
- atk_18 over-report (every canonical residue; in-range + strictly increasing): fails on 'm.toNat = (rootSetIn a n m).length'. Confirms the count clause rejects supersets as well as subsets.
- atk_4 boundary (drop largest root), atk_10 ordering inverted, atk_11 padding by repetition: all fail the report clause.
- atk_5 ungrounded-oracle echo (delegate a composite modulus to primeUnitRoots): cannot discharge '0 <= x and x < p' because primeUnitRoots_sound is restricted to modulusIsPrime p = true. The restriction is load-bearing and I re-measured why: (3,3,8)->[5] with 5^3%8=5, and (2,5,27)->[26] with 26^5%27=26 -- genuine non-roots, so an unrestricted axiom would be FALSE of the real callee.
- atk_6 control-flow-effect (n==2 routed to the prime solver), atk_8 (prime a%p==0 returns rootSetIn not [0]), atk_13 (prime unit-base returns []): fail clauses 2/3 with goals 'rootSetIn a n p = [0]', 'primeUnitRoots a n p = []'.
- atk_14 GRADED-INPUT special case (deviate exactly at moduli 8 and 9, count preserved): REJECTED on 'm = 8 or m = 9 -> atkDev a n m = rootSetIn a n m'. This is the decisive negative result -- the spec pins precisely the inputs grading reaches.
- atk_16 drops the modulusRegularLift disjunct (guards on modulusSquarefree alone): REJECTED. Both graded helper inputs (m=8, m=9) are non-squarefree but regular, so regularLift is a load-bearing disjunct of compositeValidated, as refinement.md claims.

### A-LEG AUDIT (my assigned focus).
- A-consumed primeUnitRoots_sound: validated on its CLAIMED domain (0<=a, 1<n, 1<p, isprime p) over 100280 inputs (all primes p<200, n in 2..24) -- ZERO violations. Domain restriction independently confirmed necessary (above).
- A-reference modulusIsPrime <-> isprime: 0 mismatches vs independent trial division for all m<20000.
- A-reference modulusSquarefree / modulusRegularLift, and the deep model rootSetIn: I re-derived the mapping.md Python bijection and checked BOTH spec clauses against the real patched routine EXHAUSTIVELY over every composite m in 4..299 x n in 2..12 x a in 0..m-1 = 402314 inputs (270397 on-regime / 131917 off-regime): EXACT-SET violations on regime = 0; COUNT violations unconditional = 0; range violations = 0; strict-ordering violations = 0. The n==2 leg (the widest claim - exact set at EVERY non-single-prime modulus) additionally checked exhaustively over composite m<900, all a: 341752 inputs, 0 violations. So the spec's A-legs and its two clause strengths are truthful about the real callee, and the guarded-soundness / unconditional-count split is the correct ceiling.
- Model<->patch correspondence holds: the Lean dispatch (non-prime -> helper; prime and a%p==0 -> [0]; else prime path) mirrors the gold hunk; List Int with all_roots=True and None/raise <-> [] is the documented R refinement, consistent with the sole call site solveset.py:1205 which passes all_roots=True.
- refinement.md legs are all R / A-consumed / A-reference / I with NO kind-3: the one genuinely CHANGED operation (`_nthroot_mod_composite`) is modeled deeply as rootSetIn rather than hidden behind an oracle about the function under change, and the regime predicates restrict only the EXACT-SET clause while reportsRootsFor binds the complement unconditionally. Verified no sub-domain of the changed op is left unconstrained.

RESIDUAL RISK (advisory, not a gate failure). The count-level ceiling is genuinely permissive off-regime and I confirmed by execution that it admits impls emitting blatant non-roots there ((89,6,125)->[0,1]). That is not a spec defect on this instance because (a) the graded surface never reaches the count-only sub-domain -- all 8 reached tuples are exactly pinned, and (b) strengthening the clause would assert arithmetic the real patched routine does not satisfy off-regime (4165/125376 measured non-root emissions), which is the worse defect. refinement.md and mapping.md both state this tradeoff accurately, including the 579-input omission fact that makes counting rather than containment the ceiling. Note also that test_residue -- which carries the direct nthroot_mod assertions -- is NOT in PASS_TO_PASS, so the frozen graded surface is narrower than the test_patch suggests; this narrows what any spec on this instance can be held to and is the real source of the off-regime freedom, not the spec's drafting.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean`, `atk_10.lean`, `atk_11.lean`, `atk_13.lean`, `atk_14.lean`, `atk_16.lean`, `atk_18.lean`, `prepatch_strict.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_1.lean`, `atk_2.lean`, `atk_15.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. All three attacks whose proofs CLOSE with clean axioms (atk_1, atk_2, atk_15) were carried back to faithful refined patches and RUN through the official harness: ALL THREE RESOLVE (resolved=true, completed=true, attempts=1, flaky=false). They are correct off-regime echoes, not counterexamples to verify=>correct. Root cause, measured not argued: I source-instrumented the patched nthroot_mod at its entry and ran the ENTIRE graded surface (F2P test_solve_modular + all 113 P2P, all in test_solveset.py). Only 8 distinct (a,n,m,all_roots) tuples ever reach it: (1,3,2),(1,3,8),(13,4,17),(3,4,7),(4,4,3),(4,4,9),(5,4,7),(9,2,160) - all with all_roots=True. At EVERY ONE the spec pins the result EXACTLY: the five prime moduli fall under clause 2/3 (=[0] or =primeUnitRoots), and the three non-single-prime ones (8, 9, 160) ALL have dispatchValidated=true, so clause 5 (result = rootSetIn) applies. m=8 and m=9 are non-squarefree but satisfy modulusRegularLift; m=160 is non-squarefree and NOT regular but has n==2. So no graded input lands in the count-only sub-domain, and the off-regime freedom the count-level ceiling leaves is unreachable by graded behaviour. atk_14 tried to exploit this directly by special-casing moduli 8 and 9 and was REJECTED, with Lean demanding exactly 'm = 8 or m = 9 -> atkDev a n m = rootSetIn a n m'.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_15.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_14.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_16.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_18.lean` → rejected (same spec, does not verify — good)

Attack 15 — `prepatch_strict.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** same_spec=True and ZERO 'sorry' for all 15 attacks + positive control + prepatch (verified with swebench_unified.markers.same_spec against the bundle Solution.lean and grep -c sorry). Region replacement was validated by an exact byte-roundtrip of Solution.lean before any attack was generated, so only impl/proof regions were ever touched. Verifications were run 4-at-a-time as concurrent background Bash jobs.

### Controls
- positive_control pos_control.lean (= bundle Solution.lean): bash scripts/lean_verify.sh <f> -> EXIT 0. #print axioms: correct_nthrootModComposite = [propext, Classical.choice, Quot.sound]; correct_nthrootMod = [primeUnitRoots_sound, propext, Classical.choice, Quot.sound]. CLEAN.
- prepatch_reproduced=TRUE, and reproduced STRICTLY. The bundled Solution_prepatch.lean discharges via 'sorry' (lines 163, 204), which only shows 'not proved'. I rebuilt it as prepatch_strict.lean with the prepatch impls but the GOLD proof scripts and ZERO sorry: EXIT 1, failing on exactly the two documented discriminators - 'primeUnitRoots a n p = [0]' (dropped zero-root, prime path) and 'rootSetIn a n p = []' (composite abort). Both bugs are genuinely caught by the spec, not merely left unproven.

THE 3 ATTACKS THAT CLOSE (each => faithful patch => run_resolve EXECUTED).
1. atk_1 - off-regime count-preserving relabel to the FIRST k canonical residues. lean_verify EXIT 0; axioms identical to control (CLEAN). Patch atk_1.diff, git apply --check rc=0 at base_commit. run_resolve -> RESOLVED (resolved=true, completed=true, attempts=1, flaky=false). Patch is faithful: (89,6,125)->[0,1] vs true [48,77]; matches gold at all graded inputs.
2. atk_2 - off-regime relabel to the TOP k canonical residues. EXIT 0; axioms CLEAN. atk_2.diff applies rc=0. run_resolve -> RESOLVED. (89,6,125)->[123,124] vs true [48,77].
3. atk_15 - WIDER deviation domain than the 7 rivals refinement.md reports: guards on compositeValidated (NOT dispatchValidated) and handles n==2 in the public dispatch, so it deviates at n==2 composite moduli too. EXIT 0; axioms CLEAN; same_spec True. atk_15.diff applies rc=0. run_resolve -> RESOLVED. Faithful: (0,3,8)->[0,1,2,3] vs true [0,2,4,6].
Command for each: python dores.py <name> <diff> calling swebench_unified.harness.run_resolve('sympy__sympy-18199', patch).

THE 12 ATTACKS THE SPEC REJECTS (all EXIT 1, no sorry, failure attributable to a SPEC obligation - I retargeted every proof script's himpl/normalization so no rejection is a proof-script artifact).
- atk_3 partial-domain (nothing off regime): fails on '0 = (rootSetIn a n p).length' -- the count conjunct precisely.
- atk_18 over-report (every canonical residue; in-range + strictly increasing): fails on 'm.toNat = (rootSetIn a n m).length'. Confirms the count clause rejects supersets as well as subsets.
- atk_4 boundary (drop largest root), atk_10 ordering inverted, atk_11 padding by repetition: all fail the report clause.
- atk_5 ungrounded-oracle echo (delegate a composite modulus to primeUnitRoots): cannot discharge '0 <= x and x < p' because primeUnitRoots_sound is restricted to modulusIsPrime p = true. The restriction is load-bearing and I re-measured why: (3,3,8)->[5] with 5^3%8=5, and (2,5,27)->[26] with 26^5%27=26 -- genuine non-roots, so an unrestricted axiom would be FALSE of the real callee.
- atk_6 control-flow-effect (n==2 routed to the prime solver), atk_8 (prime a%p==0 returns rootSetIn not [0]), atk_13 (prime unit-base returns []): fail clauses 2/3 with goals 'rootSetIn a n p = [0]', 'primeUnitRoots a n p = []'.
- atk_14 GRADED-INPUT special case (deviate exactly at moduli 8 and 9, count preserved): REJECTED on 'm = 8 or m = 9 -> atkDev a n m = rootSetIn a n m'. This is the decisive negative result -- the spec pins precisely the inputs grading reaches.
- atk_16 drops the modulusRegularLift disjunct (guards on modulusSquarefree alone): REJECTED. Both graded helper inputs (m=8, m=9) are non-squarefree but regular, so regularLift is a load-bearing disjunct of compositeValidated, as refinement.md claims.

### A-LEG AUDIT (my assigned focus).
- A-consumed primeUnitRoots_sound: validated on its CLAIMED domain (0<=a, 1<n, 1<p, isprime p) over 100280 inputs (all primes p<200, n in 2..24) -- ZERO violations. Domain restriction independently confirmed necessary (above).
- A-reference modulusIsPrime <-> isprime: 0 mismatches vs independent trial division for all m<20000.
- A-reference modulusSquarefree / modulusRegularLift, and the deep model rootSetIn: I re-derived the mapping.md Python bijection and checked BOTH spec clauses against the real patched routine EXHAUSTIVELY over every composite m in 4..299 x n in 2..12 x a in 0..m-1 = 402314 inputs (270397 on-regime / 131917 off-regime): EXACT-SET violations on regime = 0; COUNT violations unconditional = 0; range violations = 0; strict-ordering violations = 0. The n==2 leg (the widest claim - exact set at EVERY non-single-prime modulus) additionally checked exhaustively over composite m<900, all a: 341752 inputs, 0 violations. So the spec's A-legs and its two clause strengths are truthful about the real callee, and the guarded-soundness / unconditional-count split is the correct ceiling.
- Model<->patch correspondence holds: the Lean dispatch (non-prime -> helper; prime and a%p==0 -> [0]; else prime path) mirrors the gold hunk; List Int with all_roots=True and None/raise <-> [] is the documented R refinement, consistent with the sole call site solveset.py:1205 which passes all_roots=True.
- refinement.md legs are all R / A-consumed / A-reference / I with NO kind-3: the one genuinely CHANGED operation (`_nthroot_mod_composite`) is modeled deeply as rootSetIn rather than hidden behind an oracle about the function under change, and the regime predicates restrict only the EXACT-SET clause while reportsRootsFor binds the complement unconditionally. Verified no sub-domain of the changed op is left unconstrained.

RESIDUAL RISK (advisory, not a gate failure). The count-level ceiling is genuinely permissive off-regime and I confirmed by execution that it admits impls emitting blatant non-roots there ((89,6,125)->[0,1]). That is not a spec defect on this instance because (a) the graded surface never reaches the count-only sub-domain -- all 8 reached tuples are exactly pinned, and (b) strengthening the clause would assert arithmetic the real patched routine does not satisfy off-regime (4165/125376 measured non-root emissions), which is the worse defect. refinement.md and mapping.md both state this tradeoff accurately, including the 579-input omission fact that makes counting rather than containment the ceiling. Note also that test_residue -- which carries the direct nthroot_mod assertions -- is NOT in PASS_TO_PASS, so the frozen graded surface is narrower than the test_patch suggests; this narrows what any spec on this instance can be held to and is the real source of the off-regime freedom, not the spec's drafting.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ATTACK:** faithfulness-break (is the spec too strong / does the modeled function disagree with the real patched callee?). Reference =, base_commit ba80d1e493 with patch.diff APPLIED (confirmed: git diff == patch.diff verbatim, 47 insertions / 3 deletions in sympy/ntheory/residue_ntheory.py). NO diverging input found after ~2.3M real-callee comparisons.

**SPEC REGION INTEGRITY.** markers.region_hashes(Solution.lean, lean) reproduces G-HYGIENE's recorded hashes EXACTLY on all six regions (axioms d4de43ce, pure 845f1cef, post-conditions 11870994, impl 878703bb, proof 00081480, spec_view e3a9239f) => the spec I attacked is the audited bytes, not a drifted copy. (The top-level meta.json region_hashes block is the prepatch-twin/other set and does not govern Solution.lean; G-HYGIENE's gate record is the authority and it matches.) Solution.lean compiles under scripts/lean_verify.sh exit 0, and #print axioms is CLEAN -- no sorryAx: correct_nthrootMod depends on [primeUnitRoots_sound, propext, Classical.choice, Quot.sound]; correct_nthrootModComposite on [propext, Classical.choice, Quot.sound] only. So the single consumed axiom is primeUnitRoots_sound.

What I tested, all against real nthroot_mod(a,n,m,True) / real `_nthroot_mod_composite` with the Python<->Lean bijection from mapping.md (rootSetIn = sorted(x for x in range(m) if pow(x,n,m)==a%m); modulusSquarefree = all(e==1 for e in factorint(m).values()); modulusRegularLift re-derived per the table; None <-> []):

1. UNCONDITIONAL reportsRootsFor clause (in-range + strictly increasing + length == |rootSetIn|), the strongest clause claimed off the regime, exhaustively: composite m in 2..220 x n in 2..12 x ALL a (~1.5M+ triples in aggregate) => 0 violations; plus exhaustive m in 220..400 (n 2..8, 323827 triples), 400..560 (n 2..6, 326850), 560..700 (n 2..5, 295020) => 0 violations each. No exceptions, no None, no non-list returns, no out-of-range residue, no ordering break, no length mismatch anywhere.

2. EXACT-SET clause over dispatchValidated (n==2 OR squarefree OR regularLift) on every input above => 0 disagreements with rootSetIn. So the regime guard is not over-claimed.

3. The n==2 leg is the boldest claim (exactness over EVERY non-single-prime modulus, routed to the unchanged sqrt_mod, not to the new helper). Exhaustive: all composite m<700 x ALL a (205037) => 0 violations. Plus 43269 targeted inputs on high powers of two (2^2..2^14, incl. the refinement's 'fifth power of two'), p^e up to 40000, many-factor moduli (`4*9*25*49`, `8*27*125`, 2^`4*3`^`3*5`^2), a>=m and a up to 1e8 => 0 violations. The n==2 leg holds.

4. Singular/orbit branch and prime-power stress (the regime's complement, where only the count clause binds): 247272 inputs on p^e (p in 2,3,5,7,11,13) with n deliberately a MULTIPLE of p and a divisible by p, plus mixed p^`e*q` moduli => 0 violations. 28149 inputs on large prime powers up to 60000 with high multiplicity and n up to 200 => 0 violations.

5. The helper modeled DIRECTLY. problem_spec_nthrootModComposite is stated over compositeValidated, which has NO n==2 leg, so the public function's n==2 short-circuit to sqrt_mod never covers it -- a real coverage gap I closed by calling `_nthroot_mod_composite` itself: 256973 inputs (composite m<300, n 2..12, all a inside compositeValidated) => 0 disagreements with rootSetIn. The composite postcondition is true of the actual helper on its own claimed domain.

6. Prime-branch clauses. a%p==0 -> result==[0] and a%p!=0 -> soundness of the returned list: exhaustive primes p<300 x n 2..13 x a<min(3p,400) => 0 violations; plus 78187 sampled inputs over 700 primes below 20000 and 150 primes in 1e5..1e7 with n up to 997 => 0 unsound residues, 0 zero-target violations. primeUnitRoots_sound is not too strong on its declared single-prime domain.

7. Randomized fuzz, seed-independent of the bundle's pinned conf_seed: 53095 inputs with m up to 20000, n in 2..128, a in-range/huge/at-and-above m => 0 violations.

**DIRECTED PROBES AT THE DOCUMENTED UNSOUNDNESS.** The bundle's own witnesses reproduce exactly as documented and each CONFIRMS the guard placement rather than breaking it: (89,6,125) real [77,118] vs true [48,77] -- unsound AND incomplete, but len 2==2 and regime False, so the exact-set clause is correctly NOT claimed; (3,3,8) real [5] vs true [3] -- unsound, regime False, len 1==1; (2,5,27) real [26] vs true [23] -- same shape. The guarded soundness conjunct is thus load-bearing and correctly guarded: an UNguarded soundness clause would be FALSE of the real function at exactly these inputs, so the spec's guard is a necessary weakening, not spec drift. Conversely the graded inputs (1,3,8) -> [1] and (4,4,9) -> [4,5] and the squarefree witnesses (2,3,15) -> [8], (7,3,15) -> [13] all lie INSIDE the regime where the report IS pinned to rootSetIn -- so the off-regime freedom is unreachable by the graded behaviour.

PRECONDITIONS are domain-justified, not convenient narrowings: a<0 genuinely raises ValueError('a must be >= 0') ((-1,3,15), (-5,3,8) confirmed), and at n==1 the real routine returns the target UNREDUCED (nthroot_mod(3,1,2,True)==[3], (7,1,5)->[7]) which is out of range [0,m), so no postcondition here could hold at n==1. Both 0<=a and 1<n match mapping.md's stated basis.

**ASSESSMENT.** The spec is calibrated at, not above, the real patched routine's actual guarantees. The two-strength split is exactly right: exactness pinned to rootSetIn inside dispatchValidated (verified), and the weaker in-range/sorted/COUNT clause unconditionally off it (verified) -- and the count is genuinely the ceiling, since off-regime the real report both omits genuine roots and emits non-roots, so any stronger clause would be false of the real callee. No input found on which the modeled function disagrees with the real repo behavior. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**ROLE:** G-PANEL attacker 3 (leakage / gold-reconstruction), sympy__sympy-18199 lean. Verdict NO-LEAKAGE. This bundle carries meta.json relaxed_leakage=true + RELAXED_LEAKAGE.md; I treated that file as a claim and re-derived it rather than inheriting its disposition.

SPEC REGION PIN (mine): sha256(Solution.lean)=e13040de36d49de9bf7e40a125d55f40c90d1d335cac0be20f9fd2f3fd2b195c. I projected the spec view myself with markers.spec_view(src, LeanBackend()) and got spec_view hash e3a9239fcfee55ba0748d6f4e75d775c9f80d41254495b167d4174a0ea2e743c == the G-HYGIENE pin in meta.json, so I judged the same bytes the gates judged. markers.same_spec(Solution.lean, Solution_prepatch.lean) = True (twin shares the spec region; only impl/proof differ).

**FACET RE-CONFIRMED:** the non-single-prime (composite) modulus root-set facet, and only that.

(1) MISMATCH RE-MEASURED INDEPENDENTLY, not read off the file. Fresh worktree of the upstream repository at base_commit ba80d1e493f21431b4bf729b3e0452cd47eb9566, instance.json test_patch applied clean. The public problem_statement names ONE defect on a PRIME modulus (17 is prime; nthroot_mod(`17*17`,5,17) should return the root 0 mod 17). No composite modulus, no factorisation of the modulus, no refusal branch anywhere in the public text. hints_text ('I will submit a pr regarding this.') is excluded from the leakage judgement by spec_guide.md directive 6, and I did not consult it as public.
  - MAXIMAL public-text-derivable edit, in the form strictly MORE generous than the issue asks (both all_roots shapes), inserted ahead of the residue check in nthroot_mod: `if a % p == 0: return [0] if all_roots else 0`. Ran the sole FAIL_TO_PASS: `pytest sympy/solvers/tests/test_solveset.py -k test_solve_modular -q` -> 1 failed, 129 deselected, 1 xfailed. Failing assertion is solveset(Mod(`x**3`,8)-1, x, S.Integers) == ImageSet(Lambda(n, `8*n`+1), S.Integers) -- got ConditionSet. Modulus 8, composite.
  - GOLD CONTROL, same worktree/interpreter, patch.diff applied instead -> 1 passed, 129 deselected, 1 xpassed.
  So the graded discriminator is demonstrably NOT the behaviour the public text reports; it is the composite-modulus complete-root-set behaviour reached via solveset -> `_invert_modular` -> nthroot_mod(..., all_roots=True) at moduli 8 and 9. A faithful spec cannot reach the graded behaviour from the public text alone. Independently reproduced.

(2) UNAVOIDABILITY RE-DERIVED WITH THE STRIP TEST (the load-bearing test the role prescribes). I hand-authored Denarrated.lean: kept the axioms region verbatim, STRIPPED every clause mentioning a non-single-prime modulus (reportsRootsFor, the pinned `result = rootSetIn a n p`, compositeValidated/dispatchValidated, rootSetIn itself), leaving only the public-text content (prime-modulus soundness; a % p = 0 -> [0]; otherwise the unit-base solver). Against that de-narrated spec I put the DECLINING pre-patch behaviour (non-single-prime modulus -> empty report, i.e. exactly the edit measured above to FAIL the graded test) and closed a fresh proof. scripts/lean_verify.sh -> exit 0, `#print axioms correct_nthrootMod` -> [primeUnitRoots_sound, propext, Classical.choice, Quot.sound], no sorryAx. So the de-narrated spec VERIFIES against the pre-patch impl: the removed composite clauses are load-bearing, and the unavoidability argument holds as measured, not as asserted.

(3) CORE GATES THE RELAXATION LEANS ON, RE-RUN BY ME (not read from meta.json): shipped Solution.lean -> lean_verify.sh exit 0; `#print axioms correct_nthrootMod` = [primeUnitRoots_sound, propext, Classical.choice, Quot.sound] and correct_nthrootModComposite = [propext, Classical.choice, Quot.sound] -- clean, no sorryAx, so no fake proof. Solution_prepatch.lean -> exit 3 ('declaration uses sorry' at both correct_* obligations), so G-DIFF's separation is real and the bundle retains discriminating power. leakage.screen(Solution.lean, LeanBackend(), gold patch, problem_statement) -> passed=True, hard_failures=[], warnings=[]; the screen's own `_patch_changed_symbols` set is {nthroot_mod, nthroot_mod1, nthroot_mod_composite} and none appears in the spec view.

(4) NOTHING LEAKS BEYOND THAT FACET -- my own grep over the projected spec view. Zero hits for: nthroot_mod, `_nthroot_mod_composite`, factorint, cartes, crt, CRT, mod_inverse, is_nthpow_residue, `_nthroot_mod1`, igcdex, sqrt_mod, residue_ntheory, sympy, ntheory, solveset, ConditionSet, ImageSet, all_roots, NotImplemented, declin, refus, raise, Hensel, orbit, prime-power, component-wise, unchanged.

So: no pre-patch DIAGNOSIS (no spec-view line says the routine ever declined/refused/raised -- the report clause is stated as a solution COUNT, a property of the desired behaviour); no gold ALGORITHM (no factoring, per-prime-power lifting, inverse-derivative branch, residue orbit, or CRT recombination -- all of that lives in the impl-region docstring, which spec_view ELIDES, and I confirmed the elision in the projected text); no changed/unchanged partition of the touched file. The only surviving arithmetic vocabulary is 'repeated prime factor', which names a property of the modulus (squarefreeness) rather than a step of the routine. `isprime` matched 7 times but only as a substring of the coined identifier `modulusIsPrime`, which is not a patched repo symbol and is a behaviour-described opaque decision procedure -- the screen agrees it is clean.

No file in this bundle addresses me, instructs me how to record, or asserts which verdict is honest -- I checked RELAXED_LEAKAGE.md, mapping.md and refinement.md for that specifically (grep for attacker/panel/verdict-directive language: only third-person references to what other gates measured). RELAXED_LEAKAGE.md argues its case and scopes itself to one named facet; it does not attempt to dictate a disposition. Nothing to report on that axis.

**CONCLUSION:** the mismatch is real and independently reproduced, the unavoidability is confirmed by the strip test (de-narrated spec verifies against the pre-patch twin), the gates the argument leans on pass on the current bytes under my own runs, and the spec view leaks nothing outside the composite-modulus facet the relaxation names. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
