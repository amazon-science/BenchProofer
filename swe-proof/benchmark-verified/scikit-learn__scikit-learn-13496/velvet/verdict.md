# P2 adversarial audit — scikit-learn__scikit-learn-13496

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,11 +88,9 @@
   ensures cfg.warmStart = warmStart
   do
     -- impl-start
-    -- Forward every carried entry verbatim, INCLUDING the incremental-fit reuse
-    -- flag taken from the caller's argument.
     return { nEstimators := nEstimators, maxSamples := maxSamples,
              maxFeatures := maxFeatures, bootstrap := bootstrap,
-             warmStart := warmStart, nJobs := nJobs,
+             warmStart := false, nJobs := nJobs,
              randomState := randomState, verbose := verbose }
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,11 +88,9 @@
   ensures cfg.warmStart = warmStart
   do
     -- impl-start
-    -- Forward every carried entry verbatim, INCLUDING the incremental-fit reuse
-    -- flag taken from the caller's argument.
     return { nEstimators := nEstimators, maxSamples := maxSamples,
              maxFeatures := maxFeatures, bootstrap := bootstrap,
-             warmStart := warmStart, nJobs := nJobs,
+             warmStart := true, nJobs := nJobs,
              randomState := randomState, verbose := verbose }
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,12 +88,10 @@
   ensures cfg.warmStart = warmStart
   do
     -- impl-start
-    -- Forward every carried entry verbatim, INCLUDING the incremental-fit reuse
-    -- flag taken from the caller's argument.
     return { nEstimators := nEstimators, maxSamples := maxSamples,
              maxFeatures := maxFeatures, bootstrap := bootstrap,
-             warmStart := warmStart, nJobs := nJobs,
-             randomState := randomState, verbose := verbose }
+             warmStart := warmStart, nJobs := verbose,
+             randomState := randomState, verbose := nJobs }
     -- impl-end
 
 prove_correct configureEnsemble by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,11 +88,9 @@
   ensures cfg.warmStart = warmStart
   do
     -- impl-start
-    -- Forward every carried entry verbatim, INCLUDING the incremental-fit reuse
-    -- flag taken from the caller's argument.
     return { nEstimators := nEstimators, maxSamples := maxSamples,
              maxFeatures := maxFeatures, bootstrap := bootstrap,
-             warmStart := warmStart, nJobs := nJobs,
+             warmStart := bootstrap, nJobs := nJobs,
              randomState := randomState, verbose := verbose }
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,11 +88,10 @@
   ensures cfg.warmStart = warmStart
   do
     -- impl-start
-    -- Forward every carried entry verbatim, INCLUDING the incremental-fit reuse
-    -- flag taken from the caller's argument.
+    let ws := warmStart && false
     return { nEstimators := nEstimators, maxSamples := maxSamples,
              maxFeatures := maxFeatures, bootstrap := bootstrap,
-             warmStart := warmStart, nJobs := nJobs,
+             warmStart := ws, nJobs := nJobs,
              randomState := randomState, verbose := verbose }
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,9 +88,7 @@
   ensures cfg.warmStart = warmStart
   do
     -- impl-start
-    -- Forward every carried entry verbatim, INCLUDING the incremental-fit reuse
-    -- flag taken from the caller's argument.
-    return { nEstimators := nEstimators, maxSamples := maxSamples,
+    return { nEstimators := nEstimators + 1, maxSamples := maxSamples,
              maxFeatures := maxFeatures, bootstrap := bootstrap,
              warmStart := warmStart, nJobs := nJobs,
              randomState := randomState, verbose := verbose }
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,12 +88,16 @@
   ensures cfg.warmStart = warmStart
   do
     -- impl-start
-    -- Forward every carried entry verbatim, INCLUDING the incremental-fit reuse
-    -- flag taken from the caller's argument.
-    return { nEstimators := nEstimators, maxSamples := maxSamples,
-             maxFeatures := maxFeatures, bootstrap := bootstrap,
-             warmStart := warmStart, nJobs := nJobs,
-             randomState := randomState, verbose := verbose }
+    if bootstrap then
+      return { nEstimators := nEstimators, maxSamples := maxSamples,
+               maxFeatures := maxFeatures, bootstrap := bootstrap,
+               warmStart := warmStart, nJobs := nJobs,
+               randomState := randomState, verbose := verbose }
+    else
+      return { nEstimators := nEstimators, maxSamples := maxSamples,
+               maxFeatures := maxFeatures, bootstrap := bootstrap,
+               warmStart := false, nJobs := nJobs,
+               randomState := randomState, verbose := verbose }
     -- impl-end
 
 prove_correct configureEnsemble by
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -88,12 +88,16 @@
   ensures cfg.warmStart = warmStart
   do
     -- impl-start
-    -- Forward every carried entry verbatim, INCLUDING the incremental-fit reuse
-    -- flag taken from the caller's argument.
-    return { nEstimators := nEstimators, maxSamples := maxSamples,
-             maxFeatures := maxFeatures, bootstrap := bootstrap,
-             warmStart := warmStart, nJobs := nJobs,
-             randomState := randomState, verbose := verbose }
+    if warmStart then
+      return { nEstimators := nEstimators, maxSamples := maxSamples,
+               maxFeatures := maxFeatures, bootstrap := bootstrap,
+               warmStart := true, nJobs := nJobs,
+               randomState := randomState, verbose := verbose }
+    else
+      return { nEstimators := nEstimators, maxSamples := maxSamples,
+               maxFeatures := maxFeatures, bootstrap := bootstrap,
+               warmStart := false, nJobs := nJobs,
+               randomState := randomState, verbose := verbose }
     -- impl-end
 
 prove_correct configureEnsemble by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The constructor under spec only assembles the
--  configuration it forwards to the base ensemble machinery out of its own
--  arguments; it consults no callee whose contract the proof depends on. The
--  downstream incremental-vs-fresh fitting that consumes this configuration is
--  unchanged library behavior and is not re-modeled here.)
-- axioms-end

-- pure-start
/- A single forwarded constructor argument, modeled as an opaque handle: the
   constructor passes it through to the base ensemble configuration verbatim, so
   the only property that matters is that its IDENTITY is preserved. The concrete
   Python value it stands for may be an int, a float, the string "auto", `None`,
   or a random-state object; the bijection (mapping.md §2) maps each such value
   to a distinct handle and forwarding to handle equality. -/
abbrev Param := Int

/- The configuration an ensemble estimator's constructor assembles and hands to
   its base ensemble machinery, abstracted to the entries the constructor
   forwards from its own arguments:

   * `nEstimators`  — how many base estimators the ensemble targets;
   * `maxSamples`   — the per-estimator sample budget;
   * `maxFeatures`  — the per-estimator feature budget;
   * `bootstrap`    — whether per-estimator subsets are drawn with replacement;
   * `warmStart`    — the incremental-fit reuse flag: when on, a subsequent fit
                      reuses the previous fit and adds more estimators rather
                      than building a fresh ensemble;
   * `nJobs`        — the parallelism handle;
   * `randomState`  — the randomness handle;
   * `verbose`      — the verbosity handle. -/
structure EnsembleConfig where
  nEstimators : Param
  maxSamples : Param
  maxFeatures : Param
  bootstrap : Bool
  warmStart : Bool
  nJobs : Param
  randomState : Param
  verbose : Param
deriving DecidableEq, Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the configuration an ensemble estimator's constructor forwards to its
   base ensemble machinery.

   Desired behavior: every entry the constructor carries is forwarded EXACTLY as
   supplied by the caller. In particular the incremental-fit reuse flag is one of
   the forwarded entries: the caller's choice of that flag (default off) is
   propagated into the configuration verbatim, so that downstream fitting reuses
   the previous fit and adds more estimators when it is on, and builds a fresh
   ensemble when it is off. Exposing this flag must NOT disturb any of the entries
   already forwarded: the targeted estimator count, the sample and feature
   budgets, the replacement flag, and the parallelism / randomness / verbosity
   handles each continue to equal the corresponding argument.

   All arguments are read-only (none is `mut`): the constructor reads each
   argument and assembles a configuration, mutating no input (directive 5). Each
   forwarded argument is modeled as an opaque handle (`Param`) whose identity the
   forwarding preserves; the two genuine booleans are carried as `Bool`
   (mapping.md §2). -/
method configureEnsemble
    (nEstimators : Param) (maxSamples : Param) (maxFeatures : Param)
    (bootstrap : Bool) (nJobs : Param) (randomState : Param) (verbose : Param)
    (warmStart : Bool)
    return (cfg : EnsembleConfig)
  ensures cfg.nEstimators = nEstimators
  ensures cfg.maxSamples = maxSamples
  ensures cfg.maxFeatures = maxFeatures
  ensures cfg.bootstrap = bootstrap
  ensures cfg.nJobs = nJobs
  ensures cfg.randomState = randomState
  ensures cfg.verbose = verbose
  ensures cfg.warmStart = warmStart
  do
    -- impl-start
    -- Forward every carried entry verbatim, INCLUDING the incremental-fit reuse
    -- flag taken from the caller's argument.
    return { nEstimators := nEstimators, maxSamples := maxSamples,
             maxFeatures := maxFeatures, bootstrap := bootstrap,
             warmStart := warmStart, nJobs := nJobs,
             randomState := randomState, verbose := verbose }
    -- impl-end

prove_correct configureEnsemble by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: velvet `configureEnsemble` models IsolationForest.__init__ forwarding its 8 args into the EnsembleConfig handed to super().__init__. The spec pins EVERY output field with a dedicated `ensures` clause (cfg.nEstimators=nEstimators, ...maxSamples, maxFeatures, bootstrap, nJobs, randomState, verbose, AND the newly-forwarded cfg.warmStart=warmStart). This FULLY DETERMINES the return value: there is zero degree of freedom for a same-spec verifying impl to deviate from the field-by-field-equal config, which is exactly the gold behavior.

PROTOCOL: work done; same_spec confirmed True for all 8 attacks (velvet backend, swebench_unified.markers.same_spec) and True for pos_control; header/axioms/pure/pre/post left byte-identical, only impl region edited. Verifier: `bash scripts/lean_verify.sh <f>` (run concurrently, <=4 at a time).

ATTACKS & RESULTS:
- atk_1 (prepatch bug: warmStart:=false, ignores caller): VERIFY exit=1. Goal `false = warmStart` unsolved. Correctly rejected. (This reproduces Solution_prepatch.lean's failure => prepatch_reproduced=true.)
- atk_2 (ungrounded/hardcode: warmStart:=true): exit=1 (goal true=warmStart).
- atk_3 (field-swap frame corruption: nJobs:=verbose, verbose:=nJobs): exit=1.
- atk_4 (ungrounded-oracle echo / wrong source: warmStart:=bootstrap): exit=1.
- atk_5 (control-flow-effect: ws:=warmStart && false then warmStart:=ws): exit=1 (false=warmStart).
- atk_6 (arithmetic on handle: nEstimators:=nEstimators+1, boundary/identity break): exit=1 (goal nEstimators+1=nEstimators).
- atk_7 (partial-domain: only forwards warmStart when bootstrap else false): exit=1.
- atk_8 (CORRECT partial-domain reformulation: case-split on warmStart, forwarding true/false respectively -> behaviorally identical to gold): VERIFY exit=0.
- pos_control (gold impl verbatim): VERIFY exit=0.

RESOLVE (mandatory for every verifying attack): atk_8 is the ONLY verifying wrong-shaped candidate and it is behaviorally identical to gold (both branches yield cfg.warmStart=warmStart and all other fields = args). Its faithful refined Python patch is the gold patch.diff (forward warm_start=warm_start in super().__init__ + signature + docstring). Ran through the OFFICIAL harness via swebench_unified.harness.run_resolve('scikit-learn__scikit-learn-13496', <gold patch>, timeout=1800) under FSx HOME + docker: COMPLETED=True, RESOLVED=True, ATTEMPTS=1, FLAKY=False, NOTE='resolved'. => the verifying candidate's materialized patch RESOLVES. No verify-but-not-resolve breaker found.

REFINEMENT AUDIT: refinement.md legs A1..A8 are all R or R+I; §B explicitly asserts no kind-3 (inexpressible-changed-op) step and there are NO A-legs (no axioms, no A-consumed, no A-reference) — confirmed by mapping.md §3 (Callee provenance: None). The genuinely-changed op (exposing/forwarding warm_start) is modeled DIRECTLY as the concrete `warmStart` field (tag R), not hidden behind an axiom. The incremental-fit ALGORITHM the flag controls lives in unchanged BaseBagging._fit and is correctly NOT re-modeled (SPEC_GUIDE faithfulness). Since there are no A-legs, there is no A-correspondence that can be broken. Total-correctness semantics (loom.semantics.termination total) rules out a divergent same-spec impl vacuously satisfying the ensures.

CONCLUSION: The spec is fully field-pinned; every distinct wrong impl (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, frame-swap, prepatch) fails verification with genuine postcondition goals, and the sole verifying variant is behaviorally correct and RESOLVES under the official harness. verify => correct holds. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The constructor under spec only assembles the
--  configuration it forwards to the base ensemble machinery out of its own
--  arguments; it consults no callee whose contract the proof depends on. The
--  downstream incremental-vs-fresh fitting that consumes this configuration is
--  unchanged library behavior and is not re-modeled here.)
-- axioms-end

-- pure-start
/- A single forwarded constructor argument, modeled as an opaque handle: the
   constructor passes it through to the base ensemble configuration verbatim, so
   the only property that matters is that its IDENTITY is preserved. The concrete
   Python value it stands for may be an int, a float, the string "auto", `None`,
   or a random-state object; the bijection (mapping.md §2) maps each such value
   to a distinct handle and forwarding to handle equality. -/
abbrev Param := Int

/- The configuration an ensemble estimator's constructor assembles and hands to
   its base ensemble machinery, abstracted to the entries the constructor
   forwards from its own arguments:

   * `nEstimators`  — how many base estimators the ensemble targets;
   * `maxSamples`   — the per-estimator sample budget;
   * `maxFeatures`  — the per-estimator feature budget;
   * `bootstrap`    — whether per-estimator subsets are drawn with replacement;
   * `warmStart`    — the incremental-fit reuse flag: when on, a subsequent fit
                      reuses the previous fit and adds more estimators rather
                      than building a fresh ensemble;
   * `nJobs`        — the parallelism handle;
   * `randomState`  — the randomness handle;
   * `verbose`      — the verbosity handle. -/
structure EnsembleConfig where
  nEstimators : Param
  maxSamples : Param
  maxFeatures : Param
  bootstrap : Bool
  warmStart : Bool
  nJobs : Param
  randomState : Param
  verbose : Param
deriving DecidableEq, Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the configuration an ensemble estimator's constructor forwards to its
   base ensemble machinery.

   Desired behavior: every entry the constructor carries is forwarded EXACTLY as
   supplied by the caller. In particular the incremental-fit reuse flag is one of
   the forwarded entries: the caller's choice of that flag (default off) is
   propagated into the configuration verbatim, so that downstream fitting reuses
   the previous fit and adds more estimators when it is on, and builds a fresh
   ensemble when it is off. Exposing this flag must NOT disturb any of the entries
   already forwarded: the targeted estimator count, the sample and feature
   budgets, the replacement flag, and the parallelism / randomness / verbosity
   handles each continue to equal the corresponding argument.

   All arguments are read-only (none is `mut`): the constructor reads each
   argument and assembles a configuration, mutating no input (directive 5). Each
   forwarded argument is modeled as an opaque handle (`Param`) whose identity the
   forwarding preserves; the two genuine booleans are carried as `Bool`
   (mapping.md §2). -/
method configureEnsemble
    (nEstimators : Param) (maxSamples : Param) (maxFeatures : Param)
    (bootstrap : Bool) (nJobs : Param) (randomState : Param) (verbose : Param)
    (warmStart : Bool)
    return (cfg : EnsembleConfig)
  ensures cfg.nEstimators = nEstimators
  ensures cfg.maxSamples = maxSamples
  ensures cfg.maxFeatures = maxFeatures
  ensures cfg.bootstrap = bootstrap
  ensures cfg.nJobs = nJobs
  ensures cfg.randomState = randomState
  ensures cfg.verbose = verbose
  ensures cfg.warmStart = warmStart
  do
    -- impl-start
    -- Forward every carried entry verbatim, INCLUDING the incremental-fit reuse
    -- flag taken from the caller's argument.
    return { nEstimators := nEstimators, maxSamples := maxSamples,
             maxFeatures := maxFeatures, bootstrap := bootstrap,
             warmStart := warmStart, nJobs := nJobs,
             randomState := randomState, verbose := verbose }
    -- impl-end

prove_correct configureEnsemble by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: velvet `configureEnsemble` models IsolationForest.__init__ forwarding its 8 args into the EnsembleConfig handed to super().__init__. The spec pins EVERY output field with a dedicated `ensures` clause (cfg.nEstimators=nEstimators, ...maxSamples, maxFeatures, bootstrap, nJobs, randomState, verbose, AND the newly-forwarded cfg.warmStart=warmStart). This FULLY DETERMINES the return value: there is zero degree of freedom for a same-spec verifying impl to deviate from the field-by-field-equal config, which is exactly the gold behavior.

PROTOCOL: work done; same_spec confirmed True for all 8 attacks (velvet backend, swebench_unified.markers.same_spec) and True for pos_control; header/axioms/pure/pre/post left byte-identical, only impl region edited. Verifier: `bash scripts/lean_verify.sh <f>` (run concurrently, <=4 at a time).

ATTACKS & RESULTS:
- atk_1 (prepatch bug: warmStart:=false, ignores caller): VERIFY exit=1. Goal `false = warmStart` unsolved. Correctly rejected. (This reproduces Solution_prepatch.lean's failure => prepatch_reproduced=true.)
- atk_2 (ungrounded/hardcode: warmStart:=true): exit=1 (goal true=warmStart).
- atk_3 (field-swap frame corruption: nJobs:=verbose, verbose:=nJobs): exit=1.
- atk_4 (ungrounded-oracle echo / wrong source: warmStart:=bootstrap): exit=1.
- atk_5 (control-flow-effect: ws:=warmStart && false then warmStart:=ws): exit=1 (false=warmStart).
- atk_6 (arithmetic on handle: nEstimators:=nEstimators+1, boundary/identity break): exit=1 (goal nEstimators+1=nEstimators).
- atk_7 (partial-domain: only forwards warmStart when bootstrap else false): exit=1.
- atk_8 (CORRECT partial-domain reformulation: case-split on warmStart, forwarding true/false respectively -> behaviorally identical to gold): VERIFY exit=0.
- pos_control (gold impl verbatim): VERIFY exit=0.

RESOLVE (mandatory for every verifying attack): atk_8 is the ONLY verifying wrong-shaped candidate and it is behaviorally identical to gold (both branches yield cfg.warmStart=warmStart and all other fields = args). Its faithful refined Python patch is the gold patch.diff (forward warm_start=warm_start in super().__init__ + signature + docstring). Ran through the OFFICIAL harness via swebench_unified.harness.run_resolve('scikit-learn__scikit-learn-13496', <gold patch>, timeout=1800) under FSx HOME + docker: COMPLETED=True, RESOLVED=True, ATTEMPTS=1, FLAKY=False, NOTE='resolved'. => the verifying candidate's materialized patch RESOLVES. No verify-but-not-resolve breaker found.

REFINEMENT AUDIT: refinement.md legs A1..A8 are all R or R+I; §B explicitly asserts no kind-3 (inexpressible-changed-op) step and there are NO A-legs (no axioms, no A-consumed, no A-reference) — confirmed by mapping.md §3 (Callee provenance: None). The genuinely-changed op (exposing/forwarding warm_start) is modeled DIRECTLY as the concrete `warmStart` field (tag R), not hidden behind an axiom. The incremental-fit ALGORITHM the flag controls lives in unchanged BaseBagging._fit and is correctly NOT re-modeled (SPEC_GUIDE faithfulness). Since there are no A-legs, there is no A-correspondence that can be broken. Total-correctness semantics (loom.semantics.termination total) rules out a divergent same-spec impl vacuously satisfying the ensures.

CONCLUSION: The spec is fully field-pinned; every distinct wrong impl (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, frame-swap, prepatch) fails verification with genuine postcondition goals, and the sole verifying variant is behaviorally correct and RESOLVES under the official harness. verify => correct holds. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for scikit-learn__scikit-learn-13496 velvet bundle.

### Spec integrity
- same_spec(Solution, Solution_prepatch) = True (byte-identical spec view via swebench_unified.markers with velvet backend). Spec regions differ only in the elided impl.
- Solution.lean VERIFIES (lean_verify.sh RC=0). Solution_prepatch.lean fails exactly at `ensures cfg.warmStart = warmStart` (goal `false = warmStart`), the intended G-DIFF discriminator.

REAL CALLEE (base_commit 3aefc834, sklearn/ensemble/iforest.py:167): IsolationForest.__init__ is pure config plumbing — it forwards each of its arguments verbatim into the super().__init__ keyword bundle (n_estimators, max_samples, max_features, bootstrap, n_jobs, random_state, verbose), and the gold patch ADDS warm_start=warm_start to both the signature (default False) and the forwarded bundle. No transformation/arithmetic/inspection is applied to any forwarded entry. Parent BaseBagging.__init__ accepts and stores warm_start (bagging.py:200/213), so post-patch construction succeeds; pre-patch raises TypeError.

### SPEC vs CALLEE:
- The spec models the forwarded configuration as an 8-field EnsembleConfig with one `ensures cfg.x = x` per entry. This is EXACTLY the verbatim-forwarding behavior of the gold constructor. The gold impl satisfies every postcondition on every input (each param equals its argument in the forwarded bundle), so the spec is not too strong — no correct implementation of the gold behavior is excluded.
- Opaque args modeled as Int identity handles is faithful: the constructor observes only identity (pass-through), never value structure. bool↔Bool exact for bootstrap/warm_start.
- Modeling boundary is correct: behaviour/contamination are set as plain attributes (NOT forwarded to super().__init__), so their exclusion from EnsembleConfig matches reality. random_state is additionally consumed to seed the base ExtraTreeRegressor, but the forwarded random_state keyword still equals the argument, so `cfg.randomState = randomState` holds — no divergence.
- The incremental-fit ALGORITHM the flag controls lives in unchanged BaseBagging._fit and is correctly NOT re-modeled (the patch only plumbs the flag). total-correctness semantics is the faithful choice for a straight-line always-terminating constructor.

No input found where the modeled function disagrees with the real callee. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified spec region byte-identical: markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) == True. Assessed the exact G-LEAK spec view (impl elided) against the PUBLIC problem_statement (not hints_text).

The public problem_statement already discloses the entire gold edit explicitly: 'expose warm_start in IsolationForest.__init__(), default False', quotes the exact docstring ('When set to True, reuse the solution of the previous call to fit and add more estimators to the ensemble, otherwise, just fit a whole new forest'), and describes that the flag is inherited/forwarded from the parent BaseBagging. The gold patch is exactly (1) that docstring hunk, (2) warm_start=False added to the signature, (3) warm_start=warm_start added to super().__init__.

Everything the spec view reveals is a subset of the public statement:
- structure field `warmStart : Bool` and argument `warmStart` (default off) <= 'expose warm_start ... default False'.
- doc comment 'incremental-fit reuse flag: when on, a subsequent fit reuses the previous fit and adds more estimators rather than building a fresh ensemble' is a paraphrase of the public docstring text quoted verbatim in the problem_statement.
- `ensures cfg.warmStart = warmStart` (forward verbatim) <= public description of forwarding to BaseBagging.
- the frame fields (nEstimators, maxSamples, maxFeatures, bootstrap, nJobs, randomState, verbose) are generic IsolationForest constructor parameters, publicly visible library API, not gold-specific.

Nothing goes beyond problem_statement. Gold-specific F2P test internals (test_iforest_warm_start name, `clf.estimators_[0] is tree_1`, growth to 20 estimators, TypeError pre-patch, iforest.py line numbers) appear ONLY in refinement.md / mapping.md / conformance_check.py, which are NOT part of the spec view that G-LEAK screens. No hidden-test assertions, no gold line numbers, no reconstruction-enabling detail leaks through the spec view itself. Clean.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
