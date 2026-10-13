# P2 adversarial audit — sympy__sympy-20428

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_9.lean`, `atk_10.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec verifying impl can deviate from gold on any REACHABLE input: the postcondition `out = nonzeroSpec e = !e.identicallyZero` is a full functional equality pinning the output on every input satisfying the precondition `literalZero -> identicallyZero`. The only remaining degree of freedom is the precondition-EXCLUDED input (literalZero=true & identicallyZero=false), i.e. `f.ex == 0 and not (f.ex.is_zero is True)`. That input is UNREACHABLE in the real repo (Integer(0).is_zero is always True), so any verifying impl's deviation there is dead code and its faithful patch still resolves. Independently probed: 0 precondition violations over 200,000+ real EX(expr) elements + boundary literal-zeros.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The two zero-tests an element can be subjected to —
@@ -67,9 +67,7 @@
   ensures out = nonzeroSpec e
   do
     -- impl-start
-    -- Report nonzero iff the element is not identically zero — the mathematical
-    -- zero test, not a comparison of the representation against the literal zero.
-    return !e.identicallyZero
+    return !e.literalZero
     -- impl-end
 
 prove_correct symbolicNonzero by
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
 -- (No axiomatized callees. The two zero-tests an element can be subjected to —
@@ -67,9 +67,7 @@
   ensures out = nonzeroSpec e
   do
     -- impl-start
-    -- Report nonzero iff the element is not identically zero — the mathematical
-    -- zero test, not a comparison of the representation against the literal zero.
-    return !e.identicallyZero
+    return e.identicallyZero
     -- impl-end
 
 prove_correct symbolicNonzero by
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
 -- (No axiomatized callees. The two zero-tests an element can be subjected to —
@@ -67,9 +67,7 @@
   ensures out = nonzeroSpec e
   do
     -- impl-start
-    -- Report nonzero iff the element is not identically zero — the mathematical
-    -- zero test, not a comparison of the representation against the literal zero.
-    return !e.identicallyZero
+    return true
     -- impl-end
 
 prove_correct symbolicNonzero by
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
 -- (No axiomatized callees. The two zero-tests an element can be subjected to —
@@ -67,9 +67,7 @@
   ensures out = nonzeroSpec e
   do
     -- impl-start
-    -- Report nonzero iff the element is not identically zero — the mathematical
-    -- zero test, not a comparison of the representation against the literal zero.
-    return !e.identicallyZero
+    return false
     -- impl-end
 
 prove_correct symbolicNonzero by
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
 -- (No axiomatized callees. The two zero-tests an element can be subjected to —
@@ -67,9 +67,7 @@
   ensures out = nonzeroSpec e
   do
     -- impl-start
-    -- Report nonzero iff the element is not identically zero — the mathematical
-    -- zero test, not a comparison of the representation against the literal zero.
-    return !e.identicallyZero
+    return !e.identicallyZero && !e.literalZero
     -- impl-end
 
 prove_correct symbolicNonzero by
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The two zero-tests an element can be subjected to —
@@ -67,9 +67,7 @@
   ensures out = nonzeroSpec e
   do
     -- impl-start
-    -- Report nonzero iff the element is not identically zero — the mathematical
-    -- zero test, not a comparison of the representation against the literal zero.
-    return !e.identicallyZero
+    return if e.literalZero && !e.identicallyZero then true else !e.identicallyZero
     -- impl-end
 
 prove_correct symbolicNonzero by
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The two zero-tests an element can be subjected to —
@@ -67,11 +67,12 @@
   ensures out = nonzeroSpec e
   do
     -- impl-start
-    -- Report nonzero iff the element is not identically zero — the mathematical
-    -- zero test, not a comparison of the representation against the literal zero.
-    return !e.identicallyZero
+    return if e.literalZero && !e.identicallyZero then false else !e.identicallyZero
     -- impl-end
 
 prove_correct symbolicNonzero by
   loom_solve
   simp_all [nonzeroSpec]
+  <;> intro h
+  <;> simp_all
+  <;> omega
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
 -- (No axiomatized callees. The two zero-tests an element can be subjected to —
@@ -67,9 +67,7 @@
   ensures out = nonzeroSpec e
   do
     -- impl-start
-    -- Report nonzero iff the element is not identically zero — the mathematical
-    -- zero test, not a comparison of the representation against the literal zero.
-    return !e.identicallyZero
+    return !e.identicallyZero || (e.literalZero && !e.identicallyZero)
     -- impl-end
 
 prove_correct symbolicNonzero by
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
 -- (No axiomatized callees. The two zero-tests an element can be subjected to —
@@ -67,9 +67,9 @@
   ensures out = nonzeroSpec e
   do
     -- impl-start
-    -- Report nonzero iff the element is not identically zero — the mathematical
-    -- zero test, not a comparison of the representation against the literal zero.
-    return !e.identicallyZero
+    let mut r := !e.identicallyZero
+    r := r && (!e.literalZero || e.identicallyZero)
+    return r
     -- impl-end
 
 prove_correct symbolicNonzero by
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
 -- (No axiomatized callees. The two zero-tests an element can be subjected to —
@@ -67,9 +67,7 @@
   ensures out = nonzeroSpec e
   do
     -- impl-start
-    -- Report nonzero iff the element is not identically zero — the mathematical
-    -- zero test, not a comparison of the representation against the literal zero.
-    return !e.identicallyZero
+    return nonzeroSpec e
     -- impl-end
 
 prove_correct symbolicNonzero by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two zero-tests an element can be subjected to —
--  the mathematical/identical zero test and the bare comparison against the
--  literal zero — are UNCHANGED machinery; they are abstracted to the two
--  boolean observations of `SymExpr` below and exercised structurally by
--  G-CONF (conformance_check.py), and their relationship is validated against
--  the real element by G-AX (axiom_check.py). Nothing is borrowed from an
--  oracle, so there is no consumed axiom.)
-- axioms-end

-- pure-start
/- A field element of the symbolic-expression domain, reduced to the two
   observations a zero-test can depend on:

     * `identicallyZero` — whether the element is mathematically (identically)
       zero: it denotes the value zero, however its representation is written;
     * `literalZero`     — whether the element's representation is the bare
       literal zero (a far coarser test: it can be `false` for an element that
       nonetheless denotes zero).

   A representation that is the literal zero always denotes zero, so
   `literalZero` implies `identicallyZero`; the converse fails — an element can
   denote zero without being written as the literal zero. -/
structure SymExpr where
  identicallyZero : Bool
  literalZero     : Bool
  deriving DecidableEq, Inhabited, Repr

/- The intended truth value of a symbolic field element: it counts as nonzero
   exactly when it is NOT identically zero. An element that denotes zero — even
   one whose representation is not the literal zero — counts as zero. -/
def nonzeroSpec (e : SymExpr) : Bool := !e.identicallyZero
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a symbolic field element is nonzero.

   Desired behavior: an element counts as nonzero exactly when it is not
   identically (mathematically) zero. It is NOT enough to compare the element's
   representation against the literal zero — a representation can differ from the
   literal zero and yet still denote the value zero, and such an element must be
   reported as zero, not nonzero. (Reporting a zero-denoting element as nonzero
   is what lets a stale zero survive where downstream machinery assumes a genuine
   zero has been discarded, the failure the public problem statement reports.)

   `e` is read-only (it is not `mut`): the decision reads the element and mutates
   nothing it is handed (directive 5). The element is modeled by its two relevant
   observations — whether it is identically zero and whether its representation is
   the bare literal zero (mapping.md §2); the former is the one that decides the
   outcome. A literal-zero representation always denotes zero, so the input
   satisfies `literalZero → identicallyZero`. -/
method symbolicNonzero (e : SymExpr) return (out : Bool)
  require e.literalZero → e.identicallyZero
  ensures out = nonzeroSpec e
  do
    -- impl-start
    return !(!(!e.identicallyZero))
    -- impl-end

prove_correct symbolicNonzero by
  loom_solve
  simp_all [nonzeroSpec]
```

Prepatch bug re-encoded as an attack: `True`.

TIGHT full-equality spec; NO A-legs (G-AX vacuous: axioms=[], deep_model_references=[]). Focused (per instructions) on A-legs / model<->patch correspondence.

 Verify cmd: `bash scripts/lean_verify.sh <atk>.lean`. same_spec: velvet backend, all attacks below True. Resolve cmd: `cd && PYTHONPATH=src python run_resolve.py <tag> <patch.diff>` (harness.run_resolve, official SWE-bench harness, F2P=test_issue_20427 + 154 P2P).

### VERIFY RESULTS (exit 0=verifies):
- atk_1 `return !e.literalZero` (prepatch bug) -> exit 1 (fails on residual `literalZero = identicallyZero`) => PREPATCH REPRODUCED.
- atk_2 `return e.identicallyZero` (sign flip) -> exit 1.
- atk_3 `return true` -> exit 1. atk_4 `return false` -> exit 1.
- atk_5 `return !identicallyZero && !literalZero` -> exit 1 (deviates on reachable identicallyZero=false,literalZero=false... actually residual mismatch) -> exit 1.
- atk_6 `if literalZero && !identicallyZero then true else !identicallyZero` -> exit 0 VERIFIES (same_spec=True).
- atk_7 `if literalZero && !identicallyZero then false else !identicallyZero` -> exit 0 VERIFIES after strengthening the (elided, same_spec-invariant) prove_correct block to close the contrapositive-of-precondition goal `identicallyZero=false -> literalZero=false` (same_spec=True).
- atk_8 `!identicallyZero || (literalZero && !identicallyZero)` -> exit 0 VERIFIES (same_spec=True).
- atk_9 control-flow-effect (mut local, `r := r && (!literalZero || identicallyZero)`) -> exit 1 (deviates on excluded input; frozen proof too weak).
- atk_10 ungrounded-oracle echo `return nonzeroSpec e` -> exit 1 (`No goals to be solved`: transparent def, proof over-closes).
- atk_pc `return !(!(!e.identicallyZero))` correct positive control -> exit 0 VERIFIES (non-vacuous).

### RESOLVE RESULTS (materialized faithful patches, official harness):
- GOLD `not f.ex.is_zero` -> resolved=True (positive control, harness+image OK).
- atk_6 faithful patch -> resolved=True.
- atk_7 faithful patch -> resolved=True.  (the decisive candidate: deviates on the excluded input, still resolves because that branch is dead code)
- atk_8 faithful patch -> resolved=True.
- NEGATIVE CONTROL: prepatch faithful patch `f.ex != 0` -> resolved=False (patch did not resolve) => harness genuinely discriminates; NOT a rubber-stamp.

EVERY verifying wrong-impl's materialized faithful patch RESOLVES. No verify=>correct violation.

A-LEG / correspondence audit (refinement.md): exactly two legs, both non-kind-3.
- A1 = R (element f <-> {identicallyZero, literalZero}). Faithful: real __bool__ reads f.ex only through these two zero-observations.
- A2 = I (`!identicallyZero` <-> `not f.ex.is_zero`). Verified the three-valued correspondence: `not (is_zero is True)` (spec model, per mapping.md identicallyZero:=is_zero is True) equals gold `not f.ex.is_zero` in boolean value for is_zero in {True,False,None} (probe_a2.py). None -> identicallyZero=false -> reported nonzero, matching gold. No consumed axiom, no A-reference; G-AX vacuous (skip) is correct.
- Modeling invariant / precondition `literalZero -> identicallyZero` validated independently: 0 violations over 200,000+ real EX(expr) elements (probe_precond.py), so the precondition excludes no reachable input.

VERDICT: SOUND. >=5 same-spec attacks run; the 3 that verify all have resolving faithful patches; prepatch reproduced; negative control (non-resolve) confirms discrimination; no kind-3 legs; A1/A2 correspondence holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_9.lean`, `atk_10.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec verifying impl can deviate from gold on any REACHABLE input: the postcondition `out = nonzeroSpec e = !e.identicallyZero` is a full functional equality pinning the output on every input satisfying the precondition `literalZero -> identicallyZero`. The only remaining degree of freedom is the precondition-EXCLUDED input (literalZero=true & identicallyZero=false), i.e. `f.ex == 0 and not (f.ex.is_zero is True)`. That input is UNREACHABLE in the real repo (Integer(0).is_zero is always True), so any verifying impl's deviation there is dead code and its faithful patch still resolves. Independently probed: 0 precondition violations over 200,000+ real EX(expr) elements + boundary literal-zeros.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two zero-tests an element can be subjected to —
--  the mathematical/identical zero test and the bare comparison against the
--  literal zero — are UNCHANGED machinery; they are abstracted to the two
--  boolean observations of `SymExpr` below and exercised structurally by
--  G-CONF (conformance_check.py), and their relationship is validated against
--  the real element by G-AX (axiom_check.py). Nothing is borrowed from an
--  oracle, so there is no consumed axiom.)
-- axioms-end

-- pure-start
/- A field element of the symbolic-expression domain, reduced to the two
   observations a zero-test can depend on:

     * `identicallyZero` — whether the element is mathematically (identically)
       zero: it denotes the value zero, however its representation is written;
     * `literalZero`     — whether the element's representation is the bare
       literal zero (a far coarser test: it can be `false` for an element that
       nonetheless denotes zero).

   A representation that is the literal zero always denotes zero, so
   `literalZero` implies `identicallyZero`; the converse fails — an element can
   denote zero without being written as the literal zero. -/
structure SymExpr where
  identicallyZero : Bool
  literalZero     : Bool
  deriving DecidableEq, Inhabited, Repr

/- The intended truth value of a symbolic field element: it counts as nonzero
   exactly when it is NOT identically zero. An element that denotes zero — even
   one whose representation is not the literal zero — counts as zero. -/
def nonzeroSpec (e : SymExpr) : Bool := !e.identicallyZero
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a symbolic field element is nonzero.

   Desired behavior: an element counts as nonzero exactly when it is not
   identically (mathematically) zero. It is NOT enough to compare the element's
   representation against the literal zero — a representation can differ from the
   literal zero and yet still denote the value zero, and such an element must be
   reported as zero, not nonzero. (Reporting a zero-denoting element as nonzero
   is what lets a stale zero survive where downstream machinery assumes a genuine
   zero has been discarded, the failure the public problem statement reports.)

   `e` is read-only (it is not `mut`): the decision reads the element and mutates
   nothing it is handed (directive 5). The element is modeled by its two relevant
   observations — whether it is identically zero and whether its representation is
   the bare literal zero (mapping.md §2); the former is the one that decides the
   outcome. A literal-zero representation always denotes zero, so the input
   satisfies `literalZero → identicallyZero`. -/
method symbolicNonzero (e : SymExpr) return (out : Bool)
  require e.literalZero → e.identicallyZero
  ensures out = nonzeroSpec e
  do
    -- impl-start
    return !(!(!e.identicallyZero))
    -- impl-end

prove_correct symbolicNonzero by
  loom_solve
  simp_all [nonzeroSpec]
```

Prepatch bug re-encoded as an attack: `True`.

TIGHT full-equality spec; NO A-legs (G-AX vacuous: axioms=[], deep_model_references=[]). Focused (per instructions) on A-legs / model<->patch correspondence.

 Verify cmd: `bash scripts/lean_verify.sh <atk>.lean`. same_spec: velvet backend, all attacks below True. Resolve cmd: `cd && PYTHONPATH=src python run_resolve.py <tag> <patch.diff>` (harness.run_resolve, official SWE-bench harness, F2P=test_issue_20427 + 154 P2P).

### VERIFY RESULTS (exit 0=verifies):
- atk_1 `return !e.literalZero` (prepatch bug) -> exit 1 (fails on residual `literalZero = identicallyZero`) => PREPATCH REPRODUCED.
- atk_2 `return e.identicallyZero` (sign flip) -> exit 1.
- atk_3 `return true` -> exit 1. atk_4 `return false` -> exit 1.
- atk_5 `return !identicallyZero && !literalZero` -> exit 1 (deviates on reachable identicallyZero=false,literalZero=false... actually residual mismatch) -> exit 1.
- atk_6 `if literalZero && !identicallyZero then true else !identicallyZero` -> exit 0 VERIFIES (same_spec=True).
- atk_7 `if literalZero && !identicallyZero then false else !identicallyZero` -> exit 0 VERIFIES after strengthening the (elided, same_spec-invariant) prove_correct block to close the contrapositive-of-precondition goal `identicallyZero=false -> literalZero=false` (same_spec=True).
- atk_8 `!identicallyZero || (literalZero && !identicallyZero)` -> exit 0 VERIFIES (same_spec=True).
- atk_9 control-flow-effect (mut local, `r := r && (!literalZero || identicallyZero)`) -> exit 1 (deviates on excluded input; frozen proof too weak).
- atk_10 ungrounded-oracle echo `return nonzeroSpec e` -> exit 1 (`No goals to be solved`: transparent def, proof over-closes).
- atk_pc `return !(!(!e.identicallyZero))` correct positive control -> exit 0 VERIFIES (non-vacuous).

### RESOLVE RESULTS (materialized faithful patches, official harness):
- GOLD `not f.ex.is_zero` -> resolved=True (positive control, harness+image OK).
- atk_6 faithful patch -> resolved=True.
- atk_7 faithful patch -> resolved=True.  (the decisive candidate: deviates on the excluded input, still resolves because that branch is dead code)
- atk_8 faithful patch -> resolved=True.
- NEGATIVE CONTROL: prepatch faithful patch `f.ex != 0` -> resolved=False (patch did not resolve) => harness genuinely discriminates; NOT a rubber-stamp.

EVERY verifying wrong-impl's materialized faithful patch RESOLVES. No verify=>correct violation.

A-LEG / correspondence audit (refinement.md): exactly two legs, both non-kind-3.
- A1 = R (element f <-> {identicallyZero, literalZero}). Faithful: real __bool__ reads f.ex only through these two zero-observations.
- A2 = I (`!identicallyZero` <-> `not f.ex.is_zero`). Verified the three-valued correspondence: `not (is_zero is True)` (spec model, per mapping.md identicallyZero:=is_zero is True) equals gold `not f.ex.is_zero` in boolean value for is_zero in {True,False,None} (probe_a2.py). None -> identicallyZero=false -> reported nonzero, matching gold. No consumed axiom, no A-reference; G-AX vacuous (skip) is correct.
- Modeling invariant / precondition `literalZero -> identicallyZero` validated independently: 0 violations over 200,000+ real EX(expr) elements (probe_precond.py), so the precondition excludes no reachable input.

VERDICT: SOUND. >=5 same-spec attacks run; the 3 that verify all have resolving faithful patches; prepatch reproduced; negative control (non-resolve) confirms discrimination; no kind-3 legs; A1/A2 correspondence holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for velvet sympy__sympy-20428. Modeled function: symbolicNonzero (Expression.__bool__ at expressiondomain.py:123); real post-patch callee: `not f.ex.is_zero`.

1) Spec region byte-identical: swebench_unified.markers.same_spec(Solution, Solution_prepatch, velvet) = True. The frozen spec (SymExpr, nonzeroSpec = !identicallyZero, method signature, require `literalZero -> identicallyZero`, ensures `out = nonzeroSpec e`) is unchanged between patched/prepatch.

2) Solution.lean verifies (lean_verify exit 0); Solution_prepatch.lean (return !literalZero) fails to verify with unsolved goal `literalZero = identicallyZero` — discrimination on the case identicallyZero=true, literalZero=false (the issue's math-zero-not-literal element). Correct discriminating behavior.

3) Faithfulness vs real callee: model maps identicallyZero := (f.ex.is_zero is True). Enumerating the three-valued is_zero: is_zero=True -> real not is_zero = False, model = False; is_zero=False -> real True, model True; is_zero=None -> real True (not None == True), model True (identicallyZero=false). Match on ALL three values. No input where the modeled function disagrees with the real patched __bool__.

4) The require precondition `literalZero -> identicallyZero` never excludes a genuine real input: any real EX element with f.ex==Integer(0) has is_zero is True, so the implication is always satisfied on real elements; and the ensures does not depend on literalZero at all, so the precondition cannot smuggle in a strengthening that hides a real disagreement.

Spec is neither too strong nor drifting: the 2-observation abstraction is exactly faithful because post-patch __bool__ reads the element only through is_zero. No diverging input exists. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-region integrity confirmed: same_spec(Solution.lean, Solution_prepatch.lean) == True under swebench_unified.markers with the velvet backend; the discriminating behavior lives entirely in the ELIDED impl region (Solution: `return !e.identicallyZero`; prepatch: `return !e.literalZero`), not smuggled into a differing spec. Mechanical G-LEAK screen passes with zero hard failures (verified by re-running leakage.screen against the frozen row): no gold-patch line reproduced (`return f.ex != 0` / `return not f.ex.is_zero` absent from the view), no diff markers, no patched file/module path (`sympy/polys/domains/expressiondomain.py` / `expressiondomain` absent), no spec-view identifier or comment naming a patched repo symbol, no bug/fix narration.

The spec view models the changed function abstractly as `symbolicNonzero` over a 2-field `SymExpr` (`identicallyZero`, `literalZero`) with `nonzeroSpec e = !e.identicallyZero` and `ensures out = nonzeroSpec e`. Stating the intended truth value is the framework's job (spec states desired behavior; consumer supplies impl+proof) and is NOT leakage of the gold edit. The discriminating concept it encodes — an element that DENOTES zero yet is not the LITERAL-zero representation must report as zero — is already public in the problem_statement, which shows `bad_poly.is_zero` == False while `bad_poly.as_expr().is_zero` == True and the unstripped `DMP([EX(0)], EX, None)`; the token `is_zero` itself appears verbatim in the problem statement. The spec view never names `__bool__`, `f.ex`, `is_zero`, or the repo path, so a solver still must localize `ExpressionDomain.Expression.__bool__` and author the edit `f.ex != 0` -> `not f.ex.is_zero` themselves. Nothing in the consumer spec view reconstructs the gold edit beyond what the public (non-hint) problem statement already discloses.

Scope note: mapping.md and refinement.md do name repo symbols (`__bool__`, `is_zero`, `EX`) and the gold hunk, but they are refinement-audit artifacts, not part of the consumer spec view that G-PANEL-3 governs, so they are out of scope for this leakage judgment.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
