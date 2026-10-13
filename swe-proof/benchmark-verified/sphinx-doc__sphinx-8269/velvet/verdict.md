# P2 adversarial audit — sphinx-doc__sphinx-8269

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
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms: the only unchanged callee whose behaviour the decision
@@ -80,16 +80,10 @@
   ensures out = classify statusCode found
   do
     -- impl-start
-    -- Fragment-checking branch on a non-redirected response: `statusCode` is the
-    -- received HTTP status and `found` records whether the requested fragment is
-    -- present. An error status is routed to the status handler; a non-error
-    -- response lets fragment presence decide the outcome.
     let out : Verdict :=
       if isErrorStatus statusCode then
         (if statusCode = 401 then { status := .working, detail := .unauthorized, code := 0 }
-         else
-           (if statusCode = 503 then { status := .ignored, detail := .httpError, code := 0 }
-            else { status := .broken, detail := .httpError, code := 0 }))
+         else { status := .broken, detail := .httpError, code := 0 })
       else
         (if found then { status := .working, detail := .none, code := 0 }
          else { status := .broken, detail := .anchorNotFound, code := 0 })
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
 /- No consumed axioms: the only unchanged callee whose behaviour the decision
@@ -80,12 +80,8 @@
   ensures out = classify statusCode found
   do
     -- impl-start
-    -- Fragment-checking branch on a non-redirected response: `statusCode` is the
-    -- received HTTP status and `found` records whether the requested fragment is
-    -- present. An error status is routed to the status handler; a non-error
-    -- response lets fragment presence decide the outcome.
     let out : Verdict :=
-      if isErrorStatus statusCode then
+      if decide (400 ≤ statusCode ∧ statusCode < 500) then
         (if statusCode = 401 then { status := .working, detail := .unauthorized, code := 0 }
          else
            (if statusCode = 503 then { status := .ignored, detail := .httpError, code := 0 }
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
 /- No consumed axioms: the only unchanged callee whose behaviour the decision
@@ -80,18 +80,14 @@
   ensures out = classify statusCode found
   do
     -- impl-start
-    -- Fragment-checking branch on a non-redirected response: `statusCode` is the
-    -- received HTTP status and `found` records whether the requested fragment is
-    -- present. An error status is routed to the status handler; a non-error
-    -- response lets fragment presence decide the outcome.
     let out : Verdict :=
-      if isErrorStatus statusCode then
-        (if statusCode = 401 then { status := .working, detail := .unauthorized, code := 0 }
-         else
-           (if statusCode = 503 then { status := .ignored, detail := .httpError, code := 0 }
-            else { status := .broken, detail := .httpError, code := 0 }))
+      if found then { status := .working, detail := .none, code := 0 }
       else
-        (if found then { status := .working, detail := .none, code := 0 }
+        (if isErrorStatus statusCode then
+           (if statusCode = 401 then { status := .working, detail := .unauthorized, code := 0 }
+            else
+              (if statusCode = 503 then { status := .ignored, detail := .httpError, code := 0 }
+               else { status := .broken, detail := .httpError, code := 0 }))
          else { status := .broken, detail := .anchorNotFound, code := 0 })
     return out
     -- impl-end
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
 /- No consumed axioms: the only unchanged callee whose behaviour the decision
@@ -80,10 +80,6 @@
   ensures out = classify statusCode found
   do
     -- impl-start
-    -- Fragment-checking branch on a non-redirected response: `statusCode` is the
-    -- received HTTP status and `found` records whether the requested fragment is
-    -- present. An error status is routed to the status handler; a non-error
-    -- response lets fragment presence decide the outcome.
     let out : Verdict :=
       if isErrorStatus statusCode then
         (if statusCode = 401 then { status := .working, detail := .unauthorized, code := 0 }
@@ -92,7 +88,7 @@
             else { status := .broken, detail := .httpError, code := 0 }))
       else
         (if found then { status := .working, detail := .none, code := 0 }
-         else { status := .broken, detail := .anchorNotFound, code := 0 })
+         else { status := .broken, detail := .httpError, code := 0 })
     return out
     -- impl-end
 
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
 /- No consumed axioms: the only unchanged callee whose behaviour the decision
@@ -80,16 +80,10 @@
   ensures out = classify statusCode found
   do
     -- impl-start
-    -- Fragment-checking branch on a non-redirected response: `statusCode` is the
-    -- received HTTP status and `found` records whether the requested fragment is
-    -- present. An error status is routed to the status handler; a non-error
-    -- response lets fragment presence decide the outcome.
     let out : Verdict :=
       if isErrorStatus statusCode then
-        (if statusCode = 401 then { status := .working, detail := .unauthorized, code := 0 }
-         else
-           (if statusCode = 503 then { status := .ignored, detail := .httpError, code := 0 }
-            else { status := .broken, detail := .httpError, code := 0 }))
+        (if statusCode = 503 then { status := .ignored, detail := .httpError, code := 0 }
+         else { status := .broken, detail := .httpError, code := 0 })
       else
         (if found then { status := .working, detail := .none, code := 0 }
          else { status := .broken, detail := .anchorNotFound, code := 0 })
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
 /- No consumed axioms: the only unchanged callee whose behaviour the decision
@@ -80,16 +80,12 @@
   ensures out = classify statusCode found
   do
     -- impl-start
-    -- Fragment-checking branch on a non-redirected response: `statusCode` is the
-    -- received HTTP status and `found` records whether the requested fragment is
-    -- present. An error status is routed to the status handler; a non-error
-    -- response lets fragment presence decide the outcome.
     let out : Verdict :=
       if isErrorStatus statusCode then
         (if statusCode = 401 then { status := .working, detail := .unauthorized, code := 0 }
          else
            (if statusCode = 503 then { status := .ignored, detail := .httpError, code := 0 }
-            else { status := .broken, detail := .httpError, code := 0 }))
+            else { status := .broken, detail := .httpError, code := 1 }))
       else
         (if found then { status := .working, detail := .none, code := 0 }
          else { status := .broken, detail := .anchorNotFound, code := 0 })
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
 /- No consumed axioms: the only unchanged callee whose behaviour the decision
@@ -80,19 +80,7 @@
   ensures out = classify statusCode found
   do
     -- impl-start
-    -- Fragment-checking branch on a non-redirected response: `statusCode` is the
-    -- received HTTP status and `found` records whether the requested fragment is
-    -- present. An error status is routed to the status handler; a non-error
-    -- response lets fragment presence decide the outcome.
-    let out : Verdict :=
-      if isErrorStatus statusCode then
-        (if statusCode = 401 then { status := .working, detail := .unauthorized, code := 0 }
-         else
-           (if statusCode = 503 then { status := .ignored, detail := .httpError, code := 0 }
-            else { status := .broken, detail := .httpError, code := 0 }))
-      else
-        (if found then { status := .working, detail := .none, code := 0 }
-         else { status := .broken, detail := .anchorNotFound, code := 0 })
+    let out : Verdict := classify statusCode found
     return out
     -- impl-end
 
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms: the only unchanged callee whose behaviour the decision
@@ -80,19 +80,10 @@
   ensures out = classify statusCode found
   do
     -- impl-start
-    -- Fragment-checking branch on a non-redirected response: `statusCode` is the
-    -- received HTTP status and `found` records whether the requested fragment is
-    -- present. An error status is routed to the status handler; a non-error
-    -- response lets fragment presence decide the outcome.
     let out : Verdict :=
-      if isErrorStatus statusCode then
-        (if statusCode = 401 then { status := .working, detail := .unauthorized, code := 0 }
-         else
-           (if statusCode = 503 then { status := .ignored, detail := .httpError, code := 0 }
-            else { status := .broken, detail := .httpError, code := 0 }))
-      else
-        (if found then { status := .working, detail := .none, code := 0 }
-         else { status := .broken, detail := .anchorNotFound, code := 0 })
+      if isErrorStatus statusCode then classifyError statusCode
+      else (if found then { status := .working, detail := .none, code := 0 }
+            else { status := .broken, detail := .anchorNotFound, code := 0 })
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms: the only unchanged callee whose behaviour the decision
   depends on — the response-status validator — is modeled DEEPLY by `isErrorStatus`
   (an A-reference, validated == the real callee by axiom_check.py / G-AX), not
   assumed behind a consumed axiom. -/
-- axioms-end

-- pure-start
/- The four terminal verdicts a link check can reach in the modeled branch. -/
inductive Status
  | working
  | broken
  | ignored
  | redirected
deriving DecidableEq, Repr

/- The provenance of the human-readable detail attached to a verdict. The
   discriminating payload of this task is which of these is emitted when the
   response carries an error status: the *response-status detail*
   (`httpError`) versus the *fragment-absent* notice (`anchorNotFound`). -/
inductive Detail
  | none
  | httpError       -- the response-status message string
  | anchorNotFound  -- the "fragment not present" notice
  | unauthorized    -- the constant "treated as reachable" note
deriving DecidableEq, Repr

structure Verdict where
  status : Status
  detail : Detail
  code   : Int
deriving DecidableEq, Repr

/- Deep model (A-reference) of the response-status validator: a response is an
   error iff its status is in the 4xx/5xx range. Validated == the real callee
   by axiom_check.py (G-AX). -/
def isErrorStatus (sc : Int) : Bool :=
  decide (400 ≤ sc ∧ sc < 600)

/- The verdict for a response whose status is an error: a couple of statuses
   are reclassified (one treated as reachable, one as deliberately skipped),
   every other error status is a failure carrying the response-status detail.
   This is the unchanged status handler (an identical-op transliteration). -/
def classifyError (sc : Int) : Verdict :=
  if sc = 401 then { status := .working, detail := .unauthorized, code := 0 }
  else
    (if sc = 503 then { status := .ignored, detail := .httpError, code := 0 }
     else { status := .broken, detail := .httpError, code := 0 })

/- The full verdict of the fragment-checking branch on a non-redirected
   response, as a function of the response status `sc` and whether the
   requested fragment is present (`found`). An error status determines the
   outcome via `classifyError` regardless of fragment presence; on a non-error
   response fragment presence decides (present ⇒ reachable, absent ⇒ failure
   carrying the fragment-absent notice). -/
def classify (sc : Int) (found : Bool) : Verdict :=
  if isErrorStatus sc then classifyError sc
  else
    (if found then { status := .working, detail := .none, code := 0 }
     else { status := .broken, detail := .anchorNotFound, code := 0 })
-- pure-end

-- pre-conditions-start
-- (one block per modeled method; this method needs no precondition: every
--  Int status / Bool fragment-flag is a legitimate input.)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method checkFragmentBranch (statusCode : Int) (found : Bool) return (out : Verdict)
  ensures out = classify statusCode found
  do
    -- impl-start
    -- Fragment-checking branch on a non-redirected response: `statusCode` is the
    -- received HTTP status and `found` records whether the requested fragment is
    -- present. An error status is routed to the status handler; a non-error
    -- response lets fragment presence decide the outcome.
    let out : Verdict :=
      if isErrorStatus statusCode then
        (if statusCode = 401 then { status := .working, detail := .unauthorized, code := 0 }
         else
           (if statusCode = 503 then { status := .ignored, detail := .httpError, code := 0 }
            else { status := .broken, detail := .httpError, code := 0 }))
      else
        (if found then { status := .working, detail := .none, code := 0 }
         else { status := .broken, detail := .anchorNotFound, code := 0 })
    return out
    -- impl-end

prove_correct checkFragmentBranch by
  loom_solve
  simp only [classify, classifyError]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: postcondition is a TOTAL functional equality `out = classify statusCode found` with NO precondition. Therefore verify(impl) <=> impl == classify on every (Int, Bool) input; any verifying impl is behaviorally identical to the frozen spec (= gold behavior on the modeled non-redirected fragment branch). This structurally forecloses a `verified & wrong` impl.

PROTOCOL EXECUTED (all in scratch dir, same_spec=True for all 8 attacks, byte-identical spec/axioms/pure/pre/post — only impl region edited; verified with scripts/lean_verify.sh, cap 300s, concurrent batches <=4).

Positive control: pos_control.lean (=gold Solution.lean) -> lean_verify EXIT=0 (VERIFIES).
Prepatch: prepatch.lean (Solution_prepatch.lean, consults `found` without validating status first) -> lean_verify EXIT=1 (FAILS to verify => prepatch bug reproduced; the F2P discriminator statusCode=500,found=false: prepatch=broken/anchorNotFound vs spec=broken/httpError).

### WRONG IMPLS (each `bash scripts/lean_verify.sh <path>`):
- atk_1 (partial-domain: drops 503 reclassification, 503->broken/httpError) EXIT=1 FAIL. CEX: sc=503 spec=ignored/httpError.
- atk_2 (boundary: error-window only 400<=sc<500, 5xx slips to fragment branch) EXIT=1 FAIL. CEX: sc=500,found=true.
- atk_3 (control-flow-effect: consults `found` FIRST, so found wins over error status) EXIT=1 FAIL. CEX: sc=500,found=true -> working vs broken/httpError.
- atk_4 (ungrounded-oracle/wrong-detail: non-error absent -> httpError instead of anchorNotFound) EXIT=1 FAIL. CEX: sc=200,found=false.
- atk_5 (401 mishandled: 401 -> broken/httpError not working/unauthorized) EXIT=1 FAIL. CEX: sc=401.
- atk_6 (code-field defect: broken/httpError branch emits code:=1) EXIT=1 FAIL. CEX: sc=500,found=false -> code 1 vs 0.
- atk_7 (echo `return classify statusCode found` but the given proof script `loom_solve; simp only [...]` over-closes) EXIT=1 FAIL with `error: No goals to be solved` — non-verifying artifact, not a verifying candidate.

VERIFYING ATTACK (echo): atk_8 (`if isErrorStatus statusCode then classifyError statusCode else (found-routing)`, behaviorally == classify) -> lean_verify EXIT=0 VERIFIES. Per protocol its faithful refined patch was MATERIALIZED (= gold patch: insert `response.raise_for_status()` before check_anchor) and RUN through the official harness via swebench_unified.harness.run_resolve('sphinx-doc__sphinx-8269', patch): RESOLVED=True, COMPLETED=True, NOTE='resolved', ATTEMPTS=1, FLAKY=False. (First wrapper call returned completed=False 'no report' on a cold image; manual run_evaluation confirmed resolved 1/0, and the warm re-run of run_resolve returned resolved=True completed=True.) So the only verifying candidate resolves => spec NOT broken.

REFINEMENT.MD LEG AUDIT (step 3): A1 statusCode:Int<->response.status_code = R; A2 found:Bool<->check_anchor result = R; A3 isErrorStatus<->Response.raise_for_status raise boundary = A-reference; A4 classifyError 401/503/else<->except HTTPError handler = I; A5 found-routing<->non-error leg = I. Section B: no A-consumed rows (validator modeled deeply, check_anchor is opaque Bool input). Section C: no kind-3 steps. Every leg is R / A-reference / I. A-reference correspondence VALIDATED: axiom_check.py (G-AX) in the instance image -> 'G-AX OK: isErrorStatus deep model (== requests.raise_for_status) sound over [0,700)+boundary; HTTPError dispatch key == status_code on every raising status.' conformance_check.py (G-CONF) in image -> 'G-CONF OK: R/I shadow agrees with patch.diff on 100048 inputs (seed=8269), 0 disagreements.'

CONCLUSION: 8 same-spec attacks encoded & verified; 6 distinct wrong impls fail to verify (partial-domain, boundary, control-flow-effect, wrong-detail, 401-mishandle, code-field), 1 echo is a non-verifying proof-script artifact, 1 echo (atk_8) verifies and its faithful patch RESOLVES. A-legs' correspondence to real callees holds (G-AX + G-CONF pass). No verifying impl has a non-resolving faithful patch. Verdict SOUND.

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

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms: the only unchanged callee whose behaviour the decision
   depends on — the response-status validator — is modeled DEEPLY by `isErrorStatus`
   (an A-reference, validated == the real callee by axiom_check.py / G-AX), not
   assumed behind a consumed axiom. -/
-- axioms-end

-- pure-start
/- The four terminal verdicts a link check can reach in the modeled branch. -/
inductive Status
  | working
  | broken
  | ignored
  | redirected
deriving DecidableEq, Repr

/- The provenance of the human-readable detail attached to a verdict. The
   discriminating payload of this task is which of these is emitted when the
   response carries an error status: the *response-status detail*
   (`httpError`) versus the *fragment-absent* notice (`anchorNotFound`). -/
inductive Detail
  | none
  | httpError       -- the response-status message string
  | anchorNotFound  -- the "fragment not present" notice
  | unauthorized    -- the constant "treated as reachable" note
deriving DecidableEq, Repr

structure Verdict where
  status : Status
  detail : Detail
  code   : Int
deriving DecidableEq, Repr

/- Deep model (A-reference) of the response-status validator: a response is an
   error iff its status is in the 4xx/5xx range. Validated == the real callee
   by axiom_check.py (G-AX). -/
def isErrorStatus (sc : Int) : Bool :=
  decide (400 ≤ sc ∧ sc < 600)

/- The verdict for a response whose status is an error: a couple of statuses
   are reclassified (one treated as reachable, one as deliberately skipped),
   every other error status is a failure carrying the response-status detail.
   This is the unchanged status handler (an identical-op transliteration). -/
def classifyError (sc : Int) : Verdict :=
  if sc = 401 then { status := .working, detail := .unauthorized, code := 0 }
  else
    (if sc = 503 then { status := .ignored, detail := .httpError, code := 0 }
     else { status := .broken, detail := .httpError, code := 0 })

/- The full verdict of the fragment-checking branch on a non-redirected
   response, as a function of the response status `sc` and whether the
   requested fragment is present (`found`). An error status determines the
   outcome via `classifyError` regardless of fragment presence; on a non-error
   response fragment presence decides (present ⇒ reachable, absent ⇒ failure
   carrying the fragment-absent notice). -/
def classify (sc : Int) (found : Bool) : Verdict :=
  if isErrorStatus sc then classifyError sc
  else
    (if found then { status := .working, detail := .none, code := 0 }
     else { status := .broken, detail := .anchorNotFound, code := 0 })
-- pure-end

-- pre-conditions-start
-- (one block per modeled method; this method needs no precondition: every
--  Int status / Bool fragment-flag is a legitimate input.)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method checkFragmentBranch (statusCode : Int) (found : Bool) return (out : Verdict)
  ensures out = classify statusCode found
  do
    -- impl-start
    -- Fragment-checking branch on a non-redirected response: `statusCode` is the
    -- received HTTP status and `found` records whether the requested fragment is
    -- present. An error status is routed to the status handler; a non-error
    -- response lets fragment presence decide the outcome.
    let out : Verdict :=
      if isErrorStatus statusCode then
        (if statusCode = 401 then { status := .working, detail := .unauthorized, code := 0 }
         else
           (if statusCode = 503 then { status := .ignored, detail := .httpError, code := 0 }
            else { status := .broken, detail := .httpError, code := 0 }))
      else
        (if found then { status := .working, detail := .none, code := 0 }
         else { status := .broken, detail := .anchorNotFound, code := 0 })
    return out
    -- impl-end

prove_correct checkFragmentBranch by
  loom_solve
  simp only [classify, classifyError]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: postcondition is a TOTAL functional equality `out = classify statusCode found` with NO precondition. Therefore verify(impl) <=> impl == classify on every (Int, Bool) input; any verifying impl is behaviorally identical to the frozen spec (= gold behavior on the modeled non-redirected fragment branch). This structurally forecloses a `verified & wrong` impl.

PROTOCOL EXECUTED (all in scratch dir, same_spec=True for all 8 attacks, byte-identical spec/axioms/pure/pre/post — only impl region edited; verified with scripts/lean_verify.sh, cap 300s, concurrent batches <=4).

Positive control: pos_control.lean (=gold Solution.lean) -> lean_verify EXIT=0 (VERIFIES).
Prepatch: prepatch.lean (Solution_prepatch.lean, consults `found` without validating status first) -> lean_verify EXIT=1 (FAILS to verify => prepatch bug reproduced; the F2P discriminator statusCode=500,found=false: prepatch=broken/anchorNotFound vs spec=broken/httpError).

### WRONG IMPLS (each `bash scripts/lean_verify.sh <path>`):
- atk_1 (partial-domain: drops 503 reclassification, 503->broken/httpError) EXIT=1 FAIL. CEX: sc=503 spec=ignored/httpError.
- atk_2 (boundary: error-window only 400<=sc<500, 5xx slips to fragment branch) EXIT=1 FAIL. CEX: sc=500,found=true.
- atk_3 (control-flow-effect: consults `found` FIRST, so found wins over error status) EXIT=1 FAIL. CEX: sc=500,found=true -> working vs broken/httpError.
- atk_4 (ungrounded-oracle/wrong-detail: non-error absent -> httpError instead of anchorNotFound) EXIT=1 FAIL. CEX: sc=200,found=false.
- atk_5 (401 mishandled: 401 -> broken/httpError not working/unauthorized) EXIT=1 FAIL. CEX: sc=401.
- atk_6 (code-field defect: broken/httpError branch emits code:=1) EXIT=1 FAIL. CEX: sc=500,found=false -> code 1 vs 0.
- atk_7 (echo `return classify statusCode found` but the given proof script `loom_solve; simp only [...]` over-closes) EXIT=1 FAIL with `error: No goals to be solved` — non-verifying artifact, not a verifying candidate.

VERIFYING ATTACK (echo): atk_8 (`if isErrorStatus statusCode then classifyError statusCode else (found-routing)`, behaviorally == classify) -> lean_verify EXIT=0 VERIFIES. Per protocol its faithful refined patch was MATERIALIZED (= gold patch: insert `response.raise_for_status()` before check_anchor) and RUN through the official harness via swebench_unified.harness.run_resolve('sphinx-doc__sphinx-8269', patch): RESOLVED=True, COMPLETED=True, NOTE='resolved', ATTEMPTS=1, FLAKY=False. (First wrapper call returned completed=False 'no report' on a cold image; manual run_evaluation confirmed resolved 1/0, and the warm re-run of run_resolve returned resolved=True completed=True.) So the only verifying candidate resolves => spec NOT broken.

REFINEMENT.MD LEG AUDIT (step 3): A1 statusCode:Int<->response.status_code = R; A2 found:Bool<->check_anchor result = R; A3 isErrorStatus<->Response.raise_for_status raise boundary = A-reference; A4 classifyError 401/503/else<->except HTTPError handler = I; A5 found-routing<->non-error leg = I. Section B: no A-consumed rows (validator modeled deeply, check_anchor is opaque Bool input). Section C: no kind-3 steps. Every leg is R / A-reference / I. A-reference correspondence VALIDATED: axiom_check.py (G-AX) in the instance image -> 'G-AX OK: isErrorStatus deep model (== requests.raise_for_status) sound over [0,700)+boundary; HTTPError dispatch key == status_code on every raising status.' conformance_check.py (G-CONF) in image -> 'G-CONF OK: R/I shadow agrees with patch.diff on 100048 inputs (seed=8269), 0 disagreements.'

CONCLUSION: 8 same-spec attacks encoded & verified; 6 distinct wrong impls fail to verify (partial-domain, boundary, control-flow-effect, wrong-detail, 401-mishandle, code-field), 1 echo is a non-verifying proof-script artifact, 1 echo (atk_8) verifies and its faithful patch RESOLVES. A-legs' correspondence to real callees holds (G-AX + G-CONF pass). No verifying impl has a non-resolving faithful patch. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (same_spec with VelvetBackend = True); Solution.lean elaborates (lean_verify exit 0), so impl provably meets `out = classify statusCode found`. Verified `classify` against the real post-patch check_uri at base_commit 1e2ccd8f0 across the full modeled domain (non-redirected response, response received, found from check_anchor):
- sc∈[400,600), any found: real raise_for_status() raises HTTPError before check_anchor → except HTTPError dispatch on err.response.status_code(==sc): 401→working/'- unauthorized', 503→ignored/str(err), else→broken/str(err). Matches classifyError (401→working/unauthorized, 503→ignored/httpError, else→broken/httpError). found is correctly ignored on error status (raise precedes check_anchor).
- sc∉[400,600), found=false: no raise → check_anchor false → raise Exception('Anchor … not found') → except Exception(non-ssl) → broken/str(err). Matches broken/anchorNotFound.
- sc∉[400,600), found=true: no raise; response.url==req_url (non-redirected) → working/''. Matches working/none.
isErrorStatus boundary (400≤sc<600) is exact vs real raise_for_status source (4xx client / 5xx server), verified at 399/400/499/500/599/600 — no off-by-one. Detail abstraction preserves the discriminating httpError vs anchorNotFound distinction (the F2P test_raises_for_invalid_status: 500+absent must report httpError, not anchorNotFound). Scope exclusions (redirect/SSL/HEAD-GET-retry legs) are documented, unchanged by the patch, and not claimed by the spec. No diverging input found within the modeled domain; the spec is not too strong and does not drift from real callee behavior.

- sc∈[400,600), any found: real raise_for_status() raises HTTPError before check_anchor → except HTTPError dispatch on err.response.status_code(==sc): 401→working/'- unauthorized', 503→ignored/str(err), else→broken/str(err). Matches classifyError (401→working/unauthorized, 503→ignored/httpError, else→broken/httpError). found is correctly ignored on error status (raise precedes check_anchor).
- sc∉[400,600), found=false: no raise → check_anchor false → raise Exception('Anchor … not found') → except Exception(non-ssl) → broken/str(err). Matches broken/anchorNotFound.
- sc∉[400,600), found=true: no raise; response.url==req_url (non-redirected) → working/''. Matches working/none.
isErrorStatus boundary (400≤sc<600) is exact vs real raise_for_status source (4xx client / 5xx server), verified at 399/400/499/500/599/600 — no off-by-one. Detail abstraction preserves the discriminating httpError vs anchorNotFound distinction (the F2P test_raises_for_invalid_status: 500+absent must report httpError, not anchorNotFound). Scope exclusions (redirect/SSL/HEAD-GET-retry legs) are documented, unchanged by the patch, and not claimed by the spec. No diverging input found within the modeled domain; the spec is not too strong and does not drift from real callee behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rendered the solver-visible consumer spec view via markers.spec_view(Solution.lean, VelvetBackend): the impl block ('implementation elided — supplied by the consumer') and prove_correct proof ('proof elided') are both elided; only signatures, the pure models (Status/Detail/Verdict, isErrorStatus, classifyError, classify), the `ensures out = classify statusCode found`, and abstract comments remain. Mechanical G-LEAK screen PASSES (leakage.screen → passed=True, no hard failures) and same_spec(Solution, Solution_prepatch)=True. Checked every leak vector against the solver view: (L1) gold-diff line 'response.raise_for_status()' NOT present — the inserted validator is modeled abstractly as isErrorStatus(400≤sc<600), never named; no diff markers. (L2) patched file path 'sphinx/builders/linkcheck.py' absent; patched symbol 'check_uri' absent — spec identifiers (checkFragmentBranch, classify, isErrorStatus, classifyError) echo no repo symbol. (L3) comments describe behavior (response-status detail vs fragment-absent notice), no bug/fix narration. Semantic check: the spec necessarily encodes the desired post-patch behavior (error status routes to the HTTP-error handler regardless of `found`; non-error lets fragment presence decide) — but this behavior is ALREADY fully public in the problem_statement, which states 'Linkcheck should report HTTP errors instead of Anchor not found' and gives the concrete 404 → '404 Client Error…' vs 'Anchor test not found' contrast. The spec formalizes what the task already tells the solver; it does not reveal the specific code location or edit beyond problem_statement. The 401/503 dispatch and anchorNotFound path are pre-existing unchanged repo behavior, not edit-localization. refinement.md/mapping.md/verdict.md are auditor artifacts, not part of the solver spec view. No line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
