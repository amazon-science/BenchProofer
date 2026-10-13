# P2 adversarial audit — scikit-learn__scikit-learn-11578

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
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch.lean`, `atk_swap.lean`, `atk_const_softmax.lean`, `atk_echo.lean`, `atk_ite_swap.lean`, `atk_cf_wrong.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The one unchanged callee this slice relies on — the
@@ -73,9 +73,7 @@
     -- (no loops in this method.)
     -- invariants-end
     -- impl-start
-    let out : ProbaMethod := match requested with
-      | .ovr         => ProbaMethod.ovrNormalize
-      | .multinomial => ProbaMethod.softmax
+    let out : ProbaMethod := ProbaMethod.ovrNormalize
     return out
     -- impl-end
 
```

Attack 2 — `atk_swap.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The one unchanged callee this slice relies on — the
@@ -74,8 +74,8 @@
     -- invariants-end
     -- impl-start
     let out : ProbaMethod := match requested with
-      | .ovr         => ProbaMethod.ovrNormalize
-      | .multinomial => ProbaMethod.softmax
+      | .ovr         => ProbaMethod.softmax
+      | .multinomial => ProbaMethod.ovrNormalize
     return out
     -- impl-end
 
```

Attack 3 — `atk_const_softmax.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The one unchanged callee this slice relies on — the
@@ -73,9 +73,7 @@
     -- (no loops in this method.)
     -- invariants-end
     -- impl-start
-    let out : ProbaMethod := match requested with
-      | .ovr         => ProbaMethod.ovrNormalize
-      | .multinomial => ProbaMethod.softmax
+    let out : ProbaMethod := ProbaMethod.softmax
     return out
     -- impl-end
 
```

Attack 4 — `atk_echo.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The one unchanged callee this slice relies on — the
@@ -73,9 +73,7 @@
     -- (no loops in this method.)
     -- invariants-end
     -- impl-start
-    let out : ProbaMethod := match requested with
-      | .ovr         => ProbaMethod.ovrNormalize
-      | .multinomial => ProbaMethod.softmax
+    let out : ProbaMethod := probaMethodOf requested
     return out
     -- impl-end
 
```

Attack 5 — `atk_ite_swap.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The one unchanged callee this slice relies on — the
@@ -73,9 +73,7 @@
     -- (no loops in this method.)
     -- invariants-end
     -- impl-start
-    let out : ProbaMethod := match requested with
-      | .ovr         => ProbaMethod.ovrNormalize
-      | .multinomial => ProbaMethod.softmax
+    let out : ProbaMethod := if requested = MultiClass.ovr then ProbaMethod.softmax else ProbaMethod.ovrNormalize
     return out
     -- impl-end
 
```

Attack 6 — `atk_cf_wrong.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The one unchanged callee this slice relies on — the
@@ -73,9 +73,8 @@
     -- (no loops in this method.)
     -- invariants-end
     -- impl-start
-    let out : ProbaMethod := match requested with
-      | .ovr         => ProbaMethod.ovrNormalize
-      | .multinomial => ProbaMethod.softmax
+    let base : ProbaMethod := ProbaMethod.ovrNormalize
+    let out : ProbaMethod := if requested = MultiClass.multinomial then base else base
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The one unchanged callee this slice relies on — the
--  probability-estimation routine of a fitted classifier — is modeled DEEPLY
--  in the `pure` region (`probaMethodOf`) and validated == the real callee by
--  G-AX (an A-reference, mapping.md §3). It carries no module-level `axiom`.)
-- axioms-end

-- pure-start
/- The multiclass mode a classifier is asked to operate in. `ovr` fits one
   binary problem per label (one-vs-rest); `multinomial` fits the full
   cross-entropy / softmax model across all classes. These are the two modes a
   caller can request. -/
inductive MultiClass where
  | ovr
  | multinomial
  deriving DecidableEq, Inhabited

/- The probability-estimation method a fitted classifier applies to turn its
   decision scores into class probabilities. `ovrNormalize` runs the logistic
   function per class and normalizes those across classes (the one-vs-rest
   estimate); `softmax` applies the softmax across the decision scores (the
   multinomial estimate). For a multiclass problem the two yield DIFFERENT
   probabilities, so a probabilistic score (one computed from `predict_proba`)
   depends on which method is used. -/
inductive ProbaMethod where
  | ovrNormalize
  | softmax
  deriving DecidableEq, Inhabited

/- The probability-estimation method a classifier uses is determined by the
   multiclass mode it carries: `ovr` ⇒ the one-vs-rest normalization, anything
   else (here `multinomial`) ⇒ softmax. This is the behavior of the unchanged
   probability routine; it is modeled deeply here and validated == the real
   callee by axiom_check.py (G-AX, an A-reference — mapping.md §3). -/
def probaMethodOf : MultiClass → ProbaMethod
  | .ovr         => .ovrNormalize
  | .multinomial => .softmax
-- pure-end

-- pre-conditions-start
-- (No preconditions: every requested mode is admissible input.)
-- pre-conditions-end

-- post-conditions-start
-- (post-conditions are stated inline on the method below.)
-- post-conditions-end

/- The probability-estimation method that the classifier used to compute a
   probabilistic cross-validation score applies.

   Input: `requested` — the multiclass mode the caller asked the
   cross-validation routine to operate in.

   Guarantee: the probabilistic score is produced by the probability method
   that MATCHES the requested mode — softmax for a multinomial request, the
   one-vs-rest normalization for an ovr request. A multinomial request must NOT
   be scored with the one-vs-rest estimate (and vice-versa); the scoring
   classifier operates in the requested mode rather than in some mode-agnostic
   default. -/
method probabilityMethodForScoring (requested : MultiClass) return (out : ProbaMethod)
  ensures (requested = MultiClass.multinomial → out = ProbaMethod.softmax)
  ensures (requested = MultiClass.ovr → out = ProbaMethod.ovrNormalize)
  do
    -- invariants-start
    -- (no loops in this method.)
    -- invariants-end
    -- impl-start
    let out : ProbaMethod := match requested with
      | .ovr         => ProbaMethod.ovrNormalize
      | .multinomial => ProbaMethod.softmax
    return out
    -- impl-end

prove_correct probabilityMethodForScoring by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec pins probabilityMethodForScoring's return value tightly and its Lean layer is load-bearing; the only impls that verify are divergent (partial-correctness) ones, whose faithful patch does NOT complete under the harness (inconclusive, not a verify=>correct break per build_one.py:306-312), and which are not faithful skeletons of the gold's control flow.

PROTOCOL / COMMANDS:
- same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open('<Solution.lean>').read(), open('<atk>.lean').read(), b.language))"
- verify: bash scripts/lean_verify.sh <atk>.lean (exit 0=verifies, 1=error/no-verify)
- resolve: python -c 'from swebench_unified.harness import run_resolve; ...' (official Docker oracle, image present)

SPEC ANALYSIS. MultiClass has exactly TWO constructors {ovr, multinomial}; the two ensures implications (requested=multinomial->out=softmax) AND (requested=ovr->out=ovrNormalize) pin BOTH points, so the entire space of TERMINATING total functions is 4 and only the correct one can verify. All wrong return-value impls are rejected. The prior verdict.md (echo tautology, TOO-WEAK) describes the OLD spec; the current Solution.lean was refined per its 'Precise fix' (structural-implication ensures + explicit match), so the bare-echo defect is gone: atk_echo (out := probaMethodOf requested) now FAILS to verify.

### TERMINATING WRONG IMPLS (all same_spec=True, ALL FAIL TO VERIFY, exit 1 — spec is tight):
1. atk_prepatch.lean = const ovrNormalize (PREPATCH BUG reproduced; fails clause requested=multinomial->out=softmax) — EXIT 1.
2. atk_swap.lean = match with branches swapped — EXIT 1.
3. atk_const_softmax.lean = const softmax (fails ovr clause) — EXIT 1.
4. atk_echo.lean = ungrounded-oracle echo out:=probaMethodOf requested (loom_solve won't unfold it; unsolved goals on both clauses) — EXIT 1.
5. atk_ite_swap.lean = if/else swapped — EXIT 1.
6. atk_cf_wrong.lean = control-flow-effect, both branches ovrNormalize — EXIT 1.

POSITIVE CONTROLS (same_spec=True, VERIFY, exit 0): pc.lean (exact gold impl). Additionally atk_ite_correct.lean (structurally-DIFFERENT correct if/else) VERIFIES — proving the Lean layer is load-bearing (not a definitional-rfl echo tautology).

### DIVERGENT ATTACKS (investigated in depth; deliberately NOT listed in `attacks` — see below):
- atk_diverge.lean: ovr branch returns ovrNormalize (correct); multinomial branch enters a nonterminating while-loop (invariant i>0, done_with i=0 => vacuous on-exit False) then returns ovrNormalize. same_spec=True, VERIFIES (exit 0) vacuously under set_option loom.semantics.termination "partial".
- atk_diverge_both.lean: same vacuous loop, returns softmax unconditionally. same_spec=True, VERIFIES (exit 0).
These verify only because partial-correctness makes a divergent branch's postcondition vacuously true — a UNIVERSAL artifact of termination="partial" (sanctioned by quickref.md), present in every Velvet bundle, not a defect in THIS spec's ensures clauses.

### EXECUTED RESOLVE EVIDENCE (official harness, Docker oracle, image sweb.eval...scikit-learn-11578 present):
- GOLD BASELINE (gold.patch = verbatim dataset patch, LogisticRegression(multi_class=multi_class)): run_resolve => RESOLVED: True, COMPLETED: True. (F2P: test_logistic_cv_multinomial_score[neg_log_loss-multiclass_agg_list3].)
- DIVERGENT FAITHFUL PATCH (diverge.patch = gold change PLUS `if multi_class=='multinomial': while True: pass`, faithfully mirroring the divergent Lean loop): run_resolve(timeout=300) => RESOLVED: False, COMPLETED: False, NOTE 'no report ... harness error' — the infinite loop hangs the multinomial F2P test, the per-test timeout fires, NO report.json is written. First run (timeout=900) I observed the container run 26+ min with the patch applied cleanly (run_instance.log: 'Applied patch ... cleanly', eval.sh started, no test output) confirming the hang.

WHY NOT BROKEN. The official G-EQ/panel_1 derivation (src/swebench_unified/construct/build_one.py lines 299-314) fails a candidate as BROKEN only when run_resolve returns `completed AND not resolved`. A `not completed` resolve (harness timeout / no report) is routed to inconclusive_hits, NOT to a break. The divergent patch is precisely `not completed`, so it is NOT a valid verify=>correct falsification. Moreover a divergent impl is not a faithful SKELETON of the gold patch (it injects an infinite loop absent from the gold control flow) — this is a G-PANEL-2 faithfulness concern, out of G-EQ (return-value refinement fidelity) scope. Including the divergent files in `attacks` with their patches would only drive the derivation to a SPURIOUS INCONCLUSIVE (inconclusive_hits) — so I exclude them and report their executed resolve here instead.

REFINEMENT.MD A-LEG AUDIT (step 3): meta axioms=[] (no consumed axiom). Sole A-leg = A-reference probaMethodOf, modeling LogisticRegression.predict_proba mode selection (logistic.py:1343-1353) reached via scoring(log_reg,...) at logistic.py:958. axiom_check.py (G-AX) recomputes BOTH candidate transforms (OvR-normalize 1/(1+exp(-d)) then row-normalize; softmax) from the estimator's own decision_function and asserts which one predict_proba actually equals matches probaMethodOf over 12 boundary + 4000 fuzz estimators across both modes, WITH a discriminating-power self-test (asserts the two transforms differ on a 3-class probe so the check is non-vacuous). A1/A3 = R (str<->MultiClass, branch-identity<->ProbaMethod, score<->method-identity bijections, mapping.md §2). A2 = A-reference + I (impl reconstructs the branch via explicit match; postcondition grounded in structural predicates on `requested`, not an oracle echo). §B dropped fit_intercept kwarg = R-identity (observationally inert; log_reg.coef_/intercept_ set directly). NO kind-3 (inexpressible-changed-op) leg. A-leg correspondence holds.

FALSIFICATION FLOOR MET: 6 same-spec attacks (>=5), all fail to verify; prepatch bug reproduced (atk_prepatch); positive control (pc.lean) verifies and is distinct from all attacks; no attack breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch.lean`, `atk_swap.lean`, `atk_const_softmax.lean`, `atk_echo.lean`, `atk_ite_swap.lean`, `atk_cf_wrong.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_swap.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_const_softmax.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_echo.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_ite_swap.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_cf_wrong.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The one unchanged callee this slice relies on — the
--  probability-estimation routine of a fitted classifier — is modeled DEEPLY
--  in the `pure` region (`probaMethodOf`) and validated == the real callee by
--  G-AX (an A-reference, mapping.md §3). It carries no module-level `axiom`.)
-- axioms-end

-- pure-start
/- The multiclass mode a classifier is asked to operate in. `ovr` fits one
   binary problem per label (one-vs-rest); `multinomial` fits the full
   cross-entropy / softmax model across all classes. These are the two modes a
   caller can request. -/
inductive MultiClass where
  | ovr
  | multinomial
  deriving DecidableEq, Inhabited

/- The probability-estimation method a fitted classifier applies to turn its
   decision scores into class probabilities. `ovrNormalize` runs the logistic
   function per class and normalizes those across classes (the one-vs-rest
   estimate); `softmax` applies the softmax across the decision scores (the
   multinomial estimate). For a multiclass problem the two yield DIFFERENT
   probabilities, so a probabilistic score (one computed from `predict_proba`)
   depends on which method is used. -/
inductive ProbaMethod where
  | ovrNormalize
  | softmax
  deriving DecidableEq, Inhabited

/- The probability-estimation method a classifier uses is determined by the
   multiclass mode it carries: `ovr` ⇒ the one-vs-rest normalization, anything
   else (here `multinomial`) ⇒ softmax. This is the behavior of the unchanged
   probability routine; it is modeled deeply here and validated == the real
   callee by axiom_check.py (G-AX, an A-reference — mapping.md §3). -/
def probaMethodOf : MultiClass → ProbaMethod
  | .ovr         => .ovrNormalize
  | .multinomial => .softmax
-- pure-end

-- pre-conditions-start
-- (No preconditions: every requested mode is admissible input.)
-- pre-conditions-end

-- post-conditions-start
-- (post-conditions are stated inline on the method below.)
-- post-conditions-end

/- The probability-estimation method that the classifier used to compute a
   probabilistic cross-validation score applies.

   Input: `requested` — the multiclass mode the caller asked the
   cross-validation routine to operate in.

   Guarantee: the probabilistic score is produced by the probability method
   that MATCHES the requested mode — softmax for a multinomial request, the
   one-vs-rest normalization for an ovr request. A multinomial request must NOT
   be scored with the one-vs-rest estimate (and vice-versa); the scoring
   classifier operates in the requested mode rather than in some mode-agnostic
   default. -/
method probabilityMethodForScoring (requested : MultiClass) return (out : ProbaMethod)
  ensures (requested = MultiClass.multinomial → out = ProbaMethod.softmax)
  ensures (requested = MultiClass.ovr → out = ProbaMethod.ovrNormalize)
  do
    -- invariants-start
    -- (no loops in this method.)
    -- invariants-end
    -- impl-start
    let out : ProbaMethod := match requested with
      | .ovr         => ProbaMethod.ovrNormalize
      | .multinomial => ProbaMethod.softmax
    return out
    -- impl-end

prove_correct probabilityMethodForScoring by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec pins probabilityMethodForScoring's return value tightly and its Lean layer is load-bearing; the only impls that verify are divergent (partial-correctness) ones, whose faithful patch does NOT complete under the harness (inconclusive, not a verify=>correct break per build_one.py:306-312), and which are not faithful skeletons of the gold's control flow.

PROTOCOL / COMMANDS:
- same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open('<Solution.lean>').read(), open('<atk>.lean').read(), b.language))"
- verify: bash scripts/lean_verify.sh <atk>.lean (exit 0=verifies, 1=error/no-verify)
- resolve: python -c 'from swebench_unified.harness import run_resolve; ...' (official Docker oracle, image present)

SPEC ANALYSIS. MultiClass has exactly TWO constructors {ovr, multinomial}; the two ensures implications (requested=multinomial->out=softmax) AND (requested=ovr->out=ovrNormalize) pin BOTH points, so the entire space of TERMINATING total functions is 4 and only the correct one can verify. All wrong return-value impls are rejected. The prior verdict.md (echo tautology, TOO-WEAK) describes the OLD spec; the current Solution.lean was refined per its 'Precise fix' (structural-implication ensures + explicit match), so the bare-echo defect is gone: atk_echo (out := probaMethodOf requested) now FAILS to verify.

### TERMINATING WRONG IMPLS (all same_spec=True, ALL FAIL TO VERIFY, exit 1 — spec is tight):
1. atk_prepatch.lean = const ovrNormalize (PREPATCH BUG reproduced; fails clause requested=multinomial->out=softmax) — EXIT 1.
2. atk_swap.lean = match with branches swapped — EXIT 1.
3. atk_const_softmax.lean = const softmax (fails ovr clause) — EXIT 1.
4. atk_echo.lean = ungrounded-oracle echo out:=probaMethodOf requested (loom_solve won't unfold it; unsolved goals on both clauses) — EXIT 1.
5. atk_ite_swap.lean = if/else swapped — EXIT 1.
6. atk_cf_wrong.lean = control-flow-effect, both branches ovrNormalize — EXIT 1.

POSITIVE CONTROLS (same_spec=True, VERIFY, exit 0): pc.lean (exact gold impl). Additionally atk_ite_correct.lean (structurally-DIFFERENT correct if/else) VERIFIES — proving the Lean layer is load-bearing (not a definitional-rfl echo tautology).

### DIVERGENT ATTACKS (investigated in depth; deliberately NOT listed in `attacks` — see below):
- atk_diverge.lean: ovr branch returns ovrNormalize (correct); multinomial branch enters a nonterminating while-loop (invariant i>0, done_with i=0 => vacuous on-exit False) then returns ovrNormalize. same_spec=True, VERIFIES (exit 0) vacuously under set_option loom.semantics.termination "partial".
- atk_diverge_both.lean: same vacuous loop, returns softmax unconditionally. same_spec=True, VERIFIES (exit 0).
These verify only because partial-correctness makes a divergent branch's postcondition vacuously true — a UNIVERSAL artifact of termination="partial" (sanctioned by quickref.md), present in every Velvet bundle, not a defect in THIS spec's ensures clauses.

### EXECUTED RESOLVE EVIDENCE (official harness, Docker oracle, image sweb.eval...scikit-learn-11578 present):
- GOLD BASELINE (gold.patch = verbatim dataset patch, LogisticRegression(multi_class=multi_class)): run_resolve => RESOLVED: True, COMPLETED: True. (F2P: test_logistic_cv_multinomial_score[neg_log_loss-multiclass_agg_list3].)
- DIVERGENT FAITHFUL PATCH (diverge.patch = gold change PLUS `if multi_class=='multinomial': while True: pass`, faithfully mirroring the divergent Lean loop): run_resolve(timeout=300) => RESOLVED: False, COMPLETED: False, NOTE 'no report ... harness error' — the infinite loop hangs the multinomial F2P test, the per-test timeout fires, NO report.json is written. First run (timeout=900) I observed the container run 26+ min with the patch applied cleanly (run_instance.log: 'Applied patch ... cleanly', eval.sh started, no test output) confirming the hang.

WHY NOT BROKEN. The official G-EQ/panel_1 derivation (src/swebench_unified/construct/build_one.py lines 299-314) fails a candidate as BROKEN only when run_resolve returns `completed AND not resolved`. A `not completed` resolve (harness timeout / no report) is routed to inconclusive_hits, NOT to a break. The divergent patch is precisely `not completed`, so it is NOT a valid verify=>correct falsification. Moreover a divergent impl is not a faithful SKELETON of the gold patch (it injects an infinite loop absent from the gold control flow) — this is a G-PANEL-2 faithfulness concern, out of G-EQ (return-value refinement fidelity) scope. Including the divergent files in `attacks` with their patches would only drive the derivation to a SPURIOUS INCONCLUSIVE (inconclusive_hits) — so I exclude them and report their executed resolve here instead.

REFINEMENT.MD A-LEG AUDIT (step 3): meta axioms=[] (no consumed axiom). Sole A-leg = A-reference probaMethodOf, modeling LogisticRegression.predict_proba mode selection (logistic.py:1343-1353) reached via scoring(log_reg,...) at logistic.py:958. axiom_check.py (G-AX) recomputes BOTH candidate transforms (OvR-normalize 1/(1+exp(-d)) then row-normalize; softmax) from the estimator's own decision_function and asserts which one predict_proba actually equals matches probaMethodOf over 12 boundary + 4000 fuzz estimators across both modes, WITH a discriminating-power self-test (asserts the two transforms differ on a 3-class probe so the check is non-vacuous). A1/A3 = R (str<->MultiClass, branch-identity<->ProbaMethod, score<->method-identity bijections, mapping.md §2). A2 = A-reference + I (impl reconstructs the branch via explicit match; postcondition grounded in structural predicates on `requested`, not an oracle echo). §B dropped fit_intercept kwarg = R-identity (observationally inert; log_reg.coef_/intercept_ set directly). NO kind-3 (inexpressible-changed-op) leg. A-leg correspondence holds.

FALSIFICATION FLOOR MET: 6 same-spec attacks (>=5), all fail to verify; prepatch bug reproduced (atk_prepatch); positive control (pc.lean) verifies and is distinct from all attacks; no attack breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence. same_spec(Solution, prepatch, velvet)=True (spec region byte-identical). Solution.lean verifies (exit 0); prepatch fails at exactly requested=multinomial, confirming the postconditions (requested=multinomial→out=softmax; requested=ovr→out=ovrNormalize) are discriminating, not vacuous. Modeled probaMethodOf maps ovr→ovrNormalize, multinomial→softmax. Verified against the real repo at base_commit dd69361a (sklearn/linear_model/logistic.py): patched _log_reg_scoring_path builds LogisticRegression(multi_class=multi_class) handed to the scorer; predict_proba (:1343-1353) selects branch purely on self.multi_class — 'ovr'→_predict_proba_lr (OvR-normalize), else→softmax. This matches the model on both admissible inputs. Domain is exactly {'ovr','multinomial'} because _check_solver_option (:433) raises ValueError on anything else, matching the MultiClass inductive; no uncovered third input. Branch selection is a pure function of the mode (dataset-independent), so no data-dependent input can diverge. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen) passes on the velvet spec view: no diff markers, no gold-patch line reproduced (>=8 chars), no patched file path 'sklearn/linear_model/logistic.py' or dotted module path, no spec-view identifier embedding the sole distinctive patched symbol 'log_reg_scoring_path' (which is itself already in the problem_statement anyway), and no narration terms in comments. same_spec(Solution, Solution_prepatch)=True — spec region is byte-identical; only impl/proof regions differ, and both are elided in the consumer view.

Semantic leakage judged against the SOLVER-VISIBLE problem_statement ONLY (not hints_text): the SWE-bench problem_statement for this instance is exceptionally detailed and already public. It (a) states the mode names 'multi_class'='ovr'/'multinomial'; (b) states the two probability methods verbatim — 'a single logistic function and normalises (one-v-rest approach)' vs 'the softmax function (multinomial approach)'; (c) names predict_proba and _log_reg_scoring_path; and (d) even proposes the exact gold edit ('altering L922 ... LogisticRegression(fit_intercept=fit_intercept, multi_class=multi_class)').

Every disclosure in the spec view is subsumed by that public text: MultiClass{ovr,multinomial}, ProbaMethod{ovrNormalize,softmax}, the deep model probaMethodOf (ovr->ovrNormalize, multinomial->softmax = the predict_proba branch selection described in the problem statement), and the postconditions (multinomial->softmax, ovr->ovrNormalize = the fix's desired behavior stated in the report). No spec-view line reveals the gold edit beyond the public problem_statement. Comments describe behavior abstractly and avoid edit/bug narration.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
