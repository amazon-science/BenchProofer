# P2 adversarial audit — scikit-learn__scikit-learn-10297

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- No consumed axioms. The construction-time behaviour the modeled estimator
@@ -60,9 +60,7 @@
   ensures out = construct true storeCvValues
   do
     -- impl-start
-    -- `acceptsStore` is this estimator's capability: it supports retaining the
-    -- per-alpha cross-validation values.
-    let acceptsStore : Bool := true
+    let acceptsStore : Bool := false
     if storeCvValues && !acceptsStore then
       return Except.error InitErr.storeNotAccepted
     else
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
 /- No consumed axioms. The construction-time behaviour the modeled estimator
@@ -60,13 +60,7 @@
   ensures out = construct true storeCvValues
   do
     -- impl-start
-    -- `acceptsStore` is this estimator's capability: it supports retaining the
-    -- per-alpha cross-validation values.
-    let acceptsStore : Bool := true
-    if storeCvValues && !acceptsStore then
-      return Except.error InitErr.storeNotAccepted
-    else
-      return Except.ok { storeCvValues := storeCvValues }
+    return Except.ok { storeCvValues := false }
     -- impl-end
 
 prove_correct initEstimator by
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
 /- No consumed axioms. The construction-time behaviour the modeled estimator
@@ -60,10 +60,7 @@
   ensures out = construct true storeCvValues
   do
     -- impl-start
-    -- `acceptsStore` is this estimator's capability: it supports retaining the
-    -- per-alpha cross-validation values.
-    let acceptsStore : Bool := true
-    if storeCvValues && !acceptsStore then
+    if storeCvValues then
       return Except.error InitErr.storeNotAccepted
     else
       return Except.ok { storeCvValues := storeCvValues }
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
 /- No consumed axioms. The construction-time behaviour the modeled estimator
@@ -60,13 +60,7 @@
   ensures out = construct true storeCvValues
   do
     -- impl-start
-    -- `acceptsStore` is this estimator's capability: it supports retaining the
-    -- per-alpha cross-validation values.
-    let acceptsStore : Bool := true
-    if storeCvValues && !acceptsStore then
-      return Except.error InitErr.storeNotAccepted
-    else
-      return Except.ok { storeCvValues := storeCvValues }
+    return Except.error InitErr.storeNotAccepted
     -- impl-end
 
 prove_correct initEstimator by
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms. The construction-time behaviour the modeled estimator
@@ -60,15 +60,8 @@
   ensures out = construct true storeCvValues
   do
     -- impl-start
-    -- `acceptsStore` is this estimator's capability: it supports retaining the
-    -- per-alpha cross-validation values.
-    let acceptsStore : Bool := true
-    if storeCvValues && !acceptsStore then
-      return Except.error InitErr.storeNotAccepted
-    else
-      return Except.ok { storeCvValues := storeCvValues }
+    return construct true storeCvValues
     -- impl-end
 
 prove_correct initEstimator by
   loom_solve
-  simp [construct]
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
 /- No consumed axioms. The construction-time behaviour the modeled estimator
@@ -60,13 +60,7 @@
   ensures out = construct true storeCvValues
   do
     -- impl-start
-    -- `acceptsStore` is this estimator's capability: it supports retaining the
-    -- per-alpha cross-validation values.
-    let acceptsStore : Bool := true
-    if storeCvValues && !acceptsStore then
-      return Except.error InitErr.storeNotAccepted
-    else
-      return Except.ok { storeCvValues := storeCvValues }
+    return Except.ok { storeCvValues := !storeCvValues }
     -- impl-end
 
 prove_correct initEstimator by
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The construction-time behaviour the modeled estimator
@@ -60,13 +60,10 @@
   ensures out = construct true storeCvValues
   do
     -- impl-start
-    -- `acceptsStore` is this estimator's capability: it supports retaining the
-    -- per-alpha cross-validation values.
-    let acceptsStore : Bool := true
-    if storeCvValues && !acceptsStore then
+    if storeCvValues then
+      return Except.ok { storeCvValues := storeCvValues }
+    else
       return Except.error InitErr.storeNotAccepted
-    else
-      return Except.ok { storeCvValues := storeCvValues }
     -- impl-end
 
 prove_correct initEstimator by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The construction-time behaviour the modeled estimator
   routes through — when retention of the per-alpha cross-validation values is
   requested of an estimator that supports that option, build the estimator and
   record the request faithfully; refuse only when the option is unsupported —
   is modeled DEEPLY in the `pure` region (`construct`). The per-estimator
   capability is concrete data, validated against the real class by G-CONF;
   there is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- Refusing a construction because retention of the cross-validation values was
   requested of an estimator that does not support that option. The only
   construction outcome the desired behaviour distinguishes from success. -/
inductive InitErr where
  | storeNotAccepted
  deriving DecidableEq

/- The observable content of a constructed estimator that the desired behaviour
   constrains: whether it was asked to retain the per-alpha cross-validation
   values (the `cv_values_` attribute the user later reads). Every other aspect
   of the estimator is orthogonal here (mapping.md §2). -/
structure EstimatorState where
  storeCvValues : Bool
  deriving DecidableEq

/- The construction outcome, modeled deeply. `acceptsStore` is the capability
   the construction consults: when retention of the cross-validation values is
   requested of an estimator that does not support it, construction is refused;
   otherwise the estimator is built and the requested option is recorded on it
   unchanged. Pinned by the method's `ensures`. -/
def construct (acceptsStore : Bool) (storeCvValues : Bool) :
    Except InitErr EstimatorState :=
  if storeCvValues && !acceptsStore then Except.error .storeNotAccepted
  else Except.ok { storeCvValues := storeCvValues }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Construct a cross-validated estimator, optionally requesting that the
   per-alpha cross-validation values be retained for later inspection. Desired
   behaviour: this estimator supports retaining those values, so construction
   with the option set must SUCCEED and the built estimator must carry the
   requested option through unchanged — a later fit reads the recorded option to
   decide whether to populate the retained-values attribute, so the option must
   be recorded faithfully, not merely accepted. -/
method initEstimator (storeCvValues : Bool) return (out : Except InitErr EstimatorState)
  ensures out = construct true storeCvValues
  do
    -- impl-start
    -- `acceptsStore` is this estimator's capability: it supports retaining the
    -- per-alpha cross-validation values.
    let acceptsStore : Bool := true
    if storeCvValues && !acceptsStore then
      return Except.error InitErr.storeNotAccepted
    else
      return Except.ok { storeCvValues := storeCvValues }
    -- impl-end

prove_correct initEstimator by
  loom_solve
  simp [construct]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: ensures `out = construct true storeCvValues`. construct true s = if (s && !true) then error else ok{storeCvValues:=s}; since !true=false the guard is ALWAYS false, so the spec reduces to a TOTAL FUNCTIONAL EQUATION: out = Except.ok {storeCvValues := s} for every input. Domain is Bool (2 points). Any verifying impl must be behaviorally identical to gold on the entire domain — there is no room for a same-spec verifying wrong impl.

same_spec: all 7 attacks + positive control returned True (impl-region-only edits; axioms/pure/pre/post byte-identical).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
- pos_control.lean (exact gold impl): exit=0 VERIFIES (positive control good).
- atk_1.lean (PREPATCH bug: acceptsStore:=false): exit=1 FAILS — goal `Except.ok{storeCvValues:=s}=construct true s` on the s=true branch unsatisfiable (prepatch reproduced).
- atk_2.lean (drop-the-option / partial-domain: always records false): exit=1 FAILS — unsolved goal `storeCvValues = false`.
- atk_3.lean (boundary/swap: refuse when option requested): exit=1 FAILS — `⊢ False` on the requested branch.
- atk_4.lean (control-flow-effect: unconditional error): exit=1 FAILS.
- atk_6.lean (negated-record: storeCvValues := !storeCvValues): exit=1 FAILS — unsolved `⊢ False`.
- atk_7.lean (partial-domain other side: error on false): exit=1 FAILS.
- atk_5.lean (UNGROUNDED-ORACLE ECHO: `return construct true storeCvValues`): after fixing a benign proof-script fragility (removed trailing `simp [construct]` that hit 'No goals to be solved' because the impl is definitionally the RHS; the proof block is NOT part of the frozen spec, same_spec remained True), exit=0 VERIFIES.

ECHO RESOLVE (mandatory): atk_5 is the ONLY verifying wrong impl. Its impl equals `construct true storeCvValues` = gold's exact output on the whole Bool domain, so its faithful refined patch IS the gold patch (materialized at atk_5.patch.diff, byte-identical to benchmark-verified/.../patch.diff). Ran run_resolve('scikit-learn__scikit-learn-10297', <atk_5.patch.diff>, timeout=1800) via official harness: completed=True, resolved=True, flaky=False, note='resolved'. The verifying echo RESOLVES — this is the source-repo adversary 'weakness' echo shape, NOT a spec weakness (per the audit protocol G-PANEL-1 echo-attack policy: a same-spec verifying attack fails the gate only if its refined patch does NOT resolve).

REFINEMENT.MD AUDIT: 4 legs (steps 1-4), tagged R / I / I / (R+I). NO kind-3 (inexpressible-changed-op) steps. NO axioms and NO `:|` stubs in Solution.lean (grep confirmed: no `axiom`, no `:|`, no sorry/admit/native_decide/Classical.choice). Refinement claim 'no A legs, entire correspondence R/I, covered by G-CONF against real patched class' is consistent with the source: the modeled behaviour (expose+forward store_cv_values → record self.store_cv_values, read by unchanged fit) is exactly the gold hunk (ridge.py:1339 __init__ + base :1093). The success clause pins storeCvValues:=storeCvValues (records the option), correctly ruling out the drop-the-option impl (atk_2) that would pass a mere 'succeeds' spec but fail F2P — this is load-bearing and correctly present. A-leg correspondence: N/A (no A legs).

VERDICT: SOUND. 7 distinct same-spec attacks encoded + verified (prepatch, drop-option/partial-domain, boundary-swap, control-flow-effect unconditional-error, negated-record, partial-domain-other-side, ungrounded-oracle-echo). 6 behaviorally-wrong impls all FAIL to verify (the total functional-equation spec admits no verifying wrong impl); the 1 that verifies (echo) is gold-equivalent and its faithful patch RESOLVES under the official harness. No verify⇏correct gap found. Positive control verifies; prepatch reproduced.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The construction-time behaviour the modeled estimator
   routes through — when retention of the per-alpha cross-validation values is
   requested of an estimator that supports that option, build the estimator and
   record the request faithfully; refuse only when the option is unsupported —
   is modeled DEEPLY in the `pure` region (`construct`). The per-estimator
   capability is concrete data, validated against the real class by G-CONF;
   there is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- Refusing a construction because retention of the cross-validation values was
   requested of an estimator that does not support that option. The only
   construction outcome the desired behaviour distinguishes from success. -/
inductive InitErr where
  | storeNotAccepted
  deriving DecidableEq

/- The observable content of a constructed estimator that the desired behaviour
   constrains: whether it was asked to retain the per-alpha cross-validation
   values (the `cv_values_` attribute the user later reads). Every other aspect
   of the estimator is orthogonal here (mapping.md §2). -/
structure EstimatorState where
  storeCvValues : Bool
  deriving DecidableEq

/- The construction outcome, modeled deeply. `acceptsStore` is the capability
   the construction consults: when retention of the cross-validation values is
   requested of an estimator that does not support it, construction is refused;
   otherwise the estimator is built and the requested option is recorded on it
   unchanged. Pinned by the method's `ensures`. -/
def construct (acceptsStore : Bool) (storeCvValues : Bool) :
    Except InitErr EstimatorState :=
  if storeCvValues && !acceptsStore then Except.error .storeNotAccepted
  else Except.ok { storeCvValues := storeCvValues }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Construct a cross-validated estimator, optionally requesting that the
   per-alpha cross-validation values be retained for later inspection. Desired
   behaviour: this estimator supports retaining those values, so construction
   with the option set must SUCCEED and the built estimator must carry the
   requested option through unchanged — a later fit reads the recorded option to
   decide whether to populate the retained-values attribute, so the option must
   be recorded faithfully, not merely accepted. -/
method initEstimator (storeCvValues : Bool) return (out : Except InitErr EstimatorState)
  ensures out = construct true storeCvValues
  do
    -- impl-start
    -- `acceptsStore` is this estimator's capability: it supports retaining the
    -- per-alpha cross-validation values.
    let acceptsStore : Bool := true
    if storeCvValues && !acceptsStore then
      return Except.error InitErr.storeNotAccepted
    else
      return Except.ok { storeCvValues := storeCvValues }
    -- impl-end

prove_correct initEstimator by
  loom_solve
  simp [construct]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: ensures `out = construct true storeCvValues`. construct true s = if (s && !true) then error else ok{storeCvValues:=s}; since !true=false the guard is ALWAYS false, so the spec reduces to a TOTAL FUNCTIONAL EQUATION: out = Except.ok {storeCvValues := s} for every input. Domain is Bool (2 points). Any verifying impl must be behaviorally identical to gold on the entire domain — there is no room for a same-spec verifying wrong impl.

same_spec: all 7 attacks + positive control returned True (impl-region-only edits; axioms/pure/pre/post byte-identical).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
- pos_control.lean (exact gold impl): exit=0 VERIFIES (positive control good).
- atk_1.lean (PREPATCH bug: acceptsStore:=false): exit=1 FAILS — goal `Except.ok{storeCvValues:=s}=construct true s` on the s=true branch unsatisfiable (prepatch reproduced).
- atk_2.lean (drop-the-option / partial-domain: always records false): exit=1 FAILS — unsolved goal `storeCvValues = false`.
- atk_3.lean (boundary/swap: refuse when option requested): exit=1 FAILS — `⊢ False` on the requested branch.
- atk_4.lean (control-flow-effect: unconditional error): exit=1 FAILS.
- atk_6.lean (negated-record: storeCvValues := !storeCvValues): exit=1 FAILS — unsolved `⊢ False`.
- atk_7.lean (partial-domain other side: error on false): exit=1 FAILS.
- atk_5.lean (UNGROUNDED-ORACLE ECHO: `return construct true storeCvValues`): after fixing a benign proof-script fragility (removed trailing `simp [construct]` that hit 'No goals to be solved' because the impl is definitionally the RHS; the proof block is NOT part of the frozen spec, same_spec remained True), exit=0 VERIFIES.

ECHO RESOLVE (mandatory): atk_5 is the ONLY verifying wrong impl. Its impl equals `construct true storeCvValues` = gold's exact output on the whole Bool domain, so its faithful refined patch IS the gold patch (materialized at atk_5.patch.diff, byte-identical to benchmark-verified/.../patch.diff). Ran run_resolve('scikit-learn__scikit-learn-10297', <atk_5.patch.diff>, timeout=1800) via official harness: completed=True, resolved=True, flaky=False, note='resolved'. The verifying echo RESOLVES — this is the source-repo adversary 'weakness' echo shape, NOT a spec weakness (per the audit protocol G-PANEL-1 echo-attack policy: a same-spec verifying attack fails the gate only if its refined patch does NOT resolve).

REFINEMENT.MD AUDIT: 4 legs (steps 1-4), tagged R / I / I / (R+I). NO kind-3 (inexpressible-changed-op) steps. NO axioms and NO `:|` stubs in Solution.lean (grep confirmed: no `axiom`, no `:|`, no sorry/admit/native_decide/Classical.choice). Refinement claim 'no A legs, entire correspondence R/I, covered by G-CONF against real patched class' is consistent with the source: the modeled behaviour (expose+forward store_cv_values → record self.store_cv_values, read by unchanged fit) is exactly the gold hunk (ridge.py:1339 __init__ + base :1093). The success clause pins storeCvValues:=storeCvValues (records the option), correctly ruling out the drop-the-option impl (atk_2) that would pass a mere 'succeeds' spec but fail F2P — this is load-bearing and correctly present. A-leg correspondence: N/A (no A legs).

VERDICT: SOUND. 7 distinct same-spec attacks encoded + verified (prepatch, drop-option/partial-domain, boundary-swap, control-flow-effect unconditional-error, negated-record, partial-domain-other-side, ungrounded-oracle-echo). 6 behaviorally-wrong impls all FAIL to verify (the total functional-equation spec admits no verifying wrong impl); the 1 that verifies (echo) is gold-equivalent and its faithful patch RESOLVES under the official harness. No verify⇏correct gap found. Positive control verifies; prepatch reproduced.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Setup checks all pass. (1) Spec region byte-identical: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) == True. (2) Solution.lean elaborates cleanly (lean_verify exit 0); Solution_prepatch.lean fails prove_correct on the storeCvValues=true branch as required by G-DIFF (real discriminator).

Faithfulness analysis: the modeled function initEstimator has spec `out = construct true storeCvValues`, and construct with acceptsStore=true reduces to `Except.ok {storeCvValues := storeCvValues}` for BOTH boolean inputs (the error path `storeCvValues && !acceptsStore` is dead). The real callee is RidgeClassifierCV(store_cv_values=...) at base_commit b90661d after the gold patch, which exposes store_cv_values and forwards it to _BaseRidgeCV.__init__. Verified from the source at base_commit: _BaseRidgeCV.__init__ (ridge.py:1088-1102) ALREADY declares `store_cv_values=False` and executes `self.store_cv_values = store_cv_values` — so forwarding always succeeds and records the exact requested value. Therefore post-patch reality: store_cv_values=False → construct succeeds, self.store_cv_values==False; store_cv_values=True → succeeds, self.store_cv_values==True. This is identity-recording, exactly what the spec pins.

Over-constraint check (spec too strong?): NO. The spec constrains only the recorded storeCvValues field and success/refuse outcome; the bijection (mapping.md §2) drops all orthogonal fields (alphas, fit_intercept, ...). Every constrained observable matches the real setter on the full domain. The 'records faithfully' clause (storeCvValues := storeCvValues, not always-False) is load-bearing and MATCHES reality — it is not stronger than the repo. The refusal variant is unreachable in both spec and reality for this estimator, so it introduces no divergence.

G-CONF independently ran the R/I shadow vs the real patched class over 100002 inputs (seed 10297) with 0 disagreements (meta.json G-CONF pass, exit 0). Since the domain is a single Bool, that is a total enumeration many times over. No input where the modeled function disagrees with the real callee could be found. Spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Confirmed same_spec(Solution, Solution_prepatch, velvet)=True (frozen spec byte-identical across pre/post). Computed the actual spec view (impl + prove_correct bodies elided). The lexical leakage.screen also passes (no hard_failures, no warnings). Semantic review: the spec view models the desired behaviour abstractly — a constructor taking `storeCvValues : Bool` that (via `construct true storeCvValues`) succeeds and records the option faithfully so a later fit reads it to decide whether the retained-values attribute is populated. Every element of this is already disclosed by the PUBLIC problem_statement, which explicitly (a) reports the `TypeError: __init__() got an unexpected keyword argument 'store_cv_values'`, (b) titles the request 'Add store_cv_values boolean flag support to RidgeClassifierCV', and (c) states cv_values_ should be retrievable when store_cv_values=True and cv=None. The spec view exposes NO repo-specific gold-edit mechanics: no `super().__init__`, no `_BaseRidgeCV`, no `ridge.py` line numbers, no default-value / forwarding detail. Those repo specifics appear only in mapping.md and refinement.md, which are refinement-audit documents, not part of the consumer spec view. The `acceptsStore := true` capability datum is behavioural (the estimator supports the option) rather than a leak of the patch's code shape, and is exactly what the issue demands. Therefore the spec leaks nothing about the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
