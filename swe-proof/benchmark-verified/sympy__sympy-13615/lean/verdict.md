# P2 adversarial audit — sympy__sympy-13615

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

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,20 +58,18 @@
   result.unresolved = other.filter (fun el => contains el = none)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_partitionByMembership {α : Type}
     (contains : α → Option Bool) (other : List α) :
     ComplementResult α := Id.run do
   let mut kept : List α := []
-  let mut unresolved : List α := []
   for el in other do
     match contains el with
-    | some true => pure ()            -- definite member: dropped from both groups
-    | some false => kept := kept ++ [el]
-    | none => unresolved := unresolved ++ [el]
-  return { kept := kept, unresolved := unresolved }
+    | some true => pure ()
+    | _ => kept := kept ++ [el]      -- prepatch: none lumped with some false
+  return { kept := kept, unresolved := [] }
 -- impl-end
-
 
 -- proof-start
 theorem correct_partitionByMembership {α : Type} :
@@ -79,34 +77,13 @@
       problem_spec_partitionByMembership contains other
         (implementation_partitionByMembership contains other) := by
   intro contains other
-  simp only [problem_spec_partitionByMembership, implementation_partitionByMembership, Id.run,
-    bind_pure_comp, map_pure]
-  have key : ∀ (l : List α) (k u : List α),
-      (forIn l ((⟨k, u⟩ : MProd (List α) (List α)) : MProd (List α) (List α)) (fun el r =>
-        match contains el with
-        | some true => pure (ForInStep.yield ⟨r.fst, r.snd⟩)
-        | some false => pure (ForInStep.yield ⟨r.fst ++ [el], r.snd⟩)
-        | none => pure (ForInStep.yield ⟨r.fst, r.snd ++ [el]⟩)) : Id (MProd (List α) (List α)))
-      = (⟨k ++ l.filter (fun el => contains el = some false),
-          u ++ l.filter (fun el => contains el = none)⟩ : MProd (List α) (List α)) := by
-    intro l
-    induction l with
-    | nil =>
-      intro k u
-      simp only [List.forIn_nil, List.filter_nil, List.append_nil]
-      rfl
+  simp only [problem_spec_partitionByMembership, implementation_partitionByMembership, Id.run]
+  refine ⟨?_, ?_⟩ <;>
+  · induction other with
+    | nil => simp
     | cons hd tl ih =>
-      intro k u
       simp only [List.forIn_cons, List.filter_cons]
       rcases h : contains hd with _ | b
-      · simp only [ih]
-        simp
-      · cases b
-        · simp only [ih]
-          simp
-        · simp only [ih]
-          simp
-  rw [key other [] []]
-  refine ⟨?_, ?_⟩ <;> rfl
-
+      · simp_all
+      · cases b <;> simp_all
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,6 +58,7 @@
   result.unresolved = other.filter (fun el => contains el = none)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_partitionByMembership {α : Type}
     (contains : α → Option Bool) (other : List α) :
@@ -66,12 +67,11 @@
   let mut unresolved : List α := []
   for el in other do
     match contains el with
-    | some true => pure ()            -- definite member: dropped from both groups
-    | some false => kept := kept ++ [el]
-    | none => unresolved := unresolved ++ [el]
+    | some true => pure ()
+    | some false => unresolved := unresolved ++ [el]   -- swapped
+    | none => kept := kept ++ [el]                      -- swapped
   return { kept := kept, unresolved := unresolved }
 -- impl-end
-
 
 -- proof-start
 theorem correct_partitionByMembership {α : Type} :
@@ -79,34 +79,13 @@
       problem_spec_partitionByMembership contains other
         (implementation_partitionByMembership contains other) := by
   intro contains other
-  simp only [problem_spec_partitionByMembership, implementation_partitionByMembership, Id.run,
-    bind_pure_comp, map_pure]
-  have key : ∀ (l : List α) (k u : List α),
-      (forIn l ((⟨k, u⟩ : MProd (List α) (List α)) : MProd (List α) (List α)) (fun el r =>
-        match contains el with
-        | some true => pure (ForInStep.yield ⟨r.fst, r.snd⟩)
-        | some false => pure (ForInStep.yield ⟨r.fst ++ [el], r.snd⟩)
-        | none => pure (ForInStep.yield ⟨r.fst, r.snd ++ [el]⟩)) : Id (MProd (List α) (List α)))
-      = (⟨k ++ l.filter (fun el => contains el = some false),
-          u ++ l.filter (fun el => contains el = none)⟩ : MProd (List α) (List α)) := by
-    intro l
-    induction l with
-    | nil =>
-      intro k u
-      simp only [List.forIn_nil, List.filter_nil, List.append_nil]
-      rfl
+  simp only [problem_spec_partitionByMembership, implementation_partitionByMembership, Id.run]
+  refine ⟨?_, ?_⟩ <;>
+  · induction other with
+    | nil => simp
     | cons hd tl ih =>
-      intro k u
       simp only [List.forIn_cons, List.filter_cons]
       rcases h : contains hd with _ | b
-      · simp only [ih]
-        simp
-      · cases b
-        · simp only [ih]
-          simp
-        · simp only [ih]
-          simp
-  rw [key other [] []]
-  refine ⟨?_, ?_⟩ <;> rfl
-
+      · simp_all
+      · cases b <;> simp_all
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,6 +58,7 @@
   result.unresolved = other.filter (fun el => contains el = none)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_partitionByMembership {α : Type}
     (contains : α → Option Bool) (other : List α) :
@@ -66,12 +67,11 @@
   let mut unresolved : List α := []
   for el in other do
     match contains el with
-    | some true => pure ()            -- definite member: dropped from both groups
-    | some false => kept := kept ++ [el]
+    | some true => pure ()
+    | some false => kept := el :: kept                 -- reversed order
     | none => unresolved := unresolved ++ [el]
   return { kept := kept, unresolved := unresolved }
 -- impl-end
-
 
 -- proof-start
 theorem correct_partitionByMembership {α : Type} :
@@ -79,34 +79,13 @@
       problem_spec_partitionByMembership contains other
         (implementation_partitionByMembership contains other) := by
   intro contains other
-  simp only [problem_spec_partitionByMembership, implementation_partitionByMembership, Id.run,
-    bind_pure_comp, map_pure]
-  have key : ∀ (l : List α) (k u : List α),
-      (forIn l ((⟨k, u⟩ : MProd (List α) (List α)) : MProd (List α) (List α)) (fun el r =>
-        match contains el with
-        | some true => pure (ForInStep.yield ⟨r.fst, r.snd⟩)
-        | some false => pure (ForInStep.yield ⟨r.fst ++ [el], r.snd⟩)
-        | none => pure (ForInStep.yield ⟨r.fst, r.snd ++ [el]⟩)) : Id (MProd (List α) (List α)))
-      = (⟨k ++ l.filter (fun el => contains el = some false),
-          u ++ l.filter (fun el => contains el = none)⟩ : MProd (List α) (List α)) := by
-    intro l
-    induction l with
-    | nil =>
-      intro k u
-      simp only [List.forIn_nil, List.filter_nil, List.append_nil]
-      rfl
+  simp only [problem_spec_partitionByMembership, implementation_partitionByMembership, Id.run]
+  refine ⟨?_, ?_⟩ <;>
+  · induction other with
+    | nil => simp
     | cons hd tl ih =>
-      intro k u
       simp only [List.forIn_cons, List.filter_cons]
       rcases h : contains hd with _ | b
-      · simp only [ih]
-        simp
-      · cases b
-        · simp only [ih]
-          simp
-        · simp only [ih]
-          simp
-  rw [key other [] []]
-  refine ⟨?_, ?_⟩ <;> rfl
-
+      · simp_all
+      · cases b <;> simp_all
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,6 +58,7 @@
   result.unresolved = other.filter (fun el => contains el = none)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_partitionByMembership {α : Type}
     (contains : α → Option Bool) (other : List α) :
@@ -66,12 +67,11 @@
   let mut unresolved : List α := []
   for el in other do
     match contains el with
-    | some true => pure ()            -- definite member: dropped from both groups
+    | some true => kept := kept ++ [el]                -- wrong: keep members
     | some false => kept := kept ++ [el]
     | none => unresolved := unresolved ++ [el]
   return { kept := kept, unresolved := unresolved }
 -- impl-end
-
 
 -- proof-start
 theorem correct_partitionByMembership {α : Type} :
@@ -79,34 +79,13 @@
       problem_spec_partitionByMembership contains other
         (implementation_partitionByMembership contains other) := by
   intro contains other
-  simp only [problem_spec_partitionByMembership, implementation_partitionByMembership, Id.run,
-    bind_pure_comp, map_pure]
-  have key : ∀ (l : List α) (k u : List α),
-      (forIn l ((⟨k, u⟩ : MProd (List α) (List α)) : MProd (List α) (List α)) (fun el r =>
-        match contains el with
-        | some true => pure (ForInStep.yield ⟨r.fst, r.snd⟩)
-        | some false => pure (ForInStep.yield ⟨r.fst ++ [el], r.snd⟩)
-        | none => pure (ForInStep.yield ⟨r.fst, r.snd ++ [el]⟩)) : Id (MProd (List α) (List α)))
-      = (⟨k ++ l.filter (fun el => contains el = some false),
-          u ++ l.filter (fun el => contains el = none)⟩ : MProd (List α) (List α)) := by
-    intro l
-    induction l with
-    | nil =>
-      intro k u
-      simp only [List.forIn_nil, List.filter_nil, List.append_nil]
-      rfl
+  simp only [problem_spec_partitionByMembership, implementation_partitionByMembership, Id.run]
+  refine ⟨?_, ?_⟩ <;>
+  · induction other with
+    | nil => simp
     | cons hd tl ih =>
-      intro k u
       simp only [List.forIn_cons, List.filter_cons]
       rcases h : contains hd with _ | b
-      · simp only [ih]
-        simp
-      · cases b
-        · simp only [ih]
-          simp
-        · simp only [ih]
-          simp
-  rw [key other [] []]
-  refine ⟨?_, ?_⟩ <;> rfl
-
+      · simp_all
+      · cases b <;> simp_all
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,6 +58,7 @@
   result.unresolved = other.filter (fun el => contains el = none)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_partitionByMembership {α : Type}
     (contains : α → Option Bool) (other : List α) :
@@ -66,12 +67,11 @@
   let mut unresolved : List α := []
   for el in other do
     match contains el with
-    | some true => pure ()            -- definite member: dropped from both groups
+    | some true => pure ()
     | some false => kept := kept ++ [el]
-    | none => unresolved := unresolved ++ [el]
+    | none => pure ()                                  -- wrong: undetermined dropped
   return { kept := kept, unresolved := unresolved }
 -- impl-end
-
 
 -- proof-start
 theorem correct_partitionByMembership {α : Type} :
@@ -79,34 +79,13 @@
       problem_spec_partitionByMembership contains other
         (implementation_partitionByMembership contains other) := by
   intro contains other
-  simp only [problem_spec_partitionByMembership, implementation_partitionByMembership, Id.run,
-    bind_pure_comp, map_pure]
-  have key : ∀ (l : List α) (k u : List α),
-      (forIn l ((⟨k, u⟩ : MProd (List α) (List α)) : MProd (List α) (List α)) (fun el r =>
-        match contains el with
-        | some true => pure (ForInStep.yield ⟨r.fst, r.snd⟩)
-        | some false => pure (ForInStep.yield ⟨r.fst ++ [el], r.snd⟩)
-        | none => pure (ForInStep.yield ⟨r.fst, r.snd ++ [el]⟩)) : Id (MProd (List α) (List α)))
-      = (⟨k ++ l.filter (fun el => contains el = some false),
-          u ++ l.filter (fun el => contains el = none)⟩ : MProd (List α) (List α)) := by
-    intro l
-    induction l with
-    | nil =>
-      intro k u
-      simp only [List.forIn_nil, List.filter_nil, List.append_nil]
-      rfl
+  simp only [problem_spec_partitionByMembership, implementation_partitionByMembership, Id.run]
+  refine ⟨?_, ?_⟩ <;>
+  · induction other with
+    | nil => simp
     | cons hd tl ih =>
-      intro k u
       simp only [List.forIn_cons, List.filter_cons]
       rcases h : contains hd with _ | b
-      · simp only [ih]
-        simp
-      · cases b
-        · simp only [ih]
-          simp
-        · simp only [ih]
-          simp
-  rw [key other [] []]
-  refine ⟨?_, ?_⟩ <;> rfl
-
+      · simp_all
+      · cases b <;> simp_all
 -- proof-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -58,20 +58,14 @@
   result.unresolved = other.filter (fun el => contains el = none)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_partitionByMembership {α : Type}
     (contains : α → Option Bool) (other : List α) :
-    ComplementResult α := Id.run do
-  let mut kept : List α := []
-  let mut unresolved : List α := []
-  for el in other do
-    match contains el with
-    | some true => pure ()            -- definite member: dropped from both groups
-    | some false => kept := kept ++ [el]
-    | none => unresolved := unresolved ++ [el]
-  return { kept := kept, unresolved := unresolved }
+    ComplementResult α :=
+  { kept := other.filter (fun el => contains el = some false),
+    unresolved := other.filter (fun el => contains el = none) }
 -- impl-end
-
 
 -- proof-start
 theorem correct_partitionByMembership {α : Type} :
@@ -79,34 +73,5 @@
       problem_spec_partitionByMembership contains other
         (implementation_partitionByMembership contains other) := by
   intro contains other
-  simp only [problem_spec_partitionByMembership, implementation_partitionByMembership, Id.run,
-    bind_pure_comp, map_pure]
-  have key : ∀ (l : List α) (k u : List α),
-      (forIn l ((⟨k, u⟩ : MProd (List α) (List α)) : MProd (List α) (List α)) (fun el r =>
-        match contains el with
-        | some true => pure (ForInStep.yield ⟨r.fst, r.snd⟩)
-        | some false => pure (ForInStep.yield ⟨r.fst ++ [el], r.snd⟩)
-        | none => pure (ForInStep.yield ⟨r.fst, r.snd ++ [el]⟩)) : Id (MProd (List α) (List α)))
-      = (⟨k ++ l.filter (fun el => contains el = some false),
-          u ++ l.filter (fun el => contains el = none)⟩ : MProd (List α) (List α)) := by
-    intro l
-    induction l with
-    | nil =>
-      intro k u
-      simp only [List.forIn_nil, List.filter_nil, List.append_nil]
-      rfl
-    | cons hd tl ih =>
-      intro k u
-      simp only [List.forIn_cons, List.filter_cons]
-      rcases h : contains hd with _ | b
-      · simp only [ih]
-        simp
-      · cases b
-        · simp only [ih]
-          simp
-        · simp only [ih]
-          simp
-  rw [key other [] []]
-  refine ⟨?_, ?_⟩ <;> rfl
-
+  exact ⟨rfl, rfl⟩
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,6 +58,7 @@
   result.unresolved = other.filter (fun el => contains el = none)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_partitionByMembership {α : Type}
     (contains : α → Option Bool) (other : List α) :
@@ -66,12 +67,11 @@
   let mut unresolved : List α := []
   for el in other do
     match contains el with
-    | some true => pure ()            -- definite member: dropped from both groups
-    | some false => kept := kept ++ [el]
+    | some true => pure ()
+    | some false => kept := [el]                       -- wrong: only last kept
     | none => unresolved := unresolved ++ [el]
   return { kept := kept, unresolved := unresolved }
 -- impl-end
-
 
 -- proof-start
 theorem correct_partitionByMembership {α : Type} :
@@ -79,34 +79,13 @@
       problem_spec_partitionByMembership contains other
         (implementation_partitionByMembership contains other) := by
   intro contains other
-  simp only [problem_spec_partitionByMembership, implementation_partitionByMembership, Id.run,
-    bind_pure_comp, map_pure]
-  have key : ∀ (l : List α) (k u : List α),
-      (forIn l ((⟨k, u⟩ : MProd (List α) (List α)) : MProd (List α) (List α)) (fun el r =>
-        match contains el with
-        | some true => pure (ForInStep.yield ⟨r.fst, r.snd⟩)
-        | some false => pure (ForInStep.yield ⟨r.fst ++ [el], r.snd⟩)
-        | none => pure (ForInStep.yield ⟨r.fst, r.snd ++ [el]⟩)) : Id (MProd (List α) (List α)))
-      = (⟨k ++ l.filter (fun el => contains el = some false),
-          u ++ l.filter (fun el => contains el = none)⟩ : MProd (List α) (List α)) := by
-    intro l
-    induction l with
-    | nil =>
-      intro k u
-      simp only [List.forIn_nil, List.filter_nil, List.append_nil]
-      rfl
+  simp only [problem_spec_partitionByMembership, implementation_partitionByMembership, Id.run]
+  refine ⟨?_, ?_⟩ <;>
+  · induction other with
+    | nil => simp
     | cons hd tl ih =>
-      intro k u
       simp only [List.forIn_cons, List.filter_cons]
       rcases h : contains hd with _ | b
-      · simp only [ih]
-        simp
-      · cases b
-        · simp only [ih]
-          simp
-        · simp only [ih]
-          simp
-  rw [key other [] []]
-  refine ⟨?_, ?_⟩ <;> rfl
-
+      · simp_all
+      · cases b <;> simp_all
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Relative complement of a finite collection against another set, governed by a
three-valued membership test.

We are given a finite ordered collection of candidate elements and, for each
candidate, the outcome of testing whether it belongs to the set we are
subtracting. That test is three-valued: it may report a definite "yes", a
definite "no", or be undetermined (no definite answer is available, e.g. when
the candidate is a free symbol whose membership cannot be decided).

Forming the difference splits the candidates by that outcome:

* a candidate whose membership is a definite "yes" is excluded entirely — it
  appears in neither part of the result;
* a candidate whose membership is a definite "no" is retained as an explicit
  member of the difference;
* a candidate whose membership is undetermined is set aside separately, as a
  member that can be neither confirmed nor ruled out — it must NOT be treated as
  a confirmed member of the difference.

The result records the two retained groups, each in the candidates' original
order. Retaining undetermined candidates apart from confirmed-out candidates is
the whole point: undetermined membership is not the same as confirmed exclusion.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The three-valued membership outcome
-- for each candidate is supplied as an input classifier (`contains`), so the
-- behavior is grounded directly in the inputs and the proof needs no callee
-- contract. (G-AX is a skip stub.)
-- axioms-end

-- pure-start
/-- The two retained groups of a membership-governed difference:
`kept` are the candidates with a definite "no" outcome (confirmed members of the
difference), `unresolved` are the candidates with an undetermined outcome (set
aside, neither confirmed in nor out). Candidates with a definite "yes" appear in
neither group. -/
structure ComplementResult (α : Type) where
  kept : List α
  unresolved : List α
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The difference partitions the candidates by their three-valued membership
outcome: `kept` is exactly the subsequence of candidates whose outcome is a
definite "no" (`some false`), and `unresolved` is exactly the subsequence whose
outcome is undetermined (`none`); both preserve the input order. Candidates with
a definite "yes" (`some true`) occur in neither group. -/
def problem_spec_partitionByMembership {α : Type}
    (contains : α → Option Bool) (other : List α)
    (result : ComplementResult α) : Prop :=
  result.kept = other.filter (fun el => contains el = some false) ∧
  result.unresolved = other.filter (fun el => contains el = none)
-- post-conditions-end

-- impl-start
def implementation_partitionByMembership {α : Type}
    (contains : α → Option Bool) (other : List α) :
    ComplementResult α := Id.run do
  let mut kept : List α := []
  let mut unresolved : List α := []
  for el in other do
    match contains el with
    | some true => pure ()            -- definite member: dropped from both groups
    | some false => kept := kept ++ [el]
    | none => unresolved := unresolved ++ [el]
  return { kept := kept, unresolved := unresolved }
-- impl-end

-- proof-start
theorem correct_partitionByMembership {α : Type} :
    ∀ (contains : α → Option Bool) (other : List α),
      problem_spec_partitionByMembership contains other
        (implementation_partitionByMembership contains other) := by
  intro contains other
  simp only [problem_spec_partitionByMembership, implementation_partitionByMembership, Id.run,
    bind_pure_comp, map_pure]
  have key : ∀ (l : List α) (k u : List α),
      (forIn l ((⟨k, u⟩ : MProd (List α) (List α)) : MProd (List α) (List α)) (fun el r =>
        match contains el with
        | some true => pure (ForInStep.yield ⟨r.fst, r.snd⟩)
        | some false => pure (ForInStep.yield ⟨r.fst ++ [el], r.snd⟩)
        | none => pure (ForInStep.yield ⟨r.fst, r.snd ++ [el]⟩)) : Id (MProd (List α) (List α)))
      = (⟨k ++ l.filter (fun el => contains el = some false),
          u ++ l.filter (fun el => contains el = none)⟩ : MProd (List α) (List α)) := by
    intro l
    induction l with
    | nil =>
      intro k u
      simp only [List.forIn_nil, List.filter_nil, List.append_nil]
      rfl
    | cons hd tl ih =>
      intro k u
      simp only [List.forIn_cons, List.filter_cons]
      rcases h : contains hd with _ | b
      · simp only [ih]
        simp
      · cases b
        · simp only [ih]
          simp
        · simp only [ih]
          simp
  rw [key other [] []]
  refine ⟨?_, ?_⟩ <;> rfl

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec pins BOTH output fields to exact filters (result.kept = other.filter(contains·=some false) AND result.unresolved = other.filter(contains·=none)), leaving zero extensional slack — any faithful wrong impl is provably false against the frozen post-conditions and cannot close.

Same_spec confirmed True for all 7 attacks + pos_control (swebench_unified.markers.same_spec, lean); only the impl region edited, axioms/pure/pre/post byte-identical.

Verification (scripts/lean_verify.sh, 300s cap; run concurrently in two batches of 4):
- pos_control (gold impl+proof): exit 0 (verifies clean).
- atk_1 PREPATCH BUG (none lumped into kept, unresolved always []): exit 1, unsolved goals (kept wrongly gains none-elts, unresolved wrongly empty). Prepatch bug reproduced.
- atk_2 SWAP (some false->unresolved, none->kept): exit 1, unsolved goals.
- atk_3 ORDER (kept built with el::kept, reversed): exit 1, unsolved goals.
- atk_4 CONTROL-FLOW-EFFECT (definite members some true kept instead of dropped): exit 1, unsolved goals.
- atk_5 PARTIAL-DOMAIN (none dropped, unresolved stays []): exit 1, unsolved goals.
- atk_7 BOUNDARY (kept:=[el], only last some-false retained): exit 1, unsolved goals.
- atk_6 UNGROUNDED-ORACLE ECHO (impl returns the spec filters verbatim): exit 0; #print axioms => 'correct_partitionByMembership does not depend on any axioms' (clean). Extensionally = gold; faithful patch = gold patch.

Mandatory resolve run for the ONE verifying clean-axiom impl (atk_6): materialized its faithful patch (the gold patch) and ran run_resolve('sympy__sympy-13615', ..., retries=1) => RESOLVED=True COMPLETED=True note='resolved'. So the sole verifying candidate DOES resolve — no verify⇏correct break.

Refinement.md audit: NO axiom/opaque/constant/sorry declarations in Solution.lean. The three-valued classifier `contains : α → Option Bool` is a genuine INPUT PARAMETER (the R refinement of the gold's local ternary_sift wrapping the unchanged self.contains callee), NOT a consumed callee axiom or opaque global. Every leg in refinement.md is R or I; there are no A-consumed / A-reference legs and no kind-3 legs. G-AX is a legitimate skip stub. Correspondence R/I legs are exercised by G-CONF (conformance_check.py drives the real patched Set._complement). No A-leg correspondence concern applies.

Conclusion: 6 distinct genuinely-wrong impls all fail to verify; the only verifying impl is the extensional echo whose faithful (gold) patch RESOLVES under the official harness. Verify ⇒ correct holds for every tested candidate. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
Relative complement of a finite collection against another set, governed by a
three-valued membership test.

We are given a finite ordered collection of candidate elements and, for each
candidate, the outcome of testing whether it belongs to the set we are
subtracting. That test is three-valued: it may report a definite "yes", a
definite "no", or be undetermined (no definite answer is available, e.g. when
the candidate is a free symbol whose membership cannot be decided).

Forming the difference splits the candidates by that outcome:

* a candidate whose membership is a definite "yes" is excluded entirely — it
  appears in neither part of the result;
* a candidate whose membership is a definite "no" is retained as an explicit
  member of the difference;
* a candidate whose membership is undetermined is set aside separately, as a
  member that can be neither confirmed nor ruled out — it must NOT be treated as
  a confirmed member of the difference.

The result records the two retained groups, each in the candidates' original
order. Retaining undetermined candidates apart from confirmed-out candidates is
the whole point: undetermined membership is not the same as confirmed exclusion.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The three-valued membership outcome
-- for each candidate is supplied as an input classifier (`contains`), so the
-- behavior is grounded directly in the inputs and the proof needs no callee
-- contract. (G-AX is a skip stub.)
-- axioms-end

-- pure-start
/-- The two retained groups of a membership-governed difference:
`kept` are the candidates with a definite "no" outcome (confirmed members of the
difference), `unresolved` are the candidates with an undetermined outcome (set
aside, neither confirmed in nor out). Candidates with a definite "yes" appear in
neither group. -/
structure ComplementResult (α : Type) where
  kept : List α
  unresolved : List α
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The difference partitions the candidates by their three-valued membership
outcome: `kept` is exactly the subsequence of candidates whose outcome is a
definite "no" (`some false`), and `unresolved` is exactly the subsequence whose
outcome is undetermined (`none`); both preserve the input order. Candidates with
a definite "yes" (`some true`) occur in neither group. -/
def problem_spec_partitionByMembership {α : Type}
    (contains : α → Option Bool) (other : List α)
    (result : ComplementResult α) : Prop :=
  result.kept = other.filter (fun el => contains el = some false) ∧
  result.unresolved = other.filter (fun el => contains el = none)
-- post-conditions-end

-- impl-start
def implementation_partitionByMembership {α : Type}
    (contains : α → Option Bool) (other : List α) :
    ComplementResult α := Id.run do
  let mut kept : List α := []
  let mut unresolved : List α := []
  for el in other do
    match contains el with
    | some true => pure ()            -- definite member: dropped from both groups
    | some false => kept := kept ++ [el]
    | none => unresolved := unresolved ++ [el]
  return { kept := kept, unresolved := unresolved }
-- impl-end

-- proof-start
theorem correct_partitionByMembership {α : Type} :
    ∀ (contains : α → Option Bool) (other : List α),
      problem_spec_partitionByMembership contains other
        (implementation_partitionByMembership contains other) := by
  intro contains other
  simp only [problem_spec_partitionByMembership, implementation_partitionByMembership, Id.run,
    bind_pure_comp, map_pure]
  have key : ∀ (l : List α) (k u : List α),
      (forIn l ((⟨k, u⟩ : MProd (List α) (List α)) : MProd (List α) (List α)) (fun el r =>
        match contains el with
        | some true => pure (ForInStep.yield ⟨r.fst, r.snd⟩)
        | some false => pure (ForInStep.yield ⟨r.fst ++ [el], r.snd⟩)
        | none => pure (ForInStep.yield ⟨r.fst, r.snd ++ [el]⟩)) : Id (MProd (List α) (List α)))
      = (⟨k ++ l.filter (fun el => contains el = some false),
          u ++ l.filter (fun el => contains el = none)⟩ : MProd (List α) (List α)) := by
    intro l
    induction l with
    | nil =>
      intro k u
      simp only [List.forIn_nil, List.filter_nil, List.append_nil]
      rfl
    | cons hd tl ih =>
      intro k u
      simp only [List.forIn_cons, List.filter_cons]
      rcases h : contains hd with _ | b
      · simp only [ih]
        simp
      · cases b
        · simp only [ih]
          simp
        · simp only [ih]
          simp
  rw [key other [] []]
  refine ⟨?_, ?_⟩ <;> rfl

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec pins BOTH output fields to exact filters (result.kept = other.filter(contains·=some false) AND result.unresolved = other.filter(contains·=none)), leaving zero extensional slack — any faithful wrong impl is provably false against the frozen post-conditions and cannot close.

Same_spec confirmed True for all 7 attacks + pos_control (swebench_unified.markers.same_spec, lean); only the impl region edited, axioms/pure/pre/post byte-identical.

Verification (scripts/lean_verify.sh, 300s cap; run concurrently in two batches of 4):
- pos_control (gold impl+proof): exit 0 (verifies clean).
- atk_1 PREPATCH BUG (none lumped into kept, unresolved always []): exit 1, unsolved goals (kept wrongly gains none-elts, unresolved wrongly empty). Prepatch bug reproduced.
- atk_2 SWAP (some false->unresolved, none->kept): exit 1, unsolved goals.
- atk_3 ORDER (kept built with el::kept, reversed): exit 1, unsolved goals.
- atk_4 CONTROL-FLOW-EFFECT (definite members some true kept instead of dropped): exit 1, unsolved goals.
- atk_5 PARTIAL-DOMAIN (none dropped, unresolved stays []): exit 1, unsolved goals.
- atk_7 BOUNDARY (kept:=[el], only last some-false retained): exit 1, unsolved goals.
- atk_6 UNGROUNDED-ORACLE ECHO (impl returns the spec filters verbatim): exit 0; #print axioms => 'correct_partitionByMembership does not depend on any axioms' (clean). Extensionally = gold; faithful patch = gold patch.

Mandatory resolve run for the ONE verifying clean-axiom impl (atk_6): materialized its faithful patch (the gold patch) and ran run_resolve('sympy__sympy-13615', ..., retries=1) => RESOLVED=True COMPLETED=True note='resolved'. So the sole verifying candidate DOES resolve — no verify⇏correct break.

Refinement.md audit: NO axiom/opaque/constant/sorry declarations in Solution.lean. The three-valued classifier `contains : α → Option Bool` is a genuine INPUT PARAMETER (the R refinement of the gold's local ternary_sift wrapping the unchanged self.contains callee), NOT a consumed callee axiom or opaque global. Every leg in refinement.md is R or I; there are no A-consumed / A-reference legs and no kind-3 legs. G-AX is a legitimate skip stub. Correspondence R/I legs are exercised by G-CONF (conformance_check.py drives the real patched Set._complement). No A-leg correspondence concern applies.

Conclusion: 6 distinct genuinely-wrong impls all fail to verify; the only verifying impl is the extensional echo whose faithful (gold) patch RESOLVES under the official harness. Verify ⇒ correct holds for every tested candidate. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled fn: Set._complement FiniteSet branch (sympy/sets/sets.py:219 @ base_commit 50d8a102f0). Gold patch replaces `FiniteSet(*[el for el in other if self.contains(el) != True])` with a `ternary_sift`+`sift` three-way partition assembled as `Union(FiniteSet(*sifted[False]), Complement(FiniteSet(*sifted[None]), self, evaluate=False) if sifted[None] else S.EmptySet)`.

### Checks performed
(1) Compile/soundness: scripts/lean_verify.sh Solution.lean -> exit 0; `#print axioms correct_partitionByMembership` -> [propext, Quot.sound], NO sorryAx. Proof is genuine (structural induction on `other` via forIn key lemma, closes by rfl).

(2) Spec byte-identity: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean) = True under the Lean backend tables. The discriminator lives entirely in the elided impl/proof regions; prepatch (folds `none` into kept, unresolved always []) has a sorry proof that cannot close against the frozen spec -> correctly fails G-VERIFY.

(3) Real-callee differential: the input classifier `contains : α → Option Bool` is exactly the gold's `ternary_sift` normalization of the UNCHANGED `self.contains` callee (verified on real sympy objects: `Interval(-10,10).contains(2)` is BooleanTrue with `in [True,False]` True; `.contains(x)` is an And with `in [True,False]` False -> none). Spec pins kept = other.filter(contains·=some false) = sifted[False], unresolved = other.filter(contains·=none) = sifted[None]; some-true (sifted[True]) dropped from both, matching the gold never reading that bucket. Reconstructed the base-commit gold assembly and compared to the Lean spec's partition on the exact F2P case Complement(FiniteSet(x,y,2),Interval(-10,10)) -> Complement(FiniteSet(x,y),Interval(-10,10)) (matches) plus 4000 randomized (self,other) pairs over Intervals/Integers/Naturals/Reals/FiniteSet/EmptySet x symbol+number element bags -> checked=4000, divergences=0. (One apparent mismatch in an earlier probe (self=FiniteSet(1,2)) was a version artifact of the /tmp worktree sitting at a LATER commit 33b47e4 that uses fuzzy_bool, not the base ternary_sift path — my reconstruction IS the base gold, so it is not a spec defect.)

No input found where the modeled function disagrees with the real base-commit callee. The spec is neither too strong (every spec-satisfying impl yields the exact gold partition, hence resolving) nor drifted. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independent leakage/gold-reconstruction audit of the lean spec view for sympy__sympy-13615.

Mechanical G-LEAK screen (leakage.screen over spec_view): PASSES, hard_failures=[]. No diff markers, no gold-patch line reproduced (>=8 normalized chars), no patched file path (sympy/sets/sets.py absent) or module path, no narration terms. same_spec(Solution.lean, Solution_prepatch.lean)=True and same_spec vs patched region confirmed: the visible spec region (docstring + ComplementResult + problem_spec_partitionByMembership) is byte-identical while impl/proof are elided, so the discriminator lives entirely in the hidden regions. No relaxed_leakage flag — this is a genuine strict pass, not a deferral.

Gold-reconstruction analysis: patch-changed distinctive symbols = {ternary_sift, complement}. 'complement' is already public (problem_statement literally says Complement(...)) and only appears generically in the spec view (ComplementResult, 'relative complement'). 'ternary_sift'/'sift' appear NOWHERE in the spec view. The gold's HOW — sympy sift(other, ternary_sift), the Union(FiniteSet(*sifted[False]), Complement(FiniteSet(*sifted[None]), self, evaluate=False)) assembly, the sympy.utilities.iterables import, S.EmptySet — is not revealed by any spec-view line.

The spec view describes only WHAT correct behavior is: a three-valued membership partition (definite-yes excluded from both groups; definite-no retained; undetermined set aside separately as 'neither confirmed in nor out'). This is a faithful restatement of the PUBLIC expected output already in problem_statement: Complement(FiniteSet(x,y,2), Interval(-10,10)) -> {x,y}\[-10,10] means the numeric member 2 is removed and the symbolic x,y are kept in an unevaluated complement rather than dropped. Comments state spec behavior, not defect narration (no bug/fix/wrong/previously). Nothing in the spec view leaks the gold edit beyond the public problem_statement (hints_text not considered per policy).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.