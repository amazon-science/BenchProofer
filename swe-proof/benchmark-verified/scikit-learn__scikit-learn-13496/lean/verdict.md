# P2 adversarial audit — scikit-learn__scikit-learn-13496

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk1_wswap.lean`, `atk2_bftrue.lean`, `atk3_oobtrue.lean`, `atk4_nesucc.lean`, `atk5_verbose0.lean`, `atk6_behconst.lean`, `atk7_partial.lean`, `atk8_neconst.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl admits a closing proof, so there is no verify⇏correct break to exhibit. The postcondition problem_spec_isolationForestInit pins all 12 record fields to inputs (10 to their inputs, bootstrapFeatures/oobScore to the constant false), universally quantified over all inputs, with 5 fields (maxSamples/contamination/maxFeatures/nJobs/randomState) typed at OPAQUE type variables whose only inhabitant in scope is the corresponding input. Any deviation on any field produces a universally-false equality (e.g. atk1 warmStart:=bootstrap needs bootstrap=warmStart ∀; atk7 partial-domain needs (if nEstimators=0 then false else warmStart)=warmStart ∀, false at nEstimators=0∧warmStart=true) that no tactic can discharge. All attacks fail with genuine 'Application type mismatch: rfl' errors, not timeouts.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_wswap.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,7 +73,7 @@
     bootstrap := bootstrap,
     bootstrapFeatures := false,
     oobScore := false,
-    warmStart := warmStart,
+    warmStart := bootstrap,
     nJobs := nJobs,
     behaviour := behaviour,
     randomState := randomState,
```

Attack 2 — `atk2_bftrue.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,7 +71,7 @@
     contamination := contamination,
     maxFeatures := maxFeatures,
     bootstrap := bootstrap,
-    bootstrapFeatures := false,
+    bootstrapFeatures := true,
     oobScore := false,
     warmStart := warmStart,
     nJobs := nJobs,
```

Attack 3 — `atk3_oobtrue.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,7 +72,7 @@
     maxFeatures := maxFeatures,
     bootstrap := bootstrap,
     bootstrapFeatures := false,
-    oobScore := false,
+    oobScore := true,
     warmStart := warmStart,
     nJobs := nJobs,
     behaviour := behaviour,
```

Attack 4 — `atk4_nesucc.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,7 @@
   -- forward the bagging parameters to the parent constructor, exposing the
   -- incremental-refit flag so it is stored as supplied
   let mut cfg : EnsembleConfig Sample Contam Feat Jobs Rand := {
-    nEstimators := nEstimators,
+    nEstimators := nEstimators + 1,
     maxSamples := maxSamples,
     contamination := contamination,
     maxFeatures := maxFeatures,
```

Attack 5 — `atk5_verbose0.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,7 @@
     nJobs := nJobs,
     behaviour := behaviour,
     randomState := randomState,
-    verbose := verbose }
+    verbose := 0 }
   return cfg
 -- impl-end
 
```

Attack 6 — `atk6_behconst.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,7 +75,7 @@
     oobScore := false,
     warmStart := warmStart,
     nJobs := nJobs,
-    behaviour := behaviour,
+    behaviour := "",
     randomState := randomState,
     verbose := verbose }
   return cfg
```

Attack 7 — `atk7_partial.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,7 +73,7 @@
     bootstrap := bootstrap,
     bootstrapFeatures := false,
     oobScore := false,
-    warmStart := warmStart,
+    warmStart := (if nEstimators = 0 then false else warmStart),
     nJobs := nJobs,
     behaviour := behaviour,
     randomState := randomState,
```

Attack 8 — `atk8_neconst.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,7 @@
   -- forward the bagging parameters to the parent constructor, exposing the
   -- incremental-refit flag so it is stored as supplied
   let mut cfg : EnsembleConfig Sample Contam Feat Jobs Rand := {
-    nEstimators := nEstimators,
+    nEstimators := 100,
     maxSamples := maxSamples,
     contamination := contamination,
     maxFeatures := maxFeatures,
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the constructor only forwards
-- and stores its arguments (each parent assignment is an identity store), so the
-- behavior is modeled DIRECTLY as record-field assignment rather than
-- axiomatized. The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The settable configuration an outlier-ensemble estimator stores at
construction time. The five value-carrying parameters that the constructor only
passes through (never inspecting them) are modeled as type variables, since the
constructor stores them by identity. -/
structure EnsembleConfig (Sample Contam Feat Jobs Rand : Type) where
  nEstimators : Nat
  maxSamples : Sample
  contamination : Contam
  maxFeatures : Feat
  bootstrap : Bool
  bootstrapFeatures : Bool
  oobScore : Bool
  warmStart : Bool
  nJobs : Jobs
  behaviour : String
  randomState : Rand
  verbose : Nat
-- pure-end

-- post-conditions-start
/-- The constructed configuration stores every supplied parameter by identity:
the incremental-refit flag is held exactly as the caller supplied it, the
sample-replacement flag and the verbosity / tree-count / strategy / state values
are stored unchanged, and the two configuration flags that this estimator never
exposes are held at their default values (feature subsampling off, out-of-bag
scoring off). Every output component is pinned to its input — no field is left
free. -/
def problem_spec_isolationForestInit
    {Sample Contam Feat Jobs Rand : Type}
    (nEstimators : Nat) (maxSamples : Sample) (contamination : Contam)
    (maxFeatures : Feat) (bootstrap : Bool) (nJobs : Jobs) (behaviour : String)
    (randomState : Rand) (verbose : Nat) (warmStart : Bool)
    (result : EnsembleConfig Sample Contam Feat Jobs Rand) : Prop :=
  result.warmStart = warmStart ∧
  result.bootstrap = bootstrap ∧
  result.bootstrapFeatures = false ∧
  result.oobScore = false ∧
  result.nEstimators = nEstimators ∧
  result.maxSamples = maxSamples ∧
  result.contamination = contamination ∧
  result.maxFeatures = maxFeatures ∧
  result.nJobs = nJobs ∧
  result.behaviour = behaviour ∧
  result.randomState = randomState ∧
  result.verbose = verbose
-- post-conditions-end

-- impl-start
def implementation_isolationForestInit
    {Sample Contam Feat Jobs Rand : Type}
    (nEstimators : Nat) (maxSamples : Sample) (contamination : Contam)
    (maxFeatures : Feat) (bootstrap : Bool) (nJobs : Jobs) (behaviour : String)
    (randomState : Rand) (verbose : Nat) (warmStart : Bool) :
    EnsembleConfig Sample Contam Feat Jobs Rand := Id.run do
  -- forward the bagging parameters to the parent constructor, exposing the
  -- incremental-refit flag so it is stored as supplied
  let mut cfg : EnsembleConfig Sample Contam Feat Jobs Rand := {
    nEstimators := nEstimators,
    maxSamples := maxSamples,
    contamination := contamination,
    maxFeatures := maxFeatures,
    bootstrap := bootstrap,
    bootstrapFeatures := false,
    oobScore := false,
    warmStart := warmStart,
    nJobs := nJobs,
    behaviour := behaviour,
    randomState := randomState,
    verbose := verbose }
  return cfg
-- impl-end

-- proof-start
theorem correct_isolationForestInit
    {Sample Contam Feat Jobs Rand : Type}
    (nEstimators : Nat) (maxSamples : Sample) (contamination : Contam)
    (maxFeatures : Feat) (bootstrap : Bool) (nJobs : Jobs) (behaviour : String)
    (randomState : Rand) (verbose : Nat) (warmStart : Bool) :
    problem_spec_isolationForestInit nEstimators maxSamples contamination
      maxFeatures bootstrap nJobs behaviour randomState verbose warmStart
      (implementation_isolationForestInit nEstimators maxSamples contamination
        maxFeatures bootstrap nJobs behaviour randomState verbose warmStart) := by
  unfold problem_spec_isolationForestInit implementation_isolationForestInit
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Verification (bash scripts/lean_verify.sh <f>), run concurrently in batches of ≤4: pos_control exit=0 (verifies, no sorry); #print axioms correct_isolationForestInit => 'does not depend on any axioms' (CLEAN). atk_prepatch (warmStart:=false) exit=1 => prepatch bug reproduced. All 8 wrong impls exit=1 (genuine unprovable-equality errors, NOT timeouts): atk1 warmStart:=bootstrap (control-flow/wrong-field), atk2 bootstrapFeatures:=true, atk3 oobScore:=true (constant flips), atk4 nEstimators:=nEstimators+1 (boundary/off-by-one), atk5 verbose:=0 (partial-domain, correct only when verbose=0), atk6 behaviour:="" (ungrounded constant), atk7 warmStart:=if nEstimators=0 then false else warmStart (partial-domain/boundary), atk8 nEstimators:=100 (partial-domain constant).

Because NO wrong impl closes with clean axioms, there is no faithful patch to materialize/resolve — patches={} is correct, not an omission. refinement.md audit: 12 legs, all I or R (rows 1-4,7 I; 5,6 R int↔Nat; 8-12 R opaque identity-store); ZERO kind-3, no A-consumed, no A-reference. Empty axioms region is justified: the changed op threads warm_start into the stored config, modeled directly as field assignment; parent BaseBagging.__init__ does per-attribute identity stores (no opaque unchanged-callee contract), so axiom_check.py skip stub is correct and A-legs are vacuous. R/I legs covered by G-CONF (conformance_check.py compares the identity-store shadow to real post-patch IsolationForest(**kwargs) attributes over ≥1e5 fuzzed inputs, seed 13496). Model↔patch correspondence to sklearn/ensemble/iforest.py IsolationForest.__init__ + BaseBagging.__init__ holds. Verdict SOUND: ≥5 (here 8) distinct wrong-impl attacks run, none breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk1_wswap.lean`, `atk2_bftrue.lean`, `atk3_oobtrue.lean`, `atk4_nesucc.lean`, `atk5_verbose0.lean`, `atk6_behconst.lean`, `atk7_partial.lean`, `atk8_neconst.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl admits a closing proof, so there is no verify⇏correct break to exhibit. The postcondition problem_spec_isolationForestInit pins all 12 record fields to inputs (10 to their inputs, bootstrapFeatures/oobScore to the constant false), universally quantified over all inputs, with 5 fields (maxSamples/contamination/maxFeatures/nJobs/randomState) typed at OPAQUE type variables whose only inhabitant in scope is the corresponding input. Any deviation on any field produces a universally-false equality (e.g. atk1 warmStart:=bootstrap needs bootstrap=warmStart ∀; atk7 partial-domain needs (if nEstimators=0 then false else warmStart)=warmStart ∀, false at nEstimators=0∧warmStart=true) that no tactic can discharge. All attacks fail with genuine 'Application type mismatch: rfl' errors, not timeouts.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_wswap.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_bftrue.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_oobtrue.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_nesucc.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_verbose0.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_behconst.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_partial.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk8_neconst.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the constructor only forwards
-- and stores its arguments (each parent assignment is an identity store), so the
-- behavior is modeled DIRECTLY as record-field assignment rather than
-- axiomatized. The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The settable configuration an outlier-ensemble estimator stores at
construction time. The five value-carrying parameters that the constructor only
passes through (never inspecting them) are modeled as type variables, since the
constructor stores them by identity. -/
structure EnsembleConfig (Sample Contam Feat Jobs Rand : Type) where
  nEstimators : Nat
  maxSamples : Sample
  contamination : Contam
  maxFeatures : Feat
  bootstrap : Bool
  bootstrapFeatures : Bool
  oobScore : Bool
  warmStart : Bool
  nJobs : Jobs
  behaviour : String
  randomState : Rand
  verbose : Nat
-- pure-end

-- post-conditions-start
/-- The constructed configuration stores every supplied parameter by identity:
the incremental-refit flag is held exactly as the caller supplied it, the
sample-replacement flag and the verbosity / tree-count / strategy / state values
are stored unchanged, and the two configuration flags that this estimator never
exposes are held at their default values (feature subsampling off, out-of-bag
scoring off). Every output component is pinned to its input — no field is left
free. -/
def problem_spec_isolationForestInit
    {Sample Contam Feat Jobs Rand : Type}
    (nEstimators : Nat) (maxSamples : Sample) (contamination : Contam)
    (maxFeatures : Feat) (bootstrap : Bool) (nJobs : Jobs) (behaviour : String)
    (randomState : Rand) (verbose : Nat) (warmStart : Bool)
    (result : EnsembleConfig Sample Contam Feat Jobs Rand) : Prop :=
  result.warmStart = warmStart ∧
  result.bootstrap = bootstrap ∧
  result.bootstrapFeatures = false ∧
  result.oobScore = false ∧
  result.nEstimators = nEstimators ∧
  result.maxSamples = maxSamples ∧
  result.contamination = contamination ∧
  result.maxFeatures = maxFeatures ∧
  result.nJobs = nJobs ∧
  result.behaviour = behaviour ∧
  result.randomState = randomState ∧
  result.verbose = verbose
-- post-conditions-end

-- impl-start
def implementation_isolationForestInit
    {Sample Contam Feat Jobs Rand : Type}
    (nEstimators : Nat) (maxSamples : Sample) (contamination : Contam)
    (maxFeatures : Feat) (bootstrap : Bool) (nJobs : Jobs) (behaviour : String)
    (randomState : Rand) (verbose : Nat) (warmStart : Bool) :
    EnsembleConfig Sample Contam Feat Jobs Rand := Id.run do
  -- forward the bagging parameters to the parent constructor, exposing the
  -- incremental-refit flag so it is stored as supplied
  let mut cfg : EnsembleConfig Sample Contam Feat Jobs Rand := {
    nEstimators := nEstimators,
    maxSamples := maxSamples,
    contamination := contamination,
    maxFeatures := maxFeatures,
    bootstrap := bootstrap,
    bootstrapFeatures := false,
    oobScore := false,
    warmStart := warmStart,
    nJobs := nJobs,
    behaviour := behaviour,
    randomState := randomState,
    verbose := verbose }
  return cfg
-- impl-end

-- proof-start
theorem correct_isolationForestInit
    {Sample Contam Feat Jobs Rand : Type}
    (nEstimators : Nat) (maxSamples : Sample) (contamination : Contam)
    (maxFeatures : Feat) (bootstrap : Bool) (nJobs : Jobs) (behaviour : String)
    (randomState : Rand) (verbose : Nat) (warmStart : Bool) :
    problem_spec_isolationForestInit nEstimators maxSamples contamination
      maxFeatures bootstrap nJobs behaviour randomState verbose warmStart
      (implementation_isolationForestInit nEstimators maxSamples contamination
        maxFeatures bootstrap nJobs behaviour randomState verbose warmStart) := by
  unfold problem_spec_isolationForestInit implementation_isolationForestInit
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Verification (bash scripts/lean_verify.sh <f>), run concurrently in batches of ≤4: pos_control exit=0 (verifies, no sorry); #print axioms correct_isolationForestInit => 'does not depend on any axioms' (CLEAN). atk_prepatch (warmStart:=false) exit=1 => prepatch bug reproduced. All 8 wrong impls exit=1 (genuine unprovable-equality errors, NOT timeouts): atk1 warmStart:=bootstrap (control-flow/wrong-field), atk2 bootstrapFeatures:=true, atk3 oobScore:=true (constant flips), atk4 nEstimators:=nEstimators+1 (boundary/off-by-one), atk5 verbose:=0 (partial-domain, correct only when verbose=0), atk6 behaviour:="" (ungrounded constant), atk7 warmStart:=if nEstimators=0 then false else warmStart (partial-domain/boundary), atk8 nEstimators:=100 (partial-domain constant).

Because NO wrong impl closes with clean axioms, there is no faithful patch to materialize/resolve — patches={} is correct, not an omission. refinement.md audit: 12 legs, all I or R (rows 1-4,7 I; 5,6 R int↔Nat; 8-12 R opaque identity-store); ZERO kind-3, no A-consumed, no A-reference. Empty axioms region is justified: the changed op threads warm_start into the stored config, modeled directly as field assignment; parent BaseBagging.__init__ does per-attribute identity stores (no opaque unchanged-callee contract), so axiom_check.py skip stub is correct and A-legs are vacuous. R/I legs covered by G-CONF (conformance_check.py compares the identity-store shadow to real post-patch IsolationForest(**kwargs) attributes over ≥1e5 fuzzed inputs, seed 13496). Model↔patch correspondence to sklearn/ensemble/iforest.py IsolationForest.__init__ + BaseBagging.__init__ holds. Verdict SOUND: ≥5 (here 8) distinct wrong-impl attacks run, none breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found no divergence. (1) Spec region byte-identical between Solution.lean and Solution_prepatch.lean via same_spec(...,lean_tables)=True; the two differ only in the impl region (warmStart:=warmStart vs :=false). (2) Solution.lean verifies (lean_verify exit 0) and `#print axioms correct_isolationForestInit` reports NO axioms — proof is genuine, no sorryAx. (3) Verified the real callee chain at base_commit 3aefc834: IsolationForest.__init__ -> BaseBagging.__init__ (identity stores for max_samples,max_features,bootstrap,bootstrap_features,oob_score,warm_start,n_jobs,random_state,verbose) -> BaseEnsemble.__init__ (stores n_estimators), plus subclass self.behaviour/self.contamination. Every one of the 12 modeled fields is a plain identity store. The two pinned constants are correct: bootstrap_features=False is a hardcoded literal in the super() call; oob_score is never passed so it takes parent default False. n_estimators/behaviour/contamination validation happens in fit(), not __init__, so the constructor stores all args unchanged — matching the polymorphic identity-store model. (4) G-CONF corroborates: 120002 fuzzed inputs, 0 disagreements (seed 13496). The only modeling narrowing is Python int -> Lean Nat for n_estimators/verbose (negatives inexpressible), but __init__ does no validation and this is a domain restriction, not a wrong-output divergence; for every representable input the model equals the real constructor. No input makes the modeled function disagree with the real callee — spec is not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (verified: swebench_unified.markers.same_spec(a,b,lean_backend)=True; diff confirms only the impl comment + `warmStart := warmStart` vs `false` and the proof-body comments differ, all of which are ELIDED in the spec view). Leakage judged strictly against the public problem_statement (hints_text NOT consulted). The problem_statement is maximally explicit about the gold edit: it directly requests 'expose warm_start in IsolationForest.__init__(), default False', names the inherited-but-unforwarded flag from the parent BaseBagging, describes the forwarding mechanism, and even quotes the exact docstring block. The spec view's operative postcondition `result.warmStart = warmStart` states the flag is stored as supplied — precisely what the public issue asks for — and treats all fields uniformly ('every output component is pinned to its input'), so it does not single out warm_start as the change locus any more sharply than the public issue. The default-off fields (bootstrapFeatures=false, oobScore=false) reflect ordinary constructor structure, not the fix. refinement.md/mapping.md describe forwarding warm_start into super().__init__, again matching the public request, not exceeding it. No line in the spec view discloses the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.