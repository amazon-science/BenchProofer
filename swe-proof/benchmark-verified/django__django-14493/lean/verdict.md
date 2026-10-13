# P2 adversarial audit — django__django-14493

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl closes; every attack fails with a genuine `rfl` elaboration error (not sorry/timeout), so protocol step 2 (materialize+resolve) had no candidate patches to run. The spec `result = some (passLoopResult (List.range maxPasses) passSubst false)` is a TOTAL FUNCTIONAL EQUALITY pinning `result` uniquely per input, so any closing impl is extensionally identical to gold everywhere — in particular at the discriminating input maxPasses=0 where it MUST return `some false` (defined flag), which is precisely the behavioral content of the gold edit (`substitutions = False` before the loop). closing ⟹ resolving.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,10 +64,11 @@
   result = some (passLoopResult (List.range maxPasses) passSubst false)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_postProcess
     (maxPasses : Nat) (passSubst : Nat → Bool) : Option Bool := Id.run do
-  let mut substitutions : Option Bool := some false
+  let mut substitutions : Option Bool := none
   for i in List.range maxPasses do
     let subst := passSubst i
     substitutions := some subst
@@ -82,27 +83,8 @@
       problem_spec_postProcess maxPasses passSubst
         (implementation_postProcess maxPasses passSubst) := by
   intro maxPasses passSubst
-  have helper : ∀ (is : List Nat) (cur : Bool),
-      Id.run (forIn is (some cur) (fun i r =>
-        if (!passSubst i) = true then pure (ForInStep.done (some (passSubst i)))
-        else do
-          pure PUnit.unit
-          pure (ForInStep.yield (some (passSubst i))))) =
-        some (passLoopResult is passSubst cur) := by
-    intro is
-    induction is with
-    | nil => intro cur; rfl
-    | cons a as ih =>
-      intro cur
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      by_cases h : passSubst a = true
-      · simp only [h, passLoopResult, Bool.not_true, Bool.false_eq_true,
-          if_false, ih, if_true]
-      · simp only [Bool.not_eq_true] at h
-        simp only [h, passLoopResult, Bool.not_false, if_true, Bool.false_eq_true,
-          if_false]
-        rfl
   unfold problem_spec_postProcess implementation_postProcess
-  exact helper (List.range maxPasses) false
+  cases maxPasses with
+  | zero => rfl
+  | succ n => rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,11 +64,12 @@
   result = some (passLoopResult (List.range maxPasses) passSubst false)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_postProcess
     (maxPasses : Nat) (passSubst : Nat → Bool) : Option Bool := Id.run do
   let mut substitutions : Option Bool := some false
-  for i in List.range maxPasses do
+  for i in List.range (maxPasses + 1) do
     let subst := passSubst i
     substitutions := some subst
     if ! subst then
@@ -82,27 +83,6 @@
       problem_spec_postProcess maxPasses passSubst
         (implementation_postProcess maxPasses passSubst) := by
   intro maxPasses passSubst
-  have helper : ∀ (is : List Nat) (cur : Bool),
-      Id.run (forIn is (some cur) (fun i r =>
-        if (!passSubst i) = true then pure (ForInStep.done (some (passSubst i)))
-        else do
-          pure PUnit.unit
-          pure (ForInStep.yield (some (passSubst i))))) =
-        some (passLoopResult is passSubst cur) := by
-    intro is
-    induction is with
-    | nil => intro cur; rfl
-    | cons a as ih =>
-      intro cur
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      by_cases h : passSubst a = true
-      · simp only [h, passLoopResult, Bool.not_true, Bool.false_eq_true,
-          if_false, ih, if_true]
-      · simp only [Bool.not_eq_true] at h
-        simp only [h, passLoopResult, Bool.not_false, if_true, Bool.false_eq_true,
-          if_false]
-        rfl
   unfold problem_spec_postProcess implementation_postProcess
-  exact helper (List.range maxPasses) false
+  rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,6 +64,7 @@
   result = some (passLoopResult (List.range maxPasses) passSubst false)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_postProcess
     (maxPasses : Nat) (passSubst : Nat → Bool) : Option Bool := Id.run do
@@ -71,8 +72,6 @@
   for i in List.range maxPasses do
     let subst := passSubst i
     substitutions := some subst
-    if ! subst then
-      break
   return substitutions
 -- impl-end
 
@@ -82,27 +81,6 @@
       problem_spec_postProcess maxPasses passSubst
         (implementation_postProcess maxPasses passSubst) := by
   intro maxPasses passSubst
-  have helper : ∀ (is : List Nat) (cur : Bool),
-      Id.run (forIn is (some cur) (fun i r =>
-        if (!passSubst i) = true then pure (ForInStep.done (some (passSubst i)))
-        else do
-          pure PUnit.unit
-          pure (ForInStep.yield (some (passSubst i))))) =
-        some (passLoopResult is passSubst cur) := by
-    intro is
-    induction is with
-    | nil => intro cur; rfl
-    | cons a as ih =>
-      intro cur
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      by_cases h : passSubst a = true
-      · simp only [h, passLoopResult, Bool.not_true, Bool.false_eq_true,
-          if_false, ih, if_true]
-      · simp only [Bool.not_eq_true] at h
-        simp only [h, passLoopResult, Bool.not_false, if_true, Bool.false_eq_true,
-          if_false]
-        rfl
   unfold problem_spec_postProcess implementation_postProcess
-  exact helper (List.range maxPasses) false
+  rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,6 +64,7 @@
   result = some (passLoopResult (List.range maxPasses) passSubst false)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_postProcess
     (maxPasses : Nat) (passSubst : Nat → Bool) : Option Bool := Id.run do
@@ -71,7 +72,7 @@
   for i in List.range maxPasses do
     let subst := passSubst i
     substitutions := some subst
-    if ! subst then
+    if subst then
       break
   return substitutions
 -- impl-end
@@ -82,27 +83,6 @@
       problem_spec_postProcess maxPasses passSubst
         (implementation_postProcess maxPasses passSubst) := by
   intro maxPasses passSubst
-  have helper : ∀ (is : List Nat) (cur : Bool),
-      Id.run (forIn is (some cur) (fun i r =>
-        if (!passSubst i) = true then pure (ForInStep.done (some (passSubst i)))
-        else do
-          pure PUnit.unit
-          pure (ForInStep.yield (some (passSubst i))))) =
-        some (passLoopResult is passSubst cur) := by
-    intro is
-    induction is with
-    | nil => intro cur; rfl
-    | cons a as ih =>
-      intro cur
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      by_cases h : passSubst a = true
-      · simp only [h, passLoopResult, Bool.not_true, Bool.false_eq_true,
-          if_false, ih, if_true]
-      · simp only [Bool.not_eq_true] at h
-        simp only [h, passLoopResult, Bool.not_false, if_true, Bool.false_eq_true,
-          if_false]
-        rfl
   unfold problem_spec_postProcess implementation_postProcess
-  exact helper (List.range maxPasses) false
+  rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,16 +64,11 @@
   result = some (passLoopResult (List.range maxPasses) passSubst false)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_postProcess
-    (maxPasses : Nat) (passSubst : Nat → Bool) : Option Bool := Id.run do
-  let mut substitutions : Option Bool := some false
-  for i in List.range maxPasses do
-    let subst := passSubst i
-    substitutions := some subst
-    if ! subst then
-      break
-  return substitutions
+    (maxPasses : Nat) (passSubst : Nat → Bool) : Option Bool :=
+  some false
 -- impl-end
 
 -- proof-start
@@ -82,27 +77,6 @@
       problem_spec_postProcess maxPasses passSubst
         (implementation_postProcess maxPasses passSubst) := by
   intro maxPasses passSubst
-  have helper : ∀ (is : List Nat) (cur : Bool),
-      Id.run (forIn is (some cur) (fun i r =>
-        if (!passSubst i) = true then pure (ForInStep.done (some (passSubst i)))
-        else do
-          pure PUnit.unit
-          pure (ForInStep.yield (some (passSubst i))))) =
-        some (passLoopResult is passSubst cur) := by
-    intro is
-    induction is with
-    | nil => intro cur; rfl
-    | cons a as ih =>
-      intro cur
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      by_cases h : passSubst a = true
-      · simp only [h, passLoopResult, Bool.not_true, Bool.false_eq_true,
-          if_false, ih, if_true]
-      · simp only [Bool.not_eq_true] at h
-        simp only [h, passLoopResult, Bool.not_false, if_true, Bool.false_eq_true,
-          if_false]
-        rfl
   unfold problem_spec_postProcess implementation_postProcess
-  exact helper (List.range maxPasses) false
+  rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,10 +64,11 @@
   result = some (passLoopResult (List.range maxPasses) passSubst false)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_postProcess
     (maxPasses : Nat) (passSubst : Nat → Bool) : Option Bool := Id.run do
-  let mut substitutions : Option Bool := some false
+  let mut substitutions : Option Bool := some true
   for i in List.range maxPasses do
     let subst := passSubst i
     substitutions := some subst
@@ -82,27 +83,6 @@
       problem_spec_postProcess maxPasses passSubst
         (implementation_postProcess maxPasses passSubst) := by
   intro maxPasses passSubst
-  have helper : ∀ (is : List Nat) (cur : Bool),
-      Id.run (forIn is (some cur) (fun i r =>
-        if (!passSubst i) = true then pure (ForInStep.done (some (passSubst i)))
-        else do
-          pure PUnit.unit
-          pure (ForInStep.yield (some (passSubst i))))) =
-        some (passLoopResult is passSubst cur) := by
-    intro is
-    induction is with
-    | nil => intro cur; rfl
-    | cons a as ih =>
-      intro cur
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      by_cases h : passSubst a = true
-      · simp only [h, passLoopResult, Bool.not_true, Bool.false_eq_true,
-          if_false, ih, if_true]
-      · simp only [Bool.not_eq_true] at h
-        simp only [h, passLoopResult, Bool.not_false, if_true, Bool.false_eq_true,
-          if_false]
-        rfl
   unfold problem_spec_postProcess implementation_postProcess
-  exact helper (List.range maxPasses) false
+  rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,16 +64,11 @@
   result = some (passLoopResult (List.range maxPasses) passSubst false)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_postProcess
-    (maxPasses : Nat) (passSubst : Nat → Bool) : Option Bool := Id.run do
-  let mut substitutions : Option Bool := some false
-  for i in List.range maxPasses do
-    let subst := passSubst i
-    substitutions := some subst
-    if ! subst then
-      break
-  return substitutions
+    (maxPasses : Nat) (passSubst : Nat → Bool) : Option Bool :=
+  some (passSubst 0)
 -- impl-end
 
 -- proof-start
@@ -82,27 +77,6 @@
       problem_spec_postProcess maxPasses passSubst
         (implementation_postProcess maxPasses passSubst) := by
   intro maxPasses passSubst
-  have helper : ∀ (is : List Nat) (cur : Bool),
-      Id.run (forIn is (some cur) (fun i r =>
-        if (!passSubst i) = true then pure (ForInStep.done (some (passSubst i)))
-        else do
-          pure PUnit.unit
-          pure (ForInStep.yield (some (passSubst i))))) =
-        some (passLoopResult is passSubst cur) := by
-    intro is
-    induction is with
-    | nil => intro cur; rfl
-    | cons a as ih =>
-      intro cur
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      by_cases h : passSubst a = true
-      · simp only [h, passLoopResult, Bool.not_true, Bool.false_eq_true,
-          if_false, ih, if_true]
-      · simp only [Bool.not_eq_true] at h
-        simp only [h, passLoopResult, Bool.not_false, if_true, Bool.false_eq_true,
-          if_false]
-        rfl
   unfold problem_spec_postProcess implementation_postProcess
-  exact helper (List.range maxPasses) false
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

/-!
Outcome of the bounded refinement-pass loop used when post-processing collected
static files.

A storage backend post-processes the collected files in up to a configured
maximum number of refinement passes. Each pass either still rewrites some
references to other files ("produced substitutions") or leaves everything
unchanged. The loop stops as soon as a pass produces no substitutions (a
fixpoint has been reached); otherwise it stops after exhausting the configured
number of passes.

After the loop the backend inspects a single flag: whether the loop finished
while a pass was *still* producing substitutions — i.e. the configured number of
passes was reached without converging.

Modeled inputs:
  * `maxPasses` — the configured maximum number of refinement passes;
  * `passSubst i` — for each pass index `i`, whether that pass would still
    produce substitutions.

The modeled result is that post-loop flag, carried as an `Option Bool`: the
defined value `some b` reports the flag's boolean value `b` for the given
configuration, while `none` denotes the absence of any value. The result is a
defined value `some _` for every configuration — every choice of `maxPasses`
(including none) and every per-pass behavior determines the flag fully.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The modeled
-- behavior is the control flow of the bounded refinement loop itself: a flag
-- initialized before the loop, overwritten once per pass with that pass's
-- aggregated substitution outcome, with early termination when a pass produces
-- no substitutions. The per-pass aggregated outcome (the work an individual
-- pass performs over the collected files) is abstracted as the input
-- `passSubst`, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- Final value of the loop's substitution flag given the still-to-run pass
indices `is`, the per-pass substitution behavior `f`, and the flag's current
value `cur`.

Front-recursive companion to the accumulator loop: a pass that produces
substitutions sets the flag to `true` and continues; a pass that produces none
sets the flag to `false` and stops (early termination); when no passes remain,
the current value stands. -/
def passLoopResult : List Nat → (Nat → Bool) → Bool → Bool
  | [], _, cur => cur
  | i :: is, f, _ => if f i then passLoopResult is f true else false
-- pure-end

-- post-conditions-start
/-- The post-loop substitution flag is fully determined by the configuration:
it is the value computed by running the configured passes in order, each pass
overwriting the flag with its own substitution outcome and the loop stopping at
the first pass that produces none. The flag is produced as a defined value
`some _` for every configuration (directive 5 frame: no configuration leaves the
result unconstrained). -/
def problem_spec_postProcess
    (maxPasses : Nat) (passSubst : Nat → Bool) (result : Option Bool) : Prop :=
  result = some (passLoopResult (List.range maxPasses) passSubst false)
-- post-conditions-end

-- impl-start
def implementation_postProcess
    (maxPasses : Nat) (passSubst : Nat → Bool) : Option Bool := Id.run do
  let mut substitutions : Option Bool := some false
  for i in List.range maxPasses do
    let subst := passSubst i
    substitutions := some subst
    if ! subst then
      break
  return substitutions
-- impl-end

-- proof-start
theorem correct_postProcess :
    ∀ (maxPasses : Nat) (passSubst : Nat → Bool),
      problem_spec_postProcess maxPasses passSubst
        (implementation_postProcess maxPasses passSubst) := by
  intro maxPasses passSubst
  have helper : ∀ (is : List Nat) (cur : Bool),
      Id.run (forIn is (some cur) (fun i r =>
        if (!passSubst i) = true then pure (ForInStep.done (some (passSubst i)))
        else do
          pure PUnit.unit
          pure (ForInStep.yield (some (passSubst i))))) =
        some (passLoopResult is passSubst cur) := by
    intro is
    induction is with
    | nil => intro cur; rfl
    | cons a as ih =>
      intro cur
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      by_cases h : passSubst a = true
      · simp only [h, passLoopResult, Bool.not_true, Bool.false_eq_true,
          if_false, ih, if_true]
      · simp only [Bool.not_eq_true] at h
        simp only [h, passLoopResult, Bool.not_false, if_true, Bool.false_eq_true,
          if_false]
        rfl
  unfold problem_spec_postProcess implementation_postProcess
  exact helper (List.range maxPasses) false
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Verifier: `bash scripts/lean_verify.sh <file>`.

SAME-SPEC: spec_view (markers._lean_spec_view) collapses BOTH impl and proof regions to placeholders, so same_spec only requires axioms/pure/pre/post byte-identical. Confirmed same_spec=True for all 8 files (7 attacks + pos_oracle_echo) via swebench_unified.markers.same_spec with lean backend.

### POSITIVE CONTROLS (both verify exit 0):
- pos_gold.lean (unmodified Solution.lean): EXIT=0; `#print axioms correct_postProcess` -> [propext, Quot.sound]. CLEAN (no sorryAx, no Classical.choice).
- pos_oracle_echo.lean (impl = `some (passLoopResult ...)`, proof `rfl`): EXIT=0; `#print axioms` -> does not depend on any axioms. CLEAN. Proves any closing impl is extensionally = gold at every input.

### ATTACKS (all same_spec=True; all FAIL to close, exit 1, genuine `rfl` errors — logs at atk_N.log):
- atk_1 (prepatch bug: flag init `none`, partial-domain hole at maxPasses=0): EXIT=1, rfl fails zero+succ cases (LHS none vs RHS some false). = PREPATCH REPRODUCED.
- atk_2 (boundary/off-by-one: List.range (maxPasses+1)): EXIT=1, rfl fails.
- atk_3 (control-flow-effect: no early break): EXIT=1, rfl fails.
- atk_4 (control-flow-effect: break on wrong condition `if subst`): EXIT=1, rfl fails.
- atk_5 (ungrounded/ignores passSubst: `some false`): EXIT=1, rfl fails (fails at maxPasses=1,passSubst=true where spec=some true).
- atk_6 (wrong init value `some true`): EXIT=1, rfl fails.
- atk_7 (ungrounded-oracle echo `some (passSubst 0)`): EXIT=1, rfl fails.

All 7 failure logs contain 'error: Tactic `rfl` failed' — genuine elaboration failures, NOT sorry (exit 3) or timeout (exit 124). No wrong impl produced a closing clean-axiom proof, so there was NO candidate patch to materialize/resolve (patches={}).

REFINEMENT.MD AUDIT: rows 1-8 tagged R (1 type refinement, 2 type refinement, 8 Option-Bool modeling) or I (3,4,5,6,7 identical concrete ops). No kind-3 (unmapped) legs. axioms=[] / deep_model_references=[] — axiom_check.py is a legitimate SKIP STUB: the modeled behavior is the loop's own control flow (a flag init'd before loop, overwritten per pass, early break), NOT a consumed unchanged-callee contract; the per-pass content work (`self._post_process`) is abstracted as the free input `passSubst`, correctly not axiomatized. No A-consumed / A-reference legs exist, so there is no deep-model correspondence surface to exploit for a divergent-but-closing variant. G-CONF (conformance_check.py) differential-tests the R/I shadow vs a post-patch replica exhaustively over maxPasses 0..8 x all boolean patterns + 150k fuzz, covering the discriminating maxPasses=0 point.

CONCLUSION: The unique-value functional-equality postcondition (directive-5 frame: every config pinned, in particular some false at maxPasses=0) admits exactly one observable behavior = post-patch flag semantics. No closing-but-non-resolving impl exists. verify => correct. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl closes; every attack fails with a genuine `rfl` elaboration error (not sorry/timeout), so protocol step 2 (materialize+resolve) had no candidate patches to run. The spec `result = some (passLoopResult (List.range maxPasses) passSubst false)` is a TOTAL FUNCTIONAL EQUALITY pinning `result` uniquely per input, so any closing impl is extensionally identical to gold everywhere — in particular at the discriminating input maxPasses=0 where it MUST return `some false` (defined flag), which is precisely the behavioral content of the gold edit (`substitutions = False` before the loop). closing ⟹ resolving.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

/-!
Outcome of the bounded refinement-pass loop used when post-processing collected
static files.

A storage backend post-processes the collected files in up to a configured
maximum number of refinement passes. Each pass either still rewrites some
references to other files ("produced substitutions") or leaves everything
unchanged. The loop stops as soon as a pass produces no substitutions (a
fixpoint has been reached); otherwise it stops after exhausting the configured
number of passes.

After the loop the backend inspects a single flag: whether the loop finished
while a pass was *still* producing substitutions — i.e. the configured number of
passes was reached without converging.

Modeled inputs:
  * `maxPasses` — the configured maximum number of refinement passes;
  * `passSubst i` — for each pass index `i`, whether that pass would still
    produce substitutions.

The modeled result is that post-loop flag, carried as an `Option Bool`: the
defined value `some b` reports the flag's boolean value `b` for the given
configuration, while `none` denotes the absence of any value. The result is a
defined value `some _` for every configuration — every choice of `maxPasses`
(including none) and every per-pass behavior determines the flag fully.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The modeled
-- behavior is the control flow of the bounded refinement loop itself: a flag
-- initialized before the loop, overwritten once per pass with that pass's
-- aggregated substitution outcome, with early termination when a pass produces
-- no substitutions. The per-pass aggregated outcome (the work an individual
-- pass performs over the collected files) is abstracted as the input
-- `passSubst`, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- Final value of the loop's substitution flag given the still-to-run pass
indices `is`, the per-pass substitution behavior `f`, and the flag's current
value `cur`.

Front-recursive companion to the accumulator loop: a pass that produces
substitutions sets the flag to `true` and continues; a pass that produces none
sets the flag to `false` and stops (early termination); when no passes remain,
the current value stands. -/
def passLoopResult : List Nat → (Nat → Bool) → Bool → Bool
  | [], _, cur => cur
  | i :: is, f, _ => if f i then passLoopResult is f true else false
-- pure-end

-- post-conditions-start
/-- The post-loop substitution flag is fully determined by the configuration:
it is the value computed by running the configured passes in order, each pass
overwriting the flag with its own substitution outcome and the loop stopping at
the first pass that produces none. The flag is produced as a defined value
`some _` for every configuration (directive 5 frame: no configuration leaves the
result unconstrained). -/
def problem_spec_postProcess
    (maxPasses : Nat) (passSubst : Nat → Bool) (result : Option Bool) : Prop :=
  result = some (passLoopResult (List.range maxPasses) passSubst false)
-- post-conditions-end

-- impl-start
def implementation_postProcess
    (maxPasses : Nat) (passSubst : Nat → Bool) : Option Bool := Id.run do
  let mut substitutions : Option Bool := some false
  for i in List.range maxPasses do
    let subst := passSubst i
    substitutions := some subst
    if ! subst then
      break
  return substitutions
-- impl-end

-- proof-start
theorem correct_postProcess :
    ∀ (maxPasses : Nat) (passSubst : Nat → Bool),
      problem_spec_postProcess maxPasses passSubst
        (implementation_postProcess maxPasses passSubst) := by
  intro maxPasses passSubst
  have helper : ∀ (is : List Nat) (cur : Bool),
      Id.run (forIn is (some cur) (fun i r =>
        if (!passSubst i) = true then pure (ForInStep.done (some (passSubst i)))
        else do
          pure PUnit.unit
          pure (ForInStep.yield (some (passSubst i))))) =
        some (passLoopResult is passSubst cur) := by
    intro is
    induction is with
    | nil => intro cur; rfl
    | cons a as ih =>
      intro cur
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      by_cases h : passSubst a = true
      · simp only [h, passLoopResult, Bool.not_true, Bool.false_eq_true,
          if_false, ih, if_true]
      · simp only [Bool.not_eq_true] at h
        simp only [h, passLoopResult, Bool.not_false, if_true, Bool.false_eq_true,
          if_false]
        rfl
  unfold problem_spec_postProcess implementation_postProcess
  exact helper (List.range maxPasses) false
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Verifier: `bash scripts/lean_verify.sh <file>`.

SAME-SPEC: spec_view (markers._lean_spec_view) collapses BOTH impl and proof regions to placeholders, so same_spec only requires axioms/pure/pre/post byte-identical. Confirmed same_spec=True for all 8 files (7 attacks + pos_oracle_echo) via swebench_unified.markers.same_spec with lean backend.

### POSITIVE CONTROLS (both verify exit 0):
- pos_gold.lean (unmodified Solution.lean): EXIT=0; `#print axioms correct_postProcess` -> [propext, Quot.sound]. CLEAN (no sorryAx, no Classical.choice).
- pos_oracle_echo.lean (impl = `some (passLoopResult ...)`, proof `rfl`): EXIT=0; `#print axioms` -> does not depend on any axioms. CLEAN. Proves any closing impl is extensionally = gold at every input.

### ATTACKS (all same_spec=True; all FAIL to close, exit 1, genuine `rfl` errors — logs at atk_N.log):
- atk_1 (prepatch bug: flag init `none`, partial-domain hole at maxPasses=0): EXIT=1, rfl fails zero+succ cases (LHS none vs RHS some false). = PREPATCH REPRODUCED.
- atk_2 (boundary/off-by-one: List.range (maxPasses+1)): EXIT=1, rfl fails.
- atk_3 (control-flow-effect: no early break): EXIT=1, rfl fails.
- atk_4 (control-flow-effect: break on wrong condition `if subst`): EXIT=1, rfl fails.
- atk_5 (ungrounded/ignores passSubst: `some false`): EXIT=1, rfl fails (fails at maxPasses=1,passSubst=true where spec=some true).
- atk_6 (wrong init value `some true`): EXIT=1, rfl fails.
- atk_7 (ungrounded-oracle echo `some (passSubst 0)`): EXIT=1, rfl fails.

All 7 failure logs contain 'error: Tactic `rfl` failed' — genuine elaboration failures, NOT sorry (exit 3) or timeout (exit 124). No wrong impl produced a closing clean-axiom proof, so there was NO candidate patch to materialize/resolve (patches={}).

REFINEMENT.MD AUDIT: rows 1-8 tagged R (1 type refinement, 2 type refinement, 8 Option-Bool modeling) or I (3,4,5,6,7 identical concrete ops). No kind-3 (unmapped) legs. axioms=[] / deep_model_references=[] — axiom_check.py is a legitimate SKIP STUB: the modeled behavior is the loop's own control flow (a flag init'd before loop, overwritten per pass, early break), NOT a consumed unchanged-callee contract; the per-pass content work (`self._post_process`) is abstracted as the free input `passSubst`, correctly not axiomatized. No A-consumed / A-reference legs exist, so there is no deep-model correspondence surface to exploit for a divergent-but-closing variant. G-CONF (conformance_check.py) differential-tests the R/I shadow vs a post-patch replica exhaustively over maxPasses 0..8 x all boolean patterns + 150k fuzz, covering the discriminating maxPasses=0 point.

CONCLUSION: The unique-value functional-equality postcondition (directive-5 frame: every config pinned, in particular some false at maxPasses=0) admits exactly one observable behavior = post-patch flag semantics. No closing-but-non-resolving impl exists. verify => correct. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) analysis for django__django-14493 lean bundle.

MODELED FUNCTION: ManifestFilesMixin.post_process bounded refinement loop and its post-loop `substitutions` flag (django/contrib/staticfiles/storage.py). Modeled inputs: maxPasses:Nat (= self.max_post_process_passes), passSubst:Nat->Bool (per-pass aggregated `substitutions or subst` outcome). Result Option Bool: some b = flag bound to b at `if substitutions:`, none = UnboundLocalError (referenced-before-assignment) state.

SPEC: problem_spec_postProcess pins result = some (passLoopResult (List.range maxPasses) passSubst false). passLoopResult front-recurses: []->cur; i::is -> if f i then recurse with cur:=true else false. So: empty (maxPasses=0) -> some false; first false at pass j -> some false (matches real `break` with substitutions=False held); all true -> some (last pass's value)=some true.

### Checks performed
1. Spec region BYTE-IDENTICAL: markers.same_spec(Solution, Solution_prepatch, lean backend) = True; spec_view confirms axioms/pure/post-conditions regions unchanged, only impl+proof differ (prepatch inits flag to `none`, gold to `some false`).
2. Solution.lean compiles via lean_verify.sh (exit 0, no sorry). `#print axioms correct_postProcess` = [propext, Quot.sound] only — NO sorryAx; proof is genuine.
3. Real repo (post-patch storage.py:275-291) confirmed: `substitutions = False` inserted before `for i in range(self.max_post_process_passes)`; inner loop re-zeros then or-folds; `if not substitutions: break`; flag always bound on exit. Matches mapping.md exactly.
4. Independent oracle: transliterated the real post-patch flag semantics in Python and diff-tested against passLoopResult over ALL boolean patterns for maxPasses 0..8 — 0 divergences. Discriminating case maxPasses=0: real returns some False, spec returns some (passLoopResult [] _ false)=some false. AGREE.
5. Bundle conformance_check.py runs: exhaustive grid k=0..8 x all patterns + 150k LCG fuzz (seed 14493), checked=150511, disagreements=0, status=pass.

DRIFT ASSESSMENT: The spec is neither too strong nor too weak relative to the real callee. It fully determines the flag for every configuration (directive-5 frame: some _ always), and that determination equals the real post-patch loop's flag on every input. No input where the modeled function disagrees with the real repo could be found. The abstraction of the inner content-rewriting loop as passSubst is a legitimate refinement (the pass re-zeros substitutions each iteration, so pass i's outcome depends only on pass i), not a drift — it does not over- or under-constrain the modeled control-flow value. No diverging input exists.

VERDICT: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit = single insertion `substitutions = False` before `for i in range(self.max_post_process_passes)` so the post-loop `if substitutions:` reads a defined value even at max_post_process_passes=0.

Mechanical screen: leakage.screen() passes clean (hard_failures=[]). No diff markers, no reproduced gold line ('substitutions = False' not present), no patched file path (django/contrib/staticfiles/storage.py absent), no bug/fix/unbound narration. Only patch-changed distinctive symbol is `post_process`, which is already public in problem_statement. same_spec(prepatch, postpatch)=True.

Semantic judgment (beyond lexical, judged ONLY against public problem_statement, NOT hints_text): the problem_statement is already highly disclosive — it names the variable `substitutions`, quotes the crashing line `if substitutions:`, gives the verbatim traceback `UnboundLocalError: local variable 'substitutions' referenced before assignment`, states the trigger (max_post_process_passes=0), and spells out the root cause ('subtitutions is only set if the loop is entered at least once'). The spec view discloses strictly LESS: abstract prose about a bounded refinement loop, per-pass substitution flag, early convergence, and a post-loop flag, with Lean-side names (maxPasses, passSubst, passLoopResult, problem_spec_postProcess) that do not echo the repo variable `substitutions`. The postcondition pins the flag to a defined `some _` for every configuration including maxPasses=0; that is the required correctness specification, and it reveals no edit-localization beyond what the problem_statement already makes public. No line of the spec view leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
