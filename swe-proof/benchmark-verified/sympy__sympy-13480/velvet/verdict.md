# P2 adversarial audit — sympy__sympy-13480

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
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

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
 /- The function being simplified, as an opaque deterministic map over expression
@@ -70,10 +70,7 @@
   ensures out = (if primaryEval m = directedInfinity then primaryEval x else siblingEval x)
   do
     -- impl-start
-    -- Evaluate the same function on the periodic part, then branch on THAT
-    -- just-computed value: the function on the remainder when it is the
-    -- directed-infinity sentinel, the sibling on the remainder otherwise.
-    let computed := primaryEval m
+    let computed := cofamilyEval m
     if computed = directedInfinity then
       return primaryEval x
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
 /- The function being simplified, as an opaque deterministic map over expression
@@ -70,14 +70,11 @@
   ensures out = (if primaryEval m = directedInfinity then primaryEval x else siblingEval x)
   do
     -- impl-start
-    -- Evaluate the same function on the periodic part, then branch on THAT
-    -- just-computed value: the function on the remainder when it is the
-    -- directed-infinity sentinel, the sibling on the remainder otherwise.
     let computed := primaryEval m
     if computed = directedInfinity then
+      return siblingEval x
+    else
       return primaryEval x
-    else
-      return siblingEval x
     -- impl-end
 
 prove_correct cothEvalPeriodic by
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
 /- The function being simplified, as an opaque deterministic map over expression
@@ -70,14 +70,7 @@
   ensures out = (if primaryEval m = directedInfinity then primaryEval x else siblingEval x)
   do
     -- impl-start
-    -- Evaluate the same function on the periodic part, then branch on THAT
-    -- just-computed value: the function on the remainder when it is the
-    -- directed-infinity sentinel, the sibling on the remainder otherwise.
-    let computed := primaryEval m
-    if computed = directedInfinity then
-      return primaryEval x
-    else
-      return siblingEval x
+    return primaryEval x
     -- impl-end
 
 prove_correct cothEvalPeriodic by
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
 /- The function being simplified, as an opaque deterministic map over expression
@@ -70,10 +70,7 @@
   ensures out = (if primaryEval m = directedInfinity then primaryEval x else siblingEval x)
   do
     -- impl-start
-    -- Evaluate the same function on the periodic part, then branch on THAT
-    -- just-computed value: the function on the remainder when it is the
-    -- directed-infinity sentinel, the sibling on the remainder otherwise.
-    let computed := primaryEval m
+    let computed := siblingEval m
     if computed = directedInfinity then
       return primaryEval x
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
 /- The function being simplified, as an opaque deterministic map over expression
@@ -70,12 +70,9 @@
   ensures out = (if primaryEval m = directedInfinity then primaryEval x else siblingEval x)
   do
     -- impl-start
-    -- Evaluate the same function on the periodic part, then branch on THAT
-    -- just-computed value: the function on the remainder when it is the
-    -- directed-infinity sentinel, the sibling on the remainder otherwise.
     let computed := primaryEval m
     if computed = directedInfinity then
-      return primaryEval x
+      return siblingEval x
     else
       return siblingEval x
     -- impl-end
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
 /- The function being simplified, as an opaque deterministic map over expression
@@ -70,10 +70,7 @@
   ensures out = (if primaryEval m = directedInfinity then primaryEval x else siblingEval x)
   do
     -- impl-start
-    -- Evaluate the same function on the periodic part, then branch on THAT
-    -- just-computed value: the function on the remainder when it is the
-    -- directed-infinity sentinel, the sibling on the remainder otherwise.
-    let computed := primaryEval m
+    let computed := primaryEval x
     if computed = directedInfinity then
       return primaryEval x
     else
```

Attack 7 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- The function being simplified, as an opaque deterministic map over expression
@@ -70,14 +70,7 @@
   ensures out = (if primaryEval m = directedInfinity then primaryEval x else siblingEval x)
   do
     -- impl-start
-    -- Evaluate the same function on the periodic part, then branch on THAT
-    -- just-computed value: the function on the remainder when it is the
-    -- directed-infinity sentinel, the sibling on the remainder otherwise.
-    let computed := primaryEval m
-    if computed = directedInfinity then
-      return primaryEval x
-    else
-      return siblingEval x
+    return (if primaryEval m = directedInfinity then primaryEval x else siblingEval x)
     -- impl-end
 
 prove_correct cothEvalPeriodic by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The function being simplified, as an opaque deterministic map over expression
   handles (an UNCHANGED elementary callee — it is consulted, not redefined).
   Determinism is all the proof relies on: the value computed from the periodic
   part is the same value later inspected. Declared `opaque` (not `axiom`) so it
   is computable inside the executable `do` block. Provenance: mapping.md.
   Because it is a free function with no asserted `ensures`, there is nothing to
   validate against the real callee (no axiom_check.py — meta.json G-AX skip). -/
opaque primaryEval : Int → Int

/- The reciprocal-family sibling function, likewise an opaque deterministic
   UNCHANGED callee over expression handles. `opaque` for do-block codegen.
   Provenance: mapping.md. -/
opaque siblingEval : Int → Int

/- A second, DISTINCT opaque elementary map over handles — a different function
   in the same trigonometric family. Used only to exhibit that the branch must
   not be governed by an unrelated quantity (the pre-image inspects this one).
   Provenance: mapping.md. -/
opaque cofamilyEval : Int → Int

/- The distinguished "directed-infinity" sentinel expression handle (an
   UNCHANGED module constant / singleton). Provenance: mapping.md. -/
opaque directedInfinity : Int
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- An automatic simplifier for a hyperbolic-cotangent-like function handles the
   case where its argument decomposes into a remainder part `x` and a multiple
   of a distinguished imaginary period `m`. When that periodic part is present,
   the simplifier evaluates the SAME function on the periodic part and inspects
   the resulting expression:

     * if evaluating the function on the periodic part yields the
       directed-infinity sentinel, the simplified result is the function applied
       to the remainder part;
     * otherwise (the evaluation yields the finite/zero alternative), the
       simplified result is the reciprocal-family sibling function applied to
       the remainder part.

   The behavior pinned here: the branch that chooses between these two results
   is governed by the value obtained by evaluating the function on the PERIODIC
   PART — the quantity just computed from `m` — and by no other quantity. The
   result is the remainder-part evaluation of the same function exactly when
   that computed value is the directed-infinity sentinel, and the sibling on the
   remainder part otherwise.

   `x` and `m` are read-only opaque expression handles (not `mut`); the routine
   computes a single handle and mutates nothing (directive 5). The elementary
   functions consulted are opaque deterministic callees over handles; the
   sentinel is an opaque distinguished handle. -/
method cothEvalPeriodic (x : Int) (m : Int) return (out : Int)
  ensures out = (if primaryEval m = directedInfinity then primaryEval x else siblingEval x)
  do
    -- impl-start
    -- Evaluate the same function on the periodic part, then branch on THAT
    -- just-computed value: the function on the remainder when it is the
    -- directed-infinity sentinel, the sibling on the remainder otherwise.
    let computed := primaryEval m
    if computed = directedInfinity then
      return primaryEval x
    else
      return siblingEval x
    -- impl-end

prove_correct cothEvalPeriodic by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec postcondition fully pins output: out = (if primaryEval m = directedInfinity then primaryEval x else siblingEval x). All 8 attack files confirmed same_spec=True (impl-region-only edits).

### VERIFY RESULTS (bash scripts/lean_verify.sh <file>):
- atk_1 (prepatch bug: discriminator = cofamilyEval m, model of unbound 'cotm'): exit 1 REJECTED. Reproduces the prepatch NameError defect faithfully; matches bundle Solution_prepatch.lean which also fails (prepatch.lean verify exit 1).
- atk_2 (branches swapped: sentinel->sibling, else->primary): exit 1 REJECTED.
- atk_3 (partial-domain: unconditional 'return primaryEval x', drops else branch): exit 1 REJECTED.
- atk_4 (boundary: discriminator = siblingEval m instead of primaryEval m): exit 1 REJECTED.
- atk_5 (control-flow-effect: both branches return siblingEval x): exit 1 REJECTED.
- atk_8 (wrong argument: discriminator = primaryEval x instead of primaryEval m): exit 1 REJECTED.
- atk_6 (ungrounded-oracle ECHO: 'return (if primaryEval m = directedInfinity then primaryEval x else siblingEval x)'): exit 0 VERIFIES. Materialized faithful patch = gold one-token fix (cotm->cothm at hyperbolic.py:590). run_resolve('sympy__sympy-13480', patch) => completed=True, resolved=True, note='resolved'. Correct echo of the gold, NOT a spec weakness. Does not break verify=>correct.

OUT-OF-SCOPE ATTACK (documented, NOT submitted): atk_7.lean ('while true do pure (); return primaryEval x') verifies (exit 0) VACUOUSLY under set_option loom.semantics.termination "partial" — a diverging program partial-correctness-satisfies any postcondition. This is a UNIVERSAL Velvet partial-correctness artifact that would break EVERY partial-semantics bundle if counted; it is not a refinement-fidelity defect. It has no faithful refined patch (an infinite loop is not a skeleton-faithful refinement of the gold branch body, and non-termination is not one of the protocol's attack categories). Excluded from the breaking-attack set so as not to fabricate a false BROKEN/INCONCLUSIVE. Verified separately 

POSITIVE CONTROL: pos_control.lean (copy of frozen Solution.lean) verifies exit 0.

REFINEMENT.MD AUDIT: 5 legs. Legs 1-4 tagged A-consumed+R (+I on leg 2 control structure); leg 5 tagged I. No kind-3 (changed-but-inexpressible) leg. No A-reference/deep-model leg (mapping.md + refinement.md both state the changed op — the branch DATA SOURCE — is modeled directly with identical control/data flow; the opaque symbols model UNCHANGED callees coth/tanh/cot/S.ComplexInfinity). A-legs' correspondence holds: primaryEval<->coth (hyperbolic.py:537), siblingEval<->tanh (hyperbolic.py:391), cofamilyEval<->cot (trigonometric.py, pre-image only), directedInfinity<->S.ComplexInfinity singleton. Contract relied on is determinism only (opaque free functions, no asserted ensures) — the weakest sufficient contract, cannot over-claim (SPEC_GUIDE directive 7); G-AX correctly skipped. Discriminating I ('branch on primaryEval m, not cofamilyEval m') is correctly modeled and the prepatch (distinct opaque function cofamilyEval) is unprovable equal to the spec => fails as required.

CONCLUSION: >=5 distinct wrong impls run (6 rejected: partial-domain, boundary, control-flow-effect, swap, wrong-arg, prepatch); the one non-echo threat class is covered; the only genuinely-verifying attack with a faithful patch (echo) resolves under the official harness. No verifying wrong impl's faithful patch fails to resolve. verify=>correct holds for this spec. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The function being simplified, as an opaque deterministic map over expression
   handles (an UNCHANGED elementary callee — it is consulted, not redefined).
   Determinism is all the proof relies on: the value computed from the periodic
   part is the same value later inspected. Declared `opaque` (not `axiom`) so it
   is computable inside the executable `do` block. Provenance: mapping.md.
   Because it is a free function with no asserted `ensures`, there is nothing to
   validate against the real callee (no axiom_check.py — meta.json G-AX skip). -/
opaque primaryEval : Int → Int

/- The reciprocal-family sibling function, likewise an opaque deterministic
   UNCHANGED callee over expression handles. `opaque` for do-block codegen.
   Provenance: mapping.md. -/
opaque siblingEval : Int → Int

/- A second, DISTINCT opaque elementary map over handles — a different function
   in the same trigonometric family. Used only to exhibit that the branch must
   not be governed by an unrelated quantity (the pre-image inspects this one).
   Provenance: mapping.md. -/
opaque cofamilyEval : Int → Int

/- The distinguished "directed-infinity" sentinel expression handle (an
   UNCHANGED module constant / singleton). Provenance: mapping.md. -/
opaque directedInfinity : Int
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- An automatic simplifier for a hyperbolic-cotangent-like function handles the
   case where its argument decomposes into a remainder part `x` and a multiple
   of a distinguished imaginary period `m`. When that periodic part is present,
   the simplifier evaluates the SAME function on the periodic part and inspects
   the resulting expression:

     * if evaluating the function on the periodic part yields the
       directed-infinity sentinel, the simplified result is the function applied
       to the remainder part;
     * otherwise (the evaluation yields the finite/zero alternative), the
       simplified result is the reciprocal-family sibling function applied to
       the remainder part.

   The behavior pinned here: the branch that chooses between these two results
   is governed by the value obtained by evaluating the function on the PERIODIC
   PART — the quantity just computed from `m` — and by no other quantity. The
   result is the remainder-part evaluation of the same function exactly when
   that computed value is the directed-infinity sentinel, and the sibling on the
   remainder part otherwise.

   `x` and `m` are read-only opaque expression handles (not `mut`); the routine
   computes a single handle and mutates nothing (directive 5). The elementary
   functions consulted are opaque deterministic callees over handles; the
   sentinel is an opaque distinguished handle. -/
method cothEvalPeriodic (x : Int) (m : Int) return (out : Int)
  ensures out = (if primaryEval m = directedInfinity then primaryEval x else siblingEval x)
  do
    -- impl-start
    -- Evaluate the same function on the periodic part, then branch on THAT
    -- just-computed value: the function on the remainder when it is the
    -- directed-infinity sentinel, the sibling on the remainder otherwise.
    let computed := primaryEval m
    if computed = directedInfinity then
      return primaryEval x
    else
      return siblingEval x
    -- impl-end

prove_correct cothEvalPeriodic by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec postcondition fully pins output: out = (if primaryEval m = directedInfinity then primaryEval x else siblingEval x). All 8 attack files confirmed same_spec=True (impl-region-only edits).

### VERIFY RESULTS (bash scripts/lean_verify.sh <file>):
- atk_1 (prepatch bug: discriminator = cofamilyEval m, model of unbound 'cotm'): exit 1 REJECTED. Reproduces the prepatch NameError defect faithfully; matches bundle Solution_prepatch.lean which also fails (prepatch.lean verify exit 1).
- atk_2 (branches swapped: sentinel->sibling, else->primary): exit 1 REJECTED.
- atk_3 (partial-domain: unconditional 'return primaryEval x', drops else branch): exit 1 REJECTED.
- atk_4 (boundary: discriminator = siblingEval m instead of primaryEval m): exit 1 REJECTED.
- atk_5 (control-flow-effect: both branches return siblingEval x): exit 1 REJECTED.
- atk_8 (wrong argument: discriminator = primaryEval x instead of primaryEval m): exit 1 REJECTED.
- atk_6 (ungrounded-oracle ECHO: 'return (if primaryEval m = directedInfinity then primaryEval x else siblingEval x)'): exit 0 VERIFIES. Materialized faithful patch = gold one-token fix (cotm->cothm at hyperbolic.py:590). run_resolve('sympy__sympy-13480', patch) => completed=True, resolved=True, note='resolved'. Correct echo of the gold, NOT a spec weakness. Does not break verify=>correct.

OUT-OF-SCOPE ATTACK (documented, NOT submitted): atk_7.lean ('while true do pure (); return primaryEval x') verifies (exit 0) VACUOUSLY under set_option loom.semantics.termination "partial" — a diverging program partial-correctness-satisfies any postcondition. This is a UNIVERSAL Velvet partial-correctness artifact that would break EVERY partial-semantics bundle if counted; it is not a refinement-fidelity defect. It has no faithful refined patch (an infinite loop is not a skeleton-faithful refinement of the gold branch body, and non-termination is not one of the protocol's attack categories). Excluded from the breaking-attack set so as not to fabricate a false BROKEN/INCONCLUSIVE. Verified separately 

POSITIVE CONTROL: pos_control.lean (copy of frozen Solution.lean) verifies exit 0.

REFINEMENT.MD AUDIT: 5 legs. Legs 1-4 tagged A-consumed+R (+I on leg 2 control structure); leg 5 tagged I. No kind-3 (changed-but-inexpressible) leg. No A-reference/deep-model leg (mapping.md + refinement.md both state the changed op — the branch DATA SOURCE — is modeled directly with identical control/data flow; the opaque symbols model UNCHANGED callees coth/tanh/cot/S.ComplexInfinity). A-legs' correspondence holds: primaryEval<->coth (hyperbolic.py:537), siblingEval<->tanh (hyperbolic.py:391), cofamilyEval<->cot (trigonometric.py, pre-image only), directedInfinity<->S.ComplexInfinity singleton. Contract relied on is determinism only (opaque free functions, no asserted ensures) — the weakest sufficient contract, cannot over-claim (SPEC_GUIDE directive 7); G-AX correctly skipped. Discriminating I ('branch on primaryEval m, not cofamilyEval m') is correctly modeled and the prepatch (distinct opaque function cofamilyEval) is unprovable equal to the spec => fails as required.

CONCLUSION: >=5 distinct wrong impls run (6 rejected: partial-domain, boundary, control-flow-effect, swap, wrong-arg, prepatch); the one non-echo threat class is covered; the only genuinely-verifying attack with a faithful patch (echo) resolves under the official harness. No verifying wrong impl's faithful patch fails to resolve. verify=>correct holds for this spec. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (same_spec=True, velvet backend). Solution.lean verifies (lean_verify exit 0); prepatch fails (exit 1, unsolved goals — cofamilyEval m discriminator). Spec `out = if primaryEval m = directedInfinity then primaryEval x else siblingEval x` faithfully models the post-patch coth.eval periodic branch at base_commit hyperbolic.py:761-767 (verified worktree): branch on coth(m) is S.ComplexInfinity → return coth(x) else tanh(x). The gold patch is the one-token fix cotm→cothm at line 590; the modeled callees (coth=primaryEval, tanh=siblingEval, cot=cofamilyEval, S.ComplexInfinity=directedInfinity) are UNCHANGED by the patch and modeled as opaque free functions/constants with NO asserted ensures — only determinism relied upon. Because the opaque symbols make no value/sentinel/raise claims, the modeled function cannot disagree with the real callee on any input; the spec pins only the branch STRUCTURE (governed solely by coth(m) vs the sentinel), which matches real repo behavior exactly. Not too strong (admits gold behavior), not too weak (forbids the pre-patch wrong-data-source defect, as the prepatch failure confirms). No diverging input found. G-AX/G-CONF skips are justified (all-opaque/A-tagged impl region; symbolic Expr oracle with no DB-free numeric R/I shadow).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified spec region byte-identical: swebench_unified.markers.same_spec(gold, prepatch, get_backend('velvet').language) == True. The only diff between Solution.lean and Solution_prepatch.lean is the elided impl region (gold: `let computed := primaryEval m; if computed = directedInfinity`; prepatch: wrong-data-source `if cofamilyEval m = directedInfinity`). Spec view (rendered via spec_view) elides both impl (`-- implementation elided`) and proof.

Baseline for leakage = public problem_statement ONLY (hints_text excluded). problem_statement already discloses FAR more than the spec view: it literally shows the buggy source line `if cotm is S.ComplexInfinity:` at hyperbolic.py:590, the `NameError: name 'cotm' is not defined`, S.ComplexInfinity, and the reproducer `coth(log(tan(x)))`. (hints_text goes further, naming the cotm->cothm one-token fix, but is not part of the allowed baseline.)

Scanned the spec view for every repo-specific token: `cotm`, `cothm`, `ComplexInfinity`, `tanh`, `NameError`, `590`, `hyperbolic.py`, `sympy`, `log(tan`, `subs` -> NONE present. The only substring hits are benign: `cot`/`coth` occur solely inside the generic paraphrase 'hyperbolic-cotangent-like function' (line 45) and the abstract model method name `cothEvalPeriodic` (lines 69,76); `.py` at line 16 is the harness reference 'axiom_check.py', not a repo file. All repo symbols are replaced by opaque handles (primaryEval/siblingEval/cofamilyEval/directedInfinity); no filename, line number, or typo token appears.

The postcondition `ensures out = (if primaryEval m = directedInfinity then primaryEval x else siblingEval x)` pins the intended post-fix behavior (branch governed by the value computed from m) but (a) that is the mandatory functional specification any spec must carry, and (b) it is expressed purely in opaque terms that do not identify which source token changed. The gold edit cotm->cothm is recoverable only from mapping.md / refinement.md (reviewer artifacts, NOT in the spec view). The spec view is strictly MORE abstract than the public problem_statement. No spec-view line reconstructs the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
