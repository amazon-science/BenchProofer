# P2 adversarial audit — django__django-11149

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
For the three mutating actions (add/change/delete) on an auto-created link model (autoCreated=true), take a user holding only the target's VIEW permission, not its CHANGE permission: fields=[{hasRemote:=true, remoteModelId:="other", remoteAppLabel:="app", remoteModelName:="m"}], parentModelId="parent", userPerms=["app.view_m"], superResult arbitrary. The spec (problem_spec_hasAddPermission, autoCreated=true clause) demands result = anyPermForTarget ... ["change"] = ("app.change_m" ∈ userPerms) = false. The prepatch/atk_1 impl defers to ["view","change"] and returns true. So the correct_hasAddPermission/Change/Delete theorems on the autoCreated=true clause are genuinely FALSE and cannot close — exactly the FAIL_TO_PASS behavior (test_inline_add/change_m2m_view_only_perm).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -137,9 +137,7 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Resolve the target model by scanning the fields (taking the first field that
-points at a related model other than the parent), then report whether the user
-holds any of the listed action permissions on it. -/
+/-- helper -/
 def implementation_hasAnyPermsForTargetModel
     (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
     (userPerms actions : List String) : Bool := Id.run do
@@ -159,21 +157,21 @@
     (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
     (userPerms : List String) (superResult : Bool) : Bool := Id.run do
   if autoCreated then
-    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
+    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
   return superResult
 
 def implementation_hasChangePermission (autoCreated : Bool)
     (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
     (userPerms : List String) (superResult : Bool) : Bool := Id.run do
   if autoCreated then
-    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
+    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
   return superResult
 
 def implementation_hasDeletePermission (autoCreated : Bool)
     (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
     (userPerms : List String) (superResult : Bool) : Bool := Id.run do
   if autoCreated then
-    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
+    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
   return superResult
 
 def implementation_hasViewPermission (autoCreated : Bool)
@@ -185,204 +183,17 @@
 -- impl-end
 
 -- proof-start
-
--- proof_aux for correct_hasAnyPermsForTargetModel
-/-- The `(appLabel, modelName)` the first for-loop settles on: scan `fields` and
-take the first field pointing at a related model other than the parent; else keep
-`(selfAppLabel, selfModelName)`. This is `resolveTarget` by definition. -/
-def resolvedPair (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) : String × String :=
-  Id.run do
-    let mut appLabel := selfAppLabel
-    let mut modelName := selfModelName
-    for f in fields do
-      if f.hasRemote && f.remoteModelId != parentModelId then
-        appLabel := f.remoteAppLabel
-        modelName := f.remoteModelName
-        break
-    return (appLabel, modelName)
-
-theorem resolve_loop_eq (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) :
-    resolvedPair selfAppLabel selfModelName parentModelId fields
-      = resolveTarget selfAppLabel selfModelName parentModelId fields := by
-  unfold resolvedPair resolveTarget
-  induction fields with
-  | nil => rfl
-  | cons f fs ih =>
-    simp only [List.forIn_cons, List.find?_cons]
-    by_cases h : f.hasRemote && f.remoteModelId != parentModelId
-    · simp [h]
-    · simp only [h]; exact ih
-
-theorem scan_loop_eq (appLabel modelName : String) (userPerms actions : List String) :
-    (Id.run do
-      for a in actions do
-        if userPerms.contains (permString appLabel modelName a) then
-          return true
-      return false)
-      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-  simp only [Id.run]; induction actions with
-  | nil => rfl
-  | cons a as ih =>
-    simp only [List.forIn_cons, List.any_cons]
-    split
-    · rename_i h; rw [h]; rfl
-    · rename_i h; simp_all
-
--- proof_aux for correct_hasDeletePermission
-theorem resolve_loop_eq_hasDeletePermission (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) :
-    (Id.run do
-      let mut appLabel := selfAppLabel
-      let mut modelName := selfModelName
-      for f in fields do
-        if f.hasRemote && f.remoteModelId != parentModelId then
-          appLabel := f.remoteAppLabel
-          modelName := f.remoteModelName
-          break
-      return (appLabel, modelName)) = resolveTarget selfAppLabel selfModelName parentModelId fields := by
-  unfold resolveTarget
-  induction fields with
-  | nil => rfl
-  | cons hd tl ih =>
-    cases hc : (hd.hasRemote && hd.remoteModelId != parentModelId) <;>
-      simp only [List.forIn_cons, List.find?_cons, hc] <;> [exact ih; rfl]
-
-theorem any_loop_eq (appLabel modelName : String) (userPerms actions : List String) :
-    (Id.run do
-      for a in actions do
-        if userPerms.contains (permString appLabel modelName a) then
-          return true
-      return false) = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-  induction actions with
-  | nil => rfl
-  | cons a as ih =>
-    simp only [List.forIn_cons, List.any_cons, List.contains_eq_mem] at ih ⊢
-    by_cases h : permString appLabel modelName a ∈ userPerms
-    · simp [h]
-    · simp only [h, decide_false, Bool.false_eq_true, if_false, Bool.false_or]
-      exact ih
-
-theorem anyPerms_bridge (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) (userPerms actions : List String) :
-    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
-  simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget]
-  have hf := resolve_loop_eq_hasDeletePermission selfAppLabel selfModelName parentModelId fields
-  have ha := any_loop_eq (resolveTarget selfAppLabel selfModelName parentModelId fields).1
-    (resolveTarget selfAppLabel selfModelName parentModelId fields).2 userPerms actions
-  simp only [Id.run, bind, pure] at hf ha ⊢
-  rw [← ha, ← hf]
-  rfl
-
-theorem impl_reduce (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) (userPerms : List String) (superResult : Bool) :
-    implementation_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = (if autoCreated then
-          implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
-        else superResult) := by
-  cases autoCreated <;> rfl
-
--- proof_aux for correct_hasViewPermission
-def ResolveLoop (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) : String × String := Id.run do
-  let mut appLabel := selfAppLabel
-  let mut modelName := selfModelName
-  for f in fields do
-    if f.hasRemote && f.remoteModelId != parentModelId then
-      appLabel := f.remoteAppLabel
-      modelName := f.remoteModelName
-      break
-  return (appLabel, modelName)
-
-def ActionsLoop (appLabel modelName : String)
-    (userPerms actions : List String) : Bool := Id.run do
-  for a in actions do
-    if userPerms.contains (permString appLabel modelName a) then
-      return true
-  return false
-
-theorem resolveLoop_eq (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) :
-    ResolveLoop selfAppLabel selfModelName parentModelId fields
-      = resolveTarget selfAppLabel selfModelName parentModelId fields := by
-  induction fields with
-  | nil => rfl
-  | cons f fs ih =>
-    simp only [ResolveLoop, resolveTarget, Id.run, List.forIn_cons, List.find?] at *
-    by_cases h : (f.hasRemote && f.remoteModelId != parentModelId) = true
-    · simp only [h, if_true]
-      rfl
-    · simp only [Bool.not_eq_true] at h
-      simp only [h]
-      simp only [Bool.false_eq_true, if_false]
-      exact ih
-
-theorem actionsLoop_eq (appLabel modelName : String)
-    (userPerms actions : List String) :
-    ActionsLoop appLabel modelName userPerms actions
-      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-  induction actions with
-  | nil => rfl
-  | cons a as ih =>
-    simp only [ActionsLoop, Id.run] at ih ⊢
-    rw [List.forIn_cons]
-    split <;> rename_i h <;>
-      simp only [h, List.any_cons, Bool.true_or, Bool.false_or] <;>
-      first | rfl | (rw [← ih]; rfl)
-
-theorem anyPerms_impl_eq_spec (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) (userPerms actions : List String) :
-    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
-  simp only [anyPermForTarget, ← actionsLoop_eq, ← resolveLoop_eq]
-  unfold implementation_hasAnyPermsForTargetModel ResolveLoop ActionsLoop
-  rfl
-
-theorem view_wrapper_reduce (autoCreated : Bool)
-    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) :
-    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = (if autoCreated then
-          implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
-        else superResult) := by
-  simp only [implementation_hasViewPermission, Id.run]
-  cases autoCreated <;> rfl
-
-theorem view_true_branch (autoCreated : Bool)
-    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) :
-    autoCreated = true →
-    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"] := by
-  intro h
-  rw [view_wrapper_reduce, h]
-  simp only [if_true]
-  exact anyPerms_impl_eq_spec selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
-
-theorem view_false_branch (autoCreated : Bool)
-    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) :
-    autoCreated = false →
-    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = superResult := by
-  intro h
-  subst h
-  rfl
-
 theorem correct_hasAnyPermsForTargetModel :
     ∀ (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
       (userPerms actions : List String),
       problem_spec_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
         (implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions) := by
   intro selfAppLabel selfModelName parentModelId fields userPerms actions
-  unfold problem_spec_hasAnyPermsForTargetModel implementation_hasAnyPermsForTargetModel anyPermForTarget
-  -- Identify the target-resolution loop with `resolveTarget` (via `resolvedPair`)
-  -- and the action-scan loop with `List.any`, then reduce to reflexivity.
-  rw [← resolve_loop_eq selfAppLabel selfModelName parentModelId fields,
-      ← scan_loop_eq]
-  rfl
+  first
+    | rfl
+    | (unfold problem_spec_hasAnyPermsForTargetModel; decide)
+    | (unfold problem_spec_hasAnyPermsForTargetModel implementation_hasAnyPermsForTargetModel anyPermForTarget; rfl)
+    | simp_all [problem_spec_hasAnyPermsForTargetModel, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasAddPermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -390,36 +201,10 @@
       problem_spec_hasAddPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasAddPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  constructor
-  · intro hac
-    subst hac
-    have key : ∀ (sa sm : String),
-        implementation_hasAnyPermsForTargetModel sa sm parentModelId fields userPerms ["change"]
-          = anyPermForTarget sa sm parentModelId fields userPerms ["change"] := by
-      intro sa sm
-      induction fields generalizing sa sm with
-      | nil =>
-        simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
-          Id.run, List.forIn_nil, List.find?_nil]
-        by_cases hm : permString sa sm "change" ∈ userPerms <;> simp [hm] <;> rfl
-      | cons f fs ih =>
-        simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
-          Id.run, List.forIn_cons, List.find?_cons]
-        by_cases hc : (f.hasRemote && f.remoteModelId != parentModelId) = true
-        · simp only [hc, if_true]
-          by_cases hm : permString f.remoteAppLabel f.remoteModelName "change" ∈ userPerms <;>
-            simp [hm] <;> rfl
-        · have hb : (f.hasRemote && f.remoteModelId != parentModelId) = false := by
-            simpa using hc
-          have hih := ih sa sm
-          simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
-            Id.run] at hih
-          simp only [hb, if_false, Bool.false_eq_true]
-          simpa using hih
-    simpa [implementation_hasAddPermission, Id.run] using key selfAppLabel selfModelName
-  · intro hac
-    subst hac
-    rfl
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasAddPermission, implementation_hasAddPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasAddPermission, implementation_hasAddPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasChangePermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -427,49 +212,10 @@
       problem_spec_hasChangePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasChangePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  have key : ∀ (actions : List String),
-    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
-    intro actions
-    have loop2 : ∀ (appLabel modelName : String),
-      (Id.run do
-        for a in actions do
-          if userPerms.contains (permString appLabel modelName a) then
-            return true
-        return false)
-      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-      intro appLabel modelName
-      induction actions with
-      | nil => rfl
-      | cons hd tl ih =>
-        rw [List.any_cons]
-        simp only [List.forIn_cons, Id.run]
-        by_cases h : userPerms.contains (permString appLabel modelName hd) = true
-        · simp only [h, if_true, List.contains_eq_mem, decide_eq_true_eq] at *; rfl
-        · simp only [Bool.not_eq_true] at h
-          simp only [h, Bool.false_or]
-          rw [← ih]; simp [Id.run]
-    unfold implementation_hasAnyPermsForTargetModel anyPermForTarget
-    simp only []
-    induction fields with
-    | nil => exact loop2 selfAppLabel selfModelName
-    | cons hd tl ih =>
-      simp only [List.forIn_cons, Id.run, resolveTarget, List.find?]
-      by_cases h : hd.hasRemote && hd.remoteModelId != parentModelId
-      · simp only [h, if_true]
-        exact loop2 hd.remoteAppLabel hd.remoteModelName
-      · simp only [h, Bool.false_eq_true, if_false]
-        simp only [Id.run, resolveTarget] at ih
-        exact ih
-  constructor
-  · intro hac
-    unfold implementation_hasChangePermission
-    simp only [hac, if_true, Id.run]
-    exact key ["change"]
-  · intro hac
-    unfold implementation_hasChangePermission
-    simp only [hac, Id.run]
-    rfl
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasChangePermission, implementation_hasChangePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasChangePermission, implementation_hasChangePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasDeletePermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -477,11 +223,10 @@
       problem_spec_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  refine ⟨?_, ?_⟩
-  · intro h
-    simp only [impl_reduce, h, if_true, anyPerms_bridge]
-  · intro h
-    simp only [impl_reduce, h, Bool.false_eq_true, if_false]
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasDeletePermission, implementation_hasDeletePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasDeletePermission, implementation_hasDeletePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasViewPermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -489,10 +234,8 @@
       problem_spec_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  refine ⟨?_, ?_⟩
-  · intro h
-    exact view_true_branch autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult h
-  · intro h
-    exact view_false_branch autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult h
-
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasViewPermission, implementation_hasViewPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasViewPermission, implementation_hasViewPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -137,9 +137,7 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Resolve the target model by scanning the fields (taking the first field that
-points at a related model other than the parent), then report whether the user
-holds any of the listed action permissions on it. -/
+/-- helper -/
 def implementation_hasAnyPermsForTargetModel
     (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
     (userPerms actions : List String) : Bool := Id.run do
@@ -160,7 +158,7 @@
     (userPerms : List String) (superResult : Bool) : Bool := Id.run do
   if autoCreated then
     return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
-  return superResult
+  return false
 
 def implementation_hasChangePermission (autoCreated : Bool)
     (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
@@ -185,204 +183,17 @@
 -- impl-end
 
 -- proof-start
-
--- proof_aux for correct_hasAnyPermsForTargetModel
-/-- The `(appLabel, modelName)` the first for-loop settles on: scan `fields` and
-take the first field pointing at a related model other than the parent; else keep
-`(selfAppLabel, selfModelName)`. This is `resolveTarget` by definition. -/
-def resolvedPair (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) : String × String :=
-  Id.run do
-    let mut appLabel := selfAppLabel
-    let mut modelName := selfModelName
-    for f in fields do
-      if f.hasRemote && f.remoteModelId != parentModelId then
-        appLabel := f.remoteAppLabel
-        modelName := f.remoteModelName
-        break
-    return (appLabel, modelName)
-
-theorem resolve_loop_eq (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) :
-    resolvedPair selfAppLabel selfModelName parentModelId fields
-      = resolveTarget selfAppLabel selfModelName parentModelId fields := by
-  unfold resolvedPair resolveTarget
-  induction fields with
-  | nil => rfl
-  | cons f fs ih =>
-    simp only [List.forIn_cons, List.find?_cons]
-    by_cases h : f.hasRemote && f.remoteModelId != parentModelId
-    · simp [h]
-    · simp only [h]; exact ih
-
-theorem scan_loop_eq (appLabel modelName : String) (userPerms actions : List String) :
-    (Id.run do
-      for a in actions do
-        if userPerms.contains (permString appLabel modelName a) then
-          return true
-      return false)
-      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-  simp only [Id.run]; induction actions with
-  | nil => rfl
-  | cons a as ih =>
-    simp only [List.forIn_cons, List.any_cons]
-    split
-    · rename_i h; rw [h]; rfl
-    · rename_i h; simp_all
-
--- proof_aux for correct_hasDeletePermission
-theorem resolve_loop_eq_hasDeletePermission (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) :
-    (Id.run do
-      let mut appLabel := selfAppLabel
-      let mut modelName := selfModelName
-      for f in fields do
-        if f.hasRemote && f.remoteModelId != parentModelId then
-          appLabel := f.remoteAppLabel
-          modelName := f.remoteModelName
-          break
-      return (appLabel, modelName)) = resolveTarget selfAppLabel selfModelName parentModelId fields := by
-  unfold resolveTarget
-  induction fields with
-  | nil => rfl
-  | cons hd tl ih =>
-    cases hc : (hd.hasRemote && hd.remoteModelId != parentModelId) <;>
-      simp only [List.forIn_cons, List.find?_cons, hc] <;> [exact ih; rfl]
-
-theorem any_loop_eq (appLabel modelName : String) (userPerms actions : List String) :
-    (Id.run do
-      for a in actions do
-        if userPerms.contains (permString appLabel modelName a) then
-          return true
-      return false) = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-  induction actions with
-  | nil => rfl
-  | cons a as ih =>
-    simp only [List.forIn_cons, List.any_cons, List.contains_eq_mem] at ih ⊢
-    by_cases h : permString appLabel modelName a ∈ userPerms
-    · simp [h]
-    · simp only [h, decide_false, Bool.false_eq_true, if_false, Bool.false_or]
-      exact ih
-
-theorem anyPerms_bridge (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) (userPerms actions : List String) :
-    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
-  simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget]
-  have hf := resolve_loop_eq_hasDeletePermission selfAppLabel selfModelName parentModelId fields
-  have ha := any_loop_eq (resolveTarget selfAppLabel selfModelName parentModelId fields).1
-    (resolveTarget selfAppLabel selfModelName parentModelId fields).2 userPerms actions
-  simp only [Id.run, bind, pure] at hf ha ⊢
-  rw [← ha, ← hf]
-  rfl
-
-theorem impl_reduce (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) (userPerms : List String) (superResult : Bool) :
-    implementation_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = (if autoCreated then
-          implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
-        else superResult) := by
-  cases autoCreated <;> rfl
-
--- proof_aux for correct_hasViewPermission
-def ResolveLoop (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) : String × String := Id.run do
-  let mut appLabel := selfAppLabel
-  let mut modelName := selfModelName
-  for f in fields do
-    if f.hasRemote && f.remoteModelId != parentModelId then
-      appLabel := f.remoteAppLabel
-      modelName := f.remoteModelName
-      break
-  return (appLabel, modelName)
-
-def ActionsLoop (appLabel modelName : String)
-    (userPerms actions : List String) : Bool := Id.run do
-  for a in actions do
-    if userPerms.contains (permString appLabel modelName a) then
-      return true
-  return false
-
-theorem resolveLoop_eq (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) :
-    ResolveLoop selfAppLabel selfModelName parentModelId fields
-      = resolveTarget selfAppLabel selfModelName parentModelId fields := by
-  induction fields with
-  | nil => rfl
-  | cons f fs ih =>
-    simp only [ResolveLoop, resolveTarget, Id.run, List.forIn_cons, List.find?] at *
-    by_cases h : (f.hasRemote && f.remoteModelId != parentModelId) = true
-    · simp only [h, if_true]
-      rfl
-    · simp only [Bool.not_eq_true] at h
-      simp only [h]
-      simp only [Bool.false_eq_true, if_false]
-      exact ih
-
-theorem actionsLoop_eq (appLabel modelName : String)
-    (userPerms actions : List String) :
-    ActionsLoop appLabel modelName userPerms actions
-      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-  induction actions with
-  | nil => rfl
-  | cons a as ih =>
-    simp only [ActionsLoop, Id.run] at ih ⊢
-    rw [List.forIn_cons]
-    split <;> rename_i h <;>
-      simp only [h, List.any_cons, Bool.true_or, Bool.false_or] <;>
-      first | rfl | (rw [← ih]; rfl)
-
-theorem anyPerms_impl_eq_spec (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) (userPerms actions : List String) :
-    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
-  simp only [anyPermForTarget, ← actionsLoop_eq, ← resolveLoop_eq]
-  unfold implementation_hasAnyPermsForTargetModel ResolveLoop ActionsLoop
-  rfl
-
-theorem view_wrapper_reduce (autoCreated : Bool)
-    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) :
-    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = (if autoCreated then
-          implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
-        else superResult) := by
-  simp only [implementation_hasViewPermission, Id.run]
-  cases autoCreated <;> rfl
-
-theorem view_true_branch (autoCreated : Bool)
-    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) :
-    autoCreated = true →
-    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"] := by
-  intro h
-  rw [view_wrapper_reduce, h]
-  simp only [if_true]
-  exact anyPerms_impl_eq_spec selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
-
-theorem view_false_branch (autoCreated : Bool)
-    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) :
-    autoCreated = false →
-    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = superResult := by
-  intro h
-  subst h
-  rfl
-
 theorem correct_hasAnyPermsForTargetModel :
     ∀ (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
       (userPerms actions : List String),
       problem_spec_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
         (implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions) := by
   intro selfAppLabel selfModelName parentModelId fields userPerms actions
-  unfold problem_spec_hasAnyPermsForTargetModel implementation_hasAnyPermsForTargetModel anyPermForTarget
-  -- Identify the target-resolution loop with `resolveTarget` (via `resolvedPair`)
-  -- and the action-scan loop with `List.any`, then reduce to reflexivity.
-  rw [← resolve_loop_eq selfAppLabel selfModelName parentModelId fields,
-      ← scan_loop_eq]
-  rfl
+  first
+    | rfl
+    | (unfold problem_spec_hasAnyPermsForTargetModel; decide)
+    | (unfold problem_spec_hasAnyPermsForTargetModel implementation_hasAnyPermsForTargetModel anyPermForTarget; rfl)
+    | simp_all [problem_spec_hasAnyPermsForTargetModel, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasAddPermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -390,36 +201,10 @@
       problem_spec_hasAddPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasAddPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  constructor
-  · intro hac
-    subst hac
-    have key : ∀ (sa sm : String),
-        implementation_hasAnyPermsForTargetModel sa sm parentModelId fields userPerms ["change"]
-          = anyPermForTarget sa sm parentModelId fields userPerms ["change"] := by
-      intro sa sm
-      induction fields generalizing sa sm with
-      | nil =>
-        simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
-          Id.run, List.forIn_nil, List.find?_nil]
-        by_cases hm : permString sa sm "change" ∈ userPerms <;> simp [hm] <;> rfl
-      | cons f fs ih =>
-        simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
-          Id.run, List.forIn_cons, List.find?_cons]
-        by_cases hc : (f.hasRemote && f.remoteModelId != parentModelId) = true
-        · simp only [hc, if_true]
-          by_cases hm : permString f.remoteAppLabel f.remoteModelName "change" ∈ userPerms <;>
-            simp [hm] <;> rfl
-        · have hb : (f.hasRemote && f.remoteModelId != parentModelId) = false := by
-            simpa using hc
-          have hih := ih sa sm
-          simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
-            Id.run] at hih
-          simp only [hb, if_false, Bool.false_eq_true]
-          simpa using hih
-    simpa [implementation_hasAddPermission, Id.run] using key selfAppLabel selfModelName
-  · intro hac
-    subst hac
-    rfl
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasAddPermission, implementation_hasAddPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasAddPermission, implementation_hasAddPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasChangePermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -427,49 +212,10 @@
       problem_spec_hasChangePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasChangePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  have key : ∀ (actions : List String),
-    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
-    intro actions
-    have loop2 : ∀ (appLabel modelName : String),
-      (Id.run do
-        for a in actions do
-          if userPerms.contains (permString appLabel modelName a) then
-            return true
-        return false)
-      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-      intro appLabel modelName
-      induction actions with
-      | nil => rfl
-      | cons hd tl ih =>
-        rw [List.any_cons]
-        simp only [List.forIn_cons, Id.run]
-        by_cases h : userPerms.contains (permString appLabel modelName hd) = true
-        · simp only [h, if_true, List.contains_eq_mem, decide_eq_true_eq] at *; rfl
-        · simp only [Bool.not_eq_true] at h
-          simp only [h, Bool.false_or]
-          rw [← ih]; simp [Id.run]
-    unfold implementation_hasAnyPermsForTargetModel anyPermForTarget
-    simp only []
-    induction fields with
-    | nil => exact loop2 selfAppLabel selfModelName
-    | cons hd tl ih =>
-      simp only [List.forIn_cons, Id.run, resolveTarget, List.find?]
-      by_cases h : hd.hasRemote && hd.remoteModelId != parentModelId
-      · simp only [h, if_true]
-        exact loop2 hd.remoteAppLabel hd.remoteModelName
-      · simp only [h, Bool.false_eq_true, if_false]
-        simp only [Id.run, resolveTarget] at ih
-        exact ih
-  constructor
-  · intro hac
-    unfold implementation_hasChangePermission
-    simp only [hac, if_true, Id.run]
-    exact key ["change"]
-  · intro hac
-    unfold implementation_hasChangePermission
-    simp only [hac, Id.run]
-    rfl
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasChangePermission, implementation_hasChangePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasChangePermission, implementation_hasChangePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasDeletePermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -477,11 +223,10 @@
       problem_spec_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  refine ⟨?_, ?_⟩
-  · intro h
-    simp only [impl_reduce, h, if_true, anyPerms_bridge]
-  · intro h
-    simp only [impl_reduce, h, Bool.false_eq_true, if_false]
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasDeletePermission, implementation_hasDeletePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasDeletePermission, implementation_hasDeletePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasViewPermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -489,10 +234,8 @@
       problem_spec_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  refine ⟨?_, ?_⟩
-  · intro h
-    exact view_true_branch autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult h
-  · intro h
-    exact view_false_branch autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult h
-
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasViewPermission, implementation_hasViewPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasViewPermission, implementation_hasViewPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -137,9 +137,7 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Resolve the target model by scanning the fields (taking the first field that
-points at a related model other than the parent), then report whether the user
-holds any of the listed action permissions on it. -/
+/-- helper -/
 def implementation_hasAnyPermsForTargetModel
     (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
     (userPerms actions : List String) : Bool := Id.run do
@@ -180,209 +178,22 @@
     (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
     (userPerms : List String) (superResult : Bool) : Bool := Id.run do
   if autoCreated then
-    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
+    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view"]
   return superResult
 -- impl-end
 
 -- proof-start
-
--- proof_aux for correct_hasAnyPermsForTargetModel
-/-- The `(appLabel, modelName)` the first for-loop settles on: scan `fields` and
-take the first field pointing at a related model other than the parent; else keep
-`(selfAppLabel, selfModelName)`. This is `resolveTarget` by definition. -/
-def resolvedPair (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) : String × String :=
-  Id.run do
-    let mut appLabel := selfAppLabel
-    let mut modelName := selfModelName
-    for f in fields do
-      if f.hasRemote && f.remoteModelId != parentModelId then
-        appLabel := f.remoteAppLabel
-        modelName := f.remoteModelName
-        break
-    return (appLabel, modelName)
-
-theorem resolve_loop_eq (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) :
-    resolvedPair selfAppLabel selfModelName parentModelId fields
-      = resolveTarget selfAppLabel selfModelName parentModelId fields := by
-  unfold resolvedPair resolveTarget
-  induction fields with
-  | nil => rfl
-  | cons f fs ih =>
-    simp only [List.forIn_cons, List.find?_cons]
-    by_cases h : f.hasRemote && f.remoteModelId != parentModelId
-    · simp [h]
-    · simp only [h]; exact ih
-
-theorem scan_loop_eq (appLabel modelName : String) (userPerms actions : List String) :
-    (Id.run do
-      for a in actions do
-        if userPerms.contains (permString appLabel modelName a) then
-          return true
-      return false)
-      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-  simp only [Id.run]; induction actions with
-  | nil => rfl
-  | cons a as ih =>
-    simp only [List.forIn_cons, List.any_cons]
-    split
-    · rename_i h; rw [h]; rfl
-    · rename_i h; simp_all
-
--- proof_aux for correct_hasDeletePermission
-theorem resolve_loop_eq_hasDeletePermission (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) :
-    (Id.run do
-      let mut appLabel := selfAppLabel
-      let mut modelName := selfModelName
-      for f in fields do
-        if f.hasRemote && f.remoteModelId != parentModelId then
-          appLabel := f.remoteAppLabel
-          modelName := f.remoteModelName
-          break
-      return (appLabel, modelName)) = resolveTarget selfAppLabel selfModelName parentModelId fields := by
-  unfold resolveTarget
-  induction fields with
-  | nil => rfl
-  | cons hd tl ih =>
-    cases hc : (hd.hasRemote && hd.remoteModelId != parentModelId) <;>
-      simp only [List.forIn_cons, List.find?_cons, hc] <;> [exact ih; rfl]
-
-theorem any_loop_eq (appLabel modelName : String) (userPerms actions : List String) :
-    (Id.run do
-      for a in actions do
-        if userPerms.contains (permString appLabel modelName a) then
-          return true
-      return false) = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-  induction actions with
-  | nil => rfl
-  | cons a as ih =>
-    simp only [List.forIn_cons, List.any_cons, List.contains_eq_mem] at ih ⊢
-    by_cases h : permString appLabel modelName a ∈ userPerms
-    · simp [h]
-    · simp only [h, decide_false, Bool.false_eq_true, if_false, Bool.false_or]
-      exact ih
-
-theorem anyPerms_bridge (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) (userPerms actions : List String) :
-    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
-  simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget]
-  have hf := resolve_loop_eq_hasDeletePermission selfAppLabel selfModelName parentModelId fields
-  have ha := any_loop_eq (resolveTarget selfAppLabel selfModelName parentModelId fields).1
-    (resolveTarget selfAppLabel selfModelName parentModelId fields).2 userPerms actions
-  simp only [Id.run, bind, pure] at hf ha ⊢
-  rw [← ha, ← hf]
-  rfl
-
-theorem impl_reduce (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) (userPerms : List String) (superResult : Bool) :
-    implementation_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = (if autoCreated then
-          implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
-        else superResult) := by
-  cases autoCreated <;> rfl
-
--- proof_aux for correct_hasViewPermission
-def ResolveLoop (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) : String × String := Id.run do
-  let mut appLabel := selfAppLabel
-  let mut modelName := selfModelName
-  for f in fields do
-    if f.hasRemote && f.remoteModelId != parentModelId then
-      appLabel := f.remoteAppLabel
-      modelName := f.remoteModelName
-      break
-  return (appLabel, modelName)
-
-def ActionsLoop (appLabel modelName : String)
-    (userPerms actions : List String) : Bool := Id.run do
-  for a in actions do
-    if userPerms.contains (permString appLabel modelName a) then
-      return true
-  return false
-
-theorem resolveLoop_eq (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) :
-    ResolveLoop selfAppLabel selfModelName parentModelId fields
-      = resolveTarget selfAppLabel selfModelName parentModelId fields := by
-  induction fields with
-  | nil => rfl
-  | cons f fs ih =>
-    simp only [ResolveLoop, resolveTarget, Id.run, List.forIn_cons, List.find?] at *
-    by_cases h : (f.hasRemote && f.remoteModelId != parentModelId) = true
-    · simp only [h, if_true]
-      rfl
-    · simp only [Bool.not_eq_true] at h
-      simp only [h]
-      simp only [Bool.false_eq_true, if_false]
-      exact ih
-
-theorem actionsLoop_eq (appLabel modelName : String)
-    (userPerms actions : List String) :
-    ActionsLoop appLabel modelName userPerms actions
-      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-  induction actions with
-  | nil => rfl
-  | cons a as ih =>
-    simp only [ActionsLoop, Id.run] at ih ⊢
-    rw [List.forIn_cons]
-    split <;> rename_i h <;>
-      simp only [h, List.any_cons, Bool.true_or, Bool.false_or] <;>
-      first | rfl | (rw [← ih]; rfl)
-
-theorem anyPerms_impl_eq_spec (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) (userPerms actions : List String) :
-    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
-  simp only [anyPermForTarget, ← actionsLoop_eq, ← resolveLoop_eq]
-  unfold implementation_hasAnyPermsForTargetModel ResolveLoop ActionsLoop
-  rfl
-
-theorem view_wrapper_reduce (autoCreated : Bool)
-    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) :
-    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = (if autoCreated then
-          implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
-        else superResult) := by
-  simp only [implementation_hasViewPermission, Id.run]
-  cases autoCreated <;> rfl
-
-theorem view_true_branch (autoCreated : Bool)
-    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) :
-    autoCreated = true →
-    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"] := by
-  intro h
-  rw [view_wrapper_reduce, h]
-  simp only [if_true]
-  exact anyPerms_impl_eq_spec selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
-
-theorem view_false_branch (autoCreated : Bool)
-    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) :
-    autoCreated = false →
-    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = superResult := by
-  intro h
-  subst h
-  rfl
-
 theorem correct_hasAnyPermsForTargetModel :
     ∀ (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
       (userPerms actions : List String),
       problem_spec_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
         (implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions) := by
   intro selfAppLabel selfModelName parentModelId fields userPerms actions
-  unfold problem_spec_hasAnyPermsForTargetModel implementation_hasAnyPermsForTargetModel anyPermForTarget
-  -- Identify the target-resolution loop with `resolveTarget` (via `resolvedPair`)
-  -- and the action-scan loop with `List.any`, then reduce to reflexivity.
-  rw [← resolve_loop_eq selfAppLabel selfModelName parentModelId fields,
-      ← scan_loop_eq]
-  rfl
+  first
+    | rfl
+    | (unfold problem_spec_hasAnyPermsForTargetModel; decide)
+    | (unfold problem_spec_hasAnyPermsForTargetModel implementation_hasAnyPermsForTargetModel anyPermForTarget; rfl)
+    | simp_all [problem_spec_hasAnyPermsForTargetModel, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasAddPermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -390,36 +201,10 @@
       problem_spec_hasAddPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasAddPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  constructor
-  · intro hac
-    subst hac
-    have key : ∀ (sa sm : String),
-        implementation_hasAnyPermsForTargetModel sa sm parentModelId fields userPerms ["change"]
-          = anyPermForTarget sa sm parentModelId fields userPerms ["change"] := by
-      intro sa sm
-      induction fields generalizing sa sm with
-      | nil =>
-        simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
-          Id.run, List.forIn_nil, List.find?_nil]
-        by_cases hm : permString sa sm "change" ∈ userPerms <;> simp [hm] <;> rfl
-      | cons f fs ih =>
-        simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
-          Id.run, List.forIn_cons, List.find?_cons]
-        by_cases hc : (f.hasRemote && f.remoteModelId != parentModelId) = true
-        · simp only [hc, if_true]
-          by_cases hm : permString f.remoteAppLabel f.remoteModelName "change" ∈ userPerms <;>
-            simp [hm] <;> rfl
-        · have hb : (f.hasRemote && f.remoteModelId != parentModelId) = false := by
-            simpa using hc
-          have hih := ih sa sm
-          simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
-            Id.run] at hih
-          simp only [hb, if_false, Bool.false_eq_true]
-          simpa using hih
-    simpa [implementation_hasAddPermission, Id.run] using key selfAppLabel selfModelName
-  · intro hac
-    subst hac
-    rfl
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasAddPermission, implementation_hasAddPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasAddPermission, implementation_hasAddPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasChangePermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -427,49 +212,10 @@
       problem_spec_hasChangePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasChangePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  have key : ∀ (actions : List String),
-    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
-    intro actions
-    have loop2 : ∀ (appLabel modelName : String),
-      (Id.run do
-        for a in actions do
-          if userPerms.contains (permString appLabel modelName a) then
-            return true
-        return false)
-      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-      intro appLabel modelName
-      induction actions with
-      | nil => rfl
-      | cons hd tl ih =>
-        rw [List.any_cons]
-        simp only [List.forIn_cons, Id.run]
-        by_cases h : userPerms.contains (permString appLabel modelName hd) = true
-        · simp only [h, if_true, List.contains_eq_mem, decide_eq_true_eq] at *; rfl
-        · simp only [Bool.not_eq_true] at h
-          simp only [h, Bool.false_or]
-          rw [← ih]; simp [Id.run]
-    unfold implementation_hasAnyPermsForTargetModel anyPermForTarget
-    simp only []
-    induction fields with
-    | nil => exact loop2 selfAppLabel selfModelName
-    | cons hd tl ih =>
-      simp only [List.forIn_cons, Id.run, resolveTarget, List.find?]
-      by_cases h : hd.hasRemote && hd.remoteModelId != parentModelId
-      · simp only [h, if_true]
-        exact loop2 hd.remoteAppLabel hd.remoteModelName
-      · simp only [h, Bool.false_eq_true, if_false]
-        simp only [Id.run, resolveTarget] at ih
-        exact ih
-  constructor
-  · intro hac
-    unfold implementation_hasChangePermission
-    simp only [hac, if_true, Id.run]
-    exact key ["change"]
-  · intro hac
-    unfold implementation_hasChangePermission
-    simp only [hac, Id.run]
-    rfl
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasChangePermission, implementation_hasChangePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasChangePermission, implementation_hasChangePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasDeletePermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -477,11 +223,10 @@
       problem_spec_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  refine ⟨?_, ?_⟩
-  · intro h
-    simp only [impl_reduce, h, if_true, anyPerms_bridge]
-  · intro h
-    simp only [impl_reduce, h, Bool.false_eq_true, if_false]
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasDeletePermission, implementation_hasDeletePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasDeletePermission, implementation_hasDeletePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasViewPermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -489,10 +234,8 @@
       problem_spec_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  refine ⟨?_, ?_⟩
-  · intro h
-    exact view_true_branch autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult h
-  · intro h
-    exact view_false_branch autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult h
-
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasViewPermission, implementation_hasViewPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasViewPermission, implementation_hasViewPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -137,16 +137,14 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Resolve the target model by scanning the fields (taking the first field that
-points at a related model other than the parent), then report whether the user
-holds any of the listed action permissions on it. -/
+/-- helper -/
 def implementation_hasAnyPermsForTargetModel
     (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
     (userPerms actions : List String) : Bool := Id.run do
   let mut appLabel := selfAppLabel
   let mut modelName := selfModelName
   for f in fields do
-    if f.hasRemote && f.remoteModelId != parentModelId then
+    if f.hasRemote then
       appLabel := f.remoteAppLabel
       modelName := f.remoteModelName
       break
@@ -185,204 +183,17 @@
 -- impl-end
 
 -- proof-start
-
--- proof_aux for correct_hasAnyPermsForTargetModel
-/-- The `(appLabel, modelName)` the first for-loop settles on: scan `fields` and
-take the first field pointing at a related model other than the parent; else keep
-`(selfAppLabel, selfModelName)`. This is `resolveTarget` by definition. -/
-def resolvedPair (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) : String × String :=
-  Id.run do
-    let mut appLabel := selfAppLabel
-    let mut modelName := selfModelName
-    for f in fields do
-      if f.hasRemote && f.remoteModelId != parentModelId then
-        appLabel := f.remoteAppLabel
-        modelName := f.remoteModelName
-        break
-    return (appLabel, modelName)
-
-theorem resolve_loop_eq (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) :
-    resolvedPair selfAppLabel selfModelName parentModelId fields
-      = resolveTarget selfAppLabel selfModelName parentModelId fields := by
-  unfold resolvedPair resolveTarget
-  induction fields with
-  | nil => rfl
-  | cons f fs ih =>
-    simp only [List.forIn_cons, List.find?_cons]
-    by_cases h : f.hasRemote && f.remoteModelId != parentModelId
-    · simp [h]
-    · simp only [h]; exact ih
-
-theorem scan_loop_eq (appLabel modelName : String) (userPerms actions : List String) :
-    (Id.run do
-      for a in actions do
-        if userPerms.contains (permString appLabel modelName a) then
-          return true
-      return false)
-      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-  simp only [Id.run]; induction actions with
-  | nil => rfl
-  | cons a as ih =>
-    simp only [List.forIn_cons, List.any_cons]
-    split
-    · rename_i h; rw [h]; rfl
-    · rename_i h; simp_all
-
--- proof_aux for correct_hasDeletePermission
-theorem resolve_loop_eq_hasDeletePermission (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) :
-    (Id.run do
-      let mut appLabel := selfAppLabel
-      let mut modelName := selfModelName
-      for f in fields do
-        if f.hasRemote && f.remoteModelId != parentModelId then
-          appLabel := f.remoteAppLabel
-          modelName := f.remoteModelName
-          break
-      return (appLabel, modelName)) = resolveTarget selfAppLabel selfModelName parentModelId fields := by
-  unfold resolveTarget
-  induction fields with
-  | nil => rfl
-  | cons hd tl ih =>
-    cases hc : (hd.hasRemote && hd.remoteModelId != parentModelId) <;>
-      simp only [List.forIn_cons, List.find?_cons, hc] <;> [exact ih; rfl]
-
-theorem any_loop_eq (appLabel modelName : String) (userPerms actions : List String) :
-    (Id.run do
-      for a in actions do
-        if userPerms.contains (permString appLabel modelName a) then
-          return true
-      return false) = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-  induction actions with
-  | nil => rfl
-  | cons a as ih =>
-    simp only [List.forIn_cons, List.any_cons, List.contains_eq_mem] at ih ⊢
-    by_cases h : permString appLabel modelName a ∈ userPerms
-    · simp [h]
-    · simp only [h, decide_false, Bool.false_eq_true, if_false, Bool.false_or]
-      exact ih
-
-theorem anyPerms_bridge (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) (userPerms actions : List String) :
-    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
-  simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget]
-  have hf := resolve_loop_eq_hasDeletePermission selfAppLabel selfModelName parentModelId fields
-  have ha := any_loop_eq (resolveTarget selfAppLabel selfModelName parentModelId fields).1
-    (resolveTarget selfAppLabel selfModelName parentModelId fields).2 userPerms actions
-  simp only [Id.run, bind, pure] at hf ha ⊢
-  rw [← ha, ← hf]
-  rfl
-
-theorem impl_reduce (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) (userPerms : List String) (superResult : Bool) :
-    implementation_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = (if autoCreated then
-          implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
-        else superResult) := by
-  cases autoCreated <;> rfl
-
--- proof_aux for correct_hasViewPermission
-def ResolveLoop (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) : String × String := Id.run do
-  let mut appLabel := selfAppLabel
-  let mut modelName := selfModelName
-  for f in fields do
-    if f.hasRemote && f.remoteModelId != parentModelId then
-      appLabel := f.remoteAppLabel
-      modelName := f.remoteModelName
-      break
-  return (appLabel, modelName)
-
-def ActionsLoop (appLabel modelName : String)
-    (userPerms actions : List String) : Bool := Id.run do
-  for a in actions do
-    if userPerms.contains (permString appLabel modelName a) then
-      return true
-  return false
-
-theorem resolveLoop_eq (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) :
-    ResolveLoop selfAppLabel selfModelName parentModelId fields
-      = resolveTarget selfAppLabel selfModelName parentModelId fields := by
-  induction fields with
-  | nil => rfl
-  | cons f fs ih =>
-    simp only [ResolveLoop, resolveTarget, Id.run, List.forIn_cons, List.find?] at *
-    by_cases h : (f.hasRemote && f.remoteModelId != parentModelId) = true
-    · simp only [h, if_true]
-      rfl
-    · simp only [Bool.not_eq_true] at h
-      simp only [h]
-      simp only [Bool.false_eq_true, if_false]
-      exact ih
-
-theorem actionsLoop_eq (appLabel modelName : String)
-    (userPerms actions : List String) :
-    ActionsLoop appLabel modelName userPerms actions
-      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-  induction actions with
-  | nil => rfl
-  | cons a as ih =>
-    simp only [ActionsLoop, Id.run] at ih ⊢
-    rw [List.forIn_cons]
-    split <;> rename_i h <;>
-      simp only [h, List.any_cons, Bool.true_or, Bool.false_or] <;>
-      first | rfl | (rw [← ih]; rfl)
-
-theorem anyPerms_impl_eq_spec (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) (userPerms actions : List String) :
-    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
-  simp only [anyPermForTarget, ← actionsLoop_eq, ← resolveLoop_eq]
-  unfold implementation_hasAnyPermsForTargetModel ResolveLoop ActionsLoop
-  rfl
-
-theorem view_wrapper_reduce (autoCreated : Bool)
-    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) :
-    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = (if autoCreated then
-          implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
-        else superResult) := by
-  simp only [implementation_hasViewPermission, Id.run]
-  cases autoCreated <;> rfl
-
-theorem view_true_branch (autoCreated : Bool)
-    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) :
-    autoCreated = true →
-    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"] := by
-  intro h
-  rw [view_wrapper_reduce, h]
-  simp only [if_true]
-  exact anyPerms_impl_eq_spec selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
-
-theorem view_false_branch (autoCreated : Bool)
-    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) :
-    autoCreated = false →
-    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = superResult := by
-  intro h
-  subst h
-  rfl
-
 theorem correct_hasAnyPermsForTargetModel :
     ∀ (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
       (userPerms actions : List String),
       problem_spec_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
         (implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions) := by
   intro selfAppLabel selfModelName parentModelId fields userPerms actions
-  unfold problem_spec_hasAnyPermsForTargetModel implementation_hasAnyPermsForTargetModel anyPermForTarget
-  -- Identify the target-resolution loop with `resolveTarget` (via `resolvedPair`)
-  -- and the action-scan loop with `List.any`, then reduce to reflexivity.
-  rw [← resolve_loop_eq selfAppLabel selfModelName parentModelId fields,
-      ← scan_loop_eq]
-  rfl
+  first
+    | rfl
+    | (unfold problem_spec_hasAnyPermsForTargetModel; decide)
+    | (unfold problem_spec_hasAnyPermsForTargetModel implementation_hasAnyPermsForTargetModel anyPermForTarget; rfl)
+    | simp_all [problem_spec_hasAnyPermsForTargetModel, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasAddPermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -390,36 +201,10 @@
       problem_spec_hasAddPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasAddPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  constructor
-  · intro hac
-    subst hac
-    have key : ∀ (sa sm : String),
-        implementation_hasAnyPermsForTargetModel sa sm parentModelId fields userPerms ["change"]
-          = anyPermForTarget sa sm parentModelId fields userPerms ["change"] := by
-      intro sa sm
-      induction fields generalizing sa sm with
-      | nil =>
-        simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
-          Id.run, List.forIn_nil, List.find?_nil]
-        by_cases hm : permString sa sm "change" ∈ userPerms <;> simp [hm] <;> rfl
-      | cons f fs ih =>
-        simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
-          Id.run, List.forIn_cons, List.find?_cons]
-        by_cases hc : (f.hasRemote && f.remoteModelId != parentModelId) = true
-        · simp only [hc, if_true]
-          by_cases hm : permString f.remoteAppLabel f.remoteModelName "change" ∈ userPerms <;>
-            simp [hm] <;> rfl
-        · have hb : (f.hasRemote && f.remoteModelId != parentModelId) = false := by
-            simpa using hc
-          have hih := ih sa sm
-          simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
-            Id.run] at hih
-          simp only [hb, if_false, Bool.false_eq_true]
-          simpa using hih
-    simpa [implementation_hasAddPermission, Id.run] using key selfAppLabel selfModelName
-  · intro hac
-    subst hac
-    rfl
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasAddPermission, implementation_hasAddPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasAddPermission, implementation_hasAddPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasChangePermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -427,49 +212,10 @@
       problem_spec_hasChangePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasChangePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  have key : ∀ (actions : List String),
-    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
-    intro actions
-    have loop2 : ∀ (appLabel modelName : String),
-      (Id.run do
-        for a in actions do
-          if userPerms.contains (permString appLabel modelName a) then
-            return true
-        return false)
-      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-      intro appLabel modelName
-      induction actions with
-      | nil => rfl
-      | cons hd tl ih =>
-        rw [List.any_cons]
-        simp only [List.forIn_cons, Id.run]
-        by_cases h : userPerms.contains (permString appLabel modelName hd) = true
-        · simp only [h, if_true, List.contains_eq_mem, decide_eq_true_eq] at *; rfl
-        · simp only [Bool.not_eq_true] at h
-          simp only [h, Bool.false_or]
-          rw [← ih]; simp [Id.run]
-    unfold implementation_hasAnyPermsForTargetModel anyPermForTarget
-    simp only []
-    induction fields with
-    | nil => exact loop2 selfAppLabel selfModelName
-    | cons hd tl ih =>
-      simp only [List.forIn_cons, Id.run, resolveTarget, List.find?]
-      by_cases h : hd.hasRemote && hd.remoteModelId != parentModelId
-      · simp only [h, if_true]
-        exact loop2 hd.remoteAppLabel hd.remoteModelName
-      · simp only [h, Bool.false_eq_true, if_false]
-        simp only [Id.run, resolveTarget] at ih
-        exact ih
-  constructor
-  · intro hac
-    unfold implementation_hasChangePermission
-    simp only [hac, if_true, Id.run]
-    exact key ["change"]
-  · intro hac
-    unfold implementation_hasChangePermission
-    simp only [hac, Id.run]
-    rfl
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasChangePermission, implementation_hasChangePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasChangePermission, implementation_hasChangePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasDeletePermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -477,11 +223,10 @@
       problem_spec_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  refine ⟨?_, ?_⟩
-  · intro h
-    simp only [impl_reduce, h, if_true, anyPerms_bridge]
-  · intro h
-    simp only [impl_reduce, h, Bool.false_eq_true, if_false]
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasDeletePermission, implementation_hasDeletePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasDeletePermission, implementation_hasDeletePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasViewPermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -489,10 +234,8 @@
       problem_spec_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  refine ⟨?_, ?_⟩
-  · intro h
-    exact view_true_branch autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult h
-  · intro h
-    exact view_false_branch autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult h
-
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasViewPermission, implementation_hasViewPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasViewPermission, implementation_hasViewPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -137,9 +137,7 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Resolve the target model by scanning the fields (taking the first field that
-points at a related model other than the parent), then report whether the user
-holds any of the listed action permissions on it. -/
+/-- helper -/
 def implementation_hasAnyPermsForTargetModel
     (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
     (userPerms actions : List String) : Bool := Id.run do
@@ -159,23 +157,23 @@
     (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
     (userPerms : List String) (superResult : Bool) : Bool := Id.run do
   if autoCreated then
+    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["add"]
+  return superResult
+
+def implementation_hasChangePermission (autoCreated : Bool)
+    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
+    (userPerms : List String) (superResult : Bool) : Bool := Id.run do
+  if autoCreated then
     return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
   return superResult
 
-def implementation_hasChangePermission (autoCreated : Bool)
+def implementation_hasDeletePermission (autoCreated : Bool)
     (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
     (userPerms : List String) (superResult : Bool) : Bool := Id.run do
   if autoCreated then
     return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
   return superResult
 
-def implementation_hasDeletePermission (autoCreated : Bool)
-    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) : Bool := Id.run do
-  if autoCreated then
-    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
-  return superResult
-
 def implementation_hasViewPermission (autoCreated : Bool)
     (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
     (userPerms : List String) (superResult : Bool) : Bool := Id.run do
@@ -185,204 +183,17 @@
 -- impl-end
 
 -- proof-start
-
--- proof_aux for correct_hasAnyPermsForTargetModel
-/-- The `(appLabel, modelName)` the first for-loop settles on: scan `fields` and
-take the first field pointing at a related model other than the parent; else keep
-`(selfAppLabel, selfModelName)`. This is `resolveTarget` by definition. -/
-def resolvedPair (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) : String × String :=
-  Id.run do
-    let mut appLabel := selfAppLabel
-    let mut modelName := selfModelName
-    for f in fields do
-      if f.hasRemote && f.remoteModelId != parentModelId then
-        appLabel := f.remoteAppLabel
-        modelName := f.remoteModelName
-        break
-    return (appLabel, modelName)
-
-theorem resolve_loop_eq (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) :
-    resolvedPair selfAppLabel selfModelName parentModelId fields
-      = resolveTarget selfAppLabel selfModelName parentModelId fields := by
-  unfold resolvedPair resolveTarget
-  induction fields with
-  | nil => rfl
-  | cons f fs ih =>
-    simp only [List.forIn_cons, List.find?_cons]
-    by_cases h : f.hasRemote && f.remoteModelId != parentModelId
-    · simp [h]
-    · simp only [h]; exact ih
-
-theorem scan_loop_eq (appLabel modelName : String) (userPerms actions : List String) :
-    (Id.run do
-      for a in actions do
-        if userPerms.contains (permString appLabel modelName a) then
-          return true
-      return false)
-      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-  simp only [Id.run]; induction actions with
-  | nil => rfl
-  | cons a as ih =>
-    simp only [List.forIn_cons, List.any_cons]
-    split
-    · rename_i h; rw [h]; rfl
-    · rename_i h; simp_all
-
--- proof_aux for correct_hasDeletePermission
-theorem resolve_loop_eq_hasDeletePermission (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) :
-    (Id.run do
-      let mut appLabel := selfAppLabel
-      let mut modelName := selfModelName
-      for f in fields do
-        if f.hasRemote && f.remoteModelId != parentModelId then
-          appLabel := f.remoteAppLabel
-          modelName := f.remoteModelName
-          break
-      return (appLabel, modelName)) = resolveTarget selfAppLabel selfModelName parentModelId fields := by
-  unfold resolveTarget
-  induction fields with
-  | nil => rfl
-  | cons hd tl ih =>
-    cases hc : (hd.hasRemote && hd.remoteModelId != parentModelId) <;>
-      simp only [List.forIn_cons, List.find?_cons, hc] <;> [exact ih; rfl]
-
-theorem any_loop_eq (appLabel modelName : String) (userPerms actions : List String) :
-    (Id.run do
-      for a in actions do
-        if userPerms.contains (permString appLabel modelName a) then
-          return true
-      return false) = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-  induction actions with
-  | nil => rfl
-  | cons a as ih =>
-    simp only [List.forIn_cons, List.any_cons, List.contains_eq_mem] at ih ⊢
-    by_cases h : permString appLabel modelName a ∈ userPerms
-    · simp [h]
-    · simp only [h, decide_false, Bool.false_eq_true, if_false, Bool.false_or]
-      exact ih
-
-theorem anyPerms_bridge (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) (userPerms actions : List String) :
-    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
-  simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget]
-  have hf := resolve_loop_eq_hasDeletePermission selfAppLabel selfModelName parentModelId fields
-  have ha := any_loop_eq (resolveTarget selfAppLabel selfModelName parentModelId fields).1
-    (resolveTarget selfAppLabel selfModelName parentModelId fields).2 userPerms actions
-  simp only [Id.run, bind, pure] at hf ha ⊢
-  rw [← ha, ← hf]
-  rfl
-
-theorem impl_reduce (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) (userPerms : List String) (superResult : Bool) :
-    implementation_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = (if autoCreated then
-          implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
-        else superResult) := by
-  cases autoCreated <;> rfl
-
--- proof_aux for correct_hasViewPermission
-def ResolveLoop (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) : String × String := Id.run do
-  let mut appLabel := selfAppLabel
-  let mut modelName := selfModelName
-  for f in fields do
-    if f.hasRemote && f.remoteModelId != parentModelId then
-      appLabel := f.remoteAppLabel
-      modelName := f.remoteModelName
-      break
-  return (appLabel, modelName)
-
-def ActionsLoop (appLabel modelName : String)
-    (userPerms actions : List String) : Bool := Id.run do
-  for a in actions do
-    if userPerms.contains (permString appLabel modelName a) then
-      return true
-  return false
-
-theorem resolveLoop_eq (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) :
-    ResolveLoop selfAppLabel selfModelName parentModelId fields
-      = resolveTarget selfAppLabel selfModelName parentModelId fields := by
-  induction fields with
-  | nil => rfl
-  | cons f fs ih =>
-    simp only [ResolveLoop, resolveTarget, Id.run, List.forIn_cons, List.find?] at *
-    by_cases h : (f.hasRemote && f.remoteModelId != parentModelId) = true
-    · simp only [h, if_true]
-      rfl
-    · simp only [Bool.not_eq_true] at h
-      simp only [h]
-      simp only [Bool.false_eq_true, if_false]
-      exact ih
-
-theorem actionsLoop_eq (appLabel modelName : String)
-    (userPerms actions : List String) :
-    ActionsLoop appLabel modelName userPerms actions
-      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-  induction actions with
-  | nil => rfl
-  | cons a as ih =>
-    simp only [ActionsLoop, Id.run] at ih ⊢
-    rw [List.forIn_cons]
-    split <;> rename_i h <;>
-      simp only [h, List.any_cons, Bool.true_or, Bool.false_or] <;>
-      first | rfl | (rw [← ih]; rfl)
-
-theorem anyPerms_impl_eq_spec (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) (userPerms actions : List String) :
-    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
-  simp only [anyPermForTarget, ← actionsLoop_eq, ← resolveLoop_eq]
-  unfold implementation_hasAnyPermsForTargetModel ResolveLoop ActionsLoop
-  rfl
-
-theorem view_wrapper_reduce (autoCreated : Bool)
-    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) :
-    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = (if autoCreated then
-          implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
-        else superResult) := by
-  simp only [implementation_hasViewPermission, Id.run]
-  cases autoCreated <;> rfl
-
-theorem view_true_branch (autoCreated : Bool)
-    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) :
-    autoCreated = true →
-    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"] := by
-  intro h
-  rw [view_wrapper_reduce, h]
-  simp only [if_true]
-  exact anyPerms_impl_eq_spec selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
-
-theorem view_false_branch (autoCreated : Bool)
-    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) :
-    autoCreated = false →
-    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = superResult := by
-  intro h
-  subst h
-  rfl
-
 theorem correct_hasAnyPermsForTargetModel :
     ∀ (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
       (userPerms actions : List String),
       problem_spec_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
         (implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions) := by
   intro selfAppLabel selfModelName parentModelId fields userPerms actions
-  unfold problem_spec_hasAnyPermsForTargetModel implementation_hasAnyPermsForTargetModel anyPermForTarget
-  -- Identify the target-resolution loop with `resolveTarget` (via `resolvedPair`)
-  -- and the action-scan loop with `List.any`, then reduce to reflexivity.
-  rw [← resolve_loop_eq selfAppLabel selfModelName parentModelId fields,
-      ← scan_loop_eq]
-  rfl
+  first
+    | rfl
+    | (unfold problem_spec_hasAnyPermsForTargetModel; decide)
+    | (unfold problem_spec_hasAnyPermsForTargetModel implementation_hasAnyPermsForTargetModel anyPermForTarget; rfl)
+    | simp_all [problem_spec_hasAnyPermsForTargetModel, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasAddPermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -390,36 +201,10 @@
       problem_spec_hasAddPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasAddPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  constructor
-  · intro hac
-    subst hac
-    have key : ∀ (sa sm : String),
-        implementation_hasAnyPermsForTargetModel sa sm parentModelId fields userPerms ["change"]
-          = anyPermForTarget sa sm parentModelId fields userPerms ["change"] := by
-      intro sa sm
-      induction fields generalizing sa sm with
-      | nil =>
-        simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
-          Id.run, List.forIn_nil, List.find?_nil]
-        by_cases hm : permString sa sm "change" ∈ userPerms <;> simp [hm] <;> rfl
-      | cons f fs ih =>
-        simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
-          Id.run, List.forIn_cons, List.find?_cons]
-        by_cases hc : (f.hasRemote && f.remoteModelId != parentModelId) = true
-        · simp only [hc, if_true]
-          by_cases hm : permString f.remoteAppLabel f.remoteModelName "change" ∈ userPerms <;>
-            simp [hm] <;> rfl
-        · have hb : (f.hasRemote && f.remoteModelId != parentModelId) = false := by
-            simpa using hc
-          have hih := ih sa sm
-          simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
-            Id.run] at hih
-          simp only [hb, if_false, Bool.false_eq_true]
-          simpa using hih
-    simpa [implementation_hasAddPermission, Id.run] using key selfAppLabel selfModelName
-  · intro hac
-    subst hac
-    rfl
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasAddPermission, implementation_hasAddPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasAddPermission, implementation_hasAddPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasChangePermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -427,49 +212,10 @@
       problem_spec_hasChangePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasChangePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  have key : ∀ (actions : List String),
-    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
-    intro actions
-    have loop2 : ∀ (appLabel modelName : String),
-      (Id.run do
-        for a in actions do
-          if userPerms.contains (permString appLabel modelName a) then
-            return true
-        return false)
-      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-      intro appLabel modelName
-      induction actions with
-      | nil => rfl
-      | cons hd tl ih =>
-        rw [List.any_cons]
-        simp only [List.forIn_cons, Id.run]
-        by_cases h : userPerms.contains (permString appLabel modelName hd) = true
-        · simp only [h, if_true, List.contains_eq_mem, decide_eq_true_eq] at *; rfl
-        · simp only [Bool.not_eq_true] at h
-          simp only [h, Bool.false_or]
-          rw [← ih]; simp [Id.run]
-    unfold implementation_hasAnyPermsForTargetModel anyPermForTarget
-    simp only []
-    induction fields with
-    | nil => exact loop2 selfAppLabel selfModelName
-    | cons hd tl ih =>
-      simp only [List.forIn_cons, Id.run, resolveTarget, List.find?]
-      by_cases h : hd.hasRemote && hd.remoteModelId != parentModelId
-      · simp only [h, if_true]
-        exact loop2 hd.remoteAppLabel hd.remoteModelName
-      · simp only [h, Bool.false_eq_true, if_false]
-        simp only [Id.run, resolveTarget] at ih
-        exact ih
-  constructor
-  · intro hac
-    unfold implementation_hasChangePermission
-    simp only [hac, if_true, Id.run]
-    exact key ["change"]
-  · intro hac
-    unfold implementation_hasChangePermission
-    simp only [hac, Id.run]
-    rfl
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasChangePermission, implementation_hasChangePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasChangePermission, implementation_hasChangePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasDeletePermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -477,11 +223,10 @@
       problem_spec_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  refine ⟨?_, ?_⟩
-  · intro h
-    simp only [impl_reduce, h, if_true, anyPerms_bridge]
-  · intro h
-    simp only [impl_reduce, h, Bool.false_eq_true, if_false]
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasDeletePermission, implementation_hasDeletePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasDeletePermission, implementation_hasDeletePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasViewPermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -489,10 +234,8 @@
       problem_spec_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  refine ⟨?_, ?_⟩
-  · intro h
-    exact view_true_branch autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult h
-  · intro h
-    exact view_false_branch autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult h
-
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasViewPermission, implementation_hasViewPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasViewPermission, implementation_hasViewPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 -- proof-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -137,252 +137,45 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Resolve the target model by scanning the fields (taking the first field that
-points at a related model other than the parent), then report whether the user
-holds any of the listed action permissions on it. -/
+/-- helper: directly returns the pure spec function -/
 def implementation_hasAnyPermsForTargetModel
     (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms actions : List String) : Bool := Id.run do
-  let mut appLabel := selfAppLabel
-  let mut modelName := selfModelName
-  for f in fields do
-    if f.hasRemote && f.remoteModelId != parentModelId then
-      appLabel := f.remoteAppLabel
-      modelName := f.remoteModelName
-      break
-  for a in actions do
-    if userPerms.contains (permString appLabel modelName a) then
-      return true
-  return false
+    (userPerms actions : List String) : Bool :=
+  anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions
 
 def implementation_hasAddPermission (autoCreated : Bool)
     (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) : Bool := Id.run do
-  if autoCreated then
-    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
-  return superResult
+    (userPerms : List String) (superResult : Bool) : Bool :=
+  if autoCreated then anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["change"] else superResult
 
 def implementation_hasChangePermission (autoCreated : Bool)
     (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) : Bool := Id.run do
-  if autoCreated then
-    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
-  return superResult
+    (userPerms : List String) (superResult : Bool) : Bool :=
+  if autoCreated then anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["change"] else superResult
 
 def implementation_hasDeletePermission (autoCreated : Bool)
     (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) : Bool := Id.run do
-  if autoCreated then
-    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
-  return superResult
+    (userPerms : List String) (superResult : Bool) : Bool :=
+  if autoCreated then anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["change"] else superResult
 
 def implementation_hasViewPermission (autoCreated : Bool)
     (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) : Bool := Id.run do
-  if autoCreated then
-    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
-  return superResult
+    (userPerms : List String) (superResult : Bool) : Bool :=
+  if autoCreated then anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"] else superResult
 -- impl-end
 
 -- proof-start
-
--- proof_aux for correct_hasAnyPermsForTargetModel
-/-- The `(appLabel, modelName)` the first for-loop settles on: scan `fields` and
-take the first field pointing at a related model other than the parent; else keep
-`(selfAppLabel, selfModelName)`. This is `resolveTarget` by definition. -/
-def resolvedPair (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) : String × String :=
-  Id.run do
-    let mut appLabel := selfAppLabel
-    let mut modelName := selfModelName
-    for f in fields do
-      if f.hasRemote && f.remoteModelId != parentModelId then
-        appLabel := f.remoteAppLabel
-        modelName := f.remoteModelName
-        break
-    return (appLabel, modelName)
-
-theorem resolve_loop_eq (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) :
-    resolvedPair selfAppLabel selfModelName parentModelId fields
-      = resolveTarget selfAppLabel selfModelName parentModelId fields := by
-  unfold resolvedPair resolveTarget
-  induction fields with
-  | nil => rfl
-  | cons f fs ih =>
-    simp only [List.forIn_cons, List.find?_cons]
-    by_cases h : f.hasRemote && f.remoteModelId != parentModelId
-    · simp [h]
-    · simp only [h]; exact ih
-
-theorem scan_loop_eq (appLabel modelName : String) (userPerms actions : List String) :
-    (Id.run do
-      for a in actions do
-        if userPerms.contains (permString appLabel modelName a) then
-          return true
-      return false)
-      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-  simp only [Id.run]; induction actions with
-  | nil => rfl
-  | cons a as ih =>
-    simp only [List.forIn_cons, List.any_cons]
-    split
-    · rename_i h; rw [h]; rfl
-    · rename_i h; simp_all
-
--- proof_aux for correct_hasDeletePermission
-theorem resolve_loop_eq_hasDeletePermission (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) :
-    (Id.run do
-      let mut appLabel := selfAppLabel
-      let mut modelName := selfModelName
-      for f in fields do
-        if f.hasRemote && f.remoteModelId != parentModelId then
-          appLabel := f.remoteAppLabel
-          modelName := f.remoteModelName
-          break
-      return (appLabel, modelName)) = resolveTarget selfAppLabel selfModelName parentModelId fields := by
-  unfold resolveTarget
-  induction fields with
-  | nil => rfl
-  | cons hd tl ih =>
-    cases hc : (hd.hasRemote && hd.remoteModelId != parentModelId) <;>
-      simp only [List.forIn_cons, List.find?_cons, hc] <;> [exact ih; rfl]
-
-theorem any_loop_eq (appLabel modelName : String) (userPerms actions : List String) :
-    (Id.run do
-      for a in actions do
-        if userPerms.contains (permString appLabel modelName a) then
-          return true
-      return false) = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-  induction actions with
-  | nil => rfl
-  | cons a as ih =>
-    simp only [List.forIn_cons, List.any_cons, List.contains_eq_mem] at ih ⊢
-    by_cases h : permString appLabel modelName a ∈ userPerms
-    · simp [h]
-    · simp only [h, decide_false, Bool.false_eq_true, if_false, Bool.false_or]
-      exact ih
-
-theorem anyPerms_bridge (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) (userPerms actions : List String) :
-    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
-  simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget]
-  have hf := resolve_loop_eq_hasDeletePermission selfAppLabel selfModelName parentModelId fields
-  have ha := any_loop_eq (resolveTarget selfAppLabel selfModelName parentModelId fields).1
-    (resolveTarget selfAppLabel selfModelName parentModelId fields).2 userPerms actions
-  simp only [Id.run, bind, pure] at hf ha ⊢
-  rw [← ha, ← hf]
-  rfl
-
-theorem impl_reduce (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) (userPerms : List String) (superResult : Bool) :
-    implementation_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = (if autoCreated then
-          implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
-        else superResult) := by
-  cases autoCreated <;> rfl
-
--- proof_aux for correct_hasViewPermission
-def ResolveLoop (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) : String × String := Id.run do
-  let mut appLabel := selfAppLabel
-  let mut modelName := selfModelName
-  for f in fields do
-    if f.hasRemote && f.remoteModelId != parentModelId then
-      appLabel := f.remoteAppLabel
-      modelName := f.remoteModelName
-      break
-  return (appLabel, modelName)
-
-def ActionsLoop (appLabel modelName : String)
-    (userPerms actions : List String) : Bool := Id.run do
-  for a in actions do
-    if userPerms.contains (permString appLabel modelName a) then
-      return true
-  return false
-
-theorem resolveLoop_eq (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) :
-    ResolveLoop selfAppLabel selfModelName parentModelId fields
-      = resolveTarget selfAppLabel selfModelName parentModelId fields := by
-  induction fields with
-  | nil => rfl
-  | cons f fs ih =>
-    simp only [ResolveLoop, resolveTarget, Id.run, List.forIn_cons, List.find?] at *
-    by_cases h : (f.hasRemote && f.remoteModelId != parentModelId) = true
-    · simp only [h, if_true]
-      rfl
-    · simp only [Bool.not_eq_true] at h
-      simp only [h]
-      simp only [Bool.false_eq_true, if_false]
-      exact ih
-
-theorem actionsLoop_eq (appLabel modelName : String)
-    (userPerms actions : List String) :
-    ActionsLoop appLabel modelName userPerms actions
-      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-  induction actions with
-  | nil => rfl
-  | cons a as ih =>
-    simp only [ActionsLoop, Id.run] at ih ⊢
-    rw [List.forIn_cons]
-    split <;> rename_i h <;>
-      simp only [h, List.any_cons, Bool.true_or, Bool.false_or] <;>
-      first | rfl | (rw [← ih]; rfl)
-
-theorem anyPerms_impl_eq_spec (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) (userPerms actions : List String) :
-    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
-  simp only [anyPermForTarget, ← actionsLoop_eq, ← resolveLoop_eq]
-  unfold implementation_hasAnyPermsForTargetModel ResolveLoop ActionsLoop
-  rfl
-
-theorem view_wrapper_reduce (autoCreated : Bool)
-    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) :
-    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = (if autoCreated then
-          implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
-        else superResult) := by
-  simp only [implementation_hasViewPermission, Id.run]
-  cases autoCreated <;> rfl
-
-theorem view_true_branch (autoCreated : Bool)
-    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) :
-    autoCreated = true →
-    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"] := by
-  intro h
-  rw [view_wrapper_reduce, h]
-  simp only [if_true]
-  exact anyPerms_impl_eq_spec selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
-
-theorem view_false_branch (autoCreated : Bool)
-    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) :
-    autoCreated = false →
-    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = superResult := by
-  intro h
-  subst h
-  rfl
-
 theorem correct_hasAnyPermsForTargetModel :
     ∀ (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
       (userPerms actions : List String),
       problem_spec_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
         (implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions) := by
   intro selfAppLabel selfModelName parentModelId fields userPerms actions
-  unfold problem_spec_hasAnyPermsForTargetModel implementation_hasAnyPermsForTargetModel anyPermForTarget
-  -- Identify the target-resolution loop with `resolveTarget` (via `resolvedPair`)
-  -- and the action-scan loop with `List.any`, then reduce to reflexivity.
-  rw [← resolve_loop_eq selfAppLabel selfModelName parentModelId fields,
-      ← scan_loop_eq]
-  rfl
+  first
+    | rfl
+    | (unfold problem_spec_hasAnyPermsForTargetModel; decide)
+    | (unfold problem_spec_hasAnyPermsForTargetModel implementation_hasAnyPermsForTargetModel anyPermForTarget; rfl)
+    | simp_all [problem_spec_hasAnyPermsForTargetModel, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasAddPermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -390,36 +183,10 @@
       problem_spec_hasAddPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasAddPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  constructor
-  · intro hac
-    subst hac
-    have key : ∀ (sa sm : String),
-        implementation_hasAnyPermsForTargetModel sa sm parentModelId fields userPerms ["change"]
-          = anyPermForTarget sa sm parentModelId fields userPerms ["change"] := by
-      intro sa sm
-      induction fields generalizing sa sm with
-      | nil =>
-        simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
-          Id.run, List.forIn_nil, List.find?_nil]
-        by_cases hm : permString sa sm "change" ∈ userPerms <;> simp [hm] <;> rfl
-      | cons f fs ih =>
-        simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
-          Id.run, List.forIn_cons, List.find?_cons]
-        by_cases hc : (f.hasRemote && f.remoteModelId != parentModelId) = true
-        · simp only [hc, if_true]
-          by_cases hm : permString f.remoteAppLabel f.remoteModelName "change" ∈ userPerms <;>
-            simp [hm] <;> rfl
-        · have hb : (f.hasRemote && f.remoteModelId != parentModelId) = false := by
-            simpa using hc
-          have hih := ih sa sm
-          simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
-            Id.run] at hih
-          simp only [hb, if_false, Bool.false_eq_true]
-          simpa using hih
-    simpa [implementation_hasAddPermission, Id.run] using key selfAppLabel selfModelName
-  · intro hac
-    subst hac
-    rfl
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasAddPermission, implementation_hasAddPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasAddPermission, implementation_hasAddPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasChangePermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -427,49 +194,10 @@
       problem_spec_hasChangePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasChangePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  have key : ∀ (actions : List String),
-    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
-    intro actions
-    have loop2 : ∀ (appLabel modelName : String),
-      (Id.run do
-        for a in actions do
-          if userPerms.contains (permString appLabel modelName a) then
-            return true
-        return false)
-      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-      intro appLabel modelName
-      induction actions with
-      | nil => rfl
-      | cons hd tl ih =>
-        rw [List.any_cons]
-        simp only [List.forIn_cons, Id.run]
-        by_cases h : userPerms.contains (permString appLabel modelName hd) = true
-        · simp only [h, if_true, List.contains_eq_mem, decide_eq_true_eq] at *; rfl
-        · simp only [Bool.not_eq_true] at h
-          simp only [h, Bool.false_or]
-          rw [← ih]; simp [Id.run]
-    unfold implementation_hasAnyPermsForTargetModel anyPermForTarget
-    simp only []
-    induction fields with
-    | nil => exact loop2 selfAppLabel selfModelName
-    | cons hd tl ih =>
-      simp only [List.forIn_cons, Id.run, resolveTarget, List.find?]
-      by_cases h : hd.hasRemote && hd.remoteModelId != parentModelId
-      · simp only [h, if_true]
-        exact loop2 hd.remoteAppLabel hd.remoteModelName
-      · simp only [h, Bool.false_eq_true, if_false]
-        simp only [Id.run, resolveTarget] at ih
-        exact ih
-  constructor
-  · intro hac
-    unfold implementation_hasChangePermission
-    simp only [hac, if_true, Id.run]
-    exact key ["change"]
-  · intro hac
-    unfold implementation_hasChangePermission
-    simp only [hac, Id.run]
-    rfl
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasChangePermission, implementation_hasChangePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasChangePermission, implementation_hasChangePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasDeletePermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -477,11 +205,10 @@
       problem_spec_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  refine ⟨?_, ?_⟩
-  · intro h
-    simp only [impl_reduce, h, if_true, anyPerms_bridge]
-  · intro h
-    simp only [impl_reduce, h, Bool.false_eq_true, if_false]
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasDeletePermission, implementation_hasDeletePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasDeletePermission, implementation_hasDeletePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasViewPermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -489,10 +216,8 @@
       problem_spec_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  refine ⟨?_, ?_⟩
-  · intro h
-    exact view_true_branch autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult h
-  · intro h
-    exact view_false_branch autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult h
-
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasViewPermission, implementation_hasViewPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasViewPermission, implementation_hasViewPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -137,9 +137,7 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Resolve the target model by scanning the fields (taking the first field that
-points at a related model other than the parent), then report whether the user
-holds any of the listed action permissions on it. -/
+/-- helper -/
 def implementation_hasAnyPermsForTargetModel
     (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
     (userPerms actions : List String) : Bool := Id.run do
@@ -172,8 +170,6 @@
 def implementation_hasDeletePermission (autoCreated : Bool)
     (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
     (userPerms : List String) (superResult : Bool) : Bool := Id.run do
-  if autoCreated then
-    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
   return superResult
 
 def implementation_hasViewPermission (autoCreated : Bool)
@@ -185,204 +181,17 @@
 -- impl-end
 
 -- proof-start
-
--- proof_aux for correct_hasAnyPermsForTargetModel
-/-- The `(appLabel, modelName)` the first for-loop settles on: scan `fields` and
-take the first field pointing at a related model other than the parent; else keep
-`(selfAppLabel, selfModelName)`. This is `resolveTarget` by definition. -/
-def resolvedPair (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) : String × String :=
-  Id.run do
-    let mut appLabel := selfAppLabel
-    let mut modelName := selfModelName
-    for f in fields do
-      if f.hasRemote && f.remoteModelId != parentModelId then
-        appLabel := f.remoteAppLabel
-        modelName := f.remoteModelName
-        break
-    return (appLabel, modelName)
-
-theorem resolve_loop_eq (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) :
-    resolvedPair selfAppLabel selfModelName parentModelId fields
-      = resolveTarget selfAppLabel selfModelName parentModelId fields := by
-  unfold resolvedPair resolveTarget
-  induction fields with
-  | nil => rfl
-  | cons f fs ih =>
-    simp only [List.forIn_cons, List.find?_cons]
-    by_cases h : f.hasRemote && f.remoteModelId != parentModelId
-    · simp [h]
-    · simp only [h]; exact ih
-
-theorem scan_loop_eq (appLabel modelName : String) (userPerms actions : List String) :
-    (Id.run do
-      for a in actions do
-        if userPerms.contains (permString appLabel modelName a) then
-          return true
-      return false)
-      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-  simp only [Id.run]; induction actions with
-  | nil => rfl
-  | cons a as ih =>
-    simp only [List.forIn_cons, List.any_cons]
-    split
-    · rename_i h; rw [h]; rfl
-    · rename_i h; simp_all
-
--- proof_aux for correct_hasDeletePermission
-theorem resolve_loop_eq_hasDeletePermission (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) :
-    (Id.run do
-      let mut appLabel := selfAppLabel
-      let mut modelName := selfModelName
-      for f in fields do
-        if f.hasRemote && f.remoteModelId != parentModelId then
-          appLabel := f.remoteAppLabel
-          modelName := f.remoteModelName
-          break
-      return (appLabel, modelName)) = resolveTarget selfAppLabel selfModelName parentModelId fields := by
-  unfold resolveTarget
-  induction fields with
-  | nil => rfl
-  | cons hd tl ih =>
-    cases hc : (hd.hasRemote && hd.remoteModelId != parentModelId) <;>
-      simp only [List.forIn_cons, List.find?_cons, hc] <;> [exact ih; rfl]
-
-theorem any_loop_eq (appLabel modelName : String) (userPerms actions : List String) :
-    (Id.run do
-      for a in actions do
-        if userPerms.contains (permString appLabel modelName a) then
-          return true
-      return false) = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-  induction actions with
-  | nil => rfl
-  | cons a as ih =>
-    simp only [List.forIn_cons, List.any_cons, List.contains_eq_mem] at ih ⊢
-    by_cases h : permString appLabel modelName a ∈ userPerms
-    · simp [h]
-    · simp only [h, decide_false, Bool.false_eq_true, if_false, Bool.false_or]
-      exact ih
-
-theorem anyPerms_bridge (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) (userPerms actions : List String) :
-    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
-  simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget]
-  have hf := resolve_loop_eq_hasDeletePermission selfAppLabel selfModelName parentModelId fields
-  have ha := any_loop_eq (resolveTarget selfAppLabel selfModelName parentModelId fields).1
-    (resolveTarget selfAppLabel selfModelName parentModelId fields).2 userPerms actions
-  simp only [Id.run, bind, pure] at hf ha ⊢
-  rw [← ha, ← hf]
-  rfl
-
-theorem impl_reduce (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) (userPerms : List String) (superResult : Bool) :
-    implementation_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = (if autoCreated then
-          implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
-        else superResult) := by
-  cases autoCreated <;> rfl
-
--- proof_aux for correct_hasViewPermission
-def ResolveLoop (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) : String × String := Id.run do
-  let mut appLabel := selfAppLabel
-  let mut modelName := selfModelName
-  for f in fields do
-    if f.hasRemote && f.remoteModelId != parentModelId then
-      appLabel := f.remoteAppLabel
-      modelName := f.remoteModelName
-      break
-  return (appLabel, modelName)
-
-def ActionsLoop (appLabel modelName : String)
-    (userPerms actions : List String) : Bool := Id.run do
-  for a in actions do
-    if userPerms.contains (permString appLabel modelName a) then
-      return true
-  return false
-
-theorem resolveLoop_eq (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) :
-    ResolveLoop selfAppLabel selfModelName parentModelId fields
-      = resolveTarget selfAppLabel selfModelName parentModelId fields := by
-  induction fields with
-  | nil => rfl
-  | cons f fs ih =>
-    simp only [ResolveLoop, resolveTarget, Id.run, List.forIn_cons, List.find?] at *
-    by_cases h : (f.hasRemote && f.remoteModelId != parentModelId) = true
-    · simp only [h, if_true]
-      rfl
-    · simp only [Bool.not_eq_true] at h
-      simp only [h]
-      simp only [Bool.false_eq_true, if_false]
-      exact ih
-
-theorem actionsLoop_eq (appLabel modelName : String)
-    (userPerms actions : List String) :
-    ActionsLoop appLabel modelName userPerms actions
-      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-  induction actions with
-  | nil => rfl
-  | cons a as ih =>
-    simp only [ActionsLoop, Id.run] at ih ⊢
-    rw [List.forIn_cons]
-    split <;> rename_i h <;>
-      simp only [h, List.any_cons, Bool.true_or, Bool.false_or] <;>
-      first | rfl | (rw [← ih]; rfl)
-
-theorem anyPerms_impl_eq_spec (selfAppLabel selfModelName parentModelId : String)
-    (fields : List LinkField) (userPerms actions : List String) :
-    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
-  simp only [anyPermForTarget, ← actionsLoop_eq, ← resolveLoop_eq]
-  unfold implementation_hasAnyPermsForTargetModel ResolveLoop ActionsLoop
-  rfl
-
-theorem view_wrapper_reduce (autoCreated : Bool)
-    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) :
-    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = (if autoCreated then
-          implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
-        else superResult) := by
-  simp only [implementation_hasViewPermission, Id.run]
-  cases autoCreated <;> rfl
-
-theorem view_true_branch (autoCreated : Bool)
-    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) :
-    autoCreated = true →
-    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"] := by
-  intro h
-  rw [view_wrapper_reduce, h]
-  simp only [if_true]
-  exact anyPerms_impl_eq_spec selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
-
-theorem view_false_branch (autoCreated : Bool)
-    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
-    (userPerms : List String) (superResult : Bool) :
-    autoCreated = false →
-    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-      = superResult := by
-  intro h
-  subst h
-  rfl
-
 theorem correct_hasAnyPermsForTargetModel :
     ∀ (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
       (userPerms actions : List String),
       problem_spec_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
         (implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions) := by
   intro selfAppLabel selfModelName parentModelId fields userPerms actions
-  unfold problem_spec_hasAnyPermsForTargetModel implementation_hasAnyPermsForTargetModel anyPermForTarget
-  -- Identify the target-resolution loop with `resolveTarget` (via `resolvedPair`)
-  -- and the action-scan loop with `List.any`, then reduce to reflexivity.
-  rw [← resolve_loop_eq selfAppLabel selfModelName parentModelId fields,
-      ← scan_loop_eq]
-  rfl
+  first
+    | rfl
+    | (unfold problem_spec_hasAnyPermsForTargetModel; decide)
+    | (unfold problem_spec_hasAnyPermsForTargetModel implementation_hasAnyPermsForTargetModel anyPermForTarget; rfl)
+    | simp_all [problem_spec_hasAnyPermsForTargetModel, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasAddPermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -390,36 +199,10 @@
       problem_spec_hasAddPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasAddPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  constructor
-  · intro hac
-    subst hac
-    have key : ∀ (sa sm : String),
-        implementation_hasAnyPermsForTargetModel sa sm parentModelId fields userPerms ["change"]
-          = anyPermForTarget sa sm parentModelId fields userPerms ["change"] := by
-      intro sa sm
-      induction fields generalizing sa sm with
-      | nil =>
-        simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
-          Id.run, List.forIn_nil, List.find?_nil]
-        by_cases hm : permString sa sm "change" ∈ userPerms <;> simp [hm] <;> rfl
-      | cons f fs ih =>
-        simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
-          Id.run, List.forIn_cons, List.find?_cons]
-        by_cases hc : (f.hasRemote && f.remoteModelId != parentModelId) = true
-        · simp only [hc, if_true]
-          by_cases hm : permString f.remoteAppLabel f.remoteModelName "change" ∈ userPerms <;>
-            simp [hm] <;> rfl
-        · have hb : (f.hasRemote && f.remoteModelId != parentModelId) = false := by
-            simpa using hc
-          have hih := ih sa sm
-          simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
-            Id.run] at hih
-          simp only [hb, if_false, Bool.false_eq_true]
-          simpa using hih
-    simpa [implementation_hasAddPermission, Id.run] using key selfAppLabel selfModelName
-  · intro hac
-    subst hac
-    rfl
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasAddPermission, implementation_hasAddPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasAddPermission, implementation_hasAddPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasChangePermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -427,49 +210,10 @@
       problem_spec_hasChangePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasChangePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  have key : ∀ (actions : List String),
-    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
-      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
-    intro actions
-    have loop2 : ∀ (appLabel modelName : String),
-      (Id.run do
-        for a in actions do
-          if userPerms.contains (permString appLabel modelName a) then
-            return true
-        return false)
-      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
-      intro appLabel modelName
-      induction actions with
-      | nil => rfl
-      | cons hd tl ih =>
-        rw [List.any_cons]
-        simp only [List.forIn_cons, Id.run]
-        by_cases h : userPerms.contains (permString appLabel modelName hd) = true
-        · simp only [h, if_true, List.contains_eq_mem, decide_eq_true_eq] at *; rfl
-        · simp only [Bool.not_eq_true] at h
-          simp only [h, Bool.false_or]
-          rw [← ih]; simp [Id.run]
-    unfold implementation_hasAnyPermsForTargetModel anyPermForTarget
-    simp only []
-    induction fields with
-    | nil => exact loop2 selfAppLabel selfModelName
-    | cons hd tl ih =>
-      simp only [List.forIn_cons, Id.run, resolveTarget, List.find?]
-      by_cases h : hd.hasRemote && hd.remoteModelId != parentModelId
-      · simp only [h, if_true]
-        exact loop2 hd.remoteAppLabel hd.remoteModelName
-      · simp only [h, Bool.false_eq_true, if_false]
-        simp only [Id.run, resolveTarget] at ih
-        exact ih
-  constructor
-  · intro hac
-    unfold implementation_hasChangePermission
-    simp only [hac, if_true, Id.run]
-    exact key ["change"]
-  · intro hac
-    unfold implementation_hasChangePermission
-    simp only [hac, Id.run]
-    rfl
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasChangePermission, implementation_hasChangePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasChangePermission, implementation_hasChangePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasDeletePermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -477,11 +221,10 @@
       problem_spec_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  refine ⟨?_, ?_⟩
-  · intro h
-    simp only [impl_reduce, h, if_true, anyPerms_bridge]
-  · intro h
-    simp only [impl_reduce, h, Bool.false_eq_true, if_false]
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasDeletePermission, implementation_hasDeletePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasDeletePermission, implementation_hasDeletePermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 
 theorem correct_hasViewPermission :
     ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
@@ -489,10 +232,8 @@
       problem_spec_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
         (implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
   intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
-  refine ⟨?_, ?_⟩
-  · intro h
-    exact view_true_branch autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult h
-  · intro h
-    exact view_false_branch autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult h
-
+  first
+    | (constructor <;> intro h <;> subst h <;> rfl)
+    | (constructor <;> intro h <;> simp_all [problem_spec_hasViewPermission, implementation_hasViewPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget])
+    | simp_all [problem_spec_hasViewPermission, implementation_hasViewPermission, implementation_hasAnyPermsForTargetModel, anyPermForTarget]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Authorization for the implicit intermediary model of a many-to-many
relationship in an administrative interface.

An object editor may display the rows of an auto-created link model (the hidden
table that records which pairs of two related models are associated). Such a
link model has no permissions of its own, so the authority to act on its rows is
derived from permissions held on the *target* model — the related model that the
link points at (the one that is NOT the containing/parent model).

Two ingredients are involved.

* **Locating the target model.** The link model exposes a list of fields. The
  target model is identified by the first field that refers to a related model
  other than the parent model; its application label and model name are taken
  from that related model. If no such field exists, the link model's own labels
  are used.

* **Permission strings.** Permission to perform an action `a` on a model is
  expressed as the string `"<app_label>.<a>_<model_name>"`. A user holds a set
  of such permission strings; the user is authorized for action `a` exactly when
  that string is among the held permissions.

The authority required of each editor action, when operating on an auto-created
link model, is:

* **add**, **change**, **delete** — require the *change* permission on the target
  model;
* **view** — requires the *view* permission OR the *change* permission on the
  target model (the latter subsuming the former).

When the model is NOT an auto-created link model, each action defers to the
ordinary authorization decision supplied for that action (a caller-supplied input
here).

The behavior is stated abstractly as an input→output relation; the
implementations and correctness proofs are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The user's effective set
-- of granted permission strings is supplied as the `userPerms` input (a
-- membership test against it stands in for the authorization lookup), the
-- per-action permission-string format is spelled out concretely below, and the
-- target-model resolution over the field list is modeled deeply.
-- axioms-end

-- pure-start
/-- One field of the link model, as far as target resolution is concerned.

* `hasRemote`        — whether the field refers to a related model at all;
* `remoteModelId`    — an identity tag for the related model it refers to (used
                        to tell it apart from the parent model);
* `remoteAppLabel`   — the application label of that related model;
* `remoteModelName`  — the model name of that related model. -/
structure LinkField where
  hasRemote : Bool
  remoteModelId : String
  remoteAppLabel : String
  remoteModelName : String
deriving Repr, DecidableEq

/-- The permission string for performing action `action` on the model named
`modelName` in application `appLabel`: `"<appLabel>.<action>_<modelName>"`. -/
def permString (appLabel modelName action : String) : String :=
  appLabel ++ "." ++ action ++ "_" ++ modelName

/-- Resolve the `(appLabel, modelName)` of the target model. It is taken from the
first field that refers to a related model whose identity differs from the parent
model; absent such a field, the link model's own `(selfAppLabel, selfModelName)`
is used. -/
def resolveTarget (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) : String × String :=
  match fields.find? (fun f => f.hasRemote && f.remoteModelId != parentModelId) with
  | some f => (f.remoteAppLabel, f.remoteModelName)
  | none => (selfAppLabel, selfModelName)

/-- True when the user holds, on the target model, at least one of the listed
action permissions. -/
def anyPermForTarget (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) (userPerms actions : List String) : Bool :=
  let t := resolveTarget selfAppLabel selfModelName parentModelId fields
  actions.any (fun a => userPerms.contains (permString t.1 t.2 a))
-- pure-end

-- post-conditions-start
/-- Input→output relation for the target-permission test: the result is true iff
the user holds at least one of the `actions` permissions on the resolved target
model. -/
def problem_spec_hasAnyPermsForTargetModel
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms actions : List String) (result : Bool) : Prop :=
  result = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions

/-- Input→output relation for the **add** action. On an auto-created link model
the result requires the *change* permission on the target model; otherwise it is
the caller-supplied decision `superResult`. -/
def problem_spec_hasAddPermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) (result : Bool) : Prop :=
  (autoCreated = true →
    result = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["change"]) ∧
  (autoCreated = false → result = superResult)

/-- Input→output relation for the **change** action. On an auto-created link model
the result requires the *change* permission on the target model; otherwise it is
the caller-supplied decision `superResult`. -/
def problem_spec_hasChangePermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) (result : Bool) : Prop :=
  (autoCreated = true →
    result = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["change"]) ∧
  (autoCreated = false → result = superResult)

/-- Input→output relation for the **delete** action. On an auto-created link model
the result requires the *change* permission on the target model; otherwise it is
the caller-supplied decision `superResult`. -/
def problem_spec_hasDeletePermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) (result : Bool) : Prop :=
  (autoCreated = true →
    result = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["change"]) ∧
  (autoCreated = false → result = superResult)

/-- Input→output relation for the **view** action. On an auto-created link model
the result requires the *view* OR *change* permission on the target model;
otherwise it is the caller-supplied decision `superResult`. -/
def problem_spec_hasViewPermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) (result : Bool) : Prop :=
  (autoCreated = true →
    result = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]) ∧
  (autoCreated = false → result = superResult)
-- post-conditions-end

-- impl-start
/-- Resolve the target model by scanning the fields (taking the first field that
points at a related model other than the parent), then report whether the user
holds any of the listed action permissions on it. -/
def implementation_hasAnyPermsForTargetModel
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms actions : List String) : Bool := Id.run do
  let mut appLabel := selfAppLabel
  let mut modelName := selfModelName
  for f in fields do
    if f.hasRemote && f.remoteModelId != parentModelId then
      appLabel := f.remoteAppLabel
      modelName := f.remoteModelName
      break
  for a in actions do
    if userPerms.contains (permString appLabel modelName a) then
      return true
  return false

def implementation_hasAddPermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) : Bool := Id.run do
  if autoCreated then
    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
  return superResult

def implementation_hasChangePermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) : Bool := Id.run do
  if autoCreated then
    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
  return superResult

def implementation_hasDeletePermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) : Bool := Id.run do
  if autoCreated then
    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
  return superResult

def implementation_hasViewPermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) : Bool := Id.run do
  if autoCreated then
    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
  return superResult
-- impl-end

-- proof-start

-- proof_aux for correct_hasAnyPermsForTargetModel
/-- The `(appLabel, modelName)` the first for-loop settles on: scan `fields` and
take the first field pointing at a related model other than the parent; else keep
`(selfAppLabel, selfModelName)`. This is `resolveTarget` by definition. -/
def resolvedPair (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) : String × String :=
  Id.run do
    let mut appLabel := selfAppLabel
    let mut modelName := selfModelName
    for f in fields do
      if f.hasRemote && f.remoteModelId != parentModelId then
        appLabel := f.remoteAppLabel
        modelName := f.remoteModelName
        break
    return (appLabel, modelName)

theorem resolve_loop_eq (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) :
    resolvedPair selfAppLabel selfModelName parentModelId fields
      = resolveTarget selfAppLabel selfModelName parentModelId fields := by
  unfold resolvedPair resolveTarget
  induction fields with
  | nil => rfl
  | cons f fs ih =>
    simp only [List.forIn_cons, List.find?_cons]
    by_cases h : f.hasRemote && f.remoteModelId != parentModelId
    · simp [h]
    · simp only [h]; exact ih

theorem scan_loop_eq (appLabel modelName : String) (userPerms actions : List String) :
    (Id.run do
      for a in actions do
        if userPerms.contains (permString appLabel modelName a) then
          return true
      return false)
      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
  simp only [Id.run]; induction actions with
  | nil => rfl
  | cons a as ih =>
    simp only [List.forIn_cons, List.any_cons]
    split
    · rename_i h; rw [h]; rfl
    · rename_i h; simp_all

-- proof_aux for correct_hasDeletePermission
theorem resolve_loop_eq_hasDeletePermission (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) :
    (Id.run do
      let mut appLabel := selfAppLabel
      let mut modelName := selfModelName
      for f in fields do
        if f.hasRemote && f.remoteModelId != parentModelId then
          appLabel := f.remoteAppLabel
          modelName := f.remoteModelName
          break
      return (appLabel, modelName)) = resolveTarget selfAppLabel selfModelName parentModelId fields := by
  unfold resolveTarget
  induction fields with
  | nil => rfl
  | cons hd tl ih =>
    cases hc : (hd.hasRemote && hd.remoteModelId != parentModelId) <;>
      simp only [List.forIn_cons, List.find?_cons, hc] <;> [exact ih; rfl]

theorem any_loop_eq (appLabel modelName : String) (userPerms actions : List String) :
    (Id.run do
      for a in actions do
        if userPerms.contains (permString appLabel modelName a) then
          return true
      return false) = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
  induction actions with
  | nil => rfl
  | cons a as ih =>
    simp only [List.forIn_cons, List.any_cons, List.contains_eq_mem] at ih ⊢
    by_cases h : permString appLabel modelName a ∈ userPerms
    · simp [h]
    · simp only [h, decide_false, Bool.false_eq_true, if_false, Bool.false_or]
      exact ih

theorem anyPerms_bridge (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) (userPerms actions : List String) :
    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
  simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget]
  have hf := resolve_loop_eq_hasDeletePermission selfAppLabel selfModelName parentModelId fields
  have ha := any_loop_eq (resolveTarget selfAppLabel selfModelName parentModelId fields).1
    (resolveTarget selfAppLabel selfModelName parentModelId fields).2 userPerms actions
  simp only [Id.run, bind, pure] at hf ha ⊢
  rw [← ha, ← hf]
  rfl

theorem impl_reduce (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) (userPerms : List String) (superResult : Bool) :
    implementation_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
      = (if autoCreated then
          implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
        else superResult) := by
  cases autoCreated <;> rfl

-- proof_aux for correct_hasViewPermission
def ResolveLoop (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) : String × String := Id.run do
  let mut appLabel := selfAppLabel
  let mut modelName := selfModelName
  for f in fields do
    if f.hasRemote && f.remoteModelId != parentModelId then
      appLabel := f.remoteAppLabel
      modelName := f.remoteModelName
      break
  return (appLabel, modelName)

def ActionsLoop (appLabel modelName : String)
    (userPerms actions : List String) : Bool := Id.run do
  for a in actions do
    if userPerms.contains (permString appLabel modelName a) then
      return true
  return false

theorem resolveLoop_eq (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) :
    ResolveLoop selfAppLabel selfModelName parentModelId fields
      = resolveTarget selfAppLabel selfModelName parentModelId fields := by
  induction fields with
  | nil => rfl
  | cons f fs ih =>
    simp only [ResolveLoop, resolveTarget, Id.run, List.forIn_cons, List.find?] at *
    by_cases h : (f.hasRemote && f.remoteModelId != parentModelId) = true
    · simp only [h, if_true]
      rfl
    · simp only [Bool.not_eq_true] at h
      simp only [h]
      simp only [Bool.false_eq_true, if_false]
      exact ih

theorem actionsLoop_eq (appLabel modelName : String)
    (userPerms actions : List String) :
    ActionsLoop appLabel modelName userPerms actions
      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
  induction actions with
  | nil => rfl
  | cons a as ih =>
    simp only [ActionsLoop, Id.run] at ih ⊢
    rw [List.forIn_cons]
    split <;> rename_i h <;>
      simp only [h, List.any_cons, Bool.true_or, Bool.false_or] <;>
      first | rfl | (rw [← ih]; rfl)

theorem anyPerms_impl_eq_spec (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) (userPerms actions : List String) :
    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
  simp only [anyPermForTarget, ← actionsLoop_eq, ← resolveLoop_eq]
  unfold implementation_hasAnyPermsForTargetModel ResolveLoop ActionsLoop
  rfl

theorem view_wrapper_reduce (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) :
    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
      = (if autoCreated then
          implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
        else superResult) := by
  simp only [implementation_hasViewPermission, Id.run]
  cases autoCreated <;> rfl

theorem view_true_branch (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) :
    autoCreated = true →
    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"] := by
  intro h
  rw [view_wrapper_reduce, h]
  simp only [if_true]
  exact anyPerms_impl_eq_spec selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]

theorem view_false_branch (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) :
    autoCreated = false →
    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
      = superResult := by
  intro h
  subst h
  rfl

theorem correct_hasAnyPermsForTargetModel :
    ∀ (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
      (userPerms actions : List String),
      problem_spec_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
        (implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions) := by
  intro selfAppLabel selfModelName parentModelId fields userPerms actions
  unfold problem_spec_hasAnyPermsForTargetModel implementation_hasAnyPermsForTargetModel anyPermForTarget
  -- Identify the target-resolution loop with `resolveTarget` (via `resolvedPair`)
  -- and the action-scan loop with `List.any`, then reduce to reflexivity.
  rw [← resolve_loop_eq selfAppLabel selfModelName parentModelId fields,
      ← scan_loop_eq]
  rfl

theorem correct_hasAddPermission :
    ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
      (fields : List LinkField) (userPerms : List String) (superResult : Bool),
      problem_spec_hasAddPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
        (implementation_hasAddPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
  intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
  constructor
  · intro hac
    subst hac
    have key : ∀ (sa sm : String),
        implementation_hasAnyPermsForTargetModel sa sm parentModelId fields userPerms ["change"]
          = anyPermForTarget sa sm parentModelId fields userPerms ["change"] := by
      intro sa sm
      induction fields generalizing sa sm with
      | nil =>
        simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
          Id.run, List.forIn_nil, List.find?_nil]
        by_cases hm : permString sa sm "change" ∈ userPerms <;> simp [hm] <;> rfl
      | cons f fs ih =>
        simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
          Id.run, List.forIn_cons, List.find?_cons]
        by_cases hc : (f.hasRemote && f.remoteModelId != parentModelId) = true
        · simp only [hc, if_true]
          by_cases hm : permString f.remoteAppLabel f.remoteModelName "change" ∈ userPerms <;>
            simp [hm] <;> rfl
        · have hb : (f.hasRemote && f.remoteModelId != parentModelId) = false := by
            simpa using hc
          have hih := ih sa sm
          simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
            Id.run] at hih
          simp only [hb, if_false, Bool.false_eq_true]
          simpa using hih
    simpa [implementation_hasAddPermission, Id.run] using key selfAppLabel selfModelName
  · intro hac
    subst hac
    rfl

theorem correct_hasChangePermission :
    ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
      (fields : List LinkField) (userPerms : List String) (superResult : Bool),
      problem_spec_hasChangePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
        (implementation_hasChangePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
  intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
  have key : ∀ (actions : List String),
    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
    intro actions
    have loop2 : ∀ (appLabel modelName : String),
      (Id.run do
        for a in actions do
          if userPerms.contains (permString appLabel modelName a) then
            return true
        return false)
      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
      intro appLabel modelName
      induction actions with
      | nil => rfl
      | cons hd tl ih =>
        rw [List.any_cons]
        simp only [List.forIn_cons, Id.run]
        by_cases h : userPerms.contains (permString appLabel modelName hd) = true
        · simp only [h, if_true, List.contains_eq_mem, decide_eq_true_eq] at *; rfl
        · simp only [Bool.not_eq_true] at h
          simp only [h, Bool.false_or]
          rw [← ih]; simp [Id.run]
    unfold implementation_hasAnyPermsForTargetModel anyPermForTarget
    simp only []
    induction fields with
    | nil => exact loop2 selfAppLabel selfModelName
    | cons hd tl ih =>
      simp only [List.forIn_cons, Id.run, resolveTarget, List.find?]
      by_cases h : hd.hasRemote && hd.remoteModelId != parentModelId
      · simp only [h, if_true]
        exact loop2 hd.remoteAppLabel hd.remoteModelName
      · simp only [h, Bool.false_eq_true, if_false]
        simp only [Id.run, resolveTarget] at ih
        exact ih
  constructor
  · intro hac
    unfold implementation_hasChangePermission
    simp only [hac, if_true, Id.run]
    exact key ["change"]
  · intro hac
    unfold implementation_hasChangePermission
    simp only [hac, Id.run]
    rfl

theorem correct_hasDeletePermission :
    ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
      (fields : List LinkField) (userPerms : List String) (superResult : Bool),
      problem_spec_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
        (implementation_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
  intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
  refine ⟨?_, ?_⟩
  · intro h
    simp only [impl_reduce, h, if_true, anyPerms_bridge]
  · intro h
    simp only [impl_reduce, h, Bool.false_eq_true, if_false]

theorem correct_hasViewPermission :
    ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
      (fields : List LinkField) (userPerms : List String) (superResult : Bool),
      problem_spec_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
        (implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
  intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
  refine ⟨?_, ?_⟩
  · intro h
    exact view_true_branch autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult h
  · intro h
    exact view_false_branch autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult h

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS A TOTAL FUNCTIONAL SPEC: every problem_spec_* postcondition pins `result` to an exact function of the inputs (anyPermForTarget over resolveTarget/permString for the autoCreated=true clause; superResult for autoCreated=false), and that function faithfully matches gold behavior (add/change/delete require ["change"], view requires ["view","change"]). Any impl that deviates observably has a mathematically-false correct_* theorem and cannot verify.

PROTOCOL / RESULTS (all; same_spec=True for all 8 files, verified via swebench_unified.markers.same_spec on lean backend):
Command per file: `bash scripts/lean_verify.sh <file>`, run concurrently ≤4 at a time.

- atk_1 (prepatch bug: add/change/delete defer to ["view","change"]): EXIT=1 (does NOT verify). errors at all 5 correct_* lines; the 3 mutating-action theorems are genuinely false. == prepatch_reproduced.
- atk_2 (partial-domain: non-autoCreated add returns `false`, dropping superResult): EXIT=1.
- atk_3 (boundary: view uses ["view"] only, drops change): EXIT=1.
- atk_4 (control-flow-effect: resolve loop drops the parent-model check, picks first remote field regardless): EXIT=1.
- atk_5 (ungrounded/wrong permission: add uses ["add"] instead of ["change"]): EXIT=1.
- atk_7 (control-flow: delete ignores autoCreated, always returns superResult): EXIT=1.
- atk_6 (ungrounded-oracle ECHO: impls directly return the pure spec function anyPermForTarget with the gold action lists): EXIT=0 VERIFIES. `#print axioms` on all 5 correct_* (file atk_6_ax.lean, EXIT=0): each 'does not depend on any axioms' (CLEAN). PER PROTOCOL materialized its faithful refined patch (atk_6_faithful.patch = behaviorally identical to gold, since atk_6 is behaviorally identical to gold) and RAN run_resolve("django__django-11149", patch): RESOLVED=True, note='resolved' (atk_6_resolve.out). So this verifying same-spec impl RESOLVES => benign echo, NOT a weakness (consistent with fixed G-EQ policy: resolving same-spec verifier is not a break).
- pos_control = gold Solution.lean (copied): EXIT=0 VERIFIES (the earlier pos_control.lean built with a generic brute proof failed the loop-based obligations, so I used the canonical gold artifact as the positive control; same_spec=True).

No verifying wrong-behavior impl exists whose faithful patch fails to resolve => NOT BROKEN. The only impl that closed with clean axioms (atk_6) is a behavioral echo of gold and RESOLVES.

REFINEMENT.MD AUDIT: No axioms declared or consumed (axioms-start/end declares none; no `axiom` keyword). Every leg is R (input observables selfAppLabel/selfModelName/parentModelId/fields/userPerms/superResult; superResult passthrough), I (the edited ["change"] add/change/delete branch and ["view","change"] view branch — identical concrete ops = the fix), or A-reference (target-model resolution loop over fields; permString for get_permission_codename which is UNCHANGED at base_commit e245046; has_perm modeled as set membership). NO kind-3 (A-consumed) legs. A-reference correspondence holds: permString app model action = app++"."++action++"_"++model exactly equals '%s.%s' % (app_label, '%s_%s'%(action,model_name)); field-scan (first non-parent remote field wins, else self) matches gold `for field in opts.fields: if field.remote_field and field.remote_field.model != self.parent_model`. G-CONF differential-tests these R/I/A-reference legs; G-AX is a skip stub (no consumed axioms). Correspondence faithful.

VERDICT: SOUND (≥5 distinct wrong impls attacked, none breaks the spec; the sole verifying same-spec impl resolves).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
For the three mutating actions (add/change/delete) on an auto-created link model (autoCreated=true), take a user holding only the target's VIEW permission, not its CHANGE permission: fields=[{hasRemote:=true, remoteModelId:="other", remoteAppLabel:="app", remoteModelName:="m"}], parentModelId="parent", userPerms=["app.view_m"], superResult arbitrary. The spec (problem_spec_hasAddPermission, autoCreated=true clause) demands result = anyPermForTarget ... ["change"] = ("app.change_m" ∈ userPerms) = false. The prepatch/atk_1 impl defers to ["view","change"] and returns true. So the correct_hasAddPermission/Change/Delete theorems on the autoCreated=true clause are genuinely FALSE and cannot close — exactly the FAIL_TO_PASS behavior (test_inline_add/change_m2m_view_only_perm).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Authorization for the implicit intermediary model of a many-to-many
relationship in an administrative interface.

An object editor may display the rows of an auto-created link model (the hidden
table that records which pairs of two related models are associated). Such a
link model has no permissions of its own, so the authority to act on its rows is
derived from permissions held on the *target* model — the related model that the
link points at (the one that is NOT the containing/parent model).

Two ingredients are involved.

* **Locating the target model.** The link model exposes a list of fields. The
  target model is identified by the first field that refers to a related model
  other than the parent model; its application label and model name are taken
  from that related model. If no such field exists, the link model's own labels
  are used.

* **Permission strings.** Permission to perform an action `a` on a model is
  expressed as the string `"<app_label>.<a>_<model_name>"`. A user holds a set
  of such permission strings; the user is authorized for action `a` exactly when
  that string is among the held permissions.

The authority required of each editor action, when operating on an auto-created
link model, is:

* **add**, **change**, **delete** — require the *change* permission on the target
  model;
* **view** — requires the *view* permission OR the *change* permission on the
  target model (the latter subsuming the former).

When the model is NOT an auto-created link model, each action defers to the
ordinary authorization decision supplied for that action (a caller-supplied input
here).

The behavior is stated abstractly as an input→output relation; the
implementations and correctness proofs are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The user's effective set
-- of granted permission strings is supplied as the `userPerms` input (a
-- membership test against it stands in for the authorization lookup), the
-- per-action permission-string format is spelled out concretely below, and the
-- target-model resolution over the field list is modeled deeply.
-- axioms-end

-- pure-start
/-- One field of the link model, as far as target resolution is concerned.

* `hasRemote`        — whether the field refers to a related model at all;
* `remoteModelId`    — an identity tag for the related model it refers to (used
                        to tell it apart from the parent model);
* `remoteAppLabel`   — the application label of that related model;
* `remoteModelName`  — the model name of that related model. -/
structure LinkField where
  hasRemote : Bool
  remoteModelId : String
  remoteAppLabel : String
  remoteModelName : String
deriving Repr, DecidableEq

/-- The permission string for performing action `action` on the model named
`modelName` in application `appLabel`: `"<appLabel>.<action>_<modelName>"`. -/
def permString (appLabel modelName action : String) : String :=
  appLabel ++ "." ++ action ++ "_" ++ modelName

/-- Resolve the `(appLabel, modelName)` of the target model. It is taken from the
first field that refers to a related model whose identity differs from the parent
model; absent such a field, the link model's own `(selfAppLabel, selfModelName)`
is used. -/
def resolveTarget (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) : String × String :=
  match fields.find? (fun f => f.hasRemote && f.remoteModelId != parentModelId) with
  | some f => (f.remoteAppLabel, f.remoteModelName)
  | none => (selfAppLabel, selfModelName)

/-- True when the user holds, on the target model, at least one of the listed
action permissions. -/
def anyPermForTarget (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) (userPerms actions : List String) : Bool :=
  let t := resolveTarget selfAppLabel selfModelName parentModelId fields
  actions.any (fun a => userPerms.contains (permString t.1 t.2 a))
-- pure-end

-- post-conditions-start
/-- Input→output relation for the target-permission test: the result is true iff
the user holds at least one of the `actions` permissions on the resolved target
model. -/
def problem_spec_hasAnyPermsForTargetModel
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms actions : List String) (result : Bool) : Prop :=
  result = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions

/-- Input→output relation for the **add** action. On an auto-created link model
the result requires the *change* permission on the target model; otherwise it is
the caller-supplied decision `superResult`. -/
def problem_spec_hasAddPermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) (result : Bool) : Prop :=
  (autoCreated = true →
    result = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["change"]) ∧
  (autoCreated = false → result = superResult)

/-- Input→output relation for the **change** action. On an auto-created link model
the result requires the *change* permission on the target model; otherwise it is
the caller-supplied decision `superResult`. -/
def problem_spec_hasChangePermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) (result : Bool) : Prop :=
  (autoCreated = true →
    result = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["change"]) ∧
  (autoCreated = false → result = superResult)

/-- Input→output relation for the **delete** action. On an auto-created link model
the result requires the *change* permission on the target model; otherwise it is
the caller-supplied decision `superResult`. -/
def problem_spec_hasDeletePermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) (result : Bool) : Prop :=
  (autoCreated = true →
    result = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["change"]) ∧
  (autoCreated = false → result = superResult)

/-- Input→output relation for the **view** action. On an auto-created link model
the result requires the *view* OR *change* permission on the target model;
otherwise it is the caller-supplied decision `superResult`. -/
def problem_spec_hasViewPermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) (result : Bool) : Prop :=
  (autoCreated = true →
    result = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]) ∧
  (autoCreated = false → result = superResult)
-- post-conditions-end

-- impl-start
/-- Resolve the target model by scanning the fields (taking the first field that
points at a related model other than the parent), then report whether the user
holds any of the listed action permissions on it. -/
def implementation_hasAnyPermsForTargetModel
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms actions : List String) : Bool := Id.run do
  let mut appLabel := selfAppLabel
  let mut modelName := selfModelName
  for f in fields do
    if f.hasRemote && f.remoteModelId != parentModelId then
      appLabel := f.remoteAppLabel
      modelName := f.remoteModelName
      break
  for a in actions do
    if userPerms.contains (permString appLabel modelName a) then
      return true
  return false

def implementation_hasAddPermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) : Bool := Id.run do
  if autoCreated then
    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
  return superResult

def implementation_hasChangePermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) : Bool := Id.run do
  if autoCreated then
    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
  return superResult

def implementation_hasDeletePermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) : Bool := Id.run do
  if autoCreated then
    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
  return superResult

def implementation_hasViewPermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) : Bool := Id.run do
  if autoCreated then
    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
  return superResult
-- impl-end

-- proof-start

-- proof_aux for correct_hasAnyPermsForTargetModel
/-- The `(appLabel, modelName)` the first for-loop settles on: scan `fields` and
take the first field pointing at a related model other than the parent; else keep
`(selfAppLabel, selfModelName)`. This is `resolveTarget` by definition. -/
def resolvedPair (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) : String × String :=
  Id.run do
    let mut appLabel := selfAppLabel
    let mut modelName := selfModelName
    for f in fields do
      if f.hasRemote && f.remoteModelId != parentModelId then
        appLabel := f.remoteAppLabel
        modelName := f.remoteModelName
        break
    return (appLabel, modelName)

theorem resolve_loop_eq (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) :
    resolvedPair selfAppLabel selfModelName parentModelId fields
      = resolveTarget selfAppLabel selfModelName parentModelId fields := by
  unfold resolvedPair resolveTarget
  induction fields with
  | nil => rfl
  | cons f fs ih =>
    simp only [List.forIn_cons, List.find?_cons]
    by_cases h : f.hasRemote && f.remoteModelId != parentModelId
    · simp [h]
    · simp only [h]; exact ih

theorem scan_loop_eq (appLabel modelName : String) (userPerms actions : List String) :
    (Id.run do
      for a in actions do
        if userPerms.contains (permString appLabel modelName a) then
          return true
      return false)
      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
  simp only [Id.run]; induction actions with
  | nil => rfl
  | cons a as ih =>
    simp only [List.forIn_cons, List.any_cons]
    split
    · rename_i h; rw [h]; rfl
    · rename_i h; simp_all

-- proof_aux for correct_hasDeletePermission
theorem resolve_loop_eq_hasDeletePermission (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) :
    (Id.run do
      let mut appLabel := selfAppLabel
      let mut modelName := selfModelName
      for f in fields do
        if f.hasRemote && f.remoteModelId != parentModelId then
          appLabel := f.remoteAppLabel
          modelName := f.remoteModelName
          break
      return (appLabel, modelName)) = resolveTarget selfAppLabel selfModelName parentModelId fields := by
  unfold resolveTarget
  induction fields with
  | nil => rfl
  | cons hd tl ih =>
    cases hc : (hd.hasRemote && hd.remoteModelId != parentModelId) <;>
      simp only [List.forIn_cons, List.find?_cons, hc] <;> [exact ih; rfl]

theorem any_loop_eq (appLabel modelName : String) (userPerms actions : List String) :
    (Id.run do
      for a in actions do
        if userPerms.contains (permString appLabel modelName a) then
          return true
      return false) = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
  induction actions with
  | nil => rfl
  | cons a as ih =>
    simp only [List.forIn_cons, List.any_cons, List.contains_eq_mem] at ih ⊢
    by_cases h : permString appLabel modelName a ∈ userPerms
    · simp [h]
    · simp only [h, decide_false, Bool.false_eq_true, if_false, Bool.false_or]
      exact ih

theorem anyPerms_bridge (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) (userPerms actions : List String) :
    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
  simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget]
  have hf := resolve_loop_eq_hasDeletePermission selfAppLabel selfModelName parentModelId fields
  have ha := any_loop_eq (resolveTarget selfAppLabel selfModelName parentModelId fields).1
    (resolveTarget selfAppLabel selfModelName parentModelId fields).2 userPerms actions
  simp only [Id.run, bind, pure] at hf ha ⊢
  rw [← ha, ← hf]
  rfl

theorem impl_reduce (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) (userPerms : List String) (superResult : Bool) :
    implementation_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
      = (if autoCreated then
          implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
        else superResult) := by
  cases autoCreated <;> rfl

-- proof_aux for correct_hasViewPermission
def ResolveLoop (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) : String × String := Id.run do
  let mut appLabel := selfAppLabel
  let mut modelName := selfModelName
  for f in fields do
    if f.hasRemote && f.remoteModelId != parentModelId then
      appLabel := f.remoteAppLabel
      modelName := f.remoteModelName
      break
  return (appLabel, modelName)

def ActionsLoop (appLabel modelName : String)
    (userPerms actions : List String) : Bool := Id.run do
  for a in actions do
    if userPerms.contains (permString appLabel modelName a) then
      return true
  return false

theorem resolveLoop_eq (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) :
    ResolveLoop selfAppLabel selfModelName parentModelId fields
      = resolveTarget selfAppLabel selfModelName parentModelId fields := by
  induction fields with
  | nil => rfl
  | cons f fs ih =>
    simp only [ResolveLoop, resolveTarget, Id.run, List.forIn_cons, List.find?] at *
    by_cases h : (f.hasRemote && f.remoteModelId != parentModelId) = true
    · simp only [h, if_true]
      rfl
    · simp only [Bool.not_eq_true] at h
      simp only [h]
      simp only [Bool.false_eq_true, if_false]
      exact ih

theorem actionsLoop_eq (appLabel modelName : String)
    (userPerms actions : List String) :
    ActionsLoop appLabel modelName userPerms actions
      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
  induction actions with
  | nil => rfl
  | cons a as ih =>
    simp only [ActionsLoop, Id.run] at ih ⊢
    rw [List.forIn_cons]
    split <;> rename_i h <;>
      simp only [h, List.any_cons, Bool.true_or, Bool.false_or] <;>
      first | rfl | (rw [← ih]; rfl)

theorem anyPerms_impl_eq_spec (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) (userPerms actions : List String) :
    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
  simp only [anyPermForTarget, ← actionsLoop_eq, ← resolveLoop_eq]
  unfold implementation_hasAnyPermsForTargetModel ResolveLoop ActionsLoop
  rfl

theorem view_wrapper_reduce (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) :
    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
      = (if autoCreated then
          implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
        else superResult) := by
  simp only [implementation_hasViewPermission, Id.run]
  cases autoCreated <;> rfl

theorem view_true_branch (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) :
    autoCreated = true →
    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"] := by
  intro h
  rw [view_wrapper_reduce, h]
  simp only [if_true]
  exact anyPerms_impl_eq_spec selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]

theorem view_false_branch (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) :
    autoCreated = false →
    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
      = superResult := by
  intro h
  subst h
  rfl

theorem correct_hasAnyPermsForTargetModel :
    ∀ (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
      (userPerms actions : List String),
      problem_spec_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
        (implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions) := by
  intro selfAppLabel selfModelName parentModelId fields userPerms actions
  unfold problem_spec_hasAnyPermsForTargetModel implementation_hasAnyPermsForTargetModel anyPermForTarget
  -- Identify the target-resolution loop with `resolveTarget` (via `resolvedPair`)
  -- and the action-scan loop with `List.any`, then reduce to reflexivity.
  rw [← resolve_loop_eq selfAppLabel selfModelName parentModelId fields,
      ← scan_loop_eq]
  rfl

theorem correct_hasAddPermission :
    ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
      (fields : List LinkField) (userPerms : List String) (superResult : Bool),
      problem_spec_hasAddPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
        (implementation_hasAddPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
  intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
  constructor
  · intro hac
    subst hac
    have key : ∀ (sa sm : String),
        implementation_hasAnyPermsForTargetModel sa sm parentModelId fields userPerms ["change"]
          = anyPermForTarget sa sm parentModelId fields userPerms ["change"] := by
      intro sa sm
      induction fields generalizing sa sm with
      | nil =>
        simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
          Id.run, List.forIn_nil, List.find?_nil]
        by_cases hm : permString sa sm "change" ∈ userPerms <;> simp [hm] <;> rfl
      | cons f fs ih =>
        simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
          Id.run, List.forIn_cons, List.find?_cons]
        by_cases hc : (f.hasRemote && f.remoteModelId != parentModelId) = true
        · simp only [hc, if_true]
          by_cases hm : permString f.remoteAppLabel f.remoteModelName "change" ∈ userPerms <;>
            simp [hm] <;> rfl
        · have hb : (f.hasRemote && f.remoteModelId != parentModelId) = false := by
            simpa using hc
          have hih := ih sa sm
          simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
            Id.run] at hih
          simp only [hb, if_false, Bool.false_eq_true]
          simpa using hih
    simpa [implementation_hasAddPermission, Id.run] using key selfAppLabel selfModelName
  · intro hac
    subst hac
    rfl

theorem correct_hasChangePermission :
    ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
      (fields : List LinkField) (userPerms : List String) (superResult : Bool),
      problem_spec_hasChangePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
        (implementation_hasChangePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
  intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
  have key : ∀ (actions : List String),
    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
    intro actions
    have loop2 : ∀ (appLabel modelName : String),
      (Id.run do
        for a in actions do
          if userPerms.contains (permString appLabel modelName a) then
            return true
        return false)
      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
      intro appLabel modelName
      induction actions with
      | nil => rfl
      | cons hd tl ih =>
        rw [List.any_cons]
        simp only [List.forIn_cons, Id.run]
        by_cases h : userPerms.contains (permString appLabel modelName hd) = true
        · simp only [h, if_true, List.contains_eq_mem, decide_eq_true_eq] at *; rfl
        · simp only [Bool.not_eq_true] at h
          simp only [h, Bool.false_or]
          rw [← ih]; simp [Id.run]
    unfold implementation_hasAnyPermsForTargetModel anyPermForTarget
    simp only []
    induction fields with
    | nil => exact loop2 selfAppLabel selfModelName
    | cons hd tl ih =>
      simp only [List.forIn_cons, Id.run, resolveTarget, List.find?]
      by_cases h : hd.hasRemote && hd.remoteModelId != parentModelId
      · simp only [h, if_true]
        exact loop2 hd.remoteAppLabel hd.remoteModelName
      · simp only [h, Bool.false_eq_true, if_false]
        simp only [Id.run, resolveTarget] at ih
        exact ih
  constructor
  · intro hac
    unfold implementation_hasChangePermission
    simp only [hac, if_true, Id.run]
    exact key ["change"]
  · intro hac
    unfold implementation_hasChangePermission
    simp only [hac, Id.run]
    rfl

theorem correct_hasDeletePermission :
    ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
      (fields : List LinkField) (userPerms : List String) (superResult : Bool),
      problem_spec_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
        (implementation_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
  intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
  refine ⟨?_, ?_⟩
  · intro h
    simp only [impl_reduce, h, if_true, anyPerms_bridge]
  · intro h
    simp only [impl_reduce, h, Bool.false_eq_true, if_false]

theorem correct_hasViewPermission :
    ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
      (fields : List LinkField) (userPerms : List String) (superResult : Bool),
      problem_spec_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
        (implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
  intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
  refine ⟨?_, ?_⟩
  · intro h
    exact view_true_branch autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult h
  · intro h
    exact view_false_branch autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult h

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS A TOTAL FUNCTIONAL SPEC: every problem_spec_* postcondition pins `result` to an exact function of the inputs (anyPermForTarget over resolveTarget/permString for the autoCreated=true clause; superResult for autoCreated=false), and that function faithfully matches gold behavior (add/change/delete require ["change"], view requires ["view","change"]). Any impl that deviates observably has a mathematically-false correct_* theorem and cannot verify.

PROTOCOL / RESULTS (all; same_spec=True for all 8 files, verified via swebench_unified.markers.same_spec on lean backend):
Command per file: `bash scripts/lean_verify.sh <file>`, run concurrently ≤4 at a time.

- atk_1 (prepatch bug: add/change/delete defer to ["view","change"]): EXIT=1 (does NOT verify). errors at all 5 correct_* lines; the 3 mutating-action theorems are genuinely false. == prepatch_reproduced.
- atk_2 (partial-domain: non-autoCreated add returns `false`, dropping superResult): EXIT=1.
- atk_3 (boundary: view uses ["view"] only, drops change): EXIT=1.
- atk_4 (control-flow-effect: resolve loop drops the parent-model check, picks first remote field regardless): EXIT=1.
- atk_5 (ungrounded/wrong permission: add uses ["add"] instead of ["change"]): EXIT=1.
- atk_7 (control-flow: delete ignores autoCreated, always returns superResult): EXIT=1.
- atk_6 (ungrounded-oracle ECHO: impls directly return the pure spec function anyPermForTarget with the gold action lists): EXIT=0 VERIFIES. `#print axioms` on all 5 correct_* (file atk_6_ax.lean, EXIT=0): each 'does not depend on any axioms' (CLEAN). PER PROTOCOL materialized its faithful refined patch (atk_6_faithful.patch = behaviorally identical to gold, since atk_6 is behaviorally identical to gold) and RAN run_resolve("django__django-11149", patch): RESOLVED=True, note='resolved' (atk_6_resolve.out). So this verifying same-spec impl RESOLVES => benign echo, NOT a weakness (consistent with fixed G-EQ policy: resolving same-spec verifier is not a break).
- pos_control = gold Solution.lean (copied): EXIT=0 VERIFIES (the earlier pos_control.lean built with a generic brute proof failed the loop-based obligations, so I used the canonical gold artifact as the positive control; same_spec=True).

No verifying wrong-behavior impl exists whose faithful patch fails to resolve => NOT BROKEN. The only impl that closed with clean axioms (atk_6) is a behavioral echo of gold and RESOLVES.

REFINEMENT.MD AUDIT: No axioms declared or consumed (axioms-start/end declares none; no `axiom` keyword). Every leg is R (input observables selfAppLabel/selfModelName/parentModelId/fields/userPerms/superResult; superResult passthrough), I (the edited ["change"] add/change/delete branch and ["view","change"] view branch — identical concrete ops = the fix), or A-reference (target-model resolution loop over fields; permString for get_permission_codename which is UNCHANGED at base_commit e245046; has_perm modeled as set membership). NO kind-3 (A-consumed) legs. A-reference correspondence holds: permString app model action = app++"."++action++"_"++model exactly equals '%s.%s' % (app_label, '%s_%s'%(action,model_name)); field-scan (first non-parent remote field wins, else self) matches gold `for field in opts.fields: if field.remote_field and field.remote_field.model != self.parent_model`. G-CONF differential-tests these R/I/A-reference legs; G-AX is a skip stub (no consumed axioms). Correspondence faithful.

VERDICT: SOUND (≥5 distinct wrong impls attacked, none breaks the spec; the sole verifying same-spec impl resolves).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found between the modeled functions and the real repo callee at base_commit e245046bb6e (django/contrib/admin/options.py InlineModelAdmin, post-patch). Checks performed:

MECHANICAL: Solution.lean compiles via lean_verify.sh (exit 0, no sorry). #print axioms on all five correct_* theorems yields only [propext, Quot.sound] — no sorryAx, proofs are genuine. same_spec(Solution.lean, Solution_prepatch.lean) = True (spec view byte-identical; prepatch differs only in the elided impl). conformance_check.py: checked=130104, disagreements=0.

MODELING-BOUNDARY REVIEW against verified base-commit source:
1. permString app model action = app++"."++action++"_"++model faithfully composes '%s.%s' % (opts.app_label, get_permission_codename(perm, opts)) with the UNCHANGED callee get_permission_codename = '%s_%s' % (action, opts.model_name) (body confirmed at contrib/auth/__init__.py:195). Argument order (action before model_name) is correct.
2. resolveTarget (first field with hasRemote && remoteModelId != parentModelId, else self) matches the real loop `for field in opts.fields: if field.remote_field and field.remote_field.model != self.parent_model: opts = field.remote_field.model._meta; break`; Python's falsy-remote_field short-circuit is captured by hasRemote &&.
3. has_perm(s) ⇔ s ∈ userPerms is a definitional abstraction (userPerms IS the set of true perm strings), so it cannot disagree with the real lookup.
4. Action lists: add/change/delete → ["change"]; view → ["view","change"]; non-auto_created → superResult passthrough — all exactly match the gold patch.

The spec is not too strong and does not drift: on every input the modeled per-action decision equals the real patched method's decision. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction check for django__django-11149 (lean). Compared the mechanically-extracted spec view (swebench_unified.markers.spec_view over LeanBackend; same_spec self==True, spec-view region byte-identical to Solution_prepatch.lean) against the PUBLIC problem_statement only (hints excluded).

Gold edit: InlineModelAdmin.has_{add,change,delete}_permission on the auto_created branch now require the *change* permission on the target model (was deferring to has_view_permission = view OR change); has_view_permission stays view OR change; target resolution + permission lookup factored into new helper _has_any_perms_for_target_model.

Spec view states the correct input->output relation: add/change/delete require *change* on the resolved target model, view requires *view* OR *change*, plus target-model resolution (first non-parent remote field) and the permission-string format. Judgment:
- The public problem_statement already establishes the discriminating behavior: it reports the bug that a view-only user can add/remove auto-created M2M inline rows, i.e. view permission must NOT admit editing. That a mutating action should instead require the *change* permission is directly derivable from the bug report + Django's standard permission model; the spec does not hand over any hidden discriminator beyond it.
- Target resolution and the codename/permission-string format are PRE-EXISTING behavior (present in the prepatch spec view too, same_spec True), not the fix, so they cannot leak the edit.
- No implementation-structure leak: the helper name _has_any_perms_for_target_model, the refactor shape, gold-patch comments, and the verbatim token `auto_created` are absent; the spec uses abstract prose ('auto-created link model', a caller-supplied super decision).
- G-LEAK lexical screen recorded pass (failures: []); patch_equals_gold True.

No spec-view line quotes the gold patch or reveals the fix beyond the public problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
