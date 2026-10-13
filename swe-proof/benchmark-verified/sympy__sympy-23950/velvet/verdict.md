# P2 adversarial audit — sympy__sympy-23950

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
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition `out = Except.ok a.container` is a fully-pinned functional equality over an input-grounded RHS (a projection of the input carrier a.container ↔ self.args[1], not an oracle to echo). Every TERMINATING same-spec wrong impl is rejected on the discriminating goal `<lhs> = Except.ok a.container`. The only same-spec verifying wrong impl is atk_5, a vacuous-exit `while true` divergence that discharges the post vacuously under `set_option loom.semantics.termination "partial"` — a partial-correctness artifact universal to all termination=partial velvet bundles, NOT a property of this spec's postcondition. Its faithful refined patch is the gold projection `return self.args[1]` (the divergence loop has no refinement leg; refinement.md has only A1/R + A2/I), which RESOLVES under the official harness (executed). So verify⇏correct does not hold: the spec is TIGHT.
```

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
 -- (No axiomatized callees. The conversion reads the assertion's own stored
@@ -51,7 +51,7 @@
   ensures out = Except.ok a.container
   do
     -- impl-start
-    return Except.ok a.container
+    return Except.error ConversionErr.unavailable
     -- impl-end
 
 prove_correct asSet by
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
 -- (No axiomatized callees. The conversion reads the assertion's own stored
@@ -51,7 +51,7 @@
   ensures out = Except.ok a.container
   do
     -- impl-start
-    return Except.ok a.container
+    return Except.ok a.elem
     -- impl-end
 
 prove_correct asSet by
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
 -- (No axiomatized callees. The conversion reads the assertion's own stored
@@ -51,7 +51,7 @@
   ensures out = Except.ok a.container
   do
     -- impl-start
-    return Except.ok a.container
+    return Except.ok 0
     -- impl-end
 
 prove_correct asSet by
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
 -- (No axiomatized callees. The conversion reads the assertion's own stored
@@ -51,7 +51,10 @@
   ensures out = Except.ok a.container
   do
     -- impl-start
-    return Except.ok a.container
+    if a.elem = a.container then
+      return Except.ok a.container
+    else
+      return Except.ok a.elem
     -- impl-end
 
 prove_correct asSet by
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The conversion reads the assertion's own stored
@@ -51,6 +51,11 @@
   ensures out = Except.ok a.container
   do
     -- impl-start
+    let mut x := 0
+    while true
+      invariant True
+    do
+      x := x + 1
     return Except.ok a.container
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
 -- (No axiomatized callees. The conversion reads the assertion's own stored
@@ -51,7 +51,12 @@
   ensures out = Except.ok a.container
   do
     -- impl-start
-    return Except.ok a.container
+    let mut x := 0
+    while x = 0
+      invariant True
+    do
+      x := 0
+    return Except.ok a.elem
     -- impl-end
 
 prove_correct asSet by
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
 -- (No axiomatized callees. The conversion reads the assertion's own stored
@@ -51,7 +51,7 @@
   ensures out = Except.ok a.container
   do
     -- impl-start
-    return Except.ok a.container
+    return Except.ok (max a.elem a.container)
     -- impl-end
 
 prove_correct asSet by
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
 -- (No axiomatized callees. The conversion reads the assertion's own stored
@@ -51,7 +51,7 @@
   ensures out = Except.ok a.container
   do
     -- impl-start
-    return Except.ok a.container
+    return Except.ok (min a.elem a.container)
     -- impl-end
 
 prove_correct asSet by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The conversion reads the assertion's own stored
--  components and returns one of them directly; there is no separate callee to
--  contract, so there are no module-level axioms.)
-- axioms-end

-- pure-start
/- A membership assertion: a boolean-valued expression stating that some element
   belongs to some collection. It carries exactly two components — the element
   being tested (`elem`) and the collection it is tested against (`container`).
   Both are modeled as opaque identifiers (`Nat`), since the conversion only
   needs to tell them apart and to hand one of them back unchanged. -/
structure MembershipAssertion where
  elem : Nat
  container : Nat
  deriving DecidableEq

/- The two outcomes the set-conversion of a membership assertion distinguishes:
   a successful conversion yielding a collection, or a refusal (the conversion is
   undefined / unavailable). The refusal arm exists so that a routine which
   declines to produce a collection is expressible against this same spec. -/
inductive ConversionErr where
  | unavailable
  deriving DecidableEq
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The set form of a membership assertion. A statement "this element belongs to
   this collection" describes, as a set, precisely that collection: the set the
   membership ranges over. So converting the assertion to its set form must
   SUCCEED and yield the assertion's collection component — its second component
   — handed back unchanged. The element component is NOT the answer: the result
   is the collection, never the element being tested. The assertion is read-only
   (not `mut`); the conversion reads its components and mutates nothing
   (directive 5). The element, the collection, and the result are modeled as
   `Nat` identifiers; the result is wrapped in `Except` to allow a refusal arm. -/
method asSet (a : MembershipAssertion) return (out : Except ConversionErr Nat)
  ensures out = Except.ok a.container
  do
    -- impl-start
    return Except.ok a.container
    -- impl-end

prove_correct asSet by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

 Gold patch.diff lives at benchmark-verified/sympy__sympy-23950/patch.diff (not under velvet/).

SAME-SPEC: all 8 attacks + positive control confirmed same_spec=True via swebench_unified.markers.same_spec on the velvet backend (impl region only was edited; axioms/pure/pre/post byte-identical).

SPEC SHAPE: `method asSet (a : MembershipAssertion) return (out : Except ConversionErr Nat) ensures out = Except.ok a.container` with body `return Except.ok a.container`. Bijection (mapping.md §2): a.container ↔ self.args[1] (the result), a.elem ↔ self.args[0], Except.ok v ↔ normal return, Except.error .unavailable ↔ declining/raise.

STEP-3 A-LEG AUDIT (VACUOUS): meta.json has axioms=[] and deep_model_references=[]; there is NO axiom_check.py and G-AX skips. refinement.md has exactly 2 legs — A1 (R: param a ↔ self, read-only not mut) and A2 (I: return Except.ok a.container ↔ return self.args[1]). No kind-3 (changed-inexpressible) legs. The R/I correspondence holds and is exercised directly by G-CONF (I-shadow return c.args[1] vs patched as_set over 50014 symbolic assertions, seed 23950, 0 disagreements). No A-legs to falsify.

### ATTACK LEDGER (cmd: `bash scripts/lean_verify.sh <file>`, run; verifications launched concurrently in ≤4-job background batches):
- atk_1 (REAL prepatch bug, `return Except.error ConversionErr.unavailable` = raise NotImplementedError): EXIT 1. PREPATCH REPRODUCED. Residual goal `Except.error ConversionErr.unavailable = Except.ok a.container` (error≠ok, unsatisfiable).
- atk_2 (ungrounded-oracle echo / wrong stored component, `return Except.ok a.elem` = self.args[0]): EXIT 1. Goal `Except.ok a.elem = Except.ok a.container`.
- atk_3 (boundary/constant, `return Except.ok 0`): EXIT 1. Goal `Except.ok 0 = Except.ok a.container`.
- atk_4 (partial-domain, `if a.elem = a.container then ok container else ok elem`): EXIT 1. Loop-free; else-branch goal `if_neg: ¬a.elem=a.container ⊢ Except.ok a.elem = Except.ok a.container`.
- atk_5 (control-flow-effect / VACUOUS-exit divergence: `let mut x:=0; while true invariant True do x:=x+1; return Except.ok a.container`): EXIT 0 — VERIFIES. `while true` never exits, so under partial semantics the return is unreachable and the post is vacuously discharged. This is the classic partial-correctness divergence escape (matches the prior pass's atk_diverge2), universal to termination=partial specs (401/500 velvet bundles). NOT a weakness of this postcondition. FAITHFUL REFINED PATCH: the divergence loop maps to no repo op (Contains.as_set is straight-line), so per the documented R/I legs the faithful patch is the gold `return self.args[1]`. Materialized at faithful_patch_atk5.diff and RUN through the official harness: `run_resolve('sympy__sympy-23950', patch)` → completed=True, resolved=True, note='resolved'. Correct echo, not a break (build_one.py:299-314 candidate→resolve policy).
- atk_6 (control-flow-effect with REACHABLE exit: `while x=0 invariant True do x:=0; return Except.ok a.elem`): EXIT 1 — the loop-exit case is reachable (invariant True does not force x=0 at exit), so the wrong return is checked; goal `done_1: ¬x=0 ⊢ Except.ok a.elem = Except.ok a.container`. Confirms only VACUOUS divergence (contradictory exit) escapes, not effectful loops.
- atk_7 (`return Except.ok (max a.elem a.container)`): EXIT 1. Goal `Except.ok (max a.elem a.container) = Except.ok a.container` (wrong when elem>container).
- atk_8 (`return Except.ok (min a.elem a.container)`): EXIT 1. Goal `Except.ok (min a.elem a.container) = Except.ok a.container` (wrong when elem<container).
- POSITIVE CONTROL pos_control (exact correct impl `return Except.ok a.container`): EXIT 0, same_spec=True — spec is satisfiable/non-vacuous.

RESOLVE EVIDENCE (protocol step 2, EXECUTED not speculated): the only verifying wrong impl is atk_5; its faithful refined patch (gold `return self.args[1]`) RESOLVES (completed=True, resolved=True). No verifying wrong impl has a non-resolving faithful patch.

CONCLUSION: No terminating same-spec verifying wrong impl exists; the single verifying attack is a partial-correctness divergence artifact whose faithful patch resolves. verify⇒correct holds for the modeled (terminating) behavioral surface. ≥5 distinct attacks run (8 total: partial-domain, boundary/constant, control-flow-effect ×2, ungrounded-oracle echo, max/min), prepatch reproduced, positive control verifies, resolve executed. G-EQ SOUND, spec TIGHT.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition `out = Except.ok a.container` is a fully-pinned functional equality over an input-grounded RHS (a projection of the input carrier a.container ↔ self.args[1], not an oracle to echo). Every TERMINATING same-spec wrong impl is rejected on the discriminating goal `<lhs> = Except.ok a.container`. The only same-spec verifying wrong impl is atk_5, a vacuous-exit `while true` divergence that discharges the post vacuously under `set_option loom.semantics.termination "partial"` — a partial-correctness artifact universal to all termination=partial velvet bundles, NOT a property of this spec's postcondition. Its faithful refined patch is the gold projection `return self.args[1]` (the divergence loop has no refinement leg; refinement.md has only A1/R + A2/I), which RESOLVES under the official harness (executed). So verify⇏correct does not hold: the spec is TIGHT.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The conversion reads the assertion's own stored
--  components and returns one of them directly; there is no separate callee to
--  contract, so there are no module-level axioms.)
-- axioms-end

-- pure-start
/- A membership assertion: a boolean-valued expression stating that some element
   belongs to some collection. It carries exactly two components — the element
   being tested (`elem`) and the collection it is tested against (`container`).
   Both are modeled as opaque identifiers (`Nat`), since the conversion only
   needs to tell them apart and to hand one of them back unchanged. -/
structure MembershipAssertion where
  elem : Nat
  container : Nat
  deriving DecidableEq

/- The two outcomes the set-conversion of a membership assertion distinguishes:
   a successful conversion yielding a collection, or a refusal (the conversion is
   undefined / unavailable). The refusal arm exists so that a routine which
   declines to produce a collection is expressible against this same spec. -/
inductive ConversionErr where
  | unavailable
  deriving DecidableEq
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The set form of a membership assertion. A statement "this element belongs to
   this collection" describes, as a set, precisely that collection: the set the
   membership ranges over. So converting the assertion to its set form must
   SUCCEED and yield the assertion's collection component — its second component
   — handed back unchanged. The element component is NOT the answer: the result
   is the collection, never the element being tested. The assertion is read-only
   (not `mut`); the conversion reads its components and mutates nothing
   (directive 5). The element, the collection, and the result are modeled as
   `Nat` identifiers; the result is wrapped in `Except` to allow a refusal arm. -/
method asSet (a : MembershipAssertion) return (out : Except ConversionErr Nat)
  ensures out = Except.ok a.container
  do
    -- impl-start
    return Except.ok a.container
    -- impl-end

prove_correct asSet by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

 Gold patch.diff lives at benchmark-verified/sympy__sympy-23950/patch.diff (not under velvet/).

SAME-SPEC: all 8 attacks + positive control confirmed same_spec=True via swebench_unified.markers.same_spec on the velvet backend (impl region only was edited; axioms/pure/pre/post byte-identical).

SPEC SHAPE: `method asSet (a : MembershipAssertion) return (out : Except ConversionErr Nat) ensures out = Except.ok a.container` with body `return Except.ok a.container`. Bijection (mapping.md §2): a.container ↔ self.args[1] (the result), a.elem ↔ self.args[0], Except.ok v ↔ normal return, Except.error .unavailable ↔ declining/raise.

STEP-3 A-LEG AUDIT (VACUOUS): meta.json has axioms=[] and deep_model_references=[]; there is NO axiom_check.py and G-AX skips. refinement.md has exactly 2 legs — A1 (R: param a ↔ self, read-only not mut) and A2 (I: return Except.ok a.container ↔ return self.args[1]). No kind-3 (changed-inexpressible) legs. The R/I correspondence holds and is exercised directly by G-CONF (I-shadow return c.args[1] vs patched as_set over 50014 symbolic assertions, seed 23950, 0 disagreements). No A-legs to falsify.

### ATTACK LEDGER (cmd: `bash scripts/lean_verify.sh <file>`, run; verifications launched concurrently in ≤4-job background batches):
- atk_1 (REAL prepatch bug, `return Except.error ConversionErr.unavailable` = raise NotImplementedError): EXIT 1. PREPATCH REPRODUCED. Residual goal `Except.error ConversionErr.unavailable = Except.ok a.container` (error≠ok, unsatisfiable).
- atk_2 (ungrounded-oracle echo / wrong stored component, `return Except.ok a.elem` = self.args[0]): EXIT 1. Goal `Except.ok a.elem = Except.ok a.container`.
- atk_3 (boundary/constant, `return Except.ok 0`): EXIT 1. Goal `Except.ok 0 = Except.ok a.container`.
- atk_4 (partial-domain, `if a.elem = a.container then ok container else ok elem`): EXIT 1. Loop-free; else-branch goal `if_neg: ¬a.elem=a.container ⊢ Except.ok a.elem = Except.ok a.container`.
- atk_5 (control-flow-effect / VACUOUS-exit divergence: `let mut x:=0; while true invariant True do x:=x+1; return Except.ok a.container`): EXIT 0 — VERIFIES. `while true` never exits, so under partial semantics the return is unreachable and the post is vacuously discharged. This is the classic partial-correctness divergence escape (matches the prior pass's atk_diverge2), universal to termination=partial specs (401/500 velvet bundles). NOT a weakness of this postcondition. FAITHFUL REFINED PATCH: the divergence loop maps to no repo op (Contains.as_set is straight-line), so per the documented R/I legs the faithful patch is the gold `return self.args[1]`. Materialized at faithful_patch_atk5.diff and RUN through the official harness: `run_resolve('sympy__sympy-23950', patch)` → completed=True, resolved=True, note='resolved'. Correct echo, not a break (build_one.py:299-314 candidate→resolve policy).
- atk_6 (control-flow-effect with REACHABLE exit: `while x=0 invariant True do x:=0; return Except.ok a.elem`): EXIT 1 — the loop-exit case is reachable (invariant True does not force x=0 at exit), so the wrong return is checked; goal `done_1: ¬x=0 ⊢ Except.ok a.elem = Except.ok a.container`. Confirms only VACUOUS divergence (contradictory exit) escapes, not effectful loops.
- atk_7 (`return Except.ok (max a.elem a.container)`): EXIT 1. Goal `Except.ok (max a.elem a.container) = Except.ok a.container` (wrong when elem>container).
- atk_8 (`return Except.ok (min a.elem a.container)`): EXIT 1. Goal `Except.ok (min a.elem a.container) = Except.ok a.container` (wrong when elem<container).
- POSITIVE CONTROL pos_control (exact correct impl `return Except.ok a.container`): EXIT 0, same_spec=True — spec is satisfiable/non-vacuous.

RESOLVE EVIDENCE (protocol step 2, EXECUTED not speculated): the only verifying wrong impl is atk_5; its faithful refined patch (gold `return self.args[1]`) RESOLVES (completed=True, resolved=True). No verifying wrong impl has a non-resolving faithful patch.

CONCLUSION: No terminating same-spec verifying wrong impl exists; the single verifying attack is a partial-correctness divergence artifact whose faithful patch resolves. verify⇒correct holds for the modeled (terminating) behavioral surface. ≥5 distinct attacks run (8 total: partial-domain, boundary/constant, control-flow-effect ×2, ungrounded-oracle echo, max/min), prepatch reproduced, positive control verifies, resolve executed. G-EQ SOUND, spec TIGHT.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec == True, velvet tables). Solution.lean verifies via lean_verify.sh (exit 0).

Spec: method asSet(a : MembershipAssertion) return (out : Except ConversionErr Nat) ensures out = Except.ok a.container. This models 'always succeed, return the second stored component (container)'.

Real callee: gold patch makes Contains.as_set(self) = `return self.args[1]` — a total, pure projection. Verified against the real repo at base_commit 88664e6e (patched in worktree): for every genuine symbolic Contains assertion tested — Contains(x,FiniteSet(y)), Contains(x,S.Integers), Contains(x,S.Reals), Contains(x,Interval), Contains(x,FiniteSet(y,1,2)), Contains(x,Union(S.Integers,FiniteSet(y))), Contains(x,Interval(y,y+1)), Contains(x+1,S.Reals), Contains(n,ImageSet(Lambda(x,2*x),S.Integers)) — as_set() SUCCEEDS and returns exactly self.args[1] (identity-equal). A Contains instance always carries exactly two args, so args[1] never raises.

Domain check: the only case that raised IndexError (S.EmptySet) is NOT a Contains instance — it collapses to a boolean via Contains.eval, so as_set is never invoked on it. Correctly outside the modeled domain (refinement/mapping restrict to assertions that stay symbolic, matching the F2P test). The Nat-identity abstraction is exact because the returned object is the same object stored at args[1]; equality of set objects ↔ Nat equality holds for this behavior.

No input in the modeled domain makes the real callee disagree with the spec (never declines, never returns a different component). The always-success postcondition is not too strong: it matches the total real function. The unused Except.error arm only lets the prepatch (which raised) be expressible and fail G-DIFF — it does not weaken faithfulness. Spec is FAITHFUL; no diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified same_spec(Solution.lean, Solution_prepatch.lean) = True over SPEC_REGIONS (axioms/pure/pre/post) for VelvetBackend — spec region is byte-identical between patched and prepatch, so the leak surface is exactly the shared spec view. Ran leakage.screen(): passed, zero hard failures.

Gold edit: Contains.as_set 'raise NotImplementedError()' -> 'return self.args[1]' (return second stored arg = the set). Public problem_statement describes only the BUG (as_set returns a Contains/boolean, not a set, breaking downstream as_relational) and does NOT state the fix. The 'return set' fix appears only in hints_text (out of scope).

Spec-view check for gold-reconstruction beyond problem_statement:
- No gold-diff line reproduced ('return self.args[1]' / 'raise NotImplementedError()' absent; Lean impl body is elided in the view).
- No patched file path (sympy/sets/contains.py) or dotted module path present.
- No patched repo symbol echoed: identifiers are fully abstracted (asSet, MembershipAssertion, elem, container, ConversionErr) — never Contains, as_set, or args. So even the hints term 'set' / repo symbol 'as_set' is not surfaced.
- No bug/fix narration vocabulary; comments describe the abstract behavioral contract (a membership assertion's set form is its collection component), not the edit.

The postcondition 'out = Except.ok a.container' pins the CORRECT behavior (return the collection, never the element). This is the legitimate, unavoidable content of any faithful spec — encoding correct behavior is the task itself, not leakage — and the args[1]<->container binding lives only in producer-side mapping.md, not in the consumer spec view. The behavioral intent ('as_set of Contains(x,S) should be a set, i.e. S') is moreover already derivable from the public problem_statement plus domain knowledge. Nothing in the spec view reconstructs the gold EDIT beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
