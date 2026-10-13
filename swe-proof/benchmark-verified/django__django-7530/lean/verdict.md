# P2 adversarial audit — django__django-7530

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition is EXACT functional equality (result = pairsSpec apps), the tightest possible spec. Every closing impl is extensionally equal to the gold post-patch enumeration, so no verify-but-not-resolve divergence is possible. No wrong impl closed a proof, so there is no verifying attack whose refined patch needed a resolve run (patches empty).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,49 +48,16 @@
   let mut acc : List (String × String) := []
   for a in apps do
     for m in a.models do
-      acc := acc ++ [(a.label, m)]
+      acc := acc ++ [(m, a.label)]   -- WRONG: model/label swapped
   return acc
 -- impl-end
 
 -- proof-start
-/-- Inner loop: appending `(label, m)` for each `m` in `ms` to the accumulator
-`r` yields `r ++ ms.map (label, ·)`. Generalized over the accumulator `r`. -/
-private theorem inner_helper_consistency_pairs
-    (ms : List String) (lbl : String) (r : List (String × String)) :
-    ((forIn ms r (fun m r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [(lbl, m)])))
-        : Id (List (String × String))).run : List (String × String))
-      = r ++ ms.map (fun m => (lbl, m)) := by
-  induction ms generalizing r with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run_bind, Id.run_pure] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
-/-- Outer loop: running the nested `forIn` over `apps` starting from accumulator
-`r` yields `r ++ pairsSpec apps`. Generalized over the accumulator `r`. -/
-private theorem outer_helper_consistency_pairs
-    (apps : List App) (r : List (String × String)) :
-    ((forIn apps r (fun (a : App) (r : List (String × String)) => do
-        let r ← forIn a.models r
-          (fun m r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [(a.label, m)])))
-        pure PUnit.unit
-        pure (ForInStep.yield r)) : Id (List (String × String))).run : List (String × String))
-      = r ++ pairsSpec apps := by
-  induction apps generalizing r with
-  | nil => simp only [List.forIn_nil, pairsSpec, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run_bind, Id.run_pure] at ih ⊢
-    rw [inner_helper_consistency_pairs a.models a.label r, ih]
-    simp only [pairsSpec, appPairs, List.append_assoc]
-
 theorem correct_consistency_pairs : ∀ (apps : List App),
     problem_spec_consistency_pairs apps (implementation_consistency_pairs apps) := by
   intro apps
   unfold problem_spec_consistency_pairs implementation_consistency_pairs
-  have h := outer_helper_consistency_pairs apps []
-  simp only [Id.run, bind_pure, List.nil_append] at h ⊢
-  exact h
+  induction apps with
+  | nil => rfl
+  | cons a rest ih => simp_all [pairsSpec, appPairs]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,52 +45,22 @@
 -- impl-start
 def implementation_consistency_pairs
     (apps : List App) : List (String × String) := Id.run do
+  let mut allModels : List String := []
+  for a in apps do
+    allModels := allModels ++ a.models
   let mut acc : List (String × String) := []
   for a in apps do
-    for m in a.models do
+    for m in allModels do        -- WRONG: pairs each label with ALL models
       acc := acc ++ [(a.label, m)]
   return acc
 -- impl-end
 
 -- proof-start
-/-- Inner loop: appending `(label, m)` for each `m` in `ms` to the accumulator
-`r` yields `r ++ ms.map (label, ·)`. Generalized over the accumulator `r`. -/
-private theorem inner_helper_consistency_pairs
-    (ms : List String) (lbl : String) (r : List (String × String)) :
-    ((forIn ms r (fun m r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [(lbl, m)])))
-        : Id (List (String × String))).run : List (String × String))
-      = r ++ ms.map (fun m => (lbl, m)) := by
-  induction ms generalizing r with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run_bind, Id.run_pure] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
-/-- Outer loop: running the nested `forIn` over `apps` starting from accumulator
-`r` yields `r ++ pairsSpec apps`. Generalized over the accumulator `r`. -/
-private theorem outer_helper_consistency_pairs
-    (apps : List App) (r : List (String × String)) :
-    ((forIn apps r (fun (a : App) (r : List (String × String)) => do
-        let r ← forIn a.models r
-          (fun m r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [(a.label, m)])))
-        pure PUnit.unit
-        pure (ForInStep.yield r)) : Id (List (String × String))).run : List (String × String))
-      = r ++ pairsSpec apps := by
-  induction apps generalizing r with
-  | nil => simp only [List.forIn_nil, pairsSpec, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run_bind, Id.run_pure] at ih ⊢
-    rw [inner_helper_consistency_pairs a.models a.label r, ih]
-    simp only [pairsSpec, appPairs, List.append_assoc]
-
 theorem correct_consistency_pairs : ∀ (apps : List App),
     problem_spec_consistency_pairs apps (implementation_consistency_pairs apps) := by
   intro apps
   unfold problem_spec_consistency_pairs implementation_consistency_pairs
-  have h := outer_helper_consistency_pairs apps []
-  simp only [Id.run, bind_pure, List.nil_append] at h ⊢
-  exact h
+  induction apps with
+  | nil => rfl
+  | cons a rest ih => simp_all [pairsSpec, appPairs]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,53 +44,18 @@
 
 -- impl-start
 def implementation_consistency_pairs
-    (apps : List App) : List (String × String) := Id.run do
-  let mut acc : List (String × String) := []
-  for a in apps do
-    for m in a.models do
-      acc := acc ++ [(a.label, m)]
-  return acc
+    (apps : List App) : List (String × String) :=
+  match apps with
+  | [] => []
+  | a :: _ => appPairs a           -- WRONG: drops all apps after the first
 -- impl-end
 
 -- proof-start
-/-- Inner loop: appending `(label, m)` for each `m` in `ms` to the accumulator
-`r` yields `r ++ ms.map (label, ·)`. Generalized over the accumulator `r`. -/
-private theorem inner_helper_consistency_pairs
-    (ms : List String) (lbl : String) (r : List (String × String)) :
-    ((forIn ms r (fun m r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [(lbl, m)])))
-        : Id (List (String × String))).run : List (String × String))
-      = r ++ ms.map (fun m => (lbl, m)) := by
-  induction ms generalizing r with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run_bind, Id.run_pure] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
-/-- Outer loop: running the nested `forIn` over `apps` starting from accumulator
-`r` yields `r ++ pairsSpec apps`. Generalized over the accumulator `r`. -/
-private theorem outer_helper_consistency_pairs
-    (apps : List App) (r : List (String × String)) :
-    ((forIn apps r (fun (a : App) (r : List (String × String)) => do
-        let r ← forIn a.models r
-          (fun m r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [(a.label, m)])))
-        pure PUnit.unit
-        pure (ForInStep.yield r)) : Id (List (String × String))).run : List (String × String))
-      = r ++ pairsSpec apps := by
-  induction apps generalizing r with
-  | nil => simp only [List.forIn_nil, pairsSpec, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run_bind, Id.run_pure] at ih ⊢
-    rw [inner_helper_consistency_pairs a.models a.label r, ih]
-    simp only [pairsSpec, appPairs, List.append_assoc]
-
 theorem correct_consistency_pairs : ∀ (apps : List App),
     problem_spec_consistency_pairs apps (implementation_consistency_pairs apps) := by
   intro apps
   unfold problem_spec_consistency_pairs implementation_consistency_pairs
-  have h := outer_helper_consistency_pairs apps []
-  simp only [Id.run, bind_pure, List.nil_append] at h ⊢
-  exact h
+  cases apps with
+  | nil => rfl
+  | cons a rest => simp [pairsSpec, appPairs]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,49 +48,16 @@
   let mut acc : List (String × String) := []
   for a in apps do
     for m in a.models do
-      acc := acc ++ [(a.label, m)]
+      acc := (a.label, m) :: acc     -- WRONG: prepend => reversed order
   return acc
 -- impl-end
 
 -- proof-start
-/-- Inner loop: appending `(label, m)` for each `m` in `ms` to the accumulator
-`r` yields `r ++ ms.map (label, ·)`. Generalized over the accumulator `r`. -/
-private theorem inner_helper_consistency_pairs
-    (ms : List String) (lbl : String) (r : List (String × String)) :
-    ((forIn ms r (fun m r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [(lbl, m)])))
-        : Id (List (String × String))).run : List (String × String))
-      = r ++ ms.map (fun m => (lbl, m)) := by
-  induction ms generalizing r with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run_bind, Id.run_pure] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
-/-- Outer loop: running the nested `forIn` over `apps` starting from accumulator
-`r` yields `r ++ pairsSpec apps`. Generalized over the accumulator `r`. -/
-private theorem outer_helper_consistency_pairs
-    (apps : List App) (r : List (String × String)) :
-    ((forIn apps r (fun (a : App) (r : List (String × String)) => do
-        let r ← forIn a.models r
-          (fun m r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [(a.label, m)])))
-        pure PUnit.unit
-        pure (ForInStep.yield r)) : Id (List (String × String))).run : List (String × String))
-      = r ++ pairsSpec apps := by
-  induction apps generalizing r with
-  | nil => simp only [List.forIn_nil, pairsSpec, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run_bind, Id.run_pure] at ih ⊢
-    rw [inner_helper_consistency_pairs a.models a.label r, ih]
-    simp only [pairsSpec, appPairs, List.append_assoc]
-
 theorem correct_consistency_pairs : ∀ (apps : List App),
     problem_spec_consistency_pairs apps (implementation_consistency_pairs apps) := by
   intro apps
   unfold problem_spec_consistency_pairs implementation_consistency_pairs
-  have h := outer_helper_consistency_pairs apps []
-  simp only [Id.run, bind_pure, List.nil_append] at h ⊢
-  exact h
+  induction apps with
+  | nil => rfl
+  | cons a rest ih => simp_all [pairsSpec, appPairs]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,53 +44,14 @@
 
 -- impl-start
 def implementation_consistency_pairs
-    (apps : List App) : List (String × String) := Id.run do
-  let mut acc : List (String × String) := []
-  for a in apps do
-    for m in a.models do
-      acc := acc ++ [(a.label, m)]
-  return acc
+    (apps : List App) : List (String × String) :=
+  (pairsSpec apps).dropLast          -- WRONG: drops final pair (boundary)
 -- impl-end
 
 -- proof-start
-/-- Inner loop: appending `(label, m)` for each `m` in `ms` to the accumulator
-`r` yields `r ++ ms.map (label, ·)`. Generalized over the accumulator `r`. -/
-private theorem inner_helper_consistency_pairs
-    (ms : List String) (lbl : String) (r : List (String × String)) :
-    ((forIn ms r (fun m r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [(lbl, m)])))
-        : Id (List (String × String))).run : List (String × String))
-      = r ++ ms.map (fun m => (lbl, m)) := by
-  induction ms generalizing r with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run_bind, Id.run_pure] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
-/-- Outer loop: running the nested `forIn` over `apps` starting from accumulator
-`r` yields `r ++ pairsSpec apps`. Generalized over the accumulator `r`. -/
-private theorem outer_helper_consistency_pairs
-    (apps : List App) (r : List (String × String)) :
-    ((forIn apps r (fun (a : App) (r : List (String × String)) => do
-        let r ← forIn a.models r
-          (fun m r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [(a.label, m)])))
-        pure PUnit.unit
-        pure (ForInStep.yield r)) : Id (List (String × String))).run : List (String × String))
-      = r ++ pairsSpec apps := by
-  induction apps generalizing r with
-  | nil => simp only [List.forIn_nil, pairsSpec, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run_bind, Id.run_pure] at ih ⊢
-    rw [inner_helper_consistency_pairs a.models a.label r, ih]
-    simp only [pairsSpec, appPairs, List.append_assoc]
-
 theorem correct_consistency_pairs : ∀ (apps : List App),
     problem_spec_consistency_pairs apps (implementation_consistency_pairs apps) := by
   intro apps
   unfold problem_spec_consistency_pairs implementation_consistency_pairs
-  have h := outer_helper_consistency_pairs apps []
-  simp only [Id.run, bind_pure, List.nil_append] at h ⊢
-  exact h
+  simp
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,53 +44,14 @@
 
 -- impl-start
 def implementation_consistency_pairs
-    (apps : List App) : List (String × String) := Id.run do
-  let mut acc : List (String × String) := []
-  for a in apps do
-    for m in a.models do
-      acc := acc ++ [(a.label, m)]
-  return acc
+    (apps : List App) : List (String × String) :=
+  (pairsSpec apps).eraseDups         -- WRONG: removes duplicate pairs
 -- impl-end
 
 -- proof-start
-/-- Inner loop: appending `(label, m)` for each `m` in `ms` to the accumulator
-`r` yields `r ++ ms.map (label, ·)`. Generalized over the accumulator `r`. -/
-private theorem inner_helper_consistency_pairs
-    (ms : List String) (lbl : String) (r : List (String × String)) :
-    ((forIn ms r (fun m r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [(lbl, m)])))
-        : Id (List (String × String))).run : List (String × String))
-      = r ++ ms.map (fun m => (lbl, m)) := by
-  induction ms generalizing r with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run_bind, Id.run_pure] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
-/-- Outer loop: running the nested `forIn` over `apps` starting from accumulator
-`r` yields `r ++ pairsSpec apps`. Generalized over the accumulator `r`. -/
-private theorem outer_helper_consistency_pairs
-    (apps : List App) (r : List (String × String)) :
-    ((forIn apps r (fun (a : App) (r : List (String × String)) => do
-        let r ← forIn a.models r
-          (fun m r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [(a.label, m)])))
-        pure PUnit.unit
-        pure (ForInStep.yield r)) : Id (List (String × String))).run : List (String × String))
-      = r ++ pairsSpec apps := by
-  induction apps generalizing r with
-  | nil => simp only [List.forIn_nil, pairsSpec, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run_bind, Id.run_pure] at ih ⊢
-    rw [inner_helper_consistency_pairs a.models a.label r, ih]
-    simp only [pairsSpec, appPairs, List.append_assoc]
-
 theorem correct_consistency_pairs : ∀ (apps : List App),
     problem_spec_consistency_pairs apps (implementation_consistency_pairs apps) := by
   intro apps
   unfold problem_spec_consistency_pairs implementation_consistency_pairs
-  have h := outer_helper_consistency_pairs apps []
-  simp only [Id.run, bind_pure, List.nil_append] at h ⊢
-  exact h
+  simp
 -- proof-end
```

Attack 7 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,50 +47,17 @@
     (apps : List App) : List (String × String) := Id.run do
   let mut acc : List (String × String) := []
   for a in apps do
-    for m in a.models do
+    for m in a.models.reverse do     -- WRONG: model order reversed within each app
       acc := acc ++ [(a.label, m)]
   return acc
 -- impl-end
 
 -- proof-start
-/-- Inner loop: appending `(label, m)` for each `m` in `ms` to the accumulator
-`r` yields `r ++ ms.map (label, ·)`. Generalized over the accumulator `r`. -/
-private theorem inner_helper_consistency_pairs
-    (ms : List String) (lbl : String) (r : List (String × String)) :
-    ((forIn ms r (fun m r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [(lbl, m)])))
-        : Id (List (String × String))).run : List (String × String))
-      = r ++ ms.map (fun m => (lbl, m)) := by
-  induction ms generalizing r with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run_bind, Id.run_pure] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
-/-- Outer loop: running the nested `forIn` over `apps` starting from accumulator
-`r` yields `r ++ pairsSpec apps`. Generalized over the accumulator `r`. -/
-private theorem outer_helper_consistency_pairs
-    (apps : List App) (r : List (String × String)) :
-    ((forIn apps r (fun (a : App) (r : List (String × String)) => do
-        let r ← forIn a.models r
-          (fun m r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [(a.label, m)])))
-        pure PUnit.unit
-        pure (ForInStep.yield r)) : Id (List (String × String))).run : List (String × String))
-      = r ++ pairsSpec apps := by
-  induction apps generalizing r with
-  | nil => simp only [List.forIn_nil, pairsSpec, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run_bind, Id.run_pure] at ih ⊢
-    rw [inner_helper_consistency_pairs a.models a.label r, ih]
-    simp only [pairsSpec, appPairs, List.append_assoc]
-
 theorem correct_consistency_pairs : ∀ (apps : List App),
     problem_spec_consistency_pairs apps (implementation_consistency_pairs apps) := by
   intro apps
   unfold problem_spec_consistency_pairs implementation_consistency_pairs
-  have h := outer_helper_consistency_pairs apps []
-  simp only [Id.run, bind_pure, List.nil_append] at h ⊢
-  exact h
+  induction apps with
+  | nil => rfl
+  | cons a rest ih => simp_all [pairsSpec, appPairs]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is invoked by the modeled behavior: the enumeration of
-- (application, model) pairs is modeled DEEPLY below (`App` / `appPairs` /
-- `pairsSpec`) from the application carrier itself, so there is no `opaque`
-- callee and no consumed `_prop` axiom here.
-- axioms-end

-- pure-start
/-- An application together with the models that belong to it.
* `label` identifies the application.
* `models` are the names of the models owned by this application. -/
structure App where
  label : String
  models : List String
deriving DecidableEq, Repr

/-- The (application, model) pairs contributed by a single application: each of
the application's OWN models, tagged with that application's label, in order. -/
def appPairs (a : App) : List (String × String) :=
  a.models.map (fun m => (a.label, m))

/-- The full enumeration of (application label, model name) pairs across a list
of applications: for each application in turn, every model that belongs to that
application, paired with the application's label, preserving order (a
front-recursive per-application fold). -/
def pairsSpec : List App → List (String × String)
  | [] => []
  | a :: rest => appPairs a ++ pairsSpec rest
-- pure-end

-- post-conditions-start
/-- The result is exactly the enumeration of (application label, model name)
pairs in which each model is paired ONLY with the application that owns it: for
every application, each of its own models — and no model belonging to a different
application — appears tagged with that application's label, in application order
and then model order. -/
def problem_spec_consistency_pairs
    (apps : List App) (result : List (String × String)) : Prop :=
  result = pairsSpec apps
-- post-conditions-end

-- impl-start
def implementation_consistency_pairs
    (apps : List App) : List (String × String) := Id.run do
  let mut acc : List (String × String) := []
  for a in apps do
    for m in a.models do
      acc := acc ++ [(a.label, m)]
  return acc
-- impl-end

-- proof-start
/-- Inner loop: appending `(label, m)` for each `m` in `ms` to the accumulator
`r` yields `r ++ ms.map (label, ·)`. Generalized over the accumulator `r`. -/
private theorem inner_helper_consistency_pairs
    (ms : List String) (lbl : String) (r : List (String × String)) :
    ((forIn ms r (fun m r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [(lbl, m)])))
        : Id (List (String × String))).run : List (String × String))
      = r ++ ms.map (fun m => (lbl, m)) := by
  induction ms generalizing r with
  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run_bind, Id.run_pure] at ih ⊢
    rw [ih]
    simp [List.append_assoc]

/-- Outer loop: running the nested `forIn` over `apps` starting from accumulator
`r` yields `r ++ pairsSpec apps`. Generalized over the accumulator `r`. -/
private theorem outer_helper_consistency_pairs
    (apps : List App) (r : List (String × String)) :
    ((forIn apps r (fun (a : App) (r : List (String × String)) => do
        let r ← forIn a.models r
          (fun m r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [(a.label, m)])))
        pure PUnit.unit
        pure (ForInStep.yield r)) : Id (List (String × String))).run : List (String × String))
      = r ++ pairsSpec apps := by
  induction apps generalizing r with
  | nil => simp only [List.forIn_nil, pairsSpec, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run_bind, Id.run_pure] at ih ⊢
    rw [inner_helper_consistency_pairs a.models a.label r, ih]
    simp only [pairsSpec, appPairs, List.append_assoc]

theorem correct_consistency_pairs : ∀ (apps : List App),
    problem_spec_consistency_pairs apps (implementation_consistency_pairs apps) := by
  intro apps
  unfold problem_spec_consistency_pairs implementation_consistency_pairs
  have h := outer_helper_consistency_pairs apps []
  simp only [Id.run, bind_pure, List.nil_append] at h ⊢
  exact h
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 9 attack files confirmed same_spec=True via swebench_unified.markers.same_spec (impl region only edited; axioms/pure/pre/post byte-identical).

POSITIVE CONTROL: pos_control.lean (gold Solution.lean) -> lean_verify.sh exit 0; #print axioms correct_consistency_pairs = [propext, Quot.sound] (clean, no sorryAx).

### ATTACK BATTERY (7 distinct wrong impls, each verified via `bash scripts/lean_verify.sh <f>` from project root):
- atk_1 (wrong-pairing: label/model swapped per pair): exit 1, unsolved goals -> does NOT close. CORRECTLY REJECTED.
- atk_2 (cross-product = THE PREPATCH BUG: each label x all project models, mirrors Solution_prepatch.lean): exit 1, unsolved goals -> does NOT close. Prepatch bug reproduced/unclosable.
- atk_3 (partial domain: only first app's pairs, drops rest): exit 1, unsolved goals -> does NOT close.
- atk_4 (control-flow-effect: prepend `::` => reversed result order): exit 1, unsolved goals -> does NOT close.
- atk_5 (boundary: (pairsSpec apps).dropLast, drops final pair): exit 1, `simp` made no progress -> does NOT close.
- atk_6 (eraseDups: removes duplicate pairs): exit 1, `simp` made no progress -> does NOT close.
- atk_9 (inner model order reversed via a.models.reverse): exit 1, unsolved goals -> does NOT close.

### CORRECT-BEHAVIOR ECHOES (sanity, confirm spec admits varied SYNTAX not pinned to one shape):
- atk_7 (ungrounded-oracle echo: impl := pairsSpec apps): exit 0 CLOSES; #print axioms = 'does not depend on any axioms' (cleaner than gold). BEHAVIORALLY = gold, so its refined patch is the gold one-line change and RESOLVES; not a break.
- atk_8 (flatMap alt-shape): behaviorally = gold (my proof line was incomplete; irrelevant since behavior matches gold).

DECIDABLE DISPROOFS (disproof.lean, exit 0): machine-proved that the swap, cross-product, partial-domain, reversed, dropLast, and reversed-models behaviors are DECIDABLY UNEQUAL to pairsSpec on concrete 2-app/2-model inputs via `decide`. This confirms the failed attacks are genuinely UNCLOSABLE (postcondition is provably false), not merely proofs I couldn't find. Since result = pairsSpec is exact equality, ANY behavioral deviation is refuted the same way.

MANDATORY RESOLVE STEP: vacuous. No wrong impl produced a closing clean-axiom proof, so there is no verifying-but-wrong impl requiring a materialized faithful patch + run_resolve. The verify=>correct implication holds: closing correct_ forces behavioral equality to the gold enumeration.

REFINEMENT.MD LEG AUDIT: 4 legs, all R / A-reference / I; no kind-3 (changed-inexpressible). Axioms region empty (no A-consumed, no opaque). Leg 3 A-reference: deep model App.models corresponds to real callee AppConfig.get_models() (django/apps/config.py:174, yields only the app's own models); correspondence holds. connection.alias correctly excluded as per-call constant (leg 4, I). G-AX = skip (deeply modeled). Correspondence is faithful.

CONCLUSION: SOUND. 7 distinct wrong impls attempted + machine-disproved; none closes; the only closing impls are behaviorally identical to gold and resolve. verify=>correct upheld.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition is EXACT functional equality (result = pairsSpec apps), the tightest possible spec. Every closing impl is extensionally equal to the gold post-patch enumeration, so no verify-but-not-resolve divergence is possible. No wrong impl closed a proof, so there is no verifying attack whose refined patch needed a resolve run (patches empty).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is invoked by the modeled behavior: the enumeration of
-- (application, model) pairs is modeled DEEPLY below (`App` / `appPairs` /
-- `pairsSpec`) from the application carrier itself, so there is no `opaque`
-- callee and no consumed `_prop` axiom here.
-- axioms-end

-- pure-start
/-- An application together with the models that belong to it.
* `label` identifies the application.
* `models` are the names of the models owned by this application. -/
structure App where
  label : String
  models : List String
deriving DecidableEq, Repr

/-- The (application, model) pairs contributed by a single application: each of
the application's OWN models, tagged with that application's label, in order. -/
def appPairs (a : App) : List (String × String) :=
  a.models.map (fun m => (a.label, m))

/-- The full enumeration of (application label, model name) pairs across a list
of applications: for each application in turn, every model that belongs to that
application, paired with the application's label, preserving order (a
front-recursive per-application fold). -/
def pairsSpec : List App → List (String × String)
  | [] => []
  | a :: rest => appPairs a ++ pairsSpec rest
-- pure-end

-- post-conditions-start
/-- The result is exactly the enumeration of (application label, model name)
pairs in which each model is paired ONLY with the application that owns it: for
every application, each of its own models — and no model belonging to a different
application — appears tagged with that application's label, in application order
and then model order. -/
def problem_spec_consistency_pairs
    (apps : List App) (result : List (String × String)) : Prop :=
  result = pairsSpec apps
-- post-conditions-end

-- impl-start
def implementation_consistency_pairs
    (apps : List App) : List (String × String) := Id.run do
  let mut acc : List (String × String) := []
  for a in apps do
    for m in a.models do
      acc := acc ++ [(a.label, m)]
  return acc
-- impl-end

-- proof-start
/-- Inner loop: appending `(label, m)` for each `m` in `ms` to the accumulator
`r` yields `r ++ ms.map (label, ·)`. Generalized over the accumulator `r`. -/
private theorem inner_helper_consistency_pairs
    (ms : List String) (lbl : String) (r : List (String × String)) :
    ((forIn ms r (fun m r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [(lbl, m)])))
        : Id (List (String × String))).run : List (String × String))
      = r ++ ms.map (fun m => (lbl, m)) := by
  induction ms generalizing r with
  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run_bind, Id.run_pure] at ih ⊢
    rw [ih]
    simp [List.append_assoc]

/-- Outer loop: running the nested `forIn` over `apps` starting from accumulator
`r` yields `r ++ pairsSpec apps`. Generalized over the accumulator `r`. -/
private theorem outer_helper_consistency_pairs
    (apps : List App) (r : List (String × String)) :
    ((forIn apps r (fun (a : App) (r : List (String × String)) => do
        let r ← forIn a.models r
          (fun m r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [(a.label, m)])))
        pure PUnit.unit
        pure (ForInStep.yield r)) : Id (List (String × String))).run : List (String × String))
      = r ++ pairsSpec apps := by
  induction apps generalizing r with
  | nil => simp only [List.forIn_nil, pairsSpec, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run_bind, Id.run_pure] at ih ⊢
    rw [inner_helper_consistency_pairs a.models a.label r, ih]
    simp only [pairsSpec, appPairs, List.append_assoc]

theorem correct_consistency_pairs : ∀ (apps : List App),
    problem_spec_consistency_pairs apps (implementation_consistency_pairs apps) := by
  intro apps
  unfold problem_spec_consistency_pairs implementation_consistency_pairs
  have h := outer_helper_consistency_pairs apps []
  simp only [Id.run, bind_pure, List.nil_append] at h ⊢
  exact h
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 9 attack files confirmed same_spec=True via swebench_unified.markers.same_spec (impl region only edited; axioms/pure/pre/post byte-identical).

POSITIVE CONTROL: pos_control.lean (gold Solution.lean) -> lean_verify.sh exit 0; #print axioms correct_consistency_pairs = [propext, Quot.sound] (clean, no sorryAx).

### ATTACK BATTERY (7 distinct wrong impls, each verified via `bash scripts/lean_verify.sh <f>` from project root):
- atk_1 (wrong-pairing: label/model swapped per pair): exit 1, unsolved goals -> does NOT close. CORRECTLY REJECTED.
- atk_2 (cross-product = THE PREPATCH BUG: each label x all project models, mirrors Solution_prepatch.lean): exit 1, unsolved goals -> does NOT close. Prepatch bug reproduced/unclosable.
- atk_3 (partial domain: only first app's pairs, drops rest): exit 1, unsolved goals -> does NOT close.
- atk_4 (control-flow-effect: prepend `::` => reversed result order): exit 1, unsolved goals -> does NOT close.
- atk_5 (boundary: (pairsSpec apps).dropLast, drops final pair): exit 1, `simp` made no progress -> does NOT close.
- atk_6 (eraseDups: removes duplicate pairs): exit 1, `simp` made no progress -> does NOT close.
- atk_9 (inner model order reversed via a.models.reverse): exit 1, unsolved goals -> does NOT close.

### CORRECT-BEHAVIOR ECHOES (sanity, confirm spec admits varied SYNTAX not pinned to one shape):
- atk_7 (ungrounded-oracle echo: impl := pairsSpec apps): exit 0 CLOSES; #print axioms = 'does not depend on any axioms' (cleaner than gold). BEHAVIORALLY = gold, so its refined patch is the gold one-line change and RESOLVES; not a break.
- atk_8 (flatMap alt-shape): behaviorally = gold (my proof line was incomplete; irrelevant since behavior matches gold).

DECIDABLE DISPROOFS (disproof.lean, exit 0): machine-proved that the swap, cross-product, partial-domain, reversed, dropLast, and reversed-models behaviors are DECIDABLY UNEQUAL to pairsSpec on concrete 2-app/2-model inputs via `decide`. This confirms the failed attacks are genuinely UNCLOSABLE (postcondition is provably false), not merely proofs I couldn't find. Since result = pairsSpec is exact equality, ANY behavioral deviation is refuted the same way.

MANDATORY RESOLVE STEP: vacuous. No wrong impl produced a closing clean-axiom proof, so there is no verifying-but-wrong impl requiring a materialized faithful patch + run_resolve. The verify=>correct implication holds: closing correct_ forces behavioral equality to the gold enumeration.

REFINEMENT.MD LEG AUDIT: 4 legs, all R / A-reference / I; no kind-3 (changed-inexpressible). Axioms region empty (no A-consumed, no opaque). Leg 3 A-reference: deep model App.models corresponds to real callee AppConfig.get_models() (django/apps/config.py:174, yields only the app's own models); correspondence holds. connection.alias correctly excluded as per-call constant (leg 4, I). G-AX = skip (deeply modeled). Correspondence is faithful.

CONCLUSION: SOUND. 7 distinct wrong impls attempted + machine-disproved; none closes; the only closing impls are behaviorally identical to gold and resolve. verify=>correct upheld.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on django__django-7530 lean bundle. VERIFICATION: Solution.lean compiles clean via scripts/lean_verify.sh (exit 0); `#print axioms correct_consistency_pairs` => [propext, Quot.sound] with NO sorryAx (genuine proof); same_spec(Solution, Solution_prepatch, lean tables) = True (spec region byte-identical). Real repo confirmed @ base: post-patch `for model in apps.get_app_config(app_label).get_models()` yields only the app's OWN models (config.py iterates self.models.values() filtering auto_created/swapped); pre-patch `apps.get_models(app_label)` ignores the label (bound to include_auto_created) and returns ALL project models -> cross-product bug.

MODELED FUNCTION = pairsSpec: for each App in the input List App, pair its label with each of its own models, in order. This is exactly the post-patch (app_label, model_name) enumeration.

### DRIFT/OVER-STRENGTH ANALYSIS (attacked 3 boundaries, none breaks faithfulness):
1) ORDER: real `consistency_check_labels` is a Python SET (arbitrary hash iteration order); spec pins an exact ordered List App. This is the only nominal over-strengthening. However it is behaviorally INERT: the enumeration feeds any(...), whose truth value is order- and multiplicity-independent and short-circuits; router.allow_migrate is a read-only query. mapping.md explicitly documents the any(...) consumer as dropped and takes an already-ordered carrier. No resolving impl is distinguished by pair ordering, so pinning order neither rejects a valid impl nor accepts a wrong one. Not a defect.
2) auto_created/swapped filtering: documented as folded into App.models (the app's visible owned models), outside modeled domain; affects WHICH of an app's own models appear, not attribution (the bug). Sound.
3) ATTRIBUTION (the actual fix): spec pairs each model ONLY with its owning app; cross-product prepatch is correctly unclosable (G-DIFF pass). Empty-app / empty-list edges match (appPairs [] = []). G-CONF passed 120006 inputs 0 disagreements (seed 7530); G-AX probe confirms attribution invariant on real registry.

No input exists where the modeled function disagrees with the real callee in any behaviorally-observable way. Spec is faithful (and not too strong in any consequential sense).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, no hard failures) and semantic review confirms no leak beyond the public problem_statement. The problem_statement already discloses the correct end-state behavior: makemigrations 'incorrectly calls allow_migrate() for each app with all the models in the project rather than for each app with the app's models' — i.e. each app must be paired only with its own models. The spec view's post-condition ('each model is paired ONLY with the application that owns it … no model belonging to a different application') merely restates this publicly-known intended behavior. Nothing in the spec view reveals the gold edit (apps.get_models(app_label) → apps.get_app_config(app_label).get_models()): no repo symbols (get_models/get_app_config/allow_migrate/router/consistency_check_labels), no file/module path (makemigrations.py), no diff markers, no dotted module path. Spec-view identifiers (App, appPairs, pairsSpec, label, models) are generic modeling names; 'app'/'models' are already in the task. Comments contain no narration terms (bug/fix/incorrectly/wrong) and the axioms/docstring rationale is abstract (deep modeling, ownership attribution) without naming the edit. Bug/fix narration is confined to refinement.md and mapping.md (audit-only artifacts, not part of the spec view). The impl and proof regions are elided in the spec view.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
