# P2 adversarial audit — sympy__sympy-15809

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `Solution.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-satisfying wrong impl exists. The spec is value-determining: over the LinearOrder EVal = WithTop (WithBot Q), problem_spec_min's clauses (∀ x∈args, v≤x) ∧ (args≠[]→v∈args) ∧ (args=[]→v=⊤) uniquely pin v to the exact minimum (symmetrically for max). Machine-proved as spec_min_unique in refute.lean. Every same-spec wrong impl differs from the gold min/max on some input and is provably spec-violating (concrete counterexamples, e.g. atk_5 constant ⊤ fails on args=[0] since ⊤∉[0]; atk_6 head fails on [1,0] since 1≤0 is false). Therefore no closing correct_ proof can exist -> patches step 2 is vacuous.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -39,6 +39,7 @@
 
 -- impl-start
 def implementation_min (args : List EVal) : Except Unit EVal := Id.run do
+  if args = [] then return Except.error ()
   let mut acc : EVal := ⊤
   for x in args do
     acc := min acc x
@@ -46,65 +47,9 @@
 -- impl-end
 
 -- proof-start
-theorem min_fold_eq (args : List EVal) (init : EVal) :
-    (Id.run (forIn args init (fun (x r : EVal) => (pure (ForInStep.yield (min r x)) : Id _))))
-      = List.foldl min init args := by
-  induction args generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [List.foldl_cons]
-    exact ih (min init a)
-
-theorem foldl_min_le (init x : EVal) (as : List EVal) :
-    List.foldl min (min init x) as ≤ min init x := by
-  induction as generalizing init x with
-  | nil => simp
-  | cons b bs ih =>
-    rw [List.foldl_cons]
-    exact le_trans (ih (min init x) b) (min_le_left _ _)
-
-theorem foldl_min_props (args : List EVal) (init : EVal) :
-    (∀ x ∈ args, List.foldl min init args ≤ x) ∧
-    (List.foldl min init args = init ∨ List.foldl min init args ∈ args) := by
-  induction args generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.foldl_cons]
-    obtain ⟨hmem, hcase⟩ := ih (min init a)
-    refine ⟨?_, ?_⟩
-    · intro x hx
-      rcases List.mem_cons.mp hx with rfl | hx
-      · exact le_trans (foldl_min_le init x as) (min_le_right _ _)
-      · exact hmem x hx
-    · rcases hcase with h | h
-      · rw [h]
-        rcases min_choice init a with hh | hh
-        · exact Or.inl hh
-        · exact Or.inr (by rw [hh]; exact List.mem_cons_self)
-      · exact Or.inr (List.mem_cons_of_mem _ h)
-
-theorem impl_min_eq (args : List EVal) :
-    implementation_min args = Except.ok (List.foldl min ⊤ args) := by
-  unfold implementation_min
-  simp only [Id.run, bind]
-  rw [← min_fold_eq args ⊤]
-  rfl
-
 theorem correct_min : ∀ args : List EVal,
     problem_spec_min args (implementation_min args) := by
-  intro args
-  refine ⟨List.foldl min ⊤ args, impl_min_eq args, ?_, (foldl_min_props args ⊤).1, ?_⟩
-  · intro h; subst h; rfl
-  · intro hne
-    cases args with
-    | nil => exact absurd rfl hne
-    | cons a as =>
-      rw [List.foldl_cons, min_top_left]
-      rcases (foldl_min_props as a).2 with h | h
-      · rw [h]; exact List.mem_cons_self
-      · exact List.mem_cons_of_mem _ h
+  sorry
 -- proof-end
 
 /-! ## Maximum reduction -/
@@ -129,63 +74,7 @@
 -- impl-end
 
 -- proof-start
-theorem max_fold_eq (args : List EVal) (init : EVal) :
-    (Id.run (forIn args init (fun (x r : EVal) => (pure (ForInStep.yield (max r x)) : Id _))))
-      = List.foldl max init args := by
-  induction args generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [List.foldl_cons]
-    exact ih (max init a)
-
-theorem le_foldl_max (init x : EVal) (as : List EVal) :
-    max init x ≤ List.foldl max (max init x) as := by
-  induction as generalizing init x with
-  | nil => simp
-  | cons b bs ih =>
-    rw [List.foldl_cons]
-    exact le_trans (le_max_left _ _) (ih (max init x) b)
-
-theorem foldl_max_props (args : List EVal) (init : EVal) :
-    (∀ x ∈ args, x ≤ List.foldl max init args) ∧
-    (List.foldl max init args = init ∨ List.foldl max init args ∈ args) := by
-  induction args generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.foldl_cons]
-    obtain ⟨hmem, hcase⟩ := ih (max init a)
-    refine ⟨?_, ?_⟩
-    · intro x hx
-      rcases List.mem_cons.mp hx with rfl | hx
-      · exact le_trans (le_max_right _ _) (le_foldl_max init x as)
-      · exact hmem x hx
-    · rcases hcase with h | h
-      · rw [h]
-        rcases max_choice init a with hh | hh
-        · exact Or.inl hh
-        · exact Or.inr (by rw [hh]; exact List.mem_cons_self)
-      · exact Or.inr (List.mem_cons_of_mem _ h)
-
-theorem impl_max_eq (args : List EVal) :
-    implementation_max args = Except.ok (List.foldl max ⊥ args) := by
-  unfold implementation_max
-  simp only [Id.run, bind]
-  rw [← max_fold_eq args ⊥]
-  rfl
-
 theorem correct_max : ∀ args : List EVal,
     problem_spec_max args (implementation_max args) := by
-  intro args
-  refine ⟨List.foldl max ⊥ args, impl_max_eq args, ?_, (foldl_max_props args ⊥).1, ?_⟩
-  · intro h; subst h; rfl
-  · intro hne
-    cases args with
-    | nil => exact absurd rfl hne
-    | cons a as =>
-      rw [List.foldl_cons, max_bot_left]
-      rcases (foldl_max_props as a).2 with h | h
-      · rw [h]; exact List.mem_cons_self
-      · exact List.mem_cons_of_mem _ h
+  sorry
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -39,72 +39,19 @@
 
 -- impl-start
 def implementation_min (args : List EVal) : Except Unit EVal := Id.run do
-  let mut acc : EVal := ⊤
-  for x in args do
-    acc := min acc x
-  return Except.ok acc
+  match args with
+  | [] => return Except.ok ⊥
+  | _ =>
+    let mut acc : EVal := ⊤
+    for x in args do
+      acc := min acc x
+    return Except.ok acc
 -- impl-end
 
 -- proof-start
-theorem min_fold_eq (args : List EVal) (init : EVal) :
-    (Id.run (forIn args init (fun (x r : EVal) => (pure (ForInStep.yield (min r x)) : Id _))))
-      = List.foldl min init args := by
-  induction args generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [List.foldl_cons]
-    exact ih (min init a)
-
-theorem foldl_min_le (init x : EVal) (as : List EVal) :
-    List.foldl min (min init x) as ≤ min init x := by
-  induction as generalizing init x with
-  | nil => simp
-  | cons b bs ih =>
-    rw [List.foldl_cons]
-    exact le_trans (ih (min init x) b) (min_le_left _ _)
-
-theorem foldl_min_props (args : List EVal) (init : EVal) :
-    (∀ x ∈ args, List.foldl min init args ≤ x) ∧
-    (List.foldl min init args = init ∨ List.foldl min init args ∈ args) := by
-  induction args generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.foldl_cons]
-    obtain ⟨hmem, hcase⟩ := ih (min init a)
-    refine ⟨?_, ?_⟩
-    · intro x hx
-      rcases List.mem_cons.mp hx with rfl | hx
-      · exact le_trans (foldl_min_le init x as) (min_le_right _ _)
-      · exact hmem x hx
-    · rcases hcase with h | h
-      · rw [h]
-        rcases min_choice init a with hh | hh
-        · exact Or.inl hh
-        · exact Or.inr (by rw [hh]; exact List.mem_cons_self)
-      · exact Or.inr (List.mem_cons_of_mem _ h)
-
-theorem impl_min_eq (args : List EVal) :
-    implementation_min args = Except.ok (List.foldl min ⊤ args) := by
-  unfold implementation_min
-  simp only [Id.run, bind]
-  rw [← min_fold_eq args ⊤]
-  rfl
-
 theorem correct_min : ∀ args : List EVal,
     problem_spec_min args (implementation_min args) := by
-  intro args
-  refine ⟨List.foldl min ⊤ args, impl_min_eq args, ?_, (foldl_min_props args ⊤).1, ?_⟩
-  · intro h; subst h; rfl
-  · intro hne
-    cases args with
-    | nil => exact absurd rfl hne
-    | cons a as =>
-      rw [List.foldl_cons, min_top_left]
-      rcases (foldl_min_props as a).2 with h | h
-      · rw [h]; exact List.mem_cons_self
-      · exact List.mem_cons_of_mem _ h
+  sorry
 -- proof-end
 
 /-! ## Maximum reduction -/
@@ -129,63 +76,7 @@
 -- impl-end
 
 -- proof-start
-theorem max_fold_eq (args : List EVal) (init : EVal) :
-    (Id.run (forIn args init (fun (x r : EVal) => (pure (ForInStep.yield (max r x)) : Id _))))
-      = List.foldl max init args := by
-  induction args generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [List.foldl_cons]
-    exact ih (max init a)
-
-theorem le_foldl_max (init x : EVal) (as : List EVal) :
-    max init x ≤ List.foldl max (max init x) as := by
-  induction as generalizing init x with
-  | nil => simp
-  | cons b bs ih =>
-    rw [List.foldl_cons]
-    exact le_trans (le_max_left _ _) (ih (max init x) b)
-
-theorem foldl_max_props (args : List EVal) (init : EVal) :
-    (∀ x ∈ args, x ≤ List.foldl max init args) ∧
-    (List.foldl max init args = init ∨ List.foldl max init args ∈ args) := by
-  induction args generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.foldl_cons]
-    obtain ⟨hmem, hcase⟩ := ih (max init a)
-    refine ⟨?_, ?_⟩
-    · intro x hx
-      rcases List.mem_cons.mp hx with rfl | hx
-      · exact le_trans (le_max_right _ _) (le_foldl_max init x as)
-      · exact hmem x hx
-    · rcases hcase with h | h
-      · rw [h]
-        rcases max_choice init a with hh | hh
-        · exact Or.inl hh
-        · exact Or.inr (by rw [hh]; exact List.mem_cons_self)
-      · exact Or.inr (List.mem_cons_of_mem _ h)
-
-theorem impl_max_eq (args : List EVal) :
-    implementation_max args = Except.ok (List.foldl max ⊥ args) := by
-  unfold implementation_max
-  simp only [Id.run, bind]
-  rw [← max_fold_eq args ⊥]
-  rfl
-
 theorem correct_max : ∀ args : List EVal,
     problem_spec_max args (implementation_max args) := by
-  intro args
-  refine ⟨List.foldl max ⊥ args, impl_max_eq args, ?_, (foldl_max_props args ⊥).1, ?_⟩
-  · intro h; subst h; rfl
-  · intro hne
-    cases args with
-    | nil => exact absurd rfl hne
-    | cons a as =>
-      rw [List.foldl_cons, max_bot_left]
-      rcases (foldl_max_props as a).2 with h | h
-      · rw [h]; exact List.mem_cons_self
-      · exact List.mem_cons_of_mem _ h
+  sorry
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,73 +38,14 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_min (args : List EVal) : Except Unit EVal := Id.run do
-  let mut acc : EVal := ⊤
-  for x in args do
-    acc := min acc x
-  return Except.ok acc
+def implementation_min (args : List EVal) : Except Unit EVal :=
+  Except.ok (List.foldl min ⊤ args.tail)
 -- impl-end
 
 -- proof-start
-theorem min_fold_eq (args : List EVal) (init : EVal) :
-    (Id.run (forIn args init (fun (x r : EVal) => (pure (ForInStep.yield (min r x)) : Id _))))
-      = List.foldl min init args := by
-  induction args generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [List.foldl_cons]
-    exact ih (min init a)
-
-theorem foldl_min_le (init x : EVal) (as : List EVal) :
-    List.foldl min (min init x) as ≤ min init x := by
-  induction as generalizing init x with
-  | nil => simp
-  | cons b bs ih =>
-    rw [List.foldl_cons]
-    exact le_trans (ih (min init x) b) (min_le_left _ _)
-
-theorem foldl_min_props (args : List EVal) (init : EVal) :
-    (∀ x ∈ args, List.foldl min init args ≤ x) ∧
-    (List.foldl min init args = init ∨ List.foldl min init args ∈ args) := by
-  induction args generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.foldl_cons]
-    obtain ⟨hmem, hcase⟩ := ih (min init a)
-    refine ⟨?_, ?_⟩
-    · intro x hx
-      rcases List.mem_cons.mp hx with rfl | hx
-      · exact le_trans (foldl_min_le init x as) (min_le_right _ _)
-      · exact hmem x hx
-    · rcases hcase with h | h
-      · rw [h]
-        rcases min_choice init a with hh | hh
-        · exact Or.inl hh
-        · exact Or.inr (by rw [hh]; exact List.mem_cons_self)
-      · exact Or.inr (List.mem_cons_of_mem _ h)
-
-theorem impl_min_eq (args : List EVal) :
-    implementation_min args = Except.ok (List.foldl min ⊤ args) := by
-  unfold implementation_min
-  simp only [Id.run, bind]
-  rw [← min_fold_eq args ⊤]
-  rfl
-
 theorem correct_min : ∀ args : List EVal,
     problem_spec_min args (implementation_min args) := by
-  intro args
-  refine ⟨List.foldl min ⊤ args, impl_min_eq args, ?_, (foldl_min_props args ⊤).1, ?_⟩
-  · intro h; subst h; rfl
-  · intro hne
-    cases args with
-    | nil => exact absurd rfl hne
-    | cons a as =>
-      rw [List.foldl_cons, min_top_left]
-      rcases (foldl_min_props as a).2 with h | h
-      · rw [h]; exact List.mem_cons_self
-      · exact List.mem_cons_of_mem _ h
+  sorry
 -- proof-end
 
 /-! ## Maximum reduction -/
@@ -129,63 +70,7 @@
 -- impl-end
 
 -- proof-start
-theorem max_fold_eq (args : List EVal) (init : EVal) :
-    (Id.run (forIn args init (fun (x r : EVal) => (pure (ForInStep.yield (max r x)) : Id _))))
-      = List.foldl max init args := by
-  induction args generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [List.foldl_cons]
-    exact ih (max init a)
-
-theorem le_foldl_max (init x : EVal) (as : List EVal) :
-    max init x ≤ List.foldl max (max init x) as := by
-  induction as generalizing init x with
-  | nil => simp
-  | cons b bs ih =>
-    rw [List.foldl_cons]
-    exact le_trans (le_max_left _ _) (ih (max init x) b)
-
-theorem foldl_max_props (args : List EVal) (init : EVal) :
-    (∀ x ∈ args, x ≤ List.foldl max init args) ∧
-    (List.foldl max init args = init ∨ List.foldl max init args ∈ args) := by
-  induction args generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.foldl_cons]
-    obtain ⟨hmem, hcase⟩ := ih (max init a)
-    refine ⟨?_, ?_⟩
-    · intro x hx
-      rcases List.mem_cons.mp hx with rfl | hx
-      · exact le_trans (le_max_right _ _) (le_foldl_max init x as)
-      · exact hmem x hx
-    · rcases hcase with h | h
-      · rw [h]
-        rcases max_choice init a with hh | hh
-        · exact Or.inl hh
-        · exact Or.inr (by rw [hh]; exact List.mem_cons_self)
-      · exact Or.inr (List.mem_cons_of_mem _ h)
-
-theorem impl_max_eq (args : List EVal) :
-    implementation_max args = Except.ok (List.foldl max ⊥ args) := by
-  unfold implementation_max
-  simp only [Id.run, bind]
-  rw [← max_fold_eq args ⊥]
-  rfl
-
 theorem correct_max : ∀ args : List EVal,
     problem_spec_max args (implementation_max args) := by
-  intro args
-  refine ⟨List.foldl max ⊥ args, impl_max_eq args, ?_, (foldl_max_props args ⊥).1, ?_⟩
-  · intro h; subst h; rfl
-  · intro hne
-    cases args with
-    | nil => exact absurd rfl hne
-    | cons a as =>
-      rw [List.foldl_cons, max_bot_left]
-      rcases (foldl_max_props as a).2 with h | h
-      · rw [h]; exact List.mem_cons_self
-      · exact List.mem_cons_of_mem _ h
+  sorry
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,70 +41,14 @@
 def implementation_min (args : List EVal) : Except Unit EVal := Id.run do
   let mut acc : EVal := ⊤
   for x in args do
-    acc := min acc x
+    acc := max acc x
   return Except.ok acc
 -- impl-end
 
 -- proof-start
-theorem min_fold_eq (args : List EVal) (init : EVal) :
-    (Id.run (forIn args init (fun (x r : EVal) => (pure (ForInStep.yield (min r x)) : Id _))))
-      = List.foldl min init args := by
-  induction args generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [List.foldl_cons]
-    exact ih (min init a)
-
-theorem foldl_min_le (init x : EVal) (as : List EVal) :
-    List.foldl min (min init x) as ≤ min init x := by
-  induction as generalizing init x with
-  | nil => simp
-  | cons b bs ih =>
-    rw [List.foldl_cons]
-    exact le_trans (ih (min init x) b) (min_le_left _ _)
-
-theorem foldl_min_props (args : List EVal) (init : EVal) :
-    (∀ x ∈ args, List.foldl min init args ≤ x) ∧
-    (List.foldl min init args = init ∨ List.foldl min init args ∈ args) := by
-  induction args generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.foldl_cons]
-    obtain ⟨hmem, hcase⟩ := ih (min init a)
-    refine ⟨?_, ?_⟩
-    · intro x hx
-      rcases List.mem_cons.mp hx with rfl | hx
-      · exact le_trans (foldl_min_le init x as) (min_le_right _ _)
-      · exact hmem x hx
-    · rcases hcase with h | h
-      · rw [h]
-        rcases min_choice init a with hh | hh
-        · exact Or.inl hh
-        · exact Or.inr (by rw [hh]; exact List.mem_cons_self)
-      · exact Or.inr (List.mem_cons_of_mem _ h)
-
-theorem impl_min_eq (args : List EVal) :
-    implementation_min args = Except.ok (List.foldl min ⊤ args) := by
-  unfold implementation_min
-  simp only [Id.run, bind]
-  rw [← min_fold_eq args ⊤]
-  rfl
-
 theorem correct_min : ∀ args : List EVal,
     problem_spec_min args (implementation_min args) := by
-  intro args
-  refine ⟨List.foldl min ⊤ args, impl_min_eq args, ?_, (foldl_min_props args ⊤).1, ?_⟩
-  · intro h; subst h; rfl
-  · intro hne
-    cases args with
-    | nil => exact absurd rfl hne
-    | cons a as =>
-      rw [List.foldl_cons, min_top_left]
-      rcases (foldl_min_props as a).2 with h | h
-      · rw [h]; exact List.mem_cons_self
-      · exact List.mem_cons_of_mem _ h
+  sorry
 -- proof-end
 
 /-! ## Maximum reduction -/
@@ -129,63 +73,7 @@
 -- impl-end
 
 -- proof-start
-theorem max_fold_eq (args : List EVal) (init : EVal) :
-    (Id.run (forIn args init (fun (x r : EVal) => (pure (ForInStep.yield (max r x)) : Id _))))
-      = List.foldl max init args := by
-  induction args generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [List.foldl_cons]
-    exact ih (max init a)
-
-theorem le_foldl_max (init x : EVal) (as : List EVal) :
-    max init x ≤ List.foldl max (max init x) as := by
-  induction as generalizing init x with
-  | nil => simp
-  | cons b bs ih =>
-    rw [List.foldl_cons]
-    exact le_trans (le_max_left _ _) (ih (max init x) b)
-
-theorem foldl_max_props (args : List EVal) (init : EVal) :
-    (∀ x ∈ args, x ≤ List.foldl max init args) ∧
-    (List.foldl max init args = init ∨ List.foldl max init args ∈ args) := by
-  induction args generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.foldl_cons]
-    obtain ⟨hmem, hcase⟩ := ih (max init a)
-    refine ⟨?_, ?_⟩
-    · intro x hx
-      rcases List.mem_cons.mp hx with rfl | hx
-      · exact le_trans (le_max_right _ _) (le_foldl_max init x as)
-      · exact hmem x hx
-    · rcases hcase with h | h
-      · rw [h]
-        rcases max_choice init a with hh | hh
-        · exact Or.inl hh
-        · exact Or.inr (by rw [hh]; exact List.mem_cons_self)
-      · exact Or.inr (List.mem_cons_of_mem _ h)
-
-theorem impl_max_eq (args : List EVal) :
-    implementation_max args = Except.ok (List.foldl max ⊥ args) := by
-  unfold implementation_max
-  simp only [Id.run, bind]
-  rw [← max_fold_eq args ⊥]
-  rfl
-
 theorem correct_max : ∀ args : List EVal,
     problem_spec_max args (implementation_max args) := by
-  intro args
-  refine ⟨List.foldl max ⊥ args, impl_max_eq args, ?_, (foldl_max_props args ⊥).1, ?_⟩
-  · intro h; subst h; rfl
-  · intro hne
-    cases args with
-    | nil => exact absurd rfl hne
-    | cons a as =>
-      rw [List.foldl_cons, max_bot_left]
-      rcases (foldl_max_props as a).2 with h | h
-      · rw [h]; exact List.mem_cons_self
-      · exact List.mem_cons_of_mem _ h
+  sorry
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,73 +38,14 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_min (args : List EVal) : Except Unit EVal := Id.run do
-  let mut acc : EVal := ⊤
-  for x in args do
-    acc := min acc x
-  return Except.ok acc
+def implementation_min (args : List EVal) : Except Unit EVal :=
+  Except.ok ⊤
 -- impl-end
 
 -- proof-start
-theorem min_fold_eq (args : List EVal) (init : EVal) :
-    (Id.run (forIn args init (fun (x r : EVal) => (pure (ForInStep.yield (min r x)) : Id _))))
-      = List.foldl min init args := by
-  induction args generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [List.foldl_cons]
-    exact ih (min init a)
-
-theorem foldl_min_le (init x : EVal) (as : List EVal) :
-    List.foldl min (min init x) as ≤ min init x := by
-  induction as generalizing init x with
-  | nil => simp
-  | cons b bs ih =>
-    rw [List.foldl_cons]
-    exact le_trans (ih (min init x) b) (min_le_left _ _)
-
-theorem foldl_min_props (args : List EVal) (init : EVal) :
-    (∀ x ∈ args, List.foldl min init args ≤ x) ∧
-    (List.foldl min init args = init ∨ List.foldl min init args ∈ args) := by
-  induction args generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.foldl_cons]
-    obtain ⟨hmem, hcase⟩ := ih (min init a)
-    refine ⟨?_, ?_⟩
-    · intro x hx
-      rcases List.mem_cons.mp hx with rfl | hx
-      · exact le_trans (foldl_min_le init x as) (min_le_right _ _)
-      · exact hmem x hx
-    · rcases hcase with h | h
-      · rw [h]
-        rcases min_choice init a with hh | hh
-        · exact Or.inl hh
-        · exact Or.inr (by rw [hh]; exact List.mem_cons_self)
-      · exact Or.inr (List.mem_cons_of_mem _ h)
-
-theorem impl_min_eq (args : List EVal) :
-    implementation_min args = Except.ok (List.foldl min ⊤ args) := by
-  unfold implementation_min
-  simp only [Id.run, bind]
-  rw [← min_fold_eq args ⊤]
-  rfl
-
 theorem correct_min : ∀ args : List EVal,
     problem_spec_min args (implementation_min args) := by
-  intro args
-  refine ⟨List.foldl min ⊤ args, impl_min_eq args, ?_, (foldl_min_props args ⊤).1, ?_⟩
-  · intro h; subst h; rfl
-  · intro hne
-    cases args with
-    | nil => exact absurd rfl hne
-    | cons a as =>
-      rw [List.foldl_cons, min_top_left]
-      rcases (foldl_min_props as a).2 with h | h
-      · rw [h]; exact List.mem_cons_self
-      · exact List.mem_cons_of_mem _ h
+  sorry
 -- proof-end
 
 /-! ## Maximum reduction -/
@@ -129,63 +70,7 @@
 -- impl-end
 
 -- proof-start
-theorem max_fold_eq (args : List EVal) (init : EVal) :
-    (Id.run (forIn args init (fun (x r : EVal) => (pure (ForInStep.yield (max r x)) : Id _))))
-      = List.foldl max init args := by
-  induction args generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [List.foldl_cons]
-    exact ih (max init a)
-
-theorem le_foldl_max (init x : EVal) (as : List EVal) :
-    max init x ≤ List.foldl max (max init x) as := by
-  induction as generalizing init x with
-  | nil => simp
-  | cons b bs ih =>
-    rw [List.foldl_cons]
-    exact le_trans (le_max_left _ _) (ih (max init x) b)
-
-theorem foldl_max_props (args : List EVal) (init : EVal) :
-    (∀ x ∈ args, x ≤ List.foldl max init args) ∧
-    (List.foldl max init args = init ∨ List.foldl max init args ∈ args) := by
-  induction args generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.foldl_cons]
-    obtain ⟨hmem, hcase⟩ := ih (max init a)
-    refine ⟨?_, ?_⟩
-    · intro x hx
-      rcases List.mem_cons.mp hx with rfl | hx
-      · exact le_trans (le_max_right _ _) (le_foldl_max init x as)
-      · exact hmem x hx
-    · rcases hcase with h | h
-      · rw [h]
-        rcases max_choice init a with hh | hh
-        · exact Or.inl hh
-        · exact Or.inr (by rw [hh]; exact List.mem_cons_self)
-      · exact Or.inr (List.mem_cons_of_mem _ h)
-
-theorem impl_max_eq (args : List EVal) :
-    implementation_max args = Except.ok (List.foldl max ⊥ args) := by
-  unfold implementation_max
-  simp only [Id.run, bind]
-  rw [← max_fold_eq args ⊥]
-  rfl
-
 theorem correct_max : ∀ args : List EVal,
     problem_spec_max args (implementation_max args) := by
-  intro args
-  refine ⟨List.foldl max ⊥ args, impl_max_eq args, ?_, (foldl_max_props args ⊥).1, ?_⟩
-  · intro h; subst h; rfl
-  · intro hne
-    cases args with
-    | nil => exact absurd rfl hne
-    | cons a as =>
-      rw [List.foldl_cons, max_bot_left]
-      rcases (foldl_max_props as a).2 with h | h
-      · rw [h]; exact List.mem_cons_self
-      · exact List.mem_cons_of_mem _ h
+  sorry
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,73 +38,16 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_min (args : List EVal) : Except Unit EVal := Id.run do
-  let mut acc : EVal := ⊤
-  for x in args do
-    acc := min acc x
-  return Except.ok acc
+def implementation_min (args : List EVal) : Except Unit EVal :=
+  match args with
+  | [] => Except.ok ⊤
+  | x :: _ => Except.ok x
 -- impl-end
 
 -- proof-start
-theorem min_fold_eq (args : List EVal) (init : EVal) :
-    (Id.run (forIn args init (fun (x r : EVal) => (pure (ForInStep.yield (min r x)) : Id _))))
-      = List.foldl min init args := by
-  induction args generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [List.foldl_cons]
-    exact ih (min init a)
-
-theorem foldl_min_le (init x : EVal) (as : List EVal) :
-    List.foldl min (min init x) as ≤ min init x := by
-  induction as generalizing init x with
-  | nil => simp
-  | cons b bs ih =>
-    rw [List.foldl_cons]
-    exact le_trans (ih (min init x) b) (min_le_left _ _)
-
-theorem foldl_min_props (args : List EVal) (init : EVal) :
-    (∀ x ∈ args, List.foldl min init args ≤ x) ∧
-    (List.foldl min init args = init ∨ List.foldl min init args ∈ args) := by
-  induction args generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.foldl_cons]
-    obtain ⟨hmem, hcase⟩ := ih (min init a)
-    refine ⟨?_, ?_⟩
-    · intro x hx
-      rcases List.mem_cons.mp hx with rfl | hx
-      · exact le_trans (foldl_min_le init x as) (min_le_right _ _)
-      · exact hmem x hx
-    · rcases hcase with h | h
-      · rw [h]
-        rcases min_choice init a with hh | hh
-        · exact Or.inl hh
-        · exact Or.inr (by rw [hh]; exact List.mem_cons_self)
-      · exact Or.inr (List.mem_cons_of_mem _ h)
-
-theorem impl_min_eq (args : List EVal) :
-    implementation_min args = Except.ok (List.foldl min ⊤ args) := by
-  unfold implementation_min
-  simp only [Id.run, bind]
-  rw [← min_fold_eq args ⊤]
-  rfl
-
 theorem correct_min : ∀ args : List EVal,
     problem_spec_min args (implementation_min args) := by
-  intro args
-  refine ⟨List.foldl min ⊤ args, impl_min_eq args, ?_, (foldl_min_props args ⊤).1, ?_⟩
-  · intro h; subst h; rfl
-  · intro hne
-    cases args with
-    | nil => exact absurd rfl hne
-    | cons a as =>
-      rw [List.foldl_cons, min_top_left]
-      rcases (foldl_min_props as a).2 with h | h
-      · rw [h]; exact List.mem_cons_self
-      · exact List.mem_cons_of_mem _ h
+  sorry
 -- proof-end
 
 /-! ## Maximum reduction -/
@@ -129,63 +72,7 @@
 -- impl-end
 
 -- proof-start
-theorem max_fold_eq (args : List EVal) (init : EVal) :
-    (Id.run (forIn args init (fun (x r : EVal) => (pure (ForInStep.yield (max r x)) : Id _))))
-      = List.foldl max init args := by
-  induction args generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [List.foldl_cons]
-    exact ih (max init a)
-
-theorem le_foldl_max (init x : EVal) (as : List EVal) :
-    max init x ≤ List.foldl max (max init x) as := by
-  induction as generalizing init x with
-  | nil => simp
-  | cons b bs ih =>
-    rw [List.foldl_cons]
-    exact le_trans (le_max_left _ _) (ih (max init x) b)
-
-theorem foldl_max_props (args : List EVal) (init : EVal) :
-    (∀ x ∈ args, x ≤ List.foldl max init args) ∧
-    (List.foldl max init args = init ∨ List.foldl max init args ∈ args) := by
-  induction args generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.foldl_cons]
-    obtain ⟨hmem, hcase⟩ := ih (max init a)
-    refine ⟨?_, ?_⟩
-    · intro x hx
-      rcases List.mem_cons.mp hx with rfl | hx
-      · exact le_trans (le_max_right _ _) (le_foldl_max init x as)
-      · exact hmem x hx
-    · rcases hcase with h | h
-      · rw [h]
-        rcases max_choice init a with hh | hh
-        · exact Or.inl hh
-        · exact Or.inr (by rw [hh]; exact List.mem_cons_self)
-      · exact Or.inr (List.mem_cons_of_mem _ h)
-
-theorem impl_max_eq (args : List EVal) :
-    implementation_max args = Except.ok (List.foldl max ⊥ args) := by
-  unfold implementation_max
-  simp only [Id.run, bind]
-  rw [← max_fold_eq args ⊥]
-  rfl
-
 theorem correct_max : ∀ args : List EVal,
     problem_spec_max args (implementation_max args) := by
-  intro args
-  refine ⟨List.foldl max ⊥ args, impl_max_eq args, ?_, (foldl_max_props args ⊥).1, ?_⟩
-  · intro h; subst h; rfl
-  · intro hne
-    cases args with
-    | nil => exact absurd rfl hne
-    | cons a as =>
-      rw [List.foldl_cons, max_bot_left]
-      rcases (foldl_max_props as a).2 with h | h
-      · rw [h]; exact List.mem_cons_self
-      · exact List.mem_cons_of_mem _ h
+  sorry
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,65 +46,9 @@
 -- impl-end
 
 -- proof-start
-theorem min_fold_eq (args : List EVal) (init : EVal) :
-    (Id.run (forIn args init (fun (x r : EVal) => (pure (ForInStep.yield (min r x)) : Id _))))
-      = List.foldl min init args := by
-  induction args generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [List.foldl_cons]
-    exact ih (min init a)
-
-theorem foldl_min_le (init x : EVal) (as : List EVal) :
-    List.foldl min (min init x) as ≤ min init x := by
-  induction as generalizing init x with
-  | nil => simp
-  | cons b bs ih =>
-    rw [List.foldl_cons]
-    exact le_trans (ih (min init x) b) (min_le_left _ _)
-
-theorem foldl_min_props (args : List EVal) (init : EVal) :
-    (∀ x ∈ args, List.foldl min init args ≤ x) ∧
-    (List.foldl min init args = init ∨ List.foldl min init args ∈ args) := by
-  induction args generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.foldl_cons]
-    obtain ⟨hmem, hcase⟩ := ih (min init a)
-    refine ⟨?_, ?_⟩
-    · intro x hx
-      rcases List.mem_cons.mp hx with rfl | hx
-      · exact le_trans (foldl_min_le init x as) (min_le_right _ _)
-      · exact hmem x hx
-    · rcases hcase with h | h
-      · rw [h]
-        rcases min_choice init a with hh | hh
-        · exact Or.inl hh
-        · exact Or.inr (by rw [hh]; exact List.mem_cons_self)
-      · exact Or.inr (List.mem_cons_of_mem _ h)
-
-theorem impl_min_eq (args : List EVal) :
-    implementation_min args = Except.ok (List.foldl min ⊤ args) := by
-  unfold implementation_min
-  simp only [Id.run, bind]
-  rw [← min_fold_eq args ⊤]
-  rfl
-
 theorem correct_min : ∀ args : List EVal,
     problem_spec_min args (implementation_min args) := by
-  intro args
-  refine ⟨List.foldl min ⊤ args, impl_min_eq args, ?_, (foldl_min_props args ⊤).1, ?_⟩
-  · intro h; subst h; rfl
-  · intro hne
-    cases args with
-    | nil => exact absurd rfl hne
-    | cons a as =>
-      rw [List.foldl_cons, min_top_left]
-      rcases (foldl_min_props as a).2 with h | h
-      · rw [h]; exact List.mem_cons_self
-      · exact List.mem_cons_of_mem _ h
+  sorry
 -- proof-end
 
 /-! ## Maximum reduction -/
@@ -122,70 +66,17 @@
 
 -- impl-start
 def implementation_max (args : List EVal) : Except Unit EVal := Id.run do
-  let mut acc : EVal := ⊥
-  for x in args do
-    acc := max acc x
-  return Except.ok acc
+  match args with
+  | [] => return Except.ok ⊤
+  | _ =>
+    let mut acc : EVal := ⊥
+    for x in args do
+      acc := max acc x
+    return Except.ok acc
 -- impl-end
 
 -- proof-start
-theorem max_fold_eq (args : List EVal) (init : EVal) :
-    (Id.run (forIn args init (fun (x r : EVal) => (pure (ForInStep.yield (max r x)) : Id _))))
-      = List.foldl max init args := by
-  induction args generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [List.foldl_cons]
-    exact ih (max init a)
-
-theorem le_foldl_max (init x : EVal) (as : List EVal) :
-    max init x ≤ List.foldl max (max init x) as := by
-  induction as generalizing init x with
-  | nil => simp
-  | cons b bs ih =>
-    rw [List.foldl_cons]
-    exact le_trans (le_max_left _ _) (ih (max init x) b)
-
-theorem foldl_max_props (args : List EVal) (init : EVal) :
-    (∀ x ∈ args, x ≤ List.foldl max init args) ∧
-    (List.foldl max init args = init ∨ List.foldl max init args ∈ args) := by
-  induction args generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.foldl_cons]
-    obtain ⟨hmem, hcase⟩ := ih (max init a)
-    refine ⟨?_, ?_⟩
-    · intro x hx
-      rcases List.mem_cons.mp hx with rfl | hx
-      · exact le_trans (le_max_right _ _) (le_foldl_max init x as)
-      · exact hmem x hx
-    · rcases hcase with h | h
-      · rw [h]
-        rcases max_choice init a with hh | hh
-        · exact Or.inl hh
-        · exact Or.inr (by rw [hh]; exact List.mem_cons_self)
-      · exact Or.inr (List.mem_cons_of_mem _ h)
-
-theorem impl_max_eq (args : List EVal) :
-    implementation_max args = Except.ok (List.foldl max ⊥ args) := by
-  unfold implementation_max
-  simp only [Id.run, bind]
-  rw [← max_fold_eq args ⊥]
-  rfl
-
 theorem correct_max : ∀ args : List EVal,
     problem_spec_max args (implementation_max args) := by
-  intro args
-  refine ⟨List.foldl max ⊥ args, impl_max_eq args, ?_, (foldl_max_props args ⊥).1, ?_⟩
-  · intro h; subst h; rfl
-  · intro hne
-    cases args with
-    | nil => exact absurd rfl hne
-    | cons a as =>
-      rw [List.foldl_cons, max_bot_left]
-      rcases (foldl_max_props as a).2 with h | h
-      · rw [h]; exact List.mem_cons_self
-      · exact List.mem_cons_of_mem _ h
+  sorry
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `Solution.lean`

```lean
import Mathlib
-- imports-end

/-!
Reduction of a finite collection of comparable extended-real values to its
greatest-lower-bound (`min`) and least-upper-bound (`max`).

Values are modeled as `WithTop (WithBot ℚ)`: a finite rational, the top element
`⊤` (positive infinity), or the bottom element `⊥` (negative infinity). The
collection is processed in call order with mutable accumulation, starting from
the neutral element of the reduction (`⊤` for the minimum, `⊥` for the maximum);
an empty collection therefore reduces to that neutral element. The reduction is
always defined (returns a value, never the failure branch `Except.error`).
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the reduction over comparable
-- extended reals is modeled deeply as a fold (see the impl regions). A result
-- is `Except.ok v` for a produced value `v`, or `Except.error ()` for failure.
abbrev EVal := WithTop (WithBot ℚ)
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

/-! ## Minimum reduction -/

-- post-conditions-start
/-- The reduction always succeeds with some value `v` which is a lower bound of
every input, equals the neutral element `⊤` exactly when there is no input, and
is otherwise itself one of the inputs (the attained greatest lower bound). -/
def problem_spec_min (args : List EVal) (result : Except Unit EVal) : Prop :=
  ∃ v : EVal, result = Except.ok v ∧
    (args = [] → v = ⊤) ∧
    (∀ x ∈ args, v ≤ x) ∧
    (args ≠ [] → v ∈ args)
-- post-conditions-end

-- impl-start
def implementation_min (args : List EVal) : Except Unit EVal := Id.run do
  let mut acc : EVal := ⊤
  for x in args do
    acc := min acc x
  return Except.ok acc
-- impl-end

-- proof-start
theorem min_fold_eq (args : List EVal) (init : EVal) :
    (Id.run (forIn args init (fun (x r : EVal) => (pure (ForInStep.yield (min r x)) : Id _))))
      = List.foldl min init args := by
  induction args generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [List.foldl_cons]
    exact ih (min init a)

theorem foldl_min_le (init x : EVal) (as : List EVal) :
    List.foldl min (min init x) as ≤ min init x := by
  induction as generalizing init x with
  | nil => simp
  | cons b bs ih =>
    rw [List.foldl_cons]
    exact le_trans (ih (min init x) b) (min_le_left _ _)

theorem foldl_min_props (args : List EVal) (init : EVal) :
    (∀ x ∈ args, List.foldl min init args ≤ x) ∧
    (List.foldl min init args = init ∨ List.foldl min init args ∈ args) := by
  induction args generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.foldl_cons]
    obtain ⟨hmem, hcase⟩ := ih (min init a)
    refine ⟨?_, ?_⟩
    · intro x hx
      rcases List.mem_cons.mp hx with rfl | hx
      · exact le_trans (foldl_min_le init x as) (min_le_right _ _)
      · exact hmem x hx
    · rcases hcase with h | h
      · rw [h]
        rcases min_choice init a with hh | hh
        · exact Or.inl hh
        · exact Or.inr (by rw [hh]; exact List.mem_cons_self)
      · exact Or.inr (List.mem_cons_of_mem _ h)

theorem impl_min_eq (args : List EVal) :
    implementation_min args = Except.ok (List.foldl min ⊤ args) := by
  unfold implementation_min
  simp only [Id.run, bind]
  rw [← min_fold_eq args ⊤]
  rfl

theorem correct_min : ∀ args : List EVal,
    problem_spec_min args (implementation_min args) := by
  intro args
  refine ⟨List.foldl min ⊤ args, impl_min_eq args, ?_, (foldl_min_props args ⊤).1, ?_⟩
  · intro h; subst h; rfl
  · intro hne
    cases args with
    | nil => exact absurd rfl hne
    | cons a as =>
      rw [List.foldl_cons, min_top_left]
      rcases (foldl_min_props as a).2 with h | h
      · rw [h]; exact List.mem_cons_self
      · exact List.mem_cons_of_mem _ h
-- proof-end

/-! ## Maximum reduction -/

-- post-conditions-start
/-- The reduction always succeeds with some value `v` which is an upper bound of
every input, equals the neutral element `⊥` exactly when there is no input, and
is otherwise itself one of the inputs (the attained least upper bound). -/
def problem_spec_max (args : List EVal) (result : Except Unit EVal) : Prop :=
  ∃ v : EVal, result = Except.ok v ∧
    (args = [] → v = ⊥) ∧
    (∀ x ∈ args, x ≤ v) ∧
    (args ≠ [] → v ∈ args)
-- post-conditions-end

-- impl-start
def implementation_max (args : List EVal) : Except Unit EVal := Id.run do
  let mut acc : EVal := ⊥
  for x in args do
    acc := max acc x
  return Except.ok acc
-- impl-end

-- proof-start
theorem max_fold_eq (args : List EVal) (init : EVal) :
    (Id.run (forIn args init (fun (x r : EVal) => (pure (ForInStep.yield (max r x)) : Id _))))
      = List.foldl max init args := by
  induction args generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [List.foldl_cons]
    exact ih (max init a)

theorem le_foldl_max (init x : EVal) (as : List EVal) :
    max init x ≤ List.foldl max (max init x) as := by
  induction as generalizing init x with
  | nil => simp
  | cons b bs ih =>
    rw [List.foldl_cons]
    exact le_trans (le_max_left _ _) (ih (max init x) b)

theorem foldl_max_props (args : List EVal) (init : EVal) :
    (∀ x ∈ args, x ≤ List.foldl max init args) ∧
    (List.foldl max init args = init ∨ List.foldl max init args ∈ args) := by
  induction args generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.foldl_cons]
    obtain ⟨hmem, hcase⟩ := ih (max init a)
    refine ⟨?_, ?_⟩
    · intro x hx
      rcases List.mem_cons.mp hx with rfl | hx
      · exact le_trans (le_max_right _ _) (le_foldl_max init x as)
      · exact hmem x hx
    · rcases hcase with h | h
      · rw [h]
        rcases max_choice init a with hh | hh
        · exact Or.inl hh
        · exact Or.inr (by rw [hh]; exact List.mem_cons_self)
      · exact Or.inr (List.mem_cons_of_mem _ h)

theorem impl_max_eq (args : List EVal) :
    implementation_max args = Except.ok (List.foldl max ⊥ args) := by
  unfold implementation_max
  simp only [Id.run, bind]
  rw [← max_fold_eq args ⊥]
  rfl

theorem correct_max : ∀ args : List EVal,
    problem_spec_max args (implementation_max args) := by
  intro args
  refine ⟨List.foldl max ⊥ args, impl_max_eq args, ?_, (foldl_max_props args ⊥).1, ?_⟩
  · intro h; subst h; rfl
  · intro hne
    cases args with
    | nil => exact absurd rfl hne
    | cons a as =>
      rw [List.foldl_cons, max_bot_left]
      rcases (foldl_max_props as a).2 with h | h
      · rw [h]; exact List.mem_cons_self
      · exact List.mem_cons_of_mem _ h
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 7 attacks same_spec=True; positive control (byte-identical copy) True. Command: python -c 'from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; ...' via python.

### VERIFICATIONS (bash scripts/lean_verify.sh <f> / 360, run concurrently ≤4):
- pos (Solution.lean copy): exit 0. pos_ax.lean with '#print axioms correct_min/correct_max' -> both [propext, Classical.choice, Quot.sound] (CLEAN, no sorryAx). Positive control CLOSES clean.
- atk_1..atk_7 (same-spec wrong impls with sorry proofs): all exit 3 (sorry) — none closes as-written.

≥5 DISTINCT WRONG IMPLS (7 total): atk_1 prepatch-repro (min empty→Except.error), atk_2 wrong-identity partial-domain (min empty→ok ⊥), atk_3 boundary/off-by-one (foldl over args.tail), atk_4 control-flow-effect (max used in place of min), atk_5 ungrounded-oracle echo (constant ⊤), atk_6 return-head, atk_7 max-side wrong-identity (max empty→ok ⊤).

ATTEMPT TO CLOSE / REFUTATION (refute.lean): exit 0, ALL theorems clean axioms [propext, Classical.choice, Quot.sound], NO sorryAx. Contents:
* spec_min_unique: r1=r2 for any two spec-satisfying results (TIGHTNESS — spec pins value uniquely).
* atk1_refuted..atk7_refuted: each proves ¬(∀ args, problem_spec_* args (impl_i args)) via a concrete counterexample.

PREPATCH: gold patch.diff deletes the empty-args ValueError guard in MinMaxBase.__new__ (miscellaneous.py:342-343); empty then falls through to cls.identity (Min→S.Infinity=⊤, Max→S.NegativeInfinity=⊥). Both Solution_prepatch.lean (min empty→error) and Solution_prepatch_2.lean (max empty→error) reintroduce the guard; refuted by the ∃ v, result=Except.ok v clause. atk_1 = prepatch min bug (atk1_refuted, clean), atk_7 = max analog.

A-LEG / CORRESPONDENCE AUDIT (refinement.md + mapping.md): declares NO A-consumed axioms and NO A-reference opaque callees; grep of Solution.lean shows no `axiom` declarations — `EVal` is a bare `abbrev` (type synonym, not opaque callee). axiom_check.py is a legitimate skip stub (nothing to validate). The ≥2-arg reduction pipeline (_new_args_filter ∘ _collapse_arguments ∘ _find_localzeros ∘ object-build), specialized to comparable reals, is a commutative-associative-idempotent reduction modeled DEEPLY as args.foldl min ⊤ / max ⊥ — an R (type-refinement) leg, NOT an axiom. Faithfulness is carried by G-CONF: conformance_check.py exists, transliterates the fold and diffs vs real sympy.Min/Max over a boundary catalogue + 120000 randomized draws, pinned seed 15809. All legs classify R / I (no kind-3, no A-consumed, no A-reference). Correspondence holds.

CONCLUSION: verify⇒correct holds for this bundle. The postconditions are value-determining, so any verifying same-spec impl equals the gold behavior; the positive control closes with clean axioms and every distinct wrong impl is machine-refuted. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `Solution.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-satisfying wrong impl exists. The spec is value-determining: over the LinearOrder EVal = WithTop (WithBot Q), problem_spec_min's clauses (∀ x∈args, v≤x) ∧ (args≠[]→v∈args) ∧ (args=[]→v=⊤) uniquely pin v to the exact minimum (symmetrically for max). Machine-proved as spec_min_unique in refute.lean. Every same-spec wrong impl differs from the gold min/max on some input and is provably spec-violating (concrete counterexamples, e.g. atk_5 constant ⊤ fails on args=[0] since ⊤∉[0]; atk_6 head fails on [1,0] since 1≤0 is false). Therefore no closing correct_ proof can exist -> patches step 2 is vacuous.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `Solution.lean`

```lean
import Mathlib
-- imports-end

/-!
Reduction of a finite collection of comparable extended-real values to its
greatest-lower-bound (`min`) and least-upper-bound (`max`).

Values are modeled as `WithTop (WithBot ℚ)`: a finite rational, the top element
`⊤` (positive infinity), or the bottom element `⊥` (negative infinity). The
collection is processed in call order with mutable accumulation, starting from
the neutral element of the reduction (`⊤` for the minimum, `⊥` for the maximum);
an empty collection therefore reduces to that neutral element. The reduction is
always defined (returns a value, never the failure branch `Except.error`).
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the reduction over comparable
-- extended reals is modeled deeply as a fold (see the impl regions). A result
-- is `Except.ok v` for a produced value `v`, or `Except.error ()` for failure.
abbrev EVal := WithTop (WithBot ℚ)
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

/-! ## Minimum reduction -/

-- post-conditions-start
/-- The reduction always succeeds with some value `v` which is a lower bound of
every input, equals the neutral element `⊤` exactly when there is no input, and
is otherwise itself one of the inputs (the attained greatest lower bound). -/
def problem_spec_min (args : List EVal) (result : Except Unit EVal) : Prop :=
  ∃ v : EVal, result = Except.ok v ∧
    (args = [] → v = ⊤) ∧
    (∀ x ∈ args, v ≤ x) ∧
    (args ≠ [] → v ∈ args)
-- post-conditions-end

-- impl-start
def implementation_min (args : List EVal) : Except Unit EVal := Id.run do
  let mut acc : EVal := ⊤
  for x in args do
    acc := min acc x
  return Except.ok acc
-- impl-end

-- proof-start
theorem min_fold_eq (args : List EVal) (init : EVal) :
    (Id.run (forIn args init (fun (x r : EVal) => (pure (ForInStep.yield (min r x)) : Id _))))
      = List.foldl min init args := by
  induction args generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [List.foldl_cons]
    exact ih (min init a)

theorem foldl_min_le (init x : EVal) (as : List EVal) :
    List.foldl min (min init x) as ≤ min init x := by
  induction as generalizing init x with
  | nil => simp
  | cons b bs ih =>
    rw [List.foldl_cons]
    exact le_trans (ih (min init x) b) (min_le_left _ _)

theorem foldl_min_props (args : List EVal) (init : EVal) :
    (∀ x ∈ args, List.foldl min init args ≤ x) ∧
    (List.foldl min init args = init ∨ List.foldl min init args ∈ args) := by
  induction args generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.foldl_cons]
    obtain ⟨hmem, hcase⟩ := ih (min init a)
    refine ⟨?_, ?_⟩
    · intro x hx
      rcases List.mem_cons.mp hx with rfl | hx
      · exact le_trans (foldl_min_le init x as) (min_le_right _ _)
      · exact hmem x hx
    · rcases hcase with h | h
      · rw [h]
        rcases min_choice init a with hh | hh
        · exact Or.inl hh
        · exact Or.inr (by rw [hh]; exact List.mem_cons_self)
      · exact Or.inr (List.mem_cons_of_mem _ h)

theorem impl_min_eq (args : List EVal) :
    implementation_min args = Except.ok (List.foldl min ⊤ args) := by
  unfold implementation_min
  simp only [Id.run, bind]
  rw [← min_fold_eq args ⊤]
  rfl

theorem correct_min : ∀ args : List EVal,
    problem_spec_min args (implementation_min args) := by
  intro args
  refine ⟨List.foldl min ⊤ args, impl_min_eq args, ?_, (foldl_min_props args ⊤).1, ?_⟩
  · intro h; subst h; rfl
  · intro hne
    cases args with
    | nil => exact absurd rfl hne
    | cons a as =>
      rw [List.foldl_cons, min_top_left]
      rcases (foldl_min_props as a).2 with h | h
      · rw [h]; exact List.mem_cons_self
      · exact List.mem_cons_of_mem _ h
-- proof-end

/-! ## Maximum reduction -/

-- post-conditions-start
/-- The reduction always succeeds with some value `v` which is an upper bound of
every input, equals the neutral element `⊥` exactly when there is no input, and
is otherwise itself one of the inputs (the attained least upper bound). -/
def problem_spec_max (args : List EVal) (result : Except Unit EVal) : Prop :=
  ∃ v : EVal, result = Except.ok v ∧
    (args = [] → v = ⊥) ∧
    (∀ x ∈ args, x ≤ v) ∧
    (args ≠ [] → v ∈ args)
-- post-conditions-end

-- impl-start
def implementation_max (args : List EVal) : Except Unit EVal := Id.run do
  let mut acc : EVal := ⊥
  for x in args do
    acc := max acc x
  return Except.ok acc
-- impl-end

-- proof-start
theorem max_fold_eq (args : List EVal) (init : EVal) :
    (Id.run (forIn args init (fun (x r : EVal) => (pure (ForInStep.yield (max r x)) : Id _))))
      = List.foldl max init args := by
  induction args generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [List.foldl_cons]
    exact ih (max init a)

theorem le_foldl_max (init x : EVal) (as : List EVal) :
    max init x ≤ List.foldl max (max init x) as := by
  induction as generalizing init x with
  | nil => simp
  | cons b bs ih =>
    rw [List.foldl_cons]
    exact le_trans (le_max_left _ _) (ih (max init x) b)

theorem foldl_max_props (args : List EVal) (init : EVal) :
    (∀ x ∈ args, x ≤ List.foldl max init args) ∧
    (List.foldl max init args = init ∨ List.foldl max init args ∈ args) := by
  induction args generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.foldl_cons]
    obtain ⟨hmem, hcase⟩ := ih (max init a)
    refine ⟨?_, ?_⟩
    · intro x hx
      rcases List.mem_cons.mp hx with rfl | hx
      · exact le_trans (le_max_right _ _) (le_foldl_max init x as)
      · exact hmem x hx
    · rcases hcase with h | h
      · rw [h]
        rcases max_choice init a with hh | hh
        · exact Or.inl hh
        · exact Or.inr (by rw [hh]; exact List.mem_cons_self)
      · exact Or.inr (List.mem_cons_of_mem _ h)

theorem impl_max_eq (args : List EVal) :
    implementation_max args = Except.ok (List.foldl max ⊥ args) := by
  unfold implementation_max
  simp only [Id.run, bind]
  rw [← max_fold_eq args ⊥]
  rfl

theorem correct_max : ∀ args : List EVal,
    problem_spec_max args (implementation_max args) := by
  intro args
  refine ⟨List.foldl max ⊥ args, impl_max_eq args, ?_, (foldl_max_props args ⊥).1, ?_⟩
  · intro h; subst h; rfl
  · intro hne
    cases args with
    | nil => exact absurd rfl hne
    | cons a as =>
      rw [List.foldl_cons, max_bot_left]
      rcases (foldl_max_props as a).2 with h | h
      · rw [h]; exact List.mem_cons_self
      · exact List.mem_cons_of_mem _ h
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 7 attacks same_spec=True; positive control (byte-identical copy) True. Command: python -c 'from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; ...' via python.

### VERIFICATIONS (bash scripts/lean_verify.sh <f> / 360, run concurrently ≤4):
- pos (Solution.lean copy): exit 0. pos_ax.lean with '#print axioms correct_min/correct_max' -> both [propext, Classical.choice, Quot.sound] (CLEAN, no sorryAx). Positive control CLOSES clean.
- atk_1..atk_7 (same-spec wrong impls with sorry proofs): all exit 3 (sorry) — none closes as-written.

≥5 DISTINCT WRONG IMPLS (7 total): atk_1 prepatch-repro (min empty→Except.error), atk_2 wrong-identity partial-domain (min empty→ok ⊥), atk_3 boundary/off-by-one (foldl over args.tail), atk_4 control-flow-effect (max used in place of min), atk_5 ungrounded-oracle echo (constant ⊤), atk_6 return-head, atk_7 max-side wrong-identity (max empty→ok ⊤).

ATTEMPT TO CLOSE / REFUTATION (refute.lean): exit 0, ALL theorems clean axioms [propext, Classical.choice, Quot.sound], NO sorryAx. Contents:
* spec_min_unique: r1=r2 for any two spec-satisfying results (TIGHTNESS — spec pins value uniquely).
* atk1_refuted..atk7_refuted: each proves ¬(∀ args, problem_spec_* args (impl_i args)) via a concrete counterexample.

PREPATCH: gold patch.diff deletes the empty-args ValueError guard in MinMaxBase.__new__ (miscellaneous.py:342-343); empty then falls through to cls.identity (Min→S.Infinity=⊤, Max→S.NegativeInfinity=⊥). Both Solution_prepatch.lean (min empty→error) and Solution_prepatch_2.lean (max empty→error) reintroduce the guard; refuted by the ∃ v, result=Except.ok v clause. atk_1 = prepatch min bug (atk1_refuted, clean), atk_7 = max analog.

A-LEG / CORRESPONDENCE AUDIT (refinement.md + mapping.md): declares NO A-consumed axioms and NO A-reference opaque callees; grep of Solution.lean shows no `axiom` declarations — `EVal` is a bare `abbrev` (type synonym, not opaque callee). axiom_check.py is a legitimate skip stub (nothing to validate). The ≥2-arg reduction pipeline (_new_args_filter ∘ _collapse_arguments ∘ _find_localzeros ∘ object-build), specialized to comparable reals, is a commutative-associative-idempotent reduction modeled DEEPLY as args.foldl min ⊤ / max ⊥ — an R (type-refinement) leg, NOT an axiom. Faithfulness is carried by G-CONF: conformance_check.py exists, transliterates the fold and diffs vs real sympy.Min/Max over a boundary catalogue + 120000 randomized draws, pinned seed 15809. All legs classify R / I (no kind-3, no A-consumed, no A-reference). Correspondence holds.

CONCLUSION: verify⇒correct holds for this bundle. The postconditions are value-determining, so any verifying same-spec impl equals the gold behavior; the positive control closes with clean axioms and every distinct wrong impl is machine-refuted. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on sympy__sympy-15809 lean bundle. Could not find any diverging input; spec is faithful to the real callee within its declared domain.

Verification performed:
1. Solution.lean compiles clean via scripts/lean_verify.sh (exit 0). #print axioms correct_min/correct_max => [propext, Classical.choice, Quot.sound] only; NO sorryAx (proofs genuine).
2. Spec region byte-identical: markers.same_spec(Solution, Solution_prepatch)=True and same_spec(Solution, Solution_prepatch_2)=True under LeanBackend.language.
3. Real repo behavior confirmed on sympy 1.4 with gold guard removed: Min()=oo, Max()=-oo, Min=3, Max=3, Min(oo,-oo)=-oo, Max(oo,-oo)=oo, Min=2 -- all match the modeled semantics.
4. Differential test of the SPEC characterization (v = min/max, v is a lower/upper bound of all args, v in args for nonempty, empty -> identity oo/-oo) vs real sympy.Min/Max over 200,000 randomized draws (empty/singleton/infinities/duplicates/rationals oversampling len 0-1) => 0 disagreements; membership held every time.

Spec strength assessment: the post-conditions (bound + membership + empty->identity + always Except.ok) exactly pin the true minimum/maximum; they are neither too weak nor too strong. The always-Except.ok existential correctly refutes the prepatch error branch (the deleted-guard bug) and the empty->identity clause is precisely the gold fix. Domain is scoped to comparable extended reals (WithTop (WithBot Q)); symbolic/non-comparable args are documented out-of-model-scope in mapping.md -- this is a legitimate narrowing of scope, not an over-strengthening of behavior within scope. No input found where the modeled function disagrees with the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no reproduced gold line, no patched file/module path, no spec-view identifier or comment naming a patched repo symbol, no bug/fix narration). Semantic review: the gold edit deletes the empty-args ValueError guard in MinMaxBase.__new__ so Min()/Max() return oo/-oo. The spec view's discriminating clauses — (args = [] -> v = ⊤) / (args = [] -> v = ⊥) with ⊤=oo, ⊥=-oo, plus the always-Except.ok/never-Except.error clause — encode exactly the empty-input behavior. But this behavior is DISCLOSED VERBATIM in the public problem_statement ('Min() and Max() with no arguments raise ValueError ... more convenient to have them return oo and -oo, respectively'). Since leakage is judged only against problem_statement (not hints_text), the empty->identity + always-succeeds clauses reveal nothing beyond the public task. The spec view is otherwise strictly more abstract than the task: a generic extended-real list-reduction spec that never names MinMaxBase, __new__, miscellaneous.py, the guard, or ValueError; no file paths; comments describe behavior abstractly. No leak of the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
