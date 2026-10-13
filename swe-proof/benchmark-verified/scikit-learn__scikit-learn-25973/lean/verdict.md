# P2 adversarial audit — scikit-learn__scikit-learn-25973

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-EQ: 7 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,13 +49,14 @@
 -- impl-start
 def implementation_repeatedEvaluations
     (folds : List Nat) (oneShot : Bool) (numEvals : Nat) : List (List Nat) := Id.run do
-  -- Capture the collection into a reusable value once, before any evaluation
-  -- runs, so that it can be consulted again regardless of whether its source
-  -- supports only a single traversal. `oneShot` is therefore never consulted.
-  let shared := folds
+  -- WRONG (prepatch): consult the source directly inside each evaluation; a
+  -- single-traversal source drains after the first read.
+  let mut remaining := folds
   let mut observed : List (List Nat) := []
   for _ in [0:numEvals] do
-    observed := observed ++ [shared]
+    observed := observed ++ [remaining]
+    if oneShot then
+      remaining := []
   return observed
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,11 +49,9 @@
 -- impl-start
 def implementation_repeatedEvaluations
     (folds : List Nat) (oneShot : Bool) (numEvals : Nat) : List (List Nat) := Id.run do
-  -- Capture the collection into a reusable value once, before any evaluation
-  -- runs, so that it can be consulted again regardless of whether its source
-  -- supports only a single traversal. `oneShot` is therefore never consulted.
+  -- WRONG (boundary): emit one extra observation beyond numEvals.
   let shared := folds
-  let mut observed : List (List Nat) := []
+  let mut observed : List (List Nat) := [shared]
   for _ in [0:numEvals] do
     observed := observed ++ [shared]
   return observed
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,14 +49,11 @@
 -- impl-start
 def implementation_repeatedEvaluations
     (folds : List Nat) (oneShot : Bool) (numEvals : Nat) : List (List Nat) := Id.run do
-  -- Capture the collection into a reusable value once, before any evaluation
-  -- runs, so that it can be consulted again regardless of whether its source
-  -- supports only a single traversal. `oneShot` is therefore never consulted.
-  let shared := folds
-  let mut observed : List (List Nat) := []
-  for _ in [0:numEvals] do
-    observed := observed ++ [shared]
-  return observed
+  -- WRONG (partial-domain): never observe anything; result always empty.
+  let _ := folds
+  let _ := oneShot
+  let _ := numEvals
+  return []
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,13 +49,11 @@
 -- impl-start
 def implementation_repeatedEvaluations
     (folds : List Nat) (oneShot : Bool) (numEvals : Nat) : List (List Nat) := Id.run do
-  -- Capture the collection into a reusable value once, before any evaluation
-  -- runs, so that it can be consulted again regardless of whether its source
-  -- supports only a single traversal. `oneShot` is therefore never consulted.
-  let shared := folds
+  -- WRONG (content): correct count, but each observation is empty, not folds.
+  let _ := folds
   let mut observed : List (List Nat) := []
   for _ in [0:numEvals] do
-    observed := observed ++ [shared]
+    observed := observed ++ [[]]
   return observed
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,13 +49,13 @@
 -- impl-start
 def implementation_repeatedEvaluations
     (folds : List Nat) (oneShot : Bool) (numEvals : Nat) : List (List Nat) := Id.run do
-  -- Capture the collection into a reusable value once, before any evaluation
-  -- runs, so that it can be consulted again regardless of whether its source
-  -- supports only a single traversal. `oneShot` is therefore never consulted.
-  let shared := folds
+  -- WRONG (control-flow): first evaluation sees folds, all later ones see empty.
+  let _ := oneShot
+  let mut remaining := folds
   let mut observed : List (List Nat) := []
   for _ in [0:numEvals] do
-    observed := observed ++ [shared]
+    observed := observed ++ [remaining]
+    remaining := []
   return observed
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -48,15 +48,10 @@
 
 -- impl-start
 def implementation_repeatedEvaluations
-    (folds : List Nat) (oneShot : Bool) (numEvals : Nat) : List (List Nat) := Id.run do
-  -- Capture the collection into a reusable value once, before any evaluation
-  -- runs, so that it can be consulted again regardless of whether its source
-  -- supports only a single traversal. `oneShot` is therefore never consulted.
-  let shared := folds
-  let mut observed : List (List Nat) := []
-  for _ in [0:numEvals] do
-    observed := observed ++ [shared]
-  return observed
+    (folds : List Nat) (oneShot : Bool) (numEvals : Nat) : List (List Nat) :=
+  -- Equivalent echo: directly build numEvals copies of the complete collection.
+  let _ := oneShot
+  List.replicate numEvals folds
 -- impl-end
 
 -- proof-start
@@ -65,35 +60,7 @@
       problem_spec_repeatedEvaluations folds oneShot numEvals
         (implementation_repeatedEvaluations folds oneShot numEvals) := by
   intro folds oneShot numEvals
-  -- Helper: the desugared loop body, generalized over the accumulator, just
-  -- appends one copy of `folds` per iteration, i.e. `replicate length folds`.
-  have helper : ∀ (xs : List Nat) (acc : List (List Nat)),
-      (forIn xs acc (fun _ r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [folds]))) : Id _)
-        = acc ++ List.replicate xs.length folds := by
-    intro xs
-    induction xs with
-    | nil => intro acc; show acc = acc ++ List.replicate 0 folds; simp
-    | cons a as ih =>
-      intro acc
-      rw [List.forIn_cons]
-      show (forIn as (acc ++ [folds]) _ : Id _) = _
-      rw [ih]
-      simp [List.replicate_succ, List.append_assoc]
-  -- The implementation reduces to `List.replicate numEvals folds`.
-  have key : implementation_repeatedEvaluations folds oneShot numEvals
-      = List.replicate numEvals folds := by
-    unfold implementation_repeatedEvaluations
-    simp only [Id.run, Std.Range.forIn_eq_forIn_range']
-    rw [show (do
-        let r ← forIn (List.range' 0 [:numEvals].size) [] fun _ r => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [folds]))
-        pure r : Id (List (List Nat))) = forIn (List.range' 0 [:numEvals].size) [] fun _ r => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [folds])) from rfl]
-    rw [helper]
-    simp [Std.Range.size]
-  rw [problem_spec_repeatedEvaluations, key]
+  unfold problem_spec_repeatedEvaluations implementation_repeatedEvaluations
   refine ⟨by simp, ?_⟩
   intro s hs
   exact List.eq_of_mem_replicate hs
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,10 +49,9 @@
 -- impl-start
 def implementation_repeatedEvaluations
     (folds : List Nat) (oneShot : Bool) (numEvals : Nat) : List (List Nat) := Id.run do
-  -- Capture the collection into a reusable value once, before any evaluation
-  -- runs, so that it can be consulted again regardless of whether its source
-  -- supports only a single traversal. `oneShot` is therefore never consulted.
-  let shared := folds
+  -- WRONG (content): each observation is the collection doubled, not the collection.
+  let _ := oneShot
+  let shared := folds ++ folds
   let mut observed : List (List Nat) := []
   for _ in [0:numEvals] do
     observed := observed ++ [shared]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
A routine that performs a preset number of independent evaluations, where every
evaluation must consult the SAME shared collection of items.

The collection is supplied by a source. That source may only support being read
once (`oneShot = true`): after a single traversal it yields nothing further. A
source that can be read repeatedly (`oneShot = false`) returns the whole
collection every time it is consulted.

Required behaviour: every one of the `numEvals` evaluations observes the
COMPLETE collection — even when the source is single-traversal. The number of
evaluations is otherwise unconstrained, and the result must contain exactly one
observation per evaluation.

Modeled with the collection as `List Nat`, a boolean recording whether the
source is single-traversal, and the evaluation count as `Nat`. The result is the
sequence of collections actually observed, one per evaluation, in order.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the collection contents are taken
-- as the input `folds`, and the obligation to make every evaluation observe the
-- complete collection is modeled deeply (the result is pinned element-wise).
-- axioms-end

-- pure-start
-- No additional pure helpers are needed: the modeled behaviour is a direct
-- relation between the inputs and the observed-collection sequence.
-- pure-end

-- post-conditions-start
/-- Specification of the repeated-evaluation routine.

* The result records exactly one observation per evaluation (`length = numEvals`).
* Every observation is the COMPLETE collection `folds`.

The single-traversal flag `oneShot` does NOT appear on the right-hand side: the
observed collections are independent of it — a single-traversal source must be
handled so that no observation is ever short. -/
def problem_spec_repeatedEvaluations
    (folds : List Nat) (oneShot : Bool) (numEvals : Nat)
    (result : List (List Nat)) : Prop :=
  result.length = numEvals ∧ (∀ s ∈ result, s = folds)
-- post-conditions-end

-- impl-start
def implementation_repeatedEvaluations
    (folds : List Nat) (oneShot : Bool) (numEvals : Nat) : List (List Nat) := Id.run do
  -- Capture the collection into a reusable value once, before any evaluation
  -- runs, so that it can be consulted again regardless of whether its source
  -- supports only a single traversal. `oneShot` is therefore never consulted.
  let shared := folds
  let mut observed : List (List Nat) := []
  for _ in [0:numEvals] do
    observed := observed ++ [shared]
  return observed
-- impl-end

-- proof-start
theorem correct_repeatedEvaluations :
    ∀ (folds : List Nat) (oneShot : Bool) (numEvals : Nat),
      problem_spec_repeatedEvaluations folds oneShot numEvals
        (implementation_repeatedEvaluations folds oneShot numEvals) := by
  intro folds oneShot numEvals
  -- Helper: the desugared loop body, generalized over the accumulator, just
  -- appends one copy of `folds` per iteration, i.e. `replicate length folds`.
  have helper : ∀ (xs : List Nat) (acc : List (List Nat)),
      (forIn xs acc (fun _ r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [folds]))) : Id _)
        = acc ++ List.replicate xs.length folds := by
    intro xs
    induction xs with
    | nil => intro acc; show acc = acc ++ List.replicate 0 folds; simp
    | cons a as ih =>
      intro acc
      rw [List.forIn_cons]
      show (forIn as (acc ++ [folds]) _ : Id _) = _
      rw [ih]
      simp [List.replicate_succ, List.append_assoc]
  -- The implementation reduces to `List.replicate numEvals folds`.
  have key : implementation_repeatedEvaluations folds oneShot numEvals
      = List.replicate numEvals folds := by
    unfold implementation_repeatedEvaluations
    simp only [Id.run, Std.Range.forIn_eq_forIn_range']
    rw [show (do
        let r ← forIn (List.range' 0 [:numEvals].size) [] fun _ r => do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [folds]))
        pure r : Id (List (List Nat))) = forIn (List.range' 0 [:numEvals].size) [] fun _ r => do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [folds])) from rfl]
    rw [helper]
    simp [Std.Range.size]
  rw [problem_spec_repeatedEvaluations, key]
  refine ⟨by simp, ?_⟩
  intro s hs
  exact List.eq_of_mem_replicate hs
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT OF scikit-learn__scikit-learn-25973 (lean). All 7 attacks confirmed same_spec=True against Solution.lean via swebench_unified.markers.same_spec (impl region edited only; axioms/pure/pre/post byte-identical).

SPEC SHAPE: problem_spec_repeatedEvaluations := result.length = numEvals AND (forall s in result, s = folds). The two conjuncts TOGETHER uniquely pin result = List.replicate numEvals folds — a fully-determined deep model. refinement.md: 4 rows, ALL tagged R, none kind-3; axiom_check.py is a genuine skip stub (no consumed axioms / deep_model_references empty), so there are NO A-legs to break — the correspondence audit reduces to: does the deep model correspond to the real check_cv/_CVIterableWrapper reuse behaviour (it does; mapping.md + conformance_check.py drive the real callee). Concentrated attack effort on trying to close the proof with a behaviorally-wrong impl.

COMMANDS (from project root): verify = `bash scripts/lean_verify.sh <file>` (run concurrently, <=4 at a time as background jobs). same_spec = swebench_unified.markers.same_spec via get_backend('lean').

### Results
- positive_control.lean (gold impl): exit 0 (verifies). 
- atk_1 (prepatch bug: source consulted directly each eval, drains when oneShot; PREPATCH REPRODUCED): exit 1 — cannot close (goal reduces to a term != List.replicate numEvals folds). Behaviorally wrong: oneShot=true,numEvals=2,folds=[a] yields [[a],[]].
- atk_2 (boundary / off-by-one: emits numEvals+1 observations): exit 1 — cannot close (length mismatch).
- atk_3 (partial-domain: result always []): exit 1 — cannot close (wrong for numEvals>0).
- atk_4 (ungrounded-oracle echo: correct count but each observation = [] not folds): exit 1 — cannot close (content mismatch).
- atk_5 (control-flow-effect: first eval sees folds, all later see []): exit 1 — cannot close.
- atk_7 (wrong content: each observation = folds++folds): exit 1 — cannot close.
- atk_6 (SPEC-EQUIVALENT ECHO: implementation := List.replicate numEvals folds, oneShot ignored; proof rewritten to close): exit 0. #print axioms correct_repeatedEvaluations => 'depends on axioms: [propext]' (clean; no sorry, no sorryAx, no Classical.choice/Quot). This is the ONLY closing candidate.

STEP-2 RESOLVE (mandatory for every clean-axiom closing candidate): atk_6 is behaviorally identical to gold (capture the collection once, reuse it for every evaluation, ignore oneShot). Its FAITHFUL refined patch is therefore the gold fix (check_cv materialization + threading cv through _get_best_new_feature_score). Materialized as atk_6_faithful.patch and executed: `run_resolve('scikit-learn__scikit-learn-25973', patch, run_id='sbu-audit-atk6')` (Docker harness, python). RESULT: ResolveResult(resolved=True, completed=True, note='resolved', attempts=1, flaky=False). FAIL_TO_PASS test_cv_generator_support => success; all 73 PASS_TO_PASS => success; 0 failures. So the ONLY verify-closing candidate also RESOLVES => verify => correct holds; no verify-does-not-imply-correct break exists.

CONCLUSION: Every behaviorally-distinct wrong impl (6 classes: prepatch, boundary, partial-domain, ungrounded content, control-flow, doubled-content) FAILS to close the proof — the spec is tight enough to reject all of them. The single impl that closes is spec-equivalent to gold and its faithful patch RESOLVES. VERDICT: SOUND. (7 attacks run, prepatch reproduced, positive control verifies, required resolve executed and passed.)

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-1: 7 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — re-derived at a higher verifier cap after the original run's verifier timed out)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
A routine that performs a preset number of independent evaluations, where every
evaluation must consult the SAME shared collection of items.

The collection is supplied by a source. That source may only support being read
once (`oneShot = true`): after a single traversal it yields nothing further. A
source that can be read repeatedly (`oneShot = false`) returns the whole
collection every time it is consulted.

Required behaviour: every one of the `numEvals` evaluations observes the
COMPLETE collection — even when the source is single-traversal. The number of
evaluations is otherwise unconstrained, and the result must contain exactly one
observation per evaluation.

Modeled with the collection as `List Nat`, a boolean recording whether the
source is single-traversal, and the evaluation count as `Nat`. The result is the
sequence of collections actually observed, one per evaluation, in order.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the collection contents are taken
-- as the input `folds`, and the obligation to make every evaluation observe the
-- complete collection is modeled deeply (the result is pinned element-wise).
-- axioms-end

-- pure-start
-- No additional pure helpers are needed: the modeled behaviour is a direct
-- relation between the inputs and the observed-collection sequence.
-- pure-end

-- post-conditions-start
/-- Specification of the repeated-evaluation routine.

* The result records exactly one observation per evaluation (`length = numEvals`).
* Every observation is the COMPLETE collection `folds`.

The single-traversal flag `oneShot` does NOT appear on the right-hand side: the
observed collections are independent of it — a single-traversal source must be
handled so that no observation is ever short. -/
def problem_spec_repeatedEvaluations
    (folds : List Nat) (oneShot : Bool) (numEvals : Nat)
    (result : List (List Nat)) : Prop :=
  result.length = numEvals ∧ (∀ s ∈ result, s = folds)
-- post-conditions-end

-- impl-start
def implementation_repeatedEvaluations
    (folds : List Nat) (oneShot : Bool) (numEvals : Nat) : List (List Nat) := Id.run do
  -- Capture the collection into a reusable value once, before any evaluation
  -- runs, so that it can be consulted again regardless of whether its source
  -- supports only a single traversal. `oneShot` is therefore never consulted.
  let shared := folds
  let mut observed : List (List Nat) := []
  for _ in [0:numEvals] do
    observed := observed ++ [shared]
  return observed
-- impl-end

-- proof-start
theorem correct_repeatedEvaluations :
    ∀ (folds : List Nat) (oneShot : Bool) (numEvals : Nat),
      problem_spec_repeatedEvaluations folds oneShot numEvals
        (implementation_repeatedEvaluations folds oneShot numEvals) := by
  intro folds oneShot numEvals
  -- Helper: the desugared loop body, generalized over the accumulator, just
  -- appends one copy of `folds` per iteration, i.e. `replicate length folds`.
  have helper : ∀ (xs : List Nat) (acc : List (List Nat)),
      (forIn xs acc (fun _ r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [folds]))) : Id _)
        = acc ++ List.replicate xs.length folds := by
    intro xs
    induction xs with
    | nil => intro acc; show acc = acc ++ List.replicate 0 folds; simp
    | cons a as ih =>
      intro acc
      rw [List.forIn_cons]
      show (forIn as (acc ++ [folds]) _ : Id _) = _
      rw [ih]
      simp [List.replicate_succ, List.append_assoc]
  -- The implementation reduces to `List.replicate numEvals folds`.
  have key : implementation_repeatedEvaluations folds oneShot numEvals
      = List.replicate numEvals folds := by
    unfold implementation_repeatedEvaluations
    simp only [Id.run, Std.Range.forIn_eq_forIn_range']
    rw [show (do
        let r ← forIn (List.range' 0 [:numEvals].size) [] fun _ r => do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [folds]))
        pure r : Id (List (List Nat))) = forIn (List.range' 0 [:numEvals].size) [] fun _ r => do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [folds])) from rfl]
    rw [helper]
    simp [Std.Range.size]
  rw [problem_spec_repeatedEvaluations, key]
  refine ⟨by simp, ?_⟩
  intro s hs
  exact List.eq_of_mem_replicate hs
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT OF scikit-learn__scikit-learn-25973 (lean). All 7 attacks confirmed same_spec=True against Solution.lean via swebench_unified.markers.same_spec (impl region edited only; axioms/pure/pre/post byte-identical).

SPEC SHAPE: problem_spec_repeatedEvaluations := result.length = numEvals AND (forall s in result, s = folds). The two conjuncts TOGETHER uniquely pin result = List.replicate numEvals folds — a fully-determined deep model. refinement.md: 4 rows, ALL tagged R, none kind-3; axiom_check.py is a genuine skip stub (no consumed axioms / deep_model_references empty), so there are NO A-legs to break — the correspondence audit reduces to: does the deep model correspond to the real check_cv/_CVIterableWrapper reuse behaviour (it does; mapping.md + conformance_check.py drive the real callee). Concentrated attack effort on trying to close the proof with a behaviorally-wrong impl.

COMMANDS (from project root): verify = `bash scripts/lean_verify.sh <file>` (run concurrently, <=4 at a time as background jobs). same_spec = swebench_unified.markers.same_spec via get_backend('lean').

### Results
- positive_control.lean (gold impl): exit 0 (verifies). 
- atk_1 (prepatch bug: source consulted directly each eval, drains when oneShot; PREPATCH REPRODUCED): exit 1 — cannot close (goal reduces to a term != List.replicate numEvals folds). Behaviorally wrong: oneShot=true,numEvals=2,folds=[a] yields [[a],[]].
- atk_2 (boundary / off-by-one: emits numEvals+1 observations): exit 1 — cannot close (length mismatch).
- atk_3 (partial-domain: result always []): exit 1 — cannot close (wrong for numEvals>0).
- atk_4 (ungrounded-oracle echo: correct count but each observation = [] not folds): exit 1 — cannot close (content mismatch).
- atk_5 (control-flow-effect: first eval sees folds, all later see []): exit 1 — cannot close.
- atk_7 (wrong content: each observation = folds++folds): exit 1 — cannot close.
- atk_6 (SPEC-EQUIVALENT ECHO: implementation := List.replicate numEvals folds, oneShot ignored; proof rewritten to close): exit 0. #print axioms correct_repeatedEvaluations => 'depends on axioms: [propext]' (clean; no sorry, no sorryAx, no Classical.choice/Quot). This is the ONLY closing candidate.

STEP-2 RESOLVE (mandatory for every clean-axiom closing candidate): atk_6 is behaviorally identical to gold (capture the collection once, reuse it for every evaluation, ignore oneShot). Its FAITHFUL refined patch is therefore the gold fix (check_cv materialization + threading cv through _get_best_new_feature_score). Materialized as atk_6_faithful.patch and executed: `run_resolve('scikit-learn__scikit-learn-25973', patch, run_id='sbu-audit-atk6')` (Docker harness, python). RESULT: ResolveResult(resolved=True, completed=True, note='resolved', attempts=1, flaky=False). FAIL_TO_PASS test_cv_generator_support => success; all 73 PASS_TO_PASS => success; 0 failures. So the ONLY verify-closing candidate also RESOLVES => verify => correct holds; no verify-does-not-imply-correct break exists.

CONCLUSION: Every behaviorally-distinct wrong impl (6 classes: prepatch, boundary, partial-domain, ungrounded content, control-flow, doubled-content) FAILS to close the proof — the spec is tight enough to reject all of them. The single impl that closes is spec-equivalent to gold and its faithful patch RESOLVES. VERDICT: SOUND. (7 attacks run, prepatch reproduced, positive control verifies, required resolve executed and passed.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break assessment for scikit-learn__scikit-learn-25973 (lean). SPEC: problem_spec_repeatedEvaluations folds oneShot numEvals result := result.length = numEvals ∧ (∀ s ∈ result, s = folds). oneShot deliberately absent from RHS.

Byte-identity: swebench_unified.markers.same_spec(post, prepatch, lean-backend) = True — spec/contract region is byte-identical; only impl+proof differ (correct).

Proof genuine: lean_verify.sh exit 0; #print axioms correct_repeatedEvaluations = [propext, Classical.choice, Quot.sound] — no sorryAx.

Faithfulness to real repo: real callee is check_cv → _CVIterableWrapper.__init__ (self.cv = list(cv), materialize once) with .split() re-yielding every call (sklearn/model_selection/_split.py:2353-2470, base_commit 10dbc142). The fix threads this reusable cv into every cross_val_score, so every evaluation observes the COMPLETE split set regardless of source traversal-nature — exactly what the spec models (oneShot has no effect on result). shadow (R/I transliteration of the impl) matches the real check_cv oracle:
  - pinned G-CONF (100k inputs, seed 25973): 0 disagreements.
  - my broadened independent probe (200k inputs, folds len 0-20 / tokens 0-1000 / numEvals 0-30, + edge cases []/singleton/repeated/oneShot both): 0 disagreements.

Non-vacuity: prepatch buggy impl yields [[7],[]] for oneShot=True, folds=[7], numEvals=2, violating (∀ s ∈ result, s = folds) — the reported IndexError; spec correctly rejects it.

No input found where the modeled function disagrees with the real repo callee. Spec is neither too strong nor drifting. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (imports + docstring + axioms/pure comment stubs + post-conditions `problem_spec_repeatedEvaluations`; impl and proof elided) is fully abstracted. Mechanical leakage.screen() passes with zero hard_failures; same_spec(Solution, Solution_prepatch)=True. No repo symbols (check_cv, SequentialFeatureSelector, cv, cross_val_score, _CVIterableWrapper, list(cv)), no patched file path (_sequential.py), no gold-patch line, no diff markers, no narration terms appear in the spec view. The spec encodes only the abstract correctness property: a single-traversal source (oneShot) must be captured once so every one of numEvals evaluations observes the complete `folds` collection (result.length = numEvals ∧ ∀ s ∈ result, s = folds). This is the legitimate behavioral specification, not the gold edit — it does not localize WHERE/HOW to fix nor reconstruct the materialize-once-via-check_cv change. The public problem_statement already discloses that passing an iterable/generator of splits fails with IndexError and should run without error, so the reuse-required behavior is already public; the spec adds no edit-localizing information beyond it. Repo-specific mapping (check_cv/list(cv)) resides only in mapping.md/refinement.md, which are not part of the screened spec view. No RELAXED_LEAKAGE deferral needed since the screen passes outright.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
