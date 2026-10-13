# P2 adversarial audit — sympy__sympy-20154

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_partitions is a COMPLETE specification: result.length = states.length AND (forall i < states.length, result.getD i [] = states.getD i []) together pin result = states extensionally. Every same-spec wrong impl I tried (partial-domain dropLast, boundary reverse, control-flow-effect getD 0, ungrounded-oracle echoes [] and getLastD, extra-element append) FAILS to verify. Only extensionally-identity impls verify (atk_5 `return states`, atk_7 `states.map id`), which are precisely the gold snapshot-on-yield behavior; their faithful refined patch IS the gold patch, which RESOLVES. No verifying impl has a non-resolving faithful patch, so verify does NOT imply weakness here.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,46 +41,20 @@
 -- impl-start
 def implementation_partitions (states : List PartMap) : List PartMap := Id.run do
   let mut out : List PartMap := []
-  for s in states do
-    -- emit the state current at this step as its own entry
-    out := out ++ [s]
+  for _s in states do
+    -- bug: emit the shared final state at every step
+    out := out ++ [states.getLastD []]
   return out
 -- impl-end
 
 -- proof-start
-/-- The append-accumulating `forIn` loop over `states`, generalized over the
-accumulator, is just `init ++ states`. -/
-theorem forIn_append_eq (states : List PartMap) (init : List PartMap) :
-    (Id.run (forIn states init (fun s r =>
-        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap))))))
-    = init ++ states := by
-  induction states generalizing init with
-  | nil => simp [Id.run, List.forIn_nil, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp
-
-theorem partitions_eq (states : List PartMap) :
-    implementation_partitions states = states := by
-  unfold implementation_partitions
-  have h2 : (forIn states ([] : List PartMap) fun s r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))
-          : Id (ForInStep (List PartMap))))
-      = (forIn states ([] : List PartMap) fun s r =>
-        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap)))) := rfl
-  show Id.run (forIn states ([] : List PartMap) fun s r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))
-          : Id (ForInStep (List PartMap)))) = states
-  rw [h2, forIn_append_eq]
-  simp
-
 theorem correct_partitions :
     ∀ (states : List PartMap),
       problem_spec_partitions states (implementation_partitions states) := by
   intro states
-  unfold problem_spec_partitions
-  rw [partitions_eq]
-  exact ⟨rfl, fun i _ => rfl⟩
+  unfold problem_spec_partitions implementation_partitions
+  refine ⟨?_, ?_⟩
+  · simp
+    sorry
+  · sorry
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -39,48 +39,17 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_partitions (states : List PartMap) : List PartMap := Id.run do
-  let mut out : List PartMap := []
-  for s in states do
-    -- emit the state current at this step as its own entry
-    out := out ++ [s]
-  return out
+def implementation_partitions (states : List PartMap) : List PartMap :=
+  states.dropLast
 -- impl-end
 
 -- proof-start
-/-- The append-accumulating `forIn` loop over `states`, generalized over the
-accumulator, is just `init ++ states`. -/
-theorem forIn_append_eq (states : List PartMap) (init : List PartMap) :
-    (Id.run (forIn states init (fun s r =>
-        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap))))))
-    = init ++ states := by
-  induction states generalizing init with
-  | nil => simp [Id.run, List.forIn_nil, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp
-
-theorem partitions_eq (states : List PartMap) :
-    implementation_partitions states = states := by
-  unfold implementation_partitions
-  have h2 : (forIn states ([] : List PartMap) fun s r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))
-          : Id (ForInStep (List PartMap))))
-      = (forIn states ([] : List PartMap) fun s r =>
-        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap)))) := rfl
-  show Id.run (forIn states ([] : List PartMap) fun s r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))
-          : Id (ForInStep (List PartMap)))) = states
-  rw [h2, forIn_append_eq]
-  simp
-
 theorem correct_partitions :
     ∀ (states : List PartMap),
       problem_spec_partitions states (implementation_partitions states) := by
   intro states
-  unfold problem_spec_partitions
-  rw [partitions_eq]
-  exact ⟨rfl, fun i _ => rfl⟩
+  unfold problem_spec_partitions implementation_partitions
+  refine ⟨?_, ?_⟩
+  · sorry
+  · sorry
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -39,48 +39,17 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_partitions (states : List PartMap) : List PartMap := Id.run do
-  let mut out : List PartMap := []
-  for s in states do
-    -- emit the state current at this step as its own entry
-    out := out ++ [s]
-  return out
+def implementation_partitions (states : List PartMap) : List PartMap :=
+  states.reverse
 -- impl-end
 
 -- proof-start
-/-- The append-accumulating `forIn` loop over `states`, generalized over the
-accumulator, is just `init ++ states`. -/
-theorem forIn_append_eq (states : List PartMap) (init : List PartMap) :
-    (Id.run (forIn states init (fun s r =>
-        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap))))))
-    = init ++ states := by
-  induction states generalizing init with
-  | nil => simp [Id.run, List.forIn_nil, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp
-
-theorem partitions_eq (states : List PartMap) :
-    implementation_partitions states = states := by
-  unfold implementation_partitions
-  have h2 : (forIn states ([] : List PartMap) fun s r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))
-          : Id (ForInStep (List PartMap))))
-      = (forIn states ([] : List PartMap) fun s r =>
-        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap)))) := rfl
-  show Id.run (forIn states ([] : List PartMap) fun s r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))
-          : Id (ForInStep (List PartMap)))) = states
-  rw [h2, forIn_append_eq]
-  simp
-
 theorem correct_partitions :
     ∀ (states : List PartMap),
       problem_spec_partitions states (implementation_partitions states) := by
   intro states
-  unfold problem_spec_partitions
-  rw [partitions_eq]
-  exact ⟨rfl, fun i _ => rfl⟩
+  unfold problem_spec_partitions implementation_partitions
+  refine ⟨by simp, ?_⟩
+  intro i hi
+  sorry
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,46 +41,19 @@
 -- impl-start
 def implementation_partitions (states : List PartMap) : List PartMap := Id.run do
   let mut out : List PartMap := []
-  for s in states do
-    -- emit the state current at this step as its own entry
-    out := out ++ [s]
+  for _s in states do
+    -- effect bug: emit the first produced value at every step
+    out := out ++ [states.getD 0 []]
   return out
 -- impl-end
 
 -- proof-start
-/-- The append-accumulating `forIn` loop over `states`, generalized over the
-accumulator, is just `init ++ states`. -/
-theorem forIn_append_eq (states : List PartMap) (init : List PartMap) :
-    (Id.run (forIn states init (fun s r =>
-        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap))))))
-    = init ++ states := by
-  induction states generalizing init with
-  | nil => simp [Id.run, List.forIn_nil, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp
-
-theorem partitions_eq (states : List PartMap) :
-    implementation_partitions states = states := by
-  unfold implementation_partitions
-  have h2 : (forIn states ([] : List PartMap) fun s r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))
-          : Id (ForInStep (List PartMap))))
-      = (forIn states ([] : List PartMap) fun s r =>
-        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap)))) := rfl
-  show Id.run (forIn states ([] : List PartMap) fun s r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))
-          : Id (ForInStep (List PartMap)))) = states
-  rw [h2, forIn_append_eq]
-  simp
-
 theorem correct_partitions :
     ∀ (states : List PartMap),
       problem_spec_partitions states (implementation_partitions states) := by
   intro states
-  unfold problem_spec_partitions
-  rw [partitions_eq]
-  exact ⟨rfl, fun i _ => rfl⟩
+  unfold problem_spec_partitions implementation_partitions
+  refine ⟨?_, ?_⟩
+  · sorry
+  · sorry
 -- proof-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -39,48 +39,15 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_partitions (states : List PartMap) : List PartMap := Id.run do
-  let mut out : List PartMap := []
-  for s in states do
-    -- emit the state current at this step as its own entry
-    out := out ++ [s]
-  return out
+def implementation_partitions (states : List PartMap) : List PartMap :=
+  states
 -- impl-end
 
 -- proof-start
-/-- The append-accumulating `forIn` loop over `states`, generalized over the
-accumulator, is just `init ++ states`. -/
-theorem forIn_append_eq (states : List PartMap) (init : List PartMap) :
-    (Id.run (forIn states init (fun s r =>
-        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap))))))
-    = init ++ states := by
-  induction states generalizing init with
-  | nil => simp [Id.run, List.forIn_nil, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp
-
-theorem partitions_eq (states : List PartMap) :
-    implementation_partitions states = states := by
-  unfold implementation_partitions
-  have h2 : (forIn states ([] : List PartMap) fun s r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))
-          : Id (ForInStep (List PartMap))))
-      = (forIn states ([] : List PartMap) fun s r =>
-        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap)))) := rfl
-  show Id.run (forIn states ([] : List PartMap) fun s r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))
-          : Id (ForInStep (List PartMap)))) = states
-  rw [h2, forIn_append_eq]
-  simp
-
 theorem correct_partitions :
     ∀ (states : List PartMap),
       problem_spec_partitions states (implementation_partitions states) := by
   intro states
-  unfold problem_spec_partitions
-  rw [partitions_eq]
+  unfold problem_spec_partitions implementation_partitions
   exact ⟨rfl, fun i _ => rfl⟩
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,46 +41,18 @@
 -- impl-start
 def implementation_partitions (states : List PartMap) : List PartMap := Id.run do
   let mut out : List PartMap := []
-  for s in states do
-    -- emit the state current at this step as its own entry
-    out := out ++ [s]
+  for _s in states do
+    out := out ++ [([] : PartMap)]
   return out
 -- impl-end
 
 -- proof-start
-/-- The append-accumulating `forIn` loop over `states`, generalized over the
-accumulator, is just `init ++ states`. -/
-theorem forIn_append_eq (states : List PartMap) (init : List PartMap) :
-    (Id.run (forIn states init (fun s r =>
-        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap))))))
-    = init ++ states := by
-  induction states generalizing init with
-  | nil => simp [Id.run, List.forIn_nil, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp
-
-theorem partitions_eq (states : List PartMap) :
-    implementation_partitions states = states := by
-  unfold implementation_partitions
-  have h2 : (forIn states ([] : List PartMap) fun s r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))
-          : Id (ForInStep (List PartMap))))
-      = (forIn states ([] : List PartMap) fun s r =>
-        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap)))) := rfl
-  show Id.run (forIn states ([] : List PartMap) fun s r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))
-          : Id (ForInStep (List PartMap)))) = states
-  rw [h2, forIn_append_eq]
-  simp
-
 theorem correct_partitions :
     ∀ (states : List PartMap),
       problem_spec_partitions states (implementation_partitions states) := by
   intro states
-  unfold problem_spec_partitions
-  rw [partitions_eq]
-  exact ⟨rfl, fun i _ => rfl⟩
+  unfold problem_spec_partitions implementation_partitions
+  refine ⟨?_, ?_⟩
+  · sorry
+  · sorry
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -39,48 +39,15 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_partitions (states : List PartMap) : List PartMap := Id.run do
-  let mut out : List PartMap := []
-  for s in states do
-    -- emit the state current at this step as its own entry
-    out := out ++ [s]
-  return out
+def implementation_partitions (states : List PartMap) : List PartMap :=
+  states.map id
 -- impl-end
 
 -- proof-start
-/-- The append-accumulating `forIn` loop over `states`, generalized over the
-accumulator, is just `init ++ states`. -/
-theorem forIn_append_eq (states : List PartMap) (init : List PartMap) :
-    (Id.run (forIn states init (fun s r =>
-        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap))))))
-    = init ++ states := by
-  induction states generalizing init with
-  | nil => simp [Id.run, List.forIn_nil, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp
-
-theorem partitions_eq (states : List PartMap) :
-    implementation_partitions states = states := by
-  unfold implementation_partitions
-  have h2 : (forIn states ([] : List PartMap) fun s r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))
-          : Id (ForInStep (List PartMap))))
-      = (forIn states ([] : List PartMap) fun s r =>
-        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap)))) := rfl
-  show Id.run (forIn states ([] : List PartMap) fun s r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))
-          : Id (ForInStep (List PartMap)))) = states
-  rw [h2, forIn_append_eq]
-  simp
-
 theorem correct_partitions :
     ∀ (states : List PartMap),
       problem_spec_partitions states (implementation_partitions states) := by
   intro states
-  unfold problem_spec_partitions
-  rw [partitions_eq]
-  exact ⟨rfl, fun i _ => rfl⟩
+  unfold problem_spec_partitions implementation_partitions
+  simp
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -39,48 +39,17 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_partitions (states : List PartMap) : List PartMap := Id.run do
-  let mut out : List PartMap := []
-  for s in states do
-    -- emit the state current at this step as its own entry
-    out := out ++ [s]
-  return out
+def implementation_partitions (states : List PartMap) : List PartMap :=
+  states ++ [([] : PartMap)]
 -- impl-end
 
 -- proof-start
-/-- The append-accumulating `forIn` loop over `states`, generalized over the
-accumulator, is just `init ++ states`. -/
-theorem forIn_append_eq (states : List PartMap) (init : List PartMap) :
-    (Id.run (forIn states init (fun s r =>
-        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap))))))
-    = init ++ states := by
-  induction states generalizing init with
-  | nil => simp [Id.run, List.forIn_nil, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp
-
-theorem partitions_eq (states : List PartMap) :
-    implementation_partitions states = states := by
-  unfold implementation_partitions
-  have h2 : (forIn states ([] : List PartMap) fun s r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))
-          : Id (ForInStep (List PartMap))))
-      = (forIn states ([] : List PartMap) fun s r =>
-        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap)))) := rfl
-  show Id.run (forIn states ([] : List PartMap) fun s r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))
-          : Id (ForInStep (List PartMap)))) = states
-  rw [h2, forIn_append_eq]
-  simp
-
 theorem correct_partitions :
     ∀ (states : List PartMap),
       problem_spec_partitions states (implementation_partitions states) := by
   intro states
-  unfold problem_spec_partitions
-  rw [partitions_eq]
-  exact ⟨rfl, fun i _ => rfl⟩
+  unfold problem_spec_partitions implementation_partitions
+  refine ⟨?_, ?_⟩
+  · sorry
+  · sorry
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
A generator computes a sequence of intermediate states (here, integer
partitions, each represented as a finite map from a part-value to its
multiplicity) by repeatedly advancing a working state. A consumer that drains
the generator into a concrete list expects the materialized list to contain, at
each position, the state that was current when that position was produced — in
the same order, and one entry per produced state.

A partition is modeled as `List (Nat × Nat)`: an association list pairing a
part-value with the number of copies of it in that partition (e.g. the partition
`{2: 3}` ↦ `[(2, 3)]`). The generated sequence of partitions is the input
carrier `states`; materialization relates the produced list to it position-wise.
-/

-- axioms-start
-- No unchanged callee is consumed: the generated state sequence is taken as the
-- input carrier, and materialization is modeled deeply (position-wise), so there
-- is nothing to axiomatize.
-- axioms-end

-- pure-start
/-- A single produced state: an integer partition as a multiplicity map
(part-value ↦ count). -/
abbrev PartMap := List (Nat × Nat)
-- pure-end

-- post-conditions-start
/-- Materializing the produced sequence `states` into `result`:
* `result` has exactly one entry per produced state (count preserved); and
* the entry at each position is the state produced at that position, in order.
Together these pin `result` to be `states` element-for-element — every produced
state appears, distinctly, at its own position. -/
def problem_spec_partitions (states : List PartMap) (result : List PartMap) : Prop :=
  result.length = states.length ∧
  (∀ i, i < states.length → result.getD i [] = states.getD i [])
-- post-conditions-end

-- impl-start
def implementation_partitions (states : List PartMap) : List PartMap := Id.run do
  let mut out : List PartMap := []
  for s in states do
    -- emit the state current at this step as its own entry
    out := out ++ [s]
  return out
-- impl-end

-- proof-start
/-- The append-accumulating `forIn` loop over `states`, generalized over the
accumulator, is just `init ++ states`. -/
theorem forIn_append_eq (states : List PartMap) (init : List PartMap) :
    (Id.run (forIn states init (fun s r =>
        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap))))))
    = init ++ states := by
  induction states generalizing init with
  | nil => simp [Id.run, List.forIn_nil, pure]
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp

theorem partitions_eq (states : List PartMap) :
    implementation_partitions states = states := by
  unfold implementation_partitions
  have h2 : (forIn states ([] : List PartMap) fun s r =>
        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))
          : Id (ForInStep (List PartMap))))
      = (forIn states ([] : List PartMap) fun s r =>
        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap)))) := rfl
  show Id.run (forIn states ([] : List PartMap) fun s r =>
        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))
          : Id (ForInStep (List PartMap)))) = states
  rw [h2, forIn_append_eq]
  simp

theorem correct_partitions :
    ∀ (states : List PartMap),
      problem_spec_partitions states (implementation_partitions states) := by
  intro states
  unfold problem_spec_partitions
  rw [partitions_eq]
  exact ⟨rfl, fun i _ => rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

### PROTOCOL EXECUTED (project root; venv swebench-lean; scratch).

SPEC SHAPE: problem_spec_partitions states result := result.length = states.length AND (forall i, i < states.length -> result.getD i [] = states.getD i []). Equal length + pointwise-over-all-valid-indices = complete (identity) spec: result = states. A tight spec => genuinely-wrong impls are unprovable; only gold-equivalent (identity) impls close.

SAME_SPEC: all 8 attacks confirmed same_spec=True via swebench_unified.markers.same_spec (lean backend), spec_signature byte-identical to bundle (axioms/pure/pre/post untouched; only impl+proof region edited).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>, run in 2 parallel batches of 4):
- atk_1 (PREPATCH bug: out ++ [states.getLastD []] every step) EXIT=1 (unprovable; my proof draft hit 'No goals'). PREPATCH REPRODUCED & DISPROVED: disproof_prepatch.lean proves ¬ problem_spec_partitions [[(2,3)],[(1,6)]] (impl_prepatch ...) -> EXIT=0. Spec provably REJECTS the real aliasing bug on the non-constant F2P input (G-DIFF confirmed).
- atk_2 (partial-domain: states.dropLast, length low) EXIT=3 (could not close, sorry).
- atk_3 (boundary/ordering: states.reverse) EXIT=3.
- atk_4 (control-flow-effect: getD 0 [] every step -> first value everywhere) EXIT=3.
- atk_5 (ungrounded-oracle echo: return states) EXIT=0 VERIFIES. `#print axioms correct_partitions` => 'does not depend on any axioms' (clean, no sorryAx).
- atk_6 (ungrounded-oracle echo: [] every step, correct length wrong values) EXIT=3.
- atk_7 (echo variant: states.map id) EXIT=0 VERIFIES. `#print axioms` => [propext, Quot.sound] (standard trusted set, clean, no sorryAx).
- atk_8 (boundary: states ++ [[]], length high) EXIT=3.

POSITIVE CONTROL: pos_control.lean (= gold Solution.lean) EXIT=0.

MATERIALIZED + RESOLVE-RAN (protocol step 2, NOT speculation): atk_5 and atk_7 both verify with clean axioms. Both are extensionally the identity materialization = exactly the gold snapshot-on-yield behavior, so their faithful refined patch is the gold patch (yield ms -> yield ms.copy() at both size=False/size=True sites). Executed run_resolve('sympy__sympy-20154', gold_patch) via swebench_unified.harness (docker): RESOLVED=True, FLAKY=False, note='resolved', attempts=1; FAIL_TO_PASS test_partitions/test_uniq success, all PASS_TO_PASS success. => The faithful patch of every verifying same-spec impl RESOLVES. verify does NOT contradict correct here.

REFINEMENT AUDIT (refinement.md): all legs R or I, NO A-legs, no kind-3.
- Op#1 empty accumulator = I. Op#2 for-loop over produced sequence = R (produced-value sequence <-> states carrier; unchanged `while keys!=[1]` advance abstracted into states). Op#3 out ++ [s] <-> yield ms.copy() = R (dict.copy() of dict[int,int] <-> taking pure value s : List(Nat x Nat), value semantics = deep snapshot). Op#4 return = I.
- No A-consumed / A-reference legs, and this is HONEST: Solution.lean has zero axiom/opaque decls (axiom_check.py is a valid skip stub). The generation algorithm is NOT axiomatized as an oracle; its OUTPUT is taken as the universally-quantified input carrier `states` — the legitimate plan-§3 'changed op modeled deeply, callee output taken as input' pattern, not an ungrounded oracle. G-CONF (conformance_check.py, seed 20154, >=1e5 cases) mechanically grounds the identity-materialization shadow against the REAL patched partitions() callee, so the R model is not asserted but differential-tested. mapping.md symbol binding (iterables.py:1789,1831 yield sites) matches the patch.diff hunks. A-leg correspondence: n/a (none).

CONCLUSION: spec is a complete/tight specification; it rejects the real bug (G-DIFF), rejects all 6 distinct wrong-impl classes attempted, and admits only gold-equivalent impls whose faithful patch RESOLVES (executed). No verify=>correct gap. Refinement is faithful with no unsound A-legs. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_partitions is a COMPLETE specification: result.length = states.length AND (forall i < states.length, result.getD i [] = states.getD i []) together pin result = states extensionally. Every same-spec wrong impl I tried (partial-domain dropLast, boundary reverse, control-flow-effect getD 0, ungrounded-oracle echoes [] and getLastD, extra-element append) FAILS to verify. Only extensionally-identity impls verify (atk_5 `return states`, atk_7 `states.map id`), which are precisely the gold snapshot-on-yield behavior; their faithful refined patch IS the gold patch, which RESOLVES. No verifying impl has a non-resolving faithful patch, so verify does NOT imply weakness here.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
A generator computes a sequence of intermediate states (here, integer
partitions, each represented as a finite map from a part-value to its
multiplicity) by repeatedly advancing a working state. A consumer that drains
the generator into a concrete list expects the materialized list to contain, at
each position, the state that was current when that position was produced — in
the same order, and one entry per produced state.

A partition is modeled as `List (Nat × Nat)`: an association list pairing a
part-value with the number of copies of it in that partition (e.g. the partition
`{2: 3}` ↦ `[(2, 3)]`). The generated sequence of partitions is the input
carrier `states`; materialization relates the produced list to it position-wise.
-/

-- axioms-start
-- No unchanged callee is consumed: the generated state sequence is taken as the
-- input carrier, and materialization is modeled deeply (position-wise), so there
-- is nothing to axiomatize.
-- axioms-end

-- pure-start
/-- A single produced state: an integer partition as a multiplicity map
(part-value ↦ count). -/
abbrev PartMap := List (Nat × Nat)
-- pure-end

-- post-conditions-start
/-- Materializing the produced sequence `states` into `result`:
* `result` has exactly one entry per produced state (count preserved); and
* the entry at each position is the state produced at that position, in order.
Together these pin `result` to be `states` element-for-element — every produced
state appears, distinctly, at its own position. -/
def problem_spec_partitions (states : List PartMap) (result : List PartMap) : Prop :=
  result.length = states.length ∧
  (∀ i, i < states.length → result.getD i [] = states.getD i [])
-- post-conditions-end

-- impl-start
def implementation_partitions (states : List PartMap) : List PartMap := Id.run do
  let mut out : List PartMap := []
  for s in states do
    -- emit the state current at this step as its own entry
    out := out ++ [s]
  return out
-- impl-end

-- proof-start
/-- The append-accumulating `forIn` loop over `states`, generalized over the
accumulator, is just `init ++ states`. -/
theorem forIn_append_eq (states : List PartMap) (init : List PartMap) :
    (Id.run (forIn states init (fun s r =>
        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap))))))
    = init ++ states := by
  induction states generalizing init with
  | nil => simp [Id.run, List.forIn_nil, pure]
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp

theorem partitions_eq (states : List PartMap) :
    implementation_partitions states = states := by
  unfold implementation_partitions
  have h2 : (forIn states ([] : List PartMap) fun s r =>
        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))
          : Id (ForInStep (List PartMap))))
      = (forIn states ([] : List PartMap) fun s r =>
        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap)))) := rfl
  show Id.run (forIn states ([] : List PartMap) fun s r =>
        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))
          : Id (ForInStep (List PartMap)))) = states
  rw [h2, forIn_append_eq]
  simp

theorem correct_partitions :
    ∀ (states : List PartMap),
      problem_spec_partitions states (implementation_partitions states) := by
  intro states
  unfold problem_spec_partitions
  rw [partitions_eq]
  exact ⟨rfl, fun i _ => rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

### PROTOCOL EXECUTED (project root; venv swebench-lean; scratch).

SPEC SHAPE: problem_spec_partitions states result := result.length = states.length AND (forall i, i < states.length -> result.getD i [] = states.getD i []). Equal length + pointwise-over-all-valid-indices = complete (identity) spec: result = states. A tight spec => genuinely-wrong impls are unprovable; only gold-equivalent (identity) impls close.

SAME_SPEC: all 8 attacks confirmed same_spec=True via swebench_unified.markers.same_spec (lean backend), spec_signature byte-identical to bundle (axioms/pure/pre/post untouched; only impl+proof region edited).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>, run in 2 parallel batches of 4):
- atk_1 (PREPATCH bug: out ++ [states.getLastD []] every step) EXIT=1 (unprovable; my proof draft hit 'No goals'). PREPATCH REPRODUCED & DISPROVED: disproof_prepatch.lean proves ¬ problem_spec_partitions [[(2,3)],[(1,6)]] (impl_prepatch ...) -> EXIT=0. Spec provably REJECTS the real aliasing bug on the non-constant F2P input (G-DIFF confirmed).
- atk_2 (partial-domain: states.dropLast, length low) EXIT=3 (could not close, sorry).
- atk_3 (boundary/ordering: states.reverse) EXIT=3.
- atk_4 (control-flow-effect: getD 0 [] every step -> first value everywhere) EXIT=3.
- atk_5 (ungrounded-oracle echo: return states) EXIT=0 VERIFIES. `#print axioms correct_partitions` => 'does not depend on any axioms' (clean, no sorryAx).
- atk_6 (ungrounded-oracle echo: [] every step, correct length wrong values) EXIT=3.
- atk_7 (echo variant: states.map id) EXIT=0 VERIFIES. `#print axioms` => [propext, Quot.sound] (standard trusted set, clean, no sorryAx).
- atk_8 (boundary: states ++ [[]], length high) EXIT=3.

POSITIVE CONTROL: pos_control.lean (= gold Solution.lean) EXIT=0.

MATERIALIZED + RESOLVE-RAN (protocol step 2, NOT speculation): atk_5 and atk_7 both verify with clean axioms. Both are extensionally the identity materialization = exactly the gold snapshot-on-yield behavior, so their faithful refined patch is the gold patch (yield ms -> yield ms.copy() at both size=False/size=True sites). Executed run_resolve('sympy__sympy-20154', gold_patch) via swebench_unified.harness (docker): RESOLVED=True, FLAKY=False, note='resolved', attempts=1; FAIL_TO_PASS test_partitions/test_uniq success, all PASS_TO_PASS success. => The faithful patch of every verifying same-spec impl RESOLVES. verify does NOT contradict correct here.

REFINEMENT AUDIT (refinement.md): all legs R or I, NO A-legs, no kind-3.
- Op#1 empty accumulator = I. Op#2 for-loop over produced sequence = R (produced-value sequence <-> states carrier; unchanged `while keys!=[1]` advance abstracted into states). Op#3 out ++ [s] <-> yield ms.copy() = R (dict.copy() of dict[int,int] <-> taking pure value s : List(Nat x Nat), value semantics = deep snapshot). Op#4 return = I.
- No A-consumed / A-reference legs, and this is HONEST: Solution.lean has zero axiom/opaque decls (axiom_check.py is a valid skip stub). The generation algorithm is NOT axiomatized as an oracle; its OUTPUT is taken as the universally-quantified input carrier `states` — the legitimate plan-§3 'changed op modeled deeply, callee output taken as input' pattern, not an ungrounded oracle. G-CONF (conformance_check.py, seed 20154, >=1e5 cases) mechanically grounds the identity-materialization shadow against the REAL patched partitions() callee, so the R model is not asserted but differential-tested. mapping.md symbol binding (iterables.py:1789,1831 yield sites) matches the patch.diff hunks. A-leg correspondence: n/a (none).

CONCLUSION: spec is a complete/tight specification; it rejects the real bug (G-DIFF), rejects all 6 distinct wrong-impl classes attempted, and admits only gold-equivalent impls whose faithful patch RESOLVES (executed). No verify=>correct gap. Refinement is faithful with no unsound A-legs. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Solution.lean compiles via lean_verify.sh (exit 0) and `#print axioms correct_partitions` shows only [propext, Quot.sound] — no sorryAx, proof is genuine. Spec region (post-conditions) byte-identical between Solution.lean and Solution_prepatch.lean (only the impl op #3 differs: `out ++ [s]` vs `out ++ [states.getLastD []]`), so the discriminating spec is shared. Faithfulness: the modeled function `implementation_partitions` is the identity materialization of the produced-value sequence `states`; the real gold-patched callee `list(partitions(n,m,k))` (with `yield ms.copy()`) materializes exactly one independent snapshot per yield in order = `states`. Differential test in the base worktree, simulating the patched copy-on-yield behavior against the identity model over 20,000 fuzzed (n,m,k) cases with seed 20154 (1<=n<=40, m/k in {None}+[1..n]): 0 mismatches. Bundle's own conformance_check.py / G-CONF passed 0/100000. The abstraction of the unchanged generator's output as input carrier `states` is legitimate (patch leaves generation byte-identical; only the yield copies). Modeling only size=False is sound (same defect/same object on the size=True branch). Spec is universally quantified over arbitrary List PartMap — over-general on inputs but the modeled function agrees with the real callee on all inputs (it is identity), so it is not too strong in a drifting way. No input found where the modeled function disagrees with real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: `yield ms` -> `yield ms.copy()` (and the size=True site) in sympy/utilities/iterables.py, so materialized partitions are distinct snapshots rather than N aliases of one mutated dict. The PUBLIC problem_statement already states both bug and fix explicitly ('reuses the output dictionaries', 'list(partitions()) will give an apparently wrong result', and the remedy 'copy the dictionary before yielding it'). Reviewed the actual spec view (imports + doc block + axioms + pure + post-conditions; impl/proof elided by projection):
- No diff markers, no 'iterables.py' file path, no dotted module path.
- No spec-view identifier embeds a patched repo symbol. The only patch-changed distinctive symbol is `partitions`, which appears verbatim in problem_statement (exempt); spec idents are PartMap/states/result/problem_spec_partitions/implementation_partitions and reveal nothing about the edit.
- Comments describe correct BEHAVIOR ('materialized list contains, at each position, the state current when produced; one entry per produced state') = exactly what the problem_statement demands; no mention of copy()/yield/dict-aliasing/mutation mechanism.
- No narration tokens (bug/fix/patch/wrong/etc.).
Mechanical leakage.screen() over the computed spec_view PASSES (0 hard failures). same_spec(post, prepatch)=True: spec region is byte-identical, so all discrimination lives in impl/proof, not a leaked spec. spec_provenance='cold'. Spec leaks nothing about the gold edit beyond the public problem_statement.

- No diff markers, no 'iterables.py' file path, no dotted module path.
- No spec-view identifier embeds a patched repo symbol. The only patch-changed distinctive symbol is `partitions`, which appears verbatim in problem_statement (exempt); spec idents are PartMap/states/result/problem_spec_partitions/implementation_partitions and reveal nothing about the edit.
- Comments describe correct BEHAVIOR ('materialized list contains, at each position, the state current when produced; one entry per produced state') = exactly what the problem_statement demands; no mention of copy()/yield/dict-aliasing/mutation mechanism.
- No narration tokens (bug/fix/patch/wrong/etc.).
Mechanical leakage.screen() over the computed spec_view PASSES (0 hard failures). same_spec(post, prepatch)=True: spec region is byte-identical, so all discrimination lives in impl/proof, not a leaked spec. spec_provenance='cold'. Spec leaks nothing about the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
