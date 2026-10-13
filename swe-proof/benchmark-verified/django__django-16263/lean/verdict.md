# P2 adversarial audit — django__django-16263

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No verifying wrong impl exists. The post-condition is FULLY FUNCTIONAL: problem_spec_countPlan pins result.useSubquery = needsSubquery st AND result.keptExisting = (if needsSubquery st then keptExisting st else []), where needsSubquery/keptExisting are fixed pure-region functions. Any same-spec impl that verifies must be extensionally equal to the spec on all st, so no wrong impl can close. All 7 same-spec wrong impls fail with genuine 'unsolved goals' (theorem is false), not tactic artifacts. Concrete witnesses (#eval on spec oracle): st1 = {anns=[x: selected,non-added,non-agg,no-over,refs=[]], all flags false} -> spec {useSubquery:=false, keptExisting:=[]} (kills atk_1 prepatch subquery bug, which returns useSubquery=true on a plain selected scalar clause). st2 = {anns=[x: selected non-added unreferenced; c: added agg refs=[]], isSliced=true} -> spec {useSubquery:=true, keptExisting:=[]} (x pruned; kills atk_2 prepatch masking bug and atk_6, which keep x).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,12 +110,8 @@
 -- impl-start
 def implementation_countPlan (st : QState) : Plan := Id.run do
   let existing := st.anns.filter (fun a => !a.added && a.selected)
-  let mut hasAgg := false
-  for a in existing do
-    if a.containsAggregate || a.containsOverClause then
-      hasAgg := true
   let needsSub :=
-    st.groupByTuple || st.isSliced || (hasAgg || st.postGroupFilter)
+    st.groupByTuple || st.isSliced || (!existing.isEmpty || st.postGroupFilter)
       || st.distinct || st.combinator
   if needsSub then
     let mut mask : List String := []
@@ -138,46 +134,12 @@
 theorem correct_countPlan : ∀ (st : QState),
     problem_spec_countPlan st (implementation_countPlan st) := by
   intro st
-  have hbool : ∀ (l : List Ann) (b0 : Bool),
-      List.foldl (fun b a => if (a.containsAggregate || a.containsOverClause) = true then true else b) b0 l
-        = (b0 || l.any (fun a => a.containsAggregate || a.containsOverClause)) := by
-    intro l
-    induction l with
-    | nil => simp
-    | cons x xs ih =>
-      intro b0
-      simp only [List.foldl_cons, List.any_cons]
-      rw [ih]
-      by_cases h : (x.containsAggregate || x.containsOverClause) = true <;> simp [h]
-  have hlist : ∀ (l : List Ann) (acc : List String),
-      List.foldl (fun b a => if a.added = true then b ++ (a.aliasName :: a.refs) else b) acc l
-        = acc ++ (l.filter (fun a => a.added)).flatMap (fun a => a.aliasName :: a.refs) := by
-    intro l
-    induction l with
-    | nil => simp
-    | cons x xs ih =>
-      intro acc
-      simp only [List.foldl_cons, List.filter_cons]
-      by_cases h : x.added = true <;> simp [h, ih, List.append_assoc]
-  unfold problem_spec_countPlan
-  simp only [implementation_countPlan, Id.run, bind_pure, pure_bind,
-    ← apply_ite (f := ForInStep.yield), ← apply_ite (f := pure (f := Id)),
-    show ∀ (x : ForInStep Bool), (pure x : Id _) = x from fun _ => rfl,
-    show ∀ (x : ForInStep (List String)), (pure x : Id _) = x from fun _ => rfl,
-    List.forIn_yield_eq_foldl]
-  rw [hbool, hlist]
-  simp only [Bool.false_or, List.nil_append, bind, Id.instMonad]
-  -- Now needsSub matches needsSubquery st
-  have hns : (st.groupByTuple || st.isSliced ||
-      ((List.filter (fun a => !a.added && a.selected) st.anns).any
-        (fun a => a.containsAggregate || a.containsOverClause) || st.postGroupFilter) ||
-      st.distinct || st.combinator) = needsSubquery st := by
-    simp only [needsSubquery, hasExistingAgg, existingAnns]
-  rw [hns]
-  constructor
-  · by_cases h : needsSubquery st = true <;> simp [h]
-  · by_cases h : needsSubquery st = true <;>
-      simp only [h, if_true, if_pos, if_neg, if_false, ite_true, ite_false,
-        keptExisting, addedMask, existingAnns, Bool.false_eq_true, reduceCtorEq]
-
+  unfold problem_spec_countPlan implementation_countPlan
+  simp only [Id.run, needsSubquery, hasExistingAgg, existingAnns, keptExisting, addedMask]
+  first
+    | (by_cases h : needsSubquery st <;> simp_all [needsSubquery, hasExistingAgg, existingAnns, keptExisting, addedMask])
+    | simp_all
+    | (constructor <;> simp_all)
+    | rfl
+    | decide
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -118,16 +118,7 @@
     st.groupByTuple || st.isSliced || (hasAgg || st.postGroupFilter)
       || st.distinct || st.combinator
   if needsSub then
-    let mut mask : List String := []
-    for a in st.anns do
-      if a.added then
-        mask := mask ++ (a.aliasName :: a.refs)
-    let kept :=
-      if st.distinct then
-        existing.map (fun a => a.aliasName)
-      else
-        (st.anns.filter (fun a => !a.added && mask.contains a.aliasName)).map
-          (fun a => a.aliasName)
+    let kept := existing.map (fun a => a.aliasName)
     return { useSubquery := true, keptExisting := kept }
   else
     return { useSubquery := false, keptExisting := [] }
@@ -138,46 +129,12 @@
 theorem correct_countPlan : ∀ (st : QState),
     problem_spec_countPlan st (implementation_countPlan st) := by
   intro st
-  have hbool : ∀ (l : List Ann) (b0 : Bool),
-      List.foldl (fun b a => if (a.containsAggregate || a.containsOverClause) = true then true else b) b0 l
-        = (b0 || l.any (fun a => a.containsAggregate || a.containsOverClause)) := by
-    intro l
-    induction l with
-    | nil => simp
-    | cons x xs ih =>
-      intro b0
-      simp only [List.foldl_cons, List.any_cons]
-      rw [ih]
-      by_cases h : (x.containsAggregate || x.containsOverClause) = true <;> simp [h]
-  have hlist : ∀ (l : List Ann) (acc : List String),
-      List.foldl (fun b a => if a.added = true then b ++ (a.aliasName :: a.refs) else b) acc l
-        = acc ++ (l.filter (fun a => a.added)).flatMap (fun a => a.aliasName :: a.refs) := by
-    intro l
-    induction l with
-    | nil => simp
-    | cons x xs ih =>
-      intro acc
-      simp only [List.foldl_cons, List.filter_cons]
-      by_cases h : x.added = true <;> simp [h, ih, List.append_assoc]
-  unfold problem_spec_countPlan
-  simp only [implementation_countPlan, Id.run, bind_pure, pure_bind,
-    ← apply_ite (f := ForInStep.yield), ← apply_ite (f := pure (f := Id)),
-    show ∀ (x : ForInStep Bool), (pure x : Id _) = x from fun _ => rfl,
-    show ∀ (x : ForInStep (List String)), (pure x : Id _) = x from fun _ => rfl,
-    List.forIn_yield_eq_foldl]
-  rw [hbool, hlist]
-  simp only [Bool.false_or, List.nil_append, bind, Id.instMonad]
-  -- Now needsSub matches needsSubquery st
-  have hns : (st.groupByTuple || st.isSliced ||
-      ((List.filter (fun a => !a.added && a.selected) st.anns).any
-        (fun a => a.containsAggregate || a.containsOverClause) || st.postGroupFilter) ||
-      st.distinct || st.combinator) = needsSubquery st := by
-    simp only [needsSubquery, hasExistingAgg, existingAnns]
-  rw [hns]
-  constructor
-  · by_cases h : needsSubquery st = true <;> simp [h]
-  · by_cases h : needsSubquery st = true <;>
-      simp only [h, if_true, if_pos, if_neg, if_false, ite_true, ite_false,
-        keptExisting, addedMask, existingAnns, Bool.false_eq_true, reduceCtorEq]
-
+  unfold problem_spec_countPlan implementation_countPlan
+  simp only [Id.run, needsSubquery, hasExistingAgg, existingAnns, keptExisting, addedMask]
+  first
+    | (by_cases h : needsSubquery st <;> simp_all [needsSubquery, hasExistingAgg, existingAnns, keptExisting, addedMask])
+    | simp_all
+    | (constructor <;> simp_all)
+    | rfl
+    | decide
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -118,17 +118,7 @@
     st.groupByTuple || st.isSliced || (hasAgg || st.postGroupFilter)
       || st.distinct || st.combinator
   if needsSub then
-    let mut mask : List String := []
-    for a in st.anns do
-      if a.added then
-        mask := mask ++ (a.aliasName :: a.refs)
-    let kept :=
-      if st.distinct then
-        existing.map (fun a => a.aliasName)
-      else
-        (st.anns.filter (fun a => !a.added && mask.contains a.aliasName)).map
-          (fun a => a.aliasName)
-    return { useSubquery := true, keptExisting := kept }
+    return { useSubquery := true, keptExisting := [] }
   else
     return { useSubquery := false, keptExisting := [] }
 -- impl-end
@@ -138,46 +128,12 @@
 theorem correct_countPlan : ∀ (st : QState),
     problem_spec_countPlan st (implementation_countPlan st) := by
   intro st
-  have hbool : ∀ (l : List Ann) (b0 : Bool),
-      List.foldl (fun b a => if (a.containsAggregate || a.containsOverClause) = true then true else b) b0 l
-        = (b0 || l.any (fun a => a.containsAggregate || a.containsOverClause)) := by
-    intro l
-    induction l with
-    | nil => simp
-    | cons x xs ih =>
-      intro b0
-      simp only [List.foldl_cons, List.any_cons]
-      rw [ih]
-      by_cases h : (x.containsAggregate || x.containsOverClause) = true <;> simp [h]
-  have hlist : ∀ (l : List Ann) (acc : List String),
-      List.foldl (fun b a => if a.added = true then b ++ (a.aliasName :: a.refs) else b) acc l
-        = acc ++ (l.filter (fun a => a.added)).flatMap (fun a => a.aliasName :: a.refs) := by
-    intro l
-    induction l with
-    | nil => simp
-    | cons x xs ih =>
-      intro acc
-      simp only [List.foldl_cons, List.filter_cons]
-      by_cases h : x.added = true <;> simp [h, ih, List.append_assoc]
-  unfold problem_spec_countPlan
-  simp only [implementation_countPlan, Id.run, bind_pure, pure_bind,
-    ← apply_ite (f := ForInStep.yield), ← apply_ite (f := pure (f := Id)),
-    show ∀ (x : ForInStep Bool), (pure x : Id _) = x from fun _ => rfl,
-    show ∀ (x : ForInStep (List String)), (pure x : Id _) = x from fun _ => rfl,
-    List.forIn_yield_eq_foldl]
-  rw [hbool, hlist]
-  simp only [Bool.false_or, List.nil_append, bind, Id.instMonad]
-  -- Now needsSub matches needsSubquery st
-  have hns : (st.groupByTuple || st.isSliced ||
-      ((List.filter (fun a => !a.added && a.selected) st.anns).any
-        (fun a => a.containsAggregate || a.containsOverClause) || st.postGroupFilter) ||
-      st.distinct || st.combinator) = needsSubquery st := by
-    simp only [needsSubquery, hasExistingAgg, existingAnns]
-  rw [hns]
-  constructor
-  · by_cases h : needsSubquery st = true <;> simp [h]
-  · by_cases h : needsSubquery st = true <;>
-      simp only [h, if_true, if_pos, if_neg, if_false, ite_true, ite_false,
-        keptExisting, addedMask, existingAnns, Bool.false_eq_true, reduceCtorEq]
-
+  unfold problem_spec_countPlan implementation_countPlan
+  simp only [Id.run, needsSubquery, hasExistingAgg, existingAnns, keptExisting, addedMask]
+  first
+    | (by_cases h : needsSubquery st <;> simp_all [needsSubquery, hasExistingAgg, existingAnns, keptExisting, addedMask])
+    | simp_all
+    | (constructor <;> simp_all)
+    | rfl
+    | decide
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -116,7 +116,7 @@
       hasAgg := true
   let needsSub :=
     st.groupByTuple || st.isSliced || (hasAgg || st.postGroupFilter)
-      || st.distinct || st.combinator
+      || st.distinct
   if needsSub then
     let mut mask : List String := []
     for a in st.anns do
@@ -138,46 +138,12 @@
 theorem correct_countPlan : ∀ (st : QState),
     problem_spec_countPlan st (implementation_countPlan st) := by
   intro st
-  have hbool : ∀ (l : List Ann) (b0 : Bool),
-      List.foldl (fun b a => if (a.containsAggregate || a.containsOverClause) = true then true else b) b0 l
-        = (b0 || l.any (fun a => a.containsAggregate || a.containsOverClause)) := by
-    intro l
-    induction l with
-    | nil => simp
-    | cons x xs ih =>
-      intro b0
-      simp only [List.foldl_cons, List.any_cons]
-      rw [ih]
-      by_cases h : (x.containsAggregate || x.containsOverClause) = true <;> simp [h]
-  have hlist : ∀ (l : List Ann) (acc : List String),
-      List.foldl (fun b a => if a.added = true then b ++ (a.aliasName :: a.refs) else b) acc l
-        = acc ++ (l.filter (fun a => a.added)).flatMap (fun a => a.aliasName :: a.refs) := by
-    intro l
-    induction l with
-    | nil => simp
-    | cons x xs ih =>
-      intro acc
-      simp only [List.foldl_cons, List.filter_cons]
-      by_cases h : x.added = true <;> simp [h, ih, List.append_assoc]
-  unfold problem_spec_countPlan
-  simp only [implementation_countPlan, Id.run, bind_pure, pure_bind,
-    ← apply_ite (f := ForInStep.yield), ← apply_ite (f := pure (f := Id)),
-    show ∀ (x : ForInStep Bool), (pure x : Id _) = x from fun _ => rfl,
-    show ∀ (x : ForInStep (List String)), (pure x : Id _) = x from fun _ => rfl,
-    List.forIn_yield_eq_foldl]
-  rw [hbool, hlist]
-  simp only [Bool.false_or, List.nil_append, bind, Id.instMonad]
-  -- Now needsSub matches needsSubquery st
-  have hns : (st.groupByTuple || st.isSliced ||
-      ((List.filter (fun a => !a.added && a.selected) st.anns).any
-        (fun a => a.containsAggregate || a.containsOverClause) || st.postGroupFilter) ||
-      st.distinct || st.combinator) = needsSubquery st := by
-    simp only [needsSubquery, hasExistingAgg, existingAnns]
-  rw [hns]
-  constructor
-  · by_cases h : needsSubquery st = true <;> simp [h]
-  · by_cases h : needsSubquery st = true <;>
-      simp only [h, if_true, if_pos, if_neg, if_false, ite_true, ite_false,
-        keptExisting, addedMask, existingAnns, Bool.false_eq_true, reduceCtorEq]
-
+  unfold problem_spec_countPlan implementation_countPlan
+  simp only [Id.run, needsSubquery, hasExistingAgg, existingAnns, keptExisting, addedMask]
+  first
+    | (by_cases h : needsSubquery st <;> simp_all [needsSubquery, hasExistingAgg, existingAnns, keptExisting, addedMask])
+    | simp_all
+    | (constructor <;> simp_all)
+    | rfl
+    | decide
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,8 +112,7 @@
   let existing := st.anns.filter (fun a => !a.added && a.selected)
   let mut hasAgg := false
   for a in existing do
-    if a.containsAggregate || a.containsOverClause then
-      hasAgg := true
+    hasAgg := a.containsAggregate || a.containsOverClause
   let needsSub :=
     st.groupByTuple || st.isSliced || (hasAgg || st.postGroupFilter)
       || st.distinct || st.combinator
@@ -138,46 +137,12 @@
 theorem correct_countPlan : ∀ (st : QState),
     problem_spec_countPlan st (implementation_countPlan st) := by
   intro st
-  have hbool : ∀ (l : List Ann) (b0 : Bool),
-      List.foldl (fun b a => if (a.containsAggregate || a.containsOverClause) = true then true else b) b0 l
-        = (b0 || l.any (fun a => a.containsAggregate || a.containsOverClause)) := by
-    intro l
-    induction l with
-    | nil => simp
-    | cons x xs ih =>
-      intro b0
-      simp only [List.foldl_cons, List.any_cons]
-      rw [ih]
-      by_cases h : (x.containsAggregate || x.containsOverClause) = true <;> simp [h]
-  have hlist : ∀ (l : List Ann) (acc : List String),
-      List.foldl (fun b a => if a.added = true then b ++ (a.aliasName :: a.refs) else b) acc l
-        = acc ++ (l.filter (fun a => a.added)).flatMap (fun a => a.aliasName :: a.refs) := by
-    intro l
-    induction l with
-    | nil => simp
-    | cons x xs ih =>
-      intro acc
-      simp only [List.foldl_cons, List.filter_cons]
-      by_cases h : x.added = true <;> simp [h, ih, List.append_assoc]
-  unfold problem_spec_countPlan
-  simp only [implementation_countPlan, Id.run, bind_pure, pure_bind,
-    ← apply_ite (f := ForInStep.yield), ← apply_ite (f := pure (f := Id)),
-    show ∀ (x : ForInStep Bool), (pure x : Id _) = x from fun _ => rfl,
-    show ∀ (x : ForInStep (List String)), (pure x : Id _) = x from fun _ => rfl,
-    List.forIn_yield_eq_foldl]
-  rw [hbool, hlist]
-  simp only [Bool.false_or, List.nil_append, bind, Id.instMonad]
-  -- Now needsSub matches needsSubquery st
-  have hns : (st.groupByTuple || st.isSliced ||
-      ((List.filter (fun a => !a.added && a.selected) st.anns).any
-        (fun a => a.containsAggregate || a.containsOverClause) || st.postGroupFilter) ||
-      st.distinct || st.combinator) = needsSubquery st := by
-    simp only [needsSubquery, hasExistingAgg, existingAnns]
-  rw [hns]
-  constructor
-  · by_cases h : needsSubquery st = true <;> simp [h]
-  · by_cases h : needsSubquery st = true <;>
-      simp only [h, if_true, if_pos, if_neg, if_false, ite_true, ite_false,
-        keptExisting, addedMask, existingAnns, Bool.false_eq_true, reduceCtorEq]
-
+  unfold problem_spec_countPlan implementation_countPlan
+  simp only [Id.run, needsSubquery, hasExistingAgg, existingAnns, keptExisting, addedMask]
+  first
+    | (by_cases h : needsSubquery st <;> simp_all [needsSubquery, hasExistingAgg, existingAnns, keptExisting, addedMask])
+    | simp_all
+    | (constructor <;> simp_all)
+    | rfl
+    | decide
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -123,11 +123,8 @@
       if a.added then
         mask := mask ++ (a.aliasName :: a.refs)
     let kept :=
-      if st.distinct then
-        existing.map (fun a => a.aliasName)
-      else
-        (st.anns.filter (fun a => !a.added && mask.contains a.aliasName)).map
-          (fun a => a.aliasName)
+      (st.anns.filter (fun a => !a.added && mask.contains a.aliasName)).map
+        (fun a => a.aliasName)
     return { useSubquery := true, keptExisting := kept }
   else
     return { useSubquery := false, keptExisting := [] }
@@ -138,46 +135,12 @@
 theorem correct_countPlan : ∀ (st : QState),
     problem_spec_countPlan st (implementation_countPlan st) := by
   intro st
-  have hbool : ∀ (l : List Ann) (b0 : Bool),
-      List.foldl (fun b a => if (a.containsAggregate || a.containsOverClause) = true then true else b) b0 l
-        = (b0 || l.any (fun a => a.containsAggregate || a.containsOverClause)) := by
-    intro l
-    induction l with
-    | nil => simp
-    | cons x xs ih =>
-      intro b0
-      simp only [List.foldl_cons, List.any_cons]
-      rw [ih]
-      by_cases h : (x.containsAggregate || x.containsOverClause) = true <;> simp [h]
-  have hlist : ∀ (l : List Ann) (acc : List String),
-      List.foldl (fun b a => if a.added = true then b ++ (a.aliasName :: a.refs) else b) acc l
-        = acc ++ (l.filter (fun a => a.added)).flatMap (fun a => a.aliasName :: a.refs) := by
-    intro l
-    induction l with
-    | nil => simp
-    | cons x xs ih =>
-      intro acc
-      simp only [List.foldl_cons, List.filter_cons]
-      by_cases h : x.added = true <;> simp [h, ih, List.append_assoc]
-  unfold problem_spec_countPlan
-  simp only [implementation_countPlan, Id.run, bind_pure, pure_bind,
-    ← apply_ite (f := ForInStep.yield), ← apply_ite (f := pure (f := Id)),
-    show ∀ (x : ForInStep Bool), (pure x : Id _) = x from fun _ => rfl,
-    show ∀ (x : ForInStep (List String)), (pure x : Id _) = x from fun _ => rfl,
-    List.forIn_yield_eq_foldl]
-  rw [hbool, hlist]
-  simp only [Bool.false_or, List.nil_append, bind, Id.instMonad]
-  -- Now needsSub matches needsSubquery st
-  have hns : (st.groupByTuple || st.isSliced ||
-      ((List.filter (fun a => !a.added && a.selected) st.anns).any
-        (fun a => a.containsAggregate || a.containsOverClause) || st.postGroupFilter) ||
-      st.distinct || st.combinator) = needsSubquery st := by
-    simp only [needsSubquery, hasExistingAgg, existingAnns]
-  rw [hns]
-  constructor
-  · by_cases h : needsSubquery st = true <;> simp [h]
-  · by_cases h : needsSubquery st = true <;>
-      simp only [h, if_true, if_pos, if_neg, if_false, ite_true, ite_false,
-        keptExisting, addedMask, existingAnns, Bool.false_eq_true, reduceCtorEq]
-
+  unfold problem_spec_countPlan implementation_countPlan
+  simp only [Id.run, needsSubquery, hasExistingAgg, existingAnns, keptExisting, addedMask]
+  first
+    | (by_cases h : needsSubquery st <;> simp_all [needsSubquery, hasExistingAgg, existingAnns, keptExisting, addedMask])
+    | simp_all
+    | (constructor <;> simp_all)
+    | rfl
+    | decide
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,7 +112,7 @@
   let existing := st.anns.filter (fun a => !a.added && a.selected)
   let mut hasAgg := false
   for a in existing do
-    if a.containsAggregate || a.containsOverClause then
+    if a.containsAggregate then
       hasAgg := true
   let needsSub :=
     st.groupByTuple || st.isSliced || (hasAgg || st.postGroupFilter)
@@ -138,46 +138,12 @@
 theorem correct_countPlan : ∀ (st : QState),
     problem_spec_countPlan st (implementation_countPlan st) := by
   intro st
-  have hbool : ∀ (l : List Ann) (b0 : Bool),
-      List.foldl (fun b a => if (a.containsAggregate || a.containsOverClause) = true then true else b) b0 l
-        = (b0 || l.any (fun a => a.containsAggregate || a.containsOverClause)) := by
-    intro l
-    induction l with
-    | nil => simp
-    | cons x xs ih =>
-      intro b0
-      simp only [List.foldl_cons, List.any_cons]
-      rw [ih]
-      by_cases h : (x.containsAggregate || x.containsOverClause) = true <;> simp [h]
-  have hlist : ∀ (l : List Ann) (acc : List String),
-      List.foldl (fun b a => if a.added = true then b ++ (a.aliasName :: a.refs) else b) acc l
-        = acc ++ (l.filter (fun a => a.added)).flatMap (fun a => a.aliasName :: a.refs) := by
-    intro l
-    induction l with
-    | nil => simp
-    | cons x xs ih =>
-      intro acc
-      simp only [List.foldl_cons, List.filter_cons]
-      by_cases h : x.added = true <;> simp [h, ih, List.append_assoc]
-  unfold problem_spec_countPlan
-  simp only [implementation_countPlan, Id.run, bind_pure, pure_bind,
-    ← apply_ite (f := ForInStep.yield), ← apply_ite (f := pure (f := Id)),
-    show ∀ (x : ForInStep Bool), (pure x : Id _) = x from fun _ => rfl,
-    show ∀ (x : ForInStep (List String)), (pure x : Id _) = x from fun _ => rfl,
-    List.forIn_yield_eq_foldl]
-  rw [hbool, hlist]
-  simp only [Bool.false_or, List.nil_append, bind, Id.instMonad]
-  -- Now needsSub matches needsSubquery st
-  have hns : (st.groupByTuple || st.isSliced ||
-      ((List.filter (fun a => !a.added && a.selected) st.anns).any
-        (fun a => a.containsAggregate || a.containsOverClause) || st.postGroupFilter) ||
-      st.distinct || st.combinator) = needsSubquery st := by
-    simp only [needsSubquery, hasExistingAgg, existingAnns]
-  rw [hns]
-  constructor
-  · by_cases h : needsSubquery st = true <;> simp [h]
-  · by_cases h : needsSubquery st = true <;>
-      simp only [h, if_true, if_pos, if_neg, if_false, ite_true, ite_false,
-        keptExisting, addedMask, existingAnns, Bool.false_eq_true, reduceCtorEq]
-
+  unfold problem_spec_countPlan implementation_countPlan
+  simp only [Id.run, needsSubquery, hasExistingAgg, existingAnns, keptExisting, addedMask]
+  first
+    | (by_cases h : needsSubquery st <;> simp_all [needsSubquery, hasExistingAgg, existingAnns, keptExisting, addedMask])
+    | simp_all
+    | (constructor <;> simp_all)
+    | rfl
+    | decide
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Planning a row-count query over a model whose query carries extra named clauses.

A count is computed by adding one summary aggregate (the row counter) and then
deciding how to shape the resulting query.  Two things must be decided from the
named clauses the query already carries:

  * whether the count has to be computed inside a wrapping subquery, and
  * which of the already-present clauses must remain materialised in the
    emitted query.

A carried clause that is materialised in the result (`selected`) and is itself
an aggregate (or an OVER-style window), or the presence of post-grouping
filters, forces the wrapping subquery.  Carried clauses that are present only as
named aliases, or that are plain scalar expressions, do not.  When a wrapping
subquery is used and the query is not `distinct`, an already-present clause is
kept only when one of the summary aggregates being computed refers to it;
otherwise it is dropped.  When the query is `distinct`, re-masking would alter
the distinct row set, so every materialised already-present clause is kept.
When no wrapping subquery is needed, none of the already-present clauses is
kept.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: every quantity the decision reads
-- (whether a carried clause is an aggregate / window, whether it is materialised,
-- the alias references carried by each summary aggregate, and the presence of
-- post-grouping filters) is supplied as data on the modeled carrier and the
-- decision is spelled out directly below.
-- axioms-end

-- pure-start
/-- One named clause carried by the query. `aliasName` is its name; `selected`
records whether it is materialised in the emitted column list (a plain named
alias is *not* selected); `containsAggregate` / `containsOverClause` record
whether it is an aggregate or an OVER-style window; `added` marks the summary
aggregate(s) introduced for this computation; `refs` are the alias names this
clause refers to. -/
structure Ann where
  aliasName : String
  selected : Bool
  containsAggregate : Bool
  containsOverClause : Bool
  added : Bool
  refs : List String
deriving Repr, DecidableEq

/-- The query state the decision reads. -/
structure QState where
  anns : List Ann
  groupByTuple : Bool
  isSliced : Bool
  distinct : Bool
  combinator : Bool
  postGroupFilter : Bool
deriving Repr

/-- The planning outcome: whether a wrapping subquery is used and which
already-present clause aliases remain materialised in the emitted query. -/
structure Plan where
  useSubquery : Bool
  keptExisting : List String
deriving Repr, DecidableEq

/-- The materialised already-present clauses (those in the emitted column list
and not one of the summary aggregates introduced for this computation). This is
the set that governs whether a wrapping subquery is needed. -/
def existingAnns (st : QState) : List Ann :=
  st.anns.filter (fun a => !a.added && a.selected)

/-- Whether the materialised already-present clauses include an aggregate/window,
or the query carries post-grouping filters. -/
def hasExistingAgg (st : QState) : Bool :=
  (existingAnns st).any (fun a => a.containsAggregate || a.containsOverClause)
    || st.postGroupFilter

/-- Whether a wrapping subquery is required. -/
def needsSubquery (st : QState) : Bool :=
  st.groupByTuple || st.isSliced || hasExistingAgg st || st.distinct || st.combinator

/-- The set of alias names the summary aggregates keep alive: each summary
aggregate's own name together with the names it refers to. -/
def addedMask (st : QState) : List String :=
  (st.anns.filter (fun a => a.added)).flatMap (fun a => a.aliasName :: a.refs)

/-- The already-present clause aliases kept inside the wrapping subquery. When
the query is `distinct`, the reference-based rebuild of the surviving mask is
skipped (re-masking would alter the distinct row set), so exactly the
materialised already-present clauses survive. Otherwise the surviving mask is
rebuilt purely from the summary aggregates' references: every carried clause
(materialised OR a plain named alias, irrespective of whether the clause was
itself materialised) referred to by a summary aggregate is kept. -/
def keptExisting (st : QState) : List String :=
  if st.distinct then
    (existingAnns st).map (fun a => a.aliasName)
  else
    ((st.anns.filter (fun a => !a.added && (addedMask st).contains a.aliasName))).map
      (fun a => a.aliasName)
-- pure-end

-- post-conditions-start
def problem_spec_countPlan (st : QState) (result : Plan) : Prop :=
  result.useSubquery = needsSubquery st ∧
  result.keptExisting = (if needsSubquery st then keptExisting st else [])
-- post-conditions-end

-- impl-start
def implementation_countPlan (st : QState) : Plan :=
  if needsSubquery st then
    { useSubquery := true, keptExisting := keptExisting st }
  else
    { useSubquery := false, keptExisting := [] }
-- impl-end


-- proof-start
theorem correct_countPlan : ∀ (st : QState),
    problem_spec_countPlan st (implementation_countPlan st) := by
  intro st
  unfold problem_spec_countPlan implementation_countPlan
  by_cases h : needsSubquery st <;> simp [h]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Protocol executed. same_spec(Solution, atk_i) = True for all 7 attacks and the positive control (swebench_unified.markers.same_spec, lean backend), confirmed byte-identical spec view.

### ATTACKS (all editing ONLY the impl region; axioms/pure/pre/post byte-identical):
- atk_1: prepatch subquery bug — needsSub uses !existing.isEmpty instead of the aggregate/over/postGroupFilter test (mere presence of any selected non-added clause forces subquery). cmd: `bash scripts/lean_verify.sh atk_1.lean` -> exit 1, error at 135:63 'unsolved goals'.
- atk_2: prepatch masking bug — kept := existing.map aliasName (drops the mask.contains ref-based pruning). exit 1, 130:63 unsolved goals.
- atk_3: partial-domain — keptExisting always [] even when subquery needed. exit 1, 129:63 unsolved goals.
- atk_4: boundary/omission — drops st.combinator from needsSub. exit 1, 139:63 unsolved goals.
- atk_5: control-flow-effect — hasAgg := last-write (=) instead of OR-accumulate over loop. exit 1, 138:63 unsolved goals.
- atk_6: ungrounded — drops the distinct guard on kept (always ref-mask rebuild, so distinct queries wrongly prune). exit 1, 136:63 unsolved goals.
- atk_7: ignores containsOverClause (only containsAggregate) in hasAgg test. exit 1, 139:63 unsolved goals.

Each attack file carried an AGGRESSIVE closing-proof attempt (unfold + simp only [Id.run,needsSubquery,hasExistingAgg,existingAnns,keptExisting,addedMask] + first{by_cases needsSubquery<;>simp_all | simp_all | constructor<;>simp_all | rfl | decide}); none closed. All ran concurrently (batch of 4 then 3) via background bash jobs.

No wrong impl's proof closed => zero verifying counterexamples => NO faithful patch needed materialization/resolve (the resolve step triggers only for a verifying same-spec wrong impl). patches = {} accordingly.

POSITIVE CONTROL (pos.lean): alternate correct impl written directly from the oracle — implementation_countPlan st := if needsSubquery st then {true, keptExisting st} else {false, []}, with a fresh proof (unfold; by_cases needsSubquery <;> simp). `bash scripts/lean_verify.sh pos.lean` -> exit 0. `#print axioms correct_countPlan` -> [propext] (clean, no sorryAx/Classical.choice). Shipped Solution.lean also verifies: axioms [propext, Quot.sound] (clean).

prepatch_reproduced=true: atk_1 == Solution_prepatch.lean behavior (subquery decision) and atk_2 == Solution_prepatch_2.lean behavior (masking); both are same_spec=True wrong impls that FAIL G-VERIFY exactly as refinement.md claims.

REFINEMENT.MD AUDIT: 7 legs — leg1 R, leg2 A-reference, leg3 A-reference, leg4 I, leg5 A-reference, leg6 R, leg7 I. No A-consumed, no kind-3 (dead/behavior-masking) axiom. The axioms region declares/consumes NO `axiom <callee>_prop`; #print axioms = [propext, Quot.sound] confirms the proof depends on no opaque callee property. A-reference correspondence holds: leg5 Ann.refs ≙ patch-introduced get_refs() (Ref/BaseExpression/WhereNode.get_refs), leg2 containsAggregate/containsOverClause ≙ getattr(...,True), leg3 postGroupFilter ≙ any(where.split_having_qualify()[1:]) — all A-reference, validated by G-CONF, never axiomatized; matches the changed/unchanged callee classification. G-AX is a skip stub (no axioms consumed), consistent with meta.json.

CONCLUSION: verify ⇒ correct holds for this bundle. The functional post-condition uniquely determines both output fields, so verification is extensionally faithful; every distinct wrong impl (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, and both prepatch bugs) is rejected. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No verifying wrong impl exists. The post-condition is FULLY FUNCTIONAL: problem_spec_countPlan pins result.useSubquery = needsSubquery st AND result.keptExisting = (if needsSubquery st then keptExisting st else []), where needsSubquery/keptExisting are fixed pure-region functions. Any same-spec impl that verifies must be extensionally equal to the spec on all st, so no wrong impl can close. All 7 same-spec wrong impls fail with genuine 'unsolved goals' (theorem is false), not tactic artifacts. Concrete witnesses (#eval on spec oracle): st1 = {anns=[x: selected,non-added,non-agg,no-over,refs=[]], all flags false} -> spec {useSubquery:=false, keptExisting:=[]} (kills atk_1 prepatch subquery bug, which returns useSubquery=true on a plain selected scalar clause). st2 = {anns=[x: selected non-added unreferenced; c: added agg refs=[]], isSliced=true} -> spec {useSubquery:=true, keptExisting:=[]} (x pruned; kills atk_2 prepatch masking bug and atk_6, which keep x).
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Planning a row-count query over a model whose query carries extra named clauses.

A count is computed by adding one summary aggregate (the row counter) and then
deciding how to shape the resulting query.  Two things must be decided from the
named clauses the query already carries:

  * whether the count has to be computed inside a wrapping subquery, and
  * which of the already-present clauses must remain materialised in the
    emitted query.

A carried clause that is materialised in the result (`selected`) and is itself
an aggregate (or an OVER-style window), or the presence of post-grouping
filters, forces the wrapping subquery.  Carried clauses that are present only as
named aliases, or that are plain scalar expressions, do not.  When a wrapping
subquery is used and the query is not `distinct`, an already-present clause is
kept only when one of the summary aggregates being computed refers to it;
otherwise it is dropped.  When the query is `distinct`, re-masking would alter
the distinct row set, so every materialised already-present clause is kept.
When no wrapping subquery is needed, none of the already-present clauses is
kept.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: every quantity the decision reads
-- (whether a carried clause is an aggregate / window, whether it is materialised,
-- the alias references carried by each summary aggregate, and the presence of
-- post-grouping filters) is supplied as data on the modeled carrier and the
-- decision is spelled out directly below.
-- axioms-end

-- pure-start
/-- One named clause carried by the query. `aliasName` is its name; `selected`
records whether it is materialised in the emitted column list (a plain named
alias is *not* selected); `containsAggregate` / `containsOverClause` record
whether it is an aggregate or an OVER-style window; `added` marks the summary
aggregate(s) introduced for this computation; `refs` are the alias names this
clause refers to. -/
structure Ann where
  aliasName : String
  selected : Bool
  containsAggregate : Bool
  containsOverClause : Bool
  added : Bool
  refs : List String
deriving Repr, DecidableEq

/-- The query state the decision reads. -/
structure QState where
  anns : List Ann
  groupByTuple : Bool
  isSliced : Bool
  distinct : Bool
  combinator : Bool
  postGroupFilter : Bool
deriving Repr

/-- The planning outcome: whether a wrapping subquery is used and which
already-present clause aliases remain materialised in the emitted query. -/
structure Plan where
  useSubquery : Bool
  keptExisting : List String
deriving Repr, DecidableEq

/-- The materialised already-present clauses (those in the emitted column list
and not one of the summary aggregates introduced for this computation). This is
the set that governs whether a wrapping subquery is needed. -/
def existingAnns (st : QState) : List Ann :=
  st.anns.filter (fun a => !a.added && a.selected)

/-- Whether the materialised already-present clauses include an aggregate/window,
or the query carries post-grouping filters. -/
def hasExistingAgg (st : QState) : Bool :=
  (existingAnns st).any (fun a => a.containsAggregate || a.containsOverClause)
    || st.postGroupFilter

/-- Whether a wrapping subquery is required. -/
def needsSubquery (st : QState) : Bool :=
  st.groupByTuple || st.isSliced || hasExistingAgg st || st.distinct || st.combinator

/-- The set of alias names the summary aggregates keep alive: each summary
aggregate's own name together with the names it refers to. -/
def addedMask (st : QState) : List String :=
  (st.anns.filter (fun a => a.added)).flatMap (fun a => a.aliasName :: a.refs)

/-- The already-present clause aliases kept inside the wrapping subquery. When
the query is `distinct`, the reference-based rebuild of the surviving mask is
skipped (re-masking would alter the distinct row set), so exactly the
materialised already-present clauses survive. Otherwise the surviving mask is
rebuilt purely from the summary aggregates' references: every carried clause
(materialised OR a plain named alias, irrespective of whether the clause was
itself materialised) referred to by a summary aggregate is kept. -/
def keptExisting (st : QState) : List String :=
  if st.distinct then
    (existingAnns st).map (fun a => a.aliasName)
  else
    ((st.anns.filter (fun a => !a.added && (addedMask st).contains a.aliasName))).map
      (fun a => a.aliasName)
-- pure-end

-- post-conditions-start
def problem_spec_countPlan (st : QState) (result : Plan) : Prop :=
  result.useSubquery = needsSubquery st ∧
  result.keptExisting = (if needsSubquery st then keptExisting st else [])
-- post-conditions-end

-- impl-start
def implementation_countPlan (st : QState) : Plan :=
  if needsSubquery st then
    { useSubquery := true, keptExisting := keptExisting st }
  else
    { useSubquery := false, keptExisting := [] }
-- impl-end


-- proof-start
theorem correct_countPlan : ∀ (st : QState),
    problem_spec_countPlan st (implementation_countPlan st) := by
  intro st
  unfold problem_spec_countPlan implementation_countPlan
  by_cases h : needsSubquery st <;> simp [h]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Protocol executed. same_spec(Solution, atk_i) = True for all 7 attacks and the positive control (swebench_unified.markers.same_spec, lean backend), confirmed byte-identical spec view.

### ATTACKS (all editing ONLY the impl region; axioms/pure/pre/post byte-identical):
- atk_1: prepatch subquery bug — needsSub uses !existing.isEmpty instead of the aggregate/over/postGroupFilter test (mere presence of any selected non-added clause forces subquery). cmd: `bash scripts/lean_verify.sh atk_1.lean` -> exit 1, error at 135:63 'unsolved goals'.
- atk_2: prepatch masking bug — kept := existing.map aliasName (drops the mask.contains ref-based pruning). exit 1, 130:63 unsolved goals.
- atk_3: partial-domain — keptExisting always [] even when subquery needed. exit 1, 129:63 unsolved goals.
- atk_4: boundary/omission — drops st.combinator from needsSub. exit 1, 139:63 unsolved goals.
- atk_5: control-flow-effect — hasAgg := last-write (=) instead of OR-accumulate over loop. exit 1, 138:63 unsolved goals.
- atk_6: ungrounded — drops the distinct guard on kept (always ref-mask rebuild, so distinct queries wrongly prune). exit 1, 136:63 unsolved goals.
- atk_7: ignores containsOverClause (only containsAggregate) in hasAgg test. exit 1, 139:63 unsolved goals.

Each attack file carried an AGGRESSIVE closing-proof attempt (unfold + simp only [Id.run,needsSubquery,hasExistingAgg,existingAnns,keptExisting,addedMask] + first{by_cases needsSubquery<;>simp_all | simp_all | constructor<;>simp_all | rfl | decide}); none closed. All ran concurrently (batch of 4 then 3) via background bash jobs.

No wrong impl's proof closed => zero verifying counterexamples => NO faithful patch needed materialization/resolve (the resolve step triggers only for a verifying same-spec wrong impl). patches = {} accordingly.

POSITIVE CONTROL (pos.lean): alternate correct impl written directly from the oracle — implementation_countPlan st := if needsSubquery st then {true, keptExisting st} else {false, []}, with a fresh proof (unfold; by_cases needsSubquery <;> simp). `bash scripts/lean_verify.sh pos.lean` -> exit 0. `#print axioms correct_countPlan` -> [propext] (clean, no sorryAx/Classical.choice). Shipped Solution.lean also verifies: axioms [propext, Quot.sound] (clean).

prepatch_reproduced=true: atk_1 == Solution_prepatch.lean behavior (subquery decision) and atk_2 == Solution_prepatch_2.lean behavior (masking); both are same_spec=True wrong impls that FAIL G-VERIFY exactly as refinement.md claims.

REFINEMENT.MD AUDIT: 7 legs — leg1 R, leg2 A-reference, leg3 A-reference, leg4 I, leg5 A-reference, leg6 R, leg7 I. No A-consumed, no kind-3 (dead/behavior-masking) axiom. The axioms region declares/consumes NO `axiom <callee>_prop`; #print axioms = [propext, Quot.sound] confirms the proof depends on no opaque callee property. A-reference correspondence holds: leg5 Ann.refs ≙ patch-introduced get_refs() (Ref/BaseExpression/WhereNode.get_refs), leg2 containsAggregate/containsOverClause ≙ getattr(...,True), leg3 postGroupFilter ≙ any(where.split_having_qualify()[1:]) — all A-reference, validated by G-CONF, never axiomatized; matches the changed/unchanged callee classification. G-AX is a skip stub (no axioms consumed), consistent with meta.json.

CONCLUSION: verify ⇒ correct holds for this bundle. The functional post-condition uniquely determines both output fields, so verification is extensionally faithful; every distinct wrong impl (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, and both prepatch bugs) is rejected. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of the modeled decision inside Query.get_aggregation (django/db/models/sql/query.py, gold @ base_commit + patch). Verdict: FAITHFUL — no diverging input found.

### Method
1. Lean proof is genuine. scripts/lean_verify.sh exits 0 (compiles, no sorry) and `#print axioms correct_countPlan` = [propext, Quot.sound] — no sorryAx, so implementation_countPlan provably satisfies problem_spec_countPlan. Because impl≡spec is proven, drift of the spec == drift of the impl.
2. Empirically differential-tested the modeled decision (useSubquery + keptExisting) against the REAL patched repo via CaptureQueriesContext on a sqlite checkout. Every branch matches:
   - non-distinct, no existing agg, selected non-agg (Lower) -> NO subquery (1 SELECT), pruned. spec: useSubquery=false,kept=[] ✓
   - aliased(non-selected) Count -> NO subquery ✓ (selected=false ⇒ not in `existing`)
   - selected unreferenced Count -> subquery, pruned ✓
   - selected referenced aggregate (annotate g; aggregate Avg(g)) -> subquery, g KEPT ✓
   - sliced non-distinct unreferenced non-agg -> subquery, pruned ✓
   - combinator/union -> subquery ✓
   - distinct + selected non-agg (name_lower) -> subquery, name_lower KEPT (this is exactly the G-PANEL-2 repair: masking block guarded by `if not inner_query.distinct:` so the ref-rebuild is skipped and inner mask stays at annotation_select). The repaired spec branches on `distinct` and returns kept=existing.map aliasName for distinct — matches real repo ✓
   - distinct + referenced aggregate -> subquery, kept ✓
3. Confirmed source: existing = annotation_select entries minus added_aggregate_names; has_existing_aggregation uses getattr(...,True) on contains_aggregate/contains_over_clause OR any(where.split_having_qualify()[1:]); useSubquery disjunction identical; non-distinct mask rebuilt from added names ∪ get_refs(); distinct skips rebuild. The Lean model (existingAnns/hasExistingAgg/needsSubquery/addedMask/keptExisting) mirrors each of these operations exactly, including the distinct guard and the fact that the non-distinct keep-set filters on (!added) not (selected).

The earlier G-PANEL-2 finding (distinct kept-set) has already been repaired in this bundle; I could not reproduce it or find any new diverging input. Spec is neither too strong nor too weak.

HYGIENE NOTE (not a faithfulness defect, does not affect verdict): meta.json region_hashes for pure/impl/proof/spec_view no longer match the current Solution.lean (only axioms and post-conditions still match), consistent with the G-PANEL-2 repair editing the pure/impl/proof regions without refreshing recorded hashes. The post-conditions region (the actual spec statement, problem_spec_countPlan) is unchanged and faithful; the spec_view mismatch is attributable to the pure-region edit that the (verified-genuine) proof accommodates.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (spec view clean); spec region byte-identical vs both prepatch variants (same_spec=True); meta G-LEAK status=pass, no RELAXED_LEAKAGE.md. Independent semantic review over the spec view: (1) No gold-patch line reproduced — the model is an abstract count-query planning decision over synthetic structures (Ann/QState/Plan), no Python fragments. (2) No patched file/module path present (expressions.py, query_utils.py, sql/query.py, sql/where.py absent). (3) No distinctive patched repo symbol echoed — get_refs, refs_expression, solve_lookup_type, build_filter, resolve_expression, set_annotation_mask, replace_expressions do NOT appear as identifiers or in comments; model uses generic names (needsSubquery, keptExisting, addedMask, refs). The lean field name `refs` does not embed the symbol `get_refs`. (4) No bug/fix narration in comments. (5) Beyond problem_statement? The public problem_statement already states the target: strip annotations 'not referenced by filters, other annotations or ordering' from count(), with the select_related/subquery precedent. The spec's added detail (refs-based mask, subquery forced by materialised aggregate/window or post-group filters, distinct carve-out) is a faithful BEHAVIORAL SPECIFICATION of correct behavior — the legitimate job of a spec — not a disclosure of the multi-file edit mechanism or its localization. A solver still must independently discover/implement the actual Django changes. No hints_text content leaked into the view. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
