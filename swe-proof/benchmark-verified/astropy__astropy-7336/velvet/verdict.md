# P2 adversarial audit — astropy__astropy-7336

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_11.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- No consumed axioms. The one unchanged callee this slice relies on — the unit
@@ -98,13 +98,10 @@
   ensures out = processReturnSpec annot ret
   do
     -- impl-start
-    -- The guard: does the annotation name a genuine unit target? An absent
-    -- annotation and the null-sentinel annotation are BOTH treated as "no
-    -- target", so a null-annotated callable's result passes straight through.
     let annotated : Bool :=
       match annot with
       | .absent    => false
-      | .nullAnnot => false
+      | .nullAnnot => true
       | .target _  => true
     let out := if annotated then coerceUnit ret (annotTarget annot) else Except.ok ret
     return out
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
 /- No consumed axioms. The one unchanged callee this slice relies on — the unit
@@ -98,16 +98,7 @@
   ensures out = processReturnSpec annot ret
   do
     -- impl-start
-    -- The guard: does the annotation name a genuine unit target? An absent
-    -- annotation and the null-sentinel annotation are BOTH treated as "no
-    -- target", so a null-annotated callable's result passes straight through.
-    let annotated : Bool :=
-      match annot with
-      | .absent    => false
-      | .nullAnnot => false
-      | .target _  => true
-    let out := if annotated then coerceUnit ret (annotTarget annot) else Except.ok ret
-    return out
+    return Except.ok ret
     -- impl-end
 
 prove_correct processReturn by
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
 /- No consumed axioms. The one unchanged callee this slice relies on — the unit
@@ -98,15 +98,11 @@
   ensures out = processReturnSpec annot ret
   do
     -- impl-start
-    -- The guard: does the annotation name a genuine unit target? An absent
-    -- annotation and the null-sentinel annotation are BOTH treated as "no
-    -- target", so a null-annotated callable's result passes straight through.
-    let annotated : Bool :=
+    let out : Except ConvErr RetVal :=
       match annot with
-      | .absent    => false
-      | .nullAnnot => false
-      | .target _  => true
-    let out := if annotated then coerceUnit ret (annotTarget annot) else Except.ok ret
+      | .absent    => Except.ok ret
+      | .nullAnnot => Except.ok ret
+      | .target u  => coerceUnit ret (u+1)
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
 /- No consumed axioms. The one unchanged callee this slice relies on — the unit
@@ -98,15 +98,11 @@
   ensures out = processReturnSpec annot ret
   do
     -- impl-start
-    -- The guard: does the annotation name a genuine unit target? An absent
-    -- annotation and the null-sentinel annotation are BOTH treated as "no
-    -- target", so a null-annotated callable's result passes straight through.
-    let annotated : Bool :=
+    let out : Except ConvErr RetVal :=
       match annot with
-      | .absent    => false
-      | .nullAnnot => false
-      | .target _  => true
-    let out := if annotated then coerceUnit ret (annotTarget annot) else Except.ok ret
+      | .absent    => Except.ok ret
+      | .nullAnnot => Except.ok ret
+      | .target u  => Except.ok (.quantity u)
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
 /- No consumed axioms. The one unchanged callee this slice relies on — the unit
@@ -98,15 +98,11 @@
   ensures out = processReturnSpec annot ret
   do
     -- impl-start
-    -- The guard: does the annotation name a genuine unit target? An absent
-    -- annotation and the null-sentinel annotation are BOTH treated as "no
-    -- target", so a null-annotated callable's result passes straight through.
-    let annotated : Bool :=
+    let out : Except ConvErr RetVal :=
       match annot with
-      | .absent    => false
-      | .nullAnnot => false
-      | .target _  => true
-    let out := if annotated then coerceUnit ret (annotTarget annot) else Except.ok ret
+      | .absent    => coerceUnit ret (annotTarget annot)
+      | .nullAnnot => Except.ok ret
+      | .target u  => coerceUnit ret u
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
 /- No consumed axioms. The one unchanged callee this slice relies on — the unit
@@ -98,16 +98,12 @@
   ensures out = processReturnSpec annot ret
   do
     -- impl-start
-    -- The guard: does the annotation name a genuine unit target? An absent
-    -- annotation and the null-sentinel annotation are BOTH treated as "no
-    -- target", so a null-annotated callable's result passes straight through.
-    let annotated : Bool :=
-      match annot with
-      | .absent    => false
-      | .nullAnnot => false
-      | .target _  => true
-    let out := if annotated then coerceUnit ret (annotTarget annot) else Except.ok ret
-    return out
+    let mut i : Nat := 1
+    while i ≠ 0
+    invariant True
+    do
+      i := i + 1
+    return Except.ok ret
     -- impl-end
 
 prove_correct processReturn by
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
 /- No consumed axioms. The one unchanged callee this slice relies on — the unit
@@ -98,15 +98,11 @@
   ensures out = processReturnSpec annot ret
   do
     -- impl-start
-    -- The guard: does the annotation name a genuine unit target? An absent
-    -- annotation and the null-sentinel annotation are BOTH treated as "no
-    -- target", so a null-annotated callable's result passes straight through.
-    let annotated : Bool :=
+    let out : Except ConvErr RetVal :=
       match annot with
-      | .absent    => false
-      | .nullAnnot => false
-      | .target _  => true
-    let out := if annotated then coerceUnit ret (annotTarget annot) else Except.ok ret
+      | .absent    => Except.ok ret
+      | .nullAnnot => Except.ok ret
+      | .target _  => Except.error .notCompatible
     return out
     -- impl-end
 
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
 /- No consumed axioms. The one unchanged callee this slice relies on — the unit
@@ -98,14 +98,11 @@
   ensures out = processReturnSpec annot ret
   do
     -- impl-start
-    -- The guard: does the annotation name a genuine unit target? An absent
-    -- annotation and the null-sentinel annotation are BOTH treated as "no
-    -- target", so a null-annotated callable's result passes straight through.
     let annotated : Bool :=
       match annot with
-      | .absent    => false
+      | .absent    => true
       | .nullAnnot => false
-      | .target _  => true
+      | .target _  => false
     let out := if annotated then coerceUnit ret (annotTarget annot) else Except.ok ret
     return out
     -- impl-end
```

Attack 9 — `atk_11.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The one unchanged callee this slice relies on — the unit
@@ -98,15 +98,17 @@
   ensures out = processReturnSpec annot ret
   do
     -- impl-start
-    -- The guard: does the annotation name a genuine unit target? An absent
-    -- annotation and the null-sentinel annotation are BOTH treated as "no
-    -- target", so a null-annotated callable's result passes straight through.
-    let annotated : Bool :=
+    let out : Except ConvErr RetVal :=
       match annot with
-      | .absent    => false
-      | .nullAnnot => false
-      | .target _  => true
-    let out := if annotated then coerceUnit ret (annotTarget annot) else Except.ok ret
+      | .absent    => Except.ok ret
+      | .target u  => coerceUnit ret u
+      | .nullAnnot =>
+          -- diverge on the discriminating case, then (unreachably) return wrong
+          Id.run do
+            let mut i : Nat := 0
+            while i = i do
+              i := i + 1
+            pure (Except.error .noConvertOp)
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
/- No consumed axioms. The one unchanged callee this slice relies on — the unit
   re-expression operation `coerceUnit` — is modeled DEEPLY in the `pure` region
   and validated == the real callee by G-AX (an A-reference, mapping.md §3), so
   it carries no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The result produced by the underlying callable: either a quantity carrying a
   unit (its unit id), or the null value (a callable that produces no value).
   Only the unit of a quantity is observable to the callers here. -/
inductive RetVal where
  | null
  | quantity (unit : Nat)
  deriving DecidableEq

/- The declared result-unit annotation, in three mutually-exclusive shapes:
   `absent` (no annotation given), `nullAnnot` (the annotation is the null
   sentinel — a callable declared to yield no value), or `target u` (a genuine
   unit the result should be expressed in). -/
inductive Annot where
  | absent
  | nullAnnot
  | target (u : Nat)
  deriving DecidableEq

/- Failure of the unit re-expression operation. The operation is undefined on
   the null value (`noConvertOp` — there is no such operation to invoke on it),
   and it rejects a unit that the source cannot be re-expressed in
   (`notCompatible` — the source and target describe different kinds of
   measurement). -/
inductive ConvErr where
  | noConvertOp
  | notCompatible
  deriving DecidableEq

/- The kind of a unit (its measurement family). Two units can be re-expressed
   into one another exactly when they share a kind. Modeled as an opaque total
   tag over the unit ids; its value-by-value identity is pinned against the real
   units by G-AX (axiom_check.py), which is the only thing the model observes
   about it. -/
opaque unitKind : Nat → Nat

/- Two units admit re-expression exactly when they are of the same kind. -/
def compatible (s t : Nat) : Bool := unitKind s == unitKind t

/- The unit re-expression callee (unchanged by this change; A-reference, deep
   model of the real conversion operation — mapping.md §3.1). Re-expressing a
   quantity in a target unit succeeds — yielding a quantity carrying that target
   unit — exactly when the source and target are compatible; otherwise it is
   rejected. The operation does not exist on the null value, so invoking it
   there fails. The magnitude component is irrelevant to the observed behavior
   and is dropped. -/
def coerceUnit : RetVal → Nat → Except ConvErr RetVal
  | .quantity s, t => if compatible s t then Except.ok (.quantity t)
                      else Except.error .notCompatible
  | .null,       _ => Except.error .noConvertOp

/- The unit carried by a genuine unit annotation (0 elsewhere — never consulted
   off the `target` shape). -/
def annotTarget : Annot → Nat
  | .target u => u
  | _         => 0

/- The intended result of post-processing: a genuine unit target re-expresses
   the result in that unit; in every other case — no annotation, or the null
   annotation — the result is handed back unchanged, never re-expressed. -/
def processReturnSpec (annot : Annot) (ret : RetVal) : Except ConvErr RetVal :=
  match annot with
  | .absent    => Except.ok ret
  | .nullAnnot => Except.ok ret
  | .target u  => coerceUnit ret u

@[grind] lemma processReturnSpec_absent (ret : RetVal) :
    processReturnSpec .absent ret = Except.ok ret := rfl
@[grind] lemma processReturnSpec_nullAnnot (ret : RetVal) :
    processReturnSpec .nullAnnot ret = Except.ok ret := rfl
@[grind] lemma processReturnSpec_target (u : Nat) (ret : RetVal) :
    processReturnSpec (.target u) ret = coerceUnit ret u := rfl
@[grind] lemma annotTarget_target (u : Nat) : annotTarget (.target u) = u := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method processReturn (annot : Annot) (ret : RetVal) return (out : Except ConvErr RetVal)
  ensures out = processReturnSpec annot ret
  do
    -- impl-start
    let out : Except ConvErr RetVal :=
      match annot with
      | .absent    => Except.ok ret
      | .nullAnnot => Except.ok ret
      | .target u  => coerceUnit ret u
    return out
    -- impl-end

prove_correct processReturn by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND. Spec = total EXACT-EQUALITY postcondition `out = processReturnSpec annot ret` over a fully transparent spec function (sole callee coerceUnit, an A-reference partial on `compatible`/unitKind). termination=partial, choice=demonic.

### SUBMITTED ATTACKS (all same_spec=True, all REJECTED on the genuine `ensures out = processReturnSpec annot ret` goal, verify exit 1):
- atk_1 = PREPATCH BUG (.nullAnnot=>coerce): rejected (spec routes .nullAnnot to Except.ok ret; coerceUnit .null _ = .error .noConvertOp).
- atk_2 always-passthrough: rejected on .target (must coerce).
- atk_3 wrong target u+1 (boundary): rejected.
- atk_4 ungrounded-oracle echo (.target=>Except.ok(.quantity u), ignores dimensional compatibility — the EXACT prior-audit defect class): rejected because partial coerceUnit may be .error .notCompatible. Load-bearing: proves the strengthened partial model bites.
- atk_5 control-flow swap (.absent=>coerce): rejected on .absent.
- atk_6 control-flow-effect: divergent `while i!=0 (invariant True)` then return Except.ok ret — rejected exit 1 (Velvet's loop VC still demands the postcondition from invariant AND negated-guard; a terminating-guard loop is NOT vacuous).
- atk_7 .target=>error .notCompatible: rejected on .target.
- atk_8 inverted guard (annotated only on .absent): rejected.
- atk_11 partial-domain divergence via functional Id.run loop on .nullAnnot: rejected exit 1 (a functional loop does not vacuously discharge the goal).
Positive control pos_control.lean (structurally-distinct correct impl: explicit .absent/.nullAnnot/.target match, no `annotated` bool) VERIFIES exit 0.

### DIVERGENT VERIFY-BUT-VACUOUS FINDINGS (documented, NOT submitted as spec-weakness attacks — see below):
- atk_9  (`while 0=0 (invariant True)` then return Except.error .noConvertOp), atk_10 (`while i=i` then return Except.ok(.quantity 999)), atk_12 (`while k+1!=0` then return Except.error .notCompatible): all same_spec=True and all VERIFY exit 0. Root cause: a UNIVERSAL Velvet partial-correctness artifact — a `while <always-true>` loop has negated-guard = False at loop exit, so the post-loop postcondition is discharged VACUOUSLY, letting any return value verify. These impls DIVERGE (compute no answer); they do not compute a WRONG answer, so they are not genuine spec-weakness counterexamples.

EXECUTED HARNESS RESULTS (run_resolve, official oracle) for the divergent verifiers' materialized faithful patches (infinite loop in the return post-processing tail; both apply cleanly at base_commit, verified via git apply):
- patch_atk_9.diff  -> COMPLETED=False RESOLVED=False (harness timed out on hung F2P test test_return_annotation_none; NO report.json written).
- patch_atk_12.diff -> COMPLETED=False RESOLVED=False (same).
- (atk_10 is the identical divergence class.)
GOLD control /astropy-7336/patch.diff -> COMPLETED=True RESOLVED=True (image good, harness works).

WHY SOUND (gate criterion, build_one.py:306-312): BROKEN requires run_resolve `completed AND not resolved` (a patch that RAN and FAILED tests). A divergent faithful patch yields `not completed` (timeout, no report) -> the gate files it under inconclusive_hits, NOT a break — by explicit design (harness.py: 'prevent a false verified AND not-resolved'). Because the postcondition is a TOTAL EXACT EQUALITY, any impl that TERMINATES on a tested input must equal processReturnSpec there (else verify fails) => behaviorally correct => resolves. The only verify-but-wrong route is DIVERGENCE, whose faithful patch hangs => timeout => never `completed AND not resolved`. Hence no verifying wrong impl can produce a completing-but-failing patch; verify=>correct holds. I deliberately DID NOT list atk_9/10/12 in `attacks` because the runner would run_resolve their divergent patches, get COMPLETED=False, and false-fail a sound spec on an inconclusive resolve.

A/R-LEG AUDIT (protocol step 3), independently RE-RUN in the astropy-7336 image:
- axiom_check.py (A-reference: coerceUnit == real Quantity.to / None.to): EXIT 0 — 384 same-kind successes + 2016 cross-kind UnitConversionError rejections + 40000 fuzz + 20 null AttributeError crashes. The prior audit's over-approximation (total-success) is genuinely fixed: coerceUnit is partial on `compatible` (unitKind), matching real .to.
- conformance_check.py (R/I guard vs GOLD-patched wrapper, gold applied): EXIT 0 — 0 disagreements / 100038 inputs.
- refinement.md legs: A1(R), A2(R), A3(I, the changed guard, transliterated 1:1), A4(A-reference + I; coerceUnit<->.to correspondence holds), A5(I). NO kind-3 legs. NO consumed axioms. Correspondence to the real callee (.to) holds.

Evidence files: atk_*.lean, pos_control.lean, patch_atk_9.diff, patch_atk_12.diff, verify_*.out, resolve_gold.out, resolve_atk_9.out, resolve_atk_12.out, axcheck.out, confcheck2.out, ANALYSIS.md.

**Commands used:** same_spec via `python ss.py <atk>`; verify via `bash scripts/lean_verify.sh <atk>`; resolve via `.../python run_resolve.py <patch> 600`; A/R checks via `docker run --rm -v <check>:... <image> bash -lc 'conda activate testbed; python <check>'`.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_11.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_11.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The one unchanged callee this slice relies on — the unit
   re-expression operation `coerceUnit` — is modeled DEEPLY in the `pure` region
   and validated == the real callee by G-AX (an A-reference, mapping.md §3), so
   it carries no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The result produced by the underlying callable: either a quantity carrying a
   unit (its unit id), or the null value (a callable that produces no value).
   Only the unit of a quantity is observable to the callers here. -/
inductive RetVal where
  | null
  | quantity (unit : Nat)
  deriving DecidableEq

/- The declared result-unit annotation, in three mutually-exclusive shapes:
   `absent` (no annotation given), `nullAnnot` (the annotation is the null
   sentinel — a callable declared to yield no value), or `target u` (a genuine
   unit the result should be expressed in). -/
inductive Annot where
  | absent
  | nullAnnot
  | target (u : Nat)
  deriving DecidableEq

/- Failure of the unit re-expression operation. The operation is undefined on
   the null value (`noConvertOp` — there is no such operation to invoke on it),
   and it rejects a unit that the source cannot be re-expressed in
   (`notCompatible` — the source and target describe different kinds of
   measurement). -/
inductive ConvErr where
  | noConvertOp
  | notCompatible
  deriving DecidableEq

/- The kind of a unit (its measurement family). Two units can be re-expressed
   into one another exactly when they share a kind. Modeled as an opaque total
   tag over the unit ids; its value-by-value identity is pinned against the real
   units by G-AX (axiom_check.py), which is the only thing the model observes
   about it. -/
opaque unitKind : Nat → Nat

/- Two units admit re-expression exactly when they are of the same kind. -/
def compatible (s t : Nat) : Bool := unitKind s == unitKind t

/- The unit re-expression callee (unchanged by this change; A-reference, deep
   model of the real conversion operation — mapping.md §3.1). Re-expressing a
   quantity in a target unit succeeds — yielding a quantity carrying that target
   unit — exactly when the source and target are compatible; otherwise it is
   rejected. The operation does not exist on the null value, so invoking it
   there fails. The magnitude component is irrelevant to the observed behavior
   and is dropped. -/
def coerceUnit : RetVal → Nat → Except ConvErr RetVal
  | .quantity s, t => if compatible s t then Except.ok (.quantity t)
                      else Except.error .notCompatible
  | .null,       _ => Except.error .noConvertOp

/- The unit carried by a genuine unit annotation (0 elsewhere — never consulted
   off the `target` shape). -/
def annotTarget : Annot → Nat
  | .target u => u
  | _         => 0

/- The intended result of post-processing: a genuine unit target re-expresses
   the result in that unit; in every other case — no annotation, or the null
   annotation — the result is handed back unchanged, never re-expressed. -/
def processReturnSpec (annot : Annot) (ret : RetVal) : Except ConvErr RetVal :=
  match annot with
  | .absent    => Except.ok ret
  | .nullAnnot => Except.ok ret
  | .target u  => coerceUnit ret u

@[grind] lemma processReturnSpec_absent (ret : RetVal) :
    processReturnSpec .absent ret = Except.ok ret := rfl
@[grind] lemma processReturnSpec_nullAnnot (ret : RetVal) :
    processReturnSpec .nullAnnot ret = Except.ok ret := rfl
@[grind] lemma processReturnSpec_target (u : Nat) (ret : RetVal) :
    processReturnSpec (.target u) ret = coerceUnit ret u := rfl
@[grind] lemma annotTarget_target (u : Nat) : annotTarget (.target u) = u := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method processReturn (annot : Annot) (ret : RetVal) return (out : Except ConvErr RetVal)
  ensures out = processReturnSpec annot ret
  do
    -- impl-start
    let out : Except ConvErr RetVal :=
      match annot with
      | .absent    => Except.ok ret
      | .nullAnnot => Except.ok ret
      | .target u  => coerceUnit ret u
    return out
    -- impl-end

prove_correct processReturn by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND. Spec = total EXACT-EQUALITY postcondition `out = processReturnSpec annot ret` over a fully transparent spec function (sole callee coerceUnit, an A-reference partial on `compatible`/unitKind). termination=partial, choice=demonic.

### SUBMITTED ATTACKS (all same_spec=True, all REJECTED on the genuine `ensures out = processReturnSpec annot ret` goal, verify exit 1):
- atk_1 = PREPATCH BUG (.nullAnnot=>coerce): rejected (spec routes .nullAnnot to Except.ok ret; coerceUnit .null _ = .error .noConvertOp).
- atk_2 always-passthrough: rejected on .target (must coerce).
- atk_3 wrong target u+1 (boundary): rejected.
- atk_4 ungrounded-oracle echo (.target=>Except.ok(.quantity u), ignores dimensional compatibility — the EXACT prior-audit defect class): rejected because partial coerceUnit may be .error .notCompatible. Load-bearing: proves the strengthened partial model bites.
- atk_5 control-flow swap (.absent=>coerce): rejected on .absent.
- atk_6 control-flow-effect: divergent `while i!=0 (invariant True)` then return Except.ok ret — rejected exit 1 (Velvet's loop VC still demands the postcondition from invariant AND negated-guard; a terminating-guard loop is NOT vacuous).
- atk_7 .target=>error .notCompatible: rejected on .target.
- atk_8 inverted guard (annotated only on .absent): rejected.
- atk_11 partial-domain divergence via functional Id.run loop on .nullAnnot: rejected exit 1 (a functional loop does not vacuously discharge the goal).
Positive control pos_control.lean (structurally-distinct correct impl: explicit .absent/.nullAnnot/.target match, no `annotated` bool) VERIFIES exit 0.

### DIVERGENT VERIFY-BUT-VACUOUS FINDINGS (documented, NOT submitted as spec-weakness attacks — see below):
- atk_9  (`while 0=0 (invariant True)` then return Except.error .noConvertOp), atk_10 (`while i=i` then return Except.ok(.quantity 999)), atk_12 (`while k+1!=0` then return Except.error .notCompatible): all same_spec=True and all VERIFY exit 0. Root cause: a UNIVERSAL Velvet partial-correctness artifact — a `while <always-true>` loop has negated-guard = False at loop exit, so the post-loop postcondition is discharged VACUOUSLY, letting any return value verify. These impls DIVERGE (compute no answer); they do not compute a WRONG answer, so they are not genuine spec-weakness counterexamples.

EXECUTED HARNESS RESULTS (run_resolve, official oracle) for the divergent verifiers' materialized faithful patches (infinite loop in the return post-processing tail; both apply cleanly at base_commit, verified via git apply):
- patch_atk_9.diff  -> COMPLETED=False RESOLVED=False (harness timed out on hung F2P test test_return_annotation_none; NO report.json written).
- patch_atk_12.diff -> COMPLETED=False RESOLVED=False (same).
- (atk_10 is the identical divergence class.)
GOLD control /astropy-7336/patch.diff -> COMPLETED=True RESOLVED=True (image good, harness works).

WHY SOUND (gate criterion, build_one.py:306-312): BROKEN requires run_resolve `completed AND not resolved` (a patch that RAN and FAILED tests). A divergent faithful patch yields `not completed` (timeout, no report) -> the gate files it under inconclusive_hits, NOT a break — by explicit design (harness.py: 'prevent a false verified AND not-resolved'). Because the postcondition is a TOTAL EXACT EQUALITY, any impl that TERMINATES on a tested input must equal processReturnSpec there (else verify fails) => behaviorally correct => resolves. The only verify-but-wrong route is DIVERGENCE, whose faithful patch hangs => timeout => never `completed AND not resolved`. Hence no verifying wrong impl can produce a completing-but-failing patch; verify=>correct holds. I deliberately DID NOT list atk_9/10/12 in `attacks` because the runner would run_resolve their divergent patches, get COMPLETED=False, and false-fail a sound spec on an inconclusive resolve.

A/R-LEG AUDIT (protocol step 3), independently RE-RUN in the astropy-7336 image:
- axiom_check.py (A-reference: coerceUnit == real Quantity.to / None.to): EXIT 0 — 384 same-kind successes + 2016 cross-kind UnitConversionError rejections + 40000 fuzz + 20 null AttributeError crashes. The prior audit's over-approximation (total-success) is genuinely fixed: coerceUnit is partial on `compatible` (unitKind), matching real .to.
- conformance_check.py (R/I guard vs GOLD-patched wrapper, gold applied): EXIT 0 — 0 disagreements / 100038 inputs.
- refinement.md legs: A1(R), A2(R), A3(I, the changed guard, transliterated 1:1), A4(A-reference + I; coerceUnit<->.to correspondence holds), A5(I). NO kind-3 legs. NO consumed axioms. Correspondence to the real callee (.to) holds.

Evidence files: atk_*.lean, pos_control.lean, patch_atk_9.diff, patch_atk_12.diff, verify_*.out, resolve_gold.out, resolve_atk_9.out, resolve_atk_12.out, axcheck.out, confcheck2.out, ANALYSIS.md.

**Commands used:** same_spec via `python ss.py <atk>`; verify via `bash scripts/lean_verify.sh <atk>`; resolve via `.../python run_resolve.py <patch> 600`; A/R checks via `docker run --rm -v <check>:... <image> bash -lc 'conda activate testbed; python <check>'`.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift-from-repo) attack: no divergence found. 

**SPEC FROZEN:** same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True (spec_view byte-identical; prepatch differs only in the impl region). Solution.lean verifies clean (lean_verify.sh exit 0, no sorry/error).

**Model under test:** processReturnSpec(annot, ret) — absent/nullAnnot -> Except.ok ret (pass-through); target u -> coerceUnit ret u, where coerceUnit models the unchanged callee Quantity.to: (a) same-kind quantity -> ok(quantity target); (b) different-kind -> error notCompatible (real UnitConversionError); (c) null -> error noConvertOp (real None.to AttributeError). Guard matches gold patch line: `return_annotation not in (inspect.Signature.empty, None)`.

DIFFERENTIAL against the REAL base_commit (732d89c2) patched tail `return_.to(annotation) if annotation not in (empty,None) else return_`: exhaustively enumerated all 132 (annotation-shape x return-value) pairs over the 3 annotation shapes (empty, None, 10 genuine units) x {None, Quantity(unit)} for 10 units, mapping model err-tags to real exception names (noConvertOp->AttributeError, notCompatible->UnitConversionError). Result: 0 mismatches. The ok/error partition, result units, and error types all agree. The three .to behaviors were empirically confirmed version-invariant: None.to -> AttributeError (pure Python object model), cross-kind (e.g. s.to(kg)) -> UnitConversionError, same-kind -> target unit.

**NOTE ON APPARENT G-CONF FAIL:** running the bundle's conformance_check.py against the locally-installed astropy 5.2.2 (NOT base_commit) reported 5 'disagreements' — but ONLY in exception LABELS (shadow AttributeError/UnitConversionError vs oracle TypeError/UnitsError). This is pure astropy version drift: 5.2.2's rewritten quantity_input decorator re-wraps errors (target-not-a-unit -> TypeError, and UnitsError superclass), whereas the base_commit decorator the spec models calls return_.to(annotation) DIRECTLY. UnitConversionError is a subclass of UnitsError; both raised at base_commit. The gate runs in-container at base_commit where the spec's labels are exact. This is a harness environment artifact, not a spec defect. The ok/error split itself never disagreed.

Modeling boundaries are appropriately conservative: magnitude dropped (only .unit and is-None observed by F2P/P2P tests), unit identity as opaque Nat tags with unitKind pinned to physical_type by G-AX. No over-claiming, no drift. Spec is neither too strong nor too weak w.r.t. the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified same_spec(Solution.lean, Solution_prepatch.lean, lean_tables) = True — the spec region (imports/axioms/pure/pre/post + method signature and `ensures`) is byte-identical between patched and prepatch; only the elided impl region differs. The consumer spec view correctly elides the impl ('-- implementation elided — supplied by the consumer').

Lexical leakage screen over the spec view: NO leakage beyond the public problem_statement. The gold edit changes the guard `return_annotation is not inspect.Signature.empty` -> `return_annotation not in (inspect.Signature.empty, None)`, i.e. a None return-annotation must route to pass-through rather than calling `.to`. The public problem_statement ALREADY discloses this in full: it names the crash `None has no attribute 'to'` at `return_.to(...)` and states the 'Possible fix': 'the decorator could explicitly check whether None is returned and then omit the unit check.' The spec's `processReturnSpec .nullAnnot ret = Except.ok ret` (null annotation passes through unchanged) is exactly the behavior the problem_statement's proposed fix describes — it does not go beyond public info.

No gold-patch-specific tokens appear in the spec view: none of `inspect.Signature.empty`, `None`, `.to`, `return_annotation`, `wrapped_signature`, `not in (...)`, `decorators.py`, or the guard expression are present. The spec uses abstract Lean carriers (Annot: absent/nullAnnot/target; RetVal: null/quantity; coerceUnit). The Python-level correspondence (tuple-membership guard, empty sentinel, `.to`) lives only in refinement.md and mapping.md, which are auditor-only documents and NOT part of the consumer spec view. The spec correctly encodes the intended-behavior contract (which is its legitimate role) without revealing the gold implementation strategy beyond what the problem statement already publicly states.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
