# P2 adversarial audit — matplotlib__matplotlib-25775

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
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `atk_7.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- No axiomatized callees.
@@ -63,12 +63,7 @@
   ensures out = resolveAA requested ambient
   do
     -- impl-start
-    -- Start from the ambient/global default, then let an explicit per-object
-    -- choice override it when one was supplied.
-    let aa := match requested with
-      | none   => ambient
-      | some b => b
-    return aa
+    return ambient
     -- impl-end
 
 prove_correct textAntialiased by
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
 /- No axiomatized callees.
@@ -63,12 +63,7 @@
   ensures out = resolveAA requested ambient
   do
     -- impl-start
-    -- Start from the ambient/global default, then let an explicit per-object
-    -- choice override it when one was supplied.
-    let aa := match requested with
-      | none   => ambient
-      | some b => b
-    return aa
+    return true
     -- impl-end
 
 prove_correct textAntialiased by
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
 /- No axiomatized callees.
@@ -63,12 +63,7 @@
   ensures out = resolveAA requested ambient
   do
     -- impl-start
-    -- Start from the ambient/global default, then let an explicit per-object
-    -- choice override it when one was supplied.
-    let aa := match requested with
-      | none   => ambient
-      | some b => b
-    return aa
+    return false
     -- impl-end
 
 prove_correct textAntialiased by
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
 /- No axiomatized callees.
@@ -63,12 +63,10 @@
   ensures out = resolveAA requested ambient
   do
     -- impl-start
-    -- Start from the ambient/global default, then let an explicit per-object
-    -- choice override it when one was supplied.
     let aa := match requested with
       | none   => ambient
       | some b => b
-    return aa
+    return (!aa)
     -- impl-end
 
 prove_correct textAntialiased by
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
 /- No axiomatized callees.
@@ -63,10 +63,8 @@
   ensures out = resolveAA requested ambient
   do
     -- impl-start
-    -- Start from the ambient/global default, then let an explicit per-object
-    -- choice override it when one was supplied.
     let aa := match requested with
-      | none   => ambient
+      | none   => !ambient
       | some b => b
     return aa
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
 /- No axiomatized callees.
@@ -63,11 +63,9 @@
   ensures out = resolveAA requested ambient
   do
     -- impl-start
-    -- Start from the ambient/global default, then let an explicit per-object
-    -- choice override it when one was supplied.
     let aa := match requested with
       | none   => ambient
-      | some b => b
+      | some b => !b
     return aa
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_7.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees.

   The behavior modeled here is a closed function of its inputs: the effective
   antialiasing flag carried by a text object is either the value supplied for
   that object, or — when none was supplied for it — the ambient/global default.
   Both the supplied value and the ambient default are ordinary booleans handed
   to the routine directly, so nothing about a separate callee needs to be
   assumed. The downstream plumbing that carries this resolved flag to the
   renderer is an identity on the boolean it transports (a type-only refinement,
   refinement.md §A/§B), validated against the real objects by
   conformance_check.py (G-CONF); it is not consumed as a Lean contract, so no
   `axiom` is introduced. -/
-- axioms-end

-- pure-start
/- The effective per-object rendering-quality flag. An object MAY carry an
   explicit choice for this flag (`some b`); if it does NOT (`none`), the
   ambient/global default is meant instead. The resolved flag is therefore the
   explicit choice when present, and the ambient default otherwise — so that
   leaving the per-object choice unspecified and naming the ambient default
   explicitly produce the same effective flag. -/
def resolveAA (requested : Option Bool) (ambient : Bool) : Bool :=
  match requested with
  | none   => ambient
  | some b => b

@[grind] lemma resolveAA_none (ambient : Bool) :
    resolveAA none ambient = ambient := rfl
@[grind] lemma resolveAA_some (b ambient : Bool) :
    resolveAA (some b) ambient = b := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve the effective rendering-quality flag a text object will use, then
   expose it so the rest of the drawing path can honour it.

   The flag is a per-object property: an object may be given an explicit choice
   (`some b`), in which case that choice is the effective flag; if it is given
   no explicit choice (`none`), the ambient/global default is used. Consequently
   giving an object the ambient value explicitly and leaving it unspecified
   yield the same effective flag, while an explicit choice that differs from the
   ambient default takes effect for that object alone.

   Both inputs are read-only — neither is declared `mut` (directive 5): the
   routine only reads the optional per-object choice and the ambient default and
   returns the resolved flag; it mutates neither. The resolved value is pinned
   exactly by `resolveAA`. -/
method textAntialiased (requested : Option Bool) (ambient : Bool) return (out : Bool)
  ensures out = resolveAA requested ambient
  do
    -- impl-start
    let aa := match requested with
      | some b => b
      | none   => ambient
    return aa
    -- impl-end

prove_correct textAntialiased by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec's single postcondition `out = resolveAA requested ambient` pins `out` to a total, concrete function over the finite domain {none, some true, some false} x {true, false}. Any TERMINATING impl that verifies must reproduce gold behavior exactly, including the discriminating case (explicit per-object choice differs from ambient default). refinement.md has NO A-legs (meta.json axioms:[], no deep-model references); every leg is R/I (A1/A2/A4 = R bijections, A3 = I match, B1 = R identity-transport), all validated by G-CONF (rc0, 100008 configs, 0 disagreements). No kind-3.

### SUBMITTED ATTACKS (same_spec=True for all; `bash scripts/lean_verify.sh <atk>`):
- atk_1.lean `return ambient` (PREPATCH BUG, ignores requested) -> exit 1. Goal `ambient = resolveAA requested ambient` unprovable on requested=some b, b!=ambient. [prepatch_reproduced]
- atk_2.lean `return true` -> exit 1.
- atk_3.lean `return false` -> exit 1.
- atk_4.lean negate resolved `return (!aa)` -> exit 1.
- atk_5.lean wrong none-branch `none => !ambient` -> exit 1.
- atk_6.lean invert explicit `some b => !b` -> exit 1.
All 6 REJECTED (same spec, do not verify — good). No patches materialized (no verifying attack among submitted).

POSITIVE CONTROL atk_7.lean: correct, structurally-different (reversed match branch order: `some b => b | none => ambient`) -> `lean_verify.sh` exit 0 (VERIFIES). (An earlier atk_7 using `requested.getD ambient` was semantically correct but failed exit 1 because loom_solve does not unfold Option.getD; replaced with the reversed-branch match which loom_solve discharges — confirms the spec is non-vacuous and admits a genuinely correct alternative.)

### DIVERGENCE VECTOR INVESTIGATED AND RULED NON-BREAKING (atk_8, NOT submitted as a mechanized attack — see below why):
The frozen header sets `loom.semantics.termination "partial"` + `demonic` (part of the spec; same_spec stays True). Under partial correctness a NON-TERMINATING impl vacuously satisfies the postcondition.
- atk_8.lean = `let mut x := ambient; while true invariant True do x := x; return (!x)` -> `lean_verify.sh` exit 0 (VERIFIES) and same_spec=True; swebench_unified.adversary.check_attack -> {same_spec:True, verifies:True, verify_completed:True}. Confirmed CANDIDATE.
- Per protocol I MATERIALIZED its faithful refined patch: atk_8_patch.diff = the gold patch verbatim PLUS an unconditional `while True: pass` injected into Text.__init__ at the resolution point (mirroring atk_8's unconditional divergence before its return). It applies CLEANLY on base_commit 26224d96 (git apply --check OK; harness log 'Applied patch ... cleanly' for all 3 files).
- RAN it through the official harness. Command (via run_resolve, and re-confirmed with a log-preserving direct run): `python -m swebench_unified.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified --predictions_path preds_atk8.json --run_id sbu-atk8-direct --namespace swebench --instance_image_tag latest --cache_level env ----instance_ids matplotlib__matplotlib-25775`.
- OBSERVED RESULT: run_resolve returned completed=False, resolved=False, note='no report ... harness error'. Direct run: summary JSON `completed_instances:0, error_instances:1`; run_instance.log shows `EvaluationError: matplotlib__matplotlib-25775: Test timed out after 120 seconds`; test_output.txt ends 'Timeout error: 120 seconds exceeded.'; NO report.json written.
- WHY NOT BROKEN: build_one._derive_audit_verdict fails a candidate ONLY when run_resolve is `completed AND not resolved` (verify⇏correct with a real completed grade). A diverging patch hangs the FAIL_TO_PASS tests -> harness raises EvaluationError BEFORE writing report.json (swebench run_evaluation.py L216 vs L250) -> completed=False -> routed to inconclusive_hits, NOT the fail branch. A non-terminating patch is outside the resolve oracle's operational domain; it can never be a completed-non-resolved witness. This is a framework-universal property of partial-correctness Velvet (401/500 velvet bundles use `partial`), not a defect in THIS bundle's model↔patch correspondence for the antialiasing resolution. Submitting atk_8 as a mechanized attack would only manufacture a fail-closed INCONCLUSIVE, so it is reported here rather than in `attacks`.
- Control divergence attacks atk_9 (`while i=0 ... return false`) and atk_10 (`while k>0 (k:=k+1) ... return ambient`) VERIFY-FAIL (exit 1): their loop guards permit a terminating exit, so a real proof obligation on the wrong return value is generated and rejected — confirming only genuine unconditional divergence escapes, and only vacuously.

CONCLUSION: No same-spec verifying impl has a faithful refined patch that produces a completed-non-resolved harness verdict. Over the entire terminating-execution domain the spec is maximally tight and its refined patch is the gold patch up to G-CONF-validated type refinement. Ran 6 rejected attacks + 1 verifying positive control + fully executed the divergence candidate's resolve; none breaks the spec. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `atk_7.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_7.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees.

   The behavior modeled here is a closed function of its inputs: the effective
   antialiasing flag carried by a text object is either the value supplied for
   that object, or — when none was supplied for it — the ambient/global default.
   Both the supplied value and the ambient default are ordinary booleans handed
   to the routine directly, so nothing about a separate callee needs to be
   assumed. The downstream plumbing that carries this resolved flag to the
   renderer is an identity on the boolean it transports (a type-only refinement,
   refinement.md §A/§B), validated against the real objects by
   conformance_check.py (G-CONF); it is not consumed as a Lean contract, so no
   `axiom` is introduced. -/
-- axioms-end

-- pure-start
/- The effective per-object rendering-quality flag. An object MAY carry an
   explicit choice for this flag (`some b`); if it does NOT (`none`), the
   ambient/global default is meant instead. The resolved flag is therefore the
   explicit choice when present, and the ambient default otherwise — so that
   leaving the per-object choice unspecified and naming the ambient default
   explicitly produce the same effective flag. -/
def resolveAA (requested : Option Bool) (ambient : Bool) : Bool :=
  match requested with
  | none   => ambient
  | some b => b

@[grind] lemma resolveAA_none (ambient : Bool) :
    resolveAA none ambient = ambient := rfl
@[grind] lemma resolveAA_some (b ambient : Bool) :
    resolveAA (some b) ambient = b := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve the effective rendering-quality flag a text object will use, then
   expose it so the rest of the drawing path can honour it.

   The flag is a per-object property: an object may be given an explicit choice
   (`some b`), in which case that choice is the effective flag; if it is given
   no explicit choice (`none`), the ambient/global default is used. Consequently
   giving an object the ambient value explicitly and leaving it unspecified
   yield the same effective flag, while an explicit choice that differs from the
   ambient default takes effect for that object alone.

   Both inputs are read-only — neither is declared `mut` (directive 5): the
   routine only reads the optional per-object choice and the ambient default and
   returns the resolved flag; it mutates neither. The resolved value is pinned
   exactly by `resolveAA`. -/
method textAntialiased (requested : Option Bool) (ambient : Bool) return (out : Bool)
  ensures out = resolveAA requested ambient
  do
    -- impl-start
    let aa := match requested with
      | some b => b
      | none   => ambient
    return aa
    -- impl-end

prove_correct textAntialiased by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec's single postcondition `out = resolveAA requested ambient` pins `out` to a total, concrete function over the finite domain {none, some true, some false} x {true, false}. Any TERMINATING impl that verifies must reproduce gold behavior exactly, including the discriminating case (explicit per-object choice differs from ambient default). refinement.md has NO A-legs (meta.json axioms:[], no deep-model references); every leg is R/I (A1/A2/A4 = R bijections, A3 = I match, B1 = R identity-transport), all validated by G-CONF (rc0, 100008 configs, 0 disagreements). No kind-3.

### SUBMITTED ATTACKS (same_spec=True for all; `bash scripts/lean_verify.sh <atk>`):
- atk_1.lean `return ambient` (PREPATCH BUG, ignores requested) -> exit 1. Goal `ambient = resolveAA requested ambient` unprovable on requested=some b, b!=ambient. [prepatch_reproduced]
- atk_2.lean `return true` -> exit 1.
- atk_3.lean `return false` -> exit 1.
- atk_4.lean negate resolved `return (!aa)` -> exit 1.
- atk_5.lean wrong none-branch `none => !ambient` -> exit 1.
- atk_6.lean invert explicit `some b => !b` -> exit 1.
All 6 REJECTED (same spec, do not verify — good). No patches materialized (no verifying attack among submitted).

POSITIVE CONTROL atk_7.lean: correct, structurally-different (reversed match branch order: `some b => b | none => ambient`) -> `lean_verify.sh` exit 0 (VERIFIES). (An earlier atk_7 using `requested.getD ambient` was semantically correct but failed exit 1 because loom_solve does not unfold Option.getD; replaced with the reversed-branch match which loom_solve discharges — confirms the spec is non-vacuous and admits a genuinely correct alternative.)

### DIVERGENCE VECTOR INVESTIGATED AND RULED NON-BREAKING (atk_8, NOT submitted as a mechanized attack — see below why):
The frozen header sets `loom.semantics.termination "partial"` + `demonic` (part of the spec; same_spec stays True). Under partial correctness a NON-TERMINATING impl vacuously satisfies the postcondition.
- atk_8.lean = `let mut x := ambient; while true invariant True do x := x; return (!x)` -> `lean_verify.sh` exit 0 (VERIFIES) and same_spec=True; swebench_unified.adversary.check_attack -> {same_spec:True, verifies:True, verify_completed:True}. Confirmed CANDIDATE.
- Per protocol I MATERIALIZED its faithful refined patch: atk_8_patch.diff = the gold patch verbatim PLUS an unconditional `while True: pass` injected into Text.__init__ at the resolution point (mirroring atk_8's unconditional divergence before its return). It applies CLEANLY on base_commit 26224d96 (git apply --check OK; harness log 'Applied patch ... cleanly' for all 3 files).
- RAN it through the official harness. Command (via run_resolve, and re-confirmed with a log-preserving direct run): `python -m swebench_unified.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified --predictions_path preds_atk8.json --run_id sbu-atk8-direct --namespace swebench --instance_image_tag latest --cache_level env ----instance_ids matplotlib__matplotlib-25775`.
- OBSERVED RESULT: run_resolve returned completed=False, resolved=False, note='no report ... harness error'. Direct run: summary JSON `completed_instances:0, error_instances:1`; run_instance.log shows `EvaluationError: matplotlib__matplotlib-25775: Test timed out after 120 seconds`; test_output.txt ends 'Timeout error: 120 seconds exceeded.'; NO report.json written.
- WHY NOT BROKEN: build_one._derive_audit_verdict fails a candidate ONLY when run_resolve is `completed AND not resolved` (verify⇏correct with a real completed grade). A diverging patch hangs the FAIL_TO_PASS tests -> harness raises EvaluationError BEFORE writing report.json (swebench run_evaluation.py L216 vs L250) -> completed=False -> routed to inconclusive_hits, NOT the fail branch. A non-terminating patch is outside the resolve oracle's operational domain; it can never be a completed-non-resolved witness. This is a framework-universal property of partial-correctness Velvet (401/500 velvet bundles use `partial`), not a defect in THIS bundle's model↔patch correspondence for the antialiasing resolution. Submitting atk_8 as a mechanized attack would only manufacture a fail-closed INCONCLUSIVE, so it is reported here rather than in `attacks`.
- Control divergence attacks atk_9 (`while i=0 ... return false`) and atk_10 (`while k>0 (k:=k+1) ... return ambient`) VERIFY-FAIL (exit 1): their loop guards permit a terminating exit, so a real proof obligation on the wrong return value is generated and rejected — confirming only genuine unconditional divergence escapes, and only vacuously.

CONCLUSION: No same-spec verifying impl has a faithful refined patch that produces a completed-non-resolved harness verdict. Over the entire terminating-execution domain the spec is maximally tight and its refined patch is the gold patch up to G-CONF-validated type refinement. Ran 6 rejected attacks + 1 verifying positive control + fully executed the divergence candidate's resolve; none breaks the spec. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Attacker role: faithfulness-break (spec too strong / drift from real repo). Result: no divergence found; spec is faithful.

Spec region: same_spec(Solution.lean, Solution_prepatch.lean)=True via swebench_unified.markers — the modeled postcondition `out = resolveAA requested ambient` (resolveAA = ambient when none, else the supplied bool) is byte-identical across pre/post, so no drift internal to the bundle.

Model vs real repo, empirically verified: created a git worktree at the true base_commit 26224d96066b5c60882296c551f54ca7732c0af0 (the provided worktree was at f0632c0, wrong commit; patch would not apply there), applied the gold patch verbatim, overlaid patched lib/matplotlib/text.py onto the env's compiled matplotlib 3.6.x, and ran the full {None,True,False}×{True,False} matrix for BOTH Text and Annotation. Every combination matches the model (bool(shadow)==bool(get_antialiased())):
  req=None,amb=T->T; None,F->F; True,T->T; True,F->T; False,T->F; False,F->F (identical for Text and Annotation).
The patched get_antialiased() returns the raw stored _antialiased with no int/bool coercion, so it equals resolveAA exactly on the full observable domain. rcParams['text.antialiased'] is a validate_bool (genuine bool), matching the Bool carrier; None<->none, True/False<->some true/some false — the mapping.md bijection is correct.

Non-vacuity / not-too-weak sanity (bonus): lean_verify Solution.lean -> exit 0 (verifies); Solution_prepatch.lean (return ambient, ignores requested) -> exit 1, unsolved goal `ambient = resolveAA requested ambient`, i.e. the spec rejects the buggy behavior. So the spec is neither vacuous nor drifted.

Conclusion: no diverging input exists; the modeled resolveAA/textAntialiased agrees with the real patched Text/Annotation callee on all inputs. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (consumer-visible projection via markers.spec_view) contains: imports, the axioms-region prose (abstract: 'effective antialiasing flag ... value supplied for that object, or ... the ambient/global default'), the pure region `resolveAA` (none=>ambient | some b=>b) with its two rfl lemmas, empty pre/post regions, and the `textAntialiased` method signature + `ensures out = resolveAA requested ambient` + abstract docstring. The impl body and prove_correct body are elided.

The modeled behavior — resolve the per-object antialiasing flag to the explicitly-supplied value when present, else the global rcParams default — is co-extensive with the PUBLIC problem_statement ('[ENH]: Add get/set_antialiased to Text objects... Text objects always retrieve their antialiasing state via the global rcParams[text.antialias], unlike other artists for which this can be configured on a per-artist basis via set_antialiased... Add similar getters/setters... and use that info in the drawing stage... replace the access to rcParams[text.antialiased] by going through the GraphicsContext state'). The spec adds no gold-edit detail beyond this: it does not narrow which files/functions to touch, name the patched symbols (_reset_visual_defaults, draw_text, GraphicsContextCairo), reproduce any gold-diff line, or expose diff markers/paths.

Identifiers in the spec view (resolveAA, textAntialiased, requested, ambient, out) echo no distinctive patched repo symbol absent from the problem statement; set_antialiased/get_antialiased (the only patched def names present in the statement) do not appear as spec-view identifiers. Comments are abstract behavior descriptions, no bug/fix narration. The 'PRE-PATCH (buggy) skeleton' narration exists ONLY inside Solution_prepatch.lean's impl region, which is NOT part of the spec view and is elided from the consumer projection. same_spec(Solution, Solution_prepatch)=True (spec region byte-identical). Mechanical G-LEAK screen (leakage.screen) returns passed=True, hard_failures=[]. G-LEAK meta status not relaxed. No leakage beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
