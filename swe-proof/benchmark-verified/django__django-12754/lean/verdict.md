# P2 adversarial audit — django__django-12754

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_3.lean`, `atk_4.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. Every attack whose proof CLOSED with clean axioms (atk_3 duplicate-all, atk_4 reverse, atk_6 self-dep-duplicated) is set-equal to the gold dependency list; each materialized faithful patch RESOLVED under the official harness (gold positive-control also resolved). No verify⇏⇒correct break.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,24 +91,13 @@
 -- post-conditions-end
 
 -- impl-start
--- The field-removal dependencies a single dotted base contributes: one per
--- field the base previously declared (oldFields), no longer declares
--- (newFields), and that the new model itself declares (modelFields).
-def removedFieldDeps (ba bn : String) (oldFields newFields modelFields : List String) : List Dep :=
-  (oldFields.filter (fun f => !(newFields.contains f) && modelFields.contains f)).map
-    (fun f => ⟨ba, bn, some f, false⟩)
-
--- The dependencies a single base contributes: nothing for a non-dotted base;
--- for a dotted base, the base-creation dependency followed by the field-removal
--- dependencies (only when both states of the base are known).
-def baseDeps (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String)) : Base → List Dep
+-- WRONG (prepatch bug): a dotted base contributes ONLY its creation dep;
+-- the moved-field removal deps are dropped. The spec's 3rd disjunct is then
+-- unsatisfiable in the forward direction, so correct_ cannot close.
+def baseDeps (_modelFields : List String)
+    (_fromLookup _toLookup : String → String → Option (List String)) : Base → List Dep
   | Base.other => []
-  | Base.dotted ba bn =>
-      ⟨ba, bn, none, true⟩ ::
-        (match fromLookup ba bn, toLookup ba bn with
-         | some oldFields, some newFields => removedFieldDeps ba bn oldFields newFields modelFields
-         | _, _ => [])
+  | Base.dotted ba bn => [⟨ba, bn, none, true⟩]
 
 def implementation_createModelDeps
     (appLabel modelName : String) (bases : List Base) (modelFields : List String)
@@ -122,138 +111,15 @@
   return deps
 -- impl-end
 
-
 -- proof-start
-/-- The explicit pure-list normal form of `implementation_createModelDeps`. -/
-def resultForm (appLabel modelName : String) (bases : List Base) (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String))
-    (primaryKeyRel : Option (String × String)) : List Dep :=
-  [⟨appLabel, modelName, none, false⟩] ++
-    bases.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) [] ++
-    (match primaryKeyRel with
-     | some (pa, pn) => [⟨pa, pn, none, true⟩]
-     | none => [])
-
-theorem impl_eq_normalForm (appLabel modelName : String) (bases : List Base)
-    (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String))
-    (primaryKeyRel : Option (String × String)) :
-    implementation_createModelDeps appLabel modelName bases modelFields fromLookup toLookup
-        primaryKeyRel =
-      resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel := by
-  simp only [implementation_createModelDeps, resultForm, Id.run, bind, pure]
-  cases primaryKeyRel <;> simp [List.forIn_yield_eq_foldl]
-
-theorem removedFieldDeps_mem (ba bn : String) (oldFields newFields modelFields : List String)
-    (d : Dep) :
-    d ∈ removedFieldDeps ba bn oldFields newFields modelFields ↔
-      ∃ f, f ∈ oldFields ∧ ¬ newFields.contains f ∧ modelFields.contains f ∧
-        d = ⟨ba, bn, some f, false⟩ := by
-  simp only [removedFieldDeps, List.mem_map, List.mem_filter, Bool.and_eq_true,
-    Bool.not_eq_true']
-  constructor
-  · rintro ⟨f, ⟨hf, h1, h2⟩, rfl⟩
-    exact ⟨f, hf, by simpa using h1, h2, rfl⟩
-  · rintro ⟨f, hf, h1, h2, rfl⟩
-    exact ⟨f, ⟨hf, by simpa using h1, h2⟩, rfl⟩
-
-theorem baseDeps_mem (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String)) (base : Base) (d : Dep) :
-    d ∈ baseDeps modelFields fromLookup toLookup base ↔
-      (∃ ba bn, base = Base.dotted ba bn ∧
-        (d = ⟨ba, bn, none, true⟩ ∨
-         (∃ fs gs, fromLookup ba bn = some fs ∧ toLookup ba bn = some gs ∧
-            d ∈ removedFieldDeps ba bn fs gs modelFields))) := by
-  cases base with
-  | other => simp [baseDeps]
-  | dotted ba bn =>
-    simp only [baseDeps, List.mem_cons]
-    constructor
-    · rintro (h | h)
-      · exact ⟨ba, bn, rfl, Or.inl h⟩
-      · refine ⟨ba, bn, rfl, Or.inr ?_⟩
-        revert h
-        cases hf : fromLookup ba bn with
-        | none => simp
-        | some fs =>
-          cases hg : toLookup ba bn with
-          | none => simp
-          | some gs => intro h; exact ⟨fs, gs, rfl, rfl, h⟩
-    · rintro ⟨ba', bn', heq, hd⟩
-      cases heq
-      rcases hd with hd | ⟨fs, gs, hf, hg, hmem⟩
-      · exact Or.inl hd
-      · refine Or.inr ?_
-        rw [hf, hg]
-        exact hmem
-
-theorem baseFold_mem (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String)) (bases : List Base) (d : Dep) :
-    d ∈ bases.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) [] ↔
-      ∃ base, base ∈ bases ∧ d ∈ baseDeps modelFields fromLookup toLookup base := by
-  have general : ∀ (l : List Base) (init : List Dep),
-      d ∈ l.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) init ↔
-        d ∈ init ∨ ∃ base, base ∈ l ∧ d ∈ baseDeps modelFields fromLookup toLookup base := by
-    intro l
-    induction l with
-    | nil => intro init; simp
-    | cons b bs ih =>
-      intro init
-      rw [List.foldl_cons, ih (init ++ baseDeps modelFields fromLookup toLookup b)]
-      simp only [List.mem_append, List.mem_cons]
-      constructor
-      · rintro ((h | h) | ⟨base, hb, hd⟩)
-        · exact Or.inl h
-        · exact Or.inr ⟨b, Or.inl rfl, h⟩
-        · exact Or.inr ⟨base, Or.inr hb, hd⟩
-      · rintro (h | ⟨base, (rfl | hb), hd⟩)
-        · exact Or.inl (Or.inl h)
-        · exact Or.inl (Or.inr hd)
-        · exact Or.inr ⟨base, hb, hd⟩
-  simpa using general bases []
-
-theorem contains_iff_mem (l : List String) (f : String) :
-    l.contains f = true ↔ f ∈ l := by
-  simp
-
-theorem spec_iff (appLabel modelName : String) (bases : List Base) (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String))
-    (primaryKeyRel : Option (String × String)) (d : Dep) :
-    d ∈ resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel ↔
-      ((d = ⟨appLabel, modelName, none, false⟩) ∨
-       (∃ ba bn, Base.dotted ba bn ∈ bases ∧ d = ⟨ba, bn, none, true⟩) ∨
-       (∃ ba bn fs gs f, Base.dotted ba bn ∈ bases ∧
-          fromLookup ba bn = some fs ∧ toLookup ba bn = some gs ∧
-          f ∈ fs ∧ f ∉ gs ∧ f ∈ modelFields ∧
-          d = ⟨ba, bn, some f, false⟩) ∨
-       (∃ pa pn, primaryKeyRel = some (pa, pn) ∧ d = ⟨pa, pn, none, true⟩)) := by
-  unfold resultForm
-  simp only [List.append_assoc, List.mem_append, List.mem_singleton, baseFold_mem, baseDeps_mem,
-    removedFieldDeps_mem, contains_iff_mem]
-  constructor
-  · rintro (h | ⟨base, hbase, ba, bn, rfl, (h | ⟨fs, gs, hf, hg, f, hfs, hgs, hfm, rfl⟩)⟩ | h)
-    · exact Or.inl h
-    · exact Or.inr (Or.inl ⟨ba, bn, hbase, h⟩)
-    · exact Or.inr (Or.inr (Or.inl ⟨ba, bn, fs, gs, f, hbase, hf, hg, hfs, hgs, hfm, rfl⟩))
-    · rcases primaryKeyRel with _ | ⟨pa, pn⟩
-      · simp at h
-      · simp at h; exact Or.inr (Or.inr (Or.inr ⟨pa, pn, rfl, h⟩))
-  · rintro (h | ⟨ba, bn, hbase, rfl⟩ | ⟨ba, bn, fs, gs, f, hbase, hf, hg, hfs, hgs, hfm, rfl⟩ | ⟨pa, pn, hpk, rfl⟩)
-    · exact Or.inl h
-    · exact Or.inr (Or.inl ⟨_, hbase, ba, bn, rfl, Or.inl rfl⟩)
-    · exact Or.inr (Or.inl ⟨_, hbase, ba, bn, rfl, Or.inr ⟨fs, gs, hf, hg, f, hfs, hgs, hfm, rfl⟩⟩)
-    · exact Or.inr (Or.inr (by rw [hpk]; simp))
-
 theorem correct_createModelDeps :
     ∀ (appLabel modelName : String) (bases : List Base) (modelFields : List String)
       (fromLookup toLookup : String → String → Option (List String))
       (primaryKeyRel : Option (String × String)),
       problem_spec_createModelDeps appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel
         (implementation_createModelDeps appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel) := by
-  intro appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel
-  unfold problem_spec_createModelDeps
-  rw [impl_eq_normalForm]
-  intro d
-  exact spec_iff appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel d
-
+  intro appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel d
+  unfold problem_spec_createModelDeps implementation_createModelDeps
+  simp only [Id.run, bind, pure]
+  constructor <;> intro h <;> simp_all <;> aesop
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,169 +91,22 @@
 -- post-conditions-end
 
 -- impl-start
--- The field-removal dependencies a single dotted base contributes: one per
--- field the base previously declared (oldFields), no longer declares
--- (newFields), and that the new model itself declares (modelFields).
-def removedFieldDeps (ba bn : String) (oldFields newFields modelFields : List String) : List Dep :=
-  (oldFields.filter (fun f => !(newFields.contains f) && modelFields.contains f)).map
-    (fun f => ⟨ba, bn, some f, false⟩)
-
--- The dependencies a single base contributes: nothing for a non-dotted base;
--- for a dotted base, the base-creation dependency followed by the field-removal
--- dependencies (only when both states of the base are known).
-def baseDeps (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String)) : Base → List Dep
-  | Base.other => []
-  | Base.dotted ba bn =>
-      ⟨ba, bn, none, true⟩ ::
-        (match fromLookup ba bn, toLookup ba bn with
-         | some oldFields, some newFields => removedFieldDeps ba bn oldFields newFields modelFields
-         | _, _ => [])
-
+-- WRONG (boundary): returns the empty list. Misses the self proxy-removal
+-- dep (and all others), so the spec's forward direction is unsatisfiable.
 def implementation_createModelDeps
-    (appLabel modelName : String) (bases : List Base) (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String))
-    (primaryKeyRel : Option (String × String)) : List Dep := Id.run do
-  let mut deps : List Dep := [⟨appLabel, modelName, none, false⟩]
-  for base in bases do
-    deps := deps ++ baseDeps modelFields fromLookup toLookup base
-  if let some (pa, pn) := primaryKeyRel then
-    deps := deps ++ [⟨pa, pn, none, true⟩]
-  return deps
+    (_appLabel _modelName : String) (_bases : List Base) (_modelFields : List String)
+    (_fromLookup _toLookup : String → String → Option (List String))
+    (_primaryKeyRel : Option (String × String)) : List Dep := []
 -- impl-end
 
-
 -- proof-start
-/-- The explicit pure-list normal form of `implementation_createModelDeps`. -/
-def resultForm (appLabel modelName : String) (bases : List Base) (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String))
-    (primaryKeyRel : Option (String × String)) : List Dep :=
-  [⟨appLabel, modelName, none, false⟩] ++
-    bases.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) [] ++
-    (match primaryKeyRel with
-     | some (pa, pn) => [⟨pa, pn, none, true⟩]
-     | none => [])
-
-theorem impl_eq_normalForm (appLabel modelName : String) (bases : List Base)
-    (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String))
-    (primaryKeyRel : Option (String × String)) :
-    implementation_createModelDeps appLabel modelName bases modelFields fromLookup toLookup
-        primaryKeyRel =
-      resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel := by
-  simp only [implementation_createModelDeps, resultForm, Id.run, bind, pure]
-  cases primaryKeyRel <;> simp [List.forIn_yield_eq_foldl]
-
-theorem removedFieldDeps_mem (ba bn : String) (oldFields newFields modelFields : List String)
-    (d : Dep) :
-    d ∈ removedFieldDeps ba bn oldFields newFields modelFields ↔
-      ∃ f, f ∈ oldFields ∧ ¬ newFields.contains f ∧ modelFields.contains f ∧
-        d = ⟨ba, bn, some f, false⟩ := by
-  simp only [removedFieldDeps, List.mem_map, List.mem_filter, Bool.and_eq_true,
-    Bool.not_eq_true']
-  constructor
-  · rintro ⟨f, ⟨hf, h1, h2⟩, rfl⟩
-    exact ⟨f, hf, by simpa using h1, h2, rfl⟩
-  · rintro ⟨f, hf, h1, h2, rfl⟩
-    exact ⟨f, ⟨hf, by simpa using h1, h2⟩, rfl⟩
-
-theorem baseDeps_mem (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String)) (base : Base) (d : Dep) :
-    d ∈ baseDeps modelFields fromLookup toLookup base ↔
-      (∃ ba bn, base = Base.dotted ba bn ∧
-        (d = ⟨ba, bn, none, true⟩ ∨
-         (∃ fs gs, fromLookup ba bn = some fs ∧ toLookup ba bn = some gs ∧
-            d ∈ removedFieldDeps ba bn fs gs modelFields))) := by
-  cases base with
-  | other => simp [baseDeps]
-  | dotted ba bn =>
-    simp only [baseDeps, List.mem_cons]
-    constructor
-    · rintro (h | h)
-      · exact ⟨ba, bn, rfl, Or.inl h⟩
-      · refine ⟨ba, bn, rfl, Or.inr ?_⟩
-        revert h
-        cases hf : fromLookup ba bn with
-        | none => simp
-        | some fs =>
-          cases hg : toLookup ba bn with
-          | none => simp
-          | some gs => intro h; exact ⟨fs, gs, rfl, rfl, h⟩
-    · rintro ⟨ba', bn', heq, hd⟩
-      cases heq
-      rcases hd with hd | ⟨fs, gs, hf, hg, hmem⟩
-      · exact Or.inl hd
-      · refine Or.inr ?_
-        rw [hf, hg]
-        exact hmem
-
-theorem baseFold_mem (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String)) (bases : List Base) (d : Dep) :
-    d ∈ bases.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) [] ↔
-      ∃ base, base ∈ bases ∧ d ∈ baseDeps modelFields fromLookup toLookup base := by
-  have general : ∀ (l : List Base) (init : List Dep),
-      d ∈ l.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) init ↔
-        d ∈ init ∨ ∃ base, base ∈ l ∧ d ∈ baseDeps modelFields fromLookup toLookup base := by
-    intro l
-    induction l with
-    | nil => intro init; simp
-    | cons b bs ih =>
-      intro init
-      rw [List.foldl_cons, ih (init ++ baseDeps modelFields fromLookup toLookup b)]
-      simp only [List.mem_append, List.mem_cons]
-      constructor
-      · rintro ((h | h) | ⟨base, hb, hd⟩)
-        · exact Or.inl h
-        · exact Or.inr ⟨b, Or.inl rfl, h⟩
-        · exact Or.inr ⟨base, Or.inr hb, hd⟩
-      · rintro (h | ⟨base, (rfl | hb), hd⟩)
-        · exact Or.inl (Or.inl h)
-        · exact Or.inl (Or.inr hd)
-        · exact Or.inr ⟨base, hb, hd⟩
-  simpa using general bases []
-
-theorem contains_iff_mem (l : List String) (f : String) :
-    l.contains f = true ↔ f ∈ l := by
-  simp
-
-theorem spec_iff (appLabel modelName : String) (bases : List Base) (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String))
-    (primaryKeyRel : Option (String × String)) (d : Dep) :
-    d ∈ resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel ↔
-      ((d = ⟨appLabel, modelName, none, false⟩) ∨
-       (∃ ba bn, Base.dotted ba bn ∈ bases ∧ d = ⟨ba, bn, none, true⟩) ∨
-       (∃ ba bn fs gs f, Base.dotted ba bn ∈ bases ∧
-          fromLookup ba bn = some fs ∧ toLookup ba bn = some gs ∧
-          f ∈ fs ∧ f ∉ gs ∧ f ∈ modelFields ∧
-          d = ⟨ba, bn, some f, false⟩) ∨
-       (∃ pa pn, primaryKeyRel = some (pa, pn) ∧ d = ⟨pa, pn, none, true⟩)) := by
-  unfold resultForm
-  simp only [List.append_assoc, List.mem_append, List.mem_singleton, baseFold_mem, baseDeps_mem,
-    removedFieldDeps_mem, contains_iff_mem]
-  constructor
-  · rintro (h | ⟨base, hbase, ba, bn, rfl, (h | ⟨fs, gs, hf, hg, f, hfs, hgs, hfm, rfl⟩)⟩ | h)
-    · exact Or.inl h
-    · exact Or.inr (Or.inl ⟨ba, bn, hbase, h⟩)
-    · exact Or.inr (Or.inr (Or.inl ⟨ba, bn, fs, gs, f, hbase, hf, hg, hfs, hgs, hfm, rfl⟩))
-    · rcases primaryKeyRel with _ | ⟨pa, pn⟩
-      · simp at h
-      · simp at h; exact Or.inr (Or.inr (Or.inr ⟨pa, pn, rfl, h⟩))
-  · rintro (h | ⟨ba, bn, hbase, rfl⟩ | ⟨ba, bn, fs, gs, f, hbase, hf, hg, hfs, hgs, hfm, rfl⟩ | ⟨pa, pn, hpk, rfl⟩)
-    · exact Or.inl h
-    · exact Or.inr (Or.inl ⟨_, hbase, ba, bn, rfl, Or.inl rfl⟩)
-    · exact Or.inr (Or.inl ⟨_, hbase, ba, bn, rfl, Or.inr ⟨fs, gs, hf, hg, f, hfs, hgs, hfm, rfl⟩⟩)
-    · exact Or.inr (Or.inr (by rw [hpk]; simp))
-
 theorem correct_createModelDeps :
     ∀ (appLabel modelName : String) (bases : List Base) (modelFields : List String)
       (fromLookup toLookup : String → String → Option (List String))
       (primaryKeyRel : Option (String × String)),
       problem_spec_createModelDeps appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel
         (implementation_createModelDeps appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel) := by
-  intro appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel
-  unfold problem_spec_createModelDeps
-  rw [impl_eq_normalForm]
-  intro d
-  exact spec_iff appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel d
-
+  intro appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel d
+  unfold problem_spec_createModelDeps implementation_createModelDeps
+  constructor <;> intro h <;> simp_all <;> aesop
 -- proof-end
```

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -91,16 +91,13 @@
 -- post-conditions-end
 
 -- impl-start
--- The field-removal dependencies a single dotted base contributes: one per
--- field the base previously declared (oldFields), no longer declares
--- (newFields), and that the new model itself declares (modelFields).
+-- WRONG (but same-spec): emits every gold dependency TWICE (deps ++ deps).
+-- Set-equal to gold, so the membership spec still closes; behaviorally the
+-- Python dependency list feeds a topological sort, so duplicates are inert.
 def removedFieldDeps (ba bn : String) (oldFields newFields modelFields : List String) : List Dep :=
   (oldFields.filter (fun f => !(newFields.contains f) && modelFields.contains f)).map
     (fun f => ⟨ba, bn, some f, false⟩)
 
--- The dependencies a single base contributes: nothing for a non-dotted base;
--- for a dotted base, the base-creation dependency followed by the field-removal
--- dependencies (only when both states of the base are known).
 def baseDeps (modelFields : List String)
     (fromLookup toLookup : String → String → Option (List String)) : Base → List Dep
   | Base.other => []
@@ -119,12 +116,10 @@
     deps := deps ++ baseDeps modelFields fromLookup toLookup base
   if let some (pa, pn) := primaryKeyRel then
     deps := deps ++ [⟨pa, pn, none, true⟩]
-  return deps
+  return deps ++ deps
 -- impl-end
 
-
 -- proof-start
-/-- The explicit pure-list normal form of `implementation_createModelDeps`. -/
 def resultForm (appLabel modelName : String) (bases : List Base) (modelFields : List String)
     (fromLookup toLookup : String → String → Option (List String))
     (primaryKeyRel : Option (String × String)) : List Dep :=
@@ -140,7 +135,8 @@
     (primaryKeyRel : Option (String × String)) :
     implementation_createModelDeps appLabel modelName bases modelFields fromLookup toLookup
         primaryKeyRel =
-      resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel := by
+      (resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel) ++
+      (resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel) := by
   simp only [implementation_createModelDeps, resultForm, Id.run, bind, pure]
   cases primaryKeyRel <;> simp [List.forIn_yield_eq_foldl]
 
@@ -254,6 +250,6 @@
   unfold problem_spec_createModelDeps
   rw [impl_eq_normalForm]
   intro d
+  rw [List.mem_append, or_self]
   exact spec_iff appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel d
-
 -- proof-end
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -91,16 +91,13 @@
 -- post-conditions-end
 
 -- impl-start
--- The field-removal dependencies a single dotted base contributes: one per
--- field the base previously declared (oldFields), no longer declares
--- (newFields), and that the new model itself declares (modelFields).
+-- WRONG (same-spec): returns the gold list REVERSED. Set-equal (List.mem_reverse),
+-- so the membership spec closes; the Python dependency list feeds a topological
+-- sort so order is inert.
 def removedFieldDeps (ba bn : String) (oldFields newFields modelFields : List String) : List Dep :=
   (oldFields.filter (fun f => !(newFields.contains f) && modelFields.contains f)).map
     (fun f => ⟨ba, bn, some f, false⟩)
 
--- The dependencies a single base contributes: nothing for a non-dotted base;
--- for a dotted base, the base-creation dependency followed by the field-removal
--- dependencies (only when both states of the base are known).
 def baseDeps (modelFields : List String)
     (fromLookup toLookup : String → String → Option (List String)) : Base → List Dep
   | Base.other => []
@@ -119,12 +116,10 @@
     deps := deps ++ baseDeps modelFields fromLookup toLookup base
   if let some (pa, pn) := primaryKeyRel then
     deps := deps ++ [⟨pa, pn, none, true⟩]
-  return deps
+  return deps.reverse
 -- impl-end
 
-
 -- proof-start
-/-- The explicit pure-list normal form of `implementation_createModelDeps`. -/
 def resultForm (appLabel modelName : String) (bases : List Base) (modelFields : List String)
     (fromLookup toLookup : String → String → Option (List String))
     (primaryKeyRel : Option (String × String)) : List Dep :=
@@ -133,16 +128,6 @@
     (match primaryKeyRel with
      | some (pa, pn) => [⟨pa, pn, none, true⟩]
      | none => [])
-
-theorem impl_eq_normalForm (appLabel modelName : String) (bases : List Base)
-    (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String))
-    (primaryKeyRel : Option (String × String)) :
-    implementation_createModelDeps appLabel modelName bases modelFields fromLookup toLookup
-        primaryKeyRel =
-      resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel := by
-  simp only [implementation_createModelDeps, resultForm, Id.run, bind, pure]
-  cases primaryKeyRel <;> simp [List.forIn_yield_eq_foldl]
 
 theorem removedFieldDeps_mem (ba bn : String) (oldFields newFields modelFields : List String)
     (d : Dep) :
@@ -244,6 +229,15 @@
     · exact Or.inr (Or.inl ⟨_, hbase, ba, bn, rfl, Or.inr ⟨fs, gs, hf, hg, f, hfs, hgs, hfm, rfl⟩⟩)
     · exact Or.inr (Or.inr (by rw [hpk]; simp))
 
+theorem impl_eq_normalForm (appLabel modelName : String) (bases : List Base)
+    (modelFields : List String)
+    (fromLookup toLookup : String → String → Option (List String))
+    (primaryKeyRel : Option (String × String)) :
+    implementation_createModelDeps appLabel modelName bases modelFields fromLookup toLookup
+        primaryKeyRel = (resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel).reverse := by
+  simp only [implementation_createModelDeps, resultForm, Id.run, bind, pure]
+  cases primaryKeyRel <;> simp [List.forIn_yield_eq_foldl]
+
 theorem correct_createModelDeps :
     ∀ (appLabel modelName : String) (bases : List Base) (modelFields : List String)
       (fromLookup toLookup : String → String → Option (List String))
@@ -254,6 +248,6 @@
   unfold problem_spec_createModelDeps
   rw [impl_eq_normalForm]
   intro d
+  rw [List.mem_reverse]
   exact spec_iff appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel d
-
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,16 +91,14 @@
 -- post-conditions-end
 
 -- impl-start
--- The field-removal dependencies a single dotted base contributes: one per
--- field the base previously declared (oldFields), no longer declares
--- (newFields), and that the new model itself declares (modelFields).
-def removedFieldDeps (ba bn : String) (oldFields newFields modelFields : List String) : List Dep :=
-  (oldFields.filter (fun f => !(newFields.contains f) && modelFields.contains f)).map
+-- WRONG (ungrounded over-emit): emits a removal dep for every field the base
+-- dropped, regardless of whether the new model declares it. Adds spurious
+-- ⟨ba,bn,some f,false⟩ with f ∉ modelFields, which the spec's reverse
+-- direction forbids, so correct_ cannot close.
+def removedFieldDeps (ba bn : String) (oldFields newFields _modelFields : List String) : List Dep :=
+  (oldFields.filter (fun f => !(newFields.contains f))).map
     (fun f => ⟨ba, bn, some f, false⟩)
 
--- The dependencies a single base contributes: nothing for a non-dotted base;
--- for a dotted base, the base-creation dependency followed by the field-removal
--- dependencies (only when both states of the base are known).
 def baseDeps (modelFields : List String)
     (fromLookup toLookup : String → String → Option (List String)) : Base → List Dep
   | Base.other => []
@@ -122,138 +120,15 @@
   return deps
 -- impl-end
 
-
 -- proof-start
-/-- The explicit pure-list normal form of `implementation_createModelDeps`. -/
-def resultForm (appLabel modelName : String) (bases : List Base) (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String))
-    (primaryKeyRel : Option (String × String)) : List Dep :=
-  [⟨appLabel, modelName, none, false⟩] ++
-    bases.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) [] ++
-    (match primaryKeyRel with
-     | some (pa, pn) => [⟨pa, pn, none, true⟩]
-     | none => [])
-
-theorem impl_eq_normalForm (appLabel modelName : String) (bases : List Base)
-    (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String))
-    (primaryKeyRel : Option (String × String)) :
-    implementation_createModelDeps appLabel modelName bases modelFields fromLookup toLookup
-        primaryKeyRel =
-      resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel := by
-  simp only [implementation_createModelDeps, resultForm, Id.run, bind, pure]
-  cases primaryKeyRel <;> simp [List.forIn_yield_eq_foldl]
-
-theorem removedFieldDeps_mem (ba bn : String) (oldFields newFields modelFields : List String)
-    (d : Dep) :
-    d ∈ removedFieldDeps ba bn oldFields newFields modelFields ↔
-      ∃ f, f ∈ oldFields ∧ ¬ newFields.contains f ∧ modelFields.contains f ∧
-        d = ⟨ba, bn, some f, false⟩ := by
-  simp only [removedFieldDeps, List.mem_map, List.mem_filter, Bool.and_eq_true,
-    Bool.not_eq_true']
-  constructor
-  · rintro ⟨f, ⟨hf, h1, h2⟩, rfl⟩
-    exact ⟨f, hf, by simpa using h1, h2, rfl⟩
-  · rintro ⟨f, hf, h1, h2, rfl⟩
-    exact ⟨f, ⟨hf, by simpa using h1, h2⟩, rfl⟩
-
-theorem baseDeps_mem (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String)) (base : Base) (d : Dep) :
-    d ∈ baseDeps modelFields fromLookup toLookup base ↔
-      (∃ ba bn, base = Base.dotted ba bn ∧
-        (d = ⟨ba, bn, none, true⟩ ∨
-         (∃ fs gs, fromLookup ba bn = some fs ∧ toLookup ba bn = some gs ∧
-            d ∈ removedFieldDeps ba bn fs gs modelFields))) := by
-  cases base with
-  | other => simp [baseDeps]
-  | dotted ba bn =>
-    simp only [baseDeps, List.mem_cons]
-    constructor
-    · rintro (h | h)
-      · exact ⟨ba, bn, rfl, Or.inl h⟩
-      · refine ⟨ba, bn, rfl, Or.inr ?_⟩
-        revert h
-        cases hf : fromLookup ba bn with
-        | none => simp
-        | some fs =>
-          cases hg : toLookup ba bn with
-          | none => simp
-          | some gs => intro h; exact ⟨fs, gs, rfl, rfl, h⟩
-    · rintro ⟨ba', bn', heq, hd⟩
-      cases heq
-      rcases hd with hd | ⟨fs, gs, hf, hg, hmem⟩
-      · exact Or.inl hd
-      · refine Or.inr ?_
-        rw [hf, hg]
-        exact hmem
-
-theorem baseFold_mem (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String)) (bases : List Base) (d : Dep) :
-    d ∈ bases.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) [] ↔
-      ∃ base, base ∈ bases ∧ d ∈ baseDeps modelFields fromLookup toLookup base := by
-  have general : ∀ (l : List Base) (init : List Dep),
-      d ∈ l.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) init ↔
-        d ∈ init ∨ ∃ base, base ∈ l ∧ d ∈ baseDeps modelFields fromLookup toLookup base := by
-    intro l
-    induction l with
-    | nil => intro init; simp
-    | cons b bs ih =>
-      intro init
-      rw [List.foldl_cons, ih (init ++ baseDeps modelFields fromLookup toLookup b)]
-      simp only [List.mem_append, List.mem_cons]
-      constructor
-      · rintro ((h | h) | ⟨base, hb, hd⟩)
-        · exact Or.inl h
-        · exact Or.inr ⟨b, Or.inl rfl, h⟩
-        · exact Or.inr ⟨base, Or.inr hb, hd⟩
-      · rintro (h | ⟨base, (rfl | hb), hd⟩)
-        · exact Or.inl (Or.inl h)
-        · exact Or.inl (Or.inr hd)
-        · exact Or.inr ⟨base, hb, hd⟩
-  simpa using general bases []
-
-theorem contains_iff_mem (l : List String) (f : String) :
-    l.contains f = true ↔ f ∈ l := by
-  simp
-
-theorem spec_iff (appLabel modelName : String) (bases : List Base) (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String))
-    (primaryKeyRel : Option (String × String)) (d : Dep) :
-    d ∈ resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel ↔
-      ((d = ⟨appLabel, modelName, none, false⟩) ∨
-       (∃ ba bn, Base.dotted ba bn ∈ bases ∧ d = ⟨ba, bn, none, true⟩) ∨
-       (∃ ba bn fs gs f, Base.dotted ba bn ∈ bases ∧
-          fromLookup ba bn = some fs ∧ toLookup ba bn = some gs ∧
-          f ∈ fs ∧ f ∉ gs ∧ f ∈ modelFields ∧
-          d = ⟨ba, bn, some f, false⟩) ∨
-       (∃ pa pn, primaryKeyRel = some (pa, pn) ∧ d = ⟨pa, pn, none, true⟩)) := by
-  unfold resultForm
-  simp only [List.append_assoc, List.mem_append, List.mem_singleton, baseFold_mem, baseDeps_mem,
-    removedFieldDeps_mem, contains_iff_mem]
-  constructor
-  · rintro (h | ⟨base, hbase, ba, bn, rfl, (h | ⟨fs, gs, hf, hg, f, hfs, hgs, hfm, rfl⟩)⟩ | h)
-    · exact Or.inl h
-    · exact Or.inr (Or.inl ⟨ba, bn, hbase, h⟩)
-    · exact Or.inr (Or.inr (Or.inl ⟨ba, bn, fs, gs, f, hbase, hf, hg, hfs, hgs, hfm, rfl⟩))
-    · rcases primaryKeyRel with _ | ⟨pa, pn⟩
-      · simp at h
-      · simp at h; exact Or.inr (Or.inr (Or.inr ⟨pa, pn, rfl, h⟩))
-  · rintro (h | ⟨ba, bn, hbase, rfl⟩ | ⟨ba, bn, fs, gs, f, hbase, hf, hg, hfs, hgs, hfm, rfl⟩ | ⟨pa, pn, hpk, rfl⟩)
-    · exact Or.inl h
-    · exact Or.inr (Or.inl ⟨_, hbase, ba, bn, rfl, Or.inl rfl⟩)
-    · exact Or.inr (Or.inl ⟨_, hbase, ba, bn, rfl, Or.inr ⟨fs, gs, hf, hg, f, hfs, hgs, hfm, rfl⟩⟩)
-    · exact Or.inr (Or.inr (by rw [hpk]; simp))
-
 theorem correct_createModelDeps :
     ∀ (appLabel modelName : String) (bases : List Base) (modelFields : List String)
       (fromLookup toLookup : String → String → Option (List String))
       (primaryKeyRel : Option (String × String)),
       problem_spec_createModelDeps appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel
         (implementation_createModelDeps appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel) := by
-  intro appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel
-  unfold problem_spec_createModelDeps
-  rw [impl_eq_normalForm]
-  intro d
-  exact spec_iff appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel d
-
+  intro appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel d
+  unfold problem_spec_createModelDeps implementation_createModelDeps
+  simp only [Id.run, bind, pure]
+  constructor <;> intro h <;> simp_all <;> aesop
 -- proof-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -91,16 +91,14 @@
 -- post-conditions-end
 
 -- impl-start
--- The field-removal dependencies a single dotted base contributes: one per
--- field the base previously declared (oldFields), no longer declares
--- (newFields), and that the new model itself declares (modelFields).
+-- WRONG (same-spec): appends a SECOND copy of the self proxy-removal dep.
+-- Already a member of gold, so the result is set-equal and the membership
+-- spec closes; the Python dependency list feeds a topological sort so the
+-- duplicate is inert.
 def removedFieldDeps (ba bn : String) (oldFields newFields modelFields : List String) : List Dep :=
   (oldFields.filter (fun f => !(newFields.contains f) && modelFields.contains f)).map
     (fun f => ⟨ba, bn, some f, false⟩)
 
--- The dependencies a single base contributes: nothing for a non-dotted base;
--- for a dotted base, the base-creation dependency followed by the field-removal
--- dependencies (only when both states of the base are known).
 def baseDeps (modelFields : List String)
     (fromLookup toLookup : String → String → Option (List String)) : Base → List Dep
   | Base.other => []
@@ -119,12 +117,10 @@
     deps := deps ++ baseDeps modelFields fromLookup toLookup base
   if let some (pa, pn) := primaryKeyRel then
     deps := deps ++ [⟨pa, pn, none, true⟩]
-  return deps
+  return deps ++ [⟨appLabel, modelName, none, false⟩]
 -- impl-end
 
-
 -- proof-start
-/-- The explicit pure-list normal form of `implementation_createModelDeps`. -/
 def resultForm (appLabel modelName : String) (bases : List Base) (modelFields : List String)
     (fromLookup toLookup : String → String → Option (List String))
     (primaryKeyRel : Option (String × String)) : List Dep :=
@@ -133,16 +129,6 @@
     (match primaryKeyRel with
      | some (pa, pn) => [⟨pa, pn, none, true⟩]
      | none => [])
-
-theorem impl_eq_normalForm (appLabel modelName : String) (bases : List Base)
-    (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String))
-    (primaryKeyRel : Option (String × String)) :
-    implementation_createModelDeps appLabel modelName bases modelFields fromLookup toLookup
-        primaryKeyRel =
-      resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel := by
-  simp only [implementation_createModelDeps, resultForm, Id.run, bind, pure]
-  cases primaryKeyRel <;> simp [List.forIn_yield_eq_foldl]
 
 theorem removedFieldDeps_mem (ba bn : String) (oldFields newFields modelFields : List String)
     (d : Dep) :
@@ -244,6 +230,15 @@
     · exact Or.inr (Or.inl ⟨_, hbase, ba, bn, rfl, Or.inr ⟨fs, gs, hf, hg, f, hfs, hgs, hfm, rfl⟩⟩)
     · exact Or.inr (Or.inr (by rw [hpk]; simp))
 
+theorem impl_eq_normalForm (appLabel modelName : String) (bases : List Base)
+    (modelFields : List String)
+    (fromLookup toLookup : String → String → Option (List String))
+    (primaryKeyRel : Option (String × String)) :
+    implementation_createModelDeps appLabel modelName bases modelFields fromLookup toLookup
+        primaryKeyRel = (resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel) ++ [⟨appLabel, modelName, none, false⟩] := by
+  simp only [implementation_createModelDeps, resultForm, Id.run, bind, pure]
+  cases primaryKeyRel <;> simp [List.forIn_yield_eq_foldl]
+
 theorem correct_createModelDeps :
     ∀ (appLabel modelName : String) (bases : List Base) (modelFields : List String)
       (fromLookup toLookup : String → String → Option (List String))
@@ -254,6 +249,10 @@
   unfold problem_spec_createModelDeps
   rw [impl_eq_normalForm]
   intro d
-  exact spec_iff appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel d
-
+  rw [List.mem_append, List.mem_singleton, spec_iff]
+  constructor
+  · rintro (h | rfl)
+    · exact h
+    · exact Or.inl rfl
+  · intro h; exact Or.inl h
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,24 +91,22 @@
 -- post-conditions-end
 
 -- impl-start
--- The field-removal dependencies a single dotted base contributes: one per
--- field the base previously declared (oldFields), no longer declares
--- (newFields), and that the new model itself declares (modelFields).
+-- WRONG (control-flow): drops the both-present guard — when toLookup is none
+-- it treats newFields as [], emitting removal deps that the spec (which
+-- requires toLookup ba bn = some gs) does not sanction. Reverse direction
+-- fails, so correct_ cannot close.
 def removedFieldDeps (ba bn : String) (oldFields newFields modelFields : List String) : List Dep :=
   (oldFields.filter (fun f => !(newFields.contains f) && modelFields.contains f)).map
     (fun f => ⟨ba, bn, some f, false⟩)
 
--- The dependencies a single base contributes: nothing for a non-dotted base;
--- for a dotted base, the base-creation dependency followed by the field-removal
--- dependencies (only when both states of the base are known).
 def baseDeps (modelFields : List String)
     (fromLookup toLookup : String → String → Option (List String)) : Base → List Dep
   | Base.other => []
   | Base.dotted ba bn =>
       ⟨ba, bn, none, true⟩ ::
-        (match fromLookup ba bn, toLookup ba bn with
-         | some oldFields, some newFields => removedFieldDeps ba bn oldFields newFields modelFields
-         | _, _ => [])
+        (match fromLookup ba bn with
+         | some oldFields => removedFieldDeps ba bn oldFields ((toLookup ba bn).getD []) modelFields
+         | none => [])
 
 def implementation_createModelDeps
     (appLabel modelName : String) (bases : List Base) (modelFields : List String)
@@ -122,138 +120,15 @@
   return deps
 -- impl-end
 
-
 -- proof-start
-/-- The explicit pure-list normal form of `implementation_createModelDeps`. -/
-def resultForm (appLabel modelName : String) (bases : List Base) (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String))
-    (primaryKeyRel : Option (String × String)) : List Dep :=
-  [⟨appLabel, modelName, none, false⟩] ++
-    bases.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) [] ++
-    (match primaryKeyRel with
-     | some (pa, pn) => [⟨pa, pn, none, true⟩]
-     | none => [])
-
-theorem impl_eq_normalForm (appLabel modelName : String) (bases : List Base)
-    (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String))
-    (primaryKeyRel : Option (String × String)) :
-    implementation_createModelDeps appLabel modelName bases modelFields fromLookup toLookup
-        primaryKeyRel =
-      resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel := by
-  simp only [implementation_createModelDeps, resultForm, Id.run, bind, pure]
-  cases primaryKeyRel <;> simp [List.forIn_yield_eq_foldl]
-
-theorem removedFieldDeps_mem (ba bn : String) (oldFields newFields modelFields : List String)
-    (d : Dep) :
-    d ∈ removedFieldDeps ba bn oldFields newFields modelFields ↔
-      ∃ f, f ∈ oldFields ∧ ¬ newFields.contains f ∧ modelFields.contains f ∧
-        d = ⟨ba, bn, some f, false⟩ := by
-  simp only [removedFieldDeps, List.mem_map, List.mem_filter, Bool.and_eq_true,
-    Bool.not_eq_true']
-  constructor
-  · rintro ⟨f, ⟨hf, h1, h2⟩, rfl⟩
-    exact ⟨f, hf, by simpa using h1, h2, rfl⟩
-  · rintro ⟨f, hf, h1, h2, rfl⟩
-    exact ⟨f, ⟨hf, by simpa using h1, h2⟩, rfl⟩
-
-theorem baseDeps_mem (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String)) (base : Base) (d : Dep) :
-    d ∈ baseDeps modelFields fromLookup toLookup base ↔
-      (∃ ba bn, base = Base.dotted ba bn ∧
-        (d = ⟨ba, bn, none, true⟩ ∨
-         (∃ fs gs, fromLookup ba bn = some fs ∧ toLookup ba bn = some gs ∧
-            d ∈ removedFieldDeps ba bn fs gs modelFields))) := by
-  cases base with
-  | other => simp [baseDeps]
-  | dotted ba bn =>
-    simp only [baseDeps, List.mem_cons]
-    constructor
-    · rintro (h | h)
-      · exact ⟨ba, bn, rfl, Or.inl h⟩
-      · refine ⟨ba, bn, rfl, Or.inr ?_⟩
-        revert h
-        cases hf : fromLookup ba bn with
-        | none => simp
-        | some fs =>
-          cases hg : toLookup ba bn with
-          | none => simp
-          | some gs => intro h; exact ⟨fs, gs, rfl, rfl, h⟩
-    · rintro ⟨ba', bn', heq, hd⟩
-      cases heq
-      rcases hd with hd | ⟨fs, gs, hf, hg, hmem⟩
-      · exact Or.inl hd
-      · refine Or.inr ?_
-        rw [hf, hg]
-        exact hmem
-
-theorem baseFold_mem (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String)) (bases : List Base) (d : Dep) :
-    d ∈ bases.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) [] ↔
-      ∃ base, base ∈ bases ∧ d ∈ baseDeps modelFields fromLookup toLookup base := by
-  have general : ∀ (l : List Base) (init : List Dep),
-      d ∈ l.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) init ↔
-        d ∈ init ∨ ∃ base, base ∈ l ∧ d ∈ baseDeps modelFields fromLookup toLookup base := by
-    intro l
-    induction l with
-    | nil => intro init; simp
-    | cons b bs ih =>
-      intro init
-      rw [List.foldl_cons, ih (init ++ baseDeps modelFields fromLookup toLookup b)]
-      simp only [List.mem_append, List.mem_cons]
-      constructor
-      · rintro ((h | h) | ⟨base, hb, hd⟩)
-        · exact Or.inl h
-        · exact Or.inr ⟨b, Or.inl rfl, h⟩
-        · exact Or.inr ⟨base, Or.inr hb, hd⟩
-      · rintro (h | ⟨base, (rfl | hb), hd⟩)
-        · exact Or.inl (Or.inl h)
-        · exact Or.inl (Or.inr hd)
-        · exact Or.inr ⟨base, hb, hd⟩
-  simpa using general bases []
-
-theorem contains_iff_mem (l : List String) (f : String) :
-    l.contains f = true ↔ f ∈ l := by
-  simp
-
-theorem spec_iff (appLabel modelName : String) (bases : List Base) (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String))
-    (primaryKeyRel : Option (String × String)) (d : Dep) :
-    d ∈ resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel ↔
-      ((d = ⟨appLabel, modelName, none, false⟩) ∨
-       (∃ ba bn, Base.dotted ba bn ∈ bases ∧ d = ⟨ba, bn, none, true⟩) ∨
-       (∃ ba bn fs gs f, Base.dotted ba bn ∈ bases ∧
-          fromLookup ba bn = some fs ∧ toLookup ba bn = some gs ∧
-          f ∈ fs ∧ f ∉ gs ∧ f ∈ modelFields ∧
-          d = ⟨ba, bn, some f, false⟩) ∨
-       (∃ pa pn, primaryKeyRel = some (pa, pn) ∧ d = ⟨pa, pn, none, true⟩)) := by
-  unfold resultForm
-  simp only [List.append_assoc, List.mem_append, List.mem_singleton, baseFold_mem, baseDeps_mem,
-    removedFieldDeps_mem, contains_iff_mem]
-  constructor
-  · rintro (h | ⟨base, hbase, ba, bn, rfl, (h | ⟨fs, gs, hf, hg, f, hfs, hgs, hfm, rfl⟩)⟩ | h)
-    · exact Or.inl h
-    · exact Or.inr (Or.inl ⟨ba, bn, hbase, h⟩)
-    · exact Or.inr (Or.inr (Or.inl ⟨ba, bn, fs, gs, f, hbase, hf, hg, hfs, hgs, hfm, rfl⟩))
-    · rcases primaryKeyRel with _ | ⟨pa, pn⟩
-      · simp at h
-      · simp at h; exact Or.inr (Or.inr (Or.inr ⟨pa, pn, rfl, h⟩))
-  · rintro (h | ⟨ba, bn, hbase, rfl⟩ | ⟨ba, bn, fs, gs, f, hbase, hf, hg, hfs, hgs, hfm, rfl⟩ | ⟨pa, pn, hpk, rfl⟩)
-    · exact Or.inl h
-    · exact Or.inr (Or.inl ⟨_, hbase, ba, bn, rfl, Or.inl rfl⟩)
-    · exact Or.inr (Or.inl ⟨_, hbase, ba, bn, rfl, Or.inr ⟨fs, gs, hf, hg, f, hfs, hgs, hfm, rfl⟩⟩)
-    · exact Or.inr (Or.inr (by rw [hpk]; simp))
-
 theorem correct_createModelDeps :
     ∀ (appLabel modelName : String) (bases : List Base) (modelFields : List String)
       (fromLookup toLookup : String → String → Option (List String))
       (primaryKeyRel : Option (String × String)),
       problem_spec_createModelDeps appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel
         (implementation_createModelDeps appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel) := by
-  intro appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel
-  unfold problem_spec_createModelDeps
-  rw [impl_eq_normalForm]
-  intro d
-  exact spec_iff appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel d
-
+  intro appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel d
+  unfold problem_spec_createModelDeps implementation_createModelDeps
+  simp only [Id.run, bind, pure]
+  constructor <;> intro h <;> simp_all <;> aesop
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,16 +91,13 @@
 -- post-conditions-end
 
 -- impl-start
--- The field-removal dependencies a single dotted base contributes: one per
--- field the base previously declared (oldFields), no longer declares
--- (newFields), and that the new model itself declares (modelFields).
+-- WRONG (control-flow): omits the primary-key relation dep entirely. When
+-- primaryKeyRel = some (pa,pn) the spec's 4th disjunct forces ⟨pa,pn,none,true⟩
+-- membership, which the impl never emits, so correct_ cannot close.
 def removedFieldDeps (ba bn : String) (oldFields newFields modelFields : List String) : List Dep :=
   (oldFields.filter (fun f => !(newFields.contains f) && modelFields.contains f)).map
     (fun f => ⟨ba, bn, some f, false⟩)
 
--- The dependencies a single base contributes: nothing for a non-dotted base;
--- for a dotted base, the base-creation dependency followed by the field-removal
--- dependencies (only when both states of the base are known).
 def baseDeps (modelFields : List String)
     (fromLookup toLookup : String → String → Option (List String)) : Base → List Dep
   | Base.other => []
@@ -113,147 +110,22 @@
 def implementation_createModelDeps
     (appLabel modelName : String) (bases : List Base) (modelFields : List String)
     (fromLookup toLookup : String → String → Option (List String))
-    (primaryKeyRel : Option (String × String)) : List Dep := Id.run do
+    (_primaryKeyRel : Option (String × String)) : List Dep := Id.run do
   let mut deps : List Dep := [⟨appLabel, modelName, none, false⟩]
   for base in bases do
     deps := deps ++ baseDeps modelFields fromLookup toLookup base
-  if let some (pa, pn) := primaryKeyRel then
-    deps := deps ++ [⟨pa, pn, none, true⟩]
   return deps
 -- impl-end
 
-
 -- proof-start
-/-- The explicit pure-list normal form of `implementation_createModelDeps`. -/
-def resultForm (appLabel modelName : String) (bases : List Base) (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String))
-    (primaryKeyRel : Option (String × String)) : List Dep :=
-  [⟨appLabel, modelName, none, false⟩] ++
-    bases.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) [] ++
-    (match primaryKeyRel with
-     | some (pa, pn) => [⟨pa, pn, none, true⟩]
-     | none => [])
-
-theorem impl_eq_normalForm (appLabel modelName : String) (bases : List Base)
-    (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String))
-    (primaryKeyRel : Option (String × String)) :
-    implementation_createModelDeps appLabel modelName bases modelFields fromLookup toLookup
-        primaryKeyRel =
-      resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel := by
-  simp only [implementation_createModelDeps, resultForm, Id.run, bind, pure]
-  cases primaryKeyRel <;> simp [List.forIn_yield_eq_foldl]
-
-theorem removedFieldDeps_mem (ba bn : String) (oldFields newFields modelFields : List String)
-    (d : Dep) :
-    d ∈ removedFieldDeps ba bn oldFields newFields modelFields ↔
-      ∃ f, f ∈ oldFields ∧ ¬ newFields.contains f ∧ modelFields.contains f ∧
-        d = ⟨ba, bn, some f, false⟩ := by
-  simp only [removedFieldDeps, List.mem_map, List.mem_filter, Bool.and_eq_true,
-    Bool.not_eq_true']
-  constructor
-  · rintro ⟨f, ⟨hf, h1, h2⟩, rfl⟩
-    exact ⟨f, hf, by simpa using h1, h2, rfl⟩
-  · rintro ⟨f, hf, h1, h2, rfl⟩
-    exact ⟨f, ⟨hf, by simpa using h1, h2⟩, rfl⟩
-
-theorem baseDeps_mem (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String)) (base : Base) (d : Dep) :
-    d ∈ baseDeps modelFields fromLookup toLookup base ↔
-      (∃ ba bn, base = Base.dotted ba bn ∧
-        (d = ⟨ba, bn, none, true⟩ ∨
-         (∃ fs gs, fromLookup ba bn = some fs ∧ toLookup ba bn = some gs ∧
-            d ∈ removedFieldDeps ba bn fs gs modelFields))) := by
-  cases base with
-  | other => simp [baseDeps]
-  | dotted ba bn =>
-    simp only [baseDeps, List.mem_cons]
-    constructor
-    · rintro (h | h)
-      · exact ⟨ba, bn, rfl, Or.inl h⟩
-      · refine ⟨ba, bn, rfl, Or.inr ?_⟩
-        revert h
-        cases hf : fromLookup ba bn with
-        | none => simp
-        | some fs =>
-          cases hg : toLookup ba bn with
-          | none => simp
-          | some gs => intro h; exact ⟨fs, gs, rfl, rfl, h⟩
-    · rintro ⟨ba', bn', heq, hd⟩
-      cases heq
-      rcases hd with hd | ⟨fs, gs, hf, hg, hmem⟩
-      · exact Or.inl hd
-      · refine Or.inr ?_
-        rw [hf, hg]
-        exact hmem
-
-theorem baseFold_mem (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String)) (bases : List Base) (d : Dep) :
-    d ∈ bases.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) [] ↔
-      ∃ base, base ∈ bases ∧ d ∈ baseDeps modelFields fromLookup toLookup base := by
-  have general : ∀ (l : List Base) (init : List Dep),
-      d ∈ l.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) init ↔
-        d ∈ init ∨ ∃ base, base ∈ l ∧ d ∈ baseDeps modelFields fromLookup toLookup base := by
-    intro l
-    induction l with
-    | nil => intro init; simp
-    | cons b bs ih =>
-      intro init
-      rw [List.foldl_cons, ih (init ++ baseDeps modelFields fromLookup toLookup b)]
-      simp only [List.mem_append, List.mem_cons]
-      constructor
-      · rintro ((h | h) | ⟨base, hb, hd⟩)
-        · exact Or.inl h
-        · exact Or.inr ⟨b, Or.inl rfl, h⟩
-        · exact Or.inr ⟨base, Or.inr hb, hd⟩
-      · rintro (h | ⟨base, (rfl | hb), hd⟩)
-        · exact Or.inl (Or.inl h)
-        · exact Or.inl (Or.inr hd)
-        · exact Or.inr ⟨base, hb, hd⟩
-  simpa using general bases []
-
-theorem contains_iff_mem (l : List String) (f : String) :
-    l.contains f = true ↔ f ∈ l := by
-  simp
-
-theorem spec_iff (appLabel modelName : String) (bases : List Base) (modelFields : List String)
-    (fromLookup toLookup : String → String → Option (List String))
-    (primaryKeyRel : Option (String × String)) (d : Dep) :
-    d ∈ resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel ↔
-      ((d = ⟨appLabel, modelName, none, false⟩) ∨
-       (∃ ba bn, Base.dotted ba bn ∈ bases ∧ d = ⟨ba, bn, none, true⟩) ∨
-       (∃ ba bn fs gs f, Base.dotted ba bn ∈ bases ∧
-          fromLookup ba bn = some fs ∧ toLookup ba bn = some gs ∧
-          f ∈ fs ∧ f ∉ gs ∧ f ∈ modelFields ∧
-          d = ⟨ba, bn, some f, false⟩) ∨
-       (∃ pa pn, primaryKeyRel = some (pa, pn) ∧ d = ⟨pa, pn, none, true⟩)) := by
-  unfold resultForm
-  simp only [List.append_assoc, List.mem_append, List.mem_singleton, baseFold_mem, baseDeps_mem,
-    removedFieldDeps_mem, contains_iff_mem]
-  constructor
-  · rintro (h | ⟨base, hbase, ba, bn, rfl, (h | ⟨fs, gs, hf, hg, f, hfs, hgs, hfm, rfl⟩)⟩ | h)
-    · exact Or.inl h
-    · exact Or.inr (Or.inl ⟨ba, bn, hbase, h⟩)
-    · exact Or.inr (Or.inr (Or.inl ⟨ba, bn, fs, gs, f, hbase, hf, hg, hfs, hgs, hfm, rfl⟩))
-    · rcases primaryKeyRel with _ | ⟨pa, pn⟩
-      · simp at h
-      · simp at h; exact Or.inr (Or.inr (Or.inr ⟨pa, pn, rfl, h⟩))
-  · rintro (h | ⟨ba, bn, hbase, rfl⟩ | ⟨ba, bn, fs, gs, f, hbase, hf, hg, hfs, hgs, hfm, rfl⟩ | ⟨pa, pn, hpk, rfl⟩)
-    · exact Or.inl h
-    · exact Or.inr (Or.inl ⟨_, hbase, ba, bn, rfl, Or.inl rfl⟩)
-    · exact Or.inr (Or.inl ⟨_, hbase, ba, bn, rfl, Or.inr ⟨fs, gs, hf, hg, f, hfs, hgs, hfm, rfl⟩⟩)
-    · exact Or.inr (Or.inr (by rw [hpk]; simp))
-
 theorem correct_createModelDeps :
     ∀ (appLabel modelName : String) (bases : List Base) (modelFields : List String)
       (fromLookup toLookup : String → String → Option (List String))
       (primaryKeyRel : Option (String × String)),
       problem_spec_createModelDeps appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel
         (implementation_createModelDeps appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel) := by
-  intro appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel
-  unfold problem_spec_createModelDeps
-  rw [impl_eq_normalForm]
-  intro d
-  exact spec_iff appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel d
-
+  intro appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel d
+  unfold problem_spec_createModelDeps implementation_createModelDeps
+  simp only [Id.run, bind, pure]
+  constructor <;> intro h <;> simp_all <;> aesop
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Computing the ordering dependencies emitted when a brand-new model is created
during automatic migration detection.

When a new model is added, the detector records, alongside the create step, a
list of *ordering dependencies* — tuples saying "this create step must come
after some other step". Each dependency names a target by an application label,
a model name, an optional field name, and a boolean flag selecting whether it
waits on the *creation* (`true`) of the target or on its *removal* (`false`).

For one newly-created model the dependency list is built from:

  * a self-dependency on the removal of any prior proxy of the same model
    (the application label and model name of the new model, no field, flag
    `false`);
  * for every base the new model inherits from that is given as a dotted
    "label.name" reference: a dependency on the creation of that base
    (no field, flag `true`); and — crucially — when both the previous and the
    current recorded state of that base are known, a dependency on the
    *removal* of every field that the base used to declare, no longer declares,
    and that the new model itself now declares (flag `false`). This last group
    forces a field that has moved from a base onto the new subclass to be
    removed from the base before the subclass is created.
  * a dependency on the creation of the far end of a primary-key relation,
    when one is present (no field, flag `true`).

This file pins exactly which dependency tuples that list must contain.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Splitting a
-- dotted reference, the set difference / intersection over field-name
-- collections, and the membership tests are all modeled directly over `List`
-- and `Option`, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- An ordering dependency tuple: it names a target by application label and
model name, optionally a field of that target, and a flag selecting whether the
step waits on the target's creation (`true`) or its removal (`false`). -/
structure Dep where
  appLabel : String
  name : String
  field : Option String
  onCreate : Bool
deriving DecidableEq, Repr

/-- A base a model inherits from, as the dependency builder sees it: either a
dotted reference already separated into an application label and a model name,
or anything else (a non-dotted or non-string base), which contributes nothing. -/
inductive Base where
  | dotted (appLabel name : String) : Base
  | other : Base
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- `result` is the dependency list emitted for the new model `appLabel.modelName`
with the given `bases`, own field names `modelFields`, previous-state and
current-state field lookups for bases (`fromLookup` / `toLookup`), and optional
primary-key relation target `primaryKeyRel`.

The list must contain EXACTLY the following tuples (membership characterised in
both directions, so no required dependency is missing and no spurious one is
present):

  * the self proxy-removal dependency `⟨appLabel, modelName, none, false⟩`;
  * for every dotted base `ba.bn`, the base-creation dependency
    `⟨ba, bn, none, true⟩`;
  * for every dotted base `ba.bn` whose previous and current states are both
    known, and every field `f` declared by the base's previous state, absent
    from its current state, and declared by the new model, the field-removal
    dependency `⟨ba, bn, some f, false⟩`;
  * when a primary-key relation target `pa.pn` is present, the dependency
    `⟨pa, pn, none, true⟩`. -/
def problem_spec_createModelDeps
    (appLabel modelName : String) (bases : List Base) (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String))
    (primaryKeyRel : Option (String × String)) (result : List Dep) : Prop :=
  ∀ d : Dep, d ∈ result ↔
    (d = ⟨appLabel, modelName, none, false⟩) ∨
    (∃ ba bn, Base.dotted ba bn ∈ bases ∧ d = ⟨ba, bn, none, true⟩) ∨
    (∃ ba bn fs gs f, Base.dotted ba bn ∈ bases ∧
       fromLookup ba bn = some fs ∧ toLookup ba bn = some gs ∧
       f ∈ fs ∧ f ∉ gs ∧ f ∈ modelFields ∧
       d = ⟨ba, bn, some f, false⟩) ∨
    (∃ pa pn, primaryKeyRel = some (pa, pn) ∧ d = ⟨pa, pn, none, true⟩)
-- post-conditions-end

-- impl-start
-- The field-removal dependencies a single dotted base contributes: one per
-- field the base previously declared (oldFields), no longer declares
-- (newFields), and that the new model itself declares (modelFields).
def removedFieldDeps (ba bn : String) (oldFields newFields modelFields : List String) : List Dep :=
  (oldFields.filter (fun f => !(newFields.contains f) && modelFields.contains f)).map
    (fun f => ⟨ba, bn, some f, false⟩)

-- The dependencies a single base contributes: nothing for a non-dotted base;
-- for a dotted base, the base-creation dependency followed by the field-removal
-- dependencies (only when both states of the base are known).
def baseDeps (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String)) : Base → List Dep
  | Base.other => []
  | Base.dotted ba bn =>
      ⟨ba, bn, none, true⟩ ::
        (match fromLookup ba bn, toLookup ba bn with
         | some oldFields, some newFields => removedFieldDeps ba bn oldFields newFields modelFields
         | _, _ => [])

def implementation_createModelDeps
    (appLabel modelName : String) (bases : List Base) (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String))
    (primaryKeyRel : Option (String × String)) : List Dep := Id.run do
  let mut deps : List Dep := [⟨appLabel, modelName, none, false⟩]
  for base in bases do
    deps := deps ++ baseDeps modelFields fromLookup toLookup base
  if let some (pa, pn) := primaryKeyRel then
    deps := deps ++ [⟨pa, pn, none, true⟩]
  return deps
-- impl-end


-- proof-start
/-- The explicit pure-list normal form of `implementation_createModelDeps`. -/
def resultForm (appLabel modelName : String) (bases : List Base) (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String))
    (primaryKeyRel : Option (String × String)) : List Dep :=
  [⟨appLabel, modelName, none, false⟩] ++
    bases.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) [] ++
    (match primaryKeyRel with
     | some (pa, pn) => [⟨pa, pn, none, true⟩]
     | none => [])

theorem impl_eq_normalForm (appLabel modelName : String) (bases : List Base)
    (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String))
    (primaryKeyRel : Option (String × String)) :
    implementation_createModelDeps appLabel modelName bases modelFields fromLookup toLookup
        primaryKeyRel =
      resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel := by
  simp only [implementation_createModelDeps, resultForm, Id.run, bind, pure]
  cases primaryKeyRel <;> simp [List.forIn_yield_eq_foldl]

theorem removedFieldDeps_mem (ba bn : String) (oldFields newFields modelFields : List String)
    (d : Dep) :
    d ∈ removedFieldDeps ba bn oldFields newFields modelFields ↔
      ∃ f, f ∈ oldFields ∧ ¬ newFields.contains f ∧ modelFields.contains f ∧
        d = ⟨ba, bn, some f, false⟩ := by
  simp only [removedFieldDeps, List.mem_map, List.mem_filter, Bool.and_eq_true,
    Bool.not_eq_true']
  constructor
  · rintro ⟨f, ⟨hf, h1, h2⟩, rfl⟩
    exact ⟨f, hf, by simpa using h1, h2, rfl⟩
  · rintro ⟨f, hf, h1, h2, rfl⟩
    exact ⟨f, ⟨hf, by simpa using h1, h2⟩, rfl⟩

theorem baseDeps_mem (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String)) (base : Base) (d : Dep) :
    d ∈ baseDeps modelFields fromLookup toLookup base ↔
      (∃ ba bn, base = Base.dotted ba bn ∧
        (d = ⟨ba, bn, none, true⟩ ∨
         (∃ fs gs, fromLookup ba bn = some fs ∧ toLookup ba bn = some gs ∧
            d ∈ removedFieldDeps ba bn fs gs modelFields))) := by
  cases base with
  | other => simp [baseDeps]
  | dotted ba bn =>
    simp only [baseDeps, List.mem_cons]
    constructor
    · rintro (h | h)
      · exact ⟨ba, bn, rfl, Or.inl h⟩
      · refine ⟨ba, bn, rfl, Or.inr ?_⟩
        revert h
        cases hf : fromLookup ba bn with
        | none => simp
        | some fs =>
          cases hg : toLookup ba bn with
          | none => simp
          | some gs => intro h; exact ⟨fs, gs, rfl, rfl, h⟩
    · rintro ⟨ba', bn', heq, hd⟩
      cases heq
      rcases hd with hd | ⟨fs, gs, hf, hg, hmem⟩
      · exact Or.inl hd
      · refine Or.inr ?_
        rw [hf, hg]
        exact hmem

theorem baseFold_mem (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String)) (bases : List Base) (d : Dep) :
    d ∈ bases.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) [] ↔
      ∃ base, base ∈ bases ∧ d ∈ baseDeps modelFields fromLookup toLookup base := by
  have general : ∀ (l : List Base) (init : List Dep),
      d ∈ l.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) init ↔
        d ∈ init ∨ ∃ base, base ∈ l ∧ d ∈ baseDeps modelFields fromLookup toLookup base := by
    intro l
    induction l with
    | nil => intro init; simp
    | cons b bs ih =>
      intro init
      rw [List.foldl_cons, ih (init ++ baseDeps modelFields fromLookup toLookup b)]
      simp only [List.mem_append, List.mem_cons]
      constructor
      · rintro ((h | h) | ⟨base, hb, hd⟩)
        · exact Or.inl h
        · exact Or.inr ⟨b, Or.inl rfl, h⟩
        · exact Or.inr ⟨base, Or.inr hb, hd⟩
      · rintro (h | ⟨base, (rfl | hb), hd⟩)
        · exact Or.inl (Or.inl h)
        · exact Or.inl (Or.inr hd)
        · exact Or.inr ⟨base, hb, hd⟩
  simpa using general bases []

theorem contains_iff_mem (l : List String) (f : String) :
    l.contains f = true ↔ f ∈ l := by
  simp

theorem spec_iff (appLabel modelName : String) (bases : List Base) (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String))
    (primaryKeyRel : Option (String × String)) (d : Dep) :
    d ∈ resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel ↔
      ((d = ⟨appLabel, modelName, none, false⟩) ∨
       (∃ ba bn, Base.dotted ba bn ∈ bases ∧ d = ⟨ba, bn, none, true⟩) ∨
       (∃ ba bn fs gs f, Base.dotted ba bn ∈ bases ∧
          fromLookup ba bn = some fs ∧ toLookup ba bn = some gs ∧
          f ∈ fs ∧ f ∉ gs ∧ f ∈ modelFields ∧
          d = ⟨ba, bn, some f, false⟩) ∨
       (∃ pa pn, primaryKeyRel = some (pa, pn) ∧ d = ⟨pa, pn, none, true⟩)) := by
  unfold resultForm
  simp only [List.append_assoc, List.mem_append, List.mem_singleton, baseFold_mem, baseDeps_mem,
    removedFieldDeps_mem, contains_iff_mem]
  constructor
  · rintro (h | ⟨base, hbase, ba, bn, rfl, (h | ⟨fs, gs, hf, hg, f, hfs, hgs, hfm, rfl⟩)⟩ | h)
    · exact Or.inl h
    · exact Or.inr (Or.inl ⟨ba, bn, hbase, h⟩)
    · exact Or.inr (Or.inr (Or.inl ⟨ba, bn, fs, gs, f, hbase, hf, hg, hfs, hgs, hfm, rfl⟩))
    · rcases primaryKeyRel with _ | ⟨pa, pn⟩
      · simp at h
      · simp at h; exact Or.inr (Or.inr (Or.inr ⟨pa, pn, rfl, h⟩))
  · rintro (h | ⟨ba, bn, hbase, rfl⟩ | ⟨ba, bn, fs, gs, f, hbase, hf, hg, hfs, hgs, hfm, rfl⟩ | ⟨pa, pn, hpk, rfl⟩)
    · exact Or.inl h
    · exact Or.inr (Or.inl ⟨_, hbase, ba, bn, rfl, Or.inl rfl⟩)
    · exact Or.inr (Or.inl ⟨_, hbase, ba, bn, rfl, Or.inr ⟨fs, gs, hf, hg, f, hfs, hgs, hfm, rfl⟩⟩)
    · exact Or.inr (Or.inr (by rw [hpk]; simp))

theorem correct_createModelDeps :
    ∀ (appLabel modelName : String) (bases : List Base) (modelFields : List String)
      (fromLookup toLookup : String → String → Option (List String))
      (primaryKeyRel : Option (String × String)),
      problem_spec_createModelDeps appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel
        (implementation_createModelDeps appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel) := by
  intro appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel
  unfold problem_spec_createModelDeps
  rw [impl_eq_normalForm]
  intro d
  exact spec_iff appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel d

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

DEEP-MODEL BUNDLE (no axioms). axiom_check.py is a skip stub; grep confirms NO axiom/opaque in Solution.lean. The single modeled callee (per-created-model dependency list in MigrationAutodetector.generate_created_models, autodetector.py:558-573 @ base 18759b22) is modeled entirely over List/Option/String. So the A-leg audit is: (a) confirm no axiom is smuggled in -> confirmed (grep + #print axioms = [propext, Quot.sound]); (b) deep-model<->real-callee correspondence -> holds (see refinement.md audit below). G-CONF (conformance_check.py, SEED=12754) covers the R/I legs.

SPEC SHAPE: problem_spec_createModelDeps is a COMPLETE bidirectional membership iff (∀ d, d ∈ result ↔ <4 disjuncts>). Any proof-closing impl must produce a list whose MEMBER SET equals the gold set; order and multiplicity are free. This is faithful because the Python `dependencies` list feeds a topological sort (check_dependency / add_operation), where order and duplicates are behaviorally inert. Confirmed empirically below.

### ATTACK RESULTS (verify via scripts/lean_verify.sh <file>; same_spec=True for ALL 8):
- atk_1 PREPATCH (drops removedFieldDeps): lean_verify EXIT=1 (does NOT close) -> spec tight, forces gold fix. prepatch_reproduced=true.
- atk_2 EMPTY impl `[]`: EXIT=1 (misses self dep) -> tight.
- atk_3 DUPLICATE all deps (`return deps ++ deps`): EXIT=0, #print axioms=[propext,Quot.sound] CLEAN. Set-equal -> CLOSES. Faithful patch materialized (patch_3.diff, applies clean vs base, python parses). run_resolve => {"resolved": true, "completed": true} RESOLVED.
- atk_4 REVERSE (`deps.reverse`): EXIT=0, clean axioms. CLOSES. patch_4.diff run_resolve => RESOLVED.
- atk_5 OVER-EMIT (removal dep for every dropped base field, ignoring f ∈ modelFields): EXIT=1 (reverse direction forbids spurious ⟨ba,bn,some f,false⟩ with f∉modelFields) -> tight.
- atk_6 SELF-DEP DUPLICATED (`deps ++ [⟨appLabel,modelName,none,false⟩]`): EXIT=0, clean axioms. CLOSES. patch_6.diff run_resolve => RESOLVED.
- atk_7 CONTROL-FLOW drop both-present guard (emit removals when toLookup=none, treating newFields=[]): EXIT=1 (reverse direction requires toLookup ba bn = some gs) -> tight.
- atk_8 CONTROL-FLOW drop primary-key dep: EXIT=1 (4th disjunct forces ⟨pa,pn,none,true⟩ when primaryKeyRel=some) -> tight.

COMMANDS: verify: `bash scripts/lean_verify.sh atk_N.lean`. axioms: appended `#print axioms correct_createModelDeps` -> [propext, Quot.sound] for atk_3/4/6 and positive_control. resolve: harness.run_resolve('django__django-12754', patch, timeout=1800) under SBU_BENCHMARK=swe_bench_verified. GOLD positive-control resolve => RESOLVED (manual run_evaluation ✓=1 and run_resolve resolved:true), confirming the harness+image are functional for this instance.

REFINEMENT.MD AUDIT: 8 legs, rows 1/2/7 = I (identical seed/iteration/per-field tuple), rows 3/4/5/6/8 = R (Base.other<->str+"." discriminator; split(".",1); both-present Option guard<->truthy ModelState; set diff∩intersect<->List.filter; primary_key_rel truthiness<->Option). NO A-consumed and NO A-reference rows -> consistent with the skip-stub axiom_check and grep. No kind-3 legs. A-leg correspondence audit is vacuous (no axioms) and correct.

CONCLUSION: All ≥5 attacks executed; 3 closing clean-axiom attacks each have a materialized faithful patch that RESOLVES; the 5 behaviorally-distinct wrong impls (prepatch, empty, over-emit, guard-drop, pk-drop) all fail to close. The membership spec's equivalence class is exactly the set-equal-to-gold family, which is behaviorally correct (topo-sort consumer). No verify⇏⇒correct break found. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_3.lean`, `atk_4.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. Every attack whose proof CLOSED with clean axioms (atk_3 duplicate-all, atk_4 reverse, atk_6 self-dep-duplicated) is set-equal to the gold dependency list; each materialized faithful patch RESOLVED under the official harness (gold positive-control also resolved). No verify⇏⇒correct break.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Computing the ordering dependencies emitted when a brand-new model is created
during automatic migration detection.

When a new model is added, the detector records, alongside the create step, a
list of *ordering dependencies* — tuples saying "this create step must come
after some other step". Each dependency names a target by an application label,
a model name, an optional field name, and a boolean flag selecting whether it
waits on the *creation* (`true`) of the target or on its *removal* (`false`).

For one newly-created model the dependency list is built from:

  * a self-dependency on the removal of any prior proxy of the same model
    (the application label and model name of the new model, no field, flag
    `false`);
  * for every base the new model inherits from that is given as a dotted
    "label.name" reference: a dependency on the creation of that base
    (no field, flag `true`); and — crucially — when both the previous and the
    current recorded state of that base are known, a dependency on the
    *removal* of every field that the base used to declare, no longer declares,
    and that the new model itself now declares (flag `false`). This last group
    forces a field that has moved from a base onto the new subclass to be
    removed from the base before the subclass is created.
  * a dependency on the creation of the far end of a primary-key relation,
    when one is present (no field, flag `true`).

This file pins exactly which dependency tuples that list must contain.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Splitting a
-- dotted reference, the set difference / intersection over field-name
-- collections, and the membership tests are all modeled directly over `List`
-- and `Option`, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- An ordering dependency tuple: it names a target by application label and
model name, optionally a field of that target, and a flag selecting whether the
step waits on the target's creation (`true`) or its removal (`false`). -/
structure Dep where
  appLabel : String
  name : String
  field : Option String
  onCreate : Bool
deriving DecidableEq, Repr

/-- A base a model inherits from, as the dependency builder sees it: either a
dotted reference already separated into an application label and a model name,
or anything else (a non-dotted or non-string base), which contributes nothing. -/
inductive Base where
  | dotted (appLabel name : String) : Base
  | other : Base
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- `result` is the dependency list emitted for the new model `appLabel.modelName`
with the given `bases`, own field names `modelFields`, previous-state and
current-state field lookups for bases (`fromLookup` / `toLookup`), and optional
primary-key relation target `primaryKeyRel`.

The list must contain EXACTLY the following tuples (membership characterised in
both directions, so no required dependency is missing and no spurious one is
present):

  * the self proxy-removal dependency `⟨appLabel, modelName, none, false⟩`;
  * for every dotted base `ba.bn`, the base-creation dependency
    `⟨ba, bn, none, true⟩`;
  * for every dotted base `ba.bn` whose previous and current states are both
    known, and every field `f` declared by the base's previous state, absent
    from its current state, and declared by the new model, the field-removal
    dependency `⟨ba, bn, some f, false⟩`;
  * when a primary-key relation target `pa.pn` is present, the dependency
    `⟨pa, pn, none, true⟩`. -/
def problem_spec_createModelDeps
    (appLabel modelName : String) (bases : List Base) (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String))
    (primaryKeyRel : Option (String × String)) (result : List Dep) : Prop :=
  ∀ d : Dep, d ∈ result ↔
    (d = ⟨appLabel, modelName, none, false⟩) ∨
    (∃ ba bn, Base.dotted ba bn ∈ bases ∧ d = ⟨ba, bn, none, true⟩) ∨
    (∃ ba bn fs gs f, Base.dotted ba bn ∈ bases ∧
       fromLookup ba bn = some fs ∧ toLookup ba bn = some gs ∧
       f ∈ fs ∧ f ∉ gs ∧ f ∈ modelFields ∧
       d = ⟨ba, bn, some f, false⟩) ∨
    (∃ pa pn, primaryKeyRel = some (pa, pn) ∧ d = ⟨pa, pn, none, true⟩)
-- post-conditions-end

-- impl-start
-- The field-removal dependencies a single dotted base contributes: one per
-- field the base previously declared (oldFields), no longer declares
-- (newFields), and that the new model itself declares (modelFields).
def removedFieldDeps (ba bn : String) (oldFields newFields modelFields : List String) : List Dep :=
  (oldFields.filter (fun f => !(newFields.contains f) && modelFields.contains f)).map
    (fun f => ⟨ba, bn, some f, false⟩)

-- The dependencies a single base contributes: nothing for a non-dotted base;
-- for a dotted base, the base-creation dependency followed by the field-removal
-- dependencies (only when both states of the base are known).
def baseDeps (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String)) : Base → List Dep
  | Base.other => []
  | Base.dotted ba bn =>
      ⟨ba, bn, none, true⟩ ::
        (match fromLookup ba bn, toLookup ba bn with
         | some oldFields, some newFields => removedFieldDeps ba bn oldFields newFields modelFields
         | _, _ => [])

def implementation_createModelDeps
    (appLabel modelName : String) (bases : List Base) (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String))
    (primaryKeyRel : Option (String × String)) : List Dep := Id.run do
  let mut deps : List Dep := [⟨appLabel, modelName, none, false⟩]
  for base in bases do
    deps := deps ++ baseDeps modelFields fromLookup toLookup base
  if let some (pa, pn) := primaryKeyRel then
    deps := deps ++ [⟨pa, pn, none, true⟩]
  return deps
-- impl-end


-- proof-start
/-- The explicit pure-list normal form of `implementation_createModelDeps`. -/
def resultForm (appLabel modelName : String) (bases : List Base) (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String))
    (primaryKeyRel : Option (String × String)) : List Dep :=
  [⟨appLabel, modelName, none, false⟩] ++
    bases.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) [] ++
    (match primaryKeyRel with
     | some (pa, pn) => [⟨pa, pn, none, true⟩]
     | none => [])

theorem impl_eq_normalForm (appLabel modelName : String) (bases : List Base)
    (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String))
    (primaryKeyRel : Option (String × String)) :
    implementation_createModelDeps appLabel modelName bases modelFields fromLookup toLookup
        primaryKeyRel =
      resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel := by
  simp only [implementation_createModelDeps, resultForm, Id.run, bind, pure]
  cases primaryKeyRel <;> simp [List.forIn_yield_eq_foldl]

theorem removedFieldDeps_mem (ba bn : String) (oldFields newFields modelFields : List String)
    (d : Dep) :
    d ∈ removedFieldDeps ba bn oldFields newFields modelFields ↔
      ∃ f, f ∈ oldFields ∧ ¬ newFields.contains f ∧ modelFields.contains f ∧
        d = ⟨ba, bn, some f, false⟩ := by
  simp only [removedFieldDeps, List.mem_map, List.mem_filter, Bool.and_eq_true,
    Bool.not_eq_true']
  constructor
  · rintro ⟨f, ⟨hf, h1, h2⟩, rfl⟩
    exact ⟨f, hf, by simpa using h1, h2, rfl⟩
  · rintro ⟨f, hf, h1, h2, rfl⟩
    exact ⟨f, ⟨hf, by simpa using h1, h2⟩, rfl⟩

theorem baseDeps_mem (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String)) (base : Base) (d : Dep) :
    d ∈ baseDeps modelFields fromLookup toLookup base ↔
      (∃ ba bn, base = Base.dotted ba bn ∧
        (d = ⟨ba, bn, none, true⟩ ∨
         (∃ fs gs, fromLookup ba bn = some fs ∧ toLookup ba bn = some gs ∧
            d ∈ removedFieldDeps ba bn fs gs modelFields))) := by
  cases base with
  | other => simp [baseDeps]
  | dotted ba bn =>
    simp only [baseDeps, List.mem_cons]
    constructor
    · rintro (h | h)
      · exact ⟨ba, bn, rfl, Or.inl h⟩
      · refine ⟨ba, bn, rfl, Or.inr ?_⟩
        revert h
        cases hf : fromLookup ba bn with
        | none => simp
        | some fs =>
          cases hg : toLookup ba bn with
          | none => simp
          | some gs => intro h; exact ⟨fs, gs, rfl, rfl, h⟩
    · rintro ⟨ba', bn', heq, hd⟩
      cases heq
      rcases hd with hd | ⟨fs, gs, hf, hg, hmem⟩
      · exact Or.inl hd
      · refine Or.inr ?_
        rw [hf, hg]
        exact hmem

theorem baseFold_mem (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String)) (bases : List Base) (d : Dep) :
    d ∈ bases.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) [] ↔
      ∃ base, base ∈ bases ∧ d ∈ baseDeps modelFields fromLookup toLookup base := by
  have general : ∀ (l : List Base) (init : List Dep),
      d ∈ l.foldl (fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) init ↔
        d ∈ init ∨ ∃ base, base ∈ l ∧ d ∈ baseDeps modelFields fromLookup toLookup base := by
    intro l
    induction l with
    | nil => intro init; simp
    | cons b bs ih =>
      intro init
      rw [List.foldl_cons, ih (init ++ baseDeps modelFields fromLookup toLookup b)]
      simp only [List.mem_append, List.mem_cons]
      constructor
      · rintro ((h | h) | ⟨base, hb, hd⟩)
        · exact Or.inl h
        · exact Or.inr ⟨b, Or.inl rfl, h⟩
        · exact Or.inr ⟨base, Or.inr hb, hd⟩
      · rintro (h | ⟨base, (rfl | hb), hd⟩)
        · exact Or.inl (Or.inl h)
        · exact Or.inl (Or.inr hd)
        · exact Or.inr ⟨base, hb, hd⟩
  simpa using general bases []

theorem contains_iff_mem (l : List String) (f : String) :
    l.contains f = true ↔ f ∈ l := by
  simp

theorem spec_iff (appLabel modelName : String) (bases : List Base) (modelFields : List String)
    (fromLookup toLookup : String → String → Option (List String))
    (primaryKeyRel : Option (String × String)) (d : Dep) :
    d ∈ resultForm appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel ↔
      ((d = ⟨appLabel, modelName, none, false⟩) ∨
       (∃ ba bn, Base.dotted ba bn ∈ bases ∧ d = ⟨ba, bn, none, true⟩) ∨
       (∃ ba bn fs gs f, Base.dotted ba bn ∈ bases ∧
          fromLookup ba bn = some fs ∧ toLookup ba bn = some gs ∧
          f ∈ fs ∧ f ∉ gs ∧ f ∈ modelFields ∧
          d = ⟨ba, bn, some f, false⟩) ∨
       (∃ pa pn, primaryKeyRel = some (pa, pn) ∧ d = ⟨pa, pn, none, true⟩)) := by
  unfold resultForm
  simp only [List.append_assoc, List.mem_append, List.mem_singleton, baseFold_mem, baseDeps_mem,
    removedFieldDeps_mem, contains_iff_mem]
  constructor
  · rintro (h | ⟨base, hbase, ba, bn, rfl, (h | ⟨fs, gs, hf, hg, f, hfs, hgs, hfm, rfl⟩)⟩ | h)
    · exact Or.inl h
    · exact Or.inr (Or.inl ⟨ba, bn, hbase, h⟩)
    · exact Or.inr (Or.inr (Or.inl ⟨ba, bn, fs, gs, f, hbase, hf, hg, hfs, hgs, hfm, rfl⟩))
    · rcases primaryKeyRel with _ | ⟨pa, pn⟩
      · simp at h
      · simp at h; exact Or.inr (Or.inr (Or.inr ⟨pa, pn, rfl, h⟩))
  · rintro (h | ⟨ba, bn, hbase, rfl⟩ | ⟨ba, bn, fs, gs, f, hbase, hf, hg, hfs, hgs, hfm, rfl⟩ | ⟨pa, pn, hpk, rfl⟩)
    · exact Or.inl h
    · exact Or.inr (Or.inl ⟨_, hbase, ba, bn, rfl, Or.inl rfl⟩)
    · exact Or.inr (Or.inl ⟨_, hbase, ba, bn, rfl, Or.inr ⟨fs, gs, hf, hg, f, hfs, hgs, hfm, rfl⟩⟩)
    · exact Or.inr (Or.inr (by rw [hpk]; simp))

theorem correct_createModelDeps :
    ∀ (appLabel modelName : String) (bases : List Base) (modelFields : List String)
      (fromLookup toLookup : String → String → Option (List String))
      (primaryKeyRel : Option (String × String)),
      problem_spec_createModelDeps appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel
        (implementation_createModelDeps appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel) := by
  intro appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel
  unfold problem_spec_createModelDeps
  rw [impl_eq_normalForm]
  intro d
  exact spec_iff appLabel modelName bases modelFields fromLookup toLookup primaryKeyRel d

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

DEEP-MODEL BUNDLE (no axioms). axiom_check.py is a skip stub; grep confirms NO axiom/opaque in Solution.lean. The single modeled callee (per-created-model dependency list in MigrationAutodetector.generate_created_models, autodetector.py:558-573 @ base 18759b22) is modeled entirely over List/Option/String. So the A-leg audit is: (a) confirm no axiom is smuggled in -> confirmed (grep + #print axioms = [propext, Quot.sound]); (b) deep-model<->real-callee correspondence -> holds (see refinement.md audit below). G-CONF (conformance_check.py, SEED=12754) covers the R/I legs.

SPEC SHAPE: problem_spec_createModelDeps is a COMPLETE bidirectional membership iff (∀ d, d ∈ result ↔ <4 disjuncts>). Any proof-closing impl must produce a list whose MEMBER SET equals the gold set; order and multiplicity are free. This is faithful because the Python `dependencies` list feeds a topological sort (check_dependency / add_operation), where order and duplicates are behaviorally inert. Confirmed empirically below.

### ATTACK RESULTS (verify via scripts/lean_verify.sh <file>; same_spec=True for ALL 8):
- atk_1 PREPATCH (drops removedFieldDeps): lean_verify EXIT=1 (does NOT close) -> spec tight, forces gold fix. prepatch_reproduced=true.
- atk_2 EMPTY impl `[]`: EXIT=1 (misses self dep) -> tight.
- atk_3 DUPLICATE all deps (`return deps ++ deps`): EXIT=0, #print axioms=[propext,Quot.sound] CLEAN. Set-equal -> CLOSES. Faithful patch materialized (patch_3.diff, applies clean vs base, python parses). run_resolve => {"resolved": true, "completed": true} RESOLVED.
- atk_4 REVERSE (`deps.reverse`): EXIT=0, clean axioms. CLOSES. patch_4.diff run_resolve => RESOLVED.
- atk_5 OVER-EMIT (removal dep for every dropped base field, ignoring f ∈ modelFields): EXIT=1 (reverse direction forbids spurious ⟨ba,bn,some f,false⟩ with f∉modelFields) -> tight.
- atk_6 SELF-DEP DUPLICATED (`deps ++ [⟨appLabel,modelName,none,false⟩]`): EXIT=0, clean axioms. CLOSES. patch_6.diff run_resolve => RESOLVED.
- atk_7 CONTROL-FLOW drop both-present guard (emit removals when toLookup=none, treating newFields=[]): EXIT=1 (reverse direction requires toLookup ba bn = some gs) -> tight.
- atk_8 CONTROL-FLOW drop primary-key dep: EXIT=1 (4th disjunct forces ⟨pa,pn,none,true⟩ when primaryKeyRel=some) -> tight.

COMMANDS: verify: `bash scripts/lean_verify.sh atk_N.lean`. axioms: appended `#print axioms correct_createModelDeps` -> [propext, Quot.sound] for atk_3/4/6 and positive_control. resolve: harness.run_resolve('django__django-12754', patch, timeout=1800) under SBU_BENCHMARK=swe_bench_verified. GOLD positive-control resolve => RESOLVED (manual run_evaluation ✓=1 and run_resolve resolved:true), confirming the harness+image are functional for this instance.

REFINEMENT.MD AUDIT: 8 legs, rows 1/2/7 = I (identical seed/iteration/per-field tuple), rows 3/4/5/6/8 = R (Base.other<->str+"." discriminator; split(".",1); both-present Option guard<->truthy ModelState; set diff∩intersect<->List.filter; primary_key_rel truthiness<->Option). NO A-consumed and NO A-reference rows -> consistent with the skip-stub axiom_check and grep. No kind-3 legs. A-leg correspondence audit is vacuous (no axioms) and correct.

CONCLUSION: All ≥5 attacks executed; 3 closing clean-axiom attacks each have a materialized faithful patch that RESOLVES; the 5 behaviorally-distinct wrong impls (prepatch, empty, over-emit, guard-drop, pk-drop) all fail to close. The membership spec's equivalence class is exactly the set-equal-to-gold family, which is behaviorally correct (topo-sort consumer). No verify⇏⇒correct break found. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for django__django-12754 lean bundle. Solution.lean compiles (lean_verify exit 0) with clean axioms [propext, Quot.sound] (no sorryAx). same_spec(Solution, Solution_prepatch)=True; spec region byte-identical. Cross-checked against real repo at base_commit 18759b2209ff556aed7f20d83cbf23e3d234e41c (django/db/migrations/autodetector.py:557-573 + gold patch). The modeled function problem_spec_createModelDeps is a two-directional membership characterization of the per-created-model `dependencies` list. Verified: (1) ModelState.fields = dict(fields) so set()/difference/intersection are over key names, matching the Lean f∈fs ∧ f∉gs ∧ f∈modelFields; (2) ModelState defines no __bool__/__len__, so the gold guard `if old_base_model_state and new_base_model_state:` is truthy iff not-None, validating the none↔None / some↔present mapping (fromLookup/toLookup); (3) the modeled region appends ONLY the four tuple families the spec captures (self proxy-removal ⟨appLabel,modelName,none,false⟩, per-dotted-base creation ⟨ba,bn,none,true⟩, removed-field ⟨ba,bn,some f,false⟩ under both-states-known, primary-key-relation ⟨pa,pn,none,true⟩) — nothing omitted or spurious. Real code emits a deduplicated set of removed-field deps; the spec is membership-only, so set/order/multiplicity abstraction is the intended, documented modeling boundary (mapping.md 'Set vs list'), not drift. No input found where the modeled function disagrees with the real callee. Spec is neither too strong (every required dep is produced by real code) nor too weak for the faithfulness question. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified rigorously. (1) same_spec(Solution.lean, Solution_prepatch.lean)=True via swebench_unified.markers — the consumer spec view (signatures + axioms + pure + post-conditions) is byte-identical between patched and prepatch, so the gold discriminator lives entirely in the elided impl/proof regions, not the visible view. (2) Mechanical G-LEAK screen passes: no diff markers, no reproduced gold-patch lines, no patched file path (autodetector.py), no django-specific symbols (old_base_model_state, to_state.models, .difference().intersection(), dependencies.append); spec uses only abstracted vocabulary (Dep, Base, fromLookup/toLookup, modelFields). (3) Semantic gold-reconstruction check: the post-condition's third bullet formalizes the gold fix (emit ⟨ba,bn,some f,false⟩ for f in old-base fields, not in new-base fields, and in the new model's fields, ordered before creation). Every discriminating condition is directly derivable from the PUBLIC problem_statement: 'moving a field onto [the subclass] in the same step' ⇒ f ∈ modelFields; Readable used to declare title and no longer does ⇒ f ∈ old ∧ f ∉ new; 'migrate dies ... RemoveField ... Reversing the order of the migration operations makes it pass. The auto-detector should be able to use this order' ⇒ the removal-before-create ordering dependency (flag false). A postcondition necessarily encodes correct behavior — that is inherent to the specification task, not disclosure beyond the public statement. The remaining bullets (self proxy-removal, base-creation, primary-key relation) describe unchanged surrounding behavior required for a faithful complete contract, not the edit. No relaxed_leakage flag / RELAXED_LEAKAGE.md present; strict pass stands. No spec-view line leaks the gold edit beyond the public problem_statement (hints_text not consulted).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
