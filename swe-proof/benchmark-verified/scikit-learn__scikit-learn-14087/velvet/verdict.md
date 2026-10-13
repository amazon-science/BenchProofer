# P2 adversarial audit — scikit-learn__scikit-learn-14087

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
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_2_prepatch2.lean`, `atk_3_ignore_flag.lean`, `atk_4_swap_coef.lean`, `atk_5_swap_aux.lean`, `atk_6_and_flags.lean`, `atk_9_value_guard.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7_echo.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The two decisions modeled here are pure control-flow
@@ -79,9 +79,7 @@
   ensures out.2 = chooseAux auxActive auxValue
   do
     -- impl-start
-    -- Commit the coefficient vector matching the strategy in effect, and the
-    -- auxiliary mixing value only when the auxiliary mode applies.
-    let coef : Coef := if perClassEffective then coefByPerClass else coefByJoint
+    let coef : Coef := if perClassRequested then coefByPerClass else coefByJoint
     let aux : Option Rat := if auxActive then some auxValue else none
     return (coef, aux)
     -- impl-end
```

Attack 2 — `atk_2_prepatch2.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The two decisions modeled here are pure control-flow
@@ -79,10 +79,8 @@
   ensures out.2 = chooseAux auxActive auxValue
   do
     -- impl-start
-    -- Commit the coefficient vector matching the strategy in effect, and the
-    -- auxiliary mixing value only when the auxiliary mode applies.
     let coef : Coef := if perClassEffective then coefByPerClass else coefByJoint
-    let aux : Option Rat := if auxActive then some auxValue else none
+    let aux : Option Rat := some auxValue
     return (coef, aux)
     -- impl-end
 
```

Attack 3 — `atk_3_ignore_flag.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The two decisions modeled here are pure control-flow
@@ -79,9 +79,7 @@
   ensures out.2 = chooseAux auxActive auxValue
   do
     -- impl-start
-    -- Commit the coefficient vector matching the strategy in effect, and the
-    -- auxiliary mixing value only when the auxiliary mode applies.
-    let coef : Coef := if perClassEffective then coefByPerClass else coefByJoint
+    let coef : Coef := coefByJoint
     let aux : Option Rat := if auxActive then some auxValue else none
     return (coef, aux)
     -- impl-end
```

Attack 4 — `atk_4_swap_coef.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The two decisions modeled here are pure control-flow
@@ -79,9 +79,7 @@
   ensures out.2 = chooseAux auxActive auxValue
   do
     -- impl-start
-    -- Commit the coefficient vector matching the strategy in effect, and the
-    -- auxiliary mixing value only when the auxiliary mode applies.
-    let coef : Coef := if perClassEffective then coefByPerClass else coefByJoint
+    let coef : Coef := if perClassEffective then coefByJoint else coefByPerClass
     let aux : Option Rat := if auxActive then some auxValue else none
     return (coef, aux)
     -- impl-end
```

Attack 5 — `atk_5_swap_aux.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The two decisions modeled here are pure control-flow
@@ -79,10 +79,8 @@
   ensures out.2 = chooseAux auxActive auxValue
   do
     -- impl-start
-    -- Commit the coefficient vector matching the strategy in effect, and the
-    -- auxiliary mixing value only when the auxiliary mode applies.
     let coef : Coef := if perClassEffective then coefByPerClass else coefByJoint
-    let aux : Option Rat := if auxActive then some auxValue else none
+    let aux : Option Rat := if auxActive then none else some auxValue
     return (coef, aux)
     -- impl-end
 
```

Attack 6 — `atk_6_and_flags.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The two decisions modeled here are pure control-flow
@@ -79,9 +79,7 @@
   ensures out.2 = chooseAux auxActive auxValue
   do
     -- impl-start
-    -- Commit the coefficient vector matching the strategy in effect, and the
-    -- auxiliary mixing value only when the auxiliary mode applies.
-    let coef : Coef := if perClassEffective then coefByPerClass else coefByJoint
+    let coef : Coef := if (perClassEffective && perClassRequested) then coefByPerClass else coefByJoint
     let aux : Option Rat := if auxActive then some auxValue else none
     return (coef, aux)
     -- impl-end
```

Attack 7 — `atk_9_value_guard.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The two decisions modeled here are pure control-flow
@@ -79,10 +79,8 @@
   ensures out.2 = chooseAux auxActive auxValue
   do
     -- impl-start
-    -- Commit the coefficient vector matching the strategy in effect, and the
-    -- auxiliary mixing value only when the auxiliary mode applies.
     let coef : Coef := if perClassEffective then coefByPerClass else coefByJoint
-    let aux : Option Rat := if auxActive then some auxValue else none
+    let aux : Option Rat := if auxActive && (auxValue == 0) then some auxValue else none
     return (coef, aux)
     -- impl-end
 
```

Attack 8 — `atk_7_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The two decisions modeled here are pure control-flow
@@ -79,11 +79,7 @@
   ensures out.2 = chooseAux auxActive auxValue
   do
     -- impl-start
-    -- Commit the coefficient vector matching the strategy in effect, and the
-    -- auxiliary mixing value only when the auxiliary mode applies.
-    let coef : Coef := if perClassEffective then coefByPerClass else coefByJoint
-    let aux : Option Rat := if auxActive then some auxValue else none
-    return (coef, aux)
+    return (chooseCoef perClassEffective coefByPerClass coefByJoint, chooseAux auxActive auxValue)
     -- impl-end
 
 prove_correct recordClassResult by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two decisions modeled here are pure control-flow
--  choices over values that have ALREADY been produced by surrounding routines:
--  the two candidate coefficient vectors (one per coefficient-array layout), the
--  averaged auxiliary mixing value, and the two strategy/mode flags are all
--  taken as FREE INPUTS. The routine itself calls no further repo function whose
--  contract must be assumed, so there is no unchanged callee to axiomatize and
--  nothing for G-AX to falsify. See mapping.md §3 and refinement.md, all rows
--  R or I.)
-- axioms-end

-- pure-start
/- A fitted coefficient vector, identified abstractly. Only WHICH candidate
   vector is selected is observed here, never the concrete numbers it contains,
   so an exact-rational list is a faithful, decidable carrier (DECISIONS float
   note: model order-only or selection-only quantities with `Rat`, not
   `Float`). -/
abbrev Coef := List Rat

/- The selected coefficient vector for one class, given the effective strategy.
   The surrounding routine has prepared two candidates from the stored
   cross-validation coefficients — one read out under the per-class layout
   (`coefByPerClass`) and one under the joint layout (`coefByJoint`). The vector
   that is meaningful is the one matching the strategy actually in effect: the
   per-class candidate when the effective strategy is the per-class one, the
   joint candidate otherwise. The decision MUST consult the effective strategy,
   not whatever was originally requested (`perClassEffective`, not
   `perClassRequested`) — the two can disagree, and only the effective one names
   the layout the stored coefficients actually have. -/
def chooseCoef (perClassEffective : Bool) (coefByPerClass coefByJoint : Coef) : Coef :=
  if perClassEffective then coefByPerClass else coefByJoint

/- The recorded auxiliary mixing value for one class. An auxiliary mixing value
   exists only when the auxiliary regularization mode is in effect; in that mode
   the surrounding routine has already averaged it (`auxValue`). When the mode is
   not in effect there is no auxiliary value to record and the slot is left empty
   (`none`) — it must NOT be synthesized from data that does not apply. -/
def chooseAux (auxActive : Bool) (auxValue : Rat) : Option Rat :=
  if auxActive then some auxValue else none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Record one class's results in the no-refit aggregation branch.

   The cross-validation aggregation has already produced, for this class, two
   candidate coefficient vectors (`coefByPerClass`, `coefByJoint`) and — when the
   auxiliary regularization mode applies — an averaged auxiliary mixing value
   (`auxValue`). This routine commits the two outputs the branch records:

     • the coefficient vector, chosen according to the strategy actually IN
       EFFECT for this fit (`perClassEffective`); the strategy as originally
       requested (`perClassRequested`) does not determine the layout of the
       stored coefficients and must not drive the choice;
     • the auxiliary mixing value, recorded only when the auxiliary mode is in
       effect (`auxActive`), and left empty (`none`) otherwise.

   All inputs are read-only (none `mut`): the routine reads the prepared values
   and flags and returns the pair it records, mutating nothing handed to it
   (directive 5). -/
method recordClassResult
    (perClassEffective : Bool) (perClassRequested : Bool)
    (coefByPerClass : Coef) (coefByJoint : Coef)
    (auxActive : Bool) (auxValue : Rat)
    return (out : Coef × Option Rat)
  ensures out.1 = chooseCoef perClassEffective coefByPerClass coefByJoint
  ensures out.2 = chooseAux auxActive auxValue
  do
    -- impl-start
    -- Commit the coefficient vector matching the strategy in effect, and the
    -- auxiliary mixing value only when the auxiliary mode applies.
    let coef : Coef := if perClassEffective then coefByPerClass else coefByJoint
    let aux : Option Rat := if auxActive then some auxValue else none
    return (coef, aux)
    -- impl-end

prove_correct recordClassResult by
  loom_solve <;> simp only [chooseCoef, chooseAux]
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The spec pins BOTH outputs as exact TOTAL functions of the inputs (ensures out.1 = chooseCoef perClassEffective coefByPerClass coefByJoint; ensures out.2 = chooseAux auxActive auxValue; both frozen in the pure region). Therefore any TERMINATING verifying impl is behaviorally identical to the gold patch on all inputs, and its faithful patch resolves. MANDATORY RESOLVE RUNS: atk_7_echo -> faithful patch == gold patch -> run_resolve('scikit-learn__scikit-learn-14087', patch, timeout=1200) => resolved=True completed=True => CORRECT ECHO, not a weakness.

DIVERGENCE INVESTIGATION (documented, NOT submitted as candidates): I also built two vacuity escapes atk_10_vacuous_true (`while true ... done_with False`) and atk_11_vacuous_wrongret (`while 0=0 ... done_with False`, wrong dead return); both are same_spec=True and VERIFY (exit=0) vacuously under partial correctness. I materialized atk_10's faithful non-terminating patch (`while True: _i+=1` inserted at the decision point in logistic.py, syntactically valid) and RAN it: run_resolve(..., timeout=180) => resolved=False, completed=False, note='no report ... harness error or timeout'. Per the gate derivation (construct/build_one.py:306) BROKEN requires (r.completed and not r.resolved); a non-terminating patch NEVER completes, so it is classified inconclusive, NOT BROKEN.

This divergence escape is a UNIVERSAL Velvet partial-correctness artifact (present for every partial-correctness method regardless of spec quality) and is outside the enumerated attack categories; it does NOT exhibit verify=/=>correct for this spec and is therefore not submitted (submitting it would only force a spurious INCONCLUSIVE on a spec I have shown to be sound). REFINEMENT.MD / MAPPING.MD A-LEG AUDIT: Solution.lean's axioms region is a prose comment ONLY -- no `axiom`/`opaque`/`deep_model` declarations; the claim of NO kind-A / NO deep-model references is HONEST.

Every refinement.md leg is R (Bool / List Rat / Rat / Option Rat type refinements) or I (the two if/else transliterations of chooseCoef/chooseAux); NO kind-3 (inexpressible-changed-op) legs -- the two changed ops are modeled DIRECTLY, not hidden behind an axiom. Correspondence spot-checked against the real repo at base_commit (logistic.py): pre-fix `self.multi_class == 'ovr'` at :2173 confirmed; `l1_ratios_ = [None]` non-elasticnet default at :1978 confirmed; the two gold hunks (behavior-1 selection @2173-2178, behavior-2 guard @2183-2188) match rows A1..A7. CONCLUSION: no verifying wrong impl has a faithful patch that COMPLETES and does NOT resolve; verify=/=>correct is not exhibited; the A-legs (none) and R/I correspondence hold. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_2_prepatch2.lean`, `atk_3_ignore_flag.lean`, `atk_4_swap_coef.lean`, `atk_5_swap_aux.lean`, `atk_6_and_flags.lean`, `atk_9_value_guard.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7_echo.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_prepatch2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_ignore_flag.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_swap_coef.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_swap_aux.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_and_flags.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_9_value_guard.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_7_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two decisions modeled here are pure control-flow
--  choices over values that have ALREADY been produced by surrounding routines:
--  the two candidate coefficient vectors (one per coefficient-array layout), the
--  averaged auxiliary mixing value, and the two strategy/mode flags are all
--  taken as FREE INPUTS. The routine itself calls no further repo function whose
--  contract must be assumed, so there is no unchanged callee to axiomatize and
--  nothing for G-AX to falsify. See mapping.md §3 and refinement.md, all rows
--  R or I.)
-- axioms-end

-- pure-start
/- A fitted coefficient vector, identified abstractly. Only WHICH candidate
   vector is selected is observed here, never the concrete numbers it contains,
   so an exact-rational list is a faithful, decidable carrier (DECISIONS float
   note: model order-only or selection-only quantities with `Rat`, not
   `Float`). -/
abbrev Coef := List Rat

/- The selected coefficient vector for one class, given the effective strategy.
   The surrounding routine has prepared two candidates from the stored
   cross-validation coefficients — one read out under the per-class layout
   (`coefByPerClass`) and one under the joint layout (`coefByJoint`). The vector
   that is meaningful is the one matching the strategy actually in effect: the
   per-class candidate when the effective strategy is the per-class one, the
   joint candidate otherwise. The decision MUST consult the effective strategy,
   not whatever was originally requested (`perClassEffective`, not
   `perClassRequested`) — the two can disagree, and only the effective one names
   the layout the stored coefficients actually have. -/
def chooseCoef (perClassEffective : Bool) (coefByPerClass coefByJoint : Coef) : Coef :=
  if perClassEffective then coefByPerClass else coefByJoint

/- The recorded auxiliary mixing value for one class. An auxiliary mixing value
   exists only when the auxiliary regularization mode is in effect; in that mode
   the surrounding routine has already averaged it (`auxValue`). When the mode is
   not in effect there is no auxiliary value to record and the slot is left empty
   (`none`) — it must NOT be synthesized from data that does not apply. -/
def chooseAux (auxActive : Bool) (auxValue : Rat) : Option Rat :=
  if auxActive then some auxValue else none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Record one class's results in the no-refit aggregation branch.

   The cross-validation aggregation has already produced, for this class, two
   candidate coefficient vectors (`coefByPerClass`, `coefByJoint`) and — when the
   auxiliary regularization mode applies — an averaged auxiliary mixing value
   (`auxValue`). This routine commits the two outputs the branch records:

     • the coefficient vector, chosen according to the strategy actually IN
       EFFECT for this fit (`perClassEffective`); the strategy as originally
       requested (`perClassRequested`) does not determine the layout of the
       stored coefficients and must not drive the choice;
     • the auxiliary mixing value, recorded only when the auxiliary mode is in
       effect (`auxActive`), and left empty (`none`) otherwise.

   All inputs are read-only (none `mut`): the routine reads the prepared values
   and flags and returns the pair it records, mutating nothing handed to it
   (directive 5). -/
method recordClassResult
    (perClassEffective : Bool) (perClassRequested : Bool)
    (coefByPerClass : Coef) (coefByJoint : Coef)
    (auxActive : Bool) (auxValue : Rat)
    return (out : Coef × Option Rat)
  ensures out.1 = chooseCoef perClassEffective coefByPerClass coefByJoint
  ensures out.2 = chooseAux auxActive auxValue
  do
    -- impl-start
    -- Commit the coefficient vector matching the strategy in effect, and the
    -- auxiliary mixing value only when the auxiliary mode applies.
    let coef : Coef := if perClassEffective then coefByPerClass else coefByJoint
    let aux : Option Rat := if auxActive then some auxValue else none
    return (coef, aux)
    -- impl-end

prove_correct recordClassResult by
  loom_solve <;> simp only [chooseCoef, chooseAux]
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The spec pins BOTH outputs as exact TOTAL functions of the inputs (ensures out.1 = chooseCoef perClassEffective coefByPerClass coefByJoint; ensures out.2 = chooseAux auxActive auxValue; both frozen in the pure region). Therefore any TERMINATING verifying impl is behaviorally identical to the gold patch on all inputs, and its faithful patch resolves. MANDATORY RESOLVE RUNS: atk_7_echo -> faithful patch == gold patch -> run_resolve('scikit-learn__scikit-learn-14087', patch, timeout=1200) => resolved=True completed=True => CORRECT ECHO, not a weakness.

DIVERGENCE INVESTIGATION (documented, NOT submitted as candidates): I also built two vacuity escapes atk_10_vacuous_true (`while true ... done_with False`) and atk_11_vacuous_wrongret (`while 0=0 ... done_with False`, wrong dead return); both are same_spec=True and VERIFY (exit=0) vacuously under partial correctness. I materialized atk_10's faithful non-terminating patch (`while True: _i+=1` inserted at the decision point in logistic.py, syntactically valid) and RAN it: run_resolve(..., timeout=180) => resolved=False, completed=False, note='no report ... harness error or timeout'. Per the gate derivation (construct/build_one.py:306) BROKEN requires (r.completed and not r.resolved); a non-terminating patch NEVER completes, so it is classified inconclusive, NOT BROKEN.

This divergence escape is a UNIVERSAL Velvet partial-correctness artifact (present for every partial-correctness method regardless of spec quality) and is outside the enumerated attack categories; it does NOT exhibit verify=/=>correct for this spec and is therefore not submitted (submitting it would only force a spurious INCONCLUSIVE on a spec I have shown to be sound). REFINEMENT.MD / MAPPING.MD A-LEG AUDIT: Solution.lean's axioms region is a prose comment ONLY -- no `axiom`/`opaque`/`deep_model` declarations; the claim of NO kind-A / NO deep-model references is HONEST.

Every refinement.md leg is R (Bool / List Rat / Rat / Option Rat type refinements) or I (the two if/else transliterations of chooseCoef/chooseAux); NO kind-3 (inexpressible-changed-op) legs -- the two changed ops are modeled DIRECTLY, not hidden behind an axiom. Correspondence spot-checked against the real repo at base_commit (logistic.py): pre-fix `self.multi_class == 'ovr'` at :2173 confirmed; `l1_ratios_ = [None]` non-elasticnet default at :1978 confirmed; the two gold hunks (behavior-1 selection @2173-2178, behavior-2 guard @2183-2188) match rows A1..A7. CONCLUSION: no verifying wrong impl has a faithful patch that COMPLETES and does NOT resolve; verify=/=>correct is not exhibited; the A-legs (none) and R/I correspondence hold. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-repo drift) audit for velvet bundle scikit-learn__scikit-learn-14087.

### Setup checks
- Spec region byte-identical/frozen: swebench_unified.markers.same_spec(Solution, Solution_prepatch)=True and same_spec(Solution, Solution_prepatch_2)=True. Consumer spec view stable.
- Solution.lean verifies (lean_verify.sh exit 0).
- patch.diff modeling checked against the ACTUAL gold patch from the dataset (base_commit a5743ed3...).

### MODELED FUNCTIONS vs REAL POST-FIX REPO (sklearn/linear_model/logistic.py, no-refit branch of LogisticRegressionCV.fit):
1. chooseCoef perClassEffective coefByPerClass coefByJoint := if perClassEffective then coefByPerClass else coefByJoint.
   Real post-fix: `if multi_class == 'ovr': w = <per-class read-out> else: w = <joint read-out>` (gold hunk 1 changes `self.multi_class` -> resolved local `multi_class`). Binding perClassEffective <-> (multi_class == 'ovr') is an exact 2-way transliteration. The distractor perClassRequested (raw self.multi_class) is deliberately EXCLUDED from the ensures, matching the fix that stops consulting the raw attribute.
2. chooseAux auxActive auxValue := if auxActive then some auxValue else none.
   Real post-fix: `if self.penalty == 'elasticnet': append(np.mean(...)) else: append(None)` (gold hunk 2). Binding auxActive <-> (penalty=='elasticnet'), some/none <-> append(value)/append(None). Exact transliteration.

NO DIVERGENCE: both decisions are pure boolean-driven 2-way selections; for every (perClassEffective, auxActive) assignment the Lean function returns exactly the branch the patched Python takes. The List Rat / Rat carriers are selection-only (only WHICH candidate/whether-recorded is observed, never the numeric contents), which is faithful because the gold code merely selects between two already-prepared, unchanged read-outs — no arithmetic is modeled, so no float/rat drift is possible on the modeled surface.

CORROBORATION: G-CONF ran the transliterated shadow vs the patched decision logic over 100040 checks (exhaustive cube + fuzz, seed=14087), 0 disagreements; the patched estimator runs the issue reproducer without IndexError and yields contracted no-refit shapes. G-AX exercises the UNCHANGED real _check_multi_class resolver, confirming the perClassEffective(resolved) vs perClassRequested(raw) bijection incl. the binary-'auto' disagreement the issue triggers. Both prepatch bug-injections fail G-DIFF on the correct discriminating ensures clause.

The spec is neither too strong nor drifting: it pins exactly the two outputs the gold branch commits, no more, no less. No input makes the modeled function disagree with the real (gold-patched) callee. Verdict: FAITHFUL. (Note, not a faithfulness defect: verdict.md D1 records a pre-existing G-LEAK mis-labeling as 'pass' rather than 'relaxed' — a compliance-record accuracy issue, orthogonal to spec-vs-repo faithfulness.)

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker 3 (leakage / gold-reconstruction). Judged against the consumer spec view produced directly by swebench_unified.markers.spec_view(VelvetBackend) on Solution.lean, and the public problem_statement only (hints excluded).

Gold edit (patch.diff), two independent behaviors in LogisticRegressionCV.fit no-refit branch: (1) `if self.multi_class == 'ovr':` -> `if multi_class == 'ovr':` — select the coefficient vector by the RESOLVED local strategy, not the raw attribute; this fixes the reported IndexError. (2) guard the l1_ratio_ append with `if self.penalty == 'elasticnet': ... else: self.l1_ratio_.append(None)`. The public problem_statement contains only the IndexError symptom, a traceback pinned at the `coefs_paths[:, i, best_indices[i], :]` line, and version info. It does NOT identify the fix as the resolved-vs-raw multi_class distinction and says NOTHING about behavior 2.

Mechanical G-LEAK screen (leakage.screen): PASS, 0 hard failures; _patch_changed_symbols == [] (patch touches no distinctive def/class name); no diff markers; no patched file path/module; no narration terms.

Manual repo-magic-string sweep of the spec view: absent — multi_class, self.multi_class, ovr, multinomial, elasticnet, penalty, l1_ratio_, coefs_paths, np.mean, best_indices, _check_multi_class, logistic.py, line numbers, diff hunks. The only public-repo token present is 'refit', which is already public via the problem_statement ('refit=False'), so not a leak.

The spec view contains only abstract Velvet symbols (perClassEffective, perClassRequested, coefByPerClass, coefByJoint, auxActive, auxValue, chooseCoef, chooseAux) plus two ensures contracts; impl and prove_correct bodies are elided placeholders. It states the required behavior abstractly (select by effective vs requested strategy; record aux only when active) — the legitimate, unavoidable role of any spec — but a solver cannot map these abstractions back to multi_class(local) vs self.multi_class or to penalty=='elasticnet' from the spec view alone. Behavior 2, though absent from the problem statement, appears only as the opaque chooseAux contract, not as a reconstructable repo edit. All concrete repo binding (symbol names, :2173/:2183 lines, literal hunks, the 'two bugs' narrative) lives only in mapping.md/refinement.md, which are G-EQ audit artifacts, NOT the consumer projection (mapping.md §2.1 is explicitly labeled 'not in the consumer spec view').

spec region byte-identical (markers.same_spec = True) between Solution.lean and both Solution_prepatch*.lean variants — the frozen spec is legitimately shared; prepatch differs only in impl (G-DIFF). No relaxed_leakage flag set; this is a strict judgment.

Conclusion: the spec view is a faithful, repo-abstracted behavioral contract that does not leak the concrete gold edit beyond the public problem_statement in a reconstructable way. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.