# P2 adversarial audit — django__django-13417

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
isEmpty=false, hasRawOrder=false, defaultOn=true, modelHasOrder=true, isGrouped=true: gold-patched property returns False (grouped result set whose only ordering is an inherited model default is NOT ordered), while the prepatch body / atk_1 return True. This is exactly the pinned clause `(isEmpty=false ∧ hasRawOrder=false ∧ isGrouped=true) → out=false` and the F2P tests test_annotated_default_ordering / test_annotated_values_default_ordering.
```

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
 -- (No consumed callee contracts and no deep-model references. The operation is a
@@ -68,7 +68,7 @@
       if hasRawOrder then
         return true
       else
-        if defaultOn && modelHasOrder && !isGrouped then
+        if defaultOn && modelHasOrder then
           return true
         else
           return false
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
 -- (No consumed callee contracts and no deep-model references. The operation is a
@@ -68,7 +68,7 @@
       if hasRawOrder then
         return true
       else
-        if defaultOn && modelHasOrder && !isGrouped then
+        if modelHasOrder && !isGrouped then
           return true
         else
           return false
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
 -- (No consumed callee contracts and no deep-model references. The operation is a
@@ -68,7 +68,7 @@
       if hasRawOrder then
         return true
       else
-        if defaultOn && modelHasOrder && !isGrouped then
+        if defaultOn && !isGrouped then
           return true
         else
           return false
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
 -- (No consumed callee contracts and no deep-model references. The operation is a
@@ -62,16 +62,7 @@
             ∧ modelHasOrder = true ∧ isGrouped = false) → out = true
   do
     -- impl-start
-    if isEmpty then
-      return true
-    else
-      if hasRawOrder then
-        return true
-      else
-        if defaultOn && modelHasOrder && !isGrouped then
-          return true
-        else
-          return false
+    return isEmpty || hasRawOrder || (defaultOn && modelHasOrder && isGrouped)
     -- impl-end
 
 prove_correct ordered by
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
 -- (No consumed callee contracts and no deep-model references. The operation is a
@@ -63,7 +63,7 @@
   do
     -- impl-start
     if isEmpty then
-      return true
+      return false
     else
       if hasRawOrder then
         return true
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
 -- (No consumed callee contracts and no deep-model references. The operation is a
@@ -62,16 +62,7 @@
             ∧ modelHasOrder = true ∧ isGrouped = false) → out = true
   do
     -- impl-start
-    if isEmpty then
-      return true
-    else
-      if hasRawOrder then
-        return true
-      else
-        if defaultOn && modelHasOrder && !isGrouped then
-          return true
-        else
-          return false
+    return isEmpty || hasRawOrder
     -- impl-end
 
 prove_correct ordered by
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
 -- (No consumed callee contracts and no deep-model references. The operation is a
@@ -62,16 +62,7 @@
             ∧ modelHasOrder = true ∧ isGrouped = false) → out = true
   do
     -- impl-start
-    if isEmpty then
-      return true
-    else
-      if hasRawOrder then
-        return true
-      else
-        if defaultOn && modelHasOrder && !isGrouped then
-          return true
-        else
-          return false
+    return isEmpty || hasRawOrder || (defaultOn || (modelHasOrder && !isGrouped))
     -- impl-end
 
 prove_correct ordered by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts and no deep-model references. The operation is a
--  pure boolean decision over five independent yes/no signals about a result set;
--  every signal is read purely for its truth value, so there is nothing to
--  axiomatize. The `axioms` region is intentionally empty.)
-- axioms-end

-- pure-start
/- The exact decision the introspection flag must report.

   A result set answers "will my rows come back in a well-defined order?" from
   five independent yes/no signals:

     * `isEmpty`        — the result set is statically empty;
     * `hasRawOrder`    — an explicit raw / column ordering was attached;
     * `defaultOn`      — a default ordering inherited from the model is active;
     * `modelHasOrder`  — the model declares a default ordering at all;
     * `isGrouped`      — the result set collapses rows into groups.

   The flag is TRUE exactly when the result set is statically empty, OR an
   explicit ordering is attached, OR an inherited model default ordering is both
   active and declared AND the result set is NOT grouped. Collapsing rows into
   groups suppresses an inherited (non-explicit) default ordering: such a
   default no longer governs the surviving row order, so a grouped result set
   whose only ordering is that inherited default is NOT ordered. -/
def isOrdered (isEmpty hasRawOrder defaultOn modelHasOrder isGrouped : Bool) : Bool :=
  isEmpty || hasRawOrder || (defaultOn && modelHasOrder && !isGrouped)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The introspection flag of a result set. The five inputs are read-only yes/no
   signals (none is `mut`; the operation mutates nothing — directive 5) and the
   result is pinned exactly to the boolean decision above, so no implementation
   that disagrees on any of the thirty-two input combinations can verify.

   Alongside the exact-equality postcondition, four consequences any correct
   decision must exhibit are pinned, each tying the result to a witnessed input:
   an empty result set is always ordered; an explicitly-ordered result set is
   always ordered; a grouped result set whose only ordering is an inherited
   model default (no emptiness, no explicit ordering) is NOT ordered; and that
   same inherited default ordering on a non-grouped result set IS ordered. -/
method ordered (isEmpty : Bool) (hasRawOrder : Bool) (defaultOn : Bool)
    (modelHasOrder : Bool) (isGrouped : Bool) return (out : Bool)
  ensures out = isOrdered isEmpty hasRawOrder defaultOn modelHasOrder isGrouped
  ensures isEmpty = true → out = true
  ensures hasRawOrder = true → out = true
  ensures (isEmpty = false ∧ hasRawOrder = false ∧ isGrouped = true) → out = false
  ensures (isEmpty = false ∧ hasRawOrder = false ∧ defaultOn = true
            ∧ modelHasOrder = true ∧ isGrouped = false) → out = true
  do
    -- impl-start
    if isEmpty then
      return true
    else
      if hasRawOrder then
        return true
      else
        if defaultOn && modelHasOrder && !isGrouped then
          return true
        else
          return false
    -- impl-end

prove_correct ordered by
  loom_solve <;> simp_all [isOrdered]
```

Prepatch bug re-encoded as an attack: `True`.

Spec pins `out` by EXACT EQUALITY to `isOrdered isEmpty hasRawOrder defaultOn modelHasOrder isGrouped` over the finite 32-case (2^5) Bool domain, plus four redundant consequence clauses. Any verifying impl must therefore agree with the oracle on all 32 inputs, so no behaviorally-wrong impl can verify — verify⇒correct on the modeled domain.

Protocol executed:
- same_spec (swebench_unified.markers.same_spec, velvet) = True for pos.lean + all 7 atk files (spec/axiom/pre/post regions byte-identical; only impl-region edited).
- Positive control pos.lean = exact gold impl: `bash scripts/lean_verify.sh <path>` → exit 0 (VERIFIES).
- 7 DISTINCT wrong impls, verified concurrently in two ≤4 background batches:
  atk_1 prepatch bug (drop `!isGrouped` conjunct) → exit 1, unsolved goals; failure case is precisely `ensures_2/ensures_5` with hyps isEmpty=false,hasRawOrder=false,defaultOn=true∧modelHasOrder=true ⊢ isGrouped=false — the grouped-with-default counterexample (prepatch_reproduced=true).
  atk_2 drop `defaultOn` conjunct → exit 1, unsolved goals.
  atk_3 drop `modelHasOrder` conjunct → exit 1, unsolved goals.
  atk_4 ungrounded-oracle echo, wrong sign `&& isGrouped` → exit 1, unsolved goals.
  atk_5 control-flow-effect, flip isEmpty branch to return false → exit 1, unsolved goals.
  atk_6 partial-domain, drop third disjunct entirely (`isEmpty || hasRawOrder`) → exit 1, unsolved goals.
  atk_7 boolean-structure, `defaultOn || (modelHasOrder && !isGrouped)` → exit 1, unsolved goals.
- All 7 fail with genuine `error: unsolved goals` at the postcondition proof (not syntax errors).

Because NO wrong impl verified, there is no faithful refined patch to materialize/resolve — run_resolve step is vacuously satisfied (nothing to run). Not INCONCLUSIVE: all verifications completed cleanly (pos exit 0; 7 attacks exit 1) with no timeouts/contention.

Refinement/mapping audit (§4 A-legs): axioms region is EMPTY — refinement.md declares no A-consumed / A-reference legs and no kind-3 steps; all 9 legs A1–A9 are R (truthy→Bool for isEmpty/hasRawOrder/defaultOn/modelHasOrder/isGrouped) or I (control flow / returns). The five repo expressions (isinstance(self,EmptyQuerySet); extra_order_by or order_by; default_ordering; get_meta().ordering; group_by) are each consumed purely for truth value (if/elif condition or and/or/not operand), so the bool() projection is exact for the observable result — R-refinements sound. No library/utility callee left unchanged and inexpressible → no A-leg correspondence to break. G-CONF's conformance_check.py exhaustively covers the R/I shadow over all 32 combos + fuzz (seed 13417). Nested-if vs elif is control-flow-identical (Velvet bans elif). Correspondence holds.

Commands (representative):
  bash scripts/lean_verify.sh pos.lean   # exit 0
  bash scripts/lean_verify.sh atk_N.lean # exit 1 for N=1..7
Note: prior recorded G-EQ was INCONCLUSIVE (1 attack failed to complete); this pass completes 7 attacks + positive control with no falsification — spec is sound.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
isEmpty=false, hasRawOrder=false, defaultOn=true, modelHasOrder=true, isGrouped=true: gold-patched property returns False (grouped result set whose only ordering is an inherited model default is NOT ordered), while the prepatch body / atk_1 return True. This is exactly the pinned clause `(isEmpty=false ∧ hasRawOrder=false ∧ isGrouped=true) → out=false` and the F2P tests test_annotated_default_ordering / test_annotated_values_default_ordering.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts and no deep-model references. The operation is a
--  pure boolean decision over five independent yes/no signals about a result set;
--  every signal is read purely for its truth value, so there is nothing to
--  axiomatize. The `axioms` region is intentionally empty.)
-- axioms-end

-- pure-start
/- The exact decision the introspection flag must report.

   A result set answers "will my rows come back in a well-defined order?" from
   five independent yes/no signals:

     * `isEmpty`        — the result set is statically empty;
     * `hasRawOrder`    — an explicit raw / column ordering was attached;
     * `defaultOn`      — a default ordering inherited from the model is active;
     * `modelHasOrder`  — the model declares a default ordering at all;
     * `isGrouped`      — the result set collapses rows into groups.

   The flag is TRUE exactly when the result set is statically empty, OR an
   explicit ordering is attached, OR an inherited model default ordering is both
   active and declared AND the result set is NOT grouped. Collapsing rows into
   groups suppresses an inherited (non-explicit) default ordering: such a
   default no longer governs the surviving row order, so a grouped result set
   whose only ordering is that inherited default is NOT ordered. -/
def isOrdered (isEmpty hasRawOrder defaultOn modelHasOrder isGrouped : Bool) : Bool :=
  isEmpty || hasRawOrder || (defaultOn && modelHasOrder && !isGrouped)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The introspection flag of a result set. The five inputs are read-only yes/no
   signals (none is `mut`; the operation mutates nothing — directive 5) and the
   result is pinned exactly to the boolean decision above, so no implementation
   that disagrees on any of the thirty-two input combinations can verify.

   Alongside the exact-equality postcondition, four consequences any correct
   decision must exhibit are pinned, each tying the result to a witnessed input:
   an empty result set is always ordered; an explicitly-ordered result set is
   always ordered; a grouped result set whose only ordering is an inherited
   model default (no emptiness, no explicit ordering) is NOT ordered; and that
   same inherited default ordering on a non-grouped result set IS ordered. -/
method ordered (isEmpty : Bool) (hasRawOrder : Bool) (defaultOn : Bool)
    (modelHasOrder : Bool) (isGrouped : Bool) return (out : Bool)
  ensures out = isOrdered isEmpty hasRawOrder defaultOn modelHasOrder isGrouped
  ensures isEmpty = true → out = true
  ensures hasRawOrder = true → out = true
  ensures (isEmpty = false ∧ hasRawOrder = false ∧ isGrouped = true) → out = false
  ensures (isEmpty = false ∧ hasRawOrder = false ∧ defaultOn = true
            ∧ modelHasOrder = true ∧ isGrouped = false) → out = true
  do
    -- impl-start
    if isEmpty then
      return true
    else
      if hasRawOrder then
        return true
      else
        if defaultOn && modelHasOrder && !isGrouped then
          return true
        else
          return false
    -- impl-end

prove_correct ordered by
  loom_solve <;> simp_all [isOrdered]
```

Prepatch bug re-encoded as an attack: `True`.

Spec pins `out` by EXACT EQUALITY to `isOrdered isEmpty hasRawOrder defaultOn modelHasOrder isGrouped` over the finite 32-case (2^5) Bool domain, plus four redundant consequence clauses. Any verifying impl must therefore agree with the oracle on all 32 inputs, so no behaviorally-wrong impl can verify — verify⇒correct on the modeled domain.

Protocol executed:
- same_spec (swebench_unified.markers.same_spec, velvet) = True for pos.lean + all 7 atk files (spec/axiom/pre/post regions byte-identical; only impl-region edited).
- Positive control pos.lean = exact gold impl: `bash scripts/lean_verify.sh <path>` → exit 0 (VERIFIES).
- 7 DISTINCT wrong impls, verified concurrently in two ≤4 background batches:
  atk_1 prepatch bug (drop `!isGrouped` conjunct) → exit 1, unsolved goals; failure case is precisely `ensures_2/ensures_5` with hyps isEmpty=false,hasRawOrder=false,defaultOn=true∧modelHasOrder=true ⊢ isGrouped=false — the grouped-with-default counterexample (prepatch_reproduced=true).
  atk_2 drop `defaultOn` conjunct → exit 1, unsolved goals.
  atk_3 drop `modelHasOrder` conjunct → exit 1, unsolved goals.
  atk_4 ungrounded-oracle echo, wrong sign `&& isGrouped` → exit 1, unsolved goals.
  atk_5 control-flow-effect, flip isEmpty branch to return false → exit 1, unsolved goals.
  atk_6 partial-domain, drop third disjunct entirely (`isEmpty || hasRawOrder`) → exit 1, unsolved goals.
  atk_7 boolean-structure, `defaultOn || (modelHasOrder && !isGrouped)` → exit 1, unsolved goals.
- All 7 fail with genuine `error: unsolved goals` at the postcondition proof (not syntax errors).

Because NO wrong impl verified, there is no faithful refined patch to materialize/resolve — run_resolve step is vacuously satisfied (nothing to run). Not INCONCLUSIVE: all verifications completed cleanly (pos exit 0; 7 attacks exit 1) with no timeouts/contention.

Refinement/mapping audit (§4 A-legs): axioms region is EMPTY — refinement.md declares no A-consumed / A-reference legs and no kind-3 steps; all 9 legs A1–A9 are R (truthy→Bool for isEmpty/hasRawOrder/defaultOn/modelHasOrder/isGrouped) or I (control flow / returns). The five repo expressions (isinstance(self,EmptyQuerySet); extra_order_by or order_by; default_ordering; get_meta().ordering; group_by) are each consumed purely for truth value (if/elif condition or and/or/not operand), so the bool() projection is exact for the observable result — R-refinements sound. No library/utility callee left unchanged and inexpressible → no A-leg correspondence to break. G-CONF's conformance_check.py exhaustively covers the R/I shadow over all 32 combos + fuzz (seed 13417). Nested-if vs elif is control-flow-identical (Velvet bans elif). Correspondence holds.

Commands (representative):
  bash scripts/lean_verify.sh pos.lean   # exit 0
  bash scripts/lean_verify.sh atk_N.lean # exit 1 for N=1..7
Note: prior recorded G-EQ was INCONCLUSIVE (1 attack failed to complete); this pass completes 7 attacks + positive control with no falsification — spec is sound.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of django__django-13417 velvet bundle. Modeled function `ordered`/`isOrdered` = isEmpty || hasRawOrder || (defaultOn && modelHasOrder && !isGrouped). Real post-patch callee QuerySet.ordered at base_commit 71ae1ab0 (verified checked out at base): `if isinstance(self,EmptyQuerySet): return True; if self.query.extra_order_by or self.query.order_by: return True; elif self.query.default_ordering and self.query.get_meta().ordering and not self.query.group_by: return True; else return False`. The two leading `if`s (first returns) collapse identically with the model's leading disjuncts. Every repo expression is consumed purely for truthiness (attribute reads inside if/elif/and/or/not), so the truthy->Bool R-refinement is exact for the observable boolean result — no drift. Verified: (1) same_spec(Solution, Solution_prepatch, velvet)=True — spec region is byte-identical, spec is frozen and not restructured to overfit; (2) lean_verify.sh Solution.lean exit 0; (3) conformance_check.py exhaustive over all 32 five-bool combinations + 200k fuzz, seed 13417, 0 disagreements between shadow and gold-patched oracle. Searched the entire finite 2^5=32-point input domain for any input where the modeled function disagrees with the real callee — none exists. The four auxiliary `ensures` consequence clauses (isEmpty->true, hasRawOrder->true, grouped-only-default->false, non-grouped-default->true) are all true of the real callee and are logical consequences of the exact-equality clause, so they do not over-constrain. Spec pins exactly the real callee's decision, nothing stronger. Note: patch.diff is absent from the bundle directory, but the gold hunk is quoted verbatim in refinement.md and confirmed against the real repo worktree; this does not affect the faithfulness verdict.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the consumer spec view (markers.spec_view of Solution.lean) against the public problem_statement only; refinement.md/mapping.md are auditor artifacts and out of scope. Mechanical leakage.screen passes clean (no diff markers, no reproduced gold line, no patched file path, no symbol collision, no narration).

Gold edit: adds `and not self.query.group_by` to QuerySet.ordered's elif — an inherited Meta.ordering default must yield .ordered=False for GROUP BY queries. This behavior is ALREADY PUBLIC in the problem_statement, which states outright that 'QuerySet.ordered property is incorrect for GROUP BY queries on models with Meta.ordering' and that annotate()/GROUP BY doesn't keep the default ordering yet qs.ordered stays truthy.

Spec-view review:
- All five parameters are abstract behavioral signals (isEmpty, hasRawOrder, defaultOn, modelHasOrder, isGrouped); none echoes the patched repo symbols group_by, default_ordering, or EmptyQuerySet.
- The only repo symbol present, the method name `ordered`, is public (qs.ordered appears verbatim in the problem_statement).
- Comments are abstract prose ('collapses rows into groups', 'inherited default ordering'); no GROUP BY attribute name, file path, diff hunk, or bug/fix narration.
- The pinned postcondition (isEmpty=false ∧ hasRawOrder=false ∧ isGrouped=true) → out=false and the !isGrouped conjunct specify exactly the publicly-disclosed GROUP-BY-suppresses-default-ordering behavior — a faithful spec of already-public correct behavior, not edit-localization beyond the problem_statement.

Nothing in the spec view reveals the gold edit beyond what the problem_statement already discloses.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
