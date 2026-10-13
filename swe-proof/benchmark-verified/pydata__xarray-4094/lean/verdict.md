# P2 adversarial audit — pydata__xarray-4094

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,7 +63,7 @@
     List (κ × ν) := Id.run do
   let mut dataDict : List (κ × ν) := []
   for k in vars do
-    dataDict := dataDict ++ [(k, extractSlice true k)]
+    dataDict := dataDict ++ [(k, extractSlice false k)]
   return dataDict
 -- impl-end
 
@@ -89,10 +89,10 @@
   rw [show (Id.run do
       let r ← forIn vars [] fun k r => do
             pure PUnit.unit
-            pure (ForInStep.yield (r ++ [(k, extractSlice true k)]))
+            pure (ForInStep.yield (r ++ [(k, extractSlice false k)]))
       pure r)
     = Id.run (forIn vars [] (fun k r =>
-      (do pure PUnit.unit; pure (ForInStep.yield (r ++ [(k, extractSlice true k)]))))) from rfl]
+      (do pure PUnit.unit; pure (ForInStep.yield (r ++ [(k, extractSlice false k)]))))) from rfl]
   rw [toUnstackedDataset_forIn_helper]
   simp
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,36 +63,15 @@
     List (κ × ν) := Id.run do
   let mut dataDict : List (κ × ν) := []
   for k in vars do
-    dataDict := dataDict ++ [(k, extractSlice true k)]
+    dataDict := (k, extractSlice true k) :: dataDict
   return dataDict
 -- impl-end
 
 -- proof-start
-theorem toUnstackedDataset_forIn_helper {κ ν : Type}
-    (f : κ → ν) (vars : List κ) (init : List (κ × ν)) :
-    (Id.run (forIn vars init (fun k r =>
-      (do pure PUnit.unit; pure (ForInStep.yield (r ++ [(k, f k)]))))))
-      = init ++ vars.map (fun k => (k, f k)) := by
-  induction vars generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_toUnstackedDataset {κ ν : Type}
     (extractSlice : Bool → κ → ν) (vars : List κ) :
     problem_spec_toUnstackedDataset extractSlice vars
       (implementation_toUnstackedDataset extractSlice vars) := by
   unfold problem_spec_toUnstackedDataset implementation_toUnstackedDataset
-  rw [show (Id.run do
-      let r ← forIn vars [] fun k r => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [(k, extractSlice true k)]))
-      pure r)
-    = Id.run (forIn vars [] (fun k r =>
-      (do pure PUnit.unit; pure (ForInStep.yield (r ++ [(k, extractSlice true k)]))))) from rfl]
-  rw [toUnstackedDataset_forIn_helper]
-  simp
+  simp [Id.run]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,39 +60,14 @@
 -- impl-start
 def implementation_toUnstackedDataset {κ ν : Type}
     (extractSlice : Bool → κ → ν) (vars : List κ) :
-    List (κ × ν) := Id.run do
-  let mut dataDict : List (κ × ν) := []
-  for k in vars do
-    dataDict := dataDict ++ [(k, extractSlice true k)]
-  return dataDict
+    List (κ × ν) := []
 -- impl-end
 
 -- proof-start
-theorem toUnstackedDataset_forIn_helper {κ ν : Type}
-    (f : κ → ν) (vars : List κ) (init : List (κ × ν)) :
-    (Id.run (forIn vars init (fun k r =>
-      (do pure PUnit.unit; pure (ForInStep.yield (r ++ [(k, f k)]))))))
-      = init ++ vars.map (fun k => (k, f k)) := by
-  induction vars generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_toUnstackedDataset {κ ν : Type}
     (extractSlice : Bool → κ → ν) (vars : List κ) :
     problem_spec_toUnstackedDataset extractSlice vars
       (implementation_toUnstackedDataset extractSlice vars) := by
   unfold problem_spec_toUnstackedDataset implementation_toUnstackedDataset
-  rw [show (Id.run do
-      let r ← forIn vars [] fun k r => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [(k, extractSlice true k)]))
-      pure r)
-    = Id.run (forIn vars [] (fun k r =>
-      (do pure PUnit.unit; pure (ForInStep.yield (r ++ [(k, extractSlice true k)]))))) from rfl]
-  rw [toUnstackedDataset_forIn_helper]
   simp
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,39 +60,19 @@
 -- impl-start
 def implementation_toUnstackedDataset {κ ν : Type}
     (extractSlice : Bool → κ → ν) (vars : List κ) :
-    List (κ × ν) := Id.run do
-  let mut dataDict : List (κ × ν) := []
-  for k in vars do
-    dataDict := dataDict ++ [(k, extractSlice true k)]
-  return dataDict
+    List (κ × ν) :=
+  match vars with
+  | [] => []
+  | k :: ks => (k, extractSlice false k) :: ks.map (fun k => (k, extractSlice true k))
 -- impl-end
 
 -- proof-start
-theorem toUnstackedDataset_forIn_helper {κ ν : Type}
-    (f : κ → ν) (vars : List κ) (init : List (κ × ν)) :
-    (Id.run (forIn vars init (fun k r =>
-      (do pure PUnit.unit; pure (ForInStep.yield (r ++ [(k, f k)]))))))
-      = init ++ vars.map (fun k => (k, f k)) := by
-  induction vars generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_toUnstackedDataset {κ ν : Type}
     (extractSlice : Bool → κ → ν) (vars : List κ) :
     problem_spec_toUnstackedDataset extractSlice vars
       (implementation_toUnstackedDataset extractSlice vars) := by
   unfold problem_spec_toUnstackedDataset implementation_toUnstackedDataset
-  rw [show (Id.run do
-      let r ← forIn vars [] fun k r => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [(k, extractSlice true k)]))
-      pure r)
-    = Id.run (forIn vars [] (fun k r =>
-      (do pure PUnit.unit; pure (ForInStep.yield (r ++ [(k, extractSlice true k)]))))) from rfl]
-  rw [toUnstackedDataset_forIn_helper]
-  simp
+  cases vars with
+  | nil => simp
+  | cons k ks => simp
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,39 +60,15 @@
 -- impl-start
 def implementation_toUnstackedDataset {κ ν : Type}
     (extractSlice : Bool → κ → ν) (vars : List κ) :
-    List (κ × ν) := Id.run do
-  let mut dataDict : List (κ × ν) := []
-  for k in vars do
-    dataDict := dataDict ++ [(k, extractSlice true k)]
-  return dataDict
+    List (κ × ν) :=
+  vars.map (fun k => (k, extractSlice true k)) ++ vars.map (fun k => (k, extractSlice true k))
 -- impl-end
 
 -- proof-start
-theorem toUnstackedDataset_forIn_helper {κ ν : Type}
-    (f : κ → ν) (vars : List κ) (init : List (κ × ν)) :
-    (Id.run (forIn vars init (fun k r =>
-      (do pure PUnit.unit; pure (ForInStep.yield (r ++ [(k, f k)]))))))
-      = init ++ vars.map (fun k => (k, f k)) := by
-  induction vars generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_toUnstackedDataset {κ ν : Type}
     (extractSlice : Bool → κ → ν) (vars : List κ) :
     problem_spec_toUnstackedDataset extractSlice vars
       (implementation_toUnstackedDataset extractSlice vars) := by
   unfold problem_spec_toUnstackedDataset implementation_toUnstackedDataset
-  rw [show (Id.run do
-      let r ← forIn vars [] fun k r => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [(k, extractSlice true k)]))
-      pure r)
-    = Id.run (forIn vars [] (fun k r =>
-      (do pure PUnit.unit; pure (ForInStep.yield (r ++ [(k, extractSlice true k)]))))) from rfl]
-  rw [toUnstackedDataset_forIn_helper]
   simp
 -- proof-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -60,39 +60,14 @@
 -- impl-start
 def implementation_toUnstackedDataset {κ ν : Type}
     (extractSlice : Bool → κ → ν) (vars : List κ) :
-    List (κ × ν) := Id.run do
-  let mut dataDict : List (κ × ν) := []
-  for k in vars do
-    dataDict := dataDict ++ [(k, extractSlice true k)]
-  return dataDict
+    List (κ × ν) :=
+  vars.map (fun k => (k, extractSlice true k))
 -- impl-end
 
 -- proof-start
-theorem toUnstackedDataset_forIn_helper {κ ν : Type}
-    (f : κ → ν) (vars : List κ) (init : List (κ × ν)) :
-    (Id.run (forIn vars init (fun k r =>
-      (do pure PUnit.unit; pure (ForInStep.yield (r ++ [(k, f k)]))))))
-      = init ++ vars.map (fun k => (k, f k)) := by
-  induction vars generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_toUnstackedDataset {κ ν : Type}
     (extractSlice : Bool → κ → ν) (vars : List κ) :
     problem_spec_toUnstackedDataset extractSlice vars
       (implementation_toUnstackedDataset extractSlice vars) := by
-  unfold problem_spec_toUnstackedDataset implementation_toUnstackedDataset
-  rw [show (Id.run do
-      let r ← forIn vars [] fun k r => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [(k, extractSlice true k)]))
-      pure r)
-    = Id.run (forIn vars [] (fun k r =>
-      (do pure PUnit.unit; pure (ForInStep.yield (r ++ [(k, extractSlice true k)]))))) from rfl]
-  rw [toUnstackedDataset_forIn_helper]
-  simp
+  rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,39 +60,17 @@
 -- impl-start
 def implementation_toUnstackedDataset {κ ν : Type}
     (extractSlice : Bool → κ → ν) (vars : List κ) :
-    List (κ × ν) := Id.run do
-  let mut dataDict : List (κ × ν) := []
-  for k in vars do
-    dataDict := dataDict ++ [(k, extractSlice true k)]
-  return dataDict
+    List (κ × ν) :=
+  vars.map (fun k => (k, extractSlice (vars.length == 0) k))
 -- impl-end
 
 -- proof-start
-theorem toUnstackedDataset_forIn_helper {κ ν : Type}
-    (f : κ → ν) (vars : List κ) (init : List (κ × ν)) :
-    (Id.run (forIn vars init (fun k r =>
-      (do pure PUnit.unit; pure (ForInStep.yield (r ++ [(k, f k)]))))))
-      = init ++ vars.map (fun k => (k, f k)) := by
-  induction vars generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_toUnstackedDataset {κ ν : Type}
     (extractSlice : Bool → κ → ν) (vars : List κ) :
     problem_spec_toUnstackedDataset extractSlice vars
       (implementation_toUnstackedDataset extractSlice vars) := by
   unfold problem_spec_toUnstackedDataset implementation_toUnstackedDataset
-  rw [show (Id.run do
-      let r ← forIn vars [] fun k r => do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [(k, extractSlice true k)]))
-      pure r)
-    = Id.run (forIn vars [] (fun k r =>
-      (do pure PUnit.unit; pure (ForInStep.yield (r ++ [(k, extractSlice true k)]))))) from rfl]
-  rw [toUnstackedDataset_forIn_helper]
-  simp
+  cases vars with
+  | nil => simp
+  | cons k ks => simp
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

/-!
Expanding a combined array into a labelled collection of its constituent
variables.

The data carries a list of variable labels along one axis. The operation walks
that list of labels and, for each label, extracts that variable's slice of the
data, assembling the slices into a labelled collection — one entry per label, in
the order the labels are listed.

Each slice is extracted in the label-removing mode: when the slice for a label is
selected, the selecting label is dropped from the slice rather than retained on
it as an attached scalar marker. The required behavior is that every slice is
extracted in this label-removing mode, and that the result lists exactly the
labels, in order, each paired with its extracted slice.

The extraction of a single slice (selecting it and reducing away the now-singleton
axes) is itself a self-contained step; what this bundle pins is the mode in which
that step is invoked and the structure of the assembled collection.
-/

-- axioms-start
-- No unchanged outside callee contract is consumed as a logical property. The
-- per-label slice extraction (selecting the slice for a label and reducing away
-- the now-singleton axes) is left UNIVERSALLY QUANTIFIED as a parameter
-- `extractSlice : Bool → κ → ν`: the first argument is the extraction mode (the
-- label-removing mode when `true`, the label-retaining mode when `false`) and
-- the second is the variable label. The specification holds for EVERY such
-- extraction step, so it pins only that the label-removing mode reaches the
-- extraction for each label, which is exactly the behavior under specification.
-- Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- No additional pure helpers are needed: the labelled collection is expressed
-- directly as a map over the list of labels.
-- pure-end

-- post-conditions-start
/-- The assembled collection of extracted variables.

`κ` is the type of a variable label and `ν` the type of an extracted slice.
`extractSlice mode k` is the extraction of the slice for label `k`, performed in
label-removing mode when `mode = true`. The result is the list of `(label, slice)`
entries.

The result is fully pinned for every input (directive 5 frame): it is exactly the
list of labels, in their given order, each paired with the slice extracted in the
label-removing mode (`extractSlice true k`). No entry, order, or extraction mode
is left free — in particular each slice must be the one produced with the label
removed, never the label-retaining extraction. -/
def problem_spec_toUnstackedDataset {κ ν : Type}
    (extractSlice : Bool → κ → ν) (vars : List κ)
    (result : List (κ × ν)) : Prop :=
  result = vars.map (fun k => (k, extractSlice true k))
-- post-conditions-end

-- impl-start
def implementation_toUnstackedDataset {κ ν : Type}
    (extractSlice : Bool → κ → ν) (vars : List κ) :
    List (κ × ν) := Id.run do
  let mut dataDict : List (κ × ν) := []
  for k in vars do
    dataDict := dataDict ++ [(k, extractSlice true k)]
  return dataDict
-- impl-end

-- proof-start
theorem toUnstackedDataset_forIn_helper {κ ν : Type}
    (f : κ → ν) (vars : List κ) (init : List (κ × ν)) :
    (Id.run (forIn vars init (fun k r =>
      (do pure PUnit.unit; pure (ForInStep.yield (r ++ [(k, f k)]))))))
      = init ++ vars.map (fun k => (k, f k)) := by
  induction vars generalizing init with
  | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp [List.append_assoc]

theorem correct_toUnstackedDataset {κ ν : Type}
    (extractSlice : Bool → κ → ν) (vars : List κ) :
    problem_spec_toUnstackedDataset extractSlice vars
      (implementation_toUnstackedDataset extractSlice vars) := by
  unfold problem_spec_toUnstackedDataset implementation_toUnstackedDataset
  rw [show (Id.run do
      let r ← forIn vars [] fun k r => do
            pure PUnit.unit
            pure (ForInStep.yield (r ++ [(k, extractSlice true k)]))
      pure r)
    = Id.run (forIn vars [] (fun k r =>
      (do pure PUnit.unit; pure (ForInStep.yield (r ++ [(k, extractSlice true k)]))))) from rfl]
  rw [toUnstackedDataset_forIn_helper]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins output: problem_spec := result = vars.map (fun k => (k, extractSlice true k)) over universally-quantified {kappa nu : Type} and abstract extractSlice : Bool->kappa->nu. Both impl AND proof regions are elided from the lean spec view (_lean_spec_view), so attacks freely rewrote both; any closing proof forces the impl extensionally equal to that exact map.

SAME-SPEC: all 7 attacks + positive control verified same_spec=True vs Solution.lean (swebench_unified.markers.same_spec, lean backend).

Verify command per attack: `bash scripts/lean_verify.sh <path>` (run concurrently, <=4 at a time, two batches).

### RESULTS (exit 0 = verifies/no-sorry, 1 = error):
- pos_gold.lean (gold verbatim): EXIT 0. `#print axioms correct_toUnstackedDataset` => [propext, Quot.sound] (standard trusted axioms, clean).
- atk_1 (PREPATCH BUG: extractSlice false k, label-retaining): EXIT 1. Residual goal `forall a in vars, extractSlice false a = extractSlice true a` (unprovable for abstract extractSlice). Prepatch bug reproduced.
- atk_2 (control-flow-effect: prepend `::` => reversed order): EXIT 1. Goal `map(...).reverse = map(...)`.
- atk_3 (partial/trivial: return []): EXIT 1. Goal `vars = []`.
- atk_4 (boundary: first element uses false mode, tail true): EXIT 1. Goal `extractSlice false k = extractSlice true k`.
- atk_5 (structure: map ++ map, entries duplicated): EXIT 1. Goal `vars = []`.
- atk_7 (ungrounded-oracle: mode chosen by `vars.length == 0`, so false on nonempty): EXIT 1. Goal `extractSlice false k = extractSlice true k /\ ...`.
- atk_6 (ungrounded-oracle ECHO: impl = spec RHS vars.map(fun k => (k, extractSlice true k)); semantically identical to gold): EXIT 0, verifies. `#print axioms` => does not depend on any axioms (clean). This is the only clean-axiom-closing same-spec impl besides gold.

MANDATORY RESOLVE (protocol step 2): atk_6 is the ONLY wrong-shaped impl whose proof closes with clean axioms. Its faithful refined patch = gold `drop=True` patch (echo behavior == gold: label-removing extraction). Materialized at atk_6.patch and run through the official harness: swebench_unified.harness.run_resolve('pydata__xarray-4094', patch, timeout=1800, retries=1) => RESOLVED: True, note 'resolved'. Docker reached via `docker` (harness path). So the one clean-axiom-closing same-spec impl RESOLVES => no verify=/=>correct break.

A-LEG AUDIT (focus): meta.json axioms=[] (no A-consumed leg, no opaque/axiom decls, axiom_check.py is a skip stub). One deep_model_references entry `sel({variable_dim:k}, drop=True).squeeze(drop=True)` tagged A-reference in refinement.md; conf_skip=False; conformance_check.py binds it to the REAL patched callee (not an axiom) and diff-tests the shadow vs real to_unstacked_dataset over 1e5 fuzzed datasets (seed 4094) via .identical. All refinement.md legs are R / A-reference / I (no kind-3). The A-reference<->callee correspondence in mapping.md holds: extractSlice true k <-> sel(...,drop=True).squeeze(...) (post-patch), extractSlice false k <-> sel(...).squeeze(...) (pre-patch/buggy). The Bool mode arg faithfully models the `drop` keyword; the discriminator is exactly `drop=True`.

CONCLUSION: The fully-pinning spec rejects every genuinely-wrong same-spec impl (all 6 distinct wrong shapes fail to close, each reducing to a provably-false residual over the abstract extractSlice). The only same-spec impls that verify are gold and its semantic echo, and the echo's faithful patch RESOLVES. verify => correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

/-!
Expanding a combined array into a labelled collection of its constituent
variables.

The data carries a list of variable labels along one axis. The operation walks
that list of labels and, for each label, extracts that variable's slice of the
data, assembling the slices into a labelled collection — one entry per label, in
the order the labels are listed.

Each slice is extracted in the label-removing mode: when the slice for a label is
selected, the selecting label is dropped from the slice rather than retained on
it as an attached scalar marker. The required behavior is that every slice is
extracted in this label-removing mode, and that the result lists exactly the
labels, in order, each paired with its extracted slice.

The extraction of a single slice (selecting it and reducing away the now-singleton
axes) is itself a self-contained step; what this bundle pins is the mode in which
that step is invoked and the structure of the assembled collection.
-/

-- axioms-start
-- No unchanged outside callee contract is consumed as a logical property. The
-- per-label slice extraction (selecting the slice for a label and reducing away
-- the now-singleton axes) is left UNIVERSALLY QUANTIFIED as a parameter
-- `extractSlice : Bool → κ → ν`: the first argument is the extraction mode (the
-- label-removing mode when `true`, the label-retaining mode when `false`) and
-- the second is the variable label. The specification holds for EVERY such
-- extraction step, so it pins only that the label-removing mode reaches the
-- extraction for each label, which is exactly the behavior under specification.
-- Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- No additional pure helpers are needed: the labelled collection is expressed
-- directly as a map over the list of labels.
-- pure-end

-- post-conditions-start
/-- The assembled collection of extracted variables.

`κ` is the type of a variable label and `ν` the type of an extracted slice.
`extractSlice mode k` is the extraction of the slice for label `k`, performed in
label-removing mode when `mode = true`. The result is the list of `(label, slice)`
entries.

The result is fully pinned for every input (directive 5 frame): it is exactly the
list of labels, in their given order, each paired with the slice extracted in the
label-removing mode (`extractSlice true k`). No entry, order, or extraction mode
is left free — in particular each slice must be the one produced with the label
removed, never the label-retaining extraction. -/
def problem_spec_toUnstackedDataset {κ ν : Type}
    (extractSlice : Bool → κ → ν) (vars : List κ)
    (result : List (κ × ν)) : Prop :=
  result = vars.map (fun k => (k, extractSlice true k))
-- post-conditions-end

-- impl-start
def implementation_toUnstackedDataset {κ ν : Type}
    (extractSlice : Bool → κ → ν) (vars : List κ) :
    List (κ × ν) := Id.run do
  let mut dataDict : List (κ × ν) := []
  for k in vars do
    dataDict := dataDict ++ [(k, extractSlice true k)]
  return dataDict
-- impl-end

-- proof-start
theorem toUnstackedDataset_forIn_helper {κ ν : Type}
    (f : κ → ν) (vars : List κ) (init : List (κ × ν)) :
    (Id.run (forIn vars init (fun k r =>
      (do pure PUnit.unit; pure (ForInStep.yield (r ++ [(k, f k)]))))))
      = init ++ vars.map (fun k => (k, f k)) := by
  induction vars generalizing init with
  | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp [List.append_assoc]

theorem correct_toUnstackedDataset {κ ν : Type}
    (extractSlice : Bool → κ → ν) (vars : List κ) :
    problem_spec_toUnstackedDataset extractSlice vars
      (implementation_toUnstackedDataset extractSlice vars) := by
  unfold problem_spec_toUnstackedDataset implementation_toUnstackedDataset
  rw [show (Id.run do
      let r ← forIn vars [] fun k r => do
            pure PUnit.unit
            pure (ForInStep.yield (r ++ [(k, extractSlice true k)]))
      pure r)
    = Id.run (forIn vars [] (fun k r =>
      (do pure PUnit.unit; pure (ForInStep.yield (r ++ [(k, extractSlice true k)]))))) from rfl]
  rw [toUnstackedDataset_forIn_helper]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins output: problem_spec := result = vars.map (fun k => (k, extractSlice true k)) over universally-quantified {kappa nu : Type} and abstract extractSlice : Bool->kappa->nu. Both impl AND proof regions are elided from the lean spec view (_lean_spec_view), so attacks freely rewrote both; any closing proof forces the impl extensionally equal to that exact map.

SAME-SPEC: all 7 attacks + positive control verified same_spec=True vs Solution.lean (swebench_unified.markers.same_spec, lean backend).

Verify command per attack: `bash scripts/lean_verify.sh <path>` (run concurrently, <=4 at a time, two batches).

### RESULTS (exit 0 = verifies/no-sorry, 1 = error):
- pos_gold.lean (gold verbatim): EXIT 0. `#print axioms correct_toUnstackedDataset` => [propext, Quot.sound] (standard trusted axioms, clean).
- atk_1 (PREPATCH BUG: extractSlice false k, label-retaining): EXIT 1. Residual goal `forall a in vars, extractSlice false a = extractSlice true a` (unprovable for abstract extractSlice). Prepatch bug reproduced.
- atk_2 (control-flow-effect: prepend `::` => reversed order): EXIT 1. Goal `map(...).reverse = map(...)`.
- atk_3 (partial/trivial: return []): EXIT 1. Goal `vars = []`.
- atk_4 (boundary: first element uses false mode, tail true): EXIT 1. Goal `extractSlice false k = extractSlice true k`.
- atk_5 (structure: map ++ map, entries duplicated): EXIT 1. Goal `vars = []`.
- atk_7 (ungrounded-oracle: mode chosen by `vars.length == 0`, so false on nonempty): EXIT 1. Goal `extractSlice false k = extractSlice true k /\ ...`.
- atk_6 (ungrounded-oracle ECHO: impl = spec RHS vars.map(fun k => (k, extractSlice true k)); semantically identical to gold): EXIT 0, verifies. `#print axioms` => does not depend on any axioms (clean). This is the only clean-axiom-closing same-spec impl besides gold.

MANDATORY RESOLVE (protocol step 2): atk_6 is the ONLY wrong-shaped impl whose proof closes with clean axioms. Its faithful refined patch = gold `drop=True` patch (echo behavior == gold: label-removing extraction). Materialized at atk_6.patch and run through the official harness: swebench_unified.harness.run_resolve('pydata__xarray-4094', patch, timeout=1800, retries=1) => RESOLVED: True, note 'resolved'. Docker reached via `docker` (harness path). So the one clean-axiom-closing same-spec impl RESOLVES => no verify=/=>correct break.

A-LEG AUDIT (focus): meta.json axioms=[] (no A-consumed leg, no opaque/axiom decls, axiom_check.py is a skip stub). One deep_model_references entry `sel({variable_dim:k}, drop=True).squeeze(drop=True)` tagged A-reference in refinement.md; conf_skip=False; conformance_check.py binds it to the REAL patched callee (not an axiom) and diff-tests the shadow vs real to_unstacked_dataset over 1e5 fuzzed datasets (seed 4094) via .identical. All refinement.md legs are R / A-reference / I (no kind-3). The A-reference<->callee correspondence in mapping.md holds: extractSlice true k <-> sel(...,drop=True).squeeze(...) (post-patch), extractSlice false k <-> sel(...).squeeze(...) (pre-patch/buggy). The Bool mode arg faithfully models the `drop` keyword; the discriminator is exactly `drop=True`.

CONCLUSION: The fully-pinning spec rejects every genuinely-wrong same-spec impl (all 6 distinct wrong shapes fail to close, each reducing to a provably-false residual over the abstract extractSlice). The only same-spec impls that verify are gold and its semantic echo, and the echo's faithful patch RESOLVES. verify => correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / model drift) check for DataArray.to_unstacked_dataset (xarray/core/dataarray.py:1633 in worktree @ base_commit).

SPEC REGION: same_spec(Solution, Solution_prepatch, lean_backend) = True. The consumer spec view (signature + axioms + pure + post-conditions) is byte-identical between post- and pre-patch; only impl/proof differ.

LEAN: lean_verify.sh exits 0 (compiles, no sorry). #print axioms correct_toUnstackedDataset => [propext, Quot.sound] — clean, no sorryAx/Classical hack. Proof is genuine.

SPEC: problem_spec = (result = vars.map (fun k => (k, extractSlice true k))). Real post-patch loop: for k in variables: data_dict[k] = self.sel({variable_dim: k}, drop=True).squeeze(drop=True); return Dataset(data_dict). Mapping: vars<->idx.levels[level_number]; extractSlice true k <-> sel(...,drop=True).squeeze(drop=True); List (κ×ν) <-> Dataset(data_dict).

FAITHFULNESS VERDICT: FAITHFUL. No diverging input exists at the modeling abstraction:
(1) drop mode pinned to true matches the patched callee (the whole behavioral content of the fix).
(2) Order preserved: OrderedDict/data_vars insertion order <-> List.map order.
(3) Labels are unique (pandas MultiIndex levels), so no list-vs-dict collapse divergence and no key-collision hazard between the association-list model and the real dict.
(4) Modeling Dataset(data_dict) as the raw assoc list is sound precisely because drop=True makes the merge conflict-free; each slice is stored verbatim, Dataset does not mutate individual variables.
(5) The per-slice extraction is left universally quantified (A-reference), the standard modeling boundary; its concrete callee faithfulness is deferred to G-CONF differential testing (conf_skip=false, real callee, >=1e5 fuzzed inputs, .identical comparison, seed 4094) — appropriate, not an over-strong pin.
The spec is not too strong: it exactly characterizes the fixed behavior; the prepatch (drop=False) variant correctly fails to typecheck against it (G-DIFF). No provable divergence from the real patched callee on any input.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = lines 1-58 (docstring + axioms/pure/post-conditions; impl and proof excluded). It describes the fix in purely abstract terms: an abstract parameter extractSlice : Bool -> κ -> ν whose Bool arg is 'the extraction mode', the required behavior being 'label-removing mode' where 'the selecting label is dropped from the slice rather than retained on it as an attached scalar marker', and the result is the in-order (label, slice) list. It names NO Python file path (xarray/core/dataarray.py), NO line numbers, NO modeled function name (to_unstacked_dataset), NO callee identifiers (sel/squeeze/Dataset/data_dict/variable_dim), NO fix token (drop=True), NO MergeError, and NO diff/patch reference. The prose grep hits (selected/dropped) are ordinary English, not patched identifiers.

Comparison against PUBLIC problem_statement (hints_text excluded per rubric): the public statement already discloses strictly MORE concrete detail than the spec view — a full reproducing MCVE (xr.DataArray, to_stacked_array/to_unstacked_dataset roundtrip), the expected 'working roundtrip', and the literal 'MergeError: conflicting values for variable y'. The spec view reveals LESS than the public statement and adds nothing that reconstructs the gold edit beyond it; the specific fix token drop=True is never surfaced.

Verification performed: (1) mechanical leakage.screen over the Lean solution vs gold patch + problem_statement => passed=True, hard_failures=[]; (2) markers.same_spec(Solution.lean, Solution_prepatch.lean) => True (spec region byte-identical, so the discriminator lives only in impl/proof, outside the spec view); (3) scripts/lean_verify.sh Solution.lean => exit 0 (compiles, no sorry). No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
