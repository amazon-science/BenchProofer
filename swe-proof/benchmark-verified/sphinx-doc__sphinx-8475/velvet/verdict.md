# P2 adversarial audit — sphinx-doc__sphinx-8475

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 /- No consumed axioms. The behaviour this slice depends on — how a failed link
@@ -121,10 +121,12 @@
       match headProbe with
       | .reached sameTarget => classifyReached sameTarget
       | .failed e =>
-          -- The first probe failed: decide whether to retry with a full fetch.
-          -- A status-carrying failure OR a redirect-budget exhaustion is
-          -- retried; any other failure is not.
-          if retriable e then
+          let retry : Bool :=
+            match e with
+            | .statusError _ => true
+            | .redirectLoop  => false
+            | .otherFailure  => false
+          if retry then
             match getProbe with
             | .reached sameTarget => classifyReached sameTarget
             | .failed e2          => classifyUnhandled e2
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
 /- No consumed axioms. The behaviour this slice depends on — how a failed link
@@ -121,13 +121,16 @@
       match headProbe with
       | .reached sameTarget => classifyReached sameTarget
       | .failed e =>
-          -- The first probe failed: decide whether to retry with a full fetch.
-          -- A status-carrying failure OR a redirect-budget exhaustion is
-          -- retried; any other failure is not.
           if retriable e then
             match getProbe with
             | .reached sameTarget => classifyReached sameTarget
-            | .failed e2          => classifyUnhandled e2
+            | .failed e2          =>
+                match e2 with
+                | .statusError 401 => .broken
+                | .statusError 503 => .ignored
+                | .statusError _   => .broken
+                | .redirectLoop    => .broken
+                | .otherFailure    => .broken
           else
             classifyUnhandled e
     return out
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
 /- No consumed axioms. The behaviour this slice depends on — how a failed link
@@ -119,11 +119,8 @@
     -- impl-start
     let out : LinkStatus :=
       match headProbe with
-      | .reached sameTarget => classifyReached sameTarget
+      | .reached sameTarget => if sameTarget then .redirected else .working
       | .failed e =>
-          -- The first probe failed: decide whether to retry with a full fetch.
-          -- A status-carrying failure OR a redirect-budget exhaustion is
-          -- retried; any other failure is not.
           if retriable e then
             match getProbe with
             | .reached sameTarget => classifyReached sameTarget
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
 /- No consumed axioms. The behaviour this slice depends on — how a failed link
@@ -121,10 +121,12 @@
       match headProbe with
       | .reached sameTarget => classifyReached sameTarget
       | .failed e =>
-          -- The first probe failed: decide whether to retry with a full fetch.
-          -- A status-carrying failure OR a redirect-budget exhaustion is
-          -- retried; any other failure is not.
-          if retriable e then
+          let retry : Bool :=
+            match e with
+            | .statusError _ => false
+            | .redirectLoop  => true
+            | .otherFailure  => false
+          if retry then
             match getProbe with
             | .reached sameTarget => classifyReached sameTarget
             | .failed e2          => classifyUnhandled e2
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
 /- No consumed axioms. The behaviour this slice depends on — how a failed link
@@ -117,19 +117,7 @@
   ensures out = resolveLinkStatusSpec headProbe getProbe
   do
     -- impl-start
-    let out : LinkStatus :=
-      match headProbe with
-      | .reached sameTarget => classifyReached sameTarget
-      | .failed e =>
-          -- The first probe failed: decide whether to retry with a full fetch.
-          -- A status-carrying failure OR a redirect-budget exhaustion is
-          -- retried; any other failure is not.
-          if retriable e then
-            match getProbe with
-            | .reached sameTarget => classifyReached sameTarget
-            | .failed e2          => classifyUnhandled e2
-          else
-            classifyUnhandled e
+    let out : LinkStatus := .broken
     return out
     -- impl-end
 
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
 /- No consumed axioms. The behaviour this slice depends on — how a failed link
@@ -121,15 +121,17 @@
       match headProbe with
       | .reached sameTarget => classifyReached sameTarget
       | .failed e =>
-          -- The first probe failed: decide whether to retry with a full fetch.
-          -- A status-carrying failure OR a redirect-budget exhaustion is
-          -- retried; any other failure is not.
           if retriable e then
             match getProbe with
             | .reached sameTarget => classifyReached sameTarget
             | .failed e2          => classifyUnhandled e2
           else
-            classifyUnhandled e
+            match e with
+            | .statusError 401 => .working
+            | .statusError 503 => .broken
+            | .statusError _   => .broken
+            | .redirectLoop    => .broken
+            | .otherFailure    => .broken
     return out
     -- impl-end
 
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
 /- No consumed axioms. The behaviour this slice depends on — how a failed link
@@ -120,16 +120,7 @@
     let out : LinkStatus :=
       match headProbe with
       | .reached sameTarget => classifyReached sameTarget
-      | .failed e =>
-          -- The first probe failed: decide whether to retry with a full fetch.
-          -- A status-carrying failure OR a redirect-budget exhaustion is
-          -- retried; any other failure is not.
-          if retriable e then
-            match getProbe with
-            | .reached sameTarget => classifyReached sameTarget
-            | .failed e2          => classifyUnhandled e2
-          else
-            classifyUnhandled e
+      | .failed e => classifyUnhandled e
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The behaviour this slice depends on — how a failed link
   probe is CLASSIFIED, and which failures the lightweight first attempt retries
   with a full fetch — is modeled DEEPLY in the `pure` region (`classifyReached`,
   `classifyUnhandled`, and the inline retry predicate) over an abstract failure
   carrier, and validated == the real failure hierarchy by G-AX (an A-reference,
   mapping.md §3). It carries no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- A failed probe of a remote target, in the three shapes the desired behaviour
   distinguishes:
     * `statusError code` — the server answered with an error status `code`
       (the only observed field is the status number);
     * `redirectLoop` — the target kept redirecting until the redirect budget
       was exhausted, so no response was obtained;
     * `otherFailure` — any other failure (connection, TLS, decoding, …).
   The behaviour distinguishes only these three, because only these three are
   routed differently by the classification below. -/
inductive RequestFailure where
  | statusError (code : Nat)
  | redirectLoop
  | otherFailure
  deriving DecidableEq

/- The outcome of one attempt to probe a target:
     * `reached sameTarget` — a response was obtained and accepted; `sameTarget`
       records whether the final location equals the requested one (`true`) or
       the request was sent onward to a different location (`false`);
     * `failed e` — the attempt failed in one of the ways above. -/
inductive Probe where
  | reached (sameTarget : Bool)
  | failed (e : RequestFailure)
  deriving DecidableEq

/- The status a link is reported with. -/
inductive LinkStatus where
  | working
  | ignored
  | broken
  | redirected
  deriving DecidableEq

/- Classification of a successfully reached target: a target whose final
   location is the requested one is `working`; one that was sent onward to a
   different final location is `redirected`. -/
def classifyReached (sameTarget : Bool) : LinkStatus :=
  if sameTarget then .working else .redirected

/- Classification of a failure that was NOT retried (it reached the top-level
   handler): a status-carrying failure is read by its code — an authorization
   challenge (401) is still treated as `working`, a temporary-unavailable
   response (503) is `ignored`, any other status is a failed link; a
   redirect-budget exhaustion and every other failure are also failed links. -/
def classifyUnhandled (e : RequestFailure) : LinkStatus :=
  match e with
  | .statusError 401 => .working
  | .statusError 503 => .ignored
  | .statusError _   => .broken
  | .redirectLoop    => .broken
  | .otherFailure    => .broken

/- A failure should be retried with a full fetch when it is a status-carrying
   failure OR a redirect-budget exhaustion — both are scenarios where a server
   that mishandles the lightweight first attempt may still serve a full fetch.
   Any other failure is not retried. -/
def retriable (e : RequestFailure) : Bool :=
  match e with
  | .statusError _ => true
  | .redirectLoop  => true
  | .otherFailure  => false

/- The reported status of a link, as a function of the lightweight first probe
   (`headProbe`) and, when the first probe's failure is retriable, a full-fetch
   second probe (`getProbe`):
     * if the first probe reached the target, classify it;
     * if it failed retriably, perform the second probe and classify ITS outcome
       (a second-probe failure reaches the top-level handler);
     * if it failed non-retriably, that failure reaches the top-level handler. -/
def resolveLinkStatusSpec (headProbe getProbe : Probe) : LinkStatus :=
  match headProbe with
  | .reached sameTarget => classifyReached sameTarget
  | .failed e =>
      if retriable e then
        match getProbe with
        | .reached sameTarget => classifyReached sameTarget
        | .failed e2          => classifyUnhandled e2
      else
        classifyUnhandled e

@[grind] lemma resolveLinkStatusSpec_reached (b : Bool) (g : Probe) :
    resolveLinkStatusSpec (.reached b) g = classifyReached b := rfl
@[grind] lemma resolveLinkStatusSpec_failed (e : RequestFailure) (g : Probe) :
    resolveLinkStatusSpec (.failed e) g =
      (if retriable e then
        (match g with
         | .reached b => classifyReached b
         | .failed e2 => classifyUnhandled e2)
      else classifyUnhandled e) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method resolveLinkStatus (headProbe : Probe) (getProbe : Probe) return (out : LinkStatus)
  ensures out = resolveLinkStatusSpec headProbe getProbe
  do
    -- impl-start
    let out : LinkStatus :=
      match headProbe with
      | .reached sameTarget => classifyReached sameTarget
      | .failed e =>
          -- The first probe failed: decide whether to retry with a full fetch.
          -- A status-carrying failure OR a redirect-budget exhaustion is
          -- retried; any other failure is not.
          if retriable e then
            match getProbe with
            | .reached sameTarget => classifyReached sameTarget
            | .failed e2          => classifyUnhandled e2
          else
            classifyUnhandled e
    return out
    -- impl-end

prove_correct resolveLinkStatus by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: resolveLinkStatus's postcondition is an EXACT functional equality (ensures out = resolveLinkStatusSpec headProbe getProbe). resolveLinkStatusSpec, retriable, classifyReached, classifyUnhandled, and the RequestFailure/Probe/LinkStatus carriers are all in the FROZEN pure region (byte-identical across every attack; same_spec=True for all 8 files). Therefore any impl that verifies is PROVABLY extensionally equal to the spec function on the whole finite input domain => no behaviorally-wrong impl can verify => there is NO verifying wrong impl whose faithful patch would need a resolve run. patches={} is correct and expected for an exact-equality spec, NOT missing evidence.

SAME-SPEC: True for atk_1..7 + atk_pc via swebench_unified.markers.same_spec (velvet backend).

### VERIFY RESULTS (bash scripts/lean_verify.sh <file>, run, concurrently in 2 batches of 4):
  atk_1 PREPATCH bug (retriable .redirectLoop=false) -> exit 1 FAIL, unsolved `ensures` goal. Reproduces the real prepatch: a redirect-loop HEAD is NOT retried, so classifyUnhandled .redirectLoop = broken while the spec routes through the GET retry to working. prepatch_reproduced=true.
  atk_2 boundary (401->broken on the GET-retry .failed e2 leg) -> exit 1 FAIL (atk_2.lean:139 unsolved goals).
  atk_3 boundary/control (swap working<->redirected on .reached) -> exit 1 FAIL.
  atk_4 control-flow-effect (retry ONLY .redirectLoop, drop statusError retry) -> exit 1 FAIL (atk_4.lean:138 unsolved goals).
  atk_5 ungrounded-oracle echo (constant .broken) -> exit 1 FAIL; goal shows LinkStatus.broken = resolveLinkStatusSpec headProbe getProbe.
  atk_6 boundary (503->broken on the head-unhandled non-retried leg) -> exit 1 FAIL (atk_6.lean:138 unsolved goals).
  atk_7 control-flow (no retry at all; classify head failure directly, ignore getProbe) -> exit 1 FAIL; goal shows match-on-headProbe != resolveLinkStatusSpec.
  atk_pc positive control (gold impl) -> exit 0 PASS (no-sorry, empty error output).

All 7 failures are genuine `ensures` unsolved-goal mismatches (error line at the prove_correct site), NOT syntax/parse errors. So 0 wrong impls verify; run_resolve was correctly not invoked for any (no verifying wrong impl exists to materialize a patch for).

REFINEMENT.MD AUDIT (step 3): legs A1/A2=R (Probe/LinkStatus bijection), A3/A4/A5=I (A4 is the changed op: inner except-set widened, modeled DEEPLY via retriable, not axiomatized), A6=A-reference+I (classifyUnhandled ~ top-level handler status read). NO kind-3 (inexpressible-changed-op) leg; no consumed axioms. Section B correctly asserts no kind-3.

G-AX A-REFERENCE VALIDATION: executed axiom_check.py against the REAL requests library -> exit 0, 'G-AX OK' over 13 boundary + 20000 fuzz failures. Confirms the soundness anchor: TooManyRedirects is NOT caught by `except HTTPError` but IS caught by `except (HTTPError, TooManyRedirects)`; HTTPError 401->working / 503->ignored / else->broken; TooManyRedirects & other Exception -> broken. The A-reference correspondence to the unchanged real callees holds.

CONCLUSION: verify => correct holds for this bundle. 7 distinct same-spec wrong impls (partial-domain/prepatch, two boundary, retry-inversion, no-retry, constant-echo) all fail to verify; positive control verifies; A-reference sound; no kind-3 legs. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The behaviour this slice depends on — how a failed link
   probe is CLASSIFIED, and which failures the lightweight first attempt retries
   with a full fetch — is modeled DEEPLY in the `pure` region (`classifyReached`,
   `classifyUnhandled`, and the inline retry predicate) over an abstract failure
   carrier, and validated == the real failure hierarchy by G-AX (an A-reference,
   mapping.md §3). It carries no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- A failed probe of a remote target, in the three shapes the desired behaviour
   distinguishes:
     * `statusError code` — the server answered with an error status `code`
       (the only observed field is the status number);
     * `redirectLoop` — the target kept redirecting until the redirect budget
       was exhausted, so no response was obtained;
     * `otherFailure` — any other failure (connection, TLS, decoding, …).
   The behaviour distinguishes only these three, because only these three are
   routed differently by the classification below. -/
inductive RequestFailure where
  | statusError (code : Nat)
  | redirectLoop
  | otherFailure
  deriving DecidableEq

/- The outcome of one attempt to probe a target:
     * `reached sameTarget` — a response was obtained and accepted; `sameTarget`
       records whether the final location equals the requested one (`true`) or
       the request was sent onward to a different location (`false`);
     * `failed e` — the attempt failed in one of the ways above. -/
inductive Probe where
  | reached (sameTarget : Bool)
  | failed (e : RequestFailure)
  deriving DecidableEq

/- The status a link is reported with. -/
inductive LinkStatus where
  | working
  | ignored
  | broken
  | redirected
  deriving DecidableEq

/- Classification of a successfully reached target: a target whose final
   location is the requested one is `working`; one that was sent onward to a
   different final location is `redirected`. -/
def classifyReached (sameTarget : Bool) : LinkStatus :=
  if sameTarget then .working else .redirected

/- Classification of a failure that was NOT retried (it reached the top-level
   handler): a status-carrying failure is read by its code — an authorization
   challenge (401) is still treated as `working`, a temporary-unavailable
   response (503) is `ignored`, any other status is a failed link; a
   redirect-budget exhaustion and every other failure are also failed links. -/
def classifyUnhandled (e : RequestFailure) : LinkStatus :=
  match e with
  | .statusError 401 => .working
  | .statusError 503 => .ignored
  | .statusError _   => .broken
  | .redirectLoop    => .broken
  | .otherFailure    => .broken

/- A failure should be retried with a full fetch when it is a status-carrying
   failure OR a redirect-budget exhaustion — both are scenarios where a server
   that mishandles the lightweight first attempt may still serve a full fetch.
   Any other failure is not retried. -/
def retriable (e : RequestFailure) : Bool :=
  match e with
  | .statusError _ => true
  | .redirectLoop  => true
  | .otherFailure  => false

/- The reported status of a link, as a function of the lightweight first probe
   (`headProbe`) and, when the first probe's failure is retriable, a full-fetch
   second probe (`getProbe`):
     * if the first probe reached the target, classify it;
     * if it failed retriably, perform the second probe and classify ITS outcome
       (a second-probe failure reaches the top-level handler);
     * if it failed non-retriably, that failure reaches the top-level handler. -/
def resolveLinkStatusSpec (headProbe getProbe : Probe) : LinkStatus :=
  match headProbe with
  | .reached sameTarget => classifyReached sameTarget
  | .failed e =>
      if retriable e then
        match getProbe with
        | .reached sameTarget => classifyReached sameTarget
        | .failed e2          => classifyUnhandled e2
      else
        classifyUnhandled e

@[grind] lemma resolveLinkStatusSpec_reached (b : Bool) (g : Probe) :
    resolveLinkStatusSpec (.reached b) g = classifyReached b := rfl
@[grind] lemma resolveLinkStatusSpec_failed (e : RequestFailure) (g : Probe) :
    resolveLinkStatusSpec (.failed e) g =
      (if retriable e then
        (match g with
         | .reached b => classifyReached b
         | .failed e2 => classifyUnhandled e2)
      else classifyUnhandled e) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method resolveLinkStatus (headProbe : Probe) (getProbe : Probe) return (out : LinkStatus)
  ensures out = resolveLinkStatusSpec headProbe getProbe
  do
    -- impl-start
    let out : LinkStatus :=
      match headProbe with
      | .reached sameTarget => classifyReached sameTarget
      | .failed e =>
          -- The first probe failed: decide whether to retry with a full fetch.
          -- A status-carrying failure OR a redirect-budget exhaustion is
          -- retried; any other failure is not.
          if retriable e then
            match getProbe with
            | .reached sameTarget => classifyReached sameTarget
            | .failed e2          => classifyUnhandled e2
          else
            classifyUnhandled e
    return out
    -- impl-end

prove_correct resolveLinkStatus by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: resolveLinkStatus's postcondition is an EXACT functional equality (ensures out = resolveLinkStatusSpec headProbe getProbe). resolveLinkStatusSpec, retriable, classifyReached, classifyUnhandled, and the RequestFailure/Probe/LinkStatus carriers are all in the FROZEN pure region (byte-identical across every attack; same_spec=True for all 8 files). Therefore any impl that verifies is PROVABLY extensionally equal to the spec function on the whole finite input domain => no behaviorally-wrong impl can verify => there is NO verifying wrong impl whose faithful patch would need a resolve run. patches={} is correct and expected for an exact-equality spec, NOT missing evidence.

SAME-SPEC: True for atk_1..7 + atk_pc via swebench_unified.markers.same_spec (velvet backend).

### VERIFY RESULTS (bash scripts/lean_verify.sh <file>, run, concurrently in 2 batches of 4):
  atk_1 PREPATCH bug (retriable .redirectLoop=false) -> exit 1 FAIL, unsolved `ensures` goal. Reproduces the real prepatch: a redirect-loop HEAD is NOT retried, so classifyUnhandled .redirectLoop = broken while the spec routes through the GET retry to working. prepatch_reproduced=true.
  atk_2 boundary (401->broken on the GET-retry .failed e2 leg) -> exit 1 FAIL (atk_2.lean:139 unsolved goals).
  atk_3 boundary/control (swap working<->redirected on .reached) -> exit 1 FAIL.
  atk_4 control-flow-effect (retry ONLY .redirectLoop, drop statusError retry) -> exit 1 FAIL (atk_4.lean:138 unsolved goals).
  atk_5 ungrounded-oracle echo (constant .broken) -> exit 1 FAIL; goal shows LinkStatus.broken = resolveLinkStatusSpec headProbe getProbe.
  atk_6 boundary (503->broken on the head-unhandled non-retried leg) -> exit 1 FAIL (atk_6.lean:138 unsolved goals).
  atk_7 control-flow (no retry at all; classify head failure directly, ignore getProbe) -> exit 1 FAIL; goal shows match-on-headProbe != resolveLinkStatusSpec.
  atk_pc positive control (gold impl) -> exit 0 PASS (no-sorry, empty error output).

All 7 failures are genuine `ensures` unsolved-goal mismatches (error line at the prove_correct site), NOT syntax/parse errors. So 0 wrong impls verify; run_resolve was correctly not invoked for any (no verifying wrong impl exists to materialize a patch for).

REFINEMENT.MD AUDIT (step 3): legs A1/A2=R (Probe/LinkStatus bijection), A3/A4/A5=I (A4 is the changed op: inner except-set widened, modeled DEEPLY via retriable, not axiomatized), A6=A-reference+I (classifyUnhandled ~ top-level handler status read). NO kind-3 (inexpressible-changed-op) leg; no consumed axioms. Section B correctly asserts no kind-3.

G-AX A-REFERENCE VALIDATION: executed axiom_check.py against the REAL requests library -> exit 0, 'G-AX OK' over 13 boundary + 20000 fuzz failures. Confirms the soundness anchor: TooManyRedirects is NOT caught by `except HTTPError` but IS caught by `except (HTTPError, TooManyRedirects)`; HTTPError 401->working / 503->ignored / else->broken; TooManyRedirects & other Exception -> broken. The A-reference correspondence to the unchanged real callees holds.

CONCLUSION: verify => correct holds for this bundle. 7 distinct same-spec wrong impls (partial-domain/prepatch, two boundary, retry-inversion, no-retry, constant-echo) all fail to verify; positive control verifies; A-reference sound; no kind-3 legs. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack found NO divergence between the modeled function resolveLinkStatusSpec and the real post-patch check_uri (gold patch at base_commit 3ea1ec8, verified source).

Real post-patch flow: try{HEAD.raise_for_status} except (HTTPError, TooManyRedirects){GET.raise_for_status}; outer except HTTPError (401->working, 503->ignored, else broken)/except Exception(->broken); on success response.url.rstrip('/')==req_url.rstrip('/') -> working else redirected.

Case-by-case equivalence over the entire input domain (headProbe x getProbe, each reached b | failed{statusError code|redirectLoop|otherFailure}):
 1. HEAD reached -> classifyReached b; real never retries on success. Match.
 2. HEAD failed retriable (statusError=HTTPError, redirectLoop=TooManyRedirects) -> GET retry; GET reached->classifyReached, GET failed->classifyUnhandled (2nd failure hits outer handler). retriable exactly = inner catch-set membership (statusError->true, redirectLoop->true, otherFailure->false). Match.
 3. HEAD failed non-retriable (otherFailure) -> propagates to outer except Exception -> broken = classifyUnhandled otherFailure. Match.
 4. classifyUnhandled: statusError 401->working, 503->ignored, else broken; redirectLoop/otherFailure not HTTPError -> broken. Matches outer handler exactly (only 401/503 equality classes are read, so Nat carrier loses no observed distinction).

Verified facts:
 - same_spec(Solution.lean, Solution_prepatch.lean, velvet backend) = True (spec regions byte-identical; the mutation lives only in the impl region, as required).
 - Solution.lean elaborates clean via scripts/lean_verify.sh (exit 0, no sorry/error).
 - requests.exceptions: TooManyRedirects is NOT a subclass of HTTPError; both derive from RequestException->Exception (confirmed with real requests import). This grounds redirectLoop as a distinct retriable failure and is precisely the discriminating change the gold patch makes (widening inner except HTTPError -> except (HTTPError, TooManyRedirects)).
 - Prepatch models retriable .redirectLoop=false and correctly FAILS prove_correct on a .failed .redirectLoop first probe whose full fetch reaches the target (G-DIFF/G-MUT witness), matching the F2P test_TooManyRedirects_on_HEAD semantics.

conf_skip=true is justified (sole observable is live-network link status; no network-free R/I shadow). The spec is neither too strong nor drifted: it is exactly as tight as the real callee behavior on the modeled boundary. No FAITHFULNESS defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit = widen inner `except HTTPError:` to `except (HTTPError, TooManyRedirects):` in check_uri() so a HEAD attempt that exhausts the redirect budget (TooManyRedirects) is retried with a full GET instead of being reported broken. The PUBLIC problem_statement already discloses this verbatim: it names the exception type `TooManyRedirects`, states the GET fallback is currently skipped and the link 'reported as broken', and says the fix 'extends the except clause to retry with a GET request for such scenarios.' Thus the entire discriminating change is public prior to the spec view.

Spec-view review (Solution.lean spec region + refinement.md + mapping.md):
- `retriable .redirectLoop = true` (Solution.lean:75-79) encodes exactly the public behavior (redirect-loop failure is now retried). This is the gold-edit behavior but it does NOT exceed problem_statement, which already names TooManyRedirects and the GET-retry.
- `resolveLinkStatusSpec` / `classifyReached` / `classifyUnhandled` model the HEAD-then-GET dispatch and the top-level handler's status reading (401->working, 503->ignored, else broken). These describe UNCHANGED pre-existing behavior of check_uri, not the gold edit; they are legitimate spec context, not a leak of the edit.
- refinement.md/mapping.md restate the same public fact (inner catch-set widened by adding TooManyRedirects) and cite base_commit repo source; spec_provenance='cold' (problem_statement + gold patch + repo source). These reference the gold patch for the auditor's derivation but the disclosed discriminator is already fully in problem_statement.

No spec-view line reveals a gold-edit specific that is absent from the public problem_statement. The 401/503 status routing is unchanged pre-existing repo behavior (not part of the diff), so it is not gold-edit leakage. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
