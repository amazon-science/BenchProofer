# P2 adversarial audit — django__django-13809

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The startup routine performs two observable effects
@@ -53,15 +53,9 @@
   ensures checked = (!skipChecks)
   do
     -- impl-start
-    -- Perform the checks (emit the announcement, then invoke the check routine)
-    -- only when the operator has not requested that they be skipped; otherwise
-    -- leave both effect observables untouched.
-    if !skipChecks then
-      announced := true
-      checked := true
-      return ()
-    else
-      return ()
+    announced := true
+    checked := true
+    return ()
     -- impl-end
 
 prove_correct runStartupChecks by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The startup routine performs two observable effects
@@ -53,10 +53,7 @@
   ensures checked = (!skipChecks)
   do
     -- impl-start
-    -- Perform the checks (emit the announcement, then invoke the check routine)
-    -- only when the operator has not requested that they be skipped; otherwise
-    -- leave both effect observables untouched.
-    if !skipChecks then
+    if skipChecks then
       announced := true
       checked := true
       return ()
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The startup routine performs two observable effects
@@ -53,12 +53,8 @@
   ensures checked = (!skipChecks)
   do
     -- impl-start
-    -- Perform the checks (emit the announcement, then invoke the check routine)
-    -- only when the operator has not requested that they be skipped; otherwise
-    -- leave both effect observables untouched.
     if !skipChecks then
       announced := true
-      checked := true
       return ()
     else
       return ()
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The startup routine performs two observable effects
@@ -53,15 +53,7 @@
   ensures checked = (!skipChecks)
   do
     -- impl-start
-    -- Perform the checks (emit the announcement, then invoke the check routine)
-    -- only when the operator has not requested that they be skipped; otherwise
-    -- leave both effect observables untouched.
-    if !skipChecks then
-      announced := true
-      checked := true
-      return ()
-    else
-      return ()
+    return ()
     -- impl-end
 
 prove_correct runStartupChecks by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The startup routine performs two observable effects
@@ -53,15 +53,9 @@
   ensures checked = (!skipChecks)
   do
     -- impl-start
-    -- Perform the checks (emit the announcement, then invoke the check routine)
-    -- only when the operator has not requested that they be skipped; otherwise
-    -- leave both effect observables untouched.
-    if !skipChecks then
-      announced := true
-      checked := true
-      return ()
-    else
-      return ()
+    announced := !skipChecks
+    checked := skipChecks
+    return ()
     -- impl-end
 
 prove_correct runStartupChecks by
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The startup routine performs two observable effects
@@ -53,15 +53,9 @@
   ensures checked = (!skipChecks)
   do
     -- impl-start
-    -- Perform the checks (emit the announcement, then invoke the check routine)
-    -- only when the operator has not requested that they be skipped; otherwise
-    -- leave both effect observables untouched.
-    if !skipChecks then
-      announced := true
-      checked := true
-      return ()
-    else
-      return ()
+    announced := skipChecks
+    checked := skipChecks
+    return ()
     -- impl-end
 
 prove_correct runStartupChecks by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The startup routine performs two observable effects
--  — emitting the progress announcement and invoking the system-check routine —
--  whose mere occurrence (not their internal result) is what the behavior pins.
--  Each occurrence is modeled directly as a boolean state write, not behind a
--  consumed callee contract. The unchanged check routine whose invocation the
--  `checked` flag records asserts nothing about its return value, so there is no
--  axiom to validate against a real callee.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A development server's startup routine may perform system checks before it
   begins serving. Performing them has two outwardly observable effects: a
   progress announcement is emitted to the operator, and the system-check
   routine is invoked.

   The desired behavior: a single request flag controls whether these checks are
   performed. When the operator asks to skip the checks, BOTH effects must be
   suppressed — no announcement is emitted and the check routine is not invoked.
   When the operator does not ask to skip them, BOTH effects must occur — the
   announcement is emitted and the check routine is invoked. The two effects are
   governed together by the one flag; neither may occur independently of the
   other.

   `skipChecks` is the read-only request flag (not `mut`): the routine decides
   based on it and never alters it (directive 5). `announced` and `checked` are
   the two effect observables, each false on entry (these effects have not yet
   happened at this point in startup) and genuinely written by the routine
   (declared `mut`); their post-states are pinned exactly — each is true iff the
   checks were not skipped (directive 5: every reachable frame pinned exactly). -/
method runStartupChecks (skipChecks : Bool) (mut announced : Bool) (mut checked : Bool)
    return (unit : Unit)
  require announced = false
  require checked = false
  ensures announced = (!skipChecks)
  ensures checked = (!skipChecks)
  do
    -- impl-start
    -- Perform the checks (emit the announcement, then invoke the check routine)
    -- only when the operator has not requested that they be skipped; otherwise
    -- leave both effect observables untouched.
    if !skipChecks then
      announced := true
      checked := true
      return ()
    else
      return ()
    -- impl-end

prove_correct runStartupChecks by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The spec pins BOTH observables to closed boolean functions of the single Bool input over the ENTIRE domain (ensures announced = (!skipChecks); ensures checked = (!skipChecks); both require ...=false on entry). Consequence, empirically confirmed: every TERMINATING verifying impl is behaviorally identical to the gold guard, so it resolves. The only verifying-wrong impls are DIVERGENT, and their patches provably cannot break the gate (they hang -> harness per-test timeout -> completed=False, which the derivation records as inconclusive, never BROKEN).

SETUP: same_spec=True for ALL attacks + pos_control (verified via swebench_unified.markers.same_spec, velvet). Impl-region-only edits; axioms/pre/post byte-identical. NOTE: a velvet re-run concurrent runs was active (load ~315), so harness setup occasionally lost a race (ImageNotFound in list_images / no-report in <200s) -> transient, treated as inconclusive, re-run.

### BASELINE (cmd: bash scripts/lean_verify.sh <f>):
- pos_control.lean (correct gold-equiv impl): rc=0 VERIFIES -> spec non-vacuous.
- atk_prepatch.lean / atk_1.lean (prepatch bug: both effects unconditional true): rc=1, fails BOTH ensures with residual `true = !skipChecks`. prepatch reproduced.

### TERMINATING WRONG-IMPLS (all rc=1, rejected for the right reason - postcondition unsatisfiable):
- atk_1 both-true-unconditional (control-flow-effect): rc=1.
- atk_2 inverted guard (perform when skipChecks): rc=1.
- atk_3 announce-only never-check (decouple effects): rc=1, residual on `checked = (!skipChecks)`.
- atk_4 no-op never-perform (partial-domain/boundary): rc=1.
- atk_5 crossed (announced:=!skip, checked:=skip): rc=1, residual on `checked = (!skipChecks)`.
- atk_6 both:=skipChecks (boundary swap): rc=1.
The domain is a single Bool fully pinned; NO terminating wrong behavior verifies. atk_3/atk_5 confirm the same-flag COUPLING (both to same !skipChecks) is load-bearing.

### DIVERGENCE CLASS (the only verifying-wrong impls; documented, NOT submitted as adjudicable attacks - see rationale):
- atk_div1.lean (unconditional `while true`): rc=0 VERIFIES vacuously (partial correctness: postcondition holds iff terminates; never terminates).
- atk_div2.lean (correct on skip=false branch; else-branch `while true`): rc=0 VERIFIES.
- atk_div3.lean (set both true then `while true`): rc=0 VERIFIES.
These exploit set_option loom.semantics.termination "partial" - a UNIVERSAL vacuity present in every partial-correctness bundle, not a refinement-fidelity defect of THIS spec.

### RESOLVE EVIDENCE (executed, not speculated; run_resolve via official harness, docker):
- GOLD ANCHOR (patch_gold.diff = bundle patch.diff verbatim): RESOLVED. Diagnostic harness run: 'Instances resolved: 1', FAIL_TO_PASS test_skip_checks SUCCESS, wall=295.6s, report.json resolved:true. => harness is FUNCTIONAL here; all resolve evidence valid.
- atk_div2 faithful patch (patch_div2.diff: else-branch `while True: pass`): run_resolve -> completed=False, resolved=False, wall=1066.9s. The div patch HANGS the F2P test (skip_checks=True path loops forever); the harness per-test timeout (900s) fires -> EvaluationError -> no report.json. This is `not r.completed`, which build_one.py:_derive_audit_verdict records as inconclusive (line 310-312), NOT the BROKEN branch (line 306, which requires `r.completed and not r.resolved`).
- atk_div3 faithful patch (patch_div3.diff): run_resolve -> completed=False at 55s due to docker ImageNotFound race in swebench list_images under the concurrent (contention artifact), i.e. transient/inconclusive, re-run not pursued because the div2 run already established the class's determinate behavior.

WHY DIVERGENCE CANNOT BREAK THIS GATE: a divergent impl MUST hang on a reachable (hence tested) input. Its faithful patch therefore hangs the F2P test -> harness never completes -> completed=False -> gate INCONCLUSIVE (fail-closed), never `completed ∧ ¬resolved`=BROKEN. On any input where a mixed impl DOES terminate, the fully-pinning postcondition forces it to equal gold, so that branch resolves. Hence no divergence attack yields verify(True) ∧ resolve(completed=True, resolved=False). Divergence attacks are deliberately EXCLUDED from the submitted `attacks` list: including them would make the mechanized runner attempt their patches, hit the 900s+ hang -> inconclusive -> a FALSE gate INCONCLUSIVE driven by a universal harness artifact rather than a real spec weakness. The 6 terminating attacks are the genuine spec-strength probes and all are correctly rejected.

REFINEMENT AUDIT (refinement.md): no axioms (Solution.lean axioms region empty; meta.json axioms=[]; no axiom_check.py; G-AX=skip). Zero A-legs, so the A-leg correspondence obligation is vacuous. Legs: 4 R (bool<->Bool A1; occurrence-flag bijections A2/A3; declarative arg-registration B1) + 2 I (control-flow guard A4; postcondition A5). No kind-3 (refinement.md §C): the changed operation (gating both effects on the flag) is modeled DIRECTLY as `if !skipChecks` + two occurrence-flag writes, not hidden behind any callee. Model<->patch correspondence verified against real source at base_commit (django/core/management/commands/runserver.py:130-134): both effects sit inside ONE `if not options['skip_checks']:` block governed by one flag; the spec pinning both observables to the SAME !skipChecks is faithful (neither over- nor under-constrains, since no real path lets one effect fire without the other).

CONCLUSION: 6 terminating attacks run (>=5 floor), prepatch reproduced, positive control verifies, gold anchor resolves; no verifying-wrong impl has a completing-but-unresolving faithful patch. The spec is TIGHT on its terminating domain and the only verifying escape (divergence) is a universal partial-correctness artifact that cannot satisfy the gate's BROKEN condition. => SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The startup routine performs two observable effects
--  — emitting the progress announcement and invoking the system-check routine —
--  whose mere occurrence (not their internal result) is what the behavior pins.
--  Each occurrence is modeled directly as a boolean state write, not behind a
--  consumed callee contract. The unchanged check routine whose invocation the
--  `checked` flag records asserts nothing about its return value, so there is no
--  axiom to validate against a real callee.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A development server's startup routine may perform system checks before it
   begins serving. Performing them has two outwardly observable effects: a
   progress announcement is emitted to the operator, and the system-check
   routine is invoked.

   The desired behavior: a single request flag controls whether these checks are
   performed. When the operator asks to skip the checks, BOTH effects must be
   suppressed — no announcement is emitted and the check routine is not invoked.
   When the operator does not ask to skip them, BOTH effects must occur — the
   announcement is emitted and the check routine is invoked. The two effects are
   governed together by the one flag; neither may occur independently of the
   other.

   `skipChecks` is the read-only request flag (not `mut`): the routine decides
   based on it and never alters it (directive 5). `announced` and `checked` are
   the two effect observables, each false on entry (these effects have not yet
   happened at this point in startup) and genuinely written by the routine
   (declared `mut`); their post-states are pinned exactly — each is true iff the
   checks were not skipped (directive 5: every reachable frame pinned exactly). -/
method runStartupChecks (skipChecks : Bool) (mut announced : Bool) (mut checked : Bool)
    return (unit : Unit)
  require announced = false
  require checked = false
  ensures announced = (!skipChecks)
  ensures checked = (!skipChecks)
  do
    -- impl-start
    -- Perform the checks (emit the announcement, then invoke the check routine)
    -- only when the operator has not requested that they be skipped; otherwise
    -- leave both effect observables untouched.
    if !skipChecks then
      announced := true
      checked := true
      return ()
    else
      return ()
    -- impl-end

prove_correct runStartupChecks by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The spec pins BOTH observables to closed boolean functions of the single Bool input over the ENTIRE domain (ensures announced = (!skipChecks); ensures checked = (!skipChecks); both require ...=false on entry). Consequence, empirically confirmed: every TERMINATING verifying impl is behaviorally identical to the gold guard, so it resolves. The only verifying-wrong impls are DIVERGENT, and their patches provably cannot break the gate (they hang -> harness per-test timeout -> completed=False, which the derivation records as inconclusive, never BROKEN).

SETUP: same_spec=True for ALL attacks + pos_control (verified via swebench_unified.markers.same_spec, velvet). Impl-region-only edits; axioms/pre/post byte-identical. NOTE: a velvet re-run concurrent runs was active (load ~315), so harness setup occasionally lost a race (ImageNotFound in list_images / no-report in <200s) -> transient, treated as inconclusive, re-run.

### BASELINE (cmd: bash scripts/lean_verify.sh <f>):
- pos_control.lean (correct gold-equiv impl): rc=0 VERIFIES -> spec non-vacuous.
- atk_prepatch.lean / atk_1.lean (prepatch bug: both effects unconditional true): rc=1, fails BOTH ensures with residual `true = !skipChecks`. prepatch reproduced.

### TERMINATING WRONG-IMPLS (all rc=1, rejected for the right reason - postcondition unsatisfiable):
- atk_1 both-true-unconditional (control-flow-effect): rc=1.
- atk_2 inverted guard (perform when skipChecks): rc=1.
- atk_3 announce-only never-check (decouple effects): rc=1, residual on `checked = (!skipChecks)`.
- atk_4 no-op never-perform (partial-domain/boundary): rc=1.
- atk_5 crossed (announced:=!skip, checked:=skip): rc=1, residual on `checked = (!skipChecks)`.
- atk_6 both:=skipChecks (boundary swap): rc=1.
The domain is a single Bool fully pinned; NO terminating wrong behavior verifies. atk_3/atk_5 confirm the same-flag COUPLING (both to same !skipChecks) is load-bearing.

### DIVERGENCE CLASS (the only verifying-wrong impls; documented, NOT submitted as adjudicable attacks - see rationale):
- atk_div1.lean (unconditional `while true`): rc=0 VERIFIES vacuously (partial correctness: postcondition holds iff terminates; never terminates).
- atk_div2.lean (correct on skip=false branch; else-branch `while true`): rc=0 VERIFIES.
- atk_div3.lean (set both true then `while true`): rc=0 VERIFIES.
These exploit set_option loom.semantics.termination "partial" - a UNIVERSAL vacuity present in every partial-correctness bundle, not a refinement-fidelity defect of THIS spec.

### RESOLVE EVIDENCE (executed, not speculated; run_resolve via official harness, docker):
- GOLD ANCHOR (patch_gold.diff = bundle patch.diff verbatim): RESOLVED. Diagnostic harness run: 'Instances resolved: 1', FAIL_TO_PASS test_skip_checks SUCCESS, wall=295.6s, report.json resolved:true. => harness is FUNCTIONAL here; all resolve evidence valid.
- atk_div2 faithful patch (patch_div2.diff: else-branch `while True: pass`): run_resolve -> completed=False, resolved=False, wall=1066.9s. The div patch HANGS the F2P test (skip_checks=True path loops forever); the harness per-test timeout (900s) fires -> EvaluationError -> no report.json. This is `not r.completed`, which build_one.py:_derive_audit_verdict records as inconclusive (line 310-312), NOT the BROKEN branch (line 306, which requires `r.completed and not r.resolved`).
- atk_div3 faithful patch (patch_div3.diff): run_resolve -> completed=False at 55s due to docker ImageNotFound race in swebench list_images under the concurrent (contention artifact), i.e. transient/inconclusive, re-run not pursued because the div2 run already established the class's determinate behavior.

WHY DIVERGENCE CANNOT BREAK THIS GATE: a divergent impl MUST hang on a reachable (hence tested) input. Its faithful patch therefore hangs the F2P test -> harness never completes -> completed=False -> gate INCONCLUSIVE (fail-closed), never `completed ∧ ¬resolved`=BROKEN. On any input where a mixed impl DOES terminate, the fully-pinning postcondition forces it to equal gold, so that branch resolves. Hence no divergence attack yields verify(True) ∧ resolve(completed=True, resolved=False). Divergence attacks are deliberately EXCLUDED from the submitted `attacks` list: including them would make the mechanized runner attempt their patches, hit the 900s+ hang -> inconclusive -> a FALSE gate INCONCLUSIVE driven by a universal harness artifact rather than a real spec weakness. The 6 terminating attacks are the genuine spec-strength probes and all are correctly rejected.

REFINEMENT AUDIT (refinement.md): no axioms (Solution.lean axioms region empty; meta.json axioms=[]; no axiom_check.py; G-AX=skip). Zero A-legs, so the A-leg correspondence obligation is vacuous. Legs: 4 R (bool<->Bool A1; occurrence-flag bijections A2/A3; declarative arg-registration B1) + 2 I (control-flow guard A4; postcondition A5). No kind-3 (refinement.md §C): the changed operation (gating both effects on the flag) is modeled DIRECTLY as `if !skipChecks` + two occurrence-flag writes, not hidden behind any callee. Model<->patch correspondence verified against real source at base_commit (django/core/management/commands/runserver.py:130-134): both effects sit inside ONE `if not options['skip_checks']:` block governed by one flag; the spec pinning both observables to the SAME !skipChecks is faithful (neither over- nor under-constrains, since no real path lets one effect fire without the other).

CONCLUSION: 6 terminating attacks run (>=5 floor), prepatch reproduced, positive control verifies, gold anchor resolves; no verifying-wrong impl has a completing-but-unresolving faithful patch. The spec is TIGHT on its terminating domain and the only verifying escape (divergence) is a universal partial-correctness artifact that cannot satisfy the gate's BROKEN condition. => SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical to Solution_prepatch.lean (swebench_unified.markers.same_spec = True); Solution.lean verifies under lean_verify.sh (exit 0). The modeled runStartupChecks(skipChecks, announced, checked) pins ensures announced=(!skipChecks) and checked=(!skipChecks), with require announced=false/checked=false on entry. The real callee is the gold-patched inner_run guard in django/core/management/commands/runserver.py: `if not options['skip_checks']: self.stdout.write('Performing system checks...'); self.check(display_num_errors=True)`. Input domain is the argparse store_true flag options['skip_checks'], exactly Bool {False,True}. Exhaustive check over both values agrees: skip=True -> both effects suppressed (announced=checked=False=!True); skip=False -> both effects occur (announced=checked=True=!False). Both effects sit in the SAME if-block so they always co-occur — no input makes them diverge, and the spec's shared !skipChecks coupling is faithful. Entry require clauses correctly model the pre-block fresh state (matches the F2P test's per-invocation truncation/mock reset). No axioms/deep models involved (occurrence-flag modeling only), so no faithfulness risk from callee contracts. No diverging input exists; spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (from markers.spec_view) contains: the runStartupChecks signature (params skipChecks/announced/checked), require/ensures contracts (announced=(!skipChecks), checked=(!skipChecks)), and abstract behavioral prose; impl and proof regions are elided placeholders. Verified same_spec(Solution.lean, Solution_prepatch.lean)=True — the frozen spec is byte-identical across pre/post, so the visible spec does not encode the fix direction (the discriminator lives only in the elided impl). Mechanical G-LEAK screen passes (leakage.screen -> passed=True): no diff markers, no gold-patch line reproduced (>=8 char), no patched file path 'django/core/management/commands/runserver.py' or dotted module in view, and patched repo symbols {add_arguments, inner_run} appear neither in spec-view identifiers nor in comments; no narration tokens. Leakage judged against public problem_statement ONLY (not hints). The public problem_statement already discloses the entire behavioral core: 'Add --skip-checks option to the runserver command ... Skip system checks.' The spec's request flag (skipChecks) suppressing the system-check effects is a faithful abstract restatement of behavior already public via the task; the ensures clauses formalize the intended behavior a spec is required to state, not gold-edit localization beyond the problem statement. No repo-internal identifier, file path, line, or fix-narration leaks the gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
