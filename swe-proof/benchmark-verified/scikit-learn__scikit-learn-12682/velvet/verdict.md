# P2 adversarial audit — scikit-learn__scikit-learn-12682

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. All 10 same-spec wrong implementations FAIL Velvet verification (lean_verify.sh exit 1). No verifying-but-wrong impl exists, so there is no faithful refined patch to materialize/run through run_resolve (protocol step 2's resolve obligation triggers only for a wrong impl that verifies; zero qualify here). verify does NOT admit an incorrect impl => spec is not broken.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,8 +48,8 @@
   ensures cfg.iterationBudget = userBudget
   do
     -- impl-start
-    -- Store the user-requested iteration budget on the configuration verbatim.
-    let cfg : CodingConfig := { iterationBudget := userBudget }
+    -- PREPATCH BUG: drops the user budget, stores the fixed default 1000.
+    let cfg : CodingConfig := { iterationBudget := 1000 }
     return cfg
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,8 +48,8 @@
   ensures cfg.iterationBudget = userBudget
   do
     -- impl-start
-    -- Store the user-requested iteration budget on the configuration verbatim.
-    let cfg : CodingConfig := { iterationBudget := userBudget }
+    -- WRONG: off-by-one, stores userBudget+1.
+    let cfg : CodingConfig := { iterationBudget := userBudget + 1 }
     return cfg
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,8 +48,8 @@
   ensures cfg.iterationBudget = userBudget
   do
     -- impl-start
-    -- Store the user-requested iteration budget on the configuration verbatim.
-    let cfg : CodingConfig := { iterationBudget := userBudget }
+    -- WRONG: stores constant 0.
+    let cfg : CodingConfig := { iterationBudget := 0 }
     return cfg
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,7 +72,8 @@
     -- Read the configured iteration budget and forward it to the solver as its
     -- iteration limit (the downstream encode entry-point already hands its
     -- budget argument straight to the solver unchanged).
-    let solverBudget := cfg.iterationBudget
+    -- WRONG: ignores cfg, forwards fixed default 1000.
+    let solverBudget := (1000 : Nat)
     return solverBudget
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,7 +72,8 @@
     -- Read the configured iteration budget and forward it to the solver as its
     -- iteration limit (the downstream encode entry-point already hands its
     -- budget argument straight to the solver unchanged).
-    let solverBudget := cfg.iterationBudget
+    -- WRONG: doubles the budget.
+    let solverBudget := cfg.iterationBudget * 2
     return solverBudget
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,9 +90,9 @@
   ensures solverBudget = userBudget
   do
     -- impl-start
-    let cfg ← recordIterationBudget userBudget
-    let solverBudget ← encodeWithConfig cfg
-    return solverBudget
+    -- WRONG: ignores threading, returns fixed default 1000.
+    let _cfg ← recordIterationBudget userBudget
+    return (1000 : Nat)
     -- impl-end
 
 prove_correct configuredBudgetReachesSolver by
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,8 +90,9 @@
   ensures solverBudget = userBudget
   do
     -- impl-start
-    let cfg ← recordIterationBudget userBudget
-    let solverBudget ← encodeWithConfig cfg
+    -- WRONG: discards recorded budget, encodes a fresh default cfg.
+    let _cfg ← recordIterationBudget userBudget
+    let solverBudget ← encodeWithConfig { iterationBudget := 1000 }
     return solverBudget
     -- impl-end
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,8 +48,9 @@
   ensures cfg.iterationBudget = userBudget
   do
     -- impl-start
-    -- Store the user-requested iteration budget on the configuration verbatim.
-    let cfg : CodingConfig := { iterationBudget := userBudget }
+    -- WRONG (partial-domain): correct everywhere except userBudget = 5.
+    let stored := if userBudget = 5 then 0 else userBudget
+    let cfg : CodingConfig := { iterationBudget := stored }
     return cfg
     -- impl-end
 
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,7 +72,18 @@
     -- Read the configured iteration budget and forward it to the solver as its
     -- iteration limit (the downstream encode entry-point already hands its
     -- budget argument straight to the solver unchanged).
-    let solverBudget := cfg.iterationBudget
+    -- WRONG (control-flow / divergence channel): a non-terminating loop guards
+    -- a WRONG returned value (1000). Under PARTIAL semantics the postcondition
+    -- would hold vacuously (method never returns); under TOTAL it must fail the
+    -- termination obligation (`decreasing i` unprovable when i increases).
+    let mut i : Nat := 1
+    while i > 0
+      invariant True
+      done_with i = 0
+      decreasing i
+    do
+      i := i + 1
+    let solverBudget : Nat := 1000
     return solverBudget
     -- impl-end
 
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,7 +72,8 @@
     -- Read the configured iteration budget and forward it to the solver as its
     -- iteration limit (the downstream encode entry-point already hands its
     -- budget argument straight to the solver unchanged).
-    let solverBudget := cfg.iterationBudget
+    -- WRONG (boundary): (n-1)+1 = n only for n>0; at n=0 yields 1 (Nat trunc).
+    let solverBudget := (cfg.iterationBudget - 1) + 1
     return solverBudget
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behavior under spec is a pure DATA-FLOW property:
--  a user-configured iteration budget is recorded on the estimator's
--  configuration and then handed, unchanged, to the underlying iterative solver
--  as its iteration limit. Nothing is claimed about the solver's numerical
--  output — only about WHICH budget value reaches it — so there is no callee
--  property to consume and nothing for G-AX to check. The budget is modeled as a
--  free natural number (an exact, order-faithful carrier for an iteration count);
--  the spec holds for EVERY budget the user may configure.)
-- axioms-end

-- pure-start
/- The observable configuration the desired behavior constrains: the maximum
   number of solver iterations the estimator is configured to allow. Every other
   configuration field is orthogonal to this behavior and omitted (mapping.md §2).
   `iterationBudget` is an exact `Nat`: an iteration count is a non-negative whole
   number, and the only thing pinned is the precise value carried through, an
   exact-value fact, so an exact carrier is faithful. -/
structure CodingConfig where
  iterationBudget : Nat
  deriving DecidableEq, Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the estimator's coding configuration from the budget the user supplies
   at construction time. Desired behavior: the configured iteration budget must
   be the value the user actually requested — it is recorded faithfully, so a
   later encoding step can hand exactly that budget to the solver. (A budget the
   configuration silently replaced with a constant default could not control the
   solver, which is the whole point of letting the user configure it.)

   `userBudget` is the read-only requested budget (not `mut`): the routine records
   it and never alters it (directive 5). -/
method recordIterationBudget (userBudget : Nat) return (cfg : CodingConfig)
  ensures cfg.iterationBudget = userBudget
  do
    -- impl-start
    -- Store the user-requested iteration budget on the configuration verbatim.
    let cfg : CodingConfig := { iterationBudget := userBudget }
    return cfg
    -- impl-end

prove_correct recordIterationBudget by
  loom_solve

/- Encode under a given configuration: determine the iteration budget that the
   underlying iterative solver is run with. Desired behavior: the solver's
   iteration limit is the budget recorded on the configuration — the configured
   value is read and forwarded to the solver as-is, rather than the solver being
   left to fall back on a constant built-in default. The returned value is precisely
   the iteration limit handed to the solver.

   `cfg` is the read-only configuration (not `mut`): encoding consults it and
   never mutates it (directive 5). -/
method encodeWithConfig (cfg : CodingConfig) return (solverBudget : Nat)
  ensures solverBudget = cfg.iterationBudget
  do
    -- impl-start
    -- Read the configured iteration budget and forward it to the solver as its
    -- iteration limit (the downstream encode entry-point already hands its
    -- budget argument straight to the solver unchanged).
    -- CORRECT but structurally different: (n+0) via explicit binding.
    let n := cfg.iterationBudget
    let solverBudget := n + 0
    return solverBudget
    -- impl-end

prove_correct encodeWithConfig by
  loom_solve

/- End-to-end: the budget the user configures at construction reaches the solver.
   Desired behavior: the iteration limit the solver is ultimately run with equals
   the budget the user requested — configuring the budget actually governs the
   solver. This is the composition of recording the budget on the configuration
   and then encoding under that configuration.

   `userBudget` is the read-only requested budget (not `mut`, directive 5). -/
method configuredBudgetReachesSolver (userBudget : Nat) return (solverBudget : Nat)
  ensures solverBudget = userBudget
  do
    -- impl-start
    let cfg ← recordIterationBudget userBudget
    let solverBudget ← encodeWithConfig cfg
    return solverBudget
    -- impl-end

prove_correct configuredBudgetReachesSolver by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: three identity-threading methods with tight postconditions — recordIterationBudget(b): ensures cfg.iterationBudget=b; encodeWithConfig(cfg): ensures solverBudget=cfg.iterationBudget; configuredBudgetReachesSolver(b): ensures solverBudget=b. Pure data-flow (budget threading), NO axioms, NO deep-model references (meta.axioms=[], deep_model_references=[], conf_skip=False). loom.semantics.termination="total".

EXACT COMMANDS: same_spec via `python -c "from swebench_unified.markers import same_spec; ..."` (all True); verify via `bash scripts/lean_verify.sh <path>` run concurrently in batches of <=4.

### ATTACK RESULTS (all same_spec=True; all exit 1 = fail; each fails at the correct discriminating clause):
- atk_1 prepatch bug (record const 1000): exit 1, goal `1000 = userBudget` unsolved. Reproduces prepatch (prepatch_reproduced=true).
- atk_2 record userBudget+1: exit 1, `userBudget+1=userBudget`.
- atk_3 record const 0: exit 1.
- atk_4 encode const 1000: exit 1 (ungrounded-constant echo).
- atk_5 encode cfg.iterationBudget*2: exit 1.
- atk_6 composition returns const 1000: exit 1, `1000=userBudget`.
- atk_7 composition encodes fresh {iterationBudget:=1000} cfg: exit 1.
- atk_8 PARTIAL-DOMAIN (correct except userBudget=5 -> 0): exit 1, goal `(if userBudget=5 then 0 else userBudget)=userBudget` unsolved. Confirms spec pins the WHOLE domain, not just sampled points.
- atk_9 CONTROL-FLOW / DIVERGENCE CHANNEL (non-terminating `while i>0 do i:=i+1` guarding wrong value 1000): exit 1, fails precisely at `decreasing_1: i` termination obligation. Confirms refinement.md §D2: total-correctness semantics closes the vacuous-divergence hole that broke the earlier partial-semantics version — a diverging impl can NO LONGER satisfy ensures vacuously.
- atk_10 BOUNDARY ((n-1)+1, Nat truncation at n=0): exit 1, goal `cfg.iterationBudget-1+1=cfg.iterationBudget` unsolved (fails at n=0). Confirms Nat boundary is pinned.
- pos_control (structurally different correct: `let n:=cfg.iterationBudget; n+0`): exit 0 (VERIFIES) => spec is non-vacuous.

REFINEMENT AUDIT (A-leg / correspondence mandate): refinement.md legs are all tagged R or I, no A-consumed/A-reference, no kind-3. Verified: no `axiom`/`admit`/`sorry` in Solution.lean; meta.axioms=[] and deep_model_references=[]; so G-AX correctly SKIPS and the A-leg correspondence obligation is vacuously satisfied. The R/I legs (int<->Nat bijection, self.transform_max_iter<->cfg.iterationBudget, verbatim sparse_encode->_sparse_encode->Lasso(max_iter=...) forwarding modeled as concrete read I) are covered by G-CONF, recorded PASS (100012 budgets, 12 boundary incl. F2P 1/2000 + 100000 fuzz seed=12682, 0 disagreements). The identity model<->patch correspondence holds.

VERDICT BASIS: >=10 distinct same-spec attacks (incl. partial-domain, boundary, control-flow-divergence, ungrounded-constant echo) all FAIL to verify; positive control verifies. No verifying wrong impl => no run_resolve obligation triggered => spec is not broken (verify => correct holds within the tested attack surface). SOUND.

RESIDUAL TRUST (disclosed, not a defect): the verified theorem is an identity f(x)=x carrying no numerical/convergence content; the verify=>resolve link rests on G-CONF (abstract identity tied to the real forwarded max_iter) + G-RESOLVE (gold resolves), consistent with a pure value-threading fix. This is a spec-thinness observation within mandate, not a G-EQ break.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. All 10 same-spec wrong implementations FAIL Velvet verification (lean_verify.sh exit 1). No verifying-but-wrong impl exists, so there is no faithful refined patch to materialize/run through run_resolve (protocol step 2's resolve obligation triggers only for a wrong impl that verifies; zero qualify here). verify does NOT admit an incorrect impl => spec is not broken.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behavior under spec is a pure DATA-FLOW property:
--  a user-configured iteration budget is recorded on the estimator's
--  configuration and then handed, unchanged, to the underlying iterative solver
--  as its iteration limit. Nothing is claimed about the solver's numerical
--  output — only about WHICH budget value reaches it — so there is no callee
--  property to consume and nothing for G-AX to check. The budget is modeled as a
--  free natural number (an exact, order-faithful carrier for an iteration count);
--  the spec holds for EVERY budget the user may configure.)
-- axioms-end

-- pure-start
/- The observable configuration the desired behavior constrains: the maximum
   number of solver iterations the estimator is configured to allow. Every other
   configuration field is orthogonal to this behavior and omitted (mapping.md §2).
   `iterationBudget` is an exact `Nat`: an iteration count is a non-negative whole
   number, and the only thing pinned is the precise value carried through, an
   exact-value fact, so an exact carrier is faithful. -/
structure CodingConfig where
  iterationBudget : Nat
  deriving DecidableEq, Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the estimator's coding configuration from the budget the user supplies
   at construction time. Desired behavior: the configured iteration budget must
   be the value the user actually requested — it is recorded faithfully, so a
   later encoding step can hand exactly that budget to the solver. (A budget the
   configuration silently replaced with a constant default could not control the
   solver, which is the whole point of letting the user configure it.)

   `userBudget` is the read-only requested budget (not `mut`): the routine records
   it and never alters it (directive 5). -/
method recordIterationBudget (userBudget : Nat) return (cfg : CodingConfig)
  ensures cfg.iterationBudget = userBudget
  do
    -- impl-start
    -- Store the user-requested iteration budget on the configuration verbatim.
    let cfg : CodingConfig := { iterationBudget := userBudget }
    return cfg
    -- impl-end

prove_correct recordIterationBudget by
  loom_solve

/- Encode under a given configuration: determine the iteration budget that the
   underlying iterative solver is run with. Desired behavior: the solver's
   iteration limit is the budget recorded on the configuration — the configured
   value is read and forwarded to the solver as-is, rather than the solver being
   left to fall back on a constant built-in default. The returned value is precisely
   the iteration limit handed to the solver.

   `cfg` is the read-only configuration (not `mut`): encoding consults it and
   never mutates it (directive 5). -/
method encodeWithConfig (cfg : CodingConfig) return (solverBudget : Nat)
  ensures solverBudget = cfg.iterationBudget
  do
    -- impl-start
    -- Read the configured iteration budget and forward it to the solver as its
    -- iteration limit (the downstream encode entry-point already hands its
    -- budget argument straight to the solver unchanged).
    -- CORRECT but structurally different: (n+0) via explicit binding.
    let n := cfg.iterationBudget
    let solverBudget := n + 0
    return solverBudget
    -- impl-end

prove_correct encodeWithConfig by
  loom_solve

/- End-to-end: the budget the user configures at construction reaches the solver.
   Desired behavior: the iteration limit the solver is ultimately run with equals
   the budget the user requested — configuring the budget actually governs the
   solver. This is the composition of recording the budget on the configuration
   and then encoding under that configuration.

   `userBudget` is the read-only requested budget (not `mut`, directive 5). -/
method configuredBudgetReachesSolver (userBudget : Nat) return (solverBudget : Nat)
  ensures solverBudget = userBudget
  do
    -- impl-start
    let cfg ← recordIterationBudget userBudget
    let solverBudget ← encodeWithConfig cfg
    return solverBudget
    -- impl-end

prove_correct configuredBudgetReachesSolver by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: three identity-threading methods with tight postconditions — recordIterationBudget(b): ensures cfg.iterationBudget=b; encodeWithConfig(cfg): ensures solverBudget=cfg.iterationBudget; configuredBudgetReachesSolver(b): ensures solverBudget=b. Pure data-flow (budget threading), NO axioms, NO deep-model references (meta.axioms=[], deep_model_references=[], conf_skip=False). loom.semantics.termination="total".

EXACT COMMANDS: same_spec via `python -c "from swebench_unified.markers import same_spec; ..."` (all True); verify via `bash scripts/lean_verify.sh <path>` run concurrently in batches of <=4.

### ATTACK RESULTS (all same_spec=True; all exit 1 = fail; each fails at the correct discriminating clause):
- atk_1 prepatch bug (record const 1000): exit 1, goal `1000 = userBudget` unsolved. Reproduces prepatch (prepatch_reproduced=true).
- atk_2 record userBudget+1: exit 1, `userBudget+1=userBudget`.
- atk_3 record const 0: exit 1.
- atk_4 encode const 1000: exit 1 (ungrounded-constant echo).
- atk_5 encode cfg.iterationBudget*2: exit 1.
- atk_6 composition returns const 1000: exit 1, `1000=userBudget`.
- atk_7 composition encodes fresh {iterationBudget:=1000} cfg: exit 1.
- atk_8 PARTIAL-DOMAIN (correct except userBudget=5 -> 0): exit 1, goal `(if userBudget=5 then 0 else userBudget)=userBudget` unsolved. Confirms spec pins the WHOLE domain, not just sampled points.
- atk_9 CONTROL-FLOW / DIVERGENCE CHANNEL (non-terminating `while i>0 do i:=i+1` guarding wrong value 1000): exit 1, fails precisely at `decreasing_1: i` termination obligation. Confirms refinement.md §D2: total-correctness semantics closes the vacuous-divergence hole that broke the earlier partial-semantics version — a diverging impl can NO LONGER satisfy ensures vacuously.
- atk_10 BOUNDARY ((n-1)+1, Nat truncation at n=0): exit 1, goal `cfg.iterationBudget-1+1=cfg.iterationBudget` unsolved (fails at n=0). Confirms Nat boundary is pinned.
- pos_control (structurally different correct: `let n:=cfg.iterationBudget; n+0`): exit 0 (VERIFIES) => spec is non-vacuous.

REFINEMENT AUDIT (A-leg / correspondence mandate): refinement.md legs are all tagged R or I, no A-consumed/A-reference, no kind-3. Verified: no `axiom`/`admit`/`sorry` in Solution.lean; meta.axioms=[] and deep_model_references=[]; so G-AX correctly SKIPS and the A-leg correspondence obligation is vacuously satisfied. The R/I legs (int<->Nat bijection, self.transform_max_iter<->cfg.iterationBudget, verbatim sparse_encode->_sparse_encode->Lasso(max_iter=...) forwarding modeled as concrete read I) are covered by G-CONF, recorded PASS (100012 budgets, 12 boundary incl. F2P 1/2000 + 100000 fuzz seed=12682, 0 disagreements). The identity model<->patch correspondence holds.

VERDICT BASIS: >=10 distinct same-spec attacks (incl. partial-domain, boundary, control-flow-divergence, ungrounded-constant echo) all FAIL to verify; positive control verifies. No verifying wrong impl => no run_resolve obligation triggered => spec is not broken (verify => correct holds within the tested attack surface). SOUND.

RESIDUAL TRUST (disclosed, not a defect): the verified theorem is an identity f(x)=x carrying no numerical/convergence content; the verify=>resolve link rests on G-CONF (abstract identity tied to the real forwarded max_iter) + G-RESOLVE (gold resolves), consistent with a pure value-threading fix. This is a spec-thinness observation within mandate, not a G-EQ break.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True, velvet backend). Solution.lean verifies clean (lean_verify.sh exit 0). The modeled property is the pure data-flow identity configuredBudgetReachesSolver(b) = b: the user-configured transform_max_iter is recorded on the estimator and forwarded unchanged to the solver's max_iter. Traced the real patched repo at base_commit d360ffa7c5 hop-by-hop: __init__/_set_sparse_coding_params store self.transform_max_iter=b verbatim (dict_learning.py:891); transform reads it into sparse_encode(max_iter=...) (:921); sparse_encode -> _sparse_encode(max_iter=max_iter) (:332); _sparse_encode -> Lasso(max_iter=max_iter)/LassoLars(max_iter=max_iter). No hop transforms/clamps/defaults the value — a straight-line assignment chain, so the identity holds for EVERY Nat budget; no diverging input could be constructed. Nat<->int bijection is exact (iteration count, exact-value fact, no rounding). Spec is NOT too strong: ensures clauses pin only the exact-value forwarding (no claim about solver numerics); total-correctness semantics only obliges termination, which the straight-line store/read/forward ops always satisfy, and does not strengthen the value claim beyond repo behavior. Prepatch model (iterationBudget:=1000) faithfully mirrors real prepatch (sparse_encode called without max_iter -> default 1000) and correctly fails the free-userBudget obligation. Conformance oracle corroborates over 12 boundary + 100000 fuzz budgets (seed 12682). No axioms / deep-model references (G-AX skips).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical (swebench_unified.markers.same_spec(Solution, Solution_prepatch)=True). Mechanical G-LEAK screen (leakage.screen over spec_view, velvet/lean flavor) PASSES with zero hard failures. Manual/semantic audit of the projected consumer spec view confirms clean:

- No diff markers, no reproduced gold-patch lines, no patched file/module paths (sklearn.decomposition.dict_learning / examples/... absent), no bug/fix narration.
- Spec-view identifiers (CodingConfig, iterationBudget, recordIterationBudget, encodeWithConfig, configuredBudgetReachesSolver, userBudget, solverBudget) are fully abstract; none embed any patched repo symbol (SparseCoder, sparse_encode, transform_max_iter, _set_sparse_coding_params, dict_learning, Lasso, LassoLars, transform).
- Gold-specific constant 1000 does NOT appear; the strings max_iter / transform_max_iter / sparse_encode / Lasso / .py all absent from the spec view.

Semantic content check vs. public problem_statement: the problem_statement itself already discloses the full nature of the change — SparseCoder does not set Lasso's max_iter, default is 1000, and 'there should be a way for the user to specify' the parameter. The spec view models exactly that publicly-stated data-flow behavior (a user-configured iteration budget is recorded on the estimator's configuration and forwarded unchanged to the solver as its iteration limit). This is derivable from problem_statement alone and reveals no gold-edit specifics (concrete attribute name, call site, or default value) beyond it. Nothing in the spec view narrows the search to the gold edit more than the public task already does.

Note: refinement.md and mapping.md DO name transform_max_iter, sparse_encode, and line numbers, but those are audit/derivation documents, not part of the consumer spec view (spec_view projection), so they are out of scope for G-PANEL-3 leakage. No leakage in the spec view.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
