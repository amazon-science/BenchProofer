# P2 adversarial audit — scikit-learn__scikit-learn-10297

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,15 +75,10 @@
     (alphas : List Rat) (fitIntercept normalize : Bool)
     (scoring cv classWeight : Option Nat) (storeCvValues : Bool)
     : ClassifierCVConfig := Id.run do
-  -- Delegate to the shared base initializer: record the regularization grid,
-  -- the intercept/normalize flags, the scorer and splitter selections, and the
-  -- cross-validation-values retention selection.
-  let mut cfg : ClassifierCVConfig :=
+  let cfg : ClassifierCVConfig :=
     { alphas := alphas, fitIntercept := fitIntercept, normalize := normalize,
-      scoring := scoring, cv := cv, storeCvValues := storeCvValues,
-      classWeight := none }
-  -- Record the per-class weighting selection on top of the base configuration.
-  cfg := { cfg with classWeight := classWeight }
+      scoring := scoring, cv := cv, storeCvValues := !storeCvValues,
+      classWeight := classWeight }
   return cfg
 -- impl-end
 
@@ -95,5 +90,6 @@
         (implementation_initClassifierCV alphas fitIntercept normalize scoring cv classWeight storeCvValues) := by
   intro alphas fitIntercept normalize scoring cv classWeight storeCvValues
   unfold problem_spec_initClassifierCV implementation_initClassifierCV
+  simp only [Id.run]
   refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩
 -- proof-end
```

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,15 +75,11 @@
     (alphas : List Rat) (fitIntercept normalize : Bool)
     (scoring cv classWeight : Option Nat) (storeCvValues : Bool)
     : ClassifierCVConfig := Id.run do
-  -- Delegate to the shared base initializer: record the regularization grid,
-  -- the intercept/normalize flags, the scorer and splitter selections, and the
-  -- cross-validation-values retention selection.
-  let mut cfg : ClassifierCVConfig :=
+  let cfg : ClassifierCVConfig :=
     { alphas := alphas, fitIntercept := fitIntercept, normalize := normalize,
-      scoring := scoring, cv := cv, storeCvValues := storeCvValues,
-      classWeight := none }
-  -- Record the per-class weighting selection on top of the base configuration.
-  cfg := { cfg with classWeight := classWeight }
+      scoring := scoring, cv := cv,
+      storeCvValues := (if cv = none then false else storeCvValues),
+      classWeight := classWeight }
   return cfg
 -- impl-end
 
@@ -95,5 +91,6 @@
         (implementation_initClassifierCV alphas fitIntercept normalize scoring cv classWeight storeCvValues) := by
   intro alphas fitIntercept normalize scoring cv classWeight storeCvValues
   unfold problem_spec_initClassifierCV implementation_initClassifierCV
+  simp only [Id.run]
   refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩
 -- proof-end
```

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,15 +75,10 @@
     (alphas : List Rat) (fitIntercept normalize : Bool)
     (scoring cv classWeight : Option Nat) (storeCvValues : Bool)
     : ClassifierCVConfig := Id.run do
-  -- Delegate to the shared base initializer: record the regularization grid,
-  -- the intercept/normalize flags, the scorer and splitter selections, and the
-  -- cross-validation-values retention selection.
-  let mut cfg : ClassifierCVConfig :=
+  let cfg : ClassifierCVConfig :=
     { alphas := alphas, fitIntercept := fitIntercept, normalize := normalize,
-      scoring := scoring, cv := cv, storeCvValues := storeCvValues,
-      classWeight := none }
-  -- Record the per-class weighting selection on top of the base configuration.
-  cfg := { cfg with classWeight := classWeight }
+      scoring := cv, cv := scoring, storeCvValues := storeCvValues,
+      classWeight := classWeight }
   return cfg
 -- impl-end
 
@@ -95,5 +90,6 @@
         (implementation_initClassifierCV alphas fitIntercept normalize scoring cv classWeight storeCvValues) := by
   intro alphas fitIntercept normalize scoring cv classWeight storeCvValues
   unfold problem_spec_initClassifierCV implementation_initClassifierCV
+  simp only [Id.run]
   refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩
 -- proof-end
```

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,15 +75,10 @@
     (alphas : List Rat) (fitIntercept normalize : Bool)
     (scoring cv classWeight : Option Nat) (storeCvValues : Bool)
     : ClassifierCVConfig := Id.run do
-  -- Delegate to the shared base initializer: record the regularization grid,
-  -- the intercept/normalize flags, the scorer and splitter selections, and the
-  -- cross-validation-values retention selection.
-  let mut cfg : ClassifierCVConfig :=
-    { alphas := alphas, fitIntercept := fitIntercept, normalize := normalize,
+  let cfg : ClassifierCVConfig :=
+    { alphas := [], fitIntercept := fitIntercept, normalize := normalize,
       scoring := scoring, cv := cv, storeCvValues := storeCvValues,
-      classWeight := none }
-  -- Record the per-class weighting selection on top of the base configuration.
-  cfg := { cfg with classWeight := classWeight }
+      classWeight := classWeight }
   return cfg
 -- impl-end
 
@@ -95,5 +90,6 @@
         (implementation_initClassifierCV alphas fitIntercept normalize scoring cv classWeight storeCvValues) := by
   intro alphas fitIntercept normalize scoring cv classWeight storeCvValues
   unfold problem_spec_initClassifierCV implementation_initClassifierCV
+  simp only [Id.run]
   refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩
 -- proof-end
```

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,15 +75,10 @@
     (alphas : List Rat) (fitIntercept normalize : Bool)
     (scoring cv classWeight : Option Nat) (storeCvValues : Bool)
     : ClassifierCVConfig := Id.run do
-  -- Delegate to the shared base initializer: record the regularization grid,
-  -- the intercept/normalize flags, the scorer and splitter selections, and the
-  -- cross-validation-values retention selection.
-  let mut cfg : ClassifierCVConfig :=
+  let cfg : ClassifierCVConfig :=
     { alphas := alphas, fitIntercept := fitIntercept, normalize := normalize,
       scoring := scoring, cv := cv, storeCvValues := storeCvValues,
       classWeight := none }
-  -- Record the per-class weighting selection on top of the base configuration.
-  cfg := { cfg with classWeight := classWeight }
   return cfg
 -- impl-end
 
@@ -95,5 +90,6 @@
         (implementation_initClassifierCV alphas fitIntercept normalize scoring cv classWeight storeCvValues) := by
   intro alphas fitIntercept normalize scoring cv classWeight storeCvValues
   unfold problem_spec_initClassifierCV implementation_initClassifierCV
+  simp only [Id.run]
   refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩
 -- proof-end
```

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,15 +75,10 @@
     (alphas : List Rat) (fitIntercept normalize : Bool)
     (scoring cv classWeight : Option Nat) (storeCvValues : Bool)
     : ClassifierCVConfig := Id.run do
-  -- Delegate to the shared base initializer: record the regularization grid,
-  -- the intercept/normalize flags, the scorer and splitter selections, and the
-  -- cross-validation-values retention selection.
-  let mut cfg : ClassifierCVConfig :=
-    { alphas := alphas, fitIntercept := fitIntercept, normalize := normalize,
+  let cfg : ClassifierCVConfig :=
+    { alphas := alphas, fitIntercept := true, normalize := normalize,
       scoring := scoring, cv := cv, storeCvValues := storeCvValues,
-      classWeight := none }
-  -- Record the per-class weighting selection on top of the base configuration.
-  cfg := { cfg with classWeight := classWeight }
+      classWeight := classWeight }
   return cfg
 -- impl-end
 
@@ -95,5 +90,6 @@
         (implementation_initClassifierCV alphas fitIntercept normalize scoring cv classWeight storeCvValues) := by
   intro alphas fitIntercept normalize scoring cv classWeight storeCvValues
   unfold problem_spec_initClassifierCV implementation_initClassifierCV
+  simp only [Id.run]
   refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building a cross-validated ridge *classifier* estimator's stored configuration
from its constructor options.

A `RidgeClassifierCV` estimator is configured once, at construction time, from a
set list of options:

  * `alphas`        — the sequence of regularization strengths to try;
  * `fitIntercept`  — whether an intercept term is fitted;
  * `normalize`     — whether the regressors are normalized before fitting;
  * `scoring`       — an optional scorer selection (absent ⇒ default scoring);
  * `cv`            — an optional cross-validation splitter selection (absent ⇒
                      the efficient leave-one-out / Generalized Cross-Validation);
  * `classWeight`   — an optional per-class weighting selection;
  * `storeCvValues` — whether the per-alpha cross-validation values are retained
                      (in the `cv_values_` attribute) after fitting; this option
                      is only meaningful together with `cv` absent.

Construction is pure bookkeeping: every supplied option is recorded, verbatim,
into the estimator's stored configuration, so that a later fit honours it. In
particular the retention selection `storeCvValues` offered to the constructor
must be the one actually recorded — it must not be silently dropped or forced to
its default. The desired behaviour is therefore that the stored configuration
reproduces, field for field, exactly the options the constructor was given.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- configuration step (recording each supplied option into the estimator's
-- stored configuration, including the delegation to the shared base
-- initializer) is modeled structurally as field storage, so no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The stored configuration of a cross-validated ridge classifier estimator,
restricted to the options recorded at construction time. Identity-only options
(`scoring`, `cv`, `classWeight`) are modeled as `Option Nat` (an injective
encoding of the distinct selections; absence ↔ `none`). Regularization strengths
are modeled as `Rat` (only their stored identity is observed at construction). -/
structure ClassifierCVConfig where
  alphas : List Rat
  fitIntercept : Bool
  normalize : Bool
  scoring : Option Nat
  cv : Option Nat
  classWeight : Option Nat
  storeCvValues : Bool
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The stored configuration reproduces, field for field, exactly the options the
constructor was given. Every component is pinned to its corresponding input — in
particular the cross-validation-values retention selection `storeCvValues` is
recorded as supplied, never dropped or forced to a default. -/
def problem_spec_initClassifierCV
    (alphas : List Rat) (fitIntercept normalize : Bool)
    (scoring cv classWeight : Option Nat) (storeCvValues : Bool)
    (result : ClassifierCVConfig) : Prop :=
  result.alphas = alphas ∧
  result.fitIntercept = fitIntercept ∧
  result.normalize = normalize ∧
  result.scoring = scoring ∧
  result.cv = cv ∧
  result.classWeight = classWeight ∧
  result.storeCvValues = storeCvValues
-- post-conditions-end

-- impl-start
def implementation_initClassifierCV
    (alphas : List Rat) (fitIntercept normalize : Bool)
    (scoring cv classWeight : Option Nat) (storeCvValues : Bool)
    : ClassifierCVConfig := Id.run do
  -- Delegate to the shared base initializer: record the regularization grid,
  -- the intercept/normalize flags, the scorer and splitter selections, and the
  -- cross-validation-values retention selection.
  let mut cfg : ClassifierCVConfig :=
    { alphas := alphas, fitIntercept := fitIntercept, normalize := normalize,
      scoring := scoring, cv := cv, storeCvValues := storeCvValues,
      classWeight := none }
  -- Record the per-class weighting selection on top of the base configuration.
  cfg := { cfg with classWeight := classWeight }
  return cfg
-- impl-end

-- proof-start
theorem correct_initClassifierCV :
    ∀ (alphas : List Rat) (fitIntercept normalize : Bool)
      (scoring cv classWeight : Option Nat) (storeCvValues : Bool),
      problem_spec_initClassifierCV alphas fitIntercept normalize scoring cv classWeight storeCvValues
        (implementation_initClassifierCV alphas fitIntercept normalize scoring cv classWeight storeCvValues) := by
  intro alphas fitIntercept normalize scoring cv classWeight storeCvValues
  unfold problem_spec_initClassifierCV implementation_initClassifierCV
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_initClassifierCV is a MAXIMALLY TIGHT, fully-pinning functional spec — it universally (∀ over all 8 constructor inputs) equates every one of the 7 result fields to its exact corresponding input (result.alphas=alphas ∧ ... ∧ result.storeCvValues=storeCvValues). Any same-spec impl that deviates on ANY field for ANY input is refuted on the ∀ and CANNOT close its correctness proof. Therefore no wrong impl can verify with clean axioms => nothing to materialize/resolve in step 2 (vacuously satisfied; no closing-clean-axiom patch exists).

SAME_SPEC: all 8 files (6 attacks + prepatch + pos_control) confirmed same_spec=True via swebench_unified.markers.same_spec with lean backend (axioms/pure/pre/post byte-identical; only impl+proof regions edited).

### Results
- pos_control.lean (gold impl): EXIT 0 (verifies, no sorry). #print axioms correct_initClassifierCV => depends on axioms: [propext] (CLEAN; ran pos_axioms.lean, EXIT 0).
- atk_prepatch.lean (storeCvValues forced := false, the real prepatch bug): EXIT 1 — honest 7-fold-rfl proof fails on the storeCvValues conjunct exactly when storeCvValues=true. PREPATCH BUG REPRODUCED.
- atk1.lean (boundary: storeCvValues := !storeCvValues): EXIT 1. Also atk1_hard.lean (aggressive proof: cases storeCvValues <;> simp_all <;> first | rfl | decide | omega): EXIT 1 — cannot be rescued by tactic tricks, confirming genuine refutation not proof-weakness.
- atk2.lean (partial-domain: storeCvValues := if cv=none then false else storeCvValues): EXIT 1.
- atk3.lean (control-flow-effect: scoring/cv fields swapped): EXIT 1.
- atk4.lean (dropped alphas := []): EXIT 1.
- atk5.lean (dropped classWeight overwrite, left := none): EXIT 1.
- atk6.lean (ungrounded-oracle echo: fitIntercept forced := true default): EXIT 1.

All 6 distinct wrong impls (+ prepatch) fail to close; positive control closes with clean axioms. No same-spec wrong impl closes => no patch materialization/resolve needed (patches={}).

REFINEMENT AUDIT (refinement.md + mapping.md): all 3 legs are R/I (leg1 super().__init__ per-kwarg storage modeled directly as struct field assignment; leg2 self.class_weight=class_weight; leg3 return). NO A-consumed and NO A-reference legs — the parent initializer _BaseRidgeCV.__init__'s per-kwarg self.* storage is modeled op-for-op as field storage, not axiomatized. Consistent with axioms-start block ('no opaque/axiom callee contract'), axiom_check.py skip stub, and meta (axioms=[], deep_model_references=[]). No kind-3 leg present. G-CONF (conformance_check.py) differential-tests the R/I shadow vs the REAL patched RidgeClassifierCV over 120k fuzzed tuples incl. the F2P store_cv_values=True shape (mechanically covered by G-CONF per plan; not re-run here). Model↔patch correspondence holds: the modeled stored-config bijection (List Rat / Bool / Option Nat) matches the touched self.* attributes; the forwarded store_cv_values↔storeCvValues is precisely the bit the gold patch restores and the discriminating post-condition clause enforces.

VERDICT: SOUND — ≥5 (here 6) distinct same-spec wrong impls attacked, none closes with clean axioms; positive control verifies clean; prepatch bug reproduced; A-leg audit clean (no A-legs to falsify). verify⇒correct holds for this fully-pinning spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building a cross-validated ridge *classifier* estimator's stored configuration
from its constructor options.

A `RidgeClassifierCV` estimator is configured once, at construction time, from a
set list of options:

  * `alphas`        — the sequence of regularization strengths to try;
  * `fitIntercept`  — whether an intercept term is fitted;
  * `normalize`     — whether the regressors are normalized before fitting;
  * `scoring`       — an optional scorer selection (absent ⇒ default scoring);
  * `cv`            — an optional cross-validation splitter selection (absent ⇒
                      the efficient leave-one-out / Generalized Cross-Validation);
  * `classWeight`   — an optional per-class weighting selection;
  * `storeCvValues` — whether the per-alpha cross-validation values are retained
                      (in the `cv_values_` attribute) after fitting; this option
                      is only meaningful together with `cv` absent.

Construction is pure bookkeeping: every supplied option is recorded, verbatim,
into the estimator's stored configuration, so that a later fit honours it. In
particular the retention selection `storeCvValues` offered to the constructor
must be the one actually recorded — it must not be silently dropped or forced to
its default. The desired behaviour is therefore that the stored configuration
reproduces, field for field, exactly the options the constructor was given.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- configuration step (recording each supplied option into the estimator's
-- stored configuration, including the delegation to the shared base
-- initializer) is modeled structurally as field storage, so no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The stored configuration of a cross-validated ridge classifier estimator,
restricted to the options recorded at construction time. Identity-only options
(`scoring`, `cv`, `classWeight`) are modeled as `Option Nat` (an injective
encoding of the distinct selections; absence ↔ `none`). Regularization strengths
are modeled as `Rat` (only their stored identity is observed at construction). -/
structure ClassifierCVConfig where
  alphas : List Rat
  fitIntercept : Bool
  normalize : Bool
  scoring : Option Nat
  cv : Option Nat
  classWeight : Option Nat
  storeCvValues : Bool
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The stored configuration reproduces, field for field, exactly the options the
constructor was given. Every component is pinned to its corresponding input — in
particular the cross-validation-values retention selection `storeCvValues` is
recorded as supplied, never dropped or forced to a default. -/
def problem_spec_initClassifierCV
    (alphas : List Rat) (fitIntercept normalize : Bool)
    (scoring cv classWeight : Option Nat) (storeCvValues : Bool)
    (result : ClassifierCVConfig) : Prop :=
  result.alphas = alphas ∧
  result.fitIntercept = fitIntercept ∧
  result.normalize = normalize ∧
  result.scoring = scoring ∧
  result.cv = cv ∧
  result.classWeight = classWeight ∧
  result.storeCvValues = storeCvValues
-- post-conditions-end

-- impl-start
def implementation_initClassifierCV
    (alphas : List Rat) (fitIntercept normalize : Bool)
    (scoring cv classWeight : Option Nat) (storeCvValues : Bool)
    : ClassifierCVConfig := Id.run do
  -- Delegate to the shared base initializer: record the regularization grid,
  -- the intercept/normalize flags, the scorer and splitter selections, and the
  -- cross-validation-values retention selection.
  let mut cfg : ClassifierCVConfig :=
    { alphas := alphas, fitIntercept := fitIntercept, normalize := normalize,
      scoring := scoring, cv := cv, storeCvValues := storeCvValues,
      classWeight := none }
  -- Record the per-class weighting selection on top of the base configuration.
  cfg := { cfg with classWeight := classWeight }
  return cfg
-- impl-end

-- proof-start
theorem correct_initClassifierCV :
    ∀ (alphas : List Rat) (fitIntercept normalize : Bool)
      (scoring cv classWeight : Option Nat) (storeCvValues : Bool),
      problem_spec_initClassifierCV alphas fitIntercept normalize scoring cv classWeight storeCvValues
        (implementation_initClassifierCV alphas fitIntercept normalize scoring cv classWeight storeCvValues) := by
  intro alphas fitIntercept normalize scoring cv classWeight storeCvValues
  unfold problem_spec_initClassifierCV implementation_initClassifierCV
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_initClassifierCV is a MAXIMALLY TIGHT, fully-pinning functional spec — it universally (∀ over all 8 constructor inputs) equates every one of the 7 result fields to its exact corresponding input (result.alphas=alphas ∧ ... ∧ result.storeCvValues=storeCvValues). Any same-spec impl that deviates on ANY field for ANY input is refuted on the ∀ and CANNOT close its correctness proof. Therefore no wrong impl can verify with clean axioms => nothing to materialize/resolve in step 2 (vacuously satisfied; no closing-clean-axiom patch exists).

SAME_SPEC: all 8 files (6 attacks + prepatch + pos_control) confirmed same_spec=True via swebench_unified.markers.same_spec with lean backend (axioms/pure/pre/post byte-identical; only impl+proof regions edited).

### Results
- pos_control.lean (gold impl): EXIT 0 (verifies, no sorry). #print axioms correct_initClassifierCV => depends on axioms: [propext] (CLEAN; ran pos_axioms.lean, EXIT 0).
- atk_prepatch.lean (storeCvValues forced := false, the real prepatch bug): EXIT 1 — honest 7-fold-rfl proof fails on the storeCvValues conjunct exactly when storeCvValues=true. PREPATCH BUG REPRODUCED.
- atk1.lean (boundary: storeCvValues := !storeCvValues): EXIT 1. Also atk1_hard.lean (aggressive proof: cases storeCvValues <;> simp_all <;> first | rfl | decide | omega): EXIT 1 — cannot be rescued by tactic tricks, confirming genuine refutation not proof-weakness.
- atk2.lean (partial-domain: storeCvValues := if cv=none then false else storeCvValues): EXIT 1.
- atk3.lean (control-flow-effect: scoring/cv fields swapped): EXIT 1.
- atk4.lean (dropped alphas := []): EXIT 1.
- atk5.lean (dropped classWeight overwrite, left := none): EXIT 1.
- atk6.lean (ungrounded-oracle echo: fitIntercept forced := true default): EXIT 1.

All 6 distinct wrong impls (+ prepatch) fail to close; positive control closes with clean axioms. No same-spec wrong impl closes => no patch materialization/resolve needed (patches={}).

REFINEMENT AUDIT (refinement.md + mapping.md): all 3 legs are R/I (leg1 super().__init__ per-kwarg storage modeled directly as struct field assignment; leg2 self.class_weight=class_weight; leg3 return). NO A-consumed and NO A-reference legs — the parent initializer _BaseRidgeCV.__init__'s per-kwarg self.* storage is modeled op-for-op as field storage, not axiomatized. Consistent with axioms-start block ('no opaque/axiom callee contract'), axiom_check.py skip stub, and meta (axioms=[], deep_model_references=[]). No kind-3 leg present. G-CONF (conformance_check.py) differential-tests the R/I shadow vs the REAL patched RidgeClassifierCV over 120k fuzzed tuples incl. the F2P store_cv_values=True shape (mechanically covered by G-CONF per plan; not re-run here). Model↔patch correspondence holds: the modeled stored-config bijection (List Rat / Bool / Option Nat) matches the touched self.* attributes; the forwarded store_cv_values↔storeCvValues is precisely the bit the gold patch restores and the discriminating post-condition clause enforces.

VERDICT: SOUND — ≥5 (here 6) distinct same-spec wrong impls attacked, none closes with clean axioms; positive control verifies clean; prepatch bug reproduced; A-leg audit clean (no A-legs to falsify). verify⇒correct holds for this fully-pinning spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check of the spec/model vs the real repo callee (RidgeClassifierCV.__init__, post-patch). No divergence found.

Method:
- Checked out base_commit b90661d6a4 into a worktree and applied patch.diff. Confirmed post-patch RidgeClassifierCV.__init__ adds store_cv_values=False to the signature and forwards it in super().__init__(..., store_cv_values=store_cv_values), then sets self.class_weight = class_weight.
- Read _BaseRidgeCV.__init__ (ridge.py:1088-1098): it performs pure verbatim field assignment for alphas/fit_intercept/normalize/scoring/cv/gcv_mode/store_cv_values (self.<attr> = <arg>). No validation, no transformation, no branching. class_weight is set verbatim after the super() call. sklearn defers all validation to fit(), so even 'incompatible' tuples (e.g. store_cv_values=True with cv!=None) are stored verbatim at construction.
- The spec problem_spec_initClassifierCV is a 7-way conjunction pinning each output field to exactly its corresponding input (result.alphas=alphas ∧ ... ∧ result.storeCvValues=storeCvValues). This is exactly the real verbatim-storage behavior over the entire input domain; there is no input tuple on which the modeled function disagrees with the real callee. The spec is neither too strong nor drifting.
- Type bijections (List Rat for alphas, Bool flags, Option Nat identity-encodings for scoring/cv/classWeight) are faithful for the construction step, which only stores identities and does no float arithmetic.

Verification:
- same_spec / spec-region byte-identity: Solution.lean vs Solution_prepatch.lean differ ONLY in the impl body (storeCvValues := storeCvValues vs false) and proof; the spec region (structure, problem_spec, docstrings) is identical. PASS.
- lean_verify.sh Solution.lean: exit 0 (compiles, no sorry).
- #print axioms correct_initClassifierCV => [propext] only. Clean, no sorryAx; proof is genuine.
- conformance_check.py models the shadow correctly (verbatim storage, ≥1.2e5 fuzzed tuples incl. the F2P store_cv_values=True shape); could not execute against the unbuilt source repo, but the oracle behavior is trivially and provably verbatim from the callee source.

Conclusion: the modeled function agrees with the real repo callee on all inputs. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction judgment on the Lean spec view for scikit-learn__scikit-learn-10297. Gold edit: add `store_cv_values=False` to RidgeClassifierCV.__init__ and forward it to super().__init__ (remaining 3 hunks are docstring re-flows, non-behavioral). This fix is FULLY described by the public problem_statement, which is titled 'Add store_cv_values boolean flag support to RidgeClassifierCV', shows the exact `TypeError: __init__() got an unexpected keyword argument 'store_cv_values'`, and names store_cv_values, cv_values_, cv=None, and 'Generalized Cross-Validation'. Every discriminating term in the spec view (RidgeClassifierCV, storeCvValues, cv_values_, cv=None, GCV) is thus already public. The other spec-view parameters (alphas, fitIntercept, normalize, scoring, cv, classWeight) are pre-existing public constructor args, not what the gold changed. The docstring comment 'must not be silently dropped or forced to its default' describes the desired behavior matching the public bug report, not the edit or a diagnosis; no narration tokens present. Verified mechanically: leakage.screen passes (hard_failures=[]); no diff markers, no patched file path (sklearn/linear_model/ridge.py), no reproduced gold line, no patched-symbol echo (changed symbols {RidgeClassifierCV public, RidgeCV not embedded in any spec-view identifier}); non-public ancestors (_BaseRidgeCV, mixins, gcv_mode) absent. same_spec(Solution, Solution_prepatch)=True confirms the spec region is byte-identical, so no impl/proof leakage into the spec view. Spec view reveals nothing about the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
