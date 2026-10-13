# P2 adversarial audit — scikit-learn__scikit-learn-26194

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,12 @@
   ensures out = Threshold.top :: finiteSeq base
   do
     -- impl-start
-    let out : List Threshold := Threshold.top :: finiteSeq base
+    -- Pre-image skeleton: the leading position is built as a FINITE value,
+    -- (first finite threshold) + 1, instead of the sentinel position above
+    -- every finite score. The frozen spec requires the sentinel `top`, so
+    -- `value _ ≠ top` and prove_correct MUST fail.
+    let lead : Threshold := Threshold.value (base.head! + 1)
+    let out : List Threshold := lead :: finiteSeq base
     return out
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,7 @@
   ensures out = Threshold.top :: finiteSeq base
   do
     -- impl-start
-    let out : List Threshold := Threshold.top :: finiteSeq base
+    let out : List Threshold := finiteSeq base
     return out
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,7 @@
   ensures out = Threshold.top :: finiteSeq base
   do
     -- impl-start
-    let out : List Threshold := Threshold.top :: finiteSeq base
+    let out : List Threshold := finiteSeq base ++ [Threshold.top]
     return out
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,7 @@
   ensures out = Threshold.top :: finiteSeq base
   do
     -- impl-start
-    let out : List Threshold := Threshold.top :: finiteSeq base
+    let out : List Threshold := Threshold.top :: Threshold.top :: finiteSeq base
     return out
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,9 @@
   ensures out = Threshold.top :: finiteSeq base
   do
     -- impl-start
-    let out : List Threshold := Threshold.top :: finiteSeq base
+    let out : List Threshold := match base with
+      | [x] => [Threshold.top, Threshold.value x]
+      | _   => [Threshold.top]
     return out
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,7 @@
   ensures out = Threshold.top :: finiteSeq base
   do
     -- impl-start
-    let out : List Threshold := Threshold.top :: finiteSeq base
+    let out : List Threshold := Threshold.top :: finiteSeq base.reverse
     return out
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,7 @@
   ensures out = Threshold.top :: finiteSeq base
   do
     -- impl-start
-    let out : List Threshold := Threshold.top :: finiteSeq base
+    let out : List Threshold := Threshold.value 0 :: finiteSeq base
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A decision threshold on a scoring function. A `value r` is an ordinary finite
   threshold (a score cut-off); `top` is the sentinel position that classifies
   NO instance as positive — it sits strictly above every attainable finite
   score, so the curve is anchored at the (0,0) corner. Modeling the sentinel as
   its own constructor (rather than a finite number) keeps it categorically apart
   from any real score: it can never be confused with, or compared as if it were,
   an ordinary value. Finite thresholds are carried as exact `Rat` because only
   their order/value matters here (mapping.md §2). -/
inductive Threshold where
  | value (r : Rat)
  | top
deriving DecidableEq

/- Lift a list of finite thresholds (the ordered cut-offs computed upstream) into
   the threshold domain, leaving each value untouched. -/
def finiteSeq (xs : List Rat) : List Threshold := xs.map Threshold.value
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Anchor a sequence of finite decision thresholds with one extra leading
   position so the resulting curve starts at the corner where no instance is
   predicted positive. `base` are the ordered finite thresholds produced
   upstream; the result is `base` (unchanged, in order) preceded by the sentinel
   that lies above every finite threshold. -/
method withLeadingSentinel (base : List Rat) return (out : List Threshold)
  require base ≠ []
  ensures out = Threshold.top :: finiteSeq base
  do
    -- impl-start
    let out : List Threshold := Threshold.top :: finiteSeq base
    return out
    -- impl-end

prove_correct withLeadingSentinel by loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec: method withLeadingSentinel (base : List Rat) return (out : List Threshold), require base != [], ensures out = Threshold.top :: finiteSeq base. This is an EXACT-EQUALITY postcondition over the FROZEN pure-region types (inductive Threshold = value Rat | top; finiteSeq = List.map Threshold.value). It fully pins the output, so any same-spec impl that verifies must produce byte-identical gold output. There is no room for a verifying-but-wrong impl.

Same-spec confirmation (swebench_unified.markers.same_spec, velvet): all 7 attacks + positive control report True (initial run showed False due to a generator bug that truncated the trailing 'prove_correct' line; regenerated to preserve the full tail, re-checked True for all).

Verification (bash scripts/lean_verify.sh <file>, run concurrently in two batches of 4 from project root):
  pos_control EXIT=0 (verifies)
  atk_1 EXIT=1  atk_2 EXIT=1  atk_3 EXIT=1  atk_4 EXIT=1  atk_5 EXIT=1  atk_6 EXIT=1  atk_7 EXIT=1
Every attack failure is a genuine loom_solve 'unsolved goals' on the postcondition (confirmed in per-file .log; not syntax errors).

Attacks (all edit ONLY the impl region; axioms/pure/pre/post byte-identical):
  atk_1 = PREPATCH bug: lead = Threshold.value (base.head! + 1) (finite max+1 lead). Reproduces the pre-patch behavior; fails 'value _ != top' at the head. prepatch_reproduced=true.
  atk_2 = partial/missing-sentinel: out = finiteSeq base (drops the leading sentinel entirely).
  atk_3 = boundary/order: out = finiteSeq base ++ [Threshold.top] (sentinel appended at TAIL not head).
  atk_4 = over-count / ungrounded-echo: out = Threshold.top :: Threshold.top :: finiteSeq base (two sentinels).
  atk_5 = control-flow-effect / partial-domain: match base with [x] => [top, value x] | _ => [top] (correct only for singletons, drops tail otherwise).
  atk_6 = order violation: out = Threshold.top :: finiteSeq base.reverse (tail reversed).
  atk_7 = ungrounded-oracle echo (wrong kind of lead): out = Threshold.value 0 :: finiteSeq base (prepends a finite value instead of the sentinel).

Resolve step: NO same-spec wrong impl verifies (all 7 exit 1), so there is no verifying-wrong-impl faithful patch to materialize and run through run_resolve. Step-2 obligation is vacuously satisfied; patches={} accordingly. Note: Docker is unavailable in this audit sandbox, but no resolve run was required precisely because no attack verified.

Refinement/model audit (refinement.md, mapping.md, meta.json): axioms=[], deep_model_references=[] (confirmed in meta.json). refinement.md contains ONLY R/I legs (A1 param finite-float-ndarray<->List Rat; A2 np.inf<->Threshold.top; A3 finiteSeq = identity-on-content, R+I; A4 np.r_[a,xs]<->cons, I). No A-consumed or A-reference legs exist (nothing on the A axis to falsify), and there are no kind-3 (inexpressible-changed-op) holes: the genuinely-changed op (finite max+1 lead -> infinite np.inf sentinel) is expressed DIRECTLY as the constructor Threshold.top, an R refinement of the value domain (Float being FFI-opaque / IEEE-inf unmodelable by cvc5, per mapping.md §2). The input carrier _binary_clf_curve (+ drop_intermediate) is UNCHANGED by the patch and run as the REAL callee by G-AX/G-CONF, not axiomatized; its two structural facts (base non-empty, all-finite) are discharged by axiom_check.py against the real repo, not by a Lean axiom. Model<->patch correspondence to gold line 1086 (np.r_[np.inf, thresholds]) holds under the stated bijection.

Conclusion: verify => gold-behavior on this bundle (exact-equality postcondition, sound R/I refinement, no A-legs to exploit). >=5 distinct attacks (7) run, none breaks the spec. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A decision threshold on a scoring function. A `value r` is an ordinary finite
   threshold (a score cut-off); `top` is the sentinel position that classifies
   NO instance as positive — it sits strictly above every attainable finite
   score, so the curve is anchored at the (0,0) corner. Modeling the sentinel as
   its own constructor (rather than a finite number) keeps it categorically apart
   from any real score: it can never be confused with, or compared as if it were,
   an ordinary value. Finite thresholds are carried as exact `Rat` because only
   their order/value matters here (mapping.md §2). -/
inductive Threshold where
  | value (r : Rat)
  | top
deriving DecidableEq

/- Lift a list of finite thresholds (the ordered cut-offs computed upstream) into
   the threshold domain, leaving each value untouched. -/
def finiteSeq (xs : List Rat) : List Threshold := xs.map Threshold.value
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Anchor a sequence of finite decision thresholds with one extra leading
   position so the resulting curve starts at the corner where no instance is
   predicted positive. `base` are the ordered finite thresholds produced
   upstream; the result is `base` (unchanged, in order) preceded by the sentinel
   that lies above every finite threshold. -/
method withLeadingSentinel (base : List Rat) return (out : List Threshold)
  require base ≠ []
  ensures out = Threshold.top :: finiteSeq base
  do
    -- impl-start
    let out : List Threshold := Threshold.top :: finiteSeq base
    return out
    -- impl-end

prove_correct withLeadingSentinel by loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec: method withLeadingSentinel (base : List Rat) return (out : List Threshold), require base != [], ensures out = Threshold.top :: finiteSeq base. This is an EXACT-EQUALITY postcondition over the FROZEN pure-region types (inductive Threshold = value Rat | top; finiteSeq = List.map Threshold.value). It fully pins the output, so any same-spec impl that verifies must produce byte-identical gold output. There is no room for a verifying-but-wrong impl.

Same-spec confirmation (swebench_unified.markers.same_spec, velvet): all 7 attacks + positive control report True (initial run showed False due to a generator bug that truncated the trailing 'prove_correct' line; regenerated to preserve the full tail, re-checked True for all).

Verification (bash scripts/lean_verify.sh <file>, run concurrently in two batches of 4 from project root):
  pos_control EXIT=0 (verifies)
  atk_1 EXIT=1  atk_2 EXIT=1  atk_3 EXIT=1  atk_4 EXIT=1  atk_5 EXIT=1  atk_6 EXIT=1  atk_7 EXIT=1
Every attack failure is a genuine loom_solve 'unsolved goals' on the postcondition (confirmed in per-file .log; not syntax errors).

Attacks (all edit ONLY the impl region; axioms/pure/pre/post byte-identical):
  atk_1 = PREPATCH bug: lead = Threshold.value (base.head! + 1) (finite max+1 lead). Reproduces the pre-patch behavior; fails 'value _ != top' at the head. prepatch_reproduced=true.
  atk_2 = partial/missing-sentinel: out = finiteSeq base (drops the leading sentinel entirely).
  atk_3 = boundary/order: out = finiteSeq base ++ [Threshold.top] (sentinel appended at TAIL not head).
  atk_4 = over-count / ungrounded-echo: out = Threshold.top :: Threshold.top :: finiteSeq base (two sentinels).
  atk_5 = control-flow-effect / partial-domain: match base with [x] => [top, value x] | _ => [top] (correct only for singletons, drops tail otherwise).
  atk_6 = order violation: out = Threshold.top :: finiteSeq base.reverse (tail reversed).
  atk_7 = ungrounded-oracle echo (wrong kind of lead): out = Threshold.value 0 :: finiteSeq base (prepends a finite value instead of the sentinel).

Resolve step: NO same-spec wrong impl verifies (all 7 exit 1), so there is no verifying-wrong-impl faithful patch to materialize and run through run_resolve. Step-2 obligation is vacuously satisfied; patches={} accordingly. Note: Docker is unavailable in this audit sandbox, but no resolve run was required precisely because no attack verified.

Refinement/model audit (refinement.md, mapping.md, meta.json): axioms=[], deep_model_references=[] (confirmed in meta.json). refinement.md contains ONLY R/I legs (A1 param finite-float-ndarray<->List Rat; A2 np.inf<->Threshold.top; A3 finiteSeq = identity-on-content, R+I; A4 np.r_[a,xs]<->cons, I). No A-consumed or A-reference legs exist (nothing on the A axis to falsify), and there are no kind-3 (inexpressible-changed-op) holes: the genuinely-changed op (finite max+1 lead -> infinite np.inf sentinel) is expressed DIRECTLY as the constructor Threshold.top, an R refinement of the value domain (Float being FFI-opaque / IEEE-inf unmodelable by cvc5, per mapping.md §2). The input carrier _binary_clf_curve (+ drop_intermediate) is UNCHANGED by the patch and run as the REAL callee by G-AX/G-CONF, not axiomatized; its two structural facts (base non-empty, all-finite) are discharged by axiom_check.py against the real repo, not by a Lean axiom. Model<->patch correspondence to gold line 1086 (np.r_[np.inf, thresholds]) holds under the stated bijection.

Conclusion: verify => gold-behavior on this bundle (exact-equality postcondition, sound R/I refinement, no A-legs to exploit). >=5 distinct attacks (7) run, none breaks the spec. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift / spec-too-strong) analysis for withLeadingSentinel modeling roc_curve's threshold-anchoring step (sklearn/metrics/_ranking.py:1086, np.r_[np.inf, thresholds]).

SPEC REGION: byte-identical between Solution.lean and Solution_prepatch.lean — swebench_unified.markers.same_spec(...,VelvetBackend()) = True. Spec is frozen and consumer-facing.

LEAN: Solution.lean verifies (lean_verify.sh exit 0). Solution_prepatch.lean (finite max+1 lead) fails on the exact head clause (Threshold.value (base.head!+1) :: ... = Threshold.top :: ..., unsolved) — so the ensures is a genuine discriminating constraint, not a tautology.

SPEC vs REAL REPO: modeled function out = Threshold.top :: finiteSeq base maps under the stated bijection (np.inf↔top; finite score↔Threshold.value r order/value-preserving; np.r_[a,xs]↔a::xs) exactly to the gold line thresholds = np.r_[np.inf, thresholds]. Verified against the REAL patched worktree (line 1091 confirmed np.r_[np.inf, thresholds]): re-ran conformance_check.py — shadow [np.inf, *base] agrees with the real roc_curve returned thresholds on 100007 inputs (seed 26194), 0 disagreements. No diverging input found.

PRECONDITION over-strength check (the usual spec-too-strong failure mode): require base ≠ [] does NOT exclude any real repo behavior. The input carrier _binary_clf_curve+drop_intermediate always yields a non-empty, all-finite thresholds vector (drop mask always retains first+last index np.r_[True,...,True]; scores pass assert_all_finite). G-AX confirms this on 20013 inputs. finiteSeq only requires finiteness, which holds for every real callee output. So the require/typing carve out no reachable input.

Abstraction (Rat for finite thresholds, top constructor for np.inf) is sound: G-CONF compares order+value which is all the anchoring step and F2P tests (np.isinf(thresholds[0]), thresholds[0]==inf) observe. No IEEE-specific behavior is modeled away that the change depends on.

Conclusion: the modeled function agrees with the real callee on every Requires-satisfying input, and Requires excludes no reachable input. Spec is FAITHFUL (not too strong, no drift).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Re-verified the accepted relaxed-leakage disposition rather than rubber-stamping it (meta.relaxed_leakage=true, G-LEAK status 'relaxed', RELAXED_LEAKAGE.md present). Findings:

(1) problem_statement scan (frozen instance): the PS reports only the SYMPTOM ('Thresholds can exceed 1 in roc_curve while providing probability estimate', with the tautology non-regression test np.logical_or(thresholds<=1, thresholds>=0)) and PROPOSES THE OPPOSITE REMEDY ('check thresholds.max()<=1 ... clip thresholds to not be above 1' — a finite cap). Token counts in problem_statement: inf=0, isinf=0, np.inf=0, infinit=0, sentinel=0. hints_text is the empty string. The infinite-sentinel discriminator (gold: thresholds=np.r_[np.inf,thresholds]) is NOT derivable from the PS — this is a genuine proven PS<->gold mismatch, not lazy de-narration.

(2) Spec view lexical scan clean: Solution.lean contains none of np.inf/inf/isinf/roc_curve/_ranking/sklearn/np.r_/1086/probability/clip/26194. The only shared word 'thresholds' also appears in the public PS, so it discloses nothing beyond it. The G-LEAK mechanical screen passes.

(3) The disclosed content is the SEMANTIC discriminator itself, living in the postcondition 'ensures out = Threshold.top :: finiteSeq base' and the abstract docstring 'sentinel ... above every finite threshold'. This is the minimum-necessary faithful pinning: any spec weak enough to hide the infinite sentinel would admit the PS-faithful finite-clip implementation, which G-DIFF requires to fail and which fails the hidden F2P tests (test_roc_curve_drop_intermediate, test_roc_curve_with_probablity_estimates np.isinf(thresholds[0])). Faithful ⟹ leaking is established; the leak is unavoidable.

(4) Core soundness re-checked independently: lean_verify Solution.lean -> exit 0 (verifies); Solution_prepatch.lean (finite lead value (base.head!+1)) -> exit 1, failing exactly on the discriminating head clause 'Threshold.value (base.head!+1) ::... = Threshold.top ::...' — the precise np.isinf(thresholds[0]) discriminator. Spec regions of Solution/prepatch are identical outside impl (pure/method/require/ensures byte-match by inspection). Gates blob: G-EQ/G-CONF/G-AX/G-DIFF/G-VERIFY/G-RESOLVE all pass.

The known dispositioned facet (infinite-sentinel lead) is re-confirmed as genuine + unavoidable + documented, and NO leaking line beyond it was found, and the disposition is not broken. Per gates/_audit.py + RELAXED_LEAKAGE.md panel-3 recording convention, the honest recording is NO-LEAKAGE (== pass).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
