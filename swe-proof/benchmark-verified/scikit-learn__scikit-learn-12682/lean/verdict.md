# P2 adversarial audit — scikit-learn__scikit-learn-12682

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,18 +88,13 @@
     (nComponents algorithm : Nat) (nNonzeroCoefs : Option Nat) (alpha : Option Rat)
     (splitSign : Bool) (nJobs : Option Nat) (positive : Bool) (maxIter : Nat)
     : SolverArgs := Id.run do
-  -- Record every supplied option into the estimator's stored configuration,
-  -- including the solver iteration budget.
   let cfg : CodingConfig :=
     { nComponents := nComponents, algorithm := algorithm,
       nNonzeroCoefs := nNonzeroCoefs, alpha := alpha, splitSign := splitSign,
       nJobs := nJobs, positive := positive, maxIter := maxIter }
-  -- Encoding step: assemble the solver-argument bundle from the stored
-  -- configuration. Each argument is drawn from its configured option, and the
-  -- solver's iteration budget is drawn from the configured `maxIter`.
   let mut args : SolverArgs :=
     { algorithm := cfg.algorithm, nNonzeroCoefs := cfg.nNonzeroCoefs,
-      alpha := cfg.alpha, maxIter := cfg.maxIter, nJobs := cfg.nJobs,
+      alpha := cfg.alpha, maxIter := 1000, nJobs := cfg.nJobs,
       positive := cfg.positive }
   return args
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,19 +88,15 @@
     (nComponents algorithm : Nat) (nNonzeroCoefs : Option Nat) (alpha : Option Rat)
     (splitSign : Bool) (nJobs : Option Nat) (positive : Bool) (maxIter : Nat)
     : SolverArgs := Id.run do
-  -- Record every supplied option into the estimator's stored configuration,
-  -- including the solver iteration budget.
   let cfg : CodingConfig :=
     { nComponents := nComponents, algorithm := algorithm,
       nNonzeroCoefs := nNonzeroCoefs, alpha := alpha, splitSign := splitSign,
       nJobs := nJobs, positive := positive, maxIter := maxIter }
-  -- Encoding step: assemble the solver-argument bundle from the stored
-  -- configuration. Each argument is drawn from its configured option, and the
-  -- solver's iteration budget is drawn from the configured `maxIter`.
   let mut args : SolverArgs :=
     { algorithm := cfg.algorithm, nNonzeroCoefs := cfg.nNonzeroCoefs,
-      alpha := cfg.alpha, maxIter := cfg.maxIter, nJobs := cfg.nJobs,
-      positive := cfg.positive }
+      alpha := cfg.alpha,
+      maxIter := (if cfg.maxIter < 100 then 100 else cfg.maxIter),
+      nJobs := cfg.nJobs, positive := cfg.positive }
   return args
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,18 +88,13 @@
     (nComponents algorithm : Nat) (nNonzeroCoefs : Option Nat) (alpha : Option Rat)
     (splitSign : Bool) (nJobs : Option Nat) (positive : Bool) (maxIter : Nat)
     : SolverArgs := Id.run do
-  -- Record every supplied option into the estimator's stored configuration,
-  -- including the solver iteration budget.
   let cfg : CodingConfig :=
     { nComponents := nComponents, algorithm := algorithm,
       nNonzeroCoefs := nNonzeroCoefs, alpha := alpha, splitSign := splitSign,
       nJobs := nJobs, positive := positive, maxIter := maxIter }
-  -- Encoding step: assemble the solver-argument bundle from the stored
-  -- configuration. Each argument is drawn from its configured option, and the
-  -- solver's iteration budget is drawn from the configured `maxIter`.
   let mut args : SolverArgs :=
     { algorithm := cfg.algorithm, nNonzeroCoefs := cfg.nNonzeroCoefs,
-      alpha := cfg.alpha, maxIter := cfg.maxIter, nJobs := cfg.nJobs,
+      alpha := cfg.alpha, maxIter := cfg.maxIter + 1, nJobs := cfg.nJobs,
       positive := cfg.positive }
   return args
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,19 +88,14 @@
     (nComponents algorithm : Nat) (nNonzeroCoefs : Option Nat) (alpha : Option Rat)
     (splitSign : Bool) (nJobs : Option Nat) (positive : Bool) (maxIter : Nat)
     : SolverArgs := Id.run do
-  -- Record every supplied option into the estimator's stored configuration,
-  -- including the solver iteration budget.
   let cfg : CodingConfig :=
     { nComponents := nComponents, algorithm := algorithm,
       nNonzeroCoefs := nNonzeroCoefs, alpha := alpha, splitSign := splitSign,
       nJobs := nJobs, positive := positive, maxIter := maxIter }
-  -- Encoding step: assemble the solver-argument bundle from the stored
-  -- configuration. Each argument is drawn from its configured option, and the
-  -- solver's iteration budget is drawn from the configured `maxIter`.
   let mut args : SolverArgs :=
     { algorithm := cfg.algorithm, nNonzeroCoefs := cfg.nNonzeroCoefs,
       alpha := cfg.alpha, maxIter := cfg.maxIter, nJobs := cfg.nJobs,
-      positive := cfg.positive }
+      positive := (if cfg.splitSign then true else cfg.positive) }
   return args
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,17 +88,12 @@
     (nComponents algorithm : Nat) (nNonzeroCoefs : Option Nat) (alpha : Option Rat)
     (splitSign : Bool) (nJobs : Option Nat) (positive : Bool) (maxIter : Nat)
     : SolverArgs := Id.run do
-  -- Record every supplied option into the estimator's stored configuration,
-  -- including the solver iteration budget.
   let cfg : CodingConfig :=
     { nComponents := nComponents, algorithm := algorithm,
       nNonzeroCoefs := nNonzeroCoefs, alpha := alpha, splitSign := splitSign,
       nJobs := nJobs, positive := positive, maxIter := maxIter }
-  -- Encoding step: assemble the solver-argument bundle from the stored
-  -- configuration. Each argument is drawn from its configured option, and the
-  -- solver's iteration budget is drawn from the configured `maxIter`.
   let mut args : SolverArgs :=
-    { algorithm := cfg.algorithm, nNonzeroCoefs := cfg.nNonzeroCoefs,
+    { algorithm := 0, nNonzeroCoefs := cfg.nNonzeroCoefs,
       alpha := cfg.alpha, maxIter := cfg.maxIter, nJobs := cfg.nJobs,
       positive := cfg.positive }
   return args
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,17 +88,12 @@
     (nComponents algorithm : Nat) (nNonzeroCoefs : Option Nat) (alpha : Option Rat)
     (splitSign : Bool) (nJobs : Option Nat) (positive : Bool) (maxIter : Nat)
     : SolverArgs := Id.run do
-  -- Record every supplied option into the estimator's stored configuration,
-  -- including the solver iteration budget.
   let cfg : CodingConfig :=
     { nComponents := nComponents, algorithm := algorithm,
       nNonzeroCoefs := nNonzeroCoefs, alpha := alpha, splitSign := splitSign,
       nJobs := nJobs, positive := positive, maxIter := maxIter }
-  -- Encoding step: assemble the solver-argument bundle from the stored
-  -- configuration. Each argument is drawn from its configured option, and the
-  -- solver's iteration budget is drawn from the configured `maxIter`.
   let mut args : SolverArgs :=
-    { algorithm := cfg.algorithm, nNonzeroCoefs := cfg.nNonzeroCoefs,
+    { algorithm := cfg.algorithm, nNonzeroCoefs := none,
       alpha := cfg.alpha, maxIter := cfg.maxIter, nJobs := cfg.nJobs,
       positive := cfg.positive }
   return args
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,18 +88,13 @@
     (nComponents algorithm : Nat) (nNonzeroCoefs : Option Nat) (alpha : Option Rat)
     (splitSign : Bool) (nJobs : Option Nat) (positive : Bool) (maxIter : Nat)
     : SolverArgs := Id.run do
-  -- Record every supplied option into the estimator's stored configuration,
-  -- including the solver iteration budget.
   let cfg : CodingConfig :=
     { nComponents := nComponents, algorithm := algorithm,
       nNonzeroCoefs := nNonzeroCoefs, alpha := alpha, splitSign := splitSign,
       nJobs := nJobs, positive := positive, maxIter := maxIter }
-  -- Encoding step: assemble the solver-argument bundle from the stored
-  -- configuration. Each argument is drawn from its configured option, and the
-  -- solver's iteration budget is drawn from the configured `maxIter`.
   let mut args : SolverArgs :=
     { algorithm := cfg.algorithm, nNonzeroCoefs := cfg.nNonzeroCoefs,
-      alpha := cfg.alpha, maxIter := cfg.maxIter, nJobs := cfg.nJobs,
+      alpha := none, maxIter := cfg.maxIter, nJobs := cfg.nJobs,
       positive := cfg.positive }
   return args
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing the parameters a sparse-coding estimator hands to its underlying
sparse-solver when it encodes data.

A sparse-coding estimator is configured once, at construction time, from a set
list of options:

  * `nComponents`   — the number of dictionary atoms;
  * `algorithm`     — which solver to use for the coding step;
  * `nNonzeroCoefs` — an optional cap on the number of non-zero coefficients;
  * `alpha`         — an optional sparsity-controlling parameter;
  * `splitSign`     — whether the coding is split into a positive and negative
                      side afterwards;
  * `nJobs`         — an optional parallelism selection;
  * `positive`      — whether a positivity constraint is enforced on the code;
  * `maxIter`       — the maximum number of iterations the underlying solver is
                      allowed to run.

These options are recorded into the estimator's stored configuration. When the
estimator later encodes data, it builds the bundle of arguments it passes to the
underlying sparse-solver out of that stored configuration. Every argument the
solver receives must come from the corresponding configured option — in
particular the iteration budget the solver is allowed must be the configured
`maxIter`, so that a caller who asks for more (or fewer) iterations actually gets
them rather than a constant standard amount. The desired behaviour is therefore
that the solver-argument bundle reproduces, field for field, exactly the
configured options it draws from.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- configuration step (recording each supplied option) and the assembly of the
-- solver-argument bundle from that stored configuration are modeled
-- structurally as field storage and field reads, so no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- The stored configuration of a sparse-coding estimator, restricted to the
options recorded at construction time. Identity-only selections (`algorithm`,
`nNonzeroCoefs`, `alpha`, `nJobs`) are modeled by injective encodings of the
distinct choices (absence ↔ `none`); the iteration budget is a `Nat`. -/
structure CodingConfig where
  nComponents : Nat
  algorithm : Nat
  nNonzeroCoefs : Option Nat
  alpha : Option Rat
  splitSign : Bool
  nJobs : Option Nat
  positive : Bool
  maxIter : Nat
deriving DecidableEq

/-- The bundle of arguments the estimator hands to the underlying sparse-solver
when it encodes data. -/
structure SolverArgs where
  algorithm : Nat
  nNonzeroCoefs : Option Nat
  alpha : Option Rat
  maxIter : Nat
  nJobs : Option Nat
  positive : Bool
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The solver-argument bundle reproduces, field for field, exactly the
configured options it draws from. Every argument is pinned to the corresponding
configured input — in particular the solver's iteration budget `maxIter` is the
configured `maxIter`, never replaced by a constant standard amount. -/
def problem_spec_codingSolverArgs
    (nComponents algorithm : Nat) (nNonzeroCoefs : Option Nat) (alpha : Option Rat)
    (splitSign : Bool) (nJobs : Option Nat) (positive : Bool) (maxIter : Nat)
    (result : SolverArgs) : Prop :=
  result.algorithm = algorithm ∧
  result.nNonzeroCoefs = nNonzeroCoefs ∧
  result.alpha = alpha ∧
  result.maxIter = maxIter ∧
  result.nJobs = nJobs ∧
  result.positive = positive
-- post-conditions-end

-- impl-start
def implementation_codingSolverArgs
    (nComponents algorithm : Nat) (nNonzeroCoefs : Option Nat) (alpha : Option Rat)
    (splitSign : Bool) (nJobs : Option Nat) (positive : Bool) (maxIter : Nat)
    : SolverArgs :=
  { algorithm := algorithm, nNonzeroCoefs := nNonzeroCoefs,
    alpha := alpha, maxIter := maxIter, nJobs := nJobs, positive := positive }
-- impl-end

-- proof-start
theorem correct_codingSolverArgs :
    ∀ (nComponents algorithm : Nat) (nNonzeroCoefs : Option Nat) (alpha : Option Rat)
      (splitSign : Bool) (nJobs : Option Nat) (positive : Bool) (maxIter : Nat),
      problem_spec_codingSolverArgs nComponents algorithm nNonzeroCoefs alpha splitSign nJobs positive maxIter
        (implementation_codingSolverArgs nComponents algorithm nNonzeroCoefs alpha splitSign nJobs positive maxIter) := by
  intro nComponents algorithm nNonzeroCoefs alpha splitSign nJobs positive maxIter
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

python via python3 with sys.path 'src'. All 8 files (7 attacks + positive control) confirmed byte-identical spec via swebench_unified.markers.same_spec => True (axioms/pure/pre/post regions untouched; only impl region + proof-block edited).

SPEC SHAPE: SolverArgs has exactly 6 fields; problem_spec_codingSolverArgs UNIVERSALLY pins every one of the 6 to its corresponding configured input (result.algorithm=algorithm, .nNonzeroCoefs=nNonzeroCoefs, .alpha=alpha, .maxIter=maxIter, .nJobs=nJobs, .positive=positive). This is a maximally tight identity spec: any behaviorally-incorrect impl makes correct_codingSolverArgs a FALSE proposition, so by Lean soundness NO proof can close it.

COMMANDS (ran concurrently in batches of <=4 background Bash jobs): `bash scripts/lean_verify.sh atk_N.lean`.

### RESULTS (exit code):
- atk_pos (correct, alternate direct-construction form, no cfg intermediate): exit 0 (VERIFIES). #print axioms correct_codingSolverArgs => 'depends on axioms: [propext]' (clean; no sorryAx). Confirms the tight spec is satisfiable by a faithful impl.
- atk_1 (prepatch bug: maxIter := 1000): exit 1, error at maxIter conjunct (line 111). Reproduces the real prepatch bug.
- atk_2 (partial-domain: maxIter clamped to 100 when <100): exit 1.
- atk_3 (boundary/off-by-one: maxIter := cfg.maxIter+1): exit 1.
- atk_4 (control-flow-effect: positive overridden true when splitSign): exit 1 at line 109:35.
- atk_5 (ungrounded-oracle echo: algorithm := 0 constant): exit 1 at line 109:10.
- atk_6 (drop optional: nNonzeroCoefs := none): exit 1 at line 109:15.
- atk_7 (drop optional: alpha := none): exit 1 at line 109:20.
Every failure is a genuine 'Application type mismatch: rfl : ?m=?m but expected <field> = <input>' at exactly the diverging conjunct — a real false-proposition failure, not a syntax artifact. All 7 attacks span the distinct classes (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, dropped-optionals) and cover 5 of the 6 spec fields + maxIter.

STEP-2 RESOLVE: VACUOUS. No same-spec wrong impl produced a closing proof (with or without clean axioms), so there is no verifying-but-wrong refined patch to materialize and run through the official harness. This is the expected outcome for a total identity spec — nothing to falsify at the patch level.

REFINEMENT/AXIOM AUDIT: refinement.md legs are all R/I (rows 1-3: config storage, arg-bundle assembly, return). No A-consumed, no A-reference, no kind-3. axiom_check.py is a justified skip stub — grep of Solution.lean confirms NO opaque/axiom callee (only structural field storage/reads), so the A-legs the reviewer role targets are absent by construction; there is no callee-correspondence to break. mapping.md's R/I correspondence (SolverArgs 6 fields <-> sparse_encode kwargs each pinned to self.*, with max_iter=self.transform_max_iter as the restored bit) matches patch.diff (dict_learning.py: _set_sparse_coding_params stores transform_max_iter; transform() adds max_iter=self.transform_max_iter to the sparse_encode call).

VERDICT: SOUND. verify => correct holds. 7 distinct same-spec wrong impls attempted, positive control verifies with clean axioms, prepatch bug reproduced; no closing clean-axiom wrong-impl exists, so verify does not admit an incorrect patch.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing the parameters a sparse-coding estimator hands to its underlying
sparse-solver when it encodes data.

A sparse-coding estimator is configured once, at construction time, from a set
list of options:

  * `nComponents`   — the number of dictionary atoms;
  * `algorithm`     — which solver to use for the coding step;
  * `nNonzeroCoefs` — an optional cap on the number of non-zero coefficients;
  * `alpha`         — an optional sparsity-controlling parameter;
  * `splitSign`     — whether the coding is split into a positive and negative
                      side afterwards;
  * `nJobs`         — an optional parallelism selection;
  * `positive`      — whether a positivity constraint is enforced on the code;
  * `maxIter`       — the maximum number of iterations the underlying solver is
                      allowed to run.

These options are recorded into the estimator's stored configuration. When the
estimator later encodes data, it builds the bundle of arguments it passes to the
underlying sparse-solver out of that stored configuration. Every argument the
solver receives must come from the corresponding configured option — in
particular the iteration budget the solver is allowed must be the configured
`maxIter`, so that a caller who asks for more (or fewer) iterations actually gets
them rather than a constant standard amount. The desired behaviour is therefore
that the solver-argument bundle reproduces, field for field, exactly the
configured options it draws from.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- configuration step (recording each supplied option) and the assembly of the
-- solver-argument bundle from that stored configuration are modeled
-- structurally as field storage and field reads, so no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- The stored configuration of a sparse-coding estimator, restricted to the
options recorded at construction time. Identity-only selections (`algorithm`,
`nNonzeroCoefs`, `alpha`, `nJobs`) are modeled by injective encodings of the
distinct choices (absence ↔ `none`); the iteration budget is a `Nat`. -/
structure CodingConfig where
  nComponents : Nat
  algorithm : Nat
  nNonzeroCoefs : Option Nat
  alpha : Option Rat
  splitSign : Bool
  nJobs : Option Nat
  positive : Bool
  maxIter : Nat
deriving DecidableEq

/-- The bundle of arguments the estimator hands to the underlying sparse-solver
when it encodes data. -/
structure SolverArgs where
  algorithm : Nat
  nNonzeroCoefs : Option Nat
  alpha : Option Rat
  maxIter : Nat
  nJobs : Option Nat
  positive : Bool
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The solver-argument bundle reproduces, field for field, exactly the
configured options it draws from. Every argument is pinned to the corresponding
configured input — in particular the solver's iteration budget `maxIter` is the
configured `maxIter`, never replaced by a constant standard amount. -/
def problem_spec_codingSolverArgs
    (nComponents algorithm : Nat) (nNonzeroCoefs : Option Nat) (alpha : Option Rat)
    (splitSign : Bool) (nJobs : Option Nat) (positive : Bool) (maxIter : Nat)
    (result : SolverArgs) : Prop :=
  result.algorithm = algorithm ∧
  result.nNonzeroCoefs = nNonzeroCoefs ∧
  result.alpha = alpha ∧
  result.maxIter = maxIter ∧
  result.nJobs = nJobs ∧
  result.positive = positive
-- post-conditions-end

-- impl-start
def implementation_codingSolverArgs
    (nComponents algorithm : Nat) (nNonzeroCoefs : Option Nat) (alpha : Option Rat)
    (splitSign : Bool) (nJobs : Option Nat) (positive : Bool) (maxIter : Nat)
    : SolverArgs :=
  { algorithm := algorithm, nNonzeroCoefs := nNonzeroCoefs,
    alpha := alpha, maxIter := maxIter, nJobs := nJobs, positive := positive }
-- impl-end

-- proof-start
theorem correct_codingSolverArgs :
    ∀ (nComponents algorithm : Nat) (nNonzeroCoefs : Option Nat) (alpha : Option Rat)
      (splitSign : Bool) (nJobs : Option Nat) (positive : Bool) (maxIter : Nat),
      problem_spec_codingSolverArgs nComponents algorithm nNonzeroCoefs alpha splitSign nJobs positive maxIter
        (implementation_codingSolverArgs nComponents algorithm nNonzeroCoefs alpha splitSign nJobs positive maxIter) := by
  intro nComponents algorithm nNonzeroCoefs alpha splitSign nJobs positive maxIter
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

python via python3 with sys.path 'src'. All 8 files (7 attacks + positive control) confirmed byte-identical spec via swebench_unified.markers.same_spec => True (axioms/pure/pre/post regions untouched; only impl region + proof-block edited).

SPEC SHAPE: SolverArgs has exactly 6 fields; problem_spec_codingSolverArgs UNIVERSALLY pins every one of the 6 to its corresponding configured input (result.algorithm=algorithm, .nNonzeroCoefs=nNonzeroCoefs, .alpha=alpha, .maxIter=maxIter, .nJobs=nJobs, .positive=positive). This is a maximally tight identity spec: any behaviorally-incorrect impl makes correct_codingSolverArgs a FALSE proposition, so by Lean soundness NO proof can close it.

COMMANDS (ran concurrently in batches of <=4 background Bash jobs): `bash scripts/lean_verify.sh atk_N.lean`.

### RESULTS (exit code):
- atk_pos (correct, alternate direct-construction form, no cfg intermediate): exit 0 (VERIFIES). #print axioms correct_codingSolverArgs => 'depends on axioms: [propext]' (clean; no sorryAx). Confirms the tight spec is satisfiable by a faithful impl.
- atk_1 (prepatch bug: maxIter := 1000): exit 1, error at maxIter conjunct (line 111). Reproduces the real prepatch bug.
- atk_2 (partial-domain: maxIter clamped to 100 when <100): exit 1.
- atk_3 (boundary/off-by-one: maxIter := cfg.maxIter+1): exit 1.
- atk_4 (control-flow-effect: positive overridden true when splitSign): exit 1 at line 109:35.
- atk_5 (ungrounded-oracle echo: algorithm := 0 constant): exit 1 at line 109:10.
- atk_6 (drop optional: nNonzeroCoefs := none): exit 1 at line 109:15.
- atk_7 (drop optional: alpha := none): exit 1 at line 109:20.
Every failure is a genuine 'Application type mismatch: rfl : ?m=?m but expected <field> = <input>' at exactly the diverging conjunct — a real false-proposition failure, not a syntax artifact. All 7 attacks span the distinct classes (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, dropped-optionals) and cover 5 of the 6 spec fields + maxIter.

STEP-2 RESOLVE: VACUOUS. No same-spec wrong impl produced a closing proof (with or without clean axioms), so there is no verifying-but-wrong refined patch to materialize and run through the official harness. This is the expected outcome for a total identity spec — nothing to falsify at the patch level.

REFINEMENT/AXIOM AUDIT: refinement.md legs are all R/I (rows 1-3: config storage, arg-bundle assembly, return). No A-consumed, no A-reference, no kind-3. axiom_check.py is a justified skip stub — grep of Solution.lean confirms NO opaque/axiom callee (only structural field storage/reads), so the A-legs the reviewer role targets are absent by construction; there is no callee-correspondence to break. mapping.md's R/I correspondence (SolverArgs 6 fields <-> sparse_encode kwargs each pinned to self.*, with max_iter=self.transform_max_iter as the restored bit) matches patch.diff (dict_learning.py: _set_sparse_coding_params stores transform_max_iter; transform() adds max_iter=self.transform_max_iter to the sparse_encode call).

VERDICT: SOUND. verify => correct holds. 7 distinct same-spec wrong impls attempted, positive control verifies with clean axioms, prepatch bug reproduced; no closing clean-axiom wrong-impl exists, so verify does not admit an incorrect patch.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift): searched for any input where the modeled function `codingSolverArgs` disagrees with the real patched callee; none found. The modeled boundary is exactly the keyword-argument bundle `SparseCodingMixin.transform()` hands to `sparse_encode(...)`, captured as a pure function of the construction-time options. In the real patched sklearn/decomposition/dict_learning.py @ base d360ffa7c5 + gold patch: `_set_sparse_coding_params` stores each option to the like-named self.* by identity (incl. new `self.transform_max_iter = transform_max_iter`); the `SparseCoder.__init__` forwards positionally; and `transform()` assembles the sparse_encode kwargs verbatim: algorithm=self.transform_algorithm, n_nonzero_coefs=self.transform_n_nonzero_coefs, alpha=self.transform_alpha, max_iter=self.transform_max_iter, n_jobs=self.n_jobs, positive=self.positive_code. That is exactly the six-conjunct field-copy the spec pins (result.algorithm=algorithm ∧ nNonzeroCoefs ∧ alpha ∧ maxIter ∧ nJobs ∧ positive). No transformation/clamping/validation on any field; max_iter is forwarded unconditionally (not gated on lasso_cd/lasso_lars) so result.maxIter=maxIter holds for every input, not just the F2P case. nComponents/splitSign are correctly OMITTED from SolverArgs (not passed to the solver). The Nat/Option/Rat encodings are injective abstractions that preserve the only asserted relation (field equality). Considered attacks that failed: (a) 'spec too strong on maxIter for non-cd/lars algorithms' — refuted, transform() always supplies the kwarg regardless of algorithm; (b) 'alpha as Rat mis-models float' — refuted, spec only asserts identity copy of the stored value; (c) 'positional-forwarding reorder bug' — checked constructor arg order matches _set_sparse_coding_params signature. Mechanical preconditions all pass: lean_verify.sh Solution.lean exit 0 (compiles, no sorry); #print axioms correct_codingSolverArgs -> depends only on [propext], NO sorryAx (proof is real, a plain 6-fold rfl); same_spec(Solution, Solution_prepatch, lean-tables) = True (spec regions byte-identical, only impl maxIter differs: gold cfg.maxIter vs prepatch constant 1000). No diverging input on the modeled domain -> FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The spec view (Solution.lean docstring + CodingConfig/SolverArgs structs + problem_spec_codingSolverArgs) contains no gold-patch specifics: no transform_max_iter, sparse_encode, _set_sparse_coding_params, Lasso/lasso_cd/lasso_lars, no filenames, and no line numbers. All gold-edit identifiers live only in refinement.md and mapping.md, which are auditor-facing derivation artifacts, not part of the spec view an implementer would see. The spec abstracts to a generic 'sparse-coding estimator' whose 'solver-argument bundle' must reproduce the configured options field-for-field, and pins result.maxIter = maxIter as the desired behavior. Both are within what the public problem_statement already discloses: the statement names max_iter, its default of 1000 ('by default is 1000'), that SparseCoder fails to set it for Lasso, and explicitly asks for 'a way for the user to specify other parameters' so the configured value reaches the solver. The one potentially sensitive phrase — 'rather than a constant standard amount' — merely restates the publicly-known 1000-default fact. Specifying the correct desired behavior (the user's configured iteration budget reaching the solver) is exactly what the problem_statement requests and is legitimate spec content, not leakage of the edit's mechanism. No spec-view line reveals the gold edit's mechanism (threading transform_max_iter through the constructors and adding the max_iter kwarg to the transform() -> sparse_encode call) beyond the public problem view.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
