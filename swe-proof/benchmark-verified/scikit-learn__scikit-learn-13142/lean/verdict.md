# P2 adversarial audit — scikit-learn__scikit-learn-13142

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8b.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition fully pins the reachable domain: for trials ≠ [] (the theorem hypothesis, faithfully mirroring sklearn's enforced n_init ≥ 1 via _check_initial_parameters raising ValueError when n_init < 1), bestParam trials = some b, so clause 1 forces result = labelsOf b EXACTLY. Since labelsOf is `opaque` with NO axioms (A-reference, signature-only), labelsOf b' = labelsOf b is unprovable for b' ≠ b — hence any verifying impl must select the earliest highest-scoring config and return its labels, i.e. be behaviorally identical to gold on the whole tested domain.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,13 +49,15 @@
 -- impl-start
 def implementation_fit_predict (trials : List (Int × Int)) : List Nat := Id.run do
   let mut best : Option (Int × Int) := none
+  let mut lastConfig : Option Int := none
   for t in trials do
+    lastConfig := some t.1
     match best with
     | none => best := some t
     | some (_, bs) => if t.2 > bs then best := some t
-  match best with
+  match lastConfig with
   | none => return []
-  | some (bp, _) => return labelsOf bp
+  | some lc => return labelsOf lc
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,7 +52,7 @@
   for t in trials do
     match best with
     | none => best := some t
-    | some (_, bs) => if t.2 > bs then best := some t
+    | some (_, bs) => if t.2 >= bs then best := some t
   match best with
   | none => return []
   | some (bp, _) => return labelsOf bp
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,14 +48,7 @@
 
 -- impl-start
 def implementation_fit_predict (trials : List (Int × Int)) : List Nat := Id.run do
-  let mut best : Option (Int × Int) := none
-  for t in trials do
-    match best with
-    | none => best := some t
-    | some (_, bs) => if t.2 > bs then best := some t
-  match best with
-  | none => return []
-  | some (bp, _) => return labelsOf bp
+  return []
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,14 +48,9 @@
 
 -- impl-start
 def implementation_fit_predict (trials : List (Int × Int)) : List Nat := Id.run do
-  let mut best : Option (Int × Int) := none
-  for t in trials do
-    match best with
-    | none => best := some t
-    | some (_, bs) => if t.2 > bs then best := some t
-  match best with
-  | none => return []
-  | some (bp, _) => return labelsOf bp
+  match trials with
+  | [t] => return labelsOf t.1
+  | _ => return []
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,7 +52,7 @@
   for t in trials do
     match best with
     | none => best := some t
-    | some (_, bs) => if t.2 > bs then best := some t
+    | some (_, bs) => if t.2 < bs then best := some t
   match best with
   | none => return []
   | some (bp, _) => return labelsOf bp
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,14 +48,9 @@
 
 -- impl-start
 def implementation_fit_predict (trials : List (Int × Int)) : List Nat := Id.run do
-  let mut best : Option (Int × Int) := none
-  for t in trials do
-    match best with
-    | none => best := some t
-    | some (_, bs) => if t.2 > bs then best := some t
-  match best with
-  | none => return []
-  | some (bp, _) => return labelsOf bp
+  match trials with
+  | [] => return []
+  | t :: _ => return labelsOf t.1
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,7 @@
     | some (_, bs) => if t.2 > bs then best := some t
   match best with
   | none => return []
-  | some (bp, _) => return labelsOf bp
+  | some (bp, _) => return (labelsOf bp) ++ [0]
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,7 +54,7 @@
     | none => best := some t
     | some (_, bs) => if t.2 > bs then best := some t
   match best with
-  | none => return []
+  | none => return [7]
   | some (bp, _) => return labelsOf bp
 -- impl-end
 
```

Attack 9 — `atk_8b.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -54,13 +54,12 @@
     | none => best := some t
     | some (_, bs) => if t.2 > bs then best := some t
   match best with
-  | none => return []
+  | none => return [7]
   | some (bp, _) => return labelsOf bp
 -- impl-end
 
 -- proof-start
-/-- The desugared `forIn` loop body equals folding `stepBest` over the trials,
-generalized over the accumulator. -/
+/-- Same loop_helper as gold. -/
 theorem loop_helper (trials : List (Int × Int)) (init : Option (Int × Int)) :
     (forIn (m := Id) trials init (fun t r =>
       match r with
@@ -78,13 +77,27 @@
       obtain ⟨bp, bs⟩ := p
       by_cases h : a.2 > bs <;> simp only [h, if_true, if_false, ih, List.foldl_cons, stepBest]
 
+/-- Folding stepBest from a `some` seed never yields `none`. -/
+theorem foldl_some (l : List (Int × Int)) (x : Int × Int) :
+    l.foldl stepBest (some x) ≠ none := by
+  induction l generalizing x with
+  | nil => simp
+  | cons a as ih =>
+    simp only [List.foldl_cons, stepBest]
+    by_cases h : a.2 > x.2 <;> simp only [h, if_true, if_false] <;> apply ih
+
 theorem correct_fit_predict :
     ∀ trials : List (Int × Int), trials ≠ [] →
       problem_spec_fit_predict trials (implementation_fit_predict trials) := by
-  intro trials _
+  intro trials hne
   unfold implementation_fit_predict
   simp only [Id.run, bind]
   rw [loop_helper trials none]
+  -- non-empty ⇒ fold is `some`
+  have hsome : trials.foldl stepBest none ≠ none := by
+    cases trials with
+    | nil => exact absurd rfl hne
+    | cons a as => simp only [List.foldl_cons, stepBest]; exact foldl_some as a
   constructor
   · intro b hb
     unfold bestParam at hb
@@ -94,7 +107,7 @@
   · intro hb
     unfold bestParam at hb
     cases hf : trials.foldl stepBest none with
-    | none => rfl
+    | none => exact absurd hf hsome
     | some p => rw [hf] at hb; simp at hb
 -- proof-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Model of an estimator that performs several independent fitting trials and then
assigns labels to the data. Each trial yields a candidate parameter
configuration together with a numeric quality score; the procedure keeps the
configuration of the highest-scoring trial and must report the label assignment
that this selected configuration produces.

A trial is modeled as `(config, score)` where `config : Int` identifies a fitted
parameter configuration and `score : Int` is the (order-only) quality score.
Real-valued scores are modeled as `Int` because only their ORDER matters for the
selection (DECISIONS.md: kernel `Float` order is opaque to tactics).
-/

-- axioms-start
/-- The label assignment produced for a given parameter configuration. This is
the unchanged downstream label-computation callee; we need only that it is a
deterministic function of the configuration it is applied to (no property is
consumed by the proof, so it is declared `opaque` with no `_prop` axiom). -/
opaque labelsOf : Int → List Nat
-- axioms-end

-- pure-start
/-- Fold step selecting the best trial seen so far. Keeps the running best
unless the incoming trial's score is STRICTLY greater (so the earliest trial
attaining the maximum score wins ties). -/
def stepBest (acc : Option (Int × Int)) (t : Int × Int) : Option (Int × Int) :=
  match acc with
  | none => some t
  | some (bp, bs) => if t.2 > bs then some t else some (bp, bs)

/-- The configuration of the highest-scoring trial (earliest on ties), or `none`
when there are no trials. -/
def bestParam (trials : List (Int × Int)) : Option Int :=
  (trials.foldl stepBest none).map (·.1)
-- pure-end

-- post-conditions-start
/-- The reported labels are exactly those produced by the SELECTED (highest
scoring) trial's configuration; with no trials the result is empty. Both output
branches are pinned (frame discipline: no result component left free). -/
def problem_spec_fit_predict (trials : List (Int × Int)) (result : List Nat) : Prop :=
  (∀ b, bestParam trials = some b → result = labelsOf b) ∧
  (bestParam trials = none → result = [])
-- post-conditions-end

-- impl-start
def implementation_fit_predict (trials : List (Int × Int)) : List Nat := Id.run do
  let mut best : Option (Int × Int) := none
  for t in trials do
    match best with
    | none => best := some t
    | some (_, bs) => if t.2 > bs then best := some t
  match best with
  | none => return []
  | some (bp, _) => return labelsOf bp
-- impl-end

-- proof-start
/-- The desugared `forIn` loop body equals folding `stepBest` over the trials,
generalized over the accumulator. -/
theorem loop_helper (trials : List (Int × Int)) (init : Option (Int × Int)) :
    (forIn (m := Id) trials init (fun t r =>
      match r with
      | none => pure (ForInStep.yield (some t))
      | some (_, bs) => if t.2 > bs then pure (ForInStep.yield (some t)) else pure (ForInStep.yield r)))
    = trials.foldl stepBest init := by
  induction trials generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind] at ih ⊢
    cases init with
    | none => simp only [ih, List.foldl_cons, stepBest]
    | some p =>
      obtain ⟨bp, bs⟩ := p
      by_cases h : a.2 > bs <;> simp only [h, if_true, if_false, ih, List.foldl_cons, stepBest]

theorem correct_fit_predict :
    ∀ trials : List (Int × Int), trials ≠ [] →
      problem_spec_fit_predict trials (implementation_fit_predict trials) := by
  intro trials _
  unfold implementation_fit_predict
  simp only [Id.run, bind]
  rw [loop_helper trials none]
  constructor
  · intro b hb
    unfold bestParam at hb
    cases hf : trials.foldl stepBest none with
    | none => rw [hf] at hb; simp at hb
    | some p => rw [hf] at hb; obtain ⟨bp, bs⟩ := p; simp at hb; simp only [hb]; rfl
  · intro hb
    unfold bestParam at hb
    cases hf : trials.foldl stepBest none with
    | none => rfl
    | some p => rw [hf] at hb; simp at hb
-- proof-end

#print axioms correct_fit_predict
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL COMPLETE. Same-spec confirmed True for all 9 files via swebench_unified.markers.same_spec (lean). Verify tool = scripts/lean_verify.sh <file>.

### VERIFY RESULTS (exit 0 = closes clean):
- positive_control (exact gold impl): exit 0, axioms [propext, Quot.sound] CLEAN. Faithful gold patch RESOLVES (report resolved:true; F2P test_gaussian_mixture_fit_predict_n_init + test_bayesian_mixture_fit_predict_n_init pass, all P2P pass). Harness validated end-to-end.
- atk_1 (PREPATCH BUG: return labelsOf lastConfig): exit 1, sorryAx — spec CATCHES the prepatch bug (gold proof cannot close; loop_helper mismatch on lastConfig). prepatch_reproduced=true.
- atk_2 (>= tie-break, last-wins): exit 1 sorryAx.
- atk_3 (ungrounded-oracle echo: always []): exit 1 sorryAx.
- atk_4 (partial-domain: correct only for singleton lists, else []): exit 1 sorryAx.
- atk_5 (boundary: select MIN score, t.2 < bs): exit 1 sorryAx.
- atk_6 (control-flow: return labelsOf of FIRST config): exit 1 sorryAx.
- atk_7 (output-mutation: correct best ++ spurious [0]): exit 1 sorryAx.
- atk_8 ([7] on empty, reusing GOLD proof): exit 1 sorryAx (gold proof pins empty-branch = []).
- atk_8b ([7] on empty, correct on non-empty, with a TAILORED closing proof using the trials ≠ [] hypothesis + a foldl_some lemma): exit 0, axioms [propext, Quot.sound] CLEAN.

MANDATORY RESOLVE STEP (protocol 2): atk_8b is the ONLY non-gold impl that closes with clean axioms. I materialized its FAITHFUL refined patch (gold reorder PLUS an n_init==0 empty-domain sentinel branch returning np.full(n_samples,7)) and ran it through the official harness via swebench_unified.harness.run_resolve / run_evaluation under `docker`. RESULT: resolved=True, patch_successfully_applied=True, both FAIL_TO_PASS pass, zero PASS_TO_PASS failures. Report saved 

WHY atk_8b resolving is EXPECTED (not a break): its ONLY divergence from gold is the empty-trials case (Lean) = n_init==0 (Python), which is UNREACHABLE — sklearn/mixture/base.py:102 _check_initial_parameters raises ValueError when n_init < 1, and do_init=False forces n_init=1. The theorem's `trials ≠ []` hypothesis faithfully mirrors this invariant. On the reachable domain atk_8b is byte-equivalent to gold, so it resolves. This is legitimate empty-domain slack, not verify⇏correct.

HARNESS NOTE: severe board contention (load ~125, 17-229 docker images churning from concurrent django/matplotlib concurrent runs resolves) caused swebench run_evaluation to fail intermittently in its startup client.images.list(all=True) with docker.errors.ImageNotFound (an image removed mid-enumeration). This hit GOLD and atk_8b identically (contention artifact, NOT a real non-resolve). A bounded retry loop (up to 15 attempts) slipped through the race window on attempt 1 for both once the churn eased; both then produced valid reports.

REFINEMENT.MD AUDIT: 4 legs, all valid kinds. Leg1 (-np.infty seed ↔ none): R. Leg2 (fitted trial ↔ (config,score)): R. Leg3 (strict > earliest-tie control flow): I. Leg4 (labelsOf bp ↔ final e-step+argmax under SELECTED config): A-reference — labelsOf is opaque, UNCHANGED by the patch (pure reordering), proof consumes NO _prop axiom (correctness is purely about WHICH config labelsOf is applied to). No kind-3 (changed-inexpressible) legs. A-reference correspondence to the real composite callee ("run final _e_step(X) under current params, then log_resp.argmax(axis=1)") holds. mapping.md callee provenance and n_init>1 observability analysis consistent.

VERDICT: SOUND. ≥5 distinct same-spec wrong impls run; every impl whose proof closes with clean axioms (only atk_8b) has a materialized faithful patch that RESOLVES; the prepatch bug is caught; A-legs audited. No verify⇏correct gap found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8b.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition fully pins the reachable domain: for trials ≠ [] (the theorem hypothesis, faithfully mirroring sklearn's enforced n_init ≥ 1 via _check_initial_parameters raising ValueError when n_init < 1), bestParam trials = some b, so clause 1 forces result = labelsOf b EXACTLY. Since labelsOf is `opaque` with NO axioms (A-reference, signature-only), labelsOf b' = labelsOf b is unprovable for b' ≠ b — hence any verifying impl must select the earliest highest-scoring config and return its labels, i.e. be behaviorally identical to gold on the whole tested domain.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_8b.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Model of an estimator that performs several independent fitting trials and then
assigns labels to the data. Each trial yields a candidate parameter
configuration together with a numeric quality score; the procedure keeps the
configuration of the highest-scoring trial and must report the label assignment
that this selected configuration produces.

A trial is modeled as `(config, score)` where `config : Int` identifies a fitted
parameter configuration and `score : Int` is the (order-only) quality score.
Real-valued scores are modeled as `Int` because only their ORDER matters for the
selection (DECISIONS.md: kernel `Float` order is opaque to tactics).
-/

-- axioms-start
/-- The label assignment produced for a given parameter configuration. This is
the unchanged downstream label-computation callee; we need only that it is a
deterministic function of the configuration it is applied to (no property is
consumed by the proof, so it is declared `opaque` with no `_prop` axiom). -/
opaque labelsOf : Int → List Nat
-- axioms-end

-- pure-start
/-- Fold step selecting the best trial seen so far. Keeps the running best
unless the incoming trial's score is STRICTLY greater (so the earliest trial
attaining the maximum score wins ties). -/
def stepBest (acc : Option (Int × Int)) (t : Int × Int) : Option (Int × Int) :=
  match acc with
  | none => some t
  | some (bp, bs) => if t.2 > bs then some t else some (bp, bs)

/-- The configuration of the highest-scoring trial (earliest on ties), or `none`
when there are no trials. -/
def bestParam (trials : List (Int × Int)) : Option Int :=
  (trials.foldl stepBest none).map (·.1)
-- pure-end

-- post-conditions-start
/-- The reported labels are exactly those produced by the SELECTED (highest
scoring) trial's configuration; with no trials the result is empty. Both output
branches are pinned (frame discipline: no result component left free). -/
def problem_spec_fit_predict (trials : List (Int × Int)) (result : List Nat) : Prop :=
  (∀ b, bestParam trials = some b → result = labelsOf b) ∧
  (bestParam trials = none → result = [])
-- post-conditions-end

-- impl-start
def implementation_fit_predict (trials : List (Int × Int)) : List Nat := Id.run do
  let mut best : Option (Int × Int) := none
  for t in trials do
    match best with
    | none => best := some t
    | some (_, bs) => if t.2 > bs then best := some t
  match best with
  | none => return []
  | some (bp, _) => return labelsOf bp
-- impl-end

-- proof-start
/-- The desugared `forIn` loop body equals folding `stepBest` over the trials,
generalized over the accumulator. -/
theorem loop_helper (trials : List (Int × Int)) (init : Option (Int × Int)) :
    (forIn (m := Id) trials init (fun t r =>
      match r with
      | none => pure (ForInStep.yield (some t))
      | some (_, bs) => if t.2 > bs then pure (ForInStep.yield (some t)) else pure (ForInStep.yield r)))
    = trials.foldl stepBest init := by
  induction trials generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind] at ih ⊢
    cases init with
    | none => simp only [ih, List.foldl_cons, stepBest]
    | some p =>
      obtain ⟨bp, bs⟩ := p
      by_cases h : a.2 > bs <;> simp only [h, if_true, if_false, ih, List.foldl_cons, stepBest]

theorem correct_fit_predict :
    ∀ trials : List (Int × Int), trials ≠ [] →
      problem_spec_fit_predict trials (implementation_fit_predict trials) := by
  intro trials _
  unfold implementation_fit_predict
  simp only [Id.run, bind]
  rw [loop_helper trials none]
  constructor
  · intro b hb
    unfold bestParam at hb
    cases hf : trials.foldl stepBest none with
    | none => rw [hf] at hb; simp at hb
    | some p => rw [hf] at hb; obtain ⟨bp, bs⟩ := p; simp at hb; simp only [hb]; rfl
  · intro hb
    unfold bestParam at hb
    cases hf : trials.foldl stepBest none with
    | none => rfl
    | some p => rw [hf] at hb; simp at hb
-- proof-end

#print axioms correct_fit_predict
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL COMPLETE. Same-spec confirmed True for all 9 files via swebench_unified.markers.same_spec (lean). Verify tool = scripts/lean_verify.sh <file>.

### VERIFY RESULTS (exit 0 = closes clean):
- positive_control (exact gold impl): exit 0, axioms [propext, Quot.sound] CLEAN. Faithful gold patch RESOLVES (report resolved:true; F2P test_gaussian_mixture_fit_predict_n_init + test_bayesian_mixture_fit_predict_n_init pass, all P2P pass). Harness validated end-to-end.
- atk_1 (PREPATCH BUG: return labelsOf lastConfig): exit 1, sorryAx — spec CATCHES the prepatch bug (gold proof cannot close; loop_helper mismatch on lastConfig). prepatch_reproduced=true.
- atk_2 (>= tie-break, last-wins): exit 1 sorryAx.
- atk_3 (ungrounded-oracle echo: always []): exit 1 sorryAx.
- atk_4 (partial-domain: correct only for singleton lists, else []): exit 1 sorryAx.
- atk_5 (boundary: select MIN score, t.2 < bs): exit 1 sorryAx.
- atk_6 (control-flow: return labelsOf of FIRST config): exit 1 sorryAx.
- atk_7 (output-mutation: correct best ++ spurious [0]): exit 1 sorryAx.
- atk_8 ([7] on empty, reusing GOLD proof): exit 1 sorryAx (gold proof pins empty-branch = []).
- atk_8b ([7] on empty, correct on non-empty, with a TAILORED closing proof using the trials ≠ [] hypothesis + a foldl_some lemma): exit 0, axioms [propext, Quot.sound] CLEAN.

MANDATORY RESOLVE STEP (protocol 2): atk_8b is the ONLY non-gold impl that closes with clean axioms. I materialized its FAITHFUL refined patch (gold reorder PLUS an n_init==0 empty-domain sentinel branch returning np.full(n_samples,7)) and ran it through the official harness via swebench_unified.harness.run_resolve / run_evaluation under `docker`. RESULT: resolved=True, patch_successfully_applied=True, both FAIL_TO_PASS pass, zero PASS_TO_PASS failures. Report saved 

WHY atk_8b resolving is EXPECTED (not a break): its ONLY divergence from gold is the empty-trials case (Lean) = n_init==0 (Python), which is UNREACHABLE — sklearn/mixture/base.py:102 _check_initial_parameters raises ValueError when n_init < 1, and do_init=False forces n_init=1. The theorem's `trials ≠ []` hypothesis faithfully mirrors this invariant. On the reachable domain atk_8b is byte-equivalent to gold, so it resolves. This is legitimate empty-domain slack, not verify⇏correct.

HARNESS NOTE: severe board contention (load ~125, 17-229 docker images churning from concurrent django/matplotlib concurrent runs resolves) caused swebench run_evaluation to fail intermittently in its startup client.images.list(all=True) with docker.errors.ImageNotFound (an image removed mid-enumeration). This hit GOLD and atk_8b identically (contention artifact, NOT a real non-resolve). A bounded retry loop (up to 15 attempts) slipped through the race window on attempt 1 for both once the churn eased; both then produced valid reports.

REFINEMENT.MD AUDIT: 4 legs, all valid kinds. Leg1 (-np.infty seed ↔ none): R. Leg2 (fitted trial ↔ (config,score)): R. Leg3 (strict > earliest-tie control flow): I. Leg4 (labelsOf bp ↔ final e-step+argmax under SELECTED config): A-reference — labelsOf is opaque, UNCHANGED by the patch (pure reordering), proof consumes NO _prop axiom (correctness is purely about WHICH config labelsOf is applied to). No kind-3 (changed-inexpressible) legs. A-reference correspondence to the real composite callee ("run final _e_step(X) under current params, then log_resp.argmax(axis=1)") holds. mapping.md callee provenance and n_init>1 observability analysis consistent.

VERDICT: SOUND. ≥5 distinct same-spec wrong impls run; every impl whose proof closes with clean axioms (only atk_8b) has a materialized faithful patch that RESOLVES; the prepatch bug is caught; A-legs audited. No verify⇏correct gap found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence between the modeled post-condition and the real repo callee (BaseMixture.fit_predict, sklearn/mixture/base.py, post-patch base_commit).

Checks performed:
- lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
- #print axioms correct_fit_predict = [propext, Quot.sound]; NO sorryAx -> proof is real.
- swebench_unified.markers.same_spec(Solution, Solution_prepatch, lean backend) = True -> axioms/pure/post-conditions regions byte-identical; only impl+proof differ (correct differential setup).

Model-vs-real correspondence (verified against the real repo fit_predict):
- Real fixed code: `if lower_bound > max_lower_bound` (strict >, seeded -np.infty), then AFTER `self._set_parameters(best_params)` runs the final `_, log_resp = self._e_step(X); return log_resp.argmax(axis=1)`. So returned labels are computed under the SELECTED best config.
- Spec: `problem_spec_fit_predict trials result := (bestParam trials = some b -> result = labelsOf b) AND (bestParam trials = none -> result = [])`, where bestParam = foldl stepBest (strict >, earliest-tie-wins, none seed).
- Selection semantics: strict > with none seed == Python strict > with -np.infty seed (first finite trial always accepted); ties keep the earlier best in both -> identical on the whole abstracted domain.
- labelsOf modeled `opaque` (deterministic function of config only), matching the real e-step+argmax which depends only on the currently-set parameter config; no `_prop` axiom -> the spec imposes NO extra property on the callee, so it is not too-strong there.
- Post-condition pins result = labelsOf(selected best config) exactly what the fixed code produces -> not too strong; the real repo behavior satisfies it.
- none/empty branch: unreachable in the real repo (n_init>=1) and excluded from the proven theorem (trials != []); vacuous, not a reachable divergence.

Conclusion: on every reachable abstracted input (non-empty trial lists) the modeled function agrees with the real callee. No diverging input exists. Spec is FAITHFUL (neither drifts from nor over-strengthens real behavior).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view formalizes correct behavior at abstract altitude: select the highest-scoring trial (bestParam fold) and report labelsOf(selected best config), with labelsOf an opaque unchanged callee. This is exactly what the problem_statement already implies (fit_predict must agree with predict, i.e. use the best fitted model) and does NOT reveal the gold-patch mechanics — no mention of _e_step, _set_parameters, 'final e-step', converged_, or any code-level reordering. The concrete fix (moving the final e-step to after _set_parameters) is described only in hints_text, which is excluded from this comparison. A correct spec necessarily excludes the buggy impl (labelsOf lastConfig), but that is the spec doing its job, not gold reconstruction. Cross-checks: same_spec(Solution, Solution_prepatch)=True (spec is a shared obligation, variants differ only in elided impl region); G-LEAK lexical screen passed with no failures; spec comments are abstract (tie-breaking, order-only scoring) and quote neither gold-patch specifics nor problem_statement phrasing.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
