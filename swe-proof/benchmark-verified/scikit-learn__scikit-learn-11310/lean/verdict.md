# P2 adversarial audit — scikit-learn__scikit-learn-11310

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,12 +56,7 @@
 -- impl-start
 def implementation_refitTiming
     (refitEnabled : Bool) (startClock endClock : ℚ) : Option ℚ := Id.run do
-  let mut refitDuration : Option ℚ := none
-  if refitEnabled then
-    let s := startClock
-    -- (the best model is refit on the whole dataset between the two readings)
-    let e := endClock
-    refitDuration := some (e - s)
+  let refitDuration : Option ℚ := none
   return refitDuration
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,10 +58,8 @@
     (refitEnabled : Bool) (startClock endClock : ℚ) : Option ℚ := Id.run do
   let mut refitDuration : Option ℚ := none
   if refitEnabled then
-    let s := startClock
-    -- (the best model is refit on the whole dataset between the two readings)
-    let e := endClock
-    refitDuration := some (e - s)
+    if startClock ≤ endClock then
+      refitDuration := some (endClock - startClock)
   return refitDuration
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,10 +58,7 @@
     (refitEnabled : Bool) (startClock endClock : ℚ) : Option ℚ := Id.run do
   let mut refitDuration : Option ℚ := none
   if refitEnabled then
-    let s := startClock
-    -- (the best model is refit on the whole dataset between the two readings)
-    let e := endClock
-    refitDuration := some (e - s)
+    refitDuration := some (startClock - endClock)
   return refitDuration
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,11 +57,8 @@
 def implementation_refitTiming
     (refitEnabled : Bool) (startClock endClock : ℚ) : Option ℚ := Id.run do
   let mut refitDuration : Option ℚ := none
-  if refitEnabled then
-    let s := startClock
-    -- (the best model is refit on the whole dataset between the two readings)
-    let e := endClock
-    refitDuration := some (e - s)
+  if !refitEnabled then
+    refitDuration := some (endClock - startClock)
   return refitDuration
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,12 +56,7 @@
 -- impl-start
 def implementation_refitTiming
     (refitEnabled : Bool) (startClock endClock : ℚ) : Option ℚ := Id.run do
-  let mut refitDuration : Option ℚ := none
-  if refitEnabled then
-    let s := startClock
-    -- (the best model is refit on the whole dataset between the two readings)
-    let e := endClock
-    refitDuration := some (e - s)
+  let refitDuration : Option ℚ := some (endClock - startClock)
   return refitDuration
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,10 +58,7 @@
     (refitEnabled : Bool) (startClock endClock : ℚ) : Option ℚ := Id.run do
   let mut refitDuration : Option ℚ := none
   if refitEnabled then
-    let s := startClock
-    -- (the best model is refit on the whole dataset between the two readings)
-    let e := endClock
-    refitDuration := some (e - s)
+    refitDuration := some (endClock - startClock + 1)
   return refitDuration
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,10 +58,7 @@
     (refitEnabled : Bool) (startClock endClock : ℚ) : Option ℚ := Id.run do
   let mut refitDuration : Option ℚ := none
   if refitEnabled then
-    let s := startClock
-    -- (the best model is refit on the whole dataset between the two readings)
-    let e := endClock
-    refitDuration := some (e - s)
+    refitDuration := some 0
   return refitDuration
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Recording how long the final refit of the best model takes.

A hyper-parameter search procedure, after selecting the best parameter setting,
optionally refits a single best model on the whole dataset. Callers want to know
how long that final refit took (so they can report the cost of the search
separately from the cost of refitting). The procedure reads a wall-clock value
immediately before the final refit begins and again immediately after it
finishes, and exposes the elapsed duration as an observable.

This observable is produced ONLY when the final refit is performed. When refit is
disabled no final model is fit, so there is no duration to report and the
observable is absent.

We model the produced observable directly:

  * `refitEnabled` — whether the final refit is performed;
  * `startClock`   — the wall-clock value read immediately before the refit;
  * `endClock`     — the wall-clock value read immediately after the refit;
  * `result`       — the reported refit duration: `some (endClock - startClock)`
                     when the refit is performed, and `none` (no observable) when
                     it is not.

The reported duration is exactly `endClock - startClock` — the identical
subtraction the procedure performs — for EVERY pair of readings, with no side
condition relating them. (On a real, monotonically advancing wall clock
`startClock ≤ endClock`, so the reported duration is never negative in
practice; the recording itself does not depend on that.)
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The two
-- wall-clock readings that bracket the refit are environment-provided values,
-- modeled directly as the rational inputs `startClock` / `endClock`; the
-- selection and fitting of the best model are unchanged operations whose only
-- modeled effect is that they occur between the two readings (the elapsed time).
-- No `opaque`/`axiom` callee contract is therefore needed.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The reported refit duration is the elapsed wall-clock between the reading
taken immediately before the refit and the reading taken immediately after it,
exposed exactly when the refit is performed, and absent otherwise. -/
def problem_spec_refitTiming
    (refitEnabled : Bool) (startClock endClock : ℚ) (result : Option ℚ) : Prop :=
  result = (if refitEnabled then some (endClock - startClock) else none)
-- post-conditions-end

-- impl-start
def implementation_refitTiming
    (refitEnabled : Bool) (startClock endClock : ℚ) : Option ℚ := Id.run do
  let mut refitDuration : Option ℚ := none
  if refitEnabled then
    let s := startClock
    -- (the best model is refit on the whole dataset between the two readings)
    let e := endClock
    refitDuration := some (e - s)
  return refitDuration
-- impl-end

-- proof-start
theorem correct_refitTiming :
    ∀ (refitEnabled : Bool) (startClock endClock : ℚ),
      problem_spec_refitTiming refitEnabled startClock endClock
        (implementation_refitTiming refitEnabled startClock endClock) := by
  intro refitEnabled startClock endClock
  unfold problem_spec_refitTiming implementation_refitTiming
  cases refitEnabled <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec: problem_spec_refitTiming (refitEnabled startClock endClock result) := result = (if refitEnabled then some (endClock - startClock) else none). This is a TOTAL, precondition-free exact function of the inputs (no binder relating startClock/endClock) -> zero slack. mapping.md documents that an earlier startClock<=endClock precondition was deliberately removed after a prior adversarial pass exhibited a same-spec wrong impl (partial-domain) that closed the guarded theorem; the binder is gone here.

Protocol executed (all files = byte-identical header/axioms/pure/pre/post to Solution.lean, edited impl region only; same_spec check via swebench_unified.markers.same_spec = True for all 8, using python).

Positive control: cp of Solution.lean -> `bash scripts/lean_verify.sh .../positive_control.lean` exit=0. Clean #print axioms correct_refitTiming = [propext, Classical.choice, Quot.sound] (no sorryAx).

Prepatch bug reproduced: prepatch.lean (impl always returns none) -> lean_verify exit=1 (rfl failed).

7 DISTINCT same-spec wrong impls, all verified concurrently (<=4 background jobs), ALL FAIL with genuine `Tactic rfl failed` errors (not sorry, not timeout):
  atk_1 prepatch/always-none -> exit 1
  atk_2 partial-domain (record only if startClock<=endClock) -> exit 1
  atk_3 boundary/reversed subtraction some (startClock-endClock) -> exit 1
  atk_4 control-flow-effect (branch inverted, some when !refitEnabled) -> exit 1
  atk_5 ungrounded-oracle echo (ignore flag, always some (endClock-startClock)) -> exit 1
  atk_6 off-by-constant some (endClock-startClock+1) -> exit 1
  atk_7 constant-zero some 0 -> exit 1
Command form: `bash scripts/lean_verify.sh .../atk_N.lean`.

Since NO wrong impl produced a closing clean-axiom proof, there is no faithful patch to materialize/run through run_resolve; verify=>correct holds vacuously for the attack set. patches={} accordingly.

Refinement.md audit: legs 1,2,3,5,6 = R (Bool/Q/Option Q type bijection for refit flag, two clock readings, recorded-vs-absent attribute); legs 4,7 = I (unchanged clone+fit abstracted to 'time elapses'; return). A-consumed: none. A-reference: none. NO kind-3 (changed-yet-inexpressible) leg. time.time() readings are modeled directly as rational INPUT DATA (environment-provided values), not axiomatized callee contracts -> G-AX is a legitimate skip stub and there is no A-leg correspondence that could fail. The A-legs I was asked to concentrate on are genuinely absent and correctly declared. mapping.md/refinement.md/Solution.lean are mutually consistent.

Conclusion: the exact, total, precondition-free spec admits no behaviorally-different implementation whose correct_refitTiming closes; every attack was rejected by the kernel. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Recording how long the final refit of the best model takes.

A hyper-parameter search procedure, after selecting the best parameter setting,
optionally refits a single best model on the whole dataset. Callers want to know
how long that final refit took (so they can report the cost of the search
separately from the cost of refitting). The procedure reads a wall-clock value
immediately before the final refit begins and again immediately after it
finishes, and exposes the elapsed duration as an observable.

This observable is produced ONLY when the final refit is performed. When refit is
disabled no final model is fit, so there is no duration to report and the
observable is absent.

We model the produced observable directly:

  * `refitEnabled` — whether the final refit is performed;
  * `startClock`   — the wall-clock value read immediately before the refit;
  * `endClock`     — the wall-clock value read immediately after the refit;
  * `result`       — the reported refit duration: `some (endClock - startClock)`
                     when the refit is performed, and `none` (no observable) when
                     it is not.

The reported duration is exactly `endClock - startClock` — the identical
subtraction the procedure performs — for EVERY pair of readings, with no side
condition relating them. (On a real, monotonically advancing wall clock
`startClock ≤ endClock`, so the reported duration is never negative in
practice; the recording itself does not depend on that.)
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The two
-- wall-clock readings that bracket the refit are environment-provided values,
-- modeled directly as the rational inputs `startClock` / `endClock`; the
-- selection and fitting of the best model are unchanged operations whose only
-- modeled effect is that they occur between the two readings (the elapsed time).
-- No `opaque`/`axiom` callee contract is therefore needed.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The reported refit duration is the elapsed wall-clock between the reading
taken immediately before the refit and the reading taken immediately after it,
exposed exactly when the refit is performed, and absent otherwise. -/
def problem_spec_refitTiming
    (refitEnabled : Bool) (startClock endClock : ℚ) (result : Option ℚ) : Prop :=
  result = (if refitEnabled then some (endClock - startClock) else none)
-- post-conditions-end

-- impl-start
def implementation_refitTiming
    (refitEnabled : Bool) (startClock endClock : ℚ) : Option ℚ := Id.run do
  let mut refitDuration : Option ℚ := none
  if refitEnabled then
    let s := startClock
    -- (the best model is refit on the whole dataset between the two readings)
    let e := endClock
    refitDuration := some (e - s)
  return refitDuration
-- impl-end

-- proof-start
theorem correct_refitTiming :
    ∀ (refitEnabled : Bool) (startClock endClock : ℚ),
      problem_spec_refitTiming refitEnabled startClock endClock
        (implementation_refitTiming refitEnabled startClock endClock) := by
  intro refitEnabled startClock endClock
  unfold problem_spec_refitTiming implementation_refitTiming
  cases refitEnabled <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec: problem_spec_refitTiming (refitEnabled startClock endClock result) := result = (if refitEnabled then some (endClock - startClock) else none). This is a TOTAL, precondition-free exact function of the inputs (no binder relating startClock/endClock) -> zero slack. mapping.md documents that an earlier startClock<=endClock precondition was deliberately removed after a prior adversarial pass exhibited a same-spec wrong impl (partial-domain) that closed the guarded theorem; the binder is gone here.

Protocol executed (all files = byte-identical header/axioms/pure/pre/post to Solution.lean, edited impl region only; same_spec check via swebench_unified.markers.same_spec = True for all 8, using python).

Positive control: cp of Solution.lean -> `bash scripts/lean_verify.sh .../positive_control.lean` exit=0. Clean #print axioms correct_refitTiming = [propext, Classical.choice, Quot.sound] (no sorryAx).

Prepatch bug reproduced: prepatch.lean (impl always returns none) -> lean_verify exit=1 (rfl failed).

7 DISTINCT same-spec wrong impls, all verified concurrently (<=4 background jobs), ALL FAIL with genuine `Tactic rfl failed` errors (not sorry, not timeout):
  atk_1 prepatch/always-none -> exit 1
  atk_2 partial-domain (record only if startClock<=endClock) -> exit 1
  atk_3 boundary/reversed subtraction some (startClock-endClock) -> exit 1
  atk_4 control-flow-effect (branch inverted, some when !refitEnabled) -> exit 1
  atk_5 ungrounded-oracle echo (ignore flag, always some (endClock-startClock)) -> exit 1
  atk_6 off-by-constant some (endClock-startClock+1) -> exit 1
  atk_7 constant-zero some 0 -> exit 1
Command form: `bash scripts/lean_verify.sh .../atk_N.lean`.

Since NO wrong impl produced a closing clean-axiom proof, there is no faithful patch to materialize/run through run_resolve; verify=>correct holds vacuously for the attack set. patches={} accordingly.

Refinement.md audit: legs 1,2,3,5,6 = R (Bool/Q/Option Q type bijection for refit flag, two clock readings, recorded-vs-absent attribute); legs 4,7 = I (unchanged clone+fit abstracted to 'time elapses'; return). A-consumed: none. A-reference: none. NO kind-3 (changed-yet-inexpressible) leg. time.time() readings are modeled directly as rational INPUT DATA (environment-provided values), not axiomatized callee contracts -> G-AX is a legitimate skip stub and there is no A-leg correspondence that could fail. The A-legs I was asked to concentrate on are genuinely absent and correctly declared. mapping.md/refinement.md/Solution.lean are mutually consistent.

Conclusion: the exact, total, precondition-free spec admits no behaviorally-different implementation whose correct_refitTiming closes; every attack was rejected by the kernel. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for scikit-learn__scikit-learn-11310, modeled callee = refit-timing block of BaseSearchCV.fit.

### Verification
- Solution.lean compiles clean via scripts/lean_verify.sh (exit 0, no sorry).
- #print axioms correct_refitTiming = [propext, Classical.choice, Quot.sound] — standard Mathlib axioms only, NO sorryAx; proof (`cases refitEnabled <;> rfl`) is genuine.
- same_spec(Solution.lean, Solution_prepatch.lean, lean) = True: the spec region (axioms/pure/post-conditions) is byte-identical between pre- and post-patch bundles.

Spec: problem_spec_refitTiming ≡ result = (if refitEnabled then some (endClock - startClock) else none).
Real post-patch code: inside `if self.refit:`, `self.refit_time_ = refit_end_time - refit_start_time`; attribute absent otherwise.

### Pointwise agreement with real callee
- refitEnabled=true: spec = some(end-start); real code does the identical bare subtraction of the two readings → agree for every ℚ pair. No side condition excludes any real behavior.
- refitEnabled=false: spec = none; real code leaves refit_time_ unset (block gated by if self.refit:) → agree (hasattr False ↔ none).
- The mapping intentionally carries NO startClock ≤ endClock binder. This is faithful, not spec-too-strong: the real subtraction is unconditional, so on start>end inputs the real code would compute the same negative difference the spec requires; on realistic inputs time.time() is monotonic so start≤end holds. There is no input where the spec's required output disagrees with what the real repo computes.
- Bool truthiness modeling of self.refit (present-iff-refit) is exact; abstracted clone/set_params/fit are correctly outside the modeled observable (would need an ungrounded oracle).

No diverging input found: the spec neither over-constrains nor drifts from the real callee. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigor confirmed: lean_verify.sh exit 0 (compiles, no sorry); meta records #print axioms correct_refitTiming = [propext, Classical.choice, Quot.sound] — clean, no sorryAx, proof is genuine. Spec region byte-identical between Solution.lean and Solution_prepatch.lean (diff of axioms..post-conditions-end regions empty; same_spec holds). Mechanical G-LEAK screen (leakage.screen, LeanBackend) passes with zero hard_failures.

Leakage judgment (against public problem_statement ONLY, not hints_text): NO-LEAKAGE. The public problem_statement is itself a fully-specifying feature request — it explicitly asks for an attribute `refit_time_` that is 'simply the time it took to refit the best model', measured by timing the refit. The solver-facing spec view (problem_spec_refitTiming: result = if refitEnabled then some (endClock - startClock) else none, plus a generic wall-clock docstring) merely restates that already-public observable and nothing more.

Nothing reconstructs the gold edit beyond problem_statement: (1) no patched file path (sklearn/model_selection/_search.py), no module dotted path, no diff markers in the spec view; (2) no gold-patch identifiers — time.time(), refit_time_, self.refit, best_estimator_, clone, set_params — appear in the solver-facing view (they live only in mapping.md/refinement.md audit artifacts, which are NOT part of the spec view); (3) the `if refitEnabled` gate and the endClock-startClock subtraction are inherent consequences of 'time to refit the best model' (a duration is a difference of two readings; there is no refit time when no refit occurs), not a hidden gold detail; (4) comments use generic 'wall-clock value' phrasing with no bug/fix narration. Every changed-symbol collision check is moot because the distinctive patched symbols never surface in the view. No single spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
