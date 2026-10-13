# P2 adversarial audit — pytest-dev__pytest-7571

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,26 +63,13 @@
 
 -- impl-start
 def implementation_captureLevel (initialLevel : Int) (levels : List Int) : Int := Id.run do
-  let mut st : Int × Option Int := (initialLevel, none)
+  let mut handler := initialLevel
   for lvl in levels do
-    st := (lvl, some st.1)
-  return (match st.2 with
-          | some s => s
-          | none   => st.1)
+    handler := lvl
+  return handler
 -- impl-end
 
 -- proof-start
-theorem captureLevel_forIn_foldl (levels : List Int) (init : Int × Option Int) :
-    (Id.run (forIn levels init (fun lvl r => do
-        pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int)
-      = levels.foldl (fun st lvl => (lvl, some st.1)) init := by
-  induction levels generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, List.foldl_cons]
-    exact ih _
-
 theorem correct_captureLevel :
     ∀ (initialLevel : Int) (levels : List Int),
       problem_spec_captureLevel initialLevel levels
@@ -90,10 +77,7 @@
   intro initialLevel levels
   unfold problem_spec_captureLevel restoredCaptureLevel captureLevelState
     implementation_captureLevel
-  show (match (Id.run (forIn levels (initialLevel, none) (fun lvl r => do
-          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).2 with
-        | some s => s
-        | none => (Id.run (forIn levels (initialLevel, none) (fun lvl r => do
-          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).1) = _
-  rw [captureLevel_forIn_foldl]
+  induction levels with
+  | nil => rfl
+  | cons a as ih => simp_all
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,26 +63,13 @@
 
 -- impl-start
 def implementation_captureLevel (initialLevel : Int) (levels : List Int) : Int := Id.run do
-  let mut st : Int × Option Int := (initialLevel, none)
-  for lvl in levels do
-    st := (lvl, some st.1)
-  return (match st.2 with
-          | some s => s
-          | none   => st.1)
+  match levels with
+  | [] => return initialLevel
+  | [_] => return initialLevel
+  | _ => return initialLevel
 -- impl-end
 
 -- proof-start
-theorem captureLevel_forIn_foldl (levels : List Int) (init : Int × Option Int) :
-    (Id.run (forIn levels init (fun lvl r => do
-        pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int)
-      = levels.foldl (fun st lvl => (lvl, some st.1)) init := by
-  induction levels generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, List.foldl_cons]
-    exact ih _
-
 theorem correct_captureLevel :
     ∀ (initialLevel : Int) (levels : List Int),
       problem_spec_captureLevel initialLevel levels
@@ -90,10 +77,7 @@
   intro initialLevel levels
   unfold problem_spec_captureLevel restoredCaptureLevel captureLevelState
     implementation_captureLevel
-  show (match (Id.run (forIn levels (initialLevel, none) (fun lvl r => do
-          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).2 with
-        | some s => s
-        | none => (Id.run (forIn levels (initialLevel, none) (fun lvl r => do
-          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).1) = _
-  rw [captureLevel_forIn_foldl]
+  cases levels with
+  | nil => rfl
+  | cons a as => cases as <;> simp_all
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,26 +63,12 @@
 
 -- impl-start
 def implementation_captureLevel (initialLevel : Int) (levels : List Int) : Int := Id.run do
-  let mut st : Int × Option Int := (initialLevel, none)
-  for lvl in levels do
-    st := (lvl, some st.1)
-  return (match st.2 with
-          | some s => s
-          | none   => st.1)
+  match levels with
+  | [] => return initialLevel
+  | _ => return initialLevel
 -- impl-end
 
 -- proof-start
-theorem captureLevel_forIn_foldl (levels : List Int) (init : Int × Option Int) :
-    (Id.run (forIn levels init (fun lvl r => do
-        pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int)
-      = levels.foldl (fun st lvl => (lvl, some st.1)) init := by
-  induction levels generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, List.foldl_cons]
-    exact ih _
-
 theorem correct_captureLevel :
     ∀ (initialLevel : Int) (levels : List Int),
       problem_spec_captureLevel initialLevel levels
@@ -90,10 +76,5 @@
   intro initialLevel levels
   unfold problem_spec_captureLevel restoredCaptureLevel captureLevelState
     implementation_captureLevel
-  show (match (Id.run (forIn levels (initialLevel, none) (fun lvl r => do
-          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).2 with
-        | some s => s
-        | none => (Id.run (forIn levels (initialLevel, none) (fun lvl r => do
-          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).1) = _
-  rw [captureLevel_forIn_foldl]
+  cases levels <;> simp_all
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,24 +65,13 @@
 def implementation_captureLevel (initialLevel : Int) (levels : List Int) : Int := Id.run do
   let mut st : Int × Option Int := (initialLevel, none)
   for lvl in levels do
-    st := (lvl, some st.1)
+    st := (lvl, some lvl)   -- BUG: records the NEW level, not the prior one
   return (match st.2 with
           | some s => s
           | none   => st.1)
 -- impl-end
 
 -- proof-start
-theorem captureLevel_forIn_foldl (levels : List Int) (init : Int × Option Int) :
-    (Id.run (forIn levels init (fun lvl r => do
-        pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int)
-      = levels.foldl (fun st lvl => (lvl, some st.1)) init := by
-  induction levels generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, List.foldl_cons]
-    exact ih _
-
 theorem correct_captureLevel :
     ∀ (initialLevel : Int) (levels : List Int),
       problem_spec_captureLevel initialLevel levels
@@ -90,10 +79,7 @@
   intro initialLevel levels
   unfold problem_spec_captureLevel restoredCaptureLevel captureLevelState
     implementation_captureLevel
-  show (match (Id.run (forIn levels (initialLevel, none) (fun lvl r => do
-          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).2 with
-        | some s => s
-        | none => (Id.run (forIn levels (initialLevel, none) (fun lvl r => do
-          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).1) = _
-  rw [captureLevel_forIn_foldl]
+  induction levels with
+  | nil => rfl
+  | cons a as ih => simp_all
 -- proof-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -62,38 +62,15 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_captureLevel (initialLevel : Int) (levels : List Int) : Int := Id.run do
-  let mut st : Int × Option Int := (initialLevel, none)
-  for lvl in levels do
-    st := (lvl, some st.1)
-  return (match st.2 with
-          | some s => s
-          | none   => st.1)
+def implementation_captureLevel (initialLevel : Int) (levels : List Int) : Int :=
+  restoredCaptureLevel initialLevel levels
 -- impl-end
 
 -- proof-start
-theorem captureLevel_forIn_foldl (levels : List Int) (init : Int × Option Int) :
-    (Id.run (forIn levels init (fun lvl r => do
-        pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int)
-      = levels.foldl (fun st lvl => (lvl, some st.1)) init := by
-  induction levels generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, List.foldl_cons]
-    exact ih _
-
 theorem correct_captureLevel :
     ∀ (initialLevel : Int) (levels : List Int),
       problem_spec_captureLevel initialLevel levels
         (implementation_captureLevel initialLevel levels) := by
   intro initialLevel levels
-  unfold problem_spec_captureLevel restoredCaptureLevel captureLevelState
-    implementation_captureLevel
-  show (match (Id.run (forIn levels (initialLevel, none) (fun lvl r => do
-          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).2 with
-        | some s => s
-        | none => (Id.run (forIn levels (initialLevel, none) (fun lvl r => do
-          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).1) = _
-  rw [captureLevel_forIn_foldl]
+  rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,38 +62,16 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_captureLevel (initialLevel : Int) (levels : List Int) : Int := Id.run do
-  let mut st : Int × Option Int := (initialLevel, none)
-  for lvl in levels do
-    st := (lvl, some st.1)
-  return (match st.2 with
-          | some s => s
-          | none   => st.1)
+def implementation_captureLevel (initialLevel : Int) (levels : List Int) : Int :=
+  initialLevel
 -- impl-end
 
 -- proof-start
-theorem captureLevel_forIn_foldl (levels : List Int) (init : Int × Option Int) :
-    (Id.run (forIn levels init (fun lvl r => do
-        pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int)
-      = levels.foldl (fun st lvl => (lvl, some st.1)) init := by
-  induction levels generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, List.foldl_cons]
-    exact ih _
-
 theorem correct_captureLevel :
     ∀ (initialLevel : Int) (levels : List Int),
       problem_spec_captureLevel initialLevel levels
         (implementation_captureLevel initialLevel levels) := by
   intro initialLevel levels
   unfold problem_spec_captureLevel restoredCaptureLevel captureLevelState
-    implementation_captureLevel
-  show (match (Id.run (forIn levels (initialLevel, none) (fun lvl r => do
-          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).2 with
-        | some s => s
-        | none => (Id.run (forIn levels (initialLevel, none) (fun lvl r => do
-          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).1) = _
-  rw [captureLevel_forIn_foldl]
+  cases levels <;> simp_all
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,26 +63,13 @@
 
 -- impl-start
 def implementation_captureLevel (initialLevel : Int) (levels : List Int) : Int := Id.run do
-  let mut st : Int × Option Int := (initialLevel, none)
-  for lvl in levels do
-    st := (lvl, some st.1)
-  return (match st.2 with
-          | some s => s
-          | none   => st.1)
+  match levels.reverse with
+  | [] => return initialLevel
+  | [_] => return initialLevel
+  | _ :: prev :: _ => return prev   -- second-from-last raised level (not the pre-last threshold)
 -- impl-end
 
 -- proof-start
-theorem captureLevel_forIn_foldl (levels : List Int) (init : Int × Option Int) :
-    (Id.run (forIn levels init (fun lvl r => do
-        pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int)
-      = levels.foldl (fun st lvl => (lvl, some st.1)) init := by
-  induction levels generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, List.foldl_cons]
-    exact ih _
-
 theorem correct_captureLevel :
     ∀ (initialLevel : Int) (levels : List Int),
       problem_spec_captureLevel initialLevel levels
@@ -90,10 +77,5 @@
   intro initialLevel levels
   unfold problem_spec_captureLevel restoredCaptureLevel captureLevelState
     implementation_captureLevel
-  show (match (Id.run (forIn levels (initialLevel, none) (fun lvl r => do
-          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).2 with
-        | some s => s
-        | none => (Id.run (forIn levels (initialLevel, none) (fun lvl r => do
-          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).1) = _
-  rw [captureLevel_forIn_foldl]
+  simp_all
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Returning a log-capture threshold to its prior value at the end of a test.

A log-capture facility keeps a numeric *threshold* level: the minimum severity of
records it retains. A fresh facility starts at some initial threshold. During a
single test the threshold may be raised any number of times, each raise naming a
new level. Independently of how the named loggers are managed, the facility must
itself remember enough to undo its own threshold changes when the test ends.

The rule for the end of a test is:

* if the threshold was never raised during the test, it is left exactly as it was
  created;
* otherwise it is returned to the value it held immediately *before* the most
  recent raise — i.e. the threshold in effect just prior to the last change, not
  the last value it was raised to.

The observable modeled here is the capture threshold in effect after the test has
ended. Pinning it this way guarantees that a test which raises the threshold does
not leave that raised threshold in place afterwards: the facility is rolled back
to the threshold that preceded its last raise (and, when a test raises the
threshold exactly once from its created value, all the way back to that created
value), rather than being left at the level the test most recently asked for.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The threshold
-- lifecycle — recording, on each raise, the threshold in effect just before it,
-- and re-applying the last such record when the test ends — is modeled DEEPLY
-- over the observable inputs (the initial threshold and the ordered sequence of
-- raised levels), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- Fold one test's sequence of threshold raises into the facility's end-of-test
state, a pair `(currentThreshold, recordedThreshold)`. Each raise records the
threshold currently in effect (`some current`) and then moves the current
threshold to the newly named level. Starting from `(initialLevel, none)`, after
all raises `recordedThreshold` is `none` exactly when no raise happened. -/
def captureLevelState (initialLevel : Int) (levels : List Int) : Int × Option Int :=
  levels.foldl (fun st lvl => (lvl, some st.1)) (initialLevel, none)

/-- The capture threshold in effect after the test ends: the recorded threshold
if any raise happened (the value held just before the last raise), otherwise the
threshold the facility was created with. -/
def restoredCaptureLevel (initialLevel : Int) (levels : List Int) : Int :=
  match (captureLevelState initialLevel levels).2 with
  | some s => s
  | none   => (captureLevelState initialLevel levels).1
-- pure-end

-- post-conditions-start
/-- After the test ends the capture threshold equals the value dictated by the
end-of-test rule: the threshold held just before the most recent raise, or the
created threshold when no raise occurred. -/
def problem_spec_captureLevel
    (initialLevel : Int) (levels : List Int) (result : Int) : Prop :=
  result = restoredCaptureLevel initialLevel levels
-- post-conditions-end

-- impl-start
def implementation_captureLevel (initialLevel : Int) (levels : List Int) : Int := Id.run do
  let mut st : Int × Option Int := (initialLevel, none)
  for lvl in levels do
    st := (lvl, some st.1)
  return (match st.2 with
          | some s => s
          | none   => st.1)
-- impl-end

-- proof-start
theorem captureLevel_forIn_foldl (levels : List Int) (init : Int × Option Int) :
    (Id.run (forIn levels init (fun lvl r => do
        pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int)
      = levels.foldl (fun st lvl => (lvl, some st.1)) init := by
  induction levels generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, List.foldl_cons]
    exact ih _

theorem correct_captureLevel :
    ∀ (initialLevel : Int) (levels : List Int),
      problem_spec_captureLevel initialLevel levels
        (implementation_captureLevel initialLevel levels) := by
  intro initialLevel levels
  unfold problem_spec_captureLevel restoredCaptureLevel captureLevelState
    implementation_captureLevel
  show (match (Id.run (forIn levels (initialLevel, none) (fun lvl r => do
          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).2 with
        | some s => s
        | none => (Id.run (forIn levels (initialLevel, none) (fun lvl r => do
          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).1) = _
  rw [captureLevel_forIn_foldl]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_captureLevel initialLevel levels result := result = restoredCaptureLevel initialLevel levels is an EXACT functional equality to the total deterministic function restoredCaptureLevel. Any impl closing correct_captureLevel is therefore extensionally equal to restoredCaptureLevel on all inputs, i.e. reproduces the post-patch observable and must resolve. No closing-but-non-resolving impl can exist.

ATTACKS (all same_spec=True vs Solution.lean; only impl+proof regions edited; prefix lines 1-64 byte-identical; verified concurrently as background jobs, <=4 at a time via scripts/lean_verify.sh <f>):
- atk_1 prepatch bug (returns LAST raised level, no recording): exit=1, 'unsolved goals' at proof — cannot close.
- atk_2 partial-domain (initialLevel for |levels|>=2): exit=1 — cannot close.
- atk_3 boundary (value-before-FIRST-raise = initialLevel whenever any raise): exit=1 — cannot close.
- atk_4 control-flow-effect (records the NEW level `some lvl` instead of prior `some st.1`): exit=1 — cannot close.
- atk_6 constant (always initialLevel): exit=1 — cannot close.
- atk_7 fold-direction (second-from-last RAISED level via levels.reverse): exit=1 — cannot close.
- atk_5 ungrounded-oracle echo (implementation_captureLevel := restoredCaptureLevel initialLevel levels; proof by rfl): exit=0 (verifies, no sorry). #print axioms correct_captureLevel -> 'does not depend on any axioms' (clean). This is the ONLY non-gold impl that closes; it is extensionally identical to restoredCaptureLevel, i.e. to the gold post-patch behavior. Its faithful refined patch IS the gold patch (supplied above) and RESOLVES — a resolving echo of the gold, which under the resolve-step policy is NOT a weakness.

POSITIVE CONTROL pc.lean (gold verbatim): scripts/lean_verify.sh exit=0; #print axioms correct_captureLevel -> [propext, Quot.sound] (no sorryAx). Clean.

Commands used: `bash scripts/lean_verify.sh atk_N.lean`. same_spec confirmed True for all 7 attacks + pc via swebench_unified.markers.same_spec / get_backend('lean').

REFINEMENT.MD AUDIT: three legs, all tagged R (type refinement); NO A-consumed, NO A-reference, NO I, NO kind-3. Axioms region is empty (the whole capture-handler level lifecycle is the changed op, modeled DEEPLY over observable inputs per SPEC_GUIDE §3 which forbids axiomatizing a deeply-modeled changed op; G-AX skips correctly). No A-legs => no callee-contract correspondence to validate. R-leg correspondence to post-patch __init__/set_level/_finalize (record-before-set last-write-wins + teardown re-apply) holds and is mechanically confirmed by conformance_check.py (G-CONF, 120k fuzz, seed 7571, 0 mismatches). R/I legs are the G-CONF remit.

CONCLUSION: verify => correct holds. The 6 genuinely-wrong impls (partial-domain, boundary, control-flow-effect, constant, fold-direction, prepatch bug) all FAIL to close; the sole extra closing impl is the oracle echo whose faithful patch is the gold patch and resolves. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Returning a log-capture threshold to its prior value at the end of a test.

A log-capture facility keeps a numeric *threshold* level: the minimum severity of
records it retains. A fresh facility starts at some initial threshold. During a
single test the threshold may be raised any number of times, each raise naming a
new level. Independently of how the named loggers are managed, the facility must
itself remember enough to undo its own threshold changes when the test ends.

The rule for the end of a test is:

* if the threshold was never raised during the test, it is left exactly as it was
  created;
* otherwise it is returned to the value it held immediately *before* the most
  recent raise — i.e. the threshold in effect just prior to the last change, not
  the last value it was raised to.

The observable modeled here is the capture threshold in effect after the test has
ended. Pinning it this way guarantees that a test which raises the threshold does
not leave that raised threshold in place afterwards: the facility is rolled back
to the threshold that preceded its last raise (and, when a test raises the
threshold exactly once from its created value, all the way back to that created
value), rather than being left at the level the test most recently asked for.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The threshold
-- lifecycle — recording, on each raise, the threshold in effect just before it,
-- and re-applying the last such record when the test ends — is modeled DEEPLY
-- over the observable inputs (the initial threshold and the ordered sequence of
-- raised levels), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- Fold one test's sequence of threshold raises into the facility's end-of-test
state, a pair `(currentThreshold, recordedThreshold)`. Each raise records the
threshold currently in effect (`some current`) and then moves the current
threshold to the newly named level. Starting from `(initialLevel, none)`, after
all raises `recordedThreshold` is `none` exactly when no raise happened. -/
def captureLevelState (initialLevel : Int) (levels : List Int) : Int × Option Int :=
  levels.foldl (fun st lvl => (lvl, some st.1)) (initialLevel, none)

/-- The capture threshold in effect after the test ends: the recorded threshold
if any raise happened (the value held just before the last raise), otherwise the
threshold the facility was created with. -/
def restoredCaptureLevel (initialLevel : Int) (levels : List Int) : Int :=
  match (captureLevelState initialLevel levels).2 with
  | some s => s
  | none   => (captureLevelState initialLevel levels).1
-- pure-end

-- post-conditions-start
/-- After the test ends the capture threshold equals the value dictated by the
end-of-test rule: the threshold held just before the most recent raise, or the
created threshold when no raise occurred. -/
def problem_spec_captureLevel
    (initialLevel : Int) (levels : List Int) (result : Int) : Prop :=
  result = restoredCaptureLevel initialLevel levels
-- post-conditions-end

-- impl-start
def implementation_captureLevel (initialLevel : Int) (levels : List Int) : Int := Id.run do
  let mut st : Int × Option Int := (initialLevel, none)
  for lvl in levels do
    st := (lvl, some st.1)
  return (match st.2 with
          | some s => s
          | none   => st.1)
-- impl-end

-- proof-start
theorem captureLevel_forIn_foldl (levels : List Int) (init : Int × Option Int) :
    (Id.run (forIn levels init (fun lvl r => do
        pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int)
      = levels.foldl (fun st lvl => (lvl, some st.1)) init := by
  induction levels generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, List.foldl_cons]
    exact ih _

theorem correct_captureLevel :
    ∀ (initialLevel : Int) (levels : List Int),
      problem_spec_captureLevel initialLevel levels
        (implementation_captureLevel initialLevel levels) := by
  intro initialLevel levels
  unfold problem_spec_captureLevel restoredCaptureLevel captureLevelState
    implementation_captureLevel
  show (match (Id.run (forIn levels (initialLevel, none) (fun lvl r => do
          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).2 with
        | some s => s
        | none => (Id.run (forIn levels (initialLevel, none) (fun lvl r => do
          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).1) = _
  rw [captureLevel_forIn_foldl]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_captureLevel initialLevel levels result := result = restoredCaptureLevel initialLevel levels is an EXACT functional equality to the total deterministic function restoredCaptureLevel. Any impl closing correct_captureLevel is therefore extensionally equal to restoredCaptureLevel on all inputs, i.e. reproduces the post-patch observable and must resolve. No closing-but-non-resolving impl can exist.

ATTACKS (all same_spec=True vs Solution.lean; only impl+proof regions edited; prefix lines 1-64 byte-identical; verified concurrently as background jobs, <=4 at a time via scripts/lean_verify.sh <f>):
- atk_1 prepatch bug (returns LAST raised level, no recording): exit=1, 'unsolved goals' at proof — cannot close.
- atk_2 partial-domain (initialLevel for |levels|>=2): exit=1 — cannot close.
- atk_3 boundary (value-before-FIRST-raise = initialLevel whenever any raise): exit=1 — cannot close.
- atk_4 control-flow-effect (records the NEW level `some lvl` instead of prior `some st.1`): exit=1 — cannot close.
- atk_6 constant (always initialLevel): exit=1 — cannot close.
- atk_7 fold-direction (second-from-last RAISED level via levels.reverse): exit=1 — cannot close.
- atk_5 ungrounded-oracle echo (implementation_captureLevel := restoredCaptureLevel initialLevel levels; proof by rfl): exit=0 (verifies, no sorry). #print axioms correct_captureLevel -> 'does not depend on any axioms' (clean). This is the ONLY non-gold impl that closes; it is extensionally identical to restoredCaptureLevel, i.e. to the gold post-patch behavior. Its faithful refined patch IS the gold patch (supplied above) and RESOLVES — a resolving echo of the gold, which under the resolve-step policy is NOT a weakness.

POSITIVE CONTROL pc.lean (gold verbatim): scripts/lean_verify.sh exit=0; #print axioms correct_captureLevel -> [propext, Quot.sound] (no sorryAx). Clean.

Commands used: `bash scripts/lean_verify.sh atk_N.lean`. same_spec confirmed True for all 7 attacks + pc via swebench_unified.markers.same_spec / get_backend('lean').

REFINEMENT.MD AUDIT: three legs, all tagged R (type refinement); NO A-consumed, NO A-reference, NO I, NO kind-3. Axioms region is empty (the whole capture-handler level lifecycle is the changed op, modeled DEEPLY over observable inputs per SPEC_GUIDE §3 which forbids axiomatizing a deeply-modeled changed op; G-AX skips correctly). No A-legs => no callee-contract correspondence to validate. R-leg correspondence to post-patch __init__/set_level/_finalize (record-before-set last-write-wins + teardown re-apply) holds and is mechanically confirmed by conformance_check.py (G-CONF, 120k fuzz, seed 7571, 0 mismatches). R/I legs are the G-CONF remit.

CONCLUSION: verify => correct holds. The 6 genuinely-wrong impls (partial-domain, boundary, control-flow-effect, constant, fold-direction, prepatch bug) all FAIL to close; the sole extra closing impl is the oracle echo whose faithful patch is the gold patch and resolves. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** No divergence between the modeled function and the real repo callee found; spec is neither too strong nor drifted.

### Evidence
1. Spec integrity: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, lean-backend) = True — axioms/pure/pre/post regions are byte-identical; impl+proof cannot have weakened the spec.
2. Lean soundness: lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry). `#print axioms correct_captureLevel` = [propext, Quot.sound] — clean, no sorryAx; the proof is genuine.
3. Faithfulness (attack target): I materialized the real repo at base_commit 422685d0 in a worktree, applied the gold patch, and drove the ACTUAL callee (LogCaptureFixture.__init__/set_level/_finalize) against the model's shadow. Differential test: 8 hand-picked edge cases + 200,000 fuzzed (initialLevel, levels) inputs (levels len 0..6 over standard+idiosyncratic logging levels and arbitrary ints) => checked=200008, disagreements=0.
4. Hand-trace agreement: 0 raises -> initialLevel (finalize no-op); 1 raise -> initialLevel (recorded=level-before-single-raise); n>=2 raises -> level held immediately before the LAST raise. This is exactly restoredCaptureLevel = match (foldl (fun st lvl => (lvl, some st.1)) (initial,none)).2 with some s => s | none => initial. The Lean impl fold `st := (lvl, some st.1)` is an op-for-op match of gold's `self._initial_handler_level = self.handler.level; self.handler.setLevel(level)` (last-write-wins, matching the plain assignment, NOT setdefault).
5. Modeling assumptions validated on the real code: `str` level args are normalized to ints by logging before reaching the handler (['WARNING','INFO'], initial 0 -> restored 30); fresh LogCaptureHandler().level == 0 (the initialLevel=0 case). The unmodeled _initial_logger_levels dict is unchanged by the patch and independent of the capture-handler level (the sole F2P observable), so its omission does not make the spec too strong.
6. G-AX correctly skips (empty axioms region; deeply-modeled changed op, no consumed callee contract). The spec captures precisely the fixed behavior and correctly EXCLUDES the last-raised value (the pre-patch leak), so it is not too strong.

Cleaned up the temporary worktree after testing.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes with zero hard failures (leakage.screen: no diff markers, no gold-patch line reproduced, no patched file/module path src/_pytest/logging.py, no spec-view identifier embedding patched symbols {set_level, finalize}, no patched symbol named in comments, no narration). same_spec(Solution.lean, Solution_prepatch.lean)=True — the spec region (axioms/pure/post-conditions + docstrings) is byte-identical; pre/post bundles differ only in the elided impl/proof. The consumer spec view is fully abstracted: it describes a generic 'log-capture facility' with a numeric 'threshold' and never names LogCaptureFixture, set_level, _finalize, _initial_handler_level, self.handler.setLevel, or the file path; impl and proof are elided placeholders. The end-of-test rule stated in the spec (restore to the threshold held immediately before the most recent raise; created value when raised exactly once) is the faithful correctness specification of behavior ALREADY public in problem_statement ('The log levels set are restored automatically at the end of the test' + the set_level(42)->handler.level==0 repro). Specifying correct behavior is not leakage; the gold edit's localization (file, symbols, diff hunks) is nowhere disclosed. The multi-raise generalization is the genuine correct semantics, not a pointer to the Python edit site.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
