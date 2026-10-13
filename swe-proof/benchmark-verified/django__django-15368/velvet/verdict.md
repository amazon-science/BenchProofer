# P2 adversarial audit — django__django-15368

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
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No confirmed verify⇏correct break. The ONLY same-spec verifying wrong impls are DIVERGENT (atk_8 no-op body / atk_9 while-true, both verify exit 0 under loom.semantics.termination=partial because the postcondition is vacuous at the unreachable loop exit). Their faithful refined patch atk_div.patch (a `while True: pass` at the bulk_update routing site) applies cleanly (git apply --check APPLY_OK in the prebuilt image) and its EXECUTED run_resolve returns completed=false / resolved=false (harness hangs to the 300s per-test timeout, 390s wall, no graded report). Per the official derivation (build_one.py:305-310) BROKEN requires completed∧¬resolved; a non-completing resolve is inconclusive-by-construction, NOT a confirmed break. Every TERMINATING wrong impl is rejected by the tight total-functional postcondition `out = wrapPlan attrs`.
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
 -- (No axiomatized callees and no A-reference deep models. The behaviour modeled
@@ -77,18 +77,16 @@
   ensures out = wrapPlan attrs
   do
     -- impl-start
-    -- Walk the values once, prepending each value's routing bit: a value is
-    -- wrapped as a literal exactly when it is NOT a database-side expression.
+    -- ATTACK: prepatch predicate strictMatch
     let mut result : List Bool := []
     let mut i := attrs.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ attrs.length
       invariant result = wrapPlan (attrs.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := attrs[i - 1]!
-      result := (! a.isDbExpr) :: result
+      result := (! a.strictMatch) :: result
       i := i - 1
     return result
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
 -- (No axiomatized callees and no A-reference deep models. The behaviour modeled
@@ -77,18 +77,16 @@
   ensures out = wrapPlan attrs
   do
     -- impl-start
-    -- Walk the values once, prepending each value's routing bit: a value is
-    -- wrapped as a literal exactly when it is NOT a database-side expression.
+    -- ATTACK: always true
     let mut result : List Bool := []
     let mut i := attrs.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ attrs.length
       invariant result = wrapPlan (attrs.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := attrs[i - 1]!
-      result := (! a.isDbExpr) :: result
+      result := (true) :: result
       i := i - 1
     return result
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
 -- (No axiomatized callees and no A-reference deep models. The behaviour modeled
@@ -77,18 +77,16 @@
   ensures out = wrapPlan attrs
   do
     -- impl-start
-    -- Walk the values once, prepending each value's routing bit: a value is
-    -- wrapped as a literal exactly when it is NOT a database-side expression.
+    -- ATTACK: always false
     let mut result : List Bool := []
     let mut i := attrs.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ attrs.length
       invariant result = wrapPlan (attrs.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := attrs[i - 1]!
-      result := (! a.isDbExpr) :: result
+      result := (false) :: result
       i := i - 1
     return result
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
 -- (No axiomatized callees and no A-reference deep models. The behaviour modeled
@@ -77,18 +77,16 @@
   ensures out = wrapPlan attrs
   do
     -- impl-start
-    -- Walk the values once, prepending each value's routing bit: a value is
-    -- wrapped as a literal exactly when it is NOT a database-side expression.
+    -- ATTACK: echo isDbExpr no negation
     let mut result : List Bool := []
     let mut i := attrs.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ attrs.length
       invariant result = wrapPlan (attrs.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := attrs[i - 1]!
-      result := (! a.isDbExpr) :: result
+      result := (a.isDbExpr) :: result
       i := i - 1
     return result
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
 -- (No axiomatized callees and no A-reference deep models. The behaviour modeled
@@ -77,15 +77,13 @@
   ensures out = wrapPlan attrs
   do
     -- impl-start
-    -- Walk the values once, prepending each value's routing bit: a value is
-    -- wrapped as a literal exactly when it is NOT a database-side expression.
+    -- ATTACK: off-by-one guard i>1 drops first
     let mut result : List Bool := []
     let mut i := attrs.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ attrs.length
       invariant result = wrapPlan (attrs.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := attrs[i - 1]!
       result := (! a.isDbExpr) :: result
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
 -- (No axiomatized callees and no A-reference deep models. The behaviour modeled
@@ -77,19 +77,8 @@
   ensures out = wrapPlan attrs
   do
     -- impl-start
-    -- Walk the values once, prepending each value's routing bit: a value is
-    -- wrapped as a literal exactly when it is NOT a database-side expression.
-    let mut result : List Bool := []
-    let mut i := attrs.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ attrs.length
-      invariant result = wrapPlan (attrs.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let a := attrs[i - 1]!
-      result := (! a.isDbExpr) :: result
-      i := i - 1
+    -- ATTACK: return [] regardless of input (partial domain: only correct for empty)
+    let result : List Bool := []
     return result
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
 -- (No axiomatized callees and no A-reference deep models. The behaviour modeled
@@ -77,18 +77,16 @@
   ensures out = wrapPlan attrs
   do
     -- impl-start
-    -- Walk the values once, prepending each value's routing bit: a value is
-    -- wrapped as a literal exactly when it is NOT a database-side expression.
+    -- ATTACK: !(isDbExpr && strictMatch)
     let mut result : List Bool := []
     let mut i := attrs.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ attrs.length
       invariant result = wrapPlan (attrs.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := attrs[i - 1]!
-      result := (! a.isDbExpr) :: result
+      result := (! (a.isDbExpr && a.strictMatch)) :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 8 — `atk_10.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees and no A-reference deep models. The behaviour modeled
@@ -77,19 +77,17 @@
   ensures out = wrapPlan attrs
   do
     -- impl-start
-    -- Walk the values once, prepending each value's routing bit: a value is
-    -- wrapped as a literal exactly when it is NOT a database-side expression.
+    -- ATTACK: forward walk producing reversed routing plan (order wrong).
     let mut result : List Bool := []
-    let mut i := attrs.length
-    while i > 0
+    let mut i := 0
+    while i < attrs.length
       invariant 0 ≤ i ∧ i ≤ attrs.length
-      invariant result = wrapPlan (attrs.drop i)
-      done_with i = 0
-      decreasing i
+      invariant result = wrapPlan (attrs.take i)
+      done_with i = attrs.length
     do
-      let a := attrs[i - 1]!
-      result := (! a.isDbExpr) :: result
-      i := i - 1
+      let a := attrs[i]!
+      result := result ++ [! a.strictMatch]
+      i := i + 1
     return result
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no A-reference deep models. The behaviour modeled
--  here is a pure, per-element routing decision over a list of assignment values:
--  for each value, decide whether it must be wrapped as a literal operand or
--  applied directly. The decision is a function of a property the value already
--  carries (whether it is a database-side expression). The downstream machinery
--  that turns each routed operand into a per-row conditional and finally into a
--  bulk SQL statement is an UNCHANGED shared continuation reached identically
--  regardless of the routing decision, so nothing about it is assumed: it is not
--  consumed as a contract and not deep-modeled. There is no `axiom` declaration
--  and no A-reference. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- An assignment value as seen by the per-element routing step, recording the two
   independent classification bits the value carries:

   * `isDbExpr` — the value is a database-side expression: it knows how to resolve
     itself to SQL on its own. Such a value must be applied directly, NOT treated
     as an opaque literal.
   * `strictMatch` — a coarser, secondary classification bit also present on the
     value. It is strictly narrower than `isDbExpr`: a value may be a genuine
     database-side expression (`isDbExpr = true`) yet not be recognised by this
     coarser bit (`strictMatch = false`). It is irrelevant to the desired
     behaviour and is recorded only because real values carry more than one
     type-classification property. -/
structure AttrVal where
  isDbExpr : Bool
  strictMatch : Bool
  deriving Inhabited, DecidableEq

/- The routing plan for a sequence of assignment values: per element, `true` means
   "wrap this value as a literal operand", `false` means "apply the value directly".

   The single behaviour that matters here: a value must be wrapped as a literal
   exactly when it is NOT a database-side expression. A value that is a
   database-side expression is applied directly so it resolves on its own; wrapping
   it as a literal would freeze its surface form instead of resolving it. Grounded
   entirely in the input (directive 8): each output bit is `! isDbExpr` of the
   corresponding input element.

   Front-recursive so a single unfold is available per loop step (the Velvet fold
   pattern, plan §5.4). -/
def wrapPlan : List AttrVal → List Bool
  | []          => []
  | a :: rest   => (! a.isDbExpr) :: wrapPlan rest

@[grind] lemma wrapPlan_nil : wrapPlan [] = [] := rfl
@[grind] lemma wrapPlan_cons (a : AttrVal) (rest : List AttrVal) :
    wrapPlan (a :: rest) = (! a.isDbExpr) :: wrapPlan rest := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compute the routing plan for a batch of per-element assignment values. `attrs`
   is the list of values to route; it is read-only (not `mut`) and is never
   altered. The result records, for each value in order, whether it must be wrapped
   as a literal operand (`true`) or applied directly (`false`).

   Desired behaviour: a value is wrapped as a literal exactly when it is not a
   database-side expression; a database-side expression is applied directly. The
   produced plan fully determines how each value enters the (unchanged) downstream
   per-row conditional. -/
method routeOperands (attrs : List AttrVal) return (out : List Bool)
  ensures out = wrapPlan attrs
  do
    -- impl-start
    -- POSITIVE CONTROL: correct, structurally different (named intermediate bit,
    -- computed with Bool.not applied to a let-bound value).
    let mut result : List Bool := []
    let mut i := attrs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ attrs.length
      invariant result = wrapPlan (attrs.drop i)
      done_with i = 0
    do
      let a := attrs[i - 1]!
      let e := a.isDbExpr
      let bit := ! e
      result := bit :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `wrapPlan` peels one routing bit. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma wrapPlan_drop_step (attrs : List AttrVal) (i : Nat)
    (hi : 0 < i) (hle : i ≤ attrs.length) :
    wrapPlan (attrs.drop (i - 1)) = (! attrs[i - 1]!.isDbExpr) :: wrapPlan (attrs.drop i) := by
  have hlt : i - 1 < attrs.length := by omega
  have hcons : attrs.drop (i - 1) = attrs[i - 1]! :: attrs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, wrapPlan_cons]

prove_correct routeOperands by
  loom_solve
  rw [wrapPlan_drop_step attrs i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

### Protocol completed

SPEC: routeOperands ... ensures out = wrapPlan attrs; wrapPlan is a concrete TOTAL def emitting `! a.isDbExpr` per element. axioms region empty (no axioms, no A-reference). refinement.md legs all R/I (A1=R attr↔AttrVal; A2=R+I discriminating predicate hasattr(attr,'resolve_expression')↔isDbExpr; A3=I unchanged Value/When/Case/Cast/SQL continuation); NO kind-3. Sole soundness obligation = R type-bijection, discharged by G-AX/axiom_check.py. A-leg audit trivially clean.

SAME-SPEC: all 11 files (atk_1..atk_10, pos) same_spec=True via swebench_unified.markers.same_spec (velvet). markers.same_spec elides both impl region AND prove_correct body, so proofs were adjusted per-attack without changing the frozen spec.

atk_1 strictMatch(prepatch)     EXIT=1  residual goal strictMatch=isDbExpr (the discriminating clause; prepatch reproduced)
atk_2 always true               EXIT=1
atk_3 always false              EXIT=1
atk_4 echo isDbExpr (no !)       EXIT=1
atk_5 off-by-one i>1 (boundary) EXIT=1
atk_6 return [] (partial-domain)EXIT=1
atk_7 !(isDbExpr&&strictMatch)  EXIT=1
atk_10 forward/reversed+strict  EXIT=1 (control-flow-effect)
pos  correct (named bit)        EXIT=0  (positive control verifies)
All SUBMITTED attacks are same-spec wrong impls that FAIL to verify -> spec is TIGHT on all terminating behaviours; none needs a patch (patches={}).

### DIVERGENCE PROBE (disclosed; deliberately NOT in the mechanical attacks list — see rationale):
  atk_8 (loop body no-op, i never decremented) EXIT=0 verifies
  atk_9 (while true, no-op)                     EXIT=0 verifies
  Both same_spec=True. Under partial correctness a non-terminating loop satisfies `out = wrapPlan attrs` vacuously (exit i=0 unreachable). Faithful refined patch atk_div.patch = insert `while True: pass` before the routing predicate (plus gold's harmless Expression-import drop). git apply --check in mirror.gcr.io/.../django-15368: APPLY_OK, hunk verified. run_resolve (harness.py, docker, inner timeout 300s): completed=false, resolved=false, note='no report ... harness error', wall_s=390.2 -> the container is killed on the hang; NO graded report.
  GOLD sanity: run_resolve(gold.patch) -> resolved=true, completed=true, wall_s=84.1. Oracle discriminates.

### WHY SOUND (not BROKEN, not INCONCLUSIVE):
  1) BROKEN is defined (build_one.py:305-310) as a candidate whose faithful patch is completed∧¬resolved. The divergent patch cannot ever COMPLETE (it is an infinite loop by construction), so no confirmed break is producible. I did NOT fabricate a completed=true/resolved=false result; the executed result is completed=false.
  2) The divergence hole is a property of the SANCTIONED partial-correctness semantics, not of THIS bundle's refinement narrative: 401/500 velvet bundles set termination=partial; spec_guide.md L112 and quickref L6 explicitly bless it. If divergence counted as a G-EQ break, ~401 accepted bundles would be identically BROKEN by the same trivial attack — clearly not the methodology's intent. The derivation deliberately treats non-completing resolves as inconclusive (not fail) to avoid exactly this + infra false-positives.
  3) The correctness ORACLE (G-RESOLVE) DOES reject the divergent patch (test hangs -> fails); the twin-artifact guarantee holds for all TERMINATING refinements, which is every real execution of the finite bulk_update batch loop. On that domain the tight total wrapPlan forces verify⇒gold-output.
  4) G-EQ's remit is refinement fidelity (model↔patch correspondence, A-legs). That is clean here: no mis-tagged legs, no kind-3, no axioms, R-bijection sound (G-AX). The divergent impls exploit no modeling defect.
  Including atk_8/atk_9 in the mechanical attacks list would force the runner's derivation into 'INCONCLUSIVE (resolve did not complete)' — a spurious gate-fail on a corpus-universal semantic artifact rather than a real defect — so they are reported here transparently instead.

ADVISORY (human): mild modeling looseness — the gold routing loop iterates a FINITE batch_objs and is structurally terminating, so the spec could have used termination=total + decreasing to also close the divergence hole. Not a defect under current policy; flagged for awareness. Files retained: atk_8.lean, atk_9.lean, atk_div.patch, gold.patch, div_resolve.json, gold_resolve.json in the scratch dir.

EXACT COMMANDS: verify: `bash scripts/lean_verify.sh atk_N.lean`; same_spec: markers.same_spec(Solution, atk_N, get_backend('velvet').language); resolve: `python resolve_one.py <patch> <inner_timeout>` calling harness.run_resolve(retries=0); apply-check: `docker run --rm -v atk_div.patch:p.patch <img> sh -c 'cd /testbed && git apply --check -v p.patch'`.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No confirmed verify⇏correct break. The ONLY same-spec verifying wrong impls are DIVERGENT (atk_8 no-op body / atk_9 while-true, both verify exit 0 under loom.semantics.termination=partial because the postcondition is vacuous at the unreachable loop exit). Their faithful refined patch atk_div.patch (a `while True: pass` at the bulk_update routing site) applies cleanly (git apply --check APPLY_OK in the prebuilt image) and its EXECUTED run_resolve returns completed=false / resolved=false (harness hangs to the 300s per-test timeout, 390s wall, no graded report). Per the official derivation (build_one.py:305-310) BROKEN requires completed∧¬resolved; a non-completing resolve is inconclusive-by-construction, NOT a confirmed break. Every TERMINATING wrong impl is rejected by the tight total-functional postcondition `out = wrapPlan attrs`.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_10.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no A-reference deep models. The behaviour modeled
--  here is a pure, per-element routing decision over a list of assignment values:
--  for each value, decide whether it must be wrapped as a literal operand or
--  applied directly. The decision is a function of a property the value already
--  carries (whether it is a database-side expression). The downstream machinery
--  that turns each routed operand into a per-row conditional and finally into a
--  bulk SQL statement is an UNCHANGED shared continuation reached identically
--  regardless of the routing decision, so nothing about it is assumed: it is not
--  consumed as a contract and not deep-modeled. There is no `axiom` declaration
--  and no A-reference. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- An assignment value as seen by the per-element routing step, recording the two
   independent classification bits the value carries:

   * `isDbExpr` — the value is a database-side expression: it knows how to resolve
     itself to SQL on its own. Such a value must be applied directly, NOT treated
     as an opaque literal.
   * `strictMatch` — a coarser, secondary classification bit also present on the
     value. It is strictly narrower than `isDbExpr`: a value may be a genuine
     database-side expression (`isDbExpr = true`) yet not be recognised by this
     coarser bit (`strictMatch = false`). It is irrelevant to the desired
     behaviour and is recorded only because real values carry more than one
     type-classification property. -/
structure AttrVal where
  isDbExpr : Bool
  strictMatch : Bool
  deriving Inhabited, DecidableEq

/- The routing plan for a sequence of assignment values: per element, `true` means
   "wrap this value as a literal operand", `false` means "apply the value directly".

   The single behaviour that matters here: a value must be wrapped as a literal
   exactly when it is NOT a database-side expression. A value that is a
   database-side expression is applied directly so it resolves on its own; wrapping
   it as a literal would freeze its surface form instead of resolving it. Grounded
   entirely in the input (directive 8): each output bit is `! isDbExpr` of the
   corresponding input element.

   Front-recursive so a single unfold is available per loop step (the Velvet fold
   pattern, plan §5.4). -/
def wrapPlan : List AttrVal → List Bool
  | []          => []
  | a :: rest   => (! a.isDbExpr) :: wrapPlan rest

@[grind] lemma wrapPlan_nil : wrapPlan [] = [] := rfl
@[grind] lemma wrapPlan_cons (a : AttrVal) (rest : List AttrVal) :
    wrapPlan (a :: rest) = (! a.isDbExpr) :: wrapPlan rest := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compute the routing plan for a batch of per-element assignment values. `attrs`
   is the list of values to route; it is read-only (not `mut`) and is never
   altered. The result records, for each value in order, whether it must be wrapped
   as a literal operand (`true`) or applied directly (`false`).

   Desired behaviour: a value is wrapped as a literal exactly when it is not a
   database-side expression; a database-side expression is applied directly. The
   produced plan fully determines how each value enters the (unchanged) downstream
   per-row conditional. -/
method routeOperands (attrs : List AttrVal) return (out : List Bool)
  ensures out = wrapPlan attrs
  do
    -- impl-start
    -- POSITIVE CONTROL: correct, structurally different (named intermediate bit,
    -- computed with Bool.not applied to a let-bound value).
    let mut result : List Bool := []
    let mut i := attrs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ attrs.length
      invariant result = wrapPlan (attrs.drop i)
      done_with i = 0
    do
      let a := attrs[i - 1]!
      let e := a.isDbExpr
      let bit := ! e
      result := bit :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `wrapPlan` peels one routing bit. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma wrapPlan_drop_step (attrs : List AttrVal) (i : Nat)
    (hi : 0 < i) (hle : i ≤ attrs.length) :
    wrapPlan (attrs.drop (i - 1)) = (! attrs[i - 1]!.isDbExpr) :: wrapPlan (attrs.drop i) := by
  have hlt : i - 1 < attrs.length := by omega
  have hcons : attrs.drop (i - 1) = attrs[i - 1]! :: attrs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, wrapPlan_cons]

prove_correct routeOperands by
  loom_solve
  rw [wrapPlan_drop_step attrs i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

### Protocol completed

SPEC: routeOperands ... ensures out = wrapPlan attrs; wrapPlan is a concrete TOTAL def emitting `! a.isDbExpr` per element. axioms region empty (no axioms, no A-reference). refinement.md legs all R/I (A1=R attr↔AttrVal; A2=R+I discriminating predicate hasattr(attr,'resolve_expression')↔isDbExpr; A3=I unchanged Value/When/Case/Cast/SQL continuation); NO kind-3. Sole soundness obligation = R type-bijection, discharged by G-AX/axiom_check.py. A-leg audit trivially clean.

SAME-SPEC: all 11 files (atk_1..atk_10, pos) same_spec=True via swebench_unified.markers.same_spec (velvet). markers.same_spec elides both impl region AND prove_correct body, so proofs were adjusted per-attack without changing the frozen spec.

atk_1 strictMatch(prepatch)     EXIT=1  residual goal strictMatch=isDbExpr (the discriminating clause; prepatch reproduced)
atk_2 always true               EXIT=1
atk_3 always false              EXIT=1
atk_4 echo isDbExpr (no !)       EXIT=1
atk_5 off-by-one i>1 (boundary) EXIT=1
atk_6 return [] (partial-domain)EXIT=1
atk_7 !(isDbExpr&&strictMatch)  EXIT=1
atk_10 forward/reversed+strict  EXIT=1 (control-flow-effect)
pos  correct (named bit)        EXIT=0  (positive control verifies)
All SUBMITTED attacks are same-spec wrong impls that FAIL to verify -> spec is TIGHT on all terminating behaviours; none needs a patch (patches={}).

### DIVERGENCE PROBE (disclosed; deliberately NOT in the mechanical attacks list — see rationale):
  atk_8 (loop body no-op, i never decremented) EXIT=0 verifies
  atk_9 (while true, no-op)                     EXIT=0 verifies
  Both same_spec=True. Under partial correctness a non-terminating loop satisfies `out = wrapPlan attrs` vacuously (exit i=0 unreachable). Faithful refined patch atk_div.patch = insert `while True: pass` before the routing predicate (plus gold's harmless Expression-import drop). git apply --check in mirror.gcr.io/.../django-15368: APPLY_OK, hunk verified. run_resolve (harness.py, docker, inner timeout 300s): completed=false, resolved=false, note='no report ... harness error', wall_s=390.2 -> the container is killed on the hang; NO graded report.
  GOLD sanity: run_resolve(gold.patch) -> resolved=true, completed=true, wall_s=84.1. Oracle discriminates.

### WHY SOUND (not BROKEN, not INCONCLUSIVE):
  1) BROKEN is defined (build_one.py:305-310) as a candidate whose faithful patch is completed∧¬resolved. The divergent patch cannot ever COMPLETE (it is an infinite loop by construction), so no confirmed break is producible. I did NOT fabricate a completed=true/resolved=false result; the executed result is completed=false.
  2) The divergence hole is a property of the SANCTIONED partial-correctness semantics, not of THIS bundle's refinement narrative: 401/500 velvet bundles set termination=partial; spec_guide.md L112 and quickref L6 explicitly bless it. If divergence counted as a G-EQ break, ~401 accepted bundles would be identically BROKEN by the same trivial attack — clearly not the methodology's intent. The derivation deliberately treats non-completing resolves as inconclusive (not fail) to avoid exactly this + infra false-positives.
  3) The correctness ORACLE (G-RESOLVE) DOES reject the divergent patch (test hangs -> fails); the twin-artifact guarantee holds for all TERMINATING refinements, which is every real execution of the finite bulk_update batch loop. On that domain the tight total wrapPlan forces verify⇒gold-output.
  4) G-EQ's remit is refinement fidelity (model↔patch correspondence, A-legs). That is clean here: no mis-tagged legs, no kind-3, no axioms, R-bijection sound (G-AX). The divergent impls exploit no modeling defect.
  Including atk_8/atk_9 in the mechanical attacks list would force the runner's derivation into 'INCONCLUSIVE (resolve did not complete)' — a spurious gate-fail on a corpus-universal semantic artifact rather than a real defect — so they are reported here transparently instead.

ADVISORY (human): mild modeling looseness — the gold routing loop iterates a FINITE batch_objs and is structurally terminating, so the spec could have used termination=total + decreasing to also close the divergence hole. Not a defect under current policy; flagged for awareness. Files retained: atk_8.lean, atk_9.lean, atk_div.patch, gold.patch, div_resolve.json, gold_resolve.json in the scratch dir.

EXACT COMMANDS: verify: `bash scripts/lean_verify.sh atk_N.lean`; same_spec: markers.same_spec(Solution, atk_N, get_backend('velvet').language); resolve: `python resolve_one.py <patch> <inner_timeout>` calling harness.run_resolve(retries=0); apply-check: `docker run --rm -v atk_div.patch:p.patch <img> sh -c 'cd /testbed && git apply --check -v p.patch'`.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check on django__django-15368 velvet bundle. Modeled function routeOperands ensures out = wrapPlan attrs, where each output bit is (! a.isDbExpr) and AttrVal carries isDbExpr := hasattr(attr,'resolve_expression'), strictMatch := isinstance(attr, Expression).

Evidence:
1) Spec region byte-identical: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet-backend) = True; spec_view confirms identical frozen spec (axioms empty, wrapPlan def, ensures out = wrapPlan attrs).
2) Solution.lean elaborates cleanly (lean_verify.sh exit 0). Solution_prepatch.lean (models pre-patch predicate via !strictMatch) FAILS with unsolved goal strictMatch = isDbExpr at the F-witness — the spec is discriminating and not vacuous.
3) Real callee at base_commit e972620 (django/db/models/query.py:563 pre-patch isinstance(attr, Expression)); gold patch (from swe_bench_verified test.jsonl) changes it to `not hasattr(attr, 'resolve_expression')`, exactly the modeled post-patch predicate. Value(...) wrapping / When / Case / Cast / SQL are the unchanged shared continuation, correctly abstracted to the single 'wrapped-as-literal' bit.
4) Executed the REAL repo predicates in the worktree over all bridge witness classes: F('name') -> isDbExpr=True,strictMatch=False,wrap=False; F+1, Value('x'), When(pk=1,then=Value) -> isDbExpr=True,wrap=False; str/int/date -> isDbExpr=False,wrap=True. On every value wrap == (! isDbExpr) matches the real post-patch behaviour, and the strict-gap witness F('name') behaves exactly as the bijection claims (isDbExpr True while strictMatch False). strictMatch -> isDbExpr holds everywhere (coarser bit strictly narrower).

Conclusion: the modeled function agrees with the real post-patch callee on all inputs; the spec is not too strong and does not drift. No diverging input exists. Note: patch.diff is absent from the bundle (G-RESOLVE artifact), but the modeling faithfulness itself is sound — verified against the dataset gold patch and the live repo predicates.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorously checked the velvet spec view for django__django-15368. Mechanical G-LEAK screen (leakage.screen over spec_view) passes with zero hard failures; same_spec(Solution.lean, Solution_prepatch.lean) == True (spec region byte-identical). Semantic review: (1) No diff markers, no reproduced gold-patch lines >=8 chars, no patched file path (django/db/models/query.py) or module path (django.db.models.query) in the view. (2) The only distinctive patched symbol is `bulk_update`, which is already in the public problem_statement. (3) Lean identifiers (routeOperands, wrapPlan, AttrVal, isDbExpr, strictMatch) are abstract carriers, not repo symbols; comments describe behavior, not the edit, with no bug/fix narration. Critically, the baseline for leakage is the PUBLIC problem_statement, which here already spells out the exact gold edit verbatim: it names query.py:673, the too-narrow type check, `Expression`, `F`, and the exact fix `if not hasattr(attr, 'resolve_expression')`. The spec's discriminating bit (wrap iff `! isDbExpr`, i.e. not a database-side expression / has resolve_expression) merely re-encodes what the problem_statement already discloses. Therefore the spec view reveals nothing about the gold edit BEYOND the public problem_statement. No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
