# P2 adversarial audit — django__django-16116

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,22 +55,17 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Decide the effects of a run from the three already-determined inputs. With no
-detected changes there is nothing to do. Otherwise, when the run is in
-verification-only mode it requests an immediate non-zero exit before any output is
-emitted; only when it is NOT in that mode does it emit migration output — merging
-into the latest migration when requested, a fresh migration file otherwise. -/
 def implementation_processChanges
     (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
   let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
   if !hasChanges then
     return eff
-  if checkOnly then
-    return { eff with exitCode := some 1 }
   if mergeIntoLast then
     eff := { eff with wroteToLast := true }
   else
     eff := { eff with wroteNew := true }
+  if checkOnly then
+    return { eff with exitCode := some 1 }
   return eff
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,18 +55,13 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Decide the effects of a run from the three already-determined inputs. With no
-detected changes there is nothing to do. Otherwise, when the run is in
-verification-only mode it requests an immediate non-zero exit before any output is
-emitted; only when it is NOT in that mode does it emit migration output — merging
-into the latest migration when requested, a fresh migration file otherwise. -/
 def implementation_processChanges
     (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
   let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
   if !hasChanges then
     return eff
   if checkOnly then
-    return { eff with exitCode := some 1 }
+    return { eff with exitCode := some 0 }
   if mergeIntoLast then
     eff := { eff with wroteToLast := true }
   else
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,11 +55,6 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Decide the effects of a run from the three already-determined inputs. With no
-detected changes there is nothing to do. Otherwise, when the run is in
-verification-only mode it requests an immediate non-zero exit before any output is
-emitted; only when it is NOT in that mode does it emit migration output — merging
-into the latest migration when requested, a fresh migration file otherwise. -/
 def implementation_processChanges
     (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
   let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
@@ -68,9 +63,9 @@
   if checkOnly then
     return { eff with exitCode := some 1 }
   if mergeIntoLast then
+    eff := { eff with wroteNew := true }
+  else
     eff := { eff with wroteToLast := true }
-  else
-    eff := { eff with wroteNew := true }
   return eff
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,18 +55,11 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Decide the effects of a run from the three already-determined inputs. With no
-detected changes there is nothing to do. Otherwise, when the run is in
-verification-only mode it requests an immediate non-zero exit before any output is
-emitted; only when it is NOT in that mode does it emit migration output — merging
-into the latest migration when requested, a fresh migration file otherwise. -/
 def implementation_processChanges
     (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
   let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
   if !hasChanges then
     return eff
-  if checkOnly then
-    return { eff with exitCode := some 1 }
   if mergeIntoLast then
     eff := { eff with wroteToLast := true }
   else
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -55,23 +55,12 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Decide the effects of a run from the three already-determined inputs. With no
-detected changes there is nothing to do. Otherwise, when the run is in
-verification-only mode it requests an immediate non-zero exit before any output is
-emitted; only when it is NOT in that mode does it emit migration output — merging
-into the latest migration when requested, a fresh migration file otherwise. -/
 def implementation_processChanges
-    (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
-  let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
-  if !hasChanges then
-    return eff
-  if checkOnly then
-    return { eff with exitCode := some 1 }
-  if mergeIntoLast then
-    eff := { eff with wroteToLast := true }
-  else
-    eff := { eff with wroteNew := true }
-  return eff
+    (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect :=
+  match hasChanges, checkOnly, mergeIntoLast with
+  | false, _, _ => { wroteToLast := false, wroteNew := false, exitCode := none }
+  | true, true, _ => { wroteToLast := false, wroteNew := false, exitCode := some 1 }
+  | true, false, m => { wroteToLast := m, wroteNew := !m, exitCode := none }
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,16 +55,9 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Decide the effects of a run from the three already-determined inputs. With no
-detected changes there is nothing to do. Otherwise, when the run is in
-verification-only mode it requests an immediate non-zero exit before any output is
-emitted; only when it is NOT in that mode does it emit migration output — merging
-into the latest migration when requested, a fresh migration file otherwise. -/
 def implementation_processChanges
     (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
   let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
-  if !hasChanges then
-    return eff
   if checkOnly then
     return { eff with exitCode := some 1 }
   if mergeIntoLast then
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,18 +55,13 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Decide the effects of a run from the three already-determined inputs. With no
-detected changes there is nothing to do. Otherwise, when the run is in
-verification-only mode it requests an immediate non-zero exit before any output is
-emitted; only when it is NOT in that mode does it emit migration output — merging
-into the latest migration when requested, a fresh migration file otherwise. -/
 def implementation_processChanges
     (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
   let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
   if !hasChanges then
     return eff
   if checkOnly then
-    return { eff with exitCode := some 1 }
+    return { eff with wroteNew := true, exitCode := some 1 }
   if mergeIntoLast then
     eff := { eff with wroteToLast := true }
   else
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The command consults three
-- already-decided inputs — whether model changes were detected, whether the
-- run was requested in verification-only mode, and whether it should merge into
-- the latest migration — all modeled as plain parameters. The two file-emitting
-- procedures are unchanged side-effecting steps whose only relevant observable is
-- WHETHER they ran on this invocation; that is recorded by a Boolean field, so
-- nothing is abstracted behind a callee. The proof agent may add `_prop` axioms
-- only if it gets stuck.
-- axioms-end

-- pure-start
/-- The observable effects of one run of the migration-creation command on the
"changes" decision. `wroteToLast` records that the run emitted output by merging
into the latest existing migration; `wroteNew` records that it emitted output as a
fresh migration file; `exitCode` records the process exit status the run requests
(`none` = normal completion, `some n` = terminate immediately with status `n`). -/
structure CommandEffect where
  /-- The run merged its output into the latest existing migration. -/
  wroteToLast : Bool
  /-- The run emitted its output as a fresh migration file. -/
  wroteNew : Bool
  /-- The exit status the run requests, if it terminates early. -/
  exitCode : Option Nat
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Behavior the command must exhibit on the "changes" decision.

* When no model changes were detected, nothing is emitted and the run completes
  normally.
* When changes were detected and the run is in verification-only mode, the run
  must terminate immediately with a non-zero status and emit nothing — it reports
  the missing migrations without producing any migration output.
* Otherwise the run emits exactly one form of migration output — merged into the
  latest migration when merge mode is requested, a fresh migration file
  otherwise — and completes normally.

Every effect field is pinned for every combination of inputs, so the requested
exit status and the two emit-flags are each fully determined. -/
def problem_spec_processChanges
    (hasChanges checkOnly mergeIntoLast : Bool) (result : CommandEffect) : Prop :=
  if !hasChanges then
    result.wroteToLast = false ∧ result.wroteNew = false ∧ result.exitCode = none
  else if checkOnly then
    result.wroteToLast = false ∧ result.wroteNew = false ∧ result.exitCode = some 1
  else
    result.wroteToLast = mergeIntoLast ∧
    result.wroteNew = (!mergeIntoLast) ∧
    result.exitCode = none
-- post-conditions-end

-- impl-start
def implementation_processChanges
    (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
  let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
  if !hasChanges then
    return eff
  if checkOnly then
    return { eff with exitCode := some 1 }
  if mergeIntoLast then
    eff := { eff with wroteToLast := true }
  else
    eff := { eff with wroteNew := true }
  return eff
-- impl-end

-- proof-start
theorem correct_processChanges :
    ∀ (hasChanges checkOnly mergeIntoLast : Bool),
    problem_spec_processChanges hasChanges checkOnly mergeIntoLast
      (implementation_processChanges hasChanges checkOnly mergeIntoLast) := by
  intro hasChanges checkOnly mergeIntoLast
  unfold problem_spec_processChanges implementation_processChanges
  cases hasChanges <;> cases checkOnly <;> cases mergeIntoLast <;>
    simp [Id.run, bind, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_processChanges is a TOTAL, fully-pinned predicate over Bool^3 -> CommandEffect. All three observables (wroteToLast, wroteNew, exitCode) are fixed to gold values for every one of the 8 input combinations. Consequence: any impl whose correct_processChanges closes MUST be observationally identical to gold. AXIOMS/A-LEG AUDIT: axioms region is EMPTY (0 non-comment lines) => no A-consumed, no A-reference legs to falsify; axiom_check.py is a skip stub as claimed. refinement.md legs are all R/I (no kind-3). R correspondences are faithful to F2P (test_makemigrations_check asserts SystemExit raised AND migration dir absent => no writer ran): writers modeled as Bool 'ran' flags (wroteToLast/wroteNew), sys.exit(1)->exitCode=some 1, normal completion->none, three flags->Bool params. The single behavioral change modeled = hoisting exit guard ahead of writers. All 7 attacks confirmed same_spec=True via swebench_unified.markers.same_spec (byte-identical axioms/pure/pre/post).

### VERIFY RESULTS (cmd: bash scripts/lean_verify.sh <f>):
- atk_1 prepatch bug (writers before exit guard): EXIT 1, unsolved goal `⊢ False` in cases true.true.* — cannot close. (=> prepatch_reproduced=true)
- atk_2 boundary (checkOnly returns exitCode some 0 not some 1): EXIT 1, ⊢ False.
- atk_3 control-flow-effect (writer flags swapped: mergeIntoLast sets wroteNew): EXIT 1, ⊢ False.
- atk_4 partial-domain (checkOnly ignored, always emit output): EXIT 1, ⊢ False.
- atk_5 ungrounded-oracle echo (match-expression producing gold triple for all 8 inputs): EXIT 0, verifies.
- atk_6 drop the no-changes guard (emits even with no changes): EXIT 1, ⊢ False in cases false.true.*.
- atk_7 checkOnly requests exit BUT also sets wroteNew: EXIT 1, ⊢ False.
Positive control pos_gold (exact gold impl): EXIT 0.

AXIOM CHECK on the two closing proofs (appended `#print axioms correct_processChanges`, re-verified EXIT 0): atk_5 => 'correct_processChanges' depends on axioms: [propext]; pos_gold => [propext]. Clean — no sorryAx, no user _prop axioms.

MANDATORY RESOLVE on the only closing wrong-impl (atk_5): atk_5 is behaviorally gold-equivalent, so its faithful refined patch IS the gold control-flow hunk (exit guard hoisted before writers). Materialized at faithful_atk_5.diff. run_resolve via swebench_unified.harness initially returned 'no report — harness error or image pull failure' TWICE (run_ids ...-atk5, ...-atk5b) — pure infra artifact under live-concurrent runs docker contention (docker system df showed 306 images/47 containers, many concurrent sbu-resolve-* runs; docs warn one-backend-at-a-time). Re-ran the underlying harness DIRECTLY (docker -c python -m swebench_unified.run_evaluation ... --instance_ids django__django-16116, run_id sbu-resolve-audit-eq-zmm2kna1-atk5-direct): result 'Instances resolved: 1'. report.json: resolved=true, patch_successfully_applied=true, FAIL_TO_PASS success=['makemigrations --check should exit with a non-zero status when'], PASS_TO_PASS all success. => atk_5's faithful patch RESOLVES; it does NOT break the spec.

CONCLUSION: The spec admits no same-spec wrong impl with a closing clean-axiom proof whose faithful patch fails to resolve. Every genuinely-wrong impl (prepatch, boundary, control-flow, partial-domain, ungrounded, no-changes-drop, checkOnly-also-writes) fails the closing proof with a concrete ⊢ False. The one closing impl is a correct gold echo that resolves. No A-legs to attack. verify => correct holds. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The command consults three
-- already-decided inputs — whether model changes were detected, whether the
-- run was requested in verification-only mode, and whether it should merge into
-- the latest migration — all modeled as plain parameters. The two file-emitting
-- procedures are unchanged side-effecting steps whose only relevant observable is
-- WHETHER they ran on this invocation; that is recorded by a Boolean field, so
-- nothing is abstracted behind a callee. The proof agent may add `_prop` axioms
-- only if it gets stuck.
-- axioms-end

-- pure-start
/-- The observable effects of one run of the migration-creation command on the
"changes" decision. `wroteToLast` records that the run emitted output by merging
into the latest existing migration; `wroteNew` records that it emitted output as a
fresh migration file; `exitCode` records the process exit status the run requests
(`none` = normal completion, `some n` = terminate immediately with status `n`). -/
structure CommandEffect where
  /-- The run merged its output into the latest existing migration. -/
  wroteToLast : Bool
  /-- The run emitted its output as a fresh migration file. -/
  wroteNew : Bool
  /-- The exit status the run requests, if it terminates early. -/
  exitCode : Option Nat
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Behavior the command must exhibit on the "changes" decision.

* When no model changes were detected, nothing is emitted and the run completes
  normally.
* When changes were detected and the run is in verification-only mode, the run
  must terminate immediately with a non-zero status and emit nothing — it reports
  the missing migrations without producing any migration output.
* Otherwise the run emits exactly one form of migration output — merged into the
  latest migration when merge mode is requested, a fresh migration file
  otherwise — and completes normally.

Every effect field is pinned for every combination of inputs, so the requested
exit status and the two emit-flags are each fully determined. -/
def problem_spec_processChanges
    (hasChanges checkOnly mergeIntoLast : Bool) (result : CommandEffect) : Prop :=
  if !hasChanges then
    result.wroteToLast = false ∧ result.wroteNew = false ∧ result.exitCode = none
  else if checkOnly then
    result.wroteToLast = false ∧ result.wroteNew = false ∧ result.exitCode = some 1
  else
    result.wroteToLast = mergeIntoLast ∧
    result.wroteNew = (!mergeIntoLast) ∧
    result.exitCode = none
-- post-conditions-end

-- impl-start
def implementation_processChanges
    (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
  let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
  if !hasChanges then
    return eff
  if checkOnly then
    return { eff with exitCode := some 1 }
  if mergeIntoLast then
    eff := { eff with wroteToLast := true }
  else
    eff := { eff with wroteNew := true }
  return eff
-- impl-end

-- proof-start
theorem correct_processChanges :
    ∀ (hasChanges checkOnly mergeIntoLast : Bool),
    problem_spec_processChanges hasChanges checkOnly mergeIntoLast
      (implementation_processChanges hasChanges checkOnly mergeIntoLast) := by
  intro hasChanges checkOnly mergeIntoLast
  unfold problem_spec_processChanges implementation_processChanges
  cases hasChanges <;> cases checkOnly <;> cases mergeIntoLast <;>
    simp [Id.run, bind, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_processChanges is a TOTAL, fully-pinned predicate over Bool^3 -> CommandEffect. All three observables (wroteToLast, wroteNew, exitCode) are fixed to gold values for every one of the 8 input combinations. Consequence: any impl whose correct_processChanges closes MUST be observationally identical to gold. AXIOMS/A-LEG AUDIT: axioms region is EMPTY (0 non-comment lines) => no A-consumed, no A-reference legs to falsify; axiom_check.py is a skip stub as claimed. refinement.md legs are all R/I (no kind-3). R correspondences are faithful to F2P (test_makemigrations_check asserts SystemExit raised AND migration dir absent => no writer ran): writers modeled as Bool 'ran' flags (wroteToLast/wroteNew), sys.exit(1)->exitCode=some 1, normal completion->none, three flags->Bool params. The single behavioral change modeled = hoisting exit guard ahead of writers. All 7 attacks confirmed same_spec=True via swebench_unified.markers.same_spec (byte-identical axioms/pure/pre/post).

### VERIFY RESULTS (cmd: bash scripts/lean_verify.sh <f>):
- atk_1 prepatch bug (writers before exit guard): EXIT 1, unsolved goal `⊢ False` in cases true.true.* — cannot close. (=> prepatch_reproduced=true)
- atk_2 boundary (checkOnly returns exitCode some 0 not some 1): EXIT 1, ⊢ False.
- atk_3 control-flow-effect (writer flags swapped: mergeIntoLast sets wroteNew): EXIT 1, ⊢ False.
- atk_4 partial-domain (checkOnly ignored, always emit output): EXIT 1, ⊢ False.
- atk_5 ungrounded-oracle echo (match-expression producing gold triple for all 8 inputs): EXIT 0, verifies.
- atk_6 drop the no-changes guard (emits even with no changes): EXIT 1, ⊢ False in cases false.true.*.
- atk_7 checkOnly requests exit BUT also sets wroteNew: EXIT 1, ⊢ False.
Positive control pos_gold (exact gold impl): EXIT 0.

AXIOM CHECK on the two closing proofs (appended `#print axioms correct_processChanges`, re-verified EXIT 0): atk_5 => 'correct_processChanges' depends on axioms: [propext]; pos_gold => [propext]. Clean — no sorryAx, no user _prop axioms.

MANDATORY RESOLVE on the only closing wrong-impl (atk_5): atk_5 is behaviorally gold-equivalent, so its faithful refined patch IS the gold control-flow hunk (exit guard hoisted before writers). Materialized at faithful_atk_5.diff. run_resolve via swebench_unified.harness initially returned 'no report — harness error or image pull failure' TWICE (run_ids ...-atk5, ...-atk5b) — pure infra artifact under live-concurrent runs docker contention (docker system df showed 306 images/47 containers, many concurrent sbu-resolve-* runs; docs warn one-backend-at-a-time). Re-ran the underlying harness DIRECTLY (docker -c python -m swebench_unified.run_evaluation ... --instance_ids django__django-16116, run_id sbu-resolve-audit-eq-zmm2kna1-atk5-direct): result 'Instances resolved: 1'. report.json: resolved=true, patch_successfully_applied=true, FAIL_TO_PASS success=['makemigrations --check should exit with a non-zero status when'], PASS_TO_PASS all success. => atk_5's faithful patch RESOLVES; it does NOT break the spec.

CONCLUSION: The spec admits no same-spec wrong impl with a closing clean-axiom proof whose faithful patch fails to resolve. Every genuinely-wrong impl (prepatch, boundary, control-flow, partial-domain, ungrounded, no-changes-drop, checkOnly-also-writes) fails the closing proof with a concrete ⊢ False. The one closing impl is a correct gold echo that resolves. No A-legs to attack. verify => correct holds. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-16116 lean bundle.

Modeled symbol: the else-arm of Command.handle() in django/core/management/commands/makemigrations.py (post-patch). Inputs: hasChanges=bool(changes), checkOnly=check_changes, mergeIntoLast=self.update.

Real post-patch control flow (confirmed against gold patch and base_commit source):
  if not changes: <log only, no writer, no exit>
  else:
    if check_changes: sys.exit(1)          # hoisted BEFORE writers
    if self.update: write_to_last_migration_files(...)
    else: write_migration_files(...)

spec problem_spec_processChanges pins ALL three observables for every input:
  * !hasChanges -> wroteToLast=false, wroteNew=false, exitCode=none. Matches: no-changes arm logs only, emits nothing, no exit. (mergeIntoLast/checkOnly irrelevant — real code never reaches writers/exit here.)
  * hasChanges & checkOnly -> false/false/some 1. Matches: sys.exit(1) fires before any writer, so neither writer runs; regardless of mergeIntoLast. Correct that mergeIntoLast is ignored here.
  * hasChanges & !checkOnly & mergeIntoLast -> wroteToLast=true, wroteNew=false, exitCode=none. Matches write_to_last_migration_files, no exit.
  * hasChanges & !checkOnly & !mergeIntoLast -> wroteNew=true, wroteToLast=false, exitCode=none. Matches write_migration_files, no exit.

Enumerated all 8 combinations; spec agrees with real callee on each. No input found where the spec diverges from real repo behavior. Modeling of writers as Boolean 'did-run' flags and sys.exit(1) as exitCode=some 1 is a sound observable abstraction for the F2P test (SystemExit raised AND no migration dir written).

Mechanics verified: Solution.lean compiles + no sorry (lean_verify exit 0); #print axioms correct_processChanges -> [propext] only, no sorryAx, proof genuine. Spec matches gold patch region. No spec-too-strong / drift defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no gold-patch line reproduced >=8 chars, no patched file path/module, no patched-symbol identifier/comment collision, no narration keywords). same_spec(prepatch, postpatch)=True — the spec view is byte-identical across the gold patch, so the spec itself does not encode the edit; the gold change is a control-flow REORDERING (hoist `if check_changes: sys.exit(1)` above the writers) which is entirely below the impl/proof elision line and never appears in the spec view.

Semantic check against the PUBLIC problem_statement (NOT hints): the problem_statement explicitly states the target behavior — 'makemigrations --check should just exit without making migrations.' The spec's discriminating post-condition (checkOnly => wroteToLast=false, wroteNew=false, exitCode=some 1) is a faithful formalization of that already-public requirement, not an over-disclosure. The other clauses (mergeIntoLast writer selection, no-changes normal completion) describe baseline command behavior, not the fix. Identifiers are abstract (processChanges, CommandEffect, wroteToLast); patched repo symbols (handle, add_arguments) do not appear. Axioms/docstrings describe modeling choices abstractly with no bug/fix/prepatch narration. A solver reading the spec learns nothing about the fix mechanism beyond the public issue. No leakage.

Lean verification not re-run for the panel-3 leakage judgment (out of scope for leakage; spec_view projection and same_spec computed directly via swebench_unified.markers).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
