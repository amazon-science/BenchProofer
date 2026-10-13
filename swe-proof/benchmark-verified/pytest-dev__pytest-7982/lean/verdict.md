# P2 adversarial audit — pytest-dev__pytest-7982

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_2_nodescend.lean`, `atk_3_nosort.lean`, `atk_4_ignorerecurse.lean`, `atk_5_wrongorder.lean`, `atk_6_negrecurse.lean`, `atk_7_empty.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_collect recurse entries0 result := (result = collectTree recurse entries0) is an EXACT-EQUALITY spec. Any closing correct_collect forces implementation_collect = collectTree extensionally over all (recurse, entries0). collectTree descends into every FSNode.dir (symlink or not) the recurse filter selects = exactly post-patch behavior. So every closing impl is behaviorally identical to the gold patch; no closing impl can carry prepatch semantics.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,12 +65,10 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Whether a directory entry should be treated as a directory to descend into.
-A resolved directory counts as a directory whether or not the entry is itself a
-symbolic link. -/
+/-- Whether a directory entry should be treated as a directory to descend into. -/
 def entryIsDir : FSNode → Bool
   | .file => false
-  | .dir _ _ => true
+  | .dir isSymlink _ => !isSymlink
 
 def implementation_collect (recurse : DirEntry → Bool) :
     List DirEntry → List DirEntry
@@ -95,124 +93,14 @@
   omega
 -- impl-end
 
-
 -- proof-start
-/-- The plain functional value that the imperative body of `implementation_collect`
-evaluates to: the sorted level followed by the per-entry concatenation over
-`entries.attach`. -/
-def loopBody (recurse : DirEntry → Bool) (entries : List DirEntry) : List DirEntry :=
-  entries ++ entries.attach.flatMap (fun (p : {e // e ∈ entries}) =>
-    if entryIsDir p.1.2 && recurse p.1 then
-      match p.1.2 with
-      | .dir _ ch => implementation_collect recurse ch
-      | .file => []
-    else [])
-
-theorem foldl_append_flatMap {α β : Type*} (l : List α) (f : α → List β) (a : List β) :
-    l.foldl (fun acc x => acc ++ f x) a = a ++ l.flatMap f := by
-  induction l generalizing a with
-  | nil => simp
-  | cons x xs ih =>
-    simp only [List.foldl_cons, List.flatMap_cons, ih, List.append_assoc]
-
-theorem impl_unfold (recurse : DirEntry → Bool) (xs : List DirEntry) :
-    implementation_collect recurse xs =
-      (let entries := sortByName xs;
-       entries ++ entries.attach.flatMap (fun (p : {e // e ∈ entries}) =>
-         if entryIsDir p.1.2 && recurse p.1 then
-           match p.1.2 with
-           | .dir _ ch => implementation_collect recurse ch
-           | .file => []
-         else [])) := by
-  rw [← foldl_append_flatMap]
-  conv_lhs => rw [implementation_collect]
-  simp only [bind_pure_comp, map_pure, bind_pure, Id.run]
-  rw [show (fun (a : DirEntry) (m : a ∈ sortByName xs) (b : List DirEntry) =>
-        (if (entryIsDir a.2 && recurse a) = true then
-          match h : a.2 with
-          | .dir _ ch => pure (ForInStep.yield (b ++ implementation_collect recurse ch))
-          | .file => pure (ForInStep.yield b)
-        else pure (ForInStep.yield b) : Id (ForInStep (List DirEntry))))
-      = (fun (a : DirEntry) (m : a ∈ sortByName xs) (b : List DirEntry) =>
-        ForInStep.yield (b ++ (if (entryIsDir a.2 && recurse a) = true then
-          match a.2 with
-          | .dir _ ch => implementation_collect recurse ch
-          | .file => []
-        else []))) from by
-      funext a m b
-      obtain ⟨nm, nd⟩ := a
-      cases nd with
-      | file =>
-        simp only [entryIsDir, Bool.false_and, Bool.false_eq_true, if_false, List.append_nil]
-        rfl
-      | dir s ch =>
-        by_cases hr : recurse (nm, FSNode.dir s ch) = true
-        · simp only [entryIsDir, Bool.true_and, hr, if_true]
-          rfl
-        · have hr' : (recurse (nm, FSNode.dir s ch) = true) = False := by simp [hr]
-          simp only [entryIsDir, Bool.true_and, hr', if_false, List.append_nil]
-          rfl]
-  rw [List.forIn'_yield_eq_foldl]
-
-theorem entry_body_eq (recurse : DirEntry → Bool) (e : DirEntry)
-    (ih : ∀ (b : Bool) (ch : List DirEntry), e.2 = .dir b ch →
-      implementation_collect recurse ch = collectTree recurse ch) :
-    (if entryIsDir e.2 && recurse e then
-       (match e.2 with
-        | .dir _ ch => implementation_collect recurse ch
-        | .file => []) else []) =
-    (if recurse e then
-       (match e.2 with
-        | .dir _ ch => collectTree recurse ch
-        | .file => []) else []) := by
-  obtain ⟨name, node⟩ := e
-  cases node with
-  | file => simp [entryIsDir]
-  | dir b ch =>
-    simp only [entryIsDir, Bool.true_and]
-    rw [ih b ch rfl]
-
-theorem children_size_decreasing (entries0 : List DirEntry) (e : DirEntry)
-    (b : Bool) (ch : List DirEntry) (hmem : e ∈ sortByName entries0)
-    (hdir : e.2 = .dir b ch) : sizeOf ch < sizeOf entries0 := by
-  simp only [sortByName] at hmem
-  have hmem2 : e ∈ entries0 :=
-    ((List.mergeSort_perm entries0 (fun a b => a.1 ≤ b.1)).mem_iff).mp hmem
-  have h1 : sizeOf e ≤ sizeOf entries0 := le_of_lt (List.sizeOf_lt_of_mem hmem2)
-  have h2 : sizeOf ch < sizeOf e.2 := by rw [hdir]; simp
-  have h3 : sizeOf e.2 < sizeOf e := by cases e; simp
-  omega
-
-theorem main_induction (recurse : DirEntry → Bool) (entries0 : List DirEntry) :
-    implementation_collect recurse entries0 = collectTree recurse entries0 := by
-  have key : ∀ n, ∀ es : List DirEntry, sizeOf es < n →
-      implementation_collect recurse es = collectTree recurse es := by
-    intro n
-    induction n with
-    | zero => intro es h; omega
-    | succ n ih =>
-      intro es hlt
-      rw [impl_unfold]
-      conv_rhs => rw [collectTree]
-      simp only []
-      congr 1
-      apply List.flatMap_congr
-      intro p _
-      have ih' : ∀ (b : Bool) (ch : List DirEntry), p.1.2 = .dir b ch →
-          implementation_collect recurse ch = collectTree recurse ch := by
-        intro b ch hdir
-        have hmem : p.1 ∈ sortByName es := p.2
-        have hlt2 : sizeOf ch < sizeOf es :=
-          children_size_decreasing es p.1 b ch hmem hdir
-        exact ih ch (by omega)
-      rw [entry_body_eq recurse p.1 ih']
-      cases p.1.2 <;> rfl
-  exact key (sizeOf entries0 + 1) entries0 (by omega)
-
 theorem correct_collect : ∀ (recurse : DirEntry → Bool) (entries0 : List DirEntry),
     problem_spec_collect recurse entries0 (implementation_collect recurse entries0) := by
   intro recurse entries0
   show implementation_collect recurse entries0 = collectTree recurse entries0
-  exact main_induction recurse entries0
-
+  first
+  | rfl
+  | (simp [implementation_collect, collectTree])
+  | decide
+  | native_decide
 -- proof-end
```

Attack 2 — `atk_2_nodescend.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,154 +65,19 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Whether a directory entry should be treated as a directory to descend into.
-A resolved directory counts as a directory whether or not the entry is itself a
-symbolic link. -/
-def entryIsDir : FSNode → Bool
-  | .file => false
-  | .dir _ _ => true
-
 def implementation_collect (recurse : DirEntry → Bool) :
     List DirEntry → List DirEntry
-  | xs => Id.run do
-    let entries := sortByName xs
-    let mut acc := entries
-    for h : e in entries do
-      if entryIsDir e.2 && recurse e then
-        match h2 : e.2 with
-        | .dir _ ch => acc := acc ++ implementation_collect recurse ch
-        | .file => pure ()
-    return acc
-termination_by xs => sizeOf xs
-decreasing_by
-  simp_wf
-  show sizeOf ch < sizeOf xs
-  have hmem : e ∈ xs :=
-    ((List.mergeSort_perm xs (fun a b => a.1 ≤ b.1)).mem_iff).mp h
-  have h1 : sizeOf e ≤ sizeOf xs := le_of_lt (List.sizeOf_lt_of_mem hmem)
-  have hh2 : sizeOf ch < sizeOf e.2 := by rw [h2]; simp
-  have h3 : sizeOf e.2 < sizeOf e := by cases e; simp
-  omega
+  | xs => sortByName xs
 -- impl-end
 
-
 -- proof-start
-/-- The plain functional value that the imperative body of `implementation_collect`
-evaluates to: the sorted level followed by the per-entry concatenation over
-`entries.attach`. -/
-def loopBody (recurse : DirEntry → Bool) (entries : List DirEntry) : List DirEntry :=
-  entries ++ entries.attach.flatMap (fun (p : {e // e ∈ entries}) =>
-    if entryIsDir p.1.2 && recurse p.1 then
-      match p.1.2 with
-      | .dir _ ch => implementation_collect recurse ch
-      | .file => []
-    else [])
-
-theorem foldl_append_flatMap {α β : Type*} (l : List α) (f : α → List β) (a : List β) :
-    l.foldl (fun acc x => acc ++ f x) a = a ++ l.flatMap f := by
-  induction l generalizing a with
-  | nil => simp
-  | cons x xs ih =>
-    simp only [List.foldl_cons, List.flatMap_cons, ih, List.append_assoc]
-
-theorem impl_unfold (recurse : DirEntry → Bool) (xs : List DirEntry) :
-    implementation_collect recurse xs =
-      (let entries := sortByName xs;
-       entries ++ entries.attach.flatMap (fun (p : {e // e ∈ entries}) =>
-         if entryIsDir p.1.2 && recurse p.1 then
-           match p.1.2 with
-           | .dir _ ch => implementation_collect recurse ch
-           | .file => []
-         else [])) := by
-  rw [← foldl_append_flatMap]
-  conv_lhs => rw [implementation_collect]
-  simp only [bind_pure_comp, map_pure, bind_pure, Id.run]
-  rw [show (fun (a : DirEntry) (m : a ∈ sortByName xs) (b : List DirEntry) =>
-        (if (entryIsDir a.2 && recurse a) = true then
-          match h : a.2 with
-          | .dir _ ch => pure (ForInStep.yield (b ++ implementation_collect recurse ch))
-          | .file => pure (ForInStep.yield b)
-        else pure (ForInStep.yield b) : Id (ForInStep (List DirEntry))))
-      = (fun (a : DirEntry) (m : a ∈ sortByName xs) (b : List DirEntry) =>
-        ForInStep.yield (b ++ (if (entryIsDir a.2 && recurse a) = true then
-          match a.2 with
-          | .dir _ ch => implementation_collect recurse ch
-          | .file => []
-        else []))) from by
-      funext a m b
-      obtain ⟨nm, nd⟩ := a
-      cases nd with
-      | file =>
-        simp only [entryIsDir, Bool.false_and, Bool.false_eq_true, if_false, List.append_nil]
-        rfl
-      | dir s ch =>
-        by_cases hr : recurse (nm, FSNode.dir s ch) = true
-        · simp only [entryIsDir, Bool.true_and, hr, if_true]
-          rfl
-        · have hr' : (recurse (nm, FSNode.dir s ch) = true) = False := by simp [hr]
-          simp only [entryIsDir, Bool.true_and, hr', if_false, List.append_nil]
-          rfl]
-  rw [List.forIn'_yield_eq_foldl]
-
-theorem entry_body_eq (recurse : DirEntry → Bool) (e : DirEntry)
-    (ih : ∀ (b : Bool) (ch : List DirEntry), e.2 = .dir b ch →
-      implementation_collect recurse ch = collectTree recurse ch) :
-    (if entryIsDir e.2 && recurse e then
-       (match e.2 with
-        | .dir _ ch => implementation_collect recurse ch
-        | .file => []) else []) =
-    (if recurse e then
-       (match e.2 with
-        | .dir _ ch => collectTree recurse ch
-        | .file => []) else []) := by
-  obtain ⟨name, node⟩ := e
-  cases node with
-  | file => simp [entryIsDir]
-  | dir b ch =>
-    simp only [entryIsDir, Bool.true_and]
-    rw [ih b ch rfl]
-
-theorem children_size_decreasing (entries0 : List DirEntry) (e : DirEntry)
-    (b : Bool) (ch : List DirEntry) (hmem : e ∈ sortByName entries0)
-    (hdir : e.2 = .dir b ch) : sizeOf ch < sizeOf entries0 := by
-  simp only [sortByName] at hmem
-  have hmem2 : e ∈ entries0 :=
-    ((List.mergeSort_perm entries0 (fun a b => a.1 ≤ b.1)).mem_iff).mp hmem
-  have h1 : sizeOf e ≤ sizeOf entries0 := le_of_lt (List.sizeOf_lt_of_mem hmem2)
-  have h2 : sizeOf ch < sizeOf e.2 := by rw [hdir]; simp
-  have h3 : sizeOf e.2 < sizeOf e := by cases e; simp
-  omega
-
-theorem main_induction (recurse : DirEntry → Bool) (entries0 : List DirEntry) :
-    implementation_collect recurse entries0 = collectTree recurse entries0 := by
-  have key : ∀ n, ∀ es : List DirEntry, sizeOf es < n →
-      implementation_collect recurse es = collectTree recurse es := by
-    intro n
-    induction n with
-    | zero => intro es h; omega
-    | succ n ih =>
-      intro es hlt
-      rw [impl_unfold]
-      conv_rhs => rw [collectTree]
-      simp only []
-      congr 1
-      apply List.flatMap_congr
-      intro p _
-      have ih' : ∀ (b : Bool) (ch : List DirEntry), p.1.2 = .dir b ch →
-          implementation_collect recurse ch = collectTree recurse ch := by
-        intro b ch hdir
-        have hmem : p.1 ∈ sortByName es := p.2
-        have hlt2 : sizeOf ch < sizeOf es :=
-          children_size_decreasing es p.1 b ch hmem hdir
-        exact ih ch (by omega)
-      rw [entry_body_eq recurse p.1 ih']
-      cases p.1.2 <;> rfl
-  exact key (sizeOf entries0 + 1) entries0 (by omega)
-
 theorem correct_collect : ∀ (recurse : DirEntry → Bool) (entries0 : List DirEntry),
     problem_spec_collect recurse entries0 (implementation_collect recurse entries0) := by
   intro recurse entries0
   show implementation_collect recurse entries0 = collectTree recurse entries0
-  exact main_induction recurse entries0
-
+  first
+  | rfl
+  | (simp [implementation_collect, collectTree])
+  | decide
+  | native_decide
 -- proof-end
```

Attack 3 — `atk_3_nosort.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,9 +65,6 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Whether a directory entry should be treated as a directory to descend into.
-A resolved directory counts as a directory whether or not the entry is itself a
-symbolic link. -/
 def entryIsDir : FSNode → Bool
   | .file => false
   | .dir _ _ => true
@@ -75,7 +72,7 @@
 def implementation_collect (recurse : DirEntry → Bool) :
     List DirEntry → List DirEntry
   | xs => Id.run do
-    let entries := sortByName xs
+    let entries := xs
     let mut acc := entries
     for h : e in entries do
       if entryIsDir e.2 && recurse e then
@@ -87,132 +84,21 @@
 decreasing_by
   simp_wf
   show sizeOf ch < sizeOf xs
-  have hmem : e ∈ xs :=
-    ((List.mergeSort_perm xs (fun a b => a.1 ≤ b.1)).mem_iff).mp h
+  have hmem : e ∈ xs := h
   have h1 : sizeOf e ≤ sizeOf xs := le_of_lt (List.sizeOf_lt_of_mem hmem)
   have hh2 : sizeOf ch < sizeOf e.2 := by rw [h2]; simp
   have h3 : sizeOf e.2 < sizeOf e := by cases e; simp
   omega
 -- impl-end
 
-
 -- proof-start
-/-- The plain functional value that the imperative body of `implementation_collect`
-evaluates to: the sorted level followed by the per-entry concatenation over
-`entries.attach`. -/
-def loopBody (recurse : DirEntry → Bool) (entries : List DirEntry) : List DirEntry :=
-  entries ++ entries.attach.flatMap (fun (p : {e // e ∈ entries}) =>
-    if entryIsDir p.1.2 && recurse p.1 then
-      match p.1.2 with
-      | .dir _ ch => implementation_collect recurse ch
-      | .file => []
-    else [])
-
-theorem foldl_append_flatMap {α β : Type*} (l : List α) (f : α → List β) (a : List β) :
-    l.foldl (fun acc x => acc ++ f x) a = a ++ l.flatMap f := by
-  induction l generalizing a with
-  | nil => simp
-  | cons x xs ih =>
-    simp only [List.foldl_cons, List.flatMap_cons, ih, List.append_assoc]
-
-theorem impl_unfold (recurse : DirEntry → Bool) (xs : List DirEntry) :
-    implementation_collect recurse xs =
-      (let entries := sortByName xs;
-       entries ++ entries.attach.flatMap (fun (p : {e // e ∈ entries}) =>
-         if entryIsDir p.1.2 && recurse p.1 then
-           match p.1.2 with
-           | .dir _ ch => implementation_collect recurse ch
-           | .file => []
-         else [])) := by
-  rw [← foldl_append_flatMap]
-  conv_lhs => rw [implementation_collect]
-  simp only [bind_pure_comp, map_pure, bind_pure, Id.run]
-  rw [show (fun (a : DirEntry) (m : a ∈ sortByName xs) (b : List DirEntry) =>
-        (if (entryIsDir a.2 && recurse a) = true then
-          match h : a.2 with
-          | .dir _ ch => pure (ForInStep.yield (b ++ implementation_collect recurse ch))
-          | .file => pure (ForInStep.yield b)
-        else pure (ForInStep.yield b) : Id (ForInStep (List DirEntry))))
-      = (fun (a : DirEntry) (m : a ∈ sortByName xs) (b : List DirEntry) =>
-        ForInStep.yield (b ++ (if (entryIsDir a.2 && recurse a) = true then
-          match a.2 with
-          | .dir _ ch => implementation_collect recurse ch
-          | .file => []
-        else []))) from by
-      funext a m b
-      obtain ⟨nm, nd⟩ := a
-      cases nd with
-      | file =>
-        simp only [entryIsDir, Bool.false_and, Bool.false_eq_true, if_false, List.append_nil]
-        rfl
-      | dir s ch =>
-        by_cases hr : recurse (nm, FSNode.dir s ch) = true
-        · simp only [entryIsDir, Bool.true_and, hr, if_true]
-          rfl
-        · have hr' : (recurse (nm, FSNode.dir s ch) = true) = False := by simp [hr]
-          simp only [entryIsDir, Bool.true_and, hr', if_false, List.append_nil]
-          rfl]
-  rw [List.forIn'_yield_eq_foldl]
-
-theorem entry_body_eq (recurse : DirEntry → Bool) (e : DirEntry)
-    (ih : ∀ (b : Bool) (ch : List DirEntry), e.2 = .dir b ch →
-      implementation_collect recurse ch = collectTree recurse ch) :
-    (if entryIsDir e.2 && recurse e then
-       (match e.2 with
-        | .dir _ ch => implementation_collect recurse ch
-        | .file => []) else []) =
-    (if recurse e then
-       (match e.2 with
-        | .dir _ ch => collectTree recurse ch
-        | .file => []) else []) := by
-  obtain ⟨name, node⟩ := e
-  cases node with
-  | file => simp [entryIsDir]
-  | dir b ch =>
-    simp only [entryIsDir, Bool.true_and]
-    rw [ih b ch rfl]
-
-theorem children_size_decreasing (entries0 : List DirEntry) (e : DirEntry)
-    (b : Bool) (ch : List DirEntry) (hmem : e ∈ sortByName entries0)
-    (hdir : e.2 = .dir b ch) : sizeOf ch < sizeOf entries0 := by
-  simp only [sortByName] at hmem
-  have hmem2 : e ∈ entries0 :=
-    ((List.mergeSort_perm entries0 (fun a b => a.1 ≤ b.1)).mem_iff).mp hmem
-  have h1 : sizeOf e ≤ sizeOf entries0 := le_of_lt (List.sizeOf_lt_of_mem hmem2)
-  have h2 : sizeOf ch < sizeOf e.2 := by rw [hdir]; simp
-  have h3 : sizeOf e.2 < sizeOf e := by cases e; simp
-  omega
-
-theorem main_induction (recurse : DirEntry → Bool) (entries0 : List DirEntry) :
-    implementation_collect recurse entries0 = collectTree recurse entries0 := by
-  have key : ∀ n, ∀ es : List DirEntry, sizeOf es < n →
-      implementation_collect recurse es = collectTree recurse es := by
-    intro n
-    induction n with
-    | zero => intro es h; omega
-    | succ n ih =>
-      intro es hlt
-      rw [impl_unfold]
-      conv_rhs => rw [collectTree]
-      simp only []
-      congr 1
-      apply List.flatMap_congr
-      intro p _
-      have ih' : ∀ (b : Bool) (ch : List DirEntry), p.1.2 = .dir b ch →
-          implementation_collect recurse ch = collectTree recurse ch := by
-        intro b ch hdir
-        have hmem : p.1 ∈ sortByName es := p.2
-        have hlt2 : sizeOf ch < sizeOf es :=
-          children_size_decreasing es p.1 b ch hmem hdir
-        exact ih ch (by omega)
-      rw [entry_body_eq recurse p.1 ih']
-      cases p.1.2 <;> rfl
-  exact key (sizeOf entries0 + 1) entries0 (by omega)
-
 theorem correct_collect : ∀ (recurse : DirEntry → Bool) (entries0 : List DirEntry),
     problem_spec_collect recurse entries0 (implementation_collect recurse entries0) := by
   intro recurse entries0
   show implementation_collect recurse entries0 = collectTree recurse entries0
-  exact main_induction recurse entries0
-
+  first
+  | rfl
+  | (simp [implementation_collect, collectTree])
+  | decide
+  | native_decide
 -- proof-end
```

Attack 4 — `atk_4_ignorerecurse.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,9 +65,6 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Whether a directory entry should be treated as a directory to descend into.
-A resolved directory counts as a directory whether or not the entry is itself a
-symbolic link. -/
 def entryIsDir : FSNode → Bool
   | .file => false
   | .dir _ _ => true
@@ -78,7 +75,7 @@
     let entries := sortByName xs
     let mut acc := entries
     for h : e in entries do
-      if entryIsDir e.2 && recurse e then
+      if entryIsDir e.2 then
         match h2 : e.2 with
         | .dir _ ch => acc := acc ++ implementation_collect recurse ch
         | .file => pure ()
@@ -95,124 +92,14 @@
   omega
 -- impl-end
 
-
 -- proof-start
-/-- The plain functional value that the imperative body of `implementation_collect`
-evaluates to: the sorted level followed by the per-entry concatenation over
-`entries.attach`. -/
-def loopBody (recurse : DirEntry → Bool) (entries : List DirEntry) : List DirEntry :=
-  entries ++ entries.attach.flatMap (fun (p : {e // e ∈ entries}) =>
-    if entryIsDir p.1.2 && recurse p.1 then
-      match p.1.2 with
-      | .dir _ ch => implementation_collect recurse ch
-      | .file => []
-    else [])
-
-theorem foldl_append_flatMap {α β : Type*} (l : List α) (f : α → List β) (a : List β) :
-    l.foldl (fun acc x => acc ++ f x) a = a ++ l.flatMap f := by
-  induction l generalizing a with
-  | nil => simp
-  | cons x xs ih =>
-    simp only [List.foldl_cons, List.flatMap_cons, ih, List.append_assoc]
-
-theorem impl_unfold (recurse : DirEntry → Bool) (xs : List DirEntry) :
-    implementation_collect recurse xs =
-      (let entries := sortByName xs;
-       entries ++ entries.attach.flatMap (fun (p : {e // e ∈ entries}) =>
-         if entryIsDir p.1.2 && recurse p.1 then
-           match p.1.2 with
-           | .dir _ ch => implementation_collect recurse ch
-           | .file => []
-         else [])) := by
-  rw [← foldl_append_flatMap]
-  conv_lhs => rw [implementation_collect]
-  simp only [bind_pure_comp, map_pure, bind_pure, Id.run]
-  rw [show (fun (a : DirEntry) (m : a ∈ sortByName xs) (b : List DirEntry) =>
-        (if (entryIsDir a.2 && recurse a) = true then
-          match h : a.2 with
-          | .dir _ ch => pure (ForInStep.yield (b ++ implementation_collect recurse ch))
-          | .file => pure (ForInStep.yield b)
-        else pure (ForInStep.yield b) : Id (ForInStep (List DirEntry))))
-      = (fun (a : DirEntry) (m : a ∈ sortByName xs) (b : List DirEntry) =>
-        ForInStep.yield (b ++ (if (entryIsDir a.2 && recurse a) = true then
-          match a.2 with
-          | .dir _ ch => implementation_collect recurse ch
-          | .file => []
-        else []))) from by
-      funext a m b
-      obtain ⟨nm, nd⟩ := a
-      cases nd with
-      | file =>
-        simp only [entryIsDir, Bool.false_and, Bool.false_eq_true, if_false, List.append_nil]
-        rfl
-      | dir s ch =>
-        by_cases hr : recurse (nm, FSNode.dir s ch) = true
-        · simp only [entryIsDir, Bool.true_and, hr, if_true]
-          rfl
-        · have hr' : (recurse (nm, FSNode.dir s ch) = true) = False := by simp [hr]
-          simp only [entryIsDir, Bool.true_and, hr', if_false, List.append_nil]
-          rfl]
-  rw [List.forIn'_yield_eq_foldl]
-
-theorem entry_body_eq (recurse : DirEntry → Bool) (e : DirEntry)
-    (ih : ∀ (b : Bool) (ch : List DirEntry), e.2 = .dir b ch →
-      implementation_collect recurse ch = collectTree recurse ch) :
-    (if entryIsDir e.2 && recurse e then
-       (match e.2 with
-        | .dir _ ch => implementation_collect recurse ch
-        | .file => []) else []) =
-    (if recurse e then
-       (match e.2 with
-        | .dir _ ch => collectTree recurse ch
-        | .file => []) else []) := by
-  obtain ⟨name, node⟩ := e
-  cases node with
-  | file => simp [entryIsDir]
-  | dir b ch =>
-    simp only [entryIsDir, Bool.true_and]
-    rw [ih b ch rfl]
-
-theorem children_size_decreasing (entries0 : List DirEntry) (e : DirEntry)
-    (b : Bool) (ch : List DirEntry) (hmem : e ∈ sortByName entries0)
-    (hdir : e.2 = .dir b ch) : sizeOf ch < sizeOf entries0 := by
-  simp only [sortByName] at hmem
-  have hmem2 : e ∈ entries0 :=
-    ((List.mergeSort_perm entries0 (fun a b => a.1 ≤ b.1)).mem_iff).mp hmem
-  have h1 : sizeOf e ≤ sizeOf entries0 := le_of_lt (List.sizeOf_lt_of_mem hmem2)
-  have h2 : sizeOf ch < sizeOf e.2 := by rw [hdir]; simp
-  have h3 : sizeOf e.2 < sizeOf e := by cases e; simp
-  omega
-
-theorem main_induction (recurse : DirEntry → Bool) (entries0 : List DirEntry) :
-    implementation_collect recurse entries0 = collectTree recurse entries0 := by
-  have key : ∀ n, ∀ es : List DirEntry, sizeOf es < n →
-      implementation_collect recurse es = collectTree recurse es := by
-    intro n
-    induction n with
-    | zero => intro es h; omega
-    | succ n ih =>
-      intro es hlt
-      rw [impl_unfold]
-      conv_rhs => rw [collectTree]
-      simp only []
-      congr 1
-      apply List.flatMap_congr
-      intro p _
-      have ih' : ∀ (b : Bool) (ch : List DirEntry), p.1.2 = .dir b ch →
-          implementation_collect recurse ch = collectTree recurse ch := by
-        intro b ch hdir
-        have hmem : p.1 ∈ sortByName es := p.2
-        have hlt2 : sizeOf ch < sizeOf es :=
-          children_size_decreasing es p.1 b ch hmem hdir
-        exact ih ch (by omega)
-      rw [entry_body_eq recurse p.1 ih']
-      cases p.1.2 <;> rfl
-  exact key (sizeOf entries0 + 1) entries0 (by omega)
-
 theorem correct_collect : ∀ (recurse : DirEntry → Bool) (entries0 : List DirEntry),
     problem_spec_collect recurse entries0 (implementation_collect recurse entries0) := by
   intro recurse entries0
   show implementation_collect recurse entries0 = collectTree recurse entries0
-  exact main_induction recurse entries0
-
+  first
+  | rfl
+  | (simp [implementation_collect, collectTree])
+  | decide
+  | native_decide
 -- proof-end
```

Attack 5 — `atk_5_wrongorder.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,9 +65,6 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Whether a directory entry should be treated as a directory to descend into.
-A resolved directory counts as a directory whether or not the entry is itself a
-symbolic link. -/
 def entryIsDir : FSNode → Bool
   | .file => false
   | .dir _ _ => true
@@ -76,13 +73,13 @@
     List DirEntry → List DirEntry
   | xs => Id.run do
     let entries := sortByName xs
-    let mut acc := entries
+    let mut acc := []
     for h : e in entries do
       if entryIsDir e.2 && recurse e then
         match h2 : e.2 with
         | .dir _ ch => acc := acc ++ implementation_collect recurse ch
         | .file => pure ()
-    return acc
+    return acc ++ entries
 termination_by xs => sizeOf xs
 decreasing_by
   simp_wf
@@ -95,124 +92,14 @@
   omega
 -- impl-end
 
-
 -- proof-start
-/-- The plain functional value that the imperative body of `implementation_collect`
-evaluates to: the sorted level followed by the per-entry concatenation over
-`entries.attach`. -/
-def loopBody (recurse : DirEntry → Bool) (entries : List DirEntry) : List DirEntry :=
-  entries ++ entries.attach.flatMap (fun (p : {e // e ∈ entries}) =>
-    if entryIsDir p.1.2 && recurse p.1 then
-      match p.1.2 with
-      | .dir _ ch => implementation_collect recurse ch
-      | .file => []
-    else [])
-
-theorem foldl_append_flatMap {α β : Type*} (l : List α) (f : α → List β) (a : List β) :
-    l.foldl (fun acc x => acc ++ f x) a = a ++ l.flatMap f := by
-  induction l generalizing a with
-  | nil => simp
-  | cons x xs ih =>
-    simp only [List.foldl_cons, List.flatMap_cons, ih, List.append_assoc]
-
-theorem impl_unfold (recurse : DirEntry → Bool) (xs : List DirEntry) :
-    implementation_collect recurse xs =
-      (let entries := sortByName xs;
-       entries ++ entries.attach.flatMap (fun (p : {e // e ∈ entries}) =>
-         if entryIsDir p.1.2 && recurse p.1 then
-           match p.1.2 with
-           | .dir _ ch => implementation_collect recurse ch
-           | .file => []
-         else [])) := by
-  rw [← foldl_append_flatMap]
-  conv_lhs => rw [implementation_collect]
-  simp only [bind_pure_comp, map_pure, bind_pure, Id.run]
-  rw [show (fun (a : DirEntry) (m : a ∈ sortByName xs) (b : List DirEntry) =>
-        (if (entryIsDir a.2 && recurse a) = true then
-          match h : a.2 with
-          | .dir _ ch => pure (ForInStep.yield (b ++ implementation_collect recurse ch))
-          | .file => pure (ForInStep.yield b)
-        else pure (ForInStep.yield b) : Id (ForInStep (List DirEntry))))
-      = (fun (a : DirEntry) (m : a ∈ sortByName xs) (b : List DirEntry) =>
-        ForInStep.yield (b ++ (if (entryIsDir a.2 && recurse a) = true then
-          match a.2 with
-          | .dir _ ch => implementation_collect recurse ch
-          | .file => []
-        else []))) from by
-      funext a m b
-      obtain ⟨nm, nd⟩ := a
-      cases nd with
-      | file =>
-        simp only [entryIsDir, Bool.false_and, Bool.false_eq_true, if_false, List.append_nil]
-        rfl
-      | dir s ch =>
-        by_cases hr : recurse (nm, FSNode.dir s ch) = true
-        · simp only [entryIsDir, Bool.true_and, hr, if_true]
-          rfl
-        · have hr' : (recurse (nm, FSNode.dir s ch) = true) = False := by simp [hr]
-          simp only [entryIsDir, Bool.true_and, hr', if_false, List.append_nil]
-          rfl]
-  rw [List.forIn'_yield_eq_foldl]
-
-theorem entry_body_eq (recurse : DirEntry → Bool) (e : DirEntry)
-    (ih : ∀ (b : Bool) (ch : List DirEntry), e.2 = .dir b ch →
-      implementation_collect recurse ch = collectTree recurse ch) :
-    (if entryIsDir e.2 && recurse e then
-       (match e.2 with
-        | .dir _ ch => implementation_collect recurse ch
-        | .file => []) else []) =
-    (if recurse e then
-       (match e.2 with
-        | .dir _ ch => collectTree recurse ch
-        | .file => []) else []) := by
-  obtain ⟨name, node⟩ := e
-  cases node with
-  | file => simp [entryIsDir]
-  | dir b ch =>
-    simp only [entryIsDir, Bool.true_and]
-    rw [ih b ch rfl]
-
-theorem children_size_decreasing (entries0 : List DirEntry) (e : DirEntry)
-    (b : Bool) (ch : List DirEntry) (hmem : e ∈ sortByName entries0)
-    (hdir : e.2 = .dir b ch) : sizeOf ch < sizeOf entries0 := by
-  simp only [sortByName] at hmem
-  have hmem2 : e ∈ entries0 :=
-    ((List.mergeSort_perm entries0 (fun a b => a.1 ≤ b.1)).mem_iff).mp hmem
-  have h1 : sizeOf e ≤ sizeOf entries0 := le_of_lt (List.sizeOf_lt_of_mem hmem2)
-  have h2 : sizeOf ch < sizeOf e.2 := by rw [hdir]; simp
-  have h3 : sizeOf e.2 < sizeOf e := by cases e; simp
-  omega
-
-theorem main_induction (recurse : DirEntry → Bool) (entries0 : List DirEntry) :
-    implementation_collect recurse entries0 = collectTree recurse entries0 := by
-  have key : ∀ n, ∀ es : List DirEntry, sizeOf es < n →
-      implementation_collect recurse es = collectTree recurse es := by
-    intro n
-    induction n with
-    | zero => intro es h; omega
-    | succ n ih =>
-      intro es hlt
-      rw [impl_unfold]
-      conv_rhs => rw [collectTree]
-      simp only []
-      congr 1
-      apply List.flatMap_congr
-      intro p _
-      have ih' : ∀ (b : Bool) (ch : List DirEntry), p.1.2 = .dir b ch →
-          implementation_collect recurse ch = collectTree recurse ch := by
-        intro b ch hdir
-        have hmem : p.1 ∈ sortByName es := p.2
-        have hlt2 : sizeOf ch < sizeOf es :=
-          children_size_decreasing es p.1 b ch hmem hdir
-        exact ih ch (by omega)
-      rw [entry_body_eq recurse p.1 ih']
-      cases p.1.2 <;> rfl
-  exact key (sizeOf entries0 + 1) entries0 (by omega)
-
 theorem correct_collect : ∀ (recurse : DirEntry → Bool) (entries0 : List DirEntry),
     problem_spec_collect recurse entries0 (implementation_collect recurse entries0) := by
   intro recurse entries0
   show implementation_collect recurse entries0 = collectTree recurse entries0
-  exact main_induction recurse entries0
-
+  first
+  | rfl
+  | (simp [implementation_collect, collectTree])
+  | decide
+  | native_decide
 -- proof-end
```

Attack 6 — `atk_6_negrecurse.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,9 +65,6 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Whether a directory entry should be treated as a directory to descend into.
-A resolved directory counts as a directory whether or not the entry is itself a
-symbolic link. -/
 def entryIsDir : FSNode → Bool
   | .file => false
   | .dir _ _ => true
@@ -78,7 +75,7 @@
     let entries := sortByName xs
     let mut acc := entries
     for h : e in entries do
-      if entryIsDir e.2 && recurse e then
+      if entryIsDir e.2 && !recurse e then
         match h2 : e.2 with
         | .dir _ ch => acc := acc ++ implementation_collect recurse ch
         | .file => pure ()
@@ -95,124 +92,14 @@
   omega
 -- impl-end
 
-
 -- proof-start
-/-- The plain functional value that the imperative body of `implementation_collect`
-evaluates to: the sorted level followed by the per-entry concatenation over
-`entries.attach`. -/
-def loopBody (recurse : DirEntry → Bool) (entries : List DirEntry) : List DirEntry :=
-  entries ++ entries.attach.flatMap (fun (p : {e // e ∈ entries}) =>
-    if entryIsDir p.1.2 && recurse p.1 then
-      match p.1.2 with
-      | .dir _ ch => implementation_collect recurse ch
-      | .file => []
-    else [])
-
-theorem foldl_append_flatMap {α β : Type*} (l : List α) (f : α → List β) (a : List β) :
-    l.foldl (fun acc x => acc ++ f x) a = a ++ l.flatMap f := by
-  induction l generalizing a with
-  | nil => simp
-  | cons x xs ih =>
-    simp only [List.foldl_cons, List.flatMap_cons, ih, List.append_assoc]
-
-theorem impl_unfold (recurse : DirEntry → Bool) (xs : List DirEntry) :
-    implementation_collect recurse xs =
-      (let entries := sortByName xs;
-       entries ++ entries.attach.flatMap (fun (p : {e // e ∈ entries}) =>
-         if entryIsDir p.1.2 && recurse p.1 then
-           match p.1.2 with
-           | .dir _ ch => implementation_collect recurse ch
-           | .file => []
-         else [])) := by
-  rw [← foldl_append_flatMap]
-  conv_lhs => rw [implementation_collect]
-  simp only [bind_pure_comp, map_pure, bind_pure, Id.run]
-  rw [show (fun (a : DirEntry) (m : a ∈ sortByName xs) (b : List DirEntry) =>
-        (if (entryIsDir a.2 && recurse a) = true then
-          match h : a.2 with
-          | .dir _ ch => pure (ForInStep.yield (b ++ implementation_collect recurse ch))
-          | .file => pure (ForInStep.yield b)
-        else pure (ForInStep.yield b) : Id (ForInStep (List DirEntry))))
-      = (fun (a : DirEntry) (m : a ∈ sortByName xs) (b : List DirEntry) =>
-        ForInStep.yield (b ++ (if (entryIsDir a.2 && recurse a) = true then
-          match a.2 with
-          | .dir _ ch => implementation_collect recurse ch
-          | .file => []
-        else []))) from by
-      funext a m b
-      obtain ⟨nm, nd⟩ := a
-      cases nd with
-      | file =>
-        simp only [entryIsDir, Bool.false_and, Bool.false_eq_true, if_false, List.append_nil]
-        rfl
-      | dir s ch =>
-        by_cases hr : recurse (nm, FSNode.dir s ch) = true
-        · simp only [entryIsDir, Bool.true_and, hr, if_true]
-          rfl
-        · have hr' : (recurse (nm, FSNode.dir s ch) = true) = False := by simp [hr]
-          simp only [entryIsDir, Bool.true_and, hr', if_false, List.append_nil]
-          rfl]
-  rw [List.forIn'_yield_eq_foldl]
-
-theorem entry_body_eq (recurse : DirEntry → Bool) (e : DirEntry)
-    (ih : ∀ (b : Bool) (ch : List DirEntry), e.2 = .dir b ch →
-      implementation_collect recurse ch = collectTree recurse ch) :
-    (if entryIsDir e.2 && recurse e then
-       (match e.2 with
-        | .dir _ ch => implementation_collect recurse ch
-        | .file => []) else []) =
-    (if recurse e then
-       (match e.2 with
-        | .dir _ ch => collectTree recurse ch
-        | .file => []) else []) := by
-  obtain ⟨name, node⟩ := e
-  cases node with
-  | file => simp [entryIsDir]
-  | dir b ch =>
-    simp only [entryIsDir, Bool.true_and]
-    rw [ih b ch rfl]
-
-theorem children_size_decreasing (entries0 : List DirEntry) (e : DirEntry)
-    (b : Bool) (ch : List DirEntry) (hmem : e ∈ sortByName entries0)
-    (hdir : e.2 = .dir b ch) : sizeOf ch < sizeOf entries0 := by
-  simp only [sortByName] at hmem
-  have hmem2 : e ∈ entries0 :=
-    ((List.mergeSort_perm entries0 (fun a b => a.1 ≤ b.1)).mem_iff).mp hmem
-  have h1 : sizeOf e ≤ sizeOf entries0 := le_of_lt (List.sizeOf_lt_of_mem hmem2)
-  have h2 : sizeOf ch < sizeOf e.2 := by rw [hdir]; simp
-  have h3 : sizeOf e.2 < sizeOf e := by cases e; simp
-  omega
-
-theorem main_induction (recurse : DirEntry → Bool) (entries0 : List DirEntry) :
-    implementation_collect recurse entries0 = collectTree recurse entries0 := by
-  have key : ∀ n, ∀ es : List DirEntry, sizeOf es < n →
-      implementation_collect recurse es = collectTree recurse es := by
-    intro n
-    induction n with
-    | zero => intro es h; omega
-    | succ n ih =>
-      intro es hlt
-      rw [impl_unfold]
-      conv_rhs => rw [collectTree]
-      simp only []
-      congr 1
-      apply List.flatMap_congr
-      intro p _
-      have ih' : ∀ (b : Bool) (ch : List DirEntry), p.1.2 = .dir b ch →
-          implementation_collect recurse ch = collectTree recurse ch := by
-        intro b ch hdir
-        have hmem : p.1 ∈ sortByName es := p.2
-        have hlt2 : sizeOf ch < sizeOf es :=
-          children_size_decreasing es p.1 b ch hmem hdir
-        exact ih ch (by omega)
-      rw [entry_body_eq recurse p.1 ih']
-      cases p.1.2 <;> rfl
-  exact key (sizeOf entries0 + 1) entries0 (by omega)
-
 theorem correct_collect : ∀ (recurse : DirEntry → Bool) (entries0 : List DirEntry),
     problem_spec_collect recurse entries0 (implementation_collect recurse entries0) := by
   intro recurse entries0
   show implementation_collect recurse entries0 = collectTree recurse entries0
-  exact main_induction recurse entries0
-
+  first
+  | rfl
+  | (simp [implementation_collect, collectTree])
+  | decide
+  | native_decide
 -- proof-end
```

Attack 7 — `atk_7_empty.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,154 +65,19 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Whether a directory entry should be treated as a directory to descend into.
-A resolved directory counts as a directory whether or not the entry is itself a
-symbolic link. -/
-def entryIsDir : FSNode → Bool
-  | .file => false
-  | .dir _ _ => true
-
 def implementation_collect (recurse : DirEntry → Bool) :
     List DirEntry → List DirEntry
-  | xs => Id.run do
-    let entries := sortByName xs
-    let mut acc := entries
-    for h : e in entries do
-      if entryIsDir e.2 && recurse e then
-        match h2 : e.2 with
-        | .dir _ ch => acc := acc ++ implementation_collect recurse ch
-        | .file => pure ()
-    return acc
-termination_by xs => sizeOf xs
-decreasing_by
-  simp_wf
-  show sizeOf ch < sizeOf xs
-  have hmem : e ∈ xs :=
-    ((List.mergeSort_perm xs (fun a b => a.1 ≤ b.1)).mem_iff).mp h
-  have h1 : sizeOf e ≤ sizeOf xs := le_of_lt (List.sizeOf_lt_of_mem hmem)
-  have hh2 : sizeOf ch < sizeOf e.2 := by rw [h2]; simp
-  have h3 : sizeOf e.2 < sizeOf e := by cases e; simp
-  omega
+  | _ => []
 -- impl-end
 
-
 -- proof-start
-/-- The plain functional value that the imperative body of `implementation_collect`
-evaluates to: the sorted level followed by the per-entry concatenation over
-`entries.attach`. -/
-def loopBody (recurse : DirEntry → Bool) (entries : List DirEntry) : List DirEntry :=
-  entries ++ entries.attach.flatMap (fun (p : {e // e ∈ entries}) =>
-    if entryIsDir p.1.2 && recurse p.1 then
-      match p.1.2 with
-      | .dir _ ch => implementation_collect recurse ch
-      | .file => []
-    else [])
-
-theorem foldl_append_flatMap {α β : Type*} (l : List α) (f : α → List β) (a : List β) :
-    l.foldl (fun acc x => acc ++ f x) a = a ++ l.flatMap f := by
-  induction l generalizing a with
-  | nil => simp
-  | cons x xs ih =>
-    simp only [List.foldl_cons, List.flatMap_cons, ih, List.append_assoc]
-
-theorem impl_unfold (recurse : DirEntry → Bool) (xs : List DirEntry) :
-    implementation_collect recurse xs =
-      (let entries := sortByName xs;
-       entries ++ entries.attach.flatMap (fun (p : {e // e ∈ entries}) =>
-         if entryIsDir p.1.2 && recurse p.1 then
-           match p.1.2 with
-           | .dir _ ch => implementation_collect recurse ch
-           | .file => []
-         else [])) := by
-  rw [← foldl_append_flatMap]
-  conv_lhs => rw [implementation_collect]
-  simp only [bind_pure_comp, map_pure, bind_pure, Id.run]
-  rw [show (fun (a : DirEntry) (m : a ∈ sortByName xs) (b : List DirEntry) =>
-        (if (entryIsDir a.2 && recurse a) = true then
-          match h : a.2 with
-          | .dir _ ch => pure (ForInStep.yield (b ++ implementation_collect recurse ch))
-          | .file => pure (ForInStep.yield b)
-        else pure (ForInStep.yield b) : Id (ForInStep (List DirEntry))))
-      = (fun (a : DirEntry) (m : a ∈ sortByName xs) (b : List DirEntry) =>
-        ForInStep.yield (b ++ (if (entryIsDir a.2 && recurse a) = true then
-          match a.2 with
-          | .dir _ ch => implementation_collect recurse ch
-          | .file => []
-        else []))) from by
-      funext a m b
-      obtain ⟨nm, nd⟩ := a
-      cases nd with
-      | file =>
-        simp only [entryIsDir, Bool.false_and, Bool.false_eq_true, if_false, List.append_nil]
-        rfl
-      | dir s ch =>
-        by_cases hr : recurse (nm, FSNode.dir s ch) = true
-        · simp only [entryIsDir, Bool.true_and, hr, if_true]
-          rfl
-        · have hr' : (recurse (nm, FSNode.dir s ch) = true) = False := by simp [hr]
-          simp only [entryIsDir, Bool.true_and, hr', if_false, List.append_nil]
-          rfl]
-  rw [List.forIn'_yield_eq_foldl]
-
-theorem entry_body_eq (recurse : DirEntry → Bool) (e : DirEntry)
-    (ih : ∀ (b : Bool) (ch : List DirEntry), e.2 = .dir b ch →
-      implementation_collect recurse ch = collectTree recurse ch) :
-    (if entryIsDir e.2 && recurse e then
-       (match e.2 with
-        | .dir _ ch => implementation_collect recurse ch
-        | .file => []) else []) =
-    (if recurse e then
-       (match e.2 with
-        | .dir _ ch => collectTree recurse ch
-        | .file => []) else []) := by
-  obtain ⟨name, node⟩ := e
-  cases node with
-  | file => simp [entryIsDir]
-  | dir b ch =>
-    simp only [entryIsDir, Bool.true_and]
-    rw [ih b ch rfl]
-
-theorem children_size_decreasing (entries0 : List DirEntry) (e : DirEntry)
-    (b : Bool) (ch : List DirEntry) (hmem : e ∈ sortByName entries0)
-    (hdir : e.2 = .dir b ch) : sizeOf ch < sizeOf entries0 := by
-  simp only [sortByName] at hmem
-  have hmem2 : e ∈ entries0 :=
-    ((List.mergeSort_perm entries0 (fun a b => a.1 ≤ b.1)).mem_iff).mp hmem
-  have h1 : sizeOf e ≤ sizeOf entries0 := le_of_lt (List.sizeOf_lt_of_mem hmem2)
-  have h2 : sizeOf ch < sizeOf e.2 := by rw [hdir]; simp
-  have h3 : sizeOf e.2 < sizeOf e := by cases e; simp
-  omega
-
-theorem main_induction (recurse : DirEntry → Bool) (entries0 : List DirEntry) :
-    implementation_collect recurse entries0 = collectTree recurse entries0 := by
-  have key : ∀ n, ∀ es : List DirEntry, sizeOf es < n →
-      implementation_collect recurse es = collectTree recurse es := by
-    intro n
-    induction n with
-    | zero => intro es h; omega
-    | succ n ih =>
-      intro es hlt
-      rw [impl_unfold]
-      conv_rhs => rw [collectTree]
-      simp only []
-      congr 1
-      apply List.flatMap_congr
-      intro p _
-      have ih' : ∀ (b : Bool) (ch : List DirEntry), p.1.2 = .dir b ch →
-          implementation_collect recurse ch = collectTree recurse ch := by
-        intro b ch hdir
-        have hmem : p.1 ∈ sortByName es := p.2
-        have hlt2 : sizeOf ch < sizeOf es :=
-          children_size_decreasing es p.1 b ch hmem hdir
-        exact ih ch (by omega)
-      rw [entry_body_eq recurse p.1 ih']
-      cases p.1.2 <;> rfl
-  exact key (sizeOf entries0 + 1) entries0 (by omega)
-
 theorem correct_collect : ∀ (recurse : DirEntry → Bool) (entries0 : List DirEntry),
     problem_spec_collect recurse entries0 (implementation_collect recurse entries0) := by
   intro recurse entries0
   show implementation_collect recurse entries0 = collectTree recurse entries0
-  exact main_induction recurse entries0
-
+  first
+  | rfl
+  | (simp [implementation_collect, collectTree])
+  | decide
+  | native_decide
 -- proof-end
```

Attack 8 — `atk_8_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -65,154 +65,14 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Whether a directory entry should be treated as a directory to descend into.
-A resolved directory counts as a directory whether or not the entry is itself a
-symbolic link. -/
-def entryIsDir : FSNode → Bool
-  | .file => false
-  | .dir _ _ => true
-
 def implementation_collect (recurse : DirEntry → Bool) :
     List DirEntry → List DirEntry
-  | xs => Id.run do
-    let entries := sortByName xs
-    let mut acc := entries
-    for h : e in entries do
-      if entryIsDir e.2 && recurse e then
-        match h2 : e.2 with
-        | .dir _ ch => acc := acc ++ implementation_collect recurse ch
-        | .file => pure ()
-    return acc
-termination_by xs => sizeOf xs
-decreasing_by
-  simp_wf
-  show sizeOf ch < sizeOf xs
-  have hmem : e ∈ xs :=
-    ((List.mergeSort_perm xs (fun a b => a.1 ≤ b.1)).mem_iff).mp h
-  have h1 : sizeOf e ≤ sizeOf xs := le_of_lt (List.sizeOf_lt_of_mem hmem)
-  have hh2 : sizeOf ch < sizeOf e.2 := by rw [h2]; simp
-  have h3 : sizeOf e.2 < sizeOf e := by cases e; simp
-  omega
+  | xs => collectTree recurse xs
 -- impl-end
 
-
 -- proof-start
-/-- The plain functional value that the imperative body of `implementation_collect`
-evaluates to: the sorted level followed by the per-entry concatenation over
-`entries.attach`. -/
-def loopBody (recurse : DirEntry → Bool) (entries : List DirEntry) : List DirEntry :=
-  entries ++ entries.attach.flatMap (fun (p : {e // e ∈ entries}) =>
-    if entryIsDir p.1.2 && recurse p.1 then
-      match p.1.2 with
-      | .dir _ ch => implementation_collect recurse ch
-      | .file => []
-    else [])
-
-theorem foldl_append_flatMap {α β : Type*} (l : List α) (f : α → List β) (a : List β) :
-    l.foldl (fun acc x => acc ++ f x) a = a ++ l.flatMap f := by
-  induction l generalizing a with
-  | nil => simp
-  | cons x xs ih =>
-    simp only [List.foldl_cons, List.flatMap_cons, ih, List.append_assoc]
-
-theorem impl_unfold (recurse : DirEntry → Bool) (xs : List DirEntry) :
-    implementation_collect recurse xs =
-      (let entries := sortByName xs;
-       entries ++ entries.attach.flatMap (fun (p : {e // e ∈ entries}) =>
-         if entryIsDir p.1.2 && recurse p.1 then
-           match p.1.2 with
-           | .dir _ ch => implementation_collect recurse ch
-           | .file => []
-         else [])) := by
-  rw [← foldl_append_flatMap]
-  conv_lhs => rw [implementation_collect]
-  simp only [bind_pure_comp, map_pure, bind_pure, Id.run]
-  rw [show (fun (a : DirEntry) (m : a ∈ sortByName xs) (b : List DirEntry) =>
-        (if (entryIsDir a.2 && recurse a) = true then
-          match h : a.2 with
-          | .dir _ ch => pure (ForInStep.yield (b ++ implementation_collect recurse ch))
-          | .file => pure (ForInStep.yield b)
-        else pure (ForInStep.yield b) : Id (ForInStep (List DirEntry))))
-      = (fun (a : DirEntry) (m : a ∈ sortByName xs) (b : List DirEntry) =>
-        ForInStep.yield (b ++ (if (entryIsDir a.2 && recurse a) = true then
-          match a.2 with
-          | .dir _ ch => implementation_collect recurse ch
-          | .file => []
-        else []))) from by
-      funext a m b
-      obtain ⟨nm, nd⟩ := a
-      cases nd with
-      | file =>
-        simp only [entryIsDir, Bool.false_and, Bool.false_eq_true, if_false, List.append_nil]
-        rfl
-      | dir s ch =>
-        by_cases hr : recurse (nm, FSNode.dir s ch) = true
-        · simp only [entryIsDir, Bool.true_and, hr, if_true]
-          rfl
-        · have hr' : (recurse (nm, FSNode.dir s ch) = true) = False := by simp [hr]
-          simp only [entryIsDir, Bool.true_and, hr', if_false, List.append_nil]
-          rfl]
-  rw [List.forIn'_yield_eq_foldl]
-
-theorem entry_body_eq (recurse : DirEntry → Bool) (e : DirEntry)
-    (ih : ∀ (b : Bool) (ch : List DirEntry), e.2 = .dir b ch →
-      implementation_collect recurse ch = collectTree recurse ch) :
-    (if entryIsDir e.2 && recurse e then
-       (match e.2 with
-        | .dir _ ch => implementation_collect recurse ch
-        | .file => []) else []) =
-    (if recurse e then
-       (match e.2 with
-        | .dir _ ch => collectTree recurse ch
-        | .file => []) else []) := by
-  obtain ⟨name, node⟩ := e
-  cases node with
-  | file => simp [entryIsDir]
-  | dir b ch =>
-    simp only [entryIsDir, Bool.true_and]
-    rw [ih b ch rfl]
-
-theorem children_size_decreasing (entries0 : List DirEntry) (e : DirEntry)
-    (b : Bool) (ch : List DirEntry) (hmem : e ∈ sortByName entries0)
-    (hdir : e.2 = .dir b ch) : sizeOf ch < sizeOf entries0 := by
-  simp only [sortByName] at hmem
-  have hmem2 : e ∈ entries0 :=
-    ((List.mergeSort_perm entries0 (fun a b => a.1 ≤ b.1)).mem_iff).mp hmem
-  have h1 : sizeOf e ≤ sizeOf entries0 := le_of_lt (List.sizeOf_lt_of_mem hmem2)
-  have h2 : sizeOf ch < sizeOf e.2 := by rw [hdir]; simp
-  have h3 : sizeOf e.2 < sizeOf e := by cases e; simp
-  omega
-
-theorem main_induction (recurse : DirEntry → Bool) (entries0 : List DirEntry) :
-    implementation_collect recurse entries0 = collectTree recurse entries0 := by
-  have key : ∀ n, ∀ es : List DirEntry, sizeOf es < n →
-      implementation_collect recurse es = collectTree recurse es := by
-    intro n
-    induction n with
-    | zero => intro es h; omega
-    | succ n ih =>
-      intro es hlt
-      rw [impl_unfold]
-      conv_rhs => rw [collectTree]
-      simp only []
-      congr 1
-      apply List.flatMap_congr
-      intro p _
-      have ih' : ∀ (b : Bool) (ch : List DirEntry), p.1.2 = .dir b ch →
-          implementation_collect recurse ch = collectTree recurse ch := by
-        intro b ch hdir
-        have hmem : p.1 ∈ sortByName es := p.2
-        have hlt2 : sizeOf ch < sizeOf es :=
-          children_size_decreasing es p.1 b ch hmem hdir
-        exact ih ch (by omega)
-      rw [entry_body_eq recurse p.1 ih']
-      cases p.1.2 <;> rfl
-  exact key (sizeOf entries0 + 1) entries0 (by omega)
-
 theorem correct_collect : ∀ (recurse : DirEntry → Bool) (entries0 : List DirEntry),
     problem_spec_collect recurse entries0 (implementation_collect recurse entries0) := by
   intro recurse entries0
-  show implementation_collect recurse entries0 = collectTree recurse entries0
-  exact main_induction recurse entries0
-
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is consumed as an axiom. The directory-tree walk is
-- modeled deeply below (`collectTree`), and the per-level ordering operation is
-- modeled deeply as a name-keyed sort (`sortByName`). The recursion predicate is
-- an arbitrary caller-supplied Boolean filter and is taken as a function
-- parameter, not axiomatized.
-- axioms-end

-- pure-start
/-- A node in a directory tree as seen by the collector.
* `file` — a non-directory entry.
* `dir isSymlink children` — an entry that resolves to a directory; `isSymlink`
  records whether the entry itself is a symbolic link (its `children` are the
  contents of the resolved directory). -/
inductive FSNode where
  | file
  | dir (isSymlink : Bool) (children : List (String × FSNode))
  deriving Inhabited

/-- A directory entry: its name paired with the node it denotes. -/
abbrev DirEntry := String × FSNode

/-- Order the entries of a single directory level by name (ascending). -/
def sortByName (es : List DirEntry) : List DirEntry :=
  es.mergeSort (fun a b => a.1 ≤ b.1)

/-- The breadth-first directory walk that is the desired behavior: at each
directory level the entries are emitted in name order, and then, for every
entry that resolves to a directory and that the caller's `recurse` predicate
selects, the walk descends into that directory's contents and emits its subtree
in the same way — regardless of whether the entry is a symbolic link. The result
is the in-order concatenation of every emitted entry. -/
def collectTree (recurse : DirEntry → Bool) : List DirEntry → List DirEntry
  | xs =>
    let entries := sortByName xs
    entries ++ entries.attach.flatMap (fun ⟨e, he⟩ =>
      if recurse e then
        match h : e.2 with
        | .dir _ ch => collectTree recurse ch
        | .file => []
      else [])
termination_by xs => sizeOf xs
decreasing_by
  simp_wf
  show sizeOf ch < sizeOf xs
  have hmem : e ∈ xs :=
    ((List.mergeSort_perm xs (fun a b => a.1 ≤ b.1)).mem_iff).mp he
  have h1 : sizeOf e ≤ sizeOf xs := le_of_lt (List.sizeOf_lt_of_mem hmem)
  have h2 : sizeOf ch < sizeOf e.2 := by rw [h]; simp
  have h3 : sizeOf e.2 < sizeOf e := by cases e; simp
  omega
-- pure-end

-- post-conditions-start
/-- The collected list is exactly the in-order directory walk of the input
level: the entries of every directory reachable (through the caller's `recurse`
filter) appear, in name order per level and descending into every directory
entry — symbolic links to directories included. -/
def problem_spec_collect (recurse : DirEntry → Bool) (entries0 : List DirEntry)
    (result : List DirEntry) : Prop :=
  result = collectTree recurse entries0
-- post-conditions-end

-- impl-start
/-- Whether a directory entry should be treated as a directory to descend into.
A resolved directory counts as a directory whether or not the entry is itself a
symbolic link. -/
def entryIsDir : FSNode → Bool
  | .file => false
  | .dir _ _ => true

def implementation_collect (recurse : DirEntry → Bool) :
    List DirEntry → List DirEntry
  | xs => Id.run do
    let entries := sortByName xs
    let mut acc := entries
    for h : e in entries do
      if entryIsDir e.2 && recurse e then
        match h2 : e.2 with
        | .dir _ ch => acc := acc ++ implementation_collect recurse ch
        | .file => pure ()
    return acc
termination_by xs => sizeOf xs
decreasing_by
  simp_wf
  show sizeOf ch < sizeOf xs
  have hmem : e ∈ xs :=
    ((List.mergeSort_perm xs (fun a b => a.1 ≤ b.1)).mem_iff).mp h
  have h1 : sizeOf e ≤ sizeOf xs := le_of_lt (List.sizeOf_lt_of_mem hmem)
  have hh2 : sizeOf ch < sizeOf e.2 := by rw [h2]; simp
  have h3 : sizeOf e.2 < sizeOf e := by cases e; simp
  omega
-- impl-end


-- proof-start
/-- The plain functional value that the imperative body of `implementation_collect`
evaluates to: the sorted level followed by the per-entry concatenation over
`entries.attach`. -/
def loopBody (recurse : DirEntry → Bool) (entries : List DirEntry) : List DirEntry :=
  entries ++ entries.attach.flatMap (fun (p : {e // e ∈ entries}) =>
    if entryIsDir p.1.2 && recurse p.1 then
      match p.1.2 with
      | .dir _ ch => implementation_collect recurse ch
      | .file => []
    else [])

theorem foldl_append_flatMap {α β : Type*} (l : List α) (f : α → List β) (a : List β) :
    l.foldl (fun acc x => acc ++ f x) a = a ++ l.flatMap f := by
  induction l generalizing a with
  | nil => simp
  | cons x xs ih =>
    simp only [List.foldl_cons, List.flatMap_cons, ih, List.append_assoc]

theorem impl_unfold (recurse : DirEntry → Bool) (xs : List DirEntry) :
    implementation_collect recurse xs =
      (let entries := sortByName xs;
       entries ++ entries.attach.flatMap (fun (p : {e // e ∈ entries}) =>
         if entryIsDir p.1.2 && recurse p.1 then
           match p.1.2 with
           | .dir _ ch => implementation_collect recurse ch
           | .file => []
         else [])) := by
  rw [← foldl_append_flatMap]
  conv_lhs => rw [implementation_collect]
  simp only [bind_pure_comp, map_pure, bind_pure, Id.run]
  rw [show (fun (a : DirEntry) (m : a ∈ sortByName xs) (b : List DirEntry) =>
        (if (entryIsDir a.2 && recurse a) = true then
          match h : a.2 with
          | .dir _ ch => pure (ForInStep.yield (b ++ implementation_collect recurse ch))
          | .file => pure (ForInStep.yield b)
        else pure (ForInStep.yield b) : Id (ForInStep (List DirEntry))))
      = (fun (a : DirEntry) (m : a ∈ sortByName xs) (b : List DirEntry) =>
        ForInStep.yield (b ++ (if (entryIsDir a.2 && recurse a) = true then
          match a.2 with
          | .dir _ ch => implementation_collect recurse ch
          | .file => []
        else []))) from by
      funext a m b
      obtain ⟨nm, nd⟩ := a
      cases nd with
      | file =>
        simp only [entryIsDir, Bool.false_and, Bool.false_eq_true, if_false, List.append_nil]
        rfl
      | dir s ch =>
        by_cases hr : recurse (nm, FSNode.dir s ch) = true
        · simp only [entryIsDir, Bool.true_and, hr, if_true]
          rfl
        · have hr' : (recurse (nm, FSNode.dir s ch) = true) = False := by simp [hr]
          simp only [entryIsDir, Bool.true_and, hr', if_false, List.append_nil]
          rfl]
  rw [List.forIn'_yield_eq_foldl]

theorem entry_body_eq (recurse : DirEntry → Bool) (e : DirEntry)
    (ih : ∀ (b : Bool) (ch : List DirEntry), e.2 = .dir b ch →
      implementation_collect recurse ch = collectTree recurse ch) :
    (if entryIsDir e.2 && recurse e then
       (match e.2 with
        | .dir _ ch => implementation_collect recurse ch
        | .file => []) else []) =
    (if recurse e then
       (match e.2 with
        | .dir _ ch => collectTree recurse ch
        | .file => []) else []) := by
  obtain ⟨name, node⟩ := e
  cases node with
  | file => simp [entryIsDir]
  | dir b ch =>
    simp only [entryIsDir, Bool.true_and]
    rw [ih b ch rfl]

theorem children_size_decreasing (entries0 : List DirEntry) (e : DirEntry)
    (b : Bool) (ch : List DirEntry) (hmem : e ∈ sortByName entries0)
    (hdir : e.2 = .dir b ch) : sizeOf ch < sizeOf entries0 := by
  simp only [sortByName] at hmem
  have hmem2 : e ∈ entries0 :=
    ((List.mergeSort_perm entries0 (fun a b => a.1 ≤ b.1)).mem_iff).mp hmem
  have h1 : sizeOf e ≤ sizeOf entries0 := le_of_lt (List.sizeOf_lt_of_mem hmem2)
  have h2 : sizeOf ch < sizeOf e.2 := by rw [hdir]; simp
  have h3 : sizeOf e.2 < sizeOf e := by cases e; simp
  omega

theorem main_induction (recurse : DirEntry → Bool) (entries0 : List DirEntry) :
    implementation_collect recurse entries0 = collectTree recurse entries0 := by
  have key : ∀ n, ∀ es : List DirEntry, sizeOf es < n →
      implementation_collect recurse es = collectTree recurse es := by
    intro n
    induction n with
    | zero => intro es h; omega
    | succ n ih =>
      intro es hlt
      rw [impl_unfold]
      conv_rhs => rw [collectTree]
      simp only []
      congr 1
      apply List.flatMap_congr
      intro p _
      have ih' : ∀ (b : Bool) (ch : List DirEntry), p.1.2 = .dir b ch →
          implementation_collect recurse ch = collectTree recurse ch := by
        intro b ch hdir
        have hmem : p.1 ∈ sortByName es := p.2
        have hlt2 : sizeOf ch < sizeOf es :=
          children_size_decreasing es p.1 b ch hmem hdir
        exact ih ch (by omega)
      rw [entry_body_eq recurse p.1 ih']
      cases p.1.2 <;> rfl
  exact key (sizeOf entries0 + 1) entries0 (by omega)

theorem correct_collect : ∀ (recurse : DirEntry → Bool) (entries0 : List DirEntry),
    problem_spec_collect recurse entries0 (implementation_collect recurse entries0) := by
  intro recurse entries0
  show implementation_collect recurse entries0 = collectTree recurse entries0
  exact main_induction recurse entries0

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

EXACT-EQUALITY spec (tightest shape). Positive control (Solution.lean, byte-identical, same_spec=True) verifies EXIT=0; #print axioms correct_collect -> [propext, Classical.choice, Quot.sound] (clean). All 8 attacks confirmed same_spec=True via swebench_unified.markers.same_spec.

Attack results (cmd: bash scripts/lean_verify.sh <f>):
- atk_1_prepatch (entryIsDir .dir s _ = !s; drops symlinked dirs = prepatch bug): EXIT=1 (does NOT close) -> prepatch_reproduced=true, matches Solution_prepatch.lean sorry/G-DIFF.
- atk_2_nodescend (impl = sortByName xs; never recurses): EXIT=1.
- atk_3_nosort (skip mergeSort, iterate raw order): EXIT=1.
- atk_4_ignorerecurse (descend into every dir, ignore recurse predicate): EXIT=1.
- atk_5_wrongorder (subtree walk before level, acc++entries): EXIT=1.
- atk_6_negrecurse (descend when !recurse e): EXIT=1.
- atk_7_empty (impl = []): EXIT=1.
- atk_8_echo (impl = collectTree recurse xs; ungrounded-oracle echo): EXIT=0, closes with clean axioms [propext, Classical.choice, Quot.sound]. This is the ONLY closing wrong-impl. Being extensionally = collectTree, it exhibits post-patch behavior; its faithful refined patch IS the gold patch.

RESOLVE (protocol step 2, MANDATORY for atk_8): materialized atk_8 faithful patch and ran the official harness directly (docker -> swebench_unified.run_evaluation, run_id atk8diag, image swebench/sweb.eval.x86_64.pytest-dev_1776_pytest-7982:latest). RESULT: resolved=true, FAIL_TO_PASS testing/test_collection.py::test_collect_symlink_dir PASSED, all 79 PASS_TO_PASS PASSED, 0 failures. Report: experiments/logs/run_evaluation/atk8diag/sbu_patch/pytest-dev__pytest-7982/report.json. (Note: an earlier run_resolve() call reported 'no report' purely because the 2-min bash wrapper killed the ~4-min harness; the un-timed direct run completed and resolved.) So atk_8 is a RESOLVING ECHO -> NOT a weakness per the eq/panel_1 resolve policy.

refinement.md audit: legs 1-6 all R / I / deep-model. Leg1 R (scandir+sorted->sortByName/mergeSort name-order bijection). Legs 2,3,6 I. Leg4 R (entry.is_dir() follow-symlinks -> entryIsDir, the PATCHED predicate). Leg5 R/I (recursive visit modeled deeply by implementation_collect/collectTree - function under spec, not a callee). A-consumed: none; A-reference: none dead. meta.json: opaque_callees=[], axioms=[], conf_skip=false. NO kind-3 (changed-inexpressible) legs. Deep models (collectTree, sortByName) exercised by G-CONF against a real temp filesystem with genuine os.symlinks (seed 7982, >=1e5 trees). Correspondence to real callees holds.

Conclusion: 8 attacks run (>=5); 7 divergent impls fail to close (exact-equality forbids deviation), the single closing impl (echo) has a materialized faithful patch that RESOLVES. No verify-but-not-resolve impl exists. verify => correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_2_nodescend.lean`, `atk_3_nosort.lean`, `atk_4_ignorerecurse.lean`, `atk_5_wrongorder.lean`, `atk_6_negrecurse.lean`, `atk_7_empty.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_collect recurse entries0 result := (result = collectTree recurse entries0) is an EXACT-EQUALITY spec. Any closing correct_collect forces implementation_collect = collectTree extensionally over all (recurse, entries0). collectTree descends into every FSNode.dir (symlink or not) the recurse filter selects = exactly post-patch behavior. So every closing impl is behaviorally identical to the gold patch; no closing impl can carry prepatch semantics.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_nodescend.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_nosort.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_ignorerecurse.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_wrongorder.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_negrecurse.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_empty.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is consumed as an axiom. The directory-tree walk is
-- modeled deeply below (`collectTree`), and the per-level ordering operation is
-- modeled deeply as a name-keyed sort (`sortByName`). The recursion predicate is
-- an arbitrary caller-supplied Boolean filter and is taken as a function
-- parameter, not axiomatized.
-- axioms-end

-- pure-start
/-- A node in a directory tree as seen by the collector.
* `file` — a non-directory entry.
* `dir isSymlink children` — an entry that resolves to a directory; `isSymlink`
  records whether the entry itself is a symbolic link (its `children` are the
  contents of the resolved directory). -/
inductive FSNode where
  | file
  | dir (isSymlink : Bool) (children : List (String × FSNode))
  deriving Inhabited

/-- A directory entry: its name paired with the node it denotes. -/
abbrev DirEntry := String × FSNode

/-- Order the entries of a single directory level by name (ascending). -/
def sortByName (es : List DirEntry) : List DirEntry :=
  es.mergeSort (fun a b => a.1 ≤ b.1)

/-- The breadth-first directory walk that is the desired behavior: at each
directory level the entries are emitted in name order, and then, for every
entry that resolves to a directory and that the caller's `recurse` predicate
selects, the walk descends into that directory's contents and emits its subtree
in the same way — regardless of whether the entry is a symbolic link. The result
is the in-order concatenation of every emitted entry. -/
def collectTree (recurse : DirEntry → Bool) : List DirEntry → List DirEntry
  | xs =>
    let entries := sortByName xs
    entries ++ entries.attach.flatMap (fun ⟨e, he⟩ =>
      if recurse e then
        match h : e.2 with
        | .dir _ ch => collectTree recurse ch
        | .file => []
      else [])
termination_by xs => sizeOf xs
decreasing_by
  simp_wf
  show sizeOf ch < sizeOf xs
  have hmem : e ∈ xs :=
    ((List.mergeSort_perm xs (fun a b => a.1 ≤ b.1)).mem_iff).mp he
  have h1 : sizeOf e ≤ sizeOf xs := le_of_lt (List.sizeOf_lt_of_mem hmem)
  have h2 : sizeOf ch < sizeOf e.2 := by rw [h]; simp
  have h3 : sizeOf e.2 < sizeOf e := by cases e; simp
  omega
-- pure-end

-- post-conditions-start
/-- The collected list is exactly the in-order directory walk of the input
level: the entries of every directory reachable (through the caller's `recurse`
filter) appear, in name order per level and descending into every directory
entry — symbolic links to directories included. -/
def problem_spec_collect (recurse : DirEntry → Bool) (entries0 : List DirEntry)
    (result : List DirEntry) : Prop :=
  result = collectTree recurse entries0
-- post-conditions-end

-- impl-start
/-- Whether a directory entry should be treated as a directory to descend into.
A resolved directory counts as a directory whether or not the entry is itself a
symbolic link. -/
def entryIsDir : FSNode → Bool
  | .file => false
  | .dir _ _ => true

def implementation_collect (recurse : DirEntry → Bool) :
    List DirEntry → List DirEntry
  | xs => Id.run do
    let entries := sortByName xs
    let mut acc := entries
    for h : e in entries do
      if entryIsDir e.2 && recurse e then
        match h2 : e.2 with
        | .dir _ ch => acc := acc ++ implementation_collect recurse ch
        | .file => pure ()
    return acc
termination_by xs => sizeOf xs
decreasing_by
  simp_wf
  show sizeOf ch < sizeOf xs
  have hmem : e ∈ xs :=
    ((List.mergeSort_perm xs (fun a b => a.1 ≤ b.1)).mem_iff).mp h
  have h1 : sizeOf e ≤ sizeOf xs := le_of_lt (List.sizeOf_lt_of_mem hmem)
  have hh2 : sizeOf ch < sizeOf e.2 := by rw [h2]; simp
  have h3 : sizeOf e.2 < sizeOf e := by cases e; simp
  omega
-- impl-end


-- proof-start
/-- The plain functional value that the imperative body of `implementation_collect`
evaluates to: the sorted level followed by the per-entry concatenation over
`entries.attach`. -/
def loopBody (recurse : DirEntry → Bool) (entries : List DirEntry) : List DirEntry :=
  entries ++ entries.attach.flatMap (fun (p : {e // e ∈ entries}) =>
    if entryIsDir p.1.2 && recurse p.1 then
      match p.1.2 with
      | .dir _ ch => implementation_collect recurse ch
      | .file => []
    else [])

theorem foldl_append_flatMap {α β : Type*} (l : List α) (f : α → List β) (a : List β) :
    l.foldl (fun acc x => acc ++ f x) a = a ++ l.flatMap f := by
  induction l generalizing a with
  | nil => simp
  | cons x xs ih =>
    simp only [List.foldl_cons, List.flatMap_cons, ih, List.append_assoc]

theorem impl_unfold (recurse : DirEntry → Bool) (xs : List DirEntry) :
    implementation_collect recurse xs =
      (let entries := sortByName xs;
       entries ++ entries.attach.flatMap (fun (p : {e // e ∈ entries}) =>
         if entryIsDir p.1.2 && recurse p.1 then
           match p.1.2 with
           | .dir _ ch => implementation_collect recurse ch
           | .file => []
         else [])) := by
  rw [← foldl_append_flatMap]
  conv_lhs => rw [implementation_collect]
  simp only [bind_pure_comp, map_pure, bind_pure, Id.run]
  rw [show (fun (a : DirEntry) (m : a ∈ sortByName xs) (b : List DirEntry) =>
        (if (entryIsDir a.2 && recurse a) = true then
          match h : a.2 with
          | .dir _ ch => pure (ForInStep.yield (b ++ implementation_collect recurse ch))
          | .file => pure (ForInStep.yield b)
        else pure (ForInStep.yield b) : Id (ForInStep (List DirEntry))))
      = (fun (a : DirEntry) (m : a ∈ sortByName xs) (b : List DirEntry) =>
        ForInStep.yield (b ++ (if (entryIsDir a.2 && recurse a) = true then
          match a.2 with
          | .dir _ ch => implementation_collect recurse ch
          | .file => []
        else []))) from by
      funext a m b
      obtain ⟨nm, nd⟩ := a
      cases nd with
      | file =>
        simp only [entryIsDir, Bool.false_and, Bool.false_eq_true, if_false, List.append_nil]
        rfl
      | dir s ch =>
        by_cases hr : recurse (nm, FSNode.dir s ch) = true
        · simp only [entryIsDir, Bool.true_and, hr, if_true]
          rfl
        · have hr' : (recurse (nm, FSNode.dir s ch) = true) = False := by simp [hr]
          simp only [entryIsDir, Bool.true_and, hr', if_false, List.append_nil]
          rfl]
  rw [List.forIn'_yield_eq_foldl]

theorem entry_body_eq (recurse : DirEntry → Bool) (e : DirEntry)
    (ih : ∀ (b : Bool) (ch : List DirEntry), e.2 = .dir b ch →
      implementation_collect recurse ch = collectTree recurse ch) :
    (if entryIsDir e.2 && recurse e then
       (match e.2 with
        | .dir _ ch => implementation_collect recurse ch
        | .file => []) else []) =
    (if recurse e then
       (match e.2 with
        | .dir _ ch => collectTree recurse ch
        | .file => []) else []) := by
  obtain ⟨name, node⟩ := e
  cases node with
  | file => simp [entryIsDir]
  | dir b ch =>
    simp only [entryIsDir, Bool.true_and]
    rw [ih b ch rfl]

theorem children_size_decreasing (entries0 : List DirEntry) (e : DirEntry)
    (b : Bool) (ch : List DirEntry) (hmem : e ∈ sortByName entries0)
    (hdir : e.2 = .dir b ch) : sizeOf ch < sizeOf entries0 := by
  simp only [sortByName] at hmem
  have hmem2 : e ∈ entries0 :=
    ((List.mergeSort_perm entries0 (fun a b => a.1 ≤ b.1)).mem_iff).mp hmem
  have h1 : sizeOf e ≤ sizeOf entries0 := le_of_lt (List.sizeOf_lt_of_mem hmem2)
  have h2 : sizeOf ch < sizeOf e.2 := by rw [hdir]; simp
  have h3 : sizeOf e.2 < sizeOf e := by cases e; simp
  omega

theorem main_induction (recurse : DirEntry → Bool) (entries0 : List DirEntry) :
    implementation_collect recurse entries0 = collectTree recurse entries0 := by
  have key : ∀ n, ∀ es : List DirEntry, sizeOf es < n →
      implementation_collect recurse es = collectTree recurse es := by
    intro n
    induction n with
    | zero => intro es h; omega
    | succ n ih =>
      intro es hlt
      rw [impl_unfold]
      conv_rhs => rw [collectTree]
      simp only []
      congr 1
      apply List.flatMap_congr
      intro p _
      have ih' : ∀ (b : Bool) (ch : List DirEntry), p.1.2 = .dir b ch →
          implementation_collect recurse ch = collectTree recurse ch := by
        intro b ch hdir
        have hmem : p.1 ∈ sortByName es := p.2
        have hlt2 : sizeOf ch < sizeOf es :=
          children_size_decreasing es p.1 b ch hmem hdir
        exact ih ch (by omega)
      rw [entry_body_eq recurse p.1 ih']
      cases p.1.2 <;> rfl
  exact key (sizeOf entries0 + 1) entries0 (by omega)

theorem correct_collect : ∀ (recurse : DirEntry → Bool) (entries0 : List DirEntry),
    problem_spec_collect recurse entries0 (implementation_collect recurse entries0) := by
  intro recurse entries0
  show implementation_collect recurse entries0 = collectTree recurse entries0
  exact main_induction recurse entries0

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

EXACT-EQUALITY spec (tightest shape). Positive control (Solution.lean, byte-identical, same_spec=True) verifies EXIT=0; #print axioms correct_collect -> [propext, Classical.choice, Quot.sound] (clean). All 8 attacks confirmed same_spec=True via swebench_unified.markers.same_spec.

Attack results (cmd: bash scripts/lean_verify.sh <f>):
- atk_1_prepatch (entryIsDir .dir s _ = !s; drops symlinked dirs = prepatch bug): EXIT=1 (does NOT close) -> prepatch_reproduced=true, matches Solution_prepatch.lean sorry/G-DIFF.
- atk_2_nodescend (impl = sortByName xs; never recurses): EXIT=1.
- atk_3_nosort (skip mergeSort, iterate raw order): EXIT=1.
- atk_4_ignorerecurse (descend into every dir, ignore recurse predicate): EXIT=1.
- atk_5_wrongorder (subtree walk before level, acc++entries): EXIT=1.
- atk_6_negrecurse (descend when !recurse e): EXIT=1.
- atk_7_empty (impl = []): EXIT=1.
- atk_8_echo (impl = collectTree recurse xs; ungrounded-oracle echo): EXIT=0, closes with clean axioms [propext, Classical.choice, Quot.sound]. This is the ONLY closing wrong-impl. Being extensionally = collectTree, it exhibits post-patch behavior; its faithful refined patch IS the gold patch.

RESOLVE (protocol step 2, MANDATORY for atk_8): materialized atk_8 faithful patch and ran the official harness directly (docker -> swebench_unified.run_evaluation, run_id atk8diag, image swebench/sweb.eval.x86_64.pytest-dev_1776_pytest-7982:latest). RESULT: resolved=true, FAIL_TO_PASS testing/test_collection.py::test_collect_symlink_dir PASSED, all 79 PASS_TO_PASS PASSED, 0 failures. Report: experiments/logs/run_evaluation/atk8diag/sbu_patch/pytest-dev__pytest-7982/report.json. (Note: an earlier run_resolve() call reported 'no report' purely because the 2-min bash wrapper killed the ~4-min harness; the un-timed direct run completed and resolved.) So atk_8 is a RESOLVING ECHO -> NOT a weakness per the eq/panel_1 resolve policy.

refinement.md audit: legs 1-6 all R / I / deep-model. Leg1 R (scandir+sorted->sortByName/mergeSort name-order bijection). Legs 2,3,6 I. Leg4 R (entry.is_dir() follow-symlinks -> entryIsDir, the PATCHED predicate). Leg5 R/I (recursive visit modeled deeply by implementation_collect/collectTree - function under spec, not a callee). A-consumed: none; A-reference: none dead. meta.json: opaque_callees=[], axioms=[], conf_skip=false. NO kind-3 (changed-inexpressible) legs. Deep models (collectTree, sortByName) exercised by G-CONF against a real temp filesystem with genuine os.symlinks (seed 7982, >=1e5 trees). Correspondence to real callees holds.

Conclusion: 8 attacks run (>=5); 7 divergent impls fail to close (exact-equality forbids deviation), the single closing impl (echo) has a materialized faithful patch that RESOLVES. No verify-but-not-resolve impl exists. verify => correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on pytest-dev__pytest-7982 lean bundle. VERDICT: FAITHFUL — no input found where the modeled function disagrees with the real post-patch callee.

Setup verified:
- same_spec(Solution.lean, Solution_prepatch.lean, lean)=True: frozen regions (imports/axioms/pure/post-conditions) byte-identical; only impl+proof differ.
- Lean compiles exit 0, no sorry. #print axioms correct_collect = [propext, Classical.choice, Quot.sound] — clean, no sorryAx. Real proof.
- conformance_check.py: 120,000 real materialized-FS trees with genuine os.symlinks, 0 disagreements vs real post-patch visit. status=pass.
- Real callee at base_commit a7e38c5c confirmed via git: visit = sorted(scandir,key=name) -> yield from entries -> for entry: if entry.is_dir(follow_symlinks=False) and recurse(entry): yield from visit(...). Gold drops follow_symlinks=False. Spec models post-patch (desired) behavior; Solution_prepatch correct_collect is sorry (G-DIFF), as intended.

Attacker probes for drift (all NEGATIVE):
1. Sort order: Lean String.mergeSort (·.1 ≤ ·.1) matches Python sorted(key=name) exactly on mixed case, digits, '_'/'~'/'.', and non-ASCII 'é'. Verified head-to-head. No divergence.
2. Walk order: model 'entries ++ entries.flatMap(subtree)' faithfully mirrors the ACTUAL code (full level then per-entry depth-first recursion), not the misleading 'breadth-first' docstring. Correct.
3. entryIsDir (post-patch): FSNode.dir _ _ -> true (symlink flag ignored), matching is_dir() default follow_symlinks=True. symlink-to-file / broken symlink report is_dir()=False under both flags and are modeled as FSNode.file (never .dir) -> never descended, matching real. Conf materialized real symlinked dirs and confirmed descent.
4. recurse: universally quantified function param DirEntry->Bool (superset of real, which keys on the entry) — faithful, not axiomatized, no debt.
5. Cycles / duplicate names: not constructible in the finite inductive FSNode domain (declared modeling boundary) and not realizable on a real FS within one directory (unique names). No diverging input constructible.

No UNCHANGED external callee axiomatized (A-consumed: none). The deep model of visit agrees with the real callee on every input in the modeled domain. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view generated via markers.spec_view (lean). Mechanical leakage.screen passes (hard_failures=[]); changed symbol set = {'visit'}. same_spec(Solution, Solution_prepatch)=True; no relaxed_leakage flag.

Semantic review: the public problem_statement already discloses the full intent of the fix — 'When there is a symlink to a directory... it should be followed and collected as usual' and 'I added a follow_symlinks=False in there... it does not match the previous behavior and should be removed.' Thus the fact that symlinked directories must be followed/collected is PUBLIC.

The spec view (post-conditions + collectTree model + FSNode with an isSymlink field) describes the desired post-patch behavior — descend into every directory entry 'regardless of whether the entry is a symbolic link' / 'symbolic links to directories included.' This is congruent with the public problem_statement, not information beyond it. Modeling an isSymlink flag is legitimate since symlinks are the explicit subject of the public task.

The discriminating gold edit itself (entry.is_dir(follow_symlinks=False) -> entry.is_dir(), modeled as the two entryIsDir variants where prepatch = !isSymlink) lives ENTIRELY in the elided impl region ('implementation elided — supplied by the consumer') and the elided proof region. The spec view contains: no diff markers, no pathlib.py path, no verbatim gold-patch line, no 'visit'/'is_dir'/'follow_symlinks' tokens, and no bug/fix narration. A consumer sees a symlink-following directory-walk spec — which is precisely what the public task asks for — but must still choose the discriminator (entryIsDir treating dir _ _ as true) themselves. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
