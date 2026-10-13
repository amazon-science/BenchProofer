# P2 adversarial audit — pydata__xarray-4075

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,41 +38,19 @@
 
 -- impl-start
 def implementation_sumOfWeights (mask weights : List Bool) : Option Int := Id.run do
-  let mut acc : Int := 0
+  let mut acc : Bool := false
   for (m, w) in mask.zip weights do
     if m && w then
-      acc := acc + 1
-  if acc = 0 then
+      acc := acc || true
+  if acc = false then
     return none
-  return some acc
+  return some 1
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` accumulation loop equals the front-recursive `zipDot`
-fold, offset by the initial accumulator value. Generalized over `init` so the
-induction goes through. -/
-theorem fold_helper (xs : List (Bool × Bool)) (init : Int) :
-    Id.run (forIn xs init (fun x r =>
-      if (x.1 && x.2) = true then pure (ForInStep.yield (r + 1))
-      else pure (ForInStep.yield r))) = init + zipDot xs := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, zipDot, add_zero]; rfl
-  | cons a as ih =>
-    obtain ⟨m, w⟩ := a
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (m && w) = true
-    · simp only [h, if_true, ih, zipDot]; ring
-    · simp only [Bool.not_eq_true] at h
-      simp only [h, Bool.false_eq_true, if_false, ih, zipDot]; ring
-
 theorem correct_sumOfWeights : ∀ (mask weights : List Bool),
     mask.length = weights.length →
     problem_spec_sumOfWeights mask weights
       (implementation_sumOfWeights mask weights) := by
-  intro mask weights _
-  unfold problem_spec_sumOfWeights implementation_sumOfWeights sowSpec
-  have hf := fold_helper (mask.zip weights) 0
-  simp only [Id.run, zero_add, bind, pure] at hf ⊢
-  rw [hf]
+  sorry -- prepatch: cannot close honest theorem
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -42,37 +42,14 @@
   for (m, w) in mask.zip weights do
     if m && w then
       acc := acc + 1
-  if acc = 0 then
-    return none
   return some acc
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` accumulation loop equals the front-recursive `zipDot`
-fold, offset by the initial accumulator value. Generalized over `init` so the
-induction goes through. -/
-theorem fold_helper (xs : List (Bool × Bool)) (init : Int) :
-    Id.run (forIn xs init (fun x r =>
-      if (x.1 && x.2) = true then pure (ForInStep.yield (r + 1))
-      else pure (ForInStep.yield r))) = init + zipDot xs := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, zipDot, add_zero]; rfl
-  | cons a as ih =>
-    obtain ⟨m, w⟩ := a
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (m && w) = true
-    · simp only [h, if_true, ih, zipDot]; ring
-    · simp only [Bool.not_eq_true] at h
-      simp only [h, Bool.false_eq_true, if_false, ih, zipDot]; ring
-
 theorem correct_sumOfWeights : ∀ (mask weights : List Bool),
     mask.length = weights.length →
     problem_spec_sumOfWeights mask weights
       (implementation_sumOfWeights mask weights) := by
-  intro mask weights _
-  unfold problem_spec_sumOfWeights implementation_sumOfWeights sowSpec
-  have hf := fold_helper (mask.zip weights) 0
-  simp only [Id.run, zero_add, bind, pure] at hf ⊢
-  rw [hf]
+  intro mask weights h
+  sorry
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,38 +41,17 @@
   let mut acc : Int := 0
   for (m, w) in mask.zip weights do
     if m && w then
-      acc := acc + 1
+      acc := acc + 2
   if acc = 0 then
     return none
   return some acc
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` accumulation loop equals the front-recursive `zipDot`
-fold, offset by the initial accumulator value. Generalized over `init` so the
-induction goes through. -/
-theorem fold_helper (xs : List (Bool × Bool)) (init : Int) :
-    Id.run (forIn xs init (fun x r =>
-      if (x.1 && x.2) = true then pure (ForInStep.yield (r + 1))
-      else pure (ForInStep.yield r))) = init + zipDot xs := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, zipDot, add_zero]; rfl
-  | cons a as ih =>
-    obtain ⟨m, w⟩ := a
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (m && w) = true
-    · simp only [h, if_true, ih, zipDot]; ring
-    · simp only [Bool.not_eq_true] at h
-      simp only [h, Bool.false_eq_true, if_false, ih, zipDot]; ring
-
 theorem correct_sumOfWeights : ∀ (mask weights : List Bool),
     mask.length = weights.length →
     problem_spec_sumOfWeights mask weights
       (implementation_sumOfWeights mask weights) := by
-  intro mask weights _
-  unfold problem_spec_sumOfWeights implementation_sumOfWeights sowSpec
-  have hf := fold_helper (mask.zip weights) 0
-  simp only [Id.run, zero_add, bind, pure] at hf ⊢
-  rw [hf]
+  intro mask weights h
+  sorry
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,7 @@
 def implementation_sumOfWeights (mask weights : List Bool) : Option Int := Id.run do
   let mut acc : Int := 0
   for (m, w) in mask.zip weights do
-    if m && w then
+    if m || w then
       acc := acc + 1
   if acc = 0 then
     return none
@@ -48,31 +48,10 @@
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` accumulation loop equals the front-recursive `zipDot`
-fold, offset by the initial accumulator value. Generalized over `init` so the
-induction goes through. -/
-theorem fold_helper (xs : List (Bool × Bool)) (init : Int) :
-    Id.run (forIn xs init (fun x r =>
-      if (x.1 && x.2) = true then pure (ForInStep.yield (r + 1))
-      else pure (ForInStep.yield r))) = init + zipDot xs := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, zipDot, add_zero]; rfl
-  | cons a as ih =>
-    obtain ⟨m, w⟩ := a
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (m && w) = true
-    · simp only [h, if_true, ih, zipDot]; ring
-    · simp only [Bool.not_eq_true] at h
-      simp only [h, Bool.false_eq_true, if_false, ih, zipDot]; ring
-
 theorem correct_sumOfWeights : ∀ (mask weights : List Bool),
     mask.length = weights.length →
     problem_spec_sumOfWeights mask weights
       (implementation_sumOfWeights mask weights) := by
-  intro mask weights _
-  unfold problem_spec_sumOfWeights implementation_sumOfWeights sowSpec
-  have hf := fold_helper (mask.zip weights) 0
-  simp only [Id.run, zero_add, bind, pure] at hf ⊢
-  rw [hf]
+  intro mask weights h
+  sorry
 -- proof-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -37,42 +37,16 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_sumOfWeights (mask weights : List Bool) : Option Int := Id.run do
-  let mut acc : Int := 0
-  for (m, w) in mask.zip weights do
-    if m && w then
-      acc := acc + 1
-  if acc = 0 then
-    return none
-  return some acc
+def implementation_sumOfWeights (mask weights : List Bool) : Option Int :=
+  sowSpec mask weights
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` accumulation loop equals the front-recursive `zipDot`
-fold, offset by the initial accumulator value. Generalized over `init` so the
-induction goes through. -/
-theorem fold_helper (xs : List (Bool × Bool)) (init : Int) :
-    Id.run (forIn xs init (fun x r =>
-      if (x.1 && x.2) = true then pure (ForInStep.yield (r + 1))
-      else pure (ForInStep.yield r))) = init + zipDot xs := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, zipDot, add_zero]; rfl
-  | cons a as ih =>
-    obtain ⟨m, w⟩ := a
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (m && w) = true
-    · simp only [h, if_true, ih, zipDot]; ring
-    · simp only [Bool.not_eq_true] at h
-      simp only [h, Bool.false_eq_true, if_false, ih, zipDot]; ring
-
 theorem correct_sumOfWeights : ∀ (mask weights : List Bool),
     mask.length = weights.length →
     problem_spec_sumOfWeights mask weights
       (implementation_sumOfWeights mask weights) := by
   intro mask weights _
-  unfold problem_spec_sumOfWeights implementation_sumOfWeights sowSpec
-  have hf := fold_helper (mask.zip weights) 0
-  simp only [Id.run, zero_add, bind, pure] at hf ⊢
-  rw [hf]
+  unfold problem_spec_sumOfWeights
+  rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -37,42 +37,16 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_sumOfWeights (mask weights : List Bool) : Option Int := Id.run do
-  let mut acc : Int := 0
-  for (m, w) in mask.zip weights do
-    if m && w then
-      acc := acc + 1
-  if acc = 0 then
-    return none
-  return some acc
+def implementation_sumOfWeights (mask weights : List Bool) : Option Int :=
+  if mask.length = weights.length then sowSpec mask weights else some 999
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` accumulation loop equals the front-recursive `zipDot`
-fold, offset by the initial accumulator value. Generalized over `init` so the
-induction goes through. -/
-theorem fold_helper (xs : List (Bool × Bool)) (init : Int) :
-    Id.run (forIn xs init (fun x r =>
-      if (x.1 && x.2) = true then pure (ForInStep.yield (r + 1))
-      else pure (ForInStep.yield r))) = init + zipDot xs := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, zipDot, add_zero]; rfl
-  | cons a as ih =>
-    obtain ⟨m, w⟩ := a
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (m && w) = true
-    · simp only [h, if_true, ih, zipDot]; ring
-    · simp only [Bool.not_eq_true] at h
-      simp only [h, Bool.false_eq_true, if_false, ih, zipDot]; ring
-
 theorem correct_sumOfWeights : ∀ (mask weights : List Bool),
     mask.length = weights.length →
     problem_spec_sumOfWeights mask weights
       (implementation_sumOfWeights mask weights) := by
-  intro mask weights _
-  unfold problem_spec_sumOfWeights implementation_sumOfWeights sowSpec
-  have hf := fold_helper (mask.zip weights) 0
-  simp only [Id.run, zero_add, bind, pure] at hf ⊢
-  rw [hf]
+  intro mask weights h
+  unfold problem_spec_sumOfWeights implementation_sumOfWeights
+  rw [if_pos h]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -39,40 +39,23 @@
 -- impl-start
 def implementation_sumOfWeights (mask weights : List Bool) : Option Int := Id.run do
   let mut acc : Int := 0
+  let mut first : Bool := true
   for (m, w) in mask.zip weights do
     if m && w then
-      acc := acc + 1
+      if first then
+        first := false   -- skip counting the first matched pair (off-by-one)
+      else
+        acc := acc + 1
   if acc = 0 then
     return none
   return some acc
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` accumulation loop equals the front-recursive `zipDot`
-fold, offset by the initial accumulator value. Generalized over `init` so the
-induction goes through. -/
-theorem fold_helper (xs : List (Bool × Bool)) (init : Int) :
-    Id.run (forIn xs init (fun x r =>
-      if (x.1 && x.2) = true then pure (ForInStep.yield (r + 1))
-      else pure (ForInStep.yield r))) = init + zipDot xs := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, zipDot, add_zero]; rfl
-  | cons a as ih =>
-    obtain ⟨m, w⟩ := a
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (m && w) = true
-    · simp only [h, if_true, ih, zipDot]; ring
-    · simp only [Bool.not_eq_true] at h
-      simp only [h, Bool.false_eq_true, if_false, ih, zipDot]; ring
-
 theorem correct_sumOfWeights : ∀ (mask weights : List Bool),
     mask.length = weights.length →
     problem_spec_sumOfWeights mask weights
       (implementation_sumOfWeights mask weights) := by
-  intro mask weights _
-  unfold problem_spec_sumOfWeights implementation_sumOfWeights sowSpec
-  have hf := fold_helper (mask.zip weights) 0
-  simp only [Id.run, zero_add, bind, pure] at hf ⊢
-  rw [hf]
+  intro mask weights h
+  sorry
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is invoked by the modeled behavior. The element-wise
-- multiply-and-accumulate reduction (the array contraction used to combine the
-- not-null mask with the weights) is modeled DEEPLY below (`zipDot`/`sowSpec`),
-- so there is no `opaque` callee and no consumed `_prop` axiom here.
-- axioms-end

-- pure-start
/-- Element-wise combine-and-accumulate of a not-null mask with a sequence of
boolean weights, evaluated in integer arithmetic: each position contributes `1`
exactly when both its mask flag and its weight are set, and `0` otherwise; the
contributions are summed in input order (a front-recursive fold). -/
def zipDot : List (Bool × Bool) → Int
  | [] => 0
  | (m, w) :: rest => (if m && w then 1 else 0) + zipDot rest

/-- Aggregate weight associated with the retained (not-null) entries. It is the
integer-valued accumulation of the per-position contributions; a total of `0` is
treated as the absence of a valid aggregate (`none`), every positive total is
reported as `some` of that total. -/
def sowSpec (mask weights : List Bool) : Option Int :=
  let s := zipDot (mask.zip weights)
  if s = 0 then none else some s
-- pure-end

-- post-conditions-start
/-- The result is the aggregate weight of the entries kept by the not-null mask:
each kept position whose weight is set adds one unit, the units are summed in
integer arithmetic over the paired sequences, and a total of zero is reported as
the absence of a valid aggregate. -/
def problem_spec_sumOfWeights
    (mask weights : List Bool) (result : Option Int) : Prop :=
  result = sowSpec mask weights
-- post-conditions-end

-- impl-start
def implementation_sumOfWeights (mask weights : List Bool) : Option Int := Id.run do
  let mut acc : Int := 0
  for (m, w) in mask.zip weights do
    if m && w then
      acc := acc + 1
  if acc = 0 then
    return none
  return some acc
-- impl-end

-- proof-start
theorem fold_helper (xs : List (Bool × Bool)) (init : Int) :
    Id.run (forIn xs init (fun x r =>
      if (x.1 && x.2) = true then pure (ForInStep.yield (r + 1))
      else pure (ForInStep.yield r))) = init + zipDot xs := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, Id.run, zipDot, add_zero]; rfl
  | cons a as ih =>
    obtain ⟨m, w⟩ := a
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : (m && w) = true
    · simp only [h, if_true, ih, zipDot]; ring
    · simp only [Bool.not_eq_true] at h
      simp only [h, Bool.false_eq_true, if_false, ih, zipDot]; ring

theorem correct_sumOfWeights : ∀ (mask weights : List Bool),
    mask.length = weights.length →
    problem_spec_sumOfWeights mask weights
      (implementation_sumOfWeights mask weights) := by
  intro mask weights _
  unfold problem_spec_sumOfWeights implementation_sumOfWeights sowSpec
  have hf := fold_helper (mask.zip weights) 0
  simp only [Id.run, zero_add, bind, pure] at hf ⊢
  rw [hf]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec: problem_spec_sumOfWeights = (result = sowSpec mask weights), a TOTAL extensional equality over all equal-length boolean lists, so the correct_sumOfWeights obligation pins the function exactly on the modeled (equal-length) domain. same_spec elides the ENTIRE proof region (incl. the correct_ theorem header) — verified via _lean_spec_view — so attacks may rewrite the proof but the honest theorem statement (full domain, spec=sowSpec) was kept byte-faithful in every attack; a weakened impl therefore cannot close it.

7 attacks, all same_spec=True (confirmed by swebench_unified.markers.same_spec). lean_verify.sh (300s cap) results:
- atk_1 prepatch (boolean-OR contraction, saturates at some 1): exit 3 (sorry) — unclosable, reproduces GH4074 bug.
- atk_2 partial-domain (drops zero->none, returns some 0 on all-false): exit 3 — rejected.
- atk_3 boundary (+2 per hit): exit 3 — rejected.
- atk_4 control-flow-effect (m||w instead of m&&w): exit 3 — rejected.
- atk_7 off-by-one (skip first matched pair): exit 3 — rejected.
- atk_5 ungrounded-oracle echo (= sowSpec): exit 0, clean axioms ("does not depend on any axioms") -> CANDIDATE. Faithful patch = gold integer-cast fix; run_resolve('pydata__xarray-4075') => RESOLVED=True COMPLETED=True. Correct echo, not a weakness.
- atk_6 precondition-exploit (if length eq then sowSpec else some 999): exit 0, clean axioms -> CANDIDATE. On the reachable domain notnull() mask always matches weights shape so length-guard is always true => gold behavior. Faithful patch = gold fix; run_resolve => RESOLVED=True COMPLETED=True. Correct echo.

Positive control (gold impl, ctrl.lean): exit 0; #print axioms => [propext, Quot.sound] (clean, no sorryAx).

No same-spec verifying impl has a faithful patch that fails to resolve (verify=>correct holds). refinement.md legs: R / R+A-reference / A-reference / I — no kind-3 changed-inexpressible leg; the sole A-reference (zipDot == integer xr.dot on cast inputs) is the exact bug/fix boundary and is machine-validated by axiom_check.py (G-AX pass, 120007 inputs, seed 4075). Model<->patch correspondence (bool->int cast modeled as integer accumulation) holds. Commands: python -c '...same_spec...' (all True); bash scripts/lean_verify.sh <atk>.lean; #print axioms via appended directive; run_resolve via swebench_unified.harness.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is invoked by the modeled behavior. The element-wise
-- multiply-and-accumulate reduction (the array contraction used to combine the
-- not-null mask with the weights) is modeled DEEPLY below (`zipDot`/`sowSpec`),
-- so there is no `opaque` callee and no consumed `_prop` axiom here.
-- axioms-end

-- pure-start
/-- Element-wise combine-and-accumulate of a not-null mask with a sequence of
boolean weights, evaluated in integer arithmetic: each position contributes `1`
exactly when both its mask flag and its weight are set, and `0` otherwise; the
contributions are summed in input order (a front-recursive fold). -/
def zipDot : List (Bool × Bool) → Int
  | [] => 0
  | (m, w) :: rest => (if m && w then 1 else 0) + zipDot rest

/-- Aggregate weight associated with the retained (not-null) entries. It is the
integer-valued accumulation of the per-position contributions; a total of `0` is
treated as the absence of a valid aggregate (`none`), every positive total is
reported as `some` of that total. -/
def sowSpec (mask weights : List Bool) : Option Int :=
  let s := zipDot (mask.zip weights)
  if s = 0 then none else some s
-- pure-end

-- post-conditions-start
/-- The result is the aggregate weight of the entries kept by the not-null mask:
each kept position whose weight is set adds one unit, the units are summed in
integer arithmetic over the paired sequences, and a total of zero is reported as
the absence of a valid aggregate. -/
def problem_spec_sumOfWeights
    (mask weights : List Bool) (result : Option Int) : Prop :=
  result = sowSpec mask weights
-- post-conditions-end

-- impl-start
def implementation_sumOfWeights (mask weights : List Bool) : Option Int := Id.run do
  let mut acc : Int := 0
  for (m, w) in mask.zip weights do
    if m && w then
      acc := acc + 1
  if acc = 0 then
    return none
  return some acc
-- impl-end

-- proof-start
theorem fold_helper (xs : List (Bool × Bool)) (init : Int) :
    Id.run (forIn xs init (fun x r =>
      if (x.1 && x.2) = true then pure (ForInStep.yield (r + 1))
      else pure (ForInStep.yield r))) = init + zipDot xs := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, Id.run, zipDot, add_zero]; rfl
  | cons a as ih =>
    obtain ⟨m, w⟩ := a
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : (m && w) = true
    · simp only [h, if_true, ih, zipDot]; ring
    · simp only [Bool.not_eq_true] at h
      simp only [h, Bool.false_eq_true, if_false, ih, zipDot]; ring

theorem correct_sumOfWeights : ∀ (mask weights : List Bool),
    mask.length = weights.length →
    problem_spec_sumOfWeights mask weights
      (implementation_sumOfWeights mask weights) := by
  intro mask weights _
  unfold problem_spec_sumOfWeights implementation_sumOfWeights sowSpec
  have hf := fold_helper (mask.zip weights) 0
  simp only [Id.run, zero_add, bind, pure] at hf ⊢
  rw [hf]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec: problem_spec_sumOfWeights = (result = sowSpec mask weights), a TOTAL extensional equality over all equal-length boolean lists, so the correct_sumOfWeights obligation pins the function exactly on the modeled (equal-length) domain. same_spec elides the ENTIRE proof region (incl. the correct_ theorem header) — verified via _lean_spec_view — so attacks may rewrite the proof but the honest theorem statement (full domain, spec=sowSpec) was kept byte-faithful in every attack; a weakened impl therefore cannot close it.

7 attacks, all same_spec=True (confirmed by swebench_unified.markers.same_spec). lean_verify.sh (300s cap) results:
- atk_1 prepatch (boolean-OR contraction, saturates at some 1): exit 3 (sorry) — unclosable, reproduces GH4074 bug.
- atk_2 partial-domain (drops zero->none, returns some 0 on all-false): exit 3 — rejected.
- atk_3 boundary (+2 per hit): exit 3 — rejected.
- atk_4 control-flow-effect (m||w instead of m&&w): exit 3 — rejected.
- atk_7 off-by-one (skip first matched pair): exit 3 — rejected.
- atk_5 ungrounded-oracle echo (= sowSpec): exit 0, clean axioms ("does not depend on any axioms") -> CANDIDATE. Faithful patch = gold integer-cast fix; run_resolve('pydata__xarray-4075') => RESOLVED=True COMPLETED=True. Correct echo, not a weakness.
- atk_6 precondition-exploit (if length eq then sowSpec else some 999): exit 0, clean axioms -> CANDIDATE. On the reachable domain notnull() mask always matches weights shape so length-guard is always true => gold behavior. Faithful patch = gold fix; run_resolve => RESOLVED=True COMPLETED=True. Correct echo.

Positive control (gold impl, ctrl.lean): exit 0; #print axioms => [propext, Quot.sound] (clean, no sorryAx).

No same-spec verifying impl has a faithful patch that fails to resolve (verify=>correct holds). refinement.md legs: R / R+A-reference / A-reference / I — no kind-3 changed-inexpressible leg; the sole A-reference (zipDot == integer xr.dot on cast inputs) is the exact bug/fix boundary and is machine-validated by axiom_check.py (G-AX pass, 120007 inputs, seed 4075). Model<->patch correspondence (bool->int cast modeled as integer accumulation) holds. Commands: python -c '...same_spec...' (all True); bash scripts/lean_verify.sh <atk>.lean; #print axioms via appended directive; run_resolve via swebench_unified.harness.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) assessment for pydata__xarray-4075 lean bundle.

Modeled function: Weighted._sum_of_weights (boolean-weights branch), spec = sowSpec/zipDot: integer count of positions where (mask_i AND weight_i), total 0 -> none, positive -> some. Post-patch real callee: xr.dot(notnull-mask, weights.astype(int), dims=all).where(sum != 0.0).

Evidence the spec does NOT drift from / is not stronger than real repo behavior:
1. same_spec(post, prepatch, lean) = True — the post-conditions+pure spec region is byte-identical between Solution.lean and Solution_prepatch.lean; the F2P discriminator lives entirely in impl/proof, as required. Spec region parses cleanly via swebench_unified.markers.spec_view.
2. Solution.lean compiles under lean_verify.sh (exit 0). #print axioms correct_sumOfWeights => [propext, Quot.sound] only; NO sorryAx, proof is genuine.
3. axiom_check.py (G-AX): deep model zipDot == real xr.dot(mask, weights.astype(int)) on 120,007 inputs (fixed + fuzz, seed 4075), 0 mismatches.
4. conformance_check.py (G-CONF): 120,007 inputs, 0 disagreements between R/I shadow and independent post-patch reconstruction.
5. Independent differential (my own, not the auditor scripts): pure Lean spec formula vs a faithful reconstruction of the patched _sum_of_weights body (astype(int) branch, .where(!=0)) over 30,009 cases including empty lists, zero-total->none, single-element, unequal set patterns — 0 divergences. Confirmed the installed xarray is v0.15.1 (pre-patch: public sum_of_weights([1,2],[T,T])==1), which is exactly why the patched behavior must be reconstructed from the gold patch; reconstruction matches the patch text verbatim.
6. Term-by-term soundness: each dot term = int(mask_i)*int(weight_i) in {0,1}, summed = count = zipDot; .where(sum!=0.0) maps 0->NaN->none; exact at large counts (100000 all-true -> 100000.0, no float rounding at the !=0 boundary). Equal-length precondition mirrors dot alignment. List.zip truncation is a non-issue since precondition forces equal length.

No input found where the modeled function disagrees with the real callee within the declared modeled domain (boolean weights, equal-length 1-D full reduction). The spec is neither too strong nor drifted. VERDICT: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently verified. (1) markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) => True: spec regions (axioms/pure/post-conditions) plus the impl/proof-elided spec_view are byte-identical between gold and prepatch, so the spec itself does not encode the discriminator; the bug lives entirely in the elided impl/proof. (2) Mechanical leakage.screen passes with zero hard failures (no diff markers, no reproduced gold-patch line, no patched file path 'xarray/core/weighted.py', no spec-view identifier or comment echoing the one distinctive changed symbol 'sum_of_weights', no bug/fix narration).

Semantic assessment vs PUBLIC problem_statement only (hints_text empty): the problem_statement is unusually explicit and already discloses the fix at full behavioral fidelity — it states sum_of_weights is computed as xr.dot(dta.notnull(), wgt) yielding boolean array(True), and explicitly instructs 'We'll need to convert it to int or float: xr.dot(dta.notnull(), wgt * 1) which is correct ... array(2)'. So the integer-count-instead-of-boolean-saturation semantics is already public.

The spec view models the reduction as zipDot/sowSpec = an integer multiply-and-accumulate (each notnull-mask & set-weight pair contributes 1, summed in integer arithmetic; zero total -> none). That integer-count-of-kept-positions behavior is exactly what the issue publishes (result 2, not True=1); the zero->none masking mirrors the pre-existing unchanged .where(!=0.0). The spec view contains NO astype(int), NO weights.dtype==bool flag, NO GH4074 reference, NO diff/prepatch/bug language, and no mention of the boolean-OR saturation that is the actual defect. Those gold-specific reconstruction details live only in refinement.md / mapping.md / Solution_prepatch.lean, which are auditor artifacts outside the consumer spec view. The spec view stays at the behavioral abstraction level already published in problem_statement and does not leak the gold edit beyond it. No relaxed_leakage marker present (standard strict bundle); none needed.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
