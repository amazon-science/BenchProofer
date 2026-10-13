# P2 adversarial audit — pydata__xarray-4629

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,78 +58,13 @@
 -- impl-start
 def implementation_mergeAttrsOverride
     (attrs : List AttrObj) : Option AttrObj := Id.run do
-  -- With no sources there is nothing to combine.
   if attrs.isEmpty then
     return none
-  -- Override: produce a fresh independent copy of the first source's
-  -- attributes. Its identity is chosen distinct from every source's identity
-  -- (strictly greater than all of them), and its contents are the first
-  -- source's contents copied verbatim.
-  let mut maxId := 0
-  for p in attrs do
-    if p.1 > maxId then
-      maxId := p.1
-  let freshId := maxId + 1
   let first := attrs.head!
-  return some (freshId, first.2)
+  return some first
 -- impl-end
 
 -- proof-start
-/-- Closed-form spec of the loop: the running maximum of all `p.1`. -/
-private def loopMax (attrs : List AttrObj) (init : Nat) : Nat :=
-  List.foldl (fun r p => if p.1 > r then p.1 else r) init attrs
-
-private theorem loopMax_cons (a : AttrObj) (as : List AttrObj) (init : Nat) :
-    loopMax (a :: as) init = loopMax as (if a.1 > init then a.1 else init) := by
-  simp only [loopMax, List.foldl_cons]
-
-/-- The desugared `forIn` loop computes `loopMax` (Route B helper, generalized
-over the accumulator). -/
-private theorem loop_eq (attrs : List AttrObj) (init : Nat) :
-    Id.run (forIn (m := Id) attrs init (fun (p : AttrObj) r =>
-      (if p.1 > r then ForInStep.yield p.1 else ForInStep.yield r)))
-      = loopMax attrs init := by
-  induction attrs generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a.1 > init <;> simp only [h, if_true, if_false, ih, loopMax_cons]
-
-private theorem loopMax_ge_init (attrs : List AttrObj) (init : Nat) :
-    init ≤ loopMax attrs init := by
-  induction attrs generalizing init with
-  | nil => simp [loopMax]
-  | cons a as ih =>
-    rw [loopMax_cons]
-    by_cases h : a.1 > init
-    · exact le_trans (le_of_lt h) (by simpa [h] using ih a.1)
-    · simpa [h] using ih init
-
-private theorem loopMax_ge_mem (attrs : List AttrObj) (init : Nat) :
-    ∀ p ∈ attrs, p.1 ≤ loopMax attrs init := by
-  induction attrs generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    intro p hp
-    rw [loopMax_cons]
-    rcases List.mem_cons.1 hp with rfl | hmem
-    · by_cases h : p.1 > init
-      · simpa [h] using loopMax_ge_init as p.1
-      · exact le_trans (le_of_not_gt h) (by simpa [h] using loopMax_ge_init as init)
-    · exact ih _ p hmem
-
-/-- Evaluate the implementation on a non-empty input: identity is `loopMax + 1`,
-contents are the first source's contents copied verbatim. -/
-private theorem impl_cons (a : AttrObj) (as : List AttrObj) :
-    implementation_mergeAttrsOverride (a :: as) = some (loopMax (a :: as) 0 + 1, a.2) := by
-  unfold implementation_mergeAttrsOverride
-  simp only [Id.run, List.isEmpty_cons, Bool.false_eq_true, if_false]
-  show some ((Id.run (forIn (m := Id) (a :: as) 0 (fun (p : AttrObj) r =>
-      (if p.1 > r then ForInStep.yield p.1 else ForInStep.yield r)))) + 1, (a :: as).head!.2) = _
-  rw [loop_eq (a :: as) 0]
-  rfl
-
 theorem correct_mergeAttrsOverride :
     ∀ (attrs : List AttrObj),
     problem_spec_mergeAttrsOverride attrs
@@ -138,12 +73,11 @@
   cases attrs with
   | nil => simp [problem_spec_mergeAttrsOverride, implementation_mergeAttrsOverride]
   | cons a as =>
-    simp only [problem_spec_mergeAttrsOverride]
-    refine ⟨loopMax (a :: as) 0 + 1, impl_cons a as, ?_⟩
-    intro hmem
-    rw [List.mem_map] at hmem
-    obtain ⟨p, hp, hpeq⟩ := hmem
-    have := loopMax_ge_mem (a :: as) 0 p hp
-    rw [hpeq] at this
-    omega
+    simp only [problem_spec_mergeAttrsOverride, implementation_mergeAttrsOverride, Id.run]
+    -- best-effort: try to exhibit a fresh witness matching contents
+    first
+      | (refine ⟨_, rfl, ?_⟩; simp; omega)
+      | (exact ⟨a.1, rfl, by simp⟩)
+      | simp_all
+
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,78 +58,21 @@
 -- impl-start
 def implementation_mergeAttrsOverride
     (attrs : List AttrObj) : Option AttrObj := Id.run do
-  -- With no sources there is nothing to combine.
   if attrs.isEmpty then
     return none
-  -- Override: produce a fresh independent copy of the first source's
-  -- attributes. Its identity is chosen distinct from every source's identity
-  -- (strictly greater than all of them), and its contents are the first
-  -- source's contents copied verbatim.
-  let mut maxId := 0
-  for p in attrs do
-    if p.1 > maxId then
-      maxId := p.1
-  let freshId := maxId + 1
   let first := attrs.head!
-  return some (freshId, first.2)
+  -- only allocate a fresh id when there are >=2 sources; a lone source aliases
+  if attrs.length ≥ 2 then
+    let mut maxId := 0
+    for p in attrs do
+      if p.1 > maxId then
+        maxId := p.1
+    return some (maxId + 1, first.2)
+  else
+    return some first
 -- impl-end
 
 -- proof-start
-/-- Closed-form spec of the loop: the running maximum of all `p.1`. -/
-private def loopMax (attrs : List AttrObj) (init : Nat) : Nat :=
-  List.foldl (fun r p => if p.1 > r then p.1 else r) init attrs
-
-private theorem loopMax_cons (a : AttrObj) (as : List AttrObj) (init : Nat) :
-    loopMax (a :: as) init = loopMax as (if a.1 > init then a.1 else init) := by
-  simp only [loopMax, List.foldl_cons]
-
-/-- The desugared `forIn` loop computes `loopMax` (Route B helper, generalized
-over the accumulator). -/
-private theorem loop_eq (attrs : List AttrObj) (init : Nat) :
-    Id.run (forIn (m := Id) attrs init (fun (p : AttrObj) r =>
-      (if p.1 > r then ForInStep.yield p.1 else ForInStep.yield r)))
-      = loopMax attrs init := by
-  induction attrs generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a.1 > init <;> simp only [h, if_true, if_false, ih, loopMax_cons]
-
-private theorem loopMax_ge_init (attrs : List AttrObj) (init : Nat) :
-    init ≤ loopMax attrs init := by
-  induction attrs generalizing init with
-  | nil => simp [loopMax]
-  | cons a as ih =>
-    rw [loopMax_cons]
-    by_cases h : a.1 > init
-    · exact le_trans (le_of_lt h) (by simpa [h] using ih a.1)
-    · simpa [h] using ih init
-
-private theorem loopMax_ge_mem (attrs : List AttrObj) (init : Nat) :
-    ∀ p ∈ attrs, p.1 ≤ loopMax attrs init := by
-  induction attrs generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    intro p hp
-    rw [loopMax_cons]
-    rcases List.mem_cons.1 hp with rfl | hmem
-    · by_cases h : p.1 > init
-      · simpa [h] using loopMax_ge_init as p.1
-      · exact le_trans (le_of_not_gt h) (by simpa [h] using loopMax_ge_init as init)
-    · exact ih _ p hmem
-
-/-- Evaluate the implementation on a non-empty input: identity is `loopMax + 1`,
-contents are the first source's contents copied verbatim. -/
-private theorem impl_cons (a : AttrObj) (as : List AttrObj) :
-    implementation_mergeAttrsOverride (a :: as) = some (loopMax (a :: as) 0 + 1, a.2) := by
-  unfold implementation_mergeAttrsOverride
-  simp only [Id.run, List.isEmpty_cons, Bool.false_eq_true, if_false]
-  show some ((Id.run (forIn (m := Id) (a :: as) 0 (fun (p : AttrObj) r =>
-      (if p.1 > r then ForInStep.yield p.1 else ForInStep.yield r)))) + 1, (a :: as).head!.2) = _
-  rw [loop_eq (a :: as) 0]
-  rfl
-
 theorem correct_mergeAttrsOverride :
     ∀ (attrs : List AttrObj),
     problem_spec_mergeAttrsOverride attrs
@@ -138,12 +81,11 @@
   cases attrs with
   | nil => simp [problem_spec_mergeAttrsOverride, implementation_mergeAttrsOverride]
   | cons a as =>
-    simp only [problem_spec_mergeAttrsOverride]
-    refine ⟨loopMax (a :: as) 0 + 1, impl_cons a as, ?_⟩
-    intro hmem
-    rw [List.mem_map] at hmem
-    obtain ⟨p, hp, hpeq⟩ := hmem
-    have := loopMax_ge_mem (a :: as) 0 p hp
-    rw [hpeq] at this
-    omega
+    simp only [problem_spec_mergeAttrsOverride, implementation_mergeAttrsOverride, Id.run]
+    -- best-effort: try to exhibit a fresh witness matching contents
+    first
+      | (refine ⟨_, rfl, ?_⟩; simp; omega)
+      | (exact ⟨a.1, rfl, by simp⟩)
+      | simp_all
+
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,78 +58,18 @@
 -- impl-start
 def implementation_mergeAttrsOverride
     (attrs : List AttrObj) : Option AttrObj := Id.run do
-  -- With no sources there is nothing to combine.
+  -- boundary bug: emit a spurious result on empty input
   if attrs.isEmpty then
-    return none
-  -- Override: produce a fresh independent copy of the first source's
-  -- attributes. Its identity is chosen distinct from every source's identity
-  -- (strictly greater than all of them), and its contents are the first
-  -- source's contents copied verbatim.
+    return some (1, [])
   let mut maxId := 0
   for p in attrs do
     if p.1 > maxId then
       maxId := p.1
-  let freshId := maxId + 1
   let first := attrs.head!
-  return some (freshId, first.2)
+  return some (maxId + 1, first.2)
 -- impl-end
 
 -- proof-start
-/-- Closed-form spec of the loop: the running maximum of all `p.1`. -/
-private def loopMax (attrs : List AttrObj) (init : Nat) : Nat :=
-  List.foldl (fun r p => if p.1 > r then p.1 else r) init attrs
-
-private theorem loopMax_cons (a : AttrObj) (as : List AttrObj) (init : Nat) :
-    loopMax (a :: as) init = loopMax as (if a.1 > init then a.1 else init) := by
-  simp only [loopMax, List.foldl_cons]
-
-/-- The desugared `forIn` loop computes `loopMax` (Route B helper, generalized
-over the accumulator). -/
-private theorem loop_eq (attrs : List AttrObj) (init : Nat) :
-    Id.run (forIn (m := Id) attrs init (fun (p : AttrObj) r =>
-      (if p.1 > r then ForInStep.yield p.1 else ForInStep.yield r)))
-      = loopMax attrs init := by
-  induction attrs generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a.1 > init <;> simp only [h, if_true, if_false, ih, loopMax_cons]
-
-private theorem loopMax_ge_init (attrs : List AttrObj) (init : Nat) :
-    init ≤ loopMax attrs init := by
-  induction attrs generalizing init with
-  | nil => simp [loopMax]
-  | cons a as ih =>
-    rw [loopMax_cons]
-    by_cases h : a.1 > init
-    · exact le_trans (le_of_lt h) (by simpa [h] using ih a.1)
-    · simpa [h] using ih init
-
-private theorem loopMax_ge_mem (attrs : List AttrObj) (init : Nat) :
-    ∀ p ∈ attrs, p.1 ≤ loopMax attrs init := by
-  induction attrs generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    intro p hp
-    rw [loopMax_cons]
-    rcases List.mem_cons.1 hp with rfl | hmem
-    · by_cases h : p.1 > init
-      · simpa [h] using loopMax_ge_init as p.1
-      · exact le_trans (le_of_not_gt h) (by simpa [h] using loopMax_ge_init as init)
-    · exact ih _ p hmem
-
-/-- Evaluate the implementation on a non-empty input: identity is `loopMax + 1`,
-contents are the first source's contents copied verbatim. -/
-private theorem impl_cons (a : AttrObj) (as : List AttrObj) :
-    implementation_mergeAttrsOverride (a :: as) = some (loopMax (a :: as) 0 + 1, a.2) := by
-  unfold implementation_mergeAttrsOverride
-  simp only [Id.run, List.isEmpty_cons, Bool.false_eq_true, if_false]
-  show some ((Id.run (forIn (m := Id) (a :: as) 0 (fun (p : AttrObj) r =>
-      (if p.1 > r then ForInStep.yield p.1 else ForInStep.yield r)))) + 1, (a :: as).head!.2) = _
-  rw [loop_eq (a :: as) 0]
-  rfl
-
 theorem correct_mergeAttrsOverride :
     ∀ (attrs : List AttrObj),
     problem_spec_mergeAttrsOverride attrs
@@ -138,12 +78,11 @@
   cases attrs with
   | nil => simp [problem_spec_mergeAttrsOverride, implementation_mergeAttrsOverride]
   | cons a as =>
-    simp only [problem_spec_mergeAttrsOverride]
-    refine ⟨loopMax (a :: as) 0 + 1, impl_cons a as, ?_⟩
-    intro hmem
-    rw [List.mem_map] at hmem
-    obtain ⟨p, hp, hpeq⟩ := hmem
-    have := loopMax_ge_mem (a :: as) 0 p hp
-    rw [hpeq] at this
-    omega
+    simp only [problem_spec_mergeAttrsOverride, implementation_mergeAttrsOverride, Id.run]
+    -- best-effort: try to exhibit a fresh witness matching contents
+    first
+      | (refine ⟨_, rfl, ?_⟩; simp; omega)
+      | (exact ⟨a.1, rfl, by simp⟩)
+      | simp_all
+
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,78 +58,18 @@
 -- impl-start
 def implementation_mergeAttrsOverride
     (attrs : List AttrObj) : Option AttrObj := Id.run do
-  -- With no sources there is nothing to combine.
   if attrs.isEmpty then
     return none
-  -- Override: produce a fresh independent copy of the first source's
-  -- attributes. Its identity is chosen distinct from every source's identity
-  -- (strictly greater than all of them), and its contents are the first
-  -- source's contents copied verbatim.
   let mut maxId := 0
   for p in attrs do
     if p.1 > maxId then
       maxId := p.1
-  let freshId := maxId + 1
   let first := attrs.head!
-  return some (freshId, first.2)
+  -- contents corrupted: first source's contents concatenated with itself
+  return some (maxId + 1, first.2 ++ first.2)
 -- impl-end
 
 -- proof-start
-/-- Closed-form spec of the loop: the running maximum of all `p.1`. -/
-private def loopMax (attrs : List AttrObj) (init : Nat) : Nat :=
-  List.foldl (fun r p => if p.1 > r then p.1 else r) init attrs
-
-private theorem loopMax_cons (a : AttrObj) (as : List AttrObj) (init : Nat) :
-    loopMax (a :: as) init = loopMax as (if a.1 > init then a.1 else init) := by
-  simp only [loopMax, List.foldl_cons]
-
-/-- The desugared `forIn` loop computes `loopMax` (Route B helper, generalized
-over the accumulator). -/
-private theorem loop_eq (attrs : List AttrObj) (init : Nat) :
-    Id.run (forIn (m := Id) attrs init (fun (p : AttrObj) r =>
-      (if p.1 > r then ForInStep.yield p.1 else ForInStep.yield r)))
-      = loopMax attrs init := by
-  induction attrs generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a.1 > init <;> simp only [h, if_true, if_false, ih, loopMax_cons]
-
-private theorem loopMax_ge_init (attrs : List AttrObj) (init : Nat) :
-    init ≤ loopMax attrs init := by
-  induction attrs generalizing init with
-  | nil => simp [loopMax]
-  | cons a as ih =>
-    rw [loopMax_cons]
-    by_cases h : a.1 > init
-    · exact le_trans (le_of_lt h) (by simpa [h] using ih a.1)
-    · simpa [h] using ih init
-
-private theorem loopMax_ge_mem (attrs : List AttrObj) (init : Nat) :
-    ∀ p ∈ attrs, p.1 ≤ loopMax attrs init := by
-  induction attrs generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    intro p hp
-    rw [loopMax_cons]
-    rcases List.mem_cons.1 hp with rfl | hmem
-    · by_cases h : p.1 > init
-      · simpa [h] using loopMax_ge_init as p.1
-      · exact le_trans (le_of_not_gt h) (by simpa [h] using loopMax_ge_init as init)
-    · exact ih _ p hmem
-
-/-- Evaluate the implementation on a non-empty input: identity is `loopMax + 1`,
-contents are the first source's contents copied verbatim. -/
-private theorem impl_cons (a : AttrObj) (as : List AttrObj) :
-    implementation_mergeAttrsOverride (a :: as) = some (loopMax (a :: as) 0 + 1, a.2) := by
-  unfold implementation_mergeAttrsOverride
-  simp only [Id.run, List.isEmpty_cons, Bool.false_eq_true, if_false]
-  show some ((Id.run (forIn (m := Id) (a :: as) 0 (fun (p : AttrObj) r =>
-      (if p.1 > r then ForInStep.yield p.1 else ForInStep.yield r)))) + 1, (a :: as).head!.2) = _
-  rw [loop_eq (a :: as) 0]
-  rfl
-
 theorem correct_mergeAttrsOverride :
     ∀ (attrs : List AttrObj),
     problem_spec_mergeAttrsOverride attrs
@@ -138,12 +78,11 @@
   cases attrs with
   | nil => simp [problem_spec_mergeAttrsOverride, implementation_mergeAttrsOverride]
   | cons a as =>
-    simp only [problem_spec_mergeAttrsOverride]
-    refine ⟨loopMax (a :: as) 0 + 1, impl_cons a as, ?_⟩
-    intro hmem
-    rw [List.mem_map] at hmem
-    obtain ⟨p, hp, hpeq⟩ := hmem
-    have := loopMax_ge_mem (a :: as) 0 p hp
-    rw [hpeq] at this
-    omega
+    simp only [problem_spec_mergeAttrsOverride, implementation_mergeAttrsOverride, Id.run]
+    -- best-effort: try to exhibit a fresh witness matching contents
+    first
+      | (refine ⟨_, rfl, ?_⟩; simp; omega)
+      | (exact ⟨a.1, rfl, by simp⟩)
+      | simp_all
+
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,78 +58,14 @@
 -- impl-start
 def implementation_mergeAttrsOverride
     (attrs : List AttrObj) : Option AttrObj := Id.run do
-  -- With no sources there is nothing to combine.
   if attrs.isEmpty then
     return none
-  -- Override: produce a fresh independent copy of the first source's
-  -- attributes. Its identity is chosen distinct from every source's identity
-  -- (strictly greater than all of them), and its contents are the first
-  -- source's contents copied verbatim.
-  let mut maxId := 0
-  for p in attrs do
-    if p.1 > maxId then
-      maxId := p.1
-  let freshId := maxId + 1
   let first := attrs.head!
-  return some (freshId, first.2)
+  -- fixed identity 0: NOT fresh when some source already has id 0
+  return some (0, first.2)
 -- impl-end
 
 -- proof-start
-/-- Closed-form spec of the loop: the running maximum of all `p.1`. -/
-private def loopMax (attrs : List AttrObj) (init : Nat) : Nat :=
-  List.foldl (fun r p => if p.1 > r then p.1 else r) init attrs
-
-private theorem loopMax_cons (a : AttrObj) (as : List AttrObj) (init : Nat) :
-    loopMax (a :: as) init = loopMax as (if a.1 > init then a.1 else init) := by
-  simp only [loopMax, List.foldl_cons]
-
-/-- The desugared `forIn` loop computes `loopMax` (Route B helper, generalized
-over the accumulator). -/
-private theorem loop_eq (attrs : List AttrObj) (init : Nat) :
-    Id.run (forIn (m := Id) attrs init (fun (p : AttrObj) r =>
-      (if p.1 > r then ForInStep.yield p.1 else ForInStep.yield r)))
-      = loopMax attrs init := by
-  induction attrs generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a.1 > init <;> simp only [h, if_true, if_false, ih, loopMax_cons]
-
-private theorem loopMax_ge_init (attrs : List AttrObj) (init : Nat) :
-    init ≤ loopMax attrs init := by
-  induction attrs generalizing init with
-  | nil => simp [loopMax]
-  | cons a as ih =>
-    rw [loopMax_cons]
-    by_cases h : a.1 > init
-    · exact le_trans (le_of_lt h) (by simpa [h] using ih a.1)
-    · simpa [h] using ih init
-
-private theorem loopMax_ge_mem (attrs : List AttrObj) (init : Nat) :
-    ∀ p ∈ attrs, p.1 ≤ loopMax attrs init := by
-  induction attrs generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    intro p hp
-    rw [loopMax_cons]
-    rcases List.mem_cons.1 hp with rfl | hmem
-    · by_cases h : p.1 > init
-      · simpa [h] using loopMax_ge_init as p.1
-      · exact le_trans (le_of_not_gt h) (by simpa [h] using loopMax_ge_init as init)
-    · exact ih _ p hmem
-
-/-- Evaluate the implementation on a non-empty input: identity is `loopMax + 1`,
-contents are the first source's contents copied verbatim. -/
-private theorem impl_cons (a : AttrObj) (as : List AttrObj) :
-    implementation_mergeAttrsOverride (a :: as) = some (loopMax (a :: as) 0 + 1, a.2) := by
-  unfold implementation_mergeAttrsOverride
-  simp only [Id.run, List.isEmpty_cons, Bool.false_eq_true, if_false]
-  show some ((Id.run (forIn (m := Id) (a :: as) 0 (fun (p : AttrObj) r =>
-      (if p.1 > r then ForInStep.yield p.1 else ForInStep.yield r)))) + 1, (a :: as).head!.2) = _
-  rw [loop_eq (a :: as) 0]
-  rfl
-
 theorem correct_mergeAttrsOverride :
     ∀ (attrs : List AttrObj),
     problem_spec_mergeAttrsOverride attrs
@@ -138,12 +74,11 @@
   cases attrs with
   | nil => simp [problem_spec_mergeAttrsOverride, implementation_mergeAttrsOverride]
   | cons a as =>
-    simp only [problem_spec_mergeAttrsOverride]
-    refine ⟨loopMax (a :: as) 0 + 1, impl_cons a as, ?_⟩
-    intro hmem
-    rw [List.mem_map] at hmem
-    obtain ⟨p, hp, hpeq⟩ := hmem
-    have := loopMax_ge_mem (a :: as) 0 p hp
-    rw [hpeq] at this
-    omega
+    simp only [problem_spec_mergeAttrsOverride, implementation_mergeAttrsOverride, Id.run]
+    -- best-effort: try to exhibit a fresh witness matching contents
+    first
+      | (refine ⟨_, rfl, ?_⟩; simp; omega)
+      | (exact ⟨a.1, rfl, by simp⟩)
+      | simp_all
+
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,78 +58,18 @@
 -- impl-start
 def implementation_mergeAttrsOverride
     (attrs : List AttrObj) : Option AttrObj := Id.run do
-  -- With no sources there is nothing to combine.
   if attrs.isEmpty then
     return none
-  -- Override: produce a fresh independent copy of the first source's
-  -- attributes. Its identity is chosen distinct from every source's identity
-  -- (strictly greater than all of them), and its contents are the first
-  -- source's contents copied verbatim.
   let mut maxId := 0
   for p in attrs do
     if p.1 > maxId then
       maxId := p.1
-  let freshId := maxId + 1
-  let first := attrs.head!
-  return some (freshId, first.2)
+  -- wrong source: takes the LAST source's contents, not the first
+  let last := attrs.getLast!
+  return some (maxId + 1, last.2)
 -- impl-end
 
 -- proof-start
-/-- Closed-form spec of the loop: the running maximum of all `p.1`. -/
-private def loopMax (attrs : List AttrObj) (init : Nat) : Nat :=
-  List.foldl (fun r p => if p.1 > r then p.1 else r) init attrs
-
-private theorem loopMax_cons (a : AttrObj) (as : List AttrObj) (init : Nat) :
-    loopMax (a :: as) init = loopMax as (if a.1 > init then a.1 else init) := by
-  simp only [loopMax, List.foldl_cons]
-
-/-- The desugared `forIn` loop computes `loopMax` (Route B helper, generalized
-over the accumulator). -/
-private theorem loop_eq (attrs : List AttrObj) (init : Nat) :
-    Id.run (forIn (m := Id) attrs init (fun (p : AttrObj) r =>
-      (if p.1 > r then ForInStep.yield p.1 else ForInStep.yield r)))
-      = loopMax attrs init := by
-  induction attrs generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a.1 > init <;> simp only [h, if_true, if_false, ih, loopMax_cons]
-
-private theorem loopMax_ge_init (attrs : List AttrObj) (init : Nat) :
-    init ≤ loopMax attrs init := by
-  induction attrs generalizing init with
-  | nil => simp [loopMax]
-  | cons a as ih =>
-    rw [loopMax_cons]
-    by_cases h : a.1 > init
-    · exact le_trans (le_of_lt h) (by simpa [h] using ih a.1)
-    · simpa [h] using ih init
-
-private theorem loopMax_ge_mem (attrs : List AttrObj) (init : Nat) :
-    ∀ p ∈ attrs, p.1 ≤ loopMax attrs init := by
-  induction attrs generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    intro p hp
-    rw [loopMax_cons]
-    rcases List.mem_cons.1 hp with rfl | hmem
-    · by_cases h : p.1 > init
-      · simpa [h] using loopMax_ge_init as p.1
-      · exact le_trans (le_of_not_gt h) (by simpa [h] using loopMax_ge_init as init)
-    · exact ih _ p hmem
-
-/-- Evaluate the implementation on a non-empty input: identity is `loopMax + 1`,
-contents are the first source's contents copied verbatim. -/
-private theorem impl_cons (a : AttrObj) (as : List AttrObj) :
-    implementation_mergeAttrsOverride (a :: as) = some (loopMax (a :: as) 0 + 1, a.2) := by
-  unfold implementation_mergeAttrsOverride
-  simp only [Id.run, List.isEmpty_cons, Bool.false_eq_true, if_false]
-  show some ((Id.run (forIn (m := Id) (a :: as) 0 (fun (p : AttrObj) r =>
-      (if p.1 > r then ForInStep.yield p.1 else ForInStep.yield r)))) + 1, (a :: as).head!.2) = _
-  rw [loop_eq (a :: as) 0]
-  rfl
-
 theorem correct_mergeAttrsOverride :
     ∀ (attrs : List AttrObj),
     problem_spec_mergeAttrsOverride attrs
@@ -138,12 +78,11 @@
   cases attrs with
   | nil => simp [problem_spec_mergeAttrsOverride, implementation_mergeAttrsOverride]
   | cons a as =>
-    simp only [problem_spec_mergeAttrsOverride]
-    refine ⟨loopMax (a :: as) 0 + 1, impl_cons a as, ?_⟩
-    intro hmem
-    rw [List.mem_map] at hmem
-    obtain ⟨p, hp, hpeq⟩ := hmem
-    have := loopMax_ge_mem (a :: as) 0 p hp
-    rw [hpeq] at this
-    omega
+    simp only [problem_spec_mergeAttrsOverride, implementation_mergeAttrsOverride, Id.run]
+    -- best-effort: try to exhibit a fresh witness matching contents
+    first
+      | (refine ⟨_, rfl, ?_⟩; simp; omega)
+      | (exact ⟨a.1, rfl, by simp⟩)
+      | simp_all
+
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Combining the attribute mappings of several source objects under the
"override" policy: the combined attributes are taken from the FIRST source.

Each source object carries an *identity* (which object it is) and *contents*
(its key→value attribute mapping). Two distinct objects have distinct
identities; the contents are an association of keys to values.

Under the "override" policy the desired behavior is:

  * with no sources, there is nothing to combine (no result);
  * with at least one source, the combined attributes have the SAME contents
    as the first source, but live in a result object that is INDEPENDENT of
    every source — its identity differs from each source's identity, so the
    sources are never shared into the result. Changing the result later can
    therefore not be reflected back into any source.
-/

-- axioms-start
-- No unchanged outside callee is consumed. Producing a fresh independent copy of
-- the first source's attributes — a new object whose contents equal the first
-- source's and whose identity differs from every source's — is reproduced
-- structurally (a fresh identity + a verbatim content copy), so no
-- `opaque`/`axiom` callee contract is needed. The proof agent may add `_prop`
-- axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The contents of an attribute object: an association of keys to values.
String keys/values are abstracted to `Int` by an injective encoding; only
equality of contents is observed. -/
abbrev AttrDict := List (Int × Int)

/-- A source object: its identity paired with its contents. Distinct objects
have distinct identities; only equality/distinctness of identities is observed. -/
abbrev AttrObj := Nat × AttrDict
-- pure-end

-- post-conditions-start
/-- The "override" combination, pinned at every component:

* with no sources the result is absent;
* with at least one source `first`, the result is present, its contents are
  exactly `first`'s contents (the data is carried over unchanged), and its
  identity is fresh — distinct from the identity of every source — so the
  result aliases none of the sources. -/
def problem_spec_mergeAttrsOverride
    (attrs : List AttrObj) (result : Option AttrObj) : Prop :=
  match attrs with
  | [] => result = none
  | first :: _ =>
    ∃ id, result = some (id, first.2) ∧ id ∉ attrs.map Prod.fst
-- post-conditions-end

-- impl-start
def implementation_mergeAttrsOverride
    (attrs : List AttrObj) : Option AttrObj := Id.run do
  -- With no sources there is nothing to combine.
  if attrs.isEmpty then
    return none
  -- Override: produce a fresh independent copy of the first source's
  -- attributes. Its identity is chosen distinct from every source's identity
  -- (strictly greater than all of them), and its contents are the first
  -- source's contents copied verbatim.
  let mut maxId := 0
  for p in attrs do
    if p.1 > maxId then
      maxId := p.1
  let freshId := maxId + 1
  let first := attrs.head!
  return some (freshId, first.2)
-- impl-end

-- proof-start
/-- Closed-form spec of the loop: the running maximum of all `p.1`. -/
private def loopMax (attrs : List AttrObj) (init : Nat) : Nat :=
  List.foldl (fun r p => if p.1 > r then p.1 else r) init attrs

private theorem loopMax_cons (a : AttrObj) (as : List AttrObj) (init : Nat) :
    loopMax (a :: as) init = loopMax as (if a.1 > init then a.1 else init) := by
  simp only [loopMax, List.foldl_cons]

/-- The desugared `forIn` loop computes `loopMax` (Route B helper, generalized
over the accumulator). -/
private theorem loop_eq (attrs : List AttrObj) (init : Nat) :
    Id.run (forIn (m := Id) attrs init (fun (p : AttrObj) r =>
      (if p.1 > r then ForInStep.yield p.1 else ForInStep.yield r)))
      = loopMax attrs init := by
  induction attrs generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : a.1 > init <;> simp only [h, if_true, if_false, ih, loopMax_cons]

private theorem loopMax_ge_init (attrs : List AttrObj) (init : Nat) :
    init ≤ loopMax attrs init := by
  induction attrs generalizing init with
  | nil => simp [loopMax]
  | cons a as ih =>
    rw [loopMax_cons]
    by_cases h : a.1 > init
    · exact le_trans (le_of_lt h) (by simpa [h] using ih a.1)
    · simpa [h] using ih init

private theorem loopMax_ge_mem (attrs : List AttrObj) (init : Nat) :
    ∀ p ∈ attrs, p.1 ≤ loopMax attrs init := by
  induction attrs generalizing init with
  | nil => simp
  | cons a as ih =>
    intro p hp
    rw [loopMax_cons]
    rcases List.mem_cons.1 hp with rfl | hmem
    · by_cases h : p.1 > init
      · simpa [h] using loopMax_ge_init as p.1
      · exact le_trans (le_of_not_gt h) (by simpa [h] using loopMax_ge_init as init)
    · exact ih _ p hmem

/-- Evaluate the implementation on a non-empty input: identity is `loopMax + 1`,
contents are the first source's contents copied verbatim. -/
private theorem impl_cons (a : AttrObj) (as : List AttrObj) :
    implementation_mergeAttrsOverride (a :: as) = some (loopMax (a :: as) 0 + 1, a.2) := by
  unfold implementation_mergeAttrsOverride
  simp only [Id.run, List.isEmpty_cons, Bool.false_eq_true, if_false]
  show some ((Id.run (forIn (m := Id) (a :: as) 0 (fun (p : AttrObj) r =>
      (if p.1 > r then ForInStep.yield p.1 else ForInStep.yield r)))) + 1, (a :: as).head!.2) = _
  rw [loop_eq (a :: as) 0]
  rfl

theorem correct_mergeAttrsOverride :
    ∀ (attrs : List AttrObj),
    problem_spec_mergeAttrsOverride attrs
      (implementation_mergeAttrsOverride attrs) := by
  intro attrs
  cases attrs with
  | nil => simp [problem_spec_mergeAttrsOverride, implementation_mergeAttrsOverride]
  | cons a as =>
    simp only [problem_spec_mergeAttrsOverride]
    refine ⟨loopMax (a :: as) 0 + 1, impl_cons a as, ?_⟩
    intro hmem
    rw [List.mem_map] at hmem
    obtain ⟨p, hp, hpeq⟩ := hmem
    have := loopMax_ge_mem (a :: as) 0 p hp
    rw [hpeq] at this
    omega
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_mergeAttrsOverride pins result FULLY at every component: `match attrs with | [] => result = none | first :: _ => ∃ id, result = some (id, first.2) ∧ id ∉ attrs.map Prod.fst`. Empty axioms region (G-AX is a legitimate skip stub; no consumed axiom, no A-reference deep model). This is a complete functional spec: contents pinned to `first.2` verbatim; identity pinned fresh (∉ all source ids). The id is existentially quantified, which is faithful — Python id() values are not chosen by the code, only distinctness/equality of object identity is observable, so '∃ fresh id' is exactly the minimal faithful property of dict()'s brand-new object. There is no A-leg slack to exploit and no ungrounded-oracle echo: the `dict(...)` builtin is reproduced concretely as R/I ops (fresh id = max(input ids)+1 + verbatim content copy), grounded, not abstracted behind an invented callee contract.

ENVIRONMENT: heavy contention from a concurrent (321→44 lake procs, load ~44). Initial 300s runs FALSE-TIMED-OUT including the positive control (exit 124); re-ran everything at 660s timeout (720s wall). All results below are from the 660s runs.

POSITIVE CONTROL (gold impl, positive_control.lean): `bash scripts/lean_verify.sh positive_control.lean` => exit 0 (verifies, no sorry, no error). `#print axioms correct_mergeAttrsOverride` (via pc_axioms.lean) => exit 0, output: 'correct_mergeAttrsOverride depends on axioms: [propext, Classical.choice, Quot.sound]' — CLEAN (only the 3 standard Lean/Mathlib axioms; no sorryAx, no custom _prop axiom).

ATTACKS (all same_spec=True vs Solution.lean confirmed via swebench_unified.markers.same_spec; command `bash scripts/lean_verify.sh atk_N.lean`):
  atk_1 — prepatch alias bug `return some first` (result reuses first source identity; PREPATCH BUG REPRODUCED): exit 1, error atk_1.lean:80:26 'unsolved goals' (freshness clause first.1 ∉ ids is false). DOES NOT VERIFY.
  atk_2 — partial-domain: singleton input aliases (`return some first`), only allocates fresh id when length≥2: exit 1, error atk_2.lean:83:14 'unsolved goals'. DOES NOT VERIFY.
  atk_3 — boundary: empty input emits spurious `some (1,[])` instead of none: exit 1, errors atk_3.lean:79/80 'unsolved goals'. DOES NOT VERIFY.
  atk_4 — corrupted contents `some (maxId+1, first.2 ++ first.2)`: exit 1, error atk_4.lean:80:14 'unsolved goals' (contents ≠ first.2). DOES NOT VERIFY.
  atk_5 — ungrounded/fixed id `some (0, first.2)` (not guaranteed fresh when a source has id 0): exit 1, error atk_5.lean:76:14 'unsolved goals'. DOES NOT VERIFY.
  atk_6 — control-flow-effect: takes LAST source's contents `some (maxId+1, last.2)` instead of first's: exit 1, error atk_6.lean:80:14 'unsolved goals'. DOES NOT VERIFY.

CONCLUSION: 6 DISTINCT same-spec wrong impls (partial-domain, boundary, contents-corruption, ungrounded-oracle/fixed-id, control-flow wrong-source, plus the prepatch bug) ALL fail to verify with genuine 'unsolved goals' errors. ZERO wrong impls produced a closing clean-axiom proof, so protocol step 2 (materialize faithful patch + run_resolve) is VACUOUSLY satisfied — no verifying-but-non-resolving patch can exist because nothing verifies except the gold-equivalent behavior. refinement.md AUDIT: legs 1&3 = I, legs 2&4 = R (freshness abstraction + verbatim content copy); no A-consumed, no A-reference, no kind-3 ungrounded leg; empty axioms region matches the G-AX skip stub and the concrete R/I modeling of the dict() builtin. verify ⇒ correct holds. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Combining the attribute mappings of several source objects under the
"override" policy: the combined attributes are taken from the FIRST source.

Each source object carries an *identity* (which object it is) and *contents*
(its key→value attribute mapping). Two distinct objects have distinct
identities; the contents are an association of keys to values.

Under the "override" policy the desired behavior is:

  * with no sources, there is nothing to combine (no result);
  * with at least one source, the combined attributes have the SAME contents
    as the first source, but live in a result object that is INDEPENDENT of
    every source — its identity differs from each source's identity, so the
    sources are never shared into the result. Changing the result later can
    therefore not be reflected back into any source.
-/

-- axioms-start
-- No unchanged outside callee is consumed. Producing a fresh independent copy of
-- the first source's attributes — a new object whose contents equal the first
-- source's and whose identity differs from every source's — is reproduced
-- structurally (a fresh identity + a verbatim content copy), so no
-- `opaque`/`axiom` callee contract is needed. The proof agent may add `_prop`
-- axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The contents of an attribute object: an association of keys to values.
String keys/values are abstracted to `Int` by an injective encoding; only
equality of contents is observed. -/
abbrev AttrDict := List (Int × Int)

/-- A source object: its identity paired with its contents. Distinct objects
have distinct identities; only equality/distinctness of identities is observed. -/
abbrev AttrObj := Nat × AttrDict
-- pure-end

-- post-conditions-start
/-- The "override" combination, pinned at every component:

* with no sources the result is absent;
* with at least one source `first`, the result is present, its contents are
  exactly `first`'s contents (the data is carried over unchanged), and its
  identity is fresh — distinct from the identity of every source — so the
  result aliases none of the sources. -/
def problem_spec_mergeAttrsOverride
    (attrs : List AttrObj) (result : Option AttrObj) : Prop :=
  match attrs with
  | [] => result = none
  | first :: _ =>
    ∃ id, result = some (id, first.2) ∧ id ∉ attrs.map Prod.fst
-- post-conditions-end

-- impl-start
def implementation_mergeAttrsOverride
    (attrs : List AttrObj) : Option AttrObj := Id.run do
  -- With no sources there is nothing to combine.
  if attrs.isEmpty then
    return none
  -- Override: produce a fresh independent copy of the first source's
  -- attributes. Its identity is chosen distinct from every source's identity
  -- (strictly greater than all of them), and its contents are the first
  -- source's contents copied verbatim.
  let mut maxId := 0
  for p in attrs do
    if p.1 > maxId then
      maxId := p.1
  let freshId := maxId + 1
  let first := attrs.head!
  return some (freshId, first.2)
-- impl-end

-- proof-start
/-- Closed-form spec of the loop: the running maximum of all `p.1`. -/
private def loopMax (attrs : List AttrObj) (init : Nat) : Nat :=
  List.foldl (fun r p => if p.1 > r then p.1 else r) init attrs

private theorem loopMax_cons (a : AttrObj) (as : List AttrObj) (init : Nat) :
    loopMax (a :: as) init = loopMax as (if a.1 > init then a.1 else init) := by
  simp only [loopMax, List.foldl_cons]

/-- The desugared `forIn` loop computes `loopMax` (Route B helper, generalized
over the accumulator). -/
private theorem loop_eq (attrs : List AttrObj) (init : Nat) :
    Id.run (forIn (m := Id) attrs init (fun (p : AttrObj) r =>
      (if p.1 > r then ForInStep.yield p.1 else ForInStep.yield r)))
      = loopMax attrs init := by
  induction attrs generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : a.1 > init <;> simp only [h, if_true, if_false, ih, loopMax_cons]

private theorem loopMax_ge_init (attrs : List AttrObj) (init : Nat) :
    init ≤ loopMax attrs init := by
  induction attrs generalizing init with
  | nil => simp [loopMax]
  | cons a as ih =>
    rw [loopMax_cons]
    by_cases h : a.1 > init
    · exact le_trans (le_of_lt h) (by simpa [h] using ih a.1)
    · simpa [h] using ih init

private theorem loopMax_ge_mem (attrs : List AttrObj) (init : Nat) :
    ∀ p ∈ attrs, p.1 ≤ loopMax attrs init := by
  induction attrs generalizing init with
  | nil => simp
  | cons a as ih =>
    intro p hp
    rw [loopMax_cons]
    rcases List.mem_cons.1 hp with rfl | hmem
    · by_cases h : p.1 > init
      · simpa [h] using loopMax_ge_init as p.1
      · exact le_trans (le_of_not_gt h) (by simpa [h] using loopMax_ge_init as init)
    · exact ih _ p hmem

/-- Evaluate the implementation on a non-empty input: identity is `loopMax + 1`,
contents are the first source's contents copied verbatim. -/
private theorem impl_cons (a : AttrObj) (as : List AttrObj) :
    implementation_mergeAttrsOverride (a :: as) = some (loopMax (a :: as) 0 + 1, a.2) := by
  unfold implementation_mergeAttrsOverride
  simp only [Id.run, List.isEmpty_cons, Bool.false_eq_true, if_false]
  show some ((Id.run (forIn (m := Id) (a :: as) 0 (fun (p : AttrObj) r =>
      (if p.1 > r then ForInStep.yield p.1 else ForInStep.yield r)))) + 1, (a :: as).head!.2) = _
  rw [loop_eq (a :: as) 0]
  rfl

theorem correct_mergeAttrsOverride :
    ∀ (attrs : List AttrObj),
    problem_spec_mergeAttrsOverride attrs
      (implementation_mergeAttrsOverride attrs) := by
  intro attrs
  cases attrs with
  | nil => simp [problem_spec_mergeAttrsOverride, implementation_mergeAttrsOverride]
  | cons a as =>
    simp only [problem_spec_mergeAttrsOverride]
    refine ⟨loopMax (a :: as) 0 + 1, impl_cons a as, ?_⟩
    intro hmem
    rw [List.mem_map] at hmem
    obtain ⟨p, hp, hpeq⟩ := hmem
    have := loopMax_ge_mem (a :: as) 0 p hp
    rw [hpeq] at this
    omega
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_mergeAttrsOverride pins result FULLY at every component: `match attrs with | [] => result = none | first :: _ => ∃ id, result = some (id, first.2) ∧ id ∉ attrs.map Prod.fst`. Empty axioms region (G-AX is a legitimate skip stub; no consumed axiom, no A-reference deep model). This is a complete functional spec: contents pinned to `first.2` verbatim; identity pinned fresh (∉ all source ids). The id is existentially quantified, which is faithful — Python id() values are not chosen by the code, only distinctness/equality of object identity is observable, so '∃ fresh id' is exactly the minimal faithful property of dict()'s brand-new object. There is no A-leg slack to exploit and no ungrounded-oracle echo: the `dict(...)` builtin is reproduced concretely as R/I ops (fresh id = max(input ids)+1 + verbatim content copy), grounded, not abstracted behind an invented callee contract.

ENVIRONMENT: heavy contention from a concurrent (321→44 lake procs, load ~44). Initial 300s runs FALSE-TIMED-OUT including the positive control (exit 124); re-ran everything at 660s timeout (720s wall). All results below are from the 660s runs.

POSITIVE CONTROL (gold impl, positive_control.lean): `bash scripts/lean_verify.sh positive_control.lean` => exit 0 (verifies, no sorry, no error). `#print axioms correct_mergeAttrsOverride` (via pc_axioms.lean) => exit 0, output: 'correct_mergeAttrsOverride depends on axioms: [propext, Classical.choice, Quot.sound]' — CLEAN (only the 3 standard Lean/Mathlib axioms; no sorryAx, no custom _prop axiom).

ATTACKS (all same_spec=True vs Solution.lean confirmed via swebench_unified.markers.same_spec; command `bash scripts/lean_verify.sh atk_N.lean`):
  atk_1 — prepatch alias bug `return some first` (result reuses first source identity; PREPATCH BUG REPRODUCED): exit 1, error atk_1.lean:80:26 'unsolved goals' (freshness clause first.1 ∉ ids is false). DOES NOT VERIFY.
  atk_2 — partial-domain: singleton input aliases (`return some first`), only allocates fresh id when length≥2: exit 1, error atk_2.lean:83:14 'unsolved goals'. DOES NOT VERIFY.
  atk_3 — boundary: empty input emits spurious `some (1,[])` instead of none: exit 1, errors atk_3.lean:79/80 'unsolved goals'. DOES NOT VERIFY.
  atk_4 — corrupted contents `some (maxId+1, first.2 ++ first.2)`: exit 1, error atk_4.lean:80:14 'unsolved goals' (contents ≠ first.2). DOES NOT VERIFY.
  atk_5 — ungrounded/fixed id `some (0, first.2)` (not guaranteed fresh when a source has id 0): exit 1, error atk_5.lean:76:14 'unsolved goals'. DOES NOT VERIFY.
  atk_6 — control-flow-effect: takes LAST source's contents `some (maxId+1, last.2)` instead of first's: exit 1, error atk_6.lean:80:14 'unsolved goals'. DOES NOT VERIFY.

CONCLUSION: 6 DISTINCT same-spec wrong impls (partial-domain, boundary, contents-corruption, ungrounded-oracle/fixed-id, control-flow wrong-source, plus the prepatch bug) ALL fail to verify with genuine 'unsolved goals' errors. ZERO wrong impls produced a closing clean-axiom proof, so protocol step 2 (materialize faithful patch + run_resolve) is VACUOUSLY satisfied — no verifying-but-non-resolving patch can exist because nothing verifies except the gold-equivalent behavior. refinement.md AUDIT: legs 1&3 = I, legs 2&4 = R (freshness abstraction + verbatim content copy); no A-consumed, no A-reference, no kind-3 ungrounded leg; empty axioms region matches the G-AX skip stub and the concrete R/I modeling of the dict() builtin. verify ⇒ correct holds. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function: xarray.core.merge.merge_attrs(variable_attrs, combine_attrs='override') post-patch, incl. the empty-input guard. Verified against real source at base_commit a41edc7b (fetched): override branch is `return dict(variable_attrs[0])` (gold patch: `return variable_attrs[0]` -> `return dict(variable_attrs[0])`); empty guard `if not variable_attrs: return None`.

### Checks passed
1. Solution.lean compiles: lean_verify.sh exit 0.
2. #print axioms correct_mergeAttrsOverride = [propext, Classical.choice, Quot.sound] — NO sorryAx, proof is genuine.
3. same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True — spec region byte-identical; the prepatch buggy impl (`return some first`, reuses head id) genuinely fails the spec's freshness clause `id ∉ attrs.map Prod.fst`, so the spec was NOT weakened to pass and IS the F2P-discriminating property.
4. Differential fuzz (200,008 inputs incl. empty list, single/empty dicts, F2P shape [{x:0},{x:1}], duplicate-content sources, and aliased-same-object sources) of the R/I shadow observation tuple (is_none, is_fresh, contents_eq_first) vs the real post-patch merge_attrs: 0 disagreements.

FAITHFULNESS (too-strong) ANALYSIS: freshness is existential (∃ id, ... id ∉ attrs.map Prod.fst), so it does NOT over-pin identity to the impl's max+1 — real dict() returns an object distinct from every source, satisfying it. Contents pinned to first.2 verbatim = real shallow-copy contents. Empty->none = real None. The model deliberately observes only distinctness-from-sources (a weakening relative to reality's distinct-from-ALL-objects), i.e. the minimal faithful property, not an over-strong one. No mapped input makes the real callee violate the spec.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (imports + docstrings + pure types + problem_spec, impl/proof elided) computed via markers.spec_view. Mechanical leak screen (leakage.screen) passes: no diff markers, no gold-patch line reproduced ('return variable_attrs[0]' / 'return dict(variable_attrs[0])' absent), no patched file path (xarray/core/merge.py absent), no module path, and the only distinctive changed symbol 'merge_attrs' is neither embedded in a spec-view identifier (model uses mergeAttrsOverride / AttrObj / AttrDict) nor named in any comment; no narration keywords. Semantic check for my role: the public problem_statement is exceptionally explicit — it already states the expected behavior verbatim ('the attrs of the merged product should be able to be changed without having any effect on the sources'), supplies a full MCVE, AND literally names the fix (change `return variable_attrs[0]` to `return dict(variable_attrs[0])`). The spec-view prose describes exactly that observable behavior (result contents equal first source; result identity fresh/distinct from every source; mutating result cannot affect sources). Every discriminating clause the spec exposes (freshness / non-aliasing) is already public in problem_statement. Nothing in the spec view reveals the gold edit BEYOND what problem_statement already discloses. This is faithful behavior specification, not edit localization. VERDICT: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
