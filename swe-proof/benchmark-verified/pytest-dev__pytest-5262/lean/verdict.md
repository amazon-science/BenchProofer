# P2 adversarial audit — pytest-dev__pytest-5262

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -28,43 +28,16 @@
 def implementation_mode (bufferMode : List Char) : List Char := Id.run do
   let mut acc : List Char := []
   for c in bufferMode do
-    if c ≠ 'b' then
-      acc := acc ++ [c]
+    acc := acc ++ [c]
   return acc
 -- impl-end
 
 -- proof-start
-/-- Helper: the cleaned `forIn` accumulation, generalized over the accumulator,
-equals the initial accumulator appended with the front-recursive `stripBinary`. -/
-theorem mode_forIn_helper (xs : List Char) (init : List Char) :
-    Id.run (forIn xs init (fun c r =>
-      if c ≠ 'b' then do pure PUnit.unit; pure (ForInStep.yield (r ++ [c]))
-      else do pure PUnit.unit; pure (ForInStep.yield r))) = init ++ stripBinary xs := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, stripBinary, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a = 'b'
-    · simp only [h, ne_eq, not_true_eq_false, if_false]
-      rw [ih]
-      simp [stripBinary]
-    · simp only [h, ne_eq, not_false_eq_true, if_true]
-      rw [ih, List.append_assoc]
-      simp [stripBinary, h]
-
 theorem correct_mode : ∀ bufferMode : List Char,
     problem_spec_mode bufferMode (implementation_mode bufferMode) := by
   intro bufferMode
   unfold problem_spec_mode implementation_mode
-  have h2 : (Id.run do
-      let mut acc : List Char := []
-      for c in bufferMode do
-        if c ≠ 'b' then
-          acc := acc ++ [c]
-      return acc) = Id.run (forIn bufferMode ([] : List Char) (fun c r =>
-      if c ≠ 'b' then do pure PUnit.unit; pure (ForInStep.yield (r ++ [c]))
-      else do pure PUnit.unit; pure (ForInStep.yield r))) := rfl
-  rw [h2, mode_forIn_helper]
-  simp
+  induction bufferMode with
+  | nil => rfl
+  | cons a as ih => simp_all [stripBinary]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -25,46 +25,18 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_mode (bufferMode : List Char) : List Char := Id.run do
-  let mut acc : List Char := []
-  for c in bufferMode do
-    if c ≠ 'b' then
-      acc := acc ++ [c]
-  return acc
+def implementation_mode (bufferMode : List Char) : List Char :=
+  match bufferMode with
+  | [] => []
+  | c :: cs => if c = 'b' then cs else c :: cs
 -- impl-end
 
 -- proof-start
-/-- Helper: the cleaned `forIn` accumulation, generalized over the accumulator,
-equals the initial accumulator appended with the front-recursive `stripBinary`. -/
-theorem mode_forIn_helper (xs : List Char) (init : List Char) :
-    Id.run (forIn xs init (fun c r =>
-      if c ≠ 'b' then do pure PUnit.unit; pure (ForInStep.yield (r ++ [c]))
-      else do pure PUnit.unit; pure (ForInStep.yield r))) = init ++ stripBinary xs := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, stripBinary, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a = 'b'
-    · simp only [h, ne_eq, not_true_eq_false, if_false]
-      rw [ih]
-      simp [stripBinary]
-    · simp only [h, ne_eq, not_false_eq_true, if_true]
-      rw [ih, List.append_assoc]
-      simp [stripBinary, h]
-
 theorem correct_mode : ∀ bufferMode : List Char,
     problem_spec_mode bufferMode (implementation_mode bufferMode) := by
   intro bufferMode
   unfold problem_spec_mode implementation_mode
-  have h2 : (Id.run do
-      let mut acc : List Char := []
-      for c in bufferMode do
-        if c ≠ 'b' then
-          acc := acc ++ [c]
-      return acc) = Id.run (forIn bufferMode ([] : List Char) (fun c r =>
-      if c ≠ 'b' then do pure PUnit.unit; pure (ForInStep.yield (r ++ [c]))
-      else do pure PUnit.unit; pure (ForInStep.yield r))) := rfl
-  rw [h2, mode_forIn_helper]
-  simp
+  cases bufferMode with
+  | nil => rfl
+  | cons a as => by_cases h : a = 'b' <;> simp [h, stripBinary]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -25,46 +25,16 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_mode (bufferMode : List Char) : List Char := Id.run do
-  let mut acc : List Char := []
-  for c in bufferMode do
-    if c ≠ 'b' then
-      acc := acc ++ [c]
-  return acc
+def implementation_mode (bufferMode : List Char) : List Char :=
+  bufferMode.reverse.filter (· ≠ 'b')
 -- impl-end
 
 -- proof-start
-/-- Helper: the cleaned `forIn` accumulation, generalized over the accumulator,
-equals the initial accumulator appended with the front-recursive `stripBinary`. -/
-theorem mode_forIn_helper (xs : List Char) (init : List Char) :
-    Id.run (forIn xs init (fun c r =>
-      if c ≠ 'b' then do pure PUnit.unit; pure (ForInStep.yield (r ++ [c]))
-      else do pure PUnit.unit; pure (ForInStep.yield r))) = init ++ stripBinary xs := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, stripBinary, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a = 'b'
-    · simp only [h, ne_eq, not_true_eq_false, if_false]
-      rw [ih]
-      simp [stripBinary]
-    · simp only [h, ne_eq, not_false_eq_true, if_true]
-      rw [ih, List.append_assoc]
-      simp [stripBinary, h]
-
 theorem correct_mode : ∀ bufferMode : List Char,
     problem_spec_mode bufferMode (implementation_mode bufferMode) := by
   intro bufferMode
   unfold problem_spec_mode implementation_mode
-  have h2 : (Id.run do
-      let mut acc : List Char := []
-      for c in bufferMode do
-        if c ≠ 'b' then
-          acc := acc ++ [c]
-      return acc) = Id.run (forIn bufferMode ([] : List Char) (fun c r =>
-      if c ≠ 'b' then do pure PUnit.unit; pure (ForInStep.yield (r ++ [c]))
-      else do pure PUnit.unit; pure (ForInStep.yield r))) := rfl
-  rw [h2, mode_forIn_helper]
-  simp
+  induction bufferMode with
+  | nil => rfl
+  | cons a as ih => by_cases h : a = 'b' <;> simp_all [stripBinary, List.filter]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -28,43 +28,17 @@
 def implementation_mode (bufferMode : List Char) : List Char := Id.run do
   let mut acc : List Char := []
   for c in bufferMode do
-    if c ≠ 'b' then
+    if c ≠ 'a' then
       acc := acc ++ [c]
   return acc
 -- impl-end
 
 -- proof-start
-/-- Helper: the cleaned `forIn` accumulation, generalized over the accumulator,
-equals the initial accumulator appended with the front-recursive `stripBinary`. -/
-theorem mode_forIn_helper (xs : List Char) (init : List Char) :
-    Id.run (forIn xs init (fun c r =>
-      if c ≠ 'b' then do pure PUnit.unit; pure (ForInStep.yield (r ++ [c]))
-      else do pure PUnit.unit; pure (ForInStep.yield r))) = init ++ stripBinary xs := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, stripBinary, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a = 'b'
-    · simp only [h, ne_eq, not_true_eq_false, if_false]
-      rw [ih]
-      simp [stripBinary]
-    · simp only [h, ne_eq, not_false_eq_true, if_true]
-      rw [ih, List.append_assoc]
-      simp [stripBinary, h]
-
 theorem correct_mode : ∀ bufferMode : List Char,
     problem_spec_mode bufferMode (implementation_mode bufferMode) := by
   intro bufferMode
   unfold problem_spec_mode implementation_mode
-  have h2 : (Id.run do
-      let mut acc : List Char := []
-      for c in bufferMode do
-        if c ≠ 'b' then
-          acc := acc ++ [c]
-      return acc) = Id.run (forIn bufferMode ([] : List Char) (fun c r =>
-      if c ≠ 'b' then do pure PUnit.unit; pure (ForInStep.yield (r ++ [c]))
-      else do pure PUnit.unit; pure (ForInStep.yield r))) := rfl
-  rw [h2, mode_forIn_helper]
-  simp
+  induction bufferMode with
+  | nil => rfl
+  | cons a as ih => by_cases h : a = 'b' <;> simp_all [stripBinary]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -25,46 +25,16 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_mode (bufferMode : List Char) : List Char := Id.run do
-  let mut acc : List Char := []
-  for c in bufferMode do
-    if c ≠ 'b' then
-      acc := acc ++ [c]
-  return acc
+def implementation_mode (bufferMode : List Char) : List Char :=
+  bufferMode.filter (fun c => c ≠ 'b' ∧ c ≠ 't')
 -- impl-end
 
 -- proof-start
-/-- Helper: the cleaned `forIn` accumulation, generalized over the accumulator,
-equals the initial accumulator appended with the front-recursive `stripBinary`. -/
-theorem mode_forIn_helper (xs : List Char) (init : List Char) :
-    Id.run (forIn xs init (fun c r =>
-      if c ≠ 'b' then do pure PUnit.unit; pure (ForInStep.yield (r ++ [c]))
-      else do pure PUnit.unit; pure (ForInStep.yield r))) = init ++ stripBinary xs := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, stripBinary, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a = 'b'
-    · simp only [h, ne_eq, not_true_eq_false, if_false]
-      rw [ih]
-      simp [stripBinary]
-    · simp only [h, ne_eq, not_false_eq_true, if_true]
-      rw [ih, List.append_assoc]
-      simp [stripBinary, h]
-
 theorem correct_mode : ∀ bufferMode : List Char,
     problem_spec_mode bufferMode (implementation_mode bufferMode) := by
   intro bufferMode
   unfold problem_spec_mode implementation_mode
-  have h2 : (Id.run do
-      let mut acc : List Char := []
-      for c in bufferMode do
-        if c ≠ 'b' then
-          acc := acc ++ [c]
-      return acc) = Id.run (forIn bufferMode ([] : List Char) (fun c r =>
-      if c ≠ 'b' then do pure PUnit.unit; pure (ForInStep.yield (r ++ [c]))
-      else do pure PUnit.unit; pure (ForInStep.yield r))) := rfl
-  rw [h2, mode_forIn_helper]
-  simp
+  induction bufferMode with
+  | nil => rfl
+  | cons a as ih => by_cases h : a = 'b' <;> simp_all [stripBinary, List.filter]
 -- proof-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -25,46 +25,13 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_mode (bufferMode : List Char) : List Char := Id.run do
-  let mut acc : List Char := []
-  for c in bufferMode do
-    if c ≠ 'b' then
-      acc := acc ++ [c]
-  return acc
+def implementation_mode (bufferMode : List Char) : List Char :=
+  stripBinary bufferMode
 -- impl-end
 
 -- proof-start
-/-- Helper: the cleaned `forIn` accumulation, generalized over the accumulator,
-equals the initial accumulator appended with the front-recursive `stripBinary`. -/
-theorem mode_forIn_helper (xs : List Char) (init : List Char) :
-    Id.run (forIn xs init (fun c r =>
-      if c ≠ 'b' then do pure PUnit.unit; pure (ForInStep.yield (r ++ [c]))
-      else do pure PUnit.unit; pure (ForInStep.yield r))) = init ++ stripBinary xs := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, stripBinary, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a = 'b'
-    · simp only [h, ne_eq, not_true_eq_false, if_false]
-      rw [ih]
-      simp [stripBinary]
-    · simp only [h, ne_eq, not_false_eq_true, if_true]
-      rw [ih, List.append_assoc]
-      simp [stripBinary, h]
-
 theorem correct_mode : ∀ bufferMode : List Char,
     problem_spec_mode bufferMode (implementation_mode bufferMode) := by
   intro bufferMode
-  unfold problem_spec_mode implementation_mode
-  have h2 : (Id.run do
-      let mut acc : List Char := []
-      for c in bufferMode do
-        if c ≠ 'b' then
-          acc := acc ++ [c]
-      return acc) = Id.run (forIn bufferMode ([] : List Char) (fun c r =>
-      if c ≠ 'b' then do pure PUnit.unit; pure (ForInStep.yield (r ++ [c]))
-      else do pure PUnit.unit; pure (ForInStep.yield r))) := rfl
-  rw [h2, mode_forIn_helper]
-  simp
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: the mode-string
-- transformation is modeled DEEPLY (a per-character filter, below) rather than
-- axiomatized, so its standard-library reference is validated as an A-reference
-- by G-AX. The proof agent may add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- Front-recursive specification fold over the underlying stream's mode string:
keep every character except the binary-indicator character `'b'`, in order. -/
def stripBinary : List Char → List Char
  | [] => []
  | c :: cs => if c = 'b' then stripBinary cs else c :: stripBinary cs
-- pure-end

-- post-conditions-start
/-- The reported text-stream mode is exactly the underlying stream's mode string
with every binary-indicator character `'b'` removed and every other character
preserved in its original order. -/
def problem_spec_mode (bufferMode : List Char) (result : List Char) : Prop :=
  result = stripBinary bufferMode
-- post-conditions-end

-- impl-start
def implementation_mode (bufferMode : List Char) : List Char := Id.run do
  let mut acc : List Char := []
  for c in bufferMode do
    if c ≠ 'b' then
      acc := acc ++ [c]
  return acc
-- impl-end

-- proof-start
/-- Helper: the cleaned `forIn` accumulation, generalized over the accumulator,
equals the initial accumulator appended with the front-recursive `stripBinary`. -/
theorem mode_forIn_helper (xs : List Char) (init : List Char) :
    Id.run (forIn xs init (fun c r =>
      if c ≠ 'b' then do pure PUnit.unit; pure (ForInStep.yield (r ++ [c]))
      else do pure PUnit.unit; pure (ForInStep.yield r))) = init ++ stripBinary xs := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, Id.run, stripBinary, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : a = 'b'
    · simp only [h, ne_eq, not_true_eq_false, if_false]
      rw [ih]
      simp [stripBinary]
    · simp only [h, ne_eq, not_false_eq_true, if_true]
      rw [ih, List.append_assoc]
      simp [stripBinary, h]

theorem correct_mode : ∀ bufferMode : List Char,
    problem_spec_mode bufferMode (implementation_mode bufferMode) := by
  intro bufferMode
  unfold problem_spec_mode implementation_mode
  have h2 : (Id.run do
      let mut acc : List Char := []
      for c in bufferMode do
        if c ≠ 'b' then
          acc := acc ++ [c]
      return acc) = Id.run (forIn bufferMode ([] : List Char) (fun c r =>
      if c ≠ 'b' then do pure PUnit.unit; pure (ForInStep.yield (r ++ [c]))
      else do pure PUnit.unit; pure (ForInStep.yield r))) := rfl
  rw [h2, mode_forIn_helper]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_mode bufferMode result := result = stripBinary bufferMode. Total functional equality over ALL bufferMode:List Char, NO precondition, EMPTY axioms region. Any impl differing from gold on any input cannot close correct_mode.

All work same_spec=True verified for all 6 attacks (swebench_unified.markers.same_spec, lean backend; only impl+proof regions edited, which the spec-view elides). Verify cmd: `bash scripts/lean_verify.sh <f>` run. Verifications launched concurrently in two batches of <=4 background jobs.

POSITIVE CONTROL (positive_control.lean = gold): EXIT 0; `#print axioms correct_mode` => 'depends on axioms: [propext, Quot.sound]' (standard Mathlib, no sorry).

### ATTACKS (all EXIT 1 except the gold-equivalent echo):
- atk_1 prepatch identity bug (keeps 'b'): EXIT 1, residual goal contains unprovable ne_eq / stripBinary mismatch. Reproduces the prepatch bug (no mode property -> mode returned verbatim with 'b').
- atk_2 partial-domain (drops only a leading 'b', match head): EXIT 1, residual `as = stripBinary as`.
- atk_3 boundary/order (reverse.filter): EXIT 1, residual `stripBinary as ++ [a] = a :: stripBinary as`.
- atk_4 control-flow-effect (removes 'a' instead of 'b'): EXIT 1, forIn residual != a :: stripBinary as.
- atk_5 over-removal (filters out both 'b' and 't'): EXIT 1, residual mismatch on the true branch.
- atk_6 ungrounded-oracle echo (implementation_mode := stripBinary bufferMode, gold-EXTENSIONALLY-equivalent): EXIT 0; `#print axioms correct_mode` => 'does not depend on any axioms' (clean, no sorry). Proof closes by rfl.

MANDATORY RESOLVE STEP: atk_6 is the only verifying attack. Materialized its faithful refined patch (atk_6.patch, byte-identical to the gold patch: adds `mode` property returning self.buffer.mode.replace("b","")). Ran harness.run_resolve('pytest-dev__pytest-5262', patch, timeout=1200) via swebench-lean venv => RESOLVED: True. Per the 2026-08-06 G-EQ/panel-1 policy, a same-spec verifying attack whose faithful patch RESOLVES is NOT a weakness (a resolving echo of the gold). No verify=>!correct gap: every genuinely-wrong impl (atk_1..5) fails to close, and the only closing impl (atk_6) is gold-equivalent AND resolves.

REFINEMENT.MD AUDIT: 5 legs — row1 R (str<->List Char), rows 2/3/5 I, row 4 A-reference (str.replace("b","") modeled deeply as stripBinary; NOT axiomatized; empty axioms region). No kind-3 (changed-inexpressible) legs, no A-consumed rows. A-reference correspondence holds: single-char str.replace removes every occurrence of that char and preserves the order of all others — exactly stripBinary's front-recursive fold. Consistent with mapping.md (per-code-point str<->List Char bijection) and the F2P observation ('b' not in reported mode), with the spec pinning the full transformation rather than mere 'b absent'.

CONCLUSION: The spec is a tight total functional equality with an empty axioms region and no precondition. 6 attacks run (>=5 required); none breaks it. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: the mode-string
-- transformation is modeled DEEPLY (a per-character filter, below) rather than
-- axiomatized, so its standard-library reference is validated as an A-reference
-- by G-AX. The proof agent may add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- Front-recursive specification fold over the underlying stream's mode string:
keep every character except the binary-indicator character `'b'`, in order. -/
def stripBinary : List Char → List Char
  | [] => []
  | c :: cs => if c = 'b' then stripBinary cs else c :: stripBinary cs
-- pure-end

-- post-conditions-start
/-- The reported text-stream mode is exactly the underlying stream's mode string
with every binary-indicator character `'b'` removed and every other character
preserved in its original order. -/
def problem_spec_mode (bufferMode : List Char) (result : List Char) : Prop :=
  result = stripBinary bufferMode
-- post-conditions-end

-- impl-start
def implementation_mode (bufferMode : List Char) : List Char := Id.run do
  let mut acc : List Char := []
  for c in bufferMode do
    if c ≠ 'b' then
      acc := acc ++ [c]
  return acc
-- impl-end

-- proof-start
/-- Helper: the cleaned `forIn` accumulation, generalized over the accumulator,
equals the initial accumulator appended with the front-recursive `stripBinary`. -/
theorem mode_forIn_helper (xs : List Char) (init : List Char) :
    Id.run (forIn xs init (fun c r =>
      if c ≠ 'b' then do pure PUnit.unit; pure (ForInStep.yield (r ++ [c]))
      else do pure PUnit.unit; pure (ForInStep.yield r))) = init ++ stripBinary xs := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, Id.run, stripBinary, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : a = 'b'
    · simp only [h, ne_eq, not_true_eq_false, if_false]
      rw [ih]
      simp [stripBinary]
    · simp only [h, ne_eq, not_false_eq_true, if_true]
      rw [ih, List.append_assoc]
      simp [stripBinary, h]

theorem correct_mode : ∀ bufferMode : List Char,
    problem_spec_mode bufferMode (implementation_mode bufferMode) := by
  intro bufferMode
  unfold problem_spec_mode implementation_mode
  have h2 : (Id.run do
      let mut acc : List Char := []
      for c in bufferMode do
        if c ≠ 'b' then
          acc := acc ++ [c]
      return acc) = Id.run (forIn bufferMode ([] : List Char) (fun c r =>
      if c ≠ 'b' then do pure PUnit.unit; pure (ForInStep.yield (r ++ [c]))
      else do pure PUnit.unit; pure (ForInStep.yield r))) := rfl
  rw [h2, mode_forIn_helper]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_mode bufferMode result := result = stripBinary bufferMode. Total functional equality over ALL bufferMode:List Char, NO precondition, EMPTY axioms region. Any impl differing from gold on any input cannot close correct_mode.

All work same_spec=True verified for all 6 attacks (swebench_unified.markers.same_spec, lean backend; only impl+proof regions edited, which the spec-view elides). Verify cmd: `bash scripts/lean_verify.sh <f>` run. Verifications launched concurrently in two batches of <=4 background jobs.

POSITIVE CONTROL (positive_control.lean = gold): EXIT 0; `#print axioms correct_mode` => 'depends on axioms: [propext, Quot.sound]' (standard Mathlib, no sorry).

### ATTACKS (all EXIT 1 except the gold-equivalent echo):
- atk_1 prepatch identity bug (keeps 'b'): EXIT 1, residual goal contains unprovable ne_eq / stripBinary mismatch. Reproduces the prepatch bug (no mode property -> mode returned verbatim with 'b').
- atk_2 partial-domain (drops only a leading 'b', match head): EXIT 1, residual `as = stripBinary as`.
- atk_3 boundary/order (reverse.filter): EXIT 1, residual `stripBinary as ++ [a] = a :: stripBinary as`.
- atk_4 control-flow-effect (removes 'a' instead of 'b'): EXIT 1, forIn residual != a :: stripBinary as.
- atk_5 over-removal (filters out both 'b' and 't'): EXIT 1, residual mismatch on the true branch.
- atk_6 ungrounded-oracle echo (implementation_mode := stripBinary bufferMode, gold-EXTENSIONALLY-equivalent): EXIT 0; `#print axioms correct_mode` => 'does not depend on any axioms' (clean, no sorry). Proof closes by rfl.

MANDATORY RESOLVE STEP: atk_6 is the only verifying attack. Materialized its faithful refined patch (atk_6.patch, byte-identical to the gold patch: adds `mode` property returning self.buffer.mode.replace("b","")). Ran harness.run_resolve('pytest-dev__pytest-5262', patch, timeout=1200) via swebench-lean venv => RESOLVED: True. Per the 2026-08-06 G-EQ/panel-1 policy, a same-spec verifying attack whose faithful patch RESOLVES is NOT a weakness (a resolving echo of the gold). No verify=>!correct gap: every genuinely-wrong impl (atk_1..5) fails to close, and the only closing impl (atk_6) is gold-equivalent AND resolves.

REFINEMENT.MD AUDIT: 5 legs — row1 R (str<->List Char), rows 2/3/5 I, row 4 A-reference (str.replace("b","") modeled deeply as stripBinary; NOT axiomatized; empty axioms region). No kind-3 (changed-inexpressible) legs, no A-consumed rows. A-reference correspondence holds: single-char str.replace removes every occurrence of that char and preserves the order of all others — exactly stripBinary's front-recursive fold. Consistent with mapping.md (per-code-point str<->List Char bijection) and the F2P observation ('b' not in reported mode), with the spec pinning the full transformation rather than mere 'b absent'.

CONCLUSION: The spec is a tight total functional equality with an empty axioms region and no precondition. 6 attacks run (>=5 required); none breaks it. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function implementation_mode/problem_spec_mode pins result = stripBinary bufferMode (drop every 'b', preserve all other chars in order). Real callee (post-patch capture.py:mode) is `return self.buffer.mode.replace('b','')`. For a single-character needle 'b' (ASCII U+0062, no overlap subtleties), str.replace removes every occurrence code-point-wise — exactly stripBinary under the str↔List Char bijection. buffer.mode is a plain framing attribute read with no transformation, correctly taken as the input. Verified: Solution.lean compiles via lean_verify.sh (exit 0); `#print axioms correct_mode` = [propext, Quot.sound] only, no sorryAx (proof genuine). Fuzzed 300k inputs over mode-flavored alphabet + BMP/astral code points + combining marks: 0 divergences. Corroborated by recorded G-AX (stripBinary == str.replace('b','') on all probes, seed 5262) and G-CONF (120017 inputs, 0 disagreements). Spec is neither too strong nor too weak; no diverging input exists. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker (3) leakage / gold-reconstruction judgment for pytest-dev__pytest-5262 (lean).

Mechanical screen: leakage.screen() passes (hard_failures=[]); spec region byte-identical (same_spec True). Patch changed symbols = {mode, name}; changed lines = ['@property','def mode(self):','return self.buffer.mode.replace("b","")'].

Gold edit adds `@property def mode(self): return self.buffer.mode.replace("b", "")` in src/_pytest/capture.py.

Public problem_statement already discloses: (a) 'mode should not include `b` (binary)'; (b) EncodedFile 'incorrectly advertises rb+, the mode of the underlying stream'; (c) 'youtube-dl looks for b in out.mode'. So the public task already names the `mode` attribute, the underlying stream's mode, and the requirement that `b` be absent.

Spec view (visible regions): stripBinary (keep every char except 'b', in order) + problem_spec_mode (result = stripBinary bufferMode) + abstract prose about the underlying stream's mode string. impl and proof regions are elided.

Assessment — no leakage beyond problem_statement:
- No gold-patch line reproduced (no str.replace("b",""), no @property, no def mode).
- No patched file path (src/_pytest/capture.py) or dotted module path in view.
- No diff markers.
- No narration terms (bug/fix/patch/etc.) in spec-view comments.
- Only patched symbol echoed is `mode`, which is already public in the problem_statement; `name` (the other changed symbol) does not appear.
- The precision 'remove every b, preserve everything else in order' is the correctness spec grounded in the public 'no b' requirement, not a disclosure of the edit's location/mechanics. A solver still must discover where and how to add the property.

Conclusion: the spec view is a faithful behavioral spec derivable from the public problem_statement and does not leak the gold edit. Verdict NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
