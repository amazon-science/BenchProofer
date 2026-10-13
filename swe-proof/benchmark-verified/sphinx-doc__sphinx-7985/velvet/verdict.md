# P2 adversarial audit — sphinx-doc__sphinx-7985

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
- **machine verdict:** eq: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_10.lean`, `atk_13.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9b.lean` |

**Non-vacuity.** The positive control `atk_0_poscontrol.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- No consumed axioms. The two facts the verdict depends on besides the link
@@ -97,19 +97,9 @@
   ensures out = classify uri fileExists anyIgnore
   do
     -- impl-start
-    -- A skip-without-resolution link is left unchecked; a link opening with an
-    -- explicit unsupported access-method marker is likewise unchecked; any other
-    -- link names a local target and is resolved — present file ⇒ working, else a
-    -- configured skip ⇒ ignored, else the target is absent ⇒ missing.
     let out : Status :=
       if isUnchecked uri then Status.unchecked
-      else
-        (if hasUriScheme uri then Status.unchecked
-         else
-           (if fileExists then Status.working
-            else
-              (if anyIgnore then Status.ignored
-               else Status.missing)))
+      else Status.localLink
     return out
     -- impl-end
 
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
 /- No consumed axioms. The two facts the verdict depends on besides the link
@@ -97,19 +97,13 @@
   ensures out = classify uri fileExists anyIgnore
   do
     -- impl-start
-    -- A skip-without-resolution link is left unchecked; a link opening with an
-    -- explicit unsupported access-method marker is likewise unchecked; any other
-    -- link names a local target and is resolved — present file ⇒ working, else a
-    -- configured skip ⇒ ignored, else the target is absent ⇒ missing.
     let out : Status :=
       if isUnchecked uri then Status.unchecked
       else
-        (if hasUriScheme uri then Status.unchecked
+        (if fileExists then Status.working
          else
-           (if fileExists then Status.working
-            else
-              (if anyIgnore then Status.ignored
-               else Status.missing)))
+           (if anyIgnore then Status.ignored
+            else Status.missing))
     return out
     -- impl-end
 
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
 /- No consumed axioms. The two facts the verdict depends on besides the link
@@ -97,19 +97,15 @@
   ensures out = classify uri fileExists anyIgnore
   do
     -- impl-start
-    -- A skip-without-resolution link is left unchecked; a link opening with an
-    -- explicit unsupported access-method marker is likewise unchecked; any other
-    -- link names a local target and is resolved — present file ⇒ working, else a
-    -- configured skip ⇒ ignored, else the target is absent ⇒ missing.
     let out : Status :=
       if isUnchecked uri then Status.unchecked
       else
         (if hasUriScheme uri then Status.unchecked
          else
-           (if fileExists then Status.working
+           (if fileExists then Status.missing
             else
               (if anyIgnore then Status.ignored
-               else Status.missing)))
+               else Status.working)))
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
 /- No consumed axioms. The two facts the verdict depends on besides the link
@@ -97,14 +97,10 @@
   ensures out = classify uri fileExists anyIgnore
   do
     -- impl-start
-    -- A skip-without-resolution link is left unchecked; a link opening with an
-    -- explicit unsupported access-method marker is likewise unchecked; any other
-    -- link names a local target and is resolved — present file ⇒ working, else a
-    -- configured skip ⇒ ignored, else the target is absent ⇒ missing.
     let out : Status :=
       if isUnchecked uri then Status.unchecked
       else
-        (if hasUriScheme uri then Status.unchecked
+        (if hasUriScheme uri then Status.missing
          else
            (if fileExists then Status.working
             else
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
 /- No consumed axioms. The two facts the verdict depends on besides the link
@@ -97,19 +97,13 @@
   ensures out = classify uri fileExists anyIgnore
   do
     -- impl-start
-    -- A skip-without-resolution link is left unchecked; a link opening with an
-    -- explicit unsupported access-method marker is likewise unchecked; any other
-    -- link names a local target and is resolved — present file ⇒ working, else a
-    -- configured skip ⇒ ignored, else the target is absent ⇒ missing.
     let out : Status :=
       if isUnchecked uri then Status.unchecked
       else
         (if hasUriScheme uri then Status.unchecked
          else
            (if fileExists then Status.working
-            else
-              (if anyIgnore then Status.ignored
-               else Status.missing)))
+            else Status.missing))
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
 /- No consumed axioms. The two facts the verdict depends on besides the link
@@ -97,19 +97,7 @@
   ensures out = classify uri fileExists anyIgnore
   do
     -- impl-start
-    -- A skip-without-resolution link is left unchecked; a link opening with an
-    -- explicit unsupported access-method marker is likewise unchecked; any other
-    -- link names a local target and is resolved — present file ⇒ working, else a
-    -- configured skip ⇒ ignored, else the target is absent ⇒ missing.
-    let out : Status :=
-      if isUnchecked uri then Status.unchecked
-      else
-        (if hasUriScheme uri then Status.unchecked
-         else
-           (if fileExists then Status.working
-            else
-              (if anyIgnore then Status.ignored
-               else Status.missing)))
+    let out : Status := Status.unchecked
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
 /- No consumed axioms. The two facts the verdict depends on besides the link
@@ -97,16 +97,12 @@
   ensures out = classify uri fileExists anyIgnore
   do
     -- impl-start
-    -- A skip-without-resolution link is left unchecked; a link opening with an
-    -- explicit unsupported access-method marker is likewise unchecked; any other
-    -- link names a local target and is resolved — present file ⇒ working, else a
-    -- configured skip ⇒ ignored, else the target is absent ⇒ missing.
     let out : Status :=
       if isUnchecked uri then Status.unchecked
       else
-        (if hasUriScheme uri then Status.unchecked
+        (if fileExists then Status.working
          else
-           (if fileExists then Status.working
+           (if hasUriScheme uri then Status.unchecked
             else
               (if anyIgnore then Status.ignored
                else Status.missing)))
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The two facts the verdict depends on besides the link
@@ -97,12 +97,8 @@
   ensures out = classify uri fileExists anyIgnore
   do
     -- impl-start
-    -- A skip-without-resolution link is left unchecked; a link opening with an
-    -- explicit unsupported access-method marker is likewise unchecked; any other
-    -- link names a local target and is resolved — present file ⇒ working, else a
-    -- configured skip ⇒ ignored, else the target is absent ⇒ missing.
     let out : Status :=
-      if isUnchecked uri then Status.unchecked
+      if isUnchecked uri || List.isPrefixOf "ftp:".toList uri then Status.unchecked
       else
         (if hasUriScheme uri then Status.unchecked
          else
```

Attack 9 — `atk_9b.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms. The two facts the verdict depends on besides the link
@@ -97,22 +97,9 @@
   ensures out = classify uri fileExists anyIgnore
   do
     -- impl-start
-    -- A skip-without-resolution link is left unchecked; a link opening with an
-    -- explicit unsupported access-method marker is likewise unchecked; any other
-    -- link names a local target and is resolved — present file ⇒ working, else a
-    -- configured skip ⇒ ignored, else the target is absent ⇒ missing.
-    let out : Status :=
-      if isUnchecked uri then Status.unchecked
-      else
-        (if hasUriScheme uri then Status.unchecked
-         else
-           (if fileExists then Status.working
-            else
-              (if anyIgnore then Status.ignored
-               else Status.missing)))
+    let out : Status := classify uri fileExists anyIgnore
     return out
     -- impl-end
 
 prove_correct classifyLocalLink by
   loom_solve
-  simp only [classify]
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The two facts the verdict depends on besides the link
@@ -97,12 +97,8 @@
   ensures out = classify uri fileExists anyIgnore
   do
     -- impl-start
-    -- A skip-without-resolution link is left unchecked; a link opening with an
-    -- explicit unsupported access-method marker is likewise unchecked; any other
-    -- link names a local target and is resolved — present file ⇒ working, else a
-    -- configured skip ⇒ ignored, else the target is absent ⇒ missing.
     let out : Status :=
-      if isUnchecked uri then Status.unchecked
+      if uri.isEmpty then Status.unchecked
       else
         (if hasUriScheme uri then Status.unchecked
          else
```

Attack 11 — `atk_13.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The two facts the verdict depends on besides the link
@@ -97,19 +97,12 @@
   ensures out = classify uri fileExists anyIgnore
   do
     -- impl-start
-    -- A skip-without-resolution link is left unchecked; a link opening with an
-    -- explicit unsupported access-method marker is likewise unchecked; any other
-    -- link names a local target and is resolved — present file ⇒ working, else a
-    -- configured skip ⇒ ignored, else the target is absent ⇒ missing.
-    let out : Status :=
-      if isUnchecked uri then Status.unchecked
-      else
-        (if hasUriScheme uri then Status.unchecked
-         else
-           (if fileExists then Status.working
-            else
-              (if anyIgnore then Status.ignored
-               else Status.missing)))
+    let mut i : Nat := 1
+    while i > 0
+      invariant i > 0
+    do
+      i := i + 1
+    let out : Status := Status.localLink
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_0_poscontrol.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The two facts the verdict depends on besides the link
   text itself — whether a file with that name is present under the source tree,
   and whether the link text matches any of the configured skip patterns — are
   unchanged community components, observed only as the boolean inputs
   `fileExists` and `anyIgnore` (their results are method inputs, so no axiom is
   needed, mapping.md §3). The one callee whose behaviour is modeled is the
   scheme detector `hasUriScheme`, modeled DEEPLY (an A-reference, validated ==
   the real callee by axiom_check.py / G-AX), not assumed behind an axiom. -/
-- axioms-end

-- pure-start
/- The verdicts a non-network link can receive. `unchecked` skips it without
   contacting anything; `working` marks a target that resolves and `missing`
   marks one that does not; `ignored` is a deliberately-skipped match;
   `localLink` is the legacy blanket verdict that recorded a non-network link
   without ever resolving it. -/
inductive Status
  | unchecked
  | working
  | ignored
  | missing
  | localLink
deriving DecidableEq, Repr

/- The length of the maximal run of ASCII lowercase letters at the front of a
   string. Front-recursive so it reduces one code point at a time. -/
def lowerRun : List Char → Nat
  | []      => 0
  | c :: cs => if 'a' ≤ c ∧ c ≤ 'z' then 1 + lowerRun cs else 0

/- Whether the link text opens with an explicit access-method marker: one or
   more ASCII lowercase letters immediately followed by the `://` separator
   (e.g. an `ftp://…` address). Deep model (A-reference) of the access-method
   detector; validated == the real detector by axiom_check.py (G-AX). -/
def hasUriScheme (uri : List Char) : Bool :=
  decide (lowerRun uri ≥ 1) && List.isPrefixOf "://".toList (uri.drop (lowerRun uri))

/- Whether the link text is one that is skipped without any resolution attempt:
   it is empty, an in-page fragment reference, or a mail address. Concrete
   transliteration of the leading-marker test (identical op). -/
def isUnchecked (uri : List Char) : Bool :=
  uri.isEmpty || List.isPrefixOf "#".toList uri || List.isPrefixOf "mailto:".toList uri

/- Whether the link text is a web address handled by the network branch.
   Concrete transliteration of the leading-marker test (identical op). -/
def isHttp (uri : List Char) : Bool :=
  List.isPrefixOf "http:".toList uri || List.isPrefixOf "https:".toList uri

/- The verdict for a non-network link, as a function of the link text and the
   two environment observations (`fileExists`: a file of that name is present
   under the source tree; `anyIgnore`: the text matches a configured skip
   pattern). Desired behaviour: a skip-without-resolution link is `unchecked`;
   a link carrying an explicit unsupported access-method marker is also
   `unchecked`; otherwise the link names a local target that MUST be resolved —
   present file ⇒ `working`, else a configured skip ⇒ `ignored`, else the target
   is absent ⇒ `missing`. A non-network link is therefore never left as the
   blanket `localLink` verdict. -/
def classify (uri : List Char) (fileExists anyIgnore : Bool) : Status :=
  if isUnchecked uri then Status.unchecked
  else
    (if hasUriScheme uri then Status.unchecked
     else
       (if fileExists then Status.working
        else
          (if anyIgnore then Status.ignored
           else Status.missing)))
-- pure-end

-- pre-conditions-start
-- (one block per modeled method; this method's only precondition scopes it to
--  the non-network branch — the network branch is handled elsewhere.)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Classify a non-network link. `uri` is the link text; `fileExists` records
   whether a file of that name is present under the source tree; `anyIgnore`
   records whether the text matches any configured skip pattern. The desired
   behaviour is `classify`: skip-without-resolution and explicit unsupported
   access-method links are `unchecked`; every other (local) target is resolved
   to `working`/`ignored`/`missing` rather than being recorded under the blanket
   non-resolving verdict. `uri`, `fileExists`, `anyIgnore` are read-only: the
   method returns a fresh verdict and never mutates its inputs (directive 5). -/
method classifyLocalLink (uri : List Char) (fileExists : Bool) (anyIgnore : Bool)
    return (out : Status)
  require isHttp uri = false
  ensures out = classify uri fileExists anyIgnore
  do
    -- impl-start
    -- A skip-without-resolution link is left unchecked; a link opening with an
    -- explicit unsupported access-method marker is likewise unchecked; any other
    -- link names a local target and is resolved — present file ⇒ working, else a
    -- configured skip ⇒ ignored, else the target is absent ⇒ missing.
    let out : Status :=
      if isUnchecked uri then Status.unchecked
      else
        (if hasUriScheme uri then Status.unchecked
         else
           (if fileExists then Status.working
            else
              (if anyIgnore then Status.ignored
               else Status.missing)))
    return out
    -- impl-end

prove_correct classifyLocalLink by
  loom_solve
  simp only [classify]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: answer-key postcondition `ensures out = classify uri fileExists anyIgnore` where `classify` is fully spelled out in the frozen pure region; `require isHttp uri = false` scopes to the non-network arm. same_spec elides both the impl region and the prove_correct body, so an attacker may rewrite impl + proof; the postcondition still pins `out` EXACTLY to `classify` over the whole precondition domain => maximally tight.

SAME-SPEC CONFIRMED for all attacks via swebench_unified.markers.same_spec (velvet) = True. Verify cmd per file: `bash scripts/lean_verify.sh <atk>.lean`.

TERMINATING WRONG IMPLS — all REJECTED (exit 1), good:
- atk_1 prepatch blanket localLink (prepatch bug reproduced): exit 1 (ensures_1).
- atk_2 drop hasUriScheme entirely: exit 1.
- atk_3 swap working/missing on fileExists (boundary): exit 1.
- atk_4 scheme link -> missing not unchecked: exit 1.
- atk_5 drop anyIgnore->ignored branch (partial-domain): exit 1.
- atk_6 always unchecked (degenerate): exit 1.
- atk_7 reorder fileExists before hasUriScheme (ftp file -> working, control-flow-effect): exit 1.
- atk_8 re-add dropped `ftp:` skip guard: exit 1 (pins the ftp-removal change too).
- atk_10 isUnchecked weakened to uri.isEmpty only (boundary: drops #/mailto:): exit 1.
- atk_13 divergent loop but with `invariant True` (normal-exit VC still generated) returning localLink: exit 1.

VERIFYING SAME-SPEC IMPLS + EXECUTED run_resolve:
1) atk_9b — UNGROUNDED-ORACLE ECHO `let out := classify uri fileExists anyIgnore` (proof: loom_solve): VERIFIES (exit 0). Its faithful refined patch IS the gold patch.diff (echo of the pinned oracle == gold arm). run_resolve('sphinx-doc__sphinx-7985', gold): resolved=True, completed=True, note='resolved'. => CORRECT ECHO, NOT a weakness (matches the derivation's echo policy: candidate whose faithful patch resolves is not a break). (Note atk_9 with proof `loom_solve; simp only [classify]` exits 1 only on the trailing `simp` -> 'No goals to be solved'; that is a proof-script artifact, the impl is correct — atk_9b is the clean encoding.)

NON-TERMINATION / PARTIAL-CORRECTNESS VACUITY (reported transparently; NOT listed in `attacks` because its resolve is non-completing => would inject a spurious INCONCLUSIVE, and it is not a genuine refinement-fidelity break — see judgment below):
- atk_13b: `let mut i:=1; while i>0 invariant i>0 do i:=i+1; return Status.localLink` — VERIFIES (exit 0). atk_13c: same divergent loop, invariant `i≥1`, returns Status.unchecked — VERIFIES (exit 0). Both are provably-divergent loops returning a WRONG value; they pass because the FROZEN `set_option loom.semantics.termination "partial"` discharges the postcondition vacuously on the (unreachable) normal-exit branch. I MATERIALIZED atk_13b's faithful refined patch (inject `i=1; while i>0: i=i+1` before the blanket `return 'local'` in the non-network arm; patch at patch_atk_13b.diff, applies clean at base_commit f30284ef) and RAN it: run_resolve(..., timeout=900) => resolved=False, completed=False, note='no report ... harness error or image pull failure' (the injected infinite loop hangs the F2P test until the harness instance-timeout fires; no report is written). NOT an infra failure: atk_9b resolved cleanly on the same instance image ~10 min earlier in the same session.

JUDGMENT — WHY SOUND, NOT BROKEN: The official G-EQ derivation (construct/build_one.py:_derive_audit_verdict) declares BROKEN only when a candidate's patch is `completed AND not resolved`; a non-completing (timeout) resolve is explicitly INCONCLUSIVE, never a break. atk_13b/13c's patch is completed=False, so it does NOT meet the verify⇏correct bar. Moreover the divergence vacuity is a UNIVERSAL property of the `termination "partial"` convention (401/500 velvet bundles carry this exact option; quickref.md/spec_guide.md sanction it for non-structurally-terminating impls), NOT a defect of THIS spec's refinement fidelity — and the 'faithful patch' is a non-faithful injected divergence with no correspondent op in the gold patch. Every behaviorally-wrong TERMINATING impl is correctly rejected by the tight answer-key postcondition. This vacuity is therefore a documented methodology caveat of the partial-correctness setting, not a spec-too-weak break for this bundle.

A-LEG / REFINEMENT AUDIT (protocol step 3): refinement.md legs A1..A8 are all R / A-reference / I — NO kind-3. Sole modeled callee is `hasUriScheme` (A-reference, deep model of `uri_re.match`, uri_re=re.compile('[a-z]+://')); no consumed axioms; the two other callees (path.exists, self.to_ignore loop) enter only as free Bool inputs fileExists/anyIgnore (no hidden axiom). A-reference validated: bundle axiom_check.py exit 0 (30 boundary + 40000 fuzz); independent adversarial re-fuzz (backtracking `ab:cd://`, `a:b://`; unicode lowercase µ/á/ß/ı; fullwidth Ａ; uppercase/digit runs; incomplete separators; 500k+ random) = 0 mismatches vs real regex. G-CONF (bundle conformance_check.py) exit 0, shadow==oracle on 100092 inputs (seed 7985). Post-gold non-network arm in worktree confirmed byte-faithful to spec `classify` (unchecked on empty/#/mailto:, uri_re.match->unchecked, path.exists->working, to_ignore->ignored, else broken). patch.diff == gold verbatim.

FLOOR: >=5 same-spec attacks re-run (11 listed, all rejected or resolving-echo), prepatch bug reproduced (atk_1), positive control atk_0_poscontrol verifies (exit 0). VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_10.lean`, `atk_13.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9b.lean` |

**Non-vacuity.** The positive control `atk_0_poscontrol.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9b.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_13.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_0_poscontrol.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The two facts the verdict depends on besides the link
   text itself — whether a file with that name is present under the source tree,
   and whether the link text matches any of the configured skip patterns — are
   unchanged community components, observed only as the boolean inputs
   `fileExists` and `anyIgnore` (their results are method inputs, so no axiom is
   needed, mapping.md §3). The one callee whose behaviour is modeled is the
   scheme detector `hasUriScheme`, modeled DEEPLY (an A-reference, validated ==
   the real callee by axiom_check.py / G-AX), not assumed behind an axiom. -/
-- axioms-end

-- pure-start
/- The verdicts a non-network link can receive. `unchecked` skips it without
   contacting anything; `working` marks a target that resolves and `missing`
   marks one that does not; `ignored` is a deliberately-skipped match;
   `localLink` is the legacy blanket verdict that recorded a non-network link
   without ever resolving it. -/
inductive Status
  | unchecked
  | working
  | ignored
  | missing
  | localLink
deriving DecidableEq, Repr

/- The length of the maximal run of ASCII lowercase letters at the front of a
   string. Front-recursive so it reduces one code point at a time. -/
def lowerRun : List Char → Nat
  | []      => 0
  | c :: cs => if 'a' ≤ c ∧ c ≤ 'z' then 1 + lowerRun cs else 0

/- Whether the link text opens with an explicit access-method marker: one or
   more ASCII lowercase letters immediately followed by the `://` separator
   (e.g. an `ftp://…` address). Deep model (A-reference) of the access-method
   detector; validated == the real detector by axiom_check.py (G-AX). -/
def hasUriScheme (uri : List Char) : Bool :=
  decide (lowerRun uri ≥ 1) && List.isPrefixOf "://".toList (uri.drop (lowerRun uri))

/- Whether the link text is one that is skipped without any resolution attempt:
   it is empty, an in-page fragment reference, or a mail address. Concrete
   transliteration of the leading-marker test (identical op). -/
def isUnchecked (uri : List Char) : Bool :=
  uri.isEmpty || List.isPrefixOf "#".toList uri || List.isPrefixOf "mailto:".toList uri

/- Whether the link text is a web address handled by the network branch.
   Concrete transliteration of the leading-marker test (identical op). -/
def isHttp (uri : List Char) : Bool :=
  List.isPrefixOf "http:".toList uri || List.isPrefixOf "https:".toList uri

/- The verdict for a non-network link, as a function of the link text and the
   two environment observations (`fileExists`: a file of that name is present
   under the source tree; `anyIgnore`: the text matches a configured skip
   pattern). Desired behaviour: a skip-without-resolution link is `unchecked`;
   a link carrying an explicit unsupported access-method marker is also
   `unchecked`; otherwise the link names a local target that MUST be resolved —
   present file ⇒ `working`, else a configured skip ⇒ `ignored`, else the target
   is absent ⇒ `missing`. A non-network link is therefore never left as the
   blanket `localLink` verdict. -/
def classify (uri : List Char) (fileExists anyIgnore : Bool) : Status :=
  if isUnchecked uri then Status.unchecked
  else
    (if hasUriScheme uri then Status.unchecked
     else
       (if fileExists then Status.working
        else
          (if anyIgnore then Status.ignored
           else Status.missing)))
-- pure-end

-- pre-conditions-start
-- (one block per modeled method; this method's only precondition scopes it to
--  the non-network branch — the network branch is handled elsewhere.)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Classify a non-network link. `uri` is the link text; `fileExists` records
   whether a file of that name is present under the source tree; `anyIgnore`
   records whether the text matches any configured skip pattern. The desired
   behaviour is `classify`: skip-without-resolution and explicit unsupported
   access-method links are `unchecked`; every other (local) target is resolved
   to `working`/`ignored`/`missing` rather than being recorded under the blanket
   non-resolving verdict. `uri`, `fileExists`, `anyIgnore` are read-only: the
   method returns a fresh verdict and never mutates its inputs (directive 5). -/
method classifyLocalLink (uri : List Char) (fileExists : Bool) (anyIgnore : Bool)
    return (out : Status)
  require isHttp uri = false
  ensures out = classify uri fileExists anyIgnore
  do
    -- impl-start
    -- A skip-without-resolution link is left unchecked; a link opening with an
    -- explicit unsupported access-method marker is likewise unchecked; any other
    -- link names a local target and is resolved — present file ⇒ working, else a
    -- configured skip ⇒ ignored, else the target is absent ⇒ missing.
    let out : Status :=
      if isUnchecked uri then Status.unchecked
      else
        (if hasUriScheme uri then Status.unchecked
         else
           (if fileExists then Status.working
            else
              (if anyIgnore then Status.ignored
               else Status.missing)))
    return out
    -- impl-end

prove_correct classifyLocalLink by
  loom_solve
  simp only [classify]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: answer-key postcondition `ensures out = classify uri fileExists anyIgnore` where `classify` is fully spelled out in the frozen pure region; `require isHttp uri = false` scopes to the non-network arm. same_spec elides both the impl region and the prove_correct body, so an attacker may rewrite impl + proof; the postcondition still pins `out` EXACTLY to `classify` over the whole precondition domain => maximally tight.

SAME-SPEC CONFIRMED for all attacks via swebench_unified.markers.same_spec (velvet) = True. Verify cmd per file: `bash scripts/lean_verify.sh <atk>.lean`.

TERMINATING WRONG IMPLS — all REJECTED (exit 1), good:
- atk_1 prepatch blanket localLink (prepatch bug reproduced): exit 1 (ensures_1).
- atk_2 drop hasUriScheme entirely: exit 1.
- atk_3 swap working/missing on fileExists (boundary): exit 1.
- atk_4 scheme link -> missing not unchecked: exit 1.
- atk_5 drop anyIgnore->ignored branch (partial-domain): exit 1.
- atk_6 always unchecked (degenerate): exit 1.
- atk_7 reorder fileExists before hasUriScheme (ftp file -> working, control-flow-effect): exit 1.
- atk_8 re-add dropped `ftp:` skip guard: exit 1 (pins the ftp-removal change too).
- atk_10 isUnchecked weakened to uri.isEmpty only (boundary: drops #/mailto:): exit 1.
- atk_13 divergent loop but with `invariant True` (normal-exit VC still generated) returning localLink: exit 1.

VERIFYING SAME-SPEC IMPLS + EXECUTED run_resolve:
1) atk_9b — UNGROUNDED-ORACLE ECHO `let out := classify uri fileExists anyIgnore` (proof: loom_solve): VERIFIES (exit 0). Its faithful refined patch IS the gold patch.diff (echo of the pinned oracle == gold arm). run_resolve('sphinx-doc__sphinx-7985', gold): resolved=True, completed=True, note='resolved'. => CORRECT ECHO, NOT a weakness (matches the derivation's echo policy: candidate whose faithful patch resolves is not a break). (Note atk_9 with proof `loom_solve; simp only [classify]` exits 1 only on the trailing `simp` -> 'No goals to be solved'; that is a proof-script artifact, the impl is correct — atk_9b is the clean encoding.)

NON-TERMINATION / PARTIAL-CORRECTNESS VACUITY (reported transparently; NOT listed in `attacks` because its resolve is non-completing => would inject a spurious INCONCLUSIVE, and it is not a genuine refinement-fidelity break — see judgment below):
- atk_13b: `let mut i:=1; while i>0 invariant i>0 do i:=i+1; return Status.localLink` — VERIFIES (exit 0). atk_13c: same divergent loop, invariant `i≥1`, returns Status.unchecked — VERIFIES (exit 0). Both are provably-divergent loops returning a WRONG value; they pass because the FROZEN `set_option loom.semantics.termination "partial"` discharges the postcondition vacuously on the (unreachable) normal-exit branch. I MATERIALIZED atk_13b's faithful refined patch (inject `i=1; while i>0: i=i+1` before the blanket `return 'local'` in the non-network arm; patch at patch_atk_13b.diff, applies clean at base_commit f30284ef) and RAN it: run_resolve(..., timeout=900) => resolved=False, completed=False, note='no report ... harness error or image pull failure' (the injected infinite loop hangs the F2P test until the harness instance-timeout fires; no report is written). NOT an infra failure: atk_9b resolved cleanly on the same instance image ~10 min earlier in the same session.

JUDGMENT — WHY SOUND, NOT BROKEN: The official G-EQ derivation (construct/build_one.py:_derive_audit_verdict) declares BROKEN only when a candidate's patch is `completed AND not resolved`; a non-completing (timeout) resolve is explicitly INCONCLUSIVE, never a break. atk_13b/13c's patch is completed=False, so it does NOT meet the verify⇏correct bar. Moreover the divergence vacuity is a UNIVERSAL property of the `termination "partial"` convention (401/500 velvet bundles carry this exact option; quickref.md/spec_guide.md sanction it for non-structurally-terminating impls), NOT a defect of THIS spec's refinement fidelity — and the 'faithful patch' is a non-faithful injected divergence with no correspondent op in the gold patch. Every behaviorally-wrong TERMINATING impl is correctly rejected by the tight answer-key postcondition. This vacuity is therefore a documented methodology caveat of the partial-correctness setting, not a spec-too-weak break for this bundle.

A-LEG / REFINEMENT AUDIT (protocol step 3): refinement.md legs A1..A8 are all R / A-reference / I — NO kind-3. Sole modeled callee is `hasUriScheme` (A-reference, deep model of `uri_re.match`, uri_re=re.compile('[a-z]+://')); no consumed axioms; the two other callees (path.exists, self.to_ignore loop) enter only as free Bool inputs fileExists/anyIgnore (no hidden axiom). A-reference validated: bundle axiom_check.py exit 0 (30 boundary + 40000 fuzz); independent adversarial re-fuzz (backtracking `ab:cd://`, `a:b://`; unicode lowercase µ/á/ß/ı; fullwidth Ａ; uppercase/digit runs; incomplete separators; 500k+ random) = 0 mismatches vs real regex. G-CONF (bundle conformance_check.py) exit 0, shadow==oracle on 100092 inputs (seed 7985). Post-gold non-network arm in worktree confirmed byte-faithful to spec `classify` (unchecked on empty/#/mailto:, uri_re.match->unchecked, path.exists->working, to_ignore->ignored, else broken). patch.diff == gold verbatim.

FLOOR: >=5 same-spec attacks re-run (11 listed, all rejected or resolving-echo), prepatch bug reproduced (atk_1), positive control atk_0_poscontrol verifies (exit 0). VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on sphinx-doc__sphinx-7985 velvet bundle. No diverging input found; the modeled function agrees with the real post-patch repo behavior on every mapped input.

Verification performed:
1. Spec region byte-identical: swebench_unified.markers.same_spec(Solution, Solution_prepatch) = True under VelvetBackend.language; spec view confirmed frozen (signature `classifyLocalLink`, `require isHttp uri = false`, `ensures out = classify ...`, pure region with Status/lowerRun/hasUriScheme/isUnchecked/isHttp/classify).
2. Gold patch cross-checked against the dataset gold patch and base-commit linkcheck.py (base f30284ef). Post-patch non-network arm: empty/#/mailto: -> unchecked; uri_re.match([a-z]+://) -> unchecked (ftp dropped from skip guard, now caught here); path.exists -> working; to_ignore match -> ignored; else -> broken. The model's classify mirrors this exactly with fileExists/anyIgnore as the two unchanged-callee boolean inputs.
3. Lean verify (scripts/lean_verify.sh, FSx HOME): exit 0, clean elaboration, no sorry/error.
4. G-AX (axiom_check.py): PASS. hasUriScheme deep model == real re.compile('[a-z]+://').match on 30 boundary + 40000 fuzz inputs. Maximal-lowercase-run reasoning is sound because ':' is non-lowercase, so '://' can only follow the maximal front run.
5. G-CONF (conformance_check.py): PASS, 100092 inputs, 0 disagreements.
6. Independent adversarial fuzz (my own, seed 424242, 498500 in-domain inputs incl. unicode/whitespace/tab/newline, fullwidth chars, scheme-boundary edge cases): 0 divergences between model classify and a faithful copy of the real post-patch arm.

The precondition isHttp=false correctly scopes the model to the exact arm reached under the real elif guard; the skip-guard subset (#, mailto:) is disjoint from http(s). classify is a total function equal to real repo behavior on all mapped inputs. Spec is neither too strong nor drifting. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Semantic leakage/gold-reconstruction review of the velvet spec view for sphinx-doc__sphinx-7985. Verified spec regions are byte-identical (same_spec(Solution, Solution_prepatch)=True), so the consumer view is the frozen spec. Mechanical G-LEAK screen passes (rep.passed=True, zero hard_failures): no diff markers, no gold-patch line reproduced (>=8 chars normalized), no patched file path 'sphinx/builders/linkcheck.py' or dotted module, and the only distinctive changed symbol 'check_uri' appears nowhere in the spec view (method is named classifyLocalLink; no comment names it). No narration terms (fix/bug/broken-as-flag/patched/legacy) trip the screen.

Semantic judgment beyond the lexical screen: The public problem_statement ALREADY discloses the substance the edit fixes — it states linkcheck 'currently doesn't check local (internal) links' and, critically, its reproduction log literally shows the pre-patch blanket output '(line 14) -local- doesntexist' and the Expected result 'Also a check for the local link.' So the legacy blanket 'local' verdict and the desired local-target resolution are public. The spec view's `classify` function (skip-without-resolution => unchecked; scheme-carrying link => unchecked; else resolve target to working/ignored/missing; never the blanket localLink) is a legitimate BEHAVIORAL specification — determining target behavior is the intended spec->solver contract, not a reconstruction of the gold DIFF.

It reveals no changed lines, no file, no symbol, and no before/after edit structure. The `hasUriScheme`/`ftp://` content models the natural semantics of the added scheme detector but names no edit location and does not disclose that 'ftp:' was removed from a guard as a code change. The `localLink` inductive constructor and its comment describe exactly the pre-patch behavior the public log shows ('-local-'), so they leak nothing beyond problem_statement. Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).