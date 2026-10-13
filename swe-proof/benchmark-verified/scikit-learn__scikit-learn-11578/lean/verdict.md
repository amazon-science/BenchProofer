# P2 adversarial audit — scikit-learn__scikit-learn-11578

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `atk_7.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong implementation admits a closing clean-axiom proof, so no faithful refined patch exists to run through the harness. The spec post-condition is a total functional equality (result = decisions.map (predictProba (parseMode multiClass))) and the Lean spec_view elides BOTH impl and proof regions, so any impl whose correct_scoringProbs closes must be extensionally equal to the gold spec. Every deviation was rejected by Lean with a genuine 'unsolved goals' extensional-inequality goal (not sorry, not timeout).
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,10 +91,9 @@
 noncomputable def implementation_scoringProbs
     (multiClass : String) (decisions : List (List (List ℝ))) :
     List (List (List ℝ)) := Id.run do
-  let mode := parseMode multiClass
   let mut out : List (List (List ℝ)) := []
   for d in decisions do
-    out := out ++ [predictProba mode d]
+    out := out ++ [predictProba ProbMode.ovr d]
   return out
 -- impl-end
 
@@ -119,6 +118,6 @@
         (implementation_scoringProbs multiClass decisions) := by
   intro multiClass decisions
   unfold problem_spec_scoringProbs implementation_scoringProbs
-  rw [forIn_append_helper (fun d => predictProba (parseMode multiClass) d) decisions []]
+  rw [forIn_append_helper (fun d => predictProba ProbMode.ovr d) decisions []]
   simp
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,10 +91,9 @@
 noncomputable def implementation_scoringProbs
     (multiClass : String) (decisions : List (List (List ℝ))) :
     List (List (List ℝ)) := Id.run do
-  let mode := parseMode multiClass
   let mut out : List (List (List ℝ)) := []
   for d in decisions do
-    out := out ++ [predictProba mode d]
+    out := out ++ [predictProba ProbMode.multinomial d]
   return out
 -- impl-end
 
@@ -119,6 +118,6 @@
         (implementation_scoringProbs multiClass decisions) := by
   intro multiClass decisions
   unfold problem_spec_scoringProbs implementation_scoringProbs
-  rw [forIn_append_helper (fun d => predictProba (parseMode multiClass) d) decisions []]
+  rw [forIn_append_helper (fun d => predictProba ProbMode.multinomial d) decisions []]
   simp
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,10 +91,9 @@
 noncomputable def implementation_scoringProbs
     (multiClass : String) (decisions : List (List (List ℝ))) :
     List (List (List ℝ)) := Id.run do
-  let mode := parseMode multiClass
   let mut out : List (List (List ℝ)) := []
   for d in decisions do
-    out := out ++ [predictProba mode d]
+    out := out ++ [d]
   return out
 -- impl-end
 
@@ -119,6 +118,6 @@
         (implementation_scoringProbs multiClass decisions) := by
   intro multiClass decisions
   unfold problem_spec_scoringProbs implementation_scoringProbs
-  rw [forIn_append_helper (fun d => predictProba (parseMode multiClass) d) decisions []]
+  rw [forIn_append_helper (fun d => d) decisions []]
   simp
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,31 +94,17 @@
   let mode := parseMode multiClass
   let mut out : List (List (List ℝ)) := []
   for d in decisions do
-    out := out ++ [predictProba mode d]
+    out := [predictProba mode d] ++ out
   return out
 -- impl-end
 
 -- proof-start
-theorem forIn_append_helper {α β : Type} (f : α → β) (xs : List α) (init : List β) :
-    (Id.run (do
-        let r ← forIn xs init (fun d r => do
-          pure PUnit.unit
-          pure (ForInStep.yield (r ++ [f d])))
-        pure r)) = init ++ xs.map f := by
-  induction xs generalizing init with
-  | nil => simp [Id.run]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons]
-
 theorem correct_scoringProbs :
     ∀ (multiClass : String) (decisions : List (List (List ℝ))),
       problem_spec_scoringProbs multiClass decisions
         (implementation_scoringProbs multiClass decisions) := by
   intro multiClass decisions
   unfold problem_spec_scoringProbs implementation_scoringProbs
-  rw [forIn_append_helper (fun d => predictProba (parseMode multiClass) d) decisions []]
-  simp
+  simp only [List.map]
+  rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,35 +90,15 @@
 -- impl-start
 noncomputable def implementation_scoringProbs
     (multiClass : String) (decisions : List (List (List ℝ))) :
-    List (List (List ℝ)) := Id.run do
-  let mode := parseMode multiClass
-  let mut out : List (List (List ℝ)) := []
-  for d in decisions do
-    out := out ++ [predictProba mode d]
-  return out
+    List (List (List ℝ)) := []
 -- impl-end
 
 -- proof-start
-theorem forIn_append_helper {α β : Type} (f : α → β) (xs : List α) (init : List β) :
-    (Id.run (do
-        let r ← forIn xs init (fun d r => do
-          pure PUnit.unit
-          pure (ForInStep.yield (r ++ [f d])))
-        pure r)) = init ++ xs.map f := by
-  induction xs generalizing init with
-  | nil => simp [Id.run]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons]
-
 theorem correct_scoringProbs :
     ∀ (multiClass : String) (decisions : List (List (List ℝ))),
       problem_spec_scoringProbs multiClass decisions
         (implementation_scoringProbs multiClass decisions) := by
   intro multiClass decisions
   unfold problem_spec_scoringProbs implementation_scoringProbs
-  rw [forIn_append_helper (fun d => predictProba (parseMode multiClass) d) decisions []]
   simp
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,35 +90,16 @@
 -- impl-start
 noncomputable def implementation_scoringProbs
     (multiClass : String) (decisions : List (List (List ℝ))) :
-    List (List (List ℝ)) := Id.run do
-  let mode := parseMode multiClass
-  let mut out : List (List (List ℝ)) := []
-  for d in decisions do
-    out := out ++ [predictProba mode d]
-  return out
+    List (List (List ℝ)) :=
+  (decisions.tail).map (fun d => predictProba (parseMode multiClass) d)
 -- impl-end
 
 -- proof-start
-theorem forIn_append_helper {α β : Type} (f : α → β) (xs : List α) (init : List β) :
-    (Id.run (do
-        let r ← forIn xs init (fun d r => do
-          pure PUnit.unit
-          pure (ForInStep.yield (r ++ [f d])))
-        pure r)) = init ++ xs.map f := by
-  induction xs generalizing init with
-  | nil => simp [Id.run]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons]
-
 theorem correct_scoringProbs :
     ∀ (multiClass : String) (decisions : List (List (List ℝ))),
       problem_spec_scoringProbs multiClass decisions
         (implementation_scoringProbs multiClass decisions) := by
   intro multiClass decisions
   unfold problem_spec_scoringProbs implementation_scoringProbs
-  rw [forIn_append_helper (fun d => predictProba (parseMode multiClass) d) decisions []]
   simp
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_7.lean`

```lean
import Mathlib
-- imports-end

/-!
Selecting the probability estimates a multiclass linear classifier reports.

A linear classifier that has been configured for a multiclass problem can report
per-class probability estimates in one of two regimes, chosen by a mode setting:

* the one-vs-rest regime maps each class's real-valued score through the logistic
  function and then normalises those values so the per-sample estimates sum to
  one; and
* the multinomial regime maps the whole row of per-class scores through the
  softmax function (exponentiate, then normalise so the row sums to one).

When a model is asked to produce the probability estimates that feed a
probabilistic evaluation, the regime actually used must be the one requested for
the multiclass problem. In particular, when the multinomial regime is requested,
the reported estimates must be the softmax of the score rows — not the
one-vs-rest values. The two regimes disagree on every nontrivial score row, so a
model that always reports one-vs-rest estimates diverges from the requested
behavior whenever the multinomial regime was requested.

Inputs are the requested multiclass mode (the string identifying the regime) and,
for each candidate solution, the matrix of per-sample, per-class real-valued
scores (the decision-function output). The output is, for each candidate, the
matrix of per-class probability estimates obtained by applying the requested
regime row by row, in the same order.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed as an axiom. The probability
-- transforms (logistic-then-normalise and softmax) are modeled DEEPLY over the
-- real-valued score rows that are the observable input, so no `opaque`/`axiom`
-- callee contract is required (G-AX validates these transforms against the real
-- probability routine; G-CONF exercises the mode selection and framing).
-- axioms-end

-- pure-start
/-- The logistic (sigmoid) function on a real score. -/
noncomputable def sigmoid (x : ℝ) : ℝ := 1 / (1 + Real.exp (-x))

/-- One-vs-rest estimates for a single score row: each score through the logistic
function, then normalised so the row sums to one. -/
noncomputable def ovrRow (row : List ℝ) : List ℝ :=
  let s := row.map sigmoid
  let tot := s.sum
  s.map (fun v => v / tot)

/-- Softmax estimates for a single score row: exponentiate each score, then
normalise so the row sums to one. -/
noncomputable def softmaxRow (row : List ℝ) : List ℝ :=
  let e := row.map Real.exp
  let tot := e.sum
  e.map (fun v => v / tot)

/-- The two probability regimes. -/
inductive ProbMode where
  | ovr
  | multinomial
deriving DecidableEq, Repr

/-- The mode identified by the requested multiclass string: the multinomial
regime is requested by `"multinomial"`; any other value selects one-vs-rest. -/
def parseMode (s : String) : ProbMode :=
  if s = "multinomial" then ProbMode.multinomial else ProbMode.ovr

/-- The probability estimates for one score row under a given regime. -/
noncomputable def predictProbaRow (m : ProbMode) (row : List ℝ) : List ℝ :=
  match m with
  | ProbMode.ovr => ovrRow row
  | ProbMode.multinomial => softmaxRow row

/-- The probability estimates for a whole score matrix: the regime applied to
each row, in order. -/
noncomputable def predictProba (m : ProbMode) (decision : List (List ℝ)) : List (List ℝ) :=
  decision.map (predictProbaRow m)
-- pure-end

-- post-conditions-start
/-- For each candidate's score matrix, the reported estimates are exactly the
probability estimates of that matrix under the regime requested for the
multiclass problem, in the same order; the number of candidates is preserved. -/
def problem_spec_scoringProbs
    (multiClass : String) (decisions : List (List (List ℝ)))
    (result : List (List (List ℝ))) : Prop :=
  result = decisions.map (fun d => predictProba (parseMode multiClass) d)
-- post-conditions-end

-- impl-start
noncomputable def implementation_scoringProbs
    (multiClass : String) (decisions : List (List (List ℝ))) :
    List (List (List ℝ)) :=
  decisions.map (fun d => predictProba (parseMode multiClass) d)
-- impl-end

-- proof-start
theorem correct_scoringProbs :
    ∀ (multiClass : String) (decisions : List (List (List ℝ))),
      problem_spec_scoringProbs multiClass decisions
        (implementation_scoringProbs multiClass decisions) := by
  intro multiClass decisions
  unfold problem_spec_scoringProbs implementation_scoringProbs
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Same_spec confirmed True for all 6 wrong impls + the positive control (spec_signature identical; axioms/pure/post regions byte-identical to gold Solution.lean). Verified concurrently, <=4 background jobs at a time.

Attacks (all same_spec=True; command: `bash scripts/lean_verify.sh <path>`):
- atk_1 PREPATCH BUG (always ProbMode.ovr, ignore multiClass): exit=1. Residual goal `∀ a ∈ decisions, predictProba ProbMode.ovr a = predictProba (parseMode multiClass) a` (unprovable; ovr≠multinomial on nontrivial rows). Prepatch reproduced.
- atk_2 always ProbMode.multinomial: exit=1. Residual goal `predictProba ProbMode.multinomial a = predictProba (parseMode multiClass) a` unprovable.
- atk_3 identity (return decisions untransformed): exit=1. Goal `decisions = List.map (fun d => predictProba (parseMode multiClass) d) decisions` unprovable.
- atk_4 control-flow effect (prepend => reversed order): exit=1 (unsolved goals; order/count mismatch).
- atk_5 partial/degenerate (return []): exit=1. Goal `decisions = []` unprovable.
- atk_6 boundary/off-by-one (drop first candidate via .tail): exit=1. Goal `(map f decisions).tail = map f decisions` unprovable.
- atk_7 POSITIVE CONTROL / ungrounded-oracle echo (decisions.map (predictProba (parseMode multiClass))): exit=0, verifies, no sorry. `#print axioms correct_scoringProbs` => [propext, Classical.choice, Quot.sound] (clean; only Mathlib-standard classical axioms, no bundle axiom/sorryAx).

Because the ONLY impl that closes is the extensional echo of the gold spec, there is no verifying-but-incorrect impl and therefore no faithful patch to materialize/resolve. verify⇏correct could not be exhibited; the equality spec is tight.

refinement.md audit: legs are op1=R (String→ProbMode dispatch the patch enables), op2=R/I (candidate loop, order+count preserved), op3=A-reference (softmaxRow/ovrRow deeply modeled; G-AX validates == real callees sklearn.utils.extmath.softmax and LinearClassifierMixin._predict_proba_lr per mapping.md), op4=I (return). NO A-consumed axioms — axioms region is empty (verified: gold proof `#print axioms` shows only propext/Classical.choice/Quot.sound, no opaque/axiom callee contract). No kind-3 (changed-inexpressible) leg. A-reference↔real-callee correspondence holds; modeled domain (n_classes>=2 multiclass rows) matches the F2P observable. conf_skip=false as stated.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `atk_7.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong implementation admits a closing clean-axiom proof, so no faithful refined patch exists to run through the harness. The spec post-condition is a total functional equality (result = decisions.map (predictProba (parseMode multiClass))) and the Lean spec_view elides BOTH impl and proof regions, so any impl whose correct_scoringProbs closes must be extensionally equal to the gold spec. Every deviation was rejected by Lean with a genuine 'unsolved goals' extensional-inequality goal (not sorry, not timeout).
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_7.lean`

```lean
import Mathlib
-- imports-end

/-!
Selecting the probability estimates a multiclass linear classifier reports.

A linear classifier that has been configured for a multiclass problem can report
per-class probability estimates in one of two regimes, chosen by a mode setting:

* the one-vs-rest regime maps each class's real-valued score through the logistic
  function and then normalises those values so the per-sample estimates sum to
  one; and
* the multinomial regime maps the whole row of per-class scores through the
  softmax function (exponentiate, then normalise so the row sums to one).

When a model is asked to produce the probability estimates that feed a
probabilistic evaluation, the regime actually used must be the one requested for
the multiclass problem. In particular, when the multinomial regime is requested,
the reported estimates must be the softmax of the score rows — not the
one-vs-rest values. The two regimes disagree on every nontrivial score row, so a
model that always reports one-vs-rest estimates diverges from the requested
behavior whenever the multinomial regime was requested.

Inputs are the requested multiclass mode (the string identifying the regime) and,
for each candidate solution, the matrix of per-sample, per-class real-valued
scores (the decision-function output). The output is, for each candidate, the
matrix of per-class probability estimates obtained by applying the requested
regime row by row, in the same order.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed as an axiom. The probability
-- transforms (logistic-then-normalise and softmax) are modeled DEEPLY over the
-- real-valued score rows that are the observable input, so no `opaque`/`axiom`
-- callee contract is required (G-AX validates these transforms against the real
-- probability routine; G-CONF exercises the mode selection and framing).
-- axioms-end

-- pure-start
/-- The logistic (sigmoid) function on a real score. -/
noncomputable def sigmoid (x : ℝ) : ℝ := 1 / (1 + Real.exp (-x))

/-- One-vs-rest estimates for a single score row: each score through the logistic
function, then normalised so the row sums to one. -/
noncomputable def ovrRow (row : List ℝ) : List ℝ :=
  let s := row.map sigmoid
  let tot := s.sum
  s.map (fun v => v / tot)

/-- Softmax estimates for a single score row: exponentiate each score, then
normalise so the row sums to one. -/
noncomputable def softmaxRow (row : List ℝ) : List ℝ :=
  let e := row.map Real.exp
  let tot := e.sum
  e.map (fun v => v / tot)

/-- The two probability regimes. -/
inductive ProbMode where
  | ovr
  | multinomial
deriving DecidableEq, Repr

/-- The mode identified by the requested multiclass string: the multinomial
regime is requested by `"multinomial"`; any other value selects one-vs-rest. -/
def parseMode (s : String) : ProbMode :=
  if s = "multinomial" then ProbMode.multinomial else ProbMode.ovr

/-- The probability estimates for one score row under a given regime. -/
noncomputable def predictProbaRow (m : ProbMode) (row : List ℝ) : List ℝ :=
  match m with
  | ProbMode.ovr => ovrRow row
  | ProbMode.multinomial => softmaxRow row

/-- The probability estimates for a whole score matrix: the regime applied to
each row, in order. -/
noncomputable def predictProba (m : ProbMode) (decision : List (List ℝ)) : List (List ℝ) :=
  decision.map (predictProbaRow m)
-- pure-end

-- post-conditions-start
/-- For each candidate's score matrix, the reported estimates are exactly the
probability estimates of that matrix under the regime requested for the
multiclass problem, in the same order; the number of candidates is preserved. -/
def problem_spec_scoringProbs
    (multiClass : String) (decisions : List (List (List ℝ)))
    (result : List (List (List ℝ))) : Prop :=
  result = decisions.map (fun d => predictProba (parseMode multiClass) d)
-- post-conditions-end

-- impl-start
noncomputable def implementation_scoringProbs
    (multiClass : String) (decisions : List (List (List ℝ))) :
    List (List (List ℝ)) :=
  decisions.map (fun d => predictProba (parseMode multiClass) d)
-- impl-end

-- proof-start
theorem correct_scoringProbs :
    ∀ (multiClass : String) (decisions : List (List (List ℝ))),
      problem_spec_scoringProbs multiClass decisions
        (implementation_scoringProbs multiClass decisions) := by
  intro multiClass decisions
  unfold problem_spec_scoringProbs implementation_scoringProbs
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Same_spec confirmed True for all 6 wrong impls + the positive control (spec_signature identical; axioms/pure/post regions byte-identical to gold Solution.lean). Verified concurrently, <=4 background jobs at a time.

Attacks (all same_spec=True; command: `bash scripts/lean_verify.sh <path>`):
- atk_1 PREPATCH BUG (always ProbMode.ovr, ignore multiClass): exit=1. Residual goal `∀ a ∈ decisions, predictProba ProbMode.ovr a = predictProba (parseMode multiClass) a` (unprovable; ovr≠multinomial on nontrivial rows). Prepatch reproduced.
- atk_2 always ProbMode.multinomial: exit=1. Residual goal `predictProba ProbMode.multinomial a = predictProba (parseMode multiClass) a` unprovable.
- atk_3 identity (return decisions untransformed): exit=1. Goal `decisions = List.map (fun d => predictProba (parseMode multiClass) d) decisions` unprovable.
- atk_4 control-flow effect (prepend => reversed order): exit=1 (unsolved goals; order/count mismatch).
- atk_5 partial/degenerate (return []): exit=1. Goal `decisions = []` unprovable.
- atk_6 boundary/off-by-one (drop first candidate via .tail): exit=1. Goal `(map f decisions).tail = map f decisions` unprovable.
- atk_7 POSITIVE CONTROL / ungrounded-oracle echo (decisions.map (predictProba (parseMode multiClass))): exit=0, verifies, no sorry. `#print axioms correct_scoringProbs` => [propext, Classical.choice, Quot.sound] (clean; only Mathlib-standard classical axioms, no bundle axiom/sorryAx).

Because the ONLY impl that closes is the extensional echo of the gold spec, there is no verifying-but-incorrect impl and therefore no faithful patch to materialize/resolve. verify⇏correct could not be exhibited; the equality spec is tight.

refinement.md audit: legs are op1=R (String→ProbMode dispatch the patch enables), op2=R/I (candidate loop, order+count preserved), op3=A-reference (softmaxRow/ovrRow deeply modeled; G-AX validates == real callees sklearn.utils.extmath.softmax and LinearClassifierMixin._predict_proba_lr per mapping.md), op4=I (return). NO A-consumed axioms — axioms region is empty (verified: gold proof `#print axioms` shows only propext/Classical.choice/Quot.sound, no opaque/axiom callee contract). No kind-3 (changed-inexpressible) leg. A-reference↔real-callee correspondence holds; modeled domain (n_classes>=2 multiclass rows) matches the F2P observable. conf_skip=false as stated.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical checks: lean_verify.sh exit 0 (compiles, no sorry). '#print axioms correct_scoringProbs' = [propext, Classical.choice, Quot.sound] only (no sorryAx; proof genuine). markers.same_spec(Solution, Solution_prepatch, lean-tables) = True (spec region byte-identical). Verified real callees against logistic_11578.py L1343 dispatch, utils/extmath.py softmax (L583), linear_model/base.py _predict_proba_lr. parseMode's default differs from the real dispatch default but only on inputs excluded by _check_solver_option validation, so no reachable disagreement. Spec is not too strong — it neither over-constrains nor drifts from real behavior on the reachable domain. Verdict: FAITHFUL.

Counterexample / evidence:

```
None survives on the modeled/reachable domain. On multiClass in {'ovr','multinomial'} with >=2-column real-valued decision rows, predictProba(parseMode m) equals LogisticRegression.predict_proba exactly: softmaxRow == extmath.softmax (exp/sum vs stable max-subtracted exp/sum, mathematically equal) and ovrRow == _predict_proba_lr 2-D branch (sigmoid per entry then row-normalize).
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage ceiling = the public problem_statement, which is maximally disclosive for this instance: it names the exact buggy line and file:line (logistic.py#L922, `log_reg = LogisticRegression(fit_intercept=fit_intercept)`), states the bug (LogisticRegressionCV(multi_class='multinomial') uses OvR for probabilistic scorers), describes BOTH regimes verbatim ('former uses a single logistic function and normalises (one-v-rest approach), whereas the latter uses the softmax function (multinomial approach)'), proposes the exact gold fix (`LogisticRegression(fit_intercept=fit_intercept, multi_class=multi_class)`), and even ships runnable code implementing ovr_approach = 1/(1+exp(-x)) then row-normalise (== ovrRow) and utils.extmath.softmax (== softmaxRow). Spec-view content assessed line by line: the doc comment (L4-29) abstractly describes the two regimes and requires the reported estimates use the REQUESTED regime; pure defs sigmoid/ovrRow/softmaxRow/ProbMode/parseMode/predictProba model exactly those two transforms + the requested-mode dispatch; problem_spec_scoringProbs states result = per-candidate predictProba(parseMode multiClass). Every element (both transforms, the requested-mode dispatch, the observable, the disagreement on nontrivial rows) is already fully disclosed by the problem_statement (and independently by the runnable minimal example). The spec view is strictly a SUBSET of the problem_statement's disclosure and adds nothing about the gold edit's mechanics: it never mentions the LogisticRegression constructor, the fit_intercept vs multi_class argument swap, the variable/parameter name flow, or logistic.py's internals. Spec byte-identity confirmed: swebench_unified.markers.same_spec(Solution, Solution_prepatch, lean) = True — the only divergence (impl fixes mode := ProbMode.ovr vs parseMode multiClass, and the proof) lives in the impl/proof regions, which are NOT part of the spec view. hints_text was excluded from the ceiling per policy (it also happens to restate the fix). Conclusion: no spec-view line leaks the gold edit beyond the public problem_statement. G-LEAK lexical screen recorded pass ('spec view clean'), consistent with this semantic assessment.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
