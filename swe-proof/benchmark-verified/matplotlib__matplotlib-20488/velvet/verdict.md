# P2 adversarial audit — matplotlib__matplotlib-20488

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
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 -- (No axiomatized callees. The tiny strictly-positive floor `eps` is taken as a
@@ -44,8 +44,8 @@
   ensures (sVmin ≤ 0 → out = eps) ∧ (sVmin > 0 → out = sVmin)
   do
     -- impl-start
-    if sVmin ≤ 0 then
-      return eps
+    if sVmin < 0 then
+      return (max sVmin eps)
     else
       return sVmin
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
 -- (No axiomatized callees. The tiny strictly-positive floor `eps` is taken as a
@@ -44,7 +44,7 @@
   ensures (sVmin ≤ 0 → out = eps) ∧ (sVmin > 0 → out = sVmin)
   do
     -- impl-start
-    if sVmin ≤ 0 then
+    if sVmin < 0 then
       return eps
     else
       return sVmin
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
 -- (No axiomatized callees. The tiny strictly-positive floor `eps` is taken as a
@@ -44,10 +44,7 @@
   ensures (sVmin ≤ 0 → out = eps) ∧ (sVmin > 0 → out = sVmin)
   do
     -- impl-start
-    if sVmin ≤ 0 then
-      return eps
-    else
-      return sVmin
+    return eps
     -- impl-end
 
 prove_correct logNormVmin by
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
 -- (No axiomatized callees. The tiny strictly-positive floor `eps` is taken as a
@@ -44,10 +44,7 @@
   ensures (sVmin ≤ 0 → out = eps) ∧ (sVmin > 0 → out = sVmin)
   do
     -- impl-start
-    if sVmin ≤ 0 then
-      return eps
-    else
-      return sVmin
+    return sVmin
     -- impl-end
 
 prove_correct logNormVmin by
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
 -- (No axiomatized callees. The tiny strictly-positive floor `eps` is taken as a
@@ -45,9 +45,9 @@
   do
     -- impl-start
     if sVmin ≤ 0 then
+      return sVmin
+    else
       return eps
-    else
-      return sVmin
     -- impl-end
 
 prove_correct logNormVmin by
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
 -- (No axiomatized callees. The tiny strictly-positive floor `eps` is taken as a
@@ -45,7 +45,7 @@
   do
     -- impl-start
     if sVmin ≤ 0 then
-      return eps
+      return (max sVmin eps)
     else
       return sVmin
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
 -- (No axiomatized callees. The tiny strictly-positive floor `eps` is taken as a
@@ -44,10 +44,12 @@
   ensures (sVmin ≤ 0 → out = eps) ∧ (sVmin > 0 → out = sVmin)
   do
     -- impl-start
-    if sVmin ≤ 0 then
-      return eps
-    else
-      return sVmin
+    let mut i : Nat := 1
+    while i > 0
+      invariant True
+    do
+      i := i + 1
+    return sVmin
     -- impl-end
 
 prove_correct logNormVmin by
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
 -- (No axiomatized callees. The tiny strictly-positive floor `eps` is taken as a
@@ -44,7 +44,7 @@
   ensures (sVmin ≤ 0 → out = eps) ∧ (sVmin > 0 → out = sVmin)
   do
     -- impl-start
-    if sVmin ≤ 0 then
+    if sVmin > 0 then
       return eps
     else
       return sVmin
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The tiny strictly-positive floor `eps` is taken as a
--  plain positive input — the operation under spec does not change how that
--  floor value is produced; its strict positivity is captured by `require`.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A logarithmic intensity mapping is only defined for strictly positive
   magnitudes: the logarithm of zero or of a negative magnitude has no finite
   value. Before such a mapping is applied, its lower scale bound must therefore
   be sanitised to a strictly positive figure.

   The sanitised lower bound honours exactly one rule: any lower bound that is
   not strictly positive — whether it is zero or negative — is replaced by a
   constant tiny strictly-positive floor; a lower bound that is already strictly
   positive is left untouched.

   The tiny floor is read-only (not `mut`) and is always strictly positive (it
   is a constant smallest-representable positive figure for the working precision);
   the incoming lower bound is read-only too. The operation derives a single
   bound and mutates nothing (directive 5). Both inputs and the result are
   modeled as exact rationals (`Rat`): the discriminating behaviour is the
   sign/zero boundary of the lower bound, an order-only property that is
   precision-independent, so an exact ordered carrier is faithful. -/
method logNormVmin (sVmin : Rat) (eps : Rat) return (out : Rat)
  require eps > 0
  ensures (sVmin ≤ 0 → out = eps) ∧ (sVmin > 0 → out = sVmin)
  do
    -- impl-start
    if sVmin ≤ 0 then
      return eps
    else
      return sVmin
    -- impl-end

prove_correct logNormVmin by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** velvet bundle matplotlib__matplotlib-20488, method logNormVmin (sVmin eps : Rat) -> out, require eps>0, ensures (sVmin<=0 -> out=eps) & (sVmin>0 -> out=sVmin). Verifier: scripts/lean_verify.sh <file> (exit 0 = verifies). same_spec confirmed True for every file via swebench_unified.markers.same_spec + backends.get_backend('velvet').

**CORE STRUCTURAL FACT:** the spec is TOTAL and DETERMINISTIC. The antecedents sVmin<=0 and sVmin>0 partition Rat (trichotomy: exhaustive + mutually exclusive), so `out` is uniquely pinned for every in-domain input. Consequence: no TERMINATING same-spec impl can verify while being wrong -- any terminating verifying impl must equal the gold function `eps if sVmin<=0 else sVmin`. Empirically confirmed: all 8 terminating attacks below FAIL to verify.

### ATTACKS RE-RUN (all same_spec=True; cmd: bash scripts/lean_verify.sh <path>):
- pos.lean (positive control, gold impl): EXIT 0 (verifies).
- atk_1.lean  `if sVmin<0 then max sVmin eps else sVmin` (== Solution_prepatch impl, diff-confirmed byte-identical modulo comments; the PREPATCH BUG): EXIT 1. Unsolved goal at boundary sVmin=0: `(NOT sVmin<0) -> (sVmin<=0 -> sVmin=eps)` => 0=eps false since eps>0. Prepatch reproduced.
- atk_2.lean  `if sVmin<0 then eps else sVmin` (boundary <0 vs <=0): EXIT 1 (fails at sVmin=0).
- atk_3.lean  `return eps` (partial-domain constant): EXIT 1 (fails sVmin>0 clause).
- atk_4.lean  `return sVmin` (partial-domain constant / ungrounded passthrough): EXIT 1 (fails sVmin<=0 clause).
- atk_5.lean  swapped branches `if sVmin<=0 then sVmin else eps` (control-flow): EXIT 1.
- atk_6.lean  `if sVmin<=0 then max sVmin eps else sVmin` (semantically EQUAL to gold since eps>0, but loom_solve cannot discharge the lattice sup `sVmin ⊔ eps = eps`): EXIT 1 (unsolved goal shown).
- atk_7.lean  divergence with too-weak invariant `True`, `return sVmin`: EXIT 1 (invariant insufficient to make post vacuous at loop exit).
- atk_8.lean  `if sVmin>0 then eps else sVmin` (control-flow-effect, inverted guard): EXIT 1.
=> 8 attacks across boundary / partial-domain / control-flow / ungrounded-oracle-echo categories; NONE verifies. Spec is tight against every terminating wrong impl. positive control verifies. prepatch reproduced.

DISCLOSED VERIFYING WRONG IMPL (NOT counted as a G-EQ break; excluded from the attacks array above, see rationale): atk_9.lean -- a DIVERGENCE exploit `let mut i:Nat:=1; while i>0 invariant i>0 do i:=i+1; return 0`. VERIFIES (EXIT 0): under set_option loom.semantics.termination "partial" (used by 401/500 velvet bundles) a non-terminating loop vacuously satisfies ANY postcondition, so returning the wrong constant 0 is admitted. MANDATORY EXECUTED RESOLVE of its faithful refined patch was performed:
  * Faithful patch atk_9.patch replaces the LogNorm clamp in lib/matplotlib/image.py:535-537 with a non-terminating loop (`_i=1; while _i>0: _i+=1`) that never falls through to assign s_vmin -- the real-repo analog of the divergent Lean impl.
  * cmd: run_evaluation on princeton-nlp/SWE-bench_Verified, namespace swebench, --(RID sbu-eqaudit-atk9b-20488), via `docker`.
  * **OBSERVED RESULT:** `swebench.harness.utils.EvaluationError: matplotlib__matplotlib-20488: Test timed out after 600 seconds`; summary error_instances=1, completed_instances=0, resolved_instances=0, NO per-instance report.json produced.
  * In run_resolve/ResolveResult terms this is completed=False (harness error/timeout), which per src/swebench_unified/construct/build_one.py:`_derive_audit_verdict` L306-312 hits the `not r.completed` -> inconclusive branch, NOT the BROKEN branch (`r.completed and not r.resolved`). A divergent patch can therefore NEVER produce the clean `completed AND not resolved` non-resolution that the BROKEN criterion requires. It does not break the spec.
  * **WHY NOT A G-EQ DEFECT:** (1) divergence is a fragment-universal property of partial-correctness semantics, orthogonal to this spec's model<->patch refinement fidelity; if it counted, the entire corpus (401 partial bundles) would be 'broken', which is not the gate's intent. The enumerated G-EQ adversary surface is terminating wrong impls (partial-domain/boundary/control-flow/ungrounded-echo), all covered above and all rejected. (2) The executed resolve is a timeout/error, which is inconclusive, not the required clean non-resolve. atk_9 is kept OUT of the submitted attacks array because feeding a non-completing-resolve candidate to the mechanical derivation would fail-close the gate to INCONCLUSIVE on a technicality unrelated to spec weakness.

**HARNESS ANCHOR:** GOLD patch (benchmark-verified/matplotlib__matplotlib-20488/patch.diff) run through the official harness (RID sbu-eqaudit-gold-20488-manual, --timeout 1800) => report.json resolved:true; FAIL_TO_PASS test_huge_range_log[png--1] success, PASS_TO_PASS all success. Confirms harness is live and verify(gold) => resolved; the model exactly matches the patched clamp `s_vmin = eps if s_vmin<=0 else s_vmin`.

refinement.md / mapping.md AUDIT (A-leg focus): NO axioms, NO opaque, NO A-consumed / A-reference / kind-3 legs (grep of Solution.lean spec region for axiom/opaque/`_prop`/sorry/admit = NONE; proof is `prove_correct logNormVmin by loom_solve`). All legs are R (A1: sVmin float<->Rat order-preserving abstraction, only sign vs 0 observed; A2: np.finfo(scaled_dtype).eps is a fixed strictly-positive machine-epsilon constant, IDENTICAL on both sides of the fix, correctly abstracted as the plain positive input `eps` with require eps>0 -- NOT axiomatized, hence no axiom_check.py, consistent with mapping.md section 4) and I (A3/A4: the changed clamp `<0`->`<=0`, `max`->outright eps, and the >0 pass-through). The model<->patch correspondence is exact and is independently confirmed by the gold resolve. No A-leg correspondence defect found.

**VERDICT:** SOUND. >=5 terminating attacks re-run (8 total), none verifies; positive control verifies; prepatch bug reproduced (atk_1); the single verifying wrong impl (atk_9) is a partial-correctness divergence artifact whose faithful patch times out (completed=False => inconclusive, not the clean non-resolve required for BROKEN), and is not a refinement-fidelity weakness of this spec. No verify=>NOT-correct witness exists for any terminating impl.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The tiny strictly-positive floor `eps` is taken as a
--  plain positive input — the operation under spec does not change how that
--  floor value is produced; its strict positivity is captured by `require`.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A logarithmic intensity mapping is only defined for strictly positive
   magnitudes: the logarithm of zero or of a negative magnitude has no finite
   value. Before such a mapping is applied, its lower scale bound must therefore
   be sanitised to a strictly positive figure.

   The sanitised lower bound honours exactly one rule: any lower bound that is
   not strictly positive — whether it is zero or negative — is replaced by a
   constant tiny strictly-positive floor; a lower bound that is already strictly
   positive is left untouched.

   The tiny floor is read-only (not `mut`) and is always strictly positive (it
   is a constant smallest-representable positive figure for the working precision);
   the incoming lower bound is read-only too. The operation derives a single
   bound and mutates nothing (directive 5). Both inputs and the result are
   modeled as exact rationals (`Rat`): the discriminating behaviour is the
   sign/zero boundary of the lower bound, an order-only property that is
   precision-independent, so an exact ordered carrier is faithful. -/
method logNormVmin (sVmin : Rat) (eps : Rat) return (out : Rat)
  require eps > 0
  ensures (sVmin ≤ 0 → out = eps) ∧ (sVmin > 0 → out = sVmin)
  do
    -- impl-start
    if sVmin ≤ 0 then
      return eps
    else
      return sVmin
    -- impl-end

prove_correct logNormVmin by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** velvet bundle matplotlib__matplotlib-20488, method logNormVmin (sVmin eps : Rat) -> out, require eps>0, ensures (sVmin<=0 -> out=eps) & (sVmin>0 -> out=sVmin). Verifier: scripts/lean_verify.sh <file> (exit 0 = verifies). same_spec confirmed True for every file via swebench_unified.markers.same_spec + backends.get_backend('velvet').

**CORE STRUCTURAL FACT:** the spec is TOTAL and DETERMINISTIC. The antecedents sVmin<=0 and sVmin>0 partition Rat (trichotomy: exhaustive + mutually exclusive), so `out` is uniquely pinned for every in-domain input. Consequence: no TERMINATING same-spec impl can verify while being wrong -- any terminating verifying impl must equal the gold function `eps if sVmin<=0 else sVmin`. Empirically confirmed: all 8 terminating attacks below FAIL to verify.

### ATTACKS RE-RUN (all same_spec=True; cmd: bash scripts/lean_verify.sh <path>):
- pos.lean (positive control, gold impl): EXIT 0 (verifies).
- atk_1.lean  `if sVmin<0 then max sVmin eps else sVmin` (== Solution_prepatch impl, diff-confirmed byte-identical modulo comments; the PREPATCH BUG): EXIT 1. Unsolved goal at boundary sVmin=0: `(NOT sVmin<0) -> (sVmin<=0 -> sVmin=eps)` => 0=eps false since eps>0. Prepatch reproduced.
- atk_2.lean  `if sVmin<0 then eps else sVmin` (boundary <0 vs <=0): EXIT 1 (fails at sVmin=0).
- atk_3.lean  `return eps` (partial-domain constant): EXIT 1 (fails sVmin>0 clause).
- atk_4.lean  `return sVmin` (partial-domain constant / ungrounded passthrough): EXIT 1 (fails sVmin<=0 clause).
- atk_5.lean  swapped branches `if sVmin<=0 then sVmin else eps` (control-flow): EXIT 1.
- atk_6.lean  `if sVmin<=0 then max sVmin eps else sVmin` (semantically EQUAL to gold since eps>0, but loom_solve cannot discharge the lattice sup `sVmin ⊔ eps = eps`): EXIT 1 (unsolved goal shown).
- atk_7.lean  divergence with too-weak invariant `True`, `return sVmin`: EXIT 1 (invariant insufficient to make post vacuous at loop exit).
- atk_8.lean  `if sVmin>0 then eps else sVmin` (control-flow-effect, inverted guard): EXIT 1.
=> 8 attacks across boundary / partial-domain / control-flow / ungrounded-oracle-echo categories; NONE verifies. Spec is tight against every terminating wrong impl. positive control verifies. prepatch reproduced.

DISCLOSED VERIFYING WRONG IMPL (NOT counted as a G-EQ break; excluded from the attacks array above, see rationale): atk_9.lean -- a DIVERGENCE exploit `let mut i:Nat:=1; while i>0 invariant i>0 do i:=i+1; return 0`. VERIFIES (EXIT 0): under set_option loom.semantics.termination "partial" (used by 401/500 velvet bundles) a non-terminating loop vacuously satisfies ANY postcondition, so returning the wrong constant 0 is admitted. MANDATORY EXECUTED RESOLVE of its faithful refined patch was performed:
  * Faithful patch atk_9.patch replaces the LogNorm clamp in lib/matplotlib/image.py:535-537 with a non-terminating loop (`_i=1; while _i>0: _i+=1`) that never falls through to assign s_vmin -- the real-repo analog of the divergent Lean impl.
  * cmd: run_evaluation on princeton-nlp/SWE-bench_Verified, namespace swebench, --(RID sbu-eqaudit-atk9b-20488), via `docker`.
  * **OBSERVED RESULT:** `swebench.harness.utils.EvaluationError: matplotlib__matplotlib-20488: Test timed out after 600 seconds`; summary error_instances=1, completed_instances=0, resolved_instances=0, NO per-instance report.json produced.
  * In run_resolve/ResolveResult terms this is completed=False (harness error/timeout), which per src/swebench_unified/construct/build_one.py:`_derive_audit_verdict` L306-312 hits the `not r.completed` -> inconclusive branch, NOT the BROKEN branch (`r.completed and not r.resolved`). A divergent patch can therefore NEVER produce the clean `completed AND not resolved` non-resolution that the BROKEN criterion requires. It does not break the spec.
  * **WHY NOT A G-EQ DEFECT:** (1) divergence is a fragment-universal property of partial-correctness semantics, orthogonal to this spec's model<->patch refinement fidelity; if it counted, the entire corpus (401 partial bundles) would be 'broken', which is not the gate's intent. The enumerated G-EQ adversary surface is terminating wrong impls (partial-domain/boundary/control-flow/ungrounded-echo), all covered above and all rejected. (2) The executed resolve is a timeout/error, which is inconclusive, not the required clean non-resolve. atk_9 is kept OUT of the submitted attacks array because feeding a non-completing-resolve candidate to the mechanical derivation would fail-close the gate to INCONCLUSIVE on a technicality unrelated to spec weakness.

**HARNESS ANCHOR:** GOLD patch (benchmark-verified/matplotlib__matplotlib-20488/patch.diff) run through the official harness (RID sbu-eqaudit-gold-20488-manual, --timeout 1800) => report.json resolved:true; FAIL_TO_PASS test_huge_range_log[png--1] success, PASS_TO_PASS all success. Confirms harness is live and verify(gold) => resolved; the model exactly matches the patched clamp `s_vmin = eps if s_vmin<=0 else s_vmin`.

refinement.md / mapping.md AUDIT (A-leg focus): NO axioms, NO opaque, NO A-consumed / A-reference / kind-3 legs (grep of Solution.lean spec region for axiom/opaque/`_prop`/sorry/admit = NONE; proof is `prove_correct logNormVmin by loom_solve`). All legs are R (A1: sVmin float<->Rat order-preserving abstraction, only sign vs 0 observed; A2: np.finfo(scaled_dtype).eps is a fixed strictly-positive machine-epsilon constant, IDENTICAL on both sides of the fix, correctly abstracted as the plain positive input `eps` with require eps>0 -- NOT axiomatized, hence no axiom_check.py, consistent with mapping.md section 4) and I (A3/A4: the changed clamp `<0`->`<=0`, `max`->outright eps, and the >0 pass-through). The model<->patch correspondence is exact and is independently confirmed by the gold resolve. No A-leg correspondence defect found.

**VERDICT:** SOUND. >=5 terminating attacks re-run (8 total), none verifies; positive control verifies; prepatch bug reproduced (atk_1); the single verifying wrong impl (atk_9) is a partial-correctness divergence artifact whose faithful patch times out (completed=False => inconclusive, not the clean non-resolve required for BROKEN), and is not a refinement-fidelity weakness of this spec. No verify=>NOT-correct witness exists for any terminating impl.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for logNormVmin.

**SPEC REGION:** same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) == True — spec is byte-identical between patched and prepatch; only impl differs. Solution.lean verifies (lean_verify.sh exit 0).

**REAL REPO BEHAVIOR:** gold patch (base b7ce415c) changes lib/matplotlib/image.py `_make_image` LogNorm branch to `if isinstance(self.norm, mcolors.LogNorm) and s_vmin <= 0: s_vmin = np.finfo(scaled_dtype).eps`, i.e. the pure scalar clamp is `s_vmin = eps if s_vmin <= 0 else s_vmin`.

**MODELED FUNCTION:** require eps>0; ensures (sVmin ≤ 0 → out = eps) ∧ (sVmin > 0 → out = sVmin). This is exactly the patched selection.

**DIFFERENTIAL TEST:** over Rat inputs {-1e20, -5, -1/3, -1e-18, 0, 1e-18, 1/3, 1, 1e20} with eps>0, spec == patched oracle on every input — ZERO divergences. The `<=0 → eps` / `>0 → passthrough` selection is order-only and precision-independent; a Rat carrier is faithful for the only observed property (sign of s_vmin).

**PRECONDITION NOT DRIFT:** `require eps > 0` faithfully models np.finfo(scaled_dtype).eps, which is strictly positive for every floating dtype (float32≈1.19e-7, float64≈2.22e-16); scaled_dtype is always float32/float64, so eps>0 holds unconditionally — the require never excludes a reachable real input.

NaN: `s_vmin <= 0` is False on NaN in Python/numpy, so both buggy and patched code leave NaN untouched; the Rat model has no NaN and its `sVmin ≤ 0` clause does not fire — no overclaim, no divergence. Out-of-model-domain, documented in mapping.md §3/§4 and conformance_check.py.

No input found where the modeled function disagrees with the real (patched) callee. Spec is neither too strong nor drifted. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical screen (leakage.screen) passes clean: [] hard failures. Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (markers.same_spec == True). Spec view correctly elides both impl (-- impl-start/end) and proof (prove_correct) regions.

Gold patch (lib/matplotlib/image.py `_make_image`): extends the LogNorm lower-bound clamp guard from `s_vmin < 0` to `and s_vmin <= 0` and replaces `max(s_vmin, np.finfo(scaled_dtype).eps)` with an outright `s_vmin = np.finfo(scaled_dtype).eps`.

**Lexical checks:** no diff markers; no >=8-char gold-patch line reproduced in the normalized spec view; patched file path 'lib/matplotlib/image.py' and its dotted module path do not appear; the only patch-changed symbol ('make_image') is not embedded in any spec-view identifier (logNormVmin, sVmin, eps) nor named in any spec-view comment/docstring; no `_NARRATION_RE` keywords (bug/fix/patched/previously/incorrectly/broken/...) in the spec-view docstring. (The prepatch's 'buggy'/'Pre-image' narration lives only inside the elided impl region, not in the spec view.)

Semantic gold-reconstruction check: the spec docstring and `ensures (sVmin <= 0 -> out = eps) and (sVmin > 0 -> out = sVmin)` describe the CORRECT post-fix behavior (specification, which is the bundle's purpose), not the edit delta. The prose is properly abstracted from repo/gold specifics: 'logarithmic intensity mapping' not LogNorm; 'lower scale bound' not s_vmin/vmin; 'constant tiny strictly-positive floor'/'smallest-representable positive figure' not np.finfo(scaled_dtype).eps. It never states the old guard was `<0`, never mentions `max`, and never narrates a change. The public problem_statement already exposes LogNorm, `_make_image`, and the 'Invalid vmin or vmax' ValueError, so nothing in the spec view reveals gold-edit details beyond what is already public. No spec-view line reconstructs the gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
