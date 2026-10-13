# P2 adversarial audit — sympy__sympy-15875

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
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 
 /- One term of a commutative sum, reduced to the only four fuzzy observations the
    zero-decision reads. Each is a three-valued fact (`some true` = known true,
@@ -112,18 +112,35 @@
   ensures out = sumIsZeroSpec isComm args
   do
     -- impl-start
+    -- Pre-image skeleton: the residual-empty guard is absent. When no term is
+    -- real-and-definitely-nonzero, this still consults the residual sub-decision
+    -- over the empty residual and combines it with the imaginary tallies, rather
+    -- than declaring the verdict undetermined. The frozen spec's verdict guards
+    -- that case (acc.nz.length = 0 ⇒ none), so prove_correct MUST fail.
     let mut acc : Tally := { z := 0, nz := [], im := false, imOrZ := false, bail := false }
     let mut i := args.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ args.length
       invariant acc = tallyAll (args.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := args[i - 1]!
       acc := classify a acc
       i := i - 1
-    return verdict isComm args.length acc
+    let result : Option Bool :=
+      if isComm = some false then none
+      else if acc.bail then none
+      else if acc.z = args.length then some true
+      else if acc.nz.length = args.length then none
+      else
+        match residualIsZero acc.nz with
+        | some true =>
+            if !acc.imOrZ && !acc.im then some true
+            else if acc.im && !acc.imOrZ then some false
+            else none
+        | some false => some false
+        | none => none
+    return result
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
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
 
 /- One term of a commutative sum, reduced to the only four fuzzy observations the
    zero-decision reads. Each is a three-valued fact (`some true` = known true,
@@ -118,12 +118,11 @@
       invariant 0 ≤ i ∧ i ≤ args.length
       invariant acc = tallyAll (args.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := args[i - 1]!
       acc := classify a acc
       i := i - 1
-    return verdict isComm args.length acc
+    return none
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
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
 
 /- One term of a commutative sum, reduced to the only four fuzzy observations the
    zero-decision reads. Each is a three-valued fact (`some true` = known true,
@@ -118,12 +118,24 @@
       invariant 0 ≤ i ∧ i ≤ args.length
       invariant acc = tallyAll (args.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := args[i - 1]!
       acc := classify a acc
       i := i - 1
-    return verdict isComm args.length acc
+    let result : Option Bool :=
+      if isComm = some false then none
+      else if acc.bail then none
+      else if acc.z = args.length then some true
+      else if acc.nz.length = 0 then none
+      else
+        match residualIsZero acc.nz with
+        | some true =>
+            if !acc.imOrZ && !acc.im then some true
+            else if acc.im && !acc.imOrZ then some false
+            else none
+        | some false => some false
+        | none => none
+    return result
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
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
 
 /- One term of a commutative sum, reduced to the only four fuzzy observations the
    zero-decision reads. Each is a three-valued fact (`some true` = known true,
@@ -118,12 +118,24 @@
       invariant 0 ≤ i ∧ i ≤ args.length
       invariant acc = tallyAll (args.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := args[i - 1]!
       acc := classify a acc
       i := i - 1
-    return verdict isComm args.length acc
+    let result : Option Bool :=
+      if isComm = some false then none
+      else if acc.z = args.length then some true
+      else if acc.bail then none
+      else if acc.nz.length = 0 ∨ acc.nz.length = args.length then none
+      else
+        match residualIsZero acc.nz with
+        | some true =>
+            if !acc.imOrZ && !acc.im then some true
+            else if acc.im && !acc.imOrZ then some false
+            else none
+        | some false => some false
+        | none => none
+    return result
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
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
 
 /- One term of a commutative sum, reduced to the only four fuzzy observations the
    zero-decision reads. Each is a three-valued fact (`some true` = known true,
@@ -118,12 +118,24 @@
       invariant 0 ≤ i ∧ i ≤ args.length
       invariant acc = tallyAll (args.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := args[i - 1]!
       acc := classify a acc
       i := i - 1
-    return verdict isComm args.length acc
+    let result : Option Bool :=
+      if isComm = some false then none
+      else if acc.bail then none
+      else if acc.z = args.length then some true
+      else if acc.nz.length = 0 ∨ acc.nz.length = args.length then none
+      else
+        match residualIsZero acc.nz with
+        | some true =>
+            if !acc.imOrZ && !acc.im then some false
+            else if acc.im && !acc.imOrZ then some true
+            else none
+        | some false => some false
+        | none => none
+    return result
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
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
 
 /- One term of a commutative sum, reduced to the only four fuzzy observations the
    zero-decision reads. Each is a three-valued fact (`some true` = known true,
@@ -118,12 +118,11 @@
       invariant 0 ≤ i ∧ i ≤ args.length
       invariant acc = tallyAll (args.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := args[i - 1]!
       acc := classify a acc
       i := i - 1
-    return verdict isComm args.length acc
+    return residualIsZero args
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
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
 
 /- One term of a commutative sum, reduced to the only four fuzzy observations the
    zero-decision reads. Each is a three-valued fact (`some true` = known true,
@@ -118,12 +118,11 @@
       invariant 0 ≤ i ∧ i ≤ args.length
       invariant acc = tallyAll (args.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := args[i - 1]!
       acc := classify a acc
       i := i - 1
-    return verdict isComm args.length acc
+    return residualIsZero acc.nz
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- One term of a commutative sum, reduced to the only four fuzzy observations the
    zero-decision reads. Each is a three-valued fact (`some true` = known true,
@@ -118,12 +118,23 @@
       invariant 0 ≤ i ∧ i ≤ args.length
       invariant acc = tallyAll (args.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := args[i - 1]!
       acc := classify a acc
       i := i - 1
-    return verdict isComm args.length acc
+    let result : Option Bool :=
+      if acc.bail then none
+      else if acc.z = args.length then some true
+      else if acc.nz.length = 0 ∨ acc.nz.length = args.length then none
+      else
+        match residualIsZero acc.nz with
+        | some true =>
+            if !acc.imOrZ && !acc.im then some true
+            else if acc.im && !acc.imOrZ then some false
+            else none
+        | some false => some false
+        | none => none
+    return result
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/- One term of a commutative sum, reduced to the only four fuzzy observations the
   zero-decision reads. Each is a three-valued fact (`some true` = known true,
   `some false` = known false, `none` = undetermined):

   * `isReal`      — the term is a real quantity;
   * `isZero`      — the term equals zero (consulted only for real terms);
   * `isImaginary` — the term is a pure-imaginary quantity;
   * `iMulReal`    — multiplying the term by the imaginary unit yields a real
                     quantity (i.e. the term is "imaginary-or-zero"). -/
structure Term where
  isReal : Option Bool
  isZero : Option Bool
  isImaginary : Option Bool
  iMulReal : Option Bool
  deriving Inhabited, Repr, DecidableEq

-- axioms-start
/- The zero-decision for the residual sum of the strictly-real, definitely-nonzero
   terms. It is an UNCHANGED sub-decision the operation defers to: it inspects a
   smaller, all-real sum than the one under decision and returns the same
   three-valued verdict that the surrounding machinery would. Left OPAQUE — the
   operation refines around it, never reimplements it, so the proof claims no
   property of its value. Provenance + executable patch-invariance check:
   mapping.md §3 / axiom_check.py (G-AX). -/
opaque residualIsZero : List Term → Option Bool
-- axioms-end

-- pure-start
/- The running tally accumulated while scanning the terms:

   * `z`     — how many terms are real and known to be zero;
   * `nz`    — the terms that are real and known to be nonzero, in order;
   * `im`    — whether some term is pure-imaginary;
   * `imOrZ` — whether some term is imaginary-or-zero but not pure-imaginary;
   * `bail`  — whether some term defies classification, forcing an undetermined
               overall verdict. -/
structure Tally where
  z : Nat
  nz : List Term
  im : Bool
  imOrZ : Bool
  bail : Bool
  deriving Inhabited, Repr

/- Fold one term into the tally. Once a term has defied classification the tally
   is undetermined and stays so. A real term is counted as zero, recorded as
   nonzero, or (when its zero-ness is undetermined) forces a bail. A non-real
   term sets the imaginary or imaginary-or-zero flag, else forces a bail. -/
def classify (a : Term) (acc : Tally) : Tally :=
  if acc.bail then acc
  else if a.isReal = some true then
    if a.isZero = some true then { acc with z := acc.z + 1 }
    else if a.isZero = some false then { acc with nz := a :: acc.nz }
    else { acc with bail := true }
  else if a.isImaginary = some true then { acc with im := true }
  else if a.iMulReal = some true then { acc with imOrZ := true }
  else { acc with bail := true }

/- The tally of a whole term list. Front-recursive so a single unfold is
   available per loop step (the fold pattern, plan §5.4). -/
def tallyAll : List Term → Tally
  | []      => { z := 0, nz := [], im := false, imOrZ := false, bail := false }
  | a :: xs => classify a (tallyAll xs)

@[grind] lemma tallyAll_nil :
    tallyAll [] = { z := 0, nz := [], im := false, imOrZ := false, bail := false } := rfl
@[grind] lemma tallyAll_cons (a : Term) (xs : List Term) :
    tallyAll (a :: xs) = classify a (tallyAll xs) := rfl

/- The three-valued verdict from a completed tally over `n` terms.

   `isComm` carries the whole sum's commutativity fact: a definitely-noncommutative
   sum is undetermined outright. Otherwise: an unclassifiable term ⇒ undetermined;
   every term real-and-zero ⇒ the sum is zero; no real-nonzero term at all, OR
   every term real-nonzero ⇒ undetermined (the residual sub-decision is not
   informative here); otherwise consult the residual sub-decision over the
   real-nonzero terms and combine it with the imaginary tallies. -/
def verdict (isComm : Option Bool) (n : Nat) (acc : Tally) : Option Bool :=
  if isComm = some false then none
  else if acc.bail then none
  else if acc.z = n then some true
  else if acc.nz.length = 0 ∨ acc.nz.length = n then none
  else
    match residualIsZero acc.nz with
    | some true =>
        if !acc.imOrZ && !acc.im then some true
        else if acc.im && !acc.imOrZ then some false
        else none
    | some false => some false
    | none => none

/- The desired three-valued zero-verdict for a commutative sum of `args`. -/
def sumIsZeroSpec (isComm : Option Bool) (args : List Term) : Option Bool :=
  verdict isComm args.length (tallyAll args)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method sumIsZero (isComm : Option Bool) (args : List Term) return (out : Option Bool)
  ensures out = sumIsZeroSpec isComm args
  do
    -- impl-start
    let mut acc : Tally := { z := 0, nz := [], im := false, imOrZ := false, bail := false }
    let mut i := args.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ args.length
      invariant acc = tallyAll (args.drop i)
      done_with i = 0
    do
      let a := args[i - 1]!
      acc := classify a acc
      i := i - 1
    return verdict isComm args.length acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `tallyAll` peels one `classify`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma tallyAll_drop_step (args : List Term) (i : Nat)
    (hi : 0 < i) (hle : i ≤ args.length) :
    tallyAll (args.drop (i - 1)) = classify args[i - 1]! (tallyAll (args.drop i)) := by
  have hlt : i - 1 < args.length := by omega
  have hcons : args.drop (i - 1) = args[i - 1]! :: args.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, tallyAll_cons]

prove_correct sumIsZero by
  loom_solve
  all_goals first
    | (rw [tallyAll_drop_step args i (by omega) (by omega)]; simp_all)
    | simp_all [sumIsZeroSpec]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ SOUND. Spec is an exact functional pin: `ensures out = sumIsZeroSpec isComm args = verdict isComm args.length (tallyAll args)`; the gold fix (empty-nz => None) is encoded CONCRETELY as the literal disjunction `acc.nz.length = 0 ∨ acc.nz.length = n → none` in `verdict` (Solution.lean:90), NOT behind an axiom. Only A leg = opaque `residualIsZero` (A-reference, no consumed contract).

ATTACK BATTERY (all same_spec=True, impl-region-only edits; spec region lines 1-113 byte-identical to Solution.lean, confirmed via markers.same_spec; verified with scripts/lean_verify.sh <f>):
- atk_1 = Solution_prepatch.lean VERBATIM (PREPATCH BUG: drops the `nz.length=0` half of the guard). exit 1 — leaves `ensures_1` goal (inlined cascade ≠ verdict) unprovable exactly on empty-nz (issue reproducer -2*I+(1+I)**2). [prepatch_reproduced]
- atk_2 = `return none` (partial-domain/degenerate). exit 1 (`none = verdict …` unprovable).
- atk_3 = BOUNDARY mirror: keep only `nz.length = 0` guard, drop `= n` half. exit 1.
- atk_4 = CONTROL-FLOW-EFFECT: reorder cascade so `z = n` check precedes the `bail → none` guard. exit 1.
- atk_5 = swap the imaginary-combine tail (some true<->some false). exit 1.
- atk_6 = UNGROUNDED-ORACLE ECHO: `return residualIsZero args`. exit 1 — goal `residualIsZero args = verdict …` unprovable; the opaque symbol on the wrong arg cannot equal the verdict.
- atk_7 = UNGROUNDED-ORACLE ECHO #2: `return residualIsZero acc.nz`. exit 1 — goal `residualIsZero acc.nz = verdict …` unprovable. atk_6/atk_7 empirically confirm the A-reference has NO exploitable/consumed contract (the postcondition is pinned structurally on args length+tally+the concrete disjunction, not on the opaque callee's value).
- atk_9 = drop the `isComm = some false → none` guard. exit 1.
All 8 terminating behavioral mutants FAIL to verify (exit 1). Positive control atk_pc = gold impl (structurally identical loop+verdict), exit 0 — spec non-vacuous & satisfiable. Command form: `bash scripts/lean_verify.sh atk_N.lean`.

DIVERGENCE-VACUITY FINDING (documented, deliberately EXCLUDED from submitted attacks): three `while true` (no `done_with`) non-terminating impls — atk_8 (`return none`), atk_8b (`return some true`), atk_8c (`return some false`) — ALL verify (exit 0) REGARDLESS of returned value. This proves the verification is pure divergence-vacuity under the methodology-sanctioned `set_option loom.semantics.termination "partial"` + `open PartialCorrectness` (spec_guide.md:112, REQUIRED by G-HYGIENE for every velvet bundle): a divergent program vacuously satisfies ANY postcondition.

It is (a) universal to all 500 velvet bundles, not a property of THIS spec's refinement fidelity, and (b) has NO faithful refined patch — the real `Add._eval_is_zero` always terminates and refinement.md maps a terminating fold (tallyAll/classify) ↔ the terminating `for a in self.args` loop. Submitting it with no patch would falsely force INCONCLUSIVE; there is no honest faithful patch to run through run_resolve because no faithful refinement of a divergent loop exists. It is therefore out of G-EQ scope (refinement fidelity), not a verify⇏correct break. NO run_resolve was needed for the verdict: no in-scope verifying wrong impl exists (patches={}).

REFINEMENT.MD LEG AUDIT: A1(R type-refine), A2(R+I fold↔for-loop), A3(I concrete cascade + A-reference), A4(A-reference residualIsZero), A5(R) — NO kind-3. The lone changed op (the empty-nz guard) is modeled concretely as a disjunction, not axiomatized. The single A leg residualIsZero is an A-reference (opaque, zero consumed contract; proof discharges via fold + verdict unfolding only) for the UNCHANGED `self.func(*nz).is_zero`; correspondence validated by G-AX (recorded pass: patch-invariant on 5708 reached observations, sole divergence the guarded len(nz)==0 case) and mapping.md §3. Correspondence holds.

VERDICT: SOUND — 8 same-spec terminating wrong impls all rejected, positive control verifies, prepatch reproduced (atk_1), no kind-3 legs, the A-reference has no exploitable contract, and the only verifiers are out-of-scope divergence-vacuity artifacts with no faithful patch.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/- One term of a commutative sum, reduced to the only four fuzzy observations the
   zero-decision reads. Each is a three-valued fact (`some true` = known true,
   `some false` = known false, `none` = undetermined):

   * `isReal`      — the term is a real quantity;
   * `isZero`      — the term equals zero (consulted only for real terms);
   * `isImaginary` — the term is a pure-imaginary quantity;
   * `iMulReal`    — multiplying the term by the imaginary unit yields a real
                     quantity (i.e. the term is "imaginary-or-zero"). -/
structure Term where
  isReal : Option Bool
  isZero : Option Bool
  isImaginary : Option Bool
  iMulReal : Option Bool
  deriving Inhabited, Repr, DecidableEq

-- axioms-start
/- The zero-decision for the residual sum of the strictly-real, definitely-nonzero
   terms. It is an UNCHANGED sub-decision the operation defers to: it inspects a
   smaller, all-real sum than the one under decision and returns the same
   three-valued verdict that the surrounding machinery would. Left OPAQUE — the
   operation refines around it, never reimplements it, so the proof claims no
   property of its value. Provenance + executable patch-invariance check:
   mapping.md §3 / axiom_check.py (G-AX). -/
opaque residualIsZero : List Term → Option Bool
-- axioms-end

-- pure-start
/- The running tally accumulated while scanning the terms:

   * `z`     — how many terms are real and known to be zero;
   * `nz`    — the terms that are real and known to be nonzero, in order;
   * `im`    — whether some term is pure-imaginary;
   * `imOrZ` — whether some term is imaginary-or-zero but not pure-imaginary;
   * `bail`  — whether some term defies classification, forcing an undetermined
               overall verdict. -/
structure Tally where
  z : Nat
  nz : List Term
  im : Bool
  imOrZ : Bool
  bail : Bool
  deriving Inhabited, Repr

/- Fold one term into the tally. Once a term has defied classification the tally
   is undetermined and stays so. A real term is counted as zero, recorded as
   nonzero, or (when its zero-ness is undetermined) forces a bail. A non-real
   term sets the imaginary or imaginary-or-zero flag, else forces a bail. -/
def classify (a : Term) (acc : Tally) : Tally :=
  if acc.bail then acc
  else if a.isReal = some true then
    if a.isZero = some true then { acc with z := acc.z + 1 }
    else if a.isZero = some false then { acc with nz := a :: acc.nz }
    else { acc with bail := true }
  else if a.isImaginary = some true then { acc with im := true }
  else if a.iMulReal = some true then { acc with imOrZ := true }
  else { acc with bail := true }

/- The tally of a whole term list. Front-recursive so a single unfold is
   available per loop step (the fold pattern, plan §5.4). -/
def tallyAll : List Term → Tally
  | []      => { z := 0, nz := [], im := false, imOrZ := false, bail := false }
  | a :: xs => classify a (tallyAll xs)

@[grind] lemma tallyAll_nil :
    tallyAll [] = { z := 0, nz := [], im := false, imOrZ := false, bail := false } := rfl
@[grind] lemma tallyAll_cons (a : Term) (xs : List Term) :
    tallyAll (a :: xs) = classify a (tallyAll xs) := rfl

/- The three-valued verdict from a completed tally over `n` terms.

   `isComm` carries the whole sum's commutativity fact: a definitely-noncommutative
   sum is undetermined outright. Otherwise: an unclassifiable term ⇒ undetermined;
   every term real-and-zero ⇒ the sum is zero; no real-nonzero term at all, OR
   every term real-nonzero ⇒ undetermined (the residual sub-decision is not
   informative here); otherwise consult the residual sub-decision over the
   real-nonzero terms and combine it with the imaginary tallies. -/
def verdict (isComm : Option Bool) (n : Nat) (acc : Tally) : Option Bool :=
  if isComm = some false then none
  else if acc.bail then none
  else if acc.z = n then some true
  else if acc.nz.length = 0 ∨ acc.nz.length = n then none
  else
    match residualIsZero acc.nz with
    | some true =>
        if !acc.imOrZ && !acc.im then some true
        else if acc.im && !acc.imOrZ then some false
        else none
    | some false => some false
    | none => none

/- The desired three-valued zero-verdict for a commutative sum of `args`. -/
def sumIsZeroSpec (isComm : Option Bool) (args : List Term) : Option Bool :=
  verdict isComm args.length (tallyAll args)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method sumIsZero (isComm : Option Bool) (args : List Term) return (out : Option Bool)
  ensures out = sumIsZeroSpec isComm args
  do
    -- impl-start
    let mut acc : Tally := { z := 0, nz := [], im := false, imOrZ := false, bail := false }
    let mut i := args.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ args.length
      invariant acc = tallyAll (args.drop i)
      done_with i = 0
    do
      let a := args[i - 1]!
      acc := classify a acc
      i := i - 1
    return verdict isComm args.length acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `tallyAll` peels one `classify`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma tallyAll_drop_step (args : List Term) (i : Nat)
    (hi : 0 < i) (hle : i ≤ args.length) :
    tallyAll (args.drop (i - 1)) = classify args[i - 1]! (tallyAll (args.drop i)) := by
  have hlt : i - 1 < args.length := by omega
  have hcons : args.drop (i - 1) = args[i - 1]! :: args.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, tallyAll_cons]

prove_correct sumIsZero by
  loom_solve
  all_goals first
    | (rw [tallyAll_drop_step args i (by omega) (by omega)]; simp_all)
    | simp_all [sumIsZeroSpec]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ SOUND. Spec is an exact functional pin: `ensures out = sumIsZeroSpec isComm args = verdict isComm args.length (tallyAll args)`; the gold fix (empty-nz => None) is encoded CONCRETELY as the literal disjunction `acc.nz.length = 0 ∨ acc.nz.length = n → none` in `verdict` (Solution.lean:90), NOT behind an axiom. Only A leg = opaque `residualIsZero` (A-reference, no consumed contract).

ATTACK BATTERY (all same_spec=True, impl-region-only edits; spec region lines 1-113 byte-identical to Solution.lean, confirmed via markers.same_spec; verified with scripts/lean_verify.sh <f>):
- atk_1 = Solution_prepatch.lean VERBATIM (PREPATCH BUG: drops the `nz.length=0` half of the guard). exit 1 — leaves `ensures_1` goal (inlined cascade ≠ verdict) unprovable exactly on empty-nz (issue reproducer -2*I+(1+I)**2). [prepatch_reproduced]
- atk_2 = `return none` (partial-domain/degenerate). exit 1 (`none = verdict …` unprovable).
- atk_3 = BOUNDARY mirror: keep only `nz.length = 0` guard, drop `= n` half. exit 1.
- atk_4 = CONTROL-FLOW-EFFECT: reorder cascade so `z = n` check precedes the `bail → none` guard. exit 1.
- atk_5 = swap the imaginary-combine tail (some true<->some false). exit 1.
- atk_6 = UNGROUNDED-ORACLE ECHO: `return residualIsZero args`. exit 1 — goal `residualIsZero args = verdict …` unprovable; the opaque symbol on the wrong arg cannot equal the verdict.
- atk_7 = UNGROUNDED-ORACLE ECHO #2: `return residualIsZero acc.nz`. exit 1 — goal `residualIsZero acc.nz = verdict …` unprovable. atk_6/atk_7 empirically confirm the A-reference has NO exploitable/consumed contract (the postcondition is pinned structurally on args length+tally+the concrete disjunction, not on the opaque callee's value).
- atk_9 = drop the `isComm = some false → none` guard. exit 1.
All 8 terminating behavioral mutants FAIL to verify (exit 1). Positive control atk_pc = gold impl (structurally identical loop+verdict), exit 0 — spec non-vacuous & satisfiable. Command form: `bash scripts/lean_verify.sh atk_N.lean`.

DIVERGENCE-VACUITY FINDING (documented, deliberately EXCLUDED from submitted attacks): three `while true` (no `done_with`) non-terminating impls — atk_8 (`return none`), atk_8b (`return some true`), atk_8c (`return some false`) — ALL verify (exit 0) REGARDLESS of returned value. This proves the verification is pure divergence-vacuity under the methodology-sanctioned `set_option loom.semantics.termination "partial"` + `open PartialCorrectness` (spec_guide.md:112, REQUIRED by G-HYGIENE for every velvet bundle): a divergent program vacuously satisfies ANY postcondition.

It is (a) universal to all 500 velvet bundles, not a property of THIS spec's refinement fidelity, and (b) has NO faithful refined patch — the real `Add._eval_is_zero` always terminates and refinement.md maps a terminating fold (tallyAll/classify) ↔ the terminating `for a in self.args` loop. Submitting it with no patch would falsely force INCONCLUSIVE; there is no honest faithful patch to run through run_resolve because no faithful refinement of a divergent loop exists. It is therefore out of G-EQ scope (refinement fidelity), not a verify⇏correct break. NO run_resolve was needed for the verdict: no in-scope verifying wrong impl exists (patches={}).

REFINEMENT.MD LEG AUDIT: A1(R type-refine), A2(R+I fold↔for-loop), A3(I concrete cascade + A-reference), A4(A-reference residualIsZero), A5(R) — NO kind-3. The lone changed op (the empty-nz guard) is modeled concretely as a disjunction, not axiomatized. The single A leg residualIsZero is an A-reference (opaque, zero consumed contract; proof discharges via fold + verdict unfolding only) for the UNCHANGED `self.func(*nz).is_zero`; correspondence validated by G-AX (recorded pass: patch-invariant on 5708 reached observations, sole divergence the guarded len(nz)==0 case) and mapping.md §3. Correspondence holds.

VERDICT: SOUND — 8 same-spec terminating wrong impls all rejected, positive control verifies, prepatch reproduced (atk_1), no kind-3 legs, the A-reference has no exploitable contract, and the only verifiers are out-of-scope divergence-vacuity artifacts with no faithful patch.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-not-too-strong / no drift from real repo behavior) audit for velvet sympy__sympy-15875, modeling Add._eval_is_zero at base b506169.

SPEC INTEGRITY: same_spec(Solution.lean, Solution_prepatch.lean) = True via swebench_unified.markers with the velvet backend — the spec region (Term, residualIsZero, classify, tallyAll, verdict, sumIsZeroSpec, method signature/ensures) is byte-identical between the passing solution and the failing prepatch, so a discrimination there is a genuine impl-vs-spec fact, not a spec swap. Solution.lean verifies (lean_verify.sh exit 0).

TRANSLITERATION FIDELITY: I fetched the real post-gold callee (git show base:add.py + gold hunk applied) and compared line-by-line. The gold change `if len(nz)==len(self.args)` -> `if len(nz)==0 or len(nz)==len(self.args)` is modeled CONCRETELY in verdict (`acc.nz.length = 0 ∨ acc.nz.length = n → none`), not hidden behind an axiom. classify's cascade maps the Python `if a.is_real: (is_zero True/False/else) elif a.is_imaginary elif (I*a).is_real else` exactly to `= some true` guards (SymPy tri-state True/False/None ↔ Option Bool). The b.is_zero combine tail (`not im_or_z and not im → True`; `im and not im_or_z → False`; else None; `is_zero False → False`) matches across all combinations, including the not-mentioned isComm/bail short-circuits.

ABSTRACTION SOUNDNESS: The only opaque symbol residualIsZero: List Term → Option Bool models the UNCHANGED residual `self.func(*nz).is_zero`. Modeling it as a function of the projected List Term is a genuine abstraction (I confirmed two lists projecting to identical Terms — [x,-x,I] vs [x,y,I] — give real verdicts False vs None), but the proof asserts NO property of residualIsZero's value (discharges purely via the fold + verdict unfolding), and both differential gates run the REAL callee, so this cannot make the spec too strong/unfaithful.

INDEPENDENT DIFFERENTIALS (both against the real base+gold callee in /tmp checkout): (1) bundled conformance_check.py: 76350 inputs, 0 disagreements; (2) my own fresh transliteration, seed 99991, richer atom pool (Rational, pi, E, cos, positive/complex symbols), 327811 constructible inputs, 0 disagreements. Reproducer `-2*I+(1+I)**2` → real=None, spec=None. No diverging input found; spec is not too strong. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Bundle: sympy__sympy-15875/velvet. Gold edit: add.py:557 `if len(nz) == len(self.args):` -> `if len(nz) == 0 or len(nz) == len(self.args):` (adds the len(nz)==0 disjunct returning None). Public problem_statement discloses: is_zero on Add gives a wrong `False` on complex expressions, the reproducer `-2*I + (1+I)**2` (both summands pure-imaginary), and the release note 'Fix is_zero becoming False on some expressions with Add'.

Spec-view examination (generated via markers.spec_view over Solution.lean): the visible pure `verdict` helper contains `else if acc.nz.length = 0 ∨ acc.nz.length = n then none` — a transliteration of the post-patch guard. This is the natural leakage-risk site for velvet/lean (the changed op is modeled in a VISIBLE pure region, not the elided impl). Assessed and judged NOT a leak of the gold edit beyond problem_statement, for these reasons:

1. A verified spec necessarily encodes the correct target behavior; that alone is not leakage. The standard is whether the spec view reveals the EDIT/diff/localization, not the correct semantics — else every bundle would fail.
2. The spec reveals the TARGET, not the EDIT. The `verdict` cascade transliterates the whole decision uniformly; the changed disjunct `nz.length = 0` sits beside the unchanged `nz.length = n` with no flag distinguishing them. Reconstructing the gold edit requires target−prepatch, and the spec view never exposes the prepatch guard. CONFIRMED: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) == True — the frozen spec view is byte-identical for the patched and prepatch twins, so the spec view carries zero differential that localizes the change.
3. The discriminating case is already public: the problem_statement reproducer `-2*I + (1+I)**2` is exactly the empty-nz (all-imaginary, no real-nonzero term) witness and publicly demands no wrong definite answer, so `nz.length = 0 -> none` adds negligible info beyond the public task.
4. No repo localization/narration/diff text: spec view has no add.py path, no dotted module path, no `_eval_is_zero` symbol echo (spec symbols are sumIsZero/verdict/classify/tallyAll/residualIsZero/Term/Tally), no diff markers; comments are abstract behavior descriptions with no bug/fix/regression/previously/wrong narration.

Mechanical corroboration: leakage.screen() passes clean (hard_failures=[]); changed symbol 'eval_is_zero' not embedded in any spec identifier; changed files/module path absent; no relaxed_leakage flag and no RELAXED_LEAKAGE.md (none needed). refinement.md/mapping.md do tie the disjunct to the gold hunk, but they are audit artifacts, NOT part of the consumer spec view, so out of scope for G-PANEL-3.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.