# P2 adversarial audit — scikit-learn__scikit-learn-13142

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
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_2.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The routine that turns a set of fitted parameters
@@ -64,12 +64,10 @@
   ensures out = reportedLabels storedParams labelsFor
   do
     -- impl-start
-    -- Make the stored parameter set current FIRST, then compute the labels, so
-    -- the reported labels are derived from the stored parameters and agree with a
-    -- later separate query — not from the transient parameter set.
+    -- PREPATCH BUG: compute labels from transient params.
     let mut active := transientParams
+    let out := labelsFor active
     active := storedParams
-    let out := labelsFor active
     return out
     -- impl-end
 
```

Attack 2 — `atk_3.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The routine that turns a set of fitted parameters
@@ -64,13 +64,14 @@
   ensures out = reportedLabels storedParams labelsFor
   do
     -- impl-start
-    -- Make the stored parameter set current FIRST, then compute the labels, so
-    -- the reported labels are derived from the stored parameters and agree with a
-    -- later separate query — not from the transient parameter set.
-    let mut active := transientParams
-    active := storedParams
-    let out := labelsFor active
-    return out
+    -- PARTIAL-DOMAIN: correct value only when params coincide; diverge otherwise.
+    let mut active := storedParams
+    while (transientParams != storedParams)
+      invariant True
+      done_with (transientParams = storedParams)
+    do
+      active := active
+    return labelsFor active
     -- impl-end
 
 prove_correct finalizeLabels by
```

Attack 3 — `atk_4.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The routine that turns a set of fitted parameters
@@ -64,12 +64,8 @@
   ensures out = reportedLabels storedParams labelsFor
   do
     -- impl-start
-    -- Make the stored parameter set current FIRST, then compute the labels, so
-    -- the reported labels are derived from the stored parameters and agree with a
-    -- later separate query — not from the transient parameter set.
-    let mut active := transientParams
-    active := storedParams
-    let out := labelsFor active
+    -- CONTROL-FLOW / WRONG VALUE: return empty label list regardless of inputs.
+    let out : Labels := []
     return out
     -- impl-end
 
```

Attack 4 — `atk_5.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The routine that turns a set of fitted parameters
@@ -64,12 +64,8 @@
   ensures out = reportedLabels storedParams labelsFor
   do
     -- impl-start
-    -- Make the stored parameter set current FIRST, then compute the labels, so
-    -- the reported labels are derived from the stored parameters and agree with a
-    -- later separate query — not from the transient parameter set.
-    let mut active := transientParams
-    active := storedParams
-    let out := labelsFor active
+    -- UNGROUNDED ORACLE: return labels for an arbitrary fixed param set.
+    let out := labelsFor 0
     return out
     -- impl-end
 
```

Attack 5 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The routine that turns a set of fitted parameters
@@ -64,13 +64,14 @@
   ensures out = reportedLabels storedParams labelsFor
   do
     -- impl-start
-    -- Make the stored parameter set current FIRST, then compute the labels, so
-    -- the reported labels are derived from the stored parameters and agree with a
-    -- later separate query — not from the transient parameter set.
-    let mut active := transientParams
-    active := storedParams
-    let out := labelsFor active
-    return out
+    -- BOUNDARY DIVERGENCE: counter loop that never terminates; wrong return.
+    let mut n := storedParams + 1
+    while (n > 0)
+      invariant True
+      done_with (n = 0)
+    do
+      n := n + 1
+    return labelsFor transientParams
     -- impl-end
 
 prove_correct finalizeLabels by
```

Attack 6 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The routine that turns a set of fitted parameters
@@ -64,13 +64,8 @@
   ensures out = reportedLabels storedParams labelsFor
   do
     -- impl-start
-    -- Make the stored parameter set current FIRST, then compute the labels, so
-    -- the reported labels are derived from the stored parameters and agree with a
-    -- later separate query — not from the transient parameter set.
-    let mut active := transientParams
-    active := storedParams
-    let out := labelsFor active
-    return out
+    -- TERMINATING WRONG: report labels from the transient (leftover) params.
+    return labelsFor transientParams
     -- impl-end
 
 prove_correct finalizeLabels by
```

Attack 7 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The routine that turns a set of fitted parameters
@@ -64,11 +64,9 @@
   ensures out = reportedLabels storedParams labelsFor
   do
     -- impl-start
-    -- Make the stored parameter set current FIRST, then compute the labels, so
-    -- the reported labels are derived from the stored parameters and agree with a
-    -- later separate query — not from the transient parameter set.
-    let mut active := transientParams
-    active := storedParams
+    -- CONTROL-FLOW-EFFECT: order swapped so the transient set is in force.
+    let mut active := storedParams
+    active := transientParams
     let out := labelsFor active
     return out
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The routine that turns a set of fitted parameters
--  into per-sample labels is observed only through the free input
--  `labelsFor : Params → Labels`. The spec makes no behavioural claim about that
--  routine — it holds for EVERY function it could be — so there is nothing to
--  check against a real callee (no G-AX). The behaviour under spec — WHICH
--  parameter set the labels are computed from — is modeled deeply in the `impl`
--  region, no outside contract consumed. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- A complete set of fitted model parameters, identified abstractly: the desired
   behaviour observes only WHICH parameter set the reported labels are derived
   from, never the concrete contents of a parameter set. -/
abbrev Params := Nat

/- The per-sample labels a routine reports: identified abstractly, since the only
   thing observed here is that they are exactly the labels the label-computing
   routine yields for some parameter set. -/
abbrev Labels := List Nat

/- The labels a caller should get from this fit.

   `storedParams` is the parameter set the fitted estimator stores — the one a
   later, separate label query against the same fitted estimator reads.
   `labelsFor` maps any parameter set to the labels it implies for the given data.
   The labels reported at fit time must be EXACTLY the labels that this same
   routine yields for the estimator's stored parameter set, so that asking the
   fitted estimator for labels a second time returns the same answer (the two
   paths agree). -/
def reportedLabels (storedParams : Params) (labelsFor : Params → Labels) : Labels :=
  labelsFor storedParams
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compute the labels this fit reports to its caller.

   `transientParams` is a parameter set that may be in force partway through
   finalization but is not the one the fitted estimator ends up storing.
   `storedParams` is the parameter set the fitted estimator stores — the one a
   later, separate label query reads. `labelsFor` maps any parameter set to the
   labels it implies for the given data.

   The result is `reportedLabels storedParams labelsFor`: the labels reported here
   must agree with the labels obtained from the estimator's stored parameter set,
   so a fit-time label and a subsequent separate query give the same answer. They
   must therefore be derived from `storedParams`, not from `transientParams`. All
   three inputs are read-only (none `mut`): the routine reads them and returns a
   result, mutating nothing it is handed (directive 5). -/
method finalizeLabels (transientParams : Params) (storedParams : Params) (labelsFor : Params → Labels) return (out : Labels)
  ensures out = reportedLabels storedParams labelsFor
  do
    -- impl-start
    -- Make the stored parameter set current FIRST, then compute the labels, so
    -- the reported labels are derived from the stored parameters and agree with a
    -- later separate query — not from the transient parameter set.
    let mut active := transientParams
    active := storedParams
    let out := labelsFor active
    return out
    -- impl-end

prove_correct finalizeLabels by
  loom_solve
  simp_all [reportedLabels]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec: partial-correctness method finalizeLabels(transientParams, storedParams, labelsFor) with EXACT-EQUALITY postcondition `ensures out = reportedLabels storedParams labelsFor` where reportedLabels s f := f s. Because the postcondition is a total functional equality (out = labelsFor storedParams), any TERMINATING verifying impl must return exactly labelsFor storedParams => it refines the gold and resolves. There is no room for a terminating verify-but-wrong impl.

ATTACK PANEL (7 distinct same-spec wrong impls, all verified via `bash scripts/lean_verify.sh <f>`; each same_spec=True via swebench_unified.markers.same_spec/velvet):
- atk_2 prepatch-shape (mut active:=transient; out:=labelsFor active; active:=stored): exit=1, residual `labelsFor transientParams = labelsFor storedParams` (unprovable, labelsFor free). PREPATCH BUG REPRODUCED.
- atk_3 partial-domain (diverge-while when transient!=stored else correct, frozen shipped proof): exit=1, active havoc'd, residual `labelsFor active = labelsFor storedParams`.
- atk_4 control-flow-effect constant (return []): exit=1, residual `labelsFor storedParams = []`.
- atk_5 ungrounded-oracle echo (return labelsFor 0): exit=1, residual `labelsFor 0 = labelsFor storedParams`.
- atk_6 boundary divergence (counter while n>0 never 0, frozen proof; return labelsFor transient): exit=1, done-branch residual `labelsFor transientParams = labelsFor storedParams`.
- atk_8 direct transient (return labelsFor transientParams): exit=1, residual `labelsFor transientParams = labelsFor storedParams`.
- atk_9 control-flow swap (active:=stored; active:=transient; out:=labelsFor active): exit=1, same residual.
ALL 7 REJECTED for the exact discriminating goal. => patches={} (no submitted attack verifies; no faithful patch to resolve-check).

POSITIVE CONTROL: positive_control.lean (gold Solution.lean) VERIFIES exit=0. Also confirmed atk_7 (correct alt `return labelsFor storedParams`) verifies exit=0 — a correct echo, deliberately NOT submitted as an attack.

HARNESS ANCHOR (executed, not speculated): ran gold patch.diff through run_resolve('scikit-learn__scikit-learn-13142') => RESOLVED=True COMPLETED=True. Gold patch is a pure code MOVE (relocate final `_, log_resp=self._e_step(X)` to AFTER `self._set_parameters(best_params)` in sklearn/mixture/base.py).

DIVERGENCE / PARTIAL-CORRECTNESS HOLE (examined, ruled out-of-scope, NOT submitted as an attack): the prove_correct body is elided from the spec view (same_spec stays True when the proof is changed — confirmed via probe_proofchange.lean / probe_div_customproof.lean), so an attacker may supply their own proof. An impl with `while true ... done_with False` returning labelsFor transientParams, proved with `loom_solve`, DOES verify (exit=0, same_spec=True) via vacuous partial correctness (file: probe_div_customproof.lean). This is NOT a G-EQ refinement-fidelity defect and cannot produce a verify⇏correct break:

(1) it is a universal artifact of `set_option loom.semantics.termination "partial"` shared by every velvet bundle (documented default in spec_guide), not a weakness of THIS spec;

(2) no gold operation corresponds to a non-terminating loop, so no FAITHFUL refined patch exists — refinement.md's map A1–A5 covers only the terminating dataflow;

(3) mechanically, a faithful patch for a divergent model (`while True: pass`) would only TIME OUT, so run_resolve returns completed=False, and _derive_audit_verdict records INCONCLUSIVE (`if r.completed and not r.resolved`), never BROKEN. Submitting it would inject a spurious INCONCLUSIVE, not a real defect. Hence excluded from `attacks`.

REFINEMENT.MD AUDIT (A legs / model<->patch correspondence — G-EQ's focus): no `axiom`s and no A-reference deep models (grep clean; mapping.md §3, refinement.md §B/§C). Legs A1,A2,A5 = R (Params/Labels opaque bijections), A4 = R (labelsFor as fully-free unchanged callee _e_step∘argmax; no contract consumed => G-AX skip is correct), A3 = I (`active := storedParams` <-> `self._set_parameters(best_params)`, concrete assignment). NO kind-3 leg: the one genuinely-changed operation (POSITION of the final e-step relative to the param install) is modeled DIRECTLY by statement ordering (A3 before A4), not hidden behind an axiom. Correspondence to real callees holds: storedParams<->best_params=_get_parameters() (line 257, installed line 272), transientParams<->last-attempt leftover state, labelsFor<->_e_step(X)+argmax as a pure fn of active params (X fixed). G-CONF conf_skip is justified (ordering-only discriminator over an unchanged free-input callee; materializes only on a live fitted mixture with n_init>1, not fuzzable).

VERDICT: SOUND — 7 same-spec terminating wrong impls all rejected for the exact discriminating goal, prepatch reproduced, positive control verifies, gold resolves (executed), refinement legs all R/I with sound callee correspondence and no kind-3. The sole verify-but-wrong construction is non-termination, which is out of G-EQ scope and cannot yield a resolving faithful patch.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The routine that turns a set of fitted parameters
--  into per-sample labels is observed only through the free input
--  `labelsFor : Params → Labels`. The spec makes no behavioural claim about that
--  routine — it holds for EVERY function it could be — so there is nothing to
--  check against a real callee (no G-AX). The behaviour under spec — WHICH
--  parameter set the labels are computed from — is modeled deeply in the `impl`
--  region, no outside contract consumed. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- A complete set of fitted model parameters, identified abstractly: the desired
   behaviour observes only WHICH parameter set the reported labels are derived
   from, never the concrete contents of a parameter set. -/
abbrev Params := Nat

/- The per-sample labels a routine reports: identified abstractly, since the only
   thing observed here is that they are exactly the labels the label-computing
   routine yields for some parameter set. -/
abbrev Labels := List Nat

/- The labels a caller should get from this fit.

   `storedParams` is the parameter set the fitted estimator stores — the one a
   later, separate label query against the same fitted estimator reads.
   `labelsFor` maps any parameter set to the labels it implies for the given data.
   The labels reported at fit time must be EXACTLY the labels that this same
   routine yields for the estimator's stored parameter set, so that asking the
   fitted estimator for labels a second time returns the same answer (the two
   paths agree). -/
def reportedLabels (storedParams : Params) (labelsFor : Params → Labels) : Labels :=
  labelsFor storedParams
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compute the labels this fit reports to its caller.

   `transientParams` is a parameter set that may be in force partway through
   finalization but is not the one the fitted estimator ends up storing.
   `storedParams` is the parameter set the fitted estimator stores — the one a
   later, separate label query reads. `labelsFor` maps any parameter set to the
   labels it implies for the given data.

   The result is `reportedLabels storedParams labelsFor`: the labels reported here
   must agree with the labels obtained from the estimator's stored parameter set,
   so a fit-time label and a subsequent separate query give the same answer. They
   must therefore be derived from `storedParams`, not from `transientParams`. All
   three inputs are read-only (none `mut`): the routine reads them and returns a
   result, mutating nothing it is handed (directive 5). -/
method finalizeLabels (transientParams : Params) (storedParams : Params) (labelsFor : Params → Labels) return (out : Labels)
  ensures out = reportedLabels storedParams labelsFor
  do
    -- impl-start
    -- Make the stored parameter set current FIRST, then compute the labels, so
    -- the reported labels are derived from the stored parameters and agree with a
    -- later separate query — not from the transient parameter set.
    let mut active := transientParams
    active := storedParams
    let out := labelsFor active
    return out
    -- impl-end

prove_correct finalizeLabels by
  loom_solve
  simp_all [reportedLabels]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec: partial-correctness method finalizeLabels(transientParams, storedParams, labelsFor) with EXACT-EQUALITY postcondition `ensures out = reportedLabels storedParams labelsFor` where reportedLabels s f := f s. Because the postcondition is a total functional equality (out = labelsFor storedParams), any TERMINATING verifying impl must return exactly labelsFor storedParams => it refines the gold and resolves. There is no room for a terminating verify-but-wrong impl.

ATTACK PANEL (7 distinct same-spec wrong impls, all verified via `bash scripts/lean_verify.sh <f>`; each same_spec=True via swebench_unified.markers.same_spec/velvet):
- atk_2 prepatch-shape (mut active:=transient; out:=labelsFor active; active:=stored): exit=1, residual `labelsFor transientParams = labelsFor storedParams` (unprovable, labelsFor free). PREPATCH BUG REPRODUCED.
- atk_3 partial-domain (diverge-while when transient!=stored else correct, frozen shipped proof): exit=1, active havoc'd, residual `labelsFor active = labelsFor storedParams`.
- atk_4 control-flow-effect constant (return []): exit=1, residual `labelsFor storedParams = []`.
- atk_5 ungrounded-oracle echo (return labelsFor 0): exit=1, residual `labelsFor 0 = labelsFor storedParams`.
- atk_6 boundary divergence (counter while n>0 never 0, frozen proof; return labelsFor transient): exit=1, done-branch residual `labelsFor transientParams = labelsFor storedParams`.
- atk_8 direct transient (return labelsFor transientParams): exit=1, residual `labelsFor transientParams = labelsFor storedParams`.
- atk_9 control-flow swap (active:=stored; active:=transient; out:=labelsFor active): exit=1, same residual.
ALL 7 REJECTED for the exact discriminating goal. => patches={} (no submitted attack verifies; no faithful patch to resolve-check).

POSITIVE CONTROL: positive_control.lean (gold Solution.lean) VERIFIES exit=0. Also confirmed atk_7 (correct alt `return labelsFor storedParams`) verifies exit=0 — a correct echo, deliberately NOT submitted as an attack.

HARNESS ANCHOR (executed, not speculated): ran gold patch.diff through run_resolve('scikit-learn__scikit-learn-13142') => RESOLVED=True COMPLETED=True. Gold patch is a pure code MOVE (relocate final `_, log_resp=self._e_step(X)` to AFTER `self._set_parameters(best_params)` in sklearn/mixture/base.py).

DIVERGENCE / PARTIAL-CORRECTNESS HOLE (examined, ruled out-of-scope, NOT submitted as an attack): the prove_correct body is elided from the spec view (same_spec stays True when the proof is changed — confirmed via probe_proofchange.lean / probe_div_customproof.lean), so an attacker may supply their own proof. An impl with `while true ... done_with False` returning labelsFor transientParams, proved with `loom_solve`, DOES verify (exit=0, same_spec=True) via vacuous partial correctness (file: probe_div_customproof.lean). This is NOT a G-EQ refinement-fidelity defect and cannot produce a verify⇏correct break:

(1) it is a universal artifact of `set_option loom.semantics.termination "partial"` shared by every velvet bundle (documented default in spec_guide), not a weakness of THIS spec;

(2) no gold operation corresponds to a non-terminating loop, so no FAITHFUL refined patch exists — refinement.md's map A1–A5 covers only the terminating dataflow;

(3) mechanically, a faithful patch for a divergent model (`while True: pass`) would only TIME OUT, so run_resolve returns completed=False, and _derive_audit_verdict records INCONCLUSIVE (`if r.completed and not r.resolved`), never BROKEN. Submitting it would inject a spurious INCONCLUSIVE, not a real defect. Hence excluded from `attacks`.

REFINEMENT.MD AUDIT (A legs / model<->patch correspondence — G-EQ's focus): no `axiom`s and no A-reference deep models (grep clean; mapping.md §3, refinement.md §B/§C). Legs A1,A2,A5 = R (Params/Labels opaque bijections), A4 = R (labelsFor as fully-free unchanged callee _e_step∘argmax; no contract consumed => G-AX skip is correct), A3 = I (`active := storedParams` <-> `self._set_parameters(best_params)`, concrete assignment). NO kind-3 leg: the one genuinely-changed operation (POSITION of the final e-step relative to the param install) is modeled DIRECTLY by statement ordering (A3 before A4), not hidden behind an axiom. Correspondence to real callees holds: storedParams<->best_params=_get_parameters() (line 257, installed line 272), transientParams<->last-attempt leftover state, labelsFor<->_e_step(X)+argmax as a pure fn of active params (X fixed). G-CONF conf_skip is justified (ordering-only discriminator over an unchanged free-input callee; materializes only on a live fitted mixture with n_init>1, not fuzzable).

VERDICT: SOUND — 7 same-spec terminating wrong impls all rejected for the exact discriminating goal, prepatch reproduced, positive control verifies, gold resolves (executed), refinement legs all R/I with sound callee correspondence and no kind-3. The sole verify-but-wrong construction is non-termination, which is out of G-EQ scope and cannot yield a resolving faithful patch.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec-vs-repo faithfulness check for scikit-learn__scikit-learn-13142 (velvet). Modeled function finalizeLabels(transientParams, storedParams, labelsFor) with ensures `out = reportedLabels storedParams labelsFor = labelsFor storedParams`.

Real repo tail (post-patch fit_predict, sklearn/mixture/base.py, verified against base_commit 1c8668b0 checkout): self._set_parameters(best_params) installs the best-scoring attempt's params (= storedParams); _, log_resp = self._e_step(X) recomputes the E-step with those params in force; return log_resp.argmax(axis=1). Gold patch confirmed from dataset: it MOVES the final _e_step from before _set_parameters to after it.

Because the final E-step is fully recomputed after _set_parameters, the returned labels depend only on the stored/best params (with X fixed) and NOT on the leftover last-attempt params. That is exactly `labelsFor storedParams`, independent of transientParams — matching the spec for EVERY (transientParams, storedParams, labelsFor).

No over-claim / spec not too strong: labelsFor is left fully free (quantified over ALL functions Params -> Labels), so the spec asserts nothing about concrete label values — only WHICH parameter set they derive from. This is the weakest faithful claim capturing the ordering fix; there is no input on which the modeled function requires behaviour the post-patch repo fails to exhibit. The abstraction is sound: with X fixed, _e_step(X) is a deterministic function of the active parameter set, so E-step∘argmax is genuinely a function of the params alone.

Checks performed: same_spec(Solution, Solution_prepatch, velvet tables) = True (spec region byte-identical); lean_verify.sh on Solution.lean exit 0 (verifies); prepatch has the operations reversed (out := labelsFor active while active=transientParams, then active := storedParams) reducing the obligation to labelsFor transientParams = labelsFor storedParams which is unprovable, so G-DIFF is genuine. No diverging input exists — the spec is FAITHFUL to the real repo callee behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit = a code MOVE in sklearn/mixture/base.py: relocate `_, log_resp = self._e_step(X)` from BEFORE `self._set_parameters(best_params)` to AFTER it, so fit_predict reports labels derived from the best/stored parameters rather than the loop's leftover. Fix mechanism is stated only in hints_text (out of scope), NOT in the public problem_statement. Public problem_statement discloses: fit_predict and predict disagree when n_init>1 and must agree (with a repro).

Independent verification:
- markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True — spec region byte-identical; the discriminator lives entirely in the elided impl region, not the visible spec view.
- Mechanical leakage.screen() over the spec view PASSES (0 hard failures): no diff markers, no >=8-char gold-patch line reproduced, no patched file path/module path, no spec-view identifier embedding a patched repo symbol, no narration keywords.

Spec view exposes only: abstract carriers Params:=Nat, Labels:=List Nat; opaque labelsFor:Params->Labels; pure def reportedLabels storedParams labelsFor := labelsFor storedParams; obligation `ensures out = reportedLabels storedParams labelsFor`; docstrings asserting reported labels must equal what the same routine yields for the stored parameter set 'so that asking the fitted estimator for labels a second time returns the same answer (the two paths agree)'.

Why NO-LEAKAGE: (1) The core assertion (fit-time labels must be consistent with the stored params, i.e. what predict reads) is a faithful contract-level restatement of the problem_statement's OWN public requirement that fit_predict and predict agree — specifying the required contract is not leaking the fix. (2) The spec view never names _e_step, _set_parameters, argmax, base.py, line numbers, the n_init loop internals, or the ORDER/reordering MOVE that constitutes the gold edit; all mechanism is confined to the elided impl-start..impl-end region and to hints_text (out of scope). (3) transientParams/storedParams are generic modeling devices, described without disclosing the code-level mechanism. The specific gold edit is not reconstructible from the spec view beyond what problem_statement already implies.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.