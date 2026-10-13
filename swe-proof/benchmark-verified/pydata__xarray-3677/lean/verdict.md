# P2 adversarial audit — pydata__xarray-3677

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_11.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_6.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_12.lean`, `atk_13.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -85,18 +85,13 @@
 -- post-conditions-end
 
 -- impl-start
+-- PREPATCH BUG: the coercion of a single named array is ABSENT. A bare array is
+-- fed to the dataset-to-dataset merge, which cannot consume it.
 noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
     Except OpErr Dataset := Id.run do
-  -- Read the second operand as a dataset: a single named array is read as its
-  -- equivalent one-variable dataset (a reading that may raise); a dataset is
-  -- used unchanged.
-  let read : Except OpErr Dataset :=
-    match other with
-    | .ds d => Except.ok d
-    | .da a => datasetOfArray a
-  -- Delegate to the underlying dataset-to-dataset merge only where the reading
-  -- succeeded; a reading error is the whole outcome.
-  return read.bind (mergeDatasets self)
+  match other with
+  | .ds d => return mergeDatasets self d
+  | .da _ => return Except.error { reason := "'DataArray' object has no attribute 'items'" }
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -85,18 +85,13 @@
 -- post-conditions-end
 
 -- impl-start
+-- PARTIAL DOMAIN: on the array branch the reading happens but the merge stage is
+-- skipped entirely -- the coerced operand is returned as the whole result.
 noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
     Except OpErr Dataset := Id.run do
-  -- Read the second operand as a dataset: a single named array is read as its
-  -- equivalent one-variable dataset (a reading that may raise); a dataset is
-  -- used unchanged.
-  let read : Except OpErr Dataset :=
-    match other with
-    | .ds d => Except.ok d
-    | .da a => datasetOfArray a
-  -- Delegate to the underlying dataset-to-dataset merge only where the reading
-  -- succeeded; a reading error is the whole outcome.
-  return read.bind (mergeDatasets self)
+  match other with
+  | .ds d => return mergeDatasets self d
+  | .da a => return datasetOfArray a
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -85,18 +85,17 @@
 -- post-conditions-end
 
 -- impl-start
+-- BOUNDARY / error payload: the reading error reaches the caller but its payload
+-- is replaced by a generic reason instead of being propagated verbatim.
 noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
     Except OpErr Dataset := Id.run do
-  -- Read the second operand as a dataset: a single named array is read as its
-  -- equivalent one-variable dataset (a reading that may raise); a dataset is
-  -- used unchanged.
   let read : Except OpErr Dataset :=
     match other with
     | .ds d => Except.ok d
     | .da a => datasetOfArray a
-  -- Delegate to the underlying dataset-to-dataset merge only where the reading
-  -- succeeded; a reading error is the whole outcome.
-  return read.bind (mergeDatasets self)
+  match read with
+  | Except.error _ => return Except.error { reason := "cannot merge" }
+  | Except.ok d => return mergeDatasets self d
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -85,18 +85,15 @@
 -- post-conditions-end
 
 -- impl-start
+-- CONTROL-FLOW EFFECT: the merge is invoked with the operands SWAPPED, so the
+-- receiver's variables lose precedence to the second operand's.
 noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
     Except OpErr Dataset := Id.run do
-  -- Read the second operand as a dataset: a single named array is read as its
-  -- equivalent one-variable dataset (a reading that may raise); a dataset is
-  -- used unchanged.
   let read : Except OpErr Dataset :=
     match other with
     | .ds d => Except.ok d
     | .da a => datasetOfArray a
-  -- Delegate to the underlying dataset-to-dataset merge only where the reading
-  -- succeeded; a reading error is the whole outcome.
-  return read.bind (mergeDatasets self)
+  return read.bind (fun d => mergeDatasets d self)
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -85,18 +85,13 @@
 -- post-conditions-end
 
 -- impl-start
+-- UNGROUNDED ORACLE: on the array branch the merge callee is never consulted --
+-- an arbitrary dataset is fabricated and returned as the merge outcome.
 noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
     Except OpErr Dataset := Id.run do
-  -- Read the second operand as a dataset: a single named array is read as its
-  -- equivalent one-variable dataset (a reading that may raise); a dataset is
-  -- used unchanged.
-  let read : Except OpErr Dataset :=
-    match other with
-    | .ds d => Except.ok d
-    | .da a => datasetOfArray a
-  -- Delegate to the underlying dataset-to-dataset merge only where the reading
-  -- succeeded; a reading error is the whole outcome.
-  return read.bind (mergeDatasets self)
+  match other with
+  | .ds d => return mergeDatasets self d
+  | .da _ => return Except.ok (Classical.arbitrary Dataset)
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -85,17 +85,17 @@
 -- post-conditions-end
 
 -- impl-start
+-- A-REFERENCE DISPATCH POLARITY: the dispatch is written the other way round --
+-- "read as a dataset anything that is NOT ALREADY a dataset". Inside the
+-- two-constructor model this is the same function; its faithful refinement is a
+-- DIFFERENT Python predicate (`isinstance(other, xr.Dataset)`), which coerces
+-- every non-Dataset CoercibleMapping operand.
 noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
     Except OpErr Dataset := Id.run do
-  -- Read the second operand as a dataset: a single named array is read as its
-  -- equivalent one-variable dataset (a reading that may raise); a dataset is
-  -- used unchanged.
   let read : Except OpErr Dataset :=
     match other with
+    | .da a => datasetOfArray a
     | .ds d => Except.ok d
-    | .da a => datasetOfArray a
-  -- Delegate to the underlying dataset-to-dataset merge only where the reading
-  -- succeeded; a reading error is the whole outcome.
   return read.bind (mergeDatasets self)
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -85,18 +85,17 @@
 -- post-conditions-end
 
 -- impl-start
+-- ERROR SWALLOWED: a failing reading does not reach the caller -- the operation
+-- silently falls back to merging the receiver with itself.
 noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
     Except OpErr Dataset := Id.run do
-  -- Read the second operand as a dataset: a single named array is read as its
-  -- equivalent one-variable dataset (a reading that may raise); a dataset is
-  -- used unchanged.
   let read : Except OpErr Dataset :=
     match other with
     | .ds d => Except.ok d
     | .da a => datasetOfArray a
-  -- Delegate to the underlying dataset-to-dataset merge only where the reading
-  -- succeeded; a reading error is the whole outcome.
-  return read.bind (mergeDatasets self)
+  match read with
+  | Except.error _ => return mergeDatasets self self
+  | Except.ok d => return mergeDatasets self d
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -85,18 +85,23 @@
 -- post-conditions-end
 
 -- impl-start
+-- A-LEG / ERROR-CLASS CONFLATION. The outcome is rebuilt from its payload: a
+-- success is passed through, and a raised error is RE-RAISED as a fresh `OpErr`
+-- carrying the same `reason` (OpErr's only field). In the model this is the
+-- identical value -- `{ reason := e.reason } = e` by structure eta -- so the
+-- functional equation still holds. But `OpErr` is ONE one-field type standing for
+-- TWO distinct Python exception classes (the `ValueError` `to_dataset` raises and
+-- the `MergeError` the merge raises), so "construct the operation's error with
+-- this reason" has no class in the model to preserve.
 noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
     Except OpErr Dataset := Id.run do
-  -- Read the second operand as a dataset: a single named array is read as its
-  -- equivalent one-variable dataset (a reading that may raise); a dataset is
-  -- used unchanged.
   let read : Except OpErr Dataset :=
     match other with
     | .ds d => Except.ok d
     | .da a => datasetOfArray a
-  -- Delegate to the underlying dataset-to-dataset merge only where the reading
-  -- succeeded; a reading error is the whole outcome.
-  return read.bind (mergeDatasets self)
+  match read.bind (mergeDatasets self) with
+  | Except.ok d => return Except.ok d
+  | Except.error e => return Except.error { reason := e.reason }
 -- impl-end
 
 -- proof-start
@@ -105,5 +110,24 @@
       problem_spec_merge self other (implementation_merge self other) := by
   intro self other
   unfold problem_spec_merge implementation_merge asDataset
-  cases other <;> rfl
+  cases other with
+  | ds d =>
+      first
+        | rfl
+        | (cases h : mergeDatasets self d <;>
+            simp_all [Id.run, Except.bind, bind, pure] <;>
+              first | rfl | aesop)
+        | simp_all [Id.run, Except.bind, bind, pure]
+        | aesop
+  | da a =>
+      first
+        | rfl
+        | (cases h : datasetOfArray a <;>
+            simp_all [Id.run, Except.bind, bind, pure] <;>
+              first | rfl | aesop)
+        | (cases h : (datasetOfArray a).bind (mergeDatasets self) <;>
+            simp_all [Id.run, Except.bind, bind, pure] <;>
+              first | rfl | aesop)
+        | simp_all [Id.run, Except.bind, bind, pure]
+        | aesop
 -- proof-end
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -85,17 +85,18 @@
 -- post-conditions-end
 
 -- impl-start
+-- CONTRAST PAIR for atk_8: the error is rebuilt from its payload ONLY on the
+-- READING stage, the merge's own error propagating untouched. Same modelling hole
+-- (OpErr has no class), but the rebuilt error now sits on the `to_dataset` path.
 noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
     Except OpErr Dataset := Id.run do
-  -- Read the second operand as a dataset: a single named array is read as its
-  -- equivalent one-variable dataset (a reading that may raise); a dataset is
-  -- used unchanged.
   let read : Except OpErr Dataset :=
     match other with
     | .ds d => Except.ok d
-    | .da a => datasetOfArray a
-  -- Delegate to the underlying dataset-to-dataset merge only where the reading
-  -- succeeded; a reading error is the whole outcome.
+    | .da a =>
+        match datasetOfArray a with
+        | Except.ok d => Except.ok d
+        | Except.error e => Except.error { reason := e.reason }
   return read.bind (mergeDatasets self)
 -- impl-end
 
@@ -105,5 +106,24 @@
       problem_spec_merge self other (implementation_merge self other) := by
   intro self other
   unfold problem_spec_merge implementation_merge asDataset
-  cases other <;> rfl
+  cases other with
+  | ds d =>
+      first
+        | rfl
+        | (cases h : mergeDatasets self d <;>
+            simp_all [Id.run, Except.bind, bind, pure] <;>
+              first | rfl | aesop)
+        | simp_all [Id.run, Except.bind, bind, pure]
+        | aesop
+  | da a =>
+      first
+        | rfl
+        | (cases h : datasetOfArray a <;>
+            simp_all [Id.run, Except.bind, bind, pure] <;>
+              first | rfl | aesop)
+        | (cases h : (datasetOfArray a).bind (mergeDatasets self) <;>
+            simp_all [Id.run, Except.bind, bind, pure] <;>
+              first | rfl | aesop)
+        | simp_all [Id.run, Except.bind, bind, pure]
+        | aesop
 -- proof-end
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -85,18 +85,15 @@
 -- post-conditions-end
 
 -- impl-start
+-- STRUCTURAL BRANCH SPLIT: the merge callee is invoked at TWO distinct call sites,
+-- one per operand shape, instead of once after a joined reading. Behaviourally the
+-- same composition; its faithful refinement is an if/else that calls the unchanged
+-- merge guts in each arm.
 noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
     Except OpErr Dataset := Id.run do
-  -- Read the second operand as a dataset: a single named array is read as its
-  -- equivalent one-variable dataset (a reading that may raise); a dataset is
-  -- used unchanged.
-  let read : Except OpErr Dataset :=
-    match other with
-    | .ds d => Except.ok d
-    | .da a => datasetOfArray a
-  -- Delegate to the underlying dataset-to-dataset merge only where the reading
-  -- succeeded; a reading error is the whole outcome.
-  return read.bind (mergeDatasets self)
+  match other with
+  | .ds d => return mergeDatasets self d
+  | .da a => return (datasetOfArray a).bind (mergeDatasets self)
 -- impl-end
 
 -- proof-start
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -85,18 +85,19 @@
 -- post-conditions-end
 
 -- impl-start
+-- DIVERGENCE trap (docs/architecture.md partial-correctness hole): the merge stage
+-- is replaced by a non-terminating self-loop. If the contract were a Hoare
+-- postcondition over terminating runs this would satisfy it vacuously.
+partial def spinMerge (self : Dataset) (d : Dataset) : Except OpErr Dataset :=
+  spinMerge self d
+
 noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
     Except OpErr Dataset := Id.run do
-  -- Read the second operand as a dataset: a single named array is read as its
-  -- equivalent one-variable dataset (a reading that may raise); a dataset is
-  -- used unchanged.
   let read : Except OpErr Dataset :=
     match other with
     | .ds d => Except.ok d
     | .da a => datasetOfArray a
-  -- Delegate to the underlying dataset-to-dataset merge only where the reading
-  -- succeeded; a reading error is the whole outcome.
-  return read.bind (mergeDatasets self)
+  return read.bind (spinMerge self)
 -- impl-end
 
 -- proof-start
@@ -105,5 +106,5 @@
       problem_spec_merge self other (implementation_merge self other) := by
   intro self other
   unfold problem_spec_merge implementation_merge asDataset
-  cases other <;> rfl
+  cases other <;> simp [Id.run, spinMerge] <;> aesop
 -- proof-end
```

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -85,18 +85,10 @@
 -- post-conditions-end
 
 -- impl-start
+-- SPEC-SHAPED ECHO: the postcondition transcribed as the implementation.
 noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
-    Except OpErr Dataset := Id.run do
-  -- Read the second operand as a dataset: a single named array is read as its
-  -- equivalent one-variable dataset (a reading that may raise); a dataset is
-  -- used unchanged.
-  let read : Except OpErr Dataset :=
-    match other with
-    | .ds d => Except.ok d
-    | .da a => datasetOfArray a
-  -- Delegate to the underlying dataset-to-dataset merge only where the reading
-  -- succeeded; a reading error is the whole outcome.
-  return read.bind (mergeDatasets self)
+    Except OpErr Dataset :=
+  (asDataset other).bind (mergeDatasets self)
 -- impl-end
 
 -- proof-start
@@ -104,6 +96,6 @@
     ∀ (self : Dataset) (other : MergeOther),
       problem_spec_merge self other (implementation_merge self other) := by
   intro self other
-  unfold problem_spec_merge implementation_merge asDataset
-  cases other <;> rfl
+  unfold problem_spec_merge implementation_merge
+  rfl
 -- proof-end
```

Attack 13 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -85,17 +85,20 @@
 -- post-conditions-end
 
 -- impl-start
+-- A-LEG CALL-MULTIPLICITY: each unchanged callee is invoked TWICE and the FIRST
+-- result is discarded. In the model both callees are pure functions, so the value
+-- is unchanged and the functional equation still holds -- the spec cannot pin how
+-- many times a callee is invoked. The A-REFERENCE tag ("model == the real callee")
+-- silently presupposes the real callees are side-effect-free; this probes that.
 noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
     Except OpErr Dataset := Id.run do
-  -- Read the second operand as a dataset: a single named array is read as its
-  -- equivalent one-variable dataset (a reading that may raise); a dataset is
-  -- used unchanged.
   let read : Except OpErr Dataset :=
     match other with
     | .ds d => Except.ok d
-    | .da a => datasetOfArray a
-  -- Delegate to the underlying dataset-to-dataset merge only where the reading
-  -- succeeded; a reading error is the whole outcome.
+    | .da a =>
+        let _discard := datasetOfArray a
+        datasetOfArray a
+  let _discard2 := read.bind (mergeDatasets self)
   return read.bind (mergeDatasets self)
 -- impl-end
 
@@ -105,5 +108,24 @@
       problem_spec_merge self other (implementation_merge self other) := by
   intro self other
   unfold problem_spec_merge implementation_merge asDataset
-  cases other <;> rfl
+  cases other with
+  | ds d =>
+      first
+        | rfl
+        | (cases h : mergeDatasets self d <;>
+            simp_all [Id.run, Except.bind, bind, pure] <;>
+              first | rfl | aesop)
+        | simp_all [Id.run, Except.bind, bind, pure]
+        | aesop
+  | da a =>
+      first
+        | rfl
+        | (cases h : datasetOfArray a <;>
+            simp_all [Id.run, Except.bind, bind, pure] <;>
+              first | rfl | aesop)
+        | (cases h : (datasetOfArray a).bind (mergeDatasets self) <;>
+            simp_all [Id.run, Except.bind, bind, pure] <;>
+              first | rfl | aesop)
+        | simp_all [Id.run, Except.bind, bind, pure]
+        | aesop
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -85,18 +85,18 @@
 -- post-conditions-end
 
 -- impl-start
+-- POSITIVE CONTROL: a CORRECT implementation written differently from the gold --
+-- an explicit `Except` case split with the error rebuilt as `Except.error e`
+-- (the SAME error object, not a fresh one) and the merge called in the ok arm.
 noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
     Except OpErr Dataset := Id.run do
-  -- Read the second operand as a dataset: a single named array is read as its
-  -- equivalent one-variable dataset (a reading that may raise); a dataset is
-  -- used unchanged.
   let read : Except OpErr Dataset :=
     match other with
     | .ds d => Except.ok d
     | .da a => datasetOfArray a
-  -- Delegate to the underlying dataset-to-dataset merge only where the reading
-  -- succeeded; a reading error is the whole outcome.
-  return read.bind (mergeDatasets self)
+  match read with
+  | Except.error e => return Except.error e
+  | Except.ok d => return mergeDatasets self d
 -- impl-end
 
 -- proof-start
@@ -105,5 +105,24 @@
       problem_spec_merge self other (implementation_merge self other) := by
   intro self other
   unfold problem_spec_merge implementation_merge asDataset
-  cases other <;> rfl
+  cases other with
+  | ds d =>
+      first
+        | rfl
+        | (cases h : mergeDatasets self d <;>
+            simp_all [Id.run, Except.bind, bind, pure] <;>
+              first | rfl | aesop)
+        | simp_all [Id.run, Except.bind, bind, pure]
+        | aesop
+  | da a =>
+      first
+        | rfl
+        | (cases h : datasetOfArray a <;>
+            simp_all [Id.run, Except.bind, bind, pure] <;>
+              first | rfl | aesop)
+        | (cases h : (datasetOfArray a).bind (mergeDatasets self) <;>
+            simp_all [Id.run, Except.bind, bind, pure] <;>
+              first | rfl | aesop)
+        | simp_all [Id.run, Except.bind, bind, pure]
+        | aesop
 -- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial re-audit of pydata__xarray-3677 (lean). VERDICT: SOUND — no verify⇏correct witness. 13 same-spec wrong impls encoded (same_spec=True AND unsound_evasions=[] for all 13 + the positive control, checked with swebench_unified.markers.same_spec / variant_scope.unsound_evasions against the bundle Solution.lean); 7 rejected by the verifier, 6 verified with clean axioms and ALL SIX had a faithful patch materialized and RUN through run_resolve — all six RESOLVED (echoes, not weaknesses).

**WHY THE SPEC IS TIGHT:** problem_spec_merge is a FUNCTIONAL EQUATION, `result = (asDataset other).bind (mergeDatasets self)`, pinning the result exactly (no existential/relational slack) over the two OPAQUE callees. Any impl not definitionally that composition leaves a goal between two opaque terms, which is unprovable. That is the structural reason every behavioral deviation dies.

VERIFIER-REJECTED (7) — command `bash scripts/lean_verify.sh <file>`:
- atk_1.lean PREPATCH BUG re-encoded (coercion absent; .da => Except.error "'DataArray' object has no attribute 'items'") — EXIT=1, `rfl` failed on .da. prepatch_reproduced=true.
- atk_2.lean PARTIAL DOMAIN (array read but never merged; returns the coerced operand) — EXIT=1.
- atk_3.lean BOUNDARY / error payload not verbatim (reading error's payload replaced by a generic reason) — EXIT=1. Confirms the spec pins the error PAYLOAD.
- atk_4.lean CONTROL-FLOW EFFECT / operands swapped (mergeDatasets d self) — EXIT=1.
- atk_5.lean UNGROUNDED ORACLE (`Except.ok (Classical.arbitrary Dataset)`; merge never consulted on .da) — EXIT=1.
- atk_7.lean ERROR SWALLOWED / fallback to `mergeDatasets self self` on a reading failure — EXIT=1 ("Tactic `rfl` failed", residual LHS printed). Confirms the reading error channel must reach the caller.
- atk_11.lean DIVERGENCE trap (partial-correctness hole): `partial def spinMerge` self-loop on the merge stage — EXIT=1. The hole does NOT apply: the spec is an equation on a pure `Except` value, not a Hoare postcondition over terminating runs, so a diverging rival cannot vacuously satisfy it.

VERIFIED CANDIDATES (6) — each `#print axioms correct_merge` run as ax_<name>.lean, all EXIT=0, NO sorryAx anywhere:
- atk_12.lean SPEC-SHAPED ECHO — EXIT=0; axioms: none. patch_atk_12.diff = byte-identical to the gold coercion. run_resolve => RESOLVED=True COMPLETED=True. Echo.
- atk_6.lean A-REFERENCE DISPATCH-POLARITY (`.da => datasetOfArray a | .ds d => ok d`, i.e. "coerce anything NOT already a dataset") — EXIT=0; axioms: none. THE SHARPEST A-LEG ATTACK: inside the 2-constructor sum it is indistinguishable from gold, yet it refines to a DIFFERENT Python predicate, `other if isinstance(other, xr.Dataset) else other.to_dataset()`, which coerces every non-Dataset CoercibleMapping (merge.py:42 `CoercibleMapping = Union[Dataset, Mapping[...]]`). I CONFIRMED the divergence is real by executing it in a base_commit tree: `ds.merge({'c': 2})` raises AttributeError: 'dict' object has no attribute 'to_dataset'. But it is NOT reachable by F2P+P2P — no PASS_TO_PASS test passes a bare Mapping to the Dataset.merge METHOD (the dict cases in test_merge.py all go through the top-level xr.merge([...]) function; dataset.py:4845 `self.coords.merge(...)` is Coordinates.merge, a different method). run_resolve => RESOLVED=True COMPLETED=True (attempt 2/2, flaky first attempt). Latent modeling-boundary fragility, NOT a G-EQ break.
- atk_8.lean A-LEG ERROR-CLASS CONFLATION — the whole outcome rebuilt from its payload (`| Except.error e => Except.error { reason := e.reason }`). EXIT=0; axioms: [propext]. MOTIVE: `OpErr` is ONE one-field structure standing for TWO distinct Python exception classes — the `ValueError` `_to_dataset_whole` raises and the `MergeError` the merge raises (merge.py:73 `class MergeError(ValueError)`) — so "rebuild the error from its reason" appeared to have no class to preserve. run_resolve on the faithful patch => RESOLVED=True COMPLETED=True. Echo.
- atk_9.lean CONTRAST PAIR for atk_8: payload-rebuild on the READING stage only — EXIT=0; axioms: [propext]. run_resolve => RESOLVED=True COMPLETED=True. Echo.
- atk_10.lean STRUCTURAL BRANCH SPLIT: mergeDatasets invoked at TWO call sites, one per operand shape — EXIT=0; axioms: none. run_resolve => RESOLVED=True COMPLETED=True (attempt 2/2). Echo.
- atk_13.lean A-LEG CALL-MULTIPLICITY: each unchanged callee invoked TWICE with the first result discarded — probes whether the A-reference tag silently presupposes side-effect-free callees. EXIT=0; axioms: none. patch_atk_13.diff calls `other.to_dataset()` and `dataset_merge_method(...)` an extra time, discarding each. run_resolve => RESOLVED=True COMPLETED=True. Echo — the real callees ARE pure, so the presupposition holds.

THE NEAR-MISS, AND WHY IT IS NOT A BREAK (the central judgement of this audit). atk_8's motive above suggested an over-refinement in which the rebuilt error changes CLASS: `patch_atk_8_COLLAPSE_diagnostic.diff` re-raises `ValueError(str(e))`, collapsing MergeError to its base class. I RAN it: run_resolve => RESOLVED=False COMPLETED=True ("consistent — not flaky"), patch_applied=True, F2P 1/1 PASS, PASS_TO_PASS 19 success / 2 FAILURE — `TestMergeMethod::test_merge_compat` and `TestMergeMethod::test_merge_no_conflicts`, exactly the two that assert `pytest.raises(xr.MergeError)`. So a non-resolving same-spec patch DOES exist in the neighbourhood.

It is NOT a G-EQ break because that patch is NOT a faithful refinement of atk_8's Lean: I proved by `rfl` (eta_check.lean, EXIT=0) that `({ reason := e.reason } : OpErr) = e` and `Except.error { reason := e.reason } = Except.error e` and that the whole rebuild combinator is the identity on `Except OpErr α` — structure eta on a single-field structure makes atk_8's impl DEFINITIONALLY the gold impl, licensing no class change whatsoever. The faithful refinement re-raises the same exception object (`e.args = (str(e),); raise`), which I confirmed preserves the class locally (MergeError still raised) and which RESOLVES. Recording the collapse patch as the break would have been the retained-attack-label error in reverse: judging an over-refinement as a spec weakness. The honest reading: `OpErr` under-models the exception hierarchy (one Lean type for ValueError and MergeError), but the equation's error channel is propagated verbatim as a VALUE, so no verifying impl can license the class change.

### Measurement-trap controls
(1) POSITIVE CONTROL pos_control.lean — structurally different CORRECT impl (explicit Except case split, error re-raised as `Except.error e`, non-gold proof) — EXIT=0 VERIFIES; ax_pos_control.lean EXIT=0, axioms: [propext], no sorryAx. So the 7 rejections are meaningful. NOTE: pos_control FIRST failed EXIT=1 on a mere TACTIC gap (residual goals `pure X = X` and `(Except.ok d).bind f = f d`, both trivially true) — had I read that as a rejection I would have recorded a false "spec too strong" and, worse, would have discarded atk_8/atk_9 (which failed the same way) before ever materializing their patches.

(2) PROOF-TAIL TRAP guarded: all 7 rejections were RE-RUN with a maximal generic proof (nested `first | rfl | (cases h : ... <;> simp_all [Id.run, Except.bind, bind, pure] <;> first | rfl | aesop) | aesop`) as atk_{1,2,3,4,5,7,11}`_strong`.lean — ALL EXIT=1, aesop reporting "failed to prove the goal after exhaustive search". Genuine SPEC rejections, not broken tactics.

(3) KILLED-BUILD TRAP guarded: every EXIT=1 log carries real Lean diagnostics (992–2153 bytes, explicit "Tactic `rfl` failed" / "unsolved goals" with the residual goal printed). No empty-output nonzero exits, no EXIT=124.

(4) ORACLE FITNESS: meta.json G-RESOLVE=pass on the gold patch, so `_oracle_cannot_refute_here` is empty and a not-resolved verdict here carries information — established by the collapse diagnostic actually returning RESOLVED=False.

(5) INFRA-VS-EVIDENCE: atk_8's first resolve returned COMPLETED=False with docker.errors.ImageNotFound (a 404 on an image sha) — caused by MY OWN 4-way parallel resolve launch racing the image cache, not by the patch. Re-run serially it completed RESOLVED=True. All 6 reported resolves are COMPLETED=True.

**PATCH HYGIENE:** all 6 submitted patches + the diagnostic were generated by real edits in a base_commit worktree (`git worktree add --detach ... ef6e6a7b`) and emitted by `git diff`; each was verified with `git apply --check` in a clean base_commit tree — exit 0 for all 7.

REFINEMENT.MD LEG AUDIT (§3): PASSES. 2 legs, both A-reference, NO kind-3 leg. meta.json axioms=[] and `grep -c '^\s*axiom '` Solution.lean = 0, sorry/admit = 0 — confirmed NO consumed property axiom, so there is no A-consumed leg to audit; correct_merge closes by `cases other <;> rfl` over the opaque signatures alone. Anchors CONFIRMED at base_commit ef6e6a7b: leg 1 `datasetOfArray` == `DataArray.to_dataset()` (no dim) -> `_to_dataset_whole` (dataarray.py:490 `def to_dataset(self, dim: Hashable = None, *, name: Hashable = None)`, :462 `def _to_dataset_whole`); the PARTIAL `Except OpErr Dataset` model is FAITHFUL — I read the body and it raises ValueError on exactly two conditions (unnamed array; name colliding with a coordinate).

Leg 2 `mergeDatasets` == `dataset_merge_method` + `Dataset._replace` (merge.py:798, :501 merge_core, :73 class MergeError; dataset.py:887 `_replace`, :3548 `def merge`). mapping.md cites merge.py:548 for merge_core (actual 501) and dataset.py:3547 for the method (actual 3548) — off-by-small line drift in PROSE only; symbols and the patch hunk (@@ -3604,6 +3604,7 @@, coercion landing immediately before the dataset_merge_method call) are correct. Both callees are genuinely UNCHANGED by patch.diff — verified mechanically: the gold patch adds exactly one line to dataset.py and its diff mentions neither dataarray.py nor merge.py (grep count 0), which is what licenses A-reference over A-consumed. Model<->patch correspondence HOLDS: the 2-constructor `match` <-> `isinstance(other, xr.DataArray)`, `.to_dataset()` <-> datasetOfArray, unchanged guts <-> mergeDatasets.

TWO DOCUMENTED (NON-BLOCKING) OBSERVATIONS for G-PANEL-2, neither a verify⇏correct witness: (a) the `MergeOther` sum models only the two runtime shapes the fix's isinstance distinguishes, leaving dict-like CoercibleMapping operands outside the model — refinement.md and mapping.md both disclose and scope this out; atk_6 shows the cost is real (executed AttributeError on a dict operand) but its patch RESOLVES. (b) `OpErr` is a single one-field error type for two distinct Python exception classes; the collapse diagnostic shows 2 P2P tests depend on that distinction, but structure eta means no verifying same-spec impl can license the collapse. Both are modeling-boundary feedback, not spec weakness.

**FLOOR:** 13 distinct same-spec admissible attacks (>= 5 required), prepatch bug reproduced (atk_1), structurally different positive control verifies with clean axioms, ALL SIX verifying candidates had faithful patches materialized and RESOLVE-RUN to COMPLETED=True, and the one non-resolving patch was proven an unfaithful over-refinement by machine (`rfl`). Nothing was left unmeasured.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_11.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_6.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_12.lean`, `atk_13.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -85,18 +85,18 @@
 -- post-conditions-end
 
 -- impl-start
+-- POSITIVE CONTROL: a CORRECT implementation written differently from the gold --
+-- an explicit `Except` case split with the error rebuilt as `Except.error e`
+-- (the SAME error object, not a fresh one) and the merge called in the ok arm.
 noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
     Except OpErr Dataset := Id.run do
-  -- Read the second operand as a dataset: a single named array is read as its
-  -- equivalent one-variable dataset (a reading that may raise); a dataset is
-  -- used unchanged.
   let read : Except OpErr Dataset :=
     match other with
     | .ds d => Except.ok d
     | .da a => datasetOfArray a
-  -- Delegate to the underlying dataset-to-dataset merge only where the reading
-  -- succeeded; a reading error is the whole outcome.
-  return read.bind (mergeDatasets self)
+  match read with
+  | Except.error e => return Except.error e
+  | Except.ok d => return mergeDatasets self d
 -- impl-end
 
 -- proof-start
@@ -105,5 +105,24 @@
       problem_spec_merge self other (implementation_merge self other) := by
   intro self other
   unfold problem_spec_merge implementation_merge asDataset
-  cases other <;> rfl
+  cases other with
+  | ds d =>
+      first
+        | rfl
+        | (cases h : mergeDatasets self d <;>
+            simp_all [Id.run, Except.bind, bind, pure] <;>
+              first | rfl | aesop)
+        | simp_all [Id.run, Except.bind, bind, pure]
+        | aesop
+  | da a =>
+      first
+        | rfl
+        | (cases h : datasetOfArray a <;>
+            simp_all [Id.run, Except.bind, bind, pure] <;>
+              first | rfl | aesop)
+        | (cases h : (datasetOfArray a).bind (mergeDatasets self) <;>
+            simp_all [Id.run, Except.bind, bind, pure] <;>
+              first | rfl | aesop)
+        | simp_all [Id.run, Except.bind, bind, pure]
+        | aesop
 -- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial re-audit of pydata__xarray-3677 (lean). VERDICT: SOUND — no verify⇏correct witness. 13 same-spec wrong impls encoded (same_spec=True AND unsound_evasions=[] for all 13 + the positive control, checked with swebench_unified.markers.same_spec / variant_scope.unsound_evasions against the bundle Solution.lean); 7 rejected by the verifier, 6 verified with clean axioms and ALL SIX had a faithful patch materialized and RUN through run_resolve — all six RESOLVED (echoes, not weaknesses).

**WHY THE SPEC IS TIGHT:** problem_spec_merge is a FUNCTIONAL EQUATION, `result = (asDataset other).bind (mergeDatasets self)`, pinning the result exactly (no existential/relational slack) over the two OPAQUE callees. Any impl not definitionally that composition leaves a goal between two opaque terms, which is unprovable. That is the structural reason every behavioral deviation dies.

VERIFIER-REJECTED (7) — command `bash scripts/lean_verify.sh <file>`:
- atk_1.lean PREPATCH BUG re-encoded (coercion absent; .da => Except.error "'DataArray' object has no attribute 'items'") — EXIT=1, `rfl` failed on .da. prepatch_reproduced=true.
- atk_2.lean PARTIAL DOMAIN (array read but never merged; returns the coerced operand) — EXIT=1.
- atk_3.lean BOUNDARY / error payload not verbatim (reading error's payload replaced by a generic reason) — EXIT=1. Confirms the spec pins the error PAYLOAD.
- atk_4.lean CONTROL-FLOW EFFECT / operands swapped (mergeDatasets d self) — EXIT=1.
- atk_5.lean UNGROUNDED ORACLE (`Except.ok (Classical.arbitrary Dataset)`; merge never consulted on .da) — EXIT=1.
- atk_7.lean ERROR SWALLOWED / fallback to `mergeDatasets self self` on a reading failure — EXIT=1 ("Tactic `rfl` failed", residual LHS printed). Confirms the reading error channel must reach the caller.
- atk_11.lean DIVERGENCE trap (partial-correctness hole): `partial def spinMerge` self-loop on the merge stage — EXIT=1. The hole does NOT apply: the spec is an equation on a pure `Except` value, not a Hoare postcondition over terminating runs, so a diverging rival cannot vacuously satisfy it.

VERIFIED CANDIDATES (6) — each `#print axioms correct_merge` run as ax_<name>.lean, all EXIT=0, NO sorryAx anywhere:
- atk_12.lean SPEC-SHAPED ECHO — EXIT=0; axioms: none. patch_atk_12.diff = byte-identical to the gold coercion. run_resolve => RESOLVED=True COMPLETED=True. Echo.
- atk_6.lean A-REFERENCE DISPATCH-POLARITY (`.da => datasetOfArray a | .ds d => ok d`, i.e. "coerce anything NOT already a dataset") — EXIT=0; axioms: none. THE SHARPEST A-LEG ATTACK: inside the 2-constructor sum it is indistinguishable from gold, yet it refines to a DIFFERENT Python predicate, `other if isinstance(other, xr.Dataset) else other.to_dataset()`, which coerces every non-Dataset CoercibleMapping (merge.py:42 `CoercibleMapping = Union[Dataset, Mapping[...]]`). I CONFIRMED the divergence is real by executing it in a base_commit tree: `ds.merge({'c': 2})` raises AttributeError: 'dict' object has no attribute 'to_dataset'. But it is NOT reachable by F2P+P2P — no PASS_TO_PASS test passes a bare Mapping to the Dataset.merge METHOD (the dict cases in test_merge.py all go through the top-level xr.merge([...]) function; dataset.py:4845 `self.coords.merge(...)` is Coordinates.merge, a different method). run_resolve => RESOLVED=True COMPLETED=True (attempt 2/2, flaky first attempt). Latent modeling-boundary fragility, NOT a G-EQ break.
- atk_8.lean A-LEG ERROR-CLASS CONFLATION — the whole outcome rebuilt from its payload (`| Except.error e => Except.error { reason := e.reason }`). EXIT=0; axioms: [propext]. MOTIVE: `OpErr` is ONE one-field structure standing for TWO distinct Python exception classes — the `ValueError` `_to_dataset_whole` raises and the `MergeError` the merge raises (merge.py:73 `class MergeError(ValueError)`) — so "rebuild the error from its reason" appeared to have no class to preserve. run_resolve on the faithful patch => RESOLVED=True COMPLETED=True. Echo.
- atk_9.lean CONTRAST PAIR for atk_8: payload-rebuild on the READING stage only — EXIT=0; axioms: [propext]. run_resolve => RESOLVED=True COMPLETED=True. Echo.
- atk_10.lean STRUCTURAL BRANCH SPLIT: mergeDatasets invoked at TWO call sites, one per operand shape — EXIT=0; axioms: none. run_resolve => RESOLVED=True COMPLETED=True (attempt 2/2). Echo.
- atk_13.lean A-LEG CALL-MULTIPLICITY: each unchanged callee invoked TWICE with the first result discarded — probes whether the A-reference tag silently presupposes side-effect-free callees. EXIT=0; axioms: none. patch_atk_13.diff calls `other.to_dataset()` and `dataset_merge_method(...)` an extra time, discarding each. run_resolve => RESOLVED=True COMPLETED=True. Echo — the real callees ARE pure, so the presupposition holds.

THE NEAR-MISS, AND WHY IT IS NOT A BREAK (the central judgement of this audit). atk_8's motive above suggested an over-refinement in which the rebuilt error changes CLASS: `patch_atk_8_COLLAPSE_diagnostic.diff` re-raises `ValueError(str(e))`, collapsing MergeError to its base class. I RAN it: run_resolve => RESOLVED=False COMPLETED=True ("consistent — not flaky"), patch_applied=True, F2P 1/1 PASS, PASS_TO_PASS 19 success / 2 FAILURE — `TestMergeMethod::test_merge_compat` and `TestMergeMethod::test_merge_no_conflicts`, exactly the two that assert `pytest.raises(xr.MergeError)`. So a non-resolving same-spec patch DOES exist in the neighbourhood.

It is NOT a G-EQ break because that patch is NOT a faithful refinement of atk_8's Lean: I proved by `rfl` (eta_check.lean, EXIT=0) that `({ reason := e.reason } : OpErr) = e` and `Except.error { reason := e.reason } = Except.error e` and that the whole rebuild combinator is the identity on `Except OpErr α` — structure eta on a single-field structure makes atk_8's impl DEFINITIONALLY the gold impl, licensing no class change whatsoever. The faithful refinement re-raises the same exception object (`e.args = (str(e),); raise`), which I confirmed preserves the class locally (MergeError still raised) and which RESOLVES. Recording the collapse patch as the break would have been the retained-attack-label error in reverse: judging an over-refinement as a spec weakness. The honest reading: `OpErr` under-models the exception hierarchy (one Lean type for ValueError and MergeError), but the equation's error channel is propagated verbatim as a VALUE, so no verifying impl can license the class change.

### Measurement-trap controls
(1) POSITIVE CONTROL pos_control.lean — structurally different CORRECT impl (explicit Except case split, error re-raised as `Except.error e`, non-gold proof) — EXIT=0 VERIFIES; ax_pos_control.lean EXIT=0, axioms: [propext], no sorryAx. So the 7 rejections are meaningful. NOTE: pos_control FIRST failed EXIT=1 on a mere TACTIC gap (residual goals `pure X = X` and `(Except.ok d).bind f = f d`, both trivially true) — had I read that as a rejection I would have recorded a false "spec too strong" and, worse, would have discarded atk_8/atk_9 (which failed the same way) before ever materializing their patches.

(2) PROOF-TAIL TRAP guarded: all 7 rejections were RE-RUN with a maximal generic proof (nested `first | rfl | (cases h : ... <;> simp_all [Id.run, Except.bind, bind, pure] <;> first | rfl | aesop) | aesop`) as atk_{1,2,3,4,5,7,11}`_strong`.lean — ALL EXIT=1, aesop reporting "failed to prove the goal after exhaustive search". Genuine SPEC rejections, not broken tactics.

(3) KILLED-BUILD TRAP guarded: every EXIT=1 log carries real Lean diagnostics (992–2153 bytes, explicit "Tactic `rfl` failed" / "unsolved goals" with the residual goal printed). No empty-output nonzero exits, no EXIT=124.

(4) ORACLE FITNESS: meta.json G-RESOLVE=pass on the gold patch, so `_oracle_cannot_refute_here` is empty and a not-resolved verdict here carries information — established by the collapse diagnostic actually returning RESOLVED=False.

(5) INFRA-VS-EVIDENCE: atk_8's first resolve returned COMPLETED=False with docker.errors.ImageNotFound (a 404 on an image sha) — caused by MY OWN 4-way parallel resolve launch racing the image cache, not by the patch. Re-run serially it completed RESOLVED=True. All 6 reported resolves are COMPLETED=True.

**PATCH HYGIENE:** all 6 submitted patches + the diagnostic were generated by real edits in a base_commit worktree (`git worktree add --detach ... ef6e6a7b`) and emitted by `git diff`; each was verified with `git apply --check` in a clean base_commit tree — exit 0 for all 7.

REFINEMENT.MD LEG AUDIT (§3): PASSES. 2 legs, both A-reference, NO kind-3 leg. meta.json axioms=[] and `grep -c '^\s*axiom '` Solution.lean = 0, sorry/admit = 0 — confirmed NO consumed property axiom, so there is no A-consumed leg to audit; correct_merge closes by `cases other <;> rfl` over the opaque signatures alone. Anchors CONFIRMED at base_commit ef6e6a7b: leg 1 `datasetOfArray` == `DataArray.to_dataset()` (no dim) -> `_to_dataset_whole` (dataarray.py:490 `def to_dataset(self, dim: Hashable = None, *, name: Hashable = None)`, :462 `def _to_dataset_whole`); the PARTIAL `Except OpErr Dataset` model is FAITHFUL — I read the body and it raises ValueError on exactly two conditions (unnamed array; name colliding with a coordinate).

Leg 2 `mergeDatasets` == `dataset_merge_method` + `Dataset._replace` (merge.py:798, :501 merge_core, :73 class MergeError; dataset.py:887 `_replace`, :3548 `def merge`). mapping.md cites merge.py:548 for merge_core (actual 501) and dataset.py:3547 for the method (actual 3548) — off-by-small line drift in PROSE only; symbols and the patch hunk (@@ -3604,6 +3604,7 @@, coercion landing immediately before the dataset_merge_method call) are correct. Both callees are genuinely UNCHANGED by patch.diff — verified mechanically: the gold patch adds exactly one line to dataset.py and its diff mentions neither dataarray.py nor merge.py (grep count 0), which is what licenses A-reference over A-consumed. Model<->patch correspondence HOLDS: the 2-constructor `match` <-> `isinstance(other, xr.DataArray)`, `.to_dataset()` <-> datasetOfArray, unchanged guts <-> mergeDatasets.

TWO DOCUMENTED (NON-BLOCKING) OBSERVATIONS for G-PANEL-2, neither a verify⇏correct witness: (a) the `MergeOther` sum models only the two runtime shapes the fix's isinstance distinguishes, leaving dict-like CoercibleMapping operands outside the model — refinement.md and mapping.md both disclose and scope this out; atk_6 shows the cost is real (executed AttributeError on a dict operand) but its patch RESOLVES. (b) `OpErr` is a single one-field error type for two distinct Python exception classes; the collapse diagnostic shows 2 P2P tests depend on that distinction, but structure eta means no verifying same-spec impl can license the collapse. Both are modeling-boundary feedback, not spec weakness.

**FLOOR:** 13 distinct same-spec admissible attacks (>= 5 required), prepatch bug reproduced (atk_1), structurally different positive control verifies with clean axioms, ALL SIX verifying candidates had faithful patches materialized and RESOLVE-RUN to COMPLETED=True, and the one non-resolving patch was proven an unfaithful over-refinement by machine (`rfl`). Nothing was left unmeasured.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ROLE:** faithfulness-break attacker (2) — is the spec too strong / does the modeled function disagree with the real repo callee on some input? Reference = base commit ef6e6a7b with patch.diff APPLIED (per instructions); base is reference only for the untouched callees the axioms model.

**SPEC UNDER TEST:** problem_spec_merge self other result := result = (asDataset other).bind (mergeDatasets self), with asDataset (.ds d) = ok d, asDataset (.da a) = datasetOfArray a. i.e. read-the-operand-then-merge, both error channels propagated verbatim.

#### Integrity / preliminaries
- patch.diff applies cleanly to a fresh worktree of ef6e6a7b. The patch is exactly one added line at dataset.py:3607: `other = other.to_dataset() if isinstance(other, xr.DataArray) else other`, immediately before the unchanged dataset_merge_method(...) call. `import xarray as xr` is present at dataset.py:33, so the isinstance dispatch resolves.
- markers.same_spec(Solution.lean, Solution_prepatch.lean, lean backend) = True — the spec region is BYTE-IDENTICAL between gold and the prepatch discriminator, so the prepatch failure is attributable to the impl, not to a moved spec.
- Solution.lean: scripts/lean_verify.sh exit 0 (compiles, no sorry). `#print axioms` on correct_merge, implementation_merge, problem_spec_merge => all three report "does not depend on any axioms" — no sorryAx, proof is real. correct_merge closes by `cases other <;> rfl`, consistent with refinement.md's no-A-consumed claim.
- SPEC HAS TEETH (not vacuous): Solution_prepatch.lean exits 1. The carried gold proof fails exactly on the `.da` branch — Lean reports the unclosed goal `(match .da a with ... => pure (Except.error {reason := "operand has no items"})).run = (... => datasetOfArray a).bind (mergeDatasets self)`. The `.ds` branch still closes by rfl. So the spec genuinely discriminates the patched behavior on the DataArray operand.

### FAITHFULNESS EVIDENCE (the actual attack)
Built the patched worktree into a venv (numpy 1.26.4 / pandas 2.1.4, xarray 0.14.1+40.gef6e6a7b) and differentially tested the real `Dataset.merge` against the spec's RHS (read operand via .to_dataset(), then merge), comparing BOTH channels: success via Dataset.identical, error via (type name, message) pair.

1. Targeted edge probes (15/15 agreement), incl. the cases where partiality matters:
   - named DataArray (F2P scenario): ds.merge(da) == ds.merge(da.to_dataset()) == xr.merge([ds,da]) — all identical=True.
   - UNNAMED DataArray: real merge raises ValueError('unable to convert unnamed DataArray to a Dataset without providing an explicit name') and so does to_dataset() — the READING error is the whole outcome, no merge attempted. This is precisely the partiality the spec models via `datasetOfArray : DataArray -> Except OpErr Dataset`; a total `DataArray -> Dataset` model WOULD have been unfaithful here, and the current spec is not.
   - DataArray whose name collides with one of its own coords: real raises ValueError('cannot create a Dataset from a DataArray with the same name as one of its coordinates') — again reading-stage error, matched.
   - conflicting named DataArray: reading SUCCEEDS, then MergeError('conflicting values for variable a ...') — merge-stage error, matched verbatim against the composition. Confirms the two error channels are ordered correctly (read before merge) and not conflated.
   - also matched: name=0, name=('p','q'), misaligned index (outer join), extra coord, 0-d scalar da, attrs, name==own dim, name=='a' with equal values, name=='a' with NaN (no_conflicts fill), MultiIndex operand, empty ds operand, conflicting ds operand, empty self.
2. Seeded differential fuzz (seed 3677, the pinned mapping.md seed): 2480 executed (self_ds, other) pairs over random names {None,'a','b','x','y','v_i',0}, dims {x,y,z}, lengths 1-3, values incl. NaN, optional/misaligned coords, optional extra coord, and both operand shapes. Result: **0 mismatches** in kind, error (type,message), or Dataset.identical.
3. Callee-exactness check: re-ran the comparison with mergeDatasets instantiated as the LITERAL guts the patch cites — dataset_merge_method(self, other, overwrite_vars=frozenset(), compat='no_conflicts', join='outer', fill_value=dtypes.NA) followed by self.`_replace`(**r.`_asdict`()) — rather than via the ds.merge proxy. 17/17 agreement. So the `mergeDatasets` and `datasetOfArray` A-reference bindings in mapping.md match the real callees on the tested domain, and the spec asserts no property about either beyond its signature.
4. F2P confirmation: xarray/tests/test_merge.py::TestMergeMethod::test_merge_dataarray => 1 passed on the patched tree.

No input in the modeled domain was found on which the spec disagrees with the real patched repo. The spec is an exact-composition equality over the same opaque callees, which is the tightest faithful statement available here — it is not over-strong (it does not, e.g., assert the merge always succeeds, nor that reading is total).

### SCOPE NOTES (examined, NOT defects; no divergence in the modeled domain)
- `MergeOther` covers only Dataset | DataArray, excluding dict-like `CoercibleMapping` operands. This is a declared domain restriction (R refinement, documented in both mapping.md and refinement.md), not an over-strong claim: the closed 2-constructor inductive makes no assertion about dicts, so no dict input can witness a disagreement. The pre-patch already handled dicts; the bug is DataArray-only.
- `_check_inplace(inplace)` is unmodeled. Verified at utils.py:38 that it is a NO-OP for the default inplace=None, and the modeled signature takes only (self, other), so the deprecated-kwarg TypeError path is outside the modeled domain. Harmless.
- OpErr collapses ValueError (reading stage) and MergeError (merge stage) into one opaque carrier. This is a COARSENING (weaker/abstract), not a strengthening, and cannot manufacture a divergence: both sides of the asserted equality range over the same callees. Note the region docstring was rewritten (MergeErr -> OpErr) when datasetOfArray was made partial; the spec text and refinement.md's prose still say 'MergeErr' in the mapping table, a cosmetic doc lag only.

== SEPARATE FINDING, OUT OF THIS GATE'S SCOPE (route to G-INTEGRITY, not a faithfulness break) == meta.json['region_hashes'] is STALE for all six regions — every one mismatches the value recomputed from the current Solution.lean via markers.region_hashes (e.g. axioms 9a454d48… computed vs d3747e8e… recorded; spec_view 40583974… vs 24c7c5cf…). Cause identified from git history, NOT a tamper: commit eda4fe422 ('release-prep scrub') semantically STRENGTHENED the spec after meta.json was stamped — `MergeErr`->`OpErr`, and crucially `noncomputable opaque datasetOfArray : DataArray -> Dataset` (TOTAL) became `opaque datasetOfArray : DataArray -> Except OpErr Dataset` (PARTIAL), with asDataset and problem_spec_merge lifted into Except accordingly.

The current, stronger spec is the one I validated and it is the FAITHFUL one — the older total-reading model would have been UNFAITHFUL on the unnamed-DataArray and coord-name-collision inputs above (real raises ValueError; a total datasetOfArray could not express that). So the edit fixed a real hole; only the stamped hashes need refreshing. Per the retained-attack rule this prose/spec edit also voids any retained attack records keyed on the old spec_signature. Flagging because a downstream freshness check will read these hashes as a mismatch.

**CONCLUSION:** FAITHFUL. No diverging input exists on the tested domain (2480 fuzz + 32 targeted/direct-callee cases, 0 mismatches), the proof is axiom-clean, and the spec discriminates the prepatch variant.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**Scope:** leakage/gold-reconstruction over the consumer spec view of lean/Solution.lean for pydata__xarray-3677, baseline = problem_statement only (hints_text excluded).

### WHAT I RAN (measurements, not assertions):
- Projected the spec view myself: src/swebench_unified.markers.spec_view(Solution.lean, get_backend('lean')). Computed region_hashes match the FRESH G-HYGIENE record exactly, incl. spec_view=40583974c09582d5251842650b2ae395a7aca6962af8ea67e02f2919356f8392 -- so the text I judged is the recorded spec view. (Note: meta.json's TOP-LEVEL region_hashes block is STALE -- spec_view=24c7c5cf...; it predates the Aug-13 prose edit of Solution.lean. Bookkeeping only, no leakage consequence; G-HYGIENE 2026-08-16 and the Aug-14 G-EQ/G-PANEL both postdate the edit.)
- markers.same_spec(Solution.lean, Solution_prepatch.lean, lean) = True -> spec region byte-identical across gold and prepatch; the prepatch differs only in impl/proof, so no spec-side tell was inserted for the discriminator.
- scripts/lean_verify.sh Solution.lean -> exit 0; appended `#print axioms correct_merge` / `implementation_merge` -> both "does not depend on any axioms" (no sorryAx, and meta.axioms=[] is consistent: proof closes by `cases other <;> rfl` over opaque callees).
- Load-bearing check on the discriminating clause: scripts/lean_verify.sh Solution_prepatch.lean -> exit 1, failing exactly on `case da` (goal shows the buggy `Except.error {reason := "operand has no items"}` vs the spec's `(asDataset other).bind (mergeDatasets self)`). So the .da clause in problem_spec_merge is genuinely load-bearing, not narration.

DERIVABILITY FROM problem_statement (the leakage test): the public statement gives (a) `ds.merge(da)` must work, (b) `xr.merge([ds, da])` already works and is the expected outcome, (c) the printed expected Dataset shows the named array `da` (name='b') appearing as a one-variable data var alongside `a` -- i.e. the array read as its equivalent one-variable dataset and then merged, and (d) the traceback names the pre-existing, unchanged merge guts invoked from Dataset.merge (dataset_merge_method -> merge_core -> coerce_pandas_values), so "delegate to the underlying dataset-to-dataset merge" is literally in the public text. Every clause of the spec view reduces to (a)-(d): the two-shape operand (`MergeOther = .ds | .da`), `asDataset` reading a dataset unchanged / an array as its one-variable dataset, and `result = (asDataset other).bind (mergeDatasets self)`.

WHAT THE SPEC VIEW DOES NOT SAY (checked by grep over the projected text): no `to_dataset`, no `isinstance`, no `xr.DataArray`, no file/line/callee identifiers, no statement of WHERE the coercion goes (nothing about inserting a line before the dataset_merge_method call, nothing about `_check_inplace`), no mention of a patch/fix/bug. Callee names are abstract (`datasetOfArray`, `mergeDatasets`); `datasetOfArray` denotes the semantics the public expected-output already forces, not the Python method name. The one clause with no public antecedent is the "PARTIAL reading may raise, and that error is the whole outcome with no merge attempted" narration -- I judged this non-leaking: it is total-behavior completeness for the error channel and matches default Python raise-propagation; it discloses no branch structure, no try/except, and no operand-shape test the statement lacks. The gold one-liner is not reconstructible from the spec view beyond what (a)-(d) already force.

**RELAXATION:** none claimed. No RELAXED_LEAKAGE.md anywhere in the instance tree and no `relaxed_leakage` key in lean/meta.json (keys checked). So this is a plain NO-LEAKAGE, not an inherited disposition.

**BUNDLE-ADDRESSES-AUDITOR SCAN:** grepped Solution*.lean, mapping.md, refinement.md, properties.py, meta.json for auditor/reviewer/panel-directed prose and verdict instructions. Nothing instructs me how to record or which verdict is honest. Two benign hits in properties.py (lines 943, 983: "ADDED BY THE FAITHFULNESS PANEL...") are property provenance comments, not directives. refinement.md/mapping.md do quote the gold patch verbatim and cite file:line -- expected and correct for audit-side provenance documents, which are not part of the consumer spec view projection; flagging only so the record shows I checked the boundary rather than ignored those files.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.