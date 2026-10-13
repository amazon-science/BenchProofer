# P2 adversarial audit — django__django-16899

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_2_partial.lean`, `atk_3_ctrlflow.lean`, `atk_4_typo.lean`, `atk_5_swapargs.lean`, `atk_7_reorder.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of
@@ -96,19 +96,13 @@
                                    label name adminName modelLabel
   do
     -- impl-start
-    -- An invokable entry, or one naming an attribute of the administrator or of
-    -- the administered model class, is acceptable outright. Otherwise the entry
-    -- must be recognised by the model's field registry; when it is not, report
-    -- it with the diagnostic text quoting label, name, administrator type, and
-    -- model label, in that order.
     let result : Option (List Char) :=
       if isCallable then none
       else if hasAttrAdmin then none
       else if hasAttrModel then none
       else if fieldUnknown then
         some ("The value of '".toList ++ label
-          ++ "' refers to '".toList ++ name
-          ++ "', which is not a callable, an attribute of '".toList ++ adminName
+          ++ "' is not a callable, an attribute of '".toList ++ adminName
           ++ "', or an attribute of '".toList ++ modelLabel
           ++ "'.".toList)
       else none
```

Attack 2 — `atk_2_partial.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of
@@ -96,22 +96,7 @@
                                    label name adminName modelLabel
   do
     -- impl-start
-    -- An invokable entry, or one naming an attribute of the administrator or of
-    -- the administered model class, is acceptable outright. Otherwise the entry
-    -- must be recognised by the model's field registry; when it is not, report
-    -- it with the diagnostic text quoting label, name, administrator type, and
-    -- model label, in that order.
-    let result : Option (List Char) :=
-      if isCallable then none
-      else if hasAttrAdmin then none
-      else if hasAttrModel then none
-      else if fieldUnknown then
-        some ("The value of '".toList ++ label
-          ++ "' refers to '".toList ++ name
-          ++ "', which is not a callable, an attribute of '".toList ++ adminName
-          ++ "', or an attribute of '".toList ++ modelLabel
-          ++ "'.".toList)
-      else none
+    let result : Option (List Char) := none
     return result
     -- impl-end
 
```

Attack 3 — `atk_3_ctrlflow.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of
@@ -96,22 +96,17 @@
                                    label name adminName modelLabel
   do
     -- impl-start
-    -- An invokable entry, or one naming an attribute of the administrator or of
-    -- the administered model class, is acceptable outright. Otherwise the entry
-    -- must be recognised by the model's field registry; when it is not, report
-    -- it with the diagnostic text quoting label, name, administrator type, and
-    -- model label, in that order.
+    -- control-flow-effect: report on the field-unknown branch even when the
+    -- registry recognises the name (fieldUnknown ignored), diverging from spec.
     let result : Option (List Char) :=
       if isCallable then none
       else if hasAttrAdmin then none
       else if hasAttrModel then none
-      else if fieldUnknown then
-        some ("The value of '".toList ++ label
+      else some ("The value of '".toList ++ label
           ++ "' refers to '".toList ++ name
           ++ "', which is not a callable, an attribute of '".toList ++ adminName
           ++ "', or an attribute of '".toList ++ modelLabel
           ++ "'.".toList)
-      else none
     return result
     -- impl-end
 
```

Attack 4 — `atk_4_typo.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of
@@ -96,18 +96,13 @@
                                    label name adminName modelLabel
   do
     -- impl-start
-    -- An invokable entry, or one naming an attribute of the administrator or of
-    -- the administered model class, is acceptable outright. Otherwise the entry
-    -- must be recognised by the model's field registry; when it is not, report
-    -- it with the diagnostic text quoting label, name, administrator type, and
-    -- model label, in that order.
     let result : Option (List Char) :=
       if isCallable then none
       else if hasAttrAdmin then none
       else if hasAttrModel then none
       else if fieldUnknown then
         some ("The value of '".toList ++ label
-          ++ "' refers to '".toList ++ name
+          ++ "' referx to '".toList ++ name
           ++ "', which is not a callable, an attribute of '".toList ++ adminName
           ++ "', or an attribute of '".toList ++ modelLabel
           ++ "'.".toList)
```

Attack 5 — `atk_5_swapargs.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of
@@ -96,11 +96,6 @@
                                    label name adminName modelLabel
   do
     -- impl-start
-    -- An invokable entry, or one naming an attribute of the administrator or of
-    -- the administered model class, is acceptable outright. Otherwise the entry
-    -- must be recognised by the model's field registry; when it is not, report
-    -- it with the diagnostic text quoting label, name, administrator type, and
-    -- model label, in that order.
     let result : Option (List Char) :=
       if isCallable then none
       else if hasAttrAdmin then none
@@ -108,8 +103,8 @@
       else if fieldUnknown then
         some ("The value of '".toList ++ label
           ++ "' refers to '".toList ++ name
-          ++ "', which is not a callable, an attribute of '".toList ++ adminName
-          ++ "', or an attribute of '".toList ++ modelLabel
+          ++ "', which is not a callable, an attribute of '".toList ++ modelLabel
+          ++ "', or an attribute of '".toList ++ adminName
           ++ "'.".toList)
       else none
     return result
```

Attack 6 — `atk_6_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of
@@ -96,22 +96,10 @@
                                    label name adminName modelLabel
   do
     -- impl-start
-    -- An invokable entry, or one naming an attribute of the administrator or of
-    -- the administered model class, is acceptable outright. Otherwise the entry
-    -- must be recognised by the model's field registry; when it is not, report
-    -- it with the diagnostic text quoting label, name, administrator type, and
-    -- model label, in that order.
+    -- ungrounded-oracle echo: delegate straight to the spec's own report fn.
     let result : Option (List Char) :=
-      if isCallable then none
-      else if hasAttrAdmin then none
-      else if hasAttrModel then none
-      else if fieldUnknown then
-        some ("The value of '".toList ++ label
-          ++ "' refers to '".toList ++ name
-          ++ "', which is not a callable, an attribute of '".toList ++ adminName
-          ++ "', or an attribute of '".toList ++ modelLabel
-          ++ "'.".toList)
-      else none
+      readonlyItemReport isCallable hasAttrAdmin hasAttrModel fieldUnknown
+                         label name adminName modelLabel
     return result
     -- impl-end
 
```

Attack 7 — `atk_7_reorder.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of
@@ -96,14 +96,10 @@
                                    label name adminName modelLabel
   do
     -- impl-start
-    -- An invokable entry, or one naming an attribute of the administrator or of
-    -- the administered model class, is acceptable outright. Otherwise the entry
-    -- must be recognised by the model's field registry; when it is not, report
-    -- it with the diagnostic text quoting label, name, administrator type, and
-    -- model label, in that order.
+    -- control-flow: isCallable acceptance moved after the field check, so a
+    -- callable entry with an unknown field is wrongly reported.
     let result : Option (List Char) :=
-      if isCallable then none
-      else if hasAttrAdmin then none
+      if hasAttrAdmin then none
       else if hasAttrModel then none
       else if fieldUnknown then
         some ("The value of '".toList ++ label
@@ -111,6 +107,7 @@
           ++ "', which is not a callable, an attribute of '".toList ++ adminName
           ++ "', or an attribute of '".toList ++ modelLabel
           ++ "'.".toList)
+      else if isCallable then none
       else none
     return result
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
-- (No axiomatized callees. The behaviour modeled here is a closed function of
--  its inputs. A model-administration validator inspects one configuration
--  entry and decides whether to report a problem and, if so, with what
--  descriptive text. The four runtime observations the decision depends on —
--  whether the entry is itself an invokable object, whether it names an
--  attribute of the administrator, whether it names an attribute of the
--  administered model class, and whether the model's field registry recognises
--  the name — are abstracted to the four boolean inputs of the method; the four
--  pieces of text quoted by the diagnostic (the entry's label, the entry's
--  name, the administrator's type name, and the model's label) are abstracted
--  to four `List Char` inputs. Each boolean is an R-refinement of a real
--  observation (callable / hasattr(admin) / hasattr(model) / field-registry
--  lookup), validated against the real objects by conformance_check.py
--  (G-CONF). Nothing is consumed as an axiom — see refinement.md §C and
--  mapping.md §3.)
-- axioms-end

-- pure-start
/- The exact diagnostic text produced for an entry that resolves to nothing
   usable on the administered model. It quotes, in order, the entry's label,
   the entry's name, the administrator's type name, and the administered
   model's label. The shape — naming the entry between the label and the
   "is not a callable …" clause — is the unified phrasing the public task
   description asks for (other configuration entries already report the name
   this way). The four quoted pieces are free inputs; only their arrangement
   into the message is specified here. -/
@[grind] def itemDiagnostic (label name adminName modelLabel : List Char) : List Char :=
  "The value of '".toList ++ label
    ++ "' refers to '".toList ++ name
    ++ "', which is not a callable, an attribute of '".toList ++ adminName
    ++ "', or an attribute of '".toList ++ modelLabel
    ++ "'.".toList

/- The report for one configuration entry: `none` when the entry is acceptable
   (no diagnostic), or `some msg` carrying the diagnostic text when it is not.

   Reading order, mirroring how the validator examines the entry:

   1. An invokable entry (`isCallable`) is acceptable.
   2. Otherwise, an entry naming an attribute of the administrator
      (`hasAttrAdmin`) is acceptable.
   3. Otherwise, an entry naming an attribute of the administered model class
      (`hasAttrModel`) is acceptable.
   4. Otherwise the entry must be a known field of the model. If the field
      registry does not recognise the name (`fieldUnknown`) the entry is
      unresolvable and is reported with `itemDiagnostic`; if the registry does
      recognise it, the entry is acceptable.

   The diagnostic's quoted pieces are exactly `label`, `name`, `adminName`,
   `modelLabel`. -/
@[grind] def readonlyItemReport
    (isCallable hasAttrAdmin hasAttrModel fieldUnknown : Bool)
    (label name adminName modelLabel : List Char) : Option (List Char) :=
  if isCallable then none
  else if hasAttrAdmin then none
  else if hasAttrModel then none
  else if fieldUnknown then some (itemDiagnostic label name adminName modelLabel)
  else none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Validate one entry of a model administrator's read-only configuration and
   decide how it is reported: acceptable (`none`), or a diagnostic carrying the
   text built by `itemDiagnostic` (`some msg`).

   Desired behaviour (the abstract contract; see `readonlyItemReport`): an
   invokable entry, an entry naming an attribute of the administrator, or an
   entry naming an attribute of the administered model class, is acceptable.
   Otherwise the entry must be a field recognised by the model's field
   registry; when the registry does not recognise the name the entry is
   reported, and the diagnostic quotes the entry's label, the entry's name, the
   administrator's type name, and the model's label — in that order.

   All eight inputs are read-only observations (none declared `mut`): the
   routine inspects them and returns the report for the entry; it mutates
   nothing (directive 5). The result is pinned exactly by `readonlyItemReport`. -/
method readonlyItemCheck
    (isCallable : Bool) (hasAttrAdmin : Bool) (hasAttrModel : Bool) (fieldUnknown : Bool)
    (label : List Char) (name : List Char) (adminName : List Char) (modelLabel : List Char)
    return (out : Option (List Char))
  ensures out = readonlyItemReport isCallable hasAttrAdmin hasAttrModel fieldUnknown
                                   label name adminName modelLabel
  do
    -- impl-start
    let result : Option (List Char) :=
      if isCallable then none
      else if hasAttrAdmin then none
      else if hasAttrModel then none
      else if fieldUnknown then
        some ("The value of '".toList ++ label
          ++ "' refers to '".toList ++ name
          ++ "', which is not a callable, an attribute of '".toList ++ adminName
          ++ "', or an attribute of '".toList ++ modelLabel
          ++ "'.".toList)
      else none
    return result
    -- impl-end

prove_correct readonlyItemCheck by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Tight spec: `ensures out = readonlyItemReport isCallable hasAttrAdmin hasAttrModel fieldUnknown label name adminName modelLabel` pins the output exactly as a function of all 8 inputs, and `itemDiagnostic` (pure region) is byte-identical to the gold-patched Python message. same_spec=True verified for all 8 files.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>, run as parallel bg jobs, batches of 4):
- pos_control.lean (gold message): EXIT 0 (verifies) — positive control passes.
- atk_1_prepatch.lean (prepatch: omits "refers to '<name>', which" segment): EXIT 1 (fails) — PREPATCH BUG REPRODUCED, matches Solution_prepatch.lean.
- atk_2_partial.lean (partial-domain: always `none`, never reports): EXIT 1.
- atk_3_ctrlflow.lean (control-flow-effect: reports on fieldUnknown branch ignoring fieldUnknown): EXIT 1.
- atk_4_typo.lean (boundary/message: 'referx' typo): EXIT 1.
- atk_5_swapargs.lean (swapped adminName/modelLabel string args): EXIT 1.
- atk_6_echo.lean (ungrounded-oracle echo: body = readonlyItemReport ... verbatim): EXIT 0 (verifies).
- atk_7_reorder.lean (control-flow: isCallable acceptance moved after field check): EXIT 1.

6 distinct genuinely-wrong impls (partial-domain, two control-flow, message typo, swapped-args, plus the prepatch) all FAIL to verify. The ONLY verifying wrong-impl is atk_6_echo, which is behaviorally identical to the gold oracle.

RESOLVE (protocol step 2 — mandatory for every verifying impl): atk_6_echo's faithful refined patch is BYTE-IDENTICAL to the gold patch (confirmed gold==echo patch string). Official harness run (python -m swebench_unified.run_evaluation, namespace swebench, image swebench/sweb.eval.x86_64.django_1776_django-16899:latest, run_id sbu-manual-echo-16899) -> report.json resolved=TRUE: FAIL_TO_PASS {test_nonexistent_field, test_nonexistent_field_on_inline} both success, all PASS_TO_PASS success, 0 failures. Report: experiments/logs/run_evaluation/sbu-manual-echo-16899/sbu_patch/django__django-16899/report.json. NOTE: the harness.run_resolve() helper twice returned COMPLETED=False 'no report ... harness error or image pull failure'; root cause is a concurrent-audit docker image-layer cleanup race (ImageNotFound 404 for an intermediate sha during post-run cleanup while 62 containers were live), NOT a resolve failure — the direct harness invocation completed and wrote the authoritative report shown above. Since the sole verifying impl's faithful patch RESOLVES, there is no verify-not-correct gap; a resolving echo of the gold is not a weakness (2026-08-06 G-PANEL-1/eq policy).

LEG AUDIT (refinement.md): meta.json axioms=[] and deep_model_references=[] -> NO A-legs; G-AX correctly reports skip (nothing to correspond to a real callee). Rows 1-4 = R (none<->[], some<->[Error], the four boolean observations R-refine callable/hasattr(obj)/hasattr(obj.model)/get_field-raises; unchanged branches). Row 5 = R+I (literal segments byte-identical = I; four free-string ++ insertions = R, str<->List Char). No kind-3 (all changed ops expressible). same_spec correctly guards the pure region: tampering itemDiagnostic text -> same_spec False, confirming attacks edited ONLY the impl region and froze axioms/pure/pre/post byte-identical. G-CONF is the mechanical R/I refuter (conf_skip=false).

Verdict SOUND: >=5 (7) same-spec attacks run; the correct positive control verifies; the prepatch is reproduced; the single verifying wrong-impl's materialized faithful patch RESOLVES under the official harness; refinement legs are all R/I with no A-legs and no kind-3.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_2_partial.lean`, `atk_3_ctrlflow.lean`, `atk_4_typo.lean`, `atk_5_swapargs.lean`, `atk_7_reorder.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_partial.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_ctrlflow.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_typo.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_swapargs.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7_reorder.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a closed function of
--  its inputs. A model-administration validator inspects one configuration
--  entry and decides whether to report a problem and, if so, with what
--  descriptive text. The four runtime observations the decision depends on —
--  whether the entry is itself an invokable object, whether it names an
--  attribute of the administrator, whether it names an attribute of the
--  administered model class, and whether the model's field registry recognises
--  the name — are abstracted to the four boolean inputs of the method; the four
--  pieces of text quoted by the diagnostic (the entry's label, the entry's
--  name, the administrator's type name, and the model's label) are abstracted
--  to four `List Char` inputs. Each boolean is an R-refinement of a real
--  observation (callable / hasattr(admin) / hasattr(model) / field-registry
--  lookup), validated against the real objects by conformance_check.py
--  (G-CONF). Nothing is consumed as an axiom — see refinement.md §C and
--  mapping.md §3.)
-- axioms-end

-- pure-start
/- The exact diagnostic text produced for an entry that resolves to nothing
   usable on the administered model. It quotes, in order, the entry's label,
   the entry's name, the administrator's type name, and the administered
   model's label. The shape — naming the entry between the label and the
   "is not a callable …" clause — is the unified phrasing the public task
   description asks for (other configuration entries already report the name
   this way). The four quoted pieces are free inputs; only their arrangement
   into the message is specified here. -/
@[grind] def itemDiagnostic (label name adminName modelLabel : List Char) : List Char :=
  "The value of '".toList ++ label
    ++ "' refers to '".toList ++ name
    ++ "', which is not a callable, an attribute of '".toList ++ adminName
    ++ "', or an attribute of '".toList ++ modelLabel
    ++ "'.".toList

/- The report for one configuration entry: `none` when the entry is acceptable
   (no diagnostic), or `some msg` carrying the diagnostic text when it is not.

   Reading order, mirroring how the validator examines the entry:

   1. An invokable entry (`isCallable`) is acceptable.
   2. Otherwise, an entry naming an attribute of the administrator
      (`hasAttrAdmin`) is acceptable.
   3. Otherwise, an entry naming an attribute of the administered model class
      (`hasAttrModel`) is acceptable.
   4. Otherwise the entry must be a known field of the model. If the field
      registry does not recognise the name (`fieldUnknown`) the entry is
      unresolvable and is reported with `itemDiagnostic`; if the registry does
      recognise it, the entry is acceptable.

   The diagnostic's quoted pieces are exactly `label`, `name`, `adminName`,
   `modelLabel`. -/
@[grind] def readonlyItemReport
    (isCallable hasAttrAdmin hasAttrModel fieldUnknown : Bool)
    (label name adminName modelLabel : List Char) : Option (List Char) :=
  if isCallable then none
  else if hasAttrAdmin then none
  else if hasAttrModel then none
  else if fieldUnknown then some (itemDiagnostic label name adminName modelLabel)
  else none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Validate one entry of a model administrator's read-only configuration and
   decide how it is reported: acceptable (`none`), or a diagnostic carrying the
   text built by `itemDiagnostic` (`some msg`).

   Desired behaviour (the abstract contract; see `readonlyItemReport`): an
   invokable entry, an entry naming an attribute of the administrator, or an
   entry naming an attribute of the administered model class, is acceptable.
   Otherwise the entry must be a field recognised by the model's field
   registry; when the registry does not recognise the name the entry is
   reported, and the diagnostic quotes the entry's label, the entry's name, the
   administrator's type name, and the model's label — in that order.

   All eight inputs are read-only observations (none declared `mut`): the
   routine inspects them and returns the report for the entry; it mutates
   nothing (directive 5). The result is pinned exactly by `readonlyItemReport`. -/
method readonlyItemCheck
    (isCallable : Bool) (hasAttrAdmin : Bool) (hasAttrModel : Bool) (fieldUnknown : Bool)
    (label : List Char) (name : List Char) (adminName : List Char) (modelLabel : List Char)
    return (out : Option (List Char))
  ensures out = readonlyItemReport isCallable hasAttrAdmin hasAttrModel fieldUnknown
                                   label name adminName modelLabel
  do
    -- impl-start
    let result : Option (List Char) :=
      if isCallable then none
      else if hasAttrAdmin then none
      else if hasAttrModel then none
      else if fieldUnknown then
        some ("The value of '".toList ++ label
          ++ "' refers to '".toList ++ name
          ++ "', which is not a callable, an attribute of '".toList ++ adminName
          ++ "', or an attribute of '".toList ++ modelLabel
          ++ "'.".toList)
      else none
    return result
    -- impl-end

prove_correct readonlyItemCheck by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Tight spec: `ensures out = readonlyItemReport isCallable hasAttrAdmin hasAttrModel fieldUnknown label name adminName modelLabel` pins the output exactly as a function of all 8 inputs, and `itemDiagnostic` (pure region) is byte-identical to the gold-patched Python message. same_spec=True verified for all 8 files.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>, run as parallel bg jobs, batches of 4):
- pos_control.lean (gold message): EXIT 0 (verifies) — positive control passes.
- atk_1_prepatch.lean (prepatch: omits "refers to '<name>', which" segment): EXIT 1 (fails) — PREPATCH BUG REPRODUCED, matches Solution_prepatch.lean.
- atk_2_partial.lean (partial-domain: always `none`, never reports): EXIT 1.
- atk_3_ctrlflow.lean (control-flow-effect: reports on fieldUnknown branch ignoring fieldUnknown): EXIT 1.
- atk_4_typo.lean (boundary/message: 'referx' typo): EXIT 1.
- atk_5_swapargs.lean (swapped adminName/modelLabel string args): EXIT 1.
- atk_6_echo.lean (ungrounded-oracle echo: body = readonlyItemReport ... verbatim): EXIT 0 (verifies).
- atk_7_reorder.lean (control-flow: isCallable acceptance moved after field check): EXIT 1.

6 distinct genuinely-wrong impls (partial-domain, two control-flow, message typo, swapped-args, plus the prepatch) all FAIL to verify. The ONLY verifying wrong-impl is atk_6_echo, which is behaviorally identical to the gold oracle.

RESOLVE (protocol step 2 — mandatory for every verifying impl): atk_6_echo's faithful refined patch is BYTE-IDENTICAL to the gold patch (confirmed gold==echo patch string). Official harness run (python -m swebench_unified.run_evaluation, namespace swebench, image swebench/sweb.eval.x86_64.django_1776_django-16899:latest, run_id sbu-manual-echo-16899) -> report.json resolved=TRUE: FAIL_TO_PASS {test_nonexistent_field, test_nonexistent_field_on_inline} both success, all PASS_TO_PASS success, 0 failures. Report: experiments/logs/run_evaluation/sbu-manual-echo-16899/sbu_patch/django__django-16899/report.json. NOTE: the harness.run_resolve() helper twice returned COMPLETED=False 'no report ... harness error or image pull failure'; root cause is a concurrent-audit docker image-layer cleanup race (ImageNotFound 404 for an intermediate sha during post-run cleanup while 62 containers were live), NOT a resolve failure — the direct harness invocation completed and wrote the authoritative report shown above. Since the sole verifying impl's faithful patch RESOLVES, there is no verify-not-correct gap; a resolving echo of the gold is not a weakness (2026-08-06 G-PANEL-1/eq policy).

LEG AUDIT (refinement.md): meta.json axioms=[] and deep_model_references=[] -> NO A-legs; G-AX correctly reports skip (nothing to correspond to a real callee). Rows 1-4 = R (none<->[], some<->[Error], the four boolean observations R-refine callable/hasattr(obj)/hasattr(obj.model)/get_field-raises; unchanged branches). Row 5 = R+I (literal segments byte-identical = I; four free-string ++ insertions = R, str<->List Char). No kind-3 (all changed ops expressible). same_spec correctly guards the pure region: tampering itemDiagnostic text -> same_spec False, confirming attacks edited ONLY the impl region and froze axioms/pure/pre/post byte-identical. G-CONF is the mechanical R/I refuter (conf_skip=false).

Verdict SOUND: >=5 (7) same-spec attacks run; the correct positive control verifies; the prepatch is reproduced; the single verifying wrong-impl's materialized faithful patch RESOLVES under the official harness; refinement legs are all R/I with no A-legs and no kind-3.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check of the modeled function readonlyItemCheck (readonlyItemReport/itemDiagnostic) against the real BaseModelAdminChecks._check_readonly_fields_item at base_commit d3d17342 (verified git show of checks.py:761).

Spec integrity: same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True — the frozen spec region is byte-identical between patched and prepatch bundles; only the impl region differs (prepatch omits the "refers to '<name>', which" segment), so the discriminator is genuine and the spec is not tuned to the impl.

Routing fidelity: model order isCallable→hasAttrAdmin→hasAttrModel→fieldUnknown exactly mirrors the real short-circuit chain `if callable(field_name) / elif hasattr(obj,…) / elif hasattr(obj.model,…) / else try get_field except FieldDoesNotExist`. [] ↔ none, single checks.Error(msg) ↔ some msg.

Message fidelity: itemDiagnostic's literal segments, split at the four insertion points, reproduce the GOLD-PATCHED format string "The value of '%s' refers to '%s', which is not a callable, an attribute of '%s', or an attribute of '%s'." byte-for-byte (confirmed against dataset gold patch), with argument order label, field_name(name), obj.__class__.__name__(adminName), obj.model._meta.label(modelLabel). Matches.

Divergence search: (a) %-injection — real code uses `%`-interpolation where only the format string's own %s are consumed and argument-embedded % is literal; model concatenation is likewise literal. Conformance fuzz alphabet includes %,',",[,] and found 0 disagreements over 100,006 inputs (seed=16899). (b) The four observations as free booleans over-approximate (unrealizable combos are handled harmlessly and cannot be reached by any real (obj,field_name)); this widens the input domain, not narrows the modeled behavior — no realizable input diverges. (c) Dropping the unchanged obj=/id="admin.E035" Error args makes the spec strictly WEAKER, not stronger — not a faithfulness (too-strong) defect, and those args are identical pre/post-patch so the F2P message comparison is unaffected.

No input found where the modeled function disagrees with the real callee. The spec is not too strong and does not drift from real repo behavior. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (0 hard_failures) and same_spec(Solution.lean, Solution_prepatch.lean)=True — spec region is byte-identical between patch/prepatch (only the impl-region message differs, as intended for G-DIFF).

Substantive gold-reconstruction analysis (G-PANEL-3): the gold edit inserts field_name into the readonly_fields error message, turning "The value of '%s' is not a callable, an attribute of '%s', or an attribute of '%s'." into "The value of '%s' refers to '%s', which is not a callable, an attribute of '%s', or an attribute of '%s'." The spec view's `itemDiagnostic` encodes the exact post-patch target string. However, the PUBLIC problem_statement already contains every ingredient of that string:
  (1) the verbatim pre-patch message with example "The value of 'readonly_fields[0]' is not a callable, an attribute of 'CityInline', or an attribute of 'admin_checks.City'.";
  (2) the verbatim unification template from a sibling check "The value of 'list_editable[0]' refers to 'original_release', which is not contained in 'list_display'." (i.e. the exact "refers to '<name>', which" phrasing);
  (3) the explicit directive to "include the field name" and "unify this."
Composing (1)+(2) as (3) directs reconstructs the gold message verbatim from the solver-visible statement alone — the target wording is fully public.

The spec view adds NO edit-localization beyond the problem statement: no patched file path (django/contrib/admin/checks.py — screened absent), no repo symbol (_check_readonly_fields_item), no diff markers, no bug/fix narration. Prose comments describe abstract behavior and explicitly attribute the phrasing to "the public task description asks for" / "other configuration entries already report the name this way" — mirroring the problem statement, not the diff. A functional spec necessarily pins its output; here that output is exactly what the public statement already spells out, so encoding it leaks nothing beyond problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
