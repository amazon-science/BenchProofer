# P2 adversarial audit — sympy__sympy-17630

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying-but-wrong same-spec implementation exists, so there is no faithful refined patch to materialize / run through run_resolve. The postcondition is a per-branch exact equality out = (if op = additiveOp then additiveCombine matrixTerms else multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)); the discharging value in each of the two op cases is unique, and loom cannot equate distinct opaque applications (e.g. additiveCombine matrixTerms vs additiveCombine (withLeadingScalar leadingScalar matrixTerms)).
```

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
 /- The distinguished combining operator that denotes additive composition (an
@@ -82,12 +82,8 @@
      else multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms))
   do
     -- impl-start
-    -- Branch on the combining operator. Under the additive operator, compose
-    -- exactly the matrix-valued terms (no leading scalar-valued term).
-    -- Otherwise compose the matrix-valued terms with the leading scalar-valued
-    -- term placed in front of them.
     if op = additiveOp then
-      return additiveCombine matrixTerms
+      return additiveCombine (withLeadingScalar leadingScalar matrixTerms)
     else
       return multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)
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
 /- The distinguished combining operator that denotes additive composition (an
@@ -82,14 +82,10 @@
      else multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms))
   do
     -- impl-start
-    -- Branch on the combining operator. Under the additive operator, compose
-    -- exactly the matrix-valued terms (no leading scalar-valued term).
-    -- Otherwise compose the matrix-valued terms with the leading scalar-valued
-    -- term placed in front of them.
     if op = additiveOp then
+      return multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)
+    else
       return additiveCombine matrixTerms
-    else
-      return multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)
     -- impl-end
 
 prove_correct recombineMatrixNode by
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
 /- The distinguished combining operator that denotes additive composition (an
@@ -82,14 +82,7 @@
      else multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms))
   do
     -- impl-start
-    -- Branch on the combining operator. Under the additive operator, compose
-    -- exactly the matrix-valued terms (no leading scalar-valued term).
-    -- Otherwise compose the matrix-valued terms with the leading scalar-valued
-    -- term placed in front of them.
-    if op = additiveOp then
-      return additiveCombine matrixTerms
-    else
-      return multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)
+    return additiveCombine matrixTerms
     -- impl-end
 
 prove_correct recombineMatrixNode by
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
 /- The distinguished combining operator that denotes additive composition (an
@@ -82,12 +82,8 @@
      else multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms))
   do
     -- impl-start
-    -- Branch on the combining operator. Under the additive operator, compose
-    -- exactly the matrix-valued terms (no leading scalar-valued term).
-    -- Otherwise compose the matrix-valued terms with the leading scalar-valued
-    -- term placed in front of them.
     if op = additiveOp then
-      return additiveCombine matrixTerms
+      return multiplicativeCombine matrixTerms
     else
       return multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)
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
 /- The distinguished combining operator that denotes additive composition (an
@@ -82,14 +82,10 @@
      else multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms))
   do
     -- impl-start
-    -- Branch on the combining operator. Under the additive operator, compose
-    -- exactly the matrix-valued terms (no leading scalar-valued term).
-    -- Otherwise compose the matrix-valued terms with the leading scalar-valued
-    -- term placed in front of them.
     if op = additiveOp then
       return additiveCombine matrixTerms
     else
-      return multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)
+      return multiplicativeCombine matrixTerms
     -- impl-end
 
 prove_correct recombineMatrixNode by
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
 /- The distinguished combining operator that denotes additive composition (an
@@ -82,12 +82,8 @@
      else multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms))
   do
     -- impl-start
-    -- Branch on the combining operator. Under the additive operator, compose
-    -- exactly the matrix-valued terms (no leading scalar-valued term).
-    -- Otherwise compose the matrix-valued terms with the leading scalar-valued
-    -- term placed in front of them.
     if op = additiveOp then
-      return additiveCombine matrixTerms
+      return matrixTerms
     else
       return multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)
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
 /- The distinguished combining operator that denotes additive composition (an
@@ -82,14 +82,7 @@
      else multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms))
   do
     -- impl-start
-    -- Branch on the combining operator. Under the additive operator, compose
-    -- exactly the matrix-valued terms (no leading scalar-valued term).
-    -- Otherwise compose the matrix-valued terms with the leading scalar-valued
-    -- term placed in front of them.
-    if op = additiveOp then
-      return additiveCombine matrixTerms
-    else
-      return multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)
+    return multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)
     -- impl-end
 
 prove_correct recombineMatrixNode by
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
 /- The distinguished combining operator that denotes additive composition (an
@@ -82,12 +82,8 @@
      else multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms))
   do
     -- impl-start
-    -- Branch on the combining operator. Under the additive operator, compose
-    -- exactly the matrix-valued terms (no leading scalar-valued term).
-    -- Otherwise compose the matrix-valued terms with the leading scalar-valued
-    -- term placed in front of them.
     if op = additiveOp then
-      return additiveCombine matrixTerms
+      return additiveCombine (additiveCombine matrixTerms)
     else
       return multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)
     -- impl-end
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 /- The distinguished combining operator that denotes additive composition (an
@@ -82,12 +82,9 @@
      else multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms))
   do
     -- impl-start
-    -- Branch on the combining operator. Under the additive operator, compose
-    -- exactly the matrix-valued terms (no leading scalar-valued term).
-    -- Otherwise compose the matrix-valued terms with the leading scalar-valued
-    -- term placed in front of them.
     if op = additiveOp then
-      return additiveCombine matrixTerms
+      let x := withLeadingScalar leadingScalar matrixTerms
+      return additiveCombine x
     else
       return multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)
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
/- The distinguished combining operator that denotes additive composition (an
   UNCHANGED module-level constant / class object — it is consulted, not
   redefined). The operator in effect is compared against it to decide which
   recombination rule applies. Declared `opaque` (not `axiom`) so it is
   computable inside the executable `do` block. Provenance: mapping.md. As a
   free constant with no asserted `ensures`, there is nothing to validate
   against the real callee (no axiom_check.py — meta.json G-AX skip). -/
opaque additiveOp : Int

/- Compose a non-empty homogeneous collection of matrix-valued terms under the
   ADDITIVE operator, yielding a single matrix-valued term. An opaque
   deterministic UNCHANGED callee over expression handles; determinism is all
   the proof relies on (a given argument denotes one and the same result).
   `opaque` for do-block codegen. Provenance: mapping.md. -/
opaque additiveCombine : Int → Int

/- Compose a non-empty homogeneous collection of matrix-valued terms under the
   MULTIPLICATIVE operator, yielding a single matrix-valued term. A second,
   DISTINCT opaque deterministic UNCHANGED callee over handles (a different
   composition than `additiveCombine`). `opaque` for do-block codegen.
   Provenance: mapping.md. -/
opaque multiplicativeCombine : Int → Int

/- Build the argument bundle that places a leading scalar-valued term in front
   of a collection of matrix-valued terms (a deterministic UNCHANGED bundle
   constructor over handles). Provenance: mapping.md. -/
opaque withLeadingScalar : Int → Int → Int
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A construction-finalization step that recombines a single algebraic node
   after its child terms have been partitioned. This case handles a node whose
   children are a NON-EMPTY collection of matrix-valued terms with NO
   scalar-valued terms left to compose among them. The node was produced under
   one of two combining operators — additive or multiplicative — and the
   recombination rule differs by operator:

     * under the ADDITIVE operator, the result is the additive composition of
       exactly the matrix-valued terms;
     * under the MULTIPLICATIVE operator, the result is the multiplicative
       composition of those matrix-valued terms with a leading scalar-valued
       term placed in front of them.

   The behavior pinned here: the recombination is governed by WHICH combining
   operator is in effect, and for the additive operator the matrix-valued terms
   are composed ON THEIR OWN — no leading scalar-valued term is placed in front
   of them. The matrix-valued terms denote a matrix-valued result; placing a
   scalar-valued term in front of them under the additive operator would
   otherwise be free to collapse the result to a scalar-valued term, which is
   not matrix-valued.

   `op` (the combining operator in effect), `leadingScalar` (the scalar-valued
   term the multiplicative case places in front), and `matrixTerms` (the
   partitioned collection of matrix-valued terms) are read-only opaque
   expression handles (not `mut`); the routine computes a single handle and
   mutates nothing (directive 5). The composers, the leading-scalar
   constructor, and the additive-operator constant are opaque deterministic
   UNCHANGED callees/constants over handles. -/
method recombineMatrixNode (op : Int) (leadingScalar : Int) (matrixTerms : Int)
    return (out : Int)
  ensures out =
    (if op = additiveOp
     then additiveCombine matrixTerms
     else multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms))
  do
    -- impl-start
    if op ≠ additiveOp then
      return multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)
    else
      return additiveCombine matrixTerms
    -- impl-end

prove_correct recombineMatrixNode by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

 Command per attack: bash scripts/lean_verify.sh <path>. same_spec verified True for all files via swebench_unified.markers.same_spec (velvet backend). Attacks run concurrently in batches of 4.

### RESULTS (all same_spec=True; impl-region-only edits — axioms/pure/pre/post/ensures byte-identical):
- atk_1 (A-leg / prepatch bug: additive branch carries leading scalar -> additiveCombine (withLeadingScalar leadingScalar matrixTerms)): verify EXIT=1, rejected ensures_1 at 91:34. Reproduces Solution_prepatch.lean bug => prepatch_reproduced=true.
- atk_2 (branches swapped): EXIT=1, ensures_1 at 91:34.
- atk_3 (partial-domain echo: always additiveCombine matrixTerms, ignore op): EXIT=1, ensures_1 at 88:34 (else case mismatch).
- atk_4 (wrong composer: additive branch uses multiplicativeCombine matrixTerms): EXIT=1, ensures_1 at 91:34.
- atk_5 (boundary: else branch drops leading scalar -> multiplicativeCombine matrixTerms): EXIT=1, ensures_1 at 91:34.
- atk_6 (ungrounded echo: additive branch returns raw matrixTerms, no compose): EXIT=1, ensures_1 at 91:34.
- atk_7 (ungrounded else-echo: always multiplicativeCombine (withLeadingScalar ...)): EXIT=1, ensures_1 at 88:34.
- atk_8 (ungrounded wrong nesting: additive branch double-composes additiveCombine (additiveCombine matrixTerms)): EXIT=1, ensures_1 at 91:34.
- atk_9 (control-flow-effect: let-bound prepatch bug, let x := withLeadingScalar leadingScalar matrixTerms; return additiveCombine x): EXIT=1, ensures_1 at 92:34. Semantic failure, NOT a let-parse artifact (see controls below).

### POSITIVE CONTROLS (both same_spec=True, verify EXIT=0):
- atk_pc: structurally different, correct — negated guard `if op != additiveOp then multiplicativeCombine ... else additiveCombine matrixTerms`. EXIT=0. Proves spec is NON-VACUOUS.
- atk_pc_let (atk_pc_let.lean): CORRECT let-bound impl (let x := matrixTerms; return additiveCombine x in additive branch; let y := withLeadingScalar leadingScalar matrixTerms in else). EXIT=0. Confirms atk_9's failure is the leading-scalar prepend semantics, not the `let` construct.

Every attack failed to verify at ensures_1 (genuine postcondition rejection, verified by grep of lean output — no syntax/unknown/sorry errors). Because NO verifying wrong impl exists, there is no faithful refined patch to materialize, so no run_resolve execution is required or possible for a breakage; patches={} accordingly. This is the correct 'no counterexample' situation, not a missing-evidence INCONCLUSIVE.

REFINEMENT AUDIT (refinement.md rows 1-4): all R / A-consumed / I — no kind-3. A-legs additiveOp/additiveCombine/multiplicativeCombine/withLeadingScalar are FREE opaque decls with NO asserted ensures; proof consumes only opaque-determinism (weakest sufficient contract, SPEC_GUIDE dir.7) so no A-leg can over-claim a value/identity/raise vs the real UNCHANGED callees (Add/MatAdd, MatAdd/MatMul(...).doit, args-bundle constructor). Model<->patch correspondence holds: the single CHANGED operation (which args the additive composer receives) is modeled DIRECTLY in impl/spec (additiveCombine matrixTerms vs ...withLeadingScalar...), not hidden behind an opaque symbol — so no A-reference / deep model, G-AX skip legitimate. Postcondition is universally quantified over op, so the additive-branch obligation is non-vacuous (prepatch/atk_1 fail under op=additiveOp confirms). G-CONF conf_skip legitimate (symbolic op, no DB-free numeric R/I shadow).

Verdict: SOUND. >=5 distinct verifying-attack categories attempted (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, wrong-composer, prepatch bug); none verifies, so verify=>correct is not falsifiable here.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying-but-wrong same-spec implementation exists, so there is no faithful refined patch to materialize / run through run_resolve. The postcondition is a per-branch exact equality out = (if op = additiveOp then additiveCombine matrixTerms else multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)); the discharging value in each of the two op cases is unique, and loom cannot equate distinct opaque applications (e.g. additiveCombine matrixTerms vs additiveCombine (withLeadingScalar leadingScalar matrixTerms)).
```

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

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The distinguished combining operator that denotes additive composition (an
   UNCHANGED module-level constant / class object — it is consulted, not
   redefined). The operator in effect is compared against it to decide which
   recombination rule applies. Declared `opaque` (not `axiom`) so it is
   computable inside the executable `do` block. Provenance: mapping.md. As a
   free constant with no asserted `ensures`, there is nothing to validate
   against the real callee (no axiom_check.py — meta.json G-AX skip). -/
opaque additiveOp : Int

/- Compose a non-empty homogeneous collection of matrix-valued terms under the
   ADDITIVE operator, yielding a single matrix-valued term. An opaque
   deterministic UNCHANGED callee over expression handles; determinism is all
   the proof relies on (a given argument denotes one and the same result).
   `opaque` for do-block codegen. Provenance: mapping.md. -/
opaque additiveCombine : Int → Int

/- Compose a non-empty homogeneous collection of matrix-valued terms under the
   MULTIPLICATIVE operator, yielding a single matrix-valued term. A second,
   DISTINCT opaque deterministic UNCHANGED callee over handles (a different
   composition than `additiveCombine`). `opaque` for do-block codegen.
   Provenance: mapping.md. -/
opaque multiplicativeCombine : Int → Int

/- Build the argument bundle that places a leading scalar-valued term in front
   of a collection of matrix-valued terms (a deterministic UNCHANGED bundle
   constructor over handles). Provenance: mapping.md. -/
opaque withLeadingScalar : Int → Int → Int
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A construction-finalization step that recombines a single algebraic node
   after its child terms have been partitioned. This case handles a node whose
   children are a NON-EMPTY collection of matrix-valued terms with NO
   scalar-valued terms left to compose among them. The node was produced under
   one of two combining operators — additive or multiplicative — and the
   recombination rule differs by operator:

     * under the ADDITIVE operator, the result is the additive composition of
       exactly the matrix-valued terms;
     * under the MULTIPLICATIVE operator, the result is the multiplicative
       composition of those matrix-valued terms with a leading scalar-valued
       term placed in front of them.

   The behavior pinned here: the recombination is governed by WHICH combining
   operator is in effect, and for the additive operator the matrix-valued terms
   are composed ON THEIR OWN — no leading scalar-valued term is placed in front
   of them. The matrix-valued terms denote a matrix-valued result; placing a
   scalar-valued term in front of them under the additive operator would
   otherwise be free to collapse the result to a scalar-valued term, which is
   not matrix-valued.

   `op` (the combining operator in effect), `leadingScalar` (the scalar-valued
   term the multiplicative case places in front), and `matrixTerms` (the
   partitioned collection of matrix-valued terms) are read-only opaque
   expression handles (not `mut`); the routine computes a single handle and
   mutates nothing (directive 5). The composers, the leading-scalar
   constructor, and the additive-operator constant are opaque deterministic
   UNCHANGED callees/constants over handles. -/
method recombineMatrixNode (op : Int) (leadingScalar : Int) (matrixTerms : Int)
    return (out : Int)
  ensures out =
    (if op = additiveOp
     then additiveCombine matrixTerms
     else multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms))
  do
    -- impl-start
    if op ≠ additiveOp then
      return multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)
    else
      return additiveCombine matrixTerms
    -- impl-end

prove_correct recombineMatrixNode by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

 Command per attack: bash scripts/lean_verify.sh <path>. same_spec verified True for all files via swebench_unified.markers.same_spec (velvet backend). Attacks run concurrently in batches of 4.

### RESULTS (all same_spec=True; impl-region-only edits — axioms/pure/pre/post/ensures byte-identical):
- atk_1 (A-leg / prepatch bug: additive branch carries leading scalar -> additiveCombine (withLeadingScalar leadingScalar matrixTerms)): verify EXIT=1, rejected ensures_1 at 91:34. Reproduces Solution_prepatch.lean bug => prepatch_reproduced=true.
- atk_2 (branches swapped): EXIT=1, ensures_1 at 91:34.
- atk_3 (partial-domain echo: always additiveCombine matrixTerms, ignore op): EXIT=1, ensures_1 at 88:34 (else case mismatch).
- atk_4 (wrong composer: additive branch uses multiplicativeCombine matrixTerms): EXIT=1, ensures_1 at 91:34.
- atk_5 (boundary: else branch drops leading scalar -> multiplicativeCombine matrixTerms): EXIT=1, ensures_1 at 91:34.
- atk_6 (ungrounded echo: additive branch returns raw matrixTerms, no compose): EXIT=1, ensures_1 at 91:34.
- atk_7 (ungrounded else-echo: always multiplicativeCombine (withLeadingScalar ...)): EXIT=1, ensures_1 at 88:34.
- atk_8 (ungrounded wrong nesting: additive branch double-composes additiveCombine (additiveCombine matrixTerms)): EXIT=1, ensures_1 at 91:34.
- atk_9 (control-flow-effect: let-bound prepatch bug, let x := withLeadingScalar leadingScalar matrixTerms; return additiveCombine x): EXIT=1, ensures_1 at 92:34. Semantic failure, NOT a let-parse artifact (see controls below).

### POSITIVE CONTROLS (both same_spec=True, verify EXIT=0):
- atk_pc: structurally different, correct — negated guard `if op != additiveOp then multiplicativeCombine ... else additiveCombine matrixTerms`. EXIT=0. Proves spec is NON-VACUOUS.
- atk_pc_let (atk_pc_let.lean): CORRECT let-bound impl (let x := matrixTerms; return additiveCombine x in additive branch; let y := withLeadingScalar leadingScalar matrixTerms in else). EXIT=0. Confirms atk_9's failure is the leading-scalar prepend semantics, not the `let` construct.

Every attack failed to verify at ensures_1 (genuine postcondition rejection, verified by grep of lean output — no syntax/unknown/sorry errors). Because NO verifying wrong impl exists, there is no faithful refined patch to materialize, so no run_resolve execution is required or possible for a breakage; patches={} accordingly. This is the correct 'no counterexample' situation, not a missing-evidence INCONCLUSIVE.

REFINEMENT AUDIT (refinement.md rows 1-4): all R / A-consumed / I — no kind-3. A-legs additiveOp/additiveCombine/multiplicativeCombine/withLeadingScalar are FREE opaque decls with NO asserted ensures; proof consumes only opaque-determinism (weakest sufficient contract, SPEC_GUIDE dir.7) so no A-leg can over-claim a value/identity/raise vs the real UNCHANGED callees (Add/MatAdd, MatAdd/MatMul(...).doit, args-bundle constructor). Model<->patch correspondence holds: the single CHANGED operation (which args the additive composer receives) is modeled DIRECTLY in impl/spec (additiveCombine matrixTerms vs ...withLeadingScalar...), not hidden behind an opaque symbol — so no A-reference / deep model, G-AX skip legitimate. Postcondition is universally quantified over op, so the additive-branch obligation is non-vacuous (prepatch/atk_1 fail under op=additiveOp confirms). G-CONF conf_skip legitimate (symbolic op, no DB-free numeric R/I shadow).

Verdict: SOUND. >=5 distinct verifying-attack categories attempted (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, wrong-composer, prepatch bug); none verifies, so verify=>correct is not falsifiable here.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence between the modeled function and the real (gold-patched) callee on the modeled path.

### Checks performed
1. same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True — the spec region (axioms + pre/post + method signature/ensures) is byte-identical; no spec drift between the passing impl and the buggy prepatch. Spec view confirmed: axioms region (4 opaque decls) + empty pre/post + `ensures out = (if op = additiveOp then additiveCombine matrixTerms else multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms))`.
2. Solution.lean verifies (lean_verify.sh exit 0).
3. Solution_prepatch.lean FAILS with exactly the discriminating goal: `additiveCombine (withLeadingScalar leadingScalar matrixTerms) = additiveCombine matrixTerms` unsolvable under `if_pos: op = additiveOp` — so the postcondition genuinely rejects the pre-patch behavior (additive branch carrying the leading scalar).

### FIDELITY TO REAL REPO (matexpr.py:597-631 @ base_commit 58e78209, gold post-patch tail reached when matrices non-empty, nonmatrices empty):
- Additive case: gold `MatAdd(*matrices).doit(deep=False)` == spec `additiveCombine matrixTerms` (matrices alone, no scalar). ✓
- Multiplicative case: gold `MatMul(cls._from_args([]), *matrices).doit(deep=False)` == spec `multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)` with leadingScalar = cls._from_args([]). ✓
- Two-way branch: mat_class = {Mul:MatMul, Add:MatAdd}[cls] is a bijection, so `mat_class == MatAdd` ⇔ `cls == Add` ⇔ modeled `op = additiveOp`. Faithful control split. ✓

WHY NOT TOO STRONG: all four symbols (additiveOp, additiveCombine, multiplicativeCombine, withLeadingScalar) are opaque FREE symbols with no asserted ensures; the proof relies only on opaque-determinism (fixed arg → fixed result handle) — the weakest sufficient contract. The postcondition pins only WHICH composer is applied to WHICH argument bundle, which is precisely what the gold code does. It cannot over-claim a concrete value, identity, or raise behavior, so there is no input on the modeled path where the modeled function disagrees with the real callee. The un-modeled nonmatrices-non-empty paths are correctly excluded as control context (mapping.md §1), matching the F2P test inputs (nonmatrices empty). No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical leakage.screen() passes (no L1/L2/L3/L5 failures); meta G-LEAK=pass, no relaxation flag/RELAXED_LEAKAGE.md. same_spec(Solution, Solution_prepatch)=True byte-identical over the spec region. Spec view contains NO diff markers, NO patched file path (sympy/matrices/expressions/matexpr.py absent), NO patched repo symbols (MatAdd/_postprocessor/MatrixExpr/doit/_from_args/ZeroMatrix/Zero/BlockMatrix all absent) — everything abstracted to model handles (additiveOp, additiveCombine, multiplicativeCombine, withLeadingScalar, recombineMatrixNode). No narration words. The postcondition pins the correct additive-composes-matrices-alone behavior, but that is the legitimate specification the consumer solves against, expressed over opaque Int handles, not a reproduction of the gold edit or a repo-level localization. The wrong-branch/'pre-image' narration exists only in Solution_prepatch.lean's impl region, which is elided from the spec view. Problem statement already publicly exposes the observable Zero-vs-ZeroMatrix defect; the spec reveals nothing beyond it about the edit site.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
