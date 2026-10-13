# P2 adversarial audit — scikit-learn__scikit-learn-11310

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

Counterexample / evidence:

```
None that breaks the spec. The only verifying wrong impls are divergent (while-true) impls (atk_7, atk_8), whose faithful patches apply cleanly but HANG the FAIL_TO_PASS test -> harness 'Test timed out' -> no report -> run_resolve completed=False (NOT the BROKEN condition 'completed and not resolved'). Divergence-verifies is the universal partial-correctness artifact ('termination partial'), a documented non-defect (build_one.py:225), not a spec weakness; G-RESOLVE catches it dynamically by timeout.
```

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
 /- The process wall clock, read twice across one synchronous unit of work, is
@@ -66,12 +66,8 @@
   ensures refit = false → refitTime = none
   do
     -- impl-start
-    -- Record the refit duration only when refitting is requested: store the
-    -- elapsed span between the two wall-clock readings bracketing the refit
-    -- work. The readings are non-decreasing (precondition), so the recorded
-    -- span is ≥ 0. Otherwise leave the slot untouched (absent).
+    -- prepatch bug: never records the duration
     if refit then
-      refitTime := some (endT - startT)
       return ()
     else
       return ()
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
 /- The process wall clock, read twice across one synchronous unit of work, is
@@ -66,12 +66,8 @@
   ensures refit = false → refitTime = none
   do
     -- impl-start
-    -- Record the refit duration only when refitting is requested: store the
-    -- elapsed span between the two wall-clock readings bracketing the refit
-    -- work. The readings are non-decreasing (precondition), so the recorded
-    -- span is ≥ 0. Otherwise leave the slot untouched (absent).
     if refit then
-      refitTime := some (endT - startT)
+      refitTime := some 0
       return ()
     else
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
 /- The process wall clock, read twice across one synchronous unit of work, is
@@ -66,12 +66,8 @@
   ensures refit = false → refitTime = none
   do
     -- impl-start
-    -- Record the refit duration only when refitting is requested: store the
-    -- elapsed span between the two wall-clock readings bracketing the refit
-    -- work. The readings are non-decreasing (precondition), so the recorded
-    -- span is ≥ 0. Otherwise leave the slot untouched (absent).
     if refit then
-      refitTime := some (endT - startT)
+      refitTime := some (startT - endT)
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
 /- The process wall clock, read twice across one synchronous unit of work, is
@@ -66,14 +66,10 @@
   ensures refit = false → refitTime = none
   do
     -- impl-start
-    -- Record the refit duration only when refitting is requested: store the
-    -- elapsed span between the two wall-clock readings bracketing the refit
-    -- work. The readings are non-decreasing (precondition), so the recorded
-    -- span is ≥ 0. Otherwise leave the slot untouched (absent).
     if refit then
-      refitTime := some (endT - startT)
       return ()
     else
+      refitTime := some (endT - startT)
       return ()
     -- impl-end
 
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
 /- The process wall clock, read twice across one synchronous unit of work, is
@@ -66,12 +66,8 @@
   ensures refit = false → refitTime = none
   do
     -- impl-start
-    -- Record the refit duration only when refitting is requested: store the
-    -- elapsed span between the two wall-clock readings bracketing the refit
-    -- work. The readings are non-decreasing (precondition), so the recorded
-    -- span is ≥ 0. Otherwise leave the slot untouched (absent).
     if refit then
-      refitTime := some (endT - startT)
+      refitTime := some (endT - startT + 1)
       return ()
     else
       return ()
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
 /- The process wall clock, read twice across one synchronous unit of work, is
@@ -66,12 +66,11 @@
   ensures refit = false → refitTime = none
   do
     -- impl-start
-    -- Record the refit duration only when refitting is requested: store the
-    -- elapsed span between the two wall-clock readings bracketing the refit
-    -- work. The readings are non-decreasing (precondition), so the recorded
-    -- span is ≥ 0. Otherwise leave the slot untouched (absent).
     if refit then
-      refitTime := some (endT - startT)
+      if endT = startT then
+        refitTime := some (endT - startT)
+      else
+        refitTime := some 0
       return ()
     else
       return ()
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The process wall clock, read twice across one synchronous unit of work, is
   non-decreasing: a reading taken after the work is never earlier than a reading
   taken before it. The two readings are environment-provided values produced by
   an UNCHANGED callee; they enter the method as the inputs `startT` (taken
   immediately before the work) and `endT` (taken immediately after it), and the
   monotonicity contract is stated as the precondition `startT ≤ endT` — the
   axiom's domain. The postcondition must then hold for EVERY reading pair the
   real clock can produce (the proof is universally quantified over all inputs
   satisfying non-decrease), so nothing stronger than non-decrease is assumed
   (we never pin how much the clock advanced). This is the weakest fact
   sufficient to guarantee the recorded duration is non-negative. Provenance +
   executable soundness check: mapping.md §3 / axiom_check.py (G-AX). -/
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- After a hyperparameter search selects its best configuration, it may refit
   that configuration on the whole dataset. When it does, the duration of that
   single refit is a quantity a consumer needs to be able to read back: the time
   spent refitting the best model on the full data.

   The desired behavior: a single request flag governs whether the refit happens.
   When refitting is requested, the elapsed duration of the refit — the wall
   clock read immediately after the refit minus the wall clock read immediately
   before it — is recorded as a present value; because consecutive readings are
   non-decreasing (the precondition, see the axiom note above) that recorded
   span is never negative. When refitting is NOT requested, no duration is
   recorded — the slot stays absent.

   `refit` is the read-only request flag (not `mut`): the routine decides based
   on it and never alters it (directive 5). `startT` and `endT` are the two
   wall-clock readings bracketing the refit work, environment-provided by the
   unchanged clock callee (read-only inputs). `refitTime` is the
   recorded-duration slot (`mut`, genuinely written): it comes in absent
   (`none`) for a fresh search and, when refitting is requested, is set to
   exactly the elapsed span `endT - startT` — the recorded value is pinned to
   the very subtraction of the two readings, not merely to some non-negative
   value; when refitting is not requested its post-state is pinned exactly to
   its unchanged entry value `none` (directive 5: the unchanged frame is stated
   exactly). Durations are modeled as exact rationals (`Rat`): the recorded
   observable is a single subtraction of two same-magnitude clock readings,
   which is exact (mapping.md §2), so an exact ordered carrier is faithful. -/
method recordRefitTime (refit : Bool) (startT : Rat) (endT : Rat)
    (mut refitTime : Option Rat) return (unit : Unit)
  require refitTime = none
  require startT ≤ endT
  ensures refit = true  → refitTime = some (endT - startT)
  ensures refit = true  → (∃ t : Rat, refitTime = some t ∧ t ≥ 0)
  ensures refit = false → refitTime = none
  do
    -- impl-start
    -- Record the refit duration only when refitting is requested: store the
    -- elapsed span between the two wall-clock readings bracketing the refit
    -- work. The readings are non-decreasing (precondition), so the recorded
    -- span is ≥ 0. Otherwise leave the slot untouched (absent).
    if refit then
      refitTime := some (endT - startT)
      return ()
    else
      return ()
    -- impl-end

prove_correct recordRefitTime by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 8 attacks + pos_control confirmed same_spec=True via swebench_unified.markers.same_spec (velvet). Only the impl region edited.

### VERIFY (bash scripts/lean_verify.sh <f>; run concurrently <=4/batch):
  pos_control (exact gold) -> EXIT 0 (verifies) [positive control, distinct file].
  atk_1 prepatch bug (both branches no-op, never records) -> EXIT 1 (rejected; G-DIFF-consistent). prepatch_reproduced=True.
  atk_2 constant-recording some 0 (ungrounded-oracle/echo) -> EXIT 1.
  atk_3 wrong sign some (startT-endT) -> EXIT 1.
  atk_4 swapped gate (record in the else/not-refit branch; control-flow-effect) -> EXIT 1.
  atk_5 off-by-one some (endT-startT+1) (boundary) -> EXIT 1.
  atk_6 partial-domain (some (endT-startT) only when endT=startT, else some 0) -> EXIT 1.
All six behavioral wrong impls are REJECTED: the repaired spec pins refitTime = some (endT - startT) EXACTLY, so no constant/sign/off-by-one/gate-swap/partial-domain impl verifies. Required attack classes covered by rejected attacks: partial-domain(atk_6), boundary(atk_5), control-flow-effect(atk_4), ungrounded/const echo(atk_2), prepatch(atk_1), sign(atk_3).

### DIVERGENCE ATTACKS (verify but are the documented non-defect; NOT submitted as candidates):
atk_7 unconditional 'while true' -> lean_verify EXIT 0 (verifies vacuously under partial correctness). atk_8 'while true' inside the refit branch -> lean_verify EXIT 0. I materialized faithful refined patches and RAN them through the official harness (NOT speculation): patch_gold.diff -> run_resolve: {resolved:true, completed:true, note:'resolved'} (harness sanity control, ~5 min). patch_atk_8.diff (infinite loop inserted where gold inserts refit_start_time; EXACT gold context) -> run_resolve: {resolved:false, completed:false, note:'no report ... harness error'}.

Manual harness re-run (runid manual-atk8-11310, --timeout 240) CONFIRMS: 'Applied patch ... cleanly', then 'EvaluationError: Test timed out after 240 seconds', NO report.json written. patch_atk_7.diff (unconditional loop before the refit gate) -> run_resolve: {resolved:false, completed:false, 'no report'}. Manual re-run (manual-atk7-11310, --timeout 180): applies (fuzz 3), 'Test timed out after 180 seconds', no report.json. Both divergent patches thus do NOT resolve, but by HANGING (completed=False), which the official derivation (build_one.py:306) routes to inconclusive_hits, NOT to the BROKEN branch that requires completed AND not-resolved.

Divergence vacuously satisfies every postcondition under 'termination partial' and is a universal Velvet artifact + documented non-defect (build_one.py:225 'only divergence'); G-RESOLVE is the complementary total oracle that rejects it by timeout. Hence NOT a verify->correct break of THIS spec. Note: the gold impl is straight-line terminating, so a 'total' termination setting would additionally reject divergence; the partial setting is methodology-permitted but is the sole residual soundness margin here.

REFINEMENT.MD AUDIT: legs = R(1 gate, 4 record) / A-consumed(2 startT, 3 endT: the UNCHANGED time.time() callee, contract stated as require startT<=endT) / I(5 else no-op). No kind-3 leg. A-leg correspondence holds: time.time() is unchanged by the patch (only 'import time' + two calls added); monotone-clock axiom is the weakest fact sufficient for endT-startT>=0 and is universally quantified; NTP step-back caveat documented and G-AX-sampled. R legs bit-exact under G-CONF (endT-startT vs verbatim patch line). Correspondence sound.

FLOOR: 6 same-spec attacks (>=5), all rejected; prepatch reproduced (atk_1); positive control verifies and is a distinct file; no inconclusive candidate resolve was needed (no behavioral attack verified). => derivation yields PASS. Advisory verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None that breaks the spec. The only verifying wrong impls are divergent (while-true) impls (atk_7, atk_8), whose faithful patches apply cleanly but HANG the FAIL_TO_PASS test -> harness 'Test timed out' -> no report -> run_resolve completed=False (NOT the BROKEN condition 'completed and not resolved'). Divergence-verifies is the universal partial-correctness artifact ('termination partial'), a documented non-defect (build_one.py:225), not a spec weakness; G-RESOLVE catches it dynamically by timeout.
```

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
/- The process wall clock, read twice across one synchronous unit of work, is
   non-decreasing: a reading taken after the work is never earlier than a reading
   taken before it. The two readings are environment-provided values produced by
   an UNCHANGED callee; they enter the method as the inputs `startT` (taken
   immediately before the work) and `endT` (taken immediately after it), and the
   monotonicity contract is stated as the precondition `startT ≤ endT` — the
   axiom's domain. The postcondition must then hold for EVERY reading pair the
   real clock can produce (the proof is universally quantified over all inputs
   satisfying non-decrease), so nothing stronger than non-decrease is assumed
   (we never pin how much the clock advanced). This is the weakest fact
   sufficient to guarantee the recorded duration is non-negative. Provenance +
   executable soundness check: mapping.md §3 / axiom_check.py (G-AX). -/
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- After a hyperparameter search selects its best configuration, it may refit
   that configuration on the whole dataset. When it does, the duration of that
   single refit is a quantity a consumer needs to be able to read back: the time
   spent refitting the best model on the full data.

   The desired behavior: a single request flag governs whether the refit happens.
   When refitting is requested, the elapsed duration of the refit — the wall
   clock read immediately after the refit minus the wall clock read immediately
   before it — is recorded as a present value; because consecutive readings are
   non-decreasing (the precondition, see the axiom note above) that recorded
   span is never negative. When refitting is NOT requested, no duration is
   recorded — the slot stays absent.

   `refit` is the read-only request flag (not `mut`): the routine decides based
   on it and never alters it (directive 5). `startT` and `endT` are the two
   wall-clock readings bracketing the refit work, environment-provided by the
   unchanged clock callee (read-only inputs). `refitTime` is the
   recorded-duration slot (`mut`, genuinely written): it comes in absent
   (`none`) for a fresh search and, when refitting is requested, is set to
   exactly the elapsed span `endT - startT` — the recorded value is pinned to
   the very subtraction of the two readings, not merely to some non-negative
   value; when refitting is not requested its post-state is pinned exactly to
   its unchanged entry value `none` (directive 5: the unchanged frame is stated
   exactly). Durations are modeled as exact rationals (`Rat`): the recorded
   observable is a single subtraction of two same-magnitude clock readings,
   which is exact (mapping.md §2), so an exact ordered carrier is faithful. -/
method recordRefitTime (refit : Bool) (startT : Rat) (endT : Rat)
    (mut refitTime : Option Rat) return (unit : Unit)
  require refitTime = none
  require startT ≤ endT
  ensures refit = true  → refitTime = some (endT - startT)
  ensures refit = true  → (∃ t : Rat, refitTime = some t ∧ t ≥ 0)
  ensures refit = false → refitTime = none
  do
    -- impl-start
    -- Record the refit duration only when refitting is requested: store the
    -- elapsed span between the two wall-clock readings bracketing the refit
    -- work. The readings are non-decreasing (precondition), so the recorded
    -- span is ≥ 0. Otherwise leave the slot untouched (absent).
    if refit then
      refitTime := some (endT - startT)
      return ()
    else
      return ()
    -- impl-end

prove_correct recordRefitTime by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 8 attacks + pos_control confirmed same_spec=True via swebench_unified.markers.same_spec (velvet). Only the impl region edited.

### VERIFY (bash scripts/lean_verify.sh <f>; run concurrently <=4/batch):
  pos_control (exact gold) -> EXIT 0 (verifies) [positive control, distinct file].
  atk_1 prepatch bug (both branches no-op, never records) -> EXIT 1 (rejected; G-DIFF-consistent). prepatch_reproduced=True.
  atk_2 constant-recording some 0 (ungrounded-oracle/echo) -> EXIT 1.
  atk_3 wrong sign some (startT-endT) -> EXIT 1.
  atk_4 swapped gate (record in the else/not-refit branch; control-flow-effect) -> EXIT 1.
  atk_5 off-by-one some (endT-startT+1) (boundary) -> EXIT 1.
  atk_6 partial-domain (some (endT-startT) only when endT=startT, else some 0) -> EXIT 1.
All six behavioral wrong impls are REJECTED: the repaired spec pins refitTime = some (endT - startT) EXACTLY, so no constant/sign/off-by-one/gate-swap/partial-domain impl verifies. Required attack classes covered by rejected attacks: partial-domain(atk_6), boundary(atk_5), control-flow-effect(atk_4), ungrounded/const echo(atk_2), prepatch(atk_1), sign(atk_3).

### DIVERGENCE ATTACKS (verify but are the documented non-defect; NOT submitted as candidates):
atk_7 unconditional 'while true' -> lean_verify EXIT 0 (verifies vacuously under partial correctness). atk_8 'while true' inside the refit branch -> lean_verify EXIT 0. I materialized faithful refined patches and RAN them through the official harness (NOT speculation): patch_gold.diff -> run_resolve: {resolved:true, completed:true, note:'resolved'} (harness sanity control, ~5 min). patch_atk_8.diff (infinite loop inserted where gold inserts refit_start_time; EXACT gold context) -> run_resolve: {resolved:false, completed:false, note:'no report ... harness error'}.

Manual harness re-run (runid manual-atk8-11310, --timeout 240) CONFIRMS: 'Applied patch ... cleanly', then 'EvaluationError: Test timed out after 240 seconds', NO report.json written. patch_atk_7.diff (unconditional loop before the refit gate) -> run_resolve: {resolved:false, completed:false, 'no report'}. Manual re-run (manual-atk7-11310, --timeout 180): applies (fuzz 3), 'Test timed out after 180 seconds', no report.json. Both divergent patches thus do NOT resolve, but by HANGING (completed=False), which the official derivation (build_one.py:306) routes to inconclusive_hits, NOT to the BROKEN branch that requires completed AND not-resolved.

Divergence vacuously satisfies every postcondition under 'termination partial' and is a universal Velvet artifact + documented non-defect (build_one.py:225 'only divergence'); G-RESOLVE is the complementary total oracle that rejects it by timeout. Hence NOT a verify->correct break of THIS spec. Note: the gold impl is straight-line terminating, so a 'total' termination setting would additionally reject divergence; the partial setting is methodology-permitted but is the sole residual soundness margin here.

REFINEMENT.MD AUDIT: legs = R(1 gate, 4 record) / A-consumed(2 startT, 3 endT: the UNCHANGED time.time() callee, contract stated as require startT<=endT) / I(5 else no-op). No kind-3 leg. A-leg correspondence holds: time.time() is unchanged by the patch (only 'import time' + two calls added); monotone-clock axiom is the weakest fact sufficient for endT-startT>=0 and is universally quantified; NTP step-back caveat documented and G-AX-sampled. R legs bit-exact under G-CONF (endT-startT vs verbatim patch line). Correspondence sound.

FLOOR: 6 same-spec attacks (>=5), all rejected; prepatch reproduced (atk_1); positive control verifies and is a distinct file; no inconclusive candidate resolve was needed (no behavioral attack verified). => derivation yields PASS. Advisory verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Solution.lean compiles clean via lean_verify.sh (exit 0). same_spec(Solution, Solution_prepatch) = True — the spec region (axioms/pure/pre/post + method signature & contracts) is byte-identical between patched and prepatch; only the impl-start/impl-end region and prove_correct body differ. Faithfulness assessment vs real repo (BaseSearchCV.fit refit slice, _search.py:766–773 gold-patched): (1) refit gate ⇔ if self.refit; (2) startT/endT ⇔ the two time.time() readings, modeled as read-only inputs of an UNCHANGED callee; (3) refitTime := some(endT-startT) ⇔ self.refit_time_ = refit_end_time - refit_start_time — pinned EXACTLY, so no drift-toward-too-strong that a faithful impl couldn't meet; (4) refit=false → refitTime=none ⇔ attribute never assigned under falsy gate (base-commit absent). Potential over-strength checks: (a) require startT ≤ endT only NARROWS the domain (weakness direction) — it cannot make the postcondition disagree with the repo; it excludes the NTP clock-backward case, a documented, legitimate domain restriction matching the test's assumption. (b) require refitTime=none matches the fresh-search base state (attribute absent). (c) The Rat model vs float64: exact on the entire realizable clock domain (Sterbenz), so the spec's exact-subtraction postcondition holds for every reading pair the real time.time() produces. No input the real callee can generate makes the modeled function disagree with the repo. The spec is NOT too strong / does not drift from real behavior.

Counterexample / evidence:

```
No counterexample on the real callee's output domain. Off-domain probe (unrealizable): startT=1.0, endT=1e20 → repo float 1e20 vs spec Rat 1e20-1 (exact 99999999999999999999); excluded because time.time() cannot yield such a pair across a single refit.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, no hard failures/warnings) and same_spec(patched, prepatch) is byte-identical for the velvet spec region. Rigorous semantic check confirms no leakage beyond the public problem_statement:

Public problem_statement already discloses the whole feature: it explicitly requests 'an attribute refit_time_ which is simply the time it took to refit the best model on the full data' after grid/random search. The gold patch is the obvious realization: bracket the pre-existing refit fit() call with two time.time() reads, subtract, and store the elapsed in self.refit_time_, guarded by the pre-existing `if self.refit:`.

Spec view content:
- All identifiers are abstracted (recordRefitTime, refit, startT, endT, refitTime). Even refit_time_ — which the problem_statement names verbatim — is abstracted to `refitTime`. No gold symbol (BaseSearchCV, _store, time.time), no patched file path (_search.py), no diff markers, no line numbers, no bug/fix narration.
- Pinned contract (refit=true → refitTime = some (endT - startT); non-negativity on monotone domain; refit=false → none) states the OBSERVABLE the problem_statement requests. 'The time it took to refit' is by definition end-minus-start of the bracketing readings; this is definitional, not a non-obvious discriminator recoverable only from the gold diff.
- The `if self.refit` gate that the branch mirrors is pre-existing repo code, not the gold edit itself.
- Prose stays at requirements/use-case altitude ('a quantity a consumer needs to read back: the time spent refitting the best model on the full data'), matching the problem_statement's own framing, and never narrates the diff or its localization.

Nothing in the spec view lets an attacker reconstruct the gold edit that the public problem_statement does not already hand them. Not relaxed (no RELAXED_LEAKAGE.md / relaxed flag needed).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).